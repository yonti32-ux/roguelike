# Enemy System Quick Reference

A quick reference guide for working with the enemy system.

## Common Operations

### Getting Enemy Information

```python
from systems.enemies import get_archetype, ENEMY_ARCHETYPES

# Get a specific archetype
arch = get_archetype("goblin_skirmisher")
print(f"{arch.name}: {arch.role}, Difficulty {arch.difficulty_level}")

# List all archetypes
all_ids = list(ENEMY_ARCHETYPES.keys())
```

### Querying Enemies

```python
from systems.enemies import (
    get_enemies_by_tag,
    get_enemies_in_difficulty_range,
    get_enemies_for_floor_range,
)

# Find all undead enemies
undead = get_enemies_by_tag("undead")

# Find enemies for a difficulty range
mid_game = get_enemies_in_difficulty_range(40, 60)

# Find enemies that can spawn on floors 3-5
floor_enemies = get_enemies_for_floor_range(3, 5)
```

### Choosing Enemies for Spawning

```python
from systems.enemies import choose_archetype_for_floor, choose_pack_for_floor

# Choose an enemy for floor 3, graveyard room
enemy = choose_archetype_for_floor(3, room_tag="graveyard")

# Choose a pack for floor 5
pack = choose_pack_for_floor(5, room_tag="lair")
```

### Utility Functions

```python
from systems.enemies.utils import (
    get_archetype_count,
    get_archetypes_by_role,
    get_archetype_stats_summary,
    get_difficulty_distribution,
)

# Get statistics
total_enemies = get_archetype_count()
distribution = get_difficulty_distribution()

# Get summary
summary = get_archetype_stats_summary("dread_knight")
print(summary)

# Find by role
all_brutes = get_archetypes_by_role("Brute")
```

### Validation

```python
from systems.enemies.validation import run_full_validation

# Validate everything
report = run_full_validation()
if report["overall_valid"]:
    print("All enemies and packs are valid!")
else:
    print(f"Found {report['archetypes']['error_count']} archetype errors")
    print(f"Found {report['packs']['error_count']} pack errors")
```

### Synergies

```python
from systems.enemies.synergies import apply_synergies_to_enemies

# Apply pack bonuses to enemies
apply_synergies_to_enemies(enemy_battle_units)
```

## Enemy Archetype Structure

```python
EnemyArchetype(
    id="unique_id",
    name="Display Name",
    role="Brute",  # Brute, Skirmisher, Invoker, Support, Elite Brute, etc.
    tier=2,  # 1=early, 2=mid, 3=late (deprecated, use difficulty_level)
    ai_profile="brute",  # brute, skirmisher, caster
    base_hp=20,
    hp_per_floor=1.8,
    base_attack=7,
    atk_per_floor=1.0,
    base_defense=2,
    def_per_floor=0.4,
    base_xp=15,
    xp_per_floor=2.0,
    skill_ids=["heavy_slam", "guard"],
    difficulty_level=42,  # 1-100+ scale
    spawn_min_floor=2,
    spawn_max_floor=6,
    spawn_weight=1.0,
    tags=["mid_game", "human", "guard", "brute", "common"],
    unique_mechanics=[],  # e.g., ["regeneration"]
    resistances={},  # e.g., {"fire": 0.0} for immunity
)
```

## Pack Template Structure

```python
EnemyPackTemplate(
    id="pack_id",
    name="Pack Name",
    tier=2,
    member_arch_ids=["enemy1", "enemy2", "enemy3"],
    preferred_room_tag="lair",  # or None
    weight=1.5,  # Relative spawn weight
)
```

## Common Tags

- **Game Phase**: `early_game`, `mid_game`, `late_game`
- **Creature Type**: `goblin`, `undead`, `beast`, `human`, `construct`, `elemental`, `demon`, `dragon`
- **Role**: `brute`, `skirmisher`, `invoker`, `caster`, `support`, `tank`
- **Rarity**: `common`, `rare`, `unique`, `elite`
- **Special**: `weak`, `fire`, `ice`, `shadow`, `void`, `chaos`

## Difficulty Ranges

- **Very Easy**: 1-20 (Tier 1 equivalent)
- **Easy**: 21-40
- **Medium**: 41-60 (Tier 2 equivalent)
- **Hard**: 61-80
- **Very Hard**: 81-100 (Tier 3 equivalent)
- **Extreme**: 100+

## Adding New Enemies

1. Choose the appropriate definition file (`early_game.py`, `mid_game.py`, or `late_game.py`)
2. Add a `register_archetype()` call with your `EnemyArchetype`
3. The enemy will be automatically registered on import

Example:
```python
# In definitions/mid_game.py
register_archetype(
    EnemyArchetype(
        id="my_new_enemy",
        name="My New Enemy",
        role="Brute",
        tier=2,
        # ... rest of fields ...
    )
)
```

## Adding New Packs

1. Add to `definitions/packs.py`
2. Use `register_pack()` with your `EnemyPackTemplate`
3. Ensure all member archetype IDs exist

Example:
```python
# In definitions/packs.py
register_pack(
    EnemyPackTemplate(
        id="my_new_pack",
        name="My New Pack",
        tier=2,
        member_arch_ids=["enemy1", "enemy2"],
        preferred_room_tag="lair",
        weight=1.0,
    )
)
```
