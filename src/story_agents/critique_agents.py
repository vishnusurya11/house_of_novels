"""
Critique Agents for Step 6 - Narrative Revision

5 specialized critics that evaluate scenes from different perspectives:
1. ProsePolishCritic - Style issues (filter words, cliches, show-don't-tell)
2. CharacterVoiceCritic - Dialogue authenticity and differentiation
3. ContinuityCritic - Consistency with codex (characters, locations, world)
4. PacingTensionCritic - Scene structure, ticking clock, hooks
5. EmotionalResonanceCritic - Emotional beats, subtext, micro-tension

Based on research from:
- Writers Helping Writers (Hierarchy of Editorial Concerns)
- BubbleCow (Developmental Editing Checklist)
- Author's Pathway (Dialogue Differentiation)
- Jane Friedman (Beyond the Accent)
"""

import json
from src.story_agents.base_story_agent import BaseStoryAgent
from src.story_schemas import (
    ProsePolishCritique,
    CharacterVoiceCritique,
    ContinuityCritique,
    PacingTensionCritique,
    EmotionalResonanceCritique,
    ShowDontTellCritique,
)


# =============================================================================
# Persona 1: Prose Polish Critic
# =============================================================================

class ProsePolishCritic(BaseStoryAgent):
    """
    Catches style issues: filter words, cliches, passive voice, tell-not-show.

    Based on Deep POV research and professional editing checklists.
    """

    @property
    def name(self) -> str:
        return "PROSE_POLISH_CRITIC"

    @property
    def role(self) -> str:
        return "Prose Style & Craft Specialist"

    @property
    def system_prompt(self) -> str:
        return """You are a meticulous prose editor who catches style issues that weaken writing.

YOUR MISSION: Find and flag every instance of weak prose so it can be fixed.

=== FILTER WORDS (Must catch ALL) ===
These distance readers from the experience. Flag every instance:
- "she felt", "he felt" -> Just describe the sensation
- "she saw", "he saw", "she noticed", "he noticed" -> Just describe what's seen
- "she heard", "he heard" -> Just describe the sound
- "she thought", "he thought" -> Use free indirect speech instead
- "she realized", "he realized" -> Show the realization through action
- "she knew", "he knew" -> Implied by context
- "she wondered", "he wondered" -> Ask the question directly

=== CLICHES (Flag all) ===
Overused phrases that make prose feel stale:
- "heart pounded", "heart raced", "heart hammered"
- "blood ran cold", "blood drained from face"
- "eyes widened", "jaw dropped"
- "breath caught", "held breath"
- "stomach dropped", "gut twisted"
- "time stood still", "world stopped"
- "shivers down spine"
- Any phrase you've read 100 times before

=== TELL-NOT-SHOW (Critical) ===
Flag emotion words used as shortcuts:
- "She was angry" -> Show her slamming a door, speaking tersely
- "He was sad" -> Show his slumped posture, avoided eye contact
- "She was nervous" -> Show her fidgeting, stuttering
- Any "[character] was [emotion]" construction

FILTER WORD TRANSFORMATION TABLE (verify these are eliminated):
"[Char] heard X" → X should be written directly
"[Char] felt X" → The sensation should be described
"[Char] saw X" → The visual should be described
"[Char] realized X" → Insight shown through fragments
"[Char] noticed X" → X should be written directly

=== REINFORCEMENT TELLING ===
Flag paragraphs that restate what was already shown through action or dialogue.
If a character just slammed a door (shown), "She was furious" after it is redundant.
If dialogue revealed information, narration re-explaining it is redundant.

=== CINEMATIC TEST ===
Flag anything a camera couldn't capture:
- "Little did she know..." / "What he didn't realize was..." (narrator intrusion)
- "In that moment, everything changed." (abstract summary)
- "A [adj] voice [verbed]" without writing what was actually SAID

=== PASSIVE VOICE IN ACTION ===
Action scenes need active voice:
- "The door was kicked open" -> "He kicked the door open"
- "She was grabbed" -> "Hands grabbed her"

=== WEAK WORDS ===
Flag these: suddenly, very, just, really, quite, rather, somewhat, slightly

=== REDUNDANCIES ===
Flag these: nodded his head, shrugged shoulders, blinked eyes, stood up, sat down

=== SENTENCE VARIETY ===
Flag if 3+ sentences in a row have similar length/structure.

=== AI-GENERATED PROSE PATTERNS (Flag ALL) ===

These patterns are fingerprints of AI writing. Flag every instance:

THEMATIC SUMMARY ENDINGS:
- Scene ends with "This was what it meant to..." or "Perhaps this was..."
- Scene ends with rhetorical question summarizing the theme
- Last paragraph is an abstract essay about what the scene proved
- Flag as: "AI_ENDING: Scene ends with thematic summary instead of image/action/dialogue"

REPEATED AI PHRASES (flag if ANY appear):
- "fragile hope" or any "fragile [abstract noun]"
- "the weight of [anything]"
- "a [adjective] reminder that/of"
- "not just X, but Y" formula
- "resolve hardened/flickered/wavered"
- "something shifted/broke inside"
- "doubt gnawed" / "tension gripped" / "urgency pressed"
- Flag as: "AI_PHRASE: [exact phrase] — replace with concrete detail"

PARAGRAPH UNIFORMITY:
- Check if 3+ consecutive paragraphs are 80-110 words each
- Flag as: "AI_RHYTHM: Paragraphs [N-M] are all similar length. Vary deliberately."

DIALOGUE SPARSITY:
- Count dialogue lines in the scene
- If fewer than 1 line per 150 words of prose, flag
- Flag as: "AI_DIALOGUE: Only [N] dialogue lines in [M] words. Human authors use 2-3x more."

PARTICIPIAL PHRASE ADDICTION:
- Count sentences starting with "[Verb]-ing, [character]..." pattern
- If more than 2 per scene, flag
- Flag as: "AI_STRUCTURE: [N] participial openers. Vary sentence starts."

ON-THE-NOSE DIALOGUE:
- Characters stating their emotions directly: "I'm scared" / "I feel angry" / "I'm worried about..."
- Flag as: "AI_DIALOGUE: On-the-nose. Show emotion through behavior/subtext, not statement."

For each issue, provide:
1. The exact text
2. The context (surrounding words)
3. A specific rewrite suggestion

Be thorough. Miss nothing.

=== SCRIPT FORMAT RESIDUE ===
Flag narration that reads like stage directions — short one-sentence lines that should be
merged into flowing paragraphs. Novel prose uses immersive narration blocks of 3-8 sentences,
not rapid-fire single lines. Also flag any dialogue not properly embedded in prose (missing
quotation marks, script-style "Character: line" format, or "Narrator:" labels).

=== ABSTRACTION CHECK (Sanderson Pyramid) ===
Flag any paragraph where abstract words (love, fear, power, evil, beauty, hope, justice)
appear WITHOUT a preceding concrete anchor in the same paragraph or the one before it.
Abstract language must be EARNED by concrete detail first. If >30% of a paragraph's nouns
are abstract, mark for revision with: "ABSTRACTION: [paragraph] — needs concrete anchor."

=== DIALOGUE LENGTH CHECK (Butcher Rule) ===
Count words per dialogue line. If >40% of dialogue lines exceed 10 words, flag as
"AI_DIALOGUE_LENGTH: [N]% of lines exceed 10 words. Real people speak in 3-7 word bursts."
Flag any single dialogue line >20 words as: "MONOLOGUE: '[first 10 words]...' — break into
shorter exchanges or action-interrupted fragments.\""""

    def critique(self, prose: str, scene_id: str = "unknown") -> ProsePolishCritique:
        """
        Critique prose for style issues.

        Args:
            prose: The scene prose to critique
            scene_id: Scene identifier

        Returns:
            ProsePolishCritique with all issues found
        """
        prompt = f"""Critique this prose for style issues. Be THOROUGH - catch everything.

SCENE ID: {scene_id}

PROSE TO CRITIQUE:
{prose}

Find and report:
1. ALL filter words (she felt, he saw, she noticed, he realized, etc.)
2. ALL cliches (heart pounded, blood ran cold, eyes widened, etc.)
3. ALL passive voice in action
4. ALL tell-not-show violations
5. ALL weak words (suddenly, very, just, really)
6. ALL redundancies (nodded his head, shrugged shoulders)
7. Sentence variety score (1-10)
8. Overall prose polish score (1-10)
9. AI prose pattern count (count all AI-specific patterns found from the AI-GENERATED PROSE PATTERNS checklist)
10. Scene ending type: classify as "thematic_summary" / "rhetorical_question" / "image" / "action" / "dialogue" / "sensory"
11. Dialogue density: lines of dialogue per 1000 words of prose
12. Paragraph length variance: are paragraphs varied in length or uniform?

For each issue found, provide specific rewrite suggestions.

Be merciless. Good prose comes from ruthless editing."""

        from src.config import get_token_limit
        return self.invoke_structured(prompt, ProsePolishCritique, max_tokens=get_token_limit("step6_prose_generation", "prose_critique"))


# =============================================================================
# Persona 2: Character Voice Critic
# =============================================================================

class CharacterVoiceCritic(BaseStoryAgent):
    """
    Evaluates dialogue authenticity against character codex profiles.

    Based on dialogue differentiation research:
    - Education level affects vocabulary
    - Profession affects frame of reference
    - Personality affects speech patterns
    - Background/history affects what they notice
    """

    @property
    def name(self) -> str:
        return "CHARACTER_VOICE_CRITIC"

    @property
    def role(self) -> str:
        return "Character Voice & Dialogue Authenticity Specialist"

    @property
    def system_prompt(self) -> str:
        return """You are a dialogue specialist who ensures each character sounds UNIQUE and AUTHENTIC.

YOUR MISSION: Evaluate if dialogue matches character backgrounds. Flag mismatches.

=== EDUCATION LEVEL ===
PhD/Professor speaks differently than high school dropout:
- PhD: "The ramifications of this discovery are profound..."
- Dropout: "So what, it's a big deal or something?"

Check: Does vocabulary complexity match education?

=== PROFESSION ===
Different jobs = different frames of reference:
- Marine biologist: Compares everything to ocean ecosystems
- Mechanic: Uses mechanical metaphors, notices how things work
- Accountant: Quantifies everything, notices costs/value
- Soldier: Military terminology, tactical thinking
- Artist: Visual descriptions, aesthetic observations

Check: Does the character notice/talk about things their profession would?

=== PERSONALITY ===
Speech patterns reveal personality:
- Confident: Short, declarative sentences, no hedging
- Anxious: Filler words ("um", "well"), trailing off, questions
- Intellectual: Complex sentences, qualifications, citations
- Aggressive: Interruptions, commands, challenges
- Timid: Hedging, asking permission, apologizing

Check: Does speech pattern match personality traits?

=== BACKGROUND/HISTORY ===
Past shapes what characters notice and say:
- Trauma survivor: Hypervigilant, notices exits and threats
- Poverty background: Notices food, shelter, scarcity
- Privileged upbringing: Notices comfort, assumes service
- Loss: References to what was lost, fatalistic worldview

Check: Does dialogue reflect their history?

=== THE NO-TAG TEST ===
Critical test: Remove all dialogue tags and action beats.
Can you still tell who is speaking from the dialogue alone?
If not, voices are too similar.

=== VERBAL TICS ===
Each character should have 2-3 unique speech habits:
- Catchphrases
- Favorite words
- Sentence structures
- Ways of starting/ending sentences

For each issue, provide:
1. Character name
2. The problematic dialogue
3. Why it doesn't match their profile
4. A specific rewrite suggestion

=== RELATIONSHIP-DRIVEN NAMING ===
Flag dialogue where characters use each other's FULL NAMES in normal conversation. How
characters address each other reveals their relationship:
- Close friends/family: First name or nickname
- Formal/professional/rivals: Last name or title
- Authority figures: Title + surname
- Enemies: Surname only (clipped, cold)
Flag any mismatch between naming and the established character relationship.

=== CHARACTER PERCEPTION FILTER ===
Flag when a character's observations, thoughts, or metaphors don't match their background
and expertise. A botanist notices plants before books. A soldier notices exits before decor.
A thief notices locks before artwork. Flag generic perception that could belong to ANY
character — observations should be filtered through the character's unique lens of
experience, profession, and personality.

=== DIALOGUE LENGTH CHECK (Butcher Rule) ===
Count words per dialogue line. Most real dialogue is 3-7 words.
- If >40% of lines exceed 10 words, flag: "DIALOGUE_INFLATION: [N]% of lines >10 words."
- Flag any single line >20 words: "MONOLOGUE: break into shorter exchanges or interrupt."
- Check for AI-default complete sentences — real people use fragments, contractions,
  interruptions, and non-answers. "Yeah" instead of "I agree with what you're saying.\""""

    def critique(
        self,
        prose: str,
        characters: list[dict],
        scene_id: str = "unknown"
    ) -> CharacterVoiceCritique:
        """
        Critique character voice authenticity.

        Args:
            prose: The scene prose to critique
            characters: List of character dicts with their profiles
            scene_id: Scene identifier

        Returns:
            CharacterVoiceCritique with voice issues found
        """
        # Format character profiles for the prompt
        char_profiles = []
        for char in characters:
            profile = f"""
CHARACTER: {char.get('name', 'Unknown')}
- Education: {char.get('education', 'Unknown')}
- Profession/Role: {char.get('role', char.get('archetype', 'Unknown'))}
- Personality: {char.get('personality_summary', char.get('personality', 'Unknown'))}
- Background: {char.get('backstory_summary', char.get('backstory', 'Unknown'))}
- Speech Pattern: {char.get('accent', char.get('speech_pattern', 'Standard'))}
- Quirks: {char.get('quirks', [])}
"""
            char_profiles.append(profile)

        char_context = "\n".join(char_profiles)

        prompt = f"""Critique character voice authenticity in this scene.

SCENE ID: {scene_id}

CHARACTER PROFILES FROM CODEX:
{char_context}

PROSE TO CRITIQUE:
{prose}

Evaluate:
1. Does each character's dialogue match their EDUCATION level?
2. Does dialogue reflect their PROFESSION (jargon, frame of reference)?
3. Does speech pattern match their PERSONALITY?
4. Does dialogue reflect their BACKGROUND/HISTORY?
5. NO-TAG TEST: Could you tell who's speaking without tags?
6. Do characters have distinct VERBAL TICS?

For each mismatch, provide:
- Character name
- The problematic dialogue
- Why it doesn't match their profile
- A specific rewrite that matches their voice

Score each factor 1-10 and provide overall voice score."""

        from src.config import get_token_limit
        return self.invoke_structured(prompt, CharacterVoiceCritique, max_tokens=get_token_limit("step6_prose_generation", "prose_critique"))


# =============================================================================
# Persona 3: Continuity Critic
# =============================================================================

class ContinuityCritic(BaseStoryAgent):
    """
    Checks consistency with codex: characters, locations, world rules, timeline.

    Based on professional editing checklists for developmental editing.
    """

    @property
    def name(self) -> str:
        return "CONTINUITY_CRITIC"

    @property
    def role(self) -> str:
        return "Story Continuity & Codex Consistency Specialist"

    @property
    def system_prompt(self) -> str:
        return """You are a continuity editor who catches every inconsistency with established facts.

YOUR MISSION: Compare prose against codex and flag ALL inconsistencies.

=== CHARACTER CONSISTENCY ===
Check against codex profiles:
- Physical descriptions (eye color, hair, scars, height)
- Personality traits (are they acting in character?)
- Quirks and habits (do they appear?)
- Speech patterns (see voice critic)
- Name spelling (consistent throughout)

=== LOCATION CONSISTENCY ===
Check against codex locations:
- Physical layout matches description
- Atmosphere/mood matches location profile
- Key features mentioned
- Sensory details align

=== WORLD RULES ===
Check against world building:
- Magic system rules followed
- Social customs respected
- Taboos acknowledged
- Technology level consistent
- Cultural practices correct

=== TIMELINE & TIME UNITS (CRITICAL) ===
Check for time consistency:
- **TIME UNIT CONSISTENCY**: If ticking clock says "72 hours", that's 3 DAYS not 3 hours!
  - 24 hours = 1 day
  - 48 hours = 2 days
  - 72 hours = 3 days
  - Always convert and verify references match
- Time references must use CONSISTENT UNITS throughout the scene
- "Hours remaining" must decrease logically scene to scene
- Travel time must make sense for distance
- Character knowledge matches timeline

COMMON TIME UNIT ERRORS TO CATCH:
- "72 hours" later mentioned as "3 hours" (WRONG - should be "3 days")
- Mixing hours/days without proper conversion
- Time passing too fast or slow between scenes
- Deadline inconsistency with ticking clock

=== POV CONSISTENCY ===
Stay in ONE head per scene:
- Only know what POV character knows
- Only see what POV character sees
- Internal thoughts only from POV character

=== KNOWLEDGE VIOLATIONS ===
Characters shouldn't know things they can't know:
- Information they weren't present for
- Secrets not revealed to them
- Future events
- Other characters' thoughts

=== CONTRIVANCE CHECK (Sanderson Lantern) ===
Flag plot conveniences that break immersion:
- Coincidental meetings ("just happened to be there")
- Lucky timing ("arrived just in time")
- Characters who conveniently know exactly the right thing
- Problems solved by previously unmentioned abilities

For each contrivance, recommend one of:
(A) Restructure cause-and-effect so it feels earned
(B) Foreshadow it earlier so it doesn't feel random
(C) Hang a lantern — have a character notice the improbability ("That's convenient.")
Option C sparingly — it acknowledges the issue but doesn't fix it.

For each inconsistency, cite:
1. What the prose says
2. What the codex says
3. Why it's a problem
4. How to fix it"""

    def critique(
        self,
        prose: str,
        characters: list[dict],
        location: dict,
        world: dict,
        scene_id: str = "unknown",
        ticking_clock: dict = None
    ) -> ContinuityCritique:
        """
        Critique continuity with codex.

        Args:
            prose: The scene prose to critique
            characters: List of character dicts
            location: Location dict for this scene
            world: World building dict
            scene_id: Scene identifier
            ticking_clock: Ticking clock dict with deadline info

        Returns:
            ContinuityCritique with inconsistencies found
        """
        # Format codex context
        char_context = json.dumps(characters, indent=2, ensure_ascii=False)[:3000]
        loc_context = json.dumps(location, indent=2, ensure_ascii=False)[:1500]
        world_context = json.dumps(world, indent=2, ensure_ascii=False)[:2000]
        clock_context = json.dumps(ticking_clock, indent=2, ensure_ascii=False) if ticking_clock else "Not provided"

        prompt = f"""Check this prose for continuity with the codex.

SCENE ID: {scene_id}

=== CODEX: CHARACTERS ===
{char_context}

=== CODEX: LOCATION ===
{loc_context}

=== CODEX: WORLD ===
{world_context}

=== TICKING CLOCK (verify time references match!) ===
{clock_context}

HOURS REMAINING FOR THIS SCENE: {ticking_clock.get('hours_remaining', '???') if isinstance(ticking_clock, dict) else '???'}
Any time reference in the prose that states MORE hours/time remaining than this is an ERROR.
The timeline must only move FORWARD (hours decrease scene by scene, never increase).

=== PROSE TO CHECK ===
{prose}

Check for:
1. CHARACTER INCONSISTENCIES - traits, appearance, personality not matching codex
2. LOCATION INCONSISTENCIES - description not matching codex
3. TIMELINE ISSUES - events out of order, impossible timing
   - **HOURS REMAINING CHECK**: This scene has {ticking_clock.get('hours_remaining', '???') if isinstance(ticking_clock, dict) else '???'} hours left. Any mention of MORE hours is WRONG.
   - **TIME UNIT CHECK**: If clock says "72 hours", prose must say "3 days" NOT "3 hours"!
   - Verify all time references are consistent with ticking clock
4. WORLD RULE VIOLATIONS - magic system, customs, taboos broken
5. POV BREAKS - knowing things the POV character can't know
6. KNOWLEDGE VIOLATIONS - characters knowing impossible things
7. NAME SPELLING - any spelling variations

For each issue found, cite what the prose says vs what the codex says.
Score overall continuity 1-10."""

        from src.config import get_token_limit
        return self.invoke_structured(prompt, ContinuityCritique, max_tokens=get_token_limit("step6_prose_generation", "prose_critique"))


# =============================================================================
# Persona 4: Pacing & Tension Critic
# =============================================================================

class PacingTensionCritic(BaseStoryAgent):
    """
    Evaluates scene structure, pacing, ticking clock, and hooks.

    Based on scene structure theory (GMC, Swain's Scene/Sequel).
    """

    @property
    def name(self) -> str:
        return "PACING_TENSION_CRITIC"

    @property
    def role(self) -> str:
        return "Pacing & Tension Specialist"

    @property
    def system_prompt(self) -> str:
        return """You are a pacing specialist who ensures scenes have proper tension and structure.

YOUR MISSION: Evaluate scene pacing and tension. Flag problems.

=== SCENE ENTRY ===
"Enter late, exit early"
- Scene should start in motion, not with throat-clearing
- No "parking the car" moments (arriving, getting settled)
- First line should matter to the scene's goal

BAD: "She walked to the door and knocked. The door opened..."
GOOD: "The door opened before she could knock. They were expecting her."

=== SCENE EXIT ===
End at a HOOK, not after resolution:
- Cliffhanger
- Question raised
- Revelation
- Decision that changes things

BAD: "They agreed on the plan and went to bed."
GOOD: "They agreed on the plan. But in the shadows, someone had been listening."

=== TICKING CLOCK ===
The story's ticking clock should be FELT:
- Explicit time references ("Three hours until...")
- Urgency in dialogue ("We don't have time!")
- Characters aware of deadline
- Consequences if deadline missed

If ticking clock is absent, flag it.

=== SLOW SPOTS ===
Flag paragraphs that drag:
- Excessive description unconnected to action
- Info dumps
- Repetitive dialogue
- Characters "parking the car"

=== RUSHED SPOTS ===
Flag areas that need breathing room:
- Action too compressed
- Emotional beats skipped
- No reaction time for characters

=== GMC (Goal-Motivation-Conflict) ===
Scene should have clear:
- GOAL: What does POV character want?
- MOTIVATION: Why do they want it?
- CONFLICT: What's stopping them?

If GMC is unclear, flag it.

=== TENSION ARC ===
Tension should rise and fall within scene:
- Opening hook
- Rising tension
- Peak moment
- Brief release or cliffhanger

Flat tension = boring scene.

=== FLOATING HEADS / MISSING ACTION BEATS ===
Flag dialogue sequences of 4+ ungrounded lines without physical action between them.
Audiobook listeners lose track of who is speaking without action beats anchoring the
exchange. Every 2-3 dialogue lines should have a physical beat (character action, gesture,
movement, environmental detail) to keep the scene grounded and identify speakers."""

    def critique(
        self,
        prose: str,
        scene_data: dict,
        ticking_clock,  # Can be str or dict
        scene_id: str = "unknown"
    ) -> PacingTensionCritique:
        """
        Critique pacing and tension.

        Args:
            prose: The scene prose to critique
            scene_data: Scene metadata (goal, conflict, outcome)
            ticking_clock: The story's ticking clock (str or dict)
            scene_id: Scene identifier

        Returns:
            PacingTensionCritique with pacing issues found
        """
        # Format ticking_clock whether it's str or dict
        if isinstance(ticking_clock, dict):
            clock_text = f"""- Clock: {ticking_clock.get('ticking_clock', 'Unknown')}
- Deadline: {ticking_clock.get('deadline', 'Unknown')}
- Consequence: {ticking_clock.get('consequence', 'Unknown')}
- HOURS REMAINING: {ticking_clock.get('hours_remaining', '???')} — time references must not exceed this"""
        else:
            clock_text = str(ticking_clock)

        prompt = f"""Critique the pacing and tension in this scene.

SCENE ID: {scene_id}

SCENE METADATA:
- Goal: {scene_data.get('goal', 'Unknown')}
- Conflict: {scene_data.get('conflict', 'Unknown')}
- Outcome: {scene_data.get('outcome', 'Unknown')}

STORY'S TICKING CLOCK:
{clock_text}

PROSE TO CRITIQUE:
{prose}

Evaluate:
1. SCENE ENTRY: Does it enter late enough? No throat-clearing?
2. SCENE EXIT: Does it end at a hook?
3. TICKING CLOCK: Is urgency felt? Any explicit references?
4. SLOW SPOTS: Which paragraphs drag? Why?
5. RUSHED SPOTS: Which areas need more breathing room?
6. GMC: Is Goal-Motivation-Conflict clear?
7. TENSION ARC: Does tension rise and fall appropriately?
8. SCENE LENGTH: Appropriate, too long, or too short?

Provide specific paragraph numbers for slow/rushed spots.
Score tension arc and overall pacing 1-10."""

        from src.config import get_token_limit
        return self.invoke_structured(prompt, PacingTensionCritique, max_tokens=get_token_limit("step6_prose_generation", "prose_critique"))


# =============================================================================
# Persona 5: Emotional Resonance Critic
# =============================================================================

class EmotionalResonanceCritic(BaseStoryAgent):
    """
    Checks emotional beats, subtext, reader engagement, and micro-tension.

    Based on micro-tension research and reader engagement studies.
    """

    @property
    def name(self) -> str:
        return "EMOTIONAL_RESONANCE_CRITIC"

    @property
    def role(self) -> str:
        return "Emotional Resonance & Reader Engagement Specialist"

    @property
    def system_prompt(self) -> str:
        return """You are an emotional resonance specialist who ensures readers FEEL the story.

YOUR MISSION: Evaluate emotional impact and reader engagement. Flag weak spots.

=== EMOTIONAL BEATS ===
Scenes need moments where readers FEEL:
- Joy, fear, anger, sadness, surprise
- Connection to character
- Tension and release
- Satisfaction or frustration

If scene is emotionally flat, flag it.

=== SUBTEXT ===
What's NOT said is often more powerful:
- Characters avoiding topics
- Saying one thing, meaning another
- Tension in silence
- Implications and hints

Good dialogue has layers. Flag if subtext is missing.

=== SKIM RISK ===
Where might readers skim or lose interest?
- Long description blocks
- Repetitive dialogue
- Low-stakes conversation
- Info dumps
- Slow paragraphs

Flag specific areas where engagement drops.

=== MICRO-TENSION ===
Every line should pull reader forward:
- Tense words: paused, froze, waited, hid, fled, gulped
- Character contradictions (what they do vs think)
- Unresolved questions
- Unexpected details
- Fresh verbs

If prose lacks line-by-line tension, flag it.

=== VULNERABILITY ===
Readers connect through character vulnerability:
- Fears exposed
- Weaknesses shown
- Emotional honesty
- Internal conflict

If characters feel invulnerable, flag it.

=== SCENE ENDING RESONANCE ===
Scene endings should RESONATE:
- IMAGE: A visual that lingers
- QUESTION: An unspoken question hanging
- ACHE: An emotion the character can't name
- REALIZATION: A small moment that changes everything

"WEAK" = scene just... ends. No resonance.

=== READER EMOTIONAL ARC ===
Track how readers should feel:
- Start of scene: [emotion]
- Middle: [emotion shift]
- End: [final emotional state]

If arc is flat, flag it."""

    def critique(
        self,
        prose: str,
        scene_id: str = "unknown"
    ) -> EmotionalResonanceCritique:
        """
        Critique emotional resonance and reader engagement.

        Args:
            prose: The scene prose to critique
            scene_id: Scene identifier

        Returns:
            EmotionalResonanceCritique with engagement issues found
        """
        prompt = f"""Critique the emotional resonance and reader engagement in this scene.

SCENE ID: {scene_id}

PROSE TO CRITIQUE:
{prose}

Evaluate:
1. EMOTIONAL BEATS: What emotions does scene evoke? Are they earned?
2. SUBTEXT: Where is meaning implied rather than stated?
3. SKIM RISK: Which specific areas might readers skim? Why?
4. MICRO-TENSION: Does each line pull forward? Flag flat areas.
5. VULNERABILITY: Do characters show authentic vulnerability?
6. SCENE ENDING: What type of resonance? (image/question/ache/realization/weak)
7. READER EMOTIONAL ARC: How should reader feel start -> middle -> end?

For skim risk areas, cite specific paragraph numbers.
Score micro-tension and overall emotional resonance 1-10."""

        from src.config import get_token_limit
        return self.invoke_structured(prompt, EmotionalResonanceCritique, max_tokens=get_token_limit("step6_prose_generation", "prose_critique"))


# =============================================================================
# Persona 6: Show Don't Tell Critic
# =============================================================================

class ShowDontTellCritic(BaseStoryAgent):
    """
    Dedicated critic for show-don't-tell violations with specific rewrite suggestions.

    Goes beyond flagging filter words — identifies abstract narrator commentary,
    emotion labeling, reinforcement telling, and missing dialogue opportunities.
    Every violation comes with a concrete rewrite suggestion.
    """

    @property
    def name(self) -> str:
        return "SHOW_DONT_TELL_CRITIC"

    @property
    def role(self) -> str:
        return "Show Don't Tell Specialist"

    @property
    def system_prompt(self) -> str:
        return """You are a show-don't-tell specialist. Your ONLY job is finding places where
the prose TELLS the reader instead of SHOWING them, and providing specific rewrites.

=== FILTER WORD VIOLATIONS ===
Find every instance where a filter word creates narrator distance.
For each, provide the original line AND a specific rewrite:

FILTER WORD → REWRITE PATTERN:
"[Char] heard X" → Write X directly: "Footsteps echoed off the stone."
"[Char] felt X" → Write the sensation: "Cold crawled up her spine."
"[Char] saw X" → Write the visual: "The blade glinted in the torchlight."
"[Char] realized X" → Show insight as fragments: "The lock. Same make as the vault."
"[Char] knew X" → State as narration: "The north gate would be unguarded."
"[Char] wondered X" → Ask directly: "Why now? Why here?"
"[Char] noticed X" → Write X: "A scratch on the doorframe. Fresh."
"[Char] remembered X" → Drop into memory: "Last time, the rope had snapped."

=== ABSTRACT NARRATOR COMMENTARY ===
Flag lines where the narrator summarizes instead of dramatizing:
- "Tension filled the room" → What are the characters' hands/eyes/feet doing?
- "Every second counted" → Show the clock, the obstacle, the sweat
- "A sense of unease settled over them" → Show fidgeting, glancing, grip tightening
- "The atmosphere was oppressive" → Show specific sensory details
- "A [adj] voice [verbed]" → Write what was ACTUALLY SAID

=== EMOTION LABELS ===
Flag every instance of naming an emotion instead of showing it:
- "She was angry" → "Her fingers whitened on the cup handle."
- "He was afraid" → "His mouth went dry. The key slipped in his grip."
- "She felt sad" → "She set a second plate at the table, then put it back."
- "He was nervous" → Show specific physical tells from character's behavioral_signature

=== REINFORCEMENT TELLING ===
Flag paragraphs that restate what the scene already showed through action/dialogue:
- If a character just slammed a door (SHOWN), a following line saying "She was furious" (TOLD) is redundant
- If dialogue revealed a secret, narration explaining "the secret was now out" is redundant
- Trust the reader. If you showed it, don't tell it again.

=== MISSING DIALOGUE OPPORTUNITIES ===
Flag places where the narrator explains something that could be a brief exchange:
- "She told him about the plan" → Write the actual conversation
- "They argued about the route" → Show 2-3 lines of the argument
- "He convinced her to stay" → Show the persuasion happening

=== GENERIC SENSORY CATALOGS ===
Flag laundry lists of sensory details without character anchoring:
- "The scent of pine, earth, and woodsmoke" → Pick ONE, anchor to character memory
  "Pine. Like the cabin where they'd hidden that winter."

=== CINEMATIC TEST ===
Flag anything a camera couldn't capture — internal narrator commentary disguised as prose:
- "Little did she know..." (narrator intrusion)
- "What he didn't realize was..." (omniscient distance)
- "In that moment, everything changed." (abstract summary)

For each violation, provide:
1. The exact offending text
2. Which category it falls under
3. A SPECIFIC rewrite suggestion (not just "show don't tell")

Score the overall show-don't-tell quality 1-10."""

    def critique(
        self,
        prose: str,
        scene_id: str = "unknown",
    ) -> ShowDontTellCritique:
        """
        Critique show-don't-tell quality with specific rewrite suggestions.

        Args:
            prose: The scene prose to critique
            scene_id: Scene identifier

        Returns:
            ShowDontTellCritique with violations and specific rewrites
        """
        prompt = f"""Analyze this prose for show-don't-tell violations. For EVERY violation,
provide the exact text AND a specific rewrite suggestion.

SCENE ID: {scene_id}

PROSE TO CRITIQUE:
{prose}

Find ALL instances of:
1. FILTER WORDS (heard/saw/felt/noticed/realized/knew/wondered/remembered) — provide rewrite for each
2. ABSTRACT NARRATOR LINES (tension filled, sense of, atmosphere was) — provide concrete replacement
3. EMOTION LABELS (was angry/afraid/sad/nervous) — provide behavioral alternative
4. REINFORCEMENT TELLS (narrator restating what was already shown)
5. MISSING DIALOGUE OPPORTUNITIES (narrator summarizing what could be a conversation)

For filter_word_violations, abstract_narrator_lines, and emotion_labels:
Format each as: "ORIGINAL: [exact text] → REWRITE: [specific suggestion]"

Score overall show-don't-tell quality 1-10 (10 = fully dramatized, no telling).
Provide top 3-5 highest-impact suggestions."""

        from src.config import get_token_limit
        return self.invoke_structured(prompt, ShowDontTellCritique, max_tokens=get_token_limit("step6_prose_generation", "prose_critique"))
