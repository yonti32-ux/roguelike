"""
Skill prioritization system.

Evaluates and prioritizes skills based on situation, context, and tactical value.
"""

from typing import List, Optional, Tuple
from systems.statuses import has_status
from engine.battle.types import BattleUnit
from systems.skills import Skill


class SkillPrioritizer:
    """
    Evaluates skills and determines when they should be used.
    
    Considers:
    - Current situation (HP, enemy positions, status effects)
    - Skill effectiveness (damage, utility, cooldown)
    - Resource costs (mana, stamina)
    - Combo potential
    """
    
    def __init__(self, scene):
        self.scene = scene
    
    def evaluate_skill_value(
        self,
        unit: BattleUnit,
        skill: Skill,
        hp_ratio: float,
        enemies_in_range: List[BattleUnit],
        allies_in_range: List[BattleUnit],
    ) -> float:
        """
        Evaluate the value of using a skill in the current situation.
        
        Returns:
            Value score (higher = better to use now)
            Negative values mean don't use this skill
        """
        value = 0.0
        
        # Check if skill is on cooldown or can't be used
        cd = unit.cooldowns.get(skill.id, 0)
        if cd > 0:
            return -100.0  # Can't use
        
        can_use, reason = unit.has_resources_for_skill(skill, self.scene.combat)
        if not can_use:
            return -100.0  # Can't afford
        
        # Base value from skill power
        value += skill.base_power * 10.0
        
        # Cooldown consideration (longer cooldown = save for better moments)
        if skill.cooldown > 3:
            value -= 5.0  # Prefer to save powerful skills
        
        # Target mode considerations
        if skill.target_mode == "self":
            # Self-buffs: more valuable when low HP or when about to engage
            if hp_ratio < 0.5:
                value += 20.0
            if hp_ratio < 0.3:
                value += 15.0
            if skill.id == "berserker_rage" and hp_ratio < 0.3:
                value += 30.0  # Very valuable when low HP
            if skill.id == "regeneration" and hp_ratio < 0.5:
                value += 25.0
        
        elif skill.target_mode in ("adjacent_enemy", "any_enemy"):
            # Offensive skills: more valuable when enemies are in range
            if enemies_in_range:
                value += 15.0
                # More valuable if we can hit multiple targets (AoE)
                if getattr(skill, "aoe_radius", 0) > 0:
                    # Count potential targets in AoE
                    aoe_targets = len(enemies_in_range)  # Simplified
                    value += aoe_targets * 10.0
                
                # Debuff skills: more valuable on healthy enemies
                if skill.id in ("mark_target", "dark_hex", "crippling_blow"):
                    healthy_enemies = [e for e in enemies_in_range if e.hp > e.max_hp * 0.5]
                    if healthy_enemies:
                        value += 10.0
        
        # Status effect considerations
        if skill.id == "life_drain" and hp_ratio < 0.5:
            value += 20.0  # More valuable when low HP
        
        if skill.id in ("poison_strike", "disease_strike"):
            # More valuable on enemies without poison/disease
            unpoisoned = [e for e in enemies_in_range if not has_status(e.statuses, "poisoned")]
            if unpoisoned:
                value += 8.0
        
        # Combo potential (simplified)
        # If we have mark_target and heavy_slam, prefer marking first
        if skill.id == "mark_target":
            has_heavy_slam = "heavy_slam" in unit.skills
            if has_heavy_slam:
                value += 5.0  # Set up for combo
        
        return value
    
    def get_best_skill(
        self,
        unit: BattleUnit,
        hp_ratio: float,
        enemies_in_range: List[BattleUnit],
        allies_in_range: List[BattleUnit],
    ) -> Optional[Tuple[Skill, float]]:
        """
        Get the best skill to use right now.
        
        Returns:
            Tuple of (skill, value) or None if no good skills
        """
        best_skill = None
        best_value = -1000.0
        
        for skill in unit.skills.values():
            value = self.evaluate_skill_value(unit, skill, hp_ratio, enemies_in_range, allies_in_range)
            if value > best_value:
                best_value = value
                best_skill = skill
        
        if best_skill and best_value > 0:
            return (best_skill, best_value)
        return None


def evaluate_skill_value(
    unit: BattleUnit,
    skill: Skill,
    hp_ratio: float,
    enemies_in_range: List[BattleUnit],
    allies_in_range: List[BattleUnit],
    scene,
) -> float:
    """
    Convenience function to evaluate a skill's value.
    
    Args:
        unit: The unit considering the skill
        skill: The skill to evaluate
        hp_ratio: Unit's current HP ratio
        enemies_in_range: List of enemies in range
        allies_in_range: List of allies in range
        scene: Battle scene reference
        
    Returns:
        Value score
    """
    prioritizer = SkillPrioritizer(scene)
    return prioritizer.evaluate_skill_value(unit, skill, hp_ratio, enemies_in_range, allies_in_range)
