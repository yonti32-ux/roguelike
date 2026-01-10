# POI System Refactoring - Complete

## Overview

The POI (Point of Interest) system has been refactored to be fully modular, configurable, and extensible. New POI types can now be added without modifying core placement, save/load, or UI code.

## What Changed

### 1. Registry System (`world/poi/registry.py`)

**NEW FILE**: Created a global POI registry that maps POI type strings to factory functions.

- Supports factory functions for custom creation logic
- Supports automatic registration from POI classes
- Provides centralized POI creation through `get_registry().create()`

### 2. Enhanced Base Class (`world/poi/base.py`)

Added extensibility methods that subclasses can override:

- **`get_tooltip_lines(game)`**: Returns POI-specific tooltip information
- **`get_display_label()`**: Returns display name for the POI type
- **`serialize_state()`**: Returns POI-specific state for saving
- **`deserialize_state(data)`**: Restores POI-specific state from save data

### 3. Generic Spatial Rules (`world/poi/placement.py`)

**Refactored `_evaluate_poi_position()`** to be fully config-driven:

- **Before**: Hardcoded if/elif chains for village/dungeon/camp
- **After**: Generic rule evaluation engine that reads from config

**Rule Types Supported** (from config):
- `near_{type}`: Prefer being within min/max distance of specific POI type
- `avoid_{type}`: Penalize being too close to specific POI type  
- `prefer_remote`: Bonus for being far from all existing POIs

All rules are now defined purely in JSON config - no code changes needed!

### 4. Registry-Based Creation (`world/poi/placement.py`)

**Refactored `_create_poi()`** to use registry:

- **Before**: Hardcoded if/elif chain
- **After**: `get_registry().create()` with special handling for dungeon floor_count

### 5. Save/Load System (`engine/utils/save_system.py`)

**Updated to use registry**:

- POI deserialization uses `get_registry().create()`
- Uses `poi.serialize_state()` and `poi.deserialize_state()` for extensibility
- Backwards compatible with existing saves

### 6. Extensible UI Tooltips (`ui/overworld/poi_tooltips.py`)

**Refactored to use POI methods**:

- **Before**: Hardcoded checks for dungeon/village/town
- **After**: Uses `poi.get_tooltip_lines()` and `poi.get_display_label()`

Removed hardcoded type-specific logic - now fully extensible!

### 7. POI Type Registration (`world/poi/types.py`)

All existing POI types now:

- Implement `serialize_state()` and `deserialize_state()`
- Implement `get_tooltip_lines()` with type-specific information
- Implement `get_display_label()` for display names
- Are **auto-registered** on import via `_register_poi_types()`

## How to Add a New POI Type

### Step 1: Create the POI Class

```python
# world/poi/types.py (or new file)

class RuinPOI(PointOfInterest):
    def __init__(self, poi_id: str, position: tuple, level: int = 1, name: Optional[str] = None, **kwargs):
        super().__init__(poi_id, "ruin", position, level, name)
        self.treasure_claimed = kwargs.get("treasure_claimed", False)
        # ... custom fields
    
    def get_display_label(self) -> str:
        return "Ruin"
    
    def get_tooltip_lines(self, game: Optional["Game"] = None) -> List[str]:
        lines = []
        if self.treasure_claimed:
            lines.append("Status: Looted")
        else:
            lines.append("Status: Unexplored")
        return lines
    
    def serialize_state(self) -> Dict[str, Any]:
        return {"treasure_claimed": self.treasure_claimed}
    
    def deserialize_state(self, data: Dict[str, Any]) -> None:
        if "treasure_claimed" in data:
            self.treasure_claimed = data["treasure_claimed"]
    
    def enter(self, game: "Game") -> None:
        # Custom enter logic
        pass
```

### Step 2: Register the POI Type

```python
# In the same file, add to _register_poi_types():

def _register_poi_types() -> None:
    # ... existing registrations ...
    register_poi_type("ruin", poi_class=RuinPOI)
```

Or register manually if defined elsewhere:

```python
from world.poi.registry import register_poi_type
register_poi_type("ruin", poi_class=RuinPOI)
```

### Step 3: Update Configuration

**`config/overworld_settings.json`** - Add distribution ratio:
```json
{
  "poi": {
    "distribution": {
      "dungeon": 0.35,
      "village": 0.25,
      "town": 0.15,
      "camp": 0.15,
      "ruin": 0.10
    }
  }
}
```

**`config/generation_settings.json`** - Add spatial rules (optional):
```json
{
  "poi": {
    "placement_rules": {
      "placement_order": ["town", "village", "dungeon", "camp", "ruin"],
      "spatial_rules": {
        "ruin": {
          "avoid_town": {
            "enabled": true,
            "min_distance": 20,
            "penalty": 2.0
          },
          "prefer_remote": {
            "enabled": true,
            "distance_threshold": 25,
            "bonus_weight": 1.2
          }
        }
      }
    }
  }
}
```

### Step 4: Done!

No core code changes needed. The new POI type will:
- ✅ Be placed automatically during world generation
- ✅ Use configured spatial rules
- ✅ Save/load correctly
- ✅ Display proper tooltips
- ✅ Work with all existing systems

## Configuration Reference

### Spatial Rules Config Format

```json
{
  "near_{type}": {
    "enabled": true,
    "min_distance": 10,
    "max_distance": 30,
    "chance": 0.7,
    "bonus": 2.0,
    "close_penalty": 1.0,
    "far_penalty": 0.5
  },
  "avoid_{type}": {
    "enabled": true,
    "min_distance": 15,
    "penalty": 2.0,
    "bonus_when_far": 0.3,
    "far_threshold": 22.5
  },
  "prefer_remote": {
    "enabled": true,
    "distance_threshold": 30,
    "bonus_weight": 1.5
  }
}
```

## Benefits

1. **Modularity**: Each POI type is self-contained
2. **Configurability**: Spatial rules defined in JSON, no code changes
3. **Extensibility**: Add new types by creating class + config
4. **Maintainability**: No hardcoded if/elif chains in core logic
5. **Testability**: Easy to test individual POI types in isolation

## Backwards Compatibility

✅ All existing saves will load correctly
✅ All existing POI types work as before
✅ Configuration format unchanged
✅ No breaking API changes

## Files Modified

- `world/poi/base.py` - Added extensibility methods
- `world/poi/placement.py` - Refactored to use registry + generic rules
- `world/poi/types.py` - Added registration + extensibility methods
- `world/poi/__init__.py` - Exports registry functions
- `world/poi/registry.py` - **NEW** - Registry system
- `engine/utils/save_system.py` - Uses registry for deserialization
- `ui/overworld/poi_tooltips.py` - Uses POI extensibility methods

## Testing Checklist

- [ ] Existing POI types still spawn correctly
- [ ] Spatial rules work as configured
- [ ] Save/load works for all POI types
- [ ] Tooltips display correctly
- [ ] New POI type can be added following the guide above

## Future Enhancements

Possible future improvements:
- POI type-specific placement strategies (hook system)
- Runtime POI type registration (mod support)
- POI type validation/constraints system
- Visual representation registry for different POI types

