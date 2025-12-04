# systems/party.py

from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class CompanionDef:
    """
    Simple companion template for now.

    For P1:
    - Stats are derived from the hero and scaled by these factors.
    - skill_ids are skill ids from systems.skills.

    Later we can extend this into full heroes with:
    - their own StatBlock
    - their own inventory / perks / class
    """
    id: str
    name: str
    role: str

    hp_factor: float = 0.8
    attack_factor: float = 0.7
    defense_factor: float = 1.0
    skill_power_factor: float = 1.0

    skill_ids: List[str] = field(default_factory=list)


_COMPANIONS: Dict[str, CompanionDef] = {}


def register_companion(defn: CompanionDef) -> CompanionDef:
    if defn.id in _COMPANIONS:
        raise ValueError(f"Companion id already registered: {defn.id}")
    _COMPANIONS[defn.id] = defn
    return defn


def get_companion(companion_id: str) -> CompanionDef:
    return _COMPANIONS[companion_id]


def all_companions() -> List[CompanionDef]:
    return list(_COMPANIONS.values())


# --- Concrete companion templates -------------------------------------------

# Very basic ally; stats derived from hero.
DEFAULT_MERCENARY = register_companion(
    CompanionDef(
        id="mercenary",
        name="Sellsword",
        role="Ally",
        skill_ids=["guard"],
        hp_factor=0.8,
        attack_factor=0.7,
        defense_factor=1.0,
        skill_power_factor=1.0,
    )
)


def default_party_for_class(hero_class_id: str) -> List[CompanionDef]:
    """
    For now, every class starts with the same basic ally.

    Later we can:
    - Vary companions per hero class
    - Add 2nd/3rd party member
    - Use events to recruit instead of always-on
    """
    return [DEFAULT_MERCENARY]
