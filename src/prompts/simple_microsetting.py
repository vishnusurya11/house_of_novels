"""
Simple Microsetting prompt configuration for Deck of Worlds.

Basic worldbuilding unit with 6 card types.
"""

from .base_config import PromptConfig


class SimpleMicrosettingConfig(PromptConfig):
    """
    Simple Microsetting: Basic Deck of Worlds worldbuilding unit.

    Uses the standard 6-step recipe:
    - Region = main terrain/environment (hub)
    - Landmark = point of interest
    - Namesake = in-world nickname
    - Origin = significant past event
    - Attribute = present-day feature
    - Advent = future hook/event
    """

    @property
    def name(self) -> str:
        return "Simple Microsetting"

    @property
    def description(self) -> str:
        return "Basic worldbuilding unit with 6 card types from Deck of Worlds."

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
        return ["regions", "landmarks", "namesakes", "origins", "attributes", "advents"]

    def build_prompt(self, selected_cards: dict[str, str]) -> str:
        region = selected_cards.get("regions", "???")
        landmark = selected_cards.get("landmarks", "???")
        namesake = selected_cards.get("namesakes", "???")
        origin = selected_cards.get("origins", "???")
        attribute = selected_cards.get("attributes", "???")
        advent = selected_cards.get("advents", "???")

        return f"{namesake} {region} with {landmark} | Origin: {origin} | Now: {attribute} | Hook: {advent}"

    def get_context_for_debate(self, selected_so_far: dict[str, str],
                                next_card_type: str) -> str:
        """Custom context explaining the microsetting structure."""
        lines = ["Building a SIMPLE MICROSETTING (Deck of Worlds)"]

        if selected_so_far:
            lines.append("\nSelected so far:")
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
            "landmarks": "LANDMARK (point of interest)",
            "namesakes": "NAMESAKE (in-world nickname)",
            "origins": "ORIGIN (past event)",
            "attributes": "ATTRIBUTE (present feature)",
            "advents": "ADVENT (future hook)",
        }
        return labels.get(card_type, card_type.upper())
