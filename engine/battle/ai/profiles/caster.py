"""
Caster AI Profile.

Ranged spellcasters that maintain distance and use debuffs.
"""

from typing import List, Optional, TYPE_CHECKING
import random

from systems.statuses import has_status
from engine.battle.types import BattleUnit
from ..profiles import BaseAIProfile
from ..threat import calculate_threat_value

if TYPE_CHECKING:
    from ..core import BattleAI


class CasterProfile(BaseAIProfile):
    """Caster AI: Maintain distance, use debuffs, target low HP."""
    
    def __init__(self):
        super().__init__("caster")
    
    def choose_target(self, unit: BattleUnit, targets: List[BattleUnit], ai: "BattleAI") -> Optional[BattleUnit]:
        """Casters prioritize marked/cursed targets, then low HP."""
        if not targets:
            return None
        
        # Prioritize debuffed targets
        debuffed = [t for t in targets if has_status(t.statuses, "marked") or has_status(t.statuses, "cursed")]
        if debuffed:
            return min(debuffed, key=lambda t: t.hp)
        
        # Otherwise, target low HP
        return min(targets, key=lambda t: t.hp)
    
    def execute_turn(self, unit: BattleUnit, ai: "BattleAI", hp_ratio: float) -> None:
        """Execute caster turn: maintain distance and cast spells."""
        scene = ai.scene
        weapon_range = scene.combat._get_weapon_range(unit)
        is_ranged = weapon_range > 1
        
        # Find targets
        enemies_in_range = ai.enemies_in_range(unit, weapon_range, use_chebyshev=False)
        
        # Use debuff skills first
        if enemies_in_range:
            # Try mark_target on high-threat targets
            mark_skill = unit.skills.get("mark_target")
            if mark_skill:
                cd = unit.cooldowns.get(mark_skill.id, 0)
                can_use, _ = unit.has_resources_for_skill(mark_skill, scene.combat)
                if cd == 0 and can_use:
                    unmarked = [t for t in enemies_in_range if not has_status(t.statuses, "marked")]
                    if unmarked and random.random() < 0.7:
                        target = max(unmarked, key=calculate_threat_value)
                        if scene._use_skill_targeted(unit, mark_skill, target, for_ai=True):
                            return
            
            # Try dark_hex on healthy targets
            dark_hex = unit.skills.get("dark_hex")
            if dark_hex:
                cd = unit.cooldowns.get(dark_hex.id, 0)
                can_use, _ = unit.has_resources_for_skill(dark_hex, scene.combat)
                if cd == 0 and can_use:
                    healthy_targets = [t for t in enemies_in_range if t.hp > t.max_hp * 0.5]
                    if healthy_targets and random.random() < 0.6:
                        target = max(healthy_targets, key=calculate_threat_value)
                        if scene._use_skill_targeted(unit, dark_hex, target, for_ai=True):
                            return
        
        # Maintain optimal range for ranged units
        target = ai.nearest_target(unit, "player")
        if target and is_ranged:
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
                        scene._log(f"{unit.name} backs away.")
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
                # In range, maybe reposition
                if random.random() < 0.3:
                    moved = ai.move_towards_target(unit, target)
                    if moved:
                        scene._log(f"{unit.name} repositions.")
                    else:
                        scene._log(f"{unit.name} holds position.")
                else:
                    # Attack if in range
                    if enemies_in_range:
                        target = self.choose_target(unit, enemies_in_range, ai)
                        if target:
                            ai.perform_basic_attack(unit, target=target)
                            return
                    scene._log(f"{unit.name} holds position.")
        elif target:
            # Melee caster, move closer (use all movement points)
            moved = ai.move_towards_target(unit, target)
            if moved:
                scene._log(f"{unit.name} advances cautiously.")
            else:
                scene._log(f"{unit.name} hesitates.")
        else:
            scene.status = "victory"
            scene._log("The foes scatter.")
        
        scene._next_turn()
