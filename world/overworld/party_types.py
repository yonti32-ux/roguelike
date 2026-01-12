"""
Party type definitions for roaming parties on the overworld.

Defines different types of parties that can roam the map, their behaviors,
relationships, and properties.
"""

from dataclasses import dataclass, field
from typing import List, Set, Optional, Dict, Tuple
from enum import Enum


class PartyAlignment(Enum):
    """Alignment/faction of a party."""
    FRIENDLY = "friendly"  # Allies to player
    NEUTRAL = "neutral"   # Neither friendly nor hostile
    HOSTILE = "hostile"   # Enemies to player
    PLAYER = "player"     # Player's own party


class PartyBehavior(Enum):
    """Behavior pattern for party movement."""
    PATROL = "patrol"              # Patrol a small area
    TRAVEL = "travel"               # Travel between POIs (towns, villages)
    WANDER = "wander"               # Random wandering
    GUARD = "guard"                 # Guard a specific location
    HUNT = "hunt"                   # Actively hunt player or other parties
    FLEE = "flee"                   # Flee from threats


@dataclass
class PartyType:
    """
    Defines a type of roaming party.
    
    This is an extensible system that can be expanded with new party types
    in the future (merchants, villagers, bandits, monsters, etc.).
    """
    id: str
    name: str
    description: str
    
    # Alignment and relationships
    alignment: PartyAlignment
    behavior: PartyBehavior  # Must come before default arguments
    enemy_types: Set[str] = field(default_factory=set)  # Party type IDs this type is hostile to
    ally_types: Set[str] = field(default_factory=set)   # Party type IDs this type is friendly to
    
    # Behavior properties
    speed: float = 1.0  # Movement speed multiplier (1.0 = normal)
    sight_range: int = 5  # How many tiles they can see
    
    # Combat properties (if applicable)
    can_attack: bool = False  # Can this party initiate combat?
    can_be_attacked: bool = False  # Can this party be attacked?
    combat_strength: int = 1  # Relative strength (1 = weak, 5 = very strong)
    
    # Visual representation
    color: Tuple[int, int, int] = (128, 128, 128)  # RGB color for rendering
    sprite_id: Optional[str] = None  # For future sprite support
    icon: str = "?"  # Character icon/symbol for map
    
    # Spawn properties
    spawn_weight: float = 1.0  # Relative spawn probability
    min_level: int = 1  # Minimum player level to spawn
    max_level: int = 100  # Maximum player level to spawn
    
    # Special properties
    can_trade: bool = False  # Can player trade with this party?
    can_recruit: bool = False  # Can player recruit members from this party?
    gives_quests: bool = False  # Can this party give quests?
    
    # POI preferences (for travel behavior)
    preferred_poi_types: List[str] = field(default_factory=list)  # e.g., ["town", "village"]
    avoids_poi_types: List[str] = field(default_factory=list)  # e.g., ["dungeon"]
    
    # Faction
    faction_id: Optional[str] = None  # Which faction this party belongs to
    can_join_battle: bool = False  # Can this party fight in battles?
    battle_unit_template: Optional[str] = None  # Template for battle units (enemy archetype ID)


# Registry of party types
_PARTY_TYPES: Dict[str, PartyType] = {}


def register_party_type(party_type: PartyType) -> PartyType:
    """Register a party type."""
    if party_type.id in _PARTY_TYPES:
        raise ValueError(f"Party type already registered: {party_type.id}")
    _PARTY_TYPES[party_type.id] = party_type
    return party_type


def get_party_type(party_id: str) -> Optional[PartyType]:
    """Get a party type by ID."""
    return _PARTY_TYPES.get(party_id)


def all_party_types() -> List[PartyType]:
    """Get all registered party types."""
    return list(_PARTY_TYPES.values())


# ============================================================================
# Predefined Party Types
# ============================================================================

# Friendly/Neutral Parties
MERCHANT_PARTY = register_party_type(
    PartyType(
        id="merchant",
        name="Merchant Caravan",
        description="A traveling merchant caravan with goods to trade.",
        alignment=PartyAlignment.NEUTRAL,
        behavior=PartyBehavior.TRAVEL,
        speed=0.8,  # Slower due to cargo
        sight_range=6,
        can_attack=False,
        can_be_attacked=True,  # Can be robbed
        combat_strength=2,
        color=(255, 215, 0),  # Gold
        icon="M",
        spawn_weight=2.0,
        can_trade=True,
        preferred_poi_types=["town", "village"],
        faction_id="free_cities",  # Merchants belong to free cities
    )
)

VILLAGER_PARTY = register_party_type(
    PartyType(
        id="villager",
        name="Traveling Villagers",
        description="Villagers traveling between settlements.",
        alignment=PartyAlignment.FRIENDLY,
        behavior=PartyBehavior.TRAVEL,
        speed=1.0,
        sight_range=4,
        can_attack=False,
        can_be_attacked=True,
        combat_strength=1,
        color=(200, 200, 255),  # Light blue
        icon="V",
        spawn_weight=3.0,
        preferred_poi_types=["village", "town"],
        faction_id="kingdom_aetheria",  # Villagers belong to kingdom
    )
)

GUARD_PATROL = register_party_type(
    PartyType(
        id="guard",
        name="Guard Patrol",
        description="Town guards patrolling the roads.",
        alignment=PartyAlignment.FRIENDLY,
        enemy_types={"bandit", "monster"},
        behavior=PartyBehavior.PATROL,
        speed=1.2,
        sight_range=7,
        can_attack=True,
        can_be_attacked=False,  # Attacking guards has consequences
        combat_strength=3,
        color=(100, 150, 255),  # Blue
        icon="G",
        spawn_weight=1.5,
        preferred_poi_types=["town"],
        faction_id="kingdom_aetheria",  # Guards belong to kingdom
        can_join_battle=True,
    )
)

# Hostile Parties
BANDIT_PARTY = register_party_type(
    PartyType(
        id="bandit",
        name="Bandit Gang",
        description="A group of bandits looking for easy targets.",
        alignment=PartyAlignment.HOSTILE,
        enemy_types={"merchant", "villager", "guard"},
        behavior=PartyBehavior.WANDER,
        speed=1.1,
        sight_range=6,
        can_attack=True,
        can_be_attacked=True,
        combat_strength=2,
        color=(200, 0, 0),  # Red
        icon="B",
        spawn_weight=2.5,
        avoids_poi_types=["town"],  # Avoid towns with guards
        faction_id="bandit_confederacy",  # Bandits belong to bandit confederacy
        can_join_battle=True,
    )
)

MONSTER_PACK = register_party_type(
    PartyType(
        id="monster",
        name="Monster Pack",
        description="A pack of wild monsters roaming the wilderness.",
        alignment=PartyAlignment.HOSTILE,
        enemy_types={"merchant", "villager", "guard"},
        behavior=PartyBehavior.WANDER,
        speed=1.3,
        sight_range=8,
        can_attack=True,
        can_be_attacked=True,
        combat_strength=3,
        color=(139, 0, 139),  # Dark magenta
        icon="M",
        spawn_weight=2.0,
        avoids_poi_types=["town", "village"],
        can_join_battle=True,
    )
)

WOLF_PACK = register_party_type(
    PartyType(
        id="wolf",
        name="Wolf Pack",
        description="A pack of wolves hunting in the wilds.",
        alignment=PartyAlignment.HOSTILE,
        enemy_types={"merchant", "villager"},
        behavior=PartyBehavior.HUNT,
        speed=1.5,
        sight_range=10,
        can_attack=True,
        can_be_attacked=True,
        combat_strength=2,
        color=(128, 128, 128),  # Gray
        icon="W",
        spawn_weight=1.5,
        avoids_poi_types=["town", "village"],
    )
)

# Special Parties
ADVENTURER_PARTY = register_party_type(
    PartyType(
        id="adventurer",
        name="Adventuring Party",
        description="A group of fellow adventurers exploring the world.",
        alignment=PartyAlignment.FRIENDLY,
        behavior=PartyBehavior.WANDER,
        speed=1.0,
        sight_range=6,
        can_attack=False,
        can_be_attacked=False,
        combat_strength=4,
        color=(0, 255, 0),  # Green
        icon="A",
        spawn_weight=0.5,
        can_trade=True,
        can_recruit=True,
        gives_quests=True,
    )
)

# Additional Party Types
NOBLE_ENTOURAGE = register_party_type(
    PartyType(
        id="noble",
        name="Noble Entourage",
        description="A wealthy noble's traveling party with guards and servants.",
        alignment=PartyAlignment.NEUTRAL,
        behavior=PartyBehavior.TRAVEL,
        speed=0.7,  # Slow due to entourage
        sight_range=5,
        can_attack=False,
        can_be_attacked=True,
        combat_strength=4,  # Strong guards
        color=(255, 215, 0),  # Gold
        icon="N",
        spawn_weight=0.8,
        can_trade=True,
        preferred_poi_types=["town"],
        faction_id="kingdom_aetheria",  # Nobles belong to kingdom
    )
)

RANGER_PATROL = register_party_type(
    PartyType(
        id="ranger",
        name="Ranger Patrol",
        description="Forest rangers patrolling the wilderness.",
        alignment=PartyAlignment.FRIENDLY,
        enemy_types={"bandit", "monster", "wolf"},
        behavior=PartyBehavior.PATROL,
        speed=1.3,
        sight_range=9,
        can_attack=True,
        can_be_attacked=False,
        combat_strength=3,
        color=(34, 139, 34),  # Forest green
        icon="R",
        spawn_weight=1.2,
        preferred_poi_types=["village"],
        faction_id="wild_tribes",  # Rangers belong to wild tribes
        can_join_battle=True,
    )
)

CULTIST_GATHERING = register_party_type(
    PartyType(
        id="cultist",
        name="Cultist Gathering",
        description="A group of dark cultists performing rituals.",
        alignment=PartyAlignment.HOSTILE,
        enemy_types={"guard", "ranger", "adventurer"},
        behavior=PartyBehavior.WANDER,
        speed=0.9,
        sight_range=7,
        can_attack=True,
        can_be_attacked=True,
        combat_strength=3,
        color=(75, 0, 130),  # Indigo
        icon="C",
        spawn_weight=1.0,
        avoids_poi_types=["town", "village"],
        faction_id="shadow_cult",  # Cultists belong to shadow cult
        can_join_battle=True,
    )
)

ORC_RAIDING_PARTY = register_party_type(
    PartyType(
        id="orc",
        name="Orc Raiding Party",
        description="A war party of orcs looking for plunder.",
        alignment=PartyAlignment.HOSTILE,
        enemy_types={"merchant", "villager", "guard", "ranger"},
        behavior=PartyBehavior.HUNT,
        speed=1.2,
        sight_range=8,
        can_attack=True,
        can_be_attacked=True,
        combat_strength=4,
        color=(139, 69, 19),  # Brown
        icon="O",
        spawn_weight=1.5,
        avoids_poi_types=["town"],
        faction_id="bandit_confederacy",  # Orcs belong to bandit confederacy
        can_join_battle=True,
    )
)

TRADER_CARAVAN = register_party_type(
    PartyType(
        id="trader",
        name="Trader Caravan",
        description="A large trading caravan with valuable goods.",
        alignment=PartyAlignment.NEUTRAL,
        behavior=PartyBehavior.TRAVEL,
        speed=0.8,
        sight_range=6,
        can_attack=False,
        can_be_attacked=True,
        combat_strength=2,
        color=(255, 140, 0),  # Dark orange
        icon="T",
        spawn_weight=1.8,
        can_trade=True,
        preferred_poi_types=["town", "village"],
        faction_id="free_cities",  # Traders belong to free cities
    )
)

SCOUT_PARTY = register_party_type(
    PartyType(
        id="scout",
        name="Scout Party",
        description="Lightly armed scouts exploring the area.",
        alignment=PartyAlignment.FRIENDLY,
        behavior=PartyBehavior.WANDER,
        speed=1.4,
        sight_range=10,
        can_attack=False,
        can_be_attacked=True,
        combat_strength=2,
        color=(144, 238, 144),  # Light green
        icon="S",
        spawn_weight=1.0,
        faction_id="wild_tribes",  # Scouts belong to wild tribes
    )
)

GOBLIN_WARBAND = register_party_type(
    PartyType(
        id="goblin",
        name="Goblin Warband",
        description="A small group of goblins looking for trouble.",
        alignment=PartyAlignment.HOSTILE,
        enemy_types={"merchant", "villager", "guard"},
        behavior=PartyBehavior.WANDER,
        speed=1.0,
        sight_range=5,
        can_attack=True,
        can_be_attacked=True,
        combat_strength=1,
        color=(0, 128, 0),  # Dark green
        icon="g",
        spawn_weight=2.0,
        avoids_poi_types=["town"],
        faction_id="bandit_confederacy",  # Goblins belong to bandit confederacy
        can_join_battle=True,
    )
)

PILGRIM_GROUP = register_party_type(
    PartyType(
        id="pilgrim",
        name="Pilgrim Group",
        description="Religious pilgrims traveling to a holy site.",
        alignment=PartyAlignment.FRIENDLY,
        behavior=PartyBehavior.TRAVEL,
        speed=0.9,
        sight_range=4,
        can_attack=False,
        can_be_attacked=True,
        combat_strength=1,
        color=(255, 255, 224),  # Light yellow
        icon="P",
        spawn_weight=1.2,
        preferred_poi_types=["village", "town"],
        faction_id="kingdom_aetheria",  # Pilgrims belong to kingdom
    )
)

# Set up relationships
GUARD_PATROL.enemy_types = {"bandit", "monster", "wolf", "cultist", "orc", "goblin"}
GUARD_PATROL.ally_types = {"merchant", "villager", "adventurer", "ranger", "trader", "scout", "pilgrim"}

MERCHANT_PARTY.enemy_types = {"bandit", "monster", "wolf", "cultist", "orc", "goblin"}
MERCHANT_PARTY.ally_types = {"guard", "villager", "ranger"}

VILLAGER_PARTY.enemy_types = {"bandit", "monster", "wolf", "cultist", "orc", "goblin"}
VILLAGER_PARTY.ally_types = {"guard", "merchant", "ranger", "trader", "pilgrim"}

RANGER_PATROL.enemy_types = {"bandit", "monster", "wolf", "cultist", "orc", "goblin"}
RANGER_PATROL.ally_types = {"guard", "merchant", "villager", "adventurer", "scout"}

BANDIT_PARTY.enemy_types = {"guard", "merchant", "villager", "ranger", "trader", "noble"}
MONSTER_PACK.enemy_types = {"guard", "merchant", "villager", "ranger", "trader"}
WOLF_PACK.enemy_types = {"merchant", "villager", "pilgrim"}
CULTIST_GATHERING.enemy_types = {"guard", "ranger", "adventurer", "scout"}
ORC_RAIDING_PARTY.enemy_types = {"merchant", "villager", "guard", "ranger", "trader", "noble"}
GOBLIN_WARBAND.enemy_types = {"merchant", "villager", "guard", "ranger"}
TRADER_CARAVAN.enemy_types = {"bandit", "monster", "orc", "goblin"}
NOBLE_ENTOURAGE.enemy_types = {"bandit", "orc", "goblin"}
SCOUT_PARTY.enemy_types = {"cultist", "orc", "goblin"}
PILGRIM_GROUP.enemy_types = {"bandit", "monster", "wolf", "orc", "goblin"}

