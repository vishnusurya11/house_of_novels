#!/usr/bin/env python3
"""
Phase 1: PLOTTING (Story Structure + Characters + Locations)

Generates story outline using author's preferred structure,
then creates characters and locations in the same phase.

This phase merges the old Phase 1 (outline) and Phase 2 (characters)
with author style injection.

Usage (standalone):
    uv run python -m src.phases.phase1_plotting forge/20260105143022/codex.json
    uv run python -m src.phases.phase1_plotting forge/20260105143022/codex.json --scope flash
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
    run_phase2_characters_locations as _run_characters_locations,
)
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
from src.authors import get_author
from src.authors.base_author import BaseAuthor
from src.authors.styles import PlottingStyle
from src.story_structures import get_structure
from src.story_structures.base_structure import BaseStructure


@dataclass
class Phase1Result:
    """Result of Phase 1 plotting generation."""
    codex_path: Path
    outline: dict
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


def extract_prompts(codex: dict) -> tuple[str, str]:
    """Extract story_prompt and setting_prompt from codex."""
    # story_engine and deck_of_worlds are at ROOT level
    se_prompts = codex.get("story_engine", {}).get("prompts", [])
    story_prompt = se_prompts[0].get("prompt", "") if se_prompts else ""

    dow_prompts = codex.get("deck_of_worlds", {}).get("prompts", [])
    setting_prompt = dow_prompts[0].get("prompt", "") if dow_prompts else ""

    return story_prompt, setting_prompt


def get_author_from_codex(codex: dict) -> tuple[Optional[BaseAuthor], PlottingStyle]:
    """Get author and plotting style from codex.

    Returns:
        Tuple of (author_instance_or_None, plotting_style)
    """
    # author is at ROOT level
    author_data = codex.get("author", {})
    if not author_data:
        # No author in codex, return default plotting style
        return None, PlottingStyle()

    author_id = author_data.get("id")
    if author_id:
        try:
            author = get_author(author_id)
            return author, author.plotting_style
        except ValueError:
            pass

    # Reconstruct plotting style from codex data
    plotting_data = author_data.get("plotting_style", {})
    plotting_style = PlottingStyle(
        beat_emphasis=plotting_data.get("beat_emphasis", []),
        pacing=plotting_data.get("pacing", "medium"),
        subplot_tendency=plotting_data.get("subplot_tendency", "minimal"),
        twist_frequency=plotting_data.get("twist_frequency", "one_major"),
    )
    return None, plotting_style


def get_structure_from_codex(codex: dict) -> BaseStructure:
    """Get story structure from codex."""
    # story_structure is at ROOT level
    structure_data = codex.get("story_structure", {})
    short_name = structure_data.get("short_name", "three_act")
    return get_structure(short_name)


def build_structure_prompt(structure: BaseStructure, plotting_style: PlottingStyle) -> str:
    """Build a combined prompt from structure and plotting style."""
    parts = []

    # Add structure prompt
    parts.append(structure.get_outline_prompt("standard"))

    # Add plotting style modifiers
    style_modifier = plotting_style.get_prompt_modifier()
    if style_modifier:
        parts.append("\n## Author's Plotting Style")
        parts.append(style_modifier)

    return "\n\n".join(parts)


def run_phase1_plotting(
    codex_path: Path,
    model: str = None,
    scope: str = None,
    steps: list[int] = None,
) -> Phase1Result:
    """
    Generate story outline with author's structure, then characters and locations.

    Steps:
    1. High-Level Story Structure - using author's preferred structure
    2. Beat Sheet Generation - beats from selected structure
    3. Scene-by-Scene Outline - scenes matching beats
    4. Structure & Pacing Critique
    5. Revision & Final Outline
    6. Character Generation
    7. Location Generation

    Args:
        codex_path: Path to codex.json file
        model: LLM model to use (default: from codex config or DEFAULT_MODEL)
        scope: Story scope (default: from codex config or DEFAULT_STORY_SCOPE)
        steps: List of step numbers to run (default: all steps [1-7])

    Returns:
        Phase1Result with outline, characters, and locations
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

    # Get author and structure from codex
    author, plotting_style = get_author_from_codex(codex)
    structure = get_structure_from_codex(codex)

    print(f"\n>>> Using model: {model}")
    print(f">>> Scope: {scope} - {scope_config['description']}")
    print(f">>> Story Structure: {structure.name}")
    print(f">>> Pacing: {plotting_style.pacing}")
    if author:
        print(f">>> Author: {author.name}")

    # Build combined structure prompt
    structure_prompt = build_structure_prompt(structure, plotting_style)

    # Determine which steps to run
    steps_to_run = steps if steps is not None else [1, 2, 3, 4, 5, 6, 7]
    print(f">>> Running steps: {steps_to_run}")

    # Initialize story structure if needed
    if "story" not in codex:
        codex["story"] = {}
    if "outline" not in codex["story"]:
        codex["story"]["outline"] = {}

    # Initialize metadata in new structure
    if "metadata" not in codex:
        codex["metadata"] = {}
    if "phase_1" not in codex["metadata"]:
        codex["metadata"]["phase_1"] = {
            "phase": 1,
            "name": "Plotting (Structure + Characters)",
            "mode": "author-driven",
            "structure_used": structure.short_name,
            "steps_completed": [],
        }

    # Initialize agents as needed
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

    step_timings = {}

    # STEP 1: High-Level Story Structure
    if 1 in steps_to_run:
        print(f"\n{'='*60}")
        print("STEP 1: High-Level Story Structure (Author's Structure)")
        print(f"{'='*60}")
        step_start = time.time()

        print(f">>> Using {structure.name} structure...")
        print(">>> Researching story structures...")

        # Inject structure prompt into research
        research_insights = structure_agent.research_story_structures(
            story_prompt + "\n\n" + structure_prompt,
            setting_prompt
        )
        print(f"    Found {len(research_insights)} relevant structures")

        print("\n>>> Creating high-level structure...")
        high_level_structure = structure_agent.create_high_level_structure(
            story_prompt + "\n\n" + structure_prompt,
            setting_prompt,
            research_insights
        )

        # Store in codex
        codex["story"]["outline"]["high_level_structure"] = high_level_structure.model_dump()
        codex["metadata"]["phase_1"]["research_insights"] = [
            r.model_dump() for r in research_insights
        ]
        codex["metadata"]["phase_1"]["steps_completed"].append(1)

        step_timings["step1_structure"] = round(time.time() - step_start, 2)
        save_codex(codex, codex_path)
        print(f">>> Step 1 complete ({step_timings['step1_structure']:.1f}s)")
        print(f"    Theme: {high_level_structure.theme}")

    # STEP 2: Beat Sheet Generation
    if 2 in steps_to_run:
        print(f"\n{'='*60}")
        print("STEP 2: Beat Sheet Generation")
        print(f"{'='*60}")
        step_start = time.time()

        codex = load_codex(codex_path)
        hl_struct_dict = codex.get("story", {}).get("outline", {}).get("high_level_structure")

        if not hl_struct_dict:
            print("ERROR: No high-level structure found. Run step 1 first.")
        else:
            from src.story_schemas import HighLevelStructureSchema
            hl_struct = HighLevelStructureSchema(**hl_struct_dict)

            # Include structure beats in prompt
            beat_definitions = structure.get_beat_definitions()
            print(f">>> Using {len(structure.beats)} beats from {structure.name}...")

            beat_sheet = beat_agent.generate_beat_sheet(
                story_prompt + "\n\n" + beat_definitions,
                setting_prompt,
                hl_struct,
                scope_config
            )

            codex["story"]["outline"]["beat_sheet"] = beat_sheet.model_dump()
            codex["metadata"]["phase_1"]["steps_completed"].append(2)

            step_timings["step2_beats"] = round(time.time() - step_start, 2)
            save_codex(codex, codex_path)
            print(f">>> Step 2 complete ({step_timings['step2_beats']:.1f}s)")
            print(f"    Act 1 beats: {len(beat_sheet.act1_beats)}")
            print(f"    Act 2 beats: {len(beat_sheet.act2_beats)}")
            print(f"    Act 3 beats: {len(beat_sheet.act3_beats)}")

    # STEP 3: Scene-by-Scene Outline
    if 3 in steps_to_run:
        print(f"\n{'='*60}")
        print("STEP 3: Scene-by-Scene Outline Generation")
        print(f"{'='*60}")
        step_start = time.time()

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

            acts = []

            print(">>> Building Act 1 scenes...")
            act1 = scene_builder.build_act_scenes(
                1, beat_sheet.act1_beats, hl_struct, setting_prompt
            )
            acts.append(act1)
            print(f"    Act 1: {len(act1.scenes)} scenes")

            print(">>> Building Act 2 scenes...")
            act2 = scene_builder.build_act_scenes(
                2, beat_sheet.act2_beats, hl_struct, setting_prompt
            )
            acts.append(act2)
            print(f"    Act 2: {len(act2.scenes)} scenes")

            print(">>> Building Act 3 scenes...")
            act3 = scene_builder.build_act_scenes(
                3, beat_sheet.act3_beats, hl_struct, setting_prompt
            )
            acts.append(act3)
            print(f"    Act 3: {len(act3.scenes)} scenes")

            # Create complete outline
            outline_data = {
                "title": f"Story based on: {story_prompt[:50]}...",
                "logline": hl_struct.three_act_summary[:200],
                "protagonist": hl_struct.protagonist_arc.split(".")[0],
                "antagonist": hl_struct.antagonist_arc.split(".")[0],
                "central_conflict": hl_struct.central_conflict,
                "acts": [act.model_dump() for act in acts]
            }

            codex["story"]["outline"].update(outline_data)
            codex["metadata"]["phase_1"]["steps_completed"].append(3)

            step_timings["step3_scenes"] = round(time.time() - step_start, 2)
            save_codex(codex, codex_path)
            total_scenes = sum(len(act.scenes) for act in acts)
            print(f">>> Step 3 complete: {total_scenes} scenes ({step_timings['step3_scenes']:.1f}s)")

    # STEP 4: Structure & Pacing Critique
    if 4 in steps_to_run:
        print(f"\n{'='*60}")
        print("STEP 4: Structure & Pacing Critique")
        print(f"{'='*60}")
        step_start = time.time()

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

            critique_data = {
                "structure_critique": structure_critique.model_dump(),
                "pacing_critique": pacing_critique.model_dump(),
            }
            codex["metadata"]["phase_1"]["critiques"] = critique_data
            codex["metadata"]["phase_1"]["steps_completed"].append(4)

            step_timings["step4_critique"] = round(time.time() - step_start, 2)
            save_codex(codex, codex_path)
            print(f">>> Step 4 complete ({step_timings['step4_critique']:.1f}s)")
            print(f"    Structure issues: {len(structure_critique.issues)}")
            print(f"    Pacing issues: {len(pacing_critique.issues)}")

    # STEP 5: Revision & Final Outline
    if 5 in steps_to_run:
        print(f"\n{'='*60}")
        print("STEP 5: Revision & Final Outline")
        print(f"{'='*60}")
        step_start = time.time()

        codex = load_codex(codex_path)
        critiques = codex.get("metadata", {}).get("phase_1", {}).get("critiques")
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

            print(">>> Revising outline...")
            revised_outline = reviser.revise_outline(outline_json, critique_jsons)

            codex["story"]["outline"].update(revised_outline.model_dump())
            codex["metadata"]["phase_1"]["steps_completed"].append(5)

            step_timings["step5_revision"] = round(time.time() - step_start, 2)
            save_codex(codex, codex_path)
            print(f">>> Step 5 complete ({step_timings['step5_revision']:.1f}s)")

    # STEP 6: Character Generation
    if 6 in steps_to_run:
        print(f"\n{'='*60}")
        print("STEP 6: Character Generation")
        print(f"{'='*60}")
        step_start = time.time()

        codex = load_codex(codex_path)
        story = codex.get("story", {})

        if "outline" not in story:
            print("ERROR: No outline found. Run steps 1-5 first.")
        else:
            outline_json = json.dumps(story["outline"])

            print(f">>> Generating up to {scope_config['max_characters']} characters...")

            result = _run_characters_locations(
                outline_json,
                setting_prompt,
                model,
                max_characters=scope_config["max_characters"],
                max_locations=scope_config["max_locations"]
            )

            codex["story"]["characters"] = result["characters"]

            # Assign unique IDs
            for i, char in enumerate(codex["story"]["characters"]):
                char["id"] = f"char_{i+1:03d}"

            # Update outline with debated names if available
            if "outline_updated" in result and result["outline_updated"]:
                codex["story"]["outline"] = result["outline_updated"]
                print("    Updated outline with debated names.")

            codex["metadata"]["phase_1"]["steps_completed"].append(6)
            codex["metadata"]["phase_1"]["character_metadata"] = result.get("metadata", {})

            step_timings["step6_characters"] = round(time.time() - step_start, 2)
            save_codex(codex, codex_path)
            print(f">>> Step 6 complete: {len(result['characters'])} characters ({step_timings['step6_characters']:.1f}s)")

    # STEP 7: Location Generation
    if 7 in steps_to_run:
        print(f"\n{'='*60}")
        print("STEP 7: Location Generation")
        print(f"{'='*60}")
        step_start = time.time()

        codex = load_codex(codex_path)
        story = codex.get("story", {})

        if "characters" not in story:
            print("ERROR: No characters found. Run step 6 first.")
        else:
            # Locations were already generated in step 6, just assign IDs if needed
            if "locations" in story:
                for i, loc in enumerate(codex["story"]["locations"]):
                    if "id" not in loc:
                        loc["id"] = f"loc_{i+1:03d}"

                codex["metadata"]["phase_1"]["steps_completed"].append(7)
                step_timings["step7_locations"] = round(time.time() - step_start, 2)
                save_codex(codex, codex_path)
                print(f">>> Step 7 complete: {len(story['locations'])} locations ({step_timings['step7_locations']:.1f}s)")
            else:
                print("    Locations were generated with characters in step 6.")
                codex["metadata"]["phase_1"]["steps_completed"].append(7)
                step_timings["step7_locations"] = round(time.time() - step_start, 2)
                save_codex(codex, codex_path)

    # Update config
    codex = load_codex(codex_path)
    codex["config"]["model"] = model
    codex["config"]["scope"] = scope
    save_codex(codex, codex_path)

    # Get final data
    final_outline = codex.get("story", {}).get("outline", {})
    final_characters = codex.get("story", {}).get("characters", [])
    final_locations = codex.get("story", {}).get("locations", [])
    final_metadata = codex.get("metadata", {}).get("phase_1", {})

    print(f"\n>>> Plotting saved to: {codex_path}")

    return Phase1Result(
        codex_path=codex_path,
        outline=final_outline,
        characters=final_characters,
        locations=final_locations,
        metadata=final_metadata,
        success=True,
        step_timings=step_timings,
    )


def main():
    """CLI entry point for standalone execution."""
    parser = argparse.ArgumentParser(
        description="Phase 1: Plotting (Structure + Characters + Locations)"
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
        choices=[1, 2, 3, 4, 5, 6, 7],
        help="Run specific steps. Example: --steps 1 2 3"
    )
    args = parser.parse_args()

    if not args.codex_path.exists():
        print(f"ERROR: Codex not found: {args.codex_path}")
        sys.exit(1)

    result = run_phase1_plotting(
        args.codex_path,
        model=args.model,
        scope=args.scope,
        steps=args.steps,
    )

    print(f"\n>>> Title: {result.outline.get('title', 'Untitled')}")
    print(f">>> Characters: {len(result.characters)}")
    print(f">>> Locations: {len(result.locations)}")


if __name__ == "__main__":
    main()
