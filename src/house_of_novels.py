#!/usr/bin/env python3
"""
House of Novels - Complete Novel Generation Pipeline

Main orchestrator that runs all phases in sequence to generate a complete novel.
Can be imported as a module or run via CLI.

Phases:
    0. codex      - Story seed generation + author selection
    1. author     - 10-step author-driven creation (plotting, characters, narrative, revision)
    2. prompts    - Image/video prompts (character, location, scene, poster, thumbnail)
    3. generation - Media generation (audio + images via ComfyUI)
    4. editing    - Video editing (combine audio, create videos)
    5. upload     - YouTube upload

Usage (as module):
    from src.house_of_novels import generate_novel

    # Generate with defaults
    result_path = generate_novel()

    # Generate with options
    result_path = generate_novel(
        scope="flash",
        model="x-ai/grok-4.1-fast",
        phases=["codex", "author", "prompts"],  # Partial run
    )

Usage (CLI):
    # Full pipeline with defaults
    uv run python -m src.house_of_novels

    # Flash fiction
    uv run python -m src.house_of_novels --scope flash

    # Specific phases only
    uv run python -m src.house_of_novels --phases codex author prompts

    # Resume from existing codex
    uv run python -m src.house_of_novels --codex forge/20260105143022/codex.json --phases prompts generation
"""

import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import Optional

# Add parent directory to path for proper package imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import (
    DEFAULT_MODEL,
    STORY_SCOPES,
    DEFAULT_STORY_SCOPE,
    PHASE_NAMES,
    DEFAULT_FORGE_DIR,
)
from src.phases.phase0_codex import run_phase0_codex
from src.phases.phase1_author import run_phase1_author
from src.phases.phase2_prompts import run_phase2_prompts
from src.phases.phase3_generation import run_phase3_generation
from src.phases.phase4_editing import run_phase4_editing
from src.phases.phase5_upload import run_phase5_upload
from src.templates import get_template, set_template, TEMPLATES, DEFAULT_TEMPLATE
from src.authors import list_authors


@dataclass
class NovelResult:
    """Result of complete novel generation."""
    forge_path: Path
    codex_path: Path
    phases_completed: list[str]
    title: Optional[str]
    total_scenes: int
    total_characters: int
    total_locations: int
    success: bool
    error: Optional[str] = None


def generate_novel(
    scope: str = DEFAULT_STORY_SCOPE,
    model: str = None,
    output_dir: str = DEFAULT_FORGE_DIR,
    phases: list[str] = None,
    codex_path: str = None,
    template: str = DEFAULT_TEMPLATE,
    author_id: str = None,
    structure_id: str = None,
) -> Path:
    """
    Generate a complete novel end-to-end.

    Args:
        scope: Story scope - "flash", "short", "standard", "long"
        model: LLM model to use (defaults to config.DEFAULT_MODEL)
        output_dir: Base output directory (default: "forge")
        phases: List of phases to run. None = all phases.
                Options: ["codex", "author", "prompts", "generation", "editing", "upload"]
        codex_path: Path to existing codex (skip phase 0, resume from this file)
        template: Template for media generation (default: "static_audio")
        author_id: Specific author ID to use (default: random selection)
        structure_id: Specific story structure to use (default: author's preferred)

    Returns:
        Path to the generated forge folder (e.g., forge/20260105143022/)
    """
    model = model or DEFAULT_MODEL
    phases = phases or PHASE_NAMES  # All phases if not specified

    # Set the active template for phases 5-6
    current_template = set_template(template)

    # Validate phases
    invalid_phases = set(phases) - set(PHASE_NAMES)
    if invalid_phases:
        raise ValueError(f"Invalid phases: {invalid_phases}. Valid: {PHASE_NAMES}")

    # Determine output directory
    if codex_path:
        # Resume mode: use existing codex's directory
        codex_path = Path(codex_path)
        if not codex_path.exists():
            raise FileNotFoundError(f"Codex not found: {codex_path}")
        forge_path = codex_path.parent
        timestamp = None  # Not needed for resume
    else:
        # New run: create timestamped directory
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        forge_path = Path(output_dir) / timestamp
        forge_path.mkdir(parents=True, exist_ok=True)
        codex_path = forge_path / f"codex_{timestamp}.json"

    scope_config = STORY_SCOPES.get(scope, STORY_SCOPES[DEFAULT_STORY_SCOPE])

    print("\n" + "#" * 60)
    print("# HOUSE OF NOVELS")
    print("#" * 60)
    print(f"# Output: {forge_path}")
    print(f"# Model: {model}")
    print(f"# Scope: {scope} - {scope_config['description']}")
    print(f"# Template: {current_template.name} - {current_template.description}")
    print(f"# Phases: {', '.join(phases)}")
    print("#" * 60)

    completed_phases = []
    title = None
    total_scenes = 0
    total_characters = 0
    total_locations = 0

    # Timing tracking
    pipeline_start = time.time()
    pipeline_start_iso = datetime.now().isoformat()
    phase_timings = {}

    # Phase 0: Codex Generation
    if "codex" in phases:
        print("\n" + "=" * 60)
        print("PHASE 0: CODEX GENERATION")
        print("=" * 60)
        phase_start = time.time()
        result = run_phase0_codex(
            forge_path,
            model=model,
            scope=scope,
            timestamp=timestamp,
            author_id=author_id,
            structure_id=structure_id,
        )
        phase_timings["codex"] = {"duration_seconds": round(time.time() - phase_start, 2)}
        codex_path = result.codex_path
        completed_phases.append("codex")
        print(f"\n>>> Story prompt: {result.story_prompt[:60]}...")
        print(f">>> Setting prompt: {result.setting_prompt[:60]}...")
        print(f">>> Phase 0 completed in {phase_timings['codex']['duration_seconds']:.1f}s")

    # Phase 1: Author (10-step author-driven story creation)
    if "author" in phases:
        print("\n" + "=" * 60)
        print("PHASE 1: AUTHOR (10-Step Story Creation)")
        print("=" * 60)
        phase_start = time.time()
        result = run_phase1_author(codex_path, model=model)
        phase_timings["author"] = {
            "duration_seconds": round(time.time() - phase_start, 2),
            "steps": getattr(result, "step_timings", {})
        }
        completed_phases.append("author")
        # Load codex to get title and counts
        with open(codex_path, "r", encoding="utf-8") as f:
            codex_data = json.load(f)
        chapters_data = codex_data.get("story", {}).get("chapters", {})
        title = chapters_data.get("title", "Untitled")
        total_characters = len(codex_data.get("story", {}).get("characters", []))
        total_locations = len(codex_data.get("story", {}).get("locations", []))
        total_scenes = sum(len(ch.get("scenes", [])) for ch in chapters_data.get("chapters", []))
        print(f"\n>>> Title: {title}")
        print(f">>> Characters: {total_characters}")
        print(f">>> Locations: {total_locations}")
        print(f">>> Scenes: {total_scenes}")
        print(f">>> Phase 1 completed in {phase_timings['author']['duration_seconds']:.1f}s")

    # Phase 2: Prompts (Character, Location, Scene, Poster, Thumbnail)
    if "prompts" in phases:
        print("\n" + "=" * 60)
        print("PHASE 2: PROMPT GENERATION")
        print("=" * 60)
        phase_start = time.time()
        result = run_phase2_prompts(codex_path, model=model)
        phase_timings["prompts"] = {
            "duration_seconds": round(time.time() - phase_start, 2),
            "steps": getattr(result, "step_timings", {})
        }
        completed_phases.append("prompts")
        print(f"\n>>> Character prompts: {result.character_prompt_count}")
        print(f">>> Location prompts: {result.location_prompt_count}")
        print(f">>> Poster prompts: {result.poster_prompt_count}")
        print(f">>> Scene image prompts: {result.scene_image_prompt_count}")
        print(f">>> Phase 2 completed in {phase_timings['prompts']['duration_seconds']:.1f}s")

    # Phase 3: Generation (ComfyUI audio/images)
    if "generation" in phases:
        print("\n" + "=" * 60)
        print("PHASE 3: MEDIA GENERATION")
        print("=" * 60)
        phase_start = time.time()
        result = run_phase3_generation(codex_path, steps=[0, 1, 2, 3, 4])
        phase_timings["generation"] = {
            "duration_seconds": round(time.time() - phase_start, 2),
            "steps": getattr(result, "step_timings", {})
        }
        completed_phases.append("generation")
        print(f"\n>>> Audio files: {result.audio_count}")
        print(f">>> Character portraits: {result.character_portrait_count}")
        print(f">>> Location images: {result.location_image_count}")
        print(f">>> Poster images: {result.poster_count}")
        print(f">>> Scene images: {result.scene_image_count}")
        print(f">>> Phase 3 completed in {phase_timings['generation']['duration_seconds']:.1f}s")

    # Phase 4: Editing (combine audio, create videos)
    if "editing" in phases:
        print("\n" + "=" * 60)
        print("PHASE 4: AUDIO/VIDEO EDITING")
        print("=" * 60)
        phase_start = time.time()
        result = run_phase4_editing(codex_path, steps=[1, 2, 3])
        phase_timings["editing"] = {
            "duration_seconds": round(time.time() - phase_start, 2),
            "steps": getattr(result, "step_timings", {})
        }
        completed_phases.append("editing")
        if result.success:
            print(f"\n>>> Scene audio files: {result.scene_audio_count}")
            print(f">>> Scene videos: {result.scene_video_count}")
            if result.video_output_path:
                print(f">>> Final video: {result.video_output_path}")
                print(f">>> Total duration: {result.video_duration:.1f}s")
            print(f">>> Phase 4 completed in {phase_timings['editing']['duration_seconds']:.1f}s")
        else:
            print(f"\n>>> Editing failed: {result.error}")

    # Phase 5: YouTube Upload
    if "upload" in phases:
        print("\n" + "=" * 60)
        print("PHASE 5: YOUTUBE UPLOAD")
        print("=" * 60)
        phase_start = time.time()
        result = run_phase5_upload(codex_path)
        phase_timings["upload"] = {
            "duration_seconds": round(time.time() - phase_start, 2),
            "steps": getattr(result, "step_timings", {})
        }
        completed_phases.append("upload")
        if result.success:
            print(f"\n>>> Video URL: {result.video_url}")
            print(f">>> Title: {result.title}")
            print(f">>> Phase 5 completed in {phase_timings['upload']['duration_seconds']:.1f}s")
        else:
            print(f"\n>>> Upload failed: {result.error}")

    # Calculate total pipeline time
    pipeline_end = time.time()
    pipeline_end_iso = datetime.now().isoformat()
    total_seconds = round(pipeline_end - pipeline_start, 2)

    # Build execution_timing structure
    execution_timing = {
        "pipeline_start_iso": pipeline_start_iso,
        "pipeline_end_iso": pipeline_end_iso,
        "total_seconds": total_seconds,
        "total_minutes": round(total_seconds / 60, 2),
        "phases": phase_timings,
    }

    # Save timing to codex
    if codex_path.exists():
        with open(codex_path, "r", encoding="utf-8") as f:
            codex_data = json.load(f)
        codex_data["execution_timing"] = execution_timing
        with open(codex_path, "w", encoding="utf-8") as f:
            json.dump(codex_data, f, indent=2, ensure_ascii=False)

    print("\n" + "#" * 60)
    print("# COMPLETE!")
    print("#" * 60)
    print(f"# Codex: {codex_path}")
    print(f"# Phases completed: {', '.join(completed_phases)}")
    if title:
        print(f"# Title: {title}")
    print("#" * 60)

    # Print timing summary
    print("\n" + "=" * 60)
    print("EXECUTION TIMING SUMMARY")
    print("=" * 60)
    print(f"Total pipeline time: {total_seconds:.1f}s ({total_seconds/60:.1f} minutes)")
    print("-" * 40)
    for phase_name, timing in phase_timings.items():
        duration = timing.get("duration_seconds", 0)
        print(f"  {phase_name}: {duration:.1f}s")
        steps = timing.get("steps", {})
        if steps:
            for step_name, step_duration in steps.items():
                if isinstance(step_duration, (int, float)):
                    print(f"    - {step_name}: {step_duration:.1f}s")
                elif isinstance(step_duration, dict) and "duration_seconds" in step_duration:
                    print(f"    - {step_name}: {step_duration['duration_seconds']:.1f}s")
    print("=" * 60)

    return forge_path


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="House of Novels - Complete novel generation pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate complete novel with defaults (standard scope, static_audio template)
  uv run python -m src.house_of_novels

  # Quick flash fiction
  uv run python -m src.house_of_novels --scope flash

  # Only generate codex and author phases
  uv run python -m src.house_of_novels --phases codex author

  # Resume from existing codex (add prompts and media)
  uv run python -m src.house_of_novels --codex forge/20260105143022/codex.json --phases prompts generation

  # Use specific model
  uv run python -m src.house_of_novels --model "x-ai/grok-4.1-fast"

  # Use a specific template
  uv run python -m src.house_of_novels --template static_audio
        """
    )
    parser.add_argument(
        "--scope",
        choices=list(STORY_SCOPES.keys()),
        default=DEFAULT_STORY_SCOPE,
        help="Story scope: flash (~10min), short (~20min), standard (~35min), long (~50min)"
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"LLM model to use (default: {DEFAULT_MODEL})"
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_FORGE_DIR,
        help=f"Output directory (default: {DEFAULT_FORGE_DIR})"
    )
    parser.add_argument(
        "--phases",
        nargs="+",
        choices=PHASE_NAMES,
        default=None,
        help=f"Phases to run (default: all). Options: {', '.join(PHASE_NAMES)}"
    )
    parser.add_argument(
        "--codex",
        type=str,
        default=None,
        help="Path to existing codex.json (resume mode)"
    )
    parser.add_argument(
        "--template",
        choices=list(TEMPLATES.keys()),
        default=DEFAULT_TEMPLATE,
        help=f"Output template for media generation (default: {DEFAULT_TEMPLATE})"
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
            print(f"      Genres: {', '.join(author_info['genres'])}")
            print(f"      Preferred structure: {author_info['preferred_structure']}")
        sys.exit(0)

    try:
        forge_path = generate_novel(
            scope=args.scope,
            model=args.model,
            output_dir=args.output_dir,
            phases=args.phases,
            codex_path=args.codex,
            template=args.template,
            author_id=args.author,
            structure_id=args.structure,
        )
        print(f"\nNovel generated at: {forge_path}")
    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
    # Force immediate exit — Python's interpreter shutdown after a heavy
    # langchain + httpx + CUDA session takes 30+ seconds, making the process
    # appear stuck after "Novel generated at:" output. os._exit() skips the
    # slow GC/module teardown. HTTP pool and disk cache are cleaned up by the
    # atexit handler registered in base_story_agent.py (called before os._exit).
    import atexit
    atexit._run_exitfuncs()
    import os
    os._exit(0)
