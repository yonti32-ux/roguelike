"""
Faction-based combat logic.

Handles faction relations, combat initiation checks, and allied party support.
"""

from typing import List, Optional, Tuple, TYPE_CHECKING

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
    Determine if combat should be initiated with a party based on faction relations.
    
    Args:
        party: The roaming party to check
        party_type: The party type definition
        game: Game instance
        player_faction: Player's faction ID (if any)
    
    Returns:
        Tuple of (should_fight, reason)
        - should_fight: True if combat should happen
        - reason: Explanation for the decision
    """
    # Always fight if party is explicitly hostile
    if party_type.alignment.value == "hostile":
        return True, "Party is hostile"
    
    # Never fight if party is explicitly friendly
    if party_type.alignment.value == "friendly":
        return False, "Party is friendly"
    
    # For neutral parties, check faction relations
    if party_type.alignment.value == "neutral":
        if not party.faction_id or not player_faction:
            # No faction info - default to neutral (no combat)
            return False, "Neutral party, no faction conflict"
        
        # Check faction relations
        if game.overworld_map and game.overworld_map.faction_manager:
            relation = game.overworld_map.faction_manager.get_relation(
                player_faction, party.faction_id
            )
            
            # Hostile relations (< -50) -> combat
            if relation < -50:
                return True, f"Faction relations are hostile ({relation})"
            
            # Very friendly relations (> 50) -> no combat
            if relation > 50:
                return False, f"Faction relations are friendly ({relation})"
            
            # Neutral range (-50 to 50) -> no combat by default
            # Player can still manually attack if they want
            return False, f"Faction relations are neutral ({relation})"
    
    # Default: no combat
    return False, "No reason to fight"


def get_allied_parties_for_battle(
    party: "RoamingParty",
    party_type: "PartyType",
    game: "Game",
    player_faction: Optional[str] = None,
    radius: int = 2
) -> List["RoamingParty"]:
    """
    Get nearby allied parties that should join the battle on the player's side.
    
    Allied parties join when:
    - They are friendly to the player (same faction or high relations)
    - They are hostile to the enemy party
    - They are within range
    - They have can_join_battle = True
    
    Args:
        party: The enemy party being fought
        party_type: The enemy party type
        game: Game instance
        player_faction: Player's faction ID (if any)
        radius: Search radius for allied parties (default: 2 tiles)
    
    Returns:
        List of allied parties that should join
    """
    if not game.overworld_map or not game.overworld_map.party_manager:
        return []
    
    if not player_faction:
        # No player faction = no allies
        return []
    
    # Get player position
    player_x, player_y = game.overworld_map.get_player_position()
    
    # Find nearby parties
    nearby_parties = game.overworld_map.party_manager.get_parties_in_range(
        center_x=player_x,
        center_y=player_y,
        radius=radius
    )
    
    allies: List["RoamingParty"] = []
    
    for nearby_party in nearby_parties:
        # Skip the enemy party itself
        if nearby_party.party_id == party.party_id:
            continue
        
        # Skip parties already in combat
        if nearby_party.in_combat:
            continue
        
        from .party_types import get_party_type
        nearby_party_type = get_party_type(nearby_party.party_type_id)
        if not nearby_party_type:
            continue
        
        # Check if party can join battles
        if not nearby_party_type.can_join_battle:
            continue
        
        # Check if party is friendly to player
        is_friendly = _is_party_friendly_to_player(
            nearby_party, nearby_party_type, game, player_faction
        )
        
        # Check if party is hostile to enemy
        is_hostile_to_enemy = _is_party_hostile_to_enemy(
            nearby_party, nearby_party_type, party, party_type
        )
        
        # Join if friendly to player AND hostile to enemy
        if is_friendly and is_hostile_to_enemy:
            allies.append(nearby_party)
    
    return allies


def _is_party_friendly_to_player(
    party: "RoamingParty",
    party_type: "PartyType",
    game: "Game",
    player_faction: str
) -> bool:
    """Check if a party is friendly to the player."""
    # Explicitly friendly alignment
    if party_type.alignment.value == "friendly":
        return True
    
    # Check faction relations
    if party.faction_id:
        if game.overworld_map and game.overworld_map.faction_manager:
            relation = game.overworld_map.faction_manager.get_relation(
                player_faction, party.faction_id
            )
            # Friendly if relations > 30
            return relation > 30
    
    # Check if same faction
    if party.faction_id == player_faction:
        return True
    
    return False


def _is_party_hostile_to_enemy(
    ally_party: "RoamingParty",
    ally_party_type: "PartyType",
    enemy_party: "RoamingParty",
    enemy_party_type: "PartyType"
) -> bool:
    """Check if a party is hostile to the enemy party."""
    # Check enemy_types set
    if enemy_party_type.id in ally_party_type.enemy_types:
        return True
    
    # Check faction relations
    if ally_party.faction_id and enemy_party.faction_id:
        # If they have different factions, check if they're enemies
        # This would require faction manager, but for now use enemy_types
        pass
    
    # Check alignment
    if enemy_party_type.alignment.value == "hostile":
        # Most friendly/neutral parties are hostile to hostile parties
        if ally_party_type.alignment.value in ("friendly", "neutral"):
            return True
    
    return False

