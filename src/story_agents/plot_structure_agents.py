"""
Plot Structure Agents for Step 3: Character Arc + Story Beats

These agents debate and decide on:
1. Character arc beat structures (hero/villain focus)
2. Save the Cat 15-beat structure
3. Integration of arcs with beats
"""

import yaml
import os
from pathlib import Path
from src.story_agents.base_story_agent import BaseStoryAgent
from src.story_schemas import (
    # Arc Beat schemas
    ArcBeatProposal, ArcBeatCritique, ArcBeatVote,
    # SaveTheCat schemas
    SaveTheCatProposal, SaveTheCatCritique, SaveTheCatVote,
    SaveTheCatBeatProposal, SaveTheCatBeatCritique, SaveTheCatBeatVote,
    # Integration schemas
    BeatIntegrationProposal, BeatIntegrationCritique, BeatIntegrationVote,
)
from pydantic import BaseModel

# Load arc beat definitions from config
_config_path = Path(__file__).parent.parent / "config" / "character_arc_beats.yaml"
with open(_config_path) as f:
    ARC_BEAT_DEFINITIONS = yaml.safe_load(f)


def _get_arc_beat_count(arc_type: str) -> int:
    """Get the exact number of beats defined for an arc type."""
    if arc_type not in ARC_BEAT_DEFINITIONS:
        arc_type = "positive_change"
    return len(ARC_BEAT_DEFINITIONS[arc_type]['beats'])


def _format_arc_beats_for_prompt(arc_type: str) -> str:
    """Format arc beat definitions for inclusion in agent prompts."""
    if arc_type not in ARC_BEAT_DEFINITIONS:
        arc_type = "positive_change"  # Default fallback

    arc_config = ARC_BEAT_DEFINITIONS[arc_type]
    beats = arc_config['beats']

    formatted = f"{arc_config['name']} - {arc_config['description']}\n\nRequired Beats:\n"
    for i, beat in enumerate(beats, 1):
        formatted += f"{i}. {beat['name']} ({beat['timing']})\n"
        formatted += f"   Plot: {beat['plot_function']}\n"
        formatted += f"   Arc: {beat['arc_function']}\n"

    return formatted


def _format_arc_beats_for_prompt_micro(arc_type: str, num_beats: int = 5) -> str:
    """Format a micro-arc (5-7 key beats) for supporting characters.

    Selects the most important beats from the full arc structure.
    For Positive Change Arc: Opening, Ghost, Midpoint, All Is Lost, Climax
    """
    if arc_type not in ARC_BEAT_DEFINITIONS:
        arc_type = "positive_change"

    arc_config = ARC_BEAT_DEFINITIONS[arc_type]
    all_beats = arc_config['beats']

    # Select key beats based on arc type
    if arc_type == "positive_change" and len(all_beats) >= 12:
        # Key beats: 1, 3, 7, 10, 12 (Characteristic, Ghost, Midpoint, All Is Lost, Climax)
        key_indices = [0, 2, 6, 9, 11][:num_beats]
    elif arc_type == "flat" and len(all_beats) >= 7:
        # All beats for flat (already 7)
        key_indices = list(range(min(num_beats, 7)))
    else:
        # For other arc types, take evenly distributed beats
        step = max(1, len(all_beats) // num_beats)
        key_indices = [i * step for i in range(num_beats) if i * step < len(all_beats)]

    key_beats = [all_beats[i] for i in key_indices if i < len(all_beats)]

    formatted = f"MICRO-ARC ({num_beats} key beats from {arc_config['name']}):\n"
    for i, beat in enumerate(key_beats, 1):
        formatted += f"{i}. {beat['name']} ({beat['timing']})\n"
        formatted += f"   {beat['arc_function']}\n"

    return formatted


# =========================================================================
# ARC BEAT AGENTS (Character Arc Mapping)
# =========================================================================

class ArcBeatArchitectAgent(BaseStoryAgent):
    """Focuses on structural integrity of character arcs."""

    @property
    def name(self) -> str:
        return "ARC_ARCHITECT"

    @property
    def role(self) -> str:
        return "Character Arc Structure Expert"

    @property
    def system_prompt(self) -> str:
        return """You are an expert in character arc structure and beat mapping.

You understand:
- Positive Change Arc beats (Characteristic Moment → Ghost → Midpoint → All Is Lost → Climax)
- Flat Arc beats (Character knows Truth, transforms others)
- Negative Arc beats (Rejects Truth, descends)
- How arc beats create momentum and transformation

Focus on:
- Clear arc progression for hero and villain
- Structural integrity of transformations
- Ensuring each beat serves the arc
- Making side characters brief mentions (not full arcs)
"""


    def propose_arc_beats(self, characters: list, story_shape: str, theme_question: str) -> ArcBeatProposal:
        """Propose character arc structures for ALL major characters."""
        # Find hero and villain
        hero = next((c for c in characters if "protagonist" in c.get("role", "").lower() or
                     c.get("corner", "") == "positive"), characters[0])
        villain = next((c for c in characters if "antagonist" in c.get("role", "").lower() or
                       c.get("corner", "") == "negation"), characters[-1] if len(characters) > 1 else characters[0])

        # Find supporting characters
        supporting_chars = [c for c in characters if c not in [hero, villain]]

        hero_arc_type = hero.get("arc_type", "positive_change")
        villain_arc_type = villain.get("arc_type", "flat")

        # Get arc-specific beat templates and counts
        hero_beats_template = _format_arc_beats_for_prompt(hero_arc_type)
        villain_beats_template = _format_arc_beats_for_prompt(villain_arc_type)
        hero_beat_count = _get_arc_beat_count(hero_arc_type)
        villain_beat_count = _get_arc_beat_count(villain_arc_type)

        # Build supporting character section
        supporting_section = ""
        if supporting_chars:
            supporting_section = "\n\nSUPPORTING CHARACTERS (create micro-arcs with 5-7 key beats):\n"
            for sc in supporting_chars:
                sc_arc_type = sc.get("arc_type", "flat")
                supporting_section += f"\n{sc.get('name', 'Unknown')}\n"
                supporting_section += f"- Arc Type: {sc_arc_type}\n"
                supporting_section += f"- Lie: {sc.get('lie', 'N/A')}\n"
                supporting_section += f"- Truth: {sc.get('truth', 'N/A')}\n"
                supporting_section += f"{_format_arc_beats_for_prompt_micro(sc_arc_type, num_beats=5)}\n"

        user_prompt = f"""Design character arc structures for ALL major characters using arc-specific beats.

THEME: {theme_question}
STORY SHAPE: {story_shape}

HERO: {hero.get('name', 'Unknown')}
- Arc Type: {hero_arc_type}
- Lie: {hero.get('lie', 'N/A')}
- Truth: {hero.get('truth', 'N/A')}

{hero_beats_template}

VILLAIN: {villain.get('name', 'Unknown')}
- Arc Type: {villain_arc_type}
- Lie: {villain.get('lie', 'N/A')}
- Truth: {villain.get('truth', 'N/A')}

{villain_beats_template}
{supporting_section}

CRITICAL: Generate EXACTLY the right number of beats for each character:
- HERO: EXACTLY {hero_beat_count} beats (no more, no less)
- VILLAIN: EXACTLY {villain_beat_count} beats (no more, no less)
- SUPPORTING CHARACTERS: 5-7 key beats each (micro-arcs)

Create:
- ALL beats listed above for HERO (full arc)
- ALL beats listed above for VILLAIN (full arc)
- 5-7 key beats for EACH supporting character (micro-arcs)

Return format:
- agent_name: "{self.name}"
- hero_arc: CharacterArcStructure with all beats for {hero_arc_type}
- villain_arc: CharacterArcStructure with all beats for {villain_arc_type}
- supporting_arcs: List of CharacterArcStructure for each supporting character (5-7 beats each)
- reasoning: Why these arcs work together
"""
        return self.invoke_structured(user_prompt, ArcBeatProposal, max_tokens=16000)

    def critique_arc_beats(self, proposals: list[ArcBeatProposal], theme_question: str) -> list[ArcBeatCritique]:
        """Critique all arc beat proposals."""
        class CritiqueList(BaseModel):
            critiques: list[ArcBeatCritique]

        critiques_text = "\n\n".join([
            f"PROPOSAL {i}:\nAgent: {p.agent_name}\n"
            f"Hero Arc: {p.hero_arc.arc_type} - {len(p.hero_arc.arc_beats)} beats\n"
            f"Villain Arc: {p.villain_arc.arc_type} - {len(p.villain_arc.arc_beats)} beats\n"
            f"Reasoning: {p.reasoning[:200]}..."
            for i, p in enumerate(proposals)
        ])

        user_prompt = f"""Critique these character arc proposals:

{critiques_text}

THEME: {theme_question}

For EACH proposal (0, 1, 2), provide:
- agent_name: "{self.name}"
- proposal_index: the index
- score: 1-10 rating
- strengths: What arc structures work well
- weaknesses: What needs improvement

Return a list of exactly 3 critiques (one per proposal).
"""
        result = self.invoke_structured(user_prompt, CritiqueList)
        return result.critiques

    def vote(self, proposals: list[ArcBeatProposal], theme_question: str) -> ArcBeatVote:
        """Vote for best arc structure."""
        proposals_text = "\n\n".join([
            f"PROPOSAL {i}:\n{p.reasoning[:200]}..."
            for i, p in enumerate(proposals)
        ])

        user_prompt = f"""Vote for the best character arc structure:

{proposals_text}

THEME: {theme_question}

Return format:
- agent_name: "{self.name}"
- chosen_proposal_index: 0, 1, or 2
- reasoning: Why this is best
"""
        return self.invoke_structured(user_prompt, ArcBeatVote)


class ArcBeatPsychologicalAgent(BaseStoryAgent):
    """Focuses on psychological realism of character arcs."""

    @property
    def name(self) -> str:
        return "ARC_PSYCHOLOGICAL"

    @property
    def role(self) -> str:
        return "Character Psychology Expert"

    @property
    def system_prompt(self) -> str:
        return """You are an expert in character psychology and emotional arcs.

You understand:
- How characters resist change (psychological defenses)
- Emotional turning points and breakthroughs
- Shadow integration and transformation
- Trauma responses and healing patterns

Focus on:
- Psychologically realistic transformations
- Emotional authenticity at each beat
- Deep character work for hero/villain
- Ensuring arcs feel earned, not forced
"""

    def propose_arc_beats(self, characters: list, story_shape: str, theme_question: str) -> ArcBeatProposal:
        """Propose psychologically grounded arc structures for ALL characters."""
        hero = next((c for c in characters if "protagonist" in c.get("role", "").lower() or
                     c.get("corner", "") == "positive"), characters[0])
        villain = next((c for c in characters if "antagonist" in c.get("role", "").lower() or
                       c.get("corner", "") == "negation"), characters[-1] if len(characters) > 1 else characters[0])

        # Find supporting characters
        supporting_chars = [c for c in characters if c not in [hero, villain]]

        hero_arc_type = hero.get("arc_type", "positive_change")
        villain_arc_type = villain.get("arc_type", "flat")

        # Get arc-specific beat templates and counts
        hero_beats_template = _format_arc_beats_for_prompt(hero_arc_type)
        villain_beats_template = _format_arc_beats_for_prompt(villain_arc_type)
        hero_beat_count = _get_arc_beat_count(hero_arc_type)
        villain_beat_count = _get_arc_beat_count(villain_arc_type)

        # Build supporting character section
        supporting_section = ""
        if supporting_chars:
            supporting_section = "\n\nSUPPORTING CHARACTERS (create micro-arcs with 5-7 key beats):\n"
            for sc in supporting_chars:
                sc_arc_type = sc.get("arc_type", "flat")
                supporting_section += f"\n{sc.get('name', 'Unknown')}\n"
                supporting_section += f"- Arc Type: {sc_arc_type}\n"
                supporting_section += f"- Shadow traits: {sc.get('shadow_traits', [])}\n"
                supporting_section += f"- Lie/Truth: {sc.get('lie', 'N/A')} / {sc.get('truth', 'N/A')}\n"
                supporting_section += f"{_format_arc_beats_for_prompt_micro(sc_arc_type, num_beats=5)}\n"

        user_prompt = f"""Design psychologically realistic character arcs for ALL major characters using arc-specific beats.

THEME: {theme_question}

HERO: {hero.get('name', 'Unknown')}
- Arc Type: {hero_arc_type}
- Shadow traits: {hero.get('shadow_traits', [])}
- Want vs Need: {hero.get('want', 'N/A')} vs {hero.get('need', 'N/A')}
- Ghost: {hero.get('ghost', 'N/A')}

{hero_beats_template}

VILLAIN: {villain.get('name', 'Unknown')}
- Arc Type: {villain_arc_type}
- Shadow traits: {villain.get('shadow_traits', [])}
- Lie they believe: {villain.get('lie', 'N/A')}

{villain_beats_template}
{supporting_section}

CRITICAL: Generate EXACTLY the right number of beats for each character:
- HERO: EXACTLY {hero_beat_count} beats (no more, no less)
- VILLAIN: EXACTLY {villain_beat_count} beats (no more, no less)
- SUPPORTING CHARACTERS: 5-7 key beats each (micro-arcs)

Create:
- ALL beats listed above for HERO showing psychological transformation
- ALL beats listed above for VILLAIN showing their arc
- 5-7 key psychological beats for EACH supporting character

Return format:
- agent_name: "{self.name}"
- hero_arc: Full arc structure with all beats for {hero_arc_type}
- villain_arc: Full arc structure with all beats for {villain_arc_type}
- supporting_arcs: List of CharacterArcStructure for each supporting character (5-7 beats each)
- reasoning: Why these arcs are psychologically sound together
"""
        return self.invoke_structured(user_prompt, ArcBeatProposal, max_tokens=16000)

    def critique_arc_beats(self, proposals: list[ArcBeatProposal], theme_question: str) -> list[ArcBeatCritique]:
        """Critique arc proposals for psychological realism."""
        class CritiqueList(BaseModel):
            critiques: list[ArcBeatCritique]

        critiques_text = "\n\n".join([
            f"PROPOSAL {i} ({p.agent_name}):\nHero: {p.hero_arc.arc_summary}\nVillain: {p.villain_arc.arc_summary}"
            for i, p in enumerate(proposals)
        ])

        user_prompt = f"""Critique these arcs for psychological realism:

{critiques_text}

For each proposal (0, 1, 2), assess:
- Are transformations psychologically believable?
- Do arc beats reflect authentic emotional shifts?
- Is resistance to change realistic?

Return 3 critiques with:
- agent_name: "{self.name}"
- proposal_index, score, strengths, weaknesses
"""
        result = self.invoke_structured(user_prompt, CritiqueList)
        return result.critiques

    def vote(self, proposals: list[ArcBeatProposal], theme_question: str) -> ArcBeatVote:
        """Vote for most psychologically sound arcs."""
        user_prompt = f"""Vote for the arcs with the most psychological depth.

THEME: {theme_question}

{len(proposals)} proposals to consider.

Return:
- agent_name: "{self.name}"
- chosen_proposal_index: 0, 1, or 2
- reasoning: Why psychologically strongest
"""
        return self.invoke_structured(user_prompt, ArcBeatVote)


class ArcBeatDramaticAgent(BaseStoryAgent):
    """Focuses on dramatic impact of arc beats."""

    @property
    def name(self) -> str:
        return "ARC_DRAMATIC"

    @property
    def role(self) -> str:
        return "Dramatic Arc Expert"

    @property
    def system_prompt(self) -> str:
        return """You are an expert in dramatic storytelling and character arcs.

You understand:
- How to create maximum dramatic tension through character choices
- Escalation and stakes in character journeys
- Dramatic irony and revelations
- Emotional payoffs and catharsis

Focus on:
- Making each arc beat dramatically compelling
- Ensuring hero/villain arcs create conflict
- Building to powerful climactic moments
- Creating satisfying emotional payoffs
"""

    def propose_arc_beats(self, characters: list, story_shape: str, theme_question: str) -> ArcBeatProposal:
        """Propose dramatically powerful arc structures for ALL characters."""
        hero = next((c for c in characters if "protagonist" in c.get("role", "").lower() or
                     c.get("corner", "") == "positive"), characters[0])
        villain = next((c for c in characters if "antagonist" in c.get("role", "").lower() or
                       c.get("corner", "") == "negation"), characters[-1] if len(characters) > 1 else characters[0])

        # Find supporting characters
        supporting_chars = [c for c in characters if c not in [hero, villain]]

        hero_arc_type = hero.get("arc_type", "positive_change")
        villain_arc_type = villain.get("arc_type", "flat")

        # Get arc-specific beat templates and counts
        hero_beats_template = _format_arc_beats_for_prompt(hero_arc_type)
        villain_beats_template = _format_arc_beats_for_prompt(villain_arc_type)
        hero_beat_count = _get_arc_beat_count(hero_arc_type)
        villain_beat_count = _get_arc_beat_count(villain_arc_type)

        # Build supporting character section
        supporting_section = ""
        if supporting_chars:
            supporting_section = "\n\nSUPPORTING CHARACTERS (create micro-arcs with 5-7 key dramatic beats):\n"
            for sc in supporting_chars:
                sc_arc_type = sc.get("arc_type", "flat")
                supporting_section += f"\n{sc.get('name', 'Unknown')}\n"
                supporting_section += f"- Arc Type: {sc_arc_type}\n"
                supporting_section += f"- Role: {sc.get('role', 'N/A')}\n"
                supporting_section += f"{_format_arc_beats_for_prompt_micro(sc_arc_type, num_beats=5)}\n"

        user_prompt = f"""Design dramatically compelling character arcs for ALL major characters using arc-specific beats.

THEME: {theme_question}
STORY SHAPE: {story_shape}

HERO: {hero.get('name', 'Unknown')}
- Arc Type: {hero_arc_type}

{hero_beats_template}

VILLAIN: {villain.get('name', 'Unknown')}
- Arc Type: {villain_arc_type}

{villain_beats_template}
{supporting_section}

CRITICAL: Generate EXACTLY the right number of beats for each character:
- HERO: EXACTLY {hero_beat_count} beats (no more, no less)
- VILLAIN: EXACTLY {villain_beat_count} beats (no more, no less)
- SUPPORTING CHARACTERS: 5-7 key beats each (micro-arcs)

Create:
- ALL beats listed above for HERO maximizing dramatic tension
- ALL beats listed above for VILLAIN creating opposition
- 5-7 key dramatic beats for EACH supporting character

Return format:
- agent_name: "{self.name}"
- hero_arc: Arc with all beats for {hero_arc_type} (dramatic high points)
- villain_arc: Arc with all beats for {villain_arc_type} (creates opposition)
- supporting_arcs: List of CharacterArcStructure for each supporting character (5-7 beats each)
- reasoning: Why dramatically powerful together
"""
        return self.invoke_structured(user_prompt, ArcBeatProposal, max_tokens=16000)

    def critique_arc_beats(self, proposals: list[ArcBeatProposal], theme_question: str) -> list[ArcBeatCritique]:
        """Critique arc proposals for dramatic impact."""
        class CritiqueList(BaseModel):
            critiques: list[ArcBeatCritique]

        user_prompt = f"""Critique these arcs for dramatic impact:

{len(proposals)} proposals.

For each (0, 1, 2), assess:
- Do the arcs create compelling drama?
- Are there powerful emotional moments?
- Do hero/villain arcs create good conflict?

Return 3 critiques:
- agent_name: "{self.name}"
- proposal_index, score, strengths, weaknesses
"""
        result = self.invoke_structured(user_prompt, CritiqueList)
        return result.critiques

    def vote(self, proposals: list[ArcBeatProposal], theme_question: str) -> ArcBeatVote:
        """Vote for most dramatically powerful arcs."""
        user_prompt = f"""Vote for the most dramatically compelling arcs.

{len(proposals)} proposals.

Return:
- agent_name: "{self.name}"
- chosen_proposal_index: 0, 1, or 2
- reasoning: Why most dramatic
"""
        return self.invoke_structured(user_prompt, ArcBeatVote)


# =========================================================================
# SAVE THE CAT AGENTS (15-Beat Structure)
# =========================================================================

class SaveTheCatStructureAgent(BaseStoryAgent):
    """Focuses on structural integrity of STC beats."""

    @property
    def name(self) -> str:
        return "STC_STRUCTURE"

    @property
    def role(self) -> str:
        return "Save the Cat Structure Expert"

    @property
    def system_prompt(self) -> str:
        return """You are an expert in Save the Cat story structure.

You understand:
- All 15 beats and their structural purpose
- Timing percentages for each beat
- How beats create three-act structure
- Blake Snyder's structural principles

Focus on:
- Structurally sound beat placement
- Proper timing/pacing
- Clear cause-and-effect between beats
- Following proven STC principles

BIG MIDDLE EVENT (Butcher's Great Swampy Middle Fix): The Midpoint (beat 9) is NOT merely
a "shift in understanding." It must be a DRAMATIC CONFRONTATION — the biggest set piece
between the Catalyst and the Finale. Something that CHANGES what the character thinks the
story is about. If your midpoint is just a realization, it's too passive. Make it an EVENT
the character must survive. Everything in beats 7-8 builds TOWARD this event. Everything in
beats 10-12 deals with its FALLOUT.
"""

    def propose_beats(self, story_shape: str, save_the_cat_type: str, theme_question: str, logline: str) -> SaveTheCatBeatProposal:
        """Propose Save the Cat 15-beat structure."""
        user_prompt = f"""Design a Save the Cat 15-beat structure.

LOGLINE: {logline}
STORY SHAPE: {story_shape}
STC TYPE: {save_the_cat_type}
THEME: {theme_question}

The 15 Save the Cat beats are:
1. Opening Image (0-1%)
2. Theme Stated (5%)
3. Setup (1-10%)
4. Catalyst (10%)
5. Debate (10-20%)
6. Break Into Two (20%)
7. B Story (22%)
8. Fun and Games (20-50%)
9. Midpoint (50%)
10. Bad Guys Close In (50-75%)
11. All Is Lost (75%)
12. Dark Night of the Soul (75-80%)
13. Break Into Three (80%)
14. Finale (80-99%)
15. Final Image (99-100%)

Create ALL 15 beats above. For each beat provide:
- beat_name (from the list above)
- timing_percentage (from the list above)
- plot_event (what happens in this story)
- thematic_test (how it tests the theme)

Return format:
- agent_name: "{self.name}"
- beats: list of 15 SaveTheCatBeat objects
- overall_pacing: Fast/Medium/Slow with justification
- reasoning: Why this structure works
"""
        return self.invoke_structured(user_prompt, SaveTheCatBeatProposal)

    def critique_beats(self, proposals: list[SaveTheCatProposal], theme_question: str) -> list[SaveTheCatCritique]:
        """Critique Save the Cat proposals."""
        class CritiqueList(BaseModel):
            critiques: list[SaveTheCatCritique]

        user_prompt = f"""Critique these Save the Cat structures:

{len(proposals)} proposals.

For each (0, 1, 2), assess:
- Are all 15 beats present and properly timed?
- Does the structure create good pacing?
- Are beats causally connected?

Return 3 critiques:
- agent_name: "{self.name}"
- proposal_index, score, strengths, weaknesses
"""
        result = self.invoke_structured(user_prompt, CritiqueList)
        return result.critiques

    def vote(self, proposals: list[SaveTheCatProposal], theme_question: str) -> SaveTheCatVote:
        """Vote for best STC structure."""
        user_prompt = f"""Vote for the best Save the Cat structure.

{len(proposals)} proposals.

Return:
- agent_name: "{self.name}"
- chosen_proposal_index: 0, 1, or 2
- reasoning: Why structurally strongest
"""
        return self.invoke_structured(user_prompt, SaveTheCatVote)


class SaveTheCatPacingAgent(BaseStoryAgent):
    """Focuses on pacing and momentum."""

    @property
    def name(self) -> str:
        return "STC_PACING"

    @property
    def role(self) -> str:
        return "Story Pacing Expert"

    @property
    def system_prompt(self) -> str:
        return """You are an expert in story pacing and momentum.

You understand:
- How to maintain narrative drive
- When to accelerate/decelerate
- Escalation and tension building
- Reader engagement through pacing

Focus on:
- Creating propulsive momentum
- Balancing action and reflection
- Building to powerful peaks
- Avoiding narrative sag
"""

    def propose_beats(self, story_shape: str, save_the_cat_type: str, theme_question: str, logline: str) -> SaveTheCatBeatProposal:
        """Propose STC structure optimized for pacing."""
        user_prompt = f"""Design a well-paced Save the Cat structure.

LOGLINE: {logline}
STC TYPE: {save_the_cat_type}
THEME: {theme_question}

The 15 Save the Cat beats are:
1. Opening Image (0-1%)
2. Theme Stated (5%)
3. Setup (1-10%)
4. Catalyst (10%)
5. Debate (10-20%)
6. Break Into Two (20%)
7. B Story (22%)
8. Fun and Games (20-50%)
9. Midpoint (50%)
10. Bad Guys Close In (50-75%)
11. All Is Lost (75%)
12. Dark Night of the Soul (75-80%)
13. Break Into Three (80%)
14. Finale (80-99%)
15. Final Image (99-100%)

Create ALL 15 beats above that maintain momentum and engagement.

Return format:
- agent_name: "{self.name}"
- beats: 15 SaveTheCatBeat objects
- overall_pacing: Pacing strategy
- reasoning: Why this pacing works
"""
        return self.invoke_structured(user_prompt, SaveTheCatBeatProposal)

    def critique_beats(self, proposals: list[SaveTheCatProposal], theme_question: str) -> list[SaveTheCatCritique]:
        """Critique for pacing."""
        class CritiqueList(BaseModel):
            critiques: list[SaveTheCatCritique]

        user_prompt = f"""Critique these structures for pacing:

{len(proposals)} proposals.

For each (0, 1, 2), assess:
- Does the pacing maintain momentum?
- Are there any slow/saggy sections?
- Does it build to satisfying climaxes?

Return 3 critiques:
- agent_name: "{self.name}"
- proposal_index, score, strengths, weaknesses
"""
        result = self.invoke_structured(user_prompt, CritiqueList)
        return result.critiques

    def vote(self, proposals: list[SaveTheCatProposal], theme_question: str) -> SaveTheCatVote:
        """Vote for best paced structure."""
        user_prompt = f"""Vote for the best-paced structure.

{len(proposals)} proposals.

Return:
- agent_name: "{self.name}"
- chosen_proposal_index: 0, 1, or 2
- reasoning: Why best paced
"""
        return self.invoke_structured(user_prompt, SaveTheCatVote)


class SaveTheCatGenreAgent(BaseStoryAgent):
    """Focuses on genre expectations."""

    @property
    def name(self) -> str:
        return "STC_GENRE"

    @property
    def role(self) -> str:
        return "Genre Story Expert"

    @property
    def system_prompt(self) -> str:
        return """You are an expert in genre storytelling and conventions.

You understand:
- Genre-specific story beats
- Audience expectations
- How to deliver on genre promises
- Subverting vs. honoring conventions

Focus on:
- Meeting genre expectations
- Delivering genre-specific moments
- Balancing innovation with convention
- Satisfying the target audience
"""

    def propose_beats(self, story_shape: str, save_the_cat_type: str, theme_question: str, logline: str, genres: list) -> SaveTheCatBeatProposal:
        """Propose genre-appropriate STC structure."""
        genre_str = f"{genres[0]}" + (f"/{genres[1]}" if len(genres) > 1 else "")

        user_prompt = f"""Design a Save the Cat structure for {genre_str}.

LOGLINE: {logline}
GENRES: {genre_str}
THEME: {theme_question}

The 15 Save the Cat beats are:
1. Opening Image (0-1%)
2. Theme Stated (5%)
3. Setup (1-10%)
4. Catalyst (10%)
5. Debate (10-20%)
6. Break Into Two (20%)
7. B Story (22%)
8. Fun and Games (20-50%)
9. Midpoint (50%)
10. Bad Guys Close In (50-75%)
11. All Is Lost (75%)
12. Dark Night of the Soul (75-80%)
13. Break Into Three (80%)
14. Finale (80-99%)
15. Final Image (99-100%)

Create ALL 15 beats above that deliver on genre expectations.

Return format:
- agent_name: "{self.name}"
- beats: 15 SaveTheCatBeat objects
- overall_pacing: Genre-appropriate pacing
- reasoning: How this serves genre
"""
        return self.invoke_structured(user_prompt, SaveTheCatBeatProposal)

    def critique_beats(self, proposals: list[SaveTheCatProposal], theme_question: str, genres: list) -> list[SaveTheCatCritique]:
        """Critique for genre fit."""
        class CritiqueList(BaseModel):
            critiques: list[SaveTheCatCritique]

        genre_str = f"{genres[0]}" + (f"/{genres[1]}" if len(genres) > 1 else "")

        user_prompt = f"""Critique these structures for {genre_str} genre fit:

{len(proposals)} proposals.

For each (0, 1, 2), assess:
- Does it meet genre expectations?
- Are genre-specific beats present?
- Will it satisfy genre fans?

Return 3 critiques:
- agent_name: "{self.name}"
- proposal_index, score, strengths, weaknesses
"""
        result = self.invoke_structured(user_prompt, CritiqueList)
        return result.critiques

    def vote(self, proposals: list[SaveTheCatProposal], theme_question: str) -> SaveTheCatVote:
        """Vote for best genre-fit structure."""
        user_prompt = f"""Vote for the structure that best serves the genre.

{len(proposals)} proposals.

Return:
- agent_name: "{self.name}"
- chosen_proposal_index: 0, 1, or 2
- reasoning: Why best for genre
"""
        return self.invoke_structured(user_prompt, SaveTheCatVote)


# =========================================================================
# INTEGRATION AGENTS (Merge Arcs + Beats)
# =========================================================================

class IntegrationWeaverAgent(BaseStoryAgent):
    """Focuses on weaving arcs and beats together."""

    @property
    def name(self) -> str:
        return "INTEGRATION_WEAVER"

    @property
    def role(self) -> str:
        return "Arc/Beat Integration Expert"

    @property
    def system_prompt(self) -> str:
        return """You are an expert at integrating character arcs with plot beats.

You understand:
- How character transformations drive plot
- How plot events force character growth
- Synchronizing internal/external journeys
- Creating resonance between arc and plot

Focus on:
- Seamless integration of arc and plot
- Each beat serving both story and character
- Hero/villain arcs intersecting with plot
- Ensuring everything feels unified
"""

    def propose_integration(self, hero_arc, villain_arc, supporting_arcs, stc_beats, theme_question: str) -> BeatIntegrationProposal:
        """Propose integrated beat structure for ALL characters."""
        hero_summary = f"{hero_arc.character_name} ({hero_arc.arc_type}): {len(hero_arc.arc_beats)} beats"
        villain_summary = f"{villain_arc.character_name} ({villain_arc.arc_type}): {len(villain_arc.arc_beats)} beats"
        beats_summary = f"{len(stc_beats)} STC beats"

        # Build supporting character summary
        supporting_summary = ""
        if supporting_arcs:
            supporting_summary = "\n\nSUPPORTING CHARACTERS:\n"
            for arc in supporting_arcs:
                supporting_summary += f"- {arc.character_name} ({arc.arc_type}): {len(arc.arc_beats)} beats\n"

        user_prompt = f"""Integrate ALL character arcs with Save the Cat beats.

THEME: {theme_question}

HERO ARC: {hero_summary}
VILLAIN ARC: {villain_summary}
{supporting_summary}
STC BEATS: {beats_summary}

The 15 Save the Cat beats to integrate are:
1. Opening Image (0-1%)
2. Theme Stated (5%)
3. Setup (1-10%)
4. Catalyst (10%)
5. Debate (10-20%)
6. Break Into Two (20%)
7. B Story (22%)
8. Fun and Games (20-50%)
9. Midpoint (50%)
10. Bad Guys Close In (50-75%)
11. All Is Lost (75%)
12. Dark Night of the Soul (75-80%)
13. Break Into Three (80%)
14. Finale (80-99%)
15. Final Image (99-100%)

Create ALL 15 integrated beats above where:
- Each beat has plot event (from STC)
- Each beat has character_arcs dict mapping ALL character names to their arc beat at this moment
  (Include hero, villain, and all supporting characters)
- Each beat tests the theme
- Each beat has location_type indicating WHERE this beat occurs

LOCATION_TYPE EXAMPLES (choose appropriate for your genre):
- Fantasy: "Sacred Temple", "Public Square", "Dark Forest", "Throne Room"
- Sci-Fi: "Central Hub", "Remote Outpost", "Docking Bay", "Command Center"
- Mystery: "Crime Scene", "Police Station", "Suspect's Home", "Hidden Location"
- Romance: "First Meeting Place", "Intimate Setting", "Public Gathering", "Private Retreat"
- Horror: "Haunted Location", "Safe Haven", "Abandoned Place", "Final Confrontation Site"

Assign a location_type to each beat based on what type of setting makes sense for that story moment.

In IntegratedBeat.character_arcs, use character names as keys and their arc beat description as values.
Example: {{"Elara": "Characteristic Moment showing her Lie", "Marcus": "Representing the Truth"}}

Return format:
- agent_name: "{self.name}"
- integrated_beats: list of 15 IntegratedBeat objects (each with location_type)
- reasoning: Why this integration works for all characters
"""
        return self.invoke_structured(user_prompt, BeatIntegrationProposal, max_tokens=16000)

    def critique_integration(self, proposals: list[BeatIntegrationProposal], theme_question: str) -> list[BeatIntegrationCritique]:
        """Critique integration proposals."""
        class CritiqueList(BaseModel):
            critiques: list[BeatIntegrationCritique]

        user_prompt = f"""Critique these beat integrations:

{len(proposals)} proposals.

For each (0, 1, 2), assess:
- Is the integration seamless?
- Do arc and plot reinforce each other?
- Are both hero and villain well-integrated?

Return 3 critiques:
- agent_name: "{self.name}"
- proposal_index, score, strengths, weaknesses
"""
        result = self.invoke_structured(user_prompt, CritiqueList)
        return result.critiques

    def vote(self, proposals: list[BeatIntegrationProposal], theme_question: str) -> BeatIntegrationVote:
        """Vote for best integration."""
        user_prompt = f"""Vote for the best integration.

{len(proposals)} proposals.

Return:
- agent_name: "{self.name}"
- chosen_proposal_index: 0, 1, or 2
- reasoning: Why best integrated
"""
        return self.invoke_structured(user_prompt, BeatIntegrationVote)


class IntegrationThematicAgent(BaseStoryAgent):
    """Focuses on thematic resonance."""

    @property
    def name(self) -> str:
        return "INTEGRATION_THEMATIC"

    @property
    def role(self) -> str:
        return "Thematic Integration Expert"

    @property
    def system_prompt(self) -> str:
        return """You are an expert at ensuring every beat serves the theme.

You understand:
- How to test thematic questions through plot
- Thematic escalation across beats
- Character choices as thematic exploration
- Thematic payoffs and resolution

Focus on:
- Every beat testing the theme
- Thematic progression and escalation
- Hero/villain as thematic opposites
- Satisfying thematic resolution
"""

    def propose_integration(self, hero_arc, villain_arc, supporting_arcs, stc_beats, theme_question: str) -> BeatIntegrationProposal:
        """Propose thematically rich integration for ALL characters."""
        # Build supporting character summary
        supporting_summary = ""
        if supporting_arcs:
            supporting_summary = "\n\nSUPPORTING CHARACTERS:\n"
            for arc in supporting_arcs:
                supporting_summary += f"- {arc.character_name} ({arc.arc_type}): {len(arc.arc_beats)} beats\n"

        user_prompt = f"""Integrate ALL character arcs and beats with strong thematic focus.

THEME: {theme_question}

HERO: {hero_arc.character_name}
VILLAIN: {villain_arc.character_name}
{supporting_summary}

The 15 Save the Cat beats to integrate are:
1. Opening Image (0-1%)
2. Theme Stated (5%)
3. Setup (1-10%)
4. Catalyst (10%)
5. Debate (10-20%)
6. Break Into Two (20%)
7. B Story (22%)
8. Fun and Games (20-50%)
9. Midpoint (50%)
10. Bad Guys Close In (50-75%)
11. All Is Lost (75%)
12. Dark Night of the Soul (75-80%)
13. Break Into Three (80%)
14. Finale (80-99%)
15. Final Image (99-100%)

Ensure EVERY beat explores the theme through:
- Character choices (ALL characters, not just hero/villain)
- Plot consequences
- Thematic opposition between characters

Create ALL 15 integrated beats above with:
- plot_event (from STC)
- character_arcs dict mapping ALL character names to their arc beat at this moment
- thematic_test (how this beat explores the theme)
- location_type (WHERE this beat occurs)

LOCATION_TYPE EXAMPLES (choose appropriate for your genre):
- Fantasy: "Sacred Temple", "Public Square", "Dark Forest", "Throne Room"
- Sci-Fi: "Central Hub", "Remote Outpost", "Docking Bay", "Command Center"
- Mystery: "Crime Scene", "Police Station", "Suspect's Home", "Hidden Location"
- Romance: "First Meeting Place", "Intimate Setting", "Public Gathering", "Private Retreat"
- Horror: "Haunted Location", "Safe Haven", "Abandoned Place", "Final Confrontation Site"

Assign a location_type to each beat based on what type of setting makes sense for that story moment.

Return format:
- agent_name: "{self.name}"
- integrated_beats: 15 IntegratedBeat objects (each with clear thematic_test and location_type)
- reasoning: How theme is explored through all characters
"""
        return self.invoke_structured(user_prompt, BeatIntegrationProposal, max_tokens=16000)

    def critique_integration(self, proposals: list[BeatIntegrationProposal], theme_question: str) -> list[BeatIntegrationCritique]:
        """Critique for thematic strength."""
        class CritiqueList(BaseModel):
            critiques: list[BeatIntegrationCritique]

        user_prompt = f"""Critique for thematic resonance:

THEME: {theme_question}

{len(proposals)} proposals.

For each (0, 1, 2), assess:
- Does every beat test the theme?
- Is there thematic escalation?
- Is the theme resolved satisfyingly?

Return 3 critiques:
- agent_name: "{self.name}"
- proposal_index, score, strengths, weaknesses
"""
        result = self.invoke_structured(user_prompt, CritiqueList)
        return result.critiques

    def vote(self, proposals: list[BeatIntegrationProposal], theme_question: str) -> BeatIntegrationVote:
        """Vote for most thematically strong."""
        user_prompt = f"""Vote for the most thematically powerful integration.

THEME: {theme_question}

{len(proposals)} proposals.

Return:
- agent_name: "{self.name}"
- chosen_proposal_index: 0, 1, or 2
- reasoning: Why thematically strongest
"""
        return self.invoke_structured(user_prompt, BeatIntegrationVote)


class IntegrationConflictAgent(BaseStoryAgent):
    """Focuses on conflict and opposition."""

    @property
    def name(self) -> str:
        return "INTEGRATION_CONFLICT"

    @property
    def role(self) -> str:
        return "Conflict Integration Expert"

    @property
    def system_prompt(self) -> str:
        return """You are an expert at creating conflict through integrated beats.

You understand:
- How hero/villain arcs create opposition
- Internal vs external conflict
- Escalating conflict across beats
- Conflict resolution and catharsis

Focus on:
- Hero/villain arcs intersecting in conflict
- Each beat raising stakes
- Internal/external conflicts reinforcing
- Powerful conflict climax
"""

    def propose_integration(self, hero_arc, villain_arc, supporting_arcs, stc_beats, theme_question: str) -> BeatIntegrationProposal:
        """Propose conflict-rich integration for ALL characters."""
        # Build supporting character summary
        supporting_summary = ""
        if supporting_arcs:
            supporting_summary = "\n\nSUPPORTING CHARACTERS:\n"
            for arc in supporting_arcs:
                supporting_summary += f"- {arc.character_name} ({arc.arc_type}): {len(arc.arc_beats)} beats\n"

        user_prompt = f"""Integrate ALL character arcs and beats with maximum conflict.

THEME: {theme_question}

HERO: {hero_arc.character_name}
VILLAIN: {villain_arc.character_name}
{supporting_summary}

The 15 Save the Cat beats to integrate are:
1. Opening Image (0-1%)
2. Theme Stated (5%)
3. Setup (1-10%)
4. Catalyst (10%)
5. Debate (10-20%)
6. Break Into Two (20%)
7. B Story (22%)
8. Fun and Games (20-50%)
9. Midpoint (50%)
10. Bad Guys Close In (50-75%)
11. All Is Lost (75%)
12. Dark Night of the Soul (75-80%)
13. Break Into Three (80%)
14. Finale (80-99%)
15. Final Image (99-100%)

Ensure ALL character arcs create compelling conflict at each beat.

Create ALL 15 integrated beats above with:
- plot_event (from STC)
- character_arcs dict mapping ALL character names to their arc beat at this moment
- thematic_test (how beat explores theme through conflict)
- location_type (WHERE this beat occurs)

LOCATION_TYPE EXAMPLES (choose appropriate for your genre):
- Fantasy: "Sacred Temple", "Public Square", "Dark Forest", "Throne Room"
- Sci-Fi: "Central Hub", "Remote Outpost", "Docking Bay", "Command Center"
- Mystery: "Crime Scene", "Police Station", "Suspect's Home", "Hidden Location"
- Romance: "First Meeting Place", "Intimate Setting", "Public Gathering", "Private Retreat"
- Horror: "Haunted Location", "Safe Haven", "Abandoned Place", "Final Confrontation Site"

Assign a location_type to each beat based on what type of setting makes sense for that story moment.

Include escalating conflict between hero/villain and involving supporting characters.

Return format:
- agent_name: "{self.name}"
- integrated_beats: 15 IntegratedBeat objects (strong conflict focus, with location_type)
- reasoning: How conflict escalates through all characters
"""
        return self.invoke_structured(user_prompt, BeatIntegrationProposal, max_tokens=16000)

    def critique_integration(self, proposals: list[BeatIntegrationProposal], theme_question: str) -> list[BeatIntegrationCritique]:
        """Critique for conflict strength."""
        class CritiqueList(BaseModel):
            critiques: list[BeatIntegrationCritique]

        user_prompt = f"""Critique for conflict quality:

{len(proposals)} proposals.

For each (0, 1, 2), assess:
- Is there strong hero/villain opposition?
- Does conflict escalate properly?
- Are conflicts resolved satisfyingly?

Return 3 critiques:
- agent_name: "{self.name}"
- proposal_index, score, strengths, weaknesses
"""
        result = self.invoke_structured(user_prompt, CritiqueList)
        return result.critiques

    def vote(self, proposals: list[BeatIntegrationProposal], theme_question: str) -> BeatIntegrationVote:
        """Vote for strongest conflict."""
        user_prompt = f"""Vote for the integration with best conflict.

{len(proposals)} proposals.

Return:
- agent_name: "{self.name}"
- chosen_proposal_index: 0, 1, or 2
- reasoning: Why strongest conflict
"""
        return self.invoke_structured(user_prompt, BeatIntegrationVote)
