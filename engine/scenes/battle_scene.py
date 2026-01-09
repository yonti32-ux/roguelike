"""
Backward compatibility wrapper for BattleScene.

BattleScene has been moved to engine.battle.scene.
This file maintains backward compatibility for existing imports.
"""

from engine.battle import BattleScene

__all__ = ["BattleScene"]
