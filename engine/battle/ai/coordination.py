"""
Coordination system for enemy AI.

Enables enemies to work together: focus fire, protect allies, combo skills.
"""

from typing import List, Optional, Dict
from engine.battle.types import BattleUnit
from .threat import calculate_threat_value


class CoordinationManager:
    """
    Manages coordination between enemy units.
    
    Tracks:
    - Which enemies are targeting which players
    - Focus fire opportunities
    - Protection needs
    - Combo setup opportunities
    """
    
    def __init__(self, scene):
        self.scene = scene
        self.target_assignments: Dict[BattleUnit, BattleUnit] = {}  # enemy -> target
        self.focus_targets: Dict[BattleUnit, int] = {}  # target -> number of enemies targeting
    
    def update_target_assignment(self, unit: BattleUnit, target: BattleUnit) -> None:
        """Update the target assignment for a unit."""
        # Remove old assignment
        old_target = self.target_assignments.get(unit)
        if old_target:
            self.focus_targets[old_target] = self.focus_targets.get(old_target, 1) - 1
            if self.focus_targets[old_target] <= 0:
                del self.focus_targets[old_target]
        
        # Add new assignment
        self.target_assignments[unit] = target
        self.focus_targets[target] = self.focus_targets.get(target, 0) + 1
    
    def should_focus_fire(self, target: BattleUnit, min_focusers: int = 2) -> bool:
        """
        Check if multiple enemies should focus fire on a target.
        
        Args:
            target: The potential focus target
            min_focusers: Minimum number of enemies already targeting
            
        Returns:
            True if this target should be focused
        """
        current_focusers = self.focus_targets.get(target, 0)
        return current_focusers >= min_focusers
    
    def get_focus_target(self, enemies: List[BattleUnit]) -> Optional[BattleUnit]:
        """
        Get the best target for focus fire.
        
        Prioritizes:
        1. Targets already being focused (2+ enemies)
        2. High-threat targets
        3. Low HP targets (finish them off)
        
        Args:
            enemies: List of enemy units to coordinate
            
        Returns:
            Best focus target or None
        """
        player_units = [u for u in self.scene.player_units if u.is_alive]
        if not player_units:
            return None
        
        # Find targets already being focused
        focused_targets = [
            t for t, count in self.focus_targets.items()
            if count >= 2 and t.is_alive
        ]
        
        if focused_targets:
            # Prioritize focused targets by threat
            return max(focused_targets, key=calculate_threat_value)
        
        # Otherwise, find high-threat or low-HP targets
        # Sort by threat value (highest first)
        sorted_targets = sorted(player_units, key=calculate_threat_value, reverse=True)
        
        # Prefer high-threat targets that are also low HP (finish them)
        for target in sorted_targets:
            if target.hp < target.max_hp * 0.4:  # Below 40% HP
                return target
        
        # Return highest threat target
        return sorted_targets[0] if sorted_targets else None
    
    def should_protect_ally(self, ally: BattleUnit, enemies_nearby: List[BattleUnit]) -> bool:
        """
        Check if an ally needs protection.
        
        Args:
            ally: The ally to check
            enemies_nearby: List of enemies near the ally
            
        Returns:
            True if ally needs protection
        """
        # Protect low-HP allies
        if ally.hp < ally.max_hp * 0.3:
            return True
        
        # Protect casters/support from melee enemies
        profile = getattr(ally, "ai_profile", "brute")
        if profile in ("caster", "support") and enemies_nearby:
            return True
        
        return False
    
    def clear_assignments(self):
        """Clear all target assignments (call at start of battle or turn)."""
        self.target_assignments.clear()
        self.focus_targets.clear()


def should_focus_fire(target: BattleUnit, coordination: CoordinationManager, min_focusers: int = 2) -> bool:
    """
    Convenience function to check if a target should be focused.
    
    Args:
        target: The target to check
        coordination: Coordination manager
        min_focusers: Minimum number of focusers
        
    Returns:
        True if should focus fire
    """
    return coordination.should_focus_fire(target, min_focusers)
