"""
Faction management system.

Handles faction relations, faction-based logic, and faction queries.
"""

from .faction_manager import FactionManager
from .faction_generator import (
    generate_factions_for_world,
    generate_random_factions,
    generate_faction_name,
    generate_faction_color,
)

__all__ = [
    "FactionManager",
    "generate_factions_for_world",
    "generate_random_factions",
    "generate_faction_name",
    "generate_faction_color",
]

