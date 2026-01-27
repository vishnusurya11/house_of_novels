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
