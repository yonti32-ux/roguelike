"""
Battle pathfinding module.

Handles A* pathfinding and reachable cell calculations for battle movement.
Extracted from battle_scene.py for better code organization.

Supports 8-directional movement with diagonal movement costing more.
"""

from typing import List, Dict, Optional
import math
from engine.battle.types import BattleUnit


class BattlePathfinding:
    """
    Handles pathfinding for the battle scene.
    
    Takes a reference to the BattleScene to access terrain and unit information.
    """
    
    def __init__(self, scene):
        """
        Initialize the pathfinding with a reference to the battle scene.
        
        Args:
            scene: The BattleScene instance
        """
        self.scene = scene
    
    def find_path(self, unit: BattleUnit, target_gx: int, target_gy: int) -> Optional[List[tuple[int, int]]]:
        """
        Find a path from unit's current position to target using A* pathfinding.
        Returns the path as a list of (gx, gy) tuples, or None if no path exists.
        Respects movement points and terrain costs.
        """
        start = (unit.gx, unit.gy)
        goal = (target_gx, target_gy)
        
        if start == goal:
            return [start]
        
        if self._cell_blocked(target_gx, target_gy):
            return None
        
        # A* pathfinding
        open_set: List[tuple[int, int]] = [start]
        came_from: Dict[tuple[int, int], Optional[tuple[int, int]]] = {start: None}
        g_score: Dict[tuple[int, int], float] = {start: 0}
        
        def heuristic(pos: tuple[int, int]) -> float:
            # Use Chebyshev distance for 8-directional movement
            dx = abs(pos[0] - goal[0])
            dy = abs(pos[1] - goal[1])
            return max(dx, dy)
        
        f_score: Dict[tuple[int, int], float] = {start: heuristic(start)}
        
        while open_set:
            # Get node with lowest f_score
            current = min(open_set, key=lambda p: f_score.get(p, float('inf')))
            
            if current == goal:
                # Reconstruct path
                path = []
                while current is not None:
                    path.append(current)
                    current = came_from.get(current)
                path.reverse()
                return path
            
            open_set.remove(current)
            
            # Check neighbors (8-directional: 4 orthogonal + 4 diagonal)
            for dx, dy in [
                (0, 1), (0, -1), (1, 0), (-1, 0),  # Orthogonal
                (1, 1), (1, -1), (-1, 1), (-1, -1)  # Diagonal
            ]:
                neighbor = (current[0] + dx, current[1] + dy)
                
                if self._cell_blocked(neighbor[0], neighbor[1]):
                    continue
                
                # Calculate movement cost (diagonal costs more)
                move_cost = self._get_movement_cost(neighbor[0], neighbor[1], dx, dy)
                tentative_g = g_score.get(current, float('inf')) + move_cost
                
                # Check if we have enough movement points
                if tentative_g > unit.current_movement_points:
                    continue
                
                if tentative_g < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + heuristic(neighbor)
                    if neighbor not in open_set:
                        open_set.append(neighbor)
        
        return None  # No path found
    
    def get_reachable_cells(self, unit: BattleUnit) -> Dict[tuple[int, int], int]:
        """
        Get all cells reachable with current movement points.
        Returns dict mapping (gx, gy) -> movement cost.
        Uses BFS to find all reachable cells.
        """
        reachable: Dict[tuple[int, int], int] = {}
        queue: List[tuple[tuple[int, int], int]] = [((unit.gx, unit.gy), 0)]  # (position, cost)
        visited: set[tuple[int, int]] = set()
        
        while queue:
            pos, cost = queue.pop(0)
            if pos in visited:
                continue
            visited.add(pos)
            
            if cost <= unit.current_movement_points:
                reachable[pos] = cost
            
            # Check neighbors (8-directional)
            for dx, dy in [
                (0, 1), (0, -1), (1, 0), (-1, 0),  # Orthogonal
                (1, 1), (1, -1), (-1, 1), (-1, -1)  # Diagonal
            ]:
                neighbor = (pos[0] + dx, pos[1] + dy)
                
                if neighbor in visited:
                    continue
                
                if self._cell_blocked(neighbor[0], neighbor[1]):
                    continue
                
                move_cost = self._get_movement_cost(neighbor[0], neighbor[1], dx, dy)
                new_cost = cost + move_cost
                
                if new_cost <= unit.current_movement_points:
                    queue.append((neighbor, new_cost))
        
        return reachable
    
    def _cell_blocked(self, gx: int, gy: int) -> bool:
        """Check if a cell is blocked by terrain or units."""
        if gx < 0 or gy < 0 or gx >= self.scene.grid_width or gy >= self.scene.grid_height:
            return True
        # Check for obstacles
        terrain = self.scene.terrain_manager.get_terrain(gx, gy)
        if terrain.blocks_movement:
            return True
        # Check for units
        for u in self.scene._all_units():
            if not u.is_alive:
                continue
            if u.gx == gx and u.gy == gy:
                return True
        return False
    
    def _get_movement_cost(self, gx: int, gy: int, dx: int = 0, dy: int = 0) -> float:
        """
        Get the movement cost to enter a cell.
        Normal cells cost 1, hazards cost extra.
        Diagonal movement costs more (1.5x base cost).
        
        Args:
            gx, gy: Grid coordinates of the destination cell
            dx, dy: Direction vector (0/±1 for orthogonal, both ±1 for diagonal)
        """
        from settings import HAZARD_MOVEMENT_COST, DIAGONAL_MOVEMENT_COST
        terrain = self.scene.terrain_manager.get_terrain(gx, gy)
        
        # Base cost: 1 for normal, HAZARD_MOVEMENT_COST for hazards
        base_cost = HAZARD_MOVEMENT_COST if terrain.terrain_type == "hazard" else 1.0
        
        # Apply diagonal multiplier if moving diagonally
        is_diagonal = abs(dx) == 1 and abs(dy) == 1
        if is_diagonal:
            base_cost *= DIAGONAL_MOVEMENT_COST
        
        return base_cost

