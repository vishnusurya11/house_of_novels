# Story Improvement Plan

> **Mission:** Create a Phase 1 system that generates stories with deep thematic coherence, complex characters, and organic conflict - not "basic stories."

---

## 🌍 10,000-Foot View: The Strategic Shift

### Why Current Stories Feel "Basic"

**The Root Problem:** Our current system approaches story in the wrong order:
1. Generate plot structure (7-point beats)
2. Create characters to fill structural roles
3. Write scenes via agent debate (winner-takes-all)
4. Hope theme and meaning emerge

**What This Produces:**
- Characters that feel like plot devices
- Conflict that feels contrived
- Themes that feel tacked-on
- Prose that varies wildly in quality (different agent wins each scene)
- No emotional through-line

### The Paradigm Shift: Theme → Character → Plot

**Research-Backed Truth** (from K.M. Weiland, John Truby, Save the Cat, and professional writers):

> "Plot, Character, and Theme are not separate elements - they are a circular, regenerative relationship. **Theme creates character, character creates plot, plot reinforces theme.**"

**The New Approach:**

```
Logline (contains thematic seed)
    ↓
STEP 0: Extract Theme & Build Thematic Square
    ↓
STEP 1: Create Characters as Thematic Perspectives
    (Each character = different answer to theme's central question)
    ↓
STEP 2: Choose Story Shape + Genre
    (The container that pressures the theme)
    ↓
STEP 3: Build Plot Structure
    (Events that force thematic perspectives to clash)
    ↓
STEP 4: World Building
    (World rules/locations that reinforce theme)
    ↓
STEP 5: Scene Outline
    (Every scene tests the thematic question)
    ↓
STEP 6: Prose Generation (IMPROVED)
    (Synthesis system + higher word count + real-time critique)
    ↓
STEP 7: Revision & Polish
    (Voice consistency, emotional arc validation, theme resonance)
```

### Why This Will Create "Fucking Awesome Stories"

**1. Organic Conflict**
- Characters naturally clash because they hold **competing thematic beliefs**
- No need to manufacture drama - it emerges from genuine philosophical differences
- Example: If theme is "Does power corrupt?", characters embody different answers:
  - Character A: "Power reveals true character"
  - Character B: "Power always corrupts"
  - Character C: "Power is necessary despite its costs"
  - Put them in a situation involving power → instant meaningful conflict

**2. Deep Character Complexity**
- **Lie/Truth System:** Every character believes a Lie and must discover a Truth
- **Shadow Theory:** Characters have unconscious opposites to their conscious traits
- **Character Arcs:** Five distinct arc types (Positive Change, Flat, Disillusionment, Fall, Corruption)
- Characters aren't just plot functionaries - they're explorations of human psychology

**3. Thematic Coherence**
- Every element serves the theme: characters, plot, world, even individual scenes
- Theme isn't "the moral of the story" - it's the **question the story explores**
- Readers feel the depth even if they can't articulate why

**4. Better Prose Quality**
- **Synthesis over Selection:** Don't pick one agent's prose - blend best elements from all
- **Real-Time Critique:** Fix issues immediately, not in bulk revision
- **Higher Word Count:** 1500-2000 words/scene allows real "show don't tell"
- **Iterative Refinement:** Revise scene based on critiques before moving on

**5. Emotional Resonance**
- Character arcs are tied to thematic exploration
- Plot beats align with character transformation beats
- Readers experience theme emotionally, not intellectually

### The Mental Model Shift

**Old Model (Current System):**
- Story Shape = Plot
- Genre = Flavor
- Theme = Message
- Characters = Roles

**New Model (Research-Backed):**
- **Story Shape** = The journey type (7 Classic Plots)
- **Theme** = The central question being explored
- **Characters** = Perspectives on the theme
- **Plot** = Events that force thematic perspectives to clash
- **Genre** = The pressure/delivery mode
- **Beats** = When things happen (Save the Cat)
- **Prose** = How it's expressed (ScreenplayStyle)

These are **orthogonal systems** that layer together, not competing approaches.

---

## 📋 Proposed Phase 1 Steps (New Order)

### Overview

| Step | Name | What It Does | Why This Order |
|------|------|--------------|----------------|
| 0 | Theme Foundation | Extract theme from logline, build Thematic Square | Theme is the generative core - must come first |
| 1 | Character Creation | Generate characters as thematic perspectives using Lie/Truth + Shadow Theory | Characters emerge from theme, not structure |
| 2 | Story Shape & Genre | Choose Classic Plot + Save the Cat type + Genre(s) | Now we know what journey will best explore our theme |
| 3 | Plot Structure | Apply Save the Cat beats + character arc beats + Try-Fail cycles | Structure emerges from characters + theme, not vice versa |
| 4 | World Building | Create locations/world rules that reinforce theme | World pressures the thematic question |
| 5 | Scene Outline | Chapter/scene breakdown where each scene tests theme | Subplots woven in, all serving theme |
| 6 | Prose Generation | IMPROVED system with synthesis + higher word count | Write with thematic coherence |
| 7 | Revision & Polish | Voice consistency, emotional arc, theme resonance | Final refinement |

### Why This Order Works

**Theme → Characters → Plot** is the sequence used by professional writers (confirmed by K.M. Weiland, John Truby, and the writer in your video transcript).

**Key Quote from Research:**
> "Take a theme. What are all the potential perspectives one could have on that theme? Let's take each perspective and turn it into a character. Boom - cast. Don't include characters who have nothing to say about your theme."

This is the opposite of our current approach (structure → characters → hope theme emerges).

---

## 🎯 Detailed Phase 1 Implementation

---

### STEP 0: Theme Foundation

**Goal:** Extract the thematic question from the logline and build a Thematic Square to explore it from multiple angles.

#### Input
- `codex["story_engine"]["prompts"]` - The generated logline
- `codex["deck_of_worlds"]["prompts"]` - World context

#### Methodology

**1. Extract Theme from Logline**

Your example logline:
> "TRAUMATIC AN IMPOSTOR WANTS TO SAVE A LIFE WITH/FROM A DOCUMENT BUT IT MEANS RISKING THE THING MOST PRECIOUS TO THEM"

Extract thematic questions:
- **Identity vs. Truth:** Is authenticity worth the cost?
- **Sacrifice:** What are you willing to lose for what you believe is right?
- **Impostor Syndrome:** Can someone "fake" still do real good?

Choose the **central thematic question** that will drive the story.

**2. Build the Thematic Square** (Robert McKee's methodology)

The Thematic Square has four corners:

```
POSITIVE (The Truth)                    CONTRADICTORY (The Lie)
    ↓                                           ↓
Example: Authenticity liberates         Example: Deception protects
    ↓                                           ↓
CONTRARY (Nuanced negative)             NEGATION OF NEGATION (Extreme)
    ↓                                           ↓
Example: Authenticity isolates          Example: Total self-destruction
```

**Purpose:** This square shows that theme isn't binary (good vs. bad) - it's a spectrum of perspectives.

**3. Identify Core Thematic Perspectives**

From the Thematic Square, identify 3-5 distinct perspectives that characters will embody.

Example for "Identity vs. Truth" theme:
- Perspective A: "Truth is worth any cost" (idealist)
- Perspective B: "Some lies protect people" (pragmatist)
- Perspective C: "Identity is performance - there is no 'real' self" (cynic)
- Perspective D: "You become who you pretend to be" (optimist)

These will become your character cast in Step 1.

#### Output
- `codex["story"]["theme"]["central_question"]` - The thematic question driving the story
- `codex["story"]["theme"]["thematic_square"]` - The four corners exploring theme
- `codex["story"]["theme"]["perspectives"]` - 3-5 thematic perspectives for characters
- `codex["story"]["theme_foundation"]["adjective"]` - 🔴 **FUTURE**: Logline adjective (e.g., "DECOY")
- `codex["story"]["theme_foundation"]["adjective_meaning"]` - 🔴 **FUTURE**: Why protagonist is in this state
- `codex["story"]["theme_foundation"]["hero_role"]` - 🔴 **FUTURE**: Protagonist role from logline

#### References
- [Plot, Character, and Theme: The Greatest Love Triangle](https://www.helpingwritersbecomeauthors.com/plot-character-and-theme-the-greatest-love-triangle-in-fiction/)
- [Deepening Theme with Thematic Square](https://www.helpingwritersbecomeauthors.com/deepening-your-storys-theme-with-the-thematic-square/)
- [What is Theme?](https://www.helpingwritersbecomeauthors.com/storys-theme-2/)

---

### STEP 1: Character Creation (Theme → Characters)

**Goal:** Generate characters who embody different perspectives on the theme, giving them psychological depth via Lie/Truth and Shadow Theory.

#### Input
- `codex["story"]["theme"]` (from Step 0)
- `codex["story_engine"]["prompts"]` (logline context)

#### Methodology

**1. Characters as Thematic Perspectives**

Take each perspective from Step 0's Thematic Square and create a character who embodies it.

**Key Principle:**
> "Each character must have a unique perspective on the theme. If they don't, they're taking up space."

Example (continuing "Identity vs. Truth"):
- **Character A (Protagonist):** Impostor who believes "If people knew the real me, they'd reject me" (Lie) → must learn "Authenticity creates connection" (Truth)
- **Character B (Ally):** Friend who believes "Truth is sacred" - challenges protagonist (Flat Arc - already knows Truth)
- **Character C (Antagonist):** Person who believes "Identity is what you make others believe" - actively opposes protagonist's journey
- **Character D (Relationship Character):** Someone stuck in their own lie about identity - parallel arc

**2. Apply Lie/Truth System** (K.M. Weiland)

For EACH character:

**Define the Lie the Character Believes:**
- A specific misconception (one sentence)
- Something they think is protecting them
- Creates their internal conflict

**Define the Truth They Need to Learn:**
- The liberating insight that replaces the Lie
- May have multiple facets
- Drives their character arc

**Define the Want vs. Need:**
- **Want:** External goal (what they think they need)
- **Need:** Internal truth (what they actually need)
- Story forces them to choose

Example:
- **Lie:** "If I reveal my true identity, I'll lose everything"
- **Truth:** "Pretending to be someone else costs more than the risk of authenticity"
- **Want:** Save the life without being discovered
- **Need:** Accept their true self

**3. Choose Character Arc Type**

Based on the Lie/Truth relationship, assign an arc type:

| Arc Type | Journey | When to Use |
|----------|---------|-------------|
| **Positive Change** | Overcomes Lie → Discovers Truth | Protagonist in most stories |
| **Flat Arc** | Already knows Truth → Changes world | Mentor, hero in sequel, moral anchor |
| **Disillusionment Arc** | Overcomes Lie → Discovers tragic Truth | Tragic revelations |
| **Fall Arc** | Clings to Lie → Rejects Truth → Embraces worse Lie | Tragic descent |
| **Corruption Arc** | Starts with Truth → Rejects it → Embraces Lie | Villain origin, dark transformation |

**4. Apply Shadow Theory** (Jungian Psychology)

For depth, identify each character's **Shadow** (unconscious opposite of conscious traits):

**Shadow Questions:**
- Greatest strength → Hidden weakness?
- Strongest conviction → Secret doubt?
- What they vilify → What they secretly desire?
- What they revere → What they secretly fear?

Example:
- **Conscious:** Protagonist presents as confident impostor
- **Shadow:** Deep insecurity and self-loathing
- **Story Arc:** Must integrate shadow (accept insecurity) to become whole

**5. Generate Character Details**

Now that psychology is defined, generate:
- **Physical Appearance:** Shadow theory insight: external reflects internal (or contrasts it)
- **Backstory (Ghost):** What event created the Lie?
- **Quirks/Voice:** How does their thematic belief manifest in behavior?

**6. Name Characters**

Use existing 3-agent name debate (NameCreativeAgent, NameAuthenticAgent, NameDistinctiveAgent) - but now names should reflect thematic position if possible.

**7. Logline Adjective Integration (Protagonist)**

**CRITICAL REQUIREMENT:** The logline's adjective defines the protagonist's starting emotional/psychological state and MUST be integrated into their character psychology.

**Example:**
- Logline: "**DECOY** A THERAPIST WANTS TO PROTECT A BOAT BUT IT MAY COST THEM THEIR LIFE"
- Adjective: "DECOY" (deceptive, hiding true nature, false front)
- This MUST inform the protagonist's Lie/Truth, Shadow, and Ghost

**Implementation:**
1. Parse the logline adjective in Step 0 (Theme Foundation)
2. Store in `codex["story"]["theme_foundation"]["adjective"]` + `adjective_meaning`
3. In Step 1, for the PROTAGONIST only (positive corner character):
   - Pass adjective as context to Lie/Truth debate agents
   - Lie should connect to WHY protagonist is in this adjective state
   - Truth represents transformation FROM adjective state
   - Shadow traits should reflect the adjective's psychological implications
   - Ghost event should explain what created this adjective state

**Agent Updates Required:**
- LieTruthPhilosopherAgent, LieTruthPsychologistAgent, LieTruthNarrativeAgent
  - Add optional `adjective_context` parameter to `propose_lie_truth()` method
  - Prompts should incorporate adjective when provided for protagonist

**Example Integration for "DECOY A THERAPIST":**
- **Lie**: "I must maintain a false front to protect others from my damaged self"
- **Truth**: "Authentic vulnerability allows genuine connection and healing"
- **Want**: To be seen as trustworthy while hiding inner turmoil
- **Need**: To integrate authentic self with professional role
- **Shadow**: Conscious "Appears trustworthy" → Unconscious "Manipulates others' trust"
- **Ghost**: Event where honesty led to devastating betrayal → learned deception as survival

**Why This Matters:**
- Grounds abstract thematic character in concrete story trait from logline
- Connects Step 0 (theme) and Step 1 (characters) to story seed
- Ensures protagonist embodies the logline's defining characteristic
- Supporting/antagonist characters stay purely thematic
- Protagonist gets both thematic depth AND concrete character grounding

**Implementation Status:** 🔴 **NOT YET IMPLEMENTED** - This is planned for future work on Steps 0 and 1.

#### Agent System

**Proposed Agents:**
1. **ThematicCharacterAgent:** Generates character psychology from thematic perspective
2. **LieTruthAgent:** Defines Lie, Truth, Want, Need for character
3. **ShadowAgent:** Identifies shadow traits using Jungian questions
4. **ArcTypeAgent:** Assigns appropriate arc type based on story role
5. Existing physical/name agents for surface details

#### Output
- `codex["story"]["characters"]` - List of character objects with:
  - `thematic_perspective` - Which theme perspective they embody
  - `role` - Story function (protagonist/antagonist/supporting)
  - `adjective` - (Protagonist only) Logline adjective defining starting state
  - `adjective_meaning` - (Protagonist only) Why they're in this state
  - `lie_character_believes` - Their core misconception
  - `truth_character_needs` - The liberating insight
  - `want_vs_need` - External goal vs. internal need
  - `arc_type` - Which of 5 arc types
  - `shadow_traits` - Unconscious opposites (Jungian)
  - `ghost` - Backstory event that created the Lie
  - Physical/psychological details (as before)

#### References
- [Character Arcs Overview](https://www.helpingwritersbecomeauthors.com/write-character-arcs/)
- [The Lie Your Character Believes](https://www.helpingwritersbecomeauthors.com/truth-your-character-believes/)
- [Positive Character Arc](https://www.helpingwritersbecomeauthors.com/write-character-arcs/#positive)
- [Flat Character Arc](https://www.helpingwritersbecomeauthors.com/flat-character-arc-1/)
- [Negative Character Arcs](https://www.helpingwritersbecomeauthors.com/negative-character-arc-1/)
- [5 Arc Types at a Glance](https://www.helpingwritersbecomeauthors.com/learn-5-types-of-character-arc-at-a-glance/)
- [Shadow Theory for Complex Characters](https://www.helpingwritersbecomeauthors.com/how-to-create-insanely-complex-characters-using-shadow-theory/)

---

### STEP 2: Story Shape & Genre Selection

**Goal:** Choose the narrative container (Story Shape + Genre) that will best explore the theme and character arcs.

#### Input
- `codex["story"]["theme"]` (from Step 0)
- `codex["story"]["characters"]` (from Step 1)
- `codex["story_engine"]["prompts"]` (logline)

#### Methodology

**1. Choose Classic Story Shape (7 Plots)**

Match the logline's journey type to one of the 7 Classic Plots:

| Story Shape | Core Journey | Emotional Promise | Best For |
|-------------|--------------|-------------------|----------|
| **Overcoming the Monster** | Evil threatens → hero confronts | Safety restored through courage | Action, Horror, Fantasy, Superhero |
| **Rags to Riches** | Overlooked → rises to greatness | Worth can be revealed/earned | Coming-of-age, Romance, Sports |
| **The Quest** | Journey to obtain goal | Meaning through striving | Fantasy, Adventure, Epic sci-fi |
| **Voyage and Return** | Enter strange world → return changed | Exploration transforms identity | Portal fantasy, Sci-fi, Psychological |
| **Comedy** | Confusion → harmony restored | Chaos resolves into connection | Romance, Social drama, Ensemble |
| **Tragedy** | Flawed character → downfall | Some mistakes cannot be undone | Psychological drama, Political, Dark fantasy |
| **Rebirth** | Corrupted/imprisoned → redeemed | Change through sacrifice/love | Redemption arcs, Emotional drama |

**Your Logline Example:**
> "Impostor wants to save a life with/from a document but risks what's most precious"

**Best Matches:**
- **The Quest:** Journey to obtain/use the document
- **Rebirth:** Impostor must shed false identity to succeed
- **Voyage and Return:** Enter the world of deception, return authentic

**2. Choose Save the Cat Story Type**

Save the Cat has 10 story types that describe emotional stakes:

| Save the Cat Type | Core Structure | When to Use |
|-------------------|----------------|-------------|
| **Monster in the House** | Confined threat must be defeated | Contained horror/threat |
| **Golden Fleece** | Team journey for prize | Heist, quest, team dynamics |
| **Out of the Bottle** | Wish/power brings trouble | Magical consequences |
| **Dude with a Problem** | Ordinary person in extraordinary danger | Thriller, survival |
| **Rites of Passage** | Life transition and acceptance | Coming-of-age, transformation |
| **Buddy Love** | Relationship transforms characters | Romance, friendship |
| **Whydunit** | Mystery of motive, not just identity | Mystery, investigation |
| **The Fool Triumphant** | Underdog proves everyone wrong | Underestimated hero |
| **Institutionalized** | Character vs. oppressive system | System critique |
| **Superhero** | Powered character vs. nemesis + inner curse | Superhero, power + responsibility |

**Your Logline:**
- **Best Match:** "Dude with a Problem" (ordinary impostor thrust into life-or-death stakes)
- **Secondary:** "Rites of Passage" (transformation through crisis)

**3. Choose Genre(s)**

**Genre = The pressure/delivery mode**

Genres answer: "What kind of danger creates tension?"

| Genre | Pressure Type | Promises |
|-------|--------------|----------|
| **Mystery** | Information control | Revelation, clues, red herrings |
| **Thriller** | Time pressure | Ticking clock, escalation |
| **Horror** | Survival against threat | Dread, isolation, terror |
| **Sci-Fi** | Tech/future consequences | Speculation, ethics, systems |
| **Fantasy** | Magic/world rules | Wonder, quests, prophecy |
| **Romance** | Emotional connection | Chemistry, misunderstanding, union |
| **Action** | Physical danger | Momentum, kinetic stakes |
| **Superhero** | Power + responsibility | Identity, moral testing |

**For Your Logline:**
- **Primary Genre:** Thriller (document = ticking clock, life at stake)
- **Secondary Genre:** Mystery (what's in the document? Who's the impostor?)
- **Tone Flavor:** Psychological (impostor syndrome, identity crisis)

**4. Identify Genre-Specific Tropes**

Based on chosen genre(s), select 3-5 tropes to use:

**Thriller Tropes:** (from TVTropes)
- Ticking clock
- Race against time
- MacGuffin (the document)
- Identity reveal

**Mystery Tropes:**
- Hidden identity
- Red herrings about who the impostor is
- Revelation scene

**Trope Selection Rule:**
- Pick 3-5 intentional tropes
- Decide: Use straight, invert, or subvert
- Map to beat sheet

#### Agent System

**Proposed Agents:**
1. **StoryShapeAgent:** Analyzes logline → recommends Classic Plot(s)
2. **SaveTheCatTypeAgent:** Analyzes theme + characters → recommends STC type
3. **GenreAgent:** Analyzes stakes/pressure → recommends genre(s)
4. **TropeAgent:** Suggests genre-appropriate tropes from TVTropes database

#### Output
- `codex["story"]["story_shape"]` - Classic Plot chosen (e.g., "The Quest")
- `codex["story"]["save_the_cat_type"]` - STC type (e.g., "Dude with a Problem")
- `codex["story"]["genres"]` - List of genre(s) (e.g., ["thriller", "mystery"])
- `codex["story"]["tropes"]` - 3-5 selected tropes with usage notes

#### References
- **7 Classic Plots:** (from your shared material)
- **Save the Cat Types:** https://savethecat.com/genre/blake-snyders-glossary-of-genre-terms
- **Genre Tropes:** https://tvtropes.org/pmwiki/pmwiki.php/Main/GenreTropes
- **Trope Systems:** https://tvtropes.org (use targeted searches)
- **StoryGrid (Genre Conventions):** https://storygrid.com

---

### STEP 3: Plot Structure (Character Arc + Story Beats)

**Goal:** Build the plot structure by integrating character arc beats with Save the Cat story beats, ensuring plot events force thematic exploration.

#### Input
- `codex["story"]["theme"]` (from Step 0)
- `codex["story"]["characters"]` (from Step 1)
- `codex["story"]["story_shape"]` (from Step 2)
- `codex["story"]["save_the_cat_type"]` (from Step 2)
- `codex["story"]["genres"]` (from Step 2)

#### Methodology

**1. Character Arc Structural Beats**

Each character arc type has specific beats that must align with plot beats:

**Positive Change Arc Beats:**
1. **Characteristic Moment:** Show character living the Lie
2. **Ghost/Backstory:** Reveal what created the Lie
3. **First Plot Point:** Character thrust into situation that challenges Lie
4. **Midpoint:** Character glimpses the Truth (but doesn't fully embrace it)
5. **Third Plot Point (All Is Lost):** Lie fails catastrophically
6. **Climax:** Character chooses Truth over Lie
7. **Resolution:** Character living in the Truth

**Flat Arc Beats:**
1. Character already knows Truth
2. World/others believe the Lie
3. Character uses Truth to challenge Lie
4. Others transform, not the protagonist

**Negative Arc Beats:**
1. Character encounters Truth
2. Rejects Truth
3. Doubles down on Lie
4. Tragic consequences

**2. Save the Cat 15 Beats**

Map character arc beats onto Save the Cat structure:

| Beat | Timing | Plot Function | Character Arc Function |
|------|--------|---------------|----------------------|
| **Opening Image** | 0-1% | Snapshot of world before | Character living the Lie |
| **Theme Stated** | 5% | Thematic question posed | Someone hints at the Truth |
| **Setup** | 1-10% | Establish normal world | Show Lie in action + Ghost |
| **Catalyst** | 10% | Inciting incident | Challenge to Lie begins |
| **Debate** | 10-20% | Should they engage? | Character resists Truth |
| **Break Into Two** | 20% | Enter Act 2 | Forced to confront Lie |
| **B Story** | 22% | Relationship subplot begins | Impact Character introduced |
| **Fun and Games** | 20-50% | Promise of premise | Experiments with Truth |
| **Midpoint** | 50% | False victory/defeat | Glimpses Truth (doesn't commit) |
| **Bad Guys Close In** | 50-75% | Pressure increases | Lie fails progressively |
| **All Is Lost** | 75% | Lowest point | Lie collapses completely |
| **Dark Night of the Soul** | 75-80% | Emotional pit | Mourns the Lie |
| **Break Into Three** | 80% | Solution found | Commits to Truth |
| **Finale** | 80-99% | Confrontation | Uses Truth to succeed |
| **Final Image** | 99-100% | Mirror of Opening Image | Living the Truth |

**3. Multi-Character Arc Integration**

For stories with multiple POV characters:
- **Protagonist:** Positive Change Arc (overcomes Lie → finds Truth)
- **Antagonist:** Flat Arc (believes Lie, doesn't change) OR Negative Arc (descends)
- **Relationship Character:** Parallel arc (different Lie, same Truth) OR Flat Arc (guides protagonist)
- **Supporting Cast:** Each has micro-arc tied to theme

**Technique:** Stagger character arc beats so revelations/transformations happen at different times, creating dramatic irony.

**4. Thematic Beats**

Every major plot beat must test the thematic question:

Example (Theme: "Is authenticity worth the cost?"):
- **Catalyst:** Document requires impostor to risk exposure
- **Midpoint:** Character tries being authentic → sees potential benefit
- **All Is Lost:** Authenticity causes immediate catastrophic loss
- **Climax:** Must choose: maintain lie (save precious thing) or embrace truth (risk everything)

**5. Try-Fail Cycles** (Brandon Sanderson - if applicable)

For Quest/Adventure stories, add escalating Try-Fail cycles:
- **Try 1:** Character attempts goal using their Lie → Fails
- **Try 2:** Character adjusts approach, still clinging to Lie → Fails harder
- **Try 3:** Character attempts goal using the Truth → Succeeds (with cost)

**6. Structural Timing**

Use K.M. Weiland's structural timing guidelines:

| Section | Percentage | Word Count (100k novel) | Purpose |
|---------|-----------|-------------------------|---------|
| **Act 1** | 0-25% | 0-25,000 words | Setup, Catalyst, Debate |
| **Act 2A** | 25-50% | 25,000-50,000 words | New world, Fun & Games, Midpoint |
| **Act 2B** | 50-75% | 50,000-75,000 words | Bad Guys Close In, All Is Lost |
| **Act 3** | 75-100% | 75,000-100,000 words | Dark Night, Finale, Resolution |

**7. Subplot Integration**

**Rule:** "There are no subplots, only plots."

Every subplot must:
- Serve the central theme
- Conclude in the climax
- Reflect a facet of the Thematic Square

Example subplots for "Identity vs. Truth" theme:
- Romantic subplot: Love interest values authenticity → forces protagonist's hand
- Professional subplot: Impostor's fake credentials are questioned
- Friendship subplot: Friend discovers the lie → tests loyalty

#### Agent System

**Proposed Agents:**
1. **ArcBeatAgent:** Maps character arc type → structural beats
2. **SaveTheCatAgent:** Generates 15-beat outline
3. **ArcIntegrationAgent:** Merges character arc beats with STC beats
4. **ThematicBeatAgent:** Ensures each beat tests thematic question
5. **SubplotAgent:** Weaves thematic subplots into main structure

#### Output
- `codex["story"]["structure_beats"]` - Combined beat sheet with:
  - Save the Cat 15 beats
  - Character arc beats for each major character
  - Thematic questions tested at each beat
  - Timing percentages
  - Try-Fail cycles (if applicable)
- `codex["story"]["subplots"]` - List of subplots with thematic purpose

#### References
- [Save the Cat Beat Sheet](https://reedsy.com/blog/guide/story-structure/save-the-cat-beat-sheet)
- [Save the Cat Writes a Novel](https://savethecat.com) - Book by Jessica Brody
- [Character Arc Structure](https://www.helpingwritersbecomeauthors.com/character-arcs-2/)
- [Inciting Event and Climactic Moment](https://www.helpingwritersbecomeauthors.com/inciting-event-and-climactic-moment/)
- [Story Structural Timing](https://www.helpingwritersbecomeauthors.com/your-storys-structural-timing/)
- [Organizing Subplots](https://www.helpingwritersbecomeauthors.com/5-tips-organizing-subplots/)
- [Try-Fail Cycles](https://www.youtube.com/watch?v=LmmU5-w4uHc) - Brandon Sanderson

---

### STEP 4: World Building (Theme-Informed)

**Goal:** Create locations and world systems that reinforce and pressure the thematic question.

#### Input
- `codex["story"]["theme"]` (from Step 0)
- `codex["story"]["characters"]` (from Step 1)
- `codex["story"]["structure_beats"]` (from Step 3)
- `codex["deck_of_worlds"]["prompts"]` (world seed)

#### Methodology

**1. Thematic World Pressure**

The world should make the thematic question HARDER to answer:

Example (Theme: "Is authenticity worth the cost?"):
- **World Rule:** Society with strict identity verification
- **Cultural Norm:** Imposters are severely punished
- **Economic System:** Social mobility requires verified credentials
- **Result:** Theme is tested under maximum pressure

**2. Locations as Thematic Spaces**

Each major location should represent a different answer to the theme:

Example locations:
- **Location A:** Place where imposters thrive (supports Lie)
- **Location B:** Place demanding radical honesty (supports Truth)
- **Location C:** Grey area where identity is fluid (explores nuance)

**3. World-Building Agents** (Keep existing system, add thematic filter)

Existing agents:
- **WorldSociologistAgent:** Daily life, social structure
- **WorldEconomistAgent:** Economy, jobs, trade
- **WorldPoliticianAgent:** Government, law, military
- **WorldCulturalistAgent:** Culture, religion, entertainment

**New Addition:** Each agent must answer:
> "How does this world aspect pressure the thematic question?"

**4. Magic/Tech Systems** (if applicable)

For Fantasy/Sci-Fi:
- **Sanderson's Laws:** Magic/tech system rules must be clear
- **Thematic Integration:** Magic/tech should metaphorically represent theme

Example:
- Theme: "Is authenticity worth the cost?"
- Magic System: Shapeshifting magic that erases original form over time
- Thematic Pressure: Using the Lie (shapeshifting) has permanent cost

#### Output
- `codex["story"]["locations"]` - Locations with thematic purpose noted
- `codex["story"]["world"]` - World context with thematic pressure points
- `codex["story"]["world"]["thematic_rules"]` - How world pressures theme

#### References
- Existing world-building methodology (keep current system)
- [Sanderson's Laws of Magic](https://www.brandonsanderson.com/sandersons-first-law/) (for Fantasy/Sci-Fi)

---

### STEP 5: Scene Outline (Thematic Scenes)

**Goal:** Break the beat sheet into chapter/scene outline where every scene advances plot AND tests the thematic question.

#### ✅ RECENTLY COMPLETED: Enhanced Setup/Payoff Tracking System (Step 5B)

**Implemented:** Feb 12, 2026

**What Was Added:**
- **tracking_id System**: Unique IDs link setup chains (1 of 3 → 2 of 3 → 3 of 3) using same tracking_id
- **Forward-Pointing Tracking**: Setup scenes (1 of 3, 2 of 3) point to ONE payoff scene (3 of 3)
- **Rule of Three Enforcement**: Cognitive salience through repetition (1=accident, 2=coincidence, 3=pattern)
- **Chekhov's Gun Compliance**: Everything introduced must pay off later
- **Emotional Stake Escalation**: Low → Medium → High across tracking chain
- **Subtlety Enforcement**: Show through action/consequence, never through dialogue
- **Comprehensive Tracking**: Skills, traits, world rules, relationships, objects, secrets - EVERYTHING readers need to notice
- **Scene ID Population**: Automatically populates character_ids, location_id, pov_character_id fields
- **Tracking Chain Validation**: Validates every "1 of 3" has corresponding "2 of 3" and "3 of 3"

**Files Modified:**
1. [story_schemas.py](src/story_schemas.py) (lines 3044-3061): SetupPayoffTracking model with tracking_id
2. [foreshadowing_agents.py](src/story_agents/foreshadowing_agents.py): All 3 agent prompts updated with tracking_id system
3. [base_phase1.py](src/authors/base_phase1.py): Added helper functions + Step 5B enabled

**Schema Changes:**
```python
class SetupPayoffTracking(BaseModel):
    tracking_id: str  # NEW: Links all scenes in chain
    position: str  # "1 of 3", "2 of 3", "3 of 3"
    payoff_scene: str  # Filled in setups, empty in payoff
    emotional_stake: str  # "Low", "Medium", "High" - escalates
    demonstrates_how: str  # "Through action", never dialogue
    # ... other fields
```

**How It Works:**
1. **SetupPayoffAgent** scans chapters 7+ for payoff moments, works backward to create setups
2. **RuleOfThreeAgent** ensures every important element appears 3 times minimum
3. **TropeExecutionAgent** maps trope beats to tracking chains
4. All agents generate tracking with same tracking_id for related scenes
5. Helper function `_populate_scene_ids()` fills character/location IDs from names
6. Helper function `_validate_tracking_completeness()` checks chain integrity

**Expected Output:**
```
STEP 5B COMPLETE
  Validating 12 tracking chains...
  ✓ All tracking chains complete!
  New Scenes: 0
  Annotated Scenes: 15
  Total Scenes Now: 31
```

**Philosophy:**
> "Everything introduced must pay off. No wasted scenes. Like a fucking original author. Repetition is how audience will know how to pay attention."



#### Input
- `codex["story"]["structure_beats"]` (from Step 3)
- `codex["story"]["characters"]` (from Step 1)
- `codex["story"]["locations"]` (from Step 4)
- `codex["story"]["theme"]` (from Step 0)

#### Methodology

**1. Scene Structure (Dwight Swain)**

Every scene has:
- **Goal:** Character's immediate objective (driven by Want)
- **Conflict:** Opposition to goal (tests Lie)
- **Disaster:** Goal fails or succeeds with complication (challenges Lie)

OR

- **Goal → Conflict → Resolution** (partial victory)

**2. Scene Purpose (Triple Function)**

Every scene must serve THREE functions:
1. **Plot:** Advance external story
2. **Character:** Advance character arc (test Lie/Truth)
3. **Theme:** Test the thematic question

**Example Scene:**
- **Plot Function:** Protagonist must forge document to save life
- **Character Function:** Forging document means leaning into Lie (impostor identity)
- **Thematic Function:** Tests "Is deception ever justified?"

**3. Multi-POV Scene Distribution**

If using multiple POVs:
- **Protagonist:** Most scenes (40-50%)
- **Main Character(s):** Regular scenes (20-30% each)
- **Antagonist:** Key moments (10-20%)

**Technique:** Use POV shifts to create dramatic irony (reader knows what protagonist doesn't).

**4. Scene Outline Agents** (Modified existing system)

Keep existing agents BUT add thematic evaluation:
- **ScenePlotAgent:** Goal, Motivation, Conflict
- **SceneCharacterAgent:** Swain Scene/Sequel structure
- **ScenePacingAgent:** Rhythm and tension
- **SceneStructureAgent:** 7-point alignment
- **NEW: SceneThemeAgent:** "How does this scene test the theme?"

**5. Subplot Weaving**

Technique from research: **Color-code subplot threads**
- Main plot: Black
- Romantic subplot: Red
- Professional subplot: Blue
- etc.

Ensure subplot scenes are evenly distributed and conclude in climax.

**6. Scene Word Count Targets** (INCREASED)

**Old:** 750-1000 words/scene
**New:** 1500-2000 words/scene

**Rationale:**
- Professional novels average 1500-2500 words/scene
- More space = better "show don't tell"
- Allows proper character interiority
- Room for sensory grounding + character psychology + plot

#### Output
- `codex["story"]["chapter_outline"]` - Detailed scene breakdown with:
  - Scene Goal, Conflict, Disaster/Resolution
  - POV character
  - Location
  - Plot function
  - Character arc function
  - Thematic test
  - Target word count: 1500-2000 words
  - Subplot threads present

#### References
- [Balancing Multiple POVs](https://www.helpingwritersbecomeauthors.com/how-to-balance-multiple-povs/)
- [Scene Structure](https://www.helpingwritersbecomeauthors.com/dwight-swain-scene-structure/) (Dwight Swain)
- Existing scene debate system (modified)

---

### STEP 6: Prose Generation (MASSIVELY IMPROVED)

**Goal:** Generate high-quality prose using a SYNTHESIS system (not winner-takes-all) with real-time critique integration and iterative refinement.

#### Input
- `codex["story"]["chapter_outline"]` (from Step 5)
- `codex["story"]["characters"]` (from Step 1)
- `codex["story"]["theme"]` (from Step 0)
- All world context

#### Why Current System Fails

**Problem 1: Winner-Takes-All**
- 5 agents propose prose
- They vote
- Winner's prose used AS-IS
- 80% of work discarded

**Result:** No agent produces balanced prose - each optimizes for their specialty.

**Problem 2: Critiques Generated But Not Applied**
- Agents critique each other
- Critiques saved to metadata
- Winning prose used unchanged
- Critiques ignored until Step 6 (too late)

**Problem 3: Low Word Count**
- Target: 750-1000 words
- Reality: Too compressed for quality
- Forces telling instead of showing

**Problem 4: Voice Inconsistency**
- Different agent wins each scene
- Voice varies scene-to-scene
- No unified narrative voice

#### New Approach: Synthesis System

**Phase 1: Multi-Agent Proposals** (Keep this)
- 5 agents generate prose:
  1. CharacterContinuityAgent
  2. LocationAtmosphereAgent
  3. WorldBuildingIntegrationAgent
  4. PlotTickingClockAgent
  5. NarrativeContinuityAgent

**Phase 2: Cross-Critique** (Keep this)
- All agents critique each other's proposals
- Identify:
  - Strengths in each proposal
  - Weaknesses to avoid
  - Missing elements

**Phase 3: SYNTHESIS** (NEW)

Instead of voting → selecting winner, create a **SynthesisAgent** that:

1. **Analyzes All Proposals:**
   - Best character work (from CharacterAgent)
   - Best sensory details (from LocationAgent)
   - Best world integration (from WorldAgent)
   - Best urgency/pacing (from PlotAgent)
   - Best prose craft (from NarrativeAgent)

2. **Blends Best Elements:**
   - Uses winner's prose as structural base
   - Integrates runner-up strengths:
     - "Agent A had the best dialogue"
     - "Agent B had the best opening sensory grounding"
     - "Agent C best integrated the ticking clock"
   - Creates unified prose incorporating all perspectives

3. **Applies Critique Insights:**
   - Addresses weaknesses identified in cross-critique
   - Fixes filter words, cliches, telling
   - Ensures Deep POV

**Phase 4: Real-Time Critique & Revision** (NEW)

Instead of waiting until Step 6:

1. **Run 5 Critics Immediately:**
   - ProsePolishCritic (filter words, cliches, show-don't-tell)
   - CharacterVoiceCritic (dialogue authenticity)
   - ContinuityCritic (codex consistency)
   - PacingTensionCritic (GMC, ticking clock)
   - EmotionalResonanceCritic (emotional beats, micro-tension)

2. **ReviserAgent Fixes Issues:**
   - Addresses specific critique points
   - Revises synthesized prose
   - Targets fixes (not full rewrite)

3. **Validation Round:**
   - Re-run critics on revised prose
   - Ensure issues fixed
   - If score improves, accept revision
   - If not, iterate once more

**Phase 5: Voice Consistency Check** (NEW)

- **VoiceAgent** compares current scene to previous scenes
- Checks:
  - Sentence rhythm consistency
  - Vocabulary level consistency
  - POV consistency
  - Tone consistency
- Adjusts if scene feels "off-brand"

#### Prose Quality Improvements

**1. Higher Word Count**
- Target: **1500-2000 words/scene**
- Rationale: Professional standard, allows depth

**2. Remove Prescriptive Word Lists**

**Old Approach:**
```
Use TENSE WORDS: paused, froze, waited, hid, fled, gulped, hesitated
```

**New Approach:**
```
Create micro-tension through:
- Unresolved questions that pull reader forward
- Character contradictions between action and thought
- Unexpected sensory details that create unease
- Delayed gratification of scene goals
```

**Result:** Less formulaic, more organic tension.

**3. Flexible Paragraph Structure**

**Old:** Rigid opening/middle/closing paragraphs (100-150 words each)

**New:** Organic structure based on scene needs:
- Opening: Ground reader quickly (sensory + character state)
- Development: Build through Goal → Conflict → Outcome
- Closing: End with resonance or hook
- **Allow natural paragraph lengths**

**4. Thematic Integration**

Every scene must:
- Test the thematic question
- Show character's relationship to Lie/Truth
- Advance character arc

SynthesisAgent ensures theme is woven through prose, not stated.

#### Agent System (Revised)

**Existing 5 Proposal Agents:** (Keep)
1. CharacterContinuityAgent
2. LocationAtmosphereAgent
3. WorldBuildingIntegrationAgent
4. PlotTickingClockAgent
5. NarrativeContinuityAgent

**NEW Synthesis & Refinement Agents:**
6. **SynthesisAgent:** Blends best elements from all 5 proposals
7. **VoiceConsistencyAgent:** Ensures narrative voice matches previous scenes
8. **ThematicProseAgent:** Ensures theme woven through prose

**Existing 5 Critics:** (Move to real-time)
9. ProsePolishCritic
10. CharacterVoiceCritic
11. ContinuityCritic
12. PacingTensionCritic
13. EmotionalResonanceCritic

**Existing Reviser:** (Move to real-time)
14. ReviserAgent

#### Output
- `codex["story"]["narrative"]` - Full prose with:
  - Synthesized prose (not winner-takes-all)
  - 1500-2000 words/scene
  - Real-time critique scores
  - Voice consistency validated
  - Thematic integration verified

#### References
- Current narrative_writing_agents.py (modified for synthesis)
- Current critique_agents.py (moved to real-time)
- Current reviser_agent.py (applied per scene)

---

### STEP 7: Revision & Polish

**Goal:** Final pass for voice consistency, emotional arc validation, and theme resonance.

#### Input
- `codex["story"]["narrative"]` (from Step 6)
- All story context

#### Methodology

**1. Voice Consistency Audit**

- Read all scenes by same POV character
- Check for:
  - Sentence rhythm consistency
  - Vocabulary level consistency
  - Tone consistency
- Flag scenes that feel "off"
- Revise flagged scenes

**2. Emotional Arc Validation**

Track emotional beats across story:
- Opening emotional state
- Progression through structure
- Low point (Dark Night of the Soul)
- Resolution emotional state

Ensure arc feels earned and satisfying.

**3. Theme Resonance Check**

- Identify where theme is stated/explored
- Ensure theme is woven through (not preached)
- Check that different characters represent different thematic perspectives
- Validate that climax resolves thematic question (even if ambiguously)

**4. Character Arc Verification**

For each major character:
- Verify Lie → Truth progression
- Ensure transformation feels earned
- Check that climax demonstrates new Truth

**5. Continuity Check**

- Character names, traits consistent
- Timeline logical
- World rules consistent
- Foreshadowing paid off

**6. Final Polish**

- ProsePolishCritic final pass
- Filter word elimination
- Cliche removal
- Rhythm and flow

#### Output
- `codex["story"]["narrative"]` - Final polished prose
- `codex["metadata"]["phase_1"]["revision_report"]` - Validation scores

#### References
- Existing revision system (modified)
- [Character Arc Completion Check](https://www.helpingwritersbecomeauthors.com/write-character-arcs/)

---

## 📊 Final Phase 1 Output Structure (Codex Contract)

**These keys MUST be maintained for backward compatibility:**

```json
{
  "story": {
    "theme": {
      "central_question": "string",
      "thematic_square": {
        "positive": "string",
        "contradictory": "string",
        "contrary": "string",
        "negation_of_negation": "string"
      },
      "perspectives": ["string", "string", ...]
    },
    "outline": {
      "story_seed_parsed": {},
      "structure_beats": {},
      "theme": "string",
      "title": "string"
    },
    "characters": [
      {
        "id": "char_001",
        "name": "string",
        "thematic_perspective": "string",
        "lie_character_believes": "string",
        "truth_character_needs": "string",
        "want_vs_need": {
          "want": "string",
          "need": "string"
        },
        "arc_type": "positive_change|flat|disillusionment|fall|corruption",
        "shadow_traits": {},
        "ghost": "string",
        "physical": {},
        "psychological": {}
      }
    ],
    "story_shape": "string",
    "save_the_cat_type": "string",
    "genres": ["string"],
    "tropes": ["string"],
    "locations": [
      {
        "id": "loc_001",
        "name": "string",
        "thematic_purpose": "string",
        "physical": {},
        "atmosphere": {}
      }
    ],
    "world": {
      "thematic_rules": [],
      "daily_life": {},
      "social_structure": {},
      "government_law": {},
      "economy": {},
      "culture": {},
      "religion": {}
    },
    "structure_beats": {
      "save_the_cat_beats": [],
      "character_arc_beats": {},
      "thematic_beats": [],
      "subplots": []
    },
    "chapter_outline": {
      "chapters": [
        {
          "chapter_number": 1,
          "scenes": [
            {
              "scene_number": 1,
              "goal": "string",
              "conflict": "string",
              "disaster_or_resolution": "string",
              "pov_character": "string",
              "location": "string",
              "plot_function": "string",
              "character_arc_function": "string",
              "thematic_test": "string",
              "target_word_count": 1500
            }
          ]
        }
      ]
    },
    "narrative": {
      "title": "string",
      "subtitle": "string",
      "chapters": [
        {
          "chapter_number": 1,
          "chapter_title": "string",
          "scenes": [
            {
              "scene_number": 1,
              "text": "string (1500-2000 words)",
              "synthesis_metadata": {
                "proposals_used": [],
                "critique_scores": {},
                "voice_consistency_score": 0.0
              }
            }
          ]
        }
      ]
    }
  },
  "metadata": {
    "phase_1": {
      "phase": 1,
      "name": "Author-Driven Story Creation",
      "author_id": "string",
      "steps_completed": [0, 1, 2, 3, 4, 5, 6, 7],
      "step_timings": {},
      "revision_report": {}
    }
  }
}
```

**New keys added for improvements. Existing keys preserved for backward compatibility.**

---

## 🔗 Complete Reference Library

### Character Arc & Psychology
- [Character Arcs Overview](https://www.helpingwritersbecomeauthors.com/write-character-arcs/)
- [Character Arc Structure](https://www.helpingwritersbecomeauthors.com/character-arcs-2/)
- [The Lie Your Character Believes](https://www.helpingwritersbecomeauthors.com/truth-your-character-believes/)
- [Positive Character Arc](https://www.helpingwritersbecomeauthors.com/write-character-arcs/#positive)
- [Flat Character Arc](https://www.helpingwritersbecomeauthors.com/flat-character-arc-1/)
- [Negative Character Arcs](https://www.helpingwritersbecomeauthors.com/negative-character-arc-1/)
- [5 Arc Types at a Glance](https://www.helpingwritersbecomeauthors.com/learn-5-types-of-character-arc-at-a-glance/)
- [3 Negative Arcs Part 2](https://www.helpingwritersbecomeauthors.com/learn-5-types-of-character-arc-at-a-glance-the-3-negative-arcs-part-2-of-2/)
- [Shadow Theory for Complex Characters](https://www.helpingwritersbecomeauthors.com/how-to-create-insanely-complex-characters-using-shadow-theory/)

### Theme & Story Integration
- [Plot, Character, and Theme Triangle](https://www.helpingwritersbecomeauthors.com/plot-character-and-theme-the-greatest-love-triangle-in-fiction/)
- [Deepening Theme with Thematic Square](https://www.helpingwritersbecomeauthors.com/deepening-your-storys-theme-with-the-thematic-square/)
- [What is Theme?](https://www.helpingwritersbecomeauthors.com/storys-theme-2/)
- [Relationship Between Plot and Theme](https://www.helpingwritersbecomeauthors.com/what-is-the-relationship-between-plot-and-theme/)

### Story Structure
- [Inciting Event and Climactic Moment](https://www.helpingwritersbecomeauthors.com/inciting-event-and-climactic-moment/)
- [Story Structural Timing](https://www.helpingwritersbecomeauthors.com/your-storys-structural-timing/)
- [Movie Story Structure (The Great Escape example)](https://www.helpingwritersbecomeauthors.com/movie-storystructure/the-great-escape/)
- [Calculate Book Length](https://www.helpingwritersbecomeauthors.com/calculate-books-length-writing/)

### Multi-POV & Subplots
- [Balancing Multiple POVs](https://www.helpingwritersbecomeauthors.com/how-to-balance-multiple-povs/)
- [Organizing Subplots](https://www.helpingwritersbecomeauthors.com/5-tips-organizing-subplots/)

### Save the Cat & Beat Sheets
- [Save the Cat Official Site](https://savethecat.com)
- [Blake Snyder's Story Types](https://savethecat.com/genre/blake-snyders-glossary-of-genre-terms)
- [Save the Cat Beat Sheet Examples](https://savethecat.com/beat-sheets)
- [Reedsy Save the Cat Guide](https://reedsy.com/blog/guide/story-structure/save-the-cat-beat-sheet)
- [Squibler Save the Cat Explanation](https://www.squibler.io/learn/story-planning/what-is-save-the-cat/)

### Genre & Tropes
- [TVTropes Genre Index](https://tvtropes.org/pmwiki/pmwiki.php/Main/GenreTropes)
- [TVTropes Main Site](https://tvtropes.org)
- [StoryGrid (Genre Conventions)](https://storygrid.com)
- [Reedsy Genre Guides](https://reedsy.com/discovery/blog)
- [Mythcreants (Fantasy/Sci-Fi)](https://mythcreants.com)
- [ScreenCraft](https://screencraft.org)
- [Film Courage](https://filmcourage.com)

### Books Referenced
- **Save the Cat Writes a Novel** - Jessica Brody (integrating STC with novels)
- **The Anatomy of Story** - John Truby (moral weakness, desire, opposition)
- **Romancing the Beat** - Gwen Hayes (romance-specific beats)
- **The Hero with a Thousand Faces** - Joseph Campbell (mythic structure)
- **Man and His Symbols** - Carl Jung (shadow theory, archetypes)

---

## 🎯 Success Metrics: How We'll Know It's Working

### Thematic Coherence
- ✅ Every major character has clear thematic perspective
- ✅ Every scene tests the central thematic question
- ✅ Plot events emerge from thematic conflict (not arbitrary)

### Character Depth
- ✅ Characters have Lie/Truth defined
- ✅ Character arcs progress through structure beats
- ✅ Shadow traits create internal complexity
- ✅ Transformations feel earned, not forced

### Prose Quality
- ✅ Scenes average 1500-2000 words (not 750-1000)
- ✅ Synthesis creates balanced prose (not single-agent bias)
- ✅ Critique scores improve scene-over-scene
- ✅ Voice consistency across scenes by same POV character
- ✅ Micro-tension emerges organically (not from word lists)

### Story Satisfaction
- ✅ Plot and character arc resolve simultaneously in climax
- ✅ Theme explored (not preached)
- ✅ Emotional arc validated
- ✅ Subplots conclude meaningfully

---

## 🚀 Next Steps

**This is design phase only.** No coding yet.

**Process:**
1. **Review this plan** - Discuss, improve, refine
2. **Iterate on approach** - Adjust based on your feedback
3. **Finalize methodology** - Lock in the approach
4. **Then:** Design → Improve → Code each step individually

**Questions to Discuss:**
- Does the Step 0-7 order make sense?
- Is Theme → Character → Plot the right philosophy?
- Should we keep any current steps as-is?
- Are there techniques from the research we should emphasize more?
- What's your priority: start with Step 0 or revamp existing Step 5 (prose generation)?

**Ready to iterate on this plan!**
