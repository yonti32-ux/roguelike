"""
Utility functions for the enemy system.

Provides helper functions for querying, analyzing, and working with enemy data.
"""

from typing import List, Dict, Optional, Tuple
from .types import EnemyArchetype, EnemyPackTemplate
from .registry import ENEMY_ARCHETYPES, ENEMY_PACKS, get_archetype, get_pack


def get_archetype_count() -> int:
    """Get the total number of registered enemy archetypes."""
    return len(ENEMY_ARCHETYPES)


def get_pack_count() -> int:
    """Get the total number of registered enemy packs."""
    return len(ENEMY_PACKS)


def list_all_archetype_ids() -> List[str]:
    """Get a list of all registered archetype IDs."""
    return sorted(ENEMY_ARCHETYPES.keys())


def list_all_pack_ids() -> List[str]:
    """Get a list of all registered pack IDs."""
    return sorted(ENEMY_PACKS.keys())


def get_archetypes_by_role(role: str) -> List[EnemyArchetype]:
    """Get all archetypes with a specific role."""
    return [arch for arch in ENEMY_ARCHETYPES.values() if arch.role == role]


def get_archetypes_by_tier(tier: int) -> List[EnemyArchetype]:
    """Get all archetypes with a specific tier."""
    return [arch for arch in ENEMY_ARCHETYPES.values() if arch.tier == tier]


def get_archetypes_by_difficulty_range(min_difficulty: int, max_difficulty: int) -> List[EnemyArchetype]:
    """Get all archetypes within a difficulty range."""
    return [
        arch for arch in ENEMY_ARCHETYPES.values()
        if min_difficulty <= arch.difficulty_level <= max_difficulty
    ]


def get_packs_by_tier(tier: int) -> List[EnemyPackTemplate]:
    """Get all packs with a specific tier."""
    return [pack for pack in ENEMY_PACKS.values() if pack.tier == tier]


def get_packs_by_room_tag(room_tag: str) -> List[EnemyPackTemplate]:
    """Get all packs that prefer a specific room tag."""
    return [pack for pack in ENEMY_PACKS.values() if pack.preferred_room_tag == room_tag]


def get_archetype_stats_summary(arch_id: str) -> Dict[str, any]:
    """
    Get a summary of an archetype's stats at a given floor.
    
    Args:
        arch_id: The archetype ID
    
    Returns:
        Dict with summary information
    """
    try:
        arch = get_archetype(arch_id)
        return {
            "id": arch.id,
            "name": arch.name,
            "role": arch.role,
            "tier": arch.tier,
            "difficulty_level": arch.difficulty_level,
            "spawn_range": (arch.spawn_min_floor, arch.spawn_max_floor),
            "tags": arch.tags,
            "skill_count": len(arch.skill_ids),
            "base_stats": {
                "hp": arch.base_hp,
                "attack": arch.base_attack,
                "defense": arch.base_defense,
                "xp": arch.base_xp,
            },
            "scaling": {
                "hp_per_floor": arch.hp_per_floor,
                "atk_per_floor": arch.atk_per_floor,
                "def_per_floor": arch.def_per_floor,
            },
        }
    except KeyError:
        return {"error": f"Archetype '{arch_id}' not found"}


def get_pack_summary(pack_id: str) -> Dict[str, any]:
    """
    Get a summary of a pack template.
    
    Args:
        pack_id: The pack ID
    
    Returns:
        Dict with summary information
    """
    try:
        pack = get_pack(pack_id)
        member_archetypes = []
        for arch_id in pack.member_arch_ids:
            try:
                arch = get_archetype(arch_id)
                member_archetypes.append({
                    "id": arch.id,
                    "name": arch.name,
                    "role": arch.role,
                })
            except KeyError:
                member_archetypes.append({"id": arch_id, "error": "not found"})
        
        return {
            "id": pack.id,
            "name": pack.name,
            "tier": pack.tier,
            "member_count": len(pack.member_arch_ids),
            "members": member_archetypes,
            "preferred_room_tag": pack.preferred_room_tag,
            "weight": pack.weight,
        }
    except KeyError:
        return {"error": f"Pack '{pack_id}' not found"}


def find_archetypes_with_tag(tag: str) -> List[EnemyArchetype]:
    """Find all archetypes that have a specific tag."""
    return [arch for arch in ENEMY_ARCHETYPES.values() if tag in arch.tags]


def find_archetypes_with_skill(skill_id: str) -> List[EnemyArchetype]:
    """Find all archetypes that have a specific skill."""
    return [arch for arch in ENEMY_ARCHETYPES.values() if skill_id in arch.skill_ids]


def get_difficulty_distribution() -> Dict[str, int]:
    """
    Get a distribution of enemies by difficulty level ranges.
    
    Returns:
        Dict with counts for each difficulty range
    """
    distribution = {
        "very_easy (1-20)": 0,
        "easy (21-40)": 0,
        "medium (41-60)": 0,
        "hard (61-80)": 0,
        "very_hard (81-100)": 0,
        "extreme (100+)": 0,
    }
    
    for arch in ENEMY_ARCHETYPES.values():
        diff = arch.difficulty_level
        if diff <= 20:
            distribution["very_easy (1-20)"] += 1
        elif diff <= 40:
            distribution["easy (21-40)"] += 1
        elif diff <= 60:
            distribution["medium (41-60)"] += 1
        elif diff <= 80:
            distribution["hard (61-80)"] += 1
        elif diff <= 100:
            distribution["very_hard (81-100)"] += 1
        else:
            distribution["extreme (100+)"] += 1
    
    return distribution


def get_role_distribution() -> Dict[str, int]:
    """Get a count of enemies by role."""
    distribution: Dict[str, int] = {}
    for arch in ENEMY_ARCHETYPES.values():
        role = arch.role
        distribution[role] = distribution.get(role, 0) + 1
    return distribution


def validate_archetype(arch_id: str) -> Tuple[bool, List[str]]:
    """
    Validate an archetype for common issues.
    
    Args:
        arch_id: The archetype ID to validate
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    try:
        arch = get_archetype(arch_id)
        
        # Check for required fields
        if not arch.name:
            errors.append("Missing name")
        if arch.base_hp <= 0:
            errors.append("base_hp must be > 0")
        if arch.base_attack <= 0:
            errors.append("base_attack must be > 0")
        if arch.difficulty_level <= 0:
            errors.append("difficulty_level must be > 0")
        
        # Check spawn range validity
        if arch.spawn_min_floor is not None and arch.spawn_max_floor is not None:
            if arch.spawn_min_floor > arch.spawn_max_floor:
                errors.append("spawn_min_floor > spawn_max_floor")
        
        # Check for invalid skill references (would need skill system access)
        # This is a placeholder for future validation
        
    except KeyError:
        errors.append(f"Archetype '{arch_id}' not found")
    
    return len(errors) == 0, errors


def validate_pack(pack_id: str) -> Tuple[bool, List[str]]:
    """
    Validate a pack template for common issues.
    
    Args:
        pack_id: The pack ID to validate
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    try:
        pack = get_pack(pack_id)
        
        # Check for required fields
        if not pack.member_arch_ids:
            errors.append("Pack has no members")
        
        # Check that all member archetypes exist
        for arch_id in pack.member_arch_ids:
            try:
                get_archetype(arch_id)
            except KeyError:
                errors.append(f"Member archetype '{arch_id}' not found")
        
        # Check tier consistency (optional validation)
        if pack.member_arch_ids:
            member_tiers = set()
            for arch_id in pack.member_arch_ids:
                try:
                    arch = get_archetype(arch_id)
                    member_tiers.add(arch.tier)
                except KeyError:
                    pass
            
            # Warn if pack has members from very different tiers
            if len(member_tiers) > 1:
                tier_range = max(member_tiers) - min(member_tiers)
                if tier_range > 1:
                    errors.append(f"Pack has members from different tiers: {member_tiers}")
        
    except KeyError:
        errors.append(f"Pack '{pack_id}' not found")
    
    return len(errors) == 0, errors


def get_archetype_at_floor(arch_id: str, floor_index: int) -> Dict[str, any]:
    """
    Get an archetype's stats scaled to a specific floor.
    
    Args:
        arch_id: The archetype ID
        floor_index: The floor to scale to
    
    Returns:
        Dict with scaled stats
    """
    from .scaling import compute_scaled_stats
    
    try:
        arch = get_archetype(arch_id)
        max_hp, attack, defense, xp, initiative = compute_scaled_stats(arch, floor_index)
        
        return {
            "archetype_id": arch_id,
            "floor": floor_index,
            "stats": {
                "max_hp": max_hp,
                "attack": attack,
                "defense": defense,
                "xp": xp,
                "initiative": initiative,
            },
            "skills": arch.skill_ids,
            "tags": arch.tags,
        }
    except KeyError:
        return {"error": f"Archetype '{arch_id}' not found"}
