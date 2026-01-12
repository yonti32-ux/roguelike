"""
Faction-aware POI placement logic.

Handles intelligent faction assignment during POI placement, considering:
- Spatial relationships (nearby POIs prefer same faction)
- Faction preferences for POI types
- Faction relationships (enemies avoid being too close)
- Variation (not all POIs go to the same faction)
"""

import random
import math
from typing import Optional, List, Tuple, Dict

from ..overworld.map import OverworldMap
from ..poi.base import PointOfInterest


def select_faction_for_poi(
    overworld: OverworldMap,
    poi_type: str,
    position: Tuple[int, int],
    existing_pois: List[PointOfInterest],
    clustering_distance: float = 25.0,
    enemy_avoidance_distance: float = 15.0,
    variation_chance: float = 0.3,
) -> Optional[str]:
    """
    Select an appropriate faction for a POI based on spatial relationships and preferences.
    
    Logic:
    1. Check for nearby POIs of the same type - prefer their faction (clustering)
    2. Check for nearby enemy POIs - avoid their faction (territorial)
    3. Consider faction preferences for this POI type
    4. Add variation to prevent all POIs going to the same faction
    
    Args:
        overworld: The overworld map
        poi_type: Type of POI being placed
        position: Position (x, y) where POI will be placed
        existing_pois: Already placed POIs
        clustering_distance: Distance within which to prefer same faction
        enemy_avoidance_distance: Distance within which to avoid enemy factions
        variation_chance: Chance to ignore clustering and pick a different faction
        
    Returns:
        Faction ID, or None if no suitable faction found
    """
    if not overworld or not hasattr(overworld, "faction_manager") or not overworld.faction_manager:
        return None
    
    faction_manager = overworld.faction_manager
    x, y = position
    
    # Step 1: Find nearby POIs and their factions
    nearby_same_type: List[Tuple[PointOfInterest, float]] = []  # (poi, distance)
    nearby_any: List[Tuple[PointOfInterest, float]] = []  # (poi, distance)
    
    for poi in existing_pois:
        px, py = poi.position
        dx = x - px
        dy = y - py
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance <= clustering_distance:
            nearby_any.append((poi, distance))
            if poi.poi_type == poi_type:
                nearby_same_type.append((poi, distance))
    
    # Early return if no factions available
    all_factions = faction_manager.get_all_factions()
    if not all_factions:
        return None
    
    # Step 2: Calculate faction scores
    faction_scores: Dict[str, float] = {}
    
    # Get all factions that prefer this POI type
    preferred_factions = []
    for faction in faction_manager.get_all_factions():
        if poi_type in faction.home_poi_types:
            preferred_factions.append(faction)
            # Base score from preference and spawn weight
            base_score = faction.spawn_weight * 2.0
            faction_scores[faction.id] = base_score
        else:
            # Factions that don't prefer this type still get a small chance
            faction_scores[faction.id] = faction.spawn_weight * 0.3
    
    # Step 3: Apply clustering bonus (nearby POIs of same type)
    if nearby_same_type and random.random() > variation_chance:
        # Prefer factions of nearby POIs of the same type
        for poi, distance in nearby_same_type:
            poi_faction_id = getattr(poi, "faction_id", None)
            if poi_faction_id and poi_faction_id in faction_scores:
                # Closer = stronger bonus (inverse distance)
                distance_factor = 1.0 - (distance / clustering_distance)
                bonus = 3.0 * distance_factor  # Strong clustering bonus
                faction_scores[poi_faction_id] += bonus
    
    # Step 4: Apply clustering bonus for nearby POIs of related types
    # (e.g., villages near towns of same faction)
    if nearby_any and random.random() > variation_chance * 0.7:
        related_types = {
            "town": ["village"],  # Villages cluster near towns
            "village": ["town"],  # Towns can have nearby villages
            "camp": ["camp"],  # Camps cluster together
        }
        
        related = related_types.get(poi_type, [])
        for poi, distance in nearby_any:
            poi_faction_id = getattr(poi, "faction_id", None)
            if poi.poi_type in related and poi_faction_id and poi_faction_id in faction_scores:
                distance_factor = 1.0 - (distance / clustering_distance)
                bonus = 2.0 * distance_factor  # Moderate clustering bonus
                faction_scores[poi_faction_id] += bonus
    
    # Step 5: Apply enemy avoidance penalty
    for poi, distance in nearby_any:
        poi_faction_id = getattr(poi, "faction_id", None)
        if poi_faction_id and distance <= enemy_avoidance_distance:
            poi_faction = faction_manager.get_faction(poi_faction_id)
            if not poi_faction:
                continue
            
            # Check all factions for enemies of this POI's faction
            for faction_id, score in faction_scores.items():
                candidate_faction = faction_manager.get_faction(faction_id)
                if not candidate_faction:
                    continue
                
                # If they're enemies, apply penalty
                if faction_manager.are_enemies(poi_faction.id, candidate_faction.id):
                    # Closer enemy = stronger penalty
                    distance_factor = 1.0 - (distance / enemy_avoidance_distance)
                    penalty = 5.0 * distance_factor  # Strong penalty
                    faction_scores[faction_id] -= penalty
    
    # Step 6: Ensure all scores are positive (no negative scores)
    min_score = min(faction_scores.values()) if faction_scores else 0.0
    if min_score < 0:
        adjustment = abs(min_score) + 0.1
        for faction_id in faction_scores:
            faction_scores[faction_id] += adjustment
    
    # Step 7: Weighted random selection
    if not faction_scores:
        return None
    
    factions = list(faction_scores.keys())
    weights = list(faction_scores.values())
    
    # Normalize weights to ensure they're all positive
    min_weight = min(weights)
    if min_weight <= 0:
        weights = [w - min_weight + 0.1 for w in weights]
    
    # Select faction based on weighted random
    selected = random.choices(factions, weights=weights, k=1)[0]
    return selected


def get_faction_cluster_center(
    overworld: OverworldMap,
    faction_id: str,
    existing_pois: List[PointOfInterest],
) -> Optional[Tuple[int, int]]:
    """
    Get the approximate center of a faction's territory based on existing POIs.
    
    Args:
        overworld: The overworld map
        faction_id: Faction ID
        existing_pois: Existing POIs
        
    Returns:
        Center position (x, y), or None if faction has no POIs
    """
    faction_pois = [poi for poi in existing_pois if poi.faction_id == faction_id]
    
    if not faction_pois:
        return None
    
    # Calculate centroid
    total_x = sum(poi.position[0] for poi in faction_pois)
    total_y = sum(poi.position[1] for poi in faction_pois)
    count = len(faction_pois)
    
    return (total_x // count, total_y // count)


def should_cluster_with_faction(
    overworld: OverworldMap,
    poi_type: str,
    position: Tuple[int, int],
    faction_id: str,
    existing_pois: List[PointOfInterest],
    clustering_distance: float = 25.0,
) -> bool:
    """
    Check if a POI should cluster with a specific faction based on nearby POIs.
    
    Args:
        overworld: The overworld map
        poi_type: Type of POI
        position: Position (x, y)
        faction_id: Faction to check
        existing_pois: Existing POIs
        clustering_distance: Distance threshold
        
    Returns:
        True if should cluster with this faction
    """
    x, y = position
    
    # Check for nearby POIs of this faction
    for poi in existing_pois:
        if poi.faction_id != faction_id:
            continue
        
        px, py = poi.position
        dx = x - px
        dy = y - py
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance <= clustering_distance:
            # Same type = stronger clustering
            if poi.poi_type == poi_type:
                return True
            # Related types = moderate clustering
            related_pairs = [
                ("town", "village"),
                ("village", "town"),
                ("camp", "camp"),
            ]
            if (poi_type, poi.poi_type) in related_pairs:
                return True
    
    return False

