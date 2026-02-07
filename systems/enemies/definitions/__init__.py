"""
Enemy archetype and pack definitions.

This module contains all enemy archetype and pack template definitions.
Definitions are organized by game phase for better maintainability.

Structure:
- early_game.py: Tier 1 archetypes (Difficulty 10-30)
- mid_game.py: Tier 2 archetypes (Difficulty 40-69)
- late_game.py: Tier 3 archetypes (Difficulty 70-90+)
- overworld_parties.py: Party archetypes (guards, rangers, etc.)
- packs.py: All pack templates
"""

# Import all definition modules to register their archetypes and packs
from . import early_game
from . import mid_game
from . import late_game
from . import overworld_parties
from . import packs


def register_all_definitions() -> None:
    """Register all enemy archetypes and pack templates."""
    early_game.register_early_game_archetypes()
    mid_game.register_mid_game_archetypes()
    late_game.register_late_game_archetypes()
    overworld_parties.register_overworld_party_archetypes()
    packs.register_all_packs()
