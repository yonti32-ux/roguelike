# What Happens When You Reach Quest/Event POIs

This doc describes **current behavior** when the player reaches temporary or quest-related POIs, and the **improvements** we apply so clearing hostile camps is reflected correctly.

---

## Current flow (before changes)

### Quest-spawned camp (e.g. “Bandit Camp” from elder)
1. **Accept quest** → A temporary camp POI is spawned on the overworld (`is_temporary=True`, `source_quest_id=...`).
2. **Travel there and enter** → Same as any camp: `CampPOI.enter()` runs, quest progress “explore” is updated (objective completes), camp map is generated with `is_hostile=True` (2–4 goblins).
3. **In the camp** → Exploration mode; moving into enemies starts battle.
4. **Win battle** → Return to exploration on the same camp map (enemies gone). No flag was set on the POI.
5. **Exit** → Back to overworld. Turn-in at elder removes the quest POI from the map.
6. **Re-enter same camp (before turn-in)** → Camp loads again from state; message still said “hostile - enemies are present!” even though the map had no enemies (wrong).

### Random event: hostile camp (Bandit / Marauder / Raider)
1. **Event spawns** → Temporary camp POI with `is_hostile=True`, `source_event_id=...`, long expiry.
2. **Enter** → Same as above: camp map with enemies, “explore” quest progress if you have a matching objective.
3. **Win battle** → Back to exploration; POI was not marked cleared.
4. **Exit** → POI stayed on map until expiry (120h). Re-entering showed the same wrong “hostile” message.

### Random event: merchant or ruins (friendly)
1. **Enter** → Camp map with merchant and/or NPCs, no combat. Rest at campfire possible.
2. **Exit** → POI stays until expiry. No “cleared” state needed for friendly camps.

---

## Improvements implemented

1. **Mark hostile camp cleared on victory**  
   When battle ends in **victory** and we are inside a **hostile** `CampPOI` (quest or event):
   - Set `current_poi.is_destroyed = True` and `current_poi.cleared = True`.
   - Add message: *“You have cleared [Camp name]!”*

2. **Re-entry after clear**  
   `CampPOI.enter()` already checks `is_destroyed`: if True, it only shows *“You arrive at the ruins of [name]. The camp has been abandoned.”* and returns without loading the map. So re-entry is now correct.

3. **Remove cleared temporary event camps from the map**  
   When we mark a hostile camp cleared and it is a **temporary event** POI (`is_temporary` and `source_event_id` set), we also call `overworld_map.remove_poi(poi_id)` so the camp disappears from the overworld instead of sitting as ruins until expiry.

Quest-spawned camps are still removed only on **quest turn-in** (as before); they are not removed on clear, so the player can re-enter the ruins if desired before turning in.

---

## Summary table

| POI type              | On enter              | On clear (win battle)        | On exit / later                |
|-----------------------|------------------------|------------------------------|---------------------------------|
| Quest hostile camp    | Explore progress, combat | Mark cleared/destroyed       | Turn-in removes POI             |
| Event hostile camp    | Explore progress, combat | Mark cleared; **remove from map** | N/A (already removed)          |
| Event merchant/ruins  | Rest / merchant        | N/A (no combat)              | POI stays until expiry          |
