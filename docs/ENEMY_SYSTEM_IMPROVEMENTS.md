# Enemy System Improvements & Expansions

## Overview
This document outlines comprehensive improvements and expansions for the enemy system to increase variety, tactical depth, and player engagement.

---

## 1. Enhanced Enemy Variety & Unique Mechanics

### 1.1 New Enemy Archetypes by Tier

#### Tier 1 Additions:
- **Goblin Trapper** (Skirmisher)
  - Low HP, high initiative
  - Skills: `trap_set`, `poison_strike`
  - Unique: Can place temporary terrain hazards

- **Skeleton Warrior** (Brute)
  - Moderate HP, low defense
  - Skills: `bone_shield`, `heavy_slam`
  - Unique: Resurrects once at 50% HP (becomes "Skeleton Remnant")

- **Cultist Zealot** (Invoker)
  - Low HP, high damage
  - Skills: `dark_hex`, `self_sacrifice` (damages self, buffs allies)
  - Unique: Death triggers buff for nearby allies

#### Tier 2 Additions:
- **Wraith** (Skirmisher)
  - Low HP, high evasion
  - Skills: `phase_shift`, `life_drain`
  - Unique: Can pass through units (no collision)

- **Troll Berserker** (Brute)
  - Very high HP, moderate attack
  - Skills: `regeneration`, `berserker_rage`, `heavy_slam`
  - Unique: Regenerates HP each turn (scales with missing HP)

- **Mind Flayer** (Support)
  - Moderate HP, high skill power
  - Skills: `mind_control`, `psychic_blast`, `confusion`
  - Unique: Can temporarily control player units

- **Fire Elemental** (Invoker)
  - Moderate HP, fire immunity
  - Skills: `fireball`, `flame_wall`, `ignite`
  - Unique: Leaves fire terrain on death

#### Tier 3 Additions:
- **Death Knight** (Elite Brute)
  - Very high HP, high attack
  - Skills: `death_strike`, `raise_undead`, `war_cry`
  - Unique: Summons weak undead minions on kill

- **Void Mage** (Invoker)
  - Moderate HP, very high skill power
  - Skills: `void_bolt`, `teleport`, `disintegrate`
  - Unique: Can teleport and has AoE void damage

- **Behemoth** (Elite Brute)
  - Extremely high HP, moderate attack
  - Skills: `stomp`, `charge`, `earthquake`
  - Unique: Large size (2x2 tiles), blocks movement

### 1.2 Unique Mechanics System

Add a `unique_mechanics` field to `EnemyArchetype`:

```python
@dataclass
class EnemyArchetype:
    # ... existing fields ...
    unique_mechanics: List[str] = field(default_factory=list)
    # Examples: "resurrect", "summon_on_death", "phase_through", "fire_immunity"
```

**Implementation Priority**: High
**Effort**: Medium

---

## 2. Enhanced Battle AI

### 2.1 Advanced AI Profiles

Current profiles are basic. Expand to include:

- **Tactical Profiles**:
  - `aggressive`: Always attacks, ignores low HP
  - `defensive`: Prioritizes survival, uses defensive skills
  - `opportunist`: Targets low HP enemies, uses positioning
  - `support_focused`: Prioritizes buffing/healing allies
  - `caster_tactical`: Maintains distance, uses AoE effectively

- **AI Behavior Trees**:
  - Decision trees based on:
    - HP percentage
    - Ally status
    - Enemy positioning
    - Available skills/resources
    - Turn order

### 2.2 Enemy Coordination

- **Pack Tactics**: Enemies coordinate attacks
  - Focus fire on same target
  - Flanking bonuses when multiple enemies surround target
  - Support units prioritize healing/buffing damage dealers

- **Formation AI**: Enemies maintain formations
  - Tanks in front, casters in back
  - Skirmishers on flanks
  - Dynamic repositioning based on player actions

**Implementation Priority**: High
**Effort**: High

---

## 3. Enemy Synergies & Combos

### 3.1 Synergy System

Add synergy bonuses when certain enemy types are together:

- **Goblin Pack**: +10% attack when 3+ goblins present
- **Undead Horde**: +5% HP per undead (max +25%)
- **Cultist Circle**: Casters gain +1 skill power per cultist
- **Beast Pack**: +15% speed when 2+ beasts together

### 3.2 Combo Attacks

Enemies can perform combo attacks:

- **Marked Target Combo**: One enemy marks, others focus fire
- **Heal Chain**: Support heals tank, tank protects support
- **AoE Setup**: One enemy weakens, another uses AoE
- **Death Trigger**: When one enemy dies, others gain buffs

**Implementation Priority**: Medium
**Effort**: Medium

---

## 4. Status Effects & Interactions

### 4.1 New Status Effects

- **Burning**: Fire DoT, spreads to adjacent units
- **Frozen**: Slows movement, reduces initiative
- **Electrified**: Chain damage to adjacent units
- **Corrupted**: Reduces max HP temporarily
- **Enraged**: +50% attack, -25% defense
- **Shielded**: Absorbs next X damage

### 4.2 Status Combinations

- **Fire + Poison = Explosion**: Deals burst damage
- **Frozen + Fire = Melt**: Removes frozen, deals extra damage
- **Electrified + Water = Chain Lightning**: Spreads to all wet units
- **Bleeding + Marked = Critical Bleed**: Increased DoT

### 4.3 Status Resistance System

- Different enemies have different resistances
- Elite enemies have higher resistance
- Some enemies are immune to certain statuses
- Resistance can be reduced by debuffs

**Implementation Priority**: High
**Effort**: Medium

---

## 5. Environmental Interactions

### 5.1 Terrain-Aware Enemies

- **Fire Elementals**: Heal on fire terrain, immune to fire
- **Water Spirits**: Move faster on water, slower on fire
- **Earth Golems**: Gain defense on stone terrain
- **Flying Enemies**: Ignore terrain movement costs

### 5.2 Environmental Hazards

- Enemies can create hazards:
  - Fire mages create fire patches
  - Ice mages create slippery ice
  - Poison enemies leave poison clouds
  - Earth enemies create difficult terrain

### 5.3 Room-Specific Behaviors

- Enemies adapt to room types:
  - Lair rooms: More aggressive
  - Event rooms: More defensive
  - Graveyard: Undead gain bonuses
  - Sanctum: Holy enemies stronger

**Implementation Priority**: Medium
**Effort**: Medium

---

## 6. Enemy Evolution & Adaptation

### 6.1 Dynamic Scaling

- Enemies adapt to player strategy:
  - If player uses lots of fire, enemies gain fire resistance
  - If player uses lots of melee, enemies gain more defense
  - If player uses lots of ranged, enemies become more mobile

### 6.2 Enemy Learning

- Enemies remember player tactics:
  - Track which skills player uses most
  - Adapt positioning to counter player
  - Prioritize targets based on player behavior

### 6.3 Elite Evolution

- Elite enemies can evolve mid-battle:
  - Gain new skills when low HP
  - Transform into stronger form
  - Summon reinforcements

**Implementation Priority**: Low
**Effort**: High

---

## 7. More Unique Enemies

### 7.1 Room-Specific Uniques

Expand `UNIQUE_ROOM_ENEMIES`:

- **Library**: `arcane_golem` (high magic defense)
- **Armory**: `animated_armor` (high physical defense)
- **Kitchen**: `cursed_chef` (poison-focused)
- **Throne Room**: `royal_guard` (elite tank)
- **Crypt**: `lich_guardian` (summons undead)

### 7.2 Event Enemies

- Special enemies that only appear in events:
  - `treasure_mimic` (appears as chest)
  - `cursed_merchant` (can be fought or traded with)
  - `wandering_boss` (rare overworld boss)

### 7.3 Seasonal/Variant Enemies

- Different variants of same enemy:
  - `goblin_skirmisher_fire` (fire attacks)
  - `goblin_skirmisher_ice` (ice attacks)
  - `goblin_skirmisher_poison` (poison attacks)

**Implementation Priority**: Medium
**Effort**: Low-Medium

---

## 8. Enemy Factions & Relationships

### 8.1 Faction System

- Enemies belong to factions:
  - `goblin_tribe`
  - `undead_legion`
  - `cult_of_void`
  - `beast_pack`

### 8.2 Faction Interactions

- Factions can fight each other:
  - Goblins vs Orcs (natural enemies)
  - Undead vs Living (always hostile)
  - Some factions neutral to each other

### 8.3 Faction Bonuses

- Faction-wide bonuses:
  - All goblins gain +5% attack when warboss present
  - Undead gain +10% HP when necromancer present
  - Cultists gain +1 skill power when harbinger present

**Implementation Priority**: Low
**Effort**: Medium

---

## 9. Dynamic Difficulty & Scaling

### 9.1 Adaptive Difficulty

- Adjust enemy strength based on:
  - Player win rate
  - Recent performance
  - Party composition
  - Equipment level

### 9.2 Challenge Modes

- **Veteran Mode**: +25% enemy stats
- **Elite Mode**: All enemies are elite
- **Horde Mode**: 2x enemy count, 0.7x stats
- **Boss Rush**: Only bosses and mini-bosses

### 9.3 Scaling Improvements

- Better stat scaling formulas
- Cap maximum scaling to prevent exponential growth
- Floor-based difficulty curves
- Player level vs floor level balancing

**Implementation Priority**: Medium
**Effort**: Medium

---

## 10. Enhanced Pack System

### 10.1 More Pack Varieties

- **Mixed Packs**: Combine different enemy types
- **Specialized Packs**: All same type (glass cannon or tank)
- **Balanced Packs**: Tank + DPS + Support
- **Swarm Packs**: Many weak enemies

### 10.2 Pack Spawning Rules

- Packs spawn based on:
  - Room type
  - Floor depth
  - Player level
  - Recent encounters (avoid repetition)

### 10.3 Pack AI

- Packs coordinate:
  - Formation maintenance
  - Target prioritization
  - Skill combos
  - Retreat behavior

**Implementation Priority**: High
**Effort**: Medium

---

## 11. Visual & Audio Improvements

### 11.1 Enemy Variants

- Visual variants for same archetype:
  - Different colors
  - Different sizes
  - Different equipment
  - Elite visual effects

### 11.2 Animation Improvements

- Unique attack animations per enemy type
- Death animations
- Status effect visual indicators
- Movement animations (flying, crawling, etc.)

### 11.3 Audio Cues

- Unique sounds per enemy type
- Alert sounds when enemies spot player
- Death sounds
- Skill cast sounds

**Implementation Priority**: Low
**Effort**: Low-Medium

---

## 12. Implementation Roadmap

### Phase 1: Foundation (High Priority)
1. ✅ Enhanced AI profiles
2. ✅ New status effects
3. ✅ More enemy archetypes (10-15 new)
4. ✅ Unique mechanics system

**Estimated Effort**: 2-3 weeks

### Phase 2: Tactical Depth (High Priority)
1. ✅ Enemy synergies
2. ✅ Combo attacks
3. ✅ Enhanced pack system
4. ✅ Status combinations

**Estimated Effort**: 2-3 weeks

### Phase 3: Environmental (Medium Priority)
1. ✅ Terrain interactions
2. ✅ Room-specific behaviors
3. ✅ Environmental hazards

**Estimated Effort**: 1-2 weeks

### Phase 4: Advanced Features (Low Priority)
1. ✅ Faction system
2. ✅ Dynamic difficulty
3. ✅ Enemy evolution
4. ✅ Visual improvements

**Estimated Effort**: 3-4 weeks

---

## 13. Quick Wins (Easy to Implement)

1. **Add 5-10 new enemy archetypes** (copy existing, modify stats)
2. **Add 3-5 new status effects** (extend status system)
3. **Create 5-10 new pack templates** (mix existing enemies)
4. **Add unique room enemies** (extend UNIQUE_ROOM_ENEMIES)
5. **Improve elite spawn rates** (tweak BASE_ELITE_SPAWN_CHANCE)
6. **Add enemy name variants** (use name generator)
7. **Create enemy description system** (flavor text)

**Estimated Effort**: 1 week

---

## 14. Code Structure Suggestions

### 14.1 New Files

- `systems/enemy_mechanics.py` - Unique mechanics handlers
- `systems/enemy_synergies.py` - Synergy system
- `systems/enemy_factions.py` - Faction system
- `engine/battle/enemy_coordination.py` - Pack coordination AI

### 14.2 Extensions to Existing Files

- `systems/enemies.py` - Add unique_mechanics, faction_id fields
- `engine/battle/ai.py` - Enhanced AI profiles and coordination
- `systems/statuses.py` - Status combinations and interactions
- `world/entities.py` - Enemy visual variants

---

## 15. Testing Considerations

- Balance testing for new enemies
- AI behavior testing
- Synergy balance testing
- Performance testing (many enemies)
- Difficulty curve testing

---

## Summary

This plan provides a comprehensive roadmap for expanding and improving the enemy system. Focus on **Phase 1** and **Quick Wins** for immediate impact, then gradually implement more advanced features.

**Key Priorities**:
1. More enemy variety (archetypes, packs)
2. Better AI (profiles, coordination)
3. Status effects (new effects, combinations)
4. Unique mechanics (per-enemy special abilities)

**Estimated Total Effort**: 8-12 weeks for full implementation
**Recommended Starting Point**: Quick Wins + Phase 1 (3-4 weeks)
