"""
Story Structures Module.

Provides templates for different narrative structures that authors can use.
"""

from src.story_structures.base_structure import BaseStructure, Beat
from src.story_structures.three_act import ThreeActStructure
from src.story_structures.seven_point import SevenPointStructure
from src.story_structures.story_circle import StoryCircle
from src.story_structures.heroes_journey import HeroesJourney
from src.story_structures.registry import (
    STRUCTURE_REGISTRY,
    get_structure,
    list_structures,
)

__all__ = [
    "BaseStructure",
    "Beat",
    "ThreeActStructure",
    "SevenPointStructure",
    "StoryCircle",
    "HeroesJourney",
    "STRUCTURE_REGISTRY",
    "get_structure",
    "list_structures",
]
