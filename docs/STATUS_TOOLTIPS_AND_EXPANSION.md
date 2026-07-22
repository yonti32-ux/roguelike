# Status Effects - Tooltips & Expansion Summary

## Changes Made

### 1. Tooltip Support ✅

Added `create_status_tooltip_data()` function in `ui/status_display.py` that creates TooltipData objects compatible with the game's tooltip system.

**Features**:
- Status name as title
- Description text
- Duration information
- Stack count display
- Damage per turn (for DoT effects)
- Multiplier stats (damage output/reduction percentages)

**Usage**:
```python
from ui.status_display import create_status_tooltip_data

# In battle scene or UI, when hovering over status icon:
tooltip_data = create_status_tooltip_data(status_effect)
game.tooltip.current_tooltip = tooltip_data
```

**Integration Note**: 
Full tooltip integration requires detecting mouse hover over status icons in the battle renderer. This involves:
- Tracking status icon positions during rendering
- Checking mouse position against icon rectangles
- Updating tooltip when hovering over status icons

This is prepared but requires battle scene mouse handling integration.

---

### 2. Expanded Status Types ✅

Added new status type definitions to `STATUS_DEFINITIONS`:

**Already Existed** (now documented):
- `guard`, `regenerating`, `counter_stance` (buffs)
- `weakened`, `stunned` (debuffs)
- `poisoned`, `bleeding`, `burning`, `diseased` (DoT)
- `chilled` (utility)

**Newly Added**:
- `empowered` - 30% increased damage output (already referenced in skills, now has display definition)
- `haste` - Increased movement (for future use)
- `slow` - Reduced movement speed (for future use)
- `vulnerable` - Takes increased damage (for future use)
- `protected` - Reduced incoming damage (for future use)
- `exposed` - Cannot guard or defend (for future use)
- `warded` - Immune to debuffs (for future use)

All new statuses have:
- ASCII-safe icon symbols
- Color coding (buffs = blue/green, debuffs = red/orange)
- Description text

---

### 3. Visual Effects Ideas 📝

Created `docs/STATUS_VISUAL_EFFECTS_IDEAS.md` with comprehensive ideas for enhancing status visual feedback:

**Key Ideas**:
1. **Pulsing/Flashing**: For expiring/important statuses
2. **Glow Effects**: Colored halos around status icons
3. **Animated Icons**: Frame-based icon animations
4. **Status Bar Integration**: Visual indicators on units
5. **Expiration Warnings**: Visual cues when status is about to expire
6. **Stack Visualization**: Enhanced visual for stacking statuses
7. **Application Feedback**: Brief effects when status is applied

**Recommended Priority**:
- Phase 1: Expiration warning + subtle glow (easy, high impact)
- Phase 2: Pulsing animation + stack visualization
- Phase 3: Advanced effects (particles, animated icons)

---

## Files Modified

1. **`ui/status_display.py`**:
   - Added `empowered` status definition
   - Added 6 new status type definitions (haste, slow, vulnerable, protected, exposed, warded)
   - Added `create_status_tooltip_data()` function

2. **`docs/STATUS_VISUAL_EFFECTS_IDEAS.md`** (NEW):
   - Comprehensive visual effects ideas
   - Implementation approaches
   - Code examples
   - Priority recommendations

3. **`docs/STATUS_TOOLTIPS_AND_EXPANSION.md`** (THIS FILE):
   - Summary of changes
   - Usage documentation

---

## Future Integration Steps

### For Tooltips:

1. **Track Status Icon Positions** (in `draw_enhanced_status_indicators`):
   ```python
   # Store icon positions during rendering
   status_icon_positions[status] = (x, y, width, height)
   ```

2. **Check Mouse Hover** (in battle scene update/draw):
   ```python
   # Check if mouse is over any status icon
   mouse_pos = pygame.mouse.get_pos()
   for status, rect in status_icon_positions.items():
       if rect.collidepoint(mouse_pos):
           tooltip_data = create_status_tooltip_data(status)
           game.tooltip.current_tooltip = tooltip_data
           break
   ```

3. **Draw Tooltip** (already handled by game.tooltip.draw())

### For Visual Effects:

See `docs/STATUS_VISUAL_EFFECTS_IDEAS.md` for detailed implementation approaches.

Recommended starting point:
- Add expiration warning (flash when duration ≤ 1)
- Add subtle glow for all statuses

---

## Testing

To test the improvements:

1. **New Status Types**: 
   - Status definitions are ready for use in skills
   - Display will work automatically when statuses are applied

2. **Tooltip Function**:
   ```python
   from ui.status_display import create_status_tooltip_data
   from systems.statuses import StatusEffect
   
   # Test tooltip creation
   status = StatusEffect(name="guard", duration=1, incoming_mult=0.5)
   tooltip = create_status_tooltip_data(status)
   print(tooltip.title, tooltip.lines)
   ```

3. **Status Display**: 
   - All statuses should display correctly with new icons
   - Timers and stacks should show

---

## Notes

- All new status symbols are ASCII-safe for maximum compatibility
- Tooltip integration is prepared but requires battle scene mouse handling
- Visual effects are documented but not yet implemented
- New status types are defined but not yet used in skills (ready for future expansion)

