"""Tests for src.tts.script_generator — Hybrid audio script generation."""

import json

import pytest
from unittest.mock import MagicMock

from src.tts.script_generator import (
    AudioScriptGenerator,
    _build_arc_beats_block,
    _build_character_roster,
    _build_characters_block,
    _build_prose_block,
    _build_thematic_block,
    _normalize_quotes,
)


# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------

SAMPLE_CHARACTERS = [
    {
        "name": "Elena Cruz",
        "character_id": "char_001",
        "role": "protagonist",
        "gender": "female",
        "personality_summary": "Sharp detective with a relentless drive for truth",
    },
    {
        "name": "Ryan Park",
        "character_id": "char_002",
        "role": "witness",
        "gender": "male",
        "personality_summary": "Nervous young man caught in circumstances beyond his control",
    },
]

SAMPLE_SCENE = {
    "scene_summary": "A tense confrontation in the diner.",
    "location": "Harbor City Diner",
    "time_of_day": "night",
    "scene_type": "dialogue",
    "characters_present": ["Elena Cruz", "Ryan Park"],
    "character_arc_beats": [
        {
            "character_name": "Elena Cruz",
            "emotional_state": "Focused",
            "internal_change": "Growing suspicion",
        },
        {
            "character_name": "Ryan Park",
            "emotional_state": "Anxious",
            "internal_change": "Deciding whether to cooperate",
        },
    ],
    "thematic_beat": {
        "thematic_question": "Can truth survive under pressure?",
        "how_scene_tests_theme": "Characters weigh honesty against self-preservation.",
    },
    "prose": 'Elena leaned forward. "Tell me the truth." Ryan hesitated. "I can\'t."',
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_mock_response(content: str) -> MagicMock:
    """Create a mock OpenAI chat completion response."""
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message.content = content
    return response


@pytest.fixture
def generator() -> AudioScriptGenerator:
    """AudioScriptGenerator with mocked OpenAI client."""
    gen = AudioScriptGenerator.__new__(AudioScriptGenerator)
    gen.client = MagicMock()
    gen.model = "test-model"
    gen.temperature = 0.3
    gen.max_tokens = 4000
    return gen


# ---------------------------------------------------------------------------
# Helper function tests
# ---------------------------------------------------------------------------

class TestBuildCharactersBlock:
    """Tests for _build_characters_block helper."""

    def test_full_character_data(self):
        scene = {"characters_present": ["Elena Cruz", "Ryan Park"]}
        result = _build_characters_block(scene, SAMPLE_CHARACTERS)
        assert "Elena Cruz [ID: char_001]" in result
        assert "protagonist" in result
        assert "Ryan Park [ID: char_002]" in result

    def test_missing_character_in_codex(self):
        scene = {"characters_present": ["Unknown Person"]}
        result = _build_characters_block(scene, SAMPLE_CHARACTERS)
        assert "Unknown Person" in result

    def test_empty_characters(self):
        scene = {"characters_present": []}
        result = _build_characters_block(scene, SAMPLE_CHARACTERS)
        assert "no character details" in result

    def test_personality_as_list(self):
        chars = [{"name": "Test", "character_id": "c1", "role": "x", "personality_summary": ["brave", "kind", "smart"]}]
        scene = {"characters_present": ["Test"]}
        result = _build_characters_block(scene, chars)
        assert "brave" in result

    def test_personality_as_dict(self):
        chars = [{"name": "Test", "character_id": "c1", "role": "x", "personality_summary": {"summary": "Complex"}}]
        scene = {"characters_present": ["Test"]}
        result = _build_characters_block(scene, chars)
        assert "Complex" in result

    def test_fallback_characters_key(self):
        scene = {"characters": ["Elena Cruz"]}
        result = _build_characters_block(scene, SAMPLE_CHARACTERS)
        assert "Elena Cruz" in result


class TestBuildArcBeatsBlock:
    def test_normal_beats(self):
        result = _build_arc_beats_block(SAMPLE_SCENE)
        assert "Elena Cruz" in result
        assert "Focused" in result

    def test_empty_beats(self):
        result = _build_arc_beats_block({"character_arc_beats": []})
        assert "no arc beats" in result

    def test_missing_key(self):
        result = _build_arc_beats_block({})
        assert "no arc beats" in result


class TestBuildThematicBlock:
    def test_normal_thematic(self):
        result = _build_thematic_block(SAMPLE_SCENE)
        assert "truth survive" in result

    def test_empty_thematic(self):
        result = _build_thematic_block({"thematic_beat": {}})
        assert "no thematic context" in result

    def test_missing_key(self):
        result = _build_thematic_block({})
        assert "no thematic context" in result


class TestBuildProseBlock:
    def test_with_prose(self):
        result = _build_prose_block(SAMPLE_SCENE)
        assert "EXISTING PROSE" in result
        assert "Elena leaned forward" in result

    def test_empty_prose(self):
        assert _build_prose_block({"prose": ""}) == ""

    def test_missing_key(self):
        assert _build_prose_block({}) == ""


class TestBuildCharacterRoster:
    def test_maps_names_to_ids(self):
        result = _build_character_roster(SAMPLE_CHARACTERS, ["Elena Cruz", "Ryan Park"])
        assert result == "NARRATOR, char_001, char_002"

    def test_narrator_always_first(self):
        result = _build_character_roster(SAMPLE_CHARACTERS, ["Ryan Park"])
        assert result.startswith("NARRATOR")

    def test_unknown_character_gets_fallback_id(self):
        result = _build_character_roster(SAMPLE_CHARACTERS, ["Unknown Person"])
        assert "UNKNOWN_PERSON" in result

    def test_empty_present(self):
        assert _build_character_roster(SAMPLE_CHARACTERS, []) == "NARRATOR"


class TestNormalizeQuotes:
    def test_curly_double_quotes(self):
        assert _normalize_quotes("\u201cHello\u201d") == '"Hello"'

    def test_curly_single_quotes(self):
        assert _normalize_quotes("\u2018Hi\u2019") == "'Hi'"

    def test_no_change_for_ascii(self):
        assert _normalize_quotes('"Normal"') == '"Normal"'


# ---------------------------------------------------------------------------
# Rule-based prose splitting tests
# ---------------------------------------------------------------------------

class TestSplitProseIntoChunks:
    """Tests for AudioScriptGenerator._split_prose_into_chunks."""

    def test_simple_dialogue(self, generator):
        """Basic prose with one dialogue line splits correctly."""
        prose = 'She paused. "Tell me the truth." He looked away.'
        chunks = generator._split_prose_into_chunks(
            prose, ["Elena Cruz"], SAMPLE_CHARACTERS,
        )
        assert len(chunks) == 3
        assert chunks[0]["speaker"] == "NARRATOR"
        assert chunks[1]["speaker"] == "char_001"
        assert chunks[1]["text"] == '"Tell me the truth."'
        assert chunks[2]["speaker"] == "NARRATOR"

    def test_text_preservation(self, generator):
        """Concatenated chunk text matches original prose (whitespace-normalized)."""
        prose = 'The room was cold. "We need to go," Elena said. Ryan nodded.'
        chunks = generator._split_prose_into_chunks(
            prose, ["Elena Cruz", "Ryan Park"], SAMPLE_CHARACTERS,
        )
        reconstructed = " ".join(c["text"] for c in chunks)
        assert " ".join(prose.split()) == " ".join(reconstructed.split())

    def test_speaker_attribution_after_dialogue(self, generator):
        """'Name said' after quote attributes correctly."""
        prose = '"Run!" Elena shouted. The building shook.'
        chunks = generator._split_prose_into_chunks(
            prose, ["Elena Cruz", "Ryan Park"], SAMPLE_CHARACTERS,
        )
        dialogue_chunk = next(c for c in chunks if c["text"].startswith('"'))
        assert dialogue_chunk["speaker"] == "char_001"

    def test_speaker_attribution_pronoun(self, generator):
        """Pronoun + speech verb attributes via gender mapping."""
        prose = '"I understand," she whispered. The candle flickered.'
        chars = [
            {"name": "Maya Lin", "character_id": "char_010", "gender": "female"},
            {"name": "Jake Ross", "character_id": "char_011", "gender": "male"},
        ]
        chunks = generator._split_prose_into_chunks(
            prose, ["Maya Lin", "Jake Ross"], chars,
        )
        dialogue_chunk = next(c for c in chunks if c["text"].startswith('"'))
        assert dialogue_chunk["speaker"] == "char_010"

    def test_consecutive_narrator_merged(self, generator):
        """Consecutive narration segments get merged into one chunk."""
        prose = "The sun set. Stars appeared. Night fell."
        chunks = generator._split_prose_into_chunks(
            prose, [], [],
        )
        assert len(chunks) == 1
        assert chunks[0]["speaker"] == "NARRATOR"

    def test_multiple_dialogues(self, generator):
        """Multiple dialogue lines from different characters."""
        prose = (
            '"We should leave," Elena said. '
            'Ryan shook his head. "Not yet," he replied.'
        )
        chunks = generator._split_prose_into_chunks(
            prose, ["Elena Cruz", "Ryan Park"], SAMPLE_CHARACTERS,
        )
        dialogue_chunks = [c for c in chunks if c["speaker"] != "NARRATOR"]
        assert len(dialogue_chunks) == 2
        assert dialogue_chunks[0]["speaker"] == "char_001"  # Elena
        assert dialogue_chunks[1]["speaker"] == "char_002"  # Ryan (he)

    def test_smart_quotes_normalized(self, generator):
        """Smart/curly quotes get normalized before splitting."""
        prose = 'She said, \u201cHello.\u201d He replied, \u201cHi.\u201d'
        chunks = generator._split_prose_into_chunks(
            prose, ["Elena Cruz", "Ryan Park"], SAMPLE_CHARACTERS,
        )
        # All quotes should be ASCII after normalization
        for chunk in chunks:
            assert "\u201c" not in chunk["text"]
            assert "\u201d" not in chunk["text"]

    def test_narration_only(self, generator):
        """Prose without any dialogue produces a single NARRATOR chunk."""
        prose = "The ship sailed into the harbor. Waves crashed against the dock."
        chunks = generator._split_prose_into_chunks(prose, [], [])
        assert len(chunks) == 1
        assert chunks[0]["speaker"] == "NARRATOR"
        assert chunks[0]["text"] == prose

    def test_first_name_attribution(self, generator):
        """First name in dialogue tag matches full character name."""
        prose = '"Follow me," Elena whispered.'
        chunks = generator._split_prose_into_chunks(
            prose, ["Elena Cruz"], SAMPLE_CHARACTERS,
        )
        dialogue_chunk = next(c for c in chunks if c["text"].startswith('"'))
        assert dialogue_chunk["speaker"] == "char_001"

    def test_last_speaker_fallback(self, generator):
        """Second dialogue without tag falls back to last named speaker."""
        prose = '"Hello," Elena said. "How are you?"'
        chunks = generator._split_prose_into_chunks(
            prose, ["Elena Cruz"], SAMPLE_CHARACTERS,
        )
        dialogue_chunks = [c for c in chunks if c["speaker"] != "NARRATOR"]
        assert len(dialogue_chunks) == 2
        assert dialogue_chunks[0]["speaker"] == "char_001"
        assert dialogue_chunks[1]["speaker"] == "char_001"  # fallback to last

    def test_empty_prose(self, generator):
        """Empty prose produces empty list."""
        chunks = generator._split_prose_into_chunks("", [], [])
        assert chunks == []

    def test_escaped_quotes_in_dialogue(self, generator):
        """Escaped quotes inside dialogue don't break splitting."""
        prose = r'She said, "He told me \"run\" and I did."'
        chunks = generator._split_prose_into_chunks(
            prose, ["Elena Cruz"], SAMPLE_CHARACTERS,
        )
        # Should still split correctly
        assert any(c["speaker"] != "NARRATOR" for c in chunks)


# ---------------------------------------------------------------------------
# Hybrid generate_script tests
# ---------------------------------------------------------------------------

class TestGenerateScript:
    """Tests for the hybrid generate_script pipeline."""

    def test_splits_and_annotates(self, generator):
        """Prose is split rule-based and instructs come from LLM."""
        instruct_response = json.dumps([
            "Tense, deliberate narration.",
            "Firm, quiet authority, low controlled.",
            "Brief weighted pause in delivery.",
            "Strained, voice cracking under pressure.",
        ])
        generator.client.chat.completions.create.return_value = _make_mock_response(instruct_response)

        result = generator.generate_script(SAMPLE_SCENE, 1, 1, SAMPLE_CHARACTERS)

        # Should have multiple chunks (not a single fallback blob)
        assert len(result) >= 3
        # First chunk should be narrator
        assert result[0]["speaker"] == "NARRATOR"
        # Instructs should be from LLM, not default
        assert result[0]["instruct"] == "Tense, deliberate narration."

    def test_works_without_llm(self, generator):
        """If LLM fails, splitting still works with default instructs."""
        generator.client.chat.completions.create.side_effect = RuntimeError("Connection refused")

        result = generator.generate_script(SAMPLE_SCENE, 1, 1, SAMPLE_CHARACTERS)

        # Should still produce multi-chunk output (rule-based splitting works)
        assert len(result) >= 3
        # Default instructs remain
        assert result[0]["instruct"] == "Grounded, deliberate narration."

    def test_no_prose_uses_summary(self, generator):
        """Scene without prose returns summary as single narrator chunk."""
        scene = {**SAMPLE_SCENE, "prose": ""}
        result = generator.generate_script(scene, 1, 1, SAMPLE_CHARACTERS)
        assert len(result) == 1
        assert result[0]["speaker"] == "NARRATOR"
        assert "tense confrontation" in result[0]["text"]

    def test_instruct_mismatch_count_graceful(self, generator):
        """If LLM returns fewer instructs than chunks, extras keep defaults."""
        # Return only 2 instructs for a 4+ chunk scene
        instruct_response = json.dumps(["Custom instruct 1.", "Custom instruct 2."])
        generator.client.chat.completions.create.return_value = _make_mock_response(instruct_response)

        result = generator.generate_script(SAMPLE_SCENE, 1, 1, SAMPLE_CHARACTERS)
        assert len(result) >= 3
        # First two get custom instructs
        assert result[0]["instruct"] == "Custom instruct 1."
        assert result[1]["instruct"] == "Custom instruct 2."
        # Rest keep default
        assert result[2]["instruct"] == "Grounded, deliberate narration."


class TestFallbackScript:
    def test_with_prose(self, generator):
        result = generator._fallback_script(SAMPLE_SCENE)
        assert len(result) == 1
        assert result[0]["speaker"] == "NARRATOR"
        assert "Elena leaned forward" in result[0]["text"]

    def test_without_prose_uses_summary(self, generator):
        scene = {"scene_summary": "A tense confrontation."}
        result = generator._fallback_script(scene)
        assert "tense confrontation" in result[0]["text"]

    def test_no_prose_no_summary(self, generator):
        result = generator._fallback_script({})
        assert result[0]["text"] == "The scene continues."

    def test_always_narrator(self, generator):
        result = generator._fallback_script(SAMPLE_SCENE)
        assert result[0]["speaker"] == "NARRATOR"
        assert result[0]["instruct"] == "Grounded, deliberate narration."


class TestTitleScripts:
    def test_generate_title_script(self, generator):
        result = generator.generate_title_script("The Last Detective")
        assert len(result) == 1
        assert result[0]["speaker"] == "NARRATOR"
        assert result[0]["text"] == "The Last Detective"
        assert "gravitas" in result[0]["instruct"].lower()

    def test_generate_chapter_title_script(self, generator):
        result = generator.generate_chapter_title_script(3, "Into the Dark")
        assert len(result) == 1
        assert result[0]["text"] == "Chapter 3. Into the Dark"
        assert result[0]["speaker"] == "NARRATOR"

    def test_chapter_title_first_chapter(self, generator):
        result = generator.generate_chapter_title_script(1, "Beginning")
        assert result[0]["text"] == "Chapter 1. Beginning"


# ---------------------------------------------------------------------------
# Voice description generation tests
# ---------------------------------------------------------------------------

class TestGenerateVoiceDescriptions:
    """Tests for LLM-powered voice description generation."""

    def test_returns_voice_designs(self, generator):
        """LLM response is parsed into character_id -> description map."""
        llm_response = json.dumps({
            "NARRATOR": "male baritone, rich cinematic narrator, dynamic storytelling range",
            "char_001": "female alto, sharp commanding edge, clipped professional diction",
            "char_002": "male tenor, nervous tremor, halting speech",
        })
        generator.client.chat.completions.create.return_value = _make_mock_response(llm_response)

        result = generator.generate_voice_descriptions(SAMPLE_CHARACTERS)
        assert result["NARRATOR"] == "male baritone, rich cinematic narrator, dynamic storytelling range"
        assert result["char_001"] == "female alto, sharp commanding edge, clipped professional diction"
        assert result["char_002"] == "male tenor, nervous tremor, halting speech"

    def test_includes_narrator(self, generator):
        """Result always includes a NARRATOR entry."""
        llm_response = json.dumps({
            "NARRATOR": "male baritone, warm narration",
            "char_001": "female alto, steady",
        })
        generator.client.chat.completions.create.return_value = _make_mock_response(llm_response)

        result = generator.generate_voice_descriptions(SAMPLE_CHARACTERS)
        assert "NARRATOR" in result

    def test_strips_markdown_fences(self, generator):
        """Markdown code fences are stripped before JSON parsing."""
        llm_response = '```json\n{"NARRATOR": "male baritone, warm", "char_001": "female alto, sharp"}\n```'
        generator.client.chat.completions.create.return_value = _make_mock_response(llm_response)

        result = generator.generate_voice_descriptions(SAMPLE_CHARACTERS)
        assert "NARRATOR" in result

    def test_falls_back_on_llm_failure(self, generator):
        """LLM exception triggers rule-based fallback."""
        generator.client.chat.completions.create.side_effect = RuntimeError("API down")

        result = generator.generate_voice_descriptions(SAMPLE_CHARACTERS)
        # Should still produce results from fallback
        assert "NARRATOR" in result
        assert "char_001" in result
        assert "char_002" in result

    def test_falls_back_on_bad_json(self, generator):
        """Invalid JSON after retries triggers rule-based fallback."""
        generator.client.chat.completions.create.return_value = _make_mock_response("not json at all")

        result = generator.generate_voice_descriptions(SAMPLE_CHARACTERS, max_retries=0)
        assert "NARRATOR" in result
        assert "char_001" in result

    def test_empty_descriptions_rejected(self, generator):
        """All-empty descriptions trigger retry/fallback."""
        llm_response = json.dumps({"NARRATOR": "", "char_001": ""})
        generator.client.chat.completions.create.return_value = _make_mock_response(llm_response)

        result = generator.generate_voice_descriptions(SAMPLE_CHARACTERS, max_retries=0)
        # Fallback should produce non-empty descriptions
        assert result["NARRATOR"]
        assert result["char_001"]


class TestFallbackVoiceDescriptions:
    """Tests for rule-based fallback voice descriptions."""

    def test_always_includes_narrator(self, generator):
        result = generator._fallback_voice_descriptions([])
        assert "NARRATOR" in result
        assert "narrator" in result["NARRATOR"].lower()

    def test_maps_all_characters(self, generator):
        result = generator._fallback_voice_descriptions(SAMPLE_CHARACTERS)
        assert "char_001" in result
        assert "char_002" in result

    def test_female_gets_female_register(self, generator):
        result = generator._fallback_voice_descriptions(SAMPLE_CHARACTERS)
        assert "female" in result["char_001"].lower()

    def test_male_gets_male_register(self, generator):
        result = generator._fallback_voice_descriptions(SAMPLE_CHARACTERS)
        assert "male" in result["char_002"].lower()

    def test_register_variety(self, generator):
        """Multiple same-gender characters get different registers."""
        chars = [
            {"name": "A", "character_id": "c1", "gender": "male", "role": "protagonist"},
            {"name": "B", "character_id": "c2", "gender": "male", "role": "supporting"},
            {"name": "C", "character_id": "c3", "gender": "male", "role": "antagonist"},
        ]
        result = generator._fallback_voice_descriptions(chars)
        # Three males should get three different registers
        registers = [result["c1"].split(",")[0], result["c2"].split(",")[0], result["c3"].split(",")[0]]
        assert len(set(registers)) == 3

    def test_skips_chars_without_id(self, generator):
        chars = [{"name": "NoID", "gender": "male"}]
        result = generator._fallback_voice_descriptions(chars)
        assert len(result) == 1  # only NARRATOR
