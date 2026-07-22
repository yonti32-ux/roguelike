from __future__ import annotations

import random
from typing import Optional, List, Dict

# Works both as part of the "systems" package and if run locally for testing
try:
    from .inventory import ItemDef, all_items
    from .consumables import ConsumableDef, all_consumables
except ImportError:  # fallback if not imported as a package
    from inventory import ItemDef, all_items
    from consumables import ConsumableDef, all_consumables


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
    Return all item defs that are valid for random drops.

    For now: all items that have slot in {weapon, armor, trinket}.
    Later we can add tags / min_floor / biome filters.
    """
    candidates: List[ItemDef] = []
    for it in all_items():
        if it.slot in ("weapon", "armor", "trinket"):
            candidates.append(it)
    return candidates


def _weighted_choice(items: List[ItemDef], weights: List[float]) -> Optional[ItemDef]:
    if not items:
        return None
    if len(items) == 1:
        return items[0]

    # random.choices is fine here, we only pick a single item.
    chosen = random.choices(items, weights=weights, k=1)[0]
    return chosen


def _weighted_choice_consumable(consumables: List[ConsumableDef], weights: List[float]) -> Optional[ConsumableDef]:
    """Weighted choice for consumables."""
    if not consumables:
        return None
    if len(consumables) == 1:
        return consumables[0]

    chosen = random.choices(consumables, weights=weights, k=1)[0]
    return chosen


# ----------------- Drop chances -----------------

def battle_drop_chance(floor_index: int) -> float:
    """
    Chance that *any* loot drops from a normal battle.

    Starts around 25% and scales up a bit with floor depth,
    capped so it never becomes guaranteed.
    """
    base = 0.25 + min(0.25, floor_index * 0.04)  # up to +25% at deeper floors
    return max(0.0, min(0.5, base))  # 25% -> 50%


def chest_drop_chance(floor_index: int) -> float:
    """
    Chance that a chest actually contains an item.

    For v1, chests are generous: mostly always have something.
    We still keep a small chance for "empty" or junk later.
    """
    base = 0.80 + min(0.15, floor_index * 0.02)  # up to +15%
    return max(0.0, min(0.95, base))  # 80% -> 95%


def chest_consumable_drop_chance(floor_index: int) -> float:
    """
    Chance that a consumable drops from a chest.
    
    Chests have a good chance of containing consumables.
    Starts at 50% and scales up to 75% at deeper floors.
    """
    base = 0.50 + min(0.25, floor_index * 0.04)  # up to +25% at deeper floors
    return max(0.0, min(0.75, base))  # 50% -> 75%


def battle_consumable_drop_chance(floor_index: int) -> float:
    """
    Chance that a consumable drops from a normal battle.
    
    Consumables drop more frequently than items since they're more common.
    Starts at 35% and scales up to 60% at deeper floors.
    """
    base = 0.35 + min(0.25, floor_index * 0.05)  # up to +25% at deeper floors
    return max(0.0, min(0.60, base))  # 35% -> 60%


def _candidate_consumables() -> List[ConsumableDef]:
    """
    Return all consumable defs that are valid for random drops.
    
    Focuses on basic consumables (common and uncommon rarity).
    """
    candidates: List[ConsumableDef] = []
    for cons in all_consumables():
        # Prioritize common and uncommon consumables for drops
        if cons.rarity.lower() in ("common", "uncommon"):
            candidates.append(cons)
    return candidates


# ----------------- Public API -----------------

def roll_battle_loot(floor_index: int) -> Optional[str]:
    """
    Roll for loot from a normal battle.
    
    Note: Items returned here can be randomized when actually created.
    The randomization happens at item creation time, not here.

    Returns:
        item_id (str) if something drops, or None if no loot this time.
    """
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


def roll_chest_loot(floor_index: int) -> Optional[str]:
    """
    Roll for loot from a chest.

    Returns:
        item_id (str) if the chest has something, or None for an empty chest.
    """
    # First: does this chest contain loot at all?
    if random.random() > chest_drop_chance(floor_index):
        return None

    items = _candidate_items()
    if not items:
        return None

    weights: List[float] = []
    for it in items:
        weights.append(_rarity_weight(it.rarity, floor_index, source="chest"))

    chosen = _weighted_choice(items, weights)
    return chosen.id if chosen is not None else None


def roll_battle_consumable(floor_index: int) -> Optional[str]:
    """
    Roll for a consumable drop from a normal battle.
    
    This is separate from item loot - consumables drop independently
    and more frequently to encourage their use.
    
    Returns:
        consumable_id (str) if something drops, or None if no consumable this time.
    """
    # First: decide if a consumable drops at all
    if random.random() > battle_consumable_drop_chance(floor_index):
        return None

    consumables = _candidate_consumables()
    if not consumables:
        return None

    # Weight by rarity - common consumables are more likely
    weights: List[float] = []
    for cons in consumables:
        # Common consumables get higher weight
        if cons.rarity.lower() == "common":
            weight = 70.0
        elif cons.rarity.lower() == "uncommon":
            weight = 30.0
        else:
            weight = 10.0
        weights.append(weight)

    chosen = _weighted_choice_consumable(consumables, weights)
    return chosen.id if chosen is not None else None


def roll_chest_consumable(floor_index: int) -> Optional[str]:
    """
    Roll for a consumable drop from a chest.
    
    This is separate from item loot - consumables drop independently
    from chests to provide more variety in rewards.
    
    Returns:
        consumable_id (str) if something drops, or None if no consumable this time.
    """
    # First: decide if a consumable drops at all
    if random.random() > chest_consumable_drop_chance(floor_index):
        return None

    consumables = _candidate_consumables()
    if not consumables:
        return None

    # Weight by rarity - common consumables are more likely
    weights: List[float] = []
    for cons in consumables:
        # Common consumables get higher weight
        if cons.rarity.lower() == "common":
            weight = 70.0
        elif cons.rarity.lower() == "uncommon":
            weight = 30.0
        else:
            weight = 10.0
        weights.append(weight)

    chosen = _weighted_choice_consumable(consumables, weights)
    return chosen.id if chosen is not None else None


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
