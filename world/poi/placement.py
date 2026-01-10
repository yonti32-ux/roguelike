"""
POI placement algorithms.

Handles the placement of POIs on the overworld according to configuration.
"""

import random
import math
from typing import List, Dict, Any

from ..overworld.map import OverworldMap
from ..overworld.config import OverworldConfig
from ..overworld.terrain import TERRAIN_WATER, get_terrain
from .base import PointOfInterest
from .types import DungeonPOI, VillagePOI, TownPOI, CampPOI
from ..generation.config import load_generation_config


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
) -> PointOfInterest | None:
    """
    Attempt to place a single POI with spatial placement rules.
    
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
    gen_config = load_generation_config()
    max_attempts = gen_config.poi.max_placement_attempts
    
    if placement_rules is None:
        placement_rules = {}
    
    spatial_rules = placement_rules.get("spatial_rules", {}).get(poi_type, {})
    
    # Generate candidate positions with weighted scoring
    candidates = []
    
    for attempt in range(max_attempts):
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
        
        # Check minimum distance from existing POIs (base constraint)
        too_close = False
        for existing_poi in existing_pois:
            ex, ey = existing_poi.position
            dx = x - ex
            dy = y - ey
            distance = math.sqrt(dx * dx + dy * dy)
            
            if distance < config.poi_min_distance:
                too_close = True
                break
        
        if too_close:
            continue
        
        # Evaluate position based on spatial rules
        score = _evaluate_poi_position(
            x, y, poi_type, existing_pois, spatial_rules, overworld
        )
        
        if score > 0:  # Valid position
            candidates.append((x, y, score))
    
    # If we have candidates, choose one based on score (weighted random)
    if candidates:
        # Sort by score (higher is better)
        candidates.sort(key=lambda c: c[2], reverse=True)
        
        # Use weighted random selection (higher score = higher chance)
        # Take top candidates and randomly select from them
        top_candidates = candidates[:max(1, len(candidates) // 3)]  # Top third
        if top_candidates:
            selected = random.choice(top_candidates)
            x, y, _ = selected
            
            # Calculate POI level
            poi_level = _calculate_poi_level(poi_type, x, y, overworld, existing_pois)
            
            # Create POI
            poi = _create_poi(poi_type, poi_id, (x, y), level=poi_level)
            return poi
    
    # Failed to place after max attempts
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
    
    Returns a score (0.0 = invalid, higher = better).
    """
    score = 1.0  # Base score
    
    if not existing_pois:
        # First POI, no rules apply
        return score
    
    # Check distances to existing POIs
    for existing_poi in existing_pois:
        ex, ey = existing_poi.position
        dx = x - ex
        dy = y - ey
        distance = math.sqrt(dx * dx + dy * dy)
        existing_type = existing_poi.poi_type
        
        # Apply spatial rules based on POI type
        if poi_type == "village":
            # Villages should be near towns
            near_town_rule = spatial_rules.get("near_town", {})
            if near_town_rule.get("enabled", False) and existing_type == "town":
                min_dist = near_town_rule.get("min_distance", 10)
                max_dist = near_town_rule.get("max_distance", 30)
                chance = near_town_rule.get("chance", 0.7)
                
                if min_dist <= distance <= max_dist:
                    # Good distance from town
                    if random.random() < chance:
                        score += 2.0  # Strong preference
                    else:
                        score += 0.5  # Still acceptable
                elif distance < min_dist:
                    score -= 1.0  # Too close
                else:
                    score -= 0.5  # Too far
            
            # Villages should avoid dungeons
            avoid_dungeon_rule = spatial_rules.get("avoid_dungeon", {})
            if avoid_dungeon_rule.get("enabled", False) and existing_type == "dungeon":
                min_dist = avoid_dungeon_rule.get("min_distance", 15)
                if distance < min_dist:
                    score -= 2.0  # Strong penalty
        
        elif poi_type == "dungeon":
            # Dungeons should avoid towns
            avoid_town_rule = spatial_rules.get("avoid_town", {})
            if avoid_town_rule.get("enabled", False) and existing_type == "town":
                min_dist = avoid_town_rule.get("min_distance", 25)
                if distance < min_dist:
                    score -= 3.0  # Strong penalty for being too close to town
                else:
                    score += 0.3  # Bonus for being far from town
            
            # Dungeons should avoid villages
            avoid_village_rule = spatial_rules.get("avoid_village", {})
            if avoid_village_rule.get("enabled", False) and existing_type == "village":
                min_dist = avoid_village_rule.get("min_distance", 20)
                if distance < min_dist:
                    score -= 2.0  # Penalty for being too close to village
                else:
                    score += 0.2  # Bonus for being far from village
            
            # Dungeons prefer remote locations
            prefer_remote_rule = spatial_rules.get("prefer_remote", {})
            if prefer_remote_rule.get("enabled", False):
                distance_threshold = prefer_remote_rule.get("distance_threshold", 30)
                bonus_weight = prefer_remote_rule.get("bonus_weight", 1.5)
                if distance >= distance_threshold:
                    score += bonus_weight  # Bonus for being remote
        
        elif poi_type == "camp":
            # Camps should avoid towns
            avoid_town_rule = spatial_rules.get("avoid_town", {})
            if avoid_town_rule.get("enabled", False) and existing_type == "town":
                min_dist = avoid_town_rule.get("min_distance", 12)
                if distance < min_dist:
                    score -= 1.5  # Penalty
            
            # Camps should avoid villages
            avoid_village_rule = spatial_rules.get("avoid_village", {})
            if avoid_village_rule.get("enabled", False) and existing_type == "village":
                min_dist = avoid_village_rule.get("min_distance", 10)
                if distance < min_dist:
                    score -= 1.0  # Penalty
    
    # Return score (must be > 0 to be valid)
    return max(0.0, score)


def _calculate_dungeon_floor_count(dungeon_level: int) -> int:
    """
    Calculate the number of floors for a dungeon based on its level.
    
    Floors scale directly with level - higher level dungeons always have more floors.
    Still allows some randomness but ensures proper scaling.
    
    Args:
        dungeon_level: The level/difficulty of the dungeon
        
    Returns:
        Number of floors (based on config)
    """
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


def _create_poi(poi_type: str, poi_id: str, position: tuple[int, int], level: int = 1) -> PointOfInterest:
    """
    Create a POI instance of the given type.
    
    Args:
        poi_type: Type of POI
        poi_id: Unique identifier
        position: Overworld position
        level: Difficulty level of the POI
        
    Returns:
        PointOfInterest instance
    """
    if poi_type == "dungeon":
        floor_count = _calculate_dungeon_floor_count(level)
        return DungeonPOI(poi_id, position, level=level, floor_count=floor_count)
    elif poi_type == "village":
        return VillagePOI(poi_id, position, level=level)
    elif poi_type == "town":
        return TownPOI(poi_id, position, level=level)
    elif poi_type == "camp":
        return CampPOI(poi_id, position, level=level)
    else:
        # Default to dungeon
        floor_count = _calculate_dungeon_floor_count(level)
        return DungeonPOI(poi_id, position, level=level, floor_count=floor_count)

