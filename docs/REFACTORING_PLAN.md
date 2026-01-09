# Battle Engine Refactoring Plan

## Proposed Structure

```
engine/
  battle/
    __init__.py          # Exports BattleScene (backward compatibility)
    scene.py             # Main BattleScene class (core logic, state management)
    renderer.py          # All _draw_* methods (11 methods)
    ai.py                # Enemy AI decision-making
    pathfinding.py       # A* pathfinding algorithm
    terrain.py           # Terrain generation and management
    combat.py            # Combat calculations (damage, crits, cover, flanking)
    types.py             # BattleTerrain, BattleUnit dataclasses
```

## Migration Strategy

### Phase 1: Setup (No Breaking Changes)
1. ✅ Create `engine/battle/` folder
2. ✅ Create `engine/battle/__init__.py` with backward-compatible exports
3. Create empty module files with proper imports
4. Update `engine/battle_scene.py` to import from new modules (but keep everything in one file initially)

### Phase 2: Extract Types (Low Risk)
- Move `BattleTerrain` and `BattleUnit` to `engine/battle/types.py`
- Update imports in `battle_scene.py`

### Phase 3: Extract Renderer (Low Risk, High Impact)
- Move all `_draw_*` methods to `engine/battle/renderer.py`
- Create `BattleRenderer` class
- Update `BattleScene.draw()` to use renderer

### Phase 4: Extract Pathfinding (Low Risk)
- Move pathfinding methods to `engine/battle/pathfinding.py`
- Create `BattlePathfinding` class or module functions

### Phase 5: Extract Combat (Low Risk)
- Move combat calculation methods to `engine/battle/combat.py`
- Create `BattleCombat` class or module functions

### Phase 6: Extract Terrain (Low Risk)
- Move terrain methods to `engine/battle/terrain.py`
- Create `BattleTerrainManager` class

### Phase 7: Extract AI (Medium Risk)
- Move AI methods to `engine/battle/ai.py`
- Create `BattleAI` class

### Phase 8: Split Scene (Final Step)
- Move core `BattleScene` class to `engine/battle/scene.py`
- Keep `engine/battle_scene.py` as a thin wrapper that imports from `engine.battle.scene`
- OR: Update all imports to use `from engine.battle import BattleScene`

## Import Strategy

### Option A: Backward Compatible (Recommended)
Keep `engine/battle_scene.py` as a compatibility shim:
```python
# engine/battle_scene.py
from engine.battle import BattleScene
__all__ = ["BattleScene"]
```

### Option B: Direct Migration
Update all imports:
- `from engine.battle_scene import BattleScene` → `from engine.battle import BattleScene`

**Recommendation**: Use Option A initially, then migrate to Option B later.

## Benefits of This Structure

1. **Clear Organization**: All battle code in one place
2. **Easy Navigation**: Find battle-related code quickly
3. **Scalability**: Easy to add new battle features
4. **Testability**: Each module can be tested independently
5. **Maintainability**: Smaller, focused files are easier to understand

## File Size Targets

| File | Current | Target | Status |
|------|---------|--------|--------|
| `battle_scene.py` | 3,789 lines | ~500-800 lines | After refactoring |
| `renderer.py` | - | ~400-500 lines | New |
| `ai.py` | - | ~200-300 lines | New |
| `pathfinding.py` | - | ~100-150 lines | New |
| `combat.py` | - | ~200-300 lines | New |
| `terrain.py` | - | ~100-150 lines | New |
| `types.py` | - | ~200-300 lines | New |

## Testing Strategy

After each phase:
1. Run the game and verify behavior is identical
2. Test edge cases
3. Check for import errors
4. Verify no regressions

## Rollback Plan

If something breaks:
1. All original code is still in `engine/battle_scene.py` (until Phase 8)
2. Can revert imports easily
3. Git commits after each phase for easy rollback

