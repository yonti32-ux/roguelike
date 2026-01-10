"""
Points of Interest (POI) system.

Manages all types of POIs: dungeons, villages, towns, camps, etc.
Uses a registry pattern for extensible POI type management.
"""

from .base import PointOfInterest
from .types import DungeonPOI, VillagePOI, TownPOI, CampPOI
from .placement import place_pois
from .registry import POIRegistry, get_registry, register_poi_type

# Import types module to trigger auto-registration
# (This ensures all POI types are registered when the package is imported)
from . import types as _  # noqa: F401

__all__ = [
    "PointOfInterest",
    "DungeonPOI",
    "VillagePOI",
    "TownPOI",
    "CampPOI",
    "place_pois",
    "POIRegistry",
    "get_registry",
    "register_poi_type",
]

