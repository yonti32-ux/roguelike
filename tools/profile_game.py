#!/usr/bin/env python3
"""
Performance profiling script for the game.

This script provides various profiling options to identify performance bottlenecks.

Usage:
    # Profile overworld (default - map, parties, POIs, etc.)
    python tools/profile_game.py --method cprofile --duration 60 --mode overworld

    # Profile exploration/dungeon (battle-ready, FOV, etc.)
    python tools/profile_game.py --method cprofile --duration 60 --mode exploration

    # Profile by loading an existing save (realistic state)
    python tools/profile_game.py --method cprofile --duration 60 --mode load --slot 1

    # Profile with py-spy (sampling profiler, no code changes)
    python tools/profile_game.py --method pyspy --duration 60

    # Profile memory usage
    python tools/profile_game.py --method memory --duration 60
"""

import argparse
import cProfile
import pstats
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def _create_game_overworld(screen, hero_class_id: str = "warrior"):
    """Create a game starting in overworld mode (no dungeon loaded)."""
    from engine.core.game import Game
    from world.overworld.config import OverworldConfig

    config = OverworldConfig.load()
    game = Game(screen, hero_class_id=hero_class_id, overworld_config=config)
    return game


def _create_game_exploration(screen, hero_class_id: str = "warrior"):
    """Create a game and load into exploration/dungeon mode."""
    from engine.core.game import Game

    game = Game(screen, hero_class_id=hero_class_id)
    game.load_floor(1, from_direction=None)
    return game


def _create_game_from_save(screen, slot: int):
    """Load a game from save file."""
    from engine.utils.save_system import load_game

    game = load_game(screen, slot=slot)
    if game is None:
        raise RuntimeError(f"Failed to load save slot {slot}. Ensure a save exists.")
    return game


def profile_with_cprofile(
    duration: int = 30,
    output_file: str = "profile_results.prof",
    mode: str = "overworld",
    slot: int = 1,
):
    """
    Profile the game using cProfile (built-in Python profiler).

    Args:
        duration: How long to profile in seconds
        output_file: Where to save the profile results
        mode: Profile target - "overworld", "exploration", or "load"
        slot: Save slot for mode="load" (1-9)
    """
    print(f"Starting cProfile profiling for {duration} seconds...")
    print(f"Mode: {mode}")
    print("(Play the game normally during this time)")
    if mode == "load":
        print(f"Loading from save slot {slot}...")

    profiler = cProfile.Profile()

    import pygame
    from settings import TITLE, FPS
    from engine.core.config import load_config

    pygame.init()
    pygame.display.set_caption(f"{TITLE} (Profiling)")

    config = load_config()
    width, height = config.get_resolution()
    screen = pygame.display.set_mode((width, height))
    clock = pygame.time.Clock()

    try:
        if mode == "overworld":
            game = _create_game_overworld(screen)
            print("Game started in OVERWORLD mode. Move around, zoom, interact with parties.")
        elif mode == "exploration":
            game = _create_game_exploration(screen)
            print("Game started in EXPLORATION mode. Move in dungeon, enter battles.")
        elif mode == "load":
            game = _create_game_from_save(screen, slot)
            mode_str = getattr(game, "mode", "unknown")
            print(f"Game loaded. Current mode: {mode_str}")
        else:
            raise ValueError(f"Unknown mode: {mode}")
    except Exception as e:
        print(f"Failed to create game: {e}")
        pygame.quit()
        sys.exit(1)

    print(f"\nProfiling started. Play the game...")
    print(f"Profiling will stop after {duration} seconds or when you close the game.")

    start_time = time.time()

    try:
        profiler.enable()

        running = True
        while running and (time.time() - start_time) < duration:
            dt = clock.tick(FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break
                game.handle_event(event)

            if not running:
                break

            game.update(dt)
            game.draw()
            pygame.display.flip()

    except KeyboardInterrupt:
        print("\nProfiling interrupted by user")
    finally:
        profiler.disable()
        pygame.quit()

    profiler.dump_stats(output_file)
    print(f"\nProfile data saved to {output_file}")
    print(f"\nTo view results:")
    print(f"  python -m pstats {output_file}")
    print(f"  # In pstats: sort cumulative, stats 50")
    print(f"\nOr use snakeviz for visual browser:")
    print(f"  snakeviz {output_file}")


def profile_with_pyspy(duration: int = 30, output_file: str = "profile_pyspy.svg"):
    """
    Profile the game using py-spy (sampling profiler).
    
    This doesn't require code changes and has minimal overhead.
    
    Args:
        duration: How long to profile in seconds
        output_file: Where to save the profile results (SVG format)
    """
    print(f"py-spy profiling instructions:")
    print(f"1. Start your game: python main.py")
    print(f"2. In another terminal, run:")
    print(f"   py-spy record -o {output_file} --duration {duration} --pid <game_pid>")
    print(f"\nOr record from start:")
    print(f"   py-spy record -o {output_file} --duration {duration} -- python main.py")
    print(f"\nView the SVG file in a web browser: {output_file}")


def profile_memory(duration: int = 30):
    """
    Profile memory usage of the game.
    
    Args:
        duration: How long to profile in seconds
    """
    print("Memory profiling requires @profile decorator on functions.")
    print("See docs/PERFORMANCE_PROFILING.md for details.")
    print("\nBasic usage:")
    print("  python -m memory_profiler your_script.py")


def analyze_profile(profile_file: str = "profile_results.prof", sort_by: str = "cumulative", lines: int = 50):
    """
    Analyze a cProfile output file.
    
    Args:
        profile_file: Path to .prof file
        sort_by: How to sort results (cumulative, time, calls, etc.)
        lines: Number of lines to show
    """
    stats = pstats.Stats(profile_file)
    stats.sort_stats(sort_by)
    stats.print_stats(lines)
    
    print(f"\nTop functions by {sort_by}:")
    stats.print_callers(lines)


def main():
    parser = argparse.ArgumentParser(description="Profile game performance")
    parser.add_argument(
        "--method",
        choices=["cprofile", "pyspy", "memory", "analyze"],
        default="cprofile",
        help="Profiling method to use"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=30,
        help="How long to profile in seconds (default: 30)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path"
    )
    parser.add_argument(
        "--analyze-file",
        type=str,
        default="profile_results.prof",
        help="Profile file to analyze (for analyze method)"
    )
    parser.add_argument(
        "--sort-by",
        type=str,
        default="cumulative",
        choices=["cumulative", "time", "calls", "tottime"],
        help="How to sort results (for analyze method)"
    )
    parser.add_argument(
        "--lines",
        type=int,
        default=50,
        help="Number of lines to show (for analyze method)"
    )
    parser.add_argument(
        "--mode",
        choices=["overworld", "exploration", "load"],
        default="overworld",
        help="What to profile: overworld (map/parties/POIs), exploration (dungeon), or load from save (default: overworld)"
    )
    parser.add_argument(
        "--slot",
        type=int,
        default=1,
        choices=range(1, 10),
        metavar="1-9",
        help="Save slot for --mode load (default: 1)"
    )
    
    args = parser.parse_args()
    
    if args.method == "cprofile":
        output = args.output or "profile_results.prof"
        profile_with_cprofile(args.duration, output, mode=args.mode, slot=args.slot)
    elif args.method == "pyspy":
        output = args.output or "profile_pyspy.svg"
        profile_with_pyspy(args.duration, output)
    elif args.method == "memory":
        profile_memory(args.duration)
    elif args.method == "analyze":
        analyze_profile(args.analyze_file, args.sort_by, args.lines)


if __name__ == "__main__":
    main()

