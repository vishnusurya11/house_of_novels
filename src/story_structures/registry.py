"""
Story Structure Registry.

Central registry for all available story structures.
"""

from typing import Optional

from src.story_structures.base_structure import BaseStructure
from src.story_structures.three_act import ThreeActStructure
from src.story_structures.seven_point import SevenPointStructure
from src.story_structures.story_circle import StoryCircle
from src.story_structures.heroes_journey import HeroesJourney


# Registry of all available structures
STRUCTURE_REGISTRY: dict[str, BaseStructure] = {
    "three_act": ThreeActStructure(),
    "seven_point": SevenPointStructure(),
    "story_circle": StoryCircle(),
    "heroes_journey": HeroesJourney(),
}

# Default structure
DEFAULT_STRUCTURE = "three_act"


def get_structure(short_name: Optional[str] = None) -> BaseStructure:
    """Get a story structure by short name.

    Args:
        short_name: The structure's short name (e.g., "seven_point").
                   If None, returns the default structure.

    Returns:
        The requested BaseStructure instance.

    Raises:
        ValueError: If structure not found in registry.
    """
    if short_name is None:
        short_name = DEFAULT_STRUCTURE

    if short_name not in STRUCTURE_REGISTRY:
        available = ", ".join(STRUCTURE_REGISTRY.keys())
        raise ValueError(
            f"Unknown structure: '{short_name}'. Available: {available}"
        )

    return STRUCTURE_REGISTRY[short_name]


def list_structures() -> list[dict]:
    """List all available story structures.

    Returns:
        List of dicts with structure info (short_name, name, source, num_acts).
    """
    return [
        {
            "short_name": structure.short_name,
            "name": structure.name,
            "source": structure.source,
            "num_acts": structure.num_acts,
            "num_beats": len(structure.beats),
        }
        for structure in STRUCTURE_REGISTRY.values()
    ]
