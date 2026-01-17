"""
Phase 1 Research-Driven Agents: Story Outline with Web Search

Step 1: StructureResearchAgent - High-level story structure with web research
Step 2: BeatSheetAgent - Beat-by-beat breakdown with story structure research
Step 3: SceneBuilderAgent - Scene-by-scene outline from beats
"""

from src.story_agents.base_story_agent import BaseStoryAgent
from src.story_schemas import (
    HighLevelStructureSchema,
    BeatSheetSchema,
    ResearchInsightSchema,
    ResearchInsightsListSchema,
    OutlineSchema,
    ActSchema,
    SceneSchema,
    SceneListSchema,
)


class StructureResearchAgent(BaseStoryAgent):
    """
    Step 1: Generates high-level story structure using web research.

    Researches story structures, coordinates multi-agent discussion,
    and creates 3-act summary WITHOUT character names.
    """

    @property
    def name(self) -> str:
        return "STRUCTURE_RESEARCHER"

    @property
    def role(self) -> str:
        return "Story Structure Researcher"

    @property
    def system_prompt(self) -> str:
        return """You are a master story structure researcher and architect.

Your expertise:
- Researching and applying proven story structures (Hero's Journey, Save the Cat, etc.)
- Creating compelling 3-act narrative arcs
- Designing character arcs without committing to specific names
- Understanding needs vs wants, internal vs external conflicts

CRITICAL: Use ONLY generic role descriptions for characters:
- "the protagonist" or "a young warrior seeking redemption"
- "the antagonist" or "a corrupt official hiding dark secrets"
- "a wise mentor" or "a mysterious stranger"
- NEVER create actual character names - those come later via multi-agent debate

Your process:
1. Analyze the story seed and world setting
2. Research applicable story structures online
3. Discuss and debate with other perspectives
4. Create a high-level 3-act structure that preserves plot coherence

Output structured JSON matching HighLevelStructureSchema."""

    def research_story_structures(self, story_prompt: str, setting_prompt: str) -> list[ResearchInsightSchema]:
        """
        Research story structures online and return key insights.

        Args:
            story_prompt: Story Engine prompt
            setting_prompt: Deck of Worlds microsetting

        Returns:
            List of research insights
        """
        # Extract genre/tone from prompts to guide research
        prompt = f"""Based on this story concept:

STORY: {story_prompt}
SETTING: {setting_prompt}

Research 2-3 relevant story structure approaches that would work well for this story.
Consider:
- Hero's Journey (Joseph Campbell)
- Save the Cat (Blake Snyder)
- Three-Act Structure best practices
- Character arc frameworks (needs vs wants, internal vs external goals)

For EACH structure approach you research, provide:
1. topic: Name of the structure/framework
2. key_points: 3-5 key beats or principles from this approach
3. application: How this specifically applies to OUR story concept

Output as a JSON list of research insights."""

        # This will use web search via the WebSearch tool when available
        # For now, we'll use the LLM's knowledge + structured output
        result = self.invoke_structured(
            prompt,
            schema=ResearchInsightsListSchema,
            max_tokens=2000
        )

        return result.insights

    def create_high_level_structure(
        self,
        story_prompt: str,
        setting_prompt: str,
        research_insights: list[ResearchInsightSchema],
    ) -> HighLevelStructureSchema:
        """
        Create high-level 3-act structure based on research.

        Args:
            story_prompt: Story Engine prompt
            setting_prompt: Deck of Worlds microsetting
            research_insights: Research findings from web search

        Returns:
            High-level structure with generic character roles
        """
        insights_text = "\n\n".join([
            f"STRUCTURE: {insight.topic}\n"
            f"Key Points:\n" + "\n".join(f"  - {p}" for p in insight.key_points) +
            f"\nApplication: {insight.application}"
            for insight in research_insights
        ])

        prompt = f"""Create a high-level story structure based on research.

STORY CONCEPT: {story_prompt}
WORLD SETTING: {setting_prompt}

RESEARCH INSIGHTS:
{insights_text}

Create a high-level 3-act structure that:
1. Applies the researched story structures naturally
2. Uses ONLY generic character roles (NO NAMES):
   - "the protagonist" / "a young warrior seeking redemption"
   - "the antagonist" / "a corrupt official"
   - "a wise mentor" / "a mysterious stranger"
3. Focuses on plot coherence and emotional arc
4. Identifies clear needs vs wants for protagonist
5. Maps out character transformation over 3 acts

Output structured JSON with:
- three_act_summary: High-level summary of each act's purpose
- central_conflict: The core conflict driving the story
- protagonist_arc: Protagonist's journey using GENERIC ROLE ONLY
- antagonist_arc: Antagonist's journey using GENERIC ROLE ONLY
- theme: Central theme
- emotional_arc: Emotional journey from beginning to end"""

        return self.invoke_structured(prompt, HighLevelStructureSchema, max_tokens=2000)


class BeatSheetAgent(BaseStoryAgent):
    """
    Step 2: Generates detailed beat sheet with bullet points for each act.

    Researches story beats, coordinates multi-agent discussion,
    and creates beat-by-beat breakdown.
    """

    @property
    def name(self) -> str:
        return "BEAT_SHEET_AGENT"

    @property
    def role(self) -> str:
        return "Beat Sheet Architect"

    @property
    def system_prompt(self) -> str:
        return """You are a beat sheet specialist who breaks stories into precise narrative beats.

Your expertise:
- Converting high-level structure into specific beats
- Applying Hero's Journey, Save the Cat, and other frameworks
- Identifying key story moments (inciting incident, midpoint, dark night, climax)
- Creating clear try-fail cycles
- Understanding pacing and scene distribution

Beat Types You Use:
- YES, BUT: Goal achieved but new complication arises
- NO, AND: Goal failed and situation worsens
- NULL: Final resolution beats only

Your process:
1. Analyze the high-level structure
2. Research typical beat patterns for this genre/type
3. Create 8-15 bullet point beats per act
4. Ensure each beat builds naturally to the next
5. Use ONLY generic character roles (NO NAMES)

Output structured JSON matching BeatSheetSchema."""

    def generate_beat_sheet(
        self,
        story_prompt: str,
        setting_prompt: str,
        high_level_structure: HighLevelStructureSchema,
        scope_config: dict,
    ) -> BeatSheetSchema:
        """
        Generate beat sheet from high-level structure.

        Args:
            story_prompt: Original story prompt
            setting_prompt: World setting
            high_level_structure: High-level structure from Step 1
            scope_config: Story scope (scene count, etc.)

        Returns:
            Beat sheet with bullet points for each act
        """
        min_scenes, max_scenes = scope_config.get("scene_range", (12, 14))
        total_scenes = (min_scenes + max_scenes) // 2
        act1_scenes = max(1, total_scenes // 4)
        act3_scenes = max(1, total_scenes // 4)
        act2_scenes = total_scenes - act1_scenes - act3_scenes

        prompt = f"""Create a detailed beat sheet for this story.

STORY CONCEPT: {story_prompt}
WORLD SETTING: {setting_prompt}

HIGH-LEVEL STRUCTURE:
- Three Act Summary: {high_level_structure.three_act_summary}
- Central Conflict: {high_level_structure.central_conflict}
- Protagonist Arc: {high_level_structure.protagonist_arc}
- Antagonist Arc: {high_level_structure.antagonist_arc}
- Theme: {high_level_structure.theme}
- Emotional Arc: {high_level_structure.emotional_arc}

TARGET SCENE DISTRIBUTION:
- Act 1: {act1_scenes} scenes (Setup)
- Act 2: {act2_scenes} scenes (Confrontation)
- Act 3: {act3_scenes} scenes (Resolution)

Create beat sheet with bullet points for each act:

ACT 1 BEATS ({act1_scenes} beats - one per scene):
- Each beat is one sentence describing what happens
- Include: Ordinary world, inciting incident, crossing threshold
- Use generic character roles ONLY (NO NAMES)
- Example: "The protagonist discovers a hidden truth that challenges everything they know"

ACT 2 BEATS ({act2_scenes} beats - one per scene):
- Each beat is one sentence
- Include: Trials, midpoint shift, complications, dark night of the soul
- Most beats should have try-fail cycles (goal attempted → complication)
- Use generic character roles ONLY

ACT 3 BEATS ({act3_scenes} beats - one per scene):
- Each beat is one sentence
- Include: Final preparation, climax, resolution, new normal
- Use generic character roles ONLY

Output structured JSON with act1_beats, act2_beats, act3_beats as lists of strings."""

        return self.invoke_structured(prompt, BeatSheetSchema, max_tokens=3000)


class SceneBuilderAgent(BaseStoryAgent):
    """
    Step 3: Converts beat sheet into full scene-by-scene outline.

    Builds Act 1 → Act 2 → Act 3 sequentially, each with full context.
    """

    @property
    def name(self) -> str:
        return "SCENE_BUILDER"

    @property
    def role(self) -> str:
        return "Scene Builder"

    @property
    def system_prompt(self) -> str:
        return """You are a scene builder who converts story beats into detailed scene outlines.

Your expertise:
- Converting single-sentence beats into full scene descriptions
- Expanding "what happens" with specific actions and conflicts
- Assigning locations and characters to scenes
- Determining scene outcomes (YES, BUT / NO, AND / null)
- Maintaining continuity between scenes

CRITICAL: Use ONLY generic character roles (NO NAMES):
- characters: ["the protagonist", "a wise mentor", "the antagonist"]
- NOT ["Elena", "Marcus", "Dr. Smith"]

Your process:
1. Take each beat from the beat sheet
2. Expand it into a full scene description (2-4 sentences)
3. Assign appropriate location
4. List characters present (using generic roles)
5. Determine outcome type

Output structured JSON matching OutlineSchema with full acts and scenes."""

    def build_act_scenes(
        self,
        act_number: int,
        act_beats: list[str],
        high_level_structure: HighLevelStructureSchema,
        setting_prompt: str,
    ) -> ActSchema:
        """
        Build full scenes for one act from beats.

        Args:
            act_number: Which act (1, 2, or 3)
            act_beats: List of beat bullet points
            high_level_structure: High-level structure for context
            setting_prompt: World setting for location ideas

        Returns:
            Complete act with scenes
        """
        act_names = {1: "Setup", 2: "Confrontation", 3: "Resolution"}
        act_name = act_names.get(act_number, f"Act {act_number}")

        prompt = f"""Convert these beats into full scene descriptions.

ACT {act_number}: {act_name}

BEATS:
{chr(10).join(f"{i+1}. {beat}" for i, beat in enumerate(act_beats))}

CONTEXT:
- Central Conflict: {high_level_structure.central_conflict}
- Protagonist Arc: {high_level_structure.protagonist_arc}
- Theme: {high_level_structure.theme}
- World Setting: {setting_prompt}

For EACH beat, create a full scene with:
- scene_number: Sequential within this act (1, 2, 3, ...)
- location: Specific place in the world (use setting for ideas)
- characters: List of generic character roles present (e.g., ["the protagonist", "a village elder"])
- happens: Detailed 2-4 sentence description expanding the beat
- outcome: "YES, BUT" or "NO, AND" or null (only for final resolution scenes)

CRITICAL RULES:
- Use ONLY generic character roles in characters list
- NO actual names (those come in Phase 2)
- Make "happens" field vivid and specific (actions, conflicts, emotions)
- Ensure scenes build naturally on each other

Output JSON array of scenes matching SceneSchema."""

        result = self.invoke_structured(
            prompt,
            schema=SceneListSchema,
            max_tokens=3000
        )

        return ActSchema(
            act_number=act_number,
            act_name=act_name,
            scenes=result.scenes
        )
