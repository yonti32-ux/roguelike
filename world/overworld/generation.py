"""
World generation for the overworld map.

Generates terrain and places POIs according to configuration.
"""

import random
import math
from typing import List, Tuple, Optional, Dict

from .map import OverworldMap
from .terrain import TerrainType, TERRAIN_GRASS, TERRAIN_FOREST, TERRAIN_MOUNTAIN, TERRAIN_WATER, TERRAIN_PLAINS, TERRAIN_DESERT, get_terrain
from .config import OverworldConfig
from ..poi.base import PointOfInterest
from ..poi.types import DungeonPOI, VillagePOI, TownPOI, CampPOI
from ..generation.config import load_generation_config


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
        self.gen_config = load_generation_config()  # Load generation settings
        
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
        
        # Initialize faction manager with config-based counts
        try:
            from ..factions import FactionManager
            from systems.factions import FactionAlignment
            
            faction_counts = {
                FactionAlignment.GOOD: self.config.faction_counts.get("good", 2),
                FactionAlignment.NEUTRAL: self.config.faction_counts.get("neutral", 2),
                FactionAlignment.EVIL: self.config.faction_counts.get("evil", 2),
            }
            
            overworld.faction_manager = FactionManager(
                world_seed=self.seed,
                use_random_factions=True,
                faction_counts=faction_counts,
            )
            all_factions = overworld.faction_manager.get_all_factions()
            print(f"Faction manager initialized with {len(all_factions)} factions")
        except Exception as e:
            print(f"Warning: Failed to initialize faction manager: {e}")
            import traceback
            traceback.print_exc()
            # Continue without faction manager - POIs will be created without factions
            overworld.faction_manager = None
        
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
                # Use config-based terrain distribution
                rand = random.random()
                terrain = self._pick_terrain_from_config(rand, self.gen_config.terrain.initial_distribution)
                row.append(terrain)
            tiles.append(row)
        
        # Apply cellular automata smoothing to create biome regions
        # This creates clusters of similar terrain
        smoothing = self.gen_config.terrain.smoothing
        tiles = self._smooth_terrain(tiles, iterations=smoothing["iterations"])
        
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
        smoothing = self.gen_config.terrain.smoothing
        water_clustering = self.gen_config.terrain.water_clustering
        neighbor_radius = smoothing["neighbor_radius"]
        conversion_threshold = smoothing["conversion_threshold"]
        conversion_chance = smoothing["conversion_chance"]
        
        for _ in range(iterations):
            new_tiles = [row[:] for row in tiles]  # Copy current state
            
            for y in range(height):
                for x in range(width):
                    # Count neighbors of each terrain type
                    neighbor_counts = {}
                    
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
                        
                        # Use config-based conversion threshold and chance
                        if count >= conversion_threshold and random.random() < conversion_chance:
                            new_terrain = get_terrain(most_common_id)
                            if new_terrain:
                                new_tiles[y][x] = new_terrain
                    
                    # Special handling: prevent water from forming isolated lakes
                    # (water should cluster in larger bodies)
                    current_terrain = tiles[y][x]
                    if current_terrain.id == "water":
                        water_neighbors = neighbor_counts.get("water", 0)
                        min_neighbors = water_clustering["min_neighbors"]
                        isolation_chance = water_clustering["isolation_conversion_chance"]
                        # If surrounded by mostly non-water, convert to adjacent terrain
                        if water_neighbors < min_neighbors and random.random() < isolation_chance:
                            # Convert to most common non-water neighbor
                            non_water = [(tid, cnt) for tid, cnt in neighbor_counts.items() if tid != "water"]
                            if non_water:
                                new_terrain_id = max(non_water, key=lambda x: x[1])[0]
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
                
                # Realistic terrain placement rules (using config)
                refinement = self.gen_config.terrain.refinement
                
                # Forests prefer being near water or in grass/plains areas
                if current.id == "forest":
                    has_water = "water" in neighbors
                    has_grass_plains = any(t in neighbors for t in ["grass", "plains"])
                    # If isolated from water and in desert/mountain, might convert
                    isolation_chance = refinement["forest_isolation_chance"]
                    if not has_water and not has_grass_plains and random.random() < isolation_chance:
                        # Convert to nearby terrain type
                        if "grass" in neighbors or "plains" in neighbors:
                            tiles[y][x] = get_terrain(random.choice(["grass", "plains"])) or current
                
                # Deserts avoid water and forests
                elif current.id == "desert":
                    has_water = "water" in neighbors
                    has_forest = "forest" in neighbors
                    conversion_chance = refinement["desert_conversion_chance"]
                    if (has_water or has_forest) and random.random() < conversion_chance:
                        # Convert to plains or grass
                        tiles[y][x] = get_terrain(random.choice(["plains", "grass"])) or current
                
                # Mountains avoid water (but can be near it)
                elif current.id == "mountain":
                    water_threshold = refinement["mountain_water_threshold"]
                    conversion_chance = refinement["mountain_conversion_chance"]
                    has_water = neighbors.count("water") >= water_threshold
                    if has_water and random.random() < conversion_chance:
                        # Convert to forest or grass (mountainous coast)
                        tiles[y][x] = get_terrain(random.choice(["forest", "grass"])) or current
                
                # Add some variation: occasionally add small features
                # (e.g., small forest patches in plains)
                variation_chance = refinement["variation_chance"]
                if random.random() < variation_chance:
                    if current.id == "plains" and "forest" in neighbors:
                        tiles[y][x] = get_terrain("forest") or current
                    elif current.id == "grass" and "plains" in neighbors:
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
    
    def _pick_terrain_from_config(self, rand: float, distribution: Dict[str, float]) -> TerrainType:
        """
        Pick terrain type based on random value and distribution config.
        
        Args:
            rand: Random value between 0.0 and 1.0
            distribution: Dictionary mapping terrain IDs to cumulative weights
            
        Returns:
            TerrainType instance
        """
        cumulative = 0.0
        for terrain_id, weight in distribution.items():
            cumulative += weight
            if rand < cumulative:
                terrain = get_terrain(terrain_id)
                if terrain:
                    return terrain
        
        # Fallback to grass if distribution doesn't cover 1.0
        return TERRAIN_GRASS
    
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
        Calculate difficulty levels for all POIs using diverse random distribution.
        
        Uses weighted random distribution to create a good mix of levels:
        - More low-level POIs (levels 1-10)
        - Some mid-level POIs (levels 11-25)
        - Fewer high-level POIs (levels 26-50)
        
        POIs near the starting location have a slight level reduction to provide
        a gentler starting experience, while maintaining diversity overall.
        
        Different POI types can have slight level preferences but overall variation is high.
        
        Args:
            overworld: The overworld map
        """
        start_x, start_y = overworld.get_player_position()
        
        # Find max distance for distance normalization
        max_distance = 0.0
        for poi in overworld.get_all_pois():
            px, py = poi.position
            dx = px - start_x
            dy = py - start_y
            distance = math.sqrt(dx * dx + dy * dy)
            max_distance = max(max_distance, distance)
        
        # Define level ranges with weights for diverse distribution
        # This creates a natural distribution with more low-level content
        level_weights = []
        for level in range(self.config.base_level, self.config.max_level + 1):
            # Weight decreases as level increases (exponential decay)
            # This gives us more low-level POIs but still good high-level variety
            weight = math.exp(-level / 15.0)  # Adjust divisor to control distribution curve
            level_weights.append((level, weight))
        
        # POI type level preferences (slight bias, but still diverse)
        poi_type_bias = {
            "camp": -3,      # Camps tend to be lower level (bias towards lower levels)
            "village": -1,   # Villages slightly lower
            "town": 0,       # Towns neutral (full range)
            "dungeon": +3,   # Dungeons tend to be higher level (bias towards higher levels)
        }
        
        for poi in overworld.get_all_pois():
            # Calculate distance from starting location
            px, py = poi.position
            dx = px - start_x
            dy = py - start_y
            distance = math.sqrt(dx * dx + dy * dy)
            
            # Normalize distance (0 = at start, 1 = max distance)
            normalized_distance = distance / max_distance if max_distance > 0 else 0.0
            
            # Start with base weights
            weights = [wgt for _, wgt in level_weights]
            levels = [lvl for lvl, _ in level_weights]
            
            # Apply POI type bias (shift weights towards higher/lower levels)
            poi_bias = poi_type_bias.get(poi.poi_type, 0)
            if poi_bias != 0:
                adjusted_weights = []
                mid_level = (self.config.base_level + self.config.max_level) / 2.0
                for level, weight in level_weights:
                    # Calculate distance from mid-level
                    level_diff = (level - mid_level) / (self.config.max_level - self.config.base_level) if (self.config.max_level - self.config.base_level) > 0 else 0
                    # Positive bias increases weight for higher levels, negative for lower
                    bias_factor = 1.0 + (poi_bias * 0.15 * level_diff)
                    adjusted_weights.append(weight * max(0.1, bias_factor))
                weights = adjusted_weights
            
            # Apply distance-based modifier: reduce levels near starting location
            # Near start (normalized_distance < 0.3): reduce levels by up to 40%
            # Far from start (normalized_distance > 0.7): no reduction
            # Uses smooth curve for gradual transition
            if normalized_distance < 0.3:
                # Strong reduction near start
                distance_modifier = 0.6 + (normalized_distance / 0.3) * 0.4  # 0.6 to 1.0
            elif normalized_distance < 0.7:
                # Gradual transition
                distance_modifier = 1.0 - ((0.7 - normalized_distance) / 0.4) * 0.2  # 0.8 to 1.0
            else:
                # No reduction far from start
                distance_modifier = 1.0
            
            # Apply distance modifier to weights (reduce probability of higher levels near start)
            if distance_modifier < 1.0:
                adjusted_weights = []
                mid_level = (self.config.base_level + self.config.max_level) / 2.0
                for level, weight in level_weights:
                    # Reduce weight more for higher levels when near start
                    level_normalized = (level - self.config.base_level) / (self.config.max_level - self.config.base_level) if (self.config.max_level - self.config.base_level) > 0 else 0
                    # Higher levels get more reduction
                    reduction = 1.0 - ((1.0 - distance_modifier) * level_normalized)
                    adjusted_weights.append(weight * max(0.1, reduction))
                weights = adjusted_weights
            
            # Normalize weights
            total_weight = sum(weights)
            if total_weight > 0:
                weights = [w / total_weight for w in weights]
            
            # Select level using weighted random
            level = random.choices(levels, weights=weights, k=1)[0]
            
            # Ensure level is in valid range
            level = max(self.config.base_level, min(level, self.config.max_level))
            
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
        # Try to find a walkable tile (prefer configured terrain types)
        max_attempts = 100
        preferred_terrain = self.gen_config.poi.preferred_starting_terrain
        for _ in range(max_attempts):
            x = random.randint(0, overworld.width - 1)
            y = random.randint(0, overworld.height - 1)
            
            if overworld.is_walkable(x, y):
                tile = overworld.get_tile(x, y)
                # Prefer starting on configured terrain types
                if tile and tile.id in preferred_terrain:
                    return (x, y)
        
        # Fallback: any walkable tile
        for y in range(overworld.height):
            for x in range(overworld.width):
                if overworld.is_walkable(x, y):
                    return (x, y)
        
        # Last resort: center of map
        return (overworld.width // 2, overworld.height // 2)

