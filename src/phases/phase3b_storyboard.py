#!/usr/bin/env python3
"""
Phase 3b: Storyboard Generation

Breaks completed narrative scenes into shots for AI video generation.
Uses industry-standard screenplay/storyboard format.

Each shot is 10-15 seconds with:
- Slugline (INT./EXT. LOCATION - TIME)
- Camera direction (shot size, movement)
- Action line (present tense)
- Dialogue with parentheticals
- Audio cues (SFX, music, ambient)
- Transition

Usage (standalone):
    uv run python -m src.phases.phase3b_storyboard forge/YYYYMMDD/codex.json
"""

import sys
import json
import argparse
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

# Add parent directory to path for proper package imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.story_agents.storyboard_agents import generate_scene_storyboard
from src.config import DEFAULT_MODEL


@dataclass
class Phase3bStoryboardResult:
    """Result of Phase 3b storyboard generation."""
    codex_path: Path
    scenes_processed: int
    total_shots_generated: int
    total_duration_seconds: int
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


def run_phase3b_storyboard(
    codex_path: Path,
    model: str = None,
    max_revisions: int = 2,
) -> Phase3bStoryboardResult:
    """
    Generate storyboards for all narrative scenes.

    Iterates through all acts and scenes in the narrative,
    generating a storyboard (shot list) for each scene.

    Args:
        codex_path: Path to codex.json (must have narrative from Phase 3)
        model: LLM model to use (default: from codex config)
        max_revisions: Maximum critique-revision cycles per scene

    Returns:
        Phase3bStoryboardResult with counts and status
    """
    codex_path = Path(codex_path)
    codex = load_codex(codex_path)

    # Get model from codex config
    codex_config = codex.get("config", {})
    model = model or codex_config.get("model", DEFAULT_MODEL)

    # Get narrative
    story = codex.get("story", {})
    narrative = story.get("narrative", {})
    acts = narrative.get("acts", [])

    if not acts:
        raise ValueError("Codex missing narrative. Run Phase 3 first.")

    # Apply name substitution to narrative scenes (in case old names slipped through)
    name_mapping = codex.get("story_metadata", {}).get("phase2_characters", {}).get("name_mapping", {})
    if name_mapping:
        from src.story_workflows import substitute_names_in_text
        substitution_count = 0
        for act in acts:
            for scene in act.get("scenes", []):
                # Fix character list
                old_chars = scene.get("characters", [])
                scene["characters"] = [
                    substitute_names_in_text(c, name_mapping)
                    for c in old_chars
                ]
                # Fix narrative text
                if scene.get("text"):
                    old_text = scene["text"]
                    scene["text"] = substitute_names_in_text(old_text, name_mapping)
                    if scene["text"] != old_text:
                        substitution_count += 1
        if substitution_count > 0:
            print(f">>> Applied name substitution to {substitution_count} scenes")

    # Get characters and locations for context
    characters = story.get("characters", [])
    locations = story.get("locations", [])

    print(f"\n{'='*60}")
    print("PHASE 3b: STORYBOARD GENERATION")
    print(f"{'='*60}")
    print(f">>> Using model: {model}")

    # Count total scenes
    total_scenes = sum(len(act.get("scenes", [])) for act in acts)
    print(f">>> Scenes to process: {total_scenes}")

    # Initialize metadata storage
    phase3b_metadata = {
        "model_used": model,
        "max_revisions": max_revisions,
        "storyboards": [],  # Metadata only, shots are embedded in scenes
    }

    total_shots = 0
    total_duration = 0
    scenes_processed = 0

    # Process each act and scene
    for act in acts:
        act_num = act.get("act_number", 0)
        act_name = act.get("act_name", f"Act {act_num}")
        scenes = act.get("scenes", [])

        print(f"\n>>> Act {act_num}: {act_name} ({len(scenes)} scenes)")

        for scene in scenes:
            scene_num = scene.get("scene_number", 0)
            scene_id = f"act{act_num}_scene{scene_num}"
            scene_text = scene.get("text", "")
            scene_location = scene.get("location", "Unknown Location")
            scene_characters = scene.get("characters", [])
            scene_time = scene.get("time", "DAY")

            if not scene_text:
                print(f"    Skipping {scene_id}: No narrative text")
                continue

            print(f"\n>>> Scene {scene_num}: {scene_location}")
            print(f"    Characters: {', '.join(scene_characters)}")
            print(f"    Time: {scene_time}")

            try:
                result = generate_scene_storyboard(
                    scene_id=scene_id,
                    scene_text=scene_text,
                    scene_location=scene_location,
                    scene_characters=scene_characters,
                    all_characters=characters,
                    all_locations=locations,
                    model=model,
                    max_revisions=max_revisions,
                )

                # Embed shots directly in the scene (at same level as text)
                scene["shots"] = result["storyboard"]["shots"]

                # Store metadata
                phase3b_metadata["storyboards"].append(result["metadata"])

                # Update counts
                num_shots = result["storyboard"]["shot_count"]
                duration = result["storyboard"]["total_duration_seconds"]
                total_shots += num_shots
                total_duration += duration
                scenes_processed += 1

                print(f"    Generated {num_shots} shots ({duration}s) | Revisions: {result['revision_count']}")

            except Exception as e:
                print(f"    ERROR: {e}")
                phase3b_metadata["storyboards"].append({
                    "scene_id": scene_id,
                    "error": str(e),
                })

    # Update codex (shots are now embedded in narrative scenes)
    codex["story"] = story

    # Store metadata
    if "story_metadata" not in codex:
        codex["story_metadata"] = {}
    codex["story_metadata"]["phase3b_storyboard"] = phase3b_metadata

    save_codex(codex, codex_path)

    print(f"\n{'='*60}")
    print("PHASE 3b COMPLETE")
    print(f"{'='*60}")
    print(f">>> Scenes processed: {scenes_processed}/{total_scenes}")
    print(f">>> Total shots: {total_shots}")
    print(f">>> Total duration: {total_duration}s ({total_duration // 60}m {total_duration % 60}s)")
    print(f">>> Saved to: {codex_path}")

    return Phase3bStoryboardResult(
        codex_path=codex_path,
        scenes_processed=scenes_processed,
        total_shots_generated=total_shots,
        total_duration_seconds=total_duration,
        success=True,
    )


def main():
    """CLI entry point for standalone execution."""
    parser = argparse.ArgumentParser(
        description="Phase 3b: Generate storyboards for narrative scenes"
    )
    parser.add_argument(
        "codex_path",
        type=Path,
        help="Path to codex.json (must have narrative from Phase 3)"
    )
    parser.add_argument(
        "--model",
        default=None,
        help=f"LLM model (default: from codex or {DEFAULT_MODEL})"
    )
    parser.add_argument(
        "--max-revisions",
        type=int,
        default=2,
        help="Maximum critique-revision cycles per scene (default: 2)"
    )
    args = parser.parse_args()

    if not args.codex_path.exists():
        print(f"ERROR: Codex not found: {args.codex_path}")
        sys.exit(1)

    try:
        result = run_phase3b_storyboard(
            args.codex_path,
            model=args.model,
            max_revisions=args.max_revisions,
        )

        if result.success:
            print(f"\n>>> Storyboard generation successful!")
            print(f"    Scenes: {result.scenes_processed}")
            print(f"    Shots: {result.total_shots_generated}")
            print(f"    Duration: {result.total_duration_seconds}s")
        else:
            print(f"\n>>> Generation failed: {result.error}")
            sys.exit(1)

    except Exception as e:
        print(f"\n>>> FATAL ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
