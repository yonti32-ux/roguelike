# Character Creation Enhancement - Quick Summary

## Key Decisions Made

### 1. Stat Distribution
- **Points**: 3-5 stat points (fixed, same for all classes)
- **Purpose**: Add replayability without overwhelming complexity
- **UI**: Simple +/- buttons with stat preview

### 2. Trait System (Point-Buy)
- **System**: Point-buy (not fixed count)
- **Starting Points**: 5-7 trait points
- **Trait Costs**: 1-3 points based on power
- **Features**:
  - Can add AND remove traits (spend/refund points)
  - Traits can synergize (bonus when combined)
  - Traits can connect/enhance perks
  - Traits can conflict (cannot have conflicting ones)
- **Balance**: 10-20% stat modifiers (percentage-based)

### 3. Backgrounds
- **Selection**: Class-based (player chooses from compatible backgrounds)
- **Balance**: 5-10% stat modifiers (percentage-based, less than traits)
- **Examples per Class**:
  - Warrior: Soldier, Noble, Blacksmith, Mercenary, Knight
  - Rogue: Street Urchin, Thief, Hunter, Merchant, Assassin
  - Mage: Scholar, Hermit, Priest, Apprentice, Noble

### 4. Companions
- **First Companion (Sellsword)**:
  - Fully customizable in-world (after game start)
  - Full customization screen (same as hero creation)
  - Customization happens when recruited (not at character creation)
- **Other Companions**:
  - Default: Randomly generated backgrounds/traits
  - Premium Option: Pay 100-200 gold to fully customize
  - Premium unlocks full customization screen

### 5. Enemies
- **Priority**: Lower priority, work on later (Phase 8)
- Will add variants with backgrounds/traits when ready

### 6. UI Design
- **Approach**: Multi-page wizard with summary/overview page
- **Pages** (8 total):
  1. Class Selection
  2. Background Selection (filtered by class)
  3. Stat Distribution
  4. Trait Selection (point-buy)
  5. Appearance Customization
  6. Equipment Selection
  7. Name Entry
  8. Summary/Overview (new - shows all selections)
- **Quick Start**: Button on class selection page
  - Auto-fills all pages with recommended/defaults
  - Player can still review/edit before finalizing
- **Navigation**: Left/Right arrows, progress indicator, back button

### 7. Balance Philosophy
- **Backgrounds**: 5-10% stat modifiers (small bonuses)
- **Traits**: 10-20% stat modifiers (more significant impact)
- **Stat Distribution**: 3-5 points = small but meaningful customization
- **Presets**: "Recommended" preset for each class (auto-fills all pages)
- **Goal**: Fun, not oppressive, optional complexity for those who want it

## Implementation Order

1. **Phase 1**: Data Structures (Background, Trait, Appearance, Stat Distribution)
2. **Phase 2**: Background System (registry, UI, stat calculation)
3. **Phase 3**: Stat Distribution (UI, calculation)
4. **Phase 4**: Trait System (point-buy, synergies, UI)
5. **Phase 5**: Appearance System
6. **Phase 6**: Equipment Selection
7. **Phase 7**: Companion Integration (customization screen, premium option)
8. **Phase 8**: Enemy Enhancement (later)

## Stat Calculation Order

1. Class base stats
2. Background stat modifiers (5-10% percentage)
3. Stat distribution points (flat values)
4. Trait stat modifiers (10-20% percentage)
5. Trait synergies (additional percentage bonuses)
6. Level-based growth
7. Perk stat modifiers
8. Equipment stat modifiers

## Save/Load Compatibility

- Bump save version to "1.3"
- All new fields are Optional
- Old saves get default values (no background, no traits, default appearance)
- Migration function handles backwards compatibility

---

See `CHARACTER_CREATION_ENHANCEMENT_PLAN.md` for full details.

