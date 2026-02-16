"""
Base interface for game mode handlers.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pygame
    from engine.core.game import Game


class BaseModeHandler(ABC):
    """
    Abstract base for mode-specific update, draw, and event handling.

    Each handler receives a reference to the Game and implements
    the mode-specific logic for the main loop.
    """

    def __init__(self, game: "Game") -> None:
        self.game = game

    @abstractmethod
    def update(self, dt: float) -> None:
        """Update mode-specific game state. Called every frame when not paused."""
        ...

    @abstractmethod
    def draw(self) -> None:
        """Draw the mode-specific view. Does not include overlays or flip."""
        ...

    def handle_event(self, event: "pygame.event.Event") -> bool:
        """
        Handle mode-specific input. Called after global handlers (pause, cheats, etc.).

        Returns:
            True if the event was consumed (no further processing needed),
            False otherwise.
        """
        return False
