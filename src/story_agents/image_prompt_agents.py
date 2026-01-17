"""
Phase 4 Agents: Image Prompt Generation

- CharacterImagePromptAgent: Generates detailed AI image prompts for character portraits
- LocationImagePromptAgent: Generates detailed AI image prompts for location artwork
- SceneImagePromptAgent: Generates detailed AI image prompts for scene illustrations
- SceneImagePromptCriticAgent: Critiques scene image prompts for accuracy and detail
- StoryPosterPromptAgent: Generates epic movie poster prompts for story thumbnails
- StoryPosterCriticAgent: Critiques poster prompts for visual impact
"""

import json

from src.story_agents.base_story_agent import BaseStoryAgent
from src.story_schemas import (
    ShotPromptCritiqueSchema,
    ImagePromptSchema,
    PosterPromptSchema,
    JuryVoteSchema,
    ShotFramePromptSchema,
    ShotFrameCritiqueSchema,
)


# Style keywords for validation
STYLE_KEYWORDS = {
    "anime": ["anime", "anime style", "japanese animation", "manga style"],
    "ultra-realistic": ["ultra-realistic", "photorealistic", "hyper-realistic", "realistic"],
    "watercolor": ["watercolor", "water color", "watercolour"],
    "oil-painting": ["oil painting", "oil-painting", "classical painting"],
    "concept-art": ["concept art", "concept-art", "game art"],
    "comic": ["comic", "comic book", "graphic novel"],
    "fantasy": ["fantasy", "fantasy art", "epic fantasy"],
    "sci-fi": ["sci-fi", "science fiction", "futuristic"],
    "noir": ["noir", "film noir", "dark noir"],
    "horror": ["horror", "horror art", "dark horror"],
}


def build_full_character_description(char: dict, include_role_hint: bool = True) -> str:
    """
    Build a complete visual description for AI image generation (NO character names).

    AI image generators don't know fictional characters like "Elena" or "Yara Noble".
    They need actual visual descriptions: "a young woman with auburn hair, emerald eyes..."

    Args:
        char: Character profile dict with physical, clothing, etc.
        include_role_hint: Whether to add expression hints based on role

    Returns:
        Full visual description string suitable for image generation prompts
    """
    if not char:
        return "a mysterious figure"

    physical = char.get('physical', {})
    parts = []

    # Gender and age
    gender = char.get('gender', 'person')
    age = char.get('age', '')
    if age:
        parts.append(f"a {gender} in their {age}")
    else:
        parts.append(f"a {gender}")

    # Height and build
    if physical.get('height'):
        parts.append(physical['height'])
    if physical.get('build'):
        parts.append(f"{physical['build']} build")

    # Hair (detailed)
    if physical.get('hair_color'):
        parts.append(f"with {physical['hair_color']} hair")

    # Eyes (detailed)
    if physical.get('eye_color'):
        parts.append(f"and {physical['eye_color']} eyes")

    # Skin tone
    if physical.get('skin_tone') and physical['skin_tone'].lower() not in ['not specified', 'unknown', '']:
        parts.append(f"{physical['skin_tone']} skin tone")

    # Distinguishing features (scars, tattoos, etc.)
    features = physical.get('distinguishing_features', '')
    if features and features.lower() not in ['none', 'none specified', 'n/a', '']:
        parts.append(f"with {features}")

    # Clothing (important for visual identification)
    clothing = char.get('clothing', '')
    if clothing:
        parts.append(f"wearing {clothing}")

    # Role hint for pose/expression
    if include_role_hint:
        role = char.get('role_in_story', '')
        if role == 'protagonist':
            parts.append("with a determined, heroic expression")
        elif role == 'antagonist':
            parts.append("with a menacing, shadowed presence")
        elif role == 'mentor':
            parts.append("with wise, knowing eyes")
        elif role == 'sidekick':
            parts.append("with a loyal, supportive demeanor")

    return ", ".join(parts) if parts else "a mysterious figure"


def validate_title_in_prompt(prompt: str, title: str) -> str:
    """
    Ensure the story title appears verbatim in the poster prompt.

    AI image generators need the actual title text to render it on the poster.
    If the title is missing, append it with typography description.

    Args:
        prompt: The generated poster prompt
        title: The story title that MUST appear in the prompt

    Returns:
        Prompt with title guaranteed to be present
    """
    if not title or title == "Untitled":
        return prompt

    # Check if title appears in prompt (case-insensitive)
    if title.lower() not in prompt.lower():
        # Title is missing - append it with typography
        title_addition = f' Title text "{title}" prominently displayed in bold stylized typography at top or bottom of composition.'
        return prompt.rstrip('.') + '.' + title_addition

    return prompt


def ensure_style_in_prompt(prompt: str, style: str) -> str:
    """
    Ensure the specified art style is present in the prompt.
    If not found, append style tags at the end.

    Args:
        prompt: The generated image prompt
        style: The desired art style

    Returns:
        Prompt with style guaranteed to be present
    """
    style_lower = style.lower()
    prompt_lower = prompt.lower()

    # Check if style is already present
    if style_lower in prompt_lower:
        return prompt

    # Check for synonyms
    keywords = STYLE_KEYWORDS.get(style_lower, [style_lower])
    for keyword in keywords:
        if keyword in prompt_lower:
            return prompt

    # Style not found - append it
    prompt = prompt.rstrip('.')
    prompt += f", {style} style, {style} art."
    return prompt


class CharacterImagePromptAgent(BaseStoryAgent):
    """Generates detailed image prompts for character portraits."""

    @property
    def name(self) -> str:
        return "CHARACTER_IMAGE_PROMPT"

    @property
    def role(self) -> str:
        return "Character Portrait Prompt Generator"

    @property
    def system_prompt(self) -> str:
        return """You are an expert at creating detailed prompts for AI image generation.

Your specialty is CHARACTER PORTRAITS with these requirements:
- Extremely detailed physical appearance (face, body, posture)
- Precise clothing and accessories description
- Hair style, color, texture in detail
- Eye color, shape, expression
- Skin tone, distinguishing features (scars, tattoos, jewelry)
- Pose and body language reflecting personality
- Lighting that highlights features
- Art style appropriate to the story genre

Focus ONLY on describing the character - ignore background entirely.

Output format: A single paragraph prompt, 150-250 words, suitable for Midjourney/DALL-E/Stable Diffusion.
Include camera angle, art style, quality tags (8k, detailed, professional)."""

    def generate_prompt(self, character: dict, style: str = "fantasy") -> ImagePromptSchema:
        """
        Generate detailed image prompt for a single character.

        Args:
            character: Character dict with name, physical, clothing, etc.
            style: Art style (ultra-realistic, anime, watercolor, oil-painting, concept-art, comic, or genre like fantasy/sci-fi)

        Returns:
            ImagePromptSchema with detailed image generation prompt
        """
        # Extract physical details safely
        physical = character.get('physical', {})

        prompt = f"""Create a detailed AI image generation prompt for this character:

NAME: {character.get('name', 'Unknown')}
GENDER: {character.get('gender', 'unknown')}
AGE: {character.get('age', 'adult')}

PHYSICAL DETAILS:
- Height: {physical.get('height', 'average')}
- Build: {physical.get('build', 'average')}
- Hair: {physical.get('hair_color', 'dark')}
- Eyes: {physical.get('eye_color', 'brown')}
- Distinguishing features: {physical.get('distinguishing_features', 'none')}

CLOTHING: {character.get('clothing', 'simple clothing')}

PERSONALITY: {', '.join(character.get('personality_traits', []))}

ROLE: {character.get('role_in_story', 'character')}

ART STYLE: {style}

Generate output with:
- prompt: A SINGLE PARAGRAPH (150-250 words) for creating a portrait of this character including detailed face and expression matching personality, complete clothing description with colors and textures, pose matching their personality and role, art style ({style}), and quality tags (8k, highly detailed, professional portrait). Do NOT mention background - focus only on the character.
- style_applied: "{style}"
- key_elements: List of 5-8 key visual elements included in the prompt (e.g., "emerald green eyes", "weathered leather jacket", "confident stance")"""

        result = self.invoke_structured(prompt, ImagePromptSchema, max_tokens=1500)
        result.prompt = ensure_style_in_prompt(result.prompt, style)
        return result


class LocationImagePromptAgent(BaseStoryAgent):
    """Generates detailed image prompts for location artwork."""

    @property
    def name(self) -> str:
        return "LOCATION_IMAGE_PROMPT"

    @property
    def role(self) -> str:
        return "Location Artwork Prompt Generator"

    @property
    def system_prompt(self) -> str:
        return """You are an expert at creating detailed prompts for AI image generation.

Your specialty is ENVIRONMENT/LOCATION ART with these requirements:
- Sweeping, atmospheric compositions
- Rich environmental details (vegetation, architecture, terrain)
- Lighting that sets the mood (time of day, weather)
- Color palette matching the atmosphere
- Sense of scale and depth
- Points of interest and focal elements
- Textures (stone, wood, water, foliage)
- Environmental storytelling elements
- Art style appropriate to the story genre

Output format: A single paragraph prompt, 150-250 words, suitable for Midjourney/DALL-E/Stable Diffusion.
Include perspective, art style, quality tags (8k, concept art, matte painting)."""

    def generate_prompt(self, location: dict, style: str = "fantasy") -> ImagePromptSchema:
        """
        Generate detailed image prompt for a single location.

        Args:
            location: Location dict with name, description, atmosphere, etc.
            style: Art style (ultra-realistic, anime, watercolor, oil-painting, concept-art, comic, or genre like fantasy/sci-fi)

        Returns:
            ImagePromptSchema with detailed image generation prompt
        """
        # Build key features list
        key_features = location.get('key_features', [])
        features_text = '\n'.join('- ' + f for f in key_features) if key_features else 'None specified'

        prompt = f"""Create a detailed AI image generation prompt for this location:

NAME: {location.get('name', 'Unknown Location')}
TYPE: {location.get('type', 'landscape')}

DESCRIPTION: {location.get('description', '')}

ATMOSPHERE: {location.get('atmosphere', '')}

KEY FEATURES:
{features_text}

SENSORY DETAILS: {location.get('sensory_details', '')}

ART STYLE: {style}

Generate output with:
- prompt: A SINGLE PARAGRAPH (150-250 words) for creating artwork of this location including time of day and lighting conditions, weather and atmospheric effects, detailed environmental features with textures, color palette and mood, perspective (wide shot, establishing shot, etc.), art style ({style}), and quality tags (8k, highly detailed, cinematic, professional).
- style_applied: "{style}"
- key_elements: List of 5-8 key visual elements included in the prompt (e.g., "golden hour lighting", "ancient stone walls", "misty atmosphere")"""

        result = self.invoke_structured(prompt, ImagePromptSchema, max_tokens=1500)
        result.prompt = ensure_style_in_prompt(result.prompt, style)
        return result


class SceneImagePromptAgent(BaseStoryAgent):
    """Generates detailed image prompts for scene illustrations."""

    @property
    def name(self) -> str:
        return "SCENE_IMAGE_PROMPT"

    @property
    def role(self) -> str:
        return "Scene Illustration Prompt Generator"

    @property
    def system_prompt(self) -> str:
        return """You are an expert at creating detailed prompts for AI image generation.

Your specialty is SCENE ILLUSTRATIONS that capture a moment in a story:
- Multiple characters interacting in a specific location
- Accurate physical descriptions of each character from profiles
- Clothing and accessories matching character profiles
- Location environment with atmosphere and details
- Action/pose showing what characters are doing
- Time of day and lighting conditions
- Composition that tells the story moment
- Emotional mood and tension

Output format: A single paragraph prompt, 200-350 words, suitable for Midjourney/DALL-E/Stable Diffusion.
Include composition, camera angle, lighting, art style, quality tags."""

    def generate_prompt(self, scene: dict, characters: list[dict],
                        location: dict, style: str = "fantasy") -> ImagePromptSchema:
        """
        Generate detailed image prompt for a scene illustration.

        Args:
            scene: Scene dict with scene_number, location, characters, time, text
            characters: List of all character profiles
            location: Location profile dict for this scene's location
            style: Art style (ultra-realistic, anime, watercolor, etc.)

        Returns:
            ImagePromptSchema with detailed image generation prompt
        """
        # Build character descriptions from profiles
        char_descriptions = []
        scene_char_names = scene.get('characters', [])

        for char_name in scene_char_names:
            # Find matching character profile
            char_profile = next(
                (c for c in characters if c.get('name') == char_name),
                None
            )
            if char_profile:
                physical = char_profile.get('physical', {})
                personality_traits = char_profile.get('personality_traits', ['neutral'])
                char_descriptions.append(f"""
{char_name}:
- Gender: {char_profile.get('gender', 'unknown')}
- Age: {char_profile.get('age', 'adult')}
- Height: {physical.get('height', 'average')}
- Build: {physical.get('build', 'average')}
- Hair: {physical.get('hair_color', 'dark')} (include style and texture)
- Eyes: {physical.get('eye_color', 'brown')} (include shape and expression)
- Skin tone: {physical.get('skin_tone', 'not specified')}
- Distinguishing features: {physical.get('distinguishing_features', 'none')}
- Clothing (DETAILED with colors/textures): {char_profile.get('clothing', 'simple clothing')}
- Personality (for expression/pose): {', '.join(personality_traits)}
""")
            else:
                char_descriptions.append(f"\n{char_name}: (no profile available)\n")

        # Build location details
        loc_details = ""
        if location:
            key_features = location.get('key_features', [])
            features_text = '\n  - '.join(key_features) if key_features else 'None specified'
            loc_details = f"""
Location Type: {location.get('type', 'environment')}
Description: {location.get('description', '')}
Atmosphere/Mood: {location.get('atmosphere', '')}
Key Visual Features:
  - {features_text}
Sensory Details: {location.get('sensory_details', '')}
Story Connection: {location.get('connection_to_story', '')}
"""

        # Get scene text (truncate if too long)
        scene_text = scene.get('text', '')
        if len(scene_text) > 600:
            scene_text = scene_text[:600] + "..."

        prompt = f"""Create a detailed AI image generation prompt for this scene illustration:

SCENE ACTION (what's happening):
{scene_text}

CHARACTERS PRESENT:
{''.join(char_descriptions) if char_descriptions else 'No character profiles found'}

LOCATION: {scene.get('location', 'Unknown')}
{loc_details}

TIME OF DAY: {scene.get('time', 'daytime')}

ART STYLE: {style}

Generate output with:
- prompt: A SINGLE PARAGRAPH (200-350 words) for creating an illustration of this scene including all characters with accurate physical descriptions from their profiles, what each character is DOING (action/pose based on scene text), character clothing matching their profiles exactly, location environment with key visual details, time of day and appropriate lighting, composition (camera angle, framing, foreground/background), mood and atmosphere matching the scene, art style ({style}), and quality tags (8k, highly detailed, cinematic, professional illustration).
- style_applied: "{style}"
- key_elements: List of 6-10 key visual elements included in the prompt (e.g., "dramatic confrontation pose", "sunset lighting through windows", "character's red cloak flowing")"""

        result = self.invoke_structured(prompt, ImagePromptSchema, max_tokens=2000)
        result.prompt = ensure_style_in_prompt(result.prompt, style)
        return result

    def revise_prompt(self, original_prompt: str, critique: dict) -> ImagePromptSchema:
        """
        Revise a scene image prompt based on critique.

        Args:
            original_prompt: The original generated prompt
            critique: Critique dict with issues and suggestions

        Returns:
            ImagePromptSchema with revised image generation prompt
        """
        issues = critique.get('issues', [])
        suggestions = critique.get('suggestions', [])

        issues_text = '\n'.join(f"- {issue}" for issue in issues) if issues else "None"
        suggestions_text = '\n'.join(f"- {s}" for s in suggestions) if suggestions else "None"

        revision_prompt = f"""Revise this AI image generation prompt based on the critique:

ORIGINAL PROMPT:
{original_prompt}

ISSUES FOUND:
{issues_text}

SUGGESTIONS:
{suggestions_text}

Generate output with:
- prompt: Revised SINGLE PARAGRAPH (200-350 words) addressing all issues and incorporating suggestions. Maintain quality tags and art style.
- style_applied: The art style used in the revised prompt
- key_elements: List of 6-10 key visual elements included in the revised prompt"""

        return self.invoke_structured(revision_prompt, ImagePromptSchema, max_tokens=2000)


class SceneImagePromptCriticAgent(BaseStoryAgent):
    """Critiques scene image prompts for accuracy and detail."""

    @property
    def name(self) -> str:
        return "SCENE_PROMPT_CRITIC"

    @property
    def role(self) -> str:
        return "Scene Prompt Quality Critic"

    @property
    def system_prompt(self) -> str:
        return """You are a quality critic for AI image generation prompts.

Your job is to review scene illustration prompts and identify:
1. Missing or inaccurate character descriptions
2. Actions that don't match the scene text
3. Missing location details
4. Incorrect time of day/lighting
5. Composition issues
6. Missing important visual elements

Be specific about what's wrong and how to fix it.
Rate severity as: minor (small tweaks), moderate (several fixes needed), major (significant rewrite needed)."""

    def critique(self, prompt: str, scene: dict,
                 characters: list[dict], location: dict) -> ShotPromptCritiqueSchema:
        """
        Critique a scene image prompt for accuracy and completeness.

        Args:
            prompt: The generated image prompt to critique
            scene: Original scene dict
            characters: Character profiles for reference
            location: Location profile for reference

        Returns:
            ShotPromptCritiqueSchema with issues, suggestions, and severity
        """
        # Build reference info
        char_names = scene.get('characters', [])
        char_info = []
        for name in char_names:
            profile = next((c for c in characters if c.get('name') == name), None)
            if profile:
                char_info.append(f"{name}: {profile.get('clothing', 'unknown clothing')}")

        scene_text = scene.get('text', '')[:500]
        loc_name = location.get('name', 'Unknown') if location else 'Unknown'

        critique_prompt = f"""Critique this AI image generation prompt for a scene illustration:

PROMPT TO CRITIQUE:
{prompt}

ORIGINAL SCENE TEXT:
{scene_text}

CHARACTERS THAT SHOULD BE PRESENT:
{', '.join(char_names) if char_names else 'None specified'}

CHARACTER CLOTHING REFERENCE:
{chr(10).join(char_info) if char_info else 'No profiles available'}

LOCATION: {loc_name}
{f"Description: {location.get('description', '')}" if location else ''}

TIME: {scene.get('time', 'not specified')}

Analyze the prompt and check for:
1. Are ALL characters mentioned and accurately described (hair, eyes, build)?
2. Does the action/pose match what's happening in the scene text?
3. Is the location properly represented with key features?
4. Is the lighting/time of day correct?
5. Are there any missing important visual details?
6. Is the composition clear and well-framed?

Provide:
- issues: List of specific issues found (empty list if none)
- suggestions: List of how to fix each issue
- severity: "minor", "moderate", or "major" """

        return self.invoke_structured(critique_prompt, ShotPromptCritiqueSchema, max_tokens=1000)


class StoryPosterPromptAgent(BaseStoryAgent):
    """Generates epic movie poster prompts for story thumbnails."""

    @property
    def name(self) -> str:
        return "STORY_POSTER_PROMPT"

    @property
    def role(self) -> str:
        return "Movie Poster Prompt Generator"

    @property
    def system_prompt(self) -> str:
        return """You are an expert at creating EPIC MOVIE POSTER prompts for AI image generation.

CRITICAL: VISUAL STYLE INTEGRATION
- The prompt MUST start with the provided STYLE PREFIX
- The prompt MUST end with the provided STYLE SUFFIX
- All visual descriptions must match the style aesthetic

Your specialty is CINEMATIC MOVIE POSTERS with these requirements:
- Dramatic central composition featuring protagonist
- Title text placement (top or bottom, stylized)
- Layered visual elements (foreground character, mid-ground action, background environment)
- Cinematic lighting (dramatic shadows, volumetric light, rim lighting)
- Color grading that matches the story's mood
- Genre-appropriate visual style
- Professional movie poster composition and framing

Key elements to include:
1. Central figure in dramatic pose representing the protagonist
2. Antagonist presence (subtle shadow, looming figure, or symbolic element)
3. Key location/environment as atmospheric background
4. Visual representation of central conflict
5. Mood through color palette and lighting
6. Title text placement instructions

Output format: A single paragraph prompt, 250-400 words, suitable for Midjourney/DALL-E/Stable Diffusion.
Include composition, lighting, color palette, text placement, art style, quality tags."""

    def generate_prompt(self, outline: dict, characters: list[dict],
                        locations: list[dict], style: str = "fantasy", visual_style: dict = None) -> PosterPromptSchema:
        """
        Generate movie poster prompt for the story.

        Args:
            outline: Outline dict with title, logline, protagonist, antagonist, central_conflict
            characters: List of character profiles
            locations: List of location profiles
            style: Art style
            visual_style: Visual style dict with name, prefix, suffix

        Returns:
            PosterPromptSchema with detailed movie poster prompt
        """
        # Find protagonist and antagonist profiles
        protag_name = outline.get('protagonist', '').split(',')[0].strip()
        antag_name = outline.get('antagonist', '').split(',')[0].strip()

        protag_profile = next((c for c in characters if protag_name in c.get('name', '')), None)
        antag_profile = next((c for c in characters if antag_name in c.get('name', '')), None)

        # Build protagonist description using physical features (NO character names)
        # AI image generators don't know "Elena" but understand "a woman with auburn hair"
        protag_desc = build_full_character_description(protag_profile, include_role_hint=True)

        # Build antagonist description using physical features (NO character names)
        antag_desc = build_full_character_description(antag_profile, include_role_hint=True)

        # Build primary location description
        primary_loc = locations[0] if locations else {}
        loc_desc = f"""
Name: {primary_loc.get('name', 'Unknown')}
Type: {primary_loc.get('type', 'landscape')}
Description: {primary_loc.get('description', '')}
Atmosphere: {primary_loc.get('atmosphere', '')}
Key Features: {', '.join(primary_loc.get('key_features', []))}
"""

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

        prompt = f"""Create an EPIC MOVIE POSTER prompt for this story:

TITLE: "{outline.get('title', 'Untitled')}"

LOGLINE: {outline.get('logline', '')}

CENTRAL CONFLICT: {outline.get('central_conflict', '')}

PROTAGONIST (central figure):
{protag_desc}

ANTAGONIST (secondary/shadow presence):
{antag_desc}

PRIMARY LOCATION (background):
{loc_desc}

ART STYLE: {style}
{style_info}

Generate output with:
- prompt: A SINGLE PARAGRAPH (250-400 words) for creating an EPIC MOVIE POSTER. START WITH STYLE PREFIX, then include title "{outline.get('title', 'Untitled')}" with text placement (top center, stylized), protagonist as dramatic central figure in powerful pose, antagonist as looming shadow/presence or secondary figure, location as atmospheric layered background, visual representation of the central conflict, dramatic cinematic lighting (volumetric light, rim lighting, dramatic shadows), color palette matching story mood, composition (protagonist foreground, conflict elements mid-ground, environment background), art style ({style}, epic {style} movie poster), END WITH STYLE SUFFIX + quality tags (8k, highly detailed, professional movie poster, cinematic, dramatic).
- composition_type: One of "character_portrait", "action_scene", "symbolic" based on how the poster is composed
- color_palette: The color palette used (e.g., "teal-orange cinematic", "dark moody blues with red accents")
- title_placement: Where the title appears (e.g., "top center", "bottom third")
- style_applied: "{style}" """

        result = self.invoke_structured(prompt, PosterPromptSchema, max_tokens=2000)
        result.prompt = ensure_style_in_prompt(result.prompt, style)
        return result

    def revise_prompt(self, original_prompt: str, critique: dict) -> PosterPromptSchema:
        """
        Revise a poster prompt based on critique.

        Args:
            original_prompt: The original generated prompt
            critique: Critique dict with issues and suggestions

        Returns:
            PosterPromptSchema with revised poster prompt
        """
        issues = critique.get('issues', [])
        suggestions = critique.get('suggestions', [])

        issues_text = '\n'.join(f"- {issue}" for issue in issues) if issues else "None"
        suggestions_text = '\n'.join(f"- {s}" for s in suggestions) if suggestions else "None"

        revision_prompt = f"""Revise this EPIC MOVIE POSTER prompt based on the critique:

ORIGINAL PROMPT:
{original_prompt}

ISSUES FOUND:
{issues_text}

SUGGESTIONS FOR MORE EPIC IMPACT:
{suggestions_text}

Generate output with:
- prompt: Revised SINGLE PARAGRAPH (250-400 words) addressing all issues and incorporating suggestions. Make it MORE EPIC and DRAMATIC. Maintain quality tags and art style.
- composition_type: One of "character_portrait", "action_scene", "symbolic" based on how the poster is composed
- color_palette: The color palette used (e.g., "teal-orange cinematic", "dark moody blues with red accents")
- title_placement: Where the title appears (e.g., "top center", "bottom third")
- style_applied: The art style used in the revised prompt"""

        return self.invoke_structured(revision_prompt, PosterPromptSchema, max_tokens=2000)


class StoryPosterCriticAgent(BaseStoryAgent):
    """Critiques story poster prompts for epic visual impact."""

    @property
    def name(self) -> str:
        return "STORY_POSTER_CRITIC"

    @property
    def role(self) -> str:
        return "Movie Poster Prompt Critic"

    @property
    def system_prompt(self) -> str:
        return """You are a quality critic for AI movie poster prompts.

Your job is to review poster prompts and identify:
1. Missing or weak protagonist description
2. Missing antagonist presence/shadow
3. Weak or missing title text placement
4. Poor composition (layering, focal point)
5. Missing cinematic lighting
6. Weak color palette/mood
7. Missing quality/style tags

Be specific about what's wrong and how to make it MORE EPIC.
Rate severity as: minor (small tweaks), moderate (several fixes needed), major (significant rewrite needed)."""

    def critique(self, prompt: str, outline: dict, characters: list[dict]) -> ShotPromptCritiqueSchema:
        """
        Critique a poster prompt for epic visual impact.

        Args:
            prompt: The generated poster prompt to critique
            outline: Story outline for reference
            characters: Character profiles for reference

        Returns:
            ShotPromptCritiqueSchema with issues, suggestions, and severity
        """
        critique_prompt = f"""Critique this MOVIE POSTER prompt:

PROMPT TO CRITIQUE:
{prompt}

STORY TITLE: {outline.get('title', 'Unknown')}
LOGLINE: {outline.get('logline', '')}
CENTRAL CONFLICT: {outline.get('central_conflict', '')}

Check for:
1. Is the title "{outline.get('title', '')}" mentioned with text placement?
2. Is the protagonist clearly described as central dramatic figure?
3. Is there antagonist presence (shadow, looming figure, secondary)?
4. Is the composition layered (foreground, mid-ground, background)?
5. Is there dramatic cinematic lighting described?
6. Is the color palette/mood specified?
7. Are quality tags present (8k, cinematic, professional)?

Provide:
- issues: List of specific issues found (empty list if none)
- suggestions: List of how to make it more epic
- severity: "minor", "moderate", or "major" """

        return self.invoke_structured(critique_prompt, ShotPromptCritiqueSchema, max_tokens=1000)


# =============================================================================
# MULTI-AGENT POSTER SYSTEM (9 prompts -> 3 winners via jury voting)
# =============================================================================

# Genre-specific style adaptations with Hollywood/audiobook optimization
GENRE_ADAPTATIONS = {
    "anime": {
        # Hero close-ups optimized for thumbnails
        "character_portrait": "intense anime close-up, expressive eyes filling 40% of frame, dynamic hair movement, vibrant saturated colors, cel-shaded dramatic rim lighting, high contrast shadows",
        "action_scene": "dynamic speed lines, explosive impact frames, motion blur anime style, dramatic poses with clear silhouette, vivid neon accents against dark background",
        "symbolic": "surreal anime imagery, iconic symbolic motifs, dreamlike atmosphere with bold color palette, single powerful symbol as focal point",
        # Thumbnail-optimized versions
        "minimalist": "bold anime character silhouette, single vivid neon accent color against black, clean sharp edges, maximum contrast, iconic pose readable at any size",
        "detailed_panorama": "Studio Ghibli inspired epic vista, tiny figures against vast landscape, soft gradients, atmospheric perspective, warm golden hour lighting",
        "character_collage": "anime character ensemble, dynamic triangular arrangement, vibrant complementary colors, each face distinct and recognizable",
        "text_focused": "bold anime title typography in stylized katakana-inspired font, vivid gradient colors, clean geometric background, text as visual centerpiece",
        "silhouette": "dramatic anime silhouette with glowing eyes/accents, stark contrast, bold outlines, single vivid accent color popping against dark",
        "geometric": "geometric anime patterns, modern aesthetic, clean vector shapes, neon accents, bold flat colors with subtle gradients",
    },
    "ultra-realistic": {
        # Blockbuster hero shots
        "character_portrait": "photorealistic movie star portrait, intense emotional expression, cinematic rim lighting with teal-orange grading, shallow depth of field, eyes as focal point",
        "action_scene": "IMAX quality action freeze-frame, explosive particles, photorealistic VFX, dynamic camera angle, volumetric dust/smoke, high contrast lighting",
        "symbolic": "metaphorical imagery with photorealistic execution, meaningful symbolism, dramatic chiaroscuro lighting, single powerful visual metaphor",
        # Thumbnail-optimized versions
        "minimalist": "high contrast face against black, single dramatic light source, crystal clear at any size, photographic elegance, bold accent color in eyes or element",
        "detailed_panorama": "cinematic landscape photography, IMAX quality, volumetric god rays, epic scale with tiny human element for perspective, golden hour or blue hour lighting",
        "character_collage": "photorealistic character montage, Hollywood floating heads composition, professional portrait lighting on each face, layered depth",
        "text_focused": "elegant serif typography, professional movie title treatment, subtle lens flare, clean negative space for text, premium minimalist design",
        "silhouette": "moody film noir silhouette, volumetric fog backlit, dramatic single light source, stark contrast, mysterious and atmospheric",
        "geometric": "architectural geometry, clean modern lines, photorealistic materials, striking symmetry, bold contrast between light and shadow",
    },
    "fantasy": {
        # Epic fantasy hero shots
        "character_portrait": "epic fantasy hero portrait, magical particle effects, dramatic cloak flow, otherworldly rim lighting in gold/purple, intense heroic expression",
        "action_scene": "epic fantasy battle, sweeping magical effects, dramatic scale, vivid spell colors against dark background, dynamic poses with clear silhouettes",
        "symbolic": "mythical symbolism, fantasy iconography, magical glowing elements, ancient runes, single iconic symbol representing the story's core",
        # Thumbnail-optimized versions
        "minimalist": "iconic fantasy symbol glowing against dark background, single jewel-tone color, elegant simplicity, magical particles, instantly recognizable",
        "detailed_panorama": "vast fantasy kingdom, towering structures with magical elements, dragons or creatures in distance, atmospheric perspective, epic scale",
        "character_collage": "fantasy character ensemble in heroic arrangement, magical lighting connecting them, varied fantasy races/types, triangular composition",
        "text_focused": "ornate fantasy title typography with magical embellishments, glowing text effects, mystical symbols, rich gold/jewel tones",
        "silhouette": "heroic fantasy silhouette with magical glow emanating, cape/weapon creating strong shape, vivid magical color accent",
        "geometric": "arcane geometric patterns, glowing magical symbols, mystical circles and runes, rich purple/gold palette, ancient and powerful feel",
    },
    "sci-fi": {
        "character_portrait": "futuristic hero portrait, holographic HUD elements, neon cyberpunk lighting, metallic reflections, high-tech aesthetic",
        "action_scene": "explosive sci-fi action, laser fire and plasma effects, dynamic zero-G poses, vivid neon against dark space/metal",
        "symbolic": "technological symbolism, circuit patterns, AI/digital motifs, single powerful tech symbol",
        "minimalist": "clean sci-fi silhouette, single neon accent against black, geometric precision, futuristic minimalism",
        "detailed_panorama": "epic sci-fi cityscape or space vista, massive scale, atmospheric neon lighting, countless details suggesting vast world",
        "character_collage": "sci-fi crew ensemble, diverse species/characters, unified by lighting style, tech-forward composition",
        "text_focused": "futuristic typography, holographic text effect, clean geometric sans-serif, neon glow, tech-inspired design",
        "silhouette": "dramatic sci-fi silhouette, backlit by bright light source (sun/explosion), equipment creating strong shape",
        "geometric": "circuit board patterns, hexagonal tech motifs, clean vector lines, cyan/magenta/yellow tech palette",
    },
    "horror": {
        "character_portrait": "unsettling horror portrait, shadowed face with single eye visible, sickly color palette, subtle wrongness",
        "action_scene": "horror confrontation, monster reveal moment, dramatic shadows, stark contrast, visceral terror",
        "symbolic": "dread symbolism, ominous imagery, decay and darkness, single terrifying symbol",
        "minimalist": "stark horror minimalism, single terrifying element against black, maximum negative space, unsettling simplicity",
        "detailed_panorama": "haunted landscape, oppressive atmosphere, twisted environment, sickly green/purple palette, sense of wrongness",
        "character_collage": "horror characters emerging from darkness, faces partially obscured, threatening arrangement",
        "text_focused": "dripping/distorted horror typography, blood red accents, unsettling font choices, darkness encroaching on text",
        "silhouette": "terrifying silhouette, inhuman proportions suggested, backlit by sickly light, pure dread in shape",
        "geometric": "occult geometric patterns, disturbing symmetry, ancient evil symbols, black and crimson palette",
    },
}


def get_genre_adaptation(base_style: str, composition: str) -> str:
    """Get genre-specific style adaptation for a composition type."""
    style_lower = base_style.lower()
    # Find matching style or use fantasy as default
    for style_key in GENRE_ADAPTATIONS:
        if style_key in style_lower:
            return GENRE_ADAPTATIONS[style_key].get(composition, "")
    return GENRE_ADAPTATIONS["fantasy"].get(composition, "")


class CinematicPosterAgent(BaseStoryAgent):
    """Generates photorealistic, Hollywood-style poster prompts."""

    COMPOSITION_TYPES = [
        ("character_portrait", "Close-up protagonist with dramatic lighting, movie star quality"),
        ("action_scene", "Dynamic mid-action moment, explosions/effects, wide shot"),
        ("symbolic", "Metaphorical imagery representing central conflict"),
    ]

    @property
    def name(self) -> str:
        return "CINEMATIC_POSTER"

    @property
    def role(self) -> str:
        return "Cinematic Movie Poster Generator"

    @property
    def system_prompt(self) -> str:
        return """You are a HOLLYWOOD BLOCKBUSTER poster designer creating theatrical one-sheet quality prompts.

CRITICAL: VISUAL STYLE INTEGRATION
- The prompt MUST start with the provided STYLE PREFIX
- The prompt MUST end with the provided STYLE SUFFIX
- All visual descriptions must match the style aesthetic

DESIGN PRINCIPLES (from professional poster design):
1. AIDA Formula: Grab Attention → Create Interest → Build Desire → Drive Action
2. Visual Hierarchy: Single clear focal point that draws the eye
3. Thumbnail Test: Must be recognizable at phone thumbnail size (200x300px)
4. 2-Second Rule: Must grab attention instantly
5. Emotional Impact: Faces with strong emotions increase engagement 20-30%

YOUR SPECIALTY - BLOCKBUSTER THEATRICAL POSTERS:
- Dramatic "floating heads" composition with layered depth
- Epic scale with volumetric lighting and god rays
- Color grading that sets mood (warm=hope, cool=danger, teal-orange=action)
- Professional cinematography with shallow depth of field
- Title placement: Top or bottom third, never center
- Tagline integration with impactful typography

COMPOSITION TECHNIQUES:
- Rule of thirds for key element placement
- Leading lines drawing eye to protagonist
- Contrast between protagonist (light) and antagonist (shadow)
- Atmospheric depth with foreground, midground, background layers
- Negative space for text legibility

COLOR PSYCHOLOGY TO INCLUDE:
- Red/Orange: Energy, passion, danger, action
- Blue: Trust, mystery, isolation
- Purple: Royalty, mysticism, power
- Teal + Orange: Classic blockbuster contrast
- ALWAYS specify primary color, accent color, and mood temperature in prompts

REQUIRED QUALITY TAGS (always include):
8k, ultra-detailed, theatrical movie poster, professional marketing design,
dramatic rim lighting, volumetric light, cinematic color grading,
billboard-ready composition, high contrast, vivid saturated colors,
award-winning poster design, major studio quality

You create prompts that look like they cost $50,000 from a Hollywood studio."""

    def generate_prompts(self, outline: dict, characters: list[dict],
                         locations: list[dict], base_style: str, visual_style: dict = None) -> list[dict]:
        """Generate 3 unique prompts with different cinematic compositions."""
        prompts = []

        # Get protagonist/antagonist info
        protag_name = outline.get('protagonist', '').split(',')[0].strip()
        antag_name = outline.get('antagonist', '').split(',')[0].strip()
        protag = next((c for c in characters if protag_name in c.get('name', '')), None)
        antag = next((c for c in characters if antag_name in c.get('name', '')), None)
        primary_loc = locations[0] if locations else {}

        for comp_type, comp_desc in self.COMPOSITION_TYPES:
            genre_adapt = get_genre_adaptation(base_style, comp_type)

            result = self._generate_for_composition(
                comp_type, comp_desc, genre_adapt,
                outline, protag, antag, primary_loc, base_style, visual_style
            )

            prompts.append({
                "agent": "CINEMATIC",
                "composition": result.composition_type,
                "prompt": result.prompt,
                "style": result.style_applied,
                "color_palette": result.color_palette,
                "title_placement": result.title_placement,
            })

        return prompts

    # Example prompts for each composition type
    COMPOSITION_EXAMPLES = {
        "character_portrait": """Intense close-up portrait of a weathered male warrior in his 40s with silver-streaked black hair and deep amber eyes filled with determination, battle scars crossing his left cheek, wearing dented steel armor with a crimson cape billowing behind him. Dramatic three-quarter view, shallow depth of field blurring a burning castle in the background. Volumetric god rays pierce through smoke from upper left, rim lighting creates golden edge along his profile. Color palette: warm amber highlights against deep shadow blues, teal-orange contrast. Title "THE LAST GUARDIAN" in bold metallic serif font at top, tagline below. Emotional tone: heroic sacrifice, bittersweet resolve. 8k, ultra-detailed, theatrical movie poster, cinematic color grading, professional marketing design, major studio quality, fantasy epic style.""",

        "action_scene": """Explosive mid-action wide shot of a young woman with flowing red hair leaping through shattered glass, twin daggers catching moonlight, her emerald cloak frozen mid-swirl. Behind her, a gothic cathedral collapses in flames, debris suspended in the air. Dynamic Dutch angle composition, motion blur on peripheral elements, tack-sharp focus on her determined face. Dramatic backlighting from the inferno creates stark silhouette edges, lens flares scattered across frame. Color palette: cool midnight blues punctuated by hot orange explosion light, green accents from her cloak. Title "MIDNIGHT RECKONING" integrated into smoke effects at bottom. Emotional tone: desperate courage, climactic action. 8k, ultra-detailed, theatrical movie poster, explosive VFX, professional blockbuster quality, action fantasy style.""",

        "symbolic": """Surreal metaphorical composition: a massive ancient tree split down the middle, one half lush green with golden light, the other half dead and burning in crimson flames. A small silhouetted figure stands at the divide, facing the viewer, identity obscured. Centered symmetrical composition with reflection pool below creating infinity effect. Ethereal volumetric light from both sides meeting at the figure, atmospheric haze throughout. Color palette: rich emerald and gold on life side, deep crimson and black on death side, purple twilight sky above. Title "THE CHOICE" in elegant serif font floating above the tree, glowing softly. Emotional tone: fate, burden of decision, duality. 8k, ultra-detailed, theatrical movie poster, concept art quality, symbolic imagery, fantasy drama style.""",
    }

    def _generate_for_composition(self, comp_type: str, comp_desc: str,
                                   genre_adapt: str, outline: dict,
                                   protag: dict, antag: dict,
                                   location: dict, base_style: str, visual_style: dict = None) -> PosterPromptSchema:
        """Generate a single prompt for a specific composition type."""
        protag_desc = self._build_char_desc(protag) if protag else "Unknown protagonist"
        antag_desc = self._build_char_desc(antag) if antag else "Unknown antagonist"

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

        # Get example for this composition type
        example = self.COMPOSITION_EXAMPLES.get(comp_type, self.COMPOSITION_EXAMPLES["character_portrait"])

        prompt = f"""Create a CINEMATIC MOVIE POSTER prompt for:

TITLE: "{outline.get('title', 'Untitled')}"
LOGLINE: {outline.get('logline', '')}
CENTRAL CONFLICT: {outline.get('central_conflict', '')}

COMPOSITION TYPE: {comp_type.upper()} - {comp_desc}

PROTAGONIST: {protag_desc}
ANTAGONIST: {antag_desc}
LOCATION: {location.get('name', 'Unknown')} - {location.get('description', '')}

GENRE ADAPTATION: {genre_adapt}
BASE STYLE: {base_style}
{style_info}

HERE IS AN EXAMPLE OF AN EXCELLENT {comp_type.upper()} PROMPT:

{example}

NOW generate output with:
- prompt: A SINGLE PARAGRAPH (200-350 words) for YOUR story following the same quality and structure as the example above. Include: START WITH STYLE PREFIX, subject description, composition/camera angle, lighting (rim lighting, volumetric, etc.), atmosphere (haze, particles, lens flares), specific color palette with mood temperature, emotional tone, END WITH STYLE SUFFIX + quality tags. Apply {genre_adapt}. Make it feel like a $50,000 Hollywood studio poster.
  **CRITICAL MANDATORY REQUIREMENT**: The exact title text "{outline.get('title', 'Untitled')}" MUST appear VERBATIM in your prompt with typography description (font style, color, placement). Example: 'Title "{outline.get('title', 'Untitled')}" in bold metallic serif font at top center'. This is NON-NEGOTIABLE.
- composition_type: "{comp_type}"
- color_palette: The specific color palette used (e.g., "teal-orange cinematic", "warm amber against shadow blues")
- title_placement: Where the title appears (e.g., "top center", "bottom third")
- style_applied: "cinematic {base_style}" """

        result = self.invoke_structured(prompt, PosterPromptSchema, max_tokens=2000)
        result.prompt = ensure_style_in_prompt(result.prompt, base_style)
        # CRITICAL: Validate title is in prompt - AI image generators need actual title text
        title = outline.get('title', 'Untitled')
        result.prompt = validate_title_in_prompt(result.prompt, title)
        return result

    def _build_char_desc(self, char: dict) -> str:
        """
        Build a complete visual description for AI image generation (NO character names).

        AI image generators don't know fictional characters like "Elena" or "Yara Noble".
        They need actual visual descriptions for the prompt.
        """
        return build_full_character_description(char, include_role_hint=True)


class IllustratedPosterAgent(BaseStoryAgent):
    """Generates artistic, hand-drawn, painterly poster prompts."""

    COMPOSITION_TYPES = [
        ("minimalist", "Simple shapes, limited palette, iconic single element"),
        ("detailed_panorama", "Rich world-building, environment-focused, epic scale"),
        ("character_collage", "Multiple characters arranged artistically"),
    ]

    @property
    def name(self) -> str:
        return "ILLUSTRATED_POSTER"

    @property
    def role(self) -> str:
        return "Illustrated Art Poster Generator"

    @property
    def system_prompt(self) -> str:
        return """You are a PREMIUM ILLUSTRATED poster artist like Drew Struzan, Olly Moss, or Mondo artists.

CRITICAL: VISUAL STYLE INTEGRATION
- The prompt MUST start with the provided STYLE PREFIX
- The prompt MUST end with the provided STYLE SUFFIX
- All visual descriptions must match the style aesthetic

DESIGN PRINCIPLES:
1. Each element serves the story - no generic imagery
2. Hand-crafted artistic quality over photorealism
3. Iconic symbolism that captures the narrative essence
4. Limited color palette for visual cohesion (2-4 dominant colors)
5. Texture and brushwork that feels hand-painted

YOUR SPECIALTY - ILLUSTRATED ART POSTERS:
- Drew Struzan style: Warm nostalgic colors, character montage, painted realism
- Olly Moss style: Minimalist, negative space, dual imagery, silhouettes
- Criterion Collection: Artistic, thematic, sophisticated composition
- Concept art quality: Matte painting depth, atmospheric perspective

COMPOSITION TYPES YOU EXCEL AT:
1. **Minimalist**: Single iconic symbol, bold limited palette, maximum white space
2. **Panorama**: Epic landscape with tiny figures, sense of adventure/scale
3. **Character Collage**: Artistic arrangement like classic painted posters

ARTISTIC TECHNIQUES TO INCLUDE:
- Textured brushwork visible in the design
- Warm or cool color temperature consistency
- Symbolic imagery that represents themes
- Vintage/retro grain or texture overlays
- Hand-lettered or artistic typography feel

REQUIRED QUALITY TAGS (always include):
8k, highly detailed illustration, concept art quality, matte painting,
digital painting masterwork, artistic poster design, gallery-worthy,
visible brushwork texture, rich color palette, collectible art print quality,
award-winning illustration, frame-worthy art

You create prompts for posters people would frame and hang on their walls."""

    def generate_prompts(self, outline: dict, characters: list[dict],
                         locations: list[dict], base_style: str, visual_style: dict = None) -> list[dict]:
        """Generate 3 unique prompts with different illustrated compositions."""
        prompts = []

        protag_name = outline.get('protagonist', '').split(',')[0].strip()
        antag_name = outline.get('antagonist', '').split(',')[0].strip()
        protag = next((c for c in characters if protag_name in c.get('name', '')), None)
        antag = next((c for c in characters if antag_name in c.get('name', '')), None)
        primary_loc = locations[0] if locations else {}

        for comp_type, comp_desc in self.COMPOSITION_TYPES:
            genre_adapt = get_genre_adaptation(base_style, comp_type)

            result = self._generate_for_composition(
                comp_type, comp_desc, genre_adapt,
                outline, protag, antag, primary_loc, characters, base_style, visual_style
            )

            prompts.append({
                "agent": "ILLUSTRATED",
                "composition": result.composition_type,
                "prompt": result.prompt,
                "style": result.style_applied,
                "color_palette": result.color_palette,
                "title_placement": result.title_placement,
            })

        return prompts

    # Example prompts for each composition type
    COMPOSITION_EXAMPLES = {
        "minimalist": """Striking minimalist poster: a single black silhouette of a hooded figure holding a glowing blue lantern, standing at the edge of a cliff. Massive negative space above in deep navy blue gradating to black. The lantern's light creates subtle circular gradient around the figure. Limited three-color palette: navy blue, black, and electric blue glow. Title "THE WANDERER" in thin elegant sans-serif at top in white, barely visible. No background details, just the lone figure against void. Emotional tone: isolation, mysterious journey, quiet determination. 8k, minimalist art poster, Olly Moss inspired, limited palette design, gallery-worthy illustration, artistic poster design.""",

        "detailed_panorama": """Breathtaking illustrated panorama of a vast fantasy kingdom at golden hour: towering crystal spires rise from mist-shrouded valleys, a winding river reflects the amber sky, tiny airships dot the horizon. In the foreground bottom corner, two small figures on horseback look out at the vista. Rich painterly brushwork visible throughout, warm nostalgic color palette of golds, soft purples, and dusty pinks. Atmospheric perspective creates depth through five distinct layers. Title "REALM OF ECHOES" in ornate hand-lettered fantasy script integrated into clouds at top. Emotional tone: wonder, adventure awaiting, epic scale. 8k, highly detailed illustration, Drew Struzan inspired, matte painting quality, concept art masterwork, fantasy illustration style.""",

        "character_collage": """Artistic character collage arranged in dynamic triangular composition: protagonist (young woman with silver hair, determined expression) at center-top, largest. Mentor figure (elderly man with kind eyes, white beard) lower left, antagonist (shadowed figure with glowing red eyes, sharp features) lower right, creating tension. Supporting characters fade into painterly background. Warm golden light on heroes, cool shadows on villain. Rich oil painting texture, visible brushstrokes. Color palette: warm earth tones for heroes, deep purples and blacks for villain, united by amber accent lights. Title "LEGACY OF LIGHT" in elegant gold lettering at bottom. Emotional tone: found family, good versus evil, epic saga. 8k, illustrated movie poster, collectible art print quality, character ensemble, painterly masterwork.""",
    }

    def _generate_for_composition(self, comp_type: str, comp_desc: str,
                                   genre_adapt: str, outline: dict,
                                   protag: dict, antag: dict,
                                   location: dict, all_chars: list[dict],
                                   base_style: str, visual_style: dict = None) -> PosterPromptSchema:
        """Generate a single prompt for a specific composition type."""
        protag_desc = self._build_char_desc(protag) if protag else "Unknown protagonist"

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

        # For character_collage, include all characters
        char_list = ""
        if comp_type == "character_collage":
            char_list = "\n".join([f"- {c.get('name', 'Unknown')}: {c.get('clothing', '')}"
                                   for c in all_chars[:4]])

        # Get example for this composition type
        example = self.COMPOSITION_EXAMPLES.get(comp_type, self.COMPOSITION_EXAMPLES["minimalist"])

        prompt = f"""Create an ILLUSTRATED MOVIE POSTER prompt for:

TITLE: "{outline.get('title', 'Untitled')}"
LOGLINE: {outline.get('logline', '')}

COMPOSITION TYPE: {comp_type.upper()} - {comp_desc}

PROTAGONIST: {protag_desc}
LOCATION: {location.get('name', 'Unknown')} - {location.get('description', '')}
{f"ALL CHARACTERS:{chr(10)}{char_list}" if char_list else ""}

GENRE ADAPTATION: {genre_adapt}
BASE STYLE: {base_style}
{style_info}

HERE IS AN EXAMPLE OF AN EXCELLENT {comp_type.upper()} PROMPT:

{example}

NOW generate output with:
- prompt: A SINGLE PARAGRAPH (200-350 words) for YOUR story following the same quality and structure as the example above. Include: START WITH STYLE PREFIX, subject/scene description, artistic composition, painterly techniques (brushwork, texture), limited color palette with specific colors named, emotional tone, END WITH STYLE SUFFIX + quality tags. Apply {genre_adapt}. Make it feel like gallery-worthy art people would frame.
  **CRITICAL MANDATORY REQUIREMENT**: The exact title text "{outline.get('title', 'Untitled')}" MUST appear VERBATIM in your prompt with artistic typography treatment (hand-lettered style, color, placement). Example: 'Title "{outline.get('title', 'Untitled')}" hand-lettered in warm gold at bottom'. This is NON-NEGOTIABLE.
- composition_type: "{comp_type}"
- color_palette: The specific limited color palette used (e.g., "navy blue, black, electric blue glow")
- title_placement: Where the title appears (e.g., "top center", "bottom", "integrated into clouds")
- style_applied: "illustrated {base_style}" """

        result = self.invoke_structured(prompt, PosterPromptSchema, max_tokens=2000)
        result.prompt = ensure_style_in_prompt(result.prompt, base_style)
        # CRITICAL: Validate title is in prompt - AI image generators need actual title text
        title = outline.get('title', 'Untitled')
        result.prompt = validate_title_in_prompt(result.prompt, title)
        return result

    def _build_char_desc(self, char: dict) -> str:
        """
        Build a complete visual description for AI image generation (NO character names).

        AI image generators don't know fictional characters like "Elena" or "Yara Noble".
        They need actual visual descriptions for the prompt.
        """
        return build_full_character_description(char, include_role_hint=True)


class GraphicPosterAgent(BaseStoryAgent):
    """Generates bold typography, flat design, modern poster prompts."""

    COMPOSITION_TYPES = [
        ("text_focused", "Bold typography dominates, title as visual element"),
        ("silhouette", "High contrast, dramatic shapes against vivid background"),
        ("geometric", "Abstract patterns, modern design, clean lines"),
    ]

    @property
    def name(self) -> str:
        return "GRAPHIC_POSTER"

    @property
    def role(self) -> str:
        return "Graphic Design Poster Generator"

    @property
    def system_prompt(self) -> str:
        return """You are a MODERN GRAPHIC DESIGN poster master - think Mondo, Saul Bass, or contemporary audiobook covers.

CRITICAL: VISUAL STYLE INTEGRATION
- The prompt MUST start with the provided STYLE PREFIX
- The prompt MUST end with the provided STYLE SUFFIX
- All visual descriptions must match the style aesthetic

DESIGN PRINCIPLES:
1. Typography as a hero element - not just text, but visual art
2. Maximum impact with minimum elements
3. Bold contrast and striking color choices
4. Must work perfectly at thumbnail size (audiobook/YouTube essential)
5. Geometric precision and clean lines

YOUR SPECIALTY - GRAPHIC DESIGN POSTERS:
- Bold silhouettes against vivid color backgrounds
- Typography-forward designs where title IS the visual
- Geometric abstract patterns representing story themes
- High contrast black/white with single accent color
- Modern flat design with depth through layering

AUDIOBOOK/THUMBNAIL OPTIMIZATION (critical for digital):
- Square format thinking (works for audiobooks at 2400x2400px)
- Readable at 200x200 pixels - test this mentally
- 3D elements that pop on screen
- Vivid saturated colors that stand out in feeds
- Sharp edges and clean shapes, no muddy details

COMPOSITION TYPES YOU EXCEL AT:
1. **Text-Focused**: Title as main visual, creative typography, minimal imagery
2. **Silhouette**: Dramatic shapes, bold backlighting, stark contrast
3. **Geometric**: Abstract patterns, shapes representing themes, modern aesthetic

COLOR PSYCHOLOGY FOR THUMBNAILS:
- Use HIGH CONTRAST - muted colors disappear at small sizes
- Vivid neon accents grab scrolling attention
- Dark backgrounds with bright focal points
- Single bold accent color against neutral base

REQUIRED QUALITY TAGS (always include):
8k, graphic design poster, bold typography, high contrast,
modern minimalist, thumbnail-optimized, screen-vibrant colors,
geometric precision, flat design with depth, Saul Bass inspired,
audiobook cover quality, streaming thumbnail ready, vector-sharp edges,
scroll-stopping design

You create prompts for designs that STOP people scrolling."""

    def generate_prompts(self, outline: dict, characters: list[dict],
                         locations: list[dict], base_style: str, visual_style: dict = None) -> list[dict]:
        """Generate 3 unique prompts with different graphic compositions."""
        prompts = []

        protag_name = outline.get('protagonist', '').split(',')[0].strip()
        protag = next((c for c in characters if protag_name in c.get('name', '')), None)
        primary_loc = locations[0] if locations else {}

        for comp_type, comp_desc in self.COMPOSITION_TYPES:
            genre_adapt = get_genre_adaptation(base_style, comp_type)

            result = self._generate_for_composition(
                comp_type, comp_desc, genre_adapt,
                outline, protag, primary_loc, base_style, visual_style
            )

            prompts.append({
                "agent": "GRAPHIC",
                "composition": result.composition_type,
                "prompt": result.prompt,
                "style": result.style_applied,
                "color_palette": result.color_palette,
                "title_placement": result.title_placement,
            })

        return prompts

    # Example prompts for each composition type
    COMPOSITION_EXAMPLES = {
        "text_focused": """Bold typography-forward poster: the title "SHATTERED" dominates 70% of the frame, letters constructed from broken mirror shards reflecting a fragmented face. Each letter contains different angles of the protagonist's anguished expression. Deep black background, letters in sharp silver-white with crimson blood-red dripping from cracks. Geometric precision in letter construction, each shard catching different light. Single focal point where eyes are visible across multiple letters. Emotional tone: psychological fracture, identity crisis. 8k, bold graphic design, typography as art, high contrast, Saul Bass inspired, modern minimalist poster, thumbnail-perfect at any size.""",

        "silhouette": """Dramatic high-contrast silhouette: a lone gunslinger in full profile, hat and duster coat creating iconic western shape, standing against massive setting sun filling entire background. Sun rendered as perfect orange-red gradient circle. Ground is simple black horizon line. The figure is pure black with no internal detail except for a single glowing ember from a cigarette. Title "NO MERCY" in distressed western serif at bottom in burnt orange. Extreme simplicity, maximum impact. Emotional tone: lone justice, inevitable confrontation. 8k, graphic silhouette poster, bold contrast design, western noir style, thumbnail-optimized, streaming-ready, scroll-stopping design.""",

        "geometric": """Abstract geometric poster: the protagonist's face deconstructed into sharp triangular facets like shattered crystal, arranged in fragmented mosaic. Cool cyan and hot magenta create split lighting effect across the geometric face. Background is pure black with subtle circuit-board pattern barely visible. Title "PROTOCOL ZERO" in futuristic tech font with holographic gradient effect, positioned at top. Clean vector edges, mathematically precise angles. Neon accent lines connect facets. Emotional tone: digital identity, human vs machine. 8k, geometric graphic design, cyberpunk aesthetic, high contrast, audiobook cover quality, modern sci-fi poster, thumbnail-perfect design.""",
    }

    def _generate_for_composition(self, comp_type: str, comp_desc: str,
                                   genre_adapt: str, outline: dict,
                                   protag: dict, location: dict,
                                   base_style: str, visual_style: dict = None) -> PosterPromptSchema:
        """Generate a single prompt for a specific composition type."""
        protag_desc = self._build_char_desc(protag) if protag else "Unknown protagonist"

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

        # Get example for this composition type
        example = self.COMPOSITION_EXAMPLES.get(comp_type, self.COMPOSITION_EXAMPLES["silhouette"])

        prompt = f"""Create a GRAPHIC DESIGN MOVIE POSTER prompt for:

TITLE: "{outline.get('title', 'Untitled')}"
LOGLINE: {outline.get('logline', '')}

COMPOSITION TYPE: {comp_type.upper()} - {comp_desc}

PROTAGONIST: {protag_desc}
CENTRAL CONFLICT: {outline.get('central_conflict', '')}

GENRE ADAPTATION: {genre_adapt}
BASE STYLE: {base_style}
{style_info}

HERE IS AN EXAMPLE OF AN EXCELLENT {comp_type.upper()} PROMPT:

{example}

NOW generate output with:
- prompt: A SINGLE PARAGRAPH (200-350 words) for YOUR story following the same quality and structure as the example above. Include: START WITH STYLE PREFIX, bold graphic design elements, high contrast composition, specific color palette (limited to 2-4 colors), emotional tone, END WITH STYLE SUFFIX + thumbnail-optimized quality tags. Apply {genre_adapt}. Must work perfectly at thumbnail size (200x200px readable). Make it a scroll-stopping design.
  **CRITICAL MANDATORY REQUIREMENT**: The exact title text "{outline.get('title', 'Untitled')}" MUST appear VERBATIM in your prompt as a PROMINENT VISUAL ELEMENT with bold typography treatment. Example: 'Title "{outline.get('title', 'Untitled')}" in massive bold sans-serif dominating center'. This is NON-NEGOTIABLE.
- composition_type: "{comp_type}"
- color_palette: The specific limited color palette used (e.g., "black, silver-white, crimson blood-red")
- title_placement: Where the title appears (e.g., "dominating center", "bottom", "integrated into design")
- style_applied: "graphic {base_style}" """

        result = self.invoke_structured(prompt, PosterPromptSchema, max_tokens=2000)
        result.prompt = ensure_style_in_prompt(result.prompt, base_style)
        # CRITICAL: Validate title is in prompt - AI image generators need actual title text
        title = outline.get('title', 'Untitled')
        result.prompt = validate_title_in_prompt(result.prompt, title)
        return result

    def _build_char_desc(self, char: dict) -> str:
        """
        Build a shape-focused description for silhouette/graphic designs (NO character names).

        For graphic/silhouette posters, we focus on build and distinctive clothing shapes
        since detailed features won't be visible in high-contrast silhouettes.
        """
        if not char:
            return "a mysterious figure silhouette"

        physical = char.get('physical', {})
        parts = []

        # Gender
        gender = char.get('gender', 'person')
        parts.append(f"a {gender}")

        # Build (important for silhouette shape)
        if physical.get('build'):
            parts.append(f"{physical['build']} build")

        # Height (affects silhouette proportions)
        if physical.get('height'):
            parts.append(physical['height'])

        # Clothing silhouette (cloaks, hats, weapons create distinctive shapes)
        clothing = char.get('clothing', '')
        if clothing:
            parts.append(f"wearing {clothing}")

        # For silhouettes, add shape-defining elements
        role = char.get('role_in_story', '')
        if role == 'protagonist':
            parts.append("in a heroic stance")
        elif role == 'antagonist':
            parts.append("looming threateningly")

        return ", ".join(parts) + " silhouette" if parts else "a mysterious figure silhouette"


# =============================================================================
# JURY PANEL AGENTS
# =============================================================================

class PosterJuryImpactAgent(BaseStoryAgent):
    """Juror focused on visual impact and attention-grabbing."""

    @property
    def name(self) -> str:
        return "JURY_IMPACT"

    @property
    def role(self) -> str:
        return "Visual Impact Juror"

    @property
    def system_prompt(self) -> str:
        return """You are a SCROLL-STOPPING IMPACT expert for movie posters.

You judge posters like a Netflix thumbnail optimization specialist:
- Would this make someone STOP scrolling on their phone?
- Does it grab attention in under 2 SECONDS?
- Is there immediate visual punch and energy?
- Does the composition have a clear focal point?
- Would someone click this over 50 other thumbnails?

RED FLAGS (vote against these):
- Busy/cluttered composition with no focal point
- Muted/muddy colors that blend into backgrounds
- Generic stock-photo feel without distinctiveness
- Text illegible at small size
- No emotional hook (face, action, tension)

GREEN FLAGS (vote for these):
- Bold high-contrast design that POPS
- Emotional face or dynamic action as focal point
- Vivid eye-catching colors (especially warm accents)
- Clear single focal point with clean composition
- Works at thumbnail AND poster size

Your job: Find the poster that would WIN the click in a sea of options."""

    def vote(self, prompts: list[dict], outline: dict) -> JuryVoteSchema:
        """Return ranked top 3 choices as JuryVoteSchema."""
        prompt_list = "\n\n".join([
            f"[{i}] {p['agent']} - {p['composition']}:\n{p['prompt'][:300]}..."
            for i, p in enumerate(prompts)
        ])

        voting_prompt = f"""You are judging {len(prompts)} movie poster prompts for:
TITLE: "{outline.get('title', 'Untitled')}"
LOGLINE: {outline.get('logline', '')}

PROMPTS TO JUDGE:
{prompt_list}

As the VISUAL IMPACT juror, rank your TOP 3 choices based on:
- First impression / attention-grabbing power
- Would this stop someone scrolling?
- "Wow factor" and memorability

Provide your first_choice, second_choice, and third_choice as the indices (0-{len(prompts)-1}).
Include brief reasoning for your ranking."""

        return self.invoke_structured(voting_prompt, JuryVoteSchema, max_tokens=500)


class PosterJuryStoryAgent(BaseStoryAgent):
    """Juror focused on narrative clarity and story representation."""

    @property
    def name(self) -> str:
        return "JURY_STORY"

    @property
    def role(self) -> str:
        return "Story Clarity Juror"

    @property
    def system_prompt(self) -> str:
        return """You are a STORY COMMUNICATION expert for movie posters.

You judge posters like a book cover designer who knows: The image must SELL the story.

WHAT MAKES A POSTER TELL THE STORY:
- Does it immediately communicate the GENRE? (fantasy, thriller, romance, etc.)
- Is the PROTAGONIST clearly the hero of the image?
- Is there visual representation of the CONFLICT or stakes?
- Does the MOOD match the story's emotional core?
- Would a stranger understand what kind of story this is in 3 seconds?

RED FLAGS (vote against these):
- Generic imagery that could be any story
- Missing protagonist or unclear who the hero is
- No hint of conflict, danger, or stakes
- Mood mismatch (dark image for light story, etc.)
- No sense of the world or setting

GREEN FLAGS (vote for these):
- Genre is immediately clear from visual language
- Protagonist positioned as clear focal point
- Visual tension or conflict represented
- Emotional tone matches the story perfectly
- Setting/world communicated through background elements

Your job: Find the poster that makes someone say "I NEED to know this story!" """

    def vote(self, prompts: list[dict], outline: dict) -> JuryVoteSchema:
        """Return ranked top 3 choices as JuryVoteSchema."""
        prompt_list = "\n\n".join([
            f"[{i}] {p['agent']} - {p['composition']}:\n{p['prompt'][:300]}..."
            for i, p in enumerate(prompts)
        ])

        voting_prompt = f"""You are judging {len(prompts)} movie poster prompts for:
TITLE: "{outline.get('title', 'Untitled')}"
LOGLINE: {outline.get('logline', '')}
CENTRAL CONFLICT: {outline.get('central_conflict', '')}

PROMPTS TO JUDGE:
{prompt_list}

As the STORY CLARITY juror, rank your TOP 3 choices based on:
- How well does it convey the story's essence?
- Are characters and conflict represented?
- Does someone understand genre/tone at a glance?

Provide your first_choice, second_choice, and third_choice as the indices (0-{len(prompts)-1}).
Include brief reasoning for your ranking."""

        return self.invoke_structured(voting_prompt, JuryVoteSchema, max_tokens=500)


class PosterJuryAestheticAgent(BaseStoryAgent):
    """Juror focused on visual quality and artistic merit."""

    @property
    def name(self) -> str:
        return "JURY_AESTHETIC"

    @property
    def role(self) -> str:
        return "Aesthetic Quality Juror"

    @property
    def system_prompt(self) -> str:
        return """You are an ART DIRECTOR judging poster prompts for VISUAL EXCELLENCE.

You judge like a gallery curator deciding what deserves to be framed:

WHAT MAKES A POSTER VISUALLY EXCELLENT:
- Masterful COMPOSITION - balanced, intentional placement of elements
- Sophisticated COLOR PALETTE - harmonious, mood-appropriate, professional
- Artistic TECHNIQUE specified - lighting, texture, style with intention
- PROFESSIONAL QUALITY tags that ensure high-end output
- UNIQUE AESTHETIC that stands out from generic AI art

RED FLAGS (vote against these):
- Boring, centered composition with no visual interest
- Random color choices without palette cohesion
- Missing quality tags (8k, detailed, etc.)
- Generic "fantasy art" without specific style direction
- Cluttered or unbalanced element arrangement

GREEN FLAGS (vote for these):
- Dynamic composition using rule of thirds, leading lines
- Intentional color palette with primary/accent colors specified
- Specific artist inspiration or style reference
- Atmospheric elements (volumetric light, fog, depth)
- Balance of detail and negative space

Your job: Find the poster that would look STUNNING as actual generated art."""

    def vote(self, prompts: list[dict], outline: dict) -> JuryVoteSchema:
        """Return ranked top 3 choices as JuryVoteSchema."""
        prompt_list = "\n\n".join([
            f"[{i}] {p['agent']} - {p['composition']}:\n{p['prompt'][:300]}..."
            for i, p in enumerate(prompts)
        ])

        voting_prompt = f"""You are judging {len(prompts)} movie poster prompts for:
TITLE: "{outline.get('title', 'Untitled')}"

PROMPTS TO JUDGE:
{prompt_list}

As the AESTHETIC QUALITY juror, rank your TOP 3 choices based on:
- Would this look beautiful as actual art?
- Composition balance and visual sophistication
- Artistic merit and professional quality

Provide your first_choice, second_choice, and third_choice as the indices (0-{len(prompts)-1}).
Include brief reasoning for your ranking."""

        return self.invoke_structured(voting_prompt, JuryVoteSchema, max_tokens=500)


# =============================================================================
# POSTER JURY SUPERVISOR
# =============================================================================

class PosterJurySupervisor:
    """Orchestrates the 3-agent jury voting process."""

    def __init__(self, model: str):
        self.model = model
        self.jurors = [
            PosterJuryImpactAgent(model=model),
            PosterJuryStoryAgent(model=model),
            PosterJuryAestheticAgent(model=model),
        ]

    def run_voting(self, prompts: list[dict], outline: dict) -> dict:
        """
        Run jury voting and return results.

        Each juror ranks their top 3 via JuryVoteSchema:
        - 1st place (first_choice): 3 points
        - 2nd place (second_choice): 2 points
        - 3rd place (third_choice): 1 point

        Returns dict with winners and metadata.
        """
        votes = []
        scores = {i: 0 for i in range(len(prompts))}

        # Collect votes from each juror
        for juror in self.jurors:
            vote_result = juror.vote(prompts, outline)  # Returns JuryVoteSchema
            ranked = [vote_result.first_choice, vote_result.second_choice, vote_result.third_choice]

            votes.append({
                "juror": juror.name,
                "ranked": ranked,  # [1st_idx, 2nd_idx, 3rd_idx]
                "reasoning": vote_result.reasoning,
            })

            # Award points: 3, 2, 1 (validate indices)
            if 0 <= ranked[0] < len(prompts):
                scores[ranked[0]] += 3
            if 0 <= ranked[1] < len(prompts):
                scores[ranked[1]] += 2
            if 0 <= ranked[2] < len(prompts):
                scores[ranked[2]] += 1

        # Sort by score descending
        sorted_indices = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

        # Get top 3 winners
        winners = []
        for idx in sorted_indices[:3]:
            winner = prompts[idx].copy()
            winner["score"] = scores[idx]
            winners.append(winner)

        return {
            "all_prompts": prompts,
            "winners": winners,
            "voting_metadata": {
                "total_candidates": len(prompts),
                "jurors": [j.name for j in self.jurors],
                "votes": votes,
                "scores": {str(k): v for k, v in scores.items()},
            }
        }


# =============================================================================
# SHOT FRAME PROMPT AGENTS
# =============================================================================

class ShotFramePromptCreatorAgent(BaseStoryAgent):
    """Creates detailed first/last frame prompts for storyboard shots."""

    @property
    def name(self) -> str:
        return "SHOT_FRAME_PROMPT_CREATOR"

    @property
    def role(self) -> str:
        return "AI image prompt engineer for video frame generation"

    @property
    def system_prompt(self) -> str:
        return """You are a MASTER prompt engineer for AI image/video generation.

Your job is to create EXTREMELY DETAILED prompts for the FIRST and LAST frames of a video shot.

CRITICAL RULES:
1. NEVER use character names (AI doesn't know "Rhea" or "Elena")
2. ALWAYS use full physical descriptions: "a young woman with auburn hair, emerald eyes, wearing a tattered cloak"
3. Match the SHOT SIZE for framing:
   - WIDE: Full body, environment visible, characters small in frame
   - MEDIUM: Waist-up, characters prominent, some background
   - CLOSE-UP: Face/shoulders only, emotional detail, blurred background
   - EXTREME CLOSE-UP: Eyes, hands, or specific detail only
   - OVER-SHOULDER: One character's back/shoulder, facing another
   - POV: What character sees, no character visible
   - AERIAL: Bird's eye view, landscape dominant

4. Match TIME OF DAY for lighting:
   - DAY: Bright, natural sunlight, clear shadows
   - NIGHT: Dark, moonlight or artificial light, deep shadows
   - DAWN: Soft pink/orange glow, long shadows, misty
   - DUSK: Golden hour, amber light, warm tones
   - MORNING: Fresh light, dew, crisp shadows
   - AFTERNOON: Harsh overhead sun, short shadows

5. FIRST FRAME shows the START of the action
6. LAST FRAME shows the END of the action (after camera movement, after dialogue)

OUTPUT FORMAT:
- Each prompt: 300-500 words, single paragraph, natural language
- Include: character positions, poses, expressions, clothing, environment details, lighting, atmosphere, quality tags
- End with style tags: "cinematic, 8k, detailed, [art_style]"
"""

    def create_prompts(
        self,
        shot: dict,
        characters_in_shot: list[dict],
        location_profile: dict,
        setting_context: str = "",
        art_style: str = "fantasy"
    ) -> ShotFramePromptSchema:
        """Generate first and last frame prompts for a shot."""

        # Build character descriptions (NO NAMES)
        char_descriptions = []
        for char in characters_in_shot:
            desc = build_full_character_description(char, include_role_hint=True)
            role = char.get('role_in_story', 'character')
            char_descriptions.append(f"THE {role.upper()}: {desc}")

        chars_text = "\n".join(char_descriptions) if char_descriptions else "No characters in frame"

        # Build location context
        key_features = location_profile.get('key_features', [])
        if isinstance(key_features, list):
            key_features_str = ', '.join(key_features)
        else:
            key_features_str = str(key_features)

        loc_text = f"""
LOCATION: {location_profile.get('name', 'Unknown')}
TYPE: {location_profile.get('type', 'interior')}
DESCRIPTION: {location_profile.get('description', '')}
ATMOSPHERE: {location_profile.get('atmosphere', '')}
KEY FEATURES: {key_features_str}
SENSORY DETAILS: {location_profile.get('sensory_details', '')}
"""

        # Build shot context
        shot_text = f"""
SHOT SIZE: {shot.get('shot_size', 'MEDIUM')}
CAMERA MOVEMENT: {shot.get('camera_movement', 'STATIC')}
TIME OF DAY: {shot.get('time_of_day', 'DAY')}
INT/EXT: {shot.get('int_ext', 'INT.')}
LOCATION DETAIL: {shot.get('location_detail', '')}
ACTION: {shot.get('action', '')}
VISUAL STYLE NOTES: {shot.get('visual_style_notes', '')}
DURATION: {shot.get('duration_seconds', 10)} seconds
"""

        # Dialogue context (what's being said during shot)
        dialogue_lines = shot.get('dialogue', [])
        if dialogue_lines:
            dialogue_text = "\n".join([
                f"- {d.get('character', 'CHARACTER')}: \"{d.get('line', '')}\""
                for d in dialogue_lines
            ])
        else:
            dialogue_text = "No dialogue in this shot"

        prompt = f"""Generate FIRST FRAME and LAST FRAME image prompts for this shot:

SHOT DETAILS:
{shot_text}

CHARACTERS IN FRAME (use these descriptions, NOT names):
{chars_text}

LOCATION PROFILE:
{loc_text}

DIALOGUE DURING SHOT:
{dialogue_text}

SETTING CONTEXT: {setting_context if setting_context else "Fantasy/adventure setting"}
ART STYLE: {art_style}

REQUIREMENTS:
1. FIRST FRAME: Describe the OPENING moment - character positions, expressions, environment as the shot BEGINS
2. LAST FRAME: Describe the ENDING moment - after camera movement completes, after any action/dialogue
3. Use FULL physical descriptions for characters (hair color, eye color, build, clothing) - NO NAMES
4. Match shot_size for framing (WIDE = full body + environment, CLOSE-UP = face only, etc.)
5. Match time_of_day for lighting and shadows
6. Include atmosphere, mood, and visual_style_notes details
7. Each prompt: 300-500 words, single paragraph, end with "cinematic, 8k, detailed, {art_style}"

The FIRST and LAST frame should show PROGRESSION - the camera moves, characters shift position, expressions change."""

        return self.invoke_structured(prompt, ShotFramePromptSchema, max_tokens=3000)

    def revise_prompts(
        self,
        original: ShotFramePromptSchema,
        critique: ShotFrameCritiqueSchema,
        shot: dict,
        characters_in_shot: list[dict],
        location_profile: dict
    ) -> ShotFramePromptSchema:
        """Revise prompts based on critic feedback."""

        suggestions = "\n".join(f"- {s}" for s in critique.suggestions)

        prompt = f"""REVISE these shot frame prompts based on critic feedback:

ORIGINAL FIRST FRAME:
{original.firstframe_prompt}

ORIGINAL LAST FRAME:
{original.lastframe_prompt}

CRITIC SCORES:
- Character Accuracy: {critique.character_accuracy_score}/10
- Location Accuracy: {critique.location_accuracy_score}/10
- Framing (shot_size): {critique.framing_accuracy_score}/10
- Lighting/Mood: {critique.lighting_mood_score}/10
- Action Continuity: {critique.action_continuity_score}/10
- No Names Used: {critique.no_names_score}/10

SUGGESTIONS FOR IMPROVEMENT:
{suggestions}

SHOT CONTEXT:
- Shot Size: {shot.get('shot_size', 'MEDIUM')}
- Time of Day: {shot.get('time_of_day', 'DAY')}
- Action: {shot.get('action', '')}

Fix ALL issues, especially any scores below 8. Maintain 300-500 words per prompt."""

        return self.invoke_structured(prompt, ShotFramePromptSchema, max_tokens=3000)


class ShotFrameCriticAgent(BaseStoryAgent):
    """Critiques shot frame prompts for accuracy and quality."""

    @property
    def name(self) -> str:
        return "SHOT_FRAME_CRITIC"

    @property
    def role(self) -> str:
        return "Quality reviewer of shot frame image prompts"

    @property
    def system_prompt(self) -> str:
        return """You are a CRITICAL reviewer of AI image prompts for video frame generation.

EVALUATION CRITERIA:

1. CHARACTER ACCURACY (Score 1-10)
   - Do character descriptions match their profiles (hair, eyes, build, clothing)?
   - Are poses/expressions appropriate for the action?

2. LOCATION ACCURACY (Score 1-10)
   - Does the environment match the location profile?
   - Are key features mentioned?
   - Does atmosphere match?

3. FRAMING ACCURACY (Score 1-10)
   - Does framing match shot_size?
   - WIDE should show full bodies and environment
   - CLOSE-UP should focus on face/detail
   - MEDIUM should show waist-up

4. LIGHTING/MOOD (Score 1-10)
   - Does lighting match time_of_day?
   - Is visual_style_notes reflected?
   - Is the mood appropriate?

5. ACTION CONTINUITY (Score 1-10)
   - Does first→last frame show logical progression?
   - If camera moves, is change reflected?
   - Do character positions change appropriately?

6. NO NAMES USED (Score 1-10)
   - Are character NAMES completely absent?
   - Only physical descriptions should be used
   - AI generators don't know fictional names!

DECISION: needs_revision = true if ANY score < 7
"""

    def critique(
        self,
        prompts: ShotFramePromptSchema,
        shot: dict,
        characters_in_shot: list[dict],
        location_profile: dict
    ) -> ShotFrameCritiqueSchema:
        """Evaluate shot frame prompts."""

        # Build expected character descriptions
        char_names = [c.get('name', '') for c in characters_in_shot]
        char_profiles = "\n".join([
            f"- {c.get('name', 'Unknown')}: {c.get('gender', '')}, {c.get('physical', {}).get('hair_color', '')} hair, {c.get('physical', {}).get('eye_color', '')} eyes, wearing {c.get('clothing', '')}"
            for c in characters_in_shot
        ])

        key_features = location_profile.get('key_features', [])
        if isinstance(key_features, list):
            key_features_str = ', '.join(key_features)
        else:
            key_features_str = str(key_features)

        prompt = f"""EVALUATE these shot frame prompts:

FIRST FRAME PROMPT:
{prompts.firstframe_prompt}

LAST FRAME PROMPT:
{prompts.lastframe_prompt}

SHOT SPECIFICATIONS:
- Shot Size: {shot.get('shot_size', 'MEDIUM')}
- Time of Day: {shot.get('time_of_day', 'DAY')}
- Camera Movement: {shot.get('camera_movement', 'STATIC')}
- Action: {shot.get('action', '')}
- Visual Style Notes: {shot.get('visual_style_notes', '')}

CHARACTER PROFILES (names should NOT appear in prompts):
{char_profiles}

CHARACTER NAMES TO CHECK FOR (these should NOT be in prompts):
{', '.join(char_names)}

LOCATION PROFILE:
- Name: {location_profile.get('name', '')}
- Description: {location_profile.get('description', '')}
- Atmosphere: {location_profile.get('atmosphere', '')}
- Key Features: {key_features_str}

Score each category 1-10 and provide specific suggestions for any score below 8.
Check that character NAMES do not appear - only physical descriptions."""

        return self.invoke_structured(prompt, ShotFrameCritiqueSchema, max_tokens=1500)


# =============================================================================
# SHOT FRAME PROMPT ORCHESTRATION
# =============================================================================

def generate_shot_frame_prompts(
    shot: dict,
    all_characters: list[dict],
    all_locations: list[dict],
    setting_context: str = "",
    art_style: str = "fantasy",
    model: str = None,
    max_revisions: int = 2,
) -> dict:
    """
    Generate first/last frame prompts for a storyboard shot.

    Args:
        shot: Shot dict from storyboard
        all_characters: All character profiles from codex
        all_locations: All location profiles from codex
        setting_context: World setting for style consistency
        art_style: Art style to apply
        model: LLM model to use
        max_revisions: Maximum revision cycles

    Returns:
        Dict with firstframe_prompt, lastframe_prompt, and metadata
    """
    from src.config import DEFAULT_MODEL
    model = model or DEFAULT_MODEL

    creator = ShotFramePromptCreatorAgent(model=model)
    critic = ShotFrameCriticAgent(model=model)

    # Find characters in this shot
    chars_in_frame = shot.get('characters_in_frame', [])
    characters_in_shot = [
        c for c in all_characters
        if any(name.upper() in c.get('name', '').upper() for name in chars_in_frame)
    ]

    # Find location for this shot
    shot_location = shot.get('location', '')
    location_profile = next(
        (loc for loc in all_locations if shot_location.upper() in loc.get('name', '').upper()),
        {"name": shot_location, "description": "", "atmosphere": "", "key_features": []}
    )

    # Initial generation
    result = creator.create_prompts(
        shot, characters_in_shot, location_profile, setting_context, art_style
    )

    critique_history = []
    revision_count = 0

    # Critique-revision loop
    for i in range(max_revisions):
        critique = critic.critique(result, shot, characters_in_shot, location_profile)
        critique_dict = critique.model_dump()
        critique_history.append(critique_dict)

        min_score = min(
            critique.character_accuracy_score,
            critique.location_accuracy_score,
            critique.framing_accuracy_score,
            critique.lighting_mood_score,
            critique.action_continuity_score,
            critique.no_names_score,
        )

        if not critique.needs_revision and min_score >= 7:
            break

        if i < max_revisions - 1:
            result = creator.revise_prompts(
                result, critique, shot, characters_in_shot, location_profile
            )
            revision_count += 1

    final_critique = critique_history[-1]

    return {
        "firstframe_prompt": result.firstframe_prompt,
        "lastframe_prompt": result.lastframe_prompt,
        "shot_size_applied": result.shot_size_applied,
        "time_of_day_applied": result.time_of_day_applied,
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