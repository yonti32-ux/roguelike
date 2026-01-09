"""
Battle engine module.

This module contains all battle-related engine code, split into logical components:
- scene.py: Main BattleScene class and core battle logic
- renderer.py: Rendering and drawing logic
- ai.py: Enemy AI decision-making
- pathfinding.py: Pathfinding algorithms
- terrain.py: Terrain generation and management
- combat.py: Combat calculations (damage, crits, cover, flanking)
- types.py: Battle dataclasses (BattleUnit, BattleTerrain)
"""

from .scene import BattleScene

__all__ = ["BattleScene"]

