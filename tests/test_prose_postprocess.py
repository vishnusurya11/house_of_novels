"""Tests for src.story_agents.prose_postprocess — Deterministic prose cleanup."""

import pytest

from src.story_agents.prose_postprocess import prose_postprocess


class TestSmartQuoteNormalization:
    def test_curly_double_quotes(self):
        result = prose_postprocess("\u201cHello,\u201d she said.")
        assert "\u201c" not in result
        assert "\u201d" not in result
        assert '"Hello,"' in result

    def test_curly_single_quotes(self):
        result = prose_postprocess("It\u2019s a fine day.")
        assert "\u2019" not in result
        assert "It's" in result

    def test_em_dash_preserved(self):
        result = prose_postprocess("She ran\u2014fast.")
        assert "\u2014" in result


class TestBannedPhrases:
    def test_weight_of_removed(self):
        result = prose_postprocess("She felt the weight of responsibility.")
        assert "the weight of" not in result

    def test_fragile_hope_replaced(self):
        result = prose_postprocess("A fragile hope flickered.")
        assert "fragile hope" not in result
        assert "a stubborn hope" in result

    def test_stark_reminder_removed(self):
        result = prose_postprocess("It was a stark reminder that time was short.")
        assert "a stark reminder that" not in result

    def test_something_shifted_removed(self):
        result = prose_postprocess("Something shifted inside her.")
        assert "something shifted inside" not in result.lower()

    def test_resolve_hardened_removed(self):
        result = prose_postprocess("Her resolve hardened as she walked.")
        assert "resolve hardened" not in result.lower()

    def test_doubt_gnawed_removed(self):
        result = prose_postprocess("Doubt gnawed at him.")
        assert "doubt gnawed" not in result.lower()

    def test_case_insensitive(self):
        result = prose_postprocess("THE WEIGHT OF the world.")
        assert "the weight of" not in result.lower()


class TestOveruseCap:
    def test_shadow_capped_at_two(self):
        prose = "A shadow fell. The shadow deepened. Another shadow crept. The shadow loomed."
        result = prose_postprocess(prose)
        assert result.lower().count("shadow") == 2
        assert "darkness" in result.lower()

    def test_shadows_capped_at_two(self):
        prose = "Shadows danced. The shadows grew. More shadows appeared."
        result = prose_postprocess(prose)
        assert result.lower().count("shadows") == 2
        assert "the dark" in result.lower()

    def test_beneath_capped_at_two(self):
        prose = "Beneath the tree. Beneath the sky. Beneath the moon."
        result = prose_postprocess(prose)
        assert result.lower().count("beneath") == 2
        assert "under" in result.lower()

    def test_under_cap_no_change_if_ok(self):
        prose = "A shadow fell. The light dimmed."
        result = prose_postprocess(prose)
        assert "shadow" in result  # Only one, should stay


class TestArtifactCleanup:
    def test_double_spaces(self):
        result = prose_postprocess("She  walked  home.")
        assert "  " not in result

    def test_orphaned_comma(self):
        result = prose_postprocess("She , walked.")
        assert " ," not in result

    def test_double_periods(self):
        result = prose_postprocess("She walked..")
        assert ".." not in result

    def test_leading_spaces_on_lines(self):
        result = prose_postprocess(" She walked.\n He ran.")
        assert not any(line.startswith(" ") for line in result.split("\n"))


class TestPronounConsistency:
    def test_no_crash_on_male(self):
        """Just verifies no exception — actual check is logging only."""
        result = prose_postprocess(
            "He walked. She ran. He turned.",
            pov_gender="male",
        )
        assert result  # Returns text, doesn't crash

    def test_no_crash_on_female(self):
        result = prose_postprocess(
            "She walked. He ran. She turned.",
            pov_gender="female",
        )
        assert result

    def test_skips_when_no_gender(self):
        result = prose_postprocess("He walked. She ran.")
        assert result  # No crash with default empty gender

    def test_ignores_dialogue_pronouns(self):
        """Pronouns inside quotes shouldn't count for narration check."""
        result = prose_postprocess(
            'She looked up. "He is coming," she said. She ran.',
            pov_gender="female",
        )
        assert result


class TestEmptyInput:
    def test_empty_string(self):
        assert prose_postprocess("") == ""

    def test_whitespace_only(self):
        result = prose_postprocess("   ")
        assert result.strip() == ""


class TestPhantomCharacterDetection:
    def test_no_crash_with_roster(self):
        """Phantom check runs without crashing."""
        result = prose_postprocess(
            '"Run!" Elena shouted. The building shook.',
            characters_present=["Elena Cruz"],
        )
        assert result

    def test_no_crash_without_roster(self):
        """Works fine with no roster (skips check)."""
        result = prose_postprocess('"Hello," she said.')
        assert result

    def test_detects_phantom_speaker(self, caplog):
        """Warns when a name near a speech verb isn't in the roster."""
        import logging
        with caplog.at_level(logging.WARNING, logger="prose_quality"):
            prose_postprocess(
                'Elys urged them forward. "We must hurry!" Elys shouted.',
                characters_present=["Liora Zale"],
            )
        assert any("PHANTOM_CHARACTER" in r.message and "Elys" in r.message for r in caplog.records)

    def test_no_warning_for_known_character(self, caplog):
        """No warning when dialogue is attributed to a listed character."""
        import logging
        with caplog.at_level(logging.WARNING, logger="prose_quality"):
            prose_postprocess(
                '"Come on," Liora said.',
                characters_present=["Liora Zale"],
            )
        assert not any("PHANTOM_CHARACTER" in r.message for r in caplog.records)

    def test_first_name_match(self, caplog):
        """First name from 'Liora Zale' matches 'Liora said'."""
        import logging
        with caplog.at_level(logging.WARNING, logger="prose_quality"):
            prose_postprocess(
                '"Run!" Liora shouted. "Now!" Zale called.',
                characters_present=["Liora Zale"],
            )
        assert not any("PHANTOM_CHARACTER" in r.message for r in caplog.records)


class TestCombinedProcessing:
    def test_multiple_fixes_at_once(self):
        """Smart quotes + banned phrase + overuse in one pass."""
        prose = (
            "\u201cThe weight of it all,\u201d she sighed. "
            "A shadow fell. The shadow deepened. A shadow crept."
        )
        result = prose_postprocess(prose)
        # Smart quotes normalized
        assert "\u201c" not in result
        # Banned phrase removed
        assert "the weight of" not in result
        # Shadow capped
        assert result.lower().count("shadow") <= 2
