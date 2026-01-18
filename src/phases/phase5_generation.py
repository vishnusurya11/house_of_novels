#!/usr/bin/env python3
"""
Phase 5: Image & Media Generation

Generates images and media using ComfyUI based on prompts from Phase 4.

Step 1: Generate Audio (VibeVoice TTS for each sentence)
Step 2: Generate Static Images (characters, locations, posters)
Step 3: Generate Scene Images (scene-specific images with characters in location)
Step 4: Generate Videos (COMMENTED OUT)

Usage (standalone):
    uv run python -m src.phases.phase5_generation forge/20260113195058/codex.json
    uv run python -m src.phases.phase5_generation codex.json --steps 1 2
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
    COMFYUI_OUTPUT_DIR,
    VIDEO_GENERATION_TIMEOUT,
    AUDIO_GENERATION_TIMEOUT,
    should_run_step,
    get_workflow_path,
)


@dataclass
class Phase5GenerationResult:
    """Result of Phase 5 media generation."""
    codex_path: Path
    poster_count: int
    character_portrait_count: int
    location_image_count: int
    scene_image_count: int
    shot_frame_count: int
    video_count: int
    audio_count: int
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


def generate_audio(
    sentence_text: str,
    filename_prefix: str,
    label: str,
    comfyui_url: str,
    audio_workflow: dict,
    timeout: int = AUDIO_GENERATION_TIMEOUT,
) -> tuple[bool | None, dict]:
    """
    Generate audio for a sentence using VibeVoice workflow.

    Args:
        sentence_text: The sentence to convert to speech
        filename_prefix: Output path prefix for SaveAudioMP3 node
        label: Human-readable label for logging
        comfyui_url: ComfyUI API URL
        audio_workflow: Loaded audio workflow dict
        timeout: Timeout in seconds (default: 300s / 5min)

    Returns:
        (success, generation_data) where:
        - success=True: Generation completed
        - success=False: Generation failed (non-fatal)
        - success=None: Connection error (fatal)
    """
    import copy
    import os
    import tempfile

    workflow = copy.deepcopy(audio_workflow)

    # Replace workflow nodes
    # Node 44 - Text input (VibeVoiceSingleSpeakerNode)
    workflow["44"]["inputs"]["text"] = sentence_text

    # Node 45 - Output filename prefix (SaveAudioMP3)
    workflow["45"]["inputs"]["filename_prefix"] = filename_prefix

    gen_data = {
        "prompt_id": None,
        "status": "pending",
        "execution_time": None,
        "output_path": None,
        "generated_at": datetime.now().isoformat(),
        "error": None,
        "text_length": len(sentence_text),
    }

    try:
        # Write workflow to temp file for trigger_comfy
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(workflow, f, indent=2)
            temp_workflow_path = f.name

        try:
            result = trigger_comfy(
                workflow_json_path=temp_workflow_path,
                replacements={},
                comfyui_url=comfyui_url,
                timeout=timeout,
            )
        finally:
            os.unlink(temp_workflow_path)

        if result.get("status") == "completed":
            gen_data["prompt_id"] = result.get("prompt_id")
            gen_data["status"] = "completed"
            gen_data["execution_time"] = result.get("execution_time")
            # ComfyUI appends _00001_.mp3 to filename_prefix
            gen_data["output_path"] = f"{filename_prefix}_00001_.mp3"
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

    Step 1: Generate Audio (VibeVoice TTS for each sentence)
    Step 2: Generate Static Images (characters, locations, posters)
    Step 3: Generate Shot Frames (COMMENTED OUT)
    Step 4: Generate Videos (COMMENTED OUT)

    Args:
        codex_path: Path to codex.json (must have prompts from Phase 4)
        comfyui_url: ComfyUI API URL (default: from config)
        workflow_path: Path to ComfyUI workflow JSON (default: from config)
        steps: List of step numbers to run (default: [1, 2])
        timeout: Timeout in seconds for each generation (default: 300)

    Returns:
        Phase5GenerationResult with counts of generated media
    """
    codex_path = Path(codex_path)
    codex = load_codex(codex_path)

    # Get configuration
    comfyui_url = comfyui_url or DEFAULT_COMFYUI_URL
    workflow_path = workflow_path or str(get_workflow_path("image"))
    timeout = timeout or DEFAULT_COMFYUI_TIMEOUT
    steps_to_run = steps if steps is not None else [1, 2]

    # Filter steps based on GENERATION_STEPS config
    # Map: Phase 5 step number -> config position
    # Step 1 (audio) -> position 0
    # Step 2 (static images) -> position 1
    # Step 3 (shot frames) -> position 2
    # Step 4 (videos) -> position 3
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
    scene_image_count = 0
    shot_frame_count = 0
    video_count = 0
    audio_count = 0

    # =========================================================================
    # Step 1: Generate Audio (VibeVoice TTS for each sentence)
    # =========================================================================
    if 1 in steps_to_run:
        print(f"\n{'='*60}")
        print("STEP 1: Generate Audio (VibeVoice TTS)")
        print(f"{'='*60}")

        # Load audio workflow
        try:
            audio_workflow_path = get_workflow_path("audio")
        except ValueError as e:
            print(f">>> ERROR: {e}")
            audio_workflow_path = None

        if not audio_workflow_path:
            pass  # Error already printed
        elif not audio_workflow_path.exists():
            print(f">>> ERROR: Audio workflow not found at {audio_workflow_path}")
        else:
            with open(audio_workflow_path, "r", encoding="utf-8") as f:
                audio_workflow = json.load(f)

            # Count total sentences across all scenes
            narrative = codex.get("story", {}).get("narrative", {})
            total_sentences = 0
            for act in narrative.get("acts", []):
                for scene in act.get("scenes", []):
                    total_sentences += len(scene.get("sentences", []))

            if total_sentences == 0:
                print(">>> No sentences found in narrative, skipping")
                print(">>> (Ensure Phase 3 narrative has 'sentences' arrays)")
            else:
                print(f">>> Generating audio for {total_sentences} sentences...")
                print(f">>> Timeout: {AUDIO_GENERATION_TIMEOUT}s ({AUDIO_GENERATION_TIMEOUT // 60} minutes) per sentence")

                sentence_global_idx = 0
                audio_generated_count = 0

                for act_idx, act in enumerate(narrative.get("acts", [])):
                    act_num = act.get("act_number", act_idx + 1)
                    act_name = act.get("act_name", f"Act {act_num}")

                    print(f"\n>>> Act {act_num}: {act_name}")

                    for scene_idx, scene in enumerate(act.get("scenes", [])):
                        scene_num = scene.get("scene_number", scene_idx + 1)
                        scene_location = scene.get("location", "unknown")
                        sentences = scene.get("sentences", [])

                        if not sentences:
                            continue

                        print(f"    Scene {scene_num} ({scene_location}): {len(sentences)} sentences")

                        # Initialize audio_generation array for this scene
                        if "audio_generation" not in scene:
                            scene["audio_generation"] = []

                        for sent_idx, sentence in enumerate(sentences):
                            sentence_num = sent_idx + 1
                            sentence_global_idx += 1

                            # Output path for audio
                            filename_prefix = f"api/{timestamp}/audio/act{act_num}/scene{scene_num}/sentence{sentence_num:04d}"

                            # Truncate display of long sentences
                            display_text = sentence[:50] + "..." if len(sentence) > 50 else sentence
                            print(f"      [{sentence_global_idx}/{total_sentences}] \"{display_text}\"")

                            success, gen_data = generate_audio(
                                sentence_text=sentence,
                                filename_prefix=filename_prefix,
                                label=f"act{act_num}_scene{scene_num}_sent{sentence_num}",
                                comfyui_url=comfyui_url,
                                audio_workflow=audio_workflow,
                                timeout=AUDIO_GENERATION_TIMEOUT,
                            )

                            # Store generation data
                            gen_data["sentence_index"] = sent_idx
                            gen_data["sentence_text"] = sentence
                            scene["audio_generation"].append(gen_data)

                            if success is None:
                                # Fatal connection error - save and exit
                                print(f"\n>>> ERROR: Cannot connect to ComfyUI at {comfyui_url}")
                                save_codex(codex, codex_path)
                                return Phase5GenerationResult(
                                    codex_path=codex_path,
                                    poster_count=poster_count,
                                    character_portrait_count=character_portrait_count,
                                    location_image_count=location_image_count,
                                    scene_image_count=scene_image_count,
                                    shot_frame_count=shot_frame_count,
                                    video_count=video_count,
                                    audio_count=audio_generated_count,
                                    success=False,
                                    error=f"Cannot connect to ComfyUI: {gen_data['error']}",
                                )
                            elif success:
                                audio_generated_count += 1

                        # Save codex after each scene to preserve progress
                        save_codex(codex, codex_path)

                audio_count = audio_generated_count
                phase5_metadata["steps_executed"].append(1)
                phase5_metadata["total_audio_generated"] = audio_generated_count

                print(f"\n>>> Step 1 complete:")
                print(f"    Audio files generated: {audio_generated_count}/{total_sentences}")

    # =========================================================================
    # Helper function for image generation (used by Steps 2 and 3)
    # =========================================================================
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

    # =========================================================================
    # Step 2: Generate Static Images (Characters, Locations, Posters)
    # =========================================================================
    if 2 in steps_to_run:
        print(f"\n{'='*60}")
        print("STEP 2: Generate Static Images")
        print(f"{'='*60}")

        # ---------------------------------------------------------------------
        # Step 2a: Character Portraits
        # ---------------------------------------------------------------------
        print(f"\n--- 2a: Character Portraits ---")
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
                        scene_image_count=scene_image_count,
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
        # Step 2b: Location Images
        # ---------------------------------------------------------------------
        print(f"\n--- 2b: Location Images ---")
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
                        scene_image_count=scene_image_count,
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
        # Step 2c: Poster Images
        # ---------------------------------------------------------------------
        print(f"\n--- 2c: Poster Images ---")
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
                        scene_image_count=scene_image_count,
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
        phase5_metadata["steps_executed"].append(2)
        phase5_metadata["total_characters_generated"] = character_portrait_count
        phase5_metadata["total_locations_generated"] = location_image_count
        phase5_metadata["total_posters_generated"] = poster_count

        # Save codex after Step 2 to preserve progress
        save_codex(codex, codex_path)

        print(f"\n>>> Step 2 complete:")
        print(f"    Character portraits: {character_portrait_count}")
        print(f"    Location images: {location_image_count}")
        print(f"    Poster images: {poster_count}")

    # =========================================================================
    # Step 3: Generate Scene Images
    # =========================================================================
    if 3 in steps_to_run:
        print(f"\n{'='*60}")
        print("STEP 3: Generate Scene Images")
        print(f"{'='*60}")

        narrative = codex.get("story", {}).get("narrative", {})
        acts = narrative.get("acts", [])

        total_scenes = sum(len(act.get("scenes", [])) for act in acts)
        if total_scenes == 0:
            print(">>> No scenes found, skipping")
        else:
            print(f">>> Generating {total_scenes} scene images...")

            scene_global_idx = 0
            for act_idx, act in enumerate(acts):
                act_num = act.get("act_number", act_idx + 1)

                for scene_idx, scene in enumerate(act.get("scenes", [])):
                    scene_num = scene.get("scene_number", scene_idx + 1)
                    scene_global_idx += 1

                    scene_prompt_data = scene.get("scene_image_prompt", {})
                    prompt_text = scene_prompt_data.get("prompt", "")

                    if not prompt_text:
                        print(f"    [{scene_global_idx}/{total_scenes}] Act {act_num} Scene {scene_num} - No prompt, skipping")
                        continue

                    location_name = scene_prompt_data.get("location_name", "unknown")
                    filename_prefix = f"api/{timestamp}/scenes/act{act_num}_scene{scene_num}"
                    print(f"    [{scene_global_idx}/{total_scenes}] Act {act_num} Scene {scene_num} - {location_name}")

                    success, gen_data = generate_image(prompt_text, filename_prefix, f"act{act_num}_scene{scene_num}")

                    scene_prompt_data["generation"] = gen_data

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
                            scene_image_count=scene_image_count,
                            shot_frame_count=shot_frame_count,
                            video_count=video_count,
                            audio_count=audio_count,
                            success=False,
                            error=f"Cannot connect to ComfyUI: {gen_data['error']}",
                        )
                    elif success:
                        scene_image_count += 1

            print(f">>> Scene images complete: {scene_image_count}/{total_scenes}")

        # Update metadata for Step 3
        phase5_metadata["steps_executed"].append(3)
        phase5_metadata["total_scene_images_generated"] = scene_image_count

        # Save codex after Step 3
        save_codex(codex, codex_path)

    # =========================================================================
    # Step 4: Generate Videos (LTX 2.0 Image-to-Video) - COMMENTED OUT
    # =========================================================================
    # NOTE: This step is currently disabled. To re-enable:
    # 1. Uncomment the code below
    # 2. Update GENERATION_STEPS in config.py to include position 3
    # 3. Pass steps=[4] to run_phase5_generation()
    #
    # if 4 in steps_to_run:
    #     print(f"\n{'='*60}")
    #     print("STEP 4: Generate Videos (LTX 2.0 i2v)")
    #     print(f"{'='*60}")
    #     # ... video generation code ...
    #     pass
    if 4 in steps_to_run:
        print(f"\n>>> Step 4 (Videos) is currently disabled")

    # Save metadata and codex
    codex["story_metadata"]["phase5_generation"] = phase5_metadata
    save_codex(codex, codex_path)

    print(f"\n>>> Phase 5 complete!")
    print(f"    Poster images: {poster_count}")
    print(f"    Character portraits: {character_portrait_count}")
    print(f"    Location images: {location_image_count}")
    print(f"    Scene images: {scene_image_count}")
    print(f"    Shot frames: {shot_frame_count}")
    print(f"    Videos: {video_count}")
    print(f"    Audio: {audio_count}")
    print(f">>> Saved to: {codex_path}")

    return Phase5GenerationResult(
        codex_path=codex_path,
        poster_count=poster_count,
        character_portrait_count=character_portrait_count,
        location_image_count=location_image_count,
        scene_image_count=scene_image_count,
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
        help="Run specific steps (1: Audio [TTS], 2: Static Images [chars/locs/posters], 3: Shot Frames [disabled], 4: Videos [disabled])"
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
