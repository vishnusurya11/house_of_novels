---
description: Rules for modifying the Phase 1 pipeline orchestrator and phase runners
paths:
  - "src/authors/base_phase1.py"
  - "src/phases/**/*.py"
  - "config.yaml"
---

# Pipeline Rules

## base_phase1.py is the Largest File
- Always use line numbers when referencing code in this file
- Each step method follows the pattern: validate inputs -> run agents (often parallel) -> build result dataclass -> save to codex
- Step result dataclasses are defined at the top of the file
- The `run_all_steps()` method orchestrates sequential step execution with timing and error handling

## Step Method Pattern
```python
def step<N>_<name>(self, codex: dict) -> Step<N>Result:
    """Step N: <Description>."""
    start = time.time()
    token_usage = {}
    # ... agent instantiation, debate execution, result building ...
    duration = time.time() - start
    return Step<N>Result(success=True, duration_seconds=duration, token_usage=token_usage)
```

## Parallelism Rules
- Thread-based parallelism with `ThreadPoolExecutor`
- `max_workers` comes from `config.yaml` step config, NOT hardcoded
- All API calls go through the global `_API_SEMAPHORE` (25 concurrent) in BaseStoryAgent
- Never increase `max_workers` beyond the global semaphore count
- Parallel debate pattern: proposals in parallel -> critiques in parallel -> votes in parallel

## Config Changes
- All step configuration lives in `config.yaml` under `steps.<step_name>`
- Token limits: always test that the limit accommodates reasoning tokens
- When adding a new config key, add a default fallback in the code that reads it

## Codex State Management
- Steps read from and write to the `codex` dict
- Each step should validate that its required input keys exist before proceeding
- Write results under consistent key names that match the step
- The codex is saved to disk after each step completes (not just at the end)