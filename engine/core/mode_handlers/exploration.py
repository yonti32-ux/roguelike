"""
Exploration mode handler: dungeon movement, FOV, camera, entities.
"""

from settings import COLOR_BG
from ui.hud_exploration import draw_exploration_ui

from .base import BaseModeHandler


class ExplorationModeHandler(BaseModeHandler):
    """Handles update, draw, and events when in exploration (dungeon) mode."""

    def update(self, dt: float) -> None:
        # Post-battle grace period
        if self.game.post_battle_grace > 0.0:
            self.game.post_battle_grace = max(0.0, self.game.post_battle_grace - dt)

        # Pause world updates when overlay is open
        if self.game.is_overlay_open():
            return

        self.game.exploration.update(dt)

        # Refresh FOV only when player tile changes (avoids per-frame raycasting)
        if self.game.player is not None and self.game.current_map is not None:
            tx, ty = self.game.current_map.world_to_tile(*self.game.player.rect.center)
            last_tile = getattr(self.game, "_last_fov_tile", (None, None))
            if (tx, ty) != last_tile:
                self.game._last_fov_tile = (tx, ty)
                self.game.update_fov()

        self.game._center_camera_on_player()
        self.game._clamp_camera_to_map()

    def draw(self) -> None:
        assert self.game.current_map is not None
        assert self.game.player is not None

        self.game.screen.fill(COLOR_BG)

        zoom = self.game.zoom
        camera_x = getattr(self.game, "camera_x", 0.0)
        camera_y = getattr(self.game, "camera_y", 0.0)

        # Map tiles
        self.game.current_map.draw(
            self.game.screen,
            camera_x=camera_x,
            camera_y=camera_y,
            zoom=zoom,
        )

        # Non-player entities (enemies, chests, props) – only if visible
        for entity in getattr(self.game.current_map, "entities", []):
            cx, cy = entity.rect.center
            tx, ty = self.game.current_map.world_to_tile(cx, cy)
            if (tx, ty) not in self.game.current_map.visible:
                continue
            entity.draw(
                self.game.screen,
                camera_x=camera_x,
                camera_y=camera_y,
                zoom=zoom,
            )

        # Draw the player on top
        self.game.player.draw(
            self.game.screen,
            camera_x=camera_x,
            camera_y=camera_y,
            zoom=zoom,
        )

        draw_exploration_ui(self.game)

    def handle_event(self, event) -> bool:
        if getattr(self.game, "active_screen", None) is not None:
            self.game.active_screen.handle_event(self.game, event)
        else:
            self.game.exploration.handle_event(event)
        return True
