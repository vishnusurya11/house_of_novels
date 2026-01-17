"""
Storyboard Agents - Scene breakdown into shots for AI video generation.

Uses industry-standard screenplay/storyboard format:
- Sluglines (INT./EXT. LOCATION - TIME)
- Action lines (present tense)
- Dialogue with parentheticals
- Camera directions and transitions

3 Specialized Critics:
- Visual Critic: Camera, framing, lighting, blocking
- Dialogue Critic: Timing, delivery, word count, flow
- Continuity Critic: Shot flow, consistency, pacing
"""

import json
from typing import Optional

from src.story_agents.base_story_agent import BaseStoryAgent
from src.story_schemas import (
    StoryboardSchema,
    ShotSchema,
    VisualCritiqueSchema,
    DialogueCritiqueSchema,
    ContinuityCritiqueSchema,
)
from src.config import DEFAULT_MODEL


# =============================================================================
# Storyboard Creator Agent
# =============================================================================

class StoryboardCreatorAgent(BaseStoryAgent):
    """Breaks narrative scenes into shots using industry-standard screenplay format."""

    @property
    def name(self) -> str:
        return "STORYBOARD_CREATOR"

    @property
    def role(self) -> str:
        return "Storyboard artist and shot designer"

    @property
    def system_prompt(self) -> str:
        return """You are an expert STORYBOARD ARTIST breaking narrative prose into video shots.

Each SHOT should be 10-15 seconds of screen time (~25-35 words of dialogue max).

## INDUSTRY-STANDARD SHOT FORMAT

For each shot, provide:

### 1. SLUGLINE (Scene Heading)
Format: INT./EXT. LOCATION - TIME OF DAY
Example: INT. FATHER'S STUDY - AFTERNOON

### 2. SHOT SPECIFICATIONS
- **Shot Number**: Sequential (1, 2, 3...)
- **Duration**: 10-15 seconds
- **Shot Size**: WIDE, MEDIUM, CLOSE-UP, EXTREME CLOSE-UP, OVER-SHOULDER, POV
- **Camera Movement**: STATIC, PAN LEFT, PAN RIGHT, TILT UP, TILT DOWN, DOLLY IN, DOLLY OUT, TRACKING, CRANE, PUSH IN

### 3. ACTION LINE (Present Tense)
Describe what we SEE on screen. Be specific about:
- Character positions (frame left, frame right, center)
- Physical actions and gestures
- Foreground/midground/background elements
- Lighting and atmosphere notes

### 4. CHARACTER & DIALOGUE
Format:
                    CHARACTER NAME
            (parenthetical: tone, action)
    Dialogue line here, natural length.

Dialogue rules:
- ~150 words per minute speaking rate
- 10-second shot = MAX 25 words dialogue
- 15-second shot = MAX 37 words dialogue
- Split long speeches across multiple shots
- Include (V.O.) for voiceover, (O.S.) for off-screen

### 5. AUDIO/TRANSITION
- Ambient sounds, music cues, SFX
- Transition: CUT TO, DISSOLVE TO, FADE TO BLACK, MATCH CUT

## EXAMPLE SHOT

SHOT 3 | 12 sec | CU | DOLLY IN

INT. FATHER'S STUDY - AFTERNOON

CLOSE on ELENA's face as recognition dawns. Her eyes widen,
fingers trembling against aged parchment. Dust motes drift
through the amber light from the window behind her.

                    ELENA
            (whispered, breathless)
    This can't be real...

SFX: Clock ticking loudly. Paper rustling.
MUSIC: Subtle tension strings begin.

CUT TO:

OUTPUT: Complete shot list that recreates the scene for AI video generation."""

    def create_storyboard(
        self,
        scene_id: str,
        scene_text: str,
        scene_location: str,
        scene_characters: list[str],
        character_context: str,
        location_context: str,
    ) -> StoryboardSchema:
        """
        Create initial storyboard from narrative scene.

        Args:
            scene_id: Unique identifier (e.g., 'act1_scene2')
            scene_text: Full narrative prose for the scene
            scene_location: Location name from narrative
            scene_characters: Character names in scene
            character_context: Relevant character descriptions
            location_context: Relevant location descriptions

        Returns:
            StoryboardSchema with all shots
        """
        prompt = f"""Break down this narrative scene into a storyboard with 10-15 second shots.

SCENE ID: {scene_id}
SCENE LOCATION: {scene_location}
CHARACTERS IN SCENE: {', '.join(scene_characters)}

NARRATIVE TEXT:
{scene_text}

CHARACTER DETAILS (for blocking and expressions):
{character_context}

LOCATION DETAILS (for visual descriptions):
{location_context}

Create a complete storyboard with:
1. Scene title (brief description)
2. All shots in sequence (typically 6-12 shots per scene)
3. Each shot with: slugline, shot specs, action, dialogue, audio, transition
4. Total duration estimate

Remember:
- Each shot is 10-15 seconds
- Dialogue max 25-35 words per shot
- Use industry-standard format
- Include camera directions and transitions
- Describe visual details for AI video generation"""

        return self.invoke_structured(prompt, StoryboardSchema, max_tokens=4000)

    def revise_storyboard(
        self,
        current_storyboard: StoryboardSchema,
        visual_critique: VisualCritiqueSchema,
        dialogue_critique: DialogueCritiqueSchema,
        continuity_critique: ContinuityCritiqueSchema,
        scene_text: str,
    ) -> StoryboardSchema:
        """
        Revise storyboard based on all 3 critics' feedback.

        Args:
            current_storyboard: Current storyboard to revise
            visual_critique: Visual critic's feedback
            dialogue_critique: Dialogue critic's feedback
            continuity_critique: Continuity critic's feedback
            scene_text: Original scene for reference

        Returns:
            Revised StoryboardSchema
        """
        storyboard_json = current_storyboard.model_dump_json(indent=2)

        # Format critiques
        visual_issues = "\n".join(f"- {s}" for s in visual_critique.suggestions)
        dialogue_issues = "\n".join(f"- {s}" for s in dialogue_critique.suggestions)
        continuity_issues = "\n".join(f"- {s}" for s in continuity_critique.suggestions)

        word_violations = dialogue_critique.word_count_violations
        word_warning = ""
        if word_violations:
            word_warning = f"\nWORD COUNT VIOLATIONS in shots: {word_violations} - MUST reduce dialogue!"

        cont_errors = "\n".join(f"- {e}" for e in continuity_critique.continuity_errors)

        prompt = f"""REVISE this storyboard based on critic feedback:

CURRENT STORYBOARD:
{storyboard_json}

VISUAL CRITIQUE (Score: {visual_critique.overall_score}/10):
{visual_issues}

DIALOGUE CRITIQUE (Score: {dialogue_critique.overall_score}/10):
{dialogue_issues}{word_warning}

CONTINUITY CRITIQUE (Score: {continuity_critique.overall_score}/10):
{continuity_issues}
Continuity Errors: {cont_errors if cont_errors else 'None'}

ORIGINAL SCENE (reference):
{scene_text}

Create an IMPROVED storyboard addressing ALL critic concerns.
Focus especially on categories that scored below 7.
Ensure dialogue word counts fit within shot durations (25-35 words max per 10-15 sec shot)."""

        return self.invoke_structured(prompt, StoryboardSchema, max_tokens=4000)


# =============================================================================
# Visual Critic Agent
# =============================================================================

class VisualCriticAgent(BaseStoryAgent):
    """Critiques visual/cinematography elements of storyboard."""

    @property
    def name(self) -> str:
        return "STORYBOARD_VISUAL_CRITIC"

    @property
    def role(self) -> str:
        return "Cinematographer and visual design expert"

    @property
    def system_prompt(self) -> str:
        return """You are a CINEMATOGRAPHER reviewing storyboard shots.

EVALUATE EACH SHOT ON:

1. LOCATION CLARITY (1-10)
   - Is INT./EXT. specified correctly?
   - Does location match codex descriptions?
   - Are specific areas of location described?

2. SHOT COMPOSITION (1-10)
   - Is shot size appropriate for content?
   - Are depth layers present (foreground/mid/background)?
   - Is framing clear for AI video generation?

3. CAMERA WORK (1-10)
   - Is camera movement motivated by story?
   - Are movements achievable for AI video?
   - Do movements enhance emotional impact?

4. LIGHTING & TIME (1-10)
   - Is time of day consistent in slugline?
   - Are lighting conditions described?
   - Does lighting support the mood?

5. CHARACTER BLOCKING (1-10)
   - Are character positions clear (frame L/R/C)?
   - Are spatial relationships defined?
   - Can this blocking be recreated?

6. VISUAL STORYTELLING (1-10)
   - Does visual focus guide attention?
   - Are key story moments emphasized?
   - Is the shot visually interesting?

DECISION: needs_revision = true if ANY score < 7
Provide SPECIFIC visual improvements."""

    def critique(
        self,
        storyboard: StoryboardSchema,
        location_context: str,
    ) -> VisualCritiqueSchema:
        """
        Critique storyboard for visual quality.

        Args:
            storyboard: The storyboard to evaluate
            location_context: Location details for reference

        Returns:
            VisualCritiqueSchema with scores and suggestions
        """
        storyboard_json = storyboard.model_dump_json(indent=2)

        prompt = f"""EVALUATE this storyboard for VISUAL quality:

STORYBOARD:
{storyboard_json}

LOCATION REFERENCE:
{location_context}

Score each visual category 1-10.
Provide SPECIFIC suggestions for shots scoring below 8.
Be critical - only excellent visual direction should pass without revision.

Consider:
- Are INT./EXT. labels correct?
- Is each shot's framing and composition clear?
- Do camera movements serve the story?
- Is lighting described appropriately?
- Are character positions precise?
- Will AI video understand these directions?"""

        return self.invoke_structured(prompt, VisualCritiqueSchema, max_tokens=1500)


# =============================================================================
# Dialogue Critic Agent
# =============================================================================

class DialogueCriticAgent(BaseStoryAgent):
    """Critiques dialogue timing, delivery, and audio elements."""

    @property
    def name(self) -> str:
        return "STORYBOARD_DIALOGUE_CRITIC"

    @property
    def role(self) -> str:
        return "Dialogue director and audio specialist"

    @property
    def system_prompt(self) -> str:
        return """You are a DIALOGUE DIRECTOR reviewing storyboard shots.

## TIMING RULES
- Speaking rate: ~150 words/minute = 2.5 words/second
- 10-second shot = MAX 25 words dialogue
- 15-second shot = MAX 37 words dialogue
- Include pause time for reactions

EVALUATE EACH SHOT ON:

1. DIALOGUE LENGTH (1-10)
   - Does dialogue fit the duration?
   - COUNT WORDS: exceeding limit = automatic fail (score 1)
   - Are long speeches properly split?

2. DELIVERY NOTES (1-10)
   - Are parentheticals present for tone?
   - Is pacing indicated (pause, beat)?
   - Are emphasis points marked?

3. NATURAL FLOW (1-10)
   - Does dialogue sound natural spoken aloud?
   - Are there awkward mid-sentence breaks?
   - Do conversations flow logically?

4. CHARACTER VOICE (1-10)
   - Does dialogue match character personality?
   - Is vocabulary appropriate?
   - Are speech patterns consistent?

5. AUDIO DESIGN (1-10)
   - Are ambient sounds specified?
   - Are music cues appropriate?
   - Is audio-visual sync clear?
   - Are SFX meaningful to story?

DECISION: needs_revision = true if ANY score < 7
FLAG any shot exceeding word count limit in word_count_violations."""

    def critique(
        self,
        storyboard: StoryboardSchema,
        character_context: str,
    ) -> DialogueCritiqueSchema:
        """
        Critique storyboard for dialogue and audio quality.

        Args:
            storyboard: The storyboard to evaluate
            character_context: Character details for voice consistency

        Returns:
            DialogueCritiqueSchema with scores and suggestions
        """
        storyboard_json = storyboard.model_dump_json(indent=2)

        prompt = f"""EVALUATE this storyboard for DIALOGUE and AUDIO quality:

STORYBOARD:
{storyboard_json}

CHARACTER REFERENCE:
{character_context}

Score each dialogue/audio category 1-10.

CRITICAL: Count words in each shot's dialogue!
- 10 sec shot = MAX 25 words
- 15 sec shot = MAX 37 words
- List any shots exceeding limits in word_count_violations

Provide SPECIFIC suggestions for improvement.
Check that parentheticals guide voice actors on tone.
Verify SFX and music cues enhance the story."""

        return self.invoke_structured(prompt, DialogueCritiqueSchema, max_tokens=1500)


# =============================================================================
# Continuity Critic Agent
# =============================================================================

class ContinuityCriticAgent(BaseStoryAgent):
    """Critiques continuity and scene flow."""

    @property
    def name(self) -> str:
        return "STORYBOARD_CONTINUITY_CRITIC"

    @property
    def role(self) -> str:
        return "Script supervisor and continuity expert"

    @property
    def system_prompt(self) -> str:
        return """You are a SCRIPT SUPERVISOR reviewing storyboard continuity.

EVALUATE THE STORYBOARD ON:

1. SHOT-TO-SHOT FLOW (1-10)
   - Do shots connect logically?
   - Is the 180-degree rule respected?
   - Are eyeline matches correct?
   - Do transitions make sense?

2. CHARACTER CONTINUITY (1-10)
   - Are characters in consistent positions?
   - Do clothes/props remain consistent?
   - Are character states maintained (emotions, wounds)?
   - Do characters exit/enter logically?

3. LOCATION CONTINUITY (1-10)
   - Does environment remain consistent?
   - Are time-of-day changes logical?
   - Do spatial relationships make sense?
   - Is weather consistent within scene?

4. STORY CONTEXT (1-10)
   - Does storyboard capture scene purpose?
   - Is the emotional arc preserved?
   - Are all key plot points included?
   - Is the narrative complete?

5. PACING & RHYTHM (1-10)
   - Is there shot variety (wide/medium/close)?
   - Does pacing match scene mood?
   - Are there too many/few shots?
   - Is timing balanced?

6. OVERALL COHERENCE (1-10)
   - Would this work as video sequence?
   - Are there gaps in action?
   - Is the scene complete?
   - Can AI video generate this?

DECISION: needs_revision = true if ANY score < 7
List specific continuity errors found."""

    def critique(
        self,
        storyboard: StoryboardSchema,
        scene_text: str,
    ) -> ContinuityCritiqueSchema:
        """
        Critique storyboard for continuity and flow.

        Args:
            storyboard: The storyboard to evaluate
            scene_text: Original scene for context reference

        Returns:
            ContinuityCritiqueSchema with scores and suggestions
        """
        storyboard_json = storyboard.model_dump_json(indent=2)

        prompt = f"""EVALUATE this storyboard for CONTINUITY and FLOW:

STORYBOARD:
{storyboard_json}

ORIGINAL SCENE (reference):
{scene_text}

Score each continuity category 1-10.
List specific continuity errors in continuity_errors field.

Check:
- Does each shot flow logically to the next?
- Are character positions consistent?
- Is the 180-degree rule maintained?
- Are time-of-day and lighting consistent?
- Does the storyboard capture the full scene?
- Is there good shot variety for visual interest?
- Does pacing match the emotional tone?"""

        return self.invoke_structured(prompt, ContinuityCritiqueSchema, max_tokens=1500)


# =============================================================================
# Helper Functions
# =============================================================================

def get_character_context(character_names: list[str], all_characters: list[dict]) -> str:
    """Extract relevant character details for storyboard context."""
    relevant = []
    for char in all_characters:
        if char.get("name") in character_names:
            char_id = char.get("id", "unknown")
            relevant.append(
                f"**{char.get('name')}** (ID: {char_id}): {char.get('gender', 'unknown')}, "
                f"{char.get('age', 'unknown')}. "
                f"Physical: {json.dumps(char.get('physical', {}), indent=2)}. "
                f"Clothing: {char.get('clothing', 'unspecified')}. "
                f"Traits: {', '.join(char.get('personality_traits', []))}."
            )
    return "\n".join(relevant) if relevant else "No character details available."


def build_character_id_map(all_characters: list[dict]) -> dict[str, str]:
    """Build mapping from character name (uppercase) to ID."""
    id_map = {}
    for char in all_characters:
        name = char.get("name", "")
        char_id = char.get("id", "")
        if name and char_id:
            # Map both uppercase first name and full name
            first_name = name.split()[0].upper() if name else ""
            id_map[first_name] = char_id
            id_map[name.upper()] = char_id
            id_map[name] = char_id
    return id_map


def build_location_id_map(all_locations: list[dict]) -> dict[str, str]:
    """Build mapping from location name to ID."""
    id_map = {}
    for loc in all_locations:
        name = loc.get("name", "")
        loc_id = loc.get("id", "")
        if name and loc_id:
            id_map[name] = loc_id
            id_map[name.upper()] = loc_id
    return id_map


def get_location_context(location_name: str, all_locations: list[dict]) -> str:
    """Extract relevant location details for storyboard context."""
    for loc in all_locations:
        if loc.get("name") == location_name:
            loc_id = loc.get("id", "unknown")
            return (
                f"**{loc.get('name')}** (ID: {loc_id}) ({loc.get('type', 'location')})\n"
                f"Description: {loc.get('description', 'No description')}\n"
                f"Atmosphere: {loc.get('atmosphere', 'No atmosphere')}\n"
                f"Key Features: {', '.join(loc.get('key_features', []))}\n"
                f"Sensory: {loc.get('sensory_details', 'No sensory details')}"
            )
    return f"Location '{location_name}' - no details available."


# =============================================================================
# Orchestration Function
# =============================================================================

def generate_scene_storyboard(
    scene_id: str,
    scene_text: str,
    scene_location: str,
    scene_characters: list[str],
    all_characters: list[dict],
    all_locations: list[dict],
    model: str = DEFAULT_MODEL,
    max_revisions: int = 2,
) -> dict:
    """
    Generate a storyboard for a single scene using creator + 3 critics.

    Args:
        scene_id: Unique ID (e.g., 'act1_scene2')
        scene_text: Full narrative prose for the scene
        scene_location: Location name
        scene_characters: Character names in scene
        all_characters: Full character profiles from codex
        all_locations: Full location profiles from codex
        model: LLM model to use
        max_revisions: Max critique-revision cycles

    Returns:
        Dict with:
        - storyboard: Final StoryboardSchema as dict
        - revision_count: Number of revisions made
        - metadata: Full critique history
    """
    creator = StoryboardCreatorAgent(model=model)
    visual_critic = VisualCriticAgent(model=model)
    dialogue_critic = DialogueCriticAgent(model=model)
    continuity_critic = ContinuityCriticAgent(model=model)

    # Get relevant context
    char_context = get_character_context(scene_characters, all_characters)
    loc_context = get_location_context(scene_location, all_locations)

    print(f"    Creating storyboard for: {scene_id}")

    # Initial storyboard generation
    storyboard = creator.create_storyboard(
        scene_id=scene_id,
        scene_text=scene_text,
        scene_location=scene_location,
        scene_characters=scene_characters,
        character_context=char_context,
        location_context=loc_context,
    )

    critique_history = []
    revision_count = 0

    # Critique-revision loop
    for i in range(max_revisions):
        print(f"      Critique cycle {i + 1}/{max_revisions}...")

        # Get critiques from all 3 critics
        visual_crit = visual_critic.critique(storyboard, loc_context)
        dialogue_crit = dialogue_critic.critique(storyboard, char_context)
        continuity_crit = continuity_critic.critique(storyboard, scene_text)

        # Check if any revision needed
        any_needs_revision = (
            visual_crit.needs_revision or
            dialogue_crit.needs_revision or
            continuity_crit.needs_revision
        )

        # Collect all scores
        all_scores = [
            visual_crit.location_clarity_score,
            visual_crit.shot_composition_score,
            visual_crit.camera_work_score,
            visual_crit.lighting_time_score,
            visual_crit.character_blocking_score,
            visual_crit.visual_storytelling_score,
            dialogue_crit.dialogue_length_score,
            dialogue_crit.delivery_notes_score,
            dialogue_crit.natural_flow_score,
            dialogue_crit.character_voice_score,
            dialogue_crit.audio_design_score,
            continuity_crit.shot_flow_score,
            continuity_crit.character_continuity_score,
            continuity_crit.location_continuity_score,
            continuity_crit.story_context_score,
            continuity_crit.pacing_rhythm_score,
            continuity_crit.overall_coherence_score,
        ]
        min_score = min(all_scores)

        # Store critique history
        critique_history.append({
            "cycle": i + 1,
            "visual": {
                "location_clarity": visual_crit.location_clarity_score,
                "shot_composition": visual_crit.shot_composition_score,
                "camera_work": visual_crit.camera_work_score,
                "lighting_time": visual_crit.lighting_time_score,
                "character_blocking": visual_crit.character_blocking_score,
                "visual_storytelling": visual_crit.visual_storytelling_score,
                "overall": visual_crit.overall_score,
                "needs_revision": visual_crit.needs_revision,
                "suggestions": visual_crit.suggestions,
            },
            "dialogue": {
                "dialogue_length": dialogue_crit.dialogue_length_score,
                "delivery_notes": dialogue_crit.delivery_notes_score,
                "natural_flow": dialogue_crit.natural_flow_score,
                "character_voice": dialogue_crit.character_voice_score,
                "audio_design": dialogue_crit.audio_design_score,
                "overall": dialogue_crit.overall_score,
                "needs_revision": dialogue_crit.needs_revision,
                "word_count_violations": dialogue_crit.word_count_violations,
                "suggestions": dialogue_crit.suggestions,
            },
            "continuity": {
                "shot_flow": continuity_crit.shot_flow_score,
                "character_continuity": continuity_crit.character_continuity_score,
                "location_continuity": continuity_crit.location_continuity_score,
                "story_context": continuity_crit.story_context_score,
                "pacing_rhythm": continuity_crit.pacing_rhythm_score,
                "overall_coherence": continuity_crit.overall_coherence_score,
                "overall": continuity_crit.overall_score,
                "needs_revision": continuity_crit.needs_revision,
                "continuity_errors": continuity_crit.continuity_errors,
                "suggestions": continuity_crit.suggestions,
            },
            "min_score": min_score,
            "any_needs_revision": any_needs_revision,
        })

        # Check if approved
        if not any_needs_revision and min_score >= 7:
            print(f"      Approved! Min score: {min_score}")
            break

        # Revise if not last cycle
        if i < max_revisions - 1:
            print(f"      Revising (min score: {min_score})...")
            storyboard = creator.revise_storyboard(
                current_storyboard=storyboard,
                visual_critique=visual_crit,
                dialogue_critique=dialogue_crit,
                continuity_critique=continuity_crit,
                scene_text=scene_text,
            )
            revision_count += 1

    # Post-process: Add character_ids and location_id to each shot
    char_id_map = build_character_id_map(all_characters)
    loc_id_map = build_location_id_map(all_locations)

    # Get the location ID for this scene - all shots in a scene share the same location
    # Use scene_location (the codex location name) since shot locations may have different names
    scene_location_id = loc_id_map.get(scene_location)

    storyboard_dict = storyboard.model_dump()
    for shot in storyboard_dict.get("shots", []):
        # Map characters_in_frame names to IDs
        char_ids = []
        for char_name in shot.get("characters_in_frame", []):
            char_id = char_id_map.get(char_name) or char_id_map.get(char_name.upper())
            if char_id:
                char_ids.append(char_id)
        shot["character_ids"] = char_ids

        # Use scene location ID for all shots in this scene
        shot["location_id"] = scene_location_id

    return {
        "storyboard": storyboard_dict,
        "revision_count": revision_count,
        "metadata": {
            "scene_id": scene_id,
            "shot_count": storyboard.shot_count,
            "total_duration": storyboard.total_duration_seconds,
            "revision_count": revision_count,
            "critique_history": critique_history,
        },
    }
