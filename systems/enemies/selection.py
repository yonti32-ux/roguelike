"""
Enemy selection and choice functions.

Handles selecting appropriate enemies and packs for floors, player levels, etc.
"""

from typing import List, Optional, Tuple
import random

from .types import EnemyArchetype, EnemyPackTemplate
from .registry import ENEMY_ARCHETYPES, ENEMY_PACKS


def _tier_for_floor(floor_index: int) -> int:
    """Convert floor index to tier (1, 2, or 3)."""
    if floor_index <= 2:
        return 1
    elif floor_index <= 4:
        return 2
    else:
        return 3


def get_enemies_by_tag(tag: str) -> List[EnemyArchetype]:
    """
    Get all enemies with a specific tag.
    
    Args:
        tag: Tag to search for (e.g., "undead", "early_game", "caster")
    
    Returns:
        List of EnemyArchetype instances with the tag
    """
    return [arch for arch in ENEMY_ARCHETYPES.values() if tag in arch.tags]


def get_enemies_in_difficulty_range(min_level: int, max_level: int) -> List[EnemyArchetype]:
    """
    Get all enemies within a difficulty level range.
    
    Args:
        min_level: Minimum difficulty level (inclusive)
        max_level: Maximum difficulty level (inclusive)
    
    Returns:
        List of EnemyArchetype instances in the range
    """
    return [
        arch for arch in ENEMY_ARCHETYPES.values()
        if min_level <= arch.difficulty_level <= max_level
    ]


def get_enemies_for_floor_range(min_floor: int, max_floor: int) -> List[EnemyArchetype]:
    """
    Get all enemies that can spawn in a floor range.
    
    Args:
        min_floor: Minimum floor (inclusive)
        max_floor: Maximum floor (inclusive)
    
    Returns:
        List of EnemyArchetype instances that can spawn in this range
    """
    return [
        arch for arch in ENEMY_ARCHETYPES.values()
        if arch.spawn_min_floor <= max_floor
        and (arch.spawn_max_floor is None or arch.spawn_max_floor >= min_floor)
    ]


def floor_to_difficulty_range(floor_index: int, spread: int = 15) -> Tuple[int, int]:
    """
    Convert floor index to a difficulty level range.
    
    This can be used to find enemies appropriate for a given floor.
    
    Args:
        floor_index: Current floor
        spread: How wide the difficulty range should be (default 15)
    
    Returns:
        (min_level, max_level) tuple
    """
    # Linear scaling: floor 1 = level 10, floor 10 = level 100
    # Adjust formula as needed for your game's progression
    base_level = 10 + (floor_index - 1) * 9  # Roughly 10 per floor
    
    min_level = max(1, base_level - spread)
    max_level = min(100, base_level + spread)
    
    return (min_level, max_level)


def choose_archetype_for_player_level(
    player_level: int,
    preferred_tags: Optional[List[str]] = None,
    excluded_tags: Optional[List[str]] = None,
) -> EnemyArchetype:
    """
    Pick an enemy archetype appropriate for the player's level (for overworld spawning).
    
    Uses player_level as the "floor" for spawn range filtering, allowing higher-level
    enemies to appear in overworld as player progresses.
    
    Args:
        player_level: Current player level
        preferred_tags: Optional list of tags to prefer (e.g., ["undead", "beast"])
        excluded_tags: Optional list of tags to exclude
    
    Returns:
        EnemyArchetype appropriate for player level
    """
    # Filter by spawn range (treat player_level as floor)
    candidates = [
        arch for arch in ENEMY_ARCHETYPES.values()
        if arch.spawn_min_floor <= player_level
        and (arch.spawn_max_floor is None or arch.spawn_max_floor >= player_level)
    ]
    
    # Filter by preferred tags if provided
    if preferred_tags:
        preferred = [
            arch for arch in candidates
            if any(tag in arch.tags for tag in preferred_tags)
        ]
        if preferred:
            candidates = preferred
    
    # Filter by excluded tags if provided
    if excluded_tags:
        candidates = [
            arch for arch in candidates
            if not any(tag in arch.tags for tag in excluded_tags)
        ]
    
    # Fallback to tier system if no candidates
    if not candidates:
        tier = _tier_for_floor(player_level)
        candidates = [a for a in ENEMY_ARCHETYPES.values() if a.tier == tier]
    
    # Final fallback: use any archetype
    if not candidates:
        candidates = list(ENEMY_ARCHETYPES.values())
    
    if not candidates:
        raise RuntimeError("No enemy archetypes registered.")
    
    # Weight by spawn_weight
    weights = [arch.spawn_weight for arch in candidates]
    
    return random.choices(candidates, weights=weights, k=1)[0]


def choose_archetype_for_floor(
    floor_index: int,
    room_tag: Optional[str] = None,
) -> EnemyArchetype:
    """
    Pick an archetype for the given floor + room tag.
    
    Uses new difficulty system (spawn_min_floor, spawn_max_floor) with fallback to tier system.
    - New system: Filters by spawn range (spawn_min_floor <= floor <= spawn_max_floor)
    - Fallback: Uses tier system if no candidates found
    - room_tag nudges the weights but doesn't hard-lock anything.
    """
    # Try new system first: filter by spawn range
    candidates = [
        arch for arch in ENEMY_ARCHETYPES.values()
        if arch.spawn_min_floor <= floor_index
        and (arch.spawn_max_floor is None or arch.spawn_max_floor >= floor_index)
    ]
    
    # Fallback to tier system if no candidates found
    if not candidates:
        tier = _tier_for_floor(floor_index)
        candidates = [a for a in ENEMY_ARCHETYPES.values() if a.tier == tier]
    
    # Final fallback: use any archetype
    if not candidates:
        candidates = list(ENEMY_ARCHETYPES.values())

    if not candidates:
        raise RuntimeError("No enemy archetypes registered.")

    weights: List[float] = []
    for arch in candidates:
        # Start with spawn_weight (new system) or default to 1.0
        w = arch.spawn_weight

        # Lair rooms tend to have heavier hitters
        if room_tag == "lair" and arch.role in ("Brute", "Elite Brute"):
            w += 1.0

        # Event rooms lean a bit towards casters / cultists
        if room_tag == "event" and arch.role in ("Invoker", "Support"):
            w += 0.7
        
        # Tag-based bonuses (new system)
        if room_tag == "graveyard" and "undead" in arch.tags:
            w += 1.5
        if room_tag == "sanctum" and "holy" in arch.tags:
            w += 1.5
        if room_tag == "lair" and "beast" in arch.tags:
            w += 1.0

        weights.append(w)

    return random.choices(candidates, weights=weights, k=1)[0]


def choose_pack_for_floor(
    floor_index: int,
    room_tag: Optional[str] = None,
) -> EnemyPackTemplate:
    """
    Pick a *pack template* for the given floor + room tag.

    - Floor controls the pack tier (still uses tier for packs, but checks member spawn ranges).
    - room_tag nudges towards packs that prefer that tag.
    - If no packs are defined, falls back to a single-archetype pseudo-pack.
    """
    tier = _tier_for_floor(floor_index)

    # Filter packs by tier, but also check if pack members can spawn on this floor
    candidates = []
    for pack in ENEMY_PACKS.values():
        if pack.tier != tier:
            continue
        
        # Check if all pack members can spawn on this floor
        all_members_valid = True
        for arch_id in pack.member_arch_ids:
            if arch_id not in ENEMY_ARCHETYPES:
                all_members_valid = False
                break
            arch = ENEMY_ARCHETYPES[arch_id]
            if arch.spawn_min_floor > floor_index:
                all_members_valid = False
                break
            if arch.spawn_max_floor is not None and arch.spawn_max_floor < floor_index:
                all_members_valid = False
                break
        
        if all_members_valid:
            candidates.append(pack)

    # Fallback: if no packs found, create a pseudo-pack from a single archetype
    if not candidates:
        arch = choose_archetype_for_floor(floor_index, room_tag)
        return EnemyPackTemplate(
            id=f"_single_{arch.id}",
            name=arch.name,
            tier=arch.tier,
            member_arch_ids=[arch.id],
            preferred_room_tag=room_tag,
            weight=1.0,
        )

    weights: List[float] = []
    for pack in candidates:
        w = pack.weight
        
        # Boost weight if pack prefers this room tag
        if pack.preferred_room_tag == room_tag:
            w += 1.0
        
        weights.append(w)

    return random.choices(candidates, weights=weights, k=1)[0]
