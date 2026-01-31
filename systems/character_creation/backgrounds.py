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
        description="A veteran of countless battles, trained in the ways of war. You've stood in formation against charging hordes, weathered sieges, and learned that survival means discipline above all. Your military training has honed both your offensive and defensive capabilities, making you a reliable front-line fighter who knows when to strike and when to hold the line.",
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
        description="Born to wealth and privilege, you have connections and resources most adventurers can only dream of. Raised in opulent halls with the finest tutors and trainers, you've learned to navigate both courtly intrigue and the battlefield. Your noble upbringing has granted you resilience against mental attacks and better physical conditioning, while your family's treasury provides a significant head start in your adventures.",
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
        description="A master of metal and forge, you craft weapons and armor with skill and precision. Years of hammering steel and working the bellows have built your strength and endurance, while your intimate knowledge of weaponry makes you a formidable warrior. You understand the balance of a blade, the weight of armor, and how to maintain your equipment—skills that have kept you alive when others fall.",
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
        description="A sellsword who fights for coin. You've learned to survive by your wits and blade, taking contracts from whoever pays best and moving on before the debts come due. Your experience fighting for different causes has taught you to strike hard and fast, exploiting weaknesses and finishing fights quickly. The gold you've saved from past jobs gives you a solid foundation for your new adventures.",
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
        description="A sworn protector, bound by honor and duty. You fight for justice and defend the weak, having taken oaths that shape every action you take. Your training in defensive combat and unwavering dedication to your cause have made you exceptionally resilient. Though your code of honor may limit your options, it has forged you into a stalwart defender capable of weathering any storm.",
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
        description="Raised on the streets, you learned to survive through stealth, speed, and cunning. You've dodged guards, outrun bullies, and learned that the fastest way to safety is often the one others don't see. Your hard-won street smarts have made you quick on your feet and harder to hit, while the small stash you've scraped together from odd jobs gives you a modest start.",
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
        description="A master of locks and shadows, you've made a living by taking what others won't give. You know every trick for slipping past guards, opening any lock, and striking when your target least expects it. Your life of crime has sharpened your reflexes and taught you to find the perfect moment to strike, while the spoils of your past heists provide a comfortable starting fund.",
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
        description="A tracker and scout, you know how to read the land and strike from range. You've spent countless hours in the wilderness, learning to read tracks, predict movement, and make every shot count. Your experience hunting dangerous game has honed your aim and taught you to target vital spots, while the pelts and bounties you've collected provide a modest nest egg for your adventures.",
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
        description="A trader who knows the value of coin. You've learned to negotiate and haggle, traveling between cities and turning profit wherever opportunity presents itself. Your sharp business sense helps you read people and situations, allowing you to spot weaknesses and make advantageous deals. The capital you've accumulated from successful trades gives you a significant financial advantage at the start of your journey.",
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
        description="A killer for hire, trained in the art of death. You strike from shadows, having learned to end lives with precision and efficiency. Your training has taught you to find the perfect moment to strike, targeting vital points with deadly accuracy. The payments from your past contracts have left you well-funded, though your reputation may precede you.",
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
        description="A learned academic, versed in ancient texts and magical theory. You've spent years in libraries and universities, studying the fundamental principles of magic and the arcane arts. Your deep understanding of magical theory allows you to channel power more effectively and maintain larger reserves of mana. The focus charm you acquired during your studies helps you channel your magical energies with greater precision.",
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
        description="A recluse who studied magic in solitude. You've learned to channel power through meditation, having retreated from society to focus entirely on your magical studies. Your years of isolation have strengthened your mental fortitude and deepened your connection to the mystical forces, allowing you to regenerate mana more quickly and resist mental attacks. Though you start with little material wealth, your spiritual development is unmatched.",
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
        description="A servant of the divine, channeling holy power to heal and protect. You've dedicated your life to a higher power, learning to channel divine energy for both healing and smiting. Your faith has granted you access to greater reserves of magical power and the ability to mend wounds with holy light. The small donations from your congregation provide a modest starting fund, but your true wealth lies in the favor of the gods.",
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
        description="A student of magic, just beginning your journey. You have potential but lack experience, having recently left your master's tutelage to seek your own path. Your youth brings both enthusiasm and untapped magical reserves, though your skills are still developing. The small allowance from your former master and the energy of youth give you a solid foundation to build upon as you forge your own destiny.",
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
        description="A wanderer seeking fortune and glory. You're adaptable and resourceful, having traveled far and wide in search of adventure and opportunity. Your diverse experiences have made you tougher and more capable of seizing opportunities when they arise. The small treasures and rewards from your past exploits have accumulated into a modest starting fund, and your well-rounded nature makes you ready for whatever challenges lie ahead.",
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

