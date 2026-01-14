# Chunk-Based Terrain Generation

## Overview

The overworld terrain generation has been enhanced with a chunk-based biome system that creates more consistent, structured world maps while maintaining randomization. Instead of completely random biome placement, the world is now divided into chunks, each with a primary biome assigned using coherent placement algorithms.

## How It Works

### 1. Chunk Division
- The world is divided into chunks based on `region_size` from the overworld config (default: 64 tiles)
- Each chunk is a square region of the world map
- Chunks are processed independently but with neighbor awareness

### 2. Biome Assignment
- Each chunk is assigned a primary biome using:
  - **Noise-based placement**: Pseudo-noise function creates coherent patterns
  - **Neighbor influence**: Chunks prefer to match neighboring biomes (configurable coherence strength)
  - **Weighted distribution**: Global biome distribution is respected across the world

### 3. Terrain Generation Within Chunks
- Each chunk generates terrain based on its primary biome
- Biome-specific rules control:
  - **Variation**: How much terrain can vary within the chunk (e.g., 15-25%)
  - **Allowed terrain**: Which terrain types can appear in this biome
  - **Terrain weights**: Probability distribution of terrain types within the chunk

### 4. Smooth Transitions
- Transition zones are created at chunk boundaries
- Configurable transition width and smoothing iterations
- Blending algorithm ensures natural-looking biome boundaries

## Configuration

The chunk-based system is configured in `config/generation_settings.json` under `terrain.chunk_based`:

```json
{
  "terrain": {
    "chunk_based": {
      "enabled": true,
      "noise_scale": 0.15,
      "coherence_strength": 0.65,
      "smooth_transitions": true,
      "transition_width": 3,
      "transition_smoothing_iterations": 2,
      "transition_blend_chance": 0.5,
      "biome_distribution": {
        "grass": 0.30,
        "plains": 0.20,
        "forest": 0.18,
        "mountain": 0.12,
        "desert": 0.10,
        "water": 0.10
      },
      "biome_rules": {
        "grass": {
          "variation": 0.15,
          "allowed_terrain": ["grass", "plains"],
          "terrain_weights": {
            "grass": 0.7,
            "plains": 0.3
          }
        },
        // ... other biomes
      }
    }
  }
}
```

### Configuration Options

- **enabled**: Enable/disable chunk-based generation (default: true)
- **noise_scale**: Controls the scale of noise patterns (lower = larger regions)
- **coherence_strength**: How strongly chunks prefer matching neighbors (0.0-1.0)
- **smooth_transitions**: Enable transition smoothing between chunks
- **transition_width**: Width of transition zones in tiles
- **transition_smoothing_iterations**: Number of smoothing passes
- **transition_blend_chance**: Probability of blending at boundaries
- **biome_distribution**: Global distribution of biomes across the world
- **biome_rules**: Per-biome generation rules

## Benefits

1. **Consistency**: Biomes form coherent regions rather than random patches
2. **Structure**: World feels more like a real map with distinct regions
3. **Randomization**: Still randomized each time, but with structure
4. **Configurability**: All aspects are configurable via JSON
5. **Backward Compatibility**: Falls back to legacy generation if disabled

## Biome Rules

Each biome can have custom rules:

- **variation**: Percentage of tiles that can differ from primary biome (0.0-1.0)
- **allowed_terrain**: List of terrain types that can appear in this biome
- **terrain_weights**: Probability weights for each allowed terrain type

Example: A "forest" biome might have:
- 80% forest tiles
- 20% grass tiles (for clearings)
- 0% water tiles (unless explicitly allowed)

## Legacy Mode

If `chunk_based.enabled` is `false` or the config is missing, the system falls back to the original cellular automata-based generation method. This ensures backward compatibility.

## Technical Details

- Chunks are calculated using integer division: `chunk_x = x // chunk_size`
- Noise function uses seeded random for determinism
- Neighbor influence is checked in 8 directions (including diagonals)
- Transition smoothing uses cellular automata-like rules at boundaries
- Final refinement pass applies realistic terrain placement rules

