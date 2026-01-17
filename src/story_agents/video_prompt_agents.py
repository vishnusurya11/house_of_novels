"""
Video Prompt Agents - Generate LTX-style screenplay prompts for video shots.

Creates prompts in screenplay format combining:
- Slugline (INT/EXT. LOCATION – TIME – SHOT TYPE)
- Scene description with atmosphere and lighting
- Character descriptions (physical only, NO names)
- Dialogue with parenthetical delivery notes
- Camera movements and directions

Key Features:
- Uses `response_format` for guaranteed structured output
- Tools for retrieving character/location data from codex
- Creator + Critic workflow with revision loop

Based on:
- LTX Prompting Guide: https://ltx.io/model/model-blog/prompting-guide-for-ltx-2
- LTX Studio Blog: https://ltx.studio/blog/how-to-write-a-prompt
"""

import json
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

from src.story_schemas import VideoPromptSchema, VideoPromptCritiqueSchema
from src.config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, DEFAULT_MODEL


# =============================================================================
# Tool Factory Functions - Create tools with codex data closure
# =============================================================================

def create_codex_tools(codex: dict) -> list:
    """
    Create LangChain tools for retrieving character and location data from codex.

    Args:
        codex: The full codex dictionary

    Returns:
        List of tool functions with codex data in closure
    """
    characters = codex.get("story", {}).get("characters", [])
    locations = codex.get("story", {}).get("locations", [])

    @tool
    def get_character_description(character_name: str) -> str:
        """
        Retrieve full physical description and clothing for a character by name.
        Use this to get accurate details for describing characters in video prompts.
        Returns physical appearance, clothing, distinguishing features.

        Args:
            character_name: The character's name (case-insensitive search)
        """
        name_lower = character_name.lower().strip()

        for char in characters:
            if char.get("name", "").lower().strip() == name_lower:
                physical = char.get("physical", {})
                result = {
                    "name": char.get("name"),
                    "gender": char.get("gender", ""),
                    "age": char.get("age", ""),
                    "height": physical.get("height", ""),
                    "build": physical.get("build", ""),
                    "hair_color": physical.get("hair_color", ""),
                    "eye_color": physical.get("eye_color", ""),
                    "distinguishing_features": physical.get("distinguishing_features", ""),
                    "clothing": char.get("clothing", ""),
                    "personality_traits": char.get("personality_traits", []),
                }
                return json.dumps(result, indent=2)

        # Try partial match
        for char in characters:
            if name_lower in char.get("name", "").lower():
                physical = char.get("physical", {})
                result = {
                    "name": char.get("name"),
                    "gender": char.get("gender", ""),
                    "age": char.get("age", ""),
                    "height": physical.get("height", ""),
                    "build": physical.get("build", ""),
                    "hair_color": physical.get("hair_color", ""),
                    "eye_color": physical.get("eye_color", ""),
                    "distinguishing_features": physical.get("distinguishing_features", ""),
                    "clothing": char.get("clothing", ""),
                    "personality_traits": char.get("personality_traits", []),
                }
                return json.dumps(result, indent=2)

        return f"Character '{character_name}' not found in codex. Available characters: {[c.get('name') for c in characters]}"

    @tool
    def get_location_description(location_name: str) -> str:
        """
        Retrieve full description and atmosphere for a location by name.
        Use this to get accurate setting details for video prompts.
        Returns visual description, atmosphere, key features, sensory details.

        Args:
            location_name: The location name (case-insensitive, partial match)
        """
        name_lower = location_name.lower().strip()

        for loc in locations:
            loc_name = loc.get("name", "").lower().strip()
            if loc_name == name_lower or name_lower in loc_name or loc_name in name_lower:
                result = {
                    "name": loc.get("name"),
                    "type": loc.get("type", ""),
                    "description": loc.get("description", ""),
                    "atmosphere": loc.get("atmosphere", ""),
                    "key_features": loc.get("key_features", []),
                    "sensory_details": loc.get("sensory_details", ""),
                }
                return json.dumps(result, indent=2)

        return f"Location '{location_name}' not found in codex. Available locations: {[l.get('name') for l in locations]}"

    @tool
    def list_all_characters() -> str:
        """
        List all character names in the codex.
        Use this to see what characters are available before fetching details.
        """
        names = [c.get("name", "Unknown") for c in characters]
        return f"Available characters: {names}"

    @tool
    def list_all_locations() -> str:
        """
        List all location names in the codex.
        Use this to see what locations are available before fetching details.
        """
        names = [l.get("name", "Unknown") for l in locations]
        return f"Available locations: {names}"

    return [get_character_description, get_location_description, list_all_characters, list_all_locations]


# =============================================================================
# System Prompts
# =============================================================================

VIDEO_CREATOR_SYSTEM_PROMPT = """You are a MASTER screenplay writer and video prompt engineer for LTX/Kling/Runway AI video generation.

Your task is to create prompts in SCREENPLAY FORMAT that combine all visual, audio, and action elements into a cohesive video prompt, integrating the specified visual style throughout.

## OUTPUT FORMAT (LTX Screenplay Style):

```
INT/EXT. LOCATION – TIME – SHOT TYPE
[4-8 sentence scene description paragraph establishing setting, atmosphere, lighting]

[Character action and movement description - use PHYSICAL DESCRIPTIONS not names]

Physical-descriptor character tag (parenthetical delivery note):
"Dialogue line here."

[Camera movement and final visual description]
```

## CRITICAL RULES:

1. **NEVER USE CHARACTER NAMES** - The AI model doesn't know who "Rhea" or "Marcus" is.
   Describe characters by their PHYSICAL APPEARANCE throughout:
   - "A tall woman in her late twenties with flowing auburn hair and emerald eyes"
   - NOT "Rhea stands in the square"

2. **DIALOGUE TAGS USE PHYSICAL DESCRIPTIONS**:
   - "Auburn-haired woman (softly, looking away):" NOT "Woman:" or "Rhea:"
   - "Scarred elder with silver beard (gruffly):" NOT "Old Man:" or "Marcus:"

3. **USE THE TOOLS** - Before writing, fetch:
   - Character descriptions for each character in the shot
   - Location description for the setting

## PROMPT STRUCTURE:

1. **SLUGLINE**: INT/EXT. LOCATION – TIME – SHOT TYPE
   - INT. = Interior, EXT. = Exterior
   - Location from shot data
   - Time: DAY, NIGHT, DAWN, DUSK, etc.
   - Shot type: WIDE, MEDIUM, CLOSE-UP, etc.

2. **SCENE DESCRIPTION** (4-8 sentences, single paragraph):
   - Visual setting with key features from codex
   - Lighting quality and direction
   - Atmosphere (mood, weather, particles)
   - Color palette and textures
   - Ambient sounds (describe what we'd hear)

3. **CHARACTER DESCRIPTION & ACTION**:
   - Physical appearance from codex (gender, age, build, hair, eyes, clothing)
   - Current pose and expression
   - Movement through the shot
   - Emotional state shown through physicality

4. **DIALOGUE** (if present in shot):
   - Physical descriptor as speaker tag
   - Parenthetical for delivery (tone, action while speaking)
   - Dialogue in quotes

5. **CAMERA DIRECTION**:
   - Specific movement: dolly in, pan right, track, crane up, static
   - How the view changes through the shot
   - Final composition

## QUALITY STANDARDS:
- 500-800 words total
- Natural flowing prose (not keyword spam)
- Ultra-specific details: "weathered brown leather jacket with brass buttons" not "leather jacket"
- Present tense throughout
- Match detail level to shot scale (more detail for close-ups)

## VISUAL STYLE INTEGRATION:
- If a visual style is specified (prefix/suffix), integrate it naturally into the prompt
- Style prefix should influence the opening description
- Style suffix should be woven into quality/aesthetic descriptions
- Visual descriptions should match the specified art style aesthetic"""


VIDEO_CRITIC_SYSTEM_PROMPT = """You are a CRITICAL reviewer of LTX video prompts in screenplay format.

Your job is to validate prompts against the original codex data, ensure quality standards, and verify visual style integration.

## USE THE TOOLS to verify:
1. Character descriptions match their codex profiles
2. Location details match the codex location data
3. Physical descriptions are accurate (hair color, eye color, distinguishing features)

## EVALUATION CRITERIA (Score 1-10 each):

1. **SCREENPLAY_FORMAT** (Score 1-10)
   - Does it have a proper slugline (INT/EXT. LOCATION – TIME – SHOT)?
   - Is scene description in paragraph form?
   - Is dialogue properly formatted with physical descriptor tags?
   - Are parentheticals present for delivery notes?

2. **CHARACTER_DESCRIPTION** (Score 1-10)
   - Are physical descriptions accurate to codex?
   - Is clothing consistent with character profile?
   - Are distinguishing features included?
   - Score LOW if character names are used instead of descriptions!

3. **CAMERA_MOVEMENT** (Score 1-10)
   - Are camera directions specific (dolly, pan, track)?
   - Do movements match the shot's camera_movement field?
   - Is the visual progression clear?

4. **ATMOSPHERE_DETAIL** (Score 1-10)
   - Is lighting described (quality, direction, color)?
   - Is mood/atmosphere captured?
   - Are sensory details present (sounds, weather)?
   - Does it match time_of_day from shot data?

5. **DIALOGUE_ACCURACY** (Score 1-10)
   - If dialogue present, does it match the shot's dialogue field?
   - Are speaker tags using physical descriptions?
   - Are parentheticals appropriate for tone/delivery?
   - Score 10 if no dialogue in shot and none in prompt

6. **NO_NAMES** (Score 1-10) - CRITICAL!
   - Score 10 if NO character names appear anywhere
   - Score 1 if ANY character name is used
   - Check both description AND dialogue tags
   - This is a HARD requirement!

## DECISION RULES:
- If ANY score is below 7, mark needs_revision = true
- If no_names_score < 10, DEFINITELY needs_revision = true
- Provide SPECIFIC suggestions referencing codex data

## VISUAL STYLE CHECKING:
- If a visual style was specified, verify the prompt integrates it naturally
- Check that visual descriptions match the art style aesthetic
- Verify style keywords are present in appropriate context"""


# =============================================================================
# Video Prompt Creator Agent
# =============================================================================

class VideoPromptCreatorAgent:
    """
    Creates LTX-style screenplay prompts using tools to fetch codex data.

    Uses LangGraph ReAct agent with:
    - Tools for character/location retrieval from codex
    - response_format for guaranteed structured output (VideoPromptSchema)
    """

    def __init__(self, codex: dict, model: str = DEFAULT_MODEL, temperature: float = 0.7):
        self.model_name = model
        self.temperature = temperature
        self.codex = codex

        self.llm = ChatOpenAI(
            model=model,
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL,
            temperature=temperature,
        )

        self.tools = create_codex_tools(codex)

        # Create ReAct agent with tools AND response_format
        self.agent = create_react_agent(
            model=self.llm,
            tools=self.tools,
            response_format=VideoPromptSchema,
        )

    def create_video_prompt(self, shot_data: dict, scene_context: str = "", visual_style: dict = None) -> VideoPromptSchema:
        """
        Generate an LTX-style screenplay prompt for a shot.

        Args:
            shot_data: Shot dict with all screenplay fields
            scene_context: Additional scene context
            visual_style: Visual style dict with name, prefix, suffix

        Returns:
            VideoPromptSchema with video_prompt and metadata
        """
        shot_json = json.dumps(shot_data, indent=2)

        # Extract style components
        style_info = ""
        if visual_style:
            style_name = visual_style.get("name", "Anime")
            style_prefix = visual_style.get("prefix", "")
            style_suffix = visual_style.get("suffix", "")
            style_info = f"""
## VISUAL STYLE: {style_name}
STYLE PREFIX (integrate naturally): {style_prefix}
STYLE SUFFIX (weave into descriptions): {style_suffix}
"""

        user_prompt = f"""Generate an LTX-style SCREENPLAY VIDEO PROMPT for this shot.

## SHOT DATA:
{shot_json}

## SCENE CONTEXT:
{scene_context if scene_context else "Opening shot of scene."}
{style_info}
## INSTRUCTIONS:

1. FIRST: Use get_character_description tool for EACH character in characters_in_frame
2. SECOND: Use get_location_description tool for the location
3. THIRD: Generate the screenplay-format prompt

## FORMAT TO FOLLOW:

{shot_data.get('int_ext', 'EXT.')} {shot_data.get('location', 'LOCATION')} – {shot_data.get('time_of_day', 'DAY')} – {shot_data.get('shot_size', 'WIDE')} SHOT

[4-8 sentence scene description with lighting, atmosphere, and setting from codex]

[Character actions using PHYSICAL DESCRIPTIONS from tools - NEVER use names]

[If dialogue present, format as:]
Physical-descriptor (parenthetical):
"Dialogue line"

[Camera movement: {shot_data.get('camera_movement', 'STATIC')}]

CRITICAL:
- NEVER use character names - only physical descriptions
- Dialogue tags must use physical descriptors like "Auburn-haired woman (softly):"
- 500-800 words total
- Include ambient sounds and music cues in description
- If visual style provided, integrate style keywords naturally into descriptions"""

        result = self.agent.invoke({
            "messages": [
                {"role": "system", "content": VIDEO_CREATOR_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ]
        })

        return result["structured_response"]

    def revise_video_prompt(
        self,
        original: VideoPromptSchema,
        critique: VideoPromptCritiqueSchema,
        shot_data: dict,
        visual_style: dict = None
    ) -> VideoPromptSchema:
        """
        Revise video prompt based on critic feedback.

        Args:
            original: Original prompt to revise
            critique: Critic's evaluation
            shot_data: Original shot data
            visual_style: Visual style dict with name, prefix, suffix

        Returns:
            Revised VideoPromptSchema
        """
        suggestions = "\n".join(f"- {s}" for s in critique.suggestions)

        # Extract style components
        style_info = ""
        if visual_style:
            style_name = visual_style.get("name", "Anime")
            style_prefix = visual_style.get("prefix", "")
            style_suffix = visual_style.get("suffix", "")
            style_info = f"""
## VISUAL STYLE: {style_name}
REMINDER: Integrate these naturally into descriptions: {style_prefix}
REMINDER: Weave these quality tags into descriptions: {style_suffix}
"""

        prompt = f"""REVISE this video prompt based on critic feedback.

## ORIGINAL VIDEO PROMPT:
{original.video_prompt}

## CRITIC SCORES:
- Screenplay Format: {critique.screenplay_format_score}/10
- Character Description: {critique.character_description_score}/10
- Camera Movement: {critique.camera_movement_score}/10
- Atmosphere Detail: {critique.atmosphere_detail_score}/10
- Dialogue Accuracy: {critique.dialogue_accuracy_score}/10
- No Names (CRITICAL): {critique.no_names_score}/10

## SUGGESTIONS FOR IMPROVEMENT:
{suggestions}

## SHOT DATA (reference):
{json.dumps(shot_data, indent=2)}
{style_info}
FIRST: Use the tools to re-fetch character and location data.
THEN: Create an IMPROVED prompt addressing ALL concerns.

CRITICAL: If no_names_score < 10, remove ALL character names and replace with physical descriptions!
This includes dialogue tags - use "Auburn-haired woman:" not names!
CRITICAL: Ensure visual style is naturally integrated into descriptions."""

        result = self.agent.invoke({
            "messages": [
                {"role": "system", "content": VIDEO_CREATOR_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
        })

        return result["structured_response"]


# =============================================================================
# Video Prompt Critic Agent
# =============================================================================

class VideoPromptCriticAgent:
    """
    Critiques video prompts for accuracy against codex data.

    Uses LangGraph ReAct agent with:
    - Tools for character/location verification from codex
    - response_format for guaranteed structured output (VideoPromptCritiqueSchema)
    """

    def __init__(self, codex: dict, model: str = DEFAULT_MODEL, temperature: float = 0.3):
        self.model_name = model
        self.temperature = temperature
        self.codex = codex

        self.llm = ChatOpenAI(
            model=model,
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL,
            temperature=temperature,
        )

        self.tools = create_codex_tools(codex)

        self.agent = create_react_agent(
            model=self.llm,
            tools=self.tools,
            response_format=VideoPromptCritiqueSchema,
        )

    def critique(
        self,
        video_prompt: VideoPromptSchema,
        shot_data: dict,
        visual_style: dict = None
    ) -> VideoPromptCritiqueSchema:
        """
        Evaluate video prompt for accuracy and quality.

        Args:
            video_prompt: The prompt to critique
            shot_data: Original shot data
            visual_style: Visual style dict with name, prefix, suffix

        Returns:
            VideoPromptCritiqueSchema with scores and suggestions
        """
        # Extract style requirements
        style_check = ""
        if visual_style:
            style_name = visual_style.get("name", "Anime")
            style_prefix = visual_style.get("prefix", "")
            style_suffix = visual_style.get("suffix", "")
            style_check = f"""

## REQUIRED VISUAL STYLE: {style_name}
Expected style prefix elements: {style_prefix}
Expected style suffix keywords: {style_suffix}

CHECK STYLE ADHERENCE:
- Are style prefix elements naturally integrated into descriptions?
- Are style suffix quality tags woven into the prompt?
- Do visual descriptions match the {style_name} aesthetic?
"""

        prompt = f"""CRITICALLY EVALUATE this LTX video prompt.

## VIDEO PROMPT:
{video_prompt.video_prompt}

## SLUGLINE PROVIDED:
{video_prompt.slugline}

## SHOT DATA:
{json.dumps(shot_data, indent=2)}
{style_check}
## INSTRUCTIONS:

1. FIRST: Use get_character_description tool to get ACTUAL character descriptions from codex
2. SECOND: Use get_location_description tool to get ACTUAL location description from codex
3. THIRD: Compare the prompt against the codex data and score

SCORING CRITERIA (1-10 each):

1. SCREENPLAY_FORMAT: Proper slugline, scene description, dialogue format?
2. CHARACTER_DESCRIPTION: Physical descriptions match codex? Accurate clothing?
3. CAMERA_MOVEMENT: Clear directions matching shot's camera_movement ({shot_data.get('camera_movement', 'UNKNOWN')})?
4. ATMOSPHERE_DETAIL: Lighting, mood, weather described? Matches time_of_day ({shot_data.get('time_of_day', 'UNKNOWN')})?
5. DIALOGUE_ACCURACY: If dialogue present, matches shot data? Physical descriptor tags?
6. NO_NAMES: Score 10 if NO character names used, Score 1 if ANY names found!

CRITICAL: Check if character names like {shot_data.get('characters_in_frame', [])} appear ANYWHERE in prompt!
This includes dialogue tags! If names are present, no_names_score MUST be 1!

Set needs_revision=true if ANY score is below 7."""

        result = self.agent.invoke({
            "messages": [
                {"role": "system", "content": VIDEO_CRITIC_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
        })

        return result["structured_response"]


# =============================================================================
# Orchestration Function
# =============================================================================

def generate_video_prompt(
    shot_data: dict,
    codex: dict,
    scene_context: str = "",
    model: str = DEFAULT_MODEL,
    max_revisions: int = 2,
    visual_style: dict = None,
) -> dict:
    """
    Generate an LTX-style video prompt for a shot using creator + critic workflow.

    Uses ReAct agents with tools and guaranteed structured output via response_format.

    Args:
        shot_data: Shot dict with all screenplay fields
        codex: Full codex with characters and locations
        scene_context: Additional scene context
        model: LLM model to use
        max_revisions: Maximum revision cycles (default 2)
        visual_style: Visual style dict with name, prefix, suffix, description

    Returns:
        Dict with:
        - video_prompt: The LTX screenplay-format prompt
        - slugline: INT/EXT. LOCATION – TIME – SHOT
        - camera_movements: List of camera movements
        - dialogue_included: Whether dialogue is present
        - characters_described: Physical descriptions used
        - revision_count: Number of revisions made
        - final_scores: Final critique scores
        - critique_history: All critiques for metadata
    """
    creator = VideoPromptCreatorAgent(codex=codex, model=model)
    critic = VideoPromptCriticAgent(codex=codex, model=model, temperature=0.3)

    shot_num = shot_data.get("shot_number", "?")
    location = shot_data.get("location", "Unknown")
    print(f"      Creating video prompt for shot {shot_num} at {location}...")

    # Initial prompt generation
    current = creator.create_video_prompt(shot_data, scene_context, visual_style)

    critique_history = []
    revision_count = 0

    # Critique-revision loop
    for i in range(max_revisions):
        print(f"        Critique cycle {i + 1}/{max_revisions}...")

        critique = critic.critique(current, shot_data, visual_style)

        critique_dict = {
            "cycle": i + 1,
            "screenplay_format_score": critique.screenplay_format_score,
            "character_description_score": critique.character_description_score,
            "camera_movement_score": critique.camera_movement_score,
            "atmosphere_detail_score": critique.atmosphere_detail_score,
            "dialogue_accuracy_score": critique.dialogue_accuracy_score,
            "no_names_score": critique.no_names_score,
            "overall_score": critique.overall_score,
            "needs_revision": critique.needs_revision,
            "suggestions": critique.suggestions,
        }
        critique_history.append(critique_dict)

        # Check if revision needed
        min_score = min(
            critique.screenplay_format_score,
            critique.character_description_score,
            critique.camera_movement_score,
            critique.atmosphere_detail_score,
            critique.dialogue_accuracy_score,
            critique.no_names_score,
        )

        if not critique.needs_revision and min_score >= 7:
            print(f"        Approved! Overall: {critique.overall_score:.1f}/10")
            break

        # Revise if needed and not last cycle
        if i < max_revisions - 1:
            print(f"        Revising (min score: {min_score}, no_names: {critique.no_names_score})...")
            current = creator.revise_video_prompt(current, critique, shot_data, visual_style)
            revision_count += 1

    # Get final scores
    final_critique = critique_history[-1]

    return {
        "video_prompt": current.video_prompt,
        "slugline": current.slugline,
        "camera_movements": current.camera_movements,
        "dialogue_included": current.dialogue_included,
        "characters_described": current.characters_described,
        "revision_count": revision_count,
        "final_scores": {
            "screenplay_format": final_critique["screenplay_format_score"],
            "character_description": final_critique["character_description_score"],
            "camera_movement": final_critique["camera_movement_score"],
            "atmosphere_detail": final_critique["atmosphere_detail_score"],
            "dialogue_accuracy": final_critique["dialogue_accuracy_score"],
            "no_names": final_critique["no_names_score"],
            "overall": final_critique["overall_score"],
        },
        "critique_history": critique_history,
    }
