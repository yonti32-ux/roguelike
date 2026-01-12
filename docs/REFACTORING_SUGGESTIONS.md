# Refactoring Suggestions for hud_screens.py

## Overview
This document outlines specific refactoring opportunities to improve code organization, reduce duplication, and enhance maintainability.

## Priority 1: Extract Item List Processing (High Impact)

### Current Issue
`draw_inventory_fullscreen()` has ~100 lines of item processing logic (lines 549-650) that could be extracted.

### Suggested Refactoring
```python
def _process_inventory_items(
    inv: "Inventory",
    game: "Game",
    filter_mode: FilterMode,
    sort_mode: SortMode,
    search_query: str,
) -> Tuple[List[Tuple[Optional[str], str]], List[int], Dict[int, int]]:
    """
    Process inventory items: filter, sort, group, and build display structure.
    
    Returns:
        - flat_list: List of (item_id or None, slot) tuples
        - item_indices: List of flat_list indices that are actual items
        - flat_to_global: Map from flat_idx to global item index
    """
    # Move all the processing logic here
    pass
```

**Benefits:**
- Reduces `draw_inventory_fullscreen()` from ~330 lines to ~230 lines
- Makes item processing logic testable in isolation
- Clearer separation of concerns

---

## Priority 2: Extract Item Rendering Loop (High Impact)

### Current Issue
The item rendering loop (lines 643-750) is ~110 lines of complex nested logic.

### Suggested Refactoring
```python
def _render_inventory_item_list(
    screen: pygame.Surface,
    ui_font: pygame.font.Font,
    flat_list: List[Tuple[Optional[str], str]],
    item_indices: List[int],
    flat_to_global: Dict[int, int],
    visible_start: int,
    visible_end: int,
    cursor: int,
    all_equipped: Dict[str, List[Tuple[str, str]]],
    right_x: int,
    y: int,
    w: int,
    h: int,
) -> Tuple[int, Dict[str, Tuple[int, int, int, int]]]:
    """
    Render the inventory item list with scrolling and selection.
    
    Returns:
        - Final y position
        - Dictionary of item_id -> (x, y, width, height) for hover detection
    """
    pass
```

**Benefits:**
- Separates rendering logic from data processing
- Easier to test and modify rendering behavior
- Reduces cognitive load in main function

---

## Priority 3: Extract Stats Display Logic (High Impact - Eliminates Duplication)

### Current Issue
Stats calculation and display is duplicated between hero and companion sections in `draw_character_sheet_fullscreen()`.

**Hero section (lines 879-915):**
- Resource pool calculation
- Stats lines building
- Rendering loop

**Companion section (lines 1096-1123):**
- Nearly identical logic

### Suggested Refactoring
```python
@dataclass
class CharacterStats:
    """Container for character stats data."""
    hp: int
    max_hp: int
    attack: int
    defense: int
    skill_power: float
    max_stamina: int = 0
    current_stamina: int = 0
    max_mana: int = 0
    current_mana: int = 0

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
    """
    Render stats section.
    
    Returns:
        Y position after stats section
    """
    pass
```

**Benefits:**
- Eliminates ~50 lines of duplication
- Single source of truth for stats display
- Easier to add new stats or modify display format

---

## Priority 4: Extract Perk Rendering (Medium Impact - Eliminates Duplication)

### Current Issue
Perk rendering code is duplicated in hero section (lines 924-952) and companion section (lines 1139-1167).

### Suggested Refactoring
```python
def _render_perks_section(
    screen: pygame.Surface,
    ui_font: pygame.font.Font,
    perk_ids: List[str],
    x: int,
    y: int,
    empty_message: str = "None yet. Level up to choose perks!",
) -> int:
    """
    Render perks list.
    
    Returns:
        Y position after perks section
    """
    pass
```

**Benefits:**
- Eliminates ~30 lines of duplication
- Consistent perk display formatting
- Easier to modify perk display logic

---

## Priority 5: Extract Character Header Info (Medium Impact)

### Current Issue
Character header (name, level, XP, gold, floor) is duplicated between hero and companion.

### Suggested Refactoring
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

def _get_character_header_info(
    game: "Game",
    is_hero: bool,
    comp: Optional[CompanionState] = None,
    template: Optional[CompanionDef] = None,
) -> CharacterHeaderInfo:
    """Extract header info for hero or companion."""
    pass

def _render_character_header(
    screen: pygame.Surface,
    ui_font: pygame.font.Font,
    header_info: CharacterHeaderInfo,
    x: int,
    y: int,
) -> int:
    """
    Render character header (name, level, XP, gold, floor).
    
    Returns:
        Y position after header
    """
    pass
```

**Benefits:**
- Eliminates ~40 lines of duplication
- Consistent header formatting
- Easier to add new header fields

---

## Priority 6: Extract Party Preview Rendering (Low-Medium Impact)

### Current Issue
Party preview section (lines 954-1040) is ~90 lines that could be extracted.

### Suggested Refactoring
```python
def _render_party_preview(
    screen: pygame.Surface,
    ui_font: pygame.font.Font,
    game: "Game",
    party_list: List[CompanionState],
    focus_index: int,
    hero_name: str,
    hero_class: str,
    x: int,
    y: int,
) -> int:
    """
    Render party preview sidebar.
    
    Returns:
        Y position after party preview
    """
    pass
```

**Benefits:**
- Reduces complexity of main function
- Could be reused in other screens
- Easier to modify party display

---

## Priority 7: Extract Tooltip Handling (Low Impact)

### Current Issue
Tooltip handling code appears in multiple places with slight variations.

### Suggested Refactoring
```python
def _handle_inventory_tooltips(
    game: "Game",
    screen: pygame.Surface,
    ui_font: pygame.font.Font,
    item_positions: Dict[str, Tuple[int, int, int, int]],
    focused_is_hero: bool,
    focused_comp: Optional[CompanionState],
) -> None:
    """Handle tooltip display for inventory items."""
    pass
```

**Benefits:**
- Centralizes tooltip logic
- Consistent tooltip behavior
- Easier to add tooltip features

---

## Implementation Strategy

### Phase 1: Low-Risk Extractions (Start Here)
1. Extract `_render_perks_section()` - Simple, isolated, no dependencies
2. Extract `_render_character_header()` - Straightforward data display
3. Extract `_handle_inventory_tooltips()` - Already somewhat isolated

### Phase 2: Medium-Risk Extractions
4. Extract `_calculate_character_stats()` and `_render_stats_section()`
5. Extract `_render_party_preview()`

### Phase 3: High-Risk Extractions (Requires Careful Testing)
6. Extract `_process_inventory_items()` - Complex logic, many dependencies
7. Extract `_render_inventory_item_list()` - Complex rendering loop

## Expected Results

### Before Refactoring:
- `draw_inventory_fullscreen()`: ~330 lines
- `draw_character_sheet_fullscreen()`: ~370 lines
- Total duplication: ~120 lines

### After Refactoring:
- `draw_inventory_fullscreen()`: ~150 lines (calls helper functions)
- `draw_character_sheet_fullscreen()`: ~150 lines (calls helper functions)
- New helper functions: ~8 functions, ~400 lines total
- Total duplication: ~0 lines
- **Net improvement**: Better organization, testability, and maintainability

## Testing Strategy

1. **Visual Regression**: Ensure UI looks identical after each extraction
2. **Functional Testing**: Test all interactions (hover, selection, scrolling)
3. **Edge Cases**: Empty inventory, no perks, missing data
4. **Performance**: Verify no performance regression

## Additional Suggestions

### 1. Create a UI Component System
Consider creating reusable UI components:
```python
class StatsDisplay:
    def __init__(self, stats: CharacterStats):
        self.stats = stats
    
    def render(self, screen, font, x, y) -> int:
        # Render stats
        pass

class PerksList:
    def __init__(self, perk_ids: List[str]):
        self.perk_ids = perk_ids
    
    def render(self, screen, font, x, y) -> int:
        # Render perks
        pass
```

### 2. Use Dataclasses for Data Transfer
Replace tuple returns with dataclasses for better type safety and clarity.

### 3. Consider a Layout Manager
Extract positioning logic into a layout manager to handle margins, spacing, and column layouts consistently.

## Notes

- All refactorings maintain backward compatibility
- No functional changes - only code organization
- Each extraction should be done incrementally with testing
- Consider using type hints more extensively for better IDE support



