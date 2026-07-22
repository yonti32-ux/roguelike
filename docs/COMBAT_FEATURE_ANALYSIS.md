# Combat Feature Analysis: Diagonal Attacks & Reactions

## Current Combat System Overview

### Movement & Positioning
- **4-directional movement only**: Units move North, South, East, West (no diagonals)
- **Manhattan distance**: All range checks use `abs(dx) + abs(dy)`
- **Melee range**: 1 tile (only directly adjacent orthogonally)
- **Ranged weapons**: Can have range > 1, still uses Manhattan distance
- **Pathfinding**: A* algorithm restricted to 4 directions

### Attack Mechanics
- **Basic attacks**: Check weapon range, must be within Manhattan distance
- **Flanking**: Only applies to melee attacks when no ally is directly opposite
- **Cover**: Reduces ranged damage when target is on cover terrain

### Turn Structure
- Turn-based with initiative
- Units can move and act in same turn
- No reactions/interrupts currently

---

## Feature 1: Diagonal Attacks

### What It Means
Allow units to attack enemies in diagonal positions (8 directions total instead of 4).

### Implementation Considerations

#### Option A: Diagonal Melee Attacks Only
- **Change**: Melee weapons can attack 8 directions (orthogonal + diagonal)
- **Range check**: Use Chebyshev distance (`max(|dx|, |dy|)`) for melee, Manhattan for ranged
- **Pros**:
  - More tactical positioning options
  - Easier to engage multiple enemies
  - Feels more natural for melee combat
- **Cons**:
  - Might make combat easier (more attack angles)
  - Could reduce importance of positioning
  - Inconsistent with current Manhattan-based system

#### Option B: Diagonal Movement + Diagonal Attacks
- **Change**: Allow both diagonal movement and diagonal attacks
- **Range check**: Use Chebyshev distance for both movement and melee attacks
- **Movement cost**: Diagonal movement could cost 1.5x (common in strategy games)
- **Pros**:
  - More fluid, natural-feeling movement
  - More tactical options
  - Modern standard for grid-based tactics games
- **Cons**:
  - Requires pathfinding rewrite (8-directional instead of 4)
  - Movement costs more complex
  - Larger code changes across battle system

#### Option C: Diagonal Attacks Only (No Diagonal Movement)
- **Change**: Movement stays 4-directional, attacks can be 8-directional
- **Pros**:
  - Smaller code impact (only combat calculations change)
  - Maintains current movement feel
- **Cons**:
  - Inconsistent/unintuitive (why can't you move diagonally but attack diagonally?)
  - Might feel clunky

### Impact Analysis

#### Balance Concerns
1. **Easier engagement**: Diagonal attacks make it harder to "corner" enemies
2. **Flanking changes**: Current flanking logic only checks orthogonal positions - would need adjustment
3. **Cover positioning**: Easier to find angles that avoid cover

#### Code Changes Required (Option B - Full 8-directional)
1. **Pathfinding** (`engine/battle/pathfinding.py`):
   - Change neighbor check from 4 to 8 directions
   - Adjust movement cost calculation for diagonals
   - Update heuristic to use Chebyshev distance

2. **AI** (`engine/battle/ai.py`):
   - `enemies_in_range()` uses Manhattan - switch to Chebyshev for melee
   - Update `step_towards()` to prefer diagonals when beneficial
   - Adjust flanking calculation logic

3. **Combat** (`engine/battle/combat.py`):
   - `_get_weapon_range()` distance checks need context (Chebyshev vs Manhattan)
   - Flanking detection needs to account for 8 directions

4. **UI/Rendering** (`engine/battle/renderer.py`):
   - Range visualization needs to show 8 directions for melee
   - Attack previews need updating

#### Code Changes Required (Option A - Diagonal Attacks Only)
- Similar to Option B but skip pathfinding changes
- Simpler, but feels inconsistent

### Recommendation
**Option B (Full 8-directional)** seems most natural, but requires careful balancing:
- Consider making diagonal movement cost 1.5x movement points
- Update flanking to work with 8 directions (maybe reduce flanking bonus slightly)
- Test extensively to ensure combat isn't too easy

---

## Feature 2: Reactions / Attacks of Opportunity

### What It Means
Units can react to enemy actions, particularly movement. Classic example: "Attack of Opportunity" when enemy moves away from melee.

### Common Reaction Types

#### 1. Attacks of Opportunity (AoO)
- **Trigger**: Enemy leaves melee range (disengage)
- **Effect**: Free attack on the moving enemy
- **Classic D&D mechanic**: Moving away from an engaged enemy provokes

#### 2. Counter-Attacks
- **Trigger**: Being attacked in melee
- **Effect**: Automatic counter-attack (reduced damage)
- **Note**: Already partially implemented with `counter_stance` status!

#### 3. Reactive Skills
- **Trigger**: Specific conditions (e.g., "when attacked", "when ally takes damage")
- **Effect**: Activate defensive/offensive skills automatically
- **Cost**: Usually costs stamina/mana, may have cooldowns

### Implementation Considerations

#### Option A: Simple Attacks of Opportunity
```python
# When unit moves away from adjacent enemy:
- Check if leaving melee range (distance goes from 1 to >1)
- All adjacent enemies get a reaction opportunity
- Each can choose to AoO (free attack) or pass
```

**Pros**:
- Prevents "kiting" (moving in and out of range freely)
- Adds tactical depth to positioning
- Classic mechanic players understand

**Cons**:
- Could make movement feel "punishing"
- Might slow down combat (extra attacks each turn)
- Need to prevent infinite loops (AoO triggering AoO?)

#### Option B: Full Reaction System
```python
# Reaction points per turn (e.g., 1 reaction per turn)
# Various triggers:
- Disengagement (AoO)
- Being attacked (counter/parry)
- Ally takes damage (intercept/protect)
- Enemy casts spell (interrupt)
```

**Pros**:
- Very flexible and expandable
- Supports many tactical options
- More strategic depth

**Cons**:
- More complex to implement
- Harder to balance
- UI complexity (how to show reaction opportunities?)

#### Option C: Conditional Reactions
```python
# Only certain units/skills grant reactions
- "Sentinel" perk: Grants AoO
- "Counter-attack" skill: Active ability that triggers on being hit
- "Defensive Stance": Status that grants reactions
```

**Pros**:
- Not universally available (more balanced)
- Can be gated behind perks/skills
- Rewards specialization

**Cons**:
- Might feel inconsistent (why does this enemy get AoO but not that one?)
- Requires clear visual/UI indicators

### Balance & Gameplay Impact

#### Positive Impacts
1. **Prevents kiting**: Can't dance in and out of range safely
2. **Positioning matters more**: Moving becomes riskier, more strategic
3. **Tank builds viable**: Standing in front can control space
4. **Combat feels reactive**: Not just turn-by-turn exchanges

#### Potential Issues
1. **Movement paralysis**: Players might avoid moving at all
2. **Combat speed**: More attacks per round = longer turns
3. **AI complexity**: Enemies need to evaluate reaction risks
4. **Clear communication**: Must show when reactions will trigger

### Code Structure Considerations

#### Reaction Trigger System
```python
class ReactionTrigger:
    """Base class for reaction triggers"""
    def should_trigger(self, scene, triggering_unit, target_unit) -> bool:
        raise NotImplementedError
    
    def execute(self, scene, reacting_unit, target_unit):
        raise NotImplementedError

class DisengagementTrigger(ReactionTrigger):
    """Triggered when unit moves away from melee"""
    def should_trigger(self, scene, moving_unit, ...):
        # Check if moving from distance 1 to distance > 1
        ...
```

#### Integration Points
1. **Movement handler** (`_try_move_unit`): Check for disengagement before moving
2. **Combat handler** (`apply_damage`): Check for counter-attack triggers
3. **Turn system**: Track reaction points/uses per turn
4. **AI**: Evaluate reaction risks when planning movement

### Existing Related Features

**Counter-Attack System (Already Implemented!):**
- There's already a `counter_attack` skill that grants `counter_stance` status
- When attacked, deals 1.5x damage back (in `BattleCombat.apply_damage`)
- This is an active skill that must be used - not automatic
- Could be a model for how to implement other reactions

**Perk Trees That Could Support Reactions:**
- **Ward tree** (`ward` branch): Defense-focused, currently has Iron Guard and Shield Bash
  - Perfect fit for "Sentinel" perk granting AoO
- **Mobility tree** (`mobility` branch): Movement-focused, has Fleet Footwork perks
  - Could grant reaction abilities or movement-related reactions
- **Blade tree**: Offense-focused, could have aggressive reactions

### Recommendation

**Phased Approach**:

**Phase 1: Simple Attacks of Opportunity**
- Implement basic disengagement AoO
- Grant 1 reaction per turn (can be used for AoO or saved)
- Only trigger when moving from adjacent to non-adjacent
- Make it optional via perk/skill initially

**Phase 2: Expand Reactions** (if Phase 1 works well)
- Add counter-attack reactions (when being hit)
- Add reactive skills
- Allow multiple reaction types

**Implementation Notes**:
- Add `reactions_remaining: int` to BattleUnit (reset each turn)
- Add `has_reaction_available()` check
- Update movement logic to check for disengagement
- Add UI indicator showing "Reaction Available" or "Will trigger AoO"
- Consider making it a perk: "Sentinel - You can make attacks of opportunity"

---

## Combined Impact

### How They Work Together

1. **Diagonal attacks + AoO**:
   - More escape routes with 8-directional movement
   - But AoO prevents abuse - you can't safely disengage as easily
   - Creates interesting risk/reward: "Do I move diagonally to avoid AoO from one enemy, but risk AoO from another?"

2. **Tactical depth**:
   - Diagonal attacks = more engagement options
   - Reactions = more defensive/positioning concerns
   - Together they create more dynamic, positionally-aware combat

### Testing Priorities

1. **Combat doesn't become too easy**: Diagonal attacks make it easier to engage
2. **Movement still feels good**: Reactions shouldn't make movement feel punishing
3. **AI handles both**: Enemies need to understand diagonal positioning and reaction risks
4. **Performance**: More calculations per turn (especially reactions)

---

## Questions to Consider

1. **For Diagonal Attacks**:
   - Should diagonal movement cost more? (Common: 1.5x movement points)
   - Should diagonal attacks have any penalty? (Reduced accuracy/damage?)
   - How does this affect ranged weapons? (Keep Manhattan or switch to Chebyshev?)

2. **For Reactions**:
   - Should reactions be universal or gated behind perks?
   - How many reactions per turn? (1 is common, some games allow multiple)
   - Should AoO deal full damage or reduced? (50-75% is common)
   - What about moving *into* melee range? (Usually doesn't trigger in D&D)

3. **Combined**:
   - Should you be able to AoO diagonally? (Probably yes, if you can attack diagonally)
   - Does diagonal disengagement still trigger AoO? (I'd say yes - it's still leaving melee range)

---

## Suggested Implementation Order

1. **Start with Diagonal Attacks (Option B - Full 8-directional)**
   - Get it working and balanced first
   - Test that combat still feels good

2. **Then add Reactions (Phase 1 - Simple AoO)**
   - Start with basic disengagement AoO
   - Make it optional (perk-based)
   - Test extensively

3. **Iterate based on feedback**
   - Adjust costs, ranges, reaction triggers based on playtesting

---

## My Recommendation

**Diagonal Attacks**: Implement Option B (full 8-directional movement + attacks) with:
- Diagonal movement costs 1.5x movement points
- Chebyshev distance for melee range checks
- Keep Manhattan for ranged (or make it configurable per weapon)

**Reactions**: Start with Phase 1 (simple AoO) as a perk/skill:
- Perk: "Sentinel" (in the `ward` branch, after `iron_guard_1`)
  - Grants 1 reaction per turn
  - Unlocks ability to make attacks of opportunity
- AoO triggers on disengagement (orthogonal or diagonal)
- AoO deals 75% damage (less punishing than full)
- Make it optional so players can opt in/out
- **Note**: Already have `counter_attack` skill as a model - could make reactions a similar status/ability system

This keeps both features optional and testable before committing to full implementation.

