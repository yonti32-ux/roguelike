#!/usr/bin/env python3
"""
Performance profiling script for the game.

This script provides various profiling options to identify performance bottlenecks.

Usage:
    # Profile with cProfile (built-in, no extra dependencies)
    python tools/profile_game.py --method cprofile --duration 60
    
    # Profile with py-spy (sampling profiler, no code changes)
    python tools/profile_game.py --method pyspy --duration 60
    
    # Profile memory usage
    python tools/profile_game.py --method memory --duration 60
    
    # Profile specific function
    python tools/profile_game.py --method cprofile --function game.update
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


def profile_with_cprofile(duration: int = 30, output_file: str = "profile_results.prof"):
    """
    Profile the game using cProfile (built-in Python profiler).
    
    Args:
        duration: How long to profile in seconds
        output_file: Where to save the profile results
    """
    print(f"Starting cProfile profiling for {duration} seconds...")
    print("(Play the game normally during this time)")
    
    profiler = cProfile.Profile()
    
    # Import and run the game
    import pygame
    from settings import WINDOW_WIDTH, WINDOW_HEIGHT, TITLE, FPS
    from engine.core.game import Game
    from engine.scenes.character_creation import CharacterCreationScene
    from engine.scenes.main_menu import MainMenuScene
    from engine.scenes.save_menu import SaveMenuScene
    from engine.utils.save_system import load_game
    
    pygame.init()
    pygame.display.set_caption(f"{TITLE} (Profiling)")
    
    from engine.core.config import load_config
    config = load_config()
    width, height = config.get_resolution()
    screen = pygame.display.set_mode((width, height))
    clock = pygame.time.Clock()
    
    # Quick start - create a test game
    main_menu = MainMenuScene(screen)
    # For profiling, we'll skip menu and create a test game directly
    # You might want to load a save file instead
    
    print("\nProfiling started. Play the game...")
    print(f"Profiling will stop after {duration} seconds or when you close the game.")
    
    start_time = time.time()
    
    try:
        # Start profiling
        profiler.enable()
        
        # Quick test game creation (modify as needed)
        # For full profiling, you'd load a save or create a game normally
        game = Game(screen, hero_class_id="warrior")
        game.load_floor(1, from_direction=None)
        
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
    
    # Save results
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
    
    args = parser.parse_args()
    
    if args.method == "cprofile":
        output = args.output or "profile_results.prof"
        profile_with_cprofile(args.duration, output)
    elif args.method == "pyspy":
        output = args.output or "profile_pyspy.svg"
        profile_with_pyspy(args.duration, output)
    elif args.method == "memory":
        profile_memory(args.duration)
    elif args.method == "analyze":
        analyze_profile(args.analyze_file, args.sort_by, args.lines)


if __name__ == "__main__":
    main()

