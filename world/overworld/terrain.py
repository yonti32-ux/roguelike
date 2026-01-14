"""
Terrain types for the overworld map.

Defines different terrain types with their properties.
"""

from dataclasses import dataclass
from typing import Tuple, Optional


@dataclass
class TerrainType:
    """Represents a type of terrain on the overworld."""
    
    id: str
    name: str
    color: Tuple[int, int, int]  # RGB color for rendering
    walkable: bool = True
    movement_cost: float = 1.0  # Time cost multiplier (1.0 = normal)
    sprite_id: Optional[str] = None  # For future sprite support


# Predefined terrain types
TERRAIN_GRASS = TerrainType(
    id="grass",
    name="Grass",
    color=(34, 139, 34),  # Forest green
    walkable=True,
    movement_cost=1.0,
)

TERRAIN_FOREST = TerrainType(
    id="forest",
    name="Forest",
    color=(0, 100, 0),  # Dark green
    walkable=True,
    movement_cost=1.5,
)

TERRAIN_MOUNTAIN = TerrainType(
    id="mountain",
    name="Mountain",
    color=(100, 100, 100),  # Darker gray for better visibility
    walkable=False,  # Mountains block movement
    movement_cost=999.0,
)

TERRAIN_WATER = TerrainType(
    id="water",
    name="Water",
    color=(0, 119, 190),  # Blue
    walkable=False,
    movement_cost=999.0,
)

TERRAIN_DESERT = TerrainType(
    id="desert",
    name="Desert",
    color=(238, 203, 173),  # Sandy beige
    walkable=True,
    movement_cost=1.2,
)

TERRAIN_PLAINS = TerrainType(
    id="plains",
    name="Plains",
    color=(144, 238, 144),  # Light green
    walkable=True,
    movement_cost=0.9,
)

TERRAIN_BEACH = TerrainType(
    id="beach",
    name="Beach",
    color=(255, 228, 196),  # Sandy beige
    walkable=True,
    movement_cost=1.1,
)

TERRAIN_SNOW = TerrainType(
    id="snow",
    name="Snow",
    color=(255, 255, 255),  # Pure white
    walkable=True,
    movement_cost=1.3,
)


# Registry of all terrain types
TERRAIN_REGISTRY: dict[str, TerrainType] = {
    "grass": TERRAIN_GRASS,
    "forest": TERRAIN_FOREST,
    "mountain": TERRAIN_MOUNTAIN,
    "water": TERRAIN_WATER,
    "desert": TERRAIN_DESERT,
    "plains": TERRAIN_PLAINS,
    "beach": TERRAIN_BEACH,
    "snow": TERRAIN_SNOW,
}


def get_terrain(terrain_id: str) -> Optional[TerrainType]:
    """Get a terrain type by ID."""
    return TERRAIN_REGISTRY.get(terrain_id)


def get_all_terrain_types() -> list[TerrainType]:
    """Get all registered terrain types."""
    return list(TERRAIN_REGISTRY.values())

