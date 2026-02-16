"""
Overworld mode handler: map, parties, POIs, movement.
"""

import pygame

from .base import BaseModeHandler


class OverworldModeHandler(BaseModeHandler):
    """Handles update, draw, and events when in overworld mode."""

    def update(self, dt: float) -> None:
        if hasattr(self.game, "overworld"):
            self.game.overworld.update(dt)

        # Update tooltip mouse position (hover detection is done in draw)
        if hasattr(self.game, "tooltip") and self.game.tooltip:
            mouse_pos = pygame.mouse.get_pos()
            self.game.tooltip.mouse_pos = mouse_pos

    def draw(self) -> None:
        from ui.overworld import draw_overworld
        draw_overworld(self.game)

    def handle_event(self, event: pygame.event.Event) -> bool:
        # Mouse wheel for zoom
        if event.type == pygame.MOUSEWHEEL and hasattr(self.game, "overworld"):
            self.game.overworld.handle_mouse_wheel(event)
            return True

        # Route to modal screen or overworld controller
        if getattr(self.game, "active_screen", None) is not None:
            self.game.active_screen.handle_event(self.game, event)
        elif hasattr(self.game, "overworld"):
            self.game.overworld.handle_event(event)

        return True
