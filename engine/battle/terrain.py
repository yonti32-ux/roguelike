"""
Battle terrain management module.

Handles terrain generation and retrieval for the battle grid.
Extracted from battle_scene.py for better code organization.
"""

from typing import Dict
import random

from settings import (
    BATTLE_GRID_WIDTH,
    BATTLE_ENEMY_START_COL_OFFSET,
    TERRAIN_SPAWN_CHANCE,
)
from engine.battle.types import BattleTerrain


class BattleTerrainManager:
    """
    Handles terrain generation and management for the battle scene.
    
    Takes a reference to the BattleScene to access and modify terrain data.
    """
    
    def __init__(self, scene):
        """
        Initialize the terrain manager with a reference to the battle scene.
        
        Args:
            scene: The BattleScene instance
        """
        self.scene = scene
    
    def generate_terrain(self) -> None:
        """
        Generate terrain on the battle grid.
        Avoids spawning terrain on starting positions.
        """
        # Reserve starting positions (no terrain there)
        reserved_positions: set[tuple[int, int]] = set()
        
        # Player starting area (left side, columns 0-2)
        for gx in range(3):
            for gy in range(self.scene.grid_height):
                reserved_positions.add((gx, gy))
        
        # Enemy starting area (right side)
        enemy_start_col = self.scene.grid_width - BATTLE_ENEMY_START_COL_OFFSET
        for gx in range(enemy_start_col, self.scene.grid_width):
            for gy in range(self.scene.grid_height):
                reserved_positions.add((gx, gy))
        
        # Middle area (no-man's-land) - more likely to have terrain
        middle_start = self.scene.grid_width // 3
        middle_end = self.scene.grid_width - self.scene.grid_width // 3
        
        for gx in range(self.scene.grid_width):
            for gy in range(self.scene.grid_height):
                pos = (gx, gy)
                if pos in reserved_positions:
                    continue
                
                # Higher chance in middle area
                if middle_start <= gx < middle_end:
                    chance = TERRAIN_SPAWN_CHANCE * 1.5
                else:
                    chance = TERRAIN_SPAWN_CHANCE
                
                if random.random() < chance:
                    # Choose terrain type
                    rand = random.random()
                    if rand < 0.6:
                        # Cover (most common - 60%)
                        self.scene.terrain[pos] = BattleTerrain(terrain_type="cover")
                    elif rand < 0.9:
                        # Obstacle (30%)
                        self.scene.terrain[pos] = BattleTerrain(terrain_type="obstacle")
                    else:
                        # Hazard (10% - reduced from 30%)
                        self.scene.terrain[pos] = BattleTerrain(terrain_type="hazard")
    
    def get_terrain(self, gx: int, gy: int) -> BattleTerrain:
        """Get terrain at grid position, returns empty terrain if none."""
        return self.scene.terrain.get((gx, gy), BattleTerrain(terrain_type="none"))

