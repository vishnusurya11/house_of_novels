"""
YouTube Module

Provides YouTube OAuth credentials management and video upload functionality.
"""

from .credentials import (
    YouTubeCredentialsManager,
    get_youtube_service,
    validate_youtube_credentials,
)
from .upload import upload_video, UploadResult, set_thumbnail, add_to_playlist, create_playlist
from .schedule import claim_slots, release_slots

__all__ = [
    "YouTubeCredentialsManager",
    "get_youtube_service",
    "validate_youtube_credentials",
    "upload_video",
    "UploadResult",
    "set_thumbnail",
    "add_to_playlist",
    "create_playlist",
    "claim_slots",
    "release_slots",
]
