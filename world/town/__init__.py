"""
Town system: map generation, buildings, NPCs, and tiles.
"""

from .generation import generate_town
from .buildings import (
    Building,
    ShopBuilding,
    InnBuilding,
    TavernBuilding,
    BlacksmithBuilding,
    LibraryBuilding,
    MarketBuilding,
    TownHallBuilding,
    HouseBuilding,
    place_buildings,
)
from .npcs import (
    TownNPC,
    MerchantNPC,
    InnkeeperNPC,
    RecruiterNPC,
    MayorNPC,
    BlacksmithNPC,
    LibrarianNPC,
    CitizenNPC,
    create_npc_for_building,
    create_wandering_citizen,
)
from .tiles import (
    TOWN_COBBLESTONE_TILE,
    TOWN_PLAZA_TILE,
    TOWN_GRASS_TILE,
    TOWN_MARKET_TILE,
    STONE_FLOOR_TILE,
    STONE_WALL_TILE,
    WOODEN_FLOOR_TILE,
    WOODEN_WALL_TILE,
    BUILDING_ENTRANCE_TILE,
    FOUNTAIN_TILE,
    MARKET_STALL_TILE,
)

__all__ = [
    # Generation
    "generate_town",
    # Buildings
    "Building",
    "ShopBuilding",
    "InnBuilding",
    "TavernBuilding",
    "BlacksmithBuilding",
    "LibraryBuilding",
    "MarketBuilding",
    "TownHallBuilding",
    "HouseBuilding",
    "place_buildings",
    # NPCs
    "TownNPC",
    "MerchantNPC",
    "InnkeeperNPC",
    "RecruiterNPC",
    "MayorNPC",
    "BlacksmithNPC",
    "LibrarianNPC",
    "CitizenNPC",
    "create_npc_for_building",
    "create_wandering_citizen",
    # Tiles
    "TOWN_COBBLESTONE_TILE",
    "TOWN_PLAZA_TILE",
    "TOWN_GRASS_TILE",
    "TOWN_MARKET_TILE",
    "STONE_FLOOR_TILE",
    "STONE_WALL_TILE",
    "WOODEN_FLOOR_TILE",
    "WOODEN_WALL_TILE",
    "BUILDING_ENTRANCE_TILE",
    "FOUNTAIN_TILE",
    "MARKET_STALL_TILE",
]
