# How to Profile Your Game - Step by Step

## Quick Start: Profile Your Game in 3 Steps

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs the profiling tools (py-spy, snakeviz, memory-profiler).

---

### Step 2: Profile While Playing

**Option A: Using cProfile (Recommended - Easiest)**

```bash
# Profile for 60 seconds while playing
python tools/profile_game.py --method cprofile --duration 60
```

**What happens:**
1. The script starts your game
2. You play normally for 60 seconds (or until you close the game)
3. Profile data is saved to `profile_results.prof`

**Option B: Using py-spy (Minimal Overhead)**

If you want to profile the actual game (not the test game from the script):

```bash
# Terminal 1: Start your game normally
python main.py

# Terminal 2: Profile the running game (after 10-20 seconds of gameplay)
py-spy record -o profile.svg --duration 60 --pid $(pgrep -f "python main.py")
```

Or profile from start:
```bash
py-spy record -o profile.svg --duration 60 -- python main.py
```

---

### Step 3: View Results

**For cProfile results:**

```bash
snakeviz profile_results.prof
```

This opens your browser with an interactive visualization showing:
- **Wide bars** = functions taking most time
- **Tall stacks** = deep call chains
- **Click bars** to zoom in and see callers/callees

**For py-spy results:**

Just open `profile.svg` in your web browser - it's a flame graph showing the same information.

---

## What to Do While Profiling

### Play Normally!

**Do:**
- ✅ Play the game as you normally would
- ✅ Move around, fight enemies, use inventory, etc.
- ✅ Test the scenarios you're concerned about (e.g., if battles are slow, do battles)
- ✅ Play for the full duration (or at least 30-60 seconds)

**Don't:**
- ❌ Sit idle (profile won't show useful data)
- ❌ Just sit in menus (menus usually aren't performance-critical)
- ❌ Try to "help" the profiler (play normally)

### What Scenarios to Test

**If you want to find bottlenecks in:**
- **Exploration**: Walk around, move through floors
- **Battles**: Start and fight battles
- **UI**: Open/close inventory, character sheet, etc.
- **Overworld**: Move around the overworld map
- **Floor generation**: Go up/down stairs to generate new floors

---

## Understanding the Results

### Using snakeviz (cProfile Results)

When you run `snakeviz profile_results.prof`, you'll see:

1. **Flame Graph View** (default):
   - **Width of bars** = how much time spent in that function
   - **Height/Stack** = call chain (what calls what)
   - **Click a bar** to see details and zoom in

2. **What to Look For:**
   - 🔴 **Very wide bars** = functions taking most time (potential bottlenecks)
   - 🔴 **Functions you didn't expect** = surprising hot spots
   - 🔴 **Functions called many times** = might benefit from optimization

3. **Top Functions:**
   - Look at the top of the graph (widest bars)
   - These are your biggest time consumers
   - Focus optimization efforts here

### Using py-spy SVG (Flame Graph)

Similar to snakeviz:
- **Wide bars** = time spent
- **Tall stacks** = call depth
- **Read from bottom to top** = call chain

---

## Example: What You Might See

After profiling, you might see something like:

```
Top time consumers:
1. game_map.draw()        35% of time  ← Potential bottleneck!
2. entity.update()        20% of time
3. fov_calculation()      15% of time
4. pygame.draw operations 10% of time
5. pathfinding            5%  of time
```

**Interpretation:**
- `game_map.draw()` takes 35% of time - this is your biggest bottleneck
- Focus optimization here first
- If you fix this, you might get significant FPS improvement

---

## Next Steps After Profiling

1. **Identify the bottleneck** (widest bar in flame graph)

2. **Check if it's a problem:**
   - Is your game running at good FPS? (60 FPS = 16.67ms per frame)
   - If a function takes > 5ms per frame, it might be worth optimizing
   - If game runs fine, maybe don't optimize (premature optimization)

3. **Optimize the bottleneck:**
   - See `docs/PERFORMANCE_PROFILING.md` for optimization strategies
   - Common fixes: caching, reducing calls, better algorithms

4. **Profile again:**
   - After optimizing, profile again to verify improvement
   - Compare before/after

---

## Quick Reference

### Profile with cProfile (Easiest)
```bash
python tools/profile_game.py --method cprofile --duration 60
snakeviz profile_results.prof
```

### Profile with py-spy (Minimal Overhead)
```bash
py-spy record -o profile.svg --duration 60 -- python main.py
# Open profile.svg in browser
```

### Analyze Existing Profile
```bash
python tools/profile_game.py --method analyze --analyze-file profile_results.prof
```

### Quick Timing in Code
```python
from tools.quick_profile import profile_function, time_block

@profile_function
def my_function():
    pass  # Will print timing when called

with time_block("operation"):
    pass  # Will print timing for this block
```

---

## Troubleshooting

### "No module named 'snakeviz'"
```bash
pip install -r requirements.txt
```

### "Profile script doesn't work"
The script creates a test game. For full profiling, use py-spy on your actual game:
```bash
py-spy record -o profile.svg --duration 60 -- python main.py
```

### "Results don't make sense"
- Make sure you played the game actively (not idle)
- Profile for at least 30-60 seconds
- Try profiling different scenarios separately

### "Game runs fine, should I profile?"
- If performance is good, you might not need to optimize
- Profile when you notice slowdowns or want to optimize
- It's good to have a baseline profile for future reference

---

## Summary

1. **Install**: `pip install -r requirements.txt`
2. **Profile**: `python tools/profile_game.py --method cprofile --duration 60`
3. **Play**: Play normally for 60 seconds
4. **View**: `snakeviz profile_results.prof`
5. **Analyze**: Look for wide bars (bottlenecks)
6. **Optimize**: Fix the biggest bottlenecks
7. **Repeat**: Profile again to verify improvement

That's it! The profiler will show you exactly where your game is spending time.

