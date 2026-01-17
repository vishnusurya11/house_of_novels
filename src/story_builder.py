#!/usr/bin/env python3
"""
Story Builder - Multi-phase story generation from codex input.

Takes a codex JSON file (containing story_engine and deck_of_worlds prompts)
and generates a complete story through 3 phases of agent-based critique and revision.

Phase 1: Story Outline (3-act structure, hero's journey, try-fail cycles)
Phase 2: Character & Location Profiles
Phase 3: Narrative Prose

Usage:
    # Set your OpenRouter API key
    export OPENROUTER_API_KEY="your-key-here"

    # Run with a codex file (standard ~35 min story)
    uv run python src/story_builder.py output/codex_20260103160507.json

    # Quick flash fiction (~10 min)
    uv run python src/story_builder.py --scope flash

    # Short story (~20 min)
    uv run python src/story_builder.py --scope short

    # Long story (~50 min)
    uv run python src/story_builder.py --scope long
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# Add parent directory to path for proper package imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.story_workflows import run_full_story_pipeline
from src.config import DEFAULT_MODEL, STORY_SCOPES, DEFAULT_STORY_SCOPE


def get_output_dir() -> Path:
    """Get or create output directory."""
    output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(exist_ok=True)
    return output_dir


def find_latest_codex() -> Path | None:
    """Find the most recent codex file in output directory."""
    output_dir = get_output_dir()
    codex_files = list(output_dir.glob("codex_*.json"))
    if not codex_files:
        return None
    return max(codex_files, key=lambda p: p.stat().st_mtime)


def load_codex(codex_path: Path) -> dict:
    """Load and validate codex JSON file."""
    with open(codex_path, "r", encoding="utf-8") as f:
        codex = json.load(f)

    # Validate structure
    if "story_engine" not in codex or "deck_of_worlds" not in codex:
        raise ValueError("Codex file must contain 'story_engine' and 'deck_of_worlds' sections")

    return codex


def extract_prompts(codex: dict) -> tuple[str, str]:
    """
    Extract story prompt and setting prompt from codex.

    Returns:
        Tuple of (story_prompt, setting_prompt)
    """
    # Get story engine prompt
    se_prompts = codex.get("story_engine", {}).get("prompts", [])
    if not se_prompts:
        raise ValueError("No story_engine prompts found in codex")
    story_prompt = se_prompts[0].get("prompt", "")

    # Get deck of worlds prompt
    dow_prompts = codex.get("deck_of_worlds", {}).get("prompts", [])
    if not dow_prompts:
        raise ValueError("No deck_of_worlds prompts found in codex")
    setting_prompt = dow_prompts[0].get("prompt", "")

    return story_prompt, setting_prompt


def save_updated_codex(codex: dict, story_data: dict, original_path: Path) -> Path:
    """
    Save codex with story data added - updates the original codex file.

    Args:
        codex: Original codex data
        story_data: Generated story data from pipeline
        original_path: Path to original codex file

    Returns:
        Path to saved file (same as original_path)
    """
    # Add story data to codex
    codex["story"] = story_data["story"]
    codex["story_metadata"] = story_data["story_metadata"]
    codex["story_generated_at"] = datetime.now().isoformat()

    # Update the original codex file in-place
    with open(original_path, "w", encoding="utf-8") as f:
        json.dump(codex, f, indent=2, ensure_ascii=False)

    return original_path


def main():
    """Run story builder pipeline."""
    parser = argparse.ArgumentParser(
        description="Generate a complete story from a codex file"
    )
    parser.add_argument(
        "codex_path",
        nargs="?",
        help="Path to codex JSON file (uses latest if not specified)"
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
        help="Story scope/length: flash (~10min), short (~20min), standard (~35min), long (~50min)"
    )
    args = parser.parse_args()

    # Find codex file
    if args.codex_path:
        codex_path = Path(args.codex_path)
    else:
        codex_path = find_latest_codex()
        if not codex_path:
            print("ERROR: No codex files found in output directory.")
            print("Run codex_generator.py first to create a codex.")
            sys.exit(1)

    if not codex_path.exists():
        print(f"ERROR: Codex file not found: {codex_path}")
        sys.exit(1)

    scope_config = STORY_SCOPES[args.scope]
    print("\n" + "#" * 60)
    print("# STORY BUILDER")
    print(f"# Input: {codex_path.name}")
    print(f"# Model: {args.model}")
    print(f"# Scope: {args.scope} - {scope_config['description']}")
    print("#" * 60)

    # Load codex
    try:
        codex = load_codex(codex_path)
        story_prompt, setting_prompt = extract_prompts(codex)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"ERROR: Failed to load codex: {e}")
        sys.exit(1)

    print(f"\n>>> Story Prompt: {story_prompt[:80]}...")
    print(f">>> Setting Prompt: {setting_prompt[:80]}...")

    # Run pipeline
    try:
        story_data = run_full_story_pipeline(
            story_prompt=story_prompt,
            setting_prompt=setting_prompt,
            model=args.model,
            scope=args.scope
        )
    except Exception as e:
        print(f"\nERROR: Pipeline failed: {e}")
        raise

    # Save results
    output_path = save_updated_codex(codex, story_data, codex_path)

    print("\n" + "#" * 60)
    print(f"# Story saved to: {output_path}")
    print("#" * 60)

    # Print story summary
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
