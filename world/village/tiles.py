"""
Village-specific tile types.
"""

from dataclasses import dataclass
from typing import Tuple

from ..tiles import Tile


# Village tile colors (peaceful, warm tones - richer palette)
VILLAGE_PATH_COLOR = (140, 110, 85)      # Warm dirt path
VILLAGE_PLAZA_COLOR = (95, 130, 95)      # Lively green plaza
VILLAGE_GRASS_COLOR = (55, 110, 55)      # Richer grass green
BUILDING_FLOOR_COLOR = (95, 82, 68)      # Warm wooden floor
BUILDING_WALL_COLOR = (118, 98, 82)      # Warmer wooden wall


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
BUILDING_ENTRANCE_COLOR = (75, 65, 55)  # Darker wood door
BUILDING_ENTRANCE_TILE = Tile(
    walkable=True,
    blocks_sight=False,
    color=BUILDING_ENTRANCE_COLOR,
)

# Tree - decorative, blocks movement and sight
TREE_COLOR = (35, 85, 45)  # Deeper green for trees
TREE_TILE = Tile(
    walkable=False,
    blocks_sight=True,
    color=TREE_COLOR,
)

# Well - decorative plaza center, blocks movement
WELL_COLOR = (90, 95, 100)  # Stone well
WELL_TILE = Tile(
    walkable=False,
    blocks_sight=False,
    color=WELL_COLOR,
)

# Bench - decorative, blocks movement
BENCH_COLOR = (100, 75, 55)  # Wooden bench
BENCH_TILE = Tile(
    walkable=False,
    blocks_sight=False,
    color=BENCH_COLOR,
)

