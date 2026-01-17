"""
Story Builder Agents - Multi-phase story generation pipeline.

Phase 1: Outline generation with structure/pacing critique
Phase 2: Character and location building with consistency checks
Phase 3: Narrative writing with style/continuity critique
Phase 4: Image prompt generation for characters and locations
"""

from src.story_agents.base_story_agent import BaseStoryAgent
from src.story_agents.outline_agents import (
    OutlinerAgent,
    StructureCriticAgent,
    PacingCriticAgent,
)
from src.story_agents.character_agents import (
    CharacterBuilderAgent,
    LocationBuilderAgent,
    ConsistencyCriticAgent,
)
from src.story_agents.name_agents import (
    NameCreativeAgent,
    NameAuthenticAgent,
    NameDistinctiveAgent,
    generate_character_names_via_debate,
)
from src.story_agents.narrative_agents import (
    WriterAgent,
    StyleCriticAgent,
    ContinuityCriticAgent,
)
from src.story_agents.reviser_agent import ReviserAgent
from src.story_agents.image_prompt_agents import (
    CharacterImagePromptAgent,
    LocationImagePromptAgent,
    SceneImagePromptAgent,
    SceneImagePromptCriticAgent,
    # Single poster (fallback)
    StoryPosterPromptAgent,
    StoryPosterCriticAgent,
    # Multi-agent poster system
    CinematicPosterAgent,
    IllustratedPosterAgent,
    GraphicPosterAgent,
    PosterJuryImpactAgent,
    PosterJuryStoryAgent,
    PosterJuryAestheticAgent,
    PosterJurySupervisor,
)
from src.story_agents.character_prompt_agents import (
    CharacterPromptCreatorAgent,
    CharacterPromptCriticAgent,
    generate_character_prompt,
)
from src.story_agents.location_prompt_agents import (
    LocationPromptCreatorAgent,
    LocationPromptCriticAgent,
    generate_location_prompt,
)
from src.story_agents.storyboard_agents import (
    StoryboardCreatorAgent,
    VisualCriticAgent,
    DialogueCriticAgent,
    ContinuityCriticAgent,
    generate_scene_storyboard,
)

__all__ = [
    "BaseStoryAgent",
    # Phase 1
    "OutlinerAgent",
    "StructureCriticAgent",
    "PacingCriticAgent",
    # Phase 2a - Name Generation
    "NameCreativeAgent",
    "NameAuthenticAgent",
    "NameDistinctiveAgent",
    "generate_character_names_via_debate",
    # Phase 2b - Characters & Locations
    "CharacterBuilderAgent",
    "LocationBuilderAgent",
    "ConsistencyCriticAgent",
    # Phase 3
    "WriterAgent",
    "StyleCriticAgent",
    "ContinuityCriticAgent",
    # Phase 4 - Image Prompts
    "CharacterImagePromptAgent",
    "LocationImagePromptAgent",
    "SceneImagePromptAgent",
    "SceneImagePromptCriticAgent",
    # Single poster (fallback)
    "StoryPosterPromptAgent",
    "StoryPosterCriticAgent",
    # Multi-agent poster system
    "CinematicPosterAgent",
    "IllustratedPosterAgent",
    "GraphicPosterAgent",
    "PosterJuryImpactAgent",
    "PosterJuryStoryAgent",
    "PosterJuryAestheticAgent",
    "PosterJurySupervisor",
    # Shared
    "ReviserAgent",
    # Phase 4 - Character Prompts (creator+critic system)
    "CharacterPromptCreatorAgent",
    "CharacterPromptCriticAgent",
    "generate_character_prompt",
    # Phase 4 - Location Prompts (creator+critic system)
    "LocationPromptCreatorAgent",
    "LocationPromptCriticAgent",
    "generate_location_prompt",
    # Phase 3b - Storyboard (scene breakdown into shots)
    "StoryboardCreatorAgent",
    "VisualCriticAgent",
    "DialogueCriticAgent",
    "ContinuityCriticAgent",
    "generate_scene_storyboard",
]
