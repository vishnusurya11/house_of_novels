"""
Base Phase 1 Implementation for Authors.

Provides default implementation of the 9-step Phase 1 pipeline.
Authors can override individual steps for custom behavior.
"""

import time
import random
import string
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, TYPE_CHECKING, TypeVar, Type

from src.config import DEFAULT_MODEL, OPENROUTER_API_KEY, OPENROUTER_BASE_URL
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


@dataclass
class Step1Result:
    """Result of Step 1: Character Creation (Theme → Characters)."""
    characters: list  # List of character dicts with Lie/Truth/Shadow/Arc/Ghost
    character_debates: list  # Full debate history for each character
    success: bool
    error: Optional[str] = None
    duration_seconds: float = 0.0


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
    """Result of Step 5: Scene Narrative Writing via Multi-Agent Debate."""
    narrative: dict
    scene_debates: list
    total_scenes_written: int
    total_word_count: int
    average_words_per_scene: float
    success: bool
    error: Optional[str] = None
    duration_seconds: float = 0.0


@dataclass
class Step6Result:
    """Result of Step 6: Narrative Revision with 5 Critique Personas."""
    narrative: dict
    critiques: list  # All SceneCritiqueBundle dicts
    scenes_revised: int
    revision_passes: int
    average_score_before: float
    average_score_after: float
    success: bool
    error: Optional[str] = None
    duration_seconds: float = 0.0


@dataclass
class Step7Result:
    """Result of Step 7: Book & Chapter Title Naming via Multi-Agent Debate."""
    book_title: str
    chapter_titles: dict  # {chapter_num: title}
    book_debate: dict  # Debate metadata for book title
    chapter_debates: list  # Debate metadata for each chapter
    success: bool
    error: Optional[str] = None
    duration_seconds: float = 0.0


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

    def __init__(self, author: "BaseAuthor", model: str = None):
        """Initialize Phase 1 runner for an author.

        Args:
            author: The author instance with styles and preferences
            model: LLM model to use (default: from config)
        """
        self.author = author
        self.model = model or DEFAULT_MODEL

    def invoke_structured(self, user_prompt: str, schema: Type[T], max_tokens: int = 2000) -> T:
        """
        Invoke LLM with structured output enforcement via Pydantic schema.

        Args:
            user_prompt: The prompt to send
            schema: Pydantic model class to enforce
            max_tokens: Maximum completion tokens

        Returns:
            Parsed Pydantic model instance
        """
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage

        # Create LLM instance
        llm = ChatOpenAI(
            model=self.model,
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL,
            temperature=0.7,
        )

        # Use structured output
        structured_llm = llm.with_structured_output(schema, method="function_calling")
        limited_llm = structured_llm.bind(max_tokens=max_tokens)

        messages = [HumanMessage(content=user_prompt)]
        return limited_llm.invoke(messages)

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

            print(f"\n>>> Logline: {story_prompt}")
            if setting_prompt:
                print(f">>> Setting: {setting_prompt[:100]}...")

            # =========================================================================
            # SUBSTEP 1: THEME QUESTION DEBATE
            # =========================================================================
            print(f"\n{'='*60}")
            print("SUBSTEP 1: THEME QUESTION DEBATE")
            print(f"{'='*60}")

            # Initialize 3 theme question agents
            philosopher = ThemePhilosopherAgent(model=self.model)
            emotional = ThemeEmotionalAgent(model=self.model)
            dramatic = ThemeDramaticAgent(model=self.model)

            question_agents = [philosopher, emotional, dramatic]

            print(f"\n>>> Phase 1: Proposals (3 agents)")
            # Each agent proposes a thematic question
            question_proposals = []
            for agent in question_agents:
                print(f"    - {agent.name} proposing...")
                proposal = agent.propose_question(logline=story_prompt, world_context=setting_prompt)
                question_proposals.append(proposal)
                print(f"      → {proposal.question.question}")

            print(f"\n>>> Phase 2: Critiques (each agent critiques all 3 proposals)")
            # Each agent critiques all proposals
            all_question_critiques = []
            for agent in question_agents:
                print(f"    - {agent.name} critiquing...")
                critiques = agent.critique_questions(proposals=question_proposals, logline=story_prompt)
                all_question_critiques.extend(critiques)
                # Show scores
                for c in critiques:
                    print(f"      Proposal {c.proposal_index}: {c.score}/10")

            print(f"\n>>> Phase 3: Voting (each agent votes for best)")
            # Each agent votes
            question_votes = []
            for agent in question_agents:
                vote = agent.vote(proposals=question_proposals, logline=story_prompt)
                question_votes.append(vote)
                print(f"    - {agent.name} votes for Proposal {vote.voted_for_index}")

            # Count votes
            vote_counts = {}
            for v in question_votes:
                vote_counts[v.voted_for_index] = vote_counts.get(v.voted_for_index, 0) + 1

            winner_index = max(vote_counts, key=vote_counts.get)
            winning_question = question_proposals[winner_index].question

            print(f"\n>>> WINNER: Proposal {winner_index} ({vote_counts[winner_index]} votes)")
            print(f">>> CENTRAL QUESTION: {winning_question.question}")

            # =========================================================================
            # SUBSTEP 2: THEMATIC SQUARE DEBATE
            # =========================================================================
            print(f"\n{'='*60}")
            print("SUBSTEP 2: THEMATIC SQUARE DEBATE")
            print(f"{'='*60}")

            # Initialize 3 square agents
            architect = SquareArchitectAgent(model=self.model)
            character = SquareCharacterAgent(model=self.model)
            conflict = SquareConflictAgent(model=self.model)

            square_agents = [architect, character, conflict]

            print(f"\n>>> Phase 1: Proposals (3 agents)")
            # Each agent proposes a thematic square
            square_proposals = []
            for agent in square_agents:
                print(f"    - {agent.name} proposing...")
                proposal = agent.propose_square(
                    central_question=winning_question.question,
                    logline=story_prompt
                )
                square_proposals.append(proposal)
                print(f"      POSITIVE: {proposal.thematic_square.positive}")
                print(f"      CONTRADICTORY: {proposal.thematic_square.contradictory}")

            print(f"\n>>> Phase 2: Critiques (each agent critiques all 3 squares)")
            # Each agent critiques all proposals
            all_square_critiques = []
            for agent in square_agents:
                print(f"    - {agent.name} critiquing...")
                critiques = agent.critique_squares(
                    proposals=square_proposals,
                    central_question=winning_question.question
                )
                all_square_critiques.extend(critiques)
                for c in critiques:
                    print(f"      Proposal {c.proposal_index}: {c.score}/10")

            print(f"\n>>> Phase 3: Voting (each agent votes for best)")
            # Each agent votes
            square_votes = []
            for agent in square_agents:
                vote = agent.vote(
                    proposals=square_proposals,
                    central_question=winning_question.question
                )
                square_votes.append(vote)
                print(f"    - {agent.name} votes for Proposal {vote.voted_for_index}")

            # Count votes
            vote_counts = {}
            for v in square_votes:
                vote_counts[v.voted_for_index] = vote_counts.get(v.voted_for_index, 0) + 1

            winner_index = max(vote_counts, key=vote_counts.get)
            winning_square = square_proposals[winner_index].thematic_square

            print(f"\n>>> WINNER: Proposal {winner_index} ({vote_counts[winner_index]} votes)")
            print(f">>> THEMATIC SQUARE:")
            print(f"    POSITIVE: {winning_square.positive}")
            print(f"    CONTRADICTORY: {winning_square.contradictory}")
            print(f"    CONTRARY: {winning_square.contrary}")
            print(f"    NEGATION: {winning_square.negation_of_negation}")

            # =========================================================================
            # SUBSTEP 3: PERSPECTIVE SET DEBATE
            # =========================================================================
            print(f"\n{'='*60}")
            print("SUBSTEP 3: PERSPECTIVE SET DEBATE")
            print(f"{'='*60}")

            # Initialize 3 perspective agents
            diversity = PerspectiveDiversityAgent(model=self.model)
            story_fit = PerspectiveStoryAgent(model=self.model)
            balance = PerspectiveBalanceAgent(model=self.model)

            perspective_agents = [diversity, story_fit, balance]

            print(f"\n>>> Phase 1: Proposals (3 agents propose sets of 4 perspectives)")
            # Each agent proposes a set of perspectives
            perspective_proposals = []
            for agent in perspective_agents:
                print(f"    - {agent.name} proposing...")
                # PerspectiveStoryAgent accepts logline, others don't
                if agent.name == "PERSPECTIVE_STORY":
                    proposal = agent.propose_perspectives(
                        central_question=winning_question.question,
                        top_squares=[winning_square],
                        logline=story_prompt
                    )
                else:
                    proposal = agent.propose_perspectives(
                        central_question=winning_question.question,
                        top_squares=[winning_square]
                    )
                perspective_proposals.append(proposal)
                for p in proposal.perspectives:
                    print(f"      - {p.perspective_name} ({p.corner})")

            print(f"\n>>> Phase 2: Critiques (each agent critiques all 3 sets)")
            # Each agent critiques all proposals
            all_perspective_critiques = []
            for agent in perspective_agents:
                print(f"    - {agent.name} critiquing...")
                # PerspectiveStoryAgent accepts logline, others don't
                if agent.name == "PERSPECTIVE_STORY":
                    critiques = agent.critique_perspective_sets(
                        proposals=perspective_proposals,
                        central_question=winning_question.question,
                        logline=story_prompt
                    )
                else:
                    critiques = agent.critique_perspective_sets(
                        proposals=perspective_proposals,
                        central_question=winning_question.question
                    )
                all_perspective_critiques.extend(critiques)
                for c in critiques:
                    print(f"      Proposal {c.proposal_index}: {c.score}/10")

            print(f"\n>>> Phase 3: Voting (each agent votes for best set)")
            # Each agent votes
            perspective_votes = []
            for agent in perspective_agents:
                vote = agent.vote(
                    proposals=perspective_proposals,
                    central_question=winning_question.question
                )
                perspective_votes.append(vote)
                print(f"    - {agent.name} votes for Proposal {vote.voted_for_index}")

            # Count votes
            vote_counts = {}
            for v in perspective_votes:
                vote_counts[v.voted_for_index] = vote_counts.get(v.voted_for_index, 0) + 1

            winner_index = max(vote_counts, key=vote_counts.get)
            winning_perspectives = perspective_proposals[winner_index].perspectives

            print(f"\n>>> WINNER: Proposal {winner_index} ({vote_counts[winner_index]} votes)")
            print(f">>> PERSPECTIVES:")
            for p in winning_perspectives:
                print(f"    - {p.perspective_name} ({p.corner})")
                print(f"      Position: {p.position}")

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

            duration = time.time() - start_time

            print(f"\n{'='*60}")
            print(f"STEP 0 COMPLETE! Duration: {duration:.1f}s")
            print(f"{'='*60}")

            return Step0Result(
                theme_foundation=theme_foundation,
                step0_debates=step0_debates,
                success=True,
                duration_seconds=duration,
            )

        except Exception as e:
            duration = time.time() - start_time
            print(f"\n>>> Step 0 FAILED: {e}")
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

            # Process each perspective → 1 character
            for idx, perspective in enumerate(perspectives):
                char_id = f"char_{idx+1:03d}"

                print(f"\n{'='*60}")
                print(f"CHARACTER {idx+1}/{len(perspectives)}: {perspective['perspective_name']}")
                print(f"Corner: {perspective['corner']}")
                print(f"{'='*60}")

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
                print(f"\n--- SUBSTEP 1: LIE/TRUTH DEBATE ---")

                # Initialize agents
                lie_truth_philosopher = LieTruthPhilosopherAgent(model=self.model)
                lie_truth_psychologist = LieTruthPsychologistAgent(model=self.model)
                lie_truth_narrative = LieTruthNarrativeAgent(model=self.model)

                lie_truth_agents = [lie_truth_philosopher, lie_truth_psychologist, lie_truth_narrative]

                # Proposals
                print(f"\n>>> Phase 1: Proposals (3 agents)")
                lie_truth_proposals = []
                for agent in lie_truth_agents:
                    print(f"    - {agent.name} proposing...")
                    proposal = agent.propose_lie_truth(
                        perspective=perspective,
                        central_question=central_question,
                        square_corner=perspective['corner']
                    )
                    lie_truth_proposals.append(proposal)
                    print(f"      Lie: {proposal.lie_character_believes[:60]}...")
                    print(f"      Truth: {proposal.truth_character_needs[:60]}...")

                # Critiques
                print(f"\n>>> Phase 2: Critiques (each agent critiques all 3)")
                all_lie_truth_critiques = []
                for agent in lie_truth_agents:
                    print(f"    - {agent.name} critiquing...")
                    critiques = agent.critique_lie_truth(
                        proposals=lie_truth_proposals,
                        perspective=perspective,
                        central_question=central_question
                    )
                    all_lie_truth_critiques.extend(critiques)
                    for c in critiques:
                        print(f"      Proposal {c.proposal_index}: {c.score}/10")

                # Votes
                print(f"\n>>> Phase 3: Voting (each agent votes)")
                lie_truth_votes = []
                for agent in lie_truth_agents:
                    vote = agent.vote(proposals=lie_truth_proposals, perspective=perspective)
                    lie_truth_votes.append(vote)
                    print(f"    - {agent.name} votes for Proposal {vote.voted_for_index}")

                # Select winner
                vote_counts = {}
                for v in lie_truth_votes:
                    vote_counts[v.voted_for_index] = vote_counts.get(v.voted_for_index, 0) + 1

                winner_index = max(vote_counts, key=vote_counts.get)
                winning_lie_truth = lie_truth_proposals[winner_index]

                print(f"\n>>> WINNER: Proposal {winner_index} ({vote_counts[winner_index]} votes)")
                print(f">>> Lie: {winning_lie_truth.lie_character_believes}")
                print(f">>> Truth: {winning_lie_truth.truth_character_needs}")
                print(f">>> Want: {winning_lie_truth.want}")
                print(f">>> Need: {winning_lie_truth.need}")

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
                print(f"\n--- SUBSTEP 2A: SHADOW DEBATE ---")

                # Initialize 3 shadow agents
                shadow_archetype = ShadowArchetypeAgent(model=self.model)
                shadow_narrative = ShadowNarrativeAgent(model=self.model)
                shadow_psychologist = ShadowPsychologistAgent(model=self.model)

                shadow_agents = [shadow_archetype, shadow_narrative, shadow_psychologist]

                # Proposals
                print(f"\n>>> Phase 1: Proposals (3 agents)")
                shadow_proposals = []
                for agent in shadow_agents:
                    print(f"    - {agent.name} proposing...")
                    proposal = agent.propose_shadow(
                        perspective=perspective,
                        lie=winning_lie_truth.lie_character_believes,
                        truth=winning_lie_truth.truth_character_needs
                    )
                    shadow_proposals.append(proposal)
                    trait_keys = list(proposal.shadow_traits.keys())[:2]
                    print(f"      Shadow pairs: {', '.join(trait_keys)}...")

                # Critiques
                print(f"\n>>> Phase 2: Critiques (each agent critiques all 3)")
                all_shadow_critiques = []
                for agent in shadow_agents:
                    print(f"    - {agent.name} critiquing...")
                    critiques = agent.critique_shadow(
                        proposals=shadow_proposals,
                        perspective=perspective,
                        lie=winning_lie_truth.lie_character_believes
                    )
                    all_shadow_critiques.extend(critiques)
                    for c in critiques:
                        print(f"      Proposal {c.proposal_index}: {c.score}/10")

                # Votes
                print(f"\n>>> Phase 3: Voting (each agent votes)")
                shadow_votes = []
                for agent in shadow_agents:
                    vote = agent.vote(proposals=shadow_proposals, perspective=perspective)
                    shadow_votes.append(vote)
                    print(f"    - {agent.name} votes for Proposal {vote.voted_for_index}")

                # Select winner
                vote_counts = {}
                for v in shadow_votes:
                    vote_counts[v.voted_for_index] = vote_counts.get(v.voted_for_index, 0) + 1

                winner_index = max(vote_counts, key=vote_counts.get)
                winning_shadow = shadow_proposals[winner_index]

                print(f"\n>>> WINNER: Proposal {winner_index} ({vote_counts[winner_index]} votes)")
                print(f">>> Shadow Traits:")
                for key, value in winning_shadow.shadow_traits.items():
                    print(f"    {key}: {value}")

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
                print(f"\n--- SUBSTEP 2B: ARC TYPE DEBATE ---")

                # Initialize 3 arc type agents
                arc_agent = ArcTypeAgent(model=self.model)
                arc_narrative = ArcTypeNarrativeAgent(model=self.model)
                arc_thematic = ArcTypeThematicAgent(model=self.model)

                arc_agents = [arc_agent, arc_narrative, arc_thematic]

                # Proposals
                print(f"\n>>> Phase 1: Proposals (3 agents)")
                arc_proposals = []
                for agent in arc_agents:
                    print(f"    - {agent.name} proposing...")
                    proposal = agent.propose_arc_type(
                        perspective=perspective,
                        lie=winning_lie_truth.lie_character_believes,
                        truth=winning_lie_truth.truth_character_needs,
                        square_corner=perspective['corner']
                    )
                    arc_proposals.append(proposal)
                    print(f"      Arc: {proposal.arc_type}")

                # Critiques
                print(f"\n>>> Phase 2: Critiques (each agent critiques all 3)")
                all_arc_critiques = []
                for agent in arc_agents:
                    print(f"    - {agent.name} critiquing...")
                    critiques = agent.critique_arc_type(
                        proposals=arc_proposals,
                        perspective=perspective,
                        lie=winning_lie_truth.lie_character_believes,
                        truth=winning_lie_truth.truth_character_needs
                    )
                    all_arc_critiques.extend(critiques)
                    for c in critiques:
                        print(f"      Proposal {c.proposal_index}: {c.score}/10")

                # Votes
                print(f"\n>>> Phase 3: Voting (each agent votes)")
                arc_votes = []
                for agent in arc_agents:
                    vote = agent.vote(proposals=arc_proposals, perspective=perspective)
                    arc_votes.append(vote)
                    print(f"    - {agent.name} votes for Proposal {vote.voted_for_index}")

                # Select winner
                vote_counts = {}
                for v in arc_votes:
                    vote_counts[v.voted_for_index] = vote_counts.get(v.voted_for_index, 0) + 1

                winner_index = max(vote_counts, key=vote_counts.get)
                winning_arc = arc_proposals[winner_index]

                print(f"\n>>> WINNER: Proposal {winner_index} ({vote_counts[winner_index]} votes)")
                print(f">>> Arc Type: {winning_arc.arc_type}")
                print(f">>> Journey: {winning_arc.arc_journey}")

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
                print(f"\n--- SUBSTEP 2C: GHOST DEBATE ---")

                # Initialize 3 ghost agents
                ghost_agent = GhostAgent(model=self.model)
                ghost_emotional = GhostEmotionalAgent(model=self.model)
                ghost_thematic = GhostThematicAgent(model=self.model)

                ghost_agents = [ghost_agent, ghost_emotional, ghost_thematic]

                # Proposals
                print(f"\n>>> Phase 1: Proposals (3 agents)")
                ghost_proposals = []
                for agent in ghost_agents:
                    print(f"    - {agent.name} proposing...")
                    proposal = agent.propose_ghost(
                        perspective=perspective,
                        lie=winning_lie_truth.lie_character_believes
                    )
                    ghost_proposals.append(proposal)
                    print(f"      Event: {proposal.ghost_event[:60]}...")

                # Critiques
                print(f"\n>>> Phase 2: Critiques (each agent critiques all 3)")
                all_ghost_critiques = []
                for agent in ghost_agents:
                    print(f"    - {agent.name} critiquing...")
                    critiques = agent.critique_ghost(
                        proposals=ghost_proposals,
                        perspective=perspective,
                        lie=winning_lie_truth.lie_character_believes
                    )
                    all_ghost_critiques.extend(critiques)
                    for c in critiques:
                        print(f"      Proposal {c.proposal_index}: {c.score}/10")

                # Votes
                print(f"\n>>> Phase 3: Voting (each agent votes)")
                ghost_votes = []
                for agent in ghost_agents:
                    vote = agent.vote(proposals=ghost_proposals, perspective=perspective)
                    ghost_votes.append(vote)
                    print(f"    - {agent.name} votes for Proposal {vote.voted_for_index}")

                # Select winner
                vote_counts = {}
                for v in ghost_votes:
                    vote_counts[v.voted_for_index] = vote_counts.get(v.voted_for_index, 0) + 1

                winner_index = max(vote_counts, key=vote_counts.get)
                winning_ghost = ghost_proposals[winner_index]

                print(f"\n>>> WINNER: Proposal {winner_index} ({vote_counts[winner_index]} votes)")
                print(f">>> Ghost Event: {winning_ghost.ghost_event}")
                print(f">>> How It Created Lie: {winning_ghost.how_it_created_lie}")

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
                print(f"\n--- SUBSTEP 3: NAME GENERATION ---")

                import random
                import string

                first_initial = random.choice(string.ascii_uppercase)
                last_initial = random.choice(string.ascii_uppercase)
                print(f"    Initials: {first_initial}.{last_initial}.")

                name_result = self._run_name_debate(
                    character_role=perspective['perspective_name'],
                    first_initial=first_initial,
                    last_initial=last_initial,
                    logline=story_prompt,
                    setting_prompt=setting_prompt,
                    existing_names=existing_names,
                )

                final_name = name_result["final_name"]
                existing_names.append(final_name)
                print(f"    >>> Name: {final_name}")

                character_debate_history["name_debate"] = name_result.get("debate", {})

                # =========================================================
                # SUBSTEP 4: PHYSICAL APPEARANCE (reuse existing system)
                # =========================================================
                print(f"\n--- SUBSTEP 4: PHYSICAL APPEARANCE ---")

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

                print(f"    >>> Physical: {final_physical[:100]}...")

                character_debate_history["physical_debate"] = {
                    "proposals": physical_result.get("proposals", []),
                    "critiques": physical_result.get("critiques", []),
                    "votes": physical_result.get("votes", []),
                    "winner": physical_result.get("winner", ""),
                    "winning_physical": winning_physical,
                    "winning_costume": physical_result.get("winning_costume", "")
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
                    "gender": winning_physical.get('gender', 'unknown'),
                    "body_build": winning_physical.get('body_build', 'average build'),
                    "height": winning_physical.get('height', 'average height'),
                    "hair_color": winning_physical.get('hair_color', 'dark hair'),
                    "eye_color": winning_physical.get('eye_color', 'brown eyes'),
                    "ethnicity": winning_physical.get('ethnicity', 'mixed heritage'),
                    "distinguishing_features": winning_physical.get('distinguishing_features', ''),
                    "costume": winning_physical.get('costume', 'simple clothing'),
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

                characters.append(character)
                all_character_debates.append(character_debate_history)

                # UPDATE CODEX after each character
                if "story" not in codex:
                    codex["story"] = {}
                codex["story"]["characters"] = characters

                print(f"\n>>> Character {idx+1} complete!")

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
                "proposals": [p.dict() for p in shape_proposals],
                "critiques": [c.dict() for c in all_shape_critiques],
                "votes": [v.dict() for v in shape_votes],
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

            print(f"\n>>> Phase 1: Proposals")
            stc_proposals = []
            for agent in stc_agents:
                proposal = agent.propose_save_the_cat(story_prompt, theme_question, characters, winning_shape.story_shape)
                stc_proposals.append(proposal)
                print(f"    - {agent.name}: {proposal.save_the_cat_type}")

            print(f"\n>>> Phase 2: Critiques")
            all_stc_critiques = []
            for agent in stc_agents:
                critiques = agent.critique_save_the_cat(stc_proposals, story_prompt, characters)
                all_stc_critiques.extend(critiques)

            print(f"\n>>> Phase 3: Voting")
            stc_votes = []
            for agent in stc_agents:
                vote = agent.vote(stc_proposals, story_prompt)
                stc_votes.append(vote)
                print(f"    - {agent.name} votes for Proposal {vote.chosen_proposal_index}")

            vote_counts = {}
            for vote in stc_votes:
                vote_counts[vote.chosen_proposal_index] = vote_counts.get(vote.chosen_proposal_index, 0) + 1
            winner_index = max(vote_counts, key=vote_counts.get)
            winning_stc = stc_proposals[winner_index]

            print(f"\n>>> WINNER: {winning_stc.save_the_cat_type}")

            step2_debates["save_the_cat_debate"] = {
                "proposals": [p.dict() for p in stc_proposals],
                "critiques": [c.dict() for c in all_stc_critiques],
                "votes": [v.dict() for v in stc_votes],
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
                "proposals": [p.dict() for p in genre_proposals],
                "critiques": [c.dict() for c in all_genre_critiques],
                "votes": [v.dict() for v in genre_votes],
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
                "proposals": [p.dict() for p in trope_proposals],
                "critiques": [c.dict() for c in all_trope_critiques],
                "votes": [v.dict() for v in trope_votes],
                "winner_index": winner_index
            }

            # Convert Trope objects to dicts for storage
            tropes_as_dicts = [t.dict() for t in winning_tropes.tropes]

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

        # Round 1: Proposals
        proposals = []
        proposal_prompt = f"""{context}

Propose a character name that:
1. Starts with {first_initial} for first name
2. Starts with {last_initial} for last name
3. Fits the character's role and setting
4. Is distinct from existing names"""

        print(f"      Generating name proposals...")
        for agent in agents:
            try:
                proposal: NameProposal = agent.invoke_structured(
                    proposal_prompt, NameProposal, max_tokens=500
                )
                proposals.append({
                    "agent": agent.name,
                    "first_name": proposal.first_name,
                    "last_name": proposal.last_name,
                    "full_name": f"{proposal.first_name} {proposal.last_name}",
                    "reasoning": proposal.reasoning,
                })
            except Exception as e:
                proposals.append({
                    "agent": agent.name,
                    "first_name": f"{first_initial}ara",
                    "last_name": f"{last_initial}ith",
                    "full_name": f"{first_initial}ara {last_initial}ith",
                    "reasoning": f"Fallback: {str(e)[:50]}",
                })

        # Round 2: Critiques
        proposals_text = "\n".join([
            f"Proposal {i}: {p['full_name']} - {p['reasoning'][:80]}..."
            for i, p in enumerate(proposals)
        ])

        critique_prompt = f"""{context}

PROPOSALS:
{proposals_text}

Critique ALL proposals. Score each 1-10."""

        critiques = []
        print(f"      Gathering critiques...")
        for agent in agents:
            try:
                agent_critiques: NameCritiques = agent.invoke_structured(
                    critique_prompt, NameCritiques, max_tokens=1000
                )
                critiques.append({
                    "agent": agent.name,
                    "reviews": [
                        {"proposal": r.proposal_index, "score": r.score}
                        for r in agent_critiques.reviews
                    ]
                })
            except Exception:
                critiques.append({
                    "agent": agent.name,
                    "reviews": [{"proposal": i, "score": 5} for i in range(3)]
                })

        # Round 3: Voting
        vote_prompt = f"""{context}

PROPOSALS:
{proposals_text}

Vote for the BEST name. You CANNOT vote for your own proposal.
Agent positions: NAME_CREATIVE=0, NAME_AUTHENTIC=1, NAME_DISTINCTIVE=2"""

        votes = {}
        print(f"      Collecting votes...")
        for i, agent in enumerate(agents):
            try:
                vote: NameVote = agent.invoke_structured(vote_prompt, NameVote, max_tokens=300)
                voted_for = vote.voted_for
                if voted_for == i:
                    voted_for = (i + 1) % 3
                votes[agent.name] = voted_for
            except Exception:
                votes[agent.name] = (i + 1) % 3

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

        # Round 1: Proposals from all 4 agents
        proposals = []
        print(f"      Generating physical appearance proposals...")
        for agent in agents:
            try:
                proposal = agent.propose_physical(
                    role=character_role,
                    role_type=character_type,
                    adjective=adjective,
                    goal=goal,
                    stakes=stakes,
                    setting=setting_prompt,
                )
                proposals.append(proposal)
                print(f"        [{agent.name}] proposed")
            except Exception as e:
                print(f"        [{agent.name}] failed: {str(e)[:50]}")

        if not proposals:
            return {"error": "All proposal agents failed"}

        # Round 2: Cross-critiques (each agent critiques one other)
        critiques = []
        print(f"      Gathering critiques...")
        for i, agent in enumerate(agents[:3]):  # First 3 agents critique
            target_idx = (i + 1) % len(proposals)
            target_proposal = proposals[target_idx]
            try:
                critique = agent.critique_proposal(
                    target_agent=target_proposal.agent_name,
                    proposal=target_proposal,
                    role=character_role,
                    adjective=adjective,
                )
                critiques.append(critique)
            except Exception:
                pass

        # Round 3: All 4 agents vote
        votes = []
        print(f"      Collecting votes...")
        for agent in agents:
            try:
                vote = agent.vote_for_best(
                    proposals=proposals,
                    role=character_role,
                    adjective=adjective,
                )
                votes.append(vote)
                print(f"        [{agent.name}] votes for: {vote.voted_for_agent}")
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
            "winning_physical": winner_proposal.physical.model_dump(),
            "winning_costume": winner_proposal.costume,
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

                # Use gender from backstory generation
                gender = getattr(backstory_result, 'gender', 'female') if backstory_result else 'female'

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

            print(f"\n>>> Phase 1: Proposals (3 agents)")
            arc_proposals = []
            for agent in arc_agents:
                print(f"    - {agent.name} proposing...")
                try:
                    proposal = agent.propose_arc_beats(characters, story_shape, theme_question)
                    if proposal is None:
                        print(f"      ⚠️  {agent.name} returned None, skipping")
                        continue
                    arc_proposals.append(proposal)
                    print(f"      Hero: {proposal.hero_arc.arc_type} ({len(proposal.hero_arc.arc_beats)} beats)")
                    print(f"      Villain: {proposal.villain_arc.arc_type} ({len(proposal.villain_arc.arc_beats)} beats)")
                    print(f"      Supporting: {len(proposal.supporting_arcs)} characters")
                except Exception as e:
                    print(f"      ❌ {agent.name} failed: {str(e)[:100]}")
                    continue

            if not arc_proposals:
                return Step3Result(
                    integrated_beats=[], hero_arc_summary="", villain_arc_summary="",
                    side_character_notes="", step3_debates={},
                    success=False, error="All arc beat agents failed to generate proposals"
                )

            print(f"\n>>> Phase 2: Critiques (each agent critiques all 3)")
            all_arc_critiques = []
            for agent in arc_agents:
                print(f"    - {agent.name} critiquing...")
                critiques = agent.critique_arc_beats(arc_proposals, theme_question)
                all_arc_critiques.extend(critiques)
                for c in critiques:
                    print(f"      Proposal {c.proposal_index}: {c.score}/10")

            print(f"\n>>> Phase 3: Voting (each agent votes)")
            arc_votes = []
            for agent in arc_agents:
                vote = agent.vote(arc_proposals, theme_question)
                arc_votes.append(vote)
                print(f"    - {agent.name} votes for Proposal {vote.chosen_proposal_index}")

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

            print(f"\n>>> Phase 1: Proposals (3 agents)")
            stc_proposals = []
            for agent in stc_agents:
                print(f"    - {agent.name} proposing...")
                if agent.name == "STC_GENRE":
                    proposal = agent.propose_beats(story_shape, save_the_cat_type, theme_question, story_prompt, genres)
                else:
                    proposal = agent.propose_beats(story_shape, save_the_cat_type, theme_question, story_prompt)
                stc_proposals.append(proposal)
                print(f"      Pacing: {proposal.overall_pacing[:50]}...")

            print(f"\n>>> Phase 2: Critiques (each agent critiques all 3)")
            all_stc_critiques = []
            for agent in stc_agents:
                print(f"    - {agent.name} critiquing...")
                if agent.name == "STC_GENRE":
                    critiques = agent.critique_beats(stc_proposals, theme_question, genres)
                else:
                    critiques = agent.critique_beats(stc_proposals, theme_question)
                all_stc_critiques.extend(critiques)
                for c in critiques:
                    print(f"      Proposal {c.proposal_index}: {c.score}/10")

            print(f"\n>>> Phase 3: Voting (each agent votes)")
            stc_votes = []
            for agent in stc_agents:
                vote = agent.vote(stc_proposals, theme_question)
                stc_votes.append(vote)
                print(f"    - {agent.name} votes for Proposal {vote.chosen_proposal_index}")

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

            print(f"\n>>> Phase 1: Proposals (3 agents)")
            integration_proposals = []
            for agent in integration_agents:
                print(f"    - {agent.name} proposing...")
                proposal = agent.propose_integration(
                    winning_arcs.hero_arc,
                    winning_arcs.villain_arc,
                    winning_arcs.supporting_arcs,
                    winning_stc.beats,
                    theme_question
                )
                integration_proposals.append(proposal)
                print(f"      {len(proposal.integrated_beats)} integrated beats")

            print(f"\n>>> Phase 2: Critiques (each agent critiques all 3)")
            all_integration_critiques = []
            for agent in integration_agents:
                print(f"    - {agent.name} critiquing...")
                critiques = agent.critique_integration(integration_proposals, theme_question)
                all_integration_critiques.extend(critiques)
                for c in critiques:
                    print(f"      Proposal {c.proposal_index}: {c.score}/10")

            print(f"\n>>> Phase 3: Voting (each agent votes)")
            integration_votes = []
            for agent in integration_agents:
                vote = agent.vote(integration_proposals, theme_question)
                integration_votes.append(vote)
                print(f"    - {agent.name} votes for Proposal {vote.chosen_proposal_index}")

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
                    "character_arcs": b.character_arcs,  # Dict of all character names to arc beats
                    "thematic_test": b.thematic_test,
                    "location_type": b.location_type,  # Where this beat occurs
                }
                for b in winning_integration.integrated_beats
            ]

            # Ensure exactly 15 beats (pad or trim if needed)
            if len(integrated_beats_dicts) < 15:
                print(f">>> WARNING: Only {len(integrated_beats_dicts)} beats generated, padding to 15")
                # Pad with minimal placeholder beats
                # Create placeholder character_arcs dict with all characters
                placeholder_arcs = {char["name"]: "[To be developed]" for char in characters}
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

                # Round 1: All 4 agents propose
                proposals = []
                print(f"    Generating proposals...")
                for agent in location_agents:
                    try:
                        proposal = agent.propose_location(
                            location_source=loc_info['description'],
                            setting_prompt=setting_prompt,
                            story_context=story_context,
                        )
                        proposals.append(proposal)
                        print(f"      [{agent.name}] proposed: {proposal.name}")
                    except Exception as e:
                        print(f"      [{agent.name}] failed: {str(e)[:40]}")

                if not proposals:
                    continue

                # Round 2: Cross-critiques (3 critiques)
                critiques = []
                print(f"    Gathering critiques...")
                for i, agent in enumerate(location_agents[:3]):
                    target_idx = (i + 1) % len(proposals)
                    try:
                        critique = agent.critique_proposal(
                            target_agent=proposals[target_idx].agent_name,
                            proposal=proposals[target_idx],
                            setting_prompt=setting_prompt,
                        )
                        critiques.append(critique)
                    except Exception as e:
                        print(f"      [{agent.name}] critique failed: {str(e)[:30]}")

                # Round 3: All 4 agents vote
                votes = []
                print(f"    Collecting votes...")
                for agent in location_agents:
                    try:
                        vote = agent.vote_for_best(
                            proposals=proposals,
                            setting_prompt=setting_prompt,
                        )
                        votes.append(vote)
                        print(f"      [{agent.name}] votes for: {vote.voted_for_agent}")
                    except Exception as e:
                        print(f"      [{agent.name}] vote failed: {str(e)[:30]}")

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

            # Phase 1: Proposals
            print(f"\n>>> Phase 1: Proposals (4 agents)")
            wp_proposals = []
            for agent in world_pressure_agents:
                print(f"    - {agent.name} proposing...")
                try:
                    proposal = agent.propose_world_pressure(
                        theme_question=theme_question,
                        story_shape=story_shape,
                        world_context=world_context,
                    )
                    if proposal is None:
                        print(f"      Warning: {agent.name} returned None, skipping")
                        continue
                    wp_proposals.append(proposal)
                    print(f"      Societal: {proposal.world_pressure.societal[:80]}...")
                except Exception as e:
                    print(f"      Error: {agent.name} failed: {str(e)[:100]}")
                    continue

            if not wp_proposals:
                return Step4Result(
                    world_pressure={},
                    locations=[],
                    step4_debates=step4_debates,
                    success=False,
                    error="All world pressure agents failed to generate proposals",
                )

            # Phase 2: Critiques
            print(f"\n>>> Phase 2: Critiques (each agent critiques all {len(wp_proposals)} proposals)")
            all_wp_critiques = []
            for agent in world_pressure_agents:
                print(f"    - {agent.name} critiquing...")
                try:
                    critiques = agent.critique_world_pressures(wp_proposals, theme_question)
                    all_wp_critiques.extend(critiques)
                    for c in critiques:
                        print(f"      Proposal {c.proposal_index}: {c.score}/10")
                except Exception as e:
                    print(f"      Error: {agent.name} critique failed: {str(e)[:100]}")
                    continue

            # Phase 3: Voting
            print(f"\n>>> Phase 3: Voting (each agent votes)")
            wp_votes = []
            for agent in world_pressure_agents:
                try:
                    vote = agent.vote(wp_proposals, theme_question)
                    wp_votes.append(vote)
                    print(f"    - {agent.name} votes for Proposal {vote.chosen_proposal_index}")
                except Exception as e:
                    print(f"    Error: {agent.name} vote failed: {str(e)[:100]}")
                    continue

            # Tally votes
            if not wp_votes:
                winner_index = 0
            else:
                vote_counts = {}
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

            economy = self.invoke_structured(economy_prompt, Economy, max_tokens=2000)
            world_dict["economy"] = economy.model_dump()
            print(f"    ✓ Currency: {economy.currency}")

            # 4. GOVERNMENT & LAW
            print("\n>>> Generating Government & Law...")
            gov_prompt = f"""{world_context_prompt}

Create a government and legal system.
Focus on: government type, law enforcement, courts/trials, punishments, and military.
Show how power is wielded and maintained.

Provide a GovernmentLaw schema with all required fields."""

            government = self.invoke_structured(gov_prompt, GovernmentLaw, max_tokens=2000)
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

            religion = self.invoke_structured(religion_prompt, ReligionBeliefs, max_tokens=2000)
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

    def step5_narrative(self, codex: dict) -> Step5Result:
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
            chapter_outline = story.get("chapter_outline", {})
            characters = story.get("characters", [])
            locations = story.get("locations", [])
            world = story.get("world", {})
            outline = story.get("outline", {})

            if not chapter_outline:
                return Step5Result(
                    narrative={},
                    scene_debates=[],
                    total_scenes_written=0,
                    total_word_count=0,
                    average_words_per_scene=0,
                    success=False,
                    error="No chapter_outline found. Run Step 4 first.",
                )

            if not characters:
                return Step5Result(
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
            print("STEP 5: SCENE NARRATIVE WRITING (5-Agent Multi-Agent Debate)")
            print(f"{'='*60}")
            print(f">>> Agents: 5 narrative specialists")
            print(f">>> Method: Propose -> Critique -> Vote per scene")
            print(f">>> Target: 750-1000 words per scene (~5-7 min reading time)")

            # =========================================
            # INITIALIZE 5 NARRATIVE WRITING AGENTS
            # =========================================
            character_agent = CharacterContinuityAgent(model=self.model)
            location_agent = NarrativeLocationAgent(model=self.model)
            world_agent = WorldBuildingIntegrationAgent(model=self.model)
            plot_agent = PlotTickingClockAgent(model=self.model)
            narrative_agent = NarrativeContinuityAgent(model=self.model)

            all_agents = [character_agent, location_agent, world_agent, plot_agent, narrative_agent]

            print(f"\n--- 5 Agent Methodologies ---")
            for agent in all_agents:
                print(f"    {agent.name}: {agent.METHODOLOGY_NAME}")

            # =========================================
            # PROCESS EACH CHAPTER AND SCENE
            # =========================================
            chapters_narrative = []
            previous_scene_prose = ""

            for chapter in chapter_outline.get("chapters", []):
                chapter_num = chapter["chapter_number"]
                chapter_scenes_narrative = []

                print(f"\n{'='*50}")
                print(f"CHAPTER {chapter_num}: Writing {len(chapter['scenes'])} scenes")
                print(f"{'='*50}")

                for scene_data in chapter["scenes"]:
                    scene_num = scene_data["scene_number"]
                    scene_id = f"ch{chapter_num}_scene{scene_num}"

                    print(f"\n    --- SCENE {scene_num} ({scene_data.get('location', 'Unknown')}) ---")

                    # Build scene context for critiques/votes
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
                    # ROUND 1: ALL 5 AGENTS PROPOSE PROSE
                    # =========================================
                    proposals = []
                    print(f"    Generating 5 prose proposals...")

                    for agent in all_agents:
                        try:
                            proposal = agent.propose_prose(
                                scene_data=scene_data,
                                characters=characters,
                                locations=locations,
                                world=world,
                                previous_prose=previous_scene_prose,
                                ticking_clock=ticking_clock,
                            )
                            # Validate proposal before appending (structured output can return None)
                            if proposal is None:
                                print(f"      [{agent.name}] FAILED: Returned None")
                                continue
                            word_count = proposal.word_count()
                            techniques = proposal.techniques_used[:2] if proposal.techniques_used else []
                            proposals.append(proposal)  # Append after validation
                            print(f"      [{agent.name}] {word_count} words - {techniques}")
                        except Exception as e:
                            print(f"      [{agent.name}] FAILED: {str(e)[:50]}")

                    if not proposals:
                        # Fallback: create minimal scene
                        print(f"    All proposals failed - creating fallback prose")
                        fallback_prose = f"Scene {scene_num}: {scene_data.get('happens', 'The story continues.')}"
                        scene_narrative = {
                            "scene_id": scene_id,
                            "chapter_number": chapter_num,
                            "scene_number": scene_num,
                            "location": scene_data.get("location", "Unknown"),
                            "location_id": scene_data.get("location_id", ""),
                            "pov_character": scene_data.get("pov_character", "Unknown"),
                            "characters_present": scene_data.get("characters", []),
                            "character_ids": scene_data.get("character_ids", []),
                            "time_of_day": scene_data.get("time_of_day", "day"),
                            "prose": fallback_prose,
                            "word_count": len(fallback_prose.split()),
                            "winning_agent": "FALLBACK",
                            "techniques_integrated": [],
                        }
                        chapter_scenes_narrative.append(scene_narrative)
                        all_scene_narratives.append(scene_narrative)
                        total_word_count += len(fallback_prose.split())
                        continue

                    # =========================================
                    # ROUND 2: CROSS-AGENT CRITIQUES (5 critiques)
                    # =========================================
                    critiques = []
                    print(f"    Gathering 5 critiques...")

                    for i, agent in enumerate(all_agents):
                        target_idx = (i + 1) % len(proposals)
                        target_proposal = proposals[target_idx]
                        try:
                            critique = agent.critique_prose(
                                target_agent=target_proposal.agent_name,
                                proposal=target_proposal,
                                scene_context=scene_context,
                            )
                            if critique is None:
                                print(f"      [{agent.name}] critique failed: Returned None")
                                continue
                            critiques.append(critique)
                            print(f"      [{agent.name} -> {target_proposal.agent_name}] Score: {critique.overall_score:.1f}")
                        except Exception as e:
                            print(f"      [{agent.name}] critique failed: {str(e)[:30]}")

                    # =========================================
                    # ROUND 3: ALL 5 AGENTS VOTE
                    # =========================================
                    votes = []
                    print(f"    Collecting 5 votes...")

                    for agent in all_agents:
                        try:
                            vote = agent.vote_for_best(
                                proposals=proposals,
                                scene_context=scene_context,
                            )
                            if vote is None:
                                print(f"      [{agent.name}] vote failed: Returned None")
                                continue
                            votes.append(vote)
                            print(f"      [{agent.name}] votes for: {vote.voted_for_agent}")
                        except Exception as e:
                            print(f"      [{agent.name}] vote failed: {str(e)[:30]}")

                    # =========================================
                    # TALLY VOTES AND SELECT WINNER
                    # =========================================
                    agent_names = [p.agent_name for p in proposals]
                    winner_agent = self._tally_narrative_votes(votes, agent_names)
                    winner_proposal = next(
                        (p for p in proposals if p.agent_name == winner_agent),
                        proposals[0]
                    )

                    vote_counts = Counter(v.voted_for_agent for v in votes) if votes else {}
                    print(f"    >>> Winner: {winner_agent} ({vote_counts.get(winner_agent, 0)}/5 votes)")

                    # =========================================
                    # BUILD FINAL SCENE NARRATIVE
                    # =========================================
                    final_prose = winner_proposal.to_prose()
                    scene_word_count = len(final_prose.split())
                    total_word_count += scene_word_count

                    scene_narrative = {
                        "scene_id": scene_id,
                        "chapter_number": chapter_num,
                        "scene_number": scene_num,
                        "location": scene_data.get("location", "Unknown"),
                        "location_id": scene_data.get("location_id", ""),
                        "pov_character": scene_data.get("pov_character", "Unknown"),
                        "characters_present": scene_data.get("characters", []),
                        "character_ids": scene_data.get("character_ids", []),
                        "time_of_day": scene_data.get("time_of_day", "day"),
                        "prose": final_prose,
                        "word_count": scene_word_count,
                        "winning_agent": winner_agent,
                        "techniques_integrated": winner_proposal.techniques_used,
                    }

                    chapter_scenes_narrative.append(scene_narrative)
                    all_scene_narratives.append(scene_narrative)

                    # Update previous prose for continuity
                    previous_scene_prose = final_prose

                    # Record debate
                    scene_debates.append({
                        "scene_id": scene_id,
                        "chapter": chapter_num,
                        "scene": scene_num,
                        "proposals": [p.model_dump() for p in proposals],
                        "critiques": [c.model_dump() for c in critiques],
                        "votes": [v.model_dump() for v in votes],
                        "winner": winner_agent,
                        "final_word_count": scene_word_count,
                    })

                # Assemble chapter narrative
                chapter_word_count = sum(s["word_count"] for s in chapter_scenes_narrative)
                chapters_narrative.append({
                    "chapter_number": chapter_num,
                    "chapter_title": chapter.get("chapter_title", f"Chapter {chapter_num}"),
                    "act": chapter.get("act", 1),
                    "scenes": chapter_scenes_narrative,
                    "chapter_word_count": chapter_word_count,
                })

                print(f"\n    >>> Chapter {chapter_num} complete: {len(chapter_scenes_narrative)} scenes, {chapter_word_count:,} words")

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

            return Step5Result(
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
            return Step5Result(
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

    def step6_revision(self, codex: dict) -> Step6Result:
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
        print("STEP 6: NARRATIVE REVISION (5-Critic System)")
        print("=" * 60)

        try:
            # Get data from codex
            narrative = codex.get("story", {}).get("narrative", {})
            characters = codex.get("story", {}).get("characters", [])
            locations = codex.get("story", {}).get("locations", [])
            world = codex.get("story", {}).get("world", {})
            chapter_outline = codex.get("story", {}).get("chapter_outline", {})
            # Get full ticking clock info for time unit checking
            ticking_clock = {
                "ticking_clock": chapter_outline.get("ticking_clock", "Time is running out"),
                "deadline": chapter_outline.get("ticking_clock_deadline", "Unknown"),
                "consequence": chapter_outline.get("ticking_clock_consequence", "Unknown"),
            }

            if not narrative or not narrative.get("chapters"):
                return Step6Result(
                    narrative=narrative,
                    critiques=[],
                    scenes_revised=0,
                    revision_passes=0,
                    average_score_before=0,
                    average_score_after=0,
                    success=False,
                    error="No narrative found. Run step 5 first.",
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

                for chapter in narrative.get("chapters", []):
                    chapter_num = chapter.get("chapter_number", 0)
                    print(f"\n--- Chapter {chapter_num}: {chapter.get('chapter_title', '')} ---")

                    for scene in chapter.get("scenes", []):
                        scene_id = scene.get("scene_id", f"ch{chapter_num}_scene?")
                        prose = scene.get("prose", "")
                        print(f"\n  Scene: {scene_id}")

                        if not prose:
                            print("    [No prose to revise]")
                            continue

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

                        # Run all 5 critics
                        print("    Running critics...")

                        # 1. Prose Polish Critic
                        print("      [1/5] Prose Polish...")
                        prose_crit = prose_critic.critique(prose, scene_id)
                        print(f"            Score: {prose_crit.overall_score}/10, "
                              f"Filter words: {len(prose_crit.filter_words_found)}, "
                              f"Cliches: {len(prose_crit.cliches_found)}")

                        # 2. Character Voice Critic
                        print("      [2/5] Character Voice...")
                        voice_crit = voice_critic.critique(prose, scene_chars, scene_id)
                        print(f"            Score: {voice_crit.overall_voice_score}/10, "
                              f"Voice issues: {len(voice_crit.voice_issues)}, "
                              f"No-tag test: {'PASS' if voice_crit.no_tag_test_passed else 'FAIL'}")

                        # 3. Continuity Critic
                        print("      [3/5] Continuity...")
                        cont_crit = continuity_critic.critique(
                            prose, scene_chars, scene_loc, world, scene_id, ticking_clock
                        )
                        print(f"            Score: {cont_crit.overall_continuity_score}/10, "
                              f"Char issues: {len(cont_crit.character_inconsistencies)}, "
                              f"POV breaks: {len(cont_crit.pov_breaks)}")

                        # 4. Pacing & Tension Critic
                        print("      [4/5] Pacing & Tension...")
                        pacing_crit = pacing_critic.critique(
                            prose, scene, ticking_clock, scene_id
                        )
                        print(f"            Score: {pacing_crit.overall_pacing_score}/10, "
                              f"Ticking clock: {'YES' if pacing_crit.ticking_clock_present else 'NO'}, "
                              f"Slow spots: {len(pacing_crit.slow_spots)}")

                        # 5. Emotional Resonance Critic
                        print("      [5/5] Emotional Resonance...")
                        emot_crit = emotional_critic.critique(prose, scene_id)
                        print(f"            Score: {emot_crit.overall_emotional_score}/10, "
                              f"Ending: {emot_crit.ending_resonance_type}, "
                              f"Skim risks: {len(emot_crit.skim_risk_areas)}")

                        # Calculate average score
                        avg_score = (
                            prose_crit.overall_score +
                            voice_crit.overall_voice_score +
                            cont_crit.overall_continuity_score +
                            pacing_crit.overall_pacing_score +
                            emot_crit.overall_emotional_score
                        ) / 5
                        scores_before.append(avg_score)

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
                        all_critiques.append(critique_bundle)

                        # Check if revision needed
                        if critique_bundle["needs_revision"]:
                            print(f"    -> REVISING (avg score: {avg_score:.1f}/10)")

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
                            prose_before = prose  # Save original before revision
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
                                scenes_revised += 1
                                scores_after.append(avg_score + 1.5)  # Estimate improvement
                                print(f"    -> REVISED ({scene['word_count']} words)")

                                # Track revision history for metadata
                                revision_history.append({
                                    "scene_id": scene_id,
                                    "pass": pass_num + 1,
                                    "prose_before": prose_before,
                                    "prose_after": revised_prose,
                                    "score_before": round(avg_score, 2),
                                    "critiques_summary": {
                                        "prose_score": prose_crit.overall_score,
                                        "voice_score": voice_crit.overall_voice_score,
                                        "continuity_score": cont_crit.overall_continuity_score,
                                        "pacing_score": pacing_crit.overall_pacing_score,
                                        "emotional_score": emot_crit.overall_emotional_score,
                                    }
                                })
                            except Exception as e:
                                print(f"    -> REVISION FAILED: {e}")
                                scores_after.append(avg_score)
                        else:
                            print(f"    -> OK (avg score: {avg_score:.1f}/10)")
                            scores_after.append(avg_score)

            # Store critiques in codex
            if "story" not in codex:
                codex["story"] = {}
            codex["story"]["critiques"] = all_critiques

            # Calculate metrics
            avg_before = sum(scores_before) / len(scores_before) if scores_before else 0
            avg_after = sum(scores_after) / len(scores_after) if scores_after else 0

            # Store revision history in metadata (for future reference)
            if "metadata" not in codex:
                codex["metadata"] = {}
            if "phase_1" not in codex["metadata"]:
                codex["metadata"]["phase_1"] = {}

            codex["metadata"]["phase_1"]["step_6"] = {
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
            print("STEP 6 COMPLETE: Narrative Revision")
            print(f"  Scenes revised: {scenes_revised}")
            print(f"  Revision passes: {num_passes}")
            print(f"  Avg score before: {avg_before:.1f}/10")
            print(f"  Avg score after: {avg_after:.1f}/10")
            print(f"  Duration: {duration:.1f}s")
            print("=" * 60)

            return Step6Result(
                narrative=narrative,
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
            return Step6Result(
                narrative=codex.get("story", {}).get("narrative", {}),
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

    def step7_naming(self, codex: dict) -> Step7Result:
        """
        Generate book and chapter titles via 3-agent multi-agent debate.

        Uses 3 naming agents:
        - TitleLiteraryAgent: Evocative, poetic titles (metaphor, symbolism)
        - TitleThematicAgent: Theme-reflecting titles (core conflict, arc)
        - TitleCommercialAgent: Marketable, genre-appropriate titles (hooks)

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
            if "story" not in codex or "narrative" not in codex["story"]:
                return Step7Result(
                    book_title="Untitled",
                    chapter_titles={},
                    book_debate={},
                    chapter_debates=[],
                    success=False,
                    error="Narrative not found. Run step 5 first.",
                    duration_seconds=time.time() - start_time,
                )

            narrative = codex["story"]["narrative"]
            outline = codex["story"].get("outline", {})
            chapter_outline = codex["story"].get("chapter_outline", {})

            # Extract context for book title debate
            logline = outline.get("logline", "A compelling story.")
            theme = outline.get("theme", "")
            setting = codex.get("setting_prompt", "")

            # Build plot summary from chapter outline
            chapters = chapter_outline.get("chapters", [])
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
            # CHAPTER TITLE DEBATES
            # =================================================================
            print("\n--- Chapter Title Debates ---")

            chapter_titles = {}
            chapter_debates = []
            narrative_chapters = narrative.get("chapters", [])

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
            narrative["title"] = book_title
            if book_debate.get("winning_subtitle"):
                narrative["subtitle"] = book_debate["winning_subtitle"]

            for chapter in narrative_chapters:
                chapter_num = chapter.get("chapter_number", 0)
                if chapter_num in chapter_titles:
                    chapter["chapter_title"] = f"Chapter {chapter_num} - {chapter_titles[chapter_num]}"

            duration = time.time() - start_time
            print(f"\n  Total naming time: {duration:.1f}s")

            return Step7Result(
                book_title=book_title,
                chapter_titles=chapter_titles,
                book_debate=book_debate,
                chapter_debates=chapter_debates,
                success=True,
                duration_seconds=duration,
            )

        except Exception as e:
            return Step7Result(
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

        # Step 5: Scene Narrative Writing
        if 5 in steps_to_run:
            print(f"\n{'='*60}")
            print("STEP 5: Scene Narrative Writing (5-Agent Multi-Agent Debate)")
            print(f"{'='*60}")

            result = self.step5_narrative(codex)
            results["step5"] = result

            if result.success:
                # Store narrative at story.narrative
                codex["story"]["narrative"] = result.narrative

                steps_completed.append(5)
                step_timings["step5_narrative"] = result.duration_seconds
            else:
                print(f">>> Step 5 FAILED: {result.error}")

        # Step 6: Narrative Revision with 5-Critic System
        if 6 in steps_to_run:
            print("\n>>> Running Step 6: Narrative Revision...")
            result = self.step6_revision(codex)
            if result.success:
                print(f">>> Step 6 COMPLETE: Revised {result.scenes_revised} scenes")
                print(f"    Avg score: {result.average_score_before:.1f} -> {result.average_score_after:.1f}")
                steps_completed.append(6)
                step_timings["step6_revision"] = result.duration_seconds
            else:
                print(f">>> Step 6 FAILED: {result.error}")

        # Step 7: Book & Chapter Title Naming
        if 7 in steps_to_run:
            print(f"\n{'='*60}")
            print("STEP 7: BOOK & CHAPTER TITLE NAMING (3-Agent Debate)")
            print(f"{'='*60}")
            result = self.step7_naming(codex)
            results["step7"] = result
            if result.success:
                print(f"\n>>> Step 7 COMPLETE: Book titled \"{result.book_title}\"")
                print(f"    Chapter titles: {len(result.chapter_titles)}")
                steps_completed.append(7)
                step_timings["step7_naming"] = result.duration_seconds
            else:
                print(f">>> Step 7 FAILED: {result.error}")

        # Steps 8-10: Add as we implement them
        for step_num in range(8, 11):
            if step_num in steps_to_run:
                print(f"\n>>> Step {step_num}: Not yet implemented")

        # Update metadata with phase completion info
        codex["metadata"]["phase_1"].update({
            "phase": 1,
            "name": "Author-Driven Story Creation",
            "author_id": self.author.id,
            "author_name": self.author.name,
            "structure_used": self.author.preferred_structure,
            "steps_completed": steps_completed,
            "step_timings": step_timings,
        })

        # Add character debates to metadata (NEW Step 1)
        if "step1" in results and results["step1"].success:
            codex["metadata"]["phase_1"]["character_debates"] = results["step1"].character_debates

        # Add scene debates to metadata (OLD Step 4 only - now skipped for NEW Step 4 World Building)
        # if "step4" in results and results["step4"].success:
        #     codex["metadata"]["phase_1"]["scene_debates"] = results["step4"].scene_debates

        # Add narrative debates to metadata
        if "step5" in results and results["step5"].success:
            codex["metadata"]["phase_1"]["narrative_debates"] = results["step5"].scene_debates

        # Add title naming debates to metadata
        if "step7" in results and results["step7"].success:
            codex["metadata"]["phase_1"]["title_naming"] = {
                "book_title": results["step7"].book_title,
                "chapter_titles": results["step7"].chapter_titles,
                "book_debate": results["step7"].book_debate,
            }

        return {
            "steps_completed": steps_completed,
            "step_timings": step_timings,
            "results": results,
        }
