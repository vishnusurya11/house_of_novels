---
description: Rules for modifying Pydantic schemas in story_schemas.py
paths:
  - "src/story_schemas.py"
---

# Schema Rules for story_schemas.py

## This File is Critical
`story_schemas.py` is ~3500 lines and defines ALL structured output schemas for the pipeline.
Changes here affect every agent that uses the modified schema. Be extremely careful.

## Schema Conventions
- Every field uses `Field(...)` or `Field(default, ...)` with a `description` parameter
- Required fields: `Field(..., description="...")`
- Optional fields: `Field(None, description="...")` or `Field(default_factory=list, description="...")`
- Scores and ratings: use `ge=` and `le=` validators (e.g., `Field(..., ge=1, le=10)`)
- List fields with length constraints: `Field(..., min_length=N, max_length=M)`
- Use `field_validator` for complex validation, not `@validator` (Pydantic v2)

## Adding New Schemas
1. Place in the correct section (marked with `# ===` comment blocks)
2. Sections map to pipeline steps: Phase 1 Outline, Name Debate, Character, World Building, Scene, Narrative, Critique, etc.
3. Follow the Proposal/Critique/Vote pattern for debate schemas:
   - `<Thing>Proposal` - what an agent proposes
   - `<Thing>Critique` - agent's critique with scores
   - `<Thing>Vote` - agent's vote with reasoning

## Modifying Existing Schemas
- Adding a new optional field is safe (backward compatible with existing codex files)
- Making a field required WILL break existing codex files - add migration logic
- Renaming a field WILL break agents that reference the old name - grep for all usages first
- Before modifying, grep for: the schema class name, all field names being changed, and all files that import it

## JSON Schema Compatibility
- Schemas must be compatible with OpenRouter's `json_schema` method (strict=True)
- Avoid: Union types, discriminated unions, complex nested Optional types
- Prefer: simple types (str, int, float, bool, list[str], list[SimpleModel])
- Test schema changes with: `Schema.model_json_schema()` to verify valid JSON schema output