#!/usr/bin/env python3
"""
Template 1: Static Audio - Generation Module

Generates images and media using ComfyUI based on prompts from Phase 2.

Step 0: Character Portraits (1024x1024 square)
Step 1: Location Images (1280x720 landscape)
Step 2: Scene Images (one per scene, 1280x720 landscape)
Step 3: Thumbnails/Posters
Step 4: Audio (Qwen3-TTS direct inference - narrator + character voices)
Step 5: Video (future, disabled)

Usage (standalone):
    uv run python -m src.templates.template_1_static_audio.generation forge/xxx/codex.json
    uv run python -m src.templates.template_1_static_audio.generation forge/xxx/codex.json --steps 1
"""

import sys
import json
import time
import argparse
import random
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

# Add parent directory to path for proper package imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.comfyui_trigger import trigger_comfy
from src.config import (
    DEFAULT_COMFYUI_URL,
    DEFAULT_COMFYUI_TIMEOUT,
    COMFYUI_OUTPUT_DIR,
    VIDEO_GENERATION_TIMEOUT,
    AUDIO_GENERATION_TIMEOUT,
    should_run_step,
    get_workflow_path,
    TTS_NARRATION_MODE,
    TTS_DEVICE,
    TTS_PRECISION,
    TTS_MODEL_SIZE,
    TTS_NARRATOR_VOICE,
    TTS_PAUSE_BETWEEN_SPEAKERS,
    TTS_PAUSE_WITHIN_SPEAKER,
    TTS_LANGUAGE,
)
from src.templates.base_template import GenerationResult
from src.tts.qwen_tts_engine import (
    QwenTTSEngine,
    CustomVoiceConfig,
    CloneVoiceConfig,
)


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
    full_firstframe_path = os.path.join(comfyui_output_dir, firstframe_path.replace("/", os.sep))

    # Replace workflow nodes
    workflow["92:3"]["inputs"]["text"] = video_prompt
    workflow["75"]["inputs"]["filename_prefix"] = filename_prefix
    workflow["98"]["inputs"]["image"] = full_firstframe_path
    workflow["92:11"]["inputs"]["noise_seed"] = seed
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
        import tempfile
        import json as json_module

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json_module.dump(workflow, f, indent=2)
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
    workflow["44"]["inputs"]["text"] = sentence_text
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


def generate_audio_qwen(
    text: str,
    filename_prefix: str,
    label: str,
    comfyui_url: str,
    audio_workflow: dict,
    voice_sample_path: str = "toireland_shelley_cf_128kb.mp3",
    timeout: int = AUDIO_GENERATION_TIMEOUT,
) -> tuple[bool | None, dict]:
    """
    Generate audio using Qwen TTS voice clone workflow.
    Can handle entire scenes in one go (not sentence-by-sentence).

    Args:
        text: The text to convert to speech (can be full scene prose)
        filename_prefix: Output path prefix for SaveAudioMP3 node
        label: Human-readable label for logging
        comfyui_url: ComfyUI API URL
        audio_workflow: Loaded Qwen TTS workflow dict
        voice_sample_path: Path to reference voice audio file
        timeout: Timeout in seconds (default from config)

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

    # Update Qwen TTS workflow nodes
    workflow["6"]["inputs"]["audio"] = voice_sample_path  # Reference voice
    workflow["7"]["inputs"]["target_text"] = text          # Text to synthesize
    workflow["8"]["inputs"]["filename_prefix"] = filename_prefix  # Output path

    gen_data = {
        "prompt_id": None,
        "status": "pending",
        "execution_time": None,
        "output_path": None,
        "generated_at": datetime.now().isoformat(),
        "error": None,
        "text_length": len(text),
    }

    try:
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
            gen_data["output_path"] = f"{filename_prefix}_00001_.mp3"
            print(f"        Completed in {result.get('execution_time', 0):.1f}s")
            return True, gen_data
        else:
            gen_data["status"] = "failed"
            gen_data["error"] = result.get("error", "Unknown error")
            print(f"        FAILED: {gen_data['error']}")
            return False, gen_data

    except ConnectionError as e:
        gen_data["status"] = "connection_error"
        gen_data["error"] = str(e)
        print(f"        Connection error: {e}")
        return None, gen_data

    except TimeoutError as e:
        gen_data["status"] = "timeout"
        gen_data["error"] = str(e)
        print(f"        Timeout: {e}")
        return False, gen_data

    except Exception as e:
        gen_data["status"] = "failed"
        gen_data["error"] = str(e)
        print(f"        ERROR: {e}")
        return False, gen_data


def _generate_image(
    prompt_text: str,
    filename_prefix: str,
    label: str,
    workflow_path: str,
    comfyui_url: str,
    timeout: int,
) -> tuple[bool | None, dict]:
    """Generate a single image using a specific workflow.

    Args:
        prompt_text: The image prompt text
        filename_prefix: Output path prefix for SaveImage node
        label: Human-readable label for logging
        workflow_path: Path to the ComfyUI workflow JSON to use
        comfyui_url: ComfyUI API URL
        timeout: Timeout in seconds

    Returns:
        (success, generation_data) where:
        - success=True: Generation completed
        - success=False: Generation failed (non-fatal)
        - success=None: Connection error (fatal)
    """
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
        return None, {
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


def _find_comfyui_output(filename_prefix: str) -> Path | None:
    """Find the latest ComfyUI output file matching a SaveImage prefix.

    ComfyUI appends ``_{NNNNN}_.png`` to the prefix. On regeneration it
    increments the counter (``_00002_``, etc.). This returns the most
    recently modified file matching the prefix, or ``None`` if no match.

    Args:
        filename_prefix: The prefix passed to SaveImage
            (e.g., ``"api/20260226/scenes/ch01_sc02_sh00_layer00_loc"``).

    Returns:
        Absolute path to the latest matching file, or None.
    """
    parent = (Path(COMFYUI_OUTPUT_DIR) / filename_prefix).parent
    stem = Path(filename_prefix).name
    if not parent.exists():
        return None
    matches = list(parent.glob(f"{stem}_*_.png"))
    if not matches:
        return None
    return max(matches, key=lambda p: p.stat().st_mtime)


def _apply_ai_stamp(
    image_path: Path,
    svg_path: Path,
    corner: str = "top-right",
    scale: float = 0.15,
    padding_fraction: float = 0.02,
) -> bool:
    """Overlay an SVG stamp onto a generated image.

    Dynamically sizes the stamp relative to the image dimensions so it scales
    correctly from 720p thumbnails to 4K posters (follows ESRB/PEGI badge
    sizing conventions: ~15% of image height).

    Args:
        image_path: Absolute path to the PNG image to stamp.
        svg_path: Absolute path to the SVG stamp file.
        corner: Placement corner — "top-right", "top-left", "bottom-right", "bottom-left".
        scale: Stamp height as a fraction of image height (0.15 = 15%).
        padding_fraction: Edge padding as a fraction of image height (0.02 = 2%).

    Returns:
        True if stamp was applied successfully, False on error.
    """
    try:
        from svglib.svglib import svg2rlg
        from reportlab.graphics import renderPM
        from PIL import Image
        import io

        # Load the poster image
        poster = Image.open(image_path).convert("RGBA")
        width, height = poster.size

        # Dynamic sizing: stamp and padding scale with image resolution
        stamp_size = max(32, int(height * scale))
        pad = max(4, int(height * padding_fraction))

        # Rasterize SVG → ReportLab drawing → PIL Image (pure Python, no Cairo C lib)
        drawing = svg2rlg(str(svg_path))
        if drawing is None:
            print(f"      WARNING: Could not parse SVG: {svg_path}")
            return False

        # Scale the drawing to target stamp size
        sx = stamp_size / drawing.width
        sy = stamp_size / drawing.height
        drawing.width = stamp_size
        drawing.height = stamp_size
        drawing.scale(sx, sy)

        # Double-render alpha extraction: ReportLab always renders on an opaque
        # canvas, so we render on white and black backgrounds then mathematically
        # recover the true alpha channel. This handles anti-aliased edges cleanly
        # (no chroma-key fringing) and works for any SVG content.
        png_white = renderPM.drawToString(drawing, fmt="PNG", bg=0xFFFFFF)
        png_black = renderPM.drawToString(drawing, fmt="PNG", bg=0x000000)
        img_w = Image.open(io.BytesIO(png_white)).convert("RGB")
        img_b = Image.open(io.BytesIO(png_black)).convert("RGB")

        stamp = Image.new("RGBA", img_w.size)
        pw, pb, ps = img_w.load(), img_b.load(), stamp.load()
        for y in range(stamp.height):
            for x in range(stamp.width):
                rw, gw, bw = pw[x, y]
                rb, gb, bb = pb[x, y]
                # alpha = 1 - avg(white_channel - black_channel) / 255
                a = max(0, min(255, 255 - ((rw - rb) + (gw - gb) + (bw - bb)) // 3))
                if a < 2:
                    ps[x, y] = (0, 0, 0, 0)
                else:
                    # Recover true color: C = black_render / (alpha / 255)
                    ps[x, y] = (
                        min(255, rb * 255 // a),
                        min(255, gb * 255 // a),
                        min(255, bb * 255 // a),
                        a,
                    )

        # Compute position based on corner
        if corner == "top-right":
            x = width - stamp_size - pad
            y = pad
        elif corner == "top-left":
            x = pad
            y = pad
        elif corner == "bottom-right":
            x = width - stamp_size - pad
            y = height - stamp_size - pad
        elif corner == "bottom-left":
            x = pad
            y = height - stamp_size - pad
        else:
            x = width - stamp_size - pad
            y = pad

        # Alpha-composite the stamp onto the poster
        poster.paste(stamp, (x, y), stamp)

        # Save back as RGB PNG (drop alpha channel for final output)
        poster.convert("RGB").save(image_path, "PNG")
        return True

    except Exception as e:
        print(f"      WARNING: Failed to apply AI stamp: {e}")
        return False


def _generate_location_layer(
    prompt: str,
    base_image_name: str,
    filename_prefix: str,
    label: str,
    workflow_path: str,
    comfyui_url: str,
    timeout: int,
) -> tuple[bool | None, dict]:
    """Apply location modifications to a base location image.

    Uses the Qwen Image Edit (single-image) workflow to modify an existing
    location image for time-of-day, weather, and atmosphere effects.

    Args:
        prompt: The location_layer prompt describing modifications.
        base_image_name: Full absolute path to the base location image.
        filename_prefix: Output path prefix for SaveImage node.
        label: Human-readable label for logging.
        workflow_path: Path to the location edit workflow JSON.
        comfyui_url: ComfyUI API URL.
        timeout: Timeout in seconds.

    Returns:
        (success, generation_data) — same contract as _generate_image().
    """
    seed = generate_seed()
    try:
        result = trigger_comfy(
            workflow_json_path=workflow_path,
            replacements={
                "78_image": base_image_name,
                "102:76_prompt": prompt,
                "102:3_seed": seed,
                "60_filename_prefix": filename_prefix,
            },
            comfyui_url=comfyui_url,
            timeout=timeout,
        )

        generation_data = {
            "prompt_id": result["prompt_id"],
            "status": result["status"],
            "execution_time": result["execution_time"],
            "filename_prefix": filename_prefix,
            "seed": seed,
            "layer_type": "location",
            "input_image": base_image_name,
            "generated_at": datetime.now().isoformat(),
        }

        if result["status"] == "completed":
            output_path = _find_comfyui_output(filename_prefix)
            generation_data["output_path"] = str(output_path) if output_path else ""
            print(f"        Completed in {result['execution_time']:.1f}s")
            return True, generation_data
        else:
            error_msg = result.get("error", "Unknown error")
            print(f"        Failed: {error_msg}")
            generation_data["error"] = error_msg
            return False, generation_data

    except ConnectionError as e:
        print(f"        Connection error: {e}")
        return None, {"status": "error", "error": str(e), "layer_type": "location",
                       "generated_at": datetime.now().isoformat()}

    except TimeoutError as e:
        print(f"        Timeout: {e}")
        return False, {"status": "timeout", "error": str(e), "seed": seed,
                        "layer_type": "location", "generated_at": datetime.now().isoformat()}

    except Exception as e:
        print(f"        Error: {e}")
        return False, {"status": "error", "error": str(e), "layer_type": "location",
                        "generated_at": datetime.now().isoformat()}


def _generate_character_layer(
    prompt: str,
    scene_image_name: str,
    portrait_image_name: str,
    filename_prefix: str,
    label: str,
    workflow_path: str,
    comfyui_url: str,
    timeout: int,
) -> tuple[bool | None, dict]:
    """Composite a character into a scene image using their portrait as reference.

    Uses the Qwen Image Edit Plus (two-image) workflow. Image 1 is the current
    scene state, image 2 is the character portrait from Step 0.

    Args:
        prompt: The character_layer prompt describing placement and pose.
        scene_image_name: Full absolute path to the current scene image.
        portrait_image_name: Full absolute path to the character portrait.
        filename_prefix: Output path prefix for SaveImage node.
        label: Human-readable label for logging.
        workflow_path: Path to the two-image edit workflow JSON.
        comfyui_url: ComfyUI API URL.
        timeout: Timeout in seconds.

    Returns:
        (success, generation_data) — same contract as _generate_image().
    """
    seed = generate_seed()
    try:
        result = trigger_comfy(
            workflow_json_path=workflow_path,
            replacements={
                "41_image": scene_image_name,
                "83_image": portrait_image_name,
                "91:68_prompt": prompt,
                "91:65_seed": seed,
                "92_filename_prefix": filename_prefix,
            },
            comfyui_url=comfyui_url,
            timeout=timeout,
        )

        generation_data = {
            "prompt_id": result["prompt_id"],
            "status": result["status"],
            "execution_time": result["execution_time"],
            "filename_prefix": filename_prefix,
            "seed": seed,
            "layer_type": "character",
            "input_scene": scene_image_name,
            "input_portrait": portrait_image_name,
            "generated_at": datetime.now().isoformat(),
        }

        if result["status"] == "completed":
            output_path = _find_comfyui_output(filename_prefix)
            generation_data["output_path"] = str(output_path) if output_path else ""
            print(f"        Completed in {result['execution_time']:.1f}s")
            return True, generation_data
        else:
            error_msg = result.get("error", "Unknown error")
            print(f"        Failed: {error_msg}")
            generation_data["error"] = error_msg
            return False, generation_data

    except ConnectionError as e:
        print(f"        Connection error: {e}")
        return None, {"status": "error", "error": str(e), "layer_type": "character",
                       "generated_at": datetime.now().isoformat()}

    except TimeoutError as e:
        print(f"        Timeout: {e}")
        return False, {"status": "timeout", "error": str(e), "seed": seed,
                        "layer_type": "character", "generated_at": datetime.now().isoformat()}

    except Exception as e:
        print(f"        Error: {e}")
        return False, {"status": "error", "error": str(e), "layer_type": "character",
                        "generated_at": datetime.now().isoformat()}


def _run_location_pass(
    scene_prompt_data: dict,
    timestamp: str,
    ch_num: int,
    sc_num: int,
    comfyui_url: str,
    timeout: int,
    shot_num: int = 0,
) -> dict:
    """Run the location edit layer for a single scene.

    Resolves the base location image from Step 1 output and, if the scene
    requires location modification, runs the location edit workflow.

    This is the first pass of the two-pass scene generation pipeline.
    All location edits across scenes should be batched together so
    ComfyUI only loads the location edit model once.

    Args:
        scene_prompt_data: The scene's ``scene_image_prompt`` dict from codex.
        timestamp: Forge timestamp for path construction.
        ch_num: Chapter number.
        sc_num: Scene number.
        comfyui_url: ComfyUI API URL.
        timeout: Timeout in seconds.
        shot_num: Shot index within the scene (default 0).

    Returns:
        Scene state dict with keys:
            - current_scene_path (Path): path to use as input for character pass
            - shot_prefix (str): e.g. ``"ch01_sc02_sh00"``
            - layer_index (int): next layer index for character pass
            - layers_data (list[dict]): layer metadata collected so far
            - location_ok (bool | None): True=success, False=failed, None=connection error
    """
    location_id = scene_prompt_data.get("location_id", "")
    location_layer = scene_prompt_data.get("location_layer", {})
    location_name = scene_prompt_data.get("location_name", "unknown")
    shot_prefix = f"ch{ch_num:02d}_sc{sc_num:02d}_sh{shot_num:02d}"

    # --- Resolve base location image (full absolute path via glob) ---
    base_loc_prefix = f"api/{timestamp}/locations/{location_id}"
    current_scene_path = _find_comfyui_output(base_loc_prefix)

    if current_scene_path is None:
        error_msg = f"Base location image not found for prefix: {base_loc_prefix}"
        print(f"        {error_msg}")
        return {
            "current_scene_path": None, "shot_prefix": shot_prefix,
            "layer_index": 0, "layers_data": [],
            "location_ok": False, "error": error_msg,
        }

    layer_index = 0
    layers_data: list[dict] = []

    # --- Location layer (only if modification needed) ---
    if location_layer.get("requires_modification"):
        loc_prefix = f"api/{timestamp}/scenes/{shot_prefix}_layer{layer_index:02d}_loc"
        loc_prompt = location_layer.get("prompt", "")
        loc_edit_workflow = str(get_workflow_path("scene_location_edit"))

        print(f"      Layer {layer_index}: Location edit ({location_name})")

        success, gen_data = _generate_location_layer(
            prompt=loc_prompt,
            base_image_name=str(current_scene_path),
            filename_prefix=loc_prefix,
            label=f"{shot_prefix}_layer{layer_index:02d}_loc",
            workflow_path=loc_edit_workflow,
            comfyui_url=comfyui_url,
            timeout=timeout,
        )

        gen_data["layer_index"] = layer_index
        layers_data.append(gen_data)

        if success is None:
            return {
                "current_scene_path": None, "shot_prefix": shot_prefix,
                "layer_index": layer_index + 1, "layers_data": layers_data,
                "location_ok": None,
            }
        if not success:
            return {
                "current_scene_path": None, "shot_prefix": shot_prefix,
                "layer_index": layer_index + 1, "layers_data": layers_data,
                "location_ok": False,
            }

        # Update current scene path to location layer output (glob-based)
        current_scene_path = _find_comfyui_output(loc_prefix)
        if current_scene_path is None:
            error_msg = f"Location layer output not found for prefix: {loc_prefix}"
            print(f"        {error_msg}")
            return {
                "current_scene_path": None, "shot_prefix": shot_prefix,
                "layer_index": layer_index + 1, "layers_data": layers_data,
                "location_ok": False, "error": error_msg,
            }
        layer_index += 1

    return {
        "current_scene_path": current_scene_path, "shot_prefix": shot_prefix,
        "layer_index": layer_index, "layers_data": layers_data,
        "location_ok": True,
    }


def _run_character_pass(
    scene_state: dict,
    scene_prompt_data: dict,
    timestamp: str,
    comfyui_url: str,
    timeout: int,
) -> tuple[bool | None, dict]:
    """Run all character layers for a single scene.

    Takes the scene state produced by ``_run_location_pass()`` and
    composites characters sequentially onto ``current_scene_path``.

    This is the second pass of the two-pass scene generation pipeline.
    All character compositing across scenes should be batched together
    so ComfyUI only loads the character edit model once.

    Args:
        scene_state: Dict returned by ``_run_location_pass()``.
        scene_prompt_data: The scene's ``scene_image_prompt`` dict from codex.
        timestamp: Forge timestamp for path construction.
        comfyui_url: ComfyUI API URL.
        timeout: Timeout in seconds per layer.

    Returns:
        (success, generation_data) where generation_data includes a ``layers`` array
        covering both location and character layers.
    """
    current_scene_path = scene_state["current_scene_path"]
    shot_prefix = scene_state["shot_prefix"]
    layer_index = scene_state["layer_index"]
    layers_data = list(scene_state["layers_data"])  # copy to avoid mutation

    character_layers = scene_prompt_data.get("character_layers", [])
    location_layer = scene_prompt_data.get("location_layer", {})
    total_layers = (1 if location_layer.get("requires_modification") else 0) + len(character_layers)

    char_edit_workflow = str(get_workflow_path("scene_character_edit"))
    last_layer_prefix = ""

    for i, char_layer in enumerate(character_layers):
        char_id = char_layer.get("character_id", f"char_{i+1:03d}")
        char_name = char_layer.get("character_name", char_id)
        char_prompt = char_layer.get("prompt", "")

        # Resolve character portrait path (glob-based)
        portrait_prefix = f"api/{timestamp}/characters/{char_id}"
        portrait_path = _find_comfyui_output(portrait_prefix)

        if portrait_path is None:
            error_msg = f"Character portrait not found for prefix: {portrait_prefix}"
            print(f"        {error_msg}")
            gen_data = {"layer_type": "character", "layer_index": layer_index,
                        "character_id": char_id, "character_name": char_name,
                        "status": "error", "error": error_msg,
                        "generated_at": datetime.now().isoformat()}
            layers_data.append(gen_data)
            return False, _build_layered_result(layers_data, layer_index + 1)

        # Every layer gets a numbered name with character ID suffix
        char_prefix = f"api/{timestamp}/scenes/{shot_prefix}_layer{layer_index:02d}_{char_id}"

        print(f"      Layer {layer_index}: Character {char_name} ({char_id})")

        success, gen_data = _generate_character_layer(
            prompt=char_prompt,
            scene_image_name=str(current_scene_path),
            portrait_image_name=str(portrait_path),
            filename_prefix=char_prefix,
            label=f"{shot_prefix}_layer{layer_index:02d}_{char_id}",
            workflow_path=char_edit_workflow,
            comfyui_url=comfyui_url,
            timeout=timeout,
        )

        gen_data["layer_index"] = layer_index
        gen_data["character_id"] = char_id
        gen_data["character_name"] = char_name
        layers_data.append(gen_data)

        if success is None:
            return None, _build_layered_result(layers_data, layer_index + 1)
        if not success:
            return False, _build_layered_result(layers_data, layer_index + 1)

        # Update current scene path for next character layer (glob-based)
        current_scene_path = _find_comfyui_output(char_prefix)
        if current_scene_path is None:
            error_msg = f"Character layer output not found for prefix: {char_prefix}"
            print(f"        {error_msg}")
            return False, _build_layered_result(layers_data, layer_index + 1)
        last_layer_prefix = char_prefix
        layer_index += 1

    # --- Build final result (last layer's output is the final scene) ---
    final_path = _find_comfyui_output(last_layer_prefix) if last_layer_prefix else current_scene_path
    final_output = str(final_path) if final_path else ""
    return True, {
        "pipeline": "layered",
        "status": "completed",
        "output_path": final_output,
        "final_layer_prefix": last_layer_prefix,
        "total_layers_attempted": total_layers,
        "total_layers_completed": total_layers,
        "layers": layers_data,
        "generated_at": datetime.now().isoformat(),
    }


def _build_layered_result(
    layers_data: list[dict],
    total_attempted: int,
    error: str | None = None,
) -> dict:
    """Build a generation result dict for layered scenes (used on partial failure)."""
    completed = sum(1 for l in layers_data if l.get("status") == "completed")
    result = {
        "pipeline": "layered",
        "status": "error",
        "output_path": "",
        "total_layers_attempted": total_attempted,
        "total_layers_completed": completed,
        "layers": layers_data,
        "generated_at": datetime.now().isoformat(),
    }
    if error:
        result["error"] = error
    return result


def _make_error_result(
    codex_path: Path,
    error: str,
    **counts,
) -> GenerationResult:
    """Build a failed GenerationResult with current counts."""
    return GenerationResult(
        codex_path=codex_path,
        poster_count=counts.get("poster_count", 0),
        character_portrait_count=counts.get("character_portrait_count", 0),
        location_image_count=counts.get("location_image_count", 0),
        scene_image_count=counts.get("scene_image_count", 0),
        shot_frame_count=counts.get("shot_frame_count", 0),
        video_count=counts.get("video_count", 0),
        audio_count=counts.get("audio_count", 0),
        success=False,
        error=error,
    )


# Step name constants for logging and metadata
STEP_NAMES = {
    0: "Character Portraits",
    1: "Location Images",
    2: "Scene Images",
    3: "Thumbnails/Posters",
    4: "Audio (Qwen3-TTS Direct)",
    5: "Video (future)",
}


def run_template1_generation(
    codex_path: Path,
    comfyui_url: str = None,
    workflow_path: str = None,
    steps: list[int] = None,
    timeout: int = None,
) -> GenerationResult:
    """
    Generate images and media using ComfyUI for Template 1 (Static Audio).

    Step 0: Character Portraits (1024x1024 square)
    Step 1: Location Images (1280x720 landscape)
    Step 2: Scene Images (1280x720 landscape, one per scene)
    Step 3: Thumbnails/Posters
    Step 4: Audio (Qwen3-TTS Direct Inference)
    Step 5: Video (future, disabled)

    Args:
        codex_path: Path to codex.json (must have prompts from Phase 2)
        comfyui_url: ComfyUI API URL (default: from config)
        workflow_path: Deprecated — each step uses its own workflow from config
        steps: List of step numbers to run (default: [0, 1, 2, 3, 4])
        timeout: Timeout in seconds for each generation (default: from config)

    Returns:
        GenerationResult with counts of generated media
    """
    codex_path = Path(codex_path)
    codex = load_codex(codex_path)

    # Get configuration
    comfyui_url = comfyui_url or DEFAULT_COMFYUI_URL
    timeout = timeout or DEFAULT_COMFYUI_TIMEOUT
    steps_to_run = steps if steps is not None else [0, 1, 2, 3, 4]

    # Filter steps based on GENERATION_STEPS config
    # Step N maps to config position N (0-based)
    original_steps = steps_to_run.copy()
    steps_to_run = [s for s in steps_to_run if should_run_step(s)]

    # Report any skipped steps
    skipped_steps = [s for s in original_steps if s not in steps_to_run]
    if skipped_steps:
        skipped_names = [f"{s} ({STEP_NAMES.get(s, '?')})" for s in skipped_steps]
        print(f">>> Steps skipped by GENERATION_STEPS config: {', '.join(skipped_names)}")

    # Get timestamp for output paths
    timestamp = get_timestamp_from_codex_path(codex_path)

    print(f"\n{'='*60}")
    print("PHASE 3: MEDIA GENERATION")
    print(f"{'='*60}")
    print(f">>> ComfyUI URL: {comfyui_url}")
    print(f">>> Timeout: {timeout}s")
    step_labels = [f"{s}-{STEP_NAMES.get(s, '?')}" for s in steps_to_run]
    print(f">>> Running steps: {', '.join(step_labels)}")

    # Initialize metadata
    if "metadata" not in codex:
        codex["metadata"] = {}

    phase3_metadata = {
        "comfyui_url": comfyui_url,
        "workflows_used": {},
        "steps_executed": [],
        "template": "static_audio",
    }

    # Step timing
    step_timings = {}

    # Counters
    character_portrait_count = 0
    location_image_count = 0
    scene_image_count = 0
    poster_count = 0
    audio_count = 0
    video_count = 0
    shot_frame_count = 0

    # Helper to get current counts dict for error results
    def _counts():
        return dict(
            character_portrait_count=character_portrait_count,
            location_image_count=location_image_count,
            scene_image_count=scene_image_count,
            poster_count=poster_count,
            audio_count=audio_count,
            video_count=video_count,
            shot_frame_count=shot_frame_count,
        )

    # =========================================================================
    # Step 1: Character Portraits
    # =========================================================================
    if 0 in steps_to_run:
        step_start = time.time()
        char_workflow = str(get_workflow_path("character"))
        phase3_metadata["workflows_used"]["character"] = Path(char_workflow).name

        print(f"\n{'='*60}")
        print("STEP 0: Character Portraits")
        print(f"  Workflow: {Path(char_workflow).name}")
        print(f"{'='*60}")

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

                char_id = character.get("character_id", f"char_{i+1:03d}")
                filename_prefix = f"api/{timestamp}/characters/{char_id}"
                print(f"    [{i+1}/{len(characters)}] {char_name}")

                success, gen_data = _generate_image(
                    prompt_text, filename_prefix, char_name,
                    workflow_path=char_workflow,
                    comfyui_url=comfyui_url,
                    timeout=timeout,
                )

                char_prompt["generation"] = gen_data

                if success is None:
                    print(f"\n>>> ERROR: Cannot connect to ComfyUI at {comfyui_url}")
                    save_codex(codex, codex_path)
                    return _make_error_result(
                        codex_path, f"Cannot connect to ComfyUI: {gen_data['error']}", **_counts()
                    )
                elif success:
                    character_portrait_count += 1

            print(f">>> Characters complete: {character_portrait_count}/{len(characters)}")

        phase3_metadata["steps_executed"].append(0)
        phase3_metadata["total_characters_generated"] = character_portrait_count
        step_timings["step0_characters"] = round(time.time() - step_start, 2)
        save_codex(codex, codex_path)
        print(f">>> Step 0 complete ({step_timings['step0_characters']:.1f}s)")

    # =========================================================================
    # Step 2: Location Images
    # =========================================================================
    if 1 in steps_to_run:
        step_start = time.time()
        loc_workflow = str(get_workflow_path("location"))
        phase3_metadata["workflows_used"]["location"] = Path(loc_workflow).name

        print(f"\n{'='*60}")
        print("STEP 1: Location Images")
        print(f"  Workflow: {Path(loc_workflow).name}")
        print(f"{'='*60}")

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

                loc_id = location.get("id", f"loc_{i+1:03d}")
                filename_prefix = f"api/{timestamp}/locations/{loc_id}"
                print(f"    [{i+1}/{len(locations)}] {loc_name}")

                success, gen_data = _generate_image(
                    prompt_text, filename_prefix, loc_name,
                    workflow_path=loc_workflow,
                    comfyui_url=comfyui_url,
                    timeout=timeout,
                )

                loc_prompt["generation"] = gen_data

                if success is None:
                    print(f"\n>>> ERROR: Cannot connect to ComfyUI at {comfyui_url}")
                    save_codex(codex, codex_path)
                    return _make_error_result(
                        codex_path, f"Cannot connect to ComfyUI: {gen_data['error']}", **_counts()
                    )
                elif success:
                    location_image_count += 1

            print(f">>> Locations complete: {location_image_count}/{len(locations)}")

        phase3_metadata["steps_executed"].append(1)
        phase3_metadata["total_locations_generated"] = location_image_count
        step_timings["step1_locations"] = round(time.time() - step_start, 2)
        save_codex(codex, codex_path)
        print(f">>> Step 1 complete ({step_timings['step1_locations']:.1f}s)")

    # =========================================================================
    # Step 3: Scene Images (Two-Pass Layered Compositing Pipeline)
    # =========================================================================
    if 2 in steps_to_run:
        step_start = time.time()

        # Load workflow paths for layered pipeline
        loc_edit_wf = str(get_workflow_path("scene_location_edit"))
        char_edit_wf = str(get_workflow_path("scene_character_edit"))
        scene_workflow = str(get_workflow_path("scene"))  # flat prompt fallback

        phase3_metadata["workflows_used"]["scene_location_edit"] = Path(loc_edit_wf).name
        phase3_metadata["workflows_used"]["scene_character_edit"] = Path(char_edit_wf).name

        print(f"\n{'='*60}")
        print("STEP 2: Scene Images (Two-Pass Layered Compositing)")
        print(f"  Location edit workflow: {Path(loc_edit_wf).name}")
        print(f"  Character edit workflow: {Path(char_edit_wf).name}")
        print(f"{'='*60}")

        chapters_data = codex.get("story", {}).get("chapters", {})
        chapters = chapters_data.get("chapters", [])

        # --- Collect scene jobs ---
        # Each job: (ch_num, sc_num, scene_prompt_data, prompt_type)
        layered_jobs: list[tuple[int, int, dict]] = []
        flat_jobs: list[tuple[int, int, dict]] = []
        for ch_idx, chapter in enumerate(chapters):
            ch_num = chapter.get("chapter_number", ch_idx + 1)
            for sc_idx, scene in enumerate(chapter.get("scenes", [])):
                sc_num = scene.get("scene_number", sc_idx + 1)
                scene_prompt_data = scene.get("scene_image_prompt", {})
                prompt_type = scene_prompt_data.get("prompt_type", "")
                if prompt_type == "layered":
                    layered_jobs.append((ch_num, sc_num, scene_prompt_data))
                elif scene_prompt_data.get("prompt"):
                    flat_jobs.append((ch_num, sc_num, scene_prompt_data))

        total_scenes = len(layered_jobs) + len(flat_jobs)

        if total_scenes == 0:
            print(">>> No scene image prompts found, skipping")
            print(">>> (Ensure Phase 2 has generated scene_image_prompt for each scene)")
        else:
            print(f">>> Generating {total_scenes} scene images ({len(layered_jobs)} layered, {len(flat_jobs)} flat)...")
            scene_global_idx = 0

            # =============================================================
            # Pass 1: All location edits (keeps location edit model loaded)
            # =============================================================
            if layered_jobs:
                loc_edits_needed = sum(
                    1 for _, _, spd in layered_jobs
                    if spd.get("location_layer", {}).get("requires_modification")
                )
                print(f"\n  --- Pass 1: Location edits ({loc_edits_needed} of {len(layered_jobs)} scenes need modification) ---")

            scene_states: list[dict] = []
            for ch_num, sc_num, scene_prompt_data in layered_jobs:
                location_name = scene_prompt_data.get("location_name", "unknown")
                needs_edit = scene_prompt_data.get("location_layer", {}).get("requires_modification", False)
                scene_global_idx += 1
                label = "edit" if needs_edit else "no edit"
                print(f"    [{scene_global_idx}/{total_scenes}] Ch{ch_num} Sc{sc_num} - {location_name} ({label})")

                state = _run_location_pass(
                    scene_prompt_data=scene_prompt_data,
                    timestamp=timestamp,
                    ch_num=ch_num,
                    sc_num=sc_num,
                    comfyui_url=comfyui_url,
                    timeout=timeout,
                )
                scene_states.append(state)

                if state["location_ok"] is None:
                    # Connection error — abort entirely
                    error_msg = state.get("error", "Connection error during location pass")
                    print(f"\n>>> ERROR: Cannot connect to ComfyUI at {comfyui_url}")
                    scene_prompt_data["generation"] = _build_layered_result(
                        state["layers_data"], state["layer_index"],
                    )
                    save_codex(codex, codex_path)
                    return _make_error_result(
                        codex_path, f"Cannot connect to ComfyUI: {error_msg}", **_counts()
                    )

            # =============================================================
            # Pass 2: All character compositing (keeps char edit model loaded)
            # =============================================================
            if layered_jobs:
                total_chars = sum(
                    len(spd.get("character_layers", []))
                    for _, _, spd in layered_jobs
                )
                print(f"\n  --- Pass 2: Character compositing ({total_chars} character layers across {len(layered_jobs)} scenes) ---")

            for (ch_num, sc_num, scene_prompt_data), state in zip(layered_jobs, scene_states):
                location_name = scene_prompt_data.get("location_name", "unknown")
                n_chars = len(scene_prompt_data.get("character_layers", []))
                print(f"    Ch{ch_num} Sc{sc_num} - {location_name} ({n_chars} character(s))")

                if not state["location_ok"]:
                    # Location pass failed — record error and skip character pass
                    print(f"      Skipping: location pass failed")
                    scene_prompt_data["generation"] = _build_layered_result(
                        state["layers_data"], state["layer_index"],
                    )
                    continue

                success, gen_data = _run_character_pass(
                    scene_state=state,
                    scene_prompt_data=scene_prompt_data,
                    timestamp=timestamp,
                    comfyui_url=comfyui_url,
                    timeout=timeout,
                )

                scene_prompt_data["generation"] = gen_data

                if success is None:
                    print(f"\n>>> ERROR: Cannot connect to ComfyUI at {comfyui_url}")
                    save_codex(codex, codex_path)
                    return _make_error_result(
                        codex_path, f"Cannot connect to ComfyUI: {gen_data.get('error', 'unknown')}", **_counts()
                    )
                elif success:
                    scene_image_count += 1

            # =============================================================
            # Flat prompt fallback scenes (backward compat)
            # =============================================================
            for ch_num, sc_num, scene_prompt_data in flat_jobs:
                prompt_text = scene_prompt_data["prompt"]
                location_name = scene_prompt_data.get("location_name", "unknown")
                scene_global_idx += 1
                print(f"    [{scene_global_idx}/{total_scenes}] Ch{ch_num} Sc{sc_num} - {location_name} (flat)")

                filename_prefix = f"api/{timestamp}/scenes/ch{ch_num:02d}_sc{sc_num:02d}"
                success, gen_data = _generate_image(
                    prompt_text, filename_prefix, f"ch{ch_num}_sc{sc_num}",
                    workflow_path=scene_workflow,
                    comfyui_url=comfyui_url,
                    timeout=timeout,
                )

                scene_prompt_data["generation"] = gen_data

                if success is None:
                    print(f"\n>>> ERROR: Cannot connect to ComfyUI at {comfyui_url}")
                    save_codex(codex, codex_path)
                    return _make_error_result(
                        codex_path, f"Cannot connect to ComfyUI: {gen_data.get('error', 'unknown')}", **_counts()
                    )
                elif success:
                    scene_image_count += 1

            print(f">>> Scene images complete: {scene_image_count}/{total_scenes}")

        phase3_metadata["steps_executed"].append(2)
        phase3_metadata["total_scene_images_generated"] = scene_image_count
        step_timings["step2_scenes"] = round(time.time() - step_start, 2)
        save_codex(codex, codex_path)
        print(f">>> Step 2 complete ({step_timings['step2_scenes']:.1f}s)")

    # =========================================================================
    # Step 4: Thumbnails/Posters
    # =========================================================================
    if 3 in steps_to_run:
        step_start = time.time()
        thumb_workflow = str(get_workflow_path("thumbnail"))
        phase3_metadata["workflows_used"]["thumbnail"] = Path(thumb_workflow).name

        print(f"\n{'='*60}")
        print("STEP 3: Thumbnails/Posters")
        print(f"  Workflow: {Path(thumb_workflow).name}")
        print(f"{'='*60}")

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

                success, gen_data = _generate_image(
                    prompt_text, filename_prefix, f"poster_{i+1}",
                    workflow_path=thumb_workflow,
                    comfyui_url=comfyui_url,
                    timeout=timeout,
                )

                poster["generation"] = gen_data

                if success is None:
                    print(f"\n>>> ERROR: Cannot connect to ComfyUI at {comfyui_url}")
                    save_codex(codex, codex_path)
                    return _make_error_result(
                        codex_path, f"Cannot connect to ComfyUI: {gen_data['error']}", **_counts()
                    )
                elif success:
                    poster_count += 1

                    # Apply AI disclosure stamp to the generated poster
                    output_file = _find_comfyui_output(filename_prefix)
                    if output_file:
                        stamp_svg = Path(__file__).resolve().parent.parent.parent.parent / "svg" / "AI_stamp_1.svg"
                        if stamp_svg.exists():
                            if _apply_ai_stamp(output_file, stamp_svg):
                                print(f"      AI stamp applied to {output_file.name}")
                            poster["generation"]["stamped"] = True
                        else:
                            print(f"      WARNING: AI stamp SVG not found at {stamp_svg}")
                    else:
                        print(f"      WARNING: Could not find output file for {filename_prefix}")

            print(f">>> Posters complete: {poster_count}/{len(poster_prompts)}")

        phase3_metadata["steps_executed"].append(3)
        phase3_metadata["total_posters_generated"] = poster_count
        step_timings["step3_thumbnails"] = round(time.time() - step_start, 2)
        save_codex(codex, codex_path)
        print(f">>> Step 3 complete ({step_timings['step3_thumbnails']:.1f}s)")

    # =========================================================================
    # Step 5: Audio (Qwen3-TTS Direct Inference)
    # =========================================================================
    if 4 in steps_to_run:
        step_start = time.time()
        print(f"\n{'='*60}")
        print("STEP 4: Audio (Qwen3-TTS Direct Inference)")
        print(f"{'='*60}")
        print(f"    Mode: {TTS_NARRATION_MODE}")
        print(f"    Device: {TTS_DEVICE}, Precision: {TTS_PRECISION}")
        print(f"    Model: Qwen3-TTS-{TTS_MODEL_SIZE}")

        chapters_data = codex.get("story", {}).get("chapters", {})
        chapters = chapters_data.get("chapters", [])
        codex_characters = codex.get("story", {}).get("characters", [])

        # Build narrator voice config from settings
        if TTS_NARRATOR_VOICE.get("type") == "clone":
            narrator_config = CloneVoiceConfig(
                ref_audio=TTS_NARRATOR_VOICE.get("clone_ref_audio", ""),
                ref_text=TTS_NARRATOR_VOICE.get("clone_ref_text", ""),
            )
        else:
            narrator_config = CustomVoiceConfig(
                speaker=TTS_NARRATOR_VOICE.get("speaker", "Ryan"),
            )

        # Initialize TTS engine
        tts_engine = QwenTTSEngine(
            device=TTS_DEVICE,
            precision=TTS_PRECISION,
            model_size=TTS_MODEL_SIZE,
            narrator_voice=narrator_config,
            narration_mode=TTS_NARRATION_MODE,
            pause_between_speakers_ms=TTS_PAUSE_BETWEEN_SPEAKERS,
            pause_within_speaker_ms=TTS_PAUSE_WITHIN_SPEAKER,
        )

        # Build voice map for all characters
        voice_map = tts_engine.setup_voice_map(
            characters=codex_characters,
            narrator_config=narrator_config,
        )
        print(f"    Voice map: {len(voice_map)} entries")

        # Audio output directory (in forge, not ComfyUI output)
        forge_dir = codex_path.parent
        audio_dir = forge_dir / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)

        # Clear stale files from previous runs
        old_wavs = list(audio_dir.glob("*.wav"))
        if old_wavs:
            for old_wav in old_wavs:
                old_wav.unlink()
            print(f"    Cleared {len(old_wavs)} old audio files")

        # Reset audio generation tracking
        chapters_data["audio_generation"] = {"items": [], "total_generated": 0}
        audio_generated_count = 0
        seq_num = 0

        # 1. Book title audio
        book_title = chapters_data.get("title", "Untitled")
        if book_title:
            seq_num += 1
            title_path = audio_dir / f"{seq_num:03d}_title.wav"
            print(f"\n    [{seq_num}] Book Title: \"{book_title}\"")

            title_script = [{"speaker": "NARRATOR", "text": book_title, "instruct": "Grand, resonant announcement with gravitas."}]
            success, duration = tts_engine.generate_scene_audio(
                audio_script=title_script,
                voice_map=voice_map,
                output_path=title_path,
                language=TTS_LANGUAGE,
            )
            gen_data = {
                "sequence": seq_num, "type": "title", "status": "completed" if success else "failed",
                "output_path": str(title_path), "duration": duration,
                "generated_at": datetime.now().isoformat(),
            }
            chapters_data["audio_generation"]["items"].append(gen_data)
            if success:
                audio_generated_count += 1

        # 2. Chapter titles + scene audio
        for ch_idx, chapter in enumerate(chapters):
            ch_num = chapter.get("chapter_number", ch_idx + 1)
            ch_title = chapter.get("chapter_title", f"Chapter {ch_num}")

            # Chapter title audio
            seq_num += 1
            ch_title_path = audio_dir / f"{seq_num:03d}_ch{ch_num:02d}_title.wav"
            print(f"\n    [{seq_num}] Ch{ch_num} Title: \"{ch_title}\"")

            ch_script = [{"speaker": "NARRATOR", "text": f"Chapter {ch_num}. {ch_title}", "instruct": "Clear, measured chapter announcement."}]
            success, duration = tts_engine.generate_scene_audio(
                audio_script=ch_script,
                voice_map=voice_map,
                output_path=ch_title_path,
                language=TTS_LANGUAGE,
            )
            gen_data = {
                "sequence": seq_num, "type": "chapter_title", "chapter_number": ch_num,
                "status": "completed" if success else "failed",
                "output_path": str(ch_title_path), "duration": duration,
                "generated_at": datetime.now().isoformat(),
            }
            chapters_data["audio_generation"]["items"].append(gen_data)
            if success:
                audio_generated_count += 1

            # Scene audio (uses audio_script from Phase 2 Step 6)
            for sc_idx, scene in enumerate(chapter.get("scenes", [])):
                sc_num = scene.get("scene_number", sc_idx + 1)
                audio_script = scene.get("audio_script", [])

                if not audio_script:
                    # Fallback: use prose as single narrator chunk
                    prose = scene.get("prose", "")
                    if prose:
                        audio_script = [{"speaker": "NARRATOR", "text": prose, "instruct": "Neutral, even narration."}]
                    else:
                        print(f"\n    [skip] Ch{ch_num} Sc{sc_num}: No audio script or prose")
                        continue

                seq_num += 1
                scene_path = audio_dir / f"{seq_num:03d}_ch{ch_num:02d}_sc{sc_num:02d}.wav"
                print(f"\n    [{seq_num}] Ch{ch_num} Sc{sc_num} ({len(audio_script)} chunks)")

                success, duration = tts_engine.generate_scene_audio(
                    audio_script=audio_script,
                    voice_map=voice_map,
                    output_path=scene_path,
                    language=TTS_LANGUAGE,
                )

                gen_data = {
                    "sequence": seq_num, "type": "scene",
                    "chapter_number": ch_num, "scene_number": sc_num,
                    "status": "completed" if success else "failed",
                    "output_path": str(scene_path), "duration": duration,
                    "chunks": len(audio_script),
                    "generated_at": datetime.now().isoformat(),
                }
                chapters_data["audio_generation"]["items"].append(gen_data)
                if success:
                    audio_generated_count += 1

                # Save progress after each scene
                chapters_data["audio_generation"]["total_generated"] = audio_generated_count
                save_codex(codex, codex_path)

        audio_count = audio_generated_count
        chapters_data["audio_generation"]["total_generated"] = audio_count

        # Cleanup TTS engine
        tts_engine.close()

        phase3_metadata["steps_executed"].append(4)
        phase3_metadata["total_audio_generated"] = audio_count
        phase3_metadata["tts_engine"] = "qwen3-tts-direct"
        phase3_metadata["narration_mode"] = TTS_NARRATION_MODE
        step_timings["step4_audio"] = round(time.time() - step_start, 2)
        save_codex(codex, codex_path)
        print(f"\n>>> Step 4 complete ({step_timings.get('step4_audio', 0):.1f}s):")
        print(f"    Audio files generated: {audio_count}")

    # =========================================================================
    # Step 6: Video (future, disabled)
    # =========================================================================
    if 5 in steps_to_run:
        print(f"\n>>> Step 5 (Video) is currently disabled")

    # Save metadata and codex
    codex["metadata"]["phase_3"] = phase3_metadata
    save_codex(codex, codex_path)

    print(f"\n>>> Phase 3 Generation complete!")
    print(f"    Character portraits: {character_portrait_count}")
    print(f"    Location images: {location_image_count}")
    print(f"    Scene images: {scene_image_count}")
    print(f"    Posters/Thumbnails: {poster_count}")
    print(f"    Audio: {audio_count}")
    print(f"    Videos: {video_count}")
    print(f">>> Saved to: {codex_path}")

    return GenerationResult(
        codex_path=codex_path,
        poster_count=poster_count,
        character_portrait_count=character_portrait_count,
        location_image_count=location_image_count,
        scene_image_count=scene_image_count,
        shot_frame_count=shot_frame_count,
        video_count=video_count,
        audio_count=audio_count,
        success=True,
        step_timings=step_timings,
    )


def main():
    """CLI entry point for standalone execution."""
    parser = argparse.ArgumentParser(
        description="Template 1: Generate images and media using ComfyUI"
    )
    parser.add_argument(
        "codex_path",
        type=Path,
        help="Path to codex.json (must have prompts from Phase 2)"
    )
    parser.add_argument(
        "--comfyui-url",
        default=None,
        help=f"ComfyUI API URL (default: {DEFAULT_COMFYUI_URL})"
    )
    parser.add_argument(
        "--steps",
        nargs="+",
        type=int,
        choices=[0, 1, 2, 3, 4, 5],
        help="Run specific steps (0: Characters, 1: Locations, 2: Scenes, 3: Thumbnails, 4: Audio, 5: Video)"
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

    result = run_template1_generation(
        args.codex_path,
        comfyui_url=args.comfyui_url,
        steps=args.steps,
        timeout=args.timeout,
    )

    if not result.success:
        print(f"\n>>> ERROR: {result.error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
