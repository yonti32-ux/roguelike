# HUD Overhaul Plan

## Current State Analysis

### Exploration HUD (`draw_exploration_ui`)
**Location:** Top-left corner
**Current Elements:**
- Hero panel (280x210px, semi-transparent black)
  - Name + Class
  - Floor number
  - Level + XP (with XP bar)
  - HP (with HP bar)
  - Stamina (with bar, if > 0)
  - Mana (with bar, if > 0)
  - ATK/DEF (with gear bonuses)
  - Gold
- Context hints (below hero panel)
  - Stairs hints
  - Room vibes
  - Nearby threats
  - Chest/event proximity
- Bottom message band
  - Latest log message
  - Controls hint

**Issues:**
- Panel is cramped, especially with stamina/mana
- Information density is high
- No party member display
- Context hints can overlap/stack awkwardly
- No minimap or area awareness
- Controls hint is basic

### Battle HUD (`BattleScene.draw`)
**Location:** Top of screen
**Current Elements:**
- Top-left: Party HP total
- Top-center: Turn info ("Turn: player/enemy")
- Top-center: Active unit name
- Top-center: Active unit panel (HP, stamina, mana bars)
- Top-right: Enemy HP total
- Top-right: Enemy group label
- Bottom: Combat log (6 lines)
- Bottom: Action hints

**Issues:**
- Very basic layout
- No individual unit panels
- No skill hotbar visible
- No status effect indicators
- Combat log takes bottom space but could be better
- No turn order preview
- Resource bars are small/hard to read

## Goals

### Visual Design
1. **Modern, Clean Aesthetic**
   - Consistent color scheme
   - Better use of space
   - Clear visual hierarchy
   - Smooth borders/rounded corners (if possible with pygame)
   - Better contrast and readability

2. **Information Architecture**
   - Group related information
   - Prioritize critical info (HP, resources)
   - Make secondary info accessible but not intrusive
   - Use icons/symbols where helpful

3. **Responsive Layout**
   - Adapt to screen size
   - Don't block important game elements
   - Minimize overlap with game world

### Exploration HUD Improvements

#### Hero Panel (Top-Left)
- **Compact Header:**
  - Name + Class (one line)
  - Floor + Level (one line)
  - Gold (small, top-right of panel)

- **Resource Bars (Vertical or Horizontal):**
  - HP bar (larger, prominent)
  - XP bar (smaller, below HP)
  - Stamina bar (if > 0, color-coded)
  - Mana bar (if > 0, color-coded)
  - All bars with current/max text

- **Stats Section:**
  - ATK / DEF (with gear bonuses in smaller text)
  - Maybe crit/dodge if relevant
  - Skill Power if != 1.0

- **Party Preview (if companions exist):**
  - Small icons/panels for each companion
  - HP bar for each
  - Quick status (alive/dead, status effects)

#### Context Panel (Mid-Left or Bottom-Left)
- **Organized Context Stack:**
  - Stairs (if on stairs)
  - Room type/vibe
  - Nearby enemies count
  - Nearby interactables (chest, merchant, event)
  - All in a clean, scrollable or collapsible format

#### Bottom Bar
- **Message Area:**
  - Latest message (larger, more prominent)
  - Message history toggle (L key?)

- **Controls Hint:**
  - Context-sensitive controls
  - Only show relevant actions
  - Format: "I: Inventory | C: Character | E: Interact"

#### Optional Additions
- **Minimap** (top-right corner, small)
  - Shows explored area
  - Player position
  - Nearby enemies (red dots)
  - Stairs (up/down markers)

- **Compass/Direction Indicator**
  - Shows cardinal directions
  - Useful for navigation

### Battle HUD Improvements

#### Top Bar (Full Width)
- **Left Side - Party Panel:**
  - Individual unit cards (Hero + Companions)
  - Each card shows:
    - Name
    - HP bar (large, prominent)
    - Stamina bar (if applicable)
    - Mana bar (if applicable)
    - Status effect icons
    - Turn indicator (highlight active unit)

- **Center - Battle Info:**
  - Turn counter
  - Current phase (Player Turn / Enemy Turn)
  - Active unit name (large, prominent)
  - Turn order preview (next 2-3 units)

- **Right Side - Enemy Panel:**
  - Individual enemy cards (up to 3-4)
  - Each card shows:
    - Name/Type
    - HP bar
    - Status effect icons
    - Target indicator (if selected)

#### Active Unit Panel (Center-Top, Larger)
- **Detailed Stats:**
  - Large HP bar
  - Stamina/Mana bars (if applicable)
  - Current position (grid coordinates)
  - Movement range indicator
  - Attack range indicator

#### Skill Hotbar (Bottom-Center)
- **Visible Skill Slots:**
  - 4 skill slots (1-4 keys)
  - Each shows:
    - Skill name/icon
    - Cooldown timer
    - Resource cost (stamina/mana)
    - Available/unavailable state
  - Guard action (separate, always available)

#### Combat Log (Bottom-Right)
- **Improved Layout:**
  - Scrollable log (more lines visible)
  - Color-coded messages (damage, healing, status)
  - Action history
  - Can be toggled/collapsed

#### Action Hints (Bottom-Left)
- **Context-Sensitive:**
  - Current action mode (Move / Attack / Skill)
  - Available actions
  - Navigation hints

## Implementation Plan

### Phase 1: Exploration HUD Refactor
1. **Restructure Hero Panel**
   - Compact header design
   - Better bar layout
   - Add party preview
   - Improve stat display

2. **Improve Context Panel**
   - Better organization
   - Cleaner stacking
   - Icons/symbols for different context types

3. **Enhance Bottom Bar**
   - Better message display
   - Improved controls hint
   - Message history access

### Phase 2: Battle HUD Refactor
1. **Create Unit Card Component**
   - Reusable card for hero/companion/enemy
   - HP, resources, status effects
   - Turn indicator

2. **Top Bar Layout**
   - Party panel (left)
   - Battle info (center)
   - Enemy panel (right)

3. **Skill Hotbar**
   - Visible skill slots
   - Cooldown/resource display
   - Visual feedback

4. **Combat Log Enhancement**
   - Better formatting
   - Color coding
   - Scrollable

### Phase 3: Polish & Optional Features
1. **Minimap** (if time permits)
2. **Visual polish** (borders, shadows, animations)
3. **Settings** (HUD scale, toggle elements)

## Technical Considerations

### Code Organization
- Create reusable HUD components:
  - `UnitCard` - for displaying unit info
  - `ResourceBar` - enhanced bar drawing
  - `StatusIcon` - status effect display
  - `SkillSlot` - skill hotbar slot

### Performance
- Cache rendered text surfaces where possible
- Minimize redraws
- Use efficient pygame operations

### Accessibility
- Clear text sizes
- High contrast
- Color-blind friendly (don't rely only on color)

## Files to Modify

1. `ui/hud.py` - Exploration HUD (`draw_exploration_ui`)
2. `engine/battle_scene.py` - Battle HUD (`draw` method, `_draw_active_unit_panel`)
3. Potentially create `ui/hud_components.py` for reusable components

## Design Principles

1. **Clarity First** - Information should be immediately understandable
2. **Context Matters** - Show relevant info when needed
3. **Consistency** - Same visual language across exploration and battle
4. **Non-Intrusive** - Don't block gameplay
5. **Scalable** - Works at different resolutions

