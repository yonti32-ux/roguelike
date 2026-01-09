"""
Overworld HUD rendering.

Renders the overworld map, POIs, player, and UI elements.
"""

import pygame
from typing import TYPE_CHECKING

from settings import COLOR_BG, TILE_SIZE

if TYPE_CHECKING:
    from engine.core.game import Game


# Overworld tile size (larger than exploration tiles for zoomed-out view)
OVERWORLD_TILE_SIZE = 16  # Pixels per overworld tile


def draw_overworld(game: "Game") -> None:
    """
    Draw the overworld map.
    
    Renders:
    - Terrain tiles
    - POI markers
    - Player icon
    - UI overlay (time, position, etc.)
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
    
    # Calculate viewport (center on player)
    viewport_tiles_x = screen_w // OVERWORLD_TILE_SIZE
    viewport_tiles_y = screen_h // OVERWORLD_TILE_SIZE
    
    start_x = max(0, player_x - viewport_tiles_x // 2)
    start_y = max(0, player_y - viewport_tiles_y // 2)
    end_x = min(game.overworld_map.width, start_x + viewport_tiles_x)
    end_y = min(game.overworld_map.height, start_y + viewport_tiles_y)
    
    # Draw terrain tiles
    for y in range(start_y, end_y):
        for x in range(start_x, end_x):
            # Calculate screen position
            screen_x = (x - start_x) * OVERWORLD_TILE_SIZE
            screen_y = (y - start_y) * OVERWORLD_TILE_SIZE
            
            # Draw tile
            rect = pygame.Rect(screen_x, screen_y, OVERWORLD_TILE_SIZE, OVERWORLD_TILE_SIZE)
            
            # Check if explored
            if not game.overworld_map.is_explored(x, y):
                # Unexplored tiles: very dark gray/black
                pygame.draw.rect(screen, (20, 20, 20), rect)
                continue
            
            tile = game.overworld_map.get_tile(x, y)
            if tile is None:
                pygame.draw.rect(screen, (40, 40, 40), rect)  # Dark gray for missing tiles
                continue
            
            # Calculate distance from player for brightness
            dx = abs(x - player_x)
            dy = abs(y - player_y)
            distance = max(dx, dy)  # Chebyshev distance
            
            # Dim explored but not currently visible tiles
            if (x, y) == (player_x, player_y):
                # Current tile: full brightness
                color = tile.color
            elif distance <= 3:
                # Very close tiles: nearly full brightness
                factor = 0.9
                color = (
                    int(tile.color[0] * factor),
                    int(tile.color[1] * factor),
                    int(tile.color[2] * factor),
                )
            else:
                # Explored tiles further away: dimmed
                factor = 0.7
                color = (
                    int(tile.color[0] * factor),
                    int(tile.color[1] * factor),
                    int(tile.color[2] * factor),
                )
            
            pygame.draw.rect(screen, color, rect)
    
    # Draw POI markers
    for poi in game.overworld_map.get_all_pois():
        px, py = poi.position
        
        # Only draw if in viewport
        if not (start_x <= px < end_x and start_y <= py < end_y):
            continue
        
        # Only show discovered POIs (unless they're in the viewport and nearby)
        if not poi.discovered:
            # Check if POI is within sight range but not yet discovered
            dx = abs(px - player_x)
            dy = abs(py - player_y)
            if max(dx, dy) <= 5:  # Show POIs very close even if not discovered
                # Show as a faint marker
                screen_x = (px - start_x) * OVERWORLD_TILE_SIZE + OVERWORLD_TILE_SIZE // 2
                screen_y = (py - start_y) * OVERWORLD_TILE_SIZE + OVERWORLD_TILE_SIZE // 2
                pygame.draw.circle(screen, (100, 100, 100), (screen_x, screen_y), 3)
            continue
        
        # Calculate screen position
        screen_x = (px - start_x) * OVERWORLD_TILE_SIZE + OVERWORLD_TILE_SIZE // 2
        screen_y = (py - start_y) * OVERWORLD_TILE_SIZE + OVERWORLD_TILE_SIZE // 2
        
        # Draw POI marker (colored circle)
        poi_colors = {
            "dungeon": (200, 50, 50),
            "village": (50, 200, 50),
            "town": (50, 50, 200),
            "camp": (200, 200, 50),
        }
        color = poi_colors.get(poi.poi_type, (150, 150, 150))
        radius = 4
        
        pygame.draw.circle(screen, color, (screen_x, screen_y), radius)
        
        # Draw level indicator for dungeons
        if poi.poi_type == "dungeon":
            font = pygame.font.Font(None, 12)
            level_text = font.render(str(poi.level), True, (255, 255, 255))
            text_rect = level_text.get_rect(center=(screen_x, screen_y))
            screen.blit(level_text, text_rect)
    
    # Draw player icon
    if start_x <= player_x < end_x and start_y <= player_y < end_y:
        screen_x = (player_x - start_x) * OVERWORLD_TILE_SIZE + OVERWORLD_TILE_SIZE // 2
        screen_y = (player_y - start_y) * OVERWORLD_TILE_SIZE + OVERWORLD_TILE_SIZE // 2
        
        # Draw player as a white circle with arrow
        pygame.draw.circle(screen, (255, 255, 255), (screen_x, screen_y), 6)
        # Simple arrow pointing up
        points = [
            (screen_x, screen_y - 6),
            (screen_x - 4, screen_y + 2),
            (screen_x + 4, screen_y + 2),
        ]
        pygame.draw.polygon(screen, (0, 0, 0), points)
    
    # Draw UI overlay
    _draw_overworld_ui(game, screen)
    
    # Draw message log
    if hasattr(game, "last_message") and game.last_message:
        _draw_message(game, screen)


def _draw_overworld_ui(game: "Game", screen: pygame.Surface) -> None:
    """Draw UI overlay (time, position, etc.)."""
    font = pygame.font.Font(None, 24)
    
    # Time display
    if game.time_system is not None:
        time_text = game.time_system.get_time_string()
        time_surface = font.render(time_text, True, (255, 255, 255))
        screen.blit(time_surface, (10, 10))
    
    # Position display
    if game.overworld_map is not None:
        x, y = game.overworld_map.get_player_position()
        pos_text = f"Position: ({x}, {y})"
        pos_surface = font.render(pos_text, True, (255, 255, 255))
        screen.blit(pos_surface, (10, 40))
    
    # Instructions
    help_text = "WASD: Move | E: Enter POI | I: Inventory | C: Character"
    help_surface = font.render(help_text, True, (200, 200, 200))
    screen.blit(help_surface, (10, screen.get_height() - 30))


def _draw_message(game: "Game", screen: pygame.Surface) -> None:
    """Draw the last message at the bottom of the screen."""
    if not hasattr(game, "last_message") or not game.last_message:
        return
    
    font = pygame.font.Font(None, 24)
    text_surface = font.render(game.last_message, True, (255, 255, 255))
    
    # Center at bottom
    x = (screen.get_width() - text_surface.get_width()) // 2
    y = screen.get_height() - 60
    
    # Draw with background for readability
    bg_rect = text_surface.get_rect()
    bg_rect.x = x
    bg_rect.y = y
    bg_rect.inflate_ip(10, 5)
    pygame.draw.rect(screen, (0, 0, 0, 180), bg_rect)
    
    screen.blit(text_surface, (x, y))

