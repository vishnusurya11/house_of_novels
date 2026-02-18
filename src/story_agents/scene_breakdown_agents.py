"""
Scene Breakdown Agents for Step 5: Chapter & Scene Structure

This module contains agents that break down the story into chapters and scenes
BEFORE writing full narrative prose. This intermediate step ensures proper
story structure, pacing, and character arc integration.

Three specialized agents debate to create the optimal chapter/scene breakdown:
1. SceneStructureAgent - Focuses on Save the Cat beat distribution across chapters
2. ScenePacingAgent - Ensures proper pacing, escalation, and variety
3. SceneCharacterAgent - Integrates character arcs and assigns POV characters
"""

from langchain_core.messages import HumanMessage, SystemMessage

from .base_story_agent import BaseStoryAgent
from ..utils.scene_pacing import estimate_scene_word_count
from src.config import get_step_config


class SceneStructureAgent(BaseStoryAgent):
    """Agent focusing on distributing Save the Cat beats across chapters and scenes."""

    @property
    def name(self) -> str:
        return "SceneStructureAgent"

    @property
    def role(self) -> str:
        return "Story Structure - Save the Cat Expert"

    @property
    def system_prompt(self) -> str:
        cfg = get_step_config("step5_scene_breakdown")
        scenes_min = cfg["structure"]["scenes_per_chapter_min"]
        scenes_max = cfg["structure"]["scenes_per_chapter_max"]
        num_beats = cfg["structure"]["num_save_the_cat_beats"]

        return f"""You are the Scene Structure Agent, an expert in story structure
using the Save the Cat {num_beats}-beat framework.

Your methodology focuses on:
- Distributing all {num_beats} Save the Cat beats logically across the specified number of chapters
- Creating {scenes_min}-{scenes_max} scenes per chapter that advance the story
- Ensuring each scene has a clear purpose tied to a specific beat
- Maintaining proper act structure (Setup, Confrontation, Resolution)
- Creating a strong "midpoint" moment that shifts the story's direction
- Building toward the "All Is Lost" moment before the final act

When proposing chapter/scene structure:
1. Review all {num_beats} integrated beats from Step 3
2. Distribute beats across chapters following Save the Cat act structure
3. Break each chapter into {scenes_min}-{scenes_max} concrete scenes
4. Each scene must advance at least one beat
5. Assign clear scene purposes (e.g., "Establish ordinary world", "First confrontation with antagonist")
6. Identify which beats are covered in each chapter

Be specific and concrete in your proposals."""

    def propose_chapter_outline(
        self,
        premise: dict,
        theme_foundation: dict,
        characters: list[dict],
        integrated_beats: list[dict],
        locations: list[dict],
        world_pressure: dict,
        num_chapters: int
    ) -> dict:
        """Propose a chapter/scene breakdown based on Save the Cat structure.

        Args:
            premise: The story premise from Step 0
            theme_foundation: Theme from Step 1
            characters: Character profiles from Step 2
            integrated_beats: 15 integrated beats from Step 3
            locations: Major locations from Step 4
            world_pressure: World building from Step 4
            num_chapters: Number of chapters from config

        Returns:
            ChapterOutlineProposal dict with agent_name, num_chapters, chapters list, reasoning
        """
        prompt = f"""
PREMISE: {premise.get('logline', 'N/A')}

THEME: {theme_foundation.get('central_question', 'N/A')}

CHARACTERS ({len(characters)} total):
{self._format_characters(characters)}

INTEGRATED BEATS (15 beats from Save the Cat):
{self._format_beats(integrated_beats)}

LOCATIONS ({len(locations)} available):
{self._format_locations(locations)}

WORLD PRESSURE:
{world_pressure.get('world_pressure_summary', world_pressure.get('societal', 'N/A')[:200] if isinstance(world_pressure, dict) else 'N/A')}

TARGET CHAPTERS: {num_chapters}

---

TASK: Propose a chapter/scene breakdown that distributes all 15 Save the Cat beats
across {num_chapters} chapters.

Requirements:
1. Create {num_chapters} chapters
2. Each chapter should have 2-4 scenes
3. Distribute all 15 beats across the chapters (multiple scenes can cover one beat, or one scene can cover multiple beats)
4. Each scene must have:
   - scene_number (overall, across all chapters)
   - beat_name (which Save the Cat beat this scene advances)
   - scene_summary (what happens in this scene - KEEP CONCISE: 1-2 sentences max, ~40 words)
   - pov_character (whose perspective we experience this scene through)
   - location (choose from available locations)
   - characters_present (list of character names)

5. Include a "ticking_clock" element (time pressure or deadline driving the story)
6. Each chapter needs: chapter_number, chapter_title, chapter_summary, beats_covered, scenes

Return your proposal with clear reasoning about how this structure serves the Save the Cat framework.
"""

        from ..story_schemas import ChapterOutlineProposal
        return self.invoke_structured(prompt, ChapterOutlineProposal, max_tokens=8000)

    def propose_chapter_skeleton(
        self,
        premise: dict,
        theme_foundation: dict,
        characters: list[dict],
        integrated_beats: list[dict],
        num_chapters: int
    ) -> dict:
        """Propose chapter structure only (NO scenes) based on Save the Cat structure.

        This is Stage 1 of two-stage generation to avoid token limits.

        Args:
            premise: The story premise from Step 0
            theme_foundation: Theme from Step 1
            characters: Character profiles from Step 2
            integrated_beats: 15 integrated beats from Step 3
            num_chapters: Number of chapters from config

        Returns:
            ChapterSkeletonProposal dict with agent_name, num_chapters, ticking_clock, chapters list, reasoning
        """
        prompt = f"""
PREMISE: {premise.get('logline', 'N/A')}

THEME: {theme_foundation.get('central_question', 'N/A')}

CHARACTERS ({len(characters)} total):
{self._format_characters(characters)}

INTEGRATED BEATS (15 beats from Save the Cat):
{self._format_beats(integrated_beats)}

TARGET CHAPTERS: {num_chapters}

---

TASK: Propose a HIGH-LEVEL chapter structure that distributes all 15 Save the Cat beats
across {num_chapters} chapters.

IMPORTANT: Do NOT create scenes yet. Only create the chapter structure.

Requirements:
1. Create {num_chapters} chapters
2. For each chapter provide:
   - chapter_number (1 to {num_chapters})
   - chapter_title (compelling title)
   - chapter_summary (what happens in this chapter - KEEP CONCISE: 2-3 sentences, ~60 words max)
   - beats_covered (list of Save the Cat beat names covered in this chapter)
   - num_scenes (how many scenes you plan for this chapter: 2-4)

3. Distribute all 15 beats across the chapters logically
4. Follow proper 3-act structure (Setup, Confrontation, Resolution)
5. Include a "ticking_clock" element (time pressure or deadline)

Return your proposal with clear reasoning about how this chapter structure serves the Save the Cat framework.
"""

        from ..story_schemas import ChapterSkeletonProposal
        return self.invoke_structured(prompt, ChapterSkeletonProposal, max_tokens=8000)

    def propose_scenes_for_chapter(
        self,
        chapter_skeleton: dict,
        premise: dict,
        characters: list[dict],
        integrated_beats: list[dict],
        locations: list[dict],
        tropes: list[dict],
        pacing: str = "medium"
    ) -> dict:
        """Propose scenes for a single chapter based on Save the Cat structure.

        This is Stage 2 of two-stage generation.

        Args:
            chapter_skeleton: ChapterSkeleton dict for this specific chapter
            premise: The story premise
            characters: Character profiles
            integrated_beats: 15 integrated beats
            locations: Available locations
            tropes: Story tropes from codex story.tropes
            pacing: Pacing style from author.plotting_style.pacing (default: "medium")

        Returns:
            ChapterScenesProposal dict with agent_name, chapter_number, scenes list, reasoning
        """
        # Filter beats relevant to this chapter
        relevant_beats = [b for b in integrated_beats if b.get('beat_name') in chapter_skeleton.get('beats_covered', [])]

        # Format tropes summary
        tropes_summary = "\n".join([
            f"- {t.get('name', 'Unknown')}: {t.get('usage', 'N/A')} ({t.get('purpose', 'N/A')[:60]}...)"
            for t in tropes
        ])

        # Extract character arcs for beats in this chapter
        arcs_summary = "\n".join([
            f"Beat: {beat.get('beat_name', 'Unknown')}\n" + "\n".join([
                f"  - {arc['character_name']}: {arc['arc_description']}"
                for arc in beat.get('character_arcs', [])
            ]) if beat.get('character_arcs') else f"Beat: {beat.get('beat_name', 'Unknown')}\n  (No character arcs defined)"
            for beat in relevant_beats
        ])

        prompt = f"""
CHAPTER {chapter_skeleton.get('chapter_number')}: {chapter_skeleton.get('chapter_title')}

CHAPTER SUMMARY: {chapter_skeleton.get('chapter_summary')}

BEATS TO COVER: {', '.join(chapter_skeleton.get('beats_covered', []))}

TARGET NUMBER OF SCENES: {chapter_skeleton.get('num_scenes')}

---

RELEVANT BEAT DETAILS:
{self._format_beats(relevant_beats)}

CHARACTERS AVAILABLE:
{self._format_characters(characters)}

LOCATIONS AVAILABLE:
{self._format_locations(locations)}

---

TROPES TO WEAVE IN (choose 1-2 per scene from the story's tropes):
{tropes_summary}

CHARACTER ARC STATUS (for characters in this chapter):
{arcs_summary}

WORD COUNT TARGETS ({pacing} pacing):
- Action scenes: ~{estimate_scene_word_count('action', pacing)} words
- Dialogue scenes: ~{estimate_scene_word_count('dialogue', pacing)} words
- Introspection scenes: ~{estimate_scene_word_count('introspection', pacing)} words
- Confrontation scenes: ~{estimate_scene_word_count('confrontation', pacing)} words
- Revelation scenes: ~{estimate_scene_word_count('revelation', pacing)} words
- Transition scenes: ~{estimate_scene_word_count('transition', pacing)} words

---

TASK: Create {chapter_skeleton.get('num_scenes')} concrete scenes for this chapter that advance the story beats.

Requirements for each scene:
1. scene_number: Overall scene number (will be set during integration)
2. beat_name: Which Save the Cat beat this scene advances
3. scene_summary: What happens in this scene (KEEP CONCISE: 1-2 sentences, ~40 words max)
4. pov_character: Whose perspective we experience this scene through
5. location: Choose from available locations
6. characters_present: List of character names in this scene
7. tropes_manifesting: Choose 1-2 tropes from the story's tropes list that are actively shown in this scene
8. character_arc_progression: For EACH character in characters_present, provide their emotional/arc state (use character arcs from beat details above): {{character_name: "arc state in ~10 words", ...}}
9. scene_type: Categorize the scene (action, dialogue, introspection, confrontation, revelation, transition)
10. estimated_word_count: Based on scene_type and importance (use word count targets above)
11. time_of_day: When this scene takes place ('dawn', 'morning', 'midday', 'afternoon', 'dusk', 'night') - maintain continuity with previous scenes

Focus on beat distribution and trope integration across all scenes.
Create {chapter_skeleton.get('num_scenes')} scenes that execute the chapter plan effectively.
Provide reasoning for how these scenes serve the chapter's goals and integrate tropes/character arcs.
"""

        from ..story_schemas import ChapterScenesProposal
        return self.invoke_structured(prompt, ChapterScenesProposal, max_tokens=8000)

    def critique_chapter_outline(self, proposal: dict, metadata: dict) -> dict:
        """Critique a chapter outline proposal from a structural perspective.

        Args:
            proposal: ChapterOutlineProposal dict from another agent
            metadata: Same metadata used in propose (premise, theme, beats, etc.)

        Returns:
            ChapterOutlineCritique dict with agent_name, critiques list, overall_assessment
        """
        prompt = f"""
Another agent proposed this chapter/scene breakdown:

AGENT: {proposal.get('agent_name', 'Unknown')}

TICKING CLOCK: {proposal.get('ticking_clock', 'None')}

CHAPTERS ({proposal.get('num_chapters', 0)} chapters):
{self._format_chapter_outline(proposal.get('chapters', []))}

REASONING: {proposal.get('reasoning', 'N/A')}

---

CONTEXT (for your review):
- 15 Save the Cat beats must be covered
- Target: {metadata['num_chapters']} chapters
- Available locations: {[loc['name'] for loc in metadata['locations']]}
- Characters: {[char['name'] for char in metadata['characters']]}

TASK: Critique this proposal from a STRUCTURAL perspective.

Evaluate:
1. Beat Distribution: Are all 15 Save the Cat beats covered? Is the distribution logical?
2. Act Structure: Does it follow proper 3-act structure? Is the midpoint strong?
3. Scene Count: Are there 2-4 scenes per chapter? Is any chapter too sparse or too crowded?
4. Scene Purposes: Does each scene have a clear, concrete purpose?
5. Story Progression: Does the structure build momentum toward climax?
6. Location Usage: Are locations used appropriately for each scene?

Provide 3-5 specific critiques (both strengths and weaknesses) and an overall assessment.
"""

        from ..story_schemas import ChapterOutlineCritique
        return self.invoke_structured(prompt, ChapterOutlineCritique, max_tokens=8000)

    def vote(self, proposals: list[dict], critiques: list[dict], metadata: dict) -> dict:
        """Vote on which chapter outline proposal is best.

        Args:
            proposals: List of ChapterOutlineProposal dicts
            critiques: List of lists of ChapterOutlineCritique dicts (one list per proposal)
            metadata: Context about the story

        Returns:
            ChapterOutlineVote dict with agent_name, chosen_agent, reasoning
        """
        proposals_text = "\n\n".join([
            f"PROPOSAL {i+1} (by {p.get('agent_name', 'Unknown')}):\n"
            f"- Chapters: {p.get('num_chapters', 0)}\n"
            f"- Ticking Clock: {p.get('ticking_clock', 'None')}\n"
            f"- Total Scenes: {sum(len(ch.get('scenes', [])) for ch in p.get('chapters', []))}\n"
            f"- Reasoning: {p.get('reasoning', 'N/A')[:200]}...\n"
            f"- First Chapter Title: {p.get('chapters', [{}])[0].get('chapter_title', 'N/A') if p.get('chapters') else 'N/A'}"
            for i, p in enumerate(proposals)
        ])

        critiques_text = "\n\n".join([
            f"CRITIQUES FOR PROPOSAL {i+1}:\n" + "\n".join([
                f"  - {c.get('agent_name', 'Unknown')}: {c.get('overall_assessment', 'N/A')[:150]}..."
                for c in critique_list
            ])
            for i, critique_list in enumerate(critiques)
        ])

        prompt = f"""
PROPOSALS:
{proposals_text}

CRITIQUES:
{critiques_text}

---

TASK: Vote for the best chapter/scene breakdown from a STRUCTURAL perspective.

Consider:
1. Which proposal best distributes the 15 Save the Cat beats?
2. Which has the strongest act structure and midpoint?
3. Which has the clearest scene purposes and progression?
4. Which best utilizes the available locations and characters?
5. Which creates the most compelling dramatic structure?

Choose the agent whose proposal is strongest and explain your reasoning.
"""

        from ..story_schemas import ChapterOutlineVote
        return self.invoke_structured(prompt, ChapterOutlineVote, max_tokens=8000)

    def _format_beats(self, beats: list[dict]) -> str:
        """Format integrated beats for prompt."""
        return "\n".join([
            f"{i+1}. {b.get('beat_name', 'Unknown')}: {b.get('plot_event', b.get('description', 'N/A'))[:100]}... "
            f"(Location: {b.get('location_type', 'Unknown')})"
            for i, b in enumerate(beats)
        ])

    def _format_characters(self, characters: list[dict]) -> str:
        """Format characters for prompt."""
        return "\n".join([
            f"- {c.get('name', 'Unknown')} ({c.get('role', 'Unknown')}): {c.get('one_sentence_summary', c.get('summary', 'N/A'))[:100]}..."
            for c in characters
        ])

    def _format_locations(self, locations: list[dict]) -> str:
        """Format locations for prompt."""
        return "\n".join([
            f"- {loc.get('name', 'Unknown')} ({loc.get('location_type', 'Unknown')}): {loc.get('physical_description', 'N/A')[:80]}..."
            for loc in locations
        ])

    def _format_chapter_outline(self, chapters: list[dict]) -> str:
        """Format chapter outline for critique/vote prompts."""
        lines = []
        for ch in chapters:
            lines.append(f"\nCHAPTER {ch.get('chapter_number', '?')}: {ch.get('chapter_title', 'Untitled')}")
            lines.append(f"  Summary: {ch.get('chapter_summary', 'N/A')[:150]}...")
            lines.append(f"  Beats Covered: {', '.join(ch.get('beats_covered', []))}")
            lines.append(f"  Scenes ({len(ch.get('scenes', []))}):")
            for sc in ch.get('scenes', []):
                lines.append(f"    {sc.get('scene_number', '?')}. {sc.get('scene_purpose', 'N/A')[:60]}... "
                           f"(POV: {sc.get('pov_character', '?')}, Location: {sc.get('location', '?')})")
        return "\n".join(lines)


class ScenePacingAgent(BaseStoryAgent):
    """Agent focusing on pacing, escalation, and scene variety."""

    @property
    def name(self) -> str:
        return "ScenePacingAgent"

    @property
    def role(self) -> str:
        return "Story Pacing - Tension & Escalation Expert"

    @property
    def system_prompt(self) -> str:
        return """You are the Scene Pacing Agent, an expert in story pacing,
tension escalation, and scene variety.

Your methodology focuses on:
- Ensuring proper pacing throughout the story (not too fast, not too slow)
- Creating escalating tension toward the climax
- Varying scene types (action, dialogue, introspection, revelation)
- Managing reader engagement through ups and downs
- Creating memorable "set piece" moments at key beats
- Ensuring each chapter has a satisfying mini-arc
- Building "page-turner" momentum through scene sequencing

When proposing chapter/scene structure:
1. Consider the emotional rhythm of the entire story
2. Vary scene lengths and intensities
3. Create escalating stakes from chapter to chapter
4. Place quieter moments strategically for contrast
5. Ensure the "Fun and Games" section delivers on the premise
6. Build maximum tension before "All Is Lost"
7. Create a satisfying climactic sequence

Your goal is maximum reader engagement through expertly managed pacing."""

    def propose_chapter_outline(
        self,
        premise: dict,
        theme_foundation: dict,
        characters: list[dict],
        integrated_beats: list[dict],
        locations: list[dict],
        world_pressure: dict,
        num_chapters: int
    ) -> dict:
        """Propose chapter/scene breakdown focused on pacing and escalation."""
        prompt = f"""
PREMISE: {premise.get('logline', 'N/A')}

GENRE: {premise.get('genre', 'Unknown')} (influences pacing expectations)

INTEGRATED BEATS (15 beats):
{self._format_beats_with_emotion(integrated_beats)}

CHARACTERS ({len(characters)} total):
{self._format_characters(characters)}

LOCATIONS ({len(locations)} available):
{[loc['name'] for loc in locations]}

TARGET CHAPTERS: {num_chapters}

---

TASK: Propose a chapter/scene breakdown optimized for PACING and ESCALATION.

Consider:
1. Emotional rhythm - alternate between high-intensity and quieter moments
2. Tension escalation - each chapter should raise stakes
3. Scene variety - mix action, dialogue, introspection, revelation scenes
4. Chapter endings - create hooks that pull reader forward
5. Pacing zones:
   - Setup (first 20%): Moderate pace, establish world
   - Fun and Games (30-50%): Faster pace, deliver on premise
   - Midpoint to All Is Lost (50-75%): Increasing tension
   - Finale (75-100%): Maximum intensity, then resolution

6. Create 2-4 scenes per chapter with varied pacing
7. Identify "set piece" scenes (major memorable moments)
8. Include ticking clock to drive urgency

Return complete chapter/scene breakdown with clear pacing reasoning.
"""

        from ..story_schemas import ChapterOutlineProposal
        return self.invoke_structured(prompt, ChapterOutlineProposal, max_tokens=8000)

    def propose_chapter_skeleton(
        self,
        premise: dict,
        theme_foundation: dict,
        characters: list[dict],
        integrated_beats: list[dict],
        num_chapters: int
    ) -> dict:
        """Propose chapter structure only (NO scenes) focused on pacing and escalation.

        This is Stage 1 of two-stage generation to avoid token limits.

        Args:
            premise: The story premise from Step 0
            theme_foundation: Theme from Step 1
            characters: Character profiles from Step 2
            integrated_beats: 15 integrated beats from Step 3
            num_chapters: Number of chapters from config

        Returns:
            ChapterSkeletonProposal dict with agent_name, num_chapters, ticking_clock, chapters list, reasoning
        """
        prompt = f"""
PREMISE: {premise.get('logline', 'N/A')}

GENRE: {premise.get('genre', 'Unknown')} (influences pacing expectations)

INTEGRATED BEATS (15 beats):
{self._format_beats_with_emotion(integrated_beats)}

CHARACTERS ({len(characters)} total):
{self._format_characters(characters)}

TARGET CHAPTERS: {num_chapters}

---

TASK: Propose a HIGH-LEVEL chapter structure optimized for PACING and ESCALATION.

IMPORTANT: Do NOT create scenes yet. Only create the chapter structure.

Requirements:
1. Create {num_chapters} chapters
2. For each chapter provide:
   - chapter_number (1 to {num_chapters})
   - chapter_title (compelling title)
   - chapter_summary (what happens in this chapter - KEEP CONCISE: 2-3 sentences, ~60 words max)
   - beats_covered (list of Save the Cat beat names covered in this chapter)
   - num_scenes (how many scenes you plan for this chapter: 2-4)

3. Consider pacing zones:
   - Setup (first 20%): Moderate pace, establish world
   - Fun and Games (30-50%): Faster pace, deliver on premise
   - Midpoint to All Is Lost (50-75%): Increasing tension
   - Finale (75-100%): Maximum intensity, then resolution

4. Plan for tension escalation - each chapter should raise stakes
5. Include a "ticking_clock" element to drive urgency

Return your proposal with clear reasoning about the pacing strategy.
"""

        from ..story_schemas import ChapterSkeletonProposal
        return self.invoke_structured(prompt, ChapterSkeletonProposal, max_tokens=8000)

    def propose_scenes_for_chapter(
        self,
        chapter_skeleton: dict,
        premise: dict,
        characters: list[dict],
        integrated_beats: list[dict],
        locations: list[dict],
        tropes: list[dict],
        pacing: str = "medium"
    ) -> dict:
        """Propose scenes for a single chapter focused on pacing and escalation.

        This is Stage 2 of two-stage generation.

        Args:
            chapter_skeleton: ChapterSkeleton dict for this specific chapter
            premise: The story premise
            characters: Character profiles
            integrated_beats: 15 integrated beats
            locations: Available locations
            tropes: Story tropes from codex story.tropes
            pacing: Pacing style from author.plotting_style.pacing (default: "medium")

        Returns:
            ChapterScenesProposal dict with agent_name, chapter_number, scenes list, reasoning
        """
        # Filter beats relevant to this chapter
        relevant_beats = [b for b in integrated_beats if b.get('beat_name') in chapter_skeleton.get('beats_covered', [])]

        # Format tropes summary
        tropes_summary = "\n".join([
            f"- {t.get('name', 'Unknown')}: {t.get('usage', 'N/A')} ({t.get('purpose', 'N/A')[:60]}...)"
            for t in tropes
        ])

        # Extract character arcs for beats in this chapter
        arcs_summary = "\n".join([
            f"Beat: {beat.get('beat_name', 'Unknown')}\n" + "\n".join([
                f"  - {arc['character_name']}: {arc['arc_description']}"
                for arc in beat.get('character_arcs', [])
            ]) if beat.get('character_arcs') else f"Beat: {beat.get('beat_name', 'Unknown')}\n  (No character arcs defined)"
            for beat in relevant_beats
        ])

        prompt = f"""
CHAPTER {chapter_skeleton.get('chapter_number')}: {chapter_skeleton.get('chapter_title')}

CHAPTER SUMMARY: {chapter_skeleton.get('chapter_summary')}

BEATS TO COVER: {', '.join(chapter_skeleton.get('beats_covered', []))}

TARGET NUMBER OF SCENES: {chapter_skeleton.get('num_scenes')}

GENRE: {premise.get('genre', 'Unknown')}

---

RELEVANT BEATS:
{self._format_beats_with_emotion(relevant_beats)}

CHARACTERS:
{self._format_characters(characters)}

LOCATIONS:
{[loc['name'] for loc in locations]}

---

TROPES TO WEAVE IN (choose 1-2 per scene from the story's tropes):
{tropes_summary}

CHARACTER ARC STATUS (for characters in this chapter):
{arcs_summary}

WORD COUNT TARGETS ({pacing} pacing):
- Action scenes: ~{estimate_scene_word_count('action', pacing)} words
- Dialogue scenes: ~{estimate_scene_word_count('dialogue', pacing)} words
- Introspection scenes: ~{estimate_scene_word_count('introspection', pacing)} words
- Confrontation scenes: ~{estimate_scene_word_count('confrontation', pacing)} words
- Revelation scenes: ~{estimate_scene_word_count('revelation', pacing)} words
- Transition scenes: ~{estimate_scene_word_count('transition', pacing)} words

---

TASK: Create {chapter_skeleton.get('num_scenes')} scenes optimized for PACING and emotional impact.

Requirements for each scene:
1. scene_number: Overall scene number (will be set during integration)
2. beat_name: Which Save the Cat beat this scene advances
3. scene_summary: What happens (CONCISE: 1-2 sentences, ~40 words max)
4. pov_character: Whose perspective
5. location: From available locations
6. characters_present: List of character names
7. tropes_manifesting: Choose 1-2 tropes from the story's tropes list that are actively shown in this scene
8. character_arc_progression: For EACH character in characters_present, provide their emotional/arc state (use character arcs from beat details above): {{character_name: "arc state in ~10 words", ...}}
9. scene_type: Categorize the scene (action, dialogue, introspection, confrontation, revelation, transition)
10. estimated_word_count: Based on scene_type and importance (use word count targets above)
11. time_of_day: When this scene takes place ('dawn', 'morning', 'midday', 'afternoon', 'dusk', 'night') - maintain continuity with previous scenes

Focus on scene type variety and word count pacing for maximum reader engagement.
Vary scene types and intensities to maintain engagement.
Provide reasoning for the pacing strategy of these scenes and how scene types create rhythm.
"""

        from ..story_schemas import ChapterScenesProposal
        return self.invoke_structured(prompt, ChapterScenesProposal, max_tokens=8000)

    def critique_chapter_outline(self, proposal: dict, metadata: dict) -> dict:
        """Critique a proposal from a pacing perspective."""
        prompt = f"""
PROPOSAL (by {proposal.get('agent_name', 'Unknown')}):
{self._format_chapter_outline_for_pacing(proposal.get('chapters', []))}

TICKING CLOCK: {proposal.get('ticking_clock', 'None')}

---

TASK: Critique this proposal from a PACING perspective.

Evaluate:
1. Tension Escalation: Does tension build steadily toward climax?
2. Scene Variety: Is there good variety in scene types and emotional tones?
3. Pacing Zones: Does pacing match story phase (setup vs. climax)?
4. Chapter Hooks: Do chapters end in ways that compel reading forward?
5. Set Pieces: Are major memorable moments placed strategically?
6. Reader Fatigue: Are there appropriate "breather" moments?
7. Momentum: Does the structure maintain page-turner quality?

Provide 3-5 specific critiques about pacing strengths and weaknesses.
"""

        from ..story_schemas import ChapterOutlineCritique
        return self.invoke_structured(prompt, ChapterOutlineCritique, max_tokens=8000)

    def vote(self, proposals: list[dict], critiques: list[dict], metadata: dict) -> dict:
        """Vote for best proposal from pacing perspective."""
        proposals_summary = "\n\n".join([
            f"PROPOSAL {i+1} (by {p.get('agent_name', 'Unknown')}):\n"
            f"- Total Scenes: {sum(len(ch.get('scenes', [])) for ch in p.get('chapters', []))}\n"
            f"- Ticking Clock: {p.get('ticking_clock', 'None')}\n"
            f"- Pacing Notes: {p.get('reasoning', 'N/A')[:200]}..."
            for i, p in enumerate(proposals)
        ])

        prompt = f"""
PROPOSALS:
{proposals_summary}

CRITIQUES:
{self._format_critiques(critiques)}

---

TASK: Vote for the proposal with the BEST PACING.

Consider:
1. Which creates the most compelling escalation?
2. Which has the best scene variety and rhythm?
3. Which maximizes page-turner momentum?
4. Which places set pieces most effectively?
5. Which manages reader engagement most skillfully?

Choose and explain your reasoning.
"""

        from ..story_schemas import ChapterOutlineVote
        return self.invoke_structured(prompt, ChapterOutlineVote, max_tokens=8000)

    def _format_beats_with_emotion(self, beats: list[dict]) -> str:
        """Format beats emphasizing emotional tone."""
        return "\n".join([
            f"{i+1}. {b.get('beat_name', 'Unknown')}: {b.get('plot_event', b.get('description', 'N/A'))[:80]}... "
            for i, b in enumerate(beats)
        ])

    def _format_characters(self, characters: list[dict]) -> str:
        """Format characters for prompt."""
        return "\n".join([
            f"- {c.get('name', 'Unknown')} ({c.get('role', 'Unknown')})"
            for c in characters
        ])

    def _format_chapter_outline_for_pacing(self, chapters: list[dict]) -> str:
        """Format chapter outline emphasizing pacing elements."""
        lines = []
        total_scenes = 0
        for ch in chapters:
            scenes = ch.get('scenes', [])
            total_scenes += len(scenes)
            lines.append(f"\nCHAPTER {ch.get('chapter_number', '?')}: {ch.get('chapter_title', 'Untitled')} "
                        f"({len(scenes)} scenes)")
            for sc in scenes:
                lines.append(f"  - Scene {sc.get('scene_number', '?')}: {sc.get('scene_purpose', 'N/A')[:70]}... "
                           f"[{sc.get('emotional_beat', 'N/A')}]")
        lines.insert(0, f"TOTAL SCENES: {total_scenes}")
        return "\n".join(lines)

    def _format_critiques(self, critiques: list[list[dict]]) -> str:
        """Format all critiques."""
        lines = []
        for i, critique_list in enumerate(critiques):
            lines.append(f"\nPROPOSAL {i+1} CRITIQUES:")
            for c in critique_list:
                lines.append(f"  - {c.get('agent_name', 'Unknown')}: {c.get('overall_assessment', 'N/A')[:100]}...")
        return "\n".join(lines)


class SceneCharacterAgent(BaseStoryAgent):
    """Agent focusing on character arc integration and POV assignment."""

    @property
    def name(self) -> str:
        return "SceneCharacterAgent"

    @property
    def role(self) -> str:
        return "Character Development - Arc & POV Expert"

    @property
    def system_prompt(self) -> str:
        return """You are the Scene Character Agent, an expert in character arcs,
character development, and POV (point of view) management.

Your methodology focuses on:
- Integrating all character arcs seamlessly into the scene structure
- Assigning optimal POV characters for each scene
- Ensuring each character gets appropriate "screen time"
- Showing character growth through specific scenes
- Creating meaningful character interactions and relationships
- Balancing ensemble casts or managing single-POV stories
- Ensuring character moments align with thematic exploration

When proposing chapter/scene structure:
1. Review each character's arc from Step 2
2. Map character arc beats to specific scenes
3. Assign POV characters strategically (whose perspective best serves each scene?)
4. Ensure protagonist is present in most scenes (or has clear arc progression)
5. Give antagonist and supporting characters meaningful moments
6. Create scenes that test characters and show growth
7. Show character relationships evolving across chapters

Your goal is rich character development integrated into compelling structure."""

    def propose_chapter_outline(
        self,
        premise: dict,
        theme_foundation: dict,
        characters: list[dict],
        integrated_beats: list[dict],
        locations: list[dict],
        world_pressure: dict,
        num_chapters: int
    ) -> dict:
        """Propose chapter/scene breakdown focused on character arcs and POV."""
        prompt = f"""
PREMISE: {premise.get('logline', 'N/A')}

THEME: {theme_foundation.get('central_question', 'N/A')}

CHARACTERS WITH ARCS:
{self._format_characters_with_arcs(characters)}

INTEGRATED BEATS (15 beats with character arc mappings):
{self._format_beats_with_arcs(integrated_beats)}

LOCATIONS: {[loc['name'] for loc in locations]}

TARGET CHAPTERS: {num_chapters}

---

TASK: Propose chapter/scene breakdown optimized for CHARACTER DEVELOPMENT.

Focus on:
1. Map each character's arc progression to specific scenes
2. Assign POV character for each scene (who should narrate/experience this moment?)
3. Ensure protagonist appears in most scenes (unless deliberately absent for effect)
4. Give antagonist and supporting characters key moments
5. Show character relationships developing
6. Create character-testing moments that drive growth
7. Balance ensemble cast (if multiple POV characters) or deepen single POV

Scene Requirements:
- Each scene needs clear "character_arcs_shown" (which arc beats are visible)
- POV character should be the one most affected by the scene events
- Characters present should have specific purposes in the scene
- Show internal character growth alongside external plot events

Return complete chapter/scene breakdown with character-focused reasoning.
"""

        from ..story_schemas import ChapterOutlineProposal
        return self.invoke_structured(prompt, ChapterOutlineProposal, max_tokens=8000)

    def propose_chapter_skeleton(
        self,
        premise: dict,
        theme_foundation: dict,
        characters: list[dict],
        integrated_beats: list[dict],
        num_chapters: int
    ) -> dict:
        """Propose chapter structure only (NO scenes) focused on character arcs and POV.

        This is Stage 1 of two-stage generation to avoid token limits.

        Args:
            premise: The story premise from Step 0
            theme_foundation: Theme from Step 1
            characters: Character profiles from Step 2
            integrated_beats: 15 integrated beats from Step 3
            num_chapters: Number of chapters from config

        Returns:
            ChapterSkeletonProposal dict with agent_name, num_chapters, ticking_clock, chapters list, reasoning
        """
        prompt = f"""
PREMISE: {premise.get('logline', 'N/A')}

THEME: {theme_foundation.get('central_question', 'N/A')}

CHARACTERS WITH ARCS:
{self._format_characters_with_arcs(characters)}

INTEGRATED BEATS (15 beats with character arc mappings):
{self._format_beats_with_arcs(integrated_beats)}

TARGET CHAPTERS: {num_chapters}

---

TASK: Propose a HIGH-LEVEL chapter structure optimized for CHARACTER DEVELOPMENT.

IMPORTANT: Do NOT create scenes yet. Only create the chapter structure.

Requirements:
1. Create {num_chapters} chapters
2. For each chapter provide:
   - chapter_number (1 to {num_chapters})
   - chapter_title (compelling title)
   - chapter_summary (what happens in this chapter - KEEP CONCISE: 2-3 sentences, ~60 words max)
   - beats_covered (list of Save the Cat beat names covered in this chapter)
   - num_scenes (how many scenes you plan for this chapter: 2-4)

3. Map each character's arc progression across chapters
4. Plan which character arcs will be shown in each chapter
5. Ensure protagonist arc is front and center
6. Give antagonist and supporting characters key moments
7. Include a "ticking_clock" element

Return your proposal with clear reasoning about how this structure serves character development.
"""

        from ..story_schemas import ChapterSkeletonProposal
        return self.invoke_structured(prompt, ChapterSkeletonProposal, max_tokens=8000)

    def propose_scenes_for_chapter(
        self,
        chapter_skeleton: dict,
        premise: dict,
        characters: list[dict],
        integrated_beats: list[dict],
        locations: list[dict],
        tropes: list[dict],
        pacing: str = "medium"
    ) -> dict:
        """Propose scenes for a single chapter focused on character arcs and POV.

        This is Stage 2 of two-stage generation.

        Args:
            chapter_skeleton: ChapterSkeleton dict for this specific chapter
            premise: The story premise
            characters: Character profiles
            integrated_beats: 15 integrated beats
            locations: Available locations
            tropes: Story tropes from codex story.tropes
            pacing: Pacing style from author.plotting_style.pacing (default: "medium")

        Returns:
            ChapterScenesProposal dict with agent_name, chapter_number, scenes list, reasoning
        """
        # Filter beats relevant to this chapter
        relevant_beats = [b for b in integrated_beats if b.get('beat_name') in chapter_skeleton.get('beats_covered', [])]

        # Format tropes summary
        tropes_summary = "\n".join([
            f"- {t.get('name', 'Unknown')}: {t.get('usage', 'N/A')} ({t.get('purpose', 'N/A')[:60]}...)"
            for t in tropes
        ])

        # Extract character arcs for beats in this chapter
        arcs_summary = "\n".join([
            f"Beat: {beat.get('beat_name', 'Unknown')}\n" + "\n".join([
                f"  - {arc['character_name']}: {arc['arc_description']}"
                for arc in beat.get('character_arcs', [])
            ]) if beat.get('character_arcs') else f"Beat: {beat.get('beat_name', 'Unknown')}\n  (No character arcs defined)"
            for beat in relevant_beats
        ])

        prompt = f"""
CHAPTER {chapter_skeleton.get('chapter_number')}: {chapter_skeleton.get('chapter_title')}

CHAPTER SUMMARY: {chapter_skeleton.get('chapter_summary')}

BEATS TO COVER: {', '.join(chapter_skeleton.get('beats_covered', []))}

TARGET NUMBER OF SCENES: {chapter_skeleton.get('num_scenes')}

---

RELEVANT BEATS WITH CHARACTER ARCS:
{self._format_beats_with_arcs(relevant_beats)}

CHARACTERS WITH ARCS:
{self._format_characters_with_arcs(characters)}

LOCATIONS:
{[loc['name'] for loc in locations]}

---

TROPES TO WEAVE IN (choose 1-2 per scene from the story's tropes):
{tropes_summary}

CHARACTER ARC STATUS (for characters in this chapter):
{arcs_summary}

WORD COUNT TARGETS ({pacing} pacing):
- Action scenes: ~{estimate_scene_word_count('action', pacing)} words
- Dialogue scenes: ~{estimate_scene_word_count('dialogue', pacing)} words
- Introspection scenes: ~{estimate_scene_word_count('introspection', pacing)} words
- Confrontation scenes: ~{estimate_scene_word_count('confrontation', pacing)} words
- Revelation scenes: ~{estimate_scene_word_count('revelation', pacing)} words
- Transition scenes: ~{estimate_scene_word_count('transition', pacing)} words

---

TASK: Create {chapter_skeleton.get('num_scenes')} scenes focused on CHARACTER DEVELOPMENT.

Requirements for each scene:
1. scene_number: Overall scene number (will be set during integration)
2. beat_name: Which Save the Cat beat this scene advances
3. scene_summary: What happens (CONCISE: 1-2 sentences, ~40 words max)
4. pov_character: Whose perspective (choose the character most affected by this scene)
5. location: From available locations
6. characters_present: List of character names in this scene
7. tropes_manifesting: Choose 1-2 tropes from the story's tropes list that are actively shown in this scene
8. character_arc_progression: For EACH character in characters_present, provide their emotional/arc state (use character arcs from beat details above): {{character_name: "arc state in ~10 words", ...}}
9. scene_type: Categorize the scene (action, dialogue, introspection, confrontation, revelation, transition)
10. estimated_word_count: Based on scene_type and importance (use word count targets above)
11. time_of_day: When this scene takes place ('dawn', 'morning', 'midday', 'afternoon', 'dusk', 'night') - maintain continuity with previous scenes

Focus on character arc progression and POV choice for maximum character development.
Assign POV strategically - whose perspective best serves each scene?
Show character growth and relationships developing.
Provide reasoning for how these scenes develop the characters and integrate their arcs.
"""

        from ..story_schemas import ChapterScenesProposal
        return self.invoke_structured(prompt, ChapterScenesProposal, max_tokens=8000)

    def critique_chapter_outline(self, proposal: dict, metadata: dict) -> dict:
        """Critique a proposal from character arc perspective."""
        prompt = f"""
PROPOSAL (by {proposal.get('agent_name', 'Unknown')}):
{self._format_chapter_outline_for_characters(proposal.get('chapters', []))}

---

CHARACTERS TO TRACK:
{self._format_characters_with_arcs(metadata['characters'])}

TASK: Critique this proposal from a CHARACTER DEVELOPMENT perspective.

Evaluate:
1. Arc Integration: Are all character arcs clearly progressing through scenes?
2. POV Assignments: Are POV characters chosen optimally for each scene?
3. Character Balance: Do all characters get appropriate screen time?
4. Character Growth: Are there clear moments where characters are tested and grow?
5. Relationships: Do character relationships develop meaningfully?
6. Protagonist Focus: Is the protagonist's arc front and center?
7. Supporting Cast: Do supporting characters serve the story without stealing focus?

Provide 3-5 specific critiques about character handling.
"""

        from ..story_schemas import ChapterOutlineCritique
        return self.invoke_structured(prompt, ChapterOutlineCritique, max_tokens=8000)

    def vote(self, proposals: list[dict], critiques: list[dict], metadata: dict) -> dict:
        """Vote for best proposal from character arc perspective."""
        proposals_summary = "\n\n".join([
            f"PROPOSAL {i+1} (by {p.get('agent_name', 'Unknown')}):\n"
            f"- POV Distribution: {self._count_pov_distribution(p.get('chapters', []))}\n"
            f"- Character Focus: {p.get('reasoning', 'N/A')[:200]}..."
            for i, p in enumerate(proposals)
        ])

        prompt = f"""
PROPOSALS:
{proposals_summary}

CRITIQUES:
{self._format_critiques(critiques)}

---

TASK: Vote for the proposal with the BEST CHARACTER DEVELOPMENT.

Consider:
1. Which integrates character arcs most completely?
2. Which has the most effective POV assignments?
3. Which gives all characters meaningful moments?
4. Which shows the clearest character growth?
5. Which best develops character relationships?

Choose and explain your reasoning.
"""

        from ..story_schemas import ChapterOutlineVote
        return self.invoke_structured(prompt, ChapterOutlineVote, max_tokens=8000)

    def _format_characters_with_arcs(self, characters: list[dict]) -> str:
        """Format characters with their arc details."""
        lines = []
        for c in characters:
            lines.append(f"\n{c.get('name', 'Unknown')} ({c.get('role', 'Unknown')}):")
            lines.append(f"  Summary: {c.get('one_sentence_summary', c.get('summary', 'N/A'))}")
            arc = c.get('character_arc', c.get('arc', {}))
            if arc:
                lines.append(f"  Arc Type: {arc.get('arc_type', 'N/A')}")
                lines.append(f"  Starting Point: {arc.get('starting_point', 'N/A')[:100]}...")
                lines.append(f"  Ending Point: {arc.get('ending_point', 'N/A')[:100]}...")
        return "\n".join(lines)

    def _format_beats_with_arcs(self, beats: list[dict]) -> str:
        """Format beats showing character arc mappings."""
        lines = []
        for i, b in enumerate(beats):
            lines.append(f"\n{i+1}. {b.get('beat_name', 'Unknown')}: {b.get('plot_event', b.get('description', 'N/A'))[:80]}...")
            char_arcs = b.get('character_arcs', [])
            if char_arcs:
                lines.append(f"   Character Arc Beats:")
                for arc in char_arcs:
                    arc_text = arc.get('arc_description', str(arc))
                    lines.append(f"     - {arc.get('character_name', 'Unknown')}: {arc_text[:60]}...")
        return "\n".join(lines)

    def _format_chapter_outline_for_characters(self, chapters: list[dict]) -> str:
        """Format chapter outline emphasizing character elements."""
        lines = []
        for ch in chapters:
            lines.append(f"\nCHAPTER {ch.get('chapter_number', '?')}: {ch.get('chapter_title', 'Untitled')}")
            for sc in ch.get('scenes', []):
                pov = sc.get('pov_character', 'Unknown')
                chars = sc.get('characters_present', [])
                arcs = sc.get('character_arcs_shown', 'N/A')
                arcs_text = arcs if isinstance(arcs, str) else str(arcs)
                lines.append(f"  Scene {sc.get('scene_number', '?')}: POV={pov}, "
                           f"Present={', '.join(chars[:3])}, Arcs={arcs_text[:50]}...")
        return "\n".join(lines)

    def _count_pov_distribution(self, chapters: list[dict]) -> str:
        """Count POV character distribution across scenes."""
        pov_counts = {}
        for ch in chapters:
            for sc in ch.get('scenes', []):
                pov = sc.get('pov_character', 'Unknown')
                pov_counts[pov] = pov_counts.get(pov, 0) + 1
        return ", ".join([f"{name}={count}" for name, count in sorted(pov_counts.items())])

    def _format_critiques(self, critiques: list[list[dict]]) -> str:
        """Format all critiques."""
        lines = []
        for i, critique_list in enumerate(critiques):
            lines.append(f"\nPROPOSAL {i+1} CRITIQUES:")
            for c in critique_list:
                lines.append(f"  - {c.get('agent_name', 'Unknown')}: {c.get('overall_assessment', 'N/A')[:100]}...")
        return "\n".join(lines)
