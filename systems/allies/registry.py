"""
Ally registry system.

Manages the global registries of ally archetypes and pack templates.
"""

from typing import Dict, Optional
from .types import AllyArchetype, AllyPackTemplate


# Global registries
ALLY_ARCHETYPES: Dict[str, AllyArchetype] = {}
ALLY_PACKS: Dict[str, AllyPackTemplate] = {}


def register_archetype(arch: AllyArchetype) -> AllyArchetype:
    """Register an ally archetype."""
    ALLY_ARCHETYPES[arch.id] = arch
    return arch


def get_archetype(arch_id: str) -> AllyArchetype:
    """Get an ally archetype by ID."""
    return ALLY_ARCHETYPES[arch_id]


def get_archetype_for_party_type(party_type_id: str) -> Optional[AllyArchetype]:
    """Get an ally archetype that matches a party type."""
    for arch in ALLY_ARCHETYPES.values():
        if party_type_id in arch.party_type_ids:
            return arch
    return None


def register_pack(pack: AllyPackTemplate) -> AllyPackTemplate:
    """Register an ally pack template."""
    ALLY_PACKS[pack.id] = pack
    return pack


def get_pack(pack_id: str) -> AllyPackTemplate:
    """Get an ally pack template by ID."""
    return ALLY_PACKS[pack_id]


def get_packs_for_party_type(party_type_id: str) -> list[AllyPackTemplate]:
    """Get all ally pack templates that match a party type."""
    packs = []
    for pack in ALLY_PACKS.values():
        if party_type_id in pack.party_type_ids:
            packs.append(pack)
    return packs
