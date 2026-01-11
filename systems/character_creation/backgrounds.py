# systems/backgrounds.py

"""Background definitions and helpers for character creation.

Backgrounds provide starting bonuses and flavor for characters.
Each class has compatible backgrounds that players can choose from.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ..stats import StatBlock


@dataclass
class Background:
    """
    Character background/origin that provides starting bonuses.
    
    - id: unique identifier
    - name: display name
    - description: flavor text
    - compatible_classes: list of class IDs that can use this background
    - stat_modifiers: percentage-based stat modifiers (5-10% range)
    - starting_perks: bonus perk IDs
    - starting_skills: bonus skill IDs
    - starting_items: bonus item IDs
    - starting_gold_bonus: additional starting gold
    - recommended_traits: trait IDs that work well with this background
    """
    id: str
    name: str
    description: str
    
    # Classes that can use this background
    compatible_classes: List[str]
    
    # Percentage-based stat modifiers (5-10% range)
    stat_modifiers: StatBlock = field(default_factory=StatBlock)
    
    # Bonus starting content
    starting_perks: List[str] = field(default_factory=list)
    starting_skills: List[str] = field(default_factory=list)
    starting_items: List[str] = field(default_factory=list)
    starting_gold_bonus: int = 0
    
    # Suggested traits (for UI recommendations)
    recommended_traits: List[str] = field(default_factory=list)


# --- Registry helpers ---------------------------------------------------------

_BACKGROUNDS: Dict[str, Background] = {}


def register_background(background: Background) -> Background:
    """Register a background definition."""
    if background.id in _BACKGROUNDS:
        raise ValueError(f"Background id already registered: {background.id}")
    _BACKGROUNDS[background.id] = background
    return background


def get_background(background_id: str) -> Background:
    """Get a background by ID."""
    if background_id not in _BACKGROUNDS:
        raise KeyError(f"Background not found: {background_id}")
    return _BACKGROUNDS[background_id]


def all_backgrounds() -> List[Background]:
    """Get all registered backgrounds."""
    return list(_BACKGROUNDS.values())


def backgrounds_for_class(class_id: str) -> List[Background]:
    """Get all backgrounds compatible with a given class."""
    return [
        bg for bg in _BACKGROUNDS.values()
        if class_id in bg.compatible_classes
    ]


# --- Concrete background definitions -------------------------------------------

# Warrior backgrounds
SOLDIER = register_background(
    Background(
        id="soldier",
        name="Soldier",
        description="A veteran of countless battles, trained in the ways of war. You bring military discipline and combat experience.",
        compatible_classes=["warrior"],
        stat_modifiers=StatBlock(
            attack=0.05,  # +5% attack
            defense=0.05,  # +5% defense
        ),
        starting_perks=[],
        starting_skills=[],
        starting_items=["leather_armor"],  # Bonus armor
        starting_gold_bonus=10,
        recommended_traits=["brave", "tough"],
    )
)

NOBLE = register_background(
    Background(
        id="noble",
        name="Noble",
        description="Born to wealth and privilege, you have connections and resources most adventurers can only dream of.",
        compatible_classes=["warrior", "mage"],
        stat_modifiers=StatBlock(
            status_resist=0.05,  # +5% status resist
            max_hp=0.03,  # +3% HP (better nutrition and care)
        ),
        starting_perks=[],
        starting_skills=[],
        starting_items=[],
        starting_gold_bonus=50,  # Significant gold bonus
        recommended_traits=["clever", "lucky"],
    )
)

BLACKSMITH = register_background(
    Background(
        id="blacksmith",
        name="Blacksmith",
        description="A master of metal and forge, you craft weapons and armor with skill and precision.",
        compatible_classes=["warrior"],
        stat_modifiers=StatBlock(
            defense=0.05,  # +5% defense
            max_hp=0.03,  # +3% HP (hardy from working the forge)
        ),
        starting_perks=[],
        starting_skills=[],
        starting_items=["rusty_sword"],  # Bonus weapon
        starting_gold_bonus=15,
        recommended_traits=["strong", "tough"],
    )
)

MERCENARY = register_background(
    Background(
        id="mercenary",
        name="Mercenary",
        description="A sellsword who fights for coin. You've learned to survive by your wits and blade.",
        compatible_classes=["warrior"],
        stat_modifiers=StatBlock(
            attack=0.05,  # +5% attack
            crit_chance=0.03,  # +3% crit
        ),
        starting_perks=[],
        starting_skills=[],
        starting_items=[],
        starting_gold_bonus=20,
        recommended_traits=["brave", "strong"],
    )
)

KNIGHT = register_background(
    Background(
        id="knight",
        name="Knight",
        description="A sworn protector, bound by honor and duty. You fight for justice and defend the weak.",
        compatible_classes=["warrior"],
        stat_modifiers=StatBlock(
            defense=0.08,  # +8% defense
            max_hp=0.05,  # +5% HP
        ),
        starting_perks=[],
        starting_skills=[],
        starting_items=["leather_armor"],
        starting_gold_bonus=5,
        recommended_traits=["brave", "tough"],
    )
)

# Rogue backgrounds
STREET_URCHIN = register_background(
    Background(
        id="street_urchin",
        name="Street Urchin",
        description="Raised on the streets, you learned to survive through stealth, speed, and cunning.",
        compatible_classes=["rogue"],
        stat_modifiers=StatBlock(
            dodge_chance=0.05,  # +5% dodge
            speed=0.05,  # +5% speed
        ),
        starting_perks=[],
        starting_skills=[],
        starting_items=[],  # Could add lockpicks later
        starting_gold_bonus=15,  # Street-smart means some starting gold
        recommended_traits=["nimble", "quick_learner"],
    )
)

THIEF = register_background(
    Background(
        id="thief",
        name="Thief",
        description="A master of locks and shadows, you've made a living by taking what others won't give.",
        compatible_classes=["rogue"],
        stat_modifiers=StatBlock(
            crit_chance=0.05,  # +5% crit
            dodge_chance=0.03,  # +3% dodge
        ),
        starting_perks=[],
        starting_skills=[],
        starting_items=[],  # Could add lockpicks, poison later
        starting_gold_bonus=25,
        recommended_traits=["nimble", "lucky"],
    )
)

HUNTER = register_background(
    Background(
        id="hunter",
        name="Hunter",
        description="A tracker and scout, you know how to read the land and strike from range.",
        compatible_classes=["rogue"],
        stat_modifiers=StatBlock(
            attack=0.05,  # +5% attack
            crit_chance=0.03,  # +3% crit
        ),
        starting_perks=[],
        starting_skills=[],
        starting_items=[],
        starting_gold_bonus=10,
        recommended_traits=["nimble", "focused"],
    )
)

MERCHANT = register_background(
    Background(
        id="merchant",
        name="Merchant",
        description="A trader who knows the value of coin. You've learned to negotiate and haggle.",
        compatible_classes=["rogue"],
        stat_modifiers=StatBlock(
            status_resist=0.05,  # +5% status resist (enhanced from 3% for balance)
            crit_chance=0.02,  # +2% crit (sharp business sense helps)
        ),
        starting_perks=[],
        starting_skills=[],
        starting_items=[],
        starting_gold_bonus=40,
        recommended_traits=["clever", "lucky"],
    )
)

ASSASSIN = register_background(
    Background(
        id="assassin",
        name="Assassin",
        description="A killer for hire, trained in the art of death. You strike from shadows.",
        compatible_classes=["rogue"],
        stat_modifiers=StatBlock(
            crit_chance=0.08,  # +8% crit
            attack=0.03,  # +3% attack
        ),
        starting_perks=[],
        starting_skills=[],
        starting_items=[],
        starting_gold_bonus=30,
        recommended_traits=["nimble", "focused"],
    )
)

# Mage backgrounds
SCHOLAR = register_background(
    Background(
        id="scholar",
        name="Scholar",
        description="A learned academic, versed in ancient texts and magical theory.",
        compatible_classes=["mage"],
        stat_modifiers=StatBlock(
            skill_power=0.10,  # +10% skill power
            max_mana=0.05,  # +5% mana
        ),
        starting_perks=[],
        starting_skills=[],
        starting_items=["focus_charm"],  # Bonus item
        starting_gold_bonus=15,
        recommended_traits=["clever", "quick_learner"],
    )
)

HERMIT = register_background(
    Background(
        id="hermit",
        name="Hermit",
        description="A recluse who studied magic in solitude. You've learned to channel power through meditation.",
        compatible_classes=["mage"],
        stat_modifiers=StatBlock(
            mana_regen_bonus=1,  # +1 mana regen per turn
            status_resist=0.05,  # +5% status resist
        ),
        starting_perks=[],
        starting_skills=[],
        starting_items=[],
        starting_gold_bonus=5,
        recommended_traits=["focused", "tough"],
    )
)

PRIEST = register_background(
    Background(
        id="priest",
        name="Priest",
        description="A servant of the divine, channeling holy power to heal and protect.",
        compatible_classes=["mage"],
        stat_modifiers=StatBlock(
            max_mana=0.08,  # +8% mana
            skill_power=0.03,  # +3% skill power
        ),
        starting_perks=[],
        starting_skills=["heal"],  # Bonus healing skill if available
        starting_items=[],
        starting_gold_bonus=10,
        recommended_traits=["clever", "focused"],
    )
)

APPRENTICE = register_background(
    Background(
        id="apprentice",
        name="Apprentice",
        description="A student of magic, just beginning your journey. You have potential but lack experience.",
        compatible_classes=["mage"],
        stat_modifiers=StatBlock(
            skill_power=0.05,  # +5% skill power
            max_mana=0.03,  # +3% mana (youthful energy)
        ),
        starting_perks=[],
        starting_skills=[],
        starting_items=[],
        starting_gold_bonus=20,
        recommended_traits=["quick_learner", "clever"],
    )
)


# Cross-class backgrounds
ADVENTURER = register_background(
    Background(
        id="adventurer",
        name="Adventurer",
        description="A wanderer seeking fortune and glory. You're adaptable and resourceful.",
        compatible_classes=["warrior", "rogue", "mage"],
        stat_modifiers=StatBlock(
            max_hp=0.03,  # +3% HP
            crit_chance=0.02,  # +2% crit
        ),
        starting_perks=[],
        starting_skills=[],
        starting_items=[],
        starting_gold_bonus=15,
        recommended_traits=["lucky", "quick_learner"],
    )
)

