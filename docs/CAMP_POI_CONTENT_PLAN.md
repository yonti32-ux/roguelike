# Camp POI Content Plan

## Overview

Camps are **temporary safe spots** scattered across the overworld, providing basic rest and minimal services. They are simpler and more rustic than villages, designed for quick stops during long journeys.

## Design Philosophy

- **Simpler than villages**: No full map generation, no complex buildings
- **Temporary feel**: Quick stop, not a destination
- **Basic services only**: Rest/healing, maybe minimal trading
- **Faction-aware**: Can be friendly, neutral, or hostile depending on faction

## Proposed Content

### 1. Camp Map/Interior

**Option A: Simple Campfire Scene (Recommended)**
- Small, single-screen area (maybe 20x20 tiles)
- Central campfire (visual element, not interactive)
- A few tents or lean-tos around the perimeter
- Simple ground tiles (grass/dirt)
- No complex building interiors

**Option B: Menu-Based (Simpler)**
- No map at all - just a menu screen when entering
- Options: Rest, Trade, Leave
- Fast and simple, but less immersive

**Recommendation**: Option A for immersion, but keep it very simple.

### 2. Core Features

#### 2.1 Rest/Healing
- **Free or very cheap rest** (maybe 1-5 gold, or free for friendly factions)
- Full HP restoration
- Full stamina/mana restoration
- Simple message: "You rest by the campfire and feel refreshed."

#### 2.2 Traveling Merchant (Optional)
- **Simple merchant** with limited stock
- Only consumables (potions, food items)
- Maybe 3-5 items max
- Stock refreshes on each visit (or persists?)
- Prices slightly higher than village shops (traveling merchant premium)

#### 2.3 Camp Supplies (Optional)
- **Basic consumables** available for purchase
- Health potions, food items
- Limited selection (2-3 items)

### 3. Faction Integration

Camps can belong to different factions, affecting:
- **Friendly camps** (player's faction or neutral):
  - Free rest
  - Friendly merchant
  - Safe zone
  
- **Neutral camps**:
  - Cheap rest (1-3 gold)
  - Neutral merchant
  - Safe zone
  
- **Hostile camps** (enemy faction):
  - Cannot rest (or risky rest with chance of ambush)
  - No merchant
  - May trigger combat encounter

### 4. Visual Design

- **Campfire**: Central visual element (animated?)
- **Tents**: 2-4 simple tents around the perimeter
- **NPCs**: Maybe 1-2 NPCs (merchant, guard, or just decorative)
- **Terrain**: Simple grass/dirt tiles
- **Atmosphere**: Cozy, rustic, temporary

### 5. Implementation Details

#### 5.1 Camp Map Generation
```python
def generate_camp(level: int, camp_name: str, seed: Optional[int] = None) -> GameMap:
    """
    Generate a simple camp map.
    - Small size (20x20 to 30x30 tiles)
    - Central campfire area
    - Tents around perimeter
    - Simple ground tiles
    """
```

#### 5.2 Camp Services
- `rest_at_camp(game, cost=0)` - Free/cheap rest
- `open_camp_merchant(game)` - Simple merchant with consumables only

#### 5.3 Camp NPCs
- **Merchant NPC** (if merchant available)
- **Guard NPC** (decorative, or provides info)
- Maybe no NPCs at all - just the campfire

### 6. Comparison with Other POIs

| Feature | Camp | Village | Town |
|---------|------|---------|------|
| Map Size | Small (20x30) | Medium-Large | Large |
| Rest/Healing | Free/Cheap | Paid (inn) | Paid (inn) |
| Shop | Simple (consumables only) | Full shop | Multiple shops |
| Recruitment | No | Yes (tavern) | Yes |
| Quests | No | Yes (elder) | Yes |
| Buildings | None (just tents) | Multiple | Many |
| Complexity | Minimal | Medium | High |

### 7. Future Enhancements (Phase 2+)

- **Camp upgrades**: Player can improve camps they control
- **Camp events**: Random events at camps (traveler stories, ambushes)
- **Camp storage**: Temporary storage for items
- **Camp crafting**: Basic crafting station
- **Camp companions**: Temporary companions that join at camp

### 8. Questions to Consider

1. **Should camps have a map at all?** Or just a menu?
   - **Recommendation**: Simple map for immersion

2. **Should camps be persistent?** Or do they disappear/reappear?
   - **Recommendation**: Persistent, but simple

3. **Should camps have NPCs?** Or just be empty?
   - **Recommendation**: 1-2 NPCs max (merchant, maybe guard)

4. **Should camps have faction-specific content?**
   - **Recommendation**: Yes, affects rest cost and merchant availability

5. **Should camps be safe zones?** (No combat)
   - **Recommendation**: Yes for friendly/neutral, maybe ambush for hostile

## Recommended Implementation (Phase 1)

### Minimal Viable Camp:
1. Simple camp map (20x30 tiles)
2. Central campfire (visual)
3. 2-3 tents (decorative)
4. Free rest (full heal)
5. Optional: Simple merchant with 3-5 consumables

### CampPOI Implementation:
```python
class CampPOI(PointOfInterest):
    def __init__(...):
        self.has_merchant: bool = False  # Based on faction/level
        self.rest_cost: int = 0  # Free for friendly, cheap for neutral
    
    def enter(self, game):
        # Generate simple camp map
        # Place player at entrance
        # Show campfire and tents
    
    def rest_at_camp(self, game):
        # Full heal, restore resources
        # Cost based on faction relations
```

## Implementation Status

### ✅ Phase 1 Complete

1. ✅ **Camp Map Generation** - Simple map with campfire and tents
2. ✅ **Rest Functionality** - `rest_at_camp()` service with faction-aware pricing
3. ✅ **Camp Merchant** - Simple merchant with consumables only (3-5 items)
4. ✅ **NPC Placement** - Friendly camps have 1-2 NPCs (merchant, guard, traveler)
5. ✅ **Hostile Camps** - Hostile camps spawn enemy entities instead of NPCs
6. ✅ **Campfire Interaction** - Players can rest by interacting with campfire
7. ✅ **Camp POI Integration** - Full integration with POI system, persistent state

### 📁 File Structure

```
world/camp/
  - __init__.py          # Exports camp generation
  - tiles.py             # Camp-specific tiles (ground, fire, tent)
  - npcs.py              # Camp NPC dataclasses (stubs for now)
  - generation.py        # Camp map generation with NPC/enemy placement

systems/camp/
  - __init__.py          # Exports camp services
  - services.py          # rest_at_camp(), open_camp_merchant()

world/poi/types.py       # CampPOI class with enter/exit logic
engine/controllers/exploration.py  # Camp NPC and campfire interaction handling
```

### 🎮 How It Works

1. **Entering a Camp**: Player enters from overworld, camp map is generated (or loaded from state)
2. **Friendly Camps**: 
   - Have 1-2 NPCs (merchant, guard, traveler)
   - Campfire allows free/cheap rest
   - Merchant NPC opens camp shop
3. **Hostile Camps**:
   - Spawn 2-4 enemy entities
   - Campfire rest is blocked
   - Combat can occur
4. **Interactions**:
   - Press E near campfire → rest (if friendly)
   - Press E near merchant NPC → open shop
   - Press E near guard/traveler → dialogue

### 🔜 Future Enhancements

- Faction-based rest costs (free for friendly, cheap for neutral)
- Camp destruction/clearing mechanics
- Camp respawn system
- Natural/hostile camps (non-faction)
- Camp events and random encounters

