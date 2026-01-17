#!/usr/bin/env python3
"""
Deck of Worlds Generator

Generates microsettings and world maps by randomly drawing cards from the
Deck of Worlds, replicating the physical card game experience digitally.

Card Types:
- Regions: Main terrain/environment (the hub)
- Landmarks: Points of interest / geographic sites
- Namesakes: In-world nicknames/titles
- Origins: Significant events from the past
- Attributes: Present-day features of the area/people
- Advents: Future-changing events + story hooks
"""

import json
import random
import io
import sys
from pathlib import Path

# Output buffer to capture all prints
output_buffer = io.StringIO()


def load_deck():
    """Load the Deck of Worlds from JSON file."""
    deck_path = Path(__file__).parent.parent / "files" / "deck_of_worlds.json"
    with open(deck_path, "r", encoding="utf-8") as f:
        return json.load(f)


def draw(deck, card_type, count=1):
    """Draw random cards of a specific type."""
    cards = deck[card_type]
    if count == 1:
        return random.choice(cards)
    return random.sample(cards, min(count, len(cards)))


# =============================================================================
# MICROSETTINGS
# =============================================================================

def generate_simple_microsetting(deck):
    """
    Simple Microsetting (the standard recipe)

    A 6-card cluster around a Region:
    - Region = underlying environment type
    - Landmark = point of interest
    - Namesake = in-world nickname
    - Origin = lore-based backstory (past)
    - Attribute = present-day detail
    - Advent = future event / story hook
    """
    region = draw(deck, "regions")
    landmark = draw(deck, "landmarks")
    namesake = draw(deck, "namesakes")
    origin = draw(deck, "origins")
    attribute = draw(deck, "attributes")
    advent = draw(deck, "advents")

    print("\n" + "=" * 60)
    print("SIMPLE MICROSETTING")
    print("=" * 60)
    print(f"\n[REGION] {region}")
    print(f"\n  LANDMARK: {landmark}")
    print(f"  NAMESAKE: \"{namesake}\"")
    print(f"\n  ORIGIN (past): {origin}")
    print(f"  ATTRIBUTE (present): {attribute}")
    print(f"  ADVENT (future): {advent}")
    print()


def generate_complex_microsetting(deck):
    """
    Complex Microsetting (more choice + richer lore)

    Uses more cards with choices:
    - 1 Region
    - 2 Landmarks (choose one or use both)
    - 2 Namesakes (choose one or use both)
    - 1 Origin
    - 2 Attributes (choose one or use both)
    - 1 Advent
    """
    region = draw(deck, "regions")
    landmarks = draw(deck, "landmarks", 2)
    namesakes = draw(deck, "namesakes", 2)
    origin = draw(deck, "origins")
    attributes = draw(deck, "attributes", 2)
    advent = draw(deck, "advents")

    print("\n" + "=" * 60)
    print("COMPLEX MICROSETTING")
    print("=" * 60)
    print(f"\n[REGION] {region}")
    print(f"\n  LANDMARKS (choose one or both):")
    print(f"    1. {landmarks[0]}")
    print(f"    2. {landmarks[1]}")
    print(f"\n  NAMESAKES (choose one or both):")
    print(f"    1. \"{namesakes[0]}\"")
    print(f"    2. \"{namesakes[1]}\"")
    print(f"\n  ORIGIN (past): {origin}")
    print(f"\n  ATTRIBUTES (choose one or both):")
    print(f"    1. {attributes[0]}")
    print(f"    2. {attributes[1]}")
    print(f"\n  ADVENT (future): {advent}")
    print()


def generate_world_meta(deck):
    """
    World Meta (global rules for entire world)

    A meta is a worldbuilding concept that applies globally.
    Keep no more than 1 of each type in the meta row:
    - 1 Namesake
    - 1 Origin
    - 1 Attribute
    - 1 Advent
    """
    namesake = draw(deck, "namesakes")
    origin = draw(deck, "origins")
    attribute = draw(deck, "attributes")
    advent = draw(deck, "advents")

    print("\n" + "=" * 60)
    print("WORLD META (Global Rules)")
    print("=" * 60)
    print("\nThese apply to the ENTIRE world, not just one location:")
    print(f"\n  NAMESAKE: All places share the theme \"{namesake}\"")
    print(f"  ORIGIN: The world's shared past - {origin}")
    print(f"  ATTRIBUTE: Universal trait - {attribute}")
    print(f"  ADVENT: World-changing event - {advent}")
    print()


def generate_world_map(deck, num_microsettings=3):
    """
    World Map (multiple microsettings)

    Creates multiple microsettings that form a connected world.
    Mix of simple and complex for varied density.
    """
    print("\n" + "=" * 60)
    print(f"WORLD MAP ({num_microsettings} Microsettings)")
    print("=" * 60)

    # First generate the world meta
    namesake = draw(deck, "namesakes")
    origin = draw(deck, "origins")
    attribute = draw(deck, "attributes")
    advent = draw(deck, "advents")

    print("\n--- WORLD META ---")
    print(f"  Theme: \"{namesake}\"")
    print(f"  Shared Past: {origin}")
    print(f"  Universal Trait: {attribute}")
    print(f"  Looming Event: {advent}")

    # Generate microsettings
    for i in range(num_microsettings):
        print(f"\n--- MICROSETTING {i + 1} ---")
        region = draw(deck, "regions")
        landmark = draw(deck, "landmarks")
        local_namesake = draw(deck, "namesakes")
        local_origin = draw(deck, "origins")
        local_attribute = draw(deck, "attributes")
        local_advent = draw(deck, "advents")

        print(f"  Region: {region}")
        print(f"  Landmark: {landmark}")
        print(f"  Local Name: \"{local_namesake}\"")
        print(f"  Local History: {local_origin}")
        print(f"  Known For: {local_attribute}")
        print(f"  Current Event: {local_advent}")
    print()


# =============================================================================
# MAIN
# =============================================================================

def save_output(content):
    """Save generated worlds to file (overwrites each time)."""
    output_path = Path(__file__).parent.parent / "generated_worlds.txt"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    return output_path


def main():
    """Generate all microsetting types and save to file."""
    deck = load_deck()

    # Capture all output
    old_stdout = sys.stdout
    sys.stdout = output_buffer

    print("\n" + "#" * 60)
    print("# DECK OF WORLDS GENERATOR")
    print("#" * 60)

    print("\n--- SINGLE MICROSETTINGS ---")
    generate_simple_microsetting(deck)
    generate_complex_microsetting(deck)

    print("\n--- WORLD BUILDING ---")
    generate_world_meta(deck)
    generate_world_map(deck, num_microsettings=3)

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
