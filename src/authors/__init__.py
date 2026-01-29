"""
Authors Module.

Provides author personas with distinct writing styles.
"""

from src.authors.styles import PlottingStyle, ScreenplayStyle, RevisionStyle
from src.authors.skills import Skill
from src.authors.base_author import BaseAuthor
from src.authors.registry import (
    AUTHOR_REGISTRY,
    get_author,
    select_author,
    list_authors,
)

__all__ = [
    "PlottingStyle",
    "ScreenplayStyle",
    "RevisionStyle",
    "Skill",
    "BaseAuthor",
    "AUTHOR_REGISTRY",
    "get_author",
    "select_author",
    "list_authors",
]
