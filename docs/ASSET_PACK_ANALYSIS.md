# Asset Pack Analysis & Integration Plan

## Overview
Analyzed two asset packs for potential integration into the roguelike game:
1. **32rogues** - Comprehensive sprite sheet pack
2. **Tiny RPG Character Asset Pack v1.03** - Character animations pack

---

## 1. 32rogues Pack

### ✅ **Perfect Match for Current System**
- **Sprite Size**: All sprites are **32x32 pixels** (matches game's `TILE_SIZE = 32`)
- **Format**: PNG files organized as sprite sheets
- **License**: Commercial use allowed (with restrictions: no NFTs, blockchain, AI/ML projects)
- **Credit**: Not required but appreciated (by Seth Boyles, 2024)

### Contents Available:

#### **Character Sprites** (`rogues.png` - 224x224 = 7×7 grid of 32×32 sprites)
- Dwarf, Elf, Ranger, Rogue, Bandit
- Knight (multiple variants)
- Monk, Priest, War Clerics, Templar, Schema Monks
- Barbarians (male/female, winter variants)
- Wizards (male/female), Druid
- **Use Case**: Player character, NPCs, companions

#### **Monsters** (`monsters.png` - 384x416 = 12×13 grid of 32×32 sprites)
- **Orcs**: Orc, Orc Wizard, Orc Blademaster, Orc Warchief
- **Goblins**: Goblin, Goblin Archer, Goblin Mage, Goblin Brute
- **Giants**: Ettin, Two-headed Ettin, Troll
- **Slimes**: Small, Big, Slimebody variants
- **Undead**: Skeleton, Skeleton Archer, Lich, Death Knight, Zombie, Ghoul
- **Spirits**: Banshee, Reaper
- **Special**: Faceless Monk, Unholy Cardinal
- **Use Case**: Enemy entities for dungeons/overworld

#### **Items** (`items.png` - 352x832 = 11×26 grid of 32×32 sprites)
- **Swords**: Dagger, Short Sword, Long Sword, Bastard Sword, Zweihander
- **Magic Swords**: Sanguine Dagger, Magic Dagger, Crystal Sword, Evil Sword, Flame Sword
- **Rapiers**: Wide Short/Long Swords, Rapier variants, Flamberge, Great Sword
- **Curved**: Shotel, Scimitar variants, Kukri
- **Axes**: Hand Axe, Battle Axe, Halberd, Great Axe, Giant Axe, Hatchet, Woodcutter's Axe
- **Hammers**: Blacksmith's Hammer, Warhammers, Great Hammer
- **Use Case**: Item sprites for inventory/equipment system

#### **Tiles** (`tiles.png` - 544x832 = 17×26 grid of 32×32 sprites)
- **Walls**: Dirt, Rough Stone, Stone Brick, Igneous, Large Stone, Catacombs/Skull walls
- **Floors**: Stone floors (3 variants with/without backgrounds), Grass (3 variants)
- **Dirt**: Dirt ground tiles
- **Use Case**: Dungeon/tile rendering (replaces current color-based tiles)

#### **Animated Tiles** (`animated-tiles.png` - 352x384)
- Brazier (lit/unlit), Fire Pit, Torch, Lamp
- Fire effects (large and small)
- Water waves, Poison bubbles
- **Use Case**: Animated environmental effects, lighting

#### **Animals** (`animals.png` - 288x512)
- **Bears**: Grizzly, Black, Polar, Panda
- **Primates**: Chimpanzee, Gorilla, Orangutan, Aye-aye, Gibbon, Mandrill, Capuchin, Langur
- **Cats**: Cat, Bobcat, Cougar, Cheetah, Lynx
- **Use Case**: Wildlife for overworld, companions, or neutral entities

#### **Additional Files**:
- `autotiles.png` - Auto-tiling patterns for seamless walls/floors
- `items-palette-swaps.png` - Color variants of items (256×1376)
- `32rogues-palette.png` - Color palette reference

### Integration Notes:
- ✅ **Directly usable** - no resizing needed
- ✅ **Sprite sheet format** - can be used as-is or extracted into individual files
- ✅ **Text metadata files** - contain sprite descriptions/indexing info
- 📝 **Extraction needed** - Individual sprites can be extracted from sheets if needed

---

## 2. Tiny RPG Character Asset Pack v1.03

### ⚠️ **Requires Scaling**
- **Sprite Size**: **100×100 pixels** (needs scaling to 32×32)
- **Format**: Individual PNG files with animation sequences
- **Characters**: Soldier (human) and Orc

### Contents Available:

#### **Soldier Character** (`Characters(100x100)/Soldier/`)
- `Soldier-Idle.png` - **600×100** (6 frames of 100×100)
- `Soldier-Walk.png` - Walking animation frames
- `Soldier-Attack01.png`, `Attack02.png`, `Attack03.png` - Attack animations
- `Soldier-Hurt.png` - Hurt/damage animation
- `Soldier-Death.png` - Death animation
- `Soldier.png` - Base sprite
- Shadow sprites included
- Split effect sprites for attacks

#### **Orc Character** (`Characters(100x100)/Orc/`)
- `Orc-Idle.png` - **600×100** (6 frames of 100×100)
- `Orc-Walk.png` - Walking animation
- `Orc-Attack01.png`, `Attack02.png` - Attack animations
- `Orc-Hurt.png` - Hurt animation
- `Orc-Death.png` - Death animation
- `Orc.png` - Base sprite
- Shadow and split effect sprites

#### **Projectiles** (`Arrow(Projectile)/`)
- `Arrow01(32x32).png` - ✅ **Perfect size!** Already 32×32
- `Arrow01(100x100).png` - Larger version available

#### **Source Files**:
- `Aseprite file/Soldier.aseprite` - Source file for editing
- `Aseprite file/Orc.aseprite` - Source file for editing

### Integration Notes:
- ⚠️ **Scaling required** - 100×100 → 32×32 (downscale to ~32% size)
- ✅ **Animation sequences** - Ready-made animation frames
- ✅ **Arrow projectile** - Already 32×32, can use directly
- 📝 **High-quality source** - Aseprite files allow for re-exporting at correct size
- 💡 **Best for battle animations** - Since battle scene may support larger sprites

---

## Integration Recommendations

### **Immediate Priority (32rogues pack)**

1. **Extract and Organize Tiles** → `sprites/tile/`
   - Floor tiles (stone, grass variants)
   - Wall tiles (various types)
   - Stairs (can be added from autotiles or created)

2. **Extract Entity Sprites** → `sprites/entity/`
   - Player character options (rogue, knight, wizard, etc.)
   - Enemy monsters (goblins, orcs, skeletons, etc.)
   - Animals for overworld

3. **Extract Item Sprites** → `sprites/item/`
   - Weapons matching item IDs in `data/items.json`
   - Can map existing items to sprites

4. **Animated Effects** → `sprites/effect/` or `sprites/tile/`
   - Fire animations, torches, etc.
   - Can be used for environmental effects

### **Secondary Priority (Tiny RPG pack)**

1. **Scale Down Character Sprites** to 32×32
   - Use as alternative player/enemy sprites
   - Keep original 100×100 for potential battle scene expansion

2. **Use Arrow Projectile** → `sprites/battle/` or `sprites/effect/`
   - Already correct size, can use immediately

3. **Battle Animations** (if expanding battle scene)
   - Could use 100×100 versions for larger battle view
   - Or scale down for current system

### **Technical Integration Steps**

1. **Create extraction script** (if using sprite sheets)
   ```python
   # Extract individual 32×32 sprites from sprite sheets
   # Save to appropriate category folders
   ```

2. **Map sprites to game entities**
   - Update `engine/sprites/sprite_registry.py` to register new sprites
   - Map enemy types to monster sprites
   - Map item IDs to item sprites

3. **Update sprite manager configuration**
   - Add new sprites to preload list in `engine/sprites/init_sprites.py`

4. **Test integration**
   - Verify sprites load correctly
   - Check scaling/rendering quality
   - Ensure game still runs smoothly

---

## Asset Mapping Suggestions

### Player Character Options:
- `rogues.png` row 1: Dwarf, Elf, Ranger, **Rogue**, Bandit
- Row 2: **Knight**, Fighter variants
- Row 3: Monk, Priest, **War Cleric**
- Row 4: **Barbarian** variants
- Row 5: **Wizard**, Druid

### Enemy Mapping:
```
goblin → Goblin (from monsters.png)
orc → Orc (from monsters.png)
skeleton → Skeleton (from monsters.png)
zombie → Zombie (from monsters.png)
lich → Lich (from monsters.png)
troll → Troll (from monsters.png)
```

### Item Mapping:
- Map weapon names from `data/items.json` to corresponding sprites in `items.png`
- Use palette swaps for item variants/rarities

### Tile Mapping:
- `FLOOR_TILE` → Stone floor variants from `tiles.png`
- `WALL_TILE` → Stone brick wall from `tiles.png`
- Overworld → Grass tiles from `tiles.png`

---

## License Compliance

### 32rogues:
- ✅ **Commercial use allowed**
- ✅ **Modification allowed**
- ❌ **Cannot redistribute/resell the asset pack itself**
- ❌ **Cannot use with NFT/blockchain/AI/ML projects**
- 💡 **Credit appreciated but not required**

### Tiny RPG Character Asset Pack:
- ⚠️ **Need to check license file** (if exists in pack)
- 📝 **Verify usage rights before commercial release**

---

## Next Steps

1. ✅ **Analysis complete** - Both packs evaluated
2. 🔄 **Extract sprites from 32rogues sheets** - Create individual sprite files
3. 🔄 **Map sprites to game entities** - Update sprite registry
4. 🔄 **Scale Tiny RPG sprites** - Downscale to 32×32 or use for battle scene
5. 🔄 **Test in-game** - Verify rendering and performance
6. 🔄 **Update documentation** - Document sprite usage

---

## Summary

**32rogues pack is highly recommended for immediate use:**
- Perfect 32×32 pixel size
- Comprehensive coverage (characters, monsters, items, tiles)
- High quality, consistent art style
- Commercial license friendly
- Can be integrated with minimal work

**Tiny RPG pack has potential for specific use:**
- High-quality character animations
- Arrow projectile is ready to use (32×32)
- Character sprites need scaling but are high quality
- Good for battle scene if expanding sprite sizes

**Recommendation**: Start with 32rogues pack for core game assets, use Tiny RPG pack selectively (arrows, potential battle expansions).


