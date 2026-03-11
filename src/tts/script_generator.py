"""
Audio Script Generator — hybrid rule-based + LLM pipeline.

Splits scene prose into speaker-attributed chunks using deterministic
regex splitting (100% text-preserving), then annotates each chunk with
TTS voice direction via a lightweight LLM call.

Supports multiple LLM backends via OpenAI-compatible API:
- Ollama (local, free)
- LM Studio (local, free)
- OpenRouter (cloud, cheap)
- OpenAI (cloud)
"""

import json
import logging
import re
from typing import Optional

from openai import OpenAI

logger = logging.getLogger("audio_script")

# Smart/curly quote → ASCII mapping (applied before splitting)
_QUOTE_NORMALIZE = {
    "\u201c": '"',  # left double curly
    "\u201d": '"',  # right double curly
    "\u2018": "'",  # left single curly
    "\u2019": "'",  # right single curly
    "\u2033": '"',  # double prime
    "\u2032": "'",  # single prime
}

# Common dialogue tag verbs for speaker attribution
_SPEECH_VERBS = {
    "said", "says", "whispered", "murmured", "muttered", "shouted", "yelled",
    "called", "cried", "replied", "answered", "asked", "demanded", "snapped",
    "hissed", "growled", "snarled", "breathed", "sighed", "groaned", "barked",
    "exclaimed", "declared", "announced", "pleaded", "begged", "urged",
    "insisted", "continued", "added", "began", "finished", "interrupted",
    "stammered", "stuttered", "rasped", "croaked", "spat", "retorted",
}

# ---------------------------------------------------------------------------
# LLM prompt for instruct-only annotation (lightweight — ~500 tokens output)
# ---------------------------------------------------------------------------

INSTRUCT_SYSTEM_PROMPT = """\
You annotate audiobook script chunks with TTS voice direction.

You receive a JSON array of {speaker, text_preview} objects.
Return a JSON array of instruct strings (same length, same order).

Each instruct should be 8-15 words describing HOW to deliver the line vocally.
Layer up to three dimensions:
- EMOTIONAL TONE: furious, fearful, triumphant, melancholy
- DELIVERY: whispered, clipped, measured, urgent, deliberate
- VOCAL QUALITY: voice cracking, gravelly, breathy, husky

For NARRATOR: default "Grounded, deliberate narration." Shift to match scene tension.
For CHARACTERS: lean into the line's emotional grain. Be direct.
Describe the VOICE, not the body. "Shocked, voice breaking." NOT "Trembling."

Output ONLY a valid JSON array of strings. No markdown, no commentary."""

INSTRUCT_USER_TEMPLATE = """\
Scene: Chapter {chapter_number}, Scene {scene_number}
Summary: {scene_summary}
Scene Type: {scene_type}

Annotate these chunks with voice direction:
{chunks_json}

Output a JSON array of {count} instruct strings, one per chunk."""


# Keep the old prompt constants for backward compatibility if anything imports them
SCRIPT_SYSTEM_PROMPT = INSTRUCT_SYSTEM_PROMPT
SCRIPT_USER_TEMPLATE = INSTRUCT_USER_TEMPLATE


def _build_characters_block(scene: dict, codex_characters: list[dict]) -> str:
    """Build formatted character info for the prompt."""
    present = scene.get("characters_present", scene.get("characters", []))
    lines = []
    for name in present:
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


def _normalize_quotes(text: str) -> str:
    """Replace smart/curly quotes with ASCII equivalents."""
    for old, new in _QUOTE_NORMALIZE.items():
        text = text.replace(old, new)
    return text


class AudioScriptGenerator:
    """Generates audio scripts using rule-based splitting + LLM instruct annotation."""

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

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_script(
        self,
        scene: dict,
        chapter_number: int,
        scene_number: int,
        codex_characters: list[dict],
        max_retries: int = 2,
    ) -> list[dict]:
        """Generate an audio script for a single scene.

        Uses a hybrid approach:
        1. Rule-based regex splitting (deterministic, 100% text-preserving)
        2. LLM instruct annotation (lightweight, graceful fallback)

        Returns:
            List of {speaker, text, instruct} dicts
        """
        present = scene.get("characters_present", scene.get("characters", []))
        prose = scene.get("prose", "")

        if not prose:
            summary = scene.get("scene_summary", "The scene continues.")
            return [{
                "speaker": "NARRATOR",
                "text": summary,
                "instruct": "Grounded, deliberate narration.",
            }]

        # Step 1: Deterministic splitting (never fails)
        chunks = self._split_prose_into_chunks(prose, present, codex_characters)

        # Step 2: LLM instruct annotation (can fail gracefully)
        try:
            instructs = self._annotate_instructs(
                chunks, scene, chapter_number, scene_number, max_retries,
            )
            for i, chunk in enumerate(chunks):
                if i < len(instructs) and instructs[i]:
                    chunk["instruct"] = instructs[i]
        except Exception as e:
            logger.warning("Instruct annotation failed, using defaults: %s", e)

        return chunks

    # ------------------------------------------------------------------
    # Step 1: Rule-based prose splitting
    # ------------------------------------------------------------------

    def _split_prose_into_chunks(
        self,
        prose: str,
        present: list[str],
        codex_characters: list[dict],
    ) -> list[dict]:
        """Split prose into speaker-attributed chunks using regex.

        Splits at quote boundaries. Text inside quotes is attributed to
        characters via dialogue tag analysis. Everything else is NARRATOR.
        Guarantees: concatenated text == original prose.
        """
        # Normalize smart quotes for consistent splitting
        normalized = _normalize_quotes(prose)

        # Build name -> character_id lookup
        name_to_id: dict[str, str] = {}
        for name in present:
            char_data = next(
                (c for c in codex_characters if c.get("name") == name), None
            )
            if char_data:
                char_id = char_data.get("character_id", name.upper().replace(" ", "_"))
            else:
                char_id = name.upper().replace(" ", "_")
            name_to_id[name] = char_id
            # Also map first name and last name for tag matching
            parts = name.split()
            if len(parts) >= 2:
                name_to_id[parts[0]] = char_id  # first name
                name_to_id[parts[-1]] = char_id  # last name

        # Build pronoun -> character_id mapping for 1- or 2-person scenes
        pov_char_id = None
        pronoun_map: dict[str, str] = {}
        if len(present) == 1:
            only_id = name_to_id.get(present[0], "NARRATOR")
            pronoun_map = {"he": only_id, "she": only_id}
            pov_char_id = only_id
        elif len(present) == 2:
            # Map gendered pronouns if character genders differ
            for name in present:
                char_data = next(
                    (c for c in codex_characters if c.get("name") == name), None
                )
                if char_data:
                    gender = char_data.get("gender", "").lower()
                    cid = name_to_id.get(name, "NARRATOR")
                    if gender in ("male", "m"):
                        pronoun_map["he"] = cid
                    elif gender in ("female", "f"):
                        pronoun_map["she"] = cid

        # Split prose at quote boundaries
        # This regex captures quoted strings as separate groups
        parts = re.split(r'("(?:[^"\\]|\\.)*")', normalized)

        raw_chunks: list[dict] = []
        last_named_speaker: Optional[str] = None

        for i, part in enumerate(parts):
            if not part:
                continue

            if part.startswith('"') and part.endswith('"'):
                # This is dialogue — strip quotes for TTS text
                dialogue_text = part[1:-1]
                if not dialogue_text.strip():
                    # Empty quotes — treat as narrator
                    raw_chunks.append({
                        "speaker": "NARRATOR",
                        "text": part,
                        "instruct": "Grounded, deliberate narration.",
                    })
                    continue

                # Determine speaker from surrounding narration
                speaker = self._resolve_speaker(
                    parts, i, name_to_id, pronoun_map, last_named_speaker
                )
                last_named_speaker = speaker if speaker != "NARRATOR" else last_named_speaker

                raw_chunks.append({
                    "speaker": speaker,
                    "text": part,
                    "instruct": "Grounded, deliberate narration.",
                })
            else:
                # Narration text
                if part.strip():
                    raw_chunks.append({
                        "speaker": "NARRATOR",
                        "text": part,
                        "instruct": "Grounded, deliberate narration.",
                    })
                elif part:
                    # Whitespace-only — still keep to preserve exact text
                    raw_chunks.append({
                        "speaker": "NARRATOR",
                        "text": part,
                        "instruct": "Grounded, deliberate narration.",
                    })

        # Merge consecutive NARRATOR chunks
        merged: list[dict] = []
        for chunk in raw_chunks:
            if merged and merged[-1]["speaker"] == "NARRATOR" and chunk["speaker"] == "NARRATOR":
                merged[-1]["text"] += chunk["text"]
            else:
                merged.append(chunk)

        # Split long NARRATOR chunks at paragraph boundaries
        merged = self._split_long_narrator_chunks(merged)

        # Log warning if dialogue ratio is low
        total_words = sum(len(c["text"].split()) for c in merged)
        dialogue_chunks = [c for c in merged if c["speaker"] != "NARRATOR"]
        if total_words > 200 and len(dialogue_chunks) < total_words / 150:
            logger.warning(
                "Low dialogue ratio: %d dialogue chunks in %d words (expected ~%d). "
                "Scene may sound monotonous.",
                len(dialogue_chunks), total_words, total_words // 150,
            )

        # Strip leading/trailing whitespace from each chunk's text (but not internal)
        for chunk in merged:
            chunk["text"] = chunk["text"].strip()

        # Remove empty chunks
        merged = [c for c in merged if c["text"]]

        # Validation: concatenated text should match normalized prose
        reconstructed = " ".join(c["text"] for c in merged)
        orig_norm = " ".join(normalized.split())
        recon_norm = " ".join(reconstructed.split())
        if orig_norm != recon_norm:
            logger.warning(
                "Script text reconstruction mismatch: %d vs %d chars",
                len(orig_norm), len(recon_norm),
            )

        return merged

    # Max words per narrator chunk (~40 seconds of speech at ~230 WPM)
    MAX_NARRATOR_WORDS = 150

    def _split_long_narrator_chunks(self, chunks: list[dict]) -> list[dict]:
        """Split NARRATOR chunks that exceed MAX_NARRATOR_WORDS at paragraph boundaries.

        Ensures no single TTS narrator segment is too long, which causes
        listener fatigue and monotonous audio. Splits at \\n\\n (paragraph
        breaks) to maintain natural pacing.
        """
        result: list[dict] = []
        for chunk in chunks:
            if chunk["speaker"] != "NARRATOR" or len(chunk["text"].split()) <= self.MAX_NARRATOR_WORDS:
                result.append(chunk)
                continue

            # Split at paragraph boundaries
            paragraphs = chunk["text"].split("\n\n")
            current_text = ""
            for para in paragraphs:
                candidate = (current_text + "\n\n" + para).strip() if current_text else para
                if current_text and len(candidate.split()) > self.MAX_NARRATOR_WORDS:
                    # Flush current accumulator
                    result.append({
                        "speaker": "NARRATOR",
                        "text": current_text.strip(),
                        "instruct": chunk["instruct"],
                    })
                    current_text = para
                else:
                    current_text = candidate

            if current_text.strip():
                result.append({
                    "speaker": "NARRATOR",
                    "text": current_text.strip(),
                    "instruct": chunk["instruct"],
                })

        return result

    def _resolve_speaker(
        self,
        parts: list[str],
        dialogue_idx: int,
        name_to_id: dict[str, str],
        pronoun_map: dict[str, str],
        last_named_speaker: Optional[str],
    ) -> str:
        """Determine who speaks a dialogue chunk by scanning surrounding narration."""
        # Check narration AFTER the dialogue (dialogue tags: "said Liora", "she whispered")
        if dialogue_idx + 1 < len(parts):
            after = parts[dialogue_idx + 1]
            speaker = self._extract_speaker_from_tag(after, name_to_id, pronoun_map, leading=True)
            if speaker:
                return speaker

        # Check narration BEFORE the dialogue ("Liora said,")
        if dialogue_idx - 1 >= 0:
            before = parts[dialogue_idx - 1]
            speaker = self._extract_speaker_from_tag(before, name_to_id, pronoun_map, leading=False)
            if speaker:
                return speaker

        # Fallback: last named speaker (for continuation dialogue)
        if last_named_speaker:
            return last_named_speaker

        # Ultimate fallback: first character present
        if name_to_id:
            return next(iter(name_to_id.values()))

        return "NARRATOR"

    def _extract_speaker_from_tag(
        self,
        narration: str,
        name_to_id: dict[str, str],
        pronoun_map: dict[str, str],
        leading: bool,
    ) -> Optional[str]:
        """Extract speaker from a dialogue tag in narration text.

        Args:
            narration: The narration text adjacent to dialogue
            name_to_id: Name -> character_id mapping
            pronoun_map: Pronoun -> character_id mapping
            leading: If True, tag is at the start of narration (after dialogue)
        """
        # Normalize for matching
        text = narration.strip()
        if not text:
            return None

        if leading:
            # Pattern: "Name verb" or "pronoun verb" at start of narration after quote
            # e.g., ' Viren said,' or ' she hissed,'
            # Match first few words
            first_words = text.split()[:4]
            first_segment = " ".join(first_words).lower()

            # Check for "Name + speech_verb"
            for name, char_id in name_to_id.items():
                name_lower = name.lower()
                if first_segment.startswith(name_lower):
                    # Check if followed by a speech verb
                    rest = first_segment[len(name_lower):].strip().rstrip(".,;!?")
                    first_rest_word = rest.split()[0] if rest.split() else ""
                    if first_rest_word in _SPEECH_VERBS:
                        return char_id

            # Check for "pronoun + speech_verb"
            for pronoun, char_id in pronoun_map.items():
                if first_segment.startswith(pronoun + " "):
                    rest = first_segment[len(pronoun):].strip().rstrip(".,;!?")
                    first_rest_word = rest.split()[0] if rest.split() else ""
                    if first_rest_word in _SPEECH_VERBS:
                        return char_id
        else:
            # Pattern: "Name verb," or "pronoun verb," at END of narration before quote
            last_words = text.split()[-4:]
            last_segment = " ".join(last_words).lower().rstrip(".,;:!?")

            # Check for "Name + speech_verb" at end
            for name, char_id in name_to_id.items():
                name_lower = name.lower()
                # Look for "name verb" pattern
                pattern = re.compile(
                    rf"\b{re.escape(name_lower)}\b\s+(\w+)\s*$", re.IGNORECASE
                )
                match = pattern.search(last_segment)
                if match and match.group(1).lower() in _SPEECH_VERBS:
                    return char_id

            # Check pronoun at end
            for pronoun, char_id in pronoun_map.items():
                pattern = re.compile(
                    rf"\b{re.escape(pronoun)}\b\s+(\w+)\s*$", re.IGNORECASE
                )
                match = pattern.search(last_segment)
                if match and match.group(1).lower() in _SPEECH_VERBS:
                    return char_id

        return None

    # ------------------------------------------------------------------
    # Step 2: LLM instruct annotation
    # ------------------------------------------------------------------

    def _annotate_instructs(
        self,
        chunks: list[dict],
        scene: dict,
        chapter_number: int,
        scene_number: int,
        max_retries: int = 2,
    ) -> list[str]:
        """Generate instruct annotations for pre-split chunks via LLM.

        Only sends text previews (50 chars each) — tiny output (~500 tokens).
        Returns list of instruct strings matching chunk order.
        """
        # Build compact chunk previews for the LLM
        previews = []
        for chunk in chunks:
            text_preview = chunk["text"][:60]
            if len(chunk["text"]) > 60:
                text_preview += "..."
            previews.append({
                "speaker": chunk["speaker"],
                "text_preview": text_preview,
            })

        user_prompt = INSTRUCT_USER_TEMPLATE.format(
            chapter_number=chapter_number,
            scene_number=scene_number,
            scene_summary=scene.get("scene_summary", "No summary available"),
            scene_type=scene.get("scene_type", "mixed"),
            chunks_json=json.dumps(previews, indent=2),
            count=len(chunks),
        )

        for attempt in range(max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": INSTRUCT_SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=self.temperature,
                    max_tokens=min(self.max_tokens, 2000),
                    extra_body={"think": False},
                )

                content = response.choices[0].message.content or ""
                content = content.strip()

                # Strip think blocks and markdown fences
                content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
                if content.startswith("```"):
                    lines = content.split("\n")
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines and lines[-1].strip() == "```":
                        lines = lines[:-1]
                    content = "\n".join(lines)

                instructs = json.loads(content)

                if not isinstance(instructs, list):
                    raise ValueError(f"Expected JSON array, got {type(instructs).__name__}")

                # Validate and extract strings
                result = []
                for item in instructs:
                    if isinstance(item, str):
                        result.append(item.strip())
                    elif isinstance(item, dict):
                        result.append(item.get("instruct", "Grounded, deliberate narration.").strip())
                    else:
                        result.append("Grounded, deliberate narration.")

                return result

            except (json.JSONDecodeError, ValueError) as e:
                if attempt < max_retries:
                    logger.debug("Instruct annotation retry %d: %s", attempt + 1, e)
                    continue
                raise

        return []  # unreachable but satisfies type checker

    # ------------------------------------------------------------------
    # Fallback & utility scripts
    # ------------------------------------------------------------------

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
                "instruct": "Grounded, deliberate narration.",
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

    # ------------------------------------------------------------------
    # Voice design generation
    # ------------------------------------------------------------------

    VOICE_DESIGN_SYSTEM_PROMPT = """\
You generate TTS voice design descriptions for audiobook characters.

Each description is 10-15 words following this formula:
[gender register], [tonal quality], [delivery style], [personality trait]

Examples:
- "male tenor, warm confident authority, scholarly enthusiasm, steady composure"
- "female alto, sharp commanding edge, clipped professional diction, detective authority"
- "older male baritone, world-weary rumble, slow unhurried calm, gravel undertone"
- "young male tenor, nervous tremor, slightly breathless, halting speech"

RULES:
1. Start with gender + vocal register (soprano, mezzo, alto, tenor, baritone, bass)
2. Add 2-3 tonal/delivery traits that reflect the character's personality
3. Be acoustically specific — describe the VOICE, not emotions or actions
4. Each character must sound distinct from the others
5. NARRATOR should be a rich, dynamic storytelling voice

Output ONLY a valid JSON object. No markdown, no commentary."""

    VOICE_DESIGN_USER_TEMPLATE = """\
Generate a TTS voice design description for each character and the NARRATOR.

Characters:
{characters_block}

Return a JSON object mapping character_id to voice description:
{{"NARRATOR": "male baritone, ...", "char_001": "...", ...}}"""

    def generate_voice_descriptions(
        self,
        codex_characters: list[dict],
        max_retries: int = 2,
    ) -> dict[str, str]:
        """Generate LLM-powered voice descriptions for all characters.

        Uses character personality, role, and gender to produce acoustically
        precise voice design descriptions for the TTS VoiceDesign model.

        Args:
            codex_characters: Character list from codex
            max_retries: Retries on JSON parse failure

        Returns:
            Dict mapping character_id (and "NARRATOR") -> voice description string
        """
        # Build character summaries for the prompt
        lines = []
        for char in codex_characters:
            char_id = char.get("character_id", "unknown")
            name = char.get("name", "Unknown")
            gender = char.get("gender", "unknown")
            role = char.get("role", char.get("role_in_story", "unknown"))
            thematic = char.get("thematic_perspective", "")
            arc = char.get("arc_type", "")

            # Build personality summary
            traits = []
            if thematic:
                traits.append(thematic)
            if arc:
                traits.append(arc)
            personality = ", ".join(traits) if traits else "no details"

            lines.append(f"- {char_id}: {name} ({gender}, {role}) — {personality}")

        characters_block = "\n".join(lines)

        user_prompt = self.VOICE_DESIGN_USER_TEMPLATE.format(
            characters_block=characters_block,
        )

        for attempt in range(max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self.VOICE_DESIGN_SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=self.temperature,
                    max_tokens=min(self.max_tokens, 1500),
                    extra_body={"think": False},
                )

                content = response.choices[0].message.content or ""
                content = content.strip()

                # Strip think blocks and markdown fences
                content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
                if content.startswith("```"):
                    content_lines = content.split("\n")
                    if content_lines[0].startswith("```"):
                        content_lines = content_lines[1:]
                    if content_lines and content_lines[-1].strip() == "```":
                        content_lines = content_lines[:-1]
                    content = "\n".join(content_lines)

                result = json.loads(content)
                if not isinstance(result, dict):
                    raise ValueError(f"Expected JSON object, got {type(result).__name__}")

                # Validate: all values should be non-empty strings
                validated = {}
                for key, desc in result.items():
                    if isinstance(desc, str) and desc.strip():
                        validated[key] = desc.strip()

                if not validated:
                    raise ValueError("All voice descriptions are empty")

                logger.info("Generated %d voice descriptions via LLM", len(validated))
                return validated

            except (json.JSONDecodeError, ValueError) as e:
                if attempt < max_retries:
                    logger.debug("Voice description retry %d: %s", attempt + 1, e)
                    continue
                logger.warning("Voice description LLM failed after %d attempts: %s", max_retries + 1, e)

            except Exception as e:
                logger.warning("Voice description LLM call failed: %s", e)
                break

        # Fallback: rule-based generation (better than the 2-word engine default)
        return self._fallback_voice_descriptions(codex_characters)

    def _fallback_voice_descriptions(self, codex_characters: list[dict]) -> dict[str, str]:
        """Rule-based fallback voice descriptions from character data."""
        result = {
            "NARRATOR": "male baritone, rich cinematic narrator, dynamic storytelling range, polished presence",
        }

        _REGISTERS = {
            "male": ["male baritone", "male tenor", "deep male baritone"],
            "female": ["female mezzo-soprano", "female alto", "female contralto"],
        }
        _ROLE_TONES = {
            "protagonist": "grounded firm presence, steady composure",
            "antagonist": "dark commanding edge, steely intensity",
            "supporting": "clear balanced delivery, warm reliability",
            "mentor": "warm gravitas, patient measured wisdom",
        }

        male_idx, female_idx = 0, 0
        for char in codex_characters:
            char_id = char.get("character_id", "")
            if not char_id:
                continue

            gender = char.get("gender", "").lower()
            role = char.get("role", char.get("role_in_story", "supporting")).lower()

            # Cycle through registers to give variety
            if gender == "male":
                register = _REGISTERS["male"][male_idx % len(_REGISTERS["male"])]
                male_idx += 1
            elif gender == "female":
                register = _REGISTERS["female"][female_idx % len(_REGISTERS["female"])]
                female_idx += 1
            else:
                register = "androgynous mid-range"

            # Map role to tonal description
            tone = _ROLE_TONES.get(role, _ROLE_TONES["supporting"])

            result[char_id] = f"{register}, {tone}"

        return result
