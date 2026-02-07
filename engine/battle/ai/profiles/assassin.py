"""
Assassin AI Profile.

Targets isolated or low-HP enemies, uses stealth/teleport if available.
"""

from typing import List, Optional, TYPE_CHECKING
import random

from systems.statuses import has_status
from engine.battle.types import BattleUnit
from ..profiles import BaseAIProfile
from ..threat import calculate_threat_value

if TYPE_CHECKING:
    from ..core import BattleAI


class AssassinProfile(BaseAIProfile):
    """Assassin AI: Targets isolated/low HP enemies."""
    
    def __init__(self):
        super().__init__("assassin")
    
    def choose_target(self, unit: BattleUnit, targets: List[BattleUnit], ai: "BattleAI") -> Optional[BattleUnit]:
        """Assassins prioritize isolated or low-HP targets."""
        if not targets:
            return None
        
        # Find isolated targets (no nearby allies)
        isolated = []
        for target in targets:
            nearby_allies = ai.allies_in_range(target, 1, use_chebyshev=True)
            if len(nearby_allies) <= 1:  # Only the target itself or one ally
                isolated.append(target)
        
        if isolated:
            # Among isolated, prefer low HP
            return min(isolated, key=lambda t: t.hp)
        
        # Otherwise, just low HP
        return min(targets, key=lambda t: t.hp)
    
    def execute_turn(self, unit: BattleUnit, ai: "BattleAI", hp_ratio: float) -> None:
        """Execute assassin turn: target isolated/low HP enemies."""
        scene = ai.scene
        weapon_range = scene.combat._get_weapon_range(unit)
        is_melee = weapon_range == 1
        
        # Try to use teleport/stealth skills if available
        # (These would need to be implemented in skills system)
        # For now, we'll focus on positioning and targeting
        
        # Find targets
        enemies_in_range = ai.enemies_in_range(unit, weapon_range, use_chebyshev=is_melee)
        
        # Use high-damage skills on low HP targets
        if enemies_in_range:
            # Crippling blow on low HP targets
            crippling_blow = unit.skills.get("crippling_blow")
            if crippling_blow:
                cd = unit.cooldowns.get(crippling_blow.id, 0)
                can_use, _ = unit.has_resources_for_skill(crippling_blow, scene.combat)
                if cd == 0 and can_use:
                    low_hp = [t for t in enemies_in_range if t.hp < t.max_hp * 0.4]
                    if low_hp:
                        target = min(low_hp, key=lambda t: t.hp)
                        if scene._use_skill_targeted(unit, crippling_blow, target, for_ai=True):
                            return
            
            # Poison strike on isolated targets
            poison_strike = unit.skills.get("poison_strike")
            if poison_strike:
                cd = unit.cooldowns.get(poison_strike.id, 0)
                can_use, _ = unit.has_resources_for_skill(poison_strike, scene.combat)
                if cd == 0 and can_use:
                    isolated = []
                    for target in enemies_in_range:
                        nearby_allies = ai.allies_in_range(target, 1, use_chebyshev=True)
                        if len(nearby_allies) <= 1:
                            isolated.append(target)
                    if isolated and random.random() < 0.7:
                        target = min(isolated, key=lambda t: t.hp)
                        if scene._use_skill_targeted(unit, poison_strike, target, for_ai=True):
                            return
            
            # Basic attack on best target
            target = self.choose_target(unit, enemies_in_range, ai)
            if target:
                ai.perform_basic_attack(unit, target=target)
                return
        
        # Try to flank isolated targets
        target = ai.nearest_target(unit, "player")
        if target:
            # Check if target is isolated
            nearby_allies = ai.allies_in_range(target, 1, use_chebyshev=True)
            is_isolated = len(nearby_allies) <= 1
            
            # Try to flank if not already flanking
            if is_isolated and not scene.combat.is_flanking(unit, target):
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
                        scene._log(f"{unit.name} strikes from the shadows!")
                        scene._next_turn()
                        return
            
            # Move towards target
            moved = ai.move_towards_target(unit, target)
            if moved:
                scene._log(f"{unit.name} stalks forward.")
            else:
                scene._log(f"{unit.name} waits for an opening.")
        else:
            scene.status = "victory"
            scene._log("The foes scatter.")
        
        scene._next_turn()
