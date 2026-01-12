# Faction System & Integration Plan

## Overview

This document outlines the plan for adding factions, integrating parties with battles, expanding party capabilities, and improving UI systems while maintaining clean, extensible architecture.

## Current Architecture Analysis

### Existing Systems
- **Overworld Map**: Tile-based, POI system, party manager
- **Battle System**: Turn-based combat with enemies
- **Exploration System**: Dungeon floors, entities, AI
- **Party System**: Roaming parties with types, behaviors, interactions
- **POI System**: Towns, villages, dungeons, camps

### Strengths
- Modular design with clear separation
- Extensible party type system
- POI system uses registry pattern
- Battle system is self-contained

### Areas Needing Improvement
- No faction/ownership system
- Parties not integrated with battles
- UI screens need consolidation
- Inventory system needs fixes

---

## Phase 1: Faction System Foundation

### 1.1 Faction Data Structure

**File**: `systems/factions.py`

```python
@dataclass
class Faction:
    id: str
    name: str
    alignment: str  # "good", "neutral", "evil"
    color: Tuple[int, int, int]  # For map display
    relations: Dict[str, int]  # Relations with other factions (-100 to 100)
    home_poi_types: List[str]  # POI types this faction controls
    default_party_types: List[str]  # Party types that belong to this faction
```

**Example Factions**:
- **Kingdom of Aetheria** (good): Towns, villages, castles
- **Free Cities** (neutral): Independent towns
- **Shadow Cult** (evil): Dark camps, hidden bases
- **Wild Tribes** (neutral): Camps, villages
- **Bandit Confederacy** (evil): Bandit camps

### 1.2 POI Faction Integration

**File**: `world/poi/base.py` (extend existing)

Add to `PointOfInterest`:
```python
faction_id: Optional[str] = None
faction_relations: Dict[str, int] = field(default_factory=dict)  # Per-faction relations
```

**New POI Types**:
- `castle` / `keep`: Fortified faction strongholds
- `outpost`: Small faction-controlled points
- `bandit_camp`: Enemy-controlled camps
- `cult_sanctuary`: Evil faction bases

### 1.3 Party Faction Integration

**File**: `world/overworld/party_types.py` (extend existing)

Add to `PartyType`:
```python
faction_id: Optional[str] = None  # Which faction this party belongs to
can_join_battle: bool = False  # Can this party fight in battles?
battle_unit_template: Optional[str] = None  # Template for battle units
```

**File**: `world/overworld/roaming_party.py` (extend existing)

Add to `RoamingParty`:
```python
faction_id: Optional[str] = None
faction_relations: Dict[str, int] = field(default_factory=dict)
```

### 1.4 Faction Manager

**File**: `world/factions/faction_manager.py`

```python
class FactionManager:
    """Manages all factions, relations, and faction-based logic."""
    
    def __init__(self):
        self.factions: Dict[str, Faction] = {}
        self.global_relations: Dict[Tuple[str, str], int] = {}  # (faction1, faction2) -> relation
    
    def get_faction(self, faction_id: str) -> Optional[Faction]
    def get_relation(self, faction1: str, faction2: str) -> int
    def set_relation(self, faction1: str, faction2: str, value: int)
    def get_parties_for_faction(self, faction_id: str) -> List[RoamingParty]
    def get_pois_for_faction(self, faction_id: str) -> List[PointOfInterest]
```

---

## Phase 2: Battle System Integration

### 2.1 Party-to-Battle Unit Conversion

**File**: `world/overworld/battle_conversion.py`

```python
def party_to_battle_units(
    party: RoamingParty,
    party_type: PartyType,
    game: Game
) -> List[Enemy]:
    """
    Convert a roaming party into battle units.
    
    - Uses party_type.battle_unit_template if available
    - Falls back to party_type.combat_strength for scaling
    - Creates appropriate number of units based on party size
    """
    pass

def create_battle_from_party(
    party: RoamingParty,
    party_type: PartyType,
    game: Game
) -> BattleScene:
    """Create a battle scene from a party encounter."""
    pass
```

### 2.2 Allied Party Support

**File**: `world/overworld/allied_battle.py`

```python
def get_allied_parties_for_battle(
    player_position: Tuple[int, int],
    overworld_map: OverworldMap,
    player_faction: Optional[str]
) -> List[RoamingParty]:
    """
    Get friendly parties that can join the player in battle.
    
    - Checks nearby parties
    - Filters by faction alignment
    - Returns parties willing to help
    """
    pass

def add_allies_to_battle(
    battle: BattleScene,
    allies: List[RoamingParty]
) -> None:
    """Add allied parties as friendly units in battle."""
    pass
```

### 2.3 Battle Integration Points

**Modify**: `engine/controllers/overworld.py`

- When player attacks a party → create battle
- When hostile party attacks player → create battle
- When player is attacked → check for nearby allies
- After battle → update faction relations based on outcome

**Modify**: `engine/scenes/party_interaction_scene.py`

- "Attack" action → trigger battle
- Show faction relations before attacking

---

## Phase 3: Expanded Party Capabilities

### 3.1 Party Size & Composition

**File**: `world/overworld/roaming_party.py` (extend)

```python
@dataclass
class PartyMember:
    """Individual member of a party."""
    unit_type: str  # "warrior", "archer", "mage", etc.
    level: int
    equipment: Dict[str, Optional[str]]
    
@dataclass
class RoamingParty:
    # ... existing fields ...
    members: List[PartyMember] = field(default_factory=list)
    party_size: int = 1  # Number of members
    max_party_size: int = 5
```

### 3.2 Party Missions & Objectives

**File**: `world/overworld/party_missions.py`

```python
@dataclass
class PartyMission:
    """Mission a party is on."""
    mission_type: str  # "patrol", "escort", "raid", "trade", etc.
    target_poi_id: Optional[str] = None
    target_party_id: Optional[str] = None
    objective: str = ""
    reward: Dict[str, Any] = field(default_factory=dict)
```

### 3.3 Dynamic Party Behavior

**File**: `world/overworld/party_ai.py` (extend)

- Parties with missions follow mission objectives
- Escort missions: party follows another party
- Raid missions: party targets specific POIs
- Trade missions: party travels between specific locations

---

## Phase 4: UI System Overhaul

### 4.1 File Organization

```
ui/
├── screens/
│   ├── __init__.py
│   ├── base_screen.py          # Base class for all screens
│   ├── character_screen.py     # Character sheet (refactored)
│   ├── skills_screen.py        # Skills (refactored)
│   ├── quests_screen.py        # Quest journal (refactored)
│   ├── inventory_screen.py     # Inventory (fixed)
│   ├── party_screen.py         # NEW: Party management
│   ├── faction_screen.py       # NEW: Faction relations
│   └── trade_screen.py         # Trade interface
├── overworld/
│   ├── hud.py                  # Overworld HUD
│   ├── poi_tooltips.py
│   └── party_tooltips.py
└── battle/
    └── hud.py                  # Battle HUD
```

### 4.2 Party Screen

**File**: `ui/screens/party_screen.py`

**Features**:
- List all party members (hero + companions)
- Show party composition
- Manage party formation
- View party stats summary
- Assign roles/positions
- Equipment overview

**Layout**:
```
┌─────────────────────────────────────┐
│ Party Management                    │
├─────────────────────────────────────┤
│ Hero: [Name] [Class] [Level]        │
│ ├─ HP: 100/100                      │
│ ├─ Equipment: [Weapon] [Armor]...   │
│ └─ Skills: [Skill1] [Skill2]...    │
│                                     │
│ Companions:                         │
│ [1] Companion Name [Class] [Level]  │
│ [2] Companion Name [Class] [Level]  │
│ ...                                 │
│                                     │
│ Party Stats:                        │
│ Total HP: 300                       │
│ Average Level: 5                    │
│                                     │
│ [Manage] [Equipment] [Skills]      │
└─────────────────────────────────────┘
```

### 4.3 Faction Screen

**File**: `ui/screens/faction_screen.py`

**Features**:
- List all known factions
- Show relations with each faction
- View faction-controlled POIs
- See faction party types
- Track reputation changes

### 4.4 Inventory Screen Fixes

**File**: `ui/screens/inventory_screen.py`

**Issues to Fix**:
- Item stacking
- Equipment slots
- Item tooltips
- Drag & drop (if applicable)
- Quick actions

### 4.5 Skills Screen Improvements

**File**: `ui/screens/skills_screen.py`

**Improvements**:
- Better visual hierarchy
- Skill trees/connections
- Filter by class/type
- Search functionality
- Skill previews

### 4.6 Quests Screen Improvements

**File**: `ui/screens/quests_screen.py`

**Improvements**:
- Quest categories (active, completed, failed)
- Quest details panel
- Quest objectives tracking
- Quest rewards preview
- Quest giver information

---

## Phase 5: Integration Architecture

### 5.1 System Dependencies

```
Game Core
├── Overworld System
│   ├── Faction Manager
│   ├── Party Manager
│   └── POI System
├── Battle System
│   ├── Battle Scene
│   └── Unit Creation
└── UI System
    ├── Screen Manager
    └── Individual Screens
```

### 5.2 Data Flow

**Party → Battle**:
1. Player encounters party
2. Check faction relations
3. Convert party to battle units
4. Check for allies
5. Create battle scene
6. After battle: update relations

**Faction → POI**:
1. POI belongs to faction
2. Faction controls POI behavior
3. POI spawns faction parties
4. POI provides faction services

**Faction → Party**:
1. Party belongs to faction
2. Party follows faction objectives
3. Party affects faction relations
4. Party can join battles for faction

### 5.3 Event System (Future)

**File**: `systems/events.py`

For loose coupling between systems:
- Faction events (war declared, peace made)
- Party events (party destroyed, mission completed)
- Battle events (battle won, ally joined)
- POI events (POI captured, faction changed)

---

## Implementation Order

### Phase 1: Foundation (Week 1-2)
1. Create faction system structure
2. Add faction data to POIs
3. Add faction data to parties
4. Create faction manager
5. Test basic faction assignment

### Phase 2: Battle Integration (Week 3-4)
1. Party-to-battle unit conversion
2. Battle scene creation from parties
3. Allied party support
4. Faction-based battle outcomes
5. Test battle integration

### Phase 3: Party Expansion (Week 5-6)
1. Party member system
2. Party missions
3. Enhanced party AI
4. Party size management
5. Test party behaviors

### Phase 4: UI Overhaul (Week 7-8)
1. Refactor screen structure
2. Create party screen
3. Create faction screen
4. Fix inventory screen
5. Improve skills/quests screens
6. Test all UI screens

### Phase 5: Polish & Integration (Week 9-10)
1. Connect all systems
2. Add faction events
3. Balance party/battle interactions
4. UI polish
5. Testing & bug fixes

---

## File Structure

### New Files to Create

```
systems/
├── factions.py                    # Faction definitions
└── events.py                      # Event system (future)

world/
├── factions/
│   ├── __init__.py
│   └── faction_manager.py         # Faction management
└── overworld/
    ├── battle_conversion.py        # Party → Battle units
    ├── allied_battle.py           # Allied party support
    └── party_missions.py          # Party mission system

ui/
├── screens/
│   ├── party_screen.py            # Party management
│   └── faction_screen.py          # Faction relations
└── components/                     # Reusable UI components
    ├── stat_display.py
    ├── item_list.py
    └── quest_list.py
```

### Files to Modify

```
world/poi/base.py                  # Add faction_id
world/overworld/party_types.py     # Add faction_id, battle_unit_template
world/overworld/roaming_party.py  # Add faction_id, members, missions
world/overworld/party_ai.py        # Add mission-based behavior
world/overworld/party_manager.py   # Add faction filtering
engine/controllers/overworld.py     # Add battle triggers
engine/scenes/party_interaction_scene.py  # Add faction info
ui/screens/inventory_screen.py     # Fix inventory
ui/screens/skills_screen.py        # Improve skills UI
ui/screens/quests_screen.py        # Improve quests UI
```

---

## Design Principles

### 1. Extensibility
- Use registry patterns for factions, party types, POI types
- Make systems pluggable (add new types without core changes)
- Use composition over inheritance

### 2. Separation of Concerns
- Faction logic separate from party logic
- Battle conversion separate from battle execution
- UI separate from game logic

### 3. Data-Driven Design
- Factions defined in data files
- Party types in code but extensible
- POI types use registry pattern

### 4. Backward Compatibility
- Existing parties work without factions (faction_id = None)
- Existing POIs work without factions
- Battle system unchanged for non-party battles

### 5. Performance
- Faction manager caches relations
- Party queries use spatial indexing
- UI screens lazy-load data

---

## Testing Strategy

### Unit Tests
- Faction relations calculations
- Party-to-battle conversion
- Faction filtering

### Integration Tests
- Party encounters trigger battles
- Allied parties join battles
- Faction relations update after battles

### UI Tests
- All screens open/close correctly
- Navigation works
- Data displays correctly

---

## Future Considerations

### Potential Additions
- Faction diplomacy system
- Faction wars/campaigns
- Faction-specific quests
- Faction reputation rewards
- Multi-faction POIs (contested)
- Faction-specific items/equipment
- Faction leaders/characters

### Scalability
- Support for 10+ factions
- 100+ parties on map
- Complex faction relationships
- Dynamic faction creation

---

## Risk Mitigation

### Risks
1. **System Complexity**: Too many interconnected systems
   - *Mitigation*: Clear interfaces, documentation, incremental implementation

2. **Performance**: Too many parties/calculations
   - *Mitigation*: Spatial indexing, caching, lazy evaluation

3. **UI Overload**: Too many screens/options
   - *Mitigation*: Clear navigation, contextual menus, progressive disclosure

4. **Balance Issues**: Factions/parties too powerful/weak
   - *Mitigation*: Data-driven balance, easy tweaking, playtesting

---

## Conclusion

This plan provides a structured approach to:
- Adding factions without breaking existing systems
- Integrating parties with battles
- Expanding party capabilities
- Improving UI organization
- Maintaining clean architecture

Each phase builds on the previous one, allowing for incremental development and testing. The modular design ensures that systems can be added/changed without breaking existing functionality.

