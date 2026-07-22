"""
Example code for using sprite sets (sprite sheets and animation sequences).

This demonstrates how to:
- Register sprite sets
- Use sprite sheets
- Use animation sequences
- Auto-detect sprite sets
"""

from .sprites import get_sprite_manager, SpriteCategory
from .sprite_sets import (
    SpriteSetManager,
    SpriteSetType,
    SpriteSheetConfig,
    AnimationSequenceConfig,
)


def example_sprite_sheet_basic():
    """Basic sprite sheet usage example."""
    sprite_manager = get_sprite_manager()
    set_manager = sprite_manager.get_sprite_set_manager()
    
    # Register a sprite sheet
    set_manager.register_sprite_set(
        sprite_id="player",
        category="entity",
        set_type=SpriteSetType.SHEET,
        file_path="player_sheet.png",
        sheet_config=SpriteSheetConfig(
            rows=4,      # 4 rows
            cols=4,      # 4 columns (16 sprites total)
            spacing_x=0, # No spacing between sprites
            spacing_y=0,
        )
    )
    
    # Get sprites from the sheet
    # Method 1: By row and column
    sprite = sprite_manager.get_sprite(
        SpriteCategory.ENTITY,
        "player",
        sheet_row=0,
        sheet_col=0  # Top-left sprite
    )
    
    # Method 2: By frame index (row-major order)
    sprite = sprite_manager.get_sprite(
        SpriteCategory.ENTITY,
        "player",
        frame_index=5  # 6th sprite (0-based index)
    )


def example_animation_sequence():
    """Animation sequence usage example."""
    sprite_manager = get_sprite_manager()
    set_manager = sprite_manager.get_sprite_set_manager()
    
    # Register an animation sequence
    # Files: player_walk_1.png, player_walk_2.png, ... player_walk_8.png
    set_manager.register_sprite_set(
        sprite_id="player_walk",
        category="entity",
        set_type=SpriteSetType.SEQUENCE,
        file_path="player_walk",  # Base name
        sequence_config=AnimationSequenceConfig(
            frame_count=8,        # 8 frames
            frame_prefix="player_walk_",
            start_index=1,        # Frames start at 1
            loop=True             # Animation loops
        )
    )
    
    # Get animation frames
    current_frame = 0  # Animation frame counter
    sprite = sprite_manager.get_sprite(
        SpriteCategory.ENTITY,
        "player_walk",
        frame_index=current_frame % 8  # Loop through frames
    )


def example_character_animations():
    """Example: Character with multiple animations."""
    sprite_manager = get_sprite_manager()
    set_manager = sprite_manager.get_sprite_set_manager()
    
    # Register idle animation (sprite sheet with 4 frames)
    set_manager.register_sprite_set(
        "player_idle",
        "entity",
        SpriteSetType.SHEET,
        "player_idle_sheet.png",
        sheet_config=SpriteSheetConfig(rows=1, cols=4)
    )
    
    # Register walk animation (sequence with 8 frames)
    set_manager.register_sprite_set(
        "player_walk",
        "entity",
        SpriteSetType.SEQUENCE,
        "player_walk",
        sequence_config=AnimationSequenceConfig(frame_count=8, loop=True)
    )
    
    # Register attack animation (sequence with 6 frames)
    set_manager.register_sprite_set(
        "player_attack",
        "entity",
        SpriteSetType.SEQUENCE,
        "player_attack",
        sequence_config=AnimationSequenceConfig(frame_count=6, loop=False)
    )
    
    # In your game loop
    animation_timer = 0
    player_state = "idle"  # "idle", "walk", "attack"
    
    def get_player_sprite(current_timer, state):
        if state == "walk":
            frame = (current_timer // 10) % 8  # Change frame every 10 ticks
            return sprite_manager.get_sprite(
                SpriteCategory.ENTITY,
                "player_walk",
                frame_index=frame
            )
        elif state == "attack":
            frame = min((current_timer // 15) % 6, 5)  # Non-looping
            return sprite_manager.get_sprite(
                SpriteCategory.ENTITY,
                "player_attack",
                frame_index=frame
            )
        else:  # idle
            frame = (current_timer // 20) % 4  # Slower animation
            return sprite_manager.get_sprite(
                SpriteCategory.ENTITY,
                "player_idle",
                frame_index=frame
            )


def example_tileset():
    """Example: Using a tileset sprite sheet."""
    sprite_manager = get_sprite_manager()
    set_manager = sprite_manager.get_sprite_set_manager()
    
    # Register tileset (8x8 grid = 64 different tiles)
    set_manager.register_sprite_set(
        "tileset",
        "tile",
        SpriteSetType.SHEET,
        "tileset.png",
        sheet_config=SpriteSheetConfig(rows=8, cols=8)
    )
    
    # Define tile types
    TILE_FLOOR = (0, 0)      # Row 0, Col 0
    TILE_WALL = (1, 0)       # Row 1, Col 0
    TILE_WALL_CORNER = (1, 1)  # Row 1, Col 1
    
    # Get tile sprites
    floor_tile = sprite_manager.get_sprite(
        SpriteCategory.TILE,
        "tileset",
        sheet_row=TILE_FLOOR[0],
        sheet_col=TILE_FLOOR[1]
    )
    
    wall_tile = sprite_manager.get_sprite(
        SpriteCategory.TILE,
        "tileset",
        sheet_row=TILE_WALL[0],
        sheet_col=TILE_WALL[1]
    )


def example_auto_detection():
    """Example: Using auto-detection for sprite sets."""
    sprite_manager = get_sprite_manager()
    set_manager = sprite_manager.get_sprite_set_manager()
    
    # Register with auto-detection enabled (default)
    # System will try to detect configuration automatically
    set_manager.register_sprite_set(
        "player_walk",
        "entity",
        SpriteSetType.SEQUENCE,
        "player_walk",
        auto_detect=True  # Try to auto-detect frame count and naming
    )
    
    # Auto-detection will look for:
    # - player_walk_1.png, player_walk_2.png, etc.
    # - Or player_walk1.png, player_walk2.png
    # - Automatically counts frames
    # - Sets up loop configuration


def example_config_file():
    """Example: Using JSON config file for sprite sets."""
    # Create sprites/sprite_sets.json:
    """
    {
      "player": {
        "set_type": "sheet",
        "category": "entity",
        "file_path": "player_sheet.png",
        "sheet_config": {
          "rows": 4,
          "cols": 4,
          "spacing_x": 0,
          "spacing_y": 0
        },
        "auto_detect": true
      },
      "player_walk": {
        "set_type": "sequence",
        "category": "entity",
        "file_path": "player_walk",
        "sequence_config": {
          "frame_count": 8,
          "frame_prefix": "player_walk_",
          "start_index": 1,
          "loop": true
        },
        "auto_detect": true
      }
    }
    """
    
    # Config file is automatically loaded when sprite set manager initializes
    # No code needed - just use the sprite IDs!
    sprite_manager = get_sprite_manager()
    
    sprite = sprite_manager.get_sprite(
        SpriteCategory.ENTITY,
        "player",
        frame_index=0
    )


def example_item_icons_sheet():
    """Example: Item icons in a sprite sheet."""
    sprite_manager = get_sprite_manager()
    set_manager = sprite_manager.get_sprite_set_manager()
    
    # All item icons in one sheet (10x10 = 100 items)
    set_manager.register_sprite_set(
        "item_icons",
        "item",
        SpriteSetType.SHEET,
        "item_icons.png",
        sheet_config=SpriteSheetConfig(rows=10, cols=10)
    )
    
    # Define item icon indices
    ITEM_SWORD = 5
    ITEM_POTION = 23
    ITEM_SHIELD = 47
    
    # Get item icons
    sword_icon = sprite_manager.get_sprite(
        SpriteCategory.ITEM,
        "item_icons",
        frame_index=ITEM_SWORD
    )


if __name__ == "__main__":
    # Examples can be run individually
    print("Sprite set examples available. See function docstrings for usage.")
    print("Import this module and call example functions to try them out.")

