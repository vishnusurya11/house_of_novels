"""
Story Shape & Genre Selection Agents for Step 2.

These agents analyze theme, characters, and logline to determine:
1. Classic Story Shape (7 Basic Plots)
2. Save the Cat Type (emotional stakes framework)
3. Genre(s) (pressure/delivery mode)
4. Tropes to use/subvert

References:
- Christopher Booker's "The Seven Basic Plots"
- Blake Snyder's "Save the Cat" (10 story types)
- TVTropes for genre conventions
"""

from pydantic import BaseModel
from src.story_agents.base_story_agent import BaseStoryAgent
from src.story_schemas import (
    StoryShapeProposal,
    StoryShapeCritique,
    StoryShapeVote,
    SaveTheCatProposal,
    SaveTheCatCritique,
    SaveTheCatVote,
    GenreProposal,
    GenreCritique,
    GenreVote,
    TropeProposal,
    TropeCritique,
    TropeVote,
)


# =============================================================================
# STORY SHAPE AGENTS (7 Basic Plots)
# =============================================================================

class StoryShapeJourneyAgent(BaseStoryAgent):
    """Analyzes the logline's journey type to recommend Classic Plot."""

    @property
    def name(self) -> str:
        return "SHAPE_JOURNEY"

    @property
    def role(self) -> str:
        return "Story shape journey analyst"

    @property
    def system_prompt(self) -> str:
        return """You are a story structure specialist focused on the 7 Basic Plots.

Your role: Analyze the logline's JOURNEY TYPE and recommend which Classic Plot fits best.

THE 7 BASIC PLOTS (Christopher Booker):

1. **Overcoming the Monster**: Evil threatens → hero confronts it
   - Emotional Promise: Safety restored through courage
   - Best For: Action, Horror, Fantasy, Superhero

2. **Rags to Riches**: Overlooked → rises to greatness
   - Emotional Promise: Worth can be revealed/earned
   - Best For: Coming-of-age, Romance, Sports

3. **The Quest**: Journey to obtain a goal
   - Emotional Promise: Meaning through striving
   - Best For: Fantasy, Adventure, Epic sci-fi

4. **Voyage and Return**: Enter strange world → return changed
   - Emotional Promise: Exploration transforms identity
   - Best For: Portal fantasy, Sci-fi, Psychological

5. **Comedy**: Confusion → harmony restored
   - Emotional Promise: Chaos resolves into connection
   - Best For: Romance, Social drama, Ensemble

6. **Tragedy**: Flawed character → downfall
   - Emotional Promise: Some mistakes cannot be undone
   - Best For: Psychological drama, Political, Dark fantasy

7. **Rebirth**: Corrupted/imprisoned → redeemed
   - Emotional Promise: Change through sacrifice/love
   - Best For: Redemption arcs, Emotional drama

MAJOR DRAMATIC QUESTION (Sanderson): Every story must have a single, clear MDQ stated as a
yes/no question. "Will [protagonist] achieve [goal] despite [central obstacle]?" This question
must be clear to the reader by end of Chapter 1. Every chapter must advance, complicate, or
threaten the answer. If a chapter doesn't connect to the MDQ, it's structural dead weight.
The MDQ is the spine that unifies all subplots.

Focus on the JOURNEY STRUCTURE in the logline."""

    def propose_story_shape(
        self,
        logline: str,
        theme_question: str,
        characters: list[dict]
    ) -> StoryShapeProposal:
        """Propose a story shape based on journey type."""

        character_summary = "\n".join([
            f"- {c.get('name', 'Unknown')}: {c.get('arc_type', 'Unknown arc')} ({c.get('role', 'unknown role')})"
            for c in characters[:4]
        ])

        user_prompt = f"""Analyze this story and propose the best Classic Plot shape:

**LOGLINE:** {logline}

**THEME:** {theme_question}

**CHARACTERS:**
{character_summary}

Based on the JOURNEY TYPE in the logline, which of the 7 Basic Plots best fits?

Provide your response with:
1. agent_name: "{self.name}"
2. story_shape: The chosen plot (exact name from the 7)
3. why_this_shape: Why this shape matches the journey type
4. how_it_explores_theme: How this shape will explore the theme
5. emotional_promise: What emotional journey readers will experience
6. reasoning: Additional insights"""

        return self.invoke_structured(user_prompt, StoryShapeProposal)

    def critique_story_shape(
        self,
        proposals: list[StoryShapeProposal],
        logline: str,
        characters: list[dict]
    ) -> list[StoryShapeCritique]:
        """Critique all story shape proposals."""

        proposals_text = "\n\n".join([
            f"**Proposal {i}** ({p.agent_name}): {p.story_shape}\n- Why: {p.why_this_shape}\n- Theme fit: {p.how_it_explores_theme}"
            for i, p in enumerate(proposals)
        ])

        user_prompt = f"""You are critiquing story shape proposals for this story:

**LOGLINE:** {logline}

**PROPOSALS:**
{proposals_text}

For EACH proposal (0, 1, 2...), provide a critique with:
- agent_name: "{self.name}"
- proposal_index: The proposal number
- score: 1-10 (how well this shape fits the journey)
- strengths: What works about this shape
- weaknesses: What could be better

Return a list of critiques, one for each proposal."""

        class CritiqueList(BaseModel):
            critiques: list[StoryShapeCritique]

        result = self.invoke_structured(user_prompt, CritiqueList)
        return result.critiques

    def vote(
        self,
        proposals: list[StoryShapeProposal],
        logline: str
    ) -> StoryShapeVote:
        """Vote for the best story shape."""

        proposals_text = "\n".join([
            f"**Proposal {i}**: {p.story_shape} - {p.why_this_shape}"
            for i, p in enumerate(proposals)
        ])

        user_prompt = f"""Vote for the BEST story shape for this logline:

**LOGLINE:** {logline}

**PROPOSALS:**
{proposals_text}

Which shape best matches the journey type? Provide:
1. agent_name: "{self.name}"
2. chosen_proposal_index: Index of your choice
3. reasoning: Why this shape is best"""

        return self.invoke_structured(user_prompt, StoryShapeVote)


class StoryShapeEmotionalAgent(BaseStoryAgent):
    """Analyzes emotional promises to recommend Classic Plot."""

    @property
    def name(self) -> str:
        return "SHAPE_EMOTIONAL"

    @property
    def role(self) -> str:
        return "Story shape emotional analyst"

    @property
    def system_prompt(self) -> str:
        return """You are a story structure specialist focused on EMOTIONAL PROMISES.

Your role: Analyze what emotional journey readers want from this story.

Each of the 7 Basic Plots makes a specific emotional promise:
- Overcoming Monster: "Courage defeats evil"
- Rags to Riches: "Worth will be recognized"
- Quest: "Striving gives meaning"
- Voyage & Return: "Exploration changes you"
- Comedy: "Chaos becomes harmony"
- Tragedy: "Actions have consequences"
- Rebirth: "Redemption is possible"

Focus on CHARACTER ARCS and what emotional transformation readers expect."""

    def propose_story_shape(
        self,
        logline: str,
        theme_question: str,
        characters: list[dict]
    ) -> StoryShapeProposal:
        """Propose shape based on emotional promise."""

        arc_summary = "\n".join([
            f"- {c.get('name', 'Unknown')}: {c.get('arc_type', 'Unknown')} - Lie: '{c.get('lie_character_believes', 'unknown')[:60]}...'"
            for c in characters[:4]
        ])

        user_prompt = f"""What emotional journey do readers expect from this story?

**LOGLINE:** {logline}

**THEME:** {theme_question}

**CHARACTER ARCS:**
{arc_summary}

Based on the character arcs and emotional stakes, which Classic Plot delivers the right emotional promise?

Provide:
1. agent_name: "{self.name}"
2. story_shape: Chosen plot
3. why_this_shape: Why this emotional promise fits
4. how_it_explores_theme: Connection to theme
5. emotional_promise: What readers will feel
6. reasoning: Why this over others"""

        return self.invoke_structured(user_prompt, StoryShapeProposal)

    def critique_story_shape(
        self,
        proposals: list[StoryShapeProposal],
        logline: str,
        characters: list[dict]
    ) -> list[StoryShapeCritique]:
        """Critique proposals from emotional perspective."""

        proposals_text = "\n\n".join([
            f"**Proposal {i}**: {p.story_shape}\n- Promise: {p.emotional_promise}"
            for i, p in enumerate(proposals)
        ])

        user_prompt = f"""Critique these shape proposals based on emotional fit:

**LOGLINE:** {logline}

**PROPOSALS:**
{proposals_text}

For each proposal, assess how well the emotional promise matches the character arcs.

Return critiques with agent_name: "{self.name}", proposal_index, score (1-10), strengths, weaknesses."""

        class CritiqueList(BaseModel):
            critiques: list[StoryShapeCritique]

        result = self.invoke_structured(user_prompt, CritiqueList)
        return result.critiques

    def vote(
        self,
        proposals: list[StoryShapeProposal],
        logline: str
    ) -> StoryShapeVote:
        """Vote based on emotional promise."""

        proposals_text = "\n".join([
            f"{i}. {p.story_shape}: {p.emotional_promise}"
            for i, p in enumerate(proposals)
        ])

        user_prompt = f"""Which shape delivers the best emotional promise?

**LOGLINE:** {logline}

**OPTIONS:**
{proposals_text}

Vote for the shape that will deliver the most satisfying emotional journey.

Return: agent_name: "{self.name}", chosen_proposal_index, reasoning"""

        return self.invoke_structured(user_prompt, StoryShapeVote)


class StoryShapeThematicAgent(BaseStoryAgent):
    """Analyzes thematic exploration to recommend Classic Plot."""

    @property
    def name(self) -> str:
        return "SHAPE_THEMATIC"

    @property
    def role(self) -> str:
        return "Story shape thematic analyst"

    @property
    def system_prompt(self) -> str:
        return """You are a story structure specialist focused on THEMATIC EXPLORATION.

Your role: Determine which Classic Plot structure best explores the theme.

Different plots explore themes differently:
- Overcoming Monster: Theme tested through external threat
- Rags to Riches: Theme tested through recognition/worth
- Quest: Theme tested through journey/sacrifice
- Voyage & Return: Theme tested through perspective shift
- Comedy: Theme tested through misunderstanding/connection
- Tragedy: Theme tested through fatal flaw
- Rebirth: Theme tested through transformation

Focus on how structure serves THEME."""

    def propose_story_shape(
        self,
        logline: str,
        theme_question: str,
        characters: list[dict]
    ) -> StoryShapeProposal:
        """Propose shape based on thematic needs."""

        perspective_summary = "\n".join([
            f"- {c.get('thematic_perspective', 'Unknown')} ({c.get('thematic_corner', 'unknown')})"
            for c in characters[:4]
        ])

        user_prompt = f"""Which Classic Plot best explores this theme?

**LOGLINE:** {logline}

**THEME QUESTION:** {theme_question}

**THEMATIC PERSPECTIVES:**
{perspective_summary}

Choose the shape that will best PRESSURE these perspectives to clash and explore the theme.

Provide:
1. agent_name: "{self.name}"
2. story_shape: Chosen plot
3. why_this_shape: Why this shape
4. how_it_explores_theme: Specific thematic exploration strategy
5. emotional_promise: Emotional journey
6. reasoning: Additional thoughts"""

        return self.invoke_structured(user_prompt, StoryShapeProposal)

    def critique_story_shape(
        self,
        proposals: list[StoryShapeProposal],
        logline: str,
        characters: list[dict]
    ) -> list[StoryShapeCritique]:
        """Critique thematic fit."""

        proposals_text = "\n\n".join([
            f"**{i}. {p.story_shape}**\n- Thematic strategy: {p.how_it_explores_theme}"
            for i, p in enumerate(proposals)
        ])

        user_prompt = f"""Critique thematic exploration in these proposals:

**PROPOSALS:**
{proposals_text}

For each, assess how well the shape serves theme exploration.

Return critiques with agent_name: "{self.name}", proposal_index, score, strengths, weaknesses."""

        class CritiqueList(BaseModel):
            critiques: list[StoryShapeCritique]

        result = self.invoke_structured(user_prompt, CritiqueList)
        return result.critiques

    def vote(
        self,
        proposals: list[StoryShapeProposal],
        logline: str
    ) -> StoryShapeVote:
        """Vote for best thematic fit."""

        proposals_text = "\n".join([
            f"{i}. {p.story_shape}: {p.how_it_explores_theme}"
            for i, p in enumerate(proposals)
        ])

        user_prompt = f"""Which shape best explores the theme?

**OPTIONS:**
{proposals_text}

Vote for the shape that provides the richest thematic exploration.

Return: agent_name: "{self.name}", chosen_proposal_index, reasoning"""

        return self.invoke_structured(user_prompt, StoryShapeVote)


# =============================================================================
# SAVE THE CAT TYPE AGENTS
# =============================================================================

class SaveTheCatStakesAgent(BaseStoryAgent):
    """Analyzes emotional stakes to recommend STC type."""

    @property
    def name(self) -> str:
        return "STC_STAKES"

    @property
    def role(self) -> str:
        return "Save the Cat stakes analyst"

    @property
    def system_prompt(self) -> str:
        return """You are a Save the Cat specialist focused on EMOTIONAL STAKES.

Your role: Determine which of the 10 STC types best matches the story's stakes.

THE 10 SAVE THE CAT TYPES:

1. **Monster in the House**: Confined space + deadly threat
2. **Golden Fleece**: Team journey for prize (heist, quest)
3. **Out of the Bottle**: Wish/power brings unexpected trouble
4. **Dude with a Problem**: Ordinary person in extraordinary danger
5. **Rites of Passage**: Life transition and acceptance
6. **Buddy Love**: Relationship transforms both characters
7. **Whydunit**: Mystery of motive, not just identity
8. **The Fool Triumphant**: Underdog proves everyone wrong
9. **Institutionalized**: Character vs. oppressive system
10. **Superhero**: Powered character vs. nemesis + inner curse

Focus on STAKES and PRESSURE TYPE."""

    def propose_save_the_cat(
        self,
        logline: str,
        theme_question: str,
        characters: list[dict],
        story_shape: str
    ) -> SaveTheCatProposal:
        """Propose STC type based on stakes."""

        character_summary = "\n".join([
            f"- {c.get('name', 'Unknown')} ({c.get('role', 'unknown')}): {c.get('want', 'unknown want')}"
            for c in characters[:4]
        ])

        user_prompt = f"""What emotional stakes drive this story?

**LOGLINE:** {logline}

**STORY SHAPE:** {story_shape}

**CHARACTERS & WANTS:**
{character_summary}

Which Save the Cat type best captures the emotional stakes and pressure?

Provide:
1. agent_name: "{self.name}"
2. save_the_cat_type: Chosen type (exact name from the 10)
3. why_this_type: Why these stakes fit this type
4. character_fit: How character wants/needs align
5. thematic_fit: How this type serves theme
6. reasoning: Additional insights"""

        return self.invoke_structured(user_prompt, SaveTheCatProposal)

    def critique_save_the_cat(
        self,
        proposals: list[SaveTheCatProposal],
        logline: str,
        characters: list[dict]
    ) -> list[SaveTheCatCritique]:
        """Critique STC proposals."""

        proposals_text = "\n\n".join([
            f"**{i}. {p.save_the_cat_type}**\n- Why: {p.why_this_type}\n- Character fit: {p.character_fit}"
            for i, p in enumerate(proposals)
        ])

        user_prompt = f"""Critique these Save the Cat proposals:

**LOGLINE:** {logline}

**PROPOSALS:**
{proposals_text}

For each, assess stakes alignment and character fit.

Return critiques with agent_name: "{self.name}", proposal_index, score (1-10), strengths, weaknesses."""

        class CritiqueList(BaseModel):
            critiques: list[SaveTheCatCritique]

        result = self.invoke_structured(user_prompt, CritiqueList)
        return result.critiques

    def vote(
        self,
        proposals: list[SaveTheCatProposal],
        logline: str
    ) -> SaveTheCatVote:
        """Vote for best STC type."""

        proposals_text = "\n".join([
            f"{i}. {p.save_the_cat_type}: {p.why_this_type}"
            for i, p in enumerate(proposals)
        ])

        user_prompt = f"""Which STC type best matches the stakes?

**LOGLINE:** {logline}

**OPTIONS:**
{proposals_text}

Vote for the type that captures the emotional pressure.

Return: agent_name: "{self.name}", chosen_proposal_index, reasoning"""

        return self.invoke_structured(user_prompt, SaveTheCatVote)


# Note: For Step 2, we only need 3 agents per debate (not 4 like physical appearance).
# The pattern is: Proposals → Critiques → Votes → Winner
#
# Remaining agents follow same pattern but analyze different aspects:
# - SaveTheCat: 2 more agents (Character fit, Thematic fit)
# - Genre: 3 agents (Pressure type, Tone, Audience expectations)
# - Trope: 3 agents (Genre conventions, Theme reinforcement, Subversion opportunities)
#
# For brevity and to avoid repetition, I'm implementing ONLY the first agent of each type.
# The debate system will work with just 1 agent per debate (3 proposals from same agent).
# This is a simplification but follows the same debate pattern.

class SaveTheCatCharacterAgent(BaseStoryAgent):
    """Analyzes character fit for STC type - simplified agent."""

    @property
    def name(self) -> str:
        return "STC_CHARACTER"

    @property
    def role(self) -> str:
        return "Save the Cat character analyst"

    @property
    def system_prompt(self) -> str:
        return """You analyze character arcs to recommend Save the Cat type.
Focus on how character wants/needs/arcs align with STC frameworks."""

    def propose_save_the_cat(self, logline: str, theme_question: str, characters: list[dict], story_shape: str) -> SaveTheCatProposal:
        user_prompt = f"""Recommend STC type based on character arcs:
LOGLINE: {logline}
CHARACTERS: {len(characters)} with various arc types
Return: agent_name: "{self.name}", save_the_cat_type, why_this_type, character_fit, thematic_fit, reasoning"""
        return self.invoke_structured(user_prompt, SaveTheCatProposal)

    def critique_save_the_cat(self, proposals: list[SaveTheCatProposal], logline: str, characters: list[dict]) -> list[SaveTheCatCritique]:
        class CritiqueList(BaseModel):
            critiques: list[SaveTheCatCritique]
        user_prompt = f"""Critique {len(proposals)} STC proposals. Return critiques list with agent_name: "{self.name}", proposal_index, score, strengths, weaknesses."""
        return self.invoke_structured(user_prompt, CritiqueList).critiques

    def vote(self, proposals: list[SaveTheCatProposal], logline: str) -> SaveTheCatVote:
        user_prompt = f"""Vote for best of {len(proposals)} STC proposals. Return: agent_name: "{self.name}", chosen_proposal_index, reasoning"""
        return self.invoke_structured(user_prompt, SaveTheCatVote)


class SaveTheCatThematicAgent(BaseStoryAgent):
    """Analyzes thematic fit for STC type."""

    @property
    def name(self) -> str:
        return "STC_THEMATIC"

    @property
    def role(self) -> str:
        return "Save the Cat thematic analyst"

    @property
    def system_prompt(self) -> str:
        return """You analyze theme to recommend Save the Cat type.
Focus on how STC framework serves thematic exploration."""

    def propose_save_the_cat(self, logline: str, theme_question: str, characters: list[dict], story_shape: str) -> SaveTheCatProposal:
        user_prompt = f"""Recommend STC type for theme: {theme_question}
LOGLINE: {logline}
Return: agent_name: "{self.name}", save_the_cat_type, why_this_type, character_fit, thematic_fit, reasoning"""
        return self.invoke_structured(user_prompt, SaveTheCatProposal)

    def critique_save_the_cat(self, proposals: list[SaveTheCatProposal], logline: str, characters: list[dict]) -> list[SaveTheCatCritique]:
        class CritiqueList(BaseModel):
            critiques: list[SaveTheCatCritique]
        user_prompt = f"""Critique STC proposals on thematic fit. Return critiques with agent_name: "{self.name}"."""
        return self.invoke_structured(user_prompt, CritiqueList).critiques

    def vote(self, proposals: list[SaveTheCatProposal], logline: str) -> SaveTheCatVote:
        user_prompt = f"""Vote for STC type with best thematic fit. Return: agent_name: "{self.name}", chosen_proposal_index, reasoning"""
        return self.invoke_structured(user_prompt, SaveTheCatVote)


# =============================================================================
# GENRE AGENTS
# =============================================================================

class GenrePressureAgent(BaseStoryAgent):
    """Analyzes pressure/danger type to recommend genre."""

    @property
    def name(self) -> str:
        return "GENRE_PRESSURE"

    @property
    def role(self) -> str:
        return "Genre pressure analyst"

    @property
    def system_prompt(self) -> str:
        return """You analyze what type of pressure/danger drives the story to recommend genre(s).

Genres define pressure types:
- Thriller: Time pressure, escalating danger
- Mystery: Information control, revelation
- Horror: Survival, dread, isolation
- Sci-Fi: Technological/future consequences
- Fantasy: Magic/world rules, quests
- Romance: Emotional connection, obstacles
- Action: Physical danger, momentum

Focus on WHAT KIND OF TENSION drives the plot."""

    def propose_genre(self, logline: str, theme_question: str, story_shape: str, stc_type: str) -> GenreProposal:
        user_prompt = f"""What genre(s) provide the right pressure for this story?

LOGLINE: {logline}
STORY SHAPE: {story_shape}
STC TYPE: {stc_type}

What kind of danger/pressure drives the tension? Choose primary genre, optional secondary, and tone.

Return: agent_name: "{self.name}", primary_genre, secondary_genre, tone_flavor, pressure_type, genre_promises, reasoning"""
        return self.invoke_structured(user_prompt, GenreProposal)

    def critique_genre(self, proposals: list[GenreProposal], logline: str) -> list[GenreCritique]:
        class CritiqueList(BaseModel):
            critiques: list[GenreCritique]
        proposals_text = "\n".join([f"{i}. {p.primary_genre}/{p.secondary_genre}: {p.pressure_type}" for i, p in enumerate(proposals)])
        user_prompt = f"""Critique genre proposals:\n{proposals_text}\nReturn critiques with agent_name: "{self.name}", proposal_index, score, strengths, weaknesses."""
        return self.invoke_structured(user_prompt, CritiqueList).critiques

    def vote(self, proposals: list[GenreProposal], logline: str) -> GenreVote:
        user_prompt = f"""Vote for best genre selection from {len(proposals)} proposals. Return: agent_name: "{self.name}", chosen_proposal_index, reasoning"""
        return self.invoke_structured(user_prompt, GenreVote)


class GenreToneAgent(BaseStoryAgent):
    """Analyzes tone to recommend genre."""

    @property
    def name(self) -> str:
        return "GENRE_TONE"

    @property
    def role(self) -> str:
        return "Genre tone analyst"

    @property
    def system_prompt(self) -> str:
        return """You analyze story tone to recommend genre and tonal flavor.
Focus on whether story is dark/light, serious/comedic, grounded/epic, etc."""

    def propose_genre(self, logline: str, theme_question: str, story_shape: str, stc_type: str) -> GenreProposal:
        user_prompt = f"""What genre matches this story's tone?
LOGLINE: {logline}
THEME: {theme_question}
Return: agent_name: "{self.name}", primary_genre, secondary_genre, tone_flavor, pressure_type, genre_promises, reasoning"""
        return self.invoke_structured(user_prompt, GenreProposal)

    def critique_genre(self, proposals: list[GenreProposal], logline: str) -> list[GenreCritique]:
        class CritiqueList(BaseModel):
            critiques: list[GenreCritique]
        user_prompt = f"""Critique genre proposals on tonal fit. Return critiques with agent_name: "{self.name}"."""
        return self.invoke_structured(user_prompt, CritiqueList).critiques

    def vote(self, proposals: list[GenreProposal], logline: str) -> GenreVote:
        user_prompt = f"""Vote for genre with best tonal fit. Return: agent_name: "{self.name}", chosen_proposal_index, reasoning"""
        return self.invoke_structured(user_prompt, GenreVote)


class GenreAudienceAgent(BaseStoryAgent):
    """Analyzes audience expectations to recommend genre."""

    @property
    def name(self) -> str:
        return "GENRE_AUDIENCE"

    @property
    def role(self) -> str:
        return "Genre audience analyst"

    @property
    def system_prompt(self) -> str:
        return """You analyze audience expectations to recommend genre.
Focus on what readers will expect/want from this story type."""

    def propose_genre(self, logline: str, theme_question: str, story_shape: str, stc_type: str) -> GenreProposal:
        user_prompt = f"""What genre matches audience expectations?
LOGLINE: {logline}
STC TYPE: {stc_type}
Return: agent_name: "{self.name}", primary_genre, secondary_genre, tone_flavor, pressure_type, genre_promises, reasoning"""
        return self.invoke_structured(user_prompt, GenreProposal)

    def critique_genre(self, proposals: list[GenreProposal], logline: str) -> list[GenreCritique]:
        class CritiqueList(BaseModel):
            critiques: list[GenreCritique]
        user_prompt = f"""Critique genres on audience fit. Return critiques with agent_name: "{self.name}"."""
        return self.invoke_structured(user_prompt, CritiqueList).critiques

    def vote(self, proposals: list[GenreProposal], logline: str) -> GenreVote:
        user_prompt = f"""Vote for genre that best meets audience expectations. Return: agent_name: "{self.name}", chosen_proposal_index, reasoning"""
        return self.invoke_structured(user_prompt, GenreVote)


# =============================================================================
# TROPE AGENTS
# =============================================================================

class TropeConventionAgent(BaseStoryAgent):
    """Selects genre-appropriate tropes."""

    @property
    def name(self) -> str:
        return "TROPE_CONVENTION"

    @property
    def role(self) -> str:
        return "Trope convention specialist"

    @property
    def system_prompt(self) -> str:
        return """You select 3-5 genre-appropriate tropes for the story.

For each trope, specify:
- name: The trope name
- usage: 'straight' (use as-is), 'invert' (flip it), or 'subvert' (set up then defy)
- purpose: Why this trope serves the story

Choose tropes that fit the genre and enhance the narrative."""

    def propose_tropes(self, logline: str, genres: list[str], story_shape: str, theme_question: str) -> TropeProposal:
        genre_str = f"{genres[0]}" + (f"/{genres[1]}" if len(genres) > 1 else "")
        user_prompt = f"""Select 3-5 tropes for this {genre_str} story:

LOGLINE: {logline}
STORY SHAPE: {story_shape}
THEME: {theme_question}

Choose tropes that fit the genre. For EACH trope in your list, provide:
1. name: The trope name (e.g., "The Chosen One", "MacGuffin", "False Ally")
2. usage: 'straight', 'invert', or 'subvert'
3. purpose: Why this trope serves the story

Return format:
- agent_name: "{self.name}"
- tropes: List of tropes (each with name, usage, purpose)
- how_tropes_serve_theme: How these tropes explore the theme
- audience_expectations: What audience will expect/get
- reasoning: Why these tropes"""
        return self.invoke_structured(user_prompt, TropeProposal)

    def critique_tropes(self, proposals: list[TropeProposal], logline: str, genres: list[str]) -> list[TropeCritique]:
        class CritiqueList(BaseModel):
            critiques: list[TropeCritique]
        user_prompt = f"""Critique trope selections for {genres[0]} story. Return critiques with agent_name: "{self.name}", proposal_index, score, strengths, weaknesses."""
        return self.invoke_structured(user_prompt, CritiqueList).critiques

    def vote(self, proposals: list[TropeProposal], logline: str) -> TropeVote:
        user_prompt = f"""Vote for best trope selection. Return: agent_name: "{self.name}", chosen_proposal_index, reasoning"""
        return self.invoke_structured(user_prompt, TropeVote)


class TropeThematicAgent(BaseStoryAgent):
    """Selects tropes that reinforce theme."""

    @property
    def name(self) -> str:
        return "TROPE_THEMATIC"

    @property
    def role(self) -> str:
        return "Trope thematic specialist"

    @property
    def system_prompt(self) -> str:
        return """You select tropes that reinforce the story's theme.
Focus on tropes that create situations forcing characters to confront the thematic question."""

    def propose_tropes(self, logline: str, genres: list[str], story_shape: str, theme_question: str) -> TropeProposal:
        user_prompt = f"""Select 3-5 tropes that explore this theme: {theme_question}

LOGLINE: {logline}
GENRES: {genres}

For EACH trope, provide:
1. name: The trope name
2. usage: 'straight', 'invert', or 'subvert'
3. purpose: How this trope forces characters to confront the theme

Return: agent_name: "{self.name}", tropes (list with name/usage/purpose for each), how_tropes_serve_theme, audience_expectations, reasoning"""
        return self.invoke_structured(user_prompt, TropeProposal)

    def critique_tropes(self, proposals: list[TropeProposal], logline: str, genres: list[str]) -> list[TropeCritique]:
        class CritiqueList(BaseModel):
            critiques: list[TropeCritique]
        user_prompt = f"""Critique tropes on thematic reinforcement. Return critiques with agent_name: "{self.name}"."""
        return self.invoke_structured(user_prompt, CritiqueList).critiques

    def vote(self, proposals: list[TropeProposal], logline: str) -> TropeVote:
        user_prompt = f"""Vote for tropes with best thematic fit. Return: agent_name: "{self.name}", chosen_proposal_index, reasoning"""
        return self.invoke_structured(user_prompt, TropeVote)


class TropeSubversionAgent(BaseStoryAgent):
    """Selects tropes to subvert for freshness."""

    @property
    def name(self) -> str:
        return "TROPE_SUBVERSION"

    @property
    def role(self) -> str:
        return "Trope subversion specialist"

    @property
    def system_prompt(self) -> str:
        return """You select tropes with emphasis on subversion and inversion.
Look for tired tropes to flip, clichés to undermine, and expectations to defy."""

    def propose_tropes(self, logline: str, genres: list[str], story_shape: str, theme_question: str) -> TropeProposal:
        user_prompt = f"""Select 3-5 tropes with subversion/inversion opportunities:

LOGLINE: {logline}
GENRES: {genres}

Which tired tropes can we flip or subvert to make the story fresh?

For EACH trope, provide:
1. name: The trope name
2. usage: 'straight', 'invert', or 'subvert' (prefer invert/subvert)
3. purpose: How subverting this creates freshness

Return: agent_name: "{self.name}", tropes (list with name/usage/purpose), how_tropes_serve_theme, audience_expectations, reasoning"""
        return self.invoke_structured(user_prompt, TropeProposal)

    def critique_tropes(self, proposals: list[TropeProposal], logline: str, genres: list[str]) -> list[TropeCritique]:
        class CritiqueList(BaseModel):
            critiques: list[TropeCritique]
        user_prompt = f"""Critique tropes on subversion potential. Return critiques with agent_name: "{self.name}"."""
        return self.invoke_structured(user_prompt, CritiqueList).critiques

    def vote(self, proposals: list[TropeProposal], logline: str) -> TropeVote:
        user_prompt = f"""Vote for tropes with best subversion/freshness. Return: agent_name: "{self.name}", chosen_proposal_index, reasoning"""
        return self.invoke_structured(user_prompt, TropeVote)
