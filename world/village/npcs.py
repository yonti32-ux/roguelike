"""
Village NPC classes.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple
import random

from ..entities import Entity
from settings import TILE_SIZE


def _generate_npc_name(role: str = "villager") -> str:
    """Generate a name for an NPC based on their role."""
    try:
        from systems.namegen.pools import get_pools
        pools = get_pools()
        
        # First names (simple fantasy names)
        first_names = [
            "Aldric", "Bram", "Cedric", "Doran", "Erik", "Finn", "Gareth", "Hugo",
            "Ivor", "Jasper", "Kael", "Liam", "Marcus", "Nolan", "Owen", "Piers",
            "Quinn", "Rhys", "Silas", "Tristan", "Vance", "Wade", "Xander", "Yves",
            "Zane",
            "Aria", "Brynn", "Cora", "Dara", "Eira", "Faye", "Gwen", "Hazel",
            "Iris", "Jade", "Kira", "Luna", "Maya", "Nora", "Opal", "Pearl",
            "Quinn", "Rose", "Skye", "Tara", "Uma", "Vera", "Willow", "Yara", "Zoe"
        ]
        
        # Titles/roles for NPCs
        titles = {
            "merchant": ["Merchant", "Trader", "Shopkeeper", "Vendor"],
            "innkeeper": ["Innkeeper", "Host", "Landlord", "Hostess"],
            "recruiter": ["Recruiter", "Guild Master", "Tavern Keeper", "Hiring Agent"],
            "elder": ["Elder", "Mayor", "Sage", "Councilor", "Leader"],
            "villager": ["Villager", "Citizen", "Local", "Resident"],
        }
        
        first_name = random.choice(first_names)
        title = random.choice(titles.get(role, ["NPC"]))
        
        # Sometimes just use first name, sometimes with title
        if random.random() < 0.6:
            return first_name
        else:
            return f"{first_name} the {title}"
            
    except Exception:
        # Fallback to simple names
        fallback_names = {
            "merchant": ["Trader", "Merchant", "Shopkeeper"],
            "innkeeper": ["Innkeeper", "Host"],
            "recruiter": ["Recruiter", "Guild Master"],
            "elder": ["Elder", "Mayor"],
            "villager": ["Villager", "Citizen"],
        }
        return random.choice(fallback_names.get(role, ["NPC"]))


def _generate_merchant_dialogue() -> List[str]:
    """Generate varied dialogue for merchants."""
    dialogues = [
        ["Welcome to my shop!", "What can I get for you today?"],
        ["Greetings, traveler!", "Browse my wares - finest goods around."],
        ["Ah, a customer!", "Take your time, I have plenty to offer."],
        ["Welcome, welcome!", "Looking for something specific?"],
        ["Good to see you!", "I've got just what you need."],
        ["Step right up!", "Best prices in the village, I guarantee it."],
    ]
    return random.choice(dialogues)


def _generate_innkeeper_dialogue() -> List[str]:
    """Generate varied dialogue for innkeepers."""
    dialogues = [
        ["Welcome to the inn!", "Would you like to rest?"],
        ["Ah, a weary traveler!", "Our beds are the most comfortable around."],
        ["Welcome, friend!", "Rest here and restore your strength."],
        ["Good to see you!", "Need a place to rest? We've got rooms."],
        ["Come in, come in!", "A good rest will do you wonders."],
        ["Welcome to our humble inn!", "Stay as long as you need."],
    ]
    return random.choice(dialogues)


def _generate_recruiter_dialogue() -> List[str]:
    """Generate varied dialogue for recruiters."""
    dialogues = [
        ["Looking for companions?", "We have adventurers seeking work!"],
        ["Need help on your journey?", "I know some capable fighters looking for work."],
        ["Seeking allies?", "The guild has many skilled adventurers available."],
        ["Want to expand your party?", "I can introduce you to some reliable companions."],
        ["Traveling alone?", "We have adventurers who could use a leader."],
        ["Looking to recruit?", "I have contacts with several experienced adventurers."],
    ]
    return random.choice(dialogues)


def _generate_elder_dialogue() -> List[str]:
    """Generate varied dialogue for elders."""
    dialogues = [
        ["Welcome, adventurer!", "Our village needs your help.", "I have tasks that need doing."],
        ["Ah, a hero approaches!", "We have many problems that require your attention."],
        ["Greetings, brave soul!", "The village could use someone like you."],
        ["Welcome, traveler!", "We have urgent matters that need addressing."],
        ["Ah, finally someone capable!", "I've been waiting for an adventurer like you."],
        ["Greetings!", "Our village faces many challenges. Perhaps you can help?"],
    ]
    return random.choice(dialogues)


def _generate_villager_dialogue() -> List[str]:
    """Generate varied dialogue for villagers."""
    dialogues = [
        ["Hello, traveler!", "Welcome to our village!"],
        ["Good day!", "Nice to see a new face around here."],
        ["Greetings!", "Hope you find what you're looking for."],
        ["Hello there!", "Beautiful day, isn't it?"],
        ["Well met!", "Safe travels, adventurer."],
        ["Hey there!", "Enjoy your stay in our village."],
        ["Good morning!", "The village is always happy to see travelers."],
        ["Hello!", "Watch out for trouble on the roads."],
    ]
    return random.choice(dialogues)


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
        name: Optional[str] = None,
        building_id: Optional[str] = None,
    ):
        generated_name = name or _generate_npc_name("merchant")
        super().__init__(
            x=x,
            y=y,
            width=24,
            height=24,
            npc_type="merchant",
            building_id=building_id,
            name=generated_name,
            color=(200, 180, 120),  # Warm merchant color
            blocks_movement=True,
        )
        self.npc_id = npc_id
        self.dialogue = _generate_merchant_dialogue()


class InnkeeperNPC(VillageNPC):
    """Innkeeper NPC that provides rest/healing."""
    def __init__(
        self,
        x: float,
        y: float,
        npc_id: str = "innkeeper",
        name: Optional[str] = None,
        building_id: Optional[str] = None,
    ):
        generated_name = name or _generate_npc_name("innkeeper")
        super().__init__(
            x=x,
            y=y,
            width=24,
            height=24,
            npc_type="innkeeper",
            building_id=building_id,
            name=generated_name,
            color=(180, 200, 150),  # Greenish innkeeper color
            blocks_movement=True,
        )
        self.npc_id = npc_id
        self.dialogue = _generate_innkeeper_dialogue()


class RecruiterNPC(VillageNPC):
    """Recruiter NPC that shows available companions."""
    def __init__(
        self,
        x: float,
        y: float,
        npc_id: str = "recruiter",
        name: Optional[str] = None,
        building_id: Optional[str] = None,
    ):
        generated_name = name or _generate_npc_name("recruiter")
        super().__init__(
            x=x,
            y=y,
            width=24,
            height=24,
            npc_type="recruiter",
            building_id=building_id,
            name=generated_name,
            color=(200, 150, 150),  # Reddish recruiter color
            blocks_movement=True,
        )
        self.npc_id = npc_id
        self.dialogue = _generate_recruiter_dialogue()


class VillagerNPC(VillageNPC):
    """Generic villager NPC (atmosphere, future quests)."""
    def __init__(
        self,
        x: float,
        y: float,
        npc_id: str = "villager",
        name: Optional[str] = None,
        building_id: Optional[str] = None,
    ):
        generated_name = name or _generate_npc_name("villager")
        super().__init__(
            x=x,
            y=y,
            width=24,
            height=24,
            npc_type="villager",
            building_id=building_id,
            name=generated_name,
            color=(150, 150, 150),  # Grey villager color
            blocks_movement=True,
        )
        self.npc_id = npc_id
        self.dialogue = _generate_villager_dialogue()
        # Add speed for wandering behavior
        self.speed = 30.0  # Slower than enemies, peaceful pace


class ElderNPC(VillageNPC):
    """Village Elder NPC that gives quests."""
    def __init__(
        self,
        x: float,
        y: float,
        npc_id: str = "elder",
        name: Optional[str] = None,
        building_id: Optional[str] = None,
    ):
        generated_name = name or _generate_npc_name("elder")
        super().__init__(
            x=x,
            y=y,
            width=24,
            height=24,
            npc_type="elder",
            building_id=building_id,
            name=generated_name,
            color=(180, 160, 220),  # Purple/violet elder color
            blocks_movement=True,
        )
        self.npc_id = npc_id
        self.dialogue = _generate_elder_dialogue()
        # Store reference to quest giver system
        self.quest_giver = None


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
    elif building_type == "town_hall" or building_type == "elder_hall":
        # Town hall or elder's hall contains the elder
        return ElderNPC(
            world_x,
            world_y,
            npc_id=npc_id or "elder",
            building_id=building_id,
        )
    elif building_type == "house":
        # Houses can optionally have villagers (30% chance)
        if random.random() < 0.3:
            return VillagerNPC(
                world_x,
                world_y,
                npc_id=npc_id or "house_villager",
                building_id=building_id,
            )
        return None
    else:
        return None


def create_wandering_villager(
    x: float,
    y: float,
    npc_id: Optional[str] = None,
) -> VillagerNPC:
    """
    Create a wandering villager NPC for placement outside buildings.
    
    Args:
        x: World X coordinate
        y: World Y coordinate
        npc_id: Optional NPC ID
        
    Returns:
        VillagerNPC instance
    """
    return VillagerNPC(
        x=x,
        y=y,
        npc_id=npc_id or "wandering_villager",
    )

