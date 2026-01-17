"""
Extensible prompt configuration system for Story Engine and Deck of Worlds.
"""

from src.prompts.base_config import PromptConfig
from src.prompts.story_seed import StorySeedConfig
from src.prompts.character_concept import CharacterConceptConfig
from src.prompts.circle_of_fate import CircleOfFateConfig
from src.prompts.simple_microsetting import SimpleMicrosettingConfig
from src.prompts.complex_microsetting import ComplexMicrosettingConfig

__all__ = [
    "PromptConfig",
    # Story Engine
    "StorySeedConfig",
    "CharacterConceptConfig",
    "CircleOfFateConfig",
    # Deck of Worlds
    "SimpleMicrosettingConfig",
    "ComplexMicrosettingConfig",
]

# Registry of all available prompt types
PROMPT_CONFIGS = {
    # Story Engine prompts
    "story_seed": StorySeedConfig,
    "character_concept": CharacterConceptConfig,
    "circle_of_fate": CircleOfFateConfig,
    # Deck of Worlds prompts
    "simple_microsetting": SimpleMicrosettingConfig,
    "complex_microsetting": ComplexMicrosettingConfig,
}
