"""
Author Skills.

Skills represent capabilities that authors can have and develop over time.
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional


@dataclass
class Skill:
    """A skill that an author possesses.

    Skills can be improved over time based on feedback and practice.
    """

    name: str
    """Skill name (e.g., "tension_building", "dialogue", "foreshadowing")"""

    level: int = 5
    """Skill level from 1-10"""

    learned_date: Optional[str] = None
    """ISO date when skill was learned (for tracking growth)"""

    def __post_init__(self):
        """Validate skill level."""
        if not 1 <= self.level <= 10:
            raise ValueError(f"Skill level must be 1-10, got {self.level}")
        if self.learned_date is None:
            self.learned_date = datetime.now().isoformat()[:10]

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return asdict(self)

    def improve(self, amount: float = 0.5) -> None:
        """Improve the skill level.

        Args:
            amount: How much to improve (default 0.5)
        """
        new_level = min(10, self.level + amount)
        self.level = int(new_level) if new_level == int(new_level) else new_level

    def get_prompt_modifier(self) -> str:
        """Get prompt modifier based on skill level.

        Returns:
            String describing how this skill affects writing.
        """
        skill_descriptions = {
            "tension_building": {
                "low": "Build basic tension through conflict.",
                "mid": "Create sustained tension with strategic releases.",
                "high": "Master tension, making readers unable to look away.",
            },
            "dialogue": {
                "low": "Write functional dialogue that conveys information.",
                "mid": "Craft natural dialogue with distinct character voices.",
                "high": "Create dialogue that crackles with subtext and personality.",
            },
            "foreshadowing": {
                "low": "Include basic hints about future events.",
                "mid": "Plant subtle seeds that pay off satisfyingly.",
                "high": "Weave foreshadowing so seamlessly readers only notice on reread.",
            },
            "character_psychology": {
                "low": "Give characters clear motivations.",
                "mid": "Create psychologically consistent characters.",
                "high": "Craft complex characters with layered psychology.",
            },
            "world_building": {
                "low": "Establish the basic setting.",
                "mid": "Create a believable world with consistent rules.",
                "high": "Build immersive worlds that feel lived-in.",
            },
            "pacing": {
                "low": "Maintain a steady narrative pace.",
                "mid": "Vary pacing to match story needs.",
                "high": "Master rhythm, knowing exactly when to speed up or slow down.",
            },
            "prose_style": {
                "low": "Write clear, readable prose.",
                "mid": "Develop a distinctive voice.",
                "high": "Craft prose that's a pleasure to read sentence by sentence.",
            },
            "emotional_resonance": {
                "low": "Include emotional moments.",
                "mid": "Create scenes that resonate emotionally.",
                "high": "Write scenes that stay with readers long after.",
            },
        }

        # Determine skill tier
        if self.level <= 3:
            tier = "low"
        elif self.level <= 6:
            tier = "mid"
        else:
            tier = "high"

        # Get description for this skill
        if self.name in skill_descriptions:
            return skill_descriptions[self.name][tier]

        # Generic fallback
        return f"{self.name.replace('_', ' ').title()} (Level {self.level}/10)"


# Common skills that authors might have
COMMON_SKILLS = [
    "tension_building",
    "dialogue",
    "foreshadowing",
    "character_psychology",
    "world_building",
    "pacing",
    "prose_style",
    "emotional_resonance",
    "plot_structure",
    "sensory_detail",
    "subtext",
    "humor",
]
