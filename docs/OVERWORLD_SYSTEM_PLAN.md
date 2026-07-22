# Overworld Map System - Comprehensive Architecture Plan

## Overview
A large, modular overworld system that serves as the hub for exploration. Players move between Points of Interest (POIs) on a tile-based overworld map, with each POI leading to the existing exploration/combat system.

---

## 1. Core Architecture

### 1.1 Design Principles
- **Modularity**: Each component is self-contained and replaceable
- **Extensibility**: Easy to add new POI types, terrain types, events
- **Configurability**: World size, POI density, difficulty scaling all configurable
- **Persistence**: World state saved/loaded with game saves
- **Performance**: Large worlds use chunking/region loading for efficiency

### 1.2 System Layers
```
┌─────────────────────────────────────┐
│   Game Core (engine/core/game.py)   │  ← Mode management, state
├─────────────────────────────────────┤
│   Overworld Controller              │  ← Input, movement, transitions
├─────────────────────────────────────┤
│   Overworld Map                     │  ← Terrain, regions, chunks
├─────────────────────────────────────┤
│   POI System                        │  ← POI types, placement, state
├─────────────────────────────────────┤
│   World Generation                  │  ← Terrain gen, POI placement
├─────────────────────────────────────┤
│   Time System                       │  ← Time tracking, day/night
└─────────────────────────────────────┘
```

---

## 2. File Structure

### 2.1 New Directories & Files

```
world/
  overworld/
    __init__.py                    # Public API exports
    map.py                         # OverworldMap class
    region.py                      # Region/Chunk system for large worlds
    terrain.py                     # Terrain types, rendering
    generation.py                  # World generation logic
    config.py                      # Overworld configuration
    
  poi/
    __init__.py                    # Public API exports
    base.py                        # Base POI class
    types.py                       # POI type definitions (Dungeon, Village, etc.)
    placement.py                   # POI placement algorithms
    state.py                       # POI state management
    
  time/
    __init__.py                    # Public API exports
    time_system.py                 # Time tracking, day/night
    
engine/
  controllers/
    overworld.py                   # Overworld input/movement controller
    
  managers/
    overworld_manager.py           # Overworld state management
    
ui/
  overworld/
    __init__.py                    # Public API exports
    hud.py                         # Overworld HUD rendering
    minimap.py                     # Minimap overlay (future)
    
config/
  overworld_settings.json          # Overworld configuration file
```

### 2.2 Modified Files

```
engine/core/
  game.py                         # Add OVERWORLD mode, overworld state
  states.py                       # Add GameMode.OVERWORLD
  
engine/utils/
  save_system.py                  # Add overworld serialization
  
world/
  biomes.py                       # Extend for overworld biomes (if needed)
```

---

## 3. Core Classes & Data Structures

### 3.1 OverworldMap (`world/overworld/map.py`)

```python
class OverworldMap:
    """
    Main overworld map container. Handles regions/chunks for large worlds.
    """
    # Configuration
    width: int                     # Total map width in tiles
    height: int                    # Total map height in tiles
    region_size: int              # Size of each region/chunk (e.g., 64x64)
    
    # World data
    seed: int                      # Random seed for generation
    regions: Dict[Tuple[int, int], Region]  # Loaded regions by (rx, ry)
    
    # Player state
    player_position: Tuple[int, int]  # Current tile position
    explored_tiles: Set[Tuple[int, int]]  # Explored tiles
    
    # POIs
    pois: Dict[str, PointOfInterest]  # All POIs by ID
    
    # Methods
    def get_tile(x, y) -> TerrainType
    def get_region(x, y) -> Region
    def load_region(rx, ry) -> Region
    def unload_region(rx, ry)
    def is_explored(x, y) -> bool
    def explore_tile(x, y)
```

### 3.2 Region (`world/overworld/region.py`)

```python
class Region:
    """
    A chunk/region of the overworld (e.g., 64x64 tiles).
    Loaded on-demand for performance with large worlds.
    """
    region_x: int                 # Region X coordinate
    region_y: int                 # Region Y coordinate
    tiles: List[List[TerrainType]]  # Terrain data for this region
    pois: List[PointOfInterest]   # POIs in this region
    
    def get_tile(local_x, local_y) -> TerrainType
    def get_pois() -> List[PointOfInterest]
```

### 3.3 TerrainType (`world/overworld/terrain.py`)

```python
@dataclass
class TerrainType:
    """Represents a type of terrain on the overworld."""
    id: str                       # "grass", "forest", "mountain", etc.
    name: str                     # Display name
    color: Tuple[int, int, int]  # RGB color for rendering
    walkable: bool                # Can player walk here?
    movement_cost: float         # Time cost to move through (1.0 = normal)
    sprite_id: Optional[str]     # Sprite identifier (future)
    
# Predefined terrain types
TERRAIN_GRASS = TerrainType(...)
TERRAIN_FOREST = TerrainType(...)
TERRAIN_MOUNTAIN = TerrainType(...)
TERRAIN_WATER = TerrainType(...)
# etc.
```

### 3.4 PointOfInterest (`world/poi/base.py`)

```python
class PointOfInterest:
    """
    Base class for all Points of Interest (Dungeons, Villages, etc.)
    """
    poi_id: str                   # Unique identifier
    poi_type: str                 # "dungeon", "village", "town", etc.
    position: Tuple[int, int]     # Overworld tile position
    level: int                     # Difficulty/level rating
    name: str                      # Display name
    
    # State
    discovered: bool               # Has player found this POI?
    cleared: bool                  # Is this POI cleared/completed?
    state: Dict[str, Any]          # POI-specific state
    
    # Methods
    def can_enter(game) -> bool
    def enter(game) -> None        # Transition to POI interior
    def exit(game) -> None         # Return to overworld
    def get_description() -> str
```

### 3.5 POI Types (`world/poi/types.py`)

```python
class DungeonPOI(PointOfInterest):
    """Dungeon POI - leads to floor-based exploration."""
    floor_count: int              # Number of floors
    cleared_floors: Set[int]      # Which floors have been cleared
    difficulty_curve: str           # "linear", "exponential", etc.
    
class VillagePOI(PointOfInterest):
    """Village POI - safe zone with shops, healing."""
    buildings: List[str]          # Available buildings
    merchants: List[str]            # Merchant types available
    
class TownPOI(PointOfInterest):
    """Town POI - larger than village, more services."""
    # Similar to village but more features
    
class CampPOI(PointOfInterest):
    """Temporary camp - basic rest/healing."""
    # Minimal features
```

### 3.6 TimeSystem (`world/time/time_system.py`)

```python
class TimeSystem:
    """
    Simple time tracking system for overworld.
    """
    days: int                      # Days elapsed
    hours: int                     # Hours in current day (0-23)
    minutes: int                   # Minutes in current hour (0-59)
    
    def add_time(hours: float)     # Add time (from movement, etc.)
    def get_time_string() -> str   # "Day 3, 14:30"
    def is_daytime() -> bool       # True if between 6:00-20:00
    def get_time_of_day() -> str   # "dawn", "day", "dusk", "night"
```

---

## 4. Configuration System

### 4.1 Overworld Configuration (`config/overworld_settings.json`)

```json
{
  "world": {
    "width": 512,
    "height": 512,
    "region_size": 64,
    "seed": null
  },
  "poi": {
    "density": 0.15,
    "min_distance": 8,
    "distribution": {
      "dungeon": 0.4,
      "village": 0.3,
      "town": 0.15,
      "camp": 0.15
    }
  },
  "difficulty": {
    "scaling_type": "distance",
    "base_level": 1,
    "max_level": 20,
    "level_per_distance": 0.5
  },
  "time": {
    "movement_cost_base": 1.0,
    "terrain_costs": {
      "grass": 1.0,
      "forest": 1.5,
      "mountain": 2.0,
      "water": 999.0
    }
  },
  "starting_location": {
    "x": null,
    "y": null,
    "type": "random"
  }
}
```

### 4.2 Configuration Class (`world/overworld/config.py`)

```python
@dataclass
class OverworldConfig:
    """Overworld configuration loaded from file."""
    world_width: int
    world_height: int
    region_size: int
    poi_density: float
    poi_min_distance: int
    poi_distribution: Dict[str, float]
    difficulty_scaling: str
    base_level: int
    max_level: int
    movement_cost_base: float
    terrain_costs: Dict[str, float]
    
    @classmethod
    def load(cls) -> 'OverworldConfig'
    def save(self) -> bool
```

---

## 5. World Generation

### 5.1 Generation Pipeline (`world/overworld/generation.py`)

```python
class WorldGenerator:
    """
    Generates the overworld map with terrain and POIs.
    """
    def __init__(config: OverworldConfig, seed: Optional[int] = None)
    
    def generate() -> OverworldMap:
        """
        Generation steps:
        1. Initialize map with base terrain
        2. Generate biomes/terrain features
        3. Place POIs according to density and distribution
        4. Validate POI placement (min distance, etc.)
        5. Set starting location
        6. Return complete OverworldMap
        """
        
    def _generate_terrain() -> List[List[TerrainType]]
    def _place_pois() -> List[PointOfInterest]
    def _calculate_poi_levels() -> None
    def _set_starting_location() -> Tuple[int, int]
```

### 5.2 POI Placement Algorithm

1. **Calculate target POI count**: `world_area * poi_density`
2. **Distribute by type**: Use `poi_distribution` ratios
3. **Placement loop**:
   - Random position candidate
   - Check minimum distance from existing POIs
   - Check terrain suitability (e.g., no POIs on water)
   - Place POI if valid
   - Repeat until target count reached or max attempts
4. **Calculate levels**: Based on distance from starting location

### 5.3 Difficulty Scaling

- **Distance-based**: `level = base_level + (distance * level_per_distance)`
- **Zone-based**: Divide world into zones, each with level range
- **Hybrid**: Combine distance with zone modifiers

---

## 6. Game Mode Integration

### 6.1 New Game Mode

```python
# engine/core/states.py
class GameMode:
    OVERWORLD = "overworld"
    EXPLORATION = "exploration"  # Inside a POI
    BATTLE = "battle"
```

### 6.2 Game State Extensions

```python
# engine/core/game.py additions
class Game:
    # ... existing code ...
    
    # Overworld state
    overworld_map: Optional[OverworldMap] = None
    current_poi: Optional[PointOfInterest] = None  # If inside a POI
    time_system: Optional[TimeSystem] = None
    
    # Mode transitions
    def enter_overworld_mode(self)
    def enter_poi(self, poi: PointOfInterest)
    def exit_poi(self)
```

### 6.3 Flow Diagram

```
New Game Start
    ↓
Generate Overworld (with seed)
    ↓
Enter OVERWORLD mode
    ↓
Player moves on overworld
    ↓
Player reaches POI → Press E
    ↓
Enter POI → Switch to EXPLORATION mode
    ↓
Current floor system (existing code)
    ↓
Exit POI → Return to OVERWORLD mode
```

---

## 7. Controller System

### 7.1 OverworldController (`engine/controllers/overworld.py`)

```python
class OverworldController:
    """
    Handles input and movement for overworld mode.
    Similar to ExplorationController but for tile-based movement.
    """
    def __init__(game: Game)
    
    def handle_event(event: pygame.event.Event)
    def update(dt: float)
    
    # Movement
    def try_move(direction: Tuple[int, int])  # (dx, dy)
    def can_move_to(x, y) -> bool
    def move_player(x, y)
    
    # Interaction
    def try_enter_poi()
    def try_interact()
```

### 7.2 Movement Logic

- **Tile-based**: Player moves one tile per input
- **Movement cost**: Based on terrain type
- **Time consumption**: Add time based on movement cost
- **Collision**: Check if destination is walkable
- **POI detection**: Check if standing on POI tile

---

## 8. Save System Integration

### 8.1 Save Data Structure

```python
# engine/utils/save_system.py additions
{
    "overworld": {
        "seed": 12345,
        "width": 512,
        "height": 512,
        "player_position": [100, 150],
        "explored_tiles": [[x, y], ...],
        "regions": {
            "0,0": {...},  # Region data if needed
            "0,1": {...}
        }
    },
    "pois": {
        "dungeon_1": {
            "poi_id": "dungeon_1",
            "type": "dungeon",
            "position": [105, 155],
            "level": 5,
            "discovered": true,
            "cleared": false,
            "state": {
                "cleared_floors": [1, 2]
            }
        },
        ...
    },
    "time": {
        "days": 3,
        "hours": 14,
        "minutes": 30
    },
    "current_poi": "dungeon_1",  # or null if on overworld
    "current_floor": 2,  # Floor within current POI
    # ... existing save data ...
}
```

### 8.2 Serialization Methods

```python
def _serialize_overworld(game) -> Dict
def _deserialize_overworld(game, data: Dict)
def _serialize_pois(game) -> Dict
def _deserialize_pois(game, data: Dict)
```

---

## 9. Rendering System

### 9.1 Overworld Rendering (`ui/overworld/hud.py`)

```python
def draw_overworld(game: Game, screen: pygame.Surface):
    """
    Render the overworld map.
    """
    # 1. Render terrain tiles (visible region)
    # 2. Render explored but not visible tiles (dimmed)
    # 3. Render POI markers
    # 4. Render player icon
    # 5. Render UI overlay (time, position, etc.)
```

### 9.2 Visual Style (Phase 1 - Minimalist)

- **Terrain**: Colored rectangles (one per tile)
- **POIs**: Colored circles/squares with icons
- **Player**: Simple arrow or character icon
- **Explored areas**: Slightly dimmed but visible
- **Unexplored**: Black or dark gray

### 9.3 Camera System

- **Follow player**: Camera centers on player
- **Viewport**: Show ~20-30 tiles around player
- **Zoom**: Fixed zoom level (can add zoom later)
- **Bounds**: Clamp to map edges

---

## 10. Implementation Phases

### Phase 1: Foundation (MVP)
**Goal**: Basic overworld with tile movement and POI entry

- [ ] Create file structure
- [ ] Implement `OverworldConfig` and config loading
- [ ] Implement `TerrainType` and basic terrain types
- [ ] Implement `OverworldMap` (without regions initially)
- [ ] Implement `WorldGenerator` (simple terrain, basic POI placement)
- [ ] Implement `PointOfInterest` base class
- [ ] Implement `DungeonPOI` (first POI type)
- [ ] Add `OVERWORLD` mode to game
- [ ] Implement `OverworldController` (movement, input)
- [ ] Implement basic rendering
- [ ] Integrate with save/load system
- [ ] Test: Generate world, move around, enter dungeon

**Estimated Files**: ~8-10 new files, ~3-4 modified files

### Phase 2: POI System & Time
**Goal**: Multiple POI types, time system, better generation

- [ ] Implement `VillagePOI`, `TownPOI`, `CampPOI`
- [ ] Implement `TimeSystem`
- [ ] Integrate time with movement
- [ ] Improve POI placement algorithm
- [ ] Add POI level/difficulty calculation
- [ ] Add POI discovery system
- [ ] Improve rendering (POI icons, better visuals)
- [ ] Add time display to UI
- [ ] Test: Multiple POI types, time progression

### Phase 3: Region System & Performance
**Goal**: Support very large worlds with chunking

- [ ] Implement `Region` class
- [ ] Add region loading/unloading to `OverworldMap`
- [ ] Implement region-based generation
- [ ] Add region serialization to save system
- [ ] Optimize rendering (only render loaded regions)
- [ ] Test: Large world (512x512+), performance

### Phase 4: Polish & Expansion
**Goal**: Better visuals, features, extensibility

- [ ] Add terrain sprites (if sprite system ready)
- [ ] Add minimap
- [ ] Add fog of war improvements
- [ ] Add overworld events/encounters (foundation)
- [ ] Add resource gathering (foundation)
- [ ] Add fast travel (between discovered POIs)
- [ ] Improve POI descriptions and flavor text
- [ ] Add world seed display/selection

---

## 11. Key Design Decisions

### 11.1 World Size
- **Default**: 512x512 tiles (configurable)
- **Region size**: 64x64 tiles per region
- **Total regions**: ~64 regions for 512x512 world
- **Memory**: Only load visible regions + buffer

### 11.2 POI Density
- **Default**: 0.15 (15% of tiles have POIs) - configurable
- **Min distance**: 8 tiles between POIs
- **Distribution**: Weighted by type (dungeons most common)

### 11.3 Difficulty Scaling
- **Default**: Distance-based linear scaling
- **Formula**: `level = base_level + (distance_from_start * scaling_factor)`
- **Capped**: At max_level (e.g., 20)

### 11.4 Starting Location
- **Options**: Random, fixed center, fixed corner
- **Default**: Random (but ensure walkable terrain)

### 11.5 Movement
- **Type**: Tile-based, one tile per input
- **Time cost**: Based on terrain (configurable)
- **Directions**: 8-directional (N, NE, E, SE, S, SW, W, NW)

---

## 12. Extension Points (Future)

### 12.1 Overworld Events
- Random encounters while traveling
- Weather events
- Traveling merchants
- Bandit camps
- Resource nodes

### 12.2 POI Features
- Quest givers
- Unique NPCs
- Special events
- Dynamic POI states (villages grow, dungeons refill)

### 12.3 World Features
- Day/night cycle (visual + gameplay effects)
- Seasons (if time system expands)
- World events (meteor, dragon attack, etc.)
- Factions/territories

### 12.4 Quality of Life
- Fast travel system
- Map markers/waypoints
- Travel speed modifiers
- Mounts/vehicles (faster travel)

---

## 13. Testing Strategy

### 13.1 Unit Tests
- World generation consistency (same seed = same world)
- POI placement validation (min distance, terrain)
- Difficulty calculation accuracy
- Time system calculations

### 13.2 Integration Tests
- Save/load overworld state
- POI entry/exit transitions
- Mode switching (overworld ↔ exploration)
- Region loading/unloading

### 13.3 Manual Testing
- Generate multiple worlds, verify uniqueness
- Test movement in all directions
- Test POI entry from various positions
- Test save/load with overworld state
- Performance test with large worlds

---

## 14. Migration Strategy

### 14.1 Existing Saves
- Detect if save has overworld data
- If missing: Generate overworld on load (use deterministic seed from save)
- Place player at starting location
- Mark all POIs as undiscovered initially

### 14.2 Backward Compatibility
- Old saves without overworld: Generate new overworld
- Preserve all existing game state (inventory, stats, etc.)
- Current floor system remains unchanged (just accessed via POIs)

---

## 15. Configuration Examples

### 15.1 Small World (Testing)
```json
{
  "world": {"width": 128, "height": 128, "region_size": 64},
  "poi": {"density": 0.2, "min_distance": 5}
}
```

### 15.2 Medium World (Default)
```json
{
  "world": {"width": 512, "height": 512, "region_size": 64},
  "poi": {"density": 0.15, "min_distance": 8}
}
```

### 15.3 Large World (Epic)
```json
{
  "world": {"width": 1024, "height": 1024, "region_size": 128},
  "poi": {"density": 0.1, "min_distance": 12}
}
```

---

## 16. Next Steps

1. **Review this plan** - Confirm architecture decisions
2. **Start Phase 1** - Implement foundation
3. **Iterate** - Build, test, refine
4. **Expand** - Add features incrementally

---

## Questions & Decisions Needed

1. **Starting location**: Random or fixed? (Recommend: Random but ensure walkable)
2. **POI entry**: Stand on tile or adjacent? (Recommend: Stand on tile)
3. **POI visibility**: Always visible or need discovery? (Recommend: Need discovery)
4. **World boundaries**: Hard edges or wrap around? (Recommend: Hard edges initially)
5. **Region loading**: How many regions to keep loaded? (Recommend: 3x3 grid around player)

---

This architecture provides a solid, modular foundation that can grow with your game. Each component is designed to be independent and extensible.

