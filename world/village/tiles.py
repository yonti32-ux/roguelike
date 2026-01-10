"""
Village-specific tile types.
"""

from dataclasses import dataclass
from typing import Tuple

from ..tiles import Tile


# Village tile colors (peaceful, warm tones)
VILLAGE_PATH_COLOR = (120, 100, 80)      # Brownish path
VILLAGE_PLAZA_COLOR = (100, 120, 100)    # Greenish plaza
VILLAGE_GRASS_COLOR = (60, 100, 60)      # Dark green grass
BUILDING_FLOOR_COLOR = (80, 70, 60)      # Wooden floor
BUILDING_WALL_COLOR = (100, 90, 80)      # Wooden wall


VILLAGE_PATH_TILE = Tile(
    walkable=True,
    blocks_sight=False,
    color=VILLAGE_PATH_COLOR,
)

VILLAGE_PLAZA_TILE = Tile(
    walkable=True,
    blocks_sight=False,
    color=VILLAGE_PLAZA_COLOR,
)

VILLAGE_GRASS_TILE = Tile(
    walkable=True,
    blocks_sight=False,
    color=VILLAGE_GRASS_COLOR,
)

BUILDING_FLOOR_TILE = Tile(
    walkable=True,
    blocks_sight=False,
    color=BUILDING_FLOOR_COLOR,
)

BUILDING_WALL_TILE = Tile(
    walkable=False,
    blocks_sight=True,
    color=BUILDING_WALL_COLOR,
)

# Building entrance (door) - walkable but visually distinct
BUILDING_ENTRANCE_COLOR = (90, 80, 70)  # Slightly darker than wall
BUILDING_ENTRANCE_TILE = Tile(
    walkable=True,
    blocks_sight=False,
    color=BUILDING_ENTRANCE_COLOR,
)

# Tree - decorative, blocks movement and sight
TREE_COLOR = (40, 80, 40)  # Dark green for trees
TREE_TILE = Tile(
    walkable=False,
    blocks_sight=True,
    color=TREE_COLOR,
)

