"""
Berserker AI Profile.

Aggressive fighters that ignore defense when low HP and charge recklessly.
"""

from typing import List, Optional, TYPE_CHECKING
import random

from systems.statuses import has_status
from engine.battle.types import BattleUnit
from ..profiles import BaseAIProfile
from ..threat import calculate_threat_value

if TYPE_CHECKING:
    from ..core import BattleAI


class BerserkerProfile(BaseAIProfile):
    """Berserker AI: Aggressive, ignores defense when low HP."""
    
    def __init__(self):
        super().__init__("berserker")
    
    def choose_target(self, unit: BattleUnit, targets: List[BattleUnit], ai: "BattleAI") -> Optional[BattleUnit]:
        """Berserkers prioritize nearest target, then highest attack."""
        if not targets:
            return None
        
        # When low HP, just charge the nearest
        if unit.hp < unit.max_hp * 0.3:
            return min(targets, key=lambda t: abs(t.gx - unit.gx) + abs(t.gy - unit.gy))
        
        # Otherwise, target highest attack power
        return max(targets, key=lambda t: t.attack_power)
    
    def execute_turn(self, unit: BattleUnit, ai: "BattleAI", hp_ratio: float) -> None:
        """Execute berserker turn: aggressive and reckless."""
        scene = ai.scene
        weapon_range = scene.combat._get_weapon_range(unit)
        is_melee = weapon_range == 1
        
        # When very low HP, use berserker rage immediately
        if hp_ratio < 0.3:
            rage_skill = unit.skills.get("berserker_rage")
            if rage_skill:
                cd = unit.cooldowns.get(rage_skill.id, 0)
                can_use, _ = unit.has_resources_for_skill(rage_skill, scene.combat)
                if cd == 0 and can_use:
                    if scene._use_skill(unit, rage_skill, for_ai=True):
                        return
        
        # When low HP, ignore defensive skills and just attack
        if hp_ratio < 0.5:
            enemies_in_range = ai.enemies_in_range(unit, weapon_range, use_chebyshev=is_melee)
            if enemies_in_range:
                # Use heavy_slam recklessly
                heavy_slam = unit.skills.get("heavy_slam")
                if heavy_slam:
                    cd = unit.cooldowns.get(heavy_slam.id, 0)
                    can_use, _ = unit.has_resources_for_skill(heavy_slam, scene.combat)
                    if cd == 0 and can_use and random.random() < 0.7:
                        target = self.choose_target(unit, enemies_in_range, ai)
                        if target:
                            if scene._use_skill_targeted(unit, heavy_slam, target, for_ai=True):
                                return
                
                # Basic attack
                target = self.choose_target(unit, enemies_in_range, ai)
                if target:
                    ai.perform_basic_attack(unit, target=target)
                    return
        
        # Normal behavior: aggressive but not suicidal
        enemies_in_range = ai.enemies_in_range(unit, weapon_range, use_chebyshev=is_melee)
        
        if enemies_in_range:
            # Use offensive skills aggressively
            heavy_slam = unit.skills.get("heavy_slam")
            if heavy_slam:
                cd = unit.cooldowns.get(heavy_slam.id, 0)
                can_use, _ = unit.has_resources_for_skill(heavy_slam, scene.combat)
                if cd == 0 and can_use and random.random() < 0.5:
                    target = self.choose_target(unit, enemies_in_range, ai)
                    if target:
                        if scene._use_skill_targeted(unit, heavy_slam, target, for_ai=True):
                            return
            
            # Basic attack
            target = self.choose_target(unit, enemies_in_range, ai)
            if target:
                ai.perform_basic_attack(unit, target=target)
                return
        
        # Charge forward recklessly
        target = ai.nearest_target(unit, "player")
        if target:
            moved = ai.move_towards_target(unit, target)
            if moved:
                scene._log(f"{unit.name} charges recklessly!")
            else:
                scene._log(f"{unit.name} rages!")
        else:
            scene.status = "victory"
            scene._log("The foes scatter.")
        
        scene._next_turn()
