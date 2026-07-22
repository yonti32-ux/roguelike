"""
Simple initialization function for the sprite system.

Call this once at game startup to initialize the sprite system.
This is optional - the system works with defaults, but initialization
gives you more control and auto-loads item mappings.
"""

from .sprites import init_sprite_manager, get_sprite_manager, SpriteCategory
from .sprite_registry import init_registry


def init_game_sprites() -> None:
    """
    Initialize the sprite system for the game.
    
    Call this once at game startup (e.g., in Game.__init__() or main()).
    
    This will:
    - Initialize the sprite manager
    - Initialize the registry and auto-load item mappings
    - Optionally preload commonly used sprites
    """
    # Initialize sprite manager (uses default: sprites/ directory)
    sprite_manager = init_sprite_manager()
    
    # Initialize registry (auto-loads item sprite mappings from your item data)
    init_registry()
    
    # Optional: Preload commonly used sprites for better performance
    # Uncomment and customize as needed:
    # sprite_manager.preload_sprites([
    #     (SpriteCategory.ENTITY, "player", None),
    #     (SpriteCategory.TILE, "floor", None),
    #     (SpriteCategory.TILE, "wall", None),
    # ])
    
    print("Sprite system initialized!")


def init_game_sprites_with_preload() -> None:
    """
    Initialize sprite system with common sprites preloaded.
    
    Use this if you want better performance by preloading frequently used sprites.
    """
    sprite_manager = init_sprite_manager()
    init_registry()
    
    # Preload commonly used sprites
    sprite_manager.preload_sprites([
        (SpriteCategory.ENTITY, "player", None),
        (SpriteCategory.ENTITY, "enemy_default", None),
        (SpriteCategory.ENTITY, "chest", None),
        (SpriteCategory.TILE, "floor", None),
        (SpriteCategory.TILE, "wall", None),
        (SpriteCategory.TILE, "up_stairs", None),
        (SpriteCategory.TILE, "down_stairs", None),
    ])
    
    print("Sprite system initialized with preloading!")

