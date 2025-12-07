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


# ----------------- Public API -----------------

def roll_battle_loot(floor_index: int) -> Optional[str]:
    """
    Roll for loot from a normal battle.

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


def get_shop_stock_for_floor(floor_index: int, max_items: int = 6) -> List[str]:
    """
    Build a list of item_ids that a merchant on this floor offers.

    For now:
    - Use all equippable items.
    - Slightly bias towards higher-rarity items on deeper floors.
    - Limit to ``max_items`` unique choices.

    This is intentionally generous: the limiting factor should be the
    player's gold, not the merchant's list being empty.
    """
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
