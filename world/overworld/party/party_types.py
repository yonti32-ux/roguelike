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


class SpawnCategory(Enum):
    """
    Spawn pool for modular spawning. Used to filter or weight spawns by
    category (e.g. wildlife-only areas, humanoid-only, undead zones).
    """
    ALL = "all"           # Appears in any pool when category filter is used
    WILDLIFE = "wildlife" # Animals, prey, natural creatures
    HUMANOID = "humanoid" # People, bandits, orcs, goblins, etc.
    UNDEAD = "undead"     # Skeletons, zombies, ghouls, wraiths, necromancers


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
    combat_strength: int = 1  # Legacy: relative strength (1-5). Use power_rating for dynamic scale.
    power_rating: Optional[float] = None  # Base power (e.g. 10-100). If None, derived from combat_strength.
    
    # Visual representation
    color: Tuple[int, int, int] = (128, 128, 128)  # RGB color for rendering
    sprite_id: Optional[str] = None  # For future sprite support
    icon: str = "?"  # Character icon/symbol for map
    
    # Spawn properties
    spawn_weight: float = 1.0  # Relative spawn probability
    min_level: int = 1  # Minimum player level to spawn
    max_level: int = 100  # Maximum player level to spawn
    spawn_category: SpawnCategory = SpawnCategory.ALL  # Pool for filtered spawns (wildlife / humanoid / undead)
    
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

    # Natural / wildlife (for hunt mechanic)
    is_natural_creature: bool = False  # Animal/wildlife; can gain hunt XP from killing prey
    is_prey: bool = False  # Prey species; being killed counts as a successful hunt for the killer


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


def party_types_for_spawn_category(category: SpawnCategory) -> List[PartyType]:
    """
    Get party types that belong to a spawn category (for modular spawn pools).
    Returns types where spawn_category == category or spawn_category == ALL.
    """
    return [
        pt for pt in _PARTY_TYPES.values()
        if pt.spawn_category == category or pt.spawn_category == SpawnCategory.ALL
    ]


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
        battle_unit_template="merchant_guard",  # Use merchant guard archetype
        can_join_battle=True,
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
        battle_unit_template="villager",  # Use villager archetype
        can_join_battle=True,
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
        battle_unit_template="town_guard",  # Use guard archetype
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
        battle_unit_template="bandit_cutthroat",
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
        battle_unit_template="troll_berserker",  # Use troll for generic monsters
        can_join_battle=True,
    )
)

WOLF_PACK = register_party_type(
    PartyType(
        id="wolf",
        name="Wolf Pack",
        description="A pack of wolves hunting in the wilds.",
        alignment=PartyAlignment.HOSTILE,
        enemy_types={"merchant", "villager", "deer"},
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
        battle_unit_template="wolf",  # Use wolf archetype
        can_join_battle=True,
        is_natural_creature=True,
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
        battle_unit_template="noble_guard",  # Use noble guard archetype
        can_join_battle=True,
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
        battle_unit_template="ranger",  # Use ranger archetype
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
        battle_unit_template="cultist_adept",  # Use cultist archetype
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
        battle_unit_template="orc_raider",
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
        battle_unit_template="merchant_guard",  # Use merchant guard archetype
        can_join_battle=True,
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
        battle_unit_template="scout",  # Use scout archetype
        can_join_battle=True,
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
        min_level=1,
        max_level=40,  # Early-game threat; rarer at high level
        avoids_poi_types=["town"],
        faction_id="bandit_confederacy",  # Goblins belong to bandit confederacy
        battle_unit_template="goblin_skirmisher",
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
        battle_unit_template="pilgrim",  # Use pilgrim archetype
        can_join_battle=True,
    )
)

# Natural/Wildlife Parties
BEAR_PACK = register_party_type(
    PartyType(
        id="bear",
        name="Bear Pack",
        description="A group of bears foraging in the wilderness.",
        alignment=PartyAlignment.HOSTILE,
        behavior=PartyBehavior.WANDER,
        speed=1.0,
        sight_range=6,
        can_attack=True,
        can_be_attacked=True,
        combat_strength=3,
        color=(139, 90, 43),  # Brown
        icon="B",
        spawn_weight=1.0,
        avoids_poi_types=["town", "village"],
        battle_unit_template="bear",  # Use bear archetype
        can_join_battle=True,
        is_natural_creature=True,
    )
)

DEER_HERD = register_party_type(
    PartyType(
        id="deer",
        name="Deer Herd",
        description="A herd of deer grazing peacefully.",
        alignment=PartyAlignment.NEUTRAL,
        behavior=PartyBehavior.WANDER,
        speed=1.4,
        sight_range=8,
        can_attack=False,
        can_be_attacked=True,
        combat_strength=1,
        color=(205, 133, 63),  # Tan
        icon="D",
        spawn_weight=1.5,
        min_level=1,
        max_level=35,  # Early wilderness; less common later
        avoids_poi_types=["town", "village"],
        is_prey=True,
        # No battle_unit_template - they flee rather than fight
    )
)

BIRD_FLOCK = register_party_type(
    PartyType(
        id="bird",
        name="Bird Flock",
        description="A flock of birds flying overhead.",
        alignment=PartyAlignment.NEUTRAL,
        behavior=PartyBehavior.WANDER,
        speed=1.6,
        sight_range=10,
        can_attack=False,
        can_be_attacked=False,  # Too fast to catch
        combat_strength=1,
        color=(255, 255, 255),  # White
        icon="b",
        spawn_weight=2.0,
        # No battle_unit_template - they don't fight
    )
)

RABBIT_HERD = register_party_type(
    PartyType(
        id="rabbit",
        name="Rabbit Warren",
        description="A group of rabbits foraging in the grass.",
        alignment=PartyAlignment.NEUTRAL,
        behavior=PartyBehavior.WANDER,
        speed=1.5,
        sight_range=6,
        can_attack=False,
        can_be_attacked=True,
        combat_strength=1,
        color=(240, 220, 180),  # Light tan
        icon="r",
        spawn_weight=2.0,
        min_level=1,
        max_level=30,
        avoids_poi_types=["town", "village"],
        is_prey=True,
    )
)

FOX_PACK = register_party_type(
    PartyType(
        id="fox",
        name="Fox Pack",
        description="A fox or small pack hunting small game.",
        alignment=PartyAlignment.NEUTRAL,
        enemy_types={"deer", "rabbit"},
        behavior=PartyBehavior.HUNT,
        speed=1.4,
        sight_range=8,
        can_attack=True,
        can_be_attacked=True,
        combat_strength=1,
        color=(220, 120, 60),  # Rust/orange
        icon="f",
        spawn_weight=1.2,
        avoids_poi_types=["town", "village"],
        battle_unit_template="wolf",  # Use wolf as stand-in for fox
        can_join_battle=True,
        is_natural_creature=True,
    )
)

# More Enemy Variations
BANDIT_ROGUE = register_party_type(
    PartyType(
        id="bandit_rogue",
        name="Bandit Rogue",
        description="A skilled rogue leading a small bandit group.",
        alignment=PartyAlignment.HOSTILE,
        behavior=PartyBehavior.WANDER,
        speed=1.2,
        sight_range=7,
        can_attack=True,
        can_be_attacked=True,
        combat_strength=3,
        color=(150, 0, 0),  # Dark red
        icon="R",
        spawn_weight=1.5,
        avoids_poi_types=["town"],
        faction_id="bandit_confederacy",
        battle_unit_template="bandit_cutthroat",
        can_join_battle=True,
    )
)

MONSTER_BRUTE = register_party_type(
    PartyType(
        id="monster_brute",
        name="Monster Brute",
        description="A large, powerful monster leading a pack.",
        alignment=PartyAlignment.HOSTILE,
        behavior=PartyBehavior.HUNT,
        speed=1.1,
        sight_range=9,
        can_attack=True,
        can_be_attacked=True,
        combat_strength=4,
        color=(100, 0, 100),  # Dark purple
        icon="M",
        spawn_weight=1.0,
        avoids_poi_types=["town", "village"],
        battle_unit_template="orc_raider",
        can_join_battle=True,
    )
)

SKELETON_WARBAND = register_party_type(
    PartyType(
        id="skeleton",
        name="Skeleton Warband",
        description="Undead skeletons roaming the land.",
        alignment=PartyAlignment.HOSTILE,
        behavior=PartyBehavior.WANDER,
        speed=0.9,
        sight_range=5,
        can_attack=True,
        can_be_attacked=True,
        combat_strength=2,
        color=(200, 200, 200),  # Gray-white
        icon="S",
        spawn_weight=1.2,
        avoids_poi_types=["town", "village"],
        battle_unit_template="skeleton_warrior",  # Use skeleton_warrior for warband
        can_join_battle=True,
    )
)

# More Ally Variations
KNIGHT_PATROL = register_party_type(
    PartyType(
        id="knight",
        name="Knight Patrol",
        description="Elite knights on patrol.",
        alignment=PartyAlignment.FRIENDLY,
        behavior=PartyBehavior.PATROL,
        speed=1.1,
        sight_range=8,
        can_attack=True,
        can_be_attacked=False,
        combat_strength=4,
        color=(192, 192, 192),  # Silver
        icon="K",
        spawn_weight=0.8,
        preferred_poi_types=["town"],
        faction_id="kingdom_aetheria",
        battle_unit_template="dread_knight",
        can_join_battle=True,
    )
)

MERCENARY_COMPANY = register_party_type(
    PartyType(
        id="mercenary",
        name="Mercenary Company",
        description="A company of professional mercenaries.",
        alignment=PartyAlignment.NEUTRAL,
        behavior=PartyBehavior.TRAVEL,
        speed=1.0,
        sight_range=7,
        can_attack=True,
        can_be_attacked=True,
        combat_strength=4,
        color=(128, 128, 128),  # Gray
        icon="M",
        spawn_weight=0.6,
        preferred_poi_types=["town"],
        faction_id="free_cities",
        battle_unit_template="bandit_cutthroat",
        can_join_battle=True,
    )
)

# Set up relationships
GUARD_PATROL.enemy_types = {"bandit", "monster", "wolf", "cultist", "orc", "goblin", "bandit_rogue", "monster_brute", "skeleton", "bear"}
GUARD_PATROL.ally_types = {"merchant", "villager", "adventurer", "ranger", "trader", "scout", "pilgrim", "knight"}

MERCHANT_PARTY.enemy_types = {"bandit", "monster", "wolf", "cultist", "orc", "goblin", "bandit_rogue", "monster_brute", "skeleton", "bear"}
MERCHANT_PARTY.ally_types = {"guard", "villager", "ranger", "knight"}

VILLAGER_PARTY.enemy_types = {"bandit", "monster", "wolf", "cultist", "orc", "goblin", "bandit_rogue", "monster_brute", "skeleton", "bear"}
VILLAGER_PARTY.ally_types = {"guard", "merchant", "ranger", "trader", "pilgrim", "knight"}

RANGER_PATROL.enemy_types = {"bandit", "monster", "wolf", "fox", "cultist", "orc", "goblin", "bandit_rogue", "monster_brute", "skeleton", "bear"}
RANGER_PATROL.ally_types = {"guard", "merchant", "villager", "adventurer", "scout", "knight"}

KNIGHT_PATROL.enemy_types = {"bandit", "monster", "wolf", "cultist", "orc", "goblin", "bandit_rogue", "monster_brute", "skeleton"}
KNIGHT_PATROL.ally_types = {"guard", "merchant", "villager", "ranger", "adventurer", "scout", "pilgrim"}

BANDIT_PARTY.enemy_types = {"guard", "merchant", "villager", "ranger", "trader", "noble", "knight"}
BANDIT_ROGUE.enemy_types = {"guard", "merchant", "villager", "ranger", "trader", "noble", "knight"}

MONSTER_PACK.enemy_types = {"guard", "merchant", "villager", "ranger", "trader", "knight"}
MONSTER_BRUTE.enemy_types = {"guard", "merchant", "villager", "ranger", "trader", "knight"}

WOLF_PACK.enemy_types = {"merchant", "villager", "pilgrim", "deer", "rabbit"}
BEAR_PACK.enemy_types = {"merchant", "villager", "pilgrim", "deer", "rabbit"}
FOX_PACK.enemy_types = {"deer", "rabbit"}

CULTIST_GATHERING.enemy_types = {"guard", "ranger", "adventurer", "scout", "knight"}
ORC_RAIDING_PARTY.enemy_types = {"merchant", "villager", "guard", "ranger", "trader", "noble", "knight"}
GOBLIN_WARBAND.enemy_types = {"merchant", "villager", "guard", "ranger", "knight"}
SKELETON_WARBAND.enemy_types = {"guard", "merchant", "villager", "ranger", "trader", "knight"}

TRADER_CARAVAN.enemy_types = {"bandit", "monster", "orc", "goblin", "bandit_rogue", "monster_brute", "skeleton", "bear"}
NOBLE_ENTOURAGE.enemy_types = {"bandit", "orc", "goblin", "bandit_rogue"}
SCOUT_PARTY.enemy_types = {"cultist", "orc", "goblin", "skeleton"}
PILGRIM_GROUP.enemy_types = {"bandit", "monster", "wolf", "orc", "goblin", "bandit_rogue", "monster_brute", "skeleton", "bear"}

MERCENARY_COMPANY.enemy_types = {"bandit", "orc", "goblin", "bandit_rogue", "skeleton"}
MERCENARY_COMPANY.ally_types = {"guard", "knight", "ranger"}

# More Enemy Variations - Humanoid Types
THIEF_GANG = register_party_type(
    PartyType(
        id="thief",
        name="Thief Gang",
        description="A group of thieves and pickpockets.",
        alignment=PartyAlignment.HOSTILE,
        behavior=PartyBehavior.WANDER,
        speed=1.3,
        sight_range=7,
        can_attack=True,
        can_be_attacked=True,
        combat_strength=2,
        color=(100, 50, 0),  # Brown
        icon="T",
        spawn_weight=1.8,
        avoids_poi_types=["town"],  # Avoid guards
        faction_id="bandit_confederacy",
        battle_unit_template="bandit_cutthroat",
        can_join_battle=True,
    )
)

ASSASSIN_CREW = register_party_type(
    PartyType(
        id="assassin",
        name="Assassin Crew",
        description="A deadly group of assassins.",
        alignment=PartyAlignment.HOSTILE,
        behavior=PartyBehavior.HUNT,
        speed=1.4,
        sight_range=9,
        can_attack=True,
        can_be_attacked=True,
        combat_strength=4,
        color=(50, 0, 0),  # Dark red
        icon="A",
        spawn_weight=0.8,
        avoids_poi_types=["town", "village"],
        faction_id="bandit_confederacy",
        battle_unit_template="shadow_stalker",
        can_join_battle=True,
    )
)

RAIDER_BAND = register_party_type(
    PartyType(
        id="raider",
        name="Raider Band",
        description="A band of ruthless raiders.",
        alignment=PartyAlignment.HOSTILE,
        behavior=PartyBehavior.HUNT,
        speed=1.2,
        sight_range=8,
        can_attack=True,
        can_be_attacked=True,
        combat_strength=3,
        color=(139, 0, 0),  # Dark red
        icon="R",
        spawn_weight=1.5,
        avoids_poi_types=["town"],
        faction_id="bandit_confederacy",
        battle_unit_template="orc_raider",
        can_join_battle=True,
    )
)

# More Undead Types
GHOUL_PACK = register_party_type(
    PartyType(
        id="ghoul",
        name="Ghoul Pack",
        description="A pack of hungry ghouls.",
        alignment=PartyAlignment.HOSTILE,
        behavior=PartyBehavior.HUNT,
        speed=1.1,
        sight_range=7,
        can_attack=True,
        can_be_attacked=True,
        combat_strength=3,
        color=(100, 100, 100),  # Gray
        icon="G",
        spawn_weight=1.2,
        avoids_poi_types=["town", "village"],
        battle_unit_template="ghoul_ripper",
        can_join_battle=True,
    )
)

ZOMBIE_HORDE = register_party_type(
    PartyType(
        id="zombie",
        name="Zombie Horde",
        description="A shambling horde of zombies.",
        alignment=PartyAlignment.HOSTILE,
        behavior=PartyBehavior.WANDER,
        speed=0.7,
        sight_range=4,
        can_attack=True,
        can_be_attacked=True,
        combat_strength=2,
        color=(50, 100, 50),  # Sickly green
        icon="Z",
        spawn_weight=1.5,
        avoids_poi_types=["town", "village"],
        battle_unit_template="skeleton_warrior",  # Use skeleton_warrior for zombies (similar undead)
        can_join_battle=True,
    )
)

WRAITH_PACK = register_party_type(
    PartyType(
        id="wraith",
        name="Wraith Pack",
        description="Ethereal wraiths haunting the land.",
        alignment=PartyAlignment.HOSTILE,
        behavior=PartyBehavior.WANDER,
        speed=1.3,
        sight_range=8,
        can_attack=True,
        can_be_attacked=True,
        combat_strength=3,
        color=(150, 150, 200),  # Pale blue
        icon="W",
        spawn_weight=1.0,
        avoids_poi_types=["town", "village"],
        battle_unit_template="wraith",  # Use wraith archetype
        can_join_battle=True,
    )
)

# More Magical/Arcane Enemies
MAGE_CABAL = register_party_type(
    PartyType(
        id="mage",
        name="Mage Cabal",
        description="A group of dark mages.",
        alignment=PartyAlignment.HOSTILE,
        behavior=PartyBehavior.WANDER,
        speed=0.9,
        sight_range=8,
        can_attack=True,
        can_be_attacked=True,
        combat_strength=3,
        color=(75, 0, 130),  # Indigo
        icon="M",
        spawn_weight=1.0,
        avoids_poi_types=["town", "village"],
        faction_id="shadow_cult",
        battle_unit_template="dark_adept",
        can_join_battle=True,
    )
)

WARLOCK_COVEN = register_party_type(
    PartyType(
        id="warlock",
        name="Warlock Coven",
        description="A coven of powerful warlocks.",
        alignment=PartyAlignment.HOSTILE,
        behavior=PartyBehavior.WANDER,
        speed=0.8,
        sight_range=9,
        can_attack=True,
        can_be_attacked=True,
        combat_strength=4,
        color=(50, 0, 50),  # Dark purple
        icon="W",
        spawn_weight=0.7,
        avoids_poi_types=["town", "village"],
        faction_id="shadow_cult",
        battle_unit_template="cultist_harbinger",
        can_join_battle=True,
    )
)

NECROMANCER_CULT = register_party_type(
    PartyType(
        id="necromancer",
        name="Necromancer Cult",
        description="A cult of necromancers raising the dead.",
        alignment=PartyAlignment.HOSTILE,
        behavior=PartyBehavior.WANDER,
        speed=0.9,
        sight_range=7,
        can_attack=True,
        can_be_attacked=True,
        combat_strength=4,
        color=(0, 50, 0),  # Dark green
        icon="N",
        spawn_weight=0.8,
        avoids_poi_types=["town", "village"],
        faction_id="shadow_cult",
        battle_unit_template="necromancer",
        can_join_battle=True,
    )
)

# More Beast Types
GIANT_SPIDER = register_party_type(
    PartyType(
        id="spider",
        name="Giant Spider",
        description="A large spider with its brood.",
        alignment=PartyAlignment.HOSTILE,
        behavior=PartyBehavior.WANDER,
        speed=1.2,
        sight_range=6,
        can_attack=True,
        can_be_attacked=True,
        combat_strength=2,
        color=(100, 50, 0),  # Brown
        icon="S",
        spawn_weight=1.5,
        avoids_poi_types=["town", "village"],
        battle_unit_template="spider_scout",  # Use spider archetype
        can_join_battle=True,
        is_natural_creature=True,
    )
)

BOAR_HERD = register_party_type(
    PartyType(
        id="boar",
        name="Boar Herd",
        description="A herd of aggressive wild boars.",
        alignment=PartyAlignment.HOSTILE,
        behavior=PartyBehavior.WANDER,
        speed=1.1,
        sight_range=5,
        can_attack=True,
        can_be_attacked=True,
        combat_strength=2,
        color=(139, 69, 19),  # Brown
        icon="B",
        spawn_weight=1.8,
        avoids_poi_types=["town", "village"],
        battle_unit_template="wild_boar",  # Use wild_boar archetype
        can_join_battle=True,
        is_natural_creature=True,
    )
)

DIRE_WOLF = register_party_type(
    PartyType(
        id="dire_wolf",
        name="Dire Wolf Pack",
        description="A pack of massive dire wolves.",
        alignment=PartyAlignment.HOSTILE,
        behavior=PartyBehavior.HUNT,
        speed=1.6,
        sight_range=10,
        can_attack=True,
        can_be_attacked=True,
        combat_strength=3,
        color=(64, 64, 64),  # Dark gray
        icon="D",
        spawn_weight=1.2,
        avoids_poi_types=["town", "village"],
        battle_unit_template="dire_wolf",  # Use dire_wolf archetype
        can_join_battle=True,
        is_natural_creature=True,
    )
)

# More Monstrous Types
TROLL_BAND = register_party_type(
    PartyType(
        id="troll",
        name="Troll Band",
        description="A band of brutish trolls.",
        alignment=PartyAlignment.HOSTILE,
        behavior=PartyBehavior.WANDER,
        speed=0.9,
        sight_range=6,
        can_attack=True,
        can_be_attacked=True,
        combat_strength=4,
        color=(0, 100, 0),  # Green
        icon="T",
        spawn_weight=1.0,
        min_level=8,  # Mid-game; not seen at very low level
        avoids_poi_types=["town", "village"],
        battle_unit_template="troll_berserker",  # Use troll_berserker archetype
        can_join_battle=True,
    )
)

OGRE_WARBAND = register_party_type(
    PartyType(
        id="ogre",
        name="Ogre Warband",
        description="A warband of massive ogres.",
        alignment=PartyAlignment.HOSTILE,
        behavior=PartyBehavior.HUNT,
        speed=1.0,
        sight_range=7,
        can_attack=True,
        can_be_attacked=True,
        combat_strength=4,
        color=(139, 90, 43),  # Brown
        icon="O",
        spawn_weight=0.9,
        min_level=10,  # Mid/late; stronger than trolls
        avoids_poi_types=["town"],
        battle_unit_template="cave_troll",  # Use cave_troll for ogres (similar large brutes)
        can_join_battle=True,
    )
)

DEMON_PACK = register_party_type(
    PartyType(
        id="demon",
        name="Demon Pack",
        description="A pack of demons from the void.",
        alignment=PartyAlignment.HOSTILE,
        behavior=PartyBehavior.HUNT,
        speed=1.3,
        sight_range=9,
        can_attack=True,
        can_be_attacked=True,
        combat_strength=5,
        color=(150, 0, 150),  # Purple
        icon="D",
        spawn_weight=0.5,
        min_level=15,  # Late-game threat; only appear as player progresses
        max_level=100,
        avoids_poi_types=["town", "village"],
        faction_id="shadow_cult",
        battle_unit_template="voidspawn_mauler",
        can_join_battle=True,
    )
)

# More Specialized Enemy Types
RAT_SWARM = register_party_type(
    PartyType(
        id="rat_swarm",
        name="Rat Swarm",
        description="A swarm of dire rats.",
        alignment=PartyAlignment.HOSTILE,
        behavior=PartyBehavior.WANDER,
        speed=1.0,
        sight_range=4,
        can_attack=True,
        can_be_attacked=True,
        combat_strength=1,
        color=(80, 80, 80),  # Gray
        icon="r",
        spawn_weight=2.5,
        min_level=1,
        max_level=25,  # Early swarm; taper off later
        avoids_poi_types=["town", "village"],
        battle_unit_template="dire_rat",
        can_join_battle=True,
    )
)

GOBLIN_SHAMAN_CULT = register_party_type(
    PartyType(
        id="goblin_shaman",
        name="Goblin Shaman Cult",
        description="Goblins led by a shaman.",
        alignment=PartyAlignment.HOSTILE,
        behavior=PartyBehavior.WANDER,
        speed=1.0,
        sight_range=6,
        can_attack=True,
        can_be_attacked=True,
        combat_strength=2,
        color=(0, 150, 0),  # Green
        icon="g",
        spawn_weight=1.5,
        avoids_poi_types=["town"],
        faction_id="bandit_confederacy",
        battle_unit_template="goblin_shaman",
        can_join_battle=True,
    )
)

# Update relationships for all new enemy types
THIEF_GANG.enemy_types = {"guard", "merchant", "villager", "ranger", "trader", "noble", "knight"}
ASSASSIN_CREW.enemy_types = {"guard", "merchant", "villager", "ranger", "trader", "noble", "knight", "adventurer"}
RAIDER_BAND.enemy_types = {"guard", "merchant", "villager", "ranger", "trader", "noble", "knight"}

GHOUL_PACK.enemy_types = {"guard", "merchant", "villager", "ranger", "trader", "knight"}
ZOMBIE_HORDE.enemy_types = {"guard", "merchant", "villager", "ranger", "trader", "knight"}
WRAITH_PACK.enemy_types = {"guard", "merchant", "villager", "ranger", "trader", "knight"}

MAGE_CABAL.enemy_types = {"guard", "ranger", "adventurer", "scout", "knight"}
WARLOCK_COVEN.enemy_types = {"guard", "ranger", "adventurer", "scout", "knight"}
NECROMANCER_CULT.enemy_types = {"guard", "ranger", "adventurer", "scout", "knight"}

GIANT_SPIDER.enemy_types = {"merchant", "villager", "pilgrim", "deer", "rabbit"}
BOAR_HERD.enemy_types = {"merchant", "villager", "pilgrim", "deer", "rabbit"}
DIRE_WOLF.enemy_types = {"merchant", "villager", "pilgrim", "deer", "rabbit"}

TROLL_BAND.enemy_types = {"merchant", "villager", "guard", "ranger", "trader", "knight"}
OGRE_WARBAND.enemy_types = {"merchant", "villager", "guard", "ranger", "trader", "noble", "knight"}
DEMON_PACK.enemy_types = {"guard", "merchant", "villager", "ranger", "trader", "knight", "adventurer"}

RAT_SWARM.enemy_types = {"merchant", "villager", "pilgrim"}
GOBLIN_SHAMAN_CULT.enemy_types = {"merchant", "villager", "guard", "ranger"}

# Update existing party enemy lists to include new types
GUARD_PATROL.enemy_types.update({
    "thief", "assassin", "raider", "ghoul", "zombie", "wraith", "mage", "warlock", "necromancer",
    "spider", "boar", "dire_wolf", "fox", "troll", "ogre", "demon", "rat_swarm", "goblin_shaman"
})
MERCHANT_PARTY.enemy_types.update({
    "thief", "assassin", "raider", "ghoul", "zombie", "wraith", "spider", "boar", "dire_wolf",
    "troll", "ogre", "demon", "rat_swarm", "goblin_shaman"
})
VILLAGER_PARTY.enemy_types.update({
    "thief", "assassin", "raider", "ghoul", "zombie", "wraith", "spider", "boar", "dire_wolf",
    "troll", "ogre", "demon", "rat_swarm", "goblin_shaman"
})
RANGER_PATROL.enemy_types.update({
    "thief", "assassin", "raider", "ghoul", "zombie", "wraith", "mage", "warlock", "necromancer",
    "spider", "boar", "dire_wolf", "troll", "ogre", "demon", "rat_swarm", "goblin_shaman"
})
KNIGHT_PATROL.enemy_types.update({
    "thief", "assassin", "raider", "ghoul", "zombie", "wraith", "mage", "warlock", "necromancer",
    "troll", "ogre", "demon", "goblin_shaman"
})

# Spawn categories for modular spawn pools (wildlife / humanoid / undead)
WILDLIFE_TYPES = {
    WOLF_PACK, BEAR_PACK, DEER_HERD, BIRD_FLOCK, RABBIT_HERD, FOX_PACK,
    GIANT_SPIDER, BOAR_HERD, DIRE_WOLF, RAT_SWARM,
}
UNDEAD_TYPES = {
    SKELETON_WARBAND, GHOUL_PACK, ZOMBIE_HORDE, WRAITH_PACK, NECROMANCER_CULT,
}
for pt in WILDLIFE_TYPES:
    pt.spawn_category = SpawnCategory.WILDLIFE
for pt in UNDEAD_TYPES:
    pt.spawn_category = SpawnCategory.UNDEAD
# All others remain HUMANOID (set explicitly so ALL is reserved for cross-pool types)
HUMANOID_TYPES = {
    MERCHANT_PARTY, VILLAGER_PARTY, GUARD_PATROL, BANDIT_PARTY, MONSTER_PACK,
    ADVENTURER_PARTY, NOBLE_ENTOURAGE, RANGER_PATROL, CULTIST_GATHERING,
    ORC_RAIDING_PARTY, TRADER_CARAVAN, SCOUT_PARTY, GOBLIN_WARBAND,
    PILGRIM_GROUP, BANDIT_ROGUE, MONSTER_BRUTE, KNIGHT_PATROL, MERCENARY_COMPANY,
    THIEF_GANG, ASSASSIN_CREW, RAIDER_BAND, MAGE_CABAL, WARLOCK_COVEN,
    TROLL_BAND, OGRE_WARBAND, DEMON_PACK, GOBLIN_SHAMAN_CULT,
}
for pt in HUMANOID_TYPES:
    pt.spawn_category = SpawnCategory.HUMANOID
