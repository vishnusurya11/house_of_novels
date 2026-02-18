"""
Tests for the _run_parallel_debate() method in BaseAuthorPhase1.

This test suite validates:
1. Successful completion of the 3-stage debate process
2. Proper vote counting and winner determination
3. Thread-safe logging with worker IDs
4. Correct return structure with all required fields
"""

import pytest
from collections import Counter
from dataclasses import dataclass
from unittest.mock import MagicMock, patch
import io
import sys


# Mock data classes for proposals, critiques, and votes
@dataclass
class MockProposal:
    agent_name: str
    content: str


@dataclass
class MockCritique:
    agent_name: str
    critique: str


@dataclass
class MockVote:
    agent_name: str
    voted_for_agent: str


# Mock agent classes
class MockProposer:
    def __init__(self, name: str, proposal_content: str):
        self.name = name
        self.proposal_content = proposal_content

    def propose(self, context: dict) -> MockProposal:
        return MockProposal(agent_name=self.name, content=self.proposal_content)


class MockCritic:
    def __init__(self, name: str, critique_content: str):
        self.name = name
        self.critique_content = critique_content

    def critique(self, context: dict) -> MockCritique:
        # Validate that proposals are in context
        assert 'proposals' in context
        return MockCritique(agent_name=self.name, critique=self.critique_content)


class MockVoter:
    def __init__(self, name: str, vote_for: str):
        self.name = name
        self.vote_for = vote_for

    def vote(self, context: dict) -> MockVote:
        # Validate that proposals and critiques are in context
        assert 'proposals' in context
        assert 'critiques' in context
        return MockVote(agent_name=self.name, voted_for_agent=self.vote_for)


# Fixture to create a mock BaseAuthorPhase1 instance
@pytest.fixture
def mock_base_author():
    """Create a minimal mock of BaseAuthorPhase1 with just the _run_parallel_debate method."""
    from src.authors.base_phase1 import BaseAuthorPhase1

    # Create a mock author and config
    mock_author = MagicMock()
    mock_author.name = "TestAuthor"
    mock_author.preferred_structure = "three_act"

    # Create instance (we only need the method, not full initialization)
    instance = object.__new__(BaseAuthorPhase1)
    instance.author = mock_author

    return instance


def test_successful_debate_completion(mock_base_author):
    """Test that the debate completes successfully with all stages."""
    # Create mock agents
    proposers = [
        MockProposer("Proposer1", "Proposal A"),
        MockProposer("Proposer2", "Proposal B"),
        MockProposer("Proposer3", "Proposal C"),
    ]

    critics = [
        MockCritic("Critic1", "Critique A"),
        MockCritic("Critic2", "Critique B"),
    ]

    voters = [
        MockVoter("Voter1", "Proposer1"),
        MockVoter("Voter2", "Proposer1"),
        MockVoter("Voter3", "Proposer2"),
    ]

    context = {"test_key": "test_value"}

    # Run the debate
    result = mock_base_author._run_parallel_debate(proposers, critics, voters, context)

    # Validate structure
    assert 'proposals' in result
    assert 'critiques' in result
    assert 'votes' in result
    assert 'winner_index' in result
    assert 'winner' in result
    assert 'vote_counts' in result

    # Validate content
    assert len(result['proposals']) == 3
    assert len(result['critiques']) == 2
    assert len(result['votes']) == 3

    # Winner should be Proposer1 (2 votes)
    assert result['winner'].agent_name == "Proposer1"
    assert result['winner_index'] == 0
    assert result['vote_counts']['Proposer1'] == 2
    assert result['vote_counts']['Proposer2'] == 1


def test_vote_counting(mock_base_author):
    """Test that votes are counted correctly."""
    proposers = [
        MockProposer("Agent_A", "Proposal A"),
        MockProposer("Agent_B", "Proposal B"),
        MockProposer("Agent_C", "Proposal C"),
    ]

    critics = [MockCritic("Critic1", "Good")]

    # All voters choose Agent_B
    voters = [
        MockVoter("Voter1", "Agent_B"),
        MockVoter("Voter2", "Agent_B"),
        MockVoter("Voter3", "Agent_B"),
        MockVoter("Voter4", "Agent_B"),
    ]

    context = {}

    result = mock_base_author._run_parallel_debate(proposers, critics, voters, context)

    # Validate winner
    assert result['winner'].agent_name == "Agent_B"
    assert result['winner_index'] == 1
    assert result['vote_counts']['Agent_B'] == 4

    # Validate vote_counts is a Counter
    assert isinstance(result['vote_counts'], Counter)


def test_thread_safe_logging(mock_base_author):
    """Test that logging includes worker IDs and is thread-safe."""
    proposers = [
        MockProposer("P1", "Proposal 1"),
        MockProposer("P2", "Proposal 2"),
    ]

    critics = [MockCritic("C1", "Critique 1")]
    voters = [MockVoter("V1", "P1")]

    context = {}

    # Capture stdout
    captured_output = io.StringIO()
    sys.stdout = captured_output

    try:
        result = mock_base_author._run_parallel_debate(proposers, critics, voters, context)

        output = captured_output.getvalue()

        # Check for worker thread logging
        assert "[Worker-" in output or "Worker-" in output
        assert "proposing..." in output
        assert "critiquing..." in output
        assert "voting..." in output
        assert "finished proposal" in output
        assert "finished critique" in output
        assert "finished voting" in output

        # Check for completion messages
        assert "Collected 2 proposals" in output
        assert "Collected 1 critiques" in output
        assert "Collected 1 votes" in output

    finally:
        sys.stdout = sys.__stdout__


def test_context_passing(mock_base_author):
    """Test that context is properly passed through all stages."""
    context = {
        "story_id": "12345",
        "chapter": 3,
        "metadata": {"author": "TestAuthor"}
    }

    proposers = [MockProposer("P1", "Content")]
    critics = [MockCritic("C1", "Good")]
    voters = [MockVoter("V1", "P1")]

    # We'll use a custom voter that checks context
    class ContextCheckingVoter:
        def vote(self, ctx: dict) -> MockVote:
            # Ensure original context is present
            assert "story_id" in ctx
            assert ctx["story_id"] == "12345"
            assert "chapter" in ctx
            assert ctx["chapter"] == 3
            # Ensure proposals and critiques were added
            assert "proposals" in ctx
            assert "critiques" in ctx
            return MockVote("V1", "P1")

    voters_with_check = [ContextCheckingVoter()]

    result = mock_base_author._run_parallel_debate(proposers, critics, voters_with_check, context)

    # If we get here without assertion errors, context was passed correctly
    assert result is not None


def test_empty_vote_counts(mock_base_author):
    """Test handling when votes are distributed."""
    proposers = [
        MockProposer("A", "Proposal A"),
        MockProposer("B", "Proposal B"),
        MockProposer("C", "Proposal C"),
    ]

    critics = [MockCritic("C1", "OK")]

    voters = [
        MockVoter("V1", "A"),
        MockVoter("V2", "B"),
        MockVoter("V3", "C"),
    ]

    context = {}

    result = mock_base_author._run_parallel_debate(proposers, critics, voters, context)

    # All should have 1 vote, winner should be the one with most_common
    assert len(result['vote_counts']) == 3
    assert result['vote_counts']['A'] == 1
    assert result['vote_counts']['B'] == 1
    assert result['vote_counts']['C'] == 1

    # Winner should be one of them (first in most_common)
    assert result['winner'].agent_name in ['A', 'B', 'C']


def test_return_structure(mock_base_author):
    """Test that return dictionary has all required keys and correct types."""
    proposers = [MockProposer("P1", "Content")]
    critics = [MockCritic("C1", "Critique")]
    voters = [MockVoter("V1", "P1")]

    result = mock_base_author._run_parallel_debate(proposers, critics, voters, {})

    # Validate keys
    required_keys = {'proposals', 'critiques', 'votes', 'winner_index', 'winner', 'vote_counts'}
    assert set(result.keys()) == required_keys

    # Validate types
    assert isinstance(result['proposals'], list)
    assert isinstance(result['critiques'], list)
    assert isinstance(result['votes'], list)
    assert isinstance(result['winner_index'], int)
    assert isinstance(result['winner'], MockProposal)
    assert isinstance(result['vote_counts'], Counter)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
