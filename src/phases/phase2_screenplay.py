#!/usr/bin/env python3
"""
Phase 2: SCREENPLAY (Narrative Prose Generation)

Writes scene-by-scene prose using the author's screenplay style.
Injects author's POV, tense, dialogue ratio, and tone into the writing.

Usage (standalone):
    uv run python -m src.phases.phase2_screenplay forge/20260105143022/codex.json
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
    WriterAgent,
    StyleCriticAgent,
    ContinuityCriticAgent,
)
from src.config import DEFAULT_MODEL, STORY_SCOPES, DEFAULT_STORY_SCOPE
from src.authors import get_author
from src.authors.styles import ScreenplayStyle


@dataclass
class Phase2Result:
    """Result of Phase 2 screenplay generation."""
    codex_path: Path
    narrative: dict
    metadata: dict
    total_scenes: int
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
    """Split text into sentences, preserving abbreviations."""
    clean_text = text.replace("\n", " ")
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    sentences = re.split(r'(?<=[.!?])\s+', clean_text)
    return [s.strip() for s in sentences if s.strip()]


def get_screenplay_style_from_codex(codex: dict) -> ScreenplayStyle:
    """Get author's screenplay style from codex.

    Returns:
        ScreenplayStyle instance (default if not in codex)
    """
    author_data = codex.get("author", {})
    if not author_data:
        return ScreenplayStyle()

    author_id = author_data.get("id")
    if author_id:
        try:
            author = get_author(author_id)
            return author.screenplay_style
        except ValueError:
            pass

    # Reconstruct from codex data
    style_data = author_data.get("screenplay_style", {})
    return ScreenplayStyle(
        pov=style_data.get("pov", "third_close"),
        tense=style_data.get("tense", "past"),
        dialogue_ratio=style_data.get("dialogue_ratio", "balanced"),
        description_density=style_data.get("description_density", "moderate"),
        sentence_length=style_data.get("sentence_length", "varied"),
        vocabulary=style_data.get("vocabulary", "moderate"),
        tone=style_data.get("tone", "hopeful"),
    )


def build_style_prompt(style: ScreenplayStyle) -> str:
    """Build writing style prompt from screenplay style."""
    parts = ["## Writing Style Instructions"]
    parts.append(style.get_prompt_modifier())
    return "\n".join(parts)


def run_phase2_screenplay(
    codex_path: Path,
    model: str = None,
    steps: list[int] = None,
) -> Phase2Result:
    """
    Generate narrative prose using author's screenplay style.

    Step 1: Write Act 1 Prose
    Step 2: Write Act 2 Prose
    Step 3: Write Act 3 Prose

    Args:
        codex_path: Path to codex.json (must have outline, characters, locations)
        model: LLM model to use (default: from codex config)
        steps: List of step numbers to run (default: all steps [1,2,3])

    Returns:
        Phase2Result with narrative data
    """
    codex_path = Path(codex_path)
    codex = load_codex(codex_path)

    # Use codex config as default
    codex_config = codex.get("config", {})
    model = model or codex_config.get("model", DEFAULT_MODEL)

    # Validate Phase 1 completed
    story = codex.get("story", {})
    if "outline" not in story:
        raise ValueError("Codex missing outline. Run Phase 1 first.")
    if "characters" not in story or "locations" not in story:
        raise ValueError("Codex missing characters/locations. Run Phase 1 first.")

    # Get author's screenplay style
    screenplay_style = get_screenplay_style_from_codex(codex)
    style_prompt = build_style_prompt(screenplay_style)

    print(f"\n>>> Using model: {model}")
    print(f">>> POV: {screenplay_style.pov}")
    print(f">>> Tense: {screenplay_style.tense}")
    print(f">>> Tone: {screenplay_style.tone}")
    print(f">>> Dialogue ratio: {screenplay_style.dialogue_ratio}")

    # Safety: Apply name substitution if mapping exists
    name_mapping = codex.get("story_metadata", {}).get("phase1_plotting", {}).get("character_metadata", {}).get("name_mapping", {})
    if not name_mapping:
        # Try old location
        name_mapping = codex.get("story_metadata", {}).get("phase2_characters", {}).get("name_mapping", {})

    if name_mapping:
        from src.story_workflows import substitute_names_in_outline
        outline_dict = story["outline"]
        outline_dict = substitute_names_in_outline(outline_dict, name_mapping)
        story["outline"] = outline_dict
        print(f">>> Applied name substitution ({len(name_mapping)} mappings)")

    outline = story["outline"]
    characters_json = json.dumps(story["characters"])
    locations_json = json.dumps(story["locations"])

    # Count expected scenes
    total_scenes = sum(
        len(act.get("scenes", []))
        for act in outline.get("acts", [])
    )

    print(f">>> Total scenes in outline: {total_scenes}")

    # Determine which steps to run
    steps_to_run = steps if steps is not None else [1, 2, 3]
    print(f">>> Running steps: {steps_to_run}")

    # Initialize metadata if needed
    if "story_metadata" not in codex:
        codex["story_metadata"] = {}
    if "phase2_screenplay" not in codex["story_metadata"]:
        codex["story_metadata"]["phase2_screenplay"] = {
            "phase": 2,
            "name": "Screenplay Writing",
            "writing_mode": "author-styled",
            "screenplay_style": screenplay_style.to_dict(),
            "steps_completed": [],
        }

    # Initialize narrative structure if needed
    if "narrative" not in codex["story"]:
        codex["story"]["narrative"] = {
            "title": outline.get("title", "Untitled"),
            "acts": []
        }

    # Initialize writer with style prompt
    writer = None
    if any(step in steps_to_run for step in [1, 2, 3]):
        writer = WriterAgent(model=model, style_prompt=style_prompt)

    step_timings = {}

    # STEP 1: Write Act 1 Prose
    if 1 in steps_to_run:
        print(f"\n{'='*60}")
        print("STEP 1: Write Act 1 Prose")
        print(f"{'='*60}")
        step_start = time.time()

        acts = outline.get("acts", [])
        if len(acts) < 1:
            raise ValueError("No acts found in outline. Run Phase 1 first.")

        act1 = acts[0]
        act1_scenes = act1.get("scenes", [])
        print(f">>> Writing {len(act1_scenes)} scenes for Act 1...")

        narrative_scenes = []
        previous_ending = None

        for idx, scene in enumerate(act1_scenes, 1):
            print(f"    Writing scene {idx}/{len(act1_scenes)}...")

            prose = writer.write_scene(
                scene=scene,
                characters=characters_json,
                locations=locations_json,
                previous_scene_ending=previous_ending
            )

            narrative_scenes.append({
                "scene_number": scene.get("scene_number", idx),
                "location": scene.get("location", "Unknown"),
                "characters": scene.get("characters", []),
                "time": "continuous",
                "text": prose,
                "paragraphs": prose.split("\n\n"),
                "sentences": split_into_sentences(prose)
            })

            previous_ending = prose[-300:] if len(prose) > 300 else prose

        # Update narrative
        narrative_acts = codex["story"]["narrative"].get("acts", [])
        act1_narrative = {
            "act_number": act1.get("act_number", 1),
            "act_name": act1.get("act_name", "Act 1"),
            "scenes": narrative_scenes
        }

        if len(narrative_acts) >= 1:
            narrative_acts[0] = act1_narrative
        else:
            narrative_acts.append(act1_narrative)

        codex["story"]["narrative"]["acts"] = narrative_acts
        codex["story_metadata"]["phase2_screenplay"]["steps_completed"].append(1)
        step_timings["step1_act1"] = round(time.time() - step_start, 2)
        save_codex(codex, codex_path)
        print(f">>> Act 1 saved ({len(narrative_scenes)} scenes) ({step_timings['step1_act1']:.1f}s)")

    # STEP 2: Write Act 2 Prose
    if 2 in steps_to_run:
        print(f"\n{'='*60}")
        print("STEP 2: Write Act 2 Prose")
        print(f"{'='*60}")
        step_start = time.time()

        acts = outline.get("acts", [])
        if len(acts) < 2:
            raise ValueError("Act 2 not found in outline.")

        act2 = acts[1]
        act2_scenes = act2.get("scenes", [])
        print(f">>> Writing {len(act2_scenes)} scenes for Act 2...")

        # Get continuity from Act 1
        previous_ending = None
        narrative_acts = codex["story"]["narrative"].get("acts", [])
        if len(narrative_acts) >= 1:
            act1_scenes = narrative_acts[0].get("scenes", [])
            if act1_scenes:
                last_text = act1_scenes[-1].get("text", "")
                previous_ending = last_text[-300:] if len(last_text) > 300 else last_text

        narrative_scenes = []

        for idx, scene in enumerate(act2_scenes, 1):
            print(f"    Writing scene {idx}/{len(act2_scenes)}...")

            prose = writer.write_scene(
                scene=scene,
                characters=characters_json,
                locations=locations_json,
                previous_scene_ending=previous_ending
            )

            narrative_scenes.append({
                "scene_number": scene.get("scene_number", idx),
                "location": scene.get("location", "Unknown"),
                "characters": scene.get("characters", []),
                "time": "continuous",
                "text": prose,
                "paragraphs": prose.split("\n\n"),
                "sentences": split_into_sentences(prose)
            })

            previous_ending = prose[-300:] if len(prose) > 300 else prose

        narrative_acts = codex["story"]["narrative"].get("acts", [])
        act2_narrative = {
            "act_number": act2.get("act_number", 2),
            "act_name": act2.get("act_name", "Act 2"),
            "scenes": narrative_scenes
        }

        if len(narrative_acts) >= 2:
            narrative_acts[1] = act2_narrative
        else:
            while len(narrative_acts) < 1:
                narrative_acts.append({"act_number": len(narrative_acts) + 1, "scenes": []})
            narrative_acts.append(act2_narrative)

        codex["story"]["narrative"]["acts"] = narrative_acts
        codex["story_metadata"]["phase2_screenplay"]["steps_completed"].append(2)
        step_timings["step2_act2"] = round(time.time() - step_start, 2)
        save_codex(codex, codex_path)
        print(f">>> Act 2 saved ({len(narrative_scenes)} scenes) ({step_timings['step2_act2']:.1f}s)")

    # STEP 3: Write Act 3 Prose
    if 3 in steps_to_run:
        print(f"\n{'='*60}")
        print("STEP 3: Write Act 3 Prose")
        print(f"{'='*60}")
        step_start = time.time()

        acts = outline.get("acts", [])
        if len(acts) < 3:
            raise ValueError("Act 3 not found in outline.")

        act3 = acts[2]
        act3_scenes = act3.get("scenes", [])
        print(f">>> Writing {len(act3_scenes)} scenes for Act 3...")

        # Get continuity from Act 2
        previous_ending = None
        narrative_acts = codex["story"]["narrative"].get("acts", [])
        if len(narrative_acts) >= 2:
            act2_scenes = narrative_acts[1].get("scenes", [])
            if act2_scenes:
                last_text = act2_scenes[-1].get("text", "")
                previous_ending = last_text[-300:] if len(last_text) > 300 else last_text

        narrative_scenes = []

        for idx, scene in enumerate(act3_scenes, 1):
            print(f"    Writing scene {idx}/{len(act3_scenes)}...")

            prose = writer.write_scene(
                scene=scene,
                characters=characters_json,
                locations=locations_json,
                previous_scene_ending=previous_ending
            )

            narrative_scenes.append({
                "scene_number": scene.get("scene_number", idx),
                "location": scene.get("location", "Unknown"),
                "characters": scene.get("characters", []),
                "time": "continuous",
                "text": prose,
                "paragraphs": prose.split("\n\n"),
                "sentences": split_into_sentences(prose)
            })

            previous_ending = prose[-300:] if len(prose) > 300 else prose

        narrative_acts = codex["story"]["narrative"].get("acts", [])
        act3_narrative = {
            "act_number": act3.get("act_number", 3),
            "act_name": act3.get("act_name", "Act 3"),
            "scenes": narrative_scenes
        }

        if len(narrative_acts) >= 3:
            narrative_acts[2] = act3_narrative
        else:
            while len(narrative_acts) < 2:
                narrative_acts.append({"act_number": len(narrative_acts) + 1, "scenes": []})
            narrative_acts.append(act3_narrative)

        codex["story"]["narrative"]["acts"] = narrative_acts
        codex["story_metadata"]["phase2_screenplay"]["steps_completed"].append(3)
        step_timings["step3_act3"] = round(time.time() - step_start, 2)
        save_codex(codex, codex_path)
        print(f">>> Act 3 saved ({len(narrative_scenes)} scenes) ({step_timings['step3_act3']:.1f}s)")

    # Reload final codex state
    codex = load_codex(codex_path)
    final_narrative = codex["story"]["narrative"]

    actual_scenes = sum(
        len(act.get("scenes", []))
        for act in final_narrative.get("acts", [])
    )

    print(f"\n>>> Screenplay saved to: {codex_path}")

    final_metadata = codex.get("story_metadata", {}).get("phase2_screenplay", {})

    return Phase2Result(
        codex_path=codex_path,
        narrative=final_narrative,
        metadata=final_metadata,
        total_scenes=actual_scenes,
        success=True,
        step_timings=step_timings,
    )


def main():
    """CLI entry point for standalone execution."""
    parser = argparse.ArgumentParser(
        description="Phase 2: Screenplay Writing (Author-styled prose)"
    )
    parser.add_argument(
        "codex_path",
        type=Path,
        help="Path to codex.json (must have outline, characters, locations)"
    )
    parser.add_argument(
        "--model",
        default=None,
        help=f"LLM model (default: from codex or {DEFAULT_MODEL})"
    )
    parser.add_argument(
        "--steps",
        nargs="+",
        type=int,
        choices=[1, 2, 3],
        help="Run specific steps (1: Act 1, 2: Act 2, 3: Act 3)"
    )
    args = parser.parse_args()

    if not args.codex_path.exists():
        print(f"ERROR: Codex not found: {args.codex_path}")
        sys.exit(1)

    result = run_phase2_screenplay(
        args.codex_path,
        model=args.model,
        steps=args.steps,
    )

    print(f"\n>>> Title: {result.narrative.get('title', 'Untitled')}")
    print(f">>> Total scenes written: {result.total_scenes}")


if __name__ == "__main__":
    main()
