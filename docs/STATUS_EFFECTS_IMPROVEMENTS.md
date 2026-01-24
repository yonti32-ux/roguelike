# Status Effects Improvements

## Summary

Enhanced the status effects display system with better visuals, timers, stack counts, and support for all status types.

## Changes Made

### 1. New Enhanced Status Display Module (`ui/status_display.py`)

Created a new module specifically for rendering status effects with:

- **Better Visual Representation**: 
  - ASCII-safe symbols for each status type (e.g., `[` for guard, `v` for weakened)
  - Color-coded by status type (buffs in blue/green, debuffs in red/orange)
  
- **Duration Timers**: 
  - Shows remaining turns for each status
  - Positioned next to status icon for easy reading
  
- **Stack Counts**: 
  - Displays stack count (e.g., `×3`) for stackable statuses like disease
  - Positioned in top-right corner of status icon
  
- **Status Sorting**: 
  - Buffs displayed first, then debuffs
  - Better visual organization

- **Unlimited Status Display**: 
  - No longer limited to 4 statuses
  - All active statuses are shown

### 2. Status Type Definitions

Added definitions for all status types with:
- Unique icons/symbols
- Color coding (buffs vs debuffs)
- Descriptions (for future tooltips)

**Status Types Supported:**
- **Buffs**: `guard`, `regenerating`, `counter_stance`
- **Debuffs**: `weakened`, `stunned`
- **DoT Effects**: `poisoned`, `bleeding`, `burning`, `diseased`
- **Utility**: `chilled`

### 3. Integration

Updated rendering code in:
- `engine/battle/renderer.py` - Battle scene unit display
- `ui/hud_battle.py` - Unit cards in battle UI

### 4. Tooltip Support (Prepared)

Added `get_status_tooltip()` function that generates detailed tooltips:
- Status name
- Description
- Duration
- Stack count
- Damage per turn (for DoT)
- Multiplier effects

(Ready for future tooltip system implementation)

## Visual Improvements

### Before:
- Single letters: `G`, `W`, `!`, `•`
- Limited to 4 statuses
- No timers
- No stack counts
- Generic DOT icon for all damage-over-time effects

### After:
- Descriptive symbols: `[` (guard), `v` (weakened), `P` (poison), etc.
- All statuses displayed
- Duration timers visible
- Stack counts shown (`×3`, `×5`, etc.)
- Different icons for each DoT type (P, B, *, D)

## Example Display

```
[v 2]  - Weakened (2 turns remaining)
[P 3]  - Poisoned (3 turns)
[! 1]  - Stunned (1 turn)
[D×5 2] - Diseased (5 stacks, 2 turns remaining)
[[ 1]  - Guard (1 turn remaining)
[+ 4]  - Regenerating (4 turns)
```

## Files Modified

1. **`ui/status_display.py`** (NEW)
   - Enhanced status display functions
   - Status definitions
   - Tooltip generation

2. **`engine/battle/renderer.py`**
   - Updated to use `draw_enhanced_status_indicators()`
   - Shows all statuses with timers/stacks

3. **`ui/hud_battle.py`**
   - Updated unit cards to use enhanced display

## Future Enhancements (Not Yet Implemented)

1. **Tooltips**: 
   - Hover over status icon to see detailed info
   - Use `get_status_tooltip()` function

2. **Visual Icons**: 
   - Replace ASCII symbols with small icon images
   - More recognizable status representations

3. **Animated Status Indicators**: 
   - Pulse for expiring statuses
   - Glow for important buffs/debuffs

4. **Status Panel**: 
   - Dedicated panel showing all statuses on active unit
   - Expandable list view

5. **Status History**: 
   - Show when statuses were applied
   - Track status duration over time

## Testing

To test the improvements:

1. **Guard Status**: Use Guard skill - should show `[` icon with timer
2. **Weaken**: Use Power Strike - should show `v` icon with timer
3. **Stacking DoT**: Get diseased multiple times - should show `×N` stack count
4. **Multiple Statuses**: Have several statuses active - all should display with timers
5. **Duration Countdown**: Watch timers decrease each turn

## Configuration

Status definitions can be easily modified in `ui/status_display.py`:

```python
STATUS_DEFINITIONS = {
    "status_name": {
        "icon": "symbol",
        "color": (R, G, B),
        "is_buff": True/False,
        "description": "Status description",
    }
}
```

## Notes

- All symbols are ASCII-safe for maximum compatibility
- Timer display can be toggled with `show_timers` parameter
- Stack count display can be toggled with `show_stacks` parameter
- Maximum statuses can be limited with `max_statuses` parameter (None = all)

