"""
Brute AI Profile.

Aggressive melee fighters that charge forward and target high-threat enemies.
"""

from typing import List, Optional, TYPE_CHECKING
import random

from systems.statuses import has_status
from engine.battle.types import BattleUnit
from ..profiles import BaseAIProfile
from ..threat import calculate_threat_value, rank_targets_by_threat

if TYPE_CHECKING:
    from ..core import BattleAI


class BruteProfile(BaseAIProfile):
    """Brute AI: Charge forward, target high-threat enemies."""
    
    def __init__(self):
        super().__init__("brute")
    
    def choose_target(self, unit: BattleUnit, targets: List[BattleUnit], ai: "BattleAI") -> Optional[BattleUnit]:
        """Brutes prioritize marked targets, then high-threat targets."""
        if not targets:
            return None
        
        # Prioritize marked targets
        marked = [t for t in targets if has_status(t.statuses, "marked")]
        if marked:
            # Among marked, choose highest threat
            return max(marked, key=calculate_threat_value)
        
        # Otherwise, choose highest threat target
        return max(targets, key=calculate_threat_value)
    
    def execute_turn(self, unit: BattleUnit, ai: "BattleAI", hp_ratio: float) -> None:
        """Execute brute turn: charge forward and attack."""
        from settings import BATTLE_AI_DEFENSIVE_HP_THRESHOLD
        
        scene = ai.scene
        weapon_range = scene.combat._get_weapon_range(unit)
        is_melee = weapon_range == 1
        
        # Defensive skills when low HP
        if hp_ratio < BATTLE_AI_DEFENSIVE_HP_THRESHOLD:
            # Berserker rage when very low HP
            if hp_ratio < 0.3:
                rage_skill = unit.skills.get("berserker_rage")
                if rage_skill:
                    cd = unit.cooldowns.get(rage_skill.id, 0)
                    can_use, _ = unit.has_resources_for_skill(rage_skill, scene.combat)
                    if cd == 0 and can_use and random.random() < 0.8:
                        if scene._use_skill(unit, rage_skill, for_ai=True):
                            return
        
        # Find targets
        enemies_in_range = ai.enemies_in_range(unit, weapon_range, use_chebyshev=is_melee)
        
        # Use offensive skills
        if enemies_in_range:
            # Try heavy slam on marked targets
            heavy_slam = unit.skills.get("heavy_slam")
            if heavy_slam:
                cd = unit.cooldowns.get(heavy_slam.id, 0)
                can_use, _ = unit.has_resources_for_skill(heavy_slam, scene.combat)
                if cd == 0 and can_use:
                    marked_targets = [t for t in enemies_in_range if has_status(t.statuses, "marked")]
                    if marked_targets and random.random() < 0.7:
                        target = max(marked_targets, key=calculate_threat_value)
                        if scene._use_skill_targeted(unit, heavy_slam, target, for_ai=True):
                            return
            
            # Basic attack
            target = self.choose_target(unit, enemies_in_range, ai)
            if target:
                ai.perform_basic_attack(unit, target=target)
                return
        
        # Move towards nearest target (use all movement points)
        target = ai.nearest_target(unit, "player")
        if target:
            moved = ai.move_towards_target(unit, target)
            if moved:
                scene._log(f"{unit.name} charges forward.")
            else:
                scene._log(f"{unit.name} hesitates.")
        else:
            scene.status = "victory"
            scene._log("The foes scatter.")
        
        scene._next_turn()
