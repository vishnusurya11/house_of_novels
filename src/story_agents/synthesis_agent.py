"""
SynthesisAgent for Step 6: Scene Narrative Writing.

Replaces winner-takes-all voting with intelligent synthesis that:
1. Analyzes all 5 prose proposals + cross-critiques
2. Scores each proposal on 5 dimensions (dialogue, sensory, character, world, pacing)
3. Blends best elements from multiple proposals
4. Creates unified 1500-2000 word scene
5. Tracks sensory selection and active/passive voice ratio
6. Applies critique insights during synthesis (not after)

Philosophy: "Synthesis over Selection"
- Don't discard 80% of work - blend best of all
- Each agent excels at their specialty - use ALL strengths
- Create consistent narrative voice through synthesis logic
"""

import random
from src.story_agents.base_story_agent import BaseStoryAgent
from src.story_schemas import (
    NarrativeProseProposal,
    NarrativeProseCritique,
    DialogueAnalysis,
    DialogueMasterVote,
    NarrativeProseSynthesis,
    ProposalElementScore,
    SensorySelectionMetadata,
    VoiceRatioReport,
)


class SynthesisAgent(BaseStoryAgent):
    """
    Synthesizes best elements from multiple prose proposals into unified scene.

    Methodology: Element-Based Synthesis + Voice Consistency
    """

    METHODOLOGY_NAME = "Prose Synthesis from Multi-Agent Proposals"
    METHODOLOGY_SOURCE = "Custom - Blend Best Elements Architecture"
    CORE_BELIEFS = [
        "SYNTHESIS over SELECTION - don't discard 80% of work",
        "Each agent excels at their specialty - use ALL strengths",
        "Best dialogue + best sensory + best character = best scene",
        "Target 1500-2000 words for professional depth",
        "Active voice 80%, passive 20% (strategic use)",
        "Randomize sensory focus (avoid repetitive patterns)",
        "Apply critiques DURING synthesis, not after",
    ]

    @property
    def name(self) -> str:
        return "SYNTHESIS"

    @property
    def role(self) -> str:
        return "Prose Synthesis Specialist"

    @property
    def system_prompt(self) -> str:
        return """You are a prose synthesis master who blends the best elements from multiple narrative proposals.

YOUR METHODOLOGY:

=== SYNTHESIS PHILOSOPHY ===
You receive 5 narrative proposals from specialized agents:
1. CHARACTER_CONTINUITY - Character psychology, GMC
2. LOCATION_ATMOSPHERE - Sensory immersion, atmosphere
3. WORLD_BUILDING - Cultural details, world integration
4. PLOT_TICKING_CLOCK - Urgency, pacing, plot advancement
5. NARRATIVE_CONTINUITY - Prose craft, scene connections

Each agent excels at their specialty. Your job:
→ Don't pick ONE winner and discard the rest
→ BLEND the best elements from ALL proposals
→ Create unified scene with consistent voice

=== ELEMENT-BASED SCORING ===

Score each proposal on 5 dimensions (0-10):

1. DIALOGUE quality
   - Character voice distinctiveness
   - No alley-oop lines
   - Subtext present
   - "Yes and" flow

2. SENSORY DETAIL quality
   - Variety (not just sight)
   - Character-based perception
   - Concrete, specific details
   - Immersive, not overwhelming

3. CHARACTER INTERIORITY quality
   - Deep POV (no filter words)
   - Emotional vulnerability
   - Backstory woven naturally
   - Motivation clear

4. WORLD BUILDING quality
   - Shown through action (not exposition)
   - Cultural details embedded
   - World rules integrated
   - Natural, not info-dump

5. PACING quality
   - Micro-tension present
   - Ticking clock visible
   - Scene goal → conflict → disaster
   - Reader pulled forward

=== SYNTHESIS STRATEGY ===

Step 1: Choose structural base
- Pick the proposal with best PACING as foundation
- Use its scene structure (goal → conflict → outcome)

Step 2: Inject best elements
- Replace/enhance dialogue with best dialogue agent's lines
- Replace/enhance sensory details with best sensory agent's descriptions
- Preserve best character interiority moments
- Keep best world integration beats

Step 3: Unified voice
- Blend prose style to feel like ONE writer
- Match sentence rhythm throughout
- Consistent paragraph structure
- Smooth transitions between borrowed elements

Step 4: Metadata tracking
- Track which agent contributed which element
- Record sensory selection (1-2 primary senses)
- Calculate active/passive voice ratio (target 80/20)

=== SENSORY RANDOMIZATION ===

To avoid repetitive sensory patterns:
1. Review last 3 scenes' primary senses
2. Randomly select 1-2 NEW senses to emphasize
3. Use character profession/personality to guide selection
   - Marine biologist → smell, touch (algae, salt)
   - Mechanic → sound, touch (gears, oil)
   - Soldier → sight, sound (threats, positioning)

Available senses: sight, sound, smell, taste, touch

=== ACTIVE/PASSIVE VOICE ===

Target: 80% active, 20% passive

ACTIVE (preferred):
"She opened the door."

PASSIVE (strategic use):
"The door was opened." (when actor unknown/de-emphasized)

Track ratio, report in VoiceRatioReport.

=== OUTPUT STRUCTURE ===

Your synthesized prose must be 1500-2000 words, structured as:

1. Opening paragraph (100-200 words)
   - Ground reader immediately
   - Sensory + character state
   - Scene goal established

2. Middle paragraphs (1200-1600 words, 3-10 paragraphs)
   - Goal → Conflict → Complications
   - Character interiority woven throughout
   - Dialogue exchanges (if applicable)
   - World details embedded in action

3. Closing paragraph (100-200 words)
   - Scene outcome (disaster or resolution)
   - Emotional resonance or hook
   - Connection to next scene

Return NarrativeProseSynthesis with:
- All element scores
- Synthesis strategy (which agent for which element)
- Sensory selection metadata
- Voice ratio report
- Full prose (opening + middle + closing)
- Self-assessed synthesis score (0-10)
"""

    def synthesize_prose(
        self,
        proposals: list[NarrativeProseProposal],
        critiques: list[list[NarrativeProseCritique]],
        dialogue_analysis: DialogueAnalysis,
        dialogue_vote: DialogueMasterVote,
        characters: list[dict],
        scene_context: dict,
        previous_scenes_senses: list[list[str]] = None,
    ) -> NarrativeProseSynthesis:
        """
        Synthesize best elements from all proposals into unified scene.

        Args:
            proposals: All 5 prose proposals
            critiques: Cross-critiques (5x5 matrix)
            dialogue_analysis: DialogueMasterAgent's analysis
            dialogue_vote: Best dialogue vote
            characters: Character codex data
            scene_context: Scene metadata
            previous_scenes_senses: Last 3 scenes' primary senses (for variety)

        Returns:
            NarrativeProseSynthesis with blended prose + metadata
        """
        if previous_scenes_senses is None:
            previous_scenes_senses = []

        # Build synthesis prompt
        proposals_text = self._format_proposals(proposals)
        critiques_text = self._format_critiques(critiques)
        dialogue_text = self._format_dialogue_analysis(dialogue_analysis, dialogue_vote)
        char_context = self._build_character_context(characters, scene_context)
        sensory_guidance = self._build_sensory_guidance(previous_scenes_senses, characters, scene_context)

        prompt = f"""SYNTHESIZE the best elements from all 5 proposals into ONE unified scene (1500-2000 words).

=== ALL PROPOSALS ===
{proposals_text}

=== CROSS-CRITIQUES ===
{critiques_text}

=== DIALOGUE ANALYSIS ===
{dialogue_text}

=== CHARACTER CONTEXT ===
{char_context}

=== SENSORY GUIDANCE ===
{sensory_guidance}

=== SCENE CONTEXT ===
Scene: {scene_context.get('scene_summary', 'N/A')}
Characters present: {', '.join(scene_context.get('characters', []))}
Location: {scene_context.get('location', 'N/A')}
Goal: {scene_context.get('goal', 'N/A')}
Conflict: {scene_context.get('conflict', 'N/A')}
Disaster/Resolution: {scene_context.get('disaster_or_resolution', 'N/A')}
Ticking Clock: {scene_context.get('ticking_clock', 'N/A')}

=== YOUR SYNTHESIS TASK ===

Step 1: SCORE EACH PROPOSAL on 5 dimensions (0-10):
   - Dialogue quality
   - Sensory detail quality
   - Character interiority quality
   - World building quality
   - Pacing quality

For each dimension, extract 2-3 best excerpts as examples.

Step 2: CHOOSE SYNTHESIS STRATEGY:
   - Structural base: Which proposal has best pacing/structure?
   - Best dialogue: Use dialogue from which proposal?
   - Best sensory: Use sensory details from which proposal?
   - Best character work: Use interiority from which proposal?
   - Best world integration: Use world details from which proposal?

Step 3: SELECT SENSORY FOCUS:
   - Review previous scenes' senses to avoid repetition
   - Select 1-2 senses to emphasize THIS scene
   - Justify selection based on character/moment

Step 4: SYNTHESIZE PROSE (1500-2000 words):
   - Use structural base from best pacing proposal
   - Inject best dialogue from dialogue vote winner
   - Replace/enhance sensory details from best sensory proposal
   - Preserve best character interiority moments
   - Keep best world integration beats
   - UNIFY voice so it reads like one writer
   - Ensure smooth transitions between borrowed elements

Step 5: TRACK VOICE RATIO:
   - Count total sentences
   - Count active voice vs passive voice
   - Aim for 80% active, 20% passive
   - Note 2-3 example passive sentences

Step 6: SELF-ASSESS:
   - Synthesis score (0-10)
   - Why this synthesis works (3-5 sentences)
   - Techniques integrated

=== REQUIRED OUTPUT STRUCTURE ===

You MUST return ALL fields in NarrativeProseSynthesis schema:
- agent_name: "SYNTHESIS"
- proposals_analyzed: List of all 5 proposal agent names
- dialogue_analysis: The DialogueAnalysis object provided above
- element_scores: List of ProposalElementScore objects (one per proposal)
  Each ProposalElementScore contains:
  - proposal_name: Agent name
  - dialogue_score: Float 0-10
  - sensory_score: Float 0-10
  - character_score: Float 0-10
  - world_building_score: Float 0-10
  - pacing_score: Float 0-10
  - best_excerpts: List of 2-3 example quotes
- synthesis_strategy: String explaining which agent for which element
- sensory_selection: SensorySelectionMetadata object with:
  - primary_senses: List of 1-2 senses chosen
  - character_perception_filter: How POV character's profession guides perception
  - previous_scenes_senses: The previous_scenes_senses list provided
  - selection_reasoning: Why these senses work for this scene
- voice_ratio: VoiceRatioReport object with:
  - total_sentences: Integer count
  - active_voice_count: Integer count
  - passive_voice_count: Integer count
  - active_percentage: Float percentage
  - passive_examples: List of 2-3 example passive sentences
  - assessment: String assessment (Excellent/Good/Needs Improvement)
- opening_paragraph: String (100-200 words)
- middle_paragraphs: List of strings (3-10 paragraphs, 1200-1600 total words)
- closing_paragraph: String (100-200 words)
- word_count: Integer total word count
- synthesis_score: Float 0-10 (self-assessment)
- synthesis_reasoning: String (3-5 sentences explaining why this synthesis works)
- techniques_integrated: List of string technique names from all proposals

DO NOT OMIT ANY FIELD. Return complete NarrativeProseSynthesis."""

        from src.config import get_token_limit

        result = self.invoke_structured(
            prompt,
            schema=NarrativeProseSynthesis,
            max_tokens=get_token_limit("step6_prose_generation", "prose_synthesis"),
        )

        return result

    def _format_proposals(self, proposals: list[NarrativeProseProposal]) -> str:
        """Format all proposals for comparison."""
        formatted = []
        for prop in proposals:
            formatted.append(f"""
{'='*60}
PROPOSAL: {prop.agent_name}
{'='*60}
{prop.to_prose()}

Techniques used: {', '.join(prop.techniques_used)}
Word count: {prop.word_count}
""")
        return "\n".join(formatted)

    def _format_critiques(self, critiques: list[list[NarrativeProseCritique]]) -> str:
        """Format cross-critiques for synthesis insight."""
        formatted = []
        for critique_round in critiques:
            for crit in critique_round:
                # strengths and weaknesses are strings, not lists
                formatted.append(f"""
{crit.critic_agent} critiques {crit.target_agent}:
Strengths: {crit.strengths}
Weaknesses: {crit.weaknesses}
""")
        return "\n".join(formatted)

    def _format_dialogue_analysis(
        self,
        dialogue_analysis: DialogueAnalysis,
        dialogue_vote: DialogueMasterVote,
    ) -> str:
        """Format dialogue analysis for synthesis."""
        # Defensive type handling: dialogue_recommendations can be list[str] or list[dict]
        recommendations = dialogue_analysis.dialogue_recommendations[:3]
        rec_strs = []
        for rec in recommendations:
            if isinstance(rec, dict):
                # If LLM returned dict, extract text from common keys
                rec_strs.append(rec.get('text', rec.get('recommendation', str(rec))))
            else:
                rec_strs.append(str(rec))
        recommendations_text = '; '.join(rec_strs) if rec_strs else 'None'

        return f"""
BEST DIALOGUE: {dialogue_vote.best_dialogue_agent} (Score: {dialogue_vote.dialogue_score}/10)
Reasoning: {dialogue_vote.reasoning}

Analysis of {dialogue_analysis.proposal_analyzed}:
- Dialogue score: {dialogue_analysis.overall_dialogue_score}/10
- Voice distinctiveness: {dialogue_analysis.voice_distinctiveness_score}/10
- No-tag test: {'PASS' if dialogue_analysis.no_tag_test_passed else 'FAIL'}
- Best excerpts: {len(dialogue_analysis.best_dialogue_excerpts)}
- Recommendations: {recommendations_text}
"""

    def _build_character_context(
        self,
        characters: list[dict],
        scene_context: dict,
    ) -> str:
        """Build character context for synthesis."""
        chars_present = scene_context.get("characters", [])
        context = []

        for char in characters:
            char_name = char.get("name", "Unknown")
            if char_name not in chars_present:
                continue

            # Defensive: personality_traits is list[str], but handle edge cases
            personality = char.get('personality_traits', [])
            if isinstance(personality, list):
                personality_str = ', '.join(str(p) for p in personality[:3])
            else:
                personality_str = str(personality)

            context.append(f"""
{char_name}:
- Personality: {personality_str}
- Current goal: {char.get('want_vs_need', {}).get('want', 'N/A')}
- Emotional state: {char.get('emotional_state', 'N/A')}
""")

        return "\n".join(context) if context else "No character context available."

    def _build_sensory_guidance(
        self,
        previous_scenes_senses: list[list[str]],
        characters: list[dict],
        scene_context: dict,
    ) -> str:
        """Build sensory selection guidance."""
        # Available senses
        all_senses = ["sight", "sound", "smell", "taste", "touch"]

        # Track which senses were used recently
        recent_senses = set()
        for scene_senses in previous_scenes_senses[-3:]:  # Last 3 scenes
            recent_senses.update(scene_senses)

        # Suggest NEW senses (not recently used)
        available_senses = [s for s in all_senses if s not in recent_senses]
        if not available_senses:
            available_senses = all_senses  # All used - reset

        # Suggest 2 senses randomly (weighted by character if possible)
        suggested = random.sample(available_senses, min(2, len(available_senses)))

        # Get POV character for perception filter
        pov_char_name = scene_context.get("pov_character", "")
        pov_char = next((c for c in characters if c.get("name") == pov_char_name), None)

        profession = ""
        if pov_char:
            profession = pov_char.get("psychological", {}).get("profession", "Unknown")

        return f"""
PREVIOUS SCENES' SENSES (avoid repetition):
{', '.join([str(s) for s in previous_scenes_senses[-3:]])}

SUGGESTED SENSES FOR THIS SCENE: {', '.join(suggested)}

POV CHARACTER: {pov_char_name}
Profession: {profession}
(Use profession to guide WHAT they notice with these senses)

Example filters:
- Marine biologist → smell (algae, salt), touch (wet surfaces)
- Mechanic → sound (gears, engines), touch (oil, metal)
- Soldier → sight (exits, threats), sound (footsteps, clicks)
- Chef → smell (spices, burning), taste (subtle flavors)
"""

    def _calculate_voice_ratio(self, prose: str) -> VoiceRatioReport:
        """
        Calculate active vs passive voice ratio.

        This is a simplified heuristic - not perfect but good enough.
        """
        # Split into sentences
        sentences = prose.split(".")
        sentences = [s.strip() for s in sentences if s.strip()]

        total_sentences = len(sentences)
        passive_count = 0
        passive_examples = []

        # Heuristic: Look for passive voice indicators
        passive_indicators = [
            " was ",
            " were ",
            " been ",
            " being ",
            " is ",
            " are ",
        ]

        for sent in sentences:
            sent_lower = sent.lower()
            # Check if sentence has passive indicator + past participle pattern
            for indicator in passive_indicators:
                if indicator in sent_lower:
                    # Simple check: does it look passive?
                    # (This is approximate - full parsing would be better)
                    words = sent_lower.split()
                    idx = sent_lower.index(indicator)
                    # Check if next word looks like past participle (ends in -ed, -en)
                    next_words = sent_lower[idx:].split()[:3]
                    if any(w.endswith("ed") or w.endswith("en") for w in next_words):
                        passive_count += 1
                        if len(passive_examples) < 3:
                            passive_examples.append(sent[:100])
                        break

        active_count = total_sentences - passive_count
        active_percentage = (active_count / total_sentences * 100) if total_sentences > 0 else 0

        if active_percentage >= 80:
            assessment = "Excellent (80%+)"
        elif active_percentage >= 70:
            assessment = "Good (70-80%)"
        else:
            assessment = "Needs Improvement (<70%)"

        return VoiceRatioReport(
            total_sentences=total_sentences,
            active_voice_count=active_count,
            passive_voice_count=passive_count,
            active_percentage=round(active_percentage, 1),
            passive_examples=passive_examples,
            assessment=assessment,
        )
