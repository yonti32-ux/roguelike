"""
Validation and integrity checking for the enemy system.

Provides functions to validate that all registered enemies and packs are correct.
"""

from typing import List, Dict, Tuple
from .registry import ENEMY_ARCHETYPES, ENEMY_PACKS, get_archetype, get_pack
from .types import EnemyArchetype, EnemyPackTemplate


def validate_all_archetypes() -> Dict[str, List[str]]:
    """
    Validate all registered archetypes.
    
    Returns:
        Dict mapping archetype_id to list of errors (empty list if valid)
    """
    results = {}
    
    for arch_id, arch in ENEMY_ARCHETYPES.items():
        errors = []
        
        # Basic field validation
        if not arch.name or not arch.name.strip():
            errors.append("Missing or empty name")
        
        if arch.base_hp <= 0:
            errors.append(f"Invalid base_hp: {arch.base_hp} (must be > 0)")
        
        if arch.base_attack <= 0:
            errors.append(f"Invalid base_attack: {arch.base_attack} (must be > 0)")
        
        if arch.difficulty_level <= 0:
            errors.append(f"Invalid difficulty_level: {arch.difficulty_level} (must be > 0)")
        
        # Spawn range validation
        if arch.spawn_min_floor is not None and arch.spawn_max_floor is not None:
            if arch.spawn_min_floor < 1:
                errors.append(f"spawn_min_floor must be >= 1, got {arch.spawn_min_floor}")
            if arch.spawn_max_floor < arch.spawn_min_floor:
                errors.append(
                    f"spawn_max_floor ({arch.spawn_max_floor}) < spawn_min_floor ({arch.spawn_min_floor})"
                )
        
        # Scaling validation
        if arch.hp_per_floor < 0:
            errors.append(f"hp_per_floor cannot be negative: {arch.hp_per_floor}")
        if arch.atk_per_floor < 0:
            errors.append(f"atk_per_floor cannot be negative: {arch.atk_per_floor}")
        
        # Tag validation
        if not arch.tags:
            errors.append("No tags defined (recommended for filtering)")
        
        results[arch_id] = errors
    
    return results


def validate_all_packs() -> Dict[str, List[str]]:
    """
    Validate all registered packs.
    
    Returns:
        Dict mapping pack_id to list of errors (empty list if valid)
    """
    results = {}
    
    for pack_id, pack in ENEMY_PACKS.items():
        errors = []
        
        # Basic field validation
        if not pack.member_arch_ids:
            errors.append("Pack has no members")
        
        # Validate all member archetypes exist
        for arch_id in pack.member_arch_ids:
            if arch_id not in ENEMY_ARCHETYPES:
                errors.append(f"Member archetype '{arch_id}' not found in registry")
        
        # Weight validation
        if pack.weight <= 0:
            errors.append(f"Pack weight must be > 0, got {pack.weight}")
        
        # Tier consistency check (warning, not error)
        if pack.member_arch_ids:
            member_tiers = []
            for arch_id in pack.member_arch_ids:
                if arch_id in ENEMY_ARCHETYPES:
                    arch = ENEMY_ARCHETYPES[arch_id]
                    member_tiers.append(arch.tier)
            
            if member_tiers:
                tier_range = max(member_tiers) - min(member_tiers)
                if tier_range > 1:
                    errors.append(
                        f"Pack has members from different tiers: {set(member_tiers)} "
                        f"(may be intentional but worth reviewing)"
                    )
        
        results[pack_id] = errors
    
    return results


def check_for_orphaned_archetypes() -> List[str]:
    """
    Find archetypes that are never used in any pack.
    
    Returns:
        List of archetype IDs that are not in any pack
    """
    used_archetypes = set()
    
    for pack in ENEMY_PACKS.values():
        used_archetypes.update(pack.member_arch_ids)
    
    all_archetypes = set(ENEMY_ARCHETYPES.keys())
    orphaned = all_archetypes - used_archetypes
    
    return sorted(orphaned)


def check_for_missing_skills() -> Dict[str, List[str]]:
    """
    Check for archetypes that reference skills that might not exist.
    Note: This is a placeholder - would need access to skill system to fully validate.
    
    Returns:
        Dict mapping archetype_id to list of potentially missing skill IDs
    """
    # This would require integration with the skill system
    # For now, just return empty dict as placeholder
    return {}


def run_full_validation() -> Dict[str, any]:
    """
    Run all validation checks and return a comprehensive report.
    
    Returns:
        Dict with validation results
    """
    archetype_errors = validate_all_archetypes()
    pack_errors = validate_all_packs()
    orphaned = check_for_orphaned_archetypes()
    
    archetype_error_count = sum(len(errors) for errors in archetype_errors.values())
    pack_error_count = sum(len(errors) for errors in pack_errors.values())
    
    return {
        "archetypes": {
            "total": len(ENEMY_ARCHETYPES),
            "valid": len([a for a, e in archetype_errors.items() if not e]),
            "invalid": len([a for a, e in archetype_errors.items() if e]),
            "errors": archetype_errors,
            "error_count": archetype_error_count,
        },
        "packs": {
            "total": len(ENEMY_PACKS),
            "valid": len([p for p, e in pack_errors.items() if not e]),
            "invalid": len([p for p, e in pack_errors.items() if e]),
            "errors": pack_errors,
            "error_count": pack_error_count,
        },
        "orphaned_archetypes": {
            "count": len(orphaned),
            "ids": orphaned,
        },
        "overall_valid": archetype_error_count == 0 and pack_error_count == 0,
    }
