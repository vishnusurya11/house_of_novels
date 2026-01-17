#!/usr/bin/env python3
"""
Story Engine Prompt Generator

Generates story prompts by randomly drawing cards from the Story Engine deck,
replicating the physical card game experience digitally.

Card Types:
- Agents: Characters who make choices
- Engines: Motivations and relationships
- Anchors: Objects, locations, or events
- Conflicts: Obstacles, consequences, or dilemmas
- Aspects: Adjectives that describe other cards
"""

import json
import random
import io
import sys
from pathlib import Path

# Output buffer to capture all prints
output_buffer = io.StringIO()


def load_deck():
    """Load the Story Engine deck from JSON file."""
    deck_path = Path(__file__).parent.parent / "files" / "story_engine_main_deck.json"
    with open(deck_path, "r", encoding="utf-8") as f:
        return json.load(f)


def draw(deck, card_type, count=1):
    """Draw random cards of a specific type."""
    cards = deck[card_type]
    if count == 1:
        return random.choice(cards)
    return random.sample(cards, min(count, len(cards)))


# =============================================================================
# SIMPLE PROMPTS
# =============================================================================

def generate_story_seed(deck):
    """
    Simple Prompt #1: Story Seed (baseline)

    The core "one of each type" build:
    - Agent = main character
    - Engine = their motivation/drive
    - Anchor = what they want
    - Conflict = obstacle/consequence
    - Aspect = adds detail
    """
    agent = draw(deck, "agents")
    engine = draw(deck, "engines")
    anchor = draw(deck, "anchors")
    conflict = draw(deck, "conflicts")
    aspect = draw(deck, "aspects")

    print("\n" + "=" * 50)
    print("STORY SEED")
    print("=" * 50)
    print(f"\n{aspect} {agent}")
    print(f"{engine}")
    print(f"{anchor}")
    print(f"{conflict}")
    print()


def generate_character_concept(deck):
    """
    Simple Prompt #2: Character Concept (deeper character + arc start)

    - Agent = the character
    - Engine (choose from 2) = their motivation
    - Anchor or Agent = object of desire
    - Conflict = obstacle/cost
    - Aspects = flavor/details
    """
    agent = draw(deck, "agents")
    engines = draw(deck, "engines", 2)

    # Desire can be an Anchor or another Agent
    desire = random.choice([draw(deck, "anchors"), draw(deck, "agents")])

    conflict = draw(deck, "conflicts")
    aspects = draw(deck, "aspects", 2)

    print("\n" + "=" * 50)
    print("CHARACTER CONCEPT")
    print("=" * 50)
    print(f"\nCHARACTER: {aspects[0]} {agent}")
    print(f"\nMOTIVATION (choose one):")
    print(f"  Option A: {engines[0]}")
    print(f"  Option B: {engines[1]}")
    print(f"\nDESIRE: {aspects[1]} {desire}")
    print(f"\nOBSTACLE: {conflict}")
    print()


def generate_item_setting(deck):
    """
    Simple Prompt #3: Item/Setting-Driven Story

    Makes an object + its setting the "heart" of the story.
    - 2 Anchors: object + setting
    - Engine = effect the object will have
    - Anchor or Agent = something affected
    - Agent = owner/connected character (optional)
    - Conflict = obstacle/cost (optional)
    """
    object_anchor = draw(deck, "anchors")
    setting_anchor = draw(deck, "anchors")

    engines = draw(deck, "engines", 3)

    # Something affected by the setting
    affected = random.choice([draw(deck, "anchors"), draw(deck, "agents")])

    owner = draw(deck, "agents")
    conflict = draw(deck, "conflicts")
    aspects = draw(deck, "aspects", 3)

    print("\n" + "=" * 50)
    print("ITEM/SETTING-DRIVEN STORY")
    print("=" * 50)
    print(f"\nTHE OBJECT: {aspects[0]} {object_anchor}")
    print(f"THE SETTING: {aspects[1]} {setting_anchor}")
    print(f"\nEFFECT (choose one):")
    print(f"  Option A: {engines[0]}")
    print(f"  Option B: {engines[1]}")
    print(f"  Option C: {engines[2]}")
    print(f"\nAFFECTED: {aspects[2]} {affected}")
    print(f"OWNER/CONNECTION: {owner}")
    print(f"\nCONFLICT: {conflict}")
    print()


# =============================================================================
# COMPLEX PROMPTS
# =============================================================================

def generate_circle_of_fate(deck):
    """
    Complex Prompt #1: Circle of Fate (two-way relationship loop)

    Two characters locked in mutual push-pull.
    - Agent #1 + Engine+Conflict → Agent #2
    - Agent #2 + Engine+Conflict → Agent #1

    Result: "A wants X from B / B wants Y from A" loop
    """
    agent1 = draw(deck, "agents")
    agent2 = draw(deck, "agents")

    engine1 = draw(deck, "engines")
    conflict1 = draw(deck, "conflicts")

    engine2 = draw(deck, "engines")
    conflict2 = draw(deck, "conflicts")

    aspects = draw(deck, "aspects", 2)

    print("\n" + "=" * 50)
    print("CIRCLE OF FATE")
    print("=" * 50)
    print(f"\n{aspects[0]} {agent1}")
    print(f"  |")
    print(f"  | {engine1}")
    print(f"  | {conflict1}")
    print(f"  v")
    print(f"{aspects[1]} {agent2}")
    print(f"  |")
    print(f"  | {engine2}")
    print(f"  | {conflict2}")
    print(f"  v")
    print(f"(back to {agent1})")
    print()


def generate_clash_of_wills(deck):
    """
    Complex Prompt #2: Clash of Wills (two characters want the same thing)

    Usually rivals with different reasons.
    - Agent #1 → Engine+Conflict → shared target
    - Agent #2 → Engine+Conflict → same target (opposite direction)
    """
    agent1 = draw(deck, "agents")
    agent2 = draw(deck, "agents")

    # Shared target can be Agent or Anchor
    target = random.choice([draw(deck, "anchors"), draw(deck, "agents")])

    engine1 = draw(deck, "engines")
    conflict1 = draw(deck, "conflicts")

    engine2 = draw(deck, "engines")
    conflict2 = draw(deck, "conflicts")

    aspects = draw(deck, "aspects", 3)

    print("\n" + "=" * 50)
    print("CLASH OF WILLS")
    print("=" * 50)
    print(f"\n{aspects[0]} {agent1}")
    print(f"  | {engine1}")
    print(f"  | {conflict1}")
    print(f"  v")
    print(f"     [{aspects[2]} {target}]")
    print(f"  ^")
    print(f"  | {engine2}")
    print(f"  | {conflict2}")
    print(f"{aspects[1]} {agent2}")
    print()


def generate_soul_divided(deck):
    """
    Complex Prompt #3: Soul Divided (one character must choose between two things)

    A character pulled between two desires.
    - Desire #1 ← Engine+Conflict ← Character → Engine+Conflict → Desire #2
    """
    character = draw(deck, "agents")

    # Two desires (can be Agents or Anchors)
    desire1 = random.choice([draw(deck, "anchors"), draw(deck, "agents")])
    desire2 = random.choice([draw(deck, "anchors"), draw(deck, "agents")])

    engine1 = draw(deck, "engines")
    conflict1 = draw(deck, "conflicts")

    engine2 = draw(deck, "engines")
    conflict2 = draw(deck, "conflicts")

    aspects = draw(deck, "aspects", 3)

    print("\n" + "=" * 50)
    print("SOUL DIVIDED")
    print("=" * 50)
    print(f"\n{aspects[1]} {desire1}")
    print(f"  ^")
    print(f"  | {engine1}")
    print(f"  | {conflict1}")
    print(f"  |")
    print(f"[{aspects[0]} {character}]")
    print(f"  |")
    print(f"  | {engine2}")
    print(f"  | {conflict2}")
    print(f"  v")
    print(f"{aspects[2]} {desire2}")
    print()


# =============================================================================
# MAIN
# =============================================================================

def save_output(content):
    """Save generated prompts to file (overwrites each time)."""
    output_path = Path(__file__).parent.parent / "generated_prompts.txt"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    return output_path


def main():
    """Generate all prompt types and save to file."""
    deck = load_deck()

    # Capture all output
    old_stdout = sys.stdout
    sys.stdout = output_buffer

    print("\n" + "#" * 50)
    print("# STORY ENGINE PROMPT GENERATOR")
    print("#" * 50)

    print("\n--- SIMPLE PROMPTS ---")
    generate_story_seed(deck)
    generate_character_concept(deck)
    generate_item_setting(deck)

    print("\n--- COMPLEX PROMPTS ---")
    generate_circle_of_fate(deck)
    generate_clash_of_wills(deck)
    generate_soul_divided(deck)

    # Get captured output
    output = output_buffer.getvalue()

    # Restore stdout
    sys.stdout = old_stdout

    # Print to console
    print(output)

    # Save to file (overwrites)
    output_path = save_output(output)
    print(f"\n[Saved to: {output_path}]")


if __name__ == "__main__":
    main()
