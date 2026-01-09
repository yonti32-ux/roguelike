# Game.py Trim Plan

## Current State
- **File**: `engine/game.py`
- **Size**: 1712 lines
- **Main Class**: `Game` (contains everything)

## Analysis

The `Game` class has several distinct responsibilities that can be extracted:

### 1. Floor Spawning Logic (~605 lines) ⭐ **HIGHEST PRIORITY**
**Location**: Lines ~1094-1702

**Functions to extract**:
- `_choose_enemy_type_for_floor()` (~15 lines)
- `spawn_enemies_for_floor()` (~220 lines)
- `spawn_events_for_floor()` (~110 lines)
- `spawn_chests_for_floor()` (~120 lines)
- `spawn_merchants_for_floor()` (~140 lines)

**New file**: `engine/floor_spawning.py`
- Contains all entity spawning logic for floors
- Takes `Game` instance as parameter for access to game state
- Called from `load_floor()` method

**Benefits**:
- Removes ~600 lines from Game class
- Clear separation: spawning logic is isolated
- Easier to test spawning independently
- Can be extended without bloating Game class

---

### 2. Hero/Character Management (~285 lines) ⭐ **HIGH PRIORITY**
**Location**: Lines ~563-809

**Functions to extract**:
- `_init_hero_for_class()` (~50 lines)
- `apply_hero_stats_to_player()` (~75 lines)
- `_sync_companions_to_hero_progression()` (~20 lines)
- `_grant_xp_to_companions()` (~100 lines)
- `gain_xp_from_event()` (~40 lines)

**New file**: `engine/hero_manager.py`
- Handles hero initialization, stats application, XP management
- Companion XP and leveling logic
- Takes `Game` instance for state access

**Benefits**:
- Removes ~285 lines from Game class
- Centralizes character progression logic
- Easier to modify hero/companion systems

---

### 3. Message/Logging System (~60 lines) ⭐ **MEDIUM PRIORITY**
**Location**: Lines ~499-558

**Functions to extract**:
- `last_message` property (getter/setter) (~50 lines)
- `add_message()` (~10 lines)

**New file**: `engine/message_log.py`
- Simple `MessageLog` class
- Manages exploration log and last message
- Can be instantiated in Game.__init__

**Benefits**:
- Removes ~60 lines
- Cleaner interface for messages
- Could add features like message history UI later

---

### 4. UI/Overlay Management (~280 lines) ⭐ **MEDIUM PRIORITY**
**Location**: Lines ~212-493

**Functions to extract**:
- `toggle_inventory_overlay()` (~20 lines)
- `toggle_character_sheet_overlay()` (~20 lines)
- `toggle_battle_log_overlay()` (~15 lines)
- `toggle_exploration_log_overlay()` (~15 lines)
- `is_overlay_open()` (~10 lines)
- `cycle_character_sheet_focus()` (~25 lines)
- `cycle_inventory_focus()` (~20 lines)
- `get_available_screens()` (~10 lines)
- `switch_to_screen()` (~25 lines)
- `cycle_to_next_screen()` (~30 lines)
- `equip_item_for_inventory_focus()` (~100 lines)

**New file**: `engine/ui_manager.py`
- `UIManager` class that handles all overlay/screen state
- Manages focus indices, screen switching, etc.
- Takes `Game` instance for state access

**Benefits**:
- Removes ~280 lines
- Centralizes UI state management
- Easier to add new overlays/screens

---

## Implementation Order

### Phase 1: Floor Spawning (Biggest win - ~600 lines)
1. Create `engine/floor_spawning.py`
2. Move all `spawn_*_for_floor` methods
3. Update `load_floor()` to call spawning module
4. Test thoroughly

**Result**: 1712 → ~1112 lines

### Phase 2: Hero Management (~285 lines)
1. Create `engine/hero_manager.py`
2. Move hero initialization and XP methods
3. Update Game class to use hero manager
4. Test thoroughly

**Result**: ~1112 → ~827 lines

### Phase 3: Message Log (~60 lines)
1. Create `engine/message_log.py`
2. Create `MessageLog` class
3. Replace `last_message` property with `self.message_log`
4. Update all message references

**Result**: ~827 → ~767 lines

### Phase 4: UI Manager (~280 lines)
1. Create `engine/ui_manager.py`
2. Move all overlay/screen management methods
3. Update Game class to use UI manager
4. Test thoroughly

**Result**: ~767 → ~487 lines

---

## Final Target
- **Before**: 1712 lines
- **After**: ~487 lines (71% reduction!)
- **New modules**: 4 focused, single-responsibility modules

---

## Benefits Summary

1. **Maintainability**: Each module has a clear, focused purpose
2. **Testability**: Can test spawning, hero management, etc. independently
3. **Readability**: Game class becomes much easier to understand
4. **Extensibility**: Easy to add new spawning types, UI features, etc.
5. **No functionality changes**: All refactoring preserves existing behavior

---

## Risks & Considerations

1. **Circular imports**: Need to be careful with Game references
   - Solution: Use TYPE_CHECKING for type hints, pass Game instance at runtime
2. **State access**: Extracted modules need access to Game state
   - Solution: Pass `game` instance as first parameter to all functions
3. **Testing**: Need to verify all functionality still works
   - Solution: Test each phase thoroughly before moving to next

---

## Recommendation

**Start with Phase 1 (Floor Spawning)** - it's the biggest win with the least risk. The spawning logic is very self-contained and doesn't have complex interdependencies.

