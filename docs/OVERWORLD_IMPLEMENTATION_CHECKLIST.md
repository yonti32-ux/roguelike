# Overworld System - Implementation Checklist

## Phase 1: Foundation (MVP) - Start Here

### Step 1: Create File Structure
- [ ] Create `world/overworld/` directory
- [ ] Create `world/poi/` directory
- [ ] Create `world/time/` directory
- [ ] Create `ui/overworld/` directory
- [ ] Create all `__init__.py` files

### Step 2: Configuration System
- [ ] Create `config/overworld_settings.json` with default values
- [ ] Implement `world/overworld/config.py` (OverworldConfig class)
- [ ] Add config loading to game initialization
- [ ] Test: Load and display config values

### Step 3: Terrain System
- [ ] Create `world/overworld/terrain.py`
- [ ] Define TerrainType dataclass
- [ ] Create basic terrain types (grass, forest, mountain, water)
- [ ] Test: Create and render terrain types

### Step 4: Overworld Map (Basic)
- [ ] Create `world/overworld/map.py`
- [ ] Implement OverworldMap class (without regions initially)
- [ ] Add basic tile storage (2D list)
- [ ] Add player position tracking
- [ ] Add explored tiles tracking
- [ ] Test: Create small map, set/get tiles

### Step 5: World Generation (Basic)
- [ ] Create `world/overworld/generation.py`
- [ ] Implement WorldGenerator class
- [ ] Add simple terrain generation (random or pattern-based)
- [ ] Test: Generate small world, verify terrain placement

### Step 6: POI Base System
- [ ] Create `world/poi/base.py`
- [ ] Implement PointOfInterest base class
- [ ] Add basic POI properties (id, type, position, level)
- [ ] Add state tracking (discovered, cleared)
- [ ] Test: Create POI instances

### Step 7: Dungeon POI
- [ ] Create `world/poi/types.py`
- [ ] Implement DungeonPOI class
- [ ] Add floor count and cleared floors tracking
- [ ] Add enter/exit methods (stubs initially)
- [ ] Test: Create dungeon POI

### Step 8: POI Placement
- [ ] Create `world/poi/placement.py`
- [ ] Implement POI placement algorithm
- [ ] Add to WorldGenerator
- [ ] Test: Generate world with POIs, verify placement

### Step 9: Game Mode Integration
- [ ] Modify `engine/core/states.py` - Add OVERWORLD mode
- [ ] Modify `engine/core/game.py`:
  - [ ] Add overworld_map attribute
  - [ ] Add current_poi attribute
  - [ ] Add enter_overworld_mode() method
  - [ ] Add enter_poi() method
  - [ ] Add exit_poi() method
- [ ] Modify game initialization to start in OVERWORLD mode
- [ ] Test: Game starts in overworld mode

### Step 10: Overworld Controller
- [ ] Create `engine/controllers/overworld.py`
- [ ] Implement OverworldController class
- [ ] Add handle_event() for input
- [ ] Add update() for movement
- [ ] Add tile-based movement logic
- [ ] Add POI detection
- [ ] Integrate with game.handle_event()
- [ ] Test: Move player on overworld

### Step 11: Basic Rendering
- [ ] Create `ui/overworld/hud.py`
- [ ] Implement draw_overworld() function
- [ ] Render terrain tiles (colored rectangles)
- [ ] Render POI markers (colored circles)
- [ ] Render player icon
- [ ] Add camera system (follow player)
- [ ] Integrate with game.draw()
- [ ] Test: See overworld rendered

### Step 12: POI Entry/Exit
- [ ] Implement DungeonPOI.enter() - transition to exploration
- [ ] Implement DungeonPOI.exit() - return to overworld
- [ ] Add interaction key (E) to enter POI
- [ ] Test: Enter dungeon, see exploration mode, exit back

### Step 13: Save System Integration
- [ ] Modify `engine/utils/save_system.py`:
  - [ ] Add _serialize_overworld()
  - [ ] Add _deserialize_overworld()
  - [ ] Add _serialize_pois()
  - [ ] Add _deserialize_pois()
- [ ] Update save format version
- [ ] Test: Save game with overworld, load and verify

### Step 14: Testing & Polish
- [ ] Test full flow: New game → Overworld → Enter dungeon → Exit
- [ ] Test save/load with overworld state
- [ ] Fix any bugs
- [ ] Add basic error handling

---

## Phase 2: POI Types & Time System

### Step 15: Additional POI Types
- [ ] Implement VillagePOI class
- [ ] Implement TownPOI class
- [ ] Implement CampPOI class
- [ ] Add POI type distribution to config
- [ ] Update placement algorithm for multiple types
- [ ] Test: Generate world with all POI types

### Step 16: Time System
- [ ] Create `world/time/time_system.py`
- [ ] Implement TimeSystem class
- [ ] Add time tracking (days, hours, minutes)
- [ ] Add time string formatting
- [ ] Integrate with game
- [ ] Test: Time increments correctly

### Step 17: Movement Time Costs
- [ ] Add terrain movement costs to config
- [ ] Calculate time cost based on terrain
- [ ] Update OverworldController to consume time
- [ ] Test: Different terrains cost different time

### Step 18: POI Level Calculation
- [ ] Implement difficulty scaling algorithm
- [ ] Calculate POI levels based on distance from start
- [ ] Apply levels to POIs during generation
- [ ] Display POI level in UI
- [ ] Test: POI levels scale with distance

### Step 19: POI Discovery
- [ ] Add discovery system (POIs hidden until found)
- [ ] Update rendering (hide undiscovered POIs)
- [ ] Add discovery on approach/exploration
- [ ] Test: POIs appear when discovered

### Step 20: UI Improvements
- [ ] Add time display to overworld HUD
- [ ] Add position display
- [ ] Improve POI rendering (icons, labels)
- [ ] Add POI tooltips on hover
- [ ] Test: UI displays all information

---

## Phase 3: Region System (Large Worlds)

### Step 21: Region Class
- [ ] Create `world/overworld/region.py`
- [ ] Implement Region class
- [ ] Add region coordinate system
- [ ] Test: Create and manage regions

### Step 22: Region Loading
- [ ] Add region loading to OverworldMap
- [ ] Implement load_region() and unload_region()
- [ ] Add region buffer (keep 3x3 grid loaded)
- [ ] Test: Load/unload regions as player moves

### Step 23: Region-Based Generation
- [ ] Update WorldGenerator to generate by region
- [ ] Add lazy generation (generate on first access)
- [ ] Test: Generate large world efficiently

### Step 24: Region Serialization
- [ ] Add region data to save format
- [ ] Serialize only loaded regions
- [ ] Test: Save/load with regions

### Step 25: Performance Optimization
- [ ] Optimize rendering (only render loaded regions)
- [ ] Add region preloading (load adjacent regions)
- [ ] Test: Large world (512x512+) performance

---

## Phase 4: Polish & Expansion

### Step 26: Visual Improvements
- [ ] Add terrain sprites (if sprite system ready)
- [ ] Improve POI icons
- [ ] Add visual effects (animations, particles)
- [ ] Test: Visual polish

### Step 27: Minimap
- [ ] Create `ui/overworld/minimap.py`
- [ ] Implement minimap rendering
- [ ] Add minimap toggle
- [ ] Test: Minimap shows world overview

### Step 28: Overworld Events (Foundation)
- [ ] Create event system structure
- [ ] Add random encounter framework
- [ ] Add event triggers (time-based, location-based)
- [ ] Test: Events can trigger

### Step 29: Resource Gathering (Foundation)
- [ ] Add resource node types
- [ ] Add resource placement to generation
- [ ] Add gathering interaction
- [ ] Test: Can gather resources

### Step 30: Fast Travel
- [ ] Add fast travel system
- [ ] Add fast travel menu
- [ ] Only allow travel to discovered POIs
- [ ] Test: Fast travel between POIs

---

## Quick Reference: File Creation Order

1. **Config & Data Structures** (Steps 2-3)
   - `config/overworld_settings.json`
   - `world/overworld/config.py`
   - `world/overworld/terrain.py`

2. **Core Map System** (Steps 4-5)
   - `world/overworld/map.py`
   - `world/overworld/generation.py`

3. **POI System** (Steps 6-8)
   - `world/poi/base.py`
   - `world/poi/types.py`
   - `world/poi/placement.py`

4. **Game Integration** (Steps 9-10)
   - Modify `engine/core/states.py`
   - Modify `engine/core/game.py`
   - `engine/controllers/overworld.py`

5. **Rendering** (Step 11)
   - `ui/overworld/hud.py`

6. **Save System** (Step 13)
   - Modify `engine/utils/save_system.py`

---

## Testing Checklist (After Each Phase)

### Phase 1 Testing
- [ ] Can generate overworld
- [ ] Can move player on overworld
- [ ] Can see terrain and POIs
- [ ] Can enter dungeon POI
- [ ] Can exit back to overworld
- [ ] Can save game with overworld
- [ ] Can load game with overworld
- [ ] World is consistent (same seed = same world)

### Phase 2 Testing
- [ ] Multiple POI types generate correctly
- [ ] Time system works
- [ ] Movement consumes time
- [ ] POI levels scale with distance
- [ ] POI discovery works
- [ ] UI displays all information

### Phase 3 Testing
- [ ] Large worlds generate efficiently
- [ ] Regions load/unload correctly
- [ ] Performance is acceptable (60 FPS)
- [ ] Save/load works with regions

### Phase 4 Testing
- [ ] All new features work
- [ ] No performance regressions
- [ ] UI is polished
- [ ] Game feels complete

---

## Common Issues & Solutions

### Issue: World generation is slow
- **Solution**: Use region-based generation, generate on-demand

### Issue: Memory usage too high
- **Solution**: Unload regions not near player, limit loaded regions

### Issue: POIs too clustered
- **Solution**: Increase min_distance, improve placement algorithm

### Issue: Difficulty scaling feels wrong
- **Solution**: Adjust scaling formula, test different values

### Issue: Save file too large
- **Solution**: Only save loaded regions, compress data

---

## Notes

- Start with small world (128x128) for testing
- Test each step before moving to next
- Keep old code commented out during refactoring
- Add debug prints/logging during development
- Test save/load frequently to catch issues early

