"""
Base class for story structure templates.

Each structure defines:
- A set of beats (story milestones)
- Prompts for the outline agent
- Scene distribution guidance
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Beat:
    """A story beat - a required milestone in the narrative."""

    name: str
    description: str
    act: Optional[int] = None
    quadrant: Optional[int] = None  # For Story Circle

    def __str__(self) -> str:
        return f"{self.name}: {self.description}"


class BaseStructure:
    """Abstract base for story structure templates.

    Subclasses should set class attributes for:
    - name: Human-readable name
    - short_name: Machine identifier
    - source: Reference/citation
    - num_acts: Number of acts
    - beats: List of Beat objects
    - outline_prompt: Prompt for outline generation
    """

    # Identity
    name: str = ""
    short_name: str = ""
    source: str = ""

    # Structure Definition
    num_acts: int = 3
    beats: list[Beat] = []

    # Prompts
    outline_prompt: str = ""

    def get_outline_prompt(self, scope: str) -> str:
        """Returns prompt explaining this structure to outline agent.

        Args:
            scope: Story scope (flash, short, standard, long)

        Returns:
            Formatted prompt string
        """
        return self.outline_prompt

    def get_beat_definitions(self) -> str:
        """Returns detailed beat definitions for beat sheet agent."""
        lines = [f"## {self.name} Beat Definitions\n"]
        for i, beat in enumerate(self.beats, 1):
            act_info = f" (Act {beat.act})" if beat.act else ""
            quadrant_info = f" (Quadrant {beat.quadrant})" if beat.quadrant else ""
            lines.append(f"{i}. **{beat.name.upper()}**{act_info}{quadrant_info}")
            lines.append(f"   {beat.description}\n")
        return "\n".join(lines)

    def get_scene_distribution(self, total_scenes: int) -> dict[str, list[int]]:
        """Returns how scenes should be distributed across acts/beats.

        Args:
            total_scenes: Total number of scenes in the story

        Returns:
            Dict mapping act numbers to scene indices
        """
        # Default: distribute evenly across acts
        scenes_per_act = total_scenes // self.num_acts
        remainder = total_scenes % self.num_acts

        distribution = {}
        scene_idx = 0

        for act in range(1, self.num_acts + 1):
            act_scenes = scenes_per_act + (1 if act <= remainder else 0)
            distribution[f"act_{act}"] = list(range(scene_idx, scene_idx + act_scenes))
            scene_idx += act_scenes

        return distribution

    def get_beat_for_scene(self, scene_idx: int, total_scenes: int) -> Optional[Beat]:
        """Determine which beat a scene falls under.

        Args:
            scene_idx: Index of the scene (0-based)
            total_scenes: Total number of scenes

        Returns:
            The Beat this scene should focus on, or None
        """
        if not self.beats:
            return None

        # Map scene index to beat index
        beat_idx = int((scene_idx / total_scenes) * len(self.beats))
        beat_idx = min(beat_idx, len(self.beats) - 1)

        return self.beats[beat_idx]
