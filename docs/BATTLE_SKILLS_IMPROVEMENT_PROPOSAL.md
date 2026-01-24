# Battle Skills System Improvement Proposal

## Current System Analysis

### How It Works Now
1. **Skill Acquisition**: Skills are unlocked through perks (`grant_skills`)
2. **Skill Improvement**: Skills can be upgraded in the skill tree (ranks 1-5)
3. **Skill Usage**: Only 4 skills can be assigned to hotbar slots (SKILL_1 through SKILL_4)
4. **Skill Arrangement**: Auto-assigned on first use, can be persisted on `hero_stats.skill_slots`
5. **Limitation**: No UI to rearrange skills; once you have more than 4 skills, excess skills are unusable

### Problems Identified
- ❌ No way to arrange/reorganize skills
- ❌ Once you reach 4 skills, additional skills are inaccessible
- ❌ No way to swap skills in/out of hotbar
- ❌ No strategic choice in skill loadouts

---

## Proposed Solutions

### Solution 1: Skill Loadout Manager (Recommended - Primary Solution)
**Concept**: A skill loadout system that allows players to create, save, and switch between different skill configurations.

**Features**:
- **Loadout Creation**: Create named loadouts (e.g., "Boss Fight", "AoE Clear", "Defensive")
- **Loadout Switching**: Quick switch between loadouts (in skill screen or before battle)
- **Multiple Loadouts**: Start with 2-3 loadout slots, unlock more through perks
- **Visual UI**: Drag-and-drop or click-to-assign interface in skill screen

**Implementation**:
- Add `skill_loadouts: Dict[str, List[Optional[str]]]` to `HeroStats`
- Add UI panel in skill screen for managing loadouts
- Allow switching loadouts before entering battle or in exploration mode
- Save/load loadouts with game saves

**Benefits**:
- ✅ Solves the arrangement problem
- ✅ Makes all skills accessible
- ✅ Adds strategic depth
- ✅ Feels like a natural progression system

---

### Solution 2: Expandable Hotbar (Secondary Solution)
**Concept**: Increase the number of available skill slots through progression.

**Features**:
- **Base Slots**: Start with 4 slots (current)
- **Unlock More Slots**: 
  - Perk: "Combat Mastery" - unlocks 5th slot at level 6
  - Perk: "Weapon Expertise" - unlocks 6th slot at level 10
  - Perk: "Legendary Warrior" - unlocks 7th slot at level 15
- **Skill Mastery Bonus**: Reaching max rank (5) on 3+ skills unlocks an additional slot

**Implementation**:
- Add `max_skill_slots: int = 4` to `HeroStats`
- Add perks that increment `max_skill_slots`
- Update `MAX_SKILL_SLOTS` to be dynamic per hero
- Update UI to show all available slots

**Benefits**:
- ✅ Rewards progression
- ✅ Makes skill mastery meaningful
- ✅ Simple to understand
- ✅ Works well with loadout system

---

### Solution 3: Skill Quick-Swap System (Tertiary Solution)
**Concept**: Allow swapping skills during battle or between battles with a quick-access menu.

**Features**:
- **Battle Swap**: Press a key (e.g., Tab) to open skill swap menu mid-battle
- **Quick Access**: Radial menu or list showing all unlocked skills
- **Cooldown Preservation**: Swapped skills maintain their cooldown state
- **Limited Swaps**: Maybe 1-2 swaps per battle to prevent abuse

**Alternative**: Only allow swapping between battles (before entering combat)

**Implementation**:
- Add skill swap UI overlay in battle scene
- Track which skills are "available" vs "in hotbar"
- Add swap action to input system
- Persist swaps to `hero_stats.skill_slots`

**Benefits**:
- ✅ Maximum flexibility
- ✅ Tactical decision-making
- ✅ All skills remain useful
- ⚠️ More complex to implement

---

### Solution 4: Skill Presets with Quick-Switch (Hybrid Solution)
**Concept**: Combine loadouts with quick-switch functionality.

**Features**:
- **Preset Slots**: 3-4 preset configurations (unlock more via perks)
- **Quick Switch**: Hotkey to cycle through presets (e.g., Shift+1, Shift+2, Shift+3)
- **Visual Indicator**: Show current preset name in battle UI
- **Easy Editing**: Edit presets in skill screen with drag-and-drop

**Implementation**:
- Similar to Solution 1, but with quick-switch hotkeys
- Add preset cycling to input system
- Visual feedback in battle HUD

**Benefits**:
- ✅ Best of both worlds
- ✅ Fast access to different builds
- ✅ Strategic depth
- ✅ Feels responsive and powerful

---

## Recommended Implementation Plan

### Phase 1: Core Loadout System (High Priority)
1. Add loadout storage to `HeroStats`
2. Create skill loadout UI in skill screen
3. Implement drag-and-drop or click-to-assign interface
4. Add loadout switching functionality
5. Save/load loadouts with game state

### Phase 2: Expandable Hotbar (Medium Priority)
1. Make `MAX_SKILL_SLOTS` dynamic per hero
2. Add perks that unlock additional slots
3. Update battle UI to show variable number of slots
4. Update auto-assignment logic

### Phase 3: Quick-Switch (Low Priority - Optional)
1. Add preset cycling hotkeys
2. Visual preset indicator in battle
3. Quick-switch menu (if mid-battle swapping is desired)

---

## UI/UX Design Ideas

### Skill Screen Enhancements
```
┌─────────────────────────────────────────────────────────┐
│ Skill Tree View                    │ Loadout Manager     │
│                                     │                     │
│  [Skill Nodes]                     │ Loadout: [Boss] ▼   │
│                                     │                     │
│                                     │ Slot 1: [Power]     │
│                                     │ Slot 2: [Lunge]     │
│                                     │ Slot 3: [Cleave]    │
│                                     │ Slot 4: [Taunt]     │
│                                     │                     │
│                                     │ [+ New Loadout]    │
│                                     │ [Save] [Delete]    │
└─────────────────────────────────────────────────────────┘
```

### Battle UI Enhancement
```
┌─────────────────────────────────────┐
│ Skills: [Boss Loadout]              │
│ [1] Power Strike  [2] Lunge        │
│ [3] Cleave        [4] Taunt        │
│                                     │
│ Press Tab to switch loadouts       │
└─────────────────────────────────────┘
```

### Drag-and-Drop Interface
- Click and drag skills from "Available Skills" list to hotbar slots
- Visual feedback: highlight valid drop zones
- Empty slots show as "[Empty]" with drop indicator
- Right-click to remove skill from slot

---

## Perk Ideas for Skill System

### Loadout-Related Perks
- **"Tactical Planning"** (Level 5): Unlock 2nd skill loadout slot
- **"Combat Versatility"** (Level 8): Unlock 3rd skill loadout slot
- **"Master Strategist"** (Level 12): Unlock 4th skill loadout slot

### Slot Expansion Perks
- **"Combat Mastery"** (Level 6): +1 skill slot (5 total)
- **"Weapon Expertise"** (Level 10): +1 skill slot (6 total)
- **"Legendary Warrior"** (Level 15): +1 skill slot (7 total)

### Skill Mastery Perks
- **"Skill Specialization"**: Reaching max rank on 3 skills unlocks +1 slot
- **"Combat Flexibility"**: Reaching max rank on 5 skills unlocks +1 slot

---

## Technical Considerations

### Data Structure Changes
```python
# In HeroStats
skill_loadouts: Dict[str, List[Optional[str]]] = field(default_factory=dict)
current_loadout: str = "default"
max_skill_slots: int = 4  # Can be increased by perks
```

### Save System Compatibility
- Loadouts should be saved with hero stats
- Backward compatibility: if no loadouts exist, use `skill_slots` as "default" loadout
- Migration: convert existing `skill_slots` to "default" loadout on first load

### Performance
- Loadout switching should be instant (just changing a list reference)
- UI updates should be smooth (no lag when dragging)
- Battle scene should cache current loadout for performance

---

## Balance Considerations

### Skill Slot Limits
- **Too Many Slots**: Overwhelming, reduces decision-making
- **Too Few Slots**: Frustrating, skills feel wasted
- **Sweet Spot**: 4-6 slots base, expandable to 7-8 with perks

### Loadout Limits
- **Too Many Loadouts**: Cluttered UI, analysis paralysis
- **Too Few Loadouts**: Doesn't solve the problem
- **Sweet Spot**: 2-3 base, expandable to 4-5 with perks

### Progression Curve
- Early game: 4 slots, 1 loadout (current system)
- Mid game: 5 slots, 2 loadouts (level 6-8)
- Late game: 6-7 slots, 3-4 loadouts (level 12+)

---

## Alternative: Skill Wheel/Radial Menu

If the above solutions feel too complex, consider a **radial menu** approach:

- Hold a key (e.g., Shift) to open radial menu
- Shows all unlocked skills in a circle
- Select skill with mouse or number keys
- Simpler to implement, but less organized than loadouts

**Pros**: Simple, all skills accessible, no UI clutter
**Cons**: Less strategic, can be slower in fast-paced combat

---

## Conclusion

**Recommended Approach**: Implement **Solution 1 (Loadout System)** as the primary solution, with **Solution 2 (Expandable Hotbar)** as a complementary feature.

This combination:
- ✅ Solves the arrangement problem
- ✅ Makes all skills accessible
- ✅ Adds strategic depth
- ✅ Rewards progression
- ✅ Feels natural and intuitive
- ✅ Maintains game balance

The loadout system is the most impactful change and addresses the core user concern: "no way to arrange them and once you reach a limited number there is nothing you can do."

