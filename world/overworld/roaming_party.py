"""
Roaming party entity for the overworld.

Represents a party that moves around the overworld map with various behaviors.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Tuple, List, Set, TYPE_CHECKING
import random
import math

if TYPE_CHECKING:
    from .map import OverworldMap
    from .party_types import PartyType
    from ..poi.base import PointOfInterest


@dataclass
class RoamingParty:
    """
    A party that roams the overworld map.
    
    Each party has a type, position, and behavior pattern that determines
    how it moves and interacts with the world.
    """
    party_id: str
    party_type_id: str
    x: int  # Tile X coordinate
    y: int  # Tile Y coordinate
    
    # Current state
    target_x: Optional[int] = None  # Current movement target
    target_y: Optional[int] = None
    path: List[Tuple[int, int]] = field(default_factory=list)  # Path to target
    
    # Behavior state
    behavior_state: str = "idle"  # Current behavior state
    last_move_time: float = 0.0  # Time since last movement
    move_cooldown: float = 1.0  # Seconds between moves
    failed_move_count: int = 0  # Count consecutive failed moves (for stuck detection)
    
    # Patrol/Wander state
    patrol_center_x: Optional[int] = None
    patrol_center_y: Optional[int] = None
    patrol_radius: int = 5
    
    # Travel state
    origin_poi_id: Optional[str] = None
    destination_poi_id: Optional[str] = None
    
    # Combat state
    in_combat: bool = False
    combat_target_id: Optional[str] = None
    
    # Special properties
    gold: int = 0  # Gold this party carries (for merchants, bandits, etc.)
    items: List[str] = field(default_factory=list)  # Items this party has
    
    # Faction
    faction_id: Optional[str] = None  # Which faction this party belongs to
    faction_relations: Dict[str, int] = field(default_factory=dict)  # Per-faction relations
    
    # Party metadata for better battle connection
    party_name: Optional[str] = None  # Custom name for this party instance
    party_size: int = 1  # Number of members in this party (for variation)
    health_state: str = "healthy"  # "healthy", "wounded", "defeated" (for parties that survive battles)
    
    def __post_init__(self):
        """Initialize party after creation."""
        # Set patrol center to starting position if not set
        if self.patrol_center_x is None:
            self.patrol_center_x = self.x
        if self.patrol_center_y is None:
            self.patrol_center_y = self.y
    
    def get_position(self) -> Tuple[int, int]:
        """Get current position."""
        return (self.x, self.y)
    
    def set_position(self, x: int, y: int) -> None:
        """Set position."""
        self.x = x
        self.y = y
        self.failed_move_count = 0  # Reset failed move count on successful move
    
    def distance_to(self, other_x: int, other_y: int) -> float:
        """Calculate distance to another position."""
        dx = other_x - self.x
        dy = other_y - self.y
        return math.sqrt(dx * dx + dy * dy)
    
    def distance_to_party(self, other: "RoamingParty") -> float:
        """Calculate distance to another party."""
        return self.distance_to(other.x, other.y)
    
    def is_at_target(self) -> bool:
        """Check if party has reached its target."""
        if self.target_x is None or self.target_y is None:
            return True
        return self.x == self.target_x and self.y == self.target_y
    
    def set_target(self, x: int, y: int) -> None:
        """Set a movement target."""
        self.target_x = x
        self.target_y = y
        self.path = []  # Clear old path
    
    def clear_target(self) -> None:
        """Clear movement target."""
        self.target_x = None
        self.target_y = None
        self.path = []
    
    def can_move(self, current_time: float) -> bool:
        """Check if party can move (cooldown check)."""
        return (current_time - self.last_move_time) >= self.move_cooldown
    
    def record_move(self, current_time: float) -> None:
        """Record that party has moved."""
        self.last_move_time = current_time


def create_roaming_party(
    party_type_id: str,
    x: int,
    y: int,
    party_id: Optional[str] = None,
    party_name: Optional[str] = None,
) -> RoamingParty:
    """
    Create a new roaming party.
    
    Args:
        party_type_id: ID of the party type
        x: Starting X coordinate
        y: Starting Y coordinate
        party_id: Optional unique ID (generated if not provided)
        party_name: Optional custom name for this party instance
    
    Returns:
        A new RoamingParty instance
    """
    from .party_types import get_party_type
    
    if party_id is None:
        party_id = f"{party_type_id}_{random.randint(1000, 9999)}"
    
    party_type = get_party_type(party_type_id)
    if party_type is None:
        raise ValueError(f"Unknown party type: {party_type_id}")
    
    # Initialize party with type-specific properties
    party = RoamingParty(
        party_id=party_id,
        party_type_id=party_type_id,
        x=x,
        y=y,
    )
    
    # Set move cooldown based on speed
    party.move_cooldown = 1.0 / max(0.1, party_type.speed)
    
    # Assign faction from party type
    if party_type.faction_id:
        party.faction_id = party_type.faction_id
    
    # Generate party name if not provided
    if party_name is None:
        party_name = _generate_party_name(party_type)
    party.party_name = party_name
    
    # Set party size variation (based on combat strength with some randomness)
    base_size = max(1, party_type.combat_strength)
    size_variation = random.randint(-1, 2)  # -1 to +2 variation
    party.party_size = max(1, base_size + size_variation)
    
    # Initialize gold for certain party types
    if party_type_id == "merchant":
        party.gold = random.randint(100, 500)
    elif party_type_id == "bandit":
        party.gold = random.randint(10, 100)
    elif party_type_id == "trader":
        party.gold = random.randint(200, 800)
    elif party_type_id == "noble":
        party.gold = random.randint(500, 1500)
    
    return party


def _generate_party_name(party_type: "PartyType") -> str:
    """
    Generate a unique name for a party based on its type.
    
    This adds variety to parties on the overworld.
    """
    import random
    
    # Name templates by party type
    name_templates = {
        "merchant": ["{}'s Caravan", "{} Trading Company", "{} Merchants", "{}'s Goods"],
        "bandit": ["{} Gang", "{} Bandits", "{} Raiders", "{} Outlaws"],
        "bandit_rogue": ["{} Gang", "{} Bandits", "{} Raiders", "{} Outlaws"],
        "guard": ["{} Patrol", "{} Guards", "{} Watch", "{} Sentinels"],
        "knight": ["{} Patrol", "{} Knights", "{} Order", "{} Company"],
        "villager": ["{} Travelers", "{} Group", "{} Villagers", "{} Settlers"],
        "monster": ["{} Pack", "{} Horde", "{} Swarm", "{} Pack"],
        "monster_brute": ["{} Pack", "{} Horde", "{} Swarm", "{} Pack"],
        "wolf": ["{} Pack", "{} Hunters", "{} Pack", "{} Pack"],
        "bear": ["{} Pack", "{} Bears", "{} Pack", "{} Pack"],
        "deer": ["{} Herd", "{} Deer", "{} Herd", "{} Herd"],
        "bird": ["{} Flock", "{} Birds", "{} Flock", "{} Flock"],
        "ranger": ["{} Patrol", "{} Rangers", "{} Scouts", "{} Trackers"],
        "cultist": ["{} Gathering", "{} Cult", "{} Sect", "{} Circle"],
        "orc": ["{} Raiders", "{} Warband", "{} Horde", "{} Tribe"],
        "goblin": ["{} Warband", "{} Gang", "{} Horde", "{} Tribe"],
        "skeleton": ["{} Warband", "{} Undead", "{} Horde", "{} Legion"],
        "trader": ["{} Caravan", "{} Traders", "{} Company", "{} Merchants"],
        "noble": ["{} Entourage", "{} Party", "{} Retinue", "{} Escort"],
        "scout": ["{} Scouts", "{} Party", "{} Patrol", "{} Rangers"],
        "pilgrim": ["{} Pilgrims", "{} Group", "{} Travelers", "{} Faithful"],
        "adventurer": ["{} Party", "{} Adventurers", "{} Company", "{} Heroes"],
        "mercenary": ["{} Company", "{} Mercenaries", "{} Band", "{} Company"],
        "thief": ["{} Gang", "{} Thieves", "{} Band", "{} Crew"],
        "assassin": ["{} Crew", "{} Assassins", "{} Guild", "{} Order"],
        "raider": ["{} Band", "{} Raiders", "{} Warband", "{} Horde"],
        "ghoul": ["{} Pack", "{} Ghouls", "{} Feeders", "{} Pack"],
        "zombie": ["{} Horde", "{} Zombies", "{} Horde", "{} Horde"],
        "wraith": ["{} Pack", "{} Wraiths", "{} Spirits", "{} Pack"],
        "mage": ["{} Cabal", "{} Mages", "{} Circle", "{} Order"],
        "warlock": ["{} Coven", "{} Warlocks", "{} Circle", "{} Coven"],
        "necromancer": ["{} Cult", "{} Necromancers", "{} Circle", "{} Cult"],
        "spider": ["{} Brood", "{} Spiders", "{} Nest", "{} Brood"],
        "boar": ["{} Herd", "{} Boars", "{} Herd", "{} Herd"],
        "dire_wolf": ["{} Pack", "{} Dire Wolves", "{} Pack", "{} Pack"],
        "troll": ["{} Band", "{} Trolls", "{} Tribe", "{} Band"],
        "ogre": ["{} Warband", "{} Ogres", "{} Tribe", "{} Warband"],
        "demon": ["{} Pack", "{} Demons", "{} Horde", "{} Pack"],
        "rat_swarm": ["{} Swarm", "{} Rats", "{} Swarm", "{} Swarm"],
        "goblin_shaman": ["{} Cult", "{} Goblins", "{} Tribe", "{} Cult"],
    }
    
    # Generic names if type not found
    generic_names = ["The {}s", "{} Group", "{} Party"]
    
    templates = name_templates.get(party_type.id, generic_names)
    template = random.choice(templates)
    
    # Use party type name as base
    base_name = party_type.name.split()[0] if party_type.name else party_type.id.title()
    
    return template.format(base_name)

