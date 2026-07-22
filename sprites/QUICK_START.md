# Sprite System Quick Start Guide

## Adding Your First Sprite

1. **Create the sprite file**
   - Place it in the appropriate folder (e.g., `sprites/entity/player.png`)
   - Use PNG format with transparency support

2. **The system automatically finds it!**
   - No code changes needed for basic sprites
   - The system uses the entity/item ID to find the sprite

3. **Test it**
   - Run your game
   - The sprite should appear automatically
   - If missing, you'll see a colored rectangle (fallback)

## File Locations by Type

### Entities
- Player: `sprites/entity/player.png`
- Enemies: `sprites/entity/enemy_default.png` or `sprites/entity/enemy_{type}.png`
- Chests: `sprites/entity/chest.png` (or `chest_opened.png` for opened state)
- Merchants: `sprites/entity/merchant.png`

### Tiles
- Floor: `sprites/tile/floor.png`
- Wall: `sprites/tile/wall.png`
- Up Stairs: `sprites/tile/up_stairs.png`
- Down Stairs: `sprites/tile/down_stairs.png`

### Items
- Items use their ID from `data/items.json` or `data/consumables.json`
- Example: Item ID `"cracked_dagger"` → `sprites/item/cracked_dagger.png`
- Example: Item ID `"small_health_potion"` → `sprites/item/small_health_potion.png`

## Common Use Cases

### Adding a Player Sprite
1. Create `sprites/entity/player.png`
2. Done! The system will use it automatically

### Adding an Item Sprite
1. Find the item ID (from `data/items.json`)
2. Create `sprites/item/{item_id}.png`
3. Done!

### Adding Enemy Sprites
1. Option 1: Use default - create `sprites/entity/enemy_default.png`
2. Option 2: Specific type - register in code:
   ```python
   from engine.sprite_registry import get_registry
   registry = get_registry()
   registry.register_enemy_sprite("goblin", "enemy_goblin")
   # Then create: sprites/entity/enemy_goblin.png
   ```

### Adding Sprite Variants (Different States)
- Format: `{sprite_id}_{variant}.png`
- Example: `player_idle.png`, `player_walking.png`, `chest_opened.png`

## Integration Checklist

To enable sprites in your game:

1. ✅ Sprite system is already created
2. ✅ Directory structure exists
3. ⬜ Initialize sprite system (add to game startup - see integration example)
4. ⬜ Add sprite files as you create them
5. ⬜ Optionally update entity draw methods to use sprites (see integration example)

## Need Help?

- See `SPRITE_SYSTEM.md` for full documentation
- See `engine/sprite_integration_example.py` for code examples
- Check console for warnings about missing sprites

