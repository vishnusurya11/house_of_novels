---
description: Rules for modifying story agent files
paths:
  - "src/story_agents/**/*.py"
---

# Story Agent Rules

## Agent Structure
Every agent class MUST:
1. Extend `BaseStoryAgent`
2. Implement three `@property` methods: `name` (UPPER_SNAKE_CASE string), `role` (Title Case string), `system_prompt` (multi-line string)
3. Have a docstring explaining the agent's methodology and references

## System Prompts
- Start with "You are a [role] who [does what]"
- Include a clear METHODOLOGY section with named framework references (e.g., "Deep POV", "Save the Cat", "Lie/Truth System")
- Include explicit CONSTRAINTS or AVOID sections listing what NOT to do
- Include EXAMPLES of good and bad output where possible
- Keep prompts under 2000 tokens - concise beats verbose
- Reference the schema field names the agent will output to

## Method Patterns
- Proposal methods: take context dict, return Pydantic schema via `self.invoke_structured(prompt, Schema, max_tokens)`
- Critique methods: take proposals + context, return critique schema
- Vote methods: take proposals + critiques, return vote schema
- All methods should build a user_prompt string and call `self.invoke_structured()`

## Import Convention
- Import schemas from `src.story_schemas`
- Import base from `src.story_agents.base_story_agent`
- Group imports by schema type (proposals, critiques, votes)

## Naming Convention
- File: `<domain>_agents.py` (e.g., `theme_agents.py`, `critique_agents.py`)
- Class: `<Role><Function>Agent` (e.g., `ThemePhilosopherAgent`, `ProsePolishCritic`)
- Name property: `UPPER_SNAKE_CASE` matching the role (e.g., `"THEME_PHILOSOPHER"`)