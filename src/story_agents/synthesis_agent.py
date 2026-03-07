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

=== ANTI-REPETITION: SCENE OPENINGS ===

BANNED PATTERNS for opening paragraph:
- "Dusk/Dawn/Night/Morning settled/fell/crept over..."
- "The [time of day] air was..."
- "Shadows lengthened/deepened across..."
- "The [noun] hung heavy in the air"
- Any opening that starts with weather or time-of-day atmosphere

Every scene opening MUST be DIFFERENT from the previous scene. Follow the assigned opening type strictly.

=== BANNED VOCABULARY & AI TELLS ===

NEVER USE these AI-overused words/phrases. They are fingerprints of machine writing:
- "fragile hope" or "fragile [any abstract noun]"
- "the weight of [anything]" (e.g., "the weight of silence", "the weight of responsibility")
- "a [adjective] reminder that/of" (e.g., "a stark reminder", "a grim reminder", "a constant reminder")
- "not just X, but Y" formula (e.g., "not just for her, but for everyone")
- "the silence stretched between them"
- "something shifted" or "something broke"
- "resolve hardened" / "determination flickered" / "resolve wavered"
- "doubt gnawed" / "tension gripped" / "urgency pressed"

OVERUSED WORDS (use each NO MORE THAN ONCE per scene):
shadow/shadows, beneath, pressed, fragile, resolve, unspoken, lingered, settled, shifted

INSTEAD OF abstract emotion-settling phrases like "doubt gnawed at her" or "tension gripped him":
- Show a SPECIFIC PHYSICAL ACTION: "She lined up the salt shakers by height."
- Show a BEHAVIORAL CHOICE: "He walked past the phone without picking it up."
- Show through DIALOGUE AVOIDANCE: what the character refuses to say

=== SCENE ENDINGS: CONCRETE, NOT ABSTRACT ===

End every scene with ONE of these (rotate, never repeat same type twice in a row):
1. AN IMAGE: A concrete visual the reader can see. "The door stayed open. Nobody walked through it."
2. A LINE OF DIALOGUE: Last word is spoken. Let the reader sit with it.
3. AN ACTION: Character does something small and specific. "She folded the letter into the shape of a boat."
4. A SENSORY DETAIL: Ground the ending in the body. "The coffee had gone cold."
5. A QUESTION (internal, not rhetorical): Must be specific, not thematic. "Where had she put the key?"

NEVER end with: thematic summary, rhetorical question about meaning, abstract emotional resolution,
"And in that moment, [character] understood that...", "This was what it meant to...", or any
sentence containing the word "reminder".

=== PARAGRAPH & SENTENCE RHYTHM ===

VARY paragraph length deliberately:
- Include at least ONE single-sentence paragraph per scene (for impact)
- Include at least ONE paragraph of 150+ words (for immersion)
- NEVER let 3+ consecutive paragraphs be similar length (80-110 words)

VARY sentence length aggressively:
- Include at least TWO sentences under 6 words ("She ran." / "No." / "Gone.")
- Include at least ONE sentence over 30 words
- Use fragments deliberately: "Not yet. Not here."
- Use run-ons for urgency: "She grabbed the bag and the keys and the photo from the mantel and she didn't look back."
- NEVER write two consecutive sentences with the same grammatical structure

=== DIALOGUE DENSITY ===

MINIMUM 1 line of dialogue per 150 words of prose (aim for 10+ lines per 1500-word scene).
Dialogue must include:
- At least ONE interruption (em-dash mid-sentence: "I was going to—")
- At least ONE trailing off (ellipsis: "I thought we could...")
- At least ONE non-answer (character responds to a question with something unrelated)
- At least ONE line where subtext contradicts surface meaning
- Use "said" for tags. Do NOT use: murmured, whispered, proclaimed, declared, breathed, hissed
  (unless truly whispering/hissing). Let the CONTENT carry the tone.

=== NOVEL PROSE FORMAT (Critical — This Is a Novel, Not a Script) ===

Write DIRECT novel prose. No script formatting. No "Narrator:" labels. No character name prefixes.
The output must read like a page from a published novel.

NARRATION STYLE:
- Write in CONTINUOUS FLOWING PARAGRAPHS, not short fragmented lines
- Narration blocks should be 3-8 sentences of immersive description
- WRONG: One-sentence narrator lines bouncing between action and dialogue
- RIGHT: Rich paragraphs that ground the reader in the world, then break for dialogue

DIALOGUE EMBEDDING:
- All dialogue in quotation marks ("...")
- Use ACTION BEATS (preferred over dialogue tags):
  - ACTION BEAT: "Kael set down his cup. 'We leave at dawn.'" — action identifies speaker
  - Action beats are SEPARATE sentences (period before dialogue, not comma)
- ATTRIBUTION HIERARCHY:
  1. ACTION BEATS (preferred): Physical action next to speech identifies speaker
  2. INVISIBLE TAGS: "said" and "asked" ONLY
  3. UNTAGGED: Only when 2 speakers alternate and context is perfectly clear
- Re-identify the speaker every 2-3 exchanges (audiobook listeners can't glance back)
- After 4+ lines of pure dialogue, ground with physical action (no "floating heads")

CHARACTER NAME RULES:
- Full name (first + last) ONLY at first introduction by the narrator
- After that, use ONE consistent short form
- NEVER rotate between appellations ("the warrior", "the tall man", "her companion")
- Characters almost NEVER say each other's full names in conversation

HOW CHARACTERS ADDRESS EACH OTHER (relationship-driven):
- CLOSE FRIENDS/FAMILY: First name, nicknames ("Kael", "Rae")
- FORMAL/PROFESSIONAL/RIVALS: Last name or title ("Commander Vale", "Reed")
- AUTHORITY FIGURES: Title + surname ("Doctor Ashworth", "Captain Lorne")
- ENEMIES/COLD DISTANCE: Surname only ("Vale." — clipped, no warmth)
- INTIMACY SHIFT: Switching from "Commander" to "Aurora" signals emotional change — deliberate
- Each character pair has a CONSISTENT naming pattern reflecting their dynamic

CHARACTER-AS-PERCEPTION-FILTER:
Every character's dialogue, thoughts, actions, and observations MUST be filtered through
their background, interests, expertise, and life experience.
- BOTANIST notices plants first, SOLDIER notices exits, THIEF notices locks
- DIALOGUE: A mechanic says "This plan has too many moving parts." A doctor says "let's
  diagnose the problem."
- INTERNAL THOUGHTS: Traumatized = hypervigilant. Leader = strategic. Artist = colors/textures.
- REACTIONS: Fighter reaches for weapon. Politician reaches for words.
Two characters in the same room should describe it completely differently.

AUDIOBOOK-READY PROSE:
- Max sentence ~25 words. Context before detail.
- No abbreviations ("Doctor" not "Dr."), numbers as words ("three hundred" not "300")
- Avoid homographs: "led" not "lead", "injury" not "wound", "teardrop" not "tear"
- No nested quotes — paraphrase inner quotes
- Scene transitions signaled textually ("Three hours later"), not just whitespace

SHOW EMOTION THROUGH ACTION (MRU order):
1. STIMULUS → 2. FEELING (involuntary body) → 3. ACTION (physical) → 4. SPEECH (conscious)
- NEVER "[Character] felt [emotion]" or "[Character] was [emotion]"
- "Her knuckles whitened around the pen." NOT "She was furious."

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
        opening_type: dict = None,
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

        # Extract scene_data for proper key access
        scene_data = scene_context.get("scene_data", scene_context)

        # Build POV gender/pronoun info
        pov_name = scene_data.get("pov_character", "")
        pov_char = next((c for c in characters if c.get("name") == pov_name), {})
        pov_gender = pov_char.get("gender", "unknown")
        if pov_gender == "female":
            pov_pronouns = "she/her/hers"
        elif pov_gender == "male":
            pov_pronouns = "he/him/his"
        else:
            pov_pronouns = "they/them/theirs"

        # Build opening type guidance
        opening_guidance = ""
        if opening_type:
            opening_guidance = f"""
=== MANDATORY SCENE OPENING TYPE: {opening_type['label'].upper()} ===
{opening_type['instruction']}

EXAMPLE: {opening_type['example']}

{opening_type['avoid']}

Your opening_paragraph MUST follow this type. This is NON-NEGOTIABLE. Do NOT default to atmospheric/weather/time-of-day descriptions.

"""

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
Scene: {scene_data.get('scene_summary', scene_data.get('happens', 'N/A'))}
Characters present: {', '.join(scene_data.get('characters', []) if isinstance(scene_data.get('characters', []), list) and all(isinstance(c, str) for c in scene_data.get('characters', [])) else [c.get('name', '?') if isinstance(c, dict) else str(c) for c in scene_data.get('characters', [])])}
Location: {scene_data.get('location', 'N/A')}
Goal: {scene_data.get('goal', 'N/A')}
Conflict: {scene_data.get('conflict', 'N/A')}
Disaster/Resolution: {scene_data.get('disaster_or_resolution', 'N/A')}
Ticking Clock: {scene_data.get('ticking_clock', 'N/A')}

=== POV CHARACTER & PRONOUNS ===
POV: {pov_name} ({pov_gender})
Pronouns: {pov_pronouns}
ALL narration pronouns for this character MUST be {pov_pronouns}. Do NOT switch between he/she for the same character.

=== CHARACTER ROSTER (STRICT) ===
ONLY these characters may appear in the scene: {', '.join(scene_data.get('characters', []) if isinstance(scene_data.get('characters', []), list) and all(isinstance(c, str) for c in scene_data.get('characters', [])) else [c.get('name', '?') if isinstance(c, dict) else str(c) for c in scene_data.get('characters', [])])}
Do NOT invent, reference, or name any character not in this list.
All dialogue MUST be spoken by characters in this roster. No exceptions.

{opening_guidance}=== YOUR SYNTHESIS TASK ===

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

Step 7: DE-AI THE PROSE (Critical - do this BEFORE finalizing):
   - Search your synthesized prose for EVERY instance of: "weight of", "fragile", "reminder", "resolve", "beneath", "shadow/shadows"
   - Replace each with a CONCRETE SPECIFIC detail unique to this scene
   - Check the LAST PARAGRAPH: if it contains a thematic summary or rhetorical question about meaning, REWRITE it to end on image/action/dialogue
   - Count dialogue lines: if fewer than 10 in 1500 words, ADD more dialogue exchanges with interruptions and subtext
   - Check paragraph lengths: if 3+ consecutive paragraphs are 80-110 words, BREAK the pattern (split one short, merge two together)
   - Apply Elmore Leonard's test: "If it sounds like writing, rewrite it."

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
        scene_data = scene_context.get("scene_data", scene_context)
        # chars_present may be list[str] (from scene_data) or list[dict] (from top-level)
        raw_present = scene_data.get("characters", [])
        if raw_present and isinstance(raw_present[0], dict):
            chars_present = [c.get("name", "") for c in raw_present]
        else:
            chars_present = raw_present
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

            gender = char.get("gender", "unknown")
            if gender == "female":
                pronouns = "she/her/hers"
            elif gender == "male":
                pronouns = "he/him/his"
            else:
                pronouns = "they/them/theirs"

            context.append(f"""
{char_name} ({gender}):
- Pronouns: {pronouns}
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
        scene_data = scene_context.get("scene_data", scene_context)
        pov_char_name = scene_data.get("pov_character", "")
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
