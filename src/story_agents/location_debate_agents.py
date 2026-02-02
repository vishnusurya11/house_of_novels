"""
Location Debate Agents for Step 3A: Location Generation.

4 agents debate location design with different perspectives:

1. LocationArchitectAgent - Physical structure, layout, architecture
2. LocationAtmosphereAgent - Mood, sensory details, emotional feel
3. LocationNarrativeAgent - Story function, scene suitability, plot relevance
4. LocationAudienceAgent - Immersion, memorability, reader visualization

Each agent:
- Proposes location design based on their methodology
- Critiques other proposals
- Votes for the best proposal
"""

from src.story_agents.base_story_agent import BaseStoryAgent
from src.story_schemas import (
    LocationProposal,
    LocationCritique,
    LocationVote,
)


# =============================================================================
# Location Debate Agents
# =============================================================================

class LocationArchitectAgent(BaseStoryAgent):
    """
    Focuses on physical structure, layout, and architectural coherence.

    Core beliefs:
    - Locations must have LOGICAL physical structure
    - Architecture should reflect the world's technology/culture
    - Layout affects how scenes can unfold
    - Details should enable mental mapping
    """

    METHODOLOGY_NAME = "Architectural Design"
    METHODOLOGY_SOURCE = "Physical world-building and spatial logic"
    CORE_BELIEFS = [
        "Locations must have LOGICAL physical structure",
        "Architecture reflects culture, history, and technology",
        "Layout enables or constrains character movement",
        "Readers need enough detail to mentally map the space",
        "Form follows function - buildings serve purposes",
    ]

    @property
    def name(self) -> str:
        return "LOCATION_ARCHITECT"

    @property
    def role(self) -> str:
        return "Location Architect"

    @property
    def system_prompt(self) -> str:
        return """You are a location architect who designs physically coherent spaces.

Your core beliefs:
- Locations need LOGICAL physical structure (entrances, exits, rooms, terrain)
- Architecture should reflect the culture and technology level
- Layout affects how scenes unfold (chases, conversations, reveals)
- Provide enough detail for readers to mentally map the space
- Form follows function - why does this place exist?

When designing locations:
- Consider how people move through the space
- Think about sight lines, cover, exits
- Include architectural details that reflect the world
- Make the space functional for its intended purpose"""

    def propose_location(
        self,
        location_source: str,
        setting_prompt: str,
        story_context: str,
    ) -> LocationProposal:
        """Propose location design based on architectural analysis."""
        prompt = f"""Design a location based on ARCHITECTURAL principles:

LOCATION SOURCE: {location_source}

WORLD SETTING: {setting_prompt}

STORY CONTEXT: {story_context}

Design a location with:
1. Clear physical structure (entrances, layout, key areas)
2. Architecture reflecting the world's culture/technology
3. Functional spaces that serve story purposes
4. Details enabling mental mapping

Your methodology focus is "architecture" - physical structure and spatial logic.

Provide a proposal matching LocationProposal schema."""

        return self.invoke_structured(prompt, LocationProposal, max_tokens=1500)

    def critique_proposal(
        self,
        target_agent: str,
        proposal: LocationProposal,
        setting_prompt: str,
    ) -> LocationCritique:
        """Critique from architectural perspective."""
        prompt = f"""Critique this location design from an ARCHITECTURAL perspective:

TARGET AGENT: {target_agent}

PROPOSAL:
- Name: {proposal.name}
- Type: {proposal.type}
- Description: {proposal.description}
- Key Features: {', '.join(proposal.key_features)}
- Reasoning: {proposal.reasoning}

WORLD SETTING: {setting_prompt}

Evaluate:
1. Is the physical structure logical and coherent?
2. Does the architecture fit the world's culture/technology?
3. Is the layout functional for scenes?
4. Can readers mentally map this space?

Provide a critique matching LocationCritique schema."""

        return self.invoke_structured(prompt, LocationCritique, max_tokens=600)

    def vote_for_best(
        self,
        proposals: list[LocationProposal],
        setting_prompt: str,
    ) -> LocationVote:
        """Vote for best design from architectural perspective."""
        proposals_text = "\n\n".join([
            f"PROPOSAL by {p.agent_name}:\n"
            f"  Name: {p.name}\n"
            f"  Type: {p.type}\n"
            f"  Description: {p.description[:150]}...\n"
            f"  Features: {', '.join(p.key_features[:3])}"
            for p in proposals
        ])

        prompt = f"""Vote for the most ARCHITECTURALLY SOUND location design.

PROPOSALS:
{proposals_text}

Which proposal has the best physical structure and architectural coherence?
You CANNOT vote for your own proposal (LOCATION_ARCHITECT).

Provide a vote matching LocationVote schema."""

        return self.invoke_structured(prompt, LocationVote, max_tokens=300)


class LocationAtmosphereAgent(BaseStoryAgent):
    """
    Focuses on mood, sensory details, and emotional atmosphere.

    Core beliefs:
    - Atmosphere is created through sensory details
    - Mood should support the scene's emotional tone
    - Smells, sounds, textures make places feel REAL
    - The best locations evoke visceral responses
    """

    METHODOLOGY_NAME = "Atmospheric Design"
    METHODOLOGY_SOURCE = "Sensory immersion and mood creation"
    CORE_BELIEFS = [
        "Atmosphere is created through sensory details",
        "Mood should support the scene's emotional tone",
        "Smells, sounds, textures make places feel REAL",
        "Lighting and weather affect perception",
        "The best locations evoke visceral responses",
    ]

    @property
    def name(self) -> str:
        return "LOCATION_ATMOSPHERE"

    @property
    def role(self) -> str:
        return "Atmosphere Designer"

    @property
    def system_prompt(self) -> str:
        return """You are an atmosphere designer who creates immersive sensory experiences.

Your core beliefs:
- Atmosphere comes from SENSORY DETAILS - what you see, hear, smell, feel
- Mood should support the emotional tone of scenes set here
- Specific details (the creak of floorboards, the smell of damp stone) make places real
- Lighting, weather, and temperature affect how readers experience a space
- The best locations create visceral, emotional responses

When designing locations:
- Layer multiple senses (not just visual)
- Consider time of day, weather, season
- What sounds fill this space? What smells linger?
- How does it FEEL to be here emotionally?"""

    def propose_location(
        self,
        location_source: str,
        setting_prompt: str,
        story_context: str,
    ) -> LocationProposal:
        """Propose location design based on atmospheric analysis."""
        prompt = f"""Design a location based on ATMOSPHERIC principles:

LOCATION SOURCE: {location_source}

WORLD SETTING: {setting_prompt}

STORY CONTEXT: {story_context}

Design a location with:
1. Rich sensory details (sounds, smells, textures, temperature)
2. Mood that supports emotional scenes
3. Atmospheric elements (lighting, weather, time)
4. Visceral, emotional impact

Your methodology focus is "atmosphere" - sensory details and mood.

Provide a proposal matching LocationProposal schema."""

        return self.invoke_structured(prompt, LocationProposal, max_tokens=1500)

    def critique_proposal(
        self,
        target_agent: str,
        proposal: LocationProposal,
        setting_prompt: str,
    ) -> LocationCritique:
        """Critique from atmospheric perspective."""
        prompt = f"""Critique this location design from an ATMOSPHERIC perspective:

TARGET AGENT: {target_agent}

PROPOSAL:
- Name: {proposal.name}
- Type: {proposal.type}
- Atmosphere: {proposal.atmosphere}
- Sensory Details: {proposal.sensory_details}
- Reasoning: {proposal.reasoning}

WORLD SETTING: {setting_prompt}

Evaluate:
1. Are the sensory details rich and specific?
2. Does the atmosphere create emotional impact?
3. Are multiple senses engaged (not just visual)?
4. Would a reader feel transported to this place?

Provide a critique matching LocationCritique schema."""

        return self.invoke_structured(prompt, LocationCritique, max_tokens=600)

    def vote_for_best(
        self,
        proposals: list[LocationProposal],
        setting_prompt: str,
    ) -> LocationVote:
        """Vote for best design from atmospheric perspective."""
        proposals_text = "\n\n".join([
            f"PROPOSAL by {p.agent_name}:\n"
            f"  Name: {p.name}\n"
            f"  Atmosphere: {p.atmosphere}\n"
            f"  Sensory: {p.sensory_details[:100]}..."
            for p in proposals
        ])

        prompt = f"""Vote for the most ATMOSPHERICALLY IMMERSIVE location design.

PROPOSALS:
{proposals_text}

Which proposal creates the best sensory experience and emotional atmosphere?
You CANNOT vote for your own proposal (LOCATION_ATMOSPHERE).

Provide a vote matching LocationVote schema."""

        return self.invoke_structured(prompt, LocationVote, max_tokens=300)


class LocationNarrativeAgent(BaseStoryAgent):
    """
    Focuses on story function, scene suitability, and plot relevance.

    Core beliefs:
    - Locations must SERVE the narrative
    - Setting can reflect/contrast character states
    - Key scenes need locations that enable them
    - Location details can foreshadow or reveal
    """

    METHODOLOGY_NAME = "Narrative Function"
    METHODOLOGY_SOURCE = "Story structure and setting as character"
    CORE_BELIEFS = [
        "Locations must SERVE the narrative",
        "Setting can reflect or contrast character states",
        "Key scenes need locations that enable them",
        "Location details can foreshadow or reveal plot points",
        "The right setting elevates scene impact",
    ]

    @property
    def name(self) -> str:
        return "LOCATION_NARRATIVE"

    @property
    def role(self) -> str:
        return "Narrative Designer"

    @property
    def system_prompt(self) -> str:
        return """You are a narrative designer who creates locations that serve the story.

Your core beliefs:
- Every location must SERVE THE NARRATIVE - no random settings
- Settings can reflect character psychology (a shattered person in a crumbling place)
- Settings can contrast character state (hope in a dark place)
- Location details can foreshadow future events or reveal backstory
- The right setting transforms a good scene into a memorable one

When designing locations:
- Ask: What scenes will happen here? What do they need?
- Consider how setting can amplify emotional moments
- Include details that could be used for plot purposes
- Make the location feel essential, not interchangeable"""

    def propose_location(
        self,
        location_source: str,
        setting_prompt: str,
        story_context: str,
    ) -> LocationProposal:
        """Propose location design based on narrative function."""
        prompt = f"""Design a location based on NARRATIVE FUNCTION principles:

LOCATION SOURCE: {location_source}

WORLD SETTING: {setting_prompt}

STORY CONTEXT: {story_context}

Design a location with:
1. Clear narrative purpose - what scenes will happen here?
2. Elements that can amplify emotional moments
3. Details useful for plot (hiding places, reveals, obstacles)
4. Connection to character psychology or theme

Your methodology focus is "narrative function" - how the location serves the story.

Provide a proposal matching LocationProposal schema."""

        return self.invoke_structured(prompt, LocationProposal, max_tokens=1500)

    def critique_proposal(
        self,
        target_agent: str,
        proposal: LocationProposal,
        setting_prompt: str,
    ) -> LocationCritique:
        """Critique from narrative perspective."""
        prompt = f"""Critique this location design from a NARRATIVE perspective:

TARGET AGENT: {target_agent}

PROPOSAL:
- Name: {proposal.name}
- Type: {proposal.type}
- Description: {proposal.description}
- Key Features: {', '.join(proposal.key_features)}
- Reasoning: {proposal.reasoning}

WORLD SETTING: {setting_prompt}

Evaluate:
1. Does this location serve a clear narrative purpose?
2. Can important scenes effectively happen here?
3. Do details support plot needs (reveals, conflict, emotion)?
4. Does the setting connect to themes or character psychology?

Provide a critique matching LocationCritique schema."""

        return self.invoke_structured(prompt, LocationCritique, max_tokens=600)

    def vote_for_best(
        self,
        proposals: list[LocationProposal],
        setting_prompt: str,
    ) -> LocationVote:
        """Vote for best design from narrative perspective."""
        proposals_text = "\n\n".join([
            f"PROPOSAL by {p.agent_name}:\n"
            f"  Name: {p.name}\n"
            f"  Type: {p.type}\n"
            f"  Features: {', '.join(p.key_features)}\n"
            f"  Reasoning: {p.reasoning[:100]}..."
            for p in proposals
        ])

        prompt = f"""Vote for the most NARRATIVELY EFFECTIVE location design.

PROPOSALS:
{proposals_text}

Which proposal best serves the story's narrative needs?
You CANNOT vote for your own proposal (LOCATION_NARRATIVE).

Provide a vote matching LocationVote schema."""

        return self.invoke_structured(prompt, LocationVote, max_tokens=300)


class LocationAudienceAgent(BaseStoryAgent):
    """
    Focuses on immersion, memorability, and reader visualization.

    Core beliefs:
    - Readers need to VISUALIZE the space quickly
    - Memorable locations stick in readers' minds
    - Relatable details build connection
    - Iconic locations become part of story identity
    """

    METHODOLOGY_NAME = "Audience Immersion"
    METHODOLOGY_SOURCE = "Reader psychology and visualization"
    CORE_BELIEFS = [
        "Readers need to VISUALIZE the space quickly",
        "Memorable locations stick in readers' minds",
        "Relatable details build connection",
        "Too much detail overwhelms; too little underwhelms",
        "Iconic locations become part of story identity",
    ]

    @property
    def name(self) -> str:
        return "LOCATION_AUDIENCE"

    @property
    def role(self) -> str:
        return "Audience Immersion Expert"

    @property
    def system_prompt(self) -> str:
        return """You are an audience immersion expert who designs locations readers will remember.

Your core beliefs:
- Readers need to VISUALIZE a location quickly - give them clear mental anchors
- Memorable locations become iconic (Hogwarts, The Shire, Bag End)
- Balance detail - enough to immerse, not so much it overwhelms
- Relatable elements (a cluttered desk, a creaky stair) connect readers to fantasy spaces
- The best locations readers can picture instantly and remember forever

When designing locations:
- What's the ONE image readers should see first?
- What makes this place memorable and unique?
- Include at least one relatable, grounding detail
- Names should be evocative and easy to remember"""

    def propose_location(
        self,
        location_source: str,
        setting_prompt: str,
        story_context: str,
    ) -> LocationProposal:
        """Propose location design based on audience immersion."""
        prompt = f"""Design a location based on AUDIENCE IMMERSION principles:

LOCATION SOURCE: {location_source}

WORLD SETTING: {setting_prompt}

STORY CONTEXT: {story_context}

Design a location with:
1. Clear visual anchors readers can picture immediately
2. Memorable, iconic qualities that stick in the mind
3. Balanced detail (immersive but not overwhelming)
4. At least one relatable, grounding element

Your methodology focus is "audience immersion" - reader visualization and memorability.

Provide a proposal matching LocationProposal schema."""

        return self.invoke_structured(prompt, LocationProposal, max_tokens=1500)

    def critique_proposal(
        self,
        target_agent: str,
        proposal: LocationProposal,
        setting_prompt: str,
    ) -> LocationCritique:
        """Critique from audience immersion perspective."""
        prompt = f"""Critique this location design from an AUDIENCE IMMERSION perspective:

TARGET AGENT: {target_agent}

PROPOSAL:
- Name: {proposal.name}
- Type: {proposal.type}
- Description: {proposal.description}
- Key Features: {', '.join(proposal.key_features)}

WORLD SETTING: {setting_prompt}

Evaluate:
1. Can readers visualize this location quickly and clearly?
2. Is it memorable? Will readers remember it later?
3. Is the name evocative and easy to recall?
4. Is detail balanced (not too sparse, not overwhelming)?

Provide a critique matching LocationCritique schema."""

        return self.invoke_structured(prompt, LocationCritique, max_tokens=600)

    def vote_for_best(
        self,
        proposals: list[LocationProposal],
        setting_prompt: str,
    ) -> LocationVote:
        """Vote for best design from audience immersion perspective."""
        proposals_text = "\n\n".join([
            f"PROPOSAL by {p.agent_name}:\n"
            f"  Name: {p.name}\n"
            f"  Description: {p.description[:100]}...\n"
            f"  Features: {', '.join(p.key_features[:2])}"
            for p in proposals
        ])

        prompt = f"""Vote for the most MEMORABLE and IMMERSIVE location design.

PROPOSALS:
{proposals_text}

Which proposal will readers visualize most clearly and remember longest?
You CANNOT vote for your own proposal (LOCATION_AUDIENCE).

Provide a vote matching LocationVote schema."""

        return self.invoke_structured(prompt, LocationVote, max_tokens=300)
