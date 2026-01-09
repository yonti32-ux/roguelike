# Skills and Perks Expansion Plan

## Overview
This document outlines the plan to expand and improve the perks and skills system, adding skill point allocation, skill trees, class-specific variations, and better scaling with level progression.

## Current State Analysis

### Perks System (`systems/perks.py`)
- **Structure**: Perks are passive bonuses with stat modifications
- **Selection**: On level up, player chooses from 3 random perk options
- **Branches**: 5 branches (vitality, blade, ward, focus, mobility)
- **Prerequisites**: Perks can require other perks
- **Skill Unlocks**: Some perks grant skills via `grant_skills` field
- **Application**: Perks modify stats when learned (apply_fn)

### Skills System (`systems/skills.py`)
- **Structure**: Skills are combat abilities with cooldowns and costs
- **Unlocking**: Skills are unlocked via perks (grant_skills) or starting skills
- **Properties**: base_power, cooldown, mana_cost, stamina_cost, status effects
- **No Progression**: Skills are binary (unlocked/not unlocked), no levels or upgrades

### Classes (`systems/classes.py`)
- **Warrior**: Tanky melee, high stamina
- **Rogue**: Mobile skirmisher, high crit/dodge
- **Mage**: Fragile caster, high skill_power and mana
- **Starting Perks**: Each class starts with specific perks
- **Starting Skills**: Each class starts with specific skills

### Companions (`systems/party.py`)
- **Progression**: Companions level up alongside hero
- **Perks**: Companions can learn perks (same system as hero)
- **Skills**: Companions have skill slots and can learn skills
- **Stats**: Derived from template factors + level + perks + equipment

## Goals

1. **Skill Point System**: Add skill points gained on level up to improve unlocked skills
2. **Skill Screen**: Create a UI screen for allocating skill points
3. **Skill Trees**: Eventually evolve into visual skill trees with branches
4. **Class-Specific**: Different skill trees/options per class
5. **Companion Support**: Skill screen works for hero and companions
6. **Expanded Content**: More skills and perks to fill out the trees
7. **Logical Scaling**: Skills and perks scale appropriately with level

## Proposed Architecture

### Phase 1: Skill Points Foundation

#### 1.1 Add Skill Points to Progression
- **HeroStats**: Add `skill_points: int` field (starts at 0)
- **CompanionState**: Add `skill_points: int` field
- **Level Up Rewards**: Grant skill points on level up
  - **Scaling Formula**: `skill_points_per_level = 1 + (level // 5)`
    - Levels 1-4: 1 point per level
    - Levels 5-9: 2 points per level
    - Levels 10-14: 3 points per level
    - Levels 15-19: 4 points per level
    - Levels 20+: 5 points per level
  - Hero and Companions: Same rate
- **Storage**: Track skill points separately from perks

#### 1.2 Skill Levels/Ranks
- **Skill Structure**: Add `max_rank: int` to Skill dataclass (default 5)
- **Current Rank**: Track per entity (hero/companion)
  - HeroStats: `skill_ranks: Dict[str, int]` (skill_id -> current_rank)
  - CompanionState: `skill_ranks: Dict[str, int]`
- **Rank Effects**: Each rank improves the skill:
  - Increase base_power (e.g., +10% per rank)
  - Reduce cooldown (e.g., -1 turn every 2 ranks)
  - Reduce costs (e.g., -1 stamina/mana per rank)
  - Increase status effect duration/power
  - Unlock new effects at certain ranks

#### 1.3 Skill Point Allocation Rules
- **Prerequisites**: Can only rank up skills that are unlocked
- **Cost Scaling**: Higher ranks cost more points
  - Rank 1: 1 point
  - Rank 2: 2 points
  - Rank 3: 3 points
  - Rank 4: 4 points
  - Rank 5: 5 points
  - Total: 15 points to max a skill
- **Refund**: Optional (maybe later), for now no refunds

### Phase 2: Skill Screen UI

#### 2.1 New Scene: SkillScreen
- **Location**: `engine/skill_screen.py` or `ui/skill_screen.py`
- **Access**: From exploration mode (key binding, e.g., 'K' or menu)
- **Entity Selection**: Tabs or dropdown to switch between hero/companions
- **Layout**:
  - Left: List of unlocked skills (grouped by branch/category)
  - Center: Selected skill details (current rank, effects, next rank preview)
  - Right: Available skill points display
  - Bottom: Instructions/controls

#### 2.2 Skill Display
- **Skill List**: Show all unlocked skills for selected entity
  - Skill name
  - Current rank (e.g., "Rank 3/5")
  - Can rank up indicator (if points available)
  - Branch/category badge
- **Skill Details**: When selected, show:
  - Full description
  - Current stats (power, cooldown, costs)
  - Next rank preview (what changes)
  - Cost to upgrade
  - Upgrade button/hotkey

#### 2.3 Interaction
- **Navigation**: Arrow keys or mouse to select skills
- **Upgrade**: Press Enter/Space or click button to rank up
- **Confirmation**: Optional confirmation dialog for expensive upgrades
- **Exit**: ESC to close screen

### Phase 3: Class-Specific Skill Trees

#### 3.1 Skill Categories/Branches
- **Warrior Branches**:
  - **Weapon Mastery**: Physical damage skills (power_strike, lunge, cleave)
  - **Defense**: Tanking skills (guard, shield_bash, taunt)
  - **Berserker**: High-risk high-reward skills (fury, bloodlust)
- **Rogue Branches**:
  - **Stealth**: Evasion and positioning (nimble_step, shadow_strike)
  - **Precision**: Crit-focused skills (backstab, precision_strike)
  - **Poison**: DoT skills (poison_strike, venom_blade)
- **Mage Branches**:
  - **Destruction**: Damage spells (focus_blast, fireball, lightning)
  - **Control**: CC spells (slow, stun, charm)
  - **Support**: Buffs/debuffs (haste, weaken, shield)

#### 3.2 Class-Specific Skills
- **Unlock Methods**:
  - Starting skills (class-specific)
  - Perks grant class-specific skills
  - Some skills available to all classes (guard, basic attacks)
- **Skill Availability**: Filter skills by class when displaying
- **Cross-Class**: Some skills might be available to multiple classes

#### 3.3 Skill Prerequisites
- **Perk Prerequisites**: Some skills require specific perks
- **Rank Prerequisites**: Some skills unlock at certain ranks of other skills
- **Level Prerequisites**: Some skills unlock at certain levels

### Phase 4: Expanded Content

#### 4.1 New Skills (Examples)

**Warrior Skills**:
- `cleave`: Attack multiple adjacent enemies (1.2x damage each)
- `taunt`: Force enemy to target you for 2 turns
- `fury`: +50% damage, -25% defense for 3 turns
- `shield_wall`: +2 defense for all allies for 2 turns
- `charge`: Move to enemy and attack (1.3x damage)

**Rogue Skills**:
- `backstab`: 2.0x damage if attacking from behind (requires positioning)
- `shadow_strike`: Teleport behind enemy and attack (1.5x damage)
- `poison_blade`: Apply poison on next 3 attacks
- `evade`: Next attack against you misses
- `stealth`: Invisible for 2 turns (enemies can't target you)

**Mage Skills**:
- `fireball`: 1.8x damage, applies burn DoT
- `lightning_bolt`: 1.6x damage, chains to nearby enemies
- `slow`: Target takes 2x turns to act for 3 turns
- `haste`: +50% speed for 3 turns
- `magic_shield`: Absorb next 20 damage

**Universal Skills**:
- `second_wind`: Restore 30% HP and stamina
- `adrenaline`: Next skill has no cooldown
- `analyze`: Reveal enemy stats/weaknesses

#### 4.2 New Perks (Examples)

**Warrior Perks**:
- `weapon_mastery_4`: +3 attack, unlocks cleave
- `iron_will`: +20% status resist
- `battle_rage`: +10% damage when below 50% HP
- `shield_expert`: Shield bash stuns for 2 turns instead of 1

**Rogue Perks**:
- `assassin_training`: +15% crit chance, unlocks backstab
- `poison_mastery`: Poison damage +50%
- `shadow_adept`: Stealth duration +1 turn
- `nimble_mind`: +10% dodge chance

**Mage Perks**:
- `arcane_power`: +25% skill_power, unlocks fireball
- `mana_efficiency`: All skills cost -2 mana
- `spell_focus`: Skills have -1 cooldown
- `elemental_mastery`: Elemental skills do +20% damage

#### 4.3 Perk Tree Expansion
- **More Branches**: Add 2-3 more branches per class
- **Deeper Trees**: 5-7 ranks per branch (currently 3)
- **Branch Capstones**: Powerful perks at the end of each branch
- **Cross-Branch**: Some perks require perks from multiple branches

### Phase 5: Scaling and Balance

#### 5.1 Skill Scaling
- **Power Scaling**: Skills scale with level and rank
  - Base: skill.base_power * (1 + 0.1 * rank)
  - Level scaling: Add level-based multiplier
- **Cooldown Scaling**: Higher ranks reduce cooldowns
- **Cost Scaling**: Higher ranks reduce costs
- **Status Scaling**: Status effects scale with rank

#### 5.2 Perk Scaling
- **Stat Bonuses**: Perks scale with level or remain flat
  - Option A: Flat bonuses (current system)
  - Option B: Percentage bonuses (scale with base stats)
  - Option C: Hybrid (flat + percentage)
- **Unlock Levels**: More perks unlock at higher levels
- **Power Curve**: Early perks weaker, late perks stronger

#### 5.3 Level Progression
- **Skill Points**: Grant rate increases with level
  - Formula: `1 + (level // 5)` points per level
  - Levels 1-4: 1 point per level
  - Levels 5-9: 2 points per level
  - Levels 10-14: 3 points per level
  - Levels 15-19: 4 points per level
  - Levels 20+: 5 points per level
- **Perk Selection**: More choices at higher levels (3 → 4 → 5)
- **Skill Unlocks**: More skills unlock at higher levels

## Implementation Plan

### Step 1: Core Data Structures
1. Add `skill_points: int` to `HeroStats` and `CompanionState` (default 0)
2. Add `skill_ranks: Dict[str, int]` to track skill levels (default empty dict)
3. Add `max_rank: int = 5` to `Skill` dataclass
4. Add skill point granting on level up (formula: `1 + (level // 5)`)
5. Add `auto_allocate_skill_points: bool` setting for companions (default False, player can toggle)
6. Create helper functions for skill rank management

### Step 2: Skill Rank System
1. Implement rank calculation (power, cooldown, costs)
2. Add rank-based skill effects
3. Create skill upgrade cost calculation
4. Add validation (can upgrade check)

### Step 3: Skill Screen UI
1. Create `SkillScreen` scene class
2. Implement entity selection (hero/companions)
3. Implement skill list display
4. Implement skill details display
5. Implement upgrade interaction
6. Add to game's scene management

### Step 4: Class-Specific Filtering
1. Add `class_restrictions: List[str]` to Skill dataclass
2. Filter skills by class in skill screen
3. Update perk `grant_skills` to respect class
4. Test with different classes

### Step 5: Content Expansion
1. Add 5-10 new skills per class
2. Add 10-15 new perks per class
3. Create skill trees/branches visually
4. Balance numbers

### Step 6: Polish and Balance
1. Playtest skill progression
2. Adjust skill point rates
3. Balance skill costs
4. Adjust skill power scaling
5. Add tooltips and help text

## Technical Considerations

### Data Storage
- **Save Compatibility**: Ensure old saves work (skill_ranks defaults to empty dict)
- **Migration**: If needed, migrate old saves to new format
- **Performance**: Skill rank lookups should be fast (dict is O(1))

### UI/UX
- **Visual Design**: Make skill screen visually appealing
- **Accessibility**: Keyboard navigation, clear indicators
- **Feedback**: Show stat changes when upgrading
- **Preview**: Show "what if" when hovering over upgrades

### Balance
- **Power Curve**: Ensure skills/perks scale appropriately
- **Choice Meaning**: Make skill point allocation meaningful
- **Build Diversity**: Encourage different builds per class
- **Companion AI**: Consider how companions use upgraded skills

## Future Enhancements

1. **Visual Skill Tree**: Graph-based visualization of skill trees
2. **Skill Presets**: Save/load skill point allocations
3. **Skill Synergies**: Skills that combo together
4. **Skill Mastery**: Bonus effects at max rank
5. **Respec System**: Allow refunding skill points (costs gold?)
6. **Skill Challenges**: Unlock skills through gameplay, not just perks
7. **Legendary Skills**: Ultra-rare powerful skills
8. **Skill Modifiers**: Items that modify skill behavior

## Decisions Made

1. **Skill Point Rate**: `1 + (level // 5)` points per level (scales: 1→2→3→4→5)
2. **Max Rank**: 5 ranks per skill ✅
3. **Upgrade Costs**: 1, 2, 3, 4, 5 points per rank (15 total to max) ✅
4. **Companion AI**: Toggleable option - player can choose auto-allocate or manual ✅
5. **Skill Unlocks**: Via perks and level milestones ✅
6. **Cross-Class Skills**: 3-5 core universal skills
7. **Visual Style**: Start with list, evolve to tree later

## Files to Create/Modify

### New Files:
- `engine/skill_screen.py` - Skill allocation screen
- `systems/skill_ranks.py` - Skill rank calculation logic (optional, could be in skills.py)

### Modified Files:
- `systems/skills.py` - Add max_rank, rank calculation
- `systems/progression.py` - Add skill_points, skill_ranks to HeroStats
- `systems/party.py` - Add skill_points, skill_ranks to CompanionState
- `systems/perks.py` - Expand perk trees, add class-specific perks
- `engine/game.py` - Grant skill points on level up, integrate skill screen
- `ui/hud_exploration.py` - Add skill screen access (key binding)

### Optional Files:
- `data/skills.json` - Move skill definitions to JSON (future)
- `data/perks.json` - Move perk definitions to JSON (future)

## Success Criteria

1. ✅ Players can allocate skill points to improve skills
2. ✅ Skill screen is accessible and intuitive
3. ✅ Skills scale meaningfully with ranks
4. ✅ Different classes have distinct skill options
5. ✅ Companions can have upgraded skills
6. ✅ System feels balanced and rewarding
7. ✅ Enough content (skills/perks) to fill out trees
8. ✅ System scales well from level 1 to max level

