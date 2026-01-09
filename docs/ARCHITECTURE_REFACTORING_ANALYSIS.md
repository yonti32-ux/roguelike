# Comprehensive Architecture & Refactoring Analysis

**Date:** 2025-01-09  
**Status:** Current State Assessment & Recommendations

## Executive Summary

The codebase shows a **well-organized structure** with clear separation of concerns, but several areas would benefit from refactoring to improve maintainability, reduce complexity, and prepare for future expansion.

### Key Findings
- ✅ **Strong Foundation**: Good module organization, clear separation between systems, engine, UI, and world
- ⚠️ **Large Files**: Several files exceed 1500 lines, making maintenance challenging
- ⚠️ **Code Duplication**: Significant duplication in UI rendering code
- ⚠️ **Technical Debt**: Some legacy code paths and inconsistent patterns
- ✅ **Modern Patterns**: Good use of type hints, dataclasses, and TYPE_CHECKING

---

## Current Architecture Overview

### Directory Structure

```
roguelike_v2/
├── engine/              # Core game engine and systems
│   ├── battle/          # ✅ Well-organized battle system (already refactored)
│   ├── controllers/     # ✅ Input and game mode controllers
│   ├── core/            # ✅ Core game loop and state management
│   ├── managers/        # ✅ Specialized managers (hero, floor, messages)
│   ├── scenes/          # ✅ Game scenes (menus, battle, etc.)
│   ├── sprites/         # ✅ Sprite management system
│   └── utils/           # ✅ Utility functions
├── systems/             # ✅ Game logic systems (combat, inventory, perks, etc.)
├── ui/                  # ⚠️ UI components (some files too large)
├── world/               # ✅ World generation, entities, maps
├── data/                # ✅ JSON configuration files
└── docs/                # ✅ Comprehensive documentation
```

### Architecture Patterns

1. **Component-Based Systems**: Clean separation with `systems/` for game logic
2. **Scene Management**: Well-structured scene system in `engine/scenes/`
3. **Manager Pattern**: Specialized managers for hero, floor, messages
4. **Controller Pattern**: Controllers for input and game modes
5. **Data-Driven Design**: JSON files for items, consumables, configurations

---

## Critical Issues

### 1. Large File Sizes

| File | Lines | Target | Priority |
|------|-------|--------|----------|
| `engine/core/game.py` | ~1,823 | <800 | **HIGH** |
| `ui/hud_screens.py` | ~1,555 | <500 | **HIGH** |
| `engine/scenes/battle_scene.py` | ~2,468 | <500 | **MEDIUM** (partially refactored) |

**Impact:**
- Hard to navigate and understand
- Difficult to test in isolation
- Higher risk of merge conflicts
- Increased cognitive load for developers

**Recommendation:** Break into smaller, focused modules (see refactoring plan below)

---

### 2. Code Duplication in UI

**Location:** `ui/hud_screens.py`

**Issues Found:**
- Stats display logic duplicated between hero and companion sections (~50 lines)
- Perk rendering duplicated (~30 lines)
- Character header rendering duplicated (~40 lines)
- Item processing logic could be extracted (~100 lines)

**Total Duplication:** ~120+ lines

**Impact:**
- Changes need to be made in multiple places
- Inconsistencies can arise between duplicates
- Harder to maintain consistent behavior

**Recommendation:** Extract common rendering functions (see Priority refactorings)

---

### 3. Inconsistent Error Handling

**Patterns Found:**
```python
# Pattern 1: Defensive (good)
hero_max_stamina = int(getattr(self.player, "max_stamina", 0) or 0)

# Pattern 2: Direct access (risky)
self.player.max_hp = max_hp

# Pattern 3: Broad exception handling
except Exception:  # Too broad
```

**Impact:**
- Unpredictable behavior when attributes missing
- Hard to debug issues
- Inconsistent failure modes

**Recommendation:** Standardize on defensive patterns with specific exception types

---

### 4. Type Safety Issues

**Issues:**
- `entity: object` in `BattleUnit` (too generic)
- Missing return type hints in some functions
- Some `getattr()` calls could use proper type hints

**Example:**
```python
# Current (in battle_scene.py)
entity: object  # ❌ Too generic

# Should be:
entity: Player | Enemy  # ✅ Specific
```

**Recommendation:** Improve type hints throughout, use Union types where appropriate

---

### 5. Magic Numbers

**Status:** Partially addressed (constants exist in `settings.py`)

**Remaining Issues:**
- Some hardcoded values still in UI code (margins, colors, spacing)
- Some hardcoded battle values scattered in code

**Impact:**
- Hard to adjust values globally
- Inconsistent styling
- No single source of truth

**Recommendation:** Continue extracting magic numbers to constants

---

## Refactoring Recommendations

### Priority 1: Extract UI Components (HIGH IMPACT)

**Target:** `ui/hud_screens.py` (1,555 lines → target: <500 lines)

#### 1.1 Extract Item Processing Logic
```python
# Current: ~100 lines in draw_inventory_fullscreen()
# Extract to:
def _process_inventory_items(
    inv: "Inventory",
    game: "Game",
    filter_mode: FilterMode,
    sort_mode: SortMode,
    search_query: str,
) -> ProcessedInventory:
    """Process, filter, sort, and group inventory items."""
    pass
```

**Benefits:**
- Testable in isolation
- Reusable for other screens
- Reduces main function from ~330 to ~230 lines

#### 1.2 Extract Stats Display
```python
@dataclass
class CharacterStats:
    """Container for character stats data."""
    hp: int
    max_hp: int
    attack: int
    defense: int
    skill_power: float
    # ... etc

def _calculate_character_stats(
    game: "Game",
    is_hero: bool,
    comp: Optional[CompanionState] = None,
) -> CharacterStats:
    """Calculate stats for hero or companion."""
    pass

def _render_stats_section(
    screen: pygame.Surface,
    ui_font: pygame.font.Font,
    stats: CharacterStats,
    x: int,
    y: int,
) -> int:
    """Render stats section. Returns Y position after section."""
    pass
```

**Benefits:**
- Eliminates ~50 lines of duplication
- Single source of truth for stats display
- Easier to add new stats or modify display

#### 1.3 Extract Perk Rendering
```python
def _render_perks_section(
    screen: pygame.Surface,
    ui_font: pygame.font.Font,
    perk_ids: List[str],
    x: int,
    y: int,
    empty_message: str = "None yet. Level up to choose perks!",
) -> int:
    """Render perks list. Returns Y position after section."""
    pass
```

**Benefits:**
- Eliminates ~30 lines of duplication
- Consistent perk display formatting

#### 1.4 Extract Character Header
```python
@dataclass
class CharacterHeaderInfo:
    """Container for character header display data."""
    name: str
    class_name: str
    level: int
    xp: int
    xp_next: Optional[int]
    gold: int
    floor: int

def _get_character_header_info(...) -> CharacterHeaderInfo:
    """Extract header info for hero or companion."""
    pass

def _render_character_header(...) -> int:
    """Render character header."""
    pass
```

**Benefits:**
- Eliminates ~40 lines of duplication
- Consistent header formatting

**Estimated Impact:**
- Reduces `hud_screens.py` from 1,555 to ~800 lines
- Eliminates ~120 lines of duplication
- Improves testability and maintainability

---

### Priority 2: Split Game Class (HIGH IMPACT)

**Target:** `engine/core/game.py` (1,823 lines → target: <800 lines)

**Current Structure:**
- Game state management
- Floor generation and management
- Entity spawning
- Battle orchestration
- UI state management
- Save/load logic

**Proposed Split:**

```
engine/core/game.py (core loop, ~400 lines)
├── GameState (state management, ~200 lines)
├── FloorManager (floor generation, ~300 lines)
├── SpawnManager (entity spawning, ~200 lines)
└── BattleOrchestrator (battle coordination, ~300 lines)
```

**Benefits:**
- Clearer responsibilities
- Easier to test each component
- Better separation of concerns
- Reduces cognitive load

**Implementation Strategy:**
1. Extract `FloorManager` first (low risk)
2. Extract `SpawnManager` (low risk)
3. Extract `BattleOrchestrator` (medium risk)
4. Refactor `Game` to use managers (final step)

---

### Priority 3: Battle Scene Refactoring (MEDIUM PRIORITY)

**Status:** Partially complete (battle/ folder exists with some modules)

**Target:** `engine/scenes/battle_scene.py` (~2,468 lines)

**Current State:**
- `engine/battle/` folder exists with:
  - `ai.py`
  - `combat.py`
  - `pathfinding.py`
  - `renderer.py`
  - `terrain.py`
  - `types.py`

**Remaining Work:**
- Verify all rendering code is in `renderer.py`
- Ensure AI logic is fully extracted
- Check for any remaining large functions in `battle_scene.py`

**Recommendation:** Complete the refactoring according to `docs/REFACTORING_PLAN.md`

---

### Priority 4: Create Reusable UI Components (MEDIUM IMPACT)

**Proposal:** Create `ui/components.py` for reusable UI elements

```python
class StatsDisplay:
    """Reusable stats display component."""
    def __init__(self, stats: CharacterStats):
        self.stats = stats
    
    def render(self, screen, font, x, y) -> int:
        """Render stats. Returns Y position after."""
        pass

class PerksList:
    """Reusable perks list component."""
    def __init__(self, perk_ids: List[str]):
        self.perk_ids = perk_ids
    
    def render(self, screen, font, x, y) -> int:
        """Render perks. Returns Y position after."""
        pass

class ItemCard:
    """Reusable item display card."""
    pass

class ResourceBar:
    """Reusable resource bar (HP, Stamina, Mana)."""
    pass
```

**Benefits:**
- Consistent UI across all screens
- Easier to modify styling globally
- Better encapsulation of UI logic
- Easier to add animations/effects

---

### Priority 5: Standardize Error Handling (LOW-MEDIUM PRIORITY)

**Current Issues:**
- Mixed patterns (defensive vs direct access)
- Broad exception handling
- Inconsistent attribute access

**Proposed Standard:**

```python
# For optional attributes, always use defensive pattern:
def safe_get_attr(obj: object, attr: str, default: Any = None) -> Any:
    """Safely get attribute with default."""
    return getattr(obj, attr, default)

# For guaranteed attributes, use direct access but document:
# Note: player.max_hp is guaranteed to exist after initialization

# For exceptions, use specific types:
try:
    # operation
except (KeyError, ValueError) as e:  # ✅ Specific
    # handle
except AttributeError as e:  # ✅ Specific
    # handle
# Avoid: except Exception:  # ❌ Too broad
```

**Benefits:**
- Predictable behavior
- Easier debugging
- Better error messages

---

## Architecture Improvements

### 1. Dependency Injection

**Current:** Some modules create dependencies directly

**Proposed:** Use dependency injection for better testability

```python
# Current
class Game:
    def __init__(self):
        self.message_log = MessageLog()

# Proposed
class Game:
    def __init__(self, message_log: Optional[MessageLog] = None):
        self.message_log = message_log or MessageLog()
```

**Benefits:**
- Easier testing (can inject mocks)
- Better flexibility
- Clearer dependencies

---

### 2. Event System

**Proposal:** Consider adding an event system for decoupled communication

```python
# Example: Instead of direct calls
game.player.hp -= damage
game.update_ui()

# Use events
event_bus.emit(PlayerDamagedEvent(player, damage))
# UI subscribes and updates automatically
```

**Benefits:**
- Decoupled components
- Easier to add new features (just subscribe to events)
- Better for future expansion (achievements, analytics, etc.)

**Note:** This is a larger architectural change - consider carefully

---

### 3. Resource Pool Management

**Current Issue:** Resource tracking scattered across multiple files

**Proposal:** Centralize resource management

```python
@dataclass
class ResourcePool:
    """Centralized resource pool management."""
    current: int
    maximum: int
    
    def add(self, amount: int) -> int:
        """Add resources, return actual amount added."""
        old = self.current
        self.current = min(self.current + amount, self.maximum)
        return self.current - old
    
    def consume(self, amount: int) -> bool:
        """Consume resources, return True if successful."""
        if self.current >= amount:
            self.current -= amount
            return True
        return False
    
    @property
    def percentage(self) -> float:
        """Get current percentage."""
        return self.current / self.maximum if self.maximum > 0 else 0.0
```

**Benefits:**
- Single source of truth for resource logic
- Consistent behavior across all resources
- Easier to add features (regen, caps, etc.)

---

## Testing Recommendations

### Current State
- No visible test files
- No test infrastructure apparent

### Recommended Test Structure

```
tests/
├── __init__.py
├── conftest.py          # Pytest fixtures
├── unit/
│   ├── test_systems/
│   │   ├── test_combat.py
│   │   ├── test_inventory.py
│   │   └── test_perks.py
│   ├── test_engine/
│   │   └── test_game.py
│   └── test_ui/
│       └── test_components.py
├── integration/
│   ├── test_battle_flow.py
│   └── test_save_load.py
└── fixtures/
    └── test_data/
```

### Priority Tests

1. **Unit Tests for Systems** (HIGH PRIORITY)
   - Combat calculations
   - Inventory operations
   - Perk application
   - Status effects

2. **Integration Tests** (MEDIUM PRIORITY)
   - Battle flow (start → end)
   - Save/load cycle
   - Floor progression

3. **UI Tests** (LOW PRIORITY)
   - Visual regression (if using automated testing tools)
   - Input handling

---

## Implementation Roadmap

### Phase 1: Quick Wins (1-2 weeks)
1. ✅ Extract UI helper functions (stats, perks, headers)
2. ✅ Extract item processing logic
3. ✅ Add missing type hints
4. ✅ Extract remaining magic numbers

### Phase 2: Medium Refactoring (2-3 weeks)
1. Extract `FloorManager` from `Game`
2. Extract `SpawnManager` from `Game`
3. Create reusable UI components
4. Standardize error handling patterns

### Phase 3: Large Refactoring (3-4 weeks)
1. Split `Game` class into focused managers
2. Complete battle scene refactoring
3. Add comprehensive unit tests
4. Implement resource pool system

### Phase 4: Architecture Improvements (Optional, 4+ weeks)
1. Consider event system
2. Add dependency injection where beneficial
3. Performance profiling and optimization
4. Documentation improvements

---

## Metrics & Success Criteria

### Code Quality Metrics
- **File Size:** No file > 800 lines (target: <500 lines)
- **Code Duplication:** < 5% (currently ~10-15%)
- **Test Coverage:** > 70% for core systems (target: > 80%)
- **Type Hint Coverage:** > 90% (currently ~70%)

### Maintainability Metrics
- **Cyclomatic Complexity:** Average < 10 per function
- **Function Length:** Average < 50 lines
- **Import Dependencies:** Minimize circular dependencies

### Performance Metrics
- **Frame Rate:** Maintain 60 FPS target
- **Load Times:** < 2 seconds for floor generation
- **Memory Usage:** Profile and optimize if needed

---

## Risk Assessment

### Low Risk Refactorings
- ✅ Extract UI helper functions
- ✅ Extract constants
- ✅ Add type hints
- ✅ Extract item processing

**Mitigation:** Incremental changes, test after each step

### Medium Risk Refactorings
- ⚠️ Split Game class
- ⚠️ Extract managers
- ⚠️ Create UI components

**Mitigation:** 
- Thorough testing after each extraction
- Keep original code until verified working
- Use feature flags if needed

### High Risk Refactorings
- 🔴 Event system implementation
- 🔴 Large-scale architecture changes

**Mitigation:**
- Proof of concept first
- Incremental rollout
- Extensive testing
- Clear rollback plan

---

## Recommendations Summary

### Must Do (Before Major Expansion)
1. ✅ Extract UI duplication (Priority 1)
2. ✅ Split large files (Priority 1-2)
3. ✅ Add basic unit tests for core systems
4. ✅ Standardize error handling

### Should Do (For Better Maintainability)
1. Create reusable UI components
2. Complete battle scene refactoring
3. Improve type hints coverage
4. Extract resource pool management

### Nice to Have (Future Improvements)
1. Event system for decoupling
2. Dependency injection framework
3. Performance profiling tools
4. Comprehensive documentation

---

## Conclusion

The codebase is **well-structured** with good separation of concerns. The main issues are:

1. **File Size**: Some files are too large and should be split
2. **Code Duplication**: UI code has significant duplication
3. **Technical Debt**: Some inconsistent patterns and legacy code

**Priority Actions:**
1. Extract UI helper functions (quick win, high impact)
2. Split `Game` class into managers (high impact, medium effort)
3. Add basic testing infrastructure (foundation for future work)

With these refactorings, the codebase will be:
- ✅ Easier to maintain
- ✅ More testable
- ✅ Better prepared for expansion
- ✅ More consistent

---

## Related Documents

- `docs/REFACTORING_SUGGESTIONS.md` - Detailed UI refactoring suggestions
- `docs/ARCHITECTURE_ANALYSIS.md` - Original architecture analysis
- `docs/CODE_REVIEW_FINDINGS.md` - Code review findings
- `docs/REFACTORING_PLAN.md` - Battle system refactoring plan

---

**Next Steps:** Review this document and prioritize which refactorings to tackle first.

