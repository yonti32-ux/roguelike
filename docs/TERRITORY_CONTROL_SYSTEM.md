# Territory Control System

## Overview

A modular system for managing faction territories on the overworld map. This system adds visual representation of faction control, border conflicts, dynamic territory changes, and reputation-based effects.

## Design Principles

1. **Modular**: Completely optional system that can be enabled/disabled
2. **Non-breaking**: Works alongside existing systems without requiring core changes
3. **Configurable**: All features can be toggled and tuned via config
4. **Extensible**: Easy to add new features and mechanics

## Architecture

### Core Components

1. **TerritoryManager** (`world/overworld/territory_manager.py`)
   - Manages territory data (which faction controls which areas)
   - Handles territory updates and changes
   - Detects border conflicts
   - Integrates with FactionManager

2. **Territory Data Structure**
   - Chunk-based system (groups of tiles into territories)
   - Each territory has: faction_id, strength, last_update_time
   - Border tiles tracked for conflict detection

3. **Visual Rendering** (`ui/overworld/territory_renderer.py`)
   - Optional overlay showing territory boundaries
   - Color-coded by faction
   - Border highlighting for conflicts
   - Toggle on/off

4. **Reputation Integration**
   - Check player reputation when entering territories
   - Effects: access restrictions, prices, hostility
   - Messages and warnings

5. **Border Conflict System**
   - Detect adjacent territories of hostile factions
   - Generate conflict events
   - Visual indicators (red borders, warning markers)

## Data Structure

```python
@dataclass
class Territory:
    """Represents a territory controlled by a faction."""
    territory_id: str
    faction_id: str
    chunk_x: int  # Chunk coordinates
    chunk_y: int
    strength: float  # 0.0 to 1.0, how strongly controlled
    last_update_time: float  # Time when last updated
    border_tiles: Set[Tuple[int, int]]  # Tiles on the border
    center_poi_id: Optional[str]  # POI that anchors this territory
```

## Features

### 1. Territory Visibility
- Optional overlay showing faction territories
- Color-coded by faction alignment (Good=Blue, Neutral=Gray, Evil=Red)
- Semi-transparent overlay so terrain is still visible
- Toggle with key (default: T)

### 2. Border Conflicts
- Detect when hostile factions have adjacent territories
- Visual indicators: red borders, warning markers
- Conflict events: skirmishes, raids, territory changes
- Messages when conflicts occur

### 3. Territory Changes Over Time
- Territories can expand/contract based on:
  - Faction strength (number of POIs)
  - Player actions (helping/harming factions)
  - Time passing
  - Border conflicts
- Gradual changes, not instant

### 4. Reputation Effects
- When entering a territory:
  - Check player reputation with controlling faction
  - Low reputation (< -50): Hostile, may be attacked
  - Neutral (-50 to 50): Normal access
  - High reputation (> 50): Friendly, discounts, help
- Visual indicators on territory overlay

## Integration Points

### With Existing Systems

1. **FactionManager**: Uses existing faction data and relations
2. **OverworldMap**: Adds territory data, doesn't modify core map
3. **POI System**: Territories can be anchored to POIs
4. **Party System**: Parties respect territory boundaries
5. **Time System**: Territory updates based on game time

### Configuration

```json
{
  "territory_control": {
    "enabled": true,
    "chunk_size": 8,
    "update_interval_hours": 24.0,
    "show_overlay": false,
    "overlay_opacity": 0.3,
    "border_conflict_threshold": -50,
    "reputation_effects": {
      "hostile_threshold": -50,
      "friendly_threshold": 50,
      "price_modifier_friendly": 0.9,
      "price_modifier_hostile": 1.2
    }
  }
}
```

## Implementation Plan

### Phase 1: Core System (Non-breaking)
1. Create TerritoryManager class
2. Add territory data to OverworldMap (optional)
3. Initialize territories from POI positions
4. Basic territory queries (get_territory_at, get_faction_at)

### Phase 2: Visualization (Optional)
1. Territory overlay rendering
2. Toggle key binding
3. Color coding by faction
4. Border visualization

### Phase 3: Border Conflicts
1. Border detection algorithm
2. Conflict event generation
3. Visual indicators
4. Conflict resolution mechanics

### Phase 4: Dynamic Changes
1. Time-based territory updates
2. Territory expansion/contraction
3. Player action effects
4. Event system integration

### Phase 5: Reputation Integration
1. Reputation checking on territory entry
2. Access restrictions
3. Price modifiers
4. Visual feedback

## Usage Example

```python
# In overworld initialization
if config.territory_control.enabled:
    territory_manager = TerritoryManager(overworld_map, faction_manager)
    overworld_map.territory_manager = territory_manager
    territory_manager.initialize_from_pois()

# In overworld rendering
if game.show_territory_overlay and overworld_map.territory_manager:
    draw_territory_overlay(screen, overworld_map, territory_manager)

# In player movement
if overworld_map.territory_manager:
    territory = overworld_map.territory_manager.get_territory_at(x, y)
    if territory:
        check_reputation_effects(game, territory)
```

## Benefits

1. **Adds depth** without breaking existing gameplay
2. **Visual feedback** makes world feel more alive
3. **Strategic choices** - player actions have consequences
4. **Emergent gameplay** - conflicts create interesting situations
5. **Modular** - can be disabled if not desired

## Future Enhancements

- Territory-specific events
- Faction quests to expand territories
- Player-controlled territories
- Trade routes between territories
- Siege mechanics
- Diplomacy system

