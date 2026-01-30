#!/usr/bin/env python3
"""
Phase 3: REVISION (Multi-Pass Editing)

Performs multiple revision passes based on the author's revision style.
Each pass focuses on specific areas: pacing, dialogue, prose polish, etc.

Usage (standalone):
    uv run python -m src.phases.phase3_revision forge/20260105143022/codex.json
"""

import sys
import json
import time
import argparse
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

# Add parent directory to path for proper package imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.story_agents.narrative_agents import (
    StyleCriticAgent,
    ContinuityCriticAgent,
)
from src.story_agents.reviser_agent import ReviserAgent
from src.config import DEFAULT_MODEL
from src.authors import get_author
from src.authors.styles import RevisionStyle


@dataclass
class Phase3Result:
    """Result of Phase 3 revision."""
    codex_path: Path
    narrative: dict
    metadata: dict
    total_scenes: int
    passes_completed: int
    success: bool
    error: Optional[str] = None
    step_timings: dict = field(default_factory=dict)


def load_codex(codex_path: Path) -> dict:
    """Load codex JSON file."""
    with open(codex_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_codex(codex: dict, codex_path: Path) -> None:
    """Save codex JSON file."""
    with open(codex_path, "w", encoding="utf-8") as f:
        json.dump(codex, f, indent=2, ensure_ascii=False)


def split_into_sentences(text: str) -> list[str]:
    """Split text into sentences."""
    clean_text = text.replace("\n", " ")
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    sentences = re.split(r'(?<=[.!?])\s+', clean_text)
    return [s.strip() for s in sentences if s.strip()]


def get_revision_style_from_codex(codex: dict) -> RevisionStyle:
    """Get author's revision style from codex."""
    # author is at ROOT level
    author_data = codex.get("author", {})
    if not author_data:
        return RevisionStyle()

    author_id = author_data.get("id")
    if author_id:
        try:
            author = get_author(author_id)
            return author.revision_style
        except ValueError:
            pass

    # Reconstruct from codex data
    style_data = author_data.get("revision_style", {})
    return RevisionStyle(
        num_passes=style_data.get("num_passes", 1),
        focus_areas=style_data.get("focus_areas", ["pacing"]),
        cut_aggressively=style_data.get("cut_aggressively", False),
        expand_scenes=style_data.get("expand_scenes", False),
    )


def build_revision_prompt(focus: str, style: RevisionStyle) -> str:
    """Build revision prompt for a specific focus area."""
    prompts = {
        "pacing": """
## Revision Focus: PACING
Review the narrative for pacing issues:
- Identify scenes that drag or feel rushed
- Check for proper tension build and release
- Ensure each scene advances the story
- Balance action, dialogue, and description
""",
        "dialogue": """
## Revision Focus: DIALOGUE
Review the narrative for dialogue quality:
- Ensure each character has a distinct voice
- Check for natural conversation flow
- Add subtext where appropriate
- Remove exposition dumps in dialogue
- Make sure dialogue serves the story
""",
        "prose_polish": """
## Revision Focus: PROSE POLISH
Review the narrative for prose quality:
- Vary sentence length and structure
- Remove redundant words and phrases
- Strengthen verbs, minimize adverbs
- Improve imagery and sensory details
- Ensure consistent tone throughout
""",
        "tension": """
## Revision Focus: TENSION
Review the narrative for tension:
- Build and sustain tension throughout
- Create micro-tensions within scenes
- Use pacing to heighten suspense
- Ensure stakes are clear and escalating
- Add obstacles and complications
""",
        "continuity": """
## Revision Focus: CONTINUITY
Review the narrative for continuity:
- Check character consistency (traits, voice, motivations)
- Verify setting details remain consistent
- Ensure timeline makes sense
- Check for plot holes or contradictions
- Verify character names and relationships
""",
    }

    base_prompt = prompts.get(focus, prompts["pacing"])

    if style.cut_aggressively:
        base_prompt += """
## Additional Instruction: CUT AGGRESSIVELY
Be ruthless in cutting:
- Remove anything that doesn't serve the story
- Cut redundant scenes or passages
- Trim unnecessary description
- Delete filler dialogue
"""

    if style.expand_scenes:
        base_prompt += """
## Additional Instruction: EXPAND SCENES
Look for scenes that need more depth:
- Add emotional beats where lacking
- Expand important moments
- Deepen character interactions
- Add sensory details to key scenes
"""

    return base_prompt


def run_phase3_revision(
    codex_path: Path,
    model: str = None,
    passes: int = None,
) -> Phase3Result:
    """
    Perform multi-pass revision based on author's revision style.

    Args:
        codex_path: Path to codex.json (must have narrative from Phase 2)
        model: LLM model to use (default: from codex config)
        passes: Number of revision passes (default: from author's style)

    Returns:
        Phase3Result with revised narrative
    """
    codex_path = Path(codex_path)
    codex = load_codex(codex_path)

    # Use codex config as default
    codex_config = codex.get("config", {})
    model = model or codex_config.get("model", DEFAULT_MODEL)

    # Validate Phase 2 completed
    story = codex.get("story", {})
    if "narrative" not in story:
        raise ValueError("Codex missing narrative. Run Phase 2 first.")

    narrative = story["narrative"]
    narrative_acts = narrative.get("acts", [])
    if len(narrative_acts) < 3:
        raise ValueError(f"Incomplete narrative. Only {len(narrative_acts)} acts found.")

    # Get author's revision style
    revision_style = get_revision_style_from_codex(codex)
    num_passes = passes if passes is not None else revision_style.num_passes

    print(f"\n>>> Using model: {model}")
    print(f">>> Revision passes: {num_passes}")
    print(f">>> Focus areas: {', '.join(revision_style.focus_areas)}")
    print(f">>> Cut aggressively: {revision_style.cut_aggressively}")
    print(f">>> Expand scenes: {revision_style.expand_scenes}")

    # Get characters/locations for continuity checking
    characters_json = json.dumps(story.get("characters", []))
    locations_json = json.dumps(story.get("locations", []))

    # Initialize metadata in new structure
    if "metadata" not in codex:
        codex["metadata"] = {}
    if "phase_3" not in codex["metadata"]:
        codex["metadata"]["phase_3"] = {
            "phase": 3,
            "name": "Multi-Pass Revision",
            "revision_style": revision_style.to_dict(),
            "passes": [],
        }

    # Initialize agents
    style_critic = StyleCriticAgent(model=model)
    continuity_critic = ContinuityCriticAgent(model=model)
    reviser = ReviserAgent(model=model)

    step_timings = {}
    passes_completed = 0
    current_narrative = narrative

    # Run revision passes
    for pass_num in range(1, num_passes + 1):
        focus = revision_style.get_pass_focus(pass_num - 1)

        print(f"\n{'='*60}")
        print(f"REVISION PASS {pass_num}/{num_passes}: Focus on {focus.upper()}")
        print(f"{'='*60}")
        step_start = time.time()

        # Build focus-specific revision prompt
        revision_prompt = build_revision_prompt(focus, revision_style)

        # Get appropriate critique based on focus
        print(f">>> Getting {focus} critique...")

        if focus == "continuity":
            narrative_json = json.dumps(current_narrative)
            critique = continuity_critic.critique(
                narrative_json, characters_json, locations_json
            )
            critique_json = json.dumps(critique.model_dump())
        else:
            narrative_json = json.dumps(current_narrative)
            critique = style_critic.critique(narrative_json)
            critique_json = json.dumps(critique.model_dump())

        print(f"    Found {len(critique.model_dump().get('issues', []))} issues")

        # Revise act-by-act to avoid token limits
        print(f">>> Revising narrative (focus: {focus})...")
        revised_acts = []
        total_scenes_revised = 0

        for act in current_narrative.get("acts", []):
            act_number = act.get("act_number", len(revised_acts) + 1)
            act_scenes = act.get("scenes", [])
            print(f"    Revising Act {act_number} ({len(act_scenes)} scenes)...")

            try:
                # Build single-act narrative for revision
                act_narrative = {
                    "title": current_narrative.get("title", ""),
                    "acts": [act]
                }

                # Inject focus prompt into revision
                revised_act = reviser.revise_narrative_structured(
                    act_narrative,
                    [critique_json],
                    additional_prompt=revision_prompt
                )

                revised_act_data = revised_act.model_dump()
                if revised_act_data.get("acts") and len(revised_act_data["acts"]) > 0:
                    revised_act_dict = revised_act_data["acts"][0]
                    revised_scene_count = len(revised_act_dict.get("scenes", []))

                    if revised_scene_count >= len(act_scenes) * 0.8:  # Allow 20% scene reduction
                        revised_acts.append(revised_act_dict)
                        total_scenes_revised += revised_scene_count
                        print(f"        Revised ({revised_scene_count} scenes)")
                    else:
                        print(f"        Warning: Too many scenes lost, keeping original")
                        revised_acts.append(act)
                        total_scenes_revised += len(act_scenes)
                else:
                    print(f"        Warning: Empty revision, keeping original")
                    revised_acts.append(act)
                    total_scenes_revised += len(act_scenes)

            except Exception as e:
                print(f"        Warning: Revision failed ({e}), keeping original")
                revised_acts.append(act)
                total_scenes_revised += len(act_scenes)

        # Update current narrative for next pass
        current_narrative = {
            "title": current_narrative.get("title", ""),
            "acts": revised_acts,
        }

        # Re-add sentences and paragraphs
        for act in current_narrative["acts"]:
            for scene in act.get("scenes", []):
                text = scene.get("text", "")
                if text:
                    scene["paragraphs"] = text.split("\n\n")
                    scene["sentences"] = split_into_sentences(text)

        # Record pass metadata
        pass_timing = round(time.time() - step_start, 2)
        step_timings[f"pass{pass_num}_{focus}"] = pass_timing

        codex["metadata"]["phase_3"]["passes"].append({
            "pass_number": pass_num,
            "focus": focus,
            "issues_found": len(critique.model_dump().get("issues", [])),
            "scenes_revised": total_scenes_revised,
            "timing_seconds": pass_timing,
        })

        passes_completed += 1
        print(f">>> Pass {pass_num} complete ({total_scenes_revised} scenes) ({pass_timing:.1f}s)")

    # Save final revised narrative
    codex["story"]["narrative"] = current_narrative
    save_codex(codex, codex_path)

    # Count final scenes
    final_scene_count = sum(
        len(act.get("scenes", []))
        for act in current_narrative.get("acts", [])
    )

    print(f"\n>>> Revision complete: {passes_completed} passes")
    print(f">>> Final narrative saved to: {codex_path}")

    final_metadata = codex.get("metadata", {}).get("phase_3", {})

    return Phase3Result(
        codex_path=codex_path,
        narrative=current_narrative,
        metadata=final_metadata,
        total_scenes=final_scene_count,
        passes_completed=passes_completed,
        success=True,
        step_timings=step_timings,
    )


def main():
    """CLI entry point for standalone execution."""
    parser = argparse.ArgumentParser(
        description="Phase 3: Multi-Pass Revision"
    )
    parser.add_argument(
        "codex_path",
        type=Path,
        help="Path to codex.json (must have narrative from Phase 2)"
    )
    parser.add_argument(
        "--model",
        default=None,
        help=f"LLM model (default: from codex or {DEFAULT_MODEL})"
    )
    parser.add_argument(
        "--passes",
        type=int,
        default=None,
        help="Number of revision passes (default: from author's style)"
    )
    args = parser.parse_args()

    if not args.codex_path.exists():
        print(f"ERROR: Codex not found: {args.codex_path}")
        sys.exit(1)

    result = run_phase3_revision(
        args.codex_path,
        model=args.model,
        passes=args.passes,
    )

    print(f"\n>>> Title: {result.narrative.get('title', 'Untitled')}")
    print(f">>> Total scenes: {result.total_scenes}")
    print(f">>> Passes completed: {result.passes_completed}")


if __name__ == "__main__":
    main()
