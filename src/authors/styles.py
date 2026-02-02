"""
Author Style Components.

Dataclasses for the three phases of writing:
1. PlottingStyle - How the author structures stories
2. ScreenplayStyle - How the author tells stories in prose
3. RevisionStyle - How the author revises their work
"""

from dataclasses import dataclass, field, asdict
from typing import Literal


# Type aliases for valid options
PacingType = Literal["fast", "medium", "slow"]
SubplotType = Literal["minimal", "moderate", "complex"]
TwistType = Literal["none", "one_major", "multiple"]
POVType = Literal["first", "third_close", "third_omniscient"]
TenseType = Literal["past", "present"]
DialogueRatioType = Literal["dialogue_heavy", "balanced", "prose_heavy"]
DensityType = Literal["sparse", "moderate", "rich"]
SentenceLengthType = Literal["short", "varied", "long"]
VocabularyType = Literal["simple", "moderate", "literary"]
ToneType = Literal["dark", "hopeful", "cynical", "whimsical", "intimate", "tense"]


@dataclass
class PlottingStyle:
    """How an author approaches story structure.

    Controls outline generation and beat emphasis.
    """

    beat_emphasis: list[str] = field(default_factory=list)
    """Which story beats the author excels at (e.g., ["midpoint", "pinch_points"])"""

    pacing: PacingType = "medium"
    """Overall story pacing: fast, medium, or slow"""

    subplot_tendency: SubplotType = "minimal"
    """How many subplots the author typically includes"""

    twist_frequency: TwistType = "one_major"
    """How often plot twists occur"""

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return asdict(self)

    def get_prompt_modifier(self) -> str:
        """Generate prompt text based on plotting preferences."""
        modifiers = []

        if self.pacing == "fast":
            modifiers.append("Keep the pacing tight and relentless. Every scene should drive the plot forward.")
        elif self.pacing == "slow":
            modifiers.append("Allow the story to breathe. Build atmosphere and let tension simmer.")

        if self.subplot_tendency == "minimal":
            modifiers.append("Focus on the main plot. Avoid unnecessary subplots.")
        elif self.subplot_tendency == "complex":
            modifiers.append("Weave in meaningful subplots that enrich the main narrative.")

        if self.twist_frequency == "none":
            modifiers.append("Tell the story straight. No major twists needed.")
        elif self.twist_frequency == "multiple":
            modifiers.append("Include surprising twists that recontextualize earlier events.")

        if self.beat_emphasis:
            beats = ", ".join(self.beat_emphasis)
            modifiers.append(f"Pay special attention to these story beats: {beats}")

        return "\n".join(modifiers)


@dataclass
class ScreenplayStyle:
    """How an author tells the story in prose.

    Controls the narrative voice and prose style.
    """

    pov: POVType = "third_close"
    """Point of view: first person, third close, or third omniscient"""

    tense: TenseType = "past"
    """Narrative tense: past or present"""

    dialogue_ratio: DialogueRatioType = "balanced"
    """How much dialogue vs. prose"""

    description_density: DensityType = "moderate"
    """How detailed are descriptions"""

    sentence_length: SentenceLengthType = "varied"
    """Typical sentence length patterns"""

    vocabulary: VocabularyType = "moderate"
    """Vocabulary complexity"""

    tone: ToneType = "hopeful"
    """Overall emotional tone"""

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return asdict(self)

    def get_prompt_modifier(self) -> str:
        """Generate prompt text based on screenplay preferences."""
        modifiers = []

        # POV instructions
        if self.pov == "first":
            modifiers.append("Write in first person. The protagonist narrates their own story.")
        elif self.pov == "third_close":
            modifiers.append("Write in close third person. Stay in the protagonist's head, limited to their knowledge.")
        else:
            modifiers.append("Write in omniscient third person. The narrator knows all.")

        # Tense
        if self.tense == "present":
            modifiers.append("Use present tense for immediacy.")
        else:
            modifiers.append("Use past tense.")

        # Dialogue
        if self.dialogue_ratio == "dialogue_heavy":
            modifiers.append("Let characters speak. Favor dialogue over narration where possible.")
        elif self.dialogue_ratio == "prose_heavy":
            modifiers.append("Focus on interior narration and description. Use dialogue sparingly.")

        # Description density
        if self.description_density == "sparse":
            modifiers.append("Keep descriptions minimal. Only mention what's essential.")
        elif self.description_density == "rich":
            modifiers.append("Paint vivid scenes with detailed sensory descriptions.")

        # Sentence patterns
        if self.sentence_length == "short":
            modifiers.append("Use short, punchy sentences. Keep prose tight.")
        elif self.sentence_length == "long":
            modifiers.append("Craft flowing sentences with rhythm and complexity.")

        # Vocabulary
        if self.vocabulary == "simple":
            modifiers.append("Use accessible, everyday language.")
        elif self.vocabulary == "literary":
            modifiers.append("Employ rich, literary vocabulary.")

        # Tone
        tone_map = {
            "dark": "Maintain a dark, brooding atmosphere.",
            "hopeful": "Infuse the narrative with underlying hope.",
            "cynical": "Write with a cynical, world-weary voice.",
            "whimsical": "Keep the tone light and playful.",
            "intimate": "Create an intimate, confessional feel.",
            "tense": "Build and sustain tension throughout.",
        }
        if self.tone in tone_map:
            modifiers.append(tone_map[self.tone])

        return "\n".join(modifiers)


@dataclass
class RevisionStyle:
    """How an author revises their work.

    Controls the revision passes after initial draft.
    """

    num_passes: int = 1
    """Number of revision passes (1-3)"""

    focus_areas: list[str] = field(default_factory=lambda: ["pacing"])
    """What to focus on during revision: pacing, dialogue, prose_polish, tension, continuity"""

    cut_aggressively: bool = False
    """Whether to aggressively cut unnecessary content"""

    expand_scenes: bool = False
    """Whether to expand scenes that need more depth"""

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return asdict(self)

    def get_pass_focus(self, pass_num: int) -> str:
        """Get the focus area for a specific revision pass.

        Args:
            pass_num: 0-indexed pass number

        Returns:
            The focus area for this pass
        """
        if not self.focus_areas:
            return "general"
        return self.focus_areas[pass_num % len(self.focus_areas)]

    def get_prompt_modifier(self) -> str:
        """Generate prompt text based on revision preferences."""
        modifiers = []

        if self.cut_aggressively:
            modifiers.append("Be ruthless in cutting. Remove anything that doesn't serve the story.")
        else:
            modifiers.append("Preserve the author's voice. Only cut what's truly redundant.")

        if self.expand_scenes:
            modifiers.append("Look for scenes that need more depth or emotional beats.")

        focus_str = ", ".join(self.focus_areas)
        modifiers.append(f"Focus revision on: {focus_str}")

        return "\n".join(modifiers)
