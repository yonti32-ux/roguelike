"""
Elite enemy system.

Handles elite enemy variants with enhanced stats and visual indicators.
"""

from typing import Tuple
import random

# Elite spawn chance per enemy (can be overridden by floor)
BASE_ELITE_SPAWN_CHANCE = 0.15  # 15% chance for any enemy to spawn as elite

# Elite stat multipliers (applied to base stats)
ELITE_HP_MULTIPLIER = 1.5  # +50% HP
ELITE_ATTACK_MULTIPLIER = 1.25  # +25% attack
ELITE_DEFENSE_MULTIPLIER = 1.2  # +20% defense
ELITE_XP_MULTIPLIER = 2.0  # +100% XP (elites are worth more)


def is_elite_spawn(floor_index: int, base_chance: float = BASE_ELITE_SPAWN_CHANCE) -> bool:
    """
    Determine if an enemy should spawn as elite.
    
    Args:
        floor_index: Current floor depth
        base_chance: Base spawn chance (defaults to BASE_ELITE_SPAWN_CHANCE)
    
    Returns:
        True if this enemy should be elite
    """
    # Elite chance scales slightly with floor depth (more elites deeper)
    # Floors 1-2: base chance
    # Floors 3-4: +5% chance
    # Floors 5+: +10% chance
    if floor_index <= 2:
        chance = base_chance
    elif floor_index <= 4:
        chance = base_chance + 0.05
    else:
        chance = base_chance + 0.10
    
    return random.random() < chance


def apply_elite_modifiers(
    max_hp: int,
    attack_power: int,
    defense: int,
    xp_reward: int,
) -> Tuple[int, int, int, int]:
    """
    Apply elite stat multipliers to enemy stats.
    
    Args:
        max_hp: Base max HP
        attack_power: Base attack power
        defense: Base defense
        xp_reward: Base XP reward
    
    Returns:
        Tuple of (elite_max_hp, elite_attack_power, elite_defense, elite_xp_reward)
    """
    elite_hp = int(max_hp * ELITE_HP_MULTIPLIER)
    elite_attack = int(attack_power * ELITE_ATTACK_MULTIPLIER)
    elite_defense = int(defense * ELITE_DEFENSE_MULTIPLIER)
    elite_xp = int(xp_reward * ELITE_XP_MULTIPLIER)
    
    return elite_hp, elite_attack, elite_defense, elite_xp


def make_enemy_elite(enemy, floor_index: int) -> None:
    """
    Convert an existing enemy to an elite variant.
    
    This modifies the enemy in-place, applying:
    - Enhanced stats (HP, attack, defense, XP)
    - Elite name prefix ("Elite")
    - Elite flag for visual/mechanical identification
    
    Args:
        enemy: Enemy entity to make elite
        floor_index: Current floor (for stat scaling)
    """
    from .registry import get_archetype
    
    # Mark as elite
    setattr(enemy, "is_elite", True)
    
    # Get current stats (or compute from archetype if needed)
    max_hp = getattr(enemy, "max_hp", 12)
    attack_power = getattr(enemy, "attack_power", 4)
    defense = getattr(enemy, "defense", 0)
    xp_reward = getattr(enemy, "xp_reward", 5)
    
    # Apply elite modifiers
    elite_hp, elite_attack, elite_defense, elite_xp = apply_elite_modifiers(
        max_hp, attack_power, defense, xp_reward
    )
    
    # Update stats
    setattr(enemy, "max_hp", elite_hp)
    setattr(enemy, "hp", elite_hp)  # Full heal when becoming elite
    setattr(enemy, "attack_power", elite_attack)
    setattr(enemy, "defense", elite_defense)
    setattr(enemy, "xp_reward", elite_xp)
    
    # Update name with "Elite" prefix
    enemy_type = getattr(enemy, "enemy_type", "Enemy")
    if not enemy_type.startswith("Elite "):
        setattr(enemy, "enemy_type", f"Elite {enemy_type}")
        # Also update the original name for display
        setattr(enemy, "original_name", enemy_type)
    
    # Elite visual indicator: slightly brighter/more vibrant color
    # We'll use a glow effect in rendering, but also tint the base color
    base_color = getattr(enemy, "color", (200, 80, 80))
    # Make elite enemies slightly brighter and more saturated
    elite_color = (
        min(255, int(base_color[0] * 1.2)),
        min(255, int(base_color[1] * 1.15)),
        min(255, int(base_color[2] * 1.1)),
    )
    setattr(enemy, "color", elite_color)
