# systems/item_randomization.py
"""
Item randomization system: adds random stat variations to items when they drop.

This system allows items to have slight stat variations when found, making each
playthrough more interesting. Same item, but slightly different stats.

Features:
- Random stat bonuses/penalties based on rarity
- Configurable variation ranges
- Optional: prefix/suffix names for randomized items
- Integration with loot system
"""

from __future__ import annotations

from typing import Dict, Optional
import random

from .inventory import ItemDef, get_item_def


# ============================================================================
# Configuration
# ============================================================================

# Stat variation ranges by rarity (as percentage of base stat)
# Format: (min_variation, max_variation) as multipliers (0.9 = -10%, 1.1 = +10%)
STAT_VARIATION_RANGES: Dict[str, tuple[float, float]] = {
    "common": (0.95, 1.05),      # ±5% variation
    "uncommon": (0.90, 1.10),    # ±10% variation
    "rare": (0.85, 1.15),         # ±15% variation
    "epic": (0.80, 1.20),         # ±20% variation
    "legendary": (0.75, 1.25),    # ±25% variation
}

# Chance that an item gets randomized (0.0 to 1.0)
RANDOMIZATION_CHANCE = 0.3  # 30% of items get randomized

# Minimum stat change (to avoid tiny variations that don't matter)
MIN_STAT_CHANGE = {
    "attack": 1,           # At least ±1 attack
    "defense": 1,          # At least ±1 defense
    "max_hp": 2,           # At least ±2 HP
    "max_stamina": 2,      # At least ±2 stamina
    "max_mana": 2,         # At least ±2 mana
    "skill_power": 0.05,   # At least ±0.05 skill power
}

# Prefixes/suffixes for randomized items (optional flavor)
RANDOM_PREFIXES = [
    "Fine", "Superior", "Exceptional", "Masterwork", "Flawless",
    "Tempered", "Reinforced", "Blessed", "Cursed", "Weathered"
]

RANDOM_SUFFIXES = [
    "of Power", "of Precision", "of Protection", "of Endurance",
    "of the Bear", "of the Wolf", "of the Eagle", "of the Serpent"
]


# ============================================================================
# Core Randomization
# ============================================================================

def randomize_item(item_id: str, floor_index: int = 1) -> Optional[ItemDef]:
    """
    Create a randomized version of an item with stat variations.
    
    Args:
        item_id: Base item ID
        floor_index: Current floor (for potential floor-based bonuses)
    
    Returns:
        New ItemDef with randomized stats, or None if item not found
    """
    base_item = get_item_def(item_id)
    if base_item is None:
        return None
    
    # Check if we should randomize this item
    if random.random() > RANDOMIZATION_CHANCE:
        return base_item  # Return original, no randomization
    
    # Get variation range for this rarity
    rarity = base_item.rarity.lower()
    variation_range = STAT_VARIATION_RANGES.get(rarity, (0.95, 1.05))
    min_mult, max_mult = variation_range
    
    # Randomize each stat
    new_stats: Dict[str, float] = {}
    for stat_name, base_value in base_item.stats.items():
        # Apply random multiplier
        multiplier = random.uniform(min_mult, max_mult)
        new_value = base_value * multiplier
        
        # Round to appropriate precision
        if stat_name in ("skill_power",):
            new_value = round(new_value, 2)
        else:
            new_value = round(new_value)
        
        # Apply minimum change requirement
        min_change = MIN_STAT_CHANGE.get(stat_name, 0)
        if abs(new_value - base_value) < min_change:
            # Ensure at least minimum change (random direction)
            direction = 1 if random.random() > 0.5 else -1
            new_value = base_value + (min_change * direction)
            if stat_name in ("skill_power",):
                new_value = round(new_value, 2)
            else:
                new_value = round(new_value)
        
        # Ensure non-negative stats
        if stat_name in ("attack", "defense", "max_hp", "max_stamina", "max_mana"):
            new_value = max(1, int(new_value))
        else:
            new_value = max(0.0, float(new_value))
        
        new_stats[stat_name] = new_value
    
    # Create new name (with optional prefix/suffix)
    new_name = base_item.name
    if random.random() < 0.1:
        if random.random() > 0.5:
            # Add prefix
            prefix = random.choice(RANDOM_PREFIXES)
            new_name = f"{prefix} {base_item.name}"
        else:
            # Add suffix
            suffix = random.choice(RANDOM_SUFFIXES)
            new_name = f"{base_item.name} {suffix}"
    
    # Create a new ItemDef instance (since it's frozen, we can't modify it)
    randomized = ItemDef(
        id=base_item.id,
        name=new_name,
        slot=base_item.slot,
        description=base_item.description,
        stats=new_stats,
        rarity=base_item.rarity,
        value=base_item.value,
    )
    
    return randomized


def randomize_item_stats(item_def: ItemDef, floor_index: int = 1) -> ItemDef:
    """
    Randomize stats of an existing ItemDef (in-place modification).
    
    This is an alternative to randomize_item() that modifies the original.
    Use this if you want to modify an item you already have.
    
    Args:
        item_def: ItemDef to randomize
        floor_index: Current floor
    
    Returns:
        Modified ItemDef (same object)
    """
    # Check if we should randomize
    if random.random() > RANDOMIZATION_CHANCE:
        return item_def
    
    rarity = item_def.rarity.lower()
    variation_range = STAT_VARIATION_RANGES.get(rarity, (0.95, 1.05))
    min_mult, max_mult = variation_range
    
    # Randomize each stat
    for stat_name, base_value in list(item_def.stats.items()):
        multiplier = random.uniform(min_mult, max_mult)
        new_value = base_value * multiplier
        
        # Round appropriately
        if stat_name in ("skill_power",):
            new_value = round(new_value, 2)
        else:
            new_value = round(new_value)
        
        # Apply minimum change
        min_change = MIN_STAT_CHANGE.get(stat_name, 0)
        if abs(new_value - base_value) < min_change:
            direction = 1 if random.random() > 0.5 else -1
            new_value = base_value + (min_change * direction)
            if stat_name in ("skill_power",):
                new_value = round(new_value, 2)
            else:
                new_value = round(new_value)
        
        # Ensure non-negative
        if stat_name in ("attack", "defense", "max_hp", "max_stamina", "max_mana"):
            new_value = max(1, int(new_value))
        else:
            new_value = max(0.0, float(new_value))
        
        item_def.stats[stat_name] = new_value
    
    return item_def


# ============================================================================
# Integration Helpers
# ============================================================================

def get_randomized_item_id(item_id: str, floor_index: int = 1) -> str:
    """
    Get a randomized item ID for use in the game.
    
    Since we can't easily store randomized ItemDefs in the registry,
    this returns the base item_id. The actual randomization happens
    when the item is created/used.
    
    For now, this is a placeholder. In a full implementation, you might:
    - Store randomized items in a separate registry
    - Use a special ID format like "item_id:random_seed"
    - Apply randomization at loot generation time
    
    Args:
        item_id: Base item ID
        floor_index: Current floor
    
    Returns:
        Item ID (same as input for now)
    """
    return item_id


def should_randomize_item(item_id: str) -> bool:
    """
    Check if an item should be randomized (based on chance).
    
    Args:
        item_id: Item ID to check
    
    Returns:
        True if item should be randomized
    """
    return random.random() <= RANDOMIZATION_CHANCE

