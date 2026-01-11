# systems/character_creation/__init__.py

"""
Character creation enhancement system.

This module contains data structures and systems for enhanced character creation:
- Backgrounds: Character origins with starting bonuses
- Traits: Point-buy character traits with synergies
- Appearance: Visual customization
- Stat Distribution: Stat point allocation
"""

from .backgrounds import (
    Background,
    register_background,
    get_background,
    all_backgrounds,
    backgrounds_for_class,
)

from .traits import (
    Trait,
    register_trait,
    get_trait,
    all_traits,
    traits_by_category,
    trait_synergy_bonus,
)

from .appearance import AppearanceConfig

from .stat_distribution import StatDistribution

from .stat_helpers import apply_percentage_stat_modifiers

__all__ = [
    # Backgrounds
    "Background",
    "register_background",
    "get_background",
    "all_backgrounds",
    "backgrounds_for_class",
    # Traits
    "Trait",
    "register_trait",
    "get_trait",
    "all_traits",
    "traits_by_category",
    "trait_synergy_bonus",
    # Appearance
    "AppearanceConfig",
    # Stat Distribution
    "StatDistribution",
    # Stat Helpers
    "apply_percentage_stat_modifiers",
]

