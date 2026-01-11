# Performance Profiling Guide

This guide explains how to profile your game to identify performance bottlenecks.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Profiling Methods](#profiling-methods)
3. [Identifying Bottlenecks](#identifying-bottlenecks)
4. [Common Performance Issues](#common-performance-issues)
5. [Optimization Strategies](#optimization-strategies)
6. [Tools and Scripts](#tools-and-scripts)

---

## Quick Start

### 1. Basic Profiling (cProfile)

**Easiest method - uses built-in Python profiler:**

```bash
# Profile for 30 seconds while playing
python tools/profile_game.py --method cprofile --duration 30

# Analyze results
python tools/profile_game.py --method analyze --analyze-file profile_results.prof
```

**View in browser (recommended):**
```bash
snakeviz profile_results.prof
# Opens interactive visualization in browser
```

### 2. Sampling Profiler (py-spy)

**No code changes needed, minimal overhead:**

```bash
# Record from start
py-spy record -o profile_pyspy.svg --duration 60 -- python main.py

# Or attach to running game
py-spy record -o profile_pyspy.svg --duration 60 --pid <process_id>
```

View the SVG file in a web browser for a flame graph.

### 3. Quick FPS Check

The game already tracks FPS. Check the debug console or telemetry logs.

---

## Profiling Methods

### Method 1: cProfile (Recommended for Start)

**Pros:**
- Built into Python (no extra setup)
- Detailed function-level statistics
- Can profile specific code sections
- Good for finding hot functions

**Cons:**
- Adds overhead (may affect timing)
- Doesn't show line-by-line details

**Usage:**
```bash
python tools/profile_game.py --method cprofile --duration 60
snakeviz profile_results.prof
```

**What to look for:**
- Functions with high `cumulative` time (total time including subcalls)
- Functions with high `tottime` (time in function itself)
- Functions called many times (`ncalls`)

### Method 2: py-spy (Recommended for Ongoing Profiling)

**Pros:**
- Minimal overhead (sampling)
- No code changes needed
- Visual flame graphs
- Can attach to running process

**Cons:**
- Less detailed than cProfile
- Statistical sampling (may miss brief spikes)

**Usage:**
```bash
# Start game
python main.py

# In another terminal, profile it
py-spy record -o profile.svg --duration 60 --pid $(pgrep -f "python main.py")

# Or record from start
py-spy record -o profile.svg --duration 60 -- python main.py
```

**What to look for:**
- Wide bars in flame graph = functions taking most time
- Tall stacks = deep call chains (may indicate optimization opportunities)

### Method 3: Memory Profiling

**For memory leaks and high memory usage:**

```python
# Add to function you want to profile
from memory_profiler import profile

@profile
def my_function():
    # ... code ...
    pass
```

```bash
python -m memory_profiler your_script.py
```

### Method 4: Manual Timing

**For quick checks of specific code:**

```python
import time

start = time.perf_counter()
# ... code to time ...
elapsed = time.perf_counter() - start
print(f"Took {elapsed*1000:.2f}ms")
```

---

## Identifying Bottlenecks

### Step 1: Establish Baseline

**Before profiling, know your target:**
- Target FPS: 60 FPS = 16.67ms per frame
- Acceptable FPS: 30 FPS = 33.33ms per frame

**Check current performance:**
```python
# In game loop
fps = clock.get_fps()
print(f"FPS: {fps:.1f}")
```

### Step 2: Profile During Typical Gameplay

**Profile scenarios that matter:**
- ✅ Exploration mode (most common)
- ✅ Battle mode (action-heavy)
- ✅ Overworld (if applicable)
- ✅ UI screens (inventory, character sheet)
- ✅ Floor generation (if slow)

**Don't profile:**
- ❌ Menu screens (usually not performance-critical)
- ❌ Loading screens (one-time cost)

### Step 3: Analyze Results

#### Using cProfile + snakeviz

1. Run profiler while playing
2. Open results in snakeviz: `snakeviz profile_results.prof`
3. Look for:
   - **Wide rectangles** = functions taking most time
   - **Deep stacks** = call chains that might be optimized
   - **Hot paths** = code executed most frequently

#### Using pstats (command-line)

```bash
python -m pstats profile_results.prof
```

In pstats:
```
sort cumulative    # Sort by total time (including subcalls)
stats 50           # Show top 50 functions
```

**Key metrics:**
- `cumulative`: Total time (function + all subcalls) - most important
- `tottime`: Time in function itself (excluding subcalls)
- `ncalls`: Number of calls
- `percall`: Time per call

### Step 4: Identify Hot Spots

**Red flags:**
- 🔴 Function taking > 5ms per frame (at 60 FPS target)
- 🔴 Function called hundreds of times per frame
- 🔴 Deep call stacks (many function calls)
- 🔴 Unexpected functions in top list (e.g., JSON parsing every frame)

---

## Common Performance Issues

### 1. Drawing/Rendering

**Symptoms:**
- FPS drops when many entities visible
- FPS fine in empty areas

**Common causes:**
- Drawing too many surfaces
- Not using dirty rectangles
- Redrawing entire screen every frame
- High-resolution sprites without caching

**How to check:**
```python
import time
start = time.perf_counter()
game.draw()
elapsed = time.perf_counter() - start
print(f"Draw took {elapsed*1000:.2f}ms")
```

**Fixes:**
- Only draw visible entities
- Cache rendered surfaces
- Use sprite groups efficiently
- Reduce overdraw

### 2. Update Logic

**Symptoms:**
- FPS drops regardless of visual complexity
- Slow even with few entities

**Common causes:**
- Expensive calculations every frame
- Inefficient algorithms (O(n²) loops)
- Unnecessary work (recalculating constants)
- Poor data structures

**How to check:**
```python
import time
start = time.perf_counter()
game.update(dt)
elapsed = time.perf_counter() - start
print(f"Update took {elapsed*1000:.2f}ms")
```

**Fixes:**
- Cache expensive calculations
- Use spatial indexes for collision
- Only update what changed
- Optimize hot loops

### 3. Pathfinding/AI

**Symptoms:**
- FPS drops with many enemies
- Lag when enemies move

**Common causes:**
- Pathfinding every frame
- No path caching
- Inefficient pathfinding algorithm
- Too many AI entities updating

**Fixes:**
- Cache paths
- Update AI less frequently
- Limit concurrent pathfinding
- Use simpler AI when far from player

### 4. FOV Calculations

**Symptoms:**
- FPS drops when moving
- Slow when entering new areas

**Common causes:**
- Recalculating FOV every frame
- Expensive FOV algorithm
- Large FOV radius

**Fixes:**
- Only recalculate FOV when needed
- Cache FOV results
- Reduce FOV radius if possible
- Use simpler FOV algorithm

### 5. Memory Allocation

**Symptoms:**
- Gradual FPS decrease over time
- High memory usage
- Garbage collection stutters

**Common causes:**
- Creating new objects every frame
- Not reusing objects
- Memory leaks
- Large temporary allocations

**How to check:**
```bash
# Monitor memory
python -m memory_profiler your_script.py
```

**Fixes:**
- Object pooling
- Reuse lists/dicts
- Avoid allocations in hot loops
- Fix memory leaks

---

## Optimization Strategies

### 1. Profile First, Optimize Second

**Don't guess!** Profile to find actual bottlenecks before optimizing.

### 2. The 80/20 Rule

**Optimize the hot 20% of code that takes 80% of time.**

After profiling, focus on:
1. Functions taking most cumulative time
2. Functions called most frequently
3. Functions with highest per-call time

### 3. Optimization Techniques

#### Caching

```python
# Bad: Recalculates every time
def get_expensive_value():
    return complex_calculation()

# Good: Cache result
_cache = None
def get_expensive_value():
    global _cache
    if _cache is None:
        _cache = complex_calculation()
    return _cache
```

#### Early Exit

```python
# Bad: Always processes all items
def process_items(items):
    for item in items:
        expensive_operation(item)

# Good: Exit early when possible
def process_items(items):
    for item in items:
        if should_skip(item):
            continue
        expensive_operation(item)
```

#### Spatial Indexing

```python
# Bad: Check all entities
def find_nearby_entities(pos, radius):
    nearby = []
    for entity in all_entities:
        if distance(pos, entity.pos) < radius:
            nearby.append(entity)
    return nearby

# Good: Use spatial index (grid, quadtree, etc.)
def find_nearby_entities(pos, radius):
    grid_cells = get_grid_cells_in_radius(pos, radius)
    nearby = []
    for cell in grid_cells:
        nearby.extend(cell.entities)
    return nearby
```

#### Batch Operations

```python
# Bad: One operation per entity
for entity in entities:
    entity.update()

# Good: Batch similar operations
positions = [e.pos for e in entities]
velocities = [e.velocity for e in entities]
# ... batch process ...
```

### 4. Measure Impact

**After optimizing:**
1. Profile again
2. Compare before/after
3. Verify improvement
4. Check for regressions

---

## Tools and Scripts

### Included Scripts

**`tools/profile_game.py`**
- Wrapper script for profiling
- Supports multiple profiling methods
- Analysis tools

**Usage:**
```bash
# Profile with cProfile
python tools/profile_game.py --method cprofile --duration 60

# Analyze results
python tools/profile_game.py --method analyze --analyze-file profile_results.prof

# View in snakeviz
snakeviz profile_results.prof
```

### External Tools

**snakeviz** (installed with requirements)
- Visual browser for cProfile results
- Interactive flame graphs
- Easy to identify hot spots

**py-spy** (installed with requirements)
- Sampling profiler
- Minimal overhead
- Visual flame graphs

**memory_profiler** (installed with requirements)
- Memory usage profiling
- Line-by-line memory tracking

---

## Profiling Checklist

### Before Profiling
- [ ] Establish performance baseline (target FPS)
- [ ] Decide what to profile (exploration, battle, etc.)
- [ ] Close unnecessary applications
- [ ] Use consistent hardware/conditions

### During Profiling
- [ ] Play normally (don't artificially slow down)
- [ ] Test typical scenarios
- [ ] Profile for sufficient duration (30-60 seconds)
- [ ] Note any unusual behavior

### After Profiling
- [ ] Analyze results (identify top functions)
- [ ] Look for unexpected hot spots
- [ ] Compare different scenarios
- [ ] Document findings

### Before Optimizing
- [ ] Verify bottleneck is real (not profiling artifact)
- [ ] Understand why it's slow
- [ ] Plan optimization strategy
- [ ] Consider trade-offs (readability, maintainability)

### After Optimizing
- [ ] Profile again to measure improvement
- [ ] Test for regressions
- [ ] Verify fix doesn't break functionality
- [ ] Document changes

---

## Example Workflow

### Scenario: Game runs at 45 FPS, want 60 FPS

1. **Establish baseline:**
   ```python
   # Check FPS
   print(f"Current FPS: {clock.get_fps()}")
   # Output: ~45 FPS
   ```

2. **Profile:**
   ```bash
   python tools/profile_game.py --method cprofile --duration 60
   # Play game normally for 60 seconds
   ```

3. **Analyze:**
   ```bash
   snakeviz profile_results.prof
   # Or command-line:
   python tools/profile_game.py --method analyze
   ```

4. **Identify bottleneck:**
   ```
   Top functions by cumulative time:
   - game_map.draw()        35%  (11.5ms per frame)
   - entity.update()         20%  (6.5ms per frame)
   - fov_calculation()       15%  (5.0ms per frame)
   ```

5. **Optimize:**
   - Focus on `game_map.draw()` (biggest impact)
   - Only draw visible tiles
   - Cache tile surfaces
   - Reduce overdraw

6. **Verify:**
   ```bash
   # Profile again
   python tools/profile_game.py --method cprofile --duration 60
   # Check FPS improved
   print(f"New FPS: {clock.get_fps()}")
   # Should be closer to 60 FPS
   ```

---

## Tips

1. **Profile realistic scenarios** - Don't profile empty maps or idle states
2. **Profile multiple times** - Results can vary, get averages
3. **Profile different scenarios** - Exploration vs battle may have different bottlenecks
4. **Don't over-optimize** - 60 FPS is enough, don't optimize beyond what's needed
5. **Measure before/after** - Always verify optimizations help
6. **Consider readability** - Sometimes slight performance loss is worth cleaner code

---

## Resources

- **snakeviz documentation**: https://jiffyclub.github.io/snakeviz/
- **py-spy documentation**: https://github.com/benfred/py-spy
- **Python profiling guide**: https://docs.python.org/3/library/profile.html
- **Game optimization techniques**: Various game development blogs and books

---

## Next Steps

1. Run a baseline profile to see current performance
2. Identify top bottlenecks
3. Optimize one bottleneck at a time
4. Measure improvement after each change
5. Repeat until performance targets are met

