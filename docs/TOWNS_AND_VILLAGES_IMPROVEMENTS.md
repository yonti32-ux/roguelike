# Towns and Villages: Visual & Systems Improvements

This document outlines improvements for villages and towns in both **visuals** and **systems**, based on the current codebase.

---

## Current State Summary

### Visuals
- **Tiles**: Villages and towns use distinct tile types (path, plaza, grass, cobblestone, etc.) but **GameMap.draw()** only maps `FLOOR`, `WALL`, `UP_STAIRS`, `DOWN_STAIRS` to sprites. All village/town tiles fall through to color-only rendering (or generic floor fallback).
- **Village tiles**: Path (brown), plaza (greenish), grass (dark green), building floor/wall, entrance (door), tree.
- **Town tiles**: Cobblestone, plaza, market, grass, stone/wooden floor & wall, fountain, market stall.
- **Decorations**: Villages have trees; towns have fountains and market stalls. Layout is L-shaped paths, perimeter buildings.

### Systems
- **Village buildings**: shop, inn, tavern, town_hall, houses. NPCs: merchant, innkeeper, recruiter, elder, wandering villagers.
- **Town buildings**: shop, inn, tavern, blacksmith, library, market, town_hall, houses. NPCs include blacksmith, librarian—**but blacksmith and library are TODO** (dialogue only).
- **Quest system**: `open_quest_screen` checks `poi_type != "village"` — **towns cannot give quests** despite having a mayor.
- **Recruitment**: `open_recruitment` checks `poi_type != "village"` — **towns cannot recruit** despite having a tavern.
- **Services**: Shop and inn work. Blacksmith (upgrades), library (skill books), market (special goods) not implemented.

---

## Part 1: Visual Improvements

### 1.1 Tile Sprite Support (High Impact, Medium Effort)

**Problem**: Village/town tiles use flat colors only; no dedicated sprites.

**Solution**:
1. Add `TileSpriteType` entries for village/town tiles in `sprite_registry.py`:
   - `VILLAGE_PATH`, `VILLAGE_PLAZA`, `VILLAGE_GRASS`, `VILLAGE_BUILDING_FLOOR`, `VILLAGE_BUILDING_WALL`, `VILLAGE_ENTRANCE`, `VILLAGE_TREE`
   - `TOWN_COBBLESTONE`, `TOWN_PLAZA`, `TOWN_GRASS`, `TOWN_MARKET`, `TOWN_STONE_FLOOR`, `TOWN_WOODEN_FLOOR`, `TOWN_STONE_WALL`, `TOWN_WOODEN_WALL`, `TOWN_ENTRANCE`, `TOWN_FOUNTAIN`, `TOWN_MARKET_STALL`
2. In `game_map.py` `draw()`, add explicit checks for village/town tiles (import from `world.village.tiles` and `world.town.tiles`) and map to the new `TileSpriteType`s.
3. Create or source sprite assets for each. Until assets exist, keep color-based fallback.

**Files**: `engine/sprites/sprite_registry.py`, `world/game_map.py`, `sprites/` assets.

---

### 1.2 Richer Color Palette (Quick Win)

**Current**: Village colors are muted browns/greens; town colors are grays. Hard to distinguish at a glance.

**Improvements**:
- **Villages**: Warmer path (e.g. `(140, 110, 85)`), livelier plaza (`(95, 130, 95)`), richer grass (`(55, 110, 55)`). Slightly more saturation.
- **Towns**: Cooler stone tones, clearer plaza (`(85, 95, 115)`), distinct market area (`(120, 108, 95)`).
- **Building entrances**: Use a brighter/darker accent (e.g. door frame) so they stand out.

**Files**: `world/village/tiles.py`, `world/town/tiles.py`.

---

### 1.3 New Decorative Elements (Medium Effort)

**Villages**:
- **Well**: Non-walkable tile in plaza; sprite or distinct color.
- **Benches**: Along paths or plaza edges.
- **Flower beds**: Small clusters in grass.
- **Lamppost / torches**: Along main paths.
- **Fence sections**: Around plaza or houses.

**Towns**:
- **Street lamps**: Along cobblestone streets.
- **Benches** in plaza.
- **Statues** in plaza or at crossroads.
- **Signposts** near buildings.
- **Barrels/crates** near market.

**Implementation**: Add new tile types in `tiles.py`, place in `_place_decorative_elements()` with safe-zone logic (avoid paths, doors).

---

### 1.4 More Organic Path Layout (Medium Effort)

**Current**: Paths are L-shaped (horizontal then vertical). Very grid-like.

**Improvements**:
- Add diagonal path segments with probability.
- Occasionally branch paths (e.g. secondary path to a cluster of houses).
- **Wider main streets** in towns (2–3 tiles) vs 1 tile side paths.
- **Curved plaza edges**: Round the plaza corners for a softer look.

---

### 1.5 Building Variety by Type (Medium Effort)

**Current**: All buildings are rectangles; only size differs. Floor/wall tile is same for all.

**Improvements**:
- **Village**: Shop = wooden; inn = wooden with warmer floor; town_hall = slightly larger, maybe stone accent.
- **Town**: Already has stone vs wood by building. Add **building facade tiles** (e.g. different wall color for blacksmith vs library).
- **Roof hint**: Optional 1-tile border of darker color around building edges to suggest roof overhang.

---

### 1.6 District Layout for Towns (Higher Effort)

**Concept**: Group buildings by function:
- **Commercial**: Shop, market, blacksmith near plaza.
- **Civic**: Town hall central or prominent.
- **Residential**: Houses in clusters away from plaza.
- **Entertainment**: Tavern, inn on a “main street”.

**Implementation**: In `place_buildings()`, assign zones (e.g. quadrants) and bias building placement by type. Requires layout logic changes.

---

## Part 2: Systems Improvements

### 2.1 Fix Quest & Recruitment for Towns (Critical Bugfix, Low Effort)

**Problem**: `open_quest_screen` and `open_recruitment` only allow `poi_type == "village"`. Towns have mayors and taverns but cannot offer quests or recruitment.

**Solution**:
- Change checks to `poi_type in ("village", "town")` in both `open_quest_screen` and `open_recruitment`.
- Optionally adjust messaging: “You can only receive quests in settlements.” or “Quests are available in villages and towns.”

**Files**: `systems/village/services.py` (lines ~106, ~144, ~202).

---

### 2.2 Blacksmith Service (Medium Effort)

**Current**: Blacksmith NPC shows dialogue only; no upgrades.

**Proposed**:
- **Weapon/armor upgrades**: Spend gold to improve equipment (+damage, +armor).
- **Repair**: Restore durability if that system exists.
- **Crafting** (optional): Combine materials into new gear.
- **UI**: New “blacksmith” screen with upgrade slots, cost, and confirmation.

**Dependencies**: Item stats (upgrade tiers, max level), economy balance.

---

### 2.3 Library Service (Medium Effort)

**Current**: Librarian NPC shows dialogue only.

**Proposed**:
- **Skill books**: Purchase or borrow books that grant/improve skills or passives.
- **Lore / codex**: Unlock bestiary entries, region info, or quest hints.
- **Identify**: Identify cursed/unknown items (if relevant).
- **Research**: Unlock recipes or dungeon hints for gold.

**Implementation**: New “library” screen; link to existing codex/skill systems.

---

### 2.4 Market as Distinct from Shop (Medium Effort)

**Current**: Market building exists but may behave like a regular shop.

**Proposed**:
- **Bulk goods**: Cheaper food, potions, materials in larger quantities.
- **Rare goods**: Occasional unique or high-level items.
- **Barter / special currency**: Trade items for discounts or special stock.
- **Multiple merchants**: Several stalls with different themes (food, potions, materials).

---

### 2.5 Settlement Reputation (Optional, Higher Effort)

**Concept**: Track reputation per settlement:
- Completing quests and fair trade increases reputation.
- Theft or hostile acts decrease it.
- Effects: prices, quest availability, recruitment pool, special services.

**Implementation**: Add `reputation: float` (or similar) to POI state; update in quest turn-in, shop, recruitment. Use in price formulas and service availability.

---

### 2.6 Building Labels / Signs (Low Effort)

**Current**: Player must remember which building is which.

**Proposed**:
- When standing near a building entrance, show a tooltip: “Shop – Merchant”, “Inn – Rest”, “Town Hall – Quests”.
- Reuse `_get_nearby_entities` or similar; add building-type detection from `village_buildings` / `town_buildings`.
- Optional: Small icon or text above door.

**Files**: `engine/controllers/exploration.py`, exploration HUD.

---

### 2.7 Inn Cost Differentiation (Quick Win)

**Current**: `rest_at_inn` uses level-based cost; villages may pass `cost=0` in exploration controller.

**Proposed**:
- Villages: Cheaper rest (or free for first rest per visit).
- Towns: Slightly higher cost, maybe bonus (e.g. temporary buff, full mana restore).
- Make cost depend on POI type and level.

---

### 2.8 Time-of-Day Effects (Optional, Higher Effort)

**Concept**: Shops/inns have opening hours; some services only at certain times.

**Implementation**: Integrate with `TimeSystem`; add “open”/“closed” state to NPCs or buildings. Show “The shop is closed. Come back in the morning.” when closed. Higher effort due to UI and tuning.

---

## Part 3: Generation Improvements

### 3.1 Use Village/Town Name in Generation

**Current**: `village_name` and `town_name` are passed to generators but not used.

**Proposed**:
- Influence building count or layout from name hash.
- Themed names (e.g. “Ironforge” → more blacksmiths; “Greenleaf” → more trees).
- Use in NPC name generation for local flavor.

---

### 3.2 Level Scaling for Services

**Current**: Village/town level affects size and building count; services use player level or static values.

**Proposed**:
- Higher-level settlements: better shop stock, more companions, tougher/richer quests.
- Tie blacksmith upgrade tier and library book quality to settlement level.

---

## Priority Overview

| Priority   | Item                                      | Impact | Effort |
|-----------|-------------------------------------------|--------|--------|
| Critical  | Fix quest/recruitment for towns (2.1)     | High   | Low    |
| High      | Tile sprite support (1.1)                 | High   | Medium |
| High      | Building labels / signs (2.6)             | Medium | Low    |
| Medium    | Richer color palette (1.2)                | Medium | Low    |
| Medium    | Blacksmith service (2.2)                   | High   | Medium |
| Medium    | Library service (2.3)                     | Medium | Medium |
| Medium    | New decorative elements (1.3)             | Medium | Medium |
| Lower     | Organic paths (1.4), district layout (1.6)| Medium | Medium–High |
| Optional  | Market distinct from shop (2.4), reputation (2.5), time-of-day (2.8) | Medium–High | Medium–High |

---

## Implementation Order Suggestion

1. **Phase 1 (quick wins)** ✅ Done: Fix towns quest/recruitment (2.1), building labels (2.6), color palette (1.2).
2. **Phase 2 (visual depth)** ✅ Done: Tile sprite support (1.1), decorative elements (1.3) — well & benches in plazas.
3. **Phase 3 (new services)**: Blacksmith (2.2), library (2.3), market differentiation (2.4).
4. **Phase 4 (polish)**: Organic paths (1.4), district layout (1.6), reputation (2.5).

---

## Implemented (Summary)

| Item | Status |
|------|--------|
| Fix quest & recruitment for towns | ✅ `services.py` — allows `poi_type in ("village", "town")` |
| Richer color palette | ✅ `village/tiles.py`, `town/tiles.py` — warmer village, cooler town |
| Building labels near entrances | ✅ `hud_exploration.py` — context hints for Shop, Inn, Tavern, etc. |
| Tile sprite support | ✅ `sprite_registry.py`, `game_map.py` — registry + mapping (color fallback until assets added) |
| Decorative elements | ✅ Well + benches in village plaza; benches in town plaza |
