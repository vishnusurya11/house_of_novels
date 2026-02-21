#!/usr/bin/env python3
"""Migrate codex JSON to unified chapter structure.

This script restructures an existing codex JSON file by:
1. Merging story.narrative data into story.chapters (unified structure)
2. Moving story.critiques to metadata.phase_1.critiques
3. Fixing all scene location_id values to use loc_XXX format
4. Adding scene_id to outline scenes that don't have one
"""

import json
import sys
from copy import deepcopy


def build_location_map(locations: list) -> dict:
    """Build name->id mapping with lowercased keys.

    Also stores variants without the "The " prefix so that
    "The Belladonna Throne" can be matched as "belladonna throne".

    Args:
        locations: List of location dicts with "id" and "name" keys.

    Returns:
        Dict mapping lowercased location name variants to location id strings.
    """
    loc_map: dict[str, str] = {}
    for loc in locations:
        loc_id = loc["id"]
        name = loc["name"]
        lowered = name.lower()
        loc_map[lowered] = loc_id

        # Store variant without leading "The "
        if lowered.startswith("the "):
            loc_map[lowered[4:]] = loc_id

    return loc_map


def resolve_location_id(location_name: str, loc_map: dict) -> str:
    """Resolve a potentially messy location name to a canonical loc_XXX id.

    Resolution strategy (in order):
    1. Exact match on lowercased name
    2. Try stripping a leading "The " and match again
    3. Substring containment -- check if any known location name is contained
       in the query or vice-versa
    4. Fallback: print a warning and return an empty string

    Args:
        location_name: The raw location name or id from the scene.
        loc_map: Mapping produced by build_location_map().

    Returns:
        A canonical loc_XXX id string, or "" if no match is found.
    """
    if not location_name:
        return ""

    lowered = location_name.lower().strip()

    # Already in loc_XXX format -- return as-is
    if lowered.startswith("loc_") and lowered[4:].isdigit():
        return location_name

    # 1. Exact match
    if lowered in loc_map:
        return loc_map[lowered]

    # 2. Try without leading "The "
    without_the = lowered
    if without_the.startswith("the "):
        without_the = without_the[4:]
    if without_the in loc_map:
        return loc_map[without_the]

    # 3. Substring containment
    # Check if any key in loc_map is contained in lowered, or vice-versa.
    # Prefer longer matches to avoid false positives.
    best_match_key = ""
    best_match_len = 0
    for key, loc_id in loc_map.items():
        if key in lowered or lowered in key:
            if len(key) > best_match_len:
                best_match_key = key
                best_match_len = len(key)
    if best_match_key:
        return loc_map[best_match_key]

    # 4. Fallback
    print(f"  WARNING: Could not resolve location '{location_name}'")
    return ""


def migrate_codex(codex: dict) -> dict:
    """Perform all migration steps on the codex dict (mutates in place).

    Steps:
    1. Build location map from codex["story"]["locations"]
    2. Merge narrative data into chapters
    3. Fix location_ids in all scenes
    4. Add scene_ids where missing
    5. Move critiques from story to metadata.phase_1

    Args:
        codex: The full codex dictionary loaded from JSON.

    Returns:
        The modified codex dictionary.
    """
    story = codex["story"]

    # ------------------------------------------------------------------ #
    # 1. Build location map
    # ------------------------------------------------------------------ #
    locations = story.get("locations", [])
    loc_map = build_location_map(locations)

    # ------------------------------------------------------------------ #
    # 2. Merge narrative into chapters
    # ------------------------------------------------------------------ #
    narrative = story.get("narrative", {})
    chapters = story.get("chapters", {})

    if narrative:
        # Copy top-level narrative metadata into chapters
        for field in (
            "title",
            "subtitle",
            "total_word_count",
            "total_scenes",
            "average_words_per_scene",
        ):
            if field in narrative:
                chapters[field] = narrative[field]

        # Index narrative chapters by chapter_number for fast lookup
        narr_chapters_by_num: dict[int, dict] = {}
        for nc in narrative.get("chapters", []):
            narr_chapters_by_num[nc.get("chapter_number")] = nc

        # Walk outline chapters and merge matching narrative data
        for outline_ch in chapters.get("chapters", []):
            ch_num = outline_ch.get("chapter_number")
            narr_ch = narr_chapters_by_num.get(ch_num)
            if narr_ch is None:
                continue

            # Copy chapter-level fields from narrative
            for field in ("chapter_word_count", "act", "chapter_title"):
                if field in narr_ch:
                    outline_ch[field] = narr_ch[field]

            # Index narrative scenes by scene_number
            narr_scenes_by_num: dict[int, dict] = {}
            for ns in narr_ch.get("scenes", []):
                narr_scenes_by_num[ns.get("scene_number")] = ns

            # Merge scene-level fields
            merge_fields = [
                "scene_id",
                "prose",
                "word_count",
                "synthesis_score",
                "critique_average_score",
                "critique_scores",
                "synthesis_agent",
                "dialogue_score",
                "no_tag_test_passed",
                "sensory_selection",
                "active_voice_percentage",
                "techniques_integrated",
                "revision_notes",
            ]

            for outline_scene in outline_ch.get("scenes", []):
                scene_num = outline_scene.get("scene_number")
                narr_scene = narr_scenes_by_num.get(scene_num)
                if narr_scene is None:
                    continue
                for field in merge_fields:
                    if field in narr_scene:
                        outline_scene[field] = narr_scene[field]

        # Remove narrative now that it has been merged
        del story["narrative"]

    # ------------------------------------------------------------------ #
    # 3. Fix location_ids in all scenes
    # ------------------------------------------------------------------ #
    locations_fixed = 0
    for ch in chapters.get("chapters", []):
        for scene in ch.get("scenes", []):
            # Try resolving from the location_id slug first
            raw_loc = scene.get("location_id", "")
            resolved = resolve_location_id(raw_loc, loc_map) if raw_loc else ""

            # If slug didn't resolve, try the human-readable location name
            if not resolved:
                loc_name = scene.get("location", "")
                resolved = resolve_location_id(loc_name, loc_map) if loc_name else ""

            if resolved:
                if resolved != scene.get("location_id", ""):
                    locations_fixed += 1
                scene["location_id"] = resolved

    # ------------------------------------------------------------------ #
    # 4. Add scene_ids where missing
    # ------------------------------------------------------------------ #
    scenes_given_id = 0
    global_counter = 1
    for ch in chapters.get("chapters", []):
        ch_num = ch.get("chapter_number", 0)
        for scene in ch.get("scenes", []):
            if not scene.get("scene_id"):
                scene["scene_id"] = f"ch{ch_num}_scene{global_counter}"
                scenes_given_id += 1
            global_counter += 1

    # ------------------------------------------------------------------ #
    # 5. Move critiques to metadata.phase_1
    # ------------------------------------------------------------------ #
    critiques_moved = 0
    if "critiques" in story:
        critiques = story.pop("critiques")
        critiques_moved = len(critiques) if isinstance(critiques, list) else 0
        metadata = codex.setdefault("metadata", {})
        phase_1 = metadata.setdefault("phase_1", {})
        phase_1["critiques"] = critiques

    # Print migration summary
    print(f"  Locations fixed:    {locations_fixed}")
    print(f"  Scene IDs added:    {scenes_given_id}")
    print(f"  Critiques moved:    {critiques_moved}")

    return codex


def main() -> None:
    """Entry point: load codex JSON, migrate, and save back."""
    if len(sys.argv) < 2:
        print("Usage: python migrate_codex.py <path/to/codex.json>")
        sys.exit(1)

    codex_path = sys.argv[1]

    print(f"Loading codex from: {codex_path}")
    with open(codex_path, "r", encoding="utf-8") as f:
        codex = json.load(f)

    print("Migrating codex...")
    codex = migrate_codex(codex)

    print(f"Saving migrated codex to: {codex_path}")
    with open(codex_path, "w", encoding="utf-8") as f:
        json.dump(codex, f, indent=2, ensure_ascii=False)
        f.write("\n")

    # Summary stats
    story = codex.get("story", {})
    chapters_data = story.get("chapters", {})
    total_chapters = len(chapters_data.get("chapters", []))
    total_scenes = sum(
        len(ch.get("scenes", []))
        for ch in chapters_data.get("chapters", [])
    )
    scenes_with_prose = sum(
        1
        for ch in chapters_data.get("chapters", [])
        for s in ch.get("scenes", [])
        if s.get("prose")
    )

    print("\n--- Migration Summary ---")
    print(f"  Total chapters:     {total_chapters}")
    print(f"  Total scenes:       {total_scenes}")
    print(f"  Scenes with prose:  {scenes_with_prose}")
    print("  Done.")


if __name__ == "__main__":
    main()
