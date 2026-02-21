"""
Foreshadowing Agents for Step 5B: Setup/Payoff & Rule of Three Analysis

This module contains agents that analyze the chapter/scene breakdown to identify
payoff moments requiring setup, and ensure the Rule of Three is followed for
character traits, skills, and story elements.

Three specialized agents debate to create optimal setup/payoff tracking:
1. SetupPayoffAgent - Chekhov's Gun expert, ensures all payoffs have setup
2. RuleOfThreeAgent - Ensures 3x establishment before major payoffs
3. TropeExecutionAgent - Tracks trope execution timelines (especially subvert/invert)
"""

from langchain_core.messages import HumanMessage, SystemMessage

from .base_story_agent import BaseStoryAgent


class SetupPayoffAgent(BaseStoryAgent):
    """Agent focusing on Chekhov's Gun - ensuring all payoffs have proper setup."""

    @property
    def name(self) -> str:
        return "SetupPayoffAgent"

    @property
    def role(self) -> str:
        return "Chekhov's Gun - Setup & Payoff Expert"

    @property
    def system_prompt(self) -> str:
        return """You are the Setup & Payoff Agent, expert in Chekhov's Gun principle.

Your methodology focuses on:
- Scanning later chapters (Ch7+) for payoff moments requiring setup
- Working backward to identify where setups should exist
- Checking if existing scenes already provide setup (annotate them)
- Proposing new setup scenes where gaps exist
- Following the Rule of Three: skills/traits need 3x establishment before payoff

Payoff types to look for:
- Character skills used to solve problems (lockpicking, hacking, combat)
- Character traits that drive climactic decisions (compassion, ruthlessness)
- Plot elements revealed or used (artifacts, secrets, relationships)
- Trope executions that culminate (subversion reveals, inversion payoffs)

For each payoff:
1. Identify 2-3 setup moments (Rule of Three)
2. Check if existing scenes already cover some setups
3. Propose new setup scenes only where truly needed
4. Ensure setups are spaced naturally (not all in one chapter)
5. Make setups feel organic to the story, not forced

Be specific and concrete in your proposals."""

    def analyze_foreshadowing(
        self,
        chapter_outline: dict,
        characters: list[dict],
        integrated_beats: list[dict],
        tropes: list[dict]
    ) -> dict:
        """Analyze the chapter outline for setup/payoff opportunities.

        Args:
            chapter_outline: The complete chapter/scene breakdown from Step 5
            characters: Character profiles with arcs
            integrated_beats: 15 integrated beats
            tropes: Story tropes with usage (straight/subvert/invert)

        Returns:
            ForeshadowingMap with payoff_items and existing_scene_annotations
        """
        # Format chapters for analysis
        chapters_text = self._format_chapters(chapter_outline)
        characters_text = self._format_characters(characters)
        beats_text = self._format_beats(integrated_beats)
        tropes_text = self._format_tropes(tropes)

        prompt = f"""
CHAPTER OUTLINE ({chapter_outline.get('num_chapters', 0)} chapters):
{chapters_text}

CHARACTERS:
{characters_text}

INTEGRATED BEATS:
{beats_text}

TROPES:
{tropes_text}

---

CRITICAL RULE: Everything introduced must pay off. Track using unique tracking_id.

TRACKING_ID SYSTEM:
- Generate unique ID for each element: "family_loyalty_001", "lockpicking_skill_001", "curfew_law_001"
- Use SAME tracking_id for all scenes in chain (1 of 3, 2 of 3, 3 of 3)
- payoff_scene: Fill in setups (1 of 3, 2 of 3), leave empty in payoff (3 of 3)
- emotional_stake MUST escalate: "Low" → "Medium" → "High"
- demonstrates_how NEVER "Through dialogue" - only action/consequence/observation

TASK: Scan chapters 7+ for PAYOFF moments, work backward to find/create 2 setups.

For EXISTING scenes, provide SetupPayoffTracking objects with ALL required fields:
- tracking_id (REQUIRED): unique ID linking the chain
- trait_or_element (REQUIRED): what's being tracked
- position (REQUIRED): "1 of 3", "2 of 3", or "3 of 3"
- setup_type (REQUIRED): character_skill, character_trait, plot_element, trope_hint, world_rule
- payoff_scene: scene reference (filled in 1 of 3, 2 of 3; empty in 3 of 3)
- character_id, character_name: if applicable
- demonstrates_how: "Through action", "Through consequence", "Through observation"
- emotional_stake: "Low" (1 of 3), "Medium" (2 of 3), "High" (3 of 3)
- subtlety_level: "Subtle", "Moderate", "Obvious"

Track EVERYTHING readers need to notice: skills, traits, world rules, relationships, objects, secrets.

Aim for 5-10 priority elements with complete chains.

IMPORTANT: Provide a 'reasoning' field explaining your foreshadowing strategy.
"""

        from ..story_schemas import ForeshadowingMap
        return self.invoke_structured(prompt, ForeshadowingMap, max_tokens=8000)

    def critique_foreshadowing(self, analysis: dict, metadata: dict) -> dict:
        """Critique another agent's foreshadowing map.

        Args:
            analysis: Another agent's ForeshadowingMap
            metadata: Additional context (chapter_outline, etc.)

        Returns:
            ForeshadowingCritique with specific feedback
        """
        prompt = f"""
FORESHADOWING ANALYSIS TO CRITIQUE:
Agent: {analysis['agent_name']}

Payoff Items ({len(analysis.get('payoff_items', []))}):
{self._format_payoff_items(analysis.get('payoff_items', []))}

Existing Scene Annotations ({len(analysis.get('existing_scene_annotations', []))}):
{self._format_annotations(analysis.get('existing_scene_annotations', []))}

Reasoning: {analysis.get('reasoning', 'N/A')}

---

TASK: Critique this foreshadowing analysis from a Chekhov's Gun perspective.

Evaluate:
1. TIMING - Are setups too close to payoffs? Too clustered?
2. OVERCROWDING - Too many setups in one chapter? Feels forced?
3. MISSED OPPORTUNITIES - Critical payoffs lacking setup?
4. RULE OF THREE - Are major skills/traits established 3x before payoff?
5. NATURALNESS - Do setups feel organic or shoehorned?

Provide 3-5 specific critiques (both strengths and weaknesses).
Identify which payoff scenes are ESSENTIAL (must have proper setup).
Give an overall assessment.
"""

        from ..story_schemas import ForeshadowingCritique
        return self.invoke_structured(prompt, ForeshadowingCritique, max_tokens=8000)

    def vote_on_priorities(self, analyses: list[dict], critiques: list[dict]) -> dict:
        """Vote on which payoffs are essential vs nice-to-have.

        Args:
            analyses: All agents' ForeshadowingMaps
            critiques: All critiques

        Returns:
            ForeshadowingVote with essential_payoffs list
        """
        analyses_text = self._format_all_analyses(analyses)
        critiques_text = self._format_all_critiques(critiques)

        prompt = f"""
ALL FORESHADOWING ANALYSES:
{analyses_text}

ALL CRITIQUES:
{critiques_text}

---

TASK: Vote on which payoff items are ESSENTIAL vs NICE-TO-HAVE.

Essential payoffs (pick 5-8):
- Climactic moments requiring proper setup
- Character skills/traits critical to story resolution
- Plot reveals that must be foreshadowed
- Trope subversions/inversions needing establishment

Nice-to-have payoffs:
- Minor character moments
- Optional world-building details
- Secondary plot threads

Provide your vote with reasoning.
"""

        from ..story_schemas import ForeshadowingVote
        return self.invoke_structured(prompt, ForeshadowingVote, max_tokens=8000)

    # Helper methods
    def _format_chapters(self, outline: dict) -> str:
        lines = []
        for chapter in outline.get('chapters', []):
            lines.append(f"\nCh{chapter['chapter_number']}: {chapter['chapter_title']}")
            lines.append(f"  Summary: {chapter.get('chapter_summary', 'N/A')}")
            lines.append(f"  Beats: {', '.join(chapter.get('beats_covered', []))}")
            lines.append(f"  Scenes ({len(chapter.get('scenes', []))}):")
            for scene in chapter.get('scenes', []):
                lines.append(f"    Scene {scene['scene_number']}: {scene.get('scene_summary', 'N/A')[:100]}")
                lines.append(f"      Beat: {scene.get('beat_name', 'N/A')}, POV: {scene.get('pov_character', 'N/A')}")
        return '\n'.join(lines)

    def _format_characters(self, characters: list) -> str:
        lines = []
        for char in characters[:5]:  # Limit to avoid token bloat
            name = char.get('name', 'Unknown')
            role = char.get('role', 'N/A')
            arc = char.get('character_arc', {})
            lines.append(f"- {name} ({role})")
            if isinstance(arc, dict):
                lines.append(f"  Arc: {arc.get('lie_or_flaw', 'N/A')[:80]}")
        return '\n'.join(lines)

    def _format_beats(self, beats: list) -> str:
        lines = []
        for beat in beats:
            lines.append(f"- {beat.get('beat_name', 'N/A')}: {beat.get('description', 'N/A')[:80]}")
        return '\n'.join(lines[:15])  # Limit to 15

    def _format_tropes(self, tropes: list) -> str:
        lines = []
        for trope in tropes[:8]:  # Limit
            name = trope.get('trope_name', 'N/A')
            usage = trope.get('usage', 'N/A')
            lines.append(f"- {name} ({usage})")
        return '\n'.join(lines)

    def _format_payoff_items(self, items: list) -> str:
        lines = []
        for item in items:
            lines.append(f"- {item.get('payoff_scene', 'N/A')}: {item.get('payoff_description', 'N/A')[:80]}")
            lines.append(f"  Setups needed: {len(item.get('required_setups', []))}")
        return '\n'.join(lines)

    def _format_annotations(self, annotations: list) -> str:
        lines = []
        for ann in annotations:
            lines.append(f"- {ann.get('scene_reference', 'N/A')}: {ann.get('reasoning', 'N/A')[:80]}")
        return '\n'.join(lines)

    def _format_all_analyses(self, analyses: list) -> str:
        lines = []
        for analysis in analyses:
            lines.append(f"\n{analysis.get('agent_name', 'Unknown')}:")
            lines.append(f"  Payoffs: {len(analysis.get('payoff_items', []))}")
            lines.append(f"  Annotations: {len(analysis.get('existing_scene_annotations', []))}")
            lines.append(f"  Reasoning: {analysis.get('reasoning', 'N/A')[:100]}")
        return '\n'.join(lines)

    def _format_all_critiques(self, critiques: list) -> str:
        lines = []
        for critique in critiques:
            lines.append(f"\n{critique.get('agent_name', 'Unknown')} → {critique.get('target_agent', 'Unknown')}:")
            for c in critique.get('critiques', [])[:3]:
                lines.append(f"  - {c[:80]}")
        return '\n'.join(lines)


class RuleOfThreeAgent(BaseStoryAgent):
    """Agent focusing on Rule of Three - ensuring 3x establishment before payoff."""

    @property
    def name(self) -> str:
        return "RuleOfThreeAgent"

    @property
    def role(self) -> str:
        return "Rule of Three - Pattern Recognition Expert"

    @property
    def system_prompt(self) -> str:
        return """You are the Rule of Three Agent, expert in narrative pattern recognition.

Your methodology focuses on:
- Identifying skills/traits that need 3x establishment before payoff
- Ensuring repetition feels natural, not mechanical
- Varying the context of each establishment (show growth/escalation)
- Spacing establishments across the story (not clustered)

The Rule of Three applies to:
- Character skills (lockpicking shown 3x before critical use)
- Character traits (compassion shown 3x before defining choice)
- Physical objects (gun mentioned 3x before it fires)
- Recurring motifs (symbol appears 3x before final meaning)
- Character relationships (tension shown 3x before confrontation)

Each establishment should:
1. Show the skill/trait in different contexts
2. Escalate in stakes or complexity
3. Feel organic to the scene, not forced
4. Be memorable to the reader

For major climactic payoffs, strictly enforce 3x prior establishment.
For minor payoffs, 2x may suffice.

Be specific about HOW each establishment differs from the others."""

    def analyze_foreshadowing(
        self,
        chapter_outline: dict,
        characters: list[dict],
        integrated_beats: list[dict],
        tropes: list[dict]
    ) -> dict:
        """Analyze for Rule of Three patterns."""
        chapters_text = self._format_chapters(chapter_outline)
        characters_text = self._format_characters(characters)

        prompt = f"""
CHAPTER OUTLINE:
{chapters_text}

CHARACTERS:
{characters_text}

---

CRITICAL: You MUST include a 'reasoning' field at the top level of your response. This field should contain 2-3 sentences explaining your Rule of Three strategy and how you're ensuring proper repetition patterns.

TASK: Analyze this outline through the lens of the Rule of Three.

Focus on:
1. Character skills that appear in climactic moments (Ch7+)
   - Does the skill appear 3x before critical use?
   - Are the 3 establishments varied (different contexts/stakes)?

2. Character traits that drive key decisions
   - Is the trait demonstrated 3x before defining choice?
   - Do the 3 demonstrations escalate in impact?

3. Physical objects/tools used in climax
   - Is the object mentioned/shown 3x before critical use?
   - Are the 3 mentions spaced naturally?

4. Recurring motifs/symbols
   - Does the motif appear 3x before final revelation?

TRACKING_ID SYSTEM:
- Generate unique ID: "element_type_001"
- Use SAME tracking_id across all 3 scenes (1 of 3, 2 of 3, 3 of 3)
- payoff_scene: Fill in setups (1 of 3, 2 of 3), empty in payoff (3 of 3)
- emotional_stake MUST escalate: Low → Medium → High
- demonstrates_how NEVER "Through dialogue"

For EXISTING scenes that serve as setup, provide SetupPayoffTracking objects with ALL required fields:
- tracking_id (REQUIRED): unique ID linking the chain
- trait_or_element (REQUIRED): what's being tracked
- position (REQUIRED): "1 of 3", "2 of 3", or "3 of 3"
- setup_type (REQUIRED): character_skill, character_trait, plot_element, trope_hint, world_rule, relationship
- payoff_scene: scene reference (filled in 1 of 3, 2 of 3; empty in 3 of 3)
- character_id, character_name: if applicable
- demonstrates_how: "Through action", "Through consequence", "Through observation"
- emotional_stake: "Low" (1 of 3), "Medium" (2 of 3), "High" (3 of 3)
- subtlety_level: "Subtle", "Moderate", "Obvious"

For NEW setup scenes needed:
- Identify the payoff scene (Ch7+)
- Check how many establishments already exist
- Propose new setup scenes to complete the pattern (aim for exactly 3 total)
- Ensure each establishment is VARIED (different context, escalating stakes)

Aim for 5-10 priority patterns requiring Rule of Three.

IMPORTANT: Provide a 'reasoning' field (2-3 sentences) explaining your Rule of Three strategy and how you're ensuring proper repetition patterns.
"""

        from ..story_schemas import ForeshadowingMap
        return self.invoke_structured(prompt, ForeshadowingMap, max_tokens=8000)

    def critique_foreshadowing(self, analysis: dict, metadata: dict) -> dict:
        """Critique from Rule of Three perspective."""
        prompt = f"""
FORESHADOWING ANALYSIS TO CRITIQUE:
Agent: {analysis['agent_name']}

Payoff Items: {len(analysis.get('payoff_items', []))}
{self._format_payoff_items(analysis.get('payoff_items', []))}

---

TASK: Critique this analysis from a Rule of Three perspective.

Evaluate:
1. PATTERN COMPLETENESS - Are all major payoffs backed by 3 establishments?
2. VARIETY - Do the 3 establishments differ in context/stakes?
3. ESCALATION - Do establishments build in intensity?
4. SPACING - Are establishments too clustered or too sparse?
5. MEMORABILITY - Will readers remember all 3 by payoff time?

Provide 3-5 specific critiques.
Identify essential payoffs requiring strict 3x enforcement.
"""

        from ..story_schemas import ForeshadowingCritique
        return self.invoke_structured(prompt, ForeshadowingCritique, max_tokens=8000)

    def vote_on_priorities(self, analyses: list[dict], critiques: list[dict]) -> dict:
        """Vote on priorities."""
        analyses_text = self._format_all_analyses(analyses)

        prompt = f"""
ALL ANALYSES:
{analyses_text}

---

TASK: Vote on essential payoffs requiring strict Rule of Three enforcement.

Essential (pick 5-8):
- Climactic skills/actions
- Character-defining decisions
- Major plot reveals

Provide vote with reasoning.
"""

        from ..story_schemas import ForeshadowingVote
        return self.invoke_structured(prompt, ForeshadowingVote, max_tokens=8000)

    # Helper methods (reuse from SetupPayoffAgent)
    def _format_chapters(self, outline: dict) -> str:
        lines = []
        for chapter in outline.get('chapters', [])[:12]:  # Limit
            lines.append(f"\nCh{chapter['chapter_number']}: {chapter['chapter_title']}")
            for scene in chapter.get('scenes', []):
                lines.append(f"  Scene {scene['scene_number']}: {scene.get('scene_summary', 'N/A')[:80]}")
        return '\n'.join(lines)

    def _format_characters(self, characters: list) -> str:
        lines = []
        for char in characters[:5]:
            name = char.get('name', 'Unknown')
            role = char.get('role', 'N/A')
            skills = char.get('skills', [])[:3] if isinstance(char.get('skills'), list) else []
            lines.append(f"- {name} ({role})")
            if skills:
                lines.append(f"  Skills: {', '.join(skills)}")
        return '\n'.join(lines)

    def _format_payoff_items(self, items: list) -> str:
        lines = []
        for item in items:
            lines.append(f"- {item.get('payoff_scene', 'N/A')}: {item.get('payoff_description', 'N/A')[:80]}")
            setups = item.get('required_setups', [])
            lines.append(f"  Setups: {len(setups)} ({', '.join([s.get('rule_of_three_position', '?') for s in setups])})")
        return '\n'.join(lines)

    def _format_all_analyses(self, analyses: list) -> str:
        lines = []
        for analysis in analyses:
            lines.append(f"\n{analysis.get('agent_name', 'Unknown')}: {len(analysis.get('payoff_items', []))} payoffs")
        return '\n'.join(lines)


class TropeExecutionAgent(BaseStoryAgent):
    """Agent focusing on trope execution timelines (especially subvert/invert)."""

    @property
    def name(self) -> str:
        return "TropeExecutionAgent"

    @property
    def role(self) -> str:
        return "Trope Execution - Subversion & Inversion Specialist"

    @property
    def system_prompt(self) -> str:
        return """You are the Trope Execution Agent, expert in trope subversion and inversion.

Your methodology focuses on:
- Tracking how tropes execute across the story
- Ensuring subverted tropes are established FIRST before subversion
- Ensuring inverted tropes have clear "flip" moments
- Creating timelines for trope execution

Trope usage types:
1. STRAIGHT - Trope played as expected (no special setup needed)
2. SUBVERT - Trope established then undermined (needs 2-3 establishment scenes before subversion reveal)
3. INVERT - Trope flipped on its head (needs clear "before flip" and "after flip" scenes)

For SUBVERT tropes:
- Early chapters: Establish trope expectation (2-3 scenes)
- Middle chapters: Plant subtle hints of subversion
- Later chapters: Reveal the subversion

For INVERT tropes:
- Early-mid chapters: Show trope in original form
- Midpoint/crisis: Execute the inversion
- Later chapters: Explore inverted implications

Example (Mentor Occupational Hazard - SUBVERT):
- Ch1-2: Establish mentor as wise guide (2 scenes)
- Ch4: Mentor gives crucial advice that seems solid
- Ch8: Reveal mentor's advice was manipulative/self-serving

Be specific about which scenes establish expectations and which execute the subversion."""

    def analyze_foreshadowing(
        self,
        chapter_outline: dict,
        characters: list[dict],
        integrated_beats: list[dict],
        tropes: list[dict]
    ) -> dict:
        """Analyze trope execution timelines."""
        chapters_text = self._format_chapters(chapter_outline)
        tropes_text = self._format_tropes(tropes)

        prompt = f"""
CHAPTER OUTLINE:
{chapters_text}

TROPES:
{tropes_text}

---

CRITICAL: You MUST include a 'reasoning' field at the top level of your response. This field should contain 2-3 sentences explaining your trope execution strategy and how you're setting up subversions/inversions properly.

TASK: Analyze trope execution timelines, focusing on subvert/invert usage.

TRACKING_ID SYSTEM:
- Generate unique ID: "tropename_001"
- Use SAME tracking_id for all related scenes in chain
- payoff_scene: Fill in setups (1 of 3, 2 of 3), empty in payoff (3 of 3)
- demonstrates_how: action/consequence/observation, NEVER dialogue

For EXISTING scenes that serve as trope setup, provide SetupPayoffTracking with:
- tracking_id, trait_or_element, position, setup_type, payoff_scene
- demonstrates_how, emotional_stake, subtlety_level

Example: scene_reference="Ch2, Scene 5", add_tracking=[SetupPayoffTracking object], reasoning="explanation"

For each trope timeline, you MUST provide:
1. trope_name: Name of the trope
2. trope_usage: Must be "straight", "subvert", or "invert"
3. execution_stages: A list of dictionaries with chapter_range and action
   Example: [dict with chapter_range="Ch1-3" and action="Establish expectation", dict with chapter_range="Ch4-6" and action="Plant hints"]
4. required_setups: List of SetupRequirement objects for new scenes

Execution timeline structure for SUBVERT/INVERT tropes:
- Stage 1: chapter_range="Ch1-3", action="Establish expectation"
- Stage 2: chapter_range="Ch4-6", action="Plant subtle hints"
- Stage 3: chapter_range="Ch7+", action="Execute subversion/inversion"

For straight tropes, minimal analysis needed (just note where they manifest).

Prioritize tropes marked "subvert" or "invert" - these REQUIRE careful setup.

Provide 3-5 trope execution timelines with required setup scenes.

CRITICAL OUTPUT STRUCTURE:
Your response MUST have this EXACT structure:
- agent_name: string
- trope_execution_timelines: LIST of TropeExecutionTimeline objects ONLY (no strings, no other types)
- existing_scene_annotations: LIST of ExistingSceneAnnotation objects
- reasoning: string at TOP LEVEL (NOT inside any list)

DO NOT put 'reasoning' inside the trope_execution_timelines list!
DO NOT add extra fields to trope_execution_timelines!
The reasoning field goes at the SAME LEVEL as agent_name and trope_execution_timelines.

IMPORTANT: Provide a 'reasoning' field (2-3 sentences) explaining your trope execution strategy and how you're setting up subversions/inversions properly.
"""

        from ..story_schemas import ForeshadowingMap
        return self.invoke_structured(prompt, ForeshadowingMap, max_tokens=8000)

    def critique_foreshadowing(self, analysis: dict, metadata: dict) -> dict:
        """Critique from trope execution perspective."""
        prompt = f"""
FORESHADOWING ANALYSIS TO CRITIQUE:
Agent: {analysis['agent_name']}

Trope Timelines: {len(analysis.get('trope_execution_timelines', []))}
{self._format_timelines(analysis.get('trope_execution_timelines', []))}

---

TASK: Critique this analysis from a trope execution perspective.

Evaluate:
1. ESTABLISHMENT - Are subverted tropes established BEFORE subversion?
2. TIMING - Does subversion happen too early or too late?
3. HINTS - Are there subtle hints planted before the reveal?
4. PAYOFF - Does the subversion feel earned or cheap?
5. COVERAGE - Are all subvert/invert tropes handled?

Provide 3-5 specific critiques.
"""

        from ..story_schemas import ForeshadowingCritique
        return self.invoke_structured(prompt, ForeshadowingCritique, max_tokens=8000)

    def vote_on_priorities(self, analyses: list[dict], critiques: list[dict]) -> dict:
        """Vote on priorities."""
        analyses_text = self._format_all_analyses(analyses)

        prompt = f"""
ALL ANALYSES:
{analyses_text}

---

TASK: Vote on essential trope-related payoffs.

Essential (pick 5-8):
- Subverted tropes requiring establishment
- Inverted tropes needing clear flip moments
- Trope-driven climactic moments

Provide vote with reasoning.
"""

        from ..story_schemas import ForeshadowingVote
        return self.invoke_structured(prompt, ForeshadowingVote, max_tokens=8000)

    # Helper methods
    def _format_chapters(self, outline: dict) -> str:
        lines = []
        for chapter in outline.get('chapters', [])[:12]:
            lines.append(f"\nCh{chapter['chapter_number']}: {chapter['chapter_title']}")
            for scene in chapter.get('scenes', []):
                tropes = scene.get('tropes_manifesting', [])
                lines.append(f"  Scene {scene['scene_number']}: {scene.get('scene_summary', 'N/A')[:70]}")
                if tropes:
                    lines.append(f"    Tropes: {', '.join(tropes[:3])}")
        return '\n'.join(lines)

    def _format_tropes(self, tropes: list) -> str:
        lines = []
        for trope in tropes:
            name = trope.get('trope_name', 'N/A')
            usage = trope.get('usage', 'N/A')
            lines.append(f"- {name} ({usage})")
            if usage.lower() in ['subvert', 'invert']:
                lines.append(f"  → Requires careful execution timeline")
        return '\n'.join(lines)

    def _format_timelines(self, timelines: list) -> str:
        lines = []
        for timeline in timelines:
            lines.append(f"\n- {timeline.get('trope_name', 'N/A')} ({timeline.get('trope_usage', 'N/A')})")
            for stage in timeline.get('execution_stages', []):
                lines.append(f"  {stage.get('chapter_range', '?')}: {stage.get('action', 'N/A')[:60]}")
        return '\n'.join(lines)

    def _format_all_analyses(self, analyses: list) -> str:
        lines = []
        for analysis in analyses:
            timelines = len(analysis.get('trope_execution_timelines', []))
            lines.append(f"\n{analysis.get('agent_name', 'Unknown')}: {timelines} trope timelines")
        return '\n'.join(lines)
