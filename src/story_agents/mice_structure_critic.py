"""
MICE Structure Critic for Step 7: Narrative Revision.

Validates MICE Quotient principles in generated prose:
- Opening pattern: WHO/WHERE/GENRE in first 3 sentences, ordered by dominant MICE type
- Closing mirror: References opening element, concrete (not thematic summary), shows shift
- Try-fail dramatization: Outcome shown through action, obstacles match MICE type
- Escalation: Stakes visibly higher than previous scene on same thread

Methodology: Mary Robinette Kowal's MICE Quotient (Writing Excuses).
"""

from src.story_agents.base_story_agent import BaseStoryAgent
from src.story_schemas import MiceStructureCritique
from src.config import get_token_limit


class MiceStructureCritic(BaseStoryAgent):
    """Validates MICE Quotient principles in generated prose.

    Methodology: Mary Robinette Kowal's MICE Quotient.
    Checks opening pattern (who/where/genre ordered by MICE type),
    closing mirror, try-fail dramatization, obstacle-type matching,
    and escalation.
    """

    @property
    def name(self) -> str:
        return "MICE_STRUCTURE_CRITIC"

    @property
    def role(self) -> str:
        return "MICE Quotient Structural Analyst"

    @property
    def system_prompt(self) -> str:
        return """You are a structural editor specializing in the MICE Quotient framework.

YOUR MISSION: Evaluate prose scenes for MICE structural integrity. Check openings, closings,
try-fail dramatization, and escalation.

=== MICE THREAD TYPES ===

MILIEU: Opens when character enters unfamiliar space, closes on exit.
  Obstacles PREVENT LEAVING: physical barriers, getting lost, hostile terrain.
INQUIRY: Opens when question raised ("Huh?"), closes when answered ("Aha!").
  Obstacles PREVENT KNOWING: lies, red herrings, destroyed evidence, dead ends.
CHARACTER: Opens on identity dissatisfaction (INTERNAL), closes when identity solidifies.
  Obstacles PREVENT BECOMING: self-loathing, pressure to stay same, change backfires.
EVENT: Opens when status quo disrupted (EXTERNAL), closes on new equilibrium.
  Obstacles PREVENT RESTORING ORDER: cascading consequences, new threats.

Critical distinction: Character = INTERNAL. Event = EXTERNAL.

=== OPENING PATTERN (First 2-3 Sentences) ===

Reader needs WHO, WHERE, and GENRE/MOOD within first 3 sentences.
The ORDER signals the dominant MICE type:

MILIEU -> WHERE first (sensory environment before character)
INQUIRY -> QUESTION/anomaly first (the "Huh?" that hooks)
CHARACTER -> WHO + internal state first (reader expects transformation)
EVENT -> ACTION/disruption first (reader expects crisis response)

WHO = character + attitude via action (what they're doing, how they feel).
WHERE = sensory detail, NOT just a label.
GENRE = specific AND unique detail for this world.

=== CLOSING PATTERN (Mirror the Opening) ===

Closing paragraph MUST mirror an element from the opening to show what changed.
- Reference the SAME sensory detail, location, or action from the opening
- Show how character's RELATIONSHIP to it has SHIFTED
- Mood reflects outcome: YES_BUT = uneasy, NO_AND = darkening, YES_AND = earned relief

GOOD endings: image, action, dialogue, sensory detail
BAD endings: thematic summary ("She realized..."), rhetorical questions about meaning

=== TRY-FAIL DRAMATIZATION ===

Outcomes must be DRAMATIZED through action and consequence, not summarized.

YES_BUT (two beats): character achieves goal, THEN complication from success
NO_AND (three beats): attempt, failure, THEN additional consequence
YES_AND (resolution): smooth progress, earned relief
NO_BUT (turning point): failure, but unexpected gain

Obstacles must MATCH the MICE type:
- MILIEU: spatial barriers, hostile terrain
- INQUIRY: lies, red herrings, dead ends
- CHARACTER: self-doubt, pressure to regress
- EVENT: cascading failures, new threats

=== ESCALATION ===

Each scene should raise stakes from the previous scene on the same thread.
Look for: higher consequences, narrower options, deeper emotional investment.

For each issue, be SPECIFIC about what's wrong and how to fix it."""

    def critique(
        self,
        prose: str,
        scene_data: dict,
        previous_scene_prose: str = "",
        scene_id: str = "unknown",
    ) -> MiceStructureCritique:
        """Critique MICE structural integrity of a prose scene.

        Args:
            prose: The scene prose to critique
            scene_data: Scene metadata dict (should contain mice_threads, dominant_mice_type, outcome, goal, conflict)
            previous_scene_prose: Previous scene's prose for escalation checking
            scene_id: Scene identifier

        Returns:
            MiceStructureCritique with structural validation results
        """
        # Extract MICE metadata from scene data
        mice_threads = scene_data.get("mice_threads", [])
        dominant_mice = scene_data.get("dominant_mice_type", "event")
        outcome = scene_data.get("outcome", "")
        goal = scene_data.get("goal", "")
        conflict = scene_data.get("conflict", "")

        # Format MICE thread info
        threads_text = ""
        if mice_threads:
            threads_text = "\n".join([
                f"  - [{t.get('thread_type', '?')}] {t.get('thread_id', '?')} "
                f"(position: {t.get('position', '?')}, try-fail: {t.get('try_fail_type', 'none')})"
                for t in (mice_threads if isinstance(mice_threads, list) else [])
            ])
        else:
            threads_text = "  (No MICE threads specified — infer from prose)"

        # Build escalation context
        escalation_context = ""
        if previous_scene_prose:
            escalation_context = f"""
PREVIOUS SCENE PROSE (for escalation comparison):
{previous_scene_prose[:1000]}...
"""

        prompt = f"""Critique the MICE Quotient structural integrity of this prose scene.

SCENE ID: {scene_id}
DOMINANT MICE TYPE: {dominant_mice}
SCENE OUTCOME: {outcome}
SCENE GOAL: {goal}
SCENE CONFLICT: {conflict}

MICE THREADS IN THIS SCENE:
{threads_text}
{escalation_context}
PROSE TO CRITIQUE:
{prose}

Evaluate:
1. OPENING (first 2-3 sentences): Does it establish WHO, WHERE, GENRE/MOOD?
   Does the order match the dominant MICE type ({dominant_mice})?
2. CLOSING (final paragraph): Does it mirror an element from the opening?
   Does it show what changed? Is it concrete (image/action/dialogue) or abstract (thematic summary)?
3. TRY-FAIL: Is the scene outcome ({outcome}) dramatized through action and consequence?
   Do obstacles match the MICE type ({dominant_mice})?
   Are consequences of {outcome} visible in the prose?
4. ESCALATION: Are stakes higher than the previous scene on the same thread?

Be thorough. Flag every structural weakness."""

        return self.invoke_structured(
            prompt,
            MiceStructureCritique,
            max_tokens=get_token_limit("step6_prose_generation", "prose_critique"),
        )
