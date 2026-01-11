# Profile Analysis: Critical Bottlenecks Found

## Summary

Your profile revealed **three major bottlenecks** that are slowing down your game:

1. 🔴 **pygame.draw.rect: 7,032,226 calls (7.5s)** - Drawing way too many rectangles
2. 🔴 **Sprite file system checks: 2.5s** - Checking if sprite files exist repeatedly
3. 🟡 **HUD rendering: 5.9s** - Overworld HUD taking significant time

---

## Bottleneck #1: Excessive pygame.draw.rect Calls

### The Problem

**7,032,226 calls to `pygame.draw.rect`** taking 7.5 seconds!

This means you're drawing rectangles for every single tile, even ones that are:
- Off-screen
- Not visible (behind walls)
- Already drawn

### Why This Happens

Looking at `world/game_map.py:277(draw)`:
- The code loops through ALL tiles in the map
- Even with the screen clipping checks, it's still drawing way too many rectangles
- Each tile gets its own `pygame.draw.rect` call

### The Fix

**Option 1: Only draw visible tiles (Recommended)**

The code already has some clipping, but it needs improvement. Make sure you're only drawing tiles that are:
1. Within the camera view
2. Actually visible (not behind walls)

**Option 2: Batch rectangle drawing**

Instead of calling `pygame.draw.rect` for each tile, collect all rectangles and draw them in batches, or use `pygame.draw.rects` (if available in your pygame version).

**Option 3: Cache tile surfaces**

Pre-render common tiles (walls, floors) to surfaces and blit them instead of drawing rectangles every frame.

### Priority: **CRITICAL** 🔴

This is your biggest bottleneck. Fixing this could dramatically improve FPS.

---

## Bottleneck #2: Sprite File System Operations

### The Problem

File system operations taking **2.5 seconds**:
- `exists()` checks: 2.47s
- `stat()` calls: 2.49s, 2.46s
- `_get_sprite_path()`: 3.42s total

This means the sprite system is checking if files exist **repeatedly** instead of caching the results.

### Why This Happens

Looking at `engine/sprites/sprites.py:401(_get_sprite_path)`:
- Every time a sprite is requested, it checks if the file exists
- This file check involves disk I/O (slow!)
- No caching of "file exists" results

### The Fix

**Cache file existence checks:**

1. When the game starts, scan sprite directories once
2. Build a cache of which sprite files exist
3. Use the cache instead of checking the file system every time

**Example:**
```python
# At initialization
_sprite_file_cache = {}

def _get_sprite_path_cached(category, sprite_id):
    cache_key = (category, sprite_id)
    if cache_key not in _sprite_file_cache:
        # Check once, cache result
        path = _find_sprite_file(category, sprite_id)
        _sprite_file_cache[cache_key] = path
    return _sprite_file_cache[cache_key]
```

### Priority: **HIGH** 🔴

File I/O in the hot path is very expensive. Caching will eliminate this bottleneck.

---

## Bottleneck #3: HUD Rendering (Overworld)

### The Problem

`hud.py:21(draw_overworld)` taking **5.93 seconds** cumulative time.

This is less critical than the other two, but still significant.

### Potential Causes

- Rendering too much UI every frame
- Not caching UI elements
- Complex calculations in the render loop
- Drawing text/images repeatedly

### The Fix

**Profile the HUD function specifically:**
```bash
# Profile just the overworld HUD
python tools/profile_game.py --method cprofile --duration 30
# Then look at hud.py:21(draw_overworld) in detail
```

**Common optimizations:**
- Cache rendered text surfaces
- Only redraw when UI state changes
- Use dirty rectangles (only redraw changed areas)
- Simplify UI rendering logic

### Priority: **MEDIUM** 🟡

Optimize after fixing the first two bottlenecks.

---

## Action Plan

### Step 1: Fix pygame.draw.rect (Biggest Impact)

**Quick win: Improve tile drawing clipping**

1. Make sure you're only drawing tiles visible on screen
2. Check that screen bounds clipping is working correctly
3. Consider pre-rendering common tiles

**Expected improvement:** Could reduce draw time by 50-80%

### Step 2: Cache Sprite File Checks

**Quick win: Add file existence cache**

1. Build sprite file cache at initialization
2. Use cache instead of file system checks
3. Only check file system if sprite not in cache (missing sprite handling)

**Expected improvement:** Eliminates 2.5s of file I/O overhead

### Step 3: Optimize HUD (If Still Needed)

After fixing the first two, profile again to see if HUD is still a problem.

---

## Expected Results

After fixing bottlenecks #1 and #2:

**Current:** 
- pygame.draw.rect: 7.5s
- Sprite file checks: 2.5s
- Total overhead: ~10s

**After fixes:**
- pygame.draw.rect: 1-2s (with better clipping/caching)
- Sprite file checks: 0s (cached)
- Total improvement: ~8s reduction

This could translate to significant FPS improvement, especially if you're currently running at 30-40 FPS.

---

## Next Steps

1. **Fix pygame.draw.rect bottleneck first** (biggest impact)
2. **Add sprite file caching** (quick win, high impact)
3. **Profile again** to verify improvements
4. **Optimize HUD** if still needed after fixes

---

## How to Verify Fixes

After making changes:

```bash
# Profile again with the same duration
python tools/profile_game.py --method cprofile --duration 60
snakeviz profile_results.prof
```

Compare:
- Number of `pygame.draw.rect` calls (should be much lower)
- Time spent in sprite file operations (should be near zero)
- Overall frame time (should be lower)
- FPS (should be higher)

---

## Notes

- Don't try to fix everything at once
- Fix one bottleneck, profile again, verify improvement
- The pygame.draw.rect issue is the biggest win
- Sprite caching is a quick fix with high impact

