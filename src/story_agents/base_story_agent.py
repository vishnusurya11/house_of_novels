"""
Base class for story builder agents with OpenRouter integration.
"""

import hashlib
import inspect
import json
import threading
from abc import ABC, abstractmethod
from typing import Type, TypeVar, Union, Tuple

import httpx
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from src.config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, DEFAULT_MODEL, FALLBACK_MODELS, GLOBAL_CONFIG

T = TypeVar("T", bound=BaseModel)

# --- Global rate limiter (Change 4) ---
# Caps total concurrent API calls across all threads/agents
_MAX_CONCURRENT = GLOBAL_CONFIG.get("max_concurrent_api_calls", 25)
_API_SEMAPHORE = threading.Semaphore(_MAX_CONCURRENT)

# --- Shared HTTP connection pool (Change 5) ---
# Tuned for high concurrency: more keepalive connections, longer read timeout for LLM responses
_SHARED_HTTP_CLIENT = httpx.Client(
    limits=httpx.Limits(max_connections=150, max_keepalive_connections=80),
    timeout=httpx.Timeout(connect=10.0, read=180.0, write=10.0, pool=30.0),
)

# --- Thread-local storage for step context ---
# Allows threaded callers (e.g. Step 6 chapter workers) to set step_context
# so invoke_structured() can scope model bans correctly instead of "unknown"
_thread_local = threading.local()

# --- Disk-based LLM response cache (Change 6) ---
try:
    import diskcache
    _LLM_CACHE = diskcache.Cache(".llm_cache", size_limit=1_000_000_000)  # 1GB
except ImportError:
    _LLM_CACHE = None


def _cache_key(prompt: str, system_prompt: str, model: str, schema_name: str, max_tokens: int) -> str:
    """Generate a deterministic cache key from prompt + model + schema."""
    content = f"{model}:{schema_name}:{max_tokens}:{system_prompt}:{prompt}"
    return hashlib.md5(content.encode()).hexdigest()


class BaseStoryAgent(ABC):
    """Base class for all story builder agents."""

    # Class-level dict of models banned per-step (not globally)
    # Format: {step_name: {banned_model1, banned_model2, ...}}
    _step_banned_models: dict = {}
    _ban_lock = threading.Lock()  # Thread-safe access to _step_banned_models

    def __init__(self, model: str = DEFAULT_MODEL, temperature: float = 0.7):
        self.model_name = model
        self.temperature = temperature
        self.llm = ChatOpenAI(
            model=model,
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL,
            temperature=temperature,
            http_client=_SHARED_HTTP_CLIENT,
        )
        # Token tracking for this agent instance
        self._token_tracker = {
            'total_prompt_tokens': 0,
            'total_completion_tokens': 0,
            'total_tokens': 0,
            'call_count': 0,
            'calls': []  # List of individual call token usage
        }

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
                           max_tokens: int = 16000, max_retries: int = 2,
                           return_usage: bool = False) -> Union[T, Tuple[T, dict]]:
        """
        Invoke LLM with structured output enforcement via Pydantic schema.
        Retries with validation error feedback if initial attempts fail.
        Automatically falls back to alternative models if primary model fails.

        Uses LangChain's with_structured_output() with strict JSON schema enforcement
        for OpenRouter compatibility (gpt-5-nano, gpt-4.1-mini, etc.).

        Args:
            user_prompt: The prompt to send
            schema: Pydantic model class to enforce
            max_tokens: Maximum completion tokens (includes reasoning + output for GPT-5-nano)
            max_retries: Number of retry attempts if validation fails (default: 2)
            return_usage: If True, return tuple of (result, usage_dict) instead of just result

        Returns:
            If return_usage=False: Parsed Pydantic model instance
            If return_usage=True: Tuple of (model_instance, usage_dict) where usage_dict contains:
                - prompt_tokens: Number of input tokens
                - completion_tokens: Number of output tokens
                - total_tokens: Total tokens used
                - model: Model name that successfully returned the result
        """
        # Check disk cache first (Change 6)
        cache_k = None
        if _LLM_CACHE is not None:
            cache_k = _cache_key(user_prompt, self.system_prompt, self.model_name, schema.__name__, max_tokens)
            cached = _LLM_CACHE.get(cache_k)
            if cached is not None:
                result = schema.model_validate(cached['data'])
                usage_dict = cached.get('usage', {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0, 'model': cached.get('model', self.model_name)})
                self._track_tokens(usage_dict)
                if return_usage:
                    return result, usage_dict
                return result

        # Detect which step we're in: prefer thread-local (set by threaded callers),
        # then fall back to call stack inspection
        step_context = getattr(_thread_local, 'step_context', None)
        if not step_context:
            step_context = "unknown"
            for frame_info in inspect.stack():
                func_name = frame_info.function
                if func_name.startswith("step"):  # e.g., "step5_chapter_scene_breakdown"
                    step_context = func_name
                    break

        # Build list of models to try: primary + fallbacks (EXCLUDING banned for THIS step)
        all_models = [self.model_name] + FALLBACK_MODELS

        # Get banned models for this specific step only (thread-safe)
        with BaseStoryAgent._ban_lock:
            step_banned = BaseStoryAgent._step_banned_models.get(step_context, set()).copy()
        models_to_try = [m for m in all_models if m not in step_banned]

        # If all models banned for this step, reset step-specific ban list
        if not models_to_try:
            print(f"⚠️  All models banned for step '{step_context}' - resetting step ban list")
            with BaseStoryAgent._ban_lock:
                BaseStoryAgent._step_banned_models[step_context] = set()
            models_to_try = all_models

        for model_index, current_model in enumerate(models_to_try):
            # Create LLM instance for current model
            if current_model != self.model_name:
                print(f"\n🔄 Switching to fallback model: {current_model}")
                current_llm = ChatOpenAI(
                    model=current_model,
                    api_key=OPENROUTER_API_KEY,
                    base_url=OPENROUTER_BASE_URL,
                    temperature=self.temperature,
                    http_client=_SHARED_HTTP_CLIENT,
                )
            else:
                current_llm = self.llm

            # Use json_schema method with strict=True for better OpenRouter compatibility
            try:
                structured_llm = current_llm.with_structured_output(
                    schema,
                    method="json_schema",
                    strict=True,  # Enable strict JSON schema enforcement (OpenRouter requirement)
                    include_raw=True  # Include raw AIMessage with token usage metadata
                )
            except Exception as e:
                # Fallback to function_calling if json_schema not supported
                print(f"⚠️  WARNING: json_schema method not supported, falling back to function_calling: {e}")
                structured_llm = current_llm.with_structured_output(
                    schema,
                    method="function_calling",
                    include_raw=True  # Include raw AIMessage
                )

            # Bind max_tokens to prevent hitting completion token limits
            limited_llm = structured_llm.bind(max_tokens=max_tokens)
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=user_prompt),
            ]

            for attempt in range(max_retries + 1):
                try:
                    # Acquire global semaphore to cap concurrent API calls (Change 4)
                    with _API_SEMAPHORE:
                        response = limited_llm.invoke(messages)

                    # Extract parsed model and raw message (include_raw=True returns dict)
                    if isinstance(response, dict) and 'parsed' in response:
                        result = response['parsed']
                        raw_message = response.get('raw')
                    else:
                        # Fallback for non-include_raw mode
                        result = response
                        raw_message = response

                    if result is None:
                        print(f"\n⚠️  WARNING: {self.name} received None from LLM (schema: {schema.__name__}, attempt {attempt + 1}/{max_retries + 1})")
                        print(f"   This usually means the LLM response couldn't be parsed into the schema.")
                        if attempt < max_retries:
                            print(f"   Retrying with explicit field requirements...")
                            # Add retry instruction
                            messages.append(HumanMessage(content=f"""
RETRY REQUEST: Previous response was None (validation failed).

Please ensure you provide ALL required fields for {schema.__name__}:
{', '.join(f'"{field}"' for field in schema.__annotations__.keys())}

Try again with complete data for every field."""))
                            continue
                        else:
                            # Failed all retries with this model
                            break

                    # Success! Log if we used a fallback
                    if current_model != self.model_name:
                        print(f"✅ SUCCESS with fallback model: {current_model}")

                    # Extract token usage from raw message and track it
                    usage_dict = self._extract_token_usage(raw_message, current_model)
                    self._track_tokens(usage_dict)

                    # Store in disk cache (Change 6)
                    if _LLM_CACHE is not None and cache_k is not None:
                        try:
                            _LLM_CACHE.set(cache_k, {
                                'data': result.model_dump(),
                                'usage': usage_dict,
                                'model': current_model,
                            })
                        except Exception:
                            pass  # Cache write failure is non-fatal

                    # Return with or without token usage based on parameter
                    if return_usage:
                        return result, usage_dict
                    return result

                except Exception as e:
                    error_msg = str(e)
                    print(f"\n❌ ERROR in {self.name}.invoke_structured() (Attempt {attempt + 1}/{max_retries + 1}):")
                    print(f"   Model: {current_model}")
                    print(f"   Schema: {schema.__name__}")
                    print(f"   Error: {error_msg[:300]}")

                    # Check if this is a reasoning token error - skip to next model immediately
                    if "length limit was reached" in error_msg and "reasoning_tokens" in error_msg:
                        print(f"⚠️  Reasoning token error detected with {current_model}")
                        # Ban this model for THIS STEP ONLY (not globally, thread-safe)
                        with BaseStoryAgent._ban_lock:
                            if step_context not in BaseStoryAgent._step_banned_models:
                                BaseStoryAgent._step_banned_models[step_context] = set()
                            BaseStoryAgent._step_banned_models[step_context].add(current_model)
                        print(f"🚫 Banning {current_model} for step '{step_context}' only (reasoning token issues)")
                        print(f"   Banned for this step: {BaseStoryAgent._step_banned_models[step_context]}")
                        break  # Skip remaining retries with this model

                    if attempt < max_retries:
                        # Extract missing field info from error if possible
                        print(f"   Retrying with error feedback...")
                        messages.append(HumanMessage(content=f"""
VALIDATION ERROR: {error_msg[:500]}

Please try again and ensure ALL required fields are present:
- Check that you included: {', '.join(f'"{field}"' for field in schema.__annotations__.keys())}
- Provide complete data for each field
- Do not omit any required field

Return your response with COMPLETE data."""))
                    else:
                        # Last attempt with this model failed
                        if model_index < len(models_to_try) - 1:
                            print(f"   All retries exhausted with {current_model}, trying fallback...")
                            break  # Try next model
                        else:
                            raise  # No more models to try, re-raise error

        # If we get here, all models failed
        raise RuntimeError(f"All models failed: {', '.join(models_to_try)}")

    def _extract_token_usage(self, result, model_name: str) -> dict:
        """
        Extract token usage from LangChain AIMessage response.

        Args:
            result: The AIMessage or Pydantic model result from LLM
            model_name: Name of the model that generated this result

        Returns:
            Dictionary with token usage:
                - prompt_tokens: Number of input tokens
                - completion_tokens: Number of output tokens
                - total_tokens: Total tokens
                - model: Model name
        """
        usage = {
            'prompt_tokens': 0,
            'completion_tokens': 0,
            'total_tokens': 0,
            'model': model_name,
        }

        # Check if result has response metadata (raw AIMessage)
        if hasattr(result, 'response_metadata'):
            metadata = result.response_metadata
            if 'token_usage' in metadata:
                token_usage = metadata['token_usage']
                usage['prompt_tokens'] = token_usage.get('prompt_tokens', 0)
                usage['completion_tokens'] = token_usage.get('completion_tokens', 0)
                usage['total_tokens'] = token_usage.get('total_tokens', 0)
                return usage

        # Check if result has usage_metadata (newer LangChain format)
        if hasattr(result, 'usage_metadata'):
            metadata = result.usage_metadata
            if metadata:
                usage['prompt_tokens'] = metadata.get('input_tokens', 0)
                usage['completion_tokens'] = metadata.get('output_tokens', 0)
                usage['total_tokens'] = metadata.get('total_tokens', 0)
                return usage

        # For structured output, the actual response might be nested
        # Try to access the raw response if available
        if hasattr(result, '__pydantic_extra__'):
            extra = result.__pydantic_extra__
            if extra and 'response_metadata' in extra:
                metadata = extra['response_metadata']
                if 'token_usage' in metadata:
                    token_usage = metadata['token_usage']
                    usage['prompt_tokens'] = token_usage.get('prompt_tokens', 0)
                    usage['completion_tokens'] = token_usage.get('completion_tokens', 0)
                    usage['total_tokens'] = token_usage.get('total_tokens', 0)

        return usage

    def _track_tokens(self, usage_dict: dict):
        """
        Track token usage for this agent instance.

        Args:
            usage_dict: Dictionary with prompt_tokens, completion_tokens, total_tokens, model
        """
        self._token_tracker['total_prompt_tokens'] += usage_dict.get('prompt_tokens', 0)
        self._token_tracker['total_completion_tokens'] += usage_dict.get('completion_tokens', 0)
        self._token_tracker['total_tokens'] += usage_dict.get('total_tokens', 0)
        self._token_tracker['call_count'] += 1
        self._token_tracker['calls'].append(usage_dict)

    def get_token_usage(self) -> dict:
        """
        Get accumulated token usage for this agent instance.

        Returns:
            Dictionary with total token usage stats
        """
        return {
            'total_prompt_tokens': self._token_tracker['total_prompt_tokens'],
            'total_completion_tokens': self._token_tracker['total_completion_tokens'],
            'total_tokens': self._token_tracker['total_tokens'],
            'call_count': self._token_tracker['call_count'],
        }

    def reset_token_tracking(self):
        """Reset token tracking for this agent instance."""
        self._token_tracker = {
            'total_prompt_tokens': 0,
            'total_completion_tokens': 0,
            'total_tokens': 0,
            'call_count': 0,
            'calls': []
        }
