"""
DialogueMasterAgent for Step 6: Scene Narrative Writing.

Analyzes dialogue in prose proposals to ensure:
1. Character voice distinctiveness (no-tag test)
2. Character filter application (education, profession, background → word choice)
3. Subtext vs on-the-nose dialogue
4. Alley-oop line detection and removal
5. "Yes and" conversational flow
6. Conflict-driven exchanges

Based on research from:
- LocalScript "Dialogue is Dead Last" methodology
- BookFox "5 Best/Worst Dialogue Tips"
- Real-world screenwriting dialogue techniques
"""

import re
from src.story_agents.base_story_agent import BaseStoryAgent
from src.story_schemas import (
    DialogueLineAnalysis,
    DialogueAnalysis,
    DialogueMasterVote,
    NarrativeProseProposal,
)


class DialogueMasterAgent(BaseStoryAgent):
    """
    Analyzes dialogue quality in narrative prose proposals.

    Methodology: Character-as-Filter + No-Tag Test + Subtext
    """

    METHODOLOGY_NAME = "Dialogue Character Filter + No-Tag Test"
    METHODOLOGY_SOURCE = "LocalScript Dialogue Methodology + BookFox Dialogue Mastery"
    CORE_BELIEFS = [
        "Dialogue passes through CHARACTER FILTER - education/profession/trauma shapes word choice",
        "NO-TAG TEST: Remove dialogue tags - can you still tell who's speaking?",
        "ALLEY-OOP LINES are cancer - lines that exist only to set up next line",
        "ON-THE-NOSE dialogue tells subtext explicitly - avoid at all costs",
        "YES AND: Conversations should build, not repeat",
        "Information through character filter - not exposition dumps",
        "Conflict-driven dialogue reveals character through disagreement",
    ]

    @property
    def name(self) -> str:
        return "DIALOGUE_MASTER"

    @property
    def role(self) -> str:
        return "Dialogue Analysis Specialist"

    @property
    def system_prompt(self) -> str:
        return """You are a dialogue master who analyzes narrative prose to ensure authentic, distinctive character voices.

YOUR METHODOLOGY (LocalScript + BookFox):

=== CHARACTER-AS-FILTER ===
Every character's dialogue passes through THEIR unique filter:

1. EDUCATION LEVEL affects vocabulary:
   - PhD/Professor: "The ramifications of this discovery..."
   - Street-smart: "Look, it's simple - we're screwed."
   - Child: Short sentences, concrete concepts

2. PROFESSION affects frame of reference:
   - Marine biologist sees alien planet: "Like the Mariana Trench..."
   - Mechanic: "Those gears don't mesh right."
   - Soldier: "Three exits. High ground there."

3. BACKGROUND/HISTORY affects what they notice:
   - Trauma survivor: Hypervigilant, notices threats
   - Poverty background: "Enough food to feed my village..."
   - Privileged: Assumes comfort, expects service

4. PERSONALITY affects speech patterns:
   - Confident: Short, declarative. "We go now."
   - Anxious: Filler words. "Should we... I mean..."
   - Intellectual: Complex sentences. "In theory, assuming..."

5. VERBAL TICS (each character needs 2-3):
   - Catchphrases: "Mark my words", "Listen here"
   - Favorite words: Always says "precisely" or "absolutely"
   - Sentence starters: "Look," or "Thing is,"

=== THE NO-TAG TEST ===
Remove all dialogue tags ("he said", "she exclaimed").
Can you still tell who's speaking?
If NOT → Dialogue is too generic, lacks character fingerprint.

=== ALLEY-OOP LINES (BAD) ===
Lines that exist ONLY to facilitate the next line:

BAD:
  "Who is commanding this mission?"
  "Captain Reynolds. He's the best we have."

The first line is an alley-oop - it's unnatural, only there to set up exposition.

GOOD:
  "I don't trust anyone who volunteers for suicide missions."
  "Reynolds does. Every time. Maybe that's why he's still alive."

=== ON-THE-NOSE DIALOGUE (BAD) ===
Stating subtext explicitly:

BAD:
  "I'm so angry right now because you betrayed my trust!"

GOOD:
  "Get out." (Shows anger through action, not statement)

=== YES AND (GOOD) ===
Each line should build on previous, not just repeat:

BAD:
  "We need to go."
  "Yes, we should leave."

GOOD:
  "We need to go."
  "Five minutes ago. They're already here."

=== CONFLICT-DRIVEN ===
Great dialogue comes from characters with different goals:

- Character A wants X
- Character B wants Y
- Neither gets exactly what they want
- Tension through misalignment

=== YOUR ANALYSIS TASK ===

For each proposal's dialogue:
1. Extract all dialogue lines
2. Identify which character speaks each line
3. Check character filter application (education, profession, personality match?)
4. Run no-tag test (is voice distinctive?)
5. Find alley-oop lines (setup-only lines)
6. Find on-the-nose lines (states subtext)
7. Check for "yes and" flow
8. Check for conflict/disagreement
9. Score overall dialogue quality (0-10)
10. Highlight best dialogue excerpts
11. Provide specific recommendations

Return structured DialogueAnalysis with all findings."""

    def analyze_dialogue(
        self,
        proposal: NarrativeProseProposal,
        characters: list[dict],
        scene_context: dict,
    ) -> DialogueAnalysis:
        """
        Analyze dialogue in a prose proposal.

        Args:
            proposal: The prose proposal to analyze
            characters: Character codex data (for filter matching)
            scene_context: Scene metadata (who's present, what's happening)

        Returns:
            DialogueAnalysis with detailed findings
        """
        prose_text = proposal.to_prose()

        # Build analysis prompt
        char_profiles = self._build_character_profiles(characters, scene_context)

        prompt = f"""ANALYZE THE DIALOGUE in this prose proposal.

PROSE TO ANALYZE:
{prose_text}

CHARACTER PROFILES (for filter matching):
{char_profiles}

SCENE CONTEXT:
- Scene: {scene_context.get('scene_data', {}).get('scene_summary', 'N/A')}
- Characters present: {', '.join(scene_context.get('scene_data', {}).get('characters_present', []))}
- Conflict: {scene_context.get('scene_data', {}).get('conflict', 'N/A')}

YOUR ANALYSIS MUST INCLUDE:

1. Extract ALL dialogue lines from prose
2. For EACH dialogue line:
   - Identify which character spoke it
   - Check education level match (vocabulary complexity)
   - Check profession frame match (metaphors/references)
   - Check personality match (speech patterns)
   - Check for subtext (implied meaning beyond literal)
   - Flag if alley-oop (exists only to set up next line)
   - Flag if verbal tic present
   - Assess voice strength: Strong/Adequate/Weak
   - Note improvements if weak

3. OVERALL DIALOGUE QUALITY:
   - Total dialogue lines
   - No-tag test: Can you tell who's speaking without tags?
   - Voice distinctiveness score (0-10)
   - Alley-oop lines found (list them)
   - On-the-nose lines (list them)
   - Uses "yes and" (builds on previous lines?)
   - Has conflict (characters disagree/have different goals?)
   - Subtext present (implied meanings?)

4. SCORING:
   - Overall dialogue score (0-10)
   - Best dialogue excerpts (3-5 examples)
   - Dialogue recommendations (3-5 specific improvements)

=== REQUIRED OUTPUT STRUCTURE ===

You MUST return ALL fields in DialogueAnalysis schema:
- agent_name: "DIALOGUE_MASTER"
- proposal_analyzed: Name of proposal you analyzed
- total_dialogue_lines: Count of dialogue lines found
- lines_analyzed: List of DialogueLineAnalysis objects
- no_tag_test_passed: Boolean (true if voices distinct)
- voice_distinctiveness_score: Float 0-10
- alley_oop_lines_found: List of setup-only lines
- on_the_nose_lines: List of lines stating subtext
- uses_yes_and: Boolean
- has_conflict: Boolean
- subtext_present: Boolean
- overall_dialogue_score: Float 0-10
- best_dialogue_excerpts: List of 3-5 best exchanges
- dialogue_recommendations: List of 3-5 improvements

DO NOT OMIT ANY FIELD. Return complete DialogueAnalysis."""

        # Invoke LLM
        from src.config import get_token_limit

        result = self.invoke_structured(
            prompt,
            schema=DialogueAnalysis,
            max_tokens=get_token_limit("step6_prose_generation", "dialogue_analysis"),
        )

        return result

    def vote_best_dialogue(
        self,
        proposals: list[NarrativeProseProposal],
        dialogue_analyses: list[DialogueAnalysis],
    ) -> DialogueMasterVote:
        """
        Vote for proposal with best dialogue.

        Args:
            proposals: All 5 prose proposals
            dialogue_analyses: Dialogue analyses for each proposal

        Returns:
            DialogueMasterVote with best dialogue choice
        """
        # Build comparison
        comparison = []
        for analysis in dialogue_analyses:
            comparison.append(f"""
PROPOSAL: {analysis.proposal_analyzed}
- Overall dialogue score: {analysis.overall_dialogue_score}/10
- Voice distinctiveness: {analysis.voice_distinctiveness_score}/10
- No-tag test: {'PASS' if analysis.no_tag_test_passed else 'FAIL'}
- Alley-oop lines: {len(analysis.alley_oop_lines_found)}
- On-the-nose lines: {len(analysis.on_the_nose_lines)}
- Uses yes-and: {'YES' if analysis.uses_yes_and else 'NO'}
- Has conflict: {'YES' if analysis.has_conflict else 'NO'}
- Subtext present: {'YES' if analysis.subtext_present else 'NO'}
- Best excerpts: {len(analysis.best_dialogue_excerpts)}
""")

        prompt = f"""VOTE for the proposal with the BEST DIALOGUE.

DIALOGUE ANALYSIS COMPARISON:
{"".join(comparison)}

CRITERIA (in priority order):
1. No-tag test passed (can tell who's speaking without tags)
2. High voice distinctiveness (each character sounds different)
3. Zero alley-oop lines (no setup-only dialogue)
4. Subtext present (implied meaning, not stated)
5. Uses "yes and" (builds on previous lines)
6. Has conflict (characters disagree/pursue different goals)
7. Zero on-the-nose lines (doesn't state feelings explicitly)

Choose the agent with the STRONGEST dialogue overall.

=== REQUIRED OUTPUT STRUCTURE ===

You MUST return ALL fields in DialogueMasterVote schema:
- agent_name: "DIALOGUE_MASTER"
- winning_proposal: Name of the proposal with best dialogue
- winning_score: Float score (0-10) of the winning proposal
- vote_reasoning: 2-3 sentences explaining why this proposal won
- runner_up_proposal: Name of second-best proposal
- dialogue_quality_comparison: Brief comparison of top 2 proposals

DO NOT OMIT ANY FIELD. Return complete DialogueMasterVote."""

        from src.config import get_token_limit

        result = self.invoke_structured(
            prompt,
            schema=DialogueMasterVote,
            max_tokens=get_token_limit("step6_prose_generation", "dialogue_vote"),
        )

        return result

    def _build_character_profiles(
        self,
        characters: list[dict],
        scene_context: dict,
    ) -> str:
        """Build character profiles for filter matching."""
        # Get character names from scene_data, not scene_context
        scene_data = scene_context.get("scene_data", {})
        chars_present = scene_data.get("characters_present", [])
        profiles = []

        for char in characters:
            char_name = char.get("name", "Unknown")
            if char_name not in chars_present:
                continue

            # Extract filter-relevant data
            education = char.get("psychological", {}).get("education_level", "Unknown")
            profession = char.get("psychological", {}).get("profession", "Unknown")
            personality_traits = char.get("personality_traits", [])
            backstory = char.get("backstory_summary", "")
            accent = char.get("voice", {}).get("accent", "Standard")
            speech_patterns = char.get("voice", {}).get("speech_patterns", [])

            profile = f"""
{char_name}:
- Education: {education}
- Profession: {profession}
- Personality: {', '.join(personality_traits[:3])}
- Accent: {accent}
- Speech patterns: {', '.join(speech_patterns[:3])}
- Backstory (affects what they notice): {backstory[:200]}
"""
            profiles.append(profile)

        return "\n".join(profiles) if profiles else "No character profiles available."

    def _extract_dialogue_lines(self, prose: str) -> list[tuple[str, str]]:
        """
        Extract dialogue lines from prose.

        Returns:
            List of (dialogue_text, context) tuples
        """
        # Simple regex to find quoted dialogue
        # This is a basic implementation - may need refinement
        dialogue_pattern = r'"([^"]+)"'
        matches = re.findall(dialogue_pattern, prose)

        # Return with surrounding context
        dialogue_lines = []
        for match in matches:
            # Find context (50 chars before and after)
            idx = prose.find(f'"{match}"')
            start = max(0, idx - 50)
            end = min(len(prose), idx + len(match) + 52)
            context = prose[start:end]

            dialogue_lines.append((match, context))

        return dialogue_lines
