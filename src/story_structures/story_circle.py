"""
Dan Harmon's Story Circle.

An 8-step circular structure focusing on character transformation.
Source: https://channel101.fandom.com/wiki/Story_Structure_101
"""

from src.story_structures.base_structure import BaseStructure, Beat


class StoryCircle(BaseStructure):
    """Dan Harmon's Story Circle - 8 steps of character transformation."""

    name = "Dan Harmon's Story Circle"
    short_name = "story_circle"
    source = "https://channel101.fandom.com/wiki/Story_Structure_101"
    num_acts = 4  # 8 steps in 4 quadrants

    beats = [
        # Quadrant 1 - YOU/NEED (Top-right, Order)
        Beat("you", "Establish protagonist in comfort zone", quadrant=1),
        Beat("need", "They want something", quadrant=1),
        # Quadrant 2 - GO/SEARCH (Bottom-right, Chaos)
        Beat("go", "Enter unfamiliar situation", quadrant=2),
        Beat("search", "Adapt and struggle", quadrant=2),
        # Quadrant 3 - FIND/TAKE (Bottom-left, Chaos)
        Beat("find", "Get what they wanted", quadrant=3),
        Beat("take", "Pay heavy price for it", quadrant=3),
        # Quadrant 4 - RETURN/CHANGE (Top-left, Order)
        Beat("return", "Go back to familiar", quadrant=4),
        Beat("change", "They have changed", quadrant=4),
    ]

    outline_prompt = """
Structure this story using DAN HARMON'S STORY CIRCLE:

The circle represents a journey from ORDER (top) into CHAOS (bottom) and back.

## TOP HALF - ORDER (Conscious, Familiar)
1. **YOU**: Character in their zone of comfort/familiarity
   - Who is the protagonist in their normal life?
   - What is their status quo?

2. **NEED**: But they want something
   - What desire or need drives them?
   - This can be conscious or unconscious

## CROSSING DOWN INTO CHAOS
3. **GO**: They enter an unfamiliar situation
   - The threshold crossing
   - Leaving comfort zone behind

4. **SEARCH**: Adapt to it, struggle, learn
   - Face challenges in the new world
   - Learn the rules, meet allies/enemies

## BOTTOM OF THE CIRCLE - CHAOS (Unconscious, Unfamiliar)
5. **FIND**: Get what they wanted
   - Achieve their goal (or think they do)
   - The midpoint moment of seeming success

6. **TAKE**: Pay a heavy price for it
   - Consequences of achieving the goal
   - What did it cost them?

## CROSSING BACK UP TO ORDER
7. **RETURN**: Back to the familiar situation
   - Return to the ordinary world
   - But things are different now

8. **CHANGE**: Having changed
   - The protagonist is transformed
   - New equilibrium established

Scene Distribution:
- Quadrant 1 (YOU/NEED): ~25% of scenes
- Quadrant 2 (GO/SEARCH): ~25% of scenes
- Quadrant 3 (FIND/TAKE): ~25% of scenes
- Quadrant 4 (RETURN/CHANGE): ~25% of scenes
"""

    def get_scene_distribution(self, total_scenes: int) -> dict[str, list[int]]:
        """Distribute scenes across 4 quadrants."""
        scenes_per_quadrant = total_scenes // 4
        remainder = total_scenes % 4

        distribution = {}
        scene_idx = 0

        for quadrant in range(1, 5):
            q_scenes = scenes_per_quadrant + (1 if quadrant <= remainder else 0)
            distribution[f"quadrant_{quadrant}"] = list(range(scene_idx, scene_idx + q_scenes))
            scene_idx += q_scenes

        return distribution


# Singleton instance
story_circle = StoryCircle()
