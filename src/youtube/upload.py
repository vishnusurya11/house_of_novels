"""
YouTube Video Upload

Handles video upload with resumable upload and exponential backoff retry.
"""

import time
import random
import http.client
import httplib2
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

from src.config import DEFAULT_YOUTUBE_CATEGORY, DEFAULT_YOUTUBE_PRIVACY


# Retry configuration
httplib2.RETRIES = 1
MAX_RETRIES = 10
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]
RETRIABLE_EXCEPTIONS = (
    httplib2.HttpLib2Error,
    IOError,
    http.client.NotConnected,
    http.client.IncompleteRead,
    http.client.ImproperConnectionState,
    http.client.CannotSendRequest,
    http.client.CannotSendHeader,
    http.client.ResponseNotReady,
    http.client.BadStatusLine,
)


@dataclass
class UploadResult:
    """Result of video upload."""
    video_id: Optional[str]
    video_url: Optional[str]
    success: bool
    error: Optional[str] = None


def upload_video(
    youtube,
    file_path: Path,
    title: str,
    description: str,
    tags: list[str] = None,
    category_id: str = None,
    privacy_status: str = None,
) -> UploadResult:
    """
    Upload a video to YouTube with metadata.

    Args:
        youtube: Authenticated YouTube API service
        file_path: Path to the video file
        title: Video title (max 100 chars)
        description: Video description
        tags: List of keyword tags
        category_id: YouTube category ID (default: 24 = Entertainment)
        privacy_status: 'public', 'private', or 'unlisted'

    Returns:
        UploadResult with video_id and url on success
    """
    file_path = Path(file_path)

    if not file_path.exists():
        return UploadResult(
            video_id=None,
            video_url=None,
            success=False,
            error=f"Video file not found: {file_path}"
        )

    # Use defaults from config
    category_id = category_id or DEFAULT_YOUTUBE_CATEGORY
    privacy_status = privacy_status or DEFAULT_YOUTUBE_PRIVACY
    tags = tags or []

    # Truncate title to 100 chars (YouTube limit)
    if len(title) > 100:
        title = title[:97] + "..."

    # Build the video resource body
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': tags,
            'categoryId': category_id,
        },
        'status': {
            'privacyStatus': privacy_status,
            'selfDeclaredMadeForKids': False,
        }
    }

    # Create MediaFileUpload with resumable=True for large files
    media = MediaFileUpload(
        str(file_path),
        chunksize=-1,  # Upload entire file in single request (still resumable)
        resumable=True,
        mimetype='video/*'
    )

    # Create the insert request
    insert_request = youtube.videos().insert(
        part='snippet,status',
        body=body,
        media_body=media
    )

    print(f">>> Uploading: {file_path.name}")
    print(f">>> Title: {title}")
    print(f">>> Privacy: {privacy_status}")

    # Execute with retry logic
    try:
        video_id = _resumable_upload(insert_request)
        if video_id:
            video_url = f"https://youtube.com/watch?v={video_id}"
            print(f">>> Upload successful! Video ID: {video_id}")
            print(f">>> URL: {video_url}")
            return UploadResult(
                video_id=video_id,
                video_url=video_url,
                success=True
            )
        else:
            return UploadResult(
                video_id=None,
                video_url=None,
                success=False,
                error="Upload returned no video ID"
            )
    except Exception as e:
        return UploadResult(
            video_id=None,
            video_url=None,
            success=False,
            error=str(e)
        )


def _resumable_upload(request) -> Optional[str]:
    """
    Execute upload with exponential backoff retry logic.

    Returns:
        Video ID on success, None on failure
    """
    response = None
    error = None
    retry = 0

    while response is None:
        try:
            status, response = request.next_chunk()

            if status:
                progress = int(status.progress() * 100)
                print(f">>> Upload progress: {progress}%")

            if response is not None:
                if 'id' in response:
                    return response['id']
                else:
                    raise Exception(f"Upload failed with unexpected response: {response}")

        except HttpError as e:
            if e.resp.status in RETRIABLE_STATUS_CODES:
                error = f"Retriable HTTP error {e.resp.status}: {e.content}"
            else:
                raise

        except RETRIABLE_EXCEPTIONS as e:
            error = f"Retriable error: {e}"

        if error is not None:
            print(f">>> {error}")
            retry += 1

            if retry > MAX_RETRIES:
                raise Exception(f"Maximum retry attempts ({MAX_RETRIES}) exceeded.")

            # Exponential backoff with jitter
            max_sleep = 2 ** retry
            sleep_seconds = random.random() * max_sleep
            print(f">>> Sleeping {sleep_seconds:.1f}s before retry {retry}/{MAX_RETRIES}...")
            time.sleep(sleep_seconds)
            error = None

    return None


def set_thumbnail(youtube, video_id: str, thumbnail_path: Path) -> bool:
    """
    Set a custom thumbnail for a video.

    Args:
        youtube: Authenticated YouTube API service
        video_id: The video ID to set thumbnail for
        thumbnail_path: Path to the thumbnail image (JPEG, PNG, GIF, BMP)

    Returns:
        True on success, False on failure
    """
    thumbnail_path = Path(thumbnail_path)

    if not thumbnail_path.exists():
        print(f">>> Thumbnail not found: {thumbnail_path}")
        return False

    try:
        media = MediaFileUpload(str(thumbnail_path), mimetype='image/png')
        youtube.thumbnails().set(
            videoId=video_id,
            media_body=media
        ).execute()
        print(f">>> Thumbnail set: {thumbnail_path.name}")
        return True
    except HttpError as e:
        print(f">>> Thumbnail upload failed: {e}")
        return False


def add_to_playlist(youtube, video_id: str, playlist_id: str) -> bool:
    """
    Add a video to a playlist.

    Args:
        youtube: Authenticated YouTube API service
        video_id: The video ID to add
        playlist_id: The playlist ID to add the video to

    Returns:
        True on success, False on failure
    """
    try:
        youtube.playlistItems().insert(
            part='snippet',
            body={
                'snippet': {
                    'playlistId': playlist_id,
                    'resourceId': {
                        'kind': 'youtube#video',
                        'videoId': video_id
                    }
                }
            }
        ).execute()
        print(f">>> Added to playlist: {playlist_id}")
        return True
    except HttpError as e:
        print(f">>> Failed to add to playlist: {e}")
        return False
