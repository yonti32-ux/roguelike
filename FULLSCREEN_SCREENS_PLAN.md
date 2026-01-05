# Full-Screen Screens Refactor Plan

## Current State

### Existing Screens
1. **PerkSelectionScene** - ✅ Already full-screen blocking (good reference)
2. **InventoryScreen** - ❌ Overlay (520x420 box)
3. **CharacterSheetScreen** - ❌ Overlay (560x440 box)
4. **ShopScreen** - ❌ Overlay (520x420 box)

### Current Architecture
- Screens are managed via `Game.active_screen`
- Each screen has `handle_event()` and `draw()` methods
- Drawing functions in `ui/hud.py` create semi-transparent overlays
- Screens can be toggled on/off but not switched between

## Goals

1. **Full-Screen Experience**
   - All screens fill the entire window (like PerkSelectionScene)
   - No semi-transparent overlays - full opaque backgrounds
   - Better use of screen real estate

2. **Interchangeable Screens**
   - Switch between screens without closing (e.g., TAB or arrow keys)
   - Visual indicator of current screen
   - Quick navigation between Inventory/Character/Shop

3. **Improved UX**
   - Consistent visual style across all screens
   - Better layout with more space
   - Clear navigation hints

## Implementation Plan

### Phase 1: Create Full-Screen Drawing Functions

**New functions in `ui/hud.py`:**
- `draw_inventory_fullscreen(game)` - Full-screen inventory view
- `draw_character_sheet_fullscreen(game)` - Full-screen character sheet
- `draw_shop_fullscreen(game)` - Full-screen shop view

**Changes:**
- Fill entire screen with `COLOR_BG` background
- Use full window dimensions for layout
- Better spacing and organization
- Add screen title/header at top
- Footer with navigation hints

### Phase 2: Update Screen Classes

**Modify `ui/screens.py`:**

1. **Add screen switching logic:**
   - TAB key cycles: Inventory → Character → Shop → Inventory
   - Or use Left/Right arrows to switch
   - Visual tabs/indicators at top showing current screen

2. **Update each screen class:**
   - `InventoryScreen.draw()` - Use new fullscreen function
   - `CharacterSheetScreen.draw()` - Use new fullscreen function
   - `ShopScreen.draw()` - Use new fullscreen function

3. **Add navigation handling:**
   - Detect TAB/arrow keys in each screen's `handle_event()`
   - Switch to next/previous screen via Game helper method
   - **Shop only available when vendor is nearby** (check `game.show_shop` flag)

### Phase 3: Game Integration

**Modify `engine/game.py`:**

1. **Add screen management:**
   ```python
   def switch_to_screen(self, screen_name: str) -> None:
       """Switch to a different full-screen UI."""
       # Close current screen flags
       # Set new screen flag
       # Set active_screen
   ```

2. **Update toggle methods:**
   - `toggle_inventory_overlay()` → Opens inventory in fullscreen mode
   - `toggle_character_sheet_overlay()` → Opens character sheet in fullscreen mode
   - Shop opening → Opens shop in fullscreen mode

3. **Screen order:**
   - Define order: [Inventory, Character, Shop (if available)]
   - Implement cycling logic that skips Shop when `game.show_shop` is False
   - Shop only appears in cycle when merchant is active

### Phase 4: Visual Enhancements

1. **Screen Header:**
   - Title bar showing current screen name
   - Tab indicators showing available screens
   - Highlight current tab

2. **Navigation Hints:**
   - Footer showing: "TAB: Switch Screen | I/C/S: Jump to Screen | ESC: Close"
   - Consistent across all screens

3. **Layout Improvements:**
   - Better use of horizontal space (side-by-side columns where appropriate)
   - Larger fonts for better readability
   - More spacing between elements

## Screen-Specific Improvements

### Inventory Screen
- **Current:** 520x420 overlay, cramped
- **New:** Full screen with:
  - Left column: Character info + equipment slots
  - Right column: Item list (more items visible)
  - Better scrolling with page indicators
  - Equipment preview on selected character

### Character Sheet Screen
- **Current:** 560x440 overlay
- **New:** Full screen with:
  - Left column: Character stats, level, XP
  - Middle column: Perks list (more visible)
  - Right column: Party preview
  - Better stat visualization

### Shop Screen
- **Current:** 520x420 overlay
- **New:** Full screen with:
  - Left column: Buy list (more items visible)
  - Right column: Sell list (or toggle view)
  - Center: Current gold, transaction history
  - Better item details display

## Key Bindings

### Navigation
- **TAB** - Cycle to next screen (Inventory → Character → Shop (if vendor nearby) → Inventory)
- **SHIFT+TAB** - Cycle to previous screen
- **I** - Jump directly to Inventory
- **C** - Jump directly to Character Sheet
- **S** - Jump directly to Shop (only when vendor is nearby)
- **ESC** - Close all screens, return to exploration

**Note:** Shop screen only appears in cycle when `game.show_shop` is True (vendor nearby)

### Screen-Specific
- Keep existing bindings (Q/E for cycling characters, number keys, etc.)
- Add screen switching on top of existing functionality

## Implementation Order

1. ✅ Create plan (this document)
2. Create fullscreen drawing functions in `ui/hud.py`
3. Update screen classes to use fullscreen drawing
4. Add screen switching logic
5. Update Game class integration
6. Test and refine
7. Update navigation hints and visual polish

## Files to Modify

1. `ui/hud.py` - Add fullscreen drawing functions
2. `ui/screens.py` - Update screen classes with switching logic
3. `engine/game.py` - Add screen management helpers
4. `systems/input.py` - May need new input actions for screen switching

## Considerations

- **Backward Compatibility:** Keep toggle methods working, just change visual presentation
- **Performance:** Full-screen redraws should be fine (already doing this)
- **Consistency:** Match PerkSelectionScene style for consistency
- **Accessibility:** Clear visual feedback for current screen
- **Mobile/Tablet:** Full-screen works better for touch interfaces (future consideration)

