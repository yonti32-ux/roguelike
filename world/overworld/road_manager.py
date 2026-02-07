"""
Road management system.

Manages road data and provides queries for road information.
"""

from typing import Dict, List, Set, Tuple, Optional, TYPE_CHECKING
from .road_generator import Road

if TYPE_CHECKING:
    from .map import OverworldMap


class RoadManager:
    """
    Manages roads on the overworld map.
    
    Provides efficient queries for road information and rendering.
    """
    
    def __init__(self, overworld_map: "OverworldMap"):
        """
        Initialize road manager.
        
        Args:
            overworld_map: The overworld map
        """
        self.overworld_map = overworld_map
        self.roads: List[Road] = []
        
        # Fast lookup: tile position -> set of road indices (Road objects aren't hashable)
        self.tile_to_roads: Dict[Tuple[int, int], Set[int]] = {}
        
        # Fast lookup: POI ID -> roads connected to it
        self.poi_to_roads: Dict[str, List[Road]] = {}
    
    def add_road(self, road: Road) -> None:
        """
        Add a road to the manager.
        
        Args:
            road: Road to add
        """
        road_index = len(self.roads)
        self.roads.append(road)
        
        # Update tile lookup (use index instead of Road object since Road isn't hashable)
        for x, y in road.segments:
            tile_pos = (x, y)
            if tile_pos not in self.tile_to_roads:
                self.tile_to_roads[tile_pos] = set()
            self.tile_to_roads[tile_pos].add(road_index)
        
        # Update POI lookup
        for poi_id in [road.start_poi_id, road.end_poi_id]:
            if poi_id not in self.poi_to_roads:
                self.poi_to_roads[poi_id] = []
            self.poi_to_roads[poi_id].append(road)
    
    def add_roads(self, roads: List[Road]) -> None:
        """Add multiple roads at once."""
        for road in roads:
            self.add_road(road)
    
    def clear_roads(self) -> None:
        """Clear all roads."""
        self.roads.clear()
        self.tile_to_roads.clear()
        self.poi_to_roads.clear()
    
    def has_road_at(self, x: int, y: int) -> bool:
        """
        Check if there's a road at the given tile position.
        
        Args:
            x, y: Tile coordinates
            
        Returns:
            True if there's a road at this position
        """
        return (x, y) in self.tile_to_roads
    
    def get_roads_at(self, x: int, y: int) -> List[Road]:
        """
        Get all roads passing through a tile.
        
        Args:
            x, y: Tile coordinates
            
        Returns:
            List of roads at this position
        """
        road_indices = self.tile_to_roads.get((x, y), set())
        return [self.roads[i] for i in road_indices]
    
    def get_road_type_at(self, x: int, y: int) -> Optional[str]:
        """
        Get the road type at a tile position.
        
        If multiple roads pass through, returns the "best" one (highway > cobblestone > dirt).
        Also handles road junctions (where multiple roads meet).
        
        Args:
            x, y: Tile coordinates
            
        Returns:
            Road type string, or None if no road
        """
        roads = self.get_roads_at(x, y)
        if not roads:
            return None
        
        # If multiple roads meet here, it's a junction - use the best road type
        # Priority: highway > cobblestone > dirt
        type_priority = {"highway": 3, "cobblestone": 2, "dirt": 1}
        
        best_road = max(roads, key=lambda r: type_priority.get(r.road_type, 0))
        return best_road.road_type
    
    def is_road_junction(self, x: int, y: int) -> bool:
        """
        Check if a tile is a road junction (multiple roads meet here).
        
        Args:
            x, y: Tile coordinates
            
        Returns:
            True if this is a junction (2+ roads meet)
        """
        roads = self.get_roads_at(x, y)
        return len(roads) >= 2
    
    def get_roads_for_poi(self, poi_id: str) -> List[Road]:
        """
        Get all roads connected to a POI.
        
        Args:
            poi_id: POI identifier
            
        Returns:
            List of roads connected to this POI
        """
        return self.poi_to_roads.get(poi_id, [])
    
    def get_all_roads(self) -> List[Road]:
        """Get all roads."""
        return list(self.roads)
    
    def get_road_segments_in_viewport(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
    ) -> Set[Tuple[int, int]]:
        """
        Get all road tile positions within a viewport.
        
        Args:
            start_x, start_y: Viewport start (tile coordinates)
            end_x, end_y: Viewport end (tile coordinates)
            
        Returns:
            Set of (x, y) positions that have roads and are in viewport
        """
        visible_segments = set()
        
        for road in self.roads:
            for x, y in road.segments:
                if start_x <= x < end_x and start_y <= y < end_y:
                    visible_segments.add((x, y))
        
        return visible_segments
    
    def get_road_network_stats(self) -> Dict[str, any]:
        """
        Get statistics about the road network.
        
        Returns:
            Dictionary with road network statistics
        """
        total_length = sum(road.length for road in self.roads)
        road_types = {}
        for road in self.roads:
            road_types[road.road_type] = road_types.get(road.road_type, 0) + 1
        
        return {
            "total_roads": len(self.roads),
            "total_length": total_length,
            "road_types": road_types,
            "connected_pois": len(self.poi_to_roads),
        }


