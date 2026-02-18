"""
World Pressure Agents for Step 4: World Building.

Council of 4 agents that debate thematic world pressures:
- Sociologist: Class/caste/social hierarchy
- Economist: Resource scarcity, wealth inequality
- Politician: Power structures, laws, governance
- Culturalist: Beliefs, traditions, taboos
"""

from src.story_agents.base_story_agent import BaseStoryAgent
from src.story_schemas import (
    WorldPressureProposal,
    WorldPressureCritique,
    WorldPressureVote,
)


class WorldSociologistAgent(BaseStoryAgent):
    """Focuses on social hierarchy and class-based pressures."""

    @property
    def name(self) -> str:
        return "WORLD_SOCIOLOGIST"

    @property
    def role(self) -> str:
        return "World Sociologist - Social Hierarchy Expert"

    @property
    def system_prompt(self) -> str:
        return """You are a World Sociologist agent specializing in social structures and class dynamics.

Your expertise:
- Social hierarchies: castes, classes, nobility vs commoners
- Privilege and discrimination based on birth, status, or identity
- Social mobility barriers and opportunities
- Institutional power imbalances
- How social position constrains or enables choices

When proposing world pressures, focus on:
1. Creating social hierarchies that test characters' beliefs
2. Designing class conflicts that force moral choices
3. Building systems of privilege and oppression
4. Showing how social position shapes worldview

Your goal: Create social pressures that make the thematic question unavoidable."""

    def propose_world_pressure(
        self,
        theme_question: str,
        story_shape: str,
        world_context: str,
    ) -> WorldPressureProposal:
        """Propose world pressure structure focused on social dynamics."""
        user_prompt = f"""Create thematic world pressures that test this question: "{theme_question}"

STORY SHAPE: {story_shape}
WORLD CONTEXT: {world_context}

Design world pressures where:
- SOCIETAL: Social hierarchy/class/caste pressures (YOUR PRIMARY FOCUS)
- ECONOMIC: Resource scarcity and wealth inequality
- POLITICAL: Power structures and governance
- CULTURAL: Beliefs and traditions
- THEMATIC_INTEGRATION: How all pressures force the central question

Focus your societal pressure on class dynamics, privilege, and social barriers.
Make the other pressures support and reinforce the social structure.

Return a WorldPressureProposal with your design."""

        return self.invoke_structured(user_prompt, WorldPressureProposal, max_tokens=8000)

    def critique_world_pressures(
        self,
        proposals: list[WorldPressureProposal],
        theme_question: str,
    ) -> list[WorldPressureCritique]:
        """Critique all world pressure proposals."""
        critiques = []
        for i, proposal in enumerate(proposals):
            user_prompt = f"""Critique this world pressure proposal for the question: "{theme_question}"

PROPOSAL {i} (by {proposal.agent_name}):
- Societal: {proposal.world_pressure.societal}
- Economic: {proposal.world_pressure.economic}
- Political: {proposal.world_pressure.political}
- Cultural: {proposal.world_pressure.cultural}
- Integration: {proposal.world_pressure.thematic_integration}

Evaluate:
1. Does the social hierarchy create meaningful constraints?
2. Do the pressures interact to test the theme?
3. Are there clear stakes for characters at different social levels?
4. Does this world make the thematic question unavoidable?

Score 1-10 and explain strengths/weaknesses."""

            critique = self.invoke_structured(
                user_prompt, WorldPressureCritique, max_tokens=8000
            )
            critique.proposal_index = i
            critiques.append(critique)
        return critiques

    def vote(
        self,
        proposals: list[WorldPressureProposal],
        theme_question: str,
    ) -> WorldPressureVote:
        """Vote for the best world pressure proposal."""
        proposals_text = "\n\n".join([
            f"PROPOSAL {i} (by {p.agent_name}):\n"
            f"- Societal: {p.world_pressure.societal}\n"
            f"- Economic: {p.world_pressure.economic}\n"
            f"- Political: {p.world_pressure.political}\n"
            f"- Cultural: {p.world_pressure.cultural}"
            for i, p in enumerate(proposals)
        ])

        user_prompt = f"""Vote for the best world pressure design for: "{theme_question}"

{proposals_text}

Which proposal creates the most compelling social pressures that test the theme?
Return your vote as a WorldPressureVote."""

        return self.invoke_structured(user_prompt, WorldPressureVote, max_tokens=8000)


class WorldEconomistAgent(BaseStoryAgent):
    """Focuses on resource scarcity and economic pressures."""

    @property
    def name(self) -> str:
        return "WORLD_ECONOMIST"

    @property
    def role(self) -> str:
        return "World Economist - Resource Scarcity Expert"

    @property
    def system_prompt(self) -> str:
        return """You are a World Economist agent specializing in resource scarcity and economic pressures.

Your expertise:
- Resource scarcity: food, water, energy, materials
- Wealth inequality and poverty
- Survival pressures and desperation
- Economic systems and trade
- How scarcity forces impossible choices

When proposing world pressures, focus on:
1. Creating resource scarcity that tests characters' values
2. Designing economic systems that create moral dilemmas
3. Building survival pressures that force compromise
4. Showing how poverty/wealth shapes worldview

Your goal: Create economic pressures that make the thematic question unavoidable."""

    def propose_world_pressure(
        self,
        theme_question: str,
        story_shape: str,
        world_context: str,
    ) -> WorldPressureProposal:
        """Propose world pressure structure focused on economic dynamics."""
        user_prompt = f"""Create thematic world pressures that test this question: "{theme_question}"

STORY SHAPE: {story_shape}
WORLD CONTEXT: {world_context}

Design world pressures where:
- SOCIETAL: Social hierarchy/class/caste pressures
- ECONOMIC: Resource scarcity and wealth inequality (YOUR PRIMARY FOCUS)
- POLITICAL: Power structures and governance
- CULTURAL: Beliefs and traditions
- THEMATIC_INTEGRATION: How all pressures force the central question

Focus your economic pressure on scarcity, survival, and wealth inequality.
Make the other pressures support and reinforce the economic reality.

Return a WorldPressureProposal with your design."""

        return self.invoke_structured(user_prompt, WorldPressureProposal, max_tokens=8000)

    def critique_world_pressures(
        self,
        proposals: list[WorldPressureProposal],
        theme_question: str,
    ) -> list[WorldPressureCritique]:
        """Critique all world pressure proposals."""
        critiques = []
        for i, proposal in enumerate(proposals):
            user_prompt = f"""Critique this world pressure proposal for the question: "{theme_question}"

PROPOSAL {i} (by {proposal.agent_name}):
- Societal: {proposal.world_pressure.societal}
- Economic: {proposal.world_pressure.economic}
- Political: {proposal.world_pressure.political}
- Cultural: {proposal.world_pressure.cultural}
- Integration: {proposal.world_pressure.thematic_integration}

Evaluate:
1. Does the economic pressure create real survival stakes?
2. Does scarcity force characters into moral dilemmas?
3. Do the pressures interact to test the theme?
4. Does this world make the thematic question unavoidable?

Score 1-10 and explain strengths/weaknesses."""

            critique = self.invoke_structured(
                user_prompt, WorldPressureCritique, max_tokens=8000
            )
            critique.proposal_index = i
            critiques.append(critique)
        return critiques

    def vote(
        self,
        proposals: list[WorldPressureProposal],
        theme_question: str,
    ) -> WorldPressureVote:
        """Vote for the best world pressure proposal."""
        proposals_text = "\n\n".join([
            f"PROPOSAL {i} (by {p.agent_name}):\n"
            f"- Societal: {p.world_pressure.societal}\n"
            f"- Economic: {p.world_pressure.economic}\n"
            f"- Political: {p.world_pressure.political}\n"
            f"- Cultural: {p.world_pressure.cultural}"
            for i, p in enumerate(proposals)
        ])

        user_prompt = f"""Vote for the best world pressure design for: "{theme_question}"

{proposals_text}

Which proposal creates the most compelling economic pressures that test the theme?
Return your vote as a WorldPressureVote."""

        return self.invoke_structured(user_prompt, WorldPressureVote, max_tokens=8000)


class WorldPoliticianAgent(BaseStoryAgent):
    """Focuses on power structures and political pressures."""

    @property
    def name(self) -> str:
        return "WORLD_POLITICIAN"

    @property
    def role(self) -> str:
        return "World Politician - Power Structure Expert"

    @property
    def system_prompt(self) -> str:
        return """You are a World Politician agent specializing in power structures and governance.

Your expertise:
- Political systems: monarchy, democracy, oligarchy, tyranny
- Laws and legal systems
- Enforcement and punishment
- Corruption and abuse of power
- How power structures constrain choices

When proposing world pressures, focus on:
1. Creating power structures that test characters' beliefs
2. Designing laws that force moral dilemmas
3. Building systems of control and oppression
4. Showing how political power shapes worldview

Your goal: Create political pressures that make the thematic question unavoidable."""

    def propose_world_pressure(
        self,
        theme_question: str,
        story_shape: str,
        world_context: str,
    ) -> WorldPressureProposal:
        """Propose world pressure structure focused on political dynamics."""
        user_prompt = f"""Create thematic world pressures that test this question: "{theme_question}"

STORY SHAPE: {story_shape}
WORLD CONTEXT: {world_context}

Design world pressures where:
- SOCIETAL: Social hierarchy/class/caste pressures
- ECONOMIC: Resource scarcity and wealth inequality
- POLITICAL: Power structures and governance (YOUR PRIMARY FOCUS)
- CULTURAL: Beliefs and traditions
- THEMATIC_INTEGRATION: How all pressures force the central question

Focus your political pressure on laws, enforcement, and power dynamics.
Make the other pressures support and reinforce the political reality.

Return a WorldPressureProposal with your design."""

        return self.invoke_structured(user_prompt, WorldPressureProposal, max_tokens=8000)

    def critique_world_pressures(
        self,
        proposals: list[WorldPressureProposal],
        theme_question: str,
    ) -> list[WorldPressureCritique]:
        """Critique all world pressure proposals."""
        critiques = []
        for i, proposal in enumerate(proposals):
            user_prompt = f"""Critique this world pressure proposal for the question: "{theme_question}"

PROPOSAL {i} (by {proposal.agent_name}):
- Societal: {proposal.world_pressure.societal}
- Economic: {proposal.world_pressure.economic}
- Political: {proposal.world_pressure.political}
- Cultural: {proposal.world_pressure.cultural}
- Integration: {proposal.world_pressure.thematic_integration}

Evaluate:
1. Does the political structure create meaningful constraints?
2. Do laws and enforcement force moral dilemmas?
3. Do the pressures interact to test the theme?
4. Does this world make the thematic question unavoidable?

Score 1-10 and explain strengths/weaknesses."""

            critique = self.invoke_structured(
                user_prompt, WorldPressureCritique, max_tokens=8000
            )
            critique.proposal_index = i
            critiques.append(critique)
        return critiques

    def vote(
        self,
        proposals: list[WorldPressureProposal],
        theme_question: str,
    ) -> WorldPressureVote:
        """Vote for the best world pressure proposal."""
        proposals_text = "\n\n".join([
            f"PROPOSAL {i} (by {p.agent_name}):\n"
            f"- Societal: {p.world_pressure.societal}\n"
            f"- Economic: {p.world_pressure.economic}\n"
            f"- Political: {p.world_pressure.political}\n"
            f"- Cultural: {p.world_pressure.cultural}"
            for i, p in enumerate(proposals)
        ])

        user_prompt = f"""Vote for the best world pressure design for: "{theme_question}"

{proposals_text}

Which proposal creates the most compelling political pressures that test the theme?
Return your vote as a WorldPressureVote."""

        return self.invoke_structured(user_prompt, WorldPressureVote, max_tokens=8000)


class WorldCulturalistAgent(BaseStoryAgent):
    """Focuses on cultural beliefs and traditions."""

    @property
    def name(self) -> str:
        return "WORLD_CULTURALIST"

    @property
    def role(self) -> str:
        return "World Culturalist - Belief System Expert"

    @property
    def system_prompt(self) -> str:
        return """You are a World Culturalist agent specializing in belief systems and traditions.

Your expertise:
- Cultural beliefs and worldviews
- Traditions, rituals, and customs
- Taboos and social norms
- Religion and spirituality
- How culture shapes perception and choice

When proposing world pressures, focus on:
1. Creating cultural beliefs that test characters' values
2. Designing traditions that create moral dilemmas
3. Building taboos that force impossible choices
4. Showing how culture shapes worldview

Your goal: Create cultural pressures that make the thematic question unavoidable."""

    def propose_world_pressure(
        self,
        theme_question: str,
        story_shape: str,
        world_context: str,
    ) -> WorldPressureProposal:
        """Propose world pressure structure focused on cultural dynamics."""
        user_prompt = f"""Create thematic world pressures that test this question: "{theme_question}"

STORY SHAPE: {story_shape}
WORLD CONTEXT: {world_context}

Design world pressures where:
- SOCIETAL: Social hierarchy/class/caste pressures
- ECONOMIC: Resource scarcity and wealth inequality
- POLITICAL: Power structures and governance
- CULTURAL: Beliefs and traditions (YOUR PRIMARY FOCUS)
- THEMATIC_INTEGRATION: How all pressures force the central question

Focus your cultural pressure on beliefs, traditions, and taboos.
Make the other pressures support and reinforce the cultural reality.

Return a WorldPressureProposal with your design."""

        return self.invoke_structured(user_prompt, WorldPressureProposal, max_tokens=8000)

    def critique_world_pressures(
        self,
        proposals: list[WorldPressureProposal],
        theme_question: str,
    ) -> list[WorldPressureCritique]:
        """Critique all world pressure proposals."""
        critiques = []
        for i, proposal in enumerate(proposals):
            user_prompt = f"""Critique this world pressure proposal for the question: "{theme_question}"

PROPOSAL {i} (by {proposal.agent_name}):
- Societal: {proposal.world_pressure.societal}
- Economic: {proposal.world_pressure.economic}
- Political: {proposal.world_pressure.political}
- Cultural: {proposal.world_pressure.cultural}
- Integration: {proposal.world_pressure.thematic_integration}

Evaluate:
1. Does the cultural system create meaningful beliefs that matter?
2. Do traditions and taboos force moral dilemmas?
3. Do the pressures interact to test the theme?
4. Does this world make the thematic question unavoidable?

Score 1-10 and explain strengths/weaknesses."""

            critique = self.invoke_structured(
                user_prompt, WorldPressureCritique, max_tokens=8000
            )
            critique.proposal_index = i
            critiques.append(critique)
        return critiques

    def vote(
        self,
        proposals: list[WorldPressureProposal],
        theme_question: str,
    ) -> WorldPressureVote:
        """Vote for the best world pressure proposal."""
        proposals_text = "\n\n".join([
            f"PROPOSAL {i} (by {p.agent_name}):\n"
            f"- Societal: {p.world_pressure.societal}\n"
            f"- Economic: {p.world_pressure.economic}\n"
            f"- Political: {p.world_pressure.political}\n"
            f"- Cultural: {p.world_pressure.cultural}"
            for i, p in enumerate(proposals)
        ])

        user_prompt = f"""Vote for the best world pressure design for: "{theme_question}"

{proposals_text}

Which proposal creates the most compelling cultural pressures that test the theme?
Return your vote as a WorldPressureVote."""

        return self.invoke_structured(user_prompt, WorldPressureVote, max_tokens=8000)
