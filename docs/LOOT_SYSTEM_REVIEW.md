# Loot System Review & Improvement Suggestions

## Current Implementation Summary

The loot system handles item drops from battles, chests, and shop generation. It uses weighted random selection based on rarity and floor depth.

### Current Features
- ✅ Equipment drops from battles (25-50% chance, floor-scaled)
- ✅ Consumable drops from battles (30-60% chance, floor-scaled) - **NEW**
- ✅ Chest loot (80-95% chance, floor-scaled)
- ✅ Shop stock generation (via economy system)
- ✅ Rarity-based weighting with floor scaling
- ✅ Source-specific bonuses (chests/shops get better items)

## Recent Improvements Made

1. **Added consumable drops to battles** - Consumables now drop separately from equipment, so players can get both
2. **Fixed `_candidate_items()`** - Now includes all equipment types (weapon, helmet, armor, gloves, boots, shield, cloak, ring, amulet) instead of the outdated "trinket" slot
3. **Separate drop chances** - Equipment and consumables have independent drop chances, allowing for more varied rewards

## Suggested Improvements

### 1. **Multiple Item Drops** (Medium Priority)
**Current**: Only one equipment item can drop per battle
**Suggestion**: Allow multiple equipment items for larger encounters or boss battles
- Scale number of drops based on encounter size or difficulty
- Boss battles could guarantee 1-2 items + consumables
- Larger enemy groups could have higher drop rates

**Implementation**:
```python
def roll_battle_loot_multiple(floor_index: int, num_drops: int = 1) -> List[str]:
    """Roll for multiple equipment drops."""
    drops = []
    for _ in range(num_drops):
        item = roll_battle_loot(floor_index)
        if item:
            drops.append(item)
    return drops
```

### 2. **Item Filtering by Floor/Biome** (High Priority)
**Current**: All items are available at all floors
**Suggestion**: Add min_floor/max_floor or biome tags to items
- Early floors get basic equipment
- Deeper floors unlock better gear
- Different biomes could have themed loot (e.g., fire-themed items in lava areas)

**Implementation**:
```python
# In ItemDef, add optional fields:
min_floor: Optional[int] = None
max_floor: Optional[int] = None
biome_tags: List[str] = field(default_factory=list)

# In _candidate_items():
def _candidate_items(floor_index: int = 1, biome: Optional[str] = None) -> List[ItemDef]:
    candidates = []
    for it in all_items():
        if it.slot in equipment_slots:
            # Filter by floor
            if it.min_floor and floor_index < it.min_floor:
                continue
            if it.max_floor and floor_index > it.max_floor:
                continue
            # Filter by biome
            if biome and it.biome_tags and biome not in it.biome_tags:
                continue
            candidates.append(it)
    return candidates
```

### 3. **Consumable Variety in Chests** (Medium Priority)
**Current**: Chests only drop equipment
**Suggestion**: Chests could sometimes contain consumables or mixed loot
- Small chests: 1 item (equipment or consumable)
- Large chests: 1-2 items (mix of equipment and consumables)
- Treasure chests: Guaranteed equipment + consumables

**Implementation**:
```python
def roll_chest_loot(floor_index: int, chest_type: str = "normal") -> List[str]:
    """Roll for chest loot, can include consumables."""
    loot = []
    
    # Equipment drop
    if random.random() < chest_drop_chance(floor_index):
        item = roll_battle_loot(floor_index)
        if item:
            loot.append(item)
    
    # Consumable drop (higher chance for treasure chests)
    consumable_chance = 0.3 if chest_type == "treasure" else 0.15
    if random.random() < consumable_chance:
        consumable = roll_battle_consumable(floor_index)
        if consumable:
            loot.append(consumable)
    
    return loot
```

### 4. **Drop Rate Configuration** (Low Priority)
**Current**: Drop chances are hardcoded
**Suggestion**: Make drop rates configurable via settings file
- Allow players/mods to adjust drop rates
- Different difficulty modes could have different rates
- Easy mode: higher drop rates, Hard mode: lower drop rates

**Implementation**:
```python
# In config/loot_settings.json:
{
    "battle_equipment_drop": {
        "base": 0.25,
        "floor_scaling": 0.04,
        "max": 0.5
    },
    "battle_consumable_drop": {
        "base": 0.30,
        "floor_scaling": 0.03,
        "max": 0.60
    }
}
```

### 5. **Loot Quality Scaling** (Medium Priority)
**Current**: Rarity scales with floor, but could be more granular
**Suggestion**: Add quality tiers within rarities
- Common items can be "worn" or "pristine"
- Floor depth affects not just rarity but also quality
- Higher floors = better stat rolls on same rarity items

**Note**: This might already be handled by the randomization system in inventory.add_item()

### 6. **Guaranteed Drops for Bosses** (High Priority)
**Current**: Bosses use same drop system as regular enemies
**Suggestion**: Bosses should have guaranteed or high-chance drops
- Bosses always drop at least 1 item (equipment or consumable)
- Bosses have higher chance for rare/epic items
- Boss-specific loot tables

**Implementation**:
```python
def roll_boss_loot(floor_index: int) -> List[str]:
    """Bosses always drop something good."""
    loot = []
    
    # Guaranteed equipment (higher rarity chance)
    item = roll_battle_loot(floor_index)
    if item is None:
        # Fallback: force a drop with better rarity weighting
        item = _force_drop(floor_index, min_rarity="uncommon")
    loot.append(item)
    
    # High chance for consumable
    if random.random() < 0.7:
        consumable = roll_battle_consumable(floor_index)
        if consumable:
            loot.append(consumable)
    
    return loot
```

### 7. **Loot Tables by Enemy Type** (Medium Priority)
**Current**: All enemies use same drop tables
**Suggestion**: Different enemy types could have themed loot
- Undead enemies drop more consumables (they don't need them)
- Humanoid enemies drop more equipment
- Beast enemies drop fewer items but more gold
- Mage enemies have higher chance for skill_power items

**Implementation**:
```python
def roll_battle_loot(floor_index: int, enemy_type: Optional[str] = None) -> Optional[str]:
    """Roll for loot with enemy-type modifiers."""
    # ... existing code ...
    
    # Apply enemy type modifiers
    if enemy_type == "undead":
        # Undead drop more consumables, less equipment
        if random.random() < 0.3:  # 30% chance to skip equipment
            return None
    elif enemy_type == "humanoid":
        # Humanoids drop better equipment
        for i, weight in enumerate(weights):
            if items[i].rarity in {"uncommon", "rare"}:
                weights[i] *= 1.3
    
    # ... rest of code ...
```

### 8. **Loot Preview/Tease** (Low Priority)
**Current**: Players don't know what they'll get
**Suggestion**: Show loot preview before opening chests
- "You see something shiny inside..."
- "The chest rattles with the sound of gold"
- Could add suspense and decision-making

### 9. **Loot Stacking/Grouping** (Low Priority)
**Current**: Each drop is a separate message
**Suggestion**: Group multiple drops into single message
- "You find a Rusty Sword and Small Health Potion among the remains."
- Cleaner UI, less message spam

**Implementation**: Already partially done in battle_orchestrator - just needs message formatting

### 10. **Drop Animation/Feedback** (Low Priority)
**Current**: Loot appears in messages only
**Suggestion**: Visual feedback when items drop
- Item icons appear on ground briefly
- Particles/effects for rare items
- Sound effects for different rarities

## Code Quality Improvements

### 1. **Type Safety**
- Add return type hints to all functions
- Use `List[str]` instead of `list[str]` for Python < 3.9 compatibility (already done)

### 2. **Error Handling**
- Add try/except for item definition lookups
- Handle edge cases (no items available, invalid floor_index)

### 3. **Documentation**
- Add more detailed docstrings
- Document the rarity weight formula
- Explain drop chance scaling

### 4. **Testing**
- Unit tests for drop chances
- Tests for rarity weighting
- Tests for floor scaling

## Priority Recommendations

**High Priority** (Do Soon):
1. Item filtering by floor/biome
2. Guaranteed drops for bosses
3. Better error handling

**Medium Priority** (Nice to Have):
1. Multiple item drops for large encounters
2. Consumables in chests
3. Loot tables by enemy type
4. Loot quality scaling

**Low Priority** (Polish):
1. Drop rate configuration
2. Loot preview/tease
3. Drop animations
4. Message grouping improvements

## Current System Strengths

✅ **Simple and understandable** - Easy to reason about drop chances
✅ **Floor scaling** - Rewards get better as you progress
✅ **Source differentiation** - Chests/shops feel different from battle drops
✅ **Extensible** - Easy to add new drop types or sources
✅ **Separate consumables** - Now properly separated from equipment

## Conclusion

The loot system is solid and functional. The main improvements would be:
1. Adding floor/biome filtering for better progression
2. Special handling for bosses
3. More variety in chest contents

The system is well-structured and easy to extend, so these improvements can be added incrementally without major refactoring.

