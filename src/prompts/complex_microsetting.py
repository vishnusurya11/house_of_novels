"""
Complex Microsetting prompt configuration for Deck of Worlds.

Richer worldbuilding unit with multiple landmarks and attributes.
"""

from .base_config import PromptConfig


class ComplexMicrosettingConfig(PromptConfig):
    """
    Complex Microsetting: Richer Deck of Worlds worldbuilding unit.

    Draws multiple cards for landmarks, namesakes, and attributes:
    - Region = main terrain/environment (hub)
    - Landmark x2 = two points of interest
    - Namesake x2 = two in-world nicknames
    - Origin = significant past event
    - Attribute x2 = two present-day features
    - Advent = future hook/event
    """

    @property
    def name(self) -> str:
        return "Complex Microsetting"

    @property
    def description(self) -> str:
        return "Richer worldbuilding with multiple landmarks and attributes."

    @property
    def deck_type(self) -> str:
        return "deck_of_worlds"

    def get_card_draws(self) -> dict[str, int]:
        return {
            "regions": 4,
            "landmarks": 4,
            "namesakes": 4,
            "origins": 4,
            "attributes": 4,
            "advents": 4,
        }

    def get_selection_order(self) -> list[str]:
        return [
            "regions",
            "landmarks", "landmarks_2",
            "namesakes", "namesakes_2",
            "origins",
            "attributes", "attributes_2",
            "advents",
        ]

    def build_prompt(self, selected_cards: dict[str, str]) -> str:
        region = selected_cards.get("regions", "???")
        landmark1 = selected_cards.get("landmarks", "???")
        landmark2 = selected_cards.get("landmarks_2", "???")
        namesake1 = selected_cards.get("namesakes", "???")
        namesake2 = selected_cards.get("namesakes_2", "???")
        origin = selected_cards.get("origins", "???")
        attribute1 = selected_cards.get("attributes", "???")
        attribute2 = selected_cards.get("attributes_2", "???")
        advent = selected_cards.get("advents", "???")

        return (
            f"{namesake1} {region} {namesake2} with {landmark1} and {landmark2} | "
            f"Origin: {origin} | Now: {attribute1}, {attribute2} | Hook: {advent}"
        )

    def get_context_for_debate(self, selected_so_far: dict[str, str],
                                next_card_type: str) -> str:
        """Custom context explaining the complex microsetting structure."""
        lines = ["Building a COMPLEX MICROSETTING (Deck of Worlds)"]
        lines.append("This includes multiple landmarks, namesakes, and attributes.\n")

        if selected_so_far:
            lines.append("Selected so far:")
            for card_type, card in selected_so_far.items():
                label = self._get_label(card_type)
                lines.append(f"  {label}: {card}")

        label = self._get_label(next_card_type)
        lines.append(f"\nNow selecting: {label}")

        return "\n".join(lines)

    def _get_label(self, card_type: str) -> str:
        """Get human-readable label for card type."""
        labels = {
            "regions": "REGION (main terrain)",
            "landmarks": "LANDMARK #1",
            "landmarks_2": "LANDMARK #2",
            "namesakes": "NAMESAKE #1",
            "namesakes_2": "NAMESAKE #2",
            "origins": "ORIGIN (past event)",
            "attributes": "ATTRIBUTE #1",
            "attributes_2": "ATTRIBUTE #2",
            "advents": "ADVENT (future hook)",
        }
        return labels.get(card_type, card_type.upper())
