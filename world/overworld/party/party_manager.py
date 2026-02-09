"""
Manager for roaming parties on the overworld.

Handles spawning, updating, and managing all roaming parties.
"""

from typing import Dict, List, Optional, Tuple, Set, TYPE_CHECKING
from dataclasses import dataclass, field
import random

if TYPE_CHECKING:
    from ..map import OverworldMap
    from .roaming_party import RoamingParty
    from .party_types import PartyType, SpawnCategory
    from ...poi.base import PointOfInterest


@dataclass
class BattleState:
    """State of an ongoing battle between parties."""
    battle_id: str
    party1_id: str
    party2_id: str
    position: Tuple[int, int]  # Battle location
    turn_count: int = 0  # Number of turns the battle has lasted
    max_turns: int = 10  # Maximum turns before auto-resolution
    party1_health: int = 100  # Health percentage (0-100)
    party2_health: int = 100
    can_player_join: bool = True  # Whether player can still join
    player_joined: bool = False  # Whether player has joined
    side_joined: Optional[str] = None  # "party1" or "party2" if player joined


class PartyManager:
    """
    Manages all roaming parties on the overworld.
    
    Handles:
    - Spawning parties
    - Updating party AI
    - Party interactions
    - Rendering parties
    """
    
    def __init__(self, overworld_map: "OverworldMap"):
        """Initialize party manager."""
        self.overworld_map = overworld_map
        self.parties: Dict[str, "RoamingParty"] = {}
        self.current_time: float = 0.0
        self.spawn_timer: int = 0
        self.spawn_interval: int = 15  # Spawn new parties every 15 player moves (more frequent)
        self.max_parties: int = 100  # Increased max parties on map (more active world)
        
        # Track ongoing battles
        self.active_battles: Dict[str, "BattleState"] = {}  # Key: battle_id, Value: BattleState
    
    def add_party(self, party: "RoamingParty") -> None:
        """Add a party to the manager."""
        self.parties[party.party_id] = party
    
    def remove_party(self, party_id: str) -> None:
        """Remove a party from the manager."""
        if party_id in self.parties:
            del self.parties[party_id]
    
    def get_party(self, party_id: str) -> Optional["RoamingParty"]:
        """Get a party by ID."""
        return self.parties.get(party_id)
    
    def get_party_at(self, x: int, y: int) -> Optional["RoamingParty"]:
        """Get party at a specific position."""
        for party in self.parties.values():
            if party.x == x and party.y == y:
                return party
        return None
    
    def get_parties_in_range(
        self,
        center_x: int,
        center_y: int,
        radius: int,
    ) -> List["RoamingParty"]:
        """Get all parties within a radius."""
        result = []
        radius_sq = radius * radius
        
        for party in self.parties.values():
            dx = party.x - center_x
            dy = party.y - center_y
            dist_sq = dx * dx + dy * dy
            
            if dist_sq <= radius_sq:
                result.append(party)
        
        return result
    
    def spawn_random_party(
        self,
        player_level: int = 1,
        avoid_position: Optional[Tuple[int, int]] = None,
        min_distance: int = 10,
        spawn_category: Optional["SpawnCategory"] = None,  # WILDLIFE, HUMANOID, UNDEAD; None = all
    ) -> Optional["RoamingParty"]:
        """
        Spawn a random party based on spawn weights.
        
        Args:
            player_level: Current player level (for filtering)
            avoid_position: Position to avoid spawning near (e.g., player position)
            min_distance: Minimum distance from avoid_position
            spawn_category: If set, only spawn from this pool (WILDLIFE, HUMANOID, UNDEAD).
                None = use all types (default).
        
        Returns:
            The spawned party, or None if spawning failed
        """
        from .party_types import all_party_types, party_types_for_spawn_category, SpawnCategory
        from .party_power import get_spawn_weight_modifier_for_level

        # Choose type pool: all types or filtered by category
        if spawn_category is not None:
            candidate_types = party_types_for_spawn_category(spawn_category)
        else:
            candidate_types = all_party_types()

        # Get all valid party types for this level (min_level/max_level)
        valid_types = []
        for party_type in candidate_types:
            if (player_level >= party_type.min_level and
                    player_level <= party_type.max_level):
                # Scale weight by level: stronger types become more likely as player levels up
                modifier = get_spawn_weight_modifier_for_level(party_type, player_level)
                effective_weight = party_type.spawn_weight * modifier
                valid_types.append((party_type, max(0.1, effective_weight)))

        if not valid_types:
            return None

        # Weighted random selection (stronger parties more likely at higher level)
        total_weight = sum(weight for _, weight in valid_types)
        r = random.uniform(0, total_weight)
        cumulative = 0.0
        
        selected_type = None
        for party_type, weight in valid_types:
            cumulative += weight
            if r <= cumulative:
                selected_type = party_type
                break
        
        if selected_type is None:
            selected_type = valid_types[0][0]
        
        # Find a valid spawn position
        spawn_x, spawn_y = self._find_spawn_position(
            avoid_position=avoid_position,
            min_distance=min_distance,
        )
        
        if spawn_x is None:
            return None
        
        # Create party (pass player_level so size can scale slightly with progression)
        from .roaming_party import create_roaming_party
        party = create_roaming_party(
            party_type_id=selected_type.id,
            x=spawn_x,
            y=spawn_y,
            player_level=player_level,
        )
        
        # Assign faction if party type has one, or try to get from faction manager
        if not party.faction_id and selected_type.faction_id:
            party.faction_id = selected_type.faction_id
        elif not party.faction_id and self.overworld_map.faction_manager:
            # Try to get faction from faction manager based on party type
            faction_id = self.overworld_map.faction_manager.get_faction_for_party_type(selected_type.id)
            if faction_id:
                party.faction_id = faction_id
        
        # Initialize behavior-specific state
        if selected_type.behavior.value == "patrol":
            party.patrol_center_x = spawn_x
            party.patrol_center_y = spawn_y
            party.patrol_radius = random.randint(3, 8)
        elif selected_type.behavior.value == "guard":
            # Guards spawn near towns
            nearby_pois = self.overworld_map.get_pois_in_range(spawn_x, spawn_y, radius=5)
            if nearby_pois:
                poi = random.choice(nearby_pois)
                party.patrol_center_x = poi.position[0]
                party.patrol_center_y = poi.position[1]
                party.patrol_radius = random.randint(2, 5)
        
        self.add_party(party)
        return party
    
    def _find_spawn_position(
        self,
        avoid_position: Optional[Tuple[int, int]] = None,
        min_distance: int = 10,
        max_distance: int = 40,  # Increased max distance for farther spawns
        max_attempts: int = 100,  # Increased attempts
    ) -> Optional[Tuple[int, int]]:
        """Find a valid spawn position."""
        for attempt in range(max_attempts):
            # Try to spawn within a reasonable distance of player
            if avoid_position and max_distance > min_distance:
                # Pick random angle and distance
                import math
                angle = random.uniform(0, 2 * math.pi)
                distance = random.uniform(min_distance, max_distance)
                x = int(avoid_position[0] + distance * math.cos(angle))
                y = int(avoid_position[1] + distance * math.sin(angle))
            else:
                # Fallback: random position
                x = random.randint(0, self.overworld_map.width - 1)
                y = random.randint(0, self.overworld_map.height - 1)
            
            # Clamp to map bounds
            x = max(0, min(self.overworld_map.width - 1, x))
            y = max(0, min(self.overworld_map.height - 1, y))
            
            # Check if walkable
            if not self.overworld_map.is_walkable(x, y):
                continue
            
            # Check distance from avoid position
            if avoid_position:
                dx = x - avoid_position[0]
                dy = y - avoid_position[1]
                dist = (dx * dx + dy * dy) ** 0.5
                if dist < min_distance:
                    continue
            
            # Check if position is already occupied
            if self.get_party_at(x, y) is not None:
                continue
            
            return (x, y)
        
        return None
    
    def initial_spawn(
        self,
        count: int,
        player_level: int = 1,
        player_position: Optional[Tuple[int, int]] = None,
    ) -> None:
        """
        Spawn initial parties when overworld is first loaded.
        
        Args:
            count: Number of parties to spawn (will spawn more for active world)
            player_level: Current player level
            player_position: Player's position (to avoid spawning too close)
        """
        # Spawn more parties for a more active world
        target_count = min(count * 2, self.max_parties)  # Double the requested count
        
        spawned = 0
        for i in range(target_count):
            party = self.spawn_random_party(
                player_level=player_level,
                avoid_position=player_position,
                min_distance=10,  # Spawn farther from player
            )
            if party:
                spawned += 1
        print(f"Successfully spawned {spawned} parties out of {target_count} requested")
        if spawned > 0:
            all_parties = self.get_all_parties()
            print(f"Total parties on map: {len(all_parties)}")
            # Print first few party positions for debugging
            for i, p in enumerate(all_parties[:3]):
                print(f"  Party {i+1}: {p.party_type_id} at ({p.x}, {p.y})")
    
    def update_on_player_move(
        self,
        player_level: int = 1,
        player_position: Optional[Tuple[int, int]] = None,
    ) -> None:
        """
        Update all parties when the player moves (turn-based).
        
        This is called each time the player moves, so parties move in sync
        with the player's movement.
        
        Args:
            player_level: Current player level (for spawning)
            player_position: Player's current position
        """
        # Update party AI (one move per party per player move)
        from .party_ai import update_party_ai
        from .party_types import get_party_type
        
        all_parties = list(self.parties.values())
        for party in all_parties:
            party_type = get_party_type(party.party_type_id)
            if party_type:
                # Use a fixed "time" increment for turn-based movement
                # This allows parties to move once per player move
                update_party_ai(
                    party=party,
                    party_type=party_type,
                    overworld_map=self.overworld_map,
                    current_time=self.current_time,
                    all_parties=all_parties,
                )
                # Increment time for next update
                self.current_time += 1.0
        
        # Update active battles
        self._update_battles()
        
        # Spawn new parties more frequently (every N player moves)
        self.spawn_timer += 1
        if (self.spawn_timer >= self.spawn_interval and
            len(self.parties) < self.max_parties):
            # Spawn 2-5 parties at once (more active world)
            spawn_count = random.randint(2, 5)
            for _ in range(spawn_count):
                if len(self.parties) >= self.max_parties:
                    break
                self.spawn_random_party(
                    player_level=player_level,
                    avoid_position=player_position,
                    min_distance=15,  # Slightly closer for more interaction
                )
            self.spawn_timer = 0
    
    def update(self, dt: float, player_level: int = 1, player_position: Optional[Tuple[int, int]] = None) -> None:
        """
        Legacy update method (kept for compatibility).
        
        Parties now move when the player moves via update_on_player_move().
        This method is kept but does minimal work.
        """
        # Parties are updated in update_on_player_move() now
        pass
    
    def get_all_parties(self) -> List["RoamingParty"]:
        """Get all parties."""
        return list(self.parties.values())
    
    def _update_battles(self) -> None:
        """Update all active battles."""
        battles_to_remove = []
        
        for battle_id, battle in list(self.active_battles.items()):
            # Check if parties still exist
            party1 = self.parties.get(battle.party1_id)
            party2 = self.parties.get(battle.party2_id)
            
            if not party1 or not party2:
                # One party is gone, battle is over
                battles_to_remove.append(battle_id)
                continue
            
            # Check if parties are still at battle location
            if (party1.x, party1.y) != battle.position and (party2.x, party2.y) != battle.position:
                # Parties moved away, battle is over
                battles_to_remove.append(battle_id)
                party1.in_combat = False
                party2.in_combat = False
                continue
            
            # Increment turn count
            battle.turn_count += 1
            
            # Auto-resolve if battle lasts too long
            if battle.turn_count >= battle.max_turns:
                self._resolve_battle(battle)
                battles_to_remove.append(battle_id)
        
        # Remove finished battles
        for battle_id in battles_to_remove:
            del self.active_battles[battle_id]
    
    def _resolve_battle(self, battle: "BattleState") -> None:
        """Resolve a battle that has gone on too long."""
        party1 = self.parties.get(battle.party1_id)
        party2 = self.parties.get(battle.party2_id)
        
        if not party1 or not party2:
            return
        
        # Determine winner based on health
        if battle.party1_health > battle.party2_health:
            winner, loser = party1, party2
        elif battle.party2_health > battle.party1_health:
            winner, loser = party2, party1
        else:
            # Tie - both retreat
            from .party_ai import _make_party_flee
            _make_party_flee(party1, party2, self.overworld_map)
            _make_party_flee(party2, party1, self.overworld_map)
            party1.in_combat = False
            party2.in_combat = False
            return
        
        # Remove loser
        self.remove_party(loser.party_id)
        winner.in_combat = False
        
        # Winner gains gold
        if loser.gold > 0:
            gold_gained = min(loser.gold, random.randint(1, loser.gold))
            winner.gold += gold_gained
    
    def get_battle_at(self, x: int, y: int) -> Optional["BattleState"]:
        """Get battle at a specific position."""
        for battle in self.active_battles.values():
            if battle.position == (x, y):
                return battle
        return None
    
    def get_battles_in_range(
        self,
        center_x: int,
        center_y: int,
        radius: int,
    ) -> List["BattleState"]:
        """Get all battles within a radius."""
        result = []
        radius_sq = radius * radius
        
        for battle in self.active_battles.values():
            bx, by = battle.position
            dx = bx - center_x
            dy = by - center_y
            dist_sq = dx * dx + dy * dy
            
            if dist_sq <= radius_sq:
                result.append(battle)
        
        return result
    
    def clear(self) -> None:
        """Clear all parties and battles."""
        self.parties.clear()
        self.active_battles.clear()
        self.current_time = 0.0
        self.spawn_timer = 0.0

