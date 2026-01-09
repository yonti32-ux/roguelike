"""
Village system: map generation, buildings, NPCs, and tiles.
"""

from .generation import generate_village
from .buildings import (
    Building,
    ShopBuilding,
    InnBuilding,
    TavernBuilding,
    HouseBuilding,
    place_buildings,
)
from .npcs import (
    VillageNPC,
    MerchantNPC,
    InnkeeperNPC,
    RecruiterNPC,
    VillagerNPC,
    create_npc_for_building,
)
from .tiles import (
    VILLAGE_PATH_TILE,
    VILLAGE_PLAZA_TILE,
    VILLAGE_GRASS_TILE,
    BUILDING_FLOOR_TILE,
    BUILDING_WALL_TILE,
)

__all__ = [
    # Generation
    "generate_village",
    # Buildings
    "Building",
    "ShopBuilding",
    "InnBuilding",
    "TavernBuilding",
    "HouseBuilding",
    "place_buildings",
    # NPCs
    "VillageNPC",
    "MerchantNPC",
    "InnkeeperNPC",
    "RecruiterNPC",
    "VillagerNPC",
    "create_npc_for_building",
    # Tiles
    "VILLAGE_PATH_TILE",
    "VILLAGE_PLAZA_TILE",
    "VILLAGE_GRASS_TILE",
    "BUILDING_FLOOR_TILE",
    "BUILDING_WALL_TILE",
]

