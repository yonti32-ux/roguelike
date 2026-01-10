# POI System Extensibility Analysis

## Current Status: **Partially Extensible**

The POI system can be expanded with new types, but requires code changes in multiple files. A registry pattern would make it truly extensible.

## What Works Well ✅

1. **Configuration-Driven Placement**: POI distribution, placement order, and spatial rules are all config-based
2. **Class Inheritance**: New POI types can inherit from `PointOfInterest` base class
3. **Dynamic Distribution**: Distribution ratios read from config files
4. **Spatial Rules Structure**: The config format supports arbitrary spatial rules

## What Needs Refactoring ❌

### 1. POI Creation (`world/poi/placement.py`)

**Current (Hardcoded):**
```python
def _create_poi(poi_type: str, ...) -> PointOfInterest:
    if poi_type == "dungeon":
        return DungeonPOI(...)
    elif poi_type == "village":
        return VillagePOI(...)
    # ... more elif branches
```

**Should be:**
- Registry pattern mapping `poi_type` → factory function
- Each POI class registers itself

### 2. Spatial Rules Evaluation (`world/poi/placement.py`)

**Current (Hardcoded):**
```python
if poi_type == "village":
    # Village-specific logic
elif poi_type == "dungeon":
    # Dungeon-specific logic
```

**Should be:**
- Generic rule evaluation engine
- Rules defined in config, evaluated generically
- Or: Each POI class provides its own evaluation method

### 3. Save/Load System (`engine/utils/save_system.py`)

**Current (Hardcoded):**
```python
if poi_type == "dungeon":
    poi = DungeonPOI(...)
elif poi_type == "village":
    poi = VillagePOI(...)
```

**Should be:**
- Use the same registry/factory pattern
- Or: POI classes handle their own serialization

### 4. UI Tooltips (`ui/overworld/poi_tooltips.py`)

**Current (Hardcoded):**
```python
if poi.poi_type == "dungeon":
    # Dungeon-specific tooltip
elif poi.poi_type in ("village", "town"):
    # Settlement-specific tooltip
```

**Should be:**
- POI classes provide their own tooltip data
- Or: Tooltip factory registry

## Proposed Refactoring

### Option 1: Registry Pattern (Recommended)

Create a POI registry that maps type strings to:
- Factory functions
- Optional spatial rule evaluators
- Optional tooltip generators

**Pros:**
- Truly extensible - add new type by registering, no core code changes
- Clean separation of concerns
- Easy to test

**Cons:**
- Requires refactoring existing code
- Slightly more complex initial setup

### Option 2: Plugin/Strategy Pattern

Each POI class provides:
- Factory method (class method)
- Optional spatial rule evaluation method
- Optional tooltip generation method

**Pros:**
- Keeps POI-specific logic with POI classes
- Still extensible but less centralized

**Cons:**
- Still need some central registry
- More methods per POI class

### Option 3: Configuration-Only Rules (Simplest)

Make spatial rules purely config-driven:
- All rule evaluation logic is generic
- Rules define: "avoid_type", "near_type", "prefer_distance", etc.
- No hardcoded type-specific logic

**Pros:**
- Minimal code changes
- Very flexible via config

**Cons:**
- Less control for complex behaviors
- Spatial rules config becomes more complex

## Recommended Approach

**Hybrid: Registry + Config-Driven Rules**

1. **Registry for POI Creation**: Map `poi_type` → factory function
2. **Config-Driven Spatial Rules**: Generic rule evaluator that reads from config
3. **POI Methods for Special Cases**: Optional methods on POI classes for tooltips/special logic

## Files That Would Change

- `world/poi/placement.py` - Add registry, make `_create_poi()` use registry, make `_evaluate_poi_position()` fully generic
- `world/poi/base.py` - Add optional methods for tooltips
- `world/poi/types.py` - Register each POI class on definition
- `engine/utils/save_system.py` - Use registry for deserialization
- `ui/overworld/poi_tooltips.py` - Use POI methods or registry

## Example: Adding a New POI Type (After Refactoring)

```python
# 1. Define the class
class RuinPOI(PointOfInterest):
    def __init__(self, ...):
        super().__init__(poi_id, "ruin", position, level, name)
        # ... custom fields

# 2. Register it (automatic on import, or explicit)
POI_REGISTRY.register("ruin", RuinPOI)

# 3. Add to config
# config/overworld_settings.json: Add "ruin": 0.1 to distribution
# config/generation_settings.json: Add spatial rules for "ruin"

# Done! No core code changes needed.
```

## Conclusion

**Current State**: Works but requires manual code updates in 4+ files per new type.

**After Refactoring**: Add new POI type by:
1. Creating the class
2. Registering it (or auto-register)
3. Updating config files
4. Done!

The refactoring is worthwhile if you plan to add multiple POI types. If you only plan 1-2 more types, the current approach is acceptable.

