# Feature Improvement Suggestions

## Date: 2025-01-09

## Overview
This document provides suggestions for uplifting and enhancing existing features in the roguelike game. These are improvements to existing systems rather than new features.

---

## 1. Loot System Enhancements (High Impact, Medium Effort)

### Current State
- Basic drop system with floor scaling
- Equipment and consumable drops
- Rarity-based weighting

### Suggested Improvements

#### 1.1 Floor/Biome-Based Item Filtering (High Priority)
**Problem**: All items available at all floors, no progression feel
**Solution**: Add `min_floor`, `max_floor`, and `biome_tags` to `ItemDef`
- Early floors: basic equipment only
- Deeper floors: unlock better gear
- Biome-themed loot (fire items in lava areas, ice items in frozen areas)
**Impact**: Better progression curve, more meaningful loot discovery
**Effort**: Medium (need to update item definitions + filtering logic)

#### 1.2 Boss-Specific Loot (High Priority)
**Problem**: Bosses use same drop system as regular enemies
**Solution**: Guaranteed or high-chance drops for bosses
- Bosses always drop at least 1 item
- Higher chance for rare/epic items
- Boss-specific loot tables
**Impact**: Bosses feel rewarding, epic encounters
**Effort**: Low (extend existing loot functions)

#### 1.3 Multiple Item Drops (Medium Priority)
**Problem**: Only one equipment item per battle
**Solution**: Scale drops with encounter size/difficulty
- Boss battles: 1-2 guaranteed items + consumables
- Large enemy groups: higher drop rates
- Treasure chests: multiple items
**Impact**: More varied rewards, scaling with difficulty
**Effort**: Medium

#### 1.4 Enemy Type-Based Loot Tables (Medium Priority)
**Problem**: All enemies use same drop tables
**Solution**: Themed loot by enemy type
- Undead: more consumables, less equipment
- Humanoids: better equipment
- Beasts: fewer items, more gold
- Mages: higher chance for skill_power items
**Impact**: More variety, thematic consistency
**Effort**: Medium

#### 1.5 Consumables in Chests (Low Priority)
**Problem**: Chests only drop equipment
**Solution**: Mixed loot from chests
- Small chests: 1 item (equipment or consumable)
- Large chests: 1-2 items (mix)
- Treasure chests: guaranteed equipment + consumables
**Impact**: More variety in chest rewards
**Effort**: Low

**Reference**: See `docs/LOOT_SYSTEM_REVIEW.md` for detailed analysis

---

## 2. Battle / Combat Improvements

### Current State
- Turn-based grid combat with skills, statuses, and terrain (cover, hazard, obstacle)
- Skill-specific cast effects (orbital glows, shockwaves, auras); Guard has a dedicated shield-barrier cast effect and a shield icon on units with guard status
- AI profiles, targeting, movement, and combat log

### Suggested Improvements

#### 2.1 Skill & Status Visual Variety (Partially Done)
- **Done**: Guard skill uses a distinct shield-barrier cast effect and a shield icon on the unit while guarding.
- **Ideas**: Unique cast/impact visuals per skill family (e.g. different shockwave shapes or colors for physical vs magic), brief “impact” flash on hit, and subtle “under guard” aura or border on the unit tile.

#### 2.2 Combat Feedback & Juice
- **Screen shake** on big hits/crits (already present; tune intensity by damage/type).
- **Hit stop**: Short pause (0.05–0.1s) on crit or killing blow.
- **Floating text**: Different colors/sizes for normal, crit, heal, block, “Guarded!” when guard absorbs damage.
- **Sound**: Distinct sounds for guard, block, miss, and different damage types (optional if audio is in scope).

#### 2.3 Tactical Clarity
- **Threat/aggro indicator**: Show which enemy is targeting which ally (e.g. arrow or highlight).
- **Damage preview**: When hovering a skill on a target, show “Estimated damage: X–Y” or “Reduced by Guard”.
- **Status tooltips**: Hover on status icons (G, W, •, etc.) to see name and remaining duration.
- **Turn order**: Optional turn-order bar or list so players can plan around who acts next.

#### 2.4 Depth & Variety
- **Combo / follow-up**: Certain skills could grant “combo point” or enable a stronger follow-up if used in sequence.
- **Environment interaction**: Pushing enemies into hazards, destroying obstacles, or creating temporary cover.
- **Morale or stamina pacing**: Tension mechanics (e.g. stamina drain over time, or “last stand” at low HP) to make long fights feel more dynamic.
- **Boss phases**: Bosses change behavior or gain new abilities at HP thresholds (e.g. 50%, 25%).

#### 2.5 Balance & Progression
- **Guard tuning**: Guard already reduces damage; consider rank-based duration or extra “counter” chance when guarding.
- **Enemy variety**: More enemies that punish passive play (e.g. DoT if you don’t move) or reward positioning (backstab, flanking).
- **Rewards per turn**: Optional “speed bonus” (e.g. finish in under N turns for extra loot) to encourage aggressive play.

**Reference**: Battle scene in `engine/battle/`, skills in `systems/skills.py`, visuals in `engine/battle/visual_effects.py` and `engine/battle/renderer.py`.

---

## 3. Quest System Enhancements (High Impact, High Effort)

### Current State
- Basic quest structure with objectives and rewards
- Quest types: KILL, EXPLORE, COLLECT, DISCOVER
- Simple completion tracking

### Suggested Improvements

#### 2.1 Quest Varieties & Randomization (High Priority)
**Problem**: Quests are static, limited variety
**Solution**: Expand quest generation system
- Random quest parameters (enemy types, quantities, locations)
- Quest chains (multi-part quests)
- Daily/weekly quests
- Optional objectives with bonus rewards
**Impact**: Much more replayability, varied gameplay
**Effort**: High (requires quest generation system)

#### 2.2 Quest Difficulty Scaling (Medium Priority)
**Problem**: Quest difficulty doesn't scale with player
**Solution**: Dynamic quest difficulty
- Quests scale with player level/floor
- Optional difficulty modifiers (+rewards, -time)
- Challenge quests (harder but better rewards)
**Impact**: Better balance, meaningful choices
**Effort**: Medium

#### 2.3 Quest Rewards Variety (Medium Priority)
**Problem**: Rewards are just gold/XP/items
**Solution**: Expand reward types
- Reputation/faction rewards
- Unlock new areas/NPCs
- Permanent stat bonuses
- Skill unlocks
- Special equipment
**Impact**: More meaningful progression
**Effort**: Medium

#### 2.4 Quest UI Improvements (Low Priority)
**Problem**: Quest tracking could be more intuitive
**Solution**: Enhanced quest UI
- Progress bars for objectives
- Quest map markers
- In-progress quest indicators
- Quest log filtering/sorting
**Impact**: Better user experience
**Effort**: Low-Medium

---

## 4. Economy System Enhancements (Medium Impact, Medium Effort)

### Current State
- Dynamic pricing based on stats/rarity
- Shop markup and sell prices
- Merchant inventory generation

### Suggested Improvements

#### 3.1 Trading System (High Priority)
**Problem**: Economy is buy/sell only
**Solution**: Add trading mechanics
- Bartering system (negotiate prices)
- Trade items for items
- Reputation affects prices
- Dynamic market (prices fluctuate)
**Impact**: More engaging economy, strategic decisions
**Effort**: High

#### 3.2 Merchant Specialization (Medium Priority)
**Problem**: All merchants are the same
**Solution**: Different merchant types
- Weapon merchants (better weapon selection)
- Armor merchants (better armor selection)
- General merchants (variety)
- Specialty merchants (rare items)
**Impact**: More variety, strategic choices
**Effort**: Medium

#### 3.3 Economy Services (Medium Priority)
**Problem**: Limited gold sinks
**Solution**: Add services
- Item repair (degraded equipment)
- Item upgrade/enhancement
- Item identification (cursed items)
- Storage expansion
**Impact**: More uses for gold, progression systems
**Effort**: High (requires new systems)

#### 3.4 Price Negotiation (Low Priority)
**Problem**: Prices are fixed
**Solution**: Charisma/persuasion affects prices
- Higher charisma = better prices
- Skills/perks that improve trading
- Negotiation minigame
**Impact**: Stats matter outside combat
**Effort**: Medium

---

## 5. Combat System Enhancements (Medium Impact, Medium Effort)

### Current State
- Turn-based combat with skills
- Status effects and buffs/debuffs
- AoE abilities
- Skill ranks and progression

### Suggested Improvements

#### 4.1 Skill Combinations & Synergies (High Priority)
**Problem**: Skills work in isolation
**Solution**: Add skill synergies
- Combo attacks (skill A + skill B = bonus)
- Status effect combinations
- Class synergy bonuses
- Team combo moves
**Impact**: More tactical depth, build variety
**Effort**: High

#### 4.2 Environmental Combat (Medium Priority)
**Problem**: Combat is flat, no environment interaction
**Solution**: Add environmental elements
- Hazards (fire, traps, terrain)
- Interactive objects (explosive barrels, cover)
- Terrain advantages (high ground, cover)
- Environmental skills
**Impact**: More dynamic combat
**Effort**: High (requires map system changes)

#### 4.3 Combat Feedback & Visuals (Medium Priority)
**Problem**: Combat could be more visually engaging
**Solution**: Enhance combat visuals
- Damage numbers floating text
- Status effect icons/animations
- Skill visual effects
- Hit indicators (critical, miss, etc.)
**Impact**: Better player feedback, more engaging
**Effort**: Medium

#### 4.4 AI Improvements (Medium Priority)
**Problem**: Enemy AI could be smarter
**Solution**: Enhance enemy behavior
- Better target selection
- Skill combos for enemies
- Tactical positioning
- Adaptive difficulty
**Impact**: More challenging, interesting combat
**Effort**: High

**Note**: Some skills have TODO comments about special handling needed (taunt, line AoE, etc.)

---

## 6. Party/Companion System Enhancements (Medium Impact, Medium Effort)

### Current State
- Companion recruitment
- Individual companion progression
- Equipment per companion
- Skill slots and ranks

### Suggested Improvements

#### 5.1 Companion Relationships (High Priority)
**Problem**: Companions are just stats
**Solution**: Add relationship system
- Companion loyalty/friendship
- Relationship affects combat performance
- Companion quests/storylines
- Personality traits affect behavior
**Impact**: More engaging party management
**Effort**: High

#### 5.2 Companion Roles & Formation (Medium Priority)
**Problem**: Limited tactical positioning
**Solution**: Add formation system
- Formation bonuses
- Role-based positioning
- Formation-specific skills
- Tactical advantages
**Impact**: More strategic depth
**Effort**: Medium

#### 5.3 Companion Management UI (Medium Priority)
**Problem**: Managing multiple companions is tedious
**Solution**: Improve companion UI
- Quick equip/compare
- Bulk operations
- Companion preview/comparison
- Party overview screen
**Impact**: Better UX
**Effort**: Low-Medium

#### 5.4 Companion Interactions (Low Priority)
**Problem**: Companions don't interact much
**Solution**: Add companion interactions
- Conversation system
- Companion banter
- Relationship events
- Companion opinions on decisions
**Impact**: More immersive
**Effort**: High

---

## 7. Inventory System Enhancements (Low Impact, Low Effort)

### Current State
- Full inventory system with filtering/sorting
- Equipment slots
- Consumable usage
- Good UI with search

### Suggested Improvements

#### 6.1 Item Sets (Medium Priority)
**Problem**: No set bonuses for items
**Solution**: Add item set system
- Sets of 2-4 items
- Set bonuses when wearing multiple pieces
- Set identification in UI
**Impact**: More build variety
**Effort**: Medium

#### 6.2 Item Comparison (Low Priority)
**Problem**: Comparing items is manual
**Solution**: Add comparison UI
- Side-by-side comparison
- Stat difference highlights
- Upgrade indicators
**Impact**: Better UX
**Effort**: Low

#### 6.3 Item Favorites/Lock (Low Priority)
**Problem**: No way to protect important items
**Solution**: Add item management features
- Favorite items (mark as important)
- Lock items (prevent selling/accidental use)
- Item notes/tags
**Impact**: Quality of life
**Effort**: Low

---

## 8. Status Effect System Enhancements (Medium Impact, Low Effort)

### Current State
- Basic status effects (buffs/debuffs)
- Status stacking rules
- Status application from skills

### Suggested Improvements

#### 7.1 Status Effect Combinations (High Priority)
**Problem**: Status effects work independently
**Solution**: Add status combinations
- Fire + Poison = Explosion
- Frozen + Fire = Melt (different effect)
- Stacked effects create new effects
**Impact**: More tactical depth
**Effort**: Medium

#### 7.2 Status Effect UI Improvements (Medium Priority)
**Problem**: Status tracking could be clearer
**Solution**: Enhance status display
- Status icons with tooltips
- Duration indicators
- Stack count display
- Status history/log
**Impact**: Better player understanding
**Effort**: Low-Medium

#### 7.3 Status Effect Resistance System (Low Priority)
**Problem**: Status resistance is simple
**Solution**: Expand resistance system
- Different resistances for different status types
- Resistance from equipment/perks
- Temporary resistance buffs
**Impact**: More depth
**Effort**: Medium

---

## 9. UI/UX Improvements (High Impact, Variable Effort)

### Current State
- Good fullscreen screens for inventory/character/shop
- Some code duplication noted in documentation
- Long functions that could be refactored

### Suggested Improvements

#### 8.1 UI Code Refactoring (High Priority - Code Quality)
**Problem**: Code duplication, long functions (see `CODE_REVIEW_FINDINGS.md`)
**Solution**: Extract common patterns
- Extract status indicator rendering
- Extract stats display logic
- Extract perk rendering
- Create reusable UI components
**Impact**: Better maintainability, easier to add features
**Effort**: Medium (see `REFACTORING_SUGGESTIONS.md`)

#### 8.2 Tooltip System Improvements (Medium Priority)
**Problem**: Tooltips are basic
**Solution**: Enhanced tooltips
- Rich formatting
- Comparison tooltips (show current vs new)
- Contextual tooltips
- Tooltip animations
**Impact**: Better information display
**Effort**: Low-Medium

#### 8.3 Keyboard Shortcuts & Keybindings (Medium Priority)
**Problem**: Limited customization
**Solution**: Keybinding system
- Customizable keybinds
- Keybind UI/menu
- Multiple keybind profiles
- Hotkey tooltips
**Impact**: Better accessibility, player preference
**Effort**: Medium

#### 8.4 UI Themes/Styling (Low Priority)
**Problem**: UI style is fixed
**Solution**: Add theming support
- Color schemes
- Font options
- UI scale options
- Theme presets
**Impact**: Customization, accessibility
**Effort**: High

---

## 10. Progression System Enhancements (Medium Impact, Medium Effort)

### Current State
- Level system with XP
- Perk selection on level up
- Skill rank system
- Class-based progression

### Suggested Improvements

#### 9.1 Prestige/Meta Progression (High Priority)
**Problem**: No long-term progression
**Solution**: Add meta-progression
- Prestige system (restart with bonuses)
- Permanent unlocks
- Meta currency
- Unlockable content
**Impact**: Long-term replayability
**Effort**: High

#### 9.2 Achievement System (Medium Priority)
**Problem**: No achievements/milestones
**Solution**: Add achievement system
- Achievement tracking
- Achievement rewards
- Achievement UI
- Progress indicators
**Impact**: Goals, replayability
**Effort**: Medium

#### 9.3 More Perk Options (Medium Priority)
**Problem**: Limited perk variety
**Solution**: Expand perk system
- More perk branches
- Synergy perks
- Conditional perks
- Unique perks
**Impact**: More build variety
**Effort**: Medium-High

#### 9.4 Skill Tree Visualization (Low Priority)
**Problem**: Skill progression is not visualized
**Solution**: Add skill tree UI
- Visual skill tree
- Prerequisites shown
- Upgrade paths
- Skill descriptions
**Impact**: Better planning, understanding
**Effort**: Medium

---

## 11. Name Generation System Enhancements (Low Impact, Low Effort)

### Current State
- Name generation for various entities
- Pattern-based generation
- Good variety

### Suggested Improvements

#### 10.1 Name Customization (Low Priority)
**Problem**: Generated names can't be customized
**Solution**: Allow name editing
- Rename companions
- Rename player character
- Name suggestions
**Impact**: Personalization
**Effort**: Low

#### 10.2 Name Themes (Low Priority)
**Problem**: Names use single style
**Solution**: Add name themes
- Different naming styles
- Cultural themes
- Fantasy vs realistic
- Player preference
**Impact**: More variety
**Effort**: Low-Medium

---

## Priority Recommendations

### Quick Wins (Low Effort, High Impact)
1. **Boss-Specific Loot** - Easy to implement, high player satisfaction
2. **Consumables in Chests** - Simple extension of existing system
3. **Item Comparison UI** - Straightforward UI addition
4. **Status Effect UI Improvements** - Visual polish

### High Impact Features (Medium-High Effort)
1. **Floor/Biome-Based Item Filtering** - Better progression curve
2. **Quest Varieties & Randomization** - Major replayability boost
3. **Trading System** - More engaging economy
4. **Skill Combinations & Synergies** - Tactical depth

### Code Quality Improvements
1. **UI Code Refactoring** - Better maintainability (see existing docs)
2. **Extract Magic Numbers** - Already documented
3. **Type Safety Improvements** - Better code quality

---

## Implementation Strategy

1. **Phase 1**: Quick wins and code quality (1-2 weeks)
   - Boss loot, consumables in chests
   - UI refactoring (extract common patterns)
   - Item comparison UI

2. **Phase 2**: Medium-impact features (2-4 weeks)
   - Floor/biome item filtering
   - Quest system enhancements
   - Economy improvements
   - Companion management UI

3. **Phase 3**: High-impact features (1-2 months)
   - Trading system
   - Skill synergies
   - Companion relationships
   - Meta-progression

---

## Notes

- Many of these improvements build on existing systems
- Reference existing documentation for detailed analysis:
  - `CODE_REVIEW_FINDINGS.md` - Code quality issues
  - `LOOT_SYSTEM_REVIEW.md` - Loot system analysis
  - `REFACTORING_SUGGESTIONS.md` - UI refactoring plan
  - `STAT_SYSTEM_ANALYSIS.md` - Stat system overview
- Consider player feedback when prioritizing features
- Test incrementally - don't try to implement everything at once

