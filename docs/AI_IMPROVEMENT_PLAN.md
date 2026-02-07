# Battle AI Improvement Plan

## Current State Analysis

### Current AI Profiles
- **brute**: Charges forward, targets highest attack power
- **skirmisher**: Flanks, targets low HP
- **caster**: Maintains distance, targets debuffed/low HP
- **support**: Heals/buffs allies

### Current Limitations
1. **Skill Usage**: Mostly random with chance-based decisions (40-70% chance)
2. **No Coordination**: Enemies act independently, no focus fire or combos
3. **Limited Tactics**: Basic positioning, no threat assessment
4. **No Synergy Awareness**: Doesn't leverage pack synergies strategically
5. **Resource Blind**: Doesn't consider mana/stamina costs
6. **No Adaptive Behavior**: Same strategy regardless of situation

## Proposed Improvements

### Phase 1: Enhanced AI Profiles

#### New AI Profiles
1. **tactician** - Smart positioning, combo setup, threat assessment
2. **berserker** - Aggressive, ignores defense when low HP, charges recklessly
3. **defender** - Protects allies, bodyblocks, uses defensive skills proactively
4. **controller** - Focuses on debuffs, crowd control, positioning enemies
5. **assassin** - Targets isolated/low HP enemies, uses stealth/teleport
6. **commander** - Coordinates allies, buffs team, calls focus fire

### Phase 2: Tactical Decision Making

#### Threat Assessment System
- Calculate threat value for each player unit
- Factors: HP%, attack power, skill power, status effects, position
- Prioritize high-threat targets

#### Skill Prioritization
- **Situational Awareness**: Use skills based on context, not random chance
- **Combo Detection**: Chain skills together (e.g., mark → heavy_slam)
- **Resource Management**: Consider mana/stamina before using expensive skills
- **Cooldown Planning**: Save powerful skills for optimal moments

#### Coordination System
- **Focus Fire**: Multiple enemies target same player unit
- **Protect Allies**: Defenders position to block attacks on casters
- **Formation Tactics**: Maintain optimal spacing for AoE and support
- **Combo Setup**: One enemy marks, another uses heavy attack

### Phase 3: Advanced Behaviors

#### Positioning Intelligence
- **AoE Optimization**: Position to hit multiple targets
- **Flanking Priority**: Skirmishers actively seek flanking positions
- **Cover Usage**: Use terrain/obstacles for protection
- **Formation Maintenance**: Keep support units safe

#### Adaptive Behavior
- **HP-Based Strategy**: Change tactics when low HP
- **Enemy Count Awareness**: More aggressive when outnumbered
- **Skill Availability**: Adapt when key skills on cooldown
- **Player Pattern Recognition**: Learn from player behavior (future)

### Phase 4: Pack Tactics

#### Synergy Utilization
- **Tag-Based Coordination**: Undead units work together for horde bonus
- **Role Synergy**: Casters buff brutes, support heals tanks
- **Combo Chains**: Set up multi-enemy skill combos

#### Group Behaviors
- **Pack Leader**: One enemy coordinates others
- **Protect the Caster**: Brutes form defensive line
- **Swarm Tactics**: Weak enemies overwhelm single target

## Implementation Plan

### Step 1: Enhanced AI Profiles
- Add new AI profile types to `EnemyArchetype`
- Create profile-specific decision trees
- Update `BattleAI.get_ai_profile()` to support new profiles

### Step 2: Threat Assessment
- Create `calculate_threat_value()` function
- Update `choose_target_by_priority()` to use threat assessment
- Add threat-based targeting for all profiles

### Step 3: Skill Prioritization System
- Replace random chance with situational evaluation
- Create skill priority scoring system
- Implement combo detection

### Step 4: Coordination Framework
- Add battle state tracking (who's targeting whom)
- Implement focus fire logic
- Add formation/positioning helpers

### Step 5: Testing & Balancing
- Test each profile individually
- Test coordination behaviors
- Balance skill usage frequencies
- Ensure AI is challenging but not unfair

## Benefits

1. **More Engaging Combat**: Enemies feel smarter and more tactical
2. **Variety**: Different enemy types require different strategies
3. **Scalability**: Easy to add new profiles and behaviors
4. **Player Satisfaction**: Beating smart AI feels rewarding
5. **Replayability**: Different enemy compositions create different challenges

## Next Steps

1. Implement enhanced AI profiles
2. Add threat assessment system
3. Improve skill prioritization
4. Add coordination behaviors
5. Test and balance
6. Add new enemies that leverage improved AI
