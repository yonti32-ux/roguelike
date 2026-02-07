# Enemy System Module Structure

This module has been refactored into a modular structure for better organization and maintainability.

## Current Structure

```
systems/enemies/
├── __init__.py              # Main entry point, exports all public APIs
├── types.py                 # EnemyArchetype and EnemyPackTemplate classes
├── registry.py              # Registry dicts and registration functions
├── selection.py             # Enemy/pack selection and choice functions
├── scaling.py               # Stat scaling functions
├── elite.py                 # Elite enemy system
├── synergies.py             # Enemy pack synergy bonuses
├── utils.py                 # Utility functions for querying and analyzing
├── validation.py            # Validation and integrity checking
├── definitions/             # Enemy archetype and pack definitions
│   ├── __init__.py          # Registration coordinator
│   ├── early_game.py        # Tier 1 archetypes (Difficulty 10-30)
│   ├── mid_game.py          # Tier 2 archetypes (Difficulty 40-69)
│   ├── late_game.py         # Tier 3 archetypes (Difficulty 70-90+)
│   ├── overworld_parties.py # Party archetypes (guards, rangers, etc.)
│   └── packs.py             # All pack templates
└── README.md                # This file
```

## Migration Status

✅ **Complete**: The migration from the legacy `systems/enemies.py` file is complete. All definitions have been moved to the new modular structure.

### Phase 1: ✅ Complete
- Created modular structure
- Separated core functionality (types, registry, selection, scaling, elite)
- Maintained backward compatibility

### Phase 2: ✅ Complete
- Split definitions into separate files:
  - `definitions/early_game.py` - Tier 1 archetypes (goblins, bandits, etc.)
  - `definitions/mid_game.py` - Tier 2 archetypes (orcs, trolls, etc.)
  - `definitions/late_game.py` - Tier 3 archetypes (dragons, liches, etc.)
  - `definitions/overworld_parties.py` - Party archetypes (guards, rangers, etc.)
  - `definitions/packs.py` - All pack templates
- Moved `enemy_synergies.py` to `synergies.py` within the enemies module
- Removed legacy `systems/enemies.py` file

### Phase 3: ✅ Complete
- Added utility functions (`utils.py`) for querying and analyzing enemies
- Added validation system (`validation.py`) for integrity checking
- Enhanced documentation and exports

## Usage

The module maintains 100% backward compatibility. All existing imports continue to work:

```python
from systems.enemies import get_archetype, EnemyArchetype, choose_archetype_for_floor
from systems.enemies.synergies import apply_synergies_to_enemies
```

### Utility Functions

```python
from systems.enemies.utils import (
    get_archetype_count,
    get_archetypes_by_role,
    get_archetypes_by_difficulty_range,
    get_archetype_stats_summary,
    get_difficulty_distribution,
    get_role_distribution,
)

# Get statistics
count = get_archetype_count()
distribution = get_difficulty_distribution()

# Query enemies
brutes = get_archetypes_by_role("Brute")
mid_game = get_archetypes_by_difficulty_range(40, 60)
```

### Validation

```python
from systems.enemies.validation import (
    validate_all_archetypes,
    validate_all_packs,
    run_full_validation,
    check_for_orphaned_archetypes,
)

# Validate everything
report = run_full_validation()
if not report["overall_valid"]:
    print("Validation errors found!")
    print(report["archetypes"]["errors"])
    print(report["packs"]["errors"])
```

## Benefits

1. **Better Organization**: Related functionality is grouped together
2. **Easier Maintenance**: Smaller files are easier to navigate and modify
3. **Scalability**: Easy to add new enemy types without bloating a single file
4. **Clear Separation**: Definitions are separated from core functionality
5. **Validation Tools**: Built-in validation helps catch errors early
6. **Utility Functions**: Helper functions make it easy to query and analyze enemies

## Module Overview

### Core Modules

- **`types.py`**: Defines `EnemyArchetype` and `EnemyPackTemplate` dataclasses
- **`registry.py`**: Manages global registries and registration functions
- **`selection.py`**: Functions for choosing enemies/packs based on floor, level, tags
- **`scaling.py`**: Computes scaled stats for enemies at different floors
- **`elite.py`**: Elite enemy spawning and stat modifiers
- **`synergies.py`**: Pack synergy bonuses when enemies work together

### Utility Modules

- **`utils.py`**: Query functions, statistics, summaries, and analysis tools
- **`validation.py`**: Validation and integrity checking for all enemies and packs

### Definition Modules

- **`definitions/early_game.py`**: Early game enemies (Difficulty 10-30)
- **`definitions/mid_game.py`**: Mid game enemies (Difficulty 40-69)
- **`definitions/late_game.py`**: Late game enemies (Difficulty 70-90+)
- **`definitions/overworld_parties.py`**: Overworld party archetypes
- **`definitions/packs.py`**: All enemy pack templates