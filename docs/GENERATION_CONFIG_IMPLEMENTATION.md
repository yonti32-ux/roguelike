# Generation Configuration System - Implementation Summary

## What Was Done

We've implemented a simple configuration-based system for map and POI generation. This replaces hardcoded values with configurable JSON settings that can be modified without changing code.

## Files Created

1. **`config/generation_settings.json`** - Main configuration file with all generation parameters
2. **`world/generation/config.py`** - Configuration loader and data classes
3. **`world/generation/__init__.py`** - Module exports

## Files Modified

1. **`world/overworld/generation.py`** - Now reads terrain generation settings from config
2. **`world/poi/placement.py`** - Now reads POI placement settings from config
3. **`world/mapgen.py`** - Now reads floor generation and room tagging settings from config

## How It Works

### Before (Hardcoded):
```python
# In generation.py
if rand < 0.35:
    terrain = TERRAIN_GRASS
elif rand < 0.55:
    terrain = TERRAIN_PLAINS
# etc...
```

### After (Config-Based):
```python
# In generation.py
terrain = self._pick_terrain_from_config(rand, self.gen_config.terrain.initial_distribution)

# In generation_settings.json
{
  "terrain": {
    "initial_distribution": {
      "grass": 0.35,
      "plains": 0.20,
      // etc...
    }
  }
}
```

## Configuration Structure

### Terrain Generation
- **Initial distribution**: Weights for each terrain type (grass, plains, forest, etc.)
- **Smoothing**: Cellular automata parameters (iterations, neighbor radius, conversion threshold/chance)
- **Water clustering**: Prevents isolated water tiles
- **Refinement**: Rules for realistic terrain placement (forest isolation, desert conversion, etc.)

### POI Placement
- **Max POIs**: Maximum number of POIs to place (default: 200)
- **Placement attempts**: Max attempts per POI (default: 200)
- **Failure handling**: Max consecutive failures before stopping (default: 50)
- **Terrain blacklist**: Terrain types where POIs can't be placed (default: ["water"])
- **Preferred starting terrain**: Terrain types preferred for starting location

### Floor Generation
- **Size scaling**: Progressive scaling rules for different floor ranges (1, 2, 3-4, 5-6, 7-8, 9+)
- **Min/max scale**: Bounds for floor size scaling
- **Room count**: Base count, min/max limits, density formula
- **Room size**: Min/max room dimensions
- **Wall border**: Size of wall border around rooms

### Room Tagging
- **Tag configurations**: Chance, min_floor, max_per_floor for each tag type
  - Shop, Graveyard, Sanctum, Armory, Library, Arena

### Dungeon Floor Count
- **Base floor count**: Starting floor count (default: 3)
- **Level multiplier**: How floors scale with level (default: 0.4)
- **Variance ranges**: Different variance for low/mid/high level dungeons
- **Min floors per level range**: Minimum floors based on dungeon level

## Usage

### Loading Configuration

```python
from world.generation.config import load_generation_config

gen_config = load_generation_config()
```

### Using Configuration Values

```python
# Access terrain settings
grass_weight = gen_config.terrain.initial_distribution["grass"]
smoothing_iterations = gen_config.terrain.smoothing["iterations"]

# Access POI settings
max_pois = gen_config.poi.max_pois
terrain_blacklist = gen_config.poi.terrain_blacklist

# Access floor settings
base_rooms = gen_config.floor.room_count["base"]
room_min_size = gen_config.floor.room_size["min"]

# Access room tag settings
shop_chance = gen_config.room_tags.shop["chance"]

# Access dungeon settings
base_floors = gen_config.dungeon.floor_count["base"]
```

### Modifying Configuration

Simply edit `config/generation_settings.json` and restart the game. No code changes needed!

**Example: Change terrain distribution to have more forests:**
```json
{
  "terrain": {
    "initial_distribution": {
      "grass": 0.30,
      "plains": 0.20,
      "forest": 0.25,  // Increased from 0.15
      "mountain": 0.12,
      "desert": 0.08,
      "water": 0.05
    }
  }
}
```

**Example: Make floors bigger earlier:**
```json
{
  "floor": {
    "size_scaling": {
      "1": {
        "scales": [1.2, 1.5, 1.8],  // Bigger scales
        "weights": [0.3, 0.4, 0.3]
      }
    }
  }
}
```

**Example: Increase shop spawn chance:**
```json
{
  "room_tags": {
    "shop": {
      "chance": 0.9,  // Increased from 0.7
      "max_per_floor": 1
    }
  }
}
```

## Benefits

1. **Easy Tuning**: Change generation parameters without touching code
2. **Preset Support**: Create different config files for different game modes
3. **User Customization**: Players can modify generation behavior
4. **Clear Documentation**: Config file serves as documentation of all parameters
5. **Safe Defaults**: If config file is missing, sensible defaults are used

## Future Enhancements

1. **Multiple Config Files**: Support for preset configs (small_world.json, large_world.json, etc.)
2. **Runtime Reloading**: Hot-reload config without restart (advanced)
3. **Config Validation**: Validate config values at load time
4. **Config UI**: In-game editor for generation settings
5. **Migration Support**: Auto-update config files when schema changes

## Migration Notes

- **Backwards Compatible**: If config file doesn't exist, defaults are used (matches old behavior)
- **No Breaking Changes**: All existing functionality preserved
- **Config File Created**: On first run, default config file is created at `config/generation_settings.json`

## Testing

To test the system:

1. Generate a world and note the characteristics
2. Edit `config/generation_settings.json` (e.g., change terrain weights)
3. Generate a new world and verify changes took effect
4. Compare before/after to confirm configuration is working

## Example Config Presets

### Small World (Testing)
```json
{
  "poi": {
    "max_pois": 50,
    "max_placement_attempts": 100
  },
  "floor": {
    "room_count": {
      "base": 6,
      "min": 4,
      "max": 15
    }
  }
}
```

### Large World (Epic)
```json
{
  "poi": {
    "max_pois": 500,
    "max_placement_attempts": 300
  },
  "floor": {
    "room_count": {
      "base": 15,
      "min": 10,
      "max": 30
    }
  }
}
```

## Summary

This implementation provides a simple, effective way to configure map and POI generation without the complexity of a full rule engine. It's easy to understand, maintain, and extend while providing most of the benefits of a more complex system.

