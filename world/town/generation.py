"""
Town map generation.

Towns are larger and more complex than villages, with more buildings,
districts, and urban features.
"""

import random
import math
from typing import List, Tuple, Optional

from settings import WINDOW_WIDTH, WINDOW_HEIGHT, TILE_SIZE
from ..game_map import GameMap
from ..tiles import WALL_TILE
from .tiles import (
    TOWN_COBBLESTONE_TILE,
    TOWN_PLAZA_TILE,
    TOWN_GRASS_TILE,
    TOWN_MARKET_TILE,
    STONE_FLOOR_TILE,
    STONE_WALL_TILE,
    WOODEN_FLOOR_TILE,
    WOODEN_WALL_TILE,
    BUILDING_ENTRANCE_TILE,
    FOUNTAIN_TILE,
    MARKET_STALL_TILE,
    BENCH_TILE,
)
from .buildings import Building, place_buildings
from .npcs import TownNPC, create_npc_for_building


def generate_town(
    level: int,
    town_name: str,
    seed: Optional[int] = None,
) -> GameMap:
    """
    Generate a complete town map.
    
    Towns are larger than villages and have more buildings, districts, and features.
    
    Args:
        level: Town level (affects size and building count)
        town_name: Name of the town (for potential future use)
        seed: Random seed for deterministic generation
        
    Returns:
        GameMap instance with town layout
    """
    if seed is not None:
        random.seed(seed)
    
    # Calculate town size based on level
    # Towns are significantly larger than villages
    base_tiles_x = WINDOW_WIDTH // TILE_SIZE
    base_tiles_y = WINDOW_HEIGHT // TILE_SIZE
    
    # Town size scaling - much larger than villages
    if level <= 3:
        # Small town
        scale = random.uniform(2.0, 2.8)
    elif level <= 7:
        # Medium town
        scale = random.uniform(2.8, 3.5)
    else:
        # Large town
        scale = random.uniform(3.5, 4.5)
    
    map_width = int(base_tiles_x * scale)
    map_height = int(base_tiles_y * scale)
    
    # Ensure minimum size (larger than villages)
    map_width = max(60, map_width)
    map_height = max(60, map_height)
    
    # Create empty map (all walls initially)
    tiles = [[WALL_TILE for _ in range(map_width)] for _ in range(map_height)]
    
    # Place central plaza (larger than villages)
    plaza_x, plaza_y, plaza_w, plaza_h = _place_plaza(map_width, map_height, level)
    _carve_area(tiles, plaza_x, plaza_y, plaza_w, plaza_h, TOWN_PLAZA_TILE)
    
    # Add fountain in plaza center
    plaza_center_x = plaza_x + plaza_w // 2
    plaza_center_y = plaza_y + plaza_h // 2
    if 0 <= plaza_center_x < map_width and 0 <= plaza_center_y < map_height:
        tiles[plaza_center_y][plaza_center_x] = FOUNTAIN_TILE
    
    # Place buildings
    buildings = place_buildings(map_width, map_height, level, seed)
    
    # Carve buildings into map
    npcs: List[TownNPC] = []
    for i, building in enumerate(buildings):
        building_id = f"building_{i}"
        
        # Choose floor and wall tiles based on building material
        if building.material == "stone":
            floor_tile = STONE_FLOOR_TILE
            wall_tile = STONE_WALL_TILE
        else:
            floor_tile = WOODEN_FLOOR_TILE
            wall_tile = WOODEN_WALL_TILE
        
        # Carve building interior (floor tiles)
        _carve_area(
            tiles,
            building.x + 1,  # Leave 1 tile border for walls
            building.y + 1,
            building.width - 2,
            building.height - 2,
            floor_tile,
        )
        
        # Add building walls around perimeter
        _add_building_walls(tiles, building, wall_tile)
        
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
        
        # Special handling for market buildings - add market stalls
        if building.building_type == "market":
            _add_market_stalls(tiles, building)
    
    # Create paths from entrance to plaza, and plaza to buildings
    entrance_x = map_width // 2
    entrance_y = map_height - 2
    
    # Ensure entrance is walkable (cobblestone tile)
    if 0 <= entrance_x < map_width and 0 <= entrance_y < map_height:
        tiles[entrance_y][entrance_x] = TOWN_COBBLESTONE_TILE
    
    # Path from entrance to plaza (using cobblestone)
    _create_path(tiles, entrance_x, entrance_y, plaza_center_x, plaza_center_y, TOWN_COBBLESTONE_TILE)
    
    # Paths from plaza to each building entrance
    for building in buildings:
        if building.entrance_x is not None and building.entrance_y is not None:
            # Path to entrance (one tile outside the building)
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
                tiles[entrance_outside_y][entrance_outside_x] = TOWN_COBBLESTONE_TILE
                _create_path(tiles, plaza_center_x, plaza_center_y, entrance_outside_x, entrance_outside_y, TOWN_COBBLESTONE_TILE)
    
    # Fill remaining space with grass (less common in towns)
    for y in range(map_height):
        for x in range(map_width):
            if tiles[y][x] == WALL_TILE:
                # Towns have less grass - more cobblestone
                if random.random() < 0.3:  # 30% grass, 70% cobblestone
                    tiles[y][x] = TOWN_GRASS_TILE
                else:
                    tiles[y][x] = TOWN_COBBLESTONE_TILE
    
    # Place exit points on all edges of the map
    exit_tiles = _place_town_exits(tiles, map_width, map_height, plaza_center_x, plaza_center_y)
    
    # Add decorative elements: benches, fountains, etc.
    _place_decorative_elements(
        tiles, map_width, map_height, buildings,
        plaza_x, plaza_y, plaza_w, plaza_h,
        plaza_center_x, plaza_center_y,
    )
    
    # Add some wandering citizens outside buildings
    _add_wandering_citizens(npcs, tiles, map_width, map_height, buildings, plaza_x, plaza_y, plaza_w, plaza_h)
    
    # Create GameMap
    town_map = GameMap(
        tiles=tiles,
        up_stairs=None,  # Towns don't have stairs
        down_stairs=None,
        entities=npcs,
        rooms=[],  # Towns don't use room system
    )
    
    # Store entrance position for player placement
    town_map.town_entrance = (entrance_x, entrance_y)
    
    # Store exit tiles (list of (x, y) tuples where player can exit)
    town_map.town_exit_tiles = exit_tiles
    
    # Store buildings for building detection
    town_map.town_buildings = buildings
    
    return town_map


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
    # Plaza size based on level - larger than villages
    if level <= 3:
        min_size = 12
        max_size = 18
    elif level <= 7:
        min_size = 16
        max_size = 24
    else:
        min_size = 20
        max_size = 30
    
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
    wall_tile,
) -> None:
    """Add walls around a building perimeter."""
    # Top and bottom walls
    for x in range(building.x, building.x2):
        if 0 <= x < len(tiles[0]):
            # Top wall
            if 0 <= building.y < len(tiles):
                tiles[building.y][x] = wall_tile
            # Bottom wall
            if 0 <= building.y2 - 1 < len(tiles):
                tiles[building.y2 - 1][x] = wall_tile
    
    # Left and right walls
    for y in range(building.y, building.y2):
        if 0 <= y < len(tiles):
            # Left wall
            if 0 <= building.x < len(tiles[0]):
                tiles[y][building.x] = wall_tile
            # Right wall
            if 0 <= building.x2 - 1 < len(tiles[0]):
                tiles[y][building.x2 - 1] = wall_tile


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
    path_tile,
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
            tiles[current_y][current_x] = path_tile
        current_x += 1 if x2 > current_x else -1
    
    # Move vertically
    while current_y != y2:
        if 0 <= current_x < len(tiles[0]) and 0 <= current_y < len(tiles):
            tiles[current_y][current_x] = path_tile
        current_y += 1 if y2 > current_y else -1
    
    # Mark destination
    if 0 <= current_x < len(tiles[0]) and 0 <= current_y < len(tiles):
        tiles[current_y][current_x] = path_tile


def _add_market_stalls(
    tiles: List[List],
    building: Building,
) -> None:
    """Add market stalls inside a market building."""
    # Place 3-5 market stalls randomly inside the market
    num_stalls = random.randint(3, 5)
    
    for _ in range(num_stalls):
        # Random position inside building (avoid walls)
        stall_x = random.randint(building.x + 2, building.x2 - 2)
        stall_y = random.randint(building.y + 2, building.y2 - 2)
        
        if 0 <= stall_x < len(tiles[0]) and 0 <= stall_y < len(tiles):
            # Only place if it's a floor tile (not wall or entrance)
            if tiles[stall_y][stall_x].walkable:
                tiles[stall_y][stall_x] = MARKET_STALL_TILE


def _place_decorative_elements(
    tiles: List[List],
    map_width: int,
    map_height: int,
    buildings: List[Building],
    plaza_x: int,
    plaza_y: int,
    plaza_w: int,
    plaza_h: int,
    plaza_center_x: int,
    plaza_center_y: int,
) -> None:
    """
    Place decorative elements around the town: benches in plaza, fountains, etc.
    Avoids paths, buildings for other decorations.
    """
    # Place benches in plaza (only on plaza tiles, not on fountain)
    plaza_tiles = []
    for dy in range(plaza_h):
        for dx in range(plaza_w):
            tx = plaza_x + dx
            ty = plaza_y + dy
            if 0 <= tx < map_width and 0 <= ty < map_height and tiles[ty][tx] == TOWN_PLAZA_TILE:
                plaza_tiles.append((tx, ty))
    if plaza_tiles:
        num_benches = min(random.randint(4, 8), len(plaza_tiles))
        for _ in range(num_benches):
            if plaza_tiles:
                bench_pos = random.choice(plaza_tiles)
                tiles[bench_pos[1]][bench_pos[0]] = BENCH_TILE
                plaza_tiles.remove(bench_pos)

    # Calculate safe areas (don't place decorations here)
    safe_tiles = set()
    
    # Mark plaza as safe
    for dy in range(plaza_h):
        for dx in range(plaza_w):
            tx = plaza_x + dx
            ty = plaza_y + dy
            if 0 <= tx < map_width and 0 <= ty < map_height:
                safe_tiles.add((tx, ty))
    
    # Mark buildings and their immediate surroundings as safe
    for building in buildings:
        for dy in range(-3, building.height + 3):
            for dx in range(-3, building.width + 3):
                tx = building.x + dx
                ty = building.y + dy
                if 0 <= tx < map_width and 0 <= ty < map_height:
                    safe_tiles.add((tx, ty))
    
    # Mark paths as safe
    for y in range(map_height):
        for x in range(map_width):
            if tiles[y][x] in (TOWN_COBBLESTONE_TILE, TOWN_PLAZA_TILE):
                # Mark path tile and adjacent tiles
                for dy in range(-1, 2):
                    for dx in range(-1, 2):
                        tx = x + dx
                        ty = y + dy
                        if 0 <= tx < map_width and 0 <= ty < map_height:
                            safe_tiles.add((tx, ty))
    
    # Place additional fountains (1-2 more besides plaza center)
    num_fountains = random.randint(1, 2)
    placed_fountains = 0
    attempts = 0
    max_attempts = 100
    
    while placed_fountains < num_fountains and attempts < max_attempts:
        attempts += 1
        x = random.randint(0, map_width - 1)
        y = random.randint(0, map_height - 1)
        
        # Check if this tile is safe and is cobblestone or plaza
        if (x, y) in safe_tiles:
            continue
        if tiles[y][x] not in (TOWN_COBBLESTONE_TILE, TOWN_PLAZA_TILE):
            continue
        
        # Avoid clustering - check if there's already a fountain nearby (5 tile radius)
        too_close = False
        for dy in range(-5, 6):
            for dx in range(-5, 6):
                tx = x + dx
                ty = y + dy
                if 0 <= tx < map_width and 0 <= ty < map_height:
                    if tiles[ty][tx] == FOUNTAIN_TILE:
                        too_close = True
                        break
            if too_close:
                break
        
        if too_close:
            continue
        
        # Place fountain
        tiles[y][x] = FOUNTAIN_TILE
        placed_fountains += 1


def _place_town_exits(
    tiles: List[List],
    map_width: int,
    map_height: int,
    plaza_center_x: int,
    plaza_center_y: int,
) -> List[Tuple[int, int]]:
    """
    Place exit points on all edges of the town map.
    Each exit is a larger area (7 tiles wide) for easier access.
    
    Returns:
        List of (x, y) tile coordinates that are exit points
    """
    exit_tiles: List[Tuple[int, int]] = []
    exit_width = 7  # Make exits 7 tiles wide for easier access
    
    # Top edge exit (centered horizontally)
    top_exit_start = max(1, map_width // 2 - exit_width // 2)
    top_exit_end = min(map_width - 1, top_exit_start + exit_width)
    top_exit_center_x = (top_exit_start + top_exit_end) // 2
    for x in range(top_exit_start, top_exit_end):
        if 0 <= x < map_width and 0 < map_height:
            tiles[0][x] = TOWN_COBBLESTONE_TILE
            exit_tiles.append((x, 0))
    if 0 <= top_exit_center_x < map_width:
        _create_path(tiles, top_exit_center_x, 0, plaza_center_x, plaza_center_y, TOWN_COBBLESTONE_TILE)
    
    # Bottom edge exit (centered horizontally)
    bottom_exit_start = max(1, map_width // 2 - exit_width // 2)
    bottom_exit_end = min(map_width - 1, bottom_exit_start + exit_width)
    bottom_exit_center_x = (bottom_exit_start + bottom_exit_end) // 2
    for x in range(bottom_exit_start, bottom_exit_end):
        if 0 <= x < map_width and map_height > 0:
            tiles[map_height - 1][x] = TOWN_COBBLESTONE_TILE
            exit_tiles.append((x, map_height - 1))
    if 0 <= bottom_exit_center_x < map_width:
        _create_path(tiles, bottom_exit_center_x, map_height - 1, plaza_center_x, plaza_center_y, TOWN_COBBLESTONE_TILE)
    
    # Left edge exit (centered vertically)
    left_exit_start = max(1, map_height // 2 - exit_width // 2)
    left_exit_end = min(map_height - 1, left_exit_start + exit_width)
    left_exit_center_y = (left_exit_start + left_exit_end) // 2
    for y in range(left_exit_start, left_exit_end):
        if 0 < map_width and 0 <= y < map_height:
            tiles[y][0] = TOWN_COBBLESTONE_TILE
            exit_tiles.append((0, y))
    if 0 <= left_exit_center_y < map_height:
        _create_path(tiles, 0, left_exit_center_y, plaza_center_x, plaza_center_y, TOWN_COBBLESTONE_TILE)
    
    # Right edge exit (centered vertically)
    right_exit_start = max(1, map_height // 2 - exit_width // 2)
    right_exit_end = min(map_height - 1, right_exit_start + exit_width)
    right_exit_center_y = (right_exit_start + right_exit_end) // 2
    for y in range(right_exit_start, right_exit_end):
        if map_width > 0 and 0 <= y < map_height:
            tiles[y][map_width - 1] = TOWN_COBBLESTONE_TILE
            exit_tiles.append((map_width - 1, y))
    if 0 <= right_exit_center_y < map_height:
        _create_path(tiles, map_width - 1, right_exit_center_y, plaza_center_x, plaza_center_y, TOWN_COBBLESTONE_TILE)
    
    return exit_tiles


def _add_wandering_citizens(
    npcs: List[TownNPC],
    tiles: List[List],
    map_width: int,
    map_height: int,
    buildings: List[Building],
    plaza_x: int,
    plaza_y: int,
    plaza_w: int,
    plaza_h: int,
) -> None:
    """
    Add some wandering citizens outside buildings for atmosphere.
    They'll be placed in the plaza and on paths.
    """
    from .npcs import create_wandering_citizen
    
    # Number of wandering citizens: 10-16 (towns are busy - people walk the streets)
    num_citizens = random.randint(10, 16)
    
    valid_positions = []
    
    # Find valid positions (plaza and paths, but not too close to buildings)
    for y in range(map_height):
        for x in range(map_width):
            tile = tiles[y][x]
            if tile not in (TOWN_COBBLESTONE_TILE, TOWN_PLAZA_TILE):
                continue
            
            # Check if too close to any building entrance (at least 2 tiles away)
            too_close = False
            for building in buildings:
                if building.entrance_x is not None and building.entrance_y is not None:
                    dist = abs(x - building.entrance_x) + abs(y - building.entrance_y)
                    if dist < 2:
                        too_close = True
                        break
            
            if not too_close:
                valid_positions.append((x, y))
    
    # Place citizens
    placed = 0
    for _ in range(min(num_citizens, len(valid_positions))):
        if not valid_positions:
            break
        
        x, y = random.choice(valid_positions)
        valid_positions.remove((x, y))
        
        # Convert to world coordinates
        world_x = x * TILE_SIZE + (TILE_SIZE - 24) / 2
        world_y = y * TILE_SIZE + (TILE_SIZE - 24) / 2
        
        # Create wandering citizen with generated name
        citizen = create_wandering_citizen(
            world_x,
            world_y,
            npc_id=f"wandering_citizen_{placed}",
        )
        if citizen:
            npcs.append(citizen)
            placed += 1
