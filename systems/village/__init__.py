"""
Village services: inn, shop, recruitment, and companion generation.
"""

from .services import (
    rest_at_inn,
    open_shop,
    open_recruitment,
    recruit_companion,
)
from .companion_generation import (
    generate_random_companion,
    calculate_recruitment_cost,
    generate_companion_name,
    select_random_class,
    assign_starting_perks,
    generate_village_companions,
    AvailableCompanion,
)

__all__ = [
    # Services
    "rest_at_inn",
    "open_shop",
    "open_recruitment",
    "recruit_companion",
    # Companion generation
    "generate_random_companion",
    "calculate_recruitment_cost",
    "generate_companion_name",
    "select_random_class",
    "assign_starting_perks",
    "generate_village_companions",
    "AvailableCompanion",
]

