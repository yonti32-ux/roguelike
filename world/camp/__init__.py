"""
Camp system: simple camp maps, tiles, and NPC stubs.

This mirrors the structure of the village system but is intentionally
much simpler: small outdoor maps with a campfire, tents, and a few NPCs.
"""

from .generation import generate_camp
from .tiles import (
    CAMP_GROUND_TILE,
    CAMP_FIRE_TILE,
    CAMP_TENT_TILE,
)
from .npcs import (
    CampNPC,
    CampMerchantNPC,
    CampGuardNPC,
    CampTravelerNPC,
)

__all__ = [
    "generate_camp",
    "CAMP_GROUND_TILE",
    "CAMP_FIRE_TILE",
    "CAMP_TENT_TILE",
    "CampNPC",
    "CampMerchantNPC",
    "CampGuardNPC",
    "CampTravelerNPC",
]


