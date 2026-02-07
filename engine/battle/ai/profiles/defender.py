"""
Defender AI Profile.

Protective fighters that bodyblock for allies and use defensive skills proactively.
"""

from typing import List, Optional, TYPE_CHECKING
import random

from systems.statuses import has_status
from engine.battle.types import BattleUnit
from ..profiles import BaseAIProfile
from ..threat import calculate_threat_value

if TYPE_CHECKING:
    from ..core import BattleAI


class DefenderProfile(BaseAIProfile):
    """Defender AI: Protects allies, bodyblocks, uses defensive skills."""
    
    def __init__(self):
        super().__init__("defender")
    
    def choose_target(self, unit: BattleUnit, targets: List[BattleUnit], ai: "BattleAI") -> Optional[BattleUnit]:
        """Defenders prioritize enemies threatening allies."""
        if not targets:
            return None
        
        # Find allies that need protection
        allies = ai.allies_in_range(unit, 3, use_chebyshev=True)
        threatened_allies = []
        for ally in allies:
            enemies_near_ally = ai.enemies_in_range(ally, 1, use_chebyshev=True)
            if enemies_near_ally:
                threatened_allies.append(ally)
        
        # If allies are threatened, target the enemies threatening them
        if threatened_allies:
            for ally in threatened_allies:
                enemies_near_ally = ai.enemies_in_range(ally, 1, use_chebyshev=True)
                for enemy in enemies_near_ally:
                    if enemy in targets:
                        return enemy
        
        # Otherwise, target highest threat
        return max(targets, key=calculate_threat_value)
    
    def execute_turn(self, unit: BattleUnit, ai: "BattleAI", hp_ratio: float) -> None:
        """Execute defender turn: protect allies, then attack."""
        scene = ai.scene
        weapon_range = scene.combat._get_weapon_range(unit)
        
        # Find allies that need protection
        allies = ai.allies_in_range(unit, 3, use_chebyshev=True)
        threatened_allies = []
        for ally in allies:
            enemies_near_ally = ai.enemies_in_range(ally, 1, use_chebyshev=True)
            if enemies_near_ally:
                threatened_allies.append(ally)
        
        # Move to protect threatened allies
        if threatened_allies:
            # Find the most threatened ally
            most_threatened = min(threatened_allies, key=lambda a: a.hp / float(a.max_hp))
            enemies_near = ai.enemies_in_range(most_threatened, 1, use_chebyshev=True)
            
            if enemies_near:
                # Try to position between ally and enemy
                enemy = enemies_near[0]
                # Find position adjacent to ally, closer to enemy
                protect_positions = [
                    (most_threatened.gx + 1, most_threatened.gy),
                    (most_threatened.gx - 1, most_threatened.gy),
                    (most_threatened.gx, most_threatened.gy + 1),
                    (most_threatened.gx, most_threatened.gy - 1),
                ]
                
                # Choose position closest to enemy
                best_pos = None
                best_dist = float('inf')
                for px, py in protect_positions:
                    if not scene._cell_blocked(px, py):
                        dist = abs(enemy.gx - px) + abs(enemy.gy - py)
                        if dist < best_dist:
                            best_dist = dist
                            best_pos = (px, py)
                
                if best_pos:
                    px, py = best_pos
                    dx = px - unit.gx
                    dy = py - unit.gy
                    if abs(dx) > 0:
                        dx = 1 if dx > 0 else -1
                    if abs(dy) > 0:
                        dy = 1 if dy > 0 else -1
                    if scene._try_move_unit(unit, dx, dy):
                        scene._log(f"{unit.name} moves to protect {most_threatened.name}!")
                        scene._next_turn()
                        return
        
        # Use defensive skills proactively
        guard_skill = unit.skills.get("guard")
        if guard_skill and hp_ratio < 0.7:
            cd = unit.cooldowns.get(guard_skill.id, 0)
            can_use, _ = unit.has_resources_for_skill(guard_skill, scene.combat)
            if cd == 0 and can_use and random.random() < 0.6:
                if scene._use_skill(unit, guard_skill, for_ai=True):
                    return
        
        # Attack enemies threatening allies
        enemies_in_range = ai.enemies_in_range(unit, weapon_range, use_chebyshev=(weapon_range == 1))
        if enemies_in_range:
            target = self.choose_target(unit, enemies_in_range, ai)
            if target:
                ai.perform_basic_attack(unit, target=target)
                return
        
        # Move towards nearest threat
        target = ai.nearest_target(unit, "player")
        if target:
            moved = ai.move_towards_target(unit, target)
            if moved:
                scene._log(f"{unit.name} advances defensively.")
            else:
                scene._log(f"{unit.name} holds position.")
        else:
            scene.status = "victory"
            scene._log("The foes scatter.")
        
        scene._next_turn()
