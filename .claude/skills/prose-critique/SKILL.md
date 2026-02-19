---
name: prose-critique
description: >
  Deep critique of a prose passage or scene using professional fiction
  editing standards. Evaluates craft elements: sensory detail, dialogue
  mechanics, deep POV, micro-tension, subtext, and prose rhythm.
  Use for detailed feedback on specific scenes or passages.
argument-hint: <paste text or "chapter 3 scene 2" or codex path>
allowed-tools:
  - Read
  - Bash(jq:*)
---

# Prose Critique (Professional Fiction Standards)

Perform a detailed craft-level critique of prose text.

## Input
$ARGUMENTS can be:
- Inline prose text to critique
- A scene reference like "chapter 3 scene 2" (will load from most recent codex)
- A codex file path + scene coordinates

## Critique Framework

### 1. Deep POV & Psychic Distance
- Is the reader inside the character's head or observing from outside?
- Filter words creating distance? (felt, saw, noticed, heard, thought, realized)
- Does the prose use free indirect discourse? (character's thoughts without "he thought")
- **Good**: "The room stank of copper. Blood, then." **Bad**: "She noticed the smell of blood."

### 2. Sensory Immersion
- How many of the 5 senses are engaged? (aim for 2+ non-visual per scene)
- Are sensory details specific and concrete, or generic?
- Do sensory details serve double duty (atmosphere + characterization)?
- **Good**: "The leather of the chair creaked as he leaned forward, cold and stiff." **Bad**: "It was a nice room."

### 3. Dialogue Craft
- Does each character have a distinct voice pattern (vocabulary, rhythm, tics)?
- Is there subtext (what's NOT said matters more than what is)?
- Are dialogue tags invisible ("said") or distracting ("exclaimed", "retorted")?
- Action beats between dialogue lines? ("She set down the cup. 'That's not what I meant.'")

### 4. Micro-Tension (Sol Stein)
- Does every paragraph contain some form of tension, question, or forward pull?
- Are there "dead spots" where nothing is at stake?
- Does the scene end with a hook or turn?
- Tension types: disagreement, uncertainty, time pressure, secret, dilemma, unasked question

### 5. Prose Rhythm
- Is sentence length varied? (short for impact, long for atmosphere)
- Active/passive voice ratio (aim for 80/20 active)
- Paragraph breaks at moments of impact?
- One-sentence paragraphs used sparingly for emphasis?

### 6. Specificity & Precision
- Nouns concrete and specific? ("oak" not "tree", "Glock" not "gun")
- Verbs active and precise? ("lunged" not "moved quickly")
- Adverbs earning their place or replaceable with stronger verbs?
- Adjectives specific or generic filler?

## Output

1. **Line-by-line annotations** where craft issues occur (quote the text, explain the issue, suggest a fix)
2. **Top 3 strengths** - what this prose does well
3. **Top 3 weaknesses** - most impactful improvements
4. **Rewrite** of the weakest paragraph demonstrating the fixes
5. **Craft score**: 1-10 with breakdown per dimension