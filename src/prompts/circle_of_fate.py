"""
Circle of Fate prompt configuration.

Complex prompt with two characters in mutual push-pull relationship.
"""

from .base_config import PromptConfig


class CircleOfFateConfig(PromptConfig):
    """
    Complex Prompt #1: Circle of Fate (two-way relationship loop)

    Two characters locked in mutual push-pull:
    - Agent #1 + Engine + Conflict → Agent #2
    - Agent #2 + Engine + Conflict → Agent #1

    Result: "A wants X from B / B wants Y from A" loop
    """

    @property
    def name(self) -> str:
        return "Circle of Fate"

    @property
    def description(self) -> str:
        return "Two characters locked in mutual push-pull relationship."

    def get_card_draws(self) -> dict[str, int]:
        return {
            "agents": 4,      # Will draw twice for two characters
            "engines": 4,     # Will draw twice for each relationship
            "conflicts": 4,   # Will draw twice for each relationship
            "aspects": 4,     # Will draw twice for character descriptors
        }

    def get_selection_order(self) -> list[str]:
        return [
            "agents",       # First character
            "aspects",      # First character's descriptor
            "agents_2",     # Second character
            "aspects_2",    # Second character's descriptor
            "engines",      # What Agent 1 wants from Agent 2
            "conflicts",    # Agent 1's obstacle
            "engines_2",    # What Agent 2 wants from Agent 1
            "conflicts_2",  # Agent 2's obstacle
        ]

    def build_prompt(self, selected_cards: dict[str, str]) -> str:
        agent1 = selected_cards.get("agents", "???")
        aspect1 = selected_cards.get("aspects", "???")
        agent2 = selected_cards.get("agents_2", "???")
        aspect2 = selected_cards.get("aspects_2", "???")
        engine1 = selected_cards.get("engines", "???")
        conflict1 = selected_cards.get("conflicts", "???")
        engine2 = selected_cards.get("engines_2", "???")
        conflict2 = selected_cards.get("conflicts_2", "???")

        return f"{aspect1} {agent1} {engine1} {aspect2} {agent2} {conflict1} | {aspect2} {agent2} {engine2} {aspect1} {agent1} {conflict2}"

    def get_context_for_debate(self, selected_so_far: dict[str, str],
                                next_card_type: str) -> str:
        """Custom context explaining the circular relationship."""
        lines = ["Building a CIRCLE OF FATE - two characters in mutual push-pull"]

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
            "agents": "CHARACTER #1",
            "aspects": "CHARACTER #1 descriptor",
            "agents_2": "CHARACTER #2",
            "aspects_2": "CHARACTER #2 descriptor",
            "engines": "What #1 wants from #2",
            "conflicts": "Obstacle for #1",
            "engines_2": "What #2 wants from #1",
            "conflicts_2": "Obstacle for #2",
        }
        return labels.get(card_type, card_type.upper())
