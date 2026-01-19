"""
Template 1: Static Audio - Editing Module

Audio & Video Editing for the Static Audio template.

- Step 1: Combine sentence audio → scene audio
- Step 2: Generate scene videos (scene image + scene audio)
- Step 3: Concatenate scene videos → final video
"""

import json
import time
import subprocess
import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# MoviePy for video generation (MoviePy 2.x)
try:
    from moviepy import ImageClip, AudioFileClip, VideoFileClip, concatenate_videoclips
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False

# Get ffmpeg path from imageio-ffmpeg (bundled with moviepy)
try:
    import imageio_ffmpeg
    FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()
    FFMPEG_AVAILABLE = True
except ImportError:
    FFMPEG_PATH = None
    FFMPEG_AVAILABLE = False

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.config import COMFYUI_OUTPUT_DIR
from src.templates.base_template import EditingResult


def load_codex(codex_path: Path) -> dict:
    """Load codex JSON file."""
    with open(codex_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_codex(codex: dict, codex_path: Path) -> None:
    """Save codex JSON file."""
    with open(codex_path, "w", encoding="utf-8") as f:
        json.dump(codex, f, indent=2, ensure_ascii=False)


def get_audio_full_path(relative_path: str, comfyui_output_dir: str) -> Path:
    """Convert relative audio path to full absolute path."""
    return Path(comfyui_output_dir) / relative_path


def get_audio_duration(audio_path: Path) -> float:
    """Get duration of audio file in seconds using ffprobe."""
    if not FFMPEG_AVAILABLE or not audio_path.exists():
        return 0.0

    try:
        result = subprocess.run(
            [FFMPEG_PATH, "-i", str(audio_path), "-f", "null", "-"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        import re
        duration_match = re.search(r"Duration: (\d+):(\d+):(\d+)\.(\d+)", result.stderr)
        if duration_match:
            hours, mins, secs, ms = duration_match.groups()
            return int(hours) * 3600 + int(mins) * 60 + int(secs) + int(ms) / 100
    except Exception:
        pass
    return 0.0


def combine_audio_files(
    audio_paths: list[Path],
    output_path: Path,
    label: str,
) -> tuple[bool, float]:
    """
    Combine multiple MP3 files into one using ffmpeg.

    Args:
        audio_paths: List of paths to audio files (in order)
        output_path: Path for combined output file
        label: Label for logging

    Returns:
        (success, duration_seconds)
    """
    if not FFMPEG_AVAILABLE:
        print(f"        ERROR: ffmpeg not available")
        return False, 0.0

    valid_paths = [p for p in audio_paths if p.exists()]

    if not valid_paths:
        print(f"        ERROR: No valid audio files found for {label}")
        return False, 0.0

    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            for path in valid_paths:
                escaped_path = str(path.absolute()).replace("\\", "/")
                f.write(f"file '{escaped_path}'\n")
            concat_file = f.name

        try:
            result = subprocess.run(
                [
                    FFMPEG_PATH,
                    "-y",
                    "-f", "concat",
                    "-safe", "0",
                    "-i", concat_file,
                    "-c", "copy",
                    str(output_path)
                ],
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode != 0:
                print(f"        ERROR: ffmpeg failed: {result.stderr[:200]}")
                return False, 0.0

        finally:
            import os
            os.unlink(concat_file)

        duration = get_audio_duration(output_path)
        return True, duration

    except subprocess.TimeoutExpired:
        print(f"        ERROR: ffmpeg timed out for {label}")
        return False, 0.0
    except Exception as e:
        print(f"        ERROR: {e}")
        return False, 0.0


def format_duration(seconds: float) -> str:
    """Format duration as MM:SS."""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}:{secs:02d}"


def create_static_clip(
    image_path: Path,
    audio_path: Path,
    output_path: Path,
) -> tuple[bool, float]:
    """
    Create video clip from a static image with audio.

    Args:
        image_path: Path to the source image
        audio_path: Path to the audio file
        output_path: Path for the output video

    Returns:
        (success, duration)
    """
    if not MOVIEPY_AVAILABLE:
        print("        ERROR: moviepy not available")
        return False, 0.0

    try:
        audio = AudioFileClip(str(audio_path))
        duration = audio.duration

        img = ImageClip(str(image_path), duration=duration)
        video = img.with_audio(audio)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        video.write_videofile(
            str(output_path),
            fps=24,
            codec="h264_nvenc",  # NVIDIA GPU encoder (RTX 4090)
            audio_codec="aac",
            logger=None
        )

        audio.close()
        video.close()

        return True, duration

    except Exception as e:
        print(f"        ERROR: {e}")
        return False, 0.0


def run_template1_editing(
    codex_path: Path,
    steps: list[int] = None,
    comfyui_output_dir: str = None,
) -> EditingResult:
    """
    Run Template 1 Editing: Audio & Video Editing.

    Steps:
        1: Combine sentence audio → scene audio
        2: Generate scene videos (image + audio)
        3: Concatenate scene videos → final video

    Args:
        codex_path: Path to codex JSON file
        steps: List of steps to run (default: [1, 2, 3])
        comfyui_output_dir: ComfyUI output directory (default: from config)

    Returns:
        EditingResult with success status and output paths
    """
    steps_to_run = steps or [1, 2, 3]

    print(f"\n{'='*60}")
    print("TEMPLATE 1: Audio & Video Editing (Static Audio)")
    print(f"{'='*60}")
    print(f">>> Steps to run: {steps_to_run}")

    # Check ffmpeg availability
    if not FFMPEG_AVAILABLE:
        return EditingResult(
            codex_path=codex_path,
            scene_audio_count=0,
            scene_video_count=0,
            video_output_path=None,
            video_duration=0,
            success=False,
            error="ffmpeg not available. Install imageio-ffmpeg.",
        )

    print(f">>> Using ffmpeg: {FFMPEG_PATH}")

    # Load codex
    codex_path = Path(codex_path)
    if not codex_path.exists():
        return EditingResult(
            codex_path=codex_path,
            scene_audio_count=0,
            scene_video_count=0,
            video_output_path=None,
            video_duration=0,
            success=False,
            error=f"Codex not found: {codex_path}",
        )

    codex = load_codex(codex_path)

    # Get ComfyUI output directory
    if comfyui_output_dir is None:
        comfyui_output_dir = COMFYUI_OUTPUT_DIR

    # Output directories in forge
    forge_dir = codex_path.parent
    audio_dir = forge_dir / "audio"

    # Initialize counters
    scene_audio_count = 0

    # Initialize metadata
    if "story_metadata" not in codex:
        codex["story_metadata"] = {}
    phase6_metadata = {
        "started_at": datetime.now().isoformat(),
        "steps_executed": [],
        "template": "static_audio",
    }

    # Step timing
    step_timings = {}

    narrative = codex.get("story", {}).get("narrative", {})

    # =========================================================================
    # Step 1: Combine Sentences into Scene Audio
    # =========================================================================
    if 1 in steps_to_run:
        step_start = time.time()
        print(f"\n{'='*60}")
        print("STEP 1: Combine Sentences into Scene Audio")
        print(f"{'='*60}")

        scenes_dir = audio_dir / "scenes"
        scenes_dir.mkdir(parents=True, exist_ok=True)

        total_scenes = sum(len(act.get("scenes", [])) for act in narrative.get("acts", []))
        scene_idx = 0

        for act in narrative.get("acts", []):
            act_num = act.get("act_number", 0)
            act_name = act.get("act_name", f"Act {act_num}")

            print(f"\n>>> Act {act_num}: {act_name}")

            for scene in act.get("scenes", []):
                scene_num = scene.get("scene_number", 0)
                scene_location = scene.get("location", "unknown")
                audio_gen = scene.get("audio_generation", [])
                scene_idx += 1

                if not audio_gen:
                    print(f"    Scene {scene_num} ({scene_location}): No audio data, skipping")
                    continue

                # Get completed audio paths in order by sentence_index
                audio_paths = []
                for audio in sorted(audio_gen, key=lambda x: x.get("sentence_index", 0)):
                    if audio.get("status") == "completed" and audio.get("output_path"):
                        full_path = get_audio_full_path(audio["output_path"], comfyui_output_dir)
                        audio_paths.append(full_path)

                if audio_paths:
                    output_path = scenes_dir / f"act{act_num}_scene{scene_num}.mp3"
                    print(f"    [{scene_idx}/{total_scenes}] Scene {scene_num} ({scene_location}): {len(audio_paths)} sentences...")

                    success, duration = combine_audio_files(
                        audio_paths, output_path, f"Act {act_num} Scene {scene_num}"
                    )

                    if success:
                        scene["combined_audio"] = {
                            "path": str(output_path),
                            "duration": duration,
                            "sentence_count": len(audio_paths),
                        }
                        scene_audio_count += 1
                        print(f"        -> {output_path.name} ({format_duration(duration)})")
                else:
                    print(f"    Scene {scene_num} ({scene_location}): No completed audio files")

        # Save codex after Step 1
        save_codex(codex, codex_path)
        phase6_metadata["steps_executed"].append(1)
        phase6_metadata["scene_audio_count"] = scene_audio_count
        step_timings["step1_combine_audio"] = round(time.time() - step_start, 2)

        print(f"\n>>> Step 1 complete ({step_timings['step1_combine_audio']:.1f}s): {scene_audio_count} scene audio files created")

    # =========================================================================
    # Step 2: Generate Scene Videos (Image + Audio)
    # =========================================================================
    scene_video_count = 0
    if 2 in steps_to_run:
        step_start = time.time()
        print(f"\n{'='*60}")
        print("STEP 2: Generate Scene Videos")
        print(f"{'='*60}")

        if not MOVIEPY_AVAILABLE:
            print(">>> ERROR: moviepy not available. Install moviepy to generate videos.")
        else:
            # Reload codex in case Step 1 was run in a previous invocation
            codex = load_codex(codex_path)
            narrative = codex.get("story", {}).get("narrative", {})

            videos_dir = forge_dir / "videos"
            videos_dir.mkdir(parents=True, exist_ok=True)

            total_scenes = sum(len(act.get("scenes", [])) for act in narrative.get("acts", []))
            scene_idx = 0

            for act in narrative.get("acts", []):
                act_num = act.get("act_number", 0)

                for scene in act.get("scenes", []):
                    scene_num = scene.get("scene_number", 0)
                    scene_idx += 1

                    # Get combined audio path from Step 1
                    combined_audio = scene.get("combined_audio", {})
                    audio_path = Path(combined_audio.get("path", ""))

                    # Get scene image path from generation data (stored in Phase 5)
                    scene_image_data = scene.get("scene_image_prompt", {}).get("generation", {})
                    image_relative_path = scene_image_data.get("output_path", "")
                    if image_relative_path:
                        image_path = Path(comfyui_output_dir) / image_relative_path
                    else:
                        # No generation data - scene image wasn't generated
                        image_path = None

                    if not audio_path.exists():
                        print(f"    [{scene_idx}/{total_scenes}] Act {act_num} Scene {scene_num} - No audio, skipping")
                        continue
                    if image_path is None or not image_path.exists():
                        print(f"    [{scene_idx}/{total_scenes}] Act {act_num} Scene {scene_num} - No image, skipping")
                        continue

                    output_path = videos_dir / f"act{act_num}_scene{scene_num}.mp4"
                    print(f"    [{scene_idx}/{total_scenes}] Act {act_num} Scene {scene_num}...")

                    success, duration = create_static_clip(
                        image_path, audio_path, output_path
                    )

                    if success:
                        scene["video"] = {
                            "path": str(output_path),
                            "duration": duration,
                        }
                        scene_video_count += 1
                        print(f"        -> {output_path.name} ({format_duration(duration)})")

            save_codex(codex, codex_path)
            phase6_metadata["steps_executed"].append(2)
            phase6_metadata["scene_video_count"] = scene_video_count
            step_timings["step2_scene_videos"] = round(time.time() - step_start, 2)

            print(f"\n>>> Step 2 complete ({step_timings['step2_scene_videos']:.1f}s): {scene_video_count} scene videos created")

    # =========================================================================
    # Step 3: Concatenate into Final Video
    # =========================================================================
    video_output_path = None
    video_duration = 0.0
    if 3 in steps_to_run:
        step_start = time.time()
        print(f"\n{'='*60}")
        print("STEP 3: Create Final Video")
        print(f"{'='*60}")

        if not MOVIEPY_AVAILABLE:
            print(">>> ERROR: moviepy not available. Install moviepy to generate videos.")
        else:
            # Reload codex in case Steps 1-2 were run in previous invocations
            codex = load_codex(codex_path)
            narrative = codex.get("story", {}).get("narrative", {})

            # Collect scene video paths in order
            video_paths = []
            for act in sorted(narrative.get("acts", []), key=lambda x: x.get("act_number", 0)):
                for scene in sorted(act.get("scenes", []), key=lambda x: x.get("scene_number", 0)):
                    video_info = scene.get("video", {})
                    if video_info.get("path"):
                        path = Path(video_info["path"])
                        if path.exists():
                            video_paths.append(path)

            if video_paths:
                output_path = forge_dir / "final_video.mp4"
                print(f">>> Concatenating {len(video_paths)} scene videos...")

                try:
                    clips = [VideoFileClip(str(p)) for p in video_paths]
                    final = concatenate_videoclips(clips, method="compose")

                    final.write_videofile(
                        str(output_path),
                        fps=24,
                        codec="h264_nvenc",  # NVIDIA GPU encoder (RTX 4090)
                        audio_codec="aac",
                        logger=None
                    )

                    total_duration = sum(c.duration for c in clips)
                    for c in clips:
                        c.close()
                    final.close()

                    video_output_path = output_path
                    video_duration = total_duration

                    phase6_metadata["final_video"] = {
                        "path": str(output_path),
                        "duration": total_duration,
                        "duration_formatted": format_duration(total_duration),
                        "scene_count": len(video_paths),
                    }

                    print(f"    -> {output_path.name} ({format_duration(total_duration)})")
                    print(f"    File size: {output_path.stat().st_size / (1024*1024):.1f} MB")

                except Exception as e:
                    print(f">>> ERROR: {e}")
            else:
                print(">>> No scene videos found. Run Step 2 first.")

        step_timings["step3_final_video"] = round(time.time() - step_start, 2)
        phase6_metadata["steps_executed"].append(3)
        print(f"\n>>> Step 3 complete ({step_timings['step3_final_video']:.1f}s)")

    # Finalize metadata
    phase6_metadata["completed_at"] = datetime.now().isoformat()
    codex["story_metadata"]["phase6_editing"] = phase6_metadata
    save_codex(codex, codex_path)

    # Summary
    print(f"\n{'='*60}")
    print("TEMPLATE 1 EDITING COMPLETE")
    print(f"{'='*60}")
    print(f">>> Scene audio files: {scene_audio_count}")
    print(f">>> Scene videos: {scene_video_count}")
    if video_output_path:
        print(f">>> Final video: {video_output_path}")
        print(f">>> Total duration: {format_duration(video_duration)}")

    return EditingResult(
        codex_path=codex_path,
        scene_audio_count=scene_audio_count,
        scene_video_count=scene_video_count,
        video_output_path=video_output_path,
        video_duration=video_duration,
        success=True,
        step_timings=step_timings,
    )


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Template 1: Audio & Video Editing (Static Audio)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Steps:
  1: Combine sentence audio -> scene audio
  2: Generate scene videos (static image + audio)
  3: Concatenate scene videos -> final video

Examples:
  # Run all steps
  uv run python -m src.templates.template_1_static_audio.editing forge/20260116191326/codex_20260116191326.json

  # Run specific steps
  uv run python -m src.templates.template_1_static_audio.editing forge/20260116191326/codex_20260116191326.json --steps 1 2 3
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

    result = run_template1_editing(
        codex_path=Path(args.codex_path),
        steps=args.steps,
    )

    if result.success:
        print(f"\n>>> Template 1 Editing complete!")
        print(f"    Scene audio: {result.scene_audio_count}")
        print(f"    Scene videos: {result.scene_video_count}")
        if result.video_output_path:
            print(f"    Final video: {result.video_output_path}")
            print(f"    Duration: {format_duration(result.video_duration)}")
    else:
        print(f"\n>>> Template 1 Editing failed: {result.error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
