"""
Chapter Image Prompt Agents - Generate one representative image prompt per chapter.

Uses LangGraph ReAct agents with tools to retrieve character and location descriptions
from the codex, then generates hyper-detailed cinematic prompts without using
character names (only physical descriptions, since the model doesn't know who is who).

Key Features:
- One image per CHAPTER (not per scene) - captures the chapter's essence
- Uses `response_format` for guaranteed structured output
- Tools for retrieving character/location data from codex
- Composer + Critic workflow with revision loop

Workflow:
1. ChapterImageComposerAgent - Uses tools to fetch char/loc data, generates prompt
2. ChapterImageCriticAgent - Uses tools to validate prompts against codex data
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
        Use this to get accurate details for describing characters in chapter prompts.
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
        Use this to get accurate setting details for chapter prompts.
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
# Chapter Image Composer Agent (with Tools)
# =============================================================================

COMPOSER_SYSTEM_PROMPT = """You are a MASTER cinematic image prompt engineer specializing in creating representative CHAPTER images.

Your task is to create ONE HYPER-DETAILED prompt that captures the essence of an entire CHAPTER.
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
   - Use get_character_description for each featured character to get their physical appearance
   - Use get_location_description to get the main location details AND its ID
   - IMPORTANT: Save the character NAMES (not roles!) and IDs for your output fields

3. **CAPTURE THE CHAPTER'S KEY MOMENT** - Choose the most visually compelling moment:
   - The emotional peak of the chapter
   - The dramatic confrontation
   - The pivotal action or turning point
   - The most visually interesting scene

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
- **location_name**: The main location name from codex
- **location_id**: The location ID from get_location_description tool
- **characters_in_scene**: ACTUAL CHARACTER NAMES from the codex, NOT role descriptions!
  - WRONG: ["the protagonist", "the antagonist"]
  - RIGHT: ["Yara Ridgewell", "Quillon Blackwood"]
- **character_ids**: The character IDs from the tools

Remember: The model will receive character reference images, so focus on what they're DOING
and WEARING in THIS specific chapter, plus the environment around them."""


CRITIC_SYSTEM_PROMPT = """You are a CRITICAL reviewer of AI chapter image prompts.

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


class ChapterImageComposerAgent:
    """
    Creates detailed chapter image prompts using tools to fetch codex data.

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

    def create_chapter_prompt(
        self,
        chapter_data: dict,
        visual_style: dict = None
    ) -> SceneImagePromptSchema:
        """
        Generate a representative image prompt for a chapter.

        The agent will use tools to fetch character/location descriptions,
        then generate hyper-detailed prompts with guaranteed structured output.

        Args:
            chapter_data: Chapter dict with chapter_number, chapter_title, scenes[]
            visual_style: Visual style dict with name, prefix, suffix

        Returns:
            SceneImagePromptSchema with the chapter prompt
        """
        chapter_num = chapter_data.get("chapter_number", 1)
        chapter_title = chapter_data.get("chapter_title", f"Chapter {chapter_num}")
        scenes = chapter_data.get("scenes", [])

        # Collect all unique characters and locations from chapter scenes
        all_characters = set()
        all_locations = set()
        scene_summaries = []

        for scene in scenes:
            # Collect characters
            for char in scene.get("characters_present", []):
                all_characters.add(char)
            # Collect locations
            if scene.get("location"):
                all_locations.add(scene.get("location"))
            # Get prose snippets as summaries
            prose = scene.get("prose", "")
            if prose:
                scene_summaries.append(prose[:300])

        # Build chapter context
        chapter_context = {
            "chapter_number": chapter_num,
            "chapter_title": chapter_title,
            "characters": list(all_characters),
            "locations": list(all_locations),
            "scene_count": len(scenes),
            "scene_summaries": scene_summaries[:3],  # Max 3 summaries
        }

        chapter_json = json.dumps(chapter_context, indent=2)

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

        user_prompt = f"""Generate ONE representative image prompt for this CHAPTER.

## CHAPTER DATA:
{chapter_json}
{style_info}
## INSTRUCTIONS:

1. FIRST: Use get_character_description tool for EACH main character in the chapter
2. SECOND: Use get_location_description tool for the PRIMARY location
3. THIRD: Generate the prompt based on the retrieved data

Choose the most VISUALLY COMPELLING moment from the chapter:
- What is the key dramatic beat?
- What poses/expressions capture the emotion?
- What composition tells the story?

CRITICAL RULES:
- NEVER use character names - only physical descriptions from the tools
- Prompt: 300-500 words, single paragraph
- START with style prefix, END with style suffix (if provided)
- Focus on the MAIN characters (protagonist, antagonist) if present"""

        # Run the ReAct agent - structured_response is guaranteed via response_format
        result = self.agent.invoke({
            "messages": [
                {"role": "system", "content": COMPOSER_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ]
        })

        # With response_format, output is guaranteed in structured_response
        return result["structured_response"]

    def revise_chapter_prompt(
        self,
        original: SceneImagePromptSchema,
        critique: SceneImageCritiqueSchema,
        chapter_data: dict,
        visual_style: dict = None
    ) -> SceneImagePromptSchema:
        """
        Revise chapter prompt based on critic feedback.

        Args:
            original: Original prompt to revise
            critique: Critic's evaluation with scores and suggestions
            chapter_data: Original chapter data for reference
            visual_style: Visual style dict with name, prefix, suffix

        Returns:
            Revised SceneImagePromptSchema
        """
        suggestions = "\n".join(f"- {s}" for s in critique.suggestions)

        # Collect characters from chapter
        all_characters = set()
        for scene in chapter_data.get("scenes", []):
            for char in scene.get("characters_present", []):
                all_characters.add(char)

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

        prompt = f"""REVISE this chapter image prompt based on critic feedback.

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

## CHAPTER DATA (reference):
Chapter: {chapter_data.get("chapter_title", "Unknown")}
Characters: {list(all_characters)}
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
# Chapter Image Critic Agent (with Tools)
# =============================================================================

class ChapterImageCriticAgent:
    """
    Critiques chapter image prompts for accuracy against codex data.

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
        chapter_prompt: SceneImagePromptSchema,
        chapter_data: dict,
        visual_style: dict = None
    ) -> SceneImageCritiqueSchema:
        """
        Evaluate chapter prompt for accuracy and quality.

        Uses tools to verify descriptions match codex data with guaranteed structured output.

        Args:
            chapter_prompt: The prompt to critique
            chapter_data: Original chapter data for reference
            visual_style: Visual style dict with name, prefix, suffix

        Returns:
            SceneImageCritiqueSchema with scores and suggestions
        """
        # Collect characters from chapter
        all_characters = set()
        for scene in chapter_data.get("scenes", []):
            for char in scene.get("characters_present", []):
                all_characters.add(char)

        characters = list(all_characters)

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

        prompt = f"""CRITICALLY EVALUATE this chapter image prompt.

## CHAPTER IMAGE PROMPT:
{chapter_prompt.prompt}

## CHAPTER DATA:
Chapter: {chapter_data.get("chapter_title", "Unknown")}
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

def _collect_chapter_characters(chapter_data: dict, codex: dict) -> tuple[list[str], list[str]]:
    """
    Collect all character names and IDs from a chapter's scenes.

    Returns:
        tuple of (character_names, character_ids)
    """
    characters_codex = codex.get("story", {}).get("characters", [])
    all_chars = set()

    for scene in chapter_data.get("scenes", []):
        for char in scene.get("characters_present", []):
            all_chars.add(char)
        # Also check character_ids if present
        for char_id in scene.get("character_ids", []):
            # Find name from ID
            for c in characters_codex:
                if c.get("id") == char_id:
                    all_chars.add(c.get("name", ""))

    names = []
    ids = []

    for char_name in all_chars:
        if not char_name:
            continue
        name_lower = char_name.lower().strip()
        for c in characters_codex:
            if c.get("name", "").lower().strip() == name_lower:
                names.append(c.get("name"))
                if c.get("id"):
                    ids.append(c["id"])
                break

    return names, ids


def _get_primary_location(chapter_data: dict, codex: dict) -> tuple[str, str]:
    """
    Get the primary (most frequent) location in a chapter.

    Returns:
        tuple of (location_name, location_id)
    """
    locations_codex = codex.get("story", {}).get("locations", [])
    location_counts = {}

    for scene in chapter_data.get("scenes", []):
        loc = scene.get("location", "")
        if loc:
            location_counts[loc] = location_counts.get(loc, 0) + 1

    if not location_counts:
        return "Unknown", ""

    # Get most frequent location
    primary_loc = max(location_counts, key=location_counts.get)

    # Look up ID
    loc_id = ""
    name_lower = primary_loc.lower().strip()
    for loc in locations_codex:
        loc_name = loc.get("name", "").lower().strip()
        if loc_name == name_lower or name_lower in loc_name or loc_name in name_lower:
            loc_id = loc.get("id", "")
            primary_loc = loc.get("name", primary_loc)  # Use exact name from codex
            break

    return primary_loc, loc_id


def generate_chapter_image_prompt(
    chapter_data: dict,
    codex: dict,
    visual_style: dict = None,
    model: str = DEFAULT_MODEL,
    max_revisions: int = 2,
) -> dict:
    """
    Generate a representative image prompt for a chapter using composer + critic workflow.

    Uses ReAct agents with tools and guaranteed structured output via response_format.

    Args:
        chapter_data: Chapter dict with chapter_number, chapter_title, scenes[]
        codex: Full codex with characters and locations
        visual_style: Visual style dict with name, prefix, suffix, description
        model: LLM model to use
        max_revisions: Maximum revision cycles (default 2)

    Returns:
        Dict with:
        - prompt: The chapter image prompt
        - chapter_number: Chapter number
        - chapter_title: Chapter title
        - location_name: Primary location
        - location_id: Location ID from codex
        - characters_in_scene: Characters in chapter
        - character_ids: Character IDs from codex
        - scene_summary: Brief summary of chapter content
        - composition_notes: Composition notes
        - mood_lighting: Lighting/mood description
        - revision_count: Number of revisions made
        - final_scores: Final critique scores
        - critique_history: All critiques for metadata
    """
    composer = ChapterImageComposerAgent(codex=codex, model=model)
    critic = ChapterImageCriticAgent(codex=codex, model=model, temperature=0.3)

    chapter_num = chapter_data.get("chapter_number", 1)
    chapter_title = chapter_data.get("chapter_title", f"Chapter {chapter_num}")
    print(f"      Creating chapter image prompt for {chapter_title}...")

    # Step 1: Initial composition
    current_prompt = composer.create_chapter_prompt(chapter_data, visual_style)
    critique_history = []
    revision_count = 0

    # Step 2: Critic + revision loop
    for i in range(max_revisions):
        print(f"        Critique round {i + 1}...")
        critique = critic.critique(current_prompt, chapter_data, visual_style)
        critique_history.append({
            "round": i + 1,
            "scores": {
                "character_accuracy": critique.character_accuracy_score,
                "location_accuracy": critique.location_accuracy_score,
                "no_names": critique.no_names_score,
                "visual_detail": critique.visual_detail_score,
                "composition": critique.composition_score,
            },
            "needs_revision": critique.needs_revision,
            "suggestions": critique.suggestions,
        })

        if not critique.needs_revision:
            print(f"        Passed critique with scores: {critique.character_accuracy_score}/{critique.location_accuracy_score}/{critique.no_names_score}")
            break

        print(f"        Revising (scores: char={critique.character_accuracy_score}, loc={critique.location_accuracy_score}, names={critique.no_names_score})...")
        current_prompt = composer.revise_chapter_prompt(current_prompt, critique, chapter_data, visual_style)
        revision_count += 1

    # Get final critique scores
    final_critique = critique_history[-1] if critique_history else {}
    final_scores = final_critique.get("scores", {
        "character_accuracy": 7,
        "location_accuracy": 7,
        "no_names": 10,
        "visual_detail": 7,
        "composition": 7,
    })

    # Calculate overall score
    scores = list(final_scores.values())
    final_scores["overall"] = sum(scores) / len(scores) if scores else 7.0

    # Get character and location info
    char_names, char_ids = _collect_chapter_characters(chapter_data, codex)
    loc_name, loc_id = _get_primary_location(chapter_data, codex)

    # Use prompt data if available, fallback to our lookups
    result_location = current_prompt.location_name if current_prompt.location_name else loc_name
    result_loc_id = current_prompt.location_id if current_prompt.location_id else loc_id
    result_chars = current_prompt.characters_in_scene if current_prompt.characters_in_scene else char_names
    result_char_ids = current_prompt.character_ids if current_prompt.character_ids else char_ids

    return {
        "prompt": current_prompt.prompt,
        "chapter_number": chapter_num,
        "chapter_title": chapter_title,
        "location_name": result_location,
        "location_id": result_loc_id,
        "characters_in_scene": result_chars,
        "character_ids": result_char_ids,
        "scene_summary": current_prompt.scene_summary,
        "composition_notes": current_prompt.composition_notes,
        "mood_lighting": current_prompt.mood_lighting,
        "revision_count": revision_count,
        "final_scores": final_scores,
        "critique_history": critique_history,
    }
