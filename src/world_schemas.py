"""
World Building Schemas for Step 4 World Generation

These schemas define the structure for comprehensive world building,
covering daily life, social structure, economy, government, education,
entertainment, religion, and cultural customs.
"""

from pydantic import BaseModel, Field


# =============================================================================
# 1. DAILY LIFE
# =============================================================================

class DailyLife(BaseModel):
    """Daily life details for the world."""
    common_foods: list[str] = Field(
        ...,
        description="List of 5-7 common foods people eat in this world",
    )
    eating_customs: str = Field(
        ...,
        description="Paragraph describing eating customs, meal traditions, and food culture (150-250 words)",
    )
    clothing_styles: str = Field(
        ...,
        description="Paragraph describing typical clothing for different classes and occasions (150-250 words)",
    )
    shelter_types: str = Field(
        ...,
        description="Paragraph describing typical housing and shelters for different social classes (150-250 words)",
    )


# =============================================================================
# 2. SOCIAL STRUCTURE
# =============================================================================

class SocialStructure(BaseModel):
    """Social hierarchy and organization."""
    class_system: str = Field(
        ...,
        description="Paragraph describing the class system, wealth gaps, and social mobility (200-300 words)",
    )
    common_jobs: list[str] = Field(
        ...,
        description="List of 5-7 typical jobs most people have",
    )
    desirable_jobs: list[str] = Field(
        ...,
        description="List of 3-5 prestigious or desirable occupations",
    )
    lowly_jobs: list[str] = Field(
        ...,
        description="List of 3-5 jobs considered undesirable or low-status",
    )
    guilds_organizations: list[str] = Field(
        ...,
        description="List of 3-5 important guilds, organizations, or factions",
    )


# =============================================================================
# 3. ECONOMY
# =============================================================================

class Economy(BaseModel):
    """Economic system and trade."""
    currency: str = Field(
        ...,
        description="Name of the currency used (e.g., 'Penance Stones', 'Gold Crowns')",
    )
    trade_goods: list[str] = Field(
        ...,
        description="List of 4-6 major trade goods or exports",
    )
    resources: list[str] = Field(
        ...,
        description="List of 3-5 important natural resources",
    )
    taxation: str = Field(
        ...,
        description="Paragraph describing taxation system and how it affects people (100-200 words)",
    )


# =============================================================================
# 4. GOVERNMENT & LAW
# =============================================================================

class GovernmentLaw(BaseModel):
    """Government structure and legal system."""
    government_type: str = Field(
        ...,
        description="Type of government (e.g., 'Oligarchy', 'Monarchy', 'Democracy')",
    )
    law_enforcement: str = Field(
        ...,
        description="Who enforces laws and maintains order",
    )
    courts_trials: str = Field(
        ...,
        description="How justice is administered and trials conducted",
    )
    punishments: list[str] = Field(
        ...,
        description="List of 3-5 common punishments for crimes",
    )
    military: str = Field(
        ...,
        description="Description of military or defense forces",
    )


# =============================================================================
# 5. EDUCATION & HEALTH
# =============================================================================

class EducationHealth(BaseModel):
    """Education and healthcare systems."""
    education_system: str = Field(
        ...,
        description="Paragraph describing how people learn, literacy rates, and attitudes toward education (200-300 words)",
    )
    medicine: str = Field(
        ...,
        description="Paragraph describing healthcare availability, effectiveness, and costs (150-250 words)",
    )
    healers: str = Field(
        ...,
        description="Paragraph describing who provides healing and unique healing traditions (150-250 words)",
    )
    common_ailments: list[str] = Field(
        ...,
        description="List of 4-6 common diseases or health problems",
    )


# =============================================================================
# 6. ENTERTAINMENT
# =============================================================================

class Entertainment(BaseModel):
    """Entertainment and leisure activities."""
    poor_entertainment: list[str] = Field(
        ...,
        description="List of 3-4 ways poor people entertain themselves (each item 20-50 words)",
    )
    rich_entertainment: list[str] = Field(
        ...,
        description="List of 3-4 ways wealthy people entertain themselves (each item 20-50 words)",
    )
    festivals: list[str] = Field(
        ...,
        description="List of 2-3 major festivals or celebrations (each item 30-80 words)",
    )
    art_forms: list[str] = Field(
        ...,
        description="List of 3-4 important art forms (music, storytelling, visual arts, etc., each item 20-50 words)",
    )


# =============================================================================
# 7. RELIGION & BELIEFS
# =============================================================================

class ReligionBeliefs(BaseModel):
    """Religious and spiritual beliefs."""
    main_religion: str = Field(
        ...,
        description="Name of the primary religion or belief system",
    )
    gods_deities: list[str] = Field(
        ...,
        description="List of 2-3 important gods, deities, or spiritual entities",
    )
    temples_worship: str = Field(
        ...,
        description="Description of main temples or places of worship",
    )
    superstitions: list[str] = Field(
        ...,
        description="List of 3-4 common superstitions or folk beliefs",
    )
    taboos: list[str] = Field(
        ...,
        description="List of 3-4 major cultural or religious taboos",
    )


# =============================================================================
# 8. CULTURE & CUSTOMS
# =============================================================================

class CultureCustoms(BaseModel):
    """Cultural norms and social customs."""
    social_rules: list[str] = Field(
        ...,
        description="List of 4-5 important social rules or etiquette guidelines",
    )
    gestures_respect: str = Field(
        ...,
        description="Description of gestures or actions showing respect (50-100 words)",
    )
    gestures_rudeness: str = Field(
        ...,
        description="Description of gestures or actions considered rude or offensive (50-100 words)",
    )
    family_structure: str = Field(
        ...,
        description="Paragraph describing typical family structures, inheritance, and gender roles (150-250 words)",
    )
    naming_conventions: str = Field(
        ...,
        description="Paragraph describing how people are named and title conventions (100-150 words)",
    )
