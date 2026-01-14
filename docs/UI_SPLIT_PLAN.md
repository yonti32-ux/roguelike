# UI Split Plan - Option 3

## Overview
Split `ui/hud_screens.py` (~1760 lines) into focused screen-specific modules.

## Modules to Create

### 1. `ui/screens/inventory_screen.py`
**Functions:**
- `draw_inventory_fullscreen()`
- `_process_inventory_items()` 
- `_render_inventory_item_list()`
- `_resolve_focus_character()`
- `_get_character_display_info()`
- `_build_stats_line()`
- `_get_all_equipped_items()`
- `ProcessedInventory` dataclass

### 2. `ui/screens/character_screen.py`
**Functions:**
- `draw_character_sheet_fullscreen()`
- `_calculate_character_stats()`
- `_get_character_header_info()`

### 3. `ui/screens/shop_screen.py`
**Functions:**
- `draw_shop_fullscreen()`
- `_sort_items_by_type()`
- `_get_category_name()`

### 4. `ui/screens/skill_screen.py`
**Functions:**
- `draw_skill_screen_fullscreen()`

### 5. `ui/screens/recruitment_screen.py`
**Functions:**
- `draw_recruitment_fullscreen()`

### 6. `ui/screens/quest_screen.py`
**Functions:**
- `draw_quest_fullscreen()`

## Shared Utilities
- `_safe_getattr()` - Used by all screens, keep in shared location or each module

## Files That Import From hud_screens
- `ui/screens.py` - imports all 6 draw functions + `_process_inventory_items`
- `ui/village/quest_screen.py` - imports `draw_quest_fullscreen`
- `ui/village/recruitment_screen.py` - imports `draw_recruitment_fullscreen`

## Strategy
1. Create `ui/screens/` directory
2. Create each module one at a time
3. Update imports incrementally
4. Keep `hud_screens.py` as compatibility layer initially (re-export from modules)
5. Eventually remove `hud_screens.py` once all imports are updated

