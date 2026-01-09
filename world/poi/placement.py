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
        
        # Valid position found - create POI
        poi = _create_poi(poi_type, poi_id, (x, y))
        return poi
    
    # Failed to place after max attempts
    return None


def _create_poi(poi_type: str, poi_id: str, position: tuple[int, int]) -> PointOfInterest:
    """
    Create a POI instance of the given type.
    
    Args:
        poi_type: Type of POI
        poi_id: Unique identifier
        position: Overworld position
        
    Returns:
        PointOfInterest instance
    """
    if poi_type == "dungeon":
        return DungeonPOI(poi_id, position, floor_count=5)
    elif poi_type == "village":
        return VillagePOI(poi_id, position)
    elif poi_type == "town":
        return TownPOI(poi_id, position)
    elif poi_type == "camp":
        return CampPOI(poi_id, position)
    else:
        # Default to dungeon
        return DungeonPOI(poi_id, position)

