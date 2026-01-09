"""
Camera and FOV management system.

Handles camera positioning, zoom levels, and field-of-view calculations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, List

from settings import TILE_SIZE, FOV_RADIUS_TILES

if TYPE_CHECKING:
    import pygame
    from world.game_map import GameMap
    from world.entities import Player


class CameraManager:
    """
    Manages camera position, zoom, and field-of-view calculations.
    
    Responsibilities:
    - Track camera position (x, y)
    - Manage zoom levels for exploration and overworld
    - Calculate FOV around player
    - Center and clamp camera to map bounds
    """
    
    def __init__(
        self,
        screen: "pygame.Surface",
        default_zoom_levels: Optional[List[float]] = None,
        default_overworld_zoom_levels: Optional[List[float]] = None,
    ) -> None:
        """
        Initialize the camera manager.
        
        Args:
            screen: The pygame screen surface
            default_zoom_levels: List of zoom levels for exploration (default: calculated from screen size)
            default_overworld_zoom_levels: List of zoom levels for overworld (default: [0.5, 0.75, 1.0, 1.25, 1.5])
        """
        self.screen = screen
        
        # Camera position
        self.camera_x: float = 0.0
        self.camera_y: float = 0.0
        
        # Calculate default zoom based on screen size if not provided
        if default_zoom_levels is None:
            screen_w, screen_h = screen.get_size()
            from settings import WINDOW_WIDTH, WINDOW_HEIGHT
            resolution_scale = min(screen_w / WINDOW_WIDTH, screen_h / WINDOW_HEIGHT)
            if resolution_scale > 1.0:
                default_zoom = min(1.0 + (resolution_scale - 1.0) * 0.7, 3.0)
            else:
                default_zoom = max(resolution_scale, 0.5)
            
            self.zoom_levels = [
                default_zoom * 0.7,
                default_zoom,
                default_zoom * 1.4
            ]
        else:
            self.zoom_levels = default_zoom_levels
        
        self.zoom_index: int = 1  # start at default zoom
        
        # Overworld zoom (separate from exploration zoom)
        self.overworld_zoom_levels = default_overworld_zoom_levels or [0.5, 0.75, 1.0, 1.25, 1.5]
        self.overworld_zoom_index: int = 1  # Start at 75% (0.75) - default
    
    @property
    def zoom(self) -> float:
        """Current zoom scale for the exploration camera."""
        if not self.zoom_levels:
            return 1.0
        idx = max(0, min(self.zoom_index, len(self.zoom_levels) - 1))
        return float(self.zoom_levels[idx])
    
    @property
    def overworld_zoom(self) -> float:
        """Current zoom scale for the overworld map."""
        if not self.overworld_zoom_levels:
            return 1.0
        idx = max(0, min(self.overworld_zoom_index, len(self.overworld_zoom_levels) - 1))
        return float(self.overworld_zoom_levels[idx])
    
    def center_camera_on_player(self, player: "Player", current_map: "GameMap") -> None:
        """
        Center the camera around the player in world space before clamping.
        
        Args:
            player: The player entity
            current_map: The current game map
        """
        if player is None or current_map is None:
            return
        
        zoom = self.zoom
        if zoom <= 0:
            zoom = 1.0
        
        screen_w, screen_h = self.screen.get_size()
        view_w = screen_w / zoom
        view_h = screen_h / zoom
        
        px, py = player.rect.center
        self.camera_x = px - view_w / 2
        self.camera_y = py - view_h / 2
    
    def clamp_camera_to_map(self, current_map: "GameMap") -> None:
        """
        Clamp the camera so it never shows outside the current map.
        
        Args:
            current_map: The current game map
        """
        if current_map is None:
            return
        
        zoom = self.zoom
        if zoom <= 0:
            zoom = 1.0
        
        screen_w, screen_h = self.screen.get_size()
        view_w = screen_w / zoom
        view_h = screen_h / zoom
        
        world_w = current_map.width * TILE_SIZE
        world_h = current_map.height * TILE_SIZE
        
        max_x = max(0.0, world_w - view_w)
        max_y = max(0.0, world_h - view_h)
        
        self.camera_x = max(0.0, min(self.camera_x, max_x))
        self.camera_y = max(0.0, min(self.camera_y, max_y))
    
    def update_fov(
        self,
        player: Optional["Player"],
        current_map: Optional["GameMap"],
        debug_reveal_map: bool = False,
    ) -> None:
        """
        Recompute the map's field of view around the player.
        
        Args:
            player: The player entity
            current_map: The current game map
            debug_reveal_map: If True, reveal entire map (debug mode)
        """
        if current_map is None:
            return
        
        # Debug: reveal entire map if enabled
        if debug_reveal_map:
            all_coords = {
                (x, y)
                for y in range(current_map.height)
                for x in range(current_map.width)
            }
            current_map.visible = set(all_coords)
            current_map.explored = set(all_coords)
            return
        
        if player is None:
            return
        
        px, py = player.rect.center
        tx, ty = current_map.world_to_tile(px, py)
        current_map.compute_fov(tx, ty, radius=FOV_RADIUS_TILES)

