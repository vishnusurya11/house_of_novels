#!/usr/bin/env python3
"""
Phase 2: Characters & Locations Generation

Creates character profiles and location descriptions based on story outline.
Requires Phase 1 (outline) to be complete.

Usage (standalone):
    uv run python -m src.phases.phase2_characters forge/20260105143022/codex.json
    uv run python -m src.phases.phase2_characters forge/20260105143022/codex.json --scope flash

Fix names in existing codex (repair mismatched names from debate):
    uv run python -m src.phases.phase2_characters forge/20260105143022/codex.json --fix-names
"""

import sys
import json
import time
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

# Add parent directory to path for proper package imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.story_workflows import (
    run_phase2_characters_locations as _run_phase2,
    apply_name_substitutions,
)
from src.config import DEFAULT_MODEL, STORY_SCOPES, DEFAULT_STORY_SCOPE


@dataclass
class Phase2Result:
    """Result of Phase 2 character/location generation."""
    codex_path: Path
    characters: list[dict]
    locations: list[dict]
    metadata: dict
    success: bool
    error: Optional[str] = None
    step_timings: dict = field(default_factory=dict)


def load_codex(codex_path: Path) -> dict:
    """Load codex JSON file."""
    with open(codex_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_codex(codex: dict, codex_path: Path) -> None:
    """Save codex JSON file."""
    with open(codex_path, "w", encoding="utf-8") as f:
        json.dump(codex, f, indent=2, ensure_ascii=False)


def extract_setting_prompt(codex: dict) -> str:
    """Extract setting_prompt from codex."""
    dow_prompts = codex.get("deck_of_worlds", {}).get("prompts", [])
    return dow_prompts[0].get("prompt", "") if dow_prompts else ""


def run_phase2_characters(
    codex_path: Path,
    model: str = None,
    scope: str = None,
) -> Phase2Result:
    """
    Generate characters and locations from outline in codex.

    Args:
        codex_path: Path to codex.json (must have outline from Phase 1)
        model: LLM model to use (default: from codex config)
        scope: Story scope - determines max characters/locations (default: from codex)

    Returns:
        Phase2Result with characters and locations
    """
    codex_path = Path(codex_path)
    codex = load_codex(codex_path)

    # Use codex config as defaults
    codex_config = codex.get("config", {})
    model = model or codex_config.get("model", DEFAULT_MODEL)
    scope = scope or codex_config.get("scope", DEFAULT_STORY_SCOPE)

    # Validate Phase 1 completed
    story = codex.get("story", {})
    if "outline" not in story:
        raise ValueError("Codex missing outline. Run Phase 1 first.")

    outline_json = json.dumps(story["outline"])
    setting_prompt = extract_setting_prompt(codex)
    scope_config = STORY_SCOPES.get(scope, STORY_SCOPES[DEFAULT_STORY_SCOPE])

    print(f"\n>>> Using model: {model}")
    print(f">>> Scope: {scope} - max {scope_config['max_characters']} characters, {scope_config['max_locations']} locations")

    # Step timing
    step_timings = {}
    step_start = time.time()

    # Use existing workflow function
    result = _run_phase2(
        outline_json,
        setting_prompt,
        model,
        max_characters=scope_config["max_characters"],
        max_locations=scope_config["max_locations"]
    )
    step_timings["step1_generation"] = round(time.time() - step_start, 2)

    # Update codex with character/location profiles (names are embedded in characters)
    codex["story"]["characters"] = result["characters"]
    codex["story"]["locations"] = result["locations"]

    # Assign unique IDs to characters and locations
    for i, char in enumerate(codex["story"]["characters"]):
        char["id"] = f"char_{i+1:03d}"
    for i, loc in enumerate(codex["story"]["locations"]):
        loc["id"] = f"loc_{i+1:03d}"

    print(f"    Assigned IDs to {len(codex['story']['characters'])} characters and {len(codex['story']['locations'])} locations")

    # CRITICAL: Save updated outline with debated names back to codex
    # This ensures Phase 3+ sees the outline with correct character names
    if "outline_updated" in result and result["outline_updated"]:
        codex["story"]["outline"] = result["outline_updated"]
        print("    Updated outline saved with debated names.")

    # Store metadata including name debate details
    if "story_metadata" not in codex:
        codex["story_metadata"] = {}
    codex["story_metadata"]["phase2_characters"] = result["metadata"]

    save_codex(codex, codex_path)

    print(f"\n>>> Characters & Locations saved to: {codex_path}")

    return Phase2Result(
        codex_path=codex_path,
        characters=result["characters"],
        locations=result["locations"],
        metadata=result["metadata"],
        success=True,
        step_timings=step_timings,
    )


def fix_names(codex_path: Path) -> dict:
    """
    Fix names in existing codex by applying name substitutions.

    Use this to repair a codex where names were generated via debate
    but not applied to characters/narrative.

    Args:
        codex_path: Path to codex.json with name_mapping in metadata

    Returns:
        Dict with substitution stats
    """
    codex_path = Path(codex_path)
    codex = load_codex(codex_path)

    # Get name_mapping from metadata (stored during Phase 2)
    mapping = codex.get("story_metadata", {}).get("phase2_characters", {}).get("name_mapping", {})
    if not mapping:
        # Fallback: check if it's stored at top level
        mapping = codex.get("story", {}).get("name_mapping", {})

    if not mapping:
        print("ERROR: No name mapping found in codex. Run Phase 2 first.")
        return {"success": False, "error": "No name_mapping in codex"}

    print(f"\n{'='*60}")
    print("FIX NAMES: Applying name substitutions to existing codex")
    print(f"{'='*60}")

    # Apply substitutions with the mapping
    codex = apply_name_substitutions(codex, mapping)

    # Save updated codex
    save_codex(codex, codex_path)

    print(f"\n>>> Name substitutions applied!")
    print(f"    Replacements: {len(mapping)}")
    print(f"    Saved to: {codex_path}")

    return {
        "success": True,
        "mapping": mapping,
        "replacements": len(mapping),
    }


def main():
    """CLI entry point for standalone execution."""
    parser = argparse.ArgumentParser(
        description="Phase 2: Generate characters and locations"
    )
    parser.add_argument(
        "codex_path",
        type=Path,
        help="Path to codex.json (must have outline from Phase 1)"
    )
    parser.add_argument(
        "--model",
        default=None,
        help=f"LLM model (default: from codex or {DEFAULT_MODEL})"
    )
    parser.add_argument(
        "--scope",
        choices=list(STORY_SCOPES.keys()),
        default=None,
        help="Story scope (default: from codex)"
    )
    parser.add_argument(
        "--fix-names",
        action="store_true",
        help="Fix names in existing codex (apply name substitutions without re-running Phase 2)"
    )
    args = parser.parse_args()

    if not args.codex_path.exists():
        print(f"ERROR: Codex not found: {args.codex_path}")
        sys.exit(1)

    # If --fix-names flag is set, just apply name substitutions
    if args.fix_names:
        result = fix_names(args.codex_path)
        if not result["success"]:
            sys.exit(1)
        return

    # Otherwise run full Phase 2
    result = run_phase2_characters(
        args.codex_path,
        model=args.model,
        scope=args.scope,
    )

    print(f"\n>>> Characters: {len(result.characters)}")
    for char in result.characters:
        print(f"    - {char.get('name', 'Unknown')}: {char.get('role_in_story', 'unknown role')}")

    print(f"\n>>> Locations: {len(result.locations)}")
    for loc in result.locations:
        print(f"    - {loc.get('name', 'Unknown')}: {loc.get('type', 'unknown type')}")


if __name__ == "__main__":
    main()
