"""
Village map generation.
"""

import random
import math
from typing import List, Tuple, Optional

from settings import TILE_SIZE
from ..game_map import GameMap
from ..tiles import WALL_TILE
from .tiles import (
    VILLAGE_PATH_TILE,
    VILLAGE_PLAZA_TILE,
    VILLAGE_GRASS_TILE,
    BUILDING_FLOOR_TILE,
    BUILDING_WALL_TILE,
    BUILDING_ENTRANCE_TILE,
    TREE_TILE,
    WELL_TILE,
    BENCH_TILE,
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
    
    # Calculate village size based on level (use display resolution for viewport-relative sizing)
    from engine.core.config import get_display_resolution
    res_w, res_h = get_display_resolution()
    base_tiles_x = res_w // TILE_SIZE
    base_tiles_y = res_h // TILE_SIZE
    
    # Village size scaling - made larger with more variety
    if level <= 3:
        # Small village - now larger
        scale = random.uniform(1.2, 1.6)
    elif level <= 7:
        # Medium village - significantly larger
        scale = random.uniform(1.6, 2.2)
    else:
        # Large village - very large with good variety
        scale = random.uniform(2.0, 2.8)
    
    map_width = int(base_tiles_x * scale)
    map_height = int(base_tiles_y * scale)
    
    # Ensure minimum size (increased from 30)
    map_width = max(40, map_width)
    map_height = max(40, map_height)
    
    # Create empty map (all walls initially)
    tiles = [[WALL_TILE for _ in range(map_width)] for _ in range(map_height)]
    
    # Place central plaza
    plaza_x, plaza_y, plaza_w, plaza_h = _place_plaza(map_width, map_height, level)
    _carve_area(tiles, plaza_x, plaza_y, plaza_w, plaza_h, VILLAGE_PLAZA_TILE)
    
    # Calculate plaza center coordinates (needed for building placement)
    plaza_center_x = plaza_x + plaza_w // 2
    plaza_center_y = plaza_y + plaza_h // 2
    
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
    
    # Path from entrance to plaza (plaza_center_x and plaza_center_y already calculated above)
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
    
    # Place exit points on all edges of the map (bigger exit areas)
    # Do this before decorative elements so trees don't block exits
    exit_tiles = _place_village_exits(tiles, map_width, map_height, plaza_center_x, plaza_center_y)
    
    # Add decorative elements: well, benches, trees
    _place_decorative_elements(
        tiles, map_width, map_height, buildings,
        plaza_x, plaza_y, plaza_w, plaza_h,
        plaza_center_x, plaza_center_y,
    )
    
    # Add some wandering villagers outside buildings
    _add_wandering_villagers(npcs, tiles, map_width, map_height, buildings, plaza_x, plaza_y, plaza_w, plaza_h)
    
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
    
    # Store exit tiles (list of (x, y) tuples where player can exit)
    village_map.village_exit_tiles = exit_tiles
    
    # Store buildings for building detection and room hints
    village_map.village_buildings = buildings
    
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
    # Plaza size based on level - made larger to match larger villages
    if level <= 3:
        # Small plaza (larger than before)
        min_size = 8
        max_size = 12
    elif level <= 7:
        # Medium plaza (significantly larger)
        min_size = 12
        max_size = 16
    else:
        # Large plaza (very large)
        min_size = 14
        max_size = 20
    
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
    Place trees and other decorative elements around the village.
    Also places well and benches in plaza. Avoids paths, buildings for trees.
    """
    # Place plaza decorations (well and benches) on plaza tiles only
    plaza_tiles = []
    for dy in range(plaza_h):
        for dx in range(plaza_w):
            tx = plaza_x + dx
            ty = plaza_y + dy
            if 0 <= tx < map_width and 0 <= ty < map_height and tiles[ty][tx] == VILLAGE_PLAZA_TILE:
                plaza_tiles.append((tx, ty))
    if plaza_tiles:
        # Place well - pick tile nearest to center but not exact center (path junction)
        def dist_to_center(pos):
            return (pos[0] - plaza_center_x) ** 2 + (pos[1] - plaza_center_y) ** 2
        # Prefer tiles 1-2 steps from center for well
        candidates = [p for p in plaza_tiles if 4 <= dist_to_center(p) <= 25]
        if candidates:
            well_pos = min(candidates, key=dist_to_center)
            tiles[well_pos[1]][well_pos[0]] = WELL_TILE
            plaza_tiles = [p for p in plaza_tiles if p != well_pos]
        # Place benches
        num_benches = min(random.randint(2, 4), len(plaza_tiles))
        for _ in range(num_benches):
            if plaza_tiles:
                bench_pos = random.choice(plaza_tiles)
                tiles[bench_pos[1]][bench_pos[0]] = BENCH_TILE
                plaza_tiles.remove(bench_pos)

    # Calculate safe areas (don't place trees here)
    safe_tiles = set()
    
    # Mark plaza as safe
    for dy in range(plaza_h):
        for dx in range(plaza_w):
            tx = plaza_x + dx
            ty = plaza_y + dy
            if 0 <= tx < map_width and 0 <= ty < map_height:
                safe_tiles.add((tx, ty))
    
    # Mark buildings and their immediate surroundings as safe (3 tiles around)
    for building in buildings:
        for dy in range(-3, building.height + 3):
            for dx in range(-3, building.width + 3):
                tx = building.x + dx
                ty = building.y + dy
                if 0 <= tx < map_width and 0 <= ty < map_height:
                    safe_tiles.add((tx, ty))
    
    # Mark paths as safe (check all tiles and mark path tiles + 1 tile buffer)
    for y in range(map_height):
        for x in range(map_width):
            if tiles[y][x] == VILLAGE_PATH_TILE:
                # Mark path tile and adjacent tiles
                for dy in range(-1, 2):
                    for dx in range(-1, 2):
                        tx = x + dx
                        ty = y + dy
                        if 0 <= tx < map_width and 0 <= ty < map_height:
                            safe_tiles.add((tx, ty))
    
    # Place trees in grass areas
    # Number of trees based on map size (density: ~2-3% of grass tiles)
    total_grass_tiles = map_width * map_height - len(safe_tiles)
    num_trees = max(5, int(total_grass_tiles * random.uniform(0.02, 0.03)))
    
    placed_trees = 0
    attempts = 0
    max_attempts = num_trees * 10  # Give up after many failed attempts
    
    while placed_trees < num_trees and attempts < max_attempts:
        attempts += 1
        x = random.randint(0, map_width - 1)
        y = random.randint(0, map_height - 1)
        
        # Check if this tile is safe and is grass
        if (x, y) in safe_tiles:
            continue
        if tiles[y][x] != VILLAGE_GRASS_TILE:
            continue
        
        # Avoid clustering - check if there's already a tree nearby (3 tile radius)
        too_close = False
        for dy in range(-3, 4):
            for dx in range(-3, 4):
                tx = x + dx
                ty = y + dy
                if 0 <= tx < map_width and 0 <= ty < map_height:
                    if tiles[ty][tx] == TREE_TILE:
                        too_close = True
                        break
            if too_close:
                break
        
        if too_close:
            continue
        
        # Place tree
        tiles[y][x] = TREE_TILE
        placed_trees += 1


def _place_village_exits(
    tiles: List[List],
    map_width: int,
    map_height: int,
    plaza_center_x: int,
    plaza_center_y: int,
) -> List[Tuple[int, int]]:
    """
    Place exit points on all edges of the village map.
    Each exit is a larger area (5 tiles wide) for easier access.
    
    Returns:
        List of (x, y) tile coordinates that are exit points
    """
    exit_tiles: List[Tuple[int, int]] = []
    exit_width = 5  # Make exits 5 tiles wide for easier access
    
    # Top edge exit (centered horizontally)
    top_exit_start = max(1, map_width // 2 - exit_width // 2)
    top_exit_end = min(map_width - 1, top_exit_start + exit_width)
    top_exit_center_x = (top_exit_start + top_exit_end) // 2
    for x in range(top_exit_start, top_exit_end):
        if 0 <= x < map_width and 0 < map_height:
            tiles[0][x] = VILLAGE_PATH_TILE
            exit_tiles.append((x, 0))
    # Create path from center of exit to plaza
    if 0 <= top_exit_center_x < map_width:
        _create_path(tiles, top_exit_center_x, 0, plaza_center_x, plaza_center_y)
    
    # Bottom edge exit (centered horizontally)
    bottom_exit_start = max(1, map_width // 2 - exit_width // 2)
    bottom_exit_end = min(map_width - 1, bottom_exit_start + exit_width)
    bottom_exit_center_x = (bottom_exit_start + bottom_exit_end) // 2
    for x in range(bottom_exit_start, bottom_exit_end):
        if 0 <= x < map_width and map_height > 0:
            tiles[map_height - 1][x] = VILLAGE_PATH_TILE
            exit_tiles.append((x, map_height - 1))
    # Create path from center of exit to plaza
    if 0 <= bottom_exit_center_x < map_width:
        _create_path(tiles, bottom_exit_center_x, map_height - 1, plaza_center_x, plaza_center_y)
    
    # Left edge exit (centered vertically)
    left_exit_start = max(1, map_height // 2 - exit_width // 2)
    left_exit_end = min(map_height - 1, left_exit_start + exit_width)
    left_exit_center_y = (left_exit_start + left_exit_end) // 2
    for y in range(left_exit_start, left_exit_end):
        if 0 < map_width and 0 <= y < map_height:
            tiles[y][0] = VILLAGE_PATH_TILE
            exit_tiles.append((0, y))
    # Create path from center of exit to plaza
    if 0 <= left_exit_center_y < map_height:
        _create_path(tiles, 0, left_exit_center_y, plaza_center_x, plaza_center_y)
    
    # Right edge exit (centered vertically)
    right_exit_start = max(1, map_height // 2 - exit_width // 2)
    right_exit_end = min(map_height - 1, right_exit_start + exit_width)
    right_exit_center_y = (right_exit_start + right_exit_end) // 2
    for y in range(right_exit_start, right_exit_end):
        if map_width > 0 and 0 <= y < map_height:
            tiles[y][map_width - 1] = VILLAGE_PATH_TILE
            exit_tiles.append((map_width - 1, y))
    # Create path from center of exit to plaza
    if 0 <= right_exit_center_y < map_height:
        _create_path(tiles, map_width - 1, right_exit_center_y, plaza_center_x, plaza_center_y)
    
    return exit_tiles


def _add_wandering_villagers(
    npcs: List[VillageNPC],
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
    Add some wandering villagers outside buildings for atmosphere.
    They'll be placed in the plaza and on paths.
    """
    from .npcs import create_wandering_villager
    
    # Number of wandering villagers: 4-7 (roam the streets)
    num_villagers = random.randint(4, 7)
    
    valid_positions = []
    
    # Find valid positions (plaza and paths, but not too close to buildings)
    for y in range(map_height):
        for x in range(map_width):
            tile = tiles[y][x]
            if tile not in (VILLAGE_PATH_TILE, VILLAGE_PLAZA_TILE):
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
    
    # Place villagers
    placed = 0
    for _ in range(min(num_villagers, len(valid_positions))):
        if not valid_positions:
            break
        
        x, y = random.choice(valid_positions)
        valid_positions.remove((x, y))
        
        # Convert to world coordinates
        world_x = x * TILE_SIZE + (TILE_SIZE - 24) / 2
        world_y = y * TILE_SIZE + (TILE_SIZE - 24) / 2
        
        # Create wandering villager with generated name
        villager = create_wandering_villager(
            world_x,
            world_y,
            npc_id=f"wandering_villager_{placed}",
        )
        if villager:
            npcs.append(villager)
            placed += 1

