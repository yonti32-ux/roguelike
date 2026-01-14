"""
Shared utilities for screen modules.
"""

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from engine.core.game import Game


def safe_getattr(game: "Game", attr: str, default: Any = None) -> Any:
    """
    Helper to safely get attributes from game object with a default.
    Reduces repetition of getattr(game, ...) calls.
    """
    return getattr(game, attr, default)

