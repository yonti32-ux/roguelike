# world/tiles.py

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class Tile:
    """Basic tile definition."""
    walkable: bool
    blocks_sight: bool
    color: Tuple[int, int, int]


# Base colors — warm stone dungeon palette
FLOOR_COLOR = (48, 44, 52)
WALL_COLOR = (78, 72, 68)

# Stair colors (just for now, we’ll swap to sprites later)
UP_STAIRS_COLOR = (110, 175, 210)     # cool blue
DOWN_STAIRS_COLOR = (210, 150, 85)    # warm amber

FLOOR_TILE = Tile(
    walkable=True,
    blocks_sight=False,
    color=FLOOR_COLOR,
)

WALL_TILE = Tile(
    walkable=False,
    blocks_sight=True,
    color=WALL_COLOR,
)

UP_STAIRS_TILE = Tile(
    walkable=True,
    blocks_sight=False,
    color=UP_STAIRS_COLOR,
)

DOWN_STAIRS_TILE = Tile(
    walkable=True,
    blocks_sight=False,
    color=DOWN_STAIRS_COLOR,
)
