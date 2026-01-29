"""
Marcus Vane - Psychological Thriller Author.

A former journalist turned thriller writer known for tight prose
and psychological tension.
"""

from src.authors.base_author import BaseAuthor
from src.authors.styles import PlottingStyle, ScreenplayStyle, RevisionStyle
from src.authors.skills import Skill


marcus_vane = BaseAuthor(
    # === IDENTITY ===
    id="marcus_vane",
    name="Marcus Vane",
    pen_name="The Shadowsmith",
    bio="Former journalist turned thriller writer. Known for tight prose and psychological tension. "
        "His stories cut deep into the human psyche, exploring what drives people to their breaking points.",

    # === SPECIALIZATION ===
    genres=["thriller", "mystery", "noir", "psychological"],
    specialty="Psychological Thrillers",

    # === STRUCTURE KNOWLEDGE ===
    known_structures=["seven_point", "three_act"],
    preferred_structure="seven_point",

    # === PLOTTING STYLE ===
    plotting_style=PlottingStyle(
        beat_emphasis=["pinch_points", "midpoint"],  # Excels at pressure moments
        pacing="fast",
        subplot_tendency="minimal",
        twist_frequency="one_major",
    ),

    # === SCREENPLAY STYLE ===
    screenplay_style=ScreenplayStyle(
        pov="third_close",
        tense="past",
        dialogue_ratio="balanced",
        description_density="sparse",
        sentence_length="short",
        vocabulary="simple",
        tone="dark",
    ),

    # === REVISION STYLE ===
    revision_style=RevisionStyle(
        num_passes=2,
        focus_areas=["pacing", "tension", "dialogue"],
        cut_aggressively=True,
        expand_scenes=False,
    ),

    # === SKILLS ===
    skills=[
        Skill("tension_building", level=9),
        Skill("dialogue", level=7),
        Skill("foreshadowing", level=8),
        Skill("character_psychology", level=8),
        Skill("pacing", level=9),
    ],
)
