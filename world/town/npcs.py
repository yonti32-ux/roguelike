"""
Town NPC classes.

Towns have more NPC types than villages: blacksmiths, librarians, etc.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple
import random

from ..entities import Entity
from settings import TILE_SIZE


def _generate_npc_name(role: str = "citizen") -> str:
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
            "mayor": ["Mayor", "Governor", "Magistrate", "Council Leader"],
            "blacksmith": ["Blacksmith", "Forge Master", "Armorer", "Weaponsmith"],
            "librarian": ["Librarian", "Scholar", "Scribe", "Archivist"],
            "citizen": ["Citizen", "Townsfolk", "Local", "Resident"],
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
            "mayor": ["Mayor", "Governor"],
            "blacksmith": ["Blacksmith", "Forge Master"],
            "librarian": ["Librarian", "Scholar"],
            "citizen": ["Citizen", "Townsfolk"],
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
        ["Step right up!", "Best prices in town, I guarantee it."],
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
        ["Welcome to our inn!", "Stay as long as you need."],
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


def _generate_mayor_dialogue() -> List[str]:
    """Generate varied dialogue for mayors."""
    dialogues = [
        ["Welcome, adventurer!", "Our town needs your help.", "I have tasks that need doing."],
        ["Ah, a hero approaches!", "We have many problems that require your attention."],
        ["Greetings, brave soul!", "The town could use someone like you."],
        ["Welcome, traveler!", "We have urgent matters that need addressing."],
        ["Ah, finally someone capable!", "I've been waiting for an adventurer like you."],
        ["Greetings!", "Our town faces many challenges. Perhaps you can help?"],
    ]
    return random.choice(dialogues)


def _generate_blacksmith_dialogue() -> List[str]:
    """Generate varied dialogue for blacksmiths."""
    dialogues = [
        ["Welcome to my forge!", "I can upgrade your weapons and armor."],
        ["Ah, an adventurer!", "Need your gear improved? I'm the best in town."],
        ["Greetings!", "I craft the finest weapons and armor around."],
        ["Welcome!", "Looking to enhance your equipment?"],
        ["Come in!", "I can make your weapons stronger and armor tougher."],
        ["Welcome to the forge!", "Let me help you prepare for battle."],
    ]
    return random.choice(dialogues)


def _generate_librarian_dialogue() -> List[str]:
    """Generate varied dialogue for librarians."""
    dialogues = [
        ["Welcome to the library!", "Knowledge is power, adventurer."],
        ["Ah, a seeker of knowledge!", "We have many books that might interest you."],
        ["Greetings!", "The library holds many secrets and skills."],
        ["Welcome!", "Looking to learn something new?"],
        ["Come in!", "We have skill books and knowledge to share."],
        ["Welcome, scholar!", "What knowledge do you seek?"],
    ]
    return random.choice(dialogues)


def _generate_citizen_dialogue() -> List[str]:
    """Generate varied dialogue for citizens."""
    dialogues = [
        ["Hello, traveler!", "Welcome to our town!"],
        ["Good day!", "Nice to see a new face around here."],
        ["Greetings!", "Hope you find what you're looking for."],
        ["Hello there!", "Beautiful day, isn't it?"],
        ["Well met!", "Safe travels, adventurer."],
        ["Hey there!", "Enjoy your stay in our town."],
        ["Good morning!", "The town is always happy to see travelers."],
        ["Hello!", "Watch out for trouble on the roads."],
    ]
    return random.choice(dialogues)


@dataclass
class TownNPC(Entity):
    """Base class for town NPCs (non-hostile entities)."""
    # Required fields (no defaults) - must come before fields with defaults
    npc_type: str = "citizen"  # "merchant", "innkeeper", "recruiter", "citizen", etc.
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


class MerchantNPC(TownNPC):
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


class InnkeeperNPC(TownNPC):
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


class RecruiterNPC(TownNPC):
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


class MayorNPC(TownNPC):
    """Town Mayor NPC that gives quests."""
    def __init__(
        self,
        x: float,
        y: float,
        npc_id: str = "mayor",
        name: Optional[str] = None,
        building_id: Optional[str] = None,
    ):
        generated_name = name or _generate_npc_name("mayor")
        super().__init__(
            x=x,
            y=y,
            width=24,
            height=24,
            npc_type="mayor",
            building_id=building_id,
            name=generated_name,
            color=(180, 160, 220),  # Purple/violet mayor color
            blocks_movement=True,
        )
        self.npc_id = npc_id
        self.dialogue = _generate_mayor_dialogue()


class BlacksmithNPC(TownNPC):
    """Blacksmith NPC for weapon/armor upgrades."""
    def __init__(
        self,
        x: float,
        y: float,
        npc_id: str = "blacksmith",
        name: Optional[str] = None,
        building_id: Optional[str] = None,
    ):
        generated_name = name or _generate_npc_name("blacksmith")
        super().__init__(
            x=x,
            y=y,
            width=24,
            height=24,
            npc_type="blacksmith",
            building_id=building_id,
            name=generated_name,
            color=(150, 100, 80),  # Brown/orange blacksmith color
            blocks_movement=True,
        )
        self.npc_id = npc_id
        self.dialogue = _generate_blacksmith_dialogue()


class LibrarianNPC(TownNPC):
    """Librarian NPC for skill books and knowledge."""
    def __init__(
        self,
        x: float,
        y: float,
        npc_id: str = "librarian",
        name: Optional[str] = None,
        building_id: Optional[str] = None,
    ):
        generated_name = name or _generate_npc_name("librarian")
        super().__init__(
            x=x,
            y=y,
            width=24,
            height=24,
            npc_type="librarian",
            building_id=building_id,
            name=generated_name,
            color=(120, 150, 200),  # Blue librarian color
            blocks_movement=True,
        )
        self.npc_id = npc_id
        self.dialogue = _generate_librarian_dialogue()


class CitizenNPC(TownNPC):
    """Generic citizen NPC (atmosphere, future quests)."""
    def __init__(
        self,
        x: float,
        y: float,
        npc_id: str = "citizen",
        name: Optional[str] = None,
        building_id: Optional[str] = None,
    ):
        generated_name = name or _generate_npc_name("citizen")
        super().__init__(
            x=x,
            y=y,
            width=24,
            height=24,
            npc_type="citizen",
            building_id=building_id,
            name=generated_name,
            color=(150, 150, 150),  # Grey citizen color
            blocks_movement=True,
        )
        self.npc_id = npc_id
        self.dialogue = _generate_citizen_dialogue()
        # Add speed for wandering behavior
        self.speed = 30.0  # Slower than enemies, peaceful pace


def create_npc_for_building(
    building_type: str,
    building_center_x: int,
    building_center_y: int,
    npc_id: Optional[str] = None,
    building_id: Optional[str] = None,
) -> Optional[TownNPC]:
    """
    Create an appropriate NPC for a building type.
    
    Args:
        building_type: Type of building ("shop", "inn", "tavern", "blacksmith", etc.)
        building_center_x: Center X tile coordinate
        building_center_y: Center Y tile coordinate
        npc_id: Optional NPC ID
        building_id: Optional building ID
        
    Returns:
        TownNPC instance, or None if building doesn't need an NPC
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
    elif building_type == "town_hall":
        return MayorNPC(
            world_x,
            world_y,
            npc_id=npc_id or "mayor",
            building_id=building_id,
        )
    elif building_type == "blacksmith":
        return BlacksmithNPC(
            world_x,
            world_y,
            npc_id=npc_id or "blacksmith",
            building_id=building_id,
        )
    elif building_type == "library":
        return LibrarianNPC(
            world_x,
            world_y,
            npc_id=npc_id or "librarian",
            building_id=building_id,
        )
    elif building_type == "market":
        # Markets can have merchants (50% chance)
        if random.random() < 0.5:
            return MerchantNPC(
                world_x,
                world_y,
                npc_id=npc_id or "market_merchant",
                building_id=building_id,
            )
        return None
    elif building_type == "house":
        # Houses can optionally have citizens (30% chance)
        if random.random() < 0.3:
            return CitizenNPC(
                world_x,
                world_y,
                npc_id=npc_id or "house_citizen",
                building_id=building_id,
            )
        return None
    else:
        return None


def create_wandering_citizen(
    x: float,
    y: float,
    npc_id: Optional[str] = None,
) -> CitizenNPC:
    """
    Create a wandering citizen NPC for placement outside buildings.
    
    Args:
        x: World X coordinate
        y: World Y coordinate
        npc_id: Optional NPC ID
        
    Returns:
        CitizenNPC instance
    """
    return CitizenNPC(
        x=x,
        y=y,
        npc_id=npc_id or "wandering_citizen",
    )
