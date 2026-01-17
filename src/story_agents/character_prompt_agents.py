"""
Character Image Prompt Agents - Creator + Critic workflow for AI image generation.

Generates SUPER DETAILED character prompts optimized for qwen 2.5 / Flux Turbo models.
Focus on CHARACTER ONLY (no background) - physical appearance, clothing, marks, expression.
"""

import json
from typing import Optional

from src.story_agents.base_story_agent import BaseStoryAgent
from src.story_schemas import CharacterPromptSchema, CharacterPromptCritique
from src.config import DEFAULT_MODEL


# =============================================================================
# Character Prompt Creator Agent
# =============================================================================

class CharacterPromptCreatorAgent(BaseStoryAgent):
    """Creates SUPER DETAILED character prompts for AI image generation."""

    @property
    def name(self) -> str:
        return "CHARACTER_PROMPT_CREATOR"

    @property
    def role(self) -> str:
        return "Master prompt engineer for character portraits"

    @property
    def system_prompt(self) -> str:
        return """You are a MASTER prompt engineer for AI image generation (Flux, SDXL, qwen-2.5).

Your prompts must be EXTREMELY DETAILED for CHARACTER PORTRAITS:

CRITICAL: VISUAL STYLE INTEGRATION
- The prompt MUST start with the provided STYLE PREFIX
- The prompt MUST end with the provided STYLE SUFFIX
- All visual descriptions must match the style aesthetic

REQUIRED ELEMENTS (in this order):
1. STYLE PREFIX: Start with the exact style prefix provided
2. SHOT TYPE: "medium shot portrait", "bust shot", "full body standing pose"
3. GENDER & AGE: precise description (e.g., "woman in her late twenties")
4. FACE DETAILS: face shape, skin tone, skin texture, complexion
5. EYES: color, shape, expression, lashes, eyebrows in detail
6. NOSE & MOUTH: shape, lips color, expression
7. HAIR: exact color, length, texture, style, bangs, partings, any highlights
8. DISTINGUISHING MARKS: scars, tattoos, birthmarks, piercings, jewelry - be specific about placement
9. EXPRESSION: emotional state, mood conveyed through face
10. POSE & POSTURE: body language, hand position, shoulder orientation
11. CLOTHING: EXTREMELY DETAILED - fabric type, color, pattern, fit, wear/tear, accessories, layers
12. LIGHTING: direction, quality, mood (e.g., "soft diffused front lighting with rim light")
13. STYLE SUFFIX: End with the exact style suffix + quality tags: 8k, highly detailed, professional portrait, sharp focus, cinematic

BACKGROUND: Mention briefly as solid color or simple gradient - the focus is CHARACTER.

OUTPUT RULES:
- Single continuous paragraph, 300-500 words
- Use natural language descriptions, NOT keyword spam
- Be SPECIFIC: "emerald green with gold flecks" not just "green eyes"
- Describe textures: "weathered leather", "gossamer silk", "rough-hewn cotton"
- Include micro-details: "slight crinkle around eyes", "calloused hands"

For Flux/qwen models: Detailed natural language works BETTER than comma-separated keywords."""


    def create_prompt(self, character_data: dict, setting_context: str = "", visual_style: dict = None) -> CharacterPromptSchema:
        """
        Generate a detailed character image prompt from character profile.

        Args:
            character_data: Character dict with name, physical, clothing, etc.
            setting_context: Optional world setting for style consistency
            visual_style: Visual style dict with name, prefix, suffix

        Returns:
            CharacterPromptSchema with the detailed prompt
        """
        char_json = json.dumps(character_data, indent=2)

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

        prompt = f"""Create an EXTREMELY DETAILED AI image prompt for this character:

CHARACTER DATA:
{char_json}

SETTING CONTEXT: {setting_context if setting_context else "Modern/contemporary setting"}
{style_info}
Generate a prompt that captures EVERY physical detail. Focus on:
- START WITH THE STYLE PREFIX
- Face structure, skin, eyes, lips, eyebrows in rich detail
- Hair color, style, texture, length with precision
- Clothing fabrics, colors, fit, condition, accessories
- Any scars, marks, jewelry, tattoos with exact placement
- Expression and pose that reflects their personality
- Lighting that enhances the character's mood
- END WITH THE STYLE SUFFIX + quality tags

Remember: 300-500 words, single paragraph, natural language, HYPER-DETAILED.
NO BACKGROUND description - just mention a solid color briefly."""

        return self.invoke_structured(prompt, CharacterPromptSchema, max_tokens=1500)


    def revise_prompt(self, original_prompt: str, critique: CharacterPromptCritique,
                      character_data: dict, visual_style: dict = None) -> CharacterPromptSchema:
        """
        Revise a prompt based on critic feedback.

        Args:
            original_prompt: The prompt to improve
            critique: Critic's evaluation with scores and suggestions
            character_data: Original character data for reference
            visual_style: Visual style dict with name, prefix, suffix

        Returns:
            Revised CharacterPromptSchema
        """
        char_json = json.dumps(character_data, indent=2)
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
- Face Detail: {critique.face_detail_score}/10
- Clothing Detail: {critique.clothing_detail_score}/10
- Distinguishing Marks: {critique.distinguishing_marks_score}/10
- Pose/Expression: {critique.pose_expression_score}/10
- Quality Tags: {critique.quality_tags_score}/10

SUGGESTIONS FOR IMPROVEMENT:
{suggestions}

CHARACTER DATA (reference):
{char_json}
{style_info}
Create an IMPROVED version addressing ALL the critic's concerns.
Maintain 300-500 words, single paragraph, natural language.
CRITICAL: Ensure style prefix at START and style suffix at END.
Focus especially on categories that scored below 8."""

        return self.invoke_structured(prompt, CharacterPromptSchema, max_tokens=1500)


# =============================================================================
# Character Prompt Critic Agent
# =============================================================================

class CharacterPromptCriticAgent(BaseStoryAgent):
    """Critiques character prompts for completeness and detail quality."""

    @property
    def name(self) -> str:
        return "CHARACTER_PROMPT_CRITIC"

    @property
    def role(self) -> str:
        return "Critical reviewer of AI image prompts"

    @property
    def system_prompt(self) -> str:
        return """You are a CRITICAL reviewer of AI image generation prompts for character portraits.

Your job is to evaluate prompts for COMPLETENESS and QUALITY of detail.

EVALUATION CRITERIA:

1. FACE DETAIL (Score 1-10)
   - Is face shape mentioned? Skin tone and texture?
   - Are eyes described in detail (color, shape, expression, lashes)?
   - Are eyebrows, nose, and lips described?
   - Are there micro-details (freckles, lines, pores)?

2. CLOTHING DETAIL (Score 1-10)
   - Is fabric type mentioned (silk, leather, cotton, linen)?
   - Are colors specific (not just "blue" but "deep navy" or "sky blue")?
   - Is fit described (loose, tailored, fitted)?
   - Are there accessories (belts, buttons, jewelry)?
   - Is condition mentioned (worn, pristine, tattered)?

3. DISTINGUISHING MARKS (Score 1-10)
   - Are scars, tattoos, birthmarks mentioned if character has them?
   - Is placement specific ("scar above left eyebrow")?
   - Is jewelry described (rings, necklaces, earrings)?
   - Are any unique features highlighted?

4. POSE & EXPRESSION (Score 1-10)
   - Is body posture described?
   - Is head position/angle mentioned?
   - Is emotional expression clear?
   - Are hands positioned?

5. QUALITY TAGS (Score 1-10)
   - Are resolution tags present (8k, high detail)?
   - Is lighting described?
   - Are style tags appropriate (professional portrait, cinematic)?
   - Is background mentioned (even if simple)?

DECISION RULES:
- If ANY score is below 7, mark needs_revision = true
- If overall average is below 7.5, mark needs_revision = true
- Provide SPECIFIC suggestions for each low-scoring category

Be DEMANDING - high quality prompts produce high quality images."""


    def critique(self, prompt: str, character_data: dict, visual_style: dict = None) -> CharacterPromptCritique:
        """
        Evaluate a character image prompt for quality and completeness.

        Args:
            prompt: The image prompt to critique
            character_data: Original character data to verify coverage
            visual_style: Visual style dict with name, prefix, suffix

        Returns:
            CharacterPromptCritique with scores and suggestions
        """
        char_json = json.dumps(character_data, indent=2)

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

        critique_prompt = f"""EVALUATE this AI image prompt for a character portrait:

PROMPT TO EVALUATE:
{prompt}

ORIGINAL CHARACTER DATA:
{char_json}
{style_check}
Score each category 1-10 based on the evaluation criteria.
Provide SPECIFIC suggestions for any category scoring below 8.
Be critical - only the best prompts should pass without revision.

Consider:
- Does the prompt capture ALL the character's physical details?
- Is the clothing described with fabric, color, and fit specifics?
- Are distinguishing marks (if any) clearly placed?
- Is the pose and expression vivid?
- Is the visual style correctly applied (prefix at start, suffix at end)?
- Are quality/style tags present?"""

        return self.invoke_structured(critique_prompt, CharacterPromptCritique, max_tokens=1000)


# =============================================================================
# Orchestration Function
# =============================================================================

def generate_character_prompt(
    character_data: dict,
    setting_context: str = "",
    visual_style: dict = None,
    model: str = DEFAULT_MODEL,
    max_revisions: int = 2,
) -> dict:
    """
    Generate a detailed character image prompt using creator + critic workflow.

    Args:
        character_data: Character profile dict from codex
        setting_context: World setting for style consistency
        visual_style: Visual style dict with name, prefix, suffix, description
        model: LLM model to use
        max_revisions: Maximum revision cycles (default 2)

    Returns:
        Dict with:
        - prompt: Final image prompt string
        - shot_type: Type of shot (bust, medium, full body)
        - key_features: Features included in prompt
        - revision_count: Number of revisions made
        - final_scores: Final critique scores
        - critique_history: All critiques for metadata
    """
    creator = CharacterPromptCreatorAgent(model=model)
    critic = CharacterPromptCriticAgent(model=model)

    char_name = character_data.get("name", "Unknown")
    print(f"    Creating prompt for: {char_name}")

    # Initial prompt generation
    result = creator.create_prompt(character_data, setting_context, visual_style)
    current_prompt = result.prompt

    critique_history = []
    revision_count = 0

    # Critique-revision loop
    for i in range(max_revisions):
        print(f"      Critique cycle {i + 1}/{max_revisions}...")

        # Get critique
        critique = critic.critique(current_prompt, character_data, visual_style)
        critique_dict = {
            "cycle": i + 1,
            "face_detail_score": critique.face_detail_score,
            "clothing_detail_score": critique.clothing_detail_score,
            "distinguishing_marks_score": critique.distinguishing_marks_score,
            "pose_expression_score": critique.pose_expression_score,
            "quality_tags_score": critique.quality_tags_score,
            "overall_score": critique.overall_score,
            "needs_revision": critique.needs_revision,
            "suggestions": critique.suggestions,
        }
        critique_history.append(critique_dict)

        # Check if revision needed
        min_score = min(
            critique.face_detail_score,
            critique.clothing_detail_score,
            critique.distinguishing_marks_score,
            critique.pose_expression_score,
            critique.quality_tags_score,
        )

        if not critique.needs_revision and min_score >= 7:
            print(f"      Approved! Overall score: {critique.overall_score}/10")
            break

        # Revise if needed and not last cycle
        if i < max_revisions - 1:
            print(f"      Revising (min score: {min_score})...")
            revised = creator.revise_prompt(current_prompt, critique, character_data, visual_style)
            current_prompt = revised.prompt
            revision_count += 1

    # Get final scores from last critique
    final_critique = critique_history[-1]

    return {
        "prompt": current_prompt,
        "shot_type": result.shot_type,
        "key_features": result.key_features_included,
        "revision_count": revision_count,
        "final_scores": {
            "face_detail": final_critique["face_detail_score"],
            "clothing_detail": final_critique["clothing_detail_score"],
            "distinguishing_marks": final_critique["distinguishing_marks_score"],
            "pose_expression": final_critique["pose_expression_score"],
            "quality_tags": final_critique["quality_tags_score"],
            "overall": final_critique["overall_score"],
        },
        "critique_history": critique_history,
    }
