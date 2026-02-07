"""
Enemy system module.

This module provides enemy archetypes, pack templates, and related functionality.
The module has been refactored into a modular structure for better organization.

All public APIs are exported from this module for backward compatibility.
"""

# Import from the new modular structure
from .types import EnemyArchetype, EnemyPackTemplate
from .registry import (
    ENEMY_ARCHETYPES, ENEMY_PACKS, UNIQUE_ROOM_ENEMIES,
    register_archetype, get_archetype, register_pack,
)
from .selection import (
    get_enemies_by_tag, get_enemies_in_difficulty_range,
    get_enemies_for_floor_range, floor_to_difficulty_range,
    choose_archetype_for_player_level, choose_archetype_for_floor,
    choose_pack_for_floor,
)
from .scaling import compute_scaled_stats
from .elite import (
    BASE_ELITE_SPAWN_CHANCE, ELITE_HP_MULTIPLIER,
    ELITE_ATTACK_MULTIPLIER, ELITE_DEFENSE_MULTIPLIER,
    ELITE_XP_MULTIPLIER, is_elite_spawn,
    apply_elite_modifiers, make_enemy_elite,
)
from .synergies import (
    calculate_pack_synergies,
    apply_synergies_to_enemies,
)

# Register all definitions on import
from .definitions import register_all_definitions
register_all_definitions()

# Backward compatibility alias (if used anywhere)
get_enemy_archetype = get_archetype

# Export everything for backward compatibility
__all__ = [
    "EnemyArchetype",
    "EnemyPackTemplate",
    "ENEMY_ARCHETYPES",
    "ENEMY_PACKS",
    "UNIQUE_ROOM_ENEMIES",
    "register_archetype",
    "get_archetype",
    "get_enemy_archetype",  # Backward compatibility alias
    "register_pack",
    "get_enemies_by_tag",
    "get_enemies_in_difficulty_range",
    "get_enemies_for_floor_range",
    "floor_to_difficulty_range",
    "choose_archetype_for_player_level",
    "choose_archetype_for_floor",
    "choose_pack_for_floor",
    "compute_scaled_stats",
    "BASE_ELITE_SPAWN_CHANCE",
    "ELITE_HP_MULTIPLIER",
    "ELITE_ATTACK_MULTIPLIER",
    "ELITE_DEFENSE_MULTIPLIER",
    "ELITE_XP_MULTIPLIER",
    "is_elite_spawn",
    "apply_elite_modifiers",
    "make_enemy_elite",
    # Synergy system
    # Synergy system
    "calculate_pack_synergies",
    "apply_synergies_to_enemies",
]

# Export utility and validation functions (optional imports)
# These are available but not in __all__ to keep the main API clean
# Import them explicitly: from systems.enemies.utils import ...
# or: from systems.enemies.validation import ...
