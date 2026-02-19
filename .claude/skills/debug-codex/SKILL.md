---
name: debug-codex
description: >
  Inspect and validate a codex JSON file for structural issues, missing
  fields, schema mismatches, or incomplete pipeline steps. Use when a
  codex seems broken or a pipeline step failed.
argument-hint: <codex-path-or-forge-timestamp>
allowed-tools:
  - Read
  - Bash(jq:*)
  - Bash(python3:*)
  - Bash(ls:*)
  - Grep
  - Glob
---

# Debug Codex

Inspect a codex JSON file for structural integrity and completeness.

## Input
$ARGUMENTS should be a codex path or forge timestamp.
If no argument, find most recent with `ls -td forge/*/`.

## Validation Checks

### 1. Top-Level Structure
Required keys: `generated_at`, `config`, `author`, `story_engine`, `deck_of_worlds`
After Phase 1: `story` key must exist.
Check `config.scope` matches expected story scope constraints (flash/short/standard/long).

### 2. Phase 1 Step Completeness
Check which steps have been completed by looking for these keys in `story`:

| Step | Key | Validation |
|------|-----|------------|
| 0 | `theme_foundation` | Has `central_question`, `thematic_square` with 4 positions |
| 1 | `characters` | List with correct count per scope, each has `lie`, `truth`, `shadow`, `ghost`, `arc_type` |
| 2 | `story_shape` | Has `classic_plot`, `save_the_cat_type`, `primary_genre` |
| 3 | `plot_structure` | `integrated_beats` has ~15 entries |
| 4 | `world_building` + `locations` | Locations list matches scope count |
| 5 | `chapters` | Chapter count matches scope, scenes have IDs and metadata |
| 5B | Scene-level `setup_payoff_tracking` | Foreshadowing chains present |
| 5C | Scene-level `scene_causality`, `active_plot_threads` | Interconnection data |
| 6 | Scene-level `prose` | Non-empty text in scene objects |
| 7 | Scene-level critique scores or revision markers | Revision pass completed |
| 8 | `title`, `chapter_titles` | Title naming completed |

### 3. Cross-Reference Checks
- Characters mentioned in scenes exist in the character list
- Locations mentioned in scenes exist in the location list
- Scene IDs are unique and sequential
- POV characters in scenes are valid character IDs/names

### 4. Word Count Audit
- Extract prose from all scenes
- Report per-scene word count (target: 1500-2000)
- Flag under 1200 or over 2200

### 5. Metadata
- Report: total token usage, step timings, models used
- Flag steps that took abnormally long (>10 minutes per scene)
- Report disk size of codex file

## Output
Traffic-light summary per check:
- PASS: All good
- WARN: Minor issues, pipeline can continue
- FAIL: Structural problem that will break downstream steps

End with recommended next action (re-run step X, fix field Y, etc.)