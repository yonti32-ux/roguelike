"""
Mode handlers for the main game loop.

Each game mode (overworld, exploration, battle) has a handler that encapsulates
update(), draw(), and handle_event() logic. Game delegates to the active handler.
"""

from .base import BaseModeHandler
from .overworld import OverworldModeHandler
from .exploration import ExplorationModeHandler
from .battle import BattleModeHandler

__all__ = [
    "BaseModeHandler",
    "OverworldModeHandler",
    "ExplorationModeHandler",
    "BattleModeHandler",
]
