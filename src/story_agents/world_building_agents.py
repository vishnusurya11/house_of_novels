"""
World Building Agents for Step 3B: World Context Generation.

4 specialized agents each handle specific world-building categories.
NO DEBATE - each agent generates its categories independently.

1. WorldSociologistAgent - Daily life, Social structure
2. WorldEconomistAgent - Economy, Jobs, Trade
3. WorldPoliticianAgent - Government, Law, Military
4. WorldCulturalistAgent - Culture, Religion, Entertainment
"""

from src.story_agents.base_story_agent import BaseStoryAgent
from src.story_schemas import (
    DailyLifeSchema,
    SocialStructureSchema,
    GovernmentLawSchema,
    EconomySchema,
    EducationHealthSchema,
    EntertainmentSchema,
    ReligionBeliefsSchema,
    CultureCustomsSchema,
)


# =============================================================================
# World Building Agents (Specialized Generators - No Debate)
# =============================================================================

class WorldSociologistAgent(BaseStoryAgent):
    """
    Generates daily life and social structure details.

    Specializes in:
    - Daily life patterns (food, clothing, shelter)
    - Social hierarchies (classes, mobility, inequality)
    - Work and labor (common jobs, guilds, professions)
    """

    METHODOLOGY_NAME = "World Sociology"
    METHODOLOGY_SOURCE = "Social structure and daily life analysis"

    @property
    def name(self) -> str:
        return "WORLD_SOCIOLOGIST"

    @property
    def role(self) -> str:
        return "World Sociologist"

    @property
    def system_prompt(self) -> str:
        return """You are a world sociologist who understands how societies function.

You specialize in:
- Daily life patterns (food, clothing, shelter, routines)
- Social hierarchies (classes, mobility, inequality)
- Work and labor (common jobs, guilds, professions)

Create details that feel LIVED-IN and CONSISTENT with the world setting.
Think about how ordinary people spend their days.
Consider how the world's history and geography shape daily life.

Your details should feel authentic and grounded - things readers can imagine experiencing."""

    def generate_daily_life(
        self,
        setting_prompt: str,
        deck_of_worlds: dict,
        story_context: str,
    ) -> DailyLifeSchema:
        """Generate daily life details."""
        prompt = f"""Generate DAILY LIFE details for this world:

WORLD SETTING: {setting_prompt}

DECK OF WORLDS:
- Location: {deck_of_worlds.get('location', 'unknown')}
- Origin: {deck_of_worlds.get('origin', 'unknown')}
- Current State: {deck_of_worlds.get('attribute', 'unknown')}
- Hook: {deck_of_worlds.get('advent', 'unknown')}

STORY CONTEXT: {story_context}

Generate realistic daily life details:

1. COMMON FOODS (5-7 items):
   - What grows/lives in this environment?
   - What do poor people eat vs rich?
   - Any signature dishes or staples?

2. EATING CUSTOMS:
   - Do people eat together or alone?
   - Street food? Formal meals? Communal eating?
   - Any rituals around food?

3. CLOTHING STYLES:
   - What do common people wear?
   - How do rich people dress differently?
   - What materials are available?
   - How does the environment affect clothing?

4. SHELTER TYPES:
   - What kind of homes do common people live in?
   - How do wealthy people's homes differ?
   - Building materials? Architecture style?

Make these details SPECIFIC to this world's environment and history."""

        return self.invoke_structured(prompt, DailyLifeSchema, max_tokens=1200)

    def generate_social_structure(
        self,
        setting_prompt: str,
        deck_of_worlds: dict,
        story_context: str,
    ) -> SocialStructureSchema:
        """Generate social structure details."""
        prompt = f"""Generate SOCIAL STRUCTURE details for this world:

WORLD SETTING: {setting_prompt}

DECK OF WORLDS:
- Location: {deck_of_worlds.get('location', 'unknown')}
- Origin: {deck_of_worlds.get('origin', 'unknown')}
- Current State: {deck_of_worlds.get('attribute', 'unknown')}

STORY CONTEXT: {story_context}

Generate social hierarchy details:

1. CLASS SYSTEM:
   - How big is the gap between rich and poor?
   - Can people move between classes? How?
   - What divides people (wealth, birth, skill, magic)?

2. COMMON JOBS (5-7 typical occupations):
   - What do most ordinary people do for work?
   - Jobs specific to this environment

3. DESIRABLE JOBS (3-5 prestigious ones):
   - What jobs do people aspire to?
   - Why are they respected?

4. LOWLY JOBS (3-5 looked-down-upon ones):
   - What work is considered shameful?
   - Who does these jobs?

5. GUILDS/ORGANIZATIONS:
   - What important groups exist?
   - Trade guilds? Religious orders? Criminal networks?
   - Consider the "crime family" from the setting

Make these reflect how the Origin and Current State shaped society."""

        return self.invoke_structured(prompt, SocialStructureSchema, max_tokens=1200)


class WorldEconomistAgent(BaseStoryAgent):
    """
    Generates economy and trade details.

    Specializes in:
    - Currency and money systems
    - Trade goods and commerce
    - Natural resources
    - Taxation and wealth distribution
    """

    METHODOLOGY_NAME = "World Economics"
    METHODOLOGY_SOURCE = "Economic systems and trade analysis"

    @property
    def name(self) -> str:
        return "WORLD_ECONOMIST"

    @property
    def role(self) -> str:
        return "World Economist"

    @property
    def system_prompt(self) -> str:
        return """You are a world economist who understands how economies function.

You specialize in:
- Currency and money systems
- Trade goods and commerce
- Natural resources
- Taxation and wealth distribution

Create economic details that make SENSE for the world's technology and culture.
Think about what's valuable, what's scarce, and who controls it.
Consider how power and wealth intersect.

Your details should create opportunities for conflict and story."""

    def generate_economy(
        self,
        setting_prompt: str,
        deck_of_worlds: dict,
        story_context: str,
    ) -> EconomySchema:
        """Generate economy details."""
        prompt = f"""Generate ECONOMY details for this world:

WORLD SETTING: {setting_prompt}

DECK OF WORLDS:
- Location: {deck_of_worlds.get('location', 'unknown')}
- Origin: {deck_of_worlds.get('origin', 'unknown')}
- Current State: {deck_of_worlds.get('attribute', 'unknown')}
- Hook: {deck_of_worlds.get('advent', 'unknown')}

STORY CONTEXT: {story_context}

Generate economic details:

1. CURRENCY:
   - What do people use as money?
   - Is it coins, paper, goods, something else?
   - What's it called?

2. TRADE GOODS (major items traded):
   - What does this region produce?
   - What do they import?
   - Any illegal trade? (Consider the crime family)

3. RESOURCES (natural resources):
   - What's abundant here?
   - What's scarce and valuable?
   - How do resources shape the economy?

4. TAXATION:
   - Who collects taxes? How?
   - Is there corruption?
   - How do people feel about it?

Connect these to the current power structure (crime family headquarters)."""

        return self.invoke_structured(prompt, EconomySchema, max_tokens=1000)


class WorldPoliticianAgent(BaseStoryAgent):
    """
    Generates government, law, and military details.

    Specializes in:
    - Government systems (who holds power, how)
    - Law enforcement and justice
    - Courts and punishment
    - Military and conflicts
    """

    METHODOLOGY_NAME = "World Politics"
    METHODOLOGY_SOURCE = "Power structures and governance analysis"

    @property
    def name(self) -> str:
        return "WORLD_POLITICIAN"

    @property
    def role(self) -> str:
        return "World Politician"

    @property
    def system_prompt(self) -> str:
        return """You are a world politician who understands power structures.

You specialize in:
- Government systems (who holds power, how they got it)
- Law enforcement and justice
- Courts and punishment
- Military and conflicts

Create political details that create TENSION and OPPORTUNITY for story.
Power is never simple - there are always factions, grudges, and ambitions.
Consider how the current crisis affects governance.

Your details should feel believable and create dramatic potential."""

    def generate_government_law(
        self,
        setting_prompt: str,
        deck_of_worlds: dict,
        story_context: str,
    ) -> GovernmentLawSchema:
        """Generate government and law details."""
        prompt = f"""Generate GOVERNMENT & LAW details for this world:

WORLD SETTING: {setting_prompt}

DECK OF WORLDS:
- Location: {deck_of_worlds.get('location', 'unknown')}
- Origin: {deck_of_worlds.get('origin', 'unknown')}
- Current State: {deck_of_worlds.get('attribute', 'unknown')} (IMPORTANT: This is now headquarters of a crime family!)
- Hook: {deck_of_worlds.get('advent', 'unknown')} (IMPORTANT: People are rioting!)

STORY CONTEXT: {story_context}

Generate political details:

1. GOVERNMENT TYPE:
   - Who officially holds power?
   - But who REALLY controls things? (Crime family?)
   - Is there a puppet government?

2. LAW ENFORCEMENT:
   - Who enforces laws? Official police? Crime family thugs?
   - How corrupt is law enforcement?
   - How do common people deal with crime?

3. COURTS & TRIALS:
   - Is there a justice system?
   - Is it fair? Bribable? Controlled by the crime family?
   - How do the powerful avoid justice?

4. PUNISHMENTS (common ones):
   - What happens to criminals?
   - Are punishments harsh? Public?
   - Any unique punishments for this world?

5. MILITARY:
   - Is there a formal army?
   - Private militias? Crime family enforcers?
   - What conflicts are brewing? (Connect to the riots)

Remember: This is a crime family headquarters with rioting - the law is complicated here."""

        return self.invoke_structured(prompt, GovernmentLawSchema, max_tokens=1200)


class WorldCulturalistAgent(BaseStoryAgent):
    """
    Generates culture, religion, and entertainment details.

    Specializes in:
    - Religion and spirituality
    - Entertainment and leisure
    - Cultural customs and taboos
    - Education and knowledge
    """

    METHODOLOGY_NAME = "World Culture"
    METHODOLOGY_SOURCE = "Cultural anthropology and belief systems"

    @property
    def name(self) -> str:
        return "WORLD_CULTURALIST"

    @property
    def role(self) -> str:
        return "World Culturalist"

    @property
    def system_prompt(self) -> str:
        return """You are a world culturalist who understands beliefs and traditions.

You specialize in:
- Religion and spirituality
- Entertainment and leisure
- Cultural customs and taboos
- Education and knowledge

Create cultural details that feel DEEP and CONSISTENT.
Culture emerges from history, environment, and shared experience.
The "vanished people" origin should leave traces in current culture.

Your details should enrich the world and provide story opportunities."""

    def generate_education_health(
        self,
        setting_prompt: str,
        deck_of_worlds: dict,
        story_context: str,
    ) -> EducationHealthSchema:
        """Generate education and health details."""
        prompt = f"""Generate EDUCATION & HEALTH details for this world:

WORLD SETTING: {setting_prompt}

DECK OF WORLDS:
- Location: {deck_of_worlds.get('location', 'unknown')}
- Origin: {deck_of_worlds.get('origin', 'unknown')} (Home of a vanished people!)
- Current State: {deck_of_worlds.get('attribute', 'unknown')}

STORY CONTEXT: {story_context}

Generate details:

1. EDUCATION SYSTEM:
   - How do people learn? Schools? Apprenticeships?
   - Who gets educated? (Rich only? Everyone?)
   - Literacy rate? What's the attitude toward learning?
   - Any lost knowledge from the vanished people?

2. MEDICINE:
   - Is healthcare available? To whom?
   - Is it effective?
   - How expensive?

3. HEALERS:
   - Who provides healing? Doctors? Herbalists? Magic?
   - Are they respected? Feared?
   - Any unique healing traditions?

4. COMMON AILMENTS (health issues):
   - What diseases are common here? (Swamp environment!)
   - Environmental health problems?
   - Occupational hazards?

Connect these to the swamp environment and current social upheaval."""

        return self.invoke_structured(prompt, EducationHealthSchema, max_tokens=1000)

    def generate_entertainment(
        self,
        setting_prompt: str,
        deck_of_worlds: dict,
        story_context: str,
    ) -> EntertainmentSchema:
        """Generate entertainment details."""
        prompt = f"""Generate ENTERTAINMENT details for this world:

WORLD SETTING: {setting_prompt}

DECK OF WORLDS:
- Location: {deck_of_worlds.get('location', 'unknown')}
- Origin: {deck_of_worlds.get('origin', 'unknown')}
- Current State: {deck_of_worlds.get('attribute', 'unknown')}
- Hook: {deck_of_worlds.get('advent', 'unknown')}

STORY CONTEXT: {story_context}

Generate entertainment details:

1. POOR ENTERTAINMENT (what common people do for fun):
   - Free or cheap activities
   - Community gatherings?
   - How do they escape their troubles?

2. RICH ENTERTAINMENT (what wealthy do for fun):
   - Expensive pleasures
   - Exclusive activities
   - How do they display status through leisure?

3. FESTIVALS (major celebrations):
   - What do people celebrate?
   - Any festivals from the vanished people still observed?
   - How do current tensions affect celebrations?

4. ART FORMS (popular art, music, stories):
   - What kind of music is popular?
   - Storytelling traditions?
   - Visual arts? Performance?
   - Any forbidden or subversive art (related to rioting)?

Consider how entertainment reflects the divide between rich and poor."""

        return self.invoke_structured(prompt, EntertainmentSchema, max_tokens=1000)

    def generate_religion_beliefs(
        self,
        setting_prompt: str,
        deck_of_worlds: dict,
        story_context: str,
    ) -> ReligionBeliefsSchema:
        """Generate religion and beliefs details."""
        prompt = f"""Generate RELIGION & BELIEFS details for this world:

WORLD SETTING: {setting_prompt}

DECK OF WORLDS:
- Location: {deck_of_worlds.get('location', 'unknown')}
- Origin: {deck_of_worlds.get('origin', 'unknown')} (Home of a VANISHED PEOPLE!)
- Current State: {deck_of_worlds.get('attribute', 'unknown')}

STORY CONTEXT: {story_context}

Generate religion details:

1. MAIN RELIGION:
   - What do most people believe?
   - Is it organized? Personal?
   - How does it interact with the crime family's power?

2. GODS/DEITIES (if any):
   - What gods do people worship?
   - Any gods from the vanished people?
   - Are the gods active or distant?

3. TEMPLES & WORSHIP:
   - Where do people worship?
   - When? How?
   - Role of religious leaders?

4. SUPERSTITIONS (common beliefs):
   - What do people fear? Avoid?
   - Lucky/unlucky things?
   - Beliefs about the swamp, the vanished people, etc.

5. TABOOS (forbidden things):
   - What's absolutely forbidden?
   - Social taboos vs religious taboos?
   - What happens if you break them?

The vanished people should leave spiritual traces - ghost stories, old shrines, warnings."""

        return self.invoke_structured(prompt, ReligionBeliefsSchema, max_tokens=1000)

    def generate_culture_customs(
        self,
        setting_prompt: str,
        deck_of_worlds: dict,
        story_context: str,
    ) -> CultureCustomsSchema:
        """Generate culture and customs details."""
        prompt = f"""Generate CULTURE & CUSTOMS details for this world:

WORLD SETTING: {setting_prompt}

DECK OF WORLDS:
- Location: {deck_of_worlds.get('location', 'unknown')}
- Origin: {deck_of_worlds.get('origin', 'unknown')}
- Current State: {deck_of_worlds.get('attribute', 'unknown')}

STORY CONTEXT: {story_context}

Generate cultural details:

1. SOCIAL RULES (important etiquette):
   - What rules must people follow?
   - Rules for addressing superiors?
   - Guest customs? Business customs?
   - Rules specific to crime family territory?

2. GESTURES OF RESPECT:
   - How do people show respect?
   - Bowing? Titles? Gifts?
   - How do you show respect to the crime family?

3. RUDE GESTURES:
   - What's considered offensive?
   - Insults specific to this culture?
   - What could get you in serious trouble?

4. FAMILY STRUCTURE:
   - Nuclear families? Extended clans?
   - Who leads the household?
   - Inheritance? Children's roles?
   - How does the crime family model affect other families?

5. NAMING CONVENTIONS:
   - How do names work?
   - Family names? Titles?
   - Any traditions from the vanished people?

These customs should feel organic to a place controlled by organized crime."""

        return self.invoke_structured(prompt, CultureCustomsSchema, max_tokens=1000)
