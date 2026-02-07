# Enemy Difficulty System Proposal

## ✅ Implementation Status

**Status**: Phase 1 Complete - System is live and backward compatible!

### Completed:
- ✅ Extended `EnemyArchetype` with new fields (difficulty_level, spawn_min_floor, spawn_max_floor, tags, spawn_weight)
- ✅ Added `__post_init__` for automatic backward compatibility (auto-calculates from tier)
- ✅ Updated `choose_archetype_for_floor()` to use new system with tier fallback
- ✅ Updated `choose_pack_for_floor()` to check member spawn ranges
- ✅ Added helper functions (get_enemies_by_tag, get_enemies_in_difficulty_range, etc.)
- ✅ Migrated example enemies (goblin_skirmisher, dread_knight, grave_warden)

### In Progress:
- 🔄 Migrating remaining enemy archetypes (all existing enemies work via auto-calculation)

### Next Steps:
- Update all enemy definitions with explicit new system values
- Add more tags to existing enemies
- Update pack templates to use new system
- Remove tier system (Phase 4 - after full migration)

---

## Current System Issues

The current tier system has several limitations:
- **Rigid**: Only 3 tiers (1, 2, 3)
- **Hard-coded floor ranges**: `_tier_for_floor()` uses fixed ranges (1-2, 3-4, 5+)
- **Not scalable**: Adding more difficulty levels requires code changes
- **Limited flexibility**: Can't have enemies that span multiple "tiers"
- **No granularity**: Can't have "early tier 2" vs "late tier 2" enemies

## Proposed Solutions

### Option 1: Difficulty Level System (Recommended)

Replace tiers with a **difficulty level** (1-100 scale) and **spawn range** system.

#### Benefits:
- ✅ Infinitely scalable (1-100, can go higher)
- ✅ Granular control over when enemies appear
- ✅ Easy to add new enemies without restructuring
- ✅ Can overlap spawn ranges for variety
- ✅ Backward compatible (can map old tiers to levels)

#### Implementation:

```python
@dataclass
class EnemyArchetype:
    # ... existing fields ...
    
    # Replace: tier: int
    # With:
    difficulty_level: int  # 1-100 (or higher), represents base difficulty
    spawn_min_floor: int = 1  # Earliest floor this enemy can appear
    spawn_max_floor: Optional[int] = None  # Latest floor (None = unlimited)
    spawn_weight: float = 1.0  # Relative spawn chance within valid floors
    
    # Optional: Tags for categorization
    tags: List[str] = field(default_factory=list)
    # Examples: ["early_game", "undead", "caster", "elite_candidate"]
```

#### Spawn Selection Logic:

```python
def choose_archetype_for_floor(
    floor_index: int,
    room_tag: Optional[str] = None,
    difficulty_range: Optional[Tuple[int, int]] = None,
) -> EnemyArchetype:
    """
    Pick an archetype for the given floor.
    
    Args:
        floor_index: Current floor
        room_tag: Room type tag
        difficulty_range: Optional (min_level, max_level) to filter by difficulty
    """
    # Filter by spawn range
    candidates = [
        arch for arch in ENEMY_ARCHETYPES.values()
        if arch.spawn_min_floor <= floor_index
        and (arch.spawn_max_floor is None or arch.spawn_max_floor >= floor_index)
    ]
    
    # Optional: Filter by difficulty range
    if difficulty_range:
        min_level, max_level = difficulty_range
        candidates = [
            arch for arch in candidates
            if min_level <= arch.difficulty_level <= max_level
        ]
    
    if not candidates:
        # Fallback: use any valid enemy
        candidates = [
            arch for arch in ENEMY_ARCHETYPES.values()
            if arch.spawn_min_floor <= floor_index
        ]
    
    # Calculate weights
    weights = []
    for arch in candidates:
        w = arch.spawn_weight
        
        # Room tag bonuses (existing logic)
        if room_tag == "lair" and arch.role in ("Brute", "Elite Brute"):
            w += 1.0
        if room_tag == "event" and arch.role in ("Invoker", "Support"):
            w += 0.7
        
        # Tag-based bonuses
        if room_tag == "graveyard" and "undead" in arch.tags:
            w += 1.5
        if room_tag == "sanctum" and "holy" in arch.tags:
            w += 1.5
        
        weights.append(w)
    
    return random.choices(candidates, weights=weights, k=1)[0]
```

#### Difficulty Level Mapping:

```python
# Helper function to convert old tier system to difficulty levels
def tier_to_difficulty_level(tier: int, position: str = "mid") -> int:
    """
    Convert old tier system to difficulty level.
    
    Args:
        tier: Old tier (1, 2, 3)
        position: "early", "mid", "late" within tier
    
    Returns:
        Difficulty level (1-100)
    """
    base_levels = {1: 20, 2: 50, 3: 80}
    position_offsets = {"early": -10, "mid": 0, "late": +10}
    
    base = base_levels.get(tier, 50)
    offset = position_offsets.get(position, 0)
    
    return max(1, min(100, base + offset))

# Example mappings:
# Tier 1 early: 10-20
# Tier 1 mid: 20-30
# Tier 1 late: 30-40
# Tier 2 early: 40-50
# Tier 2 mid: 50-60
# Tier 2 late: 60-70
# Tier 3 early: 70-80
# Tier 3 mid: 80-90
# Tier 3 late: 90-100
```

#### Floor to Difficulty Range:

```python
def floor_to_difficulty_range(floor_index: int, spread: int = 15) -> Tuple[int, int]:
    """
    Convert floor index to a difficulty level range.
    
    Args:
        floor_index: Current floor
        spread: How wide the difficulty range should be
    
    Returns:
        (min_level, max_level) tuple
    """
    # Linear scaling: floor 1 = level 10, floor 10 = level 100
    # Adjust formula as needed
    base_level = 10 + (floor_index - 1) * 9  # Roughly 10 per floor
    
    min_level = max(1, base_level - spread)
    max_level = min(100, base_level + spread)
    
    return (min_level, max_level)
```

---

### Option 2: Tag-Based System

Use tags instead of tiers for categorization.

#### Benefits:
- ✅ Very flexible
- ✅ Multiple tags per enemy
- ✅ Easy to query ("all undead enemies", "all casters")
- ✅ Can combine tags for complex filtering

#### Implementation:

```python
@dataclass
class EnemyArchetype:
    # ... existing fields ...
    
    # Replace tier with tags
    tags: List[str] = field(default_factory=list)
    # Examples:
    # - ["early_game", "skirmisher", "goblin"]
    # - ["mid_game", "brute", "undead"]
    # - ["late_game", "caster", "elite"]
    
    spawn_min_floor: int = 1
    spawn_max_floor: Optional[int] = None
    spawn_weight: float = 1.0
```

#### Spawn Selection:

```python
def choose_archetype_for_floor(
    floor_index: int,
    room_tag: Optional[str] = None,
    required_tags: Optional[List[str]] = None,
    excluded_tags: Optional[List[str]] = None,
) -> EnemyArchetype:
    """
    Pick an archetype using tag-based filtering.
    """
    candidates = [
        arch for arch in ENEMY_ARCHETYPES.values()
        if arch.spawn_min_floor <= floor_index
        and (arch.spawn_max_floor is None or arch.spawn_max_floor >= floor_index)
    ]
    
    # Filter by required tags
    if required_tags:
        candidates = [
            arch for arch in candidates
            if all(tag in arch.tags for tag in required_tags)
        ]
    
    # Filter by excluded tags
    if excluded_tags:
        candidates = [
            arch for arch in candidates
            if not any(tag in arch.tags for tag in excluded_tags)
        ]
    
    # ... rest of selection logic ...
```

---

### Option 3: Hybrid System (Best of Both)

Combine difficulty level + tags + spawn ranges.

#### Benefits:
- ✅ Maximum flexibility
- ✅ Can filter by difficulty OR tags OR both
- ✅ Backward compatible
- ✅ Future-proof

#### Implementation:

```python
@dataclass
class EnemyArchetype:
    # ... existing fields ...
    
    # Difficulty system
    difficulty_level: int  # 1-100
    spawn_min_floor: int = 1
    spawn_max_floor: Optional[int] = None
    spawn_weight: float = 1.0
    
    # Tag system for categorization
    tags: List[str] = field(default_factory=list)
    
    # Optional: Keep tier for backward compatibility
    tier: Optional[int] = None  # Deprecated, use difficulty_level
    
    # Optional: Spawn conditions
    spawn_conditions: Dict[str, Any] = field(default_factory=dict)
    # Examples:
    # {"min_player_level": 5, "required_room_tag": "lair"}
```

---

## Recommended Approach: Option 3 (Hybrid)

### Migration Strategy

1. **Phase 1: Add new fields, keep tier**
   - Add `difficulty_level`, `spawn_min_floor`, `spawn_max_floor`, `tags`
   - Keep `tier` field for backward compatibility
   - Auto-calculate difficulty_level from tier if not provided

2. **Phase 2: Update spawn logic**
   - Update `choose_archetype_for_floor()` to use new system
   - Keep fallback to tier system
   - Add tag-based filtering

3. **Phase 3: Migrate existing enemies**
   - Convert all existing enemies to use new system
   - Remove tier field (or mark as deprecated)

4. **Phase 4: Remove tier system**
   - Remove `_tier_for_floor()` function
   - Remove tier field from EnemyArchetype
   - Update all references

### Example Migration:

```python
# Old system
register_archetype(
    EnemyArchetype(
        id="goblin_skirmisher",
        name="Goblin Skirmisher",
        role="Skirmisher",
        tier=1,  # Old way
        # ... rest ...
    )
)

# New system
register_archetype(
    EnemyArchetype(
        id="goblin_skirmisher",
        name="Goblin Skirmisher",
        role="Skirmisher",
        difficulty_level=15,  # New way
        spawn_min_floor=1,
        spawn_max_floor=5,  # Can appear floors 1-5
        spawn_weight=1.5,  # More common
        tags=["early_game", "skirmisher", "goblin", "common"],
        tier=1,  # Keep for backward compat during migration
        # ... rest ...
    )
)
```

---

## Implementation Plan

### Step 1: Extend EnemyArchetype (Non-Breaking)

```python
@dataclass
class EnemyArchetype:
    # ... existing required fields ...
    tier: int  # Keep existing
    
    # New optional fields
    difficulty_level: Optional[int] = None
    spawn_min_floor: Optional[int] = None
    spawn_max_floor: Optional[int] = None
    spawn_weight: float = 1.0
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Auto-calculate difficulty_level from tier if not provided."""
        if self.difficulty_level is None:
            # Map tier to difficulty level
            tier_to_level = {1: 25, 2: 55, 3: 85}
            self.difficulty_level = tier_to_level.get(self.tier, 50)
        
        if self.spawn_min_floor is None:
            # Map tier to spawn range
            tier_to_min_floor = {1: 1, 2: 3, 3: 5}
            self.spawn_min_floor = tier_to_min_floor.get(self.tier, 1)
        
        if self.spawn_max_floor is None:
            # Default: can spawn up to 2 floors after tier ends
            tier_to_max_floor = {1: 3, 2: 6, 3: None}  # None = unlimited
            self.spawn_max_floor = tier_to_max_floor.get(self.tier, None)
```

### Step 2: Update Spawn Functions

```python
def choose_archetype_for_floor(
    floor_index: int,
    room_tag: Optional[str] = None,
) -> EnemyArchetype:
    """
    Pick an archetype using new system with fallback to tier.
    """
    # Try new system first
    candidates = [
        arch for arch in ENEMY_ARCHETYPES.values()
        if arch.spawn_min_floor <= floor_index
        and (arch.spawn_max_floor is None or arch.spawn_max_floor >= floor_index)
    ]
    
    # Fallback to tier system if no candidates
    if not candidates:
        tier = _tier_for_floor(floor_index)
        candidates = [a for a in ENEMY_ARCHETYPES.values() if a.tier == tier]
    
    # ... rest of selection logic ...
```

### Step 3: Add Helper Functions

```python
def get_enemies_by_tag(tag: str) -> List[EnemyArchetype]:
    """Get all enemies with a specific tag."""
    return [arch for arch in ENEMY_ARCHETYPES.values() if tag in arch.tags]

def get_enemies_in_difficulty_range(min_level: int, max_level: int) -> List[EnemyArchetype]:
    """Get all enemies within a difficulty range."""
    return [
        arch for arch in ENEMY_ARCHETYPES.values()
        if min_level <= arch.difficulty_level <= max_level
    ]

def get_enemies_for_floor_range(min_floor: int, max_floor: int) -> List[EnemyArchetype]:
    """Get all enemies that can spawn in a floor range."""
    return [
        arch for arch in ENEMY_ARCHETYPES.values()
        if arch.spawn_min_floor <= max_floor
        and (arch.spawn_max_floor is None or arch.spawn_max_floor >= min_floor)
    ]
```

---

## Benefits of New System

1. **Scalability**: Add enemies at any difficulty level (1-100+)
2. **Flexibility**: Overlapping spawn ranges create variety
3. **Modularity**: Tags allow easy categorization and filtering
4. **Backward Compatible**: Can migrate gradually
5. **Future-Proof**: Easy to add new features (spawn conditions, etc.)

## Example Use Cases

### Use Case 1: Add a "Very Early" Enemy
```python
register_archetype(
    EnemyArchetype(
        id="weak_skeleton",
        difficulty_level=5,  # Very easy
        spawn_min_floor=1,
        spawn_max_floor=2,  # Only appears floors 1-2
        tags=["early_game", "undead", "weak"],
        # ... rest ...
    )
)
```

### Use Case 2: Add a "Mid-Late" Enemy
```python
register_archetype(
    EnemyArchetype(
        id="elite_guardian",
        difficulty_level=75,  # Hard
        spawn_min_floor=4,
        spawn_max_floor=None,  # Can appear from floor 4 onwards
        tags=["mid_game", "late_game", "elite", "tank"],
        # ... rest ...
    )
)
```

### Use Case 3: Tag-Based Queries
```python
# Get all undead enemies
undead = get_enemies_by_tag("undead")

# Get all early game enemies
early = get_enemies_by_tag("early_game")

# Get enemies for a specific floor range
floor_3_5 = get_enemies_for_floor_range(3, 5)
```

---

## Recommendation

**Use Option 3 (Hybrid System)** because:
- ✅ Maximum flexibility for future expansion
- ✅ Backward compatible with existing code
- ✅ Easy to migrate gradually
- ✅ Supports both difficulty-based and tag-based filtering
- ✅ Can add more features later (spawn conditions, etc.)

**Migration Path**: Implement in phases, keeping tier system as fallback until fully migrated.

---

## Implementation Examples

### Example 1: Early Game Enemy (Migrated)
```python
register_archetype(
    EnemyArchetype(
        id="goblin_skirmisher",
        name="Goblin Skirmisher",
        role="Skirmisher",
        tier=1,  # Kept for backward compatibility
        # ... stats ...
        # New difficulty system (explicit values)
        difficulty_level=15,  # Early game enemy
        spawn_min_floor=1,
        spawn_max_floor=4,  # Can appear floors 1-4
        spawn_weight=1.5,  # Common enemy
        tags=["early_game", "goblin", "skirmisher", "common"],
    )
)
```

### Example 2: Late Game Elite (Migrated)
```python
register_archetype(
    EnemyArchetype(
        id="dread_knight",
        name="Dread Knight",
        role="Elite Brute",
        tier=3,  # Kept for backward compatibility
        # ... stats ...
        # New difficulty system
        difficulty_level=85,  # Late game elite enemy
        spawn_min_floor=5,
        spawn_max_floor=None,  # Can appear from floor 5 onwards
        spawn_weight=1.0,
        tags=["late_game", "elite", "brute", "undead"],
    )
)
```

### Example 3: Unique Room Enemy (Migrated)
```python
register_archetype(
    EnemyArchetype(
        id="grave_warden",
        name="Grave Warden",
        role="Elite Support",
        tier=2,  # Kept for backward compatibility
        # ... stats ...
        # New difficulty system - unique room enemy
        difficulty_level=60,  # Mid-late game unique
        spawn_min_floor=3,
        spawn_max_floor=8,  # Spawns in mid-game range
        spawn_weight=0.3,  # Rare spawn (unique enemy)
        tags=["mid_game", "late_game", "elite", "undead", "unique", "graveyard"],
    )
)
```

### Example 4: Using Helper Functions
```python
# Get all undead enemies
undead_enemies = get_enemies_by_tag("undead")

# Get enemies for difficulty range 40-60
mid_game_enemies = get_enemies_in_difficulty_range(40, 60)

# Get enemies that can spawn on floors 3-5
floor_3_5_enemies = get_enemies_for_floor_range(3, 5)

# Convert floor to difficulty range
min_level, max_level = floor_to_difficulty_range(floor_index=5, spread=15)
# Returns: (40, 70) - enemies in this range can spawn on floor 5
```

---

## Usage Guide

### For New Enemies:
Always specify the new system fields explicitly:
```python
register_archetype(
    EnemyArchetype(
        # ... required fields ...
        difficulty_level=25,  # Explicit difficulty
        spawn_min_floor=2,
        spawn_max_floor=6,
        spawn_weight=1.2,
        tags=["mid_game", "beast", "common"],
    )
)
```

### For Existing Enemies:
They work automatically via `__post_init__`, but you can override:
```python
# Old way (still works)
register_archetype(EnemyArchetype(..., tier=1, ...))

# New way (recommended)
register_archetype(EnemyArchetype(..., tier=1, difficulty_level=15, spawn_min_floor=1, ...))
```

### Tag-Based Spawning:
The spawn system now checks tags for room-based bonuses:
- `room_tag="graveyard"` + `tag="undead"` → +1.5 weight bonus
- `room_tag="sanctum"` + `tag="holy"` → +1.5 weight bonus
- `room_tag="lair"` + `tag="beast"` → +1.0 weight bonus
