# House of Novels

AI-powered novel generation system. Story seeds flow through a 10-step Phase 1 author pipeline, then image/video generation, editing, and YouTube upload.

## Commands

```bash
uv sync                                    # Install dependencies
uv run python -m src.house_of_novels --scope standard  # Full pipeline (all phases)
uv run python -m src.phases.phase1_author forge/<ts>/codex_<ts>.json  # Phase 1 only
uv run python -m src.phases.phase1_author forge/<ts>/codex_<ts>.json --steps 0 1 2  # Specific steps
uv run pytest tests/ -v                    # Run tests
uv run python -m py_compile src/story_agents/<file>.py  # Syntax check
```

## Architecture

**6 Phases:** Codex -> Author (Phase 1) -> Prompts -> Generation -> Editing -> Upload

**Phase 1 (10 steps):** Theme -> Characters -> Story Shape -> Plot -> World -> Scenes/Foreshadowing/Interconnection -> Prose (synthesis) -> Revision (5 critics) -> Titles

**Agent Debate Pattern:** Propose -> Cross-Critique -> Vote -> Synthesize
- Agents extend `BaseStoryAgent` with structured output via `invoke_structured()`
- Automatic model fallback chain, disk cache, thread-based parallelism (25 concurrent)

**Key Files:**
- `src/authors/base_phase1.py` - Phase 1 orchestrator
- `src/story_schemas.py` - All Pydantic schemas (~3500 lines)
- `config.yaml` - Models, temperatures, token limits, parallelism
- `src/story_agents/` - 38 specialized agent files

## Code Style

- Python 3.13+, type hints on all signatures, `list[str]` not `List[str]`
- Pydantic v2 with `Field(...)` and descriptions on every field
- f-strings, double quotes, imports: stdlib -> third-party -> src
- Config values from `config.yaml` via `src/config.py` helpers - never hardcode models/tokens/temps
- LLM calls through `BaseStoryAgent.invoke_structured()` for retry, fallback, caching

## Git & Commits

- Do NOT commit unless explicitly asked. No Claude attribution in commits
- Do NOT push to remote unless explicitly asked
- Do NOT amend or `--force` unless explicitly asked

## Critical Rules

- **CRITICAL**: Do NOT run long-running jobs (5+ minutes) without asking first
- Do NOT run the full pipeline (`src.house_of_novels`) without asking - it costs real API money
- Wait for user approval before significant changes
- Ask before deleting files or making destructive operations
- Prefer editing existing files over creating new ones
- For non-trivial tasks (3+ steps), plan first before implementing
- Simplicity first. Find root causes. No temporary fixes. Senior developer standards.

## Workflow Orchestration

### 1. Plan Node Default

- Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions)
- If something goes sideways, STOP and re-plan immediately - don't keep pushing
- Use plan mode for verification steps, not just building
- Write detailed specs upfront to reduce ambiguity

### 2. Subagent Strategy

- Use subagents liberally to keep main context window clean
- Offload research, exploration, and parallel analysis to subagents
- For complex problems, throw more compute at it via subagents
- One tack per subagent for focused execution

### 3. Self-Improvement Loop

- After ANY correction from the user: update `tasks/lessons.md` with the pattern
- Write rules for yourself that prevent the same mistake
- Ruthlessly iterate on these lessons until mistake rate drops
- Review lessons at session start for relevant project

### 4. Verification Before Done

- Never mark a task complete without proving it works
- Diff behavior between main and your changes when relevant
- Ask yourself: "Would a staff engineer approve this?"
- Run tests, check logs, demonstrate correctness

### 5. Demand Elegance (Balanced)

- For non-trivial changes: pause and ask "is there a more elegant way?"
- If a fix feels hacky: "Knowing everything I know now, implement the elegant solution"
- Skip this for simple, obvious fixes - don't over-engineer
- Challenge your own work before presenting it

### 6. Autonomous Bug Fizing

- When given a bug report: just fix it. Don't ask for hand-holding
- Point at logs, errors, failing tests - then resolve them
- Zero context switching required from the user
- Go fix failing CI tests without being told how

## Task Management

1. **Plan First**: Write plan to `tasks/todo.md` with checkable items
2. **Verify Plan**: Check in before starting implementation
3. **Track Progress**: Mark items complete as you go
4. **Explain Changes**: High-level summary at each step
5. **Document Results**: Add review section to `tasks/todo.md`
6. **Capture Lessons**: Update `tasks/lessons.md` after corrections

## Core Principles

- **Simplicity First**: Make every change as simple as possible. Impact minimal code.
- **No Laziness**: Find root causes. No temporary fixes. Senior developer standards.
- **Minimat Impact**: Changes should only touch what's necessary. Avoid introducing bugs.
