"""
Ally stat scaling functions.

Handles scaling ally stats based on player level.
"""

from .types import AllyArchetype


def compute_scaled_stats(arch: AllyArchetype, player_level: int) -> tuple[int, int, int, float, int]:
    """
    Scale an ally archetype's stats for the given player level.
    
    Allies scale to match the player's level, but are typically slightly weaker
    to maintain player as the primary combatant.
    
    Returns (max_hp, attack_power, defense, skill_power, initiative).
    """
    level = max(1, player_level)
    
    # Scale stats based on level
    max_hp = int(arch.base_hp + arch.hp_per_level * (level - 1))
    attack = int(arch.base_attack + arch.atk_per_level * (level - 1))
    defense = int(arch.base_defense + arch.def_per_level * (level - 1))
    skill_power = float(arch.base_skill_power + arch.skill_power_per_level * (level - 1))
    
    # Initiative scaling (similar to enemies, but allies can be slightly faster)
    initiative = int(arch.base_initiative + arch.init_per_level * (level - 1))
    
    return max_hp, attack, defense, skill_power, initiative
