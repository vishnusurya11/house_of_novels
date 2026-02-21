"""
Test cases for SUBSTEP 7A: Scene Structure Validator

Run with: uv run pytest tests/test_scene_structure_validator.py -v
"""

import pytest
from src.story_agents.scene_structure_validator import SceneStructureValidator


# Test fixtures - sample scenes
PERFECT_ACTION_SCENE = """
Alice needed to steal the key before dawn. She had one chance.

The guard turned, hand on his sword. Alice froze behind the pillar, heart hammering.

"Who's there?" He stepped closer, boots echoing on stone.

Alice's breath caught. She couldn't move. Couldn't run.

The alarm bell rang. The guard whirled toward the sound.

Alice ran, empty-handed into the shadows. Behind her, shouts erupted. They knew she'd been there.
"""

MISSING_GOAL_SCENE = """
Alice walked through the garden. Birds sang in the trees. The morning sun felt warm on her face.

She turned the corner and saw roses blooming. Red ones, like her mother used to grow.

A guard appeared suddenly. Alice hid behind a statue.

Everything went dark as storm clouds gathered overhead.
"""

SEQUEL_SCENE = """
Alice slumped against the cold stone wall, her heart still pounding from the chase. She'd failed. The key was still locked away, and now they knew someone had tried.

If she tried again tonight, the guards would be ready. They'd kill her on sight. But if she didn't try, her sister would die tomorrow at dawn. Two impossible choices.

She stood slowly, jaw clenched. There was another way in. Through the sewers. It would be dangerous, disgusting, probably suicidal. But it was the only option left.

She started walking toward the east gate. Decision made.
"""

MISSING_DISASTER_SCENE = """
Alice needed to find the traitor before the meeting at noon.

She searched the records room, pulling out dusty files. Marcus's name appeared three times in the ledgers. Always present when shipments went missing.

She found the final proof - a letter in Marcus's handwriting. He was the one.

Alice set the file aside and looked at the clock. Still had time.
"""

NO_STRUCTURE_SCENE = """
Alice ate breakfast. The eggs were cold but she didn't mind. She liked cold eggs sometimes.

Outside, a bird flew past the window. It was probably a robin. Or maybe a sparrow.

She thought about her day. Maybe she'd go for a walk later. Or read a book. She hadn't decided yet.

The morning passed quietly.
"""


@pytest.fixture
def validator():
    """Create validator instance for tests."""
    return SceneStructureValidator()


def test_perfect_action_scene(validator):
    """Test 1: Perfect action scene should score 9+."""

    result = validator.validate_structure(
        scene_prose=PERFECT_ACTION_SCENE,
        scene_context={
            "pov_character": "Alice",
            "goal": "Steal the key"
        }
    )

    # Assertions
    assert result.has_clear_goal == True, "Should detect clear goal"
    assert "paragraph 1" in result.goal_stated_location.lower(), "Goal should be in opening"
    assert result.has_conflict == True, "Should detect conflict"
    assert result.conflict_type in ["face-to-face", "situational"], "Should identify conflict type"
    assert result.has_disaster_or_outcome == True, "Should detect disaster"
    assert result.scene_type == "action_scene", "Should identify as action scene"
    assert result.structure_score >= 7.5, f"Should score 7.5+ but got {result.structure_score}"
    assert result.revision_needed == False, "Well-structured scene shouldn't need revision"
    assert len(result.missing_elements) == 0, "Should have no missing elements"


def test_missing_goal(validator):
    """Test 2: Scene with no clear goal should fail validation."""

    result = validator.validate_structure(
        scene_prose=MISSING_GOAL_SCENE,
        scene_context={
            "pov_character": "Alice"
        }
    )

    # Assertions
    assert result.has_clear_goal == False, "Should detect missing goal"
    assert "missing" in result.goal_stated_location.lower(), "Goal location should be 'missing'"
    assert "clear_goal" in result.missing_elements or "goal" in result.missing_elements, \
        "Missing elements should include goal"
    assert result.structure_score < 6.0, f"Should score < 6 but got {result.structure_score}"
    assert result.revision_needed == True, "Missing goal should require revision"
    assert len(result.revision_suggestions) > 0, "Should provide revision suggestions"


def test_sequel_scene_structure(validator):
    """Test 3: Sequel scene (Reaction → Dilemma → Decision) should be recognized."""

    result = validator.validate_structure(
        scene_prose=SEQUEL_SCENE,
        scene_context={
            "pov_character": "Alice"
        }
    )

    # Assertions
    assert result.scene_type == "sequel_scene", f"Should identify as sequel_scene but got {result.scene_type}"
    assert result.has_clear_goal == True, "Sequel has goal: make a decision"
    assert result.has_disaster_or_outcome == True, "Should have decision as outcome"
    assert result.structure_score >= 8.0, f"Well-structured sequel should score 8+ but got {result.structure_score}"


def test_missing_disaster(validator):
    """Test 4: Scene with no disaster/outcome should be flagged."""

    result = validator.validate_structure(
        scene_prose=MISSING_DISASTER_SCENE,
        scene_context={
            "pov_character": "Alice",
            "goal": "Find the traitor"
        }
    )

    # Assertions
    assert result.has_disaster_or_outcome == False, "Should detect missing disaster"
    assert "missing" in result.disaster_location.lower(), "Disaster location should be 'missing'"
    assert "disaster" in result.missing_elements or "outcome" in result.missing_elements, \
        "Missing elements should include disaster/outcome"
    assert result.revision_needed == True, "Missing disaster should require revision"


def test_no_structure(validator):
    """Test 5: Scene with no structure should score very low."""

    result = validator.validate_structure(
        scene_prose=NO_STRUCTURE_SCENE,
        scene_context={
            "pov_character": "Alice"
        }
    )

    # Assertions
    assert result.has_clear_goal == False, "Should detect no goal"
    assert result.has_conflict == False, "Should detect no conflict"
    assert result.has_disaster_or_outcome == False, "Should detect no outcome"
    assert result.scene_type == "unclear", f"Should be 'unclear' but got {result.scene_type}"
    assert result.structure_score < 3.0, f"Should score < 3 but got {result.structure_score}"
    assert result.revision_needed == True, "Should need major revision"
    assert len(result.missing_elements) >= 2, "Should have multiple missing elements"


def test_integration_with_real_codex_format(validator):
    """Test 6: Ensure validator works with actual codex scene format."""

    # Simulate how scenes appear in codex
    codex_scene = {
        "scene_id": "ch1_sc1",
        "prose": PERFECT_ACTION_SCENE,
        "pov_character": "Alice",
        "goal": "Steal the key",
        "conflict": "Guard confrontation",
        "disaster": "Alarm rings, escape empty-handed"
    }

    result = validator.validate_structure(
        scene_prose=codex_scene["prose"],
        scene_context={
            "pov_character": codex_scene["pov_character"],
            "goal": codex_scene["goal"]
        }
    )

    # Should work without errors
    assert isinstance(result.structure_score, float)
    assert 0.0 <= result.structure_score <= 10.0
    assert isinstance(result.revision_needed, bool)


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v"])
