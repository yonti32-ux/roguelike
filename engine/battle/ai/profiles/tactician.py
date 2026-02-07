"""
Tactician AI Profile.

Smart fighters that use positioning, combos, and threat assessment.
"""

from typing import List, Optional, TYPE_CHECKING
import random

from systems.statuses import has_status
from engine.battle.types import BattleUnit
from ..profiles import BaseAIProfile
from ..threat import calculate_threat_value, rank_targets_by_threat
from ..coordination import should_focus_fire

if TYPE_CHECKING:
    from ..core import BattleAI


class TacticianProfile(BaseAIProfile):
    """Tactician AI: Smart positioning, combos, threat assessment."""
    
    def __init__(self):
        super().__init__("tactician")
    
    def choose_target(self, unit: BattleUnit, targets: List[BattleUnit], ai: "BattleAI") -> Optional[BattleUnit]:
        """Tacticians prioritize focus fire targets, then high-threat enemies."""
        if not targets:
            return None
        
        # Check for focus fire opportunities
        focus_targets = [t for t in targets if should_focus_fire(t, ai.coordination, min_focusers=1)]
        if focus_targets:
            # Among focus targets, choose highest threat
            return max(focus_targets, key=calculate_threat_value)
        
        # Otherwise, use threat assessment
        ranked = rank_targets_by_threat(targets)
        return ranked[0] if ranked else None
    
    def execute_turn(self, unit: BattleUnit, ai: "BattleAI", hp_ratio: float) -> None:
        """Execute tactician turn: smart positioning and combos."""
        scene = ai.scene
        weapon_range = scene.combat._get_weapon_range(unit)
        is_melee = weapon_range == 1
        
        # Find targets
        enemies_in_range = ai.enemies_in_range(unit, weapon_range, use_chebyshev=is_melee)
        
        # Set up combos: mark target first if we have heavy_slam
        if enemies_in_range:
            mark_skill = unit.skills.get("mark_target")
            heavy_slam = unit.skills.get("heavy_slam")
            
            # If we have both skills, try to set up combo
            if mark_skill and heavy_slam:
                mark_cd = unit.cooldowns.get(mark_skill.id, 0)
                heavy_cd = unit.cooldowns.get(heavy_slam.id, 0)
                
                # Mark unmarked high-threat targets
                if mark_cd == 0:
                    can_use, _ = unit.has_resources_for_skill(mark_skill, scene.combat)
                    if can_use:
                        unmarked = [t for t in enemies_in_range if not has_status(t.statuses, "marked")]
                        if unmarked:
                            target = max(unmarked, key=calculate_threat_value)
                            if scene._use_skill_targeted(unit, mark_skill, target, for_ai=True):
                                return
                
                # Use heavy_slam on marked targets
                if heavy_cd == 0:
                    can_use, _ = unit.has_resources_for_skill(heavy_slam, scene.combat)
                    if can_use:
                        marked = [t for t in enemies_in_range if has_status(t.statuses, "marked")]
                        if marked and random.random() < 0.8:  # High chance to combo
                            target = max(marked, key=calculate_threat_value)
                            if scene._use_skill_targeted(unit, heavy_slam, target, for_ai=True):
                                return
        
        # Smart positioning: try to flank if possible
        target = ai.nearest_target(unit, "player")
        if target and not scene.combat.is_flanking(unit, target):
            flank_pos = ai.positioning.find_flanking_position(unit, target)
            if flank_pos:
                fx, fy = flank_pos
                dx = fx - unit.gx
                dy = fy - unit.gy
                if abs(dx) > 0:
                    dx = 1 if dx > 0 else -1
                if abs(dy) > 0:
                    dy = 1 if dy > 0 else -1
                if scene._try_move_unit(unit, dx, dy):
                    scene._log(f"{unit.name} maneuvers tactically.")
                    scene._next_turn()
                    return
        
        # Use offensive skills intelligently
        if enemies_in_range:
            # Try crippling blow on high-threat targets
            crippling_blow = unit.skills.get("crippling_blow")
            if crippling_blow:
                cd = unit.cooldowns.get(crippling_blow.id, 0)
                can_use, _ = unit.has_resources_for_skill(crippling_blow, scene.combat)
                if cd == 0 and can_use:
                    high_threat = rank_targets_by_threat(enemies_in_range)[:2]  # Top 2 threats
                    if high_threat and random.random() < 0.6:
                        target = high_threat[0]
                        if scene._use_skill_targeted(unit, crippling_blow, target, for_ai=True):
                            return
            
            # Basic attack with smart targeting
            target = self.choose_target(unit, enemies_in_range, ai)
            if target:
                ai.perform_basic_attack(unit, target=target)
                return
        
        # Move towards highest threat target
        if target:
            moved = ai.move_towards_target(unit, target)
            if moved:
                scene._log(f"{unit.name} advances strategically.")
            else:
                scene._log(f"{unit.name} holds position.")
        else:
            scene.status = "victory"
            scene._log("The foes scatter.")
        
        scene._next_turn()
