"""
The Hero's Journey (Monomyth).

Joseph Campbell's 12-stage mythic structure.
Source: "The Hero with a Thousand Faces" by Joseph Campbell
"""

from src.story_structures.base_structure import BaseStructure, Beat


class HeroesJourney(BaseStructure):
    """Campbell's Hero's Journey - 12 stages across 3 acts."""

    name = "The Hero's Journey"
    short_name = "heroes_journey"
    source = "Joseph Campbell - The Hero with a Thousand Faces"
    num_acts = 3

    beats = [
        # Act 1 - Departure (The Ordinary World)
        Beat("ordinary_world", "Hero's normal life before adventure", act=1),
        Beat("call_to_adventure", "Challenge or quest presented", act=1),
        Beat("refusal_of_call", "Initial hesitation or reluctance", act=1),
        Beat("meeting_mentor", "Guidance from a wise figure", act=1),
        Beat("crossing_threshold", "Commits to the journey, leaves ordinary world", act=1),
        # Act 2 - Initiation (The Special World)
        Beat("tests_allies_enemies", "Faces challenges, makes friends and foes", act=2),
        Beat("approach", "Prepares for the major challenge", act=2),
        Beat("ordeal", "Faces greatest fear, death and rebirth", act=2),
        Beat("reward", "Achieves goal, gains the reward/elixir", act=2),
        # Act 3 - Return (Back to Ordinary World)
        Beat("road_back", "Consequences of achievement, journey home begins", act=3),
        Beat("resurrection", "Final test, hero is transformed", act=3),
        Beat("return_elixir", "Returns home changed, shares wisdom", act=3),
    ]

    outline_prompt = """
Structure this story using THE HERO'S JOURNEY (Monomyth):

## ACT 1 - DEPARTURE (Ordinary World)
1. **ORDINARY WORLD**: Establish the hero in their normal life
   - Who are they before the adventure?
   - What is their flaw or limitation?

2. **CALL TO ADVENTURE**: A challenge disrupts their world
   - What problem or opportunity appears?
   - Why does this matter to the hero?

3. **REFUSAL OF THE CALL**: Initial hesitation
   - Why are they reluctant?
   - What fears hold them back?

4. **MEETING THE MENTOR**: Wisdom from a guide
   - Who helps prepare them?
   - What gift, advice, or training do they receive?

5. **CROSSING THE THRESHOLD**: Commitment to the journey
   - The point of no return
   - Entering the Special World

## ACT 2 - INITIATION (Special World)
6. **TESTS, ALLIES, ENEMIES**: Navigating the new world
   - What challenges do they face?
   - Who becomes friend or foe?

7. **APPROACH TO THE INMOST CAVE**: Preparing for the ordeal
   - Getting closer to the goal
   - Building to the crisis

8. **THE ORDEAL**: Death and rebirth
   - The hero's greatest fear
   - Near-death experience (literal or symbolic)

9. **REWARD (SEIZING THE SWORD)**: The prize is won
   - What do they gain?
   - Moment of triumph

## ACT 3 - RETURN (Ordinary World Transformed)
10. **THE ROAD BACK**: Journey home begins
    - Consequences of taking the reward
    - Chase or pursuit

11. **RESURRECTION**: Final test
    - One last battle
    - Hero applies all they've learned

12. **RETURN WITH THE ELIXIR**: Transformed hero returns
    - Sharing wisdom with the world
    - New equilibrium

Scene Distribution:
- Act 1 (Departure): ~25% of scenes
- Act 2 (Initiation): ~50% of scenes
- Act 3 (Return): ~25% of scenes
"""

    def get_scene_distribution(self, total_scenes: int) -> dict[str, list[int]]:
        """Standard 25/50/25 distribution for Hero's Journey."""
        act1_count = max(1, int(total_scenes * 0.25))
        act3_count = max(1, int(total_scenes * 0.25))
        act2_count = total_scenes - act1_count - act3_count

        return {
            "act_1": list(range(0, act1_count)),
            "act_2": list(range(act1_count, act1_count + act2_count)),
            "act_3": list(range(act1_count + act2_count, total_scenes)),
        }


# Singleton instance
heroes_journey = HeroesJourney()
