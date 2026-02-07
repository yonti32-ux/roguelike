"""
Road generation system.

Generates roads between POIs using pathfinding algorithms.
Modular and customizable - supports different road types and generation strategies.
"""

import math
import random
from typing import List, Set, Tuple, Optional, Dict, TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from .map import OverworldMap
    from ..poi.base import PointOfInterest


@dataclass
class RoadSegment:
    """Represents a single road segment (connection between two tiles)."""
    x: int
    y: int
    road_type: str  # "dirt", "cobblestone", "highway", etc.
    width: int = 1  # Road width in tiles (for future expansion)
    
    def __hash__(self) -> int:
        return hash((self.x, self.y))
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, RoadSegment):
            return False
        return self.x == other.x and self.y == other.y


@dataclass
class Road:
    """Represents a complete road connecting two POIs."""
    start_poi_id: str
    end_poi_id: str
    segments: List[Tuple[int, int]]  # List of (x, y) positions
    road_type: str
    length: float  # Total length of the road
    
    def get_segments_set(self) -> Set[Tuple[int, int]]:
        """Get all road positions as a set for fast lookup."""
        return set(self.segments)


class RoadGenerator:
    """
    Generates roads between POIs using pathfinding.
    
    Supports multiple generation strategies:
    - Direct: Straight lines (with terrain avoidance)
    - Pathfinding: A* pathfinding around obstacles
    - Hybrid: Combination of both
    """
    
    def __init__(
        self,
        overworld_map: "OverworldMap",
        config: Optional[Dict] = None,
    ):
        """
        Initialize road generator.
        
        Args:
            overworld_map: The overworld map to generate roads on
            config: Road generation configuration
        """
        self.overworld_map = overworld_map
        self.config = config or {}
        
        # Default configuration
        self.min_poi_distance = self.config.get("min_poi_distance", 10)
        self.max_road_length = self.config.get("max_road_length", 200)
        self.road_types = self.config.get("road_types", {
            "town_to_town": "highway",
            "town_to_village": "cobblestone",
            "village_to_village": "dirt",
            "default": "dirt",
        })
        self.generation_strategy = self.config.get("strategy", "pathfinding")
        self.avoid_terrain = self.config.get("avoid_terrain", ["water", "mountain"])
        self.smooth_roads = self.config.get("smooth_roads", True)
        self.road_width = self.config.get("road_width", 1)
    
    def generate_roads(
        self,
        pois: List["PointOfInterest"],
        connect_types: Optional[List[str]] = None,
    ) -> List[Road]:
        """
        Generate roads between POIs.
        
        Args:
            pois: List of POIs to connect
            connect_types: POI types to connect (if None, connects all)
            
        Returns:
            List of generated roads
        """
        if connect_types is None:
            connect_types = ["town", "village"]  # Default: connect towns and villages
        
        # Filter POIs by type
        target_pois = [poi for poi in pois if poi.poi_type in connect_types]
        
        if len(target_pois) < 2:
            print(f"Road generation: Only {len(target_pois)} POIs of types {connect_types} found, need at least 2")
            return []  # Need at least 2 POIs to create roads
        
        roads: List[Road] = []
        
        # Strategy 1: Connect towns first (create a network)
        towns = [poi for poi in target_pois if poi.poi_type == "town"]
        if len(towns) >= 2:
            # Create a minimum spanning tree between towns
            town_roads = self._generate_network(towns, "highway")
            roads.extend(town_roads)
        
        # Strategy 2: Connect villages to nearest town
        villages = [poi for poi in target_pois if poi.poi_type == "village"]
        for village in villages:
            nearest_town = self._find_nearest_poi(village, towns)
            if nearest_town:
                road = self._generate_road(
                    village,
                    nearest_town,
                    road_type="cobblestone",
                )
                if road:
                    roads.append(road)
        
        # Strategy 3: Connect nearby villages to each other (optional)
        if self.config.get("connect_villages", False):
            village_roads = self._connect_nearby_pois(villages, max_distance=30)
            roads.extend(village_roads)
        
        return roads
    
    def _generate_network(
        self,
        pois: List["PointOfInterest"],
        road_type: str,
    ) -> List[Road]:
        """
        Generate a network of roads connecting POIs (minimum spanning tree).
        
        Uses Prim's algorithm to create an efficient network.
        """
        if len(pois) < 2:
            return []
        
        roads: List[Road] = []
        connected: Set[str] = {pois[0].poi_id}
        unconnected = {poi.poi_id: poi for poi in pois[1:]}
        
        while unconnected:
            # Find closest unconnected POI to any connected POI
            best_connection = None
            best_distance = float('inf')
            
            for connected_id in connected:
                connected_poi = next(p for p in pois if p.poi_id == connected_id)
                for unconnected_id, unconnected_poi in unconnected.items():
                    distance = self._euclidean_distance(
                        connected_poi.position,
                        unconnected_poi.position,
                    )
                    if distance < best_distance:
                        best_distance = distance
                        best_connection = (connected_id, unconnected_id)
            
            if best_connection:
                start_id, end_id = best_connection
                start_poi = next(p for p in pois if p.poi_id == start_id)
                end_poi = next(p for p in pois if p.poi_id == end_id)
                
                road = self._generate_road(start_poi, end_poi, road_type=road_type)
                if road and len(road.segments) >= 2:
                    # Only add if road has valid segments
                    roads.append(road)
                    connected.add(end_id)
                    del unconnected[end_id]
                elif road:
                    print(f"Warning: Road from {start_poi.poi_id} to {end_poi.poi_id} has only {len(road.segments)} segments, skipping")
            else:
                break  # Can't connect any more
        
        return roads
    
    def _connect_nearby_pois(
        self,
        pois: List["PointOfInterest"],
        max_distance: float,
    ) -> List[Road]:
        """Connect POIs that are within max_distance of each other."""
        roads: List[Road] = []
        
        for i, poi1 in enumerate(pois):
            for poi2 in pois[i + 1:]:
                distance = self._euclidean_distance(poi1.position, poi2.position)
                if distance <= max_distance:
                    road = self._generate_road(poi1, poi2, road_type="dirt")
                    if road:
                        roads.append(road)
        
        return roads
    
    def _generate_road(
        self,
        start_poi: "PointOfInterest",
        end_poi: "PointOfInterest",
        road_type: Optional[str] = None,
    ) -> Optional[Road]:
        """
        Generate a single road between two POIs.
        
        Args:
            start_poi: Starting POI
            end_poi: Ending POI
            road_type: Type of road (if None, determines from POI types)
            
        Returns:
            Road object, or None if generation failed
        """
        if road_type is None:
            road_type = self._determine_road_type(start_poi, end_poi)
        
        # Check if road would be too long
        distance = self._euclidean_distance(start_poi.position, end_poi.position)
        if distance > self.max_road_length:
            return None
        
        # Generate path based on strategy
        path = None
        if self.generation_strategy == "direct":
            path = self._generate_direct_path(start_poi.position, end_poi.position)
        elif self.generation_strategy == "pathfinding":
            path = self._generate_pathfinding_path(start_poi.position, end_poi.position)
        else:  # hybrid
            path = self._generate_hybrid_path(start_poi.position, end_poi.position)
        
        # If pathfinding failed, try direct path as fallback
        if not path or len(path) < 2:
            print(f"Warning: Pathfinding failed from {start_poi.poi_id} to {end_poi.poi_id}, trying direct path")
            path = self._generate_direct_path(start_poi.position, end_poi.position)
        
        # Validate path - must connect start to end
        if not path or len(path) < 2:
            print(f"Warning: Failed to generate any path from {start_poi.poi_id} to {end_poi.poi_id}")
            return None
        
        # Ensure path starts and ends at POI positions
        if path[0] != start_poi.position:
            path.insert(0, start_poi.position)
        if path[-1] != end_poi.position:
            path.append(end_poi.position)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_path = []
        for pos in path:
            if pos not in seen:
                seen.add(pos)
                unique_path.append(pos)
        path = unique_path
        
        # Validate path is continuous (adjacent tiles)
        path = self._ensure_path_continuity(path)
        
        # Smooth the path if enabled (but ensure start/end are preserved)
        if self.smooth_roads and len(path) > 2:
            smoothed = self._smooth_path(path)
            # Ensure start and end are still in smoothed path
            if smoothed[0] != start_poi.position:
                smoothed.insert(0, start_poi.position)
            if smoothed[-1] != end_poi.position:
                smoothed.append(end_poi.position)
            # Ensure continuity after smoothing
            smoothed = self._ensure_path_continuity(smoothed)
            path = smoothed
        
        # Calculate total length
        total_length = self._calculate_path_length(path)
        
        return Road(
            start_poi_id=start_poi.poi_id,
            end_poi_id=end_poi.poi_id,
            segments=path,
            road_type=road_type,
            length=total_length,
        )
    
    def _generate_direct_path(
        self,
        start: Tuple[int, int],
        end: Tuple[int, int],
    ) -> List[Tuple[int, int]]:
        """
        Generate a direct path using Bresenham's line algorithm.
        
        Prefers easier terrain types (plains, grass) when possible.
        """
        path = []
        x0, y0 = start
        x1, y1 = end
        
        # Always include start position
        path.append(start)
        
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        
        x, y = x0, y0
        
        while True:
            if x == x1 and y == y1:
                break
            
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy
            
            # Add tile if walkable (or if it's the end position, always add it)
            if (x, y) == end:
                path.append((x, y))
                break
            elif self.overworld_map.is_walkable(x, y):
                path.append((x, y))
        
        # Ensure end is always included
        if path[-1] != end:
            path.append(end)
        
        # Post-process: try to prefer easier terrain when possible
        # This makes roads follow plains/grass when available
        optimized_path = self._optimize_path_terrain(path)
        
        return optimized_path
    
    def _optimize_path_terrain(self, path: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """
        Optimize path to prefer easier terrain types when possible.
        
        Tries to route through plains/grass instead of forest/desert when
        there's a nearby alternative.
        """
        try:
            if len(path) < 3:
                return path
            
            optimized = [path[0]]
            
            for i in range(1, len(path) - 1):
                prev = path[i - 1]
                curr = path[i]
                next_pos = path[i + 1]
                
                # Check current terrain
                tile = self.overworld_map.get_tile(curr[0], curr[1])
                if not tile:
                    optimized.append(curr)
                    continue
                
                current_terrain = tile.id if hasattr(tile, 'id') else "grass"
                
                # If we're on difficult terrain, try to find a nearby easier alternative
                if current_terrain in ["forest", "desert"]:
                    # Look for nearby plains/grass tiles
                    best_alt = None
                    best_score = 0
                    
                    for dx in [-1, 0, 1]:
                        for dy in [-1, 0, 1]:
                            if dx == 0 and dy == 0:
                                continue
                            
                            alt_x = curr[0] + dx
                            alt_y = curr[1] + dy
                            
                            if not self.overworld_map.in_bounds(alt_x, alt_y):
                                continue
                            
                            if not self.overworld_map.is_walkable(alt_x, alt_y):
                                continue
                            
                            # Check if this alternative maintains path continuity
                            if self._are_adjacent(prev, (alt_x, alt_y)) and self._are_adjacent((alt_x, alt_y), next_pos):
                                alt_tile = self.overworld_map.get_tile(alt_x, alt_y)
                                if alt_tile and hasattr(alt_tile, 'id'):
                                    # Score: plains=3, grass=2, forest=1, desert=1
                                    terrain_scores = {"plains": 3, "grass": 2, "forest": 1, "desert": 1}
                                    score = terrain_scores.get(alt_tile.id, 1)
                                    if score > best_score:
                                        best_score = score
                                        best_alt = (alt_x, alt_y)
                    
                    if best_alt:
                        optimized.append(best_alt)
                    else:
                        optimized.append(curr)
                else:
                    optimized.append(curr)
            
            optimized.append(path[-1])
            return optimized
        except Exception as e:
            # If optimization fails, just return original path
            print(f"Warning: Path terrain optimization failed: {e}")
            return path
    
    def _generate_pathfinding_path(
        self,
        start: Tuple[int, int],
        end: Tuple[int, int],
    ) -> List[Tuple[int, int]]:
        """
        Generate path using A* pathfinding.
        
        Avoids unwalkable terrain and optionally avoids certain terrain types.
        """
        return self._astar_pathfinding(start, end)
    
    def _generate_hybrid_path(
        self,
        start: Tuple[int, int],
        end: Tuple[int, int],
    ) -> List[Tuple[int, int]]:
        """
        Generate path using hybrid approach.
        
        Tries direct path first, falls back to pathfinding if blocked.
        """
        direct_path = self._generate_direct_path(start, end)
        
        # Check if direct path is blocked
        blocked = False
        for x, y in direct_path:
            if not self.overworld_map.is_walkable(x, y):
                blocked = True
                break
        
        if not blocked:
            return direct_path
        
        # Use pathfinding as fallback
        return self._generate_pathfinding_path(start, end)
    
    def _astar_pathfinding(
        self,
        start: Tuple[int, int],
        goal: Tuple[int, int],
    ) -> List[Tuple[int, int]]:
        """
        A* pathfinding algorithm.
        
        Finds optimal path avoiding unwalkable terrain and optionally avoiding
        certain terrain types (water, mountains, etc.).
        """
        open_set: List[Tuple[float, Tuple[int, int]]] = [(0, start)]
        came_from: Dict[Tuple[int, int], Optional[Tuple[int, int]]] = {start: None}
        g_score: Dict[Tuple[int, int], float] = {start: 0}
        f_score: Dict[Tuple[int, int], float] = {start: self._heuristic(start, goal)}
        
        while open_set:
            # Get node with lowest f_score
            open_set.sort(key=lambda x: x[0])
            current = open_set.pop(0)[1]
            
            if current == goal:
                # Reconstruct path
                path = []
                while current is not None:
                    path.append(current)
                    current = came_from.get(current)
                return list(reversed(path))
            
            # Check neighbors (8-directional)
            for dx, dy in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
                neighbor = (current[0] + dx, current[1] + dy)
                
                if not self.overworld_map.in_bounds(neighbor[0], neighbor[1]):
                    continue
                
                if not self.overworld_map.is_walkable(neighbor[0], neighbor[1]):
                    continue
                
                # Check if we should avoid this terrain type
                tile = self.overworld_map.get_tile(neighbor[0], neighbor[1])
                if tile and tile.id in self.avoid_terrain:
                    # Still allow, but with much higher cost (prefer avoiding)
                    move_cost = 5.0
                else:
                    move_cost = 1.0
                
                # Prefer certain terrain types for roads (plains, grass are easier)
                if tile:
                    if tile.id == "plains":
                        move_cost *= 0.8  # Plains are easier to build roads on
                    elif tile.id == "grass":
                        move_cost *= 0.9  # Grass is slightly easier
                    elif tile.id == "forest":
                        move_cost *= 1.3  # Forests are harder (but still passable)
                    elif tile.id == "desert":
                        move_cost *= 1.1  # Deserts are slightly harder
                
                # Diagonal movement costs more
                if dx != 0 and dy != 0:
                    move_cost *= 1.414  # sqrt(2)
                
                tentative_g = g_score.get(current, float('inf')) + move_cost
                
                if tentative_g < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + self._heuristic(neighbor, goal)
                    
                    # Add to open set if not already there
                    if not any(n == neighbor for _, n in open_set):
                        open_set.append((f_score[neighbor], neighbor))
        
        # No path found
        return []
    
    def _heuristic(self, a: Tuple[int, int], b: Tuple[int, int]) -> float:
        """Heuristic function for A* (Euclidean distance)."""
        dx = a[0] - b[0]
        dy = a[1] - b[1]
        return math.sqrt(dx * dx + dy * dy)
    
    def _smooth_path(self, path: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """
        Smooth a path by removing unnecessary waypoints.
        
        Uses line-of-sight checks to remove intermediate points.
        Preserves connectivity - ensures path is still valid.
        """
        if len(path) <= 2:
            return path
        
        # First pass: remove unnecessary waypoints
        smoothed = [path[0]]  # Always keep start
        
        i = 0
        while i < len(path) - 1:
            # Try to skip ahead as far as possible
            j = len(path) - 1
            found_skip = False
            while j > i + 1:
                if self._has_line_of_sight(path[i], path[j]):
                    smoothed.append(path[j])
                    i = j
                    found_skip = True
                    break
                j -= 1
            
            if not found_skip:
                # Can't skip, add next point to maintain connectivity
                smoothed.append(path[i + 1])
                i += 1
        
        # Always ensure end is included
        if smoothed[-1] != path[-1]:
            smoothed.append(path[-1])
        
        return smoothed
    
    def _are_adjacent(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> bool:
        """Check if two positions are adjacent (including diagonals)."""
        dx = abs(pos1[0] - pos2[0])
        dy = abs(pos1[1] - pos2[1])
        return dx <= 1 and dy <= 1
    
    def _has_line_of_sight(
        self,
        start: Tuple[int, int],
        end: Tuple[int, int],
    ) -> bool:
        """
        Check if there's a clear line of sight between two points.
        
        Returns True if all tiles along the line are walkable.
        """
        x0, y0 = start
        x1, y1 = end
        
        # If start and end are the same, it's valid
        if start == end:
            return True
        
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        
        x, y = x0, y0
        
        # Check all tiles along the line (including start and end)
        while True:
            # Check bounds
            if not self.overworld_map.in_bounds(x, y):
                return False
            
            # Check if walkable
            if not self.overworld_map.is_walkable(x, y):
                return False
            
            # Check if we reached the end
            if x == x1 and y == y1:
                break
            
            # Move to next tile
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy
        
        return True
    
    def _calculate_path_length(self, path: List[Tuple[int, int]]) -> float:
        """Calculate total length of a path."""
        if len(path) < 2:
            return 0.0
        
        total = 0.0
        for i in range(len(path) - 1):
            total += self._euclidean_distance(path[i], path[i + 1])
        
        return total
    
    def _euclidean_distance(
        self,
        a: Tuple[int, int],
        b: Tuple[int, int],
    ) -> float:
        """Calculate Euclidean distance between two points."""
        dx = a[0] - b[0]
        dy = a[1] - b[1]
        return math.sqrt(dx * dx + dy * dy)
    
    def _determine_road_type(
        self,
        poi1: "PointOfInterest",
        poi2: "PointOfInterest",
    ) -> str:
        """Determine road type based on POI types."""
        types_key = f"{poi1.poi_type}_to_{poi2.poi_type}"
        reverse_key = f"{poi2.poi_type}_to_{poi1.poi_type}"
        
        if types_key in self.road_types:
            return self.road_types[types_key]
        elif reverse_key in self.road_types:
            return self.road_types[reverse_key]
        else:
            return self.road_types.get("default", "dirt")
    
    def _find_nearest_poi(
        self,
        poi: "PointOfInterest",
        candidates: List["PointOfInterest"],
    ) -> Optional["PointOfInterest"]:
        """Find the nearest POI from a list of candidates."""
        if not candidates:
            return None
        
        nearest = None
        min_distance = float('inf')
        
        for candidate in candidates:
            distance = self._euclidean_distance(poi.position, candidate.position)
            if distance < min_distance:
                min_distance = distance
                nearest = candidate
        
        return nearest
    
    def _ensure_path_continuity(self, path: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """
        Ensure path is continuous (all adjacent tiles are connected).
        
        If there are gaps, fills them in with intermediate tiles.
        """
        if len(path) < 2:
            return path
        
        continuous_path = [path[0]]
        
        for i in range(len(path) - 1):
            current = path[i]
            next_pos = path[i + 1]
            
            # Check if adjacent (including diagonals)
            dx = abs(next_pos[0] - current[0])
            dy = abs(next_pos[1] - current[1])
            
            if dx <= 1 and dy <= 1:
                # Adjacent, just add next position
                continuous_path.append(next_pos)
            else:
                # Not adjacent - fill in the gap with a line
                gap_path = self._generate_direct_path(current, next_pos)
                # Add all intermediate points (skip first as it's already in path)
                for pos in gap_path[1:]:
                    continuous_path.append(pos)
        
        return continuous_path


