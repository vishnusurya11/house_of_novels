"""
Seven-Point Story Structure.

A plot-driven structure focusing on key turning points.
Source: https://reedsy.com/blog/guide/story-structure/seven-point-story-structure/
"""

from src.story_structures.base_structure import BaseStructure, Beat


class SevenPointStructure(BaseStructure):
    """Seven-Point Story Structure for plot-driven narratives."""

    name = "Seven-Point Story Structure"
    short_name = "seven_point"
    source = "https://reedsy.com/blog/guide/story-structure/seven-point-story-structure/"
    num_acts = 3

    beats = [
        Beat("hook", "Opening state - opposite of resolution", act=1),
        Beat("plot_turn_1", "Call to adventure - world changes", act=1),
        Beat("pinch_point_1", "First major pressure/antagonist force", act=2),
        Beat("midpoint", "Protagonist shifts from reactive to proactive", act=2),
        Beat("pinch_point_2", "Second major pressure - all seems lost", act=2),
        Beat("plot_turn_2", "Final piece of puzzle - power to win", act=3),
        Beat("resolution", "Final state - opposite of hook", act=3),
    ]

    outline_prompt = """
Structure this story using the SEVEN-POINT STRUCTURE:

1. **HOOK**: Show protagonist in their "before" state (opposite of where they'll end)
   - This is who they are BEFORE transformation
   - Should mirror/contrast with the resolution

2. **PLOT TURN 1**: Something disrupts their world, forces them into the story
   - The call to adventure
   - New information or event that changes everything

3. **PINCH POINT 1**: Antagonist applies pressure, stakes become real
   - First major obstacle or setback
   - Shows what protagonist is up against

4. **MIDPOINT**: Protagonist stops reacting, starts taking charge
   - Shift from passive to active
   - Often involves gaining crucial knowledge or making a decision

5. **PINCH POINT 2**: Everything falls apart, darkest moment
   - Second major pressure from antagonist
   - Protagonist loses something important
   - All seems lost

6. **PLOT TURN 2**: Discovery/revelation that gives them power to succeed
   - Final piece of the puzzle falls into place
   - Protagonist gains what they need to win

7. **RESOLUTION**: Protagonist in transformed "after" state
   - Opposite of the hook
   - Story question answered

Scene Distribution:
- Hook + Plot Turn 1: ~25% of scenes
- Pinch 1 + Midpoint + Pinch 2: ~50% of scenes
- Plot Turn 2 + Resolution: ~25% of scenes
"""

    def get_scene_distribution(self, total_scenes: int) -> dict[str, list[int]]:
        """Custom distribution matching 7-point structure."""
        # 25% setup, 50% middle, 25% resolution
        setup_count = max(1, int(total_scenes * 0.25))
        resolution_count = max(1, int(total_scenes * 0.25))
        middle_count = total_scenes - setup_count - resolution_count

        return {
            "act_1": list(range(0, setup_count)),  # Hook + Plot Turn 1
            "act_2": list(range(setup_count, setup_count + middle_count)),  # Pinch points + Midpoint
            "act_3": list(range(setup_count + middle_count, total_scenes)),  # Plot Turn 2 + Resolution
        }


# Singleton instance
seven_point_structure = SevenPointStructure()
