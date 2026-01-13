# Combat System Integration Plan

## Overview

This document outlines how to integrate the combat system with the overworld, faction system, and roaming party system. The goal is to create a seamless flow where parties on the overworld can engage in combat, with faction relationships affecting combat outcomes and party behaviors.

## Current State Analysis

### Existing Systems

1. **Battle System** (`engine/battle/scene.py`)
   - Turn-based combat on a grid
   - Supports player + companions vs enemies
   - Uses `Enemy` entities created from `EnemyArchetype`
   - Battle scene is self-contained

2. **Overworld System** (`world/overworld/`)
   - Tile-based overworld map
   - Roaming parties (`RoamingParty`) with types (`PartyType`)
   - Party manager handles spawning and updates
   - Party AI handles movement and behavior

3. **Faction System** (`systems/factions.py`)
   - Faction definitions with relations
   - Parties can have `faction_id`
   - POIs can have `faction_id`
   - Faction manager (planned/partial)

4. **Party Interaction** (`engine/scenes/party_interaction_scene.py`)
   - Dialog screen for party interactions
   - "Attack" action exists but doesn't trigger combat yet
   - Shows party info and available actions

### Gaps to Address

1. **Party → Battle Conversion**: No system to convert `RoamingParty` to battle `Enemy` units
2. **Combat Triggers**: Attack action doesn't actually start combat
3. **Faction Relations**: Not used to determine combat behavior
4. **Allied Parties**: No system for friendly parties to join battles
5. **Post-Combat Effects**: No faction relation updates after combat
6. **Party State**: Parties don't track if they're defeated

---

## Integration Architecture

### 0. Dynamic Enemy Scaling System

**Core Design Principle**: Enemy count scales dynamically with player party size to maintain balanced, challenging combat.

#### Scaling Formula

```
Base Enemies (party_size = 2, hero + 1 companion): 1-4 enemies
  - Minimum: 1 enemy (allows weak parties even at higher levels)
  - Maximum: 2 + (combat_strength - 1) enemies
  - Example: combat_strength 2 → 1-3 enemies base

Scaling Per Party Member: +1.0 to +2.0 enemies per member
  - Formula: base + (party_size - 2) × (1.0 to 2.0)
  - Variation: ±0.3 enemies per member (random)
  - Example: party_size 4 → base + 2-4 additional enemies

Total Range:
  - Minimum: 1 enemy (always)
  - Maximum: 8 enemies (default, configurable)
  - Can be increased later for epic battles
```

#### Examples

| Player Party Size | Composition | Base | Additional | Total Range | Typical | Notes |
|-------------------|--------------|------------|-------------|---------|
| 2 (Hero + 1)      | Starting    | 1-3  | +0         | 1-3         | 2       | Game start |
| 3 (Hero + 2)      | Growing     | 1-3  | +1-2       | 2-5         | 3-4     | Early game |
| 4 (Hero + 3)      | Established | 1-3  | +2-4       | 3-7         | 4-5     | Mid game |
| 5 (Hero + 4)      | Full party  | 1-3  | +3-6       | 4-9 (capped 8) | 5-6     | Late game |
| 6+ (Hero + 5+)    | Expanded    | 1-3  | +4-8       | 5-11 (capped 8) | 6-7     | Max party |

**Key Feature**: Minimum of 1 enemy ensures you can still find weak parties (like a single goblin scout) even with a full party, creating variety and allowing for easier encounters.

#### Party Type Modifiers

Different party types have special scaling rules:

- **Swarm Types** (goblin, wolf, monster, rat): +50% more enemies
  - Example: 4 enemies → 6 enemies
  - Rationale: Weak individually, strong in numbers

- **Elite Types** (knight, boss, guard, noble): -25% fewer enemies
  - Example: 4 enemies → 3 enemies
  - Rationale: Strong individually, fewer needed

- **Balanced Types** (bandit, adventurer, etc.): Standard scaling
  - No modifier applied

#### XP Balancing

To prevent XP inflation with more enemies:
- XP per enemy decreases as total enemy count increases
- Formula: `base_xp / (1.0 + (total_enemies - 1) × 0.3)`
- Total XP reward remains balanced regardless of enemy count

#### Companion Death Handling

When companions die during gameplay:
- Enemy count is calculated **at battle start** based on current party size
- If companions die mid-game, future battles will have fewer enemies
- This creates natural difficulty adjustment: losing companions = easier battles
- Future enhancement: Could add "persistent death" mode where enemy count adjusts dynamically

#### Extensibility

The system is designed for future expansion:

1. **Increase Max Enemies**: Change `MAX_ENEMIES` constant (default: 8)
   - Can be increased to 10, 12, 15+ for epic battles
   - Could even scale with player level (e.g., +1 max per 5 levels)

2. **Add New Party Types**: Extend `_apply_party_type_scaling_rules()`
   - Easy to add new party types with custom scaling
   - Example: `"dragon_pack"` → elite scaling (-25%)

3. **Pack Types System**: New pack types can have unique scaling
   - **Swarm Packs**: "goblin_swarm", "rat_swarm" → +50% enemies
   - **Elite Packs**: "knight_squad", "boss_guard" → -25% enemies
   - **Balanced Packs**: Standard scaling
   - **Mixed Packs**: Combination of types (future)

4. **Enemy Type Expansion**: 
   - New enemy archetypes automatically work with the system
   - Just set `battle_unit_template` in party type definition
   - System handles scaling automatically

5. **Difficulty Settings**: 
   - Easy: -25% enemy count
   - Normal: Standard scaling
   - Hard: +25% enemy count
   - Nightmare: +50% enemy count

### 1. Party-to-Battle Conversion System

**File**: `world/overworld/battle_conversion.py`

```python
"""
Convert roaming parties into battle units.

This module handles the conversion of overworld parties into enemies
that can fight in the battle system.
"""

from typing import List, Optional, TYPE_CHECKING
from world.entities import Enemy
from systems.enemies import get_archetype, EnemyArchetype

if TYPE_CHECKING:
    from .roaming_party import RoamingParty
    from .party_types import PartyType
    from engine.core.game import Game


def party_to_battle_enemies(
    party: "RoamingParty",
    party_type: "PartyType",
    game: "Game",
    player_level: int = 1
) -> List[Enemy]:
    """
    Convert a roaming party into a list of Enemy entities for battle.
    
    Strategy:
    1. Calculate player party size (hero + active companions)
    2. Scale enemy count based on player party size (dynamic scaling)
    3. Use party_type.battle_unit_template if available (enemy archetype ID)
    4. Otherwise, use party_type.combat_strength to scale generic enemies
    5. Scale enemy stats based on player level and combat_strength
    
    Enemy Count Scaling:
    - Base: 1-3 enemies (when player has 1 character = just hero)
    - Scales up: +1-2 enemies per additional party member
    - Formula: base_count + (party_size - 1) * scaling_factor
    - Minimum: 1 enemy
    - Maximum: Configurable limit (default: 8, can be increased later)
    
    Args:
        party: The roaming party to convert
        party_type: The party's type definition
        game: Game instance (for map/context and party access)
        player_level: Current player level (for scaling)
    
    Returns:
        List of Enemy entities ready for battle
    """
    enemies = []
    
    # Calculate player party size (hero + active companions)
    player_party_size = _get_player_party_size(game)
    
    # Calculate enemy count based on party size and combat strength
    num_enemies = _calculate_enemy_count(
        player_party_size=player_party_size,
        party_combat_strength=party_type.combat_strength,
        party_type_id=party_type.id
    )
    
    # Try to use battle_unit_template if available
    if party_type.battle_unit_template:
        archetype = get_archetype(party_type.battle_unit_template)
        if archetype:
            # Use the specified archetype
            for i in range(num_enemies):
                enemy = _create_enemy_from_archetype(
                    archetype, player_level, party, i, num_enemies
                )
                enemies.append(enemy)
            return enemies
    
    # Fallback: Create generic enemies based on combat_strength
    # Use a default archetype or create enemies with scaled stats
    default_archetype = _get_default_archetype_for_strength(
        party_type.combat_strength
    )
    
    for i in range(num_enemies):
        enemy = _create_enemy_from_archetype(
            default_archetype, player_level, party, i, num_enemies
        )
        enemies.append(enemy)
    
    return enemies


def _get_player_party_size(game: "Game") -> int:
    """
    Get the current player party size (hero + active companions).
    
    Note: The game starts with hero + 1 companion, so minimum party_size = 2.
    
    Args:
        game: Game instance
    
    Returns:
        Party size (minimum 2: hero + 1 companion)
    """
    # Hero always counts as 1
    party_size = 1
    
    # Add active companions
    if hasattr(game, 'party') and game.party:
        # Count only active (alive) companions
        # For now, all companions in party list are considered active
        # In the future, we might track alive/dead status
        party_size += len(game.party)
    
    # Ensure minimum of 2 (hero + 1 companion at game start)
    # If somehow party is smaller, treat as 2 for scaling purposes
    return max(2, party_size)


def _calculate_enemy_count(
    player_party_size: int,
    party_combat_strength: int,
    party_type_id: str
) -> int:
    """
    Calculate the number of enemies to spawn based on player party size.
    
    Scaling Formula:
    - Base count: 1-3 enemies (when party_size = 2, hero + 1 companion)
    - Per additional party member: +1.0 to +2.0 enemies (with variation)
    - Combat strength affects base count
    - Party type can have special scaling rules
    - Minimum always 1 to allow weak encounters even with large party
    
    Configuration:
    - MIN_ENEMIES: 1 (absolute minimum, allows variety)
    - MAX_ENEMIES: 8 (default, can be increased later)
    - BASE_SCALING_MIN: 1.0 enemies per party member (minimum)
    - BASE_SCALING_MAX: 2.0 enemies per party member (maximum)
    
    Args:
        player_party_size: Number of characters in player party (2+)
                          Note: Game starts with hero + 1 companion = 2
        party_combat_strength: Combat strength of the party (1-5)
        party_type_id: ID of the party type (for special rules)
    
    Returns:
        Number of enemies to spawn (1-8, with large variation)
    """
    import random
    
    # Configuration constants (can be moved to settings later)
    MIN_ENEMIES = 1  # Always allow weak encounters
    MAX_ENEMIES = 8  # Can be increased later for larger battles
    BASE_ENEMIES_MIN = 1  # Minimum base (when party_size = 2)
    BASE_ENEMIES_MAX = 3  # Maximum base (when party_size = 2)
    SCALING_MIN = 1.0  # Minimum enemies per additional party member
    SCALING_MAX = 2.0  # Maximum enemies per additional party member
    
    # Ensure minimum party size is 2 (hero + 1 companion)
    effective_party_size = max(2, player_party_size)
    
    # Base enemy count (when party_size = 2, hero + 1 companion)
    # Combat strength affects base count: stronger parties = more base enemies
    # But keep minimum at 1 to allow weak encounters
    base_min = BASE_ENEMIES_MIN  # Always 1
    base_max = BASE_ENEMIES_MAX + (party_combat_strength - 1)  # 1-5 max base
    
    # Random base count within range (creates variety)
    base_count = random.randint(base_min, base_max)
    
    # Scale based on party size beyond the base (party_size - 2)
    # Each additional party member adds 1.0 to 2.0 enemies
    additional_members = effective_party_size - 2  # How many beyond hero+1
    
    if additional_members > 0:
        # Random scaling factor per member (1.0 to 2.0)
        scaling_per_member = random.uniform(SCALING_MIN, SCALING_MAX)
        
        # Add variation: ±0.3 enemies per member for more randomness
        variation = random.uniform(-0.3, 0.3)
        
        # Calculate additional enemies
        additional_enemies = int(additional_members * (scaling_per_member + variation))
        additional_enemies = max(0, additional_enemies)  # Can't be negative
    else:
        additional_enemies = 0
    
    total_count = base_count + additional_enemies
    
    # Apply min/max bounds
    # Keep minimum at 1 to ensure variety (weak parties can still appear)
    total_count = max(MIN_ENEMIES, min(MAX_ENEMIES, total_count))
    
    # Special rules for specific party types (extensible)
    total_count = _apply_party_type_scaling_rules(
        total_count, party_type_id, effective_party_size
    )
    
    # Final bounds check after party type modifiers
    total_count = max(MIN_ENEMIES, min(MAX_ENEMIES, total_count))
    
    return total_count


def _apply_party_type_scaling_rules(
    base_count: int,
    party_type_id: str,
    player_party_size: int
) -> int:
    """
    Apply special scaling rules for specific party types.
    
    This allows different party types to have unique scaling behavior:
    - Swarm types (goblins, wolves): More enemies, weaker individually
    - Elite types (knights, bosses): Fewer enemies, stronger individually
    - Balanced types: Standard scaling
    
    Args:
        base_count: Calculated enemy count
        party_type_id: ID of the party type
        player_party_size: Player party size
    
    Returns:
        Adjusted enemy count
    """
    # Swarm types: +50% more enemies (rounded)
    SWARM_TYPES = {"goblin", "wolf", "monster", "rat"}
    if party_type_id in SWARM_TYPES:
        return int(base_count * 1.5)
    
    # Elite types: -25% fewer enemies (but stronger)
    ELITE_TYPES = {"knight", "boss", "guard", "noble"}
    if party_type_id in ELITE_TYPES:
        return max(1, int(base_count * 0.75))
    
    # Balanced types: no change
    return base_count


def _create_enemy_from_archetype(
    archetype: EnemyArchetype,
    player_level: int,
    party: "RoamingParty",
    index: int,
    total_enemies: int
) -> Enemy:
    """
    Create an Enemy entity from an archetype.
    
    Args:
        archetype: Enemy archetype definition
        player_level: Current player level
        party: The roaming party this enemy belongs to
        index: Index of this enemy (0-based)
        total_enemies: Total number of enemies in this battle (for naming)
    
    Returns:
        Enemy entity ready for battle
    """
    from world.entities import create_enemy
    
    # Calculate stats based on archetype and level
    floor = max(1, player_level)  # Use player level as "floor"
    
    hp = int(archetype.base_hp + archetype.hp_per_floor * (floor - 1))
    attack = int(archetype.base_attack + archetype.atk_per_floor * (floor - 1))
    defense = int(archetype.base_defense + archetype.def_per_floor * (floor - 1))
    xp = int(archetype.base_xp + archetype.xp_per_floor * (floor - 1))
    
    # Adjust XP per enemy based on total count (more enemies = less XP each)
    # This keeps total XP reward balanced regardless of enemy count
    if total_enemies > 1:
        xp = int(xp / (1.0 + (total_enemies - 1) * 0.3))  # Diminishing returns
        xp = max(1, xp)  # Minimum 1 XP
    
    # Create enemy with party context
    enemy = create_enemy(
        archetype_id=archetype.id,
        name=f"{party.party_type_id.title()} {index + 1}",  # e.g., "Bandit 1"
        hp=hp,
        attack=attack,
        defense=defense,
        xp=xp,
        skill_ids=archetype.skill_ids.copy(),
    )
    
    # Store party reference for post-combat updates
    enemy.party_id = party.party_id
    
    return enemy


def _get_default_archetype_for_strength(strength: int) -> EnemyArchetype:
    """Get a default enemy archetype based on combat strength."""
    # Map combat_strength (1-5) to appropriate archetypes
    # This is a fallback when battle_unit_template is not set
    strength_to_archetype = {
        1: "goblin",      # Weak enemies
        2: "bandit",      # Moderate enemies
        3: "orc",         # Strong enemies
        4: "troll",       # Very strong enemies
        5: "dragon",      # Boss-level enemies
    }
    
    archetype_id = strength_to_archetype.get(strength, "bandit")
    archetype = get_archetype(archetype_id)
    
    if archetype is None:
        # Ultimate fallback: create a basic archetype
        from systems.enemies import EnemyArchetype
        return EnemyArchetype(
            id="generic",
            name="Generic Enemy",
            role="Fighter",
            tier=1,
            ai_profile="aggressive",
            base_hp=30 + (strength * 10),
            hp_per_floor=5.0,
            base_attack=5 + strength,
            atk_per_floor=1.0,
            base_defense=1 + strength,
            def_per_floor=0.5,
            base_xp=10 + (strength * 5),
            xp_per_floor=2.0,
            skill_ids=[],
            base_initiative=10,
        )
    
    return archetype
```

### 2. Combat Trigger System

**Modify**: `engine/scenes/party_interaction_scene.py`

```python
def _action_attack(self) -> None:
    """Attack the party and trigger combat."""
    from world.overworld.battle_conversion import party_to_battle_enemies
    from engine.battle.scene import BattleScene
    
    # Convert party to enemies
    enemies = party_to_battle_enemies(
        party=self.party,
        party_type=self.party_type,
        game=self.game,
        player_level=self.game.player.level if self.game.player else 1
    )
    
    if not enemies:
        self.game.add_message("Unable to engage in combat.")
        self.closed = True
        return
    
    # Close interaction screen
    self.closed = True
    
    # Trigger battle
    self.game.start_battle(enemies, context_party=self.party)
```

**Modify**: `engine/core/game.py` (add battle trigger method)

```python
def start_battle(
    self,
    enemies: List[Enemy],
    context_party: Optional[RoamingParty] = None
) -> None:
    """
    Start a battle with the given enemies.
    
    Args:
        enemies: List of Enemy entities to fight
        context_party: Optional party that triggered this battle (for post-combat updates)
    """
    from engine.battle.scene import BattleScene
    
    # Get player companions
    companions = []
    if self.party_manager:
        companions = self.party_manager.get_active_companions()
    
    # Create battle scene
    battle = BattleScene(
        player=self.player,
        enemies=enemies,
        font=self.font,
        companions=companions,
        game=self
    )
    
    # Store context for post-combat
    battle.context_party = context_party
    
    # Switch to battle state
    self.current_state = GameState.BATTLE
    self.battle_scene = battle
```

### 3. Faction-Based Combat Logic

**File**: `world/overworld/faction_combat.py`

```python
"""
Faction-based combat logic.

Determines combat behavior based on faction relationships.
"""

from typing import Optional, List, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .roaming_party import RoamingParty
    from .party_types import PartyType
    from engine.core.game import Game


def should_initiate_combat(
    party: "RoamingParty",
    party_type: "PartyType",
    game: "Game",
    player_faction: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Determine if combat should be initiated with a party.
    
    Returns:
        (should_fight, reason)
        - should_fight: True if combat should happen
        - reason: Explanation for the decision
    """
    # Check party alignment
    if party_type.alignment.value == "hostile":
        return (True, "Hostile party")
    
    if party_type.alignment.value == "friendly":
        return (False, "Friendly party")
    
    # Check faction relations
    if player_faction and party.faction_id:
        relation = _get_faction_relation(
            player_faction, party.faction_id, game
        )
        
        if relation < -50:  # Very hostile
            return (True, "Hostile faction")
        elif relation < 0:  # Somewhat hostile
            return (True, "Unfriendly faction")
        elif relation > 50:  # Very friendly
            return (False, "Allied faction")
    
    # Default: neutral parties can be attacked but aren't automatically hostile
    return (False, "Neutral party")


def get_allied_parties_for_battle(
    player_position: Tuple[int, int],
    overworld_map: "OverworldMap",
    player_faction: Optional[str] = None,
    radius: int = 3
) -> List["RoamingParty"]:
    """
    Get friendly parties that can join the player in battle.
    
    Args:
        player_position: Player's (x, y) position
        overworld_map: The overworld map
        player_faction: Player's faction ID
        radius: Search radius in tiles
    
    Returns:
        List of allied parties willing to help
    """
    if not overworld_map.party_manager:
        return []
    
    # Get parties in range
    nearby_parties = overworld_map.party_manager.get_parties_in_range(
        center_x=player_position[0],
        center_y=player_position[1],
        radius=radius
    )
    
    allies = []
    for party in nearby_parties:
        from .party_types import get_party_type
        party_type = get_party_type(party.party_type_id)
        if not party_type:
            continue
        
        # Check if party can join battle
        if not party_type.can_join_battle:
            continue
        
        # Check alignment
        if party_type.alignment.value == "friendly":
            allies.append(party)
            continue
        
        # Check faction relations
        if player_faction and party.faction_id:
            relation = _get_faction_relation(
                player_faction, party.faction_id, overworld_map
            )
            if relation > 50:  # Very friendly
                allies.append(party)
    
    return allies


def _get_faction_relation(
    faction1: str,
    faction2: str,
    game_or_map
) -> int:
    """Get relation between two factions (-100 to 100)."""
    # Try to get from faction manager
    if hasattr(game_or_map, 'faction_manager') and game_or_map.faction_manager:
        return game_or_map.faction_manager.get_relation(faction1, faction2)
    
    # Fallback: check default relations
    from systems.factions import get_faction
    faction = get_faction(faction1)
    if faction:
        return faction.default_relations.get(faction2, 0)
    
    return 0  # Neutral by default
```

### 4. Post-Combat Updates

**Modify**: `engine/battle/scene.py` (add post-combat callback)

```python
def on_battle_end(self, victory: bool) -> None:
    """Called when battle ends."""
    # Handle post-combat updates
    if hasattr(self, 'context_party') and self.context_party:
        from world.overworld.post_combat import handle_party_defeat
        
        if not victory:
            # Player lost - party might pursue or flee
            pass
        else:
            # Player won - update party state and faction relations
            handle_party_defeat(
                party=self.context_party,
                game=self.game
            )
```

**File**: `world/overworld/post_combat.py`

```python
"""
Handle post-combat updates.

Updates party state, faction relations, and loot distribution.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .roaming_party import RoamingParty
    from engine.core.game import Game


def handle_party_defeat(
    party: "RoamingParty",
    game: "Game"
) -> None:
    """
    Handle what happens when a party is defeated.
    
    - Remove party from map (or mark as defeated)
    - Update faction relations
    - Distribute loot (gold, items)
    - Update party manager
    """
    from .party_types import get_party_type
    
    party_type = get_party_type(party.party_type_id)
    if not party_type:
        return
    
    # Remove party from map
    if game.overworld_map and game.overworld_map.party_manager:
        game.overworld_map.party_manager.remove_party(party.party_id)
    
    # Update faction relations
    _update_faction_relations(party, party_type, game)
    
    # Distribute loot
    _distribute_loot(party, party_type, game)
    
    # Add message
    game.add_message(f"Defeated {party_type.name}!")


def _update_faction_relations(
    party: "RoamingParty",
    party_type: "PartyType",
    game: "Game"
) -> None:
    """Update faction relations based on combat outcome."""
    if not party.faction_id:
        return
    
    # Get player faction (if any)
    player_faction = getattr(game, 'player_faction', None)
    if not player_faction:
        return
    
    # Decrease relation with defeated party's faction
    if game.overworld_map and game.overworld_map.faction_manager:
        current_relation = game.overworld_map.faction_manager.get_relation(
            player_faction, party.faction_id
        )
        # Decrease by 5-15 points depending on party type
        decrease = 5 + (party_type.combat_strength * 2)
        new_relation = max(-100, current_relation - decrease)
        
        game.overworld_map.faction_manager.set_relation(
            player_faction, party.faction_id, new_relation
        )
        
        # Also update relations with allied factions
        _update_allied_faction_relations(
            party.faction_id, player_faction, game, decrease // 2
        )


def _update_allied_faction_relations(
    defeated_faction: str,
    player_faction: str,
    game: "Game",
    relation_change: int
) -> None:
    """Update relations with factions allied to the defeated faction."""
    # This is a simplified version - could be more sophisticated
    from systems.factions import get_faction
    
    defeated = get_faction(defeated_faction)
    if not defeated:
        return
    
    # Check default relations to find allies
    for other_faction_id, relation in defeated.default_relations.items():
        if relation > 30:  # Allied
            if game.overworld_map and game.overworld_map.faction_manager:
                current = game.overworld_map.faction_manager.get_relation(
                    player_faction, other_faction_id
                )
                new_relation = max(-100, current - relation_change)
                game.overworld_map.faction_manager.set_relation(
                    player_faction, other_faction_id, new_relation
                )


def _distribute_loot(
    party: "RoamingParty",
    party_type: "PartyType",
    game: "Game"
) -> None:
    """Distribute loot from defeated party."""
    # Give gold
    if party.gold > 0:
        if hasattr(game, 'player') and game.player:
            game.player.gold += party.gold
            game.add_message(f"Gained {party.gold} gold!")
    
    # Give items (if any)
    if party.items:
        for item_id in party.items:
            # Add to player inventory
            if hasattr(game, 'inventory_manager'):
                game.inventory_manager.add_item(item_id)
                from systems.inventory import get_item_def
                item_def = get_item_def(item_id)
                if item_def:
                    game.add_message(f"Gained {item_def.name}!")
```

### 5. Automatic Combat Triggers

**Modify**: `engine/controllers/overworld.py`

Add automatic combat triggers for hostile parties:

```python
def _check_party_interactions(self) -> None:
    """Check for automatic party interactions (combat, etc.)."""
    if not self.game.overworld_map or not self.game.overworld_map.party_manager:
        return
    
    player_x, player_y = self.game.overworld_map.get_player_position()
    
    # Check for hostile parties that attack automatically
    nearby_parties = self.game.overworld_map.party_manager.get_parties_in_range(
        center_x=player_x,
        center_y=player_y,
        radius=1  # Adjacent tiles only
    )
    
    for party in nearby_parties:
        from world.overworld.party_types import get_party_type
        party_type = get_party_type(party.party_type_id)
        if not party_type:
            continue
        
        # Check if party should attack automatically
        if (party_type.alignment.value == "hostile" and 
            party_type.can_attack and
            not party.in_combat):
            
            # Trigger combat
            self._trigger_combat_with_party(party, party_type)


def _trigger_combat_with_party(
    self,
    party: "RoamingParty",
    party_type: "PartyType"
) -> None:
    """Trigger combat with a party."""
    from world.overworld.battle_conversion import party_to_battle_enemies
    from world.overworld.faction_combat import should_initiate_combat
    
    # Check if combat should happen
    player_faction = getattr(self.game, 'player_faction', None)
    should_fight, reason = should_initiate_combat(
        party, party_type, self.game, player_faction
    )
    
    if not should_fight:
        return
    
    # Mark party as in combat
    party.in_combat = True
    
    # Convert to enemies
    enemies = party_to_battle_enemies(
        party=party,
        party_type=party_type,
        game=self.game,
        player_level=self.game.player.level if self.game.player else 1
    )
    
    if enemies:
        self.game.add_message(f"{party_type.name} attacks!")
        self.game.start_battle(enemies, context_party=party)
```

---

## Integration Flow

### Combat Initiation Flow

```
1. Player encounters party (overworld)
   ↓
2. Party interaction screen opens
   ↓
3. Player selects "Attack" action
   ↓
4. Check faction relations (should_initiate_combat)
   ↓
5. Convert party to enemies (party_to_battle_enemies)
   ↓
6. Check for allied parties (get_allied_parties_for_battle)
   ↓
7. Start battle scene
   ↓
8. Battle plays out
   ↓
9. Battle ends (victory/defeat)
   ↓
10. Post-combat updates (handle_party_defeat)
    - Remove party from map
    - Update faction relations
    - Distribute loot
```

### Automatic Combat Flow

```
1. Hostile party moves adjacent to player
   ↓
2. Overworld controller detects proximity
   ↓
3. Check if party should attack (faction logic)
   ↓
4. Trigger combat automatically
   ↓
5. Same flow as manual combat (steps 5-10)
```

---

## Implementation Checklist

### Phase 1: Core Conversion System
- [ ] Create `world/overworld/battle_conversion.py`
- [ ] Implement `party_to_battle_enemies()`
- [ ] Implement `_create_enemy_from_archetype()`
- [ ] Implement `_get_default_archetype_for_strength()`
- [ ] Test conversion with different party types

### Phase 2: Combat Triggers
- [ ] Modify `party_interaction_scene.py` `_action_attack()`
- [ ] Add `start_battle()` method to `Game` class
- [ ] Test manual combat triggers
- [ ] Add automatic combat triggers in overworld controller
- [ ] Test automatic combat

### Phase 3: Faction Integration
- [ ] Create `world/overworld/faction_combat.py`
- [ ] Implement `should_initiate_combat()`
- [ ] Implement `get_allied_parties_for_battle()`
- [ ] Integrate faction checks into combat triggers
- [ ] Test faction-based combat behavior

### Phase 4: Post-Combat Updates
- [ ] Create `world/overworld/post_combat.py`
- [ ] Implement `handle_party_defeat()`
- [ ] Implement faction relation updates
- [ ] Implement loot distribution
- [ ] Add battle end callback to `BattleScene`
- [ ] Test post-combat updates

### Phase 5: Allied Party Support (Future)
- [ ] Extend battle scene to support allied units
- [ ] Implement allied party joining logic
- [ ] Add allied unit AI
- [ ] Test multi-party battles

### Phase 6: Polish & Balance
- [ ] Balance enemy scaling from parties
- [ ] Tune faction relation changes
- [ ] Add visual feedback for combat triggers
- [ ] Add sound effects
- [ ] Test edge cases

---

## Design Considerations

### 1. Enemy Scaling

Parties should scale appropriately to player level:
- Use `player_level` as the "floor" for enemy stats
- Apply `combat_strength` as a multiplier
- Ensure battles are challenging but fair

### 2. Faction Relations

Faction relations should:
- Change gradually (not too drastic)
- Have meaningful consequences
- Be visible to the player
- Allow for redemption/repair

### 3. Party Removal

When a party is defeated:
- Remove from map immediately
- Don't respawn too quickly
- Consider respawn timers for certain party types

### 4. Battle Context

Store context about the battle:
- Which party triggered it
- Faction relationships
- Special conditions (ambush, etc.)

### 5. Performance

Combat triggers should:
- Be efficient (don't check every frame)
- Only check when player moves
- Cache faction relations
- Limit concurrent battles

---

## Future Enhancements

### Combat System
1. **Multi-Party Battles**: Multiple parties fighting together
2. **Ambushes**: Surprise attacks from parties
3. **Retreat Mechanics**: Parties can flee from combat
4. **Boss Parties**: Special powerful parties as mini-bosses
5. **Formation System**: Parties have formations that affect battle

### Scaling & Balance
6. **Dynamic Difficulty**: Adjust enemy count based on player performance
7. **Level-Based Max Enemies**: Increase max enemies as player levels up
8. **Companion Death Impact**: Real-time enemy count adjustment (optional)
9. **Difficulty Settings**: Easy/Normal/Hard/Nightmare modes

### Party & Pack Types
10. **Pack Type System**: 
    - "wolf_pack_alpha" (large pack, swarm scaling)
    - "knight_squad" (elite group, elite scaling)
    - "mixed_raiding_party" (combination of types)
11. **Enemy Type Expansion**: 
    - More enemy archetypes
    - Unique abilities per type
    - Type-specific scaling rules

### World Systems
12. **Party Regeneration**: Defeated parties respawn after time
13. **Dynamic Relations**: Relations change based on player actions
14. **Quest Integration**: Combat tied to quest objectives
15. **Faction Wars**: Large-scale battles between factions

---

## Testing Strategy

### Unit Tests
- Party-to-enemy conversion
- Faction relation calculations
- Loot distribution

### Integration Tests
- Combat trigger flow
- Post-combat updates
- Faction relation changes

### Manual Testing
- Test all party types in combat
- Test faction-based behavior
- Test edge cases (no faction, neutral parties, etc.)
- Test automatic vs manual combat

---

## Conclusion

This integration plan provides a comprehensive approach to connecting combat with the overworld, factions, and parties. The modular design allows for incremental implementation and testing, ensuring each component works correctly before moving to the next phase.

