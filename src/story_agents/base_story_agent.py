"""
Base class for story builder agents with OpenRouter integration.
"""

from abc import ABC, abstractmethod
from typing import Type, TypeVar

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from src.config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, DEFAULT_MODEL

T = TypeVar("T", bound=BaseModel)


class BaseStoryAgent(ABC):
    """Base class for all story builder agents."""

    def __init__(self, model: str = DEFAULT_MODEL, temperature: float = 0.7):
        self.model_name = model
        self.temperature = temperature
        self.llm = ChatOpenAI(
            model=model,
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL,
            temperature=temperature,
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

    def invoke(self, user_prompt: str) -> str:
        """
        Send a prompt to the LLM and get a response.

        Args:
            user_prompt: The user message to send

        Returns:
            The LLM's response content
        """
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=user_prompt),
        ]
        response = self.llm.invoke(messages)
        return response.content

    def invoke_with_json(self, user_prompt: str) -> str:
        """
        Send a prompt expecting JSON response.

        Args:
            user_prompt: The user message to send

        Returns:
            The LLM's response content (should be JSON)
        """
        json_instruction = (
            "\n\nIMPORTANT: Respond ONLY with valid JSON. "
            "No markdown code blocks, no explanations, just raw JSON."
        )
        return self.invoke(user_prompt + json_instruction)

    def invoke_structured(self, user_prompt: str, schema: Type[T],
                           max_tokens: int = 2000) -> T:
        """
        Invoke LLM with structured output enforcement via Pydantic schema.

        Uses LangChain's with_structured_output() to force the model
        to return data matching the provided Pydantic schema.

        Args:
            user_prompt: The prompt to send
            schema: Pydantic model class to enforce
            max_tokens: Maximum completion tokens (prevents hitting model limits)

        Returns:
            Parsed Pydantic model instance
        """
        # Use function_calling method to avoid strict JSON schema requirements
        # (OpenAI's strict mode requires additionalProperties: false at every level)
        structured_llm = self.llm.with_structured_output(schema, method="function_calling")
        # Bind max_tokens to prevent hitting completion token limits
        limited_llm = structured_llm.bind(max_tokens=max_tokens)
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=user_prompt),
        ]
        try:
            result = limited_llm.invoke(messages)
            if result is None:
                print(f"\n⚠️  WARNING: {self.name} received None from LLM (schema: {schema.__name__})")
                print(f"   This usually means the LLM response couldn't be parsed into the schema.")
            return result
        except Exception as e:
            error_msg = str(e)
            print(f"\n❌ ERROR in {self.name}.invoke_structured():")
            print(f"   Schema: {schema.__name__}")
            print(f"   Error: {error_msg[:300]}")
            raise  # Re-raise so caller's except block can handle it
