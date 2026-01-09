# Hero Management Extraction - Overlap Analysis

## Summary
Before extracting hero management from `engine/game.py`, we need to understand what's already in the systems and avoid duplication.

---

## What's Already in Systems

### `systems/progression.py` (HeroStats class)
✅ **Already handles:**
- `grant_xp(amount)` - Hero XP and level-ups
- `apply_class(class_def)` - Applies class to hero stats
- XP curve calculation (`xp_to_next()`)
- Gold management (`add_gold()`, `spend_gold()`, `can_afford()`)
- Stat properties (max_hp, attack_power, defense, etc.)

### `systems/party.py` (CompanionState & helpers)
✅ **Already handles:**
- `CompanionState.grant_xp(amount)` - Companion XP and level-ups
- `recalc_companion_stats_for_level()` - Recomputes companion stats
- `init_companion_stats()` - Initializes companion stats
- `default_party_states_for_class()` - Creates initial party
- `get_companion()` - Gets companion template

---

## What's in `engine/game.py` (To Extract)

### 1. `_init_hero_for_class(hero_class_id)` (~45 lines)
**Purpose:** Orchestrates hero initialization for a class
**What it does:**
- Finds class definition
- Creates `HeroStats()` and calls `apply_class()`
- Creates `Inventory()` and adds starting items
- Auto-equips items
- Creates party using `default_party_states_for_class()`
- Initializes companion stats using `init_companion_stats()`

**Overlap:** ✅ Uses systems correctly - no duplication
**Extraction:** ✅ Good candidate - this is Game-specific orchestration

---

### 2. `apply_hero_stats_to_player(full_heal)` (~75 lines)
**Purpose:** Syncs `HeroStats` to the in-world `Player` entity
**What it does:**
- Copies max_hp, attack_power, defense from HeroStats to Player
- Applies crit_chance, dodge_chance, status_resist
- Sets resource pools (max_stamina, max_mana)
- Sets move speed
- Mirrors perks list to Player entity

**Overlap:** ❌ **NO overlap** - This is Game-specific (syncs HeroStats → Player entity)
**Extraction:** ✅ Good candidate - clear responsibility

---

### 3. `_sync_companions_to_hero_progression()` (~15 lines)
**Purpose:** Keeps companions in lockstep with hero level/xp
**What it does:**
- Sets all companion levels to hero level
- Sets all companion XP to hero XP

**Overlap:** ⚠️ **POTENTIAL OVERLAP** - This might be legacy/unused
**Note:** The comment says "Later we can give companions their own independent progression" and `_grant_xp_to_companions()` already handles independent progression
**Extraction:** ⚠️ Check if this is actually used before extracting

---

### 4. `_grant_xp_to_companions(amount, leveled_indices)` (~105 lines)
**Purpose:** Grants XP to all companions and handles level-ups
**What it does:**
- Iterates through party
- Calls `comp_state.grant_xp(amount)` (from party.py)
- Calls `recalc_companion_stats_for_level()` (from party.py)
- Generates level-up messages
- Tracks which companions leveled up

**Overlap:** ✅ Uses `CompanionState.grant_xp()` correctly - no duplication
**Extraction:** ✅ Good candidate - this is Game-specific orchestration (coordinates party XP)

---

### 5. `gain_xp_from_event(amount)` (~50 lines)
**Purpose:** Grants XP from map events and triggers perk selection
**What it does:**
- Calls `hero_stats.grant_xp(amount)` (from progression.py)
- Calls `_grant_xp_to_companions()` (from game.py)
- Shows messages
- Triggers perk selection scene if anyone leveled up

**Overlap:** ✅ Uses `HeroStats.grant_xp()` correctly - no duplication
**Extraction:** ✅ Good candidate - this is Game-specific orchestration

---

## Recommendations

### ✅ Safe to Extract (No Overlap)
1. **`apply_hero_stats_to_player()`** - Pure Game-specific sync logic
2. **`_grant_xp_to_companions()`** - Game-specific orchestration (uses party.py correctly)
3. **`gain_xp_from_event()`** - Game-specific orchestration (uses progression.py correctly)
4. **`_init_hero_for_class()`** - Game-specific orchestration (uses systems correctly)

### ⚠️ Check Before Extracting
1. **`_sync_companions_to_hero_progression()`** - Might be unused/legacy
   - **Action:** Search codebase for usages
   - If unused, remove it instead of extracting

---

## Proposed Extraction Structure

### `engine/hero_manager.py`
**Functions:**
- `init_hero_for_class(game, hero_class_id)` - Hero initialization
- `apply_hero_stats_to_player(game, full_heal)` - Sync stats to Player
- `grant_xp_to_companions(game, amount, leveled_indices)` - Party XP
- `gain_xp_from_event(game, amount)` - Event XP handling

**Dependencies:**
- Uses `systems.progression.HeroStats`
- Uses `systems.party.*` functions
- Uses `systems.inventory.*` functions
- Takes `Game` instance for state access

---

## Verification Checklist

Before extracting, verify:
- [ ] `_sync_companions_to_hero_progression()` is actually used
- [ ] All functions use systems correctly (no duplication)
- [ ] No circular import issues
- [ ] All Game state access is through `game` parameter

