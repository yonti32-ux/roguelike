# Village System Implementation Plan

## Overview

Villages are safe zones in the overworld where players can rest, shop, and interact with NPCs. They provide a peaceful contrast to the dangerous dungeons and serve as hubs for resource management and progression.

## Goals

1. **Safe Haven**: Villages are combat-free zones where players can rest and recover
2. **Services**: Provide shops, inns, and other services for gameplay needs
3. **Atmosphere**: Create a distinct feel from dungeons - open, peaceful, community-oriented
4. **Foundation**: Build a system that can expand to towns, cities, and other settlements

## Architecture

### Project Structure

Following the existing project patterns (similar to `world/overworld/` and `world/poi/`), village code will be organized into dedicated subdirectories:

```
world/
  village/                    # NEW: Village subsystem
    __init__.py              # Exports main village classes
    generation.py            # Village map generation
    buildings.py             # Building definitions and placement
    npcs.py                  # Village NPC classes
    tiles.py                 # Village-specific tile types (or extend world/tiles.py)

systems/
  village/                   # NEW: Village services subsystem
    __init__.py              # Exports village service functions
    services.py              # Village service handlers (inn, shop, recruitment)
    companion_generation.py  # Random companion generation for recruitment

ui/
  village/                   # NEW: Village UI subsystem (optional, can be in ui/)
    __init__.py              # Exports village UI components
    recruitment_screen.py    # Recruitment screen UI
    # OR: Keep in ui/screens.py if simpler
```

**Alternative (Simpler) Structure** (if subdirectories seem excessive):
```
world/
  village_generation.py      # Village map generation
  village_buildings.py        # Building definitions
  village_npcs.py            # Village NPCs
  # tiles.py extended in-place

systems/
  village_services.py        # All village services
  companion_generation.py    # Companion generation

ui/
  screens.py                 # (extend) Add RecruitmentScreen
```

**Recommendation**: Use subdirectories (`world/village/`, `systems/village/`) to match the pattern of `world/overworld/` and `world/poi/`. This keeps code organized and makes it easier to expand later.

### Integration Points

- **POI System**: `VillagePOI` class already exists as placeholder in `world/poi/types.py`
- **Map Generation**: Need village-specific map generator (different from dungeon generator)
- **Game Modes**: Uses existing `exploration` mode but with village-specific behavior
- **Shop System**: Integrate with existing `ShopScreen` and economy system
- **NPCs**: Extend `Entity` system to support non-hostile NPCs (merchants, innkeepers)

### Key Components

1. **Village Map Generator** (`world/village/generation.py`)
   - Generate village layouts (open spaces, buildings, paths)
   - Place buildings (shops, inns, houses)
   - Create village-specific terrain (paths, plazas, gardens)

2. **Village Buildings** (`world/village/buildings.py`)
   - Building types: Shop, Inn, Town Hall, Houses
   - Building placement and layout
   - Building interiors (optional for Phase 1)

3. **Village NPCs** (`world/village/npcs.py`)
   - Merchant NPCs (shopkeepers)
   - Innkeeper NPCs (rest/healing)
   - Recruiter NPCs (companion recruitment)
   - Generic villagers (atmosphere, future quests)

4. **Village Services** (`systems/village/services.py`)
   - Inn rest/healing system
   - Shop integration
   - Recruitment service
   - Future: quest board, blacksmith, etc.

5. **Companion Generation** (`systems/village/companion_generation.py`)
   - Random companion generation
   - Name generation integration
   - Class selection and stat initialization
   - Perk assignment
   - Recruitment cost calculation

## Recruitment System

### Overview
Villages serve as recruitment hubs where players can hire new companions to join their party. Each village will have a Tavern or Guild Hall where adventurers gather, looking for work.

### Architecture

The recruitment system integrates with:
- **Companion System**: Uses `CompanionDef` templates and `CompanionState` runtime objects
- **Name Generation**: Uses existing name generation system for companion names
- **Class System**: Randomly selects from available classes (`systems/classes.py`)
- **Perk System**: Assigns starting perks based on level and class
- **Party System**: Adds recruited companions to `game.party` list

### Recruitment Features

1. **Recruitment Building**
   - **Tavern/Guild Hall**: Building where companions can be recruited
   - Contains recruiter NPC (tavern keeper, guild master, etc.)
   - Visual distinction from other buildings

2. **Random Companion Generation**
   - Companions are randomly generated when village is first visited
   - Each village has 1-3 available companions (scales with village level)
   - Companions have:
     - Randomly generated names (using name generation system)
     - Random class selection (warrior, rogue, mage, etc.)
     - Random level (scales with village level, ±2 variance)
     - Random starting perks (0-2 perks based on level)
     - Random starting equipment (optional, basic gear)
     - Personality/backstory snippets (for flavor)

3. **Recruitment Mechanics**
   - **Cost**: Companions cost gold to recruit (scales with level/quality)
   - **Party Size Limit**: Maximum party size (e.g., 4 total including hero)
   - **Preview**: Show companion stats, class, skills before recruiting
   - **Confirmation**: Confirm recruitment with cost display

4. **Companion Generation Algorithm**
   - Select random class from available classes
   - Generate name using name generation system
   - Calculate level based on village level
   - Generate starting perks (weighted by class/level)
   - Initialize companion state with stats
   - Create unique companion ID

5. **Recruitment UI**
   - List of available companions
   - Companion details (name, class, level, stats, cost)
   - Preview companion skills and perks
   - Recruit button with cost confirmation
   - Party size indicator

### Companion Generation Details

**Level Calculation**:
- Base level = village level
- Variance: ±2 levels (random)
- Minimum level: 1
- Maximum level: village level + 2

**Class Selection**:
- Random selection from all available classes
- Equal probability for each class
- Can be weighted later (e.g., more warriors in some villages)

**Name Generation**:
- Use name generation system (`systems/namegen/`)
- Create companion name generator (or extend existing)
- Generate unique names per companion
- Store generated name in `CompanionState.name_override`

**Starting Perks**:
- Number of perks: `min(level // 3, 2)` (0-2 perks)
- Perks selected from class-appropriate perk pool
- Weighted by perk unlock level (can't get perks above companion level)

**Recruitment Cost Formula**:
```python
base_cost = 50 * companion_level
class_multiplier = 1.0  # Can vary by class rarity
perk_bonus = 10 * num_perks
total_cost = int((base_cost * class_multiplier) + perk_bonus)
```

**Companion Persistence**:
- Generated companions stored in `VillagePOI.state["available_companions"]`
- Companions persist until recruited
- Can refresh companions after certain conditions (future enhancement)

## Phase 1 Features (MVP)

### Core Features

1. **Village Map Generation**
   - Open village layout (not dungeon-style)
   - Central plaza/square
   - Buildings placed around perimeter
   - Paths connecting buildings
   - Village entrance/exit point

2. **Basic Buildings**
   - **Shop**: General merchant (uses existing shop system)
   - **Inn**: Rest and full heal (new service)
   - **Tavern/Guild Hall**: Companion recruitment (new service)
   - **Houses**: Decorative buildings (atmosphere)

3. **NPCs**
   - Shopkeeper (merchant) - interactive, opens shop
   - Innkeeper - interactive, provides rest/healing
   - Recruiter/Tavern Keeper - interactive, shows available companions
   - Villagers (optional) - non-interactive, atmosphere

4. **Services**
   - **Shopping**: Buy/sell items (existing system)
   - **Resting**: Full HP restore at inn (new)
   - **Recruitment**: Hire new companions (new system)
   - **Exit**: Return to overworld

### Map Layout Design

```
Village Layout Concept:
┌─────────────────────────────┐
│  [House]  [House]  [House]  │
│                             │
│  [Shop]    [Plaza]   [Inn]  │
│             [Well]           │
│                             │
│  [Tavern] [House]  [House]   │
│                             │
│         [Entrance]          │
└─────────────────────────────┘
```

- **Size**: Medium-sized map (similar to early dungeon floors)
- **Style**: Open, with clear paths and building clusters
- **Terrain**: Village-specific tiles (paths, grass, building floors)

## Implementation Steps

### Step 0: Create Directory Structure
**Files**: Create new directories and `__init__.py` files

- Create `world/village/` directory
- Create `world/village/__init__.py` with exports
- Create `systems/village/` directory  
- Create `systems/village/__init__.py` with exports
- Create `ui/village/` directory (optional, or extend `ui/screens.py`)
- Create `ui/village/__init__.py` if using subdirectory

**Example `world/village/__init__.py`**:
```python
"""
Village system: map generation, buildings, NPCs, and tiles.
"""

from .generation import generate_village
from .buildings import (
    Building,
    ShopBuilding,
    InnBuilding,
    TavernBuilding,
    HouseBuilding,
)
from .npcs import (
    VillageNPC,
    MerchantNPC,
    InnkeeperNPC,
    RecruiterNPC,
)
from .tiles import (
    VILLAGE_PATH_TILE,
    VILLAGE_PLAZA_TILE,
    VILLAGE_GRASS_TILE,
    BUILDING_FLOOR_TILE,
    BUILDING_WALL_TILE,
)

__all__ = [
    # Generation
    "generate_village",
    # Buildings
    "Building",
    "ShopBuilding",
    "InnBuilding",
    "TavernBuilding",
    "HouseBuilding",
    # NPCs
    "VillageNPC",
    "MerchantNPC",
    "InnkeeperNPC",
    "RecruiterNPC",
    # Tiles
    "VILLAGE_PATH_TILE",
    "VILLAGE_PLAZA_TILE",
    "VILLAGE_GRASS_TILE",
    "BUILDING_FLOOR_TILE",
    "BUILDING_WALL_TILE",
]
```

**Example `systems/village/__init__.py`**:
```python
"""
Village services: inn, shop, recruitment, and companion generation.
"""

from .services import (
    rest_at_inn,
    open_shop,
    open_recruitment,
    recruit_companion,
)
from .companion_generation import (
    generate_random_companion,
    calculate_recruitment_cost,
    generate_companion_name,
    select_random_class,
    assign_starting_perks,
    AvailableCompanion,
)

__all__ = [
    # Services
    "rest_at_inn",
    "open_shop",
    "open_recruitment",
    "recruit_companion",
    # Companion generation
    "generate_random_companion",
    "calculate_recruitment_cost",
    "generate_companion_name",
    "select_random_class",
    "assign_starting_perks",
    "AvailableCompanion",
]
```

**Import Pattern** (following existing code style):
```python
# In world/village/generation.py
from ..game_map import GameMap
from ..tiles import Tile
from .buildings import Building
from .npcs import VillageNPC

# In systems/village/services.py
from ...world.village.npcs import VillageNPC
from ...systems.party import CompanionState
from ...engine.core.game import Game

# In world/poi/types.py (updating VillagePOI)
from ..village.generation import generate_village
```

### Step 1: Village Map Generation
**File**: `world/village/generation.py`

- Create `generate_village()` function
- Generate village layout:
  - Central plaza (open space)
  - Building placement around perimeter
  - Paths connecting key areas
  - Village entrance point
- Return `GameMap` with village-specific structure

**Key Functions**:
- `generate_village(level: int, village_name: str, seed: Optional[int] = None) -> GameMap`
- `_place_buildings(map_width, map_height, level: int) -> List[Building]`
- `_create_paths(buildings, plaza) -> List[Path]`
- `_place_plaza(map_width, map_height) -> Tuple[int, int, int, int]`  # x, y, w, h

**Exports** (in `world/village/__init__.py`):
```python
from .generation import generate_village
from .buildings import Building, ShopBuilding, InnBuilding, TavernBuilding, HouseBuilding
from .npcs import VillageNPC, MerchantNPC, InnkeeperNPC, RecruiterNPC
from .tiles import VILLAGE_PATH_TILE, VILLAGE_PLAZA_TILE, VILLAGE_GRASS_TILE

__all__ = [
    "generate_village",
    "Building", "ShopBuilding", "InnBuilding", "TavernBuilding", "HouseBuilding",
    "VillageNPC", "MerchantNPC", "InnkeeperNPC", "RecruiterNPC",
    "VILLAGE_PATH_TILE", "VILLAGE_PLAZA_TILE", "VILLAGE_GRASS_TILE",
]
```

### Step 2: Building System
**File**: `world/village/buildings.py`

- Define building types and layouts
- Building placement logic
- Building-to-service mapping

**Building Types**:
- `ShopBuilding`: Contains merchant
- `InnBuilding`: Contains innkeeper
- `TavernBuilding`: Contains recruiter (companion recruitment)
- `HouseBuilding`: Decorative

**Key Classes**:
```python
@dataclass
class Building:
    building_type: str  # "shop", "inn", "tavern", "house"
    x: int
    y: int
    width: int
    height: int
    npc_id: Optional[str] = None
```

### Step 3: Village NPCs
**File**: `world/village/npcs.py`

- Extend `Entity` to create `VillageNPC` class
- NPC types: Merchant, Innkeeper, Recruiter, Villager
- NPC placement in buildings
- Interaction system (talk to NPC)

**Key Classes**:
```python
class VillageNPC(Entity):
    npc_type: str  # "merchant", "innkeeper", "recruiter", "villager"
    building_id: Optional[str] = None
    dialogue: List[str] = field(default_factory=list)
```

### Step 4: Village Services
**File**: `systems/village/services.py`

- Inn rest/healing service
- Shop integration (already exists)
- Recruitment service
- Service interaction handlers

**Key Functions**:
- `rest_at_inn(game: Game) -> None`: Full heal, restore resources
- `open_shop(game: Game, merchant_id: str) -> None`: Open shop screen
- `open_recruitment(game: Game, recruiter_id: str) -> None`: Open recruitment screen
- `recruit_companion(game: Game, companion_state: CompanionState, cost: int) -> bool`: Recruit companion

### Step 4b: Companion Generation System
**File**: `systems/village/companion_generation.py`

- Random companion generation
- Name generation integration
- Class selection and stat initialization
- Perk assignment
- Recruitment cost calculation

**Key Functions**:
- `generate_random_companion(village_level: int, seed: Optional[int] = None) -> CompanionState`: Generate random companion
- `calculate_recruitment_cost(companion_state: CompanionState) -> int`: Calculate gold cost
- `generate_companion_name() -> str`: Generate name using name system
- `select_random_class() -> str`: Select random class from available classes
- `assign_starting_perks(companion_state: CompanionState, level: int) -> None`: Assign random starting perks

**Key Classes**:
```python
@dataclass
class AvailableCompanion:
    """A companion available for recruitment in a village."""
    companion_state: CompanionState
    recruitment_cost: int
    generated_name: str
    backstory_snippet: str  # Optional flavor text
```

### Step 5: Update VillagePOI
**File**: `world/poi/types.py`

- Implement `VillagePOI.enter()` to load village map
- Generate village on first entry
- Generate available companions on first visit
- Handle village exit
- Store village state (discovered buildings, available companions, etc.)

**Changes**:
```python
def enter(self, game: "Game") -> None:
    """Enter the village and load village map."""
    game.current_poi = self
    
    # Generate village map if not already generated
    if "village_map" not in self.state:
        from world.village import generate_village
        village_map = generate_village(self.level, self.name)
        self.state["village_map"] = village_map
    
    # Load the village map
    game.current_map = self.state["village_map"]
    game.enter_exploration_mode()
    
    # Place player at entrance
    # ... positioning logic ...
    
    game.add_message(f"You enter {self.name}. A peaceful village.")
```

### Step 6: Village Tiles
**File**: `world/village/tiles.py` (new file, or extend `world/tiles.py`)

**Option A**: Create new file `world/village/tiles.py` for village-specific tiles
**Option B**: Extend existing `world/tiles.py` with village tiles

**Recommendation**: Create `world/village/tiles.py` to keep village code self-contained, then import/register tiles in `world/tiles.py` if needed for compatibility.

- Add village-specific tile types:
  - `VILLAGE_PATH_TILE`: Walkable paths
  - `VILLAGE_PLAZA_TILE`: Central plaza
  - `VILLAGE_GRASS_TILE`: Village grass
  - `BUILDING_FLOOR_TILE`: Building interiors
  - `BUILDING_WALL_TILE`: Building walls

### Step 7: NPC Interaction
**File**: `engine/core/game.py` (extend)

- Add NPC interaction handling
- Check for NPCs at player position
- Handle interaction (talk, use service)
- Open appropriate screens (shop, inn menu)

### Step 8: UI Enhancements
**Files**: `ui/hud_exploration.py`, `ui/screens.py`

- Add village-specific UI hints
- Inn rest confirmation dialog
- NPC interaction prompts
- Recruitment screen UI

### Step 8b: Recruitment Screen
**File**: `ui/village/recruitment_screen.py` (new file) OR `ui/screens.py` (extend existing)

**Option A**: Create `ui/village/recruitment_screen.py` for village-specific UI
**Option B**: Add `RecruitmentScreen` class to existing `ui/screens.py`

**Recommendation**: If village UI grows (recruitment, inn menu, etc.), use `ui/village/` subdirectory. Otherwise, extend `ui/screens.py` for simplicity.

- Display list of available companions
- Show companion details (stats, class, skills, perks)
- Display recruitment cost
- Recruit button with confirmation
- Party size limit indicator
- Companion preview/inspection

**Key Features**:
- Scrollable list of companions
- Detailed companion stat display
- Cost confirmation before recruitment
- Party size check (prevent over-recruitment)

## Technical Details

### Map Generation Algorithm

1. **Plaza Placement**
   - Place central plaza (8x8 to 12x12 tiles)
   - Ensure it's walkable and central

2. **Building Placement**
   - Place buildings around perimeter
   - Ensure minimum spacing
   - Connect to plaza with paths

3. **Path Generation**
   - Create paths from entrance to plaza
   - Connect plaza to all buildings
   - Use A* or simple pathfinding

4. **NPC Placement**
   - Place NPCs inside their respective buildings
   - Ensure NPCs are on walkable tiles

### Village Size Scaling

- **Small Village** (Level 1-3): 3-4 buildings, small plaza
- **Medium Village** (Level 4-7): 5-7 buildings, medium plaza
- **Large Village** (Level 8+): 8-10 buildings, large plaza

### NPC Interaction Flow

1. Player moves to NPC tile
2. Press interact key (E, Space, or Enter)
3. Check NPC type:
   - **Merchant**: Open shop screen
   - **Innkeeper**: Show rest menu (Rest? Y/N)
   - **Recruiter**: Open recruitment screen
   - **Villager**: Show dialogue (future: quests)

### Inn Rest System

- **Cost**: Free or small gold cost (10-50 gold based on level)
- **Effect**: Full HP restore, restore stamina/mana
- **Message**: "You rest at the inn and feel refreshed."

### Shop Integration

- Use existing `ShopScreen` class
- Generate merchant stock based on village level
- Use existing economy system for pricing

### Recruitment Integration

- Generate companions when village is first visited
- Store available companions in village state
- Companions persist until recruited or village resets
- Use existing `CompanionState` and `CompanionDef` system
- Integrate with existing party system (`game.party`)
- Use name generation system for companion names

## Future Enhancements (Post-MVP)

1. **Building Interiors**: Enter buildings for interior maps
2. **Quest Board**: Accept quests from village
3. **Blacksmith**: Upgrade/repair equipment
4. **Library**: Skill training or lore
5. **Village Events**: Random events in villages
6. **Village Reputation**: Track player actions
7. **Dynamic Villages**: Villages that change over time
8. **Village Upgrades**: Player can invest in village improvements
9. **Companion Relationships**: Companions have relationships with each other
10. **Companion Quests**: Special quests from recruited companions
11. **Companion Dismissal**: Ability to dismiss companions (with consequences)
12. **Companion Specializations**: Companions with unique abilities/roles
13. **Recruitment Events**: Special events that bring unique companions
14. **Companion Loyalty**: Companions may leave if mistreated

## Testing Checklist

- [ ] Village generates correctly
- [ ] Buildings are placed properly
- [ ] Paths connect all areas
- [ ] Player can enter village from overworld
- [ ] Player can exit village to overworld
- [ ] Shop NPC opens shop screen
- [ ] Inn NPC provides rest/healing
- [ ] Recruiter NPC opens recruitment screen
- [ ] Companions generate with random names
- [ ] Companions generate with appropriate classes
- [ ] Companions generate with level-appropriate stats
- [ ] Recruitment cost scales correctly
- [ ] Can recruit companions successfully
- [ ] Party size limit enforced
- [ ] Recruited companions join party correctly
- [ ] Village persists between visits
- [ ] Available companions persist until recruited
- [ ] Multiple villages work independently
- [ ] Village level affects building count/quality
- [ ] Village level affects companion availability/quality

## File Structure

### Recommended Structure (Following Project Patterns)

```
world/
  village/                          # NEW: Village subsystem
    __init__.py                    # Exports: generate_village, Building, VillageNPC, etc.
    generation.py                   # Village map generation
    buildings.py                    # Building definitions and placement
    npcs.py                         # Village NPC classes
    tiles.py                       # Village-specific tile types (or extend world/tiles.py)

  poi/
    types.py                        # (update) VillagePOI implementation

systems/
  village/                          # NEW: Village services subsystem
    __init__.py                    # Exports: rest_at_inn, open_recruitment, etc.
    services.py                    # Village service handlers (inn, shop, recruitment)
    companion_generation.py        # Random companion generation for recruitment

ui/
  village/                          # NEW: Village UI (optional)
    __init__.py                    # Exports: RecruitmentScreen
    recruitment_screen.py          # Recruitment screen UI
  # OR: extend ui/screens.py instead

  screens.py                        # (extend) BaseScreen protocol, add RecruitmentScreen if not in subdirectory
```

### Import Path Examples

```python
# From world/village/generation.py
from ..game_map import GameMap
from ..tiles import Tile
from .buildings import Building
from .npcs import VillageNPC

# From systems/village/services.py
from ...world.village.npcs import VillageNPC, RecruiterNPC
from ...systems.party import CompanionState
from ...systems.economy import calculate_shop_buy_price
from ...engine.core.game import Game

# From world/poi/types.py (updating VillagePOI)
from ..village import generate_village
from ..village.buildings import Building

# From ui/village/recruitment_screen.py
from ...systems.village.companion_generation import AvailableCompanion
from ...systems.party import CompanionState
from ...engine.core.game import Game

# From engine/core/game.py (adding village support)
from world.village import generate_village
from systems.village.services import rest_at_inn, open_recruitment
```

### Alternative Simpler Structure (If Subdirectories Seem Excessive)

```
world/
  village_generation.py            # Village map generation
  village_buildings.py              # Building definitions
  village_npcs.py                   # Village NPCs
  # tiles.py extended in-place

systems/
  village_services.py               # All village services
  companion_generation.py           # Companion generation

ui/
  screens.py                        # (extend) Add RecruitmentScreen

world/poi/
  types.py                          # (update) VillagePOI implementation
```

**Note**: The subdirectory approach is recommended to match existing patterns (`world/overworld/`, `world/poi/`, `systems/namegen/`) and makes the codebase more organized as it grows.

## Dependencies

- Existing POI system
- Existing shop system (`ui/screens.py`, `systems/economy.py`)
- Existing map generation (`world/mapgen.py` for reference)
- Existing entity system (`world/entities.py`)
- Existing game mode system (`engine/core/game.py`)
- Existing companion system (`systems/party.py`)
- Existing name generation system (`systems/namegen/`)
- Existing class system (`systems/classes.py`)
- Existing perk system (`systems/perks.py`)

## Notes

### Architecture Considerations

- **Follow Existing Patterns**: Match the structure of `world/overworld/` and `world/poi/` with subdirectories
- **Import Organization**: Use relative imports within subdirectories, absolute imports for cross-module
- **Module Exports**: Each `__init__.py` should export main classes/functions for clean imports
- **Separation of Concerns**: 
  - `world/village/` = world representation (maps, buildings, NPCs, tiles)
  - `systems/village/` = game logic (services, companion generation)
  - `ui/village/` = user interface (screens, dialogs)
- **Extensibility**: Structure allows easy addition of new building types, NPCs, services

### Design Principles

- Villages should feel distinct from dungeons (open, peaceful)
- Keep village generation deterministic (same seed = same village)
- Consider caching generated villages for performance
- Village state should persist in save files
- NPCs should have simple but distinct personalities (names, dialogue)
- Companion generation should be deterministic per village (same seed = same companions)
- Companions should feel unique with generated names and varied classes
- Recruitment cost should scale meaningfully (not too cheap, not too expensive)
- Party size limit prevents overwhelming the player with too many companions
- Consider companion "refresh" - new companions appear after some time/conditions

### Import Update Strategy

When implementing, update imports in this order:
1. Create new files with relative imports
2. Create `__init__.py` files with exports
3. Update existing files that need village functionality:
   - `world/poi/types.py` - import from `world.village`
   - `engine/core/game.py` - import from `systems.village.services`
   - `ui/screens.py` or new `ui/village/` - import from `systems.village`
4. Test imports work correctly
5. Update any other files that reference village code

