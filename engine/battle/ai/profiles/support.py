"""
Support AI Profile.

Healers and buffers that prioritize helping allies.
"""

from typing import List, Optional, TYPE_CHECKING
import random

from systems.statuses import has_status
from engine.battle.types import BattleUnit
from ..profiles import BaseAIProfile
from ..threat import calculate_threat_value

if TYPE_CHECKING:
    from ..core import BattleAI


class SupportProfile(BaseAIProfile):
    """Support AI: Heal and buff allies, then attack."""
    
    def __init__(self):
        super().__init__("support")
    
    def choose_target(self, unit: BattleUnit, targets: List[BattleUnit], ai: "BattleAI") -> Optional[BattleUnit]:
        """Support units prioritize low HP targets when attacking."""
        if not targets:
            return None
        return min(targets, key=lambda t: t.hp)
    
    def execute_turn(self, unit: BattleUnit, ai: "BattleAI", hp_ratio: float) -> None:
        """Execute support turn: heal/buff allies, then attack."""
        scene = ai.scene
        
        # Check for heal_ally skill
        heal_skill = unit.skills.get("heal_ally")
        if heal_skill:
            cd = unit.cooldowns.get(heal_skill.id, 0)
            if cd == 0:
                injured_ally = ai.find_injured_ally(unit, max_range=1)
                if injured_ally and random.random() < 0.6:
                    # Heal for 30% of ally's max HP
                    heal_amount = max(1, int(injured_ally.max_hp * 0.3))
                    current_hp = getattr(injured_ally.entity, "hp", 0)
                    max_hp = getattr(injured_ally.entity, "max_hp", 1)
                    new_hp = min(max_hp, current_hp + heal_amount)
                    setattr(injured_ally.entity, "hp", new_hp)
                    unit.cooldowns[heal_skill.id] = heal_skill.cooldown
                    scene._log(f"{unit.name} heals {injured_ally.name} for {heal_amount} HP.")
                    scene._next_turn()
                    return
        
        # Check for buff_ally skill
        buff_skill = unit.skills.get("buff_ally")
        if buff_skill:
            cd = unit.cooldowns.get(buff_skill.id, 0)
            if cd == 0:
                ally_to_buff = ai.find_ally_to_buff(unit, max_range=1)
                if ally_to_buff and random.random() < 0.5:
                    if scene._use_skill_targeted(unit, buff_skill, ally_to_buff, for_ai=True):
                        return
        
        # If no support actions, attack
        weapon_range = scene.combat._get_weapon_range(unit)
        enemies_in_range = ai.enemies_in_range(unit, weapon_range, use_chebyshev=(weapon_range == 1))
        
        if enemies_in_range:
            target = self.choose_target(unit, enemies_in_range, ai)
            if target:
                ai.perform_basic_attack(unit, target=target)
                return
        
        # Move towards target
        target = ai.nearest_target(unit, "player")
        if target:
            moved = ai.move_towards_target(unit, target)
            if moved:
                scene._log(f"{unit.name} advances.")
            else:
                scene._log(f"{unit.name} hesitates.")
        else:
            scene.status = "victory"
            scene._log("The foes scatter.")
        
        scene._next_turn()
