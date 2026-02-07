"""
Commander AI Profile.

Coordinates allies, buffs team, calls focus fire.
"""

from typing import List, Optional, TYPE_CHECKING
import random

from systems.statuses import has_status
from engine.battle.types import BattleUnit
from ..profiles import BaseAIProfile
from ..threat import calculate_threat_value
from ..coordination import should_focus_fire

if TYPE_CHECKING:
    from ..core import BattleAI


class CommanderProfile(BaseAIProfile):
    """Commander AI: Coordinates allies, buffs team, focus fire."""
    
    def __init__(self):
        super().__init__("commander")
    
    def choose_target(self, unit: BattleUnit, targets: List[BattleUnit], ai: "BattleAI") -> Optional[BattleUnit]:
        """Commanders prioritize focus fire targets."""
        if not targets:
            return None
        
        # Check for focus fire opportunities
        focus_targets = [t for t in targets if should_focus_fire(t, ai.coordination, min_focusers=1)]
        if focus_targets:
            # Among focus targets, choose highest threat
            return max(focus_targets, key=calculate_threat_value)
        
        # Otherwise, coordinate on highest threat
        return max(targets, key=calculate_threat_value)
    
    def execute_turn(self, unit: BattleUnit, ai: "BattleAI", hp_ratio: float) -> None:
        """Execute commander turn: coordinate and buff team."""
        scene = ai.scene
        weapon_range = scene.combat._get_weapon_range(unit)
        
        # Buff allies first
        buff_skill = unit.skills.get("buff_ally")
        war_cry = unit.skills.get("war_cry")
        
        if buff_skill:
            cd = unit.cooldowns.get(buff_skill.id, 0)
            if cd == 0:
                ally_to_buff = ai.find_ally_to_buff(unit, max_range=2)
                if ally_to_buff and random.random() < 0.6:
                    if scene._use_skill_targeted(unit, buff_skill, ally_to_buff, for_ai=True):
                        return
        
        if war_cry:
            cd = unit.cooldowns.get(war_cry.id, 0)
            can_use, _ = unit.has_resources_for_skill(war_cry, scene.combat)
            if cd == 0 and can_use:
                # Use war cry if multiple allies nearby
                allies = ai.allies_in_range(unit, 2, use_chebyshev=True)
                if len(allies) >= 2 and random.random() < 0.5:
                    if scene._use_skill(unit, war_cry, for_ai=True):
                        return
        
        # Coordinate focus fire
        enemies_in_range = ai.enemies_in_range(unit, weapon_range, use_chebyshev=(weapon_range == 1))
        if enemies_in_range:
            # Get focus target from coordination manager
            focus_target = ai.coordination.get_focus_target(ai.scene.enemy_units)
            
            if focus_target and focus_target in enemies_in_range:
                # Update coordination
                ai.coordination.update_target_assignment(unit, focus_target)
                
                # Use mark_target to help team focus
                mark_skill = unit.skills.get("mark_target")
                if mark_skill:
                    cd = unit.cooldowns.get(mark_skill.id, 0)
                    can_use, _ = unit.has_resources_for_skill(mark_skill, scene.combat)
                    if cd == 0 and can_use:
                        if not has_status(focus_target.statuses, "marked"):
                            if scene._use_skill_targeted(unit, mark_skill, focus_target, for_ai=True):
                                return
                
                # Attack focus target
                ai.perform_basic_attack(unit, target=focus_target)
                return
            
            # No focus target, choose best target
            target = self.choose_target(unit, enemies_in_range, ai)
            if target:
                ai.coordination.update_target_assignment(unit, target)
                ai.perform_basic_attack(unit, target=target)
                return
        
        # Move towards best target
        target = ai.nearest_target(unit, "player")
        if target:
            moved = ai.move_towards_target(unit, target)
            if moved:
                scene._log(f"{unit.name} coordinates the assault.")
            else:
                scene._log(f"{unit.name} directs the battle.")
        else:
            scene.status = "victory"
            scene._log("The foes scatter.")
        
        scene._next_turn()
