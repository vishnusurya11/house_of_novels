"""
Story Builder Workflows - 3 Phase pipeline with critique-revision cycles.

Each phase follows the pattern:
  [CREATOR] → draft_v1
  [CRITIC_1 + CRITIC_2] → critiques_v1
  [REVISER] → draft_v2
  [CRITIC_1 + CRITIC_2] → critiques_v2
  [REVISER] → final
"""

import json
import re
from typing import Any, Dict, List

from src.story_agents.outline_agents import (
    OutlinerAgent,
    StructureCriticAgent,
    PacingCriticAgent,
)
from src.story_agents.character_agents import (
    CharacterBuilderAgent,
    LocationBuilderAgent,
    ConsistencyCriticAgent,
)
from src.story_agents.narrative_agents import (
    WriterAgent,
    StyleCriticAgent,
    ContinuityCriticAgent,
)
from src.story_agents.reviser_agent import ReviserAgent
from src.story_agents.name_agents import generate_character_names_via_debate
from src.config import DEFAULT_MODEL, STORY_SCOPES, DEFAULT_STORY_SCOPE


CRITIQUE_CYCLES = 2  # Number of critique-revision cycles per phase


# =============================================================================
# Name Substitution Utilities
# =============================================================================

def substitute_names_in_text(text: str, mapping: Dict[str, str]) -> str:
    """
    Replace all occurrences of old names with new names using word boundaries.

    Names are sorted by length (descending) to prevent partial replacements
    (e.g., "Ann" won't replace part of "Annabelle").
    """
    if not text or not mapping:
        return text

    result = text
    # Sort by length descending to replace longer names first
    for old_name in sorted(mapping.keys(), key=len, reverse=True):
        if not old_name:
            continue
        new_name = mapping[old_name]
        # Single pattern with word boundaries
        pattern = r'\b' + re.escape(old_name) + r'\b'
        result = re.sub(pattern, new_name, result)
    return result


def substitute_names_in_outline(outline: dict, mapping: Dict[str, str]) -> dict:
    """Replace names in outline structure."""
    if not outline or not mapping:
        return outline

    # Update protagonist/antagonist
    if outline.get("protagonist"):
        outline["protagonist"] = substitute_names_in_text(outline["protagonist"], mapping)
    if outline.get("antagonist"):
        outline["antagonist"] = substitute_names_in_text(outline["antagonist"], mapping)

    # Update scene character lists and text
    for act in outline.get("acts", []):
        for scene in act.get("scenes", []):
            # Update character list
            if scene.get("characters"):
                scene["characters"] = [
                    mapping.get(char, char) for char in scene["characters"]
                ]
            # Update "happens" text
            if scene.get("happens"):
                scene["happens"] = substitute_names_in_text(scene["happens"], mapping)

    return outline


def substitute_names_in_characters(characters: List[dict], mapping: Dict[str, str]) -> List[dict]:
    """Replace names in character profiles."""
    if not characters or not mapping:
        return characters

    for char in characters:
        old_name = char.get("name", "")
        # Check if any part of the name should be replaced
        for old, new in mapping.items():
            if old and old.lower() in old_name.lower():
                char["name"] = substitute_names_in_text(old_name, mapping)
                break
        # Update text fields that may contain character names
        for field in ["backstory", "motivation", "arc", "description", "personality"]:
            if char.get(field):
                char[field] = substitute_names_in_text(char[field], mapping)
    return characters


def substitute_names_in_narrative(narrative: dict, mapping: Dict[str, str]) -> dict:
    """Replace names in narrative text."""
    if not narrative or not mapping:
        return narrative

    # Handle raw JSON string format (when parse_error occurred)
    if narrative.get("raw"):
        narrative["raw"] = substitute_names_in_text(narrative["raw"], mapping)

    # Handle parsed acts format
    for act in narrative.get("acts", []):
        for scene in act.get("scenes", []):
            # Update character list
            if scene.get("characters"):
                scene["characters"] = [
                    mapping.get(char, char) for char in scene["characters"]
                ]
            # Update narrative text
            if scene.get("text"):
                scene["text"] = substitute_names_in_text(scene["text"], mapping)
            # Update sentences list
            if scene.get("sentences"):
                scene["sentences"] = [
                    substitute_names_in_text(s, mapping) for s in scene["sentences"]
                ]
    return narrative


def apply_name_substitutions(codex: dict, mapping: Dict[str, str] = None) -> dict:
    """
    Apply name substitutions across entire codex.

    Call this AFTER name debate but BEFORE character building,
    or as a repair step for existing codex.

    Args:
        codex: Full codex dictionary
        mapping: Optional direct mapping of old_name -> new_name.
                 If not provided, uses stored name_mapping from codex.

    Returns:
        Updated codex with names replaced
    """
    # Use provided mapping or get from codex
    if mapping is None:
        mapping = codex.get("story", {}).get("name_mapping", {})

    if not mapping:
        # Try to build mapping from names list (fallback for older codexes)
        names = codex.get("story", {}).get("names", [])
        if names:
            # Build mapping from the old_name field if present
            mapping = {}
            for name_entry in names:
                old_name = name_entry.get("old_name")
                final_name = name_entry.get("final_name")
                if old_name and final_name and old_name != final_name:
                    mapping[old_name] = final_name

    if not mapping:
        return codex

    print(f"\n>>> Name substitution mapping:")
    for old, new in mapping.items():
        print(f"    '{old}' -> '{new}'")

    # Store mapping for reference
    if "story" not in codex:
        codex["story"] = {}
    codex["story"]["name_mapping"] = mapping

    # Apply to outline
    if codex.get("story", {}).get("outline"):
        codex["story"]["outline"] = substitute_names_in_outline(
            codex["story"]["outline"], mapping
        )

    # Apply to characters
    if codex.get("story", {}).get("characters"):
        codex["story"]["characters"] = substitute_names_in_characters(
            codex["story"]["characters"], mapping
        )

    # Apply to narrative
    if codex.get("story", {}).get("narrative"):
        codex["story"]["narrative"] = substitute_names_in_narrative(
            codex["story"]["narrative"], mapping
        )

    return codex

# Abbreviations that should NOT trigger sentence splits
ABBREVIATIONS = r"(?:Mr|Mrs|Ms|Dr|Jr|Sr|St|Prof|Rev|Gen|Col|Lt|Capt|Sgt|Mt|vs|etc|Inc|Ltd|Corp|Co|Ave|Blvd|Rd|i\.e|e\.g)"


def split_into_sentences(text: str) -> list[str]:
    """
    Split text into sentences, preserving abbreviations.
    Removes newline characters and splits on sentence-ending periods.
    """
    # Remove newlines
    clean_text = text.replace("\n", " ")

    # Normalize multiple spaces
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()

    # Replace abbreviation periods with placeholder
    protected = re.sub(
        rf'\b({ABBREVIATIONS})\.',
        r'\1<ABBR>',
        clean_text,
        flags=re.IGNORECASE
    )

    # Split on sentence-ending punctuation (. ! ?)
    sentences = re.split(r'(?<=[.!?])\s+', protected)

    # Restore abbreviation periods and clean up
    sentences = [s.replace('<ABBR>', '.').strip() for s in sentences if s.strip()]

    return sentences


def run_phase1_outline(story_prompt: str, setting_prompt: str,
                       model: str = DEFAULT_MODEL,
                       scope_config: dict = None) -> dict[str, Any]:
    """
    Phase 1: Generate story outline with structure/pacing critique.

    Args:
        story_prompt: Story Engine prompt
        setting_prompt: Deck of Worlds microsetting
        model: LLM model to use
        scope_config: Story scope configuration (scene count, character limits)

    Returns:
        Dict with final outline and phase metadata
    """
    if scope_config is None:
        scope_config = STORY_SCOPES[DEFAULT_STORY_SCOPE]

    print("\n" + "=" * 50)
    print(f"PHASE 1: STORY OUTLINE ({scope_config['description']})")
    print("=" * 50)

    # Initialize agents
    outliner = OutlinerAgent(model=model)
    structure_critic = StructureCriticAgent(model=model)
    pacing_critic = PacingCriticAgent(model=model)
    reviser = ReviserAgent(model=model)

    phase_metadata = {
        "phase": 1,
        "name": "Story Outline",
        "scope": scope_config["description"],
        "cycles": [],
    }

    # Create initial outline with scope constraints
    print("\n>>> Creating initial outline...")
    outline_schema = outliner.create_outline(story_prompt, setting_prompt, scope_config)
    current_outline_json = json.dumps(outline_schema.model_dump(), indent=2)
    print("    Initial outline created.")

    # Critique-revision cycles
    for cycle in range(CRITIQUE_CYCLES):
        print(f"\n>>> Critique-Revision Cycle {cycle + 1}/{CRITIQUE_CYCLES}")
        cycle_data = {"cycle": cycle + 1, "critiques": [], "revision_applied": True}

        # Get critiques (now returns CritiqueSchema objects)
        print("    Getting structure critique...")
        structure_critique = structure_critic.critique(current_outline_json)
        cycle_data["critiques"].append(structure_critique.model_dump())

        print("    Getting pacing critique...")
        pacing_critique = pacing_critic.critique(current_outline_json)
        cycle_data["critiques"].append(pacing_critique.model_dump())

        # Revise based on critiques (now returns OutlineSchema)
        print("    Revising outline...")
        revised_outline = reviser.revise_outline(
            current_outline_json,
            [json.dumps(structure_critique.model_dump()), json.dumps(pacing_critique.model_dump())]
        )
        current_outline_json = json.dumps(revised_outline.model_dump(), indent=2)
        print("    Revision complete.")

        phase_metadata["cycles"].append(cycle_data)

    # Final outline is already a dict from the last revision
    final_outline = json.loads(current_outline_json)

    phase_metadata["final_outline"] = final_outline

    print("\n>>> Phase 1 complete.")
    return {
        "outline": final_outline,
        "outline_json": current_outline_json,
        "metadata": phase_metadata,
    }


def run_phase2_characters_locations(outline_json: str, setting_prompt: str,
                                     model: str = DEFAULT_MODEL,
                                     max_characters: int = 8,
                                     max_locations: int = 6) -> dict[str, Any]:
    """
    Phase 2: Build character and location profiles.

    Args:
        outline_json: Story outline JSON from Phase 1
        setting_prompt: Deck of Worlds microsetting
        model: LLM model to use
        max_characters: Maximum number of character profiles to create
        max_locations: Maximum number of location profiles to create

    Returns:
        Dict with characters, locations, names, and phase metadata
    """
    print("\n" + "=" * 50)
    print(f"PHASE 2: CHARACTERS & LOCATIONS (max {max_characters} chars, {max_locations} locs)")
    print("=" * 50)

    # Initialize agents
    character_builder = CharacterBuilderAgent(model=model)
    location_builder = LocationBuilderAgent(model=model)
    consistency_critic = ConsistencyCriticAgent(model=model)
    reviser = ReviserAgent(model=model)

    phase_metadata = {
        "phase": 2,
        "name": "Characters & Locations",
        "max_characters": max_characters,
        "max_locations": max_locations,
        "cycles": [],
    }

    # NEW: Generate character names via multi-agent debate
    # Returns names list, debate metadata, AND direct name mapping
    print("\n>>> PHASE 2a: Name Generation via Debate")
    print("-" * 40)
    names, name_debates, name_mapping = generate_character_names_via_debate(
        outline_json=outline_json,
        setting_prompt=setting_prompt,
        model=model,
        max_characters=max_characters,
    )
    phase_metadata["name_debates"] = name_debates

    # Apply name substitutions to outline BEFORE character building
    print("\n>>> PHASE 2a.1: Applying Name Substitutions to Outline")
    print("-" * 40)
    try:
        outline_dict = json.loads(outline_json)
        if name_mapping:
            print(f"    Name mapping: {name_mapping}")
            outline_dict = substitute_names_in_outline(outline_dict, name_mapping)
            outline_json = json.dumps(outline_dict, indent=2, ensure_ascii=False)
            phase_metadata["name_mapping"] = name_mapping

            # CRITICAL: Sync the names list so role descriptions match updated outline
            # This ensures CharacterBuilder gets consistent role descriptions
            for name_entry in names:
                name_entry["role"] = substitute_names_in_text(name_entry["role"], name_mapping)

            print("    Outline updated with new names.")
            print("    Names list synced with updated outline.")
        else:
            print("    No name mapping generated.")
    except json.JSONDecodeError:
        print("    WARNING: Could not parse outline for name substitution")

    # Extract locked names for revision cycles
    locked_names = [n["final_name"] for n in names if n.get("final_name")]

    # Create initial profiles with limits, using pre-generated names
    print(f"\n>>> Building character profiles (max {max_characters})...")
    characters_schema = character_builder.build_characters(
        outline_json, setting_prompt, max_characters,
        predefined_names=names  # Pass pre-generated names (now synced)
    )
    current_characters_json = json.dumps(characters_schema.model_dump(), indent=2)
    print("    Characters created.")

    print(f"\n>>> Building location profiles (max {max_locations})...")
    locations_schema = location_builder.build_locations(
        outline_json, setting_prompt, max_locations
    )
    current_locations_json = json.dumps(locations_schema.model_dump(), indent=2)
    print("    Locations created.")

    # Critique-revision cycles
    for cycle in range(CRITIQUE_CYCLES):
        print(f"\n>>> Critique-Revision Cycle {cycle + 1}/{CRITIQUE_CYCLES}")
        cycle_data = {"cycle": cycle + 1, "critiques": [], "revision_applied": True}

        # Get consistency critique (now returns CritiqueSchema)
        print("    Getting consistency critique...")
        consistency_critique = consistency_critic.critique(
            outline_json, current_characters_json, current_locations_json
        )
        cycle_data["critiques"].append(consistency_critique.model_dump())

        # Revise both based on critique (with locked names to preserve debate results)
        print("    Revising characters...")
        revised_characters = reviser.revise_characters(
            current_characters_json,
            [json.dumps(consistency_critique.model_dump())],
            locked_names=locked_names  # Preserve debated names
        )
        current_characters_json = json.dumps(revised_characters.model_dump(), indent=2)

        print("    Revising locations...")
        revised_locations = reviser.revise_locations(
            current_locations_json,
            [json.dumps(consistency_critique.model_dump())]
        )
        current_locations_json = json.dumps(revised_locations.model_dump(), indent=2)
        print("    Revision complete.")

        phase_metadata["cycles"].append(cycle_data)

    # Parse final outputs from JSON strings
    characters_data = json.loads(current_characters_json)
    final_characters = characters_data.get("characters", characters_data)

    locations_data = json.loads(current_locations_json)
    final_locations = locations_data.get("locations", locations_data)

    phase_metadata["final_characters"] = final_characters
    phase_metadata["final_locations"] = final_locations

    print("\n>>> Phase 2 complete.")
    return {
        "characters": final_characters,
        "characters_json": current_characters_json,
        "locations": final_locations,
        "locations_json": current_locations_json,
        "metadata": phase_metadata,
        "outline_updated": outline_dict,  # Updated outline with debated names
    }


def run_phase3_narrative(outline_json: str, characters_json: str,
                          locations_json: str, model: str = DEFAULT_MODEL) -> dict[str, Any]:
    """
    Phase 3: Write narrative prose scene-by-scene with style/continuity critique.

    Writes each scene individually using structured output to enforce
    proper paragraph structure, then assembles into final narrative.

    Args:
        outline_json: Story outline JSON
        characters_json: Character profiles JSON
        locations_json: Location profiles JSON
        model: LLM model to use

    Returns:
        Dict with narrative and phase metadata
    """
    print("\n" + "=" * 50)
    print("PHASE 3: NARRATIVE WRITING (scene-by-scene)")
    print("=" * 50)

    # Initialize agents
    writer = WriterAgent(model=model)
    style_critic = StyleCriticAgent(model=model)
    continuity_critic = ContinuityCriticAgent(model=model)
    reviser = ReviserAgent(model=model)

    # Parse outline
    try:
        outline = json.loads(outline_json)
    except json.JSONDecodeError:
        outline = {"acts": [], "title": "Untitled"}

    phase_metadata = {
        "phase": 3,
        "name": "Narrative Writing",
        "writing_mode": "scene-by-scene",
        "cycles": [],
    }

    # Write scenes one at a time
    print("\n>>> Writing scenes individually...")
    narrative_acts = []
    previous_ending = None
    total_scenes = sum(len(act.get("scenes", [])) for act in outline.get("acts", []))
    scene_count = 0

    for act in outline.get("acts", []):
        narrative_scenes = []
        for scene in act.get("scenes", []):
            scene_count += 1
            print(f"    Writing scene {scene_count}/{total_scenes}: "
                  f"Act {act.get('act_number', '?')} Scene {scene.get('scene_number', '?')}...")

            # Write this scene with structured output
            prose = writer.write_scene(
                scene=scene,
                characters=characters_json,
                locations=locations_json,
                previous_scene_ending=previous_ending
            )

            narrative_scenes.append({
                "scene_number": scene.get("scene_number", scene_count),
                "location": scene.get("location", "Unknown"),
                "characters": scene.get("characters", []),
                "time": "continuous",
                "text": prose,
                "sentences": split_into_sentences(prose)
            })

            # Keep last 300 chars for continuity
            previous_ending = prose[-300:] if len(prose) > 300 else prose

        narrative_acts.append({
            "act_number": act.get("act_number", 1),
            "act_name": act.get("act_name", "Unnamed"),
            "scenes": narrative_scenes
        })

    # Assemble initial narrative as dict (not JSON string)
    current_narrative_dict = {
        "title": outline.get("title", "Untitled"),
        "acts": narrative_acts
    }
    print(f"    All {total_scenes} scenes written.")

    # Critique-revision cycles - keep narrative as dict throughout
    for cycle in range(CRITIQUE_CYCLES):
        print(f"\n>>> Critique-Revision Cycle {cycle + 1}/{CRITIQUE_CYCLES}")
        cycle_data = {"cycle": cycle + 1, "critiques": [], "revision_applied": True}

        # Convert to JSON for critics (they expect JSON string)
        current_narrative_json = json.dumps(current_narrative_dict, indent=2, ensure_ascii=False)

        # Get critiques (now returns CritiqueSchema objects)
        print("    Getting style critique...")
        style_critique = style_critic.critique(current_narrative_json)
        cycle_data["critiques"].append(style_critique.model_dump())

        print("    Getting continuity critique...")
        continuity_critique = continuity_critic.critique(
            current_narrative_json, characters_json, locations_json
        )
        cycle_data["critiques"].append(continuity_critique.model_dump())

        # Revise narrative using structured output
        print("    Revising narrative (structured output)...")
        try:
            revised = reviser.revise_narrative_structured(
                current_narrative_dict,
                [json.dumps(style_critique.model_dump()), json.dumps(continuity_critique.model_dump())]
            )
            # Convert Pydantic model to dict
            current_narrative_dict = revised.model_dump()
            print("    Revision complete.")
        except Exception as e:
            print(f"    Warning: Structured revision failed ({e}), using scene-by-scene fallback...")

            # Scene-by-scene revision fallback (handles token limit issues)
            try:
                revised_acts = []
                total_scenes_revised = 0

                for act in current_narrative_dict.get("acts", []):
                    revised_scenes = []

                    for scene in act.get("scenes", []):
                        scene_num = scene.get("scene_number", 0)

                        # Build targeted critique for this scene
                        scene_critique = f"""
Style Issues (from STYLE_CRITIC):
{json.dumps(style_critique.model_dump().get('issues', []), indent=2)}

Continuity Issues (from CONTINUITY_CRITIC):
{json.dumps(continuity_critique.model_dump().get('issues', []), indent=2)}

Focus on issues that apply to scene {scene_num}.
"""

                        print(f"      Revising scene {scene_num}...")
                        revised_scene = reviser.revise_scene(
                            scene,
                            scene_critique,
                            characters_context=characters_json,
                            locations_context=locations_json
                        )

                        # Build revised scene dict
                        revised_scenes.append({
                            "scene_number": scene.get("scene_number"),
                            "location": scene.get("location"),
                            "characters": scene.get("characters", []),
                            "time": scene.get("time", ""),
                            "text": revised_scene.text,
                        })
                        total_scenes_revised += 1

                    revised_acts.append({
                        "act_number": act.get("act_number"),
                        "act_name": act.get("act_name", ""),
                        "scenes": revised_scenes,
                    })

                current_narrative_dict = {
                    "title": current_narrative_dict.get("title", ""),
                    "acts": revised_acts,
                }
                print(f"    Scene-by-scene revision complete ({total_scenes_revised} scenes).")

            except Exception as scene_e:
                print(f"    Warning: Scene-by-scene revision also failed ({scene_e})")
                print("    Keeping current narrative without revision.")
                # Don't modify current_narrative_dict - keep the original

        phase_metadata["cycles"].append(cycle_data)

    # No json.loads needed - already a dict
    final_narrative = current_narrative_dict

    phase_metadata["final_narrative"] = final_narrative
    phase_metadata["total_scenes_written"] = total_scenes

    print("\n>>> Phase 3 complete.")
    return {
        "narrative": final_narrative,
        "narrative_json": json.dumps(final_narrative, indent=2, ensure_ascii=False),
        "metadata": phase_metadata,
    }


def run_full_story_pipeline(story_prompt: str, setting_prompt: str,
                            model: str = DEFAULT_MODEL,
                            scope: str = DEFAULT_STORY_SCOPE) -> dict[str, Any]:
    """
    Run complete 3-phase story generation pipeline.

    Args:
        story_prompt: Story Engine prompt
        setting_prompt: Deck of Worlds microsetting
        model: LLM model to use
        scope: Story scope preset (flash, short, standard, long)

    Returns:
        Complete story data with all phases
    """
    scope_config = STORY_SCOPES.get(scope, STORY_SCOPES[DEFAULT_STORY_SCOPE])

    print("\n" + "#" * 60)
    print("# STORY BUILDER PIPELINE")
    print(f"# Scope: {scope_config['description']}")
    print("# 3 Phases × 2 Critique-Revision Cycles")
    print("#" * 60)

    # Phase 1: Outline with scope constraints
    phase1 = run_phase1_outline(story_prompt, setting_prompt, model, scope_config)

    # Phase 2: Characters & Locations with max limits
    phase2 = run_phase2_characters_locations(
        phase1["outline_json"],
        setting_prompt,
        model,
        max_characters=scope_config["max_characters"],
        max_locations=scope_config["max_locations"]
    )

    # Phase 3: Narrative (scene-by-scene)
    phase3 = run_phase3_narrative(
        phase1["outline_json"],
        phase2["characters_json"],
        phase2["locations_json"],
        model
    )

    print("\n" + "#" * 60)
    print("# PIPELINE COMPLETE")
    print("#" * 60)

    return {
        "story": {
            "outline": phase1["outline"],
            "characters": phase2["characters"],
            "locations": phase2["locations"],
            "narrative": phase3["narrative"],
        },
        "story_metadata": {
            "phase1_outline": phase1["metadata"],
            "phase2_characters": phase2["metadata"],
            "phase3_narrative": phase3["metadata"],
            "critique_cycles_per_phase": CRITIQUE_CYCLES,
            "model_used": model,
            "scope": scope,
            "scope_config": scope_config,
        },
    }
