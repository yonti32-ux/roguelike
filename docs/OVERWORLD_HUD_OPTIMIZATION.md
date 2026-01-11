# Overworld HUD Optimization Plan

## Problem

The overworld HUD is calling `pygame.draw.rect` **21,764,352 times** (21+ million calls) taking **8.04 seconds**.

**Location:** `ui/overworld/hud.py:21(draw_overworld)`

**Root Cause:**
- Drawing one rectangle per tile in the overworld viewport
- Large viewport = many tiles = many draw calls
- Example: 80x45 tiles = 3,600 tiles per frame
- At 60 FPS for 60 seconds: 3,600 × 60 × 60 = 12.96 million calls (close to the 21M we're seeing)

---

## Current Code

```python
# ui/overworld/hud.py lines 73-119
for y in range(start_y, end_y):
    for x in range(start_x, end_x):
        # ... calculate color based on distance, exploration, etc ...
        pygame.draw.rect(screen, color, rect)  # One call per tile!
```

**Issues:**
- Every tile gets its own `pygame.draw.rect` call
- Colors vary by distance (brightness), so we can't easily batch
- But many tiles have the same or similar colors

---

## Optimization Options

### Option 1: Surface.fill() for Same-Color Tiles (Recommended - Easiest)

Group tiles by color and use `surface.fill()` which is faster than many small rectangles.

**Pros:**
- Simple to implement
- Significant speedup for common cases
- No caching needed

**Cons:**
- Still some overhead for grouping
- Less effective if many unique colors

### Option 2: Pre-render Tile Surfaces (Best Performance)

Create small surfaces for each tile type/color at initialization, blit them.

**Pros:**
- Fastest option (blit is faster than draw.rect)
- Can cache by tile type + brightness
- Scales well

**Cons:**
- More complex implementation
- Memory overhead (cached surfaces)
- Need to handle brightness variations

### Option 3: Batch Rectangle Drawing

Use `pygame.draw.rects()` if available (some pygame versions), or collect rectangles by color.

**Pros:**
- Batch operations are faster
- Minimal code changes

**Cons:**
- `pygame.draw.rects()` may not be available in all pygame versions
- Grouping by color adds complexity

---

## Recommended Solution: Surface.fill() Grouping

**Approach:**
1. Group tiles by color (or color category)
2. For groups of same-color tiles, use `surface.fill()` on a region
3. For unique/rare colors, still use `pygame.draw.rect`

**Implementation Strategy:**
- Create a color-to-rectangles dictionary
- Group rectangles by exact color
- For large groups (>10 tiles), use `surface.fill()` on bounding box
- For small groups/singles, use `pygame.draw.rect`

**Expected Improvement:**
- Reduce draw calls by 70-90% (most tiles are same/similar colors)
- Should reduce time from 8s to 1-2s

---

## Implementation Priority

1. **Quick Win:** Group same-color tiles, use `surface.fill()` for groups
2. **Medium Term:** Pre-render common tile types to surfaces
3. **Long Term:** Full tile caching system

---

## Notes

- This is overworld-specific (different from dungeon/exploration mode)
- The overworld has fewer tile types, so grouping should be very effective
- Distance-based brightness creates color variations, but many tiles still share colors

