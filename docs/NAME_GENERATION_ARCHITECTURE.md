# Name Generation Architecture

## Overview
This document outlines a modular, extensible name generation system designed to support multiple contexts (bosses, dungeons, towns, NPCs, etc.) while keeping everything organized and reusable.

## Directory Structure

```
systems/
  namegen/
    __init__.py              # Main exports and factory functions
    base.py                  # Base generator classes and interfaces
    pools.py                 # Shared name pools and building blocks
    patterns.py              # Name pattern templates
    generators/
      __init__.py
      boss_generator.py      # Boss/mini-boss names
      dungeon_generator.py   # Dungeon/location names
      town_generator.py      # Town/village names
      character_generator.py # NPC names (future)
      place_generator.py     # Generic place names (future)
```

## Core Architecture

### 1. Base Generator (`base.py`)

```python
@dataclass
class NameGenerator:
    """Base class for all name generators."""
    context: str  # "boss", "dungeon", "town", etc.
    pools: NamePools
    
    def generate(self, **kwargs) -> str:
        """Generate a name. Subclasses override this."""
        raise NotImplementedError
```

### 2. Shared Name Pools (`pools.py`)

Shared building blocks that can be reused across generators:

- **Syllables**: Core fantasy syllables for constructing names
  - `FANTASY_SYLLABLES`: ["gor", "thak", "mal", "char", "nix", ...]
  - `BRUTAL_SYLLABLES`: ["krul", "zarg", "vor", "gorth", ...]
  - `MYSTICAL_SYLLABLES`: ["arc", "cel", "xyl", "sylph", ...]

- **Prefixes/Suffixes**: Common prefixes/suffixes
  - `DUNGEON_PREFIXES`: ["Dark", "Ancient", "Cursed", ...]
  - `DUNGEON_SUFFIXES`: ["Crypt", "Caverns", "Keep", "Temple", ...]
  - `TOWN_PREFIXES`: ["New", "Old", "Green", "Iron", ...]
  - `TOWN_SUFFIXES`: ["ville", "ton", "ham", "burgh", ...]

- **Descriptors/Adjectives**: Reusable descriptors
  - `BRUTAL_DESCRIPTORS`: ["Bloodthirsty", "Fierce", "Savage", ...]
  - `MYSTICAL_DESCRIPTORS`: ["Ancient", "Eternal", "Omnipotent", ...]
  - `DUNGEON_DESCRIPTORS`: ["Abandoned", "Forgotten", "Haunted", ...]

- **Geographical Terms**: For location names
  - `TERRAIN_TYPES`: ["Valley", "Peak", "Forest", "Marsh", ...]
  - `STRUCTURE_TYPES`: ["Tower", "Castle", "Fortress", ...]

### 3. Name Patterns (`patterns.py`)

Reusable pattern templates:

```python
@dataclass
class NamePattern:
    """Defines a pattern for generating names."""
    template: str  # "{prefix} {root}{suffix}, the {title}"
    parts: List[str]  # ["prefix", "root", "suffix", "title"]
    
PATTERNS = {
    "boss_with_title": NamePattern(
        template="{name}, the {title}",
        parts=["name", "title"]
    ),
    "dungeon_prefixed": NamePattern(
        template="{prefix} {root}{suffix}",
        parts=["prefix", "root", "suffix"]
    ),
    "town_simple": NamePattern(
        template="{prefix}{suffix}",
        parts=["prefix", "suffix"]
    ),
}
```

### 4. Context-Specific Generators

Each generator handles a specific context and can combine patterns + pools:

#### Boss Generator (`generators/boss_generator.py`)

- Uses `FANTASY_SYLLABLES` to build boss names
- Applies tiered titles from `BRUTAL_DESCRIPTORS` / `MYSTICAL_DESCRIPTORS`
- Pattern: `"{name}, the {title}"`
- Supports tier-based title selection

#### Dungeon Generator (`generators/dungeon_generator.py`)

- Combines `DUNGEON_PREFIXES` + root names + `DUNGEON_SUFFIXES`
- Examples: "Dark Crypt", "Ancient Caverns", "Cursed Temple"
- Can incorporate geographical terms

#### Town Generator (`generators/town_generator.py`)

- Uses `TOWN_PREFIXES` + `TOWN_SUFFIXES`
- Can include geographical context
- Examples: "Greenvale", "Ironburgh", "New Hampton"

## Usage Examples

```python
from systems.namegen import generate_boss_name, generate_dungeon_name

# Boss names
boss_name = generate_boss_name(tier=2)  
# -> "Gorthak, the Bloodthirsty"

# Dungeon names
dungeon_name = generate_dungeon_name()
# -> "Dark Crypt of Shadows"

# Town names
town_name = generate_town_name()
# -> "Greenvale"
```

## Design Principles

1. **Modularity**: Each generator is self-contained but can share pools
2. **Extensibility**: Easy to add new generators without touching existing code
3. **Reusability**: Shared pools prevent duplication
4. **Consistency**: Patterns ensure similar contexts produce similar structures
5. **Context-Aware**: Generators can adjust based on context (tier, level, etc.)

## Extension Points

### Adding a New Generator

1. Create new file in `systems/namegen/generators/`
2. Import base classes and pools
3. Implement `generate()` method
4. Register in `systems/namegen/__init__.py`
5. Export factory function for easy use

### Adding New Pools

1. Add pool to `systems/namegen/pools.py`
2. Organize by theme/category
3. Available to all generators via `NamePools` instance

### Custom Patterns

1. Define pattern in `patterns.py`
2. Use in generators via `apply_pattern()`
3. Patterns can be context-specific or shared

## File Organization Benefits

- **Easy to find**: All name generation code in one place
- **Easy to extend**: Add new generators without modifying existing ones
- **Easy to test**: Each generator can be tested independently
- **Easy to maintain**: Shared pools reduce duplication
- **Clear structure**: Separates concerns (pools, patterns, generators)

## Future Enhancements

- **Name caching**: Prevent duplicates (optional)
- **Name validation**: Ensure names don't conflict with reserved words
- **Localization**: Support multiple languages
- **Procedural syllables**: Generate syllables algorithmically
- **Name history**: Track generated names for consistency across sessions

