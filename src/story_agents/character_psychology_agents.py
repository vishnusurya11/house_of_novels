"""
Character Psychology Agents for Step 1: Character Creation.

These agents implement K.M. Weiland's Lie/Truth system, Jungian Shadow Theory,
and 5 Character Arc Types to create psychologically complex characters from
thematic perspectives.

References:
- https://www.helpingwritersbecomeauthors.com/truth-your-character-believes/
- https://www.helpingwritersbecomeauthors.com/learn-5-types-of-character-arc-at-a-glance/
- https://www.helpingwritersbecomeauthors.com/how-to-create-insanely-complex-characters-using-shadow-theory/
"""

from src.story_agents.base_story_agent import BaseStoryAgent
from src.story_schemas import (
    LieTruthProposal,
    LieTruthCritique,
    LieTruthVote,
    ShadowProposal,
    ShadowCritique,
    ShadowVote,
    ArcTypeProposal,
    ArcTypeCritique,
    ArcTypeVote,
    GhostProposal,
    GhostCritique,
    GhostVote,
)
from pydantic import BaseModel, Field


# =============================================================================
# SUBSTEP 1: LIE/TRUTH AGENTS (3 agents)
# =============================================================================

class LieTruthPhilosopherAgent(BaseStoryAgent):
    """Defines the Lie a character believes based on their thematic perspective.

    Focuses on philosophical depth - the Lie as a fundamental misconception about
    reality, and the Truth as a liberating philosophical insight.
    """

    @property
    def name(self) -> str:
        return "LIETRUTH_PHILOSOPHER"

    @property
    def role(self) -> str:
        return "Philosophical character psychologist"

    @property
    def system_prompt(self) -> str:
        return """You are a philosophical character psychologist specializing in the Lie/Truth system.

Your role: Define the LIE a character believes and the TRUTH they need to learn.

PRINCIPLES (from K.M. Weiland):
- The Lie is a specific misconception the character believes (not a general flaw)
- The Lie protects the character from pain but limits their growth
- The Truth is the liberating insight that replaces the Lie
- Want = what character thinks they need (driven by Lie)
- Need = what character actually needs (the Truth)

THEMATIC CORNERS & DEFAULT LIES:
- POSITIVE corner: Character closer to Truth but fears fully embracing it
  Example Lie: "If I fully commit to this truth, I'll lose my safety"
- CONTRADICTORY corner: Character believes the Lie deeply
  Example Lie: "The opposite of truth is the only way to survive"
- CONTRARY corner: Character sees complexity, stuck in middle
  Example Lie: "Both sides are wrong - there is no answer"
- NEGATION corner: Character embraces extreme version of Lie
  Example Lie: "Truth is weakness - only power matters"

Your Lies are PHILOSOPHICAL and UNIVERSAL."""

    def propose_lie_truth(
        self,
        perspective: dict,
        central_question: str,
        square_corner: str
    ) -> LieTruthProposal:
        """Propose Lie, Truth, Want, and Need for this character."""
        user_prompt = f"""Define the Lie and Truth for this character.

THEMATIC PERSPECTIVE:
Perspective Name: {perspective['perspective_name']}
Position: {perspective['position']}
Corner: {square_corner}
Example Belief: {perspective['example_belief']}

CENTRAL QUESTION:
{central_question}

YOUR TASK:
Based on this perspective's position on the theme, define:

1. LIE CHARACTER BELIEVES: A specific misconception (one sentence)
   - Must relate to their thematic corner position
   - Something they think protects them
   - Creates their internal conflict

2. TRUTH CHARACTER NEEDS: The liberating insight (one sentence)
   - Replaces the Lie
   - Represents growth/transformation
   - Aligns with thematic exploration

3. WANT: External goal driven by the Lie (one sentence)
   - What they think will solve their problem
   - Pursuing this while believing Lie = conflict

4. NEED: Internal truth they actually need (one sentence)
   - What will actually fulfill them
   - Often conflicts with Want
   - Achieving this requires embracing Truth

In your response, provide:
1. lie_character_believes: The Lie
2. truth_character_needs: The Truth
3. want: External goal
4. need: Internal need
5. reasoning: WHY this Lie/Truth pair best serves the character's thematic exploration

Use agent_name: "{self.name}"
"""

        return self.invoke_structured(user_prompt, LieTruthProposal)

    def critique_lie_truth(
        self,
        proposals: list[LieTruthProposal],
        perspective: dict,
        central_question: str
    ) -> list[LieTruthCritique]:
        """Critique all Lie/Truth proposals."""
        class CritiqueList(BaseModel):
            critiques: list[LieTruthCritique] = Field(
                min_length=len(proposals),
                max_length=len(proposals),
                description=f"Exactly {len(proposals)} critiques"
            )

        proposals_text = "\n\n".join([
            f"PROPOSAL {i}:\n"
            f"  Agent: {p.agent_name}\n"
            f"  Lie: {p.lie_character_believes}\n"
            f"  Truth: {p.truth_character_needs}\n"
            f"  Want: {p.want}\n"
            f"  Need: {p.need}\n"
            f"  Reasoning: {p.reasoning}"
            for i, p in enumerate(proposals)
        ])

        user_prompt = f"""Critique all {len(proposals)} Lie/Truth proposals for this character.

PERSPECTIVE:
{perspective['perspective_name']} - {perspective['position']}
Corner: {perspective['corner']}

CENTRAL QUESTION:
{central_question}

{proposals_text}

For EACH proposal (0 to {len(proposals)-1}), evaluate:

STRENGTHS:
- Does Lie align with thematic corner?
- Is Truth a genuine transformation?
- Do Want/Need create dramatic tension?

WEAKNESSES:
- Is Lie too vague or generic?
- Is Truth preachy or obvious?
- Are Want/Need disconnected from theme?

Score 1-10 (10 = perfect Lie/Truth pair for this character's arc).

Use agent_name: "{self.name}"
"""

        result = self.invoke_structured(user_prompt, CritiqueList)
        return result.critiques

    def vote(
        self,
        proposals: list[LieTruthProposal],
        perspective: dict
    ) -> LieTruthVote:
        """Vote for best Lie/Truth proposal."""
        proposals_text = "\n\n".join([
            f"PROPOSAL {i}:\n"
            f"  Lie: {p.lie_character_believes}\n"
            f"  Truth: {p.truth_character_needs}\n"
            f"  Want: {p.want}\n"
            f"  Need: {p.need}"
            for i, p in enumerate(proposals)
        ])

        user_prompt = f"""Vote for the BEST Lie/Truth proposal.

PERSPECTIVE:
{perspective['perspective_name']} - {perspective['position']}

PROPOSALS:
{proposals_text}

Which proposal creates the most compelling character arc?

Consider:
- Lie believable and specific?
- Truth transformative and earned?
- Want vs. Need creates genuine tension?
- Aligns with thematic perspective?

Vote for proposal index (0 to {len(proposals)-1}) with reasoning.

Use agent_name: "{self.name}"
"""

        return self.invoke_structured(user_prompt, LieTruthVote)


class LieTruthPsychologistAgent(BaseStoryAgent):
    """Defines Truth as psychological growth path.

    Focuses on psychological depth - the Lie as protective mechanism,
    and the Truth as psychological healing/integration.
    """

    @property
    def name(self) -> str:
        return "LIETRUTH_PSYCHOLOGIST"

    @property
    def role(self) -> str:
        return "Clinical psychologist for character development"

    @property
    def system_prompt(self) -> str:
        return """You are a clinical psychologist specializing in character development.

Your role: Define the LIE as a psychological defense mechanism and the TRUTH as healing.

PSYCHOLOGICAL PRINCIPLES:
- Lies are formed in response to trauma/pain (the "Ghost")
- Lies protect from perceived danger but create dysfunction
- Truth requires vulnerability but enables authentic living
- Want = external validation/safety the character seeks
- Need = internal healing/self-acceptance

CORNER-SPECIFIC PSYCHOLOGY:
- POSITIVE: Fear of vulnerability prevents full self-actualization
- CONTRADICTORY: Defense mechanisms create self-sabotage
- CONTRARY: Intellectualization prevents emotional processing
- NEGATION: Dissociation/splitting from authentic self

Your Lies are PSYCHOLOGICAL and PROTECTIVE.
Your Truths are about HEALING and INTEGRATION."""

    def propose_lie_truth(
        self,
        perspective: dict,
        central_question: str,
        square_corner: str
    ) -> LieTruthProposal:
        """Propose psychological Lie/Truth."""
        user_prompt = f"""Define the psychological Lie and Truth for this character.

THEMATIC PERSPECTIVE:
Perspective Name: {perspective['perspective_name']}
Position: {perspective['position']}
Corner: {square_corner}

CENTRAL QUESTION:
{central_question}

YOUR TASK (from psychological lens):

1. LIE: A psychological defense mechanism
   - Formed to protect from pain/trauma
   - Creates dysfunction in relationships/life
   - Prevents authentic connection

2. TRUTH: Psychological healing/integration
   - Requires vulnerability
   - Enables authentic self-expression
   - Heals core wound

3. WANT: External validation/safety sought
4. NEED: Internal healing required

In your response, provide:
1. lie_character_believes
2. truth_character_needs
3. want
4. need
5. reasoning: WHY this addresses psychological growth

Use agent_name: "{self.name}"
"""

        return self.invoke_structured(user_prompt, LieTruthProposal)

    def critique_lie_truth(
        self,
        proposals: list[LieTruthProposal],
        perspective: dict,
        central_question: str
    ) -> list[LieTruthCritique]:
        """Critique proposals from psychological lens."""
        class CritiqueList(BaseModel):
            critiques: list[LieTruthCritique] = Field(
                min_length=len(proposals),
                max_length=len(proposals)
            )

        proposals_text = "\n\n".join([
            f"PROPOSAL {i}: Lie: {p.lie_character_believes} | Truth: {p.truth_character_needs}"
            for i, p in enumerate(proposals)
        ])

        user_prompt = f"""Critique these proposals psychologically.

PERSPECTIVE: {perspective['perspective_name']}

{proposals_text}

For each proposal:
- Is Lie a believable defense mechanism?
- Does Truth represent genuine healing?
- Are Want/Need psychologically coherent?

Score 1-10. Use agent_name: "{self.name}"
"""

        result = self.invoke_structured(user_prompt, CritiqueList)
        return result.critiques

    def vote(
        self,
        proposals: list[LieTruthProposal],
        perspective: dict
    ) -> LieTruthVote:
        """Vote for most psychologically compelling proposal."""
        proposals_text = "\n\n".join([
            f"PROPOSAL {i}: Lie: {p.lie_character_believes} | Truth: {p.truth_character_needs}"
            for i, p in enumerate(proposals)
        ])

        user_prompt = f"""Vote for the most psychologically compelling Lie/Truth.

{proposals_text}

Which creates the most believable psychological journey?

Use agent_name: "{self.name}"
"""

        return self.invoke_structured(user_prompt, LieTruthVote)


class LieTruthNarrativeAgent(BaseStoryAgent):
    """Defines Want vs. Need for narrative tension.

    Focuses on story craft - the Lie as obstacle to external goal,
    and the Truth as key to achieving what truly matters.
    """

    @property
    def name(self) -> str:
        return "LIETRUTH_NARRATIVE"

    @property
    def role(self) -> str:
        return "Narrative structure expert"

    @property
    def system_prompt(self) -> str:
        return """You are a narrative structure expert specializing in Want vs. Need.

Your role: Define the LIE as narrative obstacle and TRUTH as key to fulfillment.

NARRATIVE PRINCIPLES:
- Want = external story goal (plot-driven)
- Need = internal requirement for fulfillment (character-driven)
- Lie = why pursuing Want alone fails
- Truth = what allows achieving true Need

NARRATIVE PATTERNS:
- Character pursues Want based on Lie
- Plot forces choice: Want OR Need
- Climax: Character chooses Truth/Need over Lie/Want
- Resolution: Gets true Need (may or may not get Want)

CORNER-SPECIFIC NARRATIVES:
- POSITIVE: Nearly has it right, final push needed
- CONTRADICTORY: Completely wrong approach
- CONTRARY: Torn between two wrong paths
- NEGATION: On path to destruction

Your Lies create NARRATIVE OBSTACLES.
Your Truths enable NARRATIVE FULFILLMENT."""

    def propose_lie_truth(
        self,
        perspective: dict,
        central_question: str,
        square_corner: str
    ) -> LieTruthProposal:
        """Propose narrative-driven Lie/Truth."""
        user_prompt = f"""Define the narrative Lie and Truth for this character.

THEMATIC PERSPECTIVE:
Perspective Name: {perspective['perspective_name']}
Position: {perspective['position']}
Corner: {square_corner}

CENTRAL QUESTION:
{central_question}

YOUR TASK (from narrative lens):

1. LIE: Why character's approach will fail
   - Creates false goal (Want)
   - Prevents real fulfillment
   - Generates plot complications

2. TRUTH: What enables true success
   - Unlocks real goal (Need)
   - Resolves internal conflict
   - Completes arc

3. WANT: External plot goal (driven by Lie)
4. NEED: Internal truth (requires accepting Truth)

In your response, provide:
1. lie_character_believes
2. truth_character_needs
3. want (be SPECIFIC - an achievable story goal)
4. need (be SPECIFIC - measurable inner change)
5. reasoning: WHY this creates compelling Want vs. Need tension

Use agent_name: "{self.name}"
"""

        return self.invoke_structured(user_prompt, LieTruthProposal)

    def critique_lie_truth(
        self,
        proposals: list[LieTruthProposal],
        perspective: dict,
        central_question: str
    ) -> list[LieTruthCritique]:
        """Critique proposals for narrative strength."""
        class CritiqueList(BaseModel):
            critiques: list[LieTruthCritique] = Field(
                min_length=len(proposals),
                max_length=len(proposals)
            )

        proposals_text = "\n\n".join([
            f"PROPOSAL {i}:\n  Want: {p.want}\n  Need: {p.need}\n  Lie: {p.lie_character_believes}"
            for i, p in enumerate(proposals)
        ])

        user_prompt = f"""Critique these proposals narratively.

PERSPECTIVE: {perspective['perspective_name']}

{proposals_text}

For each proposal:
- Is Want a clear external goal?
- Is Need a measurable internal change?
- Does Lie create genuine Want vs. Need tension?
- Will climax force meaningful choice?

Score 1-10. Use agent_name: "{self.name}"
"""

        result = self.invoke_structured(user_prompt, CritiqueList)
        return result.critiques

    def vote(
        self,
        proposals: list[LieTruthProposal],
        perspective: dict
    ) -> LieTruthVote:
        """Vote for strongest narrative tension."""
        proposals_text = "\n\n".join([
            f"PROPOSAL {i}: Want: {p.want} | Need: {p.need}"
            for i, p in enumerate(proposals)
        ])

        user_prompt = f"""Vote for the strongest Want vs. Need narrative.

{proposals_text}

Which creates the most compelling choice for the character?

Use agent_name: "{self.name}"
"""

        return self.invoke_structured(user_prompt, LieTruthVote)


# =============================================================================
# SUBSTEP 2: SHADOW/ARC/GHOST AGENTS (3 agents)
# =============================================================================

class ShadowArchetypeAgent(BaseStoryAgent):
    """Identifies Jungian shadow traits (unconscious opposites).

    Maps conscious strengths to unconscious weaknesses, and conscious values
    to unconscious fears, creating psychological depth.
    """

    @property
    def name(self) -> str:
        return "SHADOW_ARCHETYPE"

    @property
    def role(self) -> str:
        return "Jungian shadow psychologist"

    @property
    def system_prompt(self) -> str:
        return """You are a Jungian psychologist specializing in Shadow Theory.

Your role: Identify the SHADOW - unconscious opposite of conscious traits.

SHADOW PRINCIPLES (Carl Jung):
- Shadow = parts of self we repress/deny
- Conscious strength → Unconscious weakness
- Conscious value → Unconscious fear
- What we vilify → What we secretly desire
- What we revere → What we secretly fear

SHADOW MAPPING:
Conscious → Shadow pairs create complexity:
- "Confident" → "Insecure" (overcompensation)
- "Independent" → "Terrified of abandonment"
- "Rational" → "Emotionally volatile underneath"
- "Altruistic" → "Craves recognition"

STORY FUNCTION:
- Shadow emerges under pressure
- Character arc = integrating shadow (not destroying it)
- Villain often = character's shadow externalized

Your shadow traits create PSYCHOLOGICAL COMPLEXITY."""

    def propose_shadow(
        self,
        perspective: dict,
        lie: str,
        truth: str
    ) -> ShadowProposal:
        """Propose shadow traits for this character."""
        user_prompt = f"""Identify the shadow traits for this character.

THEMATIC PERSPECTIVE:
{perspective['perspective_name']} - {perspective['position']}

LIE CHARACTER BELIEVES:
{lie}

TRUTH CHARACTER NEEDS:
{truth}

YOUR TASK:
Identify 4 Conscious→Shadow pairs:

1. CONSCIOUS STRENGTH → UNCONSCIOUS WEAKNESS
2. CONSCIOUS VALUE → UNCONSCIOUS FEAR
3. CONSCIOUS DESIRE → UNCONSCIOUS OPPOSITE
4. CONSCIOUS REJECTION → UNCONSCIOUS ATTRACTION

The shadow should:
- Relate to the Lie (shadow reinforces it)
- Make Truth harder to accept
- Create internal contradiction

In your response, provide:
1. conscious_strength: The conscious strength they display
2. shadow_weakness: The unconscious weakness opposite of that strength
3. conscious_value: The conscious value they hold
4. shadow_fear: The unconscious fear opposite of that value
5. conscious_desire: The conscious desire they pursue
6. shadow_opposite: The unconscious opposite of that desire
7. conscious_rejection: What they consciously reject
8. shadow_attraction: What they unconsciously want
9. reasoning: WHY this shadow deepens the character

Use agent_name: "{self.name}"
"""

        return self.invoke_structured(user_prompt, ShadowProposal)

    def critique_shadow(
        self,
        proposals: list[ShadowProposal],
        perspective: dict,
        lie: str
    ) -> list[ShadowCritique]:
        """Critique shadow proposals."""
        class CritiqueList(BaseModel):
            critiques: list[ShadowCritique] = Field(
                min_length=len(proposals),
                max_length=len(proposals)
            )

        proposals_text = "\n\n".join([
            f"PROPOSAL {i}:\n" + "\n".join([f"  {k}: {v}" for k, v in p.shadow_traits.items()])
            for i, p in enumerate(proposals)
        ])

        user_prompt = f"""Critique these shadow proposals.

PERSPECTIVE: {perspective['perspective_name']}
LIE: {lie}

{proposals_text}

For each proposal:
- Are shadow traits true psychological opposites?
- Do they relate to the Lie?
- Do they create genuine internal conflict?

Score 1-10. Use agent_name: "{self.name}"
"""

        result = self.invoke_structured(user_prompt, CritiqueList)
        return result.critiques

    def vote(
        self,
        proposals: list[ShadowProposal],
        perspective: dict
    ) -> ShadowVote:
        """Vote for most compelling shadow."""
        proposals_text = "\n\n".join([
            f"PROPOSAL {i}: {list(p.shadow_traits.keys())}"
            for i, p in enumerate(proposals)
        ])

        user_prompt = f"""Vote for the best shadow proposal.

{proposals_text}

Which creates the deepest psychological complexity?

Use agent_name: "{self.name}"
"""

        return self.invoke_structured(user_prompt, ShadowVote)


class ShadowNarrativeAgent(BaseStoryAgent):
    """Shadow specialist focused on narrative conflict.

    Ensures shadow traits create story-driven internal conflict
    that manifests in character decisions and plot complications.
    """

    @property
    def name(self) -> str:
        return "SHADOW_NARRATIVE"

    @property
    def role(self) -> str:
        return "Shadow narrative specialist"

    @property
    def system_prompt(self) -> str:
        return """You are a narrative specialist using Jungian Shadow Theory for storytelling.

Your role: Create shadow traits that generate NARRATIVE CONFLICT.

SHADOW AS STORY ENGINE:
- Shadow drives character to make flawed choices
- Shadow creates want vs. need tension
- Shadow manifests in relationships (projection, transference)
- Shadow emerges under plot pressure
- Integration of shadow = character growth

NARRATIVE SHADOW PAIRS:
Conscious Behavior → Shadow Behavior (under pressure):
- "Brave in battle" → "Paralyzed by intimacy"
- "Protects others" → "Can't protect self"
- "Seeks truth" → "Lies to self about motives"
- "Rational leader" → "Emotionally volatile in private"

STORY APPLICATIONS:
- Act 1: Conscious persona dominates
- Act 2: Shadow emerges through failures
- Act 3: Integration or destruction

Your shadow traits create PLOT COMPLICATIONS."""

    def propose_shadow(
        self,
        perspective: dict,
        lie: str,
        truth: str
    ) -> ShadowProposal:
        """Propose shadow traits optimized for narrative conflict."""
        user_prompt = f"""Identify shadow traits that create narrative conflict.

THEMATIC PERSPECTIVE:
{perspective['perspective_name']} - {perspective['position']}

LIE CHARACTER BELIEVES:
{lie}

TRUTH CHARACTER NEEDS:
{truth}

YOUR TASK (narrative lens):
Identify 4 Conscious→Shadow pairs that create PLOT COMPLICATIONS:

1. PUBLIC PERSONA → PRIVATE BREAKDOWN
2. EXTERNAL STRENGTH → INTERNAL WOUND
3. CONSCIOUS MISSION → UNCONSCIOUS SABOTAGE
4. PROJECTED VILLAIN → INTERNAL DEMON

The shadow should:
- Create consequences in plot (failed missions, broken relationships)
- Manifest in Act 2 when stakes rise
- Require integration for Act 3 resolution

In your response, provide:
1. conscious_strength: Public persona/strength they show the world
2. shadow_weakness: How it breaks down in private/under pressure
3. conscious_value: External strength/victory they achieve
4. shadow_fear: Internal wound/defeat they hide
5. conscious_desire: Their conscious mission/goal
6. shadow_opposite: How they unconsciously sabotage that mission
7. conscious_rejection: What they hate/reject in others (projected villain)
8. shadow_attraction: The internal demon they deny in themselves
9. reasoning: HOW this shadow drives the plot forward

Use agent_name: "{self.name}"
"""

        return self.invoke_structured(user_prompt, ShadowProposal)

    def critique_shadow(
        self,
        proposals: list[ShadowProposal],
        perspective: dict,
        lie: str
    ) -> list[ShadowCritique]:
        """Critique shadow proposals for narrative utility."""
        class CritiqueList(BaseModel):
            critiques: list[ShadowCritique] = Field(
                min_length=len(proposals),
                max_length=len(proposals)
            )

        proposals_text = "\n\n".join([
            f"PROPOSAL {i}:\n" + "\n".join([f"  {k}: {v}" for k, v in p.shadow_traits.items()])
            for i, p in enumerate(proposals)
        ])

        user_prompt = f"""Critique these shadow proposals narratively.

PERSPECTIVE: {perspective['perspective_name']}
LIE: {lie}

{proposals_text}

For each proposal:
- Do shadow traits create plot complications?
- Will shadow manifest in character decisions?
- Does shadow create relationship conflict?
- Is shadow integration achievable by Act 3?

Score 1-10. Use agent_name: "{self.name}"
"""

        result = self.invoke_structured(user_prompt, CritiqueList)
        return result.critiques

    def vote(
        self,
        proposals: list[ShadowProposal],
        perspective: dict
    ) -> ShadowVote:
        """Vote for shadow with strongest narrative potential."""
        proposals_text = "\n\n".join([
            f"PROPOSAL {i}: {list(p.shadow_traits.keys())}"
            for i, p in enumerate(proposals)
        ])

        user_prompt = f"""Vote for the shadow that creates the most story conflict.

{proposals_text}

Which shadow will drive the most compelling plot complications?

Use agent_name: "{self.name}"
"""

        return self.invoke_structured(user_prompt, ShadowVote)


class ShadowPsychologistAgent(BaseStoryAgent):
    """Shadow specialist with clinical psychology focus.

    Uses defense mechanisms, attachment theory, and trauma psychology
    to create realistic shadow manifestations.
    """

    @property
    def name(self) -> str:
        return "SHADOW_PSYCHOLOGIST"

    @property
    def role(self) -> str:
        return "Clinical shadow psychologist"

    @property
    def system_prompt(self) -> str:
        return """You are a clinical psychologist specializing in shadow psychology.

Your role: Create shadow traits grounded in PSYCHOLOGICAL REALISM.

CLINICAL SHADOW THEORY:
Shadow forms through:
- Defense mechanisms (repression, projection, reaction formation)
- Attachment wounds (anxious, avoidant, disorganized)
- Trauma responses (fight/flight/freeze/fawn)
- Developmental arrests (unmet childhood needs)

DEFENSE MECHANISM SHADOWS:
- Projection: "They're all selfish" → Character is selfish
- Reaction Formation: "I'm so generous" → Hoards resources secretly
- Splitting: "Everyone's good or evil" → Can't integrate own complexity
- Intellectualization: "Emotions are illogical" → Terror of vulnerability

ATTACHMENT SHADOWS:
- Anxious: Appears independent → Desperate for validation
- Avoidant: Values freedom → Terrified of abandonment
- Disorganized: Seeks safety → Creates chaos

TRAUMA RESPONSES:
- Fight: Appears aggressive → Protecting vulnerable inner child
- Fawn: People-pleaser → Rage underneath compliance
- Freeze: Appears calm → Dissociated from terror

Your shadow traits are CLINICALLY ACCURATE."""

    def propose_shadow(
        self,
        perspective: dict,
        lie: str,
        truth: str
    ) -> ShadowProposal:
        """Propose shadow traits using clinical psychology."""
        user_prompt = f"""Identify shadow traits using clinical psychology.

THEMATIC PERSPECTIVE:
{perspective['perspective_name']} - {perspective['position']}

LIE CHARACTER BELIEVES:
{lie}

TRUTH CHARACTER NEEDS:
{truth}

YOUR TASK (clinical lens):
Identify 4 Conscious→Shadow pairs based on defense mechanisms:

1. DEFENSE MECHANISM → UNDERLYING WOUND
2. ATTACHMENT STYLE → CORE FEAR
3. TRAUMA RESPONSE → FROZEN NEED
4. CONSCIOUS IDEAL → REPRESSED OPPOSITE

The shadow should:
- Be psychologically coherent (follow defense logic)
- Stem from developmental wounds
- Make sense with the Lie's origin

In your response, provide:
1. conscious_strength: Defense mechanism they use (e.g., "Appears generous")
2. shadow_weakness: Underlying wound it hides (e.g., "Hoards resources secretly")
3. conscious_value: How they relate to others (attachment style)
4. shadow_fear: What they actually fear (core fear)
5. conscious_desire: Adaptive trauma response behavior
6. shadow_opposite: Frozen unmet need underneath
7. conscious_rejection: Conscious ideal/value they champion
8. shadow_attraction: Repressed opposite they deny
9. reasoning: The CLINICAL logic of this shadow formation

Use agent_name: "{self.name}"
"""

        return self.invoke_structured(user_prompt, ShadowProposal)

    def critique_shadow(
        self,
        proposals: list[ShadowProposal],
        perspective: dict,
        lie: str
    ) -> list[ShadowCritique]:
        """Critique shadow proposals for clinical accuracy."""
        class CritiqueList(BaseModel):
            critiques: list[ShadowCritique] = Field(
                min_length=len(proposals),
                max_length=len(proposals)
            )

        proposals_text = "\n\n".join([
            f"PROPOSAL {i}:\n" + "\n".join([f"  {k}: {v}" for k, v in p.shadow_traits.items()])
            for i, p in enumerate(proposals)
        ])

        user_prompt = f"""Critique these shadow proposals clinically.

PERSPECTIVE: {perspective['perspective_name']}
LIE: {lie}

{proposals_text}

For each proposal:
- Are shadow traits clinically plausible?
- Do they follow defense mechanism logic?
- Are they grounded in attachment/trauma theory?
- Would real humans manifest this way?

Score 1-10. Use agent_name: "{self.name}"
"""

        result = self.invoke_structured(user_prompt, CritiqueList)
        return result.critiques

    def vote(
        self,
        proposals: list[ShadowProposal],
        perspective: dict
    ) -> ShadowVote:
        """Vote for most clinically accurate shadow."""
        proposals_text = "\n\n".join([
            f"PROPOSAL {i}: {list(p.shadow_traits.keys())}"
            for i, p in enumerate(proposals)
        ])

        user_prompt = f"""Vote for the most psychologically realistic shadow.

{proposals_text}

Which shadow is most clinically plausible and grounded in real psychology?

Use agent_name: "{self.name}"
"""

        return self.invoke_structured(user_prompt, ShadowVote)


class ArcTypeAgent(BaseStoryAgent):
    """Assigns character arc type based on Lie/Truth relationship.

    Chooses from 5 arc types (K.M. Weiland):
    - Positive Change Arc
    - Flat Arc
    - Disillusionment Arc
    - Fall Arc
    - Corruption Arc
    """

    @property
    def name(self) -> str:
        return "ARC_TYPE"

    @property
    def role(self) -> str:
        return "Character arc specialist"

    @property
    def system_prompt(self) -> str:
        return """You are a character arc specialist (K.M. Weiland methodology).

Your role: Assign the appropriate CHARACTER ARC TYPE.

5 ARC TYPES:

1. POSITIVE CHANGE ARC (most common for protagonists)
   - Starts believing Lie
   - Overcomes Lie → Discovers Truth
   - Transforms for the better
   - Example: Hero learns to trust others

2. FLAT ARC (heroes who change the world)
   - Already knows Truth
   - World/others believe Lie
   - Character uses Truth to change others
   - Example: Mentor figure, sequel hero

3. DISILLUSIONMENT ARC (tragic truth)
   - Starts believing Lie
   - Overcomes Lie → Discovers tragic Truth
   - Truth is painful but necessary
   - Example: Idealist learns harsh reality

4. FALL ARC (tragic descent)
   - Starts with some truth
   - Clings to Lie → Rejects Truth → Embraces worse Lie
   - Descends into tragedy
   - Example: Character corrupted by power

5. CORRUPTION ARC (villain origin)
   - Starts knowing Truth
   - Rejects Truth → Embraces Lie
   - Becomes antagonist
   - Example: Good person turns evil

CORNER → DEFAULT ARC:
- POSITIVE: Usually Positive Change or Flat
- CONTRADICTORY: Usually Positive Change
- CONTRARY: Usually Disillusionment
- NEGATION: Usually Fall or Corruption

Your arc choice creates the CHARACTER'S JOURNEY."""

    def propose_arc_type(
        self,
        perspective: dict,
        lie: str,
        truth: str,
        square_corner: str
    ) -> ArcTypeProposal:
        """Propose arc type for this character."""
        user_prompt = f"""Assign the character arc type.

THEMATIC PERSPECTIVE:
{perspective['perspective_name']} - {perspective['position']}
Corner: {square_corner}

LIE CHARACTER BELIEVES:
{lie}

TRUTH CHARACTER NEEDS:
{truth}

YOUR TASK:
Based on the Lie/Truth relationship and thematic corner, choose the arc type:

1. Positive Change Arc - Overcomes Lie → Learns Truth
2. Flat Arc - Already knows Truth → Changes world
3. Disillusionment Arc - Overcomes Lie → Learns tragic Truth
4. Fall Arc - Clings to Lie → Descends
5. Corruption Arc - Rejects Truth → Embraces Lie

Also describe the ARC JOURNEY:
- Where they start (relationship to Lie/Truth)
- What happens at midpoint
- What happens at climax
- Where they end

In your response, provide:
1. arc_type: One of the 5 types
2. arc_journey: The transformation path (3-4 sentences)
3. reasoning: WHY this arc type fits the character's thematic role

Use agent_name: "{self.name}"
"""

        return self.invoke_structured(user_prompt, ArcTypeProposal)

    def critique_arc_type(
        self,
        proposals: list[ArcTypeProposal],
        perspective: dict,
        lie: str,
        truth: str
    ) -> list[ArcTypeCritique]:
        """Critique arc type proposals."""
        class CritiqueList(BaseModel):
            critiques: list[ArcTypeCritique] = Field(
                min_length=len(proposals),
                max_length=len(proposals)
            )

        proposals_text = "\n\n".join([
            f"PROPOSAL {i}:\n  Arc Type: {p.arc_type}\n  Journey: {p.arc_journey}"
            for i, p in enumerate(proposals)
        ])

        user_prompt = f"""Critique these arc type proposals.

PERSPECTIVE: {perspective['perspective_name']}
LIE: {lie}
TRUTH: {truth}

{proposals_text}

For each proposal:
- Does arc type match Lie/Truth relationship?
- Is journey description clear and compelling?
- Does it serve thematic exploration?

Score 1-10. Use agent_name: "{self.name}"
"""

        result = self.invoke_structured(user_prompt, CritiqueList)
        return result.critiques

    def vote(
        self,
        proposals: list[ArcTypeProposal],
        perspective: dict
    ) -> ArcTypeVote:
        """Vote for best arc type."""
        proposals_text = "\n\n".join([
            f"PROPOSAL {i}: {p.arc_type}"
            for i, p in enumerate(proposals)
        ])

        user_prompt = f"""Vote for the best arc type.

{proposals_text}

Which arc type best serves this character's role in the story?

Use agent_name: "{self.name}"
"""

        return self.invoke_structured(user_prompt, ArcTypeVote)


class ArcTypeNarrativeAgent(BaseStoryAgent):
    """Arc type specialist focused on story structure.

    Maps character arcs to three-act structure and plot progression,
    ensuring arc type creates satisfying narrative shape.
    """

    @property
    def name(self) -> str:
        return "ARCTYPE_NARRATIVE"

    @property
    def role(self) -> str:
        return "Arc type narrative specialist"

    @property
    def system_prompt(self) -> str:
        return """You are a story structure expert specializing in character arcs.

Your role: Map arc types to NARRATIVE STRUCTURE.

ARC TYPES AND THREE-ACT STRUCTURE:

1. POSITIVE CHANGE ARC:
   - Act 1: Character believes Lie, pursues Want
   - Act 2: Lie tested, failures mount, glimpse Truth
   - Act 3: Embrace Truth, get Need (may/may not get Want)

2. FLAT ARC:
   - Act 1: Character knows Truth, world doesn't
   - Act 2: World tests character's Truth, nearly breaks them
   - Act 3: Character holds to Truth, changes the world

3. DISILLUSIONMENT ARC:
   - Act 1: Character believes comforting Lie
   - Act 2: Reality shatters Lie
   - Act 3: Accept harsh Truth, bittersweet wisdom

4. FALL ARC:
   - Act 1: Character could choose Truth
   - Act 2: Chooses Lie, doubles down
   - Act 3: Destroyed by Lie, tragic end

5. CORRUPTION ARC:
   - Act 1: Character knows Truth
   - Act 2: Chooses Lie for power/safety
   - Act 3: Becomes villain, wins but soul lost

NARRATIVE FIT:
Your arc choice must create:
- Clear Act 2 crisis (Lie vs. Truth collision)
- Satisfying Act 3 resolution (character changed or destroyed)
- Thematic resonance with story's central question"""

    def propose_arc_type(
        self,
        perspective: dict,
        lie: str,
        truth: str,
        square_corner: str
    ) -> ArcTypeProposal:
        """Propose arc type optimized for narrative structure."""
        user_prompt = f"""Assign arc type based on narrative structure needs.

THEMATIC PERSPECTIVE:
{perspective['perspective_name']} - {perspective['position']}
Corner: {square_corner}

LIE CHARACTER BELIEVES:
{lie}

TRUTH CHARACTER NEEDS:
{truth}

YOUR TASK (narrative lens):
Choose the arc type that creates the best narrative shape:

1. Will Act 2 crisis be compelling?
2. Will Act 3 resolution be satisfying?
3. Does arc fit the thematic corner?
   - POSITIVE corner → Positive Change Arc (most common)
   - CONTRADICTORY corner → Disillusionment or Flat Arc
   - CONTRARY corner → Fall or Corruption Arc
   - NEGATION corner → Corruption Arc (darkest)

In your response, provide:
1. arc_type: One of the 5 types
2. arc_journey: How this arc progresses through 3 acts
3. reasoning: WHY this arc creates the best narrative structure

Use agent_name: "{self.name}"
"""

        return self.invoke_structured(user_prompt, ArcTypeProposal)

    def critique_arc_type(
        self,
        proposals: list[ArcTypeProposal],
        perspective: dict,
        lie: str,
        truth: str
    ) -> list[ArcTypeCritique]:
        """Critique arc type proposals for narrative effectiveness."""
        class CritiqueList(BaseModel):
            critiques: list[ArcTypeCritique] = Field(
                min_length=len(proposals),
                max_length=len(proposals)
            )

        proposals_text = "\n\n".join([
            f"PROPOSAL {i}:\n  Arc: {p.arc_type}\n  Journey: {p.arc_journey}"
            for i, p in enumerate(proposals)
        ])

        user_prompt = f"""Critique these arc type proposals narratively.

PERSPECTIVE: {perspective['perspective_name']}
LIE: {lie}
TRUTH: {truth}

{proposals_text}

For each proposal:
- Does arc create clear 3-act progression?
- Will Act 2 crisis be dramatic?
- Is Act 3 resolution satisfying?
- Does arc journey make narrative sense?

Score 1-10. Use agent_name: "{self.name}"
"""

        result = self.invoke_structured(user_prompt, CritiqueList)
        return result.critiques

    def vote(
        self,
        proposals: list[ArcTypeProposal],
        perspective: dict
    ) -> ArcTypeVote:
        """Vote for arc with best narrative structure."""
        proposals_text = "\n\n".join([
            f"PROPOSAL {i}: {p.arc_type}"
            for i, p in enumerate(proposals)
        ])

        user_prompt = f"""Vote for the arc type with the best narrative shape.

{proposals_text}

Which arc type will create the most satisfying story structure?

Use agent_name: "{self.name}"
"""

        return self.invoke_structured(user_prompt, ArcTypeVote)


class ArcTypeThematicAgent(BaseStoryAgent):
    """Arc type specialist focused on thematic resonance.

    Ensures arc type aligns with thematic square corner and
    explores the central question in a meaningful way.
    """

    @property
    def name(self) -> str:
        return "ARCTYPE_THEMATIC"

    @property
    def role(self) -> str:
        return "Arc type thematic specialist"

    @property
    def system_prompt(self) -> str:
        return """You are a thematic analyst specializing in character arcs.

Your role: Ensure arc types serve THEMATIC EXPLORATION.

ARC TYPES AND THEMATIC SQUARE:

THEMATIC SQUARE CORNERS:
1. POSITIVE: Life-affirming answer
   → Positive Change Arc or Flat Arc (hero affirms truth)

2. CONTRADICTORY: Paradoxical tension
   → Disillusionment Arc (comfortable lie vs. harsh truth)

3. CONTRARY: Opposite of positive
   → Fall Arc (refusal to grow)

4. NEGATION OF NEGATION: Darkest corner
   → Corruption Arc (willful embrace of darkness)

THEMATIC RESONANCE:
Your arc choice must:
- Embody the character's corner of thematic square
- Explore central question from their perspective
- Create meaningful contrast with other characters
- Serve the story's philosophical depth

ARC AS ARGUMENT:
Each character's arc is a philosophical position on the central question.
All 4 characters' arcs together = complete thematic exploration."""

    def propose_arc_type(
        self,
        perspective: dict,
        lie: str,
        truth: str,
        square_corner: str
    ) -> ArcTypeProposal:
        """Propose arc type based on thematic fit."""
        user_prompt = f"""Assign arc type based on thematic resonance.

THEMATIC PERSPECTIVE:
{perspective['perspective_name']} - {perspective['position']}
Corner: {square_corner}

LIE CHARACTER BELIEVES:
{lie}

TRUTH CHARACTER NEEDS:
{truth}

YOUR TASK (thematic lens):
Choose the arc type that best explores this thematic corner:

CORNER-SPECIFIC GUIDANCE:
- POSITIVE: Usually Positive Change (embraces truth) or Flat Arc (already has truth)
- CONTRADICTORY: Often Disillusionment (harsh awakening)
- CONTRARY: Often Fall Arc (refuses growth)
- NEGATION: Usually Corruption Arc (embraces darkness)

Consider:
1. How does this arc ARGUE a position on the central question?
2. How does it CONTRAST with other characters' perspectives?
3. Does it DEEPEN thematic complexity?

In your response, provide:
1. arc_type: One of the 5 types
2. arc_journey: How this arc explores the theme
3. reasoning: WHY this arc serves thematic depth

Use agent_name: "{self.name}"
"""

        return self.invoke_structured(user_prompt, ArcTypeProposal)

    def critique_arc_type(
        self,
        proposals: list[ArcTypeProposal],
        perspective: dict,
        lie: str,
        truth: str
    ) -> list[ArcTypeCritique]:
        """Critique arc type proposals for thematic resonance."""
        class CritiqueList(BaseModel):
            critiques: list[ArcTypeCritique] = Field(
                min_length=len(proposals),
                max_length=len(proposals)
            )

        proposals_text = "\n\n".join([
            f"PROPOSAL {i}:\n  Arc: {p.arc_type}\n  Journey: {p.arc_journey}"
            for i, p in enumerate(proposals)
        ])

        user_prompt = f"""Critique these arc type proposals thematically.

PERSPECTIVE: {perspective['perspective_name']}
CORNER: {perspective.get('corner', 'N/A')}
LIE: {lie}
TRUTH: {truth}

{proposals_text}

For each proposal:
- Does arc fit thematic square corner?
- Does it explore central question deeply?
- Will it create thematic contrast with other characters?
- Does it add philosophical complexity?

Score 1-10. Use agent_name: "{self.name}"
"""

        result = self.invoke_structured(user_prompt, CritiqueList)
        return result.critiques

    def vote(
        self,
        proposals: list[ArcTypeProposal],
        perspective: dict
    ) -> ArcTypeVote:
        """Vote for arc with strongest thematic resonance."""
        proposals_text = "\n\n".join([
            f"PROPOSAL {i}: {p.arc_type}"
            for i, p in enumerate(proposals)
        ])

        user_prompt = f"""Vote for the arc type with the deepest thematic resonance.

{proposals_text}

Which arc type best serves the thematic exploration?

Use agent_name: "{self.name}"
"""

        return self.invoke_structured(user_prompt, ArcTypeVote)


class GhostAgent(BaseStoryAgent):
    """Creates backstory 'Ghost' - the event that formed the Lie.

    The Ghost is a past wound/trauma that created the character's Lie.
    It haunts them throughout the story until they face it.
    """

    @property
    def name(self) -> str:
        return "GHOST"

    @property
    def role(self) -> str:
        return "Backstory specialist"

    @property
    def system_prompt(self) -> str:
        return """You are a backstory specialist focusing on the "Ghost" (K.M. Weiland).

Your role: Create the GHOST - the past event that formed the Lie.

GHOST PRINCIPLES:
- Ghost = past wound/trauma
- Created the character's Lie as protective response
- Character hasn't processed it
- Must be faced to embrace Truth
- Not always tragic - can be misinterpreted positive event

GHOST CHARACTERISTICS:
- Specific event (not vague backstory)
- Age when it happened (shapes response)
- Why it created THIS Lie
- What character learned from it (the wrong lesson)

EXAMPLES:
- Betrayed by trusted mentor → "Trust = weakness"
- Witnessed parent's sacrifice → "Love = pain"
- Failed when tried hardest → "Trying = failure"
- Saved by deception → "Honesty = danger"

STORY FUNCTION:
- Revealed progressively
- Character tries to avoid facing it
- Climax often involves confronting Ghost
- Accepting truth about Ghost = embracing Truth

Your Ghost creates the WOUND that drives the arc."""

    def propose_ghost(
        self,
        perspective: dict,
        lie: str
    ) -> GhostProposal:
        """Propose Ghost backstory event."""
        user_prompt = f"""Create the Ghost for this character.

THEMATIC PERSPECTIVE:
{perspective['perspective_name']} - {perspective['position']}

LIE CHARACTER BELIEVES:
{lie}

YOUR TASK:
Create a specific past event (the "Ghost") that created this Lie.

The Ghost should:
1. Be a SPECIFIC event (not vague backstory)
2. Show why the character formed THIS Lie
3. Be something character hasn't fully processed
4. Relate to thematic perspective

Example format:
"At age 14, character witnessed [specific event] which led them to believe [Lie] because [reason]."

In your response, provide:
1. ghost_event: The specific past event (2-3 sentences)
2. how_it_created_lie: Why this event led to this Lie (1-2 sentences)
3. reasoning: WHY this Ghost deepens the character arc

Use agent_name: "{self.name}"
"""

        return self.invoke_structured(user_prompt, GhostProposal)

    def critique_ghost(
        self,
        proposals: list[GhostProposal],
        perspective: dict,
        lie: str
    ) -> list[GhostCritique]:
        """Critique Ghost proposals."""
        class CritiqueList(BaseModel):
            critiques: list[GhostCritique] = Field(
                min_length=len(proposals),
                max_length=len(proposals)
            )

        proposals_text = "\n\n".join([
            f"PROPOSAL {i}:\n  Ghost: {p.ghost_event}\n  How: {p.how_it_created_lie}"
            for i, p in enumerate(proposals)
        ])

        user_prompt = f"""Critique these Ghost proposals.

PERSPECTIVE: {perspective['perspective_name']}
LIE: {lie}

{proposals_text}

For each proposal:
- Is Ghost specific enough?
- Does it logically create the Lie?
- Is it emotionally resonant?
- Will it deepen character arc?

Score 1-10. Use agent_name: "{self.name}"
"""

        result = self.invoke_structured(user_prompt, CritiqueList)
        return result.critiques

    def vote(
        self,
        proposals: list[GhostProposal],
        perspective: dict
    ) -> GhostVote:
        """Vote for most compelling Ghost."""
        proposals_text = "\n\n".join([
            f"PROPOSAL {i}: {p.ghost_event[:80]}..."
            for i, p in enumerate(proposals)
        ])

        user_prompt = f"""Vote for the best Ghost.

{proposals_text}

Which Ghost creates the most compelling backstory wound?

Use agent_name: "{self.name}"
"""

        return self.invoke_structured(user_prompt, GhostVote)


class GhostEmotionalAgent(BaseStoryAgent):
    """Ghost specialist focused on emotional impact.

    Creates backstory wounds with maximum emotional resonance,
    ensuring the Ghost hits hard and justifies the Lie's formation.
    """

    @property
    def name(self) -> str:
        return "GHOST_EMOTIONAL"

    @property
    def role(self) -> str:
        return "Emotional backstory specialist"

    @property
    def system_prompt(self) -> str:
        return """You are an emotional storytelling expert specializing in character backstory wounds.

Your role: Create Ghosts with MAXIMUM EMOTIONAL IMPACT.

GHOST PRINCIPLES (K.M. Weiland):
- Ghost = past event that created the Lie
- Not just "something bad happened"
- Must emotionally JUSTIFY why character believes the Lie
- Should haunt character throughout story
- Facing the Ghost = moment of truth in Act 3

EMOTIONAL WOUND TYPES:

1. BETRAYAL:
   - Trusted authority figure failed them
   - Creates Lie: "I can't trust anyone"

2. ABANDONMENT:
   - Lost someone they needed
   - Creates Lie: "I must be self-sufficient"

3. HUMILIATION:
   - Public failure/shame
   - Creates Lie: "I must be perfect/invisible"

4. LOSS OF INNOCENCE:
   - Witnessed something traumatic
   - Creates Lie: "The world is fundamentally unsafe"

5. FAILURE TO PROTECT:
   - Couldn't save someone
   - Creates Lie: "I must control everything"

EMOTIONAL LOGIC:
Ghost → Emotional Wound → Protective Lie → Dysfunctional Behavior

Your Ghosts create EMOTIONAL JUSTIFICATION for the Lie."""

    def propose_ghost(
        self,
        perspective: dict,
        lie: str
    ) -> GhostProposal:
        """Propose Ghost optimized for emotional impact."""
        user_prompt = f"""Create a backstory Ghost with powerful emotional resonance.

THEMATIC PERSPECTIVE:
{perspective['perspective_name']} - {perspective['position']}

LIE CHARACTER BELIEVES:
{lie}

YOUR TASK (emotional lens):
Create a Ghost (backstory wound) that:

1. HITS HARD EMOTIONALLY:
   - Not abstract, but concrete and visceral
   - Reader feels the pain
   - Universally relatable (even if unique circumstances)

2. JUSTIFIES THE LIE:
   - After this event, Lie feels RATIONAL
   - Makes character sympathetic (not stupid for believing Lie)
   - Clear emotional logic: This wound → This protection

3. HAUNTS THE STORY:
   - Echoes in character's present behavior
   - Triggers activated by plot events
   - Can't be resolved without facing it

4. CREATES CLIMACTIC POTENTIAL:
   - Act 3 must force character to revisit Ghost
   - Facing Ghost = accepting Truth

In your response, provide:
1. ghost_event: Specific, concrete backstory event (when they were younger)
2. how_it_created_lie: The emotional logic connecting wound to Lie
3. reasoning: WHY this Ghost has maximum emotional impact

Use agent_name: "{self.name}"
"""

        return self.invoke_structured(user_prompt, GhostProposal)

    def critique_ghost(
        self,
        proposals: list[GhostProposal],
        perspective: dict,
        lie: str
    ) -> list[GhostCritique]:
        """Critique Ghost proposals for emotional power."""
        class CritiqueList(BaseModel):
            critiques: list[GhostCritique] = Field(
                min_length=len(proposals),
                max_length=len(proposals)
            )

        proposals_text = "\n\n".join([
            f"PROPOSAL {i}:\n  Event: {p.ghost_event}\n  Connection: {p.how_it_created_lie[:100]}..."
            for i, p in enumerate(proposals)
        ])

        user_prompt = f"""Critique these Ghost proposals emotionally.

PERSPECTIVE: {perspective['perspective_name']}
LIE: {lie}

{proposals_text}

For each proposal:
- Does Ghost hit hard emotionally?
- Is the wound→Lie connection clear and justified?
- Will this Ghost haunt the character throughout the story?
- Is it concrete and visceral (not abstract)?

Score 1-10. Use agent_name: "{self.name}"
"""

        result = self.invoke_structured(user_prompt, CritiqueList)
        return result.critiques

    def vote(
        self,
        proposals: list[GhostProposal],
        perspective: dict
    ) -> GhostVote:
        """Vote for Ghost with strongest emotional impact."""
        proposals_text = "\n\n".join([
            f"PROPOSAL {i}: {p.ghost_event[:80]}..."
            for i, p in enumerate(proposals)
        ])

        user_prompt = f"""Vote for the Ghost with the most emotional power.

{proposals_text}

Which Ghost creates the most compelling emotional wound?

Use agent_name: "{self.name}"
"""

        return self.invoke_structured(user_prompt, GhostVote)


class GhostThematicAgent(BaseStoryAgent):
    """Ghost specialist focused on thematic connection.

    Ensures Ghost connects to thematic square corner and
    creates backstory that explores the central question.
    """

    @property
    def name(self) -> str:
        return "GHOST_THEMATIC"

    @property
    def role(self) -> str:
        return "Thematic backstory specialist"

    @property
    def system_prompt(self) -> str:
        return """You are a thematic analyst specializing in character backstory.

Your role: Create Ghosts that explore THEMATIC QUESTIONS.

GHOST AS THEMATIC EXPLORATION:
- Ghost isn't just trauma, it's a PHILOSOPHICAL MOMENT
- The moment character first encountered the central question
- Their answer (the Lie) shaped their worldview

THEMATIC SQUARE AND GHOST:

POSITIVE CORNER:
- Ghost: Moment they glimpsed truth but chose fear
- Lie formed: Protection from vulnerability

CONTRADICTORY CORNER:
- Ghost: Moment of betrayal/disillusionment
- Lie formed: Cynical protection from hope

CONTRARY CORNER:
- Ghost: Moment they chose self over others
- Lie formed: Isolation as safety

NEGATION CORNER:
- Ghost: Moment of profound loss/darkness
- Lie formed: Embrace of nihilism/control

GHOST AS THEMATIC ECHO:
The Ghost is the first time character faced the central question.
Their Lie is their answer.
The story is about revisiting that question.

Your Ghosts create THEMATIC RESONANCE."""

    def propose_ghost(
        self,
        perspective: dict,
        lie: str
    ) -> GhostProposal:
        """Propose Ghost with strong thematic connection."""
        user_prompt = f"""Create a backstory Ghost that explores the thematic question.

THEMATIC PERSPECTIVE:
{perspective['perspective_name']} - {perspective['position']}
Corner: {perspective.get('corner', 'N/A')}

LIE CHARACTER BELIEVES:
{lie}

YOUR TASK (thematic lens):
Create a Ghost that:

1. EMBODIES THE CENTRAL QUESTION:
   - Not just "bad thing happened"
   - A moment character first faced the thematic dilemma
   - Their Lie = their answer to that moment

2. FITS THE CORNER:
   - POSITIVE: Chose fear over growth
   - CONTRADICTORY: Chose cynicism over hope
   - CONTRARY: Chose isolation over connection
   - NEGATION: Chose darkness over light

3. CREATES THEMATIC ECHO:
   - Story events will echo this Ghost
   - Act 3 climax = revisiting this choice
   - Different answer = character growth

4. CONNECTS TO OTHER CHARACTERS:
   - How might this Ghost relate to central question
   - How might it contrast with other perspectives

In your response, provide:
1. ghost_event: Backstory event as thematic moment
2. how_it_created_lie: How this shaped character's worldview
3. reasoning: WHY this Ghost serves thematic exploration

Use agent_name: "{self.name}"
"""

        return self.invoke_structured(user_prompt, GhostProposal)

    def critique_ghost(
        self,
        proposals: list[GhostProposal],
        perspective: dict,
        lie: str
    ) -> list[GhostCritique]:
        """Critique Ghost proposals for thematic resonance."""
        class CritiqueList(BaseModel):
            critiques: list[GhostCritique] = Field(
                min_length=len(proposals),
                max_length=len(proposals)
            )

        proposals_text = "\n\n".join([
            f"PROPOSAL {i}:\n  Event: {p.ghost_event}\n  Connection: {p.how_it_created_lie[:100]}..."
            for i, p in enumerate(proposals)
        ])

        user_prompt = f"""Critique these Ghost proposals thematically.

PERSPECTIVE: {perspective['perspective_name']}
CORNER: {perspective.get('corner', 'N/A')}
LIE: {lie}

{proposals_text}

For each proposal:
- Does Ghost embody the central question?
- Does it fit the thematic square corner?
- Will it create thematic echoes in the story?
- Does it deepen philosophical exploration?

Score 1-10. Use agent_name: "{self.name}"
"""

        result = self.invoke_structured(user_prompt, CritiqueList)
        return result.critiques

    def vote(
        self,
        proposals: list[GhostProposal],
        perspective: dict
    ) -> GhostVote:
        """Vote for Ghost with strongest thematic resonance."""
        proposals_text = "\n\n".join([
            f"PROPOSAL {i}: {p.ghost_event[:80]}..."
            for i, p in enumerate(proposals)
        ])

        user_prompt = f"""Vote for the Ghost with the deepest thematic resonance.

{proposals_text}

Which Ghost best explores the thematic question?

Use agent_name: "{self.name}"
"""

        return self.invoke_structured(user_prompt, GhostVote)
