---
name: story-review
description: >
  Review generated story prose from a codex JSON file for quality issues.
  Analyzes pacing, voice consistency, show-don't-tell, filter words,
  dialogue quality, and emotional resonance. Use when reviewing a
  completed Phase 1 output or individual scene prose.
argument-hint: <codex-path-or-forge-timestamp>
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash(jq:*)
  - Bash(python3:*)
---

# Story Review

Review generated prose from a House of Novels codex for quality issues.

## Input
$ARGUMENTS should be a path to a codex JSON file or a forge timestamp directory.
If no argument given, find the most recent forge directory with `ls -td forge/*/`.

## Review Process

### 1. Word Count Check
Each scene should target 1500-2000 words per config. Flag scenes under 1200 or over 2200.

### 2. Filter Word Scan
Count per scene: felt, saw, noticed, heard, thought, realized, knew, wondered, seemed, appeared.
These create psychic distance - the reader is told what the character perceives instead of experiencing it directly.

### 3. Cliche Detection
Flag: "heart pounded/raced/hammered", "blood ran cold", "eyes widened", "breath caught", "stomach dropped", "time stood still", "tears streamed", "jaw clenched", "knuckles whitened".

### 4. Show-Don't-Tell Violations
Flag patterns like "[Character] was [emotion]" or "[Character] felt [emotion]".
Good: physical sensation + action. Bad: named emotion without grounding.

### 5. Voice Consistency
- Does POV stay consistent within each scene?
- Does dialogue voice differ between characters?
- Are there POV breaks (seeing what the POV character can't)?

### 6. Pacing Analysis
- Do scene openings vary? (Check against 10 SCENE_OPENING_TYPES if available)
- Does every scene have a turning point or shift?
- Are there dead spots with no tension, question, or forward pull?

### 7. Dialogue Quality
- Is there subtext (what's NOT said)?
- Are dialogue tags mostly invisible ("said")?
- Is there action beats between dialogue lines?

## Output Format

For each scene:
- **Scene ID**: Chapter X, Scene Y
- **Word count**: N (PASS/WARN/FAIL)
- **Filter words**: N total (list top offenders)
- **Cliches**: N found (list them)
- **Show-don't-tell**: N violations
- **Voice**: PASS/WARN with notes
- **Pacing**: PASS/WARN with notes
- **Quality score**: 1-10

End with:
- Aggregate statistics across all scenes
- Top 3 patterns to fix system-wide
- Strongest scene and weakest scene with reasoning