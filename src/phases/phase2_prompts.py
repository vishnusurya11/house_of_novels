#!/usr/bin/env python3
"""
Phase 2: Prompt Generation

Creates AI image generation prompts and audio scripts for story elements.
Step 1: Character Prompts
Step 2: Location Prompts
Step 3: Poster/Thumbnail Prompts (Multi-Agent with Jury Voting)
Step 4: Scene Image Prompts (One image per scene within chapters)
Step 5: YouTube Thumbnail Prompts (Agent Council with debate and voting)
Step 6: Audio Scripts (LLM-generated narrator + character dialogue per scene)

Usage (standalone):
    uv run python -m src.phases.phase2_prompts forge/xxx/codex.json
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
from src.story_agents.scene_image_prompt_agents import generate_scene_image_prompt  # noqa: F401
from src.story_agents.scene_image_prompt_agents import generate_layered_scene_image_prompt
from src.story_agents.chapter_image_prompt_agents import generate_chapter_image_prompt
from src.story_agents.thumbnail_agents import generate_thumbnail_prompts_via_council
# from src.story_agents.shot_frame_prompt_agents import generate_shot_frame_prompts
# from src.story_agents.video_prompt_agents import generate_video_prompt
from src.visual_styles import get_default_style
from src.config import (
    DEFAULT_MODEL,
    ANNOTATION_LLM_BASE_URL,
    ANNOTATION_LLM_MODEL,
    ANNOTATION_LLM_API_KEY,
    ANNOTATION_LLM_TEMPERATURE,
    ANNOTATION_LLM_MAX_TOKENS,
)
from src.tts.script_generator import AudioScriptGenerator


@dataclass
class Phase2PromptsResult:
    """Result of Phase 2 prompt generation."""
    codex_path: Path
    character_prompt_count: int
    location_prompt_count: int
    poster_prompt_count: int
    scene_image_prompt_count: int  # Step 4: Scene image prompts (one per scene)
    thumbnail_prompt_count: int  # Step 5: YouTube thumbnail prompts (Agent Council)
    audio_script_count: int = 0  # Step 6: Audio scripts (narrator + character dialogue)
    success: bool = True
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
    # deck_of_worlds is at ROOT level
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


def normalize_codex_for_phase2(codex: dict) -> dict:
    """
    Normalize new codex structure for Phase 2 agent compatibility.

    Handles field name differences between the new Phase 1 output and what
    Phase 2 agents expect:
    - Populates story.outline from story.chapters (title, subtitle)
    - Maps character_id → id, role → role_in_story, flat fields → physical dict
    - Maps scene characters_present → characters
    """
    story = codex.get("story", {})
    chapters_data = story.get("chapters", {})

    # 1. Populate outline from chapters title if outline is empty
    outline = story.get("outline", {})
    if not outline.get("title") and chapters_data.get("title"):
        outline["title"] = chapters_data["title"]
        outline["subtitle"] = chapters_data.get("subtitle", "")
        # Derive logline from theme foundation
        theme = story.get("theme_foundation", {})
        outline["logline"] = theme.get("central_question", "")
        # Derive protagonist/antagonist from characters
        for char in story.get("characters", []):
            role = char.get("role") or char.get("role_in_story", "")
            if role == "protagonist":
                outline["protagonist"] = char.get("name", "")
            elif role == "antagonist":
                outline["antagonist"] = char.get("name", "")
        story["outline"] = outline

    # 2. Normalize character fields (flat → nested physical + field renames)
    for char in story.get("characters", []):
        if not char.get("id") and char.get("character_id"):
            char["id"] = char["character_id"]
        if not char.get("role_in_story") and char.get("role"):
            char["role_in_story"] = char["role"]
        if not char.get("physical"):
            char["physical"] = {
                "height": char.get("height", ""),
                "build": char.get("body_build", ""),
                "hair_color": char.get("hair_color", ""),
                "hair": char.get("hair_color", ""),
                "eye_color": char.get("eye_color", ""),
                "eyes": char.get("eye_color", ""),
                "skin_tone": char.get("ethnicity", ""),
                "distinguishing_features": char.get("distinguishing_features", ""),
            }
        if not char.get("clothing") and char.get("costume"):
            char["clothing"] = char["costume"]

    # 3. Normalize scene fields
    for chapter in chapters_data.get("chapters", []):
        for scene in chapter.get("scenes", []):
            if not scene.get("characters") and scene.get("characters_present"):
                scene["characters"] = scene["characters_present"]

    return codex


def detect_genre(codex: dict) -> str:
    """
    Detect story genre from codex prompts for art style selection.

    Args:
        codex: Loaded codex dictionary

    Returns:
        Genre string (fantasy, sci-fi, noir, horror, etc.)
    """
    # deck_of_worlds and story_engine are at ROOT level

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


def run_phase2_prompts(
    codex_path: Path,
    model: str = None,
    steps: list[int] = None,
) -> Phase2PromptsResult:
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
        Phase2PromptsResult with counts of generated prompts
    """
    codex_path = Path(codex_path)
    codex = load_codex(codex_path)
    codex = normalize_codex_for_phase2(codex)

    # Determine which steps to run (1-6 are active steps)
    steps_to_run = steps if steps is not None else [1, 2, 3, 4, 5, 6]
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

    # Initialize metadata storage in new structure
    if "metadata" not in codex:
        codex["metadata"] = {}

    phase2_metadata = {
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
                phase2_metadata["character_prompts"].append({
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
                phase2_metadata["character_prompts"].append({
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
                phase2_metadata["location_prompts"].append({
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
                phase2_metadata["location_prompts"].append({
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
            phase2_metadata["poster_prompts"] = {
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

                phase2_metadata["poster_prompts"] = {
                    "art_style": art_style,
                    "fallback_used": True,
                }

            except Exception as fallback_e:
                print(f"    FALLBACK ERROR: {fallback_e}")
                outline["poster_prompts"] = []
                phase2_metadata["poster_prompts"] = {"error": str(fallback_e)}

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
    # Step 4: Scene Image Prompts (One image per scene)
    # =========================================================================
    scene_image_prompt_count = 0
    chapter_outline = story.get("chapters", {})
    chapters = chapter_outline.get("chapters", [])

    # Validate chapter structure before processing
    if not isinstance(chapters, list):
        print(f"  [WARN] chapters is {type(chapters).__name__}, expected list — resetting to []")
        chapters = []

    # Count total scenes for progress reporting
    total_scenes = sum(len(ch.get("scenes", [])) for ch in chapters)

    if 4 in steps_to_run and total_scenes > 0:
        step_start = time.time()
        print(f"\n>>> Step 4: Generating scene image prompts...")
        print(f"    Total scenes to process: {total_scenes}")

        phase2_metadata["scene_image_prompts"] = []

        scene_global_idx = 0
        for chapter_idx, chapter in enumerate(chapters):
            ch_num = chapter.get("chapter_number", chapter_idx + 1)
            ch_title = chapter.get("chapter_title", f"Chapter {ch_num}")

            for scene_idx, scene in enumerate(chapter.get("scenes", [])):
                sc_num = scene.get("scene_number", scene_idx + 1)
                scene_global_idx += 1

                print(f"\n    [{scene_global_idx}/{total_scenes}] Ch{ch_num} Sc{sc_num} - {ch_title}...")

                try:
                    result = generate_layered_scene_image_prompt(
                        scene_data=scene,
                        act_number=ch_num,
                        codex=codex,
                        visual_style=visual_style,
                        model=model,
                        max_revisions=2,
                    )

                    # Store layered result directly (already has prompt_type="layered")
                    result["chapter_number"] = ch_num
                    result["scene_number"] = sc_num
                    scene["scene_image_prompt"] = result

                    # Store metadata
                    char_names = [cl["character_name"] for cl in result.get("character_layers", [])]
                    phase2_metadata["scene_image_prompts"].append({
                        "chapter_number": ch_num,
                        "scene_number": sc_num,
                        "location": result["location_name"],
                        "characters": char_names,
                        "total_layers": result["total_layers"],
                        "revision_count": result["revision_count"],
                        "final_scores": result["final_scores"],
                        "critique_history": result["critique_history"],
                    })

                    scene_image_prompt_count += 1
                    avg_score = result["final_scores"].get("overall", 0)
                    print(f"        Score: {avg_score:.1f}/10 (layers: {result['total_layers']}, revisions: {result['revision_count']})")

                except Exception as e:
                    print(f"        ERROR: {e}")
                    phase2_metadata["scene_image_prompts"].append({
                        "chapter_number": ch_num,
                        "scene_number": sc_num,
                        "error": str(e),
                    })

        # Scene prompts are already updated directly in codex.story.chapters
        # No need to save separate narrative structure
        step_timings["step4_scene_images"] = round(time.time() - step_start, 2)
        save_codex(codex, codex_path)

        print(f"\n>>> Step 4 complete: {scene_image_prompt_count} scene image prompts generated ({step_timings['step4_scene_images']:.1f}s)")
    elif 4 in steps_to_run:
        print("\n>>> Step 4: No scenes found in narrative, skipping scene image prompts")
        print("    (Run Phase 1 narrative generation first)")
    else:
        print("\n>>> Step 4: Skipped (not in requested steps)")

    # =========================================================================
    # Step 5: YouTube Thumbnail Prompts (Agent Council with Debate & Voting)
    # =========================================================================
    thumbnail_prompt_count = 0

    if 5 in steps_to_run and outline.get("title"):
        step_start = time.time()
        print(f"\n>>> Step 5: Generating YouTube thumbnail prompts via Agent Council...")
        print(f"    Story title: {outline.get('title')}")
        print(f"    Visual style: {visual_style['name']}")

        try:
            # Run the agent council (4 agents debate and vote)
            thumbnail_result = generate_thumbnail_prompts_via_council(
                codex=codex,
                model=model,
                verbose=True,
            )

            # Store thumbnail data in codex
            codex["story"]["thumbnail"] = {
                "prompts": thumbnail_result["prompts"],
                "title": outline.get("title", ""),
                "style": thumbnail_result["style"],
                "metadata": {
                    "total_candidates": thumbnail_result["metadata"].get("total_candidates", 0),
                    "agent_contributions": thumbnail_result["metadata"].get("agent_contributions", {}),
                    "genre": thumbnail_result["metadata"].get("genre", ""),
                },
            }

            thumbnail_prompt_count = len(thumbnail_result["prompts"])

            # Store detailed metadata
            phase2_metadata["thumbnail_prompts"] = {
                "prompts_selected": thumbnail_prompt_count,
                "total_candidates": len(thumbnail_result.get("all_candidates", [])),
                "voting_results": thumbnail_result.get("voting_results", []),
                "agent_contributions": thumbnail_result["metadata"].get("agent_contributions", {}),
            }

            print(f"\n    Top {thumbnail_prompt_count} thumbnail prompts selected from {len(thumbnail_result.get('all_candidates', []))} candidates")

        except Exception as e:
            print(f"\n    ERROR in thumbnail generation: {e}")
            codex["story"]["thumbnail"] = {"error": str(e)}
            phase2_metadata["thumbnail_prompts"] = {"error": str(e)}

        # Save after Step 5
        step_timings["step5_thumbnails"] = round(time.time() - step_start, 2)
        save_codex(codex, codex_path)
        print(f"\n>>> Step 5 complete: {thumbnail_prompt_count} thumbnail prompts generated ({step_timings['step5_thumbnails']:.1f}s)")
    elif 5 in steps_to_run:
        print("\n>>> Step 5: No outline title found, skipping thumbnail prompts")
    else:
        print("\n>>> Step 5: Skipped (not in requested steps)")

    # =========================================================================
    # Step 6: Audio Scripts (LLM-generated narrator + character dialogue)
    # =========================================================================
    audio_script_count = 0

    if 6 in steps_to_run and total_scenes > 0:
        step_start = time.time()
        print(f"\n{'='*60}")
        print("STEP 6: Audio Script Generation")
        print(f"{'='*60}")
        print(f"    LLM: {ANNOTATION_LLM_MODEL} @ {ANNOTATION_LLM_BASE_URL}")
        print(f"    Total scenes: {total_scenes}")

        # Initialize the script generator with annotation LLM config
        script_gen = AudioScriptGenerator(
            base_url=ANNOTATION_LLM_BASE_URL,
            model=ANNOTATION_LLM_MODEL,
            api_key=ANNOTATION_LLM_API_KEY,
            temperature=ANNOTATION_LLM_TEMPERATURE,
            max_tokens=ANNOTATION_LLM_MAX_TOKENS,
        )

        # Reload codex in case earlier steps modified it
        codex = load_codex(codex_path)
        story = codex.get("story", {})
        chapters_data = story.get("chapters", {})
        chapters = chapters_data.get("chapters", [])
        codex_characters = story.get("characters", [])

        # Generate voice designs for all characters (single LLM call)
        print("    Generating voice designs for characters...")
        voice_designs = script_gen.generate_voice_descriptions(codex_characters)
        for char in codex_characters:
            char_id = char.get("character_id", "")
            if char_id in voice_designs:
                char["voice_design"] = voice_designs[char_id]
        # Store narrator voice design in chapters metadata
        narrator_vd = voice_designs.get("NARRATOR", "")
        if narrator_vd:
            chapters_data["narrator_voice_design"] = narrator_vd
        print(f"    -> {len(voice_designs)} voice designs generated")

        phase2_metadata["audio_scripts"] = []

        scene_global_idx = 0
        for chapter_idx, chapter in enumerate(chapters):
            ch_num = chapter.get("chapter_number", chapter_idx + 1)
            ch_title = chapter.get("chapter_title", f"Chapter {ch_num}")

            for scene_idx, scene in enumerate(chapter.get("scenes", [])):
                sc_num = scene.get("scene_number", scene_idx + 1)
                scene_global_idx += 1

                print(f"\n    [{scene_global_idx}/{total_scenes}] Ch{ch_num} Sc{sc_num}...")

                try:
                    audio_script = script_gen.generate_script(
                        scene=scene,
                        chapter_number=ch_num,
                        scene_number=sc_num,
                        codex_characters=codex_characters,
                    )

                    # Store audio script in the scene
                    scene["audio_script"] = audio_script

                    # Count speakers
                    speakers = set(e["speaker"] for e in audio_script)
                    print(f"        -> {len(audio_script)} chunks, speakers: {', '.join(sorted(speakers))}")

                    phase2_metadata["audio_scripts"].append({
                        "chapter_number": ch_num,
                        "scene_number": sc_num,
                        "chunk_count": len(audio_script),
                        "speakers": sorted(speakers),
                    })

                    audio_script_count += 1

                except Exception as e:
                    print(f"        ERROR: {e}")
                    phase2_metadata["audio_scripts"].append({
                        "chapter_number": ch_num,
                        "scene_number": sc_num,
                        "error": str(e),
                    })

        # Save after Step 6
        step_timings["step6_audio_scripts"] = round(time.time() - step_start, 2)
        save_codex(codex, codex_path)
        print(f"\n>>> Step 6 complete: {audio_script_count} audio scripts generated ({step_timings['step6_audio_scripts']:.1f}s)")
    elif 6 in steps_to_run:
        print("\n>>> Step 6: No scenes found, skipping audio scripts")
    else:
        print("\n>>> Step 6: Skipped (not in requested steps)")

    # Update codex
    codex["story"]["characters"] = characters
    codex["story"]["locations"] = locations
    codex["story"]["outline"] = story.get("outline", {})
    codex["metadata"]["phase_2"] = phase2_metadata
    save_codex(codex, codex_path)

    print(f"\n>>> Phase 2 complete!")
    print(f"    Character prompts: {char_prompt_count}")
    print(f"    Location prompts: {loc_prompt_count}")
    print(f"    Poster prompts: {poster_prompt_count}")
    print(f"    Scene image prompts: {scene_image_prompt_count}")
    print(f"    Thumbnail prompts: {thumbnail_prompt_count}")
    print(f"    Audio scripts: {audio_script_count}")
    print(f">>> Saved to: {codex_path}")

    return Phase2PromptsResult(
        codex_path=codex_path,
        character_prompt_count=char_prompt_count,
        location_prompt_count=loc_prompt_count,
        poster_prompt_count=poster_prompt_count,
        scene_image_prompt_count=scene_image_prompt_count,
        thumbnail_prompt_count=thumbnail_prompt_count,
        audio_script_count=audio_script_count,
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
        choices=[1, 2, 3, 4, 5, 6],
        help="Run specific steps (1: Characters, 2: Locations, 3: Posters, 4: Scene Images, 5: Thumbnails, 6: Audio Scripts). Example: --steps 1 2"
    )
    args = parser.parse_args()

    if not args.codex_path.exists():
        print(f"ERROR: Codex not found: {args.codex_path}")
        sys.exit(1)

    result = run_phase2_prompts(
        args.codex_path,
        model=args.model,
        steps=args.steps,
    )

    print(f"\n>>> Prompts generated:")
    print(f"    Character prompts: {result.character_prompt_count}")
    print(f"    Location prompts: {result.location_prompt_count}")
    print(f"    Poster prompts: {result.poster_prompt_count}")
    print(f"    Scene image prompts: {result.scene_image_prompt_count}")
    print(f"    Thumbnail prompts: {result.thumbnail_prompt_count}")
    print(f"    Audio scripts: {result.audio_script_count}")


if __name__ == "__main__":
    main()
