# Skill Implementation Priority & Quick Reference

## Top 4 Skills to Implement First

These provide the most tactical value with reasonable implementation complexity.

### 1. **Expose Weakness** (Rogue) - Key: X
**Why First**: 
- Simple implementation (just apply vulnerable status)
- High tactical value (setup for big damage)
- Great synergy with existing skills

**Status**: `vulnerable` (incoming_mult=1.25, duration=3)

**Implementation Complexity**: ⭐ Low
- Just needs vulnerable status to work in damage calculation

---

### 2. **Crippling Strike** (Warrior) - Key: H
**Why Second**:
- Control option warriors lack
- Uses slow status (needs movement multiplier implementation)
- Fits warrior theme perfectly

**Status**: `slow` (movement_points_multiplier=0.5, duration=2)

**Implementation Complexity**: ⭐⭐ Medium
- Requires movement multiplier system

---

### 3. **Iron Skin** (Warrior) - Key: Z
**Why Third**:
- Alternative defensive option to guard
- Longer duration, longer cooldown
- Simple implementation

**Status**: `protected` (incoming_mult=0.7, duration=3)

**Implementation Complexity**: ⭐ Low
- Just needs protected status in damage calculation

---

### 4. **Disarm** (Rogue) - Key: C
**Why Fourth**:
- Counter to guard-heavy enemies
- Tactical option
- Requires exposed status check in guard skill

**Status**: `exposed` (duration=2, prevents guard)

**Implementation Complexity**: ⭐⭐ Medium
- Requires guard skill to check for exposed status

---

## Implementation Order

### Phase 1: Simple Status Effects (No System Changes)
1. **Expose Weakness** - Uses vulnerable (just multiplier)
2. **Iron Skin** - Uses protected (just multiplier)

**System Changes Needed**:
- Add vulnerable/protected to damage calculation in `BattleCombat.apply_damage()`

### Phase 2: Movement Modifiers
3. **Crippling Strike** - Uses slow (needs movement system)

**System Changes Needed**:
- Add `movement_points_multiplier` to StatusEffect
- Modify movement point calculation to check statuses
- Update `_on_unit_turn_start()` to calculate effective movement

### Phase 3: Status Checks
4. **Disarm** - Uses exposed (needs guard check)

**System Changes Needed**:
- Add exposed check in guard skill handler
- Or: Add `can_guard` property check

---

## Quick Implementation Checklist

### For Vulnerable/Protected:
- [ ] Add status definitions to `ui/status_display.py` (already done)
- [ ] Modify `BattleCombat.apply_damage()` to check for vulnerable/protected
- [ ] Create Expose Weakness skill
- [ ] Create Iron Skin skill
- [ ] Test damage multipliers work correctly

### For Slow:
- [ ] Add `movement_points_multiplier` field to StatusEffect
- [ ] Add helper function to calculate effective movement points
- [ ] Modify turn start to apply movement multipliers
- [ ] Create Crippling Strike skill
- [ ] Test movement reduction works

### For Exposed:
- [ ] Add exposed check in guard skill
- [ ] Create Disarm skill
- [ ] Test guard is blocked when exposed

---

## Code Examples

### Vulnerable in Damage Calculation

```python
# In engine/battle/combat.py, BattleCombat.apply_damage():
# After calculating base damage, before defense:

# Check for vulnerable status (takes more damage)
if self.scene._has_status(target, "vulnerable"):
    vulnerable_status = next(s for s in target.statuses if s.name == "vulnerable")
    damage = int(damage * vulnerable_status.incoming_mult)

# Check for protected status (takes less damage)  
if self.scene._has_status(target, "protected"):
    protected_status = next(s for s in target.statuses if s.name == "protected")
    damage = int(damage * protected_status.incoming_mult)
```

### Movement Multiplier

```python
# In systems/statuses.py:
@dataclass
class StatusEffect:
    # ... existing fields ...
    movement_points_multiplier: float = 1.0

# In engine/scenes/battle_scene.py, _on_unit_turn_start():
def _on_unit_turn_start(self, unit: BattleUnit) -> None:
    # ... existing code ...
    
    # Calculate effective movement points (check for haste/slow)
    base_mp = unit.max_movement_points
    movement_mult = 1.0
    for status in unit.statuses:
        mult = getattr(status, "movement_points_multiplier", 1.0)
        movement_mult *= mult
    unit.current_movement_points = int(base_mp * movement_mult)
```

### Exposed Check in Guard

```python
# In battle_scene._use_skill() or guard handler:
if skill_id == "guard":
    if self._has_status(unit, "exposed"):
        self._log(f"{unit.name} is exposed and cannot guard!")
        return
    # ... continue with guard ...
```

---

## Testing Plan

### For Each Skill:

1. **Status Application**:
   - Use skill, verify status appears
   - Check status icon displays correctly
   - Verify timer counts down

2. **Status Effect**:
   - Vulnerable: Take damage, verify 25% increase
   - Protected: Take damage, verify 30% reduction
   - Slow: Try to move, verify reduced movement
   - Exposed: Try to guard, verify it's blocked

3. **Status Interaction**:
   - Vulnerable + Protected: Should cancel out (1.25 * 0.7 = 0.875)
   - Multiple sources: Should refresh, not stack
   - Status expiration: Should remove correctly

4. **Skill Balance**:
   - Cooldown timing
   - Resource costs
   - Damage/effect strength

---

## Next Steps After Top 4

### Phase 4: More Player Skills
5. **Adrenaline Rush** (Rogue) - Haste self-buff
6. **Frost Bolt** (Mage) - Slow debuff
7. **Cleanse** (Mage) - Warded self-buff

### Phase 5: Enemy Skills
8. Enemy versions of vulnerable, slow, protected
9. Enemy warded skills for casters

### Phase 6: Advanced
10. AoE status skills
11. Multi-status skills
12. Status removal skills
