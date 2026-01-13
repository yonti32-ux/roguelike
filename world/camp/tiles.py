"""
Camp-specific tile types.

Camps are small outdoor areas with a central campfire and a few tents,
using simple earthy colors to distinguish them from dungeons and villages.
"""

from ..tiles import Tile

# Base ground for camps (dirt/grass mix)
CAMP_GROUND_COLOR = (90, 80, 60)  # muted brownish ground

CAMP_GROUND_TILE = Tile(
    walkable=True,
    blocks_sight=False,
    color=CAMP_GROUND_COLOR,
)

# Campfire tile – walkable but visually distinct, may be used for center
CAMP_FIRE_COLOR = (180, 120, 60)  # warm orange/brown

CAMP_FIRE_TILE = Tile(
    walkable=True,
    blocks_sight=False,
    color=CAMP_FIRE_COLOR,
)

# Tent tile – blocks movement and sight a bit like a low wall
CAMP_TENT_COLOR = (140, 120, 90)

CAMP_TENT_TILE = Tile(
    walkable=False,
    blocks_sight=True,
    color=CAMP_TENT_COLOR,
)


