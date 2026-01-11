# Character Creation Enhancement Plan

## Overview
This document outlines a plan to enhance the character creation system to make it more in-depth and customizable, affecting heroes, companions, enemies, and items. The goal is to add depth while maintaining backwards compatibility and system integrity.

## Current State Analysis

### What We Have
1. **Character Creation Flow** (`engine/scenes/character_creation.py`)
   - Phase 1: Choose class (Warrior/Rogue/Mage)
   - Phase 2: Enter hero name
   - Simple class-based stat assignment

2. **Core Data Structures**
   - `HeroStats` (`systems/progression.py`): level, xp, gold, class_id, perks, skills
   - `ClassDef` (`systems/classes.py`): base stats, starting perks/skills/items
   - `CompanionState` (`systems/party.py`): similar to hero but for companions
   - `EnemyArchetype` (`systems/enemies.py`): enemy templates with scaling

3. **Save/Load System**
   - JSON-based serialization
   - Version: "1.2"
   - Serializes all hero/companion/enemy state

### What's Missing
- Background/Origin selection
- Custom stat distribution
- Trait/personality system
- Appearance customization
- Equipment choice at creation
- Background story generation
- Deeper customization options

---

## Enhancement Goals

### Primary Goals
1. **Add Background System**: Character backgrounds/origins that provide starting bonuses
2. **Stat Distribution**: Allow players to allocate stat points at creation
3. **Trait System**: Add character traits that affect gameplay
4. **Appearance System**: Sprite/color selection for visual customization
5. **Starting Equipment Selection**: Choose from equipment sets per class
6. **Extend to Companions**: Companions should use the same systems
7. **Extend to Enemies**: Enemies can have variants with backgrounds/traits
8. **Backwards Compatibility**: Old saves must still load correctly

### Secondary Goals
- Name generation integration
- Background story generation
- Stat reroll/randomization options
- Quick-start presets

---

## Phase 1: Core Systems Extension

### 1.1 Background/Origin System

**New Data Structure:**
```python
@dataclass
class Background:
    id: str
    name: str
    description: str
    stat_modifiers: StatBlock  # Bonus stats
    starting_perks: List[str]  # Bonus perks
    starting_skills: List[str]  # Bonus skills
    starting_items: List[str]  # Bonus items
    starting_gold_bonus: int
```

**Examples:**
- Noble: +gold, +status resist, diplomatic perk
- Street Urchin: +dodge, +pickpocket skill, lockpicks
- Scholar: +skill power, +mana, spellbook
- Soldier: +defense, +attack, military training perk
- Hermit: +mana regen, +status resist, herbalism skill

**Integration Points:**
- Add to `HeroStats`: `background_id: Optional[str]`
- Add to `CompanionState`: `background_id: Optional[str]`
- Add to `ClassDef`: `recommended_backgrounds: List[str]`
- Update save/load serialization

### 1.2 Stat Distribution System

**Enhancement:**
- Add `stat_points_available: int` to character creation
- Allow redistribution of base stats within constraints
- Class provides "recommended" stat distribution
- Background can provide stat points

**UI Flow:**
- After class selection, show stat distribution screen
- Points can be allocated to: HP, Attack, Defense, Skill Power, Crit, Dodge, Speed
- Class sets minimums/maximums per stat
- "Recommended" button to auto-fill based on class

**Data Structure:**
```python
@dataclass
class StatDistribution:
    hp_points: int = 0
    attack_points: int = 0
    defense_points: int = 0
    skill_power_points: float = 0.0
    crit_points: float = 0.0
    dodge_points: float = 0.0
    speed_points: float = 0.0
```

**Implementation:**
- Store distribution in `HeroStats.stat_distribution`
- Apply to `HeroStats.base` stats after class/base stats
- Also store in saves for consistency

### 1.3 Trait System (Point-Buy)

**New Data Structure:**
```python
@dataclass
class Trait:
    id: str
    name: str
    description: str
    category: str  # "personality", "physical", "mental", "social"
    cost: int  # Trait points required (1-3)
    stat_modifiers: StatBlock  # Percentage-based modifiers
    perk_modifiers: List[str]  # Perks that interact/enhance with this trait
    synergies: List[str]  # Trait IDs that synergize with this one
    conflicts: List[str]  # Trait IDs that conflict (cannot have both)
```

**Examples:**
- **Quick Learner** (cost: 1): +10% xp gain, -1 starting skill points
- **Brave** (cost: 2): +15% attack, -10% defense, resistance to fear status
- **Cautious** (cost: 2): +10% defense, -5% speed, bonus to perception
- **Lucky** (cost: 2): +5% crit chance, +3% dodge, -5% max hp
- **Strong** (cost: 2): +10% attack, +10% max hp, -5% speed
- **Nimble** (cost: 2): +10% speed, +5% dodge, -5% max hp
- **Gifted** (cost: 3): +20% skill power, -5% max hp
- **Tough** (cost: 2): +15% max hp, +5% defense, -5% attack

**Trait Synergies:**
- Brave + Strong: +5% attack (additional synergy bonus)
- Cautious + Nimble: +3% dodge (additional synergy bonus)
- Lucky + Quick Learner: +2% xp gain (additional synergy bonus)

**Integration:**
- `HeroStats.traits: List[str]` (trait IDs)
- `HeroStats.trait_points_available: int` (starting trait points: 5-7)
- Traits can be added/removed (spend/refund points)
- Traits can synergize with each other (bonus when combined)
- Traits can enhance/unlock perks (connection system)
- Traits can conflict (cannot have conflicting traits)
- Backgrounds can suggest certain traits (recommendations)

---

## Phase 2: Visual & Equipment Customization

### 2.1 Appearance System

**New Data Structure:**
```python
@dataclass
class AppearanceConfig:
    sprite_id: str  # Which sprite variant to use
    color_primary: Tuple[int, int, int]  # RGB color for customization
    color_secondary: Tuple[int, int, int]
    scale_factor: float = 1.0
```

**Integration:**
- `HeroStats.appearance: Optional[AppearanceConfig]`
- `CompanionState.appearance: Optional[AppearanceConfig]`
- Update sprite rendering to use appearance
- Store in saves

**UI:**
- Sprite selection from available variants
- Color picker for primary/secondary
- Preview panel showing character appearance

### 2.2 Starting Equipment Selection

**Enhancement:**
- Instead of fixed starting items, offer equipment sets
- Each class gets 2-3 equipment set options
- Sets can include: weapon choice, armor choice, trinket choice
- One set can be "recommended" for class

**Data Structure:**
```python
@dataclass
class EquipmentSet:
    id: str
    name: str
    description: str
    items: List[str]  # Item IDs
    recommended_for_classes: List[str]
```

**UI Flow:**
- After stat distribution, show equipment selection
- Display 2-3 sets per class
- Show stats comparison between sets
- Preview what items will be equipped

---

## Phase 3: Enhanced Character Creation Flow

### 3.1 New Multi-Phase Flow

**Proposed Phases:**
1. **Class Selection** (existing, enhanced)
   - Show class details with stats/preview
   - Add "recommended" backgrounds per class
   
2. **Background Selection** (new)
   - Show available backgrounds
   - Filter by compatibility with selected class
   - Show bonuses/penalties
   
3. **Stat Distribution** (new)
   - Distribute stat points
   - Show impact of choices
   - Preview final stats
   
4. **Trait Selection** (new - Point-Buy System)
   - Start with 5-7 trait points
   - Select traits by spending points
   - Show trait costs, available points
   - Display synergies (bonus effects when combined)
   - Show conflicts/warnings
   - Display trait effects (percentage-based)
   - Can add/remove traits (refund points)
   
5. **Appearance Customization** (new)
   - Select sprite variant
   - Choose colors
   - Preview appearance
   
6. **Equipment Selection** (new)
   - Choose starting equipment set
   - Preview equipped stats
   
7. **Name Entry** (existing, enhanced)
   - Add name generator button
   - Suggest names based on background/class

### 3.2 Quick Start Presets

**Add Preset System:**
- "Recommended" preset for each class
- "Random" preset for quick starts
- "Balanced" preset
- Custom preset saving (later feature)

---

## Phase 4: Companion System Enhancement

### 4.1 Apply Same Systems to Companions

**First Companion (Sellsword):**
- Recruited early in game (via story/quest)
- **Full customization screen** after recruitment
- Player can customize: background, traits (with point-buy), stat distribution, appearance
- Same systems as hero character creation
- Customization happens **in-world** (not at game start)
- Add companion customization UI/screen

**Other Companions:**
- **Default**: Randomly generated backgrounds/traits based on companion template
- **Premium Option**: Player can pay gold (100-200 gold) to fully customize
- Premium customization unlocks full customization screen (same as first companion)
- Random generation uses class-appropriate backgrounds and balanced trait selection

**Recruitment Flow:**
- Standard recruitment: Show generated companion stats, accept/reject
- Premium recruitment: Pay gold → full customization screen
- First companion: Always get customization screen (free)

**Data:**
- Add same fields to `CompanionState` as `HeroStats`
- Update companion stat calculation to include backgrounds/traits
- Update save/load serialization
- Add `customization_cost: int` field to track premium customization

---

## Phase 5: Enemy System Enhancement

### 5.1 Enemy Variants

**Enhancement:**
- Enemies can have "elite" variants with backgrounds/traits
- Bosses automatically get backgrounds/traits
- Random generation of enemy variants based on floor/tier

**Examples:**
- "Veteran" goblin: +attack, +defense, soldier background
- "Wise" skeleton: +skill power, scholar background
- "Berserker" orc: +attack, -defense, brave trait

**Data Structure:**
```python
@dataclass
class EnemyVariant:
    variant_id: str
    archetype_id: str  # Which base archetype
    background_id: Optional[str]
    traits: List[str]
    stat_modifiers: StatBlock
    name_prefix: str  # "Veteran", "Elite", etc.
```

---

## Phase 6: Implementation Strategy

### 6.1 Backwards Compatibility

**Migration Strategy:**
1. Add new fields as Optional in all data structures
2. Provide defaults for missing data in deserialization
3. Bump save version to "1.3"
4. Add migration function for old saves:
   - Old saves get default values (no background, no traits, default appearance)
   - Existing stats remain unchanged

**Save Version Handling:**
```python
def _deserialize_hero_stats(hero_stats: HeroStats, data: Dict[str, Any], version: str) -> None:
    # Existing fields (always load)
    hero_stats.level = data.get("level", 1)
    # ... existing code ...
    
    # New fields (version >= "1.3")
    if version >= "1.3":
        hero_stats.background_id = data.get("background_id")
        hero_stats.traits = list(data.get("traits", []))
        hero_stats.appearance = _deserialize_appearance(data.get("appearance"))
        # ... new fields ...
    else:
        # Default values for old saves
        hero_stats.background_id = None
        hero_stats.traits = []
        hero_stats.appearance = None
```

### 6.2 Incremental Implementation Order

**Step 1: Data Structures (Low Risk)**
1. Add `Background` class and registry
2. Add fields to `HeroStats` (as Optional)
3. Update save/load with backwards compatibility
4. Test: Load old saves, verify defaults work

**Step 2: Background System (Medium Risk)**
1. Create background registry with examples
2. Update character creation UI to include background selection
3. Apply background bonuses in stat calculation
4. Test: Create new character, verify bonuses apply

**Step 3: Stat Distribution (Medium Risk)**
1. Add stat distribution UI to character creation
2. Update stat calculation to include distribution
3. Test: Verify stats calculate correctly

**Step 4: Trait System (Medium Risk)**
1. Create trait registry
2. Add trait selection to character creation
3. Update stat calculation to include traits
4. Test: Verify traits work and conflicts handled

**Step 5: Appearance (Low Risk)**
1. Add appearance data structure
2. Add appearance selection UI
3. Update sprite rendering
4. Test: Verify appearance saves/loads

**Step 6: Equipment Selection (Low Risk)**
1. Create equipment sets
2. Add equipment selection UI
3. Update starting inventory
4. Test: Verify starting items correct

**Step 7: Companion Integration (Medium Risk)**
1. Add same fields to `CompanionState`
2. Update companion stat calculation
3. Update companion recruitment
4. Test: Recruit companion, verify stats

**Step 8: Enemy Enhancement (Low Risk)**
1. Add enemy variant system
2. Update enemy generation
3. Test: Verify variants spawn correctly

### 6.3 Testing Strategy

**Unit Tests:**
- Stat calculation with backgrounds/traits
- Save/load with new fields
- Backwards compatibility loading
- Trait conflict detection

**Integration Tests:**
- Full character creation flow
- Companion recruitment with new systems
- Enemy variant generation

**Gameplay Tests:**
- Create character, verify all bonuses apply
- Level up, verify progression works
- Save/load, verify data persists
- Recruit companion, verify stats correct

---

## Phase 7: Data Definitions

### 7.1 Background Registry

**File:** `systems/backgrounds.py`

**Example Backgrounds:**
- `noble`: +gold, status resist, diplomatic perk
- `street_urchin`: +dodge, pickpocket skill, lockpicks
- `scholar`: +skill power, +mana, spellbook item
- `soldier`: +defense, +attack, military training
- `hermit`: +mana regen, +status resist, herbalism
- `merchant`: +gold, trade perk, starting items
- `priest`: +mana, healing skill, holy symbol
- `thief`: +crit, +dodge, lockpicks, poison
- `blacksmith`: +defense, repair skill, tools
- `hunter`: +attack, tracking skill, bow

### 7.2 Trait Registry (Point-Buy)

**File:** `systems/traits.py`

**Trait Point System:**
- Players start with **5-7 trait points** (configurable)
- Traits cost 1-3 points based on power
- Can add/remove traits (spend/refund points)
- Maximum trait points cannot exceed starting amount

**Example Traits (with costs and percentages):**
- `quick_learner` (cost: 1): +10% xp gain, -1 starting skill points
- `brave` (cost: 2): +15% attack, -10% defense, fear resistance, synergies: ["strong"]
- `cautious` (cost: 2): +10% defense, -5% speed, perception bonus, synergies: ["nimble"]
- `lucky` (cost: 2): +5% crit chance, +3% dodge chance, -5% max hp, synergies: ["quick_learner"]
- `strong` (cost: 2): +10% attack, +10% max hp, -5% speed, synergies: ["brave"]
- `nimble` (cost: 2): +10% speed, +5% dodge, -5% max hp, synergies: ["cautious"]
- `tough` (cost: 2): +15% max hp, +5% defense, -5% attack
- `clever` (cost: 2): +15% skill power, +10% max mana, -5% attack
- `gifted` (cost: 3): +20% skill power, -5% max hp (premium trait)
- `focused` (cost: 1): +5% skill power, +5% mana regen

**Trait Conflicts:**
- `brave` conflicts with `cautious`
- `strong` conflicts with `nimble` (can still have both, but no synergy)

### 7.3 Equipment Sets

**File:** `systems/equipment_sets.py`

**Example Sets for Warrior:**
- `warrior_balanced`: longsword, chainmail, basic shield
- `warrior_aggressive`: greatsword, leather armor, damage trinket
- `warrior_defensive`: sword, plate armor, defense trinket

---

## Phase 8: UI/UX Considerations

### 8.1 Character Creation Screen Flow

**Multi-Page Navigation:**
- Use left/right arrow keys to navigate phases
- Show progress indicator (e.g., "Step 2 of 7")
- Allow going back to previous steps
- "Randomize" button for quick generation
- "Recommended" button for auto-fill

**Visual Design:**
- Preview panel showing character stats/appearance
- Clear indication of what's selected
- Tooltips explaining each option
- Stat impact preview when making choices

### 8.2 Companion Customization

**When Recruiting:**
- Show generated companion details
- Allow customization of appearance
- Optional: Allow stat reroll (if enabled)
- Show compatibility with party

---

## Phase 9: Integration with Existing Systems

### 9.1 Stat Calculation Updates

**Order of Application:**
1. Class base stats
2. Background stat modifiers
3. Stat distribution points
4. Trait stat modifiers
5. Level-based growth
6. Perk stat modifiers
7. Equipment stat modifiers

**Update Functions:**
- `recalc_companion_stats_for_level()` in `systems/party.py`
- `apply_class()` in `systems/progression.py`
- Stat calculation in battle system

### 9.2 Item System Integration

**Considerations:**
- Starting items from backgrounds should integrate with inventory
- Equipment sets should respect inventory limits
- Background items might need special handling

### 9.3 Name Generation Integration

**Enhancement:**
- Use existing name generation system (`systems/namegen/`)
- Generate names based on background/class
- Allow selection from generated list
- Still allow manual entry

---

## Phase 10: Future Enhancements

### 10.1 Advanced Features (Post-Phase 6)

- **Custom Presets**: Save/load character creation presets
- **Stat Reroll**: Randomize stats within constraints
- **Background Stories**: Generate narrative backgrounds
- **Trait Evolution**: Traits that change over time
- **Class Specializations**: Sub-classes within classes
- **Multi-Class System**: Combine classes (advanced)

### 10.2 Modding Support

- **JSON Definitions**: Move backgrounds/traits to JSON
- **Mod Loader**: Support external mod files
- **Custom Backgrounds**: User-defined backgrounds

---

## Risk Assessment

### High Risk Areas
1. **Save/Load Compatibility**: Old saves must work
   - **Mitigation**: Careful versioning, default values, extensive testing

2. **Stat Calculation Bugs**: Incorrect stat application
   - **Mitigation**: Unit tests, clear calculation order, validation

3. **UI Complexity**: Too many steps might overwhelm users
   - **Mitigation**: "Quick Start" option, clear navigation, progress indicator

### Medium Risk Areas
1. **Balance Issues**: New bonuses might break game balance
   - **Mitigation**: Careful stat tuning, playtesting, feedback loops

2. **Performance**: More data to save/load
   - **Mitigation**: Minimal data structures, efficient serialization

### Low Risk Areas
1. **Appearance System**: Visual only, doesn't affect gameplay
2. **Equipment Sets**: Simple data structure addition

---

## Success Criteria

### Must Have
- ✅ Background system implemented and working
- ✅ Stat distribution working correctly
- ✅ Traits system functional
- ✅ Backwards compatibility maintained
- ✅ Companions use same systems
- ✅ Save/load works for all new fields

### Nice to Have
- ✅ Appearance customization
- ✅ Equipment selection
- ✅ Enemy variants
- ✅ Name generation integration
- ✅ Quick start presets

### Future
- Custom presets
- Background stories
- Modding support

---

## Implementation Timeline Estimate

- **Phase 1 (Data Structures)**: 2-3 hours
- **Phase 2 (Background System)**: 4-6 hours
- **Phase 3 (Stat Distribution)**: 4-6 hours
- **Phase 4 (Traits)**: 4-6 hours
- **Phase 5 (Appearance)**: 3-4 hours
- **Phase 6 (Equipment Selection)**: 3-4 hours
- **Phase 7 (Companion Integration)**: 4-5 hours
- **Phase 8 (Enemy Enhancement)**: 3-4 hours
- **Testing & Bug Fixes**: 4-6 hours

**Total Estimate**: 31-44 hours

**Recommended Approach**: Implement incrementally, test after each phase, get feedback before moving to next phase.

---

## Questions to Answer Before Implementation - ANSWERED

1. **Stat Distribution**: ✅ Players get a few points (3-5 recommended) to add replayability without overwhelming new players. Fixed amount, simple and fair.
   
2. **Traits**: ✅ **Point-buy system** - Traits have a cost/score value. Can be added AND removed. Traits can synergize with each other and connect to perks. More complex than initially thought - this is a flexible trait management system.
   
3. **Backgrounds**: ✅ **Class-based** - Player chooses from backgrounds that are compatible with their selected class. Class determines which backgrounds are available.
   
4. **Companions**: ✅ 
   - **First companion (sellsword)**: Fully customizable in-world (after game start, not at character creation)
   - **Other companions**: Mostly randomly generated
   - **Premium option**: Players can pay extra gold to customize additional recruits
   
5. **Enemies**: ✅ Yes, but work on it later - Move enemy variants to Phase 8 (lower priority)
   
6. **UI**: ✅ **Hybrid approach recommended**:
   - Multi-page wizard (since we already have pages working)
   - Add a summary/overview page showing all selections
   - Progress indicator and clear navigation
   - "Quick Start" preset button for players who want to skip customization
   
7. **Balance**: ✅ 
   - **Percentage-based** stat modifiers (not flat values)
   - **Backgrounds**: Less effective than traits (smaller bonuses, ~5-10% modifiers)
   - **Traits**: More significant impact (~10-20% modifiers)
   - **Presets required**: For players who want to start quickly
   - **Not oppressive**: Must be fun, optional complexity for those who want it

---

## Updated Implementation Details

### Stat Distribution
- **Points available**: 3-5 stat points (fixed, same for all classes)
- **Distribution**: Can allocate to HP, Attack, Defense, Skill Power, Crit, Dodge, Speed
- **UI**: Simple +/- buttons with preview of final stats
- **Purpose**: Add replayability, allow players to customize their build slightly

### Trait System (Enhanced)
- **Point-buy system**: Each trait has a cost (e.g., 1-3 points)
- **Trait points**: Players start with 5-7 trait points to spend
- **Add/Remove**: Traits can be added and removed (spend/refund points)
- **Synergies**: Traits can have synergy bonuses when combined
- **Perk connections**: Traits can unlock or enhance certain perks
- **UI**: Show trait costs, available points, synergies, conflicts

**Example Trait Costs:**
- Minor traits: 1 point (e.g., "Quick Learner": +10% xp gain)
- Moderate traits: 2 points (e.g., "Brave": +15% attack, -10% defense)
- Major traits: 3 points (e.g., "Gifted": +20% skill power, -5% max hp)

### Background System
- **Class-based selection**: Each class has 3-5 compatible backgrounds
- **Modifiers**: Small percentage bonuses (5-10% stat changes)
- **Starting bonuses**: Small amounts of gold, items, or skills
- **Examples**: 
  - Warrior: Soldier, Noble, Blacksmith, Mercenary, Knight
  - Rogue: Street Urchin, Thief, Hunter, Merchant, Assassin
  - Mage: Scholar, Hermit, Priest, Apprentice, Noble

### Companion System
- **First companion (sellsword)**: 
  - Recruited early in game
  - Full customization screen after recruitment
  - Same systems as hero: background, traits, stat distribution, appearance
  - Customization happens in-world, not at character creation
- **Other companions**:
  - Randomly generated backgrounds/traits
  - Can pay gold (e.g., 100-200 gold) to customize them
  - Premium customization gives access to full customization screen
- **Implementation**: Add companion customization screen/UI

### UI Design Decision
- **Multi-page wizard** with overview:
  1. Class Selection
  2. Background Selection (filtered by class)
  3. Stat Distribution
  4. Trait Selection (point-buy system)
  5. Appearance Customization
  6. Equipment Selection
  7. Name Entry
  8. **Summary/Overview** (new - shows all selections before finalizing)
- **Quick Start button**: On class selection page - auto-fills everything with recommended/defaults
- **Navigation**: Left/Right arrows, progress indicator, back button on all pages

### Balance Philosophy
- **Backgrounds**: 5-10% stat modifiers, small bonuses
- **Traits**: 10-20% stat modifiers, more significant impact
- **Stat distribution**: 3-5 points = small but meaningful customization
- **Presets**: "Recommended" preset for each class (auto-fills all pages)
- **Optional complexity**: Full customization available but not required

---

## Next Steps

1. ✅ Questions answered - proceed with implementation
2. Create detailed technical specs for Phase 1 (with updated trait system)
3. Begin implementation with data structures
4. Test backwards compatibility early
5. Iterate based on testing and feedback

