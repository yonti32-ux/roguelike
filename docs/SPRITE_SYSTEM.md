# Sprite System Documentation

This document explains how to use the modular sprite system for adding sprites to the game.

## Overview

The sprite system is designed to be:
- **Modular**: Easy to add sprites one at a time
- **Flexible**: Supports multiple sprite categories and variants
- **Backward Compatible**: Falls back to colored rectangles when sprites are missing
- **Extensible**: Easy to add new sprite types and categories
- **Sprite Set Support**: Optional sprite sheets and animation sequences with auto-management

## Directory Structure

Sprites are organized in the `sprites/` directory by category:

```
sprites/
├── entity/          # Player, enemies, NPCs
│   ├── player.png
│   ├── enemy_default.png
│   ├── enemy_goblin.png
│   ├── chest.png
│   ├── merchant.png
│   └── event_node.png
├── tile/            # Floor, walls, stairs
│   ├── floor.png
│   ├── wall.png
│   ├── up_stairs.png
│   └── down_stairs.png
├── item/            # Weapons, armor, consumables
│   ├── cracked_dagger.png
│   ├── rusty_sword.png
│   ├── small_health_potion.png
│   └── ...
├── battle/          # Battle-specific sprites
│   └── ...
├── ui/              # UI elements
│   └── ...
├── effect/          # Status effects
│   └── ...
├── skill/           # Skill icons
│   └── ...
└── terrain/         # Battle terrain
    └── ...
```

## File Naming Convention

### Basic Sprites
- Format: `{sprite_id}.png`
- Example: `player.png`, `floor.png`, `sword.png`

### Sprite Variants
- Format: `{sprite_id}_{variant}.png`
- Example: `player_idle.png`, `chest_opened.png`, `enemy_attacking.png`

## Quick Start

### 1. Adding Your First Sprite

1. Create the sprite file (e.g., `sprites/entity/player.png`)
2. The system will automatically load it when requested
3. If the sprite is missing, it will use a colored rectangle fallback

### 2. Basic Usage

```python
from engine.sprites import get_sprite_manager, SpriteCategory
from engine.sprite_registry import get_registry, EntitySpriteType

# Get sprite manager and registry
sprite_manager = get_sprite_manager()
registry = get_registry()

# Get a sprite
sprite = sprite_manager.get_sprite(
    SpriteCategory.ENTITY,
    "player",
    size=(32, 32)
)

# Draw it
surface.blit(sprite, (x, y))
```

### 3. Using Helper Functions

```python
from engine.sprite_helpers import draw_entity_sprite, EntitySpriteType

# Draw an entity with its sprite
draw_entity_sprite(
    surface,
    EntitySpriteType.PLAYER,
    x, y,
    width=32, height=32
)
```

## Integration Examples

### Integrating with Entities

Modify entity draw methods to use sprites:

```python
from engine.sprite_helpers import draw_entity_sprite, EntitySpriteType, draw_sprite_with_camera

class Player(Entity):
    def draw(self, surface, camera_x=0.0, camera_y=0.0, zoom=1.0):
        # Get sprite
        from engine.sprites import get_sprite_manager, SpriteCategory
        from engine.sprite_registry import get_registry, EntitySpriteType
        
        sprite_manager = get_sprite_manager()
        registry = get_registry()
        
        sprite_id = registry.get_entity_sprite_id(EntitySpriteType.PLAYER)
        sprite = sprite_manager.get_sprite(
            SpriteCategory.ENTITY,
            sprite_id,
            size=(self.width, self.height),
            fallback_color=self.color  # Use existing color as fallback
        )
        
        # Draw with camera transform
        draw_sprite_with_camera(
            surface, sprite,
            self.x, self.y,
            camera_x, camera_y, zoom
        )
```

### Integrating with Tiles

Modify tile rendering to use sprites:

```python
from engine.sprite_helpers import draw_tile_sprite, TileSpriteType

def draw_tile(self, surface, x, y, tile_type):
    if tile_type == FLOOR_TILE:
        draw_tile_sprite(surface, TileSpriteType.FLOOR, x, y, TILE_SIZE)
    elif tile_type == WALL_TILE:
        draw_tile_sprite(surface, TileSpriteType.WALL, x, y, TILE_SIZE)
```

### Registering Custom Mappings

If your sprite filename doesn't match the default ID:

```python
from engine.sprite_registry import get_registry

registry = get_registry()

# Register custom item sprite
registry.register_item_sprite("cracked_dagger", "weapon_dagger")

# Register custom enemy sprite
registry.register_enemy_sprite("goblin_warrior", "enemy_goblin_armored")
```

## Adding New Sprite Types

### 1. Add a New Category

Edit `engine/sprites.py`:

```python
class SpriteCategory(Enum):
    # ... existing categories ...
    NEW_TYPE = "new_type"
```

Create the directory: `sprites/new_type/`

### 2. Add Registry Support

Edit `engine/sprite_registry.py` to add mappings for the new type.

## Sprite Sets (Optional)

The sprite system supports **sprite sets** - sprite sheets and animation sequences that are automatically managed!

### Quick Overview

- **Sprite Sheets**: Multiple sprites in one image file (grid-based)
- **Animation Sequences**: Multiple image files forming an animation
- **Auto-Detection**: Automatically detects sprite set configurations
- **Seamless Integration**: Works with existing sprite code

### Example: Using a Sprite Sheet

```python
from engine.sprites import get_sprite_manager, SpriteCategory
from engine.sprite_sets import SpriteSetManager, SpriteSetType, SpriteSheetConfig

sprite_manager = get_sprite_manager()
set_manager = sprite_manager.get_sprite_set_manager()

# Register a sprite sheet
set_manager.register_sprite_set(
    sprite_id="player",
    category="entity",
    set_type=SpriteSetType.SHEET,
    file_path="player_sheet.png",
    sheet_config=SpriteSheetConfig(rows=4, cols=4)  # 16 sprites
)

# Get a sprite from the sheet
sprite = sprite_manager.get_sprite(
    SpriteCategory.ENTITY,
    "player",
    frame_index=5  # Get 6th sprite (0-based)
)
```

### Example: Using an Animation Sequence

```python
# Register an animation sequence
set_manager.register_sprite_set(
    sprite_id="player_walk",
    category="entity",
    set_type=SpriteSetType.SEQUENCE,
    file_path="player_walk",  # Base name
    sequence_config=AnimationSequenceConfig(frame_count=8)
)

# Get an animation frame
frame = sprite_manager.get_sprite(
    SpriteCategory.ENTITY,
    "player_walk",
    frame_index=current_frame
)
```

**For detailed sprite set documentation, see `SPRITE_SETS_GUIDE.md`**

## Advanced Features

### Sprite Variants

Use variants for different states:

```python
# Get idle sprite
sprite = sprite_manager.get_sprite(
    SpriteCategory.ENTITY,
    "player",
    variant="idle"
)  # Looks for: sprites/entity/player_idle.png

# Get attacking sprite
sprite = sprite_manager.get_sprite(
    SpriteCategory.ENTITY,
    "player",
    variant="attacking"
)  # Looks for: sprites/entity/player_attacking.png
```

### Preloading Sprites

Preload commonly used sprites for better performance:

```python
sprite_manager = get_sprite_manager()
sprite_manager.preload_sprites([
    (SpriteCategory.ENTITY, "player", None),
    (SpriteCategory.TILE, "floor", None),
    (SpriteCategory.ITEM, "sword", None),
])
```

### Clearing Cache

If you need to reload sprites:

```python
sprite_manager.clear_cache()
```

## Best Practices

1. **Start Small**: Add sprites one at a time, testing as you go
2. **Use Fallbacks**: Always provide fallback colors for missing sprites
3. **Consistent Naming**: Use clear, descriptive sprite IDs
4. **Organize by Category**: Keep sprites organized in their category folders
5. **Test Missing Sprites**: Verify fallbacks work when sprites are missing

## Troubleshooting

### Sprite Not Showing

1. Check the file exists in the correct directory
2. Verify the filename matches the sprite_id exactly
3. Check for typos in category names
4. Look for error messages in console about missing sprites

### Performance Issues

1. Use sprite caching (automatic)
2. Preload commonly used sprites
3. Use appropriate sprite sizes (don't use huge images for small icons)

### Missing Sprites

The system will automatically use colored rectangles as fallbacks. To customize fallback colors:

```python
sprite = sprite_manager.get_sprite(
    SpriteCategory.ENTITY,
    "player",
    fallback_color=(220, 210, 90)  # Custom fallback color
)
```

