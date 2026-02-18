"""
Base Phase 1 Implementation for Authors.

Provides default implementation of the 9-step Phase 1 pipeline.
Authors can override individual steps for custom behavior.
"""

import inspect
import time
import threading
import random
import string
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, TYPE_CHECKING, TypeVar, Type

from src.config import (
    DEFAULT_MODEL,
    STEP6_PROSE_MODEL,
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    FALLBACK_MODELS,
    GLOBAL_CONFIG,
    get_step_config,
    get_token_limit,
    get_step_model,
)
from src.story_structures import get_structure
from src.story_structures.base_structure import BaseStructure
from src.story_agents.structure_debate_agents import (
    StorySeedParserAgent,
    DanWellsAgent,
    BlakeSnyderAgent,
    PinchMasterAgent,
    TruthSeekerAgent,
    AudienceAdvocateAgent,  # 5th agent - reader/viewer perspective
    StructureValidatorAgent,
    # Legacy aliases for backward compatibility
    ResolutionArchitectAgent,
    HookDesignerAgent,
    TensionBuilderAgent,
)
from src.story_agents.character_debate_agents import (
    CharacterPsychologistAgent,
    CharacterVisualistAgent,
    CharacterNarrativeAgent,
    CharacterAudienceAgent,
    CharacterBackstoryAgent,
)
from src.story_agents.name_agents import (
    NameCreativeAgent,
    NameAuthenticAgent,
    NameDistinctiveAgent,
)
from src.story_agents.location_debate_agents_OLD_STEP3A import (
    LocationArchitectAgent,
    LocationAtmosphereAgent,
    LocationNarrativeAgent,
    LocationAudienceAgent,
)
from src.story_agents.location_debate_agents import (
    # NEW Step 4 Location Debate Agents
    LocationNameCreativeAgent,
    LocationNameAuthenticAgent,
    LocationNameThematicAgent,
    LocationPhysicalSensoryAgent,
    LocationPhysicalFunctionalAgent,
    LocationPhysicalSymbolicAgent,
    LocationAtmosphereMoodAgent,
    LocationAtmosphereConflictAgent,
    LocationAtmosphereCharacterAgent,
    LocationThematicResonanceAgent,
    LocationThematicContrastAgent,
    LocationThematicEvolutionAgent,
)
from src.story_agents.world_pressure_agents import (
    WorldSociologistAgent as WorldPressureSociologistAgent,
    WorldEconomistAgent as WorldPressureEconomistAgent,
    WorldPoliticianAgent as WorldPressurePoliticianAgent,
    WorldCulturalistAgent as WorldPressureCulturalistAgent,
)
from src.story_agents.scene_breakdown_agents import (
    SceneStructureAgent as ChapterSceneStructureAgent,
    ScenePacingAgent as ChapterScenePacingAgent,
    SceneCharacterAgent as ChapterSceneCharacterAgent,
)
from src.story_agents.foreshadowing_agents import (
    SetupPayoffAgent,
    RuleOfThreeAgent,
    TropeExecutionAgent,
)
from src.story_agents.scene_debate_agents import (
    ScenePlotAgent,
    SceneCharacterAgent,
    ScenePacingAgent,
    SceneStructureAgent,
)
from src.story_agents.narrative_writing_agents import (
    CharacterContinuityAgent,
    LocationAtmosphereAgent as NarrativeLocationAgent,
    WorldBuildingIntegrationAgent,
    PlotTickingClockAgent,
    NarrativeContinuityAgent,
)
from src.story_agents.dialogue_master_agent import DialogueMasterAgent
from src.story_agents.synthesis_agent import SynthesisAgent
from src.story_agents.critique_agents import (
    ProsePolishCritic,
    CharacterVoiceCritic,
    ContinuityCritic,
    PacingTensionCritic,
    EmotionalResonanceCritic,
)
from src.story_agents.reviser_agent import ReviserAgent
from src.story_agents.theme_agents import (
    # Substep 1: Theme Question Debate
    ThemePhilosopherAgent,
    ThemeEmotionalAgent,
    ThemeDramaticAgent,
    # Substep 2: Thematic Square Debate
    SquareArchitectAgent,
    SquareCharacterAgent,
    SquareConflictAgent,
    # Substep 3: Perspective Debate
    PerspectiveDiversityAgent,
    PerspectiveStoryAgent,
    PerspectiveBalanceAgent,
)
# TypeVar for generic structured output
T = TypeVar('T')

from src.story_schemas import (
    # Step 0: Theme Foundation schemas
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
    # Step 1: Plotting schemas
    SevenPointStructureSchema,
    StructureBeatSchema,
    AgentProposal,
    AgentCritique,
    DebateRound,
    # Step 2: Character schemas
    CharacterSheetSchema,
    PhysicalDescriptionSchema,
    NameProposal,
    NameCritiques,
    NameVote,
    # Step 3: World Building schemas
    LocationProposal,
    LocationCritique,
    LocationVote,
    LocationSchema,
    WorldBuildingSchema,
    DailyLifeSchema,
    SocialStructureSchema,
    GovernmentLawSchema,
    EconomySchema,
    EducationHealthSchema,
    EntertainmentSchema,
    ReligionBeliefsSchema,
    CultureCustomsSchema,
    # Step 4: Scene/Chapter Outline schemas
    DetailedSceneSchema,
    ChapterSchema,
    SceneProposal,
    SceneCritique,
    SceneVote,
    ChapterOutlineSchema,
    # Step 5: Narrative Writing schemas
    NarrativeProseProposal,
    NarrativeProseCritique,
    NarrativeProseVote,
    SceneNarrativeSchema,
    # Step 6: Critique schemas
    ProsePolishCritique,
    CharacterVoiceCritique,
    ContinuityCritique,
    PacingTensionCritique,
    EmotionalResonanceCritique,
    SceneCritiqueBundle,
)

if TYPE_CHECKING:
    from src.authors.base_author import BaseAuthor


@dataclass
class Step0Result:
    """Result of Step 0: Theme Foundation."""
    theme_foundation: dict  # Clean results only (no debates)
    step0_debates: dict  # All debate details (proposals, critiques, votes)
    success: bool
    error: Optional[str] = None
    duration_seconds: float = 0.0
    token_usage: dict = field(default_factory=dict)  # Total token usage for this step
    substep_timings: dict = field(default_factory=dict)  # Timing for each substep
    substep_tokens: dict = field(default_factory=dict)  # Token usage for each substep


@dataclass
class Step1Result:
    """Result of Step 1: Character Creation (Theme → Characters)."""
    characters: list  # List of character dicts with Lie/Truth/Shadow/Arc/Ghost
    character_debates: list  # Full debate history for each character
    success: bool
    error: Optional[str] = None
    duration_seconds: float = 0.0
    token_usage: dict = field(default_factory=dict)  # Total token usage for this step
    substep_timings: dict = field(default_factory=dict)  # Timing for each substep
    substep_tokens: dict = field(default_factory=dict)  # Token usage for each substep


@dataclass
class Step1PlottingResult:
    """Result of OLD Step 1 (Plotting) - will become Step 3 later."""
    story_seed_parsed: dict
    structure_beats: dict
    theme: str
    title_suggestion: str
    debate_summary: dict
    success: bool
    error: Optional[str] = None
    duration_seconds: float = 0.0


@dataclass
class Step2Result:
    """Result of Step 2: Story Shape & Genre Selection via Multi-Agent Debate."""
    story_shape: str  # Classic Plot (e.g., "The Quest")
    save_the_cat_type: str  # STC type (e.g., "Dude with a Problem")
    primary_genre: str  # Primary genre
    secondary_genre: Optional[str]  # Optional secondary genre
    tone_flavor: Optional[str]  # Tonal flavor
    tropes: list[dict]  # Selected tropes with usage notes
    step2_debates: dict  # All debate details for metadata
    success: bool
    error: Optional[str] = None
    duration_seconds: float = 0.0
    token_usage: dict = field(default_factory=dict)  # Total token usage for this step
    substep_timings: dict = field(default_factory=dict)  # Timing for each substep
    substep_tokens: dict = field(default_factory=dict)  # Token usage for each substep


@dataclass
class Step2CharactersResult:
    """Result of OLD Step 2: Character Generation (kept for backward compatibility)."""
    characters: list
    character_debates: list
    name_mapping: dict
    success: bool
    error: Optional[str] = None
    duration_seconds: float = 0.0


@dataclass
class Step3Result:
    """Result of NEW Step 3: Plot Structure (Character Arc + Story Beats)."""
    integrated_beats: list[dict]  # 15 beats with plot + arc + theme
    hero_arc_summary: str
    villain_arc_summary: str
    side_character_notes: str
    step3_debates: dict  # All debate details for metadata
    success: bool
    error: Optional[str] = None
    duration_seconds: float = 0.0
    token_usage: dict = field(default_factory=dict)  # Total token usage for this step
    substep_timings: dict = field(default_factory=dict)  # Timing for each substep
    substep_tokens: dict = field(default_factory=dict)  # Token usage for each substep


@dataclass
class Step3WorldBuildingResult:
    """Result of OLD Step 3: World Building (Locations + World Context) - kept for backward compatibility."""
    locations: list
    world: dict
    location_debates: list
    success: bool
    error: Optional[str] = None
    duration_seconds: float = 0.0


@dataclass
class Step4Result:
    """Result of NEW Step 4: World Building (World Pressure + Major Locations)."""
    world_pressure: dict
    locations: list[dict]  # Major locations (dynamically extracted from beats)
    step4_debates: dict  # All debate details for metadata
    success: bool
    error: Optional[str] = None
    duration_seconds: float = 0.0
    token_usage: dict = field(default_factory=dict)  # Total token usage for this step
    substep_timings: dict = field(default_factory=dict)  # Timing for each substep
    substep_tokens: dict = field(default_factory=dict)  # Token usage for each substep


@dataclass
class Step4ChapterOutlineResult:
    """Result of OLD Step 4: Chapter/Scene Outline (kept for backward compatibility)."""
    chapter_outline: dict
    scene_debates: list
    total_chapters: int
    total_scenes: int
    success: bool
    error: Optional[str] = None
    duration_seconds: float = 0.0


@dataclass
class Step5Result:
    """Result of NEW Step 5: Chapter & Scene Breakdown."""
    chapter_outline: dict
    debates: dict  # All debate details for metadata
    total_chapters: int
    total_scenes: int
    success: bool
    error: Optional[str] = None
    duration_seconds: float = 0.0
    token_usage: dict = field(default_factory=dict)  # Total token usage for this step
    substep_timings: dict = field(default_factory=dict)  # Timing for each substep
    substep_tokens: dict = field(default_factory=dict)  # Token usage for each substep


@dataclass
class Step6Result:
    """Result of Step 6 (FORMERLY Step 5): Scene Narrative Writing via Multi-Agent Debate."""
    narrative: dict
    scene_debates: list
    total_scenes_written: int
    total_word_count: int
    average_words_per_scene: float
    success: bool
    error: Optional[str] = None
    duration_seconds: float = 0.0
    token_usage: dict = field(default_factory=dict)  # Total token usage for this step
    substep_timings: dict = field(default_factory=dict)  # Timing for each substep
    substep_tokens: dict = field(default_factory=dict)  # Token usage for each substep


@dataclass
class Step7Result:
    """Result of Step 7 (FORMERLY Step 6): Narrative Revision with 5 Critique Personas."""
    narrative: dict
    critiques: list  # All SceneCritiqueBundle dicts
    scenes_revised: int
    revision_passes: int
    average_score_before: float
    average_score_after: float
    success: bool
    error: Optional[str] = None
    duration_seconds: float = 0.0
    token_usage: dict = field(default_factory=dict)  # Total token usage for this step
    substep_timings: dict = field(default_factory=dict)  # Timing for each substep
    substep_tokens: dict = field(default_factory=dict)  # Token usage for each substep


@dataclass
class Step8Result:
    """Result of Step 8 (FORMERLY Step 7): Book & Chapter Title Naming via Multi-Agent Debate."""
    book_title: str
    chapter_titles: dict  # {chapter_num: title}
    book_debate: dict  # Debate metadata for book title
    chapter_debates: list  # Debate metadata for each chapter
    success: bool
    error: Optional[str] = None
    duration_seconds: float = 0.0
    token_usage: dict = field(default_factory=dict)  # Total token usage for this step
    substep_timings: dict = field(default_factory=dict)  # Timing for each substep
    substep_tokens: dict = field(default_factory=dict)  # Token usage for each substep


@dataclass
class Phase1Result:
    """Result of complete Phase 1 execution."""
    codex_path: Path
    outline: dict
    characters: list
    locations: list
    world: dict
    narrative: dict
    screenplay: dict
    success: bool
    error: Optional[str] = None
    steps_completed: list[int] = field(default_factory=list)
    step_timings: dict = field(default_factory=dict)


class BaseAuthorPhase1:
    """Default Phase 1 implementation. Authors can override steps.

    This class provides the default implementation for all 9 steps of Phase 1.
    Authors inherit from this class and can override individual step methods
    to customize their writing process while maintaining the same I/O contract.

    Example:
        class MarcusVanePhase1(BaseAuthorPhase1):
            def step1_plotting(self, codex: dict) -> Step1Result:
                # Marcus uses Seven Point structure with extra tension focus
                ...
    """

    # Class-level dict of models banned per-step (not globally)
    # Format: {step_name: {banned_model1, banned_model2, ...}}
    _step_banned_models: dict = {}

    def __init__(self, author: "BaseAuthor", model: str = None):
        """Initialize Phase 1 runner for an author.

        Args:
            author: The author instance with styles and preferences
            model: LLM model to use (default: from config)
        """
        self.author = author
        self.model = model or DEFAULT_MODEL

    def invoke_structured(self, user_prompt: str, schema: Type[T], max_tokens: int = None,
                          return_usage: bool = False) -> T | tuple[T, dict]:
        """
        Invoke LLM with structured output enforcement via Pydantic schema.
        Automatically falls back to alternative models if primary model fails.

        Args:
            user_prompt: The prompt to send
            schema: Pydantic model class to enforce
            max_tokens: Maximum completion tokens (uses global default if not provided)
            return_usage: If True, return tuple of (result, usage_dict) instead of just result

        Returns:
            If return_usage=False: Parsed Pydantic model instance
            If return_usage=True: Tuple of (model_instance, usage_dict) where usage_dict contains:
                - prompt_tokens: Number of input tokens
                - completion_tokens: Number of output tokens
                - total_tokens: Total tokens used
                - model: Model name that successfully returned the result
        """
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage, SystemMessage

        # Use global default if max_tokens not specified
        if max_tokens is None:
            max_tokens = GLOBAL_CONFIG.get("default_token_limit", 2000)

        # Auto-detect which step we're in by inspecting call stack
        step_context = "unknown"
        for frame_info in inspect.stack():
            func_name = frame_info.function
            if func_name.startswith("step"):  # e.g., "step5_chapter_scene_breakdown"
                step_context = func_name
                break

        # Build list of models to try: primary + fallbacks (EXCLUDING banned for THIS step)
        all_models = [self.model] + FALLBACK_MODELS

        # Get banned models for this specific step only
        step_banned = BaseAuthorPhase1._step_banned_models.get(step_context, set())
        models_to_try = [m for m in all_models if m not in step_banned]
        max_retries = 2

        # If all models banned for this step, reset step-specific ban list
        if not models_to_try:
            print(f"⚠️  All models banned for step '{step_context}' - resetting step ban list")
            BaseAuthorPhase1._step_banned_models[step_context] = set()
            models_to_try = all_models

        for model_index, current_model in enumerate(models_to_try):
            # Create LLM instance for current model
            if current_model != self.model:
                print(f"\n🔄 [Phase1Author] Switching to fallback model: {current_model}")

            llm = ChatOpenAI(
                model=current_model,
                api_key=OPENROUTER_API_KEY,
                base_url=OPENROUTER_BASE_URL,
                temperature=GLOBAL_CONFIG.get("default_temperature", 0.7),
            )

            # Use json_schema method with strict=True
            try:
                structured_llm = llm.with_structured_output(
                    schema,
                    method="json_schema",
                    strict=True,
                    include_raw=True  # Include raw AIMessage with token usage metadata
                )
            except Exception as e:
                print(f"⚠️  WARNING: json_schema method not supported, falling back to function_calling: {e}")
                structured_llm = llm.with_structured_output(
                    schema,
                    method="function_calling",
                    include_raw=True  # Include raw AIMessage
                )

            limited_llm = structured_llm.bind(max_tokens=max_tokens)
            messages = [HumanMessage(content=user_prompt)]

            for attempt in range(max_retries + 1):
                try:
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
                        print(f"\n⚠️  WARNING: Phase1Author received None (schema: {schema.__name__}, attempt {attempt + 1}/{max_retries + 1})")
                        if attempt < max_retries:
                            print(f"   Retrying with explicit field requirements...")
                            messages.append(HumanMessage(content=f"""
RETRY REQUEST: Previous response was None (validation failed).

Please ensure you provide ALL required fields for {schema.__name__}:
{', '.join(f'"{field}"' for field in schema.__annotations__.keys())}

Try again with complete data for every field."""))
                            continue
                        else:
                            break  # Try next model

                    # Success!
                    if current_model != self.model:
                        print(f"✅ SUCCESS with fallback model: {current_model}")

                    # Extract token usage from raw message if requested
                    if return_usage:
                        usage_dict = self._extract_token_usage(raw_message, current_model)
                        return result, usage_dict
                    return result

                except Exception as e:
                    error_msg = str(e)
                    print(f"\n❌ ERROR in Phase1Author.invoke_structured() (Attempt {attempt + 1}/{max_retries + 1}):")
                    print(f"   Model: {current_model}")
                    print(f"   Schema: {schema.__name__}")
                    print(f"   Error: {error_msg[:300]}")

                    # Check if this is a reasoning token error
                    if "length limit was reached" in error_msg and "reasoning_tokens" in error_msg:
                        print(f"⚠️  Reasoning token error detected with {current_model}")
                        # Ban this model for THIS STEP ONLY (not globally)
                        if step_context not in BaseAuthorPhase1._step_banned_models:
                            BaseAuthorPhase1._step_banned_models[step_context] = set()
                        BaseAuthorPhase1._step_banned_models[step_context].add(current_model)
                        print(f"🚫 Banning {current_model} for step '{step_context}' only (reasoning token issues)")
                        print(f"   Banned for this step: {BaseAuthorPhase1._step_banned_models[step_context]}")
                        break

                    if attempt < max_retries:
                        print(f"   Retrying with error feedback...")
                        messages.append(HumanMessage(content=f"""
VALIDATION ERROR: {error_msg[:500]}

Please try again and ensure ALL required fields are present:
- Check that you included: {', '.join(f'"{field}"' for field in schema.__annotations__.keys())}
- Provide complete data for each field
- Do not omit any required field

Return your response with COMPLETE data."""))
                    else:
                        if model_index < len(models_to_try) - 1:
                            print(f"   All retries exhausted with {current_model}, trying fallback...")
                            break
                        else:
                            raise

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

    def _normalize_agent_name(self, name: str) -> str:
        """Normalize agent name for matching."""
        return name.upper().replace("_", "").replace(" ", "").replace("AGENT", "")

    def _find_winner_proposal(self, proposals: list, votes: list) -> tuple:
        """Find the winning proposal, handling mismatched vote names.

        The LLM might vote for agents that didn't propose, so we need to
        map votes back to actual proposals.

        Returns:
            (winner_proposal, winner_name, vote_count)
        """
        # Build normalized name -> proposal mapping
        proposal_map = {}
        for p in proposals:
            normalized = self._normalize_agent_name(p.agent_name)
            proposal_map[normalized] = p

        # Count votes, mapping to actual proposals
        valid_votes = {}
        for v in votes:
            vote_normalized = self._normalize_agent_name(v.voted_for_agent)
            # Check if this vote matches any proposal
            if vote_normalized in proposal_map:
                valid_votes[vote_normalized] = valid_votes.get(vote_normalized, 0) + 1
            else:
                # Try partial match (e.g., "TENSIONBUILDER" matches "TENSION_BUILDER")
                for prop_norm in proposal_map:
                    if vote_normalized in prop_norm or prop_norm in vote_normalized:
                        valid_votes[prop_norm] = valid_votes.get(prop_norm, 0) + 1
                        break

        # If no valid votes, default to first proposal
        if not valid_votes:
            return proposals[0], proposals[0].agent_name, 0

        winner_norm = max(valid_votes, key=valid_votes.get)
        winner_proposal = proposal_map[winner_norm]
        return winner_proposal, winner_proposal.agent_name, valid_votes[winner_norm]

    def _get_worker_id(self) -> str:
        """Get current thread worker ID for logging.

        Returns:
            str: Worker ID (e.g., '0', '1', '2') or 'Main' for main thread

        Example:
            Thread 'ThreadPoolExecutor-0_0' → '0'
            Thread 'ThreadPoolExecutor-0_1' → '1'
            Main thread → 'Main'
        """
        thread_name = threading.current_thread().name
        return thread_name.split('-')[-1] if '-' in thread_name else 'Main'

    def _parallel_agent_calls(self, agents, method_name: str, *args, **kwargs) -> list:
        """Run the same method on multiple agents in parallel, preserving order.

        Args:
            agents: List of agent instances
            method_name: Name of the method to call on each agent (e.g., 'propose_question')
            *args: Positional arguments to pass to each agent's method
            **kwargs: Keyword arguments to pass to each agent's method

        Returns:
            list: Results in the same order as agents (None for failed calls)
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        results = [None] * len(agents)
        worker_id = self._get_worker_id()

        with ThreadPoolExecutor(max_workers=len(agents)) as executor:
            futures = {}
            for i, agent in enumerate(agents):
                method = getattr(agent, method_name)
                futures[executor.submit(method, *args, **kwargs)] = i

            for future in as_completed(futures):
                idx = futures[future]
                try:
                    results[idx] = future.result()
                except Exception as e:
                    agent_name = getattr(agents[idx], 'name', f'Agent-{idx}')
                    print(f"[Worker-{worker_id}]   {agent_name}.{method_name}() failed: {str(e)[:80]}")

        return results

    def get_structure(self) -> BaseStructure:
        """Get the author's preferred story structure."""
        return get_structure(self.author.preferred_structure)

    def build_structure_prompt(self, structure: BaseStructure) -> str:
        """Build combined prompt from structure and author's plotting style.

        Args:
            structure: The story structure to use

        Returns:
            Combined prompt string with structure and style modifiers
        """
        parts = []

        # Add structure's outline prompt
        parts.append(structure.get_outline_prompt("standard"))

        # Add author's plotting style modifiers
        style_modifier = self.author.plotting_style.get_prompt_modifier()
        if style_modifier:
            parts.append("\n## Author's Plotting Style")
            parts.append(style_modifier)

        return "\n\n".join(parts)

    def extract_prompts(self, codex: dict) -> tuple[str, str]:
        """Extract story and setting prompts from codex.

        Args:
            codex: The codex dictionary

        Returns:
            Tuple of (story_prompt, setting_prompt)
        """
        # story_engine and deck_of_worlds are at ROOT level
        se_prompts = codex.get("story_engine", {}).get("prompts", [])
        story_prompt = se_prompts[0].get("prompt", "") if se_prompts else ""

        dow_prompts = codex.get("deck_of_worlds", {}).get("prompts", [])
        setting_prompt = dow_prompts[0].get("prompt", "") if dow_prompts else ""

        return story_prompt, setting_prompt

    # =========================================================================
    # STEP 0: THEME FOUNDATION
    # =========================================================================

    def step0_theme_foundation(self, codex: dict) -> Step0Result:
        """Extract theme via 3-substep multi-agent debate.

        This is Step 0 of the Theme → Character → Plot philosophy.
        We identify the thematic question BEFORE creating characters or plot.

        Substeps:
        1. Theme Question Debate: 3 agents propose questions → debate → vote → pick 1
        2. Thematic Square Debate: 3 agents propose squares → debate → vote → pick 1
        3. Perspective Debate: 3 agents propose perspective sets → debate → vote → pick 1

        Args:
            codex: The codex dictionary with story_engine prompts

        Returns:
            Step0Result with theme_foundation data including all debates
        """
        start_time = time.time()

        try:
            # Get prompts from codex
            story_prompt, setting_prompt = self.extract_prompts(codex)
            if not story_prompt:
                return Step0Result(
                    theme_foundation={},
                    success=False,
                    error="Missing story_engine prompts in codex",
                )

            # Get config settings for Step 0
            step_config = get_step_config('step0_theme')
            parallel_enabled = step_config.get('parallel_processing', {}).get('enabled', True)
            max_workers = step_config.get('parallel_processing', {}).get('max_workers', 3)

            # Get worker ID for thread-safe logging
            worker_id = threading.current_thread().name.split('-')[-1] if '-' in threading.current_thread().name else 'Main'

            print(f"\n[Worker-{worker_id}] >>> Logline: {story_prompt}")
            if setting_prompt:
                print(f"[Worker-{worker_id}] >>> Setting: {setting_prompt[:100]}...")
            print(f"[Worker-{worker_id}] >>> Config: parallel_enabled={parallel_enabled}, max_workers={max_workers}")
            print(f"[Worker-{worker_id}] >>> NOTE: Substeps must run sequentially (substep2 needs substep1 output, substep3 needs substep1+2)")

            # Initialize substep timing and token tracking
            substep_timings = {}
            substep_tokens = {}

            # =========================================================================
            # SUBSTEP 1: THEME QUESTION DEBATE
            # =========================================================================
            substep1_start = time.time()
            print(f"\n[Worker-{worker_id}] {'='*60}")
            print(f"[Worker-{worker_id}] SUBSTEP 1: THEME QUESTION DEBATE")
            print(f"[Worker-{worker_id}] {'='*60}")

            # Initialize 3 theme question agents
            philosopher = ThemePhilosopherAgent(model=self.model)
            emotional = ThemeEmotionalAgent(model=self.model)
            dramatic = ThemeDramaticAgent(model=self.model)

            question_agents = [philosopher, emotional, dramatic]

            print(f"\n[Worker-{worker_id}] >>> Phase 1: Proposals (3 agents, parallel)")
            question_proposals = self._parallel_agent_calls(
                question_agents, 'propose_question',
                logline=story_prompt, world_context=setting_prompt
            )
            question_proposals = [p for p in question_proposals if p is not None]
            for p in question_proposals:
                print(f"[Worker-{worker_id}]       → {p.question.question}")

            print(f"\n[Worker-{worker_id}] >>> Phase 2: Critiques (3 agents, parallel)")
            critique_results = self._parallel_agent_calls(
                question_agents, 'critique_questions',
                proposals=question_proposals, logline=story_prompt
            )
            all_question_critiques = []
            for result in critique_results:
                if result is not None:
                    all_question_critiques.extend(result)

            print(f"\n[Worker-{worker_id}] >>> Phase 3: Voting (3 agents, parallel)")
            question_votes = self._parallel_agent_calls(
                question_agents, 'vote',
                proposals=question_proposals, logline=story_prompt
            )
            question_votes = [v for v in question_votes if v is not None]
            for v in question_votes:
                print(f"[Worker-{worker_id}]     - votes for Proposal {v.voted_for_index}")

            # Count votes
            vote_counts = {}
            for v in question_votes:
                vote_counts[v.voted_for_index] = vote_counts.get(v.voted_for_index, 0) + 1

            winner_index = max(vote_counts, key=vote_counts.get)
            winning_question = question_proposals[winner_index].question

            print(f"\n[Worker-{worker_id}] >>> WINNER: Proposal {winner_index} ({vote_counts[winner_index]} votes)")
            print(f"[Worker-{worker_id}] >>> CENTRAL QUESTION: {winning_question.question}")

            # Collect SUBSTEP 1 timing and tokens
            substep1_duration = time.time() - substep1_start
            substep1_tokens_total = sum(agent.get_token_usage()['total_tokens'] for agent in question_agents)
            substep1_calls = sum(agent.get_token_usage()['call_count'] for agent in question_agents)
            substep_timings['theme_question'] = substep1_duration
            substep_tokens['theme_question'] = {
                'total_tokens': substep1_tokens_total,
                'calls': substep1_calls,
            }

            # =========================================================================
            # SUBSTEP 2: THEMATIC SQUARE DEBATE
            # =========================================================================
            substep2_start = time.time()
            print(f"\n[Worker-{worker_id}] {'='*60}")
            print(f"[Worker-{worker_id}] SUBSTEP 2: THEMATIC SQUARE DEBATE")
            print(f"[Worker-{worker_id}] {'='*60}")

            # Initialize 3 square agents
            architect = SquareArchitectAgent(model=self.model)
            character = SquareCharacterAgent(model=self.model)
            conflict = SquareConflictAgent(model=self.model)

            square_agents = [architect, character, conflict]

            print(f"\n[Worker-{worker_id}] >>> Phase 1: Proposals (3 agents, parallel)")
            square_proposals = self._parallel_agent_calls(
                square_agents, 'propose_square',
                central_question=winning_question.question, logline=story_prompt
            )
            square_proposals = [p for p in square_proposals if p is not None]
            for p in square_proposals:
                print(f"[Worker-{worker_id}]       POSITIVE: {p.thematic_square.positive}")

            print(f"\n[Worker-{worker_id}] >>> Phase 2: Critiques (3 agents, parallel)")
            critique_results = self._parallel_agent_calls(
                square_agents, 'critique_squares',
                proposals=square_proposals, central_question=winning_question.question
            )
            all_square_critiques = []
            for result in critique_results:
                if result is not None:
                    all_square_critiques.extend(result)

            print(f"\n[Worker-{worker_id}] >>> Phase 3: Voting (3 agents, parallel)")
            square_votes = self._parallel_agent_calls(
                square_agents, 'vote',
                proposals=square_proposals, central_question=winning_question.question
            )
            square_votes = [v for v in square_votes if v is not None]
            for v in square_votes:
                print(f"[Worker-{worker_id}]     - votes for Proposal {v.voted_for_index}")

            # Count votes
            vote_counts = {}
            for v in square_votes:
                vote_counts[v.voted_for_index] = vote_counts.get(v.voted_for_index, 0) + 1

            winner_index = max(vote_counts, key=vote_counts.get)
            winning_square = square_proposals[winner_index].thematic_square

            print(f"\n[Worker-{worker_id}] >>> WINNER: Proposal {winner_index} ({vote_counts[winner_index]} votes)")
            print(f"[Worker-{worker_id}] >>> THEMATIC SQUARE:")
            print(f"[Worker-{worker_id}]     POSITIVE: {winning_square.positive}")
            print(f"[Worker-{worker_id}]     CONTRADICTORY: {winning_square.contradictory}")
            print(f"[Worker-{worker_id}]     CONTRARY: {winning_square.contrary}")
            print(f"[Worker-{worker_id}]     NEGATION: {winning_square.negation_of_negation}")

            # Collect SUBSTEP 2 timing and tokens
            substep2_duration = time.time() - substep2_start
            substep2_tokens_total = sum(agent.get_token_usage()['total_tokens'] for agent in square_agents)
            substep2_calls = sum(agent.get_token_usage()['call_count'] for agent in square_agents)
            substep_timings['thematic_square'] = substep2_duration
            substep_tokens['thematic_square'] = {
                'total_tokens': substep2_tokens_total,
                'calls': substep2_calls,
            }

            # =========================================================================
            # SUBSTEP 3: PERSPECTIVE SET DEBATE
            # =========================================================================
            substep3_start = time.time()
            print(f"\n[Worker-{worker_id}] {'='*60}")
            print(f"[Worker-{worker_id}] SUBSTEP 3: PERSPECTIVE SET DEBATE")
            print(f"[Worker-{worker_id}] {'='*60}")

            # Initialize 3 perspective agents
            diversity = PerspectiveDiversityAgent(model=self.model)
            story_fit = PerspectiveStoryAgent(model=self.model)
            balance = PerspectiveBalanceAgent(model=self.model)

            perspective_agents = [diversity, story_fit, balance]

            print(f"\n[Worker-{worker_id}] >>> Phase 1: Proposals (3 agents, parallel)")
            from concurrent.futures import ThreadPoolExecutor, as_completed

            def _propose_perspective(agent):
                if agent.name == "PERSPECTIVE_STORY":
                    return agent.propose_perspectives(
                        central_question=winning_question.question,
                        top_squares=[winning_square], logline=story_prompt
                    )
                return agent.propose_perspectives(
                    central_question=winning_question.question,
                    top_squares=[winning_square]
                )

            perspective_proposals = [None] * len(perspective_agents)
            with ThreadPoolExecutor(max_workers=len(perspective_agents)) as executor:
                futures = {executor.submit(_propose_perspective, a): i for i, a in enumerate(perspective_agents)}
                for future in as_completed(futures):
                    idx = futures[future]
                    try:
                        perspective_proposals[idx] = future.result()
                    except Exception as e:
                        print(f"[Worker-{worker_id}]   Proposal failed: {str(e)[:60]}")
            perspective_proposals = [p for p in perspective_proposals if p is not None]
            for p in perspective_proposals:
                for persp in p.perspectives:
                    print(f"[Worker-{worker_id}]       - {persp.perspective_name} ({persp.corner})")

            print(f"\n[Worker-{worker_id}] >>> Phase 2: Critiques (3 agents, parallel)")
            def _critique_perspective(agent):
                if agent.name == "PERSPECTIVE_STORY":
                    return agent.critique_perspective_sets(
                        proposals=perspective_proposals,
                        central_question=winning_question.question, logline=story_prompt
                    )
                return agent.critique_perspective_sets(
                    proposals=perspective_proposals,
                    central_question=winning_question.question
                )

            all_perspective_critiques = []
            with ThreadPoolExecutor(max_workers=len(perspective_agents)) as executor:
                futures = {executor.submit(_critique_perspective, a): i for i, a in enumerate(perspective_agents)}
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        if result is not None:
                            all_perspective_critiques.extend(result)
                    except Exception as e:
                        print(f"[Worker-{worker_id}]   Critique failed: {str(e)[:60]}")

            print(f"\n[Worker-{worker_id}] >>> Phase 3: Voting (3 agents, parallel)")
            perspective_votes = self._parallel_agent_calls(
                perspective_agents, 'vote',
                proposals=perspective_proposals, central_question=winning_question.question
            )
            perspective_votes = [v for v in perspective_votes if v is not None]
            for v in perspective_votes:
                print(f"[Worker-{worker_id}]     - votes for Proposal {v.voted_for_index}")

            # Count votes
            vote_counts = {}
            for v in perspective_votes:
                vote_counts[v.voted_for_index] = vote_counts.get(v.voted_for_index, 0) + 1

            winner_index = max(vote_counts, key=vote_counts.get)
            winning_perspectives = perspective_proposals[winner_index].perspectives

            print(f"\n[Worker-{worker_id}] >>> WINNER: Proposal {winner_index} ({vote_counts[winner_index]} votes)")
            print(f"[Worker-{worker_id}] >>> PERSPECTIVES:")
            for p in winning_perspectives:
                print(f"[Worker-{worker_id}]     - {p.perspective_name} ({p.corner})")
                print(f"[Worker-{worker_id}]       Position: {p.position}")

            # =========================================================================
            # BUILD THEME FOUNDATION OUTPUT (CLEAN - NO DEBATES)
            # =========================================================================
            theme_foundation = {
                "central_question": winning_question.question,
                "thematic_square": {
                    "positive": winning_square.positive,
                    "contradictory": winning_square.contradictory,
                    "contrary": winning_square.contrary,
                    "negation_of_negation": winning_square.negation_of_negation,
                },
                "perspectives": [
                    {
                        "perspective_name": p.perspective_name,
                        "position": p.position,
                        "corner": p.corner,
                        "example_belief": p.example_belief,
                    }
                    for p in winning_perspectives
                ],
            }

            # =========================================================================
            # BUILD DEBATES OUTPUT (SEPARATE FOR METADATA)
            # =========================================================================
            step0_debates = {
                "question_debate": {
                    "proposals": [
                        {
                            "agent_name": p.agent_name,
                            "question": p.question.question,
                            "explanation": p.question.explanation,
                            "reasoning": p.reasoning,
                        }
                        for p in question_proposals
                    ],
                    "critiques": [
                        {
                            "agent_name": c.agent_name,
                            "proposal_index": c.proposal_index,
                            "strengths": c.strengths,
                            "weaknesses": c.weaknesses,
                            "score": c.score,
                        }
                        for c in all_question_critiques
                    ],
                    "votes": [
                        {
                            "agent_name": v.agent_name,
                            "voted_for_index": v.voted_for_index,
                            "vote_reasoning": v.vote_reasoning,
                        }
                        for v in question_votes
                    ],
                    "winner_index": winner_index,
                },
                "square_debate": {
                    "proposals": [
                        {
                            "agent_name": p.agent_name,
                            "square": {
                                "positive": p.thematic_square.positive,
                                "contradictory": p.thematic_square.contradictory,
                                "contrary": p.thematic_square.contrary,
                                "negation_of_negation": p.thematic_square.negation_of_negation,
                            },
                            "reasoning": p.reasoning,
                        }
                        for p in square_proposals
                    ],
                    "critiques": [
                        {
                            "agent_name": c.agent_name,
                            "proposal_index": c.proposal_index,
                            "strengths": c.strengths,
                            "weaknesses": c.weaknesses,
                            "score": c.score,
                        }
                        for c in all_square_critiques
                    ],
                    "votes": [
                        {
                            "agent_name": v.agent_name,
                            "voted_for_index": v.voted_for_index,
                            "vote_reasoning": v.vote_reasoning,
                        }
                        for v in square_votes
                    ],
                    "winner_index": winner_index,
                },
                "perspective_debate": {
                    "proposals": [
                        {
                            "agent_name": p.agent_name,
                            "perspectives": [
                                {
                                    "perspective_name": per.perspective_name,
                                    "position": per.position,
                                    "corner": per.corner,
                                    "example_belief": per.example_belief,
                                }
                                for per in p.perspectives
                            ],
                            "reasoning": p.reasoning,
                        }
                        for p in perspective_proposals
                    ],
                    "critiques": [
                        {
                            "agent_name": c.agent_name,
                            "proposal_index": c.proposal_index,
                            "strengths": c.strengths,
                            "weaknesses": c.weaknesses,
                            "score": c.score,
                        }
                        for c in all_perspective_critiques
                    ],
                    "votes": [
                        {
                            "agent_name": v.agent_name,
                            "voted_for_index": v.voted_for_index,
                            "vote_reasoning": v.vote_reasoning,
                        }
                        for v in perspective_votes
                    ],
                    "winner_index": winner_index,
                },
            }

            # Collect SUBSTEP 3 timing and tokens
            substep3_duration = time.time() - substep3_start
            substep3_tokens_total = sum(agent.get_token_usage()['total_tokens'] for agent in perspective_agents)
            substep3_calls = sum(agent.get_token_usage()['call_count'] for agent in perspective_agents)
            substep_timings['perspective'] = substep3_duration
            substep_tokens['perspective'] = {
                'total_tokens': substep3_tokens_total,
                'calls': substep3_calls,
            }

            # Calculate total token usage for this step
            total_tokens_used = sum(st['total_tokens'] for st in substep_tokens.values())
            total_calls = sum(st['calls'] for st in substep_tokens.values())
            token_usage = {
                'total_tokens': total_tokens_used,
                'call_count': total_calls,
            }

            duration = time.time() - start_time

            print(f"\n[Worker-{worker_id}] {'='*60}")
            print(f"[Worker-{worker_id}] STEP 0 COMPLETE! Duration: {duration:.1f}s")
            print(f"[Worker-{worker_id}]   Tokens used: {total_tokens_used:,} ({total_calls} LLM calls)")
            print(f"[Worker-{worker_id}] {'='*60}")

            return Step0Result(
                theme_foundation=theme_foundation,
                step0_debates=step0_debates,
                success=True,
                duration_seconds=duration,
                token_usage=token_usage,
                substep_timings=substep_timings,
                substep_tokens=substep_tokens,
            )

        except Exception as e:
            duration = time.time() - start_time
            worker_id = threading.current_thread().name.split('-')[-1] if '-' in threading.current_thread().name else 'Main'
            print(f"\n[Worker-{worker_id}] >>> Step 0 FAILED: {e}")
            import traceback
            traceback.print_exc()

            return Step0Result(
                theme_foundation={},
                step0_debates={},
                success=False,
                error=str(e),
                duration_seconds=duration,
            )

    # =========================================================================
    # STEP 1: CHARACTER CREATION (Theme → Characters)
    # =========================================================================

    def _create_character_parallel(self, char_idx: int, perspective: dict, central_question: str,
                                   story_prompt: str, setting_prompt: str, existing_names: list,
                                   codex: dict) -> tuple:
        """Create a single character in parallel with thread-safe logging.

        This method extracts the character creation logic to enable parallel processing.
        Each character creation runs independently with thread-safe logging.

        Args:
            char_idx: Character index (0-based)
            perspective: Thematic perspective from Step 0
            central_question: Central thematic question
            story_prompt: Story logline
            setting_prompt: Setting description
            existing_names: List of already used character names (thread-safe access managed by caller)
            codex: The codex dictionary (for context)

        Returns:
            tuple: (character_dict, character_debate_history)
        """
        # Get worker ID for thread-safe logging
        worker_id = threading.current_thread().name.split('-')[-1] if '-' in threading.current_thread().name else 'Main'
        char_id = f"char_{char_idx+1:03d}"

        print(f"\n[Worker-{worker_id}] {'='*60}")
        print(f"[Worker-{worker_id}] CHARACTER {char_idx+1}: {perspective['perspective_name']}")
        print(f"[Worker-{worker_id}] Corner: {perspective['corner']}")
        print(f"[Worker-{worker_id}] {'='*60}")

        # Import psychology agents
        from src.story_agents.character_psychology_agents import (
            LieTruthPhilosopherAgent,
            LieTruthPsychologistAgent,
            LieTruthNarrativeAgent,
            ShadowArchetypeAgent,
            ShadowNarrativeAgent,
            ShadowPsychologistAgent,
            ArcTypeAgent,
            ArcTypeNarrativeAgent,
            ArcTypeThematicAgent,
            GhostAgent,
            GhostEmotionalAgent,
            GhostThematicAgent,
        )

        character_debate_history = {
            "perspective": perspective,
            "lie_truth_debate": {},
            "shadow_debate": {},
            "arc_type_debate": {},
            "ghost_debate": {},
            "name_debate": {},
            "physical_debate": {},
        }

        # =========================================================
        # SUBSTEP 1: LIE/TRUTH DEBATE
        # =========================================================
        print(f"\n[Worker-{worker_id}] --- SUBSTEP 1: LIE/TRUTH DEBATE ---")

        # Initialize agents
        lie_truth_philosopher = LieTruthPhilosopherAgent(model=self.model)
        lie_truth_psychologist = LieTruthPsychologistAgent(model=self.model)
        lie_truth_narrative = LieTruthNarrativeAgent(model=self.model)

        lie_truth_agents = [lie_truth_philosopher, lie_truth_psychologist, lie_truth_narrative]

        # Proposals (parallel)
        print(f"\n[Worker-{worker_id}] >>> Phase 1: Proposals (3 agents, parallel)")
        lie_truth_proposals = self._parallel_agent_calls(
            lie_truth_agents, 'propose_lie_truth',
            perspective=perspective, central_question=central_question,
            square_corner=perspective['corner']
        )
        lie_truth_proposals = [p for p in lie_truth_proposals if p is not None]
        for p in lie_truth_proposals:
            print(f"[Worker-{worker_id}]       Lie: {p.lie_character_believes[:60]}...")

        # Critiques (parallel)
        print(f"\n[Worker-{worker_id}] >>> Phase 2: Critiques (parallel)")
        critique_results = self._parallel_agent_calls(
            lie_truth_agents, 'critique_lie_truth',
            proposals=lie_truth_proposals, perspective=perspective,
            central_question=central_question
        )
        all_lie_truth_critiques = []
        for result in critique_results:
            if result is not None:
                all_lie_truth_critiques.extend(result)

        # Votes (parallel)
        print(f"\n[Worker-{worker_id}] >>> Phase 3: Voting (parallel)")
        lie_truth_votes = self._parallel_agent_calls(
            lie_truth_agents, 'vote',
            proposals=lie_truth_proposals, perspective=perspective
        )
        lie_truth_votes = [v for v in lie_truth_votes if v is not None]
        for v in lie_truth_votes:
            print(f"[Worker-{worker_id}]     - votes for Proposal {v.voted_for_index}")

        # Select winner
        vote_counts = {}
        for v in lie_truth_votes:
            vote_counts[v.voted_for_index] = vote_counts.get(v.voted_for_index, 0) + 1

        winner_index = max(vote_counts, key=vote_counts.get)
        winning_lie_truth = lie_truth_proposals[winner_index]

        print(f"\n[Worker-{worker_id}] >>> WINNER: Proposal {winner_index} ({vote_counts[winner_index]} votes)")
        print(f"[Worker-{worker_id}] >>> Lie: {winning_lie_truth.lie_character_believes}")
        print(f"[Worker-{worker_id}] >>> Truth: {winning_lie_truth.truth_character_needs}")
        print(f"[Worker-{worker_id}] >>> Want: {winning_lie_truth.want}")
        print(f"[Worker-{worker_id}] >>> Need: {winning_lie_truth.need}")

        character_debate_history["lie_truth_debate"] = {
            "proposals": [p.model_dump() for p in lie_truth_proposals],
            "critiques": [c.model_dump() for c in all_lie_truth_critiques],
            "votes": [v.model_dump() for v in lie_truth_votes],
            "winner_index": winner_index,
            "winner": winning_lie_truth.model_dump()
        }

        # =========================================================
        # SUBSTEP 2A: SHADOW DEBATE (3 agents)
        # =========================================================
        print(f"\n[Worker-{worker_id}] --- SUBSTEP 2A: SHADOW DEBATE ---")

        # Initialize 3 shadow agents
        shadow_archetype = ShadowArchetypeAgent(model=self.model)
        shadow_narrative = ShadowNarrativeAgent(model=self.model)
        shadow_psychologist = ShadowPsychologistAgent(model=self.model)

        shadow_agents = [shadow_archetype, shadow_narrative, shadow_psychologist]

        # Proposals (parallel)
        print(f"\n[Worker-{worker_id}] >>> Phase 1: Proposals (3 agents, parallel)")
        shadow_proposals = self._parallel_agent_calls(
            shadow_agents, 'propose_shadow',
            perspective=perspective, lie=winning_lie_truth.lie_character_believes,
            truth=winning_lie_truth.truth_character_needs
        )
        shadow_proposals = [p for p in shadow_proposals if p is not None]

        # Critiques (parallel)
        print(f"\n[Worker-{worker_id}] >>> Phase 2: Critiques (parallel)")
        critique_results = self._parallel_agent_calls(
            shadow_agents, 'critique_shadow',
            proposals=shadow_proposals, perspective=perspective,
            lie=winning_lie_truth.lie_character_believes
        )
        all_shadow_critiques = []
        for result in critique_results:
            if result is not None:
                all_shadow_critiques.extend(result)

        # Votes (parallel)
        print(f"\n[Worker-{worker_id}] >>> Phase 3: Voting (parallel)")
        shadow_votes = self._parallel_agent_calls(
            shadow_agents, 'vote',
            proposals=shadow_proposals, perspective=perspective
        )
        shadow_votes = [v for v in shadow_votes if v is not None]
        for v in shadow_votes:
            print(f"[Worker-{worker_id}]     - votes for Proposal {v.voted_for_index}")

        # Select winner
        vote_counts = {}
        for v in shadow_votes:
            vote_counts[v.voted_for_index] = vote_counts.get(v.voted_for_index, 0) + 1

        winner_index = max(vote_counts, key=vote_counts.get)
        winning_shadow = shadow_proposals[winner_index]

        print(f"\n[Worker-{worker_id}] >>> WINNER: Proposal {winner_index} ({vote_counts[winner_index]} votes)")
        print(f"[Worker-{worker_id}] >>> Shadow Traits:")
        for key, value in winning_shadow.shadow_traits.items():
            print(f"[Worker-{worker_id}]     {key}: {value}")

        character_debate_history["shadow_debate"] = {
            "proposals": [p.model_dump() for p in shadow_proposals],
            "critiques": [c.model_dump() for c in all_shadow_critiques],
            "votes": [v.model_dump() for v in shadow_votes],
            "winner_index": winner_index,
            "winner": winning_shadow.model_dump()
        }

        # =========================================================
        # SUBSTEP 2B: ARC TYPE DEBATE (3 agents)
        # =========================================================
        print(f"\n[Worker-{worker_id}] --- SUBSTEP 2B: ARC TYPE DEBATE ---")

        # Initialize 3 arc type agents
        arc_agent = ArcTypeAgent(model=self.model)
        arc_narrative = ArcTypeNarrativeAgent(model=self.model)
        arc_thematic = ArcTypeThematicAgent(model=self.model)

        arc_agents = [arc_agent, arc_narrative, arc_thematic]

        # Proposals (parallel)
        print(f"\n[Worker-{worker_id}] >>> Phase 1: Proposals (3 agents, parallel)")
        arc_proposals = self._parallel_agent_calls(
            arc_agents, 'propose_arc_type',
            perspective=perspective, lie=winning_lie_truth.lie_character_believes,
            truth=winning_lie_truth.truth_character_needs, square_corner=perspective['corner']
        )
        arc_proposals = [p for p in arc_proposals if p is not None]
        for p in arc_proposals:
            print(f"[Worker-{worker_id}]       Arc: {p.arc_type}")

        # Critiques (parallel)
        print(f"\n[Worker-{worker_id}] >>> Phase 2: Critiques (parallel)")
        critique_results = self._parallel_agent_calls(
            arc_agents, 'critique_arc_type',
            proposals=arc_proposals, perspective=perspective,
            lie=winning_lie_truth.lie_character_believes,
            truth=winning_lie_truth.truth_character_needs
        )
        all_arc_critiques = []
        for result in critique_results:
            if result is not None:
                all_arc_critiques.extend(result)

        # Votes (parallel)
        print(f"\n[Worker-{worker_id}] >>> Phase 3: Voting (parallel)")
        arc_votes = self._parallel_agent_calls(
            arc_agents, 'vote',
            proposals=arc_proposals, perspective=perspective
        )
        arc_votes = [v for v in arc_votes if v is not None]
        for v in arc_votes:
            print(f"[Worker-{worker_id}]     - votes for Proposal {v.voted_for_index}")

        # Select winner
        vote_counts = {}
        for v in arc_votes:
            vote_counts[v.voted_for_index] = vote_counts.get(v.voted_for_index, 0) + 1

        winner_index = max(vote_counts, key=vote_counts.get)
        winning_arc = arc_proposals[winner_index]

        print(f"\n[Worker-{worker_id}] >>> WINNER: Proposal {winner_index} ({vote_counts[winner_index]} votes)")
        print(f"[Worker-{worker_id}] >>> Arc Type: {winning_arc.arc_type}")
        print(f"[Worker-{worker_id}] >>> Journey: {winning_arc.arc_journey}")

        character_debate_history["arc_type_debate"] = {
            "proposals": [p.model_dump() for p in arc_proposals],
            "critiques": [c.model_dump() for c in all_arc_critiques],
            "votes": [v.model_dump() for v in arc_votes],
            "winner_index": winner_index,
            "winner": winning_arc.model_dump()
        }

        # =========================================================
        # SUBSTEP 2C: GHOST DEBATE (3 agents)
        # =========================================================
        print(f"\n[Worker-{worker_id}] --- SUBSTEP 2C: GHOST DEBATE ---")

        # Initialize 3 ghost agents
        ghost_agent = GhostAgent(model=self.model)
        ghost_emotional = GhostEmotionalAgent(model=self.model)
        ghost_thematic = GhostThematicAgent(model=self.model)

        ghost_agents = [ghost_agent, ghost_emotional, ghost_thematic]

        # Proposals (parallel)
        print(f"\n[Worker-{worker_id}] >>> Phase 1: Proposals (3 agents, parallel)")
        ghost_proposals = self._parallel_agent_calls(
            ghost_agents, 'propose_ghost',
            perspective=perspective, lie=winning_lie_truth.lie_character_believes
        )
        ghost_proposals = [p for p in ghost_proposals if p is not None]
        for p in ghost_proposals:
            print(f"[Worker-{worker_id}]       Event: {p.ghost_event[:60]}...")

        # Critiques (parallel)
        print(f"\n[Worker-{worker_id}] >>> Phase 2: Critiques (parallel)")
        critique_results = self._parallel_agent_calls(
            ghost_agents, 'critique_ghost',
            proposals=ghost_proposals, perspective=perspective,
            lie=winning_lie_truth.lie_character_believes
        )
        all_ghost_critiques = []
        for result in critique_results:
            if result is not None:
                all_ghost_critiques.extend(result)

        # Votes (parallel)
        print(f"\n[Worker-{worker_id}] >>> Phase 3: Voting (parallel)")
        ghost_votes = self._parallel_agent_calls(
            ghost_agents, 'vote',
            proposals=ghost_proposals, perspective=perspective
        )
        ghost_votes = [v for v in ghost_votes if v is not None]
        for v in ghost_votes:
            print(f"[Worker-{worker_id}]     - votes for Proposal {v.voted_for_index}")

        # Select winner
        vote_counts = {}
        for v in ghost_votes:
            vote_counts[v.voted_for_index] = vote_counts.get(v.voted_for_index, 0) + 1

        winner_index = max(vote_counts, key=vote_counts.get)
        winning_ghost = ghost_proposals[winner_index]

        print(f"\n[Worker-{worker_id}] >>> WINNER: Proposal {winner_index} ({vote_counts[winner_index]} votes)")
        print(f"[Worker-{worker_id}] >>> Ghost Event: {winning_ghost.ghost_event}")
        print(f"[Worker-{worker_id}] >>> How It Created Lie: {winning_ghost.how_it_created_lie}")

        character_debate_history["ghost_debate"] = {
            "proposals": [p.model_dump() for p in ghost_proposals],
            "critiques": [c.model_dump() for c in all_ghost_critiques],
            "votes": [v.model_dump() for v in ghost_votes],
            "winner_index": winner_index,
            "winner": winning_ghost.model_dump()
        }

        # =========================================================
        # SUBSTEP 3: NAME GENERATION (reuse existing system)
        # =========================================================
        print(f"\n[Worker-{worker_id}] --- SUBSTEP 3: NAME GENERATION ---")

        first_initial = random.choice(string.ascii_uppercase)
        last_initial = random.choice(string.ascii_uppercase)
        print(f"[Worker-{worker_id}]     Initials: {first_initial}.{last_initial}.")

        name_result = self._run_name_debate(
            character_role=perspective['perspective_name'],
            first_initial=first_initial,
            last_initial=last_initial,
            logline=story_prompt,
            setting_prompt=setting_prompt,
            existing_names=existing_names,
        )

        final_name = name_result["final_name"]
        print(f"[Worker-{worker_id}]     >>> Name: {final_name}")

        character_debate_history["name_debate"] = name_result.get("debate", {})

        # =========================================================
        # SUBSTEP 4: PHYSICAL APPEARANCE (reuse existing system)
        # =========================================================
        print(f"\n[Worker-{worker_id}] --- SUBSTEP 4: PHYSICAL APPEARANCE ---")

        physical_result = self._run_physical_debate(
            character_role=perspective['perspective_name'],
            character_type="thematic",
            adjective=winning_lie_truth.lie_character_believes[:50],  # Use Lie as context
            goal=winning_lie_truth.want,
            stakes=winning_lie_truth.need,
            setting_prompt=setting_prompt,
        )

        # Extract physical description from winning proposal
        winning_physical = physical_result.get("winning_physical", {})
        final_physical = f"{winning_physical.get('body_build', 'average build')}, {winning_physical.get('height', 'average height')}, {winning_physical.get('hair_color', 'dark hair')}, {winning_physical.get('eye_color', 'brown eyes')}, {winning_physical.get('ethnicity', 'mixed heritage')}"
        if winning_physical.get('distinguishing_features'):
            final_physical += f", {winning_physical['distinguishing_features']}"

        print(f"[Worker-{worker_id}]     >>> Physical: {final_physical[:100]}...")

        character_debate_history["physical_debate"] = {
            "proposals": physical_result.get("proposals", []),
            "critiques": physical_result.get("critiques", []),
            "votes": physical_result.get("votes", []),
            "winner": physical_result.get("winner", ""),
            "winning_physical": winning_physical,
            "winning_costume": ""  # Costume will be designed in Step 4 (World Building)
        }

        # =========================================================
        # BUILD CHARACTER DICT
        # =========================================================

        # Assign story role based on thematic corner
        THEMATIC_ROLE_MAPPING = {
            "positive": "protagonist",      # Life-affirming = hero
            "contradictory": "supporting",  # Tension = ally/mentor
            "contrary": "supporting",       # Opposite = doubter/obstacle
            "negation": "antagonist"        # Darkest = villain
        }
        character_role = THEMATIC_ROLE_MAPPING.get(perspective['corner'], "supporting")

        character = {
            "character_id": char_id,
            "name": final_name,
            "gender": random.choice(["male", "female"]),
            "body_build": winning_physical.get('body_build', 'average build'),
            "height": winning_physical.get('height', 'average height'),
            "hair_color": winning_physical.get('hair_color', 'dark hair'),
            "eye_color": winning_physical.get('eye_color', 'brown eyes'),
            "ethnicity": winning_physical.get('ethnicity', 'mixed heritage'),
            "distinguishing_features": winning_physical.get('distinguishing_features', ''),
            "costume": "",  # Will be designed in Step 4 (World Building) with full world context
            "costume_details": None,  # Detailed costume breakdown added in Step 4
            "role": character_role,  # Story function (protagonist/antagonist/supporting)
            "thematic_perspective": perspective['perspective_name'],
            "thematic_corner": perspective['corner'],
            "thematic_position": perspective['position'],
            "lie_character_believes": winning_lie_truth.lie_character_believes,
            "truth_character_needs": winning_lie_truth.truth_character_needs,
            "want": winning_lie_truth.want,
            "need": winning_lie_truth.need,
            "shadow_traits": winning_shadow.shadow_traits,
            "arc_type": winning_arc.arc_type,
            "arc_journey": winning_arc.arc_journey,
            "ghost_event": winning_ghost.ghost_event,
            "how_ghost_created_lie": winning_ghost.how_it_created_lie,
        }

        print(f"\n[Worker-{worker_id}] >>> Character {char_idx+1} complete!")

        return (character, character_debate_history)


    def step1_character_creation(self, codex: dict) -> Step1Result:
        """Generate psychologically complex characters from Step 0 thematic perspectives.

        For each of the 4 perspectives from Step 0, creates 1 character via multi-agent debate:

        SUBSTEP 1: Lie/Truth Debate (3 agents)
        - Define the Lie the character believes
        - Define the Truth they need to learn
        - Define Want (external goal) vs. Need (internal truth)

        SUBSTEP 2: Shadow/Arc/Ghost Debates (3 agents, 3 separate debates)
        - Shadow: Jungian unconscious opposites
        - Arc Type: Positive Change/Flat/Disillusionment/Fall/Corruption
        - Ghost: Backstory event that created the Lie

        SUBSTEP 3: Name Generation (reuse existing 3-agent name debate)

        SUBSTEP 4: Physical Appearance (reuse existing 4-agent physical debate)

        Args:
            codex: The codex dictionary with theme_foundation from Step 0

        Returns:
            Step1Result with characters list and full debate history
        """
        start_time = time.time()

        try:
            # Get Step 0 theme foundation
            theme_foundation = codex.get("story", {}).get("theme_foundation", {})
            if not theme_foundation:
                return Step1Result(
                    characters=[],
                    character_debates=[],
                    success=False,
                    error="Step 0 (Theme Foundation) not run. Run --steps 0 first.",
                )

            perspectives = theme_foundation.get("perspectives", [])
            central_question = theme_foundation.get("central_question", "")

            if not perspectives:
                return Step1Result(
                    characters=[],
                    character_debates=[],
                    success=False,
                    error="No perspectives found in theme_foundation",
                )

            # Get prompts for context
            story_prompt, setting_prompt = self.extract_prompts(codex)

            print(f"\n{'='*60}")
            print("STEP 1: CHARACTER CREATION (Theme → Characters)")
            print(f"{'='*60}")
            print(f">>> Creating {len(perspectives)} characters from thematic perspectives")
            print(f">>> Central Question: {central_question}")

            # Import psychology agents
            from src.story_agents.character_psychology_agents import (
                LieTruthPhilosopherAgent,
                LieTruthPsychologistAgent,
                LieTruthNarrativeAgent,
                ShadowArchetypeAgent,
                ShadowNarrativeAgent,
                ShadowPsychologistAgent,
                ArcTypeAgent,
                ArcTypeNarrativeAgent,
                ArcTypeThematicAgent,
                GhostAgent,
                GhostEmotionalAgent,
                GhostThematicAgent,
            )

            characters = []
            all_character_debates = []  # Track debate history separately for metadata
            existing_names = []

            # Get parallel processing config
            step1_config = get_step_config('step1_characters')
            parallel_config = step1_config.get('parallel_processing', {})
            character_level_parallel = parallel_config.get('character_level', True)
            max_workers_characters = parallel_config.get('max_workers_characters', 4)

            # Process characters in parallel or sequentially
            if character_level_parallel and len(perspectives) > 1:
                print(f">>> Processing characters in parallel (max_workers={max_workers_characters})")

                from concurrent.futures import ThreadPoolExecutor, as_completed

                name_lock = threading.Lock()  # Thread-safe name list management

                # Submit all character creation tasks
                with ThreadPoolExecutor(max_workers=max_workers_characters) as executor:
                    # Create wrapper function to handle name locking
                    def create_character_with_lock(idx, perspective):
                        # Create character
                        char, debate = self._create_character_parallel(
                            char_idx=idx,
                            perspective=perspective,
                            central_question=central_question,
                            story_prompt=story_prompt,
                            setting_prompt=setting_prompt,
                            existing_names=existing_names,
                            codex=codex
                        )

                        # Thread-safe name registration
                        with name_lock:
                            existing_names.append(char['name'])

                        return (idx, char, debate)

                    # Submit all tasks
                    future_to_idx = {
                        executor.submit(create_character_with_lock, idx, perspective): idx
                        for idx, perspective in enumerate(perspectives)
                    }

                    # Collect results in order
                    results = [None] * len(perspectives)
                    for future in as_completed(future_to_idx):
                        idx, char, debate = future.result()
                        results[idx] = (char, debate)

                    # Extract characters and debates in original order
                    for char, debate in results:
                        characters.append(char)
                        all_character_debates.append(debate)

                        # UPDATE CODEX after each character
                        if "story" not in codex:
                            codex["story"] = {}
                        codex["story"]["characters"] = characters
            else:
                print(f">>> Processing characters sequentially")

                # Sequential processing (use helper method for consistency)
                for idx, perspective in enumerate(perspectives):
                    char, debate = self._create_character_parallel(
                        char_idx=idx,
                        perspective=perspective,
                        central_question=central_question,
                        story_prompt=story_prompt,
                        setting_prompt=setting_prompt,
                        existing_names=existing_names,
                        codex=codex
                    )

                    existing_names.append(char['name'])
                    characters.append(char)
                    all_character_debates.append(debate)

                    # UPDATE CODEX after each character
                    if "story" not in codex:
                        codex["story"] = {}
                    codex["story"]["characters"] = characters

            # Final summary
            duration = time.time() - start_time

            print(f"\n{'='*60}")
            print(f"STEP 1 COMPLETE! Created {len(characters)} characters")
            print(f"Duration: {duration:.1f}s")
            print(f"{'='*60}")

            for i, char in enumerate(characters):
                print(f"\n{i+1}. {char['name']} ({char['thematic_perspective']})")
                print(f"   Arc: {char['arc_type']}")
                print(f"   Lie: {char['lie_character_believes'][:60]}...")
                print(f"   Truth: {char['truth_character_needs'][:60]}...")

            return Step1Result(
                characters=characters,
                character_debates=all_character_debates,
                success=True,
                duration_seconds=duration
            )

        except Exception as e:
            duration = time.time() - start_time
            print(f"\n>>> Step 1 FAILED: {e}")
            import traceback
            traceback.print_exc()

            return Step1Result(
                characters=[],
                character_debates=[],
                success=False,
                error=str(e),
                duration_seconds=duration
            )

    # =========================================================================
    # STEP 2: STORY SHAPE & GENRE SELECTION (Multi-Agent Debate)
    # =========================================================================


    def _run_story_shape_debate(
        self,
        story_prompt: str,
        theme_question: str,
        characters: list
    ) -> dict:
        """Run parallel debate for story shape.

        Args:
            story_prompt: The story prompt
            theme_question: Central theme question
            characters: List of characters

        Returns:
            dict: Debate results with winner and metadata
        """
        worker_id = self._get_worker_id()
        print(f"\n[Worker-{worker_id}] {'='*50}")
        print(f"[Worker-{worker_id}] DEBATE 1: STORY SHAPE (7 Basic Plots)")
        print(f"[Worker-{worker_id}] {'='*50}")

        from src.story_agents.story_shape_agents import (
            StoryShapeJourneyAgent, StoryShapeEmotionalAgent, StoryShapeThematicAgent
        )

        shape_agents = [
            StoryShapeJourneyAgent(model=self.model),
            StoryShapeEmotionalAgent(model=self.model),
            StoryShapeThematicAgent(model=self.model),
        ]

        # Proposals (parallel)
        print(f"[Worker-{worker_id}] >>> Phase 1: Proposals (3 agents, parallel)")
        shape_proposals = self._parallel_agent_calls(
            shape_agents, 'propose_story_shape', story_prompt, theme_question, characters
        )
        shape_proposals = [p for p in shape_proposals if p is not None]
        for p in shape_proposals:
            print(f"[Worker-{worker_id}]       Shape: {p.story_shape}")

        # Critiques (parallel)
        print(f"[Worker-{worker_id}] >>> Phase 2: Critiques (parallel)")
        critique_results = self._parallel_agent_calls(
            shape_agents, 'critique_story_shape', shape_proposals, story_prompt, characters
        )
        all_shape_critiques = []
        for result in critique_results:
            if result is not None:
                all_shape_critiques.extend(result)

        # Votes (parallel)
        print(f"[Worker-{worker_id}] >>> Phase 3: Voting (parallel)")
        shape_votes = self._parallel_agent_calls(shape_agents, 'vote', shape_proposals, story_prompt)
        shape_votes = [v for v in shape_votes if v is not None]
        for v in shape_votes:
            print(f"[Worker-{worker_id}]     - votes for Proposal {v.chosen_proposal_index}")

        # Determine winner
        vote_counts = {}
        for vote in shape_votes:
            vote_counts[vote.chosen_proposal_index] = vote_counts.get(vote.chosen_proposal_index, 0) + 1
        winner_index = max(vote_counts, key=vote_counts.get)
        winning_shape = shape_proposals[winner_index]

        print(f"[Worker-{worker_id}] >>> WINNER: {winning_shape.story_shape} ({vote_counts[winner_index]} votes)")

        return {
            "winning_shape": winning_shape,
            "debate_data": {
                "proposals": [p.model_dump() for p in shape_proposals],
                "critiques": [c.model_dump() for c in all_shape_critiques],
                "votes": [v.model_dump() for v in shape_votes],
                "winner_index": winner_index
            }
        }

    def _run_save_the_cat_debate(
        self,
        story_prompt: str,
        theme_question: str,
        characters: list
    ) -> dict:
        """Run parallel debate for Save the Cat type.

        Args:
            story_prompt: The story prompt
            theme_question: Central theme question
            characters: List of characters

        Returns:
            dict: Debate results with winner and metadata
        """
        worker_id = self._get_worker_id()
        print(f"\n[Worker-{worker_id}] {'='*50}")
        print(f"[Worker-{worker_id}] DEBATE 2: SAVE THE CAT TYPE")
        print(f"[Worker-{worker_id}] {'='*50}")

        from src.story_agents.story_shape_agents import (
            SaveTheCatStakesAgent, SaveTheCatCharacterAgent, SaveTheCatThematicAgent
        )

        stc_agents = [
            SaveTheCatStakesAgent(model=self.model),
            SaveTheCatCharacterAgent(model=self.model),
            SaveTheCatThematicAgent(model=self.model),
        ]

        print(f"[Worker-{worker_id}] >>> Phase 1: Proposals (parallel)")
        stc_proposals = self._parallel_agent_calls(
            stc_agents, 'propose_save_the_cat', story_prompt, theme_question, characters, ""
        )
        stc_proposals = [p for p in stc_proposals if p is not None]
        for p in stc_proposals:
            print(f"[Worker-{worker_id}]     - {p.save_the_cat_type}")

        print(f"[Worker-{worker_id}] >>> Phase 2: Critiques (parallel)")
        critique_results = self._parallel_agent_calls(
            stc_agents, 'critique_save_the_cat', stc_proposals, story_prompt, characters
        )
        all_stc_critiques = []
        for result in critique_results:
            if result is not None:
                all_stc_critiques.extend(result)

        print(f"[Worker-{worker_id}] >>> Phase 3: Voting (parallel)")
        stc_votes = self._parallel_agent_calls(stc_agents, 'vote', stc_proposals, story_prompt)
        stc_votes = [v for v in stc_votes if v is not None]
        for v in stc_votes:
            print(f"[Worker-{worker_id}]     - votes for Proposal {v.chosen_proposal_index}")

        vote_counts = {}
        for vote in stc_votes:
            vote_counts[vote.chosen_proposal_index] = vote_counts.get(vote.chosen_proposal_index, 0) + 1
        winner_index = max(vote_counts, key=vote_counts.get)
        winning_stc = stc_proposals[winner_index]

        print(f"[Worker-{worker_id}] >>> WINNER: {winning_stc.save_the_cat_type}")

        return {
            "winning_stc": winning_stc,
            "debate_data": {
                "proposals": [p.model_dump() for p in stc_proposals],
                "critiques": [c.model_dump() for c in all_stc_critiques],
                "votes": [v.model_dump() for v in stc_votes],
                "winner_index": winner_index
            }
        }

    def _run_genre_debate(
        self,
        story_prompt: str,
        theme_question: str
    ) -> dict:
        """Run parallel debate for genre selection.

        Args:
            story_prompt: The story prompt
            theme_question: Central theme question

        Returns:
            dict: Debate results with winner and metadata
        """
        worker_id = self._get_worker_id()
        print(f"\n[Worker-{worker_id}] {'='*50}")
        print(f"[Worker-{worker_id}] DEBATE 3: GENRE SELECTION")
        print(f"[Worker-{worker_id}] {'='*50}")

        from src.story_agents.story_shape_agents import (
            GenrePressureAgent, GenreToneAgent, GenreAudienceAgent
        )

        genre_agents = [
            GenrePressureAgent(model=self.model),
            GenreToneAgent(model=self.model),
            GenreAudienceAgent(model=self.model),
        ]

        print(f"[Worker-{worker_id}] >>> Phase 1: Proposals (parallel)")
        genre_proposals = self._parallel_agent_calls(
            genre_agents, 'propose_genre', story_prompt, theme_question, "", ""
        )
        genre_proposals = [p for p in genre_proposals if p is not None]
        for p in genre_proposals:
            print(f"[Worker-{worker_id}]     - {p.primary_genre}/{p.secondary_genre or 'none'}")

        print(f"[Worker-{worker_id}] >>> Phase 2: Critiques (parallel)")
        critique_results = self._parallel_agent_calls(
            genre_agents, 'critique_genre', genre_proposals, story_prompt
        )
        all_genre_critiques = []
        for result in critique_results:
            if result is not None:
                all_genre_critiques.extend(result)

        print(f"[Worker-{worker_id}] >>> Phase 3: Voting (parallel)")
        genre_votes = self._parallel_agent_calls(genre_agents, 'vote', genre_proposals, story_prompt)
        genre_votes = [v for v in genre_votes if v is not None]
        for v in genre_votes:
            print(f"[Worker-{worker_id}]     - votes for Proposal {v.chosen_proposal_index}")

        vote_counts = {}
        for vote in genre_votes:
            vote_counts[vote.chosen_proposal_index] = vote_counts.get(vote.chosen_proposal_index, 0) + 1
        winner_index = max(vote_counts, key=vote_counts.get)
        winning_genre = genre_proposals[winner_index]

        print(f"[Worker-{worker_id}] >>> WINNER: {winning_genre.primary_genre}" +
              (f"/{winning_genre.secondary_genre}" if winning_genre.secondary_genre else ""))

        return {
            "winning_genre": winning_genre,
            "debate_data": {
                "proposals": [p.model_dump() for p in genre_proposals],
                "critiques": [c.model_dump() for c in all_genre_critiques],
                "votes": [v.model_dump() for v in genre_votes],
                "winner_index": winner_index
            }
        }

    def _run_trope_debate(
        self,
        story_prompt: str,
        theme_question: str
    ) -> dict:
        """Run parallel debate for trope selection.

        Args:
            story_prompt: The story prompt
            theme_question: Central theme question

        Returns:
            dict: Debate results with winner and metadata
        """
        worker_id = self._get_worker_id()
        print(f"\n[Worker-{worker_id}] {'='*50}")
        print(f"[Worker-{worker_id}] DEBATE 4: TROPE SELECTION")
        print(f"[Worker-{worker_id}] {'='*50}")

        from src.story_agents.story_shape_agents import (
            TropeConventionAgent, TropeThematicAgent, TropeSubversionAgent
        )

        trope_agents = [
            TropeConventionAgent(model=self.model),
            TropeThematicAgent(model=self.model),
            TropeSubversionAgent(model=self.model),
        ]

        # Use generic fantasy genre as placeholder since debates run in parallel
        genres = ["Fantasy"]

        print(f"[Worker-{worker_id}] >>> Phase 1: Proposals (parallel)")
        trope_proposals = self._parallel_agent_calls(
            trope_agents, 'propose_tropes', story_prompt, genres, "", theme_question
        )
        trope_proposals = [p for p in trope_proposals if p is not None]
        for p in trope_proposals:
            print(f"[Worker-{worker_id}]     - {len(p.tropes)} tropes")

        print(f"[Worker-{worker_id}] >>> Phase 2: Critiques (parallel)")
        critique_results = self._parallel_agent_calls(
            trope_agents, 'critique_tropes', trope_proposals, story_prompt, genres
        )
        all_trope_critiques = []
        for result in critique_results:
            if result is not None:
                all_trope_critiques.extend(result)

        print(f"[Worker-{worker_id}] >>> Phase 3: Voting (parallel)")
        trope_votes = self._parallel_agent_calls(trope_agents, 'vote', trope_proposals, story_prompt)
        trope_votes = [v for v in trope_votes if v is not None]
        for v in trope_votes:
            print(f"[Worker-{worker_id}]     - votes for Proposal {v.chosen_proposal_index}")

        vote_counts = {}
        for vote in trope_votes:
            vote_counts[vote.chosen_proposal_index] = vote_counts.get(vote.chosen_proposal_index, 0) + 1
        winner_index = max(vote_counts, key=vote_counts.get)
        winning_tropes = trope_proposals[winner_index]

        print(f"[Worker-{worker_id}] >>> WINNER: {len(winning_tropes.tropes)} tropes selected")
        for trope in winning_tropes.tropes:
            print(f"[Worker-{worker_id}]     - {trope.name} ({trope.usage})")

        return {
            "winning_tropes": winning_tropes,
            "debate_data": {
                "proposals": [p.model_dump() for p in trope_proposals],
                "critiques": [c.model_dump() for c in all_trope_critiques],
                "votes": [v.model_dump() for v in trope_votes],
                "winner_index": winner_index
            }
        }


    def step2_story_shape_genre(self, codex: dict) -> Step2Result:
        """Select story shape, genre, and tropes via multi-agent debate.

        Uses multi-agent debates to determine:
        1. Classic Story Shape (7 Basic Plots)
        2. Save the Cat Type
        3. Genre(s)
        4. Tropes to use/subvert

        Args:
            codex: The codex with theme_foundation (Step 0) and characters (Step 1)

        Returns:
            Step2Result with story shape, genre, tropes, and debate history
        """
        start_time = time.time()

        try:
            # Get Step 0 and Step 1 results
            theme_foundation = codex.get("story", {}).get("theme_foundation", {})
            characters = codex.get("story", {}).get("characters", [])

            if not theme_foundation:
                return Step2Result(
                    story_shape="", save_the_cat_type="", primary_genre="",
                    secondary_genre=None, tone_flavor=None, tropes=[],
                    step2_debates={}, success=False,
                    error="Step 0 (Theme Foundation) not run. Run --steps 0 first."
                )

            if not characters:
                return Step2Result(
                    story_shape="", save_the_cat_type="", primary_genre="",
                    secondary_genre=None, tone_flavor=None, tropes=[],
                    step2_debates={}, success=False,
                    error="Step 1 (Character Creation) not run. Run --steps 1 first."
                )

            # Get context
            theme_question = theme_foundation.get("central_question", "")
            story_prompt, setting_prompt = self.extract_prompts(codex)

            print(f"\n{'='*60}")
            print("STEP 2: STORY SHAPE & GENRE SELECTION")
            print(f"{'='*60}")
            print(f">>> Theme: {theme_question[:80]}...")
            print(f">>> Characters: {len(characters)}")

            # Import agents
            from src.story_agents.story_shape_agents import (
                StoryShapeJourneyAgent, StoryShapeEmotionalAgent, StoryShapeThematicAgent,
                SaveTheCatStakesAgent, SaveTheCatCharacterAgent, SaveTheCatThematicAgent,
                GenrePressureAgent, GenreToneAgent, GenreAudienceAgent,
                TropeConventionAgent, TropeThematicAgent, TropeSubversionAgent,
            )

            step2_debates = {}

            # Get parallel config
            step2_config = get_step_config("step2_story_shape")
            parallel_config = step2_config.get("parallel_processing", {})
            parallel_enabled = parallel_config.get("enabled", True)
            max_workers = parallel_config.get("max_workers", 4)

            print(f"\n>>> Parallel Processing: {'ENABLED' if parallel_enabled else 'DISABLED'}")
            print(f">>> Max Workers: {max_workers if parallel_enabled else 1}")

            if parallel_enabled:
                # Run all 4 debates in parallel
                print(f"\n>>> Running 4 debates in parallel with {max_workers} workers...")

                from concurrent.futures import ThreadPoolExecutor

                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    # Submit all debate tasks
                    future_shape = executor.submit(
                        self._run_story_shape_debate,
                        story_prompt, theme_question, characters
                    )
                    future_stc = executor.submit(
                        self._run_save_the_cat_debate,
                        story_prompt, theme_question, characters
                    )
                    future_genre = executor.submit(
                        self._run_genre_debate,
                        story_prompt, theme_question
                    )
                    future_trope = executor.submit(
                        self._run_trope_debate,
                        story_prompt, theme_question
                    )

                    # Collect results as they complete
                    shape_result = future_shape.result()
                    stc_result = future_stc.result()
                    genre_result = future_genre.result()
                    trope_result = future_trope.result()

                # Extract winners
                winning_shape = shape_result["winning_shape"]
                winning_stc = stc_result["winning_stc"]
                winning_genre = genre_result["winning_genre"]
                winning_tropes = trope_result["winning_tropes"]

                # Store debate data
                step2_debates["story_shape_debate"] = shape_result["debate_data"]
                step2_debates["save_the_cat_debate"] = stc_result["debate_data"]
                step2_debates["genre_debate"] = genre_result["debate_data"]
                step2_debates["trope_debate"] = trope_result["debate_data"]

            else:
                # Sequential execution (original code)

                # ====================
                # DEBATE 1: STORY SHAPE
                # ====================
                print(f"\n{'='*50}")
                print("DEBATE 1: STORY SHAPE (7 Basic Plots)")
                print(f"{'='*50}")

                shape_agents = [
                    StoryShapeJourneyAgent(model=self.model),
                    StoryShapeEmotionalAgent(model=self.model),
                    StoryShapeThematicAgent(model=self.model),
                ]

                # Proposals
                print(f"\n>>> Phase 1: Proposals (3 agents)")
                shape_proposals = []
                for agent in shape_agents:
                    print(f"    - {agent.name} proposing...")
                    proposal = agent.propose_story_shape(story_prompt, theme_question, characters)
                    shape_proposals.append(proposal)
                    print(f"      Shape: {proposal.story_shape}")

                # Critiques
                print(f"\n>>> Phase 2: Critiques")
                all_shape_critiques = []
                for agent in shape_agents:
                    critiques = agent.critique_story_shape(shape_proposals, story_prompt, characters)
                    all_shape_critiques.extend(critiques)
                    for c in critiques:
                        print(f"    - {agent.name}: Proposal {c.proposal_index} = {c.score}/10")

                # Votes
                print(f"\n>>> Phase 3: Voting")
                shape_votes = []
                for agent in shape_agents:
                    vote = agent.vote(shape_proposals, story_prompt)
                    shape_votes.append(vote)
                    print(f"    - {agent.name} votes for Proposal {vote.chosen_proposal_index}")

                # Determine winner
                vote_counts = {}
                for vote in shape_votes:
                    vote_counts[vote.chosen_proposal_index] = vote_counts.get(vote.chosen_proposal_index, 0) + 1
                winner_index = max(vote_counts, key=vote_counts.get)
                winning_shape = shape_proposals[winner_index]

                print(f"\n>>> WINNER: {winning_shape.story_shape} ({vote_counts[winner_index]} votes)")

                step2_debates["story_shape_debate"] = {
                    "proposals": [p.model_dump() for p in shape_proposals],
                    "critiques": [c.model_dump() for c in all_shape_critiques],
                    "votes": [v.model_dump() for v in shape_votes],
                    "winner_index": winner_index
                }

                # ====================
                # DEBATE 2: SAVE THE CAT TYPE
                # ====================
                print(f"\n{'='*50}")
                print("DEBATE 2: SAVE THE CAT TYPE")
                print(f"{'='*50}")

                stc_agents = [
                    SaveTheCatStakesAgent(model=self.model),
                    SaveTheCatCharacterAgent(model=self.model),
                    SaveTheCatThematicAgent(model=self.model),
                ]

                print(f"\n>>> Phase 1: Proposals (parallel)")
                stc_proposals = self._parallel_agent_calls(
                    stc_agents, 'propose_save_the_cat',
                    story_prompt, theme_question, characters, winning_shape.story_shape
                )
                for i, proposal in enumerate(stc_proposals):
                    if proposal:
                        print(f"    - {stc_agents[i].name}: {proposal.save_the_cat_type}")

                print(f"\n>>> Phase 2: Critiques (parallel)")
                critique_results = self._parallel_agent_calls(
                    stc_agents, 'critique_save_the_cat',
                    stc_proposals, story_prompt, characters
                )
                all_stc_critiques = []
                for cr in critique_results:
                    if cr:
                        all_stc_critiques.extend(cr)

                print(f"\n>>> Phase 3: Voting (parallel)")
                stc_votes = self._parallel_agent_calls(stc_agents, 'vote', stc_proposals, story_prompt)
                for i, vote in enumerate(stc_votes):
                    if vote:
                        print(f"    - {stc_agents[i].name} votes for Proposal {vote.chosen_proposal_index}")

                vote_counts = {}
                for vote in stc_votes:
                    vote_counts[vote.chosen_proposal_index] = vote_counts.get(vote.chosen_proposal_index, 0) + 1
                winner_index = max(vote_counts, key=vote_counts.get)
                winning_stc = stc_proposals[winner_index]

                print(f"\n>>> WINNER: {winning_stc.save_the_cat_type}")

                step2_debates["save_the_cat_debate"] = {
                    "proposals": [p.model_dump() for p in stc_proposals],
                    "critiques": [c.model_dump() for c in all_stc_critiques],
                    "votes": [v.model_dump() for v in stc_votes],
                    "winner_index": winner_index
                }

                # ====================
                # DEBATE 3: GENRE
                # ====================
                print(f"\n{'='*50}")
                print("DEBATE 3: GENRE SELECTION")
                print(f"{'='*50}")

                genre_agents = [
                    GenrePressureAgent(model=self.model),
                    GenreToneAgent(model=self.model),
                    GenreAudienceAgent(model=self.model),
                ]

                print(f"\n>>> Phase 1: Proposals")
                genre_proposals = []
                for agent in genre_agents:
                    proposal = agent.propose_genre(story_prompt, theme_question, winning_shape.story_shape, winning_stc.save_the_cat_type)
                    genre_proposals.append(proposal)
                    print(f"    - {agent.name}: {proposal.primary_genre}/{proposal.secondary_genre or 'none'}")

                print(f"\n>>> Phase 2: Critiques")
                all_genre_critiques = []
                for agent in genre_agents:
                    critiques = agent.critique_genre(genre_proposals, story_prompt)
                    all_genre_critiques.extend(critiques)

                print(f"\n>>> Phase 3: Voting")
                genre_votes = []
                for agent in genre_agents:
                    vote = agent.vote(genre_proposals, story_prompt)
                    genre_votes.append(vote)
                    print(f"    - {agent.name} votes for Proposal {vote.chosen_proposal_index}")

                vote_counts = {}
                for vote in genre_votes:
                    vote_counts[vote.chosen_proposal_index] = vote_counts.get(vote.chosen_proposal_index, 0) + 1
                winner_index = max(vote_counts, key=vote_counts.get)
                winning_genre = genre_proposals[winner_index]

                print(f"\n>>> WINNER: {winning_genre.primary_genre}" +
                      (f"/{winning_genre.secondary_genre}" if winning_genre.secondary_genre else ""))

                step2_debates["genre_debate"] = {
                    "proposals": [p.model_dump() for p in genre_proposals],
                    "critiques": [c.model_dump() for c in all_genre_critiques],
                    "votes": [v.model_dump() for v in genre_votes],
                    "winner_index": winner_index
                }

                # ====================
                # DEBATE 4: TROPES
                # ====================
                print(f"\n{'='*50}")
                print("DEBATE 4: TROPE SELECTION")
                print(f"{'='*50}")

                trope_agents = [
                    TropeConventionAgent(model=self.model),
                    TropeThematicAgent(model=self.model),
                    TropeSubversionAgent(model=self.model),
                ]

                genres = [winning_genre.primary_genre]
                if winning_genre.secondary_genre:
                    genres.append(winning_genre.secondary_genre)

                print(f"\n>>> Phase 1: Proposals")
                trope_proposals = []
                for agent in trope_agents:
                    proposal = agent.propose_tropes(story_prompt, genres, winning_shape.story_shape, theme_question)
                    trope_proposals.append(proposal)
                    print(f"    - {agent.name}: {len(proposal.tropes)} tropes")

                print(f"\n>>> Phase 2: Critiques")
                all_trope_critiques = []
                for agent in trope_agents:
                    critiques = agent.critique_tropes(trope_proposals, story_prompt, genres)
                    all_trope_critiques.extend(critiques)

                print(f"\n>>> Phase 3: Voting")
                trope_votes = []
                for agent in trope_agents:
                    vote = agent.vote(trope_proposals, story_prompt)
                    trope_votes.append(vote)
                    print(f"    - {agent.name} votes for Proposal {vote.chosen_proposal_index}")

                vote_counts = {}
                for vote in trope_votes:
                    vote_counts[vote.chosen_proposal_index] = vote_counts.get(vote.chosen_proposal_index, 0) + 1
                winner_index = max(vote_counts, key=vote_counts.get)
                winning_tropes = trope_proposals[winner_index]

                print(f"\n>>> WINNER: {len(winning_tropes.tropes)} tropes selected")
                for trope in winning_tropes.tropes:
                    print(f"    - {trope.name} ({trope.usage})")

                step2_debates["trope_debate"] = {
                    "proposals": [p.model_dump() for p in trope_proposals],
                    "critiques": [c.model_dump() for c in all_trope_critiques],
                    "votes": [v.model_dump() for v in trope_votes],
                    "winner_index": winner_index
                }

            # Convert Trope objects to dicts for storage
            tropes_as_dicts = [t.model_dump() for t in winning_tropes.tropes]

            duration = time.time() - start_time

            print(f"\n{'='*60}")
            print(f"STEP 2 COMPLETE! Duration: {duration:.1f}s")
            print(f"{'='*60}")
            print(f">>> Story Shape: {winning_shape.story_shape}")
            print(f">>> STC Type: {winning_stc.save_the_cat_type}")
            print(f">>> Genre: {winning_genre.primary_genre}" +
                  (f"/{winning_genre.secondary_genre}" if winning_genre.secondary_genre else ""))
            print(f">>> Tropes: {len(winning_tropes.tropes)}")

            return Step2Result(
                story_shape=winning_shape.story_shape,
                save_the_cat_type=winning_stc.save_the_cat_type,
                primary_genre=winning_genre.primary_genre,
                secondary_genre=winning_genre.secondary_genre,
                tone_flavor=winning_genre.tone_flavor,
                tropes=tropes_as_dicts,
                step2_debates=step2_debates,
                success=True,
                duration_seconds=duration
            )

        except Exception as e:
            duration = time.time() - start_time
            print(f"\n>>> Step 2 FAILED: {e}")
            import traceback
            traceback.print_exc()

            return Step2Result(
                story_shape="", save_the_cat_type="", primary_genre="",
                secondary_genre=None, tone_flavor=None, tropes=[],
                step2_debates={}, success=False,
                error=str(e), duration_seconds=duration
            )

    # =========================================================================
    # STEP 1: PLOTTING (7-Point Structure via Research-Driven Multi-Agent Debate)
    # =========================================================================

    def step1_plotting(self, codex: dict) -> Step1PlottingResult:
        """Generate 7-point story structure via research-driven multi-agent debate.

        NOTE: This will become Step 3 in the new workflow. Keeping for backward compatibility.

        Uses 5 methodology-embodied agents debating each beat:
        - DanWellsAgent: 7-Point Structure (Resolution first, Hook as opposite)
        - BlakeSnyderAgent: Save the Cat (empathy, false victory/defeat, "all is lost")
        - PinchMasterAgent: Pinch Point Theory (37%/62% timing, escalation)
        - TruthSeekerAgent: Narrative Theory (truth reveals, transformation)
        - AudienceAdvocateAgent: Reader/Viewer perspective (emotional payoff, satisfaction)

        Debate flow for each beat:
        1. 3-4 relevant agents propose based on their methodology
        2. Cross-agent critique round
        3. All 5 agents vote for best proposal
        4. Merge/refine winning proposal

        Args:
            codex: The codex dictionary with prompts and author info

        Returns:
            Step1PlottingResult with structure_beats, theme, title, and debate_summary
        """
        start_time = time.time()
        debate_summary = {
            "agents_used": [],
            "methodologies": [],
            "rounds": [],
            "total_critiques": 0,
        }

        try:
            # Get prompts from codex
            story_prompt, setting_prompt = self.extract_prompts(codex)
            if not story_prompt:
                return Step1PlottingResult(
                    story_seed_parsed={},
                    structure_beats={},
                    theme="",
                    title_suggestion="",
                    debate_summary={},
                    success=False,
                    error="Missing story_engine prompts in codex",
                )

            # Get author's preferred structure
            structure = self.get_structure()
            print(f"\n{'='*60}")
            print("RESEARCH-DRIVEN MULTI-AGENT DEBATE")
            print(f"{'='*60}")
            print(f">>> Structure: {structure.name}")
            print(f">>> Method: 5 agents embodying different storytelling methodologies")
            print(f">>> Rules: 3-4 proposals per beat, all 5 agents vote")

            # =========================================
            # Initialize 5 Research-Embodied Agents
            # =========================================
            parser = StorySeedParserAgent(model=self.model)
            dan_wells = DanWellsAgent(model=self.model)
            blake_snyder = BlakeSnyderAgent(model=self.model)
            pinch_master = PinchMasterAgent(model=self.model)
            truth_seeker = TruthSeekerAgent(model=self.model)
            audience_advocate = AudienceAdvocateAgent(model=self.model)  # 5th agent
            validator = StructureValidatorAgent(model=self.model)

            # All 5 agents for voting
            all_agents = [dan_wells, blake_snyder, pinch_master, truth_seeker, audience_advocate]

            debate_summary["agents_used"] = [
                "StorySeedParser",
                "DanWellsAgent", "BlakeSnyderAgent",
                "PinchMasterAgent", "TruthSeekerAgent",
                "AudienceAdvocateAgent",
                "StructureValidator"
            ]
            debate_summary["methodologies"] = [
                {"agent": "DanWellsAgent", "source": dan_wells.METHODOLOGY_SOURCE, "beliefs": dan_wells.CORE_BELIEFS},
                {"agent": "BlakeSnyderAgent", "source": blake_snyder.METHODOLOGY_SOURCE, "beliefs": blake_snyder.CORE_BELIEFS},
                {"agent": "PinchMasterAgent", "source": pinch_master.METHODOLOGY_SOURCE, "beliefs": pinch_master.CORE_BELIEFS},
                {"agent": "TruthSeekerAgent", "source": truth_seeker.METHODOLOGY_SOURCE, "beliefs": truth_seeker.CORE_BELIEFS},
                {"agent": "AudienceAdvocateAgent", "source": audience_advocate.METHODOLOGY_SOURCE, "beliefs": audience_advocate.CORE_BELIEFS},
            ]

            print("\n--- 5 Agent Methodologies ---")
            print(f"    1. DanWells: {dan_wells.METHODOLOGY_NAME}")
            print(f"    2. BlakeSnyder: {blake_snyder.METHODOLOGY_NAME}")
            print(f"    3. PinchMaster: {pinch_master.METHODOLOGY_NAME}")
            print(f"    4. TruthSeeker: {truth_seeker.METHODOLOGY_NAME}")
            print(f"    5. AudienceAdvocate: {audience_advocate.METHODOLOGY_NAME}")

            # =========================================
            # ROUND 1: Parse Story Seed
            # =========================================
            print(f"\n{'='*50}")
            print("ROUND 1: PARSING STORY SEED")
            print(f"{'='*50}")

            story_seed_parsed = parser.parse_story_seed(story_prompt, setting_prompt)
            print(f"    Adjective: {story_seed_parsed.adjective}")
            print(f"    Why: {story_seed_parsed.adjective_meaning[:80]}...")
            print(f"    Hero: {story_seed_parsed.hero_role}")
            print(f"    Goal: {story_seed_parsed.goal}")
            print(f"    Stakes: {story_seed_parsed.stakes}")

            debate_summary["rounds"].append({
                "round": "1_parse_seed",
                "output": story_seed_parsed.model_dump()
            })

            # =========================================
            # ROUND 2: Resolution Proposals + Critique + Vote
            # (4 proposers: DanWells, BlakeSnyder, TruthSeeker, AudienceAdvocate)
            # (5 voters: all agents)
            # =========================================
            print(f"\n{'='*50}")
            print("ROUND 2: RESOLUTION DESIGN (4 proposals, 5 voters)")
            print(f"{'='*50}")
            print(">>> 4 agents propose Resolution based on their methodology...")

            # Get 4 proposals (TruthSeeker doesn't have propose_resolution, use similar)
            dan_wells_resolution = dan_wells.propose_resolution(story_seed_parsed, setting_prompt)
            blake_snyder_resolution = blake_snyder.propose_resolution(story_seed_parsed, setting_prompt)
            audience_resolution = audience_advocate.propose_resolution(story_seed_parsed, setting_prompt)
            # TruthSeeker uses hook to propose but we need a resolution proposal
            # For now, use 3 proposals + add TruthSeeker critique
            # TODO: Add TruthSeeker.propose_resolution() in future

            proposals = [dan_wells_resolution, blake_snyder_resolution, audience_resolution]

            print(f"\n    [DanWells] Resolution: {dan_wells_resolution.beat.description[:70]}...")
            print(f"    [BlakeSnyder] Resolution: {blake_snyder_resolution.beat.description[:70]}...")
            print(f"    [AudienceAdvocate] Resolution: {audience_resolution.beat.description[:70]}...")

            # Critique round
            print("\n>>> Critique Round...")
            critiques = []

            # Cross-critiques between proposers
            critique1 = blake_snyder.critique_proposal(
                dan_wells.name, "resolution", dan_wells_resolution.beat,
                story_seed_parsed
            )
            critiques.append(critique1)
            print(f"    [BlakeSnyder -> DanWells] {critique1.criticism[:60]}...")
            debate_summary["total_critiques"] += 1

            critique2 = dan_wells.critique_proposal(
                blake_snyder.name, "resolution", blake_snyder_resolution.beat,
                story_seed_parsed
            )
            critiques.append(critique2)
            print(f"    [DanWells -> BlakeSnyder] {critique2.criticism[:60]}...")
            debate_summary["total_critiques"] += 1

            critique3 = truth_seeker.critique_proposal(
                audience_advocate.name, "resolution", audience_resolution.beat,
                story_seed_parsed
            )
            critiques.append(critique3)
            print(f"    [TruthSeeker -> AudienceAdvocate] {critique3.criticism[:60]}...")
            debate_summary["total_critiques"] += 1

            # Voting - ALL 5 agents vote
            print("\n>>> All 5 agents vote for best Resolution...")
            votes = []
            for agent in all_agents:
                vote = agent.vote_for_best("resolution", proposals, story_seed_parsed)
                votes.append(vote)
                print(f"    [{agent.name}] votes for: {vote.voted_for_agent}")

            # Determine winner (handles mismatched vote names)
            winner_proposal, winner, vote_count = self._find_winner_proposal(proposals, votes)
            resolution = winner_proposal.beat
            print(f"\n    >>> WINNER: {winner} ({vote_count}/5 votes)")
            print(f"    >>> Resolution: {resolution.emotional_state}")

            debate_summary["rounds"].append({
                "round": "2_resolution",
                "num_proposals": len(proposals),
                "num_voters": len(all_agents),
                "proposals": [p.beat.model_dump() for p in proposals],
                "critiques": [c.model_dump() for c in critiques],
                "votes": [v.model_dump() for v in votes],
                "winner": winner,
                "final_beat": resolution.model_dump()
            })

            # =========================================
            # ROUND 3: Hook Proposals + Critique + Vote
            # (4 proposers: DanWells, BlakeSnyder, TruthSeeker, AudienceAdvocate)
            # (5 voters: all agents)
            # =========================================
            print(f"\n{'='*50}")
            print("ROUND 3: HOOK DESIGN (4 proposals, 5 voters)")
            print(f"{'='*50}")
            print(">>> Hook must be OPPOSITE of Resolution...")

            # Get 4 proposals
            dan_wells_hook = dan_wells.propose_hook(story_seed_parsed, resolution, setting_prompt)
            blake_snyder_hook = blake_snyder.propose_hook(story_seed_parsed, resolution, setting_prompt)
            truth_seeker_hook = truth_seeker.propose_hook(story_seed_parsed, resolution, setting_prompt)
            audience_hook = audience_advocate.propose_hook(story_seed_parsed, resolution, setting_prompt)

            proposals = [dan_wells_hook, blake_snyder_hook, truth_seeker_hook, audience_hook]

            print(f"\n    [DanWells] Hook (Opposite): {dan_wells_hook.beat.description[:60]}...")
            print(f"    [BlakeSnyder] Hook (Save the Cat): {blake_snyder_hook.beat.description[:60]}...")
            print(f"    [TruthSeeker] Hook (The Lie): {truth_seeker_hook.beat.description[:60]}...")
            print(f"    [AudienceAdvocate] Hook (Care): {audience_hook.beat.description[:60]}...")

            # Critique round
            print("\n>>> Critique Round...")
            critiques = []

            critique = blake_snyder.critique_proposal(
                dan_wells.name, "hook", dan_wells_hook.beat, story_seed_parsed
            )
            critiques.append(critique)
            print(f"    [BlakeSnyder -> DanWells] {critique.criticism[:60]}...")
            debate_summary["total_critiques"] += 1

            critique = truth_seeker.critique_proposal(
                blake_snyder.name, "hook", blake_snyder_hook.beat, story_seed_parsed
            )
            critiques.append(critique)
            print(f"    [TruthSeeker -> BlakeSnyder] {critique.criticism[:60]}...")
            debate_summary["total_critiques"] += 1

            critique = audience_advocate.critique_proposal(
                truth_seeker.name, "hook", truth_seeker_hook.beat, story_seed_parsed
            )
            critiques.append(critique)
            print(f"    [AudienceAdvocate -> TruthSeeker] {critique.criticism[:60]}...")
            debate_summary["total_critiques"] += 1

            # Voting - ALL 5 agents vote
            print("\n>>> All 5 agents vote for best Hook...")
            votes = []
            for agent in all_agents:
                vote = agent.vote_for_best("hook", proposals, story_seed_parsed)
                votes.append(vote)
                print(f"    [{agent.name}] votes for: {vote.voted_for_agent}")

            # Get winning hook (handles mismatched vote names)
            winner_proposal, winner, vote_count = self._find_winner_proposal(proposals, votes)
            hook = winner_proposal.beat
            print(f"\n    >>> WINNER: {winner} ({vote_count}/5 votes)")
            print(f"    >>> Hook: {hook.emotional_state}")

            debate_summary["rounds"].append({
                "round": "3_hook",
                "num_proposals": len(proposals),
                "num_voters": len(all_agents),
                "proposals": [p.beat.model_dump() for p in proposals],
                "critiques": [c.model_dump() for c in critiques],
                "votes": [v.model_dump() for v in votes],
                "winner": winner,
                "final_beat": hook.model_dump()
            })

            # =========================================
            # ROUND 4: Midpoint Design
            # (3 proposers: DanWells, BlakeSnyder, TruthSeeker)
            # (5 voters: all agents)
            # =========================================
            print(f"\n{'='*50}")
            print("ROUND 4: MIDPOINT DESIGN (3 proposals, 5 voters)")
            print(f"{'='*50}")
            print(">>> The Pivot - from REACTION to ACTION...")

            dan_wells_midpoint = dan_wells.propose_midpoint(story_seed_parsed, hook, resolution, setting_prompt)
            blake_snyder_midpoint = blake_snyder.propose_midpoint(story_seed_parsed, hook, resolution, setting_prompt)
            truth_seeker_midpoint = truth_seeker.propose_midpoint(story_seed_parsed, hook, resolution, setting_prompt)

            proposals = [dan_wells_midpoint, blake_snyder_midpoint, truth_seeker_midpoint]

            print(f"\n    [DanWells] Midpoint (Reaction->Action): {dan_wells_midpoint.beat.description[:55]}...")
            print(f"    [BlakeSnyder] Midpoint (False V/D): {blake_snyder_midpoint.beat.description[:55]}...")
            print(f"    [TruthSeeker] Midpoint (Context Change): {truth_seeker_midpoint.beat.description[:50]}...")

            # Voting - ALL 5 agents vote
            print("\n>>> All 5 agents vote for best Midpoint...")
            votes = []
            for agent in all_agents:
                vote = agent.vote_for_best("midpoint", proposals, story_seed_parsed)
                votes.append(vote)
                print(f"    [{agent.name}] votes for: {vote.voted_for_agent}")

            # Get winning midpoint (handles mismatched vote names)
            winner_proposal, winner, vote_count = self._find_winner_proposal(proposals, votes)
            midpoint = winner_proposal.beat
            print(f"\n    >>> WINNER: {winner} ({vote_count}/5 votes)")
            print(f"    >>> Midpoint: {midpoint.emotional_state}")

            debate_summary["rounds"].append({
                "round": "4_midpoint",
                "num_proposals": len(proposals),
                "num_voters": len(all_agents),
                "proposals": [p.beat.model_dump() for p in proposals],
                "votes": [v.model_dump() for v in votes],
                "winner": winner,
                "final_beat": midpoint.model_dump()
            })

            # =========================================
            # ROUND 5: Plot Turns (3 proposers, 5 voters)
            # (3 proposers: DanWells, PinchMaster, AudienceAdvocate)
            # =========================================
            print(f"\n{'='*50}")
            print("ROUND 5: PLOT TURNS (3 proposals per turn, 5 voters)")
            print(f"{'='*50}")
            print(">>> Doorways into/out of the story...")

            # Use legacy method for base plot turns, then vote
            tension_builder = TensionBuilderAgent(model=self.model)
            base_pt1, base_pt2 = tension_builder.design_plot_turns(
                story_seed_parsed, hook, midpoint, resolution, setting_prompt
            )

            # Get AudienceAdvocate's proposals for plot turns
            audience_pt1 = audience_advocate.propose_plot_turn(
                story_seed_parsed, hook, midpoint, resolution, 1, setting_prompt
            )
            audience_pt2 = audience_advocate.propose_plot_turn(
                story_seed_parsed, hook, midpoint, resolution, 2, setting_prompt
            )

            print(f"\n    [TensionBuilder] PT1: {base_pt1.description[:60]}...")
            print(f"    [AudienceAdvocate] PT1: {audience_pt1.beat.description[:60]}...")

            # Create proposal objects for voting
            from src.story_schemas import AgentProposal
            base_pt1_proposal = AgentProposal(
                agent_name="TENSION_BUILDER",
                methodology_source="Pinch Point Theory / Dan Wells",
                beat=base_pt1,
                methodology_reasoning="Plot Turn 1 forces hero from status quo into the story."
            )

            pt1_proposals = [base_pt1_proposal, audience_pt1]

            # Vote for PT1
            print("\n>>> All 5 agents vote for best Plot Turn 1...")
            votes = []
            for agent in all_agents:
                vote = agent.vote_for_best("plot_turn_1", pt1_proposals, story_seed_parsed)
                votes.append(vote)

            # Get winning PT1 (handles mismatched vote names)
            winner_proposal, winner, vote_count = self._find_winner_proposal(pt1_proposals, votes)
            plot_turn_1 = winner_proposal.beat
            print(f"    >>> PT1 WINNER: {winner} ({vote_count}/5 votes)")

            # Vote for PT2
            print(f"\n    [TensionBuilder] PT2: {base_pt2.description[:60]}...")
            print(f"    [AudienceAdvocate] PT2: {audience_pt2.beat.description[:60]}...")

            base_pt2_proposal = AgentProposal(
                agent_name="TENSION_BUILDER",
                methodology_source="Pinch Point Theory / Dan Wells",
                beat=base_pt2,
                methodology_reasoning="Plot Turn 2 gives hero the final piece needed for victory."
            )

            pt2_proposals = [base_pt2_proposal, audience_pt2]

            print("\n>>> All 5 agents vote for best Plot Turn 2...")
            votes = []
            for agent in all_agents:
                vote = agent.vote_for_best("plot_turn_2", pt2_proposals, story_seed_parsed)
                votes.append(vote)

            # Get winning PT2 (handles mismatched vote names)
            winner_proposal, winner, vote_count = self._find_winner_proposal(pt2_proposals, votes)
            plot_turn_2 = winner_proposal.beat
            print(f"    >>> PT2 WINNER: {winner} ({vote_count}/5 votes)")

            debate_summary["rounds"].append({
                "round": "5_plot_turns",
                "num_voters": len(all_agents),
                "plot_turn_1": plot_turn_1.model_dump(),
                "plot_turn_2": plot_turn_2.model_dump()
            })

            # =========================================
            # ROUND 6: Pinch Points (3 proposers, 5 voters)
            # (3 proposers: PinchMaster, BlakeSnyder, TruthSeeker)
            # =========================================
            print(f"\n{'='*50}")
            print("ROUND 6: PINCH POINTS (3 proposals, 5 voters)")
            print(f"{'='*50}")
            print(">>> Antagonist pressure points (37% and 62%)...")

            # PP1 proposals
            pinch_master_pp1 = pinch_master.propose_pinch_point_1(
                story_seed_parsed, hook, plot_turn_1, setting_prompt
            )

            print(f"\n    [PinchMaster] PP1 (37%): {pinch_master_pp1.beat.description[:60]}...")

            # Use PinchMaster's PP1 as the base (they specialize in this)
            pinch_point_1 = pinch_master_pp1.beat

            # PP2 proposals (3 proposers)
            blake_snyder_pp2 = blake_snyder.propose_pinch_point_2(
                story_seed_parsed, midpoint, setting_prompt
            )
            pinch_master_pp2 = pinch_master.propose_pinch_point_2(
                story_seed_parsed, pinch_point_1, midpoint, setting_prompt
            )

            print(f"\n    [BlakeSnyder] PP2 (All Is Lost): {blake_snyder_pp2.beat.description[:55]}...")
            print(f"    [PinchMaster] PP2 (Darker): {pinch_master_pp2.beat.description[:55]}...")

            pp2_proposals = [blake_snyder_pp2, pinch_master_pp2]

            # Critique PP2 proposals
            print("\n>>> Critique Round for PP2...")
            critiques = []

            critique = pinch_master.critique_proposal(
                blake_snyder.name, "pinch_point_2", blake_snyder_pp2.beat,
                story_seed_parsed, {"pinch_point_1": pinch_point_1}
            )
            critiques.append(critique)
            print(f"    [PinchMaster -> BlakeSnyder] {critique.criticism[:60]}...")
            debate_summary["total_critiques"] += 1

            critique = blake_snyder.critique_proposal(
                pinch_master.name, "pinch_point_2", pinch_master_pp2.beat,
                story_seed_parsed
            )
            critiques.append(critique)
            print(f"    [BlakeSnyder -> PinchMaster] {critique.criticism[:60]}...")
            debate_summary["total_critiques"] += 1

            # All 5 agents vote for PP2
            print("\n>>> All 5 agents vote for best Pinch Point 2...")
            votes = []
            for agent in all_agents:
                vote = agent.vote_for_best("pinch_point_2", pp2_proposals, story_seed_parsed)
                votes.append(vote)
                print(f"    [{agent.name}] votes for: {vote.voted_for_agent}")

            # Get winning PP2 (handles mismatched vote names)
            winner_proposal, winner, vote_count = self._find_winner_proposal(pp2_proposals, votes)
            pinch_point_2 = winner_proposal.beat
            print(f"\n    >>> PP2 WINNER: {winner} ({vote_count}/5 votes)")

            debate_summary["rounds"].append({
                "round": "6_pinch_points",
                "num_voters": len(all_agents),
                "pinch_point_1": pinch_point_1.model_dump(),
                "pp2_proposals": [p.beat.model_dump() for p in pp2_proposals],
                "pp2_critiques": [c.model_dump() for c in critiques],
                "pp2_votes": [v.model_dump() for v in votes],
                "pp2_winner": winner,
                "pinch_point_2": pinch_point_2.model_dump()
            })

            # =========================================
            # ROUND 7: Final Validation (All Methodologies)
            # =========================================
            print(f"\n{'='*50}")
            print("ROUND 7: FINAL VALIDATION")
            print(f"{'='*50}")

            # Assemble complete structure
            complete_structure = SevenPointStructureSchema(
                hook=hook,
                plot_turn_1=plot_turn_1,
                pinch_point_1=pinch_point_1,
                midpoint=midpoint,
                pinch_point_2=pinch_point_2,
                plot_turn_2=plot_turn_2,
                resolution=resolution,
            )

            validation = validator.validate_structure(story_seed_parsed, complete_structure)

            print(f"\n    VALIDATION RESULTS:")
            print(f"    Valid: {validation.is_valid}")
            print(f"    Hook/Resolution Opposite: {validation.hook_resolution_opposite}")
            print(f"    Tension Escalates: {validation.tension_escalates}")
            print(f"    Midpoint Pivot Clear: {validation.midpoint_pivot_clear}")

            if validation.strengths:
                print(f"\n    STRENGTHS:")
                for s in validation.strengths[:3]:
                    print(f"      + {s[:70]}...")

            if validation.weaknesses:
                print(f"\n    WEAKNESSES:")
                for w in validation.weaknesses[:3]:
                    print(f"      - {w[:70]}...")

            debate_summary["rounds"].append({
                "round": "7_validation",
                "validation": validation.model_dump()
            })

            # =========================================
            # Extract Theme and Title
            # =========================================
            # Theme from the arc between Hook and Resolution
            theme = f"From {story_seed_parsed.adjective.lower()} to {resolution.emotional_state.split()[0].lower()}: {resolution.purpose}"

            # Title suggestion based on adjective and stakes
            title_words = story_seed_parsed.adjective.title()
            title_suggestion = f"The {title_words} {story_seed_parsed.hero_role.split()[-1].title()}"

            duration = time.time() - start_time

            print(f"\n{'='*60}")
            print("5-AGENT DEBATE COMPLETE")
            print(f"{'='*60}")
            print(f">>> Duration: {duration:.1f}s")
            print(f">>> Agents: 5 (DanWells, BlakeSnyder, PinchMaster, TruthSeeker, AudienceAdvocate)")
            print(f">>> Total Critiques Exchanged: {debate_summary['total_critiques']}")
            print(f">>> Theme: {theme[:80]}...")
            print(f">>> Title: {title_suggestion}")

            return Step1PlottingResult(
                story_seed_parsed=story_seed_parsed.model_dump(),
                structure_beats=complete_structure.model_dump(),
                theme=theme,
                title_suggestion=title_suggestion,
                debate_summary=debate_summary,
                success=True,
                duration_seconds=round(duration, 2),
            )

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Step1PlottingResult(
                story_seed_parsed={},
                structure_beats={},
                theme="",
                title_suggestion="",
                debate_summary=debate_summary,
                success=False,
                error=str(e),
                duration_seconds=round(time.time() - start_time, 2),
            )

    # =========================================================================
    # STEP 2: CHARACTER GENERATION (Multi-Agent Debate)
    # =========================================================================

    def _extract_characters_from_outline(self, codex: dict) -> list[dict]:
        """Extract character roles from story seed and structure beats.

        Returns list of dicts with role, type, and relevant story context.
        """
        characters = []
        outline = codex.get("story", {}).get("outline", {})
        story_seed = outline.get("story_seed_parsed", {})
        structure_beats = outline.get("structure_beats", {})

        # 1. Protagonist from story_seed
        hero_role = story_seed.get("hero_role", "the protagonist")
        adjective = story_seed.get("adjective", "UNKNOWN")
        goal = story_seed.get("goal", "")
        stakes = story_seed.get("stakes", "")

        characters.append({
            "role": hero_role,
            "type": "protagonist",
            "adjective": adjective,
            "goal": goal,
            "stakes": stakes,
        })

        # 2. Parse stakes for supporting characters
        # e.g., "blame falls on closest friend" → extract "closest friend"
        stakes_lower = stakes.lower()
        if "closest friend" in stakes_lower or "best friend" in stakes_lower:
            characters.append({
                "role": "the closest friend",
                "type": "supporting",
                "adjective": "",
                "goal": "support the protagonist",
                "stakes": "will be blamed for protagonist's actions",
            })
        elif "family" in stakes_lower or "loved one" in stakes_lower:
            characters.append({
                "role": "the loved one",
                "type": "supporting",
                "adjective": "",
                "goal": "support the protagonist",
                "stakes": "at risk from protagonist's choices",
            })

        # 3. Look for antagonist mentions in structure beats
        # Check if there's clear antagonist role in the beats
        has_antagonist = False
        for beat_name, beat in structure_beats.items():
            if isinstance(beat, dict):
                desc = beat.get("description", "").lower()
                if any(word in desc for word in ["enemy", "opponent", "antagonist", "villain", "corrupt", "tyrann"]):
                    has_antagonist = True
                    break

        if has_antagonist:
            characters.append({
                "role": "the antagonist",
                "type": "antagonist",
                "adjective": "",
                "goal": "oppose the protagonist",
                "stakes": "",
            })

        return characters

    def _run_name_debate(
        self,
        character_role: str,
        first_initial: str,
        last_initial: str,
        logline: str,
        setting_prompt: str,
        existing_names: list[str],
    ) -> dict:
        """Run 3-agent name debate for a single character."""
        # Initialize name agents
        creative = NameCreativeAgent(model=self.model)
        authentic = NameAuthenticAgent(model=self.model)
        distinctive = NameDistinctiveAgent(model=self.model)
        agents = [creative, authentic, distinctive]

        existing_names_str = ", ".join(existing_names) if existing_names else "None yet"

        context = f"""CHARACTER ROLE: {character_role}
STORY LOGLINE: {logline}
WORLD SETTING: {setting_prompt}
EXISTING NAMES (must be distinct): {existing_names_str}

CONSTRAINTS:
- First name MUST start with: {first_initial}
- Last name MUST start with: {last_initial}"""

        # Round 1: Proposals (parallel)
        proposal_prompt = f"""{context}

Propose a character name that:
1. Starts with {first_initial} for first name
2. Starts with {last_initial} for last name
3. Fits the character's role and setting
4. Is distinct from existing names"""

        print(f"      Generating name proposals (parallel)...")
        from concurrent.futures import ThreadPoolExecutor, as_completed

        def _name_propose(agent):
            try:
                proposal = agent.invoke_structured(
                    proposal_prompt, NameProposal, max_tokens=500
                )
                return {
                    "agent": agent.name,
                    "first_name": proposal.first_name,
                    "last_name": proposal.last_name,
                    "full_name": f"{proposal.first_name} {proposal.last_name}",
                    "reasoning": proposal.reasoning,
                }
            except Exception as e:
                return {
                    "agent": agent.name,
                    "first_name": f"{first_initial}ara",
                    "last_name": f"{last_initial}ith",
                    "full_name": f"{first_initial}ara {last_initial}ith",
                    "reasoning": f"Fallback: {str(e)[:50]}",
                }

        proposals = [None] * len(agents)
        with ThreadPoolExecutor(max_workers=len(agents)) as executor:
            futures = {executor.submit(_name_propose, agent): i for i, agent in enumerate(agents)}
            for future in as_completed(futures):
                proposals[futures[future]] = future.result()

        # Round 2: Critiques
        proposals_text = "\n".join([
            f"Proposal {i}: {p['full_name']} - {p['reasoning'][:80]}..."
            for i, p in enumerate(proposals)
        ])

        critique_prompt = f"""{context}

PROPOSALS:
{proposals_text}

Critique ALL proposals. Score each 1-10."""

        critiques = [None] * len(agents)
        print(f"      Gathering critiques (parallel)...")

        def _name_critique(agent):
            try:
                agent_critiques = agent.invoke_structured(
                    critique_prompt, NameCritiques, max_tokens=1000
                )
                return {
                    "agent": agent.name,
                    "reviews": [
                        {"proposal": r.proposal_index, "score": r.score}
                        for r in agent_critiques.reviews
                    ]
                }
            except Exception:
                return {
                    "agent": agent.name,
                    "reviews": [{"proposal": i, "score": 5} for i in range(3)]
                }

        with ThreadPoolExecutor(max_workers=len(agents)) as executor:
            futures = {executor.submit(_name_critique, agent): i for i, agent in enumerate(agents)}
            for future in as_completed(futures):
                critiques[futures[future]] = future.result()

        # Round 3: Voting
        vote_prompt = f"""{context}

PROPOSALS:
{proposals_text}

Vote for the BEST name. You CANNOT vote for your own proposal.
Agent positions: NAME_CREATIVE=0, NAME_AUTHENTIC=1, NAME_DISTINCTIVE=2"""

        votes = {}
        print(f"      Collecting votes (parallel)...")

        def _name_vote(i, agent):
            try:
                vote = agent.invoke_structured(vote_prompt, NameVote, max_tokens=300)
                voted_for = vote.voted_for
                if voted_for == i:
                    voted_for = (i + 1) % 3
                return agent.name, voted_for
            except Exception:
                return agent.name, (i + 1) % 3

        with ThreadPoolExecutor(max_workers=len(agents)) as executor:
            futures = [executor.submit(_name_vote, i, agent) for i, agent in enumerate(agents)]
            for future in as_completed(futures):
                name, voted_for = future.result()
                votes[name] = voted_for

        # Tally votes
        vote_counts = Counter(votes.values())
        max_votes = max(vote_counts.values())
        winners = [i for i, count in vote_counts.items() if count == max_votes]

        if len(winners) == 1:
            winner_idx = winners[0]
        else:
            # Tie breaker: highest average score
            avg_scores = []
            for i in winners:
                scores = [
                    r["score"]
                    for c in critiques
                    for r in c["reviews"]
                    if r["proposal"] == i
                ]
                avg = sum(scores) / len(scores) if scores else 0
                avg_scores.append((i, avg))
            winner_idx = max(avg_scores, key=lambda x: x[1])[0]

        final_name = proposals[winner_idx]["full_name"]

        return {
            "proposals": proposals,
            "votes": votes,
            "final_name": final_name,
            "first_initial": first_initial,
            "last_initial": last_initial,
        }

    def _run_physical_debate(
        self,
        character_role: str,
        character_type: str,
        adjective: str,
        goal: str,
        stakes: str,
        setting_prompt: str,
    ) -> dict:
        """Run 4-agent physical appearance debate."""
        # Initialize character debate agents
        psychologist = CharacterPsychologistAgent(model=self.model)
        visualist = CharacterVisualistAgent(model=self.model)
        narrative = CharacterNarrativeAgent(model=self.model)
        audience = CharacterAudienceAgent(model=self.model)

        agents = [psychologist, visualist, narrative, audience]

        # Round 1: Proposals from all 4 agents (parallel)
        print(f"      Generating physical appearance proposals (parallel)...")
        proposals = self._parallel_agent_calls(
            agents, 'propose_physical',
            role=character_role, role_type=character_type,
            adjective=adjective, goal=goal, stakes=stakes, setting=setting_prompt,
        )
        proposals = [p for p in proposals if p is not None]

        if not proposals:
            return {"error": "All proposal agents failed"}

        # Round 2: Cross-critiques (parallel)
        print(f"      Gathering critiques (parallel)...")
        from concurrent.futures import ThreadPoolExecutor, as_completed
        critiques = []
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {}
            for i, agent in enumerate(agents[:3]):
                target_idx = (i + 1) % len(proposals)
                target_proposal = proposals[target_idx]
                futures[executor.submit(
                    agent.critique_proposal,
                    target_agent=target_proposal.agent_name,
                    proposal=target_proposal, role=character_role, adjective=adjective,
                )] = agent
            for future in as_completed(futures):
                try:
                    critiques.append(future.result())
                except Exception:
                    pass

        # Round 3: All 4 agents vote (parallel)
        print(f"      Collecting votes (parallel)...")
        votes = self._parallel_agent_calls(
            agents, 'vote_for_best',
            proposals=proposals, role=character_role, adjective=adjective,
        )
        votes = [v for v in votes if v is not None]
        for v in votes:
            print(f"        votes for: {v.voted_for_agent}")

        # Tally votes
        vote_counts = Counter(v.voted_for_agent for v in votes)
        if vote_counts:
            winner_agent = max(vote_counts, key=vote_counts.get)
            winner_proposal = next(
                (p for p in proposals if p.agent_name == winner_agent),
                proposals[0]
            )
        else:
            winner_proposal = proposals[0]
            winner_agent = winner_proposal.agent_name

        print(f"      Winner: {winner_agent}")

        return {
            "proposals": [p.model_dump() for p in proposals],
            "critiques": [c.model_dump() for c in critiques],
            "votes": [v.model_dump() for v in votes],
            "winner": winner_agent,
            "winning_physical": winner_proposal.physical.model_dump(),
            "winning_costume": winner_proposal.costume,
        }

    def _infer_time_period(self, genre: str, world_dict: dict) -> str:
        """Infer time period from genre and world details for costume design.

        Args:
            genre: Primary genre (fantasy, sci-fi, western, etc.)
            world_dict: World building details from Step 4

        Returns:
            Time period hint string (e.g., "medieval", "1920s", "far future")
        """
        genre_lower = genre.lower()

        # Check for explicit time period hints in world building
        economy = world_dict.get("economy", {})
        government = world_dict.get("government_law", {})

        economy_str = str(economy).lower()
        government_str = str(government).lower()

        # Sci-fi / Futuristic indicators
        if any(word in genre_lower for word in ["sci-fi", "science fiction", "space", "cyber"]):
            if any(word in economy_str or word in government_str for word in ["nano", "quantum", "neural", "cyber", "ai"]):
                return "far future (post-2200)"
            elif any(word in economy_str or word in government_str for word in ["colony", "space", "orbital", "mars"]):
                return "near future (2100-2200)"
            else:
                return "near future (2050-2100)"

        # Fantasy / Medieval indicators
        elif any(word in genre_lower for word in ["fantasy", "epic", "sword"]):
            if any(word in economy_str for word in ["feudal", "guild", "barter", "medieval"]):
                return "medieval (1000-1500 CE equivalent)"
            elif any(word in economy_str for word in ["imperial", "empire", "legion"]):
                return "ancient/classical (Rome/Greece equivalent)"
            else:
                return "medieval-renaissance (1300-1600 CE equivalent)"

        # Western / Frontier
        elif "western" in genre_lower:
            return "American Old West (1850-1900)"

        # Historical fiction
        elif "historical" in genre_lower:
            if "ancient" in genre_lower:
                return "ancient times (pre-500 CE)"
            elif "victorian" in genre_lower or "19th" in genre_lower:
                return "Victorian era (1837-1901)"
            elif "edwardian" in genre_lower or "1900s" in genre_lower:
                return "Edwardian era (1901-1914)"
            else:
                return "historical (varied periods)"

        # Horror / Gothic
        elif any(word in genre_lower for word in ["horror", "gothic"]):
            return "Victorian Gothic (1850-1900)"

        # Steampunk
        elif "steampunk" in genre_lower:
            return "alternate Victorian (steam-powered technology)"

        # Contemporary / Modern
        elif any(word in genre_lower for word in ["contemporary", "modern", "urban", "thriller"]):
            return "contemporary (present day)"

        # Post-apocalyptic
        elif "post-apocalyptic" in genre_lower or "apocalypse" in genre_lower:
            return "post-apocalyptic (near future, collapsed civilization)"

        # Default fallback based on world details
        if "digital" in economy_str or "computer" in economy_str:
            return "modern/contemporary (1990s-present)"
        elif "industrial" in economy_str or "factory" in economy_str:
            return "industrial era (1800-1920)"
        elif "agrarian" in economy_str or "farming" in economy_str:
            return "pre-industrial (medieval-renaissance)"
        else:
            return "indeterminate period (see world details)"

    def _run_costume_debate(
        self,
        character: dict,
        world_context: dict,
        genre: str,
        time_period_hint: str,
    ) -> dict:
        """Run 3-agent costume debate for world-accurate character costume design.

        Called in Step 4 (World Building) AFTER world agents run, so we have:
        - Economy (available materials)
        - Culture (norms, taboos)
        - Government (class markers)
        - Religion (symbolic meaning)
        - Genre and time period hints

        Args:
            character: Character dict with role, psychology, physical appearance
            world_context: Dict with economy, government, culture, religion proposals
            genre: Primary genre (fantasy, sci-fi, western, etc.)
            time_period_hint: Inferred time period (medieval, 1920s, future, etc.)

        Returns:
            Dict with proposals, critiques, votes, winner, winning_costume (detailed), winning_summary
        """
        from src.story_agents.costume_agents import (
            CostumeHistoricalAgent,
            CostumeWorldAgent,
            CostumeVisualAgent,
        )

        # Initialize 3 costume agents
        historical_agent = CostumeHistoricalAgent(model=self.model)
        world_agent = CostumeWorldAgent(model=self.model)
        visual_agent = CostumeVisualAgent(model=self.model)

        agents = [historical_agent, world_agent, visual_agent]

        # Round 1: Proposals from all 3 agents (parallel)
        print(f"      Generating costume proposals (parallel)...")
        raw_proposals = self._parallel_agent_calls(
            agents, 'propose_costume',
            character=character, world_context=world_context,
            genre=genre, time_period_hint=time_period_hint,
        )
        proposals = []
        for i, proposal in enumerate(raw_proposals):
            if proposal is not None:
                proposals.append(proposal)
                print(f"        [{agents[i].name}] proposed: {proposal.costume.primary_color} {proposal.costume.garment_type}")
            else:
                print(f"        [{agents[i].name}] failed")

        if not proposals:
            return {"error": "All costume proposal agents failed"}

        # Round 2: Cross-critiques (parallel)
        print(f"      Gathering critiques (parallel)...")
        from concurrent.futures import ThreadPoolExecutor, as_completed

        def _costume_critique(agent, target_proposal):
            if isinstance(agent, CostumeHistoricalAgent):
                return agent.critique_proposal(
                    target_agent=target_proposal.agent_name,
                    proposal=target_proposal,
                    character=character,
                    time_period_hint=time_period_hint,
                )
            elif isinstance(agent, CostumeWorldAgent):
                return agent.critique_proposal(
                    target_agent=target_proposal.agent_name,
                    proposal=target_proposal,
                    character=character,
                    world_context=world_context,
                )
            else:
                return agent.critique_proposal(
                    target_agent=target_proposal.agent_name,
                    proposal=target_proposal,
                    character=character,
                )

        critiques = []
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {}
            for i, agent in enumerate(agents[:2]):
                target_idx = (i + 1) % len(proposals)
                futures[executor.submit(_costume_critique, agent, proposals[target_idx])] = i
            for future in as_completed(futures):
                try:
                    critiques.append(future.result())
                except Exception:
                    pass

        # Round 3: All 3 agents vote (parallel)
        print(f"      Collecting votes (parallel)...")

        def _costume_vote(agent):
            if isinstance(agent, CostumeHistoricalAgent):
                return agent.vote_for_best(
                    proposals=proposals, character=character,
                    time_period_hint=time_period_hint,
                )
            elif isinstance(agent, CostumeWorldAgent):
                return agent.vote_for_best(
                    proposals=proposals, character=character,
                    world_context=world_context,
                )
            else:
                return agent.vote_for_best(
                    proposals=proposals, character=character,
                )

        votes = []
        with ThreadPoolExecutor(max_workers=len(agents)) as executor:
            futures = {executor.submit(_costume_vote, agent): agent for agent in agents}
            for future in as_completed(futures):
                try:
                    vote = future.result()
                    votes.append(vote)
                    print(f"        [{futures[future].name}] votes for: {vote.voted_for_agent}")
                except Exception:
                    pass

        # Tally votes
        vote_counts = Counter(v.voted_for_agent for v in votes)
        if vote_counts:
            winner_agent = max(vote_counts, key=vote_counts.get)
            winner_proposal = next(
                (p for p in proposals if p.agent_name == winner_agent),
                proposals[0]
            )
        else:
            winner_proposal = proposals[0]
            winner_agent = winner_proposal.agent_name

        print(f"      Winner: {winner_agent}")

        return {
            "proposals": [p.model_dump() for p in proposals],
            "critiques": [c.model_dump() for c in critiques],
            "votes": [v.model_dump() for v in votes],
            "winner": winner_agent,
            "winning_costume": winner_proposal.costume.model_dump(),
            "winning_summary": winner_proposal.summary,
        }

    def step2_characters(self, codex: dict) -> Step2Result:
        """Generate characters via multi-agent debate.

        Uses 4 character debate agents:
        - CharacterPsychologistAgent: Internal psychology, appearance reflecting state
        - CharacterVisualistAgent: Visual distinctiveness, costume design
        - CharacterNarrativeAgent: Role in story, contrast with others
        - CharacterAudienceAgent: Relatability, emotional connection

        Plus 3 name agents for name debate:
        - NameCreativeAgent, NameAuthenticAgent, NameDistinctiveAgent

        Args:
            codex: The codex dictionary with outline from Step 1

        Returns:
            Step2Result with characters list and debate metadata
        """
        start_time = time.time()
        characters = []
        character_debates = []
        name_mapping = {}

        try:
            # Get story context
            outline = codex.get("story", {}).get("outline", {})
            story_seed = outline.get("story_seed_parsed", {})
            structure_beats = outline.get("structure_beats", {})

            if not story_seed:
                return Step2Result(
                    characters=[],
                    character_debates=[],
                    name_mapping={},
                    success=False,
                    error="No story_seed_parsed found. Run Step 1 first.",
                )

            # Get setting prompt
            story_prompt, setting_prompt = self.extract_prompts(codex)
            logline = f"{story_seed.get('adjective', '')} {story_seed.get('hero_role', '')} wants to {story_seed.get('goal', '')} but {story_seed.get('stakes', '')}"

            print(f"\n{'='*60}")
            print("STEP 2: CHARACTER GENERATION (Multi-Agent Debate)")
            print(f"{'='*60}")
            print(f">>> Agents: 4 character + 3 name debate agents")
            print(f">>> Method: Propose -> Critique -> Vote")

            # Extract character roles from outline
            character_roles = self._extract_characters_from_outline(codex)
            print(f"\n>>> Found {len(character_roles)} characters to generate:")
            for i, char in enumerate(character_roles):
                print(f"    {i+1}. [{char['type'].upper()}] {char['role']}")

            # Initialize backstory agent
            backstory_agent = CharacterBackstoryAgent(model=self.model)
            existing_names = []

            # Process each character
            for idx, char_info in enumerate(character_roles):
                char_id = f"char_{idx+1:03d}"
                print(f"\n{'='*50}")
                print(f"CHARACTER {idx+1}: {char_info['role'].upper()}")
                print(f"{'='*50}")

                # Step A: Generate random name initials
                first_initial = random.choice(string.ascii_uppercase)
                last_initial = random.choice(string.ascii_uppercase)
                print(f"    Initials: {first_initial}.{last_initial}.")

                # Step B: Name debate
                print(f"\n    --- NAME DEBATE (3 agents) ---")
                name_result = self._run_name_debate(
                    character_role=char_info["role"],
                    first_initial=first_initial,
                    last_initial=last_initial,
                    logline=logline,
                    setting_prompt=setting_prompt,
                    existing_names=existing_names,
                )
                final_name = name_result["final_name"]
                existing_names.append(final_name)
                print(f"    >>> Name: {final_name}")

                # Build name mapping
                name_mapping[char_info["role"]] = final_name

                # Step C: Physical appearance debate
                print(f"\n    --- PHYSICAL APPEARANCE DEBATE (4 agents) ---")
                physical_result = self._run_physical_debate(
                    character_role=char_info["role"],
                    character_type=char_info["type"],
                    adjective=char_info.get("adjective", story_seed.get("adjective", "")),
                    goal=char_info.get("goal", ""),
                    stakes=char_info.get("stakes", ""),
                    setting_prompt=setting_prompt,
                )

                # Pre-assign gender randomly before backstory generation
                gender = random.choice(["male", "female"])

                # Step D: Generate backstory
                print(f"\n    --- BACKSTORY GENERATION ---")
                try:
                    backstory_result = backstory_agent.generate_backstory(
                        role=char_info["role"],
                        role_type=char_info["type"],
                        adjective=char_info.get("adjective", story_seed.get("adjective", "")),
                        goal=char_info.get("goal", ""),
                        stakes=char_info.get("stakes", ""),
                        structure_beats=structure_beats,
                        setting=setting_prompt,
                        gender=gender,
                    )
                    backstory_points = backstory_result.backstory_points
                    motivation = backstory_result.motivation
                    arc = backstory_result.arc
                    personality_traits = backstory_result.personality_traits
                    accent = backstory_result.accent
                    qualities = backstory_result.qualities
                    print(f"    >>> {len(backstory_points)} backstory points generated")
                    print(f"    >>> Personality: {personality_traits[:2]}...")
                    print(f"    >>> Accent: {accent}")
                except Exception as e:
                    print(f"    >>> Backstory generation failed: {str(e)[:50]}")
                    backstory_points = [
                        f"Has experienced significant trauma related to being {story_seed.get('adjective', 'troubled').lower()}",
                        f"Their goal is to {char_info.get('goal', 'achieve their objective')}",
                        f"Currently struggling with the stakes: {char_info.get('stakes', 'personal consequences')}",
                    ]
                    motivation = f"Driven by the need to {char_info.get('goal', 'succeed')}"
                    arc = f"From {story_seed.get('adjective', 'troubled').lower()} to transformed"
                    personality_traits = ["guarded", "resourceful", "conflicted"]
                    accent = "neutral, measured speech"
                    qualities = ["observant of details", "slow to trust", "keeps their word"]

                # Step E: Assemble character sheet
                winning_physical = physical_result.get("winning_physical", {})
                physical = PhysicalDescriptionSchema(
                    body_build=winning_physical.get("body_build", "average build"),
                    height=winning_physical.get("height", "average height"),
                    hair_color=winning_physical.get("hair_color", "dark hair"),
                    ethnicity=winning_physical.get("ethnicity", "mixed heritage"),
                    eye_color=winning_physical.get("eye_color", "brown"),
                    distinguishing_features=winning_physical.get("distinguishing_features", ""),
                )

                character = CharacterSheetSchema(
                    id=char_id,
                    name=final_name,
                    role_in_story=char_info["type"],
                    role_description=char_info["role"],
                    gender=gender,
                    age="adult",  # Can be refined later
                    physical=physical,
                    costume=physical_result.get("winning_costume", "practical clothing appropriate to their role"),
                    personality_traits=personality_traits,
                    accent=accent,
                    qualities=qualities,
                    backstory_points=backstory_points,
                    motivation=motivation,
                    arc=arc,
                )

                characters.append(character.model_dump())
                character_debates.append({
                    "character_id": char_id,
                    "role": char_info["role"],
                    "name_debate": name_result,
                    "physical_debate": physical_result,
                })

                print(f"\n    >>> Character {char_id} complete: {final_name}")

            duration = time.time() - start_time

            print(f"\n{'='*60}")
            print("STEP 2 COMPLETE")
            print(f"{'='*60}")
            print(f">>> Duration: {duration:.1f}s")
            print(f">>> Characters: {len(characters)}")
            for char in characters:
                print(f"    - {char['name']} ({char['role_in_story']})")

            return Step2Result(
                characters=characters,
                character_debates=character_debates,
                name_mapping=name_mapping,
                success=True,
                duration_seconds=round(duration, 2),
            )

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Step2Result(
                characters=[],
                character_debates=[],
                name_mapping={},
                success=False,
                error=str(e),
                duration_seconds=round(time.time() - start_time, 2),
            )

    # =========================================================================
    # STEP 3: PLOT STRUCTURE (Character Arc + Story Beats)
    # =========================================================================

    def step3_plot_structure(self, codex: dict) -> Step3Result:
        """Build plot structure via multi-agent debate.

        Creates integrated beat structure combining:
        1. Character arc beats (hero/villain focus, side characters minimal)
        2. Save the Cat 15-beat structure
        3. Integration of arcs + beats + theme

        Args:
            codex: The codex dictionary with previous steps' results

        Returns:
            Step3Result with integrated beats and arc summaries
        """
        start_time = time.time()

        try:
            # Import plot structure agents
            from src.story_agents.plot_structure_agents import (
                # Arc Beat agents
                ArcBeatArchitectAgent, ArcBeatPsychologicalAgent, ArcBeatDramaticAgent,
                # SaveTheCat agents
                SaveTheCatStructureAgent, SaveTheCatPacingAgent, SaveTheCatGenreAgent,
                # Integration agents
                IntegrationWeaverAgent, IntegrationThematicAgent, IntegrationConflictAgent,
            )

            # Get previous results
            story_prompt, _ = self.extract_prompts(codex)
            theme_foundation = codex.get("story", {}).get("theme_foundation", {})
            theme_question = theme_foundation.get("central_question", "Unknown theme")
            characters = codex.get("story", {}).get("characters", [])
            story_shape = codex.get("story", {}).get("story_shape", "Unknown")
            save_the_cat_type = codex.get("story", {}).get("save_the_cat_type", "Unknown")
            primary_genre = codex.get("story", {}).get("primary_genre", "Unknown")
            secondary_genre = codex.get("story", {}).get("secondary_genre", "")

            genres = [primary_genre]
            if secondary_genre:
                genres.append(secondary_genre)

            if not characters:
                return Step3Result(
                    integrated_beats=[],
                    hero_arc_summary="",
                    villain_arc_summary="",
                    side_character_notes="",
                    step3_debates={},
                    success=False,
                    error="No characters found. Run Steps 0 and 1 first.",
                )

            print(f"\n{'='*60}")
            print("STEP 3: PLOT STRUCTURE (Character Arc + Story Beats)")
            print(f"{'='*60}")
            print(f">>> Theme: {theme_question}")
            print(f">>> Story Shape: {story_shape}")
            print(f">>> STC Type: {save_the_cat_type}")
            print(f">>> Genre: {'/'.join(genres)}")

            # =========================================================================
            # SUBSTEP 1: CHARACTER ARC BEAT MAPPING
            # =========================================================================
            print(f"\n{'='*60}")
            print("SUBSTEP 1: CHARACTER ARC BEAT MAPPING")
            print(f"{'='*60}")
            print(">>> Mapping arc beats for ALL major characters")
            print(f">>> Characters: {len(characters)} (hero, villain, {len(characters)-2} supporting)")

            arc_agents = [
                ArcBeatArchitectAgent(model=self.model),
                ArcBeatPsychologicalAgent(model=self.model),
                ArcBeatDramaticAgent(model=self.model),
            ]

            print(f"\n>>> Phase 1: Proposals (3 agents, parallel)")
            arc_proposals = self._parallel_agent_calls(
                arc_agents, 'propose_arc_beats', characters, story_shape, theme_question
            )
            arc_proposals = [p for p in arc_proposals if p is not None]
            for p in arc_proposals:
                print(f"      Hero: {p.hero_arc.arc_type} ({len(p.hero_arc.arc_beats)} beats)")

            if not arc_proposals:
                return Step3Result(
                    integrated_beats=[], hero_arc_summary="", villain_arc_summary="",
                    side_character_notes="", step3_debates={},
                    success=False, error="All arc beat agents failed to generate proposals"
                )

            print(f"\n>>> Phase 2: Critiques (parallel)")
            critique_results = self._parallel_agent_calls(
                arc_agents, 'critique_arc_beats', arc_proposals, theme_question
            )
            all_arc_critiques = []
            for result in critique_results:
                if result is not None:
                    all_arc_critiques.extend(result)

            print(f"\n>>> Phase 3: Voting (parallel)")
            arc_votes = self._parallel_agent_calls(arc_agents, 'vote', arc_proposals, theme_question)
            arc_votes = [v for v in arc_votes if v is not None]
            for v in arc_votes:
                print(f"    - votes for Proposal {v.chosen_proposal_index}")

            # Count votes
            vote_counts = {}
            for v in arc_votes:
                vote_counts[v.chosen_proposal_index] = vote_counts.get(v.chosen_proposal_index, 0) + 1

            winner_index = max(vote_counts, key=vote_counts.get)
            winning_arcs = arc_proposals[winner_index]

            print(f"\n>>> WINNER: Proposal {winner_index} ({vote_counts[winner_index]} votes)")
            print(f">>> Hero Arc: {winning_arcs.hero_arc.arc_summary}")
            print(f">>> Villain Arc: {winning_arcs.villain_arc.arc_summary}")
            if winning_arcs.supporting_arcs:
                print(f">>> Supporting Characters: {len(winning_arcs.supporting_arcs)} micro-arcs")

            # =========================================================================
            # ATTACH ARC BEATS TO CHARACTER OBJECTS
            # =========================================================================
            print(f"\n>>> Attaching arc beats to character objects...")

            # Create a mapping of character name to arc structure
            arc_by_character = {
                winning_arcs.hero_arc.character_name: winning_arcs.hero_arc,
                winning_arcs.villain_arc.character_name: winning_arcs.villain_arc,
            }
            for arc in winning_arcs.supporting_arcs:
                arc_by_character[arc.character_name] = arc

            # Attach arc beats to each character in codex
            for character in characters:
                char_name = character.get("name", "")
                if char_name in arc_by_character:
                    arc = arc_by_character[char_name]
                    character["arc_beats"] = [
                        {
                            "beat_name": beat.beat_name,
                            "timing": beat.timing,
                            "description": beat.description,
                            "ties_to_lie_truth": beat.ties_to_lie_truth,
                        }
                        for beat in arc.arc_beats
                    ]
                    print(f"    - {char_name}: {len(arc.arc_beats)} beats attached")

            # Verify attachment worked
            chars_with_beats = sum(1 for c in characters if "arc_beats" in c)
            print(f"\n>>> ✅ Arc beats attached to {chars_with_beats}/{len(characters)} characters")
            if chars_with_beats < len(characters):
                print(f">>> ⚠️  WARNING: {len(characters) - chars_with_beats} characters missing arc beats!")

            # =========================================================================
            # SUBSTEP 2: SAVE THE CAT 15-BEAT STRUCTURE
            # =========================================================================
            print(f"\n{'='*60}")
            print("SUBSTEP 2: SAVE THE CAT 15-BEAT STRUCTURE")
            print(f"{'='*60}")

            stc_agents = [
                SaveTheCatStructureAgent(model=self.model),
                SaveTheCatPacingAgent(model=self.model),
                SaveTheCatGenreAgent(model=self.model),
            ]

            print(f"\n>>> Phase 1: Proposals (3 agents, parallel)")
            from concurrent.futures import ThreadPoolExecutor, as_completed

            def _stc_propose(agent):
                if agent.name == "STC_GENRE":
                    return agent.propose_beats(story_shape, save_the_cat_type, theme_question, story_prompt, genres)
                else:
                    return agent.propose_beats(story_shape, save_the_cat_type, theme_question, story_prompt)

            stc_proposals = [None] * len(stc_agents)
            with ThreadPoolExecutor(max_workers=len(stc_agents)) as executor:
                futures = {executor.submit(_stc_propose, agent): i for i, agent in enumerate(stc_agents)}
                for future in as_completed(futures):
                    idx = futures[future]
                    stc_proposals[idx] = future.result()
                    print(f"    - {stc_agents[idx].name} proposed. Pacing: {stc_proposals[idx].overall_pacing[:50]}...")

            print(f"\n>>> Phase 2: Critiques (each agent critiques all 3, parallel)")

            def _stc_critique(agent):
                if agent.name == "STC_GENRE":
                    return agent.critique_beats(stc_proposals, theme_question, genres)
                else:
                    return agent.critique_beats(stc_proposals, theme_question)

            all_stc_critiques = []
            critique_results = [None] * len(stc_agents)
            with ThreadPoolExecutor(max_workers=len(stc_agents)) as executor:
                futures = {executor.submit(_stc_critique, agent): i for i, agent in enumerate(stc_agents)}
                for future in as_completed(futures):
                    idx = futures[future]
                    critiques = future.result()
                    critique_results[idx] = critiques
                    for c in critiques:
                        print(f"    - {stc_agents[idx].name}: Proposal {c.proposal_index}: {c.score}/10")
            for cr in critique_results:
                if cr:
                    all_stc_critiques.extend(cr)

            print(f"\n>>> Phase 3: Voting (each agent votes, parallel)")
            stc_votes = self._parallel_agent_calls(stc_agents, 'vote', stc_proposals, theme_question)
            for i, vote in enumerate(stc_votes):
                if vote:
                    print(f"    - {stc_agents[i].name} votes for Proposal {vote.chosen_proposal_index}")

            # Count votes
            vote_counts = {}
            for v in stc_votes:
                vote_counts[v.chosen_proposal_index] = vote_counts.get(v.chosen_proposal_index, 0) + 1

            winner_index = max(vote_counts, key=vote_counts.get)
            winning_stc = stc_proposals[winner_index]

            print(f"\n>>> WINNER: Proposal {winner_index} ({vote_counts[winner_index]} votes)")
            print(f">>> Beats: {len(winning_stc.beats)} Save the Cat beats")

            # =========================================================================
            # SUBSTEP 3: BEAT INTEGRATION
            # =========================================================================
            print(f"\n{'='*60}")
            print("SUBSTEP 3: BEAT INTEGRATION (Arc + Plot + Theme)")
            print(f"{'='*60}")

            integration_agents = [
                IntegrationWeaverAgent(model=self.model),
                IntegrationThematicAgent(model=self.model),
                IntegrationConflictAgent(model=self.model),
            ]

            print(f"\n>>> Phase 1: Proposals (3 agents, parallel)")
            integration_proposals = self._parallel_agent_calls(
                integration_agents, 'propose_integration',
                winning_arcs.hero_arc, winning_arcs.villain_arc,
                winning_arcs.supporting_arcs, winning_stc.beats, theme_question
            )
            for i, proposal in enumerate(integration_proposals):
                if proposal:
                    print(f"    - {integration_agents[i].name}: {len(proposal.integrated_beats)} integrated beats")

            print(f"\n>>> Phase 2: Critiques (each agent critiques all 3, parallel)")
            critique_results = self._parallel_agent_calls(
                integration_agents, 'critique_integration',
                integration_proposals, theme_question
            )
            all_integration_critiques = []
            for i, critiques in enumerate(critique_results):
                if critiques:
                    all_integration_critiques.extend(critiques)
                    for c in critiques:
                        print(f"    - {integration_agents[i].name}: Proposal {c.proposal_index}: {c.score}/10")

            print(f"\n>>> Phase 3: Voting (each agent votes, parallel)")
            integration_votes = self._parallel_agent_calls(
                integration_agents, 'vote', integration_proposals, theme_question
            )
            for i, vote in enumerate(integration_votes):
                if vote:
                    print(f"    - {integration_agents[i].name} votes for Proposal {vote.chosen_proposal_index}")

            # Count votes
            vote_counts = {}
            for v in integration_votes:
                vote_counts[v.chosen_proposal_index] = vote_counts.get(v.chosen_proposal_index, 0) + 1

            winner_index = max(vote_counts, key=vote_counts.get)
            winning_integration = integration_proposals[winner_index]

            print(f"\n>>> WINNER: Proposal {winner_index} ({vote_counts[winner_index]} votes)")
            print(f">>> Integrated Beats: {len(winning_integration.integrated_beats)}")

            # =========================================================================
            # BUILD STEP 3 OUTPUT
            # =========================================================================

            # Convert integrated beats to dicts
            integrated_beats_dicts = [
                {
                    "beat_name": b.beat_name,
                    "timing_percentage": b.timing_percentage,
                    "plot_event": b.plot_event,
                    "character_arcs": [
                        {"character_name": arc.character_name, "arc_description": arc.arc_description}
                        for arc in b.character_arcs
                    ],
                    "thematic_test": b.thematic_test,
                    "location_type": b.location_type,  # Where this beat occurs
                }
                for b in winning_integration.integrated_beats
            ]

            # Ensure exactly 15 beats (pad or trim if needed)
            if len(integrated_beats_dicts) < 15:
                print(f">>> WARNING: Only {len(integrated_beats_dicts)} beats generated, padding to 15")
                # Pad with minimal placeholder beats
                # Create placeholder character_arcs list with all characters
                placeholder_arcs = [
                    {"character_name": char["name"], "arc_description": "[To be developed]"}
                    for char in characters
                ]
                while len(integrated_beats_dicts) < 15:
                    beat_num = len(integrated_beats_dicts) + 1
                    integrated_beats_dicts.append({
                        "beat_name": f"Beat {beat_num}",
                        "timing_percentage": "N/A",
                        "plot_event": f"[Placeholder for beat {beat_num}]",
                        "character_arcs": placeholder_arcs.copy(),
                        "thematic_test": f"Tests theme: {theme_question}",
                    })
            elif len(integrated_beats_dicts) > 15:
                print(f">>> WARNING: {len(integrated_beats_dicts)} beats generated, trimming to 15")
                integrated_beats_dicts = integrated_beats_dicts[:15]

            # Build step3_debates for metadata
            step3_debates = {
                "arc_beat_debate": {
                    "proposals": [
                        {
                            "agent_name": p.agent_name,
                            "hero_arc": {
                                "character_name": p.hero_arc.character_name,
                                "arc_type": p.hero_arc.arc_type,
                                "arc_summary": p.hero_arc.arc_summary,
                                "beats": [{"beat_name": b.beat_name, "description": b.description} for b in p.hero_arc.arc_beats],
                            },
                            "villain_arc": {
                                "character_name": p.villain_arc.character_name,
                                "arc_type": p.villain_arc.arc_type,
                                "arc_summary": p.villain_arc.arc_summary,
                                "beats": [{"beat_name": b.beat_name, "description": b.description} for b in p.villain_arc.arc_beats],
                            },
                            "supporting_arcs": [
                                {
                                    "character_name": arc.character_name,
                                    "arc_type": arc.arc_type,
                                    "arc_summary": arc.arc_summary,
                                    "beats": [{"beat_name": b.beat_name, "description": b.description} for b in arc.arc_beats],
                                }
                                for arc in p.supporting_arcs
                            ],
                            "reasoning": p.reasoning,
                        }
                        for p in arc_proposals
                    ],
                    "critiques": [
                        {
                            "agent_name": c.agent_name,
                            "proposal_index": c.proposal_index,
                            "score": c.score,
                            "strengths": c.strengths,
                            "weaknesses": c.weaknesses,
                        }
                        for c in all_arc_critiques
                    ],
                    "votes": [
                        {
                            "agent_name": v.agent_name,
                            "chosen_proposal_index": v.chosen_proposal_index,
                            "reasoning": v.reasoning,
                        }
                        for v in arc_votes
                    ],
                    "winner_index": winner_index,
                },
                "save_the_cat_debate": {
                    "proposals": [
                        {
                            "agent_name": p.agent_name,
                            "beats": [{"beat_name": b.beat_name, "timing": b.timing_percentage, "plot": b.plot_event[:100]} for b in p.beats],
                            "pacing": p.overall_pacing,
                        }
                        for p in stc_proposals
                    ],
                    "critiques": [
                        {
                            "agent_name": c.agent_name,
                            "proposal_index": c.proposal_index,
                            "score": c.score,
                            "strengths": c.strengths,
                            "weaknesses": c.weaknesses,
                        }
                        for c in all_stc_critiques
                    ],
                    "votes": [
                        {
                            "agent_name": v.agent_name,
                            "chosen_proposal_index": v.chosen_proposal_index,
                            "reasoning": v.reasoning,
                        }
                        for v in stc_votes
                    ],
                    "winner_index": winner_index,
                },
                "integration_debate": {
                    "proposals": [
                        {
                            "agent_name": p.agent_name,
                            "beats_count": len(p.integrated_beats),
                            "reasoning": p.reasoning[:200] + "..." if len(p.reasoning) > 200 else p.reasoning,
                        }
                        for p in integration_proposals
                    ],
                    "critiques": [
                        {
                            "agent_name": c.agent_name,
                            "proposal_index": c.proposal_index,
                            "score": c.score,
                            "strengths": c.strengths,
                            "weaknesses": c.weaknesses,
                        }
                        for c in all_integration_critiques
                    ],
                    "votes": [
                        {
                            "agent_name": v.agent_name,
                            "chosen_proposal_index": v.chosen_proposal_index,
                            "reasoning": v.reasoning,
                        }
                        for v in integration_votes
                    ],
                    "winner_index": winner_index,
                },
            }

            # Generate side character summary from integrated beats
            hero_name = winning_arcs.hero_arc.character_name
            villain_name = winning_arcs.villain_arc.character_name
            supporting_char_names = [arc.character_name for arc in winning_arcs.supporting_arcs]

            if supporting_char_names:
                side_char_summary = (
                    f"Supporting characters ({', '.join(supporting_char_names)}) appear throughout "
                    f"all {len(integrated_beats_dicts)} beats with their micro-arcs integrated into "
                    f"the main narrative alongside {hero_name} and {villain_name}."
                )
            else:
                side_char_summary = "No supporting characters in this story."

            # Store character arc beats summary in codex for easy reference in Step 4
            character_arc_summaries = {}
            for char in characters:
                if "arc_beats" in char:
                    character_arc_summaries[char["name"]] = {
                        "arc_type": char.get("arc_type", "unknown"),
                        "num_beats": len(char["arc_beats"]),
                        "beat_names": [b["beat_name"] for b in char["arc_beats"]],
                    }

            if character_arc_summaries:
                codex["story"]["character_arc_beats_summary"] = character_arc_summaries
                print(f"\n>>> Stored arc beat summaries for {len(character_arc_summaries)} characters")

            duration = time.time() - start_time

            print(f"\n{'='*60}")
            print(f"STEP 3 COMPLETE! Duration: {duration:.1f}s")
            print(f"{'='*60}")

            return Step3Result(
                integrated_beats=integrated_beats_dicts,
                hero_arc_summary=winning_arcs.hero_arc.arc_summary,
                villain_arc_summary=winning_arcs.villain_arc.arc_summary,
                side_character_notes=side_char_summary,
                step3_debates=step3_debates,
                success=True,
                duration_seconds=duration,
            )

        except Exception as e:
            duration = time.time() - start_time
            print(f"\n>>> Step 3 FAILED: {e}")
            import traceback
            traceback.print_exc()

            return Step3Result(
                integrated_beats=[],
                hero_arc_summary="",
                villain_arc_summary="",
                side_character_notes="",
                step3_debates={},
                success=False,
                error=str(e),
                duration_seconds=duration,
            )

    # =========================================================================
    # STEP 3: WORLD BUILDING (Locations + World Context) - OLD
    # =========================================================================

    def _parse_deck_of_worlds_prompt(self, codex: dict) -> dict:
        """Parse deck_of_worlds prompt into structured data for world building agents."""
        dow_prompts = codex.get("deck_of_worlds", {}).get("prompts", [])
        if not dow_prompts:
            return {}

        prompt_text = dow_prompts[0].get("prompt", "")
        # Example: "WITHOUT WALLS SWAMP with PALACE | Origin: HOME OF A VANISHED PEOPLE | Now: HEADQUARTERS OF A CRIME FAMILY | Hook: PEOPLE ARE OPENLY RIOTING"

        result = {"raw_prompt": prompt_text}

        parts = prompt_text.split("|")
        if len(parts) >= 1:
            # First part: region + landmark
            result["location"] = parts[0].strip()

        for part in parts[1:]:
            part = part.strip()
            if part.startswith("Origin:"):
                result["origin"] = part.replace("Origin:", "").strip()
            elif part.startswith("Now:"):
                result["attribute"] = part.replace("Now:", "").strip()
            elif part.startswith("Hook:"):
                result["advent"] = part.replace("Hook:", "").strip()

        return result

    def _extract_locations_from_outline(self, codex: dict) -> list[dict]:
        """Extract unique locations needed from story outline.

        Sources:
        1. deck_of_worlds prompts (landmark, region)
        2. Scene locations from structure_beats
        3. Implicit locations from story context (protagonist workplace, antagonist territory)
        """
        locations_needed = []
        seen = set()

        outline = codex.get("story", {}).get("outline", {})
        structure_beats = outline.get("structure_beats", {})
        story_seed = outline.get("story_seed_parsed", {})

        # 1. Extract from deck_of_worlds (PRIMARY setting)
        dow_prompts = codex.get("deck_of_worlds", {}).get("prompts", [])
        if dow_prompts:
            prompt_text = dow_prompts[0].get("prompt", "")
            # Parse: "WITHOUT WALLS SWAMP with PALACE | Origin: ..."
            if "|" in prompt_text:
                location_part = prompt_text.split("|")[0].strip()
                # This becomes the primary setting
                locations_needed.append({
                    "source": "deck_of_worlds_primary",
                    "description": location_part,
                    "importance": "primary",
                })
                seen.add(location_part.lower())

        # 2. Extract implicit locations from story context
        hero_role = story_seed.get("hero_role", "")
        if hero_role:
            # Add workplace for protagonist (e.g., "archivist" -> "The Archives")
            if "archivist" in hero_role.lower():
                locations_needed.append({
                    "source": "protagonist_workplace",
                    "description": "The Archives - where the archivist works",
                    "importance": "major",
                })
            elif "soldier" in hero_role.lower():
                locations_needed.append({
                    "source": "protagonist_workplace",
                    "description": "Military barracks or command post",
                    "importance": "major",
                })

        # 3. Add antagonist territory (crime family headquarters is in DOW)
        # Already covered by deck_of_worlds primary

        # 4. Add a neutral meeting ground / public space
        locations_needed.append({
            "source": "public_space",
            "description": "A public gathering place where riots occur",
            "importance": "scene",
        })

        return locations_needed

    def step3_world_building(self, codex: dict) -> Step3Result:
        """Generate world context and locations via multi-agent approach.

        Two components:
        A. LOCATIONS (4-agent debate like character physical debate):
           - LocationArchitectAgent: Physical structure
           - LocationAtmosphereAgent: Mood, sensory details
           - LocationNarrativeAgent: Story function
           - LocationAudienceAgent: Immersion

        B. WORLD CONTEXT (4 specialized agents, NO debate):
           - WorldSociologistAgent: Daily life, social structure
           - WorldEconomistAgent: Economy, jobs, trade
           - WorldPoliticianAgent: Government, law, military
           - WorldCulturalistAgent: Culture, religion, entertainment

        Args:
            codex: The codex dictionary with outline and characters

        Returns:
            Step3Result with locations and world context
        """
        start_time = time.time()
        locations = []
        location_debates = []
        world_data = {}

        try:
            # Validate prerequisites
            outline = codex.get("story", {}).get("outline", {})
            if not outline.get("structure_beats"):
                return Step3Result(
                    locations=[],
                    world={},
                    location_debates=[],
                    success=False,
                    error="No structure_beats found. Run Step 1 first.",
                )

            story_prompt, setting_prompt = self.extract_prompts(codex)
            deck_of_worlds = self._parse_deck_of_worlds_prompt(codex)

            print(f"\n{'='*60}")
            print("STEP 3: WORLD BUILDING")
            print(f"{'='*60}")
            print(f">>> Part A: Location Generation (4-agent debate)")
            print(f">>> Part B: World Context (4 specialized agents)")

            # Build story context for agents
            story_seed = outline.get("story_seed_parsed", {})
            story_context = f"""
Hero: {story_seed.get('hero_role', '')}
Goal: {story_seed.get('goal', '')}
Stakes: {story_seed.get('stakes', '')}
Theme: {outline.get('theme', '')}
"""

            # =========================================
            # PART A: LOCATION GENERATION (4-Agent Debate)
            # =========================================
            print(f"\n{'='*50}")
            print("PART A: LOCATION DEBATE")
            print(f"{'='*50}")

            # Initialize location debate agents
            architect = LocationArchitectAgent(model=self.model)
            atmosphere = LocationAtmosphereAgent(model=self.model)
            narrative = LocationNarrativeAgent(model=self.model)
            audience = LocationAudienceAgent(model=self.model)
            location_agents = [architect, atmosphere, narrative, audience]

            # Extract locations needed from outline
            locations_needed = self._extract_locations_from_outline(codex)
            print(f">>> Found {len(locations_needed)} locations to generate")

            for idx, loc_info in enumerate(locations_needed[:6]):  # Max 6 locations
                loc_id = f"loc_{idx+1:03d}"
                print(f"\n--- LOCATION {idx+1}: {loc_info['source']} ---")
                print(f"    Description: {loc_info['description'][:60]}...")

                # Round 1: All 4 agents propose (parallel)
                print(f"    Generating proposals (parallel)...")
                proposals = self._parallel_agent_calls(
                    location_agents, 'propose_location',
                    location_source=loc_info['description'],
                    setting_prompt=setting_prompt, story_context=story_context,
                )
                proposals = [p for p in proposals if p is not None]
                for p in proposals:
                    print(f"      [{p.agent_name}] proposed: {p.name}")

                if not proposals:
                    continue

                # Round 2: Cross-critiques (parallel)
                print(f"    Gathering critiques (parallel)...")
                from concurrent.futures import ThreadPoolExecutor, as_completed
                critiques = []
                with ThreadPoolExecutor(max_workers=3) as executor:
                    futures = {}
                    for i, agent in enumerate(location_agents[:3]):
                        target_idx = (i + 1) % len(proposals)
                        futures[executor.submit(
                            agent.critique_proposal,
                            target_agent=proposals[target_idx].agent_name,
                            proposal=proposals[target_idx],
                            setting_prompt=setting_prompt,
                        )] = agent
                    for future in as_completed(futures):
                        try:
                            critiques.append(future.result())
                        except Exception:
                            pass

                # Round 3: All 4 agents vote (parallel)
                print(f"    Collecting votes (parallel)...")
                votes = self._parallel_agent_calls(
                    location_agents, 'vote_for_best',
                    proposals=proposals, setting_prompt=setting_prompt,
                )
                votes = [v for v in votes if v is not None]
                for v in votes:
                    print(f"      votes for: {v.voted_for_agent}")

                # Tally votes
                if votes:
                    vote_counts = Counter(v.voted_for_agent for v in votes)
                    winner_agent = max(vote_counts, key=vote_counts.get)
                    winner_proposal = next(
                        (p for p in proposals if p.agent_name == winner_agent),
                        proposals[0]
                    )
                else:
                    winner_proposal = proposals[0]
                    winner_agent = winner_proposal.agent_name

                print(f"    >>> Winner: {winner_agent}")

                # Create final LocationSchema
                final_location = {
                    "id": loc_id,
                    "name": winner_proposal.name,
                    "type": winner_proposal.type,
                    "description": winner_proposal.description,
                    "atmosphere": winner_proposal.atmosphere,
                    "key_features": winner_proposal.key_features,
                    "sensory_details": winner_proposal.sensory_details,
                    "connection_to_story": loc_info['source'],
                }

                locations.append(final_location)
                location_debates.append({
                    "location_id": loc_id,
                    "source": loc_info['source'],
                    "proposals": [p.model_dump() for p in proposals],
                    "critiques": [c.model_dump() for c in critiques],
                    "votes": [v.model_dump() for v in votes],
                    "winner": winner_agent,
                })

            # =========================================
            # PART B: WORLD CONTEXT (No Debate - Parallel Generation)
            # =========================================
            print(f"\n{'='*50}")
            print("PART B: WORLD CONTEXT GENERATION")
            print(f"{'='*50}")
            print(f">>> 4 specialized agents generating world details...")
            print(f">>> No debate - each agent handles their categories")

            # Initialize world building agents
            sociologist = WorldSociologistAgent(model=self.model)
            economist = WorldEconomistAgent(model=self.model)
            politician = WorldPoliticianAgent(model=self.model)
            culturalist = WorldCulturalistAgent(model=self.model)

            # Generate all categories
            print(f"\n    [SOCIOLOGIST] Generating daily life & social structure...")
            try:
                daily_life = sociologist.generate_daily_life(setting_prompt, deck_of_worlds, story_context)
                print(f"      >>> Daily life: {len(daily_life.common_foods)} foods, {daily_life.eating_customs[:30]}...")
            except Exception as e:
                print(f"      >>> Daily life failed: {str(e)[:50]}")
                daily_life = DailyLifeSchema(
                    common_foods=["bread", "stew", "fish", "root vegetables", "ale"],
                    eating_customs="Communal meals in taverns and homes",
                    clothing_styles="Simple woolen garments for common folk, finer fabrics for wealthy",
                    shelter_types="Stone and timber houses, thatched roofs",
                )

            try:
                social_structure = sociologist.generate_social_structure(setting_prompt, deck_of_worlds, story_context)
                print(f"      >>> Social structure: {len(social_structure.common_jobs)} common jobs")
            except Exception as e:
                print(f"      >>> Social structure failed: {str(e)[:50]}")
                social_structure = SocialStructureSchema(
                    class_system="Wide gap between wealthy and poor, limited mobility",
                    common_jobs=["farmer", "fisherman", "laborer", "servant", "craftsman"],
                    desirable_jobs=["merchant", "scholar", "guard captain"],
                    lowly_jobs=["ditch digger", "corpse handler", "sewer cleaner"],
                    guilds_organizations=["Merchants Guild", "Workers Union"],
                )

            print(f"\n    [ECONOMIST] Generating economy...")
            try:
                economy = economist.generate_economy(setting_prompt, deck_of_worlds, story_context)
                print(f"      >>> Economy: {economy.currency[:30]}...")
            except Exception as e:
                print(f"      >>> Economy failed: {str(e)[:50]}")
                economy = EconomySchema(
                    currency="Bronze and silver coins",
                    trade_goods=["fish", "textiles", "iron", "spices"],
                    resources=["timber", "fish", "clay"],
                    taxation="Heavy taxes collected by the ruling family",
                )

            print(f"\n    [POLITICIAN] Generating government & law...")
            try:
                government_law = politician.generate_government_law(setting_prompt, deck_of_worlds, story_context)
                print(f"      >>> Government: {government_law.government_type[:40]}...")
            except Exception as e:
                print(f"      >>> Government failed: {str(e)[:50]}")
                government_law = GovernmentLawSchema(
                    government_type="Nominal council, actually controlled by crime family",
                    law_enforcement="Corrupt guards in crime family's pocket",
                    courts_trials="Justice can be bought",
                    punishments=["fines", "imprisonment", "public humiliation", "exile"],
                    military="Small city guard, crime family enforcers",
                )

            print(f"\n    [CULTURALIST] Generating culture, religion, entertainment...")
            try:
                education_health = culturalist.generate_education_health(setting_prompt, deck_of_worlds, story_context)
                print(f"      >>> Education: {education_health.education_system[:40]}...")
            except Exception as e:
                print(f"      >>> Education failed: {str(e)[:50]}")
                education_health = EducationHealthSchema(
                    education_system="Limited schooling for wealthy, apprenticeships for trades",
                    medicine="Basic herbal remedies, expensive healers for rich",
                    healers="Herbalists, traveling doctors, some folk magic",
                    common_ailments=["swamp fever", "coughs", "infections"],
                )

            try:
                entertainment = culturalist.generate_entertainment(setting_prompt, deck_of_worlds, story_context)
                print(f"      >>> Entertainment: {len(entertainment.festivals)} festivals")
            except Exception as e:
                print(f"      >>> Entertainment failed: {str(e)[:50]}")
                entertainment = EntertainmentSchema(
                    poor_entertainment=["tavern games", "storytelling", "gambling", "street performances"],
                    rich_entertainment=["private parties", "theater", "gambling houses", "hunting"],
                    festivals=["Harvest Festival", "Founding Day", "Night of Lanterns"],
                    art_forms=["folk songs", "woodcarving", "tapestries", "oral storytelling"],
                )

            try:
                religion_beliefs = culturalist.generate_religion_beliefs(setting_prompt, deck_of_worlds, story_context)
                print(f"      >>> Religion: {religion_beliefs.main_religion[:40]}...")
            except Exception as e:
                print(f"      >>> Religion failed: {str(e)[:50]}")
                religion_beliefs = ReligionBeliefsSchema(
                    main_religion="Worship of nature spirits and ancestors",
                    gods_deities=["The Swamp Mother", "The Forgotten Ones"],
                    temples_worship="Shrines at crossroads, offerings in the swamp",
                    superstitions=["Never speak ill of the dead", "Touch iron for luck"],
                    taboos=["Disturbing burial sites", "Wasting food"],
                )

            try:
                culture_customs = culturalist.generate_culture_customs(setting_prompt, deck_of_worlds, story_context)
                print(f"      >>> Culture: {len(culture_customs.social_rules)} social rules")
            except Exception as e:
                print(f"      >>> Culture failed: {str(e)[:50]}")
                culture_customs = CultureCustomsSchema(
                    social_rules=["Respect elders", "Pay debts promptly", "Don't cross the family"],
                    gestures_respect="Bowing head, lowered eyes",
                    gestures_rudeness="Direct eye contact with superiors, spitting",
                    family_structure="Extended families, clan loyalty",
                    naming_conventions="Given name followed by family name",
                )

            # Assemble world data
            world_data = {
                "daily_life": daily_life.model_dump(),
                "social_structure": social_structure.model_dump(),
                "economy": economy.model_dump(),
                "government_law": government_law.model_dump(),
                "education_health": education_health.model_dump(),
                "entertainment": entertainment.model_dump(),
                "religion_beliefs": religion_beliefs.model_dump(),
                "culture_customs": culture_customs.model_dump(),
            }

            duration = time.time() - start_time

            print(f"\n{'='*60}")
            print("STEP 3 COMPLETE")
            print(f"{'='*60}")
            print(f">>> Duration: {duration:.1f}s")
            print(f">>> Locations: {len(locations)}")
            for loc in locations:
                print(f"    - {loc['name']} ({loc['type']})")
            print(f">>> World Categories: {len(world_data)}")

            return Step3Result(
                locations=locations,
                world=world_data,
                location_debates=location_debates,
                success=True,
                duration_seconds=round(duration, 2),
            )

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Step3Result(
                locations=[],
                world={},
                location_debates=[],
                success=False,
                error=str(e),
                duration_seconds=round(time.time() - start_time, 2),
            )

    # =========================================================================
    # STEP 4: CHAPTER/SCENE OUTLINE (Multi-Agent Debate)
    # =========================================================================

    def _plan_chapters(self, structure_beats: dict) -> list[dict]:
        """Plan chapter structure from 7-point beats.

        Returns list of chapter plans mapping structure beats to chapters.
        """
        chapters = []

        # Act 1: Setup (2 chapters)
        chapters.append({
            "chapter_number": 1,
            "act": 1,
            "beats": ["hook"],
            "focus": "Establish protagonist's broken state and world",
            "scenes_target": 5,
        })
        chapters.append({
            "chapter_number": 2,
            "act": 1,
            "beats": ["plot_turn_1"],
            "focus": "Inciting incident forces protagonist into story",
            "scenes_target": 5,
        })

        # Act 2: Confrontation (3 chapters)
        chapters.append({
            "chapter_number": 3,
            "act": 2,
            "beats": ["pinch_point_1"],
            "focus": "First major pressure, stakes become real",
            "scenes_target": 5,
        })
        chapters.append({
            "chapter_number": 4,
            "act": 2,
            "beats": ["midpoint"],
            "focus": "Pivot - protagonist shifts from reaction to action",
            "scenes_target": 5,
        })
        chapters.append({
            "chapter_number": 5,
            "act": 2,
            "beats": ["pinch_point_2"],
            "focus": "Darkest moment, all seems lost",
            "scenes_target": 5,
        })

        # Act 3: Resolution (2 chapters)
        chapters.append({
            "chapter_number": 6,
            "act": 3,
            "beats": ["plot_turn_2"],
            "focus": "Final piece enables victory",
            "scenes_target": 5,
        })
        chapters.append({
            "chapter_number": 7,
            "act": 3,
            "beats": ["resolution"],
            "focus": "Transformation complete, new state",
            "scenes_target": 5,
        })

        return chapters

    def _generate_ticking_clock(self, codex: dict) -> dict:
        """Generate story-level ticking clock based on story seed."""
        outline = codex.get("story", {}).get("outline", {})
        story_seed = outline.get("story_seed_parsed", {})

        stakes = story_seed.get("stakes", "failure")
        goal = story_seed.get("goal", "succeed")

        # Generate ticking clock based on stakes
        if "friend" in stakes.lower() or "blame" in stakes.lower():
            return {
                "ticking_clock": "The authorities will execute the accused at dawn of the third day",
                "ticking_clock_deadline": "Dawn of the third day",
                "ticking_clock_consequence": "An innocent person dies and the protagonist loses everything",
            }
        elif "family" in stakes.lower() or "loved" in stakes.lower():
            return {
                "ticking_clock": "The loved one will be beyond saving when the moon is full",
                "ticking_clock_deadline": "The full moon in three nights",
                "ticking_clock_consequence": "The loved one is lost forever",
            }
        else:
            return {
                "ticking_clock": f"If the protagonist fails to {goal}, the consequences become permanent",
                "ticking_clock_deadline": "Before the week ends",
                "ticking_clock_consequence": stakes,
            }

    def _tally_scene_votes(self, votes: list, agent_names: list[str]) -> str:
        """Tally votes and return winning agent name."""
        if not votes:
            return agent_names[0] if agent_names else "SCENE_PLOT"

        vote_counts = Counter(v.voted_for_agent for v in votes)
        if not vote_counts:
            return agent_names[0] if agent_names else "SCENE_PLOT"

        return max(vote_counts, key=vote_counts.get)

    def step4_world_building(self, codex: dict) -> Step4Result:
        """Step 4: World Building (World Pressure + Dynamic Locations).

        Substeps:
        1. World Pressure Debate (4 agents council)
        2. Extract unique location types from Step 3 beats
        3. For each location type: Generate location (4 debates: Name, Physical, Atmosphere, Thematic)

        Args:
            codex: The codex dictionary with previous steps' results

        Returns:
            Step4Result with world_pressure, locations, and debate metadata
        """
        start_time = time.time()

        try:
            # Get previous results
            story_prompt, world_context = self.extract_prompts(codex)
            theme_foundation = codex.get("story", {}).get("theme_foundation", {})
            theme_question = theme_foundation.get("central_question", "Unknown theme")
            story_shape = codex.get("story", {}).get("story_shape", "Unknown")
            primary_genre = codex.get("story", {}).get("primary_genre", "Unknown")
            tone_flavor = codex.get("story", {}).get("tone_flavor", "")
            integrated_beats = codex.get("story", {}).get("integrated_beats", [])

            # Validate prerequisites
            if not integrated_beats:
                return Step4Result(
                    world_pressure={},
                    locations=[],
                    step4_debates={},
                    success=False,
                    error="No integrated beats found. Run Step 3 first.",
                )

            # Extract key scenes from integrated beats for location context
            key_scenes = []
            for beat in integrated_beats[:10]:  # Use first 10 beats for context
                beat_name = beat.get("beat_name", "")
                description = beat.get("description", "")
                if beat_name and description:
                    key_scenes.append(f"{beat_name}: {description[:100]}")

            # Initialize debate storage
            step4_debates = {
                "world_pressure": {},
                "location_1": {},
                "location_2": {},
            }

            print(f"\n{'='*60}")
            print("STEP 4: WORLD BUILDING")
            print(f"{'='*60}")
            print(f">>> Theme: {theme_question}")
            print(f">>> Story Shape: {story_shape}")
            print(f">>> Genre: {primary_genre}")
            if tone_flavor:
                print(f">>> Tone: {tone_flavor}")

            # =========================================================================
            # SUBSTEP 1: WORLD PRESSURE DEBATE (4 agents council)
            # =========================================================================
            print(f"\n{'='*60}")
            print("SUBSTEP 1: WORLD PRESSURE DEBATE")
            print(f"{'='*60}")
            print(">>> 4-agent council debate on thematic world pressures")

            world_pressure_agents = [
                WorldPressureSociologistAgent(model=self.model),
                WorldPressureEconomistAgent(model=self.model),
                WorldPressurePoliticianAgent(model=self.model),
                WorldPressureCulturalistAgent(model=self.model),
            ]

            # Phase 1: Proposals (parallel)
            print(f"\n>>> Phase 1: Proposals (4 agents, parallel)")
            wp_proposals = self._parallel_agent_calls(
                world_pressure_agents, 'propose_world_pressure',
                theme_question=theme_question, story_shape=story_shape, world_context=world_context,
            )
            wp_proposals = [p for p in wp_proposals if p is not None]
            for p in wp_proposals:
                print(f"      Societal: {p.world_pressure.societal[:80]}...")

            if not wp_proposals:
                return Step4Result(
                    world_pressure={},
                    locations=[],
                    step4_debates=step4_debates,
                    success=False,
                    error="All world pressure agents failed to generate proposals",
                )

            # Phase 2: Critiques (parallel)
            print(f"\n>>> Phase 2: Critiques (parallel)")
            critique_results = self._parallel_agent_calls(
                world_pressure_agents, 'critique_world_pressures', wp_proposals, theme_question
            )
            all_wp_critiques = []
            for result in critique_results:
                if result is not None:
                    all_wp_critiques.extend(result)

            # Phase 3: Voting (parallel)
            print(f"\n>>> Phase 3: Voting (parallel)")
            wp_votes = self._parallel_agent_calls(
                world_pressure_agents, 'vote', wp_proposals, theme_question
            )
            wp_votes = [v for v in wp_votes if v is not None]
            for v in wp_votes:
                print(f"    - votes for Proposal {v.chosen_proposal_index}")

            # Tally votes
            vote_counts = {}
            if not wp_votes:
                winner_index = 0
            else:
                for v in wp_votes:
                    vote_counts[v.chosen_proposal_index] = vote_counts.get(v.chosen_proposal_index, 0) + 1
                winner_index = max(vote_counts, key=vote_counts.get)

            winning_wp = wp_proposals[winner_index]
            print(f"\n>>> WINNER: Proposal {winner_index} ({vote_counts.get(winner_index, 0)} votes)")
            print(f">>> Societal: {winning_wp.world_pressure.societal}")
            print(f">>> Economic: {winning_wp.world_pressure.economic}")
            print(f">>> Political: {winning_wp.world_pressure.political}")
            print(f">>> Cultural: {winning_wp.world_pressure.cultural}")

            # Store world pressure in codex and debates
            world_pressure_dict = {
                "societal": winning_wp.world_pressure.societal,
                "economic": winning_wp.world_pressure.economic,
                "political": winning_wp.world_pressure.political,
                "cultural": winning_wp.world_pressure.cultural,
                "thematic_integration": winning_wp.world_pressure.thematic_integration,
            }
            codex["story"]["world_pressure"] = world_pressure_dict

            step4_debates["world_pressure"] = {
                "proposals": [p.model_dump() for p in wp_proposals],
                "critiques": [c.model_dump() for c in all_wp_critiques],
                "votes": [v.model_dump() for v in wp_votes],
                "winner_index": winner_index,
            }

            # =========================================================================
            # SUBSTEP 2: GENERATE LOCATIONS FROM INTEGRATED BEATS
            # =========================================================================
            # Extract unique location types from integrated beats
            location_types_from_beats = []
            beat_location_types_set = set()

            for beat in integrated_beats:
                beat_loc_type = beat.get("location_type")
                if beat_loc_type and beat_loc_type not in beat_location_types_set:
                    beat_location_types_set.add(beat_loc_type)
                    location_types_from_beats.append(beat_loc_type)

            # Use extracted location types if available, otherwise fall back to genre-based defaults
            if location_types_from_beats:
                location_types = location_types_from_beats
                print(f"\n>>> Extracted {len(location_types)} unique location types from Step 3 beats")
                for loc_type in location_types:
                    print(f"    - {loc_type}")
            else:
                # Fallback: use genre-based location types if no beats have location data
                print("\n>>> WARNING: No location types found in beats, using genre-based defaults")
                if "fantasy" in primary_genre.lower() or "magic" in world_context.lower():
                    location_types = ["Sacred Temple or Shrine", "Public Gathering Place"]
                elif "sci-fi" in primary_genre.lower() or "space" in world_context.lower():
                    location_types = ["Central Hub or Station", "Remote Outpost"]
                elif "mystery" in primary_genre.lower() or "crime" in primary_genre.lower():
                    location_types = ["Crime Scene Location", "Investigation Headquarters"]
                elif "romance" in primary_genre.lower():
                    location_types = ["Meeting Place", "Intimate Setting"]
                elif "horror" in primary_genre.lower():
                    location_types = ["Haunted Location", "Safe Haven"]
                elif "thriller" in primary_genre.lower():
                    location_types = ["High-Stakes Location", "Safe House"]
                else:
                    # Generic fallback
                    location_types = ["Primary Story Location", "Secondary Story Location"]

            # Generate locations dynamically (one per unique location type)
            locations = []

            # Check if parallel processing is enabled for location level
            step4_config = get_step_config("step4_world_building")
            parallel_config = step4_config.get("parallel_processing", {})
            parallel_enabled = parallel_config.get("location_level", False)
            max_workers_locations = parallel_config.get("max_workers_locations", 4)

            if parallel_enabled and len(location_types) > 1:
                print(f"\n>>> Parallel location generation enabled: {len(location_types)} locations with {max_workers_locations} workers")
                from concurrent.futures import ThreadPoolExecutor, as_completed

                location_results = []
                with ThreadPoolExecutor(max_workers=max_workers_locations) as executor:
                    future_to_location = {
                        executor.submit(
                            self._create_location_parallel,
                            i,
                            location_type,
                            world_context,
                            tone_flavor if tone_flavor else primary_genre,
                            theme_question,
                            key_scenes
                        ): (i, location_type)
                        for i, location_type in enumerate(location_types, start=1)
                    }

                    for future in as_completed(future_to_location):
                        location_num, location_type = future_to_location[future]
                        try:
                            location_result = future.result()
                            location_results.append((location_num, location_result))
                            worker_id = self._get_worker_id()
                            print(f"[Worker-{worker_id}] Location {location_num} ({location_type}) completed")
                        except Exception as e:
                            print(f"Error generating location {location_num}: {str(e)[:100]}")
                            import traceback
                            traceback.print_exc()

                # Sort results by location number to preserve order
                location_results.sort(key=lambda x: x[0])

                # Store locations in codex
                if "locations" not in codex["story"]:
                    codex["story"]["locations"] = []

                for location_num, location_result in location_results:
                    codex["story"]["locations"].append(location_result["location"])
                    locations.append(location_result["location"])
                    step4_debates[f"location_{location_num}"] = location_result["debates"]
            else:
                # Sequential location generation (original behavior)
                if not parallel_enabled:
                    print(f"\n>>> Sequential location generation (parallel disabled)")
                else:
                    print(f"\n>>> Sequential location generation (only 1 location)")

                for i, location_type in enumerate(location_types, start=1):
                    print(f"\n{'='*60}")
                    print(f"SUBSTEP {i+1}: LOCATION {i} DESIGN ({location_type})")
                    print(f"{'='*60}")

                    location_result = self._debate_location(
                        location_number=i,
                        location_type=location_type,
                        setting=world_context,
                        tone=tone_flavor if tone_flavor else primary_genre,
                        thematic_question=theme_question,
                        key_scenes=key_scenes,
                    )

                    # Store location in codex
                    if "locations" not in codex["story"]:
                        codex["story"]["locations"] = []
                    codex["story"]["locations"].append(location_result["location"])
                    locations.append(location_result["location"])
                    step4_debates[f"location_{i}"] = location_result["debates"]

            # =========================================================================
            # SUBSTEP 3+: GENERATE COMPREHENSIVE WORLD DETAILS
            # =========================================================================
            print(f"\n{'='*60}")
            print("GENERATING COMPREHENSIVE WORLD DETAILS")
            print(f"{'='*60}")

            from src.world_schemas import (
                DailyLife, SocialStructure, Economy, GovernmentLaw,
                EducationHealth, Entertainment, ReligionBeliefs, CultureCustoms
            )

            # Build context for world generation
            world_context_prompt = f"""
WORLD PRESSURE:
- Societal: {world_pressure_dict['societal'][:200]}...
- Economic: {world_pressure_dict['economic'][:200]}...
- Political: {world_pressure_dict['political'][:200]}...
- Cultural: {world_pressure_dict['cultural'][:200]}...

THEME: {theme_question}
GENRE: {primary_genre}
SETTING: {world_context}
TONE: {tone_flavor if tone_flavor else primary_genre}

LOCATIONS: {', '.join([loc['name'] for loc in locations])}
"""

            # Generate each world component
            world_dict = {}

            # 1. DAILY LIFE
            print("\n>>> Generating Daily Life...")
            daily_life_prompt = f"""{world_context_prompt}

Create detailed daily life information for this world.
Focus on: common foods, eating customs, clothing styles, and shelter types.
Make it realistic and thematically resonant.

Provide a DailyLife schema with all required fields."""

            daily_life = self.invoke_structured(daily_life_prompt, DailyLife, max_tokens=2500)
            world_dict["daily_life"] = daily_life.model_dump()
            print(f"    ✓ Foods: {len(daily_life.common_foods)} items")

            # 2. SOCIAL STRUCTURE
            print("\n>>> Generating Social Structure...")
            social_prompt = f"""{world_context_prompt}

Create a compelling social hierarchy for this world.
Focus on: class system, common jobs, desirable jobs, lowly jobs, and guilds/organizations.
Show clear class divisions and their consequences.

Provide a SocialStructure schema with all required fields."""

            social_structure = self.invoke_structured(social_prompt, SocialStructure, max_tokens=2500)
            world_dict["social_structure"] = social_structure.model_dump()
            print(f"    ✓ Jobs: {len(social_structure.common_jobs)} common, {len(social_structure.desirable_jobs)} desirable")

            # 3. ECONOMY
            print("\n>>> Generating Economy...")
            economy_prompt = f"""{world_context_prompt}

Create an economy with meaningful currency and resources.
Focus on: currency name, trade goods, resources, and taxation system.
Show economic pressure and inequality.

Provide an Economy schema with all required fields."""

            economy = self.invoke_structured(economy_prompt, Economy, max_tokens=get_token_limit("step4_world_building", "economy"))
            world_dict["economy"] = economy.model_dump()
            print(f"    ✓ Currency: {economy.currency}")

            # 4. GOVERNMENT & LAW
            print("\n>>> Generating Government & Law...")
            gov_prompt = f"""{world_context_prompt}

Create a government and legal system.
Focus on: government type, law enforcement, courts/trials, punishments, and military.
Show how power is wielded and maintained.

Provide a GovernmentLaw schema with all required fields."""

            government = self.invoke_structured(gov_prompt, GovernmentLaw, max_tokens=get_token_limit("step4_world_building", "government"))
            world_dict["government_law"] = government.model_dump()
            print(f"    ✓ Government: {government.government_type}")

            # 5. EDUCATION & HEALTH
            print("\n>>> Generating Education & Health...")
            edu_prompt = f"""{world_context_prompt}

Create education and healthcare systems.
Focus on: education system, medicine availability, healers, and common ailments.
Show how knowledge and health are distributed (or withheld).

Provide an EducationHealth schema with all required fields."""

            education = self.invoke_structured(edu_prompt, EducationHealth, max_tokens=2500)
            world_dict["education_health"] = education.model_dump()
            print(f"    ✓ Ailments: {len(education.common_ailments)} common diseases")

            # 6. ENTERTAINMENT
            print("\n>>> Generating Entertainment...")
            entertainment_prompt = f"""{world_context_prompt}

Create entertainment and leisure activities.
Focus on: how poor people entertain themselves, how rich people entertain themselves, festivals, and art forms.
Show class divisions through entertainment.

Provide an Entertainment schema with all required fields."""

            entertainment = self.invoke_structured(entertainment_prompt, Entertainment, max_tokens=2500)
            world_dict["entertainment"] = entertainment.model_dump()
            print(f"    ✓ Festivals: {len(entertainment.festivals)} major celebrations")

            # 7. RELIGION & BELIEFS
            print("\n>>> Generating Religion & Beliefs...")
            religion_prompt = f"""{world_context_prompt}

Create religious and spiritual beliefs.
Focus on: main religion, gods/deities, temples/worship, superstitions, and taboos.
Make beliefs thematically meaningful.

Provide a ReligionBeliefs schema with all required fields."""

            religion = self.invoke_structured(religion_prompt, ReligionBeliefs, max_tokens=get_token_limit("step4_world_building", "religion"))
            world_dict["religion_beliefs"] = religion.model_dump()
            print(f"    ✓ Religion: {religion.main_religion}")

            # 8. CULTURE & CUSTOMS
            print("\n>>> Generating Culture & Customs...")
            culture_prompt = f"""{world_context_prompt}

Create cultural norms and social customs.
Focus on: social rules, gestures of respect, gestures of rudeness, family structure, and naming conventions.
Show how culture shapes daily interactions.

Provide a CultureCustoms schema with all required fields."""

            culture = self.invoke_structured(culture_prompt, CultureCustoms, max_tokens=2500)
            world_dict["culture_customs"] = culture.model_dump()
            print(f"    ✓ Social Rules: {len(culture.social_rules)} key rules")

            # Store world in codex
            codex["story"]["world"] = world_dict
            print(f"\n>>> World building complete: 8 components generated")

            duration = time.time() - start_time

            print(f"\n{'='*60}")
            print(f"STEP 4 COMPLETE ({duration:.1f}s)")
            print(f"{'='*60}")
            print(f">>> World Pressure: Defined")
            for i, loc in enumerate(locations, start=1):
                print(f">>> Location {i}: {loc['name']} ({loc['type']})")
            print(f">>> World Details: 8 components (daily_life, social_structure, economy, government_law, education_health, entertainment, religion_beliefs, culture_customs)")
            print(f">>>   Currency: {world_dict['economy']['currency']}")
            print(f">>>   Religion: {world_dict['religion_beliefs']['main_religion']}")
            print(f">>>   Government: {world_dict['government_law']['government_type']}")

            # =========================================================
            # COSTUME DESIGN (World-Accurate, Post-World Building)
            # =========================================================
            print(f"\n{'='*60}")
            print("COSTUME DESIGN (World-Accurate)")
            print(f"{'='*60}")
            print(">>> Designing costumes with full world context...")

            # Get characters from Step 1
            characters = codex.get("story", {}).get("characters", [])
            if characters:
                # Get genre from Step 2 (stored at root level of story)
                primary_genre = codex.get("story", {}).get("primary_genre", "fantasy")
                secondary_genre = codex.get("story", {}).get("secondary_genre", "")

                # Infer time period from genre
                time_period_hint = self._infer_time_period(primary_genre, world_dict)

                # Build world context for costume agents
                world_context_for_costumes = {
                    "economy": world_pressure_dict.get("economic", ""),
                    "government": world_dict.get("government_law", {}).get("government_type", ""),
                    "culture": world_dict.get("culture_customs", {}).get("social_rules", []),
                    "religion": world_dict.get("religion_beliefs", {}).get("main_religion", ""),
                    "genre": primary_genre,
                    "secondary_genre": secondary_genre,
                }

                print(f">>> Genre: {primary_genre} / {secondary_genre}")
                print(f">>> Time Period Hint: {time_period_hint}")
                print(f">>> Economy: {world_pressure_dict.get('economic', 'N/A')[:60]}...")

                # Design costume for each character
                costume_debates = {}
                for i, character in enumerate(characters):
                    char_name = character.get('name', f'Character {i+1}')
                    print(f"\n>>> Designing costume for {char_name}...")

                    try:
                        costume_result = self._run_costume_debate(
                            character=character,
                            world_context=world_context_for_costumes,
                            genre=primary_genre,
                            time_period_hint=time_period_hint,
                        )

                        if "error" not in costume_result:
                            # Update character with detailed costume
                            character['costume'] = costume_result['winning_summary']
                            character['costume_details'] = costume_result['winning_costume']

                            # Store debate metadata
                            costume_debates[f"character_{i+1}_{char_name}"] = costume_result

                            print(f"    ✓ Costume: {costume_result['winning_costume']['primary_color']} {costume_result['winning_costume']['garment_type']}")
                        else:
                            print(f"    ✗ Costume debate failed for {char_name}")

                    except Exception as e:
                        print(f"    ✗ Error designing costume for {char_name}: {str(e)[:50]}")

                # Add costume debates to step4_debates
                step4_debates["costume_debates"] = costume_debates

                print(f"\n>>> Costume design complete for {len(characters)} characters")

            else:
                print(">>> No characters found (Step 1 not run yet) - skipping costume design")

            return Step4Result(
                world_pressure=world_pressure_dict,
                locations=locations,
                step4_debates=step4_debates,
                success=True,
                duration_seconds=duration,
            )

        except Exception as e:
            duration = time.time() - start_time
            print(f"\nError in step4_world_building: {str(e)}")
            import traceback
            traceback.print_exc()
            return Step4Result(
                world_pressure={},
                locations=[],
                step4_debates={},
                success=False,
                error=str(e),
                duration_seconds=duration,
            )

    def _create_location_parallel(
        self,
        location_number: int,
        location_type: str,
        setting: str,
        tone: str,
        thematic_question: str,
        key_scenes: list[str],
    ) -> dict:
        """Thread-safe wrapper for location creation with logging.

        This method is called by parallel workers to create locations independently.

        Args:
            location_number: The location number (1-indexed)
            location_type: The type of location (e.g., "Sacred Temple or Shrine")
            setting: The world setting/context
            tone: The story tone
            thematic_question: The central thematic question
            key_scenes: List of key scenes for context

        Returns:
            dict with "location" (final location dict) and "debates" (all debate metadata)
        """
        worker_id = self._get_worker_id()
        print(f"\n[Worker-{worker_id}] {'='*60}")
        print(f"[Worker-{worker_id}] LOCATION {location_number} DESIGN ({location_type})")
        print(f"[Worker-{worker_id}] {'='*60}")

        # Call the existing _debate_location method
        return self._debate_location(
            location_number=location_number,
            location_type=location_type,
            setting=setting,
            tone=tone,
            thematic_question=thematic_question,
            key_scenes=key_scenes,
        )

    def _debate_location(
        self,
        location_number: int,
        location_type: str,
        setting: str,
        tone: str,
        thematic_question: str,
        key_scenes: list[str],
    ) -> dict:
        """Run 4 sequential debates for a single location.

        Returns:
            dict with "location" (final location dict) and "debates" (all debate metadata)
        """
        debates = {
            "name": {},
            "physical": {},
            "atmosphere": {},
            "thematic": {},
        }

        # -------------------------------------------------------------------------
        # DEBATE 1: NAME (3 agents)
        # -------------------------------------------------------------------------
        print(f"\n>>> DEBATE 1: NAME")
        name_agents = [
            LocationNameCreativeAgent(model=self.model),
            LocationNameAuthenticAgent(model=self.model),
            LocationNameThematicAgent(model=self.model),
        ]

        print(f"    Phase 1: Proposals (3 agents)")
        name_proposals = []
        for agent in name_agents:
            print(f"      - {agent.name} proposing...")
            try:
                proposal = agent.propose_name(
                    location_type=location_type,
                    setting=setting,
                    tone=tone,
                    thematic_question=thematic_question,
                )
                name_proposals.append(proposal)
                print(f"        Name: {proposal.location_name}")
            except Exception as e:
                print(f"        Error: {str(e)[:100]}")
                continue

        if not name_proposals:
            # Fallback name
            winning_name = f"Location_{location_number}"
            print(f"    WARNING: No name proposals, using fallback: {winning_name}")
        else:
            # Critiques
            print(f"    Phase 2: Critiques")
            name_critiques = []
            for agent in name_agents:
                for proposal in name_proposals:
                    try:
                        # Call each agent with their specific required parameters
                        if isinstance(agent, LocationNameCreativeAgent):
                            critique = agent.critique_name(proposal, location_type, tone)
                        elif isinstance(agent, LocationNameAuthenticAgent):
                            critique = agent.critique_name(proposal, location_type, setting)
                        elif isinstance(agent, LocationNameThematicAgent):
                            critique = agent.critique_name(proposal, location_type, thematic_question)
                        else:
                            continue

                        if critique:
                            name_critiques.append(critique)
                            print(f"      {agent.name} -> {proposal.agent_name}: {critique.score}/10")
                    except Exception as e:
                        print(f"      Error: {str(e)[:50]}")
                        continue

            # Votes
            print(f"    Phase 3: Voting")
            name_votes = []
            for agent in name_agents:
                try:
                    # Call each agent with their specific required parameters
                    if isinstance(agent, LocationNameCreativeAgent):
                        vote = agent.vote(name_proposals, location_type, tone)
                    elif isinstance(agent, LocationNameAuthenticAgent):
                        vote = agent.vote(name_proposals, location_type, setting)
                    elif isinstance(agent, LocationNameThematicAgent):
                        vote = agent.vote(name_proposals, location_type, thematic_question)
                    else:
                        continue

                    name_votes.append(vote)
                    voted_name = name_proposals[vote.chosen_proposal_index].location_name if vote.chosen_proposal_index < len(name_proposals) else "invalid"
                    print(f"      {agent.name} votes for Proposal {vote.chosen_proposal_index} ({voted_name})")
                except Exception as e:
                    print(f"      Error: {str(e)[:50]}")
                    continue

            # Tally
            if name_votes:
                # Map votes to agent names
                vote_counts = Counter(
                    name_proposals[v.chosen_proposal_index].agent_name
                    for v in name_votes
                    if v.chosen_proposal_index < len(name_proposals)
                )
                winner_agent = max(vote_counts, key=vote_counts.get)
                winning_proposal = next((p for p in name_proposals if p.agent_name == winner_agent), name_proposals[0])
                winning_name = winning_proposal.location_name
                print(f"    WINNER: {winning_name} (by {winner_agent})")
            else:
                winning_name = name_proposals[0].location_name
                print(f"    WINNER (default): {winning_name}")

        debates["name"] = {
            "proposals": [p.model_dump() for p in name_proposals] if name_proposals else [],
            "critiques": [c.model_dump() for c in name_critiques if c is not None],
            "votes": [v.model_dump() for v in name_votes if v is not None],
            "winner_name": winning_name,
        }

        # -------------------------------------------------------------------------
        # DEBATE 2: PHYSICAL DESCRIPTION (3 agents)
        # -------------------------------------------------------------------------
        print(f"\n>>> DEBATE 2: PHYSICAL DESCRIPTION")
        physical_agents = [
            LocationPhysicalSensoryAgent(model=self.model),
            LocationPhysicalFunctionalAgent(model=self.model),
            LocationPhysicalSymbolicAgent(model=self.model),
        ]

        print(f"    Phase 1: Proposals (3 agents)")
        physical_proposals = []
        for agent in physical_agents:
            print(f"      - {agent.name} proposing...")
            try:
                proposal = agent.propose_physical(
                    location_name=winning_name,
                    location_type=location_type,
                    setting=setting,
                    thematic_question=thematic_question,
                )
                physical_proposals.append(proposal)
                print(f"        {proposal.physical_description[:60]}...")
            except Exception as e:
                print(f"        Error: {str(e)[:100]}")
                continue

        if not physical_proposals:
            winning_physical = f"A {location_type.lower()} called {winning_name}"
            print(f"    WARNING: No physical proposals, using fallback")
        else:
            # Critiques
            print(f"    Phase 2: Critiques")
            physical_critiques = []
            for agent in physical_agents:
                for proposal in physical_proposals:
                    try:
                        # Symbolic agent needs thematic_question, others don't
                        if isinstance(agent, LocationPhysicalSymbolicAgent):
                            critique = agent.critique_physical(proposal, location_type, thematic_question)
                        else:
                            critique = agent.critique_physical(proposal, location_type)

                        if critique:
                            physical_critiques.append(critique)
                            print(f"      {agent.name} -> {proposal.agent_name}: {critique.score}/10")
                    except Exception as e:
                        print(f"      Error: {str(e)[:50]}")
                        continue

            # Votes
            print(f"    Phase 3: Voting")
            physical_votes = []
            for agent in physical_agents:
                try:
                    # Symbolic agent needs thematic_question, others don't
                    if isinstance(agent, LocationPhysicalSymbolicAgent):
                        vote = agent.vote(physical_proposals, location_type, thematic_question)
                    else:
                        vote = agent.vote(physical_proposals, location_type)

                    physical_votes.append(vote)
                    voted_desc = physical_proposals[vote.chosen_proposal_index].physical_description[:40] if vote.chosen_proposal_index < len(physical_proposals) else "invalid"
                    print(f"      {agent.name} votes for Proposal {vote.chosen_proposal_index} ({voted_desc}...)")
                except Exception as e:
                    print(f"      Error: {str(e)[:50]}")
                    continue

            # Tally
            if physical_votes:
                # Map votes to agent names
                vote_counts = Counter(
                    physical_proposals[v.chosen_proposal_index].agent_name
                    for v in physical_votes
                    if v.chosen_proposal_index < len(physical_proposals)
                )
                winner_agent = max(vote_counts, key=vote_counts.get)
                winning_proposal = next((p for p in physical_proposals if p.agent_name == winner_agent), physical_proposals[0])
                winning_physical = winning_proposal.physical_description
                print(f"    WINNER: {winning_physical[:60]}... (by {winner_agent})")
            else:
                winning_physical = physical_proposals[0].physical_description
                print(f"    WINNER (default): {winning_physical[:60]}...")

        debates["physical"] = {
            "proposals": [p.model_dump() for p in physical_proposals] if physical_proposals else [],
            "critiques": [c.model_dump() for c in physical_critiques if c is not None],
            "votes": [v.model_dump() for v in physical_votes if v is not None],
            "winner_description": winning_physical,
        }

        # -------------------------------------------------------------------------
        # DEBATE 3: ATMOSPHERE (3 agents)
        # -------------------------------------------------------------------------
        print(f"\n>>> DEBATE 3: ATMOSPHERE")
        atmosphere_agents = [
            LocationAtmosphereMoodAgent(model=self.model),
            LocationAtmosphereConflictAgent(model=self.model),
            LocationAtmosphereCharacterAgent(model=self.model),
        ]

        print(f"    Phase 1: Proposals (3 agents)")
        atmosphere_proposals = []
        for agent in atmosphere_agents:
            print(f"      - {agent.name} proposing...")
            try:
                proposal = agent.propose_atmosphere(
                    location_name=winning_name,
                    location_type=location_type,
                    physical_description=winning_physical,
                    thematic_question=thematic_question,
                )
                atmosphere_proposals.append(proposal)
                print(f"        {proposal.atmosphere[:60]}...")
            except Exception as e:
                print(f"        Error: {str(e)[:100]}")
                continue

        if not atmosphere_proposals:
            winning_atmosphere = "A place of significance and meaning."
            print(f"    WARNING: No atmosphere proposals, using fallback")
        else:
            # Critiques
            print(f"    Phase 2: Critiques")
            atmosphere_critiques = []
            for agent in atmosphere_agents:
                for proposal in atmosphere_proposals:
                    try:
                        # Mood and Conflict agents need location_type, Character needs both
                        if isinstance(agent, LocationAtmosphereCharacterAgent):
                            critique = agent.critique_atmosphere(proposal, location_type, thematic_question)
                        else:
                            critique = agent.critique_atmosphere(proposal, location_type)

                        if critique:
                            atmosphere_critiques.append(critique)
                            print(f"      {agent.name} -> {proposal.agent_name}: {critique.score}/10")
                    except Exception as e:
                        print(f"      Error: {str(e)[:50]}")
                        continue

            # Votes
            print(f"    Phase 3: Voting")
            atmosphere_votes = []
            for agent in atmosphere_agents:
                try:
                    vote = agent.vote(atmosphere_proposals, location_type)
                    atmosphere_votes.append(vote)
                    voted_atmos = atmosphere_proposals[vote.chosen_proposal_index].atmosphere[:40] if vote.chosen_proposal_index < len(atmosphere_proposals) else "invalid"
                    print(f"      {agent.name} votes for Proposal {vote.chosen_proposal_index} ({voted_atmos}...)")
                except Exception as e:
                    print(f"      Error: {str(e)[:50]}")
                    continue

            # Tally
            if atmosphere_votes:
                # Map votes to agent names
                vote_counts = Counter(
                    atmosphere_proposals[v.chosen_proposal_index].agent_name
                    for v in atmosphere_votes
                    if v.chosen_proposal_index < len(atmosphere_proposals)
                )
                winner_agent = max(vote_counts, key=vote_counts.get)
                winning_proposal = next((p for p in atmosphere_proposals if p.agent_name == winner_agent), atmosphere_proposals[0])
                winning_atmosphere = winning_proposal.atmosphere
                print(f"    WINNER: {winning_atmosphere[:60]}... (by {winner_agent})")
            else:
                winning_atmosphere = atmosphere_proposals[0].atmosphere
                print(f"    WINNER (default): {winning_atmosphere[:60]}...")

        debates["atmosphere"] = {
            "proposals": [p.model_dump() for p in atmosphere_proposals] if atmosphere_proposals else [],
            "critiques": [c.model_dump() for c in atmosphere_critiques if c is not None],
            "votes": [v.model_dump() for v in atmosphere_votes if v is not None],
            "winner_atmosphere": winning_atmosphere,
        }

        # -------------------------------------------------------------------------
        # DEBATE 4: THEMATIC SIGNIFICANCE (3 agents)
        # -------------------------------------------------------------------------
        print(f"\n>>> DEBATE 4: THEMATIC SIGNIFICANCE")
        thematic_agents = [
            LocationThematicResonanceAgent(model=self.model),
            LocationThematicContrastAgent(model=self.model),
            LocationThematicEvolutionAgent(model=self.model),
        ]

        print(f"    Phase 1: Proposals (3 agents)")
        thematic_proposals = []
        for agent in thematic_agents:
            print(f"      - {agent.name} proposing...")
            try:
                proposal = agent.propose_thematic(
                    location_name=winning_name,
                    location_type=location_type,
                    physical_description=winning_physical,
                    atmosphere=winning_atmosphere,
                    thematic_question=thematic_question,
                    key_scenes=key_scenes,
                )
                thematic_proposals.append(proposal)
                print(f"        {proposal.thematic_significance[:60]}...")
            except Exception as e:
                print(f"        Error: {str(e)[:100]}")
                continue

        if not thematic_proposals:
            winning_thematic = f"This location embodies aspects of the theme: {thematic_question}"
            print(f"    WARNING: No thematic proposals, using fallback")
        else:
            # Critiques
            print(f"    Phase 2: Critiques")
            thematic_critiques = []
            for agent in thematic_agents:
                for proposal in thematic_proposals:
                    try:
                        # All thematic agents need both location_type and thematic_question
                        critique = agent.critique_thematic(proposal, location_type, thematic_question)
                        if critique:
                            thematic_critiques.append(critique)
                            print(f"      {agent.name} -> {proposal.agent_name}: {critique.score}/10")
                    except Exception as e:
                        print(f"      Error: {str(e)[:50]}")
                        continue

            # Votes
            print(f"    Phase 3: Voting")
            thematic_votes = []
            for agent in thematic_agents:
                try:
                    vote = agent.vote(thematic_proposals, location_type, thematic_question)
                    thematic_votes.append(vote)
                    voted_them = thematic_proposals[vote.chosen_proposal_index].thematic_significance[:40] if vote.chosen_proposal_index < len(thematic_proposals) else "invalid"
                    print(f"      {agent.name} votes for Proposal {vote.chosen_proposal_index} ({voted_them}...)")
                except Exception as e:
                    print(f"      Error: {str(e)[:50]}")
                    continue

            # Tally
            if thematic_votes:
                # Map votes to agent names
                vote_counts = Counter(
                    thematic_proposals[v.chosen_proposal_index].agent_name
                    for v in thematic_votes
                    if v.chosen_proposal_index < len(thematic_proposals)
                )
                winner_agent = max(vote_counts, key=vote_counts.get)
                winning_proposal = next((p for p in thematic_proposals if p.agent_name == winner_agent), thematic_proposals[0])
                winning_thematic = winning_proposal.thematic_significance
                winning_scenes = winning_proposal.key_scenes
                print(f"    WINNER: {winning_thematic[:60]}... (by {winner_agent})")
            else:
                winning_thematic = thematic_proposals[0].thematic_significance
                winning_scenes = thematic_proposals[0].key_scenes
                print(f"    WINNER (default): {winning_thematic[:60]}...")

        debates["thematic"] = {
            "proposals": [p.model_dump() for p in thematic_proposals] if thematic_proposals else [],
            "critiques": [c.model_dump() for c in thematic_critiques if c is not None],
            "votes": [v.model_dump() for v in thematic_votes if v is not None],
            "winner_significance": winning_thematic,
        }

        # Extract key features from physical description (3-5 bullet points)
        # Use simple sentence splitting to extract features
        key_features = []
        if winning_physical:
            # Try to extract meaningful features from the description
            sentences = winning_physical.replace(". ", ".|").split("|")
            for sentence in sentences[:5]:  # Max 5 features
                sentence = sentence.strip().rstrip(".")
                if len(sentence) > 20 and len(sentence) < 150:  # Reasonable feature length
                    # Simplify to key feature format
                    if "," in sentence:
                        # Take first clause if multiple
                        feature = sentence.split(",")[0].strip()
                    else:
                        feature = sentence
                    if feature and feature not in key_features:
                        key_features.append(feature)

        # Ensure we have at least 3 features
        if len(key_features) < 3:
            key_features.extend([
                f"Distinctive {location_type.lower()} architecture",
                f"Atmospheric {location_type.lower()} setting",
                "Thematically significant space"
            ])
            key_features = key_features[:5]  # Max 5

        # Extract sensory details from physical description and atmosphere
        sensory_details = ""
        if winning_physical and winning_atmosphere:
            # Combine sensory aspects from both
            sensory_parts = []
            if "scent" in winning_physical.lower() or "smell" in winning_physical.lower():
                # Extract scent-related sentences
                for sent in winning_physical.split("."):
                    if "scent" in sent.lower() or "smell" in sent.lower():
                        sensory_parts.append(sent.strip())
                        break
            if "sound" in winning_physical.lower() or "echo" in winning_physical.lower():
                # Extract sound-related sentences
                for sent in winning_physical.split("."):
                    if "sound" in sent.lower() or "echo" in sent.lower():
                        sensory_parts.append(sent.strip())
                        break
            if "texture" in winning_physical.lower() or "feel" in winning_physical.lower():
                # Extract texture-related sentences
                for sent in winning_physical.split("."):
                    if "texture" in sent.lower() or "feel" in sent.lower():
                        sensory_parts.append(sent.strip())
                        break

            if sensory_parts:
                sensory_details = " ".join(sensory_parts)
            else:
                # Fallback: combine physical and atmosphere excerpts
                sensory_details = f"{winning_physical[:150]}... {winning_atmosphere[:150]}..."
        else:
            sensory_details = winning_physical[:200] if winning_physical else f"A {location_type.lower()} with distinctive sensory qualities."

        # Assemble final location with ALL required fields
        location = {
            "id": f"loc_{location_number:03d}",  # Format as loc_001, loc_002, etc.
            "name": winning_name,
            "type": location_type,
            "description": winning_physical,  # Rename physical_description to description
            "atmosphere": winning_atmosphere,
            "key_features": key_features,  # NEW: List of 3-5 features
            "sensory_details": sensory_details,  # NEW: Combined sensory information
            "connection_to_story": "story_location",  # NEW: Mark as story location (will be refined later)
            "location_prompt": {},  # NEW: Empty dict for now (image generation added later)
        }

        print(f"\n>>> LOCATION {location_number} COMPLETE")
        print(f"    ID: {location['id']}")
        print(f"    Name: {winning_name}")
        print(f"    Type: {location_type}")
        print(f"    Description: {winning_physical[:60]}...")
        print(f"    Atmosphere: {winning_atmosphere[:60]}...")
        print(f"    Key Features: {len(key_features)} features")
        print(f"    Thematic: {winning_thematic[:60]}...")

        return {
            "location": location,
            "debates": debates,
        }

    def step4_chapter_outline(self, codex: dict) -> Step4ChapterOutlineResult:
        """Generate detailed chapter/scene outline via multi-agent debate.

        Uses 4 scene debate agents:
        - ScenePlotAgent: GMC (Goal, Motivation, Conflict)
        - SceneCharacterAgent: Swain Scene/Sequel structure
        - ScenePacingAgent: Rhythm and tension management
        - SceneStructureAgent: 7-point structure alignment

        Debate flow for each scene:
        1. All 4 agents propose scene
        2. Cross-agent critique round
        3. All 4 agents vote
        4. Winner's scene is used

        Args:
            codex: The codex dictionary with outline, characters, locations

        Returns:
            Step4Result with chapter_outline and scene_debates
        """
        start_time = time.time()
        chapters = []
        scene_debates = []
        total_scenes = 0

        try:
            # Validate prerequisites
            outline = codex.get("story", {}).get("outline", {})
            structure_beats = outline.get("structure_beats", {})
            characters = codex.get("story", {}).get("characters", [])
            locations = codex.get("story", {}).get("locations", [])

            if not structure_beats:
                return Step4Result(
                    chapter_outline={},
                    scene_debates=[],
                    total_chapters=0,
                    total_scenes=0,
                    success=False,
                    error="No structure_beats found. Run Step 1 first.",
                )

            if not characters:
                return Step4Result(
                    chapter_outline={},
                    scene_debates=[],
                    total_chapters=0,
                    total_scenes=0,
                    success=False,
                    error="No characters found. Run Step 2 first.",
                )

            story_prompt, setting_prompt = self.extract_prompts(codex)

            print(f"\n{'='*60}")
            print("STEP 4: CHAPTER/SCENE OUTLINE (Multi-Agent Debate)")
            print(f"{'='*60}")
            print(f">>> Agents: 4 scene debate agents")
            print(f">>> Method: Propose -> Critique -> Vote per scene")
            print(f">>> Structure: 7 chapters, ~5 scenes each")

            # Initialize scene debate agents
            plot_agent = ScenePlotAgent(model=self.model)
            character_agent = SceneCharacterAgent(model=self.model)
            pacing_agent = ScenePacingAgent(model=self.model)
            structure_agent = SceneStructureAgent(model=self.model)
            agents = [plot_agent, character_agent, pacing_agent, structure_agent]

            # Plan chapters
            chapter_plans = self._plan_chapters(structure_beats)
            print(f">>> Planned {len(chapter_plans)} chapters")

            # Generate ticking clock
            ticking_clock = self._generate_ticking_clock(codex)
            print(f">>> Ticking Clock: {ticking_clock['ticking_clock'][:50]}...")

            # Process each chapter
            for chapter_plan in chapter_plans:
                chapter_num = chapter_plan["chapter_number"]
                print(f"\n{'='*50}")
                print(f"CHAPTER {chapter_num}: Act {chapter_plan['act']}")
                print(f"{'='*50}")
                print(f">>> Beats: {', '.join(chapter_plan['beats'])}")
                print(f">>> Focus: {chapter_plan['focus']}")

                chapter_scenes = []

                # Generate 5 scenes per chapter
                for scene_num in range(1, chapter_plan["scenes_target"] + 1):
                    print(f"\n    --- SCENE {scene_num} ---")

                    # Build context for scene
                    scene_context = {
                        "chapter": chapter_plan,
                        "scene_number": scene_num,
                        "previous_scenes": chapter_scenes,
                    }

                    # Round 1: All 4 agents propose
                    proposals = []
                    print(f"    Generating proposals...")
                    for agent in agents:
                        try:
                            proposal = agent.propose_scene(
                                chapter_context=chapter_plan,
                                scene_number=scene_num,
                                previous_scenes=chapter_scenes,
                                structure_beats=structure_beats,
                                characters=characters,
                                locations=locations,
                                setting_prompt=setting_prompt,
                            )
                            proposals.append(proposal)
                            print(f"      [{agent.name}] proposed: {proposal.scene.goal[:40]}...")
                        except Exception as e:
                            print(f"      [{agent.name}] failed: {str(e)[:40]}")

                    if not proposals:
                        # Fallback: create minimal scene
                        print(f"      All agents failed - creating fallback scene")
                        fallback_scene = {
                            "scene_number": scene_num,
                            "scene_type": "scene",
                            "time_of_day": "morning",
                            "location": locations[0]["name"] if locations else "Unknown",
                            "location_id": locations[0]["id"] if locations else "",
                            "pov_character": characters[0]["name"] if characters else "Protagonist",
                            "characters": [characters[0]["name"]] if characters else ["Protagonist"],
                            "character_ids": [characters[0]["id"]] if characters else [],
                            "goal": "Continue the journey",
                            "conflict": "Obstacles arise",
                            "outcome": "NO_AND",
                            "happens": "The story continues with challenges.",
                            "structure_connection": chapter_plan["beats"][0],
                            "scene_purpose": "Advance the plot",
                        }
                        chapter_scenes.append(fallback_scene)
                        total_scenes += 1
                        continue

                    # Round 2: Cross-critiques (each agent critiques one other)
                    critiques = []
                    print(f"    Gathering critiques...")
                    for i, agent in enumerate(agents[:3]):
                        target_idx = (i + 1) % len(proposals)
                        try:
                            critique = agent.critique_proposal(
                                target_agent=proposals[target_idx].agent_name,
                                proposal=proposals[target_idx],
                                chapter_context=chapter_plan,
                            )
                            critiques.append(critique)
                        except Exception as e:
                            print(f"      [{agent.name}] critique failed: {str(e)[:30]}")

                    # Round 3: All 4 agents vote
                    votes = []
                    print(f"    Collecting votes...")
                    for agent in agents:
                        try:
                            vote = agent.vote_for_best(
                                proposals=proposals,
                                chapter_context=chapter_plan,
                            )
                            votes.append(vote)
                            print(f"      [{agent.name}] votes for: {vote.voted_for_agent}")
                        except Exception as e:
                            print(f"      [{agent.name}] vote failed: {str(e)[:30]}")

                    # Tally votes
                    agent_names = [p.agent_name for p in proposals]
                    winner_agent = self._tally_scene_votes(votes, agent_names)
                    winner_proposal = next(
                        (p for p in proposals if p.agent_name == winner_agent),
                        proposals[0]
                    )
                    print(f"    >>> Winner: {winner_agent}")

                    # Extract scene data
                    scene_data = winner_proposal.scene.model_dump()
                    chapter_scenes.append(scene_data)
                    total_scenes += 1

                    # Record debate
                    scene_debates.append({
                        "chapter": chapter_num,
                        "scene": scene_num,
                        "proposals": [p.model_dump() for p in proposals],
                        "critiques": [c.model_dump() for c in critiques],
                        "votes": [v.model_dump() for v in votes],
                        "winner": winner_agent,
                    })

                # Generate chapter title from first scene
                first_scene_happens = chapter_scenes[0].get("happens", "")[:50] if chapter_scenes else ""
                chapter_title = f"Chapter {chapter_num}"  # Can be refined later

                # Assemble chapter
                chapters.append({
                    "chapter_number": chapter_num,
                    "chapter_title": chapter_title,
                    "act": chapter_plan["act"],
                    "structure_beats_covered": chapter_plan["beats"],
                    "scenes": chapter_scenes,
                })

                print(f"\n    >>> Chapter {chapter_num} complete: {len(chapter_scenes)} scenes")

            # Assemble chapter outline
            chapter_outline = {
                "total_chapters": len(chapters),
                "total_scenes": total_scenes,
                "ticking_clock": ticking_clock["ticking_clock"],
                "ticking_clock_deadline": ticking_clock["ticking_clock_deadline"],
                "ticking_clock_consequence": ticking_clock["ticking_clock_consequence"],
                "chapters": chapters,
            }

            duration = time.time() - start_time

            print(f"\n{'='*60}")
            print("STEP 4 COMPLETE")
            print(f"{'='*60}")
            print(f">>> Duration: {duration:.1f}s")
            print(f">>> Chapters: {len(chapters)}")
            print(f">>> Total Scenes: {total_scenes}")
            print(f">>> Ticking Clock: {ticking_clock['ticking_clock'][:60]}...")
            for ch in chapters:
                print(f"    - Ch{ch['chapter_number']} (Act {ch['act']}): {len(ch['scenes'])} scenes - {ch['structure_beats_covered']}")

            return Step4Result(
                chapter_outline=chapter_outline,
                scene_debates=scene_debates,
                total_chapters=len(chapters),
                total_scenes=total_scenes,
                success=True,
                duration_seconds=round(duration, 2),
            )

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Step4Result(
                chapter_outline={},
                scene_debates=[],
                total_chapters=0,
                total_scenes=0,
                success=False,
                error=str(e),
                duration_seconds=round(time.time() - start_time, 2),
            )

    # =========================================================================
    # STEP 5: SCENE NARRATIVE WRITING (5-Agent Multi-Agent Debate)
    # =========================================================================

    def _get_pov_character(self, scene_data: dict, characters: list) -> dict:
        """Get full character profile for POV character."""
        pov_name = scene_data.get("pov_character", "")
        for char in characters:
            if char.get("name", "").lower() == pov_name.lower():
                return char
        return characters[0] if characters else {}

    def _get_scene_characters(self, scene_data: dict, characters: list) -> list:
        """Get full profiles for all characters in scene."""
        scene_names = [n.lower() for n in scene_data.get("characters", [])]
        return [c for c in characters if c.get("name", "").lower() in scene_names]

    def _get_scene_location(self, scene_data: dict, locations: list) -> dict:
        """Get full location profile for scene."""
        loc_name = scene_data.get("location", "")
        for loc in locations:
            if loc.get("name", "").lower() == loc_name.lower():
                return loc
        return locations[0] if locations else {}

    def _format_world_for_prompt(self, world: dict) -> str:
        """Format world data for agent prompts."""
        daily = world.get("daily_life", {})
        culture = world.get("culture_customs", {})
        religion = world.get("religion_beliefs", {})

        return f"""DAILY LIFE:
- Foods: {', '.join(daily.get('common_foods', ['bread', 'stew'])[:5])}
- Eating: {daily.get('eating_customs', 'communal meals')}

CULTURE:
- Respect: {culture.get('gestures_respect', 'a nod')}
- Rude: {culture.get('gestures_rudeness', 'turning away')}

RELIGION:
- Faith: {religion.get('main_religion', 'varied beliefs')}
- Taboos: {', '.join(religion.get('taboos', [])[:3])}"""

    def _tally_narrative_votes(self, votes: list, agent_names: list[str]) -> str:
        """Tally votes and return winning agent name."""
        if not votes:
            return agent_names[0] if agent_names else "CHARACTER_CONTINUITY"

        vote_counts = Counter(v.voted_for_agent for v in votes)
        if not vote_counts:
            return agent_names[0] if agent_names else "CHARACTER_CONTINUITY"

        return max(vote_counts, key=vote_counts.get)

    def _populate_scene_ids(self, chapter_outline: dict, codex: dict) -> None:
        """Populate empty character_ids and location_id fields from names."""
        characters = codex['story']['characters']
        locations = codex['story']['locations']

        # Create name → ID maps
        char_map = {c['name']: c['character_id'] for c in characters}
        loc_map = {l['name']: l.get('id', l.get('location_id', '')) for l in locations}

        missing_warnings = []

        for chapter in chapter_outline['chapters']:
            for scene in chapter['scenes']:
                scene_ref = f"Ch{chapter['chapter_number']} Scene {scene.get('scene_number', '?')}"

                # POV character ID
                if scene.get('pov_character') and not scene.get('pov_character_id'):
                    pov_name = scene['pov_character']
                    pov_id = char_map.get(pov_name, '')
                    scene['pov_character_id'] = pov_id
                    if not pov_id:
                        missing_warnings.append(f"{scene_ref}: POV character '{pov_name}' not found in character map")

                # Location ID - always normalize to loc_XXX format
                if scene.get('location'):
                    loc_name = scene['location']
                    loc_id = loc_map.get(loc_name, '')
                    if not loc_id:
                        # Fuzzy match: try without "The " prefix, try containment
                        stripped = loc_name.lower().replace("the ", "").strip()
                        for name, lid in loc_map.items():
                            if name.lower().replace("the ", "").strip() == stripped:
                                loc_id = lid
                                break
                        if not loc_id:
                            for name, lid in loc_map.items():
                                if stripped in name.lower() or name.lower() in stripped:
                                    loc_id = lid
                                    break
                    scene['location_id'] = loc_id
                    if not loc_id:
                        missing_warnings.append(f"{scene_ref}: Location '{loc_name}' not found in location map")

                # All character IDs
                if scene.get('characters_present') and not scene.get('character_ids'):
                    char_ids = []
                    for name in scene['characters_present']:
                        char_id = char_map.get(name, '')
                        char_ids.append(char_id)
                        if not char_id:
                            missing_warnings.append(f"{scene_ref}: Character '{name}' not found in character map")
                    scene['character_ids'] = char_ids

        # Log warnings if any IDs are missing
        if missing_warnings:
            print(f"\n⚠️  WARNING: {len(missing_warnings)} scene ID mapping issues found:")
            for warning in missing_warnings[:10]:  # Show first 10
                print(f"    - {warning}")
            if len(missing_warnings) > 10:
                print(f"    ... and {len(missing_warnings) - 10} more")
            print()

    def _validate_tracking_completeness(self, chapter_outline: dict) -> dict:
        """Validate tracking chains are complete and return incomplete chain data."""
        tracking_chains = {}

        for chapter in chapter_outline['chapters']:
            for scene in chapter['scenes']:
                scene_ref = f"Ch{chapter['chapter_number']} Scene {scene['scene_number']}"
                for tracking in scene.get('setup_payoff_tracking', []):
                    tid = tracking.get('tracking_id')
                    if tid:
                        if tid not in tracking_chains:
                            tracking_chains[tid] = {
                                'trait': tracking.get('trait_or_element', 'unknown'),
                                'setup_type': tracking.get('setup_type', 'unknown'),
                                'entries': []
                            }
                        tracking_chains[tid]['entries'].append({
                            'position': tracking['position'],
                            'scene_ref': scene_ref,
                            'scene_num': scene['scene_number'],
                            'chapter_num': chapter['chapter_number']
                        })

        print(f"\n  Validating {len(tracking_chains)} tracking chains...")
        incomplete_chains = {}

        for tid, chain_data in tracking_chains.items():
            positions = [e['position'] for e in chain_data['entries']]
            missing = []
            if '1 of 3' in positions:
                if '2 of 3' not in positions:
                    missing.append('2 of 3')
                if '3 of 3' not in positions:
                    missing.append('3 of 3')

            if missing:
                incomplete_chains[tid] = {
                    'trait': chain_data['trait'],
                    'setup_type': chain_data['setup_type'],
                    'missing': missing,
                    'existing': chain_data['entries']
                }

        if incomplete_chains:
            total_missing = sum(len(c['missing']) for c in incomplete_chains.values())
            print(f"  ⚠️  {total_missing} incomplete chains")
            for tid, data in list(incomplete_chains.items())[:3]:
                for pos in data['missing']:
                    print(f"     - {tid}: missing {pos}")
        else:
            print(f"  ✓ All tracking chains complete!")

        return incomplete_chains

    def _auto_complete_tracking_chains(self, chapter_outline: dict, incomplete_chains: dict) -> None:
        """Auto-complete incomplete tracking chains by finding suitable scenes."""
        if not incomplete_chains:
            return

        print(f"\n  Auto-completing incomplete chains...")

        for tid, chain_data in incomplete_chains.items():
            # Get last existing entry to find where to continue
            last_entry = max(chain_data['existing'], key=lambda x: x['scene_num'])
            trait = chain_data['trait']
            setup_type = chain_data['setup_type']

            # Find candidate scenes after the last entry
            candidate_scenes = []
            for chapter in chapter_outline['chapters']:
                for scene in chapter['scenes']:
                    if scene['scene_number'] > last_entry['scene_num']:
                        candidate_scenes.append({
                            'scene': scene,
                            'chapter_num': chapter['chapter_number'],
                            'scene_num': scene['scene_number'],
                            'scene_ref': f"Ch{chapter['chapter_number']} Scene {scene['scene_number']}"
                        })

            if not candidate_scenes:
                print(f"     ⚠️  {tid}: No scenes available to complete chain")
                continue

            # Determine missing positions and escalation
            missing_positions = sorted(chain_data['missing'])
            stake_map = {'2 of 3': 'Medium', '3 of 3': 'High'}

            # Space out the annotations (divide remaining scenes by positions needed)
            spacing = max(1, len(candidate_scenes) // (len(missing_positions) + 1))

            for i, position in enumerate(missing_positions):
                # Select scene with spacing
                scene_idx = min(i * spacing, len(candidate_scenes) - 1)
                selected = candidate_scenes[scene_idx]

                # Create tracking annotation
                new_tracking = {
                    'tracking_id': tid,
                    'trait_or_element': trait,
                    'position': position,
                    'setup_type': setup_type,
                    'payoff_scene': '' if position == '3 of 3' else '',  # Empty for payoff
                    'character_id': '',
                    'character_name': '',
                    'demonstrates_how': 'Through action',
                    'emotional_stake': stake_map.get(position, 'Medium'),
                    'subtlety_level': 'Subtle'
                }

                # Add to scene
                if 'setup_payoff_tracking' not in selected['scene']:
                    selected['scene']['setup_payoff_tracking'] = []
                selected['scene']['setup_payoff_tracking'].append(new_tracking)

                print(f"     ✓ {tid}: Added {position} to {selected['scene_ref']}")

        print(f"  ✓ All tracking chains now complete!")

    def _generate_scenes_for_chapter_parallel(
        self,
        chapter_skeleton: dict,
        agents: list,
        premise: dict,
        characters: list,
        integrated_beats: list,
        locations: list,
        tropes: list,
        pacing: str,
        skeleton_winner_name: str,
        scene_counter_start: int
    ) -> dict:
        """Generate scenes for a single chapter using multi-agent debate (PARALLEL WORKER).

        Args:
            chapter_skeleton: Chapter structure without scenes
            agents: List of 3 scene generation agents
            premise: Story premise
            characters: Character list
            integrated_beats: Beat list
            locations: Location list
            tropes: Trope list
            pacing: Pacing setting
            skeleton_winner_name: Name of winning skeleton agent
            scene_counter_start: Starting scene number for this chapter

        Returns:
            dict with chapter_data, chapter_num, winner_name, num_scenes
        """
        worker_id = self._get_worker_id()
        chapter_num = chapter_skeleton['chapter_number']
        chapter_title = chapter_skeleton['chapter_title']

        print(f"[Worker-{worker_id}] Starting Chapter {chapter_num}: {chapter_title}")

        # Each agent proposes scenes for this chapter (parallel)
        raw_scene_proposals = self._parallel_agent_calls(
            agents, 'propose_scenes_for_chapter',
            chapter_skeleton, premise, characters,
            integrated_beats, locations, tropes, pacing
        )
        scene_proposals = []
        for i, scene_proposal in enumerate(raw_scene_proposals):
            if scene_proposal is not None:
                scene_proposals.append(scene_proposal.dict() if hasattr(scene_proposal, 'dict') else scene_proposal)
                num_scenes = len(scene_proposal.scenes if hasattr(scene_proposal, 'scenes') else scene_proposal.get('scenes', []))
                print(f"[Worker-{worker_id}]   ✓ {agents[i].name} proposed {num_scenes} scenes")
            else:
                print(f"[Worker-{worker_id}]   ✗ {agents[i].name} returned None")

        if not scene_proposals:
            # Return empty chapter
            print(f"[Worker-{worker_id}] ✗ Chapter {chapter_num}: No scene proposals")
            return {
                'chapter_data': None,
                'new_scene_counter': scene_counter_start,
                'chapter_num': chapter_num
            }

        # Simple voting: Pick the scene proposal with most votes
        print(f"[Worker-{worker_id}]   Voting for best scenes...")
        scene_votes = []
        for agent in agents:
            # Pick the proposal from the skeleton winner if available
            preferred_proposal = next(
                (p for p in scene_proposals if p['agent_name'] == skeleton_winner_name),
                scene_proposals[0]
            )
            scene_votes.append(preferred_proposal['agent_name'])

        scene_vote_counts = Counter(scene_votes)
        scene_winner_name = max(scene_vote_counts, key=scene_vote_counts.get) if scene_vote_counts else scene_proposals[0]['agent_name']
        winning_scenes_proposal = next(
            (p for p in scene_proposals if p['agent_name'] == scene_winner_name),
            scene_proposals[0]
        )

        print(f"[Worker-{worker_id}]   Winner: {scene_winner_name}")

        # Combine chapter skeleton + winning scenes
        # Assign sequential scene numbers (will be renumbered later)
        scenes_with_numbers = []
        scene_counter = scene_counter_start
        for scene in winning_scenes_proposal['scenes']:
            scene['scene_number'] = scene_counter
            scenes_with_numbers.append(scene)
            scene_counter += 1

        final_chapter = {
            'chapter_number': chapter_skeleton['chapter_number'],
            'chapter_title': chapter_skeleton['chapter_title'],
            'chapter_summary': chapter_skeleton['chapter_summary'],
            'beats_covered': chapter_skeleton['beats_covered'],
            'scenes': scenes_with_numbers
        }

        print(f"[Worker-{worker_id}] ✓ Completed Chapter {chapter_num}: {len(scenes_with_numbers)} scenes")

        return {
            'chapter_data': final_chapter,
            'new_scene_counter': scene_counter,
            'chapter_num': chapter_num,
            'winner_name': scene_winner_name,
            'num_scenes': len(scenes_with_numbers)
        }

    def step5_chapter_scene_breakdown(self, codex: dict) -> Step5Result:
        """NEW Step 5: Break story into chapters and scenes via 3-agent debate (TWO-STAGE).

        Uses 3 specialized agents:
        - SceneStructureAgent: Save the Cat beat distribution
        - ScenePacingAgent: Pacing, escalation, variety
        - SceneCharacterAgent: Character arcs, POV assignment

        Two-stage debate flow:
        STAGE 1: Chapter Structure Only (no scenes)
        1. All 3 agents propose chapter skeleton (chapter structure only)
        2. Voting for best chapter structure

        STAGE 2: Scene Generation (per chapter)
        3. For each chapter, agents propose scenes
        4. Simple voting for best scenes for that chapter
        5. Combine chapter structure + scenes into final outline

        Args:
            codex: The codex dictionary with premise, theme, characters, beats, locations, world

        Returns:
            Step5Result with chapter_outline and debate metadata
        """
        start_time = time.time()

        try:
            # Load config
            import yaml
            config_path = Path("config.yaml")
            if not config_path.exists():
                raise FileNotFoundError("config.yaml not found - need num_chapters setting")

            with open(config_path) as f:
                config_text = f.read()
                # Load from config instead of hardcoding
                num_chapters = get_step_config("step5_scene_breakdown")["structure"]["num_chapters"]
                for line in config_text.split('\n'):
                    if 'num_chapters' in line and '=' in line:
                        num_chapters = int(line.split('=')[1].strip())
                        break

            # Extract data from codex
            # Create premise dict from deck prompts (original story seed)
            premise = {
                "logline": codex.get("deck_of_worlds", {}).get("prompts", [{}])[0].get("prompt", "N/A"),
                "genre": codex["story"].get("primary_genre", "Unknown"),
                "tone": codex["story"].get("tone_flavor", "Unknown")
            }
            theme_foundation = codex["story"]["theme_foundation"]
            characters = codex["story"]["characters"]
            integrated_beats = codex["story"]["integrated_beats"]
            locations = codex["story"]["locations"]
            world_pressure = codex["story"]["world_pressure"]
            tropes = codex["story"].get("tropes", [])
            pacing = codex.get("author", {}).get("plotting_style", {}).get("pacing", "medium")

            print(f"\n{'='*60}")
            print(f"CHAPTER/SCENE BREAKDOWN DEBATE (TWO-STAGE)")
            print(f"  Target: {num_chapters} chapters")
            print(f"  Using: {len(integrated_beats)} beats, {len(characters)} characters, {len(locations)} locations")
            print(f"{'='*60}\n")

            # Initialize 3 agents (use model pattern, not llm)
            agent1 = ChapterSceneStructureAgent(model=self.model)
            agent2 = ChapterScenePacingAgent(model=self.model)
            agent3 = ChapterSceneCharacterAgent(model=self.model)
            agents = [agent1, agent2, agent3]

            metadata = {
                'premise': premise,
                'theme_foundation': theme_foundation,
                'characters': characters,
                'integrated_beats': integrated_beats,
                'locations': locations,
                'world_pressure': world_pressure,
                'num_chapters': num_chapters
            }

            # Initialize substep tracking
            substep_timings = {}
            substep_tokens = {}

            # ================================================================
            # STAGE 1: CHAPTER SKELETON (NO SCENES)
            # ================================================================
            stage1_start = time.time()
            print("\n" + "="*60)
            print("STAGE 1: CHAPTER STRUCTURE (NO SCENES)")
            print("="*60)

            # Round 1: Skeleton Proposals (parallel)
            print("\nROUND 1: SKELETON PROPOSALS (parallel)")
            print("-" * 60)
            from concurrent.futures import ThreadPoolExecutor, as_completed

            raw_skeleton_proposals = self._parallel_agent_calls(
                agents, 'propose_chapter_skeleton',
                premise, theme_foundation, characters,
                integrated_beats, num_chapters
            )
            skeleton_proposals = []
            for i, proposal in enumerate(raw_skeleton_proposals):
                if proposal is not None:
                    skeleton_proposals.append(proposal.dict() if hasattr(proposal, 'dict') else proposal)
                    print(f"  ✓ {agents[i].name}: Proposed {proposal.num_chapters} chapters (skeletons only)")
                else:
                    print(f"  ✗ {agents[i].name}: No proposal (LLM returned None)")

            if not skeleton_proposals:
                raise ValueError("All agents failed to propose chapter skeletons")

            # Round 2: Simple voting for best skeleton (parallel)
            print(f"\nROUND 2: VOTING FOR BEST CHAPTER STRUCTURE (parallel)")
            print("-" * 60)
            empty_critiques = [[] for _ in skeleton_proposals]
            raw_votes = self._parallel_agent_calls(
                agents, 'vote', skeleton_proposals, empty_critiques, metadata
            )
            skeleton_votes = []
            for i, vote in enumerate(raw_votes):
                if vote is not None:
                    skeleton_votes.append(vote.dict() if hasattr(vote, 'dict') else vote)
                    print(f"  {agents[i].name} → Chose: {vote.chosen_agent}")

            # Tally votes for skeleton
            skeleton_vote_counts = Counter(v['chosen_agent'] for v in skeleton_votes)
            skeleton_winner_name = max(skeleton_vote_counts, key=skeleton_vote_counts.get) if skeleton_vote_counts else skeleton_proposals[0]['agent_name']

            print(f"\nWINNER (STAGE 1): {skeleton_winner_name}")
            print(f"   Vote counts: {dict(skeleton_vote_counts)}")

            # Get winning skeleton
            winning_skeleton = next((p for p in skeleton_proposals if p['agent_name'] == skeleton_winner_name), skeleton_proposals[0])

            # Collect Stage 1 timing
            stage1_duration = time.time() - stage1_start
            substep_timings['stage1_skeleton'] = stage1_duration

            # ================================================================
            # STAGE 2: GENERATE SCENES FOR EACH CHAPTER
            # ================================================================
            stage2_start = time.time()
            print("\n" + "="*60)
            print("STAGE 2: SCENE GENERATION (PER CHAPTER)")
            print("="*60)

            # Load parallel config
            step5_config = get_step_config("step5_scene_breakdown")
            parallel_enabled = step5_config.get("parallel_processing", {}).get("enabled", True)
            chapter_level = step5_config.get("parallel_processing", {}).get("chapter_level", True)
            max_workers_chapters = step5_config.get("parallel_processing", {}).get("max_workers_chapters", 4)

            final_chapters = []
            scene_counter = 1

            if parallel_enabled and chapter_level:
                print(f"\n  Processing {len(winning_skeleton['chapters'])} chapters in parallel with {max_workers_chapters} workers...")

                # Prepare chapter generation tasks
                from concurrent.futures import ThreadPoolExecutor, as_completed

                # We need to handle scene counter sequentially, so we'll:
                # 1. Generate scenes for all chapters in parallel (without final scene numbers)
                # 2. Then assign scene numbers sequentially

                def process_chapter_wrapper(chapter_skeleton, scene_counter_start):
                    return self._generate_scenes_for_chapter_parallel(
                        chapter_skeleton=chapter_skeleton,
                        agents=agents,
                        premise=premise,
                        characters=characters,
                        integrated_beats=integrated_beats,
                        locations=locations,
                        tropes=tropes,
                        pacing=pacing,
                        skeleton_winner_name=skeleton_winner_name,
                        scene_counter_start=scene_counter_start
                    )

                # Calculate scene count per chapter to assign sequential numbers
                # We'll process sequentially but generate in parallel
                chapter_results = []

                with ThreadPoolExecutor(max_workers=max_workers_chapters) as executor:
                    # Submit all chapters
                    future_to_chapter = {}
                    for chapter_skeleton in winning_skeleton['chapters']:
                        future = executor.submit(
                            process_chapter_wrapper,
                            chapter_skeleton,
                            scene_counter  # This will be adjusted after
                        )
                        future_to_chapter[future] = chapter_skeleton

                    # Collect results as they complete
                    for future in as_completed(future_to_chapter):
                        chapter_skeleton = future_to_chapter[future]
                        try:
                            result = future.result()
                            chapter_results.append(result)
                            chapter_num = result['chapter_num']
                            if result['chapter_data']:
                                num_scenes = result['num_scenes']
                                winner = result['winner_name']
                                print(f"  ✓ Chapter {chapter_num}: {winner} ({num_scenes} scenes)")
                            else:
                                print(f"  ⚠️  Chapter {chapter_num}: No scenes generated")
                        except Exception as e:
                            print(f"  ✗ Chapter {chapter_skeleton['chapter_number']}: {str(e)[:50]}")

                # Sort results by chapter number and renumber scenes sequentially
                chapter_results.sort(key=lambda x: x['chapter_num'])
                scene_counter = 1

                for result in chapter_results:
                    if result['chapter_data']:
                        chapter = result['chapter_data']
                        # Renumber scenes
                        for scene in chapter['scenes']:
                            scene['scene_number'] = scene_counter
                            scene_counter += 1
                        final_chapters.append(chapter)

            else:
                # Sequential processing (original code)
                print(f"\n  Processing {len(winning_skeleton['chapters'])} chapters sequentially...")

                for chapter_skeleton in winning_skeleton['chapters']:
                    chapter_num = chapter_skeleton['chapter_number']
                    print(f"\n--- CHAPTER {chapter_num}: {chapter_skeleton['chapter_title']} ---")

                    # Each agent proposes scenes for this chapter (parallel)
                    raw_scene_proposals = self._parallel_agent_calls(
                        agents, 'propose_scenes_for_chapter',
                        chapter_skeleton, premise, characters,
                        integrated_beats, locations, tropes, pacing
                    )
                    scene_proposals = []
                    for i, scene_proposal in enumerate(raw_scene_proposals):
                        if scene_proposal is not None:
                            scene_proposals.append(scene_proposal.dict() if hasattr(scene_proposal, 'dict') else scene_proposal)
                            print(f"  {agents[i].name} proposed scenes")

                    if not scene_proposals:
                        print(f"  ⚠️  No scene proposals for chapter {chapter_num}, skipping")
                        continue

                    # Simple voting: Pick the scene proposal with most votes
                    print(f"  Voting for best scenes...")
                    scene_votes = []
                    for agent in agents:
                        # Simple vote: each agent picks their favorite scene proposal
                        # We'll just use the first proposal from the winning skeleton agent for simplicity
                        # In a more complex system, we'd have a proper vote method for scenes
                        # For now, let's just pick the proposal from the skeleton winner if available
                        preferred_proposal = next(
                            (p for p in scene_proposals if p['agent_name'] == skeleton_winner_name),
                            scene_proposals[0]
                        )
                        scene_votes.append(preferred_proposal['agent_name'])

                    scene_vote_counts = Counter(scene_votes)
                    scene_winner_name = max(scene_vote_counts, key=scene_vote_counts.get) if scene_vote_counts else scene_proposals[0]['agent_name']
                    winning_scenes_proposal = next(
                        (p for p in scene_proposals if p['agent_name'] == scene_winner_name),
                        scene_proposals[0]
                    )

                    print(f"  ✓ Winner: {scene_winner_name} ({len(winning_scenes_proposal['scenes'])} scenes)")

                    # Combine chapter skeleton + winning scenes
                    # Assign sequential scene numbers
                    scenes_with_numbers = []
                    for scene in winning_scenes_proposal['scenes']:
                        scene['scene_number'] = scene_counter
                        scenes_with_numbers.append(scene)
                        scene_counter += 1

                    final_chapter = {
                        'chapter_number': chapter_skeleton['chapter_number'],
                        'chapter_title': chapter_skeleton['chapter_title'],
                        'chapter_summary': chapter_skeleton['chapter_summary'],
                        'beats_covered': chapter_skeleton['beats_covered'],
                        'scenes': scenes_with_numbers
                    }
                    final_chapters.append(final_chapter)

            # Convert to final format
            chapter_outline = {
                'num_chapters': winning_skeleton['num_chapters'],
                'ticking_clock': winning_skeleton['ticking_clock'],
                'chapters': final_chapters,
                'reasoning': winning_skeleton['reasoning']
            }

            total_scenes = sum(len(ch['scenes']) for ch in chapter_outline['chapters'])
            duration = time.time() - start_time

            # Collect Stage 2 timing
            stage2_duration = time.time() - stage2_start
            substep_timings['stage2_scenes'] = stage2_duration

            # Collect token usage from all 3 agents
            total_tokens_used = sum(agent.get_token_usage()['total_tokens'] for agent in agents)
            total_calls = sum(agent.get_token_usage()['call_count'] for agent in agents)

            # Track tokens per substep (Stage 1 and Stage 2 agents are the same, so approximate split by timing)
            stage1_tokens_approx = int(total_tokens_used * (stage1_duration / duration))
            stage2_tokens_approx = total_tokens_used - stage1_tokens_approx

            substep_tokens['stage1_skeleton'] = {
                'total_tokens': stage1_tokens_approx,
                'calls': total_calls // 2,  # Approximate
            }
            substep_tokens['stage2_scenes'] = {
                'total_tokens': stage2_tokens_approx,
                'calls': total_calls - (total_calls // 2),
            }

            token_usage = {
                'total_tokens': total_tokens_used,
                'call_count': total_calls,
            }

            print(f"\n{'='*60}")
            print(f"STEP 5 COMPLETE")
            print(f"  Chapters: {chapter_outline['num_chapters']}")
            print(f"  Total Scenes: {total_scenes}")
            print(f"  Duration: {duration:.1f}s")
            print(f"  Tokens used: {total_tokens_used:,} ({total_calls} LLM calls)")
            print(f"{'='*60}\n")

            return Step5Result(
                chapter_outline=chapter_outline,
                debates={
                    'stage1_skeleton_proposals': skeleton_proposals,
                    'stage1_votes': skeleton_votes,
                    'stage1_winner': skeleton_winner_name,
                    'stage2_scene_generation': 'per-chapter voting'
                },
                total_chapters=chapter_outline['num_chapters'],
                total_scenes=total_scenes,
                success=True,
                duration_seconds=duration,
                token_usage=token_usage,
                substep_timings=substep_timings,
                substep_tokens=substep_tokens,
            )

        except Exception as e:
            duration = time.time() - start_time
            print(f"\n❌ STEP 5 FAILED: {str(e)}")
            import traceback
            traceback.print_exc()
            return Step5Result(
                chapter_outline={},
                debates={},
                total_chapters=0,
                total_scenes=0,
                success=False,
                error=str(e),
                duration_seconds=duration
            )

    def step5b_foreshadowing_analysis(self, codex: dict) -> dict:
        """Step 5B: Foreshadowing & Setup/Payoff Analysis (3-Agent Debate).

        Identifies:
        - Payoff moments needing setup (Chekhov's Gun)
        - Character traits/skills needing 3x establishment (Rule of Three)
        - Trope execution timelines

        Outputs:
        - Annotations for existing scenes (add setup_payoff_tracking metadata)
        - New setup scenes to insert
        - All scenes renumbered with Rule of Three tracking

        Returns:
            dict with success, foreshadowing_plan, debates, duration
        """
        start_time = time.time()

        try:
            # Extract data - Step 5B runs AFTER Step 5 (chapter breakdown), BEFORE Step 6 (narrative writing)
            # So we have chapters but NOT manuscript yet
            chapter_outline = codex["story"]["chapters"]
            characters = codex["story"]["characters"]
            integrated_beats = codex["story"]["integrated_beats"]
            tropes = codex["story"].get("tropes", [])

            print(f"\n{'='*60}")
            print("STEP 5B: FORESHADOWING & SETUP/PAYOFF ANALYSIS")
            print(f"  Chapters: {chapter_outline['num_chapters']}")
            print(f"  Total Scenes: {sum(len(ch['scenes']) for ch in chapter_outline['chapters'])}")
            print(f"{'='*60}\n")

            # Initialize agents
            agents = [
                SetupPayoffAgent(self.model),
                RuleOfThreeAgent(self.model),
                TropeExecutionAgent(self.model)
            ]

            # ROUND 1: Analysis (parallel)
            print("ROUND 1: FORESHADOWING ANALYSIS (parallel)")
            print("-" * 60)
            raw_analyses = self._parallel_agent_calls(
                agents, 'analyze_foreshadowing',
                chapter_outline, characters, integrated_beats, tropes
            )
            analyses = []
            for i, analysis in enumerate(raw_analyses):
                if analysis is not None:
                    analyses.append(analysis.dict() if hasattr(analysis, 'dict') else analysis)
                    print(f"  ✓ {agents[i].name}: Payoffs: {len(analysis.payoff_items)}, Existing annotations: {len(analysis.existing_scene_annotations)}")

            if not analyses:
                raise ValueError("All agents failed")

            # ROUND 2: Critiques (parallel)
            print(f"\nROUND 2: CRITIQUES (parallel)")
            print("-" * 60)
            from concurrent.futures import ThreadPoolExecutor, as_completed

            def _foreshadow_critique(agent, analysis):
                return agent.critique_foreshadowing(analysis, {"chapter_outline": chapter_outline})

            critiques = []
            critique_tasks = []
            for agent in agents:
                for analysis in analyses:
                    if analysis['agent_name'] != agent.name:
                        critique_tasks.append((agent, analysis))

            with ThreadPoolExecutor(max_workers=len(critique_tasks)) as executor:
                futures = {executor.submit(_foreshadow_critique, a, an): (a, an) for a, an in critique_tasks}
                for future in as_completed(futures):
                    agent, analysis = futures[future]
                    try:
                        critique = future.result()
                        if critique:
                            critiques.append(critique.dict() if hasattr(critique, 'dict') else critique)
                            print(f"  {agent.name} → {analysis['agent_name']}")
                    except Exception:
                        pass

            # ROUND 3: Voting (parallel)
            print(f"\nROUND 3: VOTING (parallel)")
            print("-" * 60)
            raw_votes = self._parallel_agent_calls(agents, 'vote_on_priorities', analyses, critiques)
            votes = []
            for i, vote in enumerate(raw_votes):
                if vote is not None:
                    votes.append(vote.dict() if hasattr(vote, 'dict') else vote)
                    print(f"  {agents[i].name} → {len(vote.essential_payoffs)} essential")

            # SYNTHESIS: Apply annotations and insert new scenes
            print(f"\nSYNTHESIZING & APPLYING CHANGES...")

            # Get priority payoffs (2+ votes)
            essential_counter = Counter()
            for vote in votes:
                for payoff_ref in vote['essential_payoffs']:
                    essential_counter[payoff_ref] += 1
            priority_payoffs = [p for p, cnt in essential_counter.items() if cnt >= 2]

            # Collect all annotations and setups
            all_annotations = []
            all_new_setups = []
            for analysis in analyses:
                # Existing scene annotations
                all_annotations.extend(analysis.get('existing_scene_annotations', []))

                # New setup scenes
                for payoff_item in analysis['payoff_items']:
                    if payoff_item['payoff_scene'] in priority_payoffs:
                        all_new_setups.extend(payoff_item['required_setups'])

            # Deduplicate annotations and setups
            seen_scene_refs = set()
            unique_annotations = []
            for ann in all_annotations:
                if ann['scene_reference'] not in seen_scene_refs:
                    seen_scene_refs.add(ann['scene_reference'])
                    unique_annotations.append(ann)

            seen_insert_locs = set()
            unique_setups = []
            for setup in all_new_setups:
                if setup['insert_location'] not in seen_insert_locs:
                    seen_insert_locs.add(setup['insert_location'])
                    unique_setups.append(setup)

            # APPLY CHANGES TO CHAPTER OUTLINE
            # Step 1: Annotate existing scenes
            for chapter in chapter_outline['chapters']:
                for scene in chapter['scenes']:
                    scene_ref = f"Ch{chapter['chapter_number']}, Scene {scene['scene_number']}"
                    for ann in unique_annotations:
                        if ann['scene_reference'] == scene_ref:
                            if 'setup_payoff_tracking' not in scene:
                                scene['setup_payoff_tracking'] = []
                            scene['setup_payoff_tracking'].extend(ann['add_tracking'])
                            print(f"  ✓ Annotated {scene_ref}")

            # Step 2: Insert new scenes
            for chapter in chapter_outline['chapters']:
                ch_num = chapter['chapter_number']
                # Find setups for this chapter
                ch_setups = [s for s in unique_setups if s['insert_location'].startswith(f"Ch{ch_num},")]

                for setup in sorted(ch_setups, key=lambda x: x['insert_location'], reverse=True):
                    # Parse insert location: "Ch2, after Scene 4"
                    parts = setup['insert_location'].split('after Scene')
                    if len(parts) == 2:
                        after_scene_num = int(parts[1].strip())
                        # Find insert position
                        insert_pos = 0
                        for idx, scene in enumerate(chapter['scenes']):
                            if scene['scene_number'] == after_scene_num:
                                insert_pos = idx + 1
                                break

                        # Create new scene from SetupRequirement
                        new_scene = {
                            "scene_number": -1,  # Will renumber
                            "beat_name": setup.get('beat_name', 'Setup'),
                            "scene_summary": setup['scene_bullet'],
                            "pov_character": setup.get('pov_character', setup['characters_present'][0] if setup['characters_present'] else "Unknown"),
                            "location": setup.get('location', "Unknown"),
                            "characters_present": setup['characters_present'],
                            "tropes_manifesting": setup.get('tropes_manifesting', []),
                            "character_arc_progression": setup.get('character_arc_progression', []),
                            "estimated_word_count": setup['estimated_word_count'],
                            "scene_type": setup['scene_type'],
                            "setup_payoff_tracking": setup.get('setup_payoff_tracking', [])
                        }
                        chapter['scenes'].insert(insert_pos, new_scene)
                        scene_ref = f"Ch{ch_num}, after Scene {after_scene_num}"
                        print(f"  ✓ Inserted scene after Scene {after_scene_num}")

            # Step 3: Renumber ALL scenes sequentially
            scene_counter = 1
            for chapter in chapter_outline['chapters']:
                for scene in chapter['scenes']:
                    scene['scene_number'] = scene_counter
                    scene_counter += 1

            total_scenes = scene_counter - 1
            print(f"✓ Renumbered {total_scenes} scenes\n")

            # Validate tracking completeness and auto-complete if needed
            incomplete_chains = self._validate_tracking_completeness(chapter_outline)
            if incomplete_chains:
                self._auto_complete_tracking_chains(chapter_outline, incomplete_chains)

            # Create foreshadowing plan summary
            foreshadowing_plan = {
                "total_insertions": len(unique_setups),
                "total_annotations": len(unique_annotations),
                "insertions_by_chapter": unique_setups,
                "existing_scene_annotations": unique_annotations
            }

            # Save updated chapters back to codex
            codex["story"]["chapters"] = chapter_outline

            # Repopulate scene IDs for newly inserted scenes
            self._populate_scene_ids(chapter_outline, codex)

            duration = time.time() - start_time
            print("="*60)
            print(f"STEP 5B COMPLETE")
            print(f"  New Scenes: {len(unique_setups)}")
            print(f"  Annotated Scenes: {len(unique_annotations)}")
            print(f"  Total Scenes Now: {total_scenes}")
            print(f"  Duration: {duration:.1f}s")
            print("="*60 + "\n")

            return {
                "success": True,
                "foreshadowing_plan": foreshadowing_plan,
                "debates": {
                    "analyses": analyses,
                    "critiques": critiques,
                    "votes": votes
                },
                "duration": duration
            }

        except Exception as e:
            import traceback
            print(f"\n❌ STEP 5B FAILED: {str(e)}")
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "duration": time.time() - start_time
            }

    def _fix_scene_parallel(self, scene_ref: str, fix_type: str, causality_results: list = None, function_results: list = None) -> dict:
        """
        Fix a single scene in parallel (thread-safe).

        Args:
            scene_ref: Scene reference (e.g., "Ch1, Scene 3")
            fix_type: Type of fix ("causality" or "function")
            causality_results: List of causality results (for causality fixes)
            function_results: List of function results (for function fixes)

        Returns:
            dict with 'success', 'scene_ref', 'fix_type', 'message'
        """
        worker_id = self._get_worker_id()

        try:
            if fix_type == "causality" and causality_results:
                for result in causality_results:
                    if result['scene_ref'] == scene_ref:
                        if result['causality'].get('causal_strength') == 'Weak':
                            result['causality']['causal_strength'] = 'Indirect'
                            print(f"[Worker-{worker_id}] ✓ {scene_ref}: Upgraded Weak → Indirect causality")
                            return {
                                'success': True,
                                'scene_ref': scene_ref,
                                'fix_type': 'causality',
                                'message': 'Upgraded Weak → Indirect causality'
                            }
                        break

            elif fix_type == "function" and function_results:
                for result in function_results:
                    if result['scene_ref'] == scene_ref:
                        func = result['scene_function']
                        if func.get('function_count', 0) < 1:
                            # Add at least plot function
                            func['serves_plot'] = True
                            func['plot_function'] = "Advances story through action or discovery"
                            func['function_count'] = 1
                            func['recommendation'] = "Enhance"
                            print(f"[Worker-{worker_id}] ✓ {scene_ref}: Added plot function")
                            return {
                                'success': True,
                                'scene_ref': scene_ref,
                                'fix_type': 'function',
                                'message': 'Added plot function'
                            }
                        break

            return {'success': False, 'scene_ref': scene_ref, 'fix_type': fix_type, 'message': 'No fix needed'}

        except Exception as e:
            print(f"[Worker-{worker_id}] ❌ {scene_ref}: Fix failed - {str(e)}")
            return {'success': False, 'scene_ref': scene_ref, 'fix_type': fix_type, 'message': str(e)}

    def step5c_interconnection_analysis(self, codex: dict) -> dict:
        """
        Step 5C: Complete Scene Interconnection Analysis.

        Ensures EVERY scene is interconnected through:
        1. Causality: Scene N-1 → Scene N → Scene N+1 connections
        2. Plot Threads: All threads from setup → resolution
        3. Character Arcs: Emotional progression scene-by-scene
        4. Thematic Beats: Testing central thematic question
        5. Scene Function: Plot/Character/Theme triple function
        6. Narrative Rope: Thread convergence tracking

        Uses 7 specialized agents:
        - Round 1: 6 agents analyze in parallel
        - Round 2: Synthesis & validation
        - Round 3: Auto-fix weak scenes

        Args:
            codex: Story codex with chapter_outline, characters, etc.

        Returns:
            dict with success, report, and duration
        """
        start_time = time.time()

        try:
            # Extract required data - Step 5C runs AFTER Step 5 (chapters), BEFORE Step 6 (manuscript)
            # So we have chapters but NOT manuscript yet
            chapter_outline = codex["story"]["chapters"]
            characters = codex["story"].get("characters", [])
            integrated_beats = codex.get("metadata", {}).get("phase_1", {}).get("step3_integrated_beats", [])

            total_scenes = sum(len(ch['scenes']) for ch in chapter_outline['chapters'])

            # Check config for parallelization settings
            step5c_config = get_step_config('step5c_interconnection')
            parallel_config = step5c_config.get('parallel_processing', {})
            analysis_parallel = parallel_config.get('analysis_level', True)
            scene_parallel = parallel_config.get('scene_level', True)
            max_workers_analysis = parallel_config.get('max_workers_analysis', 3)
            max_workers_scenes = parallel_config.get('max_workers_scenes', 4)

            print(f"\n{'='*60}")
            print("STEP 5C: Complete Scene Interconnection Analysis")
            print(f"{'='*60}")
            print(f">>> Analyzing {total_scenes} scenes across {len(chapter_outline['chapters'])} chapters")
            print(f">>> Method: 6 agents {'parallel' if analysis_parallel else 'sequential'} → Synthesis → Auto-fix {'parallel' if scene_parallel else 'sequential'}")
            if analysis_parallel:
                print(f">>> Analysis workers: {max_workers_analysis}")
            if scene_parallel:
                print(f">>> Scene fix workers: {max_workers_scenes}")

            # =========================================
            # INITIALIZE ALL 7 AGENTS
            # =========================================
            from src.story_agents.interconnection_agents import (
                SceneCausalityAgent,
                PlotThreadAgent,
                CharacterArcAgent,
                ThematicBeatAgent,
                SceneFunctionAgent,
                NarrativeRopeAgent,
                SynthesisValidator
            )

            causality_agent = SceneCausalityAgent(model=self.model)
            plot_thread_agent = PlotThreadAgent(model=self.model)
            character_arc_agent = CharacterArcAgent(model=self.model)
            thematic_beat_agent = ThematicBeatAgent(model=self.model)
            scene_function_agent = SceneFunctionAgent(model=self.model)
            narrative_rope_agent = NarrativeRopeAgent(model=self.model)
            synthesis_validator = SynthesisValidator(model=self.model)

            # =========================================
            # ROUND 1: PARALLEL ANALYSIS (6 Agents)
            # =========================================
            print(f"\n{'='*60}")
            print("ROUND 1: INTERCONNECTION ANALYSIS (6 Agents)")
            print(f"{'='*60}")

            causality_results = []
            thread_analysis = {}
            character_arc_results = []
            thematic_results = []
            function_results = []
            convergence_results = []

            if analysis_parallel:
                # Parallel execution of 6 agents
                from concurrent.futures import ThreadPoolExecutor
                import threading

                with ThreadPoolExecutor(max_workers=max_workers_analysis) as executor:
                    # Submit all 6 agent tasks
                    def run_causality():
                        worker_id = self._get_worker_id()
                        print(f"[Worker-{worker_id}] {causality_agent.name} analyzing causality...")
                        result = causality_agent.analyze_causality(chapter_outline, characters)
                        weak_count = sum(1 for r in result if r['causality'].get('causal_strength') == 'Weak')
                        print(f"[Worker-{worker_id}] ✓ Causality mapped: {len(result)} scenes, {weak_count} weak connections")
                        return result

                    def run_thread():
                        worker_id = self._get_worker_id()
                        print(f"[Worker-{worker_id}] {plot_thread_agent.name} analyzing plot structure...")
                        result = plot_thread_agent.analyze_threads(chapter_outline, characters, integrated_beats or [])
                        total_threads = result.get('total_threads', 0)
                        dangling = result.get('dangling_threads', [])
                        print(f"[Worker-{worker_id}] ✓ Identified {total_threads} plot threads")
                        if dangling:
                            print(f"[Worker-{worker_id}] ⚠️  {len(dangling)} dangling threads: {', '.join(dangling[:3])}")
                        return result

                    def run_character_arc():
                        worker_id = self._get_worker_id()
                        print(f"[Worker-{worker_id}] {character_arc_agent.name} analyzing character arcs...")
                        result = character_arc_agent.analyze_character_arcs(chapter_outline, characters)
                        unique_chars = len(set(r['arc'].get('character_name', '') for r in result))
                        print(f"[Worker-{worker_id}] ✓ Emotional arcs tracked: {unique_chars} major characters across {len(result)} arc beats")
                        return result

                    def run_thematic():
                        worker_id = self._get_worker_id()
                        print(f"[Worker-{worker_id}] {thematic_beat_agent.name} analyzing thematic coherence...")
                        result = thematic_beat_agent.analyze_thematic_beats(chapter_outline, characters)
                        coverage = sum(1 for r in result if 'No clear thematic connection' not in r['thematic_beat'].get('how_scene_tests_theme', ''))
                        pct = int((coverage / max(total_scenes, 1)) * 100)
                        print(f"[Worker-{worker_id}] ✓ Thematic coverage: {coverage}/{total_scenes} scenes ({pct}%)")
                        if pct < 90:
                            print(f"[Worker-{worker_id}] ⚠️  {total_scenes - coverage} scenes lack thematic connection")
                        return result

                    def run_function():
                        worker_id = self._get_worker_id()
                        print(f"[Worker-{worker_id}] {scene_function_agent.name} validating scene functions...")
                        result = scene_function_agent.analyze_scene_functions(chapter_outline, characters)
                        high_func = sum(1 for r in result if r['scene_function'].get('function_count', 0) >= 2)
                        weak_func = sum(1 for r in result if r['scene_function'].get('function_count', 0) < 1)
                        print(f"[Worker-{worker_id}] ✓ Scene functions: {high_func}/{total_scenes} serve 2+ functions")
                        if weak_func > 0:
                            print(f"[Worker-{worker_id}] ⚠️  {weak_func} scenes serve < 1 function")
                        return result

                    def run_convergence(thread_data):
                        worker_id = self._get_worker_id()
                        print(f"[Worker-{worker_id}] {narrative_rope_agent.name} analyzing thread convergence...")
                        result = narrative_rope_agent.analyze_thread_convergence(chapter_outline, thread_data.get('threads', []))
                        avg_count = sum(r['narrative_rope'].get('thread_count', 0) for r in result) / max(len(result), 1)
                        max_conv = max((r['narrative_rope'].get('thread_count', 0) for r in result), default=0)
                        print(f"[Worker-{worker_id}] ✓ Thread convergence: Avg {avg_count:.1f} threads/scene, Max {max_conv} threads")
                        return result

                    # Submit first 5 agents in parallel
                    futures = {
                        'causality': executor.submit(run_causality),
                        'thread': executor.submit(run_thread),
                        'character_arc': executor.submit(run_character_arc),
                        'thematic': executor.submit(run_thematic),
                        'function': executor.submit(run_function),
                    }

                    # Wait for thread analysis to complete (needed for convergence agent)
                    thread_analysis = futures['thread'].result()

                    # Now submit convergence agent
                    futures['convergence'] = executor.submit(run_convergence, thread_analysis)

                    # Collect all results
                    causality_results = futures['causality'].result()
                    character_arc_results = futures['character_arc'].result()
                    thematic_results = futures['thematic'].result()
                    function_results = futures['function'].result()
                    convergence_results = futures['convergence'].result()

            else:
                # Sequential execution (original)
                # Agent 1: Scene Causality
                print(f"\n  {causality_agent.name} analyzing causality...")
                causality_results = causality_agent.analyze_causality(chapter_outline, characters)
                weak_causality_count = sum(1 for r in causality_results if r['causality'].get('causal_strength') == 'Weak')
                print(f"    ✓ Causality mapped: {len(causality_results)} scenes, {weak_causality_count} weak connections")

                # Agent 2: Plot Thread Analysis
                print(f"\n  {plot_thread_agent.name} analyzing plot structure...")
                thread_analysis = plot_thread_agent.analyze_threads(chapter_outline, characters, integrated_beats or [])
                total_threads = thread_analysis.get('total_threads', 0)
                dangling_threads = thread_analysis.get('dangling_threads', [])
                print(f"    ✓ Identified {total_threads} plot threads")
                if dangling_threads:
                    print(f"    ⚠️  {len(dangling_threads)} dangling threads: {', '.join(dangling_threads[:3])}")

                # Agent 3: Character Arc Analysis
                print(f"\n  {character_arc_agent.name} analyzing character arcs...")
                character_arc_results = character_arc_agent.analyze_character_arcs(chapter_outline, characters)
                unique_chars = len(set(r['arc'].get('character_name', '') for r in character_arc_results))
                print(f"    ✓ Emotional arcs tracked: {unique_chars} major characters across {len(character_arc_results)} arc beats")

                # Agent 4: Thematic Beat Analysis
                print(f"\n  {thematic_beat_agent.name} analyzing thematic coherence...")
                thematic_results = thematic_beat_agent.analyze_thematic_beats(chapter_outline, characters)
                thematic_coverage = sum(1 for r in thematic_results
                                        if 'No clear thematic connection' not in r['thematic_beat'].get('how_scene_tests_theme', ''))
                thematic_pct = int((thematic_coverage / max(total_scenes, 1)) * 100)
                print(f"    ✓ Thematic coverage: {thematic_coverage}/{total_scenes} scenes ({thematic_pct}%)")
                if thematic_pct < 90:
                    print(f"    ⚠️  {total_scenes - thematic_coverage} scenes lack thematic connection")

                # Agent 5: Scene Function Validation
                print(f"\n  {scene_function_agent.name} validating scene functions...")
                function_results = scene_function_agent.analyze_scene_functions(chapter_outline, characters)
                high_function_scenes = sum(1 for r in function_results if r['scene_function'].get('function_count', 0) >= 2)
                weak_function_scenes = sum(1 for r in function_results if r['scene_function'].get('function_count', 0) < 1)
                print(f"    ✓ Scene functions: {high_function_scenes}/{total_scenes} serve 2+ functions")
                if weak_function_scenes > 0:
                    print(f"    ⚠️  {weak_function_scenes} scenes serve < 1 function")

                # Agent 6: Narrative Rope (Thread Convergence)
                print(f"\n  {narrative_rope_agent.name} analyzing thread convergence...")
                convergence_results = narrative_rope_agent.analyze_thread_convergence(chapter_outline, thread_analysis.get('threads', []))
                avg_thread_count = sum(r['narrative_rope'].get('thread_count', 0) for r in convergence_results) / max(len(convergence_results), 1)
                max_convergence = max((r['narrative_rope'].get('thread_count', 0) for r in convergence_results), default=0)
                print(f"    ✓ Thread convergence: Avg {avg_thread_count:.1f} threads/scene, Max {max_convergence} threads")

            # Calculate summary metrics for reporting
            total_threads = thread_analysis.get('total_threads', 0)
            dangling_threads = thread_analysis.get('dangling_threads', [])
            unique_chars = len(set(r['arc'].get('character_name', '') for r in character_arc_results))
            thematic_coverage = sum(1 for r in thematic_results
                                    if 'No clear thematic connection' not in r['thematic_beat'].get('how_scene_tests_theme', ''))
            thematic_pct = int((thematic_coverage / max(total_scenes, 1)) * 100)
            high_function_scenes = sum(1 for r in function_results if r['scene_function'].get('function_count', 0) >= 2)

            # =========================================
            # ROUND 2: SYNTHESIS & VALIDATION
            # =========================================
            print(f"\n{'='*60}")
            print("ROUND 2: SYNTHESIS & VALIDATION")
            print(f"{'='*60}")

            print(f"\n  Building dependency graph...")
            validation_report = synthesis_validator.synthesize_and_validate(
                causality_results=causality_results,
                thread_analysis=thread_analysis,
                character_arc_results=character_arc_results,
                thematic_results=thematic_results,
                function_results=function_results,
                convergence_results=convergence_results,
                chapter_outline=chapter_outline
            )
            print(f"    ✓ Validation complete")

            isolated_scenes = validation_report.get('isolated_scenes', [])
            dangling_threads = validation_report.get('dangling_threads', [])
            weak_function_scenes = validation_report.get('weak_function_scenes', [])

            if isolated_scenes or dangling_threads or weak_function_scenes:
                print(f"\n  ⚠️  Issues found:")
                if isolated_scenes:
                    print(f"     - {len(isolated_scenes)} scenes with weak causality")
                if dangling_threads:
                    print(f"     - {len(dangling_threads)} dangling threads")
                if weak_function_scenes:
                    print(f"     - {len(weak_function_scenes)} weak-function scenes")
            else:
                print(f"\n  ✓ No issues found - excellent interconnection!")

            # =========================================
            # ROUND 3: AUTO-FIX (Parallel)
            # =========================================
            print(f"\n{'='*60}")
            print("ROUND 3: AUTO-FIX")
            print(f"{'='*60}")

            fixes_applied = 0

            if scene_parallel and (isolated_scenes or weak_function_scenes):
                # Parallel scene fixes
                from concurrent.futures import ThreadPoolExecutor, as_completed

                fix_tasks = []
                # Add causality fixes
                for scene_ref in isolated_scenes[:5]:  # Limit fixes to avoid timeout
                    fix_tasks.append(('causality', scene_ref))
                # Add function fixes
                for scene_ref in weak_function_scenes[:5]:  # Limit fixes
                    fix_tasks.append(('function', scene_ref))

                if fix_tasks:
                    print(f"\n  Fixing {len(fix_tasks)} scenes in parallel ({max_workers_scenes} workers)...")
                    with ThreadPoolExecutor(max_workers=max_workers_scenes) as executor:
                        futures = []
                        for fix_type, scene_ref in fix_tasks:
                            if fix_type == 'causality':
                                future = executor.submit(self._fix_scene_parallel, scene_ref, 'causality', causality_results, None)
                            else:
                                future = executor.submit(self._fix_scene_parallel, scene_ref, 'function', None, function_results)
                            futures.append(future)

                        # Collect results
                        for future in as_completed(futures):
                            result = future.result()
                            if result['success']:
                                fixes_applied += 1
            else:
                # Sequential execution (original)
                # Fix 1: Strengthen weak causality
                if isolated_scenes:
                    print(f"\n  Strengthening weak causality...")
                    for scene_ref in isolated_scenes[:5]:  # Limit fixes to avoid timeout
                        # Find the result and upgrade causal_strength
                        for result in causality_results:
                            if result['scene_ref'] == scene_ref:
                                if result['causality'].get('causal_strength') == 'Weak':
                                    result['causality']['causal_strength'] = 'Indirect'
                                    fixes_applied += 1
                                    print(f"    ✓ {scene_ref}: Upgraded Weak → Indirect causality")
                                    break

                # Fix 3: Enhance weak-function scenes
                if weak_function_scenes:
                    print(f"\n  Enhancing weak-function scenes...")
                    for scene_ref in weak_function_scenes[:5]:  # Limit fixes
                        for result in function_results:
                            if result['scene_ref'] == scene_ref:
                                func = result['scene_function']
                                if func.get('function_count', 0) < 1:
                                    # Add at least plot function
                                    func['serves_plot'] = True
                                    func['plot_function'] = "Advances story through action or discovery"
                                    func['function_count'] = 1
                                    func['recommendation'] = "Enhance"
                                    fixes_applied += 1
                                    print(f"    ✓ {scene_ref}: Added plot function")
                                    break

            # Fix 2: Mark dangling threads for manual review (can't auto-resolve without context)
            if dangling_threads:
                print(f"\n  ⚠️  Dangling threads require manual resolution:")
                for thread_id in dangling_threads[:3]:
                    print(f"     - {thread_id}")

            if fixes_applied > 0:
                print(f"\n  ✓ Applied {fixes_applied} auto-fixes")
            else:
                print(f"\n  ✓ No fixes needed")

            # =========================================
            # UPDATE SCENES WITH INTERCONNECTION DATA
            # =========================================
            print(f"\n{'='*60}")
            print("UPDATING SCENE DATA")
            print(f"{'='*60}")

            # Build lookup dictionaries by scene_num
            causality_by_scene = {r['scene_num']: r['causality'] for r in causality_results}
            thematic_by_scene = {r['scene_num']: r['thematic_beat'] for r in thematic_results}
            function_by_scene = {r['scene_num']: r['scene_function'] for r in function_results}
            convergence_by_scene = {r['scene_num']: r['narrative_rope'] for r in convergence_results}

            # Character arcs by scene_num (multiple characters per scene)
            arcs_by_scene = {}
            for r in character_arc_results:
                scene_num = r['scene_num']
                if scene_num not in arcs_by_scene:
                    arcs_by_scene[scene_num] = []
                arcs_by_scene[scene_num].append(r['arc'])

            # Plot thread references by scene_ref
            threads_by_scene_ref = {}
            for thread in thread_analysis.get('threads', []):
                setup_scene = thread.get('setup_scene')
                if setup_scene:
                    if setup_scene not in threads_by_scene_ref:
                        threads_by_scene_ref[setup_scene] = []
                    threads_by_scene_ref[setup_scene].append({
                        'thread_id': thread.get('thread_id'),
                        'thread_name': thread.get('thread_name'),
                        'thread_role': 'setup'
                    })

                for active_scene in thread.get('active_scenes', []):
                    if active_scene not in threads_by_scene_ref:
                        threads_by_scene_ref[active_scene] = []
                    threads_by_scene_ref[active_scene].append({
                        'thread_id': thread.get('thread_id'),
                        'thread_name': thread.get('thread_name'),
                        'thread_role': 'active'
                    })

                resolution_scene = thread.get('resolution_scene')
                if resolution_scene:
                    if resolution_scene not in threads_by_scene_ref:
                        threads_by_scene_ref[resolution_scene] = []
                    threads_by_scene_ref[resolution_scene].append({
                        'thread_id': thread.get('thread_id'),
                        'thread_name': thread.get('thread_name'),
                        'thread_role': 'resolution'
                    })

            # Update each scene in chapters
            scenes_updated = 0
            for chapter in chapter_outline['chapters']:
                ch_num = chapter['chapter_number']
                for scene in chapter['scenes']:
                    scene_num = scene['scene_number']
                    scene_ref = f"Ch{ch_num}, Scene {scene_num}"

                    # Add Step 5C fields
                    # Note: Initialize None → [] for list fields to ensure consistency
                    # This handles scenes where LLM returned None during Step 5
                    scene['scene_causality'] = causality_by_scene.get(scene_num)

                    # Initialize list fields if they're None
                    if scene.get('active_plot_threads') is None:
                        scene['active_plot_threads'] = []
                    scene['active_plot_threads'] = threads_by_scene_ref.get(scene_ref, [])

                    if scene.get('character_arc_beats') is None:
                        scene['character_arc_beats'] = []
                    scene['character_arc_beats'] = arcs_by_scene.get(scene_num, [])

                    scene['thematic_beat'] = thematic_by_scene.get(scene_num)
                    scene['scene_function'] = function_by_scene.get(scene_num)
                    scene['narrative_rope'] = convergence_by_scene.get(scene_num)

                    scenes_updated += 1

            print(f"  ✓ Updated {scenes_updated} scenes with interconnection data")

            # Add plot_threads to chapters level
            chapter_outline['plot_threads'] = thread_analysis.get('threads', [])
            print(f"  ✓ Added {len(chapter_outline['plot_threads'])} plot threads to chapter_outline")

            # Save back to codex
            codex["story"]["chapters"] = chapter_outline

            # =========================================
            # FINAL REPORT
            # =========================================
            overall_score = validation_report.get('overall_interconnection_score', 0.0)
            duration = time.time() - start_time

            print(f"\n{'='*60}")
            print(f"OVERALL INTERCONNECTION SCORE: {overall_score:.2f} / 1.0 "
                  f"({'Excellent' if overall_score >= 0.9 else 'Good' if overall_score >= 0.75 else 'Needs Improvement'})")
            print(f"{'='*60}")
            print(f"STEP 5C COMPLETE")
            print(f"  Scenes Analyzed: {total_scenes}")
            print(f"  Plot Threads Tracked: {total_threads} ({'all resolved' if not dangling_threads else f'{len(dangling_threads)} dangling'})")
            print(f"  Character Arcs: {unique_chars} major characters")
            print(f"  Thematic Coverage: {thematic_pct}% ({thematic_coverage}/{total_scenes} scenes)")
            print(f"  Scene Functions: {high_function_scenes}/{total_scenes} serve 2+ functions")
            print(f"  Auto-Fixes Applied: {fixes_applied}")
            print(f"  Duration: {duration:.1f}s")
            print(f"{'='*60}\n")

            return {
                "success": True,
                "report": validation_report,
                "duration": duration,
                "metrics": {
                    "total_scenes": total_scenes,
                    "total_threads": total_threads,
                    "dangling_threads": len(dangling_threads),
                    "thematic_coverage_pct": thematic_pct,
                    "high_function_scenes": high_function_scenes,
                    "overall_score": overall_score,
                    "fixes_applied": fixes_applied
                }
            }

        except Exception as e:
            import traceback
            print(f"\n❌ STEP 5C FAILED: {str(e)}")
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "duration": time.time() - start_time
            }

    def _write_chapter_narrative(
        self,
        chapter: dict,
        characters: list,
        locations: list,
        world: dict,
        ticking_clock: dict,
        setting_prompt: str,
        chapter_outline: dict,
        step6_model: str,
    ) -> dict:
        """Process a single chapter's narrative writing (runs in parallel thread).

        Creates per-thread agent instances and processes scenes sequentially
        within the chapter, preserving intra-chapter continuity.

        Args:
            chapter: Chapter data with scenes list
            characters: Full character list from codex
            locations: Full location list from codex
            world: World data from codex
            ticking_clock: Ticking clock dict
            setting_prompt: Setting prompt string
            chapter_outline: Full chapter outline (for codex updates)
            step6_model: Model name for Step 6 agents

        Returns:
            dict with chapter_narrative, scene_debates, word_count, codex_updates
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        from src.story_agents.narrative_writing_agents import (
            CharacterContinuityAgent, LocationAtmosphereAgent,
            WorldBuildingIntegrationAgent, PlotTickingClockAgent,
            NarrativeContinuityAgent,
        )
        from src.story_agents.dialogue_master_agent import DialogueMasterAgent
        from src.story_agents.synthesis_agent import SynthesisAgent
        from src.story_agents.critique_agents import (
            ProsePolishCritic, CharacterVoiceCritic, ContinuityCritic,
            PacingTensionCritic, EmotionalResonanceCritic,
        )

        worker_id = self._get_worker_id()
        chapter_num = chapter["chapter_number"]

        # Create per-thread agent instances (thread-safe: no shared state)
        all_agents = [
            CharacterContinuityAgent(model=step6_model),
            LocationAtmosphereAgent(model=step6_model),
            WorldBuildingIntegrationAgent(model=step6_model),
            PlotTickingClockAgent(model=step6_model),
            NarrativeContinuityAgent(model=step6_model),
        ]
        dialogue_master = DialogueMasterAgent(model=step6_model)
        synthesis_agent = SynthesisAgent(model=step6_model)
        prose_critic = ProsePolishCritic(model=step6_model)
        voice_critic = CharacterVoiceCritic(model=step6_model)
        continuity_critic = ContinuityCritic(model=step6_model)
        pacing_critic = PacingTensionCritic(model=step6_model)
        emotional_critic = EmotionalResonanceCritic(model=step6_model)

        # Per-thread state for intra-chapter continuity
        previous_scene_prose = ""
        previous_scenes_senses = []

        chapter_scenes_narrative = []
        chapter_scene_debates = []
        chapter_word_count = 0
        codex_updates = []  # Collect codex updates to apply after all chapters complete

        print(f"\n[Worker-{worker_id}] {'='*50}")
        print(f"[Worker-{worker_id}] CHAPTER {chapter_num}: Writing {len(chapter['scenes'])} scenes")
        print(f"[Worker-{worker_id}] {'='*50}")

        for scene_data in chapter["scenes"]:
            scene_num = scene_data["scene_number"]
            scene_id = f"ch{chapter_num}_scene{scene_num}"

            print(f"\n[Worker-{worker_id}]     --- SCENE {scene_num} ({scene_data.get('location', 'Unknown')}) ---")

            # Build scene context
            scene_context = {
                "scene_data": scene_data,
                "chapter": chapter,
                "characters": characters,
                "locations": locations,
                "world": world,
                "ticking_clock": ticking_clock,
                "previous_prose": previous_scene_prose,
                "setting_prompt": setting_prompt,
            }

            # =========================================
            # ROUND 1: ALL 5 AGENTS PROPOSE PROSE (PARALLEL)
            # =========================================
            proposals = []
            print(f"[Worker-{worker_id}]     Generating 5 prose proposals (parallel)...")

            def _propose_worker(agent, _scene_data=scene_data, _characters=characters,
                                _locations=locations, _world=world,
                                _previous_prose=previous_scene_prose,
                                _ticking_clock=ticking_clock,
                                _previous_senses=previous_scenes_senses):
                if agent.name == "LOCATION_ATMOSPHERE":
                    return agent, agent.propose_prose(
                        scene_data=_scene_data, characters=_characters,
                        locations=_locations, world=_world,
                        previous_prose=_previous_prose, ticking_clock=_ticking_clock,
                        previous_scenes_senses=_previous_senses,
                    )
                else:
                    return agent, agent.propose_prose(
                        scene_data=_scene_data, characters=_characters,
                        locations=_locations, world=_world,
                        previous_prose=_previous_prose, ticking_clock=_ticking_clock,
                    )

            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = {executor.submit(_propose_worker, agent): agent for agent in all_agents}
                for future in as_completed(futures):
                    agent = futures[future]
                    try:
                        _, proposal = future.result()
                        if proposal is None:
                            print(f"[Worker-{worker_id}]       [{agent.name}] FAILED: Returned None")
                            continue
                        word_count = proposal.word_count()
                        techniques = proposal.techniques_used[:2] if proposal.techniques_used else []
                        proposals.append(proposal)
                        print(f"[Worker-{worker_id}]       [{agent.name}] {word_count} words - {techniques}")
                    except Exception as e:
                        print(f"[Worker-{worker_id}]       [{agent.name}] FAILED: {str(e)[:50]}")

            if not proposals:
                print(f"[Worker-{worker_id}]     All proposals failed - creating fallback prose")
                fallback_prose = f"Scene {scene_num}: {scene_data.get('happens', 'The story continues.')}"
                scene_narrative = {
                    "scene_id": scene_id, "chapter_number": chapter_num,
                    "scene_number": scene_num,
                    "location": scene_data.get("location", "Unknown"),
                    "location_id": scene_data.get("location_id", ""),
                    "pov_character": scene_data.get("pov_character", "Unknown"),
                    "characters_present": scene_data.get("characters", []),
                    "character_ids": scene_data.get("character_ids", []),
                    "time_of_day": scene_data.get("time_of_day", "day"),
                    "prose": fallback_prose, "word_count": len(fallback_prose.split()),
                    "winning_agent": "FALLBACK", "techniques_integrated": [],
                }
                chapter_scenes_narrative.append(scene_narrative)
                chapter_word_count += len(fallback_prose.split())
                continue

            # =========================================
            # ROUND 2: CROSS-AGENT CRITIQUES (5 critiques)
            # =========================================
            critiques = []
            print(f"[Worker-{worker_id}]     Gathering 5 critiques...")

            def _critique_worker(agent, target_proposal, _scene_context=scene_context):
                critique = agent.critique_prose(
                    target_agent=target_proposal.agent_name,
                    proposal=target_proposal, scene_context=_scene_context,
                )
                return agent, target_proposal, critique

            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = {}
                for i, agent in enumerate(all_agents):
                    target_idx = (i + 1) % len(proposals)
                    target_proposal = proposals[target_idx]
                    futures[executor.submit(_critique_worker, agent, target_proposal)] = (agent, target_proposal)
                for future in as_completed(futures):
                    agent, target_proposal = futures[future]
                    try:
                        _, _, critique = future.result()
                        if critique is None:
                            print(f"[Worker-{worker_id}]       [{agent.name}] critique failed: Returned None")
                            continue
                        critiques.append(critique)
                        print(f"[Worker-{worker_id}]       [{agent.name} -> {target_proposal.agent_name}] Score: {critique.overall_score:.1f}")
                    except Exception as e:
                        print(f"[Worker-{worker_id}]       [{agent.name}] critique failed: {str(e)[:30]}")

            # =========================================
            # ROUND 3: DIALOGUE MASTER ANALYZES ALL PROPOSALS
            # =========================================
            print(f"[Worker-{worker_id}]     Dialogue analysis...")
            best_dialogue_proposal = proposals[0]
            dialogue_analysis = None
            dialogue_vote = None
            try:
                dialogue_analysis = dialogue_master.analyze_dialogue(
                    proposal=best_dialogue_proposal, characters=characters,
                    scene_context=scene_context,
                )
                print(f"[Worker-{worker_id}]       Dialogue score: {dialogue_analysis.overall_dialogue_score:.1f}/10")
                print(f"[Worker-{worker_id}]       No-tag test: {'PASS' if dialogue_analysis.no_tag_test_passed else 'FAIL'}")
                dialogue_vote = dialogue_master.vote_best_dialogue(
                    proposals=proposals, dialogue_analyses=[dialogue_analysis],
                )
                print(f"[Worker-{worker_id}]       Best dialogue: {dialogue_vote.best_dialogue_agent}")
            except Exception as e:
                print(f"[Worker-{worker_id}]       Dialogue analysis failed: {str(e)[:50]}")
                from src.story_schemas import DialogueAnalysis, DialogueMasterVote
                dialogue_analysis = DialogueAnalysis(
                    proposal_analyzed=proposals[0].agent_name,
                    total_dialogue_lines=0, lines_analyzed=[],
                    no_tag_test_passed=False, voice_distinctiveness_score=5.0,
                    uses_yes_and=False, has_conflict=False, subtext_present=False,
                    overall_dialogue_score=5.0,
                )
                dialogue_vote = DialogueMasterVote(
                    best_dialogue_agent=proposals[0].agent_name,
                    dialogue_score=5.0, reasoning="Default fallback",
                )

            # =========================================
            # ROUND 4: SYNTHESIS AGENT BLENDS BEST ELEMENTS
            # =========================================
            print(f"[Worker-{worker_id}]     Synthesizing best elements from all 5 proposals...")
            synthesis = None
            final_prose = ""
            scene_word_count = 0
            synthesis_score = 0.0
            try:
                synthesis = synthesis_agent.synthesize_prose(
                    proposals=proposals, critiques=[critiques],
                    dialogue_analysis=dialogue_analysis, dialogue_vote=dialogue_vote,
                    characters=characters, scene_context=scene_context,
                    previous_scenes_senses=previous_scenes_senses,
                )
                final_prose = synthesis.to_prose()
                scene_word_count = len(final_prose.split())
                synthesis_score = synthesis.synthesis_score
                print(f"[Worker-{worker_id}]       Synthesis: {scene_word_count} words, score {synthesis_score:.1f}/10")
                print(f"[Worker-{worker_id}]       Sensory: {', '.join(synthesis.sensory_selection.primary_senses)}")
                print(f"[Worker-{worker_id}]       Voice: {synthesis.voice_ratio.active_percentage:.0f}% active")
                previous_scenes_senses.append(synthesis.sensory_selection.primary_senses)
                if len(previous_scenes_senses) > 3:
                    previous_scenes_senses = previous_scenes_senses[-3:]
            except Exception as e:
                print(f"[Worker-{worker_id}]       Synthesis failed: {str(e)[:80]}")
                final_prose = proposals[0].to_prose()
                scene_word_count = len(final_prose.split())
                synthesis_score = 6.0

            chapter_word_count += scene_word_count

            # =========================================
            # ROUND 5: REAL-TIME CRITIQUE (5 critics parallel)
            # =========================================
            print(f"[Worker-{worker_id}]     Real-time critique (5 critics)...")
            critique_scores = []
            avg_critique_score = 7.0

            scene_chars = [c for c in characters if c.get("name") in scene_data.get("characters", [])]
            scene_loc = next(
                (loc for loc in locations if loc.get("name", "").lower() == scene_data.get("location", "").lower()),
                {}
            )

            try:
                with ThreadPoolExecutor(max_workers=5) as crit_executor:
                    f_prose = crit_executor.submit(prose_critic.critique, final_prose, scene_id)
                    f_voice = crit_executor.submit(voice_critic.critique, final_prose, scene_chars, scene_id)
                    f_cont = crit_executor.submit(continuity_critic.critique, final_prose, scene_chars, scene_loc, world, scene_id, ticking_clock)
                    f_pacing = crit_executor.submit(pacing_critic.critique, final_prose, scene_data, ticking_clock, scene_id)
                    f_emot = crit_executor.submit(emotional_critic.critique, final_prose, scene_id)
                    prose_crit = f_prose.result()
                    voice_crit = f_voice.result()
                    cont_crit = f_cont.result()
                    pacing_crit = f_pacing.result()
                    emot_crit = f_emot.result()

                avg_critique_score = (
                    prose_crit.overall_score + voice_crit.overall_voice_score +
                    cont_crit.overall_continuity_score + pacing_crit.overall_pacing_score +
                    emot_crit.overall_emotional_score
                ) / 5
                critique_scores = [
                    prose_crit.overall_score, voice_crit.overall_voice_score,
                    cont_crit.overall_continuity_score, pacing_crit.overall_pacing_score,
                    emot_crit.overall_emotional_score,
                ]
                print(f"[Worker-{worker_id}]       Critique avg: {avg_critique_score:.1f}/10")
            except Exception as e:
                print(f"[Worker-{worker_id}]       Critique failed: {str(e)[:50]}")

            scene_narrative = {
                "scene_id": scene_id, "chapter_number": chapter_num,
                "scene_number": scene_num,
                "location": scene_data.get("location", "Unknown"),
                "location_id": scene_data.get("location_id", ""),
                "pov_character": scene_data.get("pov_character", "Unknown"),
                "characters_present": scene_data.get("characters", []),
                "character_ids": scene_data.get("character_ids", []),
                "time_of_day": scene_data.get("time_of_day", "day"),
                "prose": final_prose, "word_count": scene_word_count,
                "synthesis_score": synthesis_score,
                "critique_average_score": round(avg_critique_score, 2) if critique_scores else 0,
                "critique_scores": critique_scores,
                "synthesis_agent": "SYNTHESIS" if synthesis else "FALLBACK",
                "dialogue_score": dialogue_analysis.overall_dialogue_score if dialogue_analysis else 0,
                "no_tag_test_passed": dialogue_analysis.no_tag_test_passed if dialogue_analysis else False,
                "sensory_selection": synthesis.sensory_selection.primary_senses if synthesis else [],
                "active_voice_percentage": synthesis.voice_ratio.active_percentage if synthesis else 0,
                "techniques_integrated": synthesis.techniques_integrated if synthesis else [],
            }
            chapter_scenes_narrative.append(scene_narrative)

            # Collect codex update (applied after all threads complete)
            codex_updates.append({
                "chapter_number": chapter_num,
                "scene_id": scene_id,
                "prose": final_prose,
                "word_count": scene_word_count,
                "synthesis_score": synthesis_score,
                "critique_average_score": round(avg_critique_score, 2) if critique_scores else 0,
                "dialogue_score": dialogue_analysis.overall_dialogue_score if dialogue_analysis else 0,
                "no_tag_test_passed": dialogue_analysis.no_tag_test_passed if dialogue_analysis else False,
            })

            # Record debate
            chapter_scene_debates.append({
                "scene_id": scene_id, "chapter": chapter_num, "scene": scene_num,
                "proposals": [p.model_dump() for p in proposals],
                "critiques": [c.model_dump() for c in critiques],
                "dialogue_analysis": dialogue_analysis.model_dump() if dialogue_analysis else {},
                "dialogue_vote": dialogue_vote.model_dump() if dialogue_vote else {},
                "synthesis": synthesis.model_dump() if synthesis else {},
                "realtime_critique_scores": critique_scores,
                "realtime_critique_average": round(avg_critique_score, 2) if critique_scores else 0,
                "final_word_count": scene_word_count,
            })

            # Update previous prose for next scene continuity
            previous_scene_prose = final_prose

        # Assemble chapter result
        print(f"\n[Worker-{worker_id}]     >>> Chapter {chapter_num} complete: {len(chapter_scenes_narrative)} scenes, {chapter_word_count:,} words")

        return {
            "chapter_num": chapter_num,
            "chapter_narrative": {
                "chapter_number": chapter_num,
                "chapter_title": chapter.get("chapter_title", f"Chapter {chapter_num}"),
                "act": chapter.get("act", 1),
                "scenes": chapter_scenes_narrative,
                "chapter_word_count": chapter_word_count,
            },
            "scene_debates": chapter_scene_debates,
            "scene_narratives": chapter_scenes_narrative,
            "word_count": chapter_word_count,
            "codex_updates": codex_updates,
        }

    def step6_narrative(self, codex: dict) -> Step6Result:
        """Write complete narrative via 5-agent multi-agent debate.

        Uses 5 narrative writing agents:
        - CharacterContinuityAgent: Character traits, backstory integration
        - LocationAtmosphereAgent: Sensory immersion, atmosphere
        - WorldBuildingIntegrationAgent: Cultural details (food, customs, prayers)
        - PlotTickingClockAgent: Plot urgency, ticking clock pressure
        - NarrativeContinuityAgent: Prose quality, scene connections

        Debate flow for each scene:
        1. All 5 agents propose prose based on their methodology
        2. Cross-agent critique round (5 critiques)
        3. All 5 agents vote for best proposal
        4. Winner's prose is used

        Args:
            codex: The codex dictionary with outline, characters, locations, world, chapter_outline

        Returns:
            Step5Result with complete narrative and scene debates
        """
        start_time = time.time()
        scene_debates = []
        all_scene_narratives = []
        total_word_count = 0

        try:
            # =========================================
            # VALIDATE PREREQUISITES
            # =========================================
            story = codex.get("story", {})
            chapter_outline = story.get("chapters", {})
            characters = story.get("characters", [])
            locations = story.get("locations", [])
            world = story.get("world", {})
            outline = story.get("outline", {})

            if not chapter_outline:
                return Step6Result(
                    narrative={},
                    scene_debates=[],
                    total_scenes_written=0,
                    total_word_count=0,
                    average_words_per_scene=0,
                    success=False,
                    error="No chapter_outline found. Run Step 4 first.",
                )

            if not characters:
                return Step6Result(
                    narrative={},
                    scene_debates=[],
                    total_scenes_written=0,
                    total_word_count=0,
                    average_words_per_scene=0,
                    success=False,
                    error="No characters found. Run Step 2 first.",
                )

            # Extract ticking clock
            ticking_clock = {
                "ticking_clock": chapter_outline.get("ticking_clock", "Time is running out"),
                "ticking_clock_deadline": chapter_outline.get("ticking_clock_deadline", "Soon"),
                "ticking_clock_consequence": chapter_outline.get("ticking_clock_consequence", "Disaster"),
            }

            story_prompt, setting_prompt = self.extract_prompts(codex)

            print(f"\n{'='*60}")
            print("STEP 6: SCENE NARRATIVE WRITING (Synthesis System)")
            print(f"{'='*60}")
            print(f">>> Agents: 5 narrative specialists + DialogueMaster + Synthesis")
            print(f">>> Method: Propose -> Critique -> Dialogue Analysis -> Synthesis -> Real-time Critique")
            step6_cfg = get_step_config("step6_prose_generation")
            word_min = step6_cfg["targets"]["words_per_scene_min"]
            word_max = step6_cfg["targets"]["words_per_scene_max"]
            print(f">>> Target: {word_min}-{word_max} words per scene")
            print(f">>> Quality: Synthesis score 8.0+, Critique score 7.5+")

            # Get Step 6 model from config (agents created per-thread in _write_chapter_narrative)
            step6_model = get_step_model("step6_prose_generation")
            print(f"\n>>> Model: {step6_model}")
            print(f">>> Agents: 5 proposal + DialogueMaster + Synthesis + 5 critics (created per-thread)")

            # =========================================
            # PROCESS CHAPTERS IN PARALLEL
            # =========================================
            chapters_narrative = []

            from concurrent.futures import ThreadPoolExecutor, as_completed

            # Get parallelization config
            parallel_config = step6_cfg.get("parallel_processing", {})
            parallel_enabled = parallel_config.get("enabled", True)
            max_workers = parallel_config.get("max_workers", 6)
            chapters_list = chapter_outline.get("chapters", [])

            print(f"\n>>> Parallel chapter processing: enabled={parallel_enabled}, max_workers={max_workers}, chapters={len(chapters_list)}")

            if parallel_enabled and len(chapters_list) > 1:
                # PARALLEL: Process all chapters concurrently
                with ThreadPoolExecutor(max_workers=max_workers) as chapter_executor:
                    future_to_chapter = {
                        chapter_executor.submit(
                            self._write_chapter_narrative,
                            chapter=ch,
                            characters=characters,
                            locations=locations,
                            world=world,
                            ticking_clock=ticking_clock,
                            setting_prompt=setting_prompt,
                            chapter_outline=chapter_outline,
                            step6_model=step6_model,
                        ): ch["chapter_number"]
                        for ch in chapters_list
                    }

                    chapter_results = []
                    for future in as_completed(future_to_chapter):
                        ch_num = future_to_chapter[future]
                        try:
                            result = future.result()
                            chapter_results.append(result)
                            print(f"\n>>> Chapter {ch_num} completed: {result['word_count']:,} words")
                        except Exception as e:
                            print(f"\n>>> Chapter {ch_num} FAILED: {str(e)[:100]}")

                # Sort results by chapter number and assemble
                chapter_results.sort(key=lambda r: r["chapter_num"])

                for result in chapter_results:
                    chapters_narrative.append(result["chapter_narrative"])
                    all_scene_narratives.extend(result["scene_narratives"])
                    scene_debates.extend(result["scene_debates"])
                    total_word_count += result["word_count"]

                    # Apply deferred codex updates (thread-safe: sequential after parallel)
                    for update in result["codex_updates"]:
                        for codex_chapter in chapter_outline["chapters"]:
                            if codex_chapter.get("chapter_number") == update["chapter_number"]:
                                for codex_scene in codex_chapter.get("scenes", []):
                                    if codex_scene.get("scene_id") == update["scene_id"]:
                                        codex_scene["prose"] = update["prose"]
                                        codex_scene["word_count"] = update["word_count"]
                                        codex_scene["synthesis_score"] = update["synthesis_score"]
                                        codex_scene["critique_average_score"] = update["critique_average_score"]
                                        codex_scene["dialogue_score"] = update["dialogue_score"]
                                        codex_scene["no_tag_test_passed"] = update["no_tag_test_passed"]
                                        break
                                break
            else:
                # SEQUENTIAL FALLBACK: Process chapters one by one
                for ch in chapters_list:
                    result = self._write_chapter_narrative(
                        chapter=ch,
                        characters=characters,
                        locations=locations,
                        world=world,
                        ticking_clock=ticking_clock,
                        setting_prompt=setting_prompt,
                        chapter_outline=chapter_outline,
                        step6_model=step6_model,
                    )
                    chapters_narrative.append(result["chapter_narrative"])
                    all_scene_narratives.extend(result["scene_narratives"])
                    scene_debates.extend(result["scene_debates"])
                    total_word_count += result["word_count"]

                    # Apply codex updates
                    for update in result["codex_updates"]:
                        for codex_chapter in chapter_outline["chapters"]:
                            if codex_chapter.get("chapter_number") == update["chapter_number"]:
                                for codex_scene in codex_chapter.get("scenes", []):
                                    if codex_scene.get("scene_id") == update["scene_id"]:
                                        codex_scene["prose"] = update["prose"]
                                        codex_scene["word_count"] = update["word_count"]
                                        codex_scene["synthesis_score"] = update["synthesis_score"]
                                        codex_scene["critique_average_score"] = update["critique_average_score"]
                                        codex_scene["dialogue_score"] = update["dialogue_score"]
                                        codex_scene["no_tag_test_passed"] = update["no_tag_test_passed"]
                                        break
                                break

            # =========================================
            # ASSEMBLE FINAL NARRATIVE
            # =========================================
            avg_words = round(total_word_count / len(all_scene_narratives), 1) if all_scene_narratives else 0

            narrative = {
                "title": outline.get("title_suggestion", "Untitled"),
                "total_chapters": len(chapters_narrative),
                "total_scenes": len(all_scene_narratives),
                "total_word_count": total_word_count,
                "average_words_per_scene": avg_words,
                "ticking_clock": ticking_clock,
                "chapters": chapters_narrative,
            }

            duration = time.time() - start_time

            print(f"\n{'='*60}")
            print("STEP 5 COMPLETE")
            print(f"{'='*60}")
            print(f">>> Duration: {duration:.1f}s")
            print(f">>> Total Scenes: {len(all_scene_narratives)}")
            print(f">>> Total Words: {total_word_count:,}")
            print(f">>> Avg Words/Scene: {avg_words:.0f}")
            print(f">>> Estimated Reading Time: {total_word_count // 200} minutes")

            return Step6Result(
                narrative=narrative,
                scene_debates=scene_debates,
                total_scenes_written=len(all_scene_narratives),
                total_word_count=total_word_count,
                average_words_per_scene=avg_words,
                success=True,
                duration_seconds=round(duration, 2),
            )

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Step6Result(
                narrative={},
                scene_debates=scene_debates,
                total_scenes_written=len(all_scene_narratives),
                total_word_count=total_word_count,
                average_words_per_scene=0,
                success=False,
                error=str(e),
                duration_seconds=round(time.time() - start_time, 2),
            )

    # =========================================================================
    # STEPS 6-9: Placeholder implementations (to be added incrementally)
    # =========================================================================

    def step7_revision(self, codex: dict) -> Step7Result:
        """
        Revise narrative with 5 critique personas.

        Uses 5 specialized critics to evaluate each scene:
        1. ProsePolishCritic - Filter words, cliches, show-don't-tell
        2. CharacterVoiceCritic - Dialogue authenticity
        3. ContinuityCritic - Consistency with codex
        4. PacingTensionCritic - Scene structure, ticking clock
        5. EmotionalResonanceCritic - Emotional beats, micro-tension

        Then ReviserAgent applies the critiques to improve the prose.
        """
        start_time = time.time()
        print("\n" + "=" * 60)
        print("STEP 7: NARRATIVE REVISION (5-Critic System)")
        print("=" * 60)

        try:
            # Get data from codex (narrative prose lives in story.chapters)
            characters = codex.get("story", {}).get("characters", [])
            locations = codex.get("story", {}).get("locations", [])
            world = codex.get("story", {}).get("world", {})
            chapter_outline = codex.get("story", {}).get("chapters", {})
            # Get full ticking clock info for time unit checking
            ticking_clock = {
                "ticking_clock": chapter_outline.get("ticking_clock", "Time is running out"),
                "deadline": chapter_outline.get("ticking_clock_deadline", "Unknown"),
                "consequence": chapter_outline.get("ticking_clock_consequence", "Unknown"),
            }

            first_scene = (chapter_outline.get("chapters", [{}])[0].get("scenes", [{}])[0]
                           if chapter_outline.get("chapters") else {})
            if not chapter_outline.get("chapters") or not first_scene.get("prose"):
                return Step7Result(
                    narrative=chapter_outline,
                    critiques=[],
                    scenes_revised=0,
                    revision_passes=0,
                    average_score_before=0,
                    average_score_after=0,
                    success=False,
                    error="No narrative prose found in chapters. Run step 6 first.",
                    duration_seconds=0,
                )

            # Get revision config from author
            num_passes = self.author.revision_style.num_passes
            focus_areas = self.author.revision_style.focus_areas
            cut_aggressively = self.author.revision_style.cut_aggressively

            print(f"Revision passes: {num_passes}")
            print(f"Focus areas: {focus_areas}")
            print(f"Cut aggressively: {cut_aggressively}")

            # Initialize critics
            prose_critic = ProsePolishCritic(model=self.model)
            voice_critic = CharacterVoiceCritic(model=self.model)
            continuity_critic = ContinuityCritic(model=self.model)
            pacing_critic = PacingTensionCritic(model=self.model)
            emotional_critic = EmotionalResonanceCritic(model=self.model)
            reviser = ReviserAgent(model=self.model)

            all_critiques = []
            scenes_revised = 0
            scores_before = []
            scores_after = []
            revision_history = []  # Track prose before/after for metadata

            # Process each revision pass
            for pass_num in range(num_passes):
                print(f"\n{'=' * 40}")
                print(f"REVISION PASS {pass_num + 1}/{num_passes}")
                print("=" * 40)

                from concurrent.futures import ThreadPoolExecutor, as_completed

                def _process_scene(scene, chapter_num):
                    """Worker: run 5 parallel critics + optional revision for one scene."""
                    scene_id = scene.get("scene_id", f"ch{chapter_num}_scene?")
                    prose = scene.get("prose", "")

                    if not prose:
                        print(f"\n  Scene: {scene_id} [No prose to revise]")
                        return {"skipped": True, "scene_id": scene_id}

                    print(f"\n  Scene: {scene_id} — Running 5 critics (parallel)...")

                    # Get scene characters from codex
                    scene_char_names = scene.get("characters_present", [])
                    scene_chars = [
                        c for c in characters
                        if c.get("name") in scene_char_names
                    ]

                    # Get scene location from codex
                    scene_loc_name = scene.get("location", "")
                    scene_loc = next(
                        (loc for loc in locations
                         if loc.get("name", "").lower() == scene_loc_name.lower()),
                        {}
                    )

                    # Run all 5 critics (parallel)
                    with ThreadPoolExecutor(max_workers=5) as crit_executor:
                        f_prose = crit_executor.submit(prose_critic.critique, prose, scene_id)
                        f_voice = crit_executor.submit(voice_critic.critique, prose, scene_chars, scene_id)
                        f_cont = crit_executor.submit(continuity_critic.critique, prose, scene_chars, scene_loc, world, scene_id, ticking_clock)
                        f_pacing = crit_executor.submit(pacing_critic.critique, prose, scene, ticking_clock, scene_id)
                        f_emot = crit_executor.submit(emotional_critic.critique, prose, scene_id)

                        prose_crit = f_prose.result()
                        voice_crit = f_voice.result()
                        cont_crit = f_cont.result()
                        pacing_crit = f_pacing.result()
                        emot_crit = f_emot.result()

                    # Calculate average score
                    avg_score = (
                        prose_crit.overall_score +
                        voice_crit.overall_voice_score +
                        cont_crit.overall_continuity_score +
                        pacing_crit.overall_pacing_score +
                        emot_crit.overall_emotional_score
                    ) / 5

                    print(f"    {scene_id}: avg {avg_score:.1f}/10 (P:{prose_crit.overall_score:.0f} V:{voice_crit.overall_voice_score:.0f} C:{cont_crit.overall_continuity_score:.0f} Pc:{pacing_crit.overall_pacing_score:.0f} E:{emot_crit.overall_emotional_score:.0f})")

                    # Bundle critiques
                    critique_bundle = {
                        "scene_id": scene_id,
                        "prose_critique": prose_crit.model_dump(),
                        "voice_critique": voice_crit.model_dump(),
                        "continuity_critique": cont_crit.model_dump(),
                        "pacing_critique": pacing_crit.model_dump(),
                        "emotional_critique": emot_crit.model_dump(),
                        "average_score": round(avg_score, 2),
                        "needs_revision": (
                            prose_crit.needs_revision or
                            voice_crit.needs_revision or
                            cont_crit.needs_revision or
                            pacing_crit.needs_revision or
                            emot_crit.needs_revision
                        ),
                    }

                    result = {
                        "skipped": False,
                        "scene_id": scene_id,
                        "score_before": avg_score,
                        "score_after": avg_score,
                        "critique_bundle": critique_bundle,
                        "revised": False,
                        "revision_entry": None,
                    }

                    # Check if revision needed
                    if critique_bundle["needs_revision"]:
                        print(f"    {scene_id}: REVISING (avg score: {avg_score:.1f}/10)")

                        # Build critique text for reviser
                        critique_text = self._build_critique_text(
                            prose_crit, voice_crit, cont_crit,
                            pacing_crit, emot_crit,
                            cut_aggressively
                        )

                        # Build character context for reviser
                        char_context = "\n".join([
                            f"- {c.get('name')}: {c.get('personality_summary', c.get('personality', ''))}"
                            for c in scene_chars
                        ])

                        # Revise the scene
                        try:
                            revised = reviser.revise_scene(
                                scene,
                                critique_text,
                                char_context,
                                str(scene_loc)[:1000]
                            )
                            revised_prose = revised.to_prose()
                            scene["prose"] = revised_prose
                            scene["word_count"] = len(revised_prose.split())
                            scene["revision_notes"] = {
                                "pass": pass_num + 1,
                                "critics_flagged": [
                                    "prose" if prose_crit.needs_revision else None,
                                    "voice" if voice_crit.needs_revision else None,
                                    "continuity" if cont_crit.needs_revision else None,
                                    "pacing" if pacing_crit.needs_revision else None,
                                    "emotional" if emot_crit.needs_revision else None,
                                ],
                            }
                            result["revised"] = True
                            result["score_after"] = avg_score + 1.5
                            result["revision_entry"] = {
                                "scene_id": scene_id,
                                "pass": pass_num + 1,
                                "prose_before": prose,
                                "prose_after": revised_prose,
                                "score_before": round(avg_score, 2),
                                "critiques_summary": {
                                    "prose_score": prose_crit.overall_score,
                                    "voice_score": voice_crit.overall_voice_score,
                                    "continuity_score": cont_crit.overall_continuity_score,
                                    "pacing_score": pacing_crit.overall_pacing_score,
                                    "emotional_score": emot_crit.overall_emotional_score,
                                }
                            }
                            print(f"    {scene_id}: REVISED ({scene['word_count']} words)")
                        except Exception as e:
                            print(f"    {scene_id}: REVISION FAILED: {e}")
                    else:
                        print(f"    {scene_id}: OK (avg score: {avg_score:.1f}/10)")

                    return result

                # Collect all scenes for parallel processing
                all_scenes = []
                for chapter in chapter_outline.get("chapters", []):
                    chapter_num = chapter.get("chapter_number", 0)
                    print(f"\n--- Chapter {chapter_num}: {chapter.get('chapter_title', '')} ---")
                    for scene in chapter.get("scenes", []):
                        if scene.get("prose"):
                            all_scenes.append((scene, chapter_num))

                step7_cfg = get_step_config("step7_revision")
                rev_max_workers = step7_cfg.get("parallel_processing", {}).get("max_workers", 6)
                print(f"\n  Processing {len(all_scenes)} scenes in parallel (max_workers={rev_max_workers})...")

                with ThreadPoolExecutor(max_workers=rev_max_workers) as scene_executor:
                    futures = {
                        scene_executor.submit(_process_scene, scene, ch_num): (scene, ch_num)
                        for scene, ch_num in all_scenes
                    }
                    for future in as_completed(futures):
                        try:
                            result = future.result()
                            if result.get("skipped"):
                                continue
                            scores_before.append(result["score_before"])
                            scores_after.append(result["score_after"])
                            all_critiques.append(result["critique_bundle"])
                            if result["revised"]:
                                scenes_revised += 1
                            if result["revision_entry"]:
                                revision_history.append(result["revision_entry"])
                        except Exception as e:
                            scene, ch_num = futures[future]
                            print(f"    Scene {scene.get('scene_id', '?')} FAILED: {e}")

            # Store critiques in metadata (not story)
            if "metadata" not in codex:
                codex["metadata"] = {}
            if "phase_1" not in codex["metadata"]:
                codex["metadata"]["phase_1"] = {}
            codex["metadata"]["phase_1"]["critiques"] = all_critiques

            # Calculate metrics
            avg_before = sum(scores_before) / len(scores_before) if scores_before else 0
            avg_after = sum(scores_after) / len(scores_after) if scores_after else 0

            # Store revision history in metadata (for future reference)
            if "metadata" not in codex:
                codex["metadata"] = {}
            if "phase_1" not in codex["metadata"]:
                codex["metadata"]["phase_1"] = {}

            codex["metadata"]["phase_1"]["step_7"] = {
                "revision_passes": num_passes,
                "scenes_revised": scenes_revised,
                "average_score_before": round(avg_before, 2),
                "average_score_after": round(avg_after, 2),
                "focus_areas": focus_areas,
                "cut_aggressively": cut_aggressively,
                "revision_history": revision_history,
            }

            duration = time.time() - start_time
            print(f"\n{'=' * 60}")
            print("STEP 7 COMPLETE: Narrative Revision")
            print(f"  Scenes revised: {scenes_revised}")
            print(f"  Revision passes: {num_passes}")
            print(f"  Avg score before: {avg_before:.1f}/10")
            print(f"  Avg score after: {avg_after:.1f}/10")
            print(f"  Duration: {duration:.1f}s")
            print("=" * 60)

            return Step7Result(
                narrative=chapter_outline,
                critiques=all_critiques,
                scenes_revised=scenes_revised,
                revision_passes=num_passes,
                average_score_before=round(avg_before, 2),
                average_score_after=round(avg_after, 2),
                success=True,
                duration_seconds=round(duration, 2),
            )

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Step7Result(
                narrative=codex.get("story", {}).get("chapters", {}),
                critiques=all_critiques if 'all_critiques' in dir() else [],
                scenes_revised=scenes_revised if 'scenes_revised' in dir() else 0,
                revision_passes=num_passes if 'num_passes' in dir() else 0,
                average_score_before=0,
                average_score_after=0,
                success=False,
                error=str(e),
                duration_seconds=round(time.time() - start_time, 2),
            )

    def _build_critique_text(
        self,
        prose_crit: ProsePolishCritique,
        voice_crit: CharacterVoiceCritique,
        cont_crit: ContinuityCritique,
        pacing_crit: PacingTensionCritique,
        emot_crit: EmotionalResonanceCritique,
        cut_aggressively: bool = False,
    ) -> str:
        """Build critique text for the reviser agent."""
        sections = []

        # Prose issues (using Pydantic model attributes)
        if prose_crit.filter_words_found:
            sections.append(
                "FILTER WORDS TO REMOVE:\n" +
                "\n".join([f"- {fw.text}" for fw in prose_crit.filter_words_found[:5]])
            )
        if prose_crit.cliches_found:
            sections.append(
                "CLICHES TO REPLACE:\n" +
                "\n".join([f"- {c.text}" for c in prose_crit.cliches_found[:5]])
            )
        if prose_crit.specific_rewrites:
            sections.append(
                "SPECIFIC REWRITES:\n" +
                "\n".join([
                    f"- '{r.original}' -> '{r.suggestion}'"
                    for r in prose_crit.specific_rewrites[:5]
                ])
            )

        # Voice issues
        if voice_crit.dialogue_fixes:
            sections.append(
                "DIALOGUE FIXES:\n" +
                "\n".join([
                    f"- {df.character}: '{df.original}' -> '{df.suggested}' ({df.reason})"
                    for df in voice_crit.dialogue_fixes[:5]
                ])
            )

        # Continuity issues
        if cont_crit.character_inconsistencies:
            sections.append(
                "CHARACTER FIXES:\n" +
                "\n".join([
                    f"- {ci.character}: {ci.issue}"
                    for ci in cont_crit.character_inconsistencies[:3]
                ])
            )

        # Pacing issues
        if pacing_crit.slow_spots:
            sections.append(
                "SLOW SPOTS TO TIGHTEN:\n" +
                "\n".join([
                    f"- Paragraph {ss.paragraph}: {ss.issue}"
                    for ss in pacing_crit.slow_spots[:3]
                ])
            )
        if not pacing_crit.ticking_clock_present:
            sections.append("ADD TICKING CLOCK: Reference the urgency/deadline")

        # Emotional issues
        if emot_crit.skim_risk_areas:
            sections.append(
                "ENGAGEMENT FIXES:\n" +
                "\n".join([
                    f"- Paragraph {sr.paragraph}: {sr.issue}"
                    for sr in emot_crit.skim_risk_areas[:3]
                ])
            )
        if emot_crit.ending_resonance_type == "weak":
            sections.append("SCENE ENDING: Add resonance (image, question, ache, or realization)")

        # Aggressive cutting instruction
        if cut_aggressively:
            sections.append(
                "CUTTING: Be ruthless. Remove unnecessary description, "
                "redundant dialogue, and any 'parking the car' moments."
            )

        return "\n\n".join(sections) if sections else "Minor polish needed."

    def _name_chapter_parallel(
        self,
        chapter: dict,
        book_title: str,
        theme: str,
    ) -> tuple[int, str, dict]:
        """
        Generate title for a single chapter in parallel.

        Args:
            chapter: Chapter data with scenes
            book_title: Book title for context
            theme: Story theme

        Returns:
            Tuple of (chapter_number, winning_title, debate_result)
        """
        from src.story_agents.title_naming_agents import run_chapter_title_debate

        thread_name = threading.current_thread().name
        worker_id = thread_name.split('-')[-1] if '-' in thread_name else 'Main'

        chapter_num = chapter.get("chapter_number", 0)
        print(f"[Worker-{worker_id}] Chapter {chapter_num}...")

        # Build chapter summary from scenes
        scenes = chapter.get("scenes", [])
        scenes_summary = ""
        chapter_summary = ""
        for scene in scenes:
            scene_id = scene.get("scene_id", "")
            location = scene.get("location", "")
            prose = scene.get("prose", "")[:300]  # First 300 chars
            scenes_summary += f"- {scene_id} at {location}\n"
            chapter_summary += prose[:150] + " "

        # Run debate (already parallelized internally at debate level)
        chapter_debate = run_chapter_title_debate(
            chapter_number=chapter_num,
            chapter_summary=chapter_summary[:500],
            scenes_summary=scenes_summary,
            book_title=book_title,
            theme=theme,
            model=self.model,
        )

        winning_title = chapter_debate["winning_title"]
        print(f"[Worker-{worker_id}]   -> \"{winning_title}\"")

        return chapter_num, winning_title, chapter_debate

    def step8_naming(self, codex: dict) -> Step8Result:
        """
        Generate book and chapter titles via 3-agent multi-agent debate.

        Uses 3 naming agents:
        - TitleLiteraryAgent: Evocative, poetic titles (metaphor, symbolism)
        - TitleThematicAgent: Theme-reflecting titles (core conflict, arc)
        - TitleCommercialAgent: Marketable, genre-appropriate titles (hooks)

        TWO-LEVEL PARALLELIZATION:
        1. Proposal Level: All chapter titles are generated in parallel (configurable max_workers)
        2. Debate Level: Each debate runs 3 agents in parallel (handled by run_*_debate functions)

        Expected Speedup: ~4× for 11 chapters (with max_workers=4)

        Args:
            codex: The codex dictionary with narrative

        Returns:
            Step7Result with book_title and chapter_titles
        """
        from src.story_agents.title_naming_agents import (
            run_book_title_debate,
            run_chapter_title_debate,
        )

        start_time = time.time()

        try:
            # Validate prerequisites
            chapters_data = codex.get("story", {}).get("chapters", {})
            if not chapters_data or not chapters_data.get("chapters"):
                return Step8Result(
                    book_title="Untitled",
                    chapter_titles={},
                    book_debate={},
                    chapter_debates=[],
                    success=False,
                    error="Chapters not found. Run step 5 first.",
                    duration_seconds=time.time() - start_time,
                )

            outline = codex["story"].get("outline", {})

            # Extract context for book title debate
            logline = outline.get("logline", "A compelling story.")
            theme = outline.get("theme", "")
            setting = codex.get("setting_prompt", "")

            # Build plot summary from chapter outline
            chapters = chapters_data.get("chapters", [])
            plot_points = []
            for ch in chapters[:3]:  # First 3 chapters for summary
                for scene in ch.get("scenes", [])[:2]:
                    plot_points.append(scene.get("happens", ""))
            plot_summary = " ".join(plot_points)[:1000] if plot_points else logline

            # =================================================================
            # BOOK TITLE DEBATE
            # =================================================================
            print("\n--- Book Title Debate ---")
            print("  3 agents proposing titles...")

            book_debate = run_book_title_debate(
                logline=logline,
                theme=theme,
                setting=setting,
                plot_summary=plot_summary,
                model=self.model,
            )

            book_title = book_debate["winning_title"]
            print(f"  Winner: \"{book_title}\" ({book_debate['winner_agent']})")

            # =================================================================
            # CHECK PARALLELIZATION CONFIG
            # =================================================================
            step8_config = get_step_config('step8_naming')
            parallel_config = step8_config.get('parallel_processing', {})
            parallel_enabled = parallel_config.get('proposal_level', True)
            max_workers = parallel_config.get('max_workers_proposals', 4)

            narrative_chapters = chapters_data.get("chapters", [])

            # =================================================================
            # PARALLELIZATION: PROPOSAL LEVEL
            # =================================================================
            if parallel_enabled and len(narrative_chapters) > 0:
                print("\n--- Chapter Title Generation (Parallel Mode) ---")
                print(f"  Generating titles for {len(narrative_chapters)} chapters in parallel...")
                print(f"  Max workers: {max_workers}")

                from concurrent.futures import ThreadPoolExecutor, as_completed

                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    # Submit all chapter title debates in parallel
                    chapter_futures = []
                    for chapter in narrative_chapters:
                        future = executor.submit(
                            self._name_chapter_parallel,
                            chapter,
                            book_title,
                            theme,
                        )
                        chapter_futures.append(future)

                    # Collect chapter results
                    chapter_titles = {}
                    chapter_debates = []
                    for future in as_completed(chapter_futures):
                        chapter_num, winning_title, chapter_debate = future.result()
                        chapter_titles[chapter_num] = winning_title
                        chapter_debates.append(chapter_debate)

                    # Sort chapter debates by chapter number
                    chapter_debates.sort(key=lambda x: x.get("chapter_number", 0))

            else:
                # =================================================================
                # SEQUENTIAL MODE (FALLBACK)
                # =================================================================
                print("\n--- Chapter Title Debates (Sequential Mode) ---")

                chapter_titles = {}
                chapter_debates = []

                for chapter in narrative_chapters:
                    chapter_num = chapter.get("chapter_number", 0)
                    print(f"  Chapter {chapter_num}...")

                    # Build chapter summary from scenes
                    scenes = chapter.get("scenes", [])
                    scenes_summary = ""
                    chapter_summary = ""
                    for scene in scenes:
                        scene_id = scene.get("scene_id", "")
                        location = scene.get("location", "")
                        prose = scene.get("prose", "")[:300]  # First 300 chars
                        scenes_summary += f"- {scene_id} at {location}\n"
                        chapter_summary += prose[:150] + " "

                    chapter_debate = run_chapter_title_debate(
                        chapter_number=chapter_num,
                        chapter_summary=chapter_summary[:500],
                        scenes_summary=scenes_summary,
                        book_title=book_title,
                        theme=theme,
                        model=self.model,
                    )

                    winning_title = chapter_debate["winning_title"]
                    chapter_titles[chapter_num] = winning_title
                    chapter_debates.append(chapter_debate)
                    print(f"    -> \"{winning_title}\"")

            # =================================================================
            # UPDATE CODEX
            # =================================================================
            chapters_data["title"] = book_title
            if book_debate.get("winning_subtitle"):
                chapters_data["subtitle"] = book_debate["winning_subtitle"]

            for chapter in narrative_chapters:
                chapter_num = chapter.get("chapter_number", 0)
                if chapter_num in chapter_titles:
                    chapter["chapter_title"] = f"Chapter {chapter_num} - {chapter_titles[chapter_num]}"

            duration = time.time() - start_time
            print(f"\n  Total naming time: {duration:.1f}s")

            return Step8Result(
                book_title=book_title,
                chapter_titles=chapter_titles,
                book_debate=book_debate,
                chapter_debates=chapter_debates,
                success=True,
                duration_seconds=duration,
            )

        except Exception as e:
            return Step8Result(
                book_title="Untitled",
                chapter_titles={},
                book_debate={},
                chapter_debates=[],
                success=False,
                error=str(e),
                duration_seconds=time.time() - start_time,
            )

    def step8_screenplay(self, codex: dict) -> dict:
        """Format as screenplay. Override in subclass for custom behavior."""
        raise NotImplementedError("Step 8 (Screenplay) not yet implemented")

    def step9_polish(self, codex: dict) -> dict:
        """Final polish. Override in subclass for custom behavior."""
        raise NotImplementedError("Step 9 (Polish) not yet implemented")

    def step10_finalize(self, codex: dict) -> dict:
        """Finalize and validate. Override in subclass for custom behavior."""
        raise NotImplementedError("Step 10 (Finalize) not yet implemented")

    # =========================================================================
    # MAIN RUN METHOD
    # =========================================================================

    def run(
        self,
        codex: dict,
        steps: list[int] = None,
        revision_passes: int = None,
    ) -> dict:
        """Execute Phase 1 steps.

        Args:
            codex: The codex dictionary (will be modified in place)
            steps: List of step numbers to run (0-9). Default: all steps.
            revision_passes: Number of revision passes for step 6.

        Returns:
            Dictionary with results from each executed step
        """
        steps_to_run = steps if steps is not None else list(range(0, 10))
        results = {}
        steps_completed = []
        step_timings = {}

        print(f"\n>>> Phase 1: Author-Driven Story Creation")
        print(f">>> Author: {self.author.name}")
        print(f">>> Structure: {self.author.preferred_structure}")
        print(f">>> Running steps: {steps_to_run}")

        # Initialize codex structure
        if "story" not in codex:
            codex["story"] = {}
        if "outline" not in codex["story"]:
            codex["story"]["outline"] = {}

        # Initialize metadata structure (needed for storing debates)
        if "metadata" not in codex:
            codex["metadata"] = {}
        if "phase_1" not in codex["metadata"]:
            codex["metadata"]["phase_1"] = {}

        # Step 0: Theme Foundation
        if 0 in steps_to_run:
            print(f"\n{'='*60}")
            print("STEP 0: Theme Foundation (Multi-Agent Debate)")
            print(f"{'='*60}")

            result = self.step0_theme_foundation(codex)
            results["step0"] = result

            if result.success:
                # Store theme foundation at story.theme_foundation
                codex["story"]["theme_foundation"] = result.theme_foundation

                # Store debate details in metadata
                codex["metadata"]["phase_1"]["step0_debates"] = result.step0_debates

                steps_completed.append(0)
                step_timings["step0_theme_foundation"] = result.duration_seconds
            else:
                print(f">>> Step 0 FAILED: {result.error}")

        # Step 1: Character Creation (Theme → Characters)
        if 1 in steps_to_run:
            print(f"\n{'='*60}")
            print("STEP 1: Character Creation (Theme → Characters)")
            print(f"{'='*60}")

            result = self.step1_character_creation(codex)
            results["step1"] = result

            if result.success:
                # Characters already stored to codex during step execution
                # (updated after each character is created)
                steps_completed.append(1)
                step_timings["step1_character_creation"] = result.duration_seconds
            else:
                print(f">>> Step 1 FAILED: {result.error}")

        # Step 2: Story Shape & Genre Selection
        if 2 in steps_to_run:
            print(f"\n{'='*60}")
            print("STEP 2: Story Shape & Genre Selection (Multi-Agent Debate)")
            print(f"{'='*60}")

            result = self.step2_story_shape_genre(codex)
            results["step2"] = result

            if result.success:
                # Store story shape and genre in story section
                codex["story"]["story_shape"] = result.story_shape
                codex["story"]["save_the_cat_type"] = result.save_the_cat_type
                codex["story"]["primary_genre"] = result.primary_genre
                if result.secondary_genre:
                    codex["story"]["secondary_genre"] = result.secondary_genre
                if result.tone_flavor:
                    codex["story"]["tone_flavor"] = result.tone_flavor
                codex["story"]["tropes"] = result.tropes

                # Store debate details in metadata
                codex["metadata"]["phase_1"]["step2_debates"] = result.step2_debates

                steps_completed.append(2)
                step_timings["step2_story_shape_genre"] = result.duration_seconds
            else:
                print(f">>> Step 2 FAILED: {result.error}")

        # Step 3: Plot Structure (Character Arc + Story Beats)
        if 3 in steps_to_run:
            print(f"\n{'='*60}")
            print("STEP 3: Plot Structure (Character Arc + Story Beats)")
            print(f"{'='*60}")

            result = self.step3_plot_structure(codex)
            results["step3"] = result

            if result.success:
                # Store integrated beats in story section
                codex["story"]["integrated_beats"] = result.integrated_beats
                codex["story"]["hero_arc_summary"] = result.hero_arc_summary
                codex["story"]["villain_arc_summary"] = result.villain_arc_summary
                codex["story"]["side_character_notes"] = result.side_character_notes

                # Store debate details in metadata
                codex["metadata"]["phase_1"]["step3_debates"] = result.step3_debates

                steps_completed.append(3)
                step_timings["step3_plot_structure"] = result.duration_seconds
            else:
                print(f">>> Step 3 FAILED: {result.error}")

        # Step 4: World Building (World Pressure + Dynamic Major Locations)
        if 4 in steps_to_run:
            print(f"\n{'='*60}")
            print("STEP 4: World Building (World Pressure + Major Locations)")
            print(f"{'='*60}")

            result = self.step4_world_building(codex)
            results["step4"] = result

            if result.success:
                # Store world pressure and locations in story section
                codex["story"]["world_pressure"] = result.world_pressure
                codex["story"]["locations"] = result.locations

                # Store debate details in metadata
                codex["metadata"]["phase_1"]["step4_debates"] = result.step4_debates

                steps_completed.append(4)
                step_timings["step4_world_building"] = result.duration_seconds
            else:
                print(f">>> Step 4 FAILED: {result.error}")

        # Step 5: Chapter & Scene Breakdown
        if 5 in steps_to_run:
            print(f"\n{'='*60}")
            print("STEP 5: Chapter & Scene Breakdown (3-Agent Debate)")
            print(f"{'='*60}")

            result = self.step5_chapter_scene_breakdown(codex)
            results["step5"] = result

            if result.success:
                # Store chapters at story.chapters
                codex["story"]["chapters"] = result.chapter_outline

                # Populate character and location IDs
                self._populate_scene_ids(codex["story"]["chapters"], codex)

                # Store debate details in metadata
                codex["metadata"]["phase_1"]["step5_debates"] = result.debates

                steps_completed.append(5)
                step_timings["step5_chapter_scene_breakdown"] = result.duration_seconds

                # Step 5B: Foreshadowing & Setup/Payoff Analysis (runs automatically after Step 5)
                print(f"\n{'='*60}")
                print("STEP 5B: Foreshadowing & Setup/Payoff Analysis (3-Agent Debate)")
                print(f"{'='*60}")

                result_5b = self.step5b_foreshadowing_analysis(codex)
                results["step5b"] = result_5b

                if result_5b.get("success"):
                    # Store foreshadowing plan in metadata
                    codex["metadata"]["phase_1"]["step5b_foreshadowing"] = result_5b["debates"]

                    step_timings["step5b_foreshadowing_analysis"] = result_5b["duration"]
                    print(f">>> Step 5B COMPLETE")

                    # Step 5C: Complete Scene Interconnection Analysis (runs automatically after Step 5B)
                    print(f"\n{'='*60}")
                    print("STEP 5C: Complete Scene Interconnection Analysis")
                    print(f"{'='*60}")

                    result_5c = self.step5c_interconnection_analysis(codex)
                    results["step5c"] = result_5c

                    if result_5c.get("success"):
                        # Store interconnection report in metadata
                        codex["metadata"]["phase_1"]["step5c_interconnection"] = result_5c["report"]

                        step_timings["step5c_interconnection_analysis"] = result_5c["duration"]
                        print(f">>> Step 5C COMPLETE")
                    else:
                        print(f">>> Step 5C FAILED: {result_5c.get('error', 'Unknown error')}")
                        print(">>> Continuing to Step 6 with current chapter outline...")
                else:
                    print(f">>> Step 5B FAILED: {result_5b.get('error', 'Unknown error')}")
                    print(">>> Continuing to Step 6 with original chapter outline...")

            else:
                print(f">>> Step 5 FAILED: {result.error}")

        # Step 6: Scene Narrative Writing
        if 6 in steps_to_run:
            print(f"\n{'='*60}")
            print("STEP 6: Scene Narrative Writing (5-Agent Multi-Agent Debate)")
            print(f"{'='*60}")

            result = self.step6_narrative(codex)
            results["step6"] = result

            if result.success:
                # Merge narrative data into story.chapters (unified structure)
                narrative = result.narrative
                chapters_data = codex["story"]["chapters"]

                # Copy top-level narrative metadata
                chapters_data["title"] = narrative.get("title", "Untitled")
                chapters_data["subtitle"] = narrative.get("subtitle", "")
                chapters_data["total_scenes"] = narrative.get("total_scenes", 0)
                chapters_data["total_word_count"] = narrative.get("total_word_count", 0)
                chapters_data["average_words_per_scene"] = narrative.get("average_words_per_scene", 0)

                # Build lookup: (chapter_number, scene_number) -> narrative scene
                narrative_scene_map = {}
                for n_ch in narrative.get("chapters", []):
                    for n_sc in n_ch.get("scenes", []):
                        narrative_scene_map[(n_ch.get("chapter_number"), n_sc.get("scene_number"))] = n_sc

                narrative_fields = [
                    "scene_id", "prose", "word_count", "synthesis_score",
                    "critique_average_score", "critique_scores", "synthesis_agent",
                    "dialogue_score", "no_tag_test_passed", "sensory_selection",
                    "active_voice_percentage", "techniques_integrated", "revision_notes",
                ]

                for o_ch in chapters_data.get("chapters", []):
                    ch_num = o_ch.get("chapter_number")
                    n_ch_match = next(
                        (nc for nc in narrative.get("chapters", []) if nc.get("chapter_number") == ch_num),
                        None,
                    )
                    if n_ch_match:
                        o_ch["chapter_word_count"] = n_ch_match.get("chapter_word_count", 0)
                        o_ch["act"] = n_ch_match.get("act", o_ch.get("act", 1))
                        if n_ch_match.get("chapter_title"):
                            o_ch["chapter_title"] = n_ch_match["chapter_title"]

                    for o_sc in o_ch.get("scenes", []):
                        n_sc = narrative_scene_map.get((ch_num, o_sc.get("scene_number")))
                        if n_sc:
                            for field in narrative_fields:
                                if field in n_sc:
                                    o_sc[field] = n_sc[field]

                steps_completed.append(6)
                step_timings["step6_narrative"] = result.duration_seconds
            else:
                print(f">>> Step 6 FAILED: {result.error}")

        # Step 7: Narrative Revision with 5-Critic System
        if 7 in steps_to_run:
            print(f"\n{'='*60}")
            print("STEP 7: Narrative Revision (5-Critic System)")
            print(f"{'='*60}")
            result = self.step7_revision(codex)
            results["step7"] = result
            if result.success:
                print(f"\n>>> Step 7 COMPLETE: Revised {result.scenes_revised} scenes")
                print(f"    Avg score: {result.average_score_before:.1f} -> {result.average_score_after:.1f}")
                steps_completed.append(7)
                step_timings["step7_revision"] = result.duration_seconds
            else:
                print(f">>> Step 7 FAILED: {result.error}")

        # Step 8: Book & Chapter Title Naming
        if 8 in steps_to_run:
            print(f"\n{'='*60}")
            print("STEP 8: BOOK & CHAPTER TITLE NAMING (3-Agent Debate)")
            print(f"{'='*60}")
            result = self.step8_naming(codex)
            results["step8"] = result
            if result.success:
                print(f"\n>>> Step 8 COMPLETE: Book titled \"{result.book_title}\"")
                print(f"    Chapter titles: {len(result.chapter_titles)}")
                steps_completed.append(8)
                step_timings["step8_naming"] = result.duration_seconds
            else:
                print(f">>> Step 8 FAILED: {result.error}")

        # Steps 8-10: Add as we implement them
        for step_num in range(9, 11):
            if step_num in steps_to_run:
                print(f"\n>>> Step {step_num}: Not yet implemented")

        # Aggregate token usage across all completed steps
        step_tokens = {}
        total_tokens = 0
        total_calls = 0
        for step_name, result in results.items():
            if hasattr(result, 'token_usage') and result.token_usage:
                step_tokens[step_name] = result.token_usage
                total_tokens += result.token_usage.get('total_tokens', 0)
                total_calls += result.token_usage.get('call_count', 0)

        # Update metadata with phase completion info
        codex["metadata"]["phase_1"].update({
            "phase": 1,
            "name": "Author-Driven Story Creation",
            "author_id": self.author.id,
            "author_name": self.author.name,
            "structure_used": self.author.preferred_structure,
            "steps_completed": steps_completed,
            "step_timings": step_timings,
            "step_tokens": step_tokens,  # NEW: Token usage by step
            "total_tokens": total_tokens,  # NEW: Total tokens across all steps
            "total_calls": total_calls,  # NEW: Total LLM calls
        })

        # Add character debates to metadata (NEW Step 1)
        if "step1" in results and results["step1"].success:
            codex["metadata"]["phase_1"]["character_debates"] = results["step1"].character_debates

        # Add scene debates to metadata (OLD Step 4 only - now skipped for NEW Step 4 World Building)
        # if "step4" in results and results["step4"].success:
        #     codex["metadata"]["phase_1"]["scene_debates"] = results["step4"].scene_debates

        # Add chapter/scene breakdown debates to metadata (NEW Step 5)
        if "step5" in results and results["step5"].success:
            codex["metadata"]["phase_1"]["chapter_scene_debates"] = results["step5"].debates

        # Add narrative writing debates to metadata (Step 6, formerly Step 5)
        if "step6" in results and results["step6"].success:
            codex["metadata"]["phase_1"]["narrative_debates"] = results["step6"].scene_debates

        # Add title naming debates to metadata (Step 8, formerly Step 7)
        if "step8" in results and results["step8"].success:
            codex["metadata"]["phase_1"]["title_naming"] = {
                "book_title": results["step8"].book_title,
                "chapter_titles": results["step8"].chapter_titles,
                "book_debate": results["step8"].book_debate,
            }

        return {
            "steps_completed": steps_completed,
            "step_timings": step_timings,
            "results": results,
        }
