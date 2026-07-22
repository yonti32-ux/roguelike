# New Skills with New Status Types - Summary

## Quick Overview

We've identified **4 high-priority skills** to implement that use the new status types:

1. **Expose Weakness** (Rogue, X key) - Applies `vulnerable` (+25% damage taken)
2. **Crippling Strike** (Warrior, H key) - Applies `slow` (reduced movement)
3. **Iron Skin** (Warrior, Z key) - Applies `protected` (-30% damage taken)
4. **Disarm** (Rogue, C key) - Applies `exposed` (cannot guard)

---

## Status Types Ready to Use

✅ **Already Defined in `ui/status_display.py`**:
- `vulnerable` - Takes increased damage
- `protected` - Takes reduced damage
- `slow` - Reduced movement
- `haste` - Increased movement
- `exposed` - Cannot guard
- `warded` - Immune to debuffs
- `empowered` - Increased damage output (already used in buff_ally)

---

## Implementation Roadmap

### Step 1: Extend StatusEffect (Required for all)

Add new fields to `systems/statuses.py`:

```python
@dataclass
class StatusEffect:
    # ... existing fields ...
    movement_points_multiplier: float = 1.0  # For haste/slow
    # Note: vulnerable/protected use existing incoming_mult
    # Note: exposed/warded need special checks (not just multipliers)
```

### Step 2: Implement Vulnerable/Protected (Easiest)

**Files to Modify**:
- `engine/battle/combat.py` - Add vulnerable/protected checks in `apply_damage()`

**Skills to Add**:
- Expose Weakness (Rogue)
- Iron Skin (Warrior)

**Complexity**: ⭐ Low - Just multiplier checks

### Step 3: Implement Movement Modifiers

**Files to Modify**:
- `engine/scenes/battle_scene.py` - Modify `_on_unit_turn_start()` to calculate effective movement

**Skills to Add**:
- Crippling Strike (Warrior)

**Complexity**: ⭐⭐ Medium - Requires movement system changes

### Step 4: Implement Exposed Check

**Files to Modify**:
- `engine/scenes/battle_scene.py` - Add exposed check in guard skill handler

**Skills to Add**:
- Disarm (Rogue)

**Complexity**: ⭐⭐ Medium - Requires guard skill modification

---

## Detailed Skill Definitions

### Expose Weakness (Rogue)
```python
expose_weakness = register(
    Skill(
        id="expose_weakness",
        name="Expose Weakness",
        description="Strike that exposes the target's weaknesses, making them take 25% more damage for 3 turns.",
        key=pygame.K_x,
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

### Crippling Strike (Warrior)
```python
crippling_strike = register(
    Skill(
        id="crippling_strike",
        name="Crippling Strike",
        description="Heavy blow that slows the target for 2 turns.",
        key=pygame.K_h,
        target_mode="adjacent_enemy",
        base_power=1.3,
        uses_skill_power=False,
        cooldown=4,
        stamina_cost=4,
        class_restrictions=["warrior"],
        make_target_status=lambda: StatusEffect(
            name="slow",
            duration=2,
            movement_points_multiplier=0.5,  # 50% movement
        ),
    )
)
```

### Iron Skin (Warrior)
```python
iron_skin = register(
    Skill(
        id="iron_skin",
        name="Iron Skin",
        description="Harden your skin, reducing incoming damage by 30% for 3 turns.",
        key=pygame.K_z,
        target_mode="self",
        base_power=0.0,
        uses_skill_power=False,
        cooldown=5,
        stamina_cost=4,
        class_restrictions=["warrior"],
        make_self_status=lambda: StatusEffect(
            name="protected",
            duration=3,
            incoming_mult=0.7,  # Takes 30% less damage
        ),
    )
)
```

### Disarm (Rogue)
```python
disarm = register(
    Skill(
        id="disarm",
        name="Disarm",
        description="Disarm the target, preventing them from using guard for 2 turns.",
        key=pygame.K_c,
        target_mode="adjacent_enemy",
        base_power=0.8,
        uses_skill_power=False,
        cooldown=5,
        stamina_cost=3,
        class_restrictions=["rogue"],
        make_target_status=lambda: StatusEffect(
            name="exposed",
            duration=2,
            # No multiplier - special check needed
        ),
    )
)
```

---

## System Modifications Required

### 1. StatusEffect Extension

**File**: `systems/statuses.py`

```python
@dataclass
class StatusEffect:
    name: str
    duration: int
    stacks: int = 1
    outgoing_mult: float = 1.0
    incoming_mult: float = 1.0
    flat_damage_each_turn: int = 0
    stunned: bool = False
    movement_points_multiplier: float = 1.0  # NEW: For haste/slow
```

### 2. Damage Calculation (Vulnerable/Protected)

**File**: `engine/battle/combat.py`

```python
# In BattleCombat.apply_damage(), after calculating base damage:

# Check for vulnerable status (takes more damage)
vulnerable_status = next((s for s in target.statuses if s.name == "vulnerable"), None)
if vulnerable_status:
    damage = int(damage * vulnerable_status.incoming_mult)

# Check for protected status (takes less damage)
# Note: This should apply AFTER vulnerable (multiplicative)
protected_status = next((s for s in target.statuses if s.name == "protected"), None)
if protected_status:
    damage = int(damage * protected_status.incoming_mult)
```

### 3. Movement Points Calculation (Haste/Slow)

**File**: `engine/scenes/battle_scene.py`

```python
# In _on_unit_turn_start(), after resetting movement points:

# Calculate effective movement points (check for haste/slow)
base_mp = unit.max_movement_points
movement_mult = 1.0
for status in unit.statuses:
    mult = getattr(status, "movement_points_multiplier", 1.0)
    movement_mult *= mult
unit.current_movement_points = int(base_mp * movement_mult)
```

### 4. Guard Check (Exposed)

**File**: `engine/scenes/battle_scene.py`

```python
# In _use_skill() or guard skill handler:
if skill_id == "guard":
    if self._has_status(unit, "exposed"):
        self._log(f"{unit.name} is exposed and cannot guard!")
        return
    # ... continue with normal guard logic ...
```

### 5. Warded Check (For Future)

**File**: `engine/scenes/battle_scene.py`

```python
# In _add_status(), before applying status:
if self._has_status(unit, "warded"):
    from ui.status_display import get_status_display_info
    info = get_status_display_info(status)
    if not info["is_buff"]:  # It's a debuff
        self._log(f"{unit.name} is warded and resists {status.name}!")
        return
```

---

## Testing Checklist

### For Each Skill:

- [ ] Skill appears in skill list for correct class
- [ ] Key binding works
- [ ] Status applies correctly
- [ ] Status icon displays with timer
- [ ] Status effect works (damage/movement/guard)
- [ ] Status expires correctly
- [ ] Cooldown works
- [ ] Resource cost works
- [ ] Status refreshes (doesn't stack)

### Integration Tests:

- [ ] Vulnerable + Protected cancel out correctly
- [ ] Slow reduces movement appropriately
- [ ] Exposed prevents guard
- [ ] Multiple statuses display correctly
- [ ] Status tooltips work (when implemented)

---

## Balance Notes

### Status Strengths:
- **Vulnerable**: +25% damage (strong but not overwhelming)
- **Protected**: -30% damage (stronger than guard, longer cooldown)
- **Slow**: 50% movement (significant but not crippling)
- **Exposed**: Prevents guard (very strong, short duration)

### Cooldown Rationale:
- **Expose Weakness**: 4 turns (setup skill, moderate cooldown)
- **Crippling Strike**: 4 turns (control skill, moderate cooldown)
- **Iron Skin**: 5 turns (defensive skill, longer cooldown than guard)
- **Disarm**: 5 turns (tactical skill, longer cooldown)

### Resource Costs:
- **Expose Weakness**: 3 stamina (moderate)
- **Crippling Strike**: 4 stamina (higher, more damage)
- **Iron Skin**: 4 stamina (higher, defensive)
- **Disarm**: 3 stamina (moderate, utility)

---

## Next Steps

1. **Review this document** - Confirm skill designs
2. **Extend StatusEffect** - Add movement_points_multiplier
3. **Implement vulnerable/protected** - Easiest first
4. **Add Expose Weakness & Iron Skin** - Test basic statuses
5. **Implement movement modifiers** - Add slow support
6. **Add Crippling Strike** - Test movement system
7. **Implement exposed check** - Add guard prevention
8. **Add Disarm** - Test exposed system
9. **Balance & iterate** - Adjust based on playtesting

---

## References

- `docs/NEW_SKILLS_PROPOSAL.md` - Full skill proposals
- `docs/SKILL_IMPLEMENTATION_PRIORITY.md` - Detailed implementation guide
- `docs/STATUS_TOOLTIPS_AND_EXPANSION.md` - Status system improvements
- `ui/status_display.py` - Status display definitions
