# Step 0: Theme Foundation - Test Instructions

## What Was Implemented

**Step 0 now uses 3-substep multi-agent debate structure:**

### Substep 1: Theme Question Debate
- **Agents:** ThemePhilosopherAgent, ThemeEmotionalAgent, ThemeDramaticAgent
- **Process:** Propose → Critique → Vote
- **Output:** 1 winning thematic question

### Substep 2: Thematic Square Debate
- **Agents:** SquareArchitectAgent, SquareCharacterAgent, SquareConflictAgent
- **Process:** Propose → Critique → Vote
- **Output:** 1 winning thematic square (4 corners: positive, contradictory, contrary, negation)

### Substep 3: Perspective Set Debate
- **Agents:** PerspectiveDiversityAgent, PerspectiveStoryAgent, PerspectiveBalanceAgent
- **Process:** Propose → Critique → Vote
- **Output:** 1 winning set of 4 character perspectives

---

## How to Test

### Command

```bash
# Test with any existing codex file:
uv run python -m src.phases.phase1_author forge/20260208153351/codex_20260208153351.json --steps 0
```

### Available Test Codex Files

```bash
# Option 1:
uv run python -m src.phases.phase1_author forge/20260208153351/codex_20260208153351.json --steps 0

# Option 2:
uv run python -m src.phases.phase1_author forge/20260201230516/codex_20260201230516.json --steps 0

# Option 3:
uv run python -m src.phases.phase1_author forge/20260207200812/codex_20260207200812.json --steps 0
```

---

## What You'll See

The output will show:

```
============================================================
PHASE 1: AUTHOR-DRIVEN STORY CREATION
============================================================
>>> Codex: forge/xxx/codex_xxx.json
>>> Model: ...
>>> Author: ...
>>> Running steps: [0]

============================================================
STEP 0: Theme Foundation (Theme → Character → Plot)
============================================================

>>> Logline: [your logline]
>>> Setting: [your setting]...

============================================================
SUBSTEP 1: THEME QUESTION DEBATE
============================================================

>>> Phase 1: Proposals (3 agents)
    - THEME_PHILOSOPHER proposing...
      → [Philosophical question]
    - THEME_EMOTIONAL proposing...
      → [Emotional question]
    - THEME_DRAMATIC proposing...
      → [Dramatic question]

>>> Phase 2: Critiques (each agent critiques all 3 proposals)
    - THEME_PHILOSOPHER critiquing...
      Proposal 0: 8.5/10
      Proposal 1: 7.0/10
      Proposal 2: 9.0/10
    - THEME_EMOTIONAL critiquing...
      [... scores for all proposals ...]
    - THEME_DRAMATIC critiquing...
      [... scores for all proposals ...]

>>> Phase 3: Voting (each agent votes for best)
    - THEME_PHILOSOPHER votes for Proposal 2
    - THEME_EMOTIONAL votes for Proposal 0
    - THEME_DRAMATIC votes for Proposal 2

>>> WINNER: Proposal 2 (2 votes)
>>> CENTRAL QUESTION: [The winning thematic question]

============================================================
SUBSTEP 2: THEMATIC SQUARE DEBATE
============================================================

>>> Phase 1: Proposals (3 agents)
    - SQUARE_ARCHITECT proposing...
      POSITIVE: [Truth statement]
      CONTRADICTORY: [Lie statement]
    - SQUARE_CHARACTER proposing...
      POSITIVE: [Truth statement]
      CONTRADICTORY: [Lie statement]
    - SQUARE_CONFLICT proposing...
      POSITIVE: [Truth statement]
      CONTRADICTORY: [Lie statement]

>>> Phase 2: Critiques (each agent critiques all 3 squares)
    - SQUARE_ARCHITECT critiquing...
      Proposal 0: 8.0/10
      Proposal 1: 7.5/10
      Proposal 2: 9.0/10
    [... more critiques ...]

>>> Phase 3: Voting (each agent votes for best)
    - SQUARE_ARCHITECT votes for Proposal 1
    - SQUARE_CHARACTER votes for Proposal 1
    - SQUARE_CONFLICT votes for Proposal 0

>>> WINNER: Proposal 1 (2 votes)
>>> THEMATIC SQUARE:
    POSITIVE: [Truth]
    CONTRADICTORY: [Lie]
    CONTRARY: [Nuanced negative]
    NEGATION: [Extreme]

============================================================
SUBSTEP 3: PERSPECTIVE SET DEBATE
============================================================

>>> Phase 1: Proposals (3 agents propose sets of 4 perspectives)
    - PERSPECTIVE_DIVERSITY proposing...
      - The Unmasked Warrior (positive)
      - The Protective Phantom (contradictory)
      - The Burned Idealist (contrary)
      - The Shapeshifter (negation_of_negation)
    - PERSPECTIVE_STORY proposing...
      [... 4 perspectives ...]
    - PERSPECTIVE_BALANCE proposing...
      [... 4 perspectives ...]

>>> Phase 2: Critiques (each agent critiques all 3 sets)
    - PERSPECTIVE_DIVERSITY critiquing...
      Proposal 0: 8.5/10
      Proposal 1: 7.0/10
      Proposal 2: 9.0/10
    [... more critiques ...]

>>> Phase 3: Voting (each agent votes for best set)
    - PERSPECTIVE_DIVERSITY votes for Proposal 0
    - PERSPECTIVE_STORY votes for Proposal 2
    - PERSPECTIVE_BALANCE votes for Proposal 0

>>> WINNER: Proposal 0 (2 votes)
>>> PERSPECTIVES:
    - The Unmasked Warrior (positive)
      Position: [Their stance on the theme]
    - The Protective Phantom (contradictory)
      Position: [Their stance on the theme]
    [... more perspectives ...]

============================================================
STEP 0 COMPLETE! Duration: 45.3s
============================================================

>>> Codex saved to: forge/xxx/codex_xxx.json
>>> Phase 1 complete!
>>> Steps completed: [0]
```

---

## Output in Codex

After running, open the codex JSON file and you'll find:

```json
{
  "story": {
    "theme": {
      "central_question": "The winning thematic question",
      "question_debate": {
        "proposals": [
          {
            "agent_name": "THEME_PHILOSOPHER",
            "question": "...",
            "explanation": "...",
            "reasoning": "..."
          }
          // ... 2 more proposals
        ],
        "critiques": [
          {
            "agent_name": "THEME_PHILOSOPHER",
            "proposal_index": 0,
            "strengths": "...",
            "weaknesses": "...",
            "score": 8.5
          }
          // ... 8 more critiques (3 agents × 3 proposals)
        ],
        "votes": [
          {
            "agent_name": "THEME_PHILOSOPHER",
            "voted_for_index": 2,
            "vote_reasoning": "..."
          }
          // ... 2 more votes
        ],
        "winner_index": 2
      },
      "thematic_square": {
        "positive": "...",
        "contradictory": "...",
        "contrary": "...",
        "negation_of_negation": "..."
      },
      "square_debate": {
        "proposals": [...],
        "critiques": [...],
        "votes": [...],
        "winner_index": 1
      },
      "perspectives": [
        {
          "perspective_name": "The Unmasked Warrior",
          "position": "...",
          "corner": "positive",
          "example_belief": "..."
        }
        // ... 3 more perspectives
      ],
      "perspective_debate": {
        "proposals": [...],
        "critiques": [...],
        "votes": [...],
        "winner_index": 0
      }
    }
  }
}
```

---

## What to Test For

1. **Theme Question Quality:**
   - Are the 3 proposed questions distinct?
   - Does the winner feel appropriate for the story?
   - Are critiques insightful?

2. **Thematic Square Quality:**
   - Are the 4 corners (positive, contradictory, contrary, negation) truly distinct?
   - Is CONTRADICTORY genuinely opposite of POSITIVE?
   - Does CONTRARY show nuance (not just negativity)?
   - Is NEGATION the worst-case extreme?

3. **Perspective Quality:**
   - Are the 4 perspectives genuinely different?
   - Do they map to different corners of the square?
   - Are the names memorable and fitting?
   - Would real characters believably hold these worldviews?

4. **Debate Process:**
   - Do critiques reflect agent specializations? (Philosopher = depth, Emotional = resonance, Dramatic = conflict)
   - Do votes align with critique scores?
   - Are winning proposals deserving?

---

## Known Issues / Things to Check

1. **Vote ties:** If 3 agents vote and there's a 3-way tie, `max()` will pick the first. May need tiebreaker logic.
2. **Agent consistency:** Check if agents vote for themselves too often.
3. **Perspective corner coverage:** Should always include positive and contradictory, check if this is enforced.
4. **Performance:** Step 0 makes 27 LLM calls (9 agents × 3 operations each). Should take ~1-2 minutes.

---

## Iteration Notes

After testing, recommend changes for:
- Agent prompts (if output quality is poor)
- Critique criteria (if scores don't make sense)
- Voting logic (if winners seem wrong)
- Number of perspectives (currently hardcoded to 4)
- Output verbosity (currently very detailed)

Test with 2-3 different codex files to see variety in outputs!
