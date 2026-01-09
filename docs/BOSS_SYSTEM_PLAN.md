# Boss and Mini-Boss System Plan

## Overview
This document outlines the design for a modular boss and mini-boss system that adds exciting encounters to the dungeon.

## System Architecture

### Core Components

1. **Boss Archetype System** (`systems/bosses.py`)
   - Similar to enemy archetypes but for bosses
   - Define boss templates with base stats, scaling, and special abilities
   - Support for both mini-bosses and full bosses

2. **Name Generation System** (uses `systems/namegen/`)
   - Uses the shared name generation architecture
   - Boss-specific generator in `systems/namegen/generators/boss_generator.py`
   - Title system with thematic titles
   - Combination rules: "Name, the Title" format

3. **Spawn Logic** (integrated into `engine/managers/floor_spawning.py`)
   - Mini-boss: Every 3 floors, randomly placed (floors 3, 6, 9, etc.)
   - Final Boss: Always on the last floor (`current_poi.floor_count`)

4. **Boss Variants Registry**
   - Modular system to register different boss types
   - Easy to add new boss variations
   - Tiered system (Mini-boss tier 1-3, Final boss tier 3+)

## Design Details

### Mini-Boss System
- **Frequency**: One mini-boss every 3 floors (floors 3, 6, 9, 12, ...)
- **Placement**: Random room (prefer "lair" rooms if available)
- **Scaling**: Based on floor tier (same as enemy archetypes)
- **Stats**: Stronger than elite enemies, but weaker than final boss
- **Naming**: "Random Name, the Title" (e.g., "Gorthak, the Bloodthirsty")

### Final Boss System
- **Frequency**: One final boss on the last floor only
- **Placement**: In the "treasure" room (farthest from start)
- **Stats**: Significantly stronger than mini-bosses
- **Naming**: More epic names and titles
- **Special**: Guaranteed unique encounter

### Name Generation

#### Name Pools (Theme-based)
- **Brutal Names**: Gorthak, Krull, Zargoth, Vorax, Thulgrim
- **Dark Names**: Malachar, Nyx, Zephyrion, Morgrath, Venomir
- **Mystical Names**: Arcanus, Xylos, Sylphia, Meridian, Celestia
- **Beast Names**: Fangorn, Direclaw, Ironhide, Shadowfang, Venomscale

#### Title Pools (Tier-based)
- **Tier 1 (Early)**: the Bold, the Fierce, the Ruthless, the Cunning
- **Tier 2 (Mid)**: the Bloodthirsty, the Terrible, the Unstoppable, the Savage
- **Tier 3 (Late)**: the Destroyer, the Annihilator, the Warden, the Harbinger
- **Final Boss**: the Ancient, the Eternal, the Omnipotent, the Final Guardian

### Boss Archetype Structure

```python
@dataclass
class BossArchetype:
    id: str
    base_name_pool: List[str]  # Fallback if name gen fails
    base_title_pool: List[str]  # Fallback titles
    role: str  # "Brute", "Invoker", "Hybrid", etc.
    tier: int  # 1-3 for mini-bosses, 3+ for final bosses
    boss_type: str  # "mini_boss" or "final_boss"
    
    # Stat scaling (higher than regular enemies)
    base_hp: int
    hp_per_floor: float
    base_attack: int
    atk_per_floor: float
    base_defense: int
    def_per_floor: float
    base_xp: int  # Much higher than regular enemies
    xp_per_floor: float
    
    skill_ids: List[str]  # Special boss abilities
    ai_profile: str
```

### Stat Multipliers

**Mini-Boss** (vs Elite Enemy):
- HP: 2.0x (double elite HP)
- Attack: 1.5x
- Defense: 1.3x
- XP: 5.0x (massive XP reward)

**Final Boss** (vs Mini-Boss):
- HP: 1.8x mini-boss HP
- Attack: 1.4x
- Defense: 1.3x
- XP: 3.0x mini-boss XP

## Implementation Steps

### Phase 1: Core Infrastructure
1. Create `systems/namegen/` architecture (base, pools, patterns)
2. Create `systems/namegen/generators/boss_generator.py`
3. Create `systems/bosses.py` with boss archetype dataclass
4. Create boss registry system (similar to enemy archetypes)

### Phase 2: Boss Definitions
1. Define mini-boss archetypes (tier 1-3)
2. Define final boss archetypes (tier 3+)
3. Register all boss variants

### Phase 3: Spawn Integration
1. Add `spawn_miniboss_for_floor()` function
2. Add `spawn_final_boss()` function
3. Integrate into `spawn_all_entities_for_floor()`
4. Update floor logic to detect last floor

### Phase 4: Visual & UI
1. Add boss visual indicators (glow, size, color)
2. Update battle UI to show boss names properly
3. Add special boss introduction messages

### Phase 5: Polish
1. Balance stat scaling
2. Add more name/title variations
3. Add boss-specific room decorations (optional)

## File Structure

```
systems/
  bosses.py          # Boss archetypes and registry
  namegen/           # Shared name generation architecture
    __init__.py
    base.py
    pools.py
    patterns.py
    generators/
      boss_generator.py

engine/managers/
  floor_spawning.py  # Updated to spawn bosses

world/entities.py    # May need Enemy subclass for Boss (optional)
```

## Extension Points

The system is designed to be easily extensible:

1. **Adding New Boss Types**: Register new `BossArchetype` with `register_boss()`
2. **Custom Name Pools**: Add new pools to `systems/namegen/pools.py` (shared across all generators)
3. **Special Behaviors**: Add boss-specific AI or skills
4. **Boss Phases**: Future enhancement for multi-phase bosses
5. **Boss Loot**: Special loot tables for boss drops
6. **Extending Name Generation**: Add new generators in `systems/namegen/generators/` for dungeons, towns, etc.

## Example Boss Encounters

**Mini-Boss (Floor 3)**:
- "Gorthak, the Fierce" (Goblin Warboss)
- HP: 48, Attack: 8, Defense: 2
- Skills: Heavy Slam, War Cry

**Mini-Boss (Floor 6)**:
- "Malachar, the Bloodthirsty" (Orc Warlord)
- HP: 90, Attack: 14, Defense: 4
- Skills: Berserker Rage, Feral Claws

**Final Boss (Floor 10)**:
- "Arcanus, the Final Guardian" (Lich King)
- HP: 240, Attack: 28, Defense: 8
- Skills: Life Drain, Dark Hex, Regeneration, War Cry

