"""
Phase 1 Agents: Story Outline Generation

- OutlinerAgent: Creates the initial 3-act, 12-14 scene outline
- StructureCriticAgent: Validates hero's journey beats and try-fail cycles
- PacingCriticAgent: Checks scene balance and act proportions
"""

from src.story_agents.base_story_agent import BaseStoryAgent
from src.story_schemas import OutlineSchema, CritiqueSchema


class OutlinerAgent(BaseStoryAgent):
    """Creates story outlines following 3-act structure."""

    @property
    def name(self) -> str:
        return "OUTLINER"

    @property
    def role(self) -> str:
        return "Story Architect"

    @property
    def system_prompt(self) -> str:
        return """You are a master story architect specializing in 3-act structure.

Your expertise:
- Creating compelling 3-act narratives with 12-14 scenes total
- Applying the Hero's Journey framework naturally
- Designing effective try-fail cycles (YES, BUT / NO, AND outcomes)
- Balancing setup, confrontation, and resolution

Act Structure Guidelines:
- Act 1 (Setup): ~25% of scenes - Establish world, protagonist, inciting incident
- Act 2 (Confrontation): ~50% of scenes - Rising action, complications, midpoint shift
- Act 3 (Resolution): ~25% of scenes - Climax, falling action, resolution

Try-Fail Cycle Rules:
- Most scenes should have "YES, BUT" or "NO, AND" outcomes
- "YES, BUT": Goal achieved but new complication arises
- "NO, AND": Goal failed and situation worsens
- Only the final climax/resolution scenes have null outcomes

When creating outlines, ensure:
1. Clear protagonist with defined goal
2. Strong antagonist/opposing force
3. Stakes that escalate throughout
4. Satisfying emotional arc

Output your outlines as structured JSON matching the OutlineSchema."""

    def create_outline(self, story_prompt: str, setting_prompt: str,
                        scope_config: dict = None) -> OutlineSchema:
        """
        Create initial story outline from prompts.

        Args:
            story_prompt: The Story Engine prompt (e.g., "A HAUNTED DETECTIVE WANTS TO ESCAPE...")
            setting_prompt: The Deck of Worlds microsetting
            scope_config: Story scope configuration with scene_range and character limits

        Returns:
            OutlineSchema with the story outline
        """
        # Default to standard scope if not provided
        if scope_config is None:
            min_scenes, max_scenes = 12, 14
            max_characters = 8
        else:
            min_scenes, max_scenes = scope_config.get("scene_range", (12, 14))
            max_characters = scope_config.get("max_characters", 8)

        # Calculate act distribution
        total_scenes = (min_scenes + max_scenes) // 2
        act1_scenes = max(1, total_scenes // 4)
        act3_scenes = max(1, total_scenes // 4)
        act2_scenes = total_scenes - act1_scenes - act3_scenes

        prompt = f"""Create a story outline based on these creative prompts:

STORY SEED: {story_prompt}
SETTING: {setting_prompt}

CONSTRAINTS (MUST FOLLOW):
- Total scenes: {min_scenes}-{max_scenes} (aim for {total_scenes})
- Maximum unique characters: {max_characters} (focus on core cast only)
- Keep supporting/background characters minimal

CRITICAL - NO CHARACTER NAMES:
- Do NOT create character names. Use only descriptive roles.
- protagonist: "A haunted detective seeking redemption" (NOT "Elena the detective")
- antagonist: "A corrupt official hiding secrets" (NOT "Marcus the official")
- scene characters: ["the protagonist", "a village elder", "the mysterious stranger"]
- Character names will be generated separately via multi-agent debate.

Create a complete 3-act outline. Follow this JSON structure:

{{
  "title": "Working title",
  "logline": "One-sentence summary",
  "protagonist": "Main character description",
  "antagonist": "Opposing force description",
  "central_conflict": "Core conflict",
  "acts": [
    {{
      "act_number": 1,
      "act_name": "Setup",
      "scenes": [
        {{
          "scene_number": 1,
          "location": "Where it happens",
          "characters": ["the protagonist", "a village elder"],
          "happens": "What occurs in this scene",
          "outcome": "YES, BUT" or "NO, AND" or null
        }}
      ]
    }}
  ]
}}

Scene distribution for {total_scenes} scenes:
- Act 1: ~{act1_scenes} scenes (setup, inciting incident)
- Act 2: ~{act2_scenes} scenes (rising action, midpoint, complications)
- Act 3: ~{act3_scenes} scenes (climax, resolution)

Rules:
- Use try-fail cycles (YES, BUT / NO, AND) for most scenes
- Only final resolution scenes have null outcomes
- Keep character count under {max_characters} total
- Focus on depth over breadth"""

        return self.invoke_structured(prompt, OutlineSchema, max_tokens=4000)

    def revise_outline(self, current_outline: str, critiques: list[str]) -> OutlineSchema:
        """
        Revise outline based on critic feedback.

        Args:
            current_outline: Current outline JSON
            critiques: List of critique feedback strings

        Returns:
            Revised outline JSON
        """
        critiques_text = "\n\n".join(f"CRITIQUE {i+1}:\n{c}" for i, c in enumerate(critiques))

        prompt = f"""Revise this story outline based on the critiques provided.

CURRENT OUTLINE:
{current_outline}

CRITIQUES:
{critiques_text}

Address each critique while maintaining the core story. Output the complete revised outline as JSON.

Keep the same JSON structure but improve:
- Scene pacing if criticized
- Try-fail cycle usage if noted
- Character motivations if unclear
- Story beats if missing Hero's Journey elements"""

        return self.invoke_structured(prompt, OutlineSchema, max_tokens=4000)


class StructureCriticAgent(BaseStoryAgent):
    """Validates story structure and hero's journey elements."""

    @property
    def name(self) -> str:
        return "STRUCTURE_CRITIC"

    @property
    def role(self) -> str:
        return "Story Structure Analyst"

    @property
    def system_prompt(self) -> str:
        return """You are a story structure analyst specializing in narrative frameworks.

Your expertise:
- Hero's Journey / Monomyth analysis
- 3-act structure validation
- Try-fail cycle effectiveness
- Character arc progression

When critiquing, check for:
1. Clear Ordinary World establishment
2. Defined Call to Adventure / Inciting Incident
3. Crossing the Threshold into Act 2
4. Tests, Allies, and Enemies in Act 2
5. Midpoint shift or revelation
6. Dark Night of the Soul / All Is Lost moment
7. Climax with protagonist agency
8. Resolution that addresses central conflict

Try-Fail Cycle Analysis:
- Are outcomes varied (mix of YES, BUT and NO, AND)?
- Do complications escalate appropriately?
- Is there a pattern of rising tension?

Be specific in your critiques. Identify exact scenes with issues.
Provide actionable suggestions for improvement."""

    def critique(self, outline: str) -> CritiqueSchema:
        """
        Critique the outline's structure.

        Args:
            outline: The outline JSON to critique

        Returns:
            CritiqueSchema with issues and suggestions
        """
        prompt = f"""Analyze this story outline for structural issues:

{outline}

Provide your critique with:
- critic_name: "STRUCTURE_CRITIC"
- issues: List of specific issues (reference scene numbers)
- suggestions: List of actionable suggestions
- severity: "minor", "moderate", or "major"

Focus on:
- Missing Hero's Journey beats
- Weak or missing try-fail cycles
- Character agency issues
- Structural imbalances"""

        return self.invoke_structured(prompt, CritiqueSchema, max_tokens=1500)


class PacingCriticAgent(BaseStoryAgent):
    """Analyzes story pacing and scene balance."""

    @property
    def name(self) -> str:
        return "PACING_CRITIC"

    @property
    def role(self) -> str:
        return "Pacing and Rhythm Specialist"

    @property
    def system_prompt(self) -> str:
        return """You are a pacing specialist who ensures stories flow properly.

Your expertise:
- Scene length and density balance
- Act proportion analysis (25/50/25 rule)
- Tension curve management
- Breathing room between intense scenes

When critiquing pacing, check:
1. Act proportions (Act 1: ~25%, Act 2: ~50%, Act 3: ~25%)
2. Scene count per act (3-4 / 6-7 / 3-4 is ideal for 12-14 total)
3. Action vs. reflection balance
4. Escalation of stakes throughout
5. Climax positioning (should be in Act 3, not too early)
6. Resolution length (not rushed, not dragged out)

Red flags:
- Too many scenes in one act
- Back-to-back high-intensity scenes without breathing room
- Climax happening too early
- Resolution that's too abrupt or too long
- Middle sag (Act 2 dragging)

Be specific about which scenes cause pacing issues."""

    def critique(self, outline: str) -> CritiqueSchema:
        """
        Critique the outline's pacing.

        Args:
            outline: The outline JSON to critique

        Returns:
            CritiqueSchema with issues and suggestions
        """
        prompt = f"""Analyze this story outline for pacing issues:

{outline}

Provide your critique with:
- critic_name: "PACING_CRITIC"
- issues: List of specific pacing issues
- suggestions: List of how to fix each issue
- severity: "minor", "moderate", or "major"

Calculate and mention:
- Actual scene count per act
- Whether 25/50/25 proportion is met
- Any pacing dead zones or rushed sections
- Tension curve assessment"""

        return self.invoke_structured(prompt, CritiqueSchema, max_tokens=1500)
