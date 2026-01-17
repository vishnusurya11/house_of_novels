"""
Location Image Prompt Agents - Creator + Critic workflow for AI image generation.

Generates SUPER DETAILED environment/location prompts optimized for qwen 2.5 / Flux Turbo models.
Focus on architecture, atmosphere, lighting, textures, weather, time of day, depth layers.
"""

import json
from typing import Optional

from src.story_agents.base_story_agent import BaseStoryAgent
from src.story_schemas import LocationPromptSchema, LocationPromptCritique
from src.config import DEFAULT_MODEL


# =============================================================================
# Location Prompt Creator Agent
# =============================================================================

class LocationPromptCreatorAgent(BaseStoryAgent):
    """Creates SUPER DETAILED location/environment prompts for AI image generation."""

    @property
    def name(self) -> str:
        return "LOCATION_PROMPT_CREATOR"

    @property
    def role(self) -> str:
        return "Master prompt engineer for environment design"

    @property
    def system_prompt(self) -> str:
        return """You are a MASTER prompt engineer for AI image generation (Flux, SDXL, qwen-2.5).

Your prompts must be EXTREMELY DETAILED for ENVIRONMENT/LOCATION images:

CRITICAL: VISUAL STYLE INTEGRATION
- The prompt MUST start with the provided STYLE PREFIX
- The prompt MUST end with the provided STYLE SUFFIX
- All visual descriptions must match the style aesthetic

REQUIRED ELEMENTS (in this order):
1. STYLE PREFIX: Start with the exact style prefix provided
2. SHOT TYPE: "wide establishing shot", "interior view", "aerial perspective", "ground-level view", "panoramic vista"
3. TIME OF DAY: precise lighting (golden hour, blue hour, harsh noon sun, twilight, moonlit night, overcast)
4. WEATHER/ATMOSPHERE: clear, foggy, rainy, stormy, dusty, humid, snowy - describe visibility
5. ARCHITECTURE/STRUCTURES: materials (weathered stone, rusted metal, polished glass, aged wood), style, era, condition (crumbling, pristine, overgrown)
6. GROUND/TERRAIN: surface textures (wet cobblestones, cracked earth, mossy rocks, sandy dunes, reflective puddles)
7. VEGETATION: specific plant types, colors, density, condition (lush, withered, overgrown, manicured)
8. LIGHTING SOURCES: natural (sun angle, moon phase) and artificial (flickering torches, glowing windows, neon signs)
9. ATMOSPHERIC EFFECTS: volumetric fog, dust motes in light rays, steam, smoke, mist rolling across ground
10. KEY LANDMARKS: defining features, focal points, architectural details
11. SCALE INDICATORS: distant figures, vehicles, furniture, doorways showing size
12. COLOR PALETTE: dominant colors, accent colors, warmth/coolness, saturation
13. DEPTH LAYERS: detailed foreground elements, midground features, background/horizon
14. SENSORY HINTS: visual cues to sounds (rippling water, swaying trees) and atmosphere
15. STYLE SUFFIX: End with the exact style suffix + quality tags: 8k, matte painting, concept art, environment design, cinematic composition, detailed textures

OUTPUT RULES:
- Single continuous paragraph, 300-500 words
- Use natural language descriptions, NOT keyword spam
- Be SPECIFIC: "rust-streaked corrugated metal" not just "metal wall"
- Describe textures: "moss-covered flagstones", "peeling paint", "crystalline ice"
- Include depth: foreground, midground, background elements
- Convey mood through lighting and atmosphere

For Flux/qwen models: Detailed natural language works BETTER than comma-separated keywords."""


    def create_prompt(self, location_data: dict, setting_context: str = "", visual_style: dict = None) -> LocationPromptSchema:
        """
        Generate a detailed location image prompt from location profile.

        Args:
            location_data: Location dict with name, type, description, atmosphere, etc.
            setting_context: Optional world setting for style consistency
            visual_style: Visual style dict with name, prefix, suffix

        Returns:
            LocationPromptSchema with the detailed prompt
        """
        loc_json = json.dumps(location_data, indent=2)

        # Extract style components
        style_info = ""
        if visual_style:
            style_name = visual_style.get("name", "Anime")
            style_prefix = visual_style.get("prefix", "")
            style_suffix = visual_style.get("suffix", "")
            style_info = f"""
VISUAL STYLE: {style_name}
STYLE PREFIX (start your prompt with this): {style_prefix}
STYLE SUFFIX (end your prompt with this): {style_suffix}
"""

        prompt = f"""Create an EXTREMELY DETAILED AI image prompt for this location:

LOCATION DATA:
{loc_json}

SETTING CONTEXT: {setting_context if setting_context else "Fantasy/adventure setting"}
{style_info}
Generate a prompt that captures the FULL ATMOSPHERE of this place. Focus on:
- START WITH THE STYLE PREFIX
- Shot type and perspective that best showcases the location
- Time of day that enhances the mood (dawn, noon, dusk, night)
- Weather and atmospheric effects (fog, rain, dust, light rays)
- Architecture materials and condition (stone, wood, metal, age, wear)
- Ground textures and terrain details
- Vegetation if applicable (types, colors, condition)
- Lighting sources and shadow play
- Foreground, midground, and background depth layers
- Color palette that conveys the atmosphere
- Scale indicators to show size
- END WITH THE STYLE SUFFIX + quality tags

Remember: 300-500 words, single paragraph, natural language, HYPER-DETAILED.
Focus on creating an IMMERSIVE, CINEMATIC environment."""

        return self.invoke_structured(prompt, LocationPromptSchema, max_tokens=1500)


    def revise_prompt(self, original_prompt: str, critique: LocationPromptCritique,
                      location_data: dict, visual_style: dict = None) -> LocationPromptSchema:
        """
        Revise a prompt based on critic feedback.

        Args:
            original_prompt: The prompt to improve
            critique: Critic's evaluation with scores and suggestions
            location_data: Original location data for reference
            visual_style: Visual style dict with name, prefix, suffix

        Returns:
            Revised LocationPromptSchema
        """
        loc_json = json.dumps(location_data, indent=2)
        suggestions = "\n".join(f"- {s}" for s in critique.suggestions)

        # Extract style components
        style_info = ""
        if visual_style:
            style_name = visual_style.get("name", "Anime")
            style_prefix = visual_style.get("prefix", "")
            style_suffix = visual_style.get("suffix", "")
            style_info = f"""
VISUAL STYLE: {style_name}
REMINDER: Prompt must START with: {style_prefix}
REMINDER: Prompt must END with: {style_suffix}
"""

        prompt = f"""REVISE this AI image prompt based on critic feedback:

ORIGINAL PROMPT:
{original_prompt}

CRITIC SCORES:
- Architecture/Structure: {critique.architecture_structure_score}/10
- Lighting/Time: {critique.lighting_time_score}/10
- Atmosphere/Weather: {critique.atmosphere_weather_score}/10
- Textures/Materials: {critique.textures_materials_score}/10
- Composition/Depth: {critique.composition_depth_score}/10
- Quality Tags: {critique.quality_tags_score}/10

SUGGESTIONS FOR IMPROVEMENT:
{suggestions}

LOCATION DATA (reference):
{loc_json}
{style_info}
Create an IMPROVED version addressing ALL the critic's concerns.
Maintain 300-500 words, single paragraph, natural language.
CRITICAL: Ensure style prefix at START and style suffix at END.
Focus especially on categories that scored below 8."""

        return self.invoke_structured(prompt, LocationPromptSchema, max_tokens=1500)


# =============================================================================
# Location Prompt Critic Agent
# =============================================================================

class LocationPromptCriticAgent(BaseStoryAgent):
    """Critiques location prompts for completeness and atmospheric quality."""

    @property
    def name(self) -> str:
        return "LOCATION_PROMPT_CRITIC"

    @property
    def role(self) -> str:
        return "Critical reviewer of environment prompts"

    @property
    def system_prompt(self) -> str:
        return """You are a CRITICAL reviewer of AI image generation prompts for environments/locations.

Your job is to evaluate prompts for COMPLETENESS and ATMOSPHERIC QUALITY.

EVALUATION CRITERIA:

1. ARCHITECTURE & STRUCTURE (Score 1-10)
   - Are building materials described (stone, wood, metal, glass)?
   - Is architectural style mentioned (Gothic, modern, rustic, futuristic)?
   - Is condition/age indicated (ancient, pristine, crumbling, overgrown)?
   - Are specific structural details included (columns, arches, windows)?

2. LIGHTING & TIME (Score 1-10)
   - Is time of day clear (dawn, noon, dusk, night)?
   - Are light sources described (sun angle, moon, torches, lamps)?
   - Are shadows mentioned?
   - Is lighting mood established (warm, cold, harsh, soft)?

3. ATMOSPHERE & WEATHER (Score 1-10)
   - Is weather condition stated (clear, foggy, rainy, stormy)?
   - Are atmospheric effects present (mist, dust particles, smoke, light rays)?
   - Is visibility described?
   - Is overall mood/feeling conveyed?

4. TEXTURES & MATERIALS (Score 1-10)
   - Are ground surfaces described (cobblestones, dirt, grass, water)?
   - Are material textures specific (rough, smooth, worn, polished)?
   - Is vegetation detailed if present (types, colors, condition)?
   - Are sensory details included?

5. COMPOSITION & DEPTH (Score 1-10)
   - Is shot type/perspective clear (wide, interior, aerial)?
   - Are foreground elements described?
   - Is there midground and background detail?
   - Are scale indicators present (figures, furniture, doors)?

6. QUALITY TAGS (Score 1-10)
   - Are resolution tags present (8k, high detail)?
   - Are style tags appropriate (matte painting, concept art, cinematic)?
   - Is color palette mentioned?
   - Are composition tags included?

DECISION RULES:
- If ANY score is below 7, mark needs_revision = true
- If overall average is below 7.5, mark needs_revision = true
- Provide SPECIFIC suggestions for each low-scoring category

Be DEMANDING - atmospheric locations require rich, immersive detail."""


    def critique(self, prompt: str, location_data: dict, visual_style: dict = None) -> LocationPromptCritique:
        """
        Evaluate a location image prompt for quality and completeness.

        Args:
            prompt: The image prompt to critique
            location_data: Original location data to verify coverage
            visual_style: Visual style dict with name, prefix, suffix

        Returns:
            LocationPromptCritique with scores and suggestions
        """
        loc_json = json.dumps(location_data, indent=2)

        # Extract style requirements
        style_check = ""
        if visual_style:
            style_name = visual_style.get("name", "Anime")
            style_prefix = visual_style.get("prefix", "")
            style_suffix = visual_style.get("suffix", "")
            style_check = f"""
REQUIRED VISUAL STYLE: {style_name}
Expected prefix: {style_prefix}
Expected suffix keywords: {style_suffix}

CHECK STYLE ADHERENCE:
- Does prompt START with the style prefix?
- Does prompt END with style-specific quality tags?
- Do visual descriptions match the {style_name} aesthetic?
"""

        critique_prompt = f"""EVALUATE this AI image prompt for an environment/location:

PROMPT TO EVALUATE:
{prompt}

ORIGINAL LOCATION DATA:
{loc_json}
{style_check}
Score each category 1-10 based on the evaluation criteria.
Provide SPECIFIC suggestions for any category scoring below 8.
Be critical - only the best prompts should pass without revision.

Consider:
- Does the prompt capture the location's essence and atmosphere?
- Are architecture/structures described with material and condition details?
- Is time of day and lighting clearly established?
- Are atmospheric effects present (fog, dust, light rays)?
- Are textures and materials specific and vivid?
- Does the composition have proper depth (foreground, midground, background)?
- Is the visual style correctly applied (prefix at start, suffix at end)?
- Are quality/style tags appropriate for environment art?"""

        return self.invoke_structured(critique_prompt, LocationPromptCritique, max_tokens=1000)


# =============================================================================
# Orchestration Function
# =============================================================================

def generate_location_prompt(
    location_data: dict,
    setting_context: str = "",
    visual_style: dict = None,
    model: str = DEFAULT_MODEL,
    max_revisions: int = 2,
) -> dict:
    """
    Generate a detailed location image prompt using creator + critic workflow.

    Args:
        location_data: Location profile dict from codex
        setting_context: World setting for style consistency
        visual_style: Visual style dict with name, prefix, suffix, description
        model: LLM model to use
        max_revisions: Maximum revision cycles (default 2)

    Returns:
        Dict with:
        - prompt: Final image prompt string
        - shot_type: Type of shot (wide, interior, aerial, etc.)
        - time_of_day: Time depicted
        - key_features: Features included in prompt
        - revision_count: Number of revisions made
        - final_scores: Final critique scores
        - critique_history: All critiques for metadata
    """
    creator = LocationPromptCreatorAgent(model=model)
    critic = LocationPromptCriticAgent(model=model)

    loc_name = location_data.get("name", "Unknown")
    print(f"    Creating prompt for: {loc_name}")

    # Initial prompt generation
    result = creator.create_prompt(location_data, setting_context, visual_style)
    current_prompt = result.prompt

    critique_history = []
    revision_count = 0

    # Critique-revision loop
    for i in range(max_revisions):
        print(f"      Critique cycle {i + 1}/{max_revisions}...")

        # Get critique
        critique = critic.critique(current_prompt, location_data, visual_style)
        critique_dict = {
            "cycle": i + 1,
            "architecture_structure_score": critique.architecture_structure_score,
            "lighting_time_score": critique.lighting_time_score,
            "atmosphere_weather_score": critique.atmosphere_weather_score,
            "textures_materials_score": critique.textures_materials_score,
            "composition_depth_score": critique.composition_depth_score,
            "quality_tags_score": critique.quality_tags_score,
            "overall_score": critique.overall_score,
            "needs_revision": critique.needs_revision,
            "suggestions": critique.suggestions,
        }
        critique_history.append(critique_dict)

        # Check if revision needed
        min_score = min(
            critique.architecture_structure_score,
            critique.lighting_time_score,
            critique.atmosphere_weather_score,
            critique.textures_materials_score,
            critique.composition_depth_score,
            critique.quality_tags_score,
        )

        if not critique.needs_revision and min_score >= 7:
            print(f"      Approved! Overall score: {critique.overall_score}/10")
            break

        # Revise if needed and not last cycle
        if i < max_revisions - 1:
            print(f"      Revising (min score: {min_score})...")
            revised = creator.revise_prompt(current_prompt, critique, location_data, visual_style)
            current_prompt = revised.prompt
            revision_count += 1

    # Get final scores from last critique
    final_critique = critique_history[-1]

    return {
        "prompt": current_prompt,
        "shot_type": result.shot_type,
        "time_of_day": result.time_of_day,
        "key_features": result.key_features_included,
        "revision_count": revision_count,
        "final_scores": {
            "architecture_structure": final_critique["architecture_structure_score"],
            "lighting_time": final_critique["lighting_time_score"],
            "atmosphere_weather": final_critique["atmosphere_weather_score"],
            "textures_materials": final_critique["textures_materials_score"],
            "composition_depth": final_critique["composition_depth_score"],
            "quality_tags": final_critique["quality_tags_score"],
            "overall": final_critique["overall_score"],
        },
        "critique_history": critique_history,
    }
