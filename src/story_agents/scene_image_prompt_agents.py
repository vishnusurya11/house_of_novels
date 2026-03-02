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
            "characters": scene_data.get("_resolved_character_names") or scene_data.get("characters", []),
            "text": scene_data.get("text", "")[:1000],  # Truncate long prose
        }, indent=2)

        # Extract injected context (deterministically resolved from codex)
        char_context = scene_data.get("_injected_character_context", "")
        loc_context = scene_data.get("_injected_location_context", "")

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
Characters: {scene_data.get("_resolved_character_names") or scene_data.get("characters", [])}

{scene_json}

## CHARACTER DETAILS (from codex — use these EXACT physical descriptions):
{char_context}

## LOCATION DETAILS (from codex — use these details):
{loc_context}
{style_info}
## INSTRUCTIONS:

1. The character and location details above are PRE-RESOLVED from the codex.
   You may also use the tools to get additional details if needed.
2. Generate the prompt using the physical descriptions provided above.
3. You can use the tools to verify or get extra details, but the above context is authoritative.

Choose the most VISUALLY COMPELLING moment from the scene:
- What is the key dramatic beat?
- What poses/expressions capture the emotion?
- What composition tells the story?

CRITICAL RULES:
- NEVER use character names - only physical descriptions
- EVERY named character listed above MUST be described in the prompt using their physical traits
- Prompt: 300-500 words, single paragraph
- START with style prefix, END with style suffix (if provided)
- Include ALL characters listed above in the scene"""

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

def _resolve_scene_characters(scene_data: dict, codex: dict) -> tuple[list[str], list[str], list[dict]]:
    """Deterministically resolve characters from scene data against codex.

    Uses characters_present (or characters) from the scene — these are ground truth
    set by Phase 1, not something the LLM should guess.

    Returns:
        (names, ids, full_profiles) where full_profiles includes physical descriptions
    """
    characters = codex.get("story", {}).get("characters", [])
    char_by_name: dict[str, dict] = {}
    for char in characters:
        char_by_name[char.get("name", "").lower().strip()] = char

    scene_chars = scene_data.get("characters_present") or scene_data.get("characters") or []

    names: list[str] = []
    ids: list[str] = []
    profiles: list[dict] = []

    for char_name in scene_chars:
        name_lower = char_name.lower().strip()
        # Exact match first
        char = char_by_name.get(name_lower)
        # Partial match fallback
        if not char:
            for key, c in char_by_name.items():
                if name_lower in key or key in name_lower:
                    char = c
                    break
        if char:
            names.append(char.get("name", char_name))
            char_id = char.get("id") or char.get("character_id", "")
            ids.append(char_id)
            profiles.append(char)
        # Skip unnamed/generic characters (e.g. "community members", "guards")

    return names, ids, profiles


def _resolve_scene_location(scene_data: dict, codex: dict) -> tuple[str, str, dict]:
    """Deterministically resolve location from scene data against codex.

    Uses location_id from scene data first (exact), falls back to name matching.

    Returns:
        (location_name, location_id, location_profile)
    """
    locations = codex.get("story", {}).get("locations", [])
    scene_loc_id = scene_data.get("location_id", "")
    scene_loc_name = scene_data.get("location", "")

    # Exact ID match (most reliable)
    if scene_loc_id:
        for loc in locations:
            loc_id = loc.get("id") or loc.get("location_id", "")
            if loc_id == scene_loc_id:
                return loc.get("name", scene_loc_name), loc_id, loc

    # Name match fallback
    name_lower = scene_loc_name.lower().strip()
    for loc in locations:
        loc_name = loc.get("name", "").lower().strip()
        if loc_name == name_lower:
            loc_id = loc.get("id") or loc.get("location_id", "")
            return loc.get("name", scene_loc_name), loc_id, loc

    return scene_loc_name, scene_loc_id, {}


def _pronouns_for_gender(gender: str) -> str:
    """Return pronoun set string from a gender value."""
    g = gender.lower().strip()
    if g in ("male", "man", "boy"):
        return "he/him/his"
    if g in ("female", "woman", "girl"):
        return "she/her/her"
    return "they/them/their"


def _build_character_context(profiles: list[dict]) -> str:
    """Build a character context block from resolved profiles for injection into agent prompt."""
    if not profiles:
        return "No named characters in this scene."
    blocks = []
    for char in profiles:
        physical = char.get("physical", {})
        char_id = char.get("id") or char.get("character_id", "")
        gender = char.get("gender", "unknown")
        pronouns = _pronouns_for_gender(gender)
        parts = [
            f"**{char.get('name', 'Unknown')}** (ID: {char_id})",
            f"  Role: {char.get('role_in_story', 'unknown')}",
            f"  Gender: {gender}, Pronouns: {pronouns}, Age: {char.get('age', 'unknown')}",
            f"  Height: {physical.get('height', 'unknown')}, Build: {physical.get('build', 'unknown')}",
            f"  Hair: {physical.get('hair_color', '') or physical.get('hair', 'unknown')}",
            f"  Eyes: {physical.get('eye_color', '') or physical.get('eyes', 'unknown')}",
            f"  Skin: {physical.get('skin_tone', 'unknown')}",
            f"  Distinguishing features: {physical.get('distinguishing_features', 'none')}",
            f"  Clothing: {char.get('clothing', 'unknown')}",
        ]
        blocks.append("\n".join(parts))
    return "\n\n".join(blocks)


def _build_location_context(loc_profile: dict) -> str:
    """Build a location context block from resolved profile for injection into agent prompt."""
    if not loc_profile:
        return "Location details not found in codex."
    loc_id = loc_profile.get("id") or loc_profile.get("location_id", "")
    parts = [
        f"**{loc_profile.get('name', 'Unknown')}** (ID: {loc_id})",
        f"  Type: {loc_profile.get('type', 'unknown')}",
        f"  Description: {loc_profile.get('description', 'none')}",
        f"  Atmosphere: {loc_profile.get('atmosphere', 'none')}",
        f"  Key features: {loc_profile.get('key_features', [])}",
    ]
    return "\n".join(parts)


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
    # Deterministically resolve characters and location from scene data (ground truth)
    char_names, char_ids, char_profiles = _resolve_scene_characters(scene_data, codex)
    loc_name, loc_id, loc_profile = _resolve_scene_location(scene_data, codex)

    # Inject resolved context into scene_data so the agent prompt includes it
    enriched_scene = dict(scene_data)
    enriched_scene["_injected_character_context"] = _build_character_context(char_profiles)
    enriched_scene["_injected_location_context"] = _build_location_context(loc_profile)
    enriched_scene["_resolved_character_names"] = char_names
    enriched_scene["_resolved_location_name"] = loc_name

    composer = SceneImageComposerAgent(codex=codex, model=model)
    critic = SceneImageCriticAgent(codex=codex, model=model, temperature=0.3)

    scene_num = scene_data.get("scene_number", "?")
    location = scene_data.get("location", "Unknown")
    print(f"      Creating scene image prompt for scene {scene_num} at {location}...")
    print(f"        Characters (from codex): {char_names}")
    print(f"        Location (from codex): {loc_name} ({loc_id})")

    # Initial prompt generation (guaranteed structured output)
    current = composer.create_scene_prompt(enriched_scene, act_number, visual_style)

    critique_history = []
    revision_count = 0

    # Critique-revision loop
    for i in range(max_revisions):
        print(f"        Critique cycle {i + 1}/{max_revisions}...")

        # Get critique (guaranteed structured output)
        critique = critic.critique(current, enriched_scene, visual_style)

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
            current = composer.revise_scene_prompt(current, critique, enriched_scene, visual_style)
            revision_count += 1

    # Validate: check that named characters are described in the prompt
    prompt_lower = current.prompt.lower()
    missing_chars = []
    for profile in char_profiles:
        physical = profile.get("physical", {})
        # Check for at least one distinguishing physical trait in the prompt
        hair = (physical.get("hair_color", "") or physical.get("hair", "")).lower()
        eyes = (physical.get("eye_color", "") or physical.get("eyes", "")).lower()
        clothing = profile.get("clothing", "").lower()
        found = False
        for trait in [hair, eyes, clothing]:
            if trait and len(trait) > 2 and trait in prompt_lower:
                found = True
                break
        if not found:
            missing_chars.append(profile.get("name", "Unknown"))

    if missing_chars:
        print(f"        [WARN] Characters not described in prompt: {missing_chars}")

    # Get final scores from last critique
    final_critique = critique_history[-1]

    # Use deterministic scene data for output fields — NOT agent guesses
    return {
        "prompt": current.prompt,
        "location_name": loc_name,
        "location_id": loc_id,
        "characters_in_scene": char_names,
        "character_ids": char_ids,
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
    ShotTypeSpec,
    CharacterStagingHint,
)
from src.config import get_max_character_layers, get_shot_selection_config


# =============================================================================
# Shot Type Rules & Character Action Templates
# =============================================================================

SHOT_TYPE_RULES: dict[str, dict[str, str]] = {
    "wide_establishing": {
        "description": "Wide establishing shot — environment dominates, character 5-20% of frame",
        "camera_distance": "24mm wide-angle cinematic framing",
        "character_scale": "character occupies 5-20% of frame, small figure against vast environment",
        "composition_rule": "rule of thirds, environment dominates, deep depth of field, layered foreground-midground-background",
        "negative_composition": "NOT: close-up, portrait, headshot, bust shot, upper body only, centered face, character dominating frame, zoomed-in composition",
    },
    "full_shot": {
        "description": "Full shot — full body visible, character 20-35% of frame",
        "camera_distance": "35mm standard lens",
        "character_scale": "full body visible, character occupies 20-35% of frame",
        "composition_rule": "character framed head-to-toe with environment context, moderate depth of field",
        "negative_composition": "NOT: close-up, portrait, headshot, bust shot, reference sheet style",
    },
    "medium_wide": {
        "description": "Medium wide shot — characters visible knees-up, body language readable",
        "camera_distance": "50mm standard lens",
        "character_scale": "characters visible from knees up, body language clearly readable",
        "composition_rule": "two-person framing, balanced spacing, body language as storytelling",
        "negative_composition": "NOT: close-up, portrait, headshot, zoomed-in face",
    },
    "two_shot": {
        "description": "Two-shot — tension between two people, spacing conveys relationship",
        "camera_distance": "50mm standard lens, shallow depth of field",
        "character_scale": "two characters framed together, spacing conveys relationship tension",
        "composition_rule": "balanced two-person framing, negative space between characters conveys tension or intimacy",
        "negative_composition": "NOT: single portrait, close-up, crowd scene",
    },
    "over_shoulder": {
        "description": "Over-the-shoulder — foreground silhouette, power imbalance or observation",
        "camera_distance": "85mm telephoto, shallow depth of field",
        "character_scale": "foreground character as silhouette/blur, background character in focus",
        "composition_rule": "foreground silhouette framing background subject, power imbalance, voyeuristic framing",
        "negative_composition": "NOT: both characters equally visible, wide shot, centered composition",
    },
    "crowd_tension": {
        "description": "Crowd tension shot — focal character embedded in or separated from group",
        "camera_distance": "35mm wide-angle",
        "character_scale": "focal character distinct amid crowd, either isolated or engulfed",
        "composition_rule": "focal character differentiated from crowd by lighting, position, or action; crowd as environmental pressure",
        "negative_composition": "NOT: empty background, single portrait, two-shot only",
    },
    "tracking_motion": {
        "description": "Tracking motion shot — character moving through space, caught mid-stride",
        "camera_distance": "35mm, slight motion blur on background",
        "character_scale": "character mid-stride or mid-action, dynamic pose, environment streaks or blurs",
        "composition_rule": "leading space in direction of movement, dynamic diagonal lines, motion blur on environment",
        "negative_composition": "NOT: static pose, standing still, centered symmetrical composition, portrait",
    },
    "insert_detail": {
        "description": "Insert detail shot — symbolic object, scar, clue, or significant detail",
        "camera_distance": "100mm macro or tight telephoto",
        "character_scale": "object or detail fills 50-80% of frame, minimal character visible",
        "composition_rule": "extreme shallow depth of field, object dominates, hand or partial body as context",
        "negative_composition": "NOT: wide shot, full body, environment focus, multiple characters",
    },
}

ACTION_TEMPLATES: dict[str, dict[str, str]] = {
    "action": {
        "body_language": "dynamic, weight shifted forward, muscles tensed",
        "physical_action_hint": "caught mid-motion, reacting physically to threat or opportunity",
        "attention_direction": "locked on the immediate danger or target",
    },
    "dialogue": {
        "body_language": "leaning toward or away from conversation partner, hands gesturing",
        "physical_action_hint": "mid-gesture, hands emphasizing a point or reaching out",
        "attention_direction": "eyes on the person being addressed",
    },
    "introspection": {
        "body_language": "turned inward, shoulders slightly curved, arms close to body",
        "physical_action_hint": "touching own face or hands, staring at a fixed point",
        "attention_direction": "gazing into middle distance or down at own hands",
    },
    "confrontation": {
        "body_language": "squared off, chin raised, space between combatants charged",
        "physical_action_hint": "pointing, stepping forward, or blocking a path",
        "attention_direction": "eyes locked on the opponent",
    },
    "revelation": {
        "body_language": "frozen mid-motion, breath caught, hands suspended",
        "physical_action_hint": "recoiling, hand raised to mouth, or gripping something for support",
        "attention_direction": "staring at the source of the revelation",
    },
    "transition": {
        "body_language": "in motion, purposeful stride, looking ahead",
        "physical_action_hint": "walking, climbing, or passing through a doorway",
        "attention_direction": "looking toward destination",
    },
}

ARC_STATE_MODIFIERS: dict[str, dict[str, str]] = {
    "confident": {
        "body_language_mod": "upright posture, open stance",
        "attention_mod": "direct gaze",
    },
    "doubt": {
        "body_language_mod": "fidgeting, weight shifting",
        "attention_mod": "eyes darting, avoiding direct contact",
    },
    "grief": {
        "body_language_mod": "hunched, arms wrapped around self",
        "attention_mod": "eyes downcast or closed",
    },
    "anger": {
        "body_language_mod": "rigid, jaw clenched, fists tight",
        "attention_mod": "glaring, intense focus",
    },
    "fear": {
        "body_language_mod": "shrinking, pulling back",
        "attention_mod": "eyes wide, scanning for escape",
    },
    "resolve": {
        "body_language_mod": "straightened spine, chin lifted",
        "attention_mod": "steady forward gaze",
    },
    "betrayal": {
        "body_language_mod": "stiffened, stepping back",
        "attention_mod": "staring at betrayer with shock or hurt",
    },
    "hope": {
        "body_language_mod": "leaning forward slightly, shoulders relaxing",
        "attention_mod": "eyes brightening, looking up",
    },
}


# =============================================================================
# Shot Selection & Character Staging (pure functions)
# =============================================================================


def select_shot_type(scene_data: dict) -> ShotTypeSpec:
    """Select the optimal camera shot type based on scene metadata.

    Pure function: deterministic, no LLM calls. Uses scene_type, beat_name,
    character count, tropes, and thematic_beat to pick the best framing.

    Args:
        scene_data: Scene dict with scene_type, beat_name, characters_present,
                    tropes_manifesting, thematic_beat, scene_causality

    Returns:
        ShotTypeSpec with shot_type, camera_distance, character_scale, etc.
    """
    scene_type = scene_data.get("scene_type", "dialogue")
    beat_name = scene_data.get("beat_name", "")
    chars = scene_data.get("characters_present") or scene_data.get("characters", [])
    char_count = len(chars)
    tropes = scene_data.get("tropes_manifesting", [])
    tropes_lower = " ".join(str(t) for t in tropes).lower()
    thematic_beat = scene_data.get("thematic_beat") or {}
    if not isinstance(thematic_beat, dict):
        thematic_beat = {}
    causality = scene_data.get("scene_causality") or {}
    if not isinstance(causality, dict):
        causality = {}

    # Check config for forced override
    shot_config = get_shot_selection_config()
    force = shot_config.get("force_shot_type")
    if force and force in SHOT_TYPE_RULES:
        rules = SHOT_TYPE_RULES[force]
        return ShotTypeSpec(
            shot_type=force,
            shot_description=rules["description"],
            camera_distance=rules["camera_distance"],
            character_scale=rules["character_scale"],
            composition_rule=rules["composition_rule"],
            negative_composition=rules["negative_composition"],
        )

    shot_key = "full_shot"  # default

    # Priority 1: Insert detail (rare — symbolic revelation at story inflection)
    if (beat_name in ("Catalyst", "Midpoint")
            and scene_type == "revelation"
            and char_count <= 1):
        shot_key = "insert_detail"

    # Priority 2: Wide establishing — location-first scenes
    elif (beat_name in ("Opening Image", "Final Image", "Theme Stated")
          or scene_type == "transition"
          or (scene_type == "introspection" and char_count <= 1)):
        shot_key = "wide_establishing"

    # Priority 3: Crowd tension — public/social scenes
    elif (any(kw in tropes_lower for kw in (
            "public", "crowd", "ceremony", "riot", "gathering", "speech", "unrest"))
          or char_count >= 4):
        shot_key = "crowd_tension"

    # Priority 4: Tracking motion — character in action, reacting
    elif (scene_type == "action"
          and causality.get("caused_by", "")):
        shot_key = "tracking_motion"

    # Priority 5: Over-shoulder — confrontation with power dynamic
    elif (scene_type == "confrontation"
          and char_count == 2
          and thematic_beat.get("thematic_perspective")):
        shot_key = "over_shoulder"

    # Priority 6: Two-shot — two characters in dialogue or confrontation
    elif char_count == 2 and scene_type in ("dialogue", "confrontation"):
        shot_key = "two_shot"

    # Priority 7: Medium wide — two characters, other scene types
    elif char_count == 2:
        shot_key = "medium_wide"

    # Priority 8: Full shot (default)

    rules = SHOT_TYPE_RULES[shot_key]
    return ShotTypeSpec(
        shot_type=shot_key,
        shot_description=rules["description"],
        camera_distance=rules["camera_distance"],
        character_scale=rules["character_scale"],
        composition_rule=rules["composition_rule"],
        negative_composition=rules["negative_composition"],
    )


def infer_character_staging(
    character_name: str,
    character_id: str,
    scene_data: dict,
    is_pov: bool,
) -> CharacterStagingHint:
    """Infer staging hints for a character based on scene metadata.

    Uses scene_type, character_arc_beats/progression, tropes to generate
    body language, action, and attention hints. These guide the LLM composer.

    Args:
        character_name: Character name from codex
        character_id: Character ID
        scene_data: Full scene dict with metadata
        is_pov: Whether this is the POV character

    Returns:
        CharacterStagingHint with staging_role, physical_action, body_language, etc.
    """
    scene_type = scene_data.get("scene_type", "dialogue")
    template = ACTION_TEMPLATES.get(scene_type, ACTION_TEMPLATES["dialogue"])

    body_language = template["body_language"]
    physical_action = template["physical_action_hint"]
    attention_direction = template["attention_direction"]
    staging_role = f"{'focal POV character' if is_pov else 'supporting character'} in {scene_type} scene"

    # Overlay emotional state from character_arc_beats (detailed format)
    arc_beats = scene_data.get("character_arc_beats") or []
    matched_arc = False
    for arc in arc_beats:
        if not isinstance(arc, dict):
            continue
        if arc.get("character_name", "").lower().strip() == character_name.lower().strip():
            emotional_state = arc.get("emotional_state", "").lower()
            arc_milestone = arc.get("arc_milestone", "")

            for keyword, mods in ARC_STATE_MODIFIERS.items():
                if keyword in emotional_state:
                    body_language = mods["body_language_mod"]
                    attention_direction = mods["attention_mod"]
                    matched_arc = True
                    break

            if arc_milestone:
                staging_role += f" — {arc_milestone}"
            break

    # Fallback to character_arc_progression (simpler format)
    if not matched_arc:
        arc_prog = scene_data.get("character_arc_progression") or []
        for prog in arc_prog:
            if not isinstance(prog, dict):
                continue
            if prog.get("character_name", "").lower().strip() == character_name.lower().strip():
                arc_state = prog.get("arc_state", "").lower()
                for keyword, mods in ARC_STATE_MODIFIERS.items():
                    if keyword in arc_state:
                        body_language = mods["body_language_mod"]
                        attention_direction = mods["attention_mod"]
                        break
                break

    return CharacterStagingHint(
        character_name=character_name,
        character_id=character_id,
        staging_role=staging_role,
        physical_action=physical_action,
        body_language=body_language,
        attention_direction=attention_direction,
        camera_awareness="unaware",
    )


# =============================================================================
# System Prompts
# =============================================================================

LAYERED_COMPOSER_SYSTEM_PROMPT = """You are a MASTER cinematic scene composition engineer.

Your task is to create a LAYERED image generation plan for a scene. Each layer will be
applied sequentially to build the final scene image using an image edit model.

## HOW LAYERED GENERATION WORKS:
1. Layer 1 (Location): Single-image edit — modifies the pre-generated location image
   for this scene's context (time of day, weather, damage, atmospheric effects).
2. Layer 2+ (Characters): Two-image edit — image 1 is the evolving scene (previous
   layer result), image 2 is the character portrait. The edit prompt tells the model
   how to place image 2 into image 1.

## IMPORTANT — STRUCTURED FIELDS DRIVE THE FINAL PROMPT:
The structured fields you fill in (position_in_frame, action_pose, emotional_expression,
body_language, attention_direction) will be automatically composed into the final edit
prompt sent to the image model. Write the `prompt` field as a brief creative supplement
(30-80 words) — the structured fields handle placement and action.

## CAMERA SHOT TYPES:
You will receive a MANDATORY shot type specification with your scene data. This determines:
- How much of the frame characters occupy (character scale)
- Camera distance and lens choice
- Overall composition rules
- What framing to AVOID

Follow the shot type EXACTLY. Examples:
- wide_establishing = characters 5-20% of frame, environment dominates
- full_shot = full body visible, 20-35% of frame
- two_shot = both characters framed together, spacing conveys tension
- crowd_tension = focal character distinct amid crowd
- tracking_motion = character mid-stride, dynamic pose

Set shot_type and camera_notes fields in your output to match the specified shot.

## CHARACTER STAGING:
Characters must ALWAYS be doing something specific. NEVER describe a character as simply
"standing" or "present in the scene." Every character needs:
- A specific PHYSICAL ACTION (gripping, reaching, turning, running, gesturing)
- BODY LANGUAGE that conveys their emotional state (tense shoulders, clenched fists)
- A clear ATTENTION DIRECTION (where they are looking — never at the camera)
- camera_awareness: "unaware" — characters do NOT look at the camera or pose

Use the staging hints provided in the scene data as a starting point, then enhance
with scene-specific details. The image should capture a MOMENT, not a character lineup.

## CHARACTER POSITIONING:
- Maximum 3 foreground characters with individual layers. Any additional characters
  should be mentioned as background figures in the last character layer's prompt.
- Horizontal placement (center/left/right of image) is assigned automatically in
  post-processing, so focus on action and depth in position_in_frame.
- Layout: 1 char = center; 2 chars = left + right; 3 chars = center + left + right.
- The primary/focal character is always placed first.

## CRITICAL RULES:

1. **LOCATION LAYER** — Describe ONLY modifications to the existing location image.
   - The base location image already exists. Do NOT describe the location from scratch.
   - Focus on: time changes (night vs day), weather (rain, fog, snow), damage (fire,
     destruction), atmospheric effects (dust, smoke), crowd presence, lighting shifts.
   - If no modifications needed (same conditions as the base location), set
     requires_modification=false with a minimal prompt like "No changes needed."
   - Keep the prompt to 30-80 words.

2. **CHARACTER LAYERS** — Describe ONLY action, pose, and position. NO physical descriptions.
   - The character's portrait (image 2) provides their physical appearance automatically.
   - Do NOT describe hair color, eye color, clothing, height, build, skin tone, etc.
   - DO describe: what they are doing, body language, where they stand in the frame,
     what they are looking at, how they interact with the environment or other characters.
   - For character 2+: describe position relative to character(s) already placed.
   - Fill in position_in_frame, action_pose, emotional_expression, staging_role,
     body_language, attention_direction, camera_awareness fields precisely.
   - Order characters by narrative importance: primary/focal character FIRST.
   - Keep each prompt to 30-80 words.
   - **PRONOUN CONSISTENCY**: Use pronouns that match the character's stated gender.
     Male = he/him/his. Female = she/her/her. Non-binary = they/them/their.
     NEVER use mismatched pronouns (e.g., "her" for a male character).

3. **USE THE TOOLS** to retrieve character and location data from the codex:
   - Use lookup_character_by_role to find character names and IDs from role descriptions
   - Use get_character_description to get character IDs
   - Use get_location_description to get the location ID
   - You need these IDs for cross-referencing with pre-generated images.

4. **COMPOSITION** — Think about the overall composition across all layers:
   - Follow the shot type's composition rules and character scale
   - Where does each character stand relative to the camera and each other?
   - What is the visual focal point?
   - Do the character positions create natural interaction?
   - Consider depth: foreground, midground, background placement.

## OUTPUT FIELDS:
- shot_type: Copy from the shot type specification provided
- camera_notes: Camera distance and framing from the shot specification
- location_id: From get_location_description tool (e.g., 'loc_001')
- character_layers: Ordered list — primary character FIRST
- Each character_layer needs character_name, character_id, position_in_frame,
  action_pose, emotional_expression, staging_role, body_language,
  attention_direction, camera_awareness
- total_layers: 1 (location) + number of character layers"""


LAYERED_CRITIC_SYSTEM_PROMPT = """You are a CRITICAL reviewer of layered scene image prompts.

These prompts are designed for an image edit model where:
- Layer 1 modifies an existing location image (single-image edit)
- Layers 2+ add characters: image 1 = previous layer result, image 2 = character portrait

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

6. **SHOT_ADHERENCE** (Score 1-10)
   - Does the composition match the specified shot type?
   - Are characters at the correct SCALE for this shot type?
     (e.g., wide_establishing = characters 5-20% of frame, NOT dominating)
   - Is the camera distance appropriate for the shot type?
   - Score LOW if a "wide_establishing" shot has characters dominating the frame
   - Score LOW if a "two_shot" only shows one character prominently

7. **CHARACTER_ACTION** (Score 1-10) — CRITICAL!
   - Is every character DOING something specific?
   - Score LOW if any character is described as simply "standing" or "present"
   - Are body_language descriptions specific (not generic like "neutral")?
   - Is attention_direction specified (not facing the camera)?
   - Are characters "unaware" of the camera (candid, not posing)?
   - Does the image feel like a captured story MOMENT, not a character showcase?

## OVERALL SCORE:
- Calculate overall_score as the average of all 7 component scores above.

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

def build_composer_prompt(
    scene_data: dict,
    act_number: int,
    visual_style: dict | None,
    shot_spec: ShotTypeSpec | None = None,
    staging_hints: list[CharacterStagingHint] | None = None,
) -> str:
    """Build the user prompt string for the layered composer agent."""
    scene_json = json.dumps({
        "scene_number": scene_data.get("scene_number"),
        "location": scene_data.get("location"),
        "time_of_day": scene_data.get("time_of_day", ""),
        "characters": scene_data.get("_resolved_character_names") or scene_data.get("characters", []),
        "pov_character": scene_data.get("pov_character", ""),
        "text": scene_data.get("text", "")[:1000],
    }, indent=2)

    # Extract injected context (deterministically resolved from codex)
    char_context = scene_data.get("_injected_character_context", "")
    loc_context = scene_data.get("_injected_location_context", "")

    style_info = ""
    if visual_style:
        style_info = f"""
## VISUAL STYLE: {visual_style.get("name", "Anime")}
Note: Style is applied at the image generation level, not in layer prompts.
Keep layer prompts focused on content/action, not artistic style."""

    # Shot type section
    shot_section = ""
    if shot_spec:
        neg = f"\nAVOID: {shot_spec.negative_composition}" if shot_spec.negative_composition else ""
        shot_section = f"""
## CAMERA SHOT TYPE (MANDATORY — follow these framing rules):
Shot: {shot_spec.shot_type} — {shot_spec.shot_description}
Camera: {shot_spec.camera_distance}
Character Scale: {shot_spec.character_scale}
Composition: {shot_spec.composition_rule}{neg}
"""

    # Staging hints section
    staging_section = ""
    if staging_hints:
        hint_lines = []
        for hint in staging_hints:
            hint_lines.append(
                f"**{hint.character_name}** ({hint.staging_role}):\n"
                f"  - Action: {hint.physical_action}\n"
                f"  - Body language: {hint.body_language}\n"
                f"  - Looking at: {hint.attention_direction}\n"
                f"  - Camera awareness: {hint.camera_awareness}"
            )
        staging_section = (
            "\n## CHARACTER STAGING HINTS (use these to guide character actions):\n"
            + "\n\n".join(hint_lines) + "\n"
        )

    # Shot-specific instructions
    shot_instructions = ""
    if shot_spec:
        shot_instructions = f"""
4. SHOT TYPE: This scene MUST use {shot_spec.shot_type} framing.
   - Characters must match the scale: {shot_spec.character_scale}
   - Use camera distance: {shot_spec.camera_distance}
   - Set shot_type="{shot_spec.shot_type}" and camera_notes in your output

5. CHARACTER STAGING: Each character MUST be DOING something specific.
   - Use the staging hints above as a starting point
   - Characters should NOT be standing still facing the camera
   - Body language and attention direction must be specific
   - All characters: camera_awareness = "unaware" (candid, not posing)
"""

    return f"""Generate a LAYERED image composition plan for this scene.

## SCENE DATA:
Act {act_number}, Scene {scene_data.get("scene_number")}
Location: {scene_data.get("location")}
Time of Day: {scene_data.get("time_of_day", "unknown")}
POV Character: {scene_data.get("pov_character", "unknown")}
Characters: {scene_data.get("_resolved_character_names") or scene_data.get("characters", [])}

{scene_json}

## CHARACTER DETAILS (pre-resolved from codex):
{char_context}

## LOCATION DETAILS (pre-resolved from codex):
{loc_context}
{shot_section}{staging_section}{style_info}
## INSTRUCTIONS:

1. The character and location details above are PRE-RESOLVED from the codex.
   You may also use the tools to verify or get additional details.
2. Create the layered prompt plan using the provided character names and IDs:

   - LOCATION LAYER: What changes from the base location image for THIS scene?
     (time of day, weather, atmospheric effects, damage, etc.)
     If the base location already matches, set requires_modification=false.

   - CHARACTER LAYERS (one per character, primary/POV character FIRST):
     What is each character DOING? Where do they STAND in the frame?
     What is their EXPRESSION? How do they INTERACT with the scene/each other?
     Do NOT describe their appearance — the portrait reference handles that.
     Use the character NAMES and IDs from the details above for each layer.
     CRITICAL: Match pronouns to each character's stated gender and pronouns above.

3. Set total_layers = 1 + number of character layers
{shot_instructions}
CRITICAL: Keep each layer prompt to 100-200 words. Be specific and actionable."""


def build_revision_prompt(
    original: LayeredSceneImagePromptSchema,
    critique: LayeredSceneImageCritiqueSchema,
    scene_data: dict,
    visual_style: dict | None,
    shot_spec: ShotTypeSpec | None = None,
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

    shot_reminder = ""
    if shot_spec:
        neg = f"\nAVOID: {shot_spec.negative_composition}" if shot_spec.negative_composition else ""
        shot_reminder = f"""
SHOT TYPE REMINDER: This scene uses {shot_spec.shot_type} framing.
Character scale: {shot_spec.character_scale}
Camera: {shot_spec.camera_distance}{neg}
"""

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
- Shot Adherence: {critique.shot_adherence_score}/10
- Character Action: {critique.character_action_score}/10

## SUGGESTIONS FOR IMPROVEMENT:
{suggestions}

## SCENE DATA (reference):
Location: {scene_data.get("location")}
Characters: {scene_data.get("characters", [])}
{shot_reminder}
FIRST: Use the tools to re-fetch character and location data for accuracy.
THEN: Create IMPROVED layered prompt addressing ALL the critic's concerns.

CRITICAL REMINDERS:
- Location layer: CHANGES only, not full description
- Character layers: ONLY action/pose/position — NO physical descriptions (no hair, eyes, clothing, build)
- The structured fields (position_in_frame, action_pose, emotional_expression, body_language) will be
  composed into the final edit prompt automatically — fill them in precisely
- Characters must be DOING something (not standing passively)
- Characters must NOT face the camera (camera_awareness = "unaware")
- Keep each layer prompt concise (30-80 words)"""


def build_critique_prompt(
    scene_prompt: LayeredSceneImagePromptSchema,
    scene_data: dict,
    visual_style: dict | None,
    shot_spec: ShotTypeSpec | None = None,
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
            f"      staging_role: {cl.staging_role}\n"
            f"      body_language: {cl.body_language}\n"
            f"      attention_direction: {cl.attention_direction}\n"
            f"      camera_awareness: {cl.camera_awareness}\n"
            f"      is_primary: {cl.is_primary}\n"
            f"      prompt: {cl.prompt}"
        )
    char_info = "\n".join(char_summaries)

    characters = scene_data.get("characters", [])

    shot_check = ""
    if shot_spec:
        shot_check = f"""
## SHOT TYPE CHECK:
Expected shot: {shot_spec.shot_type} — {shot_spec.shot_description}
Expected character scale: {shot_spec.character_scale}
Expected camera: {shot_spec.camera_distance}

- Does the composition match the shot type?
- Are characters at the correct scale for this shot?
"""

    return f"""CRITICALLY EVALUATE this layered scene image prompt.

## LOCATION LAYER:
{loc_summary}

## CHARACTER LAYERS:
{char_info}

## SCENE DATA:
Location: {scene_data.get("location")}
Characters: {characters}
{shot_check}
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
- Are characters DOING something (not just "standing" or "present")?
- Is camera_awareness "unaware" for all characters (not facing camera)?
- Does the framing match the expected shot type?

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
        critique.shot_adherence_score,
        critique.character_action_score,
    )
    return critique.needs_revision or min_score < 7


def resolve_ids(
    schema: LayeredSceneImagePromptSchema,
    codex: dict,
    scene_data: dict | None = None,
) -> LayeredSceneImagePromptSchema:
    """Ensure location_id and character_ids are resolved from codex.

    If scene_data is provided, uses the deterministic scene-level data first
    (location_id, characters_present) before falling back to name matching.
    """
    # Resolve location ID — prefer scene data (ground truth)
    location_id = schema.location_id
    if not location_id and scene_data:
        _, loc_id, _ = _resolve_scene_location(scene_data, codex)
        location_id = loc_id
    if not location_id:
        # Last resort: name match from schema
        locations = codex.get("story", {}).get("locations", [])
        name_lower = schema.location_name.lower().strip()
        for loc in locations:
            loc_name = loc.get("name", "").lower().strip()
            if loc_name == name_lower:
                location_id = loc.get("id") or loc.get("location_id", "")
                break

    # Resolve character IDs — prefer exact name match
    updated_layers = []
    characters = codex.get("story", {}).get("characters", [])
    for cl in schema.character_layers:
        char_id = cl.character_id
        if not char_id:
            name_lower = cl.character_name.lower().strip()
            for char in characters:
                if char.get("name", "").lower().strip() == name_lower:
                    char_id = char.get("id") or char.get("character_id", "")
                    break
        if not char_id:
            print(f"  [WARN] Character '{cl.character_name}' not found in codex characters")
        updated_layers.append(cl.model_copy(update={"character_id": char_id}))

    return schema.model_copy(update={
        "location_id": location_id,
        "character_layers": updated_layers,
    })


def _enforce_scene_characters(
    schema: LayeredSceneImagePromptSchema,
    char_names: list[str],
    char_ids: list[str],
    max_layers: int,
) -> LayeredSceneImagePromptSchema:
    """Force character_layers to contain exactly the characters from scene data.

    The agent may generate layers for wrong characters or miss some.
    This post-processing step ensures the output matches ground truth:
    1. Keep layers that match expected characters (by name)
    2. Create placeholder layers for missing characters
    3. Remove layers for characters NOT in the expected list
    4. Respect max_layers limit, prioritizing primary/POV characters
    """
    if not char_names:
        return schema

    expected = {name.lower().strip(): (name, cid) for name, cid in zip(char_names, char_ids)}

    # Index existing agent layers by character name (lowered)
    agent_layers: dict[str, CharacterLayerPrompt] = {}
    for cl in schema.character_layers:
        agent_layers[cl.character_name.lower().strip()] = cl

    # Build final layer list in the order of expected characters
    final_layers: list[CharacterLayerPrompt] = []
    for i, (name_lower, (canon_name, canon_id)) in enumerate(expected.items()):
        existing = agent_layers.get(name_lower)
        if existing:
            # Agent got this character right — keep the layer, fix name/id
            final_layers.append(existing.model_copy(update={
                "character_name": canon_name,
                "character_id": canon_id,
            }))
        else:
            # Agent missed this character — create a placeholder layer
            is_first = i == 0
            final_layers.append(CharacterLayerPrompt(
                character_name=canon_name,
                character_id=canon_id,
                prompt=f"{canon_name} is present in this scene.",
                position_in_frame="center midground" if is_first else "right midground",
                action_pose="standing",
                emotional_expression="neutral",
                is_primary=is_first,
            ))
            print(f"  [WARN] Character '{canon_name}' was missing from agent output — added placeholder layer")

    # Respect max_layers limit
    if len(final_layers) > max_layers:
        kept = final_layers[:max_layers]
        excess = final_layers[max_layers:]
        excess_names = [cl.character_name for cl in excess]
        background_note = (
            f" Other characters present in the background: {', '.join(excess_names)}."
        )
        last_layer = kept[-1]
        kept[-1] = last_layer.model_copy(update={"prompt": last_layer.prompt + background_note})
        final_layers = kept

    return schema.model_copy(update={
        "character_layers": final_layers,
        "total_layers": 1 + len(final_layers),
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


def _compose_location_edit_prompt(
    layer: "LocationLayerPrompt",
    schema: LayeredSceneImagePromptSchema,
) -> str:
    """Compose a location edit prompt with time, weather, camera, and lighting.

    Location uses a single-image workflow (no second reference image).
    Weaves structured metadata into the prompt so the image model sees everything.
    """
    parts: list[str] = []
    parts.append(f"Set the scene to {layer.time_of_day}, {layer.weather_atmosphere}.")
    if schema.camera_notes:
        parts.append(f"Camera: {schema.shot_type}, {schema.camera_notes}.")
    if schema.mood_lighting:
        parts.append(f"Lighting: {schema.mood_lighting}.")
    parts.append(layer.prompt)
    return " ".join(parts)


def _compose_character_edit_prompt(
    layer: "CharacterLayerPrompt",
    layer_index: int,
    total_layers: int,
) -> str:
    """Compose a character edit prompt — short, clear placement instruction.

    Strictly about the new character: where to place it and what it's doing.
    No physical descriptions (portrait reference handles identity).
    image 1 = previous layer result, image 2 = new character portrait.

    Positions are deterministic based on character count:
      1 char  → center
      2 chars → left side, right side
      3 chars → center, left side, right side
    """
    # Deterministic position based on character count and layer index
    if total_layers == 1:
        side = "the center of"
    elif total_layers == 2:
        side = "the left side of" if layer_index == 0 else "the right side of"
    else:  # 3 characters
        if layer_index == 0:
            side = "the center of"
        elif layer_index == 1:
            side = "the left side of"
        else:
            side = "the right side of"

    # Intro: placement instruction — side is always set
    if layer_index == 0:
        intro = f"Place the person from image 2 on {side} image 1"
    else:
        char_ref = "characters" if layer_index > 1 else "character"
        intro = f"Place the person from image 2 on {side} image 1, near the {char_ref} already in image 1"

    # Action description — short, comma-separated
    actions: list[str] = []
    if layer.action_pose:
        actions.append(layer.action_pose)
    if layer.body_language:
        actions.append(layer.body_language)
    if layer.emotional_expression:
        actions.append(layer.emotional_expression)
    if layer.attention_direction and layer_index > 0:
        actions.append(layer.attention_direction)

    if actions:
        return f"{intro}, {', '.join(actions)}."
    return f"{intro}."


def format_layered_result(
    schema: LayeredSceneImagePromptSchema,
    critique_history: list[dict],
    revision_count: int,
    codex: dict,
) -> dict:
    """Convert schema + metadata into the final codex-ready dict.

    Composes short, clear edit-ready prompts from structured fields:
    - Location: weaves time, weather, camera/lens, lighting into prompt
    - Characters: "Place the person from image 2 in image 1, [action]"
    No physical descriptions — portrait references handle visual identity.
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
            "shot_adherence": last.get("shot_adherence_score"),
            "character_action": last.get("character_action_score"),
            "overall": last.get("overall_score"),
        }

    # Compose location edit prompt with inline metadata
    enriched_location = schema.location_layer.model_dump()
    enriched_location["prompt"] = _compose_location_edit_prompt(
        schema.location_layer, schema
    )

    # Compose short, clear character edit prompts (no physical descriptions)
    total_chars = len(schema.character_layers)
    enriched_layers = []
    for i, cl in enumerate(schema.character_layers):
        layer_dict = cl.model_dump()
        layer_dict["prompt"] = _compose_character_edit_prompt(cl, i, total_chars)
        enriched_layers.append(layer_dict)

    return {
        "prompt_type": "layered",
        "shot_type": schema.shot_type,
        "camera_notes": schema.camera_notes,
        "location_name": schema.location_name,
        "location_id": schema.location_id,
        "location_layer": enriched_location,
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

    # Deterministically resolve characters and location from scene data (ground truth)
    char_names, char_ids, char_profiles = _resolve_scene_characters(scene_data, codex)
    loc_name, loc_id, loc_profile = _resolve_scene_location(scene_data, codex)

    # Inject resolved context into scene_data so agent prompts include it
    enriched_scene = dict(scene_data)
    enriched_scene["_injected_character_context"] = _build_character_context(char_profiles)
    enriched_scene["_injected_location_context"] = _build_location_context(loc_profile)
    enriched_scene["_resolved_character_names"] = char_names
    enriched_scene["_resolved_location_name"] = loc_name

    print(f"      Creating layered scene prompt for scene {scene_num} at {location}...")
    print(f"        Characters (from codex): {char_names}")
    print(f"        Location (from codex): {loc_name} ({loc_id})")

    # Select shot type deterministically from scene metadata
    shot_config = get_shot_selection_config()
    shot_spec: ShotTypeSpec | None = None
    if shot_config.get("enabled", True):
        shot_spec = select_shot_type(enriched_scene)
        print(f"        Shot type: {shot_spec.shot_type} ({shot_spec.camera_distance})")

    # Infer character staging hints from scene metadata
    pov_char = scene_data.get("pov_character", "")
    staging_hints: list[CharacterStagingHint] = []
    for name, cid in zip(char_names, char_ids):
        is_pov = name.lower().strip() == pov_char.lower().strip()
        hint = infer_character_staging(name, cid, enriched_scene, is_pov)
        staging_hints.append(hint)

    # 1. Create agents
    composer_agent = create_layered_composer_agent(codex, model)
    critic_agent = create_layered_critic_agent(codex, model)

    # 2. Initial composition — pass shot_spec and staging_hints
    prompt = build_composer_prompt(enriched_scene, act_number, visual_style, shot_spec, staging_hints)
    current = run_composer(composer_agent, prompt)

    # Enforce shot_type in output (deterministic, not LLM-dependent)
    if shot_spec:
        current = current.model_copy(update={
            "shot_type": shot_spec.shot_type,
            "camera_notes": f"{shot_spec.camera_distance}, {shot_spec.character_scale}",
        })

    current = enforce_character_limit(current, max_layers)

    # 3. Critique-revision loop
    critique_history = []
    revision_count = 0

    for i in range(max_revisions):
        print(f"        Critique cycle {i + 1}/{max_revisions}...")

        crit_prompt = build_critique_prompt(current, enriched_scene, visual_style, shot_spec)
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
                critique.shot_adherence_score,
                critique.character_action_score,
            )
            print(f"        Revising (min score: {min_score:.1f})...")
            rev_prompt = build_revision_prompt(current, critique, enriched_scene, visual_style, shot_spec)
            current = run_composer(composer_agent, rev_prompt)

            # Re-enforce shot_type after revision
            if shot_spec:
                current = current.model_copy(update={
                    "shot_type": shot_spec.shot_type,
                    "camera_notes": f"{shot_spec.camera_distance}, {shot_spec.character_scale}",
                })

            current = enforce_character_limit(current, max_layers)
            revision_count += 1

    # 4. Finalize — use scene data for ID resolution
    current = resolve_ids(current, codex, scene_data=scene_data)

    # Override location with deterministic values from scene data
    current = current.model_copy(update={"location_id": loc_id, "location_name": loc_name})

    # Enforce character_layers match scene's characters_present (ground truth)
    current = _enforce_scene_characters(current, char_names, char_ids, max_layers)

    return format_layered_result(current, critique_history, revision_count, codex)
