"""
Location Debate Agents for Step 4: Location Generation.

12 agents debate location design across 4 dimensions:

NAME (3 agents):
1. LocationNameCreativeAgent - Evocative, memorable, tonally appropriate names
2. LocationNameAuthenticAgent - Realistic, setting-appropriate, culturally accurate names
3. LocationNameThematicAgent - Names that embody themes and foreshadow meaning

PHYSICAL DESCRIPTION (3 agents):
4. LocationPhysicalSensoryAgent - Rich sensory details, immersive physical description
5. LocationPhysicalFunctionalAgent - Practical layout, spatial logic, usability
6. LocationPhysicalSymbolicAgent - Visual symbolism, meaningful architectural choices

ATMOSPHERE (3 agents):
7. LocationAtmosphereMoodAgent - Emotional tone, visceral feeling, mood evocation
8. LocationAtmosphereConflictAgent - Tension potential, dramatic opportunities
9. LocationAtmosphereCharacterAgent - How space reflects/challenges character psychology

THEMATIC SIGNIFICANCE (3 agents):
10. LocationThematicResonanceAgent - Direct thematic embodiment and reinforcement
11. LocationThematicContrastAgent - Ironic subversion, thematic opposition
12. LocationThematicEvolutionAgent - How location meaning changes through story

Each agent:
- Proposes their aspect of location design based on their methodology
- Critiques other proposals from their perspective
- Votes for the best proposal
"""

from src.story_agents.base_story_agent import BaseStoryAgent
from src.story_schemas import (
    LocationNameProposal,
    LocationNameCritique,
    LocationNameVote,
    LocationPhysicalProposal,
    LocationPhysicalCritique,
    LocationPhysicalVote,
    LocationAtmosphereProposal,
    LocationAtmosphereCritique,
    LocationAtmosphereVote,
    LocationThematicProposal,
    LocationThematicCritique,
    LocationThematicVote,
)


# =============================================================================
# NAME DEBATE AGENTS (3 agents)
# =============================================================================

class LocationNameCreativeAgent(BaseStoryAgent):
    """
    Focuses on evocative, memorable, tonally appropriate names.

    Core beliefs:
    - Names should evoke emotion and imagery
    - The best names are memorable and distinctive
    - Names must match the story's tone (dark, whimsical, realistic, etc.)
    - Sound matters - harsh consonants vs. soft vowels create different feelings
    - Names should hint at what happens here without being too literal
    """

    @property
    def name(self) -> str:
        return "LOC_NAME_CREATIVE"

    @property
    def role(self) -> str:
        return "Creative Location Naming Expert"

    @property
    def system_prompt(self) -> str:
        return """You are a creative location naming expert focused on evocative, memorable names.

Your core beliefs:
- Names should evoke emotion and imagery
- The best names are memorable and distinctive
- Names must match the story's tone (dark, whimsical, realistic, epic, etc.)
- Sound matters - harsh consonants create tension, soft vowels create comfort
- Names should hint at what happens here without being too literal
- Avoid generic names like "The Dark Forest" or "Old Mansion"

When creating names:
- Consider phonetic qualities and rhythm
- Use unexpected combinations that feel fresh
- Make sure the name is easy to remember and pronounce
- Let the name create atmosphere through sound and association
- Balance creativity with clarity - don't be too obscure"""

    def propose_name(
        self,
        location_type: str,
        setting: str,
        tone: str,
        thematic_question: str,
    ) -> LocationNameProposal:
        """Propose a location name based on creative principles."""
        prompt = f"""Create an evocative, memorable name for this location:

LOCATION TYPE: {location_type}
WORLD SETTING: {setting}
STORY TONE: {tone}
THEMATIC QUESTION: {thematic_question}

Design a name that:
- Evokes emotion and imagery
- Is memorable and distinctive
- Matches the story's tone
- Has pleasing or appropriate sound qualities
- Hints at significance without being too literal

Provide a proposal matching LocationNameProposal schema."""

        return self.invoke_structured(prompt, LocationNameProposal, max_tokens=8000)

    def critique_name(
        self,
        proposal: LocationNameProposal,
        location_type: str,
        tone: str,
    ) -> LocationNameCritique:
        """Critique another agent's name proposal."""
        prompt = f"""Critique this location name from a CREATIVE perspective:

TARGET AGENT: {proposal.agent_name}
LOCATION TYPE: {location_type}
STORY TONE: {tone}

PROPOSED NAME: {proposal.location_name}
REASONING: {proposal.reasoning}

Evaluate:
1. Is the name evocative and memorable?
2. Does it match the story's tone?
3. Are the phonetic qualities appropriate?
4. Is it distinctive or generic?
5. Does it create the right emotional association?

Provide a critique matching LocationNameCritique schema."""

        return self.invoke_structured(prompt, LocationNameCritique, max_tokens=8000)

    def vote(
        self,
        proposals: list[LocationNameProposal],
        location_type: str,
        tone: str,
    ) -> LocationNameVote:
        """Vote for the best location name."""
        proposals_text = "\n\n".join([
            f"PROPOSAL {i} by {p.agent_name}:\n"
            f"  Name: {p.location_name}\n"
            f"  Reasoning: {p.reasoning}"
            for i, p in enumerate(proposals)
        ])

        prompt = f"""Vote for the BEST location name from a creative perspective.

LOCATION TYPE: {location_type}
STORY TONE: {tone}

PROPOSALS:
{proposals_text}

Which name is most evocative, memorable, and tonally appropriate?
You CANNOT vote for your own proposal.

Provide a vote matching LocationNameVote schema."""

        return self.invoke_structured(prompt, LocationNameVote, max_tokens=8000)


class LocationNameAuthenticAgent(BaseStoryAgent):
    """
    Focuses on realistic, setting-appropriate, culturally accurate names.

    Core beliefs:
    - Names must fit the world's cultural/historical context
    - Realism grounds the story and builds credibility
    - Names should follow setting-appropriate naming conventions
    - Anachronisms break immersion
    - Local language and etymology matter
    """

    @property
    def name(self) -> str:
        return "LOC_NAME_AUTHENTIC"

    @property
    def role(self) -> str:
        return "Authentic Location Naming Expert"

    @property
    def system_prompt(self) -> str:
        return """You are an authentic location naming expert focused on realism and cultural accuracy.

Your core beliefs:
- Names must fit the world's cultural and historical context
- Realism grounds the story and builds reader credibility
- Names should follow setting-appropriate naming conventions
- Anachronisms break immersion
- Real places are named for practical reasons (geography, founders, function)

CRITICAL NAMING RULES:
- ALWAYS prefer accessible English-based fantasy names over constructed/indigenous-sounding names
- Names should be pronounceable and memorable to English readers
- AVOID creating fictional languages or overly exotic phonetics
- GOOD examples: "Mourner's Canyon", "The Echoing Grove", "Whispering Hollow", "Shadowfen Crossing"
- BAD examples: "Xalumiri Caldera", "Tāru-Mūra", "Kälen'thar", "Tlahuizcalli", "Teralith Holt"
- "Authentic" means fitting the story's world, NOT creating constructed languages
- Use English words with evocative meaning: descriptive adjectives + nouns (Broken Bridge, Silent Forest, etc.)

When evaluating names:
- Check cultural and historical appropriateness FOR THE GENRE (most fantasy uses English-based names)
- Consider who would have named this place and why
- Ensure it feels grounded in the setting
- Flag anything that sounds like a constructed language
- Balance authenticity with reader accessibility - accessibility wins"""

    def propose_name(
        self,
        location_type: str,
        setting: str,
        tone: str,
        thematic_question: str,
    ) -> LocationNameProposal:
        """Propose a location name based on authenticity principles."""
        prompt = f"""Create a realistic, setting-appropriate name for this location:

LOCATION TYPE: {location_type}
WORLD SETTING: {setting}
STORY TONE: {tone}
THEMATIC QUESTION: {thematic_question}

Design a name that:
- Fits the cultural and historical context
- Follows realistic naming conventions
- Sounds like it belongs in this world
- Has appropriate linguistic roots
- Feels grounded and authentic

Consider: Who would have named this place? When? Why?

Provide a proposal matching LocationNameProposal schema."""

        return self.invoke_structured(prompt, LocationNameProposal, max_tokens=8000)

    def critique_name(
        self,
        proposal: LocationNameProposal,
        location_type: str,
        setting: str,
    ) -> LocationNameCritique:
        """Critique another agent's name proposal."""
        prompt = f"""Critique this location name from an AUTHENTICITY perspective:

TARGET AGENT: {proposal.agent_name}
LOCATION TYPE: {location_type}
WORLD SETTING: {setting}

PROPOSED NAME: {proposal.location_name}
REASONING: {proposal.reasoning}

Evaluate:
1. Does it fit the cultural and historical context?
2. Does it follow realistic naming conventions?
3. Are there any anachronisms or setting inconsistencies?
4. Would this name make sense in this world?
5. Is it linguistically appropriate?

Provide a critique matching LocationNameCritique schema."""

        return self.invoke_structured(prompt, LocationNameCritique, max_tokens=8000)

    def vote(
        self,
        proposals: list[LocationNameProposal],
        location_type: str,
        setting: str,
    ) -> LocationNameVote:
        """Vote for the best location name."""
        proposals_text = "\n\n".join([
            f"PROPOSAL {i} by {p.agent_name}:\n"
            f"  Name: {p.location_name}\n"
            f"  Reasoning: {p.reasoning}"
            for i, p in enumerate(proposals)
        ])

        prompt = f"""Vote for the BEST location name from an authenticity perspective.

LOCATION TYPE: {location_type}
WORLD SETTING: {setting}

PROPOSALS:
{proposals_text}

Which name is most realistic, setting-appropriate, and culturally grounded?
You CANNOT vote for your own proposal.

Provide a vote matching LocationNameVote schema."""

        return self.invoke_structured(prompt, LocationNameVote, max_tokens=8000)


class LocationNameThematicAgent(BaseStoryAgent):
    """
    Focuses on names that embody themes and foreshadow meaning.

    Core beliefs:
    - Names should reinforce the story's central thematic question
    - The best location names have layers of meaning
    - Symbolism should be subtle, not heavy-handed
    - Names can foreshadow what happens in this space
    - Thematic resonance deepens emotional impact
    """

    @property
    def name(self) -> str:
        return "LOC_NAME_THEMATIC"

    @property
    def role(self) -> str:
        return "Thematic Location Naming Expert"

    @property
    def system_prompt(self) -> str:
        return """You are a thematic location naming expert focused on symbolic meaning.

Your core beliefs:
- Names should reinforce the story's central thematic question
- The best location names have layers of meaning
- Symbolism should be subtle, not heavy-handed
- Names can foreshadow what happens in this space
- Thematic resonance deepens emotional impact
- Avoid obvious metaphors - let meaning emerge naturally

When creating names:
- Consider how the name relates to the thematic question
- Look for double meanings and symbolic associations
- Let the name hint at character transformation that happens here
- Balance thematic depth with naturalistic feel
- Make sure symbolism serves the story, not the other way around"""

    def propose_name(
        self,
        location_type: str,
        setting: str,
        tone: str,
        thematic_question: str,
    ) -> LocationNameProposal:
        """Propose a location name based on thematic principles."""
        prompt = f"""Create a thematically resonant name for this location:

LOCATION TYPE: {location_type}
WORLD SETTING: {setting}
STORY TONE: {tone}
THEMATIC QUESTION: {thematic_question}

Design a name that:
- Reinforces the central thematic question
- Has layers of symbolic meaning
- Foreshadows significance without being obvious
- Creates thematic resonance
- Feels natural while carrying deeper meaning

Consider: How does this location relate to the thematic question? What transformation happens here?

Provide a proposal matching LocationNameProposal schema."""

        return self.invoke_structured(prompt, LocationNameProposal, max_tokens=8000)

    def critique_name(
        self,
        proposal: LocationNameProposal,
        location_type: str,
        thematic_question: str,
    ) -> LocationNameCritique:
        """Critique another agent's name proposal."""
        prompt = f"""Critique this location name from a THEMATIC perspective:

TARGET AGENT: {proposal.agent_name}
LOCATION TYPE: {location_type}
THEMATIC QUESTION: {thematic_question}

PROPOSED NAME: {proposal.location_name}
REASONING: {proposal.reasoning}

Evaluate:
1. Does it reinforce the thematic question?
2. Does it have layers of symbolic meaning?
3. Is the symbolism subtle or heavy-handed?
4. Does it create thematic resonance?
5. Does it foreshadow significance appropriately?

Provide a critique matching LocationNameCritique schema."""

        return self.invoke_structured(prompt, LocationNameCritique, max_tokens=8000)

    def vote(
        self,
        proposals: list[LocationNameProposal],
        location_type: str,
        thematic_question: str,
    ) -> LocationNameVote:
        """Vote for the best location name."""
        proposals_text = "\n\n".join([
            f"PROPOSAL {i} by {p.agent_name}:\n"
            f"  Name: {p.location_name}\n"
            f"  Reasoning: {p.reasoning}"
            for i, p in enumerate(proposals)
        ])

        prompt = f"""Vote for the BEST location name from a thematic perspective.

LOCATION TYPE: {location_type}
THEMATIC QUESTION: {thematic_question}

PROPOSALS:
{proposals_text}

Which name has the strongest thematic resonance and symbolic depth?
You CANNOT vote for your own proposal.

Provide a vote matching LocationNameVote schema."""

        return self.invoke_structured(prompt, LocationNameVote, max_tokens=8000)


# =============================================================================
# PHYSICAL DESCRIPTION DEBATE AGENTS (3 agents)
# =============================================================================

class LocationPhysicalSensoryAgent(BaseStoryAgent):
    """
    Focuses on rich sensory details and immersive physical description.

    Core beliefs:
    - All five senses bring locations to life
    - Specific details beat generic descriptions
    - Physical space should be cinematically vivid
    - Readers need to SEE, HEAR, SMELL, FEEL the location
    - Sensory details create emotional atmosphere
    """

    @property
    def name(self) -> str:
        return "LOC_PHYSICAL_SENSORY"

    @property
    def role(self) -> str:
        return "Sensory Location Description Expert"

    @property
    def system_prompt(self) -> str:
        return """You are a sensory location description expert focused on immersive, vivid details.

Your core beliefs:
- All five senses bring locations to life (not just visual)
- Specific details beat generic descriptions
- Physical space should be cinematically vivid
- Readers need to SEE, HEAR, SMELL, FEEL, TASTE the location
- Sensory details create emotional atmosphere
- Show texture, temperature, light quality, sounds, scents

When creating physical descriptions:
- Engage multiple senses in every description
- Use specific, concrete details (not vague generalities)
- Consider lighting and how it affects the space
- Include ambient sounds and background noise
- Don't forget smell and tactile sensations
- Make the space feel three-dimensional and inhabited"""

    def propose_physical(
        self,
        location_name: str,
        location_type: str,
        setting: str,
        thematic_question: str,
    ) -> LocationPhysicalProposal:
        """Propose physical description based on sensory richness."""
        prompt = f"""Create a sensory-rich physical description for this location:

LOCATION NAME: {location_name}
LOCATION TYPE: {location_type}
WORLD SETTING: {setting}
THEMATIC QUESTION: {thematic_question}

Design a physical description that:
- Engages all five senses (sight, sound, smell, touch, taste where appropriate)
- Uses specific, concrete details
- Creates a cinematically vivid image
- Shows texture, temperature, light quality
- Includes ambient sounds and scents
- Makes the space feel three-dimensional

Write 2-4 sentences of immersive sensory description.

Provide a proposal matching LocationPhysicalProposal schema."""

        return self.invoke_structured(prompt, LocationPhysicalProposal, max_tokens=8000)

    def critique_physical(
        self,
        proposal: LocationPhysicalProposal,
        location_type: str,
    ) -> LocationPhysicalCritique:
        """Critique another agent's physical description."""
        prompt = f"""Critique this physical description from a SENSORY perspective:

TARGET AGENT: {proposal.agent_name}
LOCATION TYPE: {location_type}

PHYSICAL DESCRIPTION: {proposal.physical_description}
REASONING: {proposal.reasoning}

Evaluate:
1. How many senses are engaged?
2. Are the details specific or generic?
3. Is the description cinematically vivid?
4. Can you SEE, HEAR, SMELL, FEEL this space?
5. Does it create immersive atmosphere?

Provide a critique matching LocationPhysicalCritique schema."""

        return self.invoke_structured(prompt, LocationPhysicalCritique, max_tokens=8000)

    def vote(
        self,
        proposals: list[LocationPhysicalProposal],
        location_type: str,
    ) -> LocationPhysicalVote:
        """Vote for the best physical description."""
        proposals_text = "\n\n".join([
            f"PROPOSAL {i} by {p.agent_name}:\n"
            f"  Description: {p.physical_description}\n"
            f"  Reasoning: {p.reasoning}"
            for i, p in enumerate(proposals)
        ])

        prompt = f"""Vote for the BEST physical description from a sensory perspective.

LOCATION TYPE: {location_type}

PROPOSALS:
{proposals_text}

Which description is most sensory-rich, specific, and immersive?
You CANNOT vote for your own proposal.

Provide a vote matching LocationPhysicalVote schema."""

        return self.invoke_structured(prompt, LocationPhysicalVote, max_tokens=8000)


class LocationPhysicalFunctionalAgent(BaseStoryAgent):
    """
    Focuses on practical layout, spatial logic, and usability.

    Core beliefs:
    - Locations must have clear spatial logic
    - Layout should serve story needs (blocking, staging)
    - Readers need to understand where things are
    - Functional details enable specific action
    - Space should feel USABLE for the scenes that happen here
    """

    @property
    def name(self) -> str:
        return "LOC_PHYSICAL_FUNCTIONAL"

    @property
    def role(self) -> str:
        return "Functional Location Design Expert"

    @property
    def system_prompt(self) -> str:
        return """You are a functional location design expert focused on spatial logic and usability.

Your core beliefs:
- Locations must have clear spatial logic (where things are in relation to each other)
- Layout should serve story needs (blocking, staging, chase scenes, conversations)
- Readers need to understand the geography of the space
- Functional details enable specific action
- Space should feel USABLE for the scenes that happen here
- Consider entrances, exits, sightlines, distances

When creating physical descriptions:
- Establish clear spatial relationships
- Note practical elements (doors, windows, furniture, obstacles)
- Consider how characters will move through this space
- Think about what actions need to happen here
- Ensure the layout supports dramatic needs
- Balance functionality with atmosphere"""

    def propose_physical(
        self,
        location_name: str,
        location_type: str,
        setting: str,
        thematic_question: str,
    ) -> LocationPhysicalProposal:
        """Propose physical description based on functional design."""
        prompt = f"""Create a functionally clear physical description for this location:

LOCATION NAME: {location_name}
LOCATION TYPE: {location_type}
WORLD SETTING: {setting}
THEMATIC QUESTION: {thematic_question}

Design a physical description that:
- Establishes clear spatial logic and layout
- Shows practical elements (entrances, exits, key features)
- Enables character movement and action
- Supports dramatic staging
- Makes the geography clear to readers
- Provides usable details for scenes

Write 2-4 sentences focused on functional spatial description.

Provide a proposal matching LocationPhysicalProposal schema."""

        return self.invoke_structured(prompt, LocationPhysicalProposal, max_tokens=8000)

    def critique_physical(
        self,
        proposal: LocationPhysicalProposal,
        location_type: str,
    ) -> LocationPhysicalCritique:
        """Critique another agent's physical description."""
        prompt = f"""Critique this physical description from a FUNCTIONAL perspective:

TARGET AGENT: {proposal.agent_name}
LOCATION TYPE: {location_type}

PHYSICAL DESCRIPTION: {proposal.physical_description}
REASONING: {proposal.reasoning}

Evaluate:
1. Is the spatial logic clear?
2. Are practical elements identified?
3. Can you understand the layout and geography?
4. Does it enable character movement and action?
5. Is the space usable for dramatic scenes?

Provide a critique matching LocationPhysicalCritique schema."""

        return self.invoke_structured(prompt, LocationPhysicalCritique, max_tokens=8000)

    def vote(
        self,
        proposals: list[LocationPhysicalProposal],
        location_type: str,
    ) -> LocationPhysicalVote:
        """Vote for the best physical description."""
        proposals_text = "\n\n".join([
            f"PROPOSAL {i} by {p.agent_name}:\n"
            f"  Description: {p.physical_description}\n"
            f"  Reasoning: {p.reasoning}"
            for i, p in enumerate(proposals)
        ])

        prompt = f"""Vote for the BEST physical description from a functional perspective.

LOCATION TYPE: {location_type}

PROPOSALS:
{proposals_text}

Which description has the clearest spatial logic and best supports dramatic action?
You CANNOT vote for your own proposal.

Provide a vote matching LocationPhysicalVote schema."""

        return self.invoke_structured(prompt, LocationPhysicalVote, max_tokens=8000)


class LocationPhysicalSymbolicAgent(BaseStoryAgent):
    """
    Focuses on visual symbolism and meaningful architectural choices.

    Core beliefs:
    - Physical details should carry symbolic weight
    - Architecture reflects deeper themes
    - Visual metaphors enhance meaning
    - Physical decay/beauty mirrors character states
    - Space can embody thematic conflicts
    """

    @property
    def name(self) -> str:
        return "LOC_PHYSICAL_SYMBOLIC"

    @property
    def role(self) -> str:
        return "Symbolic Location Design Expert"

    @property
    def system_prompt(self) -> str:
        return """You are a symbolic location design expert focused on meaningful physical details.

Your core beliefs:
- Physical details should carry symbolic weight
- Architecture and design reflect deeper themes
- Visual metaphors enhance meaning without being obvious
- Physical decay or beauty can mirror character states
- Space can embody thematic conflicts
- Every significant detail should resonate with story meaning

When creating physical descriptions:
- Choose details that have symbolic significance
- Consider how physical state reflects themes
- Use architectural metaphors (heights, depths, barriers, openings)
- Let physical qualities mirror emotional/thematic content
- Avoid heavy-handed symbolism - be subtle
- Ensure symbols serve the story naturally"""

    def propose_physical(
        self,
        location_name: str,
        location_type: str,
        setting: str,
        thematic_question: str,
    ) -> LocationPhysicalProposal:
        """Propose physical description based on symbolic design."""
        prompt = f"""Create a symbolically resonant physical description for this location:

LOCATION NAME: {location_name}
LOCATION TYPE: {location_type}
WORLD SETTING: {setting}
THEMATIC QUESTION: {thematic_question}

Design a physical description that:
- Includes details with symbolic significance
- Uses architecture/design to reflect themes
- Creates visual metaphors for thematic content
- Embodies the thematic question in physical form
- Shows meaning through physical qualities
- Maintains subtlety - not heavy-handed

Write 2-4 sentences of symbolically meaningful physical description.

Provide a proposal matching LocationPhysicalProposal schema."""

        return self.invoke_structured(prompt, LocationPhysicalProposal, max_tokens=8000)

    def critique_physical(
        self,
        proposal: LocationPhysicalProposal,
        location_type: str,
        thematic_question: str,
    ) -> LocationPhysicalCritique:
        """Critique another agent's physical description."""
        prompt = f"""Critique this physical description from a SYMBOLIC perspective:

TARGET AGENT: {proposal.agent_name}
LOCATION TYPE: {location_type}
THEMATIC QUESTION: {thematic_question}

PHYSICAL DESCRIPTION: {proposal.physical_description}
REASONING: {proposal.reasoning}

Evaluate:
1. Do physical details carry symbolic weight?
2. Does architecture reflect themes?
3. Are there effective visual metaphors?
4. Does the physical space embody thematic questions?
5. Is the symbolism subtle or heavy-handed?

Provide a critique matching LocationPhysicalCritique schema."""

        return self.invoke_structured(prompt, LocationPhysicalCritique, max_tokens=8000)

    def vote(
        self,
        proposals: list[LocationPhysicalProposal],
        location_type: str,
        thematic_question: str,
    ) -> LocationPhysicalVote:
        """Vote for the best physical description."""
        proposals_text = "\n\n".join([
            f"PROPOSAL {i} by {p.agent_name}:\n"
            f"  Description: {p.physical_description}\n"
            f"  Reasoning: {p.reasoning}"
            for i, p in enumerate(proposals)
        ])

        prompt = f"""Vote for the BEST physical description from a symbolic perspective.

LOCATION TYPE: {location_type}
THEMATIC QUESTION: {thematic_question}

PROPOSALS:
{proposals_text}

Which description has the strongest symbolic resonance and thematic depth?
You CANNOT vote for your own proposal.

Provide a vote matching LocationPhysicalVote schema."""

        return self.invoke_structured(prompt, LocationPhysicalVote, max_tokens=8000)


# =============================================================================
# ATMOSPHERE DEBATE AGENTS (3 agents)
# =============================================================================

class LocationAtmosphereMoodAgent(BaseStoryAgent):
    """
    Focuses on emotional tone, visceral feeling, and mood evocation.

    Core beliefs:
    - Atmosphere creates emotional resonance
    - Every location should have a distinct FEELING
    - Mood should match or contrast scene content strategically
    - Visceral emotional response matters more than literal description
    - Atmosphere primes reader for what's coming
    """

    @property
    def name(self) -> str:
        return "LOC_ATMOSPHERE_MOOD"

    @property
    def role(self) -> str:
        return "Atmospheric Mood Expert"

    @property
    def system_prompt(self) -> str:
        return """You are an atmospheric mood expert focused on emotional tone and visceral feeling.

Your core beliefs:
- Atmosphere creates emotional resonance with readers
- Every location should have a distinct FEELING that stays with the reader
- Mood should match scene content or create strategic contrast
- Visceral emotional response matters more than literal description
- Atmosphere primes reader expectations and emotions
- Use mood words, emotional associations, and feeling-focused language

When creating atmosphere:
- Focus on the FEELING the space evokes
- Use emotionally charged language
- Consider what emotions you want readers to feel here
- Think about psychological impact of the space
- Create mood through word choice and tone
- Balance evocation with clarity"""

    def propose_atmosphere(
        self,
        location_name: str,
        location_type: str,
        physical_description: str,
        thematic_question: str,
    ) -> LocationAtmosphereProposal:
        """Propose atmosphere based on emotional mood."""
        prompt = f"""Create an emotionally resonant atmosphere for this location:

LOCATION NAME: {location_name}
LOCATION TYPE: {location_type}
PHYSICAL DESCRIPTION: {physical_description}
THEMATIC QUESTION: {thematic_question}

Design an atmosphere that:
- Evokes a distinct emotional FEELING
- Creates visceral reader response
- Uses emotionally charged language
- Establishes psychological mood
- Primes reader emotions appropriately
- Resonates with thematic content

Write 2-3 sentences focused on emotional tone and mood.

Provide a proposal matching LocationAtmosphereProposal schema."""

        return self.invoke_structured(prompt, LocationAtmosphereProposal, max_tokens=8000)

    def critique_atmosphere(
        self,
        proposal: LocationAtmosphereProposal,
        location_type: str,
    ) -> LocationAtmosphereCritique:
        """Critique another agent's atmosphere proposal."""
        prompt = f"""Critique this atmosphere from a MOOD perspective:

TARGET AGENT: {proposal.agent_name}
LOCATION TYPE: {location_type}

ATMOSPHERE: {proposal.atmosphere}
REASONING: {proposal.reasoning}

Evaluate:
1. Does it evoke a distinct emotional feeling?
2. Is the language emotionally charged?
3. Does it create visceral reader response?
4. Is the psychological mood clear?
5. Does it effectively prime reader emotions?

Provide a critique matching LocationAtmosphereCritique schema."""

        return self.invoke_structured(prompt, LocationAtmosphereCritique, max_tokens=8000)

    def vote(
        self,
        proposals: list[LocationAtmosphereProposal],
        location_type: str,
    ) -> LocationAtmosphereVote:
        """Vote for the best atmosphere."""
        proposals_text = "\n\n".join([
            f"PROPOSAL {i} by {p.agent_name}:\n"
            f"  Atmosphere: {p.atmosphere}\n"
            f"  Reasoning: {p.reasoning}"
            for i, p in enumerate(proposals)
        ])

        prompt = f"""Vote for the BEST atmosphere from a mood perspective.

LOCATION TYPE: {location_type}

PROPOSALS:
{proposals_text}

Which atmosphere creates the strongest emotional resonance and visceral feeling?
You CANNOT vote for your own proposal.

Provide a vote matching LocationAtmosphereVote schema."""

        return self.invoke_structured(prompt, LocationAtmosphereVote, max_tokens=8000)


class LocationAtmosphereConflictAgent(BaseStoryAgent):
    """
    Focuses on tension potential and dramatic opportunities.

    Core beliefs:
    - Locations should enhance dramatic conflict
    - Atmosphere can create tension even in calm scenes
    - Space should have inherent dramatic potential
    - The best locations make conflict HARDER for characters
    - Environmental pressure raises stakes
    """

    @property
    def name(self) -> str:
        return "LOC_ATMOSPHERE_CONFLICT"

    @property
    def role(self) -> str:
        return "Conflict-Driven Atmosphere Expert"

    @property
    def system_prompt(self) -> str:
        return """You are a conflict-driven atmosphere expert focused on tension and dramatic potential.

Your core beliefs:
- Locations should enhance dramatic conflict, not just house it
- Atmosphere can create tension even in otherwise calm scenes
- Space should have inherent dramatic potential (danger, pressure, stakes)
- The best locations make conflict HARDER for characters to navigate
- Environmental pressure raises stakes organically
- Tension should simmer in the background of every scene here

When creating atmosphere:
- Identify sources of tension in the space
- Consider how location adds pressure to character conflicts
- Think about what could go wrong here
- Show how space constrains or challenges characters
- Create underlying unease or threat
- Balance overt danger with subtle tension"""

    def propose_atmosphere(
        self,
        location_name: str,
        location_type: str,
        physical_description: str,
        thematic_question: str,
    ) -> LocationAtmosphereProposal:
        """Propose atmosphere based on conflict potential."""
        prompt = f"""Create a tension-filled atmosphere for this location:

LOCATION NAME: {location_name}
LOCATION TYPE: {location_type}
PHYSICAL DESCRIPTION: {physical_description}
THEMATIC QUESTION: {thematic_question}

Design an atmosphere that:
- Enhances dramatic conflict
- Creates inherent tension
- Shows dramatic potential of the space
- Adds pressure to character situations
- Suggests what could go wrong
- Maintains underlying threat or unease

Write 2-3 sentences focused on tension and conflict potential.

Provide a proposal matching LocationAtmosphereProposal schema."""

        return self.invoke_structured(prompt, LocationAtmosphereProposal, max_tokens=8000)

    def critique_atmosphere(
        self,
        proposal: LocationAtmosphereProposal,
        location_type: str,
    ) -> LocationAtmosphereCritique:
        """Critique another agent's atmosphere proposal."""
        prompt = f"""Critique this atmosphere from a CONFLICT perspective:

TARGET AGENT: {proposal.agent_name}
LOCATION TYPE: {location_type}

ATMOSPHERE: {proposal.atmosphere}
REASONING: {proposal.reasoning}

Evaluate:
1. Does it enhance dramatic conflict?
2. Is there inherent tension in the space?
3. Does it show dramatic potential?
4. Does it add pressure to character situations?
5. Is there underlying threat or unease?

Provide a critique matching LocationAtmosphereCritique schema."""

        return self.invoke_structured(prompt, LocationAtmosphereCritique, max_tokens=8000)

    def vote(
        self,
        proposals: list[LocationAtmosphereProposal],
        location_type: str,
    ) -> LocationAtmosphereVote:
        """Vote for the best atmosphere."""
        proposals_text = "\n\n".join([
            f"PROPOSAL {i} by {p.agent_name}:\n"
            f"  Atmosphere: {p.atmosphere}\n"
            f"  Reasoning: {p.reasoning}"
            for i, p in enumerate(proposals)
        ])

        prompt = f"""Vote for the BEST atmosphere from a conflict perspective.

LOCATION TYPE: {location_type}

PROPOSALS:
{proposals_text}

Which atmosphere best enhances tension and dramatic potential?
You CANNOT vote for your own proposal.

Provide a vote matching LocationAtmosphereVote schema."""

        return self.invoke_structured(prompt, LocationAtmosphereVote, max_tokens=8000)


class LocationAtmosphereCharacterAgent(BaseStoryAgent):
    """
    Focuses on how space reflects and challenges character psychology.

    Core beliefs:
    - Atmosphere should mirror or contrast character emotional states
    - Locations can be extensions of character psychology
    - Space should challenge characters' internal conflicts
    - The best atmospheres feel personally significant to characters
    - Environmental mood can reflect character arc position
    """

    @property
    def name(self) -> str:
        return "LOC_ATMOSPHERE_CHARACTER"

    @property
    def role(self) -> str:
        return "Character-Psychological Atmosphere Expert"

    @property
    def system_prompt(self) -> str:
        return """You are a character-psychological atmosphere expert focused on character-space relationships.

Your core beliefs:
- Atmosphere should mirror or contrast character emotional states
- Locations can be extensions of character psychology (external made internal)
- Space should challenge characters' internal conflicts
- The best atmospheres feel personally significant to characters
- Environmental mood can reflect where character is in their arc
- Consider how characters EXPERIENCE this space psychologically

When creating atmosphere:
- Think about character emotional states and how space reflects them
- Consider which characters use this space and what it means to them
- Show how atmosphere challenges internal conflicts
- Create personal psychological significance
- Use space to externalize character feelings
- Balance character-specific resonance with general mood"""

    def propose_atmosphere(
        self,
        location_name: str,
        location_type: str,
        physical_description: str,
        thematic_question: str,
    ) -> LocationAtmosphereProposal:
        """Propose atmosphere based on character psychology."""
        prompt = f"""Create a character-resonant atmosphere for this location:

LOCATION NAME: {location_name}
LOCATION TYPE: {location_type}
PHYSICAL DESCRIPTION: {physical_description}
THEMATIC QUESTION: {thematic_question}

Design an atmosphere that:
- Reflects or contrasts character emotional states
- Acts as extension of character psychology
- Challenges internal character conflicts
- Feels personally significant to characters
- Shows how characters experience this space
- Externalizes character feelings through environment

Write 2-3 sentences focused on character-space psychological relationship.

Provide a proposal matching LocationAtmosphereProposal schema."""

        return self.invoke_structured(prompt, LocationAtmosphereProposal, max_tokens=8000)

    def critique_atmosphere(
        self,
        proposal: LocationAtmosphereProposal,
        location_type: str,
        thematic_question: str,
    ) -> LocationAtmosphereCritique:
        """Critique another agent's atmosphere proposal."""
        prompt = f"""Critique this atmosphere from a CHARACTER-PSYCHOLOGICAL perspective:

TARGET AGENT: {proposal.agent_name}
LOCATION TYPE: {location_type}
THEMATIC QUESTION: {thematic_question}

ATMOSPHERE: {proposal.atmosphere}
REASONING: {proposal.reasoning}

Evaluate:
1. Does it reflect or contrast character emotional states?
2. Can it serve as extension of character psychology?
3. Does it challenge internal character conflicts?
4. Does it feel personally significant to characters?
5. Does it show how characters experience this space?

Provide a critique matching LocationAtmosphereCritique schema."""

        return self.invoke_structured(prompt, LocationAtmosphereCritique, max_tokens=8000)

    def vote(
        self,
        proposals: list[LocationAtmosphereProposal],
        location_type: str,
    ) -> LocationAtmosphereVote:
        """Vote for the best atmosphere."""
        proposals_text = "\n\n".join([
            f"PROPOSAL {i} by {p.agent_name}:\n"
            f"  Atmosphere: {p.atmosphere}\n"
            f"  Reasoning: {p.reasoning}"
            for i, p in enumerate(proposals)
        ])

        prompt = f"""Vote for the BEST atmosphere from a character-psychological perspective.

LOCATION TYPE: {location_type}

PROPOSALS:
{proposals_text}

Which atmosphere best connects to character psychology and internal conflicts?
You CANNOT vote for your own proposal.

Provide a vote matching LocationAtmosphereVote schema."""

        return self.invoke_structured(prompt, LocationAtmosphereVote, max_tokens=8000)


# =============================================================================
# THEMATIC SIGNIFICANCE DEBATE AGENTS (3 agents)
# =============================================================================

class LocationThematicResonanceAgent(BaseStoryAgent):
    """
    Focuses on direct thematic embodiment and reinforcement.

    Core beliefs:
    - Locations should directly embody the thematic question
    - Space can be a living metaphor for themes
    - The best locations make themes VISIBLE and PHYSICAL
    - Every location should deepen thematic understanding
    - Thematic reinforcement should feel organic, not forced
    """

    @property
    def name(self) -> str:
        return "LOC_THEMATIC_RESONANCE"

    @property
    def role(self) -> str:
        return "Thematic Resonance Expert"

    @property
    def system_prompt(self) -> str:
        return """You are a thematic resonance expert focused on direct thematic embodiment.

Your core beliefs:
- Locations should directly embody the thematic question
- Space can be a living metaphor for central themes
- The best locations make themes VISIBLE and PHYSICAL
- Every location should deepen reader's thematic understanding
- Thematic reinforcement should feel organic, not forced or preachy
- Consider how space dramatizes the thematic conflict

When creating thematic significance:
- Show how location directly relates to thematic question
- Identify ways space embodies theme physically
- Consider which key thematic moments happen here
- Connect location to character's thematic journey
- Make themes visible through spatial qualities
- Ensure thematic connection feels natural and earned"""

    def propose_thematic(
        self,
        location_name: str,
        location_type: str,
        physical_description: str,
        atmosphere: str,
        thematic_question: str,
        key_scenes: list[str],
    ) -> LocationThematicProposal:
        """Propose thematic significance based on direct resonance."""
        prompt = f"""Define the thematic significance for this location:

LOCATION NAME: {location_name}
LOCATION TYPE: {location_type}
PHYSICAL DESCRIPTION: {physical_description}
ATMOSPHERE: {atmosphere}
THEMATIC QUESTION: {thematic_question}
KEY SCENES: {', '.join(key_scenes)}

Design thematic significance that:
- Directly embodies the thematic question
- Makes themes VISIBLE through physical space
- Shows how space dramatizes thematic conflict
- Connects to character's thematic journey
- Deepens thematic understanding organically
- Identifies which key thematic beats happen here

Provide a proposal matching LocationThematicProposal schema."""

        return self.invoke_structured(prompt, LocationThematicProposal, max_tokens=8000)

    def critique_thematic(
        self,
        proposal: LocationThematicProposal,
        location_type: str,
        thematic_question: str,
    ) -> LocationThematicCritique:
        """Critique another agent's thematic proposal."""
        prompt = f"""Critique this thematic significance from a RESONANCE perspective:

TARGET AGENT: {proposal.agent_name}
LOCATION TYPE: {location_type}
THEMATIC QUESTION: {thematic_question}

THEMATIC SIGNIFICANCE: {proposal.thematic_significance}
KEY SCENES: {proposal.key_scenes}
REASONING: {proposal.reasoning}

Evaluate:
1. Does it directly embody the thematic question?
2. Are themes made VISIBLE through the space?
3. Does it dramatize thematic conflict effectively?
4. Is the thematic connection organic or forced?
5. Does it deepen thematic understanding?

Provide a critique matching LocationThematicCritique schema."""

        return self.invoke_structured(prompt, LocationThematicCritique, max_tokens=8000)

    def vote(
        self,
        proposals: list[LocationThematicProposal],
        location_type: str,
        thematic_question: str,
    ) -> LocationThematicVote:
        """Vote for the best thematic significance."""
        proposals_text = "\n\n".join([
            f"PROPOSAL {i} by {p.agent_name}:\n"
            f"  Significance: {p.thematic_significance}\n"
            f"  Key Scenes: {p.key_scenes}\n"
            f"  Reasoning: {p.reasoning}"
            for i, p in enumerate(proposals)
        ])

        prompt = f"""Vote for the BEST thematic significance from a resonance perspective.

LOCATION TYPE: {location_type}
THEMATIC QUESTION: {thematic_question}

PROPOSALS:
{proposals_text}

Which proposal most directly and organically embodies the thematic question?
You CANNOT vote for your own proposal.

Provide a vote matching LocationThematicVote schema."""

        return self.invoke_structured(prompt, LocationThematicVote, max_tokens=8000)


class LocationThematicContrastAgent(BaseStoryAgent):
    """
    Focuses on ironic subversion and thematic opposition.

    Core beliefs:
    - The most powerful thematic moments come from CONTRAST
    - Ironic locations create deeper meaning (church as site of betrayal)
    - Subverting expectations strengthens themes
    - Opposition and contradiction make themes complex
    - Thematic tension is more interesting than reinforcement
    """

    @property
    def name(self) -> str:
        return "LOC_THEMATIC_CONTRAST"

    @property
    def role(self) -> str:
        return "Thematic Contrast Expert"

    @property
    def system_prompt(self) -> str:
        return """You are a thematic contrast expert focused on irony and opposition.

Your core beliefs:
- The most powerful thematic moments come from CONTRAST and irony
- Ironic locations create deeper meaning (beauty hiding ugliness, safety being dangerous)
- Subverting expectations strengthens thematic impact
- Opposition and contradiction make themes more complex
- Thematic tension is more interesting than simple reinforcement
- Consider what this location SEEMS vs. what it MEANS

When creating thematic significance:
- Look for ironic contrasts (appearance vs. reality)
- Consider how location might subvert expectations
- Find thematic opposition or contradiction
- Show complexity through contrasting elements
- Use irony to deepen thematic questions
- Balance contrast with clarity"""

    def propose_thematic(
        self,
        location_name: str,
        location_type: str,
        physical_description: str,
        atmosphere: str,
        thematic_question: str,
        key_scenes: list[str],
    ) -> LocationThematicProposal:
        """Propose thematic significance based on contrast."""
        prompt = f"""Define the thematic significance for this location emphasizing CONTRAST:

LOCATION NAME: {location_name}
LOCATION TYPE: {location_type}
PHYSICAL DESCRIPTION: {physical_description}
ATMOSPHERE: {atmosphere}
THEMATIC QUESTION: {thematic_question}
KEY SCENES: {', '.join(key_scenes)}

Design thematic significance that:
- Uses ironic contrast (appearance vs. reality)
- Subverts thematic expectations
- Shows opposition or contradiction
- Creates thematic tension through contrast
- Adds complexity to thematic questions
- Makes meaning through what's NOT obvious

Provide a proposal matching LocationThematicProposal schema."""

        return self.invoke_structured(prompt, LocationThematicProposal, max_tokens=8000)

    def critique_thematic(
        self,
        proposal: LocationThematicProposal,
        location_type: str,
        thematic_question: str,
    ) -> LocationThematicCritique:
        """Critique another agent's thematic proposal."""
        prompt = f"""Critique this thematic significance from a CONTRAST perspective:

TARGET AGENT: {proposal.agent_name}
LOCATION TYPE: {location_type}
THEMATIC QUESTION: {thematic_question}

THEMATIC SIGNIFICANCE: {proposal.thematic_significance}
KEY SCENES: {proposal.key_scenes}
REASONING: {proposal.reasoning}

Evaluate:
1. Does it use ironic contrast effectively?
2. Does it subvert thematic expectations?
3. Is there meaningful opposition or contradiction?
4. Does contrast add thematic complexity?
5. Is the irony clear but not heavy-handed?

Provide a critique matching LocationThematicCritique schema."""

        return self.invoke_structured(prompt, LocationThematicCritique, max_tokens=8000)

    def vote(
        self,
        proposals: list[LocationThematicProposal],
        location_type: str,
        thematic_question: str,
    ) -> LocationThematicVote:
        """Vote for the best thematic significance."""
        proposals_text = "\n\n".join([
            f"PROPOSAL {i} by {p.agent_name}:\n"
            f"  Significance: {p.thematic_significance}\n"
            f"  Key Scenes: {p.key_scenes}\n"
            f"  Reasoning: {p.reasoning}"
            for i, p in enumerate(proposals)
        ])

        prompt = f"""Vote for the BEST thematic significance from a contrast perspective.

LOCATION TYPE: {location_type}
THEMATIC QUESTION: {thematic_question}

PROPOSALS:
{proposals_text}

Which proposal uses ironic contrast and thematic opposition most effectively?
You CANNOT vote for your own proposal.

Provide a vote matching LocationThematicVote schema."""

        return self.invoke_structured(prompt, LocationThematicVote, max_tokens=8000)


class LocationThematicEvolutionAgent(BaseStoryAgent):
    """
    Focuses on how location meaning changes through the story.

    Core beliefs:
    - Locations should have different meaning at different story points
    - Character transformation changes how they see a space
    - The best locations evolve with the character arc
    - Return visits to locations show character growth
    - Thematic significance should deepen over time
    """

    @property
    def name(self) -> str:
        return "LOC_THEMATIC_EVOLUTION"

    @property
    def role(self) -> str:
        return "Thematic Evolution Expert"

    @property
    def system_prompt(self) -> str:
        return """You are a thematic evolution expert focused on how location meaning changes over time.

Your core beliefs:
- Locations should have different meaning at different story points
- Character transformation changes how they perceive and experience a space
- The best locations evolve alongside the character arc
- Return visits to locations show character growth
- Thematic significance should deepen and shift over time
- Consider how THIS place means different things in Act 1 vs. Act 3

When creating thematic significance:
- Show how location meaning shifts through the story
- Connect location evolution to character arc
- Consider if characters return here and what's different
- Track how thematic significance deepens over time
- Show transformation through changing perception of space
- Make location a marker of character growth"""

    def propose_thematic(
        self,
        location_name: str,
        location_type: str,
        physical_description: str,
        atmosphere: str,
        thematic_question: str,
        key_scenes: list[str],
    ) -> LocationThematicProposal:
        """Propose thematic significance based on evolution."""
        prompt = f"""Define the thematic significance for this location emphasizing EVOLUTION:

LOCATION NAME: {location_name}
LOCATION TYPE: {location_type}
PHYSICAL DESCRIPTION: {physical_description}
ATMOSPHERE: {atmosphere}
THEMATIC QUESTION: {thematic_question}
KEY SCENES: {', '.join(key_scenes)}

Design thematic significance that:
- Shows how location meaning shifts through story
- Connects location evolution to character arc
- Considers different meanings at different story points
- Shows transformation through changing perception
- Deepens thematic significance over time
- Makes location a marker of character growth

If characters visit multiple times, show how meaning changes.

Provide a proposal matching LocationThematicProposal schema."""

        return self.invoke_structured(prompt, LocationThematicProposal, max_tokens=8000)

    def critique_thematic(
        self,
        proposal: LocationThematicProposal,
        location_type: str,
        thematic_question: str,
    ) -> LocationThematicCritique:
        """Critique another agent's thematic proposal."""
        prompt = f"""Critique this thematic significance from an EVOLUTION perspective:

TARGET AGENT: {proposal.agent_name}
LOCATION TYPE: {location_type}
THEMATIC QUESTION: {thematic_question}

THEMATIC SIGNIFICANCE: {proposal.thematic_significance}
KEY SCENES: {proposal.key_scenes}
REASONING: {proposal.reasoning}

Evaluate:
1. Does it show how location meaning shifts over time?
2. Is location evolution connected to character arc?
3. Does it track thematic deepening through story?
4. Does it show transformation through perception changes?
5. Is the location a marker of character growth?

Provide a critique matching LocationThematicCritique schema."""

        return self.invoke_structured(prompt, LocationThematicCritique, max_tokens=8000)

    def vote(
        self,
        proposals: list[LocationThematicProposal],
        location_type: str,
        thematic_question: str,
    ) -> LocationThematicVote:
        """Vote for the best thematic significance."""
        proposals_text = "\n\n".join([
            f"PROPOSAL {i} by {p.agent_name}:\n"
            f"  Significance: {p.thematic_significance}\n"
            f"  Key Scenes: {p.key_scenes}\n"
            f"  Reasoning: {p.reasoning}"
            for i, p in enumerate(proposals)
        ])

        prompt = f"""Vote for the BEST thematic significance from an evolution perspective.

LOCATION TYPE: {location_type}
THEMATIC QUESTION: {thematic_question}

PROPOSALS:
{proposals_text}

Which proposal best shows how location meaning evolves through the story?
You CANNOT vote for your own proposal.

Provide a vote matching LocationThematicVote schema."""

        return self.invoke_structured(prompt, LocationThematicVote, max_tokens=8000)
