# Overworld Enemy Spawning

## Overview

The overworld enemy system has been updated to use the new modular difficulty system, allowing higher-level enemies to appear as the player progresses.

---

## How It Works

### Player Level as "Floor"

The overworld system treats **player level** as the "floor" for enemy selection:
- `player_level = 1` → Early game enemies (floors 1-4)
- `player_level = 3` → Mid game enemies (floors 3-8)
- `player_level = 5+` → Late game enemies (floors 5+)

### Enemy Selection Priority

1. **Party Type Template** (if set): Uses `party_type.battle_unit_template` (hardcoded archetype)
2. **New Difficulty System**: Uses `choose_archetype_for_player_level()` to select based on player level
3. **Fallback**: Uses old strength-based system

### Example Flow

```python
# Overworld party spawns
party_type = GOBLIN_WARBAND  # battle_unit_template="goblin_skirmisher"

# If battle_unit_template is set, use it
if party_type.battle_unit_template:
    archetype = get_archetype("goblin_skirmisher")
    
# Otherwise, use new system
else:
    archetype = choose_archetype_for_player_level(
        player_level=5,  # Player is level 5
        preferred_tags=["beast"]  # Optional
    )
    # Returns enemy with spawn_min_floor <= 5 and spawn_max_floor >= 5
```

---

## Current Behavior

### Party Types with Templates

These party types have hardcoded enemy archetypes:
- `GOBLIN_WARBAND` → `goblin_skirmisher`
- `BANDIT_PARTY` → `bandit_cutthroat`
- `ORC_RAIDING_PARTY` → `orc_raider`
- `MONSTER_PACK` → `orc_raider`
- `SKELETON_WARBAND` → `skeleton_archer`
- `KNIGHT_PATROL` → `dread_knight` (allied)
- `ASSASSIN_CREW` → `shadow_stalker`
- `DEMON_PACK` → `voidspawn_mauler`
- `WARLOCK_COVEN` → `cultist_harbinger`
- `NECROMANCER_CULT` → `necromancer`

### Party Types Without Templates

These use the new difficulty system:
- Any party type without `battle_unit_template` set
- Fallback when template archetype is not found

---

## Dungeon Floor Count

### Current Configuration

Most dungeons have **5 floors** (configurable):
- Low level (1-3): 3 floors
- Mid level (4-6): 4 floors
- High level (7-9): 5 floors
- Very high level (10+): 6-20 floors

### Enemy Spawn Ranges

Enemies are configured with spawn ranges that work for 5-floor dungeons:
- **Early game**: `spawn_min_floor=1, spawn_max_floor=4` (floors 1-4)
- **Mid game**: `spawn_min_floor=3, spawn_max_floor=8` (floors 3-8)
- **Late game**: `spawn_min_floor=5, spawn_max_floor=None` (floors 5+)

This means:
- ✅ Early game enemies appear on floors 1-4
- ✅ Mid game enemies appear on floors 3-8 (overlaps with early)
- ✅ Late game enemies appear on floors 5+ (works for 5-floor dungeons)

---

## Making Higher Floor Enemies Appear in Overworld

### Option 1: Use New Difficulty System (Recommended)

Remove or don't set `battle_unit_template` on party types, and they'll automatically use `choose_archetype_for_player_level()`:

```python
# Old way (hardcoded)
GOBLIN_WARBAND = PartyType(
    ...
    battle_unit_template="goblin_skirmisher",  # Always goblin_skirmisher
)

# New way (dynamic)
GOBLIN_WARBAND = PartyType(
    ...
    # battle_unit_template=None,  # Uses new system
    # Will spawn appropriate enemies for player level
)
```

### Option 2: Update Party Type Templates

Update `battle_unit_template` to use higher-level enemies for stronger party types:

```python
DEMON_PACK = PartyType(
    ...
    combat_strength=5,
    battle_unit_template="voidspawn_mauler",  # Late game enemy
    min_level=5,  # Only spawns when player is level 5+
)
```

### Option 3: Use Tag-Based Selection

Use `choose_archetype_for_player_level()` with preferred tags:

```python
# In battle_conversion.py
archetype = choose_archetype_for_player_level(
    player_level=player_level,
    preferred_tags=["undead", "late_game"],  # Prefer late game undead
)
```

---

## Recommendations

### For 5-Floor Dungeons

Current spawn ranges work well:
- Early enemies: floors 1-4 ✅
- Mid enemies: floors 3-8 ✅ (appears on floors 3-5)
- Late enemies: floors 5+ ✅ (appears on floor 5)

### For Overworld

1. **Keep templates for themed parties** (goblins always spawn goblins)
2. **Use new system for generic parties** (monsters spawn appropriate level)
3. **Update party `min_level`/`max_level`** to control when they spawn

### Example: Dynamic Overworld Enemies

```python
# Generic monster pack - uses new system
MONSTER_PACK = PartyType(
    ...
    battle_unit_template=None,  # Use new system
    min_level=1,
    max_level=100,
    # Will spawn goblin_skirmisher at level 1, orc_raider at level 3, dread_knight at level 5+
)
```

---

## Testing

To test overworld enemy spawning:
1. Set player level to different values
2. Spawn overworld parties
3. Check which enemy archetypes appear
4. Verify they match expected difficulty for player level

---

## Future Improvements

1. **Tag-based party types**: Party types could specify preferred enemy tags
2. **Difficulty scaling**: Overworld enemies could scale with dungeon depth nearby
3. **Regional enemies**: Different regions could have different enemy pools
4. **Time-based spawning**: Some enemies only spawn at certain times
