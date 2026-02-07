"""
Ally synergy system for pack bonuses.

When certain ally types are together, they gain bonuses.
This makes ally composition more tactical and interesting.
"""

from typing import Dict, List
from engine.battle.types import BattleUnit
from .registry import get_archetype


def calculate_pack_synergies(allies: List[BattleUnit]) -> Dict[str, float]:
    """
    Calculate synergy bonuses for a pack of allies.
    
    Args:
        allies: List of ally BattleUnits in the pack
    
    Returns:
        Dict of stat multipliers (e.g., {"attack_mult": 1.1, "hp_mult": 1.05})
    """
    bonuses = {
        "attack_mult": 1.0,
        "hp_mult": 1.0,
        "defense_mult": 1.0,
        "skill_power_mult": 1.0,
        "initiative_bonus": 0,
        "movement_bonus": 0,
    }
    
    if not allies:
        return bonuses
    
    # Count ally types by tags
    guardian_count = 0
    ranger_count = 0
    military_count = 0
    merchant_count = 0
    civilian_count = 0
    support_count = 0
    elite_count = 0
    
    for ally in allies:
        arch_id = getattr(ally.entity, "ally_archetype_id", None)
        if not arch_id:
            continue
        
        try:
            arch = get_archetype(arch_id)
            tags = getattr(arch, "tags", [])
            
            # Count by tags
            if "guardian" in tags:
                guardian_count += 1
            if "ranger" in tags or "skirmisher" in tags:
                ranger_count += 1
            if "military" in tags:
                military_count += 1
            if "merchant" in tags:
                merchant_count += 1
            if "civilian" in tags:
                civilian_count += 1
            if "support" in tags:
                support_count += 1
            if "elite" in tags:
                elite_count += 1
        except (KeyError, AttributeError):
            continue
    
    # Apply synergies (balanced bonuses for allies)
    
    # Guard Formation: 2+ guardians = +10% defense
    if guardian_count >= 2:
        bonuses["defense_mult"] += 0.10
    
    # Ranger Coordination: 2+ rangers = +15% attack (flanking bonus)
    if ranger_count >= 2:
        bonuses["attack_mult"] += 0.15
    
    # Military Discipline: 2+ military = +10% attack, +5% defense
    if military_count >= 2:
        bonuses["attack_mult"] += 0.10
        bonuses["defense_mult"] += 0.05
    
    # Caravan Defense: 2+ merchant guards = +10% HP
    if merchant_count >= 2:
        bonuses["hp_mult"] += 0.10
    
    # Elite Coordination: 1+ elite = +5% all stats per elite (max +15%)
    if elite_count >= 1:
        elite_bonus = min(0.15, 0.05 * elite_count)
        bonuses["attack_mult"] += elite_bonus
        bonuses["defense_mult"] += elite_bonus
        bonuses["hp_mult"] += elite_bonus
    
    # Support Network: 1+ support = +20% skill power
    if support_count >= 1:
        bonuses["skill_power_mult"] += 0.20
    
    # Combined Tactics: Mix of guardian + ranger = +1 movement
    if guardian_count >= 1 and ranger_count >= 1:
        bonuses["movement_bonus"] += 1
    
    # Professional Teamwork: 2+ military/mercenary = +1 initiative
    if (military_count >= 2) or (military_count >= 1 and merchant_count >= 1):
        bonuses["initiative_bonus"] += 1
    
    return bonuses


def apply_synergies_to_allies(allies: List[BattleUnit]) -> None:
    """
    Apply synergy bonuses to a list of allies.
    
    Modifies the allies' stats in place based on pack synergies.
    """
    if not allies:
        return
    
    bonuses = calculate_pack_synergies(allies)
    
    for ally in allies:
        # Apply multipliers to base stats
        if bonuses["attack_mult"] != 1.0:
            current_attack = getattr(ally.entity, "attack_power", 0)
            new_attack = int(current_attack * bonuses["attack_mult"])
            setattr(ally.entity, "attack_power", new_attack)
            # Also update max for display
            if hasattr(ally, "max_attack"):
                setattr(ally, "max_attack", new_attack)
        
        if bonuses["hp_mult"] != 1.0:
            current_max_hp = getattr(ally.entity, "max_hp", 0)
            current_hp = getattr(ally.entity, "hp", 0)
            new_max_hp = int(current_max_hp * bonuses["hp_mult"])
            # Maintain HP ratio
            hp_ratio = current_hp / current_max_hp if current_max_hp > 0 else 1.0
            new_hp = int(new_max_hp * hp_ratio)
            setattr(ally.entity, "max_hp", new_max_hp)
            setattr(ally.entity, "hp", new_hp)
        
        if bonuses["defense_mult"] != 1.0:
            current_defense = getattr(ally.entity, "defense", 0)
            new_defense = int(current_defense * bonuses["defense_mult"])
            setattr(ally.entity, "defense", new_defense)
        
        if bonuses["skill_power_mult"] != 1.0:
            current_sp = getattr(ally.entity, "skill_power", 1.0)
            new_sp = float(current_sp * bonuses["skill_power_mult"])
            setattr(ally.entity, "skill_power", new_sp)
        
        # Apply flat bonuses
        if bonuses["initiative_bonus"] > 0:
            current_init = getattr(ally.entity, "initiative", 10)
            setattr(ally.entity, "initiative", current_init + bonuses["initiative_bonus"])
        
        if bonuses["movement_bonus"] > 0:
            ally.max_movement_points += bonuses["movement_bonus"]
            ally.current_movement_points = min(
                ally.current_movement_points + bonuses["movement_bonus"],
                ally.max_movement_points
            )
