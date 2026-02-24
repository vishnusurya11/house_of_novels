"""
Scene Image Prompt Agents - Generate one representative image prompt per scene.

Uses LangGraph ReAct agents with tools to retrieve character and location descriptions
from the codex, then generates hyper-detailed cinematic prompts without using
character names (only physical descriptions, since the model doesn't know who is who).

Key Features:
- Uses `response_format` for guaranteed structured output
- Tools for retrieving character/location data from codex
- Composer + Critic workflow with revision loop

Workflow:
1. SceneImageComposerAgent - Uses tools to fetch char/loc data, generates prompt
2. SceneImageCriticAgent - Uses tools to validate prompts against codex data
3. Composer revises based on critique
"""

import json
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

from src.story_schemas import SceneImagePromptSchema, SceneImageCritiqueSchema
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
    def lookup_character_by_role(role: str) -> str:
        """
        Look up a character by their story role (protagonist, antagonist, supporting).
        Use this when scene data has role descriptions like "the protagonist" instead of names.

        Args:
            role: The role like "protagonist", "antagonist", "supporting", "the protagonist", etc.

        Returns:
            Character name, ID, and basic info if found.
        """
        role_lower = role.lower().replace("the ", "").strip()

        for char in characters:
            char_role = char.get("role_in_story", "").lower()
            if char_role == role_lower:
                return json.dumps({
                    "id": char.get("id", ""),
                    "name": char.get("name", ""),
                    "role_in_story": char.get("role_in_story", ""),
                    "gender": char.get("gender", ""),
                    "age": char.get("age", ""),
                }, indent=2)

        return f"No character found with role '{role}'. Available roles: {[c.get('role_in_story') for c in characters]}"

    @tool
    def get_character_description(character_name: str) -> str:
        """
        Retrieve full physical description and clothing for a character by name.
        Use this to get accurate details for describing characters in scene prompts.
        Returns ID, physical appearance, clothing, distinguishing features.

        Args:
            character_name: The character's name (case-insensitive search)
        """
        name_lower = character_name.lower().strip()

        for char in characters:
            if char.get("name", "").lower().strip() == name_lower:
                physical = char.get("physical", {})
                result = {
                    "id": char.get("id", ""),
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
                    "id": char.get("id", ""),
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
        Use this to get accurate setting details for scene prompts.
        Returns ID, visual description, atmosphere, key features, sensory details.

        Args:
            location_name: The location name (case-insensitive, partial match)
        """
        name_lower = location_name.lower().strip()

        for loc in locations:
            loc_name = loc.get("name", "").lower().strip()
            if loc_name == name_lower or name_lower in loc_name or loc_name in name_lower:
                result = {
                    "id": loc.get("id", ""),
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

    return [lookup_character_by_role, get_character_description, get_location_description, list_all_characters, list_all_locations]


# =============================================================================
# Scene Image Composer Agent (with Tools)
# =============================================================================

COMPOSER_SYSTEM_PROMPT = """You are a MASTER cinematic image prompt engineer specializing in creating representative scene images.

Your task is to create ONE HYPER-DETAILED prompt that captures the essence of an entire scene.
This prompt will be used with AI image generation models (Flux, SDXL, Stable Diffusion).

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
   - If scene has role descriptions like "the protagonist" or "the antagonist", use lookup_character_by_role to get the actual character NAME and ID
   - Then use get_character_description with the character NAME to get their physical appearance
   - Use get_location_description to get the location details AND its ID
   - IMPORTANT: Save the character NAMES (not roles!) and IDs for your output fields

3. **CAPTURE THE KEY MOMENT** - Choose the most visually compelling moment of the scene:
   - The emotional peak
   - The dramatic confrontation
   - The pivotal action

## PROMPT STRUCTURE:

1. **SHOT SIZE & FRAMING**: "Wide establishing shot", "Medium shot", "Close-up"
2. **CAMERA ANGLE**: Eye level, low angle, high angle, Dutch angle
3. **LOCATION SETTING**: Detailed environment description from codex
4. **CHARACTER DESCRIPTIONS** (physical, NOT names):
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
- Prompt: 300-500 words, single flowing paragraph
- Natural language descriptions (not comma-separated keywords)
- Ultra-specific details: "weathered brown leather jacket with brass buttons" not "leather jacket"

## OUTPUT FIELDS (CRITICAL):
- **location_name**: The location name from codex (e.g., "Weeps Canyon Gardens")
- **location_id**: The location ID from get_location_description tool (e.g., "loc_001")
- **characters_in_scene**: ACTUAL CHARACTER NAMES from lookup_character_by_role, NOT role descriptions!
  - WRONG: ["the protagonist", "the antagonist"]
  - RIGHT: ["Yara Ridgewell", "Quillon Blackwood"]
- **character_ids**: The character IDs from lookup_character_by_role (e.g., ["char_001", "char_002"])

Remember: The model will receive character reference images, so focus on what they're DOING
and WEARING in THIS specific scene, plus the environment around them."""


CRITIC_SYSTEM_PROMPT = """You are a CRITICAL reviewer of AI scene image prompts.

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

3. **NO_NAMES** (Score 1-10) - CRITICAL!
   - Score 10 if NO character names appear (only physical descriptions)
   - Score 1 if ANY character name is used in prompts
   - This is a HARD requirement - names break image generation!

4. **VISUAL_DETAIL** (Score 1-10)
   - Is there enough detail for image generation?
   - Are textures, materials, colors specified?
   - Is lighting and atmosphere described?

5. **COMPOSITION** (Score 1-10)
   - Is the framing clear (wide, medium, close-up)?
   - Is there a clear focal point?
   - Are foreground/background layers described?

## STYLE ADHERENCE (if visual style is provided):
- Does the prompt START with the required style prefix?
- Does the prompt END with style-specific quality tags?
- Do visual descriptions match the style aesthetic?

## DECISION RULES:
- If ANY score is below 7, mark needs_revision = true
- If no_names_score < 10, DEFINITELY needs_revision = true
- Provide SPECIFIC suggestions referencing codex data"""


class SceneImageComposerAgent:
    """
    Creates detailed scene image prompts using tools to fetch codex data.

    Uses LangGraph ReAct agent with:
    - Tools for character/location retrieval from codex
    - response_format for guaranteed structured output (SceneImagePromptSchema)
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
            response_format=SceneImagePromptSchema,
        )

    def create_scene_prompt(
        self,
        scene_data: dict,
        act_number: int,
        visual_style: dict = None
    ) -> SceneImagePromptSchema:
        """
        Generate a representative image prompt for a scene.

        The agent will use tools to fetch character/location descriptions,
        then generate hyper-detailed prompts with guaranteed structured output.

        Args:
            scene_data: Scene dict with location, characters, text, paragraphs
            act_number: Act number for context
            visual_style: Visual style dict with name, prefix, suffix

        Returns:
            SceneImagePromptSchema with the scene prompt
        """
        scene_json = json.dumps({
            "scene_number": scene_data.get("scene_number"),
            "location": scene_data.get("location"),
            "characters": scene_data.get("characters", []),
            "text": scene_data.get("text", "")[:1000],  # Truncate long prose
        }, indent=2)

        # Extract style components
        style_info = ""
        if visual_style:
            style_name = visual_style.get("name", "Anime")
            style_prefix = visual_style.get("prefix", "")
            style_suffix = visual_style.get("suffix", "")
            style_info = f"""
## VISUAL STYLE: {style_name}
STYLE PREFIX (start the prompt with this): {style_prefix}
STYLE SUFFIX (end the prompt with this): {style_suffix}
"""

        user_prompt = f"""Generate ONE representative image prompt for this scene.

## SCENE DATA:
Act {act_number}, Scene {scene_data.get("scene_number")}
Location: {scene_data.get("location")}
Characters: {scene_data.get("characters", [])}

{scene_json}
{style_info}
## INSTRUCTIONS:

1. FIRST: Use get_character_description tool for EACH character in the scene
2. SECOND: Use get_location_description tool for the location
3. THIRD: Generate the prompt based on the retrieved data

Choose the most VISUALLY COMPELLING moment from the scene:
- What is the key dramatic beat?
- What poses/expressions capture the emotion?
- What composition tells the story?

CRITICAL RULES:
- NEVER use character names - only physical descriptions from the tools
- Prompt: 300-500 words, single paragraph
- START with style prefix, END with style suffix (if provided)
- Include all characters present in the scene"""

        # Run the ReAct agent - structured_response is guaranteed via response_format
        result = self.agent.invoke({
            "messages": [
                {"role": "system", "content": COMPOSER_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ]
        })

        # With response_format, output is guaranteed in structured_response
        return result["structured_response"]

    def revise_scene_prompt(
        self,
        original: SceneImagePromptSchema,
        critique: SceneImageCritiqueSchema,
        scene_data: dict,
        visual_style: dict = None
    ) -> SceneImagePromptSchema:
        """
        Revise scene prompt based on critic feedback.

        Args:
            original: Original prompt to revise
            critique: Critic's evaluation with scores and suggestions
            scene_data: Original scene data for reference
            visual_style: Visual style dict with name, prefix, suffix

        Returns:
            Revised SceneImagePromptSchema
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
REMINDER: The prompt must START with: {style_prefix}
REMINDER: The prompt must END with: {style_suffix}
"""

        prompt = f"""REVISE this scene image prompt based on critic feedback.

## ORIGINAL PROMPT:
{original.prompt}

## CRITIC SCORES:
- Character Accuracy: {critique.character_accuracy_score}/10
- Location Accuracy: {critique.location_accuracy_score}/10
- No Names (CRITICAL): {critique.no_names_score}/10
- Visual Detail: {critique.visual_detail_score}/10
- Composition: {critique.composition_score}/10

## SUGGESTIONS FOR IMPROVEMENT:
{suggestions}

## SCENE DATA (reference):
Location: {scene_data.get("location")}
Characters: {scene_data.get("characters", [])}
{style_info}
FIRST: Use the tools to re-fetch character and location data for accuracy.
THEN: Create IMPROVED prompt addressing ALL the critic's concerns.

CRITICAL: If no_names_score < 10, you MUST remove all character names and replace with physical descriptions!
CRITICAL: Ensure style prefix at START and style suffix at END of the prompt.

Maintain 300-500 words, single paragraph."""

        # Run agent with tools for revision - structured_response guaranteed
        result = self.agent.invoke({
            "messages": [
                {"role": "system", "content": COMPOSER_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
        })

        # With response_format, output is guaranteed in structured_response
        return result["structured_response"]


# =============================================================================
# Scene Image Critic Agent (with Tools)
# =============================================================================

class SceneImageCriticAgent:
    """
    Critiques scene image prompts for accuracy against codex data.

    Uses LangGraph ReAct agent with:
    - Tools for character/location verification from codex
    - response_format for guaranteed structured output (SceneImageCritiqueSchema)
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
            response_format=SceneImageCritiqueSchema,
        )

    def critique(
        self,
        scene_prompt: SceneImagePromptSchema,
        scene_data: dict,
        visual_style: dict = None
    ) -> SceneImageCritiqueSchema:
        """
        Evaluate scene prompt for accuracy and quality.

        Uses tools to verify descriptions match codex data with guaranteed structured output.

        Args:
            scene_prompt: The prompt to critique
            scene_data: Original scene data for reference
            visual_style: Visual style dict with name, prefix, suffix

        Returns:
            SceneImageCritiqueSchema with scores and suggestions
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
- Does the prompt START with the style prefix?
- Does the prompt END with style-specific quality tags?
- Do visual descriptions match the {style_name} aesthetic?
"""

        characters = scene_data.get("characters", [])

        prompt = f"""CRITICALLY EVALUATE this scene image prompt.

## SCENE IMAGE PROMPT:
{scene_prompt.prompt}

## SCENE DATA:
Location: {scene_data.get("location")}
Characters: {characters}
{style_check}
## INSTRUCTIONS:

1. FIRST: Use get_character_description tool to get ACTUAL character descriptions from codex for each character: {characters}
2. SECOND: Use get_location_description tool to get ACTUAL location description from codex
3. THIRD: Compare the prompt against the codex data and score

SCORING CRITERIA (1-10 each):

1. CHARACTER_ACCURACY: Do descriptions match codex? (hair color, eye color, clothing, distinguishing marks)
2. LOCATION_ACCURACY: Does setting match codex location? (key features, atmosphere)
3. NO_NAMES: Score 10 if NO character names used, Score 1 if ANY names found!
4. VISUAL_DETAIL: Is there enough detail for image generation?
5. COMPOSITION: Is framing clear with good focal point?

CRITICAL: Check if character names like {characters} appear in the prompt!
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

def _map_roles_to_characters(role_descriptions: list[str], codex: dict) -> tuple[list[str], list[str]]:
    """
    Map role descriptions to actual character names and IDs.

    Matches by role_in_story field (e.g., "the protagonist" → character with role="protagonist")

    Returns:
        tuple of (character_names, character_ids)
    """
    characters = codex.get("story", {}).get("characters", [])
    names = []
    ids = []

    for desc in role_descriptions:
        desc_lower = desc.lower().strip()
        matched = False

        # Try matching by role_in_story
        if "protagonist" in desc_lower:
            for char in characters:
                if char.get("role_in_story", "").lower() == "protagonist":
                    names.append(char.get("name", desc))
                    if char.get("id"):
                        ids.append(char["id"])
                    matched = True
                    break
        elif "antagonist" in desc_lower:
            for char in characters:
                if char.get("role_in_story", "").lower() == "antagonist":
                    names.append(char.get("name", desc))
                    if char.get("id"):
                        ids.append(char["id"])
                    matched = True
                    break
        elif "mentor" in desc_lower or "elder" in desc_lower or "wise" in desc_lower:
            for char in characters:
                if char.get("role_in_story", "").lower() == "supporting":
                    names.append(char.get("name", desc))
                    if char.get("id"):
                        ids.append(char["id"])
                    matched = True
                    break

        # Try matching by actual name (for cases where scene has real names)
        if not matched:
            for char in characters:
                char_name = char.get("name", "").lower()
                if desc_lower == char_name or desc_lower in char_name or char_name in desc_lower:
                    names.append(char.get("name", desc))
                    if char.get("id"):
                        ids.append(char["id"])
                    matched = True
                    break

        # Skip if no match - don't keep generic descriptions like "community members"
        # This keeps names and ids lists synchronized and avoids generic text in character data

    return names, ids


def _lookup_location_id(location_name: str, codex: dict) -> str:
    """Look up location ID from codex by name (case-insensitive)."""
    locations = codex.get("story", {}).get("locations", [])
    name_lower = location_name.lower().strip()
    for loc in locations:
        loc_name = loc.get("name", "").lower().strip()
        if loc_name == name_lower or name_lower in loc_name or loc_name in name_lower:
            return loc.get("id", "")
    return ""


def generate_scene_image_prompt(
    scene_data: dict,
    act_number: int,
    codex: dict,
    visual_style: dict = None,
    model: str = DEFAULT_MODEL,
    max_revisions: int = 2,
) -> dict:
    """
    Generate a representative image prompt for a scene using composer + critic workflow.

    Uses ReAct agents with tools and guaranteed structured output via response_format.

    Args:
        scene_data: Scene dict with location, characters, text, paragraphs
        act_number: Act number for context
        codex: Full codex with characters and locations
        visual_style: Visual style dict with name, prefix, suffix, description
        model: LLM model to use
        max_revisions: Maximum revision cycles (default 2)

    Returns:
        Dict with:
        - prompt: The scene image prompt
        - location_name: Location from scene
        - location_id: Location ID from codex (e.g., 'loc_001')
        - characters_in_scene: Characters in scene
        - character_ids: Character IDs from codex (e.g., ['char_001', 'char_002'])
        - scene_summary: Brief summary
        - composition_notes: Composition notes
        - mood_lighting: Lighting/mood description
        - revision_count: Number of revisions made
        - final_scores: Final critique scores
        - critique_history: All critiques for metadata
    """
    composer = SceneImageComposerAgent(codex=codex, model=model)
    critic = SceneImageCriticAgent(codex=codex, model=model, temperature=0.3)

    scene_num = scene_data.get("scene_number", "?")
    location = scene_data.get("location", "Unknown")
    print(f"      Creating scene image prompt for scene {scene_num} at {location}...")

    # Initial prompt generation (guaranteed structured output)
    current = composer.create_scene_prompt(scene_data, act_number, visual_style)

    critique_history = []
    revision_count = 0

    # Critique-revision loop
    for i in range(max_revisions):
        print(f"        Critique cycle {i + 1}/{max_revisions}...")

        # Get critique (guaranteed structured output)
        critique = critic.critique(current, scene_data, visual_style)

        critique_dict = {
            "cycle": i + 1,
            "character_accuracy_score": critique.character_accuracy_score,
            "location_accuracy_score": critique.location_accuracy_score,
            "no_names_score": critique.no_names_score,
            "visual_detail_score": critique.visual_detail_score,
            "composition_score": critique.composition_score,
            "overall_score": critique.overall_score,
            "needs_revision": critique.needs_revision,
            "suggestions": critique.suggestions,
        }
        critique_history.append(critique_dict)

        # Check if revision needed
        min_score = min(
            critique.character_accuracy_score,
            critique.location_accuracy_score,
            critique.no_names_score,
            critique.visual_detail_score,
            critique.composition_score,
        )

        if not critique.needs_revision and min_score >= 7:
            print(f"        Approved! Overall: {critique.overall_score:.1f}/10")
            break

        # Revise if needed and not last cycle
        if i < max_revisions - 1:
            print(f"        Revising (min score: {min_score}, no_names: {critique.no_names_score})...")
            current = composer.revise_scene_prompt(current, critique, scene_data, visual_style)
            revision_count += 1

    # Get final scores from last critique
    final_critique = critique_history[-1]

    # Map role descriptions to actual character names and IDs
    location_id = _lookup_location_id(scene_data.get("location", ""), codex)
    character_names, character_ids = _map_roles_to_characters(
        scene_data.get("characters", []), codex
    )

    return {
        "prompt": current.prompt,
        "location_name": current.location_name,
        "location_id": location_id,
        "characters_in_scene": character_names,  # Actual names like "Yara Ridgewell"
        "character_ids": character_ids,  # IDs like ["char_001"]
        "scene_summary": current.scene_summary,
        "composition_notes": current.composition_notes,
        "mood_lighting": current.mood_lighting,
        "revision_count": revision_count,
        "final_scores": {
            "character_accuracy": final_critique["character_accuracy_score"],
            "location_accuracy": final_critique["location_accuracy_score"],
            "no_names": final_critique["no_names_score"],
            "visual_detail": final_critique["visual_detail_score"],
            "composition": final_critique["composition_score"],
            "overall": final_critique["overall_score"],
        },
        "critique_history": critique_history,
    }


# =============================================================================
# Layered Scene Image Prompt Generation
# =============================================================================
# Each function does ONE thing. The orchestrator wires them together.
# =============================================================================

from src.story_schemas import (
    LayeredSceneImagePromptSchema,
    LayeredSceneImageCritiqueSchema,
    LocationLayerPrompt,
    CharacterLayerPrompt,
)
from src.config import get_max_character_layers


# =============================================================================
# System Prompts
# =============================================================================

LAYERED_COMPOSER_SYSTEM_PROMPT = """You are a MASTER cinematic scene composition engineer.

Your task is to create a LAYERED image generation plan for a scene. Each layer will be
applied sequentially to build the final scene image using FLUX Kontext iterative editing.

## HOW LAYERED GENERATION WORKS:
1. Layer 1 (Location): Takes the pre-generated location image and modifies it
   for this scene's context (time of day, weather, damage, atmospheric effects).
2. Layer 2 (Primary Character): Takes the modified location + character portrait
   reference image and places the character in the scene.
3. Layer 3+ (Additional Characters): Same process for each additional character,
   building on the previous layer's output.

## CRITICAL RULES:

1. **LOCATION LAYER** — Describe ONLY modifications to the existing location image.
   - The base location image already exists. Do NOT describe the location from scratch.
   - Focus on: time changes (night vs day), weather (rain, fog, snow), damage (fire,
     destruction), atmospheric effects (dust, smoke), crowd presence, lighting shifts.
   - If no modifications needed (same conditions as the base location), set
     requires_modification=false with a minimal prompt like "No changes needed."
   - Keep the prompt to 100-200 words.

2. **CHARACTER LAYERS** — Describe ONLY pose, action, position, and expression.
   - The character's reference portrait provides their physical appearance automatically.
   - Do NOT describe hair color, eye color, clothing, height, build, skin tone, etc.
   - DO describe: what they are doing, their emotional state, where they stand in the
     frame (left/center/right, foreground/midground/background), how they interact
     with the environment or other characters already placed.
   - Order characters by narrative importance: primary/focal character FIRST.
   - Keep each prompt to 100-200 words.

3. **USE THE TOOLS** to retrieve character and location data from the codex:
   - Use lookup_character_by_role to find character names and IDs from role descriptions
   - Use get_character_description to get character IDs
   - Use get_location_description to get the location ID
   - You need these IDs for cross-referencing with pre-generated images.

4. **COMPOSITION** — Think about the overall composition across all layers:
   - Where does each character stand relative to the camera and each other?
   - What is the visual focal point?
   - Do the character positions create natural interaction?
   - Consider depth: foreground, midground, background placement.

## OUTPUT FIELDS:
- location_id: From get_location_description tool (e.g., 'loc_001')
- character_layers: Ordered list — primary character FIRST
- Each character_layer needs character_name and character_id from the lookup tools
- total_layers: 1 (location) + number of character layers"""


LAYERED_CRITIC_SYSTEM_PROMPT = """You are a CRITICAL reviewer of layered scene image prompts.

These prompts are designed for FLUX Kontext iterative image generation where:
- Layer 1 modifies an existing location image
- Layers 2+ add characters using portrait reference images

## USE THE TOOLS to verify:
1. Character IDs exist in the codex
2. Location ID exists in the codex
3. Character descriptions in character layers do NOT duplicate physical appearance

## EVALUATION CRITERIA (Score 1-10 each):

1. **LOCATION_MODIFICATION** (Score 1-10)
   - Does the location layer describe CHANGES, not the full location?
   - Are modifications specific and actionable (e.g., "add torchlight" not "dark atmosphere")?
   - Is requires_modification correctly set (false only if truly no changes needed)?

2. **CHARACTER_PLACEMENT** (Score 1-10)
   - Are poses, positions, and actions clearly described?
   - Is each character's position in the frame specified?
   - Are interactions between characters described where applicable?

3. **NO_REDUNDANCY** (Score 1-10) — CRITICAL!
   - Score 10 if character layers contain ZERO physical appearance descriptions
   - Score LOW if any character layer mentions hair color, eye color, clothing details,
     height, build, skin tone, etc. (the portrait reference handles all of this)
   - Score LOW if character layers re-describe the location setting

4. **COMPOSITION** (Score 1-10)
   - Do the character positions create a visually balanced layout?
   - Is there a clear focal point (primary character)?
   - Does the spatial arrangement make sense for the scene's action?

5. **ACTION_CLARITY** (Score 1-10)
   - Are character actions visually interesting and specific?
   - Can the actions be depicted in a still image?
   - Do actions convey the emotional tone of the scene?

## OVERALL SCORE:
- Calculate overall_score as the average of all 5 component scores above.

## DECISION RULES:
- If ANY score is below 7, mark needs_revision = true
- Provide SPECIFIC suggestions referencing what needs to change"""


# =============================================================================
# Agent Constructors
# =============================================================================

def create_layered_composer_agent(codex: dict, model: str = DEFAULT_MODEL, temperature: float = 0.7):
    """Create a ReAct agent for layered scene prompt composition."""
    llm = ChatOpenAI(
        model=model,
        api_key=OPENROUTER_API_KEY,
        base_url=OPENROUTER_BASE_URL,
        temperature=temperature,
    )
    tools = create_codex_tools(codex)
    return create_react_agent(
        model=llm,
        tools=tools,
        response_format=LayeredSceneImagePromptSchema,
    )


def create_layered_critic_agent(codex: dict, model: str = DEFAULT_MODEL, temperature: float = 0.3):
    """Create a ReAct agent for layered scene prompt critique."""
    llm = ChatOpenAI(
        model=model,
        api_key=OPENROUTER_API_KEY,
        base_url=OPENROUTER_BASE_URL,
        temperature=temperature,
    )
    tools = create_codex_tools(codex)
    return create_react_agent(
        model=llm,
        tools=tools,
        response_format=LayeredSceneImageCritiqueSchema,
    )


# =============================================================================
# Prompt Builders
# =============================================================================

def build_composer_prompt(scene_data: dict, act_number: int, visual_style: dict | None) -> str:
    """Build the user prompt string for the layered composer agent."""
    scene_json = json.dumps({
        "scene_number": scene_data.get("scene_number"),
        "location": scene_data.get("location"),
        "time_of_day": scene_data.get("time_of_day", ""),
        "characters": scene_data.get("characters", []),
        "pov_character": scene_data.get("pov_character", ""),
        "text": scene_data.get("text", "")[:1000],
    }, indent=2)

    style_info = ""
    if visual_style:
        style_info = f"""
## VISUAL STYLE: {visual_style.get("name", "Anime")}
Note: Style is applied at the image generation level, not in layer prompts.
Keep layer prompts focused on content/action, not artistic style."""

    return f"""Generate a LAYERED image composition plan for this scene.

## SCENE DATA:
Act {act_number}, Scene {scene_data.get("scene_number")}
Location: {scene_data.get("location")}
Time of Day: {scene_data.get("time_of_day", "unknown")}
POV Character: {scene_data.get("pov_character", "unknown")}
Characters: {scene_data.get("characters", [])}

{scene_json}
{style_info}
## INSTRUCTIONS:

1. FIRST: Use get_location_description tool to get the location details and ID
2. SECOND: For EACH character, use lookup_character_by_role or get_character_description
   to get their NAME and ID
3. THIRD: Create the layered prompt plan:

   - LOCATION LAYER: What changes from the base location image for THIS scene?
     (time of day, weather, atmospheric effects, damage, etc.)
     If the base location already matches, set requires_modification=false.

   - CHARACTER LAYERS (one per character, primary/POV character FIRST):
     What is each character DOING? Where do they STAND in the frame?
     What is their EXPRESSION? How do they INTERACT with the scene/each other?
     Do NOT describe their appearance — the portrait reference handles that.

4. Set total_layers = 1 + number of character layers

CRITICAL: Keep each layer prompt to 100-200 words. Be specific and actionable."""


def build_revision_prompt(
    original: LayeredSceneImagePromptSchema,
    critique: LayeredSceneImageCritiqueSchema,
    scene_data: dict,
    visual_style: dict | None,
) -> str:
    """Build the user prompt string for a revision pass."""
    suggestions = "\n".join(f"- {s}" for s in critique.suggestions)

    # Serialize the original layered prompt
    location_info = (
        f"requires_modification: {original.location_layer.requires_modification}\n"
        f"prompt: {original.location_layer.prompt}"
    )
    char_info = "\n".join(
        f"  [{i+1}] {cl.character_name} ({cl.character_id}): {cl.prompt[:100]}..."
        for i, cl in enumerate(original.character_layers)
    )

    return f"""REVISE this layered scene image prompt based on critic feedback.

## ORIGINAL LOCATION LAYER:
{location_info}

## ORIGINAL CHARACTER LAYERS:
{char_info}

## CRITIC SCORES:
- Location Modification: {critique.location_modification_score}/10
- Character Placement: {critique.character_placement_score}/10
- No Redundancy (CRITICAL): {critique.no_redundancy_score}/10
- Composition: {critique.composition_score}/10
- Action Clarity: {critique.action_clarity_score}/10

## SUGGESTIONS FOR IMPROVEMENT:
{suggestions}

## SCENE DATA (reference):
Location: {scene_data.get("location")}
Characters: {scene_data.get("characters", [])}

FIRST: Use the tools to re-fetch character and location data for accuracy.
THEN: Create IMPROVED layered prompt addressing ALL the critic's concerns.

CRITICAL REMINDERS:
- Location layer: CHANGES only, not full description
- Character layers: POSE/ACTION/POSITION only, no physical appearance
- Keep each layer prompt to 100-200 words"""


def build_critique_prompt(
    scene_prompt: LayeredSceneImagePromptSchema,
    scene_data: dict,
    visual_style: dict | None,
) -> str:
    """Build the user prompt string for the critic agent."""
    # Serialize location layer
    loc_layer = scene_prompt.location_layer
    loc_summary = (
        f"requires_modification: {loc_layer.requires_modification}\n"
        f"time_of_day: {loc_layer.time_of_day}\n"
        f"weather: {loc_layer.weather_atmosphere}\n"
        f"modifications: {loc_layer.modifications}\n"
        f"prompt: {loc_layer.prompt}"
    )

    # Serialize character layers
    char_summaries = []
    for i, cl in enumerate(scene_prompt.character_layers):
        char_summaries.append(
            f"  [{i+1}] {cl.character_name} ({cl.character_id})\n"
            f"      position: {cl.position_in_frame}\n"
            f"      action: {cl.action_pose}\n"
            f"      expression: {cl.emotional_expression}\n"
            f"      is_primary: {cl.is_primary}\n"
            f"      prompt: {cl.prompt}"
        )
    char_info = "\n".join(char_summaries)

    characters = scene_data.get("characters", [])

    return f"""CRITICALLY EVALUATE this layered scene image prompt.

## LOCATION LAYER:
{loc_summary}

## CHARACTER LAYERS:
{char_info}

## SCENE DATA:
Location: {scene_data.get("location")}
Characters: {characters}

## INSTRUCTIONS:

1. FIRST: Use get_character_description for each character: {characters}
2. SECOND: Use get_location_description to get the location details
3. THIRD: Compare each layer against codex data and score

KEY CHECKS:
- Does the location layer describe CHANGES only (not the full location)?
- Do character layers avoid physical appearance descriptions?
  (Check: NO mentions of hair color, eye color, clothing details, height, build)
- Do character positions create a sensible spatial layout?
- Are actions specific enough to depict in a still image?

Set needs_revision=true if ANY score is below 7."""


# =============================================================================
# Single-Step Execution
# =============================================================================

def run_composer(agent, user_prompt: str) -> LayeredSceneImagePromptSchema:
    """Run the layered composer agent once. Returns structured output."""
    result = agent.invoke({
        "messages": [
            {"role": "system", "content": LAYERED_COMPOSER_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
    })
    return result["structured_response"]


def run_critic(agent, user_prompt: str) -> LayeredSceneImageCritiqueSchema:
    """Run the layered critic agent once. Returns structured output."""
    result = agent.invoke({
        "messages": [
            {"role": "system", "content": LAYERED_CRITIC_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
    })
    return result["structured_response"]


# =============================================================================
# Post-Processing
# =============================================================================

def enforce_character_limit(
    schema: LayeredSceneImagePromptSchema,
    max_layers: int,
) -> LayeredSceneImagePromptSchema:
    """Truncate character_layers to max_layers. Excess become background note in last layer."""
    max_layers = max(1, max_layers)
    if len(schema.character_layers) <= max_layers:
        return schema

    kept = list(schema.character_layers[:max_layers])
    excess = schema.character_layers[max_layers:]

    # Append background note to the last kept layer's prompt
    excess_names = [cl.character_name for cl in excess]
    background_note = (
        f" Other characters present in the background: {', '.join(excess_names)}."
    )
    last_layer = kept[-1]
    kept[-1] = last_layer.model_copy(update={"prompt": last_layer.prompt + background_note})

    return schema.model_copy(update={
        "character_layers": kept,
        "total_layers": 1 + len(kept),
    })


def check_needs_revision(critique: LayeredSceneImageCritiqueSchema) -> bool:
    """Return True if any score < 7 or critique says needs_revision."""
    min_score = min(
        critique.location_modification_score,
        critique.character_placement_score,
        critique.no_redundancy_score,
        critique.composition_score,
        critique.action_clarity_score,
    )
    return critique.needs_revision or min_score < 7


def resolve_ids(schema: LayeredSceneImagePromptSchema, codex: dict) -> LayeredSceneImagePromptSchema:
    """Ensure location_id and character_ids are resolved from codex."""
    # Resolve location ID if missing
    location_id = schema.location_id
    if not location_id:
        location_id = _lookup_location_id(schema.location_name, codex)

    # Resolve character IDs if missing
    updated_layers = []
    for cl in schema.character_layers:
        char_id = cl.character_id
        if not char_id:
            # Try to find by name
            characters = codex.get("story", {}).get("characters", [])
            for char in characters:
                if char.get("name", "").lower().strip() == cl.character_name.lower().strip():
                    char_id = char.get("id", "")
                    break
        if not char_id:
            print(f"  [WARN] Character '{cl.character_name}' not found in codex characters")
        updated_layers.append(cl.model_copy(update={"character_id": char_id}))

    return schema.model_copy(update={
        "location_id": location_id,
        "character_layers": updated_layers,
    })


def build_character_description(character_name: str, codex: dict) -> str:
    """Build a physical description string for a character from codex data.

    Image models need visual descriptors (hair, eyes, build, clothing) — not names.
    This extracts the physical fields and returns a comma-separated description.
    """
    characters = codex.get("story", {}).get("characters", [])
    for char in characters:
        if char.get("name", "").lower().strip() == character_name.lower().strip():
            physical = char.get("physical", {})
            parts = []
            gender = char.get("gender", "")
            if gender:
                parts.append(f"a {gender}")
            height = physical.get("height", "")
            build = physical.get("build", "")
            if height or build:
                body = ", ".join(filter(None, [height, build]))
                parts.append(body)
            hair = physical.get("hair_color", "") or physical.get("hair", "")
            if hair:
                # Only append "hair" if the value is just a color (no descriptors)
                parts.append(f"{hair} hair" if len(hair.split()) <= 3 else hair)
            eyes = physical.get("eye_color", "") or physical.get("eyes", "")
            if eyes:
                parts.append(f"{eyes} eyes" if len(eyes.split()) <= 3 else eyes)
            skin = physical.get("skin_tone", "")
            if skin:
                parts.append(f"{skin} skin" if len(skin.split()) <= 3 else skin)
            features = physical.get("distinguishing_features", "")
            if features:
                parts.append(features)
            clothing = char.get("clothing", "")
            if clothing:
                parts.append(f"wearing {clothing}")
            if parts:
                return ", ".join(parts) + "."
    return ""


def format_layered_result(
    schema: LayeredSceneImagePromptSchema,
    critique_history: list[dict],
    revision_count: int,
    codex: dict,
) -> dict:
    """Convert schema + metadata into the final codex-ready dict.

    Enriches each character layer prompt with the character's physical description
    from the codex, so image models can render the character without a reference image.
    """
    final_scores = {}
    if critique_history:
        last = critique_history[-1]
        final_scores = {
            "location_modification": last.get("location_modification_score"),
            "character_placement": last.get("character_placement_score"),
            "no_redundancy": last.get("no_redundancy_score"),
            "composition": last.get("composition_score"),
            "action_clarity": last.get("action_clarity_score"),
            "overall": last.get("overall_score"),
        }

    # Enrich character layer prompts with physical descriptions from codex
    enriched_layers = []
    for cl in schema.character_layers:
        char_desc = build_character_description(cl.character_name, codex)
        layer_dict = cl.model_dump()
        if char_desc:
            layer_dict["prompt"] = f"{char_desc} {cl.prompt}"
        enriched_layers.append(layer_dict)

    return {
        "prompt_type": "layered",
        "location_name": schema.location_name,
        "location_id": schema.location_id,
        "location_layer": schema.location_layer.model_dump(),
        "character_layers": enriched_layers,
        "scene_summary": schema.scene_summary,
        "composition_notes": schema.composition_notes,
        "mood_lighting": schema.mood_lighting,
        "total_layers": schema.total_layers,
        "revision_count": revision_count,
        "final_scores": final_scores,
        "critique_history": critique_history,
    }


# =============================================================================
# Orchestrator
# =============================================================================

def generate_layered_scene_image_prompt(
    scene_data: dict,
    act_number: int,
    codex: dict,
    visual_style: dict | None = None,
    model: str = DEFAULT_MODEL,
    max_revisions: int = 2,
) -> dict:
    """Generate a layered scene image prompt using composer + critic workflow.

    Each function called does exactly one thing:
    - create agents → build prompt → run composer → enforce limits
    - loop: build critique → run critic → check → build revision → run composer
    - resolve IDs → format result

    Args:
        scene_data: Scene dict with location, characters, text
        act_number: Act/chapter number for context
        codex: Full codex with characters and locations
        visual_style: Visual style dict with name, prefix, suffix
        model: LLM model to use
        max_revisions: Maximum revision cycles (default 2)

    Returns:
        Dict with prompt_type="layered", location_layer, character_layers, etc.
    """
    max_layers = get_max_character_layers()
    scene_num = scene_data.get("scene_number", "?")
    location = scene_data.get("location", "Unknown")
    print(f"      Creating layered scene prompt for scene {scene_num} at {location}...")

    # 1. Create agents
    composer_agent = create_layered_composer_agent(codex, model)
    critic_agent = create_layered_critic_agent(codex, model)

    # 2. Initial composition
    prompt = build_composer_prompt(scene_data, act_number, visual_style)
    current = run_composer(composer_agent, prompt)
    current = enforce_character_limit(current, max_layers)

    # 3. Critique-revision loop
    critique_history = []
    revision_count = 0

    for i in range(max_revisions):
        print(f"        Critique cycle {i + 1}/{max_revisions}...")

        crit_prompt = build_critique_prompt(current, scene_data, visual_style)
        critique = run_critic(critic_agent, crit_prompt)

        critique_dict = critique.model_dump()
        critique_dict["cycle"] = i + 1
        critique_history.append(critique_dict)

        if not check_needs_revision(critique):
            print(f"        Approved! Overall: {critique.overall_score:.1f}/10")
            break

        if i < max_revisions - 1:
            min_score = min(
                critique.location_modification_score,
                critique.character_placement_score,
                critique.no_redundancy_score,
                critique.composition_score,
                critique.action_clarity_score,
            )
            print(f"        Revising (min score: {min_score:.1f})...")
            rev_prompt = build_revision_prompt(current, critique, scene_data, visual_style)
            current = run_composer(composer_agent, rev_prompt)
            current = enforce_character_limit(current, max_layers)
            revision_count += 1

    # 4. Finalize
    current = resolve_ids(current, codex)
    return format_layered_result(current, critique_history, revision_count, codex)
