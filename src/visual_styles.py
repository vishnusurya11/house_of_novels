"""
Visual style definitions for AI image/video generation.

Provides style configurations that control the aesthetic of generated images.
Each style includes prefix (for prompt beginning) and suffix (for quality tags).

Based on 2026 AI prompt engineering best practices:
- Style keywords work best when mentioned EARLY in prompts
- Reinforced at END with technical quality tags
- Research: Leonardo.Ai, Microsoft Copilot AI Art Guides, Medium prompt engineering studies
"""

import random
from typing import TypedDict


class VisualStyle(TypedDict):
    """Visual style configuration for image generation."""
    name: str
    prefix: str  # Added early in prompts (first 1/3)
    suffix: str  # Added at end with quality tags
    description: str


# Style definitions following 2026 prompt engineering best practices
VISUAL_STYLES: dict[str, VisualStyle] = {
    "anime": {
        "name": "Anime",
        "prefix": "Anime style illustration,",
        "suffix": "anime art style, cel shaded, vibrant saturated colors, Studio Ghibli inspired, Japanese animation aesthetic, clean linework, expressive character design, high quality anime",
        "description": "Japanese anime/manga style with cel shading and vibrant colors"
    },
    "cartoon": {
        "name": "Cartoon",
        "prefix": "Cartoon illustration,",
        "suffix": "cartoon art style, hand-drawn animation quality, colorful and expressive, western animation aesthetic, bold outlines, playful character design, professional cartoon art",
        "description": "Western cartoon style with bold lines and bright colors"
    },
    # Future additions (commented out for Phase 1):
    # "pixar_3d": {
    #     "name": "Pixar 3D",
    #     "prefix": "3D animated illustration,",
    #     "suffix": "3D render, Pixar animation style, Octane render, stylized 3D, DreamWorks quality, polished CGI animation",
    #     "description": "Pixar/DreamWorks style 3D CGI animation"
    # },
    # "ghibli": {
    #     "name": "Studio Ghibli",
    #     "prefix": "Studio Ghibli style illustration,",
    #     "suffix": "Ghibli art style, Hayao Miyazaki inspired, soft watercolor aesthetic, nostalgic anime quality, hand-painted feel",
    #     "description": "Studio Ghibli's signature soft watercolor style"
    # },
    # "oil_painting": {
    #     "name": "Oil Painting",
    #     "prefix": "Oil painting artwork,",
    #     "suffix": "oil painting style, classical painting technique, rich textures, visible brushwork, museum quality art",
    #     "description": "Traditional oil painting with rich textures"
    # },
}


def get_random_style() -> VisualStyle:
    """
    Randomly select a visual style from available options.

    Returns:
        VisualStyle: Dictionary with name, prefix, suffix, and description
    """
    style_key = random.choice(list(VISUAL_STYLES.keys()))
    return VISUAL_STYLES[style_key]


def get_style_by_name(style_name: str) -> VisualStyle:
    """
    Get a specific visual style by name.

    Args:
        style_name: Style identifier (e.g., "anime", "cartoon")

    Returns:
        VisualStyle: The requested style configuration

    Raises:
        KeyError: If style_name is not found
    """
    return VISUAL_STYLES[style_name]


def get_default_style() -> VisualStyle:
    """
    Get the default fallback style (anime).

    Returns:
        VisualStyle: Default anime style configuration
    """
    return VISUAL_STYLES["anime"]
