# AI Profiles Guide

Complete guide to all available AI profiles for enemy units.

## Available Profiles

### Basic Profiles

#### 1. **brute**
**Behavior**: Aggressive melee fighters that charge forward
- **Targeting**: Prioritizes marked targets, then highest threat
- **Skills**: Uses heavy_slam on marked targets
- **Movement**: Direct charge forward
- **Best For**: Tanky melee enemies, front-line fighters

#### 2. **skirmisher**
**Behavior**: Mobile fighters that flank enemies
- **Targeting**: Prioritizes marked targets, then low HP (finish them off)
- **Skills**: Uses crippling_blow on low HP targets
- **Movement**: Actively seeks flanking positions
- **Best For**: Fast, mobile enemies, rogues

#### 3. **caster**
**Behavior**: Ranged spellcasters that maintain distance
- **Targeting**: Prioritizes debuffed targets, then low HP
- **Skills**: Uses mark_target and dark_hex
- **Movement**: Maintains optimal range, backs away if too close
- **Best For**: Mages, spellcasters, ranged enemies

#### 4. **support**
**Behavior**: Healers and buffers that prioritize allies
- **Targeting**: Low HP targets when attacking
- **Skills**: Heals and buffs allies first
- **Movement**: Advances after supporting
- **Best For**: Clerics, healers, support units

### Advanced Profiles

#### 5. **tactician**
**Behavior**: Smart fighters using positioning and combos
- **Targeting**: Focus fire targets, then threat assessment
- **Skills**: Sets up combos (mark → heavy_slam)
- **Movement**: Seeks flanking positions tactically
- **Best For**: Elite fighters, tactical enemies, leaders

#### 6. **berserker**
**Behavior**: Aggressive fighters that ignore defense when low HP
- **Targeting**: Nearest target when low HP, otherwise highest attack
- **Skills**: Uses berserker_rage when very low HP, ignores defense
- **Movement**: Reckless charge, especially when low HP
- **Best For**: Barbarians, berserkers, aggressive brutes

#### 7. **defender**
**Behavior**: Protective fighters that bodyblock for allies
- **Targeting**: Enemies threatening allies, then highest threat
- **Skills**: Uses guard proactively
- **Movement**: Positions to protect threatened allies
- **Best For**: Paladins, bodyguards, protective tanks

#### 8. **controller**
**Behavior**: Focuses on debuffs and crowd control
- **Targeting**: High-threat unmarked targets
- **Skills**: Prioritizes mark_target, dark_hex, fear_scream (AoE stun)
- **Movement**: Maintains distance for ranged controllers
- **Best For**: Necromancers, debuffers, crowd controllers

#### 9. **assassin**
**Behavior**: Targets isolated or low-HP enemies
- **Targeting**: Isolated targets first, then low HP
- **Skills**: Uses crippling_blow and poison_strike on isolated targets
- **Movement**: Seeks flanking positions, stalks forward
- **Best For**: Rogues, assassins, backstabbers

#### 10. **commander**
**Behavior**: Coordinates allies and calls focus fire
- **Targeting**: Focus fire targets, coordinates team
- **Skills**: Buffs allies (buff_ally, war_cry), marks focus targets
- **Movement**: Advances while coordinating
- **Best For**: Leaders, commanders, team coordinators

## Profile Comparison

| Profile | Aggression | Tactics | Support | Best Role |
|---------|-----------|---------|---------|-----------|
| brute | High | Low | None | Front-line DPS |
| skirmisher | Medium | Medium | None | Mobile DPS |
| caster | Low | Medium | Low | Ranged DPS |
| support | Low | Low | High | Healer/Buffer |
| tactician | Medium | High | Low | Tactical DPS |
| berserker | Very High | Low | None | Aggressive DPS |
| defender | Low | Medium | High | Tank/Protector |
| controller | Low | High | Medium | Crowd Control |
| assassin | Medium | High | None | Burst DPS |
| commander | Medium | High | High | Leader/Coordinator |

## Usage

### In Enemy Archetype Definition

```python
EnemyArchetype(
    id="elite_warrior",
    name="Elite Warrior",
    role="Elite Brute",
    ai_profile="tactician",  # Use tactician AI
    # ... other fields ...
)
```

### Profile Selection Guidelines

- **Early Game**: Use basic profiles (brute, skirmisher, caster, support)
- **Mid Game**: Mix basic and advanced profiles
- **Late Game**: Use advanced profiles for variety and challenge
- **Elite Enemies**: Use tactician, commander, or defender
- **Bosses**: Use commander or tactician for coordination

## Combining Profiles in Packs

### Effective Combinations

1. **Tactical Pack**: tactician + commander + defender
   - Commander coordinates, tactician executes, defender protects

2. **Aggressive Pack**: berserker + brute + assassin
   - All focus on damage, different approaches

3. **Control Pack**: controller + caster + support
   - Debuffs, damage, and healing

4. **Balanced Pack**: brute + skirmisher + caster + support
   - Classic RPG party composition

## Customization

Each profile can be customized by:
1. Modifying the profile class in `engine/battle/ai/profiles/`
2. Adjusting skill usage probabilities
3. Changing targeting priorities
4. Modifying movement behavior

## Testing

To test a profile:
1. Create an enemy with that profile
2. Observe behavior in battle
3. Adjust probabilities and priorities as needed
4. Test in different scenarios (low HP, multiple enemies, etc.)

## Future Enhancements

- Profile-specific skill preferences
- Adaptive behavior based on battle state
- Profile synergies (certain profiles work better together)
- Dynamic profile switching (e.g., berserker when low HP)
