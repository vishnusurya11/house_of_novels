#!/usr/bin/env python3
"""
Generate Story - Complete pipeline from prompts to story.

Combines codex generation and story building into one command.

Usage:
    # Set your OpenRouter API key
    export OPENROUTER_API_KEY="your-key-here"

    # Standard story (~35 min)
    uv run python src/generate_story.py

    # Quick flash fiction (~10 min)
    uv run python src/generate_story.py --scope flash

    # Short story (~20 min)
    uv run python src/generate_story.py --scope short

    # Long story (~50 min)
    uv run python src/generate_story.py --scope long

    # Custom model
    uv run python src/generate_story.py --model "x-ai/grok-4.1-fast"
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path for proper package imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.codex_generator import main as generate_codex
from src.story_builder import (
    find_latest_codex, load_codex, extract_prompts, save_updated_codex
)
from src.story_workflows import run_full_story_pipeline
from src.config import DEFAULT_MODEL, STORY_SCOPES, DEFAULT_STORY_SCOPE


def main():
    """Run complete story generation pipeline."""
    parser = argparse.ArgumentParser(
        description="Generate complete story from scratch (codex + story)"
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"LLM model to use (default: {DEFAULT_MODEL})"
    )
    parser.add_argument(
        "--scope",
        choices=list(STORY_SCOPES.keys()),
        default=DEFAULT_STORY_SCOPE,
        help="Story length: flash (~10min), short (~20min), standard (~35min), long (~50min)"
    )
    args = parser.parse_args()

    scope_config = STORY_SCOPES[args.scope]

    print("\n" + "#" * 60)
    print("# GENERATE STORY - Complete Pipeline")
    print(f"# Model: {args.model}")
    print(f"# Scope: {args.scope} - {scope_config['description']}")
    print("#" * 60)

    # Step 1: Generate codex (prompts + setting)
    print("\n" + "=" * 60)
    print("STEP 1: GENERATING CODEX (prompts + setting)")
    print("=" * 60)
    generate_codex()

    # Step 2: Find the codex we just created
    codex_path = find_latest_codex()
    if not codex_path:
        print("\nERROR: Codex generation failed - no codex file found")
        sys.exit(1)

    print(f"\n>>> Using codex: {codex_path.name}")

    # Step 3: Load codex and extract prompts
    codex = load_codex(codex_path)
    story_prompt, setting_prompt = extract_prompts(codex)

    # Step 4: Run story builder pipeline
    print("\n" + "=" * 60)
    print("STEP 2: GENERATING STORY")
    print("=" * 60)

    story_data = run_full_story_pipeline(
        story_prompt=story_prompt,
        setting_prompt=setting_prompt,
        model=args.model,
        scope=args.scope
    )

    # Step 5: Save to codex
    output_path = save_updated_codex(codex, story_data, codex_path)

    # Print summary
    print("\n" + "#" * 60)
    print("# COMPLETE!")
    print(f"# Story saved to: {output_path}")
    print("#" * 60)

    # Print story details
    story = story_data.get("story", {})
    outline = story.get("outline", {})
    if isinstance(outline, dict) and "title" in outline:
        print(f"\n>>> Title: {outline.get('title', 'Untitled')}")
        print(f">>> Logline: {outline.get('logline', 'N/A')}")
        print(f">>> Characters: {len(story.get('characters', []))}")
        print(f">>> Locations: {len(story.get('locations', []))}")

        narrative = story.get("narrative", {})
        if isinstance(narrative, dict) and "acts" in narrative:
            total_scenes = sum(
                len(act.get("scenes", []))
                for act in narrative.get("acts", [])
            )
            print(f">>> Scenes written: {total_scenes}")


if __name__ == "__main__":
    main()
