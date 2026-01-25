from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from systems.inventory import get_item_def


@dataclass(frozen=True)
class ConsumableDef:
    """
    Data definition for a consumable item.

    Note: Basic display fields (name, rarity, value) are also present in
    ItemDef via items/consumables.json. This definition focuses on the
    gameplay effect block.
    """

    id: str
    name: str
    description: str
    rarity: str
    value: int
    effect: Dict[str, Any]


_CONSUMABLE_DEFS: Dict[str, ConsumableDef] = {}
_CONSUMABLES_LOADED: bool = False


def _consumables_path() -> Path:
    here = Path(__file__).resolve()
    data_dir = here.parent.parent / "data"
    return data_dir / "consumables.json"


def _load_consumable_definitions() -> None:
    global _CONSUMABLE_DEFS, _CONSUMABLES_LOADED
    if _CONSUMABLES_LOADED:
        return

    path = _consumables_path()
    if not path.exists():
        _CONSUMABLE_DEFS = {}
        _CONSUMABLES_LOADED = True
        return

    import json

    with path.open("r", encoding="utf-8") as f:
        raw_list = json.load(f)

    defs: Dict[str, ConsumableDef] = {}
    for entry in raw_list:
        item_id = entry["id"]
        item_def = get_item_def(item_id)
        name = entry.get("name") or (item_def.name if item_def is not None else item_id)
        description = entry.get("description") or (item_def.description if item_def is not None else "")
        rarity = entry.get("rarity") or (item_def.rarity if item_def is not None else "common")
        value = int(entry.get("value", item_def.value if item_def is not None else 0))
        effect = dict(entry.get("effect", {}))

        defs[item_id] = ConsumableDef(
            id=item_id,
            name=name,
            description=description,
            rarity=rarity,
            value=value,
            effect=effect,
        )

    _CONSUMABLE_DEFS = defs
    _CONSUMABLES_LOADED = True


def all_consumables() -> List[ConsumableDef]:
    _load_consumable_definitions()
    return list(_CONSUMABLE_DEFS.values())


def get_consumable(consumable_id: str) -> Optional[ConsumableDef]:
    _load_consumable_definitions()
    return _CONSUMABLE_DEFS.get(consumable_id)


def _compute_heal_amount(max_hp: int, effect: Dict[str, Any]) -> int:
    base = int(effect.get("amount", 0))
    percent = float(effect.get("percent_max", 0.0))
    bonus = int(max_hp * max(0.0, percent))
    total = base + bonus
    return max(1, total)


def _compute_resource_restore(max_value: int, effect: Dict[str, Any]) -> int:
    base = int(effect.get("amount", 0))
    percent = float(effect.get("percent_max", 0.0))
    bonus = int(max_value * max(0.0, percent))
    total = base + bonus
    return max(1, total)


def apply_consumable_to_entity(
    *,
    entity: Any,
    hero_max_hp: Optional[int],
    consumable: ConsumableDef,
) -> Tuple[str, int]:
    """
    Apply a consumable in exploration context to a world entity (hero only for now).

    Returns:
        (message, primary_amount) where primary_amount is the HP or resource delta.
    """
    effect = consumable.effect or {}
    etype = effect.get("type")

    if etype == "heal":
        max_hp = hero_max_hp if hero_max_hp is not None else int(getattr(entity, "max_hp", 0))
        max_hp = max(1, max_hp)
        amount = _compute_heal_amount(max_hp, effect)
        current_hp = int(getattr(entity, "hp", 0))
        new_hp = min(max_hp, current_hp + amount)
        actual = new_hp - current_hp
        setattr(entity, "hp", new_hp)
        if actual <= 0:
            return (f"{consumable.name} has no effect.", 0)
        return (f"You drink {consumable.name} and recover {actual} HP.", actual)

    if etype == "resource":
        resource = (effect.get("resource") or "").lower()
        if resource not in {"stamina", "mana"}:
            return (f"{consumable.name} fizzles uselessly.", 0)

        attr_max = f"max_{resource}"
        attr_cur = f"current_{resource}"
        max_val = int(getattr(entity, attr_max, 0))
        if max_val <= 0:
            return (f"{consumable.name} has no effect.", 0)

        amount = _compute_resource_restore(max_val, effect)
        current_val = int(getattr(entity, attr_cur, max_val))
        new_val = min(max_val, current_val + amount)
        actual = new_val - current_val
        setattr(entity, attr_cur, new_val)

        if actual <= 0:
            return (f"{consumable.name} has no effect.", 0)

        label = "stamina" if resource == "stamina" else "mana"
        return (f"You drink {consumable.name} and restore {actual} {label}.", actual)

    return (f"You are not sure how to use {consumable.name}.", 0)


def apply_consumable_in_battle(
    *,
    game: Any,
    battle_scene: Any,
    user_unit: Any,
    consumable: ConsumableDef,
) -> str:
    """
    Apply a consumable during battle to the active unit.

    Returns:
        Log message string for the battle log.
    """
    effect = consumable.effect or {}
    etype = effect.get("type")

    # In battle we work directly on the unit entity (hero or companion)
    entity = getattr(user_unit, "entity", user_unit)

    if etype == "heal":
        max_hp = int(getattr(entity, "max_hp", 0))
        max_hp = max(1, max_hp)
        amount = _compute_heal_amount(max_hp, effect)
        current_hp = int(getattr(entity, "hp", 0))
        new_hp = min(max_hp, current_hp + amount)
        actual = new_hp - current_hp
        setattr(entity, "hp", new_hp)

        if actual <= 0:
            return f"{user_unit.name} uses {consumable.name}, but it has no effect."
        
        # Add floating healing number
        if hasattr(battle_scene, "_floating_damage"):
            battle_scene._floating_damage.append({
                "target": user_unit,
                "damage": actual,
                "timer": 1.8,
                "y_offset": 0,
                "is_crit": False,
                "is_kill": False,
                "is_healing": True,  # Mark as healing
            })
        
        return f"{user_unit.name} drinks {consumable.name} and recovers {actual} HP."

    if etype == "resource":
        resource = (effect.get("resource") or "").lower()
        if resource not in {"stamina", "mana"}:
            return f"{user_unit.name} fumbles with {consumable.name} to no effect."

        attr_max = f"max_{resource}"
        attr_cur = f"current_{resource}"
        max_val = int(getattr(user_unit, attr_max, 0))
        if max_val <= 0:
            return f"{consumable.name} has no effect."

        amount = _compute_resource_restore(max_val, effect)
        current_val = int(getattr(user_unit, attr_cur, max_val))
        new_val = min(max_val, current_val + amount)
        actual = new_val - current_val
        setattr(user_unit, attr_cur, new_val)

        if actual <= 0:
            return f"{consumable.name} has no effect."

        label = "stamina" if resource == "stamina" else "mana"
        return f"{user_unit.name} drinks {consumable.name} and restores {actual} {label}."

    return f"{user_unit.name} is not sure how to use {consumable.name}."



