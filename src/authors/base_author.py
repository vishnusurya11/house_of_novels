"""
Base Author Class.

Defines the structure for author personas with their styles and skills.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional

from src.authors.styles import PlottingStyle, ScreenplayStyle, RevisionStyle
from src.authors.skills import Skill


@dataclass
class BaseAuthor:
    """Author profile with preferences, skills, and style.

    Each author has three main phases of writing:
    1. Plotting - How they structure stories
    2. Screenplay - How they tell stories in prose
    3. Revision - How they refine their work
    """

    # === IDENTITY ===
    id: str = ""
    """Unique identifier (lowercase, underscores)"""

    name: str = ""
    """Display name"""

    pen_name: str = ""
    """Optional pen name"""

    bio: str = ""
    """Short author bio"""

    # === SPECIALIZATION ===
    genres: list[str] = field(default_factory=list)
    """List of genres they write"""

    specialty: str = ""
    """Their main specialty"""

    # === STRUCTURE KNOWLEDGE ===
    known_structures: list[str] = field(default_factory=lambda: ["three_act"])
    """Structures they know how to use"""

    preferred_structure: str = "three_act"
    """Default structure choice"""

    # === WRITING STYLES ===
    plotting_style: PlottingStyle = field(default_factory=PlottingStyle)
    """How they approach story structure"""

    screenplay_style: ScreenplayStyle = field(default_factory=ScreenplayStyle)
    """How they tell stories in prose"""

    revision_style: RevisionStyle = field(default_factory=RevisionStyle)
    """How they revise their work"""

    # === SKILLS ===
    skills: list[Skill] = field(default_factory=list)
    """Author's developed skills"""

    # === PERFORMANCE TRACKING ===
    stories_written: int = 0
    """Number of stories completed"""

    total_views: int = 0
    """Total views across all stories"""

    avg_reception: float = 0.0
    """Average reception score (0-10)"""

    best_performing_genre: Optional[str] = None
    """Genre with best performance"""

    def to_dict(self) -> dict:
        """Convert author to dictionary for serialization (e.g., storing in codex)."""
        return {
            "id": self.id,
            "name": self.name,
            "pen_name": self.pen_name,
            "bio": self.bio,
            "genres": self.genres,
            "specialty": self.specialty,
            "known_structures": self.known_structures,
            "preferred_structure": self.preferred_structure,
            "plotting_style": self.plotting_style.to_dict(),
            "screenplay_style": self.screenplay_style.to_dict(),
            "revision_style": self.revision_style.to_dict(),
            "skills": [s.to_dict() for s in self.skills],
            "stories_written": self.stories_written,
            "total_views": self.total_views,
            "avg_reception": self.avg_reception,
            "best_performing_genre": self.best_performing_genre,
        }

    def learn_structure(self, structure_id: str) -> None:
        """Author learns a new story structure.

        Args:
            structure_id: Short name of the structure to learn
        """
        if structure_id not in self.known_structures:
            self.known_structures.append(structure_id)

    def learn_skill(self, skill: Skill) -> None:
        """Author gains a new skill.

        Args:
            skill: The Skill to add
        """
        existing = self.get_skill(skill.name)
        if existing is None:
            self.skills.append(skill)
        else:
            # Upgrade existing skill if new one is better
            if skill.level > existing.level:
                existing.level = skill.level

    def get_skill(self, skill_name: str) -> Optional[Skill]:
        """Get a skill by name.

        Args:
            skill_name: Name of the skill

        Returns:
            The Skill if found, None otherwise
        """
        for skill in self.skills:
            if skill.name == skill_name:
                return skill
        return None

    def improve_skill(self, skill_name: str, amount: float = 0.5) -> bool:
        """Author improves an existing skill.

        Args:
            skill_name: Name of skill to improve
            amount: How much to improve (default 0.5)

        Returns:
            True if skill was found and improved, False otherwise
        """
        skill = self.get_skill(skill_name)
        if skill:
            skill.improve(amount)
            return True
        return False

    def get_skill_level(self, skill_name: str) -> int:
        """Get skill level, returns 0 if skill not found."""
        skill = self.get_skill(skill_name)
        return skill.level if skill else 0

    def get_full_prompt_modifier(self) -> str:
        """Get combined prompt modifiers from all styles and skills.

        Returns:
            Complete prompt modifier string for this author
        """
        sections = []

        # Author identity
        sections.append(f"## Author: {self.name}")
        if self.pen_name:
            sections.append(f"*Writing as {self.pen_name}*")
        sections.append(f"\n{self.bio}\n")

        # Specialization
        if self.specialty:
            sections.append(f"**Specialty**: {self.specialty}")
        if self.genres:
            sections.append(f"**Genres**: {', '.join(self.genres)}")

        # Style modifiers
        sections.append("\n### Writing Style")
        sections.append(self.screenplay_style.get_prompt_modifier())

        # Skill modifiers
        if self.skills:
            sections.append("\n### Author Strengths")
            for skill in sorted(self.skills, key=lambda s: s.level, reverse=True)[:5]:
                sections.append(f"- {skill.get_prompt_modifier()}")

        return "\n".join(sections)

    def record_story(self, views: int = 0, reception: float = 0.0, genre: Optional[str] = None) -> None:
        """Record a completed story for performance tracking.

        Args:
            views: Number of views this story received
            reception: Reception score (0-10)
            genre: Genre of the story
        """
        self.stories_written += 1
        self.total_views += views

        # Update rolling average reception
        if self.stories_written == 1:
            self.avg_reception = reception
        else:
            # Weighted rolling average (recent stories matter more)
            self.avg_reception = (self.avg_reception * 0.7) + (reception * 0.3)

        # Track best performing genre (simplified)
        if genre and reception > 7.0:
            self.best_performing_genre = genre
