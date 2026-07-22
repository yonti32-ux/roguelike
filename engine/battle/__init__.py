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

During refactoring, this module will gradually be populated.
For now, BattleScene is still in engine/battle_scene.py.
"""

# TODO: After refactoring, uncomment this:
# from .scene import BattleScene
# __all__ = ["BattleScene"]

__all__ = []

