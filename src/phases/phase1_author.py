#!/usr/bin/env python3
"""
Phase 1: Author-Driven Story Creation

Unified Phase 1 with 9 selective sub-steps, driven by the author's unique approach.
Each author can implement the steps differently while maintaining the same I/O contract.

Steps:
    1: Plotting - Structure research → Beat sheet → Scene outline
    2: Characters - Generate characters, name mapping
    3: World Building - Expand setting + Generate lore/rules + Locations
    4: Critique & Revise - Structure/pacing critique → Outline revision
    5: Complete Narrative - Write full prose story
    6: Narrative Revision - Multi-focus revision
    7: Screenplay - Format narrative for presentation
    8: Final Polish - Final continuity/prose polish
    9: Final Output - Validate and finalize story dict

Usage (standalone):
    uv run python -m src.phases.phase1_author forge/xxx/codex.json
    uv run python -m src.phases.phase1_author forge/xxx/codex.json --steps 1
    uv run python -m src.phases.phase1_author forge/xxx/codex.json --steps 1 2 3
"""

import sys
import json
import argparse
import importlib
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

# Add parent directory to path for proper package imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config import DEFAULT_MODEL


@dataclass
class Phase1AuthorResult:
    """Result of Phase 1 Author-Driven execution."""
    codex_path: Path
    outline: dict
    characters: list
    locations: list
    success: bool
    error: Optional[str] = None
    steps_completed: list[int] = field(default_factory=list)
    step_timings: dict = field(default_factory=dict)


def load_codex(codex_path: Path) -> dict:
    """Load codex JSON file."""
    with open(codex_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_codex(codex: dict, codex_path: Path) -> None:
    """Save codex JSON file."""
    with open(codex_path, "w", encoding="utf-8") as f:
        json.dump(codex, f, indent=2, ensure_ascii=False)


def get_author_phase1_runner(author_id: str, model: str = None):
    """Get the Phase 1 runner for a specific author.

    Attempts to import the author's module and get their phase1 runner.
    Falls back to default BaseAuthorPhase1 if no custom runner exists.

    Args:
        author_id: The author's ID (e.g., "marcus_vane")
        model: LLM model to use

    Returns:
        BaseAuthorPhase1 instance (or subclass) for this author
    """
    # Try to import author's specific phase1 runner
    try:
        module = importlib.import_module(f"src.authors.personas.{author_id}")
        if hasattr(module, "get_phase1_runner"):
            return module.get_phase1_runner(model=model)
    except ImportError:
        pass

    # Fallback: use default runner with author from registry
    from src.authors import get_author
    from src.authors.base_phase1 import BaseAuthorPhase1

    author = get_author(author_id)
    return BaseAuthorPhase1(author, model=model)


def run_phase1_author(
    codex_path: Path,
    model: str = None,
    steps: list[int] = None,
    revision_passes: int = None,
) -> Phase1AuthorResult:
    """
    Run Phase 1: Author-Driven Story Creation.

    Loads the codex, identifies the author, and delegates to their
    Phase 1 implementation.

    Args:
        codex_path: Path to codex JSON file
        model: LLM model to use (default: from codex or config)
        steps: List of step numbers to run (1-9). Default: all steps.
        revision_passes: Number of revision passes for step 6.

    Returns:
        Phase1AuthorResult with outline, characters, locations
    """
    codex_path = Path(codex_path)

    print(f"\n{'='*60}")
    print("PHASE 1: AUTHOR-DRIVEN STORY CREATION")
    print(f"{'='*60}")
    print(f">>> Codex: {codex_path}")

    # Load codex
    codex = load_codex(codex_path)

    # Get model from codex config or use default
    codex_config = codex.get("config", {})
    model = model or codex_config.get("model", DEFAULT_MODEL)
    print(f">>> Model: {model}")

    # Get author from codex
    author_data = codex.get("author", {})
    author_id = author_data.get("id")

    if not author_id:
        return Phase1AuthorResult(
            codex_path=codex_path,
            outline={},
            characters=[],
            locations=[],
            success=False,
            error="No author found in codex. Run Phase 0 first.",
        )

    print(f">>> Author: {author_data.get('name', author_id)}")

    # Get author's Phase 1 runner
    try:
        phase1_runner = get_author_phase1_runner(author_id, model=model)
    except Exception as e:
        return Phase1AuthorResult(
            codex_path=codex_path,
            outline={},
            characters=[],
            locations=[],
            success=False,
            error=f"Failed to load author's Phase 1 runner: {e}",
        )

    # Run Phase 1 with author's implementation
    try:
        run_result = phase1_runner.run(
            codex=codex,
            steps=steps,
            revision_passes=revision_passes,
        )
    except Exception as e:
        return Phase1AuthorResult(
            codex_path=codex_path,
            outline={},
            characters=[],
            locations=[],
            success=False,
            error=f"Phase 1 execution failed: {e}",
        )

    # Save updated codex
    save_codex(codex, codex_path)
    print(f"\n>>> Codex saved to: {codex_path}")

    # Extract results
    story = codex.get("story", {})
    outline = story.get("outline", {})
    characters = story.get("characters", [])
    locations = story.get("locations", [])

    steps_completed = run_result.get("steps_completed", [])
    step_timings = run_result.get("step_timings", {})

    print(f"\n>>> Phase 1 complete!")
    print(f">>> Steps completed: {steps_completed}")

    return Phase1AuthorResult(
        codex_path=codex_path,
        outline=outline,
        characters=characters,
        locations=locations,
        success=True,
        steps_completed=steps_completed,
        step_timings=step_timings,
    )


def main():
    """CLI entry point for standalone execution."""
    parser = argparse.ArgumentParser(
        description="Phase 1: Author-Driven Story Creation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all steps
  uv run python -m src.phases.phase1_author forge/xxx/codex.json

  # Run only Step 1 (Plotting)
  uv run python -m src.phases.phase1_author forge/xxx/codex.json --steps 1

  # Run Steps 1-3
  uv run python -m src.phases.phase1_author forge/xxx/codex.json --steps 1 2 3
        """
    )
    parser.add_argument(
        "codex_path",
        type=Path,
        help="Path to codex JSON file"
    )
    parser.add_argument(
        "--model",
        default=None,
        help=f"LLM model (default: from codex or {DEFAULT_MODEL})"
    )
    parser.add_argument(
        "--steps",
        nargs="+",
        type=int,
        choices=list(range(1, 10)),
        help="Run specific steps (1-9). Example: --steps 1 2 3"
    )
    parser.add_argument(
        "--revision-passes",
        type=int,
        default=None,
        help="Number of revision passes for Step 6"
    )

    args = parser.parse_args()

    if not args.codex_path.exists():
        print(f"ERROR: Codex not found: {args.codex_path}")
        sys.exit(1)

    result = run_phase1_author(
        codex_path=args.codex_path,
        model=args.model,
        steps=args.steps,
        revision_passes=args.revision_passes,
    )

    if not result.success:
        print(f"\n>>> ERROR: {result.error}")
        sys.exit(1)

    # Print summary
    outline = result.outline
    if outline:
        hl_struct = outline.get("high_level_structure", {})
        if hl_struct:
            print(f"\n>>> Theme: {hl_struct.get('theme', 'N/A')}")
            print(f">>> Central Conflict: {hl_struct.get('central_conflict', 'N/A')[:100]}...")


if __name__ == "__main__":
    main()
