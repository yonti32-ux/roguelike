# systems/economy.py
"""
Economy system: dynamic pricing, merchant inventory, and gold sinks.

Features:
- Dynamic item value calculation based on stats, rarity, and floor depth
- Shop pricing with floor scaling and merchant markup
- Sell price calculation (typically 50% of buy price)
- Merchant inventory generation
- Gold sink services (repair, upgrade, identify) - for future expansion
"""

from __future__ import annotations

from typing import Optional, List, Dict
import math

from .inventory import ItemDef, get_item_def


# ============================================================================
# Constants & Configuration
# ============================================================================

# Base value multipliers by rarity
RARITY_VALUE_MULTIPLIERS: Dict[str, float] = {
    "common": 1.0,
    "uncommon": 2.5,
    "rare": 6.0,
    "epic": 15.0,
    "legendary": 40.0,
}

# Stat value weights (how much each stat point is worth in gold)
STAT_VALUE_WEIGHTS: Dict[str, float] = {
    "attack": 8.0,           # Attack is valuable
    "defense": 6.0,          # Defense is valuable but slightly less
    "max_hp": 2.0,           # HP is useful but cheaper per point
    "skill_power": 12.0,     # Skill power is premium
    "max_stamina": 3.0,      # Stamina is moderately valuable
    "max_mana": 4.0,          # Mana is moderately valuable
}

# Shop pricing configuration
SHOP_MARKUP_MULTIPLIER = 1.5  # Merchants sell at 150% of base value
SELL_PRICE_RATIO = 0.5        # Players sell at 50% of base value
MIN_SHOP_PRICE = 1           # Minimum price for any item
FLOOR_SCALING_FACTOR = 0.15   # +15% price per floor after floor 1

# Merchant inventory configuration
MERCHANT_BASE_STOCK_SIZE = 6
MERCHANT_FLOOR_BONUS = 0.3    # +30% stock size per floor (capped)


# ============================================================================
# Core Value Calculation
# ============================================================================

def calculate_item_base_value(item_def: ItemDef, floor_index: int = 1) -> int:
    """
    Calculate the base gold value of an item based on its stats and rarity.
    
    Formula:
    1. Sum all stat bonuses weighted by their value
    2. Multiply by rarity multiplier
    3. Apply floor scaling (deeper floors = slightly more valuable)
    4. Round to integer
    
    Args:
        item_def: The item definition
        floor_index: Current floor (for scaling)
    
    Returns:
        Base gold value (minimum 1)
    """
    if item_def.value > 0:
        # If item has explicit value, use it as base but still apply floor scaling
        base = item_def.value
    else:
        # Calculate from stats
        stat_value = 0.0
        for stat_name, stat_amount in item_def.stats.items():
            weight = STAT_VALUE_WEIGHTS.get(stat_name, 1.0)
            stat_value += stat_amount * weight
        
        # Apply rarity multiplier
        rarity_mult = RARITY_VALUE_MULTIPLIERS.get(
            item_def.rarity.lower(), 
            RARITY_VALUE_MULTIPLIERS["common"]
        )
        base = stat_value * rarity_mult
    
    # Floor scaling: items on deeper floors are slightly more valuable
    # (represents scarcity and demand)
    floor_bonus = 1.0 + max(0, floor_index - 1) * FLOOR_SCALING_FACTOR
    
    # Minimum value of 1 gold
    final_value = max(1, int(base * floor_bonus))
    
    return final_value


def calculate_shop_buy_price(item_def: ItemDef, floor_index: int = 1) -> int:
    """
    Calculate the price a merchant charges for an item (buy price).
    
    Merchants apply a markup over base value.
    
    Args:
        item_def: The item definition
        floor_index: Current floor
    
    Returns:
        Price in gold (minimum MIN_SHOP_PRICE)
    """
    base_value = calculate_item_base_value(item_def, floor_index)
    buy_price = max(MIN_SHOP_PRICE, int(base_value * SHOP_MARKUP_MULTIPLIER))
    return buy_price


def calculate_shop_sell_price(item_def: ItemDef, floor_index: int = 1) -> int:
    """
    Calculate the price a merchant pays for an item (sell price).
    
    Merchants typically pay 50% of base value (not buy price).
    
    Args:
        item_def: The item definition
        floor_index: Current floor
    
    Returns:
        Price in gold (minimum 1)
    """
    base_value = calculate_item_base_value(item_def, floor_index)
    sell_price = max(1, int(base_value * SELL_PRICE_RATIO))
    return sell_price


# ============================================================================
# Merchant Inventory Generation
# ============================================================================

def generate_merchant_stock(
    floor_index: int,
    max_items: Optional[int] = None,
    prefer_rarity: Optional[str] = None
) -> List[str]:
    """
    Generate a merchant's stock list for a given floor.
    
    This is an economy-aware version that considers:
    - Floor depth (deeper floors get better items)
    - Stock size scaling
    - Optional rarity preference
    
    Args:
        floor_index: Current floor
        max_items: Maximum items to stock (None = auto-calculate)
        prefer_rarity: Optional rarity to prefer ("common", "rare", etc.)
    
    Returns:
        List of item IDs the merchant has in stock
    """
    from .loot import _candidate_items, _rarity_weight, _weighted_choice
    
    # Calculate stock size
    if max_items is None:
        base_size = MERCHANT_BASE_STOCK_SIZE
        floor_bonus = int(base_size * MERCHANT_FLOOR_BONUS * (floor_index - 1))
        max_items = base_size + floor_bonus
        max_items = max(3, min(max_items, 12))  # Clamp between 3 and 12
    
    # Get candidate items
    candidates = _candidate_items()
    if not candidates or max_items <= 0:
        return []
    
    # Build weighted pool
    weighted_pool = list(candidates)
    weights = []
    
    for item in weighted_pool:
        # Base weight from rarity and floor
        base_weight = _rarity_weight(item.rarity, floor_index, source="shop")
        
        # Boost if it matches preferred rarity
        if prefer_rarity and item.rarity.lower() == prefer_rarity.lower():
            base_weight *= 2.0
        
        weights.append(base_weight)
    
    # Sample without replacement
    chosen_ids: List[str] = []
    
    while weighted_pool and len(chosen_ids) < max_items:
        chosen = _weighted_choice(weighted_pool, weights)
        if chosen is None:
            break
        
        chosen_ids.append(chosen.id)
        
        # Remove from pool
        idx = weighted_pool.index(chosen)
        weighted_pool.pop(idx)
        weights.pop(idx)
    
    return chosen_ids


# ============================================================================
# Gold Sink Services (Future Expansion)
# ============================================================================

def calculate_repair_cost(
    item_def: ItemDef,
    durability_lost: float = 1.0,
    floor_index: int = 1
) -> int:
    """
    Calculate cost to repair an item.
    
    Repair cost is based on item value and how much durability was lost.
    This is a placeholder for future durability system.
    
    Args:
        item_def: The item to repair
        durability_lost: Fraction of durability lost (0.0 to 1.0)
        floor_index: Current floor
    
    Returns:
        Repair cost in gold
    """
    base_value = calculate_item_base_value(item_def, floor_index)
    repair_cost = max(1, int(base_value * durability_lost * 0.3))  # 30% of value per full repair
    return repair_cost


def calculate_upgrade_cost(
    item_def: ItemDef,
    upgrade_level: int = 1,
    floor_index: int = 1
) -> int:
    """
    Calculate cost to upgrade an item.
    
    Upgrade cost scales exponentially with upgrade level.
    This is a placeholder for future upgrade system.
    
    Args:
        item_def: The item to upgrade
        upgrade_level: Target upgrade level (1 = first upgrade)
        floor_index: Current floor
    
    Returns:
        Upgrade cost in gold
    """
    base_value = calculate_item_base_value(item_def, floor_index)
    # Exponential scaling: 1st upgrade = 50% of value, 2nd = 100%, 3rd = 200%, etc.
    cost_multiplier = 0.5 * (2 ** (upgrade_level - 1))
    upgrade_cost = max(1, int(base_value * cost_multiplier))
    return upgrade_cost


def calculate_identify_cost(
    item_def: ItemDef,
    floor_index: int = 1
) -> int:
    """
    Calculate cost to identify an unknown item.
    
    Identification cost is a small fraction of item value.
    This is a placeholder for future identification system.
    
    Args:
        item_def: The item to identify
        floor_index: Current floor
    
    Returns:
        Identification cost in gold
    """
    base_value = calculate_item_base_value(item_def, floor_index)
    identify_cost = max(1, int(base_value * 0.1))  # 10% of value
    return identify_cost


# ============================================================================
# Utility Functions
# ============================================================================

def get_item_price_info(item_id: str, floor_index: int = 1) -> Dict[str, int]:
    """
    Get comprehensive pricing information for an item.
    
    Returns a dict with:
    - base_value: Calculated base value
    - buy_price: Shop buy price
    - sell_price: Shop sell price
    
    Args:
        item_id: Item ID
        floor_index: Current floor
    
    Returns:
        Dict with price information
    """
    item_def = get_item_def(item_id)
    if item_def is None:
        return {
            "base_value": 0,
            "buy_price": 0,
            "sell_price": 0,
        }
    
    return {
        "base_value": calculate_item_base_value(item_def, floor_index),
        "buy_price": calculate_shop_buy_price(item_def, floor_index),
        "sell_price": calculate_shop_sell_price(item_def, floor_index),
    }


def format_price(price: int) -> str:
    """
    Format a price for display.
    
    Args:
        price: Price in gold
    
    Returns:
        Formatted string (e.g., "50 gold", "1,234 gold")
    """
    if price <= 0:
        return "0 gold"
    
    # Add commas for large numbers
    price_str = f"{price:,}" if price >= 1000 else str(price)
    return f"{price_str} gold"

