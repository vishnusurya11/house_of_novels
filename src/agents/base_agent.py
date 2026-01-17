"""
Base agent class with OpenRouter integration via LangChain.
"""

from abc import ABC, abstractmethod
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from src.config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, DEFAULT_MODEL


class BaseAgent(ABC):
    """Base class for all debate agents."""

    def __init__(self, model: str = DEFAULT_MODEL):
        self.model_name = model
        self.llm = ChatOpenAI(
            model=model,
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL,
            temperature=0.7,
        )

    @property
    @abstractmethod
    def name(self) -> str:
        """Agent's display name."""
        pass

    @property
    @abstractmethod
    def role(self) -> str:
        """Agent's role description."""
        pass

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """System prompt defining agent's personality and approach."""
        pass

    def respond(self, context: str, cards: list[str], card_type: str,
                previous_messages: list[str] = None) -> str:
        """
        Generate agent's response about card choices.

        Args:
            context: Current story context (previously selected cards)
            cards: List of 4 card options to choose from
            card_type: Type of card being discussed (e.g., "agents", "engines")
            previous_messages: Previous debate messages from other agents

        Returns:
            Agent's opinion/argument as a string
        """
        previous = ""
        if previous_messages:
            previous = "\n\nPrevious discussion:\n" + "\n".join(previous_messages)

        cards_formatted = "\n".join(f"  {i+1}. {card}" for i, card in enumerate(cards))

        user_prompt = f"""We are selecting a {card_type.upper()} card for a story prompt.

Current story context:
{context if context else "(Starting fresh - no cards selected yet)"}

Available {card_type} options:
{cards_formatted}
{previous}

Based on your perspective as {self.name}, which card do you advocate for and why?
Keep your response concise (2-3 sentences). State your preferred card number and reasoning."""

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=user_prompt),
        ]

        response = self.llm.invoke(messages)
        return f"**{self.name}**: {response.content}"

    def vote(self, context: str, cards: list[str], card_type: str,
             debate_transcript: str) -> int:
        """
        Cast a vote for the best card after debate.

        Args:
            context: Current story context
            cards: List of 4 card options
            card_type: Type of card being voted on
            debate_transcript: Full debate transcript

        Returns:
            Index (0-3) of chosen card
        """
        cards_formatted = "\n".join(f"  {i+1}. {card}" for i, card in enumerate(cards))

        user_prompt = f"""Based on the debate, cast your final vote for the {card_type.upper()} card.

Current story context:
{context if context else "(Starting fresh)"}

Options:
{cards_formatted}

Debate transcript:
{debate_transcript}

Reply with ONLY a single number (1, 2, 3, or 4) representing your vote."""

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=user_prompt),
        ]

        response = self.llm.invoke(messages)

        # Parse the vote (extract first digit found)
        for char in response.content:
            if char in "1234":
                return int(char) - 1  # Convert to 0-indexed

        # Default to first card if parsing fails
        return 0
