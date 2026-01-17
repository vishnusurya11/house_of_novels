"""
Story Seed prompt configuration.

The core "one of each type" build - the baseline prompt type.
"""

from .base_config import PromptConfig


class StorySeedConfig(PromptConfig):
    """
    Simple Prompt #1: Story Seed (baseline)

    The core "one of each type" build:
    - Agent = main character
    - Engine = their motivation/drive
    - Anchor = what they want
    - Conflict = obstacle/consequence
    - Aspect = adds detail (applied to Agent)
    """

    @property
    def name(self) -> str:
        return "Story Seed"

    @property
    def description(self) -> str:
        return "Core prompt with one of each card type - a complete story concept."

    def get_card_draws(self) -> dict[str, int]:
        return {
            "agents": 4,
            "engines": 4,
            "anchors": 4,
            "conflicts": 4,
            "aspects": 4,
        }

    def get_selection_order(self) -> list[str]:
        # Start with character, then motivation, then object, obstacle, and flavor
        return ["agents", "engines", "anchors", "conflicts", "aspects"]

    def build_prompt(self, selected_cards: dict[str, str]) -> str:
        agent = selected_cards.get("agents", "???")
        engine = selected_cards.get("engines", "???")
        anchor = selected_cards.get("anchors", "???")
        conflict = selected_cards.get("conflicts", "???")
        aspect = selected_cards.get("aspects", "???")

        return f"{aspect} {agent} {engine} {anchor} {conflict}"
