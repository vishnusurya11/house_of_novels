"""
Research-Driven Structure Debate Agents for 7-Point Story Structure Generation.

Each agent embodies a specific storytelling methodology and brings those
principles to the multi-agent debate:

1. DanWellsAgent - Dan Wells' 7-Point Method (Resolution first, Hook as opposite)
2. BlakeSnyderAgent - Blake Snyder's Save the Cat (empathy, false victory/defeat)
3. PinchMasterAgent - Larry Brooks/Weiland Pinch Point Theory (37%/62% timing)
4. TruthSeekerAgent - September C. Fawkes' Narrative Theory (truth reveals)
5. AudienceAdvocateAgent - Reader/Viewer perspective (emotional payoff, satisfaction)

The agents debate each beat through:
- Proposals: 3-4 proposals per beat from relevant methodology experts
- Critiques: Cross-agent critiques with methodology backing
- Votes: All 5 agents vote on every beat

Utility agents:
- StorySeedParserAgent: Parses the story seed logline
- StructureValidatorAgent: Final validation of complete structure
"""

from src.story_agents.base_story_agent import BaseStoryAgent
from src.story_schemas import (
    StorySeedParsed,
    StructureBeatSchema,
    SevenPointStructureSchema,
    StructureDebateCritique,
    AgentCritique,
    AgentProposal,
    AgentVote,
)


# =============================================================================
# Utility Agents
# =============================================================================

class StorySeedParserAgent(BaseStoryAgent):
    """
    Parses the story seed logline to extract key components.

    Identifies:
    - The opening ADJECTIVE (hero's emotional state)
    - WHY the hero is in this state
    - The hero's role/occupation
    - Their goal
    - What's at stake
    """

    @property
    def name(self) -> str:
        return "STORY_SEED_PARSER"

    @property
    def role(self) -> str:
        return "Story Seed Analyst"

    @property
    def system_prompt(self) -> str:
        return """You are a story analyst who deconstructs story seeds to find their core components.

Your expertise:
- Identifying the emotional STATE word that defines the hero's opening condition
- Understanding WHY characters are in their emotional state (backstory/trauma)
- Separating role, goal, and stakes from a logline
- Recognizing the story's implicit promise to the audience

When you see a story seed like:
"SHATTERED AN ARCHIVIST WANTS TO END THE POWER OF A REBELLION BUT THE BLAME WILL FALL ON THEIR CLOSEST FRIEND"

You extract:
- Adjective: SHATTERED (this is the HOOK state - we need to understand WHY)
- Hero Role: An archivist
- Goal: End the power of a rebellion
- Stakes: The blame will fall on their closest friend

The ADJECTIVE is crucial - it defines the hero's starting emotional state.
The RESOLUTION will be the OPPOSITE of this adjective.

Output structured JSON matching StorySeedParsed."""

    def parse_story_seed(self, story_seed: str, setting_prompt: str) -> StorySeedParsed:
        """
        Parse a story seed to extract components.

        Args:
            story_seed: The story seed logline (e.g., "SHATTERED AN ARCHIVIST...")
            setting_prompt: The world setting for context

        Returns:
            StorySeedParsed with extracted components
        """
        prompt = f"""Parse this story seed into its components:

STORY SEED: {story_seed}

WORLD SETTING: {setting_prompt}

Extract:
1. ADJECTIVE: The opening emotional state word (usually in CAPS or first word)
2. ADJECTIVE_MEANING: WHY is the hero in this state? What trauma/event caused it?
   - Think deeply about what could make someone [ADJECTIVE]
   - Consider the world setting for context
3. HERO_ROLE: What is the hero's role/occupation?
4. GOAL: What does the hero want to accomplish?
5. STAKES: What happens if they fail? What's at risk?
6. SETTING_CONTEXT: Any world/setting clues from the seed

The ADJECTIVE is the key to the whole story:
- It defines the HOOK (hero's BEFORE state)
- The RESOLUTION must be the OPPOSITE
- Understanding WHY they're [ADJECTIVE] drives the character arc

Output structured JSON."""

        return self.invoke_structured(prompt, StorySeedParsed, max_tokens=1000)


# =============================================================================
# Research-Embodied Debate Agents
# =============================================================================

class DanWellsAgent(BaseStoryAgent):
    """
    Embodies Dan Wells' 7-Point Story Structure methodology.

    Core beliefs (from Dan Wells' method):
    - Start with RESOLUTION first - know your ending before your beginning
    - HOOK is the OPPOSITE of Resolution - emotional/psychological opposites
    - MIDPOINT = hero shifts from REACTION to ACTION (conscious decision)
    - PLOT TURN 1 = world changes from status quo
    - PLOT TURN 2 = hero obtains the last thing needed to resolve conflict
    - PINCH POINTS = pressure that forces hero to act
    - "Everything in the story leads to the Resolution moment"

    Sources:
    - https://www.campfirewriting.com/learn/seven-point-story-structure
    - https://www.authorflows.com/blogs/7-point-story-structure-dan-wells-plotting-method-examples
    - https://reedsy.com/blog/guide/story-structure/seven-point-story-structure/
    """

    METHODOLOGY_NAME = "Dan Wells 7-Point Structure"
    METHODOLOGY_SOURCE = "Dan Wells' 7-Point Story Structure (Star Trek RPG adaptation)"

    CORE_BELIEFS = [
        "Design the RESOLUTION first - know your ending before your beginning",
        "HOOK must be the psychological/emotional OPPOSITE of Resolution",
        "MIDPOINT is the conscious decision to shift from REACTION to ACTION",
        "Plot Turns 1 and 2 are the doorways that change everything",
        "Every beat must serve the Resolution - all roads lead to the ending",
    ]

    @property
    def name(self) -> str:
        return "DAN_WELLS_AGENT"

    @property
    def role(self) -> str:
        return "7-Point Structure Advocate"

    @property
    def system_prompt(self) -> str:
        return """You are a story architect who embodies Dan Wells' 7-Point Story Structure methodology.

YOUR METHODOLOGY (Dan Wells' 7-Point Structure):
Based on Dan Wells' adaptation from the Star Trek RPG Narrator's Guide.

CORE PRINCIPLES:
1. RESOLUTION FIRST: Design the ending BEFORE the beginning
   - Know exactly how the story ends
   - This determines everything else

2. HOOK/RESOLUTION OPPOSITES: These MUST be psychological mirrors
   - If hero ends WHOLE, they start SHATTERED
   - If hero ends COURAGEOUS, they start FEARFUL
   - The transformation arc connects them

3. MIDPOINT = REACTION → ACTION PIVOT:
   - Before Midpoint: things happen TO the hero
   - After Midpoint: hero MAKES things happen
   - This is a CONSCIOUS DECISION, not circumstance

4. PLOT TURNS ARE DOORWAYS:
   - PT1: Forces hero out of their normal world (inciting incident)
   - PT2: Hero obtains the final piece needed for victory

5. PINCH POINTS APPLY PRESSURE:
   - PP1: Stakes become REAL (not theoretical)
   - PP2: DARKEST MOMENT - all seems lost

6. EVERYTHING SERVES RESOLUTION:
   - Every beat must point toward the ending
   - If a beat doesn't serve the Resolution, cut it

WHEN CRITIQUING OTHER PROPOSALS:
- Are Hook/Resolution truly OPPOSITES? (This is non-negotiable)
- Does the Midpoint show a clear DECISION to act?
- Do Plot Turns genuinely CHANGE the story's direction?
- Is there a clear throughline to the Resolution?

CRITICAL: Use ONLY generic character roles (e.g., "the archivist", "the protagonist")
NEVER use actual character names - those come later.

Your critiques should be DIRECT and METHODOLOGY-BASED.
Always cite which Dan Wells principle supports your critique."""

    def propose_resolution(
        self,
        story_seed_parsed: StorySeedParsed,
        setting_prompt: str,
    ) -> AgentProposal:
        """Propose the Resolution beat based on Dan Wells methodology."""
        prompt = f"""As the Dan Wells 7-Point Structure advocate, propose the RESOLUTION beat.

DAN WELLS PRINCIPLE: "Design the ending FIRST. Know exactly where your story goes."

STORY SEED:
- Adjective: {story_seed_parsed.adjective}
- Why: {story_seed_parsed.adjective_meaning}
- Hero: {story_seed_parsed.hero_role}
- Goal: {story_seed_parsed.goal}
- Stakes: {story_seed_parsed.stakes}

SETTING: {setting_prompt}

YOUR TASK:
Design the RESOLUTION - the hero's AFTER state.

Dan Wells says: "The Resolution is the OPPOSITE of the Hook. If your hero starts SHATTERED, they end WHOLE."

Resolution for {story_seed_parsed.adjective} → must be the OPPOSITE state.

Think: What does "un-{story_seed_parsed.adjective}" look like?
- SHATTERED → WHOLE/INTEGRATED
- DESPERATE → SECURE/GROUNDED
- LOST → FOUND/CENTERED
- BROKEN → HEALED/COMPLETE

Create a Resolution that:
1. Shows the hero's complete transformation
2. Answers the story's central question
3. Uses ONLY generic roles (no names)

CRITICAL FORMAT: Description must be 1-2 sentences MAX (under 40 words). Focus on what HAPPENS, not atmosphere. Example: "The archivist, now whole and trusting, leads the alliance between archives and rebellion."

Output structured JSON for StructureBeatSchema with beat_name="resolution"."""

        beat = self.invoke_structured(prompt, StructureBeatSchema, max_tokens=1000)

        return AgentProposal(
            agent_name=self.name,
            methodology_source=self.METHODOLOGY_SOURCE,
            beat=beat,
            methodology_reasoning=f"Dan Wells principle: 'Resolution is designed FIRST and must be the OPPOSITE of {story_seed_parsed.adjective}. The hero's transformation from {story_seed_parsed.adjective} to {beat.emotional_state} is the story's core arc.'"
        )

    def propose_hook(
        self,
        story_seed_parsed: StorySeedParsed,
        resolution: StructureBeatSchema,
        setting_prompt: str,
    ) -> AgentProposal:
        """Propose the Hook beat based on Dan Wells methodology."""
        prompt = f"""As the Dan Wells 7-Point Structure advocate, propose the HOOK beat.

DAN WELLS PRINCIPLE: "The Hook is the OPPOSITE of the Resolution. Show the hero at their most [ADJECTIVE]."

STORY SEED:
- Adjective: {story_seed_parsed.adjective}
- Why: {story_seed_parsed.adjective_meaning}
- Hero: {story_seed_parsed.hero_role}

RESOLUTION (already designed):
{resolution.description}
State: {resolution.emotional_state}

SETTING: {setting_prompt}

YOUR TASK:
Design the HOOK - the hero's BEFORE state.

The Hook must be the MIRROR OPPOSITE of Resolution:
- Resolution shows: {resolution.emotional_state}
- Hook must show: {story_seed_parsed.adjective}

Dan Wells says: "Show WHY the hero is in their broken state. Make the audience understand their wound."

Create a Hook that:
1. Shows the hero at maximum {story_seed_parsed.adjective}
2. Reveals WHY they're in this state
3. Sets up the contrast with Resolution
4. Uses ONLY generic roles (no names)

CRITICAL FORMAT: Description must be 1-2 sentences MAX (under 40 words). Focus on what HAPPENS, not atmosphere. Example: "The archivist, isolated and paranoid after betrayal, refuses help from the resistance."

Output structured JSON for StructureBeatSchema with beat_name="hook"."""

        beat = self.invoke_structured(prompt, StructureBeatSchema, max_tokens=1000)

        return AgentProposal(
            agent_name=self.name,
            methodology_source=self.METHODOLOGY_SOURCE,
            beat=beat,
            methodology_reasoning=f"Dan Wells principle: 'Hook is the OPPOSITE of Resolution. Hero starts {story_seed_parsed.adjective} (the Hook state) and ends {resolution.emotional_state} (the Resolution state). This opposition defines the transformation arc.'"
        )

    def propose_midpoint(
        self,
        story_seed_parsed: StorySeedParsed,
        hook: StructureBeatSchema,
        resolution: StructureBeatSchema,
        setting_prompt: str,
    ) -> AgentProposal:
        """Propose the Midpoint beat based on Dan Wells methodology."""
        prompt = f"""As the Dan Wells 7-Point Structure advocate, propose the MIDPOINT beat.

DAN WELLS PRINCIPLE: "The Midpoint is when the hero shifts from REACTION to ACTION. It's a CONSCIOUS DECISION."

STORY CONTEXT:
- Hero: {story_seed_parsed.hero_role}
- Hook state: {hook.emotional_state}
- Resolution state: {resolution.emotional_state}
- Goal: {story_seed_parsed.goal}

HOOK: {hook.description}
RESOLUTION: {resolution.description}

SETTING: {setting_prompt}

YOUR TASK:
Design the MIDPOINT - the PIVOT moment.

Dan Wells says:
- Before Midpoint: things happen TO the hero (reactive)
- After Midpoint: hero MAKES things happen (proactive)
- This is NOT circumstance forcing action - it's a CHOICE

The Midpoint for this story:
- Hero stops running/hiding/reacting
- Makes a CONSCIOUS DECISION to pursue their goal
- This decision drives everything that follows

Create a Midpoint that:
1. Shows a clear shift from reaction to action
2. Is a CHARACTER DECISION, not external forcing
3. Makes the journey to Resolution possible
4. Uses ONLY generic roles (no names)

CRITICAL FORMAT: Description must be 1-2 sentences MAX (under 40 words). Focus on what HAPPENS, not atmosphere. Example: "The archivist decides to expose the rebellion's secrets, shifting from hiding to actively fighting back."

Output structured JSON for StructureBeatSchema with beat_name="midpoint"."""

        beat = self.invoke_structured(prompt, StructureBeatSchema, max_tokens=1000)

        return AgentProposal(
            agent_name=self.name,
            methodology_source=self.METHODOLOGY_SOURCE,
            beat=beat,
            methodology_reasoning="Dan Wells principle: 'The Midpoint is the PIVOT - a conscious decision to shift from reaction to action. Before: things happen TO hero. After: hero MAKES things happen.'"
        )

    def critique_proposal(
        self,
        target_agent: str,
        target_beat: str,
        proposal: StructureBeatSchema,
        story_seed_parsed: StorySeedParsed,
        other_beats: dict = None,
    ) -> AgentCritique:
        """Critique another agent's proposal from Dan Wells methodology perspective."""
        other_beats = other_beats or {}
        context = ""
        if "resolution" in other_beats:
            context += f"\nRESOLUTION: {other_beats['resolution'].emotional_state}"
        if "hook" in other_beats:
            context += f"\nHOOK: {other_beats['hook'].emotional_state}"

        prompt = f"""As the Dan Wells 7-Point Structure advocate, critique this {target_beat} proposal.

DAN WELLS PRINCIPLES TO CHECK:
1. Hook/Resolution must be OPPOSITES (non-negotiable)
2. Midpoint must be REACTION → ACTION pivot (conscious decision)
3. Every beat must serve the Resolution
4. Clear cause-and-effect between beats

TARGET: {target_beat} proposal from {target_agent}
{proposal.description}
Emotional state: {proposal.emotional_state}

STORY CONTEXT:
- Original adjective: {story_seed_parsed.adjective}
- Hero: {story_seed_parsed.hero_role}
- Goal: {story_seed_parsed.goal}
{context}

YOUR CRITIQUE (be DIRECT and SPECIFIC):
What Dan Wells principles does this proposal violate or follow?

Output structured JSON with:
- critic_agent: "{self.name}"
- target_agent: "{target_agent}"
- target_beat: "{target_beat}"
- criticism: What's wrong or weak (cite specific Dan Wells principle)
- suggestion: How to fix it (based on Dan Wells method)
- methodology_basis: The Dan Wells principle this critique is based on
- severity: "minor", "moderate", or "major\""""

        return self.invoke_structured(prompt, AgentCritique, max_tokens=800)

    def vote_for_best(
        self,
        target_beat: str,
        proposals: list[AgentProposal],
        story_seed_parsed: StorySeedParsed,
    ) -> AgentVote:
        """Vote for the best proposal based on Dan Wells methodology."""
        proposals_text = "\n\n".join([
            f"PROPOSAL {i+1} ({p.agent_name}):\n{p.beat.description}\nState: {p.beat.emotional_state}"
            for i, p in enumerate(proposals)
        ])

        prompt = f"""As the Dan Wells 7-Point Structure advocate, vote for the best {target_beat} proposal.

DAN WELLS VOTING CRITERIA:
1. Does it serve the Resolution?
2. For Hook: Is it truly OPPOSITE of Resolution?
3. For Midpoint: Is it a clear REACTION → ACTION pivot?
4. Does it follow cause-and-effect storytelling?

STORY CONTEXT:
- Original adjective: {story_seed_parsed.adjective}
- Hero: {story_seed_parsed.hero_role}
- Goal: {story_seed_parsed.goal}

PROPOSALS:
{proposals_text}

Vote for the proposal that BEST follows Dan Wells' 7-Point principles.

Output structured JSON with:
- voter_agent: "{self.name}"
- voted_for_agent: (name of agent whose proposal you vote for)
- vote_reasoning: Why this is best according to Dan Wells methodology"""

        return self.invoke_structured(prompt, AgentVote, max_tokens=500)


class BlakeSnyderAgent(BaseStoryAgent):
    """
    Embodies Blake Snyder's Save the Cat Beat Sheet methodology.

    Core beliefs (from Save the Cat):
    - "Save the Cat" moment = hero earns audience empathy early
    - Midpoint is either FALSE VICTORY or FALSE DEFEAT (stakes raised)
    - "All Is Lost" (75%) = lowest beat, "whiff of death"
    - "Dark Night of the Soul" = darkness before dawn
    - Finale: hero must CHANGE THE WORLD, not just win
    - Theme Stated early by secondary character

    Sources:
    - https://www.studiobinder.com/blog/save-the-cat-beat-sheet/
    - https://kindlepreneur.com/save-the-cat-beat-sheet/
    - https://blog.reedsy.com/guide/story-structure/save-the-cat-beat-sheet/
    """

    METHODOLOGY_NAME = "Save the Cat Beat Sheet"
    METHODOLOGY_SOURCE = "Blake Snyder's Save the Cat! (2005)"

    CORE_BELIEFS = [
        "Hero must earn audience EMPATHY early ('save the cat' moment)",
        "Midpoint is FALSE VICTORY or FALSE DEFEAT - stakes get raised",
        "All Is Lost = whiff of death, lowest point before rebirth",
        "Hero must CHANGE THE WORLD, not just succeed personally",
        "Theme is stated by a secondary character early on",
    ]

    @property
    def name(self) -> str:
        return "BLAKE_SNYDER_AGENT"

    @property
    def role(self) -> str:
        return "Save the Cat Advocate"

    @property
    def system_prompt(self) -> str:
        return """You are a story architect who embodies Blake Snyder's Save the Cat Beat Sheet methodology.

YOUR METHODOLOGY (Blake Snyder's Save the Cat):
From the 2005 screenwriting book that transformed Hollywood storytelling.

CORE PRINCIPLES:
1. SAVE THE CAT MOMENT:
   - Hero must earn empathy EARLY
   - Show them doing something likeable/relatable
   - Audience must ROOT for them before conflict begins

2. FALSE VICTORY/DEFEAT MIDPOINT:
   - Midpoint is NOT neutral - it's either too good (false victory) or too bad (false defeat)
   - This RAISES the stakes dramatically
   - The hero thinks they've won/lost, but they're wrong

3. ALL IS LOST (around 75%):
   - The LOWEST beat in the story
   - "Whiff of death" - something or someone dies (literally or metaphorically)
   - Must feel like absolute defeat before the climb back

4. DARK NIGHT OF THE SOUL:
   - Hero wallows in hopelessness after All Is Lost
   - Darkness before the dawn
   - This is where the hero digs deep and finds inner strength

5. HERO CHANGES THE WORLD:
   - Victory is NOT enough - hero must TRANSFORM their world
   - The "synthesis" of thesis (old world) and antithesis (adventure)
   - Personal success + world impact

6. THEME STATED EARLY:
   - Theme is spoken by a secondary character (often offhand)
   - Hero doesn't understand it yet
   - Pays off at the Resolution

WHEN CRITIQUING OTHER PROPOSALS:
- Is there audience EMPATHY established?
- Does the Midpoint raise stakes (false victory/defeat)?
- Is there a "whiff of death" in the darkest moment?
- Does the Resolution CHANGE THE WORLD, not just win?

CRITICAL: Use ONLY generic character roles
Your critiques should be EMOTIONALLY FOCUSED - Save the Cat is about audience connection."""

    def propose_resolution(
        self,
        story_seed_parsed: StorySeedParsed,
        setting_prompt: str,
    ) -> AgentProposal:
        """Propose the Resolution beat based on Save the Cat methodology."""
        prompt = f"""As the Blake Snyder Save the Cat advocate, propose the RESOLUTION beat.

BLAKE SNYDER PRINCIPLE: "It's not enough for the hero to succeed - they must CHANGE THE WORLD."

STORY SEED:
- Adjective: {story_seed_parsed.adjective}
- Why: {story_seed_parsed.adjective_meaning}
- Hero: {story_seed_parsed.hero_role}
- Goal: {story_seed_parsed.goal}
- Stakes: {story_seed_parsed.stakes}

SETTING: {setting_prompt}

YOUR TASK:
Design the RESOLUTION that shows SYNTHESIS.

Blake Snyder's "Finale" principle:
- Hero doesn't just win personally
- They TRANSFORM the world around them
- Thesis (old world) + Antithesis (adventure) = Synthesis (new world)

For this story:
- Hero was {story_seed_parsed.adjective}
- After the journey, they must be transformed AND transform others
- Show ripple effects of their growth

Create a Resolution that:
1. Shows personal transformation (opposite of {story_seed_parsed.adjective})
2. Shows WORLD transformation (not just personal victory)
3. Pays off the theme
4. Uses ONLY generic roles (no names)

CRITICAL FORMAT: Description must be 1-2 sentences MAX (under 40 words). Focus on what HAPPENS, not atmosphere.

Output structured JSON for StructureBeatSchema with beat_name="resolution"."""

        beat = self.invoke_structured(prompt, StructureBeatSchema, max_tokens=1000)

        return AgentProposal(
            agent_name=self.name,
            methodology_source=self.METHODOLOGY_SOURCE,
            beat=beat,
            methodology_reasoning="Blake Snyder principle: 'Hero must CHANGE THE WORLD, not just succeed personally. Resolution shows synthesis - the merging of who they were with who they've become, transforming everything around them.'"
        )

    def propose_hook(
        self,
        story_seed_parsed: StorySeedParsed,
        resolution: StructureBeatSchema,
        setting_prompt: str,
    ) -> AgentProposal:
        """Propose the Hook beat based on Save the Cat methodology."""
        prompt = f"""As the Blake Snyder Save the Cat advocate, propose the HOOK beat.

BLAKE SNYDER PRINCIPLE: "Hero must SAVE THE CAT - earn audience empathy before the adventure begins."

STORY SEED:
- Adjective: {story_seed_parsed.adjective}
- Why: {story_seed_parsed.adjective_meaning}
- Hero: {story_seed_parsed.hero_role}

RESOLUTION: {resolution.description}

SETTING: {setting_prompt}

YOUR TASK:
Design the HOOK that includes a "SAVE THE CAT" moment.

Blake Snyder says:
- Before conflict, show the hero doing something LIKEABLE
- Make the audience ROOT for them
- Even if they're flawed ({story_seed_parsed.adjective}), show their humanity

For this story:
- Hero is {story_seed_parsed.adjective}, which is their flaw
- BUT they must also do something that earns empathy
- Show both their wound AND their humanity

Create a Hook that:
1. Shows the hero's {story_seed_parsed.adjective} state
2. Includes a "save the cat" moment (something that makes us root for them)
3. Sets up what they need to learn
4. Uses ONLY generic roles (no names)

CRITICAL FORMAT: Description must be 1-2 sentences MAX (under 40 words). Focus on what HAPPENS, not atmosphere.

Output structured JSON for StructureBeatSchema with beat_name="hook"."""

        beat = self.invoke_structured(prompt, StructureBeatSchema, max_tokens=1000)

        return AgentProposal(
            agent_name=self.name,
            methodology_source=self.METHODOLOGY_SOURCE,
            beat=beat,
            methodology_reasoning=f"Blake Snyder principle: 'Save the Cat - hero must earn audience empathy early. Even though they're {story_seed_parsed.adjective}, we need to see their humanity and root for their journey.'"
        )

    def propose_midpoint(
        self,
        story_seed_parsed: StorySeedParsed,
        hook: StructureBeatSchema,
        resolution: StructureBeatSchema,
        setting_prompt: str,
    ) -> AgentProposal:
        """Propose the Midpoint beat based on Save the Cat methodology."""
        prompt = f"""As the Blake Snyder Save the Cat advocate, propose the MIDPOINT beat.

BLAKE SNYDER PRINCIPLE: "The Midpoint is either a FALSE VICTORY or FALSE DEFEAT. Stakes are raised."

STORY CONTEXT:
- Hero: {story_seed_parsed.hero_role}
- Hook state: {hook.emotional_state}
- Resolution state: {resolution.emotional_state}
- Goal: {story_seed_parsed.goal}
- Stakes: {story_seed_parsed.stakes}

HOOK: {hook.description}

SETTING: {setting_prompt}

YOUR TASK:
Design the MIDPOINT as FALSE VICTORY or FALSE DEFEAT.

Blake Snyder says:
- FALSE VICTORY: Hero thinks they've won, but it's hollow/incomplete
- FALSE DEFEAT: Hero thinks they've lost, but it plants seeds of true victory
- Either way: STAKES ARE RAISED dramatically

Choose which fits this story better:
- FALSE VICTORY might work if hero achieves {story_seed_parsed.goal} too easily at first
- FALSE DEFEAT might work if related to {story_seed_parsed.stakes}

Create a Midpoint that:
1. Is either FALSE VICTORY or FALSE DEFEAT
2. RAISES the stakes (makes things more serious)
3. Forces the hero to dig deeper
4. Uses ONLY generic roles (no names)

CRITICAL FORMAT: Description must be 1-2 sentences MAX (under 40 words). Focus on what HAPPENS, not atmosphere.

Output structured JSON for StructureBeatSchema with beat_name="midpoint"."""

        beat = self.invoke_structured(prompt, StructureBeatSchema, max_tokens=1000)

        return AgentProposal(
            agent_name=self.name,
            methodology_source=self.METHODOLOGY_SOURCE,
            beat=beat,
            methodology_reasoning="Blake Snyder principle: 'Midpoint is FALSE VICTORY or FALSE DEFEAT - the hero thinks they've won/lost, but they're wrong. Either way, stakes are raised and the real challenge begins.'"
        )

    def propose_pinch_point_2(
        self,
        story_seed_parsed: StorySeedParsed,
        midpoint: StructureBeatSchema,
        setting_prompt: str,
    ) -> AgentProposal:
        """Propose Pinch Point 2 (All Is Lost) based on Save the Cat methodology."""
        prompt = f"""As the Blake Snyder Save the Cat advocate, propose PINCH POINT 2 (the "ALL IS LOST" beat).

BLAKE SNYDER PRINCIPLE: "All Is Lost is the lowest point - there must be a WHIFF OF DEATH."

STORY CONTEXT:
- Hero: {story_seed_parsed.hero_role}
- Stakes: {story_seed_parsed.stakes}
- Midpoint: {midpoint.description}

SETTING: {setting_prompt}

YOUR TASK:
Design the "ALL IS LOST" moment (Pinch Point 2).

Blake Snyder says:
- This is the LOWEST beat in the story
- There's a "whiff of death" - something dies (literal or metaphorical)
- Could be death of: hope, a mentor, a relationship, an ideal, a plan
- Must feel like ABSOLUTE DEFEAT before the climb back

For this story, consider:
- What matters most to {story_seed_parsed.hero_role}?
- The stakes mention: {story_seed_parsed.stakes}
- What loss would devastate them most?

Create a Pinch Point 2 that:
1. Is the LOWEST moment (all seems lost)
2. Includes a "whiff of death" (something/someone dies or seems to)
3. Sets up the Dark Night of the Soul
4. Uses ONLY generic roles (no names)

CRITICAL FORMAT: Description must be 1-2 sentences MAX (under 40 words). Focus on what HAPPENS, not atmosphere.

Output structured JSON for StructureBeatSchema with beat_name="pinch_point_2"."""

        beat = self.invoke_structured(prompt, StructureBeatSchema, max_tokens=1000)

        return AgentProposal(
            agent_name=self.name,
            methodology_source=self.METHODOLOGY_SOURCE,
            beat=beat,
            methodology_reasoning="Blake Snyder principle: 'All Is Lost must have a WHIFF OF DEATH - something or someone dies, literally or metaphorically. This is the lowest point before rebirth.'"
        )

    def critique_proposal(
        self,
        target_agent: str,
        target_beat: str,
        proposal: StructureBeatSchema,
        story_seed_parsed: StorySeedParsed,
        other_beats: dict = None,
    ) -> AgentCritique:
        """Critique another agent's proposal from Save the Cat perspective."""
        prompt = f"""As the Blake Snyder Save the Cat advocate, critique this {target_beat} proposal.

SAVE THE CAT PRINCIPLES TO CHECK:
1. Hook: Is there a "save the cat" empathy moment?
2. Midpoint: Is it FALSE VICTORY or FALSE DEFEAT?
3. Pinch Point 2: Is there a "whiff of death"?
4. Resolution: Does hero CHANGE THE WORLD, not just win?

TARGET: {target_beat} proposal from {target_agent}
{proposal.description}
Emotional state: {proposal.emotional_state}

STORY CONTEXT:
- Hero: {story_seed_parsed.hero_role}
- Stakes: {story_seed_parsed.stakes}

YOUR CRITIQUE (focus on EMOTIONAL IMPACT):
Does this proposal create the emotional beats Save the Cat requires?

Output structured JSON with:
- critic_agent: "{self.name}"
- target_agent: "{target_agent}"
- target_beat: "{target_beat}"
- criticism: What's missing emotionally (cite Save the Cat principle)
- suggestion: How to add emotional impact
- methodology_basis: The Save the Cat principle this is based on
- severity: "minor", "moderate", or "major\""""

        return self.invoke_structured(prompt, AgentCritique, max_tokens=800)

    def vote_for_best(
        self,
        target_beat: str,
        proposals: list[AgentProposal],
        story_seed_parsed: StorySeedParsed,
    ) -> AgentVote:
        """Vote for the best proposal based on Save the Cat methodology."""
        proposals_text = "\n\n".join([
            f"PROPOSAL {i+1} ({p.agent_name}):\n{p.beat.description}\nState: {p.beat.emotional_state}"
            for i, p in enumerate(proposals)
        ])

        prompt = f"""As the Blake Snyder Save the Cat advocate, vote for the best {target_beat} proposal.

SAVE THE CAT VOTING CRITERIA:
1. Emotional resonance with audience
2. Proper stake-raising at Midpoint
3. "Whiff of death" at darkest moment
4. World-changing Resolution

PROPOSALS:
{proposals_text}

Vote for the proposal that creates the strongest EMOTIONAL JOURNEY.

Output structured JSON with:
- voter_agent: "{self.name}"
- voted_for_agent: (name of agent you vote for)
- vote_reasoning: Why this creates the best emotional impact"""

        return self.invoke_structured(prompt, AgentVote, max_tokens=500)


class PinchMasterAgent(BaseStoryAgent):
    """
    Embodies Larry Brooks / K.M. Weiland Pinch Point Theory.

    Core beliefs (from Story Engineering and Helping Writers Become Authors):
    - Pinch Point 1 at 37% (between Plot Turn 1 and Midpoint)
    - Pinch Point 2 at 62% (between Midpoint and Plot Turn 2)
    - Pinch Points = reminder of antagonistic force's power
    - PP1 foreshadows what hero will fully realize at Midpoint
    - PP2 shows antagonist is STILL formidable even after hero levels up
    - "Without well-placed Pinch Points, story loses rising action"

    Sources:
    - https://www.helpingwritersbecomeauthors.com/pinch-points/
    - https://writershelpingwriters.net/2021/10/what-are-pinch-points-and-where-do-they-go/
    """

    METHODOLOGY_NAME = "Pinch Point Theory"
    METHODOLOGY_SOURCE = "Larry Brooks' Story Engineering / K.M. Weiland"

    CORE_BELIEFS = [
        "Pinch Point 1 at 37% mark - first REAL taste of antagonist's power",
        "Pinch Point 2 at 62% mark - antagonist is STILL formidable after Midpoint",
        "Pinch Points are REMINDERS of what the hero is up against",
        "Without pinch points, tension PLATEAUS instead of escalating",
        "PP2 must be DARKER than PP1 - stakes always escalate",
    ]

    @property
    def name(self) -> str:
        return "PINCH_MASTER_AGENT"

    @property
    def role(self) -> str:
        return "Pinch Point Theory Advocate"

    @property
    def system_prompt(self) -> str:
        return """You are a story architect who embodies Larry Brooks / K.M. Weiland's Pinch Point Theory.

YOUR METHODOLOGY (Pinch Point Theory):
From Story Engineering and Helping Writers Become Authors.

CORE PRINCIPLES:
1. PINCH POINT PLACEMENT:
   - PP1 at 37% (between First Plot Point and Midpoint)
   - PP2 at 62% (between Midpoint and Second Plot Point)
   - These are EXACT positions for maximum tension

2. PINCH POINTS = ANTAGONIST POWER:
   - Show the antagonistic force's strength
   - Remind readers what hero is up against
   - The obstacle is REAL, not theoretical

3. PP1 FORESHADOWS:
   - First Pinch Point hints at what's really going on
   - Hero doesn't fully understand yet
   - Plants seeds for Midpoint revelation

4. PP2 SHOWS ESCALATION:
   - After Midpoint, hero is stronger/smarter
   - PP2 shows antagonist is STILL formidable
   - Must be DARKER than PP1
   - "Even now, you can still lose"

5. TENSION ESCALATION:
   - PP1 < Midpoint stakes < PP2 < Climax
   - Pressure ALWAYS increases
   - Never plateau - always escalate

WHEN CRITIQUING OTHER PROPOSALS:
- Do Pinch Points show ANTAGONIST POWER?
- Is PP2 demonstrably DARKER than PP1?
- Does tension escalate consistently?
- Are stakes raised at each beat?

Your critiques should focus on TENSION and ANTAGONIST PRESENCE."""

    def propose_pinch_point_1(
        self,
        story_seed_parsed: StorySeedParsed,
        hook: StructureBeatSchema,
        plot_turn_1: StructureBeatSchema,
        setting_prompt: str,
    ) -> AgentProposal:
        """Propose Pinch Point 1 based on Pinch Point Theory."""
        prompt = f"""As the Pinch Point Theory advocate, propose PINCH POINT 1.

LARRY BROOKS PRINCIPLE: "PP1 at 37% - first REAL taste of antagonist's power. Stakes become real."

STORY CONTEXT:
- Hero: {story_seed_parsed.hero_role}
- Goal: {story_seed_parsed.goal}
- Stakes: {story_seed_parsed.stakes}

HOOK: {hook.description}
PLOT TURN 1: {plot_turn_1.description}

SETTING: {setting_prompt}

YOUR TASK:
Design PINCH POINT 1 (37% mark).

Larry Brooks says:
- This is the first REAL confrontation with the antagonist/obstacle
- Before: stakes were theoretical. NOW: stakes are REAL
- Shows the antagonist's power to hurt/stop the hero
- Hero is forced to REACT (not act - that's Midpoint's job)
- Foreshadows what hero will fully understand at Midpoint

Create a Pinch Point 1 that:
1. Shows antagonist/obstacle's POWER directly
2. Makes stakes REAL, not theoretical
3. Forces hero to react/respond
4. Sets up what will be revealed at Midpoint
5. Uses ONLY generic roles (no names)

CRITICAL FORMAT: Description must be 1-2 sentences MAX (under 40 words). Focus on what HAPPENS, not atmosphere.

Output structured JSON for StructureBeatSchema with beat_name="pinch_point_1"."""

        beat = self.invoke_structured(prompt, StructureBeatSchema, max_tokens=1000)

        return AgentProposal(
            agent_name=self.name,
            methodology_source=self.METHODOLOGY_SOURCE,
            beat=beat,
            methodology_reasoning="Larry Brooks principle: 'Pinch Point 1 at 37% is the first REAL taste of antagonist power. Stakes become real, not theoretical. Hero is forced to react.'"
        )

    def propose_pinch_point_2(
        self,
        story_seed_parsed: StorySeedParsed,
        pinch_point_1: StructureBeatSchema,
        midpoint: StructureBeatSchema,
        setting_prompt: str,
    ) -> AgentProposal:
        """Propose Pinch Point 2 based on Pinch Point Theory."""
        prompt = f"""As the Pinch Point Theory advocate, propose PINCH POINT 2.

LARRY BROOKS PRINCIPLE: "PP2 at 62% - shows antagonist is STILL formidable even after hero levels up."

STORY CONTEXT:
- Hero: {story_seed_parsed.hero_role}
- Stakes: {story_seed_parsed.stakes}

PINCH POINT 1: {pinch_point_1.description}
MIDPOINT (hero is now proactive): {midpoint.description}

SETTING: {setting_prompt}

YOUR TASK:
Design PINCH POINT 2 (62% mark).

Larry Brooks says:
- After Midpoint, hero is stronger/smarter
- PP2 MUST show antagonist is STILL a formidable threat
- This is DARKER than Pinch Point 1
- "Even now that you're better, you can STILL lose"
- Maximum pressure before the final push

CRITICAL: PP2 must be MORE intense than PP1.
- PP1 showed: {pinch_point_1.emotional_state}
- PP2 must be WORSE

Create a Pinch Point 2 that:
1. Shows antagonist STILL has power (even after hero grew at Midpoint)
2. Is DARKER than Pinch Point 1
3. Raises stakes to near-maximum
4. Makes victory feel uncertain
5. Uses ONLY generic roles (no names)

CRITICAL FORMAT: Description must be 1-2 sentences MAX (under 40 words). Focus on what HAPPENS, not atmosphere.

Output structured JSON for StructureBeatSchema with beat_name="pinch_point_2"."""

        beat = self.invoke_structured(prompt, StructureBeatSchema, max_tokens=1000)

        return AgentProposal(
            agent_name=self.name,
            methodology_source=self.METHODOLOGY_SOURCE,
            beat=beat,
            methodology_reasoning="Larry Brooks principle: 'Pinch Point 2 at 62% shows antagonist is STILL formidable even after hero's Midpoint growth. PP2 must be DARKER than PP1 - stakes always escalate.'"
        )

    def critique_proposal(
        self,
        target_agent: str,
        target_beat: str,
        proposal: StructureBeatSchema,
        story_seed_parsed: StorySeedParsed,
        other_beats: dict = None,
    ) -> AgentCritique:
        """Critique another agent's proposal from Pinch Point Theory perspective."""
        other_beats = other_beats or {}
        pp1_context = ""
        if "pinch_point_1" in other_beats:
            pp1_context = f"\nPP1 for comparison: {other_beats['pinch_point_1'].emotional_state}"

        prompt = f"""As the Pinch Point Theory advocate, critique this {target_beat} proposal.

PINCH POINT PRINCIPLES TO CHECK:
1. Do Pinch Points show ANTAGONIST POWER?
2. Is PP2 DARKER than PP1?
3. Does tension ESCALATE consistently?
4. Are stakes raised, never plateaued?

TARGET: {target_beat} proposal from {target_agent}
{proposal.description}
Emotional state: {proposal.emotional_state}
{pp1_context}

STORY STAKES: {story_seed_parsed.stakes}

YOUR CRITIQUE (focus on TENSION and ESCALATION):
Does this maintain rising tension? Does antagonist feel threatening?

Output structured JSON with:
- critic_agent: "{self.name}"
- target_agent: "{target_agent}"
- target_beat: "{target_beat}"
- criticism: What's wrong with tension/escalation
- suggestion: How to increase pressure
- methodology_basis: The pinch point principle this is based on
- severity: "minor", "moderate", or "major\""""

        return self.invoke_structured(prompt, AgentCritique, max_tokens=800)

    def vote_for_best(
        self,
        target_beat: str,
        proposals: list[AgentProposal],
        story_seed_parsed: StorySeedParsed,
    ) -> AgentVote:
        """Vote for the best proposal based on Pinch Point Theory."""
        proposals_text = "\n\n".join([
            f"PROPOSAL {i+1} ({p.agent_name}):\n{p.beat.description}\nState: {p.beat.emotional_state}"
            for i, p in enumerate(proposals)
        ])

        prompt = f"""As the Pinch Point Theory advocate, vote for the best {target_beat} proposal.

PINCH POINT VOTING CRITERIA:
1. Shows antagonist POWER
2. Escalates tension properly
3. Makes stakes REAL
4. Maintains pressure curve

PROPOSALS:
{proposals_text}

Vote for the proposal that best maintains RISING TENSION.

Output structured JSON with:
- voter_agent: "{self.name}"
- voted_for_agent: (name of agent you vote for)
- vote_reasoning: Why this creates best tension escalation"""

        return self.invoke_structured(prompt, AgentVote, max_tokens=500)


class TruthSeekerAgent(BaseStoryAgent):
    """
    Embodies September C. Fawkes' Narrative Theory.

    Core beliefs (from Story Structure blog):
    - "Pinch points are about exposing the TRUTH"
    - Truth about protagonist, antagonist, and their situations
    - "Realizing truth often causes pain but transforms protagonist"
    - Protagonist fails to transform = tragic ending
    - Midpoint = new information that CHANGES THE CONTEXT
    - "Hero stops being a wanderer, becomes a warrior"

    Sources:
    - https://www.septembercfawkes.com/2019/04/story-structure-explained-pinch-points.html
    - https://www.septembercfawkes.com/2021/05/how-each-of-5-major-plot-points-turn.html
    """

    METHODOLOGY_NAME = "Narrative Theory - Truth Reveals"
    METHODOLOGY_SOURCE = "September C. Fawkes' Story Structure"

    CORE_BELIEFS = [
        "Pinch points are about exposing TRUTH - painful but necessary",
        "Each beat reveals truth about protagonist, antagonist, or situation",
        "Realizing truth causes PAIN but enables TRANSFORMATION",
        "Midpoint = new information that CHANGES THE CONTEXT completely",
        "Hero goes from WANDERER (reactive) to WARRIOR (proactive)",
        "Failure to accept truth = tragic ending",
    ]

    @property
    def name(self) -> str:
        return "TRUTH_SEEKER_AGENT"

    @property
    def role(self) -> str:
        return "Narrative Theory Advocate"

    @property
    def system_prompt(self) -> str:
        return """You are a story architect who embodies September C. Fawkes' Narrative Theory.

YOUR METHODOLOGY (Truth Reveals):
From September C. Fawkes' deep analysis of story structure.

CORE PRINCIPLES:
1. TRUTH AS DRIVER:
   - Each major beat exposes a TRUTH
   - Truth about the hero, antagonist, or situation
   - Characters resist truth before accepting it

2. PAINFUL TRUTH = TRANSFORMATION:
   - Realizing truth often HURTS
   - Pain is necessary for growth
   - Avoiding truth leads to tragedy

3. LIES AND TRUTH ARCS:
   - Hero starts believing a LIE about themselves/world
   - Story forces them to confront truth
   - Resolution = accepting truth fully

4. MIDPOINT = CONTEXT CHANGE:
   - New information that reframes EVERYTHING
   - What hero thought was true... isn't
   - This enables the shift from wanderer to warrior

5. WANDERER TO WARRIOR:
   - Before Midpoint: hero wanders, unsure
   - After Midpoint: hero becomes a warrior with clear purpose
   - Truth provides clarity and direction

6. TRAGIC VS. TRIUMPHANT:
   - Accept truth = triumphant ending
   - Reject truth = tragic ending
   - The choice belongs to the hero

WHEN CRITIQUING OTHER PROPOSALS:
- What TRUTH is being revealed?
- What LIE is being challenged?
- Does realization cause appropriate PAIN?
- Is transformation earned through truth?

Your critiques should focus on TRUTH, LIES, and TRANSFORMATION."""

    def propose_hook(
        self,
        story_seed_parsed: StorySeedParsed,
        resolution: StructureBeatSchema,
        setting_prompt: str,
    ) -> AgentProposal:
        """Propose the Hook beat based on Truth/Lie Narrative Theory."""
        prompt = f"""As the Truth Seeker narrative theory advocate, propose the HOOK beat.

SEPTEMBER C. FAWKES PRINCIPLE: "Hero starts believing a LIE about themselves or the world."

STORY SEED:
- Adjective: {story_seed_parsed.adjective}
- Why: {story_seed_parsed.adjective_meaning}
- Hero: {story_seed_parsed.hero_role}
- Goal: {story_seed_parsed.goal}

RESOLUTION (where they end): {resolution.description}

SETTING: {setting_prompt}

YOUR TASK:
Design the HOOK that establishes the hero's LIE.

September C. Fawkes says:
- Hero believes something FALSE about themselves or the world
- This LIE is connected to why they're {story_seed_parsed.adjective}
- The story will force them to confront the TRUTH
- By Resolution, they accept the truth and transform

For this story:
- The hero is {story_seed_parsed.adjective}
- What LIE do they believe that keeps them in this state?
- Examples: "I'm better off alone" / "Trust leads to pain" / "I'm not worthy"

Create a Hook that:
1. Shows the hero's {story_seed_parsed.adjective} state
2. Establishes the LIE they believe
3. Shows how the lie PROTECTS them (falsely)
4. Sets up the truth they'll eventually accept
5. Uses ONLY generic roles (no names)

CRITICAL FORMAT: Description must be 1-2 sentences MAX (under 40 words). Focus on what HAPPENS, not atmosphere.

Output structured JSON for StructureBeatSchema with beat_name="hook"."""

        beat = self.invoke_structured(prompt, StructureBeatSchema, max_tokens=1000)

        return AgentProposal(
            agent_name=self.name,
            methodology_source=self.METHODOLOGY_SOURCE,
            beat=beat,
            methodology_reasoning=f"Fawkes principle: 'Hero starts believing a LIE. Being {story_seed_parsed.adjective} is maintained by a false belief that the story will challenge. Truth acceptance = transformation.'"
        )

    def propose_midpoint(
        self,
        story_seed_parsed: StorySeedParsed,
        hook: StructureBeatSchema,
        resolution: StructureBeatSchema,
        setting_prompt: str,
    ) -> AgentProposal:
        """Propose the Midpoint beat based on Truth/Lie Narrative Theory."""
        prompt = f"""As the Truth Seeker narrative theory advocate, propose the MIDPOINT beat.

SEPTEMBER C. FAWKES PRINCIPLE: "Midpoint = new information that CHANGES THE CONTEXT. Hero becomes warrior."

STORY CONTEXT:
- Hero: {story_seed_parsed.hero_role}
- Original state: {story_seed_parsed.adjective}
- Goal: {story_seed_parsed.goal}

HOOK (the LIE state): {hook.description}
RESOLUTION (truth accepted): {resolution.description}

SETTING: {setting_prompt}

YOUR TASK:
Design the MIDPOINT as CONTEXT CHANGE.

September C. Fawkes says:
- Midpoint brings NEW INFORMATION
- This information REFRAMES everything
- What hero thought was true... isn't
- "Hero stops being a WANDERER, becomes a WARRIOR"

For this story:
- Before Midpoint: hero wanders, unsure, reactive
- Midpoint: learns something that changes EVERYTHING
- After Midpoint: hero has clarity, purpose, direction

Create a Midpoint that:
1. Reveals truth that CHANGES THE CONTEXT
2. Challenges the hero's existing beliefs/assumptions
3. Transforms hero from wanderer to warrior
4. Enables the path to Resolution
5. Uses ONLY generic roles (no names)

CRITICAL FORMAT: Description must be 1-2 sentences MAX (under 40 words). Focus on what HAPPENS, not atmosphere.

Output structured JSON for StructureBeatSchema with beat_name="midpoint"."""

        beat = self.invoke_structured(prompt, StructureBeatSchema, max_tokens=1000)

        return AgentProposal(
            agent_name=self.name,
            methodology_source=self.METHODOLOGY_SOURCE,
            beat=beat,
            methodology_reasoning="Fawkes principle: 'Midpoint is new information that CHANGES THE CONTEXT. Hero transforms from WANDERER (uncertain, reactive) to WARRIOR (purposeful, proactive).'"
        )

    def critique_proposal(
        self,
        target_agent: str,
        target_beat: str,
        proposal: StructureBeatSchema,
        story_seed_parsed: StorySeedParsed,
        other_beats: dict = None,
    ) -> AgentCritique:
        """Critique another agent's proposal from Truth/Lie narrative perspective."""
        prompt = f"""As the Truth Seeker narrative theory advocate, critique this {target_beat} proposal.

TRUTH/LIE PRINCIPLES TO CHECK:
1. What TRUTH or LIE is being addressed?
2. Is there appropriate PAIN with realization?
3. Does this move hero toward or away from truth?
4. Is transformation EARNED?

TARGET: {target_beat} proposal from {target_agent}
{proposal.description}
Emotional state: {proposal.emotional_state}

HERO'S JOURNEY: From {story_seed_parsed.adjective} to transformation

YOUR CRITIQUE (focus on TRUTH and TRANSFORMATION):
Is truth being confronted? Is change earned through painful realization?

Output structured JSON with:
- critic_agent: "{self.name}"
- target_agent: "{target_agent}"
- target_beat: "{target_beat}"
- criticism: What's missing in truth/transformation
- suggestion: How to deepen the truth journey
- methodology_basis: The narrative theory principle this is based on
- severity: "minor", "moderate", or "major\""""

        return self.invoke_structured(prompt, AgentCritique, max_tokens=800)

    def vote_for_best(
        self,
        target_beat: str,
        proposals: list[AgentProposal],
        story_seed_parsed: StorySeedParsed,
    ) -> AgentVote:
        """Vote for the best proposal based on Truth/Lie Narrative Theory."""
        proposals_text = "\n\n".join([
            f"PROPOSAL {i+1} ({p.agent_name}):\n{p.beat.description}\nState: {p.beat.emotional_state}"
            for i, p in enumerate(proposals)
        ])

        prompt = f"""As the Truth Seeker narrative theory advocate, vote for the best {target_beat} proposal.

TRUTH/LIE VOTING CRITERIA:
1. Engages with truth/lie arc
2. Shows appropriate pain/realization
3. Moves toward earned transformation
4. Deepens character understanding

PROPOSALS:
{proposals_text}

Vote for the proposal that best serves the TRUTH/TRANSFORMATION journey.

Output structured JSON with:
- voter_agent: "{self.name}"
- voted_for_agent: (name of agent you vote for)
- vote_reasoning: Why this best serves truth and transformation"""

        return self.invoke_structured(prompt, AgentVote, max_tokens=500)


class AudienceAdvocateAgent(BaseStoryAgent):
    """
    Embodies the Reader/Viewer Perspective.

    Core beliefs (from audience engagement research):
    - Reader must CARE about the hero before conflict begins
    - Emotional payoff must match emotional investment
    - Universal themes resonate across cultures
    - Satisfying endings feel EARNED, not forced
    - Pacing must maintain engagement throughout
    - Catharsis comes through genuine character growth

    Focus:
    - What would a reader/viewer WANT to see?
    - Is the emotional journey satisfying?
    - Will this resonate with a broad audience?
    """

    METHODOLOGY_NAME = "Audience Perspective"
    METHODOLOGY_SOURCE = "Reader/viewer empathy and satisfaction research"

    CORE_BELIEFS = [
        "Reader must CARE about the hero before conflict begins",
        "Emotional payoff must match the reader's emotional investment",
        "Satisfying endings feel EARNED, not forced or convenient",
        "Universal themes (love, loss, redemption) resonate across cultures",
        "Pacing must maintain engagement - don't lose the reader",
        "Catharsis comes through genuine character growth",
    ]

    @property
    def name(self) -> str:
        return "AUDIENCE_ADVOCATE_AGENT"

    @property
    def role(self) -> str:
        return "Reader/Viewer Perspective Advocate"

    @property
    def system_prompt(self) -> str:
        return """You are a story advocate who represents the READER/VIEWER perspective.

YOUR METHODOLOGY (Audience Engagement):
You represent what audiences actually want from stories.

CORE PRINCIPLES:
1. EARN THE READER'S CARE:
   - Before any conflict, reader must CARE about the hero
   - Show relatable humanity, vulnerability, or admirable qualities
   - If we don't care, stakes don't matter

2. EMOTIONAL INVESTMENT = PAYOFF:
   - The bigger the emotional journey, the bigger the satisfaction
   - Don't shortchange the emotional beats
   - Payoff must MATCH investment

3. SATISFYING ENDINGS ARE EARNED:
   - Endings feel hollow if not earned through struggle
   - Deus ex machina = reader betrayal
   - Victory must cost something

4. UNIVERSAL THEMES RESONATE:
   - Love, loss, redemption, belonging, identity
   - These themes cross cultures and demographics
   - Specific stories with universal hearts

5. MAINTAIN ENGAGEMENT:
   - Pacing matters - don't lose readers in the middle
   - Every beat should serve the emotional journey
   - Confusion = disengagement

6. CATHARSIS THROUGH GROWTH:
   - Readers want to see characters CHANGE
   - Growth should be visible and meaningful
   - The journey matters as much as the destination

WHEN CRITIQUING OTHER PROPOSALS:
- Will readers CARE about this?
- Does this feel SATISFYING or hollow?
- Is the emotional beat EARNED?
- Would a general audience connect with this?

Your critiques should focus on READER EXPERIENCE and EMOTIONAL SATISFACTION."""

    def propose_resolution(
        self,
        story_seed_parsed: StorySeedParsed,
        setting_prompt: str,
    ) -> AgentProposal:
        """Propose the Resolution beat based on audience satisfaction."""
        prompt = f"""As the Audience Advocate, propose the RESOLUTION beat.

AUDIENCE PRINCIPLE: "Satisfying endings feel EARNED - victory must cost something."

STORY SEED:
- Adjective: {story_seed_parsed.adjective}
- Why: {story_seed_parsed.adjective_meaning}
- Hero: {story_seed_parsed.hero_role}
- Goal: {story_seed_parsed.goal}
- Stakes: {story_seed_parsed.stakes}

SETTING: {setting_prompt}

YOUR TASK:
Design a RESOLUTION that will SATISFY readers.

Think like an audience member:
- After investing in this journey, what ending would feel EARNED?
- How should the hero's transformation SHOW (not tell)?
- What universal theme should resonate?
- What lasting emotional impact should remain?

For a hero who was {story_seed_parsed.adjective}:
- What transformation will feel meaningful?
- How can we show they've grown (through action, not exposition)?
- What will readers REMEMBER about this ending?

Create a Resolution that:
1. Feels EARNED through the hero's struggle
2. Shows transformation through ACTION
3. Resonates with universal themes
4. Leaves lasting emotional impact
5. Uses ONLY generic roles (no names)

CRITICAL FORMAT: Description must be 1-2 sentences MAX (under 40 words). Focus on what HAPPENS, not atmosphere.

Output structured JSON for StructureBeatSchema with beat_name="resolution"."""

        beat = self.invoke_structured(prompt, StructureBeatSchema, max_tokens=1000)

        return AgentProposal(
            agent_name=self.name,
            methodology_source=self.METHODOLOGY_SOURCE,
            beat=beat,
            methodology_reasoning="Audience principle: 'Satisfying endings feel EARNED. Readers invest emotionally in the journey - the payoff must match that investment. Victory should cost something.'"
        )

    def propose_hook(
        self,
        story_seed_parsed: StorySeedParsed,
        resolution: StructureBeatSchema,
        setting_prompt: str,
    ) -> AgentProposal:
        """Propose the Hook beat based on audience engagement."""
        prompt = f"""As the Audience Advocate, propose the HOOK beat.

AUDIENCE PRINCIPLE: "Reader must CARE about the hero before conflict begins."

STORY SEED:
- Adjective: {story_seed_parsed.adjective}
- Why: {story_seed_parsed.adjective_meaning}
- Hero: {story_seed_parsed.hero_role}

RESOLUTION: {resolution.description}

SETTING: {setting_prompt}

YOUR TASK:
Design a HOOK that makes readers CARE.

Think like a reader picking up this story:
- Why should I invest my time in this hero?
- What makes them RELATABLE or ADMIRABLE?
- Even if they're flawed ({story_seed_parsed.adjective}), why root for them?
- What universal experience do they represent?

Readers connect with:
- Vulnerability (shows humanity)
- Competence (admiration)
- Humor (likability)
- Kindness (empathy)
- Relatability (I've felt that way)

Create a Hook that:
1. Makes readers CARE before the plot kicks in
2. Shows the hero's humanity despite their {story_seed_parsed.adjective} state
3. Establishes why we should root for their transformation
4. Connects to universal human experiences
5. Uses ONLY generic roles (no names)

CRITICAL FORMAT: Description must be 1-2 sentences MAX (under 40 words). Focus on what HAPPENS, not atmosphere.

Output structured JSON for StructureBeatSchema with beat_name="hook"."""

        beat = self.invoke_structured(prompt, StructureBeatSchema, max_tokens=1000)

        return AgentProposal(
            agent_name=self.name,
            methodology_source=self.METHODOLOGY_SOURCE,
            beat=beat,
            methodology_reasoning=f"Audience principle: 'Reader must CARE before conflict begins. Even a {story_seed_parsed.adjective} hero needs relatable humanity - something that makes us root for their journey.'"
        )

    def propose_plot_turn(
        self,
        story_seed_parsed: StorySeedParsed,
        hook: StructureBeatSchema,
        midpoint: StructureBeatSchema,
        resolution: StructureBeatSchema,
        plot_turn_number: int,
        setting_prompt: str,
    ) -> AgentProposal:
        """Propose a Plot Turn beat based on audience engagement."""
        beat_name = f"plot_turn_{plot_turn_number}"

        if plot_turn_number == 1:
            prompt = f"""As the Audience Advocate, propose PLOT TURN 1.

AUDIENCE PRINCIPLE: "The story must HOOK us into caring about what happens next."

STORY CONTEXT:
- Hero: {story_seed_parsed.hero_role}
- Starting state: {story_seed_parsed.adjective}
- Goal: {story_seed_parsed.goal}
- Stakes: {story_seed_parsed.stakes}

HOOK: {hook.description}

SETTING: {setting_prompt}

YOUR TASK:
Design PLOT TURN 1 that compels readers to keep reading.

Think like a reader deciding whether to continue:
- What event would make me NEED to know what happens next?
- How does this disrupt the hero's world in a compelling way?
- Why can't I put this book down now?

Create a Plot Turn 1 that:
1. Creates URGENCY - reader needs to know what's next
2. Disrupts the status quo in a meaningful way
3. Raises questions readers want answered
4. Connects personally to the hero (not just external events)
5. Uses ONLY generic roles (no names)

CRITICAL FORMAT: Description must be 1-2 sentences MAX (under 40 words). Focus on what HAPPENS, not atmosphere.

Output structured JSON for StructureBeatSchema with beat_name="{beat_name}"."""
        else:
            prompt = f"""As the Audience Advocate, propose PLOT TURN 2.

AUDIENCE PRINCIPLE: "Give readers hope before the final push - they need to believe victory is possible."

STORY CONTEXT:
- Hero: {story_seed_parsed.hero_role}
- Goal: {story_seed_parsed.goal}

MIDPOINT: {midpoint.description}
RESOLUTION: {resolution.description}

SETTING: {setting_prompt}

YOUR TASK:
Design PLOT TURN 2 that gives readers HOPE.

Think like a reader at this point in the story:
- After the darkness, I need to believe victory is possible
- What discovery/tool/alliance makes victory conceivable?
- How does this energize me for the final act?

Create a Plot Turn 2 that:
1. Gives readers HOPE after the darkest moment
2. Provides the hero with what they need (but they must still EARN victory)
3. Creates anticipation for the climax
4. Feels earned, not convenient
5. Uses ONLY generic roles (no names)

CRITICAL FORMAT: Description must be 1-2 sentences MAX (under 40 words). Focus on what HAPPENS, not atmosphere.

Output structured JSON for StructureBeatSchema with beat_name="{beat_name}"."""

        beat = self.invoke_structured(prompt, StructureBeatSchema, max_tokens=1000)

        return AgentProposal(
            agent_name=self.name,
            methodology_source=self.METHODOLOGY_SOURCE,
            beat=beat,
            methodology_reasoning=f"Audience principle: 'Plot turns must maintain reader engagement. PT1 hooks us in, PT2 gives hope before the climax.'"
        )

    def critique_proposal(
        self,
        target_agent: str,
        target_beat: str,
        proposal: StructureBeatSchema,
        story_seed_parsed: StorySeedParsed,
        other_beats: dict = None,
    ) -> AgentCritique:
        """Critique another agent's proposal from audience perspective."""
        prompt = f"""As the Audience Advocate, critique this {target_beat} proposal.

AUDIENCE PRINCIPLES TO CHECK:
1. Will readers CARE about this?
2. Does this feel SATISFYING or hollow?
3. Is the emotional beat EARNED?
4. Would a general audience connect with this?
5. Does this maintain engagement?

TARGET: {target_beat} proposal from {target_agent}
{proposal.description}
Emotional state: {proposal.emotional_state}

STORY CONTEXT:
- Hero: {story_seed_parsed.hero_role}
- Starting state: {story_seed_parsed.adjective}
- Stakes: {story_seed_parsed.stakes}

YOUR CRITIQUE (focus on READER EXPERIENCE):
Would readers find this satisfying? Would they care? Would they stay engaged?

Output structured JSON with:
- critic_agent: "{self.name}"
- target_agent: "{target_agent}"
- target_beat: "{target_beat}"
- criticism: What's missing for reader satisfaction
- suggestion: How to improve reader engagement
- methodology_basis: The audience principle this is based on
- severity: "minor", "moderate", or "major\""""

        return self.invoke_structured(prompt, AgentCritique, max_tokens=800)

    def vote_for_best(
        self,
        target_beat: str,
        proposals: list[AgentProposal],
        story_seed_parsed: StorySeedParsed,
    ) -> AgentVote:
        """Vote for the best proposal based on audience satisfaction."""
        proposals_text = "\n\n".join([
            f"PROPOSAL {i+1} ({p.agent_name}):\n{p.beat.description}\nState: {p.beat.emotional_state}"
            for i, p in enumerate(proposals)
        ])

        prompt = f"""As the Audience Advocate, vote for the best {target_beat} proposal.

AUDIENCE VOTING CRITERIA:
1. Will readers CARE about this?
2. Does this feel EARNED, not forced?
3. Is there emotional resonance?
4. Would this keep readers engaged?

PROPOSALS:
{proposals_text}

Vote for the proposal that will create the best READER EXPERIENCE.

Output structured JSON with:
- voter_agent: "{self.name}"
- voted_for_agent: (name of agent you vote for)
- vote_reasoning: Why this creates the best reader experience"""

        return self.invoke_structured(prompt, AgentVote, max_tokens=500)


# =============================================================================
# Legacy Agents (Kept for Backward Compatibility)
# =============================================================================

class ResolutionArchitectAgent(DanWellsAgent):
    """
    Legacy alias for DanWellsAgent.

    The Resolution Architect role is now handled by DanWellsAgent,
    which proposes Resolution first per Dan Wells methodology.
    """

    @property
    def name(self) -> str:
        return "RESOLUTION_ARCHITECT"

    def design_resolution(
        self,
        story_seed_parsed: StorySeedParsed,
        setting_prompt: str,
    ) -> StructureBeatSchema:
        """Design the Resolution beat (legacy method)."""
        proposal = self.propose_resolution(story_seed_parsed, setting_prompt)
        return proposal.beat


class HookDesignerAgent(BlakeSnyderAgent):
    """
    Legacy alias for BlakeSnyderAgent.

    Hook design now incorporates Blake Snyder's "Save the Cat" empathy moment.
    """

    @property
    def name(self) -> str:
        return "HOOK_DESIGNER"

    def design_hook(
        self,
        story_seed_parsed: StorySeedParsed,
        resolution: StructureBeatSchema,
        setting_prompt: str,
    ) -> StructureBeatSchema:
        """Design the Hook beat (legacy method)."""
        proposal = self.propose_hook(story_seed_parsed, resolution, setting_prompt)
        return proposal.beat


class TensionBuilderAgent(PinchMasterAgent):
    """
    Legacy alias for PinchMasterAgent.

    Middle beats are now handled with proper pinch point theory.
    """

    @property
    def name(self) -> str:
        return "TENSION_BUILDER"

    def design_midpoint(
        self,
        story_seed_parsed: StorySeedParsed,
        hook: StructureBeatSchema,
        resolution: StructureBeatSchema,
        setting_prompt: str,
    ) -> StructureBeatSchema:
        """Design the Midpoint beat (uses DanWellsAgent internally)."""
        dan_wells = DanWellsAgent(model=self.model_name, temperature=self.temperature)
        proposal = dan_wells.propose_midpoint(story_seed_parsed, hook, resolution, setting_prompt)
        return proposal.beat

    def design_plot_turns(
        self,
        story_seed_parsed: StorySeedParsed,
        hook: StructureBeatSchema,
        midpoint: StructureBeatSchema,
        resolution: StructureBeatSchema,
        setting_prompt: str,
    ) -> tuple[StructureBeatSchema, StructureBeatSchema]:
        """Design Plot Turn 1 and Plot Turn 2 (legacy method)."""
        # Plot Turn 1
        pt1_prompt = f"""Design PLOT TURN 1 (the inciting incident).

STORY: {story_seed_parsed.hero_role} who is {story_seed_parsed.adjective}
GOAL: {story_seed_parsed.goal}
STAKES: {story_seed_parsed.stakes}

HOOK: {hook.description}
MIDPOINT: {midpoint.description}

SETTING: {setting_prompt}

PLOT TURN 1 forces the hero out of their Hook state into the story.

CRITICAL FORMAT: Description must be 1-2 sentences MAX (under 40 words). Focus on what HAPPENS, not atmosphere.

Output structured JSON for StructureBeatSchema with beat_name="plot_turn_1"."""

        plot_turn_1 = self.invoke_structured(pt1_prompt, StructureBeatSchema, max_tokens=1000)

        # Plot Turn 2
        pt2_prompt = f"""Design PLOT TURN 2 (the final piece).

STORY: {story_seed_parsed.hero_role}
GOAL: {story_seed_parsed.goal}

MIDPOINT: {midpoint.description}
RESOLUTION: {resolution.description}

SETTING: {setting_prompt}

PLOT TURN 2 is the discovery/tool/insight that enables victory.

CRITICAL FORMAT: Description must be 1-2 sentences MAX (under 40 words). Focus on what HAPPENS, not atmosphere.

Output structured JSON for StructureBeatSchema with beat_name="plot_turn_2"."""

        plot_turn_2 = self.invoke_structured(pt2_prompt, StructureBeatSchema, max_tokens=1000)

        return plot_turn_1, plot_turn_2

    def design_pinch_points(
        self,
        story_seed_parsed: StorySeedParsed,
        hook: StructureBeatSchema,
        plot_turn_1: StructureBeatSchema,
        midpoint: StructureBeatSchema,
        plot_turn_2: StructureBeatSchema,
        resolution: StructureBeatSchema,
        setting_prompt: str,
    ) -> tuple[StructureBeatSchema, StructureBeatSchema]:
        """Design Pinch Point 1 and Pinch Point 2 (legacy method)."""
        pp1_proposal = self.propose_pinch_point_1(story_seed_parsed, hook, plot_turn_1, setting_prompt)
        pp2_proposal = self.propose_pinch_point_2(story_seed_parsed, pp1_proposal.beat, midpoint, setting_prompt)
        return pp1_proposal.beat, pp2_proposal.beat


class StructureValidatorAgent(BaseStoryAgent):
    """
    Validates and critiques the complete 7-point structure.

    Integrates validation criteria from all four methodologies:
    - Dan Wells: Hook/Resolution opposites
    - Blake Snyder: Emotional beats, "all is lost"
    - Pinch Point Theory: Tension escalation
    - Truth Seeker: Transformation arc
    """

    @property
    def name(self) -> str:
        return "STRUCTURE_VALIDATOR"

    @property
    def role(self) -> str:
        return "Multi-Methodology Structure Validator"

    @property
    def system_prompt(self) -> str:
        return """You are a story structure expert who validates 7-point structures using multiple methodologies.

VALIDATION METHODOLOGIES:

1. DAN WELLS CHECK:
   - Hook and Resolution are TRUE OPPOSITES
   - Midpoint is clear REACTION → ACTION pivot
   - All beats serve the Resolution

2. BLAKE SNYDER CHECK:
   - "Save the cat" empathy moment in Hook
   - False victory/defeat at Midpoint
   - "Whiff of death" at Pinch Point 2
   - Resolution CHANGES THE WORLD

3. PINCH POINT THEORY CHECK:
   - PP1 < PP2 in intensity (escalation)
   - Both show antagonist power
   - Tension never plateaus

4. TRUTH SEEKER CHECK:
   - Clear lie→truth arc
   - Transformation is EARNED
   - Pain leads to growth

5. UNIVERSAL CHECKS:
   - No character NAMES used (only roles)
   - Logical cause-and-effect between beats
   - Emotional arc is coherent

Output structured JSON matching StructureDebateCritique."""

    def validate_structure(
        self,
        story_seed_parsed: StorySeedParsed,
        structure: SevenPointStructureSchema,
    ) -> StructureDebateCritique:
        """Validate the complete 7-point structure using all methodologies."""
        prompt = f"""Validate this 7-point structure using ALL methodologies:

STORY SEED:
- Adjective: {story_seed_parsed.adjective}
- Hero: {story_seed_parsed.hero_role}
- Goal: {story_seed_parsed.goal}
- Stakes: {story_seed_parsed.stakes}

STRUCTURE:

HOOK:
{structure.hook.description}
State: {structure.hook.emotional_state}

PLOT TURN 1:
{structure.plot_turn_1.description}
State: {structure.plot_turn_1.emotional_state}

PINCH POINT 1:
{structure.pinch_point_1.description}
State: {structure.pinch_point_1.emotional_state}

MIDPOINT:
{structure.midpoint.description}
State: {structure.midpoint.emotional_state}

PINCH POINT 2:
{structure.pinch_point_2.description}
State: {structure.pinch_point_2.emotional_state}

PLOT TURN 2:
{structure.plot_turn_2.description}
State: {structure.plot_turn_2.emotional_state}

RESOLUTION:
{structure.resolution.description}
State: {structure.resolution.emotional_state}

VALIDATE AGAINST ALL METHODOLOGIES:

DAN WELLS:
1. Are Hook ({structure.hook.emotional_state}) and Resolution ({structure.resolution.emotional_state}) true OPPOSITES?
2. Is Midpoint a clear REACTION → ACTION pivot?
3. Do all beats serve the Resolution?

BLAKE SNYDER:
4. Is there empathy established in Hook?
5. Is Midpoint a false victory/defeat?
6. Is PP2 the "all is lost" moment?
7. Does Resolution CHANGE THE WORLD?

PINCH POINT THEORY:
8. Does PP1 show antagonist power?
9. Is PP2 DARKER than PP1?
10. Does tension escalate consistently?

TRUTH SEEKER:
11. What lie does hero start with?
12. What truth do they accept?
13. Is transformation earned?

UNIVERSAL:
14. Are there any character NAMES? (there shouldn't be)
15. Is cause-and-effect clear?

Output structured JSON with comprehensive validation."""

        return self.invoke_structured(prompt, StructureDebateCritique, max_tokens=1500)
