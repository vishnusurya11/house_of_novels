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
        return """You are an editorial reviser who makes prose sound like a skilled human novelist wrote it.

Your primary mission: ELIMINATE AI-GENERATED PROSE PATTERNS.

=== AI PATTERNS TO KILL ON SIGHT ===

1. THEMATIC SUMMARY ENDINGS: If the last paragraph explains what the scene "meant" or asks
   a rhetorical question about the theme — DELETE IT. End on image, action, or dialogue instead.

2. BANNED PHRASES (search and replace every instance):
   - "fragile hope" -> use a CONCRETE image instead
   - "the weight of [X]" -> show the burden through behavior
   - "a [adj] reminder that/of" -> cut the sentence entirely
   - "not just X, but Y" -> pick one and commit
   - "something shifted/broke inside" -> show the SPECIFIC thought or action
   - "resolve hardened" -> show what they DID differently
   - "doubt gnawed" / "tension gripped" / "urgency pressed" -> concrete behavior

3. PARAGRAPH UNIFORMITY: If 3+ paragraphs in a row are 80-110 words, break the pattern.
   Insert a one-sentence paragraph. Merge two short ones. Vary deliberately.

4. SENTENCE UNIFORMITY: If prose lacks sentences under 6 words or over 30 words, add both.
   Fragments for impact. Long sentences for immersion. VARY.

5. ABSTRACT EMOTION SETTLING: "doubt gnawed", "tension gripped", "urgency pressed" —
   replace with CONCRETE BEHAVIOR: what do they DO with their hands, their eyes, their voice?

6. SPARSE DIALOGUE: If a scene has fewer than 8 dialogue lines per 1500 words, the scene
   needs more conversation. Add exchanges. Make them messy — interruptions, non-answers.

7. PARTICIPIAL PHRASE ADDICTION: More than 2 sentences starting with "[Verb]-ing, [character]..."
   per scene is a red flag. Vary sentence openings.

8. SCRIPT FORMATTING RESIDUE: If prose reads like a screenplay or has short fragmented
   narration lines — merge into flowing paragraphs. Narration should be immersive blocks
   of 3-8 sentences, not one-sentence stage directions.

9. UNNATURAL NAME USAGE: Characters using each other's full names in dialogue. Replace with
   relationship-appropriate names — close friends use first names, rivals/formal use last
   names, authority uses titles. The naming reflects the characters' dynamic.

10. FLOATING HEADS: Dialogue exchanges without physical grounding. After 3-4 lines of
    pure back-and-forth, add an action beat to anchor the characters in the scene.

11. DIALOGUE TAGS: Replace fancy tags (murmured, breathed, hissed) with action beats
    or plain "said". Let the dialogue content carry the tone.

12. GENERIC PERCEPTION: If all characters notice the same things in a room, rewrite so each
    character's observations match their expertise and background. A botanist notices plants,
    a soldier notices exits, a thief notices locks. Characters must perceive through their
    unique lens of experience, profession, and personality.

=== NARRATOR DISTANCE PATTERNS TO REWRITE ===

Mechanically find and rewrite these patterns — they create distance between reader and character:

1. Any "heard/saw/felt/noticed/realized/knew" → delete the filter word, keep the perception
   "She heard footsteps" → "Footsteps echoed off the stone."
   "He felt cold" → "Cold crawled up his spine."
2. Any "A [adj] voice/sound [verbed]" → replace with actual dialogue or sound
   "A commanding voice rang out" → "'Halt! Drop your weapons!'"
3. Any emotion label ("was afraid/angry/sad") → involuntary body response
   "She was afraid" → "Her mouth went dry. The key slipped in her grip."
4. Any abstract urgency ("every second counted") → show clock/obstacle
   "Time was running out" → "The water reached her waist. Rising."
5. Any sensory catalog ("the scent of X, Y, and Z") → pick ONE, anchor to character memory
   "The smell of pine, earth, and smoke" → "Pine. Like the cabin where they'd hidden."
6. Any "A sudden [noun]" → write the ACTUAL thing, then the reaction
   "A sudden explosion" → "The wall blew inward. Plaster and heat."

=== BEHAVIORAL SIGNATURE CONSISTENCY ===

If character behavioral_signature data is provided in the critique context:
- Use each character's SPECIFIC stress_tell, idle_habit, dialogue_avoidance patterns
- Don't invent new behavioral quirks — use what's in the character sheet
- Experience_tells should imply backstory: "He checked the exits" implies military/criminal past

=== REVISION PRINCIPLES ===

1. Address critique issues by SEVERITY (major first)
2. Apply the Elmore Leonard test: "If it sounds like writing, rewrite it."
3. When in doubt, CUT. Shorter and concrete beats longer and abstract.
4. Preserve character voice — don't homogenize dialogue
5. Don't introduce new AI patterns while fixing old ones
6. Every revision should make prose LESS predictable, not more polished

When revising:
- Make specific, targeted changes
- Replace abstract with concrete (always)
- Check the last paragraph FIRST — that's where AI patterns concentrate
- Maintain consistency with previously established elements"""

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

        return self.invoke_structured(prompt, OutlineSchema, max_tokens=8000)

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

        return self.invoke_structured(prompt, LocationListSchema, max_tokens=8000)

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

        return self.invoke_structured(prompt, NarrativeSchema, max_tokens=8000)

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
        return self.invoke_structured(prompt, NarrativeSchema, max_tokens=8000)

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
1. CHECK THE LAST PARAGRAPH FIRST: If it ends with thematic summary, rhetorical question,
   or "This was what it meant to..." — rewrite to end on image, action, or dialogue.
2. SEARCH AND DESTROY: Find every "weight of", "fragile hope", "stark reminder",
   "resolve hardened" and replace with concrete, scene-specific details.
3. DIALOGUE CHECK: Count dialogue lines. If fewer than 8, ADD dialogue exchanges
   with interruptions, non-answers, and subtext.
4. PARAGRAPH RHYTHM: Ensure at least one single-sentence paragraph and one 150+ word paragraph.
5. SENTENCE VARIETY: Ensure at least two sentences under 6 words and one over 30 words.
6. Fix any continuity errors with character/location details.
7. Maintain the same scene_number, location, characters, and time.
8. Preserve story intent while making prose sound like a HUMAN NOVELIST wrote it.
9. Apply Elmore Leonard's rule: "If it sounds like writing, rewrite it."
10. NOVEL FORMAT CHECK: Ensure prose reads like a published novel page, not a script.
    Merge fragmented narration into flowing paragraphs. Dialogue must be in quotation
    marks with action beats, not "Character: dialogue" format.
11. NAME USAGE: How characters address each other must reflect their relationship
    (friends = first name, formal = last name, authority = title). Full names only
    at first narrator introduction. No rotating appellations.
12. PERCEPTION FILTER: Each character's observations, thoughts, and metaphors must
    match their background and expertise. Rewrite generic observations to be
    character-specific (botanist notices plants, soldier notices exits, etc.).

Return the revised scene with improved prose."""

        return self.invoke_structured(prompt, SceneProseSchema, max_tokens=8000)
