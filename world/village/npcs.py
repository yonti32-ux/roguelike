"""
Village NPC classes.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from ..entities import Entity
from settings import TILE_SIZE


@dataclass
class VillageNPC(Entity):
    """Base class for village NPCs (non-hostile entities)."""
    # Required fields (no defaults) - must come before fields with defaults
    npc_type: str = "villager"  # "merchant", "innkeeper", "recruiter", "villager"
    # Fields with defaults
    building_id: Optional[str] = None  # ID of building this NPC is in
    dialogue: List[str] = field(default_factory=list)  # Dialogue lines
    name: str = "NPC"
    color: Tuple[int, int, int] = (150, 150, 200)  # Default NPC color (bluish)
    blocks_movement: bool = True  # NPCs block movement (like other entities)
    
    def __post_init__(self) -> None:
        """Initialize NPC after creation."""
        # NPCs are non-hostile but do block movement
        self.blocks_movement = True


class MerchantNPC(VillageNPC):
    """Merchant NPC that opens the shop."""
    def __init__(
        self,
        x: float,
        y: float,
        npc_id: str = "merchant",
        name: str = "Merchant",
        building_id: Optional[str] = None,
    ):
        super().__init__(
            x=x,
            y=y,
            width=24,
            height=24,
            npc_type="merchant",
            building_id=building_id,
            name=name,
            color=(200, 180, 120),  # Warm merchant color
            blocks_movement=True,
        )
        self.npc_id = npc_id
        self.dialogue = [
            "Welcome to my shop!",
            "What can I get for you today?",
        ]


class InnkeeperNPC(VillageNPC):
    """Innkeeper NPC that provides rest/healing."""
    def __init__(
        self,
        x: float,
        y: float,
        npc_id: str = "innkeeper",
        name: str = "Innkeeper",
        building_id: Optional[str] = None,
    ):
        super().__init__(
            x=x,
            y=y,
            width=24,
            height=24,
            npc_type="innkeeper",
            building_id=building_id,
            name=name,
            color=(180, 200, 150),  # Greenish innkeeper color
            blocks_movement=True,
        )
        self.npc_id = npc_id
        self.dialogue = [
            "Welcome to the inn!",
            "Would you like to rest?",
        ]


class RecruiterNPC(VillageNPC):
    """Recruiter NPC that shows available companions."""
    def __init__(
        self,
        x: float,
        y: float,
        npc_id: str = "recruiter",
        name: str = "Tavern Keeper",
        building_id: Optional[str] = None,
    ):
        super().__init__(
            x=x,
            y=y,
            width=24,
            height=24,
            npc_type="recruiter",
            building_id=building_id,
            name=name,
            color=(200, 150, 150),  # Reddish recruiter color
            blocks_movement=True,
        )
        self.npc_id = npc_id
        self.dialogue = [
            "Looking for companions?",
            "We have adventurers seeking work!",
        ]


class VillagerNPC(VillageNPC):
    """Generic villager NPC (atmosphere, future quests)."""
    def __init__(
        self,
        x: float,
        y: float,
        npc_id: str = "villager",
        name: str = "Villager",
        building_id: Optional[str] = None,
    ):
        super().__init__(
            x=x,
            y=y,
            width=24,
            height=24,
            npc_type="villager",
            building_id=building_id,
            name=name,
            color=(150, 150, 150),  # Grey villager color
            blocks_movement=True,
        )
        self.npc_id = npc_id
        self.dialogue = [
            "Hello, traveler!",
            "Welcome to our village!",
        ]


def create_npc_for_building(
    building_type: str,
    building_center_x: int,
    building_center_y: int,
    npc_id: Optional[str] = None,
    building_id: Optional[str] = None,
) -> Optional[VillageNPC]:
    """
    Create an appropriate NPC for a building type.
    
    Args:
        building_type: Type of building ("shop", "inn", "tavern", "house")
        building_center_x: Center X tile coordinate
        building_center_y: Center Y tile coordinate
        npc_id: Optional NPC ID
        building_id: Optional building ID
        
    Returns:
        VillageNPC instance, or None if building doesn't need an NPC
    """
    # Convert tile coordinates to world coordinates
    world_x = building_center_x * TILE_SIZE + (TILE_SIZE - 24) / 2
    world_y = building_center_y * TILE_SIZE + (TILE_SIZE - 24) / 2
    
    if building_type == "shop":
        return MerchantNPC(
            world_x,
            world_y,
            npc_id=npc_id or "merchant",
            building_id=building_id,
        )
    elif building_type == "inn":
        return InnkeeperNPC(
            world_x,
            world_y,
            npc_id=npc_id or "innkeeper",
            building_id=building_id,
        )
    elif building_type == "tavern":
        return RecruiterNPC(
            world_x,
            world_y,
            npc_id=npc_id or "recruiter",
            building_id=building_id,
        )
    elif building_type == "house":
        # Houses can optionally have villagers, but not required
        # For now, skip villagers in houses (can add later)
        return None
    else:
        return None

