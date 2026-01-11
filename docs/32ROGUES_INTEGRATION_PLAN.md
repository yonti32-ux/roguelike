# 32rogues Asset Pack Integration Plan

## Overview
Integration plan for the 32rogues asset pack into the roguelike game.

## Current Status
✅ Asset pack analyzed  
✅ Extraction script created  
⏳ Sprites need to be extracted  
⏳ Sprites need to be mapped to game entities  
⏳ Sprite registry needs to be updated  

---

## Step 1: Extract Sprites from Sprite Sheets

### Run the Extraction Script

```bash
cd i:\python\roguelike_v2
python tools/extract_32rogues_sprites.py
```

This will:
- Extract individual 32×32 sprites from all sprite sheets
- Organize them into categories:
  - `sprites/entity/` - Characters, monsters, animals
  - `sprites/item/` - Weapons and items
  - `sprites/tile/` - Floor and wall tiles
  - `sprites/effect/` - Animated effects

### Expected Output Structure

```
sprites/
├── entity/
│   ├── rogues_0_0.png    (dwarf)
│   ├── rogues_0_1.png    (elf)
│   ├── rogues_0_2.png    (ranger)
│   ├── rogues_0_3.png    (rogue)
│   ├── monsters_0_0.png  (orc)
│   ├── monsters_0_1.png  (orc wizard)
│   └── ...
├── item/
│   ├── items_0_0.png     (dagger)
│   ├── items_0_1.png     (short sword)
│   └── ...
├── tile/
│   ├── tiles_6_0.png     (floor stone 1)
│   ├── tiles_6_1.png     (floor stone 2)
│   ├── tiles_0_0.png     (dirt wall top)
│   └── ...
└── effect/
    ├── animated-tiles_0_0.png  (brazier unlit)
    └── ...
```

---

## Step 2: Map Sprites to Game Entities

### Enemy Sprite Mappings

Based on `systems/enemies.py`, map enemy types to sprites:

| Enemy ID | Enemy Name | Sprite Source | Notes |
|----------|------------|---------------|-------|
| `goblin_skirmisher` | Goblin Skirmisher | `monsters.png` row 1, col 2 (goblin) | Use goblin sprite |
| `goblin_brute` | Goblin Brute | `monsters.png` row 1, col 7 (goblin brute) | Use goblin brute sprite |
| `goblin_shaman` | Goblin Shaman | `monsters.png` row 1, col 6 (goblin mage) | Use goblin mage sprite |
| `skeleton_archer` | Skeleton Archer | `monsters.png` row 5, col 1 (skeleton archer) | Direct match |
| `orc_raider` | Orc Raider | `monsters.png` row 1, col 0 (orc) | Use orc sprite |
| `ghoul_ripper` | Ghoul Ripper | `monsters.png` row 5, col 5 (ghoul) | Direct match |
| `necromancer` | Necromancer | `monsters.png` row 4, col 2 (unholy cardinal) or `rogues.png` | Use priest/monk variant |
| `dread_knight` | Dread Knight | `monsters.png` row 5, col 3 (death knight) | Direct match |
| `lich` | Lich | `monsters.png` row 5, col 2 (lich) | Direct match |
| `banshee` | Banshee | `monsters.png` row 6, col 0 (banshee) | Direct match |
| `dire_rat` | Dire Rat | `animals.png` or custom | May need different sprite |
| `shadow_stalker` | Shadow Stalker | `monsters.png` row 6, col 1 (reaper) | Use reaper sprite |
| `stone_golem` | Stone Golem | Create or use generic monster sprite | May need custom |

### Player Character Options

From `rogues.png`:
- Row 1, Col 3: **Rogue** (default player)
- Row 1, Col 0: Dwarf
- Row 1, Col 1: Elf
- Row 2, Col 0: Knight
- Row 3, Col 0: Monk
- Row 3, Col 1: Priest
- Row 4, Col 0: Male Barbarian
- Row 5, Col 0: Female Wizard
- Row 5, Col 1: Male Wizard

---

## Step 3: Map Sprites to Game Items

### Item Sprite Mappings

Based on `data/items.json`, map items to sprites from `items.png`:

| Item ID | Item Name | Sprite Source | Notes |
|---------|-----------|---------------|-------|
| `cracked_dagger` | Cracked Dagger | `items.png` row 0, col 0 (dagger) | Direct match |
| `rusty_sword` | Rusty Sword | `items.png` row 0, col 1 (short sword) | Direct match |
| `short_sword` | Short Sword | `items.png` row 0, col 1 (short sword) | Direct match |
| `long_sword` | Long Sword | `items.png` row 0, col 3 (long sword) | Direct match |
| `battle_axe` | Battle Axe | `items.png` row 3, col 1 (battle axe) | Direct match |
| `warhammer` | Warhammer | `items.png` row 4, col 1 (short warhammer) | Direct match |
| `rapier` | Rapier | `items.png` row 2, col 2 (rapier) | Direct match |

**Note**: Review all items in `data/items.json` and map them to appropriate sprites from the items sheet.

---

## Step 4: Map Sprites to Game Tiles

### Tile Sprite Mappings

From `tiles.png`, map to game tile types:

| Tile Type | Sprite Source | Notes |
|-----------|---------------|-------|
| `FLOOR_TILE` | Row 7, Col 1-3 (floor stones) | Use floor stone variants |
| `WALL_TILE` | Row 2, Col 0-2 (stone brick walls) | Use stone brick wall |
| `UP_STAIRS` | Create or use tile variant | May need custom sprite |
| `DOWN_STAIRS` | Create or use tile variant | May need custom sprite |

For overworld/grass areas:
- Use Row 8, Col 1-3 (grass tiles)

---

## Step 5: Rename Extracted Sprites

After extraction, rename sprites to match game IDs:

### Example Renaming Script

```python
# tools/rename_sprites.py
import shutil
from pathlib import Path

# Mapping of extracted sprite names to game IDs
RENAMING_MAP = {
    # Entities
    "monsters_1_0": "enemy_goblin",  # goblin
    "monsters_1_3": "enemy_orc",     # orc blademaster
    "monsters_5_1": "enemy_skeleton_archer",  # skeleton archer
    "monsters_5_2": "enemy_lich",    # lich
    "rogues_0_3": "player",          # rogue (default player)
    
    # Items
    "items_0_0": "cracked_dagger",   # dagger
    "items_0_1": "rusty_sword",      # short sword
    "items_0_3": "long_sword",       # long sword
    
    # Tiles
    "tiles_7_1": "floor",            # floor stone 1
    "tiles_2_0": "wall",             # stone brick wall top
}

def rename_sprites(sprites_dir: Path, mapping: dict):
    """Rename sprites according to mapping."""
    for old_name, new_name in mapping.items():
        old_path = sprites_dir / f"{old_name}.png"
        new_path = sprites_dir / f"{new_name}.png"
        
        if old_path.exists() and not new_path.exists():
            shutil.move(old_path, new_path)
            print(f"Renamed: {old_name} -> {new_name}")
```

---

## Step 6: Update Sprite Registry

### Update `engine/sprites/sprite_registry.py`

Add mappings for enemy sprites:

```python
# In sprite_registry.py
ENTITY_SPRITE_MAP = {
    EntitySpriteType.PLAYER: "player",
    EntitySpriteType.ENEMY: "enemy_default",
    # Add enemy type mappings
    "goblin_skirmisher": "enemy_goblin",
    "goblin_brute": "enemy_goblin_brute",
    "goblin_shaman": "enemy_goblin_mage",
    "skeleton_archer": "enemy_skeleton_archer",
    "orc_raider": "enemy_orc",
    "ghoul_ripper": "enemy_ghoul",
    "lich": "enemy_lich",
    "banshee": "enemy_banshee",
    "dread_knight": "enemy_death_knight",
    # ... etc
}
```

### Update `engine/sprites/init_sprites.py`

Add common sprites to preload:

```python
sprite_manager.preload_sprites([
    (SpriteCategory.ENTITY, "player", None),
    (SpriteCategory.ENTITY, "enemy_goblin", None),
    (SpriteCategory.ENTITY, "enemy_orc", None),
    (SpriteCategory.ENTITY, "enemy_skeleton_archer", None),
    (SpriteCategory.TILE, "floor", None),
    (SpriteCategory.TILE, "wall", None),
    (SpriteCategory.TILE, "up_stairs", None),
    (SpriteCategory.TILE, "down_stairs", None),
    # Add more as needed
])
```

---

## Step 7: Update Entity Rendering

Ensure entities use sprites correctly. Check `world/entities.py` and ensure:
- Player entity uses `EntitySpriteType.PLAYER`
- Enemy entities use appropriate sprite IDs based on their archetype ID

---

## Step 8: Update Tile Rendering

Update `world/tiles.py` or tile rendering code to use sprite-based tiles instead of color-based.

---

## Step 9: Test Integration

1. **Run the game** and verify sprites load correctly
2. **Check entity sprites** - player, enemies should have sprites
3. **Check item sprites** - items in inventory should show sprites
4. **Check tile sprites** - floor/walls should use sprite tiles
5. **Verify performance** - ensure sprite loading doesn't cause lag

---

## Troubleshooting

### Sprites not showing
- Check file paths match sprite IDs
- Verify sprite files exist in correct directories
- Check sprite registry mappings
- Verify preload list includes needed sprites

### Wrong sprites showing
- Check sprite ID mappings in registry
- Verify enemy type to sprite ID mapping
- Check item ID to sprite ID mapping

### Performance issues
- Reduce preload list
- Check sprite cache settings
- Verify sprite files aren't too large

---

## Next Steps After Integration

1. **Add more sprite variants** - Different states (idle, attacking, etc.)
2. **Add animated tiles** - Use animated-tiles.png for torches, fires
3. **Add palette swaps** - Use items-palette-swaps.png for item variants
4. **Expand sprite usage** - Add sprites for NPCs, merchants, chests
5. **Optimize** - Consider sprite atlasing if performance becomes an issue

---

## File Reference

- Extraction script: `tools/extract_32rogues_sprites.py`
- Sprite registry: `engine/sprites/sprite_registry.py`
- Sprite initialization: `engine/sprites/init_sprites.py`
- Enemy definitions: `systems/enemies.py`
- Item definitions: `data/items.json`
- Tile definitions: `world/tiles.py`

---

## Sprite Sheet Reference

From the 32rogues pack metadata:

### rogues.png (7×7 grid)
- Row 1: Dwarf, Elf, Ranger, Rogue, Bandit
- Row 2: Knight variants
- Row 3: Monk, Priest, War Clerics
- Row 4: Barbarians
- Row 5: Wizards, Druid

### monsters.png (13×12 grid)
- Row 1: Orcs and Goblins
- Row 2: Giants (Ettin, Troll)
- Row 3: Slimes
- Row 4: Special enemies
- Row 5: Undead (Skeletons, Lich, Death Knight, Zombie, Ghoul)
- Row 6: Spirits (Banshee, Reaper)

### items.png (26×11 grid)
- Row 1: Swords (Dagger, Short Sword, Long Sword, etc.)
- Row 2: Wide Swords, Rapiers
- Row 3: Curved Swords (Scimitar, Kukri)
- Row 4: Axes
- Row 5: Hammers

### tiles.png (26×17 grid)
- Rows 1-6: Walls (various types)
- Rows 7-8: Floors (stone and grass variants)
- Row 9: Dirt ground

