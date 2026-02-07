"""
Road rendering system.

Renders roads on the overworld map with customizable visual styles.
"""

import pygame
from typing import Dict, Tuple, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from world.overworld.map import OverworldMap
    from world.overworld.road_manager import RoadManager


# Road visual styles (color, pattern, etc.)
# Made brighter and more visually distinct
ROAD_STYLES: Dict[str, Dict] = {
    "dirt": {
        "color": (180, 140, 100),  # Warm tan/brown
        "border_color": (140, 100, 70),  # Darker brown border
        "width": 1,
        "pattern": "solid",
        "center_line": False,  # No center line for dirt roads
    },
    "cobblestone": {
        "color": (150, 150, 150),  # Medium-light gray
        "border_color": (110, 110, 110),  # Darker gray border
        "width": 1,
        "pattern": "checkered",  # Checkered pattern for cobblestone
        "center_line": False,
    },
    "highway": {
        "color": (220, 220, 220),  # Very light gray (almost white)
        "border_color": (160, 160, 160),  # Medium gray border
        "width": 2,  # Wider roads (2 tiles)
        "pattern": "solid",
        "center_line": True,  # Center line for highways
        "center_line_color": (255, 255, 0),  # Yellow center line
    },
}


def draw_roads(
    screen: pygame.Surface,
    road_manager: "RoadManager",
    overworld_map: "OverworldMap",
    start_x: int,
    start_y: int,
    end_x: int,
    end_y: int,
    tile_size: int,
    zoom: float = 1.0,
    config: Optional[Dict] = None,
    explored_tiles: Optional[Dict] = None,
    current_time: Optional[float] = None,
    sight_radius: int = 8,
    timeout_hours: float = 12.0,
    player_x: int = 0,
    player_y: int = 0,
) -> None:
    """
    Draw roads on the overworld map.
    
    Args:
        screen: Pygame surface to draw on
        road_manager: Road manager with road data
        overworld_map: Overworld map
        start_x, start_y: Viewport start (tile coordinates)
        end_x, end_y: Viewport end (tile coordinates)
        tile_size: Size of each tile in pixels
        zoom: Current zoom level
        config: Optional rendering configuration
    """
    if config is None:
        config = {}
    
    # Check if roads are enabled (default to True if not specified)
    # Note: "enabled" is in the main roads config, not rendering config
    # So we always render if road_manager exists
    
    # Get visible road segments
    visible_segments = road_manager.get_road_segments_in_viewport(
        start_x, start_y, end_x, end_y
    )
    
    if not visible_segments:
        return
    
    # Get rendering options
    opacity = config.get("opacity", 1.0)
    show_borders = config.get("show_borders", True)
    border_width = max(1, int(config.get("border_width", 1) * zoom))
    
    # Draw each road segment (only if explored - respect fog of war)
    for x, y in visible_segments:
        # Check fog of war - only show roads on explored tiles
        tile_pos = (x, y)
        if explored_tiles is not None:
            was_explored = tile_pos in explored_tiles
            if not was_explored:
                continue  # Don't show roads in unexplored areas
            
            # Check if within sight radius or within timeout
            dx = abs(x - player_x)
            dy = abs(y - player_y)
            distance = max(dx, dy)  # Chebyshev distance
            is_within_sight = distance <= sight_radius
            
            if not is_within_sight:
                # Outside sight: check timeout
                if current_time is not None:
                    last_seen = explored_tiles.get(tile_pos, 0.0)
                    time_since_seen = current_time - last_seen
                    if time_since_seen > timeout_hours:
                        continue  # Too old, don't show
        
        # Calculate screen position
        screen_x = (x - start_x) * tile_size
        screen_y = (y - start_y) * tile_size
        
        # Get road type at this position
        road_type = road_manager.get_road_type_at(x, y)
        if not road_type:
            continue
        
        # Get road style
        style = ROAD_STYLES.get(road_type, ROAD_STYLES["dirt"])
        
        # Check if this is a junction (multiple roads meet)
        try:
            is_junction = road_manager.is_road_junction(x, y)
        except Exception:
            is_junction = False  # Fallback if junction check fails
        
        # Apply opacity
        base_color = style["color"]
        if opacity < 1.0:
            # Blend with underlying terrain (simplified)
            color = tuple(int(c * opacity) for c in base_color)
        else:
            color = base_color
        
        # Ensure color is visible (boost brightness to stand out from terrain)
        # Roads should be clearly visible, so ensure minimum brightness
        min_brightness = 100  # Minimum RGB value to ensure visibility
        color = tuple(max(min_brightness, c) for c in color)
        
        # Junctions are slightly brighter to stand out
        if is_junction:
            color = tuple(min(255, c + 20) for c in color)
        
        # Draw road tile (handle width > 1 for highways)
        road_width = style.get("width", 1)
        road_rect = pygame.Rect(screen_x, screen_y, tile_size, tile_size)
        
        # Draw based on pattern
        if style["pattern"] == "checkered":
            # Checkered pattern for cobblestone
            _draw_checkered_road(screen, road_rect, color, style["border_color"], tile_size)
        else:
            # Solid road
            pygame.draw.rect(screen, color, road_rect)
            
            # Draw center line for highways
            if style.get("center_line", False) and road_width >= 1:
                center_line_color = style.get("center_line_color", (255, 255, 0))
                center_y = road_rect.y + road_rect.height // 2
                line_width = max(1, int(2 * zoom))
                pygame.draw.line(
                    screen,
                    center_line_color,
                    (road_rect.x, center_y),
                    (road_rect.x + road_rect.width, center_y),
                    line_width
                )
            
            # Draw border if enabled
            if show_borders:
                border_color = style["border_color"]
                if opacity < 1.0:
                    border_color = tuple(int(c * opacity) for c in border_color)
                pygame.draw.rect(screen, border_color, road_rect, border_width)


def _draw_checkered_road(
    screen: pygame.Surface,
    rect: pygame.Rect,
    color: Tuple[int, int, int],
    border_color: Tuple[int, int, int],
    tile_size: int,
) -> None:
    """Draw a checkered pattern for cobblestone roads."""
    # Draw base color
    pygame.draw.rect(screen, color, rect)
    
    # Draw checkered pattern (simplified - alternating squares)
    check_size = max(2, tile_size // 4)
    x, y = rect.x, rect.y
    
    for i in range(0, tile_size, check_size * 2):
        for j in range(0, tile_size, check_size * 2):
            # Draw darker squares in checker pattern
            check_rect = pygame.Rect(x + i, y + j, check_size, check_size)
            pygame.draw.rect(screen, border_color, check_rect)
            
            # Draw opposite squares
            check_rect2 = pygame.Rect(x + i + check_size, y + j + check_size, check_size, check_size)
            if check_rect2.right <= rect.right and check_rect2.bottom <= rect.bottom:
                pygame.draw.rect(screen, border_color, check_rect2)


def get_road_style(road_type: str) -> Dict:
    """
    Get visual style for a road type.
    
    Args:
        road_type: Type of road
        
    Returns:
        Dictionary with style properties
    """
    return ROAD_STYLES.get(road_type, ROAD_STYLES["dirt"])


def register_road_style(
    road_type: str,
    color: Tuple[int, int, int],
    border_color: Optional[Tuple[int, int, int]] = None,
    width: int = 1,
    pattern: str = "solid",
) -> None:
    """
    Register a custom road style.
    
    Args:
        road_type: Type identifier for the road
        color: Base color (RGB tuple)
        border_color: Border color (if None, uses darker version of color)
        width: Road width in tiles
        pattern: Pattern type ("solid", "checkered", etc.)
    """
    if border_color is None:
        # Auto-generate darker border
        border_color = tuple(max(0, c - 30) for c in color)
    
    ROAD_STYLES[road_type] = {
        "color": color,
        "border_color": border_color,
        "width": width,
        "pattern": pattern,
    }


