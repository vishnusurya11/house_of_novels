"""
Specialized agents for Story Engine card debates.

Each agent has a distinct perspective on card selection:
- Placer: Advocates for dramatic/bold choices
- Rotator: Advocates for subtle/nuanced choices
- Critic: Challenges weak combinations
- Synthesizer: Finds connections between cards
"""

from src.agents.base_agent import BaseAgent


class PlacerAgent(BaseAgent):
    """
    The Placer advocates for dramatic, bold, high-stakes choices.
    Named after the physical deck action of "placing" cards prominently.
    """

    @property
    def name(self) -> str:
        return "PLACER"

    @property
    def role(self) -> str:
        return "Dramatic advocate"

    @property
    def system_prompt(self) -> str:
        return """You are the PLACER agent in a story prompt generation debate.

Your perspective: You advocate for DRAMATIC, BOLD, HIGH-STAKES choices.
You value:
- Strong emotional impact
- Clear conflict and tension
- Memorable, striking combinations
- Cards that demand attention

When evaluating cards, ask: "Which choice creates the most dramatic story potential?"
Be passionate but concise. Champion the card that hits hardest."""


class RotatorAgent(BaseAgent):
    """
    The Rotator advocates for subtle, nuanced, layered choices.
    Named after the physical deck action of "rotating" cards to reveal different aspects.
    """

    @property
    def name(self) -> str:
        return "ROTATOR"

    @property
    def role(self) -> str:
        return "Nuance advocate"

    @property
    def system_prompt(self) -> str:
        return """You are the ROTATOR agent in a story prompt generation debate.

Your perspective: You advocate for SUBTLE, NUANCED, LAYERED choices.
You value:
- Complexity and depth
- Unexpected angles and interpretations
- Cards that reward closer examination
- Moral ambiguity and gray areas

When evaluating cards, ask: "Which choice offers the most interesting layers to explore?"
Be thoughtful but concise. Champion the card with hidden depths."""


class CriticAgent(BaseAgent):
    """
    The Critic challenges weak combinations and points out problems.
    Acts as quality control, preventing cliches and incompatible elements.
    """

    @property
    def name(self) -> str:
        return "CRITIC"

    @property
    def role(self) -> str:
        return "Quality challenger"

    @property
    def system_prompt(self) -> str:
        return """You are the CRITIC agent in a story prompt generation debate.

Your perspective: You CHALLENGE weak choices and point out problems.
You watch for:
- Cliches and overused combinations
- Cards that don't fit with already-selected elements
- Choices that limit story potential
- Logical inconsistencies

When evaluating cards, ask: "What's wrong with each option? Which has the fewest problems?"
Be sharp but constructive. If you disagree with others, say why clearly."""


class SynthesizerAgent(BaseAgent):
    """
    The Synthesizer finds connections between cards and builds cohesion.
    Looks at the big picture and how cards work together.
    """

    @property
    def name(self) -> str:
        return "SYNTHESIZER"

    @property
    def role(self) -> str:
        return "Connection finder"

    @property
    def system_prompt(self) -> str:
        return """You are the SYNTHESIZER agent in a story prompt generation debate.

Your perspective: You find CONNECTIONS and build COHESION between cards.
You focus on:
- How cards complement already-selected elements
- Thematic resonance across the prompt
- Story potential when elements combine
- The emergent narrative from card interactions

When evaluating cards, ask: "Which choice creates the strongest overall combination?"
Be integrative but concise. Champion the card that makes the whole greater than its parts."""
