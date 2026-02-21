"""
Unit tests for _format_chapters helper function.

This function does ONE thing: Format chapter outline → readable text for LLM prompts.
No LLM calls, pure logic, easy to test.
"""

import pytest
from src.story_agents.interconnection_agents import _format_chapters


class TestFormatChaptersBasic:
    """Test basic formatting functionality"""

    def test_format_single_chapter_single_scene(self):
        """Single chapter with one scene should format correctly"""
        chapter_outline = {
            'chapters': [{
                'chapter_number': 1,
                'chapter_title': 'The Beginning',
                'scenes': [{
                    'scene_number': 1,
                    'beat_name': 'Opening Image',
                    'scene_summary': 'Hero wakes up in a quiet village',
                    'pov_character': 'Hero'
                }]
            }]
        }

        result = _format_chapters(chapter_outline)

        assert '**CHAPTER 1: The Beginning**' in result
        assert 'Scene 1: Opening Image' in result
        assert 'Hero wakes up in a quiet village' in result
        assert 'POV: Hero' in result

    def test_format_multiple_chapters(self):
        """Multiple chapters should all be included"""
        chapter_outline = {
            'chapters': [
                {
                    'chapter_number': 1,
                    'chapter_title': 'Start',
                    'scenes': [{
                        'scene_number': 1,
                        'beat_name': 'Opening',
                        'scene_summary': 'Scene 1 summary',
                        'pov_character': 'Hero'
                    }]
                },
                {
                    'chapter_number': 2,
                    'chapter_title': 'Middle',
                    'scenes': [{
                        'scene_number': 2,
                        'beat_name': 'Catalyst',
                        'scene_summary': 'Scene 2 summary',
                        'pov_character': 'Mentor'
                    }]
                }
            ]
        }

        result = _format_chapters(chapter_outline)

        assert '**CHAPTER 1: Start**' in result
        assert '**CHAPTER 2: Middle**' in result
        assert 'Scene 1: Opening' in result
        assert 'Scene 2: Catalyst' in result


class TestFormatChaptersTruncation:
    """Test max_scenes truncation feature"""

    def test_truncation_at_max_scenes(self):
        """Should truncate when scene count exceeds max_scenes"""
        # Create outline with 5 scenes
        scenes = [
            {
                'scene_number': i+1,
                'beat_name': f'Beat {i+1}',
                'scene_summary': f'Summary {i+1}',
                'pov_character': 'Hero'
            }
            for i in range(5)
        ]

        chapter_outline = {
            'chapters': [{
                'chapter_number': 1,
                'chapter_title': 'Chapter',
                'scenes': scenes
            }]
        }

        # Truncate at 3 scenes
        result = _format_chapters(chapter_outline, max_scenes=3)

        assert 'Scene 1: Beat 1' in result
        assert 'Scene 2: Beat 2' in result
        assert 'Scene 3: Beat 3' in result
        assert 'Scene 4: Beat 4' not in result
        assert 'Scene 5: Beat 5' not in result
        assert '(remaining scenes truncated for brevity)' in result

    def test_no_truncation_under_limit(self):
        """Should not truncate when under max_scenes"""
        scenes = [
            {
                'scene_number': i+1,
                'beat_name': f'Beat {i+1}',
                'scene_summary': f'Summary {i+1}',
                'pov_character': 'Hero'
            }
            for i in range(3)
        ]

        chapter_outline = {
            'chapters': [{
                'chapter_number': 1,
                'chapter_title': 'Chapter',
                'scenes': scenes
            }]
        }

        result = _format_chapters(chapter_outline, max_scenes=10)

        assert 'Scene 1: Beat 1' in result
        assert 'Scene 2: Beat 2' in result
        assert 'Scene 3: Beat 3' in result
        assert 'truncated' not in result


class TestFormatChaptersEdgeCases:
    """Test edge cases and missing data"""

    def test_empty_chapters_list(self):
        """Empty chapters list should return empty string"""
        chapter_outline = {'chapters': []}

        result = _format_chapters(chapter_outline)

        assert result == ""

    def test_missing_chapters_key(self):
        """Missing 'chapters' key should return empty string"""
        chapter_outline = {}

        result = _format_chapters(chapter_outline)

        assert result == ""

    def test_chapter_with_no_scenes(self):
        """Chapter with empty scenes list should show chapter header only"""
        chapter_outline = {
            'chapters': [{
                'chapter_number': 1,
                'chapter_title': 'Empty Chapter',
                'scenes': []
            }]
        }

        result = _format_chapters(chapter_outline)

        assert '**CHAPTER 1: Empty Chapter**' in result
        assert 'Scene' not in result

    def test_missing_optional_fields(self):
        """Missing optional fields should show 'Unknown' or default values"""
        chapter_outline = {
            'chapters': [{
                'chapter_number': 1,
                # Missing chapter_title
                'scenes': [{
                    'scene_number': 1,
                    # Missing beat_name, summary, pov
                }]
            }]
        }

        result = _format_chapters(chapter_outline)

        assert '**CHAPTER 1: Untitled**' in result  # Default title
        assert 'Scene 1: Unknown' in result  # Default beat_name
        assert 'No summary' in result  # Default summary
        assert 'POV: Unknown' in result  # Default pov

    def test_very_long_summary_truncation(self):
        """Summaries should be truncated to 150 characters"""
        long_summary = 'A' * 200  # 200 character summary

        chapter_outline = {
            'chapters': [{
                'chapter_number': 1,
                'chapter_title': 'Chapter',
                'scenes': [{
                    'scene_number': 1,
                    'beat_name': 'Beat',
                    'scene_summary': long_summary,
                    'pov_character': 'Hero'
                }]
            }]
        }

        result = _format_chapters(chapter_outline)

        # Should contain truncated version (150 chars)
        assert long_summary[:150] in result
        # Should NOT contain full 200 chars
        assert long_summary not in result

    def test_unicode_characters_in_content(self):
        """Should handle unicode characters correctly"""
        chapter_outline = {
            'chapters': [{
                'chapter_number': 1,
                'chapter_title': 'Çhåptér Ωné 中文',
                'scenes': [{
                    'scene_number': 1,
                    'beat_name': 'Bëät 日本語',
                    'scene_summary': 'Sümmary with émojis 🎭🌟',
                    'pov_character': 'Hérø'
                }]
            }]
        }

        result = _format_chapters(chapter_outline)

        assert 'Çhåptér Ωné 中文' in result
        assert 'Bëät 日本語' in result
        assert 'Sümmary with émojis 🎭🌟' in result
        assert 'Hérø' in result


class TestFormatChaptersRealWorld:
    """Test with realistic story structures"""

    def test_realistic_story_structure(self):
        """Test with a realistic 3-chapter, 6-scene story"""
        chapter_outline = {
            'chapters': [
                {
                    'chapter_number': 1,
                    'chapter_title': 'The Call',
                    'scenes': [
                        {
                            'scene_number': 1,
                            'beat_name': 'Opening Image',
                            'scene_summary': 'Hero lives mundane life in village',
                            'pov_character': 'Caelum'
                        },
                        {
                            'scene_number': 2,
                            'beat_name': 'Catalyst',
                            'scene_summary': 'Mysterious stranger arrives with offer',
                            'pov_character': 'Caelum'
                        }
                    ]
                },
                {
                    'chapter_number': 2,
                    'chapter_title': 'The Journey',
                    'scenes': [
                        {
                            'scene_number': 3,
                            'beat_name': 'Debate',
                            'scene_summary': 'Hero debates whether to accept call',
                            'pov_character': 'Caelum'
                        },
                        {
                            'scene_number': 4,
                            'beat_name': 'Break into Two',
                            'scene_summary': 'Hero leaves village, journey begins',
                            'pov_character': 'Caelum'
                        }
                    ]
                },
                {
                    'chapter_number': 3,
                    'chapter_title': 'The Return',
                    'scenes': [
                        {
                            'scene_number': 5,
                            'beat_name': 'Midpoint',
                            'scene_summary': 'Hero discovers true cost of quest',
                            'pov_character': 'Caelum'
                        },
                        {
                            'scene_number': 6,
                            'beat_name': 'Final Image',
                            'scene_summary': 'Hero returns transformed',
                            'pov_character': 'Caelum'
                        }
                    ]
                }
            ]
        }

        result = _format_chapters(chapter_outline)

        # Check all chapters present
        assert '**CHAPTER 1: The Call**' in result
        assert '**CHAPTER 2: The Journey**' in result
        assert '**CHAPTER 3: The Return**' in result

        # Check all scenes present
        for i in range(1, 7):
            assert f'Scene {i}:' in result

        # Check key content
        assert 'Opening Image' in result
        assert 'Catalyst' in result
        assert 'Final Image' in result
        assert 'Caelum' in result
