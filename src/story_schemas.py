"""
Pydantic models for structured story output.

These schemas define the JSON structure for:
- Phase 1: Story outline with acts and scenes
- Phase 2: Character and location profiles
- Phase 3: Narrative prose
"""

from typing import Optional
from pydantic import BaseModel, Field


# =============================================================================
# Phase 1: Story Outline Schemas
# =============================================================================

class SceneSchema(BaseModel):
    """A single scene within an act."""
    scene_number: int = Field(..., description="Scene number within the act")
    location: str = Field(..., description="Where the scene takes place")
    characters: list[str] = Field(..., description="Characters present in scene")
    happens: str = Field(..., description="What happens in this scene")
    outcome: Optional[str] = Field(
        None,
        description="Try-fail cycle outcome: 'YES, BUT', 'NO, AND', or null for final resolution"
    )


class ActSchema(BaseModel):
    """A single act containing multiple scenes."""
    act_number: int = Field(..., description="Act number (1, 2, or 3)")
    act_name: str = Field(..., description="Name of the act (e.g., 'Setup', 'Confrontation', 'Resolution')")
    scenes: list[SceneSchema] = Field(..., description="Scenes in this act")


class OutlineSchema(BaseModel):
    """Complete story outline with 3 acts."""
    title: str = Field(..., description="Working title for the story")
    logline: str = Field(..., description="One-sentence story summary")
    protagonist: str = Field(..., description="Main character name/description")
    antagonist: str = Field(..., description="Opposing force name/description")
    central_conflict: str = Field(..., description="Core conflict driving the story")
    acts: list[ActSchema] = Field(..., description="The 3 acts of the story")


class CritiqueSchema(BaseModel):
    """Critique from a critic agent."""
    critic_name: str = Field(..., description="Name of the critic agent")
    issues: list[str] = Field(..., description="List of issues found")
    suggestions: list[str] = Field(..., description="Suggested improvements")
    severity: str = Field(..., description="Overall severity: 'minor', 'moderate', 'major'")


# =============================================================================
# Name Debate Schemas (Pre-Phase 2)
# =============================================================================

class NameProposal(BaseModel):
    """A proposed character name from a naming agent."""
    first_name: str = Field(..., description="First name starting with required initial")
    last_name: str = Field(..., description="Last name starting with required initial")
    reasoning: str = Field(..., description="Why this name fits the character and setting")


class NameCritiqueReview(BaseModel):
    """Critique of a single name proposal."""
    proposal_index: int = Field(..., description="Which proposal (0, 1, or 2)")
    strengths: str = Field(..., description="What works well about this name")
    weaknesses: str = Field(..., description="What could be improved")
    score: int = Field(..., ge=1, le=10, description="Score 1-10")


class NameCritiques(BaseModel):
    """All critiques from one agent."""
    reviews: list[NameCritiqueReview] = Field(
        ..., description="Reviews of all 3 proposals", min_length=3, max_length=3
    )


class NameVote(BaseModel):
    """An agent's vote for the best name."""
    voted_for: int = Field(..., ge=0, le=2, description="Index of proposal voted for (0, 1, or 2)")
    vote_reasoning: str = Field(..., description="Why this name is the best choice")


# =============================================================================
# Phase 2: Character & Location Schemas
# =============================================================================

class PhysicalDescriptionSchema(BaseModel):
    """Physical attributes of a character."""
    height: str = Field(..., description="Height description")
    build: str = Field(..., description="Body type/build")
    hair_color: str = Field(..., description="Hair color and style")
    eye_color: str = Field(..., description="Eye color")
    distinguishing_features: str = Field(..., description="Scars, tattoos, unique features")


class CharacterSchema(BaseModel):
    """Detailed character profile."""
    id: Optional[str] = Field(None, description="Unique ID like 'char_001' (assigned in Phase 2)")
    name: str = Field(..., description="Character's full name")
    gender: str = Field(..., description="Character's gender")
    age: str = Field(..., description="Age or age range")
    physical: PhysicalDescriptionSchema = Field(..., description="Physical appearance")
    clothing: str = Field(..., description="Typical clothing/style")
    personality_traits: list[str] = Field(..., description="3-5 key personality traits")
    backstory: str = Field(..., description="Brief background (2-3 sentences)")
    motivation: str = Field(..., description="What drives this character")
    role_in_story: str = Field(..., description="'protagonist', 'antagonist', or 'supporting'")
    arc: str = Field(..., description="Character's growth/change arc")


class LocationSchema(BaseModel):
    """Detailed location profile."""
    id: Optional[str] = Field(None, description="Unique ID like 'loc_001' (assigned in Phase 2)")
    name: str = Field(..., description="Location name")
    type: str = Field(..., description="Type of location (city, forest, building, etc.)")
    description: str = Field(..., description="Visual description (2-3 sentences)")
    atmosphere: str = Field(..., description="Mood/feeling of the place")
    key_features: list[str] = Field(..., description="3-5 notable features")
    sensory_details: str = Field(..., description="Sounds, smells, textures")
    connection_to_story: str = Field(..., description="How this location matters to the plot")


class CharactersAndLocationsSchema(BaseModel):
    """Combined output for Phase 2."""
    characters: list[CharacterSchema] = Field(..., description="All character profiles")
    locations: list[LocationSchema] = Field(..., description="All location profiles")


class CharacterListSchema(BaseModel):
    """Wrapper for character list output."""
    characters: list[CharacterSchema] = Field(..., description="All character profiles")


class LocationListSchema(BaseModel):
    """Wrapper for location list output."""
    locations: list[LocationSchema] = Field(..., description="All location profiles")


class ShotPromptCritiqueSchema(BaseModel):
    """Critique for shot/poster image prompts."""
    issues: list[str] = Field(default=[], description="List of issues found")
    suggestions: list[str] = Field(default=[], description="Suggested improvements")
    severity: str = Field(..., description="Severity: 'minor', 'moderate', 'major'")


# =============================================================================
# Phase 3: Narrative Schemas
# =============================================================================

class SceneProseSchema(BaseModel):
    """Enforced structure for scene prose output via LangChain structured output.

    This schema forces the LLM to generate proper multi-paragraph prose
    instead of one-liner summaries.
    """

    opening_paragraph: str = Field(
        ...,
        description=(
            "Opening paragraph that establishes the setting, mood, and introduces "
            "the characters present. Use sensory details from location profile. "
            "MINIMUM 100 words, aim for 120-150 words."
        )
    )

    middle_paragraphs: list[str] = Field(
        ...,
        description=(
            "2-4 paragraphs developing the scene. Include dialogue if multiple "
            "characters are present. Show conflict/action progressing. Each "
            "paragraph should be 80-120 words."
        ),
        min_length=2,
    )

    closing_paragraph: str = Field(
        ...,
        description=(
            "Closing paragraph that resolves the scene's immediate conflict or "
            "creates a hook to the next scene. End with impact. "
            "MINIMUM 80 words, aim for 100-120 words."
        )
    )

    def to_prose(self) -> str:
        """Assemble paragraphs into continuous prose."""
        paragraphs = [self.opening_paragraph]
        paragraphs.extend(self.middle_paragraphs)
        paragraphs.append(self.closing_paragraph)
        return "\n\n".join(paragraphs)


class NarrativeSceneSchema(BaseModel):
    """A written scene with prose."""
    scene_number: int = Field(..., description="Scene number")
    location: str = Field(..., description="Scene location")
    characters: list[str] = Field(..., description="Characters in scene")
    time: str = Field(..., description="Time of day/relative time")
    text: str = Field(..., description="The actual narrative prose")
    # NOTE: shots are added later in Phase 3b via dict manipulation, not via this schema


class NarrativeActSchema(BaseModel):
    """An act containing written scenes."""
    act_number: int = Field(..., description="Act number")
    act_name: str = Field(..., description="Name of the act")
    scenes: list[NarrativeSceneSchema] = Field(..., description="Written scenes")


class NarrativeSchema(BaseModel):
    """Complete narrative with all written prose."""
    title: str = Field(..., description="Story title")
    acts: list[NarrativeActSchema] = Field(..., description="All acts with prose")


# =============================================================================
# Complete Story Schema (Final Output)
# =============================================================================

# =============================================================================
# Phase 4: Character Image Prompt Schemas
# =============================================================================

class CharacterPromptSchema(BaseModel):
    """Structured output for character image prompt generation."""
    prompt: str = Field(
        ...,
        description="The detailed image prompt, 300-500 words, single paragraph"
    )
    shot_type: str = Field(
        ...,
        description="Type of shot: 'bust', 'medium', or 'full body'"
    )
    key_features_included: list[str] = Field(
        ...,
        description="List of key features described in prompt (e.g., 'scar on left cheek', 'leather jacket')"
    )


class CharacterPromptCritique(BaseModel):
    """Critique scores for character image prompt quality."""
    face_detail_score: int = Field(
        ..., ge=1, le=10,
        description="Score 1-10 for face description completeness"
    )
    clothing_detail_score: int = Field(
        ..., ge=1, le=10,
        description="Score 1-10 for clothing description detail"
    )
    distinguishing_marks_score: int = Field(
        ..., ge=1, le=10,
        description="Score 1-10 for scars, tattoos, jewelry description"
    )
    pose_expression_score: int = Field(
        ..., ge=1, le=10,
        description="Score 1-10 for pose and expression clarity"
    )
    quality_tags_score: int = Field(
        ..., ge=1, le=10,
        description="Score 1-10 for lighting, resolution, style tags"
    )
    overall_score: int = Field(
        ..., ge=1, le=10,
        description="Overall quality score 1-10"
    )
    needs_revision: bool = Field(
        ...,
        description="True if any category needs improvement"
    )
    suggestions: list[str] = Field(
        ...,
        description="Specific suggestions for improvement"
    )


# =============================================================================
# Phase 4: Location Image Prompt Schemas
# =============================================================================

class LocationPromptSchema(BaseModel):
    """Structured output for location image prompt generation."""
    prompt: str = Field(
        ...,
        description="The detailed image prompt, 300-500 words, single paragraph"
    )
    shot_type: str = Field(
        ...,
        description="Type of shot: 'wide establishing', 'interior', 'aerial', 'ground-level', 'panoramic'"
    )
    time_of_day: str = Field(
        ...,
        description="Time depicted: 'dawn', 'morning', 'noon', 'afternoon', 'dusk', 'night'"
    )
    key_features_included: list[str] = Field(
        ...,
        description="List of key features described (e.g., 'crumbling stone walls', 'misty forest')"
    )


class LocationPromptCritique(BaseModel):
    """Critique scores for location image prompt quality."""
    architecture_structure_score: int = Field(
        ..., ge=1, le=10,
        description="Score 1-10 for architecture and structure detail"
    )
    lighting_time_score: int = Field(
        ..., ge=1, le=10,
        description="Score 1-10 for lighting and time of day"
    )
    atmosphere_weather_score: int = Field(
        ..., ge=1, le=10,
        description="Score 1-10 for atmosphere and weather effects"
    )
    textures_materials_score: int = Field(
        ..., ge=1, le=10,
        description="Score 1-10 for textures and materials"
    )
    composition_depth_score: int = Field(
        ..., ge=1, le=10,
        description="Score 1-10 for composition and depth layers"
    )
    quality_tags_score: int = Field(
        ..., ge=1, le=10,
        description="Score 1-10 for quality and style tags"
    )
    overall_score: int = Field(
        ..., ge=1, le=10,
        description="Overall quality score 1-10"
    )
    needs_revision: bool = Field(
        ...,
        description="True if any category needs improvement"
    )
    suggestions: list[str] = Field(
        ...,
        description="Specific suggestions for improvement"
    )


# =============================================================================
# Phase 3b: Storyboard Schemas (Industry-Standard Format)
# =============================================================================

class DialogueLineSchema(BaseModel):
    """A single line of dialogue in a shot."""
    character: str = Field(..., description="Character name (uppercase)")
    parenthetical: str = Field(
        default="",
        description="Tone/action note (e.g., 'whispered', 'angrily', 'looking away')"
    )
    line: str = Field(..., description="The dialogue text")


class ShotSchema(BaseModel):
    """A single shot in industry-standard screenplay/storyboard format."""

    # Shot identification
    shot_number: int = Field(..., description="Sequential shot number within scene")
    duration_seconds: int = Field(
        ..., ge=5, le=20,
        description="Duration in seconds (10-15 typical)"
    )

    # Slugline components
    int_ext: str = Field(
        ...,
        description="Interior or exterior: 'INT.' or 'EXT.'"
    )
    location: str = Field(..., description="Location name from codex")
    location_detail: str = Field(
        default="",
        description="Specific area (e.g., 'NEAR THE WINDOW', 'AT THE DESK')"
    )
    time_of_day: str = Field(
        ...,
        description="Time: 'DAY', 'NIGHT', 'DAWN', 'DUSK', 'AFTERNOON', 'MORNING'"
    )

    # Shot specifications
    shot_size: str = Field(
        ...,
        description="WIDE, MEDIUM, CLOSE-UP, EXTREME CLOSE-UP, OVER-SHOULDER, POV, AERIAL"
    )
    camera_movement: str = Field(
        ...,
        description="STATIC, PAN LEFT, PAN RIGHT, TILT UP, TILT DOWN, DOLLY IN, DOLLY OUT, TRACKING, CRANE, PUSH IN"
    )

    # Action line
    action: str = Field(
        ...,
        description="Present tense description of what we SEE (character positions, actions, visual details)"
    )

    # Characters and dialogue
    characters_in_frame: list[str] = Field(
        default=[],
        description="Character names visible in shot (uppercase, e.g., 'CALISTA')"
    )
    character_ids: list[str] = Field(
        default=[],
        description="Character IDs visible in shot (e.g., ['char_001', 'char_002'])"
    )
    location_id: Optional[str] = Field(
        None,
        description="Location ID for this shot (e.g., 'loc_001')"
    )
    dialogue: list[DialogueLineSchema] = Field(
        default=[],
        description="Dialogue lines in this shot"
    )

    # Audio
    sfx: list[str] = Field(
        default=[],
        description="Sound effects (e.g., 'Door creaking', 'Thunder rumbling')"
    )
    music_cue: str = Field(
        default="",
        description="Music direction (e.g., 'Tension strings begin', 'Theme swells')"
    )
    ambient: str = Field(
        default="",
        description="Background ambience (e.g., 'Rain on windows', 'Crowd murmur')"
    )

    # Transition
    transition: str = Field(
        ...,
        description="CUT TO, DISSOLVE TO, FADE TO BLACK, MATCH CUT, SMASH CUT"
    )

    # AI video generation notes
    visual_style_notes: str = Field(
        default="",
        description="Additional notes for AI video (mood, effects, style)"
    )


class StoryboardSchema(BaseModel):
    """Complete storyboard for a single scene."""
    scene_id: str = Field(..., description="Unique ID: 'act{N}_scene{M}'")
    scene_title: str = Field(..., description="Brief scene description")
    total_duration_seconds: int = Field(..., description="Sum of all shot durations")
    shot_count: int = Field(..., description="Number of shots")
    shots: list[ShotSchema] = Field(..., description="All shots in sequence", min_length=1)


class VisualCritiqueSchema(BaseModel):
    """Visual critic's evaluation of storyboard."""
    location_clarity_score: int = Field(..., ge=1, le=10, description="INT./EXT. and location specificity")
    shot_composition_score: int = Field(..., ge=1, le=10, description="Shot size and depth layers")
    camera_work_score: int = Field(..., ge=1, le=10, description="Camera movement motivation")
    lighting_time_score: int = Field(..., ge=1, le=10, description="Lighting and time consistency")
    character_blocking_score: int = Field(..., ge=1, le=10, description="Character positions clarity")
    visual_storytelling_score: int = Field(..., ge=1, le=10, description="Visual focus and emphasis")
    overall_score: int = Field(..., ge=1, le=10, description="Overall visual quality")
    needs_revision: bool = Field(..., description="True if any score < 7")
    suggestions: list[str] = Field(..., description="Specific visual improvements")


class DialogueCritiqueSchema(BaseModel):
    """Dialogue critic's evaluation of storyboard."""
    dialogue_length_score: int = Field(..., ge=1, le=10, description="Dialogue fits duration (25-35 words)")
    delivery_notes_score: int = Field(..., ge=1, le=10, description="Parentheticals for tone")
    natural_flow_score: int = Field(..., ge=1, le=10, description="Natural spoken dialogue")
    character_voice_score: int = Field(..., ge=1, le=10, description="Consistent character voice")
    audio_design_score: int = Field(..., ge=1, le=10, description="SFX, music, ambient quality")
    overall_score: int = Field(..., ge=1, le=10, description="Overall dialogue quality")
    needs_revision: bool = Field(..., description="True if any score < 7")
    word_count_violations: list[int] = Field(
        default=[],
        description="Shot numbers exceeding word limits"
    )
    suggestions: list[str] = Field(..., description="Specific dialogue improvements")


class ContinuityCritiqueSchema(BaseModel):
    """Continuity critic's evaluation of storyboard."""
    shot_flow_score: int = Field(..., ge=1, le=10, description="Logical shot connections, 180° rule")
    character_continuity_score: int = Field(..., ge=1, le=10, description="Character position consistency")
    location_continuity_score: int = Field(..., ge=1, le=10, description="Environment consistency")
    story_context_score: int = Field(..., ge=1, le=10, description="Scene purpose and plot points")
    pacing_rhythm_score: int = Field(..., ge=1, le=10, description="Shot variety and timing")
    overall_coherence_score: int = Field(..., ge=1, le=10, description="Works as video sequence")
    overall_score: int = Field(..., ge=1, le=10, description="Overall continuity quality")
    needs_revision: bool = Field(..., description="True if any score < 7")
    continuity_errors: list[str] = Field(
        default=[],
        description="Specific continuity issues found"
    )
    suggestions: list[str] = Field(..., description="Specific continuity fixes")


# =============================================================================
# Complete Story Schema (Final Output)
# =============================================================================

class StoryMetadataSchema(BaseModel):
    """Metadata about the story generation process."""
    phase1_cycles: int = Field(..., description="Number of critique-revision cycles in Phase 1")
    phase2_cycles: int = Field(..., description="Number of critique-revision cycles in Phase 2")
    phase3_cycles: int = Field(..., description="Number of critique-revision cycles in Phase 3")
    model_used: str = Field(..., description="LLM model used for generation")


class CompleteStorySchema(BaseModel):
    """Complete story output combining all phases."""
    outline: OutlineSchema = Field(..., description="Phase 1: Story outline")
    characters: list[CharacterSchema] = Field(..., description="Phase 2: Character profiles")
    locations: list[LocationSchema] = Field(..., description="Phase 2: Location profiles")
    narrative: NarrativeSchema = Field(..., description="Phase 3: Written narrative")
    metadata: StoryMetadataSchema = Field(..., description="Generation metadata")


# =============================================================================
# Phase 4: Generic Image Prompt Schemas
# =============================================================================

class ImagePromptSchema(BaseModel):
    """Structured output for generic image prompts (character, location, scene)."""
    prompt: str = Field(
        ...,
        description="The detailed image prompt, 150-400 words depending on type"
    )
    style_applied: str = Field(
        ...,
        description="The art style applied to this prompt"
    )
    key_elements: list[str] = Field(
        ...,
        description="Key visual elements included in the prompt"
    )


class PosterPromptSchema(BaseModel):
    """Structured output for movie poster prompts."""
    prompt: str = Field(
        ...,
        description="The detailed poster prompt, 250-400 words"
    )
    composition_type: str = Field(
        ...,
        description="Type: 'character_portrait', 'action_scene', 'symbolic', 'minimalist', 'panorama', 'collage', 'text_focused', 'silhouette', 'geometric'"
    )
    color_palette: str = Field(
        ...,
        description="Primary colors and mood (e.g., 'teal-orange cinematic', 'dark moody blues')"
    )
    title_placement: str = Field(
        ...,
        description="Where title text should appear (e.g., 'top center', 'bottom third')"
    )
    style_applied: str = Field(
        ...,
        description="The art style applied"
    )


class JuryVoteSchema(BaseModel):
    """Structured output for jury voting."""
    first_choice: int = Field(
        ..., ge=0,
        description="Index of first choice (3 points)"
    )
    second_choice: int = Field(
        ..., ge=0,
        description="Index of second choice (2 points)"
    )
    third_choice: int = Field(
        ..., ge=0,
        description="Index of third choice (1 point)"
    )
    reasoning: str = Field(
        ...,
        description="Brief reasoning for the ranking"
    )


# =============================================================================
# Phase 4: Shot Frame Prompt Schemas
# =============================================================================

class ShotFramePromptSchema(BaseModel):
    """Structured output for shot frame image prompts."""
    firstframe_prompt: str = Field(
        ...,
        description="Detailed image prompt for the shot's opening frame (300-500 words)"
    )
    lastframe_prompt: str = Field(
        ...,
        description="Detailed image prompt for the shot's ending frame (300-500 words)"
    )
    shot_size_applied: str = Field(
        ...,
        description="The shot size used for framing (WIDE, MEDIUM, CLOSE-UP, etc.)"
    )
    time_of_day_applied: str = Field(
        ...,
        description="The time of day lighting applied"
    )
    characters_described: list[str] = Field(
        ...,
        description="List of character roles described (NOT names)"
    )


class ShotFrameCritiqueSchema(BaseModel):
    """Critique for shot frame prompts."""
    character_accuracy_score: int = Field(..., ge=1, le=10, description="Are character descriptions accurate to profiles?")
    location_accuracy_score: int = Field(..., ge=1, le=10, description="Does location match codex profile?")
    framing_accuracy_score: int = Field(..., ge=1, le=10, description="Does framing match shot_size?")
    lighting_mood_score: int = Field(..., ge=1, le=10, description="Does lighting match time_of_day and visual_style_notes?")
    action_continuity_score: int = Field(..., ge=1, le=10, description="Does first→last frame show logical action progression?")
    no_names_score: int = Field(..., ge=1, le=10, description="Are character NAMES absent (only descriptions)?")
    overall_score: float = Field(..., description="Average of all scores")
    needs_revision: bool = Field(..., description="True if any score < 7")
    suggestions: list[str] = Field(default=[], description="Specific improvements needed")


# =============================================================================
# Phase 4 Step 5: Video Prompt Schemas (LTX Screenplay Format)
# =============================================================================

class VideoPromptSchema(BaseModel):
    """
    LTX-style video prompt in screenplay format.

    Combines scene description, character actions, dialogue, and camera directions
    into a single flowing screenplay-format prompt for AI video generation.
    """
    video_prompt: str = Field(
        ...,
        description=(
            "Complete LTX screenplay-style prompt (500-800 words). "
            "Includes slugline, scene description, character actions (physical descriptions only), "
            "dialogue with parentheticals, and camera movements."
        )
    )
    slugline: str = Field(
        ...,
        description="INT/EXT. LOCATION – TIME – SHOT TYPE (e.g., 'EXT. VILLAGE SQUARE – DUSK – WIDE SHOT')"
    )
    camera_movements: list[str] = Field(
        ...,
        description="Camera movements described in prompt (e.g., ['dolly in', 'pan right', 'static'])"
    )
    dialogue_included: bool = Field(
        ...,
        description="Whether dialogue is present in this shot"
    )
    characters_described: list[str] = Field(
        ...,
        description="Physical descriptions used for each character (NOT names)"
    )


class VideoPromptCritiqueSchema(BaseModel):
    """Critique for LTX video prompts."""
    screenplay_format_score: int = Field(
        ..., ge=1, le=10,
        description="Is the prompt in proper screenplay format (slugline, action, dialogue)?"
    )
    character_description_score: int = Field(
        ..., ge=1, le=10,
        description="Are characters described by physical appearance, not names?"
    )
    camera_movement_score: int = Field(
        ..., ge=1, le=10,
        description="Are camera movements clear and appropriate for the action?"
    )
    atmosphere_detail_score: int = Field(
        ..., ge=1, le=10,
        description="Is atmosphere (lighting, mood, weather) well described?"
    )
    dialogue_accuracy_score: int = Field(
        ..., ge=1, le=10,
        description="If dialogue present, is it accurate to shot data with proper parentheticals?"
    )
    no_names_score: int = Field(
        ..., ge=1, le=10,
        description="Score 10 if NO character names used, Score 1 if ANY names found"
    )
    overall_score: float = Field(..., description="Average of all scores")
    needs_revision: bool = Field(..., description="True if any score < 7")
    suggestions: list[str] = Field(default=[], description="Specific improvements needed")


# =============================================================================
# Phase 1 Step-Granular Schemas (Research-Driven Outline Generation)
# =============================================================================

class HighLevelStructureSchema(BaseModel):
    """High-level story structure without character names."""
    three_act_summary: str = Field(..., description="Summary of 3-act structure")
    central_conflict: str = Field(..., description="Core conflict of the story")
    protagonist_arc: str = Field(..., description="Protagonist's journey (generic role, no names)")
    antagonist_arc: str = Field(..., description="Antagonist's journey (generic role, no names)")
    theme: str = Field(..., description="Central theme of the story")
    emotional_arc: str = Field(..., description="Emotional journey of the story")


class BeatSheetSchema(BaseModel):
    """Beat sheet with bullet points for each act."""
    act1_beats: list[str] = Field(..., description="Bullet points for Act 1 (Setup)")
    act2_beats: list[str] = Field(..., description="Bullet points for Act 2 (Confrontation)")
    act3_beats: list[str] = Field(..., description="Bullet points for Act 3 (Resolution)")


class ResearchInsightSchema(BaseModel):
    """Research insight from web search."""
    topic: str = Field(..., description="What was researched (e.g., 'Hero's Journey', 'Save the Cat')")
    key_points: list[str] = Field(..., description="Key insights from research")
    application: str = Field(..., description="How to apply this to our story")


class ResearchInsightsListSchema(BaseModel):
    """Wrapper for research insights list output."""
    insights: list[ResearchInsightSchema] = Field(
        ..., description="List of research insights"
    )


class SceneListSchema(BaseModel):
    """Wrapper for scene list output."""
    scenes: list[SceneSchema] = Field(
        ..., description="List of scenes"
    )


# =============================================================================
# Phase 4 Step 4: Scene Image Prompt Schemas
# =============================================================================

class SceneImagePromptSchema(BaseModel):
    """Structured output for scene image prompt generation."""
    prompt: str = Field(
        ...,
        description="Detailed 300-500 word image prompt with physical descriptions (NO character names in prompt text)"
    )
    location_name: str = Field(..., description="Location name from get_location_description tool (e.g., 'Weeps Canyon Gardens')")
    location_id: str = Field(default="", description="Location ID from get_location_description tool (e.g., 'loc_001')")
    characters_in_scene: list[str] = Field(
        ...,
        description="ACTUAL character NAMES from lookup_character_by_role tool, NOT role descriptions. Example: ['Yara Ridgewell', 'Quillon Blackwood'], NOT ['the protagonist', 'the antagonist']"
    )
    character_ids: list[str] = Field(
        default_factory=list,
        description="Character IDs from lookup_character_by_role tool (e.g., ['char_001', 'char_002'])"
    )
    scene_summary: str = Field(..., description="Brief summary of what happens in scene")
    composition_notes: str = Field(..., description="Notes on framing, focus, composition")
    mood_lighting: str = Field(..., description="Lighting and atmosphere description")


class SceneImageCritiqueSchema(BaseModel):
    """Critique for scene image prompts."""
    character_accuracy_score: int = Field(
        ..., ge=1, le=10,
        description="Physical descriptions match codex character profiles"
    )
    location_accuracy_score: int = Field(
        ..., ge=1, le=10,
        description="Setting matches codex location profile"
    )
    no_names_score: int = Field(
        ..., ge=1, le=10,
        description="Score 10 if NO character names used, Score 1 if ANY names found"
    )
    visual_detail_score: int = Field(
        ..., ge=1, le=10,
        description="Sufficient detail for image generation"
    )
    composition_score: int = Field(
        ..., ge=1, le=10,
        description="Good framing and focus"
    )
    overall_score: float = Field(..., description="Average of all scores")
    needs_revision: bool = Field(
        ...,
        description="True if any score < 7 or no_names_score < 10"
    )
    suggestions: list[str] = Field(
        default=[],
        description="Specific improvements needed"
    )
