"""
SUBSTEP 7A: Scene Structure Validator

Validates Goal → Conflict → Disaster structure (Dwight V. Swain framework).

Based on research from:
- KM Weiland's Scene Structure
- Swain's "Techniques of the Selling Writer"
- Professional developmental editing practices
"""

from src.story_agents.base_story_agent import BaseStoryAgent
from src.story_schemas import SceneStructureResult
from src.config import get_token_limit


class SceneStructureValidator(BaseStoryAgent):
    """
    Validates scene structure using Goal → Conflict → Disaster framework.

    Single Responsibility: Check if scene has proper structural elements.

    NOT responsible for:
    - Scene purpose (that's SUBSTEP 7B)
    - Voice consistency (that's SUBSTEP 7C)
    - Chapter-level validation (that's SUBSTEP 7D)
    """

    @property
    def name(self) -> str:
        return "Scene Structure Validator"

    @property
    def role(self) -> str:
        return "Developmental Editor - Scene Structure Specialist"

    @property
    def system_prompt(self) -> str:
        return """You are a professional developmental editor specializing in scene structure validation.

You use the Goal → Conflict → Disaster framework (Dwight V. Swain) to evaluate scenes.

Your expertise includes:
- Identifying action scenes (Goal → Conflict → Disaster)
- Identifying sequel scenes (Reaction → Dilemma → Decision)
- Detecting missing structural elements
- Providing specific, actionable revision suggestions"""

    def validate_structure(
        self,
        scene_prose: str,
        scene_context: dict
    ) -> SceneStructureResult:
        """
        Validate scene structure.

        Args:
            scene_prose: The actual prose text of the scene
            scene_context: Dictionary with:
                - goal: Character's scene goal (optional, for validation)
                - pov_character: POV character name
                - conflict: Expected conflict (optional)
                - outcome: Expected outcome (optional)

        Returns:
            SceneStructureResult with validation details
        """

        prompt = f"""You are a professional developmental editor specializing in scene structure.

You use the Goal → Conflict → Disaster framework (Dwight V. Swain) to validate scenes.

**SCENE STRUCTURE FRAMEWORKS:**

**ACTION SCENE:**
1. GOAL: Character wants something specific this scene
2. CONFLICT: Face-to-face opposition preventing goal
3. DISASTER: Scene ends badly, goal not achieved OR achieved with complications

**SEQUEL SCENE (Reaction Scene):**
1. REACTION: Character processes previous disaster emotionally
2. DILEMMA: Character weighs limited options
3. DECISION: Character decides on new goal

**YOUR TASK:**

Analyze the scene below and determine:

1. **Does it have a CLEAR GOAL?**
   - Is there something specific the character wants THIS scene?
   - Where is it stated? (which paragraph)
   - NOT the overarching story goal - the SCENE goal

2. **Does it have CONFLICT?**
   - Is there face-to-face opposition? (another character resisting)
   - OR internal conflict? (character wrestling with decision)
   - OR situational conflict? (environment/circumstances opposing)
   - Is conflict active on the page? (not just mentioned)

3. **Does it have DISASTER or OUTCOME?**
   - Does scene end with character's situation changed?
   - YES-BUT (goal achieved but complications)
   - NO-AND (goal failed and things worse)
   - Where does disaster occur? (which paragraph)

4. **SCENE TYPE:**
   - action_scene (Goal → Conflict → Disaster)
   - sequel_scene (Reaction → Dilemma → Decision)
   - unclear (doesn't fit either pattern)

5. **SCORING:**
   - 9-10: Perfect structure, all elements present and clear
   - 7-8: Good structure, minor gaps
   - 5-6: Weak structure, missing 1 critical element
   - 3-4: Poor structure, missing 2+ elements
   - 0-2: No discernible structure

**SCENE TO VALIDATE:**

POV Character: {scene_context.get('pov_character', 'Unknown')}
Expected Goal (if provided): {scene_context.get('goal', 'Not specified')}

PROSE:
{scene_prose}

**OUTPUT REQUIREMENTS:**

- has_clear_goal: bool
- goal_stated_location: "paragraph 1" | "paragraph 2" | "missing"
- has_conflict: bool
- conflict_type: "face-to-face" | "internal" | "situational" | "missing"
- has_disaster_or_outcome: bool
- disaster_location: "final paragraph" | "paragraph X" | "missing"
- scene_type: "action_scene" | "sequel_scene" | "unclear"
- structure_score: float (0.0-10.0)
- missing_elements: list[str] (e.g., ["clear_goal", "disaster"])
- strengths: list[str] (e.g., ["strong conflict", "clear goal"])
- revision_needed: bool (true if score < 7.5 OR missing critical elements)
- revision_suggestions: list[str] (specific fixes)

Be specific and analytical. Don't just say "good" - explain WHY."""

        # Get token limit from config
        max_tokens = get_token_limit("step7_revision", "scene_critique")

        result = self.invoke_structured(
            prompt,
            schema=SceneStructureResult,
            max_tokens=max_tokens
        )

        return result
