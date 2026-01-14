# UI Refactoring Plan

## Current State
- `ui/hud_screens.py`: 2032 lines - Contains all fullscreen UI screens
- Some refactoring already done (helper functions exist)
- Still has room for improvement in organization

## Goals
1. Extract common UI components into reusable module
2. Make it easier to add new UI features
3. Improve code organization and maintainability
4. Reduce duplication

## Strategy

### Phase 1: Extract Common Components (Current)
- Create `ui/screen_components.py` for reusable screen components
- Move common rendering functions:
  - `_draw_screen_header`
  - `_draw_screen_footer`
  - `_render_stats_section`
  - `_render_perks_section`
  - `_render_character_header`
  - `_draw_equipment_section`
  - `_render_category_header`
- Move UI constants to shared location
- Update imports in `hud_screens.py`

### Phase 2: Organize Data Structures (Future)
- Move dataclasses to appropriate modules
- Consider if they belong in `screen_components.py` or separate file

### Phase 3: Split Large Functions (Future - if needed)
- If individual screen functions get too large, split them
- But current structure with helper functions is acceptable

## Notes
- Keep backward compatibility - all public functions should still work
- Update imports incrementally
- Test after each change

