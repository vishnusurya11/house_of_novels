#!/usr/bin/env python3
"""
Phase 5: YouTube Upload (Per-Chapter)

Uploads individual chapter videos to YouTube with scheduled publishing,
shared thumbnails, and part numbering.

Steps:
    1: Discover chapter videos from Phase 4 output
    2: Claim schedule slots from visurena_studio.db
    3: Authenticate with YouTube API
    4: Select shared thumbnail (random poster)
    5: Upload each chapter video with scheduling
    6: Save upload metadata to codex

Usage (standalone):
    uv run python -m src.phases.phase5_upload forge/xxx/codex.json
    uv run python -m src.phases.phase5_upload codex.json --privacy unlisted
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
from src.config import (
    DEFAULT_YOUTUBE_PRIVACY,
    DEFAULT_MODEL,
    DEFAULT_YOUTUBE_PLAYLIST,
    COMFYUI_OUTPUT_DIR,
    SCHEDULE_DB_PATH,
    ENVIRONMENT,
)


@dataclass
class Phase5UploadResult:
    """Result of Phase 5 YouTube upload."""
    codex_path: Path
    upload_mode: str = "per_chapter"
    total_chapters: int = 0
    uploaded_count: int = 0
    video_ids: list[str] = field(default_factory=list)
    video_urls: list[str] = field(default_factory=list)
    success: bool = False
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
    chapters_data = story.get("chapters", {})

    title = chapters_data.get("title", outline.get("title", "Untitled Story"))
    logline = outline.get("logline", "A captivating story.")

    chapters = chapters_data.get("chapters", [])
    chapter_titles = []
    for ch in chapters:
        ch_title = ch.get("chapter_title", ch.get("title", f"Chapter {ch.get('chapter_number', '?')}"))
        chapter_titles.append(ch_title)

    return {
        "title": title,
        "logline": logline,
        "chapter_titles": chapter_titles,
    }


def find_chapter_videos(codex_path: Path) -> list[tuple[int, Path]]:
    """Find per-chapter video files from Phase 4 output.

    Args:
        codex_path: Path to the codex JSON file.

    Returns:
        Sorted list of (chapter_number, video_path) tuples.
    """
    forge_dir = codex_path.parent
    videos_dir = forge_dir / "videos"

    if not videos_dir.exists():
        return []

    chapter_videos = []
    for mp4 in sorted(videos_dir.glob("chapter_*.mp4")):
        # Parse chapter number from filename: chapter_01.mp4 → 1
        try:
            ch_num = int(mp4.stem.split("_")[1])
            chapter_videos.append((ch_num, mp4))
        except (IndexError, ValueError):
            continue

    return chapter_videos


def find_random_poster(codex: dict) -> Optional[Path]:
    """Find a random poster image from the codex poster generation data."""
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


def run_phase5_upload(
    codex_path: Path,
    privacy_status: str = None,
    model: str = None,
) -> Phase5UploadResult:
    """
    Run Phase 5: Per-Chapter YouTube Upload with Schedule Integration.

    Steps:
        1: Discover chapter videos
        2: Claim schedule slots from DB
        3: Authenticate with YouTube API
        4: Select shared thumbnail
        5: Upload each chapter video
        6: Save metadata to codex

    Args:
        codex_path: Path to codex JSON file
        privacy_status: Video privacy ('public', 'unlisted', 'private')
        model: LLM model for metadata generation (unused, kept for interface compat)

    Returns:
        Phase5UploadResult with upload status and video URLs
    """
    codex_path = Path(codex_path)
    privacy_status = privacy_status or DEFAULT_YOUTUBE_PRIVACY
    step_timings = {}

    print(f"\n{'='*60}")
    print("PHASE 5: YOUTUBE UPLOAD (Per-Chapter)")
    print(f"{'='*60}")
    print(f">>> Codex: {codex_path}")
    print(f">>> Privacy: {privacy_status}")
    print(f">>> Environment: {ENVIRONMENT}")

    codex = load_codex(codex_path)

    if "metadata" not in codex:
        codex["metadata"] = {}

    phase5_metadata = {
        "phase": 5,
        "name": "YouTube Upload (Per-Chapter)",
        "upload_mode": "per_chapter",
        "steps_executed": [],
    }

    # ========================================
    # Step 1: Discover chapter videos
    # ========================================
    print(f"\n{'-'*40}")
    print("STEP 1: Discover Chapter Videos")
    print(f"{'-'*40}")
    step_start = time.time()

    chapter_videos = find_chapter_videos(codex_path)
    if not chapter_videos:
        return Phase5UploadResult(
            codex_path=codex_path,
            error="No chapter videos found. Run Phase 4 (editing) first.",
        )

    total_chapters = len(chapter_videos)
    print(f">>> Found {total_chapters} chapter videos")
    for ch_num, path in chapter_videos:
        size_mb = path.stat().st_size / (1024 * 1024)
        print(f"    Chapter {ch_num}: {path.name} ({size_mb:.1f} MB)")

    step_timings["step1_discover"] = {"duration_seconds": round(time.time() - step_start, 2)}
    phase5_metadata["steps_executed"].append("step1_discover")
    phase5_metadata["total_chapters"] = total_chapters

    # ========================================
    # Step 2: Claim schedule slots from DB
    # ========================================
    print(f"\n{'-'*40}")
    print("STEP 2: Claim Schedule Slots")
    print(f"{'-'*40}")
    step_start = time.time()

    # Use forge timestamp as book_id
    forge_dir = codex_path.parent
    book_id = forge_dir.name  # e.g., "20260310073812"

    story_data = extract_story_data(codex)
    book_name = story_data["title"]

    schedule_slots = []
    try:
        from src.youtube.schedule import claim_slots
        schedule_slots = claim_slots(
            book_id=book_id,
            book_name=book_name,
            num_chapters=total_chapters,
        )
        if schedule_slots:
            print(f">>> Claimed {len(schedule_slots)} slots for '{book_name}'")
            for slot in schedule_slots:
                print(f"    Part {slot['part']}: {slot['time_slot']} → {slot['publish_at']}")
        else:
            print(">>> No schedule slots available — uploading without scheduling")
    except FileNotFoundError:
        print(f">>> Schedule DB not found at {SCHEDULE_DB_PATH} — uploading without scheduling")
    except Exception as e:
        print(f">>> Schedule DB error: {e} — uploading without scheduling")

    step_timings["step2_schedule"] = {"duration_seconds": round(time.time() - step_start, 2)}
    phase5_metadata["steps_executed"].append("step2_schedule")
    phase5_metadata["schedule_book_id"] = book_id

    # ========================================
    # Step 3: Authenticate with YouTube
    # ========================================
    print(f"\n{'-'*40}")
    print("STEP 3: Authenticate with YouTube")
    print(f"{'-'*40}")
    step_start = time.time()

    try:
        from src.youtube import get_youtube_service
        youtube = get_youtube_service()
        print(">>> YouTube authentication successful")
    except Exception as e:
        # Release slots on auth failure
        if schedule_slots:
            try:
                from src.youtube.schedule import release_slots
                release_slots(book_id)
            except Exception:
                pass
        return Phase5UploadResult(
            codex_path=codex_path,
            total_chapters=total_chapters,
            error=f"YouTube authentication failed: {e}",
        )

    step_timings["step3_auth"] = {"duration_seconds": round(time.time() - step_start, 2)}
    phase5_metadata["steps_executed"].append("step3_auth")

    # ========================================
    # Step 4: Select shared thumbnail
    # ========================================
    print(f"\n{'-'*40}")
    print("STEP 4: Select Shared Thumbnail")
    print(f"{'-'*40}")
    step_start = time.time()

    thumbnail_path = find_random_poster(codex)
    if thumbnail_path:
        print(f">>> Thumbnail: {thumbnail_path.name}")
        phase5_metadata["shared_thumbnail"] = str(thumbnail_path)
    else:
        print(">>> No poster images found — chapters will have no custom thumbnail")

    step_timings["step4_thumbnail"] = {"duration_seconds": round(time.time() - step_start, 2)}
    phase5_metadata["steps_executed"].append("step4_thumbnail")

    # ========================================
    # Step 4b: Create book-specific playlist
    # ========================================
    print(f"\n{'-'*40}")
    print("STEP 4b: Create Book Playlist")
    print(f"{'-'*40}")
    step_start = time.time()

    from src.youtube import upload_video, set_thumbnail, add_to_playlist, create_playlist

    book_playlist_id = None
    try:
        book_playlist_id = create_playlist(
            youtube,
            title=book_name,
            description=story_data["logline"],
        )
        if book_playlist_id:
            phase5_metadata["book_playlist_id"] = book_playlist_id
        else:
            print(">>> Book playlist creation failed — will use env playlist only")
    except Exception as e:
        print(f">>> Book playlist error: {e} — will use env playlist only")

    step_timings["step4b_playlist"] = {"duration_seconds": round(time.time() - step_start, 2)}
    phase5_metadata["steps_executed"].append("step4b_playlist")

    # ========================================
    # Step 5: Upload each chapter video
    # ========================================
    print(f"\n{'-'*40}")
    print("STEP 5: Upload Chapter Videos")
    print(f"{'-'*40}")
    step_start = time.time()
    from src.story_agents.youtube_metadata_agent import generate_chapter_youtube_metadata

    chapter_results = []
    video_ids = []
    video_urls = []

    for ch_num, video_path in chapter_videos:
        print(f"\n  --- Chapter {ch_num} of {total_chapters} ---")

        # Generate metadata
        ch_title = ""
        if ch_num - 1 < len(story_data["chapter_titles"]):
            ch_title = story_data["chapter_titles"][ch_num - 1]

        metadata = generate_chapter_youtube_metadata(
            story_title=book_name,
            logline=story_data["logline"],
            chapter_number=ch_num,
            total_chapters=total_chapters,
            chapter_title=ch_title,
        )

        # Determine publish_at from schedule slot
        publish_at = None
        slot_info = None
        if schedule_slots:
            matching = [s for s in schedule_slots if s["part"] == ch_num]
            if matching:
                slot_info = matching[0]
                publish_at = slot_info["publish_at"]

        print(f"  Title: {metadata.title}")
        if publish_at:
            print(f"  Scheduled: {publish_at}")
        else:
            print(f"  Publishing: immediate ({privacy_status})")

        # Upload
        try:
            result = upload_video(
                youtube=youtube,
                file_path=video_path,
                title=metadata.title,
                description=metadata.description,
                tags=metadata.tags,
                privacy_status=privacy_status,
                publish_at=publish_at,
            )

            if not result.success:
                print(f"  ERROR: {result.error}")
                chapter_results.append({
                    "chapter_number": ch_num,
                    "success": False,
                    "error": result.error,
                })
                continue

            video_id = result.video_id
            video_url = result.video_url
            video_ids.append(video_id)
            video_urls.append(video_url)

            print(f"  Uploaded: {video_url}")

            # Set thumbnail (same poster for all chapters)
            if thumbnail_path:
                set_thumbnail(youtube, video_id, thumbnail_path)

            # Add to book playlist (chapters added in order = correct playlist order)
            if book_playlist_id:
                add_to_playlist(youtube, video_id, book_playlist_id)

            # Add to environment-wide playlist
            add_to_playlist(youtube, video_id, DEFAULT_YOUTUBE_PLAYLIST)

            ch_result = {
                "chapter_number": ch_num,
                "part": f"Part {ch_num} of {total_chapters}",
                "video_id": video_id,
                "video_url": video_url,
                "title": metadata.title,
                "success": True,
            }
            if slot_info:
                ch_result["publish_at"] = slot_info["publish_at"]
                ch_result["time_slot"] = slot_info["time_slot"]

            chapter_results.append(ch_result)

        except Exception as e:
            print(f"  ERROR: {e}")
            chapter_results.append({
                "chapter_number": ch_num,
                "success": False,
                "error": str(e),
            })

    uploaded_count = len(video_ids)
    step_timings["step5_uploads"] = {"duration_seconds": round(time.time() - step_start, 2)}
    phase5_metadata["steps_executed"].append("step5_uploads")

    # Release slots for chapters that failed to upload
    if schedule_slots:
        failed_parts = [
            r["chapter_number"] for r in chapter_results if not r.get("success")
        ]
        if failed_parts:
            print(f"\n>>> {len(failed_parts)} chapters failed — their slots remain claimed")

    # ========================================
    # Step 6: Save metadata to codex
    # ========================================
    print(f"\n{'-'*40}")
    print("STEP 6: Save Metadata")
    print(f"{'-'*40}")

    phase5_metadata["uploaded_count"] = uploaded_count
    phase5_metadata["playlist_id"] = DEFAULT_YOUTUBE_PLAYLIST
    phase5_metadata["chapters"] = chapter_results

    codex["metadata"]["phase_5"] = phase5_metadata
    save_codex(codex, codex_path)

    print(f"\n>>> Phase 5 complete!")
    print(f">>> Uploaded: {uploaded_count}/{total_chapters} chapters")
    for url in video_urls:
        print(f"    {url}")

    return Phase5UploadResult(
        codex_path=codex_path,
        upload_mode="per_chapter",
        total_chapters=total_chapters,
        uploaded_count=uploaded_count,
        video_ids=video_ids,
        video_urls=video_urls,
        success=uploaded_count > 0,
        step_timings=step_timings,
    )


def main():
    """CLI entry point for standalone execution."""
    parser = argparse.ArgumentParser(
        description="Phase 5: Upload per-chapter videos to YouTube",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Upload chapter videos (public by default, scheduled via DB)
  uv run python -m src.phases.phase5_upload forge/20260118/codex.json

  # Upload as unlisted (no scheduling)
  uv run python -m src.phases.phase5_upload forge/20260118/codex.json --privacy unlisted
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

    args = parser.parse_args()

    if not args.codex_path.exists():
        print(f"ERROR: Codex not found: {args.codex_path}")
        sys.exit(1)

    result = run_phase5_upload(
        codex_path=args.codex_path,
        privacy_status=args.privacy,
    )

    if not result.success:
        print(f"\n>>> ERROR: {result.error}")
        sys.exit(1)

    print(f"\n>>> Upload complete! {result.uploaded_count} chapters uploaded.")


if __name__ == "__main__":
    main()
