"""
Party-to-Player interaction system.

Handles enhanced interactions between roaming parties and the player,
including information sharing, warnings, requests, and escort offers.
"""

from typing import Optional, List, Tuple, TYPE_CHECKING
import random

if TYPE_CHECKING:
    from .roaming_party import RoamingParty
    from .party_types import PartyType
    from ..map import OverworldMap
    from engine.core.game import Game


def get_party_information(
    party: "RoamingParty",
    party_type: "PartyType",
    overworld_map: "OverworldMap",
) -> List[str]:
    """
    Get information that a party can share with the player.
    
    Returns:
        List of information strings the party can share
    """
    info = []
    
    # Share information about visited POIs
    if party.visited_pois:
        poi_count = len(party.visited_pois)
        if poi_count > 0:
            info.append(f"I've visited {poi_count} location{'s' if poi_count > 1 else ''} recently.")
    
    # Share information about known dangers
    if party.known_dangers:
        danger_count = len(party.known_dangers)
        if danger_count > 0:
            info.append(f"I know of {danger_count} dangerous area{'s' if danger_count > 1 else ''} nearby.")
    
    # Share information about nearby enemies
    if overworld_map.party_manager:
        nearby_enemies = []
        for other in overworld_map.party_manager.get_all_parties():
            if (other.party_id != party.party_id and
                other.party_type_id in party_type.enemy_types):
                dist = party.distance_to_party(other)
                if dist <= party_type.sight_range * 2:  # Extended range for warnings
                    nearby_enemies.append((other, dist))
        
        if nearby_enemies:
            closest = min(nearby_enemies, key=lambda x: x[1])
            enemy_party, dist = closest
            from .party_types import get_party_type
            enemy_type = get_party_type(enemy_party.party_type_id)
            if enemy_type:
                info.append(f"I spotted {enemy_type.name} nearby, about {int(dist)} tiles away.")
    
    # Share information about nearby POIs
    nearby_pois = overworld_map.get_pois_in_range(party.x, party.y, radius=party_type.sight_range * 2)
    if nearby_pois:
        poi = random.choice(nearby_pois)
        poi_type = getattr(poi, "poi_type", None) or getattr(poi, "type", None)
        if poi_type:
            info.append(f"There's a {poi_type} called {poi.name} not far from here.")
    
    return info


def get_party_warning(
    party: "RoamingParty",
    party_type: "PartyType",
    player_position: Tuple[int, int],
    overworld_map: "OverworldMap",
) -> Optional[str]:
    """
    Get a warning message from a party to the player.
    
    Returns:
        Warning message string, or None if no warning
    """
    player_x, player_y = player_position
    
    # Check for nearby enemies to the player
    if overworld_map.party_manager:
        for other in overworld_map.party_manager.get_all_parties():
            if other.party_type_id in party_type.enemy_types:
                dist_to_player = ((other.x - player_x)**2 + (other.y - player_y)**2)**0.5
                dist_to_party = party.distance_to_party(other)
                
                # If enemy is close to player and party can see it
                if dist_to_player <= 10 and dist_to_party <= party_type.sight_range:
                    from .party_types import get_party_type
                    enemy_type = get_party_type(other.party_type_id)
                    if enemy_type:
                        return f"Watch out! {enemy_type.name} is nearby!"
    
    # Check for known dangers near player
    for danger_pos, description in party.known_dangers.items():
        danger_x, danger_y = danger_pos
        dist = ((danger_x - player_x)**2 + (danger_y - player_y)**2)**0.5
        if dist <= 8:
            return f"Be careful! {description}"
    
    return None


def can_party_offer_escort(
    party: "RoamingParty",
    party_type: "PartyType",
    player_position: Tuple[int, int],
) -> bool:
    """
    Check if a party can offer escort to the player.
    
    Returns:
        True if party can offer escort
    """
    # Only friendly/neutral parties can offer escort
    if party_type.alignment.value not in ["friendly", "neutral"]:
        return False
    
    # Party must not already be escorting someone
    if party.escort_target_id is not None:
        return False
    
    # Party must be close to player
    player_x, player_y = player_position
    dist = party.distance_to(player_x, player_y)
    if dist > 5:
        return False
    
    # Certain party types are more likely to offer escort
    escort_types = ["guard", "knight", "ranger", "adventurer", "mercenary"]
    return party.party_type_id in escort_types


def get_party_request(
    party: "RoamingParty",
    party_type: "PartyType",
    overworld_map: "OverworldMap",
) -> Optional[str]:
    """
    Get a request that a party might make to the player.
    
    Returns:
        Request message string, or None if no request
    """
    # Only friendly/neutral parties make requests
    if party_type.alignment.value not in ["friendly", "neutral"]:
        return None
    
    # Check if party needs help (low health, being pursued, etc.)
    if party.health_state == "wounded":
        return "We're wounded and could use some help!"
    
    # Check if party is being pursued
    if overworld_map.party_manager:
        for other in overworld_map.party_manager.get_all_parties():
            if (other.party_id != party.party_id and
                other.party_type_id in party_type.enemy_types):
                dist = party.distance_to_party(other)
                if dist <= party_type.sight_range:
                    from .party_types import get_party_type
                    enemy_type = get_party_type(other.party_type_id)
                    if enemy_type:
                        return f"We're being pursued by {enemy_type.name}! Can you help?"
    
    # Merchants might request escort
    if party.party_type_id in ["merchant", "trader", "villager", "pilgrim"]:
        if random.random() < 0.3:  # 30% chance
            return "We're traveling to a nearby settlement. Would you escort us?"
    
    return None


def update_party_player_awareness(
    party: "RoamingParty",
    party_type: "PartyType",
    player_position: Tuple[int, int],
    overworld_map: "OverworldMap",
) -> None:
    """
    Update party's awareness of the player and react accordingly.
    
    This is called when the player is near a party.
    """
    player_x, player_y = player_position
    dist = party.distance_to(player_x, player_y)
    
    # Only react if player is within sight range
    if dist > party_type.sight_range:
        return
    
    # Hostile parties might hunt the player
    if (party_type.alignment.value == "hostile" and
        party_type.behavior.value == "hunt" and
        party.following_party_id is None):
        # Start following player
        party.set_target(player_x, player_y)
        party.behavior_state = "hunting_player"
    
    # Friendly parties might offer to follow/escort
    elif (party_type.alignment.value in ["friendly", "neutral"] and
          party_type.behavior.value in ["wander", "travel"] and
          party.following_party_id is None and
          random.random() < 0.1):  # 10% chance
        # Might start following player if they're friendly
        if can_party_offer_escort(party, party_type, player_position):
            party.following_party_id = "player"  # Special ID for player
            party.behavior_state = "following_player"
    
    # Update known dangers based on player's position (if player is fighting)
    # This would require game state, so we'll skip for now
