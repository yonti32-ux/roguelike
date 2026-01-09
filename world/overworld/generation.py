"""
World generation for the overworld map.

Generates terrain and places POIs according to configuration.
"""

import random
import math
from typing import List, Tuple, Optional, Dict

from .map import OverworldMap
from .terrain import TerrainType, TERRAIN_GRASS, TERRAIN_FOREST, TERRAIN_MOUNTAIN, TERRAIN_WATER, TERRAIN_PLAINS, TERRAIN_DESERT
from .config import OverworldConfig
from ..poi.base import PointOfInterest
from ..poi.types import DungeonPOI, VillagePOI, TownPOI, CampPOI


class WorldGenerator:
    """
    Generates the overworld map with terrain and POIs.
    """
    
    def __init__(self, config: OverworldConfig, seed: Optional[int] = None) -> None:
        """
        Initialize the world generator.
        
        Args:
            config: Overworld configuration
            seed: Random seed (if None, uses config seed or generates new)
        """
        self.config = config
        
        # Use provided seed, config seed, or generate new
        if seed is not None:
            self.seed = seed
        elif config.seed is not None:
            self.seed = config.seed
        else:
            self.seed = random.randint(0, 2**31 - 1)
        
        random.seed(self.seed)
    
    def generate(self) -> OverworldMap:
        """
        Generate a complete overworld map.
        
        Steps:
        1. Generate terrain
        2. Set starting location
        3. Place POIs
        4. Calculate POI levels
        5. Return complete map
        
        Returns:
            Complete OverworldMap instance
        """
        print("Generating overworld terrain...")
        # Generate terrain
        tiles = self._generate_terrain()
        print(f"Terrain generated: {len(tiles)}x{len(tiles[0]) if tiles else 0}")
        
        # Create map
        overworld = OverworldMap(
            width=self.config.world_width,
            height=self.config.world_height,
            seed=self.seed,
            tiles=tiles,
        )
        
        # Set starting location FIRST (needed for POI level calculation)
        start_x, start_y = self._set_starting_location(overworld)
        # Explore area around starting location with full sight radius
        overworld.set_player_position(start_x, start_y, sight_radius=self.config.sight_radius)
        print(f"Starting location: ({start_x}, {start_y})")
        
        # Place POIs
        print("Placing POIs...")
        pois = self._place_pois(overworld)
        for poi in pois:
            overworld.add_poi(poi)
        print(f"Placed {len(pois)} POIs")
        
        # Calculate POI levels based on distance from start
        print("Calculating POI levels...")
        self._calculate_poi_levels(overworld)
        
        print("Overworld generation complete!")
        return overworld
    
    def _generate_terrain(self) -> List[List[TerrainType]]:
        """
        Generate terrain for the overworld.
        
        For Phase 1, uses a simple random distribution.
        Can be enhanced later with biomes, noise, etc.
        
        Returns:
            2D list of TerrainType
        """
        tiles = []
        
        for y in range(self.config.world_height):
            row = []
            for x in range(self.config.world_width):
                # Simple random terrain distribution
                rand = random.random()
                
                if rand < 0.4:
                    terrain = TERRAIN_GRASS
                elif rand < 0.6:
                    terrain = TERRAIN_PLAINS
                elif rand < 0.75:
                    terrain = TERRAIN_FOREST
                elif rand < 0.85:
                    terrain = TERRAIN_MOUNTAIN
                elif rand < 0.95:
                    terrain = TERRAIN_DESERT
                else:
                    terrain = TERRAIN_WATER
                
                row.append(terrain)
            tiles.append(row)
        
        return tiles
    
    def _place_pois(self, overworld: OverworldMap) -> List[PointOfInterest]:
        """
        Place POIs on the overworld according to configuration.
        
        Args:
            overworld: The overworld map to place POIs on
            
        Returns:
            List of placed POIs
        """
        from ..poi.placement import place_pois
        
        return place_pois(overworld, self.config)
    
    def _calculate_poi_levels(self, overworld: OverworldMap) -> None:
        """
        Calculate difficulty levels for all POIs based on distance from start.
        
        Args:
            overworld: The overworld map
        """
        start_x, start_y = overworld.get_player_position()
        
        for poi in overworld.get_all_pois():
            px, py = poi.position
            
            # Calculate distance from starting location
            dx = px - start_x
            dy = py - start_y
            distance = math.sqrt(dx * dx + dy * dy)
            
            # Calculate level based on distance
            if self.config.difficulty_scaling == "distance":
                level = int(self.config.base_level + (distance * self.config.level_per_distance))
            else:
                # Default to base level
                level = self.config.base_level
            
            # Clamp to valid range
            level = max(1, min(level, self.config.max_level))
            
            poi.level = level
    
    def _set_starting_location(self, overworld: OverworldMap) -> Tuple[int, int]:
        """
        Set the starting location for the player.
        
        Args:
            overworld: The overworld map
            
        Returns:
            Starting position (x, y)
        """
        if self.config.starting_location_type == "fixed":
            if (self.config.starting_location_x is not None and
                self.config.starting_location_y is not None):
                x = self.config.starting_location_x
                y = self.config.starting_location_y
                if overworld.in_bounds(x, y) and overworld.is_walkable(x, y):
                    return (x, y)
        
        # Random starting location
        # Try to find a walkable tile (prefer grass/plains)
        max_attempts = 100
        for _ in range(max_attempts):
            x = random.randint(0, overworld.width - 1)
            y = random.randint(0, overworld.height - 1)
            
            if overworld.is_walkable(x, y):
                tile = overworld.get_tile(x, y)
                # Prefer starting on grass or plains
                if tile and tile.id in ("grass", "plains"):
                    return (x, y)
        
        # Fallback: any walkable tile
        for y in range(overworld.height):
            for x in range(overworld.width):
                if overworld.is_walkable(x, y):
                    return (x, y)
        
        # Last resort: center of map
        return (overworld.width // 2, overworld.height // 2)

