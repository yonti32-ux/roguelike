"""
POI placement algorithms.

Handles the placement of POIs on the overworld according to configuration.
Uses registry pattern for extensible POI creation.
"""

import random
import math
from typing import List, Dict, Any

from ..overworld.map import OverworldMap
from ..overworld.config import OverworldConfig
from ..overworld.terrain import TERRAIN_WATER, get_terrain
from .base import PointOfInterest
from .registry import get_registry
from ..generation.config import load_generation_config
from systems.namegen import generate_dungeon_name, generate_town_name, generate_village_name
from .faction_placement import select_faction_for_poi

# Import types to ensure POI types are registered before use
# This ensures auto-registration happens even if placement is imported directly
from . import types  # noqa: F401


def place_pois(overworld: OverworldMap, config: OverworldConfig) -> List[PointOfInterest]:
    """
    Place POIs on the overworld according to configuration and placement rules.
    
    Uses spatial placement rules:
    - Towns are placed first (hubs)
    - Villages spawn near towns
    - Dungeons spawn further from towns/villages
    - Camps avoid towns/villages
    
    Args:
        overworld: The overworld map
        config: Configuration with POI settings
        
    Returns:
        List of placed POIs
    """
    gen_config = load_generation_config()  # Load generation settings
    pois: List[PointOfInterest] = []
    
    # Calculate target POI count
    world_area = overworld.width * overworld.height
    target_count = int(world_area * config.poi_density)
    
    # Cap maximum POIs to prevent performance issues (from config)
    max_pois = min(target_count, gen_config.poi.max_pois)
    
    # Distribute by type
    poi_type_counts = _distribute_poi_types(max_pois, config.poi_distribution)
    
    # Get placement order from rules (or use default)
    placement_rules = gen_config.poi.placement_rules
    placement_order = placement_rules.get("placement_order", ["town", "village", "dungeon", "camp"])
    
    # Place POIs in order (towns first, then villages near towns, etc.)
    poi_id_counter = 1
    failed_placements = 0
    max_failures = gen_config.poi.max_consecutive_failures
    
    # Place each type in the specified order
    for poi_type in placement_order:
        if poi_type not in poi_type_counts:
            continue
        
        count = poi_type_counts[poi_type]
        for _ in range(count):
            poi = _place_single_poi(
                overworld=overworld,
                poi_type=poi_type,
                poi_id=f"{poi_type}_{poi_id_counter}",
                config=config,
                existing_pois=pois,
                placement_rules=placement_rules,
                gen_config=gen_config,
            )
            
            if poi is not None:
                pois.append(poi)
                poi_id_counter += 1
                failed_placements = 0  # Reset failure counter on success
            else:
                failed_placements += 1
                if failed_placements >= max_failures:
                    # Too many failures, stop trying
                    print(f"Warning: Stopped placing {poi_type} POIs after {failed_placements} consecutive failures")
                    break
        
        if failed_placements >= max_failures:
            break
    
    print(f"Placed {len(pois)} POIs out of {max_pois} target")
    return pois


def _distribute_poi_types(total: int, distribution: dict[str, float]) -> dict[str, int]:
    """
    Distribute total POI count across types based on distribution ratios.
    
    Args:
        total: Total number of POIs to place
        distribution: Dict mapping POI type to ratio (should sum to ~1.0)
        
    Returns:
        Dict mapping POI type to count
    """
    result: dict[str, int] = {}
    remaining = total
    
    # Sort by ratio (descending) to handle rounding better
    sorted_types = sorted(distribution.items(), key=lambda x: x[1], reverse=True)
    
    for poi_type, ratio in sorted_types:
        count = int(total * ratio)
        result[poi_type] = count
        remaining -= count
    
    # Distribute any remainder to the first type
    if remaining > 0 and sorted_types:
        result[sorted_types[0][0]] += remaining
    
    return result


def _calculate_poi_level(poi_type: str, x: int, y: int, overworld: OverworldMap, existing_pois: List[PointOfInterest]) -> int:
    """
    Calculate the difficulty level for a POI based on its position and type.
    
    For now, uses random level 1-10, but could be enhanced to:
    - Scale with distance from spawn
    - Scale with existing POI levels nearby
    - Have different ranges for different POI types
    
    Args:
        poi_type: Type of POI
        x, y: Position of POI
        overworld: The overworld map
        existing_pois: Already placed POIs
        
    Returns:
        Difficulty level (1-10)
    """
    # Simple random level for now (1-10)
    # Could be enhanced to scale with distance from center or other factors
    return random.randint(1, 10)


def _place_single_poi(
    overworld: OverworldMap,
    poi_type: str,
    poi_id: str,
    config: OverworldConfig,
    existing_pois: List[PointOfInterest],
    placement_rules: dict = None,
    gen_config = None,
) -> PointOfInterest | None:
    """
    Attempt to place a single POI with spatial placement rules.
    
    Uses multiple strategies with progressively relaxed constraints:
    1. First pass: Full constraints and spatial rules
    2. Second pass: Relaxed minimum distance
    3. Third pass: Minimal constraints (just walkable and terrain)
    
    Args:
        overworld: The overworld map
        poi_type: Type of POI to place
        poi_id: Unique identifier
        config: Configuration
        existing_pois: Already placed POIs (for distance checking)
        placement_rules: Placement rules from config
        
    Returns:
        Placed POI, or None if placement failed
    """
    if gen_config is None:
        gen_config = load_generation_config()
    max_attempts = gen_config.poi.max_placement_attempts
    
    if placement_rules is None:
        placement_rules = {}
    
    spatial_rules = placement_rules.get("spatial_rules", {}).get(poi_type, {})
    
    # Strategy 1: Full constraints with spatial rules
    poi = _try_place_with_constraints(
        overworld, poi_type, poi_id, config, existing_pois,
        spatial_rules, gen_config, min_distance=config.poi_min_distance,
        use_spatial_rules=True, attempts=max_attempts
    )
    if poi is not None:
        return poi
    
    # Strategy 2: Relaxed minimum distance (75% of original)
    relaxed_distance = max(4, int(config.poi_min_distance * 0.75))
    poi = _try_place_with_constraints(
        overworld, poi_type, poi_id, config, existing_pois,
        spatial_rules, gen_config, min_distance=relaxed_distance,
        use_spatial_rules=True, attempts=max_attempts // 2
    )
    if poi is not None:
        return poi
    
    # Strategy 3: Further relaxed distance (50% of original) with lenient scoring
    very_relaxed_distance = max(3, int(config.poi_min_distance * 0.5))
    poi = _try_place_with_constraints(
        overworld, poi_type, poi_id, config, existing_pois,
        spatial_rules, gen_config, min_distance=very_relaxed_distance,
        use_spatial_rules=False, attempts=max_attempts // 2, min_score=0.1
    )
    if poi is not None:
        return poi
    
    # Strategy 4: Minimal constraints - just walkable and terrain, ignore distance
    poi = _try_place_with_constraints(
        overworld, poi_type, poi_id, config, existing_pois,
        spatial_rules, gen_config, min_distance=0,
        use_spatial_rules=False, attempts=max_attempts // 4, min_score=0.0
    )
    if poi is not None:
        return poi
    
    # All strategies failed
    return None


def _try_place_with_constraints(
    overworld: OverworldMap,
    poi_type: str,
    poi_id: str,
    config: OverworldConfig,
    existing_pois: List[PointOfInterest],
    spatial_rules: dict,
    gen_config,
    min_distance: int,
    use_spatial_rules: bool,
    attempts: int,
    min_score: float = 0.5,
) -> PointOfInterest | None:
    """
    Attempt to place a POI with specific constraints.
    
    Args:
        overworld: The overworld map
        poi_type: Type of POI to place
        poi_id: Unique identifier
        config: Configuration
        existing_pois: Already placed POIs
        spatial_rules: Spatial rules to apply (if use_spatial_rules is True)
        gen_config: Generation config
        min_distance: Minimum distance from existing POIs (0 = no constraint)
        use_spatial_rules: Whether to apply spatial rule scoring
        attempts: Number of attempts to make
        min_score: Minimum score to accept (lower = more lenient)
        
    Returns:
        Placed POI, or None if placement failed
    """
    candidates = []
    
    for attempt in range(attempts):
        # Random position
        x = random.randint(0, overworld.width - 1)
        y = random.randint(0, overworld.height - 1)
        
        # Check if tile is walkable
        if not overworld.is_walkable(x, y):
            continue
        
        # Check terrain suitability (use config-based blacklist)
        tile = overworld.get_tile(x, y)
        if tile is None:
            continue
        
        # Check if terrain is in blacklist
        terrain_blacklist = gen_config.poi.terrain_blacklist
        if tile.id in terrain_blacklist:
            continue
        
        # Check minimum distance from existing POIs (if constraint applies)
        if min_distance > 0:
            too_close = False
            for existing_poi in existing_pois:
                ex, ey = existing_poi.position
                dx = x - ex
                dy = y - ey
                distance = math.sqrt(dx * dx + dy * dy)
                
                if distance < min_distance:
                    too_close = True
                    break
            
            if too_close:
                continue
        
        # Evaluate position based on spatial rules (if enabled)
        if use_spatial_rules:
            score = _evaluate_poi_position(
                x, y, poi_type, existing_pois, spatial_rules, overworld
            )
        else:
            # Simple base score if spatial rules disabled
            score = 1.0
        
        # Accept positions meeting minimum score threshold
        if score >= min_score:
            candidates.append((x, y, score))
    
    # If we have candidates, choose one using weighted random selection
    if candidates:
        # Sort by score (higher is better)
        candidates.sort(key=lambda c: c[2], reverse=True)
        
        # Use weighted random selection from candidates
        # Consider more candidates (top 50% instead of top 33%)
        candidate_pool_size = max(1, len(candidates) // 2)
        candidate_pool = candidates[:candidate_pool_size]
        
        # Weighted random: higher scores have better chance, but all valid candidates can be chosen
        if len(candidate_pool) == 1:
            selected = candidate_pool[0]
        else:
            # Calculate weights based on scores (normalize to sum to 1)
            scores = [c[2] for c in candidate_pool]
            min_score_val = min(scores)
            max_score_val = max(scores)
            
            if max_score_val > min_score_val:
                # Normalize scores to [0, 1] range
                normalized = [(s - min_score_val) / (max_score_val - min_score_val) for s in scores]
                # Add small base weight to ensure even low scores have a chance
                weights = [n + 0.1 for n in normalized]
                # Normalize weights to sum to 1
                total_weight = sum(weights)
                weights = [w / total_weight for w in weights]
            else:
                # All scores equal, use uniform distribution
                weights = [1.0 / len(candidate_pool)] * len(candidate_pool)
            
            selected = random.choices(candidate_pool, weights=weights, k=1)[0]
        
        x, y, _ = selected
        
        # Calculate POI level
        poi_level = _calculate_poi_level(poi_type, x, y, overworld, existing_pois)
        
        # Get world seed from overworld map for deterministic name generation
        world_seed = overworld.seed if hasattr(overworld, "seed") and overworld.seed is not None else None
        
        # Select faction using intelligent placement logic (spatial awareness)
        # This happens AFTER position is determined, so we can consider nearby POIs
        faction_id = None
        try:
            if overworld and hasattr(overworld, "faction_manager") and overworld.faction_manager:
                faction_id = select_faction_for_poi(
                    overworld=overworld,
                    poi_type=poi_type,
                    position=(x, y),
                    existing_pois=existing_pois,
                    clustering_distance=25.0,  # POIs within 25 tiles prefer same faction
                    enemy_avoidance_distance=15.0,  # Avoid enemy factions within 15 tiles
                    variation_chance=0.3,  # 30% chance to ignore clustering for variety
                )
                
                # Fallback to default if no faction selected
                if not faction_id:
                    faction_id = overworld.faction_manager.get_faction_for_poi_type(poi_type)
        except Exception as e:
            # If faction selection fails, just continue without a faction
            print(f"Warning: Faction selection failed for {poi_type} at ({x}, {y}): {e}")
            faction_id = None
        
        # Create POI (pass gen_config for dungeon floor calculation and world_seed for name generation)
        poi = _create_poi(
            poi_type, poi_id, (x, y), level=poi_level, 
            gen_config=gen_config, world_seed=world_seed,
            overworld=overworld, faction_id=faction_id
        )
        return poi
    
    # No valid candidates found
    return None


def _evaluate_poi_position(
    x: int,
    y: int,
    poi_type: str,
    existing_pois: List[PointOfInterest],
    spatial_rules: dict,
    overworld: OverworldMap,
) -> float:
    """
    Evaluate a position for POI placement based on spatial rules.
    
    This function is fully config-driven and generic. It evaluates spatial rules
    defined in the configuration without hardcoding POI type-specific logic.
    
    Rule types supported (from config):
    - "near_{type}": Prefer being within min/max distance of specific POI type
    - "avoid_{type}": Penalize being too close to specific POI type
    - "prefer_remote": Bonus for being far from all existing POIs
    - Custom rules can be added by extending this function
    
    Returns a score (higher = better, always >= 0.1 to ensure position is considered).
    """
    score = 1.0  # Base score
    
    if not existing_pois:
        # First POI, no rules apply
        return score
    
    # Calculate distances to all existing POIs
    distances_by_type: Dict[str, List[float]] = {}
    for existing_poi in existing_pois:
        ex, ey = existing_poi.position
        dx = x - ex
        dy = y - ey
        distance = math.sqrt(dx * dx + dy * dy)
        existing_type = existing_poi.poi_type
        
        if existing_type not in distances_by_type:
            distances_by_type[existing_type] = []
        distances_by_type[existing_type].append(distance)
    
    # Apply configured spatial rules generically
    for rule_name, rule_config in spatial_rules.items():
        if not rule_config.get("enabled", False):
            continue
        
        # Handle "near_{type}" rules (e.g., "near_town")
        if rule_name.startswith("near_"):
            target_type = rule_name[5:]  # Remove "near_" prefix
            if target_type not in distances_by_type:
                # No target type present - apply small penalty or neutral
                # Don't penalize too heavily, allow placement anyway
                continue
            
            # Use minimum distance to target type
            min_distance_to_target = min(distances_by_type[target_type])
            
            min_dist = rule_config.get("min_distance", 10)
            max_dist = rule_config.get("max_distance", 30)
            chance = rule_config.get("chance", 0.7)
            bonus = rule_config.get("bonus", 2.0)
            close_penalty = rule_config.get("close_penalty", 0.5)  # Reduced default penalty
            far_penalty = rule_config.get("far_penalty", 0.2)  # Reduced default penalty
            
            if min_dist <= min_distance_to_target <= max_dist:
                # Good distance - apply chance-based bonus
                if random.random() < chance:
                    score += bonus  # Strong preference
                else:
                    score += bonus * 0.25  # Still acceptable
            elif min_distance_to_target < min_dist:
                # Too close - apply reduced penalty (don't eliminate position)
                score -= close_penalty
            else:
                # Too far - apply small penalty (still acceptable)
                score -= far_penalty
        
        # Handle "avoid_{type}" rules (e.g., "avoid_town")
        elif rule_name.startswith("avoid_"):
            target_type = rule_name[6:]  # Remove "avoid_" prefix
            if target_type not in distances_by_type:
                # No target type to avoid - this is good, small bonus
                score += 0.2
                continue
            
            # Use minimum distance to target type
            min_distance_to_target = min(distances_by_type[target_type])
            
            min_dist = rule_config.get("min_distance", 15)
            penalty = rule_config.get("penalty", 0.8)  # Reduced default penalty
            bonus_when_far = rule_config.get("bonus_when_far", 0.3)
            far_threshold = rule_config.get("far_threshold", min_dist * 1.5)
            
            if min_distance_to_target < min_dist:
                # Too close, apply penalty (but don't eliminate)
                score -= penalty
            elif min_distance_to_target >= far_threshold:
                # Far enough, small bonus
                score += bonus_when_far
            # If in between, no change (neutral)
        
        # Handle "prefer_remote" rule (bonus for being far from everything)
        elif rule_name == "prefer_remote":
            # Use minimum distance to any existing POI
            all_distances = [d for dist_list in distances_by_type.values() for d in dist_list]
            if not all_distances:
                continue
            
            min_distance_to_any = min(all_distances)
            distance_threshold = rule_config.get("distance_threshold", 30)
            bonus_weight = rule_config.get("bonus_weight", 1.5)
            
            if min_distance_to_any >= distance_threshold:
                score += bonus_weight  # Bonus for being remote
            # If closer, no penalty - this is a preference, not a requirement
    
    # Ensure score is always positive (minimum 0.1) to allow position consideration
    # This makes the system more lenient - positions are only eliminated if truly impossible
    return max(0.1, score)


def _calculate_dungeon_floor_count(dungeon_level: int, gen_config = None) -> int:
    """
    Calculate the number of floors for a dungeon based on its level.
    
    Floors scale directly with level - higher level dungeons always have more floors.
    Still allows some randomness but ensures proper scaling.
    
    Args:
        dungeon_level: The level/difficulty of the dungeon
        gen_config: Optional generation config (loaded if not provided)
        
    Returns:
        Number of floors (based on config)
    """
    if gen_config is None:
        gen_config = load_generation_config()
    floor_config = gen_config.dungeon.floor_count
    
    # Calculate base floor count that scales with level
    base = floor_config["base"]
    multiplier = floor_config["level_multiplier"]
    base_floors = base + int(dungeon_level * multiplier)
    
    # Add variance based on level range
    variance_config = floor_config["variance"]
    if dungeon_level <= variance_config["low_level"]["max_level"]:
        var_range = variance_config["low_level"]
    elif dungeon_level <= variance_config["mid_level"]["max_level"]:
        var_range = variance_config["mid_level"]
    else:
        var_range = variance_config["high_level"]
    
    variance = random.randint(var_range["min"], var_range["max"])
    floor_count = base_floors + variance
    
    # Ensure minimum based on level range (from config)
    min_floors_config = floor_config["min_floors_per_level_range"]
    level_min = _get_min_floors_for_level(dungeon_level, min_floors_config)
    floor_count = max(level_min, floor_count)
    
    # Cap at maximum (from config)
    max_floors = floor_config["max"]
    floor_count = min(floor_count, max_floors)
    
    return floor_count


def _get_min_floors_for_level(level: int, min_floors_config: Dict[str, int]) -> int:
    """Get minimum floors for a given level from config."""
    if level >= 19:
        return min_floors_config.get("19+", 9)
    elif level >= 16:
        return min_floors_config.get("16-18", 8)
    elif level >= 13:
        return min_floors_config.get("13-15", 7)
    elif level >= 10:
        return min_floors_config.get("10-12", 6)
    elif level >= 7:
        return min_floors_config.get("7-9", 5)
    elif level >= 4:
        return min_floors_config.get("4-6", 4)
    else:
        return min_floors_config.get("1-3", 3)


def _create_poi(
    poi_type: str,
    poi_id: str,
    position: tuple[int, int],
    level: int = 1,
    gen_config = None,
    world_seed: int | None = None,
    overworld = None,
    faction_id: str | None = None,
) -> PointOfInterest:
    """
    Create a POI instance of the given type using the registry.
    
    Args:
        poi_type: Type of POI
        poi_id: Unique identifier
        position: Overworld position
        level: Difficulty level of the POI
        gen_config: Optional generation config (for dungeon floor calculation)
        world_seed: Optional world seed for deterministic name generation
        
    Returns:
        PointOfInterest instance
        
    Raises:
        ValueError: If poi_type is not registered
    """
    registry = get_registry()
    
    # Generate name using name generation system with deterministic seed
    # Use world_seed + poi_id + position to create a unique but deterministic seed
    # Calculate a deterministic integer seed from the inputs
    if world_seed is not None:
        # Combine world seed, POI ID hash, and position into a single integer
        poi_id_hash = abs(hash(poi_id)) % 10000  # Limit hash to reasonable range
        name_seed = (world_seed * 100000 + poi_id_hash * 100 + position[0] * 10 + position[1]) % (2**31)
    else:
        # Fallback: use poi_id and position (less ideal but still deterministic)
        poi_id_hash = abs(hash(poi_id)) % 10000
        name_seed = (poi_id_hash * 1000 + position[0] * 100 + position[1]) % (2**31)
    
    # Save current random state
    old_state = random.getstate()
    try:
        # Set seed for deterministic name generation
        random.seed(name_seed)
        
        # Get faction info for name generation (faction_id already selected above)
        faction = None
        if overworld and hasattr(overworld, "faction_manager") and overworld.faction_manager and faction_id:
            faction = overworld.faction_manager.get_faction(faction_id)
        
        # Generate name based on POI type (faction-aware)
        if poi_type == "dungeon":
            name = generate_dungeon_name(include_descriptor=True, pattern="auto")
        elif poi_type == "village":
            name = generate_village_name(pattern="auto", faction_id=faction_id, faction=faction)
        elif poi_type == "town":
            name = generate_town_name(pattern="auto", faction_id=faction_id, faction=faction)
        elif poi_type == "camp":
            # Camps use village names (simpler, more rustic)
            name = generate_village_name(pattern="simple", faction_id=faction_id, faction=faction)
        else:
            # Fallback: use default naming
            name = None
    finally:
        # Restore random state
        random.setstate(old_state)
    
    
    # Special handling for dungeon (needs floor_count)
    if poi_type == "dungeon":
        floor_count = _calculate_dungeon_floor_count(level, gen_config)
        return registry.create(
            poi_type, poi_id, position, level=level, name=name, 
            floor_count=floor_count, faction_id=faction_id
        )
    else:
        # For other types, use standard creation
        return registry.create(poi_type, poi_id, position, level=level, name=name, faction_id=faction_id)

