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


def _load_item_definitions() -> None:
    global _ITEM_DEFS, _ITEMS_LOADED
    if _ITEMS_LOADED:
        return

    path = _items_path()
    if not path.exists():
        # Quiet fail: project can still run without items, but nothing to load.
        _ITEM_DEFS = {}
        _ITEMS_LOADED = True
        return

    import json

    with path.open("r", encoding="utf-8") as f:
        raw_list = json.load(f)

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
            "armor": None,
            "trinket": None,
        }
    )

    def add_item(self, item_id: str) -> None:
        if get_item_def(item_id) is None:
            # Unknown id; ignore for now.
            return
        self.items.append(item_id)

    def remove_item(self, item_id: str) -> None:
        if item_id in self.items:
            self.items.remove(item_id)
        # If it was equipped, unequip that slot
        for slot, equipped_id in list(self.equipped.items()):
            if equipped_id == item_id:
                self.equipped[slot] = None

    def equip(self, item_id: str) -> str:
        """
        Equip an item by id. Returns a human-readable message.
        If the item is not equippable (e.g. consumable), does nothing.
        """
        item = get_item_def(item_id)
        if item is None:
            return "You don't recognise how to use that."

        slot = item.slot
        if slot not in self.equipped:
            return f"You can't equip {item.name}."

        if item_id not in self.items:
            return f"You don't have {item.name}."

        previous = self.equipped.get(slot)
        self.equipped[slot] = item_id

        if previous is None:
            return f"You equip {item.name}."
        else:
            prev_item = get_item_def(previous)
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
        item_id = self.equipped.get(slot)
        if not item_id:
            return None
        return get_item_def(item_id)

    def get_items_by_slot(self, slot: str) -> List[ItemDef]:
        result: List[ItemDef] = []
        for item_id in self.items:
            item = get_item_def(item_id)
            if item is not None and item.slot == slot:
                result.append(item)
        return result

    def total_stat_modifiers(self) -> Dict[str, float]:
        """
        Sum up all stat bonuses from currently equipped items.
        Returns a dict like {"max_hp": +10, "attack": +3, ...}
        """
        totals: Dict[str, float] = {}

        for slot, item_id in self.equipped.items():
            if not item_id:
                continue
            item = get_item_def(item_id)
            if item is None:
                continue
            for stat_name, value in item.stats.items():
                totals[stat_name] = totals.get(stat_name, 0.0) + value

        return totals
