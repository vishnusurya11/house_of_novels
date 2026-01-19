#!/usr/bin/env python3
"""
Phase 4: Prompt Generation

Creates AI image generation prompts for characters, locations, posters, and video frames.
Step 1: Character Prompts
Step 2: Location Prompts
Step 3: Poster/Thumbnail Prompts (Multi-Agent with Jury Voting)
Step 4: Shot Frame Prompts (First/Last frame for each video shot)

Usage (standalone):
    uv run python -m src.phases.phase4_prompts forge/20260105143022/codex.json
"""

import sys
import json
import time
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

# Add parent directory to path for proper package imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.story_agents.character_prompt_agents import generate_character_prompt
from src.story_agents.location_prompt_agents import generate_location_prompt
from src.story_agents.image_prompt_agents import (
    CinematicPosterAgent,
    IllustratedPosterAgent,
    GraphicPosterAgent,
    PosterJurySupervisor,
    StoryPosterPromptAgent,
    StoryPosterCriticAgent,
)
from src.story_agents.scene_image_prompt_agents import generate_scene_image_prompt
# from src.story_agents.shot_frame_prompt_agents import generate_shot_frame_prompts
# from src.story_agents.video_prompt_agents import generate_video_prompt
from src.visual_styles import get_default_style
from src.config import DEFAULT_MODEL


@dataclass
class Phase4PromptsResult:
    """Result of Phase 4 prompt generation."""
    codex_path: Path
    character_prompt_count: int
    location_prompt_count: int
    poster_prompt_count: int
    scene_image_prompt_count: int  # Step 4: Scene image prompts (NEW)
    shot_frame_prompt_count: int  # Step 5: First/last frame prompts per shot (COMMENTED OUT)
    video_prompt_count: int  # Step 6: LTX screenplay video prompts per shot (COMMENTED OUT)
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


def extract_setting_prompt(codex: dict) -> str:
    """Extract setting_prompt from codex for style consistency."""
    dow_prompts = codex.get("deck_of_worlds", {}).get("prompts", [])
    return dow_prompts[0].get("prompt", "") if dow_prompts else ""


def get_visual_style_from_codex(codex: dict) -> dict:
    """
    Extract visual style config from codex.

    Args:
        codex: Loaded codex dictionary

    Returns:
        Visual style dict with name, prefix, suffix, description.
        Falls back to anime style if not found (backward compatibility).
    """
    visual_style = codex.get("config", {}).get("visual_style")

    if visual_style is None:
        # Backward compatibility: use anime as default
        return get_default_style()

    return visual_style


def detect_genre(codex: dict) -> str:
    """
    Detect story genre from codex prompts for art style selection.

    Args:
        codex: Loaded codex dictionary

    Returns:
        Genre string (fantasy, sci-fi, noir, horror, etc.)
    """
    # Get setting prompt from deck_of_worlds
    setting = codex.get("deck_of_worlds", {}).get("prompts", [{}])
    if setting:
        setting = setting[0].get("prompt", "")
    else:
        setting = ""

    # Also check story engine prompt
    story = codex.get("story_engine", {}).get("prompts", [{}])
    if story:
        story = story[0].get("prompt", "")
    else:
        story = ""

    combined = (setting + " " + story).lower()

    # Genre detection heuristics
    if any(w in combined for w in ["castle", "kingdom", "dragon", "magic", "sword", "wizard", "elf", "dwarf"]):
        return "fantasy"
    elif any(w in combined for w in ["spaceship", "planet", "galaxy", "robot", "cyber", "android", "starship"]):
        return "sci-fi"
    elif any(w in combined for w in ["detective", "murder", "crime", "mystery", "noir", "investigation"]):
        return "noir"
    elif any(w in combined for w in ["ghost", "haunted", "demon", "horror", "vampire", "zombie", "nightmare"]):
        return "horror"
    elif any(w in combined for w in ["romance", "love", "heart", "passion"]):
        return "romance"
    elif any(w in combined for w in ["western", "cowboy", "frontier", "sheriff"]):
        return "western"
    else:
        return "fantasy"  # default


def run_phase4_prompts(
    codex_path: Path,
    model: str = None,
    steps: list[int] = None,
) -> Phase4PromptsResult:
    """
    Generate image prompts for story elements in codex.

    Step 1: Character Prompts - detailed character portraits
    Step 2: Location Prompts - detailed environment/location images
    Step 3: Poster/Thumbnail Prompts - multi-agent jury voting
    Step 4: Shot Frame Prompts - first/last frame for each video shot
    Step 5: Video Prompts - LTX screenplay format prompts

    Args:
        codex_path: Path to codex.json (must have characters/locations from Phase 2)
        model: LLM model to use (default: from codex config)
        steps: List of step numbers to run (default: all steps [1,2,3,4,5])

    Returns:
        Phase4PromptsResult with counts of generated prompts
    """
    codex_path = Path(codex_path)
    codex = load_codex(codex_path)

    # Determine which steps to run
    steps_to_run = steps if steps is not None else [1, 2, 3, 4, 5]
    print(f"\n>>> Running steps: {steps_to_run}")

    # Get model from codex config
    codex_config = codex.get("config", {})
    model = model or codex_config.get("model", DEFAULT_MODEL)

    # Validate characters exist
    story = codex.get("story", {})
    characters = story.get("characters", [])
    locations = story.get("locations", [])

    if not characters and not locations:
        raise ValueError("Codex missing characters and locations. Run Phase 2 first.")

    # Get setting context for style consistency
    setting_context = extract_setting_prompt(codex)

    # Get visual style for all prompts
    visual_style = get_visual_style_from_codex(codex)

    print(f"\n>>> Using model: {model}")
    print(f">>> Visual Style: {visual_style['name']}")

    # Initialize metadata storage
    if "story_metadata" not in codex:
        codex["story_metadata"] = {}

    phase4_metadata = {
        "model_used": model,
        "character_prompts": [],
        "location_prompts": [],
    }

    # Step timing
    step_timings = {}

    # =========================================================================
    # Step 1: Character Prompts
    # =========================================================================
    char_prompt_count = 0
    if 1 in steps_to_run and characters:
        step_start = time.time()
        print(f"\n>>> Step 1: Generating character prompts...")
        print(f"    Characters to process: {len(characters)}")

        for i, char in enumerate(characters):
            char_name = char.get("name", f"Character {i+1}")
            print(f"\n>>> Character {i+1}/{len(characters)}: {char_name}")

            try:
                result = generate_character_prompt(
                    character_data=char,
                    setting_context=setting_context,
                    visual_style=visual_style,
                    model=model,
                    max_revisions=2,
                )

                # Store prompt in character data
                char["character_prompt"] = {
                    "prompt": result["prompt"],
                    "shot_type": result["shot_type"],
                    "key_features": result["key_features"],
                    "revision_count": result["revision_count"],
                    "final_scores": result["final_scores"],
                }

                # Store detailed metadata
                phase4_metadata["character_prompts"].append({
                    "character_name": char_name,
                    "final_prompt": result["prompt"],
                    "revision_count": result["revision_count"],
                    "final_scores": result["final_scores"],
                    "critique_history": result["critique_history"],
                })

                char_prompt_count += 1
                avg_score = sum(result["final_scores"].values()) / len(result["final_scores"])
                print(f"    Final score: {avg_score:.1f}/10 (revisions: {result['revision_count']})")

            except Exception as e:
                print(f"    ERROR generating prompt: {e}")
                phase4_metadata["character_prompts"].append({
                    "character_name": char_name,
                    "error": str(e),
                })

        # Save after Step 1 to preserve progress
        codex["story"]["characters"] = characters
        step_timings["step1_characters"] = round(time.time() - step_start, 2)
        save_codex(codex, codex_path)
        print(f"\n>>> Step 1 complete: {char_prompt_count} character prompts generated ({step_timings['step1_characters']:.1f}s)")
    elif 1 in steps_to_run:
        print("\n>>> Step 1: No characters found, skipping character prompts")
    else:
        print("\n>>> Step 1: Skipped (not in requested steps)")

    # =========================================================================
    # Step 2: Location Prompts
    # =========================================================================
    loc_prompt_count = 0
    if 2 in steps_to_run and locations:
        step_start = time.time()
        print(f"\n>>> Step 2: Generating location prompts...")
        print(f"    Locations to process: {len(locations)}")

        for i, loc in enumerate(locations):
            loc_name = loc.get("name", f"Location {i+1}")
            print(f"\n>>> Location {i+1}/{len(locations)}: {loc_name}")

            try:
                result = generate_location_prompt(
                    location_data=loc,
                    setting_context=setting_context,
                    visual_style=visual_style,
                    model=model,
                    max_revisions=2,
                )

                # Store prompt in location data
                loc["location_prompt"] = {
                    "prompt": result["prompt"],
                    "shot_type": result["shot_type"],
                    "time_of_day": result["time_of_day"],
                    "key_features": result["key_features"],
                    "revision_count": result["revision_count"],
                    "final_scores": result["final_scores"],
                }

                # Store detailed metadata
                phase4_metadata["location_prompts"].append({
                    "location_name": loc_name,
                    "final_prompt": result["prompt"],
                    "shot_type": result["shot_type"],
                    "time_of_day": result["time_of_day"],
                    "revision_count": result["revision_count"],
                    "final_scores": result["final_scores"],
                    "critique_history": result["critique_history"],
                })

                loc_prompt_count += 1
                avg_score = sum(result["final_scores"].values()) / len(result["final_scores"])
                print(f"    Final score: {avg_score:.1f}/10 (revisions: {result['revision_count']})")

            except Exception as e:
                print(f"    ERROR generating prompt: {e}")
                phase4_metadata["location_prompts"].append({
                    "location_name": loc_name,
                    "error": str(e),
                })

        # Save after Step 2 to preserve progress
        codex["story"]["locations"] = locations
        step_timings["step2_locations"] = round(time.time() - step_start, 2)
        save_codex(codex, codex_path)
        print(f"\n>>> Step 2 complete: {loc_prompt_count} location prompts generated ({step_timings['step2_locations']:.1f}s)")
    elif 2 in steps_to_run:
        print("\n>>> Step 2: No locations found, skipping location prompts")
    else:
        print("\n>>> Step 2: Skipped (not in requested steps)")

    # =========================================================================
    # Step 3: Poster/Thumbnail Prompts (Multi-Agent with Jury Voting)
    # =========================================================================
    poster_prompt_count = 0
    outline = story.get("outline", {})

    if 3 in steps_to_run and outline.get("title"):
        step_start = time.time()
        print(f"\n>>> Step 3: Generating poster/thumbnail prompts...")
        print(f"    Story title: {outline.get('title')}")

        # Detect art style from genre
        art_style = detect_genre(codex)
        print(f"    Art style: {art_style} (auto-detected)")

        try:
            # Step 3a: Generate 9 prompts (3 agents × 3 compositions each)
            print("\n    Step 3a: Generating 9 poster candidates...")

            cinematic = CinematicPosterAgent(model=model)
            illustrated = IllustratedPosterAgent(model=model)
            graphic = GraphicPosterAgent(model=model)

            all_prompts = []

            print("      CINEMATIC agent generating 3 prompts...")
            cinematic_prompts = cinematic.generate_prompts(
                outline, characters, locations, art_style, visual_style
            )
            all_prompts.extend(cinematic_prompts)
            print(f"      -> Generated {len(cinematic_prompts)} cinematic prompts")

            print("      ILLUSTRATED agent generating 3 prompts...")
            illustrated_prompts = illustrated.generate_prompts(
                outline, characters, locations, art_style, visual_style
            )
            all_prompts.extend(illustrated_prompts)
            print(f"      -> Generated {len(illustrated_prompts)} illustrated prompts")

            print("      GRAPHIC agent generating 3 prompts...")
            graphic_prompts = graphic.generate_prompts(
                outline, characters, locations, art_style, visual_style
            )
            all_prompts.extend(graphic_prompts)
            print(f"      -> Generated {len(graphic_prompts)} graphic prompts")

            print(f"      Total candidates: {len(all_prompts)}")

            # Step 3b: Jury voting to select top 3
            print("\n    Step 3b: Jury voting on top 3...")

            jury = PosterJurySupervisor(model=model)
            voting_results = jury.run_voting(all_prompts, outline)

            # Store ONLY winners in outline (the actual prompts to use)
            outline["poster_prompts"] = voting_results["winners"]

            poster_prompt_count = len(voting_results["winners"])

            print(f"\n    Top {poster_prompt_count} selected:")
            for i, winner in enumerate(voting_results["winners"], 1):
                score = winner.get("score", 0)
                agent = winner.get("agent", "Unknown")
                comp = winner.get("composition", "unknown")
                print(f"      #{i}: {agent} - {comp} ({score} pts)")

            # Store ALL metadata in phase4_metadata (not in outline)
            phase4_metadata["poster_prompts"] = {
                "art_style": art_style,
                "candidates_generated": len(all_prompts),
                "winners_selected": poster_prompt_count,
                "all_poster_candidates": voting_results["all_prompts"],
                "voting_metadata": voting_results["voting_metadata"],
            }

        except Exception as e:
            print(f"\n    ERROR in multi-agent system: {e}")
            print("    Falling back to single poster generation...")

            try:
                poster_agent = StoryPosterPromptAgent(model=model)
                poster_critic = StoryPosterCriticAgent(model=model)

                result = poster_agent.generate_prompt(
                    outline, characters, locations, art_style, visual_style
                )

                critique = poster_critic.critique(result.prompt, outline, characters)

                if critique.severity in ["moderate", "major"]:
                    result = poster_agent.revise_prompt(result.prompt, critique.model_dump())

                outline["poster_prompts"] = [{
                    "agent": "FALLBACK",
                    "composition": "single",
                    "prompt": result.prompt,
                    "style": result.style_applied,
                    "score": 0
                }]

                poster_prompt_count = 1
                print(f"    Fallback generated 1 poster prompt")

                phase4_metadata["poster_prompts"] = {
                    "art_style": art_style,
                    "fallback_used": True,
                }

            except Exception as fallback_e:
                print(f"    FALLBACK ERROR: {fallback_e}")
                outline["poster_prompts"] = []
                phase4_metadata["poster_prompts"] = {"error": str(fallback_e)}

        # Update outline in story and save after Step 3
        story["outline"] = outline
        codex["story"]["outline"] = outline
        step_timings["step3_posters"] = round(time.time() - step_start, 2)
        save_codex(codex, codex_path)
        print(f"\n>>> Step 3 complete: {poster_prompt_count} poster prompts generated ({step_timings['step3_posters']:.1f}s)")
    elif 3 in steps_to_run:
        print("\n>>> Step 3: No outline title found, skipping poster prompts")
    else:
        print("\n>>> Step 3: Skipped (not in requested steps)")

    # =========================================================================
    # Step 4: Scene Image Prompts (One representative image per scene)
    # =========================================================================
    scene_image_prompt_count = 0
    narrative = story.get("narrative", {})
    acts = narrative.get("acts", [])

    # Count total scenes for progress reporting
    total_scenes = 0
    for act in acts:
        total_scenes += len(act.get("scenes", []))

    if 4 in steps_to_run and total_scenes > 0:
        step_start = time.time()
        print(f"\n>>> Step 4: Generating scene image prompts...")
        print(f"    Total scenes to process: {total_scenes}")

        phase4_metadata["scene_image_prompts"] = []
        scene_index = 0

        for act_idx, act in enumerate(acts):
            act_num = act.get("act_number", act_idx + 1)

            for scene_idx, scene in enumerate(act.get("scenes", [])):
                scene_index += 1
                scene_num = scene.get("scene_number", scene_idx + 1)
                scene_location = scene.get("location", "Unknown")

                print(f"\n    [{scene_index}/{total_scenes}] Act {act_num}, Scene {scene_num} ({scene_location})...")

                try:
                    result = generate_scene_image_prompt(
                        scene_data=scene,
                        act_number=act_num,
                        codex=codex,
                        visual_style=visual_style,
                        model=model,
                        max_revisions=2,
                    )

                    # Add scene image prompt to scene data
                    scene["scene_image_prompt"] = {
                        "prompt": result["prompt"],
                        "location_name": result["location_name"],
                        "characters_in_scene": result["characters_in_scene"],
                        "scene_summary": result["scene_summary"],
                        "composition_notes": result["composition_notes"],
                        "mood_lighting": result["mood_lighting"],
                        "revision_count": result["revision_count"],
                        "final_scores": result["final_scores"],
                    }

                    # Store metadata
                    phase4_metadata["scene_image_prompts"].append({
                        "act": act_num,
                        "scene": scene_num,
                        "location": scene_location,
                        "characters": scene.get("characters", []),
                        "revision_count": result["revision_count"],
                        "final_scores": result["final_scores"],
                        "critique_history": result["critique_history"],
                    })

                    scene_image_prompt_count += 1
                    avg_score = result["final_scores"]["overall"]
                    print(f"        Score: {avg_score:.1f}/10 (revisions: {result['revision_count']})")

                except Exception as e:
                    print(f"        ERROR: {e}")
                    phase4_metadata["scene_image_prompts"].append({
                        "act": act_num,
                        "scene": scene_num,
                        "error": str(e),
                    })

        # Update narrative with modified scenes and save after Step 4
        codex["story"]["narrative"] = narrative
        step_timings["step4_scene_images"] = round(time.time() - step_start, 2)
        save_codex(codex, codex_path)

        print(f"\n>>> Step 4 complete: {scene_image_prompt_count} scene image prompts generated ({step_timings['step4_scene_images']:.1f}s)")
    elif 4 in steps_to_run:
        print("\n>>> Step 4: No scenes found in narrative, skipping scene image prompts")
        print("    (Run Phase 3 narrative generation first)")
    else:
        print("\n>>> Step 4: Skipped (not in requested steps)")

    # =========================================================================
    # Step 5: Shot Frame Prompts (COMMENTED OUT)
    # =========================================================================
    shot_frame_count = 0
    # NOTE: Shot frame prompts are commented out for now
    # Uncomment when ready to generate first/last frame prompts for video shots
    #
    # if 5 in steps_to_run:
    #     # ... shot frame prompt generation code ...
    #     pass
    print("\n>>> Step 5 (Shot Frame Prompts): COMMENTED OUT")

    # =========================================================================
    # Step 6: Video Prompts (COMMENTED OUT)
    # =========================================================================
    video_prompt_count = 0
    # NOTE: Video prompts are commented out for now
    # Uncomment when ready to generate LTX screenplay video prompts
    #
    # if 6 in steps_to_run:
    #     # ... video prompt generation code ...
    #     pass
    print("\n>>> Step 6 (Video Prompts): COMMENTED OUT")

    # Update codex
    codex["story"]["characters"] = characters
    codex["story"]["locations"] = locations
    codex["story"]["outline"] = story.get("outline", {})
    codex["story_metadata"]["phase4_prompts"] = phase4_metadata
    save_codex(codex, codex_path)

    print(f"\n>>> Phase 4 complete!")
    print(f"    Character prompts: {char_prompt_count}")
    print(f"    Location prompts: {loc_prompt_count}")
    print(f"    Poster prompts: {poster_prompt_count}")
    print(f"    Scene image prompts: {scene_image_prompt_count}")
    print(f"    Shot frame prompts: {shot_frame_count} (commented out)")
    print(f"    Video prompts: {video_prompt_count} (commented out)")
    print(f">>> Saved to: {codex_path}")

    return Phase4PromptsResult(
        codex_path=codex_path,
        character_prompt_count=char_prompt_count,
        location_prompt_count=loc_prompt_count,
        poster_prompt_count=poster_prompt_count,
        scene_image_prompt_count=scene_image_prompt_count,
        shot_frame_prompt_count=shot_frame_count,
        video_prompt_count=video_prompt_count,
        success=True,
        step_timings=step_timings,
    )


def main():
    """CLI entry point for standalone execution."""
    parser = argparse.ArgumentParser(
        description="Phase 4: Generate image prompts"
    )
    parser.add_argument(
        "codex_path",
        type=Path,
        help="Path to codex.json (must have characters from Phase 2)"
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
        help="Run specific steps (1: Characters, 2: Locations, 3: Posters, 4: Shot Frames, 5: Video). Example: --steps 1 2"
    )
    args = parser.parse_args()

    if not args.codex_path.exists():
        print(f"ERROR: Codex not found: {args.codex_path}")
        sys.exit(1)

    result = run_phase4_prompts(
        args.codex_path,
        model=args.model,
        steps=args.steps,
    )

    print(f"\n>>> Prompts generated:")
    print(f"    Character prompts: {result.character_prompt_count}")
    print(f"    Location prompts: {result.location_prompt_count}")
    print(f"    Poster prompts: {result.poster_prompt_count}")
    print(f"    Scene image prompts: {result.scene_image_prompt_count}")
    print(f"    Shot frame prompts: {result.shot_frame_prompt_count} (commented out)")
    print(f"    Video prompts: {result.video_prompt_count} (commented out)")


if __name__ == "__main__":
    main()
