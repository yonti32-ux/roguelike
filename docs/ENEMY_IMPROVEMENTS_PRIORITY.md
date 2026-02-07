# Enemy System Improvements - Priority List

## Current State ✅
- ✅ 53 enemies (23 original + 30 new)
- ✅ Modular difficulty system (1-100 scale)
- ✅ Tag-based categorization
- ✅ 15+ pack templates
- ✅ Overworld enemy scaling

---

## High Priority Improvements (Quick Wins)

### 1. Unique Mechanics System ⭐ **RECOMMENDED FIRST**

Add special abilities to enemies beyond just skills.

**Implementation:**
```python
@dataclass
class EnemyArchetype:
    # ... existing fields ...
    unique_mechanics: List[str] = field(default_factory=list)
    # Examples: "regeneration", "fire_immunity", "phase_through", "summon_on_death"
```

**Benefits:**
- Makes enemies more memorable
- Adds tactical depth
- Easy to implement (just add field, handle in battle logic)

**Examples:**
- Troll Berserker: `["regeneration"]` - Heals each turn
- Fire Elemental: `["fire_immunity"]` - Immune to fire damage
- Wraith: `["phase_through"]` - Can move through units
- Death Knight: `["summon_on_kill"]` - Summons minion when kills enemy

**Effort**: Low-Medium (1-2 days)
**Impact**: High

---

### 2. Enemy Synergy System ⭐ **RECOMMENDED SECOND**

Enemies get bonuses when certain types are together.

**Implementation:**
```python
def calculate_pack_synergies(enemies: List[Enemy]) -> Dict[str, float]:
    """
    Calculate synergy bonuses for a pack of enemies.
    
    Returns:
        Dict of stat bonuses (e.g., {"attack_mult": 1.1, "hp_mult": 1.05})
    """
    bonuses = {"attack_mult": 1.0, "hp_mult": 1.0, "defense_mult": 1.0}
    
    # Count enemy types
    goblin_count = sum(1 for e in enemies if "goblin" in e.tags)
    undead_count = sum(1 for e in enemies if "undead" in e.tags)
    # ... etc
    
    # Apply synergies
    if goblin_count >= 3:
        bonuses["attack_mult"] += 0.1  # +10% attack
    
    if undead_count >= 2:
        bonuses["hp_mult"] += 0.05 * undead_count  # +5% HP per undead
    
    return bonuses
```

**Synergy Ideas:**
- **Goblin Pack** (3+ goblins): +10% attack
- **Undead Horde** (2+ undead): +5% HP per undead (max +25%)
- **Cultist Circle** (2+ cultists): +1 skill power per cultist
- **Beast Pack** (2+ beasts): +15% speed
- **Elemental Storm** (2+ elementals): +20% skill power
- **Tank Line** (2+ tanks): +10% defense each

**Effort**: Medium (2-3 days)
**Impact**: High

---

### 3. More Room-Specific Enemies

Expand unique room enemies for variety.

**New Uniques:**
- **Library**: `arcane_golem` - High magic defense
- **Armory**: `animated_armor` - High physical defense
- **Kitchen**: `cursed_chef` - Poison-focused
- **Throne Room**: `royal_guard` - Elite tank
- **Crypt**: `lich_guardian` - Summons undead

**Effort**: Low (1 day)
**Impact**: Medium

---

### 4. Resistance System

Add damage type resistances to enemies.

**Implementation:**
```python
@dataclass
class EnemyArchetype:
    # ... existing fields ...
    resistances: Dict[str, float] = field(default_factory=dict)
    # Examples: {"fire": 0.5, "poison": 0.0, "physical": 0.1}
    # 0.0 = immune, 0.5 = 50% damage, 1.0 = normal
```

**Examples:**
- Fire Elemental: `{"fire": 0.0}` - Immune to fire
- Ice Wraith: `{"ice": 0.0, "fire": 1.5}` - Immune to ice, weak to fire
- Stone Golem: `{"physical": 0.3}` - 70% physical resistance

**Effort**: Medium (2-3 days)
**Impact**: High

---

## Medium Priority Improvements

### 5. Enhanced AI Profiles

More sophisticated AI behaviors.

**New Profiles:**
- `aggressive` - Always attacks, ignores low HP
- `defensive` - Prioritizes survival
- `opportunist` - Targets low HP enemies
- `support_focused` - Prioritizes buffing/healing
- `tactical_caster` - Maintains distance, uses AoE

**Effort**: Medium-High (3-5 days)
**Impact**: High

---

### 6. Status Effect Combinations

Status effects interact with each other.

**Combinations:**
- Fire + Poison = Explosion (burst damage)
- Frozen + Fire = Melt (removes frozen, extra damage)
- Electrified + Water = Chain Lightning
- Bleeding + Marked = Critical Bleed

**Effort**: Medium (2-3 days)
**Impact**: Medium-High

---

### 7. Enemy Variants System

Create variants of existing enemies easily.

**Implementation:**
```python
def create_enemy_variant(base_arch: EnemyArchetype, variant_type: str) -> EnemyArchetype:
    """
    Create a variant of an enemy (fire goblin, ice goblin, etc.)
    """
    variant = EnemyArchetype(
        id=f"{base_arch.id}_{variant_type}",
        name=f"{variant_type.title()} {base_arch.name}",
        # ... copy base stats ...
        # Modify based on variant
        resistances={"fire": 0.0} if variant_type == "fire" else {},
        tags=base_arch.tags + [variant_type],
    )
    return variant
```

**Effort**: Low-Medium (1-2 days)
**Impact**: Medium

---

### 8. Initiative Variety

More variation in enemy initiative.

**Current**: Most enemies have `base_initiative=10`

**Improvement**: 
- Fast enemies: `base_initiative=12-15`
- Slow enemies: `base_initiative=7-9`
- Elite enemies: `base_initiative=13-16`

**Effort**: Low (few hours)
**Impact**: Medium

---

## Lower Priority (Future)

### 9. Enemy Coordination
- Pack tactics (focus fire)
- Formation AI
- Support prioritization

### 10. Environmental Interactions
- Terrain-aware enemies
- Hazard creation
- Room-specific behaviors

### 11. Dynamic Difficulty
- Enemies adapt to player strategy
- Learning AI
- Elite evolution mid-battle

---

## Recommended Implementation Order

### Phase 1: Quick Wins (1 week)
1. ✅ Unique Mechanics System
2. ✅ More Room-Specific Enemies
3. ✅ Initiative Variety

### Phase 2: Tactical Depth (1 week)
4. ✅ Enemy Synergy System
5. ✅ Resistance System

### Phase 3: Advanced Features (2 weeks)
6. ✅ Enhanced AI Profiles
7. ✅ Status Effect Combinations
8. ✅ Enemy Variants

---

## Quick Implementation Examples

### Example 1: Add Unique Mechanics
```python
# In EnemyArchetype
unique_mechanics: List[str] = field(default_factory=list)

# In battle logic
if "regeneration" in enemy.unique_mechanics:
    enemy.hp = min(enemy.max_hp, enemy.hp + 2)
```

### Example 2: Add Synergies
```python
# When creating battle from pack
synergies = calculate_pack_synergies(enemies)
for enemy in enemies:
    enemy.attack_power = int(enemy.attack_power * synergies["attack_mult"])
    enemy.max_hp = int(enemy.max_hp * synergies["hp_mult"])
```

### Example 3: Add Resistances
```python
# In damage calculation
damage_type = "fire"
resistance = enemy.resistances.get(damage_type, 1.0)
final_damage = int(base_damage * resistance)
```

---

## Summary

**Best Next Steps:**
1. **Unique Mechanics** - Easy, high impact
2. **Enemy Synergies** - Makes packs more interesting
3. **Resistance System** - Adds tactical depth
4. **More Room Uniques** - Quick variety boost

These improvements will make enemies feel more unique and tactical without requiring major system overhauls!
