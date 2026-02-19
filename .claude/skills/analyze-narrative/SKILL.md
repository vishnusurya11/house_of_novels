---
name: analyze-narrative
description: >
  Analyze a generated story's narrative structure for theme coherence,
  character arc completion, plot beat coverage, and scene interconnection.
  Use after Phase 1 completes to validate structural quality before
  proceeding to media generation.
argument-hint: <codex-path-or-forge-timestamp>
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash(jq:*)
  - Bash(python3:*)
---

# Narrative Structure Analysis

Analyze a completed story's structural integrity against professional fiction standards.

## Input
$ARGUMENTS should be a path to a codex JSON file or forge timestamp. If none given, use most recent forge.

## Analysis Dimensions

### 1. Theme Coherence
- Read `story.theme_foundation` - extract the central thematic question and thematic square
- For each scene: does it test/explore the thematic question?
- Track which characters embody which thematic square positions
- Flag scenes that feel disconnected from theme
- Score: percentage of scenes with clear thematic relevance

### 2. Character Arc Tracking
For each character in `story.characters`:
- Map Lie -> Truth arc progression through scenes they appear in
- Verify Ghost/Wound is referenced or echoed
- Track Shadow trait integration
- Note arc type completion (positive change, flat, disillusionment, fall, corruption)
- Flag characters who appear in scenes but have no arc movement

### 3. Plot Beat Coverage
Compare `story.plot_structure.integrated_beats` (15 Save the Cat beats) against actual scenes:
- Opening Image, Theme Stated, Setup, Catalyst, Debate
- Break into Two, B Story, Fun and Games, Midpoint
- Bad Guys Close In, All Is Lost, Dark Night of the Soul
- Break into Three, Finale, Final Image
- Flag beats that are missing or weakly represented in the prose

### 4. Foreshadowing Validation
- Read `story.foreshadowing` or scene-level `setup_payoff_tracking`
- Check Rule of Three: each foreshadowed element should appear ~3 times (plant, reminder, payoff)
- Flag foreshadowing planted but never paid off (Chekhov's Gun violation)
- Flag payoffs that appear without adequate setup

### 5. Scene Interconnection
- Check scene-to-scene causal chains
- Verify each scene's outcome drives the next scene's conflict
- Flag isolated scenes with no cause-effect connection to adjacent scenes
- Check plot thread resolution: are all threads closed by the end?

## Output

Structured report with:
- Score per dimension (1-10) with specific citations
- Overall narrative integrity score
- Top 3 structural strengths
- Top 3 structural weaknesses with specific fix recommendations
- Character arc completion table (character x scenes matrix)