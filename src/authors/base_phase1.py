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
from typing import Optional, TYPE_CHECKING

from src.config import DEFAULT_MODEL
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
from src.story_agents.location_debate_agents import (
    LocationArchitectAgent,
    LocationAtmosphereAgent,
    LocationNarrativeAgent,
    LocationAudienceAgent,
)
from src.story_agents.world_building_agents import (
    WorldSociologistAgent,
    WorldEconomistAgent,
    WorldPoliticianAgent,
    WorldCulturalistAgent,
)
from src.story_agents.scene_debate_agents import (
    ScenePlotAgent,
    SceneCharacterAgent,
    ScenePacingAgent,
    SceneStructureAgent,
)
from src.story_schemas import (
    SevenPointStructureSchema,
    StructureBeatSchema,
    AgentProposal,
    AgentCritique,
    DebateRound,
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
)

if TYPE_CHECKING:
    from src.authors.base_author import BaseAuthor


@dataclass
class Step1Result:
    """Result of Step 1: Plotting (7-Point Structure via Multi-Agent Debate)."""
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
    """Result of Step 2: Character Generation via Multi-Agent Debate."""
    characters: list
    character_debates: list
    name_mapping: dict
    success: bool
    error: Optional[str] = None
    duration_seconds: float = 0.0


@dataclass
class Step3Result:
    """Result of Step 3: World Building (Locations + World Context)."""
    locations: list
    world: dict
    location_debates: list
    success: bool
    error: Optional[str] = None
    duration_seconds: float = 0.0


@dataclass
class Step4Result:
    """Result of Step 4: Chapter/Scene Outline."""
    chapter_outline: dict
    scene_debates: list
    total_chapters: int
    total_scenes: int
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
    # STEP 1: PLOTTING (7-Point Structure via Research-Driven Multi-Agent Debate)
    # =========================================================================

    def step1_plotting(self, codex: dict) -> Step1Result:
        """Generate 7-point story structure via research-driven multi-agent debate.

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
            Step1Result with structure_beats, theme, title, and debate_summary
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
                return Step1Result(
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

            # Determine winner (simple majority)
            vote_counts = {}
            for v in votes:
                vote_counts[v.voted_for_agent] = vote_counts.get(v.voted_for_agent, 0) + 1
            winner = max(vote_counts, key=vote_counts.get)

            # Use winner's proposal
            winner_proposal = next(p for p in proposals if p.agent_name == winner)
            resolution = winner_proposal.beat
            print(f"\n    >>> WINNER: {winner} ({vote_counts[winner]}/5 votes)")
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

            vote_counts = {}
            for v in votes:
                vote_counts[v.voted_for_agent] = vote_counts.get(v.voted_for_agent, 0) + 1
            winner = max(vote_counts, key=vote_counts.get)

            # Get winning hook
            winner_proposal = next(p for p in proposals if p.agent_name == winner)
            hook = winner_proposal.beat
            print(f"\n    >>> WINNER: {winner} ({vote_counts[winner]}/5 votes)")
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

            vote_counts = {}
            for v in votes:
                vote_counts[v.voted_for_agent] = vote_counts.get(v.voted_for_agent, 0) + 1
            winner = max(vote_counts, key=vote_counts.get)

            winner_proposal = next(p for p in proposals if p.agent_name == winner)
            midpoint = winner_proposal.beat
            print(f"\n    >>> WINNER: {winner} ({vote_counts[winner]}/5 votes)")
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

            vote_counts = {}
            for v in votes:
                vote_counts[v.voted_for_agent] = vote_counts.get(v.voted_for_agent, 0) + 1
            winner = max(vote_counts, key=vote_counts.get)
            winner_proposal = next(p for p in pt1_proposals if p.agent_name == winner)
            plot_turn_1 = winner_proposal.beat
            print(f"    >>> PT1 WINNER: {winner} ({vote_counts[winner]}/5 votes)")

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

            vote_counts = {}
            for v in votes:
                vote_counts[v.voted_for_agent] = vote_counts.get(v.voted_for_agent, 0) + 1
            winner = max(vote_counts, key=vote_counts.get)
            winner_proposal = next(p for p in pt2_proposals if p.agent_name == winner)
            plot_turn_2 = winner_proposal.beat
            print(f"    >>> PT2 WINNER: {winner} ({vote_counts[winner]}/5 votes)")

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

            vote_counts = {}
            for v in votes:
                vote_counts[v.voted_for_agent] = vote_counts.get(v.voted_for_agent, 0) + 1
            winner = max(vote_counts, key=vote_counts.get)

            winner_proposal = next(p for p in pp2_proposals if p.agent_name == winner)
            pinch_point_2 = winner_proposal.beat
            print(f"\n    >>> PP2 WINNER: {winner} ({vote_counts[winner]}/5 votes)")

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

            return Step1Result(
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
            return Step1Result(
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
    # STEP 3: WORLD BUILDING (Locations + World Context)
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

    def step4_chapter_outline(self, codex: dict) -> Step4Result:
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
    # STEPS 5-9: Placeholder implementations (to be added incrementally)
    # =========================================================================

    def step5_narrative(self, codex: dict) -> dict:
        """Write complete narrative. Override in subclass for custom behavior."""
        raise NotImplementedError("Step 5 (Narrative) not yet implemented")

    def step6_revision(self, codex: dict) -> dict:
        """Revise narrative. Override in subclass for custom behavior."""
        raise NotImplementedError("Step 6 (Revision) not yet implemented")

    def step7_screenplay(self, codex: dict) -> dict:
        """Format as screenplay. Override in subclass for custom behavior."""
        raise NotImplementedError("Step 7 (Screenplay) not yet implemented")

    def step8_polish(self, codex: dict) -> dict:
        """Final polish. Override in subclass for custom behavior."""
        raise NotImplementedError("Step 8 (Polish) not yet implemented")

    def step9_finalize(self, codex: dict) -> dict:
        """Finalize and validate. Override in subclass for custom behavior."""
        raise NotImplementedError("Step 9 (Finalize) not yet implemented")

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
            steps: List of step numbers to run (1-9). Default: all steps.
            revision_passes: Number of revision passes for step 6.

        Returns:
            Dictionary with results from each executed step
        """
        steps_to_run = steps if steps is not None else list(range(1, 10))
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

        # Step 1: Plotting (7-Point Structure)
        if 1 in steps_to_run:
            print(f"\n{'='*60}")
            print("STEP 1: Plotting (7-Point Structure via Multi-Agent Debate)")
            print(f"{'='*60}")

            result = self.step1_plotting(codex)
            results["step1"] = result

            if result.success:
                # Store parsed story seed
                codex["story"]["outline"]["story_seed_parsed"] = result.story_seed_parsed

                # Store 7-point structure beats
                codex["story"]["outline"]["structure_beats"] = result.structure_beats

                # Store theme and title
                codex["story"]["outline"]["theme"] = result.theme
                codex["story"]["outline"]["title"] = result.title_suggestion

                steps_completed.append(1)
                step_timings["step1_plotting"] = result.duration_seconds
            else:
                print(f">>> Step 1 FAILED: {result.error}")

        # Step 2: Character Generation
        if 2 in steps_to_run:
            print(f"\n{'='*60}")
            print("STEP 2: Character Generation (Multi-Agent Debate)")
            print(f"{'='*60}")

            result = self.step2_characters(codex)
            results["step2"] = result

            if result.success:
                # Store characters at story.characters
                codex["story"]["characters"] = result.characters

                # Store name mapping for later use
                if "outline" in codex["story"]:
                    codex["story"]["outline"]["name_mapping"] = result.name_mapping

                steps_completed.append(2)
                step_timings["step2_characters"] = result.duration_seconds
            else:
                print(f">>> Step 2 FAILED: {result.error}")

        # Step 3: World Building (Locations + World Context)
        if 3 in steps_to_run:
            print(f"\n{'='*60}")
            print("STEP 3: World Building (Locations + World Context)")
            print(f"{'='*60}")

            result = self.step3_world_building(codex)
            results["step3"] = result

            if result.success:
                # Store locations at story.locations
                codex["story"]["locations"] = result.locations

                # Store world context at story.world
                codex["story"]["world"] = result.world

                steps_completed.append(3)
                step_timings["step3_world_building"] = result.duration_seconds
            else:
                print(f">>> Step 3 FAILED: {result.error}")

        # Step 4: Chapter/Scene Outline
        if 4 in steps_to_run:
            print(f"\n{'='*60}")
            print("STEP 4: Chapter/Scene Outline (Multi-Agent Debate)")
            print(f"{'='*60}")

            result = self.step4_chapter_outline(codex)
            results["step4"] = result

            if result.success:
                # Store chapter outline at story.chapter_outline
                codex["story"]["chapter_outline"] = result.chapter_outline

                steps_completed.append(4)
                step_timings["step4_chapter_outline"] = result.duration_seconds
            else:
                print(f">>> Step 4 FAILED: {result.error}")

        # Steps 5-9: Add as we implement them
        for step_num in range(5, 10):
            if step_num in steps_to_run:
                print(f"\n>>> Step {step_num}: Not yet implemented")

        # Update metadata
        if "metadata" not in codex:
            codex["metadata"] = {}
        codex["metadata"]["phase_1"] = {
            "phase": 1,
            "name": "Author-Driven Story Creation",
            "author_id": self.author.id,
            "author_name": self.author.name,
            "structure_used": self.author.preferred_structure,
            "steps_completed": steps_completed,
            "step_timings": step_timings,
        }

        # Add debate summary to metadata
        if "step1" in results and results["step1"].success:
            codex["metadata"]["phase_1"]["debate_summary"] = results["step1"].debate_summary

        # Add character debates to metadata
        if "step2" in results and results["step2"].success:
            codex["metadata"]["phase_1"]["character_debates"] = results["step2"].character_debates

        # Add location debates to metadata
        if "step3" in results and results["step3"].success:
            codex["metadata"]["phase_1"]["location_debates"] = results["step3"].location_debates

        # Add scene debates to metadata
        if "step4" in results and results["step4"].success:
            codex["metadata"]["phase_1"]["scene_debates"] = results["step4"].scene_debates

        return {
            "steps_completed": steps_completed,
            "step_timings": step_timings,
            "results": results,
        }
