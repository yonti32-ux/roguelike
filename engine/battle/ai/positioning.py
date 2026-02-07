"""
Positioning and movement system for AI.

Helps AI units find optimal positions for:
- Flanking
- AoE optimization
- Maintaining range
- Formation tactics
"""

from typing import List, Optional, Tuple
from engine.battle.types import BattleUnit


class PositioningHelper:
    """
    Helps AI units find optimal positions.
    
    Considers:
    - Flanking opportunities
    - AoE positioning
    - Range maintenance
    - Formation spacing
    - Cover/terrain
    """
    
    def __init__(self, scene):
        self.scene = scene
    
    def find_flanking_position(
        self,
        unit: BattleUnit,
        target: BattleUnit,
        max_range: int = 2,
    ) -> Optional[Tuple[int, int]]:
        """
        Find a position that would flank the target.
        
        Args:
            unit: The unit seeking a flank
            target: The target to flank
            max_range: Maximum distance to search
            
        Returns:
            (gx, gy) position or None
        """
        # Check adjacent positions to target
        flank_positions = [
            (target.gx + 1, target.gy),  # Right
            (target.gx - 1, target.gy),  # Left
            (target.gx, target.gy + 1),  # Down
            (target.gx, target.gy - 1),  # Up
        ]
        
        for fx, fy in flank_positions:
            # Check if this position would be a flank
            if self.scene.combat.is_flanking(
                BattleUnit(entity=unit.entity, side=unit.side, gx=fx, gy=fy, name=unit.name),
                target
            ):
                # Check if position is valid and reachable
                if not self.scene._cell_blocked(fx, fy):
                    # Check if it's within movement range
                    dx = abs(fx - unit.gx)
                    dy = abs(fy - unit.gy)
                    if max(dx, dy) <= max_range:
                        return (fx, fy)
        
        return None
    
    def find_optimal_aoe_position(
        self,
        unit: BattleUnit,
        targets: List[BattleUnit],
        aoe_radius: int,
    ) -> Optional[Tuple[int, int]]:
        """
        Find position that maximizes AoE effectiveness.
        
        Args:
            unit: The unit casting AoE
            targets: List of potential targets
            aoe_radius: Radius of AoE effect
            
        Returns:
            (gx, gy) position or None
        """
        if not targets:
            return None
        
        # Find center of mass of targets
        avg_x = sum(t.gx for t in targets) / len(targets)
        avg_y = sum(t.gy for t in targets) / len(targets)
        
        # Find nearest valid position to center of mass
        best_pos = None
        best_score = 0
        
        # Check positions around center of mass
        for dx in range(-aoe_radius, aoe_radius + 1):
            for dy in range(-aoe_radius, aoe_radius + 1):
                gx = int(avg_x) + dx
                gy = int(avg_y) + dy
                
                # Check if position is valid
                if self.scene._cell_blocked(gx, gy):
                    continue
                
                # Count targets in AoE range
                targets_in_range = 0
                for target in targets:
                    dist = abs(target.gx - gx) + abs(target.gy - gy)
                    if dist <= aoe_radius:
                        targets_in_range += 1
                
                if targets_in_range > best_score:
                    best_score = targets_in_range
                    best_pos = (gx, gy)
        
        return best_pos
    
    def find_optimal_range_position(
        self,
        unit: BattleUnit,
        target: BattleUnit,
        preferred_range: int,
        weapon_range: int,
    ) -> Optional[Tuple[int, int]]:
        """
        Find position that maintains optimal range from target.
        
        Args:
            unit: The unit seeking position
            target: The target to maintain range from
            preferred_range: Preferred distance
            weapon_range: Maximum weapon range
            
        Returns:
            (gx, gy) position or None
        """
        current_dist = abs(target.gx - unit.gx) + abs(target.gy - unit.gy)
        
        # If already at optimal range, stay put
        if current_dist == preferred_range:
            return None
        
        # Find positions that get us closer to preferred range
        best_pos = None
        best_dist_diff = float('inf')
        
        # Check adjacent positions
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                
                gx = unit.gx + dx
                gy = unit.gy + dy
                
                if self.scene._cell_blocked(gx, gy):
                    continue
                
                new_dist = abs(target.gx - gx) + abs(target.gy - gy)
                dist_diff = abs(new_dist - preferred_range)
                
                if dist_diff < best_dist_diff and new_dist <= weapon_range:
                    best_dist_diff = dist_diff
                    best_pos = (gx, gy)
        
        return best_pos
    
    def find_formation_position(
        self,
        unit: BattleUnit,
        allies: List[BattleUnit],
        preferred_spacing: int = 2,
    ) -> Optional[Tuple[int, int]]:
        """
        Find position that maintains formation with allies.
        
        Args:
            unit: The unit seeking position
            allies: List of ally units
            preferred_spacing: Preferred spacing between units
            
        Returns:
            (gx, gy) position or None
        """
        if not allies:
            return None
        
        # Find average position of allies
        avg_x = sum(a.gx for a in allies) / len(allies)
        avg_y = sum(a.gy for a in allies) / len(allies)
        
        # Find position near average that maintains spacing
        best_pos = None
        best_score = float('inf')
        
        for dx in range(-preferred_spacing, preferred_spacing + 1):
            for dy in range(-preferred_spacing, preferred_spacing + 1):
                gx = int(avg_x) + dx
                gy = int(avg_y) + dy
                
                if self.scene._cell_blocked(gx, gy):
                    continue
                
                # Calculate spacing score (lower is better)
                total_spacing = 0
                for ally in allies:
                    dist = abs(ally.gx - gx) + abs(ally.gy - gy)
                    spacing_diff = abs(dist - preferred_spacing)
                    total_spacing += spacing_diff
                
                if total_spacing < best_score:
                    best_score = total_spacing
                    best_pos = (gx, gy)
        
        return best_pos


def find_optimal_position(
    unit: BattleUnit,
    target: BattleUnit,
    scene,
    position_type: str = "flank",
) -> Optional[Tuple[int, int]]:
    """
    Convenience function to find optimal position.
    
    Args:
        unit: The unit seeking position
        target: The target
        scene: Battle scene
        position_type: Type of position ("flank", "range", "formation")
        
    Returns:
        (gx, gy) position or None
    """
    helper = PositioningHelper(scene)
    
    if position_type == "flank":
        return helper.find_flanking_position(unit, target)
    elif position_type == "range":
        weapon_range = scene.combat._get_weapon_range(unit)
        return helper.find_optimal_range_position(unit, target, weapon_range // 2, weapon_range)
    
    return None
