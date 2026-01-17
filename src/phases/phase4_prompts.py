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
import argparse
from pathlib import Path
from dataclasses import dataclass
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
from src.story_agents.shot_frame_prompt_agents import generate_shot_frame_prompts
from src.story_agents.video_prompt_agents import generate_video_prompt
from src.visual_styles import get_default_style
from src.config import DEFAULT_MODEL


@dataclass
class Phase4PromptsResult:
    """Result of Phase 4 prompt generation."""
    codex_path: Path
    character_prompt_count: int
    location_prompt_count: int
    poster_prompt_count: int
    shot_frame_prompt_count: int  # Step 4: First/last frame prompts per shot
    video_prompt_count: int  # Step 5: LTX screenplay video prompts per shot
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

    # =========================================================================
    # Step 1: Character Prompts
    # =========================================================================
    char_prompt_count = 0
    if 1 in steps_to_run and characters:
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

        print(f"\n>>> Step 1 complete: {char_prompt_count} character prompts generated")
    elif 1 in steps_to_run:
        print("\n>>> Step 1: No characters found, skipping character prompts")
    else:
        print("\n>>> Step 1: Skipped (not in requested steps)")

    # =========================================================================
    # Step 2: Location Prompts
    # =========================================================================
    loc_prompt_count = 0
    if 2 in steps_to_run and locations:
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

        print(f"\n>>> Step 2 complete: {loc_prompt_count} location prompts generated")
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

        # Update outline in story
        story["outline"] = outline
        print(f"\n>>> Step 3 complete: {poster_prompt_count} poster prompts generated")
    elif 3 in steps_to_run:
        print("\n>>> Step 3: No outline title found, skipping poster prompts")
    else:
        print("\n>>> Step 3: Skipped (not in requested steps)")

    # =========================================================================
    # Step 4: Shot Frame Prompts (First/Last frame for video generation)
    # =========================================================================
    shot_frame_count = 0
    narrative = story.get("narrative", {})
    acts = narrative.get("acts", [])

    # Count total shots for progress reporting
    total_shots = 0
    for act in acts:
        for scene in act.get("scenes", []):
            total_shots += len(scene.get("shots", []))

    if 4 in steps_to_run and total_shots > 0:
        print(f"\n>>> Step 4: Generating shot frame prompts...")
        print(f"    Total shots to process: {total_shots}")

        phase4_metadata["shot_frame_prompts"] = []
        shot_index = 0

        for act_idx, act in enumerate(acts):
            act_num = act.get("act_number", act_idx + 1)

            for scene_idx, scene in enumerate(act.get("scenes", [])):
                scene_num = scene.get("scene_number", scene_idx + 1)
                scene_location = scene.get("location", "Unknown")
                scene_text = scene.get("text", "")

                shots = scene.get("shots", [])
                if not shots:
                    continue

                print(f"\n    Act {act_num}, Scene {scene_num} ({scene_location}): {len(shots)} shots")

                for shot_idx, shot in enumerate(shots):
                    shot_index += 1
                    shot_num = shot.get("shot_number", shot_idx + 1)

                    print(f"      [{shot_index}/{total_shots}] Shot {shot_num}...")

                    # Build scene context from previous shots
                    prev_shots = shots[:shot_idx]
                    scene_context = f"Scene location: {scene_location}. "
                    if prev_shots:
                        last_action = prev_shots[-1].get("action", "")
                        scene_context += f"Previous shot ended with: {last_action}"
                    else:
                        scene_context += "Opening shot of scene."

                    try:
                        result = generate_shot_frame_prompts(
                            shot_data=shot,
                            codex=codex,
                            scene_context=scene_context,
                            visual_style=visual_style,
                            model=model,
                            max_revisions=2,
                        )

                        # Add frame prompts to shot data (at same level as shot_number)
                        shot["firstframe_prompt"] = result["firstframe_prompt"]
                        shot["lastframe_prompt"] = result["lastframe_prompt"]

                        # Store metadata
                        phase4_metadata["shot_frame_prompts"].append({
                            "act": act_num,
                            "scene": scene_num,
                            "shot": shot_num,
                            "location": shot.get("location", ""),
                            "characters": shot.get("characters_in_frame", []),
                            "revision_count": result["revision_count"],
                            "final_scores": result["final_scores"],
                            "critique_history": result["critique_history"],
                        })

                        shot_frame_count += 1
                        avg_score = result["final_scores"]["overall"]
                        print(f"        Score: {avg_score:.1f}/10 (revisions: {result['revision_count']})")

                    except Exception as e:
                        print(f"        ERROR: {e}")
                        phase4_metadata["shot_frame_prompts"].append({
                            "act": act_num,
                            "scene": scene_num,
                            "shot": shot_num,
                            "error": str(e),
                        })

        # Update narrative with modified shots
        codex["story"]["narrative"] = narrative

        print(f"\n>>> Step 4 complete: {shot_frame_count} shot frame prompts generated")
    elif 4 in steps_to_run:
        print("\n>>> Step 4: No shots found in narrative, skipping frame prompts")
        print("    (Run Phase 3b storyboard generation first)")
    else:
        print("\n>>> Step 4: Skipped (not in requested steps)")

    # =========================================================================
    # Step 5: Video Prompts (LTX Screenplay Format)
    # =========================================================================
    video_prompt_count = 0

    # Re-fetch narrative in case Step 4 modified it
    narrative = codex.get("story", {}).get("narrative", {})
    acts = narrative.get("acts", [])

    # Count total shots for progress
    total_shots = 0
    for act in acts:
        for scene in act.get("scenes", []):
            total_shots += len(scene.get("shots", []))

    if 5 in steps_to_run and total_shots > 0:
        print(f"\n>>> Step 5: Generating LTX video prompts...")
        print(f"    Total shots to process: {total_shots}")

        phase4_metadata["video_prompts"] = []
        shot_index = 0

        for act_idx, act in enumerate(acts):
            act_num = act.get("act_number", act_idx + 1)

            for scene_idx, scene in enumerate(act.get("scenes", [])):
                scene_num = scene.get("scene_number", scene_idx + 1)
                scene_location = scene.get("location", "Unknown")

                shots = scene.get("shots", [])
                if not shots:
                    continue

                print(f"\n    Act {act_num}, Scene {scene_num} ({scene_location}): {len(shots)} shots")

                for shot_idx, shot in enumerate(shots):
                    shot_index += 1
                    shot_num = shot.get("shot_number", shot_idx + 1)

                    print(f"      [{shot_index}/{total_shots}] Shot {shot_num}...")

                    # Build scene context from previous shots
                    prev_shots = shots[:shot_idx]
                    scene_context = f"Scene location: {scene_location}. "
                    if prev_shots:
                        last_action = prev_shots[-1].get("action", "")
                        scene_context += f"Previous shot ended with: {last_action}"
                    else:
                        scene_context += "Opening shot of scene."

                    try:
                        result = generate_video_prompt(
                            shot_data=shot,
                            codex=codex,
                            scene_context=scene_context,
                            visual_style=visual_style,
                            model=model,
                            max_revisions=2,
                        )

                        # Add video prompt to shot data (same level as shot_number)
                        shot["video_prompt"] = result["video_prompt"]

                        # Store metadata
                        phase4_metadata["video_prompts"].append({
                            "act": act_num,
                            "scene": scene_num,
                            "shot": shot_num,
                            "location": shot.get("location", ""),
                            "characters": shot.get("characters_in_frame", []),
                            "slugline": result["slugline"],
                            "dialogue_included": result["dialogue_included"],
                            "revision_count": result["revision_count"],
                            "final_scores": result["final_scores"],
                            "critique_history": result["critique_history"],
                        })

                        video_prompt_count += 1
                        avg_score = result["final_scores"]["overall"]
                        print(f"        Score: {avg_score:.1f}/10 (revisions: {result['revision_count']})")

                    except Exception as e:
                        print(f"        ERROR: {e}")
                        phase4_metadata["video_prompts"].append({
                            "act": act_num,
                            "scene": scene_num,
                            "shot": shot_num,
                            "error": str(e),
                        })

        # Update narrative with modified shots
        codex["story"]["narrative"] = narrative

        print(f"\n>>> Step 5 complete: {video_prompt_count} video prompts generated")
    elif 5 in steps_to_run:
        print("\n>>> Step 5: No shots found in narrative, skipping video prompts")
        print("    (Run Phase 3b storyboard generation first)")
    else:
        print("\n>>> Step 5: Skipped (not in requested steps)")

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
    print(f"    Shot frame prompts: {shot_frame_count}")
    print(f"    Video prompts: {video_prompt_count}")
    print(f">>> Saved to: {codex_path}")

    return Phase4PromptsResult(
        codex_path=codex_path,
        character_prompt_count=char_prompt_count,
        location_prompt_count=loc_prompt_count,
        poster_prompt_count=poster_prompt_count,
        shot_frame_prompt_count=shot_frame_count,
        video_prompt_count=video_prompt_count,
        success=True,
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
    print(f"    Shot frame prompts: {result.shot_frame_prompt_count}")
    print(f"    Video prompts: {result.video_prompt_count}")


if __name__ == "__main__":
    main()
