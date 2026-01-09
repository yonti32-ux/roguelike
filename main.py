import sys
import pygame

from settings import WINDOW_WIDTH, WINDOW_HEIGHT, TITLE, FPS
from engine.core.game import Game
from engine.scenes.character_creation import CharacterCreationScene
from engine.scenes.main_menu import MainMenuScene
from engine.scenes.save_menu import SaveMenuScene
from engine.utils.save_system import load_game

TELEMETRY_ENABLED = False  # flip to True when needed

if TELEMETRY_ENABLED:
    from pathlib import Path
    from telemetry.logger import telemetry
else:
    class _NullTelemetry:
        enabled = False
        def init(self, *_args, **_kwargs): pass
        def log(self, *_args, **_kwargs): pass
        def tick_frame(self): return 0
        def should_log_frame(self): return False

    telemetry = _NullTelemetry()


def _game_snapshot(game: Game) -> dict:
    """
    Create a lightweight snapshot of game state for telemetry/logging.
    Keep it defensive: never assume fields exist.
    """
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

    # Load resolution settings
    from engine.core.config import load_config
    config = load_config()
    width, height = config.get_resolution()
    
    # Create screen with configured resolution
    screen = pygame.display.set_mode((width, height))
    clock = pygame.time.Clock()

    # Init telemetry file (relative to repo root next to main.py)
    if TELEMETRY_ENABLED:
        from pathlib import Path
        telemetry_path = Path(__file__).resolve().parent / "telemetry" / "telemetry.jsonl"
        telemetry.init(telemetry_path)

    # --- Main Menu ---
    main_menu = MainMenuScene(screen)
    menu_choice = main_menu.run()

    if menu_choice is None:
        telemetry.log("quit_from_main_menu")
        pygame.quit()
        sys.exit()

    # Handle menu choice
    if menu_choice == "quit":
        telemetry.log("quit_from_main_menu")
        pygame.quit()
        sys.exit()
    
    elif menu_choice == "options":
        # Show options menu (resolution settings)
        from engine.scenes.pause_menu import OptionsMenuScene
        from engine.scenes.resolution_menu import ResolutionMenuScene
        options_menu = OptionsMenuScene(screen)
        sub_choice = options_menu.run()
        
        if sub_choice == "resolution":
            res_menu = ResolutionMenuScene(screen)
            result = res_menu.run()
            if result is not None:
                # Resolution changed, need to restart to apply
                print("Resolution changed. Please restart the game to apply the new resolution.")
                # Recreate screen with new resolution
                width, height, match_desktop = result
                screen = pygame.display.set_mode((width, height))
                # Go back to main menu so user can continue or restart
                main_menu = MainMenuScene(screen)
                menu_choice = main_menu.run()
                if menu_choice is None or menu_choice == "quit":
                    pygame.quit()
                    sys.exit()
                # Continue with the new menu choice (fall through)
        else:
            # User cancelled options, go back to main menu
            main_menu = MainMenuScene(screen)
            menu_choice = main_menu.run()
            if menu_choice is None or menu_choice == "quit":
                pygame.quit()
                sys.exit()
            # Continue with the new menu choice (fall through)
    
    if menu_choice == "load_game":
        # Show save selection menu
        save_menu = SaveMenuScene(screen, mode="load")
        selected_slot = save_menu.run()
        
        if selected_slot is None:
            # User cancelled, go back to main menu
            pygame.quit()
            sys.exit()
        
        # Load the selected save
        game = load_game(screen, slot=selected_slot)
        
        if game is None:
            # Failed to load, show error and exit
            print(f"Failed to load save slot {selected_slot}")
            pygame.quit()
            sys.exit()
        
        telemetry.log("game_loaded", slot=selected_slot, **_game_snapshot(game))
    
    if menu_choice == "new_game":
        # --- Character creation: choose class + name ---
        creation_scene = CharacterCreationScene(screen)
        result = creation_scene.run()

        if result is None:
            telemetry.log("quit_during_character_creation")
            pygame.quit()
            sys.exit()

        selected_class_id, hero_name = result
        telemetry.log("character_created", hero_class_id=selected_class_id, hero_name=hero_name)

        # --- Overworld Configuration: customize world settings ---
        from engine.scenes.overworld_config_scene import OverworldConfigScene
        config_scene = OverworldConfigScene(screen)
        overworld_config = config_scene.run()
        
        if overworld_config is None:
            # User cancelled config, exit
            telemetry.log("quit_during_overworld_config")
            pygame.quit()
            sys.exit()
        
        telemetry.log("overworld_configured", 
                     world_size=f"{overworld_config.world_width}x{overworld_config.world_height}",
                     poi_density=overworld_config.poi_density,
                     seed=overworld_config.seed)

        # Start game with the chosen class and overworld config
        game = Game(screen, hero_class_id=selected_class_id, overworld_config=overworld_config)

        # Store the chosen name on hero_stats
        game.hero_stats.hero_name = hero_name

        # Sync stats + name into the Player entity
        if game.player is not None:
            game.apply_hero_stats_to_player(full_heal=True)

        telemetry.log("game_start", **_game_snapshot(game))
    else:
        # Should not reach here, but handle gracefully
        pygame.quit()
        sys.exit()

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
            
            # Check for return to main menu request
            if hasattr(game, "_return_to_main_menu") and game._return_to_main_menu:
                # Return to main menu
                main_menu = MainMenuScene(screen)
                menu_choice = main_menu.run()
                
                if menu_choice is None or menu_choice == "quit":
                    running = False
                    continue
                
                # Handle menu choice (similar to initial menu handling)
                if menu_choice == "load_game":
                    save_menu = SaveMenuScene(screen, mode="load")
                    selected_slot = save_menu.run()
                    if selected_slot is None:
                        running = False
                        continue
                    game = load_game(screen, slot=selected_slot)
                    if game is None:
                        print(f"Failed to load save slot {selected_slot}")
                        running = False
                        continue
                    telemetry.log("game_loaded", slot=selected_slot, **_game_snapshot(game))
                elif menu_choice == "new_game":
                    creation_scene = CharacterCreationScene(screen)
                    result = creation_scene.run()
                    if result is None:
                        running = False
                        continue
                    selected_class_id, hero_name = result
                    game = Game(screen, hero_class_id=selected_class_id)
                    game.hero_stats.hero_name = hero_name
                    if game.player is not None:
                        game.apply_hero_stats_to_player(full_heal=True)
                    telemetry.log("game_start", **_game_snapshot(game))
                
                game._return_to_main_menu = False
                continue
            
            # Check for quit game request
            if hasattr(game, "_quit_game") and game._quit_game:
                running = False
                continue

        # Check for in-game reload request
        if hasattr(game, "_reload_slot") and game._reload_slot is not None:
            reload_slot = game._reload_slot
            game._reload_slot = None  # Clear flag
            
            # Load the new game (use the imported function from top of file)
            loaded_game = load_game(screen, slot=reload_slot)
            if loaded_game is not None:
                game = loaded_game
                telemetry.log("game_reloaded_in_game", slot=reload_slot, **_game_snapshot(game))
            else:
                # Failed to load, show error message
                if hasattr(game, "add_message"):
                    game.add_message("Failed to load game.")
                print(f"Failed to load save slot {reload_slot}")

        # Pass clock to game for debug console
        if hasattr(game, 'debug_console'):
            game._debug_clock = clock
        
        try:
            game.update(dt)
            game.draw()
        except Exception as e:
            telemetry.log("exception", where="main_loop", error=repr(e), frame=frame, **_game_snapshot(game))
            # Log to debug console if available
            if hasattr(game, 'debug_console') and game.debug_console:
                game.debug_console.log_error(e, "main_loop")
            raise

        pygame.display.flip()

    telemetry.log("game_exit")
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
