"""
Character Debate Agents for Step 2: Character Generation.

4 agents debate character design with different perspectives:

1. CharacterPsychologistAgent - Internal psychology, motivation, arc consistency
2. CharacterVisualistAgent - Physical appearance, costume, visual distinctiveness
3. CharacterNarrativeAgent - Role in story, relationships, scene presence
4. CharacterAudienceAgent - Relatability, emotional resonance, reader investment

Each agent:
- Proposes physical appearance based on their methodology
- Critiques other proposals
- Votes for the best proposal
"""

from src.story_agents.base_story_agent import BaseStoryAgent
from src.story_schemas import (
    PhysicalDescriptionSchema,
    CharacterPhysicalProposal,
    CharacterPhysicalCritique,
    CharacterPhysicalVote,
    CharacterBackstoryProposal,
)


# =============================================================================
# Character Debate Agents
# =============================================================================

class CharacterPsychologistAgent(BaseStoryAgent):
    """
    Focuses on internal psychology, motivation, and arc consistency.

    Core beliefs:
    - Characters must have INTERNAL LOGIC driving their actions
    - Motivation must connect to backstory trauma
    - Arc must show genuine transformation (not just event change)
    - Physical appearance should REFLECT psychological state
    """

    METHODOLOGY_NAME = "Character Psychology"
    METHODOLOGY_SOURCE = "Character development and psychological realism"
    CORE_BELIEFS = [
        "Characters must have INTERNAL LOGIC driving their actions",
        "Motivation must connect to backstory trauma or defining experiences",
        "Arc must show genuine psychological transformation",
        "Physical appearance should REFLECT inner state and life experiences",
        "Flaws must be directly connected to the story's stakes",
    ]

    @property
    def name(self) -> str:
        return "CHARACTER_PSYCHOLOGIST"

    @property
    def role(self) -> str:
        return "Character Psychology Expert"

    @property
    def system_prompt(self) -> str:
        return """You are a character psychology expert who designs characters from the inside out.

Your core beliefs:
- Characters must have INTERNAL LOGIC driving their actions
- Physical appearance should REFLECT psychological state and life experiences
- A shattered person shows it in their posture, grooming, eye contact
- Motivation connects directly to backstory trauma
- Transformation arc must feel psychologically EARNED

When designing a character's appearance:
- Consider how their emotional state affects their physical presentation
- Body language and posture reflect mental state
- Clothing choices reveal personality and status
- Physical details tell the character's story

## VISUAL DIFFERENTIATION (MANDATORY):
Physical appearance must be visually DISTINCT from every other character.
A character's psychology should manifest in UNIQUE physical traits:
- Different posture (a confident leader stands differently from a broken outcast)
- Different build (anxiety might make someone thin; comfort-eating might make another heavy)
- Different grooming (meticulous vs. unkempt reflects different inner states)
- Different movement style implied by build and posture
If a visual slot has been pre-assigned, you MUST design within that slot.
Psychology explains WHY this character looks the way the slot dictates.

You always connect the external to the internal."""

    def propose_physical(
        self,
        role: str,
        role_type: str,
        adjective: str,
        goal: str,
        stakes: str,
        setting: str,
        gender: str = "",
    ) -> CharacterPhysicalProposal:
        """Propose physical appearance based on psychological analysis."""
        gender_line = f"\nCHARACTER GENDER: {gender}\nUse {gender} pronouns consistently (he/him/his for male, she/her/hers for female). Set gender=\"{gender}\" in the physical schema." if gender else ""
        prompt = f"""Design the physical appearance for this character based on their psychological state:

CHARACTER ROLE: {role}
CHARACTER TYPE: {role_type}
EMOTIONAL STATE: {adjective}
GOAL: {goal}
STAKES: {stakes}{gender_line}
WORLD SETTING: {setting}

Design their appearance to REFLECT their psychological state.

Consider:
- How does being {adjective} affect their posture and body language?
- What does their clothing say about their mental state?
- How do they carry themselves given their goal and stakes?
- What physical signs of their emotional state would be visible?

CRITICAL FORMAT:
- gender: MUST be "{gender}" (pre-assigned, do not change)
- body_build: How their life/state shaped their body (1-2 sentences)
- height: Simple height description
- hair_color: Hair color AND style that reflects their state
- ethnicity: Ethnic appearance/complexion
- eye_color: Eye color
- distinguishing_features: ONLY if meaningful to their psychology, otherwise leave empty
- costume: DETAILED clothing that tells their story (2-3 sentences)

IMPORTANT: All description fields must use pronouns matching the character's gender ({gender}).

Provide a proposal matching CharacterPhysicalProposal schema."""

        return self.invoke_structured(prompt, CharacterPhysicalProposal, max_tokens=8000)

    def critique_proposal(
        self,
        target_agent: str,
        proposal: CharacterPhysicalProposal,
        role: str,
        adjective: str,
    ) -> CharacterPhysicalCritique:
        """Critique another agent's physical proposal."""
        prompt = f"""Critique this character physical design from a PSYCHOLOGICAL perspective:

TARGET AGENT: {target_agent}
CHARACTER ROLE: {role}
EMOTIONAL STATE: {adjective}

PROPOSAL:
- Body Build: {proposal.physical.body_build}
- Height: {proposal.physical.height}
- Hair: {proposal.physical.hair_color}
- Ethnicity: {proposal.physical.ethnicity}
- Eyes: {proposal.physical.eye_color}
- Distinguishing Features: {proposal.physical.distinguishing_features}
- Costume: {proposal.costume}
- Reasoning: {proposal.reasoning}

Evaluate:
1. Does the physical appearance REFLECT the psychological state ({adjective})?
2. Does the costume tell a coherent story about their mental state?
3. Are there psychological inconsistencies?

Provide a critique matching CharacterPhysicalCritique schema."""

        return self.invoke_structured(prompt, CharacterPhysicalCritique, max_tokens=8000)

    def vote_for_best(
        self,
        proposals: list[CharacterPhysicalProposal],
        role: str,
        adjective: str,
    ) -> CharacterPhysicalVote:
        """Vote for the best physical proposal."""
        proposals_text = "\n\n".join([
            f"PROPOSAL {i+1} by {p.agent_name}:\n"
            f"  Build: {p.physical.body_build}\n"
            f"  Costume: {p.costume}\n"
            f"  Reasoning: {p.reasoning}"
            for i, p in enumerate(proposals)
        ])

        prompt = f"""Vote for the BEST character physical design from a psychological perspective.

CHARACTER ROLE: {role}
EMOTIONAL STATE: {adjective}

PROPOSALS:
{proposals_text}

Which proposal best reflects the character's psychological state ({adjective})?
You CANNOT vote for your own proposal if you have one.

Provide a vote matching CharacterPhysicalVote schema."""

        return self.invoke_structured(prompt, CharacterPhysicalVote, max_tokens=8000)


class CharacterVisualistAgent(BaseStoryAgent):
    """
    Focuses on physical appearance, costume, and visual distinctiveness.

    Core beliefs:
    - Physical appearance should make characters INSTANTLY RECOGNIZABLE
    - Costume tells character's story (class, occupation, personality)
    - NO default scars - unique features must be MEANINGFUL
    - Visual design should aid reader in quickly identifying character
    - Contrast between characters helps distinguish them
    """

    METHODOLOGY_NAME = "Visual Character Design"
    METHODOLOGY_SOURCE = "Visual storytelling and character design principles"
    CORE_BELIEFS = [
        "Characters should be INSTANTLY RECOGNIZABLE from visual description",
        "Costume tells the character's story at a glance",
        "NO default scars - every unique feature must be MEANINGFUL",
        "Visual design aids quick reader identification",
        "Contrast between characters helps distinguish them",
    ]

    @property
    def name(self) -> str:
        return "CHARACTER_VISUALIST"

    @property
    def role(self) -> str:
        return "Visual Character Designer"

    @property
    def system_prompt(self) -> str:
        return """You are a visual character designer focused on DISTINCTIVE, RECOGNIZABLE character designs.

Your core beliefs:
- Each character should be INSTANTLY identifiable from their visual description
- Costume is the MOST important visual element - it tells the whole story
- NO default scars, birthmarks, or "interesting features" unless they MEAN something
- Physical design should reflect occupation, class, and personality
- Good character design creates visual contrast between characters

When designing:
- Make costume the star - what they wear defines them
- Consider silhouette - would this character be recognizable in shadow?
- Avoid generic "attractive" or "scarred" descriptions
- Connect physical details to their role and occupation
- Create memorable, specific details (not generic ones)

## VISUAL DIFFERENTIATION RULES (MANDATORY):
1. Apply the SILHOUETTE TEST: if this character is filled solid black,
   can you tell them apart from every other character by outline alone?
2. Apply the THUMBNAIL TEST: at 64x64 pixels (tiny image), can you STILL
   tell this character apart from every other character?
3. Assign a PRIMARY SHAPE to overall body proportions:
   - CIRCULAR = warm, rounded, approachable
   - RECTANGULAR = broad, sturdy, stable
   - TRIANGULAR = angular, dynamic, sharp
   - DIAMOND = narrow top/bottom, wide middle
   No two characters should share the same primary shape.
4. HAIR is the #1 visual identifier — vary color AND style AND length across cast.
   Hair must be dramatically different between characters (not just shade variations).
5. VARY body builds deliberately: wiry, stocky, lean, muscular, petite, lanky.
   NOT everyone "average" or "athletic."
6. VARY heights: short, below-average, above-average, tall. NOT everyone the same.
7. COSTUME COLOR: No two characters should share the same dominant clothing color.
   Each character gets their own color palette.
8. FABRIC/TEXTURE: Vary materials — one leather, one linen, one silk, one wool, etc.
9. SIGNATURE ACCESSORY: Each character must carry or wear ONE unique prop/accessory
   that no other character shares (a specific hat, a piece of jewelry, a tool, a weapon).
10. Scars are NOT a distinguishing feature unless the story demands it.
    Prefer: freckles, dimples, calloused hands, ink stains, weather-beaten skin.
11. If a visual slot has been pre-assigned, you MUST design within that slot.

FORBIDDEN (these are lazy AI defaults):
- Giving every character a facial scar
- Making everyone "average height" with "dark hair"
- Using "athletic build" as the default for everyone
- Making all characters the same ethnicity unless the story requires it
- Hazel eyes on more than one character
- "Soft" or "deep" as eye color modifiers on everyone
- Same dominant clothing color on multiple characters
- Generic "dark cloak" or "simple tunic" on everyone
- All characters in the same fabric/material

You design characters that readers can VISUALIZE instantly — even as tiny thumbnails."""

    def propose_physical(
        self,
        role: str,
        role_type: str,
        adjective: str,
        goal: str,
        stakes: str,
        setting: str,
        gender: str = "",
    ) -> CharacterPhysicalProposal:
        """Propose physical appearance focused on visual distinctiveness."""
        gender_line = f"\nCHARACTER GENDER: {gender}\nUse {gender} pronouns consistently (he/him/his for male, she/her/hers for female). Set gender=\"{gender}\" in the physical schema." if gender else ""
        prompt = f"""Design a VISUALLY DISTINCTIVE physical appearance for this character:

CHARACTER ROLE: {role}
CHARACTER TYPE: {role_type}
GOAL: {goal}{gender_line}
WORLD SETTING: {setting}

Create a design that makes this character INSTANTLY RECOGNIZABLE.

Focus on:
1. COSTUME (most important) - what do they wear that tells their story?
2. Body language and posture from their occupation/role
3. Visual contrast with typical characters in this setting
4. Memorable, SPECIFIC details (not generic)

CRITICAL RULES:
- gender: MUST be "{gender}" (pre-assigned, do not change)
- NO default scars, birthmarks, or mysterious marks unless they mean something
- distinguishing_features should be EMPTY unless truly significant
- Costume should be 2-3 sentences of SPECIFIC detail
- Make them visually memorable
- All description fields must use pronouns matching the character's gender ({gender})

Provide a proposal matching CharacterPhysicalProposal schema."""

        return self.invoke_structured(prompt, CharacterPhysicalProposal, max_tokens=8000)

    def critique_proposal(
        self,
        target_agent: str,
        proposal: CharacterPhysicalProposal,
        role: str,
        adjective: str,
    ) -> CharacterPhysicalCritique:
        """Critique from visual design perspective."""
        prompt = f"""Critique this character design from a VISUAL DISTINCTIVENESS perspective:

TARGET AGENT: {target_agent}
CHARACTER ROLE: {role}

PROPOSAL:
- Body Build: {proposal.physical.body_build}
- Hair: {proposal.physical.hair_color}
- Ethnicity: {proposal.physical.ethnicity}
- Distinguishing Features: {proposal.physical.distinguishing_features}
- Costume: {proposal.costume}
- Reasoning: {proposal.reasoning}

Evaluate:
1. Is this character VISUALLY DISTINCTIVE and memorable?
2. Does the costume tell their story effectively?
3. Are there any generic/default features (unnecessary scars, etc.)?
4. Would readers be able to visualize this character clearly?

Provide a critique matching CharacterPhysicalCritique schema."""

        return self.invoke_structured(prompt, CharacterPhysicalCritique, max_tokens=8000)

    def vote_for_best(
        self,
        proposals: list[CharacterPhysicalProposal],
        role: str,
        adjective: str,
    ) -> CharacterPhysicalVote:
        """Vote for most visually distinctive design."""
        proposals_text = "\n\n".join([
            f"PROPOSAL {i+1} by {p.agent_name}:\n"
            f"  Build: {p.physical.body_build}\n"
            f"  Costume: {p.costume}\n"
            f"  Features: {p.physical.distinguishing_features}"
            for i, p in enumerate(proposals)
        ])

        prompt = f"""Vote for the most VISUALLY DISTINCTIVE character design.

CHARACTER ROLE: {role}

PROPOSALS:
{proposals_text}

Which proposal creates the most memorable, recognizable character?
You CANNOT vote for your own proposal if you have one.

Provide a vote matching CharacterPhysicalVote schema."""

        return self.invoke_structured(prompt, CharacterPhysicalVote, max_tokens=8000)


class CharacterNarrativeAgent(BaseStoryAgent):
    """
    Focuses on role in story, relationships, and scene presence.

    Core beliefs:
    - Each character must SERVE the narrative purpose
    - Characters should create CONTRAST with each other
    - Supporting characters have their own goals (not just serve protagonist)
    - Physical appearance should hint at narrative role
    """

    METHODOLOGY_NAME = "Narrative Function"
    METHODOLOGY_SOURCE = "Story structure and character function analysis"
    CORE_BELIEFS = [
        "Each character must SERVE a clear narrative purpose",
        "Characters should create CONTRAST with each other",
        "Supporting characters have their OWN goals beyond serving the protagonist",
        "Physical appearance should hint at narrative role and function",
        "Character presence in scenes must be intentional",
    ]

    @property
    def name(self) -> str:
        return "CHARACTER_NARRATIVE"

    @property
    def role(self) -> str:
        return "Narrative Function Analyst"

    @property
    def system_prompt(self) -> str:
        return """You are a narrative function analyst who designs characters based on their ROLE IN THE STORY.

Your core beliefs:
- Every character exists to serve the narrative
- Physical appearance should hint at their function (mentor, foil, ally, threat)
- Characters create CONTRAST - protagonists need supporting cast that highlights them
- Even minor characters need clear purpose and presence

When designing:
- Consider what this character DOES for the story
- How do they contrast with the protagonist?
- What visual cues hint at their narrative role?
- How does their appearance set reader expectations?

## VISUAL DIFFERENTIATION (MANDATORY):
Characters must be visually distinguishable in EVERY scene. If two characters
stood side by side as silhouettes, readers must tell them apart INSTANTLY.
Narrative role should drive CONTRASTING visual design:
- Mentor vs. protege should look fundamentally different (not just older/younger)
- Antagonist should be visually opposite to protagonist (different shape, color palette, build)
- Allies should be visually distinct from each other — not a matching set
- Think Disney/Pixar: every character has a unique silhouette and color scheme
If a visual slot has been pre-assigned, you MUST design within that slot.

You design characters that FIT their narrative function AND are visually unmistakable."""

    def propose_physical(
        self,
        role: str,
        role_type: str,
        adjective: str,
        goal: str,
        stakes: str,
        setting: str,
        gender: str = "",
    ) -> CharacterPhysicalProposal:
        """Propose physical appearance based on narrative function."""
        gender_line = f"\nCHARACTER GENDER: {gender}\nUse {gender} pronouns consistently (he/him/his for male, she/her/hers for female). Set gender=\"{gender}\" in the physical schema." if gender else ""
        prompt = f"""Design physical appearance based on NARRATIVE FUNCTION:

CHARACTER ROLE: {role}
CHARACTER TYPE: {role_type} (their function: protagonist/antagonist/supporting)
PROTAGONIST STATE: {adjective}
PROTAGONIST GOAL: {goal}
STAKES: {stakes}{gender_line}
WORLD SETTING: {setting}

Design appearance that reflects their NARRATIVE PURPOSE.

Consider:
- What story function does this character serve?
- How should they CONTRAST with the protagonist?
- What visual cues hint at their role (mentor, ally, threat, foil)?
- How does their appearance set reader expectations?

For {role_type}:
- Protagonist: Design that readers root for
- Antagonist: Design that creates meaningful opposition
- Supporting: Design that complements/contrasts protagonist

IMPORTANT: gender MUST be "{gender}" (pre-assigned). All descriptions must use matching pronouns.

Provide a proposal matching CharacterPhysicalProposal schema."""

        return self.invoke_structured(prompt, CharacterPhysicalProposal, max_tokens=8000)

    def critique_proposal(
        self,
        target_agent: str,
        proposal: CharacterPhysicalProposal,
        role: str,
        adjective: str,
    ) -> CharacterPhysicalCritique:
        """Critique from narrative function perspective."""
        prompt = f"""Critique this character design from a NARRATIVE FUNCTION perspective:

TARGET AGENT: {target_agent}
CHARACTER ROLE: {role}

PROPOSAL:
- Body Build: {proposal.physical.body_build}
- Costume: {proposal.costume}
- Reasoning: {proposal.reasoning}

Evaluate:
1. Does the design clearly signal their narrative function?
2. Will this design create good CONTRAST with other characters?
3. Does the appearance set appropriate reader expectations?
4. Does the design serve the story effectively?

Provide a critique matching CharacterPhysicalCritique schema."""

        return self.invoke_structured(prompt, CharacterPhysicalCritique, max_tokens=8000)

    def vote_for_best(
        self,
        proposals: list[CharacterPhysicalProposal],
        role: str,
        adjective: str,
    ) -> CharacterPhysicalVote:
        """Vote for best design from narrative perspective."""
        proposals_text = "\n\n".join([
            f"PROPOSAL {i+1} by {p.agent_name}:\n"
            f"  Costume: {p.costume}\n"
            f"  Reasoning: {p.reasoning}"
            for i, p in enumerate(proposals)
        ])

        prompt = f"""Vote for the design that best serves the NARRATIVE FUNCTION.

CHARACTER ROLE: {role}

PROPOSALS:
{proposals_text}

Which proposal best serves this character's role in the story?
You CANNOT vote for your own proposal if you have one.

Provide a vote matching CharacterPhysicalVote schema."""

        return self.invoke_structured(prompt, CharacterPhysicalVote, max_tokens=8000)


class CharacterAudienceAgent(BaseStoryAgent):
    """
    Focuses on relatability, emotional resonance, and reader investment.

    Core beliefs:
    - Readers must be able to EMPATHIZE with the character
    - Universal emotions (fear, hope, love, loss) create connection
    - Characters need relatable struggles
    - Physical design should evoke appropriate emotional response
    """

    METHODOLOGY_NAME = "Audience Connection"
    METHODOLOGY_SOURCE = "Reader psychology and emotional engagement"
    CORE_BELIEFS = [
        "Readers must be able to EMPATHIZE with the character",
        "Universal emotions create deep connection",
        "Characters need struggles readers can relate to",
        "Physical design should evoke appropriate emotional response",
        "Approachability matters - readers need to care",
    ]

    @property
    def name(self) -> str:
        return "CHARACTER_AUDIENCE"

    @property
    def role(self) -> str:
        return "Audience Connection Expert"

    @property
    def system_prompt(self) -> str:
        return """You are an audience connection expert who designs characters readers will CARE about.

Your core beliefs:
- Readers need to EMPATHIZE with characters quickly
- Physical appearance creates first impressions
- Relatable details build emotional connection
- Universal struggles (loneliness, fear, hope) resonate
- Characters should feel like real people, not archetypes

When designing:
- What makes this character RELATABLE?
- What physical details invite empathy?
- How does their appearance invite connection?
- What tells readers "this could be me"?

## VISUAL DIFFERENTIATION (MANDATORY):
Audiences identify characters by visual shorthand. Each character needs ONE
iconic visual trait that no other character shares. Think Disney:
- Elsa = ice-blue, single braid, tall and regal
- Anna = warm colors, double braids, shorter and energetic
- Rapunzel = impossibly long golden hair
Every character needs that ONE thing an audience remembers instantly.
If a visual slot has been pre-assigned, you MUST design within that slot.
Make the character relatable AND visually unmistakable.

You design characters that readers emotionally invest in AND can identify at a glance."""

    def propose_physical(
        self,
        role: str,
        role_type: str,
        adjective: str,
        goal: str,
        stakes: str,
        setting: str,
        gender: str = "",
    ) -> CharacterPhysicalProposal:
        """Propose physical appearance focused on audience connection."""
        gender_line = f"\nCHARACTER GENDER: {gender}\nUse {gender} pronouns consistently (he/him/his for male, she/her/hers for female). Set gender=\"{gender}\" in the physical schema." if gender else ""
        prompt = f"""Design physical appearance that creates AUDIENCE CONNECTION:

CHARACTER ROLE: {role}
CHARACTER TYPE: {role_type}
EMOTIONAL STATE: {adjective}
GOAL: {goal}
STAKES: {stakes}{gender_line}
WORLD SETTING: {setting}

Design appearance that makes readers CARE about this character.

Consider:
- What physical details invite empathy?
- How can their appearance signal relatable struggles?
- What makes them feel like a REAL person, not an archetype?
- How does their look create emotional connection?

For a {adjective} character:
- What physical signs of their struggle would readers recognize?
- How do we show their humanity through appearance?

IMPORTANT: gender MUST be "{gender}" (pre-assigned). All descriptions must use matching pronouns.

Provide a proposal matching CharacterPhysicalProposal schema."""

        return self.invoke_structured(prompt, CharacterPhysicalProposal, max_tokens=8000)

    def critique_proposal(
        self,
        target_agent: str,
        proposal: CharacterPhysicalProposal,
        role: str,
        adjective: str,
    ) -> CharacterPhysicalCritique:
        """Critique from audience connection perspective."""
        prompt = f"""Critique this character design from an AUDIENCE CONNECTION perspective:

TARGET AGENT: {target_agent}
CHARACTER ROLE: {role}
EMOTIONAL STATE: {adjective}

PROPOSAL:
- Body Build: {proposal.physical.body_build}
- Hair: {proposal.physical.hair_color}
- Costume: {proposal.costume}
- Reasoning: {proposal.reasoning}

Evaluate:
1. Will readers EMPATHIZE with this character?
2. Does the design feel like a real person or an archetype?
3. Are there relatable details that build connection?
4. Does the appearance invite emotional investment?

Provide a critique matching CharacterPhysicalCritique schema."""

        return self.invoke_structured(prompt, CharacterPhysicalCritique, max_tokens=8000)

    def vote_for_best(
        self,
        proposals: list[CharacterPhysicalProposal],
        role: str,
        adjective: str,
    ) -> CharacterPhysicalVote:
        """Vote for most relatable design."""
        proposals_text = "\n\n".join([
            f"PROPOSAL {i+1} by {p.agent_name}:\n"
            f"  Build: {p.physical.body_build}\n"
            f"  Costume: {p.costume}"
            for i, p in enumerate(proposals)
        ])

        prompt = f"""Vote for the design that best creates AUDIENCE CONNECTION.

CHARACTER ROLE: {role}
EMOTIONAL STATE: {adjective}

PROPOSALS:
{proposals_text}

Which proposal will make readers CARE about this character most?
You CANNOT vote for your own proposal if you have one.

Provide a vote matching CharacterPhysicalVote schema."""

        return self.invoke_structured(prompt, CharacterPhysicalVote, max_tokens=8000)


# =============================================================================
# Backstory Generation Agent
# =============================================================================

class CharacterBackstoryAgent(BaseStoryAgent):
    """
    Generates character backstory bullet points from story outline.

    Analyzes structure beats to extract relevant backstory points.
    """

    @property
    def name(self) -> str:
        return "CHARACTER_BACKSTORY"

    @property
    def role(self) -> str:
        return "Backstory Generator"

    @property
    def system_prompt(self) -> str:
        return """You are a backstory specialist who creates unique character histories.

Your approach:
- Generate backstory SPECIFIC to the character role you're given
- NEVER reference other characters (like "the archivist") unless that IS the character
- Create 3-6 specific bullet points that explain WHO this character is
- Each bullet should be a single, clear statement about THIS character
- Generate unique personality traits, speech patterns, and qualities

CRITICAL: If given "the closest friend" - write about THE FRIEND, not the protagonist.
If given "the antagonist" - write about THE ANTAGONIST, not the protagonist.

Each character is their own person with their own history."""

    def generate_backstory(
        self,
        role: str,
        role_type: str,
        adjective: str,
        goal: str,
        stakes: str,
        structure_beats: dict,
        setting: str,
        gender: str = "",
        suggested_role: str = "",
    ) -> CharacterBackstoryProposal:
        """Generate backstory bullet points from story outline."""

        # Format structure beats for context
        beats_text = ""
        for beat_name, beat in structure_beats.items():
            if isinstance(beat, dict):
                desc = beat.get("description", "")
                state = beat.get("emotional_state", "")
                beats_text += f"\n{beat_name.upper()}: {desc}\n  Emotional State: {state}\n"

        prompt = f"""Generate a COMPLETE character profile for THIS SPECIFIC character:

═══════════════════════════════════════════════════════════════
⚠️  CRITICAL: Generate backstory for "{role}" - NOT the protagonist!
═══════════════════════════════════════════════════════════════

CHARACTER TO DEVELOP: {role}
CHARACTER TYPE: {role_type}

{'PROTAGONIST STATE: ' + adjective if role_type == 'protagonist' else 'PROTAGONIST (for context only): ' + adjective + ' - DO NOT write about them!'}
STORY GOAL: {goal}
STORY STAKES: {stakes}

STORY CONTEXT:
{beats_text}

WORLD SETTING: {setting}
{f"SUGGESTED OCCUPATION/ROLE: {suggested_role}" if suggested_role else ""}
{("If a suggested role is provided above, ground this character's backstory, speech patterns, "
  "and qualities in this specific profession/position. Their expertise, daily routines, "
  "and professional vocabulary should inform who they are.") if suggested_role else ""}

═══════════════════════════════════════════════════════════════
GENERATE FOR "{role.upper()}" (NOT the protagonist unless this IS the protagonist):
═══════════════════════════════════════════════════════════════

1. BACKSTORY POINTS (3-6 bullets about THIS character's history):
   - If this is "the closest friend" → their childhood, their job, why they're friends with protagonist
   - If this is "the antagonist" → their rise to power, their motivations, their past
   - Each bullet is about THIS character, not anyone else

2. MOTIVATION: What drives THIS character (not the protagonist)

3. ARC: How THIS character changes during the story

4. PERSONALITY_TRAITS (3-5 unique traits for THIS character):
   - NOT generic like "determined, complex, evolving"
   - SPECIFIC like "paranoid about locked doors", "laughs when nervous", "fiercely protective"

5. ACCENT/SPEECH PATTERN: How THIS character speaks (choose ONE or combine):
   - REGIONAL DIALECT: Based on setting (e.g., "thick Scottish brogue", "Southern drawl", "clipped British accent", "Brooklyn street talk")
   - GRAMMATICAL STYLE: How they construct sentences (e.g., "formal scholarly with perfect grammar", "drops articles and uses sentence fragments", "speaks in passive voice", "always uses rhetorical questions")
   - VOCABULARY: Their word choice (e.g., "uses archaic words", "peppers speech with technical jargon", "street slang heavy", "flowery and metaphorical")
   - SPEECH IMPEDIMENT (for ~10% of characters): Physical or psychological (e.g., "slight lisp on 's' sounds", "stutters when nervous", "speaks in whispers", "talks too fast when excited")
   - TEMPO/RHYTHM: Speed and cadence (e.g., "slow and deliberate", "rapid-fire delivery", "pauses mid-sentence to think", "talks in bursts")

   IMPORTANT: Every character comes from somewhere, so give them a regional/cultural speech pattern that fits the setting.
   Examples: "warm rural drawl with agricultural metaphors", "clipped aristocratic with formal diction", "hesitant whisper with stuttered 't' sounds", "rapid street slang from the market district"

6. QUALITIES (5-7 specific quirks/behaviors for THIS character):
   - e.g., "obsessively counts things", "speaks in metaphors", "never makes eye contact"
   - "always arrives early", "hums when thinking", "collects odd trinkets"

7. TAGS & TRAITS (Butcher technique — mandatory per character):
   These create instant reader recognition. Once assigned, these EXACT words/items recur in every scene.
   - APPEARANCE TAGS (2-3 vivid words): Repeated every time this character appears. EXCLUSIVE — never
     use another character's tag words. E.g., "gaunt, iron-gray, weathered" or "wiry, sun-darkened, hawk-nosed"
   - PROP TRAITS (1-2 signature items): Objects always associated with them.
     E.g., "fur-lined cloak", "bone-handled knife", "cracked leather satchel"
   - MANNERISM TRAIT: One recurring physical behavior. E.g., "cracks knuckles one by one"
   - SPEECH FINGERPRINT: Sentence length tendency + formality + metaphor source in one line.
     E.g., "terse, casual, military metaphors" or "verbose, formal, botanical analogies"

8. BEHAVIORAL SIGNATURE (one unique answer per category — these MUST be specific to THIS character):
   Each category needs a CONCRETE, OBSERVABLE behavior — not abstract descriptions.
   These will be used by prose agents to write consistent, character-specific actions throughout the story.

   - STRESS TELL: Involuntary physical reaction under pressure
     (e.g., "cracks knuckles one by one", "jaw clenches, neck vein pulses", "picks at cuticles")
   - IDLE HABIT: What they do when thinking or waiting — MUST differ from other characters
     (e.g., "turns ring. Twice.", "taps index finger in morse rhythm", "traces figure-eights on nearest surface")
   - DIALOGUE AVOIDANCE: How they dodge emotional conversations
     (e.g., "deflects with sarcasm", "changes subject to logistics", "answers a question with a question")
   - COMFORT ACTION: Self-soothing gesture tied to their backstory
     (e.g., "touches locket at throat", "runs thumb along blade handle", "presses thumb into opposite palm")
   - STACCATO PATTERN: Example of their inner thought rhythm under duress (write an actual example)
     (e.g., "The door. Locked. No — jammed.", "Three guards. Two exits. One chance.")
   - ENVIRONMENTAL DISPLACEMENT: How they express emotion by noticing objects instead of feelings
     (e.g., "The coffee had gone cold.", "The flowers needed water.", "Someone had left the window open.")
   - SENSORY BIAS: Which sense they default to AND WHY from backstory (must connect to their history)
     (e.g., "sound-first — grew up blind until age 8", "smell-first — trained as perfumer", "touch-first — worked leather since childhood")
   - EXPERIENCE TELLS: Casual competence that implies backstory without stating it
     (e.g., "checked the exits before sitting", "counted the guards without looking up", "tested the rope with two sharp tugs")

9. GENDER: This character's gender is '{gender}'
   - Use this exact gender assignment

RULES:
- NEVER mention "the archivist" or the protagonist UNLESS this IS the protagonist
- Each field is about "{role}" specifically
- Be specific and unique - no generic traits
- Make this character feel like a real, distinct person

Provide a proposal matching CharacterBackstoryProposal schema."""

        return self.invoke_structured(prompt, CharacterBackstoryProposal, max_tokens=8000)
