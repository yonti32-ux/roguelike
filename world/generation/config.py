"""
Generation configuration loader.

Loads and validates generation settings from JSON config file.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


# Config file location
CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"
GENERATION_CONFIG_FILE = CONFIG_DIR / "generation_settings.json"


@dataclass
class TerrainConfig:
    """Terrain generation configuration."""
    initial_distribution: Dict[str, float] = field(default_factory=lambda: {
        "grass": 0.35,
        "plains": 0.20,
        "forest": 0.15,
        "mountain": 0.12,
        "desert": 0.10,
        "water": 0.08,
    })
    smoothing: Dict[str, Any] = field(default_factory=lambda: {
        "iterations": 3,
        "neighbor_radius": 1,
        "conversion_threshold": 4,
        "conversion_chance": 0.6,
    })
    water_clustering: Dict[str, Any] = field(default_factory=lambda: {
        "min_neighbors": 2,
        "isolation_conversion_chance": 0.3,
    })
    refinement: Dict[str, Any] = field(default_factory=lambda: {
        "forest_isolation_chance": 0.15,
        "desert_conversion_chance": 0.25,
        "mountain_water_threshold": 3,
        "mountain_conversion_chance": 0.2,
        "variation_chance": 0.02,
    })


@dataclass
class POIConfig:
    """POI placement configuration."""
    max_pois: int = 400  # Increased from 200 for more POIs
    max_placement_attempts: int = 200
    max_consecutive_failures: int = 50
    terrain_blacklist: List[str] = field(default_factory=lambda: ["water"])
    preferred_starting_terrain: List[str] = field(default_factory=lambda: ["grass", "plains"])
    placement_rules: Dict[str, Any] = field(default_factory=lambda: {
        "placement_order": ["town", "village", "dungeon", "camp"],
        "spatial_rules": {
            "village": {
                "near_town": {"enabled": True, "min_distance": 10, "max_distance": 30, "chance": 0.7},
                "avoid_dungeon": {"enabled": True, "min_distance": 15},
            },
            "dungeon": {
                "avoid_town": {"enabled": True, "min_distance": 25},
                "avoid_village": {"enabled": True, "min_distance": 20},
                "prefer_remote": {"enabled": True, "bonus_weight": 1.5, "distance_threshold": 30},
            },
            "camp": {
                "avoid_town": {"enabled": True, "min_distance": 12},
                "avoid_village": {"enabled": True, "min_distance": 10},
            },
        },
    })


@dataclass
class FloorConfig:
    """Floor generation configuration."""
    size_scaling: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    min_scale: float = 0.9
    max_scale: float = 2.5
    room_count: Dict[str, Any] = field(default_factory=lambda: {
        "base": 10,
        "min": 6,
        "max": 22,
        "density_formula": "sqrt",
    })
    room_size: Dict[str, int] = field(default_factory=lambda: {
        "min": 4,
        "max": 9,
    })
    wall_border: int = 1


@dataclass
class RoomTagConfig:
    """Room tagging configuration."""
    shop: Dict[str, Any] = field(default_factory=lambda: {
        "chance": 0.7,
        "max_per_floor": 1,
    })
    graveyard: Dict[str, Any] = field(default_factory=lambda: {
        "min_floor": 2,
        "chance": 0.8,
        "max_per_floor": 1,
    })
    sanctum: Dict[str, Any] = field(default_factory=lambda: {
        "min_floor": 3,
        "chance": 0.5,
        "max_per_floor": 1,
    })
    armory: Dict[str, Any] = field(default_factory=lambda: {
        "min_floor": 2,
        "chance": 0.5,
        "max_per_floor": 1,
    })
    library: Dict[str, Any] = field(default_factory=lambda: {
        "min_floor": 2,
        "chance": 0.5,
        "max_per_floor": 1,
    })
    arena: Dict[str, Any] = field(default_factory=lambda: {
        "min_floor": 3,
        "chance": 0.4,
        "max_per_floor": 1,
    })


@dataclass
class DungeonConfig:
    """Dungeon floor count configuration."""
    floor_count: Dict[str, Any] = field(default_factory=lambda: {
        "base": 3,
        "level_multiplier": 0.4,
        "max": 20,
        "variance": {
            "low_level": {"max_level": 5, "min": -1, "max": 2},
            "mid_level": {"max_level": 10, "min": -2, "max": 2},
            "high_level": {"min": -2, "max": 3},
        },
        "min_floors_per_level_range": {
            "1-3": 3,
            "4-6": 4,
            "7-9": 5,
            "10-12": 6,
            "13-15": 7,
            "16-18": 8,
            "19+": 9,
        },
    })


@dataclass
class GenerationConfig:
    """Complete generation configuration."""
    terrain: TerrainConfig = field(default_factory=TerrainConfig)
    poi: POIConfig = field(default_factory=POIConfig)
    floor: FloorConfig = field(default_factory=FloorConfig)
    room_tags: RoomTagConfig = field(default_factory=RoomTagConfig)
    dungeon: DungeonConfig = field(default_factory=DungeonConfig)
    
    @classmethod
    def load(cls, config_file: Optional[Path] = None) -> "GenerationConfig":
        """
        Load configuration from file, using defaults if file doesn't exist.
        
        Args:
            config_file: Optional path to config file (defaults to standard location)
            
        Returns:
            GenerationConfig instance
        """
        if config_file is None:
            config_file = GENERATION_CONFIG_FILE
        
        config = cls()
        
        if not config_file.exists():
            print(f"Generation config file not found at {config_file}, using defaults.")
            # Save default config file
            config.save(config_file)
            return config
        
        try:
            with config_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Load terrain config
            if "terrain" in data:
                terrain_data = data["terrain"]
                config.terrain = TerrainConfig(
                    initial_distribution=terrain_data.get("initial_distribution", config.terrain.initial_distribution),
                    smoothing=terrain_data.get("smoothing", config.terrain.smoothing),
                    water_clustering=terrain_data.get("water_clustering", config.terrain.water_clustering),
                    refinement=terrain_data.get("refinement", config.terrain.refinement),
                )
            
            # Load POI config
            if "poi" in data:
                poi_data = data["poi"]
                config.poi = POIConfig(
                    max_pois=poi_data.get("max_pois", config.poi.max_pois),
                    max_placement_attempts=poi_data.get("max_placement_attempts", config.poi.max_placement_attempts),
                    max_consecutive_failures=poi_data.get("max_consecutive_failures", config.poi.max_consecutive_failures),
                    terrain_blacklist=poi_data.get("terrain_blacklist", config.poi.terrain_blacklist),
                    preferred_starting_terrain=poi_data.get("preferred_starting_terrain", config.poi.preferred_starting_terrain),
                    placement_rules=poi_data.get("placement_rules", config.poi.placement_rules),
                )
            
            # Load floor config
            if "floor" in data:
                floor_data = data["floor"]
                config.floor = FloorConfig(
                    size_scaling=floor_data.get("size_scaling", config.floor.size_scaling),
                    min_scale=floor_data.get("min_scale", config.floor.min_scale),
                    max_scale=floor_data.get("max_scale", config.floor.max_scale),
                    room_count=floor_data.get("room_count", config.floor.room_count),
                    room_size=floor_data.get("room_size", config.floor.room_size),
                    wall_border=floor_data.get("wall_border", config.floor.wall_border),
                )
            
            # Load room tag config
            if "room_tags" in data:
                room_tags_data = data["room_tags"]
                config.room_tags = RoomTagConfig(
                    shop=room_tags_data.get("shop", config.room_tags.shop),
                    graveyard=room_tags_data.get("graveyard", config.room_tags.graveyard),
                    sanctum=room_tags_data.get("sanctum", config.room_tags.sanctum),
                    armory=room_tags_data.get("armory", config.room_tags.armory),
                    library=room_tags_data.get("library", config.room_tags.library),
                    arena=room_tags_data.get("arena", config.room_tags.arena),
                )
            
            # Load dungeon config
            if "dungeon" in data:
                dungeon_data = data["dungeon"]
                config.dungeon = DungeonConfig(
                    floor_count=dungeon_data.get("floor_count", config.dungeon.floor_count),
                )
            
        except Exception as e:
            print(f"Error loading generation config: {e}")
            print("Using default configuration.")
        
        return config
    
    def save(self, config_file: Optional[Path] = None) -> bool:
        """
        Save configuration to file.
        
        Args:
            config_file: Optional path to config file (defaults to standard location)
            
        Returns:
            True if saved successfully, False otherwise
        """
        if config_file is None:
            config_file = GENERATION_CONFIG_FILE
        
        try:
            CONFIG_DIR.mkdir(exist_ok=True)
            
            data = {
                "terrain": {
                    "initial_distribution": self.terrain.initial_distribution,
                    "smoothing": self.terrain.smoothing,
                    "water_clustering": self.terrain.water_clustering,
                    "refinement": self.terrain.refinement,
                },
                "poi": {
                    "max_pois": self.poi.max_pois,
                    "max_placement_attempts": self.poi.max_placement_attempts,
                    "max_consecutive_failures": self.poi.max_consecutive_failures,
                    "terrain_blacklist": self.poi.terrain_blacklist,
                    "preferred_starting_terrain": self.poi.preferred_starting_terrain,
                    "placement_rules": self.poi.placement_rules,
                },
                "floor": {
                    "size_scaling": self.floor.size_scaling,
                    "min_scale": self.floor.min_scale,
                    "max_scale": self.floor.max_scale,
                    "room_count": self.floor.room_count,
                    "room_size": self.floor.room_size,
                    "wall_border": self.floor.wall_border,
                },
                "room_tags": {
                    "shop": self.room_tags.shop,
                    "graveyard": self.room_tags.graveyard,
                    "sanctum": self.room_tags.sanctum,
                    "armory": self.room_tags.armory,
                    "library": self.room_tags.library,
                    "arena": self.room_tags.arena,
                },
                "dungeon": {
                    "floor_count": self.dungeon.floor_count,
                },
            }
            
            with config_file.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving generation config: {e}")
            return False


def load_generation_config(config_file: Optional[Path] = None) -> GenerationConfig:
    """
    Convenience function to load generation config.
    
    Args:
        config_file: Optional path to config file
        
    Returns:
        GenerationConfig instance
    """
    return GenerationConfig.load(config_file)

