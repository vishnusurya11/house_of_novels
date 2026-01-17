#!/usr/bin/env python3
"""
Phase 5: Image & Media Generation

Generates images and media using ComfyUI based on prompts from Phase 4.

Step 1: Generate Static Images (characters, locations, posters)
Step 2: Generate Shot Frames (future)
Step 3: Generate Videos (future)
Step 4: Generate Audio/Music (future)

Usage (standalone):
    uv run python -m src.phases.phase5_generation forge/20260113195058/codex.json
    uv run python -m src.phases.phase5_generation codex.json --steps 1
    uv run python -m src.phases.phase5_generation codex.json --comfyui-url http://192.168.1.100:8188
"""

import sys
import json
import argparse
import random
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

# Add parent directory to path for proper package imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.comfyui_trigger import trigger_comfy
from src.config import (
    DEFAULT_COMFYUI_URL,
    DEFAULT_COMFYUI_TIMEOUT,
    COMFYUI_WORKFLOWS,
    COMFYUI_OUTPUT_DIR,
    VIDEO_GENERATION_TIMEOUT,
    should_run_step,
)


@dataclass
class Phase5GenerationResult:
    """Result of Phase 5 media generation."""
    codex_path: Path
    poster_count: int
    character_portrait_count: int  # Future
    location_image_count: int      # Future
    shot_frame_count: int          # Future
    video_count: int               # Future
    audio_count: int               # Future
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


def generate_seed() -> int:
    """Generate a random 15-digit seed for ComfyUI."""
    return random.randint(100000000000000, 999999999999999)


def get_timestamp_from_codex_path(codex_path: Path) -> str:
    """Extract timestamp from codex path for output organization."""
    name = codex_path.stem
    if "_" in name:
        return name.split("_", 1)[1]
    return codex_path.parent.name


def sanitize_filename(name: str) -> str:
    """Convert name to lowercase with underscores for filename."""
    import re
    # Replace spaces with underscores, remove apostrophes and special chars
    clean = name.lower().replace(" ", "_").replace("'", "")
    # Remove any remaining non-alphanumeric characters except underscores
    clean = re.sub(r'[^a-z0-9_]', '', clean)
    return clean


def generate_video(
    video_prompt: str,
    firstframe_path: str,
    filename_prefix: str,
    label: str,
    comfyui_url: str,
    video_workflow: dict,
    comfyui_output_dir: str,
    timeout: int = VIDEO_GENERATION_TIMEOUT,
) -> tuple[bool | None, dict]:
    """
    Generate video using LTX 2.0 i2v workflow.

    Args:
        video_prompt: Motion/action description for the video
        firstframe_path: Relative path to first frame (from codex, e.g., "api/.../image_00001_.png")
        filename_prefix: Output path prefix for SaveVideo node
        label: Human-readable label for logging
        comfyui_url: ComfyUI API URL
        video_workflow: Loaded video workflow dict (already parsed JSON)
        comfyui_output_dir: ComfyUI output directory for full path resolution
        timeout: Timeout in seconds (default: 900s / 15min)

    Returns:
        (success, generation_data) where:
        - success=True: Generation completed
        - success=False: Generation failed (non-fatal)
        - success=None: Connection error (fatal)
    """
    import copy
    import os

    workflow = copy.deepcopy(video_workflow)

    # Generate random seed (15 digits)
    seed = generate_seed()

    # Convert relative firstframe path to FULL ABSOLUTE PATH
    # Codex stores: "api/20260115201245/firstframes/act1/scene1/shot1/image_00001_.png"
    # Need: "D:\...\ComfyUI\output\api\20260115201245\firstframes\act1\scene1\shot1\image_00001_.png"
    full_firstframe_path = os.path.join(comfyui_output_dir, firstframe_path.replace("/", os.sep))

    # Replace workflow nodes
    # Node 92:3 - Text prompt (CLIPTextEncode)
    workflow["92:3"]["inputs"]["text"] = video_prompt

    # Node 75 - Output filename prefix (SaveVideo)
    workflow["75"]["inputs"]["filename_prefix"] = filename_prefix

    # Node 98 - Input image (LoadImage) - FULL PATH REQUIRED
    workflow["98"]["inputs"]["image"] = full_firstframe_path

    # Node 92:11 - Random noise seed
    workflow["92:11"]["inputs"]["noise_seed"] = seed

    # Node 92:67 - Second random noise seed (both need same seed)
    workflow["92:67"]["inputs"]["noise_seed"] = seed

    gen_data = {
        "prompt_id": None,
        "status": "pending",
        "execution_time": None,
        "output_path": None,
        "seed": seed,
        "generated_at": datetime.now().isoformat(),
        "error": None,
        "input_image": full_firstframe_path,
    }

    try:
        # Use WebSocket-based trigger with the modified workflow dict
        # The trigger_comfy expects a path, but we need to pass the workflow directly
        # We'll write a temp file or use direct API call
        import tempfile
        import json as json_module

        # Write workflow to temp file for trigger_comfy
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json_module.dump(workflow, f, indent=2)
            temp_workflow_path = f.name

        try:
            result = trigger_comfy(
                workflow_json_path=temp_workflow_path,
                replacements={},  # Already applied replacements to workflow
                comfyui_url=comfyui_url,
                timeout=timeout,
            )
        finally:
            # Clean up temp file
            os.unlink(temp_workflow_path)

        if result.get("status") == "completed":
            gen_data["prompt_id"] = result.get("prompt_id")
            gen_data["status"] = "completed"
            gen_data["execution_time"] = result.get("execution_time")
            # ComfyUI appends _00001_.mp4 to filename_prefix
            gen_data["output_path"] = f"{filename_prefix}_00001_.mp4"
            print(f"          Completed in {result.get('execution_time', 0):.1f}s")
            return True, gen_data
        else:
            gen_data["status"] = "failed"
            gen_data["error"] = result.get("error", "Unknown error")
            print(f"          FAILED: {gen_data['error']}")
            return False, gen_data

    except ConnectionError as e:
        gen_data["status"] = "connection_error"
        gen_data["error"] = str(e)
        print(f"          Connection error: {e}")
        return None, gen_data

    except TimeoutError as e:
        gen_data["status"] = "timeout"
        gen_data["error"] = str(e)
        print(f"          Timeout: {e}")
        return False, gen_data

    except Exception as e:
        gen_data["status"] = "failed"
        gen_data["error"] = str(e)
        print(f"          ERROR: {e}")
        return False, gen_data


def run_phase5_generation(
    codex_path: Path,
    comfyui_url: str = None,
    workflow_path: str = None,
    steps: list[int] = None,
    timeout: int = None,
) -> Phase5GenerationResult:
    """
    Generate images and media using ComfyUI.

    Step 1: Generate Static Images (characters, locations, posters)
    Step 2: Generate Shot Frames (future)
    Step 3: Generate Videos (future)
    Step 4: Generate Audio/Music (future)

    Args:
        codex_path: Path to codex.json (must have prompts from Phase 4)
        comfyui_url: ComfyUI API URL (default: from config)
        workflow_path: Path to ComfyUI workflow JSON (default: from config)
        steps: List of step numbers to run (default: [1])
        timeout: Timeout in seconds for each generation (default: 300)

    Returns:
        Phase5GenerationResult with counts of generated media
    """
    codex_path = Path(codex_path)
    codex = load_codex(codex_path)

    # Get configuration
    comfyui_url = comfyui_url or DEFAULT_COMFYUI_URL
    workflow_path = workflow_path or COMFYUI_WORKFLOWS.get("image")
    timeout = timeout or DEFAULT_COMFYUI_TIMEOUT
    steps_to_run = steps if steps is not None else [1]

    # Filter steps based on GENERATION_STEPS config
    # Map: Phase 5 step number -> config position
    # Step 1 (static images) -> position 0
    # Step 2 (shot frames) -> position 1
    # Step 3 (videos) -> position 2
    # Step 4 (audio) -> position 3
    STEP_CONFIG_MAP = {1: 0, 2: 1, 3: 2, 4: 3}
    original_steps = steps_to_run.copy()
    steps_to_run = [s for s in steps_to_run if should_run_step(STEP_CONFIG_MAP.get(s, -1))]

    # Report any skipped steps
    skipped_steps = [s for s in original_steps if s not in steps_to_run]
    if skipped_steps:
        print(f">>> Steps {skipped_steps} skipped by GENERATION_STEPS config")

    # Get timestamp for output paths
    timestamp = get_timestamp_from_codex_path(codex_path)

    print(f"\n{'='*60}")
    print("PHASE 5: MEDIA GENERATION")
    print(f"{'='*60}")
    print(f">>> ComfyUI URL: {comfyui_url}")
    print(f">>> Workflow: {workflow_path}")
    print(f">>> Timeout: {timeout}s")
    print(f">>> Running steps: {steps_to_run}")

    # Initialize metadata
    if "story_metadata" not in codex:
        codex["story_metadata"] = {}

    phase5_metadata = {
        "comfyui_url": comfyui_url,
        "workflow_used": Path(workflow_path).name if workflow_path else None,
        "steps_executed": [],
    }

    # Counters
    poster_count = 0
    character_portrait_count = 0
    location_image_count = 0
    shot_frame_count = 0
    video_count = 0
    audio_count = 0

    # =========================================================================
    # Step 1: Generate Static Images (Characters, Locations, Posters)
    # =========================================================================
    if 1 in steps_to_run:
        print(f"\n{'='*60}")
        print("STEP 1: Generate Static Images")
        print(f"{'='*60}")

        # Helper function to handle ComfyUI generation with error handling
        def generate_image(prompt_text: str, filename_prefix: str, label: str) -> tuple[bool, dict]:
            """Generate a single image. Returns (success, generation_data)."""
            seed = generate_seed()
            try:
                result = trigger_comfy(
                    workflow_json_path=workflow_path,
                    replacements={
                        "10_filename_prefix": filename_prefix,
                        "5_seed": seed,
                        "11_text": prompt_text,
                    },
                    comfyui_url=comfyui_url,
                    timeout=timeout,
                )

                generation_data = {
                    "prompt_id": result["prompt_id"],
                    "status": result["status"],
                    "execution_time": result["execution_time"],
                    "output_path": f"{filename_prefix}_00001_.png",
                    "seed": seed,
                    "generated_at": datetime.now().isoformat(),
                }

                if result["status"] == "completed":
                    print(f"        Completed in {result['execution_time']:.1f}s")
                    return True, generation_data
                else:
                    error_msg = result.get("error", "Unknown error")
                    print(f"        Failed: {error_msg}")
                    generation_data["error"] = error_msg
                    return False, generation_data

            except ConnectionError as e:
                print(f"        Connection error: {e}")
                return None, {  # None indicates fatal error
                    "status": "error",
                    "error": str(e),
                    "generated_at": datetime.now().isoformat(),
                }

            except TimeoutError as e:
                print(f"        Timeout: {e}")
                return False, {
                    "status": "timeout",
                    "error": str(e),
                    "seed": seed,
                    "generated_at": datetime.now().isoformat(),
                }

            except Exception as e:
                print(f"        Error: {e}")
                return False, {
                    "status": "error",
                    "error": str(e),
                    "generated_at": datetime.now().isoformat(),
                }

        # ---------------------------------------------------------------------
        # Step 1a: Character Portraits
        # ---------------------------------------------------------------------
        print(f"\n--- 1a: Character Portraits ---")
        characters = codex.get("story", {}).get("characters", [])

        if not characters:
            print(">>> No characters found, skipping")
        else:
            print(f">>> Generating {len(characters)} character portraits...")

            for i, character in enumerate(characters):
                char_prompt = character.get("character_prompt", {})
                prompt_text = char_prompt.get("prompt", "")
                char_name = character.get("name", f"character_{i+1}")

                if not prompt_text:
                    print(f"    [{i+1}/{len(characters)}] {char_name} - No prompt, skipping")
                    continue

                filename_prefix = f"api/{timestamp}/characters/{sanitize_filename(char_name)}"
                print(f"    [{i+1}/{len(characters)}] {char_name}")

                success, gen_data = generate_image(prompt_text, filename_prefix, char_name)

                char_prompt["generation"] = gen_data

                if success is None:
                    # Fatal connection error
                    print(f"\n>>> ERROR: Cannot connect to ComfyUI at {comfyui_url}")
                    print(">>> Make sure ComfyUI is running and try again.")
                    save_codex(codex, codex_path)
                    return Phase5GenerationResult(
                        codex_path=codex_path,
                        poster_count=poster_count,
                        character_portrait_count=character_portrait_count,
                        location_image_count=location_image_count,
                        shot_frame_count=shot_frame_count,
                        video_count=video_count,
                        audio_count=audio_count,
                        success=False,
                        error=f"Cannot connect to ComfyUI: {gen_data['error']}",
                    )
                elif success:
                    character_portrait_count += 1

            print(f">>> Characters complete: {character_portrait_count}/{len(characters)}")

        # ---------------------------------------------------------------------
        # Step 1b: Location Images
        # ---------------------------------------------------------------------
        print(f"\n--- 1b: Location Images ---")
        locations = codex.get("story", {}).get("locations", [])

        if not locations:
            print(">>> No locations found, skipping")
        else:
            print(f">>> Generating {len(locations)} location images...")

            for i, location in enumerate(locations):
                loc_prompt = location.get("location_prompt", {})
                prompt_text = loc_prompt.get("prompt", "")
                loc_name = location.get("name", f"location_{i+1}")

                if not prompt_text:
                    print(f"    [{i+1}/{len(locations)}] {loc_name} - No prompt, skipping")
                    continue

                filename_prefix = f"api/{timestamp}/locations/{sanitize_filename(loc_name)}"
                print(f"    [{i+1}/{len(locations)}] {loc_name}")

                success, gen_data = generate_image(prompt_text, filename_prefix, loc_name)

                loc_prompt["generation"] = gen_data

                if success is None:
                    # Fatal connection error
                    print(f"\n>>> ERROR: Cannot connect to ComfyUI at {comfyui_url}")
                    print(">>> Make sure ComfyUI is running and try again.")
                    save_codex(codex, codex_path)
                    return Phase5GenerationResult(
                        codex_path=codex_path,
                        poster_count=poster_count,
                        character_portrait_count=character_portrait_count,
                        location_image_count=location_image_count,
                        shot_frame_count=shot_frame_count,
                        video_count=video_count,
                        audio_count=audio_count,
                        success=False,
                        error=f"Cannot connect to ComfyUI: {gen_data['error']}",
                    )
                elif success:
                    location_image_count += 1

            print(f">>> Locations complete: {location_image_count}/{len(locations)}")

        # ---------------------------------------------------------------------
        # Step 1c: Poster Images
        # ---------------------------------------------------------------------
        print(f"\n--- 1c: Poster Images ---")
        poster_prompts = codex.get("story", {}).get("outline", {}).get("poster_prompts", [])

        if not poster_prompts:
            print(">>> No poster prompts found, skipping")
        else:
            print(f">>> Generating {len(poster_prompts)} poster images...")

            for i, poster in enumerate(poster_prompts):
                prompt_text = poster.get("prompt", "")
                if not prompt_text:
                    print(f"    [{i+1}/{len(poster_prompts)}] No prompt text, skipping")
                    continue

                filename_prefix = f"api/{timestamp}/posters/poster_{i+1:04d}"
                agent = poster.get("agent", "Unknown")
                composition = poster.get("composition", "unknown")
                print(f"    [{i+1}/{len(poster_prompts)}] {agent} - {composition}")

                success, gen_data = generate_image(prompt_text, filename_prefix, f"poster_{i+1}")

                poster["generation"] = gen_data

                if success is None:
                    # Fatal connection error
                    print(f"\n>>> ERROR: Cannot connect to ComfyUI at {comfyui_url}")
                    print(">>> Make sure ComfyUI is running and try again.")
                    save_codex(codex, codex_path)
                    return Phase5GenerationResult(
                        codex_path=codex_path,
                        poster_count=poster_count,
                        character_portrait_count=character_portrait_count,
                        location_image_count=location_image_count,
                        shot_frame_count=shot_frame_count,
                        video_count=video_count,
                        audio_count=audio_count,
                        success=False,
                        error=f"Cannot connect to ComfyUI: {gen_data['error']}",
                    )
                elif success:
                    poster_count += 1

            print(f">>> Posters complete: {poster_count}/{len(poster_prompts)}")

        # Update metadata
        phase5_metadata["steps_executed"].append(1)
        phase5_metadata["total_characters_generated"] = character_portrait_count
        phase5_metadata["total_locations_generated"] = location_image_count
        phase5_metadata["total_posters_generated"] = poster_count

        print(f"\n>>> Step 1 complete:")
        print(f"    Character portraits: {character_portrait_count}")
        print(f"    Location images: {location_image_count}")
        print(f"    Poster images: {poster_count}")

    # =========================================================================
    # Step 2: Generate Shot Frames (First & Last Frames)
    # =========================================================================
    if 2 in steps_to_run:
        print(f"\n{'='*60}")
        print("STEP 2: Generate Shot Frames")
        print(f"{'='*60}")

        # Helper function for image generation (same as Step 1)
        def generate_image(prompt_text: str, filename_prefix: str, label: str) -> tuple[bool, dict]:
            """Generate a single image. Returns (success, generation_data)."""
            seed = generate_seed()
            try:
                result = trigger_comfy(
                    workflow_json_path=workflow_path,
                    replacements={
                        "10_filename_prefix": filename_prefix,
                        "5_seed": seed,
                        "11_text": prompt_text,
                    },
                    comfyui_url=comfyui_url,
                    timeout=timeout,
                )

                generation_data = {
                    "prompt_id": result["prompt_id"],
                    "status": result["status"],
                    "execution_time": result["execution_time"],
                    "output_path": f"{filename_prefix}_00001_.png",
                    "seed": seed,
                    "generated_at": datetime.now().isoformat(),
                }

                if result["status"] == "completed":
                    print(f"          Completed in {result['execution_time']:.1f}s")
                    return True, generation_data
                else:
                    error_msg = result.get("error", "Unknown error")
                    print(f"          Failed: {error_msg}")
                    generation_data["error"] = error_msg
                    return False, generation_data

            except ConnectionError as e:
                print(f"          Connection error: {e}")
                return None, {
                    "status": "error",
                    "error": str(e),
                    "generated_at": datetime.now().isoformat(),
                }

            except TimeoutError as e:
                print(f"          Timeout: {e}")
                return False, {
                    "status": "timeout",
                    "error": str(e),
                    "seed": seed,
                    "generated_at": datetime.now().isoformat(),
                }

            except Exception as e:
                print(f"          Error: {e}")
                return False, {
                    "status": "error",
                    "error": str(e),
                    "generated_at": datetime.now().isoformat(),
                }

        # Count total shots first
        narrative = codex.get("story", {}).get("narrative", {})
        total_shots = 0
        for act in narrative.get("acts", []):
            for scene in act.get("scenes", []):
                total_shots += len(scene.get("shots", []))

        if total_shots == 0:
            print(">>> No shots found in narrative, skipping")
        else:
            print(f">>> Generating frames for {total_shots} shots...")
            print(f">>> Total images: {total_shots * 2} (first + last frames)")

            shot_global_idx = 0
            firstframe_count = 0
            lastframe_count = 0

            for act_idx, act in enumerate(narrative.get("acts", [])):
                act_num = act.get("act_number", act_idx + 1)
                act_name = act.get("act_name", f"Act {act_num}")

                print(f"\n>>> Act {act_num}: {act_name}")

                for scene_idx, scene in enumerate(act.get("scenes", [])):
                    scene_num = scene.get("scene_number", scene_idx + 1)
                    scene_location = scene.get("location", "unknown")
                    shots = scene.get("shots", [])

                    if not shots:
                        continue

                    print(f"    Scene {scene_num} ({scene_location}): {len(shots)} shots")

                    for shot_idx, shot in enumerate(shots):
                        shot_num = shot.get("shot_number", shot_idx + 1)
                        shot_global_idx += 1

                        # --- First Frame ---
                        firstframe_prompt = shot.get("firstframe_prompt", "")
                        if firstframe_prompt:
                            filename_prefix = f"api/{timestamp}/firstframes/act{act_num}/scene{scene_num}/shot{shot_num}/image"
                            print(f"      [{shot_global_idx}/{total_shots}] Shot {shot_num} - First frame...")

                            success, gen_data = generate_image(
                                firstframe_prompt, filename_prefix, f"act{act_num}_scene{scene_num}_shot{shot_num}_first"
                            )

                            shot["firstframe_generation"] = gen_data

                            if success is None:
                                # Fatal connection error - save and exit
                                print(f"\n>>> ERROR: Cannot connect to ComfyUI at {comfyui_url}")
                                save_codex(codex, codex_path)
                                return Phase5GenerationResult(
                                    codex_path=codex_path,
                                    poster_count=poster_count,
                                    character_portrait_count=character_portrait_count,
                                    location_image_count=location_image_count,
                                    shot_frame_count=firstframe_count + lastframe_count,
                                    video_count=video_count,
                                    audio_count=audio_count,
                                    success=False,
                                    error=f"Cannot connect to ComfyUI: {gen_data['error']}",
                                )
                            elif success:
                                firstframe_count += 1

                        # --- Last Frame ---
                        lastframe_prompt = shot.get("lastframe_prompt", "")
                        if lastframe_prompt:
                            filename_prefix = f"api/{timestamp}/lastframes/act{act_num}/scene{scene_num}/shot{shot_num}/image"
                            print(f"      [{shot_global_idx}/{total_shots}] Shot {shot_num} - Last frame...")

                            success, gen_data = generate_image(
                                lastframe_prompt, filename_prefix, f"act{act_num}_scene{scene_num}_shot{shot_num}_last"
                            )

                            shot["lastframe_generation"] = gen_data

                            if success is None:
                                # Fatal connection error - save and exit
                                print(f"\n>>> ERROR: Cannot connect to ComfyUI at {comfyui_url}")
                                save_codex(codex, codex_path)
                                return Phase5GenerationResult(
                                    codex_path=codex_path,
                                    poster_count=poster_count,
                                    character_portrait_count=character_portrait_count,
                                    location_image_count=location_image_count,
                                    shot_frame_count=firstframe_count + lastframe_count,
                                    video_count=video_count,
                                    audio_count=audio_count,
                                    success=False,
                                    error=f"Cannot connect to ComfyUI: {gen_data['error']}",
                                )
                            elif success:
                                lastframe_count += 1

                        # Save codex periodically (every shot) to preserve progress
                        save_codex(codex, codex_path)

            shot_frame_count = firstframe_count + lastframe_count
            phase5_metadata["steps_executed"].append(2)
            phase5_metadata["total_firstframes_generated"] = firstframe_count
            phase5_metadata["total_lastframes_generated"] = lastframe_count

            print(f"\n>>> Step 2 complete:")
            print(f"    First frames: {firstframe_count}/{total_shots}")
            print(f"    Last frames: {lastframe_count}/{total_shots}")
            print(f"    Total shot frames: {shot_frame_count}")

    # =========================================================================
    # Step 3: Generate Videos (LTX 2.0 Image-to-Video)
    # =========================================================================
    if 3 in steps_to_run:
        print(f"\n{'='*60}")
        print("STEP 3: Generate Videos (LTX 2.0 i2v)")
        print(f"{'='*60}")

        # Load video workflow
        video_workflow_path = COMFYUI_WORKFLOWS.get("video")
        if not video_workflow_path:
            print(">>> ERROR: Video workflow not configured in COMFYUI_WORKFLOWS")
        elif not Path(video_workflow_path).exists():
            print(f">>> ERROR: Video workflow not found at {video_workflow_path}")
        else:
            with open(video_workflow_path, "r", encoding="utf-8") as f:
                video_workflow = json.load(f)

            # Get ComfyUI output directory for full path resolution
            comfyui_output_dir = COMFYUI_OUTPUT_DIR

            # Count shots with firstframe AND video_prompt
            narrative = codex.get("story", {}).get("narrative", {})
            eligible_shots = 0
            for act in narrative.get("acts", []):
                for scene in act.get("scenes", []):
                    for shot in scene.get("shots", []):
                        has_firstframe = shot.get("firstframe_generation", {}).get("output_path")
                        has_video_prompt = shot.get("video_prompt")
                        if has_firstframe and has_video_prompt:
                            eligible_shots += 1

            if eligible_shots == 0:
                print(">>> No eligible shots found (need firstframe + video_prompt)")
                print(">>> Run Step 2 first to generate firstframes")
            else:
                print(f">>> Generating videos for {eligible_shots} shots...")
                print(f">>> Timeout: {VIDEO_GENERATION_TIMEOUT}s ({VIDEO_GENERATION_TIMEOUT // 60} minutes) per video")

                shot_global_idx = 0
                video_generated_count = 0

                for act_idx, act in enumerate(narrative.get("acts", [])):
                    act_num = act.get("act_number", act_idx + 1)
                    act_name = act.get("act_name", f"Act {act_num}")

                    print(f"\n>>> Act {act_num}: {act_name}")

                    for scene_idx, scene in enumerate(act.get("scenes", [])):
                        scene_num = scene.get("scene_number", scene_idx + 1)
                        scene_location = scene.get("location", "unknown")
                        shots = scene.get("shots", [])

                        if not shots:
                            continue

                        # Count eligible shots in this scene
                        scene_eligible = sum(
                            1 for s in shots
                            if s.get("firstframe_generation", {}).get("output_path")
                            and s.get("video_prompt")
                        )
                        if scene_eligible > 0:
                            print(f"    Scene {scene_num} ({scene_location}): {scene_eligible} videos")

                        for shot_idx, shot in enumerate(shots):
                            shot_num = shot.get("shot_number", shot_idx + 1)

                            # Check prerequisites
                            firstframe_path = shot.get("firstframe_generation", {}).get("output_path")
                            video_prompt = shot.get("video_prompt")

                            if not firstframe_path:
                                continue  # No firstframe, skip
                            if not video_prompt:
                                continue  # No video prompt, skip

                            shot_global_idx += 1

                            # Output path for video
                            filename_prefix = f"api/{timestamp}/videos/act{act_num}/scene{scene_num}/shot{shot_num}/video"
                            print(f"      [{shot_global_idx}/{eligible_shots}] Shot {shot_num} - Video...")

                            success, gen_data = generate_video(
                                video_prompt=video_prompt,
                                firstframe_path=firstframe_path,
                                filename_prefix=filename_prefix,
                                label=f"act{act_num}_scene{scene_num}_shot{shot_num}",
                                comfyui_url=comfyui_url,
                                video_workflow=video_workflow,
                                comfyui_output_dir=comfyui_output_dir,
                            )

                            # Store generation data on the shot
                            shot["video_generation"] = gen_data

                            if success is None:
                                # Fatal connection error - save and exit
                                print(f"\n>>> ERROR: Cannot connect to ComfyUI at {comfyui_url}")
                                save_codex(codex, codex_path)
                                return Phase5GenerationResult(
                                    codex_path=codex_path,
                                    poster_count=poster_count,
                                    character_portrait_count=character_portrait_count,
                                    location_image_count=location_image_count,
                                    shot_frame_count=shot_frame_count,
                                    video_count=video_generated_count,
                                    audio_count=audio_count,
                                    success=False,
                                    error=f"Cannot connect to ComfyUI: {gen_data['error']}",
                                )
                            elif success:
                                video_generated_count += 1

                            # Save codex after each video to preserve progress
                            save_codex(codex, codex_path)

                video_count = video_generated_count
                phase5_metadata["steps_executed"].append(3)
                phase5_metadata["total_videos_generated"] = video_generated_count

                print(f"\n>>> Step 3 complete:")
                print(f"    Videos generated: {video_generated_count}/{eligible_shots}")

    # =========================================================================
    # Step 4: Generate Audio/Music (Future)
    # =========================================================================
    if 4 in steps_to_run:
        print(f"\n{'='*60}")
        print("STEP 4: Generate Audio/Music")
        print(f"{'='*60}")
        print(">>> Not yet implemented")
        phase5_metadata["steps_executed"].append(4)

    # Save metadata and codex
    codex["story_metadata"]["phase5_generation"] = phase5_metadata
    save_codex(codex, codex_path)

    print(f"\n>>> Phase 5 complete!")
    print(f"    Poster images: {poster_count}")
    print(f"    Character portraits: {character_portrait_count}")
    print(f"    Location images: {location_image_count}")
    print(f"    Shot frames: {shot_frame_count}")
    print(f"    Videos: {video_count}")
    print(f"    Audio: {audio_count}")
    print(f">>> Saved to: {codex_path}")

    return Phase5GenerationResult(
        codex_path=codex_path,
        poster_count=poster_count,
        character_portrait_count=character_portrait_count,
        location_image_count=location_image_count,
        shot_frame_count=shot_frame_count,
        video_count=video_count,
        audio_count=audio_count,
        success=True,
    )


def main():
    """CLI entry point for standalone execution."""
    parser = argparse.ArgumentParser(
        description="Phase 5: Generate images and media using ComfyUI"
    )
    parser.add_argument(
        "codex_path",
        type=Path,
        help="Path to codex.json (must have prompts from Phase 4)"
    )
    parser.add_argument(
        "--comfyui-url",
        default=None,
        help=f"ComfyUI API URL (default: {DEFAULT_COMFYUI_URL})"
    )
    parser.add_argument(
        "--workflow",
        default=None,
        help="Path to ComfyUI workflow JSON (default: from config)"
    )
    parser.add_argument(
        "--steps",
        nargs="+",
        type=int,
        choices=[1, 2, 3, 4],
        help="Run specific steps (1: Static Images [chars/locs/posters], 2: Shot Frames, 3: Videos, 4: Audio)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        help=f"Timeout per generation in seconds (default: {DEFAULT_COMFYUI_TIMEOUT})"
    )
    args = parser.parse_args()

    if not args.codex_path.exists():
        print(f"ERROR: Codex not found: {args.codex_path}")
        sys.exit(1)

    result = run_phase5_generation(
        args.codex_path,
        comfyui_url=args.comfyui_url,
        workflow_path=args.workflow,
        steps=args.steps,
        timeout=args.timeout,
    )

    if not result.success:
        print(f"\n>>> ERROR: {result.error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
