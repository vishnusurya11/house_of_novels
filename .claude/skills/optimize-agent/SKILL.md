---
name: optimize-agent
description: >
  Analyze a story agent's system prompt for quality, specificity, and
  effectiveness. Suggests improvements based on prompt engineering best
  practices and fiction craft knowledge. Use to improve agent output quality.
argument-hint: <agent-class-name-or-file-path>
allowed-tools:
  - Read
  - Grep
  - Glob
---

# Optimize Agent Prompt

Analyze and improve a story agent's system prompt and configuration.

## Input
$ARGUMENTS should be an agent class name (e.g., `ProsePolishCritic`) or file path (e.g., `src/story_agents/critique_agents.py`).

## Analysis Process

### 1. Locate the Agent
- Search `src/story_agents/` for the class definition
- Extract: `name`, `role`, `system_prompt` properties
- Find all methods that call `invoke_structured()` - extract the user prompts built there

### 2. Prompt Quality Checklist

| Criterion | What to Check |
|-----------|---------------|
| **Role clarity** | Does the system prompt clearly define WHO this agent is? |
| **Task specificity** | Does it say exactly WHAT to produce? |
| **Methodology** | Does it reference specific craft frameworks (Save the Cat, Deep POV, etc.)? |
| **Examples** | Does it include concrete examples of good/bad output? |
| **Constraints** | Does it list what NOT to do? (negative examples reduce errors) |
| **Output format** | Does it describe the expected structure clearly? |
| **Token efficiency** | Is the prompt concise or bloated with repetition? |

### 3. Fiction Craft Alignment
For writing-focused agents:
- Does the prompt reference real writing craft concepts?
- Are evaluation criteria from professional editing standards?
- Does it avoid generic instructions like "make it better" or "be creative"?
- Does it encourage specificity in the agent's output?

### 4. Schema Alignment
- Find the Pydantic schema this agent outputs to (in `src/story_schemas.py`)
- Check if the system prompt's instructions match the schema's field descriptions
- Flag mismatches (prompt asks for X but schema expects Y)
- Flag schema fields with no corresponding prompt guidance

## Output
- **Current assessment**: strengths and weaknesses of the existing prompt
- **Specific rewrites**: before/after for the weakest sections
- **Schema alignment report**: mismatches and fixes
- **Estimated impact**: which output quality dimensions will improve most