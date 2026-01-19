"""
Template 1: Static Audio

Static images with narrated audio for each scene.
- Generates character portraits, location images, posters, and scene images
- Generates TTS audio for narrative text
- Combines audio and images into scene videos
- Concatenates scene videos into final video
"""

from .template import StaticAudioTemplate

__all__ = ["StaticAudioTemplate"]
