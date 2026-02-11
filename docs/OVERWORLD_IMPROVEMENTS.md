# Overworld & Systems Improvement Suggestions

This document suggests improvements to the overworld and its related systems, based on the current codebase and existing design docs (`QUEST_AND_EVENT_POI_WHEN_YOU_REACH.md`, `QUEST_AND_TEMPORARY_POI_PLAN.md`, `FEATURE_IMPROVEMENT_SUGGESTIONS.md`).

---

## Current State Summary

| System | What Exists |
|--------|-------------|
| **Map** | 2D grid, terrain (grass/forest/mountain/water), bounds, walkability |
| **Time** | Time advances per move via `terrain_costs`; `movement_cost_base`; time used for exploration timeout |
| **Exploration** | Sight radius, `explored_tiles` with timestamp; tiles fade after `memory_timeout_hours` |
| **POIs** | Permanent + temporary (quest/event); add/remove; discover on enter/sight; cleared/destroyed state |
| **Roads** | Generated (town–town, village–village, etc.), rendered; **not used for movement cost** |
| **Parties** | Roaming parties, spawn on timer, AI (pathfinding, party-vs-party combat, hunt/prey flee), faction alignment, join battle (J); **speed** = move probability per player move (capped at 1.0); **spawn categories** (WILDLIFE / HUMANOID / UNDEAD) for modular spawns |
| **Factions** | FactionManager, relations, territory (chunk-based, optional overlay) |
| **Random events** | Cooldown + chance per move; spawn temp POIs (hostile camp, merchant, ruins); expiry; max 3 at once |
| **Quests** | Elder/town quests; real or temp POIs; quest map markers (gold + ring); turn-in removes temp POI |

---

## Done Overworld Improvements (summary)

Implemented and in use:

| # | Improvement | Where |
|---|-------------|--------|
| 1.1 | Road movement cost | `OverworldConfig.road_movement_multiplier`; `try_move()` applies it when on road |
| 1.4 B | Multiple moves per turn for fast parties | `party_ai.update_party_ai()`: speed &gt; 1.0 → chance of 2 moves |
| 2.1 | Exploration timeout from config | `OverworldConfig.memory_timeout_hours`; single source for fog-of-war fade |
| 2.2 | Minimap | Toggle **M**; 96×96 corner map, terrain + POIs + player |
| 2.3 | Discovery log / codex | **L**; scrollable list of discovered POIs with cleared state |
| 3.4 | Hunt mechanic (natural parties) | Prey (deer, rabbit) + predators (wolf, bear, fox, etc.); instant hunt → hunt XP; XP scales power |
| 3.4 | Prey flee | Prey flee from nearby natural predators within sight |
| 3.5 | Spawn categories (modular spawn pools) | `SpawnCategory` (WILDLIFE / HUMANOID / UNDEAD); `spawn_random_party(spawn_category=...)`; `party_types_for_spawn_category()` |

---

## 1. Movement & Time

### 1.1 Road movement cost (high value, low effort) ✅ Done

**Problem**: Roads are generated and drawn but have no gameplay effect. Walking on a road is the same as walking on grass.

**Solution (implemented)**:

- `OverworldConfig` has `road_movement_multiplier: float = 0.7` (in `config.py`; load/save under `time`).
- In `try_move()` (overworld controller), after terrain cost: if `overworld_map.road_manager` exists and `road_manager.has_road_at(new_x, new_y)`, multiply cost by `config.road_movement_multiplier` before `add_time()`.
- `RoadManager.has_road_at(x, y)` is used for the check.

**Impact**: Roads are faster; players have a reason to follow them.  
**Status**: Implemented.

### 1.2 Diagonal vs cardinal cost (optional)

**Problem**: Diagonal moves cost the same as cardinal moves but cover more distance; can make movement feel samey.

**Solution**: Option in config (e.g. `diagonal_cost_multiplier: 1.4`) and in `try_move()` multiply time cost when `dx != 0 and dy != 0`. Keeps one-move-per-keypress but makes diagonals “cost” more time.

**Effort**: Low.

### 1.3 Time of day / day–night (optional, higher effort)

**Problem**: Time passes but there’s no visible day/night or time-of-day effects on overworld.

**Solution**: If `TimeSystem` exposes time of day (e.g. hour 0–23 or phase “dawn/day/dusk/night”):

- Overworld HUD could show “Dawn”, “Noon”, “Dusk”, “Night” or a small clock.
- Optional: slight tint or brightness change for the overworld view by time of day; or POI/party behavior (e.g. “bandits more active at night”) later.

**Effort**: Medium (UI + optional rendering); high if you add many time-of-day mechanics.

### 1.4 Time and movement balance with parties (critical for chase/escape)

**Problem**: Time and movement must be balanced so that parties can meaningfully catch or escape each other (and the player). Right now:

- **Player**: 1 tile per keypress; game time advances by terrain cost (e.g. 1 h grass, 2 h mountain). So “tiles per hour” varies by route (roads would make the player faster in time).
- **Parties**: Updated once per player move. Each party gets one “tick” and moves with probability `min(1.0, party_type.speed)`. So:
  - **Speed &lt; 1.0** (e.g. merchant 0.7): moves only some of the time → can be caught.
  - **Speed ≥ 1.0**: always moves once per player move → **capped at 1 tile per player move**. So fast parties (1.3, 1.5) never get to move *more* than the player in tiles per keypress.

So with equal “1 move per turn” for player and fast parties, they can never catch each other; only slower parties can be caught. The world clock (hours) is not used for party movement—only a simple “+1.0” counter per player move—so road/terrain time costs don’t change how far parties move relative to the player.

**Goals**:

1. **Relative speed in time**: Over the same in-game hours, a “fast” party should cover more tiles than a “slow” party, so chases and escapes are possible.
2. **Consistency with terrain/roads**: If the player spends more time per tile (e.g. mountains), parties should get *more* movement in that same time; if the player uses roads (less time per tile), parties get *fewer* steps. Then “take the fast route” is a real way to outrun or avoid parties.

**Solution A – Time-based party movement (recommended)**  

Tie party movement to **elapsed game time** instead of “one tick per player move”:

1. When the player moves, compute **time delta** = terrain cost × movement_cost_base (and road multiplier if 1.1 is in). Pass this `time_delta_hours` into `PartyManager.update_on_player_move(time_delta_hours=...)`.
2. Define a constant, e.g. **base tiles per hour** at speed 1.0 (e.g. `PARTY_TILES_PER_HOUR = 1.0` or 2.0 so parties don’t feel sluggish).
3. For each party: **movement steps this tick** = `time_delta_hours * PARTY_TILES_PER_HOUR * party_type.speed`. Use floor or fractional accumulation (e.g. store `party.movement_accumulator += steps`, take `int(accumulator)` moves, keep remainder).
4. Run the party AI **that many times** (each run = one tile move attempt) for this party during this update. Cooldowns (rest, resupply) can stay in “ticks” or be converted to hours; battles still one update per “player move” or per N party steps, as you prefer.

Result:

- **Fast party (speed 1.5)** in 2 hours gets ~3 steps; **slow party (0.7)** gets ~1.4 → fast can catch slow.
- **Player on road** (0.7 h per tile): 10 tiles = 7 h → parties get 7× base steps. **Player in mountains** (2 h per tile): 10 tiles = 20 h → parties get 20× base steps. So the player can “outrun” by choosing fast terrain/roads (less time = fewer party steps).

**Solution B – Multiple moves per turn for fast parties (simpler, no time tie-in)** ✅ Done  

Keep “one update per player move” but allow **multiple tile moves** when speed &gt; 1.0:

- `moves_this_turn = 1` if speed ≤ 1.0, else 2 with probability `min(1.0, speed - 1.0)` (e.g. speed 1.5 → 50% chance 2 moves).
- Run the movement step of the AI `moves_this_turn` times for that party.

Implemented in `party_ai.py`: `_do_one_movement_step()` does one step; `update_party_ai()` computes `num_moves` (1 or 2) and loops. Fast parties can catch slow ones and the player. Combined with road movement cost (1.1), the player can save time by using roads (fewer hours per tile) while fast parties still get at most 2 moves per keypress.

**Recommendation**: Solution A so that (1) relative party speeds matter in a consistent way (tiles per hour), and (2) road/terrain movement cost (and any future time-based mechanics) naturally balance with party movement. Add a config: `party_tiles_per_hour` (default e.g. 1.0) and optionally `party_terrain_costs: true` so parties also pay terrain cost per step (so they’re slower in mountains too). That keeps chase/escape and “fast route vs slow route” all in one coherent time/movement model.

**Effort**: Medium (change `update_on_player_move` signature, pass time delta from controller, loop party AI by steps; tune `PARTY_TILES_PER_HOUR` and cooldowns).

---

## 2. Exploration

### 2.1 Fog of war consistency ✅ Done

**Problem**: `is_explored` uses a timeout; config has `memory_timeout_hours` (e.g. 12) while code default is 2.0 hours. HUD may use a different value than the one in config.

**Solution (implemented)**:

- Single source of truth: `OverworldConfig.memory_timeout_hours` (default 12.0). Used in HUD, road renderer, territory overlay; `map.is_explored()` default updated to 12.0; config docstring states it is used for fog-of-war fade everywhere.
- Territory renderer accepts `timeout_hours` (default 12.0) so callers can pass config.

**Status**: Implemented.

### 2.2 Minimap or “you are here” indicator ✅ Done

**Problem**: On large maps it’s easy to get lost; no minimap or compact overview.

**Solution (implemented)**:

- **Minimap**: Small corner map (96×96) in bottom-right showing terrain (with fog: dimmed unexplored/expired), discovered POIs as dots, player as yellow dot. Toggle with **M** key. Position already shown in top-left panel.

**Status**: Implemented.

### 2.3 Discovery log / codex ✅ Done

**Problem**: Discovering a POI only gives a one-off message; no persistent list of discovered locations.

**Solution (implemented)**:

- `OverworldMap.discovery_log`: list of `{poi_id, name, poi_type, level, cleared}`. `record_discovery(poi)` called whenever a POI is discovered (controller + game init). Cleared state shown from current POI when still on map, else stored value.
- Save/load: `discovery_log` serialized/restored with overworld in save system.
- UI: **L** key toggles “Discovery Log” overlay (scrollable list with name, type, level, cleared/active). ESC or L to close; mouse wheel and arrow keys to scroll.

**Status**: Implemented.

---

## 3. Parties & Faction Combat

### 3.1 Party visibility and behavior by relationship

**Problem**: It’s not always obvious which parties are hostile vs neutral vs friendly before interacting.

**Solution**:

- Tooltips (and optionally party marker color/shape) reflect effective alignment: e.g. “Hostile (faction)”, “Friendly”, “Neutral”. Reuse `get_effective_alignment` from faction_combat so tooltip text and color stay in sync with join-battle logic.
- Optional: hostile parties could have a different icon or outline so the player can read the map at a glance.

**Effort**: Low (tooltip + optional art).

### 3.2 Party density and spawn tuning

**Problem**: Spawn rate and max parties are fixed (`spawn_interval: 15`, `max_parties: 100`); may feel too dense or too empty depending on map size and playstyle.

**Solution**: Move to config (e.g. in `overworld_settings.json` under `parties`: `spawn_interval`, `max_parties`, maybe `spawn_near_poi_chance`). Allows tuning without code changes and per-world presets.

**Effort**: Low.

### 3.3 Escort / “follow me” or “meet at POI” (quest hook)

**Problem**: Quests are mostly “go to POI / kill / explore”; no overworld escort or “meet ally at X”.

**Solution**: Use existing party system: spawn a temporary “quest ally” party that pathfinds toward a target POI; quest completes when that party reaches the POI or when the player “delivers” them (e.g. interact at destination). Reuses `RoamingParty` + `PartyManager`; new quest type or objective (e.g. ESCORT with `target_poi_id` and optional `escort_party_id`).

**Effort**: Medium–high (quest objective type + party spawn/ownership + completion condition).

### 3.4 Hunt mechanic (natural parties) ✅ Done

**Implemented**: Natural animal parties (wolves, bears, dire wolves, boar, spider) can **hunt prey** (e.g. deer). When a natural creature is adjacent to prey and they’re enemies: instant hunt (prey removed, hunter gains **hunt XP**). XP scales power in `get_party_power()` (up to +25% at 200 XP). Same XP grant when a natural party wins a multi-turn battle vs prey.

- **PartyType**: `is_natural_creature`, `is_prey`. **RoamingParty**: `xp`.
- **Future**: Prey flee from natural creatures in sight (FLEE when prey sees hunter). Loot/drops from hunted prey. When overworld parties are serialized in save/load, include `xp` so experienced packs persist.

**Status**: Implemented.

### 3.5 Spawn categories (modular spawn pools) ✅ Done

**Implemented**: Party types have a **spawn category** (`SpawnCategory`: `ALL`, `WILDLIFE`, `HUMANOID`, `UNDEAD`). `PartyManager.spawn_random_party(..., spawn_category=SpawnCategory.WILDLIFE)` spawns only from that pool; `spawn_category=None` (default) uses all types (unchanged behavior). Helper: `party_types_for_spawn_category(category)` (when category is `ALL`, returns all types).

- **WILDLIFE**: deer, rabbit, bird, wolf, bear, fox, dire_wolf, spider, boar, rat_swarm.
- **UNDEAD**: skeleton, ghoul, zombie, wraith, necromancer_cult.
- **HUMANOID**: everyone else (merchant, bandit, guard, orc, goblin, etc.).
- **ALL**: reserved for types that should appear in any filtered pool; currently unused.

Use for biome/region spawns later (e.g. forest = mostly wildlife, road = humanoid, ruins = undead). See **Done Overworld Improvements** above.

---

## 4. POIs & Random Events

### 4.1 Event variety and pacing

**Problem**: Random events are good but limited to a few templates (hostile camp, merchant, ruins); same trigger logic for all.

**Solution**:

- **More event types**: e.g. “Wandering healer” (one-off heal/rest), “Distressed traveler” (small quest or info), “Blocked road” (temporary obstacle or mini-encounter). Reuse same pattern: `try_trigger_random_event` → pick category → spawn temp POI with `source_event_id` and expiry.
- **Pacing**: Optional “event fatigue” so that after N events in a short time (or in a region), chance drops until the player moves a lot or time passes. Prevents event spam in one area.

**Effort**: Medium (new POI types or camp variants + optional fatigue counter).

### 4.2 Temporary POI placement rules

**Problem**: Event POIs spawn at random walkable tiles; can land on roads or in odd terrain.

**Solution**: Prefer or require certain terrain (e.g. forest/grass for camps, not water); optionally avoid road tiles so events feel “off the road”. Reuse `_find_spawn_position` with extra filters (terrain type, `is_on_road` if available).

**Effort**: Low.

### 4.3 Quest POI persistence and “ruins” state

**Current**: Quest hostile camps are marked cleared/destroyed on victory; re-entry shows “ruins”; POI removed only on turn-in. Event hostile camps are removed from map on clear. Documented in `QUEST_AND_EVENT_POI_WHEN_YOU_REACH.md`.

**Improvement**: Optional “remove quest camp from map on clear” (like events) for a cleaner map; or keep current behavior and add a HUD hint (“Quest target cleared – return to elder to complete”).

**Effort**: Low (config or single branch).

---

## 5. World Structure & Generation

### 5.1 Regions or “named areas”

**Problem**: Map is one flat grid; no sense of “the Northern Woods” or “Kingdom of X”. Territory is chunk-based but not necessarily named.

**Solution**: Introduce optional **regions**: names and boundaries (e.g. per-chunk or per-POI). Use for: HUD “Current region: …”, discovery log “Region: …”, and later for region-specific events or difficulty. Can be generated from terrain clusters + POI ownership (faction) or from a simple grid of region IDs.

**Effort**: Medium (generation + storage + HUD); high if you add region-specific content.

### 5.2 Starting location and difficulty curve

**Problem**: Starting location type is configurable (“random” vs fixed); level scaling is by distance. No explicit “safe zone” vs “danger zone”.

**Solution**: Ensure starting area is always walkable and has at least one “safe” POI (village/town). Optionally tag a “starting region” and scale difficulty down there (e.g. lower party level or fewer hostile spawns). Keeps early game predictable without removing exploration.

**Effort**: Low–medium (generation + optional difficulty mask).

### 5.3 Road connectivity and gameplay

**Problem**: Roads connect POIs but aren’t used for movement (see 1.1). No “follow road” or “nearest road” logic.

**Solution**: After 1.1 (road movement cost), optionally add: “Nearest road” query for AI or for a “Snap to road” / “Follow road” movement mode (higher effort). At minimum, making roads faster (1.1) already improves connectivity in practice.

**Effort**: Low for 1.1; medium+ for follow-road AI/mode.

---

## 6. Overworld UI & Feedback

### 6.1 Quest distance / “nearest objective” HUD

**Problem**: Player knows which POIs are quest targets (gold + ring) but not which is closest or how far.

**Solution**: Small HUD line: “Nearest quest: [POI name] – N tiles” or a compass arrow. Use `get_player_position` and `get_pois_in_range` / distance to quest objective POIs; sort by distance and show first. Optional: only when a single “go here” objective is active.

**Effort**: Low.

### 6.2 Time and travel cost preview

**Problem**: Player doesn’t know how much time a move will take until after moving.

**Solution**: On hover (or on a “destination” cursor), show “Travel time: ~X hours” for the tile under cursor (using same terrain + road cost logic as `try_move`). Requires a “pending” or “hover” tile and one shared cost function.

**Effort**: Low–medium.

### 6.3 Overworld message log / history

**Problem**: Discovery and event messages can scroll away; hard to review what happened.

**Solution**: Keep a short overworld message log (last N messages) and expose it via key (e.g. L) or a small “Log” button. Reuse or mirror the existing message API (`add_message`) so overworld and battle/dungeon can share or separate logs as you prefer.

**Effort**: Low–medium.

### 6.4 Keyboard shortcuts and controls

**Problem**: Some actions are key-bound (e.g. J for join battle, H for tutorial); others may be undiscoverable.

**Solution**: In-game “Controls” overlay (e.g. ? or from menu) listing overworld keys: Move, Interact, Join battle, Inventory, Tutorial, Zoom, etc. Align with `FEATURE_IMPROVEMENT_SUGGESTIONS.md` (keybindings) if you add remapping later.

**Effort**: Low.

---

## 7. Save/Load & Stability

### 7.1 Temporary POIs and parties across save/load

**Current**: Temp POIs are saved with `is_temporary` and expiry; expired ones removed on `enter_overworld_mode`. Parties are managed by `PartyManager`; ensure they’re serialized with the overworld.

**Improvement**: Document or assert that after load: (1) expired temp POIs are removed, (2) party positions and state are restored, (3) active battles (if any) are either resolved or restored. Add a simple “save and reload on overworld” test to avoid regressions.

**Effort**: Low (docs + optional test).

### 7.2 Region/territory save (if you add regions)

If you implement regions (5.1), include region IDs and names in save so that “Current region” and codex stay correct after load.

---

## Priority Overview

| Priority | Item | Impact | Effort |
|----------|------|--------|--------|
| **Critical for balance** | Time-based party movement (1.4) | High | Medium |
| **Done** | Option B: multiple moves for fast parties (1.4 variant) | High | — |
| **Done** | Road movement cost (1.1) | High | — |
| **Done** | Exploration timeout from config (2.1) | Medium | — |
| **Done** | Minimap (2.2) | High | — |
| **Done** | Discovery log / codex (2.3) | Medium | — |
| **Done** | Hunt mechanic + prey flee (3.4) | Medium | — |
| **Done** | Spawn categories / modular spawn pools (3.5) | Medium | — |
| **Quick wins** | Quest distance / nearest objective HUD (6.1) | Medium | Low | ✅ Done |
| | Party alignment in tooltips (3.1) | Medium | Low | ✅ Done |
| | Party spawn config (3.2) | Low | Low | ✅ Done |
| | Time preview on hover (6.2) | Medium | Low–Medium | ✅ Done |
| **Medium** | More event types (4.1) | Medium | Medium |
| **Larger** | Regions (5.1) | High | Medium–High |
| | Escort / meet-at-POI quests (3.3) | High | Medium–High |

---

## Implementation Order Suggestion

1. **Phase 1 (balance + quick)**: Option B + roads + 2.1 + 2.2 + 2.3 + 3.4 (hunt + prey flee) + 3.5 (spawn categories) are done. Also done: 3.1 party tooltip alignment, 6.1 nearest quest HUD, 3.2 party spawn config, 6.2 time preview. Optional: 1.4 time-based party movement later for full time/road tie-in.
2. **Phase 2 (polish)**: 4.1 more events, 4.2 event placement rules.
3. **Phase 3 (depth)**: 5.1 regions (if desired), 3.3 escort quests, 1.3 time of day (optional). Use spawn categories (3.5) for biome/region-specific spawns.

This keeps the overworld feel consistent with your existing quest/event/POI design and makes roads and exploration more meaningful without large rewrites.
