"""
Ally archetype definitions.

Registers all ally archetypes for different party types.
"""

from .guardians import register_guardian_archetypes
from .rangers import register_ranger_archetypes
from .merchants import register_merchant_archetypes
from .military import register_military_archetypes
from .specialists import register_specialist_archetypes
from .support import register_support_archetypes


def register_all_ally_archetypes() -> None:
    """Register all ally archetype definitions."""
    register_guardian_archetypes()
    register_ranger_archetypes()
    register_merchant_archetypes()
    register_military_archetypes()
    register_specialist_archetypes()
    register_support_archetypes()