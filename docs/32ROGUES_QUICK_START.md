# 32rogues Integration - Quick Start Guide

## Summary

We've analyzed the 32rogues asset pack and created tools for integration. Here's what you need to do:

---

## ✅ What's Ready

1. **Extraction Script**: `tools/extract_32rogues_sprites.py`
   - Extracts individual 32×32 sprites from sprite sheets
   - Organizes them into proper directories
   - Parses metadata from .txt files for naming

2. **Integration Plan**: `docs/32ROGUES_INTEGRATION_PLAN.md`
   - Complete step-by-step integration guide
   - Sprite mapping tables
   - Registry update instructions

---

## 🚀 Step-by-Step Integration

### Step 1: Extract Sprites (5 minutes)

Run the extraction script:

```bash
cd i:\python\roguelike_v2
python tools/extract_32rogues_sprites.py
```

**What this does:**
- Reads all sprite sheets from `32rogues/` directory
- Extracts individual 32×32 sprites
- Saves them to `sprites/entity/`, `sprites/item/`, `sprites/tile/`, `sprites/effect/`
- Creates a summary document

**Expected output:**
```
Processing rogues.png (7x7 grid)...
  Extracted 49 sprites to sprites/entity/
Processing monsters.png (13x12 grid)...
  Extracted 156 sprites to sprites/entity/
...
```

### Step 2: Review Extracted Sprites (10 minutes)

Check the extracted sprites:
- Open `sprites/entity/` - Should have character/monster sprites
- Open `sprites/item/` - Should have weapon/item sprites
- Open `sprites/tile/` - Should have floor/wall sprites

**Note**: Sprites will be named like `rogues_0_3.png` (sheet_row_col). You'll need to rename the important ones in Step 3.

### Step 3: Rename Key Sprites (15 minutes)

Rename the most important sprites to match game IDs:

**Player sprite:**
```bash
# Rename default player sprite
sprites/entity/rogues_0_3.png → sprites/entity/player.png  (rogue character)
```

**Enemy sprites** (based on enemy IDs from `systems/enemies.py`):
```bash
# Goblins
sprites/entity/monsters_0_2.png → sprites/entity/enemy_goblin.png
sprites/entity/monsters_0_7.png → sprites/entity/enemy_goblin_brute.png
sprites/entity/monsters_0_6.png → sprites/entity/enemy_goblin_shaman.png

# Orcs
sprites/entity/monsters_0_0.png → sprites/entity/enemy_orc.png

# Skeletons/Undead
sprites/entity/monsters_4_0.png → sprites/entity/enemy_skeleton.png
sprites/entity/monsters_4_1.png → sprites/entity/enemy_skeleton_archer.png
sprites/entity/monsters_4_2.png → sprites/entity/enemy_lich.png
sprites/entity/monsters_4_3.png → sprites/entity/enemy_death_knight.png
sprites/entity/monsters_4_4.png → sprites/entity/enemy_zombie.png
sprites/entity/monsters_4_5.png → sprites/entity/enemy_ghoul.png

# Spirits
sprites/entity/monsters_5_0.png → sprites/entity/enemy_banshee.png
sprites/entity/monsters_5_1.png → sprites/entity/enemy_reaper.png

# Default fallback
sprites/entity/monsters_0_0.png → sprites/entity/enemy_default.png  (or copy one)
```

**Tile sprites:**
```bash
# Floors
sprites/tile/tiles_6_1.png → sprites/tile/floor.png  (floor stone 1)

# Walls
sprites/tile/tiles_2_0.png → sprites/tile/wall.png  (stone brick wall top)

# Stairs (may need to create or use variant)
# For now, keep color-based stairs or find suitable sprite
```

**Item sprites** (based on item IDs from `data/items.json`):
```bash
# Weapons
sprites/item/items_0_0.png → sprites/item/cracked_dagger.png  (dagger)
sprites/item/items_0_1.png → sprites/item/rusty_sword.png  (short sword)
sprites/item/items_0_3.png → sprites/item/long_sword.png  (long sword)
# ... etc for other weapons
```

### Step 4: Update Sprite Registry (10 minutes)

Edit `engine/sprites/sprite_registry.py` to register enemy sprites. Add this to `init_registry()` function:

```python
def init_registry() -> SpriteRegistry:
    """Initialize the global sprite registry and load default mappings."""
    global _registry
    _registry = SpriteRegistry()
    
    # Auto-load item mappings if items data is available
    try:
        from systems.inventory import all_items
        items = all_items()
        items_data = [{"id": item.id} for item in items]
        _registry.load_item_mappings_from_data(items_data)
    except Exception:
        pass  # Items not loaded yet, that's okay
    
    # Register enemy sprite mappings
    _registry.register_enemy_sprite("goblin_skirmisher", "enemy_goblin")
    _registry.register_enemy_sprite("goblin_brute", "enemy_goblin_brute")
    _registry.register_enemy_sprite("goblin_shaman", "enemy_goblin_shaman")
    _registry.register_enemy_sprite("skeleton_archer", "enemy_skeleton_archer")
    _registry.register_enemy_sprite("orc_raider", "enemy_orc")
    _registry.register_enemy_sprite("ghoul_ripper", "enemy_ghoul")
    _registry.register_enemy_sprite("lich", "enemy_lich")
    _registry.register_enemy_sprite("banshee", "enemy_banshee")
    _registry.register_enemy_sprite("dread_knight", "enemy_death_knight")
    _registry.register_enemy_sprite("necromancer", "enemy_necro")  # Use appropriate sprite
    # Add more as needed...
    
    return _registry
```

### Step 5: Update Sprite Preloading (5 minutes)

Edit `engine/sprites/init_sprites.py` to preload commonly used sprites:

```python
def init_game_sprites_with_preload() -> None:
    """Initialize sprite system with common sprites preloaded."""
    sprite_manager = init_sprite_manager()
    init_registry()
    
    # Preload commonly used sprites
    sprite_manager.preload_sprites([
        (SpriteCategory.ENTITY, "player", None),
        (SpriteCategory.ENTITY, "enemy_default", None),
        (SpriteCategory.ENTITY, "enemy_goblin", None),
        (SpriteCategory.ENTITY, "enemy_orc", None),
        (SpriteCategory.ENTITY, "enemy_skeleton", None),
        (SpriteCategory.TILE, "floor", None),
        (SpriteCategory.TILE, "wall", None),
        (SpriteCategory.TILE, "up_stairs", None),
        (SpriteCategory.TILE, "down_stairs", None),
    ])
    
    print("Sprite system initialized with preloading!")
```

### Step 6: Update Entity Rendering Code (10 minutes)

Check `world/entities.py` and ensure enemies use the sprite registry. The code should already be using `get_registry().get_enemy_sprite_id(enemy_archetype_id)`, but verify it's working.

Look for enemy rendering code that might need updating to use the sprite system instead of color-based rendering.

### Step 7: Test Integration (5 minutes)

Run the game:

```bash
python main.py
```

**What to check:**
- ✅ Player sprite appears correctly
- ✅ Enemy sprites appear correctly (different enemies show different sprites)
- ✅ Floor/wall tiles use sprite images instead of colors
- ✅ Items in inventory show sprite icons
- ✅ No errors in console about missing sprites

---

## 🎯 Quick Reference

### Key Files to Modify

1. **`tools/extract_32rogues_sprites.py`** - Extraction script (already created)
2. **`engine/sprites/sprite_registry.py`** - Add enemy sprite registrations
3. **`engine/sprites/init_sprites.py`** - Add sprites to preload list
4. **`world/entities.py`** - Verify enemy sprite usage
5. **`world/tiles.py`** - Verify tile sprite usage (may need updates)

### Sprite Directory Structure

```
sprites/
├── entity/       # Characters, monsters, NPCs
│   ├── player.png
│   ├── enemy_goblin.png
│   └── ...
├── item/         # Weapons, armor, consumables
│   ├── cracked_dagger.png
│   └── ...
├── tile/         # Floor, walls, terrain
│   ├── floor.png
│   ├── wall.png
│   └── ...
└── effect/       # Animated effects
    └── ...
```

### Common Enemy IDs → Sprite Names

- `goblin_skirmisher` → `enemy_goblin`
- `goblin_brute` → `enemy_goblin_brute`
- `goblin_shaman` → `enemy_goblin_shaman`
- `skeleton_archer` → `enemy_skeleton_archer`
- `orc_raider` → `enemy_orc`
- `ghoul_ripper` → `enemy_ghoul`
- `lich` → `enemy_lich`
- `banshee` → `enemy_banshee`
- `dread_knight` → `enemy_death_knight`

---

## ⚠️ Troubleshooting

### Sprites not showing?
- Check sprite files exist in correct directories
- Verify sprite names match what's registered
- Check console for error messages about missing sprites

### Wrong sprites showing?
- Verify enemy ID to sprite ID mapping in registry
- Check that sprite files are named correctly

### Game crashes or errors?
- Check that sprite initialization is called in `main.py`
- Verify all sprite paths are correct
- Check that pygame is initialized before loading sprites

---

## 📚 Next Steps (Optional)

After basic integration works:

1. **Add more sprite variants** - Different states, animations
2. **Use animated tiles** - Torches, fires from `animated-tiles.png`
3. **Add palette swaps** - Use `items-palette-swaps.png` for item variants
4. **Expand mappings** - Add sprites for all enemies/items
5. **Optimize** - Consider sprite atlasing if performance issues

---

## 📖 Full Documentation

See `docs/32ROGUES_INTEGRATION_PLAN.md` for complete integration guide with detailed mapping tables.

