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

Be thorough. Miss nothing."""

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
4. A specific rewrite suggestion"""

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

=== PROSE TO CHECK ===
{prose}

Check for:
1. CHARACTER INCONSISTENCIES - traits, appearance, personality not matching codex
2. LOCATION INCONSISTENCIES - description not matching codex
3. TIMELINE ISSUES - events out of order, impossible timing
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

Flat tension = boring scene."""

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
- Consequence: {ticking_clock.get('consequence', 'Unknown')}"""
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
