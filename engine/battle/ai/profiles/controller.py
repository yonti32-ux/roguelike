"""
Controller AI Profile.

Focuses on debuffs, crowd control, and positioning enemies.
"""

from typing import List, Optional, TYPE_CHECKING
import random

from systems.statuses import has_status
from engine.battle.types import BattleUnit
from ..profiles import BaseAIProfile
from ..threat import calculate_threat_value, rank_targets_by_threat

if TYPE_CHECKING:
    from ..core import BattleAI


class ControllerProfile(BaseAIProfile):
    """Controller AI: Debuffs, crowd control, positioning."""
    
    def __init__(self):
        super().__init__("controller")
    
    def choose_target(self, unit: BattleUnit, targets: List[BattleUnit], ai: "BattleAI") -> Optional[BattleUnit]:
        """Controllers prioritize high-threat targets that aren't debuffed."""
        if not targets:
            return None
        
        # Prioritize unmarked high-threat targets
        unmarked = [t for t in targets if not has_status(t.statuses, "marked")]
        if unmarked:
            return max(unmarked, key=calculate_threat_value)
        
        # Otherwise, highest threat
        return max(targets, key=calculate_threat_value)
    
    def execute_turn(self, unit: BattleUnit, ai: "BattleAI", hp_ratio: float) -> None:
        """Execute controller turn: debuff and control enemies."""
        scene = ai.scene
        weapon_range = scene.combat._get_weapon_range(unit)
        
        # Find targets
        enemies_in_range = ai.enemies_in_range(unit, weapon_range, use_chebyshev=False)
        
        # Prioritize debuff skills
        if enemies_in_range:
            # Mark high-threat targets
            mark_skill = unit.skills.get("mark_target")
            if mark_skill:
                cd = unit.cooldowns.get(mark_skill.id, 0)
                can_use, _ = unit.has_resources_for_skill(mark_skill, scene.combat)
                if cd == 0 and can_use:
                    unmarked = [t for t in enemies_in_range if not has_status(t.statuses, "marked")]
                    if unmarked:
                        target = max(unmarked, key=calculate_threat_value)
                        if scene._use_skill_targeted(unit, mark_skill, target, for_ai=True):
                            return
            
            # Dark hex on healthy targets
            dark_hex = unit.skills.get("dark_hex")
            if dark_hex:
                cd = unit.cooldowns.get(dark_hex.id, 0)
                can_use, _ = unit.has_resources_for_skill(dark_hex, scene.combat)
                if cd == 0 and can_use:
                    healthy = [t for t in enemies_in_range if t.hp > t.max_hp * 0.6]
                    if healthy:
                        target = max(healthy, key=calculate_threat_value)
                        if scene._use_skill_targeted(unit, dark_hex, target, for_ai=True):
                            return
            
            # Fear scream (AoE stun) if multiple enemies nearby
            fear_skill = unit.skills.get("fear_scream")
            if fear_skill:
                cd = unit.cooldowns.get(fear_skill.id, 0)
                if cd == 0:
                    nearby = ai.enemies_in_range(unit, 1, use_chebyshev=True)
                    if len(nearby) >= 2 and random.random() < 0.5:
                        # Apply stun to all adjacent enemies
                        for enemy in nearby:
                            from systems.statuses import StatusEffect
                            scene._add_status(enemy, StatusEffect(
                                name="stunned",
                                duration=1,
                                stunned=True,
                            ))
                        unit.cooldowns[fear_skill.id] = fear_skill.cooldown
                        scene._log(f"{unit.name} screams in terror, stunning nearby enemies!")
                        scene._next_turn()
                        return
        
        # Maintain distance for ranged controllers
        target = ai.nearest_target(unit, "player")
        if target and weapon_range > 1:
            dx = abs(target.gx - unit.gx)
            dy = abs(target.gy - unit.gy)
            distance = max(dx, dy)
            
            if distance <= 1:
                # Too close, back away
                dx = unit.gx - target.gx
                dy = unit.gy - target.gy
                if dx != 0 or dy != 0:
                    step_x = 0
                    step_y = 0
                    if abs(dx) >= abs(dy) and dx != 0:
                        step_x = 1 if dx > 0 else -1
                    elif dy != 0:
                        step_y = 1 if dy > 0 else -1
                    if scene._try_move_unit(unit, step_x, step_y):
                        scene._log(f"{unit.name} maintains distance.")
                        scene._next_turn()
                        return
            elif distance > weapon_range:
                # Too far, move closer (use all movement points)
                moved = ai.move_towards_target(unit, target)
                if moved:
                    scene._log(f"{unit.name} advances.")
                else:
                    scene._log(f"{unit.name} hesitates.")
            else:
                # In range, attack if no debuffs to apply
                if enemies_in_range:
                    target = self.choose_target(unit, enemies_in_range, ai)
                    if target:
                        ai.perform_basic_attack(unit, target=target)
                        return
                scene._log(f"{unit.name} maintains control.")
        elif target:
            # Melee controller, move closer (use all movement points)
            moved = ai.move_towards_target(unit, target)
            if moved:
                scene._log(f"{unit.name} advances.")
            else:
                scene._log(f"{unit.name} hesitates.")
        else:
            scene.status = "victory"
            scene._log("The foes scatter.")
        
        scene._next_turn()
