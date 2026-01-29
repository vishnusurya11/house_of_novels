"""
Traditional Three-Act Structure.

The classic beginning-middle-end framework used in most Western storytelling.
"""

from src.story_structures.base_structure import BaseStructure, Beat


class ThreeActStructure(BaseStructure):
    """Traditional three-act story structure."""

    name = "Three-Act Structure"
    short_name = "three_act"
    source = "Aristotle's Poetics / Syd Field"
    num_acts = 3

    beats = [
        # Act 1 - Setup (25%)
        Beat("exposition", "Introduce protagonist, world, and status quo", act=1),
        Beat("inciting_incident", "Event that disrupts the status quo", act=1),
        Beat("first_plot_point", "Protagonist commits to the journey", act=1),
        # Act 2 - Confrontation (50%)
        Beat("rising_action", "Obstacles and complications increase", act=2),
        Beat("midpoint", "Major revelation or reversal", act=2),
        Beat("crisis", "Lowest point, all seems lost", act=2),
        # Act 3 - Resolution (25%)
        Beat("climax", "Final confrontation, protagonist faces ultimate challenge", act=3),
        Beat("resolution", "New equilibrium established", act=3),
    ]

    outline_prompt = """
Structure this story using the CLASSIC THREE-ACT STRUCTURE:

## ACT 1 - SETUP (First 25% of story)
- **EXPOSITION**: Establish protagonist in their ordinary world
- **INCITING INCIDENT**: Something disrupts the status quo
- **FIRST PLOT POINT**: Protagonist commits to confronting the problem

## ACT 2 - CONFRONTATION (Middle 50% of story)
- **RISING ACTION**: Obstacles escalate, stakes increase
- **MIDPOINT**: Major revelation changes everything (often a false victory or defeat)
- **CRISIS**: Darkest moment, protagonist faces their deepest fear

## ACT 3 - RESOLUTION (Final 25% of story)
- **CLIMAX**: Final confrontation where protagonist must prove transformation
- **RESOLUTION**: New normal established, story questions answered

Scene Distribution:
- Act 1: ~25% of scenes
- Act 2: ~50% of scenes
- Act 3: ~25% of scenes
"""

    def get_scene_distribution(self, total_scenes: int) -> dict[str, list[int]]:
        """Custom distribution: 25% / 50% / 25%."""
        act1_count = max(1, int(total_scenes * 0.25))
        act3_count = max(1, int(total_scenes * 0.25))
        act2_count = total_scenes - act1_count - act3_count

        return {
            "act_1": list(range(0, act1_count)),
            "act_2": list(range(act1_count, act1_count + act2_count)),
            "act_3": list(range(act1_count + act2_count, total_scenes)),
        }


# Singleton instance
three_act_structure = ThreeActStructure()
