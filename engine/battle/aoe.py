"""
Area of Effect (AoE) helper module.

Provides functions to find units within an AoE area based on center point,
radius, and shape.
"""

from typing import List, Tuple, Literal
from engine.battle.types import BattleUnit


def get_units_in_aoe(
    center_gx: int,
    center_gy: int,
    radius: int,
    shape: Literal["circle", "square"],
    all_units: List[BattleUnit],
    *,
    affects_allies: bool = False,
    affects_enemies: bool = True,
    affects_self: bool = False,
    exclude_unit: BattleUnit = None,
) -> List[BattleUnit]:
    """
    Find all units within an AoE area.
    
    Args:
        center_gx: Grid X coordinate of AoE center
        center_gy: Grid Y coordinate of AoE center
        radius: Radius of AoE in tiles (0 = single target only)
        shape: Shape of AoE ("circle" or "square")
        all_units: List of all units to check
        affects_allies: Whether to include friendly units
        affects_enemies: Whether to include enemy units
        affects_self: Whether to include the caster
        exclude_unit: Unit to exclude from results (usually the caster)
    
    Returns:
        List of units within the AoE area
    """
    if radius <= 0:
        # Single target - return empty list (caller should handle primary target separately)
        return []
    
    affected_units: List[BattleUnit] = []
    
    for unit in all_units:
        if not unit.is_alive:
            continue
        
        # Exclude the specified unit (usually the caster)
        if exclude_unit is not None and unit is exclude_unit:
            if not affects_self:
                continue
        
        # Check if unit should be affected based on side
        if unit.side == "player":
            if not affects_allies:
                continue
        else:  # enemy
            if not affects_enemies:
                continue
        
        # Calculate distance based on shape
        distance = _get_distance(center_gx, center_gy, unit.gx, unit.gy, shape)
        
        if distance <= radius:
            affected_units.append(unit)
    
    return affected_units


def get_tiles_in_aoe(
    center_gx: int,
    center_gy: int,
    radius: int,
    shape: Literal["circle", "square"],
    grid_width: int,
    grid_height: int,
) -> List[Tuple[int, int]]:
    """
    Get all tile coordinates within an AoE area.
    Useful for visualization.
    
    Args:
        center_gx: Grid X coordinate of AoE center
        center_gy: Grid Y coordinate of AoE center
        radius: Radius of AoE in tiles
        shape: Shape of AoE ("circle" or "square")
        grid_width: Width of the battle grid
        grid_height: Height of the battle grid
    
    Returns:
        List of (gx, gy) tuples for tiles within the AoE
    """
    if radius <= 0:
        return [(center_gx, center_gy)]
    
    tiles: List[Tuple[int, int]] = []
    
    # Determine bounds to check
    min_gx = max(0, center_gx - radius)
    max_gx = min(grid_width - 1, center_gx + radius)
    min_gy = max(0, center_gy - radius)
    max_gy = min(grid_height - 1, center_gy + radius)
    
    for gx in range(min_gx, max_gx + 1):
        for gy in range(min_gy, max_gy + 1):
            distance = _get_distance(center_gx, center_gy, gx, gy, shape)
            if distance <= radius:
                tiles.append((gx, gy))
    
    return tiles


def _get_distance(
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    shape: Literal["circle", "square"],
) -> int:
    """
    Calculate distance between two points based on shape.
    
    For "circle": Uses Euclidean distance (rounded)
    For "square": Uses Chebyshev distance (max of dx, dy)
    
    Returns:
        Distance in tiles
    """
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    
    if shape == "circle":
        # Euclidean distance (rounded)
        import math
        return int(math.sqrt(dx * dx + dy * dy))
    else:  # square
        # Chebyshev distance (max of dx, dy)
        return max(dx, dy)

