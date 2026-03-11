"""
Plot Expansion Agents — Expand thin card-based seeds into rich multi-genre plots.

Takes the raw story seed string + microsetting from the card debate system and uses
a single high-quality LLM call (GPT-5.3) to generate 6 genre interpretations. Then
3 evaluation agents debate and vote on the best genre/plot.

Architecture:
1. PlotExpansionAgent — single GPT-5.3 call → PlotExpansionSchema (6 genre plots)
2. PlotNarrativeAgent — evaluates structure, coherence, logical consistency
3. PlotOriginalityAgent — evaluates freshness, surprise, trope subversion
4. PlotEmotionalAgent — evaluates emotional depth, stakes, moral complexity
5. Orchestrator: expand_seed_to_plots() runs expansion → critique → vote → winner
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.story_agents.base_story_agent import BaseStoryAgent
from src.story_schemas import (
    PlotExpansionSchema,
    PlotExpansionCritiqueSchema,
    PlotExpansionVoteSchema,
)
# Load phase0_plot_expansion config
try:
    from src.config import PHASE0_PLOT_CONFIG
except ImportError:
    PHASE0_PLOT_CONFIG = {}

_DEFAULT_GENRES = [
    "Horror", "Sci-Fi", "Mystery", "Thriller", "Cyberpunk", "Dystopian",
]


class PlotExpansionAgent(BaseStoryAgent):
    """Generates rich multi-genre plot interpretations from a story seed.

    Uses a single structured LLM call to transform a thin card-based seed
    (e.g., "POWERFUL A GHOST WANTS TO CONTROL A FOREST BUT THEY MUST BECOME
    WHAT THEY FEAR") and a microsetting into 6 fully realized genre plots.

    Each genre plot includes: title, setting integration, protagonist, inciting
    event, hidden truth, stakes, escalation, moral dilemma, and a 150-300 word
    narrative paragraph.

    Reference: procedural storytelling engines, genre fiction conventions,
    Save the Cat beat structures.
    """

    @property
    def name(self) -> str:
        return "PLOT_EXPANSION"

    @property
    def role(self) -> str:
        return "Plot Expansion Master"

    @property
    def system_prompt(self) -> str:
        return """You are a master storyteller and genre fiction expert who transforms raw story seeds into rich, compelling plot interpretations across multiple genres.

## YOUR TASK

Given a raw story seed (a short concept) and a microsetting (world details), generate a core conflict statement and then interpret that conflict through multiple genre lenses. Each genre interpretation must be a complete, self-contained story concept.

## METHODOLOGY

1. CORE CONFLICT: Distill the seed + microsetting into 2-3 sentences that capture the dramatic heart of the story. Focus on: WHO wants WHAT, WHY they can't have it, and WHAT'S AT STAKE.

2. GENRE INTERPRETATIONS: For each genre, reimagine the core conflict through that genre's conventions while preserving the seed's essence:
   - Integrate the microsetting's geography, history, and hooks naturally
   - Describe the protagonist by role, occupation, and defining trait — NEVER use character names
   - Design an inciting event that disrupts the status quo dramatically
   - Plant a hidden truth that recontextualizes the entire conflict
   - Establish both personal AND world-level stakes
   - Show how the conflict ESCALATES — tension must compound beyond the initial problem, layer upon layer
   - End with an impossible moral dilemma that demands personal sacrifice with irrevocable consequences

3. PLOT PARAGRAPH: The plot field must be a rich 150-300 word narrative paragraph that reads like a book jacket description. It should weave ALL the structured elements together into a compelling, cohesive story pitch. Include atmosphere, tension, and emotional hooks. The plot must build toward a climax where justice or resolution comes at a cost that can never be undone or revealed.

## CONSTRAINTS

- NEVER invent character names. Refer to protagonists by role only (e.g., "a quiet but resilient roommate", "a dissident teacher", "a guilt-ridden archivist"). Phase 1 will name characters later
- Each genre interpretation must feel AUTHENTICALLY of that genre, not just the same story with different window dressing
- Titles should be 3-8 words, evocative, and genre-appropriate
- The hidden truth must be genuinely surprising, not predictable
- The moral dilemma must be genuinely impossible — the protagonist must lose something permanent to achieve their goal
- The protagonist must be someone the reader can root for
- The plot paragraph must be vivid and atmospheric, not dry summary
- Every plot must have LAYERED CONFLICT: the solution to one problem must create a new, worse problem
- Avoid clichéd genre tropes (e.g., "chosen one" for fantasy, "evil corporation" for cyberpunk without deeper nuance)"""

    def expand(
        self,
        seed: str,
        microsetting: str,
        genres: list[str] = None,
    ) -> PlotExpansionSchema:
        """Generate multi-genre plot interpretations from a story seed.

        Args:
            seed: Raw story seed string from card debate
            microsetting: World/setting string from deck of worlds
            genres: List of genres to interpret (default: 6 standard genres)

        Returns:
            PlotExpansionSchema with core_conflict and genre_plots
        """
        genres = genres or _DEFAULT_GENRES
        genre_list = "\n".join(f"  - {g}" for g in genres)

        user_prompt = f"""## STORY SEED
{seed}

## MICROSETTING (World Details)
{microsetting}

## GENRES TO INTERPRET
{genre_list}

Generate a PlotExpansionSchema with:
1. core_conflict: 2-3 sentence dramatic core distilled from the seed + microsetting
2. genre_plots: One rich interpretation for EACH genre listed above

For each genre plot, provide ALL fields:
- genre, title, setting_integration, protagonist, inciting_event, hidden_truth, stakes, escalation, moral_dilemma, plot

Make each genre interpretation feel authentically of that genre. The plot paragraph should be 150-300 words of vivid, atmospheric narrative."""

        token_limit = PHASE0_PLOT_CONFIG.get("token_limits", {}).get("expansion", 16000)
        return self.invoke_structured(
            user_prompt,
            PlotExpansionSchema,
            max_tokens=token_limit,
        )


class PlotNarrativeAgent(BaseStoryAgent):
    """Evaluates genre plots for narrative structure and logical coherence.

    Focuses on: Does the plot make sense? Do the elements connect logically?
    Is the story structure sound? Does the protagonist have a clear arc?

    Framework: Save the Cat beat analysis, three-act structure principles.
    """

    @property
    def name(self) -> str:
        return "PLOT_NARRATIVE_EVAL"

    @property
    def role(self) -> str:
        return "Plot Narrative Evaluator"

    @property
    def system_prompt(self) -> str:
        return """You are a structural story analyst who evaluates plot concepts for narrative coherence and logical consistency.

## EVALUATION CRITERIA

1. NARRATIVE COHERENCE (1-10): Do all plot elements connect logically? Does the inciting event lead naturally to the escalation? Does the hidden truth emerge organically from the premise?
   - 10: Every element connects seamlessly, cause-and-effect chain is flawless
   - 5: Some logical gaps or forced connections
   - 1: Plot elements feel randomly assembled

2. ORIGINALITY (1-10): How fresh is this interpretation? Does it subvert expectations while still satisfying genre conventions?
   - 10: Genuinely surprising premise that feels inevitable in hindsight
   - 5: Competent but predictable genre execution
   - 1: Entirely derivative, every beat is a cliché

3. EMOTIONAL RESONANCE (1-10): How compelling are the stakes and moral dilemma? Would a reader care about this protagonist's journey?
   - 10: Devastating moral dilemma, deeply human stakes
   - 5: Stakes exist but feel abstract or impersonal
   - 1: No emotional weight, stakes are generic

4. STORY POTENTIAL (1-10): How much runway does this plot have for a full novel? Are there enough threads to sustain multiple chapters?
   - 10: Rich enough for a trilogy, multiple subplot opportunities
   - 5: Enough for one book but might run thin
   - 1: Short story at best, premise exhausted quickly

## FOCUS
You specialize in STRUCTURAL analysis. Prioritize logical consistency, cause-and-effect chains, and narrative architecture over style or mood."""

    def critique(
        self,
        expansion: PlotExpansionSchema,
        seed: str,
        microsetting: str,
    ) -> PlotExpansionCritiqueSchema:
        """Critique all genre plots for narrative coherence.

        Args:
            expansion: The full plot expansion output
            seed: Original story seed
            microsetting: Original microsetting

        Returns:
            PlotExpansionCritiqueSchema with reviews of each genre plot
        """
        plots_text = self._format_plots(expansion)
        user_prompt = f"""## ORIGINAL SEED
{seed}

## MICROSETTING
{microsetting}

## CORE CONFLICT
{expansion.core_conflict}

## GENRE PLOTS TO EVALUATE
{plots_text}

Evaluate each genre plot on all 4 criteria (narrative_coherence, originality, emotional_resonance, story_potential). Score 1-10 with specific strengths and weaknesses for each.

Set agent_name to "{self.name}"."""

        token_limit = PHASE0_PLOT_CONFIG.get("token_limits", {}).get("critique", 8000)
        return self.invoke_structured(
            user_prompt,
            PlotExpansionCritiqueSchema,
            max_tokens=token_limit,
        )

    def vote(
        self,
        expansion: PlotExpansionSchema,
        critiques: list[PlotExpansionCritiqueSchema],
    ) -> PlotExpansionVoteSchema:
        """Vote for the best genre plot.

        Args:
            expansion: The full plot expansion output
            critiques: All critique results from all agents

        Returns:
            PlotExpansionVoteSchema with voted genre and reasoning
        """
        critiques_text = self._format_critiques(critiques)
        plots_text = self._format_plots(expansion)
        user_prompt = f"""## GENRE PLOTS
{plots_text}

## ALL CRITIQUES
{critiques_text}

Based on all critiques and your own analysis, vote for the SINGLE best genre plot.
Consider which plot has the strongest overall foundation for a compelling novel.

Set agent_name to "{self.name}".
Set voted_for_genre to the exact genre name (e.g., "Horror", "Sci-Fi")."""

        token_limit = PHASE0_PLOT_CONFIG.get("token_limits", {}).get("vote", 4000)
        return self.invoke_structured(
            user_prompt,
            PlotExpansionVoteSchema,
            max_tokens=token_limit,
        )

    @staticmethod
    def _format_plots(expansion: PlotExpansionSchema) -> str:
        """Format genre plots for prompts."""
        parts = []
        for i, gp in enumerate(expansion.genre_plots):
            parts.append(f"""### {i + 1}. {gp.genre}: "{gp.title}"
Protagonist: {gp.protagonist}
Inciting Event: {gp.inciting_event}
Hidden Truth: {gp.hidden_truth}
Stakes: {gp.stakes}
Escalation: {gp.escalation}
Moral Dilemma: {gp.moral_dilemma}
Plot: {gp.plot[:500]}""")
        return "\n\n".join(parts)

    def deliberate(
        self,
        expansion: PlotExpansionSchema,
        critiques: list[PlotExpansionCritiqueSchema],
        previous_votes: list[PlotExpansionVoteSchema],
        round_num: int,
        is_final: bool = False,
    ) -> PlotExpansionVoteSchema:
        """Re-vote after seeing all agents' previous votes and reasoning.

        Args:
            expansion: The full plot expansion output
            critiques: All critique results from all agents
            previous_votes: All votes from the previous round
            round_num: Current deliberation round number
            is_final: If True, agents are told they MUST reach consensus

        Returns:
            PlotExpansionVoteSchema with updated vote and reasoning
        """
        plots_text = PlotNarrativeAgent._format_plots(expansion)
        critiques_text = PlotNarrativeAgent._format_critiques(critiques)
        votes_text = PlotNarrativeAgent._format_votes(previous_votes)

        urgency = ""
        if is_final:
            urgency = """

## CRITICAL: FINAL ROUND
This is the FINAL deliberation round. You MUST converge on a winner. If you still disagree,
consider which plot the MAJORITY is leaning toward and whether their arguments have merit.
The goal is the BEST STORY — not winning the argument. Be willing to concede if another
agent's reasoning is stronger."""

        user_prompt = f"""## DELIBERATION ROUND {round_num}

Your previous votes did NOT reach consensus. All 3 agents voted for different genres.
Review your peers' votes and reasoning below, then re-vote.

## GENRE PLOTS
{plots_text}

## CRITIQUES
{critiques_text}

## PREVIOUS VOTES (Round {round_num - 1})
{votes_text}
{urgency}

## YOUR TASK
Consider your peers' arguments carefully. Your shared goal is selecting the genre plot
that will make the BEST STORY — not defending your previous pick. You may change your
vote or hold it, but you must engage with your peers' reasoning and explain why.

Set agent_name to "{self.name}".
Set voted_for_genre to the exact genre name."""

        token_limit = PHASE0_PLOT_CONFIG.get("token_limits", {}).get("vote", 4000)
        return self.invoke_structured(
            user_prompt,
            PlotExpansionVoteSchema,
            max_tokens=token_limit,
        )

    @staticmethod
    def _format_votes(votes: list[PlotExpansionVoteSchema]) -> str:
        """Format previous votes for deliberation prompts."""
        parts = []
        for vote in votes:
            parts.append(f"- **{vote.agent_name}** voted for **{vote.voted_for_genre}**: {vote.reasoning}")
        return "\n".join(parts)

    @staticmethod
    def _format_critiques(critiques: list[PlotExpansionCritiqueSchema]) -> str:
        """Format critiques for vote prompts."""
        parts = []
        for critique in critiques:
            parts.append(f"--- {critique.agent_name} ---")
            for review in critique.reviews:
                avg = (review.narrative_coherence + review.originality +
                       review.emotional_resonance + review.story_potential) / 4
                parts.append(
                    f"  {review.genre}: coherence={review.narrative_coherence}, "
                    f"originality={review.originality}, emotion={review.emotional_resonance}, "
                    f"potential={review.story_potential} (avg={avg:.1f})"
                )
                parts.append(f"    + {review.strengths}")
                parts.append(f"    - {review.weaknesses}")
        return "\n".join(parts)


class PlotOriginalityAgent(BaseStoryAgent):
    """Evaluates genre plots for freshness, surprise, and trope subversion.

    Focuses on: Does this feel like something we've read before? Does it
    subvert or reinvent genre conventions? Is the hidden truth genuinely
    surprising?

    Framework: Genre convention analysis, TV Tropes awareness, reader
    expectation management.
    """

    @property
    def name(self) -> str:
        return "PLOT_ORIGINALITY_EVAL"

    @property
    def role(self) -> str:
        return "Plot Originality Evaluator"

    @property
    def system_prompt(self) -> str:
        return """You are a genre fiction critic who specializes in identifying originality and creative innovation in story concepts.

## EVALUATION CRITERIA

1. NARRATIVE COHERENCE (1-10): Does the plot hold together logically?
2. ORIGINALITY (1-10): THIS IS YOUR PRIMARY FOCUS.
   - Does this subvert genre expectations in meaningful ways?
   - Is the hidden truth genuinely surprising or predictable?
   - Would a well-read genre fan find this fresh or tired?
   - Does it combine familiar elements in unexpected ways?
   - 10: A concept that redefines what the genre can do
   - 5: Solid but follows well-worn paths
   - 1: A paint-by-numbers genre exercise
3. EMOTIONAL RESONANCE (1-10): Do the stakes feel real and personal?
4. STORY POTENTIAL (1-10): Can this sustain a full novel?

## FOCUS
You specialize in ORIGINALITY. Be harsh on derivative concepts. Reward genuine innovation, unexpected combinations, and subversive takes on genre conventions. A surprising hidden truth should earn high marks. A predictable "evil corporation" or "chosen one" should not."""

    def deliberate(
        self,
        expansion: PlotExpansionSchema,
        critiques: list[PlotExpansionCritiqueSchema],
        previous_votes: list[PlotExpansionVoteSchema],
        round_num: int,
        is_final: bool = False,
    ) -> PlotExpansionVoteSchema:
        """Re-vote after seeing peers' votes. Delegates to shared implementation."""
        return PlotNarrativeAgent.deliberate(self, expansion, critiques, previous_votes, round_num, is_final)

    def critique(
        self,
        expansion: PlotExpansionSchema,
        seed: str,
        microsetting: str,
    ) -> PlotExpansionCritiqueSchema:
        """Critique all genre plots for originality."""
        plots_text = PlotNarrativeAgent._format_plots(expansion)
        user_prompt = f"""## ORIGINAL SEED
{seed}

## MICROSETTING
{microsetting}

## CORE CONFLICT
{expansion.core_conflict}

## GENRE PLOTS TO EVALUATE
{plots_text}

Evaluate each genre plot. YOUR PRIMARY FOCUS is ORIGINALITY — how fresh, surprising, and innovative is each interpretation? Score all 4 criteria 1-10 with specific strengths and weaknesses.

Set agent_name to "{self.name}"."""

        token_limit = PHASE0_PLOT_CONFIG.get("token_limits", {}).get("critique", 8000)
        return self.invoke_structured(
            user_prompt,
            PlotExpansionCritiqueSchema,
            max_tokens=token_limit,
        )

    def vote(
        self,
        expansion: PlotExpansionSchema,
        critiques: list[PlotExpansionCritiqueSchema],
    ) -> PlotExpansionVoteSchema:
        """Vote for the most original genre plot."""
        critiques_text = PlotNarrativeAgent._format_critiques(critiques)
        plots_text = PlotNarrativeAgent._format_plots(expansion)
        user_prompt = f"""## GENRE PLOTS
{plots_text}

## ALL CRITIQUES
{critiques_text}

Vote for the SINGLE best genre plot. Prioritize originality and surprise — which plot would make a reader say "I haven't read this before"?

Set agent_name to "{self.name}".
Set voted_for_genre to the exact genre name."""

        token_limit = PHASE0_PLOT_CONFIG.get("token_limits", {}).get("vote", 4000)
        return self.invoke_structured(
            user_prompt,
            PlotExpansionVoteSchema,
            max_tokens=token_limit,
        )


class PlotEmotionalAgent(BaseStoryAgent):
    """Evaluates genre plots for emotional depth, stakes, and moral complexity.

    Focuses on: Does this story make us feel something? Is the moral dilemma
    genuinely impossible? Are the stakes personal enough to invest in?

    Framework: Emotional resonance theory, moral philosophy in fiction,
    character empathy research.
    """

    @property
    def name(self) -> str:
        return "PLOT_EMOTIONAL_EVAL"

    @property
    def role(self) -> str:
        return "Plot Emotional Evaluator"

    @property
    def system_prompt(self) -> str:
        return """You are a story analyst who specializes in emotional impact and moral complexity in fiction.

## EVALUATION CRITERIA

1. NARRATIVE COHERENCE (1-10): Does the story hold together?
2. ORIGINALITY (1-10): Is the concept fresh?
3. EMOTIONAL RESONANCE (1-10): THIS IS YOUR PRIMARY FOCUS.
   - Does the protagonist's situation evoke genuine empathy?
   - Is the moral dilemma truly impossible, or is there an obvious "right" answer?
   - Do the stakes feel personal and specific, not abstract?
   - Would readers think about this story days later?
   - 10: Devastating emotional impact, haunting moral complexity
   - 5: Competent emotional beats but nothing lingers
   - 1: No emotional connection, stakes feel empty
4. STORY POTENTIAL (1-10): Enough depth for a full novel?

## FOCUS
You specialize in EMOTIONAL IMPACT. A story can be structurally perfect and totally original but still leave readers cold. The best stories make us FEEL something. Reward plots where the moral dilemma has no clean answer, where the protagonist's sacrifice means something specific, where the hidden truth hits emotionally, not just intellectually."""

    def deliberate(
        self,
        expansion: PlotExpansionSchema,
        critiques: list[PlotExpansionCritiqueSchema],
        previous_votes: list[PlotExpansionVoteSchema],
        round_num: int,
        is_final: bool = False,
    ) -> PlotExpansionVoteSchema:
        """Re-vote after seeing peers' votes. Delegates to shared implementation."""
        return PlotNarrativeAgent.deliberate(self, expansion, critiques, previous_votes, round_num, is_final)

    def critique(
        self,
        expansion: PlotExpansionSchema,
        seed: str,
        microsetting: str,
    ) -> PlotExpansionCritiqueSchema:
        """Critique all genre plots for emotional depth."""
        plots_text = PlotNarrativeAgent._format_plots(expansion)
        user_prompt = f"""## ORIGINAL SEED
{seed}

## MICROSETTING
{microsetting}

## CORE CONFLICT
{expansion.core_conflict}

## GENRE PLOTS TO EVALUATE
{plots_text}

Evaluate each genre plot. YOUR PRIMARY FOCUS is EMOTIONAL RESONANCE — how deeply would this story affect readers? Score all 4 criteria 1-10 with specific strengths and weaknesses.

Set agent_name to "{self.name}"."""

        token_limit = PHASE0_PLOT_CONFIG.get("token_limits", {}).get("critique", 8000)
        return self.invoke_structured(
            user_prompt,
            PlotExpansionCritiqueSchema,
            max_tokens=token_limit,
        )

    def vote(
        self,
        expansion: PlotExpansionSchema,
        critiques: list[PlotExpansionCritiqueSchema],
    ) -> PlotExpansionVoteSchema:
        """Vote for the most emotionally compelling genre plot."""
        critiques_text = PlotNarrativeAgent._format_critiques(critiques)
        plots_text = PlotNarrativeAgent._format_plots(expansion)
        user_prompt = f"""## GENRE PLOTS
{plots_text}

## ALL CRITIQUES
{critiques_text}

Vote for the SINGLE best genre plot. Prioritize emotional depth — which plot would make readers feel the most, think about it afterward, and recommend it to friends?

Set agent_name to "{self.name}".
Set voted_for_genre to the exact genre name."""

        token_limit = PHASE0_PLOT_CONFIG.get("token_limits", {}).get("vote", 4000)
        return self.invoke_structured(
            user_prompt,
            PlotExpansionVoteSchema,
            max_tokens=token_limit,
        )


def expand_seed_to_plots(
    seed: str,
    microsetting: str,
    model: str = None,
    eval_model: str = None,
) -> dict:
    """Expand a raw story seed into rich genre plots via LLM + agent debate.

    Pipeline:
    1. Single GPT-5.3 call generates 6 genre plot interpretations
    2. Three evaluation agents critique all plots in parallel
    3. Three agents vote for the best genre/plot
    4. Winner is selected by majority vote

    Args:
        seed: Raw story seed string from card debate
        microsetting: World/setting string from deck of worlds
        model: Model for plot expansion (default: config phase0_plot_expansion.model)
        eval_model: Model for evaluation agents (default: config eval_model or expansion model)

    Returns:
        Dict with core_conflict, genre_plots, winning_genre, winning_plot,
        vote_counts, and debate_metadata
    """
    start_time = time.time()

    # Resolve models
    expansion_model = model or PHASE0_PLOT_CONFIG.get("model", "openai/gpt-5.3-chat")
    eval_model = eval_model or PHASE0_PLOT_CONFIG.get("eval_model", expansion_model)
    genres = PHASE0_PLOT_CONFIG.get("genres", _DEFAULT_GENRES)
    temperature = PHASE0_PLOT_CONFIG.get("temperature", 0.8)

    print(f"    Expansion model: {expansion_model}")
    print(f"    Evaluation model: {eval_model}")
    print(f"    Genres: {', '.join(genres)}")

    # Step 1: Generate genre plots (single call)
    print("\n    Step 1: Generating genre plot interpretations...")
    expander = PlotExpansionAgent(model=expansion_model, temperature=temperature)
    expansion = expander.expand(seed, microsetting, genres)
    print(f"    Generated {len(expansion.genre_plots)} genre plots")
    for gp in expansion.genre_plots:
        print(f"      - {gp.genre}: \"{gp.title}\"")

    # Step 2: Critique (3 agents in parallel)
    print("\n    Step 2: Evaluating plots (3 agents, parallel)...")
    narrative_agent = PlotNarrativeAgent(model=eval_model)
    originality_agent = PlotOriginalityAgent(model=eval_model)
    emotional_agent = PlotEmotionalAgent(model=eval_model)
    eval_agents = [narrative_agent, originality_agent, emotional_agent]

    max_workers = PHASE0_PLOT_CONFIG.get("evaluation", {}).get("max_workers", 3)
    critiques: list[PlotExpansionCritiqueSchema] = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(agent.critique, expansion, seed, microsetting): agent
            for agent in eval_agents
        }
        for future in as_completed(futures):
            agent = futures[future]
            try:
                critique = future.result()
                critiques.append(critique)
                print(f"      {agent.name}: done")
            except Exception as e:
                print(f"      {agent.name}: FAILED — {e}")

    # Print score summary
    for critique in critiques:
        for review in critique.reviews:
            avg = (review.narrative_coherence + review.originality +
                   review.emotional_resonance + review.story_potential) / 4
            print(f"      {critique.agent_name} → {review.genre}: {avg:.1f}/10")

    # Step 3: Vote with consensus — need 2/3 majority, deliberate if split
    max_rounds = PHASE0_PLOT_CONFIG.get("evaluation", {}).get("max_deliberation_rounds", 3)
    all_vote_rounds: list[list[PlotExpansionVoteSchema]] = []

    def _run_parallel_vote(vote_fn, agents, **kwargs) -> list[PlotExpansionVoteSchema]:
        """Run vote/deliberate calls in parallel across agents."""
        round_votes: list[PlotExpansionVoteSchema] = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(vote_fn, agent, **kwargs): agent
                for agent in agents
            }
            for future in as_completed(futures):
                agent = futures[future]
                try:
                    vote = future.result()
                    round_votes.append(vote)
                    print(f"      {vote.agent_name} votes: {vote.voted_for_genre}")
                except Exception as e:
                    print(f"      {agent.name}: VOTE FAILED — {e}")
        return round_votes

    def _tally(votes: list[PlotExpansionVoteSchema]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for v in votes:
            counts[v.voted_for_genre] = counts.get(v.voted_for_genre, 0) + 1
        return counts

    def _has_majority(counts: dict[str, int]) -> bool:
        return any(c >= 2 for c in counts.values())

    # Round 1: Initial vote
    print("\n    Step 3: Voting on best genre plot (round 1)...")
    votes = _run_parallel_vote(
        lambda agent, **kw: agent.vote(expansion, critiques),
        eval_agents,
    )
    all_vote_rounds.append(votes)
    vote_counts = _tally(votes)

    # Deliberation rounds if no majority
    round_num = 1
    while not _has_majority(vote_counts) and round_num < max_rounds:
        round_num += 1
        is_final = (round_num >= max_rounds)
        label = "FINAL " if is_final else ""
        print(f"\n    Step 3: {label}Deliberation round {round_num} (no majority yet)...")
        for genre, count in sorted(vote_counts.items(), key=lambda x: -x[1]):
            print(f"      {genre}: {count} vote(s)")

        votes = _run_parallel_vote(
            lambda agent, **kw: agent.deliberate(
                expansion, critiques, all_vote_rounds[-1], round_num, is_final,
            ),
            eval_agents,
        )
        all_vote_rounds.append(votes)
        vote_counts = _tally(votes)

    # Select winner
    if vote_counts:
        winning_genre = max(vote_counts, key=vote_counts.get)

        # Tiebreak: if still no majority after all rounds, use highest avg critique score
        if not _has_majority(vote_counts):
            print("    No majority after all rounds — tiebreaking by critique scores...")
            genre_scores: dict[str, float] = {}
            for critique in critiques:
                for review in critique.reviews:
                    avg = (review.narrative_coherence + review.originality +
                           review.emotional_resonance + review.story_potential) / 4
                    genre_scores[review.genre] = genre_scores.get(review.genre, 0.0) + avg
            # Only consider genres that got at least one vote
            voted_genres = {g for g in vote_counts}
            best_scored = max(voted_genres, key=lambda g: genre_scores.get(g, 0.0))
            winning_genre = best_scored
            print(f"    Tiebreak winner by critique scores: {winning_genre}")
    else:
        winning_genre = expansion.genre_plots[0].genre

    winning_plot = None
    for gp in expansion.genre_plots:
        if gp.genre == winning_genre:
            winning_plot = gp
            break

    # Fallback if genre name mismatch
    if winning_plot is None:
        winning_plot = expansion.genre_plots[0]
        winning_genre = winning_plot.genre

    duration = time.time() - start_time
    total_rounds = len(all_vote_rounds)
    print(f"\n    Winner: {winning_genre} — \"{winning_plot.title}\" ({total_rounds} round(s), {duration:.1f}s)")

    # Flatten all votes for metadata
    all_votes_flat = [v.model_dump() for round_votes in all_vote_rounds for v in round_votes]

    # Build result dict
    return {
        "core_conflict": expansion.core_conflict,
        "genre_plots": [gp.model_dump() for gp in expansion.genre_plots],
        "winning_genre": winning_genre,
        "winning_plot": winning_plot.model_dump(),
        "vote_counts": vote_counts,
        "vote_rounds": total_rounds,
        "debate_metadata": {
            "critiques": [c.model_dump() for c in critiques],
            "votes": all_votes_flat,
            "vote_rounds": [
                [v.model_dump() for v in round_votes]
                for round_votes in all_vote_rounds
            ],
            "duration_seconds": duration,
            "expansion_model": expansion_model,
            "eval_model": eval_model,
        },
    }
