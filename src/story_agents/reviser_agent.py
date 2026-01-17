"""
Reviser Agent - Generic agent that synthesizes critiques and revises content.

Used across all phases to apply critic feedback.
"""

import json
from src.story_agents.base_story_agent import BaseStoryAgent
from src.story_schemas import (
    OutlineSchema,
    CharacterListSchema,
    LocationListSchema,
    NarrativeSchema,
    SceneProseSchema,
)


class ReviserAgent(BaseStoryAgent):
    """Synthesizes critiques and revises content accordingly."""

    @property
    def name(self) -> str:
        return "REVISER"

    @property
    def role(self) -> str:
        return "Editorial Reviser"

    @property
    def system_prompt(self) -> str:
        return """You are an editorial reviser who synthesizes feedback and improves content.

Your expertise:
- Prioritizing critiques by severity
- Making surgical edits that address issues
- Preserving the core vision while improving execution
- Balancing multiple competing suggestions

Revision principles:
1. Address "major" severity issues first
2. Don't over-revise - fix what's broken, preserve what works
3. When critiques conflict, choose the one that serves the story better
4. Maintain consistency with previously established elements
5. Improve clarity without losing voice

When revising:
- Make specific, targeted changes
- Don't introduce new problems while fixing old ones
- Keep the original structure unless fundamentally flawed
- Enhance rather than replace when possible"""

    def revise_outline(self, outline: str, critiques: list[str]) -> OutlineSchema:
        """
        Revise story outline based on critiques.

        Args:
            outline: Current outline JSON
            critiques: List of critique JSON strings

        Returns:
            OutlineSchema with revised outline
        """
        critiques_text = "\n\n".join(f"CRITIQUE {i+1}:\n{c}" for i, c in enumerate(critiques))

        prompt = f"""Revise this story outline based on the critiques provided.

CURRENT OUTLINE:
{outline}

CRITIQUES:
{critiques_text}

Address the most severe issues first. Make targeted improvements while preserving what works.

Maintain the same structure with title, logline, protagonist, antagonist, central_conflict, and acts."""

        return self.invoke_structured(prompt, OutlineSchema, max_tokens=4000)

    def revise_characters(self, characters: str, critiques: list[str],
                          locked_names: list[str] = None) -> CharacterListSchema:
        """
        Revise character profiles based on critiques.

        Args:
            characters: Current characters JSON
            critiques: List of critique JSON strings
            locked_names: List of character names that MUST NOT be changed.
                          These were selected through multi-agent debate.

        Returns:
            Revised characters JSON
        """
        critiques_text = "\n\n".join(f"CRITIQUE {i+1}:\n{c}" for i, c in enumerate(critiques))

        # Build locked names instruction if provided
        if locked_names:
            locked_instruction = f"""
CRITICAL - LOCKED CHARACTER NAMES (DO NOT CHANGE):
The following character names were selected through multi-agent debate and MUST remain unchanged:
{chr(10).join(f'- {name}' for name in locked_names)}

You may revise character descriptions, backstories, motivations, arcs, and other attributes,
but these names are FINAL and must be preserved exactly as shown.
"""
        else:
            locked_instruction = ""

        prompt = f"""Revise these character profiles based on the critiques provided.

CURRENT CHARACTERS:
{characters}

CRITIQUES:
{critiques_text}
{locked_instruction}
Address consistency issues and add missing characters if noted."""

        return self.invoke_structured(prompt, CharacterListSchema, max_tokens=8000)

    def revise_locations(self, locations: str, critiques: list[str]) -> LocationListSchema:
        """
        Revise location profiles based on critiques.

        Args:
            locations: Current locations JSON
            critiques: List of critique JSON strings

        Returns:
            LocationListSchema with revised locations
        """
        critiques_text = "\n\n".join(f"CRITIQUE {i+1}:\n{c}" for i, c in enumerate(critiques))

        prompt = f"""Revise these location profiles based on the critiques provided.

CURRENT LOCATIONS:
{locations}

CRITIQUES:
{critiques_text}

Address consistency issues and add missing locations if noted."""

        return self.invoke_structured(prompt, LocationListSchema, max_tokens=6000)

    def revise_narrative(self, narrative: str, critiques: list[str]) -> NarrativeSchema:
        """
        Revise narrative prose based on critiques.

        Args:
            narrative: Current narrative JSON
            critiques: List of critique JSON strings

        Returns:
            NarrativeSchema with revised narrative
        """
        critiques_text = "\n\n".join(f"CRITIQUE {i+1}:\n{c}" for i, c in enumerate(critiques))

        prompt = f"""Revise this narrative based on the critiques provided.

CURRENT NARRATIVE:
{narrative}

CRITIQUES:
{critiques_text}

Improve style and continuity while preserving the story. Make targeted prose improvements.
Preserve the exact same structure: title, acts with act_number/act_name, scenes with scene_number/location/characters/time/text."""

        return self.invoke_structured(prompt, NarrativeSchema, max_tokens=16000)

    def revise_narrative_structured(
        self,
        narrative: dict,
        critiques: list[str]
    ) -> NarrativeSchema:
        """
        Revise narrative prose based on critiques using structured output.

        Uses LangChain's with_structured_output() to enforce valid NarrativeSchema
        output, preventing parse errors.

        Args:
            narrative: Current narrative as dict with title and acts
            critiques: List of critique JSON strings

        Returns:
            NarrativeSchema - validated Pydantic model
        """
        critiques_text = "\n\n".join(f"CRITIQUE {i+1}:\n{c}" for i, c in enumerate(critiques))

        # Convert narrative dict to readable format for prompt
        narrative_json = json.dumps(narrative, indent=2, ensure_ascii=False)

        prompt = f"""Revise this narrative based on the critiques provided.

CURRENT NARRATIVE:
{narrative_json}

CRITIQUES:
{critiques_text}

Improve style and continuity while preserving the story. Make targeted prose improvements.
Preserve the exact same structure: title, acts with act_number/act_name, scenes with scene_number/location/characters/time/text.
Return the complete revised narrative."""

        # Use 16000 tokens for full narrative revision
        return self.invoke_structured(prompt, NarrativeSchema, max_tokens=16000)

    def revise_scene(
        self,
        scene: dict,
        critique_text: str,
        characters_context: str = "",
        locations_context: str = ""
    ) -> SceneProseSchema:
        """
        Revise a single scene based on critique feedback.

        Used as fallback when full-narrative revision exceeds token limits.

        Args:
            scene: Single scene dict with scene_number, location, characters, time, text
            critique_text: Relevant critique feedback for this scene
            characters_context: Character profiles JSON for reference
            locations_context: Location profiles JSON for reference

        Returns:
            SceneProseSchema with revised scene text
        """
        scene_json = json.dumps(scene, indent=2, ensure_ascii=False)

        # Truncate context to keep prompt manageable
        chars_ctx = characters_context[:2000] if characters_context else "Not provided"
        locs_ctx = locations_context[:1000] if locations_context else "Not provided"

        prompt = f"""Revise this scene based on the critique feedback.

CURRENT SCENE:
{scene_json}

CRITIQUE FEEDBACK:
{critique_text}

CHARACTER CONTEXT:
{chars_ctx}

LOCATION CONTEXT:
{locs_ctx}

REVISION GUIDELINES:
- Fix any style issues (voice, dialogue, show-don't-tell)
- Fix any continuity errors with character/location details
- Maintain the same scene_number, location, characters, and time
- Improve prose quality while preserving story intent
- Keep the scene approximately the same length

Return the revised scene with improved prose."""

        return self.invoke_structured(prompt, SceneProseSchema, max_tokens=4000)
