#!/usr/bin/env python3
"""
Phase 7: YouTube Upload

Publishes the generated video to YouTube with AI-generated title and description.

Steps:
    1: Generate YouTube metadata (title, description) using AI agent
    2: Authenticate with YouTube API
    3: Upload video with metadata

Usage (standalone):
    uv run python -m src.phases.phase7_youtube forge/20260118/codex.json
    uv run python -m src.phases.phase7_youtube codex.json --privacy unlisted
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

import random as rand_module
from src.config import DEFAULT_YOUTUBE_PRIVACY, DEFAULT_MODEL, DEFAULT_YOUTUBE_PLAYLIST, COMFYUI_OUTPUT_DIR


@dataclass
class Phase7YouTubeResult:
    """Result of Phase 7 YouTube upload."""
    codex_path: Path
    video_id: Optional[str]
    video_url: Optional[str]
    title: str
    description: str
    tags: list[str]
    privacy_status: str
    success: bool
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


def extract_story_data(codex: dict) -> dict:
    """Extract relevant story data from codex for metadata generation."""
    story = codex.get("story", {})
    outline = story.get("outline", {})
    narrative = story.get("narrative", {})
    characters = story.get("characters", [])

    # Get title and logline
    title = outline.get("title", narrative.get("title", "Untitled Story"))
    logline = outline.get("logline", "An AI-generated story.")

    # Extract scene summaries from narrative
    scene_summaries = []
    for act in narrative.get("acts", []):
        for scene in act.get("scenes", []):
            summary = scene.get("summary", "")
            if summary:
                scene_summaries.append(summary)

    return {
        "title": title,
        "logline": logline,
        "characters": characters,
        "scene_summaries": scene_summaries,
    }


def find_random_poster(codex: dict) -> Optional[Path]:
    """Find a random poster image from the codex poster generation data."""
    # Posters are stored in outline.poster_prompts
    posters = codex.get("story", {}).get("outline", {}).get("poster_prompts", [])

    poster_paths = []
    for poster in posters:
        gen_data = poster.get("generation", {})
        if gen_data.get("status") == "completed" and gen_data.get("output_path"):
            full_path = Path(COMFYUI_OUTPUT_DIR) / gen_data["output_path"]
            if full_path.exists():
                poster_paths.append(full_path)

    if poster_paths:
        return rand_module.choice(poster_paths)

    return None


def find_final_video(codex_path: Path) -> Optional[Path]:
    """Find the final video file in the forge directory."""
    forge_dir = codex_path.parent
    video_dir = forge_dir / "videos"

    # Look for final_video.mp4 first
    final_video = video_dir / "final_video.mp4"
    if final_video.exists():
        return final_video

    # Also check directly in forge dir
    final_video = forge_dir / "final_video.mp4"
    if final_video.exists():
        return final_video

    # Look for any mp4 file in videos directory
    if video_dir.exists():
        mp4_files = list(video_dir.glob("*.mp4"))
        if mp4_files:
            # Return the most recently modified one
            return max(mp4_files, key=lambda p: p.stat().st_mtime)

    return None


def run_phase7_youtube(
    codex_path: Path,
    privacy_status: str = None,
    model: str = None,
) -> Phase7YouTubeResult:
    """
    Run Phase 7: YouTube Upload.

    Steps:
        1: Generate YouTube metadata (title, description) using AI agent
        2: Authenticate with YouTube API
        3: Upload video with metadata

    Args:
        codex_path: Path to codex JSON file
        privacy_status: Video privacy ('public', 'unlisted', 'private')
        model: LLM model for metadata generation

    Returns:
        Phase7YouTubeResult with upload status and video URL
    """
    codex_path = Path(codex_path)
    privacy_status = privacy_status or DEFAULT_YOUTUBE_PRIVACY
    model = model or DEFAULT_MODEL
    step_timings = {}

    print(f"\n{'='*60}")
    print("PHASE 7: YOUTUBE UPLOAD")
    print(f"{'='*60}")
    print(f">>> Codex: {codex_path}")
    print(f">>> Privacy: {privacy_status}")

    # Load codex
    codex = load_codex(codex_path)

    # Initialize metadata
    if "story_metadata" not in codex:
        codex["story_metadata"] = {}

    phase7_metadata = {
        "phase": 7,
        "name": "YouTube Upload",
        "steps_executed": [],
    }

    # Find the final video
    video_path = find_final_video(codex_path)
    if not video_path:
        return Phase7YouTubeResult(
            codex_path=codex_path,
            video_id=None,
            video_url=None,
            title="",
            description="",
            tags=[],
            privacy_status=privacy_status,
            success=False,
            error="No video file found. Run Phase 6 (editing) first.",
            step_timings=step_timings,
        )

    print(f">>> Video: {video_path}")

    # ========================================
    # Step 1: Generate YouTube metadata
    # ========================================
    print(f"\n{'-'*40}")
    print("STEP 1: Generate YouTube Metadata")
    print(f"{'-'*40}")
    step_start = time.time()

    try:
        from src.story_agents.youtube_metadata_agent import generate_youtube_metadata

        story_data = extract_story_data(codex)
        metadata = generate_youtube_metadata(
            story_title=story_data["title"],
            logline=story_data["logline"],
            characters=story_data["characters"],
            scene_summaries=story_data["scene_summaries"],
            model=model,
        )

        title = metadata.title
        description = metadata.description
        tags = metadata.tags

        print(f">>> Title: {title}")
        print(f">>> Description: {description[:100]}...")
        print(f">>> Tags: {', '.join(tags[:5])}...")

    except Exception as e:
        # Fallback to basic metadata if agent fails
        print(f">>> Warning: Metadata agent failed: {e}")
        print(">>> Using fallback metadata...")
        story_data = extract_story_data(codex)
        title = story_data["title"][:100]
        description = f"{story_data['logline']}\n\nAn AI-generated story video.\n\n#AIStory #GeneratedStory"
        tags = ["AI story", "generated story", "AI video", "storytelling"]

    step_timings["step1_metadata"] = {"duration_seconds": round(time.time() - step_start, 2)}
    phase7_metadata["steps_executed"].append("step1_metadata")

    # ========================================
    # Step 2: Authenticate with YouTube
    # ========================================
    print(f"\n{'-'*40}")
    print("STEP 2: Authenticate with YouTube")
    print(f"{'-'*40}")
    step_start = time.time()

    try:
        from src.youtube import get_youtube_service
        youtube = get_youtube_service()
        print(">>> YouTube authentication successful")
    except FileNotFoundError as e:
        return Phase7YouTubeResult(
            codex_path=codex_path,
            video_id=None,
            video_url=None,
            title=title,
            description=description,
            tags=tags,
            privacy_status=privacy_status,
            success=False,
            error=str(e),
            step_timings=step_timings,
        )
    except Exception as e:
        return Phase7YouTubeResult(
            codex_path=codex_path,
            video_id=None,
            video_url=None,
            title=title,
            description=description,
            tags=tags,
            privacy_status=privacy_status,
            success=False,
            error=f"YouTube authentication failed: {e}",
            step_timings=step_timings,
        )

    step_timings["step2_auth"] = {"duration_seconds": round(time.time() - step_start, 2)}
    phase7_metadata["steps_executed"].append("step2_auth")

    # ========================================
    # Step 3: Upload video
    # ========================================
    print(f"\n{'-'*40}")
    print("STEP 3: Upload Video")
    print(f"{'-'*40}")
    step_start = time.time()

    try:
        from src.youtube import upload_video

        result = upload_video(
            youtube=youtube,
            file_path=video_path,
            title=title,
            description=description,
            tags=tags,
            privacy_status=privacy_status,
        )

        if not result.success:
            return Phase7YouTubeResult(
                codex_path=codex_path,
                video_id=None,
                video_url=None,
                title=title,
                description=description,
                tags=tags,
                privacy_status=privacy_status,
                success=False,
                error=result.error,
                step_timings=step_timings,
            )

        video_id = result.video_id
        video_url = result.video_url

    except Exception as e:
        return Phase7YouTubeResult(
            codex_path=codex_path,
            video_id=None,
            video_url=None,
            title=title,
            description=description,
            tags=tags,
            privacy_status=privacy_status,
            success=False,
            error=f"Video upload failed: {e}",
            step_timings=step_timings,
        )

    step_timings["step3_upload"] = {"duration_seconds": round(time.time() - step_start, 2)}
    phase7_metadata["steps_executed"].append("step3_upload")

    # ========================================
    # Step 4: Set Thumbnail (random poster)
    # ========================================
    print(f"\n{'-'*40}")
    print("STEP 4: Set Thumbnail")
    print(f"{'-'*40}")
    step_start = time.time()

    thumbnail_path = find_random_poster(codex)
    if thumbnail_path:
        from src.youtube import set_thumbnail
        if set_thumbnail(youtube, video_id, thumbnail_path):
            phase7_metadata["thumbnail_path"] = str(thumbnail_path)
        else:
            print(">>> Thumbnail upload failed, continuing without custom thumbnail")
    else:
        print(">>> No poster images found, skipping thumbnail")

    step_timings["step4_thumbnail"] = {"duration_seconds": round(time.time() - step_start, 2)}
    phase7_metadata["steps_executed"].append("step4_thumbnail")

    # ========================================
    # Step 5: Add to Playlist
    # ========================================
    print(f"\n{'-'*40}")
    print("STEP 5: Add to Playlist")
    print(f"{'-'*40}")
    step_start = time.time()

    from src.youtube import add_to_playlist
    if add_to_playlist(youtube, video_id, DEFAULT_YOUTUBE_PLAYLIST):
        phase7_metadata["playlist_id"] = DEFAULT_YOUTUBE_PLAYLIST
    else:
        print(">>> Failed to add to playlist, video uploaded but not in playlist")

    step_timings["step5_playlist"] = {"duration_seconds": round(time.time() - step_start, 2)}
    phase7_metadata["steps_executed"].append("step5_playlist")

    # Save metadata to codex
    phase7_metadata["video_id"] = video_id
    phase7_metadata["video_url"] = video_url
    phase7_metadata["title"] = title
    phase7_metadata["description"] = description
    phase7_metadata["tags"] = tags
    phase7_metadata["privacy_status"] = privacy_status

    codex["story_metadata"]["phase7_youtube"] = phase7_metadata
    save_codex(codex, codex_path)

    print(f"\n>>> Phase 7 complete!")
    print(f">>> Video URL: {video_url}")

    return Phase7YouTubeResult(
        codex_path=codex_path,
        video_id=video_id,
        video_url=video_url,
        title=title,
        description=description,
        tags=tags,
        privacy_status=privacy_status,
        success=True,
        step_timings=step_timings,
    )


def main():
    """CLI entry point for standalone execution."""
    parser = argparse.ArgumentParser(
        description="Phase 7: Upload video to YouTube",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Upload video (unlisted by default)
  uv run python -m src.phases.phase7_youtube forge/20260118/codex.json

  # Upload as private
  uv run python -m src.phases.phase7_youtube forge/20260118/codex.json --privacy private

  # Upload as public (requires API audit approval)
  uv run python -m src.phases.phase7_youtube forge/20260118/codex.json --privacy public
        """
    )
    parser.add_argument(
        "codex_path",
        type=Path,
        help="Path to codex JSON file"
    )
    parser.add_argument(
        "--privacy",
        choices=["public", "unlisted", "private"],
        default=DEFAULT_YOUTUBE_PRIVACY,
        help=f"Video privacy status (default: {DEFAULT_YOUTUBE_PRIVACY})"
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"LLM model for metadata generation (default: {DEFAULT_MODEL})"
    )

    args = parser.parse_args()

    if not args.codex_path.exists():
        print(f"ERROR: Codex not found: {args.codex_path}")
        sys.exit(1)

    result = run_phase7_youtube(
        codex_path=args.codex_path,
        privacy_status=args.privacy,
        model=args.model,
    )

    if not result.success:
        print(f"\n>>> ERROR: {result.error}")
        sys.exit(1)

    print(f"\n>>> Upload complete!")
    print(f">>> Video: {result.video_url}")


if __name__ == "__main__":
    main()
