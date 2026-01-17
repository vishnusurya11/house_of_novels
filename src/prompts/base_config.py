"""
Base class for prompt configurations.

Each prompt type (Story Seed, Character Concept, etc.) extends this
to define its card requirements and output format.
"""

from abc import ABC, abstractmethod


class PromptConfig(ABC):
    """
    Abstract base class for prompt configurations.

    Extend this class to create new prompt types. Each prompt config defines:
    1. Which card types to draw and how many
    2. The order of card selection debates
    3. How to format the final prompt output
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Display name for this prompt type."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Brief description of what this prompt type produces."""
        pass

    @property
    def deck_type(self) -> str:
        """Which deck to use: 'story_engine' or 'deck_of_worlds'."""
        return "story_engine"

    @abstractmethod
    def get_card_draws(self) -> dict[str, int]:
        """
        Define which card types to draw and how many options per type.

        Returns:
            Dict mapping card_type to number of cards to draw.
            Example: {"agents": 4, "engines": 4, "anchors": 4}
        """
        pass

    @abstractmethod
    def get_selection_order(self) -> list[str]:
        """
        Define the order in which card types are debated/selected.

        This determines the sequence of debates. Earlier selections
        inform the context for later debates.

        Returns:
            List of card types in debate order.
            Example: ["agents", "engines", "anchors", "conflicts", "aspects"]
        """
        pass

    @abstractmethod
    def build_prompt(self, selected_cards: dict[str, str]) -> str:
        """
        Build the final formatted prompt from selected cards.

        Args:
            selected_cards: Dict mapping card_type to selected card value.
                           Example: {"agents": "A DETECTIVE", "engines": "WANTS TO SOLVE"}

        Returns:
            Formatted prompt string ready for display/use.
        """
        pass

    def get_context_for_debate(self, selected_so_far: dict[str, str],
                                next_card_type: str) -> str:
        """
        Generate context string for the next debate round.

        Override this for custom context generation.

        Args:
            selected_so_far: Cards already selected in previous debates
            next_card_type: The card type about to be debated

        Returns:
            Context string to inform agents about current state
        """
        if not selected_so_far:
            return f"Starting fresh. First selection: {next_card_type}"

        lines = ["Currently selected:"]
        for card_type, card in selected_so_far.items():
            lines.append(f"  {card_type.upper()}: {card}")
        lines.append(f"\nNow selecting: {next_card_type}")

        return "\n".join(lines)
