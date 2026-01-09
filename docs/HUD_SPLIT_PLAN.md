# HUD File Split Plan

## Current Structure (1665 lines)

The `ui/hud.py` file contains 4 main sections:

1. **Utility Functions** (lines 19-180, ~162 lines)
   - `_draw_bar` - Basic bar drawing
   - `_draw_resource_bar_with_label` - Bar with label
   - `_draw_status_indicators` - Status icons (G, W, !, •)
   - `_draw_compact_unit_card` - Compact party preview cards

2. **Battle HUD** (lines 182-420, ~239 lines)
   - `_draw_battle_unit_card` - Battle unit display
   - `_draw_battle_skill_hotbar` - Skill hotbar
   - `_draw_battle_log_line` - Battle log rendering
   - **Used by:** `engine/battle_scene.py`

3. **Exploration HUD** (lines 421-830, ~410 lines)
   - `_draw_hero_panel` - Hero info panel
   - `_gather_context_hints` - Context hint gathering
   - `draw_exploration_ui` - Main exploration UI
   - **Used by:** `engine/game.py`

4. **Fullscreen Screens** (lines 830-1665, ~835 lines)
   - `_resolve_focus_character` - Focus resolution helper
   - `_build_stats_line` - Stats string builder
   - `_get_character_display_info` - Character info helper
   - `_draw_equipment_section` - Equipment display
   - `_draw_screen_header` - Screen header/tabs
   - `_draw_screen_footer` - Screen footer/hints
   - `draw_inventory_fullscreen` - Inventory screen
   - `draw_character_sheet_fullscreen` - Character sheet screen
   - `draw_shop_fullscreen` - Shop screen
   - **Used by:** `ui/screens.py`

## Proposed Split

### File 1: `ui/hud_utils.py` (~180 lines)
**Purpose:** Shared utility functions used by all HUD components

**Functions:**
- `_draw_bar`
- `_draw_resource_bar_with_label`
- `_draw_status_indicators`
- `_draw_compact_unit_card`

**Dependencies:**
- `pygame`
- `settings.TILE_SIZE` (only for status indicators if needed)

**Used by:**
- All other HUD modules

---

### File 2: `ui/hud_battle.py` (~250 lines)
**Purpose:** Battle-specific HUD components

**Functions:**
- `_draw_battle_unit_card`
- `_draw_battle_skill_hotbar`
- `_draw_battle_log_line`

**Dependencies:**
- `ui.hud_utils` (imports utility functions)
- `pygame`
- `systems.input.InputAction`
- `settings.TILE_SIZE` (if needed)

**Used by:**
- `engine/battle_scene.py`

**Imports needed:**
```python
from ui.hud_utils import _draw_bar, _draw_status_indicators
```

---

### File 3: `ui/hud_exploration.py` (~420 lines)
**Purpose:** Exploration mode HUD

**Functions:**
- `_draw_hero_panel`
- `_gather_context_hints`
- `draw_exploration_ui`

**Dependencies:**
- `ui.hud_utils` (imports utility functions)
- `pygame`
- `settings.TILE_SIZE`
- `systems.events.get_event_def`
- `systems.party.*`
- `world.entities.Enemy`

**Used by:**
- `engine/game.py`

**Imports needed:**
```python
from ui.hud_utils import _draw_bar, _draw_resource_bar_with_label, _draw_compact_unit_card
```

---

### File 4: `ui/hud_screens.py` (~850 lines)
**Purpose:** Fullscreen screen drawing functions

**Functions:**
- `_resolve_focus_character`
- `_build_stats_line`
- `_get_character_display_info`
- `_draw_equipment_section`
- `_draw_screen_header`
- `_draw_screen_footer`
- `draw_inventory_fullscreen`
- `draw_character_sheet_fullscreen`
- `draw_shop_fullscreen`

**Dependencies:**
- `ui.hud_utils` (imports utility functions)
- `pygame`
- `settings.COLOR_BG`
- `systems.inventory.get_item_def`
- `systems.perks`
- `systems.party.*`

**Used by:**
- `ui/screens.py`

**Imports needed:**
```python
from ui.hud_utils import _draw_bar, _draw_equipment_section  # if needed
```

---

## Import Updates Required

### `engine/game.py`
**Current:**
```python
from ui.hud import draw_exploration_ui
```

**New:**
```python
from ui.hud_exploration import draw_exploration_ui
```

### `engine/battle_scene.py`
**Current:**
```python
from ui.hud import (
    _draw_battle_unit_card,
    _draw_battle_skill_hotbar,
    _draw_battle_log_line,
)
```

**New:**
```python
from ui.hud_battle import (
    _draw_battle_unit_card,
    _draw_battle_skill_hotbar,
    _draw_battle_log_line,
)
```

### `ui/screens.py`
**Current:**
```python
from ui.hud import (
    draw_inventory_fullscreen,
    draw_character_sheet_fullscreen,
    draw_shop_fullscreen,
)
```

**New:**
```python
from ui.hud_screens import (
    draw_inventory_fullscreen,
    draw_character_sheet_fullscreen,
    draw_shop_fullscreen,
)
```

---

## Benefits

1. **Clear separation of concerns** - Each file has a single, clear purpose
2. **Better maintainability** - Easier to find and modify specific functionality
3. **Reduced file size** - Largest file goes from 1665 → ~850 lines
4. **Easier testing** - Can test each module independently
5. **Better organization** - Related functions grouped together

## Risks & Considerations

1. **Circular imports** - Need to ensure utils doesn't import from other modules
2. **Shared dependencies** - Some functions might need access to utils
3. **Import updates** - Need to update all import statements
4. **Testing** - Should verify all functionality still works after split

## Implementation Order

1. Create `ui/hud_utils.py` with utility functions
2. Create `ui/hud_battle.py` with battle functions
3. Create `ui/hud_exploration.py` with exploration functions
4. Create `ui/hud_screens.py` with screen functions
5. Update all imports in dependent files
6. Delete old `ui/hud.py`
7. Test thoroughly

## File Size Estimates

- `hud_utils.py`: ~180 lines
- `hud_battle.py`: ~250 lines
- `hud_exploration.py`: ~420 lines
- `hud_screens.py`: ~850 lines
- **Total:** ~1700 lines (slight increase due to imports/headers, but better organized)

