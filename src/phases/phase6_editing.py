"""
Phase 6: Video Editing & Combination

Combines all generated shot videos into a single final video.
Uses MoviePy for video concatenation.
"""

import json
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

try:
    # MoviePy 2.x import style
    from moviepy import VideoFileClip, concatenate_videoclips
    MOVIEPY_AVAILABLE = True
except ImportError:
    try:
        # MoviePy 1.x import style (fallback)
        from moviepy.editor import VideoFileClip, concatenate_videoclips
        MOVIEPY_AVAILABLE = True
    except ImportError:
        MOVIEPY_AVAILABLE = False

from src.config import COMFYUI_OUTPUT_DIR


@dataclass
class Phase6EditingResult:
    """Result of Phase 6 video editing."""
    codex_path: Path
    output_path: Optional[Path]
    video_count: int
    total_duration: float
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


def get_video_full_path(relative_path: str, comfyui_output_dir: str) -> Path:
    """Convert relative video path to full absolute path."""
    return Path(comfyui_output_dir) / relative_path.replace("/", "\\")


def collect_video_paths(codex: dict, comfyui_output_dir: str) -> list[dict]:
    """
    Collect all video paths from codex in narrative order.

    Returns list of dicts with:
        - path: Full path to video file
        - act: Act number
        - scene: Scene number
        - shot: Shot number
        - exists: Whether file exists
    """
    videos = []
    narrative = codex.get("story", {}).get("narrative", {})

    for act in narrative.get("acts", []):
        act_num = act.get("act_number", 0)

        for scene in act.get("scenes", []):
            scene_num = scene.get("scene_number", 0)

            for shot in scene.get("shots", []):
                shot_num = shot.get("shot_number", 0)
                video_gen = shot.get("video_generation", {})
                output_path = video_gen.get("output_path")

                if output_path and video_gen.get("status") == "completed":
                    full_path = get_video_full_path(output_path, comfyui_output_dir)
                    videos.append({
                        "path": full_path,
                        "act": act_num,
                        "scene": scene_num,
                        "shot": shot_num,
                        "exists": full_path.exists(),
                    })

    return videos


def run_phase6_editing(
    codex_path: Path,
    output_filename: str = "final_video.mp4",
    comfyui_output_dir: str = None,
) -> Phase6EditingResult:
    """
    Run Phase 6: Combine all shot videos into final video.

    Args:
        codex_path: Path to codex JSON file
        output_filename: Name for output file (default: final_video.mp4)
        comfyui_output_dir: ComfyUI output directory (default: from config)

    Returns:
        Phase6EditingResult with success status and output path
    """
    print(f"\n{'='*60}")
    print("PHASE 6: Video Editing & Combination")
    print(f"{'='*60}")

    # Check MoviePy availability
    if not MOVIEPY_AVAILABLE:
        return Phase6EditingResult(
            codex_path=codex_path,
            output_path=None,
            video_count=0,
            total_duration=0,
            success=False,
            error="MoviePy not installed. Run: uv add moviepy",
        )

    # Load codex
    codex_path = Path(codex_path)
    if not codex_path.exists():
        return Phase6EditingResult(
            codex_path=codex_path,
            output_path=None,
            video_count=0,
            total_duration=0,
            success=False,
            error=f"Codex not found: {codex_path}",
        )

    codex = load_codex(codex_path)

    # Get ComfyUI output directory
    if comfyui_output_dir is None:
        comfyui_output_dir = COMFYUI_OUTPUT_DIR

    # Collect all video paths in order
    print("\n>>> Collecting video paths from codex...")
    videos = collect_video_paths(codex, comfyui_output_dir)

    if not videos:
        return Phase6EditingResult(
            codex_path=codex_path,
            output_path=None,
            video_count=0,
            total_duration=0,
            success=False,
            error="No completed videos found in codex. Run Phase 5 Step 3 first.",
        )

    # Check which videos exist
    existing_videos = [v for v in videos if v["exists"]]
    missing_videos = [v for v in videos if not v["exists"]]

    print(f">>> Found {len(videos)} videos in codex")
    print(f">>> Existing: {len(existing_videos)}, Missing: {len(missing_videos)}")

    if missing_videos:
        print("\n>>> Missing videos:")
        for v in missing_videos[:5]:  # Show first 5
            print(f"    Act {v['act']}, Scene {v['scene']}, Shot {v['shot']}")
        if len(missing_videos) > 5:
            print(f"    ... and {len(missing_videos) - 5} more")

    if not existing_videos:
        return Phase6EditingResult(
            codex_path=codex_path,
            output_path=None,
            video_count=0,
            total_duration=0,
            success=False,
            error="No video files found on disk. Check COMFYUI_OUTPUT_DIR.",
        )

    # Output path in forge directory
    forge_dir = codex_path.parent
    output_path = forge_dir / output_filename

    print(f"\n>>> Combining {len(existing_videos)} videos...")
    print(f">>> Output: {output_path}")

    # Load and concatenate videos using MoviePy
    clips = []
    total_duration = 0

    try:
        for i, video_info in enumerate(existing_videos):
            video_path = video_info["path"]
            print(f"    [{i+1}/{len(existing_videos)}] Act {video_info['act']}, Scene {video_info['scene']}, Shot {video_info['shot']}")

            clip = VideoFileClip(str(video_path))
            clips.append(clip)
            total_duration += clip.duration

        print(f"\n>>> Total duration: {total_duration:.1f}s ({total_duration/60:.1f} min)")
        print(">>> Concatenating clips...")

        # Concatenate all clips
        final_clip = concatenate_videoclips(clips, method="compose")

        print(">>> Writing final video...")
        final_clip.write_videofile(
            str(output_path),
            codec="libx264",
            audio_codec="aac",
            fps=25,
            preset="medium",
            verbose=False,
            logger=None,
        )

        # Close all clips to free resources
        for clip in clips:
            clip.close()
        final_clip.close()

        print(f"\n>>> Final video saved: {output_path}")
        print(f">>> File size: {output_path.stat().st_size / (1024*1024):.1f} MB")

        # Update codex with Phase 6 metadata
        if "story_metadata" not in codex:
            codex["story_metadata"] = {}

        codex["story_metadata"]["phase6_editing"] = {
            "completed_at": datetime.now().isoformat(),
            "output_path": str(output_path),
            "video_count": len(existing_videos),
            "missing_count": len(missing_videos),
            "total_duration_seconds": total_duration,
            "total_duration_formatted": f"{int(total_duration//60)}:{int(total_duration%60):02d}",
        }

        save_codex(codex, codex_path)

        return Phase6EditingResult(
            codex_path=codex_path,
            output_path=output_path,
            video_count=len(existing_videos),
            total_duration=total_duration,
            success=True,
        )

    except Exception as e:
        # Close any open clips
        for clip in clips:
            try:
                clip.close()
            except:
                pass

        return Phase6EditingResult(
            codex_path=codex_path,
            output_path=None,
            video_count=len(existing_videos),
            total_duration=total_duration,
            success=False,
            error=str(e),
        )


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Phase 6: Combine shot videos into final video")
    parser.add_argument("codex_path", help="Path to codex JSON file")
    parser.add_argument("--output", "-o", default="final_video.mp4", help="Output filename")

    args = parser.parse_args()

    result = run_phase6_editing(
        codex_path=Path(args.codex_path),
        output_filename=args.output,
    )

    if result.success:
        print(f"\n>>> Phase 6 complete!")
        print(f"    Videos combined: {result.video_count}")
        print(f"    Duration: {result.total_duration:.1f}s")
        print(f"    Output: {result.output_path}")
    else:
        print(f"\n>>> Phase 6 failed: {result.error}")
        import sys
        sys.exit(1)


if __name__ == "__main__":
    main()
