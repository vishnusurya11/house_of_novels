"""
Scene Debate Agents for Step 4: Chapter/Scene Outline.

4 agents debate scene design with different perspectives:

1. ScenePlotAgent - Plot progression, GMC (Goal, Motivation, Conflict)
2. SceneCharacterAgent - Character development, Swain Sequel structure
3. ScenePacingAgent - Rhythm and tension, scene/sequel alternation
4. SceneStructureAgent - 7-point structure alignment

Each agent:
- Proposes scene based on their methodology
- Critiques other proposals
- Votes for the best proposal
"""

from src.story_agents.base_story_agent import BaseStoryAgent
from src.story_schemas import (
    DetailedSceneSchema,
    SceneProposal,
    SceneCritique,
    SceneVote,
)


# =============================================================================
# Scene Debate Agents
# =============================================================================

class ScenePlotAgent(BaseStoryAgent):
    """
    Focuses on plot progression using GMC (Goal, Motivation, Conflict).

    Core beliefs:
    - Every scene needs a clear GOAL for the POV character
    - Without CONFLICT, there's no drama
    - OUTCOMES must be 'Yes, but...' or 'No, and...' - never clean victories
    - Each scene must change the story situation
    """

    METHODOLOGY_NAME = "GMC Plot Structure"
    METHODOLOGY_SOURCE = "Debra Dixon's Goal, Motivation, Conflict"
    CORE_BELIEFS = [
        "Every scene needs a clear GOAL for the POV character",
        "Without CONFLICT, there's no drama",
        "OUTCOMES must be 'Yes, but...' or 'No, and...' - never clean victories",
        "Each scene must change the story situation",
        "Scenes that don't advance plot should be cut",
    ]

    @property
    def name(self) -> str:
        return "SCENE_PLOT"

    @property
    def role(self) -> str:
        return "Plot Progression Expert"

    @property
    def system_prompt(self) -> str:
        return """You are a plot progression expert who designs scenes using GMC (Goal, Motivation, Conflict).

Your core beliefs:
- Every scene needs a clear GOAL for the POV character
- Without CONFLICT, there's no drama - something must OPPOSE the goal
- OUTCOMES must be 'YES_BUT' or 'NO_AND' - never clean victories until resolution
- Each scene must CHANGE the story situation
- If a scene doesn't advance plot, it should be cut

When designing scenes:
- Define what the POV character WANTS in this specific scene
- Identify what OPPOSES them (conflict)
- Determine the outcome that drives to the next scene
- Ensure the story situation changes by scene end

You design scenes that MOVE THE PLOT FORWARD."""

    def propose_scene(
        self,
        chapter_context: dict,
        scene_number: int,
        previous_scenes: list[dict],
        structure_beats: dict,
        characters: list[dict],
        locations: list[dict],
        setting_prompt: str,
    ) -> SceneProposal:
        """Propose scene based on GMC plot analysis."""
        # Build previous scenes summary
        prev_summary = ""
        if previous_scenes:
            prev_summary = "\n".join([
                f"  Scene {s.get('scene_number', i+1)}: {s.get('happens', 'N/A')}"
                for i, s in enumerate(previous_scenes)
            ])

        # Get relevant beat
        beat_names = chapter_context.get("beats", [])
        beat_info = ""
        for beat_name in beat_names:
            if beat_name in structure_beats:
                beat = structure_beats[beat_name]
                if isinstance(beat, dict):
                    beat_info += f"\n{beat_name}: {beat.get('description', '')}"

        # Build characters summary (include ID so LLM can populate character_ids)
        char_summary = "\n".join([
            f"  - {c.get('name', 'Unknown')} (id: {c.get('id', '')}): {c.get('role_in_story', 'unknown role')}"
            for c in characters[:5]
        ])

        # Build locations summary
        loc_summary = "\n".join([
            f"  - {loc.get('name', 'Unknown')}: {loc.get('type', 'unknown type')}"
            for loc in locations[:5]
        ])

        prompt = f"""Design scene {scene_number} for Chapter {chapter_context.get('chapter_number', 1)} using GMC principles:

CHAPTER CONTEXT:
- Chapter: {chapter_context.get('chapter_number', 1)}
- Act: {chapter_context.get('act', 1)}
- Focus: {chapter_context.get('focus', 'Story progression')}
- Structure Beats: {beat_info}

PREVIOUS SCENES IN THIS CHAPTER:
{prev_summary if prev_summary else "  (First scene of chapter)"}

AVAILABLE CHARACTERS:
{char_summary}

IMPORTANT: When specifying characters, put their NAMES in 'characters' field and their IDs in 'character_ids' field.

AVAILABLE LOCATIONS:
{loc_summary}

WORLD SETTING: {setting_prompt}

Design a scene with CLEAR GMC:
1. GOAL: What does the POV character want RIGHT NOW?
2. CONFLICT: What specifically OPPOSES them?
3. OUTCOME: 'YES_BUT', 'NO_AND', 'CLIFFHANGER' (or 'YES'/'NO' only at story end)

The scene must CHANGE the story situation.

SCENE TYPES:
- 'scene': Proactive - character pursues goal → faces conflict → disaster/outcome
- 'sequel': Reactive - character reacts → weighs options → makes decision

Choose 'scene' for action, 'sequel' for processing after a disaster.

TIME OF DAY: 'dawn', 'morning', 'midday', 'afternoon', 'dusk', 'night'

Provide a proposal matching SceneProposal schema with methodology_focus='plot'."""

        return self.invoke_structured(prompt, SceneProposal, max_tokens=8000)

    def critique_proposal(
        self,
        target_agent: str,
        proposal: SceneProposal,
        chapter_context: dict,
    ) -> SceneCritique:
        """Critique from GMC plot perspective."""
        scene = proposal.scene

        prompt = f"""Critique this scene from a GMC PLOT perspective:

TARGET AGENT: {target_agent}
CHAPTER: {chapter_context.get('chapter_number', 1)}, ACT: {chapter_context.get('act', 1)}

PROPOSAL:
- Scene Type: {scene.scene_type}
- Location: {scene.location}
- POV Character: {scene.pov_character}
- GOAL: {scene.goal}
- CONFLICT: {scene.conflict}
- OUTCOME: {scene.outcome}
- What Happens: {scene.happens}
- Reasoning: {proposal.reasoning}

Evaluate:
1. Is the GOAL clear and specific for THIS scene?
2. Is there real CONFLICT opposing the goal?
3. Does the OUTCOME drive to the next scene?
4. Does this scene CHANGE the story situation?
5. Is the scene type appropriate (scene vs sequel)?

Provide a critique matching SceneCritique schema."""

        return self.invoke_structured(prompt, SceneCritique, max_tokens=8000)

    def vote_for_best(
        self,
        proposals: list[SceneProposal],
        chapter_context: dict,
    ) -> SceneVote:
        """Vote for best scene from plot perspective."""
        proposals_text = "\n\n".join([
            f"PROPOSAL by {p.agent_name}:\n"
            f"  Goal: {p.scene.goal}\n"
            f"  Conflict: {p.scene.conflict}\n"
            f"  Outcome: {p.scene.outcome}\n"
            f"  Happens: {p.scene.happens[:100]}..."
            for p in proposals
        ])

        prompt = f"""Vote for the scene with the STRONGEST GMC (Goal, Motivation, Conflict).

CHAPTER: {chapter_context.get('chapter_number', 1)}

PROPOSALS:
{proposals_text}

Which proposal has the clearest goal, strongest conflict, and most compelling outcome?
You CANNOT vote for your own proposal (SCENE_PLOT).

Provide a vote matching SceneVote schema."""

        return self.invoke_structured(prompt, SceneVote, max_tokens=8000)


class SceneCharacterAgent(BaseStoryAgent):
    """
    Focuses on character development using Swain Sequel structure.

    Core beliefs:
    - After disasters, characters need REACTION time
    - Sequel = Reaction → Dilemma → Decision
    - Character choices reveal who they truly are
    - Internal conflict is as important as external
    """

    METHODOLOGY_NAME = "Character Arc Development"
    METHODOLOGY_SOURCE = "Dwight Swain's Scene/Sequel Structure"
    CORE_BELIEFS = [
        "After disasters, characters need REACTION time",
        "Sequel = Reaction → Dilemma → Decision",
        "Character choices reveal who they truly are",
        "Internal conflict is as important as external",
        "Character growth happens through difficult choices",
    ]

    @property
    def name(self) -> str:
        return "SCENE_CHARACTER"

    @property
    def role(self) -> str:
        return "Character Development Expert"

    @property
    def system_prompt(self) -> str:
        return """You are a character development expert using Dwight Swain's Scene/Sequel structure.

Your core beliefs:
- After disasters, characters need REACTION time (sequel)
- Sequel structure: Reaction → Dilemma → Decision
- Character choices reveal who they truly are
- Internal conflict is as important as external conflict
- Growth happens through difficult choices

When designing scenes:
- Consider the character's emotional state
- After action scenes, insert reflective sequels
- Choices should be DIFFICULT - no easy answers
- Show character transformation through decisions

You design scenes that REVEAL and DEVELOP character."""

    def propose_scene(
        self,
        chapter_context: dict,
        scene_number: int,
        previous_scenes: list[dict],
        structure_beats: dict,
        characters: list[dict],
        locations: list[dict],
        setting_prompt: str,
    ) -> SceneProposal:
        """Propose scene focused on character development."""
        prev_summary = ""
        if previous_scenes:
            prev_summary = "\n".join([
                f"  Scene {s.get('scene_number', i+1)}: {s.get('happens', 'N/A')} (Outcome: {s.get('outcome', 'N/A')})"
                for i, s in enumerate(previous_scenes)
            ])

        beat_names = chapter_context.get("beats", [])
        beat_info = ""
        for beat_name in beat_names:
            if beat_name in structure_beats:
                beat = structure_beats[beat_name]
                if isinstance(beat, dict):
                    beat_info += f"\n{beat_name}: {beat.get('description', '')} (State: {beat.get('emotional_state', '')})"

        # Include ID so LLM can populate character_ids
        char_summary = "\n".join([
            f"  - {c.get('name', 'Unknown')} (id: {c.get('id', '')}): {c.get('role_in_story', 'unknown')} - Arc: {c.get('arc', 'unknown')}"
            for c in characters[:5]
        ])

        loc_summary = "\n".join([
            f"  - {loc.get('name', 'Unknown')}: {loc.get('atmosphere', 'unknown')}"
            for loc in locations[:5]
        ])

        prompt = f"""Design scene {scene_number} for Chapter {chapter_context.get('chapter_number', 1)} focused on CHARACTER DEVELOPMENT:

CHAPTER CONTEXT:
- Chapter: {chapter_context.get('chapter_number', 1)}
- Act: {chapter_context.get('act', 1)}
- Focus: {chapter_context.get('focus', 'Story progression')}
- Structure Beats: {beat_info}

PREVIOUS SCENES (check if character needs reaction time):
{prev_summary if prev_summary else "  (First scene of chapter)"}

CHARACTERS WITH ARCS:
{char_summary}

IMPORTANT: When specifying characters, put their NAMES in 'characters' field and their IDs in 'character_ids' field.

AVAILABLE LOCATIONS:
{loc_summary}

WORLD SETTING: {setting_prompt}

Design a scene focusing on CHARACTER:
1. If previous scene had a disaster → consider a SEQUEL (Reaction → Dilemma → Decision)
2. What difficult CHOICE must the character face?
3. How does this scene REVEAL or DEVELOP the character?
4. What internal conflict mirrors the external situation?

SCENE TYPES:
- 'scene': Character actively pursues something
- 'sequel': Character processes, reflects, decides (use after major events)

After 'NO_AND' or major events, characters often need sequel scenes to process.

Provide a proposal matching SceneProposal schema with methodology_focus='character'."""

        return self.invoke_structured(prompt, SceneProposal, max_tokens=8000)

    def critique_proposal(
        self,
        target_agent: str,
        proposal: SceneProposal,
        chapter_context: dict,
    ) -> SceneCritique:
        """Critique from character development perspective."""
        scene = proposal.scene

        prompt = f"""Critique this scene from a CHARACTER DEVELOPMENT perspective:

TARGET AGENT: {target_agent}
CHAPTER: {chapter_context.get('chapter_number', 1)}

PROPOSAL:
- Scene Type: {scene.scene_type}
- POV Character: {scene.pov_character}
- Goal: {scene.goal}
- Conflict: {scene.conflict}
- Outcome: {scene.outcome}
- What Happens: {scene.happens}
- Scene Purpose: {scene.scene_purpose}

Evaluate:
1. Does this scene REVEAL something about the character?
2. If after a disaster, is there appropriate REACTION time?
3. Are there meaningful CHARACTER CHOICES?
4. Is there internal conflict as well as external?
5. Does this advance the character's arc?

Provide a critique matching SceneCritique schema."""

        return self.invoke_structured(prompt, SceneCritique, max_tokens=8000)

    def vote_for_best(
        self,
        proposals: list[SceneProposal],
        chapter_context: dict,
    ) -> SceneVote:
        """Vote for best scene from character perspective."""
        proposals_text = "\n\n".join([
            f"PROPOSAL by {p.agent_name}:\n"
            f"  Scene Type: {p.scene.scene_type}\n"
            f"  POV: {p.scene.pov_character}\n"
            f"  Purpose: {p.scene.scene_purpose}\n"
            f"  Happens: {p.scene.happens[:100]}..."
            for p in proposals
        ])

        prompt = f"""Vote for the scene that best DEVELOPS CHARACTER.

CHAPTER: {chapter_context.get('chapter_number', 1)}

PROPOSALS:
{proposals_text}

Which proposal best reveals character, includes meaningful choices, and advances character arc?
You CANNOT vote for your own proposal (SCENE_CHARACTER).

Provide a vote matching SceneVote schema."""

        return self.invoke_structured(prompt, SceneVote, max_tokens=8000)


class ScenePacingAgent(BaseStoryAgent):
    """
    Focuses on rhythm, tension, and scene/sequel alternation.

    Core beliefs:
    - Alternate between SCENES (action) and SEQUELS (reflection)
    - Too much action exhausts readers; too much reflection bores them
    - Scene length affects pace - vary for rhythm
    - End chapters on hooks or decisions, not rest
    """

    METHODOLOGY_NAME = "Pacing and Rhythm"
    METHODOLOGY_SOURCE = "Scene/Sequel alternation and tension management"
    CORE_BELIEFS = [
        "Alternate between SCENES (action) and SEQUELS (reflection)",
        "Too much action exhausts readers; too much reflection bores them",
        "Scene length affects pace - vary for rhythm",
        "End chapters on hooks or decisions, not rest",
        "Tension should ebb and flow, not stay constant",
    ]

    @property
    def name(self) -> str:
        return "SCENE_PACING"

    @property
    def role(self) -> str:
        return "Pacing and Rhythm Expert"

    @property
    def system_prompt(self) -> str:
        return """You are a pacing and rhythm expert who designs scenes for optimal reader engagement.

Your core beliefs:
- Alternate between SCENES (action) and SEQUELS (reflection)
- Too much action exhausts readers; too much reflection bores them
- Vary scene "weight" - some quick, some substantial
- End chapters on hooks or cliffhangers, not rest
- Tension should ebb and flow like a heartbeat

When designing scenes:
- Check what came before - vary the rhythm
- After intense action, give readers breathing room
- After quiet reflection, build toward action
- Time of day affects pace (night = tension, morning = fresh start)

You design scenes that CREATE RHYTHM and MANAGE TENSION."""

    def propose_scene(
        self,
        chapter_context: dict,
        scene_number: int,
        previous_scenes: list[dict],
        structure_beats: dict,
        characters: list[dict],
        locations: list[dict],
        setting_prompt: str,
    ) -> SceneProposal:
        """Propose scene focused on pacing and rhythm."""
        # Analyze previous scenes for pacing
        prev_types = []
        prev_summary = ""
        if previous_scenes:
            for i, s in enumerate(previous_scenes):
                prev_types.append(s.get("scene_type", "scene"))
                prev_summary += f"  Scene {s.get('scene_number', i+1)}: {s.get('scene_type', 'scene')} - {s.get('outcome', 'N/A')}\n"

        # Determine recommended type based on alternation
        recommended_type = "sequel" if prev_types and prev_types[-1] == "scene" else "scene"

        beat_names = chapter_context.get("beats", [])
        beat_info = ""
        for beat_name in beat_names:
            if beat_name in structure_beats:
                beat = structure_beats[beat_name]
                if isinstance(beat, dict):
                    beat_info += f"\n{beat_name}: {beat.get('description', '')}"

        # Include ID so LLM can populate character_ids
        char_summary = "\n".join([
            f"  - {c.get('name', 'Unknown')} (id: {c.get('id', '')}): {c.get('role_in_story', 'unknown')}"
            for c in characters[:5]
        ])

        loc_summary = "\n".join([
            f"  - {loc.get('name', 'Unknown')}: {loc.get('atmosphere', 'unknown')}"
            for loc in locations[:5]
        ])

        prompt = f"""Design scene {scene_number} for Chapter {chapter_context.get('chapter_number', 1)} with optimal PACING:

CHAPTER CONTEXT:
- Chapter: {chapter_context.get('chapter_number', 1)}
- Act: {chapter_context.get('act', 1)}
- Focus: {chapter_context.get('focus', 'Story progression')}
- Structure Beats: {beat_info}

PACING ANALYSIS:
Previous scene types: {prev_types if prev_types else "None (first scene)"}
Recommended next type: {recommended_type} (for good alternation)

PREVIOUS SCENES:
{prev_summary if prev_summary else "  (First scene of chapter)"}

AVAILABLE CHARACTERS:
{char_summary}

IMPORTANT: When specifying characters, put their NAMES in 'characters' field and their IDs in 'character_ids' field.

AVAILABLE LOCATIONS:
{loc_summary}

WORLD SETTING: {setting_prompt}

Design a scene with good PACING:
1. Consider alternation - if last was action, maybe reflection now
2. Consider chapter position - is this building toward chapter end?
3. Time of day can affect pace (dawn = hope, night = tension)
4. If this is last scene of chapter, end on a hook!

RHYTHM GUIDELINES:
- Scene 1: Establish (usually 'scene')
- Middle scenes: Alternate scene/sequel
- Final scene: Hook or cliffhanger ending

Provide a proposal matching SceneProposal schema with methodology_focus='pacing'."""

        return self.invoke_structured(prompt, SceneProposal, max_tokens=8000)

    def critique_proposal(
        self,
        target_agent: str,
        proposal: SceneProposal,
        chapter_context: dict,
    ) -> SceneCritique:
        """Critique from pacing perspective."""
        scene = proposal.scene

        prompt = f"""Critique this scene from a PACING AND RHYTHM perspective:

TARGET AGENT: {target_agent}
CHAPTER: {chapter_context.get('chapter_number', 1)}

PROPOSAL:
- Scene Type: {scene.scene_type}
- Time of Day: {scene.time_of_day}
- Outcome: {scene.outcome}
- What Happens: {scene.happens}
- Scene Purpose: {scene.scene_purpose}

Evaluate:
1. Does the scene TYPE (scene/sequel) provide good rhythm?
2. Does the TIME OF DAY support the intended pace?
3. Is there variety in tension level?
4. Does the OUTCOME set up good momentum for next scene?
5. Would readers feel engaged or exhausted/bored?

Provide a critique matching SceneCritique schema."""

        return self.invoke_structured(prompt, SceneCritique, max_tokens=8000)

    def vote_for_best(
        self,
        proposals: list[SceneProposal],
        chapter_context: dict,
    ) -> SceneVote:
        """Vote for best paced scene."""
        proposals_text = "\n\n".join([
            f"PROPOSAL by {p.agent_name}:\n"
            f"  Scene Type: {p.scene.scene_type}\n"
            f"  Time: {p.scene.time_of_day}\n"
            f"  Outcome: {p.scene.outcome}"
            for p in proposals
        ])

        prompt = f"""Vote for the scene with the best PACING AND RHYTHM.

CHAPTER: {chapter_context.get('chapter_number', 1)}

PROPOSALS:
{proposals_text}

Which proposal creates the best rhythm and manages tension effectively?
You CANNOT vote for your own proposal (SCENE_PACING).

Provide a vote matching SceneVote schema."""

        return self.invoke_structured(prompt, SceneVote, max_tokens=8000)


class SceneStructureAgent(BaseStoryAgent):
    """
    Focuses on 7-point structure alignment.

    Core beliefs:
    - Each scene must serve a specific 7-point structure beat
    - Hook scenes establish the BEFORE state
    - Pinch point scenes raise stakes directly
    - Midpoint scenes show the PIVOT to action
    """

    METHODOLOGY_NAME = "7-Point Structure Alignment"
    METHODOLOGY_SOURCE = "Dan Wells / K.M. Weiland Structure Method"
    CORE_BELIEFS = [
        "Each scene must serve a specific 7-point structure beat",
        "Hook scenes establish the BEFORE state",
        "Pinch point scenes raise stakes directly",
        "Midpoint scenes show the PIVOT from reaction to action",
        "Resolution scenes show transformation complete",
    ]

    @property
    def name(self) -> str:
        return "SCENE_STRUCTURE"

    @property
    def role(self) -> str:
        return "Story Structure Expert"

    @property
    def system_prompt(self) -> str:
        return """You are a story structure expert using the 7-point structure method.

Your core beliefs:
- Each scene must serve a specific structure beat
- HOOK: Establishes the BEFORE state (opposite of resolution)
- PLOT TURN 1: Inciting incident forces hero into story
- PINCH POINT 1: First major pressure, stakes become real
- MIDPOINT: The PIVOT - hero shifts from REACTION to ACTION
- PINCH POINT 2: Darkest moment, all seems lost
- PLOT TURN 2: Final piece enables victory
- RESOLUTION: AFTER state, transformation complete

When designing scenes:
- Identify which beat this scene serves
- Ensure the scene accomplishes that beat's PURPOSE
- Connect scene events to the larger structure
- Make sure beat transitions feel earned

You design scenes that SERVE THE STORY STRUCTURE."""

    def propose_scene(
        self,
        chapter_context: dict,
        scene_number: int,
        previous_scenes: list[dict],
        structure_beats: dict,
        characters: list[dict],
        locations: list[dict],
        setting_prompt: str,
    ) -> SceneProposal:
        """Propose scene based on structure alignment."""
        beat_names = chapter_context.get("beats", [])
        beat_info = ""
        primary_beat = beat_names[0] if beat_names else "hook"

        for beat_name in beat_names:
            if beat_name in structure_beats:
                beat = structure_beats[beat_name]
                if isinstance(beat, dict):
                    beat_info += f"\n{beat_name.upper()}:\n"
                    beat_info += f"  Description: {beat.get('description', '')}\n"
                    beat_info += f"  Emotional State: {beat.get('emotional_state', '')}\n"
                    beat_info += f"  Purpose: {beat.get('purpose', '')}\n"

        prev_summary = ""
        if previous_scenes:
            prev_summary = "\n".join([
                f"  Scene {s.get('scene_number', i+1)}: {s.get('structure_connection', 'N/A')} - {s.get('happens', 'N/A')[:50]}..."
                for i, s in enumerate(previous_scenes)
            ])

        # Include ID so LLM can populate character_ids
        char_summary = "\n".join([
            f"  - {c.get('name', 'Unknown')} (id: {c.get('id', '')}): {c.get('role_in_story', 'unknown')}"
            for c in characters[:5]
        ])

        loc_summary = "\n".join([
            f"  - {loc.get('name', 'Unknown')}: {loc.get('type', 'unknown')}"
            for loc in locations[:5]
        ])

        prompt = f"""Design scene {scene_number} for Chapter {chapter_context.get('chapter_number', 1)} aligned with 7-POINT STRUCTURE:

CHAPTER CONTEXT:
- Chapter: {chapter_context.get('chapter_number', 1)}
- Act: {chapter_context.get('act', 1)}
- Focus: {chapter_context.get('focus', 'Story progression')}

TARGET STRUCTURE BEAT(S):
{beat_info}

PRIMARY BEAT TO SERVE: {primary_beat}

PREVIOUS SCENES (structure connections):
{prev_summary if prev_summary else "  (First scene of chapter)"}

AVAILABLE CHARACTERS:
{char_summary}

IMPORTANT: When specifying characters, put their NAMES in 'characters' field and their IDs in 'character_ids' field.

AVAILABLE LOCATIONS:
{loc_summary}

WORLD SETTING: {setting_prompt}

Design a scene that SERVES the structure beat:

BEAT REQUIREMENTS:
- 'hook': Show the BEFORE state, establish why character is [ADJECTIVE]
- 'plot_turn_1': The incident that FORCES hero into the story
- 'pinch_point_1': Stakes become REAL, first major pressure
- 'midpoint': The PIVOT from reaction to action
- 'pinch_point_2': DARKEST moment, all seems lost
- 'plot_turn_2': Final piece that ENABLES victory
- 'resolution': Show the AFTER state, transformation COMPLETE

This scene should clearly serve: {primary_beat}

The structure_connection field MUST be one of: hook, plot_turn_1, pinch_point_1, midpoint, pinch_point_2, plot_turn_2, resolution

Provide a proposal matching SceneProposal schema with methodology_focus='structure'."""

        return self.invoke_structured(prompt, SceneProposal, max_tokens=8000)

    def critique_proposal(
        self,
        target_agent: str,
        proposal: SceneProposal,
        chapter_context: dict,
    ) -> SceneCritique:
        """Critique from structure alignment perspective."""
        scene = proposal.scene
        beat_names = chapter_context.get("beats", [])

        prompt = f"""Critique this scene from a 7-POINT STRUCTURE perspective:

TARGET AGENT: {target_agent}
CHAPTER: {chapter_context.get('chapter_number', 1)}
TARGET BEAT(S): {', '.join(beat_names)}

PROPOSAL:
- Structure Connection: {scene.structure_connection}
- Scene Purpose: {scene.scene_purpose}
- What Happens: {scene.happens}
- Outcome: {scene.outcome}

Evaluate:
1. Does this scene clearly SERVE the target structure beat?
2. Does the scene accomplish the beat's PURPOSE?
3. Is the structure_connection accurate?
4. Does this advance the overall story structure?
5. Does it set up subsequent beats properly?

Provide a critique matching SceneCritique schema."""

        return self.invoke_structured(prompt, SceneCritique, max_tokens=8000)

    def vote_for_best(
        self,
        proposals: list[SceneProposal],
        chapter_context: dict,
    ) -> SceneVote:
        """Vote for best structure-aligned scene."""
        beat_names = chapter_context.get("beats", [])

        proposals_text = "\n\n".join([
            f"PROPOSAL by {p.agent_name}:\n"
            f"  Structure Connection: {p.scene.structure_connection}\n"
            f"  Scene Purpose: {p.scene.scene_purpose}\n"
            f"  Happens: {p.scene.happens[:80]}..."
            for p in proposals
        ])

        prompt = f"""Vote for the scene that best SERVES THE STRUCTURE.

CHAPTER: {chapter_context.get('chapter_number', 1)}
TARGET BEAT(S): {', '.join(beat_names)}

PROPOSALS:
{proposals_text}

Which proposal best serves the 7-point structure beat(s) for this chapter?
You CANNOT vote for your own proposal (SCENE_STRUCTURE).

Provide a vote matching SceneVote schema."""

        return self.invoke_structured(prompt, SceneVote, max_tokens=8000)
