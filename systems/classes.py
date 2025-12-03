# systems/classes.py

"""Class definitions and helpers for hero / party creation.

For now this is all Python code so it's easy to tweak while we build the game.
Later we can move the raw data to JSON if we want external modding.
"""

from dataclasses import dataclass
from typing import Dict, List

from .stats import StatBlock


@dataclass
class ClassDef:
    id: str
    name: str
    description: str

    # Base stats at level 1 before perks / items.
    base_stats: StatBlock

    # Lists of ids; the actual systems live in systems.perks / systems.skills / systems.inventory.
    starting_perks: List[str]
    starting_skills: List[str]
    starting_items: List[str]

    # Starting gold for this class.
    starting_gold: int = 0


# --- Registry helpers ---------------------------------------------------------

_CLASSES: Dict[str, ClassDef] = {}


def register_class(class_def: ClassDef) -> ClassDef:
    if class_def.id in _CLASSES:
        raise ValueError(f"Class id already registered: {class_def.id}")
    _CLASSES[class_def.id] = class_def
    return class_def


def get_class(class_id: str) -> ClassDef:
    return _CLASSES[class_id]


def all_classes() -> List[ClassDef]:
    return list(_CLASSES.values())


# --- Concrete class definitions -----------------------------------------------

# Numbers are tuned around the default StatBlock:
#   max_hp=30, attack=6, defense=0, speed=1.0, skill_power=1.0
# We give each a distinct silhouette but keep them in a similar power band
# because perks / items will matter a lot later.

WARRIOR = register_class(
    ClassDef(
        id="warrior",
        name="Warrior",
        description="Tough frontliner with solid melee damage and strong defenses.",
        base_stats=StatBlock(
            max_hp=40,
            attack=7,
            defense=1,
            speed=1.0,
            skill_power=1.0,
            crit_chance=0.05,
            dodge_chance=0.02,
            status_resist=0.05,
        ),
        # Perk ids from systems.perks
        starting_perks=[
            "toughness_1",
            "weapon_training_1",
        ],
        # Skill ids from systems.skills
        starting_skills=[
            "guard",
            "power_strike",
        ],
        # Item ids from data/items.json
        starting_items=[
            "rusty_sword",
            "leather_armor",
        ],
        starting_gold=25,
    )
)


ROGUE = register_class(
    ClassDef(
        id="rogue",
        name="Rogue",
        description="Fast skirmisher relying on mobility, crits, and evasive maneuvers.",
        base_stats=StatBlock(
            max_hp=28,
            attack=6,
            defense=0,
            speed=1.2,
            skill_power=1.0,
            crit_chance=0.12,
            dodge_chance=0.10,
            status_resist=0.0,
        ),
        starting_perks=[
            "fleet_footwork_1",
        ],
        starting_skills=[
            "guard",
            "nimble_step",
        ],
        starting_items=[
            "rusty_sword",
            "tattered_cloak",
        ],
        starting_gold=30,
    )
)


MAGE = register_class(
    ClassDef(
        id="mage",
        name="Mage",
        description="Fragile caster with high skill power and potent abilities.",
        base_stats=StatBlock(
            max_hp=24,
            attack=4,
            defense=0,
            speed=1.0,
            skill_power=1.4,
            crit_chance=0.05,
            dodge_chance=0.05,
            status_resist=0.05,
        ),
        starting_perks=[
            "battle_focus_1",
        ],
        starting_skills=[
            "guard",
            "focus_blast",
        ],
        starting_items=[
            "tattered_cloak",
            "focus_charm",
        ],
        starting_gold=35,
    )
)
