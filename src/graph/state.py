"""
LangGraph state definitions for the debate workflow.
"""

from typing import TypedDict, Annotated
from operator import add


class DebateState(TypedDict):
    """
    State passed through the debate workflow.

    Attributes:
        deck: The full card deck data
        prompt_config_name: Name of the prompt config being used
        card_draws: Dict of card_type -> list of drawn cards
        selected_cards: Dict of card_type -> selected card
        current_card_type: Card type currently being debated
        card_selections: List of structured selection data for each card type
        final_prompt: The generated prompt after all debates
    """
    deck: dict
    prompt_config_name: str
    card_draws: dict  # {card_type: [card1, card2, card3, card4]}
    selected_cards: dict  # {card_type: selected_card}
    current_card_type: str
    card_selections: Annotated[list, add]  # Accumulates structured selection data
    final_prompt: str
