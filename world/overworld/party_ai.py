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
    Handle interactions between parties (combat, fleeing, alliances, etc.).
    
    When parties meet, they may:
    - Fight (if both can attack and are enemies)
    - Form temporary alliances (if allies and facing common enemy)
    - Share information (if friendly)
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
    
    # Check relationship status
    relationship = party.party_relationships.get(other_party.party_id, "neutral")
    
    # Check if they're enemies
    is_enemy = (other_party.party_type_id in party_type.enemy_types or
                party.party_type_id in other_party_type.enemy_types or
                relationship == "enemy")
    
    # Check if they're allies
    is_ally = (other_party.party_type_id in party_type.ally_types or
               relationship == "ally" or
               relationship == "friendly" or
               other_party.party_id in party.temporary_allies)
    
    # If allies, check for information sharing or group formation
    if is_ally and not is_enemy:
        _handle_ally_interaction(party, party_type, other_party, other_party_type, overworld_map, all_parties)
        return
    
    # Both parties must be able to attack for combat
    if not (party_type.can_attack and other_party_type.can_attack):
        return
    
    if not is_enemy:
        return  # Not enemies, no combat interaction
    
    # Start a multi-turn battle instead of instant resolution
    _start_party_battle(party, other_party, overworld_map)


def _handle_ally_interaction(
    party: "RoamingParty",
    party_type: "PartyType",
    other_party: "RoamingParty",
    other_party_type: "PartyType",
    overworld_map: "OverworldMap",
    all_parties: List["RoamingParty"],
) -> None:
    """
    Handle interactions between allied parties.
    
    Allies may:
    - Share information about dangers/POIs
    - Form temporary groups
    - Coordinate movement
    """
    # Share information about known dangers
    if party.known_dangers and random.random() < 0.3:  # 30% chance to share info
        for location, description in list(party.known_dangers.items())[:2]:  # Share up to 2 dangers
            if location not in other_party.known_dangers:
                other_party.known_dangers[location] = description
    
    # Share information about visited POIs
    if party.visited_pois and random.random() < 0.2:  # 20% chance
        for poi_id in list(party.visited_pois)[:1]:  # Share 1 POI
            if poi_id not in other_party.visited_pois:
                other_party.visited_pois.add(poi_id)
    
    # Check if they should form a temporary group (if facing common enemy nearby)
    nearby_enemy = None
    for other in all_parties:
        if (other.party_id != party.party_id and 
            other.party_id != other_party.party_id and
            other.party_type_id in party_type.enemy_types):
            dist = min(party.distance_to_party(other), other_party.distance_to_party(other))
            if dist <= party_type.sight_range:
                nearby_enemy = other
                break
    
    # Form temporary alliance if facing common enemy
    if nearby_enemy and random.random() < 0.4:  # 40% chance to form temporary alliance
        if other_party.party_id not in party.temporary_allies:
            party.temporary_allies.add(other_party.party_id)
        if party.party_id not in other_party.temporary_allies:
            other_party.temporary_allies.add(party.party_id)
        
        # Coordinate movement towards enemy or away
        if party_type.behavior.value == "hunt" or party_type.behavior.value == "guard":
            # Move together towards enemy
            party.set_target(nearby_enemy.x, nearby_enemy.y)
            other_party.set_target(nearby_enemy.x, nearby_enemy.y)
        elif party_type.behavior.value == "flee":
            # Move together away from enemy
            _make_party_flee(party, nearby_enemy, overworld_map)
            _make_party_flee(other_party, nearby_enemy, overworld_map)


def _start_party_battle(
    party1: "RoamingParty",
    party2: "RoamingParty",
    overworld_map: "OverworldMap",
) -> None:
    """
    Start a multi-turn battle between two parties.
    
    The battle will last multiple turns, giving the player time to join.
    """
    if not hasattr(overworld_map, "party_manager") or not overworld_map.party_manager:
        return
    
    # Check if battle already exists
    battle_at_pos = overworld_map.party_manager.get_battle_at(party1.x, party1.y)
    if battle_at_pos:
        # Battle already ongoing at this location
        return
    
    # Mark parties as in combat
    party1.in_combat = True
    party2.in_combat = True
    party1.combat_target_id = party2.party_id
    party2.combat_target_id = party1.party_id
    
    # Create battle state
    from .party_manager import BattleState
    import uuid
    
    battle_id = f"battle_{uuid.uuid4().hex[:8]}"
    battle = BattleState(
        battle_id=battle_id,
        party1_id=party1.party_id,
        party2_id=party2.party_id,
        position=(party1.x, party1.y),
        max_turns=15,  # Battle lasts 15 turns (gives player time to join)
        party1_health=100,
        party2_health=100,
        can_player_join=True,
    )
    
    overworld_map.party_manager.active_battles[battle_id] = battle
    
    # Parties stop moving during battle
    party1.clear_target()
    party2.clear_target()
    party1.behavior_state = "in_combat"
    party2.behavior_state = "in_combat"


def _update_party_battle(
    party: "RoamingParty",
    party_type: "PartyType",
    overworld_map: "OverworldMap",
) -> None:
    """
    Update a party's participation in an ongoing battle.
    
    Called each turn to progress the battle.
    """
    if not party.in_combat or not party.combat_target_id:
        return
    
    if not hasattr(overworld_map, "party_manager") or not overworld_map.party_manager:
        return
    
    # Find the battle
    battle = overworld_map.party_manager.get_battle_at(party.x, party.y)
    if not battle:
        # Battle ended or parties moved
        party.in_combat = False
        party.combat_target_id = None
        return
    
    # Determine which side this party is on
    is_party1 = battle.party1_id == party.party_id
    target_party_id = battle.party2_id if is_party1 else battle.party1_id
    
    # Get target party
    target_party = overworld_map.party_manager.get_party(target_party_id)
    if not target_party:
        # Target party is gone
        party.in_combat = False
        return
    
    from .party_types import get_party_type
    from .party_power import get_party_power

    target_party_type = get_party_type(target_party.party_type_id)
    if not target_party_type:
        return

    party_power = get_party_power(party, party_type)
    target_power = get_party_power(target_party, target_party_type)
    # Simulate damage from power (scale similar to battle conversion)
    party_damage = int(party_power * 0.4) + random.randint(0, 12)
    target_damage = int(target_power * 0.4) + random.randint(0, 12)
    
    # Apply damage
    if is_party1:
        battle.party2_health = max(0, battle.party2_health - party_damage)
        battle.party1_health = max(0, battle.party1_health - target_damage)
    else:
        battle.party1_health = max(0, battle.party1_health - party_damage)
        battle.party2_health = max(0, battle.party2_health - target_damage)
    
    # Check if battle should end
    if battle.party1_health <= 0 or battle.party2_health <= 0:
        # Battle is over
        if battle.party1_health <= 0:
            winner = target_party
            loser = party
        else:
            winner = party
            loser = target_party
        
        # Remove loser
        overworld_map.party_manager.remove_party(loser.party_id)
        
        # Winner gains gold
        if loser.gold > 0:
            gold_gained = min(loser.gold, random.randint(1, loser.gold))
            winner.gold += gold_gained
        
        # Clean up
        winner.in_combat = False
        winner.combat_target_id = None
        winner.behavior_state = "idle"
        
        # Remove battle
        if battle.battle_id in overworld_map.party_manager.active_battles:
            del overworld_map.party_manager.active_battles[battle.battle_id]


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
    
    # Winner learns about loser's known dangers
    if loser.known_dangers:
        winner.known_dangers.update(loser.known_dangers)
    
    # Remove loser from map
    if hasattr(overworld_map, "party_manager") and overworld_map.party_manager:
        overworld_map.party_manager.remove_party(loser.party_id)
    
    # Update relationships - parties that were allied with loser may become enemies
    for other in all_parties:
        if other.party_id in loser.temporary_allies:
            other.temporary_allies.discard(loser.party_id)
        if loser.party_id in other.temporary_allies:
            other.temporary_allies.discard(loser.party_id)
    
    # Log combat result (if game has message system, could add it here)
    # For now, combat happens silently but could be logged to message log


def _coordinate_with_allies(
    party: "RoamingParty",
    party_type: "PartyType",
    nearby_allies: List[Tuple["RoamingParty", float]],
    enemy: "RoamingParty",
    overworld_map: "OverworldMap",
) -> None:
    """
    Coordinate movement with nearby allies when facing a common enemy.
    
    Parties may:
    - Form defensive formations
    - Flank enemies
    - Support each other
    """
    if not nearby_allies:
        return
    
    # Sort allies by distance
    nearby_allies.sort(key=lambda x: x[1])
    
    # If we have multiple allies, form a formation
    if len(nearby_allies) >= 2:
        # Simple formation: position around enemy
        # Party takes one position, allies take others
        enemy_x, enemy_y = enemy.x, enemy.y
        
        # Calculate formation positions (circle around enemy)
        formation_radius = 3
        angle_step = 2 * math.pi / (len(nearby_allies) + 1)
        
        # Party's position in formation
        party_angle = 0
        party_form_x = int(enemy_x + formation_radius * math.cos(party_angle))
        party_form_y = int(enemy_y + formation_radius * math.sin(party_angle))
        
        # Clamp and validate
        party_form_x = max(0, min(overworld_map.width - 1, party_form_x))
        party_form_y = max(0, min(overworld_map.height - 1, party_form_y))
        
        if overworld_map.is_walkable(party_form_x, party_form_y):
            party.set_target(party_form_x, party_form_y)
            party.behavior_state = "forming_formation"
    else:
        # Single ally - support them by moving to their side
        ally, ally_dist = nearby_allies[0]
        if ally_dist > 2:
            # Move closer to ally
            party.set_target(ally.x, ally.y)
            party.behavior_state = "supporting_ally"


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


def _handle_poi_interaction(
    party: "RoamingParty",
    party_type: "PartyType",
    poi: "PointOfInterest",
    overworld_map: "OverworldMap",
    current_time: float,
) -> None:
    """
    Handle party interaction with a POI.
    
    Parties may:
    - Rest at friendly POIs
    - Resupply at towns/villages
    - Spawn from POIs (if appropriate)
    - Guard POIs
    - Learn about POI state
    """
    poi_type = getattr(poi, "poi_type", None) or getattr(poi, "type", None)
    
    # Mark POI as visited
    if poi.poi_id not in party.visited_pois:
        party.visited_pois.add(poi.poi_id)
    party.last_poi_visit_time[poi.poi_id] = current_time
    
    # Check if party can rest at this POI
    if poi_type in ["village", "town", "camp"]:
        # Check faction alignment
        can_rest = True
        if poi.faction_id and party.faction_id:
            # Check if factions are aligned (simplified - same faction or neutral)
            if poi.faction_id != party.faction_id:
                # Check faction relations if available
                if hasattr(overworld_map, "faction_manager") and overworld_map.faction_manager:
                    relation = overworld_map.faction_manager.get_relation(party.faction_id, poi.faction_id)
                    if relation < 0:  # Hostile relations
                        can_rest = False
        
        if can_rest and party.rest_cooldown <= current_time:
            # Rest at POI (reduces cooldown, heals party state)
            party.rest_cooldown = current_time + 20.0  # Can rest again after 20 moves
            party.health_state = "healthy"  # Restore health
            party.behavior_state = "resting"
    
    # Resupply at towns/villages (for merchants, traders)
    if poi_type in ["town", "village"] and party.party_type_id in ["merchant", "trader", "villager"]:
        if party.resupply_cooldown <= current_time:
            party.resupply_cooldown = current_time + 30.0  # Can resupply after 30 moves
            # Merchants gain some gold when visiting towns
            if party.party_type_id in ["merchant", "trader"]:
                party.gold += random.randint(50, 200)
    
    # Guards patrol around POIs
    if party_type.behavior.value == "guard" and poi_type in party_type.preferred_poi_types:
        # Set guard position to POI
        if party.patrol_center_x is None or party.patrol_center_y is None:
            party.patrol_center_x = poi.position[0]
            party.patrol_center_y = poi.position[1]
            party.patrol_radius = random.randint(3, 6)


def get_travel_target(
    party: "RoamingParty",
    party_type: "PartyType",
    overworld_map: "OverworldMap",
    current_time: float = 0.0,
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
                # Reached destination - interact with POI
                _handle_poi_interaction(party, party_type, poi, overworld_map, current_time)
                
                # Pick a new destination after visiting
                party.destination_poi_id = None
                party.origin_poi_id = poi.poi_id
                
                # Stay at POI for a few turns (rest/resupply)
                if party.behavior_state == "resting":
                    return None  # Don't move while resting
            else:
                # Continue to destination
                return poi.position
    
    # Need to pick a new destination
    all_pois = overworld_map.get_all_pois()
    
    # Filter POIs based on preferences
    candidate_pois = []
    preferred_pois = []
    
    for poi in all_pois:
        # Skip current origin (unless enough time has passed)
        if poi.poi_id == party.origin_poi_id:
            last_visit = party.last_poi_visit_time.get(poi.poi_id, 0.0)
            if current_time - last_visit < 50.0:  # Don't return to same POI too soon
                continue
        
        # Check preferences
        poi_type = getattr(poi, "poi_type", None) or getattr(poi, "type", None)
        if poi_type in party_type.avoids_poi_types:
            continue
        
        # Prefer certain types if specified
        if party_type.preferred_poi_types:
            if poi_type in party_type.preferred_poi_types:
                preferred_pois.append(poi)
                continue
        
        candidate_pois.append(poi)
    
    # Prefer preferred POIs, but allow others
    if preferred_pois:
        target_poi = random.choice(preferred_pois)
    elif candidate_pois:
        target_poi = random.choice(candidate_pois)
    else:
        # No valid POIs, just wander
        return get_next_wander_target(party, party_type, overworld_map)
    
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
        # Update ongoing battle
        _update_party_battle(party, party_type, overworld_map)
        return
    
    # Update cooldowns
    if party.rest_cooldown > 0:
        party.rest_cooldown = max(0, party.rest_cooldown - 1.0)
    if party.resupply_cooldown > 0:
        party.resupply_cooldown = max(0, party.resupply_cooldown - 1.0)
    
    # Check if party is at a POI and should interact
    nearby_pois = overworld_map.get_pois_in_range(party.x, party.y, radius=2)
    for poi in nearby_pois:
        dist = party.distance_to(poi.position[0], poi.position[1])
        if dist <= 2:
            # Check if we should interact with this POI
            if poi.poi_id not in party.visited_pois or current_time - party.last_poi_visit_time.get(poi.poi_id, 0.0) > 30.0:
                _handle_poi_interaction(party, party_type, poi, overworld_map, current_time)
    
    # Check for player (if available)
    player_position = overworld_map.get_player_position()
    if player_position:
        from .party_player_interactions import update_party_player_awareness
        update_party_player_awareness(party, party_type, player_position, overworld_map)
        
        # Handle following player
        if party.following_party_id == "player":
            player_x, player_y = player_position
            dist_to_player = party.distance_to(player_x, player_y)
            if dist_to_player > 3:  # Follow if more than 3 tiles away
                party.set_target(player_x, player_y)
            elif dist_to_player <= 1:
                # Close enough, might stop following after a while
                if random.random() < 0.1:  # 10% chance to stop following each turn
                    party.following_party_id = None
                    party.behavior_state = "idle"
                    party.clear_target()
    
    # Check for nearby enemies and allies
    nearby_enemy = None
    nearby_allies = []
    for other_party in all_parties:
        if other_party.party_id == party.party_id:
            continue
        
        dist = party.distance_to_party(other_party)
        if dist > party_type.sight_range:
            continue
        
        # Check if this is an enemy
        if other_party.party_type_id in party_type.enemy_types:
            if nearby_enemy is None or dist < party.distance_to_party(nearby_enemy):
                nearby_enemy = other_party
            # Check for party-to-party combat (only if adjacent)
            if dist <= 1:
                _handle_party_interaction(party, party_type, other_party, overworld_map, all_parties)
        # Check if this is an ally
        elif (other_party.party_type_id in party_type.ally_types or
              other_party.party_id in party.temporary_allies):
            nearby_allies.append((other_party, dist))
    
    # Coordinate with nearby allies
    if nearby_allies and nearby_enemy:
        # Form defensive formation with allies
        _coordinate_with_allies(party, party_type, nearby_allies, nearby_enemy, overworld_map)
    
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
            target = get_travel_target(party, party_type, overworld_map, current_time)
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
        else:
            # Move blocked - increment failed move count
            party.failed_move_count = getattr(party, 'failed_move_count', 0) + 1
            
            # If stuck for too many moves (e.g., 5), clear target to pick a new one
            if party.failed_move_count >= 5:
                party.clear_target()
                party.failed_move_count = 0

