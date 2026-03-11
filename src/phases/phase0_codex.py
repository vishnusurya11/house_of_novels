#!/usr/bin/env python3
"""
Phase 0: Codex Generation

Generates story prompts and worldbuilding microsettings via multi-agent debate.
Creates the foundation codex that all subsequent phases build upon.

Usage (standalone):
    uv run python -m src.phases.phase0_codex --output-dir forge/20260105143022
    uv run python -m src.phases.phase0_codex  # Auto-creates timestamped folder
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional

# Add parent directory to path for proper package imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.graph import run_prompt_generation
from src.prompts import PROMPT_CONFIGS
from src.visual_styles import get_random_style
from src.config import (
    DEFAULT_MODEL,
    DEBATE_ROUNDS,
    CARDS_PER_DRAW,
    DEFAULT_FORGE_DIR,
    DEFAULT_STORY_SCOPE,
)
from src.authors import select_author, list_authors
from src.story_structures import get_structure


# Default config names for each deck type
STORY_ENGINE_CONFIGS = ["story_seed"]
DECK_OF_WORLDS_CONFIGS = ["simple_microsetting"]


@dataclass
class Phase0Result:
    """Result of Phase 0 codex generation."""
    codex_path: Path
    codex_data: dict
    story_prompt: str
    setting_prompt: str
    success: bool
    error: Optional[str] = None


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


def run_phase0_codex(
    output_dir: Path,
    model: str = DEFAULT_MODEL,
    scope: str = DEFAULT_STORY_SCOPE,
    story_configs: list[str] = None,
    world_configs: list[str] = None,
    timestamp: str = None,
    author_id: str = None,
    structure_id: str = None,
) -> Phase0Result:
    """
    Generate codex with story prompts and worldbuilding microsettings.

    Args:
        output_dir: Directory to save codex_{timestamp}.json
        model: LLM model to use
        scope: Story scope for later phases
        story_configs: Story engine config names (default: ["story_seed"])
        world_configs: Deck of worlds config names (default: ["simple_microsetting"])
        timestamp: Timestamp for codex filename (default: extracted from output_dir name)
        author_id: Specific author ID to use (default: random selection)
        structure_id: Specific story structure to use (default: author's preferred)

    Returns:
        Phase0Result with codex path and extracted prompts
    """
    story_configs = story_configs or STORY_ENGINE_CONFIGS
    world_configs = world_configs or DECK_OF_WORLDS_CONFIGS

    # Ensure output directory exists
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get timestamp from folder name or use provided/generate new
    if timestamp is None:
        # Try to extract from folder name (assumes YYYYMMDDHHMMSS format)
        folder_name = output_dir.name
        if len(folder_name) == 14 and folder_name.isdigit():
            timestamp = folder_name
        else:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    print("\n" + "=" * 50)
    print("PHASE 0: CODEX GENERATION")
    print("=" * 50)

    # Select random visual style for this story
    selected_style = get_random_style()
    print(f"\n>>> Visual Style: {selected_style['name']}")
    print(f"    {selected_style['description']}")

    # Select author (random if not specified)
    author = select_author(author_id=author_id)
    print(f"\n>>> Author: {author.name}")
    if author.pen_name:
        print(f"    Pen name: {author.pen_name}")
    print(f"    Specialty: {author.specialty}")
    print(f"    Genres: {', '.join(author.genres)}")

    # Select story structure (author's preferred if not specified)
    structure_to_use = structure_id or author.preferred_structure
    structure = get_structure(structure_to_use)
    print(f"\n>>> Story Structure: {structure.name}")
    print(f"    Source: {structure.source}")
    print(f"    Beats: {len(structure.beats)}")

    # Generate Story Engine prompts
    print("\n>>> Story Engine")
    se_prompts, se_metadata = generate_for_configs(story_configs)

    # Generate Deck of Worlds microsettings
    print("\n>>> Deck of Worlds")
    dow_prompts, dow_metadata = generate_for_configs(world_configs)

    # Rich Plot Expansion: expand seed + microsetting into multi-genre plots
    rich_plot_data = None
    plot_expansion_metadata = {}
    raw_seed = se_prompts[0].get("prompt", "") if se_prompts else ""
    raw_microsetting = dow_prompts[0].get("prompt", "") if dow_prompts else ""

    if raw_seed:
        try:
            from src.story_agents.plot_expansion_agents import expand_seed_to_plots

            print("\n>>> Plot Expansion (generating genre interpretations)...")
            rich_plot_data = expand_seed_to_plots(
                seed=raw_seed,
                microsetting=raw_microsetting,
            )
            plot_expansion_metadata = rich_plot_data.get("debate_metadata", {})
            print(f"    Winner: {rich_plot_data['winning_genre']} — \"{rich_plot_data['winning_plot']['title']}\"")
        except Exception as e:
            print(f"\n    WARNING: Plot expansion failed, falling back to raw seed: {e}")
            rich_plot_data = None
    else:
        print("\n    SKIP: No story seed for plot expansion")

    # Build codex data - core inputs at ROOT level, processing metadata separate
    codex_data = {
        "generated_at": datetime.now().isoformat(),
        "config": {
            "model": model,
            "scope": scope,
            "visual_style": selected_style,
            "debate_rounds": DEBATE_ROUNDS,
            "cards_per_draw": CARDS_PER_DRAW,
        },
        # Core story inputs at ROOT level
        "author": author.to_dict(),
        "story_structure": {
            "short_name": structure.short_name,
            "name": structure.name,
            "source": structure.source,
            "num_acts": structure.num_acts,
            "beats": [{"name": b.name, "description": b.description, "act": b.act, "quadrant": b.quadrant} for b in structure.beats],
        },
        "story_engine": {
            "prompts": se_prompts,
            **({"rich_plot": rich_plot_data} if rich_plot_data else {}),
        },
        "deck_of_worlds": {
            "prompts": dow_prompts,
        },
        # Phase processing metadata (each phase adds its own)
        "metadata": {
            "phase_0": {
                "story_engine": se_metadata,
                "deck_of_worlds": dow_metadata,
                **({"plot_expansion": plot_expansion_metadata} if plot_expansion_metadata else {}),
            }
        },
        "story": {},  # Will be populated by phase 1+
    }

    # Extract prompts for return value (prefer rich plot if available)
    if rich_plot_data and rich_plot_data.get("winning_plot"):
        story_prompt = rich_plot_data["winning_plot"]["plot"]
    else:
        story_prompt = se_prompts[0].get("prompt", "") if se_prompts else ""
    setting_prompt = dow_prompts[0].get("prompt", "") if dow_prompts else ""

    # Save codex with timestamp in filename
    codex_path = output_dir / f"codex_{timestamp}.json"
    with open(codex_path, "w", encoding="utf-8") as f:
        json.dump(codex_data, f, indent=2, ensure_ascii=False)

    print(f"\n>>> Codex saved to: {codex_path}")

    return Phase0Result(
        codex_path=codex_path,
        codex_data=codex_data,
        story_prompt=story_prompt,
        setting_prompt=setting_prompt,
        success=True,
    )


def main():
    """CLI entry point for standalone execution."""
    parser = argparse.ArgumentParser(
        description="Phase 0: Generate story codex with prompts"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Output directory (creates timestamped folder if not specified)"
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"LLM model (default: {DEFAULT_MODEL})"
    )
    parser.add_argument(
        "--scope",
        default=DEFAULT_STORY_SCOPE,
        help=f"Story scope for later phases (default: {DEFAULT_STORY_SCOPE})"
    )
    parser.add_argument(
        "--author",
        default=None,
        help="Author ID to use (default: random selection)"
    )
    parser.add_argument(
        "--structure",
        default=None,
        help="Story structure to use (default: author's preferred)"
    )
    parser.add_argument(
        "--list-authors",
        action="store_true",
        help="List available authors and exit"
    )
    args = parser.parse_args()

    # Handle --list-authors
    if args.list_authors:
        print("\nAvailable Authors:")
        for author_info in list_authors():
            print(f"  {author_info['id']}: {author_info['name']} - {author_info['specialty']}")
        sys.exit(0)

    # Create timestamped dir if not specified
    if args.output_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        args.output_dir = Path(DEFAULT_FORGE_DIR) / timestamp

    result = run_phase0_codex(
        args.output_dir,
        model=args.model,
        scope=args.scope,
        author_id=args.author,
        structure_id=args.structure,
    )

    print(f"\n>>> Story prompt: {result.story_prompt[:80]}...")
    print(f">>> Setting prompt: {result.setting_prompt[:80]}...")


if __name__ == "__main__":
    main()
