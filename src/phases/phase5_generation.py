#!/usr/bin/env python3
"""
Phase 5: Image & Media Generation

This is a thin wrapper that delegates to the active template's generation phase.
The actual implementation is in src/templates/template_1_static_audio/generation.py.

Usage (standalone):
    uv run python -m src.phases.phase5_generation forge/20260113195058/codex.json
    uv run python -m src.phases.phase5_generation codex.json --steps 1 2
    uv run python -m src.phases.phase5_generation codex.json --comfyui-url http://192.168.1.100:8188
"""

import sys
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

# Add parent directory to path for proper package imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config import DEFAULT_COMFYUI_URL, DEFAULT_COMFYUI_TIMEOUT


@dataclass
class Phase5GenerationResult:
    """Result of Phase 5 media generation (backward compatible)."""
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
    step_timings: dict = field(default_factory=dict)


def run_phase5_generation(
    codex_path: Path,
    comfyui_url: str = None,
    workflow_path: str = None,
    steps: list[int] = None,
    timeout: int = None,
) -> Phase5GenerationResult:
    """
    Generate images and media using the active template.

    This function delegates to the template's run_generation() method.
    By default, uses template_1 (static_audio).

    Step 1: Generate Audio (VibeVoice TTS for each sentence)
    Step 2: Generate Static Images (characters, locations, posters)
    Step 3: Generate Scene Images (scene-specific images)
    Step 4: Generate Videos (DISABLED)

    Args:
        codex_path: Path to codex.json (must have prompts from Phase 4)
        comfyui_url: ComfyUI API URL (default: from config)
        workflow_path: Path to ComfyUI workflow JSON (default: from config)
        steps: List of step numbers to run (default: [1, 2, 3])
        timeout: Timeout in seconds for each generation (default: 300)

    Returns:
        Phase5GenerationResult with counts of generated media
    """
    from src.templates import get_template

    # Get the active template and run generation
    template = get_template()
    result = template.run_generation(
        codex_path=Path(codex_path),
        comfyui_url=comfyui_url,
        workflow_path=workflow_path,
        steps=steps,
        timeout=timeout,
    )

    # Convert to Phase5GenerationResult for backward compatibility
    return Phase5GenerationResult(
        codex_path=result.codex_path,
        poster_count=result.poster_count,
        character_portrait_count=result.character_portrait_count,
        location_image_count=result.location_image_count,
        scene_image_count=result.scene_image_count,
        shot_frame_count=result.shot_frame_count,
        video_count=result.video_count,
        audio_count=result.audio_count,
        success=result.success,
        error=result.error,
        step_timings=result.step_timings,
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
        help="Run specific steps (1: Audio, 2: Static Images, 3: Scene Images, 4: Videos [disabled])"
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
