"""
World generation for the overworld map.

Generates terrain and places POIs according to configuration.
"""

import random
import math
from typing import List, Tuple, Optional, Dict

from .map import OverworldMap
from .terrain import TerrainType, TERRAIN_GRASS, TERRAIN_FOREST, TERRAIN_MOUNTAIN, TERRAIN_WATER, TERRAIN_PLAINS, TERRAIN_DESERT, TERRAIN_BEACH, TERRAIN_SNOW, get_terrain
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
        Generate terrain for the overworld using chunk-based biome system.
        
        Uses a chunk-based approach:
        1. Divide world into chunks (using region_size)
        2. Assign primary biome to each chunk with coherent placement
        3. Generate terrain within chunks based on assigned biome
        4. Add smooth transitions between chunk boundaries
        
        Returns:
            2D list of TerrainType
        """
        # Check if chunk-based generation is enabled
        chunk_config = self.gen_config.terrain.chunk_based
        if chunk_config and chunk_config.get('enabled', False):
            return self._generate_chunk_based_terrain()
        else:
            # Fallback to old method for backward compatibility
            return self._generate_legacy_terrain()
    
    def _generate_chunk_based_terrain(self) -> List[List[TerrainType]]:
        """
        Generate terrain using region-based biome assignment with organic shapes.
        
        Uses smaller regions with varied sizes and organic boundaries instead of
        perfect square chunks.
        
        Returns:
            2D list of TerrainType
        """
        chunk_config = self.gen_config.terrain.chunk_based
        
        # Use smaller base region size for more variety
        base_region_size = chunk_config.get('base_region_size', 16)
        region_size_variance = chunk_config.get('region_size_variance', 0.4)
        
        # Use heightmap-based generation for realistic terrain
        use_heightmap = chunk_config.get('use_heightmap', True)
        
        if use_heightmap:
            # Realistic heightmap-based generation
            tiles = self._generate_heightmap_terrain(chunk_config)
            # Apply smoothing to blend transitions and remove straight lines
            smoothing_iterations = chunk_config.get('smoothing_iterations', 5)
            tiles = self._smooth_terrain(tiles, iterations=smoothing_iterations)
        else:
            # Fallback to old method
            tiles = self._generate_organic_biome_regions(chunk_config, base_region_size, region_size_variance)
            tiles = self._generate_water_bodies(tiles, chunk_config)
            smoothing_iterations = chunk_config.get('smoothing_iterations', 4)
            tiles = self._smooth_terrain(tiles, iterations=smoothing_iterations)
            tiles = self._ensure_biome_diversity(tiles, chunk_config)
        
        # Final refinement pass
        tiles = self._refine_terrain(tiles)
        
        return tiles
    
    def _ensure_biome_diversity(
        self, tiles: List[List[TerrainType]], chunk_config: Dict
    ) -> List[List[TerrainType]]:
        """
        Ensure all biomes appear in the map by adding small patches of underrepresented biomes.
        """
        width = len(tiles[0])
        height = len(tiles)
        
        # Count biome frequencies
        biome_counts = {}
        total_tiles = width * height
        
        for y in range(height):
            for x in range(width):
                biome_id = tiles[y][x].id
                biome_counts[biome_id] = biome_counts.get(biome_id, 0) + 1
        
        # Get expected distribution
        biome_distribution = chunk_config.get(
            'biome_distribution',
            self.gen_config.terrain.initial_distribution
        )
        total_weight = sum(biome_distribution.values())
        
        # Find underrepresented biomes and add patches
        new_tiles = [row[:] for row in tiles]
        diversity_chance = chunk_config.get('diversity_patch_chance', 0.05)  # Increased
        
        for biome_id, expected_weight in biome_distribution.items():
            if total_weight == 0:
                continue
            
            expected_frequency = expected_weight / total_weight
            actual_frequency = biome_counts.get(biome_id, 0) / total_tiles if total_tiles > 0 else 0
            
            # If biome is underrepresented (less than 70% of expected), add patches
            if actual_frequency < expected_frequency * 0.7:
                # Calculate how many patches to add
                deficit = (expected_frequency - actual_frequency) * total_tiles
                patches_to_add = int(deficit * 0.5)  # Add 50% of deficit
                
                # Skip water in diversity pass - it's handled separately
                if biome_id == "water":
                    continue
                else:
                    # For other biomes, add scattered patches
                    for _ in range(patches_to_add):
                        if random.random() < diversity_chance:
                            # Pick a random location
                            x = random.randint(1, width - 2)
                            y = random.randint(1, height - 2)
                            
                            # Only place if it makes sense (near biome boundaries or variety)
                            neighbors = self._get_neighbor_terrain_types(tiles, x, y, width, height)
                            if len(set(neighbors)) > 1:  # If there's variety nearby, it's okay to place
                                terrain = get_terrain(biome_id)
                                if terrain:
                                    new_tiles[y][x] = terrain
                                    
                                    # Sometimes add a small cluster (2-3 tiles)
                                    if random.random() < 0.3:
                                        for dy in [-1, 0, 1]:
                                            for dx in [-1, 0, 1]:
                                                if dx == 0 and dy == 0:
                                                    continue
                                                nx = x + dx
                                                ny = y + dy
                                                if 0 <= nx < width and 0 <= ny < height:
                                                    if random.random() < 0.4:
                                                        new_tiles[ny][nx] = terrain
        
        return new_tiles
    
    def _generate_organic_biome_regions(
        self, chunk_config: Dict, base_region_size: int, region_size_variance: float
    ) -> List[List[TerrainType]]:
        """
        Generate terrain with organic biome regions using multi-scale noise.
        
        Creates varied, non-square biome regions by using noise at different scales
        and combining them.
        """
        width = self.config.world_width
        height = self.config.world_height
        
        # Get biome distribution
        biome_distribution = chunk_config.get(
            'biome_distribution',
            self.gen_config.terrain.initial_distribution
        )
        
        # Initialize terrain grid
        tiles = []
        for y in range(height):
            row = []
            for x in range(width):
                row.append(TERRAIN_GRASS)  # Default
            tiles.append(row)
        
        # Use multiple noise scales to create varied regions
        noise_scales = chunk_config.get('noise_scales', [0.05, 0.15, 0.3])
        noise_weights = chunk_config.get('noise_weights', [0.5, 0.3, 0.2])
        
        # Normalize biome distribution weights to sum to 1.0
        total_weight = sum(biome_distribution.values())
        if total_weight > 0:
            normalized_distribution = {k: v / total_weight for k, v in biome_distribution.items()}
        else:
            normalized_distribution = biome_distribution
        
        # Generate biome map using combined noise
        for y in range(height):
            for x in range(width):
                # Combine multiple noise scales
                combined_noise = 0.0
                total_weight = 0.0
                
                for scale, weight in zip(noise_scales, noise_weights):
                    noise_val = self._tile_noise(x, y, scale)
                    combined_noise += noise_val * weight
                    total_weight += weight
                
                if total_weight > 0:
                    combined_noise /= total_weight
                
                # Normalize to [0, 1]
                normalized = (combined_noise + 1.0) / 2.0
                
                # Add more randomness to ensure all biomes can appear
                # This prevents noise clustering from excluding certain biomes
                rand_adjustment = (random.random() - 0.5) * 0.5  # ±25% adjustment for more variety
                normalized = max(0.0, min(1.0, normalized + rand_adjustment))
                
                # Pick biome based on noise value
                biome = self._pick_terrain_from_config(normalized, normalized_distribution)
                tiles[y][x] = biome
        
        # Apply local coherence to create regions (but keep it minimal for variety)
        coherence_radius = chunk_config.get('coherence_radius', 2)
        coherence_strength = chunk_config.get('coherence_strength', 0.15)  # Even lower for more variety
        
        # Pass to increase local coherence (create small regions, not huge ones)
        # Only do 1 pass to preserve more variety
        for _ in range(1):
            new_tiles = [row[:] for row in tiles]
            
            for y in range(height):
                for x in range(width):
                    # Count neighbors
                    neighbor_counts = {}
                    for dy in range(-coherence_radius, coherence_radius + 1):
                        for dx in range(-coherence_radius, coherence_radius + 1):
                            if dx == 0 and dy == 0:
                                continue
                            
                            nx = x + dx
                            ny = y + dy
                            
                            if 0 <= nx < width and 0 <= ny < height:
                                neighbor_terrain = tiles[ny][nx]
                                terrain_id = neighbor_terrain.id
                                neighbor_counts[terrain_id] = neighbor_counts.get(terrain_id, 0) + 1
                    
                    # If most neighbors are the same, consider matching
                    # But use a lower threshold to prevent huge uniform regions
                    if neighbor_counts:
                        most_common = max(neighbor_counts.items(), key=lambda x: x[1])
                        most_common_id, count = most_common
                        total_neighbors = sum(neighbor_counts.values())
                        
                        # Higher threshold (60%) and lower strength to keep regions smaller and more varied
                        if count >= total_neighbors * 0.6 and total_neighbors >= 4:
                            if random.random() < coherence_strength:
                                new_terrain = get_terrain(most_common_id)
                                if new_terrain:
                                    new_tiles[y][x] = new_terrain
            
            tiles = new_tiles
        
        return tiles
    
    def _tile_noise(self, x: int, y: int, scale: float) -> float:
        """
        Generate noise value for a specific tile coordinate.
        Uses multiple octaves for smoother, more natural patterns.
        """
        # Use tile coordinates with seed for determinism
        value = 0.0
        amplitude = 1.0
        frequency = scale
        total_amplitude = 0.0
        
        # Multiple octaves for natural-looking noise
        for octave in range(4):
            # Sample at different frequencies
            sample_x = x * frequency
            sample_y = y * frequency
            
            # Generate deterministic pseudo-random value
            hash_val = hash((int(sample_x * 1000), int(sample_y * 1000), self.seed, octave)) % 1000000
            normalized = (hash_val / 1000000.0) * 2.0 - 1.0  # [-1, 1]
            
            value += normalized * amplitude
            total_amplitude += amplitude
            
            # Next octave
            amplitude *= 0.5
            frequency *= 2.0
        
        # Normalize
        if total_amplitude > 0:
            value /= total_amplitude
        
        return value
    
    def _generate_heightmap_terrain(self, chunk_config: Dict) -> List[List[TerrainType]]:
        """
        Generate realistic terrain using heightmap and moisture maps.
        This creates natural-looking biomes based on elevation and moisture,
        similar to how real-world biomes work.
        """
        width = self.config.world_width
        height = self.config.world_height
        
        # Initialize terrain grid
        tiles = []
        for y in range(height):
            row = []
            for x in range(width):
                row.append(TERRAIN_GRASS)  # Default
            tiles.append(row)
        
        # Generate heightmap using multi-octave noise
        heightmap = self._generate_heightmap(width, height, chunk_config)
        
        # Generate moisture map (for biome diversity)
        moisture_map = self._generate_moisture_map(width, height, chunk_config)
        
        # Assign biomes based on height and moisture
        tiles = self._assign_biomes_from_heightmap(
            tiles, heightmap, moisture_map, chunk_config
        )
        
        return tiles
    
    def _generate_heightmap(
        self, width: int, height: int, chunk_config: Dict
    ) -> List[List[float]]:
        """
        Generate a heightmap using multi-octave Perlin-like noise.
        Returns values in range [-1, 1] where -1 is lowest (water level) and 1 is highest (mountains).
        """
        heightmap = []
        
        # Noise parameters
        base_scale = chunk_config.get('heightmap_scale', 0.05)
        octaves = chunk_config.get('heightmap_octaves', 4)
        persistence = chunk_config.get('heightmap_persistence', 0.5)
        lacunarity = chunk_config.get('heightmap_lacunarity', 2.0)
        
        for y in range(height):
            row = []
            for x in range(width):
                value = 0.0
                amplitude = 1.0
                frequency = base_scale
                max_value = 0.0
                
                # Multi-octave noise
                for octave in range(octaves):
                    noise_val = self._perlin_noise(x * frequency, y * frequency, self.seed + octave)
                    value += noise_val * amplitude
                    max_value += amplitude
                    amplitude *= persistence
                    frequency *= lacunarity
                
                # Normalize
                if max_value > 0:
                    value /= max_value
                
                row.append(value)
            heightmap.append(row)
        
        return heightmap
    
    def _generate_moisture_map(
        self, width: int, height: int, chunk_config: Dict
    ) -> List[List[float]]:
        """
        Generate a moisture map for biome diversity.
        Returns values in range [0, 1] where 0 is dry and 1 is wet.
        """
        moisture_map = []
        
        # Use different seed offset for moisture
        moisture_seed = self.seed + 10000
        base_scale = chunk_config.get('moisture_scale', 0.08)
        octaves = chunk_config.get('moisture_octaves', 3)
        persistence = chunk_config.get('moisture_persistence', 0.6)
        lacunarity = chunk_config.get('moisture_lacunarity', 2.0)
        
        for y in range(height):
            row = []
            for x in range(width):
                value = 0.0
                amplitude = 1.0
                frequency = base_scale
                max_value = 0.0
                
                # Multi-octave noise
                for octave in range(octaves):
                    noise_val = self._perlin_noise(x * frequency, y * frequency, moisture_seed + octave)
                    value += noise_val * amplitude
                    max_value += amplitude
                    amplitude *= persistence
                    frequency *= lacunarity
                
                # Normalize to [0, 1]
                if max_value > 0:
                    value = (value / max_value + 1.0) / 2.0
                
                row.append(value)
            moisture_map.append(row)
        
        return moisture_map
    
    def _perlin_noise(self, x: float, y: float, seed: int) -> float:
        """
        Simplified Perlin-like noise function.
        Returns value in range [-1, 1].
        """
        # Use integer grid for gradient vectors
        X = int(x) & 255
        Y = int(y) & 255
        
        # Fractional parts
        xf = x - int(x)
        yf = y - int(y)
        
        # Fade curves
        u = self._fade(xf)
        v = self._fade(yf)
        
        # Hash function for gradients
        def hash_coords(ix, iy, seed_val):
            return hash((ix, iy, seed_val)) % 1000000
        
        # Get gradients for 4 corners
        n00 = self._grad(hash_coords(X, Y, seed), xf, yf)
        n01 = self._grad(hash_coords(X, Y + 1, seed), xf, yf - 1)
        n10 = self._grad(hash_coords(X + 1, Y, seed), xf - 1, yf)
        n11 = self._grad(hash_coords(X + 1, Y + 1, seed), xf - 1, yf - 1)
        
        # Interpolate
        x1 = self._lerp(n00, n10, u)
        x2 = self._lerp(n01, n11, u)
        return self._lerp(x1, x2, v)
    
    def _fade(self, t: float) -> float:
        """Fade function for smooth interpolation."""
        return t * t * t * (t * (t * 6 - 15) + 10)
    
    def _lerp(self, a: float, b: float, t: float) -> float:
        """Linear interpolation."""
        return a + t * (b - a)
    
    def _grad(self, hash_val: int, x: float, y: float) -> float:
        """Gradient function."""
        # Convert hash to gradient direction
        h = hash_val & 3
        if h == 0:
            return x
        elif h == 1:
            return -x
        elif h == 2:
            return y
        else:
            return -y
    
    def _assign_biomes_from_heightmap(
        self, tiles: List[List[TerrainType]], heightmap: List[List[float]],
        moisture_map: List[List[float]], chunk_config: Dict
    ) -> List[List[TerrainType]]:
        """
        Assign biomes based on height, moisture, and latitude (Y position).
        Creates geographic climate zones: desert in south, snow/mountains in north.
        """
        width = len(tiles[0])
        height = len(tiles)
        
        # Biome thresholds
        water_level = chunk_config.get('water_level', -0.3)
        lowland_threshold = chunk_config.get('lowland_threshold', 0.0)
        highland_threshold = chunk_config.get('highland_threshold', 0.4)
        mountain_threshold = chunk_config.get('mountain_threshold', 0.7)
        
        # Latitude zones with gradual blending (0 = south, 1 = north)
        south_zone = chunk_config.get('south_zone', 0.3)  # Bottom 30% is strongly south
        north_zone = chunk_config.get('north_zone', 0.3)  # Top 30% is strongly north
        transition_width = chunk_config.get('latitude_transition', 0.2)  # Gradual transition zone
        
        for y in range(height):
            # Calculate latitude (0 = south/bottom, 1 = north/top)
            latitude = y / height if height > 0 else 0.5
            
            # Calculate influence factors with smooth transitions
            # South influence: 1.0 at bottom (y=0), fades to 0.0
            south_influence = 0.0
            if latitude < south_zone:
                # Strong south influence in bottom zone
                south_influence = 1.0 - (latitude / south_zone)
            elif latitude < south_zone + transition_width:
                # Gradual fade in transition zone
                fade_dist = (latitude - south_zone) / transition_width
                south_influence = 1.0 - fade_dist
            
            # North influence: 0.0 at bottom, increases to 1.0 at top
            north_start = 1.0 - north_zone
            north_influence = 0.0
            if latitude > north_start:
                # Strong north influence in top zone
                north_influence = (latitude - north_start) / north_zone
            elif latitude > north_start - transition_width:
                # Gradual fade in transition zone
                fade_dist = (north_start - latitude) / transition_width
                north_influence = 1.0 - fade_dist
            
            # Determine zone with smooth blending
            is_strongly_south = south_influence > 0.6
            is_strongly_north = north_influence > 0.6
            is_south = south_influence > 0.2
            is_north = north_influence > 0.2
            
            for x in range(width):
                height_val = heightmap[y][x]
                moisture_val = moisture_map[y][x]
                
                # Check if near water (for beach)
                near_water = self._is_near_water(tiles, x, y, width, height)
                
                # Water (lowest areas)
                if height_val < water_level:
                    tiles[y][x] = TERRAIN_WATER
                # Beach around water sources
                elif near_water and height_val < water_level + 0.1:
                    tiles[y][x] = TERRAIN_BEACH
                # Northern mountains and snow (with blending)
                elif is_north:
                    # Very aggressive thresholds for north - create lots of snow and mountains
                    north_snow_threshold = highland_threshold + 0.05  # Snow appears at low-medium elevation
                    north_mountain_threshold = highland_threshold - 0.02  # Mountains start very early
                    
                    # In north, prioritize snow and mountains
                    if height_val > north_snow_threshold:
                        # Medium-high elevation in north = snow (very common)
                        tiles[y][x] = TERRAIN_SNOW
                    elif height_val > north_mountain_threshold:
                        # Medium elevation in north = mountains (or snow if strong north)
                        if north_influence > 0.4 or height_val > highland_threshold:
                            tiles[y][x] = TERRAIN_SNOW
                        else:
                            tiles[y][x] = TERRAIN_MOUNTAIN
                    elif height_val > highland_threshold - 0.05:
                        # Low-medium elevation in north = mountains or forest
                        if north_influence > 0.3:
                            tiles[y][x] = TERRAIN_MOUNTAIN
                        elif moisture_val > 0.5:
                            tiles[y][x] = TERRAIN_FOREST
                        elif moisture_val > 0.3:
                            tiles[y][x] = TERRAIN_GRASS
                        else:
                            tiles[y][x] = TERRAIN_PLAINS
                    elif height_val > lowland_threshold:
                        # Low-medium elevation in north = forest, grass, or plains (more forest)
                        if moisture_val > 0.5:
                            tiles[y][x] = TERRAIN_FOREST
                        elif moisture_val > 0.35:
                            tiles[y][x] = TERRAIN_GRASS
                        elif moisture_val > 0.2:
                            tiles[y][x] = TERRAIN_PLAINS
                        else:
                            tiles[y][x] = TERRAIN_GRASS
                    else:
                        # Low elevation in north = forest, grass, or plains (more forest)
                        if moisture_val > 0.45:
                            tiles[y][x] = TERRAIN_FOREST
                        elif moisture_val > 0.3:
                            tiles[y][x] = TERRAIN_GRASS
                        else:
                            tiles[y][x] = TERRAIN_PLAINS
                # Southern desert zone (with blending)
                elif is_south:
                    if height_val > mountain_threshold:
                        tiles[y][x] = TERRAIN_MOUNTAIN
                    elif height_val > highland_threshold:
                        # Highlands in south = mountains, forest, or grass
                        if moisture_val > 0.55:
                            tiles[y][x] = TERRAIN_FOREST
                        elif moisture_val > 0.3:
                            tiles[y][x] = TERRAIN_GRASS
                        else:
                            tiles[y][x] = TERRAIN_MOUNTAIN
                    elif height_val > lowland_threshold:
                        # Medium elevation in south = desert, plains, grass, or forest (more desert)
                        if moisture_val > 0.55:
                            tiles[y][x] = TERRAIN_FOREST
                        elif moisture_val > 0.4:
                            tiles[y][x] = TERRAIN_PLAINS
                        elif moisture_val > 0.25:
                            tiles[y][x] = TERRAIN_GRASS
                        elif moisture_val > 0.1:
                            # Mix of desert and grass - favor desert in south
                            if south_influence > 0.3:
                                tiles[y][x] = TERRAIN_DESERT
                            else:
                                tiles[y][x] = TERRAIN_GRASS
                        else:
                            tiles[y][x] = TERRAIN_DESERT
                    else:
                        # Low elevation in south = desert, plains, grass, or forest (more desert)
                        if moisture_val > 0.5:
                            tiles[y][x] = TERRAIN_FOREST
                        elif moisture_val > 0.35:
                            tiles[y][x] = TERRAIN_PLAINS
                        elif moisture_val > 0.2:
                            tiles[y][x] = TERRAIN_GRASS
                        elif moisture_val > 0.1:
                            # Mix of desert and grass - favor desert in south
                            if south_influence > 0.25:
                                tiles[y][x] = TERRAIN_DESERT
                            else:
                                tiles[y][x] = TERRAIN_GRASS
                        else:
                            tiles[y][x] = TERRAIN_DESERT
                # Central/moderate climate zone (with latitude blending)
                else:
                    # Blend between north and south influences - more mixing and more forests
                    if height_val > mountain_threshold:
                        # Mountains - blend to snow if strong north influence
                        if north_influence > 0.2 and height_val > highland_threshold + 0.1:
                            tiles[y][x] = TERRAIN_SNOW
                        else:
                            tiles[y][x] = TERRAIN_MOUNTAIN
                    elif height_val > highland_threshold:
                        # Highlands: varied biomes (blend based on latitude, more forests)
                        if north_influence > 0.2:
                            tiles[y][x] = TERRAIN_MOUNTAIN
                        elif south_influence > 0.25 and moisture_val < 0.2:
                            tiles[y][x] = TERRAIN_DESERT
                        elif moisture_val > 0.5:
                            tiles[y][x] = TERRAIN_FOREST
                        elif moisture_val > 0.35:
                            tiles[y][x] = TERRAIN_GRASS
                        else:
                            tiles[y][x] = TERRAIN_PLAINS
                    elif height_val > lowland_threshold:
                        # Medium elevation: varied biomes with more mixing and forests
                        if south_influence > 0.2 and moisture_val < 0.3:
                            tiles[y][x] = TERRAIN_DESERT
                        elif moisture_val > 0.55:
                            tiles[y][x] = TERRAIN_FOREST
                        elif moisture_val > 0.4:
                            tiles[y][x] = TERRAIN_GRASS
                        elif moisture_val > 0.25:
                            tiles[y][x] = TERRAIN_PLAINS
                        elif moisture_val > 0.1:
                            # Mix between desert and grass
                            if south_influence > north_influence:
                                tiles[y][x] = TERRAIN_DESERT
                            else:
                                tiles[y][x] = TERRAIN_GRASS
                        else:
                            tiles[y][x] = TERRAIN_DESERT
                    else:
                        # Low elevation: varied biomes with more mixing and forests
                        if south_influence > 0.2 and moisture_val < 0.3:
                            tiles[y][x] = TERRAIN_DESERT
                        elif moisture_val > 0.5:
                            tiles[y][x] = TERRAIN_FOREST
                        elif moisture_val > 0.35:
                            tiles[y][x] = TERRAIN_GRASS
                        elif moisture_val > 0.25:
                            tiles[y][x] = TERRAIN_PLAINS
                        elif moisture_val > 0.1:
                            # Mix between desert and plains
                            if south_influence > 0.15:
                                tiles[y][x] = TERRAIN_DESERT
                            else:
                                tiles[y][x] = TERRAIN_PLAINS
                        else:
                            tiles[y][x] = TERRAIN_DESERT
        
        return tiles
    
    def _is_near_water(
        self, tiles: List[List[TerrainType]], x: int, y: int, width: int, height: int, radius: int = 2
    ) -> bool:
        """Check if a tile is near water (for beach placement)."""
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                nx = x + dx
                ny = y + dy
                if 0 <= nx < width and 0 <= ny < height:
                    if tiles[ny][nx].id == "water":
                        return True
        return False
    
    def _generate_water_bodies(
        self, tiles: List[List[TerrainType]], chunk_config: Dict
    ) -> List[List[TerrainType]]:
        """
        Generate coherent water bodies (lakes, rivers) instead of scattered water.
        Uses noise to create water basins that form larger, clustered water regions.
        """
        width = len(tiles[0])
        height = len(tiles)
        
        # Get water distribution target
        biome_distribution = chunk_config.get(
            'biome_distribution',
            self.gen_config.terrain.initial_distribution
        )
        water_target = biome_distribution.get('water', 0.1)
        total_tiles = width * height
        target_water_tiles = int(total_tiles * water_target)
        
        # Use noise to find low-lying areas for water
        # Water should form in "basins" - areas where noise is low
        water_noise_scale = chunk_config.get('water_noise_scale', 0.02)
        water_threshold = chunk_config.get('water_threshold', -0.3)  # Lower = more water
        
        # Generate water noise map
        water_map = []
        water_candidates = []
        
        for y in range(height):
            row = []
            for x in range(width):
                # Use different noise for water (creates basins)
                water_noise = self._tile_noise(x, y, water_noise_scale)
                row.append(water_noise)
                
                # If noise is low enough, this is a candidate for water
                if water_noise < water_threshold:
                    water_candidates.append((x, y, water_noise))
            
            water_map.append(row)
        
        # Sort candidates by noise value (lowest first = deepest basins)
        water_candidates.sort(key=lambda c: c[2])
        
        # Select water locations from candidates to reach target
        water_tiles = set()
        water_terrain = get_terrain("water")
        
        # Create water bodies by growing from seed points
        water_bodies = chunk_config.get('water_body_count', 3)
        min_body_size = chunk_config.get('min_water_body_size', 15)
        max_body_size = chunk_config.get('max_water_body_size', 80)
        
        bodies_created = 0
        tiles_used = 0
        
        for x, y, noise_val in water_candidates:
            if tiles_used >= target_water_tiles:
                break
            
            # Skip if already water or too close to existing water
            if (x, y) in water_tiles:
                continue
            
            # Check distance to existing water (to avoid tiny scattered bodies)
            too_close = False
            for wx, wy in water_tiles:
                dist = ((x - wx)**2 + (y - wy)**2) ** 0.5
                if dist < 5:  # Minimum distance between water bodies
                    too_close = True
                    break
            
            if too_close and bodies_created >= water_bodies:
                continue
            
            # Create a water body starting from this point
            body_size = random.randint(min_body_size, max_body_size)
            body_tiles = self._grow_water_body(
                tiles, water_map, x, y, body_size, water_threshold, width, height
            )
            
            # Add body tiles
            for tx, ty in body_tiles:
                if (tx, ty) not in water_tiles and tiles_used < target_water_tiles:
                    water_tiles.add((tx, ty))
                    tiles[ty][tx] = water_terrain or TERRAIN_WATER
                    tiles_used += 1
            
            bodies_created += 1
        
        return tiles
    
    def _grow_water_body(
        self, tiles: List[List[TerrainType]], water_map: List[List[float]],
        start_x: int, start_y: int, target_size: int, threshold: float,
        width: int, height: int
    ) -> List[Tuple[int, int]]:
        """
        Grow a water body from a seed point using flood-fill with noise constraints.
        """
        body_tiles = []
        queue = [(start_x, start_y)]
        visited = set()
        
        while queue and len(body_tiles) < target_size:
            x, y = queue.pop(0)
            
            if (x, y) in visited:
                continue
            
            if not (0 <= x < width and 0 <= y < height):
                continue
            
            # Check if this location is suitable for water (low noise)
            if water_map[y][x] > threshold + 0.2:  # Allow some expansion beyond threshold
                continue
            
            visited.add((x, y))
            body_tiles.append((x, y))
            
            # Add neighbors to queue (prefer lower noise values)
            neighbors = []
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    
                    nx = x + dx
                    ny = y + dy
                    
                    if (nx, ny) not in visited and 0 <= nx < width and 0 <= ny < height:
                        neighbors.append((nx, ny, water_map[ny][nx]))
            
            # Sort by noise (lower = better for water)
            neighbors.sort(key=lambda n: n[2])
            
            # Add neighbors to queue (prioritize lower noise)
            for nx, ny, _ in neighbors[:4]:  # Limit expansion
                if (nx, ny) not in visited:
                    queue.append((nx, ny))
        
        return body_tiles
    
    def _assign_chunk_biomes(
        self, chunks_x: int, chunks_y: int, chunk_config: Dict
    ) -> List[List[str]]:
        """
        Assign primary biome to each chunk with coherent placement.
        
        Uses a combination of:
        - Noise-based placement for natural distribution
        - Neighbor influence for coherence
        - Weighted random based on global distribution
        
        Returns:
            2D list of biome IDs (one per chunk)
        """
        # Get biome distribution from config
        biome_distribution = chunk_config.get(
            'biome_distribution',
            self.gen_config.terrain.initial_distribution
        )
        
        # Initialize chunk biome grid
        chunk_biomes = []
        for _ in range(chunks_y):
            chunk_biomes.append([None] * chunks_x)
        
        # Use simple noise-like pattern for initial placement
        # This creates coherent regions
        noise_scale = chunk_config.get('noise_scale', 0.1)
        coherence_strength = chunk_config.get('coherence_strength', 0.6)
        
        # First pass: assign biomes with noise-based selection
        for chunk_y in range(chunks_y):
            for chunk_x in range(chunks_x):
                # Calculate noise-like value for this chunk
                # Using simple hash-based pseudo-noise for determinism
                noise_val = self._chunk_noise(chunk_x, chunk_y, noise_scale)
                
                # Consider neighbor biomes for coherence
                neighbor_biomes = self._get_chunk_neighbor_biomes(
                    chunk_biomes, chunk_x, chunk_y, chunks_x, chunks_y
                )
                
                # Select biome
                if neighbor_biomes and random.random() < coherence_strength:
                    # Prefer matching a neighbor biome
                    biome = random.choice(neighbor_biomes)
                else:
                    # Use noise + distribution to pick biome
                    # Adjust noise to [0, 1] range
                    normalized_noise = (noise_val + 1.0) / 2.0
                    biome = self._pick_terrain_from_config(
                        normalized_noise, biome_distribution
                    ).id
                
                chunk_biomes[chunk_y][chunk_x] = biome
        
        return chunk_biomes
    
    def _chunk_noise(self, x: int, y: int, scale: float) -> float:
        """
        Generate pseudo-noise value for chunk at (x, y).
        Uses seeded random for determinism.
        """
        # Use chunk coordinates to generate deterministic "noise"
        # This creates coherent patterns
        temp_seed = self.seed + x * 73856093 + y * 19349663
        temp_rng = random.Random(temp_seed)
        
        # Generate multiple octaves for smoother noise
        value = 0.0
        amplitude = 1.0
        frequency = scale
        
        for _ in range(3):  # 3 octaves
            # Sample at different frequencies
            sample_x = x * frequency
            sample_y = y * frequency
            
            # Use hash-like function for pseudo-random value
            hash_val = hash((int(sample_x), int(sample_y), self.seed)) % 1000000
            normalized = (hash_val / 1000000.0) * 2.0 - 1.0  # [-1, 1]
            
            value += normalized * amplitude
            amplitude *= 0.5
            frequency *= 2.0
        
        return value / 1.75  # Normalize back to roughly [-1, 1]
    
    def _get_chunk_neighbor_biomes(
        self, chunk_biomes: List[List[str]], chunk_x: int, chunk_y: int,
        chunks_x: int, chunks_y: int
    ) -> List[str]:
        """Get list of biomes from neighboring chunks (already assigned)."""
        neighbors = []
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                
                nx = chunk_x + dx
                ny = chunk_y + dy
                
                if 0 <= nx < chunks_x and 0 <= ny < chunks_y:
                    biome = chunk_biomes[ny][nx]
                    if biome:
                        neighbors.append(biome)
        
        return neighbors
    
    def _generate_chunk_terrain(
        self, tiles: List[List[TerrainType]], chunk_x: int, chunk_y: int,
        chunk_size: int, primary_biome: str, chunk_config: Dict,
        chunk_biomes: List[List[str]], chunks_x: int, chunks_y: int
    ) -> None:
        """
        Generate terrain within a chunk based on its primary biome.
        Considers neighboring chunks for smooth blending at boundaries.
        
        Args:
            tiles: The terrain grid to modify
            chunk_x, chunk_y: Chunk coordinates
            chunk_size: Size of each chunk
            primary_biome: Primary biome ID for this chunk
            chunk_config: Chunk generation configuration
            chunk_biomes: Full grid of chunk biomes (for neighbor lookup)
            chunks_x, chunks_y: Total chunk dimensions
        """
        # Get biome-specific terrain generation rules
        biome_rules = chunk_config.get('biome_rules', {})
        rules = biome_rules.get(primary_biome, {})
        
        # Calculate chunk bounds
        start_x = chunk_x * chunk_size
        start_y = chunk_y * chunk_size
        end_x = min(start_x + chunk_size, self.config.world_width)
        end_y = min(start_y + chunk_size, self.config.world_height)
        
        # Get primary terrain type
        primary_terrain = get_terrain(primary_biome) or TERRAIN_GRASS
        
        # Get allowed terrain types for this biome
        allowed_terrain = rules.get('allowed_terrain', [primary_biome])
        terrain_weights = rules.get('terrain_weights', {primary_biome: 1.0})
        
        # Variation amount (how much the terrain can vary within chunk)
        variation = rules.get('variation', 0.2)
        
        # Transition settings
        transition_width = chunk_config.get('transition_width', 3)
        blend_strength = chunk_config.get('transition_blend_strength', 0.7)
        
        # Generate terrain for each tile in chunk
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                # Calculate distance to chunk edges
                local_x = x - start_x
                local_y = y - start_y
                
                # Distance to nearest edge (0 = at edge, chunk_size/2 = center)
                dist_to_left = local_x
                dist_to_right = (chunk_size - 1) - local_x
                dist_to_top = local_y
                dist_to_bottom = (chunk_size - 1) - local_y
                min_dist_to_edge = min(dist_to_left, dist_to_right, dist_to_top, dist_to_bottom)
                
                # Check if we're in a transition zone
                in_transition = min_dist_to_edge < transition_width
                
                # Determine which biome to use (blend with neighbors near edges)
                biome_to_use = primary_biome
                if in_transition:
                    # Get neighboring chunk biomes
                    neighbor_biomes = self._get_chunk_neighbor_biomes(
                        chunk_biomes, chunk_x, chunk_y, chunks_x, chunks_y
                    )
                    
                    if neighbor_biomes:
                        # Calculate blend probability based on distance to edge
                        # Closer to edge = more likely to use neighbor biome
                        edge_factor = 1.0 - (min_dist_to_edge / transition_width)
                        blend_prob = edge_factor * blend_strength
                        
                        if random.random() < blend_prob:
                            # Use a neighboring biome
                            biome_to_use = random.choice(neighbor_biomes)
                            # Get rules for the blended biome
                            blend_rules = biome_rules.get(biome_to_use, rules)
                            blend_allowed = blend_rules.get('allowed_terrain', [biome_to_use])
                            blend_weights = blend_rules.get('terrain_weights', {biome_to_use: 1.0})
                            
                            # Use blended biome's rules
                            if random.random() < blend_rules.get('variation', 0.2):
                                terrain_id = self._pick_weighted_terrain(blend_allowed, blend_weights)
                                terrain = get_terrain(terrain_id) or primary_terrain
                            else:
                                terrain = get_terrain(biome_to_use) or primary_terrain
                        else:
                            # Use primary biome with variation
                            if random.random() < variation:
                                terrain_id = self._pick_weighted_terrain(allowed_terrain, terrain_weights)
                                terrain = get_terrain(terrain_id) or primary_terrain
                            else:
                                terrain = primary_terrain
                    else:
                        # No neighbors, use primary biome
                        if random.random() < variation:
                            terrain_id = self._pick_weighted_terrain(allowed_terrain, terrain_weights)
                            terrain = get_terrain(terrain_id) or primary_terrain
                        else:
                            terrain = primary_terrain
                else:
                    # Center of chunk, use primary biome with variation
                    if random.random() < variation:
                        terrain_id = self._pick_weighted_terrain(allowed_terrain, terrain_weights)
                        terrain = get_terrain(terrain_id) or primary_terrain
                    else:
                        terrain = primary_terrain
                
                tiles[y][x] = terrain
    
    def _pick_weighted_terrain(
        self, allowed_terrain: List[str], weights: Dict[str, float]
    ) -> str:
        """Pick terrain type from allowed list using weights."""
        if not allowed_terrain:
            return "grass"
        
        # Build weight list
        weight_list = []
        for terrain_id in allowed_terrain:
            weight = weights.get(terrain_id, 1.0)
            weight_list.append(weight)
        
        # Normalize weights
        total = sum(weight_list)
        if total == 0:
            return allowed_terrain[0]
        
        # Pick using weighted random
        rand = random.random() * total
        cumulative = 0.0
        for i, weight in enumerate(weight_list):
            cumulative += weight
            if rand < cumulative:
                return allowed_terrain[i]
        
        return allowed_terrain[-1]
    
    def _smooth_chunk_transitions(
        self, tiles: List[List[TerrainType]], chunk_size: int, chunk_config: Dict
    ) -> List[List[TerrainType]]:
        """
        Apply additional smoothing passes to blend chunk boundaries.
        This is a post-processing step after initial generation.
        
        Args:
            tiles: The terrain grid
            chunk_size: Size of chunks
            chunk_config: Configuration
            
        Returns:
            Modified terrain grid
        """
        iterations = chunk_config.get('transition_smoothing_iterations', 3)
        neighbor_radius = chunk_config.get('smoothing_radius', 2)
        conversion_threshold = chunk_config.get('smoothing_threshold', 4)
        conversion_chance = chunk_config.get('smoothing_chance', 0.5)
        
        width = len(tiles[0])
        height = len(tiles)
        
        for _ in range(iterations):
            new_tiles = [row[:] for row in tiles]
            
            for y in range(height):
                for x in range(width):
                    # Count neighbors of each terrain type
                    neighbor_counts = {}
                    
                    for dy in range(-neighbor_radius, neighbor_radius + 1):
                        for dx in range(-neighbor_radius, neighbor_radius + 1):
                            if dx == 0 and dy == 0:
                                continue
                            
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
                        current_terrain_id = tiles[y][x].id
                        
                        # If most neighbors are different and threshold met, blend
                        if most_common_id != current_terrain_id and count >= conversion_threshold:
                            if random.random() < conversion_chance:
                                new_terrain = get_terrain(most_common_id)
                                if new_terrain:
                                    new_tiles[y][x] = new_terrain
            
            tiles = new_tiles
        
        return tiles
    
    def _generate_legacy_terrain(self) -> List[List[TerrainType]]:
        """
        Legacy terrain generation method (original implementation).
        
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
            distribution: Dictionary mapping terrain IDs to weights (should sum to ~1.0)
            
        Returns:
            TerrainType instance
        """
        # Normalize distribution if needed
        total = sum(distribution.values())
        if total == 0:
            return TERRAIN_GRASS
        
        # Build cumulative distribution
        cumulative = 0.0
        for terrain_id, weight in distribution.items():
            normalized_weight = weight / total
            cumulative += normalized_weight
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

