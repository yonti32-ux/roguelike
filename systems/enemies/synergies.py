"""
Enemy synergy system for pack bonuses.

When certain enemy types are together, they gain bonuses.
This makes pack composition more tactical and interesting.
"""

from typing import Dict, List
from engine.battle.types import BattleUnit
from .registry import get_archetype


def calculate_pack_synergies(enemies: List[BattleUnit]) -> Dict[str, float]:
    """
    Calculate synergy bonuses for a pack of enemies.
    
    Args:
        enemies: List of enemy BattleUnits in the pack
    
    Returns:
        Dict of stat multipliers (e.g., {"attack_mult": 1.1, "hp_mult": 1.05})
    """
    bonuses = {
        "attack_mult": 1.0,
        "hp_mult": 1.0,
        "defense_mult": 1.0,
        "skill_power_mult": 1.0,
    }
    
    if not enemies:
        return bonuses
    
    # Count enemy types by tags
    goblin_count = 0
    undead_count = 0
    cultist_count = 0
    beast_count = 0
    elemental_count = 0
    caster_count = 0
    tank_count = 0
    
    for enemy in enemies:
        arch_id = getattr(enemy.entity, "archetype_id", None)
        if not arch_id:
            continue
        
        try:
            arch = get_archetype(arch_id)
            tags = getattr(arch, "tags", [])
            
            # Count by tags
            if "goblin" in tags:
                goblin_count += 1
            if "undead" in tags:
                undead_count += 1
            if "cultist" in tags:
                cultist_count += 1
            if "beast" in tags:
                beast_count += 1
            if "elemental" in tags:
                elemental_count += 1
            if "caster" in tags or "invoker" in tags:
                caster_count += 1
            if "brute" in tags or "tank" in tags:
                tank_count += 1
        except (KeyError, AttributeError):
            continue
    
    # Apply synergies (balanced bonuses)
    
    # Goblin Pack: 3+ goblins = +10% attack
    if goblin_count >= 3:
        bonuses["attack_mult"] += 0.10
    
    # Undead Horde: 2+ undead = +5% HP per undead (max +25%)
    if undead_count >= 2:
        hp_bonus = min(0.25, 0.05 * undead_count)
        bonuses["hp_mult"] += hp_bonus
    
    # Cultist Circle: 2+ cultists = +1 skill power per cultist (as multiplier)
    if cultist_count >= 2:
        # Convert to multiplier (each cultist adds 5% skill power)
        bonuses["skill_power_mult"] += 0.05 * cultist_count
    
    # Beast Pack: 2+ beasts = +15% speed (not implemented yet, but tracked)
    # Note: Speed bonuses would need to be applied differently
    
    # Elemental Storm: 2+ elementals = +20% skill power
    if elemental_count >= 2:
        bonuses["skill_power_mult"] += 0.20
    
    # Tank Line: 2+ tanks = +10% defense each
    if tank_count >= 2:
        bonuses["defense_mult"] += 0.10 * tank_count
    
    # Caster Support: 2+ casters = +10% skill power
    if caster_count >= 2:
        bonuses["skill_power_mult"] += 0.10
    
    return bonuses


def apply_synergies_to_enemies(enemies: List[BattleUnit]) -> None:
    """
    Apply synergy bonuses to a list of enemies.
    Modifies enemy stats in-place.
    
    Args:
        enemies: List of enemy BattleUnits to apply synergies to
    """
    if not enemies:
        return
    
    synergies = calculate_pack_synergies(enemies)
    
    for enemy in enemies:
        # Apply attack multiplier
        if synergies["attack_mult"] != 1.0:
            base_attack = getattr(enemy.entity, "attack_power", 0)
            new_attack = int(base_attack * synergies["attack_mult"])
            setattr(enemy.entity, "attack_power", new_attack)
        
        # Apply HP multiplier
        if synergies["hp_mult"] != 1.0:
            base_max_hp = getattr(enemy.entity, "max_hp", 1)
            current_hp = getattr(enemy.entity, "hp", base_max_hp)
            new_max_hp = int(base_max_hp * synergies["hp_mult"])
            # Scale current HP proportionally
            hp_ratio = current_hp / base_max_hp if base_max_hp > 0 else 1.0
            new_hp = int(new_max_hp * hp_ratio)
            setattr(enemy.entity, "max_hp", new_max_hp)
            setattr(enemy.entity, "hp", new_hp)
        
        # Apply defense multiplier
        if synergies["defense_mult"] != 1.0:
            base_defense = getattr(enemy.entity, "defense", 0)
            new_defense = int(base_defense * synergies["defense_mult"])
            setattr(enemy.entity, "defense", new_defense)
        
        # Apply skill power multiplier
        if synergies["skill_power_mult"] != 1.0:
            base_skill_power = float(getattr(enemy.entity, "skill_power", 1.0))
            new_skill_power = base_skill_power * synergies["skill_power_mult"]
            setattr(enemy.entity, "skill_power", new_skill_power)
