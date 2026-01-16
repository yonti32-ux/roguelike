"""
Overworld map container.

Manages the overworld map, player position, explored tiles, and POIs.
"""

from typing import Dict, List, Optional, Set, Tuple, TYPE_CHECKING
from .terrain import TerrainType, TERRAIN_GRASS

if TYPE_CHECKING:
    from ..poi.base import PointOfInterest
    from .party_manager import PartyManager
    from world.time.time_system import TimeSystem


class OverworldMap:
    """
    Main overworld map container.
    
    For Phase 1, this is a simple 2D grid without region chunking.
    Region system will be added in Phase 3.
    """
    
    def __init__(
        self,
        width: int,
        height: int,
        seed: Optional[int] = None,
        tiles: Optional[List[List[TerrainType]]] = None,
    ) -> None:
        """
        Initialize the overworld map.
        
        Args:
            width: Map width in tiles
            height: Map height in tiles
            seed: Random seed used for generation
            tiles: Pre-generated tile data (2D list). If None, fills with grass.
        """
        self.width = width
        self.height = height
        self.seed = seed
        
        # Tile data: tiles[y][x] = TerrainType
        if tiles is not None:
            self.tiles = tiles
        else:
            # Fill with default terrain (grass)
            self.tiles = [[TERRAIN_GRASS for _ in range(width)] for _ in range(height)]
        
        # Player state
        self.player_position: Tuple[int, int] = (0, 0)
        # Track when each tile was last seen (for time-based visibility)
        # Key: (x, y) tuple, Value: timestamp in hours (from TimeSystem)
        self.explored_tiles: Dict[Tuple[int, int], float] = {}
        
        # POIs stored by ID
        self.pois: Dict[str, "PointOfInterest"] = {}
        
        # Roaming parties
        from .party_manager import PartyManager
        self.party_manager: Optional["PartyManager"] = PartyManager(self)
        
        # Faction manager (use world seed for deterministic generation)
        # Note: Faction counts will be set when config is available
        from ..factions import FactionManager
        self.faction_manager: Optional["FactionManager"] = None
        
        # Mark starting position as explored (with no timestamp - will be updated when player moves)
        # Using a very old timestamp so it will expire quickly if time system isn't available
        self.explore_tile(self.player_position[0], self.player_position[1], current_time=-999999.0)
    
    def get_tile(self, x: int, y: int) -> Optional[TerrainType]:
        """
        Get the terrain type at the given tile coordinates.
        
        Args:
            x: Tile X coordinate
            y: Tile Y coordinate
            
        Returns:
            TerrainType at that position, or None if out of bounds
        """
        if not self.in_bounds(x, y):
            return None
        return self.tiles[y][x]
    
    def set_tile(self, x: int, y: int, terrain: TerrainType) -> bool:
        """
        Set the terrain type at the given tile coordinates.
        
        Args:
            x: Tile X coordinate
            y: Tile Y coordinate
            terrain: TerrainType to set
            
        Returns:
            True if successful, False if out of bounds
        """
        if not self.in_bounds(x, y):
            return False
        self.tiles[y][x] = terrain
        return True
    
    def in_bounds(self, x: int, y: int) -> bool:
        """Check if coordinates are within map bounds."""
        return 0 <= x < self.width and 0 <= y < self.height
    
    def is_walkable(self, x: int, y: int) -> bool:
        """
        Check if a tile is walkable.
        
        Args:
            x: Tile X coordinate
            y: Tile Y coordinate
            
        Returns:
            True if walkable, False otherwise
        """
        tile = self.get_tile(x, y)
        if tile is None:
            return False
        return tile.walkable
    
    def explore_tile(self, x: int, y: int, current_time: Optional[float] = None) -> None:
        """
        Mark a tile as explored.
        
        Args:
            x: Tile X coordinate
            y: Tile Y coordinate
            current_time: Current time in hours (from TimeSystem.get_total_hours()).
                         If None, tile will be marked but without timestamp (for backwards compatibility).
        """
        if self.in_bounds(x, y):
            if current_time is not None:
                self.explored_tiles[(x, y)] = current_time
            else:
                # For backwards compatibility, use a very old timestamp so it expires quickly
                # This handles cases where time isn't provided
                self.explored_tiles[(x, y)] = -999999.0
    
    def is_explored(self, x: int, y: int, current_time: Optional[float] = None, timeout_hours: float = 2.0) -> bool:
        """
        Check if a tile has been explored and is still visible (within timeout).
        
        Args:
            x: Tile X coordinate
            y: Tile Y coordinate
            current_time: Current time in hours. If None, uses old behavior (always visible once explored).
            timeout_hours: Hours after which explored tiles fade out. Default 2.0 hours.
        
        Returns:
            True if tile was explored and is still within timeout period
        """
        tile_pos = (x, y)
        if tile_pos not in self.explored_tiles:
            return False
        
        # If no current_time provided, use old behavior (always visible once explored)
        if current_time is None:
            return True
        
        # Check if tile was seen within timeout period
        last_seen = self.explored_tiles[tile_pos]
        time_since_seen = current_time - last_seen
        return time_since_seen <= timeout_hours
    
    def set_player_position(self, x: int, y: int, sight_radius: int = 8, current_time: Optional[float] = None) -> bool:
        """
        Set the player's position on the overworld.
        
        Args:
            x: Tile X coordinate
            y: Tile Y coordinate
            sight_radius: Radius of tiles to explore around player
            current_time: Current time in hours (from TimeSystem.get_total_hours())
            
        Returns:
            True if position is valid and set, False otherwise
        """
        if not self.in_bounds(x, y):
            return False
        if not self.is_walkable(x, y):
            return False
        
        self.player_position = (x, y)
        
        # Explore tiles within sight radius (circular area)
        self.explore_area(x, y, sight_radius, current_time)
        return True
    
    def explore_area(self, center_x: int, center_y: int, radius: int, current_time: Optional[float] = None) -> None:
        """
        Explore all tiles within a radius of the center point.
        
        Args:
            center_x: Center X coordinate
            center_y: Center Y coordinate
            radius: Exploration radius in tiles
            current_time: Current time in hours (from TimeSystem.get_total_hours())
        """
        radius_sq = radius * radius
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                # Check if within circular radius
                dist_sq = dx * dx + dy * dy
                if dist_sq > radius_sq:
                    continue
                
                x = center_x + dx
                y = center_y + dy
                
                if self.in_bounds(x, y):
                    self.explore_tile(x, y, current_time)
    
    def get_player_position(self) -> Tuple[int, int]:
        """Get the player's current position."""
        return self.player_position
    
    def add_poi(self, poi: "PointOfInterest") -> None:  # type: ignore
        """Add a POI to the map."""
        self.pois[poi.poi_id] = poi
    
    def get_poi_at(self, x: int, y: int) -> Optional["PointOfInterest"]:  # type: ignore
        """
        Get the POI at the given coordinates, if any.
        
        Args:
            x: Tile X coordinate
            y: Tile Y coordinate
            
        Returns:
            PointOfInterest at that position, or None
        """
        for poi in self.pois.values():
            if poi.position == (x, y):
                return poi
        return None
    
    def get_pois_in_range(
        self,
        center_x: int,
        center_y: int,
        radius: int,
    ) -> List["PointOfInterest"]:  # type: ignore
        """
        Get all POIs within a certain radius of a position.
        
        Args:
            center_x: Center X coordinate
            center_y: Center Y coordinate
            radius: Search radius in tiles
            
        Returns:
            List of POIs within range
        """
        result = []
        radius_sq = radius * radius
        
        for poi in self.pois.values():
            px, py = poi.position
            dx = px - center_x
            dy = py - center_y
            dist_sq = dx * dx + dy * dy
            
            if dist_sq <= radius_sq:
                result.append(poi)
        
        return result
    
    def get_all_pois(self) -> List["PointOfInterest"]:  # type: ignore
        """Get all POIs on the map."""
        return list(self.pois.values())

