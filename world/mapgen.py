import random
import math
from typing import List, Tuple, Dict, Any

from settings import TILE_SIZE
from world.tiles import (
    Tile,
    FLOOR_TILE,
    WALL_TILE,
    UP_STAIRS_TILE,
    DOWN_STAIRS_TILE,
)
from world.generation.config import load_generation_config


class RectRoom:
    """Axis-aligned rectangular room on the tile grid."""
    __slots__ = ("x1", "y1", "x2", "y2", "tag")

    def __init__(self, x: int, y: int, w: int, h: int, tag: str = "generic") -> None:
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h
        # High-level type for content placement:
        # "start", "lair", "treasure", "event", "generic", "shop"
        self.tag = tag

    def center(self) -> tuple[int, int]:
        center_x = (self.x1 + self.x2) // 2
        center_y = (self.y1 + self.y2) // 2
        return center_x, center_y

    def intersects(self, other: "RectRoom") -> bool:
        return (
            self.x1 <= other.x2
            and self.x2 >= other.x1
            and self.y1 <= other.y2
            and self.y2 >= other.y1
        )


def _create_empty_map(width: int, height: int) -> List[List[Tile]]:
    """Start with solid walls everywhere."""
    return [[WALL_TILE for _ in range(width)] for _ in range(height)]


def _carve_room(tiles: List[List[Tile]], room: RectRoom) -> None:
    for y in range(room.y1 + 1, room.y2):
        for x in range(room.x1 + 1, room.x2):
            tiles[y][x] = FLOOR_TILE


def _carve_h_tunnel(tiles: List[List[Tile]], x1: int, x2: int, y: int) -> None:
    for x in range(min(x1, x2), max(x1, x2) + 1):
        tiles[y][x] = FLOOR_TILE


def _carve_v_tunnel(tiles: List[List[Tile]], y1: int, y2: int, x: int) -> None:
    for y in range(min(y1, y2), max(y1, y2) + 1):
        tiles[y][x] = FLOOR_TILE


# world/mapgen.py

def generate_floor(
    floor_index: int,
) -> Tuple[List[List[Tile]], int, int, int, int, List[RectRoom]]:
    """
    Generate a basic dungeon-style floor:
    - Random rectangular rooms
    - Connected by corridors

    Returns:
        tiles, up_stairs_tx, up_stairs_ty, down_stairs_tx, down_stairs_ty, rooms

    Floor size and room count now depend on depth:
    - Early floors: mostly around 1× screen size.
    - Mid floors: mix of 1×, 1.5×, and 2×.
    - Deep floors: mostly 1.5×–2×.
    """

    # --- Decide overall map dimensions in tiles, based on depth ---
    gen_config = load_generation_config()
    from engine.core.config import get_display_resolution
    res_w, res_h = get_display_resolution()
    base_tiles_x = res_w // TILE_SIZE
    base_tiles_y = res_h // TILE_SIZE
    base_area = base_tiles_x * base_tiles_y

    # Progressive scaling: use config-based scaling rules
    size_scaling = gen_config.floor.size_scaling
    scale_config = _get_scale_config_for_floor(floor_index, size_scaling)
    
    if scale_config:
        scales = scale_config["scales"]
        weights = scale_config["weights"]
        scale = random.choices(scales, weights=weights, k=1)[0]
    else:
        # Fallback: use default scale
        scale = 1.0

    tiles_x = int(base_tiles_x * scale)
    tiles_y = int(base_tiles_y * scale)

    # Safety clamp: use config-based min/max
    min_scale = gen_config.floor.min_scale
    max_scale = gen_config.floor.max_scale
    tiles_x = max(int(base_tiles_x * min_scale), min(tiles_x, int(base_tiles_x * max_scale)))
    tiles_y = max(int(base_tiles_y * min_scale), min(tiles_y, int(base_tiles_y * max_scale)))

    tiles = _create_empty_map(tiles_x, tiles_y)

    # --- Decide how many rooms to try for, based on map area ---
    room_count_config = gen_config.floor.room_count
    floor_area = tiles_x * tiles_y
    area_ratio = floor_area / base_area if base_area > 0 else 1.0
    
    # Use configured density formula
    if room_count_config.get("density_formula") == "sqrt":
        density_factor = math.sqrt(area_ratio)
    else:
        # Default to linear
        density_factor = area_ratio

    base_rooms = room_count_config["base"]
    max_rooms = int(round(base_rooms * density_factor))
    # Clamp so tiny floors still have a few rooms and huge floors don't explode
    min_rooms = room_count_config["min"]
    max_room_limit = room_count_config["max"]
    max_rooms = max(min_rooms, min(max_rooms, max_room_limit))

    room_size_config = gen_config.floor.room_size
    room_min_size = room_size_config["min"]
    room_max_size = room_size_config["max"]
    wall_border = gen_config.floor.wall_border

    rooms: List[RectRoom] = []

    for _ in range(max_rooms):
        w = random.randint(room_min_size, room_max_size)
        h = random.randint(room_min_size, room_max_size)

        # Keep configured wall border around the outside
        border_size = wall_border + 1  # +1 for room boundary
        if w + border_size >= tiles_x or h + border_size >= tiles_y:
            continue

        x = random.randint(1, tiles_x - w - border_size)
        y = random.randint(1, tiles_y - h - border_size)

        new_room = RectRoom(x, y, w, h)

        if any(new_room.intersects(other) for other in rooms):
            continue  # discard this room and try another

        # Carve the room
        _carve_room(tiles, new_room)

        if rooms:
            # Connect to previous room with a corridor
            prev_center_x, prev_center_y = rooms[-1].center()
            new_center_x, new_center_y = new_room.center()

            if random.random() < 0.5:
                # Horizontal then vertical
                _carve_h_tunnel(tiles, prev_center_x, new_center_x, prev_center_y)
                _carve_v_tunnel(tiles, prev_center_y, new_center_y, new_center_x)
            else:
                # Vertical then horizontal
                _carve_v_tunnel(tiles, prev_center_y, new_center_y, prev_center_x)
                _carve_h_tunnel(tiles, prev_center_x, new_center_x, new_center_y)

        rooms.append(new_room)

    # Tag rooms with high-level roles so content can key off them.
    if rooms:
        # 1) Start room = first carved room
        start_room = rooms[0]
        start_room.tag = "start"

        # 2) Treasure room = farthest from start center
        if len(rooms) > 1:
            sx, sy = start_room.center()

            def dist2(r: RectRoom) -> int:
                cx, cy = r.center()
                dx = cx - sx
                dy = cy - sy
                return dx * dx + dy * dy

            # Only consider non-start rooms
            non_start = rooms[1:]
            treasure_room = max(non_start, key=dist2)
            treasure_room.tag = "treasure"

            # 3) Lair room = another non-start, non-treasure room
            lair_candidates = [r for r in non_start if r is not treasure_room]
            if lair_candidates:
                lair_room = random.choice(lair_candidates)
                lair_room.tag = "lair"

            # 4) Event room = some remaining generic room if any
            event_candidates = [r for r in rooms if r.tag == "generic"]
            if event_candidates:
                event_room = random.choice(event_candidates)
                event_room.tag = "event"

            # Apply room tags using config
            gen_config = load_generation_config()
            room_tags_config = gen_config.room_tags
            
            # Track how many of each tag type we've placed this floor
            tags_placed: Dict[str, int] = {}
            
            # Shop room
            shop_config = room_tags_config.shop
            shop_candidates = [r for r in rooms if r.tag == "generic"]
            if (shop_candidates and 
                tags_placed.get("shop", 0) < shop_config.get("max_per_floor", 1) and
                random.random() < shop_config.get("chance", 0.7)):
                shop_room = random.choice(shop_candidates)
                shop_room.tag = "shop"
                tags_placed["shop"] = tags_placed.get("shop", 0) + 1

            # Graveyard room
            graveyard_config = room_tags_config.graveyard
            graveyard_candidates = [r for r in rooms if r.tag == "generic"]
            if (graveyard_candidates and 
                floor_index >= graveyard_config.get("min_floor", 2) and
                tags_placed.get("graveyard", 0) < graveyard_config.get("max_per_floor", 1) and
                random.random() < graveyard_config.get("chance", 0.8)):
                graveyard_room = random.choice(graveyard_candidates)
                graveyard_room.tag = "graveyard"
                tags_placed["graveyard"] = tags_placed.get("graveyard", 0) + 1

            # Sanctum room
            sanctum_config = room_tags_config.sanctum
            sanctum_candidates = [r for r in rooms if r.tag == "generic"]
            if (sanctum_candidates and 
                floor_index >= sanctum_config.get("min_floor", 3) and
                tags_placed.get("sanctum", 0) < sanctum_config.get("max_per_floor", 1) and
                random.random() < sanctum_config.get("chance", 0.5)):
                sanctum_room = random.choice(sanctum_candidates)
                sanctum_room.tag = "sanctum"
                tags_placed["sanctum"] = tags_placed.get("sanctum", 0) + 1

            # Armory room
            armory_config = room_tags_config.armory
            armory_candidates = [r for r in rooms if r.tag == "generic"]
            if (armory_candidates and 
                floor_index >= armory_config.get("min_floor", 2) and
                tags_placed.get("armory", 0) < armory_config.get("max_per_floor", 1) and
                random.random() < armory_config.get("chance", 0.5)):
                armory_room = random.choice(armory_candidates)
                armory_room.tag = "armory"
                tags_placed["armory"] = tags_placed.get("armory", 0) + 1

            # Library room
            library_config = room_tags_config.library
            library_candidates = [r for r in rooms if r.tag == "generic"]
            if (library_candidates and 
                floor_index >= library_config.get("min_floor", 2) and
                tags_placed.get("library", 0) < library_config.get("max_per_floor", 1) and
                random.random() < library_config.get("chance", 0.5)):
                library_room = random.choice(library_candidates)
                library_room.tag = "library"
                tags_placed["library"] = tags_placed.get("library", 0) + 1

            # Arena room
            arena_config = room_tags_config.arena
            arena_candidates = [r for r in rooms if r.tag == "generic"]
            if (arena_candidates and 
                floor_index >= arena_config.get("min_floor", 3) and
                tags_placed.get("arena", 0) < arena_config.get("max_per_floor", 1) and
                random.random() < arena_config.get("chance", 0.4)):
                arena_room = random.choice(arena_candidates)
                arena_room.tag = "arena"
                tags_placed["arena"] = tags_placed.get("arena", 0) + 1

    # Decide stair tiles (still using first/last room centers)
    if rooms:
        up_tx, up_ty = rooms[0].center()
        down_tx, down_ty = rooms[-1].center()
    else:
        # Fallback: center of the map
        up_tx = down_tx = tiles_x // 2
        up_ty = down_ty = tiles_y // 2

    # Place stair tiles (walkable)
    tiles[up_ty][up_tx] = UP_STAIRS_TILE
    tiles[down_ty][down_tx] = DOWN_STAIRS_TILE

    return tiles, up_tx, up_ty, down_tx, down_ty, rooms


def _get_scale_config_for_floor(floor_index: int, size_scaling: Dict[str, Dict[str, Any]]) -> Dict[str, Any] | None:
    """
    Get scale configuration for a given floor index.
    
    Args:
        floor_index: Floor number (1-based)
        size_scaling: Size scaling configuration dictionary
        
    Returns:
        Scale config dict with 'scales' and 'weights', or None if not found
    """
    # Check exact floor match first
    floor_key = str(floor_index)
    if floor_key in size_scaling:
        return size_scaling[floor_key]
    
    # Check range matches (e.g., "3-4", "5-6", "9+")
    for key, config in size_scaling.items():
        if "-" in key:
            # Range like "3-4"
            parts = key.split("-")
            if len(parts) == 2:
                try:
                    min_floor = int(parts[0])
                    max_floor = int(parts[1])
                    if min_floor <= floor_index <= max_floor:
                        return config
                except ValueError:
                    continue
        elif key.endswith("+"):
            # Range like "9+"
            try:
                min_floor = int(key[:-1])
                if floor_index >= min_floor:
                    return config
            except ValueError:
                continue
    
    return None
