# systems/traits.py

"""Trait definitions and helpers for character creation.

Traits are character qualities that affect gameplay through a point-buy system.
Players start with 5-7 trait points and can spend them on traits (cost 1-3 points).
Traits can synergize with each other and connect to perks.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ..stats import StatBlock


@dataclass
class Trait:
    """
    Character trait that provides bonuses/penalties.
    
    - id: unique identifier
    - name: display name
    - description: flavor text
    - category: "personality", "physical", "mental", "social"
    - cost: trait points required (1-3)
    - stat_modifiers: percentage-based stat modifiers (10-20% range)
    - perk_modifiers: perk IDs that interact/enhance with this trait
    - synergies: trait IDs that synergize with this one (bonus when combined)
    - conflicts: trait IDs that conflict (cannot have both, or reduce synergy)
    """
    id: str
    name: str
    description: str
    category: str  # "personality", "physical", "mental", "social"
    
    cost: int  # Trait points required (1-3)
    
    # Percentage-based stat modifiers (10-20% range)
    stat_modifiers: StatBlock = field(default_factory=StatBlock)
    
    # Perks that interact with this trait
    perk_modifiers: List[str] = field(default_factory=list)
    
    # Trait synergies (bonus effects when combined)
    synergies: List[str] = field(default_factory=list)
    
    # Trait conflicts (traits that conflict with this one)
    conflicts: List[str] = field(default_factory=list)


# --- Registry helpers ---------------------------------------------------------

_TRAITS: Dict[str, Trait] = {}


def register_trait(trait: Trait) -> Trait:
    """Register a trait definition."""
    if trait.id in _TRAITS:
        raise ValueError(f"Trait id already registered: {trait.id}")
    _TRAITS[trait.id] = trait
    return trait


def get_trait(trait_id: str) -> Trait:
    """Get a trait by ID."""
    if trait_id not in _TRAITS:
        raise KeyError(f"Trait not found: {trait_id}")
    return _TRAITS[trait_id]


def all_traits() -> List[Trait]:
    """Get all registered traits."""
    return list(_TRAITS.values())


def traits_by_category(category: str) -> List[Trait]:
    """Get all traits in a given category."""
    return [t for t in _TRAITS.values() if t.category == category]


def trait_synergy_bonus(trait_ids: List[str]) -> StatBlock:
    """
    Calculate synergy bonuses for a list of traits.
    
    Returns a StatBlock with additional bonuses from trait synergies.
    Synergies are small bonuses (1-2%) applied when compatible traits are combined.
    """
    bonus = StatBlock()
    
    for trait_id in trait_ids:
        if trait_id not in _TRAITS:
            continue
        
        trait = _TRAITS[trait_id]
        
        # Check if this trait's synergies are also in the list
        for synergy_id in trait.synergies:
            if synergy_id in trait_ids and synergy_id != trait_id:
                # Apply small synergy bonus (1-2% for now)
                # This is a simple implementation - can be enhanced later
                pass  # Synergy bonuses can be more complex, keeping simple for now
    
    return bonus


# --- Concrete trait definitions -----------------------------------------------

# Cost 1 traits (minor effects)
QUICK_LEARNER = register_trait(
    Trait(
        id="quick_learner",
        name="Quick Learner",
        description="You pick up new skills faster than most. +10% XP gain, but start with fewer skill points.",
        category="mental",
        cost=1,
        stat_modifiers=StatBlock(),  # XP gain is handled separately
        synergies=["lucky"],
    )
)

FOCUSED = register_trait(
    Trait(
        id="focused",
        name="Focused",
        description="Your mental clarity grants you enhanced magical ability. +5% skill power, +5% mana regen.",
        category="mental",
        cost=1,
        stat_modifiers=StatBlock(
            skill_power=0.05,
            mana_regen_bonus=1,
        ),
        synergies=["clever"],
    )
)

# Cost 2 traits (moderate effects)
BRAVE = register_trait(
    Trait(
        id="brave",
        name="Brave",
        description="You charge into battle without fear. +15% attack, -10% defense.",
        category="personality",
        cost=2,
        stat_modifiers=StatBlock(
            attack=0.15,
            defense=-0.10,
        ),
        synergies=["strong"],
        conflicts=["cautious"],
    )
)

CAUTIOUS = register_trait(
    Trait(
        id="cautious",
        name="Cautious",
        description="You prefer to watch and wait before acting. +10% defense, -5% speed.",
        category="personality",
        cost=2,
        stat_modifiers=StatBlock(
            defense=0.10,
            speed=-0.05,
        ),
        synergies=["nimble"],
        conflicts=["brave"],
    )
)

LUCKY = register_trait(
    Trait(
        id="lucky",
        name="Lucky",
        description="Fortune favors you. +5% crit chance, +3% dodge, -5% max HP.",
        category="personality",
        cost=2,
        stat_modifiers=StatBlock(
            crit_chance=0.05,
            dodge_chance=0.03,
            max_hp=-0.05,
        ),
        synergies=["quick_learner"],
    )
)

STRONG = register_trait(
    Trait(
        id="strong",
        name="Strong",
        description="Your physical power is exceptional. +10% attack, +10% max HP, -5% speed.",
        category="physical",
        cost=2,
        stat_modifiers=StatBlock(
            attack=0.10,
            max_hp=0.10,
            speed=-0.05,
        ),
        synergies=["brave"],
        conflicts=["nimble"],
    )
)

NIMBLE = register_trait(
    Trait(
        id="nimble",
        name="Nimble",
        description="You move with exceptional grace and speed. +10% speed, +5% dodge, -5% max HP.",
        category="physical",
        cost=2,
        stat_modifiers=StatBlock(
            speed=0.10,
            dodge_chance=0.05,
            max_hp=-0.05,
        ),
        synergies=["cautious"],
        conflicts=["strong"],
    )
)

TOUGH = register_trait(
    Trait(
        id="tough",
        name="Tough",
        description="You can take a beating and keep going. +15% max HP, +5% defense, -5% attack.",
        category="physical",
        cost=2,
        stat_modifiers=StatBlock(
            max_hp=0.15,
            defense=0.05,
            attack=-0.05,
        ),
    )
)

CLEVER = register_trait(
    Trait(
        id="clever",
        name="Clever",
        description="Your intelligence enhances your magical abilities. +15% skill power, +10% max mana, -5% attack.",
        category="mental",
        cost=2,
        stat_modifiers=StatBlock(
            skill_power=0.15,
            max_mana=0.10,
            attack=-0.05,
        ),
        synergies=["focused"],
    )
)

# Cost 3 traits (major effects)
GIFTED = register_trait(
    Trait(
        id="gifted",
        name="Gifted",
        description="You possess exceptional magical talent. +20% skill power, -5% max HP.",
        category="mental",
        cost=3,
        stat_modifiers=StatBlock(
            skill_power=0.20,
            max_hp=-0.05,
        ),
    )
)

