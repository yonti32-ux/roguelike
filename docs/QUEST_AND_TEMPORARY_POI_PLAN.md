# Quest System & Temporary POIs – Plan

This document plans improvements to the **quest system** and the introduction of **temporary POIs** on the overworld for quest targets and random events.

---

## Implementation status

| Phase | Status | Notes |
|-------|--------|--------|
| **Phase A** | ✅ Done | Temp POI fields, `remove_poi`, save/load |
| **Phase B** | ✅ Done | Elder quests use real POIs; spawn temp camp when none nearby; turn-in removes temp POI |
| **Polish** | ✅ Done | POI tooltips (Temporary/Quest objective); expired temp POI cleanup on enter overworld |
| **Phase C** | ✅ Done | Random events spawn temp POIs (bandit camp, stranded merchant); long expiry so they don’t disappear too fast |
| **Phase D** | ✅ Done | Quest map markers (gold + ring for quest-target POIs); more event types and name/message variety |

---

## 1. Current State Summary (pre–Phase A/B; see status above for what’s done)

### Quest system (`systems/quests/`)
- **Core**: `Quest`, `QuestObjective`, `QuestReward`, `QuestStatus`, `QuestType` (KILL, EXPLORE, COLLECT, DISCOVER, ESCORT, DELIVERY).
- **Progress**: `update_quest_progress(game, objective_type, target_id, amount, poi_id)` — hooked for kills/explore; POI discovery can feed DISCOVER/EXPLORE.
- **Generation**: `create_explore_dungeon_quest`, `create_kill_enemies_quest`, `initialize_elder_quests`.
- **Gap**: Elder/town quests use **placeholder** `dungeon_poi_id` (e.g. `"dungeon_placeholder_1"`) and are not tied to real overworld dungeons. No concept of “quest-only” or temporary locations.

### Overworld & POIs (`world/overworld/`, `world/poi/`)
- **Map**: `OverworldMap.pois: Dict[str, PointOfInterest]`, `add_poi(poi)`, `get_poi_at`, `get_all_pois`. **No `remove_poi`**.
- **POIs**: All POIs are **permanent**, placed at world generation (dungeon, village, town, camp). Base `PointOfInterest` has `poi_id`, `poi_type`, `position`, `level`, `discovered`, `cleared`, `state`.
- **Save**: POIs are serialized and restored by type via registry; no notion of “temporary” or removal.

---

## 2. Goals

1. **Quest system**: Connect quests to **real overworld POIs** (e.g. “Explore [this dungeon]”) and support **quest-specific or event-specific locations** that may appear and disappear.
2. **Temporary POIs**: Introduce POIs that are **not** part of initial world gen: they are **spawned** for quests or random events and can be **removed** when completed, failed, or expired.
3. **Random events**: Use temporary POIs to represent events on the overworld (e.g. “Bandit camp”, “Stranded merchant”, “Ruins”) that the player can discover and interact with.

---

## 3. Temporary POI Design

### 3.1 What is a “temporary” POI?

- **Lifecycle**: Spawned at runtime (when a quest is accepted, or when a random event fires). Exists until:
  - **Completed** (e.g. cleared, objective done),
  - **Expired** (optional time limit or world-state condition), or
  - **Removed** by design (e.g. event ends).
- **Storage**: Same overworld `pois` dict as permanent POIs, so existing `get_poi_at`, `get_all_pois`, and rendering keep working. Differentiate by a **flag** and optional metadata.

### 3.2 Base POI extension (optional but recommended)

- Add to **base** `PointOfInterest` (or a mixin / subclass used only for temp POIs):
  - `is_temporary: bool = False`
  - `source_quest_id: Optional[str] = None`  — if spawned for a quest
  - `source_event_id: Optional[str] = None`  — if spawned by a random event
  - `expires_at_hours: Optional[float] = None`  — optional; game time (from `TimeSystem`) after which the POI should be removed
- **Alternative**: Keep base unchanged and store temp POI metadata in `state` (e.g. `state["is_temporary"]`, `state["source_quest_id"]`). Simpler but less explicit.

### 3.3 Overworld map changes

- **`remove_poi(poi_id: str) -> bool`**: Remove POI by id from `self.pois`. Return `True` if it existed. Used when a temporary POI is completed/expired/removed.
- **Serialization**: When saving:
  - **Permanent POIs**: Save as today (all current POIs that are not temporary).
  - **Temporary POIs**: Save only if we want them to persist across save/load (recommended for active quest POIs). Include `is_temporary` and source/expiry in POI serialization so on load we can restore them and re-add to map. When loading, re-add both permanent and temporary POIs; no need to remove permanent POIs.

So:
- **Save**: For each POI, include a flag `is_temporary` (and source/expiry). No separate “removed POI” list needed unless we want to remember “already completed” temp POIs for journal/history.
- **Load**: Deserialize all POIs (permanent + temporary) and `add_poi`; temporary ones that are past `expires_at_hours` can be skipped or removed after load.

### 3.4 Temporary POI types (examples)

| Type              | Purpose                          | When removed                    |
|-------------------|-----------------------------------|---------------------------------|
| `quest_dungeon`   | Small dungeon for “clear this”    | When quest completed/failed     |
| `quest_camp`      | Bandit/evil camp to clear         | When cleared or quest done      |
| `quest_waypoint`  | “Go here” / discover objective    | When objective completed        |
| `event_camp`      | Random bandit/merchant camp       | When cleared or expired         |
| `event_ruins`     | One-off exploration encounter     | When explored or expired        |

These can be **new POI types** registered in the POI registry (with `is_temporary=True` set on creation), or the same types (e.g. dungeon, camp) created with `is_temporary=True` and optional expiry. Prefer **explicit temporary types** (e.g. `quest_dungeon`, `event_camp`) so behavior and UI can differ from permanent dungeons/camps.

---

## 4. Quest System Improvements

### 4.1 Link elder/town quests to real POIs

- **`initialize_elder_quests`** (and equivalent for town mayor):
  - Use `game.overworld_map` (or `game.overworld`) to get **real** dungeons/camps near the village/town (e.g. by distance from `current_poi.position`).
  - Build **explore** or **discover** quests with `dungeon_poi_id` = actual `poi.poi_id` of a chosen dungeon.
  - Optionally prefer dungeons not yet cleared for “clear the threat” flavor.
- **Fallback**: If no suitable POI exists, either:
  - **Spawn a temporary POI** (see below) and create a quest that targets it, or
  - Keep current fallback (kill quest or placeholder explore) until temp POIs are implemented.

### 4.2 Quests that spawn temporary POIs

- When an elder/mayor gives a quest like “Clear the bandit camp to the east”:
  1. **Choose or generate position**: e.g. random tile within a range of the village/town, or fixed offset.
  2. **Create temporary POI**: e.g. `CampPOI` (or `QuestCampPOI`) with `poi_id = f"quest_camp_{quest_id}_{uuid}"`, `is_temporary=True`, `source_quest_id=quest_id`.
  3. **Add to overworld**: `overworld_map.add_poi(poi)`.
  4. **Create quest**: Objective type EXPLORE or DISCOVER with `poi_id` = that POI’s id.
  5. **On quest completion / turn-in**: Remove the temporary POI: `overworld_map.remove_poi(poi_id)`. Optionally also remove on quest abandon (if we add that later).

This ties **quest flow** and **temporary POI lifecycle** together without changing the rest of the overworld logic.

### 4.3 Optional: quest map markers (UI)

- In overworld HUD, show a distinct marker (e.g. icon or tint) for POIs that are **current quest objectives** (active quest has an objective with `poi_id` = that POI). Can use `is_temporary` and cross-reference `game.active_quests` to highlight them.

---

## 5. Random events (overworld)

### 5.1 When events run

- **Options**: On overworld move (per tile or per N moves), on time tick (e.g. every N hours), or when entering a “region” (if we add regions later). Start simple: e.g. **per move** with a small probability, or **per time** when resting/traveling.

### 5.2 Event → temporary POI

- **Event**: “Scout reports a bandit camp at (x, y).”
  - Create a temporary POI (e.g. `event_camp`) at a valid overworld position (e.g. not on another POI, not too close to player), add to map, optionally set `expires_at_hours`.
  - Optionally create a **simple quest** (“Clear the bandit camp”) and attach it to the POI, or leave it as a discover/clear target without a formal quest.
- **Event**: “Stranded merchant at (x, y).”
  - Spawn temporary POI (e.g. `event_merchant`) that when entered opens a one-off shop or dialogue; remove when used or expired.

Random event system can live in a new module (e.g. `systems/random_events/` or `world/overworld/events.py`) and call into overworld to `add_poi` and later `remove_poi`.

---

## 6. Implementation Phases

### Phase A – Temporary POI foundation (no quest/event logic yet)
- Add `is_temporary`, `source_quest_id`, `source_event_id`, `expires_at_hours` to base POI (or to state).
- Add `remove_poi(poi_id)` to `OverworldMap`.
- Extend save/load to serialize and restore temporary POIs (and skip expired ones on load).
- **Optional**: One new POI type (e.g. `quest_dungeon` or reuse `camp` with `is_temporary=True`) and register it, so we can test add/remove/save/load.

### Phase B – Quests use real and temporary POIs
- **B1**: Change `initialize_elder_quests` (and town equivalent) to pick **real** nearby dungeons/camps and set `dungeon_poi_id` / `poi_id` to real POI ids. Hook progress so exploring/clearing that POI completes the objective.
- **B2**: Add “quest that spawns a temporary POI”: when creating a quest that needs a “clear bandit camp” style target, spawn a temporary camp POI, add to map, create quest with that `poi_id`; on turn-in (or completion) call `remove_poi`.

### Phase C – Random events that spawn temporary POIs ✅
- **Implemented**: `world/overworld/random_events.py` — `try_trigger_random_event(game)` is called after each overworld move. Uses cooldown (30 moves) and 2.5% chance when off cooldown; caps at 3 event POIs at once.
- **Events**: (1) **Bandit camp** — hostile camp POI; (2) **Stranded merchant** — friendly camp with merchant. Both use **long expiry** (`EVENT_POI_EXPIRY_HOURS = 120`, i.e. 5 in-game days) so temporary things don’t disappear too fast. Expired POIs are removed when entering overworld (existing cleanup).
- **Hook**: `engine/controllers/overworld.py` increments `game._overworld_move_count` after a move and calls `try_trigger_random_event(game)`.

### Phase D – Polish ✅
- **Quest map markers** (`ui/overworld/hud.py`): POIs that are the target of an active quest objective are drawn in **gold/amber** (`QUEST_MARKER_COLOR`) with a **thin outer ring** (`QUEST_MARKER_RING_COLOR`) so they stand out on the overworld. Uses `_is_poi_quest_target(poi, game)` to detect quest targets.
- **More event variety** (`world/overworld/random_events.py`): Three event categories with name and message variants:
  - **Hostile camp**: "Bandit Camp" / "Marauder Camp" / "Raider Outpost" with matching scout messages.
  - **Merchant**: "Stranded Merchant" / "Lost Caravan" / "Traveling Peddler" with matching rumors.
  - **Ruins**: "Abandoned Ruins" / "Forgotten Shrine" / "Old Watchtower" (friendly camps) with matching discovery messages.

**Polish completed (before Phase C):**
- **POI tooltips**: Temporary POIs show “Temporary (Quest)” or “Temporary (Event)” in tooltip; POIs that are the target of an active quest show “Quest objective” (`ui/overworld/poi_tooltips.py`).
- **Expired temp POI cleanup**: `OverworldMap.remove_expired_temporary_pois(current_time_hours)` removes POIs where `is_temporary` and `expires_at_hours` is set and current time ≥ expiry. Called from `Game.enter_overworld_mode()` so returning to the overworld cleans up expired event/quest POIs.

---

## 7. File / Module Checklist

| Area              | Files to touch (or add) |
|-------------------|--------------------------|
| Base POI          | `world/poi/base.py` (optional: temp flags) |
| Overworld map     | `world/overworld/map.py` (`remove_poi`) |
| POI save/load     | `engine/utils/save_system.py` (serialize/deserialize temp POIs, handle expiry) |
| Quest generation  | `systems/quests/generation.py` (real POIs, spawn temp POI for “clear camp” style) |
| Quest progress    | `systems/quests/progress.py` (already has poi_id; ensure explore/clear triggers) |
| Village/town init | Where `initialize_elder_quests` is called; ensure overworld is available |
| New POI types     | `world/poi/types.py` (e.g. `QuestCampPOI`, `EventCampPOI`) + registry |
| Random events     | New: e.g. `world/overworld/random_events.py` or `systems/random_events/` |
| Overworld HUD     | Optional: different icon/label for temp or quest-target POIs |

---

## 8. Summary

- **Temporary POIs**: Same storage as current POIs, with a flag and optional source/expiry; add `remove_poi` and save/load support.
- **Quests**: First link to **real** overworld POIs; then add **quest-driven temporary POIs** (spawn on accept, remove on completion).
- **Random events**: Separate system that can spawn (and later remove) temporary POIs, with optional quest tie-in.

This keeps the current architecture (single `pois` dict, existing POI types and registry) and extends it in a clear, phased way. **Phases A–D are complete.** Further work: more quest types, event variety, or other polish as needed.
