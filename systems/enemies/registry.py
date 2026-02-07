"""
Enemy registry system.

Manages the global registries of enemy archetypes and pack templates.
"""

from typing import Dict, List
from .types import EnemyArchetype, EnemyPackTemplate


# Global registries
ENEMY_ARCHETYPES: Dict[str, EnemyArchetype] = {}
ENEMY_PACKS: Dict[str, EnemyPackTemplate] = {}

# Mapping of room tags to special "unique" enemy archetype ids.
# These are used as rare spawns in matching room types.
UNIQUE_ROOM_ENEMIES: Dict[str, List[str]] = {
    "graveyard": ["grave_warden"],
    "sanctum": ["sanctum_guardian"],
    "lair": ["pit_champion"],
    "treasure": ["hoard_mimic"],
    "library": ["arcane_golem"],
    "armory": ["animated_armor"],
}


def register_archetype(arch: EnemyArchetype) -> EnemyArchetype:
    """Register an enemy archetype."""
    ENEMY_ARCHETYPES[arch.id] = arch
    return arch


def get_archetype(arch_id: str) -> EnemyArchetype:
    """Get an enemy archetype by ID."""
    return ENEMY_ARCHETYPES[arch_id]


def register_pack(pack: EnemyPackTemplate) -> EnemyPackTemplate:
    """Register an enemy pack template."""
    ENEMY_PACKS[pack.id] = pack
    return pack


def get_pack(pack_id: str) -> EnemyPackTemplate:
    """Get an enemy pack template by ID."""
    return ENEMY_PACKS[pack_id]
