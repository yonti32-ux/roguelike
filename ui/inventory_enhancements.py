"""
Inventory UI enhancements: filtering, sorting, search, and stat comparisons.

This module provides utilities for enhanced inventory management:
- Filtering by slot, rarity, equipped status
- Sorting by name, rarity, stat value
- Search functionality
- Stat comparison calculations
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Dict, Tuple, Callable
from enum import Enum

if TYPE_CHECKING:
    from engine.core.game import Game
    from systems.inventory import ItemDef, Inventory


class FilterMode(Enum):
    """Inventory filter modes."""
    ALL = "all"
    WEAPON = "weapon"
    ARMOR = "armor"
    TRINKET = "trinket"
    CONSUMABLE = "consumable"
    MISC = "misc"
    EQUIPPED = "equipped"
    UNEQUIPPED = "unequipped"


class SortMode(Enum):
    """Inventory sort modes."""
    DEFAULT = "default"  # By slot, then by name
    NAME = "name"
    RARITY = "rarity"
    ATTACK = "attack"
    DEFENSE = "defense"
    HP = "hp"


def filter_items(
    items: List[str],
    filter_mode: FilterMode,
    inventory: "Inventory",
    all_equipped: Dict[str, List[Tuple[str, str]]],
) -> List[str]:
    """
    Filter items based on the current filter mode.
    
    Args:
        items: List of item IDs
        filter_mode: Current filter mode
        inventory: Inventory instance
        all_equipped: Dict mapping item_id -> list of (character_name, slot) tuples
    
    Returns:
        Filtered list of item IDs
    """
    if filter_mode == FilterMode.ALL:
        return items
    
    filtered: List[str] = []
    
    for item_id in items:
        # Use inventory's method to resolve randomized items
        item_def = inventory._get_item_def(item_id) if hasattr(inventory, "_get_item_def") else None
        if item_def is None:
            if filter_mode == FilterMode.MISC:
                filtered.append(item_id)
            continue
        
        # Slot-based filtering
        if filter_mode == FilterMode.WEAPON and item_def.slot == "weapon":
            filtered.append(item_id)
        elif filter_mode == FilterMode.ARMOR and item_def.slot == "armor":
            filtered.append(item_id)
        elif filter_mode == FilterMode.TRINKET and item_def.slot == "trinket":
            filtered.append(item_id)
        elif filter_mode == FilterMode.CONSUMABLE and item_def.slot == "consumable":
            filtered.append(item_id)
        elif filter_mode == FilterMode.MISC and (item_def.slot == "misc" or not item_def.slot):
            filtered.append(item_id)
        
        # Equipped status filtering
        elif filter_mode == FilterMode.EQUIPPED:
            if item_id in all_equipped:
                filtered.append(item_id)
        elif filter_mode == FilterMode.UNEQUIPPED:
            if item_id not in all_equipped:
                filtered.append(item_id)
    
    return filtered


def sort_items(
    items: List[str],
    sort_mode: SortMode,
    inventory: Optional["Inventory"] = None,
) -> List[str]:
    """
    Sort items based on the current sort mode.
    
    Args:
        items: List of item IDs
        sort_mode: Current sort mode
        inventory: Optional inventory instance for resolving randomized items
    
    Returns:
        Sorted list of item IDs
    """
    if sort_mode == SortMode.DEFAULT:
        # Default: group by slot, then by name
        items_by_slot: Dict[str, List[str]] = {}
        for item_id in items:
            # Use inventory's method if available, otherwise fall back to base
            if inventory and hasattr(inventory, "_get_item_def"):
                item_def = inventory._get_item_def(item_id)
            else:
                from systems.inventory import get_item_def
                item_def = get_item_def(item_id)
            slot = item_def.slot if item_def else "misc"
            if slot not in items_by_slot:
                items_by_slot[slot] = []
            items_by_slot[slot].append(item_id)
        
        # Sort within each slot
        slot_order = ["weapon", "armor", "trinket", "consumable", "misc"]
        result: List[str] = []
        for slot in slot_order:
            if slot in items_by_slot:
                result.extend(sorted(items_by_slot[slot], key=lambda x: _get_item_name(x, inventory)))
        # Add any remaining slots
        for slot in sorted(items_by_slot.keys()):
            if slot not in slot_order:
                result.extend(sorted(items_by_slot[slot], key=lambda x: _get_item_name(x, inventory)))
        return result
    
    # Sort by name
    if sort_mode == SortMode.NAME:
        return sorted(items, key=lambda x: _get_item_name(x, inventory))
    
    # Sort by rarity (rarity order: common < uncommon < rare < epic < legendary)
    if sort_mode == SortMode.RARITY:
        rarity_order = {"common": 0, "uncommon": 1, "rare": 2, "epic": 3, "legendary": 4}
        return sorted(
            items,
            key=lambda x: (
                rarity_order.get(_get_item_rarity(x, inventory), -1),
                _get_item_name(x, inventory)
            ),
            reverse=True  # Higher rarity first
        )
    
    # Sort by stat value
    if sort_mode == SortMode.ATTACK:
        return sorted(
            items,
            key=lambda x: _get_item_stat(x, "attack", inventory),
            reverse=True
        )
    
    if sort_mode == SortMode.DEFENSE:
        return sorted(
            items,
            key=lambda x: _get_item_stat(x, "defense", inventory),
            reverse=True
        )
    
    if sort_mode == SortMode.HP:
        return sorted(
            items,
            key=lambda x: _get_item_stat(x, "max_hp", inventory),
            reverse=True
        )
    
    return items


def search_items(items: List[str], search_query: str, inventory: Optional["Inventory"] = None) -> List[str]:
    """
    Filter items by search query (searches in item name).
    
    Args:
        items: List of item IDs
        search_query: Search string (case-insensitive)
        inventory: Optional inventory instance for resolving randomized items
    
    Returns:
        Filtered list of item IDs matching the search query
    """
    if not search_query:
        return items
    
    query_lower = search_query.lower()
    filtered: List[str] = []
    
    for item_id in items:
        # Use inventory's method if available, otherwise fall back to base
        if inventory and hasattr(inventory, "_get_item_def"):
            item_def = inventory._get_item_def(item_id)
        else:
            from systems.inventory import get_item_def
            item_def = get_item_def(item_id)
        if item_def is None:
            # Search in item ID if no definition
            if query_lower in item_id.lower():
                filtered.append(item_id)
        else:
            # Search in item name
            if query_lower in item_def.name.lower():
                filtered.append(item_id)
            # Also search in description
            elif item_def.description and query_lower in item_def.description.lower():
                filtered.append(item_id)
    
    return filtered


def _get_item_name(item_id: str, inventory: Optional["Inventory"] = None) -> str:
    """Get item name for sorting."""
    if inventory and hasattr(inventory, "_get_item_def"):
        item_def = inventory._get_item_def(item_id)
    else:
        from systems.inventory import get_item_def
        item_def = get_item_def(item_id)
    return item_def.name if item_def else item_id


def _get_item_rarity(item_id: str, inventory: Optional["Inventory"] = None) -> str:
    """Get item rarity for sorting."""
    if inventory and hasattr(inventory, "_get_item_def"):
        item_def = inventory._get_item_def(item_id)
    else:
        from systems.inventory import get_item_def
        item_def = get_item_def(item_id)
    return getattr(item_def, "rarity", "common") if item_def else "common"


def _get_item_stat(item_id: str, stat_name: str, inventory: Optional["Inventory"] = None) -> float:
    """Get a stat value from an item for sorting."""
    if inventory and hasattr(inventory, "_get_item_def"):
        item_def = inventory._get_item_def(item_id)
    else:
        from systems.inventory import get_item_def
        item_def = get_item_def(item_id)
    if item_def:
        return float(item_def.stats.get(stat_name, 0.0))
    return 0.0


def calculate_stat_comparison(
    game: "Game",
    item_def: "ItemDef",
    character_is_hero: bool = True,
    character_comp: Optional[Any] = None,
) -> Dict[str, Tuple[float, float]]:
    """
    Calculate stat comparison for an item (current stats vs. stats with this item equipped).
    
    Args:
        game: Game instance
        item_def: Item to compare
        character_is_hero: True if hero, False if companion
        character_comp: Companion state if character_is_hero is False
    
    Returns:
        Dict mapping stat_name -> (current_value, new_value)
    """
    from systems.inventory import get_item_def
    
    comparison: Dict[str, Tuple[float, float]] = {}
    
    # Only compare equippable items
    if not item_def.slot or item_def.slot == "consumable":
        return comparison
    
    # Get base stats (without equipment)
    base_stats: Dict[str, float] = {}
    if character_is_hero:
        hero_stats = getattr(game, "hero_stats", None)
        if hero_stats:
            base_stats = {
                "attack": float(getattr(hero_stats, "attack_power", 0)),
                "defense": float(getattr(hero_stats, "defense", 0)),
                "max_hp": float(getattr(hero_stats, "max_hp", 0)),
            }
            # Remove current equipment bonuses
            inv = getattr(game, "inventory", None)
            if inv:
                gear_mods = inv.total_stat_modifiers()
                for stat, value in gear_mods.items():
                    if stat in base_stats:
                        base_stats[stat] -= value
    else:
        if character_comp:
            base_stats = {
                "attack": float(getattr(character_comp, "attack_power", 0)),
                "defense": float(getattr(character_comp, "defense", 0)),
                "max_hp": float(getattr(character_comp, "max_hp", 0)),
            }
            # Remove equipment bonuses
            comp_equipped = getattr(character_comp, "equipped", None) or {}
            for slot, equipped_id in comp_equipped.items():
                if equipped_id:
                    equipped_item = get_item_def(equipped_id)
                    if equipped_item:
                        for stat, value in equipped_item.stats.items():
                            if stat in base_stats:
                                base_stats[stat] -= value
    
    # Get currently equipped item in this slot
    current_equipped_id: Optional[str] = None
    if character_is_hero:
        inv = getattr(game, "inventory", None)
        if inv:
            current_equipped_id = inv.equipped.get(item_def.slot)
    else:
        if character_comp:
            comp_equipped = getattr(character_comp, "equipped", None) or {}
            current_equipped_id = comp_equipped.get(item_def.slot)
    
    # Remove current item's stats from base
    if current_equipped_id:
        current_equipped = get_item_def(current_equipped_id)
        if current_equipped:
            for stat, value in current_equipped.stats.items():
                if stat in base_stats:
                    base_stats[stat] -= value
    
    # Calculate new stats with this item
    for stat_name in ["attack", "defense", "max_hp"]:
        current_value = base_stats.get(stat_name, 0.0)
        new_value = current_value
        if stat_name in item_def.stats:
            new_value += item_def.stats[stat_name]
        comparison[stat_name] = (current_value, new_value)
    
    return comparison

