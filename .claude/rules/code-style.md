---
description: Python coding conventions for the House of Novels project
---

# Code Style Rules

## Python Conventions
- Python 3.13+. Use modern syntax: `list[str]` not `List[str]`, `dict[str, Any]` not `Dict[str, Any]`
- Type hints on all function signatures and return types
- Use `Optional[X]` for nullable fields (Pydantic compatibility)
- f-strings for string formatting, double quotes for all strings
- Imports order: stdlib -> third-party (langchain, pydantic, httpx) -> src modules, separated by blank lines
- No bare `except:` - always catch specific exceptions
- Use `Path` from pathlib, not string paths with `os.path`

## Project Patterns
- All config values come from `config.yaml` via `src/config.py` helpers: `get_step_config()`, `get_token_limit()`, `get_step_model()`
- Never hardcode model names, token limits, or temperature values - always reference config
- Thread parallelism uses `concurrent.futures.ThreadPoolExecutor` with `max_workers` from config.yaml
- LLM calls must go through `BaseStoryAgent.invoke_structured()` for automatic retry, fallback, caching, and token tracking
- Step results are `@dataclass` classes with `success`, `error`, `duration_seconds`, `token_usage` fields

## Testing
- Tests use pytest with fixtures, mocks via `unittest.mock`
- Test files: `tests/test_*.py`
- Mock LLM calls - never make real API calls in tests