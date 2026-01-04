import sys
import pygame

from settings import WINDOW_WIDTH, WINDOW_HEIGHT, TITLE, FPS
from engine.game import Game
from engine.character_creation import CharacterCreationScene

TELEMETRY_ENABLED = False  # flip to True when needed

if TELEMETRY_ENABLED:
    from pathlib import Path
    from telemetry.logger import telemetry

    def _game_snapshot(game: Game) -> dict:
        snap = {
            "mode": getattr(game, "mode", None),
            "floor": getattr(game, "floor", None),
        }
        player = getattr(game, "player", None)
        if player is not None and hasattr(player, "rect"):
            snap["player_xy"] = [player.rect.centerx, player.rect.centery]
        if player is not None and hasattr(player, "hp"):
            snap["player_hp"] = getattr(player, "hp", None)
        return snap
else:
    class _NullTelemetry:
        enabled = False
        def init(self, *_args, **_kwargs): pass
        def log(self, *_args, **_kwargs): pass
        def tick_frame(self): return 0
        def should_log_frame(self): return False

    telemetry = _NullTelemetry()




def _game_snapshot(game: Game) -> dict:
    # Keep it defensive: never assume fields exist.
    snap = {
        "mode": getattr(game, "mode", None),
        "floor": getattr(game, "floor", None),
    }
    player = getattr(game, "player", None)
    if player is not None and hasattr(player, "rect"):
        snap["player_xy"] = [player.rect.centerx, player.rect.centery]
    if player is not None and hasattr(player, "hp"):
        snap["player_hp"] = getattr(player, "hp", None)
    return snap


def main() -> None:
    pygame.init()
    pygame.display.set_caption(TITLE)

    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()

    # Init telemetry file (relative to repo root next to main.py)
    telemetry_path = Path(__file__).resolve().parent / "telemetry" / "telemetry.jsonl"
    telemetry.init(telemetry_path)

    # --- Character creation: choose class + name ---
    creation_scene = CharacterCreationScene(screen)
    result = creation_scene.run()

    if result is None:
        telemetry.log("quit_during_character_creation")
        pygame.quit()
        sys.exit()

    selected_class_id, hero_name = result
    telemetry.log("character_created", hero_class_id=selected_class_id, hero_name=hero_name)

    # Start game with the chosen class
    game = Game(screen, hero_class_id=selected_class_id)

    # Store the chosen name on hero_stats
    game.hero_stats.hero_name = hero_name

    # Sync stats + name into the Player entity
    if game.player is not None:
        game.apply_hero_stats_to_player(full_heal=True)

    telemetry.log("game_start", **_game_snapshot(game))

    # --- Main loop ---
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        frame = telemetry.tick_frame()

        # Reset per-frame input state before processing events.
        if hasattr(game, "input_manager") and game.input_manager is not None:
            game.input_manager.begin_frame()

        # Sample a lightweight frame snapshot occasionally (not every frame)
        if telemetry.should_log_frame():
            telemetry.log(
                "frame_sample",
                frame=frame,
                dt=dt,
                fps=clock.get_fps(),
                **_game_snapshot(game),
            )

        for event in pygame.event.get():
            # Let the InputManager observe every event first so it can maintain key state.
            if hasattr(game, "input_manager") and game.input_manager is not None:
                game.input_manager.process_event(event)

            # Log only “important” event types (avoid huge spam)
            if event.type == pygame.QUIT:
                telemetry.log("pygame_event", frame=frame, type="QUIT")
                running = False
                continue

            if event.type == pygame.KEYDOWN:
                telemetry.log("pygame_event", frame=frame, type="KEYDOWN", key=pygame.key.name(event.key))
            elif event.type == pygame.KEYUP:
                telemetry.log("pygame_event", frame=frame, type="KEYUP", key=pygame.key.name(event.key))

            elif event.type == pygame.MOUSEBUTTONDOWN:
                telemetry.log("pygame_event", frame=frame, type="MOUSEBUTTONDOWN", button=event.button, pos=list(event.pos))

            game.handle_event(event)

        try:
            game.update(dt)
            game.draw()
        except Exception as e:
            telemetry.log("exception", where="main_loop", error=repr(e), frame=frame, **_game_snapshot(game))
            raise

        pygame.display.flip()

    telemetry.log("game_exit")
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
