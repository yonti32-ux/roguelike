"""
Village map generation.
"""

import random
import math
from typing import List, Tuple, Optional

from settings import WINDOW_WIDTH, WINDOW_HEIGHT, TILE_SIZE
from ..game_map import GameMap
from ..tiles import WALL_TILE
from .tiles import (
    VILLAGE_PATH_TILE,
    VILLAGE_PLAZA_TILE,
    VILLAGE_GRASS_TILE,
    BUILDING_FLOOR_TILE,
    BUILDING_WALL_TILE,
    BUILDING_ENTRANCE_TILE,
)
from .buildings import Building, place_buildings
from .npcs import VillageNPC, create_npc_for_building


def generate_village(
    level: int,
    village_name: str,
    seed: Optional[int] = None,
) -> GameMap:
    """
    Generate a complete village map.
    
    Args:
        level: Village level (affects size and building count)
        village_name: Name of the village (for potential future use)
        seed: Random seed for deterministic generation
        
    Returns:
        GameMap instance with village layout
    """
    if seed is not None:
        random.seed(seed)
    
    # Calculate village size based on level
    base_tiles_x = WINDOW_WIDTH // TILE_SIZE
    base_tiles_y = WINDOW_HEIGHT // TILE_SIZE
    
    # Village size scaling
    if level <= 3:
        # Small village
        scale = random.uniform(0.9, 1.1)
    elif level <= 7:
        # Medium village
        scale = random.uniform(1.1, 1.4)
    else:
        # Large village
        scale = random.uniform(1.4, 1.8)
    
    map_width = int(base_tiles_x * scale)
    map_height = int(base_tiles_y * scale)
    
    # Ensure minimum size
    map_width = max(30, map_width)
    map_height = max(30, map_height)
    
    # Create empty map (all walls initially)
    tiles = [[WALL_TILE for _ in range(map_width)] for _ in range(map_height)]
    
    # Place central plaza
    plaza_x, plaza_y, plaza_w, plaza_h = _place_plaza(map_width, map_height, level)
    _carve_area(tiles, plaza_x, plaza_y, plaza_w, plaza_h, VILLAGE_PLAZA_TILE)
    
    # Place buildings
    buildings = place_buildings(map_width, map_height, level, seed)
    
    # Carve buildings into map
    npcs: List[VillageNPC] = []
    for i, building in enumerate(buildings):
        building_id = f"building_{i}"
        
        # Carve building interior (floor tiles)
        _carve_area(
            tiles,
            building.x + 1,  # Leave 1 tile border for walls
            building.y + 1,
            building.width - 2,
            building.height - 2,
            BUILDING_FLOOR_TILE,
        )
        
        # Add building walls around perimeter
        _add_building_walls(tiles, building)
        
        # Place building entrance (door) on wall facing plaza
        entrance_x, entrance_y = _place_building_entrance(tiles, building, plaza_center_x, plaza_center_y)
        building.entrance_x = entrance_x
        building.entrance_y = entrance_y
        
        # Create NPC for building
        center_x, center_y = building.center()
        npc = create_npc_for_building(
            building.building_type,
            center_x,
            center_y,
            npc_id=f"{building.building_type}_{i}",
            building_id=building_id,
        )
        if npc:
            npcs.append(npc)
    
    # Create paths from entrance to plaza, and plaza to buildings
    entrance_x = map_width // 2
    entrance_y = map_height - 2
    
    # Ensure entrance is walkable (path tile)
    if 0 <= entrance_x < map_width and 0 <= entrance_y < map_height:
        tiles[entrance_y][entrance_x] = VILLAGE_PATH_TILE
    
    # Path from entrance to plaza
    plaza_center_x = plaza_x + plaza_w // 2
    plaza_center_y = plaza_y + plaza_h // 2
    _create_path(tiles, entrance_x, entrance_y, plaza_center_x, plaza_center_y)
    
    # Paths from plaza to each building entrance
    for building in buildings:
        if building.entrance_x is not None and building.entrance_y is not None:
            # Path to entrance (one tile outside the building)
            # Find the tile just outside the entrance
            entrance_outside_x = building.entrance_x
            entrance_outside_y = building.entrance_y
            
            # Determine which side the entrance is on and place outside tile
            if building.entrance_x == building.x:  # Left wall
                entrance_outside_x = building.x - 1
            elif building.entrance_x == building.x2 - 1:  # Right wall
                entrance_outside_x = building.x2
            elif building.entrance_y == building.y:  # Top wall
                entrance_outside_y = building.y - 1
            elif building.entrance_y == building.y2 - 1:  # Bottom wall
                entrance_outside_y = building.y2
            
            # Ensure outside tile is within bounds
            if 0 <= entrance_outside_x < map_width and 0 <= entrance_outside_y < map_height:
                tiles[entrance_outside_y][entrance_outside_x] = VILLAGE_PATH_TILE
                _create_path(tiles, plaza_center_x, plaza_center_y, entrance_outside_x, entrance_outside_y)
    
    # Fill remaining space with grass
    for y in range(map_height):
        for x in range(map_width):
            if tiles[y][x] == WALL_TILE:
                tiles[y][x] = VILLAGE_GRASS_TILE
    
    # Create GameMap
    village_map = GameMap(
        tiles=tiles,
        up_stairs=None,  # Villages don't have stairs
        down_stairs=None,
        entities=npcs,
        rooms=[],  # Villages don't use room system
    )
    
    # Store entrance position for player placement
    village_map.village_entrance = (entrance_x, entrance_y)
    
    return village_map


def _place_plaza(
    map_width: int,
    map_height: int,
    level: int,
) -> Tuple[int, int, int, int]:
    """
    Place the central plaza.
    
    Returns:
        (x, y, width, height) of plaza
    """
    # Plaza size based on level
    if level <= 3:
        # Small plaza
        min_size = 6
        max_size = 8
    elif level <= 7:
        # Medium plaza
        min_size = 8
        max_size = 10
    else:
        # Large plaza
        min_size = 10
        max_size = 12
    
    plaza_w = random.randint(min_size, max_size)
    plaza_h = random.randint(min_size, max_size)
    
    # Center the plaza
    plaza_x = (map_width - plaza_w) // 2
    plaza_y = (map_height - plaza_h) // 2
    
    return plaza_x, plaza_y, plaza_w, plaza_h


def _carve_area(
    tiles: List[List],
    x: int,
    y: int,
    width: int,
    height: int,
    tile_type,
) -> None:
    """Carve out an area with a specific tile type."""
    for dy in range(height):
        for dx in range(width):
            tx = x + dx
            ty = y + dy
            if 0 <= tx < len(tiles[0]) and 0 <= ty < len(tiles):
                tiles[ty][tx] = tile_type


def _add_building_walls(
    tiles: List[List],
    building: Building,
) -> None:
    """Add walls around a building perimeter."""
    # Top and bottom walls
    for x in range(building.x, building.x2):
        if 0 <= x < len(tiles[0]):
            # Top wall
            if 0 <= building.y < len(tiles):
                tiles[building.y][x] = BUILDING_WALL_TILE
            # Bottom wall
            if 0 <= building.y2 - 1 < len(tiles):
                tiles[building.y2 - 1][x] = BUILDING_WALL_TILE
    
    # Left and right walls
    for y in range(building.y, building.y2):
        if 0 <= y < len(tiles):
            # Left wall
            if 0 <= building.x < len(tiles[0]):
                tiles[y][building.x] = BUILDING_WALL_TILE
            # Right wall
            if 0 <= building.x2 - 1 < len(tiles[0]):
                tiles[y][building.x2 - 1] = BUILDING_WALL_TILE


def _place_building_entrance(
    tiles: List[List],
    building: Building,
    plaza_x: int,
    plaza_y: int,
) -> Tuple[int, int]:
    """
    Place a building entrance (door) on the wall closest to the plaza.
    
    Returns:
        (entrance_x, entrance_y) tile coordinates
    """
    building_center_x, building_center_y = building.center()
    
    # Determine which wall is closest to plaza
    dx = plaza_x - building_center_x
    dy = plaza_y - building_center_y
    
    # Choose wall based on direction to plaza
    if abs(dx) > abs(dy):
        # Closer horizontally - use left or right wall
        if dx > 0:
            # Plaza is to the right - use right wall
            entrance_x = building.x2 - 1
            entrance_y = building.y + building.height // 2
        else:
            # Plaza is to the left - use left wall
            entrance_x = building.x
            entrance_y = building.y + building.height // 2
    else:
        # Closer vertically - use top or bottom wall
        if dy > 0:
            # Plaza is below - use bottom wall
            entrance_x = building.x + building.width // 2
            entrance_y = building.y2 - 1
        else:
            # Plaza is above - use top wall
            entrance_x = building.x + building.width // 2
            entrance_y = building.y
    
    # Ensure entrance is within building bounds
    entrance_x = max(building.x, min(entrance_x, building.x2 - 1))
    entrance_y = max(building.y, min(entrance_y, building.y2 - 1))
    
    # Place entrance tile (replaces wall tile)
    if 0 <= entrance_x < len(tiles[0]) and 0 <= entrance_y < len(tiles):
        tiles[entrance_y][entrance_x] = BUILDING_ENTRANCE_TILE
    
    return entrance_x, entrance_y


def _create_path(
    tiles: List[List],
    x1: int,
    y1: int,
    x2: int,
    y2: int,
) -> None:
    """
    Create a path between two points using simple L-shaped paths.
    
    This creates a path that goes horizontally first, then vertically.
    """
    # Simple L-shaped path: horizontal first, then vertical
    current_x, current_y = x1, y1
    
    # Move horizontally
    while current_x != x2:
        if 0 <= current_x < len(tiles[0]) and 0 <= current_y < len(tiles):
            tiles[current_y][current_x] = VILLAGE_PATH_TILE
        current_x += 1 if x2 > current_x else -1
    
    # Move vertically
    while current_y != y2:
        if 0 <= current_x < len(tiles[0]) and 0 <= current_y < len(tiles):
            tiles[current_y][current_x] = VILLAGE_PATH_TILE
        current_y += 1 if y2 > current_y else -1
    
    # Mark destination
    if 0 <= current_x < len(tiles[0]) and 0 <= current_y < len(tiles):
        tiles[current_y][current_x] = VILLAGE_PATH_TILE

