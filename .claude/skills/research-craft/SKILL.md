---
name: research-craft
description: >
  Research fiction writing craft topics such as character psychology,
  narrative theory, dialogue techniques, pacing strategies, and prose
  style. Use when you need to understand a writing craft concept to
  improve an agent's prompt or the story generation system.
argument-hint: <topic like "deep POV" or "try-fail cycles" or "dialogue subtext">
context: fork
agent: writing-researcher
allowed-tools:
  - WebSearch
  - WebFetch
  - Read
  - Grep
  - Glob
---

# Research Writing Craft

Research a fiction writing craft topic and summarize findings relevant to the House of Novels system.

## Input
$ARGUMENTS is the craft topic to research. Examples:
- "deep POV techniques"
- "try-fail cycles in scene design"
- "dialogue subtext and compression"
- "motivation-reaction units (MRUs)"
- "micro-tension techniques Sol Stein"
- "character arc beat placement"
- "scene opening variety"

## Research Process

1. **Web search** for the topic + "fiction writing craft" or "narrative technique"
2. **Prioritize sources** from established craft authorities:
   - K.M. Weiland (helpingwritersbecomeauthors.com) - Character arcs, Lie/Truth
   - Save the Cat / Blake Snyder - Beat sheets, genre types
   - Robert McKee - Story structure, scene design
   - John Truby - 22 building blocks, moral argument
   - Dwight Swain - Scene/sequel pattern, MRUs
   - Sol Stein - Micro-tension, dialogue
   - Brandon Sanderson - Magic systems, promises/payoffs
   - Writers Digest, Jane Friedman, The Creative Penn
3. **Read 3-5 quality sources** and synthesize
4. **Map to House of Novels** - identify which agents/steps would benefit

## Output Format

- **Concept**: 2-3 sentence definition
- **Key Principles**: Bulleted list of the core rules/techniques
- **Application to House of Novels**: Which specific agent file and step would benefit, and how
- **Prompt Language Suggestions**: Exact phrases/paragraphs to add to agent system prompts
- **Implementation Ideas**: Any schema or pipeline changes that could encode this technique
- **Sources**: URLs with brief descriptions of what each covers