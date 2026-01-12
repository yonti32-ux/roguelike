# Architecture Quick Reference

## Current File Organization

```
roguelike_v2/
├── engine/                    # Core game engine
│   ├── core/                  # Game, GameMode, core systems
│   ├── controllers/           # Input controllers (overworld, exploration)
│   ├── scenes/                # Full-screen scenes (menus, battles)
│   ├── managers/              # System managers (camera, UI, etc.)
│   ├── battle/                # Battle system
│   └── utils/                 # Utilities (save, cheats, etc.)
│
├── world/                     # World systems
│   ├── overworld/             # Overworld map system
│   │   ├── map.py             # OverworldMap
│   │   ├── party_types.py     # Party type definitions
│   │   ├── roaming_party.py   # Party entities
│   │   ├── party_ai.py        # Party AI
│   │   └── party_manager.py   # Party management
│   ├── poi/                   # Points of Interest
│   │   ├── base.py            # Base POI class
│   │   ├── types.py           # POI type implementations
│   │   └── registry.py        # POI registry
│   ├── entities.py            # Entity base classes
│   ├── game_map.py            # Dungeon/exploration maps
│   └── ai.py                  # Entity AI
│
├── systems/                   # Game systems
│   ├── classes.py             # Character classes
│   ├── enemies.py             # Enemy definitions
│   ├── party.py               # Player party/companions
│   ├── inventory.py           # Items and inventory
│   ├── skills.py              # Skills system
│   ├── perks.py               # Perks system
│   ├── stats.py               # Stat system
│   └── progression.py         # Hero progression
│
├── ui/                        # User interface
│   ├── screens/               # Full-screen UI screens
│   ├── overworld/             # Overworld UI
│   └── hud_*.py               # HUD components
│
└── data/                      # Data files (JSON)
    ├── items.json
    └── consumables.json
```

## Proposed New Structure

```
roguelike_v2/
├── engine/                    # (unchanged)
│
├── world/
│   ├── overworld/
│   │   ├── ... (existing)
│   │   ├── battle_conversion.py    # NEW: Party → Battle
│   │   ├── allied_battle.py        # NEW: Allied parties
│   │   └── party_missions.py       # NEW: Party missions
│   │
│   ├── factions/              # NEW: Faction system
│   │   ├── __init__.py
│   │   ├── faction_manager.py
│   │   └── faction_data.py    # Faction definitions
│   │
│   └── ... (existing)
│
├── systems/
│   ├── ... (existing)
│   ├── factions.py            # NEW: Faction definitions
│   └── events.py              # NEW: Event system (future)
│
└── ui/
    ├── screens/
    │   ├── ... (existing)
    │   ├── party_screen.py     # NEW: Party management
    │   └── faction_screen.py   # NEW: Faction relations
    │
    └── components/             # NEW: Reusable UI components
        ├── stat_display.py
        ├── item_list.py
        └── quest_list.py
```

## System Integration Points

### Party → Battle Flow
```
Overworld Party Encounter
    ↓
Check Faction Relations
    ↓
Convert Party to Battle Units (battle_conversion.py)
    ↓
Check for Allied Parties (allied_battle.py)
    ↓
Create Battle Scene
    ↓
After Battle: Update Faction Relations
```

### Faction → POI Flow
```
POI Generation
    ↓
Assign Faction (faction_manager.py)
    ↓
POI Spawns Faction Parties
    ↓
POI Provides Faction Services
```

### Faction → Party Flow
```
Party Spawn
    ↓
Assign Faction (party_types.py)
    ↓
Party Follows Faction Objectives
    ↓
Party Affects Faction Relations
```

## Key Design Patterns

### 1. Registry Pattern
- **Party Types**: `party_types.py` - `register_party_type()`
- **POI Types**: `poi/registry.py` - POI registry
- **Factions**: `factions.py` - `register_faction()`
- **Enemies**: `enemies.py` - Enemy archetype registry

### 2. Manager Pattern
- **PartyManager**: Manages all roaming parties
- **FactionManager**: Manages factions and relations
- **FloorManager**: Manages dungeon floors
- **CameraManager**: Manages camera/zoom

### 3. Component Pattern
- **Entity**: Base entity with components
- **Party**: Composed of members, missions, faction
- **POI**: Composed of type, faction, state

### 4. State Pattern
- **Party Behavior**: Different AI behaviors
- **Battle States**: Different battle phases
- **Game Modes**: Overworld, Exploration, Battle

## Data Flow Examples

### Example 1: Player Attacks Party
```
1. Player moves onto party tile
2. Press E → PartyInteractionScene opens
3. Select "Attack" → Close scene
4. Check faction relations
5. Convert party to battle units
6. Check for nearby allies
7. Create battle scene
8. Battle plays out
9. After battle: Update relations, remove/weaken party
```

### Example 2: Faction War
```
1. Faction A declares war on Faction B
2. FactionManager updates relations
3. All Faction A parties become hostile to Faction B
4. Faction A parties attack Faction B POIs
5. Faction B parties defend
6. Player can join either side
7. Relations update based on outcomes
```

### Example 3: Allied Battle
```
1. Player encounters hostile party
2. Check nearby friendly parties (within 3 tiles)
3. Check faction alignment
4. Friendly parties join battle as allies
5. Allies controlled by AI in battle
6. After battle: Allies may reward player
```

## Extension Points

### Adding New Party Types
1. Define `PartyType` in `party_types.py`
2. Register with `register_party_type()`
3. Set faction_id, battle_unit_template
4. Add to faction's default_party_types

### Adding New Factions
1. Define `Faction` in `systems/factions.py`
2. Register with `register_faction()`
3. Set relations with other factions
4. Assign to POIs and parties

### Adding New POI Types
1. Create class inheriting from `PointOfInterest`
2. Implement `enter()`, `exit()` methods
3. Register in `poi/registry.py`
4. Add faction support

### Adding New Battle Units
1. Define `EnemyArchetype` in `systems/enemies.py`
2. Create battle_unit_template in party type
3. Use in `battle_conversion.py`

## Testing Checklist

### Faction System
- [ ] Factions register correctly
- [ ] Relations calculate correctly
- [ ] POIs assign to factions
- [ ] Parties assign to factions

### Battle Integration
- [ ] Parties convert to battle units
- [ ] Allied parties join battles
- [ ] Faction relations update after battles
- [ ] Battle outcomes affect parties

### UI Systems
- [ ] Party screen displays correctly
- [ ] Faction screen shows relations
- [ ] Inventory screen works
- [ ] All screens navigate correctly

## Performance Considerations

### Optimization Strategies
1. **Spatial Indexing**: Use grid/quadtree for party queries
2. **Caching**: Cache faction relations, party lists
3. **Lazy Loading**: Load UI data on demand
4. **Batch Updates**: Update parties in batches
5. **Distance Culling**: Only process nearby parties

### Monitoring
- Track party count (should stay < 50)
- Monitor faction relation calculations
- Watch UI screen load times
- Check battle creation performance

