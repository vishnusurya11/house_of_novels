#!/usr/bin/env python3
"""
Codex Generator - Combined Story Engine + Deck of Worlds

Generates both story prompts and worldbuilding microsettings in a single run,
outputting everything to one combined JSON file.

Usage:
    # Set your OpenRouter API key
    export OPENROUTER_API_KEY="your-key-here"

    # Run the generator
    uv run python src/codex_generator.py
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add parent directory to path for proper package imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.graph import run_prompt_generation
from src.prompts import PROMPT_CONFIGS
from src.config import DEFAULT_MODEL, DEBATE_ROUNDS, CARDS_PER_DRAW


# Which configs to run for each deck type
STORY_ENGINE_CONFIGS = ["story_seed"]
DECK_OF_WORLDS_CONFIGS = ["simple_microsetting"]


def get_output_dir() -> Path:
    """Get or create output directory."""
    output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(exist_ok=True)
    return output_dir


def generate_for_configs(config_names: list[str]) -> tuple[list[dict], list[dict]]:
    """
    Generate prompts for a list of config names.

    Returns:
        Tuple of (prompts_list, metadata_list)
    """
    prompts = []
    metadata = []

    for config_name in config_names:
        config_class = PROMPT_CONFIGS.get(config_name)
        if not config_class:
            print(f"    WARNING: Unknown config '{config_name}', skipping")
            continue

        config = config_class()
        print(f"\n>>> Generating: {config.name}")
        print(f"    {config.description}")
        print("    Running debates...\n")

        try:
            final_prompt, card_selections = run_prompt_generation(config_name)

            prompts.append({
                "type": config.name,
                "prompt": final_prompt.strip(),
            })

            metadata.append({
                "type": config.name,
                "description": config.description,
                "card_selections": card_selections,
                "final_prompt": final_prompt.strip(),
                "status": "success",
            })

            print(f"\n>>> RESULT: {config.name}")
            print(final_prompt)

        except Exception as e:
            error_msg = str(e)
            print(f"    ERROR: {e}")

            metadata.append({
                "type": config.name,
                "description": config.description,
                "error": error_msg,
                "status": "error",
            })

    return prompts, metadata


def save_output(story_engine: dict, deck_of_worlds: dict) -> Path:
    """
    Save combined output to JSON file with timestamp.
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    output_dir = get_output_dir()
    output_path = output_dir / f"codex_{timestamp}.json"

    output_data = {
        "generated_at": datetime.now().isoformat(),
        "config": {
            "model": DEFAULT_MODEL,
            "debate_rounds": DEBATE_ROUNDS,
            "cards_per_draw": CARDS_PER_DRAW,
        },
        "story_engine": story_engine,
        "deck_of_worlds": deck_of_worlds,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    return output_path


def main():
    """Run combined generation for Story Engine and Deck of Worlds."""
    print("\n" + "#" * 60)
    print("# CODEX GENERATOR")
    print("# Story Engine + Deck of Worlds Combined")
    print("#" * 60)

    # Generate Story Engine prompts
    print("\n" + "=" * 40)
    print("STORY ENGINE")
    print("=" * 40)
    se_prompts, se_metadata = generate_for_configs(STORY_ENGINE_CONFIGS)

    # Generate Deck of Worlds microsettings
    print("\n" + "=" * 40)
    print("DECK OF WORLDS")
    print("=" * 40)
    dow_prompts, dow_metadata = generate_for_configs(DECK_OF_WORLDS_CONFIGS)

    # Save combined output
    output_path = save_output(
        story_engine={"prompts": se_prompts, "metadata": se_metadata},
        deck_of_worlds={"prompts": dow_prompts, "metadata": dow_metadata},
    )

    print("\n" + "#" * 60)
    print(f"# Saved to: {output_path}")
    print("#" * 60)


if __name__ == "__main__":
    main()
