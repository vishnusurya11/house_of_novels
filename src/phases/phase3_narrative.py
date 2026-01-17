#!/usr/bin/env python3
"""
Phase 3: Narrative Prose Generation

Writes scene-by-scene prose for the complete story.
Requires Phases 1-2 to be complete.

Usage (standalone):
    uv run python -m src.phases.phase3_narrative forge/20260105143022/codex.json
"""

import sys
import json
import argparse
import re
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

# Add parent directory to path for proper package imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.story_agents.narrative_agents import (
    WriterAgent,
    StyleCriticAgent,
    ContinuityCriticAgent,
)
from src.story_agents.reviser_agent import ReviserAgent
from src.config import DEFAULT_MODEL, STORY_SCOPES, DEFAULT_STORY_SCOPE

CRITIQUE_CYCLES = 2  # Number of critique-revision cycles


@dataclass
class Phase3Result:
    """Result of Phase 3 narrative generation."""
    codex_path: Path
    narrative: dict
    metadata: dict
    total_scenes: int
    success: bool
    error: Optional[str] = None


def load_codex(codex_path: Path) -> dict:
    """Load codex JSON file."""
    with open(codex_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_codex(codex: dict, codex_path: Path) -> None:
    """Save codex JSON file."""
    with open(codex_path, "w", encoding="utf-8") as f:
        json.dump(codex, f, indent=2, ensure_ascii=False)


def split_into_sentences(text: str) -> list[str]:
    """
    Split text into sentences, preserving abbreviations.
    Removes newline characters and splits on sentence-ending periods.
    """
    # Remove newlines
    clean_text = text.replace("\n", " ")

    # Normalize multiple spaces
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()

    # Split on sentence-ending punctuation
    sentences = re.split(r'(?<=[.!?])\s+', clean_text)
    return [s.strip() for s in sentences if s.strip()]


def run_phase3_narrative(
    codex_path: Path,
    model: str = None,
    steps: list[int] = None,
) -> Phase3Result:
    """
    Generate narrative prose from outline/characters/locations in codex.

    Step 1: Write Act 1 Prose - scene-by-scene writing
    Step 2: Write Act 2 Prose - scene-by-scene writing
    Step 3: Write Act 3 Prose - scene-by-scene writing
    Step 4: Style & Continuity Critique - multi-agent critique
    Step 5: Revision & Final Narrative - apply critiques and revise

    Args:
        codex_path: Path to codex.json (must have outline, characters, locations)
        model: LLM model to use (default: from codex config)
        steps: List of step numbers to run (default: all steps [1,2,3,4,5])

    Returns:
        Phase3Result with narrative data
    """
    codex_path = Path(codex_path)
    codex = load_codex(codex_path)

    # Use codex config as default
    codex_config = codex.get("config", {})
    model = model or codex_config.get("model", DEFAULT_MODEL)

    # Validate Phases 1-2 completed
    story = codex.get("story", {})
    if "outline" not in story:
        raise ValueError("Codex missing outline. Run Phase 1 first.")
    if "characters" not in story or "locations" not in story:
        raise ValueError("Codex missing characters/locations. Run Phase 2 first.")

    # Safety: Apply name substitution if mapping exists (in case outline wasn't updated)
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

    print(f"\n>>> Using model: {model}")
    print(f">>> Total scenes in outline: {total_scenes}")

    # Determine which steps to run
    steps_to_run = steps if steps is not None else [1, 2, 3, 4, 5]
    print(f">>> Running steps: {steps_to_run}")

    # Initialize metadata if needed
    if "story_metadata" not in codex:
        codex["story_metadata"] = {}
    if "phase3_narrative" not in codex["story_metadata"]:
        codex["story_metadata"]["phase3_narrative"] = {
            "phase": 3,
            "name": "Narrative Writing",
            "writing_mode": "scene-by-scene",
            "cycles": [],
        }

    # Initialize narrative structure if needed
    if "narrative" not in codex["story"]:
        codex["story"]["narrative"] = {
            "title": outline.get("title", "Untitled"),
            "acts": []
        }

    # Initialize agents (only create if needed for requested steps)
    writer = None
    style_critic = None
    continuity_critic = None
    reviser = None

    if any(step in steps_to_run for step in [1, 2, 3]):
        writer = WriterAgent(model=model)
    if 4 in steps_to_run or 5 in steps_to_run:
        style_critic = StyleCriticAgent(model=model)
        continuity_critic = ContinuityCriticAgent(model=model)
    if 5 in steps_to_run:
        reviser = ReviserAgent(model=model)

    # STEP 1: Write Act 1 Prose
    if 1 in steps_to_run:
        print(f"\n{'='*60}")
        print("STEP 1: Write Act 1 Prose")
        print(f"{'='*60}")

        acts = outline.get("acts", [])
        if len(acts) < 1:
            print("ERROR: No acts found in outline")
        else:
            act1 = acts[0]
            act1_scenes = act1.get("scenes", [])
            print(f">>> Writing {len(act1_scenes)} scenes for Act 1...")

            narrative_scenes = []
            previous_ending = None

            for idx, scene in enumerate(act1_scenes, 1):
                print(f"    Writing scene {idx}/{len(act1_scenes)}: Scene {scene.get('scene_number', idx)}...")

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
                    "sentences": split_into_sentences(prose)
                })

                # Keep last 300 chars for continuity
                previous_ending = prose[-300:] if len(prose) > 300 else prose

            # Update or create Act 1 in narrative
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
            save_codex(codex, codex_path)
            print(f">>> Act 1 saved ({len(narrative_scenes)} scenes)")

    # STEP 2: Write Act 2 Prose
    if 2 in steps_to_run:
        print(f"\n{'='*60}")
        print("STEP 2: Write Act 2 Prose")
        print(f"{'='*60}")

        acts = outline.get("acts", [])
        if len(acts) < 2:
            print("ERROR: Act 2 not found in outline")
        else:
            act2 = acts[1]
            act2_scenes = act2.get("scenes", [])
            print(f">>> Writing {len(act2_scenes)} scenes for Act 2...")

            # Get continuity from Act 1's last scene
            previous_ending = None
            narrative_acts = codex["story"]["narrative"].get("acts", [])
            if len(narrative_acts) >= 1:
                act1_scenes = narrative_acts[0].get("scenes", [])
                if act1_scenes:
                    last_text = act1_scenes[-1].get("text", "")
                    previous_ending = last_text[-300:] if len(last_text) > 300 else last_text
                    print(f">>> Loaded Act 1 continuity ({len(previous_ending)} chars)")

            narrative_scenes = []

            for idx, scene in enumerate(act2_scenes, 1):
                print(f"    Writing scene {idx}/{len(act2_scenes)}: Scene {scene.get('scene_number', idx)}...")

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
                    "sentences": split_into_sentences(prose)
                })

                previous_ending = prose[-300:] if len(prose) > 300 else prose

            # Update or create Act 2 in narrative
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
            save_codex(codex, codex_path)
            print(f">>> Act 2 saved ({len(narrative_scenes)} scenes)")

    # STEP 3: Write Act 3 Prose
    if 3 in steps_to_run:
        print(f"\n{'='*60}")
        print("STEP 3: Write Act 3 Prose")
        print(f"{'='*60}")

        acts = outline.get("acts", [])
        if len(acts) < 3:
            print("ERROR: Act 3 not found in outline")
        else:
            act3 = acts[2]
            act3_scenes = act3.get("scenes", [])
            print(f">>> Writing {len(act3_scenes)} scenes for Act 3...")

            # Get continuity from Act 2's last scene
            previous_ending = None
            narrative_acts = codex["story"]["narrative"].get("acts", [])
            if len(narrative_acts) >= 2:
                act2_scenes = narrative_acts[1].get("scenes", [])
                if act2_scenes:
                    last_text = act2_scenes[-1].get("text", "")
                    previous_ending = last_text[-300:] if len(last_text) > 300 else last_text
                    print(f">>> Loaded Act 2 continuity ({len(previous_ending)} chars)")

            narrative_scenes = []

            for idx, scene in enumerate(act3_scenes, 1):
                print(f"    Writing scene {idx}/{len(act3_scenes)}: Scene {scene.get('scene_number', idx)}...")

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
                    "sentences": split_into_sentences(prose)
                })

                previous_ending = prose[-300:] if len(prose) > 300 else prose

            # Update or create Act 3 in narrative
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
            save_codex(codex, codex_path)
            print(f">>> Act 3 saved ({len(narrative_scenes)} scenes)")

    # STEP 4: Style & Continuity Critique
    if 4 in steps_to_run:
        print(f"\n{'='*60}")
        print("STEP 4: Style & Continuity Critique")
        print(f"{'='*60}")

        # Reload codex to get latest narrative
        codex = load_codex(codex_path)
        current_narrative = codex["story"]["narrative"]

        # Check if all 3 acts exist
        narrative_acts = current_narrative.get("acts", [])
        if len(narrative_acts) < 3:
            print(f"ERROR: Only {len(narrative_acts)} act(s) written. Need all 3 acts to run critique.")
            print("       Run steps 1-3 first to write all acts.")
        else:
            current_narrative_json = json.dumps(current_narrative, indent=2, ensure_ascii=False)

            print(">>> Getting style critique...")
            style_critique = style_critic.critique(current_narrative_json)

            print(">>> Getting continuity critique...")
            continuity_critique = continuity_critic.critique(
                current_narrative_json, characters_json, locations_json
            )

            # Store critiques in metadata
            critique_data = {
                "style_critique": style_critique.model_dump(),
                "continuity_critique": continuity_critique.model_dump(),
            }
            codex["story_metadata"]["phase3_narrative"]["critiques"] = critique_data

            save_codex(codex, codex_path)
            print(f">>> Critiques saved to metadata")
            print(f"    Style issues: {len(style_critique.model_dump().get('issues', []))}")
            print(f"    Continuity issues: {len(continuity_critique.model_dump().get('issues', []))}")

    # STEP 5: Revision & Final Narrative
    if 5 in steps_to_run:
        print(f"\n{'='*60}")
        print("STEP 5: Revision & Final Narrative")
        print(f"{'='*60}")

        # Reload codex to get latest data
        codex = load_codex(codex_path)

        # Check if critiques exist
        critiques = codex.get("story_metadata", {}).get("phase3_narrative", {}).get("critiques")
        if not critiques:
            print("ERROR: No critiques found. Run step 4 first.")
        else:
            current_narrative = codex["story"]["narrative"]
            style_critique = critiques["style_critique"]
            continuity_critique = critiques["continuity_critique"]

            # Revise act-by-act to avoid token limits
            # This prevents losing Acts 2 and 3 when the LLM hits output limits
            print(">>> Revising narrative act-by-act...")
            revised_acts = []
            total_scenes_revised = 0
            original_act_count = len(current_narrative.get("acts", []))

            for act in current_narrative.get("acts", []):
                act_number = act.get("act_number", len(revised_acts) + 1)
                act_scenes = act.get("scenes", [])
                print(f"    Revising Act {act_number} ({len(act_scenes)} scenes)...")

                try:
                    # Try structured revision for this single act
                    act_narrative = {
                        "title": current_narrative.get("title", ""),
                        "acts": [act]  # Single act to stay within token limits
                    }
                    revised_act = reviser.revise_narrative_structured(
                        act_narrative,
                        [json.dumps(style_critique), json.dumps(continuity_critique)]
                    )

                    # Extract the revised act and validate
                    revised_act_data = revised_act.model_dump()
                    if revised_act_data.get("acts") and len(revised_act_data["acts"]) > 0:
                        revised_act_dict = revised_act_data["acts"][0]
                        revised_scene_count = len(revised_act_dict.get("scenes", []))

                        # Validate we didn't lose scenes
                        if revised_scene_count >= len(act_scenes):
                            revised_acts.append(revised_act_dict)
                            total_scenes_revised += revised_scene_count
                            print(f"        Revised ({revised_scene_count} scenes)")
                        else:
                            # Lost scenes during revision, keep original
                            print(f"        Warning: Revision lost scenes ({revised_scene_count}/{len(act_scenes)}), keeping original")
                            revised_acts.append(act)
                            total_scenes_revised += len(act_scenes)
                    else:
                        # Revision returned empty, keep original
                        print(f"        Warning: Revision returned empty, keeping original")
                        revised_acts.append(act)
                        total_scenes_revised += len(act_scenes)

                except Exception as e:
                    print(f"        Warning: Revision failed ({e}), keeping original")
                    revised_acts.append(act)
                    total_scenes_revised += len(act_scenes)

            # Final validation: ensure we have all acts
            if len(revised_acts) != original_act_count:
                print(f">>> ERROR: Lost acts during revision! Original: {original_act_count}, Revised: {len(revised_acts)}")
                print(">>> Keeping original narrative to prevent data loss.")
            else:
                codex["story"]["narrative"] = {
                    "title": current_narrative.get("title", ""),
                    "acts": revised_acts,
                }
                save_codex(codex, codex_path)
                print(f">>> Revision complete ({total_scenes_revised} scenes across {len(revised_acts)} acts).")

    # Reload final codex state
    codex = load_codex(codex_path)
    final_narrative = codex["story"]["narrative"]

    # Count actual scenes written
    actual_scenes = sum(
        len(act.get("scenes", []))
        for act in final_narrative.get("acts", [])
    )

    print(f"\n>>> Narrative saved to: {codex_path}")

    # Get final metadata
    final_metadata = codex.get("story_metadata", {}).get("phase3_narrative", {})

    return Phase3Result(
        codex_path=codex_path,
        narrative=final_narrative,
        metadata=final_metadata,
        total_scenes=actual_scenes,
        success=True,
    )


def main():
    """CLI entry point for standalone execution."""
    parser = argparse.ArgumentParser(
        description="Phase 3: Generate narrative prose"
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
        choices=[1, 2, 3, 4, 5],
        help="Run specific steps (1: Act 1, 2: Act 2, 3: Act 3, 4: Critique, 5: Revision). Example: --steps 1 2"
    )
    args = parser.parse_args()

    if not args.codex_path.exists():
        print(f"ERROR: Codex not found: {args.codex_path}")
        sys.exit(1)

    result = run_phase3_narrative(
        args.codex_path,
        model=args.model,
        steps=args.steps,
    )

    print(f"\n>>> Title: {result.narrative.get('title', 'Untitled')}")
    print(f">>> Total scenes written: {result.total_scenes}")

    # Show first scene preview
    acts = result.narrative.get("acts", [])
    if acts and acts[0].get("scenes"):
        first_scene = acts[0]["scenes"][0]
        text = first_scene.get("text", "")
        preview = text[:200] + "..." if len(text) > 200 else text
        print(f"\n>>> First scene preview:")
        print(f"    {preview}")


if __name__ == "__main__":
    main()
