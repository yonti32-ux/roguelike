# Perk Selection Scene Refactoring Plan

## Current State Analysis

### Problems Identified:
1. **Mixed Architecture**: Perk selection is currently a hybrid between a "mode" and an "overlay screen"
   - Uses `GameMode.PERK_CHOICE` mode
   - But implemented as `PerkChoiceScreen` overlay
   - Game class holds perk-specific state (`pending_perk_choices`, `perk_choice_queue`, etc.)

2. **Scattered State**: Perk-related state is spread across:
   - `Game` class: `pending_perk_choices`, `perk_choice_queue`, `perk_choice_owner`, `perk_choice_companion_index`
   - `PerkChoiceScreen`: Queue management logic
   - `ui/hud.py`: Drawing logic (`draw_perk_choice_overlay`)

3. **Not Self-Contained**: Unlike `BattleScene` or `CharacterCreationScene`, perk selection:
   - Doesn't have its own scene class with full control
   - Relies on Game's main loop for updates
   - Mixes overlay drawing with background exploration view

4. **Queue Management in Wrong Place**: Queue logic is in `PerkChoiceScreen` but should be scene-level

## Proposed Solution

### Create `PerkSelectionScene` Class
Similar to `BattleScene`, create a dedicated scene class that:
- Manages its own state (queue, current selection, etc.)
- Has full control over input/rendering
- Can be called from Game when perk choices are needed
- Is self-contained and reusable

### Architecture Changes

#### 1. New File: `engine/perk_selection_scene.py`
```python
class PerkSelectionScene:
    """
    Full-screen scene for selecting perks on level-up.
    
    Manages:
    - Queue of entities (hero + companions) needing perk selection
    - Current perk choices display
    - Input handling (selection, navigation, cancel)
    - Complete rendering (no overlay, full scene)
    """
    
    def __init__(self, game: Game):
        # Internal state
        self.queue: List[PerkChoiceEntry] = []
        self.current_entry: Optional[PerkChoiceEntry] = None
        self.current_choices: List[Perk] = []
        self.selected_index: int = 0
        
    def enqueue(self, owner: str, companion_index: Optional[int])
    def run(self) -> None:  # Main loop, blocks until all selections done
    def handle_event(self, event: pygame.event.Event) -> None
    def update(self, dt: float) -> None
    def draw(self) -> None
```

#### 2. Clean Up Game Class
Remove from `Game`:
- `pending_perk_choices`
- `perk_choice_queue`
- `perk_choice_owner`
- `perk_choice_companion_index`
- `perk_choice_screen` (replace with scene instance)
- `GameMode.PERK_CHOICE` (scene handles its own blocking)

Add to `Game`:
- `perk_selection_scene: Optional[PerkSelectionScene]` (created on demand or kept as instance)

#### 3. Integration Pattern
Two possible approaches:

**Option A: Blocking Scene (like CharacterCreationScene)**
```python
# In Game, when perk queue is needed:
if need_perk_selections:
    scene = PerkSelectionScene(self)
    scene.enqueue(...)  # Add entries
    scene.run()  # Blocks until all selections done
    # Continue game loop
```

**Option B: Non-Blocking Scene (like BattleScene)**
```python
# In Game main loop:
if self.perk_selection_scene is not None:
    if self.perk_selection_scene.is_complete():
        self.perk_selection_scene = None
        self.enter_exploration_mode()
    else:
        self.perk_selection_scene.update(dt)
        self.perk_selection_scene.draw()
```

**Recommendation: Option A (Blocking)** - Simpler, cleaner, perk selection should pause everything.

#### 4. UI Improvements
Move all drawing into the scene:
- Remove `draw_perk_choice_overlay` from `ui/hud.py` (or keep as helper if scene uses it)
- Scene draws full screen with background
- Better visual design - tree view? Branch highlights? Stats preview?

#### 5. Better UX Features
- Show perk tree/branches visually
- Highlight prerequisites and connections
- Show stat changes preview
- Keyboard navigation (arrow keys + enter)
- Mouse support (optional, future)

## Implementation Steps

### Phase 1: Create Scene Structure
1. Create `engine/perk_selection_scene.py`
2. Define `PerkChoiceEntry` dataclass for queue entries
3. Implement basic `__init__`, `enqueue`, `run` skeleton
4. Copy queue management logic from `PerkChoiceScreen`

### Phase 2: Move State & Logic
1. Move perk queue state into scene
2. Move selection logic into scene
3. Move perk application logic (keep using systems.perks functions)
4. Test that queue processing works

### Phase 3: UI & Rendering
1. Create scene's `draw()` method
2. Move/adapt drawing from `draw_perk_choice_overlay`
3. Make it full-screen (not overlay)
4. Improve visual design

### Phase 4: Integration
1. Update `Game` class to use scene instead of screen
2. Remove old perk-related fields from `Game`
3. Update all places that call `enqueue_perk_choice` to use scene
4. Remove `GameMode.PERK_CHOICE` usage
5. Test integration

### Phase 5: Cleanup
1. Remove `PerkChoiceScreen` class from `ui/screens.py`
2. Update imports
3. Clean up `ui/hud.py` if `draw_perk_choice_overlay` is no longer needed
4. Update documentation/comments

## Benefits

1. **Cleaner Architecture**: Clear separation - scene owns perk selection, Game owns game state
2. **Self-Contained**: Scene manages its own state, no scattered fields
3. **Consistent Pattern**: Matches `BattleScene` and `CharacterCreationScene` patterns
4. **Easier to Test**: Scene can be tested independently
5. **Better UX**: Full-screen scene allows better UI design, no overlay limitations
6. **Maintainable**: All perk selection code in one place

## Files to Modify

### New Files:
- `engine/perk_selection_scene.py`

### Modified Files:
- `engine/game.py` (remove perk fields, use scene)
- `ui/screens.py` (remove PerkChoiceScreen)
- `ui/hud.py` (possibly remove draw_perk_choice_overlay)

### Unchanged (but used):
- `systems/perks.py` (still used for perk logic, no changes needed)

## Questions to Consider

1. **Scene Style**: Full-screen with background, or overlay-style (but as scene)?
   - Recommendation: Full-screen with subtle background (like battle scene)

2. **Queue Behavior**: Process all at once, or allow canceling mid-queue?
   - Recommendation: Allow cancel (ESC clears queue, returns to game)

3. **Future Enhancements**: 
   - Perk tree visualization?
   - Stat comparison/preview?
   - Perk filtering/search?
   - Save/load perk builds?

## Migration Notes

- Existing saves might have `perk_choice_queue` - handle gracefully
- Keep backward compatibility if needed (check for old fields)
- Test with multiple level-ups (queue with hero + companions)

