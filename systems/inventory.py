# systems/inventory.py

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any


# ---------- Item definitions ----------

@dataclass(frozen=True)
class ItemDef:
    id: str
    name: str
    slot: str                 # "weapon", "armor", "trinket", "consumable", ...
    description: str
    stats: Dict[str, float]   # e.g. {"attack": 2, "defense": 1}
    rarity: str = "common"
    value: int = 0


_ITEM_DEFS: Dict[str, ItemDef] = {}
_ITEMS_LOADED: bool = False


def _items_path() -> Path:
    # systems/ -> project root / data / items.json
    here = Path(__file__).resolve()
    data_dir = here.parent.parent / "data"
    return data_dir / "items.json"


def _consumables_path() -> Path:
    # systems/ -> project root / data / consumables.json
    here = Path(__file__).resolve()
    data_dir = here.parent.parent / "data"
    return data_dir / "consumables.json"


def _load_item_definitions() -> None:
    global _ITEM_DEFS, _ITEMS_LOADED
    if _ITEMS_LOADED:
        return

    items_path = _items_path()
    consumables_path = _consumables_path()

    import json

    raw_list = []

    # Core equipment items
    if items_path.exists():
        with items_path.open("r", encoding="utf-8") as f:
            raw_list.extend(json.load(f))

    # Consumables are defined in a separate file but share the same basic
    # item schema (id, name, slot, stats...). We merge them into the same
    # ItemDef registry so inventory / UI can treat them uniformly.
    if consumables_path.exists():
        with consumables_path.open("r", encoding="utf-8") as f:
            try:
                extra = json.load(f)
                if isinstance(extra, list):
                    raw_list.extend(extra)
            except Exception:
                # Malformed consumables file should not break the rest of items.
                pass

    if not raw_list:
        _ITEM_DEFS = {}
        _ITEMS_LOADED = True
        return

    defs: Dict[str, ItemDef] = {}
    for entry in raw_list:
        stats = {k: float(v) for k, v in entry.get("stats", {}).items()}
        item = ItemDef(
            id=entry["id"],
            name=entry.get("name", entry["id"]),
            slot=entry.get("slot", "misc"),
            description=entry.get("description", ""),
            stats=stats,
            rarity=entry.get("rarity", "common"),
            value=int(entry.get("value", 0)),
        )
        defs[item.id] = item

    _ITEM_DEFS = defs
    _ITEMS_LOADED = True


def all_items() -> List[ItemDef]:
    _load_item_definitions()
    return list(_ITEM_DEFS.values())


def get_item_def(item_id: str) -> Optional[ItemDef]:
    _load_item_definitions()
    return _ITEM_DEFS.get(item_id)


# ---------- Inventory & equipment ----------

@dataclass
class Inventory:
    """
    Simple inventory + equipment container.

    - items: list of item ids you own (including equipped ones)
    - equipped: slot -> item_id (or None)

    We don't mutate HeroStats directly here. Instead, Game will ask us
    for combined stat modifiers and add them when syncing stats onto
    the Player entity.
    """

    items: List[str] = field(default_factory=list)
    equipped: Dict[str, Optional[str]] = field(
        default_factory=lambda: {
            "weapon": None,
            "helmet": None,
            "armor": None,
            "gloves": None,
            "boots": None,
            "shield": None,
            "cloak": None,
            "ring": None,
            "amulet": None,
        }
    )

    def add_item(self, item_id: str, randomized: bool = True) -> None:
        """
        Add an item to inventory.
        
        Args:
            item_id: Item ID to add
            randomized: If True, apply randomization to the item (default: True)
        """
        if get_item_def(item_id) is None:
            # Unknown id; ignore for now.
            return
        
        # Apply randomization if enabled
        if randomized:
            try:
                from .item_randomization import randomize_item
                floor_index = getattr(self, "_current_floor", 1)  # Default to 1 if not set
                randomized_item = randomize_item(item_id, floor_index)
                if randomized_item is not None:
                    base_item = get_item_def(item_id)
                    # Only use randomized version if it's actually different
                    if base_item and randomized_item.stats != base_item.stats:
                        # Store randomized version in a special registry
                        if not hasattr(self, "_randomized_items"):
                            self._randomized_items: Dict[str, ItemDef] = {}
                        # Use a special ID format to track randomized items
                        # Format: "item_id:random_seed" where seed is based on item position
                        seed = len(self.items)
                        random_id = f"{item_id}:{seed}"
                        self._randomized_items[random_id] = randomized_item
                        self.items.append(random_id)
                        return
            except ImportError:
                # Randomization system not available, fall through to normal add
                pass
        
        # Normal add (no randomization or randomization disabled)
        self.items.append(item_id)

    def remove_item(self, item_id: str) -> None:
        if item_id in self.items:
            self.items.remove(item_id)
        # If it was equipped, unequip that slot
        for slot, equipped_id in list(self.equipped.items()):
            if equipped_id == item_id:
                self.equipped[slot] = None

    def remove_one(self, item_id: str) -> bool:
        """
        Remove a single instance of ``item_id`` from the inventory list.
        Returns True if something was removed, False otherwise.

        This does *not* touch equipped slots. Selling equipped items
        should be prevented by the caller (via get_sellable_item_ids()).
        """
        try:
            self.items.remove(item_id)
        except ValueError:
            return False
        return True

    def get_sellable_item_ids(self) -> List[str]:
        """
        Return a list of item ids that are valid to sell:
        all items, minus one copy for each equipped item.
        """
        sellable = list(self.items)
        for slot, equipped_id in self.equipped.items():
            if not equipped_id:
                continue
            if equipped_id in sellable:
                sellable.remove(equipped_id)
        return sellable

    def equip(self, item_id: str) -> str:
        """
        Equip an item by id. Returns a human-readable message.
        If the item is not equippable (e.g. consumable), does nothing.
        """
        item = self._get_item_def(item_id)
        if item is None:
            return "You don't recognise how to use that."

        slot = item.slot
        
        # Backwards compatibility: map old "trinket" slot to "ring" or "amulet"
        if slot == "trinket":
            # Determine if it's a ring or amulet based on item name/ID
            item_name_lower = item.name.lower()
            item_id_lower = item_id.lower()
            if "ring" in item_id_lower or "ring" in item_name_lower:
                slot = "ring"
            elif "amulet" in item_id_lower or "amulet" in item_name_lower or "locket" in item_id_lower or "locket" in item_name_lower:
                slot = "amulet"
            else:
                # Default to ring for backwards compatibility
                slot = "ring"
        
        # Map item slot types to equipment slots
        slot_mapping = {
            "weapon": "weapon",
            "helmet": "helmet",
            "armor": "armor",
            "gloves": "gloves",
            "boots": "boots",
            "greaves": "boots",  # Greaves go in boots slot
            "shield": "shield",
            "cloak": "cloak",
            "cape": "cloak",  # Capes go in cloak slot
            "ring": "ring",
            "amulet": "amulet",
        }
        
        # Map the slot if needed
        slot = slot_mapping.get(slot, slot)
        
        if slot not in self.equipped:
            return f"You can't equip {item.name}."

        if item_id not in self.items:
            return f"You don't have {item.name}."

        previous = self.equipped.get(slot)
        self.equipped[slot] = item_id

        if previous is None:
            return f"You equip {item.name}."
        else:
            prev_item = self._get_item_def(previous)
            prev_name = prev_item.name if prev_item else "something"
            return f"You swap {prev_name} for {item.name}."

    def unequip(self, slot: str) -> str:
        if slot not in self.equipped:
            return "Nothing to unequip."
        if self.equipped[slot] is None:
            return "Nothing is equipped there."
        self.equipped[slot] = None
        return f"You remove your {slot}."

    # --- Helpers for the game / UI ---

    def get_equipped_item(self, slot: str) -> Optional[ItemDef]:
        """
        Get the ItemDef for an equipped item, including randomized versions.
        """
        item_id = self.equipped.get(slot)
        if not item_id:
            return None
        
        # Check if this is a randomized item
        if hasattr(self, "_randomized_items") and item_id in self._randomized_items:
            return self._randomized_items[item_id]
        
        # Check if item_id contains a random seed (format: "base_id:seed")
        if ":" in item_id:
            base_id = item_id.split(":")[0]
            if hasattr(self, "_randomized_items") and item_id in self._randomized_items:
                return self._randomized_items[item_id]
            # Fall back to base item if randomized version not found
            return get_item_def(base_id)
        
        return get_item_def(item_id)

    def get_items_by_slot(self, slot: str) -> List[ItemDef]:
        """
        Get all items in a slot, including randomized versions.
        """
        result: List[ItemDef] = []
        for item_id in self.items:
            # Check for randomized item
            item = None
            if hasattr(self, "_randomized_items") and item_id in self._randomized_items:
                item = self._randomized_items[item_id]
            elif ":" in item_id:
                # Try to get randomized version
                if hasattr(self, "_randomized_items") and item_id in self._randomized_items:
                    item = self._randomized_items[item_id]
                else:
                    # Fall back to base item
                    base_id = item_id.split(":")[0]
                    item = get_item_def(base_id)
            else:
                item = get_item_def(item_id)
            
            if item is not None and item.slot == slot:
                result.append(item)
        return result

    def _get_item_def(self, item_id: str) -> Optional[ItemDef]:
        """
        Get ItemDef for an item, checking for randomized versions first.
        """
        # Check for randomized item
        if hasattr(self, "_randomized_items") and item_id in self._randomized_items:
            return self._randomized_items[item_id]
        
        # Check if item_id contains a random seed (format: "base_id:seed")
        if ":" in item_id:
            base_id = item_id.split(":")[0]
            if hasattr(self, "_randomized_items") and item_id in self._randomized_items:
                return self._randomized_items[item_id]
            # Fall back to base item if randomized version not found
            return get_item_def(base_id)
        
        return get_item_def(item_id)
    
    def total_stat_modifiers(self) -> Dict[str, float]:
        """
        Sum up all stat bonuses from currently equipped items.
        Returns a dict like {"max_hp": +10, "attack": +3, ...}
        """
        totals: Dict[str, float] = {}

        for slot, item_id in self.equipped.items():
            if not item_id:
                continue
            item = self._get_item_def(item_id)
            if item is None:
                continue
            for stat_name, value in item.stats.items():
                totals[stat_name] = totals.get(stat_name, 0.0) + value

        return totals
