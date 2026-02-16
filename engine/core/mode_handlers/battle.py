"""
Battle mode handler: turn-based combat scene.
"""

from settings import COLOR_BG

from .base import BaseModeHandler


class BattleModeHandler(BaseModeHandler):
    """Handles update, draw, and events when in battle mode."""

    def update(self, dt: float) -> None:
        if self.game.battle_scene is not None:
            self.game.battle_scene.update(dt)
            self.game._check_battle_finished()

    def draw(self) -> None:
        if self.game.battle_scene is None:
            return

        self.game.screen.fill(COLOR_BG)
        self.game.battle_scene.draw(self.game.screen, self.game)

    def handle_event(self, event) -> bool:
        if getattr(self.game, "active_screen", None) is not None:
            self.game.active_screen.handle_event(self.game, event)
        elif self.game.battle_scene is not None:
            self.game.battle_scene.handle_event(self.game, event)
            self.game._check_battle_finished()
        return True
