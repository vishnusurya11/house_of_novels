"""
Theme Foundation Debate Agents for Step 0.

Implements the Theme → Character → Plot philosophy by extracting theme
from the logline BEFORE any character or plot development.

Step 0 has 3 substeps with multi-agent debates:
1. Theme Question Debate - 3 agents propose questions, debate, vote → pick 1
2. Thematic Square Debate - 3 agents propose squares, debate, vote → top 5-6
3. Perspective Debate - 3 agents propose perspective sets, debate, vote → finalize

Debate pattern:
- Proposals: Each agent proposes their version
- Critiques: Cross-agent critique with scores
- Votes: All agents vote for best proposal
"""

from src.story_agents.base_story_agent import BaseStoryAgent
from src.story_schemas import (
    ThematicQuestionSchema,
    ThemeQuestionProposal,
    ThemeQuestionCritique,
    ThemeQuestionVote,
    ThematicSquareSchema,
    ThematicSquareProposal,
    ThematicSquareCritique,
    ThematicSquareVote,
    ThematicPerspectiveSchema,
    PerspectiveSetProposal,
    PerspectiveSetCritique,
    PerspectiveSetVote,
)


# =============================================================================
# Substep 1: Theme Question Debate Agents
# =============================================================================

class ThemePhilosopherAgent(BaseStoryAgent):
    """
    Focuses on deep philosophical questions - universal human dilemmas.
    """

    @property
    def name(self) -> str:
        return "THEME_PHILOSOPHER"

    @property
    def role(self) -> str:
        return "Philosophical Theme Analyst"

    @property
    def system_prompt(self) -> str:
        return """You are a philosophical theme analyst who identifies deep, universal human questions in story premises.

Your approach:
- Look for timeless philosophical dilemmas (identity, morality, truth, sacrifice, redemption)
- Frame themes as QUESTIONS that have no easy answers
- Focus on the CHARACTER'S INNER CONFLICT, not just plot events
- Prefer themes that resonate across cultures and time periods

When you see a logline like:
"TRAUMATIC AN IMPOSTOR WANTS TO SAVE A LIFE WITH/FROM A DOCUMENT BUT IT MEANS RISKING THE THING MOST PRECIOUS TO THEM"

You extract philosophical questions like:
- "Can an inauthentic person perform authentic good?"
- "Is identity defined by actions or by truth?"
- "What defines a person: who they claim to be or what they do?"

Your themes are DEEP and UNIVERSAL, not plot-specific.
"""

    def propose_question(self, logline: str, world_context: str = "") -> ThemeQuestionProposal:
        """Propose a thematic question based on philosophical depth."""
        world_ctx = f"\nWORLD CONTEXT:\n{world_context}" if world_context else ""
        user_prompt = f"""Propose ONE thematic question for this story.

LOGLINE:
{logline}{world_ctx}

Identify the DEEPEST, most UNIVERSAL philosophical question at the heart of this premise.

Your thematic question should:
- Be framed as a genuine question (not a statement)
- Address a timeless human dilemma
- Focus on the protagonist's inner conflict
- Have genuine tension (no obvious answer)

In your response, provide:
1. question: Your proposed thematic question
2. explanation: Why this theme emerges from the logline
3. reasoning: WHY this question is the best thematic choice for this story

Return your proposal in the exact JSON format specified by ThemeQuestionProposal.
Use agent_name: "{self.name}"
"""

        return self.invoke_structured(user_prompt, ThemeQuestionProposal)

    def critique_questions(self, proposals: list[ThemeQuestionProposal], logline: str) -> list[ThemeQuestionCritique]:
        """Critique all proposed thematic questions."""
        from pydantic import BaseModel, Field

        class CritiqueList(BaseModel):
            critiques: list[ThemeQuestionCritique] = Field(
                ...,
                min_length=len(proposals),
                max_length=len(proposals)
            )

        proposals_text = "\n".join([
            f"Proposal {i}: {p.question.question}\nReasoning: {p.reasoning}"
            for i, p in enumerate(proposals)
        ])

        user_prompt = f"""Critique these thematic question proposals from a philosophical perspective.

LOGLINE:
{logline}

PROPOSALS:
{proposals_text}

For each proposal, evaluate:
- Philosophical depth: Does it address a universal human question?
- Relevance: Does it emerge naturally from the logline?
- Dramatic potential: Will it create meaningful character conflict?
- Timelessness: Will this theme resonate across audiences?

Score each proposal 1-10 based on philosophical merit.

Return critiques in JSON format specified by CritiqueList.
Use agent_name: "{self.name}" for all critiques.
"""

        result = self.invoke_structured(user_prompt, CritiqueList)
        return result.critiques

    def vote(self, proposals: list[ThemeQuestionProposal], logline: str) -> ThemeQuestionVote:
        """Vote for the best thematic question."""
        proposals_text = "\n".join([
            f"Proposal {i}: {p.question.question}"
            for i, p in enumerate(proposals)
        ])

        user_prompt = f"""Vote for the BEST thematic question.

LOGLINE:
{logline}

PROPOSALS:
{proposals_text}

Vote for the proposal with the deepest philosophical resonance and universal appeal.

Return your vote in JSON format specified by ThemeQuestionVote.
Use agent_name: "{self.name}"
"""

        return self.invoke_structured(user_prompt, ThemeQuestionVote)


class ThemeEmotionalAgent(BaseStoryAgent):
    """
    Focuses on emotional resonance - what will move the audience.
    """

    @property
    def name(self) -> str:
        return "THEME_EMOTIONAL"

    @property
    def role(self) -> str:
        return "Emotional Theme Specialist"

    @property
    def system_prompt(self) -> str:
        return """You are an emotional theme specialist who identifies themes that create powerful audience connection.

Your approach:
- Focus on themes that evoke strong emotions (fear, hope, love, loss, redemption)
- Look for RELATABLE human experiences the audience has felt
- Frame themes as emotional journeys, not abstract concepts
- Prefer themes that create empathy and catharsis

When you see a logline like:
"TRAUMATIC AN IMPOSTOR WANTS TO SAVE A LIFE BUT IT MEANS RISKING THE THING MOST PRECIOUS TO THEM"

You extract emotional questions like:
- "Is love worth the cost of vulnerability?"
- "Can you heal from trauma by helping others?"
- "What are you willing to sacrifice for redemption?"

Your themes are EMOTIONALLY RESONANT and create AUDIENCE CONNECTION.
"""

    def propose_question(self, logline: str, world_context: str = "") -> ThemeQuestionProposal:
        """Propose a thematic question based on emotional resonance."""
        world_ctx = f"\nWORLD CONTEXT:\n{world_context}" if world_context else ""
        user_prompt = f"""Propose ONE thematic question for this story.

LOGLINE:
{logline}{world_ctx}

Identify the theme with the STRONGEST EMOTIONAL RESONANCE for the audience.

Your thematic question should:
- Evoke powerful emotions (fear, hope, love, grief, redemption)
- Be something the audience can personally relate to
- Create empathy for the protagonist
- Lead to emotional catharsis

In your response, provide:
1. question: Your proposed thematic question
2. explanation: Why this theme emerges from the logline
3. reasoning: WHY this question is the best thematic choice for this story

Return your proposal in JSON format specified by ThemeQuestionProposal.
Use agent_name: "{self.name}"
"""

        return self.invoke_structured(user_prompt, ThemeQuestionProposal)

    def critique_questions(self, proposals: list[ThemeQuestionProposal], logline: str) -> list[ThemeQuestionCritique]:
        """Critique all proposed thematic questions."""
        from pydantic import BaseModel, Field

        class CritiqueList(BaseModel):
            critiques: list[ThemeQuestionCritique] = Field(
                ...,
                min_length=len(proposals),
                max_length=len(proposals)
            )

        proposals_text = "\n".join([
            f"Proposal {i}: {p.question.question}\nReasoning: {p.reasoning}"
            for i, p in enumerate(proposals)
        ])

        user_prompt = f"""Critique these thematic questions from an emotional perspective.

LOGLINE:
{logline}

PROPOSALS:
{proposals_text}

For each proposal, evaluate:
- Emotional impact: Will this move the audience?
- Relatability: Can audiences personally connect to this question?
- Cathartic potential: Will resolving this create satisfaction?
- Empathy: Does it help us feel for the protagonist?

Score each proposal 1-10 based on emotional resonance.

Return critiques in JSON format specified by CritiqueList.
Use agent_name: "{self.name}" for all critiques.
"""

        result = self.invoke_structured(user_prompt, CritiqueList)
        return result.critiques

    def vote(self, proposals: list[ThemeQuestionProposal], logline: str) -> ThemeQuestionVote:
        """Vote for the best thematic question."""
        proposals_text = "\n".join([
            f"Proposal {i}: {p.question.question}"
            for i, p in enumerate(proposals)
        ])

        user_prompt = f"""Vote for the BEST thematic question.

LOGLINE:
{logline}

PROPOSALS:
{proposals_text}

Vote for the proposal with the strongest emotional resonance and audience connection.

Return your vote in JSON format specified by ThemeQuestionVote.
Use agent_name: "{self.name}"
"""

        return self.invoke_structured(user_prompt, ThemeQuestionVote)


class ThemeDramaticAgent(BaseStoryAgent):
    """
    Focuses on dramatic potential - what creates the best conflict.
    """

    @property
    def name(self) -> str:
        return "THEME_DRAMATIC"

    @property
    def role(self) -> str:
        return "Dramatic Conflict Specialist"

    @property
    def system_prompt(self) -> str:
        return """You are a dramatic conflict specialist who identifies themes that create maximum story tension.

Your approach:
- Focus on themes that generate GENUINE CONFLICT and IMPOSSIBLE CHOICES
- Look for themes where both sides have valid arguments (not good vs evil)
- Frame themes as dilemmas where ANY choice has consequences
- Prefer themes that escalate tension throughout the story

When you see a logline like:
"TRAUMATIC AN IMPOSTOR WANTS TO SAVE A LIFE BUT IT MEANS RISKING THE THING MOST PRECIOUS TO THEM"

You extract conflict-driven questions like:
- "Is self-preservation selfish when others need you?"
- "Can you save someone else without destroying yourself?"
- "Which matters more: protecting what you have or helping those in need?"

Your themes create IMPOSSIBLE CHOICES and ESCALATING CONFLICT.
"""

    def propose_question(self, logline: str, world_context: str = "") -> ThemeQuestionProposal:
        """Propose a thematic question based on dramatic potential."""
        world_ctx = f"\nWORLD CONTEXT:\n{world_context}" if world_context else ""
        user_prompt = f"""Propose ONE thematic question for this story.

LOGLINE:
{logline}{world_ctx}

Identify the theme with the GREATEST DRAMATIC POTENTIAL - the one that creates the hardest choices.

Your thematic question should:
- Create genuine conflict (both sides have merit)
- Force impossible choices with real consequences
- Escalate tension as the story progresses
- Have no "easy answer" - any choice costs something

In your response, provide:
1. question: Your proposed thematic question
2. explanation: Why this theme emerges from the logline
3. reasoning: WHY this question is the best thematic choice for this story

Return your proposal in JSON format specified by ThemeQuestionProposal.
Use agent_name: "{self.name}"
"""

        return self.invoke_structured(user_prompt, ThemeQuestionProposal)

    def critique_questions(self, proposals: list[ThemeQuestionProposal], logline: str) -> list[ThemeQuestionCritique]:
        """Critique all proposed thematic questions."""
        from pydantic import BaseModel, Field

        class CritiqueList(BaseModel):
            critiques: list[ThemeQuestionCritique] = Field(
                ...,
                min_length=len(proposals),
                max_length=len(proposals)
            )

        proposals_text = "\n".join([
            f"Proposal {i}: {p.question.question}\nReasoning: {p.reasoning}"
            for i, p in enumerate(proposals)
        ])

        user_prompt = f"""Critique these thematic questions from a dramatic perspective.

LOGLINE:
{logline}

PROPOSALS:
{proposals_text}

For each proposal, evaluate:
- Conflict potential: Does it create genuine dilemmas?
- Choice difficulty: Are both options valid/costly?
- Tension escalation: Will conflict intensify through the story?
- Dramatic irony: Can this create powerful story moments?

Score each proposal 1-10 based on dramatic potential.

Return critiques in JSON format specified by CritiqueList.
Use agent_name: "{self.name}" for all critiques.
"""

        result = self.invoke_structured(user_prompt, CritiqueList)
        return result.critiques

    def vote(self, proposals: list[ThemeQuestionProposal], logline: str) -> ThemeQuestionVote:
        """Vote for the best thematic question."""
        proposals_text = "\n".join([
            f"Proposal {i}: {p.question.question}"
            for i, p in enumerate(proposals)
        ])

        user_prompt = f"""Vote for the BEST thematic question.

LOGLINE:
{logline}

PROPOSALS:
{proposals_text}

Vote for the proposal with the greatest dramatic potential and conflict-generating power.

Return your vote in JSON format specified by ThemeQuestionVote.
Use agent_name: "{self.name}"
"""

        return self.invoke_structured(user_prompt, ThemeQuestionVote)


# =============================================================================
# Substep 2: Thematic Square Debate Agents
# =============================================================================

class SquareArchitectAgent(BaseStoryAgent):
    """
    Builds thematic squares with clear philosophical structure.
    """

    @property
    def name(self) -> str:
        return "SQUARE_ARCHITECT"

    @property
    def role(self) -> str:
        return "Thematic Square Architect"

    @property
    def system_prompt(self) -> str:
        return """You are a thematic square architect who builds Robert McKee's 4-corner exploration of theme.

Robert McKee's Thematic Square:
1. POSITIVE (Truth): The liberating insight that sets characters free
2. CONTRADICTORY (Lie): The false belief opposite of truth - imprisons characters
3. CONTRARY (Nuanced Negative): The dark side of truth - truth's cost/complications
4. NEGATION OF NEGATION (Extreme): The worst outcome - total commitment to the lie

Your approach:
- Ensure all 4 corners are DISTINCT and cover different philosophical territory
- Make CONTRADICTORY a genuine opposite of POSITIVE (not just negative)
- Make CONTRARY show truth's complexity (not just "truth is bad")
- Make NEGATION the absolute worst case - where the lie ultimately leads

Example for theme "Is authenticity worth the cost?":
- POSITIVE: "Being your true self creates genuine connection"
- CONTRADICTORY: "Masks protect you from pain and judgment"
- CONTRARY: "Authenticity can isolate you when others can't handle your truth"
- NEGATION: "Complete self-deception leads to total disconnection from reality"

Build squares with PHILOSOPHICAL CLARITY and DISTINCT CORNERS.
"""

    def propose_square(self, central_question: str, logline: str = "") -> ThematicSquareProposal:
        """Propose a thematic square."""
        logline_ctx = f"\nLOGLINE:\n{logline}" if logline else ""
        user_prompt = f"""Build a thematic square for this theme.

CENTRAL QUESTION:
{central_question}{logline_ctx}

Build Robert McKee's 4-corner thematic square:

1. POSITIVE (Truth): What liberating insight resolves the question?
2. CONTRADICTORY (Lie): What false belief is the OPPOSITE of this truth?
3. CONTRARY (Nuanced Negative): What is the DARK SIDE of the truth?
4. NEGATION OF NEGATION (Extreme): What is the WORST outcome if the lie persists?

Each corner must be:
- 1 sentence, under 15 words
- Philosophically distinct from other corners
- Relevant to the story

In your response, provide:
1. thematic_square: The 4-corner square (positive, contradictory, contrary, negation_of_negation)
2. reasoning: WHY this thematic square creates the best foundation for dramatic conflict

Return your proposal in JSON format specified by ThematicSquareProposal.
Use agent_name: "{self.name}"
"""

        return self.invoke_structured(user_prompt, ThematicSquareProposal)

    def critique_squares(self, proposals: list[ThematicSquareProposal], central_question: str) -> list[ThematicSquareCritique]:
        """Critique all proposed thematic squares."""
        from pydantic import BaseModel, Field

        class CritiqueList(BaseModel):
            critiques: list[ThematicSquareCritique] = Field(
                ...,
                min_length=len(proposals),
                max_length=len(proposals)
            )

        proposals_text = "\n".join([
            f"Proposal {i}:\n  POSITIVE: {p.thematic_square.positive}\n  CONTRADICTORY: {p.thematic_square.contradictory}\n  CONTRARY: {p.thematic_square.contrary}\n  NEGATION: {p.thematic_square.negation_of_negation}"
            for i, p in enumerate(proposals)
        ])

        user_prompt = f"""Critique these thematic square proposals.

CENTRAL QUESTION:
{central_question}

PROPOSALS:
{proposals_text}

For each square, evaluate:
- Philosophical clarity: Are the 4 corners distinct?
- Oppositional structure: Is CONTRADICTORY truly opposite of POSITIVE?
- Nuance: Does CONTRARY show truth's complexity (not just negativity)?
- Extremity: Does NEGATION represent the worst possible outcome?

Score each 1-10.

Return critiques in JSON format specified by CritiqueList.
Use agent_name: "{self.name}"
"""

        result = self.invoke_structured(user_prompt, CritiqueList)
        return result.critiques

    def vote(self, proposals: list[ThematicSquareProposal], central_question: str) -> ThematicSquareVote:
        """Vote for the best thematic square."""
        proposals_text = "\n".join([
            f"Proposal {i}:\n  +: {p.thematic_square.positive}\n  ×: {p.thematic_square.contradictory}\n  ~: {p.thematic_square.contrary}\n  ×÷: {p.thematic_square.negation_of_negation}"
            for i, p in enumerate(proposals)
        ])

        user_prompt = f"""Vote for the BEST thematic square.

CENTRAL QUESTION:
{central_question}

PROPOSALS:
{proposals_text}

Vote for the square with the clearest philosophical structure and most distinct corners.

Return vote in JSON format specified by ThematicSquareVote.
Use agent_name: "{self.name}"
"""

        return self.invoke_structured(user_prompt, ThematicSquareVote)


class SquareCharacterAgent(BaseStoryAgent):
    """
    Builds squares focused on character potential.
    """

    @property
    def name(self) -> str:
        return "SQUARE_CHARACTER"

    @property
    def role(self) -> str:
        return "Character-Focused Square Builder"

    @property
    def system_prompt(self) -> str:
        return """You are a character-focused square builder who creates thematic squares that generate compelling character arcs.

Your approach:
- Each corner should represent a CHARACTER's WORLDVIEW
- POSITIVE = The truth the protagonist must learn
- CONTRADICTORY = The lie the protagonist believes at the start
- CONTRARY = A worldview for a complex ally/mentor (truth with costs)
- NEGATION = The antagonist's or fallen character's worldview

Think: "What would a CHARACTER who believes this corner say/do?"

Example for "Is authenticity worth the cost?":
- POSITIVE: "Only by being real can you find true belonging" (Protagonist's endpoint)
- CONTRADICTORY: "Showing weakness gets you hurt - keep the mask on" (Protagonist's start)
- CONTRARY: "I tried being honest and lost everything I loved" (Burned mentor)
- NEGATION: "I've lied so long, I don't even know who I am anymore" (Antagonist)

Build squares that create DIVERSE, CONFLICTING CHARACTER PERSPECTIVES.
"""

    def propose_square(self, central_question: str, logline: str = "") -> ThematicSquareProposal:
        """Propose a thematic square focused on character arcs."""
        logline_ctx = f"\nLOGLINE:\n{logline}" if logline else ""
        user_prompt = f"""Build a character-focused thematic square.

CENTRAL QUESTION:
{central_question}{logline_ctx}

Build a square where each corner represents a CHARACTER WORLDVIEW:

1. POSITIVE: What belief will the protagonist ultimately embrace?
2. CONTRADICTORY: What false belief does the protagonist start with?
3. CONTRARY: What worldview for a complex supporting character?
4. NEGATION: What worldview for the antagonist/fallen character?

Make each corner sound like something a REAL PERSON would believe.

In your response, provide:
1. thematic_square: The 4-corner square (positive, contradictory, contrary, negation_of_negation)
2. reasoning: WHY this thematic square creates the best foundation for dramatic conflict

Return proposal in JSON format specified by ThematicSquareProposal.
Use agent_name: "{self.name}"
"""

        return self.invoke_structured(user_prompt, ThematicSquareProposal)

    def critique_squares(self, proposals: list[ThematicSquareProposal], central_question: str) -> list[ThematicSquareCritique]:
        """Critique squares from character perspective."""
        from pydantic import BaseModel, Field

        class CritiqueList(BaseModel):
            critiques: list[ThematicSquareCritique] = Field(
                ...,
                min_length=len(proposals),
                max_length=len(proposals)
            )

        proposals_text = "\n".join([
            f"Proposal {i}:\n  +: {p.thematic_square.positive}\n  ×: {p.thematic_square.contradictory}\n  ~: {p.thematic_square.contrary}\n  ×÷: {p.thematic_square.negation_of_negation}"
            for i, p in enumerate(proposals)
        ])

        user_prompt = f"""Critique these squares from a character perspective.

CENTRAL QUESTION:
{central_question}

PROPOSALS:
{proposals_text}

For each square, evaluate:
- Character potential: Do these corners create distinct character types?
- Arc potential: Can a protagonist journey from CONTRADICTORY to POSITIVE?
- Believability: Would real people actually hold these beliefs?
- Conflict potential: Will characters with these views clash dramatically?

Score 1-10.

Return critiques in JSON format specified by CritiqueList.
Use agent_name: "{self.name}"
"""

        result = self.invoke_structured(user_prompt, CritiqueList)
        return result.critiques

    def vote(self, proposals: list[ThematicSquareProposal], central_question: str) -> ThematicSquareVote:
        """Vote for best square for character development."""
        proposals_text = "\n".join([
            f"Proposal {i}:\n  +: {p.thematic_square.positive}\n  ×: {p.thematic_square.contradictory}"
            for i, p in enumerate(proposals)
        ])

        user_prompt = f"""Vote for the square with the best character potential.

CENTRAL QUESTION:
{central_question}

PROPOSALS:
{proposals_text}

Vote for the square that will create the most compelling, diverse character perspectives.

Return vote in JSON format specified by ThematicSquareVote.
Use agent_name: "{self.name}"
"""

        return self.invoke_structured(user_prompt, ThematicSquareVote)


class SquareConflictAgent(BaseStoryAgent):
    """
    Builds squares that maximize dramatic tension.
    """

    @property
    def name(self) -> str:
        return "SQUARE_CONFLICT"

    @property
    def role(self) -> str:
        return "Conflict-Maximizing Square Builder"

    @property
    def system_prompt(self) -> str:
        return """You are a conflict-maximizing square builder who creates thematic squares that generate maximum story tension.

Your approach:
- Ensure POSITIVE and CONTRADICTORY are in DIRECT OPPOSITION
- Make CONTRARY create moral complexity (both sides have merit)
- Make NEGATION show the horrifying endpoint of the lie
- Each corner should create scenes where characters CLASH

Example for "Is authenticity worth the cost?":
- POSITIVE: "Truth always wins in the end - lies destroy you"
- CONTRADICTORY: "Truth is naive - survival requires deception"
- CONTRARY: "Truth can be cruel - sometimes lies protect the innocent"
- NEGATION: "There is no truth - everything is manipulation for power"

Build squares that create MAXIMUM PHILOSOPHICAL CONFLICT between corners.
"""

    def propose_square(self, central_question: str, logline: str = "") -> ThematicSquareProposal:
        """Propose a conflict-maximizing thematic square."""
        logline_ctx = f"\nLOGLINE:\n{logline}" if logline else ""
        user_prompt = f"""Build a conflict-maximizing thematic square.

CENTRAL QUESTION:
{central_question}{logline_ctx}

Build a square that maximizes philosophical conflict:

1. POSITIVE: The strongest argument FOR one side
2. CONTRADICTORY: The strongest argument AGAINST that side
3. CONTRARY: A position that complicates the debate (both sides have merit)
4. NEGATION: The extreme, horrifying endpoint of the CONTRADICTORY

Make each corner create opportunities for characters to CLASH in debate/action.

In your response, provide:
1. thematic_square: The 4-corner square (positive, contradictory, contrary, negation_of_negation)
2. reasoning: WHY this thematic square creates the best foundation for dramatic conflict

Return proposal in JSON format specified by ThematicSquareProposal.
Use agent_name: "{self.name}"
"""

        return self.invoke_structured(user_prompt, ThematicSquareProposal)

    def critique_squares(self, proposals: list[ThematicSquareProposal], central_question: str) -> list[ThematicSquareCritique]:
        """Critique squares from conflict perspective."""
        from pydantic import BaseModel, Field

        class CritiqueList(BaseModel):
            critiques: list[ThematicSquareCritique] = Field(
                ...,
                min_length=len(proposals),
                max_length=len(proposals)
            )

        proposals_text = "\n".join([
            f"Proposal {i}:\n  +: {p.thematic_square.positive}\n  ×: {p.thematic_square.contradictory}\n  ~: {p.thematic_square.contrary}\n  ×÷: {p.thematic_square.negation_of_negation}"
            for i, p in enumerate(proposals)
        ])

        user_prompt = f"""Critique these squares from a conflict perspective.

CENTRAL QUESTION:
{central_question}

PROPOSALS:
{proposals_text}

For each square, evaluate:
- Oppositional force: How directly do POSITIVE and CONTRADICTORY clash?
- Moral complexity: Does CONTRARY create genuine ethical dilemmas?
- Dramatic horror: Is NEGATION a truly horrifying extreme?
- Scene potential: Will this square create powerful confrontations?

Score 1-10.

Return critiques in JSON format specified by CritiqueList.
Use agent_name: "{self.name}"
"""

        result = self.invoke_structured(user_prompt, CritiqueList)
        return result.critiques

    def vote(self, proposals: list[ThematicSquareProposal], central_question: str) -> ThematicSquareVote:
        """Vote for square with maximum conflict potential."""
        proposals_text = "\n".join([
            f"Proposal {i}: +:{p.thematic_square.positive} vs ×:{p.thematic_square.contradictory}"
            for i, p in enumerate(proposals)
        ])

        user_prompt = f"""Vote for the square with maximum conflict potential.

CENTRAL QUESTION:
{central_question}

PROPOSALS:
{proposals_text}

Vote for the square that will create the most dramatic philosophical clashes.

Return vote in JSON format specified by ThematicSquareVote.
Use agent_name: "{self.name}"
"""

        return self.invoke_structured(user_prompt, ThematicSquareVote)


# =============================================================================
# Substep 3: Perspective Set Debate Agents
# =============================================================================

class PerspectiveDiversityAgent(BaseStoryAgent):
    """
    Creates diverse, distinct character perspectives.
    """

    @property
    def name(self) -> str:
        return "PERSPECTIVE_DIVERSITY"

    @property
    def role(self) -> str:
        return "Character Perspective Diversity Specialist"

    @property
    def system_prompt(self) -> str:
        return """You are a perspective diversity specialist who creates distinct, memorable character worldviews.

Your approach:
- Ensure each perspective is GENUINELY DIFFERENT (not just variations)
- Cover at least 3 corners of the thematic square (must include POSITIVE and CONTRADICTORY)
- Give each perspective a MEMORABLE NAME that captures its essence
- Make each perspective sound like a REAL PERSON'S belief system

Example for "Is authenticity worth the cost?" with a square about truth vs. deception:

1. "The Unmasked Warrior" (POSITIVE)
   - Position: "Truth is the only path to genuine connection"
   - Belief: "I'd rather be hated for who I am than loved for who I'm not"

2. "The Protective Phantom" (CONTRADICTORY)
   - Position: "Masks protect you and others from painful truths"
   - Belief: "Showing your real self just gives people ammunition to hurt you"

3. "The Burned Idealist" (CONTRARY)
   - Position: "I believed in honesty and it cost me everything"
   - Belief: "Authenticity sounds noble until you lose everyone you love"

4. "The Shapeshifter" (NEGATION)
   - Position: "Identity itself is a lie - be whoever gets you what you need"
   - Belief: "There is no 'real me' - we're all just playing roles"

Create DIVERSE perspectives that will CLASH dramatically.
"""

    def propose_perspectives(self, central_question: str, top_squares: list[ThematicSquareSchema]) -> PerspectiveSetProposal:
        """Propose a set of 3-5 character perspectives."""
        # Use top-voted square
        square = top_squares[0]

        user_prompt = f"""Create a diverse set of 4 character perspectives.

CENTRAL QUESTION:
{central_question}

THEMATIC SQUARE:
- POSITIVE: {square.positive}
- CONTRADICTORY: {square.contradictory}
- CONTRARY: {square.contrary}
- NEGATION: {square.negation_of_negation}

Create 4 character perspectives that:
1. Cover at least 3 corners (MUST include POSITIVE and CONTRADICTORY)
2. Have memorable, evocative names (e.g., "The Unmasked Warrior", "The Protective Phantom")
3. State a clear position on the central question
4. Include an example belief a character might hold
5. Are GENUINELY DISTINCT from each other

In your response, provide:
1. perspectives: A list of 4 character perspectives (each with perspective_name, position, corner, example_belief)
2. reasoning: WHY this set of perspectives best serves the story's thematic needs

Return proposal in JSON format specified by PerspectiveSetProposal.
Use agent_name: "{self.name}"
"""

        return self.invoke_structured(user_prompt, PerspectiveSetProposal)

    def critique_perspective_sets(self, proposals: list[PerspectiveSetProposal], central_question: str) -> list[PerspectiveSetCritique]:
        """Critique perspective sets."""
        from pydantic import BaseModel, Field

        class CritiqueList(BaseModel):
            critiques: list[PerspectiveSetCritique] = Field(
                ...,
                min_length=len(proposals),
                max_length=len(proposals)
            )

        proposals_text = "\n".join([
            f"Proposal {i}:\n" + "\n".join([f"  - {p.perspective_name}: {p.position}" for p in proposal.perspectives])
            for i, proposal in enumerate(proposals)
        ])

        user_prompt = f"""Critique these perspective sets.

CENTRAL QUESTION:
{central_question}

PROPOSALS:
{proposals_text}

For each set, evaluate:
- Diversity: Are the perspectives genuinely distinct?
- Coverage: Do they cover multiple corners of the square?
- Memorability: Are the names evocative and fitting?
- Believability: Would real people hold these views?

Score 1-10.

Return critiques in JSON format specified by CritiqueList.
Use agent_name: "{self.name}"
"""

        result = self.invoke_structured(user_prompt, CritiqueList)
        return result.critiques

    def vote(self, proposals: list[PerspectiveSetProposal], central_question: str) -> PerspectiveSetVote:
        """Vote for best perspective set."""
        proposals_text = "\n".join([
            f"Proposal {i}: {', '.join([p.perspective_name for p in proposal.perspectives])}"
            for i, proposal in enumerate(proposals)
        ])

        user_prompt = f"""Vote for the BEST perspective set.

CENTRAL QUESTION:
{central_question}

PROPOSALS:
{proposals_text}

Vote for the set with the most diverse, memorable, and dramatically useful perspectives.

Return vote in JSON format specified by PerspectiveSetVote.
Use agent_name: "{self.name}"
"""

        return self.invoke_structured(user_prompt, PerspectiveSetVote)


class PerspectiveStoryAgent(BaseStoryAgent):
    """
    Creates perspectives optimized for THIS story.
    """

    @property
    def name(self) -> str:
        return "PERSPECTIVE_STORY"

    @property
    def role(self) -> str:
        return "Story-Specific Perspective Designer"

    @property
    def system_prompt(self) -> str:
        return """You are a story-specific perspective designer who tailors perspectives to fit the logline's context.

Your approach:
- Ground perspectives in the SPECIFIC story context (not generic)
- Consider the world, setting, and situation from the logline
- Ensure perspectives feel NATURAL to this story's circumstances
- Make perspectives that will create scenes/conflicts specific to THIS premise

Example: If logline is "An impostor wants to save a life with a document":

NOT generic like:
- "The Truth Seeker" - "Truth is always better"

Instead story-specific like:
- "The Forged Identity" - "I've lived this lie so long, maybe it's true enough to do real good"
- "The Document Keeper" - "The truth is written - anything else is poison"

Create perspectives that emerge from THIS STORY'S unique situation.
"""

    def propose_perspectives(self, central_question: str, top_squares: list[ThematicSquareSchema], logline: str = "") -> PerspectiveSetProposal:
        """Propose story-specific perspectives."""
        square = top_squares[0]

        user_prompt = f"""Create story-specific character perspectives.

LOGLINE:
{logline}

CENTRAL QUESTION:
{central_question}

THEMATIC SQUARE:
- POSITIVE: {square.positive}
- CONTRADICTORY: {square.contradictory}
- CONTRARY: {square.contrary}
- NEGATION: {square.negation_of_negation}

Create 4 perspectives that:
1. Are grounded in THIS STORY'S specific context
2. Reference the situation/world from the logline
3. Feel natural to THIS premise (not generic)
4. Will create conflicts specific to this story

In your response, provide:
1. perspectives: A list of 4 character perspectives (each with perspective_name, position, corner, example_belief)
2. reasoning: WHY this set of perspectives best serves the story's thematic needs

Return proposal in JSON format specified by PerspectiveSetProposal.
Use agent_name: "{self.name}"
"""

        return self.invoke_structured(user_prompt, PerspectiveSetProposal)

    def critique_perspective_sets(self, proposals: list[PerspectiveSetProposal], central_question: str, logline: str = "") -> list[PerspectiveSetCritique]:
        """Critique from story-fit perspective."""
        from pydantic import BaseModel, Field

        class CritiqueList(BaseModel):
            critiques: list[PerspectiveSetCritique] = Field(
                ...,
                min_length=len(proposals),
                max_length=len(proposals)
            )

        proposals_text = "\n".join([
            f"Proposal {i}:\n" + "\n".join([f"  - {p.perspective_name}" for p in proposal.perspectives])
            for i, proposal in enumerate(proposals)
        ])

        user_prompt = f"""Critique these perspective sets for story fit.

LOGLINE:
{logline}

CENTRAL QUESTION:
{central_question}

PROPOSALS:
{proposals_text}

For each set, evaluate:
- Story specificity: Do they emerge from THIS premise?
- Contextual grounding: Do they reference the story world/situation?
- Scene potential: Will they create conflicts unique to this story?
- Natural fit: Do they feel organic to this premise?

Score 1-10.

Return critiques in JSON format specified by CritiqueList.
Use agent_name: "{self.name}"
"""

        result = self.invoke_structured(user_prompt, CritiqueList)
        return result.critiques

    def vote(self, proposals: list[PerspectiveSetProposal], central_question: str) -> PerspectiveSetVote:
        """Vote for most story-appropriate perspectives."""
        proposals_text = "\n".join([
            f"Proposal {i}: {', '.join([p.perspective_name for p in proposal.perspectives])}"
            for i, proposal in enumerate(proposals)
        ])

        user_prompt = f"""Vote for the perspective set that best fits THIS STORY.

CENTRAL QUESTION:
{central_question}

PROPOSALS:
{proposals_text}

Vote for the set that feels most natural and specific to this premise.

Return vote in JSON format specified by PerspectiveSetVote.
Use agent_name: "{self.name}"
"""

        return self.invoke_structured(user_prompt, PerspectiveSetVote)


class PerspectiveBalanceAgent(BaseStoryAgent):
    """
    Creates balanced perspectives that serve the book's needs.
    """

    @property
    def name(self) -> str:
        return "PERSPECTIVE_BALANCE"

    @property
    def role(self) -> str:
        return "Perspective Balance Specialist"

    @property
    def system_prompt(self) -> str:
        return """You are a perspective balance specialist who ensures the perspective set serves the complete book.

Your approach:
- Ensure protagonist/antagonist perspectives are clear
- Include at least one "middle ground" perspective (CONTRARY corner)
- Balance philosophical depth with practical character needs
- Make sure no perspective is redundant or too similar to another

Ideal balance for a 3-5 character story:
- 1 POSITIVE perspective (protagonist's endpoint/mentor)
- 1 CONTRADICTORY perspective (protagonist's start/obstacle)
- 1-2 CONTRARY perspectives (complex allies, moral gray areas)
- 0-1 NEGATION perspective (antagonist/cautionary tale)

Create perspective sets that give the book TONAL RANGE and PHILOSOPHICAL BALANCE.
"""

    def propose_perspectives(self, central_question: str, top_squares: list[ThematicSquareSchema]) -> PerspectiveSetProposal:
        """Propose balanced perspective set."""
        square = top_squares[0]

        user_prompt = f"""Create a balanced set of character perspectives.

CENTRAL QUESTION:
{central_question}

THEMATIC SQUARE:
- POSITIVE: {square.positive}
- CONTRADICTORY: {square.contradictory}
- CONTRARY: {square.contrary}
- NEGATION: {square.negation_of_negation}

Create 4 perspectives with BALANCE:
1. At least one POSITIVE (protagonist endpoint/mentor)
2. At least one CONTRADICTORY (protagonist start/obstacle)
3. At least one CONTRARY (complex middle ground)
4. Optional NEGATION (antagonist/extreme)

Ensure:
- No two perspectives are redundant
- The set covers philosophical range
- Each serves a distinct narrative function

In your response, provide:
1. perspectives: A list of 4 character perspectives (each with perspective_name, position, corner, example_belief)
2. reasoning: WHY this set of perspectives best serves the story's thematic needs

Return proposal in JSON format specified by PerspectiveSetProposal.
Use agent_name: "{self.name}"
"""

        return self.invoke_structured(user_prompt, PerspectiveSetProposal)

    def critique_perspective_sets(self, proposals: list[PerspectiveSetProposal], central_question: str) -> list[PerspectiveSetCritique]:
        """Critique from balance perspective."""
        from pydantic import BaseModel, Field

        class CritiqueList(BaseModel):
            critiques: list[PerspectiveSetCritique] = Field(
                ...,
                min_length=len(proposals),
                max_length=len(proposals)
            )

        proposals_text = "\n".join([
            f"Proposal {i}:\n" + "\n".join([f"  - {p.perspective_name} ({p.corner})" for p in proposal.perspectives])
            for i, proposal in enumerate(proposals)
        ])

        user_prompt = f"""Critique these perspective sets for balance.

CENTRAL QUESTION:
{central_question}

PROPOSALS:
{proposals_text}

For each set, evaluate:
- Coverage: Does it span POSITIVE, CONTRADICTORY, and CONTRARY?
- Redundancy: Are any perspectives too similar?
- Narrative function: Does each serve a distinct story purpose?
- Range: Does the set provide philosophical breadth?

Score 1-10.

Return critiques in JSON format specified by CritiqueList.
Use agent_name: "{self.name}"
"""

        result = self.invoke_structured(user_prompt, CritiqueList)
        return result.critiques

    def vote(self, proposals: list[PerspectiveSetProposal], central_question: str) -> PerspectiveSetVote:
        """Vote for most balanced perspective set."""
        proposals_text = "\n".join([
            f"Proposal {i}: {', '.join([f'{p.perspective_name}({p.corner})' for p in proposal.perspectives])}"
            for i, proposal in enumerate(proposals)
        ])

        user_prompt = f"""Vote for the most BALANCED perspective set.

CENTRAL QUESTION:
{central_question}

PROPOSALS:
{proposals_text}

Vote for the set with the best balance across corners and narrative functions.

Return vote in JSON format specified by PerspectiveSetVote.
Use agent_name: "{self.name}"
"""

        return self.invoke_structured(user_prompt, PerspectiveSetVote)
