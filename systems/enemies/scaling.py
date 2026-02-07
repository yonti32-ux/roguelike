"""
Enemy stat scaling functions.

Handles scaling enemy stats based on floor/difficulty level.
"""

from .types import EnemyArchetype


def compute_scaled_stats(arch: EnemyArchetype, floor_index: int) -> tuple[int, int, int, int, int]:
    """
    Scale an archetype's stats for the given floor.

    Returns (max_hp, attack_power, defense, xp_reward, initiative).
    
    Note: Initiative scaling is intentionally slow to prevent enemies from always
    outpacing the player. Default init_per_floor is 0.0, and even when set, it
    should be kept low (e.g., 0.2-0.5 per floor max) to maintain balance.
    """
    level = max(1, floor_index)
    max_hp = int(arch.base_hp + arch.hp_per_floor * (level - 1))
    attack = int(arch.base_attack + arch.atk_per_floor * (level - 1))
    defense = int(arch.base_defense + arch.def_per_floor * (level - 1))
    xp = int(arch.base_xp + arch.xp_per_floor * (level - 1))
    
    # Initiative scaling: cap at reasonable maximum to prevent runaway scaling
    # Player gets +1 initiative every 2 levels, so enemies should scale slower
    raw_initiative = arch.base_initiative + arch.init_per_floor * (level - 1)
    # Cap initiative scaling: base + floor-based growth shouldn't exceed base + (floor * 0.5)
    # This ensures enemies don't outpace player level-based growth too much
    max_initiative = arch.base_initiative + (level - 1) * 0.5
    initiative = int(min(raw_initiative, max_initiative))
    
    return max_hp, attack, defense, xp, initiative
