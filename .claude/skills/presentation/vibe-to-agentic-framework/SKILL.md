---
name: vibe-to-agentic-framework
description: The conceptual framework behind the presentation — what "Vibe Coding to Agentic Engineering" means, why the journey is structured the way it is, and how every slide fits the narrative arc
---

# The "Vibe Coding to Agentic Engineering" Framework

This skill teaches the **conceptual model** behind the presentation. Every slide, section, and weight exists to tell a single story: how a developer incrementally moves from unstructured "vibe coding" (0%) to fully agentic engineering (100%).

## Core Concept

**Vibe Coding (0%)** is when a developer uses Claude Code with no structure — no project context, no conventions, no reusable knowledge. Every prompt is a coin flip. Claude might create random endpoints, ignore existing patterns, skip tests, and produce inconsistent code. The codebase drifts toward entropy with every interaction.

**Agentic Engineering (100%)** is when Claude Code operates as a fully configured engineering system. It knows the project architecture (CLAUDE.md), follows scoped conventions (Rules), loads domain expertise on demand (Skills), delegates to specialized workers (Agents), orchestrates multi-step workflows (Commands), automates lifecycle events (Hooks), and connects to external tools (MCP Servers). Every prompt produces consistent, tested, production-quality code.

The journey between these two extremes is **incremental and cumulative**. Each best practice builds on the previous ones, and the presentation teaches them in the order a developer should adopt them.

## The Running Example: TodoApp Monorepo

Every technique is demonstrated on a realistic full-stack project. The presentation shows the transformation from a plain project (vibe coding) to one with full Claude Code configuration (agentic engineering):

**Before (Vibe Coding):**
```
todoapp/
├── backend/          # FastAPI (Python)
│   ├── main.py
│   ├── routes/
│   ├── models/
│   └── tests/
└── frontend/         # Next.js (TypeScript)
    ├── components/
    ├── pages/
    └── lib/
```

**After (Agentic Engineering):**
```
todoapp/
├── .claude/                  # Claude Code config
│   ├── agents/               # Custom subagents
│   ├── skills/               # Domain knowledge
│   ├── commands/             # Slash commands
│   ├── hooks/                # Lifecycle scripts
│   ├── rules/                # Modular instructions
│   ├── settings.json         # Team settings
│   └── settings.local.json   # Personal settings
├── backend/
│   └── CLAUDE.md             # Backend instructions
├── frontend/
│   └── CLAUDE.md             # Frontend instructions
├── .mcp.json                 # Managed MCP servers
└── CLAUDE.md                 # Project instructions
```

**Why TodoApp?** It's small enough to fit on slides but complex enough to demonstrate real problems: a backend with route patterns and test conventions, a frontend with component hierarchy and design tokens, and a monorepo structure where cross-cutting concerns (like adding a new feature) require coordination between both sides.

The TodoApp makes the vibe-coding problem concrete: without structure, asking Claude to "add a notes feature" produces a random `/api/notes` endpoint that doesn't follow `routes/todos.py` patterns, a standalone page with no sidebar navigation, and zero tests. With full agentic setup, the same request produces a route following existing patterns, a page integrated into the sidebar, and tests matching `test_todos.py` style.

## The Journey Arc: Why This Order

The presentation follows a deliberate pedagogical sequence. Each section unlocks a new capability layer:

### Part 0: Introduction (Slides 1–4, no weight)
**Purpose:** Set the stage. Introduce the TodoApp, define vibe coding, and show the destination.
- Title slide establishes the journey metaphor
- Example Project shows the transformation: before/after comparison of TodoApp — plain project structure vs one with full Claude Code configuration (.claude/, CLAUDE.md, .mcp.json, etc.)
- "What is Vibe Coding?" creates the 0% baseline — the pain point
- Journey Map provides a clickable TOC showing the full path ahead

### Part 1: Prerequisites (Slides 5–9, no weight)
**Purpose:** Get Claude Code installed and running. This is purely logistical — no engineering practices yet.
- Installing, authentication, first session, interface overview
- No weight because knowing how to install a tool doesn't improve code quality
- The "first session" IS vibe coding — this is intentional, so the developer experiences the 0% state firsthand

### Part 2: Better Prompting (Slides 10–17, journey 0% → 20%)
**Purpose:** The first real improvement. Better inputs produce better outputs, even without any project configuration.
- **Good vs Bad Prompts (+5%):** Specific, scoped prompts vs vague requests. The simplest possible improvement.
- **Providing Context (+5%):** Using `@files` to give Claude the code it needs. Reduces hallucination immediately.
- **Context Window & /compact (+5%):** Understanding the finite context window prevents degraded responses in long sessions.
- **Plan Mode (+5%):** `/plan` forces thinking before coding. Prevents wasted effort on wrong approaches.

**Why 20% total:** Prompting is foundational but limited. It improves individual interactions but doesn't create lasting project knowledge. Each session starts from zero.

### Part 3: Project Memory (Slides 18–24, journey 20% → 40%)
**Purpose:** The leap from session-level to project-level knowledge. Claude now remembers across sessions.
- **CLAUDE.md & /init (+5%):** The project's "README for Claude." Establishes architecture, tech stack, and conventions. This is the single most impactful file.
- **What to Include (+5%):** Practical guidance on writing effective CLAUDE.md content (keep under 150 lines, focus on what Claude needs to know).
- **Rules (+10%):** Path-scoped conventions in `.claude/rules/`. This gets **double weight** because rules are a multiplier — they apply automatically to every matching file, enforcing consistency without developer effort. A single `backend-testing.md` rule ensures every test follows the same pattern forever.

**Why 20% total:** Project memory transforms Claude from a stateless tool into a context-aware collaborator. But knowledge alone doesn't create workflows.

### Part 4: Structured Workflows (Slides 25–28, journey 40% → 50%)
**Purpose:** Systematic approaches that prevent wasted effort and improve execution quality.
- **Task Lists (+5%):** Breaking complex work into trackable steps. Prevents scope drift and ensures completeness.
- **Model Selection (+5%):** Choosing the right model (Opus for architecture, Sonnet for implementation, Haiku for quick tasks) optimizes cost and quality.

**Why 10% total:** Workflows are important but relatively simple concepts. They're enablers for the more powerful systems that follow.

### Part 5: Domain Knowledge (Slides 29–33, journey 50% → 65%)
**Purpose:** Reusable, on-demand expertise. Skills are the bridge between static memory (CLAUDE.md/Rules) and dynamic agents.
- **What Are Skills (+5%):** Skills as packaged domain knowledge that Claude loads when relevant. The concept of progressive disclosure.
- **Creating Skills (+5%):** Hands-on: building a `frontend-conventions` skill for the TodoApp that teaches Tailwind tokens, component patterns, and sidebar integration.
- **Skill Frontmatter & Invocation (+5%):** The technical details: YAML frontmatter, manual vs auto-discovery invocation, the `context: fork` option.

**Why 15% total:** Skills are the first "multiplier" concept — one skill definition improves every future interaction in its domain. But skills are passive knowledge; they need agents to become active.

### Part 6: Agentic Engineering (Slides 34–46, journey 65% → 100%)
**Purpose:** The destination. Autonomous, specialized agents that coordinate to build features end-to-end.
- **What Are Agents (+5%):** The concept of specialized subagents with constrained tools and preloaded skills.
- **Frontend Engineer Agent (+5%):** A concrete agent that uses the TodoApp's frontend conventions, adds routes to sidebar, follows design tokens. Before/after comparison shows the transformation.
- **Backend Engineer Agent (+5%):** Parallel agent for the backend — follows FastAPI route patterns, SQLAlchemy models, writes tests matching existing style.
- **Commands & Orchestration (+10%):** Double weight because commands are the **capstone pattern**: Command → Agent → Skills. A single `/add-feature` command coordinates frontend + backend agents, each with their own skills, to deliver a complete feature. This is the architectural pinnacle.
- **Hooks & MCP (+5%):** Lifecycle automation (pre-commit checks, sound notifications) and external tool integration. The final automation layer.
- **Command → Agent → Skills (+5%):** The full architecture diagram. Shows how all pieces connect: commands invoke agents, agents load skills, skills provide knowledge. This is the "100% understanding" slide.

**Why 35% total:** This section is the entire point of the presentation. Everything before it was building toward this. The heavy weighting (especially 10% on Commands) reflects that orchestration is the highest-value capability.

### The 100% Slide (Slide 44)
The celebration moment. Shows the complete TodoApp configuration:
- CLAUDE.md for project context
- Rules for path-scoped conventions
- Skills for domain knowledge
- Agents for consistent execution
- Commands for orchestrated workflows
- Hooks for lifecycle automation
- MCP servers for external tools

### Appendix (Slides 47+, no weight)
**Purpose:** Reference material. Every command, setting, and configuration option. No weight because these are reference lookups, not journey milestones. Includes: tool usage, all slash commands, commit/PR workflows, customization options, debugging tips, and golden rules.

## How to Use This Framework When Editing Slides

When creating or modifying slides, consider:

1. **Where does this concept sit on the journey?** A slide about "better error messages in prompts" belongs in Part 2 (prompting). A slide about "agent memory scopes" belongs in Part 6 (agentic).

2. **What's the before/after?** Every weighted slide should implicitly or explicitly show the contrast: what happens at 0% (vibe coding) vs what happens with this technique. Use the TodoApp to make it concrete.

3. **Does the weight feel right?** Foundational but simple concepts get +5%. Multiplier concepts that affect everything downstream get +10%. The total must stay at 100%.

4. **Does it build on what came before?** Skills assume the developer already knows about CLAUDE.md and Rules. Agents assume they know about Skills. Commands assume they know about Agents. Never reference a concept before its section.

5. **Use the TodoApp.** Abstract explanations lose the audience. Show the actual `routes/todos.py` code, the actual `Sidebar.tsx` component, the actual `CLAUDE.md` content. The running example is what makes the framework tangible.

## Weight Reference Table

| # | Slide Name | Section | Weight |
|---|-----------|---------|--------|
| 12 | Good vs Bad Prompts | Part 2: Better Prompting | +5% |
| 13 | Providing Context | Part 2: Better Prompting | +5% |
| 14 | Context Window & /compact | Part 2: Better Prompting | +5% |
| 15 | /plan — Plan Before Code | Part 2: Better Prompting | +5% |
| 19 | CLAUDE.md & /init | Part 3: Project Memory | +5% |
| 20 | What to Include in CLAUDE.md | Part 3: Project Memory | +5% |
| 22 | Rules (.claude/rules/) | Part 3: Project Memory | +10% |
| 26 | Task Lists | Part 4: Structured Workflows | +5% |
| 27 | /model — Model Selection | Part 4: Structured Workflows | +5% |
| 30 | What Are Skills? | Part 5: Domain Knowledge | +5% |
| 31 | Creating Skills: TodoApp Frontend | Part 5: Domain Knowledge | +5% |
| 32 | Skill Frontmatter & Invocation | Part 5: Domain Knowledge | +5% |
| 35 | What Are Agents? | Part 6: Agentic Engineering | +5% |
| 36 | Frontend Engineer Agent | Part 6: Agentic Engineering | +5% |
| 37 | Backend Engineer Agent | Part 6: Agentic Engineering | +5% |
| 41 | Commands & Orchestration | Part 6: Agentic Engineering | +10% |
| 42 | Hooks & MCP Servers | Part 6: Agentic Engineering | +5% |
| 43 | Command → Agent → Skills | Part 6: Agentic Engineering | +5% |
| | | **Total** | **100%** |
