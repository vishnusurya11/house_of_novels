"""
Scene Pacing Utilities

Provides word count estimation for scenes based on genre, pacing, and scene type.
Based on industry-standard scene length guidelines.
"""


def estimate_scene_word_count(
    scene_type: str,
    pacing: str = "medium",
    importance: str = "normal"
) -> int:
    """Estimate target word count for a scene based on type, pacing, and importance.

    Args:
        scene_type: Type of scene - "action", "dialogue", "introspection",
                   "confrontation", "revelation", "transition"
        pacing: Author's overall pacing style - "fast", "medium", "slow"
        importance: Scene importance - "minor", "normal", "major", "climax"

    Returns:
        int: Estimated target word count for this scene

    Industry Guidelines:
        - Typical scene: 750-2,000 words (~1,500 baseline)
        - Fast-paced (thriller): 750-1,200 words
        - Medium pace: 1,200-1,800 words
        - Slow-burn: 1,500-2,500+ words
    """
    # Base word counts by pacing style
    base_counts = {
        "fast": {
            "action": 900,
            "dialogue": 1000,
            "introspection": 700,
            "confrontation": 1100,
            "revelation": 1000,
            "transition": 600
        },
        "medium": {
            "action": 1400,
            "dialogue": 1500,
            "introspection": 1200,
            "confrontation": 1600,
            "revelation": 1500,
            "transition": 1000
        },
        "slow": {
            "action": 1800,
            "dialogue": 2000,
            "introspection": 1800,
            "confrontation": 2200,
            "revelation": 2100,
            "transition": 1400
        }
    }

    # Multipliers based on scene importance
    importance_multipliers = {
        "minor": 0.75,      # 75% of base (short scenes for minor moments)
        "normal": 1.0,      # 100% of base (standard scene)
        "major": 1.25,      # 125% of base (important plot points)
        "climax": 1.5       # 150% of base (climactic scenes need space)
    }

    # Get base count (default to medium/dialogue if not found)
    pacing = pacing.lower() if pacing else "medium"
    scene_type = scene_type.lower() if scene_type else "dialogue"

    if pacing not in base_counts:
        pacing = "medium"
    if scene_type not in base_counts[pacing]:
        scene_type = "dialogue"

    base = base_counts[pacing][scene_type]

    # Apply importance multiplier
    importance = importance.lower() if importance else "normal"
    multiplier = importance_multipliers.get(importance, 1.0)

    # Round to nearest 50 for cleaner targets
    estimated = int(base * multiplier)
    return round(estimated / 50) * 50


def get_chapter_word_count_range(pacing: str = "medium") -> tuple[int, int]:
    """Get recommended chapter word count range based on pacing.

    Args:
        pacing: "fast", "medium", or "slow"

    Returns:
        tuple: (min_words, max_words) for chapters

    Guidelines:
        - Fast-paced (thriller): 1,500-3,000 words
        - Medium pace: 2,500-4,500 words
        - Slow-burn: 3,500-6,000 words
    """
    ranges = {
        "fast": (1500, 3000),
        "medium": (2500, 4500),
        "slow": (3500, 6000)
    }
    return ranges.get(pacing.lower(), (2500, 4500))


def validate_chapter_length(
    scene_word_counts: list[int],
    pacing: str = "medium"
) -> dict:
    """Validate that chapter total falls within recommended range.

    Args:
        scene_word_counts: List of estimated word counts for scenes in chapter
        pacing: "fast", "medium", or "slow"

    Returns:
        dict with:
            - total: int (total words)
            - min_recommended: int
            - max_recommended: int
            - valid: bool (whether total is in range)
            - message: str (guidance message)
    """
    total = sum(scene_word_counts)
    min_rec, max_rec = get_chapter_word_count_range(pacing)

    valid = min_rec <= total <= max_rec

    if total < min_rec:
        message = f"Chapter may be too short ({total} words). Consider adding scene detail or an additional scene (target: {min_rec}-{max_rec} words)."
    elif total > max_rec:
        message = f"Chapter may be too long ({total} words). Consider trimming scenes or splitting chapter (target: {min_rec}-{max_rec} words)."
    else:
        message = f"Chapter length looks good ({total} words, target: {min_rec}-{max_rec})."

    return {
        "total": total,
        "min_recommended": min_rec,
        "max_recommended": max_rec,
        "valid": valid,
        "message": message
    }
