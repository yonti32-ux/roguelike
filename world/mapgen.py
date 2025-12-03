# world/mapgen.py

import random
from typing import List, Tuple

from settings import WINDOW_WIDTH, WINDOW_HEIGHT, TILE_SIZE
from world.tiles import (
    Tile,
    FLOOR_TILE,
    WALL_TILE,
    UP_STAIRS_TILE,
    DOWN_STAIRS_TILE,
)


class RectRoom:
    """Axis-aligned rectangular room on the tile grid."""
    __slots__ = ("x1", "y1", "x2", "y2", "tag")

    def __init__(self, x: int, y: int, w: int, h: int, tag: str = "generic") -> None:
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h
        # High-level type for content placement:
        # "start", "lair", "treasure", "event", "generic"
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


def generate_floor(
    floor_index: int,
) -> Tuple[List[List[Tile]], int, int, int, int, List[RectRoom]]:
    """
    Generate a basic dungeon-style floor:
    - Random rectangular rooms
    - Connected by corridors

    Returns:
        tiles, up_stairs_tx, up_stairs_ty, down_stairs_tx, down_stairs_ty, rooms

    floor_index is currently unused for layout shape, but later we can use it
    to change difficulty / style per depth.
    """

    tiles_x = WINDOW_WIDTH // TILE_SIZE
    tiles_y = WINDOW_HEIGHT // TILE_SIZE

    tiles = _create_empty_map(tiles_x, tiles_y)

    rooms: List[RectRoom] = []
    max_rooms = 12
    room_min_size = 4
    room_max_size = 9

    for _ in range(max_rooms):
        w = random.randint(room_min_size, room_max_size)
        h = random.randint(room_min_size, room_max_size)

        x = random.randint(1, tiles_x - w - 2)
        y = random.randint(1, tiles_y - h - 2)

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
