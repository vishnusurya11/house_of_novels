"""
Deterministic prose post-processing.

Applied after LLM synthesis and revision to catch issues that
prompt-based instructions fail to enforce (banned phrases, smart quotes,
word overuse). Pure Python — zero LLM cost.
"""

import logging
import re

logger = logging.getLogger("prose_quality")

# Banned phrase patterns -> replacement text (empty = delete the phrase)
BANNED_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\bthe weight of\b", re.IGNORECASE), ""),
    (re.compile(r"\bfragile hope\b", re.IGNORECASE), "a stubborn hope"),
    (re.compile(r"\ba (?:stark|grim|constant|painful|bitter) reminder (?:that|of)\b", re.IGNORECASE), ""),
    (re.compile(r"\bnot just (.+?), but (.+?)(?:\.|,)", re.IGNORECASE), r"\2."),
    (re.compile(r"\bsomething (?:shifted|broke) (?:inside|between)\b", re.IGNORECASE), ""),
    (re.compile(r"\bresolve (?:hardened|wavered|flickered)\b", re.IGNORECASE), ""),
    (re.compile(r"\b(?:doubt gnawed|tension gripped|urgency pressed)\b", re.IGNORECASE), ""),
]

# Words capped at max occurrences per scene (keep first N, replace rest)
OVERUSE_CAPS: dict[str, tuple[int, str]] = {
    "shadow": (2, "darkness"),
    "shadows": (2, "the dark"),
    "beneath": (2, "under"),
}

# Smart/curly quote replacements
QUOTE_REPLACEMENTS = {
    "\u201c": '"',  # left double curly
    "\u201d": '"',  # right double curly
    "\u2018": "'",  # left single curly
    "\u2019": "'",  # right single curly
    "\u2033": '"',  # double prime
    "\u2032": "'",  # single prime
    "\u2014": "\u2014",  # em dash — keep as-is (valid in prose)
}


def prose_postprocess(
    prose: str,
    *,
    pov_gender: str = "",
    characters_present: list[str] | None = None,
) -> str:
    """Deterministic post-processing for generated prose.

    Applied after LLM generation to catch issues the model ignores.

    Args:
        prose: The raw prose text.
        pov_gender: Gender of POV character ("male"/"female") for pronoun validation.
        characters_present: List of character names allowed in this scene.

    Returns:
        Cleaned prose text.
    """
    if not prose:
        return prose

    # 1. Smart quote normalization
    for old, new in QUOTE_REPLACEMENTS.items():
        prose = prose.replace(old, new)

    # 2. Banned phrase removal/replacement
    for pattern, replacement in BANNED_PATTERNS:
        prose = pattern.sub(replacement, prose)

    # 3. Word overuse cap
    for word, (max_count, alt) in OVERUSE_CAPS.items():
        occurrences = list(re.finditer(rf"\b{word}\b", prose, re.IGNORECASE))
        if len(occurrences) > max_count:
            # Replace occurrences beyond the cap (process in reverse to preserve indices)
            for match in reversed(occurrences[max_count:]):
                prose = prose[:match.start()] + alt + prose[match.end():]

    # 4. Clean up artifacts from removals
    prose = re.sub(r"  +", " ", prose)      # double spaces
    prose = re.sub(r" ,", ",", prose)        # orphaned comma space
    prose = re.sub(r"\.\.", ".", prose)       # double periods
    prose = re.sub(r"^ ", "", prose, flags=re.MULTILINE)  # leading spaces on lines

    # 5. Pronoun consistency check (detection only — logs warning, does not auto-fix)
    if pov_gender in ("male", "female"):
        _check_pronoun_consistency(prose, pov_gender)

    # 6. Phantom character detection (detection only — logs warning)
    if characters_present:
        _check_character_roster(prose, characters_present)

    return prose


def _check_pronoun_consistency(prose: str, pov_gender: str) -> None:
    """Log a warning if narration pronouns don't match POV character gender.

    Only checks narration (outside dialogue quotes) to avoid false positives
    from other characters speaking.
    """
    # Extract narration segments (everything outside quotation marks)
    segments = re.split(r'"[^"]*"', prose)
    narration = " ".join(segments)

    male_count = len(re.findall(r"\b(?:he|him|his)\b", narration, re.IGNORECASE))
    female_count = len(re.findall(r"\b(?:she|her|hers)\b", narration, re.IGNORECASE))

    total = male_count + female_count
    if total == 0:
        return

    if pov_gender == "female":
        expected_ratio = female_count / total
    else:
        expected_ratio = male_count / total

    if expected_ratio < 0.7:
        logger.warning(
            "PRONOUN_MIX: POV is %s but only %.0f%% matching pronouns "
            "(male=%d, female=%d)",
            pov_gender, expected_ratio * 100, male_count, female_count,
        )


# Common speech verbs for dialogue tag detection
_SPEECH_VERBS = (
    "said|says|whispered|murmured|muttered|shouted|yelled|called|cried|replied|"
    "answered|asked|demanded|snapped|hissed|growled|snarled|breathed|sighed|"
    "groaned|barked|exclaimed|declared|announced|pleaded|begged|urged|insisted|"
    "continued|added|began|finished|interrupted|stammered|stuttered|rasped|"
    "croaked|spat|retorted"
)

# Words that should never be flagged as phantom character names.
# Pronouns, demonstratives, and common nouns that appear near speech verbs
# in prose (e.g. "she said", "the stone said nothing", "Raindrops said goodbye").
_NON_NAME_WORDS = frozenset({
    "she", "her", "hers", "herself",
    "he", "him", "his", "himself",
    "they", "them", "their", "theirs", "themselves",
    "it", "its", "itself",
    "who", "whom", "whose",
    "this", "that", "these", "those",
    "what", "which", "where", "when", "how",
    "something", "someone", "nothing", "nobody", "everybody",
    "everything", "anything", "anyone",
    "the", "and", "but", "then", "just", "still", "even",
})


def _check_character_roster(prose: str, characters_present: list[str]) -> None:
    """Log a warning if prose contains dialogue attributed to unknown characters.

    Scans for capitalized names near speech verbs that aren't in the
    characters_present roster. Catches LLM-hallucinated characters like
    'Elys' appearing in a scene where only 'Liora Zale' should be present.

    Filters out pronouns, common words, and requires dialogue proximity
    (within 120 chars of a quotation mark) to reduce false positives.
    """
    # Build set of allowed names (full names, first names, last names)
    allowed: set[str] = set()
    for name in characters_present:
        allowed.add(name)
        parts = name.split()
        for part in parts:
            allowed.add(part)

    # Find names that appear in dialogue attribution patterns
    # Pattern: Capitalized word + speech verb (case-sensitive — names are always capitalized)
    tag_pattern = re.compile(
        rf"\b([A-Z][a-z]{{2,}})\s+(?:{_SPEECH_VERBS})\b"
    )

    # Find all quote positions for proximity check
    quote_positions = [i for i, ch in enumerate(prose) if ch == '"']

    phantoms: set[str] = set()
    for match in tag_pattern.finditer(prose):
        name = match.group(1)
        # Skip known non-name words
        if name.lower() in _NON_NAME_WORDS:
            continue
        # Skip already-allowed character names
        if name in allowed:
            continue
        # Require proximity to dialogue (within 120 chars of a quote mark)
        pos = match.start()
        near_dialogue = any(abs(pos - qp) <= 120 for qp in quote_positions)
        if not near_dialogue:
            continue
        phantoms.add(name)

    for phantom in sorted(phantoms):
        logger.warning(
            "PHANTOM_CHARACTER: '%s' speaks dialogue but is not in "
            "characters_present %s",
            phantom, characters_present,
        )
