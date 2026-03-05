"""
Audio Script Generator — LLM-based scene-to-script conversion.

Takes scene metadata from the codex and generates structured audio scripts
with narrator prose and per-character dialogue, each annotated with TTS
voice direction (instruct).

Supports multiple LLM backends via OpenAI-compatible API:
- Ollama (local, free)
- LM Studio (local, free)
- OpenRouter (cloud, cheap)
- OpenAI (cloud)
"""

import json
import re
from typing import Optional

from openai import OpenAI


# ---------------------------------------------------------------------------
# System prompt — adapted from Alexandria audiobook generator's approach
# ---------------------------------------------------------------------------

SCRIPT_SYSTEM_PROMPT = """\
You are an audiobook script annotator. You receive the EXISTING PROSE of a novel scene \
and split it into speaker-attributed chunks for text-to-speech narration.

OUTPUT FORMAT — valid JSON array, no markdown, no commentary:
[
  {{"speaker": "NARRATOR", "text": "The room had gone cold.", "instruct": "Quiet, tense narration."}},
  {{"speaker": "char_001", "text": "Tell me the truth.", "instruct": "Firm quiet authority, low and controlled."}},
  {{"speaker": "NARRATOR", "text": "Marcus could not meet her gaze.", "instruct": "Neutral, even narration."}}
]

FIELDS:
- "speaker": Character ID (e.g., "char_001") for characters, or "NARRATOR" for non-dialogue.
- "text": The EXACT text from the prose. Do not rewrite, paraphrase, or invent text.
- "instruct": 8-15 word voice direction for the TTS engine.

RULES:

1. SPLIT THE EXISTING PROSE — DO NOT REWRITE
   Your job is to split the EXISTING PROSE into speaker-attributed chunks.
   Preserve the EXACT wording word-for-word. Do not paraphrase, summarize, condense, or add text.
   Every word of the original prose must appear in exactly one chunk.
   - Text inside quotation marks (dialogue) → CHARACTER entry using the character ID from the roster.
   - All other text (description, action, internal thoughts, transitions) → NARRATOR entry.
   - Split at quote boundaries. Dialogue tags like "he said" go with the NARRATOR.
   - If no prose is provided, use the scene summary as a single NARRATOR entry.
   - NEVER invent dialogue that does not exist in the prose.

2. NARRATOR vs CHARACTER
   NARRATOR = everything that is NOT spoken dialogue (descriptions, actions, thoughts, tags).
   CHARACTER = only the words inside quotation marks that a character speaks aloud.
   Keep narration in third person. Never convert narration to first-person dialogue.

3. INSTRUCT GUIDELINES
   Layer up to three dimensions:
   - EMOTIONAL TONE: furious, fearful, triumphant, melancholy
   - DELIVERY: whispered, clipped, measured, urgent, deliberate
   - VOCAL QUALITY: voice cracking, gravelly, breathy, warm
   NARRATOR default: "Neutral, even narration." Shift only at scene-level tone changes.
   CHARACTER: Lean into the line's emotional grain. Be direct.
   Describe the VOICE, not the body. "Shocked, voice breaking." NOT "Trembling."
   PREFERRED VOCABULARY:
   - High-consistency: silky, even, soft, rounded, precise, firm, grounded, husky, measured
   - AVOID vague terms alone: "warm", "bright youthful energy" (causes voice instability)
   - Structure: [emotional tone], [delivery style], [vocal quality]

4. NARRATOR GROUPING
   Keep consecutive narrator text in ONE entry unless the emotional tone shifts.
   Do not split narration sentence-by-sentence.

5. TEXT PRESERVATION
   Do NOT modify any text. No number conversion, no abbreviation expansion,
   no bracket substitution. The prose is already TTS-ready.
   Your ONLY job is to split it into speaker-attributed chunks.
   Copy each word EXACTLY as it appears in the prose.

6. SCENE FLOW
   Preserve the original scene order. Do not rearrange.
   Split sequentially from start to end of the prose.

CRITICAL VALIDATION:
If you concatenate all "text" fields in order, the result MUST match the original prose
CHARACTER FOR CHARACTER. Do not add, remove, or change a single word. Think of your job
as placing labels on segments of the existing text — the text itself never changes.
"""


SCRIPT_USER_TEMPLATE = """\
Generate an audio script for this scene.

SCENE METADATA:
- Scene: Chapter {chapter_number}, Scene {scene_number}
- Summary: {scene_summary}
- Location: {location} (Time: {time_of_day})
- Scene Type: {scene_type}

CHARACTERS PRESENT:
{characters_block}

CHARACTER EMOTIONAL STATES:
{arc_beats_block}

THEMATIC CONTEXT:
{thematic_block}

{prose_block}

KNOWN CHARACTER ROSTER (use these exact names as speakers):
{character_roster}

Remember: output ONLY a valid JSON array. No markdown fences, no explanation."""


def _build_characters_block(scene: dict, codex_characters: list[dict]) -> str:
    """Build formatted character info for the prompt."""
    present = scene.get("characters_present", scene.get("characters", []))
    lines = []
    for name in present:
        # Find character details from codex
        char_data = next((c for c in codex_characters if c.get("name") == name), None)
        if char_data:
            char_id = char_data.get("character_id", "unknown")
            role = char_data.get("role", "unknown")
            personality = char_data.get("personality_summary", char_data.get("personality", ""))
            if isinstance(personality, list):
                personality = ", ".join(personality[:3])
            elif isinstance(personality, dict):
                personality = personality.get("summary", str(personality)[:100])
            lines.append(f"- {name} [ID: {char_id}] ({role}): {str(personality)[:150]}")
        else:
            lines.append(f"- {name}")
    return "\n".join(lines) if lines else "- (no character details available)"


def _build_arc_beats_block(scene: dict) -> str:
    """Build character arc beat info for the prompt."""
    arc_beats = scene.get("character_arc_beats", [])
    if not arc_beats:
        return "(no arc beats available)"
    lines = []
    for beat in arc_beats:
        name = beat.get("character_name", "Unknown")
        state = beat.get("emotional_state", "")
        change = beat.get("internal_change", "")
        lines.append(f"- {name}: {state}. {change}")
    return "\n".join(lines)


def _build_thematic_block(scene: dict) -> str:
    """Build thematic context for the prompt."""
    thematic = scene.get("thematic_beat", {})
    if not thematic:
        return "(no thematic context)"
    question = thematic.get("thematic_question", "")
    how = thematic.get("how_scene_tests_theme", "")
    return f"Question: {question}\nHow scene tests theme: {how}"


def _build_prose_block(scene: dict) -> str:
    """Include existing prose as the primary source to split."""
    prose = scene.get("prose", "")
    if not prose:
        return ""
    return f"\nEXISTING PROSE — SPLIT THIS EXACT TEXT INTO SPEAKER CHUNKS:\n{prose}"


def _build_character_roster(codex_characters: list[dict], present: list[str]) -> str:
    """Build the character roster string using character IDs."""
    roster = ["NARRATOR"]
    for name in present:
        char_data = next((c for c in codex_characters if c.get("name") == name), None)
        if char_data:
            roster.append(char_data.get("character_id", name.upper().replace(" ", "_")))
        else:
            roster.append(name.upper().replace(" ", "_"))
    return ", ".join(roster)


class AudioScriptGenerator:
    """Generates audio scripts from scene metadata using an LLM."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434/v1",
        model: str = "gpt-oss:20b",
        api_key: str = "ollama",
        temperature: float = 0.3,
        max_tokens: int = 4000,
    ):
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key,
        )
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def generate_script(
        self,
        scene: dict,
        chapter_number: int,
        scene_number: int,
        codex_characters: list[dict],
        max_retries: int = 2,
    ) -> list[dict]:
        """
        Generate an audio script for a single scene.

        Args:
            scene: Scene data from codex (scene_summary, characters, arcs, etc.)
            chapter_number: Chapter number for context
            scene_number: Scene number for context
            codex_characters: Full character list from codex
            max_retries: Number of retries on JSON parse failure

        Returns:
            List of {speaker, text, instruct} dicts
        """
        present = scene.get("characters_present", scene.get("characters", []))

        user_prompt = SCRIPT_USER_TEMPLATE.format(
            chapter_number=chapter_number,
            scene_number=scene_number,
            scene_summary=scene.get("scene_summary", "No summary available"),
            location=scene.get("location", "Unknown"),
            time_of_day=scene.get("time_of_day", "day"),
            scene_type=scene.get("scene_type", "mixed"),
            characters_block=_build_characters_block(scene, codex_characters),
            arc_beats_block=_build_arc_beats_block(scene),
            thematic_block=_build_thematic_block(scene),
            prose_block=_build_prose_block(scene),
            character_roster=_build_character_roster(codex_characters, present),
        )

        for attempt in range(max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": SCRIPT_SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    extra_body={"think": False},  # Disable thinking for Ollama reasoning models
                )

                content = response.choices[0].message.content or ""
                content = content.strip()

                # Strip <think>...</think> blocks from reasoning models (e.g., qwen3.5)
                content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()

                if not content:
                    raise ValueError("LLM returned empty response")

                # Strip markdown fences if present
                if content.startswith("```"):
                    # Remove ```json or ``` prefix and ``` suffix
                    lines = content.split("\n")
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines and lines[-1].strip() == "```":
                        lines = lines[:-1]
                    content = "\n".join(lines)

                script = json.loads(content)

                # Validate structure
                if not isinstance(script, list):
                    raise ValueError(f"Expected JSON array, got {type(script).__name__}")

                validated = []
                for entry in script:
                    if not isinstance(entry, dict):
                        continue
                    speaker = entry.get("speaker", "NARRATOR")
                    text = entry.get("text", "")
                    instruct = entry.get("instruct", "Neutral, even narration.")
                    if text.strip():
                        # NARRATOR stays uppercase; character IDs (char_001) stay as-is
                        if speaker.upper() == "NARRATOR":
                            speaker = "NARRATOR"
                        validated.append({
                            "speaker": speaker,
                            "text": text.strip(),
                            "instruct": instruct.strip(),
                        })

                if not validated:
                    raise ValueError("Script is empty after validation")

                # Validate text preservation: concatenated script should match prose
                original_prose = scene.get("prose", "")
                if original_prose:
                    reconstructed = " ".join(entry["text"] for entry in validated)
                    orig_norm = " ".join(original_prose.split())
                    recon_norm = " ".join(reconstructed.split())
                    if orig_norm != recon_norm:
                        # Calculate rough similarity (shared prefix length ratio)
                        common = 0
                        for a, b in zip(orig_norm, recon_norm):
                            if a == b:
                                common += 1
                            else:
                                break
                        ratio = common / max(len(orig_norm), 1)
                        print(f"        WARNING: Script text differs from prose (~{ratio:.0%} prefix match, {len(orig_norm)} vs {len(recon_norm)} chars)")

                return validated

            except (json.JSONDecodeError, ValueError) as e:
                if attempt < max_retries:
                    print(f"        Retry {attempt + 1}/{max_retries}: {e}")
                    continue
                print(f"        ERROR: Failed to parse script after {max_retries + 1} attempts: {e}")
                # Return a fallback narrator-only script from the prose
                return self._fallback_script(scene)

            except Exception as e:
                print(f"        ERROR: LLM call failed: {e}")
                return self._fallback_script(scene)

    def _fallback_script(self, scene: dict) -> list[dict]:
        """Generate a simple narrator-only fallback from existing prose."""
        prose = scene.get("prose", "")
        summary = scene.get("scene_summary", "")
        text = prose if prose else summary
        if not text:
            text = "The scene continues."
        return [
            {
                "speaker": "NARRATOR",
                "text": text,
                "instruct": "Neutral, even narration.",
            }
        ]

    def generate_title_script(self, title: str) -> list[dict]:
        """Generate a simple title announcement script."""
        return [
            {
                "speaker": "NARRATOR",
                "text": title,
                "instruct": "Grand, resonant announcement with gravitas.",
            }
        ]

    def generate_chapter_title_script(
        self, chapter_number: int, chapter_title: str
    ) -> list[dict]:
        """Generate a chapter title announcement script."""
        text = f"Chapter {chapter_number}. {chapter_title}"
        return [
            {
                "speaker": "NARRATOR",
                "text": text,
                "instruct": "Clear, measured chapter announcement.",
            }
        ]
