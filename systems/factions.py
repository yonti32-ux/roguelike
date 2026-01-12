"""
Faction system.

Defines factions, their relationships, and faction-based logic.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set
from enum import Enum


class FactionAlignment(Enum):
    """Faction alignment."""
    GOOD = "good"
    NEUTRAL = "neutral"
    EVIL = "evil"


@dataclass
class Faction:
    """
    Represents a faction in the game world.
    
    Factions control POIs, have parties, and maintain relations with other factions.
    """
    id: str
    name: str
    description: str
    alignment: FactionAlignment
    
    # Visual representation
    color: Tuple[int, int, int]  # RGB color for map display
    
    # Relations with other factions (-100 to 100)
    # -100 = hostile, 0 = neutral, 100 = allied
    default_relations: Dict[str, int] = field(default_factory=dict)
    
    # POI types this faction typically controls
    home_poi_types: List[str] = field(default_factory=list)
    
    # Party types that belong to this faction
    default_party_types: List[str] = field(default_factory=list)
    
    # Spawn properties
    spawn_weight: float = 1.0  # Relative spawn probability for POIs/parties


# Registry of all factions
_FACTIONS: Dict[str, Faction] = {}


def register_faction(faction: Faction) -> Faction:
    """Register a faction."""
    if faction.id in _FACTIONS:
        raise ValueError(f"Faction already registered: {faction.id}")
    _FACTIONS[faction.id] = faction
    return faction


def get_faction(faction_id: str) -> Optional[Faction]:
    """Get a faction by ID."""
    return _FACTIONS.get(faction_id)


def all_factions() -> List[Faction]:
    """Get all registered factions."""
    return list(_FACTIONS.values())


# ============================================================================
# Predefined Factions
# ============================================================================

KINGDOM_OF_AETHERIA = register_faction(
    Faction(
        id="kingdom_aetheria",
        name="Kingdom of Aetheria",
        description="A noble kingdom that controls many towns and villages.",
        alignment=FactionAlignment.GOOD,
        color=(100, 150, 255),  # Royal blue
        home_poi_types=["town", "village", "castle"],
        default_party_types=["guard", "villager", "merchant", "noble"],
        spawn_weight=2.0,
    )
)

FREE_CITIES = register_faction(
    Faction(
        id="free_cities",
        name="Free Cities",
        description="Independent city-states that trade freely.",
        alignment=FactionAlignment.NEUTRAL,
        color=(200, 200, 200),  # Gray
        home_poi_types=["town", "village"],
        default_party_types=["merchant", "trader", "villager"],
        spawn_weight=1.5,
    )
)

SHADOW_CULT = register_faction(
    Faction(
        id="shadow_cult",
        name="Shadow Cult",
        description="A dark cult that seeks to spread chaos and darkness.",
        alignment=FactionAlignment.EVIL,
        color=(75, 0, 130),  # Indigo
        home_poi_types=["camp", "cult_sanctuary"],
        default_party_types=["cultist", "monster"],
        spawn_weight=1.0,
    )
)

WILD_TRIBES = register_faction(
    Faction(
        id="wild_tribes",
        name="Wild Tribes",
        description="Tribal groups that live in the wilderness.",
        alignment=FactionAlignment.NEUTRAL,
        color=(139, 69, 19),  # Brown
        home_poi_types=["camp", "village"],
        default_party_types=["scout", "ranger"],
        spawn_weight=1.2,
    )
)

BANDIT_CONFEDERACY = register_faction(
    Faction(
        id="bandit_confederacy",
        name="Bandit Confederacy",
        description="A loose alliance of bandit groups and raiders.",
        alignment=FactionAlignment.EVIL,
        color=(200, 0, 0),  # Red
        home_poi_types=["bandit_camp", "camp"],
        default_party_types=["bandit", "goblin", "orc"],
        spawn_weight=1.8,
    )
)

# Set up default relations
KINGDOM_OF_AETHERIA.default_relations = {
    "free_cities": 30,  # Friendly with free cities
    "wild_tribes": 10,  # Slightly positive
    "shadow_cult": -80,  # Very hostile
    "bandit_confederacy": -90,  # Very hostile
}

FREE_CITIES.default_relations = {
    "kingdom_aetheria": 30,
    "wild_tribes": 20,
    "shadow_cult": -50,
    "bandit_confederacy": -60,
}

SHADOW_CULT.default_relations = {
    "kingdom_aetheria": -80,
    "free_cities": -50,
    "wild_tribes": -40,
    "bandit_confederacy": 20,  # Somewhat friendly with bandits
}

WILD_TRIBES.default_relations = {
    "kingdom_aetheria": 10,
    "free_cities": 20,
    "shadow_cult": -40,
    "bandit_confederacy": -30,
}

BANDIT_CONFEDERACY.default_relations = {
    "kingdom_aetheria": -90,
    "free_cities": -60,
    "wild_tribes": -30,
    "shadow_cult": 20,
}

