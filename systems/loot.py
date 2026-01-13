from __future__ import annotations

import random
from typing import Optional, List, Dict

# Works both as part of the "systems" package and if run locally for testing
try:
    from .inventory import ItemDef, all_items
except ImportError:  # fallback if not imported as a package
    from inventory import ItemDef, all_items


# ----------------- Rarity weighting -----------------

# Base rarity weights. These are *relative* – we just use ratios.
RARITY_WEIGHTS: Dict[str, float] = {
    "common": 60.0,
    "uncommon": 30.0,
    "rare": 8.0,
    "epic": 2.0,
    "legendary": 0.5,
}


def _rarity_weight(rarity: str, floor_index: int, source: str) -> float:
    """
    Compute a weight for an item rarity, taking floor depth and source into account.

    - Deeper floors slightly boost rarer items.
    - Chests are more generous than battle drops.
    """
    base = RARITY_WEIGHTS.get(rarity.lower(), 10.0)

    depth_factor = 1.0 + max(0, floor_index - 1) * 0.12  # +12% per floor after 1
    if rarity.lower() in {"rare", "epic", "legendary"}:
        base *= depth_factor

    # Chests (and shop selection) are more likely to show the good stuff
    if source in {"chest", "shop"} and rarity.lower() in {"uncommon", "rare", "epic", "legendary"}:
        base *= 1.5

    return base


def _candidate_items() -> List[ItemDef]:
    """
    Return all item defs that are valid for random equipment drops.

    Includes all equipment slots: weapon, helmet, armor, gloves, boots, shield, cloak, ring, amulet.
    Excludes consumables (they have their own drop function).
    """
    candidates: List[ItemDef] = []
    equipment_slots = {
        "weapon", "helmet", "armor", "gloves", "boots", 
        "shield", "cloak", "ring", "amulet"
    }
    for it in all_items():
        if it.slot in equipment_slots:
            candidates.append(it)
    return candidates


def _candidate_consumables() -> List[ItemDef]:
    """
    Return all consumable item defs that are valid for random drops.
    """
    candidates: List[ItemDef] = []
    for it in all_items():
        if it.slot == "consumable":
            candidates.append(it)
    return candidates


def _weighted_choice(items: List[ItemDef], weights: List[float]) -> Optional[ItemDef]:
    """
    Choose a random item using weighted selection.
    
    Args:
        items: List of items to choose from
        weights: Corresponding weights for each item
    
    Returns:
        Selected item or None if invalid input
    """
    try:
        if not items or not weights:
            return None
        if len(items) != len(weights):
            return None  # Mismatched lists
        if len(items) == 1:
            return items[0]
        
        # Filter out zero/negative weights
        valid_items = []
        valid_weights = []
        for item, weight in zip(items, weights):
            if weight > 0:
                valid_items.append(item)
                valid_weights.append(weight)
        
        if not valid_items:
            return None
        
        # random.choices is fine here, we only pick a single item.
        chosen = random.choices(valid_items, weights=valid_weights, k=1)[0]
        return chosen
    except Exception:
        # Error handling: return None on any error
        return None


def _force_drop(floor_index: int, min_rarity: str = "common") -> Optional[str]:
    """
    Force a drop with minimum rarity requirement (for bosses/guaranteed drops).
    
    Args:
        floor_index: Current floor number
        min_rarity: Minimum rarity to drop ("common", "uncommon", "rare", "epic", "legendary")
    
    Returns:
        item_id or None if no items match criteria
    """
    try:
        items = _candidate_items()
        if not items:
            return None
        
        # Filter by minimum rarity
        rarity_order = ["common", "uncommon", "rare", "epic", "legendary"]
        min_rarity_idx = rarity_order.index(min_rarity.lower()) if min_rarity.lower() in rarity_order else 0
        
        eligible_items = [
            it for it in items
            if it.rarity.lower() in rarity_order
            and rarity_order.index(it.rarity.lower()) >= min_rarity_idx
        ]
        
        if not eligible_items:
            # Fallback: use all items if none match rarity requirement
            eligible_items = items
        
        # Weight towards better rarities
        weights: List[float] = []
        for it in eligible_items:
            base_weight = _rarity_weight(it.rarity, floor_index, source="battle")
            # Boost higher rarities for forced drops
            if it.rarity.lower() in {"rare", "epic", "legendary"}:
                base_weight *= 2.0
            weights.append(base_weight)
        
        chosen = _weighted_choice(eligible_items, weights)
        return chosen.id if chosen is not None else None
    except Exception:
        # Error handling: try to get any item as fallback
        try:
            items = _candidate_items()
            if items:
                return items[0].id
        except Exception:
            pass
        return None


def roll_boss_loot(floor_index: int, is_final_boss: bool = False) -> List[str]:
    """
    Roll for boss loot. Bosses always drop something good.
    
    Args:
        floor_index: Current floor number
        is_final_boss: If True, this is a final boss (better drops)
    
    Returns:
        List of item_ids dropped (guaranteed at least 1 item)
    """
    loot: List[str] = []
    
    try:
        # Bosses always drop at least 1 equipment item
        # Try normal drop first
        item = roll_battle_loot(floor_index)
        
        # If no drop, force one with minimum rarity
        if item is None:
            min_rarity = "uncommon" if is_final_boss else "common"
            item = _force_drop(floor_index, min_rarity=min_rarity)
        
        if item is not None:
            loot.append(item)
        
        # Bosses have high chance for additional equipment (especially final bosses)
        additional_chance = 0.4 if is_final_boss else 0.25
        if random.random() <= additional_chance:
            additional_item = roll_battle_loot(floor_index)
            if additional_item is not None and additional_item not in loot:
                loot.append(additional_item)
        
        # Bosses have high chance for consumables
        consumable_chance = 0.7 if is_final_boss else 0.5
        if random.random() <= consumable_chance:
            consumable = roll_battle_consumable(floor_index)
            if consumable is not None:
                loot.append(consumable)
        
        # Final bosses might get a second consumable
        if is_final_boss and random.random() <= 0.3:
            consumable2 = roll_battle_consumable(floor_index)
            if consumable2 is not None and consumable2 not in loot:
                loot.append(consumable2)
        
        return loot
    except Exception:
        # Error handling: try to return at least one item
        try:
            fallback_item = _force_drop(floor_index, min_rarity="common")
            if fallback_item:
                return [fallback_item]
        except Exception:
            pass
        return []


# ----------------- Drop chances -----------------

def battle_drop_chance(floor_index: int) -> float:
    """
    Chance that *any* equipment loot drops from a normal battle.

    Starts around 25% and scales up a bit with floor depth,
    capped so it never becomes guaranteed.
    """
    base = 0.25 + min(0.25, floor_index * 0.04)  # up to +25% at deeper floors
    return max(0.0, min(0.5, base))  # 25% -> 50%


def consumable_drop_chance(floor_index: int) -> float:
    """
    Chance that a consumable drops from a normal battle.
    
    Consumables are more common than equipment but not guaranteed.
    Starts around 30% and scales up with floor depth.
    """
    base = 0.30 + min(0.20, floor_index * 0.03)  # up to +20% at deeper floors
    return max(0.0, min(0.60, base))  # 30% -> 60%


def chest_drop_chance(floor_index: int) -> float:
    """
    Chance that a chest actually contains an item.

    For v1, chests are generous: mostly always have something.
    We still keep a small chance for "empty" or junk later.
    """
    base = 0.80 + min(0.15, floor_index * 0.02)  # up to +15%
    return max(0.0, min(0.95, base))  # 80% -> 95%


# ----------------- Public API -----------------

def roll_battle_loot(floor_index: int) -> Optional[str]:
    """
    Roll for equipment loot from a normal battle.
    
    Note: Items returned here can be randomized when actually created.
    The randomization happens at item creation time, not here.

    Returns:
        item_id (str) if something drops, or None if no loot this time.
    """
    try:
        # First: decide if anything drops at all
        if random.random() > battle_drop_chance(floor_index):
            return None

        items = _candidate_items()
        if not items:
            return None

        weights: List[float] = []
        for it in items:
            weights.append(_rarity_weight(it.rarity, floor_index, source="battle"))

        chosen = _weighted_choice(items, weights)
        return chosen.id if chosen is not None else None
    except Exception:
        # Error handling: if anything goes wrong, return None (no drop)
        return None


def roll_battle_loot_multiple(floor_index: int, num_drops: int = 1, encounter_size: int = 1) -> List[str]:
    """
    Roll for multiple equipment drops from a battle.
    
    Larger encounters have higher chance for multiple drops.
    
    Args:
        floor_index: Current floor number
        num_drops: Base number of drops to attempt
        encounter_size: Number of enemies in encounter (affects drop chance)
    
    Returns:
        List of item_ids that dropped (can be empty, can have multiple)
    """
    drops: List[str] = []
    
    try:
        # Scale drop chance based on encounter size
        # Larger encounters = better chance for multiple drops
        size_multiplier = 1.0 + (encounter_size - 1) * 0.15  # +15% per extra enemy
        adjusted_chance = min(0.75, battle_drop_chance(floor_index) * size_multiplier)
        
        items = _candidate_items()
        if not items:
            return drops
        
        # Try to get multiple drops
        for _ in range(num_drops):
            if random.random() <= adjusted_chance:
                item_id = roll_battle_loot(floor_index)
                if item_id is not None:
                    drops.append(item_id)
                    # Slightly reduce chance for subsequent drops
                    adjusted_chance *= 0.7
        
        return drops
    except Exception:
        # Error handling: return empty list on error
        return []


def roll_battle_consumable(floor_index: int) -> Optional[str]:
    """
    Roll for consumable loot from a normal battle.
    
    Consumables have a separate drop chance from equipment, so both can drop.
    
    Returns:
        consumable_id (str) if a consumable drops, or None if no consumable this time.
    """
    try:
        # First: decide if a consumable drops
        if random.random() > consumable_drop_chance(floor_index):
            return None

        consumables = _candidate_consumables()
        if not consumables:
            return None

        # Consumables use simpler weighting - prefer common/uncommon
        weights: List[float] = []
        for consumable in consumables:
            base_weight = _rarity_weight(consumable.rarity, floor_index, source="battle")
            # Slightly boost consumables for battle drops (they're useful!)
            base_weight *= 1.2
            weights.append(base_weight)

        chosen = _weighted_choice(consumables, weights)
        return chosen.id if chosen is not None else None
    except Exception:
        # Error handling: return None on error
        return None


def roll_chest_loot(floor_index: int, chest_type: str = "normal") -> List[str]:
    """
    Roll for loot from a chest. Can return both equipment and consumables.
    
    Args:
        floor_index: Current floor number
        chest_type: Type of chest ("normal", "treasure", "small") - affects drop rates
    
    Returns:
        List of item_ids found in the chest (can be empty, can have multiple)
    """
    loot: List[str] = []
    
    try:
        # Equipment drop chance (higher for treasure chests)
        equipment_chance = chest_drop_chance(floor_index)
        if chest_type == "treasure":
            equipment_chance = min(0.98, equipment_chance + 0.15)  # Treasure chests are more generous
        elif chest_type == "small":
            equipment_chance = max(0.5, equipment_chance - 0.2)  # Small chests are less generous
        
        if random.random() <= equipment_chance:
            items = _candidate_items()
            if items:
                weights: List[float] = []
                for it in items:
                    weights.append(_rarity_weight(it.rarity, floor_index, source="chest"))
                
                chosen = _weighted_choice(items, weights)
                if chosen is not None:
                    loot.append(chosen.id)
        
        # Consumable drop chance (separate from equipment)
        consumable_chance = 0.15  # Base 15% chance
        if chest_type == "treasure":
            consumable_chance = 0.40  # Treasure chests have higher consumable chance
        elif chest_type == "small":
            consumable_chance = 0.25  # Small chests might have consumables instead of equipment
        
        if random.random() <= consumable_chance:
            consumable = roll_battle_consumable(floor_index)
            if consumable is not None:
                loot.append(consumable)
        
        return loot
    except Exception:
        # Error handling: return empty list on error
        return []


def get_shop_stock_for_floor(floor_index: int, max_items: int = 6) -> List[str]:
    """
    Build a list of item_ids that a merchant on this floor offers.

    This function now delegates to the economy system for merchant stock generation,
    which provides floor-aware scaling and better item selection.

    Args:
        floor_index: Current floor
        max_items: Maximum items to stock (default 6)

    Returns:
        List of item IDs the merchant has in stock
    """
    try:
        from .economy import generate_merchant_stock
        # Use economy system for better floor-aware stock generation
        return generate_merchant_stock(floor_index, max_items=max_items)
    except ImportError:
        # Fallback to original implementation if economy system not available
        items = _candidate_items()
        if not items or max_items <= 0:
            return []

        # Cap max_items so we don't try to pick more than exist.
        max_items = min(max_items, len(items))

        # Build weights biased similarly to chest loot, but using a "shop" source
        weighted_pool = list(items)
        weights = [
            _rarity_weight(it.rarity, floor_index, source="shop") for it in weighted_pool
        ]

        chosen_ids: List[str] = []

        # We want unique items, so we sample without replacement using the weights.
        while weighted_pool and len(chosen_ids) < max_items:
            chosen = _weighted_choice(weighted_pool, weights)
            if chosen is None:
                break
            chosen_ids.append(chosen.id)
            # Remove that item from the pool so we don't offer duplicates.
            idx = weighted_pool.index(chosen)
            weighted_pool.pop(idx)
            weights.pop(idx)

        return chosen_ids
