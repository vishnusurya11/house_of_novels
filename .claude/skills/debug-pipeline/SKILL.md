---
name: debug-pipeline
description: >
  Debug Phase 1 pipeline failures. Traces errors through step execution,
  identifies schema validation issues, model fallback problems, and
  parallelism bugs. Use when a pipeline step fails or produces unexpected output.
argument-hint: <error-message-or-step-number>
context: fork
agent: pipeline-debugger
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash(python3:*)
  - Bash(uv run:*)
  - Bash(jq:*)
  - Bash(ls:*)
---

# Debug Pipeline

Diagnose and fix Phase 1 pipeline failures.

## Input
$ARGUMENTS may contain:
- An error message or traceback
- A step number that failed (e.g., "step 5")
- A codex path where the failure occurred

## Step Map

| Step | Method | Key Agents | Schema |
|------|--------|------------|--------|
| 0 | step0_theme_foundation | ThemePhilosopher | ThemeFoundation |
| 1 | step1_character_creation | Character*Agent | CharacterSheetSchema |
| 2 | step2_story_shape_genre | StoryShape agents | StoryShapeSchema |
| 3 | step3_plot_structure | PlotStructure agents | IntegratedBeatSchema |
| 4 | step4_world_building | WorldPressure, Location agents | LocationSchema |
| 5 | step5_chapter_scene_breakdown | SceneBreakdown agents | ChapterOutlineSchema |
| 6 | step6_narrative | Narrative, Synthesis, Critique agents | NarrativeSceneSchema |
| 7 | step7_revision | Reviser, 5 Critic agents | RevisionSchema |
| 8 | step8_naming | TitleNaming agents | TitleSchema |

## Diagnostic Process

1. **Parse the error** - identify step name and line number from traceback
2. **Check common causes:**
   - Schema validation: LLM output doesn't match Pydantic fields -> check `story_schemas.py`
   - Token truncation: `max_tokens` too low -> check `config.yaml` step settings
   - Model incompatibility: model doesn't support `json_schema` -> check model config
   - Reasoning token overflow: reasoning tokens eat into output budget
   - Thread deadlock: semaphore exhaustion -> check `max_workers` vs semaphore count
   - Missing codex keys: previous step didn't write expected data
3. **Read relevant code** in `src/authors/base_phase1.py` (use line numbers - file is large)
4. **Read the agent** in `src/story_agents/` and the schema in `src/story_schemas.py`
5. **Propose fix** with specific file:line reference

## Output
Root cause analysis with:
- Which step/agent/schema failed
- Why it failed (specific cause)
- Proposed fix with file paths and code changes
- How to verify the fix worked