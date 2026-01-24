# New Skills Proposal - Using New Status Types

## Overview

This document proposes new skills that utilize the recently added status effect types:
- `haste` - Increased movement
- `slow` - Reduced movement speed  
- `vulnerable` - Takes increased damage
- `protected` - Reduced incoming damage
- `exposed` - Cannot guard or defend
- `warded` - Immune to debuffs

---

## Current Player Skills (Reference)

**Available to All:**
- `guard` (G) - Defensive, 50% damage reduction
- `power_strike` (Q) - Offensive, weakens target

**Class-Specific:**
- `lunge` (R) - Rogue mobility
- `shield_bash` (E) - Warrior stun
- `focus_blast` (F) - Mage skill power
- `nimble_step` (T) - Rogue defensive
- `whirlwind` - Warrior AoE
- `smoke_bomb` - Rogue AoE weaken
- And more...

---

## Proposed New Skills

### 1. **Haste Skills**

#### **Adrenaline Rush** (Player - Rogue)
- **Key**: `pygame.K_h` (or available slot)
- **Description**: "Boost your movement speed for 3 turns. Move further each turn."
- **Target**: Self
- **Status**: `haste` (duration 3, increases movement points)
- **Cooldown**: 4
- **Stamina Cost**: 3
- **Class**: Rogue
- **Power**: 0.0 (utility skill)
- **Notes**: Could increase `max_movement_points` or movement efficiency

#### **Swift Strike** (Player - Rogue)
- **Key**: Available slot
- **Description**: "Quick attack that grants haste for 2 turns."
- **Target**: Adjacent enemy
- **Power**: 1.2x
- **Status**: Self gets `haste` (duration 2)
- **Cooldown**: 3
- **Stamina Cost**: 2
- **Class**: Rogue
- **Synergy**: Mobility-focused build

#### **Haste Spell** (Enemy - Caster Archetype)
- **Description**: "Enemy buffs itself with increased movement."
- **Target**: Self
- **Status**: `haste` (duration 3)
- **Cooldown**: 5
- **AI-only**: Yes
- **Notes**: Makes casters more mobile and dangerous

---

### 2. **Slow Skills**

#### **Crippling Strike** (Player - Warrior)
- **Key**: Available slot
- **Description**: "Heavy blow that slows the target for 2 turns."
- **Target**: Adjacent enemy
- **Power**: 1.3x
- **Status**: Target gets `slow` (duration 2, reduces movement points)
- **Cooldown**: 4
- **Stamina Cost**: 4
- **Class**: Warrior
- **Synergy**: Control-focused, pairs with AoE skills

#### **Frost Bolt** (Player - Mage)
- **Key**: Available slot
- **Description**: "Ice attack that slows the target for 3 turns."
- **Target**: Adjacent enemy
- **Power**: 1.1x (uses skill power)
- **Status**: Target gets `slow` (duration 3)
- **Cooldown**: 3
- **Mana Cost**: 2
- **Class**: Mage
- **Notes**: Lower damage but longer slow duration

#### **Slow Field** (Enemy - Caster)
- **Description**: "Enemy creates a slowing field, reducing movement of nearby units."
- **Target**: AoE (radius 1)
- **Status**: Targets get `slow` (duration 2)
- **Cooldown**: 5
- **AI-only**: Yes
- **Notes**: Area control skill

---

### 3. **Vulnerable Skills**

#### **Expose Weakness** (Player - Rogue)
- **Key**: Available slot
- **Description**: "Strike that exposes the target's weaknesses, making them take 25% more damage for 3 turns."
- **Target**: Adjacent enemy
- **Power**: 1.0x (lower damage, but sets up for big hits)
- **Status**: Target gets `vulnerable` (duration 3, incoming_mult=1.25)
- **Cooldown**: 4
- **Stamina Cost**: 3
- **Class**: Rogue
- **Synergy**: Great setup skill, pairs with high-damage skills

#### **Marked for Death** (Player - All Classes)
- **Key**: Available slot
- **Description**: "Mark the target, making them take 20% more damage for 4 turns."
- **Target**: Adjacent enemy
- **Power**: 0.8x (weaker attack, but strong debuff)
- **Status**: Target gets `vulnerable` (duration 4, incoming_mult=1.2)
- **Cooldown**: 5
- **Stamina Cost**: 2
- **Class**: None (all classes)
- **Notes**: Utility skill, good for boss fights

#### **Curse** (Enemy - Caster)
- **Description**: "Enemy curses you, making you take more damage."
- **Target**: Adjacent enemy
- **Power**: 0.5x
- **Status**: Target gets `vulnerable` (duration 3, incoming_mult=1.3)
- **Cooldown**: 4
- **AI-only**: Yes
- **Notes**: Dangerous debuff from casters

---

### 4. **Protected Skills**

#### **Iron Skin** (Player - Warrior)
- **Key**: Available slot
- **Description**: "Harden your skin, reducing incoming damage by 30% for 3 turns."
- **Target**: Self
- **Status**: `protected` (duration 3, incoming_mult=0.7)
- **Cooldown**: 5
- **Stamina Cost**: 4
- **Class**: Warrior
- **Notes**: Stronger than guard but longer cooldown

#### **Protective Ward** (Player - Mage)
- **Key**: Available slot
- **Description**: "Create a protective ward, reducing incoming damage by 25% for 4 turns."
- **Target**: Self
- **Status**: `protected` (duration 4, incoming_mult=0.75)
- **Cooldown**: 6
- **Mana Cost**: 3
- **Class**: Mage
- **Notes**: Longer duration, uses mana instead of stamina

#### **Defensive Stance** (Enemy - Tank Archetype)
- **Description**: "Enemy enters defensive stance, reducing incoming damage."
- **Target**: Self
- **Status**: `protected` (duration 2, incoming_mult=0.7)
- **Cooldown**: 4
- **AI-only**: Yes
- **Notes**: Makes tank enemies harder to kill

---

### 5. **Exposed Skills**

#### **Disarm** (Player - Rogue)
- **Key**: Available slot
- **Description**: "Disarm the target, preventing them from using guard or defensive skills for 2 turns."
- **Target**: Adjacent enemy
- **Power**: 0.8x
- **Status**: Target gets `exposed` (duration 2, cannot guard)
- **Cooldown**: 5
- **Stamina Cost**: 3
- **Class**: Rogue
- **Notes**: Counter to defensive enemies, prevents guard usage

#### **Shatter Guard** (Player - Warrior)
- **Key**: Available slot
- **Description**: "Shatter the target's defenses, making them unable to guard for 3 turns."
- **Target**: Adjacent enemy
- **Power**: 1.2x
- **Status**: Target gets `exposed` (duration 3)
- **Cooldown**: 6
- **Stamina Cost**: 5
- **Class**: Warrior
- **Notes**: Stronger version, longer duration

#### **Armor Break** (Enemy - Brute)
- **Description**: "Enemy breaks your guard, preventing defensive skills."
- **Target**: Adjacent enemy
- **Power**: 1.0x
- **Status**: Target gets `exposed` (duration 2)
- **Cooldown**: 4
- **AI-only**: Yes
- **Notes**: Dangerous for players relying on guard

---

### 6. **Warded Skills**

#### **Cleanse** (Player - Mage)
- **Key**: Available slot
- **Description**: "Cleanse yourself, becoming immune to debuffs for 2 turns."
- **Target**: Self
- **Status**: `warded` (duration 2, immune to debuffs)
- **Cooldown**: 6
- **Mana Cost**: 4
- **Class**: Mage
- **Notes**: Counter to debuff-heavy enemies

#### **Ward** (Player - All Classes)
- **Key**: Available slot
- **Description**: "Ward yourself against debuffs for 3 turns."
- **Target**: Self
- **Status**: `warded` (duration 3)
- **Cooldown**: 8
- **Stamina Cost**: 3
- **Class**: None (all classes)
- **Notes**: Utility skill, situational but powerful

#### **Magic Shield** (Enemy - Caster)
- **Description**: "Enemy creates a magic shield, becoming immune to debuffs."
- **Target**: Self
- **Status**: `warded` (duration 2)
- **Cooldown**: 5
- **AI-only**: Yes
- **Notes**: Makes casters harder to debuff

---

## Skill Combinations & Synergies

### Player Combos:

1. **Expose → Power Strike**: 
   - Use Expose Weakness, then follow with Power Strike
   - Vulnerable + Weakened = massive damage reduction on enemy

2. **Haste → Mobility Build**:
   - Adrenaline Rush + Lunge + Swift Strike
   - High mobility, hit-and-run tactics

3. **Disarm → Focus Fire**:
   - Disarm enemy, then unload with high-damage skills
   - Prevents enemy from guarding

4. **Ward → Debuff Protection**:
   - Use Ward before fighting debuff-heavy enemies
   - Prevents poison, weaken, stun, etc.

### Enemy Combos:

1. **Slow → Vulnerable → Attack**:
   - Enemy slows you, makes you vulnerable, then attacks
   - Dangerous combo

2. **Protected → Tank**:
   - Tank enemies use Protected, become very hard to kill
   - Requires Expose or high damage

---

## Implementation Priority

### Phase 1: High-Impact Player Skills
1. **Expose Weakness** (Rogue) - Great setup skill
2. **Crippling Strike** (Warrior) - Control option
3. **Iron Skin** (Warrior) - Defensive option
4. **Disarm** (Rogue) - Counter to guards

### Phase 2: Utility & Support
5. **Adrenaline Rush** (Rogue) - Mobility build
6. **Cleanse** (Mage) - Debuff protection
7. **Marked for Death** (All) - Universal utility

### Phase 3: Enemy Skills
8. Enemy versions of vulnerable, slow, protected
9. Enemy warded skills for casters

### Phase 4: Advanced
10. AoE versions of status skills
11. Multi-status skills (e.g., slow + vulnerable)

---

## Balance Considerations

### Status Duration Guidelines:
- **Short (1-2 turns)**: Strong effects (exposed, warded)
- **Medium (2-3 turns)**: Standard effects (vulnerable, slow, haste)
- **Long (3-4 turns)**: Weaker effects (protected)

### Status Strength Guidelines:
- **Vulnerable**: +20-30% incoming damage (strong but not overwhelming)
- **Protected**: -25-30% incoming damage (stronger than guard but longer cooldown)
- **Slow**: -50% movement points (significant but not crippling)
- **Haste**: +50% movement points (significant mobility boost)
- **Exposed**: Prevents guard (very strong, short duration)
- **Warded**: Immune to debuffs (very strong, short duration)

### Cooldown Guidelines:
- **Utility skills** (haste, ward, cleanse): 4-6 turns
- **Debuff skills** (slow, vulnerable, exposed): 4-5 turns
- **Defensive skills** (protected): 5-6 turns
- **Offensive + status**: 3-4 turns

---

## Technical Implementation Notes

### Status Effect Definitions Needed:

```python
# In systems/statuses.py or skills.py
StatusEffect(
    name="haste",
    duration=3,
    # Would need to modify movement system to check for haste
    # Could add movement_points_multiplier field
)

StatusEffect(
    name="slow",
    duration=2,
    # Would need movement_points_multiplier = 0.5
)

StatusEffect(
    name="vulnerable",
    duration=3,
    incoming_mult=1.25,  # Takes 25% more damage
)

StatusEffect(
    name="protected",
    duration=3,
    incoming_mult=0.7,  # Takes 30% less damage
)

StatusEffect(
    name="exposed",
    duration=2,
    # Would need to check in guard skill if exposed
    # Could add can_guard field or check status
)

StatusEffect(
    name="warded",
    duration=2,
    # Would need to check in status application if warded
    # Could add immune_to_debuffs field
)
```

### System Modifications Needed:

1. **Movement System**: 
   - Check for `haste`/`slow` statuses
   - Modify movement points calculation

2. **Guard System**:
   - Check for `exposed` status
   - Prevent guard if exposed

3. **Status Application**:
   - Check for `warded` status
   - Block debuff application if warded

4. **Combat System**:
   - Apply `vulnerable` multiplier in damage calculation
   - Apply `protected` multiplier in damage calculation

---

## Example Skill Implementation

```python
# Expose Weakness (Rogue skill)
expose_weakness = register(
    Skill(
        id="expose_weakness",
        name="Expose Weakness",
        description="Strike that exposes the target's weaknesses, making them take 25% more damage for 3 turns.",
        key=pygame.K_x,  # Example key
        target_mode="adjacent_enemy",
        base_power=1.0,
        uses_skill_power=False,
        cooldown=4,
        stamina_cost=3,
        class_restrictions=["rogue"],
        make_target_status=lambda: StatusEffect(
            name="vulnerable",
            duration=3,
            incoming_mult=1.25,  # Takes 25% more damage
        ),
    )
)
```

---

## Implementation Details

### Movement Modifiers (Haste/Slow)

**Recommended Approach**: Add `movement_points_multiplier` field to StatusEffect

```python
# In systems/statuses.py
@dataclass
class StatusEffect:
    # ... existing fields ...
    movement_points_multiplier: float = 1.0  # 1.5 for haste, 0.5 for slow
```

**Implementation**:
- Modify `BattleUnit.max_movement_points` calculation to check statuses
- In `_on_unit_turn_start()` or movement reset, calculate effective max movement
- Formula: `effective_mp = base_mp * product(all movement multipliers)`

**Example**:
```python
def get_effective_movement_points(unit: BattleUnit) -> int:
    base_mp = unit.max_movement_points
    mult = 1.0
    for status in unit.statuses:
        mult *= getattr(status, "movement_points_multiplier", 1.0)
    return int(base_mp * mult)
```

### Exposed Implementation

**Recommended Approach**: Check status in guard skill before applying

```python
# In battle_scene._use_skill() or guard skill handler:
if self._has_status(unit, "exposed"):
    self._log(f"{unit.name} is exposed and cannot guard!")
    return
```

### Warded Implementation

**Recommended Approach**: Check in `_add_status` before applying debuffs

```python
# In battle_scene._add_status():
# Check if target is warded and this is a debuff
if self._has_status(unit, "warded"):
    info = get_status_display_info(status)
    if not info["is_buff"]:  # It's a debuff
        self._log(f"{unit.name} is warded and resists {status.name}!")
        return
```

### Status Stacking

**Recommendation**: 
- **Vulnerable/Protected**: Refresh duration, don't stack (same as guard/weakened)
- **Haste/Slow**: Could stack multiplicatively (haste + slow = neutral)
- **Exposed/Warded**: Refresh duration, don't stack

### Key Bindings

**Currently Used**: G, Q, R, E, F, T
**Recommended New Assignments**:
- H = Crippling Strike (Warrior)
- X = Expose Weakness (Rogue)  
- Z = Iron Skin (Warrior)
- C = Disarm (Rogue)
- V = Adrenaline Rush (Rogue) - if implemented
- B = Frost Bolt (Mage) - if implemented

---

## Recommended Starting Skills

**For Immediate Implementation:**

1. **Expose Weakness** (Rogue, key=X)
   - Simple, high impact
   - Good synergy with existing skills
   - Uses `vulnerable` status

2. **Crippling Strike** (Warrior, key=H)
   - Control option
   - Fits warrior theme
   - Uses `slow` status

3. **Iron Skin** (Warrior, key=Z)
   - Defensive option
   - Alternative to guard
   - Uses `protected` status

4. **Disarm** (Rogue, key=C)
   - Counter to guards
   - Tactical option
   - Uses `exposed` status

These four provide:
- New tactical options
- Class variety
- Synergies with existing skills
- Use of new status types

---

## Key Binding Analysis

**Currently Used:**
- G = Guard
- Q = Power Strike
- R = Lunge
- E = Shield Bash
- F = Focus Blast
- T = Nimble Step

**Available Keys:**
- H, X, Z, C, V, B, N, M
- 1, 2, 3, 4, 5, 6, 7, 8, 9, 0
- Left/Right brackets: [, ]

**Recommended Assignments:**
- H = Crippling Strike (Warrior)
- X = Expose Weakness (Rogue)
- Z = Iron Skin (Warrior)
- C = Disarm (Rogue)
- V = Adrenaline Rush (Rogue) - if implemented
- B = Frost Bolt (Mage) - if implemented
