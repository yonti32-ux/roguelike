# Sprite Sets Guide

The sprite system now supports **sprite sets** - sprite sheets and animation sequences that are automatically managed!

## What Are Sprite Sets?

### Sprite Sheets
A single image file containing multiple sprites arranged in a grid. Perfect for:
- Multiple animation frames in one file
- Variants of the same sprite (idle, walk, attack)
- Tilesets
- UI element sets

### Animation Sequences
Multiple image files that form an animation sequence. Perfect for:
- Character animations (walking, attacking)
- Effect animations
- Complex multi-frame animations

## Quick Start

### Using a Sprite Sheet

1. **Create your sprite sheet image**
   - Arrange sprites in a grid (e.g., 4x4, 2x3, etc.)
   - Save as PNG: `sprites/entity/player_sheet.png`

2. **Register the sprite set** (optional - can auto-detect)
   ```python
   from engine.sprites import get_sprite_manager
   from engine.sprite_sets import SpriteSetManager, SpriteSetType, SpriteSheetConfig
   
   sprite_manager = get_sprite_manager()
   set_manager = sprite_manager.get_sprite_set_manager()
   
   set_manager.register_sprite_set(
       sprite_id="player",
       category="entity",
       set_type=SpriteSetType.SHEET,
       file_path="player_sheet.png",
       sheet_config=SpriteSheetConfig(
           rows=4,  # 4 rows
           cols=4,  # 4 columns (16 sprites total)
           spacing_x=0,  # No spacing
           spacing_y=0,  # No spacing
       )
   )
   ```

3. **Use it in your code**
   ```python
   # Get sprite from sheet by row/column
   sprite = sprite_manager.get_sprite(
       SpriteCategory.ENTITY,
       "player",
       sheet_row=0,
       sheet_col=0  # Top-left sprite
   )
   
   # Or by frame index (row-major order)
   sprite = sprite_manager.get_sprite(
       SpriteCategory.ENTITY,
       "player",
       frame_index=5  # 6th sprite (0-based)
   )
   ```

### Using an Animation Sequence

1. **Create your animation frames**
   - Name them sequentially: `player_walk_1.png`, `player_walk_2.png`, etc.
   - Place in category folder: `sprites/entity/`

2. **Register the animation** (optional - can auto-detect)
   ```python
   from engine.sprite_sets import AnimationSequenceConfig
   
   set_manager.register_sprite_set(
       sprite_id="player_walk",
       category="entity",
       set_type=SpriteSetType.SEQUENCE,
       file_path="player_walk",  # Base name
       sequence_config=AnimationSequenceConfig(
           frame_count=8,  # 8 frames
           frame_prefix="player_walk_",
           start_index=1,  # Frames start at 1
           loop=True
       )
   )
   ```

3. **Use it in your code**
   ```python
   # Get animation frame
   frame = sprite_manager.get_sprite(
       SpriteCategory.ENTITY,
       "player_walk",
       frame_index=current_frame  # 0-based index
   )
   ```

## Configuration File

Instead of registering in code, you can use a JSON config file:

**`sprites/sprite_sets.json`**
```json
{
  "player": {
    "set_type": "sheet",
    "category": "entity",
    "file_path": "player_sheet.png",
    "sheet_config": {
      "rows": 4,
      "cols": 4,
      "spacing_x": 0,
      "spacing_y": 0,
      "padding_x": 0,
      "padding_y": 0
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
```

The config file is automatically loaded when the sprite set manager initializes.

## Auto-Detection

If `auto_detect` is enabled (default), the system will try to automatically detect sprite set configurations:

### Sprite Sheets
- Tries common grid patterns
- Can detect simple 2x2, 4x4 layouts
- Falls back to single sprite if detection fails

### Animation Sequences
- Automatically finds numbered frames (e.g., `sprite_1.png`, `sprite_2.png`)
- Detects frame patterns
- Works with various naming conventions

## Examples

### Example 1: Player Character with Multiple Animations

```python
# Register player idle animation (sprite sheet)
set_manager.register_sprite_set(
    "player_idle",
    "entity",
    SpriteSetType.SHEET,
    "player_idle_sheet.png",
    sheet_config=SpriteSheetConfig(rows=1, cols=4)  # 4-frame idle animation
)

# Register player walk animation (sequence)
set_manager.register_sprite_set(
    "player_walk",
    "entity",
    SpriteSetType.SEQUENCE,
    "player_walk",
    sequence_config=AnimationSequenceConfig(frame_count=8, loop=True)
)

# In your game loop
idle_frame = animation_timer % 4  # Loop through 4 frames
walk_frame = animation_timer % 8  # Loop through 8 frames

if player.moving:
    sprite = sprite_manager.get_sprite(
        SpriteCategory.ENTITY,
        "player_walk",
        frame_index=walk_frame
    )
else:
    sprite = sprite_manager.get_sprite(
        SpriteCategory.ENTITY,
        "player_idle",
        frame_index=idle_frame
    )
```

### Example 2: Tileset

```python
# Register tileset sprite sheet
set_manager.register_sprite_set(
    "tileset",
    "tile",
    SpriteSetType.SHEET,
    "tileset.png",
    sheet_config=SpriteSheetConfig(rows=8, cols=8)  # 64 different tiles
)

# Use different tiles
floor_tile = sprite_manager.get_sprite(
    SpriteCategory.TILE,
    "tileset",
    sheet_row=0,
    sheet_col=0
)

wall_tile = sprite_manager.get_sprite(
    SpriteCategory.TILE,
    "tileset",
    sheet_row=1,
    sheet_col=0
)
```

### Example 3: Item Icons Sheet

```python
# Register item icons sheet (all items in one image)
set_manager.register_sprite_set(
    "items",
    "item",
    SpriteSetType.SHEET,
    "item_icons.png",
    sheet_config=SpriteSheetConfig(rows=10, cols=10)  # 100 items
)

# Get specific item icon by index
sword_icon_index = 5  # Sword is at index 5
sword_icon = sprite_manager.get_sprite(
    SpriteCategory.ITEM,
    "items",
    frame_index=sword_icon_index
)
```

## Advanced Features

### Sprite Sheet Configuration Options

```python
SpriteSheetConfig(
    rows=4,              # Number of rows
    cols=4,              # Number of columns
    sprite_width=32,     # Fixed sprite width (auto if None)
    sprite_height=32,    # Fixed sprite height (auto if None)
    spacing_x=2,         # Horizontal spacing between sprites
    spacing_y=2,         # Vertical spacing between sprites
    padding_x=1,         # Padding from left/right edges
    padding_y=1,         # Padding from top/bottom edges
)
```

### Animation Sequence Configuration Options

```python
AnimationSequenceConfig(
    frames=["frame1.png", "frame2.png", ...],  # Explicit frame list
    frame_count=8,                              # Or auto-detect count
    frame_prefix="walk_",                      # Prefix for numbered frames
    frame_suffix="_anim",                      # Suffix for numbered frames
    start_index=1,                             # Starting index (1 or 0)
    loop=True,                                 # Whether to loop animation
)
```

## Integration with Existing Code

Sprite sets work seamlessly with the existing sprite system:

```python
# This works for both regular sprites AND sprite sets
sprite = sprite_manager.get_sprite(
    SpriteCategory.ENTITY,
    "player",
    variant="idle",
    frame_index=current_frame  # Only used if it's a sprite set
)

# Regular sprites ignore frame_index
# Sprite sets use it automatically
```

## Best Practices

1. **Use sprite sheets for related sprites** - Better organization, fewer files
2. **Use sequences for complex animations** - Easier to manage individual frames
3. **Name frames consistently** - Helps auto-detection work better
4. **Preload commonly used sprite sets** - Better performance
5. **Use config files for complex setups** - Easier to manage

## Disabling Sprite Sets

If you don't want to use sprite sets, you can disable them:

```python
sprite_manager = get_sprite_manager()
sprite_manager.enable_sprite_sets = False
```

Regular sprite loading will still work normally.

