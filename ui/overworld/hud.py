"""
Overworld HUD rendering.

Renders the overworld map, POIs, player, and UI elements.
"""

import pygame
import math
from typing import TYPE_CHECKING, Tuple, Optional

from settings import COLOR_BG, TILE_SIZE
from ui.screen_constants import (
    COLOR_BG_PANEL,
    COLOR_BORDER_BRIGHT,
    COLOR_SHADOW,
    COLOR_TEXT,
    COLOR_SUBTITLE,
    SHADOW_OFFSET_X,
    SHADOW_OFFSET_Y,
)

if TYPE_CHECKING:
    from engine.core.game import Game
    from world.overworld.roaming_party import RoamingParty


# Base overworld tile size (before zoom)
BASE_OVERWORLD_TILE_SIZE = 16  # Pixels per overworld tile at 100% zoom


def draw_overworld(game: "Game") -> None:
    """
    Draw the overworld map.
    
    Renders:
    - Terrain tiles
    - POI markers
    - Player icon
    - UI overlay (time, position, etc.)
    - POI tooltips on hover
    """
    if game.overworld_map is None:
        # Fallback: blank screen
        game.screen.fill(COLOR_BG)
        font = pygame.font.Font(None, 36)
        text = font.render("Overworld not initialized", True, (255, 255, 255))
        rect = text.get_rect(center=(game.screen.get_width() // 2, game.screen.get_height() // 2))
        game.screen.blit(text, rect)
        return
    
    screen = game.screen
    screen_w, screen_h = screen.get_size()
    
    # Clear screen
    screen.fill(COLOR_BG)
    
    # Get player position
    player_x, player_y = game.overworld_map.get_player_position()
    
    # Get mouse position for POI and party hover detection
    mouse_x, mouse_y = pygame.mouse.get_pos()
    hovered_poi = None
    hovered_party = None
    
    # Get current zoom level
    zoom = 1.0
    if hasattr(game, "overworld_zoom"):
        zoom = game.overworld_zoom  # It's a property, not a method
    
    # Calculate effective tile size with zoom
    tile_size = int(BASE_OVERWORLD_TILE_SIZE * zoom)
    tile_size = max(4, min(tile_size, 64))  # Clamp between 4 and 64 pixels
    
    # Calculate viewport (center on player)
    viewport_tiles_x = screen_w // tile_size
    viewport_tiles_y = screen_h // tile_size
    
    start_x = max(0, player_x - viewport_tiles_x // 2)
    start_y = max(0, player_y - viewport_tiles_y // 2)
    end_x = min(game.overworld_map.width, start_x + viewport_tiles_x)
    end_y = min(game.overworld_map.height, start_y + viewport_tiles_y)

    # PERFORMANCE: Load config and time ONCE per frame, not per tile
    from world.overworld import OverworldConfig
    config = OverworldConfig.load()
    current_time = None
    if game.time_system is not None:
        current_time = game.time_system.get_total_hours()

    # Draw terrain tiles
    # Note: pygame.draw.rect is actually faster than blitting many small surfaces
    # Surface caching increased calls from 21M to 43M and time from 8s to 16s
    for y in range(start_y, end_y):
        for x in range(start_x, end_x):
            # Calculate screen position (using zoomed tile size)
            screen_x = (x - start_x) * tile_size
            screen_y = (y - start_y) * tile_size
            rect = pygame.Rect(screen_x, screen_y, tile_size, tile_size)
            
            # Calculate tile color
            # Calculate distance from player for sight radius check
            dx = abs(x - player_x)
            dy = abs(y - player_y)
            distance = max(dx, dy)  # Chebyshev distance
            is_within_sight = distance <= config.sight_radius
            
            # Check if tile was ever explored (regardless of timeout)
            tile_pos = (x, y)
            was_explored = tile_pos in game.overworld_map.explored_tiles
            
            # Check if within timeout (for tiles outside sight radius)
            is_within_timeout = True
            if current_time is not None and was_explored and not is_within_sight:
                last_seen = game.overworld_map.explored_tiles.get(tile_pos, 0.0)
                time_since_seen = current_time - last_seen
                is_within_timeout = time_since_seen <= config.memory_timeout_hours
            
            if not was_explored:
                # Unexplored tiles: black (fog of war)
                color = (20, 20, 20)
            else:
                tile = game.overworld_map.get_tile(x, y)
                if tile is None:
                    # Dark gray for missing tiles
                    color = (40, 40, 40)
                else:
                    # Determine brightness based on visibility state
                    if (x, y) == (player_x, player_y):
                        # Current tile: full brightness
                        color = tile.color
                    elif is_within_sight:
                        # Tiles within sight radius: nearly full brightness
                        factor = 0.9
                        color = (
                            int(tile.color[0] * factor),
                            int(tile.color[1] * factor),
                            int(tile.color[2] * factor),
                        )
                    elif is_within_timeout:
                        # Explored tiles outside sight radius but within timeout: dimmed (memory)
                        factor = 0.7
                        color = (
                            int(tile.color[0] * factor),
                            int(tile.color[1] * factor),
                            int(tile.color[2] * factor),
                        )
                    else:
                        # Explored tiles outside sight radius and past timeout: very dim (old memory)
                        # Still visible but very faint - you can see the layout but not details
                        factor = 0.15  # Very dim, but still visible
                        color = (
                            int(tile.color[0] * factor),
                            int(tile.color[1] * factor),
                            int(tile.color[2] * factor),
                        )
            
            # Draw rectangle directly (faster than blitting many small surfaces)
            pygame.draw.rect(screen, color, rect)
    
    # Draw POI markers and detect hover
    for poi in game.overworld_map.get_all_pois():
        px, py = poi.position
        
        # Only draw if in viewport
        if not (start_x <= px < end_x and start_y <= py < end_y):
            continue
        
        # Calculate screen position (using zoomed tile size)
        screen_x = (px - start_x) * tile_size + tile_size // 2
        screen_y = (py - start_y) * tile_size + tile_size // 2
        
        # Check if mouse is hovering over this POI (adjust hover radius with zoom)
        hover_radius = max(8, int(8 * zoom))  # Scale hover detection with zoom
        dx_mouse = abs(mouse_x - screen_x)
        dy_mouse = abs(mouse_y - screen_y)
        if dx_mouse <= hover_radius and dy_mouse <= hover_radius:
            hovered_poi = poi
        
        # Check if player is standing on this POI
        is_player_on_poi = (px == player_x and py == player_y)
        
        # Only show discovered POIs (unless they're in the viewport and nearby)
        if not poi.discovered:
            # Check if POI is within sight range but not yet discovered
            dx = abs(px - player_x)
            dy = abs(py - player_y)
            if max(dx, dy) <= 5:  # Show POIs very close even if not discovered
                # Show as a faint marker
                marker_radius = max(2, int(3 * zoom))
                pygame.draw.circle(screen, (100, 100, 100), (screen_x, screen_y), marker_radius)
            continue
        
        # Draw POI marker (colored circle) - scale with zoom
        poi_colors = {
            "dungeon": (200, 50, 50),
            "village": (50, 200, 50),
            "town": (50, 50, 200),
            "camp": (200, 200, 50),
        }
        color = poi_colors.get(poi.poi_type, (150, 150, 150))
        
        # Calculate radius based on zoom and state
        base_radius = 4
        if is_player_on_poi:
            # Player is here - draw larger, brighter circle
            radius = max(5, int(base_radius * 1.75 * zoom))
            highlight_color = tuple(min(255, c + 50) for c in color)
            pygame.draw.circle(screen, highlight_color, (screen_x, screen_y), radius)
            # Draw border
            border_width = max(1, int(2 * zoom))
            pygame.draw.circle(screen, (255, 255, 255), (screen_x, screen_y), radius, border_width)
        elif hovered_poi == poi:
            # Hovering - draw slightly larger circle
            radius = max(4, int(base_radius * 1.5 * zoom))
            hover_color = tuple(min(255, c + 30) for c in color)
            pygame.draw.circle(screen, hover_color, (screen_x, screen_y), radius)
            border_width = max(1, int(1 * zoom))
            pygame.draw.circle(screen, (255, 255, 255), (screen_x, screen_y), radius, border_width)
        else:
            # Normal size - scale with zoom
            radius = max(2, int(base_radius * zoom))
            pygame.draw.circle(screen, color, (screen_x, screen_y), radius)
        
        # Draw level indicator for dungeons (scale font with zoom)
        if poi.poi_type == "dungeon":
            # PERFORMANCE: Cache font by size to avoid creating new fonts every frame
            font_size = max(8, int(12 * zoom))
            if not hasattr(game, "_overworld_font_cache"):
                game._overworld_font_cache = {}
            if font_size not in game._overworld_font_cache:
                game._overworld_font_cache[font_size] = pygame.font.Font(None, font_size)
            font = game._overworld_font_cache[font_size]
            level_text = font.render(str(poi.level), True, (255, 255, 255))
            text_rect = level_text.get_rect(center=(screen_x, screen_y))
            screen.blit(level_text, text_rect)
    
    # Draw player icon (scaled with zoom)
    if start_x <= player_x < end_x and start_y <= player_y < end_y:
        screen_x = (player_x - start_x) * tile_size + tile_size // 2
        screen_y = (player_y - start_y) * tile_size + tile_size // 2
        
        # Draw player as a white circle with arrow (scaled with zoom)
        player_radius = max(3, int(6 * zoom))
        pygame.draw.circle(screen, (255, 255, 255), (screen_x, screen_y), player_radius)
        
        # Get last movement direction (default to up if not available)
        last_dir = (0, -1)  # Default: pointing up
        if hasattr(game, "overworld") and hasattr(game.overworld, "last_direction"):
            last_dir = game.overworld.last_direction
        
        # Calculate angle from direction vector (dx, dy)
        # Direction (0, -1) = 0° (up), (1, 0) = 90° (right), etc.
        dx, dy = last_dir
        # Calculate angle in radians (atan2 gives angle from positive x-axis, we want from positive y-axis)
        angle = math.atan2(dx, -dy)  # -dy because screen y increases downward
        
        # Arrow points in direction of movement (scaled with zoom)
        # Base arrow shape (pointing up when angle=0)
        arrow_length = max(3, int(6 * zoom))
        arrow_width = max(2, int(4 * zoom))
        base_points = [
            (0, -arrow_length),  # Tip
            (-arrow_width, max(1, int(2 * zoom))),   # Bottom left
            (arrow_width, max(1, int(2 * zoom))),    # Bottom right
        ]
        
        # Rotate points around center
        rotated_points = []
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        for px, py in base_points:
            # Rotate point around origin
            rx = px * cos_a - py * sin_a
            ry = px * sin_a + py * cos_a
            # Translate to player position
            rotated_points.append((screen_x + int(rx), screen_y + int(ry)))
        
        pygame.draw.polygon(screen, (0, 0, 0), rotated_points)
    
    # Draw roaming parties and detect hover
    if game.overworld_map.party_manager is not None:
        hovered_party = _draw_roaming_parties(
            game, screen, start_x, start_y, end_x, end_y, tile_size, zoom, 
            player_x, player_y, mouse_x, mouse_y, config, current_time
        )
    
    # Draw UI overlay
    _draw_overworld_ui(game, screen)
    
    # Draw message log
    if hasattr(game, "last_message") and game.last_message:
        _draw_message(game, screen)
    
    # Draw tooltips if hovering
    if hasattr(game, "tooltip") and game.tooltip:
        # Priority: party tooltip over POI tooltip
        if hovered_party is not None:
            from ui.overworld.party_tooltips import create_party_tooltip_data
            from world.overworld.party_types import get_party_type
            
            party_type = get_party_type(hovered_party.party_type_id)
            if party_type:
                tooltip_data = create_party_tooltip_data(hovered_party, party_type, game)
                game.tooltip.current_tooltip = tooltip_data
                game.tooltip.mouse_pos = (mouse_x, mouse_y)
                if hasattr(game, "ui_font"):
                    game.tooltip.draw(screen, game.ui_font)
        elif hovered_poi is not None and hovered_poi.discovered:
            from ui.overworld.poi_tooltips import create_poi_tooltip_data
            
            tooltip_data = create_poi_tooltip_data(hovered_poi, game)
            # Update tooltip with POI data
            game.tooltip.current_tooltip = tooltip_data
            game.tooltip.mouse_pos = (mouse_x, mouse_y)
            # Use game's UI font for tooltip
            if hasattr(game, "ui_font"):
                game.tooltip.draw(screen, game.ui_font)
        else:
            # Clear tooltip if not hovering over anything
            game.tooltip.current_tooltip = None
    
    # Overworld tutorial overlay
    if getattr(game, "show_overworld_tutorial", False):
        from ui.overworld_tutorial import draw_overworld_tutorial
        if hasattr(game, "ui_font"):
            draw_overworld_tutorial(screen, game.ui_font, game)


def _draw_roaming_parties(
    game: "Game",
    screen: pygame.Surface,
    start_x: int,
    start_y: int,
    end_x: int,
    end_y: int,
    tile_size: int,
    zoom: float,
    player_x: int,
    player_y: int,
    mouse_x: int,
    mouse_y: int,
    config,  # OverworldConfig instance
    current_time: Optional[float],  # Current time from time_system
) -> Optional["RoamingParty"]:
    """
    Draw roaming parties on the overworld and detect hover.
    
    Returns:
        The party being hovered over, or None
    """
    from world.overworld.party_types import get_party_type
    from world.overworld.roaming_party import RoamingParty
    
    party_manager = game.overworld_map.party_manager
    if party_manager is None:
        return None
    
    all_parties = party_manager.get_all_parties()
    hovered_party = None
    
    for party in all_parties:
        px, py = party.get_position()
        
        # Only draw if in viewport
        if not (start_x <= px < end_x and start_y <= py < end_y):
            continue
        
        # Parties are only visible if:
        # 1. Within sight radius (always visible, even if not explored)
        # 2. Outside sight radius but explored AND within timeout (old memory still shows parties)
        # Parties on expired tiles (past timeout) are NOT visible (you can see layout but not parties)
        
        # Calculate distance from player for sight radius check
        dx = abs(px - player_x)
        dy = abs(py - player_y)
        distance = max(dx, dy)  # Chebyshev distance
        is_within_sight = distance <= config.sight_radius
        
        # Parties within sight radius are always visible (even if not explored yet)
        if is_within_sight:
            is_visible = True
        else:
            # Outside sight radius - must be explored AND within timeout
            # Past timeout tiles show terrain but NOT parties
            if current_time is not None:
                tile_pos = (px, py)
                if tile_pos not in game.overworld_map.explored_tiles:
                    is_visible = False
                else:
                    last_seen = game.overworld_map.explored_tiles[tile_pos]
                    time_since_seen = current_time - last_seen
                    is_visible = time_since_seen <= config.memory_timeout_hours
            else:
                # Fallback if no time system
                is_visible = game.overworld_map.is_explored(px, py, current_time=None, timeout_hours=0.0)
        
        if not is_visible:
            continue  # Not visible, don't show party
        
        # Get party type for color/icon
        party_type = get_party_type(party.party_type_id)
        if party_type is None:
            continue
        
        # Calculate screen position
        screen_x = (px - start_x) * tile_size + tile_size // 2
        screen_y = (py - start_y) * tile_size + tile_size // 2
        
        # Check if mouse is hovering over this party
        hover_radius = max(8, int(8 * zoom))  # Scale hover detection with zoom
        dx_mouse = abs(mouse_x - screen_x)
        dy_mouse = abs(mouse_y - screen_y)
        if dx_mouse <= hover_radius and dy_mouse <= hover_radius:
            hovered_party = party
        
        # Draw party icon (colored circle with icon character)
        base_radius = max(2, int(4 * zoom))
        
        # Use party type color
        color = party_type.color
        
        # Highlight if hovering
        if hovered_party == party:
            # Draw larger, brighter circle when hovering
            radius = max(3, int(base_radius * 1.5))
            highlight_color = tuple(min(255, c + 30) for c in color)
            pygame.draw.circle(screen, highlight_color, (screen_x, screen_y), radius)
            # Draw border
            border_width = max(1, int(2 * zoom))
            pygame.draw.circle(screen, (255, 255, 255), (screen_x, screen_y), radius, border_width)
        else:
            # Normal size
            pygame.draw.circle(screen, color, (screen_x, screen_y), base_radius)
            # Draw border (darker for contrast)
            border_color = tuple(max(0, c - 50) for c in color)
            pygame.draw.circle(screen, border_color, (screen_x, screen_y), base_radius, max(1, int(1 * zoom)))
        
        # Draw icon character if zoom is high enough
        if zoom >= 0.5:
            # PERFORMANCE: Cache font by size to avoid creating new fonts every frame
            font_size = max(8, int(10 * zoom))
            if not hasattr(game, "_overworld_font_cache"):
                game._overworld_font_cache = {}
            if font_size not in game._overworld_font_cache:
                game._overworld_font_cache[font_size] = pygame.font.Font(None, font_size)
            font = game._overworld_font_cache[font_size]
            icon_text = font.render(party_type.icon, True, (255, 255, 255))
            text_rect = icon_text.get_rect(center=(screen_x, screen_y))
            screen.blit(icon_text, text_rect)
    
    return hovered_party


def _draw_overworld_ui(game: "Game", screen: pygame.Surface) -> None:
    """Draw UI overlay (time, position, etc.) with polished panels."""
    # PERFORMANCE: Cache UI font to avoid creating it every frame
    if not hasattr(game, "_overworld_ui_font"):
        game._overworld_ui_font = pygame.font.Font(None, 24)
    font = game._overworld_ui_font
    
    # Top-left info panel
    info_panel_width = 250
    info_panel_height = 80
    info_panel_x = 10
    info_panel_y = 10
    
    info_panel = pygame.Surface((info_panel_width, info_panel_height), pygame.SRCALPHA)
    info_panel.fill(COLOR_BG_PANEL)
    pygame.draw.rect(info_panel, COLOR_BORDER_BRIGHT, (0, 0, info_panel_width, info_panel_height), 2)
    screen.blit(info_panel, (info_panel_x, info_panel_y))
    
    # Time display
    if game.time_system is not None:
        time_text = game.time_system.get_time_string()
        time_surface = font.render(time_text, True, COLOR_TEXT)
        screen.blit(time_surface, (info_panel_x + 12, info_panel_y + 12))
    
    # Position display
    if game.overworld_map is not None:
        x, y = game.overworld_map.get_player_position()
        pos_text = f"Position: ({x}, {y})"
        pos_surface = font.render(pos_text, True, COLOR_TEXT)
        screen.blit(pos_surface, (info_panel_x + 12, info_panel_y + 40))
    
    # Top-right zoom panel
    if hasattr(game, "overworld_zoom"):
        zoom_value = game.overworld_zoom  # It's a property, not a method
        zoom_text = f"Zoom: {int(zoom_value * 100)}%"
        zoom_surface = font.render(zoom_text, True, COLOR_SUBTITLE)
        
        zoom_panel_width = zoom_surface.get_width() + 24
        zoom_panel_height = 40
        zoom_panel_x = screen.get_width() - zoom_panel_width - 10
        zoom_panel_y = 10
        
        zoom_panel = pygame.Surface((zoom_panel_width, zoom_panel_height), pygame.SRCALPHA)
        zoom_panel.fill(COLOR_BG_PANEL)
        pygame.draw.rect(zoom_panel, COLOR_BORDER_BRIGHT, (0, 0, zoom_panel_width, zoom_panel_height), 2)
        screen.blit(zoom_panel, (zoom_panel_x, zoom_panel_y))
        screen.blit(zoom_surface, (zoom_panel_x + 12, zoom_panel_y + 10))
    
    # Bottom instructions panel
    help_text = "WASD: Move | E: Enter POI | +/-: Zoom | 0: Reset Zoom | Hover: POI Info | I: Inventory | C: Character | H: Tutorial"
    help_surface = font.render(help_text, True, COLOR_TEXT)
    
    help_panel_width = help_surface.get_width() + 24
    help_panel_height = 40
    help_panel_x = 10
    help_panel_y = screen.get_height() - help_panel_height - 10
    
    help_panel = pygame.Surface((help_panel_width, help_panel_height), pygame.SRCALPHA)
    help_panel.fill(COLOR_BG_PANEL)
    pygame.draw.rect(help_panel, COLOR_BORDER_BRIGHT, (0, 0, help_panel_width, help_panel_height), 2)
    screen.blit(help_panel, (help_panel_x, help_panel_y))
    screen.blit(help_surface, (help_panel_x + 12, help_panel_y + 10))


def _draw_message(game: "Game", screen: pygame.Surface) -> None:
    """Draw the last message at the bottom of the screen with polished styling."""
    if not hasattr(game, "last_message") or not game.last_message:
        return
    
    # PERFORMANCE: Reuse cached UI font
    if not hasattr(game, "_overworld_ui_font"):
        game._overworld_ui_font = pygame.font.Font(None, 24)
    font = game._overworld_ui_font
    text_surface = font.render(game.last_message, True, COLOR_TEXT)
    
    # Center at bottom
    message_panel_width = text_surface.get_width() + 40
    message_panel_height = 50
    x = (screen.get_width() - message_panel_width) // 2
    y = screen.get_height() - 100
    
    # Draw message panel with shadow
    message_shadow = pygame.Surface((message_panel_width + 4, message_panel_height + 4), pygame.SRCALPHA)
    message_shadow.fill((0, 0, 0, 100))
    screen.blit(message_shadow, (x - 2, y - 2))
    
    message_panel = pygame.Surface((message_panel_width, message_panel_height), pygame.SRCALPHA)
    message_panel.fill(COLOR_BG_PANEL)
    pygame.draw.rect(message_panel, COLOR_BORDER_BRIGHT, (0, 0, message_panel_width, message_panel_height), 2)
    screen.blit(message_panel, (x, y))
    
    screen.blit(text_surface, (x + 20, y + 15))
