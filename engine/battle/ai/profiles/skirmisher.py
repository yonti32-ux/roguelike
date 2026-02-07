"""
Skirmisher AI Profile.

Mobile fighters that flank enemies and finish off low-HP targets.
"""

from typing import List, Optional, TYPE_CHECKING
import random

from systems.statuses import has_status
from engine.battle.types import BattleUnit
from ..profiles import BaseAIProfile
from ..threat import calculate_threat_value

if TYPE_CHECKING:
    from ..core import BattleAI


class SkirmisherProfile(BaseAIProfile):
    """Skirmisher AI: Flank enemies, target low HP."""
    
    def __init__(self):
        super().__init__("skirmisher")
    
    def choose_target(self, unit: BattleUnit, targets: List[BattleUnit], ai: "BattleAI") -> Optional[BattleUnit]:
        """Skirmishers prioritize marked targets, then low HP targets."""
        if not targets:
            return None
        
        # Prioritize marked targets
        marked = [t for t in targets if has_status(t.statuses, "marked")]
        if marked:
            return min(marked, key=lambda t: t.hp)
        
        # Otherwise, finish off low HP targets
        return min(targets, key=lambda t: t.hp)
    
    def execute_turn(self, unit: BattleUnit, ai: "BattleAI", hp_ratio: float) -> None:
        """Execute skirmisher turn: flank and attack."""
        scene = ai.scene
        weapon_range = scene.combat._get_weapon_range(unit)
        is_melee = weapon_range == 1
        
        # Find targets
        enemies_in_range = ai.enemies_in_range(unit, weapon_range, use_chebyshev=is_melee)
        
        # Try to flank if not already flanking
        target = ai.nearest_target(unit, "player")
        if target and not scene.combat.is_flanking(unit, target):
            # Try to find a flanking position
            flank_pos = ai.positioning.find_flanking_position(unit, target)
            if flank_pos:
                fx, fy = flank_pos
                dx = fx - unit.gx
                dy = fy - unit.gy
                # Normalize to single step
                if abs(dx) > 0:
                    dx = 1 if dx > 0 else -1
                if abs(dy) > 0:
                    dy = 1 if dy > 0 else -1
                if scene._try_move_unit(unit, dx, dy):
                    scene._log(f"{unit.name} maneuvers for a flank.")
                    scene._next_turn()
                    return
        
        # Use offensive skills
        if enemies_in_range:
            # Try crippling blow on low HP targets
            crippling_blow = unit.skills.get("crippling_blow")
            if crippling_blow:
                cd = unit.cooldowns.get(crippling_blow.id, 0)
                can_use, _ = unit.has_resources_for_skill(crippling_blow, scene.combat)
                if cd == 0 and can_use:
                    low_hp_targets = [t for t in enemies_in_range if t.hp < t.max_hp * 0.5]
                    if low_hp_targets and random.random() < 0.6:
                        target = min(low_hp_targets, key=lambda t: t.hp)
                        if scene._use_skill_targeted(unit, crippling_blow, target, for_ai=True):
                            return
            
            # Basic attack
            target = self.choose_target(unit, enemies_in_range, ai)
            if target:
                ai.perform_basic_attack(unit, target=target)
                return
        
        # Move towards target
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
