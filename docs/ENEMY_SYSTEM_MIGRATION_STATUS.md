# Enemy System Migration Status

## Overview
This document tracks the migration from the old tier-based system to the new modular difficulty system.

**Last Updated**: Implementation Phase 1 Complete

---

## Migration Progress

### Phase 1: Foundation ✅ COMPLETE
- [x] Extended `EnemyArchetype` with new fields
- [x] Added `__post_init__` for backward compatibility
- [x] Updated spawn functions to use new system
- [x] Added helper functions
- [x] Migrated 3 example enemies

### Phase 2: Full Migration ✅ COMPLETE
- [x] Migrate all Tier 1 enemies (7 total) - **DONE**
- [x] Migrate all Tier 2 enemies (7 total) - **DONE**
- [x] Migrate all Tier 3 enemies (5 total) - **DONE**
- [x] Migrate unique room enemies (4 total) - **DONE**
- [x] Add tags to all enemies - **DONE**

### Phase 3: Pack System
- [ ] Update pack templates to use new system
- [ ] Add pack-level tags
- [ ] Update pack spawn logic

### Phase 4: Cleanup
- [ ] Remove `tier` field (mark as deprecated first)
- [ ] Remove `_tier_for_floor()` function
- [ ] Update all documentation

---

## Enemy Migration Checklist

### Tier 1 Enemies (Early Game) ✅ COMPLETE
- [x] goblin_skirmisher - **MIGRATED** (difficulty_level=15, floors 1-4, common)
- [x] goblin_brute - **MIGRATED** (difficulty_level=18, floors 1-4, common)
- [x] bandit_cutthroat - **MIGRATED** (difficulty_level=17, floors 1-5, common)
- [x] cultist_adept - **MIGRATED** (difficulty_level=20, floors 1-4, common)
- [x] goblin_shaman - **MIGRATED** (difficulty_level=19, floors 1-4, common)
- [x] skeleton_archer - **MIGRATED** (difficulty_level=16, floors 1-5, common)
- [x] dire_rat - **MIGRATED** (difficulty_level=12, floors 1-3, common, weak)

### Tier 2 Enemies (Mid Game) ✅ COMPLETE
- [x] ghoul_ripper - **MIGRATED** (difficulty_level=48, floors 3-7, common)
- [x] orc_raider - **MIGRATED** (difficulty_level=52, floors 3-8, common)
- [x] dark_adept - **MIGRATED** (difficulty_level=55, floors 3-7, common)
- [x] necromancer - **MIGRATED** (difficulty_level=50, floors 3-8, common)
- [x] shadow_stalker - **MIGRATED** (difficulty_level=53, floors 4-8, common)
- [x] stone_golem - **MIGRATED** (difficulty_level=58, floors 4-8, common, tank)
- [x] banshee - **MIGRATED** (difficulty_level=57, floors 4-8, common)

### Tier 3 Enemies (Late Game) ✅ COMPLETE
- [x] dread_knight - **MIGRATED** (difficulty_level=85, floors 5+, common)
- [x] voidspawn_mauler - **MIGRATED** (difficulty_level=82, floors 5+, common)
- [x] cultist_harbinger - **MIGRATED** (difficulty_level=83, floors 5+, common)
- [x] lich - **MIGRATED** (difficulty_level=88, floors 6+, rare, elite)
- [x] dragonkin - **MIGRATED** (difficulty_level=87, floors 6+, rare, elite)

### Unique Room Enemies ✅ COMPLETE
- [x] grave_warden - **MIGRATED** (difficulty_level=60, floors 3-8, rare, unique)
- [x] sanctum_guardian - **MIGRATED** (difficulty_level=62, floors 4-8, rare, unique)
- [x] pit_champion - **MIGRATED** (difficulty_level=90, floors 6+, rare, unique)
- [x] hoard_mimic - **MIGRATED** (difficulty_level=65, floors 4-8, rare, unique)

---

## Tag System

### Standard Tags
- `early_game` - Appears in early floors
- `mid_game` - Appears in mid floors
- `late_game` - Appears in late floors
- `common` - Common spawn
- `rare` - Rare spawn
- `unique` - Unique enemy
- `elite` - Elite enemy candidate

### Faction Tags
- `goblin` - Goblin faction
- `undead` - Undead faction
- `beast` - Beast faction
- `cultist` - Cultist faction
- `orc` - Orc faction

### Role Tags
- `skirmisher` - Skirmisher role
- `brute` - Brute role
- `caster` - Caster role
- `support` - Support role
- `invoker` - Invoker role

### Room-Specific Tags
- `graveyard` - Spawns in graveyard rooms
- `sanctum` - Spawns in sanctum rooms
- `lair` - Spawns in lair rooms
- `treasure` - Spawns in treasure rooms

---

## Difficulty Level Guidelines

### Mapping Tier to Difficulty Level
- **Tier 1**: 10-30 (Early game)
  - Very Easy: 10-15
  - Easy: 15-20
  - Normal: 20-25
  - Hard: 25-30

- **Tier 2**: 40-60 (Mid game)
  - Easy: 40-45
  - Normal: 45-50
  - Hard: 50-55
  - Very Hard: 55-60

- **Tier 3**: 70-90 (Late game)
  - Normal: 70-75
  - Hard: 75-80
  - Very Hard: 80-85
  - Elite: 85-90

- **Bosses**: 90-100+
  - Mini-bosses: 90-95
  - Final bosses: 95-100+

### Spawn Range Guidelines
- **Early game enemies**: spawn_min_floor=1, spawn_max_floor=3-5
- **Mid game enemies**: spawn_min_floor=3-4, spawn_max_floor=6-8
- **Late game enemies**: spawn_min_floor=5+, spawn_max_floor=None (unlimited)
- **Unique enemies**: Narrower ranges, lower spawn_weight

### Spawn Weight Guidelines
- **Common enemies**: 1.5-2.0
- **Normal enemies**: 1.0
- **Rare enemies**: 0.5-0.7
- **Unique enemies**: 0.2-0.4

---

## Testing Checklist

- [ ] All existing enemies spawn correctly (backward compatibility)
- [ ] New system enemies spawn in correct floor ranges
- [ ] Tag-based room bonuses work
- [ ] Helper functions return correct results
- [ ] Pack system works with new spawn ranges
- [ ] No performance regressions

---

## Notes

- All existing enemies work automatically via `__post_init__`
- Migration can be done gradually, one enemy at a time
- New enemies should always use the new system explicitly
- Tags are optional but recommended for better categorization
