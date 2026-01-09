"""
POI placement algorithms.

Handles the placement of POIs on the overworld according to configuration.
"""

import random
import math
from typing import List

from ..overworld.map import OverworldMap
from ..overworld.config import OverworldConfig
from ..overworld.terrain import TERRAIN_WATER
from .base import PointOfInterest
from .types import DungeonPOI, VillagePOI, TownPOI, CampPOI


def place_pois(overworld: OverworldMap, config: OverworldConfig) -> List[PointOfInterest]:
    """
    Place POIs on the overworld according to configuration.
    
    Args:
        overworld: The overworld map
        config: Configuration with POI settings
        
    Returns:
        List of placed POIs
    """
    pois: List[PointOfInterest] = []
    
    # Calculate target POI count
    world_area = overworld.width * overworld.height
    target_count = int(world_area * config.poi_density)
    
    # Cap maximum POIs to prevent performance issues
    max_pois = min(target_count, 200)  # Reasonable maximum
    
    # Distribute by type
    poi_type_counts = _distribute_poi_types(max_pois, config.poi_distribution)
    
    # Place each type
    poi_id_counter = 1
    failed_placements = 0
    max_failures = 50  # Stop if we fail too many times in a row
    
    for poi_type, count in poi_type_counts.items():
        for _ in range(count):
            poi = _place_single_poi(
                overworld=overworld,
                poi_type=poi_type,
                poi_id=f"{poi_type}_{poi_id_counter}",
                config=config,
                existing_pois=pois,
            )
            
            if poi is not None:
                pois.append(poi)
                poi_id_counter += 1
                failed_placements = 0  # Reset failure counter on success
            else:
                failed_placements += 1
                if failed_placements >= max_failures:
                    # Too many failures, stop trying
                    print(f"Warning: Stopped placing POIs after {failed_placements} consecutive failures")
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
) -> PointOfInterest | None:
    """
    Attempt to place a single POI.
    
    Args:
        overworld: The overworld map
        poi_type: Type of POI to place
        poi_id: Unique identifier
        config: Configuration
        existing_pois: Already placed POIs (for distance checking)
        
    Returns:
        Placed POI, or None if placement failed
    """
    max_attempts = 200  # Increased attempts for better placement
    
    for attempt in range(max_attempts):
        # Random position
        x = random.randint(0, overworld.width - 1)
        y = random.randint(0, overworld.height - 1)
        
        # Check if tile is walkable
        if not overworld.is_walkable(x, y):
            continue
        
        # Check terrain suitability (no POIs on water)
        tile = overworld.get_tile(x, y)
        if tile is None or tile == TERRAIN_WATER:
            continue
        
        # Check minimum distance from existing POIs
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
        
        # Calculate POI level (for now, random 1-10, but could be based on distance from start, etc.)
        poi_level = _calculate_poi_level(poi_type, x, y, overworld, existing_pois)
        
        # Valid position found - create POI
        poi = _create_poi(poi_type, poi_id, (x, y), level=poi_level)
        return poi
    
    # Failed to place after max attempts
    return None


def _calculate_dungeon_floor_count(dungeon_level: int) -> int:
    """
    Calculate the number of floors for a dungeon based on its level.
    
    Floors scale directly with level - higher level dungeons always have more floors.
    Still allows some randomness but ensures proper scaling.
    
    Args:
        dungeon_level: The level/difficulty of the dungeon
        
    Returns:
        Number of floors (3-20, with direct scaling based on level)
    """
    # Calculate base floor count that scales with level
    # Formula: base = 3 + floor(level * 0.4)
    # This ensures:
    # - Level 1: base ~3-4 floors
    # - Level 5: base ~5 floors
    # - Level 10: base ~7 floors
    # - Level 15: base ~9 floors
    # - Level 20: base ~11 floors
    # - Level 25: base ~13 floors
    
    base_floors = 3 + int(dungeon_level * 0.4)
    
    # Add variance: ±2 floors for randomness, but higher level floors can vary more
    # Lower levels: ±1 to ±2 floors
    # Higher levels (10+): ±2 to ±3 floors
    if dungeon_level <= 5:
        variance = random.randint(-1, 2)  # Allow slightly lower for early levels
    elif dungeon_level <= 10:
        variance = random.randint(-2, 2)
    else:
        variance = random.randint(-2, 3)  # More variance for higher levels
    
    floor_count = base_floors + variance
    
    # Ensure minimum based on level (higher level = higher minimum)
    # Level 1-3: min 3 floors
    # Level 4-6: min 4 floors
    # Level 7-9: min 5 floors
    # Level 10-12: min 6 floors
    # Level 13-15: min 7 floors
    # Level 16-18: min 8 floors
    # Level 19+: min 9 floors
    level_min = 3 + ((dungeon_level - 1) // 3)
    floor_count = max(level_min, floor_count)
    
    # Cap at reasonable maximum (20 floors)
    floor_count = min(floor_count, 20)
    
    return floor_count


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

