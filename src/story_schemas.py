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
    """Physical attributes emphasizing visual storytelling."""
    body_build: str = Field(
        ...,
        description="Body type/build that reflects character's life (e.g., 'wiry from years of labor', 'stocky and muscular from training')"
    )
    height: str = Field(..., description="Height description (tall, average, short)")
    hair_color: str = Field(
        ...,
        description="Hair color AND style (e.g., 'silver-streaked black, worn in tight braids')"
    )
    ethnicity: str = Field(
        ...,
        description="Ethnic appearance/complexion (e.g., 'dark-skinned with West African features', 'pale with East Asian features', 'olive Mediterranean complexion')"
    )
    eye_color: str = Field(..., description="Eye color")
    distinguishing_features: str = Field(
        default="",
        description="OPTIONAL: Meaningful unique features only if relevant to story (NOT default scars). Leave empty if none."
    )


class CharacterSchema(BaseModel):
    """Detailed character profile (legacy schema for backwards compatibility)."""
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


class CharacterSheetSchema(BaseModel):
    """Complete character sheet with backstory bullet points (Step 2 output)."""
    id: str = Field(..., description="Unique ID like 'char_001'")
    name: str = Field(..., description="Full name from name debate")
    role_in_story: str = Field(..., description="'protagonist', 'antagonist', or 'supporting'")
    role_description: str = Field(
        ...,
        description="Original role from story seed (e.g., 'an archivist', 'the closest friend')"
    )
    gender: str = Field(..., description="Character's gender")
    age: str = Field(..., description="Age or age range")
    physical: PhysicalDescriptionSchema = Field(..., description="Physical appearance")
    costume: str = Field(
        ...,
        description="DETAILED costume/dress description: clothing, accessories, items carried. This is the most important visual element."
    )
    personality_traits: list[str] = Field(
        ...,
        description="3-5 key personality traits"
    )
    accent: str = Field(
        ...,
        description="Speech pattern/accent (e.g., 'clipped aristocratic', 'warm rural drawl', 'formal scholarly')"
    )
    qualities: list[str] = Field(
        ...,
        description="5-7 specific character qualities/quirks (e.g., 'obsessively organized', 'speaks in metaphors')"
    )
    backstory_points: list[str] = Field(
        ...,
        description="3-6 bullet points of backstory derived from story outline"
    )
    motivation: str = Field(..., description="Core motivation driving the character")
    arc: str = Field(..., description="Character's transformation arc (from hook to resolution)")


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


# =============================================================================
# Step 3A: Location Debate Schemas
# =============================================================================

class LocationProposal(BaseModel):
    """A proposal for location design from a debate agent."""
    agent_name: str = Field(..., description="Name of the proposing agent")
    methodology_focus: str = Field(
        ...,
        description="Agent's focus (e.g., 'architecture', 'atmosphere', 'narrative function', 'audience immersion')"
    )
    name: str = Field(..., description="Proposed location name")
    type: str = Field(..., description="Type of location (palace, market, forest, etc.)")
    description: str = Field(..., description="Visual description (2-3 sentences)")
    atmosphere: str = Field(..., description="Mood/feeling of the place")
    key_features: list[str] = Field(..., description="3-5 notable features")
    sensory_details: str = Field(..., description="Sounds, smells, textures")
    reasoning: str = Field(..., description="Why this design fits the story")


class LocationCritique(BaseModel):
    """Critique of a location proposal."""
    critic_agent: str = Field(..., description="Name of the agent giving the critique")
    target_agent: str = Field(..., description="Name of the agent being critiqued")
    strengths: str = Field(..., description="What works well about this proposal")
    weaknesses: str = Field(..., description="What could be improved")
    suggestion: str = Field(..., description="Specific suggestion for improvement")
    score: int = Field(..., ge=1, le=10, description="Score 1-10")


class LocationVote(BaseModel):
    """An agent's vote for the best location proposal."""
    voter_agent: str = Field(..., description="Name of the voting agent")
    voted_for_agent: str = Field(..., description="Name of the agent whose proposal they voted for")
    vote_reasoning: str = Field(..., description="Why this is the best proposal")


# =============================================================================
# Step 3B: World Building Schemas
# =============================================================================

class DailyLifeSchema(BaseModel):
    """Daily life details for the world."""
    common_foods: list[str] = Field(..., description="5-7 common foods/meals typical to this region")
    eating_customs: str = Field(..., description="How people eat (family meals, street food, shifts, etc.)")
    clothing_styles: str = Field(..., description="Typical clothing by class (poor vs rich)")
    shelter_types: str = Field(..., description="Common housing/architecture styles")


class SocialStructureSchema(BaseModel):
    """Social hierarchy and organization."""
    class_system: str = Field(..., description="Rich vs poor gap, social mobility, class divisions")
    common_jobs: list[str] = Field(..., description="5-7 common occupations for ordinary people")
    desirable_jobs: list[str] = Field(..., description="3-5 prestigious/desirable occupations")
    lowly_jobs: list[str] = Field(..., description="3-5 looked-down-upon occupations")
    guilds_organizations: list[str] = Field(..., description="Important guilds, unions, or organizations")


class GovernmentLawSchema(BaseModel):
    """Government and legal system."""
    government_type: str = Field(..., description="Type of government (monarchy, democracy, theocracy, etc.)")
    law_enforcement: str = Field(..., description="How laws are enforced (police, guards, militias)")
    courts_trials: str = Field(..., description="How justice is administered")
    punishments: list[str] = Field(..., description="Common punishments for crimes")
    military: str = Field(..., description="Military structure and current conflicts")


class EconomySchema(BaseModel):
    """Economic system."""
    currency: str = Field(..., description="What money/currency looks like and is called")
    trade_goods: list[str] = Field(..., description="Major goods that are traded")
    resources: list[str] = Field(..., description="Natural resources available")
    taxation: str = Field(..., description="How taxes work and who collects them")


class EducationHealthSchema(BaseModel):
    """Education and healthcare systems."""
    education_system: str = Field(..., description="Schools, literacy levels, who gets educated")
    medicine: str = Field(..., description="Healthcare availability and quality")
    healers: str = Field(..., description="Who provides healing (doctors, herbalists, magic, etc.)")
    common_ailments: list[str] = Field(..., description="Common diseases/health issues")


class EntertainmentSchema(BaseModel):
    """Entertainment and leisure activities."""
    poor_entertainment: list[str] = Field(..., description="What poor/common people do for fun")
    rich_entertainment: list[str] = Field(..., description="What wealthy people do for fun")
    festivals: list[str] = Field(..., description="Major celebrations/holidays")
    art_forms: list[str] = Field(..., description="Popular art, music, storytelling forms")


class ReligionBeliefsSchema(BaseModel):
    """Religion and supernatural beliefs."""
    main_religion: str = Field(..., description="Dominant faith/belief system")
    gods_deities: list[str] = Field(default=[], description="Major gods/deities if any")
    temples_worship: str = Field(..., description="Where and how people worship")
    superstitions: list[str] = Field(..., description="Common superstitions")
    taboos: list[str] = Field(..., description="Things that are forbidden or shameful")


class CultureCustomsSchema(BaseModel):
    """Cultural norms and customs."""
    social_rules: list[str] = Field(..., description="Important social rules/etiquette")
    gestures_respect: str = Field(..., description="How to show respect")
    gestures_rudeness: str = Field(..., description="What's considered rude")
    family_structure: str = Field(..., description="Family unit type (nuclear, extended, clans)")
    naming_conventions: str = Field(..., description="How names work in this culture")


class WorldBuildingSchema(BaseModel):
    """Complete world building output from all agents."""
    daily_life: DailyLifeSchema = Field(..., description="Food, clothing, shelter")
    social_structure: SocialStructureSchema = Field(..., description="Classes, jobs, organizations")
    government_law: GovernmentLawSchema = Field(..., description="Politics, law, military")
    economy: EconomySchema = Field(..., description="Currency, trade, resources")
    education_health: EducationHealthSchema = Field(..., description="Education, healthcare")
    entertainment: EntertainmentSchema = Field(..., description="Fun, festivals, art")
    religion_beliefs: ReligionBeliefsSchema = Field(..., description="Religion, superstitions")
    culture_customs: CultureCustomsSchema = Field(..., description="Social rules, family")


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
    face_detail_score: float = Field(
        ..., ge=1, le=10,
        description="Score 1-10 for face description completeness"
    )
    clothing_detail_score: float = Field(
        ..., ge=1, le=10,
        description="Score 1-10 for clothing description detail"
    )
    distinguishing_marks_score: float = Field(
        ..., ge=1, le=10,
        description="Score 1-10 for scars, tattoos, jewelry description"
    )
    pose_expression_score: float = Field(
        ..., ge=1, le=10,
        description="Score 1-10 for pose and expression clarity"
    )
    quality_tags_score: float = Field(
        ..., ge=1, le=10,
        description="Score 1-10 for lighting, resolution, style tags"
    )
    overall_score: float = Field(
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
    architecture_structure_score: float = Field(
        ..., ge=1, le=10,
        description="Score 1-10 for architecture and structure detail"
    )
    lighting_time_score: float = Field(
        ..., ge=1, le=10,
        description="Score 1-10 for lighting and time of day"
    )
    atmosphere_weather_score: float = Field(
        ..., ge=1, le=10,
        description="Score 1-10 for atmosphere and weather effects"
    )
    textures_materials_score: float = Field(
        ..., ge=1, le=10,
        description="Score 1-10 for textures and materials"
    )
    composition_depth_score: float = Field(
        ..., ge=1, le=10,
        description="Score 1-10 for composition and depth layers"
    )
    quality_tags_score: float = Field(
        ..., ge=1, le=10,
        description="Score 1-10 for quality and style tags"
    )
    overall_score: float = Field(
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
    location_clarity_score: float = Field(..., ge=1, le=10, description="INT./EXT. and location specificity")
    shot_composition_score: float = Field(..., ge=1, le=10, description="Shot size and depth layers")
    camera_work_score: float = Field(..., ge=1, le=10, description="Camera movement motivation")
    lighting_time_score: float = Field(..., ge=1, le=10, description="Lighting and time consistency")
    character_blocking_score: float = Field(..., ge=1, le=10, description="Character positions clarity")
    visual_storytelling_score: float = Field(..., ge=1, le=10, description="Visual focus and emphasis")
    overall_score: float = Field(..., ge=1, le=10, description="Overall visual quality")
    needs_revision: bool = Field(..., description="True if any score < 7")
    suggestions: list[str] = Field(..., description="Specific visual improvements")


class DialogueCritiqueSchema(BaseModel):
    """Dialogue critic's evaluation of storyboard."""
    dialogue_length_score: float = Field(..., ge=1, le=10, description="Dialogue fits duration (25-35 words)")
    delivery_notes_score: float = Field(..., ge=1, le=10, description="Parentheticals for tone")
    natural_flow_score: float = Field(..., ge=1, le=10, description="Natural spoken dialogue")
    character_voice_score: float = Field(..., ge=1, le=10, description="Consistent character voice")
    audio_design_score: float = Field(..., ge=1, le=10, description="SFX, music, ambient quality")
    overall_score: float = Field(..., ge=1, le=10, description="Overall dialogue quality")
    needs_revision: bool = Field(..., description="True if any score < 7")
    word_count_violations: list[int] = Field(
        default=[],
        description="Shot numbers exceeding word limits"
    )
    suggestions: list[str] = Field(..., description="Specific dialogue improvements")


class ContinuityCritiqueSchema(BaseModel):
    """Continuity critic's evaluation of storyboard."""
    shot_flow_score: float = Field(..., ge=1, le=10, description="Logical shot connections, 180° rule")
    character_continuity_score: float = Field(..., ge=1, le=10, description="Character position consistency")
    location_continuity_score: float = Field(..., ge=1, le=10, description="Environment consistency")
    story_context_score: float = Field(..., ge=1, le=10, description="Scene purpose and plot points")
    pacing_rhythm_score: float = Field(..., ge=1, le=10, description="Shot variety and timing")
    overall_coherence_score: float = Field(..., ge=1, le=10, description="Works as video sequence")
    overall_score: float = Field(..., ge=1, le=10, description="Overall continuity quality")
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
    character_accuracy_score: float = Field(..., ge=1, le=10, description="Are character descriptions accurate to profiles?")
    location_accuracy_score: float = Field(..., ge=1, le=10, description="Does location match codex profile?")
    framing_accuracy_score: float = Field(..., ge=1, le=10, description="Does framing match shot_size?")
    lighting_mood_score: float = Field(..., ge=1, le=10, description="Does lighting match time_of_day and visual_style_notes?")
    action_continuity_score: float = Field(..., ge=1, le=10, description="Does first→last frame show logical action progression?")
    no_names_score: float = Field(..., ge=1, le=10, description="Are character NAMES absent (only descriptions)?")
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
    screenplay_format_score: float = Field(
        ..., ge=1, le=10,
        description="Is the prompt in proper screenplay format (slugline, action, dialogue)?"
    )
    character_description_score: float = Field(
        ..., ge=1, le=10,
        description="Are characters described by physical appearance, not names?"
    )
    camera_movement_score: float = Field(
        ..., ge=1, le=10,
        description="Are camera movements clear and appropriate for the action?"
    )
    atmosphere_detail_score: float = Field(
        ..., ge=1, le=10,
        description="Is atmosphere (lighting, mood, weather) well described?"
    )
    dialogue_accuracy_score: float = Field(
        ..., ge=1, le=10,
        description="If dialogue present, is it accurate to shot data with proper parentheticals?"
    )
    no_names_score: float = Field(
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
# Phase 1 Step 1: Story Seed Parsing & 7-Point Structure Schemas
# =============================================================================

class StorySeedParsed(BaseModel):
    """Parsed story seed with extracted components."""
    adjective: str = Field(
        ...,
        description="The opening adjective/emotional state (e.g., 'SHATTERED', 'DESPERATE', 'BROKEN')"
    )
    adjective_meaning: str = Field(
        ...,
        description="WHY the hero is in this state - the backstory/trauma that caused it"
    )
    hero_role: str = Field(
        ...,
        description="The hero's role/occupation (e.g., 'an archivist', 'a young warrior')"
    )
    goal: str = Field(
        ...,
        description="What the hero wants to accomplish"
    )
    stakes: str = Field(
        ...,
        description="What's at risk / consequences of failure"
    )
    setting_context: str = Field(
        default="",
        description="Any setting/world context from the seed"
    )


class StructureBeatSchema(BaseModel):
    """A single story beat in the 7-point structure."""
    beat_name: str = Field(
        ...,
        description="Beat identifier: 'hook', 'plot_turn_1', 'pinch_point_1', 'midpoint', 'pinch_point_2', 'plot_turn_2', 'resolution'"
    )
    description: str = Field(
        ...,
        description="CONCISE beat description: 1-2 sentences MAX (under 40 words). Focus on what HAPPENS or CHANGES, not atmosphere. Example: 'The archivist, isolated and paranoid after betrayal, refuses help from allies.' Use generic roles only, NO character names."
    )
    emotional_state: str = Field(
        ...,
        description="Hero's emotional/psychological state during this beat"
    )
    purpose: str = Field(
        ...,
        description="One sentence explaining why this beat matters (max 20 words)"
    )


class SevenPointStructureSchema(BaseModel):
    """Complete 7-point story structure (Dan Wells method)."""
    hook: StructureBeatSchema = Field(
        ...,
        description="HOOK: Hero's BEFORE state - opposite of resolution. Why are they [ADJECTIVE]?"
    )
    plot_turn_1: StructureBeatSchema = Field(
        ...,
        description="PLOT TURN 1: The inciting incident that forces hero into the story"
    )
    pinch_point_1: StructureBeatSchema = Field(
        ...,
        description="PINCH POINT 1: First major pressure - stakes become real"
    )
    midpoint: StructureBeatSchema = Field(
        ...,
        description="MIDPOINT: The pivot - hero shifts from REACTION to ACTION"
    )
    pinch_point_2: StructureBeatSchema = Field(
        ...,
        description="PINCH POINT 2: Darkest moment - all seems lost"
    )
    plot_turn_2: StructureBeatSchema = Field(
        ...,
        description="PLOT TURN 2: The final piece that enables victory"
    )
    resolution: StructureBeatSchema = Field(
        ...,
        description="RESOLUTION: Hero's AFTER state - opposite of hook. Transformation complete."
    )


class StructureDebateProposal(BaseModel):
    """A proposed beat from a structure debate agent."""
    beat_name: str = Field(..., description="Which beat is being proposed")
    proposal: StructureBeatSchema = Field(..., description="The proposed beat content")
    reasoning: str = Field(
        ...,
        description="Why this beat works for the story (connection to adjective, theme, other beats)"
    )


class StructureDebateCritique(BaseModel):
    """Critique of a proposed beat or structure."""
    is_valid: bool = Field(..., description="Does the beat/structure work?")
    strengths: list[str] = Field(..., description="What works well")
    weaknesses: list[str] = Field(..., description="What needs improvement")
    hook_resolution_opposite: bool = Field(
        ...,
        description="Are Hook and Resolution truly OPPOSITES?"
    )
    tension_escalates: bool = Field(
        ...,
        description="Does tension properly escalate through pinch points?"
    )
    midpoint_pivot_clear: bool = Field(
        ...,
        description="Is the Midpoint a clear shift from REACTION to ACTION?"
    )
    suggestions: list[str] = Field(..., description="Specific improvements")


class StructureDebateResult(BaseModel):
    """Complete result of the structure debate process."""
    story_seed_parsed: StorySeedParsed = Field(..., description="Parsed story seed components")
    structure_beats: SevenPointStructureSchema = Field(..., description="Final 7-point structure")
    theme: str = Field(..., description="Central theme extracted from structure")
    title_suggestion: str = Field(..., description="Suggested story title")
    debate_rounds: int = Field(..., description="Number of debate rounds conducted")


# =============================================================================
# Research-Driven Multi-Agent Debate Schemas
# =============================================================================

class AgentMethodology(BaseModel):
    """An agent's storytelling methodology/perspective."""
    agent_name: str = Field(
        ...,
        description="Agent's name (e.g., 'DanWellsAgent', 'BlakeSnyderAgent')"
    )
    source: str = Field(
        ...,
        description="The methodology source (e.g., 'Dan Wells 7-Point Structure', 'Save the Cat Beat Sheet')"
    )
    core_beliefs: list[str] = Field(
        ...,
        description="Key principles this agent advocates for"
    )


class AgentCritique(BaseModel):
    """A critique from one agent about another's proposal."""
    critic_agent: str = Field(
        ...,
        description="Name of the agent giving the critique"
    )
    target_agent: str = Field(
        ...,
        description="Name of the agent whose proposal is being critiqued"
    )
    target_beat: str = Field(
        ...,
        description="Which beat is being critiqued (e.g., 'resolution', 'hook', 'midpoint')"
    )
    criticism: str = Field(
        ...,
        description="What's wrong or could be stronger with this proposal"
    )
    suggestion: str = Field(
        ...,
        description="Specific suggestion for improvement"
    )
    methodology_basis: str = Field(
        ...,
        description="Which principle from the critic's methodology supports this critique"
    )
    severity: str = Field(
        ...,
        description="Severity of the issue: 'minor', 'moderate', 'major'"
    )


class AgentProposal(BaseModel):
    """A beat proposal from an agent with methodology backing."""
    agent_name: str = Field(..., description="Name of the proposing agent")
    methodology_source: str = Field(..., description="The methodology backing this proposal")
    beat: StructureBeatSchema = Field(..., description="The proposed beat content")
    methodology_reasoning: str = Field(
        ...,
        description="How this proposal follows the agent's methodology principles"
    )


class AgentVote(BaseModel):
    """An agent's vote for the best proposal in a round."""
    voter_agent: str = Field(..., description="Name of the voting agent")
    voted_for_agent: str = Field(..., description="Name of the agent whose proposal they voted for")
    vote_reasoning: str = Field(
        ...,
        description="Why this proposal is best according to the voter's methodology"
    )


class DebateRound(BaseModel):
    """A complete debate round with proposals, critiques, votes, and final beat."""
    round_name: str = Field(
        ...,
        description="Name of the round (e.g., 'resolution_design', 'hook_design', 'midpoint_design')"
    )
    target_beat: str = Field(
        ...,
        description="Which beat this round is designing"
    )
    proposals: list[AgentProposal] = Field(
        ...,
        description="Each agent's proposal for this beat"
    )
    critiques: list[AgentCritique] = Field(
        ...,
        description="Cross-agent critiques of proposals"
    )
    votes: list[AgentVote] = Field(
        ...,
        description="Each agent's vote for the best proposal"
    )
    winning_agent: str = Field(
        ...,
        description="Agent whose proposal won (or 'merged' if combined)"
    )
    final_beat: StructureBeatSchema = Field(
        ...,
        description="The refined final beat after debate and voting"
    )
    revision_notes: str = Field(
        default="",
        description="Notes on how the final beat was refined based on critiques"
    )


class DebateTranscript(BaseModel):
    """Complete transcript of the multi-agent structure debate."""
    agents_participating: list[AgentMethodology] = Field(
        ...,
        description="All agents participating in the debate with their methodologies"
    )
    story_seed_analysis: dict = Field(
        ...,
        description="How each agent interpreted the story seed"
    )
    rounds: list[DebateRound] = Field(
        ...,
        description="All debate rounds (resolution, hook, midpoint, etc.)"
    )
    validation_round: dict = Field(
        ...,
        description="Final validation round results"
    )
    total_critiques: int = Field(..., description="Total number of critiques exchanged")
    consensus_reached: bool = Field(..., description="Whether all agents agreed on final structure")


# =============================================================================
# Phase 1 Step 2: Character Debate Schemas
# =============================================================================

class CharacterPhysicalProposal(BaseModel):
    """A proposal for character physical appearance from a debate agent."""
    agent_name: str = Field(..., description="Name of the proposing agent")
    methodology_focus: str = Field(
        ...,
        description="Agent's focus (e.g., 'psychology', 'visual design', 'narrative role')"
    )
    physical: PhysicalDescriptionSchema = Field(..., description="Proposed physical appearance")
    costume: str = Field(
        ...,
        description="Proposed costume/clothing description"
    )
    reasoning: str = Field(
        ...,
        description="Why this appearance fits the character's role and story"
    )


class CharacterPhysicalCritique(BaseModel):
    """Critique of a character physical proposal."""
    critic_agent: str = Field(..., description="Name of the agent giving the critique")
    target_agent: str = Field(..., description="Name of the agent being critiqued")
    strengths: str = Field(..., description="What works well about this proposal")
    weaknesses: str = Field(..., description="What could be improved")
    suggestion: str = Field(..., description="Specific suggestion for improvement")
    score: int = Field(..., ge=1, le=10, description="Score 1-10")


class CharacterPhysicalVote(BaseModel):
    """An agent's vote for the best physical appearance proposal."""
    voter_agent: str = Field(..., description="Name of the voting agent")
    voted_for_agent: str = Field(..., description="Name of the agent whose proposal they voted for")
    vote_reasoning: str = Field(..., description="Why this is the best proposal")


class CharacterBackstoryProposal(BaseModel):
    """A proposal for character backstory bullet points."""
    agent_name: str = Field(..., description="Name of the proposing agent")
    backstory_points: list[str] = Field(
        ...,
        description="3-6 bullet points of backstory"
    )
    motivation: str = Field(..., description="Character's core motivation")
    arc: str = Field(..., description="Character's transformation arc")
    personality_traits: list[str] = Field(
        ...,
        description="3-5 key personality traits unique to this character"
    )
    accent: str = Field(
        ...,
        description="Speech pattern/accent (e.g., 'clipped aristocratic', 'warm rural drawl', 'formal scholarly')"
    )
    qualities: list[str] = Field(
        ...,
        description="5-7 specific character qualities/quirks (e.g., 'obsessively organized', 'speaks in metaphors', 'never makes eye contact')"
    )
    gender: str = Field(
        ...,
        description="Character's gender: 'male' or 'female'"
    )
    reasoning: str = Field(..., description="Why this backstory fits the story outline")


class CharacterDebateResult(BaseModel):
    """Complete result of character debate for one character."""
    character_role: str = Field(..., description="Original role (e.g., 'an archivist')")
    character_type: str = Field(..., description="'protagonist', 'antagonist', 'supporting'")
    name_debate: dict = Field(..., description="Name debate results")
    physical_proposals: list[CharacterPhysicalProposal] = Field(
        ...,
        description="All physical appearance proposals"
    )
    physical_critiques: list[CharacterPhysicalCritique] = Field(
        ...,
        description="All critiques of physical proposals"
    )
    physical_votes: list[CharacterPhysicalVote] = Field(
        ...,
        description="All votes for physical proposals"
    )
    winning_physical: str = Field(..., description="Agent whose physical proposal won")
    final_character: CharacterSheetSchema = Field(
        ...,
        description="Final assembled character sheet"
    )


# =============================================================================
# Phase 1 Step 7: Book & Chapter Title Naming Schemas
# =============================================================================

class BookTitleProposal(BaseModel):
    """A proposed book title from a naming agent."""
    agent_name: str = Field(..., description="Name of proposing agent")
    title: str = Field(..., description="Proposed book title")
    subtitle: str = Field(default="", description="Optional subtitle")
    reasoning: str = Field(..., description="Why this title works for the story")
    literary_devices_used: list[str] = Field(
        default=[],
        description="Literary devices used: metaphor, alliteration, symbolism, etc."
    )

    class Config:
        extra = "ignore"


class ChapterTitleProposal(BaseModel):
    """A proposed chapter title."""
    agent_name: str = Field(..., description="Name of proposing agent")
    chapter_number: int = Field(..., description="Chapter number")
    title: str = Field(..., description="Proposed chapter title")
    reasoning: str = Field(..., description="Why this title fits the chapter")

    class Config:
        extra = "ignore"


class TitleCritique(BaseModel):
    """Critique of a title proposal."""
    critic_agent: str = Field(..., description="Name of critic")
    target_agent: str = Field(..., description="Agent being critiqued")
    strengths: str = Field(..., description="What works well about this title")
    weaknesses: str = Field(..., description="What could be improved")
    score: int = Field(..., ge=1, le=10, description="Score 1-10")

    class Config:
        extra = "ignore"


class TitleVote(BaseModel):
    """An agent's vote for the best title."""
    voter_agent: str = Field(..., description="Voting agent")
    voted_for_agent: str = Field(..., description="Agent voted for")
    vote_reasoning: str = Field(..., description="Why this is the best choice")

    class Config:
        extra = "ignore"


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
    character_accuracy_score: float = Field(
        ..., ge=1, le=10,
        description="Physical descriptions match codex character profiles"
    )
    location_accuracy_score: float = Field(
        ..., ge=1, le=10,
        description="Setting matches codex location profile"
    )
    no_names_score: float = Field(
        ..., ge=1, le=10,
        description="Score 10 if NO character names used, Score 1 if ANY names found"
    )
    visual_detail_score: float = Field(
        ..., ge=1, le=10,
        description="Sufficient detail for image generation"
    )
    composition_score: float = Field(
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


# =============================================================================
# Phase 1 Step 4: Scene/Chapter Outline Schemas (GMC + Swain Structure)
# =============================================================================

class DetailedSceneSchema(BaseModel):
    """Extended scene schema following GMC + Swain scene/sequel structure."""

    # Basic identification
    scene_number: int = Field(..., description="Scene number within chapter")
    scene_type: str = Field(
        ...,
        description="'scene' (proactive: goal→conflict→disaster) or 'sequel' (reactive: reaction→dilemma→decision)"
    )

    # Setting
    time_of_day: str = Field(
        ...,
        description="Time: 'dawn', 'morning', 'midday', 'afternoon', 'dusk', 'night'"
    )
    location: str = Field(..., description="Location name from codex")
    location_id: str = Field(default="", description="Location ID (e.g., 'loc_001')")

    # Characters
    pov_character: str = Field(..., description="Point of view character for this scene")
    characters: list[str] = Field(..., description="All character names present")
    character_ids: list[str] = Field(default=[], description="Character IDs")

    # GMC Structure (Goal, Motivation, Conflict)
    goal: str = Field(
        ...,
        description="What the POV character wants to achieve IN THIS SCENE"
    )
    conflict: str = Field(
        ...,
        description="What obstacle/opposition prevents the goal"
    )
    outcome: str = Field(
        ...,
        description="'YES_BUT', 'NO_AND', 'YES', 'NO', or 'CLIFFHANGER'"
    )

    # What happens
    happens: str = Field(
        ...,
        description="2-3 sentences: what happens in this scene"
    )

    # Story structure connection
    structure_connection: str = Field(
        ...,
        description="Which 7-point beat this scene serves (e.g., 'hook', 'pinch_point_1')"
    )
    scene_purpose: str = Field(
        ...,
        description="Why this scene exists: what it accomplishes for plot/character"
    )


class ChapterSchema(BaseModel):
    """A chapter containing 5-6 scenes."""
    chapter_number: int = Field(..., description="Chapter number")
    chapter_title: str = Field(..., description="Chapter title")
    act: int = Field(..., description="Which act (1, 2, or 3)")
    structure_beats_covered: list[str] = Field(
        ...,
        description="Which 7-point beats this chapter covers"
    )
    scenes: list[DetailedSceneSchema] = Field(
        ...,
        description="5-6 scenes in this chapter"
    )


class SceneProposal(BaseModel):
    """A proposal for a scene from a debate agent."""
    agent_name: str = Field(..., description="Name of proposing agent")
    methodology_focus: str = Field(
        ...,
        description="Agent's focus: 'plot', 'character', 'pacing', 'structure'"
    )
    scene: DetailedSceneSchema = Field(..., description="The proposed scene")
    reasoning: str = Field(..., description="Why this scene works")


class SceneCritique(BaseModel):
    """Critique of a scene proposal."""
    critic_agent: str = Field(..., description="Name of the critic")
    target_agent: str = Field(..., description="Agent being critiqued")
    strengths: str = Field(..., description="What works well")
    weaknesses: str = Field(..., description="What could improve")
    suggestion: str = Field(..., description="Specific improvement")
    score: int = Field(..., ge=1, le=10, description="Score 1-10")


class SceneVote(BaseModel):
    """An agent's vote for best scene."""
    voter_agent: str = Field(..., description="Voting agent")
    voted_for_agent: str = Field(..., description="Agent voted for")
    vote_reasoning: str = Field(..., description="Why this is best")


class ChapterOutlineSchema(BaseModel):
    """Complete chapter outline for the story."""
    total_chapters: int = Field(..., description="Total number of chapters")
    total_scenes: int = Field(..., description="Total number of scenes")
    chapters: list[ChapterSchema] = Field(..., description="All chapters")

    # STORY-LEVEL TICKING CLOCK - creates urgency for entire story
    ticking_clock: str = Field(
        ...,
        description="The overarching deadline that creates urgency for the ENTIRE story (e.g., 'The execution is at dawn', 'The invasion begins in 3 days')"
    )
    ticking_clock_deadline: str = Field(
        ...,
        description="When the clock runs out (e.g., 'dawn of the third day', 'midnight tomorrow', 'when the moon is full')"
    )
    ticking_clock_consequence: str = Field(
        ...,
        description="What happens if the deadline is missed (e.g., 'the innocent dies', 'the city falls', 'the curse becomes permanent')"
    )


# =============================================================================
# Phase 1 Step 5: Narrative Writing Schemas (5-Agent Multi-Agent Debate)
# =============================================================================

class NarrativeProseProposal(BaseModel):
    """A prose proposal from a narrative writing agent."""
    agent_name: str = Field(..., description="Name of the proposing agent")
    methodology_focus: str = Field(
        ...,
        description="Agent's focus: 'character', 'location', 'world', 'plot', 'narrative'"
    )

    # Structured prose output
    opening_paragraph: str = Field(
        ...,
        description=(
            "Opening paragraph establishing setting and character entry. "
            "Heavy sensory detail, immediate scene grounding. 100-150 words."
        )
    )
    middle_paragraphs: list[str] = Field(
        ...,
        description=(
            "3-5 paragraphs developing the scene with dialogue, action, "
            "and character interaction. Each 100-150 words."
        ),
        min_length=1,
    )
    closing_paragraph: str = Field(
        ...,
        description=(
            "Closing paragraph with scene resolution or hook. "
            "Emotional resonance or cliffhanger. 100-150 words."
        )
    )

    # Methodology tracking
    techniques_used: list[str] = Field(
        ...,
        description=(
            "List of writing techniques used based on agent's methodology "
            "(e.g., 'smell trigger for backstory', 'ticking clock reference', "
            "'cultural gesture integration')"
        )
    )
    reasoning: str = Field(
        ...,
        description="Why this prose serves the scene and story best"
    )

    def to_prose(self) -> str:
        """Assemble paragraphs into continuous prose."""
        paragraphs = [self.opening_paragraph]
        paragraphs.extend(self.middle_paragraphs)
        paragraphs.append(self.closing_paragraph)
        return "\n\n".join(paragraphs)

    def word_count(self) -> int:
        """Calculate total word count."""
        return len(self.to_prose().split())


class NarrativeProseCritique(BaseModel):
    """Critique of a prose proposal from a narrative writing agent."""
    critic_agent: str = Field(..., description="Name of the agent giving the critique")
    target_agent: str = Field(..., description="Name of the agent being critiqued")

    # Dimension scores (1-10)
    character_accuracy_score: float = Field(
        ..., ge=1, le=10,
        description="Do characters match their codex profiles? Personality, speech, quirks?"
    )
    sensory_immersion_score: float = Field(
        ..., ge=1, le=10,
        description="Are all senses engaged? Does location feel real?"
    )
    world_integration_score: float = Field(
        ..., ge=1, le=10,
        description="Are world details woven naturally? Food, customs, culture?"
    )
    plot_urgency_score: float = Field(
        ..., ge=1, le=10,
        description="Does scene advance plot? Is ticking clock felt?"
    )
    prose_quality_score: float = Field(
        ..., ge=1, le=10,
        description="Is prose varied, engaging? Show don't tell? No cliches?"
    )

    # Overall assessment
    strengths: str = Field(..., description="What works well in this proposal")
    weaknesses: str = Field(..., description="What needs improvement")
    specific_suggestions: list[str] = Field(
        ...,
        description="Concrete suggestions for improvement with examples"
    )
    overall_score: float = Field(..., description="Average of all dimension scores")


class NarrativeProseVote(BaseModel):
    """An agent's vote for the best prose proposal."""
    voter_agent: str = Field(..., description="Name of the voting agent")
    voted_for_agent: str = Field(
        ...,
        description="Name of the agent whose proposal they voted for"
    )
    vote_reasoning: str = Field(
        ...,
        description="Why this proposal is the best choice for this scene"
    )
    methodology_alignment: str = Field(
        ...,
        description="How the winning proposal aligns with voter's methodology"
    )


class SceneNarrativeSchema(BaseModel):
    """Final narrative prose for a scene after multi-agent debate."""
    scene_id: str = Field(..., description="Scene identifier: 'ch{N}_scene{M}'")
    chapter_number: int = Field(..., description="Chapter number")
    scene_number: int = Field(..., description="Scene number within chapter")

    # Scene metadata from chapter_outline
    location: str = Field(..., description="Location name")
    location_id: str = Field(default="", description="Location ID")
    pov_character: str = Field(..., description="POV character name")
    characters_present: list[str] = Field(..., description="All characters in scene")
    character_ids: list[str] = Field(default=[], description="Character IDs (e.g., 'char_001')")
    time_of_day: str = Field(..., description="Time of day")

    # The prose
    prose: str = Field(
        ...,
        description="Full narrative prose (750-1000 words, multiple paragraphs)"
    )
    word_count: int = Field(..., description="Word count of prose")

    # Debate tracking
    winning_agent: str = Field(..., description="Agent whose proposal won")
    techniques_integrated: list[str] = Field(
        ...,
        description="Writing techniques used from all agents"
    )


# =============================================================================
# Phase 1 Step 6: Critique Schemas (5-Persona Revision System)
# =============================================================================

# Helper models for nested structures (required for OpenAI structured output)
class TextContextItem(BaseModel):
    """A text with its surrounding context."""
    text: str = Field(default="", description="The problematic text")
    context: str = Field(default="", description="Surrounding context")

    class Config:
        extra = "ignore"


class TextSuggestionItem(BaseModel):
    """A text with a suggestion for improvement."""
    text: str = Field(default="", description="The problematic text")
    suggestion: str = Field(default="", description="Suggested improvement")

    class Config:
        extra = "ignore"


class RewriteItem(BaseModel):
    """An original text with its suggested rewrite."""
    original: str = Field(default="", description="Original text")
    suggestion: str = Field(default="", description="Suggested rewrite")

    class Config:
        extra = "ignore"


class VoiceIssueItem(BaseModel):
    """A character voice issue."""
    character: str = Field(default="", description="Character name")
    issue: str = Field(default="", description="Description of the voice issue")

    class Config:
        extra = "ignore"


class DialogueFixItem(BaseModel):
    """A dialogue fix with character, original, suggested, and reason."""
    character: str = Field(default="", description="Character name")
    original: str = Field(default="", description="Original dialogue")
    suggested: str = Field(default="", description="Suggested dialogue")
    reason: str = Field(default="", description="Reason for the fix")

    class Config:
        extra = "ignore"


class CharacterIssueItem(BaseModel):
    """A character inconsistency with codex."""
    character: str = Field(default="", description="Character name")
    issue: str = Field(default="", description="Description of the inconsistency")
    prose_says: str = Field(default="", description="What the prose says")
    codex_says: str = Field(default="", description="What the codex says")

    class Config:
        extra = "ignore"


class LocationIssueItem(BaseModel):
    """A location inconsistency with codex."""
    location: str = Field(default="", description="Location name")
    issue: str = Field(default="", description="Description of the inconsistency")
    prose_says: str = Field(default="", description="What the prose says")
    codex_says: str = Field(default="", description="What the codex says")

    class Config:
        extra = "ignore"


class IssueItem(BaseModel):
    """A generic issue with context."""
    issue: str = Field(default="", description="Description of the issue")
    context: str = Field(default="", description="Context or example")

    class Config:
        extra = "ignore"


class ParagraphIssueItem(BaseModel):
    """An issue at a specific paragraph."""
    paragraph: int = Field(default=0, description="Paragraph number")
    issue: str = Field(default="", description="Description of the issue")

    class Config:
        extra = "ignore"


class SubtextItem(BaseModel):
    """A dialogue with its subtext."""
    dialogue: str = Field(default="", description="The dialogue")
    subtext: str = Field(default="", description="The underlying meaning")

    class Config:
        extra = "ignore"


class ProsePolishCritique(BaseModel):
    """Critique from Prose Polish Critic - catches style issues."""
    scene_id: str = Field(..., description="Scene identifier")

    # Issues found
    filter_words_found: list[TextContextItem] = Field(
        default=[],
        description="Filter words found with context"
    )
    cliches_found: list[TextContextItem] = Field(
        default=[],
        description="Cliches found with context"
    )
    passive_voice_instances: list[TextContextItem] = Field(
        default=[],
        description="Passive voice instances in action scenes"
    )
    tell_not_show: list[TextSuggestionItem] = Field(
        default=[],
        description="Tell-not-show violations with suggestions"
    )
    weak_words: list[str] = Field(
        default=[],
        description="Weak words found: suddenly, very, just, really"
    )
    redundancies: list[str] = Field(
        default=[],
        description="Redundant phrases: nodded his head, shrugged shoulders"
    )

    # Scores
    sentence_variety_score: float = Field(
        ..., ge=1, le=10,
        description="Score for sentence length variety (1-10)"
    )
    overall_score: float = Field(
        ..., ge=1, le=10,
        description="Overall prose polish score (1-10)"
    )

    # Rewrites
    specific_rewrites: list[RewriteItem] = Field(
        default=[],
        description="Suggested rewrites"
    )

    class Config:
        extra = "ignore"

    @property
    def needs_revision(self) -> bool:
        return self.overall_score < 7 or len(self.filter_words_found) > 3


class CharacterVoiceCritique(BaseModel):
    """Critique from Character Voice Critic - checks dialogue authenticity."""
    scene_id: str = Field(..., description="Scene identifier")
    characters_evaluated: list[str] = Field(
        ..., description="Characters whose dialogue was evaluated"
    )

    # Voice issues per character
    voice_issues: list[VoiceIssueItem] = Field(
        default=[],
        description="Voice issues found for characters"
    )

    # Dialogue fixes
    dialogue_fixes: list[DialogueFixItem] = Field(
        default=[],
        description="Dialogue fixes with character, original, suggested, reason"
    )

    # Tests
    no_tag_test_passed: bool = Field(
        ...,
        description="Can tell who's speaking without dialogue tags?"
    )

    # Scores by factor
    education_match_score: float = Field(
        ..., ge=1, le=10,
        description="Does vocabulary match character education level? (1-10)"
    )
    profession_match_score: float = Field(
        ..., ge=1, le=10,
        description="Does dialogue reflect character's profession/expertise? (1-10)"
    )
    personality_match_score: float = Field(
        ..., ge=1, le=10,
        description="Does speech pattern match personality (confident/timid/etc)? (1-10)"
    )
    background_match_score: float = Field(
        ..., ge=1, le=10,
        description="Does dialogue reflect character's history/trauma/passions? (1-10)"
    )
    overall_voice_score: float = Field(
        ..., ge=1, le=10,
        description="Overall character voice authenticity score (1-10)"
    )

    class Config:
        extra = "ignore"

    @property
    def needs_revision(self) -> bool:
        return (
            self.overall_voice_score < 7 or
            not self.no_tag_test_passed or
            len(self.dialogue_fixes) > 2
        )


class WorldRuleViolationItem(BaseModel):
    """A world rule violation."""
    rule: str = Field(default="", description="The world rule that was violated")
    violation: str = Field(default="", description="How it was violated")

    class Config:
        extra = "ignore"


class NameSpellingItem(BaseModel):
    """A name spelling inconsistency."""
    name: str = Field(default="", description="The character name")
    variations: list[str] = Field(default=[], description="Spelling variations found")

    class Config:
        extra = "ignore"


class ContinuityCritique(BaseModel):
    """Critique from Continuity Critic - checks consistency with codex."""
    scene_id: str = Field(..., description="Scene identifier")

    # Inconsistencies found
    character_inconsistencies: list[CharacterIssueItem] = Field(
        default=[],
        description="Character inconsistencies with codex"
    )
    location_inconsistencies: list[LocationIssueItem] = Field(
        default=[],
        description="Location inconsistencies with codex"
    )
    timeline_issues: list[IssueItem] = Field(
        default=[],
        description="Timeline problems"
    )
    world_rule_violations: list[WorldRuleViolationItem] = Field(
        default=[],
        description="World rule violations"
    )
    pov_breaks: list[IssueItem] = Field(
        default=[],
        description="POV consistency breaks"
    )
    knowledge_violations: list[VoiceIssueItem] = Field(
        default=[],
        description="Character knows things they shouldn't"
    )
    name_spelling_issues: list[NameSpellingItem] = Field(
        default=[],
        description="Name spelling inconsistencies"
    )

    # Overall
    overall_continuity_score: float = Field(
        ..., ge=1, le=10,
        description="Overall continuity score (1-10)"
    )

    class Config:
        extra = "ignore"

    @property
    def needs_revision(self) -> bool:
        return (
            self.overall_continuity_score < 8 or
            len(self.character_inconsistencies) > 0 or
            len(self.pov_breaks) > 0
        )


class PacingTensionCritique(BaseModel):
    """Critique from Pacing & Tension Critic - checks scene structure."""
    scene_id: str = Field(..., description="Scene identifier")

    # Scene structure
    scene_length_assessment: str = Field(
        ...,
        description="'appropriate', 'too_long', or 'too_short'"
    )
    enters_late_enough: bool = Field(
        ...,
        description="Does scene enter late enough (no throat-clearing)?"
    )
    exits_at_hook: bool = Field(
        ...,
        description="Does scene exit at a hook (not after resolution)?"
    )

    # Ticking clock
    ticking_clock_present: bool = Field(
        ...,
        description="Is the ticking clock felt in this scene?"
    )
    ticking_clock_references: list[str] = Field(
        default=[],
        description="Specific ticking clock references found"
    )

    # Problem areas
    slow_spots: list[ParagraphIssueItem] = Field(
        default=[],
        description="Slow spots in the scene"
    )
    rushed_spots: list[ParagraphIssueItem] = Field(
        default=[],
        description="Rushed spots in the scene"
    )

    # GMC
    gmc_clear: bool = Field(
        ...,
        description="Is Goal-Motivation-Conflict clear in scene?"
    )

    # Scores
    tension_arc_score: float = Field(
        ..., ge=1, le=10,
        description="Tension rises and falls appropriately (1-10)"
    )
    overall_pacing_score: float = Field(
        ..., ge=1, le=10,
        description="Overall pacing score (1-10)"
    )

    class Config:
        extra = "ignore"

    @property
    def needs_revision(self) -> bool:
        return (
            self.overall_pacing_score < 7 or
            not self.ticking_clock_present or
            len(self.slow_spots) > 1
        )


class EmotionalResonanceCritique(BaseModel):
    """Critique from Emotional Resonance Critic - checks reader engagement."""
    scene_id: str = Field(..., description="Scene identifier")

    # Emotional elements
    emotional_beats_present: list[str] = Field(
        default=[],
        description="Emotional beats identified in scene"
    )
    subtext_instances: list[SubtextItem] = Field(
        default=[],
        description="Subtext instances in dialogue"
    )
    vulnerability_moments: list[str] = Field(
        default=[],
        description="Moments of character vulnerability"
    )

    # Problem areas
    skim_risk_areas: list[ParagraphIssueItem] = Field(
        default=[],
        description="Areas where readers might skim"
    )

    # Scene ending
    ending_resonance_type: str = Field(
        ...,
        description="'image', 'question', 'ache', 'realization', or 'weak'"
    )

    # Reader arc
    reader_emotional_arc: str = Field(
        ...,
        description="How reader should feel: start -> middle -> end"
    )

    # Scores
    micro_tension_score: float = Field(
        ..., ge=1, le=10,
        description="Line-by-line micro-tension present (1-10)"
    )
    overall_emotional_score: float = Field(
        ..., ge=1, le=10,
        description="Overall emotional resonance score (1-10)"
    )

    class Config:
        extra = "ignore"

    @property
    def needs_revision(self) -> bool:
        return (
            self.overall_emotional_score < 7 or
            self.ending_resonance_type == "weak" or
            len(self.skim_risk_areas) > 2
        )


class SceneCritiqueBundle(BaseModel):
    """All critiques for a single scene, bundled for revision."""
    scene_id: str = Field(..., description="Scene identifier")

    # All 5 critiques
    prose_critique: ProsePolishCritique = Field(
        ..., description="Prose polish critique"
    )
    voice_critique: CharacterVoiceCritique = Field(
        ..., description="Character voice critique"
    )
    continuity_critique: ContinuityCritique = Field(
        ..., description="Continuity critique"
    )
    pacing_critique: PacingTensionCritique = Field(
        ..., description="Pacing and tension critique"
    )
    emotional_critique: EmotionalResonanceCritique = Field(
        ..., description="Emotional resonance critique"
    )

    # Aggregate
    needs_revision: bool = Field(
        ...,
        description="True if any critic flags revision needed"
    )
    priority_issues: list[str] = Field(
        default=[],
        description="Top 3 issues to fix first"
    )
    average_score: float = Field(
        ...,
        description="Average of all critic scores"
    )

    class Config:
        extra = "ignore"
