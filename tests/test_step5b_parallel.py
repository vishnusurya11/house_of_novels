"""
Test cases for Step 5B parallel processing.

These tests verify that:
1. Parallel processing can be enabled/disabled via config
2. Round 1 (analysis) runs in parallel when enabled
3. Round 2 (critiques) runs in parallel when enabled
4. Results match between sequential and parallel execution
"""

import time
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.authors.base_phase1 import BaseAuthorPhase1
from src.story_schemas import ForeshadowingAnalysis, ForeshadowingCritique, ForeshadowingVote


class TestStep5BParallelProcessing:
    """Test parallel processing in Step 5B foreshadowing analysis"""

    @pytest.fixture
    def mock_codex(self):
        """Create a minimal codex for testing"""
        return {
            "story": {
                "chapters": {
                    "num_chapters": 2,
                    "chapters": [
                        {
                            "chapter_number": 1,
                            "scenes": [
                                {
                                    "scene_number": 1,
                                    "beat_name": "Opening Image",
                                    "scene_summary": "Hero introduction",
                                    "pov_character": "Hero",
                                    "location": "Home",
                                    "characters_present": ["Hero"],
                                    "tropes_manifesting": [],
                                    "estimated_word_count": 1500,
                                    "scene_type": "action"
                                }
                            ]
                        },
                        {
                            "chapter_number": 2,
                            "scenes": [
                                {
                                    "scene_number": 2,
                                    "beat_name": "Catalyst",
                                    "scene_summary": "Call to adventure",
                                    "pov_character": "Hero",
                                    "location": "Village",
                                    "characters_present": ["Hero", "Mentor"],
                                    "tropes_manifesting": [],
                                    "estimated_word_count": 1500,
                                    "scene_type": "action"
                                }
                            ]
                        }
                    ]
                },
                "characters": [{"name": "Hero"}],
                "integrated_beats": [],
                "tropes": []
            }
        }

    @pytest.fixture
    def mock_analysis(self):
        """Create mock foreshadowing analysis"""
        return {
            "agent_name": "Setup/Payoff Agent",
            "payoff_items": [
                {
                    "payoff_scene": "Ch2, Scene 2",
                    "required_setups": [
                        {
                            "insert_location": "Ch1, after Scene 1",
                            "scene_bullet": "Show hero's skill",
                            "characters_present": ["Hero"],
                            "estimated_word_count": 500,
                            "scene_type": "action"
                        }
                    ]
                }
            ],
            "existing_scene_annotations": []
        }

    def test_parallel_config_enabled(self, mock_codex):
        """Test that parallel processing config is correctly read"""
        author = BaseAuthorPhase1()

        # Mock get_step_config to return parallel enabled
        with patch('src.authors.base_phase1.get_step_config') as mock_config:
            mock_config.return_value = {
                "parallel_processing": {
                    "enabled": True,
                    "max_workers": 3
                }
            }

            # Mock the agents to avoid actual LLM calls
            with patch('src.authors.base_phase1.SetupPayoffAgent') as mock_setup, \
                 patch('src.authors.base_phase1.RuleOfThreeAgent') as mock_rule, \
                 patch('src.authors.base_phase1.TropeExecutionAgent') as mock_trope:

                # Create mock agent instances
                mock_agent = Mock()
                mock_agent.name = "MockAgent"
                mock_agent.analyze_foreshadowing.return_value = Mock(
                    dict=lambda: {"agent_name": "MockAgent", "payoff_items": [], "existing_scene_annotations": []},
                    payoff_items=[],
                    existing_scene_annotations=[]
                )
                mock_agent.critique_foreshadowing.return_value = Mock(
                    dict=lambda: {"agent_name": "MockAgent", "critiques": []}
                )
                mock_agent.vote_on_priorities.return_value = Mock(
                    dict=lambda: {"agent_name": "MockAgent", "essential_payoffs": []},
                    essential_payoffs=[]
                )

                mock_setup.return_value = mock_agent
                mock_rule.return_value = mock_agent
                mock_trope.return_value = mock_agent

                # This should not raise an error
                result = author.step5b_foreshadowing_analysis(mock_codex)

                # Verify config was checked
                mock_config.assert_called_with("step5b_foreshadowing")
                assert result["success"] is True

    def test_parallel_speedup_round1(self, mock_codex):
        """Test that Round 1 runs faster with parallel processing"""
        author = BaseAuthorPhase1()

        # Create a slow mock agent that takes 0.1 seconds per analysis
        def slow_analyze(*args, **kwargs):
            time.sleep(0.1)
            return Mock(
                dict=lambda: {"agent_name": "SlowAgent", "payoff_items": [], "existing_scene_annotations": []},
                payoff_items=[],
                existing_scene_annotations=[]
            )

        def fast_critique(*args, **kwargs):
            return Mock(dict=lambda: {"agent_name": "SlowAgent", "critiques": []})

        def fast_vote(*args, **kwargs):
            return Mock(
                dict=lambda: {"agent_name": "SlowAgent", "essential_payoffs": []},
                essential_payoffs=[]
            )

        # Test sequential execution
        with patch('src.authors.base_phase1.get_step_config') as mock_config, \
             patch('src.authors.base_phase1.SetupPayoffAgent') as mock_setup, \
             patch('src.authors.base_phase1.RuleOfThreeAgent') as mock_rule, \
             patch('src.authors.base_phase1.TropeExecutionAgent') as mock_trope:

            mock_config.return_value = {
                "parallel_processing": {"enabled": False, "max_workers": 3}
            }

            mock_agent = Mock()
            mock_agent.name = "SlowAgent"
            mock_agent.analyze_foreshadowing = slow_analyze
            mock_agent.critique_foreshadowing = fast_critique
            mock_agent.vote_on_priorities = fast_vote

            mock_setup.return_value = mock_agent
            mock_rule.return_value = mock_agent
            mock_trope.return_value = mock_agent

            start_sequential = time.time()
            result_sequential = author.step5b_foreshadowing_analysis(mock_codex.copy())
            time_sequential = time.time() - start_sequential

        # Test parallel execution
        with patch('src.authors.base_phase1.get_step_config') as mock_config, \
             patch('src.authors.base_phase1.SetupPayoffAgent') as mock_setup, \
             patch('src.authors.base_phase1.RuleOfThreeAgent') as mock_rule, \
             patch('src.authors.base_phase1.TropeExecutionAgent') as mock_trope:

            mock_config.return_value = {
                "parallel_processing": {"enabled": True, "max_workers": 3}
            }

            mock_agent = Mock()
            mock_agent.name = "SlowAgent"
            mock_agent.analyze_foreshadowing = slow_analyze
            mock_agent.critique_foreshadowing = fast_critique
            mock_agent.vote_on_priorities = fast_vote

            mock_setup.return_value = mock_agent
            mock_rule.return_value = mock_agent
            mock_trope.return_value = mock_agent

            start_parallel = time.time()
            result_parallel = author.step5b_foreshadowing_analysis(mock_codex.copy())
            time_parallel = time.time() - start_parallel

        # Parallel should be at least 2x faster (with 3 agents taking 0.1s each)
        # Sequential: 3 * 0.1 = 0.3s, Parallel: ~0.1s
        speedup = time_sequential / time_parallel
        print(f"\nSequential: {time_sequential:.2f}s, Parallel: {time_parallel:.2f}s, Speedup: {speedup:.2f}x")

        # Allow for some overhead, expect at least 1.5x speedup
        assert speedup >= 1.5, f"Expected speedup >= 1.5x, got {speedup:.2f}x"

    def test_parallel_critiques_round2(self, mock_codex):
        """Test that Round 2 critiques run in parallel"""
        author = BaseAuthorPhase1()

        # Track which critiques were called
        critique_calls = []

        def track_critique(analysis, context):
            critique_calls.append((analysis['agent_name'], time.time()))
            time.sleep(0.05)  # Small delay to simulate work
            return Mock(dict=lambda: {"agent_name": "CriticAgent", "critiques": []})

        with patch('src.authors.base_phase1.get_step_config') as mock_config, \
             patch('src.authors.base_phase1.SetupPayoffAgent') as mock_setup, \
             patch('src.authors.base_phase1.RuleOfThreeAgent') as mock_rule, \
             patch('src.authors.base_phase1.TropeExecutionAgent') as mock_trope:

            mock_config.return_value = {
                "parallel_processing": {"enabled": True, "max_workers": 3}
            }

            # Create 3 different mock agents
            agents = []
            for i, agent_class in enumerate([mock_setup, mock_rule, mock_trope]):
                mock_agent = Mock()
                mock_agent.name = f"Agent{i}"
                mock_agent.analyze_foreshadowing.return_value = Mock(
                    dict=lambda i=i: {"agent_name": f"Agent{i}", "payoff_items": [], "existing_scene_annotations": []},
                    payoff_items=[],
                    existing_scene_annotations=[]
                )
                mock_agent.critique_foreshadowing = track_critique
                mock_agent.vote_on_priorities.return_value = Mock(
                    dict=lambda: {"agent_name": mock_agent.name, "essential_payoffs": []},
                    essential_payoffs=[]
                )
                agent_class.return_value = mock_agent
                agents.append(mock_agent)

            result = author.step5b_foreshadowing_analysis(mock_codex)

            # With parallel execution, critiques should happen concurrently
            # Check that multiple critiques started before the first one finished
            if len(critique_calls) >= 2:
                time_diff = critique_calls[1][1] - critique_calls[0][1]
                # If parallel, second critique should start before first finishes (0.05s delay)
                assert time_diff < 0.05, "Critiques did not run in parallel"

    def test_results_consistency(self, mock_codex):
        """Test that parallel and sequential execution produce consistent results"""
        author = BaseAuthorPhase1()

        # Create deterministic mock responses
        def make_analysis(agent_name):
            return Mock(
                dict=lambda: {
                    "agent_name": agent_name,
                    "payoff_items": [{"payoff_scene": f"Ch1, Scene 1 ({agent_name})"}],
                    "existing_scene_annotations": []
                },
                payoff_items=[{"payoff_scene": f"Ch1, Scene 1 ({agent_name})"}],
                existing_scene_annotations=[]
            )

        def make_critique(agent_name):
            return Mock(dict=lambda: {"agent_name": agent_name, "critiques": ["Good"]})

        def make_vote(agent_name):
            return Mock(
                dict=lambda: {"agent_name": agent_name, "essential_payoffs": [f"Ch1, Scene 1 ({agent_name})"]},
                essential_payoffs=[f"Ch1, Scene 1 ({agent_name})"]
            )

        # Test with parallel enabled
        with patch('src.authors.base_phase1.get_step_config') as mock_config, \
             patch('src.authors.base_phase1.SetupPayoffAgent') as mock_setup, \
             patch('src.authors.base_phase1.RuleOfThreeAgent') as mock_rule, \
             patch('src.authors.base_phase1.TropeExecutionAgent') as mock_trope:

            mock_config.return_value = {
                "parallel_processing": {"enabled": True, "max_workers": 3}
            }

            for i, agent_class in enumerate([mock_setup, mock_rule, mock_trope]):
                mock_agent = Mock()
                mock_agent.name = f"Agent{i}"
                mock_agent.analyze_foreshadowing.return_value = make_analysis(f"Agent{i}")
                mock_agent.critique_foreshadowing.return_value = make_critique(f"Agent{i}")
                mock_agent.vote_on_priorities.return_value = make_vote(f"Agent{i}")
                agent_class.return_value = mock_agent

            result_parallel = author.step5b_foreshadowing_analysis(mock_codex.copy())

        # Test with parallel disabled
        with patch('src.authors.base_phase1.get_step_config') as mock_config, \
             patch('src.authors.base_phase1.SetupPayoffAgent') as mock_setup, \
             patch('src.authors.base_phase1.RuleOfThreeAgent') as mock_rule, \
             patch('src.authors.base_phase1.TropeExecutionAgent') as mock_trope:

            mock_config.return_value = {
                "parallel_processing": {"enabled": False, "max_workers": 3}
            }

            for i, agent_class in enumerate([mock_setup, mock_rule, mock_trope]):
                mock_agent = Mock()
                mock_agent.name = f"Agent{i}"
                mock_agent.analyze_foreshadowing.return_value = make_analysis(f"Agent{i}")
                mock_agent.critique_foreshadowing.return_value = make_critique(f"Agent{i}")
                mock_agent.vote_on_priorities.return_value = make_vote(f"Agent{i}")
                agent_class.return_value = mock_agent

            result_sequential = author.step5b_foreshadowing_analysis(mock_codex.copy())

        # Both should succeed
        assert result_parallel["success"] is True
        assert result_sequential["success"] is True

        # Both should have the same number of analyses
        assert len(result_parallel["debates"]["analyses"]) == len(result_sequential["debates"]["analyses"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
