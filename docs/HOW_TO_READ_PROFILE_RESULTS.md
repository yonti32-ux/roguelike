# How to Read Profile Results (snakeviz)

## What You're Looking At

You're viewing a **flame graph** (also called an "icicle graph"). This visualizes where your game spends time.

## Understanding the Visualization

### The Basics

- **Wide bars** = Functions taking MORE time (potential bottlenecks)
- **Narrow bars** = Functions taking LESS time
- **Height/Stack** = Call chain (what calls what, from bottom to top)
- **Colors** = Different functions (color coding for readability)

### Reading Left to Right

The graph is sorted by time:
- **Left side** = Functions taking the most total time
- **Right side** = Functions taking less time

### Reading Bottom to Top

- **Bottom** = Entry point (main loop, event handlers)
- **Top** = Leaf functions (actual work being done)
- **Middle** = Call chain (function A calls function B calls function C...)

## What to Look For

### 1. Wide Bars = Bottlenecks

**Look for the widest bars** - these are your biggest time consumers.

Examples:
- If `game_map.draw()` has a very wide bar → drawing is slow
- If `entity.update()` has a wide bar → entity updates are slow
- If `fov_calculation()` has a wide bar → FOV is slow

### 2. Functions You Didn't Expect

**Look for functions you're surprised to see:**
- JSON parsing in the hot path? → Maybe loading data every frame?
- String operations? → Maybe doing expensive string work?
- File I/O? → Definitely shouldn't be in the game loop!

### 3. Deep Stacks = Long Call Chains

**Tall stacks** might indicate:
- Many function calls (could be optimized)
- Deep recursion (check for infinite recursion)
- Complex logic (might benefit from simplification)

### 4. Functions Called Many Times

Even if a function is fast, if it's called thousands of times, it can add up.

## How to Navigate snakeviz

### Clicking on Bars

1. **Click a bar** → Zooms in to show just that function and its callers/callees
2. **Click again** → Zooms in further or goes back
3. **Click "Reset Zoom"** → Returns to full view

### The Stats Panel

Look at the top/left of the page for:
- **Total time** - Total time spent in this function (including subcalls)
- **Self time** - Time spent in this function itself (excluding subcalls)
- **Number of calls** - How many times this function was called

### Views

snakeviz has different views:
- **Icicle** (default) - Bars going downward
- **Sunburst** - Circular view (alternative visualization)

Try clicking around to see which view you prefer!

## Interpreting the Numbers

### Time Values

- Times are usually in **seconds** or **milliseconds**
- Look at the scale at the bottom of the graph
- Example: If a bar spans 0.5 seconds and you profiled for 60 seconds, that function took 0.5/60 = 0.83% of total time

### Percentage

- Percentages show what portion of total time
- 50% = Half the total time was spent here
- 10% = One-tenth of the total time

### Call Counts

- High call counts with low time = Function is fast but called often
- Low call counts with high time = Function is slow but called rarely

## What's a Problem?

### Red Flags 🔴

1. **Any function > 5ms per frame** (at 60 FPS = 16.67ms per frame total)
   - If a function takes 10ms, that's 60% of your frame budget!

2. **Unexpected functions in the top list:**
   - File I/O (reading files)
   - JSON parsing
   - Network operations
   - String formatting in hot loops

3. **Functions called thousands of times per frame:**
   - Even fast functions add up if called too often

### Green Flags ✅

1. **Expected functions taking time:**
   - `draw()` functions (drawing is expected to take time)
   - `update()` functions (game logic)
   - Pygame operations (rendering)

2. **Reasonable time distribution:**
   - No single function dominating (>50% of time)
   - Time spread across multiple functions

3. **Fast leaf functions:**
   - Functions at the top of stacks are fast (good!)
   - Time is in expected places (drawing, game logic)

## Example: What You Might See

### Good Profile (Well-Optimized)

```
Top functions:
1. pygame.draw operations    30%  ← Expected (drawing)
2. game.update()             25%  ← Expected (game logic)
3. entity.update()           15%  ← Expected (entity logic)
4. input handling            10%  ← Expected (input)
5. Other                     20%  ← Spread out
```

**Interpretation:** Time is spread reasonably, no single bottleneck.

### Problematic Profile (Needs Optimization)

```
Top functions:
1. fov_calculation()         60%  ← 🔴 PROBLEM! Too much time
2. pygame.draw operations    15%
3. game.update()             10%
4. Other                     15%
```

**Interpretation:** FOV calculation is the bottleneck. Optimize this first!

### Another Problem Profile

```
Top functions:
1. json.loads()              40%  ← 🔴 PROBLEM! Why JSON parsing?
2. game_map.draw()           30%
3. Other                     30%
```

**Interpretation:** JSON parsing in the hot path - probably loading data every frame. Move to initialization!

## Next Steps

### 1. Identify Your Bottleneck

Look at your flame graph and find:
- The widest bar (biggest time consumer)
- Any unexpected functions
- Functions taking > 5ms per frame

### 2. Check if It's Actually a Problem

- Is your FPS good? (60 FPS = good, <30 FPS = problem)
- Is the bottleneck in expected code? (drawing, game logic)
- Is it something that can be optimized?

### 3. If It's a Problem, Optimize

See `docs/PERFORMANCE_PROFILING.md` for optimization strategies:
- Caching
- Reducing calls
- Better algorithms
- Spatial indexing

### 4. Profile Again

After optimizing:
- Profile again to verify improvement
- Compare before/after
- Check if new bottlenecks appeared

## Tips

1. **Profile different scenarios separately:**
   - Profile exploration mode
   - Profile battle mode
   - Profile UI screens
   - Each might have different bottlenecks

2. **Profile for sufficient time:**
   - At least 30-60 seconds
   - Let the game "settle" into normal gameplay
   - Avoid profiling startup/loading

3. **Compare multiple profiles:**
   - Profile before optimization
   - Profile after optimization
   - Compare to see improvement

4. **Don't over-optimize:**
   - If FPS is good (60 FPS), don't optimize
   - Focus on actual problems
   - Premature optimization is the root of all evil

## Summary

1. **Wide bars** = Most time spent (potential bottlenecks)
2. **Click bars** = Zoom in to see details
3. **Look for** = Unexpected functions, functions > 5ms, high call counts
4. **Check** = Is your FPS good? Is this a real problem?
5. **Optimize** = Focus on the biggest bottlenecks first
6. **Verify** = Profile again to confirm improvement

Your flame graph is showing you exactly where your game spends time. Use it to find bottlenecks and optimize!

