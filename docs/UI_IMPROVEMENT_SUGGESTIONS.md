# UI Improvement Suggestions

This document outlines UI/UX improvements for the roguelike game, including what's already implemented and suggestions for enhancement.

## Current UI Features (What You Already Have)

### ✅ Implemented Features

#### 1. **Enhanced Status Display System** (`ui/status_display.py`)
- ✅ Status icons with ASCII-safe symbols
- ✅ Color-coded buffs/debuffs (blue/green for buffs, red/orange for debuffs)
- ✅ Duration timers displayed next to icons
- ✅ Stack counts shown for stackable statuses (e.g., `×3`)
- ✅ Status sorting (buffs first, then debuffs)
- ✅ Support for unlimited statuses (no 4-icon limit)
- ✅ Tooltip generation functions (ready for hover integration)

**Status Types Supported:**
- Buffs: guard `[`, regenerating `+`, counter_stance `<`, empowered `^`
- Debuffs: weakened `v`, stunned `!`
- DoT Effects: poisoned `P`, bleeding `B`, burning `*`, diseased `D`
- Utility: chilled `~`, haste `>>`, slow `<<`, vulnerable `V`, etc.

#### 2. **Floating Damage Numbers** (`engine/battle/renderer.py`)
- ✅ Damage numbers float above units
- ✅ Color-coded by damage type (crits = yellow, kills = orange, normal = red)
- ✅ Fade-out animation over time
- ✅ Larger font for better visibility
- ✅ Different colors for different damage amounts

#### 3. **Tooltip System** (`ui/tooltip.py`)
- ✅ Tooltip display with delay (0.3s hover before showing)
- ✅ Smart positioning (adjusts if off-screen)
- ✅ Item tooltips with stat comparisons
- ✅ Status tooltip generation (functions exist)
- ✅ Comparison stats showing stat changes on equipment

#### 4. **Battle UI** (`ui/hud_battle.py`)
- ✅ Enhanced unit cards with portraits, HP, resources, statuses
- ✅ Skill hotbar with key bindings, cooldowns, resource costs
- ✅ Color-coded skill availability (green = ready, gray = unavailable)
- ✅ Combat log with color-coded messages
- ✅ Active unit highlighting

#### 5. **Exploration UI** (`ui/hud_exploration.py`)
- ✅ Hero panel with stats, HP, XP, resources
- ✅ Floor/level display
- ✅ Gold display
- ✅ Gear stat bonuses shown

#### 6. **UI Scaling** (`ui/ui_scaling.py`)
- ✅ Responsive UI that scales with screen size
- ✅ Logarithmic scaling for high resolutions (prevents UI from becoming too large)
- ✅ Base resolution: 1280x720

#### 7. **Screen System** (`ui/screens.py`)
- ✅ Modal screens (inventory, character sheet, shop, skills)
- ✅ Tab navigation between screens
- ✅ Keyboard shortcuts (C for character, I for inventory, etc.)

---

## UI Improvement Suggestions

### 🎯 High Priority - Visual Feedback & Clarity

#### 1. **Status Tooltip Integration** ⚠️ Missing
**Current State:** Status tooltip functions exist but aren't hooked up to mouse hover

**Suggested Implementation:**
- Hook up `create_status_tooltip_data()` to mouse hover in battle/exploration UI
- Show tooltip when hovering over status icons
- Display duration, stacks, and effects clearly

**Files to Modify:**
- `ui/hud_battle.py` - Add hover detection for status icons
- `ui/hud_exploration.py` - Add status tooltips in hero panel
- `engine/battle/renderer.py` - Add status hover in battle scene

**Impact:** High - Players can see status details without guessing

---

#### 2. **Smooth HP Bar Animations** ⚠️ Missing
**Current State:** HP bars update instantly when damage is taken

**Suggested Implementation:**
- Animate HP bar decrease over ~0.3-0.5 seconds
- Color transition (green → yellow → red) as HP decreases
- Optional: "shield" effect for guard status (overlay bar)

**Files to Modify:**
- `ui/hud_utils.py` - Add animated bar drawing function
- `ui/hud_battle.py` - Use animated bars in unit cards
- `ui/hud_exploration.py` - Use animated bars in hero panel

**Impact:** Medium-High - More polished, easier to see damage

---

#### 3. **Damage Number Improvements** 🔄 Enhancement
**Current State:** Floating damage numbers work, but could be enhanced

**Suggested Enhancements:**
- Add healing numbers (green, upward float)
- Add status effect numbers (e.g., "POISON -5" in green)
- Stack multiple damage numbers vertically if many occur quickly
- Add small shake/stagger animation for crits
- Optional: Show "RESIST" or "MISS" messages

**Files to Modify:**
- `engine/battle/renderer.py` - Enhance `draw_floating_damage()`
- `engine/battle/combat.py` - Track healing, status damage separately

**Impact:** Medium - Better feedback for all damage types

---

#### 4. **Skill Range Visualization** ⚠️ Missing
**Current State:** Players can't see skill range when selecting targets

**Suggested Implementation:**
- Highlight valid target tiles when skill is selected
- Show attack range/area on grid (colored overlay)
- Show invalid tiles (out of range) in dimmed color
- Optional: Preview damage on valid targets

**Files to Modify:**
- `engine/battle/renderer.py` - Add range overlay drawing
- `engine/scenes/battle_scene.py` - Calculate and store valid target tiles

**Impact:** High - Critical for tactical gameplay

---

#### 5. **Turn Order Indicator** ⚠️ Missing / Incomplete
**Current State:** May exist but not clearly visible

**Suggested Implementation:**
- Visual turn order list (portraits/icons in order)
- Highlight current unit
- Show next 3-5 units in queue
- Optional: Estimated turns until action (e.g., "3 turns")

**Files to Modify:**
- `ui/hud_battle.py` - Add turn order display
- `engine/scenes/battle_scene.py` - Calculate turn order

**Impact:** High - Important for tactical planning

---

### 📊 Medium Priority - Information Display

#### 6. **Combat Log Enhancements** 🔄 Enhancement
**Current State:** Combat log exists with color coding, but could be improved

**Suggested Enhancements:**
- Filter buttons (Combat/Exploration/System)
- Scrollable log (when many messages)
- Click to expand message details
- Export log to file (debugging)
- Optional: Message search

**Files to Modify:**
- `ui/hud_battle.py` - Enhance `_draw_battle_log_line()` and log panel
- `engine/core/message_log.py` - Add filtering/search functionality

**Impact:** Medium - Better for understanding what happened

---

#### 7. **Inventory Improvements** 🔄 Enhancement
**Current State:** Inventory screen exists, but could be more user-friendly

**Suggested Enhancements:**
- Sort/filter buttons (by type, rarity, stat, name)
- Item comparison tooltips (current vs hovered)
- Quick-use item slots (1-9 hotkeys in exploration)
- Item highlighting when equippable
- Optional: Item sets indicator (if wearing 2/3 of a set)

**Files to Modify:**
- `ui/inventory_enhancements.py` - May already have some features
- `ui/screens.py` - Add sorting/filtering to inventory screen
- `ui/hud_screens.py` - Enhance inventory display

**Impact:** Medium - Faster inventory management

---

#### 8. **Minimap for Exploration** ⚠️ Missing
**Current State:** No minimap visible in exploration mode

**Suggested Implementation:**
- Small minimap in corner showing explored area
- Player position indicator
- Optional: Enemies/items as dots
- Optional: Fog of war for unexplored areas

**Files to Modify:**
- `ui/hud_exploration.py` - Add minimap drawing
- `engine/exploration.py` - Track explored tiles

**Impact:** Medium - Helps with navigation

---

#### 9. **Stat Comparison Panel** ⚠️ Missing
**Current State:** Tooltips show stat changes, but no dedicated comparison view

**Suggested Implementation:**
- Side-by-side stat comparison when hovering equipment
- Show "Current" vs "With This Item" stats
- Highlight improvements in green, decreases in red
- Optional: Show all stats, not just changed ones

**Files to Modify:**
- `ui/tooltip.py` - Enhance `create_item_tooltip_data()` display
- `ui/hud_screens.py` - Add comparison panel to inventory

**Impact:** Low-Medium - Easier equipment decisions

---

### 🎨 Low Priority - Polish & Visual Appeal

#### 10. **Animated Status Indicators** ⚠️ Missing
**Current State:** Status icons are static

**Suggested Implementation:**
- Pulse animation for statuses about to expire (1 turn left)
- Glow effect for important buffs/debuffs
- Small particle effects for certain statuses (burning = flames, poison = bubbles)
- Optional: Icon shake for negative effects

**Files to Modify:**
- `ui/status_display.py` - Add animation state tracking
- `engine/battle/renderer.py` - Draw animated status indicators

**Impact:** Low - Visual polish, not critical

---

#### 11. **Screen Transitions** ⚠️ Missing
**Current State:** Screens appear/disappear instantly

**Suggested Implementation:**
- Fade-in/fade-out when opening/closing screens
- Slide animations (inventory slides in from right)
- Optional: Smooth camera transitions in battle

**Files to Modify:**
- `ui/screens.py` - Add transition state management
- `engine/core/game.py` - Handle screen transitions

**Impact:** Low - Nice polish, not gameplay critical

---

#### 12. **UI Themes** ⚠️ Missing
**Current State:** Single UI color scheme

**Suggested Implementation:**
- Dark/light mode toggle
- Optional: Colorblind-friendly palette
- Optional: High-contrast mode

**Files to Modify:**
- Create `ui/themes.py` - Define color palettes
- Update all UI drawing functions to use theme colors

**Impact:** Low - Accessibility/visual preference

---

#### 13. **Contextual Help/Tutorial System** 🔄 Enhancement
**Current State:** Tutorial systems exist (`combat_tutorial.py`, `exploration_tutorial.py`)

**Suggested Enhancements:**
- "?" button on screens showing help
- Contextual tooltips (first-time hints)
- Optional: Interactive tutorial mode
- Optional: Tutorial skip option

**Files to Modify:**
- `ui/screens.py` - Add help button
- `ui/tooltip.py` - Add help tooltip support

**Impact:** Low-Medium - Better onboarding for new players

---

#### 14. **Health Bar Colors** 🔄 Enhancement
**Current State:** HP bars are red, but could be more informative

**Suggested Implementation:**
- Dynamic color (green → yellow → red) based on HP percentage
- Optional: Gradient fill (green at top, red at bottom)
- Optional: Low HP warning (pulse/glow when <25%)

**Files to Modify:**
- `ui/hud_utils.py` - Enhance `_draw_bar()` with color interpolation

**Impact:** Low - Slight visual improvement

---

### 🔧 Technical Improvements

#### 15. **UI Performance Optimization** 🔄 Enhancement
**Current State:** UI scales properly, but could optimize rendering

**Suggested Optimizations:**
- Cache rendered text surfaces when possible
- Batch UI element drawing
- Reduce unnecessary redraws (only update changed elements)
- Optional: UI element pooling (reuse surfaces)

**Files to Modify:**
- All UI modules - Add caching where appropriate
- `ui/hud_utils.py` - Optimize bar drawing

**Impact:** Medium - Better performance on lower-end systems

---

#### 16. **Keyboard Navigation** ⚠️ Missing / Incomplete
**Current State:** Some keyboard shortcuts exist, but navigation could be improved

**Suggested Implementation:**
- Arrow keys to navigate menus/inventories
- Tab/Shift+Tab for focus cycling
- Enter/Space to select
- Esc to close/cancel
- Optional: Full keyboard-only gameplay support

**Files to Modify:**
- `ui/screens.py` - Add keyboard navigation state
- All screen modules - Add keyboard focus handling

**Impact:** Medium - Better accessibility and UX

---

#### 17. **Save/Load UI Improvements** 🔄 Enhancement
**Current State:** Save/load system exists, but UI could show more info

**Suggested Enhancements:**
- Save slot previews (timestamp, floor, level, character name)
- Save slot thumbnails (screenshot of current state)
- Auto-save indicator
- Save slot deletion confirmation

**Files to Modify:**
- `ui/hud_screens.py` - Enhance save/load screens
- `engine/core/save_system.py` - Add metadata storage

**Impact:** Medium - Better save management

---

## Priority Recommendations

### Phase 1: Critical Gameplay Features (1-2 weeks)
1. ✅ **Status Tooltip Integration** - High impact, low effort (functions exist)
2. ✅ **Skill Range Visualization** - Critical for tactical gameplay
3. ✅ **Turn Order Indicator** - Important for planning

### Phase 2: Visual Feedback (1-2 weeks)
4. ✅ **Smooth HP Bar Animations** - High polish impact
5. ✅ **Damage Number Enhancements** - Better feedback
6. ✅ **Animated Status Indicators** - Visual polish

### Phase 3: Information & Navigation (1-2 weeks)
7. ✅ **Combat Log Enhancements** - Better understanding
8. ✅ **Inventory Improvements** - Faster management
9. ✅ **Minimap** - Navigation aid

### Phase 4: Polish & Accessibility (1-2 weeks)
10. ✅ **Screen Transitions** - Visual polish
11. ✅ **Keyboard Navigation** - Better UX
12. ✅ **UI Themes** - Accessibility/preference

---

## Quick Wins (Easy + High Impact)

1. **Status Tooltip Integration** - Functions exist, just need to hook up mouse hover
2. ✅ **HP Bar Color Transitions** - ~~Simple color interpolation based on HP %~~ **COMPLETED**
3. ✅ **Damage Number Stacking** - ~~Allow multiple damage numbers to stack vertically~~ **COMPLETED**
4. **Combat Log Filtering** - Add filter buttons (already has color coding)
5. **Inventory Sorting** - Add sort by type/rarity buttons

---

## Files to Reference

### Current UI Implementation
- `ui/status_display.py` - Status display system
- `ui/tooltip.py` - Tooltip system
- `ui/hud_battle.py` - Battle UI
- `ui/hud_exploration.py` - Exploration UI
- `ui/screens.py` - Screen system
- `ui/ui_scaling.py` - UI scaling utilities
- `ui/hud_utils.py` - UI drawing utilities

### Related Documentation
- `docs/STATUS_EFFECTS_IMPROVEMENTS.md` - Status system details
- `docs/IMPROVEMENT_SUGGESTIONS.md` - General improvements (includes UI section)

---

## Notes

- Many status tooltip functions already exist - just need to integrate with mouse hover
- Floating damage numbers are already implemented and working well
- UI scaling system handles different resolutions well
- Tooltip system is well-designed and ready for expansion
- Consider accessibility early (colorblind modes, keyboard navigation)

**Focus on Phase 1 items first - they have the highest gameplay impact!**
