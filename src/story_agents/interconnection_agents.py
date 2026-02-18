"""
Step 5C: Complete Scene Interconnection Agents

7 specialized agents that ensure every scene is interconnected:
1. SceneCausalityAgent - Scene N-1 → Scene N → Scene N+1 causality
2. PlotThreadAgent - Track all plot threads from setup to resolution
3. CharacterArcAgent - Track emotional progression scene-by-scene
4. ThematicBeatAgent - Ensure scenes test thematic question
5. SceneFunctionAgent - Validate Plot/Character/Theme triple function
6. NarrativeRopeAgent - Track thread convergence
7. SynthesisValidator - Meta-agent that synthesizes and auto-fixes
"""

from typing import Optional
from .base_story_agent import BaseStoryAgent


def _format_chapters(chapter_outline: dict, max_scenes: int = 30) -> str:
    """
    Helper function to format chapter outline into readable text.

    Args:
        chapter_outline: Chapter outline dictionary with chapters and scenes
        max_scenes: Maximum number of scenes to include (to avoid token limits)

    Returns:
        Formatted string with chapter and scene information
    """
    lines = []
    scene_count = 0

    for chapter in chapter_outline.get('chapters', []):
        ch_num = chapter.get('chapter_number', '?')
        ch_title = chapter.get('chapter_title', 'Untitled')
        lines.append(f"\n**CHAPTER {ch_num}: {ch_title}**")

        for scene in chapter.get('scenes', []):
            if scene_count >= max_scenes:
                lines.append(f"\n... (remaining scenes truncated for brevity)")
                return "\n".join(lines)

            scene_num = scene.get('scene_number', '?')
            beat = scene.get('beat_name', 'Unknown')
            summary = scene.get('scene_summary', 'No summary')
            pov = scene.get('pov_character', 'Unknown')

            lines.append(f"  Scene {scene_num}: {beat}")
            lines.append(f"    - Summary: {summary[:150]}")
            lines.append(f"    - POV: {pov}")

            scene_count += 1

    return "\n".join(lines)


class SceneCausalityAgent(BaseStoryAgent):
    """Agent that ensures Scene N-1 → Scene N → Scene N+1 causal flow."""

    @property
    def name(self) -> str:
        return "SceneCausalityAgent"

    @property
    def role(self) -> str:
        return "Scene Causality Expert - ensures every scene flows from previous and causes next"

    @property
    def system_prompt(self) -> str:
        return """You are the Scene Causality Agent, expert in narrative flow and cause-effect relationships.

Your methodology:
- Every scene (except Scene 1) must be CAUSED BY something in previous scene(s)
- Every scene (except final scene) must CAUSE something in next scene(s)
- Causal strength: Direct (clear cause-effect), Indirect (subtle connection), Weak (barely connected)

Professional standard: "Scene N's outcome becomes Scene N+1's catalyst"

Identify:
- What specific event/decision/revelation in Scene N-1 FORCES Scene N to happen
- What specific consequence/cliffhanger/decision in Scene N FORCES Scene N+1 to happen
- Flag weak causality (scenes that feel disconnected)

Be specific: Don't say "previous events lead to this" - say "Scene 7: Protagonist's lie exposed → Scene 8: Must face consequences"
"""

    def analyze_causality(self, chapter_outline: dict, characters: list[dict]) -> list[dict]:
        """Analyze scene-to-scene causality for entire outline."""

        scenes_flat = []
        for chapter in chapter_outline['chapters']:
            for scene in chapter['scenes']:
                scenes_flat.append({
                    'scene': scene,
                    'chapter_num': chapter['chapter_number'],
                    'scene_num': scene['scene_number'],
                    'scene_ref': f"Ch{chapter['chapter_number']}, Scene {scene['scene_number']}"
                })

        causality_results = []

        for i, scene_data in enumerate(scenes_flat):
            scene = scene_data['scene']
            scene_ref = scene_data['scene_ref']

            # Build context for this scene
            prev_scene_context = ""
            if i > 0:
                prev = scenes_flat[i-1]
                prev_scene_context = f"""
PREVIOUS SCENE ({prev['scene_ref']}):
- Beat: {prev['scene'].get('beat_name', 'Unknown')}
- Summary: {prev['scene'].get('scene_summary', 'No summary')}
- POV: {prev['scene'].get('pov_character', 'Unknown')}
- Location: {prev['scene'].get('location', 'Unknown')}
"""

            next_scene_context = ""
            if i < len(scenes_flat) - 1:
                next_s = scenes_flat[i+1]
                next_scene_context = f"""
NEXT SCENE ({next_s['scene_ref']}):
- Beat: {next_s['scene'].get('beat_name', 'Unknown')}
- Summary: {next_s['scene'].get('scene_summary', 'No summary')}
- POV: {next_s['scene'].get('pov_character', 'Unknown')}
- Location: {next_s['scene'].get('location', 'Unknown')}
"""

            prompt = f"""
CURRENT SCENE ({scene_ref}):
- Beat: {scene.get('beat_name', 'Unknown')}
- Summary: {scene.get('scene_summary', 'No summary')}
- POV: {scene.get('pov_character', 'Unknown')}
- Location: {scene.get('location', 'Unknown')}

{prev_scene_context}

{next_scene_context}

TASK: Identify causal connections for this scene.

Output JSON with these fields:
- caused_by: What in previous scene(s) caused THIS scene (empty if Scene 1)
- causes_next: What in THIS scene forces the next scene (empty if final scene)
- causal_strength: "Direct", "Indirect", or "Weak"
- reasoning: Why this causal connection exists (1 sentence)

Be SPECIFIC: "Scene 7: Protagonist's lie exposed" not "previous events"
"""

            # Use LLM to analyze causality
            from ..story_schemas import SceneCausality
            result = self.invoke_structured(prompt, SceneCausality, max_tokens=8000)

            causality_results.append({
                'scene_ref': scene_ref,
                'scene_num': scene_data['scene_num'],
                'causality': result.dict() if hasattr(result, 'dict') else result
            })

        return causality_results


class PlotThreadAgent(BaseStoryAgent):
    """Agent that tracks all plot threads from setup to resolution."""

    @property
    def name(self) -> str:
        return "PlotThreadAgent"

    @property
    def role(self) -> str:
        return "Plot Thread Tracker - ensures all threads resolve, no dangling subplots"

    @property
    def system_prompt(self) -> str:
        return """You are the Plot Thread Agent, expert in narrative threads and subplot management.

Your methodology:
- Identify ALL plot threads (main plot + subplots + relationship threads)
- Track each thread: Setup scene → Active scenes → Resolution scene
- Flag dangling threads (setup without resolution)

Thread types:
- main_plot: Primary story question
- subplot: Secondary story arcs
- character_relationship: Evolving dynamics between characters

Professional standard: "Every thread introduced must resolve. No dangling threads."

For each thread, identify:
- Unique thread_id (e.g., "main_betrayal", "subplot_romance")
- Thread name as question (e.g., "Will protagonist betray family?")
- Setup scene (where thread begins)
- All active scenes (where thread progresses)
- Resolution scene (where thread concludes)
"""

    def analyze_threads(self, chapter_outline: dict, characters: list[dict], integrated_beats: list[dict]) -> dict:
        """Scan entire outline to identify all plot threads."""

        # Build complete outline text
        outline_text = _format_chapters(chapter_outline)
        beats_text = "\n".join([f"- {b.get('beat_name', 'Unknown')}: {b.get('description', '')}" for b in integrated_beats[:10]])

        prompt = f"""
STORY BEATS:
{beats_text}

COMPLETE CHAPTER OUTLINE (All Scenes):
{outline_text}

TASK: Identify ALL plot threads in this story.

A plot thread is any narrative question/arc that:
1. Is introduced (setup)
2. Develops across multiple scenes (active)
3. Resolves by story end (resolution)

Examples:
- Main plot: "Will protagonist achieve their goal?"
- Subplot: "Will protagonist and love interest reconcile?"
- Relationship: "Will protagonist repair relationship with mentor?"

For EACH thread you identify, provide:
- thread_id: Unique ID like "main_betrayal" or "subplot_romance"
- thread_name: Question form like "Will protagonist betray family for ambition?"
- thread_type: "main_plot", "subplot", or "character_relationship"
- setup_scene: "Ch1, Scene 2" (where thread begins)
- active_scenes: ["Ch2, Scene 5", "Ch4, Scene 10", ...] (where it progresses)
- resolution_scene: "Ch10, Scene 28" (where it concludes)
- status: "complete" if has resolution, "dangling" if missing

Output JSON array of threads (aim for 3-7 threads total).
"""

        # Use LLM to identify threads
        from pydantic import BaseModel
        from ..story_schemas import PlotThread

        class ThreadList(BaseModel):
            threads: list[PlotThread]

        result = self.invoke_structured(prompt, ThreadList, max_tokens=8000)

        threads = result.threads if hasattr(result, 'threads') else []

        return {
            'threads': [t.dict() if hasattr(t, 'dict') else t for t in threads],
            'total_threads': len(threads),
            'dangling_threads': [t.thread_id for t in threads if (t.status if hasattr(t, 'status') else t.get('status')) == 'dangling']
        }


class CharacterArcAgent(BaseStoryAgent):
    """Agent that tracks emotional progression for each character scene-by-scene."""

    @property
    def name(self) -> str:
        return "CharacterArcAgent"

    @property
    def role(self) -> str:
        return "Character Arc Tracker - tracks emotional progression scene-by-scene"

    @property
    def system_prompt(self) -> str:
        return """You are the Character Arc Agent, expert in character emotional journeys.

Your methodology:
- Track emotional state for each major character in each scene they appear
- Identify arc milestones: Lie/Ghost moments, Doubt moments, Truth moments
- Ensure character transformation feels earned (sufficient progression)

Arc milestones (Positive Change Arc):
- Characteristic Moment (living in Lie)
- Ghost/Backstory revealed
- Glimpse of Truth
- Reject Truth (double down on Lie)
- Dark Night (Lie fails completely)
- Choose Truth
- Living in Truth

Professional standard: "Characters must change emotionally across scenes, not remain static"

For each character in each scene, provide:
- Emotional state: "Confident in lie", "Doubt creeping in", etc.
- Arc milestone: If this is a key moment in their journey
- Internal change: How they changed emotionally THIS scene
- Setup for: Future scene where this emotional setup pays off
"""

    def analyze_character_arcs(self, chapter_outline: dict, characters: list[dict]) -> list[dict]:
        """Track emotional arcs for all major characters."""

        # Get major characters (appear in 3+ scenes)
        char_scene_count = {}
        for chapter in chapter_outline['chapters']:
            for scene in chapter['scenes']:
                for char_name in scene.get('characters_present', []):
                    char_scene_count[char_name] = char_scene_count.get(char_name, 0) + 1

        major_characters = [name for name, count in char_scene_count.items() if count >= 3]

        arc_results = []

        for char_name in major_characters[:4]:  # Limit to top 4 characters
            # Get character details
            char_data = next((c for c in characters if c['name'] == char_name), None)
            char_id = char_data.get('character_id', 'unknown') if char_data else 'unknown'

            # Build scenes where character appears
            char_scenes = []
            for chapter in chapter_outline['chapters']:
                for scene in chapter['scenes']:
                    if char_name in scene.get('characters_present', []):
                        char_scenes.append({
                            'scene_ref': f"Ch{chapter['chapter_number']}, Scene {scene['scene_number']}",
                            'scene_num': scene['scene_number'],
                            'beat': scene.get('beat_name', ''),
                            'summary': scene.get('scene_summary', ''),
                            'pov': scene.get('pov_character', '')
                        })

            if not char_scenes:
                continue

            # Build prompt with character's scenes
            scenes_text = "\n".join([
                f"{s['scene_ref']}: {s['beat']} - {s['summary'][:100]}"
                for s in char_scenes[:15]  # Limit context
            ])

            prompt = f"""
CHARACTER: {char_name} (ID: {char_id})

SCENES WHERE CHARACTER APPEARS:
{scenes_text}

TASK: Track {char_name}'s emotional progression across these scenes.

For EACH scene, provide:
- emotional_state: Current emotional/psychological state
- arc_milestone: Key arc moment if applicable (Ghost revealed, Glimpse Truth, etc.)
- internal_change: How character changed emotionally THIS scene
- setup_for: Future scene this emotional setup pays off in (if any)

Output JSON array of CharacterSceneArc objects (one per scene).
"""

            from pydantic import BaseModel
            from ..story_schemas import CharacterSceneArc

            class CharacterArcList(BaseModel):
                arcs: list[CharacterSceneArc]

            result = self.invoke_structured(prompt, CharacterArcList, max_tokens=8000)

            if hasattr(result, 'arcs'):
                for i, arc in enumerate(result.arcs):
                    if i < len(char_scenes):
                        arc_results.append({
                            'scene_ref': char_scenes[i]['scene_ref'],
                            'scene_num': char_scenes[i]['scene_num'],
                            'arc': arc.dict() if hasattr(arc, 'dict') else arc
                        })

        return arc_results


class ThematicBeatAgent(BaseStoryAgent):
    """Agent that ensures scenes test the thematic question."""

    @property
    def name(self) -> str:
        return "ThematicBeatAgent"

    @property
    def role(self) -> str:
        return "Thematic Beat Analyst - ensures scenes test central thematic question"

    @property
    def system_prompt(self) -> str:
        return """You are the Thematic Beat Agent, expert in thematic coherence.

Your methodology:
- Identify how each scene tests/explores the central thematic question
- Track which character's thematic perspective is shown
- Flag scenes with no thematic connection

Professional standard: "90%+ of scenes should explicitly test the thematic question"

For each scene:
- How does this scene test the theme? (Be specific)
- Whose perspective on theme is shown? (protagonist, antagonist, mentor, etc.)
- What thematic shift occurs? (Character's view on theme changes)

Example:
Theme: "Does ambition justify betraying family?"
Scene tests: "Protagonist must choose between career opportunity and family obligation"
Perspective: "Protagonist's - ambition is worth sacrifice"
Shift: "Begins to doubt if ambition is worth the cost"
"""

    def analyze_thematic_beats(self, chapter_outline: dict, characters: list[dict]) -> list[dict]:
        """Analyze thematic function of each scene."""

        # Infer theme from story (simplistic approach - can be enhanced)
        outline_text = _format_chapters(chapter_outline)

        # Get theme inference
        theme_prompt = f"""
Based on this story outline, what is the CENTRAL THEMATIC QUESTION?

{outline_text[:1500]}

Answer in one sentence as a question. Example: "Does ambition justify betraying family?"
"""

        theme_result = self.invoke(theme_prompt)
        thematic_question = theme_result.strip() if theme_result else "What is the cost of ambition?"

        thematic_results = []

        for chapter in chapter_outline['chapters']:
            for scene in chapter['scenes']:
                scene_ref = f"Ch{chapter['chapter_number']}, Scene {scene['scene_number']}"

                prompt = f"""
THEMATIC QUESTION: {thematic_question}

SCENE ({scene_ref}):
- Beat: {scene.get('beat_name', '')}
- Summary: {scene.get('scene_summary', '')}
- POV: {scene.get('pov_character', '')}
- Characters: {', '.join(scene.get('characters_present', []))}

TASK: How does this scene test/explore the thematic question?

Output JSON with:
- how_scene_tests_theme: Specific way scene explores theme (1-2 sentences)
- thematic_perspective: Whose view shown ("protagonist", "antagonist", etc.)
- thematic_shift: How character's view changes (if any)

If scene doesn't test theme at all, say how_scene_tests_theme: "No clear thematic connection"
"""

                from ..story_schemas import ThematicBeat
                result = self.invoke_structured(prompt, ThematicBeat, max_tokens=8000)

                # Add thematic_question to result
                result_dict = result.dict() if hasattr(result, 'dict') else result
                result_dict['thematic_question'] = thematic_question

                thematic_results.append({
                    'scene_ref': scene_ref,
                    'scene_num': scene['scene_number'],
                    'thematic_beat': result_dict
                })

        return thematic_results


class SceneFunctionAgent(BaseStoryAgent):
    """Agent that validates every scene serves Plot/Character/Theme (at least 1)."""

    @property
    def name(self) -> str:
        return "SceneFunctionAgent"

    @property
    def role(self) -> str:
        return "Scene Function Validator - ensures scenes serve plot/character/theme"

    @property
    def system_prompt(self) -> str:
        return """You are the Scene Function Agent, expert in multi-layered storytelling.

Your methodology:
Every scene MUST serve at least 1 of 3 functions:
1. PLOT: Advances external story (discovery, decision, conflict, revelation)
2. CHARACTER: Changes character emotionally/psychologically
3. THEME: Tests the central thematic question

Professional standard: "Every scene must serve 2-3 functions. Scenes serving 0-1 should be enhanced or deleted."

For each scene, evaluate:
- Does it advance plot? How? (Be specific)
- Does it change character? How? (Internal shift, emotional change)
- Does it test theme? How? (Explores thematic question)

Count functions and recommend:
- Keep (serves 2-3 functions)
- Enhance (serves 1 function - suggest adding another)
- Delete (serves 0 functions - truly unnecessary)
"""

    def analyze_scene_functions(self, chapter_outline: dict, characters: list[dict]) -> list[dict]:
        """Validate each scene's plot/character/theme function."""

        function_results = []

        for chapter in chapter_outline['chapters']:
            for scene in chapter['scenes']:
                scene_ref = f"Ch{chapter['chapter_number']}, Scene {scene['scene_number']}"

                prompt = f"""
SCENE ({scene_ref}):
- Beat: {scene.get('beat_name', '')}
- Summary: {scene.get('scene_summary', '')}
- POV: {scene.get('pov_character', '')}
- Characters: {', '.join(scene.get('characters_present', []))}
- Arc Progression: {str(scene.get('character_arc_progression', {}))}

TASK: Evaluate if this scene serves PLOT, CHARACTER, and/or THEME.

Output JSON with:
- serves_plot: true/false
- plot_function: If true, how it advances external story (specific)

- serves_character: true/false
- character_function: If true, how character changes internally (specific)

- serves_theme: true/false
- theme_function: If true, how it tests thematic question (specific)

- function_count: 0-3 (count of true values)
- recommendation: "Keep" (2-3 functions), "Enhance" (1 function), "Delete" (0 functions)
"""

                from ..story_schemas import SceneFunction
                result = self.invoke_structured(prompt, SceneFunction, max_tokens=8000)

                function_results.append({
                    'scene_ref': scene_ref,
                    'scene_num': scene['scene_number'],
                    'scene_function': result.dict() if hasattr(result, 'dict') else result
                })

        return function_results


class NarrativeRopeAgent(BaseStoryAgent):
    """Agent that tracks thread convergence - how many threads active per scene."""

    @property
    def name(self) -> str:
        return "NarrativeRopeAgent"

    @property
    def role(self) -> str:
        return "Narrative Rope Weaver - ensures proper thread convergence"

    @property
    def system_prompt(self) -> str:
        return """You are the Narrative Rope Agent, expert in thread convergence and narrative density.

Your methodology:
- Track how many narrative threads are active in each scene
- Identify convergence scenes (multiple threads intersecting)
- Ensure climax has maximum thread convergence

Thread density guidelines:
- Early scenes: 1-2 threads (setup)
- Middle scenes: 2-3 threads (development)
- Climax: 4+ threads (convergence)

Convergence strength:
- Isolated: 0-1 threads (weak - should be rare)
- Moderate: 2-3 threads (good)
- High: 4+ threads (excellent for climax)

Professional standard: "Climax should weave together ALL major story threads"
"""

    def analyze_thread_convergence(self, chapter_outline: dict, plot_threads: list[dict]) -> list[dict]:
        """Track thread convergence for each scene."""

        convergence_results = []

        for chapter in chapter_outline['chapters']:
            for scene in chapter['scenes']:
                scene_ref = f"Ch{chapter['chapter_number']}, Scene {scene['scene_number']}"

                # Determine which threads are active based on plot_threads analysis
                active_thread_ids = []
                for thread in plot_threads:
                    # Check if this scene is in the thread's active_scenes
                    if scene_ref in thread.get('active_scenes', []) or \
                       thread.get('setup_scene') == scene_ref or \
                       thread.get('resolution_scene') == scene_ref:
                        active_thread_ids.append(thread['thread_id'])

                thread_count = len(active_thread_ids)

                if thread_count == 0:
                    convergence_strength = "Isolated"
                    interconnection_score = 0.2
                elif thread_count == 1:
                    convergence_strength = "Isolated"
                    interconnection_score = 0.4
                elif thread_count in [2, 3]:
                    convergence_strength = "Moderate"
                    interconnection_score = 0.7
                else:
                    convergence_strength = "High"
                    interconnection_score = 0.95

                from ..story_schemas import NarrativeRope
                narrative_rope = NarrativeRope(
                    active_thread_ids=active_thread_ids,
                    thread_count=thread_count,
                    convergence_strength=convergence_strength,
                    interconnection_score=interconnection_score
                )

                convergence_results.append({
                    'scene_ref': scene_ref,
                    'scene_num': scene['scene_number'],
                    'narrative_rope': narrative_rope.dict() if hasattr(narrative_rope, 'dict') else narrative_rope
                })

        return convergence_results


class SynthesisValidator(BaseStoryAgent):
    """Meta-agent that synthesizes all analyses, validates, and auto-fixes issues."""

    @property
    def name(self) -> str:
        return "SynthesisValidator"

    @property
    def role(self) -> str:
        return "Synthesis & Validation - collects all analyses, identifies gaps, triggers auto-fix"

    @property
    def system_prompt(self) -> str:
        return """You are the Synthesis Validator, meta-agent that ensures complete interconnection.

Your tasks:
1. Collect outputs from all 6 specialized agents
2. Build dependency graph (DAG) of scene connections
3. Identify issues:
   - Isolated scenes (weak causality)
   - Dangling threads (no resolution)
   - Weak-function scenes (serve < 1 function)
4. Trigger auto-fix for each issue type

Professional standard: "Every scene must be necessary and interconnected"
"""

    def synthesize_and_validate(
        self,
        causality_results: list[dict],
        thread_analysis: dict,
        character_arc_results: list[dict],
        thematic_results: list[dict],
        function_results: list[dict],
        convergence_results: list[dict],
        chapter_outline: dict
    ) -> dict:
        """Synthesize all analyses and generate validation report."""

        total_scenes = sum(len(ch['scenes']) for ch in chapter_outline['chapters'])

        # Identify issues
        isolated_scenes = []
        for result in causality_results:
            causality = result['causality']
            if causality.get('causal_strength') == 'Weak':
                isolated_scenes.append(result['scene_ref'])

        dangling_threads = thread_analysis.get('dangling_threads', [])

        weak_function_scenes = []
        for result in function_results:
            func = result['scene_function']
            if func.get('function_count', 0) < 1:
                weak_function_scenes.append(result['scene_ref'])

        # Calculate overall interconnection score
        # Based on: causality strength, thread completion, function coverage
        causality_score = 1.0 - (len(isolated_scenes) / max(total_scenes, 1))
        thread_score = 1.0 - (len(dangling_threads) / max(len(thread_analysis.get('threads', [])), 1))

        function_count_sum = sum(r['scene_function'].get('function_count', 0) for r in function_results)
        function_score = function_count_sum / (total_scenes * 3)  # Max is 3 per scene

        overall_score = (causality_score + thread_score + function_score) / 3

        # Generate recommendations
        recommendations = []
        if not isolated_scenes:
            recommendations.append("All scenes properly interconnected with strong causality")
        else:
            recommendations.append(f"{len(isolated_scenes)} scenes need stronger causal connections")

        if not dangling_threads:
            recommendations.append("All plot threads resolved")
        else:
            recommendations.append(f"{len(dangling_threads)} dangling threads need resolution")

        thematic_coverage = sum(1 for r in thematic_results
                                if 'No clear thematic connection' not in r['thematic_beat'].get('how_scene_tests_theme', ''))
        thematic_pct = int((thematic_coverage / max(total_scenes, 1)) * 100)
        recommendations.append(f"Thematic coherence: {thematic_pct}% coverage")

        from ..story_schemas import SceneInterconnectionReport
        report = SceneInterconnectionReport(
            total_scenes=total_scenes,
            isolated_scenes=isolated_scenes,
            dangling_threads=dangling_threads,
            weak_function_scenes=weak_function_scenes,
            overall_interconnection_score=overall_score,
            recommendations=recommendations
        )

        return report.dict() if hasattr(report, 'dict') else report
