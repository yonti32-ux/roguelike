"""
Town-specific tile types.

Towns use more sophisticated tiles than villages: cobblestone streets,
market areas, stone buildings, etc.
"""

from dataclasses import dataclass
from typing import Tuple

from ..tiles import Tile


# Town tile colors (urban, stone-based - clearer distinction)
TOWN_COBBLESTONE_COLOR = (105, 105, 110)      # Cool gray cobblestone
TOWN_PLAZA_COLOR = (85, 95, 115)              # Stone plaza with blue tint
TOWN_GRASS_COLOR = (48, 88, 52)               # Park grass (less common)
TOWN_MARKET_COLOR = (118, 105, 95)            # Warm market stone
STONE_FLOOR_COLOR = (95, 95, 98)              # Stone floor
STONE_WALL_COLOR = (72, 72, 78)               # Stone wall (cooler)
WOODEN_FLOOR_COLOR = (88, 75, 62)             # Wooden floor (taverns, inns)
WOODEN_WALL_COLOR = (105, 92, 78)             # Wooden wall


TOWN_COBBLESTONE_TILE = Tile(
    walkable=True,
    blocks_sight=False,
    color=TOWN_COBBLESTONE_COLOR,
)

TOWN_PLAZA_TILE = Tile(
    walkable=True,
    blocks_sight=False,
    color=TOWN_PLAZA_COLOR,
)

TOWN_GRASS_TILE = Tile(
    walkable=True,
    blocks_sight=False,
    color=TOWN_GRASS_COLOR,
)

TOWN_MARKET_TILE = Tile(
    walkable=True,
    blocks_sight=False,
    color=TOWN_MARKET_COLOR,
)

STONE_FLOOR_TILE = Tile(
    walkable=True,
    blocks_sight=False,
    color=STONE_FLOOR_COLOR,
)

STONE_WALL_TILE = Tile(
    walkable=False,
    blocks_sight=True,
    color=STONE_WALL_COLOR,
)

WOODEN_FLOOR_TILE = Tile(
    walkable=True,
    blocks_sight=False,
    color=WOODEN_FLOOR_COLOR,
)

WOODEN_WALL_TILE = Tile(
    walkable=False,
    blocks_sight=True,
    color=WOODEN_WALL_COLOR,
)

# Building entrance (door) - walkable but visually distinct
BUILDING_ENTRANCE_COLOR = (55, 55, 60)  # Dark stone door
BUILDING_ENTRANCE_TILE = Tile(
    walkable=True,
    blocks_sight=False,
    color=BUILDING_ENTRANCE_COLOR,
)

# Decorative elements
FOUNTAIN_COLOR = (75, 105, 130)  # Cool blue-gray for fountains
FOUNTAIN_TILE = Tile(
    walkable=False,
    blocks_sight=False,
    color=FOUNTAIN_COLOR,
)

# Market stall (decorative, doesn't block movement)
MARKET_STALL_COLOR = (115, 95, 75)  # Warm brown for stalls
MARKET_STALL_TILE = Tile(
    walkable=True,
    blocks_sight=False,
    color=MARKET_STALL_COLOR,
)

# Bench - decorative plaza seating
BENCH_COLOR = (95, 80, 60)  # Stone/wood bench
BENCH_TILE = Tile(
    walkable=False,
    blocks_sight=False,
    color=BENCH_COLOR,
)
