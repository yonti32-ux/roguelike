"""
Ally system for friendly units that join the player in battle.

Provides archetypes for different types of allies (guards, rangers, merchants, etc.)
similar to the enemy archetype system.
"""

from .registry import (
    register_archetype,
    get_archetype,
    get_archetype_for_party_type,
    register_pack,
    get_pack,
    get_packs_for_party_type,
    ALLY_ARCHETYPES,
    ALLY_PACKS,
)
from .types import AllyArchetype, AllyPackTemplate
from .definitions import register_all_ally_archetypes
from .definitions.packs import register_all_ally_packs

# Auto-register all ally archetypes and packs when module is imported
register_all_ally_archetypes()
register_all_ally_packs()

__all__ = [
    "register_archetype",
    "get_archetype",
    "get_archetype_for_party_type",
    "register_pack",
    "get_pack",
    "get_packs_for_party_type",
    "ALLY_ARCHETYPES",
    "ALLY_PACKS",
    "AllyArchetype",
    "AllyPackTemplate",
]
