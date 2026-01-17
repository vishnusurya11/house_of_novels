"""
Shot Frame Prompt Agents - Generate first/last frame image prompts for video shots.

Uses LangGraph ReAct agents with tools to retrieve character and location descriptions
from the codex, then generates hyper-detailed cinematic prompts without using
character names (only physical descriptions, since the model doesn't know who is who).

Key Features:
- Uses `response_format` for guaranteed structured output
- Tools for retrieving character/location data from codex
- Creator + Critic workflow with revision loop

Workflow:
1. FramePromptCreatorAgent - Uses tools to fetch char/loc data, generates prompts
2. FramePromptCriticAgent - Uses tools to validate prompts against codex data
3. Creator revises based on critique
"""

import json
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

from src.story_schemas import ShotFramePromptSchema, ShotFrameCritiqueSchema
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
        Use this to get accurate details for describing characters in frame prompts.
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
        Use this to get accurate setting details for frame prompts.
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
# Frame Prompt Creator Agent (with Tools)
# =============================================================================

CREATOR_SYSTEM_PROMPT = """You are a MASTER cinematic image prompt engineer specializing in video frame generation.

Your task is to create HYPER-DETAILED prompts for the FIRST FRAME and LAST FRAME of a video shot.
These prompts will be used with AI image generation models (Flux, SDXL, Kling, Runway).

## CRITICAL RULES:

0. **VISUAL STYLE INTEGRATION** - If a style is provided:
   - The prompt MUST start with the provided STYLE PREFIX
   - The prompt MUST end with the provided STYLE SUFFIX
   - All visual descriptions must match the style aesthetic

1. **NEVER USE CHARACTER NAMES** - The AI model doesn't know who "Rhea" or "Marcus" is.
   Instead, describe characters by their PHYSICAL APPEARANCE:
   - "A tall woman in her late twenties with flowing auburn hair and emerald eyes"
   - NOT "Rhea stands in the square"

2. **USE THE TOOLS** - Before writing prompts, use the tools to:
   - Fetch character descriptions for each character in the shot
   - Fetch location descriptions for the setting

3. **SHOW PROGRESSION** - First frame and last frame should show the ACTION PROGRESSION:
   - First frame: Starting position/state of the action
   - Last frame: End position/state after the action described in shot

## PROMPT STRUCTURE (for EACH frame):

1. **SHOT SIZE & FRAMING**: "Wide establishing shot", "Medium shot", "Close-up"
2. **CAMERA ANGLE**: Eye level, low angle, high angle, Dutch angle
3. **LOCATION SETTING**: Detailed environment description from codex
4. **CHARACTER DESCRIPTION** (physical, NOT names):
   - Gender, age, build
   - Hair (color, length, style)
   - Eyes (color, expression)
   - Clothing (fabric, color, condition, style)
   - Distinguishing marks (scars, tattoos, jewelry)
   - Current pose/action/expression
5. **LIGHTING**: Direction, quality, color temperature, shadows
6. **ATMOSPHERE**: Mood, weather effects, particles (dust, rain, fog)
7. **COMPOSITION**: Foreground, midground, background layers
8. **QUALITY TAGS**: 8k, cinematic, film grain, shallow depth of field, etc.

## OUTPUT FORMAT:
- Each prompt: 300-500 words, single flowing paragraph
- Natural language descriptions (not comma-separated keywords)
- Ultra-specific details: "weathered brown leather jacket with brass buttons" not "leather jacket"

Remember: The model will receive the character's reference image, so focus on what they're DOING
and WEARING in THIS specific shot, plus the environment around them."""


CRITIC_SYSTEM_PROMPT = """You are a CRITICAL reviewer of AI video frame prompts.

Your job is to validate prompts against the original codex data and ensure quality standards.

## USE THE TOOLS to verify:
1. Character descriptions match their codex profiles
2. Location details match the codex location data
3. Physical descriptions are accurate (hair color, eye color, distinguishing features)

## EVALUATION CRITERIA (Score 1-10 each):

1. **CHARACTER_ACCURACY** (Score 1-10)
   - Do physical descriptions match codex data?
   - Is clothing description consistent with character profile?
   - Are distinguishing features included and accurate?
   - Score 1 if character names are used instead of descriptions!

2. **LOCATION_ACCURACY** (Score 1-10)
   - Does the setting match the codex location profile?
   - Are key features of the location present?
   - Is the atmosphere consistent with codex?

3. **FRAMING_ACCURACY** (Score 1-10)
   - Does the prompt use the correct shot_size from the shot data?
   - Is the camera angle/movement reflected in the description?

4. **LIGHTING_MOOD** (Score 1-10)
   - Does lighting match the time_of_day in shot data?
   - Is the visual_style_notes mood captured?
   - Are atmosphere effects (weather, particles) described?

5. **ACTION_CONTINUITY** (Score 1-10)
   - Does first frame → last frame show logical progression?
   - Is the action from the shot captured in both frames?
   - Does movement make sense across the frames?

6. **NO_NAMES** (Score 1-10) - CRITICAL!
   - Score 10 if NO character names appear (only physical descriptions)
   - Score 1 if ANY character name is used in prompts
   - This is a HARD requirement - names break image generation!

## STYLE ADHERENCE (if visual style is provided):
- Does each prompt START with the required style prefix?
- Does each prompt END with the required style suffix?
- Do visual descriptions match the style aesthetic?

## DECISION RULES:
- If ANY score is below 7, mark needs_revision = true
- If no_names_score < 10, DEFINITELY needs_revision = true
- Provide SPECIFIC suggestions referencing codex data"""


class FramePromptCreatorAgent:
    """
    Creates detailed first/last frame prompts using tools to fetch codex data.

    Uses LangGraph ReAct agent with:
    - Tools for character/location retrieval from codex
    - response_format for guaranteed structured output (ShotFramePromptSchema)
    """

    def __init__(self, codex: dict, model: str = DEFAULT_MODEL, temperature: float = 0.7):
        self.model_name = model
        self.temperature = temperature
        self.codex = codex

        # Create LLM
        self.llm = ChatOpenAI(
            model=model,
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL,
            temperature=temperature,
        )

        # Create tools with codex in closure
        self.tools = create_codex_tools(codex)

        # Create ReAct agent with tools AND response_format for guaranteed structured output
        self.agent = create_react_agent(
            model=self.llm,
            tools=self.tools,
            response_format=ShotFramePromptSchema,
        )

    def create_frame_prompts(self, shot_data: dict, scene_context: str = "", visual_style: dict = None) -> ShotFramePromptSchema:
        """
        Generate first and last frame prompts for a shot.

        The agent will use tools to fetch character/location descriptions,
        then generate hyper-detailed prompts with guaranteed structured output.

        Args:
            shot_data: Shot dict with characters_in_frame, location, action, etc.
            scene_context: Additional scene context (e.g., what happened before)
            visual_style: Visual style dict with name, prefix, suffix

        Returns:
            ShotFramePromptSchema with firstframe_prompt and lastframe_prompt
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
STYLE PREFIX (start each prompt with this): {style_prefix}
STYLE SUFFIX (end each prompt with this): {style_suffix}
"""

        user_prompt = f"""Generate FIRST FRAME and LAST FRAME image prompts for this video shot.

## SHOT DATA:
{shot_json}

## SCENE CONTEXT:
{scene_context if scene_context else "Opening shot of scene."}
{style_info}
## INSTRUCTIONS:

1. FIRST: Use get_character_description tool for EACH character in characters_in_frame
2. SECOND: Use get_location_description tool for the location
3. THIRD: Generate the prompts based on the retrieved data

For the FIRST FRAME:
- START WITH THE STYLE PREFIX if provided
- Show the BEGINNING state of the action described
- Where are characters positioned at the START?
- What expression/pose at the START?
- END WITH THE STYLE SUFFIX if provided

For the LAST FRAME:
- START WITH THE STYLE PREFIX if provided
- Show the END state after the action
- Where have characters moved to?
- What changed expression/pose?
- END WITH THE STYLE SUFFIX if provided

CRITICAL RULES:
- NEVER use character names - only physical descriptions from the tools
- Each prompt: 300-500 words, single paragraph
- First frame shows START of action, last frame shows END of action
- Use shot_size for framing, time_of_day for lighting"""

        # Run the ReAct agent - structured_response is guaranteed via response_format
        result = self.agent.invoke({
            "messages": [
                {"role": "system", "content": CREATOR_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ]
        })

        # With response_format, output is guaranteed in structured_response
        return result["structured_response"]

    def revise_frame_prompts(
        self,
        original: ShotFramePromptSchema,
        critique: ShotFrameCritiqueSchema,
        shot_data: dict,
        visual_style: dict = None
    ) -> ShotFramePromptSchema:
        """
        Revise frame prompts based on critic feedback.

        Args:
            original: Original prompts to revise
            critique: Critic's evaluation with scores and suggestions
            shot_data: Original shot data for reference
            visual_style: Visual style dict with name, prefix, suffix

        Returns:
            Revised ShotFramePromptSchema
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
REMINDER: Each prompt must START with: {style_prefix}
REMINDER: Each prompt must END with: {style_suffix}
"""

        prompt = f"""REVISE these frame prompts based on critic feedback.

## ORIGINAL FIRST FRAME PROMPT:
{original.firstframe_prompt}

## ORIGINAL LAST FRAME PROMPT:
{original.lastframe_prompt}

## CRITIC SCORES:
- Character Accuracy: {critique.character_accuracy_score}/10
- Location Accuracy: {critique.location_accuracy_score}/10
- Framing Accuracy: {critique.framing_accuracy_score}/10
- Lighting/Mood: {critique.lighting_mood_score}/10
- Action Continuity: {critique.action_continuity_score}/10
- No Names (CRITICAL): {critique.no_names_score}/10

## SUGGESTIONS FOR IMPROVEMENT:
{suggestions}

## SHOT DATA (reference):
{json.dumps(shot_data, indent=2)}
{style_info}
FIRST: Use the tools to re-fetch character and location data for accuracy.
THEN: Create IMPROVED prompts addressing ALL the critic's concerns.

CRITICAL: If no_names_score < 10, you MUST remove all character names and replace with physical descriptions!
CRITICAL: Ensure style prefix at START and style suffix at END of each prompt.

Maintain 300-500 words per prompt, single paragraph each."""

        # Run agent with tools for revision - structured_response guaranteed
        result = self.agent.invoke({
            "messages": [
                {"role": "system", "content": CREATOR_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
        })

        # With response_format, output is guaranteed in structured_response
        return result["structured_response"]


# =============================================================================
# Frame Prompt Critic Agent (with Tools)
# =============================================================================

class FramePromptCriticAgent:
    """
    Critiques frame prompts for accuracy against codex data.

    Uses LangGraph ReAct agent with:
    - Tools for character/location verification from codex
    - response_format for guaranteed structured output (ShotFrameCritiqueSchema)
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

        # Create ReAct agent with tools AND response_format for guaranteed structured output
        self.agent = create_react_agent(
            model=self.llm,
            tools=self.tools,
            response_format=ShotFrameCritiqueSchema,
        )

    def critique(
        self,
        frame_prompts: ShotFramePromptSchema,
        shot_data: dict,
        visual_style: dict = None
    ) -> ShotFrameCritiqueSchema:
        """
        Evaluate frame prompts for accuracy and quality.

        Uses tools to verify descriptions match codex data with guaranteed structured output.

        Args:
            frame_prompts: The prompts to critique
            shot_data: Original shot data for reference
            visual_style: Visual style dict with name, prefix, suffix

        Returns:
            ShotFrameCritiqueSchema with scores and suggestions
        """
        # Extract style requirements
        style_check = ""
        if visual_style:
            style_name = visual_style.get("name", "Anime")
            style_prefix = visual_style.get("prefix", "")
            style_suffix = visual_style.get("suffix", "")
            style_check = f"""

## REQUIRED VISUAL STYLE: {style_name}
Expected prefix: {style_prefix}
Expected suffix keywords: {style_suffix}

CHECK STYLE ADHERENCE:
- Does FIRST FRAME prompt START with the style prefix?
- Does FIRST FRAME prompt END with style-specific quality tags?
- Does LAST FRAME prompt START with the style prefix?
- Does LAST FRAME prompt END with style-specific quality tags?
- Do visual descriptions match the {style_name} aesthetic?
"""

        prompt = f"""CRITICALLY EVALUATE these frame prompts.

## FIRST FRAME PROMPT:
{frame_prompts.firstframe_prompt}

## LAST FRAME PROMPT:
{frame_prompts.lastframe_prompt}

## SHOT DATA:
{json.dumps(shot_data, indent=2)}
{style_check}
## INSTRUCTIONS:

1. FIRST: Use get_character_description tool to get ACTUAL character descriptions from codex
2. SECOND: Use get_location_description tool to get ACTUAL location description from codex
3. THIRD: Compare the prompts against the codex data and score

SCORING CRITERIA (1-10 each):

1. CHARACTER_ACCURACY: Do descriptions match codex? (hair color, eye color, clothing, distinguishing marks)
2. LOCATION_ACCURACY: Does setting match codex location? (key features, atmosphere)
3. FRAMING_ACCURACY: Does prompt use correct shot_size ({shot_data.get('shot_size', 'UNKNOWN')})?
4. LIGHTING_MOOD: Does lighting match time_of_day ({shot_data.get('time_of_day', 'UNKNOWN')})?
5. ACTION_CONTINUITY: Does first→last frame show logical action progression?
6. NO_NAMES: Score 10 if NO character names used, Score 1 if ANY names found!

CRITICAL: Check if character names like {shot_data.get('characters_in_frame', [])} appear in prompts!
If names are present, no_names_score MUST be 1!

If visual style is provided, check style adherence and include in suggestions if missing.

Set needs_revision=true if ANY score is below 7."""

        # Run agent - structured_response is guaranteed via response_format
        result = self.agent.invoke({
            "messages": [
                {"role": "system", "content": CRITIC_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
        })

        # With response_format, output is guaranteed in structured_response
        return result["structured_response"]


# =============================================================================
# Orchestration Function
# =============================================================================

def generate_shot_frame_prompts(
    shot_data: dict,
    codex: dict,
    scene_context: str = "",
    visual_style: dict = None,
    model: str = DEFAULT_MODEL,
    max_revisions: int = 2,
) -> dict:
    """
    Generate first/last frame prompts for a shot using creator + critic workflow.

    Uses ReAct agents with tools and guaranteed structured output via response_format.

    Args:
        shot_data: Shot dict with characters_in_frame, location, action, etc.
        codex: Full codex with characters and locations
        scene_context: Additional scene context
        visual_style: Visual style dict with name, prefix, suffix, description
        model: LLM model to use
        max_revisions: Maximum revision cycles (default 2)

    Returns:
        Dict with:
        - firstframe_prompt: First frame image prompt
        - lastframe_prompt: Last frame image prompt
        - shot_size_applied: Shot size used
        - time_of_day_applied: Time of day lighting
        - characters_described: List of character descriptions used
        - revision_count: Number of revisions made
        - final_scores: Final critique scores
        - critique_history: All critiques for metadata
    """
    creator = FramePromptCreatorAgent(codex=codex, model=model)
    critic = FramePromptCriticAgent(codex=codex, model=model, temperature=0.3)

    shot_num = shot_data.get("shot_number", "?")
    location = shot_data.get("location", "Unknown")
    print(f"      Creating frame prompts for shot {shot_num} at {location}...")

    # Initial prompt generation (guaranteed structured output)
    current = creator.create_frame_prompts(shot_data, scene_context, visual_style)

    critique_history = []
    revision_count = 0

    # Critique-revision loop
    for i in range(max_revisions):
        print(f"        Critique cycle {i + 1}/{max_revisions}...")

        # Get critique (guaranteed structured output)
        critique = critic.critique(current, shot_data, visual_style)

        critique_dict = {
            "cycle": i + 1,
            "character_accuracy_score": critique.character_accuracy_score,
            "location_accuracy_score": critique.location_accuracy_score,
            "framing_accuracy_score": critique.framing_accuracy_score,
            "lighting_mood_score": critique.lighting_mood_score,
            "action_continuity_score": critique.action_continuity_score,
            "no_names_score": critique.no_names_score,
            "overall_score": critique.overall_score,
            "needs_revision": critique.needs_revision,
            "suggestions": critique.suggestions,
        }
        critique_history.append(critique_dict)

        # Check if revision needed
        min_score = min(
            critique.character_accuracy_score,
            critique.location_accuracy_score,
            critique.framing_accuracy_score,
            critique.lighting_mood_score,
            critique.action_continuity_score,
            critique.no_names_score,
        )

        if not critique.needs_revision and min_score >= 7:
            print(f"        Approved! Overall: {critique.overall_score:.1f}/10")
            break

        # Revise if needed and not last cycle
        if i < max_revisions - 1:
            print(f"        Revising (min score: {min_score}, no_names: {critique.no_names_score})...")
            current = creator.revise_frame_prompts(current, critique, shot_data, visual_style)
            revision_count += 1

    # Get final scores from last critique
    final_critique = critique_history[-1]

    return {
        "firstframe_prompt": current.firstframe_prompt,
        "lastframe_prompt": current.lastframe_prompt,
        "shot_size_applied": current.shot_size_applied,
        "time_of_day_applied": current.time_of_day_applied,
        "characters_described": current.characters_described,
        "revision_count": revision_count,
        "final_scores": {
            "character_accuracy": final_critique["character_accuracy_score"],
            "location_accuracy": final_critique["location_accuracy_score"],
            "framing_accuracy": final_critique["framing_accuracy_score"],
            "lighting_mood": final_critique["lighting_mood_score"],
            "action_continuity": final_critique["action_continuity_score"],
            "no_names": final_critique["no_names_score"],
            "overall": final_critique["overall_score"],
        },
        "critique_history": critique_history,
    }