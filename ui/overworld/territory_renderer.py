"""
Territory visualization for the overworld.

Renders faction territories as an optional overlay on the map.
"""

import pygame
from typing import TYPE_CHECKING, Optional, Tuple

if TYPE_CHECKING:
    from world.overworld.map import OverworldMap
    from world.overworld.territory_manager import TerritoryManager, Territory
    from systems.factions import Faction


def draw_territory_overlay(
    screen: pygame.Surface,
    overworld_map: "OverworldMap",
    territory_manager: "TerritoryManager",
    start_x: int,
    start_y: int,
    end_x: int,
    end_y: int,
    tile_size: int,
    opacity: float = 0.3,
    player_x: int = 0,
    player_y: int = 0,
    explored_tiles: dict = None,
    current_time: float = None,
    sight_radius: int = 8,
    timeout_hours: float = 12.0,
) -> None:
    """
    Draw territory overlay on the overworld map (OPTIMIZED - only visible tiles).
    
    Args:
        screen: Screen surface to draw on
        overworld_map: Overworld map
        territory_manager: Territory manager
        start_x, start_y: Viewport start (tile coordinates)
        end_x, end_y: Viewport end (tile coordinates)
        tile_size: Size of each tile in pixels
        opacity: Overlay opacity (0.0 to 1.0)
        player_x, player_y: Player position (for fog of war)
        explored_tiles: Dict of explored tiles (for fog of war)
        current_time: Current time (for fog of war timeout)
        sight_radius: Sight radius (for fog of war)
        timeout_hours: Hours after which explored tiles fade (use OverworldConfig.memory_timeout_hours)
    """
    if not territory_manager or not territory_manager.enabled or not territory_manager.initialized:
        return
    
    if not overworld_map.faction_manager:
        return
    
    if explored_tiles is None:
        explored_tiles = {}
    
    # OPTIMIZATION: Get only territories in viewport (uses optimized method)
    visible_territories = territory_manager.get_territories_in_viewport(
        start_x, start_y, end_x, end_y
    )
    
    if not visible_territories:
        return  # No territories in viewport
    
    # Create a surface for the overlay (with alpha)
    overlay = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
    
    # OPTIMIZATION: Build a map of tile -> territory for faster lookup
    tile_to_territory = {}
    for territory in visible_territories:
        for tile_x, tile_y in territory.controlled_tiles:
            # Only include tiles in viewport
            if start_x <= tile_x < end_x and start_y <= tile_y < end_y:
                tile_to_territory[(tile_x, tile_y)] = territory
    
    # OPTIMIZATION: Draw territories tile-by-tile in viewport order (cache-friendly)
    # Group by faction to reduce color lookups
    faction_colors = {}
    
    for y in range(start_y, end_y):
        for x in range(start_x, end_x):
            # Check if this tile has a territory
            territory = tile_to_territory.get((x, y))
            if not territory:
                continue
            
            # Check fog of war - only show territories for explored tiles
            tile_pos = (x, y)
            was_explored = tile_pos in explored_tiles
            
            if not was_explored:
                continue  # Don't show territories in fog of war
            
            # Check if within sight or timeout (same logic as terrain rendering)
            dx = abs(x - player_x)
            dy = abs(y - player_y)
            distance = max(dx, dy)
            is_within_sight = distance <= sight_radius
            
            is_within_timeout = True
            if current_time is not None and was_explored and not is_within_sight:
                last_seen = explored_tiles.get(tile_pos, 0.0)
                time_since_seen = current_time - last_seen
                is_within_timeout = time_since_seen <= timeout_hours
            
            # Only show territory if within sight or within timeout
            if not is_within_sight and not is_within_timeout:
                continue
            
            # Get faction color (cache it)
            if territory.faction_id not in faction_colors:
                faction = overworld_map.faction_manager.get_faction(territory.faction_id)
                if not faction:
                    continue
                base_color = faction.color
                faction_colors[territory.faction_id] = (
                    base_color[0],
                    base_color[1],
                    base_color[2],
                    int(255 * opacity),
                )
            
            overlay_color = faction_colors[territory.faction_id]
            
            # Calculate screen position
            screen_x = (x - start_x) * tile_size
            screen_y = (y - start_y) * tile_size
            rect = pygame.Rect(screen_x, screen_y, tile_size, tile_size)
            
            # Draw semi-transparent rectangle
            pygame.draw.rect(overlay, overlay_color, rect)
    
    # OPTIMIZATION: Draw border conflicts only for visible territories
    # Cache conflict pairs to avoid duplicate checks
    conflict_pairs = set()
    for territory in visible_territories:
        for other_territory in visible_territories:
            if other_territory.territory_id == territory.territory_id:
                continue
            
            pair_key = tuple(sorted([territory.territory_id, other_territory.territory_id]))
            if pair_key in conflict_pairs:
                continue
            conflict_pairs.add(pair_key)
            
            if territory_manager.has_border_conflict(territory, other_territory):
                conflict_strength = territory_manager.get_conflict_strength(territory, other_territory)
                
                # Draw red border on conflict tiles
                conflict_color = (
                    255,
                    0,
                    0,
                    int(255 * opacity * conflict_strength),
                )
                
                # Only draw border tiles in viewport
                for tile_x, tile_y in territory.border_tiles:
                    if not (start_x <= tile_x < end_x and start_y <= tile_y < end_y):
                        continue
                    
                    # Check if explored
                    if (tile_x, tile_y) not in explored_tiles:
                        continue
                    
                    # Check if this border tile is adjacent to the conflicting territory
                    is_conflict_border = False
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        neighbor_x = tile_x + dx
                        neighbor_y = tile_y + dy
                        neighbor_territory = territory_manager.get_territory_at(neighbor_x, neighbor_y)
                        if neighbor_territory and neighbor_territory.territory_id == other_territory.territory_id:
                            is_conflict_border = True
                            break
                    
                    if is_conflict_border:
                        # Calculate screen position
                        screen_x = (tile_x - start_x) * tile_size
                        screen_y = (tile_y - start_y) * tile_size
                        rect = pygame.Rect(screen_x, screen_y, tile_size, tile_size)
                        
                        # Draw red border
                        pygame.draw.rect(overlay, conflict_color, rect, max(1, tile_size // 4))
    
    # Blit overlay onto screen
    screen.blit(overlay, (0, 0))


def get_territory_info_at(
    x: int,
    y: int,
    overworld_map: "OverworldMap",
    territory_manager: Optional["TerritoryManager"],
) -> Optional[Tuple["Territory", "Faction"]]:
    """
    Get territory and faction information at the given coordinates.
    
    Args:
        x, y: Tile coordinates
        overworld_map: Overworld map
        territory_manager: Territory manager
        
    Returns:
        Tuple of (Territory, Faction) or None
    """
    if not territory_manager or not territory_manager.enabled:
        return None
    
    territory = territory_manager.get_territory_at(x, y)
    if not territory:
        return None
    
    if not overworld_map.faction_manager:
        return None
    
    faction = overworld_map.faction_manager.get_faction(territory.faction_id)
    if not faction:
        return None
    
    return (territory, faction)

