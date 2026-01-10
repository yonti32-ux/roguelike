# Map & POI Generation Rules System - Architecture Plan

## Overview

This document outlines a comprehensive rule-based system for making map generation and POI (Point of Interest) generation highly configurable and extensible. The goal is to replace hardcoded logic with declarative rules that can be defined in configuration files and extended through a plugin-like system.

---

## Design Principles

1. **Declarative Configuration**: Rules defined in JSON/YAML, not code
2. **Composability**: Rules can be combined, chained, and nested
3. **Extensibility**: Easy to add new rule types without modifying core code
4. **Backwards Compatibility**: Existing hardcoded logic becomes default rules
5. **Validation**: Rules can validate and enforce constraints
6. **Modularity**: Separate rule systems for different aspects (terrain, POI placement, room generation, etc.)

---

## Architecture

### System Layers

```
┌─────────────────────────────────────────┐
│   Rule Configuration Files (JSON)       │  ← User-defined rules
├─────────────────────────────────────────┤
│   Rule Engine / Rule Parser             │  ← Loads & validates rules
├─────────────────────────────────────────┤
│   Rule Executors                        │  ← Applies rules during generation
├─────────────────────────────────────────┤
│   Generation Systems                    │  ← Terrain, POI, Floor generators
└─────────────────────────────────────────┘
```

### Key Components

1. **Rule Definitions** (`config/generation_rules/`)
   - `terrain_rules.json` - Terrain generation rules
   - `poi_placement_rules.json` - POI placement constraints
   - `floor_generation_rules.json` - Dungeon floor rules
   - `room_tag_rules.json` - Room tagging rules

2. **Rule Engine** (`world/generation/rules/`)
   - `rule_engine.py` - Core rule evaluation engine
   - `rule_types.py` - Base rule type definitions
   - `executors/` - Rule executors for different domains

3. **Generation Systems** (Modified)
   - `world/overworld/generation.py` - Uses terrain rules
   - `world/poi/placement.py` - Uses POI placement rules
   - `world/mapgen.py` - Uses floor generation rules

---

## Rule System Design

### Rule Structure

A rule consists of:
- **Type**: What kind of rule (constraint, generator, modifier, validator)
- **Conditions**: When the rule applies
- **Actions**: What the rule does
- **Priority**: Order of evaluation (lower = earlier)
- **Metadata**: Name, description, enabled flag

### Basic Rule Schema

```json
{
  "id": "rule_unique_id",
  "name": "Human-readable name",
  "description": "What this rule does",
  "type": "constraint|generator|modifier|validator",
  "domain": "terrain|poi|floor|room",
  "enabled": true,
  "priority": 100,
  "conditions": {
    // When to apply this rule
  },
  "actions": {
    // What to do when rule applies
  }
}
```

---

## Rule Types

### 1. Constraint Rules
Define what **cannot** happen. Used for validation and rejection.

**Examples:**
- "POIs cannot be placed on water"
- "Rooms must be at least 4x4 tiles"
- "Dungeons must have minimum distance of 8 tiles from other POIs"

**Schema:**
```json
{
  "type": "constraint",
  "conditions": {
    "check": "poi_placement",
    "context": { "poi_type": "dungeon", "terrain": "water" }
  },
  "actions": {
    "reject": true,
    "reason": "Cannot place POI on water terrain"
  }
}
```

### 2. Generator Rules
Define how to **generate** content.

**Examples:**
- "Generate terrain using cellular automata with these parameters"
- "Create POI distribution with these type ratios"
- "Generate rooms with size range 4-9"

**Schema:**
```json
{
  "type": "generator",
  "conditions": {
    "when": "terrain_generation"
  },
  "actions": {
    "method": "cellular_automata",
    "parameters": {
      "iterations": 3,
      "neighbor_radius": 1,
      "conversion_threshold": 4
    }
  }
}
```

### 3. Modifier Rules
**Modify** existing content after initial generation.

**Examples:**
- "Smooth terrain transitions"
- "Adjust POI levels based on distance from start"
- "Add room tags based on floor index"

**Schema:**
```json
{
  "type": "modifier",
  "conditions": {
    "when": "post_generation",
    "context": { "domain": "terrain" }
  },
  "actions": {
    "method": "smooth_transitions",
    "parameters": {
      "neighbor_radius": 1,
      "chance": 0.15
    }
  }
}
```

### 4. Validator Rules
**Validate** generated content meets requirements.

**Examples:**
- "All rooms must be connected"
- "Must have at least one POI per region"
- "Terrain must have walkable path from start"

**Schema:**
```json
{
  "type": "validator",
  "conditions": {
    "when": "validation_phase"
  },
  "actions": {
    "method": "check_connectivity",
    "parameters": {
      "required": true,
      "on_failure": "regenerate"
    }
  }
}
```

---

## Domain-Specific Rule Sets

### 1. Terrain Generation Rules

**Location:** `config/generation_rules/terrain_rules.json`

**Example Rules:**
```json
{
  "rules": [
    {
      "id": "terrain_initial_distribution",
      "type": "generator",
      "domain": "terrain",
      "priority": 1,
      "conditions": {
        "when": "initial_terrain_generation"
      },
      "actions": {
        "method": "random_distribution",
        "parameters": {
          "terrain_weights": {
            "grass": 0.35,
            "plains": 0.20,
            "forest": 0.15,
            "mountain": 0.12,
            "desert": 0.10,
            "water": 0.08
          }
        }
      }
    },
    {
      "id": "terrain_smoothing",
      "type": "modifier",
      "domain": "terrain",
      "priority": 2,
      "conditions": {
        "when": "post_generation"
      },
      "actions": {
        "method": "cellular_automata_smooth",
        "parameters": {
          "iterations": 3,
          "neighbor_radius": 1,
          "conversion_threshold": 4,
          "conversion_chance": 0.6
        }
      }
    },
    {
      "id": "terrain_forest_preferences",
      "type": "modifier",
      "domain": "terrain",
      "priority": 3,
      "conditions": {
        "when": "terrain_refinement",
        "context": {
          "terrain_type": "forest"
        }
      },
      "actions": {
        "method": "prefer_neighbors",
        "parameters": {
          "preferred_neighbors": ["water", "grass", "plains"],
          "isolation_chance": 0.15,
          "conversion_to": ["grass", "plains"]
        }
      }
    },
    {
      "id": "terrain_water_clustering",
      "type": "constraint",
      "domain": "terrain",
      "priority": 4,
      "conditions": {
        "check": "water_placement",
        "context": {
          "water_neighbors": { "$lt": 2 }
        }
      },
      "actions": {
        "method": "prevent_isolated_water",
        "parameters": {
          "min_neighbors": 2,
          "conversion_chance": 0.3,
          "convert_to_adjacent": true
        }
      }
    }
  ]
}
```

### 2. POI Placement Rules

**Location:** `config/generation_rules/poi_placement_rules.json`

**Example Rules:**
```json
{
  "rules": [
    {
      "id": "poi_density_calculation",
      "type": "generator",
      "domain": "poi",
      "priority": 1,
      "conditions": {
        "when": "poi_count_calculation"
      },
      "actions": {
        "method": "calculate_from_density",
        "parameters": {
          "density": 0.1,
          "max_pois": 200,
          "formula": "area * density"
        }
      }
    },
    {
      "id": "poi_type_distribution",
      "type": "generator",
      "domain": "poi",
      "priority": 2,
      "conditions": {
        "when": "poi_type_allocation"
      },
      "actions": {
        "method": "distribute_by_ratio",
        "parameters": {
          "distribution": {
            "dungeon": 0.4,
            "village": 0.3,
            "town": 0.15,
            "camp": 0.15
          }
        }
      }
    },
    {
      "id": "poi_terrain_constraint",
      "type": "constraint",
      "domain": "poi",
      "priority": 10,
      "conditions": {
        "check": "poi_placement",
        "context": {
          "terrain": { "$in": ["water"] }
        }
      },
      "actions": {
        "reject": true,
        "reason": "Cannot place POI on water"
      }
    },
    {
      "id": "poi_minimum_distance",
      "type": "constraint",
      "domain": "poi",
      "priority": 20,
      "conditions": {
        "check": "poi_placement",
        "context": {
          "distance_to_nearest_poi": { "$lt": 8 }
        }
      },
      "actions": {
        "reject": true,
        "reason": "Too close to existing POI"
      }
    },
    {
      "id": "poi_terrain_preferences",
      "type": "modifier",
      "domain": "poi",
      "priority": 5,
      "conditions": {
        "when": "poi_placement_candidate",
        "context": {
          "poi_type": "village"
        }
      },
      "actions": {
        "method": "weight_by_terrain",
        "parameters": {
          "preferred_terrain": {
            "grass": 2.0,
            "plains": 1.5
          },
          "avoid_terrain": {
            "mountain": 0.1,
            "desert": 0.3
          }
        }
      }
    },
    {
      "id": "poi_level_calculation",
      "type": "modifier",
      "domain": "poi",
      "priority": 30,
      "conditions": {
        "when": "poi_post_placement"
      },
      "actions": {
        "method": "calculate_level_by_distance",
        "parameters": {
          "base_level": 1,
          "max_level": 20,
          "scaling_type": "distance",
          "level_per_distance": 0.5
        }
      }
    }
  ]
}
```

### 3. Floor Generation Rules

**Location:** `config/generation_rules/floor_generation_rules.json`

**Example Rules:**
```json
{
  "rules": [
    {
      "id": "floor_size_scaling",
      "type": "generator",
      "domain": "floor",
      "priority": 1,
      "conditions": {
        "when": "floor_size_calculation",
        "context": {
          "floor_index": { "$var": "floor_index" }
        }
      },
      "actions": {
        "method": "progressive_scaling",
        "parameters": {
          "base_size": { "$var": "base_tiles" },
          "scales_by_floor": {
            "1": { "scales": [0.9, 1.0, 1.1], "weights": [0.3, 0.4, 0.3] },
            "2": { "scales": [1.0, 1.1, 1.25], "weights": [0.3, 0.4, 0.3] },
            "3-4": { "scales": [1.1, 1.25, 1.5], "weights": [0.2, 0.5, 0.3] },
            "5-6": { "scales": [1.25, 1.5, 1.75], "weights": [0.3, 0.4, 0.3] },
            "7-8": { "scales": [1.5, 1.75, 2.0], "weights": [0.2, 0.5, 0.3] },
            "9+": { "scales": [1.75, 2.0, 2.25], "weights": [0.3, 0.4, 0.3] }
          },
          "min_scale": 0.9,
          "max_scale": 2.5
        }
      }
    },
    {
      "id": "room_count_calculation",
      "type": "generator",
      "domain": "floor",
      "priority": 2,
      "conditions": {
        "when": "room_count_calculation"
      },
      "actions": {
        "method": "calculate_from_area",
        "parameters": {
          "base_rooms": 10,
          "density_factor_formula": "sqrt(area_ratio)",
          "min_rooms": 6,
          "max_rooms": 22
        }
      }
    },
    {
      "id": "room_size_constraints",
      "type": "constraint",
      "domain": "floor",
      "priority": 10,
      "conditions": {
        "check": "room_creation",
        "context": {
          "width": { "$lt": 4 },
          "height": { "$lt": 4 }
        }
      },
      "actions": {
        "reject": true,
        "reason": "Room too small"
      }
    },
    {
      "id": "room_size_range",
      "type": "generator",
      "domain": "floor",
      "priority": 3,
      "conditions": {
        "when": "room_size_generation"
      },
      "actions": {
        "method": "random_range",
        "parameters": {
          "min_size": 4,
          "max_size": 9
        }
      }
    },
    {
      "id": "room_intersection_constraint",
      "type": "constraint",
      "domain": "floor",
      "priority": 20,
      "conditions": {
        "check": "room_placement",
        "context": {
          "intersects_existing": true
        }
      },
      "actions": {
        "reject": true,
        "reason": "Room overlaps existing room"
      }
    }
  ]
}
```

### 4. Room Tagging Rules

**Location:** `config/generation_rules/room_tag_rules.json`

**Example Rules:**
```json
{
  "rules": [
    {
      "id": "tag_start_room",
      "type": "modifier",
      "domain": "room",
      "priority": 1,
      "conditions": {
        "when": "room_tagging",
        "context": {
          "room_index": 0
        }
      },
      "actions": {
        "method": "set_tag",
        "parameters": {
          "tag": "start"
        }
      }
    },
    {
      "id": "tag_treasure_room",
      "type": "modifier",
      "domain": "room",
      "priority": 2,
      "conditions": {
        "when": "room_tagging",
        "context": {
          "room_index": { "$gt": 0 },
          "distance_from_start": { "$max": true }
        }
      },
      "actions": {
        "method": "set_tag",
        "parameters": {
          "tag": "treasure"
        }
      }
    },
    {
      "id": "tag_lair_room",
      "type": "modifier",
      "domain": "room",
      "priority": 3,
      "conditions": {
        "when": "room_tagging",
        "context": {
          "tag": "generic",
          "not_tagged": ["start", "treasure"]
        }
      },
      "actions": {
        "method": "set_tag_random",
        "parameters": {
          "tag": "lair",
          "chance": 1.0,
          "max_per_floor": 1
        }
      }
    },
    {
      "id": "tag_shop_room",
      "type": "modifier",
      "domain": "room",
      "priority": 4,
      "conditions": {
        "when": "room_tagging",
        "context": {
          "tag": "generic"
        }
      },
      "actions": {
        "method": "set_tag_random",
        "parameters": {
          "tag": "shop",
          "chance": 0.7,
          "max_per_floor": 1
        }
      }
    },
    {
      "id": "tag_graveyard_room",
      "type": "modifier",
      "domain": "room",
      "priority": 5,
      "conditions": {
        "when": "room_tagging",
        "context": {
          "tag": "generic",
          "floor_index": { "$gte": 2 }
        }
      },
      "actions": {
        "method": "set_tag_random",
        "parameters": {
          "tag": "graveyard",
          "chance": 0.8,
          "max_per_floor": 1
        }
      }
    },
    {
      "id": "tag_sanctum_room",
      "type": "modifier",
      "domain": "room",
      "priority": 6,
      "conditions": {
        "when": "room_tagging",
        "context": {
          "tag": "generic",
          "floor_index": { "$gte": 3 }
        }
      },
      "actions": {
        "method": "set_tag_random",
        "parameters": {
          "tag": "sanctum",
          "chance": 0.5,
          "max_per_floor": 1
        }
      }
    }
  ]
}
```

---

## Rule Engine Implementation

### Core Rule Engine (`world/generation/rules/rule_engine.py`)

```python
class RuleEngine:
    """
    Core rule evaluation and execution engine.
    """
    
    def __init__(self, rule_files: List[Path]):
        """Load rules from configuration files."""
        self.rules = []
        for rule_file in rule_files:
            self.rules.extend(self._load_rules(rule_file))
        self.rules.sort(key=lambda r: r.priority)
    
    def evaluate(self, domain: str, event: str, context: Dict) -> Dict:
        """
        Evaluate rules for a given domain and event.
        
        Args:
            domain: Rule domain (terrain, poi, floor, room)
            event: Event type (generation, placement, modification, validation)
            context: Context data for rule evaluation
            
        Returns:
            Result dictionary with actions to take
        """
        applicable_rules = [
            r for r in self.rules
            if r.domain == domain and r.enabled and r.matches(context, event)
        ]
        
        result = {"actions": [], "rejections": [], "modifications": []}
        
        for rule in applicable_rules:
            rule_result = rule.execute(context)
            result["actions"].extend(rule_result.get("actions", []))
            result["rejections"].extend(rule_result.get("rejections", []))
            result["modifications"].extend(rule_result.get("modifications", []))
        
        return result
    
    def _load_rules(self, rule_file: Path) -> List[Rule]:
        """Load rules from JSON file."""
        # Implementation...
```

### Rule Executors

Different executors for different domains:

- `TerrainRuleExecutor` - Applies terrain rules
- `POIRuleExecutor` - Applies POI placement rules
- `FloorRuleExecutor` - Applies floor generation rules
- `RoomRuleExecutor` - Applies room tagging rules

---

## Condition System

### Condition Operators

Support various operators for flexible condition matching:

```json
{
  "conditions": {
    "equality": { "terrain": "grass" },
    "inequality": { "distance": { "$gt": 5 } },
    "inclusion": { "terrain": { "$in": ["grass", "plains"] } },
    "comparison": { "floor_index": { "$gte": 3 } },
    "logic": {
      "$and": [
        { "poi_type": "dungeon" },
        { "distance": { "$lt": 10 } }
      ]
    },
    "variables": { "floor_index": { "$var": "floor_index" } },
    "functions": { "distance": { "$calc": "sqrt(dx^2 + dy^2)" } }
  }
}
```

### Supported Operators

- `$eq` / `==` - Equality
- `$ne` / `!=` - Inequality
- `$gt` - Greater than
- `$gte` - Greater than or equal
- `$lt` - Less than
- `$lte` - Less than or equal
- `$in` - In list
- `$nin` - Not in list
- `$and` - Logical AND
- `$or` - Logical OR
- `$not` - Logical NOT
- `$var` - Reference variable from context
- `$calc` - Calculate value from expression
- `$max` - Maximum value in collection
- `$min` - Minimum value in collection

---

## Action System

### Action Types

1. **Reject**: Reject current candidate
   ```json
   {
     "reject": true,
     "reason": "Validation failed"
   }
   ```

2. **Modify**: Modify context/state
   ```json
   {
     "modify": {
       "property": "level",
       "value": 5,
       "method": "set|add|multiply|max|min"
     }
   }
   ```

3. **Generate**: Generate new content
   ```json
   {
     "generate": {
       "method": "random_distribution",
       "parameters": { ... }
     }
   }
   ```

4. **Call Function**: Call custom function
   ```json
   {
     "call": {
       "function": "calculate_level",
       "parameters": { ... }
     }
   }
   ```

---

## Implementation Plan

### Phase 1: Core Rule Engine (Foundation)
**Goal**: Basic rule loading and evaluation

- [ ] Create `world/generation/rules/` directory structure
- [ ] Implement `Rule` base class
- [ ] Implement `RuleEngine` core
- [ ] Implement condition evaluation system
- [ ] Implement action execution system
- [ ] Create rule schema validator
- [ ] Write unit tests for rule engine

### Phase 2: Terrain Rules Integration
**Goal**: Migrate terrain generation to use rules

- [ ] Create `config/generation_rules/terrain_rules.json`
- [ ] Port existing terrain logic to rules
- [ ] Implement `TerrainRuleExecutor`
- [ ] Integrate with `world/overworld/generation.py`
- [ ] Test terrain generation with rules
- [ ] Keep old code as fallback option

### Phase 3: POI Placement Rules
**Goal**: Migrate POI placement to use rules

- [ ] Create `config/generation_rules/poi_placement_rules.json`
- [ ] Port existing POI placement logic to rules
- [ ] Implement `POIRuleExecutor`
- [ ] Integrate with `world/poi/placement.py`
- [ ] Test POI placement with rules

### Phase 4: Floor Generation Rules
**Goal**: Migrate floor generation to use rules

- [ ] Create `config/generation_rules/floor_generation_rules.json`
- [ ] Port existing floor generation logic to rules
- [ ] Implement `FloorRuleExecutor`
- [ ] Integrate with `world/mapgen.py`
- [ ] Test floor generation with rules

### Phase 5: Room Tagging Rules
**Goal**: Migrate room tagging to use rules

- [ ] Create `config/generation_rules/room_tag_rules.json`
- [ ] Port existing room tagging logic to rules
- [ ] Implement `RoomRuleExecutor`
- [ ] Integrate with `world/mapgen.py`
- [ ] Test room tagging with rules

### Phase 6: Advanced Features
**Goal**: Add extensibility and advanced features

- [ ] Custom function registration system
- [ ] Rule composition and chaining
- [ ] Rule profiling/debugging tools
- [ ] Rule validation UI/tooling
- [ ] Documentation and examples
- [ ] Migration guide

---

## File Structure

```
config/
  generation_rules/
    terrain_rules.json
    poi_placement_rules.json
    floor_generation_rules.json
    room_tag_rules.json
    examples/
      custom_terrain_biome.json
      custom_poi_types.json

world/
  generation/
    __init__.py
    rules/
      __init__.py
      rule_engine.py        # Core rule engine
      rule_types.py         # Base rule classes
      condition_evaluator.py # Condition evaluation
      action_executor.py    # Action execution
      executors/
        __init__.py
        terrain_executor.py
        poi_executor.py
        floor_executor.py
        room_executor.py
      functions/            # Custom rule functions
        __init__.py
        terrain_functions.py
        poi_functions.py
        floor_functions.py
```

---

## Extensibility Examples

### Adding Custom Terrain Biomes

```json
{
  "id": "custom_swamp_biome",
  "type": "generator",
  "domain": "terrain",
  "priority": 1,
  "conditions": {
    "when": "initial_terrain_generation",
    "context": {
      "region": { "$in": ["swamp_region"] }
    }
  },
  "actions": {
    "method": "add_terrain_type",
    "parameters": {
      "terrain_id": "swamp",
      "weight": 0.3,
      "color": [80, 100, 60],
      "walkable": true,
      "movement_cost": 1.8
    }
  }
}
```

### Adding Custom POI Types

```json
{
  "id": "poi_custom_ruins",
  "type": "generator",
  "domain": "poi",
  "priority": 3,
  "conditions": {
    "when": "poi_type_allocation"
  },
  "actions": {
    "method": "register_poi_type",
    "parameters": {
      "poi_type": "ruins",
      "distribution_weight": 0.05,
      "min_level": 3,
      "max_level": 15,
      "preferred_terrain": ["forest", "mountain"]
    }
  }
}
```

### Custom Room Tags

```json
{
  "id": "tag_boss_arena",
  "type": "modifier",
  "domain": "room",
  "priority": 10,
  "conditions": {
    "when": "room_tagging",
    "context": {
      "tag": "generic",
      "floor_index": { "$gte": 5 },
      "room_size": { "$gte": 64 }
    }
  },
  "actions": {
    "method": "set_tag_random",
    "parameters": {
      "tag": "boss_arena",
      "chance": 0.3,
      "max_per_floor": 1
    }
  }
}
```

---

## Benefits

1. **Easy Configuration**: Change generation behavior without code changes
2. **Modularity**: Each aspect (terrain, POI, floors) independently configurable
3. **Extensibility**: Add new rules without modifying core generation code
4. **Testability**: Easy to test individual rules
5. **Shareability**: Users can share rule sets
6. **Debugging**: Clear which rules applied and why
7. **Performance**: Rules can be cached and optimized

---

## Migration Strategy

1. **Keep Existing Code**: Maintain current hardcoded logic as default fallback
2. **Gradual Migration**: Port one domain at a time (terrain → POI → floors → rooms)
3. **Backwards Compatibility**: Old code works if rules not found/disabled
4. **Feature Flag**: Enable rule-based generation via config flag
5. **Validation**: Ensure rule-based generation matches old behavior

---

## Future Enhancements

1. **Visual Rule Editor**: GUI tool for creating/editing rules
2. **Rule Templates**: Pre-built rule sets for different game styles
3. **Rule Marketplace**: Community-shared rule sets
4. **Performance Profiling**: Track rule execution time
5. **Rule Dependencies**: Rules that depend on other rules
6. **Dynamic Rules**: Rules that can be modified at runtime
7. **Rule Versioning**: Track rule changes and compatibility

---

## Questions & Decisions Needed

1. **Rule Format**: JSON vs YAML vs Python DSL? (Recommend: JSON for now, Python DSL later)
2. **Performance**: How much overhead is acceptable? (Recommend: <10% generation time)
3. **Validation**: Strict schema validation or flexible? (Recommend: Strict with helpful errors)
4. **Backwards Compatibility**: How long to maintain old code? (Recommend: 1-2 major versions)
5. **Error Handling**: How to handle invalid rules? (Recommend: Fail fast with clear errors)
6. **Rule Loading**: Load all rules at startup or on-demand? (Recommend: On-demand with caching)

---

This plan provides a comprehensive foundation for a rule-based generation system that's both powerful and extensible. The system can start simple and grow in complexity as needed.

