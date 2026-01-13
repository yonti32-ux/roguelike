# Combat Integration Summary

## Quick Reference: System Connections

### High-Level Flow

```
┌─────────────────┐
│   OVERWORLD     │
│   (Tile Map)    │
└────────┬────────┘
         │
         │ Player moves / encounters
         ▼
┌─────────────────┐
│ ROAMING PARTIES │
│  (RoamingParty) │
└────────┬────────┘
         │
         │ Interaction / Attack
         ▼
┌─────────────────┐      ┌──────────────┐
│ PARTY TYPE      │─────▶│   FACTION    │
│ (PartyType)     │      │  Relations   │
└────────┬────────┘      └──────────────┘
         │
         │ Convert to enemies
         ▼
┌─────────────────┐
│ BATTLE SYSTEM   │
│  (BattleScene)  │
└────────┬────────┘
         │
         │ Battle ends
         ▼
┌─────────────────┐
│ POST-COMBAT     │
│  - Remove party │
│  - Update rels  │
│  - Give loot    │
└─────────────────┘
```

## Key Components

### 1. Party Types → Battle Units (Dynamic Scaling)

**Mapping Strategy:**
- `PartyType.battle_unit_template` → Enemy Archetype ID
- `PartyType.combat_strength` → Base enemy count (1-5)
- **Player party size** → Additional enemies (+1.5 per member)
- `PartyType.combat_strength` → Enemy stat scaling
- `PartyType.id` → Special scaling rules (swarm/elite)

**Scaling Formula:**
```
Base: 1-3 enemies (when party_size = 2, hero + 1 companion)
+ (party_size - 2) × (1.0 to 2.0) enemies per additional member
+ Random variation: ±0.3 per member
+ Combat strength modifier
+ Party type modifier (swarm/elite)
= Total enemies (1-8, configurable max)
```

**Key Design:**
- **Starts at party_size = 2** (hero + 1 companion at game start)
- **Minimum always 1** (allows weak encounters even with large party)
- **Large range** (e.g., 2-5 for party_size 3) creates variety
- **Random variation** ensures no two encounters are identical

**Examples:**
```
Scenario 1: Hero + 1 companion vs Bandit Party (Game Start)
  Party Size: 2
  Combat Strength: 2
  Base: 1-3 enemies (random)
  Scaling: +0 (base party size)
  Total: 1-3 enemies (can be just 1 weak bandit!)

Scenario 2: Hero + 2 companions vs Bandit Party
  Party Size: 3
  Combat Strength: 2
  Base: 1-3 enemies (random)
  Scaling: +1-2 enemies (from 1 additional member)
  Total: 2-5 enemies (large range for variety)

Scenario 3: Hero + 3 companions vs Goblin Swarm
  Party Size: 4
  Combat Strength: 1
  Base: 1 enemy (random, could be 1-3)
  Scaling: +2-4 enemies (from 2 additional members)
  Subtotal: 3-7 enemies
  Swarm modifier: +50% → 4-10 enemies (capped at 8)
  Total: 4-8 enemies

Scenario 4: Hero + 4 companions vs Elite Knight Squad
  Party Size: 5
  Combat Strength: 4
  Base: 1-5 enemies (random, higher due to strength)
  Scaling: +3-6 enemies
  Subtotal: 4-11 enemies
  Elite modifier: -25% → 3-8 enemies
  Total: 3-8 enemies (still can find just 3 knights!)
```

### 2. Faction Relations → Combat Behavior

**Decision Tree:**
```
Party Alignment?
├─ Hostile → Always fight
├─ Friendly → Never fight (unless player attacks)
└─ Neutral → Check faction relations
    ├─ Relation < -50 → Fight
    ├─ Relation > 50 → Don't fight
    └─ Otherwise → Player choice
```

### 3. Combat Triggers

**Manual:**
- Player opens party interaction
- Selects "Attack" action
- Combat starts

**Automatic:**
- Hostile party moves adjacent to player
- System checks faction relations
- Combat starts automatically

### 4. Post-Combat Effects

**On Victory:**
1. Remove party from overworld map
2. Decrease faction relation with party's faction (-5 to -15)
3. Decrease relation with allied factions (-2 to -7)
4. Give player gold and items from party
5. Add victory message

**On Defeat:**
- Party may pursue player
- Faction relations unchanged (or slightly improved for party's faction)
- Player respawns at last safe location

## Data Flow Example

### Scenario: Player Attacks Bandit Party

```
1. Player Position: (50, 50)
   Party Position: (50, 50)
   ↓
2. Party Interaction Screen Opens
   Party: RoamingParty(id="bandit_123", faction_id="bandit_confederacy")
   Type: PartyType(id="bandit", alignment=HOSTILE, combat_strength=2)
   ↓
3. Player Selects "Attack"
   ↓
4. Check Faction Relations
   Player Faction: "kingdom_aetheria"
   Party Faction: "bandit_confederacy"
   Relation: -90 (very hostile) ✓ Fight
   ↓
5. Convert Party to Enemies
   Player Party Size: 2 (hero + 1 companion)
   battle_unit_template: "bandit"
   combat_strength: 2
   Base enemies: 2
   Scaling: +1-2 (from 1 additional party member)
   → Creates 3-4 Enemy entities from "bandit" archetype
   → Scales stats to player level 5
   → Adjusts XP per enemy to balance total reward
   ↓
6. Start Battle
   BattleScene(player, [enemy1, enemy2], companions)
   ↓
7. Battle Plays Out
   [Turn-based combat]
   ↓
8. Player Wins
   ↓
9. Post-Combat Updates
   - Remove party "bandit_123" from map
   - Update relation: kingdom_aetheria ↔ bandit_confederacy: -90 → -100
   - Give player: 50 gold (from party.gold)
   - Message: "Defeated Bandit Gang!"
```

## File Structure

```
world/overworld/
├── battle_conversion.py      # Party → Enemy conversion
├── faction_combat.py        # Faction-based combat logic
├── post_combat.py           # Post-combat updates
├── roaming_party.py         # Party entity (existing)
├── party_types.py           # Party type definitions (existing)
└── party_manager.py         # Party manager (existing)

engine/
├── battle/scene.py          # Battle scene (modify for context)
├── controllers/overworld.py # Overworld controller (add triggers)
└── scenes/party_interaction_scene.py  # Modify attack action

systems/
└── factions.py             # Faction definitions (existing)
```

## Integration Points

### Existing Systems to Modify

1. **`engine/scenes/party_interaction_scene.py`**
   - `_action_attack()` → Call battle conversion and start combat

2. **`engine/core/game.py`**
   - Add `start_battle()` method
   - Store battle context (party reference)

3. **`engine/battle/scene.py`**
   - Add `on_battle_end()` callback
   - Store `context_party` reference

4. **`engine/controllers/overworld.py`**
   - `_check_party_interactions()` → Add automatic combat triggers

5. **`world/overworld/party_types.py`**
   - Ensure `battle_unit_template` and `can_join_battle` are set
   - Add faction IDs to party types

## Testing Checklist

### Basic Functionality
- [ ] Can attack a party manually
- [ ] Party converts to enemies correctly
- [ ] Battle starts and plays out
- [ ] Party is removed after defeat
- [ ] Loot is distributed correctly

### Faction Integration
- [ ] Hostile parties fight automatically
- [ ] Friendly parties don't fight
- [ ] Neutral parties respect faction relations
- [ ] Faction relations update after combat
- [ ] Allied factions are affected

### Edge Cases
- [ ] Party with no faction
- [ ] Party with no battle_unit_template
- [ ] Player with no faction
- [ ] Multiple parties nearby
- [ ] Party already in combat

## Next Steps

1. **Implement Phase 1**: Core conversion system
2. **Test**: Verify party-to-enemy conversion works
3. **Implement Phase 2**: Combat triggers
4. **Test**: Verify combat starts correctly
5. **Implement Phase 3**: Faction integration
6. **Test**: Verify faction-based behavior
7. **Implement Phase 4**: Post-combat updates
8. **Test**: Verify all updates work
9. **Polish**: Balance, feedback, edge cases

## Dynamic Scaling Configuration

### Current Settings
- **MIN_ENEMIES**: 1 (absolute minimum, allows weak encounters)
- **MAX_ENEMIES**: 8 (can be increased later)
- **BASE_ENEMIES**: 1-3 (when party_size = 2, hero + 1 companion)
- **SCALING_PER_MEMBER**: 1.0 to 2.0 enemies (random range)
- **SCALING_VARIATION**: ±0.3 per member (adds unpredictability)
- **XP_DIMINISHING_FACTOR**: 0.3 (prevents XP inflation)
- **STARTING_PARTY_SIZE**: 2 (hero + 1 companion)

### Scaling Examples by Party Size

**Note**: Game starts with hero + 1 companion (party_size = 2)

| Party Size | Composition | Base | Scaling | Total (Range) | Typical | Notes |
|------------|-------------|------|---------|---------------|---------|-------|
| 2 | Hero + 1 companion | 1-3 | +0 | **1-3** | 2 | **Game start** |
| 3 | Hero + 2 companions | 1-3 | +1-2 | **2-5** | 3-4 | Early game |
| 4 | Hero + 3 companions | 1-3 | +2-4 | **3-7** | 4-5 | Mid game |
| 5 | Hero + 4 companions | 1-3 | +3-6 | **4-9 (→8)** | 5-6 | Late game |
| 6+ | Hero + 5+ companions | 1-3 | +4-8 | **5-11 (→8)** | 6-7 | Max party |

**Key Features:**
- **Minimum always 1**: Allows weak encounters (single goblin scout) even with full party
- **Large range**: Creates variety - can find easier or harder parties
- **Random variation**: ±0.3 per member adds unpredictability

**With Swarm Modifier (+50%):**
- Party size 3: 2-5 → 3-7 enemies
- Party size 4: 3-7 → 4-10 (→8) enemies

**With Elite Modifier (-25%):**
- Party size 3: 2-5 → 1-3 enemies (can be just 1!)
- Party size 4: 3-7 → 2-5 enemies

### Future Expansion Points
1. **Increase MAX_ENEMIES** for epic battles (10, 12, 15+)
2. **Add pack types** with unique scaling (e.g., "wolf_pack_alpha" → +100% enemies)
3. **Difficulty settings** that modify scaling (easy: -25%, hard: +25%)
4. **Dynamic difficulty** based on player performance

## Questions to Consider

1. **Should parties respawn?** If so, how long?
2. **Should there be a cooldown** between combat triggers?
3. **How should allied parties work?** Join battle or just support?
4. **Should there be surrender mechanics?** Parties can surrender?
5. **How to handle party vs party combat?** (Future feature)
6. **Should MAX_ENEMIES scale with player level?** (e.g., +1 per 5 levels)
7. **How to handle companion deaths?** Should enemy count adjust mid-game?

