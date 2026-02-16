# Mode Handlers

Mode handlers encapsulate the main-loop logic for each game mode (overworld, exploration, battle). The `Game` class delegates `update()`, `draw()`, and `handle_event()` to the active handler.

## Structure

```
mode_handlers/
├── __init__.py      # Exports all handlers
├── base.py          # BaseModeHandler (abstract interface)
├── overworld.py     # OverworldModeHandler
├── exploration.py  # ExplorationModeHandler
└── battle.py       # BattleModeHandler
```

## Flow

1. **Game.update(dt)** – Updates tooltip, then calls `handler.update(dt)`.
2. **Game.handle_event(event)** – Global handlers first (pause, cheats, save/load, confirmation, debug console), then `handler.handle_event(event)`.
3. **Game.draw()** – Calls `handler.draw()`, then draws overlays (inventory, skill screen, etc.), debug console, confirmation dialog, and flips the display.

## Adding a New Mode

1. Create a new handler class in a new file, extending `BaseModeHandler`.
2. Implement `update(dt)` and `draw()`.
3. Override `handle_event(event)` if the mode needs input.
4. Register the handler in `Game.__init__` and add the mode to `GameMode`.
