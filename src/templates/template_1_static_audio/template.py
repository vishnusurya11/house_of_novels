"""
Template 1: Static Audio - Template Class

Main template class that implements BaseTemplate for static images with narrated audio.
"""

from pathlib import Path

from ..base_template import BaseTemplate, GenerationResult, EditingResult
from .config import (
    TEMPLATE_NAME,
    TEMPLATE_DESCRIPTION,
    DEFAULT_GENERATION_STEPS,
    DEFAULT_EDITING_STEPS,
)


class StaticAudioTemplate(BaseTemplate):
    """
    Template 1: Static Images with Narrated Audio.

    This template generates:
    - Character portraits
    - Location images
    - Poster images
    - Scene images (characters in locations)
    - TTS audio for narrative text

    And combines them into:
    - Scene videos (image + audio)
    - Final concatenated video
    """

    name = TEMPLATE_NAME
    description = TEMPLATE_DESCRIPTION

    def run_generation(
        self,
        codex_path: Path,
        comfyui_url: str = None,
        workflow_path: str = None,
        steps: list[int] = None,
        timeout: int = None,
        **kwargs
    ) -> GenerationResult:
        """
        Run media generation for Template 1.

        Step 1: Generate Audio (VibeVoice TTS for each sentence)
        Step 2: Generate Static Images (characters, locations, posters)
        Step 3: Generate Scene Images (scene-specific images with characters in location)

        Args:
            codex_path: Path to codex.json
            comfyui_url: ComfyUI API URL (optional, uses default)
            workflow_path: Path to ComfyUI workflow JSON (optional)
            steps: List of step numbers to run (default: [1, 2, 3])
            timeout: Timeout in seconds per generation (optional)

        Returns:
            GenerationResult with counts and status
        """
        from .generation import run_template1_generation

        steps = steps or DEFAULT_GENERATION_STEPS
        return run_template1_generation(
            codex_path=codex_path,
            comfyui_url=comfyui_url,
            workflow_path=workflow_path,
            steps=steps,
            timeout=timeout,
        )

    def run_editing(
        self,
        codex_path: Path,
        steps: list[int] = None,
        comfyui_output_dir: str = None,
        **kwargs
    ) -> EditingResult:
        """
        Run media editing for Template 1.

        Step 1: Combine sentence audio → scene audio
        Step 2: Generate scene videos (image + audio)
        Step 3: Concatenate scene videos → final video

        Args:
            codex_path: Path to codex.json
            steps: List of step numbers to run (default: [1, 2, 3])
            comfyui_output_dir: ComfyUI output directory (optional)

        Returns:
            EditingResult with output paths and status
        """
        from .editing import run_template1_editing

        steps = steps or DEFAULT_EDITING_STEPS
        return run_template1_editing(
            codex_path=codex_path,
            steps=steps,
            comfyui_output_dir=comfyui_output_dir,
        )

    def get_default_generation_steps(self) -> list[int]:
        """Return default generation steps for Template 1."""
        return DEFAULT_GENERATION_STEPS

    def get_default_editing_steps(self) -> list[int]:
        """Return default editing steps for Template 1."""
        return DEFAULT_EDITING_STEPS


def main():
    """CLI entry point for standalone template execution."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Template 1: Static Audio - Static images with narrated audio",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run both generation and editing
  uv run python -m src.templates.template_1_static_audio forge/xxx/codex.json

  # Run only generation
  uv run python -m src.templates.template_1_static_audio forge/xxx/codex.json --phase generation

  # Run only editing
  uv run python -m src.templates.template_1_static_audio forge/xxx/codex.json --phase editing

  # Run specific steps
  uv run python -m src.templates.template_1_static_audio forge/xxx/codex.json --phase generation --steps 1 2
        """
    )
    parser.add_argument("codex_path", type=Path, help="Path to codex.json")
    parser.add_argument(
        "--phase",
        choices=["generation", "editing", "both"],
        default="both",
        help="Phase to run (default: both)"
    )
    parser.add_argument(
        "--steps",
        nargs="+",
        type=int,
        help="Specific steps to run (generation: 1=audio, 2=static, 3=scenes; editing: 1=combine, 2=videos, 3=final)"
    )

    args = parser.parse_args()

    if not args.codex_path.exists():
        print(f"ERROR: Codex not found: {args.codex_path}")
        sys.exit(1)

    template = StaticAudioTemplate()

    print(f"\n{'#'*60}")
    print(f"# TEMPLATE: {template.name}")
    print(f"# {template.description}")
    print(f"{'#'*60}")
    print(f"# Codex: {args.codex_path}")
    print(f"# Phase: {args.phase}")
    if args.steps:
        print(f"# Steps: {args.steps}")
    print(f"{'#'*60}\n")

    if args.phase in ["generation", "both"]:
        result = template.run_generation(args.codex_path, steps=args.steps)
        if not result.success:
            print(f"\nERROR: Generation failed: {result.error}")
            sys.exit(1)
        print(f"\n>>> Generation complete: {result.audio_count} audio, {result.scene_image_count} scenes")

    if args.phase in ["editing", "both"]:
        result = template.run_editing(args.codex_path, steps=args.steps)
        if not result.success:
            print(f"\nERROR: Editing failed: {result.error}")
            sys.exit(1)
        print(f"\n>>> Editing complete: {result.scene_video_count} videos")
        if result.video_output_path:
            print(f">>> Final video: {result.video_output_path}")

    print("\n>>> Template complete!")


if __name__ == "__main__":
    main()
