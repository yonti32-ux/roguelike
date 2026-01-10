# Rule System Explained - Simple vs Complex

## What You Have Now (Hardcoded)

### Current Approach: Code-Based Logic

Your generation logic is **hardcoded in Python files**. Here's what that means:

**Terrain Generation** (`world/overworld/generation.py`):
```python
# Lines 108-119 - Hardcoded percentages
if rand < 0.35:
    terrain = TERRAIN_GRASS
elif rand < 0.55:
    terrain = TERRAIN_PLAINS
elif rand < 0.70:
    terrain = TERRAIN_FOREST
# ... etc
```

**Floor Scaling** (`world/mapgen.py`):
```python
# Lines 89-112 - Hardcoded floor scaling rules
if floor_index == 1:
    scales = [0.9, 1.0, 1.1]
    weights = [0.3, 0.4, 0.3]
elif floor_index == 2:
    scales = [1.0, 1.1, 1.25]
# ... many more hardcoded conditions
```

**POI Placement** (`world/poi/placement.py`):
```python
# Lines 158-160 - Hardcoded constraint
if tile is None or tile == TERRAIN_WATER:
    continue  # Can't place POI on water

# Lines 170 - Hardcoded distance check
if distance < config.poi_min_distance:
    too_close = True
```

**Room Tagging** (`world/mapgen.py`):
```python
# Lines 176-242 - Hardcoded room tagging logic
start_room.tag = "start"
treasure_room.tag = "treasure"
if random.random() < 0.7:
    shop_room.tag = "shop"
# ... etc
```

### Problems with Current Approach:
1. **To change behavior, you must edit Python code**
2. **To add new terrain types, edit multiple places**
3. **To adjust percentages, find the right if/elif chain**
4. **Difficult to share configurations between worlds**
5. **Testing requires code changes**

---

## What the Rule System Does

The rule system **moves logic from code to configuration files**. Instead of:

```python
if rand < 0.35:
    terrain = TERRAIN_GRASS
```

You write:

```json
{
  "terrain_weights": { "grass": 0.35 }
}
```

Then the rule engine reads the config and applies it.

---

## Two Approaches Compared

### Approach 1: SIMPLE Configuration-Based (Recommended for You)

Instead of a complex rule engine, just make your existing code read from config files.

**Pros:**
- ✅ Simple to understand
- ✅ Easy to implement (just add config loading)
- ✅ No new systems to learn
- ✅ Direct mapping: config → behavior
- ✅ Fast to implement (few hours vs days)

**Cons:**
- ❌ Less flexible than full rule system
- ❌ Still need code changes for new generation methods
- ❌ Can't compose rules dynamically

**Example Implementation:**

```python
# config/generation_settings.json
{
  "terrain": {
    "initial_distribution": {
      "grass": 0.35,
      "plains": 0.20,
      "forest": 0.15,
      "mountain": 0.12,
      "desert": 0.10,
      "water": 0.08
    },
    "smoothing": {
      "iterations": 3,
      "neighbor_radius": 1,
      "conversion_threshold": 4,
      "conversion_chance": 0.6
    }
  },
  "poi": {
    "density": 0.1,
    "min_distance": 8,
    "terrain_blacklist": ["water"],
    "terrain_preferences": {
      "village": {"grass": 2.0, "plains": 1.5},
      "dungeon": {"forest": 1.5, "mountain": 1.2}
    }
  },
  "floor": {
    "size_scaling": {
      "1": {"scales": [0.9, 1.0, 1.1], "weights": [0.3, 0.4, 0.3]},
      "2": {"scales": [1.0, 1.1, 1.25], "weights": [0.3, 0.4, 0.3]},
      "3-4": {"scales": [1.1, 1.25, 1.5], "weights": [0.2, 0.5, 0.3]}
    },
    "room_count": {
      "base": 10,
      "min": 6,
      "max": 22,
      "density_factor": "sqrt(area_ratio)"
    },
    "room_size": {
      "min": 4,
      "max": 9
    }
  },
  "room_tags": {
    "start": {"room_index": 0},
    "treasure": {"method": "farthest_from_start"},
    "shop": {"chance": 0.7, "max_per_floor": 1},
    "lair": {"chance": 1.0, "max_per_floor": 1},
    "graveyard": {"chance": 0.8, "min_floor": 2},
    "sanctum": {"chance": 0.5, "min_floor": 3}
  }
}
```

**Code Changes (Simple):**

```python
# world/overworld/generation.py
def _generate_terrain(self) -> List[List[TerrainType]]:
    config = GenerationConfig.load()  # Load from JSON
    
    tiles = []
    for y in range(self.config.world_height):
        for x in range(self.config.world_width):
            rand = random.random()
            terrain = self._pick_terrain_from_config(rand, config.terrain.initial_distribution)
            tiles.append(terrain)
    
    # Use config values instead of hardcoded
    tiles = self._smooth_terrain(tiles, 
                                 iterations=config.terrain.smoothing.iterations,
                                 threshold=config.terrain.smoothing.conversion_threshold)
    return tiles

def _pick_terrain_from_config(self, rand: float, weights: dict) -> TerrainType:
    cumulative = 0.0
    for terrain_id, weight in weights.items():
        cumulative += weight
        if rand < cumulative:
            return get_terrain(terrain_id)
    return TERRAIN_GRASS  # fallback
```

**This is 90% easier and gives you 80% of the benefits!**

---

### Approach 2: COMPLEX Rule Engine (From the Plan)

A full rule engine where you write JSON that describes rules, conditions, and actions.

**Pros:**
- ✅ Maximum flexibility
- ✅ Can compose complex rules
- ✅ Can add new rule types without code changes
- ✅ Very powerful for advanced use cases
- ✅ Can share rule sets as "mods"

**Cons:**
- ❌ Complex to implement (days/weeks of work)
- ❌ Complex to understand (need to learn rule syntax)
- ❌ Overkill for most use cases
- ❌ Harder to debug ("why isn't my rule working?")
- ❌ Performance overhead (rule evaluation)
- ❌ More moving parts = more bugs

**When You'd Need This:**
- Creating a "rule marketplace" where users share rule sets
- Making the game completely data-driven (no code for generation)
- Supporting complex modding scenarios
- You want users to write custom generation algorithms in JSON

---

## My Recommendation: **START SIMPLE**

### Phase 1: Simple Config Files (1-2 days)

1. Create `config/generation_settings.json` with all your hardcoded values
2. Create `GenerationConfig` class to load/validate it
3. Update generation code to read from config instead of hardcoded values
4. Done! You can now change behavior by editing JSON

**Benefits:**
- ✅ No code changes needed to tweak percentages
- ✅ Easy to create preset configs ("small_world.json", "large_world.json")
- ✅ Clear and simple
- ✅ Fast to implement and test

### Phase 2: Add More Config Options (If Needed)

As you find more hardcoded values, add them to the config:
- Room tagging probabilities
- Terrain smoothing parameters
- POI placement preferences
- Floor scaling curves

### Phase 3: Advanced Rule Engine (Only If Needed)

Only build the complex rule engine if:
- You find yourself wanting to write "if X then Y else Z" in config
- You need to compose multiple rules dynamically
- You want users to create custom generation algorithms
- Simple config files aren't flexible enough

---

## Example: What Changes

### Before (Hardcoded):
```python
# To change terrain distribution, edit Python:
if rand < 0.35:
    terrain = TERRAIN_GRASS  # Change this percentage
elif rand < 0.55:
    terrain = TERRAIN_PLAINS
```

### After Simple Config:
```python
# Code reads from config:
config = GenerationConfig.load()
terrain = _pick_terrain(rand, config.terrain.initial_distribution)

# You change JSON instead:
{
  "terrain": {
    "initial_distribution": {
      "grass": 0.40,  // Just change this number!
      "plains": 0.25
    }
  }
}
```

### After Complex Rule Engine:
```json
// You write rules in JSON:
{
  "id": "terrain_distribution",
  "type": "generator",
  "conditions": {"when": "initial_terrain_generation"},
  "actions": {
    "method": "random_distribution",
    "parameters": {"terrain_weights": {"grass": 0.40}}
  }
}
```

**Simple config is 10x easier to understand and use!**

---

## When Each Approach Makes Sense

| Scenario | Simple Config | Complex Rules |
|----------|---------------|---------------|
| Change percentages/weights | ✅ Perfect | ❌ Overkill |
| Tweak generation parameters | ✅ Perfect | ❌ Overkill |
| Add new terrain type | ✅ Easy (add to config + code) | ✅ Easy (just config) |
| Create preset configs | ✅ Perfect | ✅ Also works |
| Dynamic rule composition | ❌ Need code changes | ✅ Possible |
| User-created generation algorithms | ❌ Not possible | ✅ Possible |
| "If terrain X, then do Y" logic | ❌ Need code | ✅ Rules can do this |
| Simple conditional behavior | ✅ Just code it | ✅ Overkill |

---

## Decision Matrix

**Choose Simple Config if:**
- ✅ You want to move hardcoded values to config files
- ✅ You want to easily tweak generation parameters
- ✅ You want preset configurations (small/large worlds, etc.)
- ✅ You have 1-2 days to implement
- ✅ You want something easy to understand and maintain

**Choose Complex Rule Engine if:**
- ✅ You need users to write custom generation logic
- ✅ You need dynamic rule composition
- ✅ You want a "rule marketplace" for sharing configs
- ✅ You have weeks to implement and test
- ✅ Simple config files aren't flexible enough

---

## My Recommendation for Your Project

**Start with Simple Config!**

1. You'll get most of the benefits immediately
2. Much faster to implement (hours vs days)
3. Easier to understand and maintain
4. If you later need the complex system, you can build it on top

The complex rule engine is like building a Formula 1 race car when you need a reliable sedan. It's cool and powerful, but probably unnecessary for your needs.

Would you like me to:
1. **Implement the simple config approach** (recommended)
2. **Show you exactly what code changes are needed**
3. **Create example config files** based on your current code
4. **Explain any part in more detail**

