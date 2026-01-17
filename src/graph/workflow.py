"""
LangGraph workflow for orchestrating multi-agent debates.
"""

import json
import random
import os
import time
import hashlib
from pathlib import Path

from langgraph.graph import StateGraph, END

from src.graph.state import DebateState
from src.agents import Supervisor
from src.prompts import PROMPT_CONFIGS
from src.config import CARDS_PER_DRAW, DEFAULT_MODEL


def seed_random():
    """Seed random from multiple entropy sources for better distribution."""
    entropy_sources = [
        str(time.time_ns()),
        str(os.getpid()),
        os.urandom(16).hex(),
        str(id(object())),
    ]
    combined = "".join(entropy_sources)
    seed_value = int(hashlib.sha256(combined.encode()).hexdigest()[:16], 16)
    random.seed(seed_value)


def load_deck(deck_type: str = "story_engine") -> dict:
    """Load a card deck from JSON file.

    Args:
        deck_type: Either 'story_engine' or 'deck_of_worlds'

    Returns:
        Dict with card types as keys and lists of cards as values
    """
    files_dir = Path(__file__).parent.parent.parent / "files"

    if deck_type == "deck_of_worlds":
        deck_path = files_dir / "deck_of_worlds.json"
    else:
        deck_path = files_dir / "story_engine_main_deck.json"

    with open(deck_path, "r", encoding="utf-8") as f:
        return json.load(f)


def draw_cards(deck: dict, card_type: str, count: int = CARDS_PER_DRAW) -> list[str]:
    """Draw random cards of a specific type."""
    # Handle card types with suffixes (e.g., "agents_2" -> "agents")
    base_type = card_type.split("_")[0]
    cards = deck.get(base_type, [])
    return random.sample(cards, min(count, len(cards)))


def initialize_state(state: DebateState) -> DebateState:
    """Initialize state with deck and card draws."""
    seed_random()  # Better entropy before drawing cards

    config_class = PROMPT_CONFIGS.get(state["prompt_config_name"])

    if not config_class:
        raise ValueError(f"Unknown prompt config: {state['prompt_config_name']}")

    config = config_class()
    deck = load_deck(config.deck_type)
    card_requirements = config.get_card_draws()
    selection_order = config.get_selection_order()

    # Draw cards for each type needed
    card_draws = {}
    for card_type in selection_order:
        base_type = card_type.split("_")[0]
        count = card_requirements.get(base_type, CARDS_PER_DRAW)
        card_draws[card_type] = draw_cards(deck, card_type, count)

    return {
        **state,
        "deck": deck,
        "card_draws": card_draws,
        "selected_cards": {},
        "current_card_type": selection_order[0],
        "card_selections": [],
        "final_prompt": "",
    }


def run_debate(state: DebateState) -> DebateState:
    """Run a debate for the current card type."""
    config_class = PROMPT_CONFIGS.get(state["prompt_config_name"])
    config = config_class()

    supervisor = Supervisor(model=DEFAULT_MODEL)

    card_type = state["current_card_type"]
    cards = state["card_draws"][card_type]
    context = config.get_context_for_debate(state["selected_cards"], card_type)

    selected_card, selection_data = supervisor.run_debate(
        context=context,
        cards=cards,
        card_type=card_type,
    )

    # Update selected cards
    new_selected = {**state["selected_cards"], card_type: selected_card}

    return {
        **state,
        "selected_cards": new_selected,
        "card_selections": [selection_data],
    }


def advance_to_next_card(state: DebateState) -> DebateState:
    """Move to the next card type in selection order."""
    config_class = PROMPT_CONFIGS.get(state["prompt_config_name"])
    config = config_class()
    selection_order = config.get_selection_order()

    current_idx = selection_order.index(state["current_card_type"])
    next_idx = current_idx + 1

    if next_idx < len(selection_order):
        return {**state, "current_card_type": selection_order[next_idx]}
    else:
        return {**state, "current_card_type": None}


def build_final_prompt(state: DebateState) -> DebateState:
    """Build the final prompt from selected cards."""
    config_class = PROMPT_CONFIGS.get(state["prompt_config_name"])
    config = config_class()

    final_prompt = config.build_prompt(state["selected_cards"])

    return {**state, "final_prompt": final_prompt}


def should_continue(state: DebateState) -> str:
    """Determine if more debates are needed."""
    if state["current_card_type"] is None:
        return "finalize"
    return "debate"


def create_debate_workflow() -> StateGraph:
    """Create the LangGraph workflow for prompt generation."""
    workflow = StateGraph(DebateState)

    # Add nodes
    workflow.add_node("initialize", initialize_state)
    workflow.add_node("debate", run_debate)
    workflow.add_node("advance", advance_to_next_card)
    workflow.add_node("finalize", build_final_prompt)

    # Set entry point
    workflow.set_entry_point("initialize")

    # Add edges
    workflow.add_edge("initialize", "debate")
    workflow.add_edge("debate", "advance")
    workflow.add_conditional_edges(
        "advance",
        should_continue,
        {
            "debate": "debate",
            "finalize": "finalize",
        }
    )
    workflow.add_edge("finalize", END)

    return workflow.compile()


def run_prompt_generation(prompt_config_name: str) -> tuple[str, list[dict]]:
    """
    Run the full prompt generation workflow.

    Args:
        prompt_config_name: Name of the prompt config (e.g., "story_seed")

    Returns:
        Tuple of (final_prompt, card_selections_metadata)
    """
    workflow = create_debate_workflow()

    initial_state = {
        "prompt_config_name": prompt_config_name,
        "deck": {},
        "card_draws": {},
        "selected_cards": {},
        "current_card_type": "",
        "card_selections": [],
        "final_prompt": "",
    }

    result = workflow.invoke(initial_state)

    return result["final_prompt"], result["card_selections"]
