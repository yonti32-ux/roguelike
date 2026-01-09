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
        Generate terrain for the overworld with biome coherence.
        
        Uses a two-pass approach:
        1. Generate biome regions using cellular automata-like clustering
        2. Smooth and refine terrain transitions
        
        Returns:
            2D list of TerrainType
        """
        # Initialize with random terrain (seed for biome centers)
        tiles = []
        for y in range(self.config.world_height):
            row = []
            for x in range(self.config.world_width):
                # Initial random distribution (more varied for biome seeding)
                rand = random.random()
                if rand < 0.35:
                    terrain = TERRAIN_GRASS
                elif rand < 0.55:
                    terrain = TERRAIN_PLAINS
                elif rand < 0.70:
                    terrain = TERRAIN_FOREST
                elif rand < 0.82:
                    terrain = TERRAIN_MOUNTAIN
                elif rand < 0.92:
                    terrain = TERRAIN_DESERT
                else:
                    terrain = TERRAIN_WATER
                row.append(terrain)
            tiles.append(row)
        
        # Apply cellular automata smoothing to create biome regions
        # This creates clusters of similar terrain
        tiles = self._smooth_terrain(tiles, iterations=3)
        
        # Add some variation and refine transitions
        tiles = self._refine_terrain(tiles)
        
        return tiles
    
    def _smooth_terrain(self, tiles: List[List[TerrainType]], iterations: int = 3) -> List[List[TerrainType]]:
        """
        Smooth terrain using cellular automata to create biome regions.
        
        For each tile, look at neighbors and if most neighbors are the same type,
        convert the tile to match (with some randomness for variation).
        """
        width = len(tiles[0])
        height = len(tiles)
        
        for _ in range(iterations):
            new_tiles = [row[:] for row in tiles]  # Copy current state
            
            for y in range(height):
                for x in range(width):
                    # Count neighbors of each terrain type
                    neighbor_counts = {}
                    neighbor_radius = 1
                    
                    for dy in range(-neighbor_radius, neighbor_radius + 1):
                        for dx in range(-neighbor_radius, neighbor_radius + 1):
                            if dx == 0 and dy == 0:
                                continue  # Skip center tile
                            
                            nx = x + dx
                            ny = y + dy
                            
                            if 0 <= nx < width and 0 <= ny < height:
                                neighbor_terrain = tiles[ny][nx]
                                terrain_id = neighbor_terrain.id
                                neighbor_counts[terrain_id] = neighbor_counts.get(terrain_id, 0) + 1
                    
                    # Find most common neighbor terrain type
                    if neighbor_counts:
                        most_common = max(neighbor_counts.items(), key=lambda x: x[1])
                        most_common_id, count = most_common
                        
                        # If at least 4 neighbors are the same type, convert this tile
                        # (with some randomness to avoid complete uniformity)
                        if count >= 4 and random.random() < 0.6:
                            from .terrain import get_terrain
                            new_terrain = get_terrain(most_common_id)
                            if new_terrain:
                                new_tiles[y][x] = new_terrain
                    
                    # Special handling: prevent water from forming isolated lakes
                    # (water should cluster in larger bodies)
                    current_terrain = tiles[y][x]
                    if current_terrain.id == "water":
                        water_neighbors = neighbor_counts.get("water", 0)
                        # If surrounded by mostly non-water, convert to adjacent terrain
                        if water_neighbors < 2 and random.random() < 0.3:
                            # Convert to most common non-water neighbor
                            non_water = [(tid, cnt) for tid, cnt in neighbor_counts.items() if tid != "water"]
                            if non_water:
                                new_terrain_id = max(non_water, key=lambda x: x[1])[0]
                                from .terrain import get_terrain
                                new_terrain = get_terrain(new_terrain_id)
                                if new_terrain:
                                    new_tiles[y][x] = new_terrain
            
            tiles = new_tiles
        
        return tiles
    
    def _refine_terrain(self, tiles: List[List[TerrainType]]) -> List[List[TerrainType]]:
        """
        Refine terrain transitions and add some realistic placement rules.
        
        - Forests tend to be near water or grass
        - Mountains tend to cluster and avoid water
        - Deserts avoid water and forests
        - Water should form coherent bodies
        """
        width = len(tiles[0])
        height = len(tiles)
        
        for y in range(height):
            for x in range(width):
                current = tiles[y][x]
                
                # Skip water (already handled in smoothing)
                if current.id == "water":
                    continue
                
                # Count neighboring terrain types
                neighbors = self._get_neighbor_terrain_types(tiles, x, y, width, height)
                
                # Realistic terrain placement rules
                
                # Forests prefer being near water or in grass/plains areas
                if current.id == "forest":
                    has_water = "water" in neighbors
                    has_grass_plains = any(t in neighbors for t in ["grass", "plains"])
                    # If isolated from water and in desert/mountain, might convert
                    if not has_water and not has_grass_plains and random.random() < 0.15:
                        # Convert to nearby terrain type
                        if "grass" in neighbors or "plains" in neighbors:
                            from .terrain import get_terrain
                            tiles[y][x] = get_terrain(random.choice(["grass", "plains"])) or current
                
                # Deserts avoid water and forests
                elif current.id == "desert":
                    has_water = "water" in neighbors
                    has_forest = "forest" in neighbors
                    if (has_water or has_forest) and random.random() < 0.25:
                        # Convert to plains or grass
                        from .terrain import get_terrain
                        tiles[y][x] = get_terrain(random.choice(["plains", "grass"])) or current
                
                # Mountains avoid water (but can be near it)
                elif current.id == "mountain":
                    has_water = neighbors.count("water") >= 3
                    if has_water and random.random() < 0.2:
                        # Convert to forest or grass (mountainous coast)
                        from .terrain import get_terrain
                        tiles[y][x] = get_terrain(random.choice(["forest", "grass"])) or current
                
                # Add some variation: occasionally add small features
                # (e.g., small forest patches in plains)
                if random.random() < 0.02:  # 2% chance
                    if current.id == "plains" and "forest" in neighbors:
                        from .terrain import get_terrain
                        tiles[y][x] = get_terrain("forest") or current
                    elif current.id == "grass" and "plains" in neighbors:
                        from .terrain import get_terrain
                        tiles[y][x] = get_terrain("plains") or current
        
        return tiles
    
    def _get_neighbor_terrain_types(
        self, 
        tiles: List[List[TerrainType]], 
        x: int, 
        y: int, 
        width: int, 
        height: int
    ) -> List[str]:
        """Get list of neighbor terrain type IDs."""
        neighbors = []
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                if dx == 0 and dy == 0:
                    continue
                
                nx = x + dx
                ny = y + dy
                
                if 0 <= nx < width and 0 <= ny < height:
                    neighbors.append(tiles[ny][nx].id)
        
        return neighbors
    
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

