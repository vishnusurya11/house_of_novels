"""
Cast Ensemble Validation Agents for Step 1: Post-Creation Visual Audit.

3 agents debate the visual distinctiveness of the ENTIRE character cast:

1. CastEnsembleVisualistAgent — overall visual identity (shape, color, build, height)
2. CastEnsembleSilhouetteAgent — silhouette test (outline, proportions, posture, hair shape)
3. CastEnsembleCostumeAgent — costume contrast (color, fabric, accessories, style)

Each agent:
- Reviews ALL characters simultaneously and proposes corrections
- Cross-critiques other agents' correction proposals
- Votes for the best correction set

Called AFTER all characters are created in Step 1. Replaces the old single-LLM
cast visual audit with a proper multi-agent debate.
"""

from src.story_agents.base_story_agent import BaseStoryAgent
from src.story_schemas import (
    CastEnsembleProposal,
    CastEnsembleCritique,
    CastEnsembleVote,
)


# =============================================================================
# Cast Ensemble Debate Agents
# =============================================================================


class CastEnsembleVisualistAgent(BaseStoryAgent):
    """
    Reviews the full cast for overall visual identity collisions.

    Focus: shape language, color palette, build, height, eye color, hair color,
    overall visual impression. Ensures no two characters could be confused.
    """

    METHODOLOGY_NAME = "Visual Identity Analysis"
    METHODOLOGY_SOURCE = "Character design ensemble theory, Disney/Pixar principles"
    CORE_BELIEFS = [
        "Every character must be instantly identifiable in a lineup",
        "Shape language must vary across the cast (circle, rectangle, triangle, diamond)",
        "Color palette must be distinct per character",
        "Build and height must spread across a spectrum",
        "No two characters should share the same overall visual impression",
    ]

    @property
    def name(self) -> str:
        return "CAST_VISUALIST"

    @property
    def role(self) -> str:
        return "Cast Visual Identity Analyst"

    @property
    def system_prompt(self) -> str:
        return """You are a cast visual identity analyst. You review ALL characters in a story
simultaneously and identify where they look too similar.

Your expertise:
- Shape language: each character should have a different primary body shape
  (circular/rounded, rectangular/broad, triangular/angular, diamond/narrow)
- Color theory: each character should occupy a different color family
  (warm earth, cool blue/silver, jewel tones, muted neutrals)
- Build spectrum: the cast should span short-to-tall, petite-to-stocky
- Hair: the #1 identifier — every character must have dramatically different hair
  (different color AND different style AND different length)
- Eyes: no two characters should share the same eye color
- Overall impression: if you blurred the image, could you still tell them apart?

When proposing corrections:
- Identify SPECIFIC collisions (e.g., "Both have dark hair in braids")
- Propose MINIMUM targeted fixes — don't redesign from scratch
- Preserve each character's psychological authenticity
- Ensure fixes don't create NEW collisions with other characters
- Include costume corrections when clothing is too similar"""

    def propose_corrections(
        self,
        characters_text: str,
    ) -> CastEnsembleProposal:
        """Review full cast and propose corrections for visual identity collisions."""
        prompt = f"""Review this ENTIRE character cast for visual identity collisions.

{characters_text}

For each collision found, propose the MINIMUM fix to make characters distinct.
Check: shape language, build, height, hair (color + style + length), eye color,
ethnicity, posture, and overall color palette.

RULES:
- Every fix must be the SMALLEST change that resolves the collision
- Don't redesign characters — fix specific colliding attributes
- If a character has no collisions, return them unchanged with changes_made="no changes"
- Ensure your fixes don't create new collisions with other characters
- Include costume field in your corrections (even if unchanged)

Return corrections for ALL characters."""

        return self.invoke_structured(prompt, CastEnsembleProposal, max_tokens=12000)

    def critique_proposal(
        self,
        target_agent: str,
        proposal: CastEnsembleProposal,
        characters_text: str,
    ) -> CastEnsembleCritique:
        """Critique another agent's correction proposal."""
        corrections_text = "\n".join(
            f"- {c.character_name}: {c.changes_made}" for c in proposal.characters
        )
        prompt = f"""Critique this cast correction proposal from a VISUAL IDENTITY perspective.

ORIGINAL CHARACTERS:
{characters_text}

PROPOSED CORRECTIONS by {target_agent}:
{corrections_text}

Evaluate:
1. Do the corrections resolve ALL visual collisions?
2. Are any fixes too drastic (breaking character psychology)?
3. Do the fixes introduce NEW collisions?
4. Is the overall cast now visually diverse enough?

Provide a score 1-10 and specific suggestions."""

        return self.invoke_structured(prompt, CastEnsembleCritique, max_tokens=8000)

    def vote_for_best(
        self,
        proposals: list[CastEnsembleProposal],
    ) -> CastEnsembleVote:
        """Vote for the best correction set."""
        proposals_text = "\n\n".join(
            f"PROPOSAL by {p.agent_name}:\n{p.ensemble_analysis}\nChanges: "
            + ", ".join(f"{c.character_name}: {c.changes_made}" for c in p.characters)
            for p in proposals
        )

        prompt = f"""Vote for the BEST cast correction proposal.

{proposals_text}

Which proposal creates the most visually distinct character cast?
You CANNOT vote for your own proposal.

Provide a vote with reasoning."""

        return self.invoke_structured(prompt, CastEnsembleVote, max_tokens=8000)


class CastEnsembleSilhouetteAgent(BaseStoryAgent):
    """
    Reviews the full cast purely through the silhouette test.

    Focus: body outline, proportions, posture, hair shape, height.
    If you filled each character solid black, could you tell them apart?
    """

    METHODOLOGY_NAME = "Silhouette Distinctiveness"
    METHODOLOGY_SOURCE = "Animation industry silhouette test, shape language theory"
    CORE_BELIEFS = [
        "Every character must pass the silhouette test",
        "Body proportions create the most fundamental visual distinction",
        "Posture is as identifying as body shape",
        "Hair outline is the strongest silhouette differentiator",
        "Height variation is critical for group scenes",
    ]

    @property
    def name(self) -> str:
        return "CAST_SILHOUETTE"

    @property
    def role(self) -> str:
        return "Cast Silhouette Analyst"

    @property
    def system_prompt(self) -> str:
        return """You are a silhouette test specialist. You evaluate character casts by imagining
each character as a SOLID BLACK OUTLINE and checking if they are distinguishable.

The silhouette test is the GOLD STANDARD in professional character design
(Disney, Pixar, Ghibli, game studios all use it).

What creates unique silhouettes:
- BODY SHAPE: round vs. angular vs. broad vs. narrow (the most fundamental)
- HEIGHT: must vary significantly across cast (not all "average")
- POSTURE: how they stand — upright, hunched, leaning, coiled
- HAIR OUTLINE: the biggest silhouette differentiator — different shape, volume, length
- PROPORTIONS: head-to-body ratio, shoulder width, limb length
- ACCESSORIES: hats, capes, weapons, bags create unique outlines

What FAILS the silhouette test:
- Characters with same height + same build + same posture
- "Average" everything — average height, medium build, standard posture
- Similar hair shapes even if colors differ (colors disappear in silhouette!)
- All characters standing the same way

When proposing corrections:
- Focus ONLY on what affects the outline/silhouette
- Color and texture don't matter for silhouette — focus on SHAPE
- Suggest changes to height, build, posture, hair shape, or accessories
- Each character should have a unique outline that is NEVER confused with another"""

    def propose_corrections(
        self,
        characters_text: str,
    ) -> CastEnsembleProposal:
        """Review full cast for silhouette test failures."""
        prompt = f"""Apply the SILHOUETTE TEST to this entire character cast.

{characters_text}

Imagine each character as a SOLID BLACK OUTLINE. Can you tell them apart?

Check:
1. Are any two characters the same height + same build? = FAIL
2. Do any characters have similar hair shapes? = FAIL
3. Do any characters have the same posture? = FAIL
4. Would any pair be confused in a group silhouette? = FAIL

For each failure, propose the MINIMUM fix to create unique silhouettes.
Return corrections for ALL characters (unchanged ones get changes_made="no changes").
Include costume field (even if unchanged)."""

        return self.invoke_structured(prompt, CastEnsembleProposal, max_tokens=12000)

    def critique_proposal(
        self,
        target_agent: str,
        proposal: CastEnsembleProposal,
        characters_text: str,
    ) -> CastEnsembleCritique:
        """Critique from silhouette perspective."""
        corrections_text = "\n".join(
            f"- {c.character_name}: {c.changes_made}" for c in proposal.characters
        )
        prompt = f"""Critique from SILHOUETTE TEST perspective.

ORIGINAL CHARACTERS:
{characters_text}

PROPOSED CORRECTIONS by {target_agent}:
{corrections_text}

Would the corrected cast pass the silhouette test? Score 1-10."""

        return self.invoke_structured(prompt, CastEnsembleCritique, max_tokens=8000)

    def vote_for_best(
        self,
        proposals: list[CastEnsembleProposal],
    ) -> CastEnsembleVote:
        """Vote for best silhouette corrections."""
        proposals_text = "\n\n".join(
            f"PROPOSAL by {p.agent_name}:\n{p.ensemble_analysis}"
            for p in proposals
        )

        prompt = f"""Vote for the proposal that best passes the SILHOUETTE TEST.

{proposals_text}

Which correction set creates the most distinct character outlines?
You CANNOT vote for your own proposal."""

        return self.invoke_structured(prompt, CastEnsembleVote, max_tokens=8000)


class CastEnsembleCostumeAgent(BaseStoryAgent):
    """
    Reviews the full cast for costume and clothing differentiation.

    Focus: clothing color, fabric, style, accessories, overall look.
    Ensures each character has a unique "costume identity."
    """

    METHODOLOGY_NAME = "Costume Ensemble Design"
    METHODOLOGY_SOURCE = "Costume design for film, theatre, and animation"
    CORE_BELIEFS = [
        "Costume is the EASIEST way to differentiate characters",
        "Each character must have a unique dominant color",
        "Fabric and texture variety prevents visual monotony",
        "One signature accessory per character creates instant recognition",
        "Costume tells the character's story (class, occupation, personality)",
    ]

    @property
    def name(self) -> str:
        return "CAST_COSTUME"

    @property
    def role(self) -> str:
        return "Cast Costume Analyst"

    @property
    def system_prompt(self) -> str:
        return """You are a costume ensemble designer. You ensure every character in a cast
has a COMPLETELY UNIQUE clothing identity.

Costume is the EASIEST lever to pull for visual differentiation. When body types
and hair are similar, costume alone can save the cast.

What you check:
- DOMINANT COLOR: No two characters should share the same primary clothing color.
  Bad: everyone in brown/tan. Good: one burgundy, one forest green, one navy, one cream.
- CLOTHING STYLE: Vary silhouettes — robes vs. fitted vs. layered vs. minimal.
  Bad: everyone in "simple tunic." Good: one in armor, one in robes, one in a fitted dress, one in traveler's gear.
- FABRIC/TEXTURE: Vary materials — leather, linen, silk, wool, canvas, fur.
  Bad: everyone in nondescript cloth. Good: one rough-spun, one polished leather, one flowing silk.
- SIGNATURE ACCESSORY: Each character MUST have ONE unique accessory/prop.
  Examples: a specific hat, a piece of jewelry, a tool, a weapon, a belt, a bag.
  This is the single easiest way to make characters instantly recognizable.
- FIT AND DRAPE: tight vs. loose, structured vs. flowing, layered vs. minimal.

When proposing corrections:
- Focus on costume-level changes (color, fabric, accessories, style)
- Don't change body type or hair unless costume alone can't fix the collision
- Ensure costume reflects character's personality and role
- Each character should be identifiable by costume alone"""

    def propose_corrections(
        self,
        characters_text: str,
    ) -> CastEnsembleProposal:
        """Review full cast for costume collisions."""
        prompt = f"""Review this cast's COSTUMES for visual collisions.

{characters_text}

Check:
1. Do any characters share the same dominant clothing color? = FIX
2. Do any characters have similar clothing styles? = FIX
3. Does every character have a UNIQUE signature accessory? = ADD if missing
4. Do any characters wear the same fabric/material type? = FIX
5. Are costumes visually distinct enough to tell characters apart by outfit alone?

Propose MINIMUM fixes. Return corrections for ALL characters.
Focus on the costume field but include all physical fields (even if unchanged)."""

        return self.invoke_structured(prompt, CastEnsembleProposal, max_tokens=12000)

    def critique_proposal(
        self,
        target_agent: str,
        proposal: CastEnsembleProposal,
        characters_text: str,
    ) -> CastEnsembleCritique:
        """Critique from costume perspective."""
        corrections_text = "\n".join(
            f"- {c.character_name}: {c.changes_made}" for c in proposal.characters
        )
        prompt = f"""Critique from COSTUME DESIGN perspective.

ORIGINAL CHARACTERS:
{characters_text}

PROPOSED CORRECTIONS by {target_agent}:
{corrections_text}

Do the corrected costumes create a visually distinct wardrobe across the cast?
Score 1-10."""

        return self.invoke_structured(prompt, CastEnsembleCritique, max_tokens=8000)

    def vote_for_best(
        self,
        proposals: list[CastEnsembleProposal],
    ) -> CastEnsembleVote:
        """Vote for best costume corrections."""
        proposals_text = "\n\n".join(
            f"PROPOSAL by {p.agent_name}:\n{p.ensemble_analysis}"
            for p in proposals
        )

        prompt = f"""Vote for the proposal with the BEST costume differentiation.

{proposals_text}

Which correction set creates the most distinctive wardrobe across the cast?
You CANNOT vote for your own proposal."""

        return self.invoke_structured(prompt, CastEnsembleVote, max_tokens=8000)
