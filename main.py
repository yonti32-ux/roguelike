import sys
import pygame

from settings import WINDOW_WIDTH, WINDOW_HEIGHT, TITLE, FPS
from engine.game import Game
from engine.character_creation import CharacterCreationScene


def main() -> None:
    pygame.init()
    pygame.display.set_caption(TITLE)

    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()

    # --- Character creation: choose class + name ---
    creation_scene = CharacterCreationScene(screen)
    result = creation_scene.run()

    if result is None:
        # Player quit during character creation
        pygame.quit()
        sys.exit()

    selected_class_id, hero_name = result

    # Start game with the chosen class
    game = Game(screen, hero_class_id=selected_class_id)

    # Store the chosen name on hero_stats
    game.hero_stats.hero_name = hero_name

    # Sync stats + name into the Player entity
    if game.player is not None:
        game.apply_hero_stats_to_player(full_heal=True)

    # --- Main loop ---
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        # Reset per-frame input state before processing events.
        if hasattr(game, "input_manager") and game.input_manager is not None:
            game.input_manager.begin_frame()

        for event in pygame.event.get():
            # Let the InputManager observe every event first so it can
            # maintain key state. It ignores non-key events.
            if hasattr(game, "input_manager") and game.input_manager is not None:
                game.input_manager.process_event(event)

            if event.type == pygame.QUIT:
                running = False
                continue

            game.handle_event(event)

        game.update(dt)
        game.draw()
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
