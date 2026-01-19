"""
Phase 6: Audio & Video Editing

This is a thin wrapper that delegates to the active template's editing phase.
The actual implementation is in src/templates/template_1_static_audio/editing.py.

- Step 1: Combine sentence audio → scene audio
- Step 2: Generate scene videos (scene image + scene audio)
- Step 3: Concatenate scene videos → final video
"""

import sys
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

# Add parent directory to path for proper package imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@dataclass
class Phase6EditingResult:
    """Result of Phase 6 audio/video editing (backward compatible)."""
    codex_path: Path
    # Audio outputs
    scene_audio_count: int
    # Video outputs
    scene_video_count: int
    video_output_path: Optional[Path]
    video_duration: float
    # Status
    success: bool
    error: Optional[str] = None
    step_timings: dict = field(default_factory=dict)


def run_phase6_editing(
    codex_path: Path,
    steps: list[int] = None,
    comfyui_output_dir: str = None,
) -> Phase6EditingResult:
    """
    Run Phase 6: Audio & Video Editing using the active template.

    This function delegates to the template's run_editing() method.
    By default, uses template_1 (static_audio).

    Steps:
        1: Combine sentence audio → scene audio
        2: Generate scene videos (image + audio)
        3: Concatenate scene videos → final video

    Args:
        codex_path: Path to codex JSON file
        steps: List of steps to run (default: [1, 2, 3])
        comfyui_output_dir: ComfyUI output directory (default: from config)

    Returns:
        Phase6EditingResult with success status and output paths
    """
    from src.templates import get_template

    # Get the active template and run editing
    template = get_template()
    result = template.run_editing(
        codex_path=Path(codex_path),
        steps=steps,
        comfyui_output_dir=comfyui_output_dir,
    )

    # Convert to Phase6EditingResult for backward compatibility
    return Phase6EditingResult(
        codex_path=result.codex_path,
        scene_audio_count=result.scene_audio_count,
        scene_video_count=result.scene_video_count,
        video_output_path=result.video_output_path,
        video_duration=result.video_duration,
        success=result.success,
        error=result.error,
        step_timings=result.step_timings,
    )


def format_duration(seconds: float) -> str:
    """Format duration as MM:SS."""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}:{secs:02d}"


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Phase 6: Audio & Video Editing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Steps:
  1: Combine sentence audio -> scene audio
  2: Generate scene videos (static image + audio)
  3: Concatenate scene videos -> final video

Examples:
  # Run all steps
  uv run python -m src.phases.phase6_editing forge/20260116191326/codex_20260116191326.json

  # Run specific steps
  uv run python -m src.phases.phase6_editing forge/20260116191326/codex_20260116191326.json --steps 1 2 3
        """
    )
    parser.add_argument("codex_path", help="Path to codex JSON file")
    parser.add_argument(
        "--steps",
        nargs="+",
        type=int,
        choices=[1, 2, 3],
        default=[1, 2, 3],
        help="Steps to run (default: 1 2 3)"
    )

    args = parser.parse_args()

    result = run_phase6_editing(
        codex_path=Path(args.codex_path),
        steps=args.steps,
    )

    if result.success:
        print(f"\n>>> Phase 6 complete!")
        print(f"    Scene audio: {result.scene_audio_count}")
        print(f"    Scene videos: {result.scene_video_count}")
        if result.video_output_path:
            print(f"    Final video: {result.video_output_path}")
            print(f"    Duration: {format_duration(result.video_duration)}")
    else:
        print(f"\n>>> Phase 6 failed: {result.error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
