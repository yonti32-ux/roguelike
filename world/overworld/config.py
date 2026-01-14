"""
Overworld configuration system.

Loads and manages overworld settings from config file.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

# Config file location
CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"
OVERWORLD_CONFIG_FILE = CONFIG_DIR / "overworld_settings.json"


@dataclass
class OverworldConfig:
    """Overworld configuration loaded from file."""
    
    # World settings
    world_width: int = 128
    world_height: int = 128
    region_size: int = 64
    seed: Optional[int] = None
    world_name: Optional[str] = None
    
    # POI settings
    poi_density: float = 0.25  # Increased from 0.15 for more POIs
    poi_min_distance: int = 8
    poi_distribution: Dict[str, float] = field(default_factory=lambda: {
        "dungeon": 0.4,
        "village": 0.3,
        "town": 0.15,
        "camp": 0.15,
    })
    
    # Difficulty settings
    difficulty_scaling: str = "distance"
    base_level: int = 1
    max_level: int = 20
    level_per_distance: float = 0.5
    
    # Time settings
    movement_cost_base: float = 1.0
    terrain_costs: Dict[str, float] = field(default_factory=lambda: {
        "grass": 1.0,
        "forest": 1.5,
        "mountain": 2.0,
        "water": 999.0,
    })
    
    # Starting location
    starting_location_type: str = "random"
    starting_location_x: Optional[int] = None
    starting_location_y: Optional[int] = None
    
    # Sight/exploration settings
    sight_radius: int = 8
    
    # Zoom settings
    default_zoom_index: int = 1  # Index into zoom levels (1 = 75% default)
    
    # Faction settings (advanced)
    faction_counts: Dict[str, int] = field(default_factory=lambda: {
        "good": 2,
        "neutral": 2,
        "evil": 2,
    })
    
    @classmethod
    def load(cls) -> "OverworldConfig":
        """Load configuration from file, using defaults if file doesn't exist."""
        config = cls()
        
        if not OVERWORLD_CONFIG_FILE.exists():
            # Create default config file
            config.save()
            return config
        
        try:
            with OVERWORLD_CONFIG_FILE.open("r", encoding="utf-8") as f:
                data = json.load(f)
            
            # World settings
            world_data = data.get("world", {})
            config.world_width = world_data.get("width", config.world_width)
            config.world_height = world_data.get("height", config.world_height)
            config.region_size = world_data.get("region_size", config.region_size)
            seed_val = world_data.get("seed")
            config.seed = int(seed_val) if seed_val is not None else None
            config.world_name = world_data.get("world_name", config.world_name)
            
            # POI settings
            poi_data = data.get("poi", {})
            config.poi_density = poi_data.get("density", config.poi_density)
            config.poi_min_distance = poi_data.get("min_distance", config.poi_min_distance)
            config.poi_distribution = poi_data.get("distribution", config.poi_distribution)
            
            # Difficulty settings
            diff_data = data.get("difficulty", {})
            config.difficulty_scaling = diff_data.get("scaling_type", config.difficulty_scaling)
            config.base_level = diff_data.get("base_level", config.base_level)
            config.max_level = diff_data.get("max_level", config.max_level)
            config.level_per_distance = diff_data.get("level_per_distance", config.level_per_distance)
            
            # Time settings
            time_data = data.get("time", {})
            config.movement_cost_base = time_data.get("movement_cost_base", config.movement_cost_base)
            config.terrain_costs = time_data.get("terrain_costs", config.terrain_costs)
            
            # Starting location
            start_data = data.get("starting_location", {})
            config.starting_location_type = start_data.get("type", config.starting_location_type)
            start_x = start_data.get("x")
            start_y = start_data.get("y")
            config.starting_location_x = int(start_x) if start_x is not None else None
            config.starting_location_y = int(start_y) if start_y is not None else None
            
            # Sight settings
            sight_data = data.get("sight", {})
            config.sight_radius = sight_data.get("radius", config.sight_radius)
            
            # Zoom settings
            zoom_data = data.get("zoom", {})
            config.default_zoom_index = zoom_data.get("default_index", config.default_zoom_index)
            
            # Faction settings (advanced)
            faction_data = data.get("factions", {})
            config.faction_counts = faction_data.get("counts", config.faction_counts)
            
        except Exception as e:
            print(f"Error loading overworld config: {e}")
            print("Using default configuration.")
        
        return config
    
    def save(self) -> bool:
        """Save configuration to file."""
        try:
            CONFIG_DIR.mkdir(exist_ok=True)
            
            data = {
                "world": {
                    "width": self.world_width,
                    "height": self.world_height,
                    "region_size": self.region_size,
                    "seed": self.seed,
                    "world_name": self.world_name,
                },
                "poi": {
                    "density": self.poi_density,
                    "min_distance": self.poi_min_distance,
                    "distribution": self.poi_distribution,
                },
                "difficulty": {
                    "scaling_type": self.difficulty_scaling,
                    "base_level": self.base_level,
                    "max_level": self.max_level,
                    "level_per_distance": self.level_per_distance,
                },
                "time": {
                    "movement_cost_base": self.movement_cost_base,
                    "terrain_costs": self.terrain_costs,
                },
                "starting_location": {
                    "x": self.starting_location_x,
                    "y": self.starting_location_y,
                    "type": self.starting_location_type,
                },
                "sight": {
                    "radius": self.sight_radius,
                },
                "zoom": {
                    "default_index": self.default_zoom_index,
                },
                "factions": {
                    "counts": self.faction_counts,
                },
            }
            
            with OVERWORLD_CONFIG_FILE.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving overworld config: {e}")
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "world_width": self.world_width,
            "world_height": self.world_height,
            "region_size": self.region_size,
            "seed": self.seed,
            "world_name": self.world_name,
            "poi_density": self.poi_density,
            "poi_min_distance": self.poi_min_distance,
            "poi_distribution": self.poi_distribution,
            "difficulty_scaling": self.difficulty_scaling,
            "base_level": self.base_level,
            "max_level": self.max_level,
            "level_per_distance": self.level_per_distance,
            "movement_cost_base": self.movement_cost_base,
            "terrain_costs": self.terrain_costs,
            "starting_location_type": self.starting_location_type,
            "starting_location_x": self.starting_location_x,
            "starting_location_y": self.starting_location_y,
            "sight_radius": self.sight_radius,
            "default_zoom_index": self.default_zoom_index,
            "faction_counts": self.faction_counts,
        }

