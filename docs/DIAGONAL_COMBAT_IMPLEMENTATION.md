# Diagonal Combat & Reactions Implementation Summary

## Status: ✅ Implemented

Both **diagonal combat** and **reactions/attacks of opportunity** have been fully implemented in the game!

---

## Diagonal Movement & Attacks

### What's Implemented

1. **8-Directional Movement**
   - Pathfinding supports diagonal movement (`engine/battle/pathfinding.py`)
   - Diagonal movement costs 1.5x (configurable via `DIAGONAL_MOVEMENT_COST` in `settings.py`)
   - Chebyshev distance used for pathfinding heuristic

2. **8-Directional Attacks**
   - Melee weapons can attack diagonally (using Chebyshev distance)
   - Ranged weapons still use Manhattan distance (orthogonal only)
   - Flanking detection works with 8 directions

3. **Direct Keyboard Diagonal Input**
   - Players can press W+D, W+A, S+D, S+A for diagonal movement
   - Uses key state checking to detect simultaneous key presses
   - Works with both InputManager and direct key checks

### Key Files

- `engine/battle/pathfinding.py` - 8-directional A* pathfinding
- `engine/battle/combat.py` - Chebyshev distance for melee, flanking logic
- `engine/battle/ai.py` - AI uses 8-directional movement and Chebyshev distance
- `engine/scenes/battle_scene.py` - Diagonal keyboard input support (lines ~1950-2020)

### How It Works

- **Movement**: Diagonal moves cost 1.5x movement points (e.g., 1.5 MP instead of 1 MP)
- **Range Checks**: Melee uses `max(|dx|, |dy|)` (Chebyshev), ranged uses `|dx| + |dy|` (Manhattan)
- **Input**: Check `pygame.key.get_pressed()` or `InputManager.is_action_pressed()` to detect simultaneous keys

---

## Reactions / Attacks of Opportunity (AoO)

### What's Implemented

1. **Reaction System** (`engine/battle/reactions.py`)
   - Units can have reaction capabilities (granted by perks)
   - 1 reaction per turn (resets at start of turn)
   - Disengagement detection (leaving melee range)

2. **Attacks of Opportunity**
   - Triggers when unit moves from adjacent (distance 1) to non-adjacent (distance > 1)
   - Works with both orthogonal and diagonal disengagement
   - Deals 75% damage (less punishing than full attack)

3. **Sentinel Perk** (`systems/perks.py`)
   - Grants AoO capability
   - Unlocks at level 4
   - Requires `iron_guard_1` perk
   - Located in `ward` branch (defense tree)

### Key Files

- `engine/battle/reactions.py` - Complete reaction system
- `engine/battle/types.py` - BattleUnit has `reaction_capabilities` and `reactions_remaining`
- `engine/scenes/battle_scene.py` - Movement triggers disengagement checks (lines ~789-866)
- `systems/perks.py` - Sentinel perk definition (line ~313)

### How It Works

1. **Reaction Reset**: Each turn, units with reaction capabilities get 1 reaction point
2. **Disengagement Check**: Before movement, check if leaving melee range
3. **AoO Trigger**: If disengaging, all adjacent enemies with AoO capability can react
4. **Execution**: AoO deals 75% damage and consumes reaction point

### Example Flow

```
Turn starts:
  - Unit A has Sentinel perk → gets 1 reaction_remaining
  
Enemy moves:
  - Enemy was adjacent (distance 1) to Unit A
  - Enemy moves away (distance > 1)
  - check_disengagement() detects disengagement
  - execute_attack_of_opportunity() triggers
  - Unit A attacks for 75% damage
  - Unit A's reaction_remaining → 0
```

---

## Integration Points

### Movement & Reactions Together

1. **Diagonal Movement + AoO**:
   - Player can move diagonally to escape
   - But AoO can still trigger if disengaging from melee
   - More tactical: "Can I move diagonally to avoid AoO from one enemy but not another?"

2. **Tactical Depth**:
   - Diagonal movement = more positioning options
   - Reactions = more defensive/positioning concerns
   - Together = more dynamic, positionally-aware combat

### Turn System

- Reactions reset at start of turn: `reactions.reset_reactions(unit)` (called in `_on_unit_turn_start`)
- Movement checks disengagement: `reactions.check_disengagement()` called before actual movement
- AoO execute after movement: Reactions happen after the moving unit completes their move

---

## Testing Checklist

### Diagonal Movement
- [ ] Can move diagonally with keyboard (W+D, W+A, S+D, S+A)
- [ ] Diagonal movement costs 1.5x movement points
- [ ] Pathfinding finds diagonal paths correctly
- [ ] AI uses diagonal movement appropriately
- [ ] Can attack diagonally adjacent enemies

### Reactions
- [ ] Sentinel perk grants AoO capability
- [ ] Reactions reset at start of turn (1 per turn)
- [ ] AoO triggers on orthogonal disengagement
- [ ] AoO triggers on diagonal disengagement
- [ ] AoO deals 75% damage (not 100%)
- [ ] AoO consumes reaction point
- [ ] Can't make multiple AoOs per turn (only 1 reaction)

### Combined
- [ ] Moving diagonally away from enemy triggers AoO (if enemy has Sentinel)
- [ ] Diagonal positioning works correctly with flanking
- [ ] Movement mode pathfinding shows correct diagonal costs
- [ ] Combat log shows AoO messages correctly

---

## Configuration

### Settings (`settings.py`)

```python
DIAGONAL_MOVEMENT_COST = 1.5  # Diagonal movement costs 1.5x more
```

### Perk (`systems/perks.py`)

```python
Perk(
    id="sentinel",
    name="Sentinel",
    description="You can make attacks of opportunity when enemies leave your melee range. Deals 75% damage.",
    unlock_level=4,
    branch="ward",
    requires=["iron_guard_1"],
)
```

---

## Future Enhancements (Not Currently Implemented)

1. **More Reaction Types**:
   - Overwatch (react to movement in range)
   - Counter-Attack reactions (when being hit)
   - Intercept (protect ally from attack)

2. **Reaction UI Indicators**:
   - Show "Reaction Available" icon
   - Preview which enemies will trigger AoO
   - Visual feedback when AoO triggers

3. **Balance Tuning**:
   - Adjust AoO damage multiplier (currently 75%)
   - Adjust reaction point count (currently 1 per turn)
   - Consider making reactions universal vs perk-gated

---

## Notes

- Both systems are **optional/opt-in**: Diagonal movement is always available, but AoO requires Sentinel perk
- The implementation follows the recommendations from `COMBAT_FEATURE_ANALYSIS.md`
- Code is well-documented and follows existing patterns
- AI automatically benefits from diagonal movement and can use reactions if enemies have Sentinel

---

## References

- `docs/COMBAT_FEATURE_ANALYSIS.md` - Original feature analysis and recommendations
- `docs/IMPROVEMENT_SUGGESTIONS.md` - Part of "Core Gameplay" improvements

