"""
Character Concept prompt configuration.

Deeper character with motivation choices and arc potential.
"""

from .base_config import PromptConfig


class CharacterConceptConfig(PromptConfig):
    """
    Simple Prompt #2: Character Concept (deeper character + arc start)

    Focuses on a single character with richer development:
    - Agent = the character
    - Aspects (2) = character descriptors
    - Engines (debated) = their motivation
    - Anchor or Agent = object of desire
    - Conflict = obstacle/cost
    """

    @property
    def name(self) -> str:
        return "Character Concept"

    @property
    def description(self) -> str:
        return "Deep dive into a single character with motivation and desire."

    def get_card_draws(self) -> dict[str, int]:
        return {
            "agents": 4,      # Main character
            "aspects": 4,     # Character flavor (will draw twice)
            "engines": 4,     # Motivation options
            "anchors": 4,     # Object of desire
            "conflicts": 4,   # Obstacle
        }

    def get_selection_order(self) -> list[str]:
        # Character first, then aspects, motivation, desire, obstacle
        return ["agents", "aspects", "aspects_2", "engines", "anchors", "conflicts"]

    def build_prompt(self, selected_cards: dict[str, str]) -> str:
        agent = selected_cards.get("agents", "???")
        aspect1 = selected_cards.get("aspects", "???")
        aspect2 = selected_cards.get("aspects_2", "???")
        engine = selected_cards.get("engines", "???")
        anchor = selected_cards.get("anchors", "???")
        conflict = selected_cards.get("conflicts", "???")

        return f"{aspect1} {agent} {engine} {aspect2} {anchor} {conflict}"

    def get_context_for_debate(self, selected_so_far: dict[str, str],
                                next_card_type: str) -> str:
        """Custom context that explains the character focus."""
        if not selected_so_far:
            return "Building a CHARACTER CONCEPT - starting with the main character."

        lines = ["Building a CHARACTER CONCEPT"]
        lines.append("Selected so far:")

        for card_type, card in selected_so_far.items():
            label = card_type.upper()
            if card_type == "aspects":
                label = "ASPECT (character)"
            elif card_type == "aspects_2":
                label = "ASPECT (desire)"
            lines.append(f"  {label}: {card}")

        if next_card_type == "aspects_2":
            lines.append("\nNow selecting: Second ASPECT (to describe the desire)")
        else:
            lines.append(f"\nNow selecting: {next_card_type}")

        return "\n".join(lines)
