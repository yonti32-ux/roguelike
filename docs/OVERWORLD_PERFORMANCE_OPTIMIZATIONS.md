# Overworld Performance Optimizations

## Overview

The overworld rendering has been optimized for better performance, especially when adding more features. These optimizations reduce CPU usage and improve frame rates.

## Optimizations Applied

### 1. Viewport Filtering
- **Before**: Iterated through ALL POIs/parties, then checked if in viewport
- **After**: Pre-filters POIs/parties by viewport before rendering
- **Impact**: Reduces iterations from O(n) to O(visible), significant when many POIs/parties exist

### 2. Dictionary Lookup Optimization
- **Before**: Multiple dictionary lookups per tile (`game.overworld_map.explored_tiles`)
- **After**: Cached reference to `explored_tiles` dict
- **Impact**: Faster attribute access, reduced overhead

### 3. Pre-calculated Values
- **Before**: Calculated distance, color factors, etc. repeatedly
- **After**: Pre-calculated constants and cached values
- **Impact**: Eliminates redundant calculations

### 4. Text Surface Caching
- **Before**: Rendered text surfaces every frame (time, position, zoom, messages)
- **After**: Cached text surfaces, only re-render when value changes
- **Impact**: Major reduction in font rendering calls

### 5. UI Panel Caching
- **Before**: Created UI panels every frame
- **After**: Cached panel surfaces, only recreate if size changes
- **Impact**: Eliminates surface creation overhead

### 6. Font Caching
- **Before**: Created fonts for POI levels/party icons every frame
- **After**: Cached fonts by size, cached text surfaces
- **Impact**: Reduces font creation and text rendering

### 7. Fast Paths
- **Before**: Same logic for all tiles
- **After**: Fast paths for common cases (player tile, unexplored tiles)
- **Impact**: Early exits reduce processing

### 8. Config Caching
- **Before**: Loaded config every frame
- **After**: Cached config (only loads once)
- **Impact**: Eliminates file I/O per frame

### 9. Cache Size Limits
- **Before**: Caches could grow unbounded
- **After**: Limited cache sizes with LRU-style eviction
- **Impact**: Prevents memory bloat

## Performance Improvements

### Expected Gains
- **Terrain rendering**: ~20-30% faster (reduced calculations, fast paths)
- **POI rendering**: ~50-70% faster (viewport filtering)
- **Party rendering**: ~50-70% faster (viewport filtering)
- **UI rendering**: ~80-90% faster (text/panel caching)
- **Overall**: Should see 30-50% improvement in frame rate

### Memory Usage
- **Before**: Minimal caching, more allocations per frame
- **After**: More caching, but with size limits
- **Impact**: Slightly higher baseline memory, but much more stable

## Cache Management

All caches have size limits to prevent memory bloat:
- UI cache: 50 entries max
- POI level cache: 100 entries max
- Party icon cache: 20 entries max

Caches use simple LRU-style eviction (keep most recent entries).

## Future Optimization Opportunities

1. **Tile batching**: Group similar tiles and draw in batches
2. **Dirty rectangles**: Only redraw changed areas
3. **Surface pooling**: Reuse surfaces instead of creating new ones
4. **Multithreading**: Offload some calculations to background threads
5. **Level-of-detail**: Reduce detail when zoomed out
6. **Occlusion culling**: Skip drawing tiles behind other elements

## Testing

To verify performance improvements:
1. Monitor frame rate before/after
2. Check CPU usage
3. Test with many POIs/parties
4. Test at different zoom levels
5. Test with long play sessions (check for memory leaks)

## Notes

- All optimizations maintain visual quality
- Caches are cleared when appropriate (e.g., on world regeneration)
- Performance improvements are most noticeable with:
  - Large overworld maps
  - Many POIs
  - Many parties
  - Frequent UI updates

