# Sprite System Optimization Plan

## Implemented Optimizations

### 1. Canonical Art Size = TILE_SIZE ✓
- **Standard**: All sprites are assumed to be `TILE_SIZE` (32px) in their original form
- **Default**: If no size is specified, sprites are loaded/used at canonical size
- **Benefit**: Consistent sprite sizing, easier asset management

### 2. Integer-Only Scaling ✓
- **Rule**: Only scale by whole number multiples (1x, 2x, 3x, etc.)
- **Implementation**: `_calculate_integer_scale()` rounds to nearest integer multiple
- **Behavior**: If non-integer scale requested (e.g., 50px), rounds to nearest (e.g., 64px = 2x)
- **Method**: Uses `pygame.transform.scale()` for integer scaling
- **Benefit**: Maintains pixel-perfect quality, no blurriness, no silent failures

### 3. convert_alpha() Caching ✓
- **Strategy**: Only call `convert_alpha()` once per unique sprite
- **Cache Key**: `(path, target_size, sprite_set_info)`
- **Storage**: `_raw_sprite_cache` stores converted sprites before final caching
- **Benefit**: `convert_alpha()` is expensive - this significantly improves performance

### 4. Sprite Size Validation ✓
- **Rule**: Validates sprite sizes on load
- **Warning**: Warns if sprite is not canonical size (32×32) or integer multiple
- **Message**: Clear warning with expected vs actual size
- **Benefit**: Catches asset creation errors early, prevents mysterious visual bugs

### 5. Tile Chunk Caching (Infrastructure Ready)
- **Plan**: Cache 16×16 tile chunks for faster rendering
- **Status**: Infrastructure in place, implementation pending
- **Method**: `get_tile_chunk()` placeholder ready
- **Future**: Will render entire chunks once and cache them

## Usage

### Loading Sprites at Canonical Size
```python
# Automatically uses TILE_SIZE (32px)
sprite = sprite_manager.get_sprite(SpriteCategory.ENTITY, "player")
```

### Scaling to Integer Multiples
```python
# 2x scale (64px) - allowed
sprite = sprite_manager.get_sprite(
    SpriteCategory.ENTITY, "player",
    size=(64, 64)  # 2x canonical size
)

# 3x scale (96px) - allowed
sprite = sprite_manager.get_sprite(
    SpriteCategory.ENTITY, "player",
    size=(96, 96)  # 3x canonical size
)

# Non-integer scale (50px) - rounds to nearest integer multiple (64px = 2x)
sprite = sprite_manager.get_sprite(
    SpriteCategory.ENTITY, "player",
    size=(50, 50)  # Will round to 64px (2x) - nearest integer multiple
)
```

### Performance Benefits

1. **convert_alpha() Caching**
   - First load: Loads file + converts alpha (~5-10ms)
   - Subsequent loads: Direct cache lookup (~0.01ms)
   - **Speedup**: ~500-1000x for cached sprites

2. **Integer Scaling**
   - Only scales when needed
   - Rounds to nearest integer multiple (no silent failures)
   - Caches scaled versions
   - Prevents unnecessary rescaling

3. **Size Validation**
   - Catches incorrect sprite sizes early
   - Clear warnings help debug asset issues
   - Prevents mysterious visual bugs

3. **Canonical Size**
   - Consistent sizing reduces cache misses
   - Easier to manage sprite assets
   - Better memory efficiency

## Future: Tile Chunk Caching

### When Implemented:
```python
# Render 16x16 tile chunk once
chunk = sprite_manager.get_tile_chunk(chunk_x=0, chunk_y=0, zoom_level=1)

# Subsequent access is instant (cached)
# Only needs to re-render when tiles in that chunk change
```

### Benefits:
- **Current**: Renders each tile individually every frame (~1000+ tiles)
- **With Chunks**: Render 16×16 chunks once, reuse (~40-60 chunks)
- **Speedup**: Potentially 10-20x faster tile rendering

## Asset Guidelines

### Sprite Creation
- Create all sprites at **32×32 pixels** (TILE_SIZE)
- Use transparent PNG format
- No need to create multiple sizes - scaling handles it

### Scaling Recommendations
- **1x** (32px): Default exploration view
- **2x** (64px): Battle scene, larger UI elements
- **3x** (96px): Close-up views, large entities
- **4x+** (128px+): UI icons, special effects

### Performance Tips
1. Keep sprites at canonical size (32px)
2. Let the system handle scaling
3. Use sprite sets for animations (more efficient)
4. Preload commonly used sprites at startup

## Cache Management

```python
# Clear all caches (useful for debugging or reloading)
sprite_manager.clear_cache()

# Clear only tile chunk cache (when map changes)
sprite_manager.clear_tile_chunk_cache()
```

## Implementation Status

- ✅ Canonical size enforcement
- ✅ Integer scaling with rounding
- ✅ Sprite size validation & warnings
- ✅ convert_alpha() caching
- ✅ Cache key optimization
- ⏳ Tile chunk rendering (infrastructure ready)
- ⏳ Chunk invalidation system
- ⏳ Map-aware chunk management

## Size Validation Examples

When loading a sprite with incorrect size:
```
WARNING: player.png is 30x30; expected 32x32 (or integer multiple like 64x64)
```

Valid sizes:
- ✅ 32×32 (1x canonical)
- ✅ 64×64 (2x canonical)
- ✅ 96×96 (3x canonical)
- ❌ 30×30 (invalid - will warn)
- ❌ 50×50 (invalid - will warn)

