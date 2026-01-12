"""
AI system for roaming parties.

Handles movement, pathfinding, and behavior logic for parties on the overworld.
"""

from typing import Optional, Tuple, List, TYPE_CHECKING
import random
import math

from .party_types import PartyBehavior

if TYPE_CHECKING:
    from .map import OverworldMap
    from .party_types import PartyType
    from .roaming_party import RoamingParty
    from ..poi.base import PointOfInterest


def _handle_party_interaction(
    party: "RoamingParty",
    party_type: "PartyType",
    other_party: "RoamingParty",
    overworld_map: "OverworldMap",
    all_parties: List["RoamingParty"],
) -> None:
    """
    Handle interactions between parties (combat, fleeing, etc.).
    
    When parties meet, they may:
    - Fight (if both can attack and are enemies)
    - One party flees (if weaker)
    - Ignore each other (if neutral)
    """
    from .party_types import get_party_type
    
    other_party_type = get_party_type(other_party.party_type_id)
    if other_party_type is None:
        return
    
    # Check if parties are at the same position (adjacent or same tile)
    dist = party.distance_to_party(other_party)
    if dist > 1:  # Only interact if adjacent or same tile
        return
    
    # Skip if already in combat
    if party.in_combat or other_party.in_combat:
        return
    
    # Both parties must be able to attack for combat
    if not (party_type.can_attack and other_party_type.can_attack):
        return
    
    # Check if they're enemies
    is_enemy = (other_party.party_type_id in party_type.enemy_types or
                party.party_type_id in other_party_type.enemy_types)
    
    if not is_enemy:
        return  # Not enemies, no interaction
    
    # Determine combat outcome based on strength
    party_strength = party_type.combat_strength
    other_strength = other_party_type.combat_strength
    
    # Add some randomness
    party_roll = party_strength + random.randint(-1, 1)
    other_roll = other_strength + random.randint(-1, 1)
    
    # Determine winner
    if party_roll > other_roll:
        # This party wins
        _resolve_party_combat(party, other_party, overworld_map, all_parties)
    elif other_roll > party_roll:
        # Other party wins
        _resolve_party_combat(other_party, party, overworld_map, all_parties)
    else:
        # Tie - both parties retreat
        _make_party_flee(party, other_party, overworld_map)
        _make_party_flee(other_party, party, overworld_map)


def _resolve_party_combat(
    winner: "RoamingParty",
    loser: "RoamingParty",
    overworld_map: "OverworldMap",
    all_parties: List["RoamingParty"],
) -> None:
    """
    Resolve combat between two parties.
    
    Winner survives, loser is removed from the map.
    Winner may gain gold/items from loser.
    """
    from .party_types import get_party_type
    
    winner_type = get_party_type(winner.party_type_id)
    loser_type = get_party_type(loser.party_type_id)
    
    if winner_type is None or loser_type is None:
        return
    
    # Winner gains gold from loser (if loser has any)
    if loser.gold > 0:
        gold_gained = min(loser.gold, random.randint(1, loser.gold))
        winner.gold += gold_gained
        loser.gold -= gold_gained
    
    # Remove loser from map
    if hasattr(overworld_map, "party_manager") and overworld_map.party_manager:
        overworld_map.party_manager.remove_party(loser.party_id)
    
    # Log combat result (if game has message system, could add it here)
    # For now, combat happens silently but could be logged to message log


def _make_party_flee(
    fleeing_party: "RoamingParty",
    from_party: "RoamingParty",
    overworld_map: "OverworldMap",
) -> None:
    """Make a party flee from another party."""
    # Set target away from enemy
    dx = fleeing_party.x - from_party.x
    dy = fleeing_party.y - from_party.y
    
    # If same position, pick random direction
    if dx == 0 and dy == 0:
        dx = random.choice([-1, 1])
        dy = random.choice([-1, 1])
    
    # Normalize and move away
    dist = math.sqrt(dx * dx + dy * dy)
    if dist > 0:
        dx = int(dx / dist * 5)  # Move 5 tiles away
        dy = int(dy / dist * 5)
    
    target_x = fleeing_party.x + dx
    target_y = fleeing_party.y + dy
    
    # Clamp to map bounds
    target_x = max(0, min(overworld_map.width - 1, target_x))
    target_y = max(0, min(overworld_map.height - 1, target_y))
    
    # Find nearest walkable tile
    if not overworld_map.is_walkable(target_x, target_y):
        for radius in range(1, 6):
            for test_dx in range(-radius, radius + 1):
                for test_dy in range(-radius, radius + 1):
                    if test_dx * test_dx + test_dy * test_dy > radius * radius:
                        continue
                    test_x = target_x + test_dx
                    test_y = target_y + test_dy
                    if (overworld_map.in_bounds(test_x, test_y) and
                        overworld_map.is_walkable(test_x, test_y)):
                        target_x = test_x
                        target_y = test_y
                        break
                else:
                    continue
                break
    
    fleeing_party.set_target(target_x, target_y)
    fleeing_party.behavior_state = "fleeing"


def find_path(
    start_x: int,
    start_y: int,
    target_x: int,
    target_y: int,
    overworld_map: "OverworldMap",
    max_steps: int = 100,
) -> List[Tuple[int, int]]:
    """
    Simple pathfinding using A* or greedy approach.
    
    For now, uses a simple greedy approach. Can be upgraded to A* later.
    """
    if start_x == target_x and start_y == target_y:
        return []
    
    path = []
    current_x, current_y = start_x, start_y
    visited = {(current_x, current_y)}
    
    # Try to move towards target
    for _ in range(max_steps):
        if current_x == target_x and current_y == target_y:
            break
        
        # Calculate direction to target
        dx = target_x - current_x
        dy = target_y - current_y
        
        # Try moving in the best direction
        best_move = None
        best_dist = float('inf')
        
        # Try all 8 directions (including diagonals)
        for move_dx in [-1, 0, 1]:
            for move_dy in [-1, 0, 1]:
                if move_dx == 0 and move_dy == 0:
                    continue
                
                new_x = current_x + move_dx
                new_y = current_y + move_dy
                
                # Check if valid and walkable
                if not overworld_map.in_bounds(new_x, new_y):
                    continue
                if not overworld_map.is_walkable(new_x, new_y):
                    continue
                if (new_x, new_y) in visited:
                    continue
                
                # Calculate distance to target
                dist = math.sqrt((target_x - new_x)**2 + (target_y - new_y)**2)
                if dist < best_dist:
                    best_dist = dist
                    best_move = (new_x, new_y)
        
        if best_move is None:
            # Can't find a path
            break
        
        current_x, current_y = best_move
        path.append((current_x, current_y))
        visited.add((current_x, current_y))
    
    return path


def get_next_patrol_target(
    party: "RoamingParty",
    party_type: "PartyType",
    overworld_map: "OverworldMap",
) -> Optional[Tuple[int, int]]:
    """Get next patrol target for a party."""
    if party.patrol_center_x is None or party.patrol_center_y is None:
        party.patrol_center_x = party.x
        party.patrol_center_y = party.y
    
    # Pick a random point within patrol radius
    angle = random.uniform(0, 2 * math.pi)
    distance = random.uniform(0, party.patrol_radius)
    
    target_x = int(party.patrol_center_x + distance * math.cos(angle))
    target_y = int(party.patrol_center_y + distance * math.sin(angle))
    
    # Clamp to map bounds and ensure walkable
    target_x = max(0, min(overworld_map.width - 1, target_x))
    target_y = max(0, min(overworld_map.height - 1, target_y))
    
    # Find nearest walkable tile if target isn't walkable
    if not overworld_map.is_walkable(target_x, target_y):
        # Try nearby tiles
        for radius in range(1, party.patrol_radius + 1):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    if dx * dx + dy * dy > radius * radius:
                        continue
                    test_x = target_x + dx
                    test_y = target_y + dy
                    if (overworld_map.in_bounds(test_x, test_y) and
                        overworld_map.is_walkable(test_x, test_y)):
                        return (test_x, test_y)
        return None
    
    return (target_x, target_y)


def get_next_wander_target(
    party: "RoamingParty",
    party_type: "PartyType",
    overworld_map: "OverworldMap",
) -> Optional[Tuple[int, int]]:
    """Get next wander target for a party."""
    # Pick a random direction and distance
    angle = random.uniform(0, 2 * math.pi)
    distance = random.uniform(3, 10)
    
    target_x = int(party.x + distance * math.cos(angle))
    target_y = int(party.y + distance * math.sin(angle))
    
    # Clamp to map bounds
    target_x = max(0, min(overworld_map.width - 1, target_x))
    target_y = max(0, min(overworld_map.height - 1, target_y))
    
    # Find nearest walkable tile
    if not overworld_map.is_walkable(target_x, target_y):
        for radius in range(1, 6):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    if dx * dx + dy * dy > radius * radius:
                        continue
                    test_x = target_x + dx
                    test_y = target_y + dy
                    if (overworld_map.in_bounds(test_x, test_y) and
                        overworld_map.is_walkable(test_x, test_y)):
                        return (test_x, test_y)
        return None
    
    return (target_x, target_y)


def get_travel_target(
    party: "RoamingParty",
    party_type: "PartyType",
    overworld_map: "OverworldMap",
) -> Optional[Tuple[int, int]]:
    """
    Get travel target for a party (between POIs).
    
    If party has a destination, move towards it.
    Otherwise, pick a new destination POI.
    """
    from ..poi.base import PointOfInterest
    
    # If we have a destination and haven't reached it, continue
    if party.destination_poi_id:
        poi = overworld_map.pois.get(party.destination_poi_id)
        if poi:
            # Check if we're close enough (within 2 tiles)
            dist = party.distance_to(poi.position[0], poi.position[1])
            if dist <= 2:
                # Reached destination, pick a new one
                party.destination_poi_id = None
                party.origin_poi_id = poi.poi_id
            else:
                # Continue to destination
                return poi.position
    
    # Need to pick a new destination
    all_pois = overworld_map.get_all_pois()
    
    # Filter POIs based on preferences
    candidate_pois = []
    for poi in all_pois:
        # Skip current origin
        if poi.poi_id == party.origin_poi_id:
            continue
        
        # Check preferences
        poi_type = getattr(poi, "poi_type", None) or getattr(poi, "type", None)
        if poi_type in party_type.avoids_poi_types:
            continue
        
        # Prefer certain types if specified
        if party_type.preferred_poi_types:
            if poi_type not in party_type.preferred_poi_types:
                # Still allow, but lower priority
                pass
        
        candidate_pois.append(poi)
    
    if not candidate_pois:
        # No valid POIs, just wander
        return get_next_wander_target(party, party_type, overworld_map)
    
    # Pick a random candidate
    target_poi = random.choice(candidate_pois)
    party.destination_poi_id = target_poi.poi_id
    
    return target_poi.position


def update_party_ai(
    party: "RoamingParty",
    party_type: "PartyType",
    overworld_map: "OverworldMap",
    current_time: float,
    all_parties: List["RoamingParty"],
) -> None:
    """
    Update party AI - movement and behavior.
    
    For turn-based movement, parties move once per player move.
    Speed affects how often they move (faster parties move more often).
    
    Args:
        party: The party to update
        party_type: The party's type definition
        overworld_map: The overworld map
        current_time: Current game time (incremented each player move)
        all_parties: List of all other parties (for interactions)
    """
    # For turn-based movement, speed determines move frequency
    # Faster parties (speed > 1.0) move more often
    # Slower parties (speed < 1.0) move less often
    move_chance = min(1.0, party_type.speed)
    import random
    if random.random() > move_chance:
        return  # Skip this move for slower parties
    
    # Handle combat state
    if party.in_combat:
        # Combat logic handled elsewhere
        return
    
    # Check for nearby enemies and allies
    nearby_enemy = None
    nearby_ally = None
    for other_party in all_parties:
        if other_party.party_id == party.party_id:
            continue
        
        dist = party.distance_to_party(other_party)
        if dist > party_type.sight_range:
            continue
        
        # Check if this is an enemy
        if other_party.party_type_id in party_type.enemy_types:
            nearby_enemy = other_party
            # Check for party-to-party combat (only if adjacent)
            if dist <= 1:
                _handle_party_interaction(party, party_type, other_party, overworld_map, all_parties)
            break
        # Check if this is an ally
        elif other_party.party_type_id in party_type.ally_types:
            nearby_ally = other_party
    
    # React to enemies based on behavior
    if nearby_enemy:
        if party_type.behavior == PartyBehavior.HUNT:
            # Move towards enemy
            party.set_target(nearby_enemy.x, nearby_enemy.y)
        elif party_type.behavior == PartyBehavior.FLEE:
            # Move away from enemy
            dx = party.x - nearby_enemy.x
            dy = party.y - nearby_enemy.y
            if dx == 0 and dy == 0:
                # Same position, pick random direction
                dx = random.choice([-1, 1])
                dy = random.choice([-1, 1])
            
            # Normalize and move away
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > 0:
                dx = int(dx / dist * party_type.sight_range * 2)
                dy = int(dy / dist * party_type.sight_range * 2)
            
            target_x = party.x + dx
            target_y = party.y + dy
            target_x = max(0, min(overworld_map.width - 1, target_x))
            target_y = max(0, min(overworld_map.height - 1, target_y))
            party.set_target(target_x, target_y)
            return  # Don't continue with normal movement if fleeing
    
    # If no target or reached target, pick new target based on behavior
    if party.is_at_target() or party.target_x is None:
        target = None
        
        if party_type.behavior == PartyBehavior.PATROL:
            target = get_next_patrol_target(party, party_type, overworld_map)
        elif party_type.behavior == PartyBehavior.TRAVEL:
            target = get_travel_target(party, party_type, overworld_map)
        elif party_type.behavior == PartyBehavior.WANDER:
            target = get_next_wander_target(party, party_type, overworld_map)
        elif party_type.behavior == PartyBehavior.GUARD:
            # Stay near guard position
            if party.patrol_center_x is not None and party.patrol_center_y is not None:
                dist = party.distance_to(party.patrol_center_x, party.patrol_center_y)
                if dist > party.patrol_radius:
                    # Return to guard position
                    target = (party.patrol_center_x, party.patrol_center_y)
                else:
                    # Small patrol around guard position
                    target = get_next_patrol_target(party, party_type, overworld_map)
        elif party_type.behavior == PartyBehavior.HUNT:
            # If no enemy, wander
            if nearby_enemy is None:
                target = get_next_wander_target(party, party_type, overworld_map)
        
        if target:
            party.set_target(target[0], target[1])
    
    # Move towards target
    if not party.is_at_target() and party.target_x is not None and party.target_y is not None:
        # Simple movement: move one step towards target
        dx = party.target_x - party.x
        dy = party.target_y - party.y
        
        # Normalize to one step
        if abs(dx) > 1 or abs(dy) > 1:
            if abs(dx) > abs(dy):
                dx = 1 if dx > 0 else -1
                dy = 0
            else:
                dx = 0
                dy = 1 if dy > 0 else -1
        
        new_x = party.x + dx
        new_y = party.y + dy
        
        # Check if valid move
        if (overworld_map.in_bounds(new_x, new_y) and
            overworld_map.is_walkable(new_x, new_y)):
            party.set_position(new_x, new_y)
            party.record_move(current_time)
            
            # If reached target, clear it
            if party.is_at_target():
                party.clear_target()

