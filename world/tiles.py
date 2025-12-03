# world/tiles.py

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class Tile:
    """Basic tile definition."""
    walkable: bool
    blocks_sight: bool
    color: Tuple[int, int, int]


# Base colors
FLOOR_COLOR = (40, 40, 60)
WALL_COLOR = (90, 90, 120)

# Stair colors (just for now, we’ll swap to sprites later)
UP_STAIRS_COLOR = (120, 200, 255)     # bluish
DOWN_STAIRS_COLOR = (255, 200, 120)   # orangish

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
