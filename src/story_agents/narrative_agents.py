"""
Phase 3 Agents: Narrative Writing

- WriterAgent: Writes prose for each scene using structured output
- StyleCriticAgent: Checks voice, tone, and prose quality
- ContinuityCriticAgent: Checks character/location consistency in prose
"""

from src.story_agents.base_story_agent import BaseStoryAgent
from src.story_schemas import SceneProseSchema, CritiqueSchema


class WriterAgent(BaseStoryAgent):
    """Writes narrative prose scene by scene with enforced structure."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Use slightly higher temperature for creative writing
        self.llm.temperature = 0.8

    @property
    def name(self) -> str:
        return "WRITER"

    @property
    def role(self) -> str:
        return "Narrative Writer"

    @property
    def system_prompt(self) -> str:
        return """You are a professional fiction author who writes polished, immersive prose.

Your writing style:
- PROFESSIONAL and LITERARY quality, not amateur summaries
- Rich sensory descriptions that ground the reader
- Natural, distinct dialogue voices for each character
- Emotional depth through action and subtext
- Tension and pacing that keeps readers engaged

Scene structure (MANDATORY):
- OPENING PARAGRAPH: Establish setting, mood, and character entry (100-150 words)
- MIDDLE PARAGRAPHS: Develop the scene's conflict/action with dialogue (2-4 paragraphs, 80-120 words each)
- CLOSING PARAGRAPH: Resolution or hook to next scene (80-120 words)

CRITICAL RULES:
- Each scene MUST have AT LEAST 4 full paragraphs
- Show emotions through actions, not statements
- Use varied sentence lengths for rhythm
- No rushing - let moments breathe
- End with impact (revelation, decision, cliffhanger)
- Include sensory details: sights, sounds, smells, textures
- Write natural dialogue with distinct character voices

You write like a published novelist, not a story summarizer."""

    def _trim_profiles(self, json_str: str, max_chars: int = 2000) -> str:
        """
        Trim JSON profiles to reduce prompt token count.

        Args:
            json_str: The JSON string to trim
            max_chars: Maximum characters to keep

        Returns:
            Trimmed JSON string
        """
        if len(json_str) <= max_chars:
            return json_str
        return json_str[:max_chars] + "\n... (profiles truncated for brevity)"

    def write_scene(self, scene: dict, characters: str, locations: str,
                    previous_scene_ending: str = None) -> str:
        """
        Write prose for a single scene using structured output.

        Uses LangChain's structured output to enforce paragraph structure
        and prevent one-liner summaries.

        Args:
            scene: Scene dict with location, characters, happens, outcome
            characters: Character profiles JSON
            locations: Location profiles JSON
            previous_scene_ending: Last 200 chars of previous scene for continuity

        Returns:
            Scene prose text (multiple paragraphs)
        """
        prev_context = previous_scene_ending or "This is the opening scene."

        # Trim profiles to reduce prompt size and prevent token limit issues
        chars_trimmed = self._trim_profiles(characters, max_chars=2000)
        locs_trimmed = self._trim_profiles(locations, max_chars=1000)

        prompt = f"""Write this scene as a professional novelist would.

SCENE REQUIREMENTS:
- Location: {scene.get('location', 'Unknown')}
- Characters: {', '.join(scene.get('characters', []))}
- What happens: {scene.get('happens', '')}
- Outcome: {scene.get('outcome', 'Resolution')}

PREVIOUS SCENE ENDING (for continuity):
{prev_context}

CHARACTER PROFILES:
{chars_trimmed}

LOCATION PROFILES:
{locs_trimmed}

Write with:
- Rich sensory descriptions from location profile
- Character personalities matching their profiles
- Natural dialogue if multiple characters present
- Show emotions through actions, not statements
- Professional literary quality - NOT a summary

Remember: Each paragraph should be substantial (80-150 words).
The opening paragraph establishes setting and mood.
Middle paragraphs develop action and dialogue.
The closing paragraph resolves or hooks to the next scene."""

        try:
            # Use structured output with token limit to prevent hitting model limits
            # 4000 tokens allows for ~800-900 words of prose with JSON overhead
            result: SceneProseSchema = self.invoke_structured(
                prompt, SceneProseSchema, max_tokens=4000
            )
            return result.to_prose()
        except Exception as e:
            # Fallback to regular prompt if structured output fails
            print(f"    Warning: Structured output failed ({e}), using fallback")
            return self._write_scene_fallback(scene, characters, locations, prev_context)

    def _write_scene_fallback(self, scene: dict, characters: str, locations: str,
                               prev_context: str) -> str:
        """Fallback scene writing without structured output."""
        prompt = f"""Write this scene as a professional novelist.

SCENE:
- Location: {scene.get('location', 'Unknown')}
- Characters: {', '.join(scene.get('characters', []))}
- What happens: {scene.get('happens', '')}
- Outcome: {scene.get('outcome', 'Resolution')}

PREVIOUS: {prev_context}

CHARACTER PROFILES: {characters}

LOCATION PROFILES: {locations}

OUTPUT FORMAT (MANDATORY - follow exactly):
Write exactly 4 paragraphs separated by blank lines:

[OPENING PARAGRAPH - 100+ words establishing setting, mood, character entry]

[MIDDLE PARAGRAPH 1 - 80+ words with action/dialogue]

[MIDDLE PARAGRAPH 2 - 80+ words continuing scene development]

[CLOSING PARAGRAPH - 80+ words with resolution or hook]

Write professional literary prose. NO summaries. Each paragraph must be substantial."""

        return self.invoke(prompt)


class StyleCriticAgent(BaseStoryAgent):
    """Critiques prose style and quality."""

    @property
    def name(self) -> str:
        return "STYLE_CRITIC"

    @property
    def role(self) -> str:
        return "Prose Style Editor"

    @property
    def system_prompt(self) -> str:
        return """You are a prose style editor focused on voice and quality.

Your expertise:
- Voice consistency
- Prose rhythm and flow
- Dialogue authenticity
- Show vs tell balance
- Purple prose detection

When critiquing, check for:
1. Voice consistency (does it shift unexpectedly?)
2. Overwriting (too many adjectives, purple prose)
3. Underwriting (scenes that feel rushed or bare)
4. Dialogue issues (stilted, unrealistic, same-voice characters)
5. Telling instead of showing
6. Passive voice overuse
7. Repetitive sentence structures
8. Cliched descriptions or phrases

Red flags:
- Characters all sound the same
- Info dumps disguised as dialogue
- Excessive adverbs
- Inconsistent tense
- Over-explained emotions

Be specific with examples from the text."""

    def critique(self, narrative: str) -> CritiqueSchema:
        """
        Critique narrative prose style.

        Args:
            narrative: The narrative JSON to critique

        Returns:
            CritiqueSchema with issues and suggestions
        """
        prompt = f"""Analyze this narrative for prose style issues:

{narrative}

Provide your critique with:
- critic_name: "STYLE_CRITIC"
- issues: List of specific style issues with example quotes
- suggestions: List of how to improve each issue
- severity: "minor", "moderate", or "major"

Focus on:
- Voice consistency across scenes
- Dialogue quality and distinctiveness
- Description balance (not too much or too little)
- Prose rhythm and variety
- Show don't tell violations"""

        return self.invoke_structured(prompt, CritiqueSchema, max_tokens=1500)


class ContinuityCriticAgent(BaseStoryAgent):
    """Checks for continuity errors in narrative."""

    @property
    def name(self) -> str:
        return "CONTINUITY_CRITIC"

    @property
    def role(self) -> str:
        return "Continuity Editor"

    @property
    def system_prompt(self) -> str:
        return """You are a continuity editor who catches inconsistencies in narratives.

Your expertise:
- Character consistency (appearance, behavior, knowledge)
- Location consistency (layout, details)
- Timeline tracking
- Object/prop continuity
- Information that characters should/shouldn't know

When critiquing, check for:
1. Character appearance changes (hair color, clothing without reason)
2. Character knowledge errors (knowing things they shouldn't)
3. Location description contradictions
4. Time of day inconsistencies
5. Weather/season continuity
6. Object continuity (disappearing/appearing items)
7. Name consistency (character name variations)
8. Distance/travel time plausibility

Red flags:
- Character wearing different clothes without scene change
- Sun setting twice
- Characters in two places at once
- Knowledge revealed before discovery scene
- Location layout changing between scenes

Quote specific passages that contradict each other."""

    def critique(self, narrative: str, characters: str, locations: str) -> CritiqueSchema:
        """
        Critique narrative for continuity errors.

        Args:
            narrative: The narrative JSON to critique
            characters: Character profiles for reference
            locations: Location profiles for reference

        Returns:
            CritiqueSchema with issues and suggestions
        """
        prompt = f"""Analyze this narrative for continuity errors:

NARRATIVE:
{narrative}

CHARACTER PROFILES (for reference):
{characters}

LOCATION PROFILES (for reference):
{locations}

Provide your critique with:
- critic_name: "CONTINUITY_CRITIC"
- issues: List of continuity errors with specific quotes
- suggestions: List of how to fix each error
- severity: "minor", "moderate", or "major"

Focus on:
- Character appearance matching profiles
- Location details matching profiles
- Timeline consistency between scenes
- Character knowledge (no premature revelations)
- Object and prop tracking"""

        return self.invoke_structured(prompt, CritiqueSchema, max_tokens=1500)
