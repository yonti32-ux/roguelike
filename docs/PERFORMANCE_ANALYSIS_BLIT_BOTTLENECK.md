# Performance Analysis: Blit Bottleneck

## Current Situation

After optimizing rectangle drawing, we now have a new bottleneck:

### Before Optimization
- `pygame.draw.rect`: 21,764,352 calls (8.04s)
- One rectangle per tile

### After Surface Caching
- `surface.blit`: 43,894,220 calls (16.59s) ❌
- One blit per tile (using cached surfaces)

**Result:** Actually slower! More calls and more time.

---

## Why This Happened

The surface caching approach:
- ✅ Eliminated `pygame.draw.rect` calls
- ❌ Replaced them with `surface.blit` calls (one per tile)
- ❌ Blitting many small surfaces is actually slower than drawing rectangles!

**The problem:** We're still doing one operation per tile. Just changed from `draw.rect` to `blit`, but the number of operations is the same (or more).

---

## Root Cause

The fundamental issue is: **We're rendering too many individual tiles.**

With a large viewport:
- 80x45 tiles = 3,600 tiles per frame
- At 60 FPS for 60 seconds: 3,600 × 60 × 60 = 12.96 million operations
- But we're seeing 43+ million, so something is being called more frequently

**The real solution:** Reduce the number of individual rendering operations, not just change the operation type.

---

## Better Solutions

### Option 1: Render to Intermediate Surface (Recommended)

Instead of blitting each tile directly to the screen:
1. Create a temporary surface for the visible area
2. Blit all tiles to this surface
3. Blit the entire surface to screen once

**Pros:**
- Only one final blit to screen
- Intermediate surface operations are faster
- Can use dirty rectangles for updates

**Cons:**
- Extra memory for temporary surface
- Still need to render all tiles

### Option 2: Chunk-Based Rendering

Group tiles into chunks (e.g., 16x16 tiles per chunk):
1. Render chunks to surfaces
2. Cache chunk surfaces
3. Only re-render chunks when they change
4. Blit chunks instead of individual tiles

**Pros:**
- Fewer blit operations (chunks instead of tiles)
- Can cache unchanged chunks
- Scales well for large maps

**Cons:**
- More complex implementation
- Memory overhead for cached chunks
- Need to handle chunk invalidation

### Option 3: Go Back to draw.rect with Better Optimization

Since `draw.rect` was actually faster (8s vs 16s), maybe we should optimize that instead:
1. Use `pygame.draw.rects()` if available (batch drawing)
2. Or accept that rectangles are fast enough
3. Focus on reducing viewport size or tile count

**Pros:**
- Simpler code
- draw.rect was already faster

**Cons:**
- Still many draw calls
- Not ideal long-term

### Option 4: Reduce Viewport Size

Limit the maximum number of tiles visible:
- Cap viewport to reasonable size (e.g., 60x40 tiles max)
- Or reduce tile size further
- Or increase zoom minimum

**Pros:**
- Simple fix
- Fewer tiles = fewer operations

**Cons:**
- Affects gameplay (smaller visible area)
- Not a code optimization, just a gameplay change

---

## Recommendation

**Short term:** Revert to `draw.rect` (it was faster!)

**Medium term:** Implement chunk-based rendering for better performance

**Long term:** Consider using a different rendering approach (e.g., render to texture, use GPU if available)

---

## Immediate Action

The surface caching actually made things slower. We should revert to the rectangle drawing approach, but with the optimizations we made (caching colors, etc.).

Or, accept that drawing many rectangles is necessary for the overworld view, and focus optimization efforts elsewhere.

