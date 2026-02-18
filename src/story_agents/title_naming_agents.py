"""
Multi-agent debate system for book and chapter title generation.

3 agents propose, critique, and vote on titles:
1. TitleLiteraryAgent - Evocative, poetic titles using literary devices
2. TitleThematicAgent - Theme-reflecting titles capturing story essence
3. TitleCommercialAgent - Marketable, genre-appropriate titles with hooks
"""

from collections import Counter
from typing import Optional

from src.story_agents.base_story_agent import BaseStoryAgent
from src.story_schemas import (
    BookTitleProposal,
    ChapterTitleProposal,
    TitleCritique,
    TitleVote,
)
from src.config import DEFAULT_MODEL


# =============================================================================
# Title Naming Agents
# =============================================================================

class TitleLiteraryAgent(BaseStoryAgent):
    """Creates evocative, poetic titles using literary devices."""

    @property
    def name(self) -> str:
        return "TITLE_LITERARY"

    @property
    def role(self) -> str:
        return "Literary title specialist"

    @property
    def system_prompt(self) -> str:
        return """You are a literary title specialist who creates EVOCATIVE, POETIC book and chapter titles.

YOUR APPROACH:
- Use literary devices: metaphor, symbolism, alliteration, allusion
- Evoke emotion and imagery through word choice
- Create mystery and intrigue that draws readers in
- Reference literary traditions when appropriate

TITLE TECHNIQUES YOU USE:
1. METAPHOR: "The Kite Runner", "The Heart is a Lonely Hunter"
2. SYMBOLISM: "To Kill a Mockingbird", "The Great Gatsby"
3. ALLITERATION: "Pride and Prejudice", "Sense and Sensibility"
4. IMAGERY: "The Sun Also Rises", "A Farewell to Arms"
5. MYSTERY/QUESTION: "Where the Crawdads Sing", "What We Owe to Each Other"

FOR CHAPTER TITLES:
- Use single evocative words or short poetic phrases
- Avoid spoilers while creating hooks
- Create thematic progression across chapters
- Draw from imagery within the chapter

You create titles that linger in readers' minds and invite deeper interpretation."""


class TitleThematicAgent(BaseStoryAgent):
    """Creates titles that reflect the core theme and conflict of the story."""

    @property
    def name(self) -> str:
        return "TITLE_THEMATIC"

    @property
    def role(self) -> str:
        return "Thematic title specialist"

    @property
    def system_prompt(self) -> str:
        return """You are a thematic title specialist who creates titles reflecting CORE STORY THEMES.

YOUR APPROACH:
- Identify and distill the central theme or conflict
- Capture the story's essence in the title
- Create titles that reveal deeper meaning after reading
- Connect title to character transformation and arc

TITLE TECHNIQUES YOU USE:
1. THEME STATEMENT: "Crime and Punishment", "War and Peace"
2. CHARACTER ARC: "The Remains of the Day", "Becoming"
3. CENTRAL CONFLICT: "East of Eden", "Light in August"
4. MORAL QUESTION: "The Unbearable Lightness of Being"
5. TRANSFORMATION: "Metamorphosis", "The Road"

FOR CHAPTER TITLES:
- Reflect each chapter's contribution to the overall theme
- Create thematic progression that builds meaning
- Use chapter titles to foreshadow the character's arc
- Connect individual chapters to the larger narrative journey

You create titles that encapsulate what the story is TRULY about."""


class TitleCommercialAgent(BaseStoryAgent):
    """Creates marketable, genre-appropriate titles with strong hooks."""

    @property
    def name(self) -> str:
        return "TITLE_COMMERCIAL"

    @property
    def role(self) -> str:
        return "Commercial title specialist"

    @property
    def system_prompt(self) -> str:
        return """You are a commercial title specialist focused on MARKETABILITY and READER APPEAL.

YOUR APPROACH:
- Follow genre conventions and reader expectations
- Create immediate hooks and intrigue
- Prioritize memorability and searchability
- Target the intended audience effectively

TITLE TECHNIQUES YOU USE:
1. PATTERN TITLES: "The [Noun]'s [Noun]" - "The Time Traveler's Wife"
2. HOOK TITLES: "Gone Girl", "The Girl on the Train"
3. MYSTERY TITLES: "The Silent Patient", "The Whisper Man"
4. ACTION TITLES: Short, punchy - "Dune", "Twilight", "Divergent"
5. NAMED TITLES: "Rebecca", "Jane Eyre", "Carrie"

FOR CHAPTER TITLES:
- Create page-turner effect that keeps readers moving forward
- Build anticipation for what's coming next
- Match genre-appropriate style (thriller chapters feel different from romance)
- Make readers curious about the chapter content

You create titles that SELL books and keep readers turning pages."""


# =============================================================================
# Title Debate Orchestration
# =============================================================================

def run_book_title_debate(
    logline: str,
    theme: str,
    setting: str,
    plot_summary: str,
    model: str = DEFAULT_MODEL,
) -> dict:
    """
    Run a 3-agent debate to determine the book title.

    Args:
        logline: One-sentence story summary
        theme: Central theme of the story
        setting: Setting/world description
        plot_summary: Brief plot overview
        model: LLM model to use

    Returns:
        dict with:
            - winning_title: The selected book title
            - proposals: All 3 proposals
            - critiques: All critiques
            - votes: All votes
            - vote_tally: Vote counts
    """
    # Initialize agents
    agents = [
        TitleLiteraryAgent(model=model),
        TitleThematicAgent(model=model),
        TitleCommercialAgent(model=model),
    ]

    context = f"""STORY CONTEXT:
Logline: {logline}
Theme: {theme}
Setting: {setting}

PLOT SUMMARY:
{plot_summary}"""

    # ==========================================================================
    # Round 1: Proposals
    # ==========================================================================
    proposals = {}
    for agent in agents:
        prompt = f"""Propose a compelling BOOK TITLE for this story.

{context}

Create a title that:
1. Captures the essence of this story
2. Follows your methodology (literary devices / thematic depth / commercial appeal)
3. Would work on a book cover
4. Is memorable and distinctive

Provide your proposed title with reasoning."""

        proposal = agent.invoke_structured(prompt, BookTitleProposal, max_tokens=8000)
        proposals[agent.name] = proposal

    # ==========================================================================
    # Round 2: Critiques
    # ==========================================================================
    critiques = []
    for i, critic_agent in enumerate(agents):
        for j, target_agent in enumerate(agents):
            if i != j:  # Don't critique own proposal
                target_proposal = proposals[target_agent.name]
                prompt = f"""Critique this book title proposal:

{context}

PROPOSAL FROM {target_agent.name}:
Title: "{target_proposal.title}"
{f'Subtitle: "{target_proposal.subtitle}"' if target_proposal.subtitle else ''}
Reasoning: {target_proposal.reasoning}
Literary devices: {', '.join(target_proposal.literary_devices_used) if target_proposal.literary_devices_used else 'None specified'}

Evaluate this title's effectiveness. Be constructive but honest about strengths and weaknesses.
Consider: memorability, appropriateness, clarity, intrigue, and marketability."""

                critique = critic_agent.invoke_structured(prompt, TitleCritique, max_tokens=8000)
                critiques.append(critique)

    # ==========================================================================
    # Round 3: Votes
    # ==========================================================================
    votes = []
    for voter_agent in agents:
        # Build proposals summary for voting
        proposals_text = ""
        for agent_name, prop in proposals.items():
            if agent_name != voter_agent.name:  # Can't vote for own
                proposals_text += f"""
{agent_name}:
  Title: "{prop.title}"
  Reasoning: {prop.reasoning}
"""

        prompt = f"""Vote for the BEST book title for this story.

{context}

PROPOSALS TO CHOOSE FROM (you cannot vote for your own):
{proposals_text}

Select the title that best serves this story. Consider all factors:
memorability, thematic fit, commercial appeal, and literary quality."""

        vote = voter_agent.invoke_structured(prompt, TitleVote, max_tokens=8000)

        # Validate voted_for_agent is a real agent name (LLM sometimes returns a title string)
        valid_agents = {a.name for a in agents}
        if vote.voted_for_agent not in valid_agents:
            # Try to match the vote string against proposal titles
            matched = None
            for agent_name, prop in proposals.items():
                if agent_name != voter_agent.name and prop.title == vote.voted_for_agent:
                    matched = agent_name
                    break
            if matched:
                vote.voted_for_agent = matched
            else:
                other_agents = [a.name for a in agents if a.name != voter_agent.name]
                vote.voted_for_agent = other_agents[0]
        elif vote.voted_for_agent == voter_agent.name:
            # Pick another agent if they voted for themselves
            other_agents = [a.name for a in agents if a.name != voter_agent.name]
            vote.voted_for_agent = other_agents[0]

        votes.append(vote)

    # ==========================================================================
    # Tally votes and determine winner
    # ==========================================================================
    vote_counts = Counter(v.voted_for_agent for v in votes)

    if not vote_counts:
        # Fallback to first agent
        winner_agent = agents[0].name
    else:
        # Get agent(s) with most votes
        max_votes = max(vote_counts.values())
        winners = [agent for agent, count in vote_counts.items() if count == max_votes]

        if len(winners) == 1:
            winner_agent = winners[0]
        else:
            # Tie-break: use average critique score
            agent_scores = {}
            for agent_name in winners:
                agent_critiques = [c for c in critiques if c.target_agent == agent_name]
                if agent_critiques:
                    agent_scores[agent_name] = sum(c.score for c in agent_critiques) / len(agent_critiques)
                else:
                    agent_scores[agent_name] = 5.0
            winner_agent = max(agent_scores, key=agent_scores.get)

    winning_title = proposals[winner_agent].title
    winning_subtitle = proposals[winner_agent].subtitle

    return {
        "winning_title": winning_title,
        "winning_subtitle": winning_subtitle,
        "winner_agent": winner_agent,
        "proposals": {k: v.model_dump() for k, v in proposals.items()},
        "critiques": [c.model_dump() for c in critiques],
        "votes": [v.model_dump() for v in votes],
        "vote_tally": dict(vote_counts),
    }


def run_chapter_title_debate(
    chapter_number: int,
    chapter_summary: str,
    scenes_summary: str,
    book_title: str,
    theme: str,
    model: str = DEFAULT_MODEL,
) -> dict:
    """
    Run a 3-agent debate to determine a chapter title.

    Args:
        chapter_number: The chapter number
        chapter_summary: Summary of what happens in the chapter
        scenes_summary: Brief description of scenes
        book_title: The book's title (for consistency)
        theme: Story theme
        model: LLM model to use

    Returns:
        dict with:
            - winning_title: The selected chapter title
            - proposals: All 3 proposals
            - votes: All votes
    """
    # Initialize agents
    agents = [
        TitleLiteraryAgent(model=model),
        TitleThematicAgent(model=model),
        TitleCommercialAgent(model=model),
    ]

    context = f"""BOOK TITLE: {book_title}
THEME: {theme}
CHAPTER NUMBER: {chapter_number}

CHAPTER CONTENT:
{chapter_summary}

SCENES IN THIS CHAPTER:
{scenes_summary}"""

    # ==========================================================================
    # Round 1: Proposals
    # ==========================================================================
    proposals = {}
    for agent in agents:
        prompt = f"""Propose a CHAPTER TITLE for Chapter {chapter_number}.

{context}

Create a chapter title that:
1. Reflects what happens in this chapter
2. Creates intrigue without spoilers
3. Fits tonally with the book title "{book_title}"
4. Follows your methodology

The title should be SHORT (1-5 words typically).
Format: Just the title, no "Chapter X:" prefix."""

        proposal = agent.invoke_structured(prompt, ChapterTitleProposal, max_tokens=8000)
        proposals[agent.name] = proposal

    # ==========================================================================
    # Round 2: Quick vote (skip detailed critiques for chapters)
    # ==========================================================================
    votes = []
    for voter_agent in agents:
        proposals_text = ""
        for agent_name, prop in proposals.items():
            if agent_name != voter_agent.name:
                proposals_text += f'{agent_name}: "{prop.title}" - {prop.reasoning}\n'

        prompt = f"""Vote for the BEST chapter title for Chapter {chapter_number}.

{context}

PROPOSALS (you cannot vote for your own):
{proposals_text}

Select the title that best serves this chapter."""

        vote = voter_agent.invoke_structured(prompt, TitleVote, max_tokens=8000)

        # Validate voted_for_agent is a real agent name (LLM sometimes returns a title string)
        valid_agents = {a.name for a in agents}
        if vote.voted_for_agent not in valid_agents:
            matched = None
            for agent_name, prop in proposals.items():
                if agent_name != voter_agent.name and prop.title == vote.voted_for_agent:
                    matched = agent_name
                    break
            if matched:
                vote.voted_for_agent = matched
            else:
                other_agents = [a.name for a in agents if a.name != voter_agent.name]
                vote.voted_for_agent = other_agents[0]
        elif vote.voted_for_agent == voter_agent.name:
            other_agents = [a.name for a in agents if a.name != voter_agent.name]
            vote.voted_for_agent = other_agents[0]

        votes.append(vote)

    # ==========================================================================
    # Tally and determine winner
    # ==========================================================================
    vote_counts = Counter(v.voted_for_agent for v in votes)

    if not vote_counts:
        winner_agent = agents[0].name
    else:
        winner_agent = max(vote_counts, key=vote_counts.get)

    winning_title = proposals[winner_agent].title

    return {
        "chapter_number": chapter_number,
        "winning_title": winning_title,
        "winner_agent": winner_agent,
        "proposals": {k: v.model_dump() for k, v in proposals.items()},
        "votes": [v.model_dump() for v in votes],
        "vote_tally": dict(vote_counts),
    }
