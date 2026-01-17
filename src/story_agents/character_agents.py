"""
Phase 2 Agents: Character and Location Building

- CharacterBuilderAgent: Creates detailed character profiles
- LocationBuilderAgent: Creates detailed location profiles
- ConsistencyCriticAgent: Checks for contradictions and gaps
"""

from src.story_agents.base_story_agent import BaseStoryAgent
from src.story_schemas import CharacterListSchema, LocationListSchema, CritiqueSchema


class CharacterBuilderAgent(BaseStoryAgent):
    """Creates detailed character profiles from outline."""

    @property
    def name(self) -> str:
        return "CHARACTER_BUILDER"

    @property
    def role(self) -> str:
        return "Character Designer"

    @property
    def system_prompt(self) -> str:
        return """You are a character designer who creates vivid, consistent characters.

Your expertise:
- Physical description that reflects personality
- Backstory that motivates current behavior
- Personality traits that drive conflict
- Character arcs that show growth

For each character, define:
1. Full name (fitting the setting)
2. Gender and age
3. Physical appearance (height, build, hair, eyes, distinguishing features)
4. Typical clothing/style
5. 3-5 personality traits
6. Brief backstory (2-3 sentences)
7. Core motivation
8. Role in story (protagonist/antagonist/supporting)
9. Character arc (how they change)

CRITICAL RULES - UNIQUE INDIVIDUALS ONLY:
- Every character MUST be a unique individual with distinct physical features
- If multiple characters share the same role (e.g., "Community Member"), number them: "Community Member #1", "Community Member #2"
- Each character MUST have COMPLETELY DIFFERENT physical descriptions (different height, hair, eyes, build, clothing)
- NO TWO CHARACTERS can share the same physical description
- Each character must be distinct enough to generate a unique portrait image
- Generic group descriptions like "various villagers" or "the crowd" are FORBIDDEN

Guidelines:
- Make descriptions specific, not generic
- Physical traits should hint at personality/history
- Motivations should connect to the central conflict
- Ensure diversity in character types
- Avoid cliches unless subverting them"""

    def build_characters(self, outline: str, setting: str,
                          max_characters: int = 8,
                          predefined_names: list[dict] = None) -> CharacterListSchema:
        """
        Build character profiles from outline.

        Args:
            outline: The story outline JSON
            setting: The microsetting description
            max_characters: Maximum number of character profiles to create
            predefined_names: Optional list of pre-generated names from debate.
                             Each dict has: role, character_type, old_name, final_name,
                             first_initial, last_initial

        Returns:
            JSON array of character profiles
        """
        # Build names instruction based on whether we have predefined names
        if predefined_names:
            # Group names by character type for clarity
            protagonist_names = [n for n in predefined_names if n.get("character_type") == "protagonist"]
            antagonist_names = [n for n in predefined_names if n.get("character_type") == "antagonist"]
            supporting_names = [n for n in predefined_names if n.get("character_type") == "supporting"]

            names_instruction = """USE THESE EXACT CHARACTER NAMES (from multi-agent debate):

PROTAGONIST:
"""
            for n in protagonist_names:
                names_instruction += f"- {n['final_name']} (from role: {n['role']})\n"

            names_instruction += "\nANTAGONIST:\n"
            for n in antagonist_names:
                names_instruction += f"- {n['final_name']} (from role: {n['role']})\n"

            if supporting_names:
                names_instruction += "\nSUPPORTING CAST:\n"
                for n in supporting_names:
                    names_instruction += f"- {n['final_name']} (from role: {n['role']})\n"

            names_instruction += """
CRITICAL: You MUST use these EXACT names for each character. Do NOT modify, shorten, or substitute them.
Match each name to the corresponding character in the outline by their role/description."""
        else:
            names_instruction = "Generate appropriate names for each character that fit the setting."

        prompt = f"""Based on this story outline and setting, create detailed profiles for the main characters.

OUTLINE:
{outline}

SETTING:
{setting}

CHARACTER NAMES:
{names_instruction}

CONSTRAINTS:
- Create profiles for MAXIMUM {max_characters} characters
- Prioritize: 1 protagonist, 1 antagonist, then key supporting cast
- If the outline mentions more characters, consolidate minor ones or skip unnamed extras
- Focus on depth over breadth

CRITICAL - UNIQUE INDIVIDUALS ONLY:
- Every character MUST be a unique individual with completely distinct physical features
- If multiple characters share roles, NUMBER them (e.g., "Community Member #1", "Community Member #2")
- Each character MUST have DIFFERENT: height, hair color, eye color, build, clothing, distinguishing features
- NO duplicate or similar descriptions - each character needs a unique visual identity
- Each profile must describe ONE specific person who could be drawn as a distinct portrait

Output as JSON array:

{{
  "characters": [
    {{
      "name": "Full Name",
      "gender": "male/female/non-binary/other",
      "age": "age or range",
      "physical": {{
        "height": "tall/average/short + specifics",
        "build": "body type",
        "hair_color": "color and style",
        "eye_color": "color",
        "distinguishing_features": "scars, tattoos, unique traits"
      }},
      "clothing": "typical attire description",
      "personality_traits": ["trait1", "trait2", "trait3"],
      "backstory": "2-3 sentence background",
      "motivation": "what drives them",
      "role_in_story": "protagonist/antagonist/supporting",
      "arc": "how they change through the story"
    }}
  ]
}}

Create profiles that:
- Fit the setting's atmosphere
- Support the story's themes
- Have clear visual distinctiveness
- Show internal contradictions that make them interesting

Remember: Maximum {max_characters} character profiles. Quality over quantity."""

        return self.invoke_structured(prompt, CharacterListSchema, max_tokens=8000)

    def revise_characters(self, characters: str, critiques: list[str]) -> CharacterListSchema:
        """Revise character profiles based on critiques."""
        critiques_text = "\n\n".join(f"CRITIQUE {i+1}:\n{c}" for i, c in enumerate(critiques))

        prompt = f"""Revise these character profiles based on the critiques:

CURRENT CHARACTERS:
{characters}

CRITIQUES:
{critiques_text}

Address each issue while maintaining character essence. Output the complete revised character list."""

        return self.invoke_structured(prompt, CharacterListSchema, max_tokens=8000)


class LocationBuilderAgent(BaseStoryAgent):
    """Creates detailed location profiles from outline."""

    @property
    def name(self) -> str:
        return "LOCATION_BUILDER"

    @property
    def role(self) -> str:
        return "World Builder"

    @property
    def system_prompt(self) -> str:
        return """You are a world builder who creates immersive, vivid locations.

Your expertise:
- Visual and sensory description
- Atmosphere and mood creation
- Environmental storytelling
- Location as character

For each location, define:
1. Name (evocative, fitting the setting)
2. Type (city, forest, building, etc.)
3. Visual description (2-3 sentences)
4. Atmosphere/mood
5. 3-5 key features
6. Sensory details (sounds, smells, textures)
7. Connection to story (why this location matters)

Guidelines:
- Locations should reflect the story's themes
- Include details that could become plot-relevant
- Mix beauty with danger or comfort with unease
- Consider how time of day/weather affects the space
- Make each location distinct and memorable"""

    def build_locations(self, outline: str, setting: str,
                         max_locations: int = 6) -> LocationListSchema:
        """
        Build location profiles from outline.

        Args:
            outline: The story outline JSON
            setting: The microsetting description
            max_locations: Maximum number of location profiles to create

        Returns:
            LocationListSchema with location profiles
        """
        prompt = f"""Based on this story outline and setting, create detailed profiles for the key locations.

OUTLINE:
{outline}

SETTING:
{setting}

CONSTRAINT: Create profiles for MAXIMUM {max_locations} locations.
- Prioritize locations central to key scenes
- Combine similar/nearby locations if needed
- Skip generic transitional spaces

For each location include:
- name: Location name
- type: city/forest/building/etc
- description: 2-3 sentence visual description
- atmosphere: mood and feeling
- key_features: list of 3-5 notable features
- sensory_details: sounds, smells, textures present
- connection_to_story: why this location matters to the plot

Create locations that:
- Reflect the microsetting's unique qualities
- Support the emotional beats of scenes set there
- Have enough detail for immersive writing
- Feel lived-in and believable

Remember: Maximum {max_locations} location profiles. Focus on key story locations."""

        return self.invoke_structured(prompt, LocationListSchema, max_tokens=6000)

    def revise_locations(self, locations: str, critiques: list[str]) -> LocationListSchema:
        """Revise location profiles based on critiques."""
        critiques_text = "\n\n".join(f"CRITIQUE {i+1}:\n{c}" for i, c in enumerate(critiques))

        prompt = f"""Revise these location profiles based on the critiques:

CURRENT LOCATIONS:
{locations}

CRITIQUES:
{critiques_text}

Address each issue while maintaining location essence. Output the complete revised location list."""

        return self.invoke_structured(prompt, LocationListSchema, max_tokens=6000)


class ConsistencyCriticAgent(BaseStoryAgent):
    """Checks for contradictions and consistency issues."""

    @property
    def name(self) -> str:
        return "CONSISTENCY_CRITIC"

    @property
    def role(self) -> str:
        return "Continuity Editor"

    @property
    def system_prompt(self) -> str:
        return """You are a continuity editor who catches inconsistencies and gaps.

Your expertise:
- Spotting contradictions in descriptions
- Identifying missing information
- Ensuring internal logic
- Cross-referencing between characters, locations, and outline

When critiquing, check:
1. Character contradictions (traits vs. actions in outline)
2. Location consistency (descriptions match how they're used)
3. Missing characters (mentioned in outline but no profile)
4. Missing locations (scenes set there but no profile)
5. Setting fit (do characters/locations fit the microsetting?)
6. Timeline consistency (ages, backstory timing)
7. Motivation alignment (do stated motivations match outline actions?)

Red flags:
- Character described as "shy" but leads confrontations
- Location described as "isolated" but has crowds
- Missing key characters from scenes
- Backstory dates that don't add up

Be specific about contradictions with exact quotes."""

    def critique(self, outline: str, characters: str, locations: str) -> CritiqueSchema:
        """
        Critique characters and locations for consistency.

        Args:
            outline: The story outline JSON
            characters: Character profiles JSON
            locations: Location profiles JSON

        Returns:
            CritiqueSchema with issues and suggestions
        """
        prompt = f"""Analyze these story elements for consistency issues:

OUTLINE:
{outline}

CHARACTERS:
{characters}

LOCATIONS:
{locations}

Provide your critique with:
- critic_name: "CONSISTENCY_CRITIC"
- issues: List of specific contradictions or gaps (with quotes/references)
- suggestions: List of how to resolve each issue
- severity: "minor", "moderate", or "major"

Check for:
- Characters in scenes but missing profiles
- Locations in scenes but missing profiles
- Trait/action contradictions
- Setting mismatches
- Timeline inconsistencies"""

        return self.invoke_structured(prompt, CritiqueSchema, max_tokens=1500)
