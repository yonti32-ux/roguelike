"""
Points of Interest (POI) system.

Manages all types of POIs: dungeons, villages, towns, camps, etc.
"""

from .base import PointOfInterest
from .types import DungeonPOI, VillagePOI, TownPOI, CampPOI
from .placement import place_pois

__all__ = [
    "PointOfInterest",
    "DungeonPOI",
    "VillagePOI",
    "TownPOI",
    "CampPOI",
    "place_pois",
]

