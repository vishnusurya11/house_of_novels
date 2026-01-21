#!/usr/bin/env python3
"""
House of Novels - Complete Novel Generation Pipeline

Main orchestrator that runs all phases in sequence to generate a complete novel.
Can be imported as a module or run via CLI.

Usage (as module):
    from src.house_of_novels import generate_novel

    # Generate with defaults
    result_path = generate_novel()

    # Generate with options
    result_path = generate_novel(
        scope="flash",
        model="x-ai/grok-4.1-fast",
        phases=["codex", "outline", "characters"],  # Partial run
    )

Usage (CLI):
    # Full pipeline with defaults
    uv run python -m src.house_of_novels

    # Flash fiction
    uv run python -m src.house_of_novels --scope flash

    # Specific phases only
    uv run python -m src.house_of_novels --phases codex outline characters

    # Resume from existing codex
    uv run python -m src.house_of_novels --codex forge/20260105143022/codex.json --phases narrative images
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
    should_run_step,
)
from src.phases.phase0_codex import run_phase0_codex
from src.phases.phase1_outline import run_phase1_outline
from src.phases.phase2_characters import run_phase2_characters
from src.phases.phase3_narrative import run_phase3_narrative
from src.phases.phase3b_storyboard import run_phase3b_storyboard
from src.phases.phase4_prompts import run_phase4_prompts
from src.phases.phase5_generation import run_phase5_generation
from src.phases.phase6_editing import run_phase6_editing
from src.phases.phase7_youtube import run_phase7_youtube
from src.templates import get_template, set_template, TEMPLATES, DEFAULT_TEMPLATE


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
) -> Path:
    """
    Generate a complete novel end-to-end.

    Args:
        scope: Story scope - "flash", "short", "standard", "long"
        model: LLM model to use (defaults to config.DEFAULT_MODEL)
        output_dir: Base output directory (default: "forge")
        phases: List of phases to run. None = all phases.
                Options: ["codex", "outline", "characters", "narrative", "storyboard", "prompts"]
        codex_path: Path to existing codex (skip phase 0, resume from this file)
        template: Template for media generation (default: "static_audio")

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
        result = run_phase0_codex(forge_path, model=model, scope=scope, timestamp=timestamp)
        phase_timings["codex"] = {"duration_seconds": round(time.time() - phase_start, 2)}
        codex_path = result.codex_path
        completed_phases.append("codex")
        print(f"\n>>> Story prompt: {result.story_prompt[:60]}...")
        print(f">>> Setting prompt: {result.setting_prompt[:60]}...")
        print(f">>> Phase 0 completed in {phase_timings['codex']['duration_seconds']:.1f}s")

    # Phase 1: Story Outline
    if "outline" in phases:
        print("\n" + "=" * 60)
        print("PHASE 1: STORY OUTLINE")
        print("=" * 60)
        phase_start = time.time()
        result = run_phase1_outline(codex_path, model=model, scope=scope)
        phase_timings["outline"] = {
            "duration_seconds": round(time.time() - phase_start, 2),
            "steps": getattr(result, "step_timings", {})
        }
        completed_phases.append("outline")
        title = result.outline.get("title", "Untitled")
        print(f"\n>>> Title: {title}")
        print(f">>> Logline: {result.outline.get('logline', 'N/A')[:80]}...")
        print(f">>> Phase 1 completed in {phase_timings['outline']['duration_seconds']:.1f}s")

    # Phase 2: Characters & Locations
    if "characters" in phases:
        print("\n" + "=" * 60)
        print("PHASE 2: CHARACTERS & LOCATIONS")
        print("=" * 60)
        phase_start = time.time()
        result = run_phase2_characters(codex_path, model=model, scope=scope)
        phase_timings["characters"] = {
            "duration_seconds": round(time.time() - phase_start, 2),
            "steps": getattr(result, "step_timings", {})
        }
        completed_phases.append("characters")
        total_characters = len(result.characters)
        total_locations = len(result.locations)
        print(f"\n>>> Characters: {total_characters}")
        print(f">>> Locations: {total_locations}")
        print(f">>> Phase 2 completed in {phase_timings['characters']['duration_seconds']:.1f}s")

    # Phase 3: Narrative Writing
    if "narrative" in phases:
        print("\n" + "=" * 60)
        print("PHASE 3: NARRATIVE WRITING")
        print("=" * 60)
        phase_start = time.time()
        result = run_phase3_narrative(codex_path, model=model)
        phase_timings["narrative"] = {
            "duration_seconds": round(time.time() - phase_start, 2),
            "steps": getattr(result, "step_timings", {})
        }
        completed_phases.append("narrative")
        total_scenes = result.total_scenes
        print(f"\n>>> Scenes written: {total_scenes}")
        print(f">>> Phase 3 completed in {phase_timings['narrative']['duration_seconds']:.1f}s")

    # Phase 3b: Storyboard Generation
    if "storyboard" in phases:
        print("\n" + "=" * 60)
        print("PHASE 3b: STORYBOARD GENERATION")
        print("=" * 60)
        phase_start = time.time()
        result = run_phase3b_storyboard(codex_path, model=model)
        phase_timings["storyboard"] = {
            "duration_seconds": round(time.time() - phase_start, 2),
            "steps": getattr(result, "step_timings", {})
        }
        completed_phases.append("storyboard")
        print(f"\n>>> Shots generated: {result.total_shots_generated}")
        print(f">>> Total duration: {result.total_duration_seconds}s")
        print(f">>> Phase 3b completed in {phase_timings['storyboard']['duration_seconds']:.1f}s")

    # Phase 4: Prompts (Character, Location, Scene, Video)
    if "prompts" in phases:
        print("\n" + "=" * 60)
        print("PHASE 4: PROMPT GENERATION")
        print("=" * 60)
        phase_start = time.time()
        result = run_phase4_prompts(codex_path, model=model)
        phase_timings["prompts"] = {
            "duration_seconds": round(time.time() - phase_start, 2),
            "steps": getattr(result, "step_timings", {})
        }
        completed_phases.append("prompts")
        print(f"\n>>> Character prompts: {result.character_prompt_count}")
        print(f">>> Location prompts: {result.location_prompt_count}")
        print(f">>> Poster prompts: {result.poster_prompt_count}")
        print(f">>> Scene image prompts: {result.scene_image_prompt_count}")
        print(f">>> Phase 4 completed in {phase_timings['prompts']['duration_seconds']:.1f}s")

    # Phase 5: Generation (ComfyUI audio/images)
    # Run Steps 1 (audio TTS), 2 (static images), 3 (scene images)
    if "generation" in phases:
        print("\n" + "=" * 60)
        print("PHASE 5: MEDIA GENERATION")
        print("=" * 60)
        phase_start = time.time()
        result = run_phase5_generation(codex_path, steps=[1, 2, 3])
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
        print(f">>> Phase 5 completed in {phase_timings['generation']['duration_seconds']:.1f}s")

    # Phase 6: Editing (combine audio hierarchically)
    # Steps: 1=sentence->scene, 2=scene videos, 3=final video
    if "editing" in phases:
        if should_run_step(4):
            print("\n" + "=" * 60)
            print("PHASE 6: AUDIO/VIDEO EDITING")
            print("=" * 60)
            phase_start = time.time()
            result = run_phase6_editing(codex_path, steps=[1, 2, 3])
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
                print(f">>> Phase 6 completed in {phase_timings['editing']['duration_seconds']:.1f}s")
            else:
                print(f"\n>>> Editing failed: {result.error}")
        else:
            print("\n>>> Phase 6 (editing) skipped by GENERATION_STEPS config")

    # Phase 7: YouTube Upload
    if "upload" in phases:
        print("\n" + "=" * 60)
        print("PHASE 7: YOUTUBE UPLOAD")
        print("=" * 60)
        phase_start = time.time()
        result = run_phase7_youtube(codex_path)
        phase_timings["upload"] = {
            "duration_seconds": round(time.time() - phase_start, 2),
            "steps": getattr(result, "step_timings", {})
        }
        completed_phases.append("upload")
        if result.success:
            print(f"\n>>> Video URL: {result.video_url}")
            print(f">>> Title: {result.title}")
            print(f">>> Phase 7 completed in {phase_timings['upload']['duration_seconds']:.1f}s")
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

  # Only generate codex and outline
  uv run python -m src.house_of_novels --phases codex outline

  # Resume from existing codex (add narrative and images)
  uv run python -m src.house_of_novels --codex forge/20260105143022/codex.json --phases narrative images

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

    args = parser.parse_args()

    try:
        forge_path = generate_novel(
            scope=args.scope,
            model=args.model,
            output_dir=args.output_dir,
            phases=args.phases,
            codex_path=args.codex,
            template=args.template,
        )
        print(f"\nNovel generated at: {forge_path}")
    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
