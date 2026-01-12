# Roaming Parties System

## Overview

The roaming parties system adds dynamic NPC parties that move around the overworld map. These parties can be merchants, villagers, bandits, monsters, and more, each with their own behaviors, relationships, and interactions.

## Architecture

### Core Components

1. **Party Types** (`world/overworld/party_types.py`)
   - Defines different types of parties (merchants, villagers, bandits, monsters, etc.)
   - Each type has:
     - Alignment (friendly, neutral, hostile)
     - Enemy/ally relationships
     - Behavior patterns (patrol, travel, wander, guard, hunt, flee)
     - Combat properties
     - Visual representation (color, icon)
     - Spawn properties

2. **Roaming Party** (`world/overworld/roaming_party.py`)
   - Represents a single party instance on the map
   - Tracks position, target, path, and state
   - Handles movement and behavior state

3. **Party AI** (`world/overworld/party_ai.py`)
   - Implements movement and behavior logic
   - Handles pathfinding
   - Manages different behavior patterns:
     - **Patrol**: Patrols a small area
     - **Travel**: Travels between POIs (towns, villages)
     - **Wander**: Random wandering
     - **Guard**: Guards a specific location
     - **Hunt**: Actively hunts enemies
     - **Flee**: Flees from threats

4. **Party Manager** (`world/overworld/party_manager.py`)
   - Manages all parties on the overworld
   - Handles spawning, updating, and removal
   - Provides query functions (get party at position, parties in range, etc.)

## Predefined Party Types

### Friendly/Neutral Parties

- **Merchant Caravan** (`merchant`)
  - Travels between towns and villages
  - Can be traded with
  - Carries gold and items
  - Enemies: bandits, monsters

- **Traveling Villagers** (`villager`)
  - Travels between settlements
  - Friendly to player
  - Enemies: bandits, monsters

- **Guard Patrol** (`guard`)
  - Patrols around towns
  - Attacks bandits and monsters
  - Protects merchants and villagers

- **Adventuring Party** (`adventurer`)
  - Wanders the world
  - Can trade, recruit, and give quests
  - Friendly to player

### Hostile Parties

- **Bandit Gang** (`bandit`)
  - Wanders the wilderness
  - Attacks merchants, villagers, guards
  - Can be attacked by player
  - Avoids towns

- **Monster Pack** (`monster`)
  - Wanders the wilderness
  - Attacks most other parties
  - Can be attacked by player
  - Avoids settlements

- **Wolf Pack** (`wolf`)
  - Hunts in the wilds
  - Attacks merchants and villagers
  - Fast and aggressive

## Integration

### Overworld Map

The `OverworldMap` class now includes a `PartyManager` instance that manages all roaming parties.

### Game Loop

- Parties are updated in `OverworldController.update()`
- Parties are rendered in `ui/overworld/hud.py`
- Initial parties are spawned when overworld is initialized

### Interactions

The system checks for party interactions when:
- Player moves onto a party's position
- Player is near a hostile party

Currently implemented:
- Basic interaction messages
- Combat trigger placeholders (TODO: implement combat)

Future enhancements:
- Trade interface for merchants
- Quest dialog for adventurers
- Combat system integration
- Recruitment system

## Extensibility

The system is designed to be easily extensible:

### Adding New Party Types

1. Create a new `PartyType` in `party_types.py`:
```python
NEW_PARTY_TYPE = register_party_type(
    PartyType(
        id="new_type",
        name="New Party Type",
        description="Description here",
        alignment=PartyAlignment.NEUTRAL,
        behavior=PartyBehavior.WANDER,
        # ... other properties
    )
)
```

2. Set up relationships:
```python
NEW_PARTY_TYPE.enemy_types = {"bandit"}
NEW_PARTY_TYPE.ally_types = {"merchant"}
```

### Adding New Behaviors

1. Add new `PartyBehavior` enum value
2. Implement behavior logic in `party_ai.py`:
   - Add helper function (e.g., `get_next_<behavior>_target()`)
   - Add case in `update_party_ai()`

### Customizing Spawn Rates

Adjust `spawn_weight` in party type definitions. Higher values = more likely to spawn.

## Configuration

- **Initial Party Count**: Set in `game.py` `_init_overworld()` (default: 10)
- **Max Parties**: Set in `PartyManager.__init__()` (default: 20)
- **Spawn Interval**: Set in `PartyManager.__init__()` (default: 30 seconds)

## Future Enhancements

1. **Combat Integration**
   - Trigger combat when player encounters hostile parties
   - Party vs party combat
   - Loot from defeated parties

2. **Trade System**
   - Merchant trading interface
   - Dynamic prices based on location
   - Special items from traveling merchants

3. **Quest System**
   - Quests from adventuring parties
   - Escort missions
   - Bounty hunting

4. **Recruitment**
   - Recruit members from friendly parties
   - Temporary allies
   - Mercenary hiring

5. **Advanced AI**
   - Party formations
   - Coordinated attacks
   - Dynamic relationships (reputation system)

6. **Visual Enhancements**
   - Sprite support for parties
   - Animations
   - Party size indicators

## Files Modified/Created

### New Files
- `world/overworld/party_types.py` - Party type definitions
- `world/overworld/roaming_party.py` - Party entity
- `world/overworld/party_ai.py` - AI system
- `world/overworld/party_manager.py` - Party manager

### Modified Files
- `world/overworld/__init__.py` - Added exports
- `world/overworld/map.py` - Added party manager
- `engine/core/game.py` - Initialize parties on overworld creation
- `engine/controllers/overworld.py` - Update parties and check interactions
- `ui/overworld/hud.py` - Render parties on map

