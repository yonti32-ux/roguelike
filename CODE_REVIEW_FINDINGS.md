# Code Review Findings - Pre-Expansion Checklist

## Critical Issues (Fix Before Expanding)

### 1. File Size - Major Refactoring Needed
- **`ui/hud.py`**: 2,424 lines - Should be split into:
  - `ui/battle_hud.py` - Battle UI components
  - `ui/exploration_hud.py` - Exploration UI
  - `ui/overlays.py` - Character sheet, inventory, shop overlays
  - `ui/components.py` - Reusable UI components (bars, cards, etc.)

- **`engine/game.py`**: 2,083 lines - Should be split into:
  - `engine/game_state.py` - Core state management
  - `engine/floor_manager.py` - Floor generation and management
  - `engine/spawn_manager.py` - Enemy/entity spawning logic
  - `engine/battle_manager.py` - Battle orchestration

- **`engine/battle_scene.py`**: 1,627 lines - Could split into:
  - Keep core battle logic
  - Extract `battle_ai.py` - Enemy AI decision making
  - Extract `battle_rendering.py` - Drawing logic

### 2. Type Safety Issues

**Location**: `engine/battle_scene.py:41`
```python
entity: object  # ❌ Too generic
```
**Fix**: Use proper union type
```python
entity: Player | Enemy  # ✅ Specific
```

**Location**: Several functions missing return type hints

### 3. Magic Numbers Should Be Constants

**Add to `settings.py`:**
```python
# Battle settings
BATTLE_GRID_WIDTH = 11
BATTLE_GRID_HEIGHT = 5
BATTLE_CELL_SIZE = 80
BATTLE_ENEMY_TIMER = 0.6
MAX_BATTLE_ENEMIES = 3
BATTLE_AI_DEFENSIVE_HP_THRESHOLD = 0.4
BATTLE_AI_SKILL_CHANCE = 0.4

# Default stats
DEFAULT_PLAYER_MAX_HP = 24
DEFAULT_PLAYER_ATTACK = 5
DEFAULT_PLAYER_STAMINA = 6
DEFAULT_COMPANION_STAMINA = 4
DEFAULT_ENEMY_STAMINA = 6

# Skill slots
MAX_SKILL_SLOTS = 4  # SKILL_1 to SKILL_4
```

### 4. Code Duplication

#### Status Indicator Rendering
- Duplicated in `battle_scene.py` lines 1227-1244 and 1317-1332
- Also in `hud.py` for unit cards
- **Fix**: Extract to `ui/components.py::draw_status_indicators()`

#### Resource Bar Drawing
- `_draw_bar()` and `_draw_resource_bar_with_label()` in `hud.py` are good
- But status indicators are repeated
- **Fix**: Centralize status rendering

#### Companion Stat Initialization
- Duplicated logic in `battle_scene.py` around lines 193-251 and 240-251
- Similar patterns in `game.py`
- **Fix**: Extract to `systems/party.py` helper function

### 5. Inconsistent Error Handling

**Problem**: Mix of patterns:
```python
# Pattern 1: Defensive
hero_max_stamina = int(getattr(self.player, "max_stamina", 0) or 0)

# Pattern 2: Direct access (risky)
self.player.max_hp = max_hp

# Pattern 3: Broad exception handling
except Exception:  # Too broad
```

**Recommendation**: 
- Use defensive `getattr()` consistently for optional attributes
- Use specific exception types where possible
- Document which attributes are guaranteed vs optional

### 6. Import Organization

**Location**: `ui/hud.py:248`
```python
def _draw_battle_skill_hotbar(...):
    if input_manager is not None:
        try:
            from systems.input import InputAction  # ❌ Local import
```
**Fix**: Move to top of file

### 7. Legacy Code Markers

Found many comments like:
- "Backwards-compatible alias"
- "Legacy path"
- "NEW" markers
- "For now we still only use..."

**Recommendation**: 
- Audit these areas
- Remove truly unused legacy code
- Update comments to reflect current architecture
- Consider deprecation warnings for old patterns

### 8. Resource Pool Management

**Problem**: Stamina/mana tracking scattered across:
- `battle_scene.py` - Initialization and usage
- `game.py` - Hero stats syncing
- `hud.py` - Display
- `systems/party.py` - Companion stats

**Fix**: 
- Create `ResourcePool` dataclass
- Centralize regeneration logic
- Document ownership (who owns current vs max?)

### 9. Missing Documentation

**Areas needing better docs:**
- Battle turn flow
- Resource regeneration rules
- Status effect stacking/refresh rules
- Companion stat calculation formulas

### 10. Minor Issues

- **Unused variable**: `main.py:38` has duplicate `_game_snapshot()` function definition (lines 14-24 and 38-49)
- **Type hints**: Some functions use `List` instead of `list` (Python 3.9+ style)
- **Constants**: Several hardcoded UI dimensions could be in `settings.py`

## Recommended Refactoring Order

1. **Phase 1** (Quick wins):
   - Extract magic numbers to `settings.py`
   - Fix duplicate `_game_snapshot()` in `main.py`
   - Move local import to top of `hud.py`
   - Add missing type hints for `BattleUnit.entity`

2. **Phase 2** (Medium effort):
   - Extract status indicator rendering to shared function
   - Extract companion stat initialization helper
   - Centralize resource pool logic
   - Add constants for UI dimensions

3. **Phase 3** (Major refactoring):
   - Split `hud.py` into focused modules
   - Split `game.py` into managers
   - Audit and remove legacy code paths
   - Improve error handling consistency

## Testing Recommendations

Before expanding, consider adding:
- Unit tests for resource pool management
- Tests for status effect application
- Tests for companion stat calculations
- Integration tests for battle flow

## Notes

The codebase is generally well-structured with good separation of concerns. The main issues are:
1. File size (making maintenance harder)
2. Some technical debt (legacy code paths)
3. Missing abstractions for common patterns (status rendering, resource pools)

These are **quality-of-life** improvements rather than critical bugs. The code works, but would benefit from refactoring before adding new features.

