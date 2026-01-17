#!/usr/bin/env python3
"""
Multi-Agent Deck of Worlds Microsetting Generator

Uses a team of 4 AI agents to debate and select cards for worldbuilding,
replicating the collaborative discussion experience of the physical card game.

Agent Roles:
- PLACER: Advocates for dramatic/bold choices
- ROTATOR: Advocates for subtle/nuanced choices
- CRITIC: Challenges weak combinations
- SYNTHESIZER: Finds connections between cards

Usage:
    # Set your OpenRouter API key
    export OPENROUTER_API_KEY="your-key-here"

    # Run the generator
    uv run python src/deck_of_worlds_agents.py
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


# Deck of Worlds specific configs
DECK_OF_WORLDS_CONFIGS = {
    "simple_microsetting": PROMPT_CONFIGS["simple_microsetting"],
    "complex_microsetting": PROMPT_CONFIGS["complex_microsetting"],
}


def get_output_dir() -> Path:
    """Get or create output directory."""
    output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(exist_ok=True)
    return output_dir


def save_output(prompts: list[dict], metadata: list[dict]) -> Path:
    """
    Save generated microsettings to JSON file with timestamp.

    Output structure:
    {
        "prompts": [...],      # Final prompts only
        "metadata": [...]      # Full debate logs and details
    }
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    output_dir = get_output_dir()
    output_path = output_dir / f"microsettings_{timestamp}.json"

    output_data = {
        "generated_at": datetime.now().isoformat(),
        "deck": "deck_of_worlds",
        "config": {
            "model": DEFAULT_MODEL,
            "debate_rounds": DEBATE_ROUNDS,
            "cards_per_draw": CARDS_PER_DRAW,
        },
        "prompts": prompts,
        "metadata": metadata,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    return output_path


def main():
    """Run multi-agent microsetting generation for Deck of Worlds."""
    print("\n" + "#" * 60)
    print("# MULTI-AGENT DECK OF WORLDS")
    print("# 4 AI agents debate to select the best cards")
    print("#" * 60)

    prompts = []
    metadata = []

    # Generate each microsetting type
    for config_name, config_class in DECK_OF_WORLDS_CONFIGS.items():
        config = config_class()
        print(f"\n>>> Generating: {config.name}")
        print(f"    {config.description}")
        print("    Running debates...\n")

        try:
            final_prompt, card_selections = run_prompt_generation(config_name)

            # Store final prompt (clean)
            prompts.append({
                "type": config.name,
                "prompt": final_prompt.strip(),
            })

            # Store full metadata with structured selection data
            metadata.append({
                "type": config.name,
                "description": config.description,
                "card_selections": card_selections,
                "final_prompt": final_prompt.strip(),
                "status": "success",
            })

            print("\n>>> FINAL MICROSETTING:")
            print(final_prompt)

        except Exception as e:
            error_msg = str(e)
            print(f"    ERROR: {e}")

            # Record error in metadata
            metadata.append({
                "type": config.name,
                "description": config.description,
                "error": error_msg,
                "status": "error",
            })

    # Save to JSON
    output_path = save_output(prompts, metadata)
    print(f"\n[Saved to: {output_path}]")


if __name__ == "__main__":
    main()
