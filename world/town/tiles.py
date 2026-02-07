"""
Town-specific tile types.

Towns use more sophisticated tiles than villages: cobblestone streets,
market areas, stone buildings, etc.
"""

from dataclasses import dataclass
from typing import Tuple

from ..tiles import Tile


# Town tile colors (more urban, stone-based)
TOWN_COBBLESTONE_COLOR = (100, 100, 100)      # Gray cobblestone
TOWN_PLAZA_COLOR = (90, 90, 100)              # Stone plaza
TOWN_GRASS_COLOR = (50, 80, 50)               # Darker grass (less common in towns)
TOWN_MARKET_COLOR = (110, 100, 90)            # Market area (lighter stone)
STONE_FLOOR_COLOR = (90, 90, 90)              # Stone floor (for buildings)
STONE_WALL_COLOR = (70, 70, 70)               # Stone wall
WOODEN_FLOOR_COLOR = (80, 70, 60)             # Wooden floor (for some buildings)
WOODEN_WALL_COLOR = (100, 90, 80)             # Wooden wall (for some buildings)


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
BUILDING_ENTRANCE_COLOR = (60, 60, 60)  # Darker stone for doors
BUILDING_ENTRANCE_TILE = Tile(
    walkable=True,
    blocks_sight=False,
    color=BUILDING_ENTRANCE_COLOR,
)

# Decorative elements
FOUNTAIN_COLOR = (80, 100, 120)  # Blue-gray for fountains
FOUNTAIN_TILE = Tile(
    walkable=False,
    blocks_sight=False,
    color=FOUNTAIN_COLOR,
)

# Market stall (decorative, doesn't block movement)
MARKET_STALL_COLOR = (120, 100, 80)  # Brown for market stalls
MARKET_STALL_TILE = Tile(
    walkable=True,
    blocks_sight=False,
    color=MARKET_STALL_COLOR,
)
