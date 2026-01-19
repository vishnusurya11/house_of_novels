#!/usr/bin/env python3
"""
Phase 1: Story Outline Generation

Creates 3-act story structure with hero's journey beats and try-fail cycles.
Requires a codex file from Phase 0.

Usage (standalone):
    uv run python -m src.phases.phase1_outline forge/20260105143022/codex.json
    uv run python -m src.phases.phase1_outline forge/20260105143022/codex.json --scope flash
"""

import sys
import json
import time
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Any

# Add parent directory to path for proper package imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.story_workflows import run_phase1_outline as _run_phase1_outline_monolithic
from src.story_agents.outline_research_agents import (
    StructureResearchAgent,
    BeatSheetAgent,
    SceneBuilderAgent,
)
from src.story_agents.outline_agents import (
    StructureCriticAgent,
    PacingCriticAgent,
)
from src.story_agents.reviser_agent import ReviserAgent
from src.config import DEFAULT_MODEL, STORY_SCOPES, DEFAULT_STORY_SCOPE


@dataclass
class Phase1Result:
    """Result of Phase 1 outline generation."""
    codex_path: Path
    outline: dict
    outline_json: str
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


def extract_prompts(codex: dict) -> tuple[str, str]:
    """Extract story_prompt and setting_prompt from codex."""
    se_prompts = codex.get("story_engine", {}).get("prompts", [])
    story_prompt = se_prompts[0].get("prompt", "") if se_prompts else ""

    dow_prompts = codex.get("deck_of_worlds", {}).get("prompts", [])
    setting_prompt = dow_prompts[0].get("prompt", "") if dow_prompts else ""

    return story_prompt, setting_prompt


def run_phase1_outline(
    codex_path: Path,
    model: str = None,
    scope: str = None,
    steps: list[int] = None,
) -> Phase1Result:
    """
    Generate story outline from codex with step-granular execution.

    Step 1: High-Level Story Structure - research-driven 3-act summary
    Step 2: Beat Sheet Generation - bullet points for each act
    Step 3: Scene-by-Scene Outline - full scenes from beats
    Step 4: Structure & Pacing Critique - multi-agent critique
    Step 5: Revision & Final Outline - apply critiques and revise

    Args:
        codex_path: Path to codex.json file
        model: LLM model to use (default: from codex config or DEFAULT_MODEL)
        scope: Story scope (default: from codex config or DEFAULT_STORY_SCOPE)
        steps: List of step numbers to run (default: all steps [1,2,3,4,5])

    Returns:
        Phase1Result with outline data
    """
    codex_path = Path(codex_path)
    codex = load_codex(codex_path)

    # Use codex config as defaults, allow override
    codex_config = codex.get("config", {})
    model = model or codex_config.get("model", DEFAULT_MODEL)
    scope = scope or codex_config.get("scope", DEFAULT_STORY_SCOPE)

    # Validate prompts exist
    story_prompt, setting_prompt = extract_prompts(codex)
    if not story_prompt:
        raise ValueError("Codex missing story_engine prompts. Run Phase 0 first.")

    scope_config = STORY_SCOPES.get(scope, STORY_SCOPES[DEFAULT_STORY_SCOPE])

    print(f"\n>>> Using model: {model}")
    print(f">>> Scope: {scope} - {scope_config['description']}")

    # Determine which steps to run
    steps_to_run = steps if steps is not None else [1, 2, 3, 4, 5]
    print(f">>> Running steps: {steps_to_run}")

    # Initialize story structure if needed
    if "story" not in codex:
        codex["story"] = {}
    if "outline" not in codex["story"]:
        codex["story"]["outline"] = {}

    # Initialize metadata
    if "story_metadata" not in codex:
        codex["story_metadata"] = {}
    if "phase1_outline" not in codex["story_metadata"]:
        codex["story_metadata"]["phase1_outline"] = {
            "phase": 1,
            "name": "Outline Generation",
            "mode": "research-driven",
            "steps_completed": [],
        }

    # Initialize agents (only create if needed for requested steps)
    structure_agent = None
    beat_agent = None
    scene_builder = None
    structure_critic = None
    pacing_critic = None
    reviser = None

    if 1 in steps_to_run:
        structure_agent = StructureResearchAgent(model=model)
    if 2 in steps_to_run:
        beat_agent = BeatSheetAgent(model=model)
    if 3 in steps_to_run:
        scene_builder = SceneBuilderAgent(model=model)
    if 4 in steps_to_run or 5 in steps_to_run:
        structure_critic = StructureCriticAgent(model=model)
        pacing_critic = PacingCriticAgent(model=model)
    if 5 in steps_to_run:
        reviser = ReviserAgent(model=model)

    # Step timing tracking
    step_timings = {}

    # STEP 1: High-Level Story Structure
    if 1 in steps_to_run:
        print(f"\n{'='*60}")
        print("STEP 1: High-Level Story Structure (Research-Driven)")
        print(f"{'='*60}")
        step_start = time.time()

        print(">>> Researching story structures...")
        research_insights = structure_agent.research_story_structures(
            story_prompt, setting_prompt
        )
        print(f"    Found {len(research_insights)} relevant structures")
        for insight in research_insights:
            print(f"    - {insight.topic}")

        print("\n>>> Creating high-level 3-act structure...")
        high_level_structure = structure_agent.create_high_level_structure(
            story_prompt, setting_prompt, research_insights
        )

        # Store in codex
        codex["story"]["outline"]["high_level_structure"] = high_level_structure.model_dump()
        codex["story_metadata"]["phase1_outline"]["research_insights"] = [
            r.model_dump() for r in research_insights
        ]
        codex["story_metadata"]["phase1_outline"]["steps_completed"].append(1)

        step_timings["step1_structure"] = round(time.time() - step_start, 2)
        save_codex(codex, codex_path)
        print(f">>> Step 1 complete: High-level structure saved ({step_timings['step1_structure']:.1f}s)")
        print(f"    Theme: {high_level_structure.theme}")
        print(f"    Central Conflict: {high_level_structure.central_conflict[:80]}...")

    # STEP 2: Beat Sheet Generation
    if 2 in steps_to_run:
        print(f"\n{'='*60}")
        print("STEP 2: Beat Sheet Generation")
        print(f"{'='*60}")
        step_start = time.time()

        # Load high-level structure from codex
        codex = load_codex(codex_path)
        hl_struct_dict = codex.get("story", {}).get("outline", {}).get("high_level_structure")

        if not hl_struct_dict:
            print("ERROR: No high-level structure found. Run step 1 first.")
        else:
            from src.story_schemas import HighLevelStructureSchema
            hl_struct = HighLevelStructureSchema(**hl_struct_dict)

            print(">>> Generating beat sheet with research...")
            beat_sheet = beat_agent.generate_beat_sheet(
                story_prompt, setting_prompt, hl_struct, scope_config
            )

            # Store in codex
            codex["story"]["outline"]["beat_sheet"] = beat_sheet.model_dump()
            codex["story_metadata"]["phase1_outline"]["steps_completed"].append(2)

            step_timings["step2_beats"] = round(time.time() - step_start, 2)
            save_codex(codex, codex_path)
            print(f">>> Step 2 complete: Beat sheet saved ({step_timings['step2_beats']:.1f}s)")
            print(f"    Act 1 beats: {len(beat_sheet.act1_beats)}")
            print(f"    Act 2 beats: {len(beat_sheet.act2_beats)}")
            print(f"    Act 3 beats: {len(beat_sheet.act3_beats)}")

    # STEP 3: Scene-by-Scene Outline
    if 3 in steps_to_run:
        print(f"\n{'='*60}")
        print("STEP 3: Scene-by-Scene Outline Generation")
        print(f"{'='*60}")
        step_start = time.time()

        # Load beat sheet and high-level structure from codex
        codex = load_codex(codex_path)
        beat_sheet_dict = codex.get("story", {}).get("outline", {}).get("beat_sheet")
        hl_struct_dict = codex.get("story", {}).get("outline", {}).get("high_level_structure")

        if not beat_sheet_dict:
            print("ERROR: No beat sheet found. Run step 2 first.")
        elif not hl_struct_dict:
            print("ERROR: No high-level structure found. Run step 1 first.")
        else:
            from src.story_schemas import BeatSheetSchema, HighLevelStructureSchema
            beat_sheet = BeatSheetSchema(**beat_sheet_dict)
            hl_struct = HighLevelStructureSchema(**hl_struct_dict)

            # Build acts sequentially
            acts = []

            print(">>> Building Act 1 scenes from beats...")
            act1 = scene_builder.build_act_scenes(
                1, beat_sheet.act1_beats, hl_struct, setting_prompt
            )
            acts.append(act1)
            print(f"    Act 1: {len(act1.scenes)} scenes")

            print(">>> Building Act 2 scenes from beats...")
            act2 = scene_builder.build_act_scenes(
                2, beat_sheet.act2_beats, hl_struct, setting_prompt
            )
            acts.append(act2)
            print(f"    Act 2: {len(act2.scenes)} scenes")

            print(">>> Building Act 3 scenes from beats...")
            act3 = scene_builder.build_act_scenes(
                3, beat_sheet.act3_beats, hl_struct, setting_prompt
            )
            acts.append(act3)
            print(f"    Act 3: {len(act3.scenes)} scenes")

            # Validate all acts have scenes
            for i, act in enumerate(acts):
                if not act.scenes:
                    raise ValueError(f"Act {i+1} has 0 scenes - beat sheet may have empty act{i+1}_beats")

            # Create complete outline
            outline_data = {
                "title": f"Story based on: {story_prompt[:50]}...",
                "logline": hl_struct.three_act_summary[:200],
                "protagonist": hl_struct.protagonist_arc.split(".")[0],
                "antagonist": hl_struct.antagonist_arc.split(".")[0],
                "central_conflict": hl_struct.central_conflict,
                "acts": [act.model_dump() for act in acts]
            }

            # Store in codex
            codex["story"]["outline"].update(outline_data)
            codex["story_metadata"]["phase1_outline"]["steps_completed"].append(3)

            step_timings["step3_scenes"] = round(time.time() - step_start, 2)
            save_codex(codex, codex_path)
            total_scenes = sum(len(act.scenes) for act in acts)
            print(f">>> Step 3 complete: {total_scenes} scenes generated ({step_timings['step3_scenes']:.1f}s)")

    # STEP 4: Structure & Pacing Critique
    if 4 in steps_to_run:
        print(f"\n{'='*60}")
        print("STEP 4: Structure & Pacing Critique")
        print(f"{'='*60}")
        step_start = time.time()

        # Load complete outline from codex
        codex = load_codex(codex_path)
        outline = codex.get("story", {}).get("outline", {})

        if "acts" not in outline or not outline["acts"]:
            print("ERROR: No complete outline found. Run step 3 first.")
        else:
            outline_json = json.dumps(outline)

            print(">>> Getting structure critique...")
            structure_critique = structure_critic.critique(outline_json)

            print(">>> Getting pacing critique...")
            pacing_critique = pacing_critic.critique(outline_json)

            # Store critiques in metadata
            critique_data = {
                "structure_critique": structure_critique.model_dump(),
                "pacing_critique": pacing_critique.model_dump(),
            }
            codex["story_metadata"]["phase1_outline"]["critiques"] = critique_data
            codex["story_metadata"]["phase1_outline"]["steps_completed"].append(4)

            step_timings["step4_critique"] = round(time.time() - step_start, 2)
            save_codex(codex, codex_path)
            print(f">>> Step 4 complete: Critiques saved ({step_timings['step4_critique']:.1f}s)")
            print(f"    Structure issues: {len(structure_critique.issues)}")
            print(f"    Pacing issues: {len(pacing_critique.issues)}")

    # STEP 5: Revision & Final Outline
    if 5 in steps_to_run:
        print(f"\n{'='*60}")
        print("STEP 5: Revision & Final Outline")
        print(f"{'='*60}")
        step_start = time.time()

        # Load critiques and outline from codex
        codex = load_codex(codex_path)
        critiques = codex.get("story_metadata", {}).get("phase1_outline", {}).get("critiques")
        outline = codex.get("story", {}).get("outline", {})

        if not critiques:
            print("ERROR: No critiques found. Run step 4 first.")
        elif "acts" not in outline:
            print("ERROR: No complete outline found. Run step 3 first.")
        else:
            outline_json = json.dumps(outline)
            critique_jsons = [
                json.dumps(critiques["structure_critique"]),
                json.dumps(critiques["pacing_critique"])
            ]

            print(">>> Revising outline based on critiques...")
            revised_outline = reviser.revise_outline(outline_json, critique_jsons)

            # Store revised outline
            codex["story"]["outline"].update(revised_outline.model_dump())
            codex["story_metadata"]["phase1_outline"]["steps_completed"].append(5)

            step_timings["step5_revision"] = round(time.time() - step_start, 2)
            save_codex(codex, codex_path)
            print(f">>> Step 5 complete: Final outline saved ({step_timings['step5_revision']:.1f}s)")

    # Update config
    codex = load_codex(codex_path)
    codex["config"]["model"] = model
    codex["config"]["scope"] = scope
    save_codex(codex, codex_path)

    # Get final outline
    final_outline = codex.get("story", {}).get("outline", {})
    final_metadata = codex.get("story_metadata", {}).get("phase1_outline", {})

    print(f"\n>>> Outline saved to: {codex_path}")

    return Phase1Result(
        codex_path=codex_path,
        outline=final_outline,
        outline_json=json.dumps(final_outline, indent=2, ensure_ascii=False),
        metadata=final_metadata,
        success=True,
        step_timings=step_timings,
    )


def main():
    """CLI entry point for standalone execution."""
    parser = argparse.ArgumentParser(
        description="Phase 1: Generate story outline (research-driven)"
    )
    parser.add_argument(
        "codex_path",
        type=Path,
        help="Path to codex.json"
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
        help="Story scope: flash, short, standard, long (default: from codex)"
    )
    parser.add_argument(
        "--steps",
        nargs="+",
        type=int,
        choices=[1, 2, 3, 4, 5],
        help="Run specific steps (1: Structure, 2: Beats, 3: Scenes, 4: Critique, 5: Revision). Example: --steps 1 2"
    )
    args = parser.parse_args()

    if not args.codex_path.exists():
        print(f"ERROR: Codex not found: {args.codex_path}")
        sys.exit(1)

    result = run_phase1_outline(
        args.codex_path,
        model=args.model,
        scope=args.scope,
        steps=args.steps,
    )

    print(f"\n>>> Title: {result.outline.get('title', 'Untitled')}")
    print(f">>> Logline: {result.outline.get('logline', 'N/A')[:100]}...")


if __name__ == "__main__":
    main()
