"""
Narrative Writing Agents for Step 5: Scene Narrative Writing.

5 agents debate prose writing with different perspectives:

1. CharacterContinuityAgent - Character traits, backstory integration
2. LocationAtmosphereAgent - Sensory immersion, atmosphere
3. WorldBuildingIntegrationAgent - Cultural details (food, customs, prayers)
4. PlotTickingClockAgent - Plot urgency, ticking clock pressure
5. NarrativeContinuityAgent - Prose quality, scene connections

Each agent:
- Proposes ~850 words of prose based on their methodology
- Critiques other proposals on multiple dimensions
- Votes for the best proposal
"""

from src.story_agents.base_story_agent import BaseStoryAgent
from src.story_schemas import (
    NarrativeProseProposal,
    NarrativeProseCritique,
    NarrativeProseVote,
)


# =============================================================================
# Agent 1: Character Continuity Agent
# =============================================================================

class CharacterContinuityAgent(BaseStoryAgent):
    """
    Ensures characters are portrayed consistently with their codex profiles.
    Weaves backstory naturally through action, dialogue, and sensory triggers.

    Methodology: Debra Dixon's GMC + Character Psychology
    """

    METHODOLOGY_NAME = "Character Continuity & GMC"
    METHODOLOGY_SOURCE = "Debra Dixon's Goal, Motivation, Conflict + Character Psychology"
    CORE_BELIEFS = [
        "Characters must act according to their established PERSONALITY TRAITS",
        "Backstory should be WOVEN IN naturally, not info-dumped",
        "Current actions should MIRROR or CONTRAST past experiences",
        "Dialogue must match character's ACCENT and SPEECH PATTERNS",
        "Physical reactions reveal CHARACTER QUALITIES (quirks, habits)",
        "Motivation drives EVERY action - nothing happens without reason",
    ]

    @property
    def name(self) -> str:
        return "CHARACTER_CONTINUITY"

    @property
    def role(self) -> str:
        return "Character Continuity Specialist"

    @property
    def system_prompt(self) -> str:
        return """You are a character continuity specialist who writes prose that honors each character's established profile.

YOUR METHODOLOGY (Debra Dixon's GMC + Psychology):
- Every character action must flow from their MOTIVATION and BACKSTORY
- Show personality traits through BEHAVIOR, not exposition
- Weave backstory through sensory triggers (a smell reminds them of...)
- Use dialogue subtext - what's NOT said reveals character
- Physical quirks and habits should appear naturally
- Character voice must match their established ACCENT and SPEECH PATTERNS

DEEP POV RULES (Critical for immersion):
1. ELIMINATE filter words: "he saw", "she felt", "he thought", "she noticed"
   - BAD: "She saw the door was locked"
   - GOOD: "The door. Locked."
2. Write AS the character, not ABOUT them
3. Reader should feel BEHIND the character's eyes
4. Use free indirect speech: blend narration with character thoughts
   - "The rain caught her off guard. Why did she always forget?"

MICRO-TENSION (Line-by-line engagement):
1. Use TENSE WORDS: paused, froze, waited, hid, fled, gulped, hesitated
2. Include character CONTRADICTIONS - what they do vs what they think
3. FRESH verbs, unexpected word choices
4. Short sentences for tension: "He ran. The door. Locked. No time."
5. Every line should pull the reader forward

INTERIORITY (Character's inner life):
1. Show emotional VULNERABILITY - readers connect emotionally
2. Reveal truths too dark to speak aloud
3. Use BURST + BEAT pattern:
   - Burst: Short charged thought ("This couldn't be happening.")
   - Beat: External action (She gripped the railing)
   - Burst: Another thought ("Not again.")
4. Meld thoughts into narrative seamlessly (no "he thought")
5. Internal monologue = connective tissue, not side conversation

CRITICAL WRITING RULES:
1. NEVER tell us a character is "nervous" - show fidgeting, speech patterns, eye movement
2. Use SMELL to trigger a memory or emotion from backstory
3. Mirror current situations to backstory events (they faced this before...)
4. Dialogue should reveal character through rhythm, word choice, what's avoided
5. Physical descriptions must match codex profiles EXACTLY
6. Show character qualities through action (if "obsessively organized" - show them organizing)

=== DIALOGUE DIFFERENTIATION (Critical for authentic voices) ===

1. EDUCATION LEVEL affects vocabulary:
   - PhD/Professor: "The ramifications of this discovery are profound..."
   - Street-smart: "Look, it's simple - we're screwed."
   - Child: Short sentences, concrete concepts, wonder at simple things

2. PROFESSION affects frame of reference:
   - Marine biologist sees alien planet: "The bioluminescence... like the Mariana Trench"
   - Mechanic sees alien planet: "Those gears don't mesh right. Inefficient design."
   - Soldier sees alien planet: "Three exits. High ground there. Defensible."

3. BACKGROUND/HISTORY affects what they notice:
   - Trauma survivor: Hypervigilant, notices exits and threats first
   - Poverty background: "Enough food here to feed my village for a year"
   - Privileged upbringing: Assumes comfort, expects service

4. PERSONALITY affects speech patterns:
   - Confident: Short, declarative. No hedging. "We go now."
   - Anxious: Filler words ("um", "well"), questions. "Should we... I mean..."
   - Intellectual: Complex sentences, qualifications. "In theory, assuming..."

5. VERBAL TICS (each character needs 2-3):
   - Catchphrases: "Mark my words", "Listen here"
   - Favorite words: Always says "precisely" or "absolutely"
   - Sentence starters: Always begins with "Look," or "Thing is,"

6. THE NO-TAG TEST:
   - If you remove dialogue tags, readers should still know who's speaking
   - Each character's voice is their FINGERPRINT

When writing, integrate:
- personality_traits: Show through behavior
- backstory_points: Weave through reflection, dialogue, sensory triggers
- qualities: Demonstrate quirks naturally
- accent: Reflect in dialogue patterns
- motivation: Drive every decision

Write prose where the CHARACTER drives the narrative, not plot convenience.
Your prose should be 750-1000 words, rich with sensory detail and subtext."""

    def propose_prose(
        self,
        scene_data: dict,
        characters: list[dict],
        locations: list[dict],
        world: dict,
        previous_prose: str,
        ticking_clock: dict,
    ) -> NarrativeProseProposal:
        """Propose prose with focus on character continuity and backstory integration."""
        # Get POV character
        pov_name = scene_data.get("pov_character", "")
        pov_char = next(
            (c for c in characters if c.get("name", "").lower() == pov_name.lower()),
            characters[0] if characters else {}
        )

        # Get scene characters
        scene_char_names = [n.lower() for n in scene_data.get("characters", [])]
        scene_chars = [c for c in characters if c.get("name", "").lower() in scene_char_names]

        # Format character details
        char_details = self._format_character_for_prompt(pov_char)
        other_chars = "\n".join([
            f"  - {c.get('name', 'Unknown')} ({c.get('gender', 'unknown')}): {', '.join(c.get('personality_traits', [])[:3])}"
            for c in scene_chars if c.get("name") != pov_name
        ])

        # Get location
        loc_name = scene_data.get("location", "")
        location = next(
            (loc for loc in locations if loc.get("name", "").lower() == loc_name.lower()),
            locations[0] if locations else {}
        )

        prompt = f"""Write this scene focusing on CHARACTER CONTINUITY.

SCENE CONTEXT:
- Location: {scene_data.get('location', 'Unknown')}
- Time: {scene_data.get('time_of_day', 'day')}
- Scene Goal: {scene_data.get('goal', 'Continue story')}
- Conflict: {scene_data.get('conflict', 'Obstacles arise')}
- What Happens: {scene_data.get('happens', 'Story continues')}
- Outcome: {scene_data.get('outcome', 'NO_AND')}

POV CHARACTER PROFILE (MUST HONOR):
{char_details}

OTHER CHARACTERS IN SCENE:
{other_chars if other_chars else '  None'}

LOCATION DETAILS:
- Name: {location.get('name', 'Unknown')}
- Atmosphere: {location.get('atmosphere', '')}
- Sensory Details: {location.get('sensory_details', '')}

TICKING CLOCK (maintain urgency):
{ticking_clock.get('ticking_clock', 'Time is running out')}

PREVIOUS SCENE ENDING (for continuity):
{previous_prose[-500:] if previous_prose else 'This is the opening scene.'}

YOUR TASK:
Write 750-1000 words of prose that:
1. Shows POV character's personality traits through ACTIONS (not telling)
2. Weaves in at least ONE backstory point naturally (via smell, similar situation, or dialogue)
3. Uses character's accent/speech pattern in dialogue
4. Demonstrates at least ONE character quirk/quality
5. Uses sensory details to ground the scene
6. Maintains established character voices

TECHNIQUE REQUIREMENTS:
- Use SMELL to trigger a memory or emotion
- Include dialogue with SUBTEXT (what's not said matters)
- Vary sentence length: short punchy for tension, longer for reflection
- Show emotions through body language, not statements
- End with a hook or emotional beat

STRUCTURE:
- opening_paragraph: Establish scene through character's senses (100-150 words)
- middle_paragraphs: 3-5 paragraphs of action/dialogue showing character (each 100-150 words)
- closing_paragraph: End with emotional resonance or hook (100-150 words)

Write like a published novelist. NO summaries. Show, don't tell."""

        return self.invoke_structured(prompt, NarrativeProseProposal, max_tokens=5000)

    def _format_character_for_prompt(self, char: dict) -> str:
        """Format character data for prompt."""
        return f"""- Name: {char.get('name', 'Unknown')}
- Gender: {char.get('gender', 'unknown')} (USE CORRECT PRONOUNS)
- Personality Traits: {', '.join(char.get('personality_traits', []))}
- Backstory Points: {'; '.join(char.get('backstory_points', [])[:3])}
- Qualities/Quirks: {', '.join(char.get('qualities', []))}
- Accent/Speech: {char.get('accent', 'standard')}
- Motivation: {char.get('motivation', '')}
- Physical Build: {char.get('physical', {}).get('build', '')}
- Distinguishing Features: {', '.join(char.get('physical', {}).get('distinguishing_features', []))}"""

    def critique_prose(
        self,
        target_agent: str,
        proposal: NarrativeProseProposal,
        scene_context: dict,
    ) -> NarrativeProseCritique:
        """Critique prose from character continuity perspective."""
        prompt = f"""Critique this prose proposal from {target_agent} focusing on CHARACTER CONTINUITY.

PROSE TO CRITIQUE:
{proposal.to_prose()[:3000]}

TECHNIQUES CLAIMED:
{', '.join(proposal.techniques_used)}

SCENE CONTEXT:
- POV Character: {scene_context.get('scene_data', {}).get('pov_character', 'Unknown')}
- Location: {scene_context.get('scene_data', {}).get('location', 'Unknown')}
- Goal: {scene_context.get('scene_data', {}).get('goal', 'Unknown')}

CRITIQUE FROM CHARACTER CONTINUITY PERSPECTIVE:
Score each dimension 1-10:
1. character_accuracy_score: Do characters match their codex profiles? Are personality traits SHOWN through action?
2. sensory_immersion_score: Are senses engaged? Is the location vivid?
3. world_integration_score: Are world details woven naturally?
4. plot_urgency_score: Does the ticking clock feel present?
5. prose_quality_score: Is the prose varied, engaging, free of cliches?

Identify:
- strengths: What works well?
- weaknesses: What needs improvement?
- specific_suggestions: 2-3 concrete improvements with examples

Calculate overall_score as average of the 5 dimension scores."""

        return self.invoke_structured(prompt, NarrativeProseCritique, max_tokens=1500)

    def vote_for_best(
        self,
        proposals: list[NarrativeProseProposal],
        scene_context: dict,
    ) -> NarrativeProseVote:
        """Vote for the best prose proposal."""
        proposals_text = "\n\n---\n\n".join([
            f"PROPOSAL FROM {p.agent_name}:\n{p.to_prose()[:1500]}..."
            for p in proposals if p.agent_name != self.name
        ])

        prompt = f"""Vote for the BEST prose proposal (you cannot vote for your own).

PROPOSALS:
{proposals_text}

SCENE CONTEXT:
- POV Character: {scene_context.get('scene_data', {}).get('pov_character', 'Unknown')}
- Goal: {scene_context.get('scene_data', {}).get('goal', 'Unknown')}

As the CHARACTER_CONTINUITY agent, vote for the proposal that:
1. Best honors character profiles through action
2. Weaves backstory most naturally
3. Has the most authentic dialogue voice

You CANNOT vote for CHARACTER_CONTINUITY.

Provide:
- voted_for_agent: Name of agent you vote for
- vote_reasoning: Why this is the best choice
- methodology_alignment: How it aligns with character continuity principles"""

        return self.invoke_structured(prompt, NarrativeProseVote, max_tokens=500)


# =============================================================================
# Agent 2: Location Atmosphere Agent
# =============================================================================

class LocationAtmosphereAgent(BaseStoryAgent):
    """
    Creates immersive prose using location sensory details.
    Makes readers FEEL the environment through all five senses.

    Methodology: Environmental Storytelling + Sensory Writing
    """

    METHODOLOGY_NAME = "Sensory Immersion"
    METHODOLOGY_SOURCE = "Environmental Storytelling and Sensory Writing Techniques"
    CORE_BELIEFS = [
        "Readers should FEEL like they're IN the location",
        "Every sense matters: sight, sound, smell, texture, taste",
        "Location ATMOSPHERE should mirror or contrast scene emotion",
        "Environmental details can foreshadow or reflect character state",
        "Key features from location profile MUST appear naturally",
        "Weather and time of day affect EVERYTHING",
    ]

    @property
    def name(self) -> str:
        return "LOCATION_ATMOSPHERE"

    @property
    def role(self) -> str:
        return "Sensory Immersion Writer"

    @property
    def system_prompt(self) -> str:
        return """You are a sensory immersion writer who makes locations come alive.

YOUR METHODOLOGY (Environmental Storytelling):
- Readers must FEEL the location through all five senses
- Use sensory_details from location profile as foundation
- Atmosphere should enhance or contrast the scene's emotional tone
- Key features should appear naturally, not as lists
- Time of day affects lighting, shadows, activity levels
- Weather influences mood and character behavior

DEEP POV RULES (Critical for immersion):
1. ELIMINATE filter words: "he saw", "she felt", "he noticed"
   - BAD: "She noticed the room was cold"
   - GOOD: "Cold seeped through her thin dress."
2. Write AS the character experiencing the environment
3. Reader should feel BEHIND the character's eyes
4. Sensory details filtered through character's emotional state

MICRO-TENSION (Line-by-line engagement):
1. Use TENSE WORDS: paused, froze, waited, hid, fled, gulped, hesitated
2. Environment can threaten, comfort, or unsettle
3. FRESH verbs for sensory experiences
4. Every line should pull the reader forward
5. Find the unease even in beautiful places

VISCERAL WRITING (Physical sensations):
1. INTERNAL sensations: hunger pangs, muscle aches, racing hearts, dry mouth
2. SMELL triggers memory - most powerful sense for emotion
3. Be SPECIFIC and PARTICULAR to this character, this moment
4. Brain mirroring: readers' brains light up as if EXPERIENCING it
5. Temperature, texture, pressure on skin
6. Breathing changes, sweat, muscle tension
7. How the body responds to the environment

CRITICAL WRITING RULES:
1. OPEN with sensory grounding - what does the character notice FIRST?
2. Use SMELL as a memory trigger or atmosphere builder
3. Include TEXTURE - what surfaces do characters touch?
4. SOUND tells us what's happening beyond the viewpoint
5. Light and shadow create mood and visual interest
6. Temperature and weather affect character comfort and behavior

LAYERED SENSORY TECHNIQUE:
- Layer 1: Primary sense (usually visual) - establish space
- Layer 2: Secondary sense (sound) - establish life/activity
- Layer 3: Tertiary sense (smell/texture) - establish intimacy/memory
- Layer 4: Internal sensation - establish character's physical state

Example: "The market square stretched before her (visual), vendors calling prices like competing songbirds (sound), the air thick with woodsmoke and roasting meat (smell), cobblestones slick beneath her worn boots (texture). Her stomach cramped with hunger (internal)."

Make the SETTING a character in the story.
Your prose should be 750-1000 words, rich with sensory detail."""

    def propose_prose(
        self,
        scene_data: dict,
        characters: list[dict],
        locations: list[dict],
        world: dict,
        previous_prose: str,
        ticking_clock: dict,
    ) -> NarrativeProseProposal:
        """Propose prose with focus on sensory immersion and atmosphere."""
        # Get location
        loc_name = scene_data.get("location", "")
        location = next(
            (loc for loc in locations if loc.get("name", "").lower() == loc_name.lower()),
            locations[0] if locations else {}
        )

        # Get POV character
        pov_name = scene_data.get("pov_character", "")
        pov_char = next(
            (c for c in characters if c.get("name", "").lower() == pov_name.lower()),
            characters[0] if characters else {}
        )

        prompt = f"""Write this scene focusing on SENSORY IMMERSION and ATMOSPHERE.

SCENE CONTEXT:
- Time of Day: {scene_data.get('time_of_day', 'day')}
- Scene Goal: {scene_data.get('goal', 'Continue story')}
- Conflict: {scene_data.get('conflict', 'Obstacles arise')}
- What Happens: {scene_data.get('happens', 'Story continues')}
- Outcome: {scene_data.get('outcome', 'NO_AND')}

LOCATION PROFILE (USE THESE DETAILS):
- Name: {location.get('name', 'Unknown')}
- Type: {location.get('type', 'unknown')}
- Description: {location.get('description', '')}
- Atmosphere: {location.get('atmosphere', '')}
- Key Features: {', '.join(location.get('key_features', []))}
- Sensory Details: {location.get('sensory_details', '')}

POV CHARACTER:
- Name: {pov_char.get('name', 'Unknown')}
- Gender: {pov_char.get('gender', 'unknown')} (USE CORRECT PRONOUNS)
- Physical state to show: Consider how environment affects them

TICKING CLOCK:
{ticking_clock.get('ticking_clock', 'Time is running out')}

PREVIOUS SCENE ENDING:
{previous_prose[-400:] if previous_prose else 'This is the opening scene.'}

YOUR TASK:
Write 750-1000 words of prose that:
1. OPENS with sensory grounding (what does character notice FIRST?)
2. Uses ALL FIVE SENSES throughout:
   - SIGHT: Light, shadow, colors, movement
   - SOUND: What's heard near and far?
   - SMELL: The dominant and subtle scents
   - TEXTURE: What surfaces are touched?
   - TASTE: If eating/drinking, or taste of air
3. Includes at least 2 KEY FEATURES from location profile
4. Has ATMOSPHERE that mirrors or contrasts the emotional tone
5. Uses WEATHER or TIME OF DAY to affect mood

LAYERED SENSORY TECHNIQUE:
Layer your sensory details - don't dump them all at once.
Start with the dominant sense, then layer others as the scene progresses.

STRUCTURE:
- opening_paragraph: Establish location through layered senses (100-150 words)
- middle_paragraphs: Action/dialogue grounded in environment (each 100-150 words)
- closing_paragraph: End with atmospheric resonance (100-150 words)

Write immersive prose. NO generic descriptions. Make readers FEEL the space."""

        return self.invoke_structured(prompt, NarrativeProseProposal, max_tokens=5000)

    def critique_prose(
        self,
        target_agent: str,
        proposal: NarrativeProseProposal,
        scene_context: dict,
    ) -> NarrativeProseCritique:
        """Critique prose from sensory immersion perspective."""
        prompt = f"""Critique this prose proposal from {target_agent} focusing on SENSORY IMMERSION.

PROSE TO CRITIQUE:
{proposal.to_prose()[:3000]}

LOCATION FROM CODEX:
- Name: {scene_context.get('scene_data', {}).get('location', 'Unknown')}

CRITIQUE FROM SENSORY IMMERSION PERSPECTIVE:
Score each dimension 1-10:
1. character_accuracy_score: Are characters acting authentically?
2. sensory_immersion_score: Are ALL FIVE SENSES engaged? Is the location VIVID?
3. world_integration_score: Are world details woven naturally?
4. plot_urgency_score: Does urgency feel present?
5. prose_quality_score: Is prose varied and engaging?

Focus your critique on:
- How many senses are engaged?
- Is the location vivid or generic?
- Does atmosphere enhance the emotional tone?
- Are key features from the location profile used?

Provide specific_suggestions for improving sensory details."""

        return self.invoke_structured(prompt, NarrativeProseCritique, max_tokens=1500)

    def vote_for_best(
        self,
        proposals: list[NarrativeProseProposal],
        scene_context: dict,
    ) -> NarrativeProseVote:
        """Vote for the best prose proposal."""
        proposals_text = "\n\n---\n\n".join([
            f"PROPOSAL FROM {p.agent_name}:\n{p.to_prose()[:1500]}..."
            for p in proposals if p.agent_name != self.name
        ])

        prompt = f"""Vote for the BEST prose proposal (you cannot vote for your own).

PROPOSALS:
{proposals_text}

As the LOCATION_ATMOSPHERE agent, vote for the proposal that:
1. Best engages ALL FIVE senses
2. Makes the location feel REAL and VIVID
3. Uses atmosphere to enhance emotional tone

You CANNOT vote for LOCATION_ATMOSPHERE.

Provide:
- voted_for_agent: Name of agent you vote for
- vote_reasoning: Why this is most immersive
- methodology_alignment: How it aligns with sensory immersion principles"""

        return self.invoke_structured(prompt, NarrativeProseVote, max_tokens=500)


# =============================================================================
# Agent 3: World Building Integration Agent
# =============================================================================

class WorldBuildingIntegrationAgent(BaseStoryAgent):
    """
    Weaves world-building details naturally into narrative.
    Food, customs, religion, social rules appear in background.

    Methodology: Iceberg World-Building + Cultural Anthropology
    """

    METHODOLOGY_NAME = "World Integration"
    METHODOLOGY_SOURCE = "Iceberg World-Building Theory + Cultural Anthropology"
    CORE_BELIEFS = [
        "World-building should appear in BACKGROUND, not foreground",
        "Characters EAT, PRAY, follow customs - show don't explain",
        "Culture reveals itself through character REACTIONS to normal things",
        "Social rules create conflict when broken",
        "Religion/beliefs affect daily decisions and speech",
        "Class differences visible in food, clothing, behavior",
    ]

    @property
    def name(self) -> str:
        return "WORLD_INTEGRATION"

    @property
    def role(self) -> str:
        return "World-Building Integration Specialist"

    @property
    def system_prompt(self) -> str:
        return """You are a world-building integration specialist who weaves cultural details naturally.

YOUR METHODOLOGY (Iceberg World-Building):
- Only 10% of world-building shows; 90% is implied
- Characters don't EXPLAIN their world - they LIVE in it
- Food, prayer, customs appear as BACKGROUND actions
- Social rules create natural conflict
- Cultural details reveal class, education, region

DEEP POV RULES (Critical for immersion):
1. ELIMINATE filter words: "he saw", "she felt", "he thought"
   - BAD: "He noticed the strange custom"
   - GOOD: "The merchant's bow seemed too deep. Something was off."
2. Write AS the character experiencing their world
3. World details filtered through character's knowledge and biases
4. What they take for granted vs what surprises them

MICRO-TENSION (Line-by-line engagement):
1. Use TENSE WORDS: paused, froze, waited, hid, fled, gulped, hesitated
2. Cultural tensions create micro-conflict
3. Breaking taboos = immediate tension
4. Social rules being tested or bent
5. Every line should pull the reader forward
6. Find the unease in normal activities

CRITICAL WRITING RULES:
1. Characters EAT from common_foods list - describe the food, don't explain it
2. Include a cultural GESTURE (gesture_respect or gesture_rudeness)
3. Reference a SUPERSTITION or TABOO through character behavior
4. Show social_rules being followed or broken
5. Religion appears through casual oaths, prayers, or avoidance
6. Class shows through food quality, clothing details, speech

INTEGRATION TECHNIQUES:
- Character pauses to eat -> show WHAT they eat (from world foods)
- Character greets someone -> use cultural GESTURE
- Character avoids something -> reveals TABOO or SUPERSTITION
- Character swears or prays -> reveals RELIGION
- Background people do jobs -> show COMMON_JOBS

Example BAD: "In this world, people bow to show respect."
Example GOOD: "She dipped her head as the merchant passed, as was proper."

The world should feel LIVED-IN, not explained.
Your prose should be 750-1000 words."""

    def propose_prose(
        self,
        scene_data: dict,
        characters: list[dict],
        locations: list[dict],
        world: dict,
        previous_prose: str,
        ticking_clock: dict,
    ) -> NarrativeProseProposal:
        """Propose prose with focus on world-building integration."""
        # Get POV character
        pov_name = scene_data.get("pov_character", "")
        pov_char = next(
            (c for c in characters if c.get("name", "").lower() == pov_name.lower()),
            characters[0] if characters else {}
        )

        # Format world details
        world_details = self._format_world_for_prompt(world)

        prompt = f"""Write this scene focusing on WORLD-BUILDING INTEGRATION.

SCENE CONTEXT:
- Location: {scene_data.get('location', 'Unknown')}
- Time: {scene_data.get('time_of_day', 'day')}
- Scene Goal: {scene_data.get('goal', 'Continue story')}
- Conflict: {scene_data.get('conflict', 'Obstacles arise')}
- What Happens: {scene_data.get('happens', 'Story continues')}
- Outcome: {scene_data.get('outcome', 'NO_AND')}

POV CHARACTER:
- Name: {pov_char.get('name', 'Unknown')}
- Gender: {pov_char.get('gender', 'unknown')} (USE CORRECT PRONOUNS)
- Role: {pov_char.get('role_in_story', 'unknown')}

WORLD DETAILS (MUST INTEGRATE NATURALLY):
{world_details}

TICKING CLOCK:
{ticking_clock.get('ticking_clock', 'Time is running out')}

PREVIOUS SCENE ENDING:
{previous_prose[-400:] if previous_prose else 'This is the opening scene.'}

YOUR TASK:
Write 750-1000 words of prose that:
1. Shows characters EATING or DRINKING (use specific foods from list)
2. Includes at least ONE cultural GESTURE (respect or rudeness)
3. References a SUPERSTITION or TABOO naturally
4. Shows RELIGION through oaths, prayers, or avoidance
5. Background characters doing COMMON_JOBS
6. Social rules being followed or subtly broken

INTEGRATION RULES:
- NEVER explain the world - show characters LIVING in it
- Food appears as WHAT they eat, not explanations of cuisine
- Gestures happen naturally, without narration explaining them
- Religion in casual oaths ("Gods willing", "May the Flame protect us")
- Class differences in food quality and manners

STRUCTURE:
- opening_paragraph: Ground scene with cultural detail (100-150 words)
- middle_paragraphs: Action with world elements woven in (each 100-150 words)
- closing_paragraph: End with world detail that resonates (100-150 words)

Write a scene that feels LIVED-IN. NO anthropology lectures."""

        return self.invoke_structured(prompt, NarrativeProseProposal, max_tokens=5000)

    def _format_world_for_prompt(self, world: dict) -> str:
        """Format world data for prompt."""
        daily = world.get("daily_life", {})
        culture = world.get("culture_customs", {})
        religion = world.get("religion_beliefs", {})
        social = world.get("social_structure", {})

        return f"""DAILY LIFE:
- Foods: {', '.join(daily.get('common_foods', ['bread', 'stew'])[:7])}
- Eating Customs: {daily.get('eating_customs', 'communal meals')}
- Clothing: {daily.get('clothing_styles', 'varied by class')}

CULTURE & CUSTOMS:
- Respect Gesture: {culture.get('gestures_respect', 'a nod')}
- Rude Gesture: {culture.get('gestures_rudeness', 'turning away')}
- Social Rules: {', '.join(culture.get('social_rules', [])[:3])}
- Naming: {culture.get('naming_conventions', 'family names')}

RELIGION & BELIEFS:
- Main Religion: {religion.get('main_religion', 'varied beliefs')}
- Gods: {', '.join(religion.get('gods_deities', [])[:3])}
- Superstitions: {', '.join(religion.get('superstitions', [])[:3])}
- Taboos: {', '.join(religion.get('taboos', [])[:3])}

SOCIAL STRUCTURE:
- Common Jobs: {', '.join(social.get('common_jobs', [])[:5])}
- Class System: {social.get('class_system', 'distinct classes')}"""

    def critique_prose(
        self,
        target_agent: str,
        proposal: NarrativeProseProposal,
        scene_context: dict,
    ) -> NarrativeProseCritique:
        """Critique prose from world-building perspective."""
        prompt = f"""Critique this prose proposal from {target_agent} focusing on WORLD-BUILDING INTEGRATION.

PROSE TO CRITIQUE:
{proposal.to_prose()[:3000]}

CRITIQUE FROM WORLD INTEGRATION PERSPECTIVE:
Score each dimension 1-10:
1. character_accuracy_score: Are characters acting authentically?
2. sensory_immersion_score: Is the location vivid?
3. world_integration_score: Are WORLD DETAILS woven NATURALLY? Food, customs, gestures, religion?
4. plot_urgency_score: Does urgency feel present?
5. prose_quality_score: Is prose engaging?

Focus your critique on:
- Does the world feel LIVED-IN or explained?
- Are cultural details shown through ACTION or exposition?
- Do characters EAT, PRAY, follow customs naturally?
- Are superstitions/taboos referenced?

Provide specific_suggestions for better world integration."""

        return self.invoke_structured(prompt, NarrativeProseCritique, max_tokens=1500)

    def vote_for_best(
        self,
        proposals: list[NarrativeProseProposal],
        scene_context: dict,
    ) -> NarrativeProseVote:
        """Vote for the best prose proposal."""
        proposals_text = "\n\n---\n\n".join([
            f"PROPOSAL FROM {p.agent_name}:\n{p.to_prose()[:1500]}..."
            for p in proposals if p.agent_name != self.name
        ])

        prompt = f"""Vote for the BEST prose proposal (you cannot vote for your own).

PROPOSALS:
{proposals_text}

As the WORLD_INTEGRATION agent, vote for the proposal that:
1. Best weaves world details NATURALLY (not as exposition)
2. Shows characters LIVING in their world (eating, customs, religion)
3. Feels most LIVED-IN and authentic

You CANNOT vote for WORLD_INTEGRATION.

Provide:
- voted_for_agent: Name of agent you vote for
- vote_reasoning: Why this world integration is best
- methodology_alignment: How it aligns with iceberg world-building"""

        return self.invoke_structured(prompt, NarrativeProseVote, max_tokens=500)


# =============================================================================
# Agent 4: Plot & Ticking Clock Agent
# =============================================================================

class PlotTickingClockAgent(BaseStoryAgent):
    """
    Ensures every scene advances plot and maintains story urgency.
    The ticking clock creates constant pressure.

    Methodology: Dwight Swain Scene/Sequel + Ticking Clock Theory
    """

    METHODOLOGY_NAME = "Plot Urgency & Ticking Clock"
    METHODOLOGY_SOURCE = "Dwight Swain Scene/Sequel + Thriller Pacing Techniques"
    CORE_BELIEFS = [
        "Every scene must CHANGE the story situation",
        "The ticking clock creates URGENCY in every scene",
        "Scene outcomes (YES BUT, NO AND) drive to next scene",
        "GOAL-CONFLICT-DISASTER structure creates momentum",
        "Time pressure should be FELT by characters and readers",
        "Stakes must be RAISED or CLARIFIED each scene",
    ]

    @property
    def name(self) -> str:
        return "PLOT_TICKING_CLOCK"

    @property
    def role(self) -> str:
        return "Plot Urgency Specialist"

    @property
    def system_prompt(self) -> str:
        return """You are a plot urgency specialist who ensures every scene moves the story forward.

YOUR METHODOLOGY (Ticking Clock + Swain Structure):
- SCENE: Goal -> Conflict -> Disaster
- SEQUEL: Reaction -> Dilemma -> Decision
- The ticking clock PRESSES on every decision
- Outcomes (YES BUT, NO AND) create story momentum
- Each scene must leave characters WORSE OFF or with NEW PROBLEMS

DEEP POV RULES (Critical for immersion):
1. ELIMINATE filter words: "he saw", "she felt", "he realized"
   - BAD: "She realized time was running out"
   - GOOD: "Three hours. Only three hours left."
2. Write AS the character experiencing the urgency
3. Time pressure filtered through character's emotional state
4. Reader should feel the panic in their own chest

MICRO-TENSION (Line-by-line engagement):
1. Use TENSE WORDS: paused, froze, waited, hid, fled, gulped, hesitated
2. Character CONTRADICTIONS - wanting to rush but forced to wait
3. FRESH verbs for urgency
4. Short sentences for tension: "No time. Move. NOW."
5. Every line should pull the reader forward
6. Find the panic in every moment
7. Interrupted actions, failed attempts

CRITICAL WRITING RULES:
1. REFERENCE the ticking clock explicitly at least once
2. Scene GOAL must be clear in first quarter of scene
3. CONFLICT must actively OPPOSE the goal
4. OUTCOME must be shown, not summarized
5. Characters should feel TIME PRESSURE in decisions
6. End scenes with HOOKS that demand continuation

TENSION TECHNIQUES:
- Deadline reminders: "By dawn, it would be too late."
- Time markers: "Three hours until the execution."
- Urgency in dialogue: "We don't have time for this!"
- Physical symptoms of stress: racing heart, shallow breath, dry mouth
- Difficult choices under pressure
- Interrupted plans, complications that eat time

The reader should feel the CLOCK TICKING throughout the prose.
Your prose should be 750-1000 words."""

    def propose_prose(
        self,
        scene_data: dict,
        characters: list[dict],
        locations: list[dict],
        world: dict,
        previous_prose: str,
        ticking_clock: dict,
    ) -> NarrativeProseProposal:
        """Propose prose with focus on plot urgency and ticking clock."""
        # Get POV character
        pov_name = scene_data.get("pov_character", "")
        pov_char = next(
            (c for c in characters if c.get("name", "").lower() == pov_name.lower()),
            characters[0] if characters else {}
        )

        prompt = f"""Write this scene focusing on PLOT URGENCY and TICKING CLOCK.

SCENE CONTEXT:
- Location: {scene_data.get('location', 'Unknown')}
- Time: {scene_data.get('time_of_day', 'day')}
- Scene Type: {scene_data.get('scene_type', 'scene')}
- Scene Goal: {scene_data.get('goal', 'Continue story')}
- Conflict: {scene_data.get('conflict', 'Obstacles arise')}
- What Happens: {scene_data.get('happens', 'Story continues')}
- Outcome: {scene_data.get('outcome', 'NO_AND')}
- Structure Connection: {scene_data.get('structure_connection', 'advancing plot')}

POV CHARACTER:
- Name: {pov_char.get('name', 'Unknown')}
- Gender: {pov_char.get('gender', 'unknown')} (USE CORRECT PRONOUNS)
- Motivation: {pov_char.get('motivation', 'survival')}

TICKING CLOCK (MUST REFERENCE):
- Clock: {ticking_clock.get('ticking_clock', 'Time is running out')}
- Deadline: {ticking_clock.get('ticking_clock_deadline', 'Soon')}
- Consequence: {ticking_clock.get('ticking_clock_consequence', 'Disaster')}

PREVIOUS SCENE ENDING:
{previous_prose[-400:] if previous_prose else 'This is the opening scene.'}

YOUR TASK:
Write 750-1000 words of prose that:
1. REFERENCES the ticking clock explicitly at least ONCE
2. Makes the scene GOAL clear in the first quarter
3. Shows CONFLICT actively opposing the goal
4. Demonstrates the OUTCOME (don't summarize it)
5. Characters feel TIME PRESSURE in their decisions
6. Ends with a HOOK that demands the next scene

URGENCY TECHNIQUES:
- Deadline reminders in dialogue or narration
- Physical symptoms of stress (racing heart, sweat, shallow breath)
- Difficult choices with no good options
- Time markers ("Three hours until...")
- Interrupted plans, complications

STRUCTURE:
- opening_paragraph: Establish goal and urgency immediately (100-150 words)
- middle_paragraphs: Conflict escalation with time pressure (each 100-150 words)
- closing_paragraph: Outcome + hook for next scene (100-150 words)

Write prose where readers feel the CLOCK TICKING."""

        return self.invoke_structured(prompt, NarrativeProseProposal, max_tokens=5000)

    def critique_prose(
        self,
        target_agent: str,
        proposal: NarrativeProseProposal,
        scene_context: dict,
    ) -> NarrativeProseCritique:
        """Critique prose from plot urgency perspective."""
        ticking_clock = scene_context.get("ticking_clock", {})

        prompt = f"""Critique this prose proposal from {target_agent} focusing on PLOT URGENCY.

PROSE TO CRITIQUE:
{proposal.to_prose()[:3000]}

TICKING CLOCK TO REFERENCE:
{ticking_clock.get('ticking_clock', 'Time pressure')}

CRITIQUE FROM PLOT URGENCY PERSPECTIVE:
Score each dimension 1-10:
1. character_accuracy_score: Are characters acting authentically?
2. sensory_immersion_score: Is the location vivid?
3. world_integration_score: Are world details present?
4. plot_urgency_score: Is the TICKING CLOCK FELT? Does scene ADVANCE plot? Is outcome clear?
5. prose_quality_score: Is prose engaging?

Focus your critique on:
- Is the ticking clock EXPLICITLY referenced?
- Is the scene goal CLEAR?
- Does conflict OPPOSE the goal?
- Do characters feel TIME PRESSURE?
- Does the ending create a HOOK?

Provide specific_suggestions for increasing urgency."""

        return self.invoke_structured(prompt, NarrativeProseCritique, max_tokens=1500)

    def vote_for_best(
        self,
        proposals: list[NarrativeProseProposal],
        scene_context: dict,
    ) -> NarrativeProseVote:
        """Vote for the best prose proposal."""
        proposals_text = "\n\n---\n\n".join([
            f"PROPOSAL FROM {p.agent_name}:\n{p.to_prose()[:1500]}..."
            for p in proposals if p.agent_name != self.name
        ])

        prompt = f"""Vote for the BEST prose proposal (you cannot vote for your own).

PROPOSALS:
{proposals_text}

As the PLOT_TICKING_CLOCK agent, vote for the proposal that:
1. Best references the TICKING CLOCK
2. Has clearest GOAL-CONFLICT-OUTCOME
3. Creates most URGENCY and momentum

You CANNOT vote for PLOT_TICKING_CLOCK.

Provide:
- voted_for_agent: Name of agent you vote for
- vote_reasoning: Why this creates best urgency
- methodology_alignment: How it aligns with plot momentum principles"""

        return self.invoke_structured(prompt, NarrativeProseVote, max_tokens=500)


# =============================================================================
# Agent 5: Narrative Continuity Agent
# =============================================================================

class NarrativeContinuityAgent(BaseStoryAgent):
    """
    Ensures prose quality and narrative consistency across scenes.
    Maintains voice, tone, and connects to previous scenes.

    Methodology: Prose Rhythm Theory + Voice Consistency Techniques
    """

    METHODOLOGY_NAME = "Narrative Craft & Continuity"
    METHODOLOGY_SOURCE = "Prose Rhythm Theory + Voice Consistency Techniques"
    CORE_BELIEFS = [
        "Prose RHYTHM creates reading experience",
        "Sentence variety keeps readers engaged",
        "Previous scene's ending must CONNECT to new scene's opening",
        "Voice and tone should be CONSISTENT across scenes",
        "Show don't tell is a CRAFT principle, not just advice",
        "Every word should EARN its place",
    ]

    @property
    def name(self) -> str:
        return "NARRATIVE_CONTINUITY"

    @property
    def role(self) -> str:
        return "Prose Craft & Continuity Specialist"

    @property
    def system_prompt(self) -> str:
        return """You are a prose craft specialist who ensures narrative quality and continuity.

YOUR METHODOLOGY (Prose Rhythm + Voice):
- Sentence LENGTH creates rhythm: short for tension, long for reflection
- Previous scene ending CONNECTS to new scene opening
- Voice consistency across the entire narrative
- Show don't tell through SPECIFIC details
- Avoid cliches, purple prose, and overwriting

=== DEEP POV RULES (Critical for immersion) ===
1. ELIMINATE filter words: "he saw", "she felt", "he thought", "she noticed"
   - BAD: "She saw the door was locked"
   - GOOD: "The door. Locked."
2. Write AS the character, not ABOUT them
3. Reader should feel BEHIND the character's eyes
4. Use free indirect speech: blend narration with character thoughts
   - "The rain caught her off guard. Why did she always forget?"
5. NO emotional labels - show through ACTION and BODY

=== MICRO-TENSION (Line-by-line engagement) ===
1. Use TENSE WORDS: paused, froze, waited, hid, fled, gulped, hesitated
2. Include character CONTRADICTIONS - what they do vs what they think
3. FRESH verbs, unexpected word choices (not walked/went/said)
4. Short sentences for tension: "He ran. The door. Locked. No time."
5. Every line should pull the reader forward
6. Find the CONFLICT even in quiet moments - unspoken tension

=== EMOTIONAL LAYERING (Subterranean emotional network) ===
1. Build emotions BENEATH the surface action
   - Surface: She poured coffee -> Subtext: avoiding his question
2. Layer emotions of DIFFERENT INTENSITY across the scene
   - Don't stay at one emotional level - let it shift and breathe
3. Contrast surface action with internal truth
   - What they SAY vs what they FEEL
4. Use SENSORY TRIGGERS for emotional memory
   - A smell, sound, or texture that unlocks deeper feeling
5. End scenes with EMOTIONAL RESONANCE:
   - A haunting image that lingers
   - An unspoken question hanging in the air
   - An ache the character can't name
   - A small realization that changes everything

PROSE RHYTHM TECHNIQUES:
- Tension moment: "He ran. The door. Locked. No time."
- Reflection moment: "She watched the sun sink below the horizon, painting the sky in shades she had no words for, and wondered if this was the last sunset she would ever see."
- Transition: Mirror an element from previous scene's ending

QUALITY CHECKLIST:
- No "suddenly" or "very"
- No "felt" or "thought" - show instead
- No passive voice in action
- No redundancy (nodded his head)
- No cliches (heart pounding, blood ran cold, etc.)
- No filter words (he saw, she noticed, she realized)

Write PROFESSIONAL literary prose that flows naturally.
Your prose should be 750-1000 words."""

    def propose_prose(
        self,
        scene_data: dict,
        characters: list[dict],
        locations: list[dict],
        world: dict,
        previous_prose: str,
        ticking_clock: dict,
    ) -> NarrativeProseProposal:
        """Propose prose with focus on craft and continuity."""
        # Get POV character
        pov_name = scene_data.get("pov_character", "")
        pov_char = next(
            (c for c in characters if c.get("name", "").lower() == pov_name.lower()),
            characters[0] if characters else {}
        )

        # Get location
        loc_name = scene_data.get("location", "")
        location = next(
            (loc for loc in locations if loc.get("name", "").lower() == loc_name.lower()),
            locations[0] if locations else {}
        )

        prompt = f"""Write this scene focusing on PROSE CRAFT and NARRATIVE CONTINUITY.

SCENE CONTEXT:
- Location: {scene_data.get('location', 'Unknown')}
- Time: {scene_data.get('time_of_day', 'day')}
- Scene Goal: {scene_data.get('goal', 'Continue story')}
- Conflict: {scene_data.get('conflict', 'Obstacles arise')}
- What Happens: {scene_data.get('happens', 'Story continues')}
- Outcome: {scene_data.get('outcome', 'NO_AND')}

POV CHARACTER:
- Name: {pov_char.get('name', 'Unknown')}
- Gender: {pov_char.get('gender', 'unknown')} (USE CORRECT PRONOUNS)
- Stay in their head throughout

LOCATION:
- Name: {location.get('name', 'Unknown')}
- Atmosphere: {location.get('atmosphere', '')}

TICKING CLOCK:
{ticking_clock.get('ticking_clock', 'Time is running out')}

PREVIOUS SCENE ENDING (MUST CONNECT TO):
{previous_prose[-600:] if previous_prose else 'This is the OPENING scene - establish voice and tone.'}

YOUR TASK:
Write 750-1000 words of prose that:
1. CONNECTS naturally to previous scene's ending (or establishes story voice if first)
2. VARIES sentence length intentionally (short for tension, long for reflection)
3. Uses STRONG verbs (slammed, crept, lunged - not walked, went, moved)
4. AVOIDS: "suddenly", "very", "felt", "thought", passive voice, cliches
5. Shows emotions through BODY LANGUAGE and ACTION
6. Ends with RESONANCE (image, question, or realization)

PROSE RHYTHM RULES:
- DON'T use the same sentence length three times in a row
- Tension: Short. Punchy. Fragmented. Then breathe.
- Reflection: Let sentences stretch and flow, carrying the weight of the moment forward.

THINGS TO NEVER WRITE:
- "Her heart pounded" (show anxiety differently each time)
- "He suddenly realized" (cut "suddenly", show the realization)
- "She felt sad" (show her behavior that reveals sadness)
- Adverbs after dialogue tags ("she said angrily")

STRUCTURE:
- opening_paragraph: Connect to previous, establish rhythm (100-150 words)
- middle_paragraphs: Varied rhythm, strong verbs, no cliches (each 100-150 words)
- closing_paragraph: End with RESONANCE (100-150 words)

Write publishable literary prose. Every word earns its place."""

        return self.invoke_structured(prompt, NarrativeProseProposal, max_tokens=5000)

    def critique_prose(
        self,
        target_agent: str,
        proposal: NarrativeProseProposal,
        scene_context: dict,
    ) -> NarrativeProseCritique:
        """Critique prose from craft and continuity perspective."""
        prompt = f"""Critique this prose proposal from {target_agent} focusing on PROSE CRAFT.

PROSE TO CRITIQUE:
{proposal.to_prose()[:3000]}

PREVIOUS SCENE ENDING (should connect to):
{scene_context.get('previous_prose', 'N/A')[-300:] if scene_context.get('previous_prose') else 'First scene'}

CRITIQUE FROM PROSE CRAFT PERSPECTIVE:
Score each dimension 1-10:
1. character_accuracy_score: Are characters portrayed well?
2. sensory_immersion_score: Is the scene vivid?
3. world_integration_score: Are world details present?
4. plot_urgency_score: Is urgency maintained?
5. prose_quality_score: Is prose VARIED in rhythm? Free of CLICHES? Strong VERBS? Show not tell?

Focus your critique on:
- Does it CONNECT to previous scene?
- Is sentence LENGTH varied intentionally?
- Are verbs STRONG or weak?
- Any "suddenly", "very", "felt", "thought", passive voice, cliches?
- Does it end with RESONANCE?

Provide specific_suggestions with BEFORE/AFTER examples."""

        return self.invoke_structured(prompt, NarrativeProseCritique, max_tokens=1500)

    def vote_for_best(
        self,
        proposals: list[NarrativeProseProposal],
        scene_context: dict,
    ) -> NarrativeProseVote:
        """Vote for the best prose proposal."""
        proposals_text = "\n\n---\n\n".join([
            f"PROPOSAL FROM {p.agent_name}:\n{p.to_prose()[:1500]}..."
            for p in proposals if p.agent_name != self.name
        ])

        prompt = f"""Vote for the BEST prose proposal (you cannot vote for your own).

PROPOSALS:
{proposals_text}

As the NARRATIVE_CONTINUITY agent, vote for the proposal that:
1. Has best PROSE RHYTHM (varied sentence length)
2. Uses strongest VERBS, fewest cliches
3. CONNECTS best to the previous scene
4. Ends with most RESONANCE

You CANNOT vote for NARRATIVE_CONTINUITY.

Provide:
- voted_for_agent: Name of agent you vote for
- vote_reasoning: Why this is best crafted prose
- methodology_alignment: How it aligns with prose craft principles"""

        return self.invoke_structured(prompt, NarrativeProseVote, max_tokens=500)
