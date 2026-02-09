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
    from world.overworld.party import RoamingParty


# Base overworld tile size (before zoom)
BASE_OVERWORLD_TILE_SIZE = 16  # Pixels per overworld tile at 100% zoom

# Quest marker: color and ring for POIs that are active quest objectives
QUEST_MARKER_COLOR = (255, 220, 100)  # Gold/amber
QUEST_MARKER_RING_COLOR = (255, 255, 200)


def _is_poi_quest_target(poi, game: "Game") -> bool:
    """True if any active quest has an objective targeting this POI."""
    try:
        from systems.quests import QuestStatus
        active = getattr(game, "active_quests", None) or {}
        for quest in active.values():
            if getattr(quest, "status", None) != QuestStatus.ACTIVE:
                continue
            for obj in getattr(quest, "objectives", []):
                if getattr(obj, "poi_id", None) == poi.poi_id:
                    return True
    except Exception:
        pass
    return False


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
    # OPTIMIZATION: Cache config (it rarely changes)
    if not hasattr(game, "_overworld_config_cache"):
        from world.overworld import OverworldConfig
        game._overworld_config_cache = OverworldConfig.load()
    config = game._overworld_config_cache
    
    current_time = None
    if game.time_system is not None:
        current_time = game.time_system.get_total_hours()

    # OPTIMIZATION: Cache explored_tiles reference and pre-calculate values
    explored_tiles = game.overworld_map.explored_tiles
    sight_radius = config.sight_radius
    timeout_hours = config.memory_timeout_hours
    player_tile_pos = (player_x, player_y)
    
    # Pre-calculated color factors (avoid repeated calculations)
    COLOR_FACTOR_SIGHT = 0.9
    COLOR_FACTOR_MEMORY = 0.7
    COLOR_FACTOR_OLD = 0.15
    
    # Draw terrain tiles (OPTIMIZED)
    for y in range(start_y, end_y):
        for x in range(start_x, end_x):
            # Calculate screen position
            screen_x = (x - start_x) * tile_size
            screen_y = (y - start_y) * tile_size
            rect = pygame.Rect(screen_x, screen_y, tile_size, tile_size)
            
            # OPTIMIZATION: Use tuple for position (faster dict lookup)
            tile_pos = (x, y)
            was_explored = tile_pos in explored_tiles
            
            if not was_explored:
                # Unexplored tiles: black (fog of war)
                pygame.draw.rect(screen, (20, 20, 20), rect)
                continue
            
            # Get tile
            tile = game.overworld_map.get_tile(x, y)
            if tile is None:
                pygame.draw.rect(screen, (40, 40, 40), rect)
                continue
            
            # OPTIMIZATION: Fast path for player tile
            if tile_pos == player_tile_pos:
                pygame.draw.rect(screen, tile.color, rect)
                continue
            
            # OPTIMIZATION: Calculate distance once
            dx = abs(x - player_x)
            dy = abs(y - player_y)
            distance = max(dx, dy)  # Chebyshev distance
            is_within_sight = distance <= sight_radius
            
            # Determine color based on visibility
            if is_within_sight:
                # Within sight: nearly full brightness
                color = (
                    int(tile.color[0] * COLOR_FACTOR_SIGHT),
                    int(tile.color[1] * COLOR_FACTOR_SIGHT),
                    int(tile.color[2] * COLOR_FACTOR_SIGHT),
                )
            else:
                # Check timeout
                if current_time is not None:
                    last_seen = explored_tiles.get(tile_pos, 0.0)
                    time_since_seen = current_time - last_seen
                    is_within_timeout = time_since_seen <= timeout_hours
                else:
                    is_within_timeout = True
                
                if is_within_timeout:
                    # Memory: dimmed
                    color = (
                        int(tile.color[0] * COLOR_FACTOR_MEMORY),
                        int(tile.color[1] * COLOR_FACTOR_MEMORY),
                        int(tile.color[2] * COLOR_FACTOR_MEMORY),
                    )
                else:
                    # Old memory: very dim
                    color = (
                        int(tile.color[0] * COLOR_FACTOR_OLD),
                        int(tile.color[1] * COLOR_FACTOR_OLD),
                        int(tile.color[2] * COLOR_FACTOR_OLD),
                    )
            
            pygame.draw.rect(screen, color, rect)
    
    # Draw roads (before POIs so they appear under markers)
    if game.overworld_map.road_manager is not None:
        from ui.overworld.road_renderer import draw_roads
        roads_config = getattr(config, "roads", {})
        road_config = roads_config.get("rendering", {}) if isinstance(roads_config, dict) else {}
        draw_roads(
            screen,
            game.overworld_map.road_manager,
            game.overworld_map,
            start_x,
            start_y,
            end_x,
            end_y,
            tile_size,
            zoom,
            road_config,
            explored_tiles=explored_tiles,
            current_time=current_time,
            sight_radius=sight_radius,
            timeout_hours=timeout_hours,
            player_x=player_x,
            player_y=player_y,
        )
    
    # OPTIMIZATION: Pre-filter POIs by viewport before rendering
    all_pois = game.overworld_map.get_all_pois()
    visible_pois = [
        poi for poi in all_pois
        if start_x <= poi.position[0] < end_x and start_y <= poi.position[1] < end_y
    ]
    
    # OPTIMIZATION: Pre-calculate POI colors dict (avoid lookup in loop)
    poi_colors = {
        "dungeon": (200, 50, 50),
        "village": (50, 200, 50),
        "town": (50, 50, 200),
        "camp": (200, 200, 50),
    }
    
    # Draw POI markers and detect hover (only visible ones)
    hovered_poi = None
    for poi in visible_pois:
        px, py = poi.position
        
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
        
        # Get color (already defined above); use quest marker color if this POI is an active quest target
        color = poi_colors.get(poi.poi_type, (150, 150, 150))
        is_quest_target = _is_poi_quest_target(poi, game)
        if is_quest_target:
            color = QUEST_MARKER_COLOR
        
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
        
        # Quest marker: thin outer ring for POIs that are active quest objectives
        if is_quest_target:
            ring_radius = radius + max(2, int(2 * zoom))
            pygame.draw.circle(screen, QUEST_MARKER_RING_COLOR, (screen_x, screen_y), ring_radius, max(1, int(1 * zoom)))
        
        # Draw level indicator for dungeons (scale font with zoom)
        if poi.poi_type == "dungeon":
            # PERFORMANCE: Cache font by size
            font_size = max(8, int(12 * zoom))
            if not hasattr(game, "_overworld_font_cache"):
                game._overworld_font_cache = {}
            if font_size not in game._overworld_font_cache:
                game._overworld_font_cache[font_size] = pygame.font.Font(None, font_size)
            font = game._overworld_font_cache[font_size]
            
            # OPTIMIZATION: Cache level text surfaces (level rarely changes)
            level_cache_key = f"{poi.poi_id}_{font_size}"
            if not hasattr(game, "_poi_level_cache"):
                game._poi_level_cache = {}
            
            # OPTIMIZATION: Limit cache size
            MAX_POI_CACHE_SIZE = 100
            if len(game._poi_level_cache) > MAX_POI_CACHE_SIZE:
                cache_items = list(game._poi_level_cache.items())
                game._poi_level_cache = dict(cache_items[-MAX_POI_CACHE_SIZE:])
            
            if level_cache_key not in game._poi_level_cache:
                game._poi_level_cache[level_cache_key] = font.render(str(poi.level), True, (255, 255, 255))
            
            level_text = game._poi_level_cache[level_cache_key]
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
    
    # OPTIMIZATION: Pre-filter parties by viewport
    hovered_party = None
    if game.overworld_map.party_manager is not None:
        hovered_party = _draw_roaming_parties(
            game, screen, start_x, start_y, end_x, end_y, tile_size, zoom, 
            player_x, player_y, mouse_x, mouse_y, config, current_time, explored_tiles
        )
    
    # Draw minimap (toggle with M; single source of truth for visibility)
    if getattr(game, "show_minimap", True):
        _draw_minimap(game, screen, config, current_time, explored_tiles, timeout_hours)
    
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
            from world.overworld.party import get_party_type
            
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
    
    # Discovery log / codex overlay (L key)
    if getattr(game, "show_discovery_log", False):
        _draw_discovery_log(game, screen)
    
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
    explored_tiles: dict,  # Cached explored tiles dict
) -> Optional["RoamingParty"]:
    """
    Draw roaming parties on the overworld and detect hover (OPTIMIZED).
    
    Returns:
        The party being hovered over, or None
    """
    from world.overworld.party import get_party_type
    from world.overworld.party import RoamingParty
    
    party_manager = game.overworld_map.party_manager
    if party_manager is None:
        return None
    
    all_parties = party_manager.get_all_parties()
    hovered_party = None
    
    # OPTIMIZATION: Pre-filter parties by viewport
    visible_parties = [
        party for party in all_parties
        if start_x <= party.get_position()[0] < end_x and start_y <= party.get_position()[1] < end_y
    ]
    
    sight_radius = config.sight_radius
    timeout_hours = config.memory_timeout_hours
    
    for party in visible_parties:
        px, py = party.get_position()
        
        # OPTIMIZATION: Use cached explored_tiles and pre-calculated values
        # Calculate distance from player for sight radius check
        dx = abs(px - player_x)
        dy = abs(py - player_y)
        distance = max(dx, dy)  # Chebyshev distance
        is_within_sight = distance <= sight_radius
        
        # Parties within sight radius are always visible
        if is_within_sight:
            is_visible = True
        else:
            # Outside sight radius - must be explored AND within timeout
            if current_time is not None:
                tile_pos = (px, py)
                if tile_pos not in explored_tiles:
                    is_visible = False
                else:
                    last_seen = explored_tiles[tile_pos]
                    time_since_seen = current_time - last_seen
                    is_visible = time_since_seen <= timeout_hours
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
            # PERFORMANCE: Cache font by size
            font_size = max(8, int(10 * zoom))
            if not hasattr(game, "_overworld_font_cache"):
                game._overworld_font_cache = {}
            if font_size not in game._overworld_font_cache:
                game._overworld_font_cache[font_size] = pygame.font.Font(None, font_size)
            font = game._overworld_font_cache[font_size]
            
            # OPTIMIZATION: Cache icon text surfaces
            icon_cache_key = f"{party_type.icon}_{font_size}"
            if not hasattr(game, "_party_icon_cache"):
                game._party_icon_cache = {}
            
            # OPTIMIZATION: Limit cache size (party icons are limited, so small limit is fine)
            MAX_PARTY_CACHE_SIZE = 20
            if len(game._party_icon_cache) > MAX_PARTY_CACHE_SIZE:
                cache_items = list(game._party_icon_cache.items())
                game._party_icon_cache = dict(cache_items[-MAX_PARTY_CACHE_SIZE:])
            
            if icon_cache_key not in game._party_icon_cache:
                game._party_icon_cache[icon_cache_key] = font.render(party_type.icon, True, (255, 255, 255))
            
            icon_text = game._party_icon_cache[icon_cache_key]
            text_rect = icon_text.get_rect(center=(screen_x, screen_y))
            screen.blit(icon_text, text_rect)
    
    # Draw battle indicators
    _draw_battle_indicators(game, screen, start_x, start_y, end_x, end_y, tile_size, zoom, player_x, player_y, mouse_x, mouse_y, config, current_time, explored_tiles)
    
    return hovered_party


def _draw_battle_indicators(
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
    config,
    current_time: Optional[float],
    explored_tiles: dict,
) -> None:
    """Draw visual indicators for ongoing battles."""
    party_manager = game.overworld_map.party_manager
    if party_manager is None or not hasattr(party_manager, "active_battles"):
        return
    
    # Get battles in viewport
    battles_in_view = []
    for battle in party_manager.active_battles.values():
        bx, by = battle.position
        if start_x <= bx < end_x and start_y <= by < end_y:
            battles_in_view.append(battle)
    
    for battle in battles_in_view:
        bx, by = battle.position
        
        # Check visibility (same logic as parties)
        dx = abs(bx - player_x)
        dy = abs(by - player_y)
        distance = max(dx, dy)
        is_within_sight = distance <= config.sight_radius
        
        if is_within_sight:
            is_visible = True
        else:
            if current_time is not None:
                tile_pos = (bx, by)
                if tile_pos not in explored_tiles:
                    is_visible = False
                else:
                    last_seen = explored_tiles[tile_pos]
                    time_since_seen = current_time - last_seen
                    is_visible = time_since_seen <= config.memory_timeout_hours
            else:
                is_visible = game.overworld_map.is_explored(bx, by, current_time=None, timeout_hours=0.0)
        
        if not is_visible:
            continue
        
        # Calculate screen position
        screen_x = (bx - start_x) * tile_size + tile_size // 2
        screen_y = (by - start_y) * tile_size + tile_size // 2
        
        # Draw pulsing red circle to indicate battle
        import math
        import time
        pulse = (math.sin(time.time() * 3) + 1) / 2  # 0 to 1
        radius = int((8 + pulse * 4) * zoom)
        
        # Draw outer glow
        for i in range(3):
            alpha = int(100 * (1 - i / 3) * (0.5 + pulse * 0.5))
            color = (255, 0, 0, alpha)
            glow_radius = radius + i * 2
            # Create surface with per-pixel alpha
            glow_surface = pygame.Surface((glow_radius * 2 + 2, glow_radius * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, color, (glow_radius + 1, glow_radius + 1), glow_radius)
            screen.blit(glow_surface, (screen_x - glow_radius - 1, screen_y - glow_radius - 1))
        
        # Draw main battle indicator
        pygame.draw.circle(screen, (255, 0, 0), (screen_x, screen_y), radius, max(1, int(2 * zoom)))
        pygame.draw.circle(screen, (255, 100, 100), (screen_x, screen_y), radius - 1)
        
        # Draw "!" icon if player can join
        if battle.can_player_join and not battle.player_joined:
            font_size = max(10, int(12 * zoom))
            if not hasattr(game, "_battle_font_cache"):
                game._battle_font_cache = {}
            if font_size not in game._battle_font_cache:
                game._battle_font_cache[font_size] = pygame.font.Font(None, font_size)
            font = game._battle_font_cache[font_size]
            
            exclamation = font.render("!", True, (255, 255, 0))
            exclamation_rect = exclamation.get_rect(center=(screen_x, screen_y - radius - 8))
            screen.blit(exclamation, exclamation_rect)


# Minimap: default size (overridden by config.minimap_size), bounds, margin
MINIMAP_SIZE_DEFAULT = 160
MINIMAP_SIZE_MIN = 64
MINIMAP_SIZE_MAX = 320
MINIMAP_MARGIN = 10

# Discovery log panel
DISCOVERY_LOG_PANEL_WIDTH = 380
DISCOVERY_LOG_PANEL_MAX_HEIGHT = 400
DISCOVERY_LOG_LINE_HEIGHT = 22
DISCOVERY_LOG_MARGIN = 12


def _draw_minimap(
    game: "Game",
    screen: pygame.Surface,
    config,
    current_time: Optional[float],
    explored_tiles: dict,
    timeout_hours: float,
) -> None:
    """Draw a small corner minimap: terrain, explored fog, discovered POIs, player."""
    overworld_map = game.overworld_map
    if overworld_map is None:
        return
    size = getattr(config, "minimap_size", MINIMAP_SIZE_DEFAULT)
    size = max(MINIMAP_SIZE_MIN, min(MINIMAP_SIZE_MAX, size))
    w, h = overworld_map.width, overworld_map.height
    player_x, player_y = overworld_map.get_player_position()
    # Bottom-right corner, above help panel
    screen_w, screen_h = screen.get_size()
    mm_x = screen_w - size - MINIMAP_MARGIN
    mm_y = screen_h - size - MINIMAP_MARGIN - 50  # Above help strip
    mm_y = max(MINIMAP_MARGIN, mm_y)
    
    # Build minimap surface (one pixel per tile sample)
    surf = pygame.Surface((size, size))
    for py in range(size):
        for px in range(size):
            tx = min(w - 1, (px * w) // size)
            ty = min(h - 1, (py * h) // size)
            tile = overworld_map.get_tile(tx, ty)
            if tile is None:
                color = (40, 40, 40)
            else:
                color = tile.color
            # Fog: dim if not explored or expired
            tile_pos = (tx, ty)
            if tile_pos not in explored_tiles:
                color = tuple(int(c * 0.2) for c in color)
            elif current_time is not None:
                last_seen = explored_tiles.get(tile_pos, 0.0)
                if current_time - last_seen > timeout_hours:
                    color = tuple(int(c * 0.35) for c in color)
            else:
                color = tuple(color)
            surf.set_at((px, py), color)
    
    # POI dots (discovered only)
    poi_colors = {"dungeon": (200, 50, 50), "village": (50, 200, 50), "town": (50, 50, 200), "camp": (200, 200, 50)}
    for poi in overworld_map.get_all_pois():
        if not poi.discovered:
            continue
        mx = (poi.position[0] * size) // w
        my = (poi.position[1] * size) // h
        mx = max(0, min(size - 1, mx))
        my = max(0, min(size - 1, my))
        dot = poi_colors.get(poi.poi_type, (150, 150, 150))
        pygame.draw.circle(surf, dot, (mx, my), max(1, size // 96))
    
    # Player dot
    px = (player_x * size) // w
    py = (player_y * size) // h
    px = max(0, min(size - 1, px))
    py = max(0, min(size - 1, py))
    pygame.draw.circle(surf, (255, 255, 0), (px, py), max(2, size // 48))
    
    # Border and panel background
    panel = pygame.Surface((size + 4, size + 4), pygame.SRCALPHA)
    panel.fill(COLOR_BG_PANEL)
    pygame.draw.rect(panel, COLOR_BORDER_BRIGHT, (0, 0, size + 4, size + 4), 2)
    screen.blit(panel, (mm_x - 2, mm_y - 2))
    screen.blit(surf, (mm_x, mm_y))


def _draw_discovery_log(game: "Game", screen: pygame.Surface) -> None:
    """Draw the discovery log (codex) overlay: list of discovered POIs with name, type, level, cleared."""
    if game.overworld_map is None:
        return
    log = getattr(game.overworld_map, "discovery_log", [])
    if not hasattr(game, "_overworld_ui_font"):
        game._overworld_ui_font = pygame.font.Font(None, 24)
    font = game._overworld_ui_font
    font_title = pygame.font.Font(None, 28)
    
    # Resolve cleared state: use current POI if on map, else use stored
    def get_cleared(entry: dict) -> bool:
        poi = game.overworld_map.pois.get(entry.get("poi_id"))
        return poi.cleared if poi else entry.get("cleared", False)
    
    title_surf = font_title.render("Discovery Log (L to close)", True, COLOR_TEXT)
    panel_content_h = DISCOVERY_LOG_LINE_HEIGHT * max(1, len(log)) + 40
    panel_h = min(DISCOVERY_LOG_PANEL_MAX_HEIGHT, panel_content_h + 40)
    panel_w = DISCOVERY_LOG_PANEL_WIDTH
    screen_w, screen_h = screen.get_size()
    panel_x = (screen_w - panel_w) // 2
    panel_y = (screen_h - panel_h) // 2
    
    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    panel.fill(COLOR_BG_PANEL)
    pygame.draw.rect(panel, COLOR_BORDER_BRIGHT, (0, 0, panel_w, panel_h), 2)
    screen.blit(panel, (panel_x, panel_y))
    screen.blit(title_surf, (panel_x + DISCOVERY_LOG_MARGIN, panel_y + 8))
    
    scroll = getattr(game, "discovery_log_scroll_offset", 0)
    visible_lines = (panel_h - 50) // DISCOVERY_LOG_LINE_HEIGHT
    y_start = panel_y + 36
    for i, entry in enumerate(log):
        line_y = y_start + i * DISCOVERY_LOG_LINE_HEIGHT - scroll
        if line_y < y_start - DISCOVERY_LOG_LINE_HEIGHT or line_y > panel_y + panel_h - 10:
            continue
        name = entry.get("name", "?")
        poi_type = entry.get("poi_type", "?")
        level = entry.get("level", 1)
        cleared = get_cleared(entry)
        status = "Cleared" if cleared else "Active"
        text = f"{name} — {poi_type.title()} Lv.{level} ({status})"
        surf = font.render(text, True, COLOR_TEXT)
        screen.blit(surf, (panel_x + DISCOVERY_LOG_MARGIN, line_y))
    
    if not log:
        empty_surf = font.render("No locations discovered yet.", True, COLOR_SUBTITLE)
        screen.blit(empty_surf, (panel_x + DISCOVERY_LOG_MARGIN, y_start))


def _draw_overworld_ui(game: "Game", screen: pygame.Surface) -> None:
    """Draw UI overlay (time, position, etc.) with polished panels (OPTIMIZED with caching)."""
    # PERFORMANCE: Cache UI font
    if not hasattr(game, "_overworld_ui_font"):
        game._overworld_ui_font = pygame.font.Font(None, 24)
    font = game._overworld_ui_font
    
    # OPTIMIZATION: Cache UI surfaces (only recreate if changed)
    if not hasattr(game, "_overworld_ui_cache"):
        game._overworld_ui_cache = {}
    
    # OPTIMIZATION: Limit cache size to prevent memory bloat (keep last 50 entries)
    MAX_UI_CACHE_SIZE = 50
    if len(game._overworld_ui_cache) > MAX_UI_CACHE_SIZE:
        # Remove oldest entries (simple: keep only most recent)
        cache_items = list(game._overworld_ui_cache.items())
        game._overworld_ui_cache = dict(cache_items[-MAX_UI_CACHE_SIZE:])
    
    # Top-left info panel
    info_panel_width = 250
    info_panel_height = 80
    info_panel_x = 10
    info_panel_y = 10
    
    # OPTIMIZATION: Cache panel surface
    panel_key = f"info_{info_panel_width}_{info_panel_height}"
    if panel_key not in game._overworld_ui_cache:
        info_panel = pygame.Surface((info_panel_width, info_panel_height), pygame.SRCALPHA)
        info_panel.fill(COLOR_BG_PANEL)
        pygame.draw.rect(info_panel, COLOR_BORDER_BRIGHT, (0, 0, info_panel_width, info_panel_height), 2)
        game._overworld_ui_cache[panel_key] = info_panel
    else:
        info_panel = game._overworld_ui_cache[panel_key]
    
    screen.blit(info_panel, (info_panel_x, info_panel_y))
    
    # Time display (cache text surface)
    if game.time_system is not None:
        time_text = game.time_system.get_time_string()
        time_cache_key = f"time_{time_text}"
        if time_cache_key not in game._overworld_ui_cache:
            game._overworld_ui_cache[time_cache_key] = font.render(time_text, True, COLOR_TEXT)
        time_surface = game._overworld_ui_cache[time_cache_key]
        screen.blit(time_surface, (info_panel_x + 12, info_panel_y + 12))
    
    # Position display (cache text surface)
    if game.overworld_map is not None:
        x, y = game.overworld_map.get_player_position()
        pos_text = f"Position: ({x}, {y})"
        pos_cache_key = f"pos_{x}_{y}"
        if pos_cache_key not in game._overworld_ui_cache:
            game._overworld_ui_cache[pos_cache_key] = font.render(pos_text, True, COLOR_TEXT)
        pos_surface = game._overworld_ui_cache[pos_cache_key]
        screen.blit(pos_surface, (info_panel_x + 12, info_panel_y + 40))
    
    # Top-right zoom panel
    if hasattr(game, "overworld_zoom"):
        zoom_value = game.overworld_zoom
        zoom_text = f"Zoom: {int(zoom_value * 100)}%"
        zoom_cache_key = f"zoom_{int(zoom_value * 100)}"
        if zoom_cache_key not in game._overworld_ui_cache:
            zoom_surface = font.render(zoom_text, True, COLOR_SUBTITLE)
            game._overworld_ui_cache[zoom_cache_key] = zoom_surface
        else:
            zoom_surface = game._overworld_ui_cache[zoom_cache_key]
        
        zoom_panel_width = zoom_surface.get_width() + 24
        zoom_panel_height = 40
        zoom_panel_x = screen.get_width() - zoom_panel_width - 10
        zoom_panel_y = 10
        
        zoom_panel_key = f"zoom_panel_{zoom_panel_width}_{zoom_panel_height}"
        if zoom_panel_key not in game._overworld_ui_cache:
            zoom_panel = pygame.Surface((zoom_panel_width, zoom_panel_height), pygame.SRCALPHA)
            zoom_panel.fill(COLOR_BG_PANEL)
            pygame.draw.rect(zoom_panel, COLOR_BORDER_BRIGHT, (0, 0, zoom_panel_width, zoom_panel_height), 2)
            game._overworld_ui_cache[zoom_panel_key] = zoom_panel
        else:
            zoom_panel = game._overworld_ui_cache[zoom_panel_key]
        
        screen.blit(zoom_panel, (zoom_panel_x, zoom_panel_y))
        screen.blit(zoom_surface, (zoom_panel_x + 12, zoom_panel_y + 10))
    
    # Bottom instructions panel (static - cache it)
    help_cache_key = "help_panel"
    if help_cache_key not in game._overworld_ui_cache:
        help_text = "WASD: Move | E: Enter | M: Minimap | +/-: Zoom | 0: Reset | I: Inventory | C: Character | L: Discovery Log | H: Tutorial"
        help_surface = font.render(help_text, True, COLOR_TEXT)
        help_panel_width = help_surface.get_width() + 24
        help_panel_height = 40
        
        help_panel = pygame.Surface((help_panel_width, help_panel_height), pygame.SRCALPHA)
        help_panel.fill(COLOR_BG_PANEL)
        pygame.draw.rect(help_panel, COLOR_BORDER_BRIGHT, (0, 0, help_panel_width, help_panel_height), 2)
        
        game._overworld_ui_cache[help_cache_key] = (help_panel, help_surface, help_panel_width, help_panel_height)
    
    help_panel, help_surface, help_panel_width, help_panel_height = game._overworld_ui_cache[help_cache_key]
    help_panel_x = 10
    help_panel_y = screen.get_height() - help_panel_height - 10
    screen.blit(help_panel, (help_panel_x, help_panel_y))
    screen.blit(help_surface, (help_panel_x + 12, help_panel_y + 10))


def _draw_message(game: "Game", screen: pygame.Surface) -> None:
    """Draw the last message at the bottom of the screen (OPTIMIZED with caching)."""
    if not hasattr(game, "last_message") or not game.last_message:
        return
    
    # Cache font
    if not hasattr(game, "_overworld_ui_font"):
        game._overworld_ui_font = pygame.font.Font(None, 24)
    font = game._overworld_ui_font
    
    # OPTIMIZATION: Cache message surface
    if not hasattr(game, "_overworld_ui_cache"):
        game._overworld_ui_cache = {}
    
    message_cache_key = f"msg_{game.last_message}"
    if message_cache_key not in game._overworld_ui_cache:
        text_surface = font.render(game.last_message, True, COLOR_TEXT)
        game._overworld_ui_cache[message_cache_key] = text_surface
    else:
        text_surface = game._overworld_ui_cache[message_cache_key]
    
    # Center at bottom
    message_panel_width = text_surface.get_width() + 40
    message_panel_height = 50
    x = (screen.get_width() - message_panel_width) // 2
    y = screen.get_height() - 100
    
    # OPTIMIZATION: Cache message panel
    panel_cache_key = f"msg_panel_{message_panel_width}_{message_panel_height}"
    if panel_cache_key not in game._overworld_ui_cache:
        message_shadow = pygame.Surface((message_panel_width + 4, message_panel_height + 4), pygame.SRCALPHA)
        message_shadow.fill((0, 0, 0, 100))
        message_panel = pygame.Surface((message_panel_width, message_panel_height), pygame.SRCALPHA)
        message_panel.fill(COLOR_BG_PANEL)
        pygame.draw.rect(message_panel, COLOR_BORDER_BRIGHT, (0, 0, message_panel_width, message_panel_height), 2)
        game._overworld_ui_cache[panel_cache_key] = (message_shadow, message_panel)
    else:
        message_shadow, message_panel = game._overworld_ui_cache[panel_cache_key]
    
    screen.blit(message_shadow, (x - 2, y - 2))
    screen.blit(message_panel, (x, y))
    screen.blit(text_surface, (x + 20, y + 15))
