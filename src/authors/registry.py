"""
Author Registry.

Central registry for all available authors with selection functions.
"""

import random
from typing import Optional

from src.authors.base_author import BaseAuthor
from src.authors.personas.marcus_vane import marcus_vane


# Registry of all available authors
AUTHOR_REGISTRY: dict[str, BaseAuthor] = {
    "marcus_vane": marcus_vane,
}

# Default author (None means random selection)
DEFAULT_AUTHOR: Optional[str] = None


def get_author(author_id: Optional[str] = None) -> BaseAuthor:
    """Get an author by ID.

    Args:
        author_id: The author's ID. If None, uses DEFAULT_AUTHOR or random selection.

    Returns:
        The requested BaseAuthor instance.

    Raises:
        ValueError: If author not found in registry.
    """
    if author_id is None:
        author_id = DEFAULT_AUTHOR

    if author_id is None:
        # Random selection
        return random.choice(list(AUTHOR_REGISTRY.values()))

    if author_id not in AUTHOR_REGISTRY:
        available = ", ".join(AUTHOR_REGISTRY.keys())
        raise ValueError(
            f"Unknown author: '{author_id}'. Available: {available}"
        )

    return AUTHOR_REGISTRY[author_id]


def select_author(
    author_id: Optional[str] = None,
    genre: Optional[str] = None,
    exclude: Optional[list[str]] = None,
) -> BaseAuthor:
    """Select an author, optionally filtering by genre.

    Args:
        author_id: Specific author to select (overrides other params)
        genre: Preferred genre to match
        exclude: List of author IDs to exclude

    Returns:
        Selected BaseAuthor instance
    """
    if author_id:
        return get_author(author_id)

    candidates = list(AUTHOR_REGISTRY.values())

    # Exclude specified authors
    if exclude:
        candidates = [a for a in candidates if a.id not in exclude]

    if not candidates:
        # Fallback to any author if all excluded
        candidates = list(AUTHOR_REGISTRY.values())

    # Filter by genre if specified
    if genre:
        genre_matches = [a for a in candidates if genre.lower() in [g.lower() for g in a.genres]]
        if genre_matches:
            candidates = genre_matches

    # Random selection from candidates
    return random.choice(candidates)


def list_authors() -> list[dict]:
    """List all available authors.

    Returns:
        List of dicts with author info.
    """
    return [
        {
            "id": author.id,
            "name": author.name,
            "pen_name": author.pen_name,
            "specialty": author.specialty,
            "genres": author.genres,
            "preferred_structure": author.preferred_structure,
        }
        for author in AUTHOR_REGISTRY.values()
    ]


def register_author(author: BaseAuthor) -> None:
    """Register a new author in the registry.

    Args:
        author: The author to register
    """
    AUTHOR_REGISTRY[author.id] = author
