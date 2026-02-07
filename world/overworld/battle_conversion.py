"""
Convert roaming parties into battle units.

This module handles the conversion of overworld parties into enemies
that can fight in the battle system, and also converts allied parties
into player-side units.
"""

from typing import List, Optional, TYPE_CHECKING
import random

from world.entities import Enemy, Player
from systems.enemies import (
    get_archetype, 
    EnemyArchetype, 
    compute_scaled_stats,
    choose_archetype_for_player_level,
)

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
        try:
            archetype = get_archetype(party_type.battle_unit_template)
            if archetype:
                # Use the specified archetype
                for i in range(num_enemies):
                    enemy = _create_enemy_from_archetype(
                        archetype, player_level, party, i, num_enemies
                    )
                    enemies.append(enemy)
                return enemies
        except (KeyError, Exception) as e:
            print(f"Warning: Failed to get archetype '{party_type.battle_unit_template}': {e}")
            # Fall through to default
    
    # Fallback: Create generic enemies based on combat_strength
    # Try to use new difficulty system first (player_level-based selection)
    try:
        # Use new system: select archetype based on player level
        # This allows higher-level enemies to appear in overworld as player progresses
        default_archetype = choose_archetype_for_player_level(
            player_level=player_level,
            preferred_tags=None,  # Could add tag preferences based on party_type
        )
        
        for i in range(num_enemies):
            enemy = _create_enemy_from_archetype(
                default_archetype, player_level, party, i, num_enemies
            )
            enemies.append(enemy)
    except Exception as e:
        # Fallback to old strength-based system if new system fails
        print(f"Warning: choose_archetype_for_player_level failed: {e}, using fallback")
        try:
            default_archetype = _get_default_archetype_for_strength(
                party_type.combat_strength
            )
            
            for i in range(num_enemies):
                enemy = _create_enemy_from_archetype(
                    default_archetype, player_level, party, i, num_enemies
                )
                enemies.append(enemy)
        except Exception as e2:
            print(f"Error creating enemies: {e2}")
            import traceback
            traceback.print_exc()
            # Return empty list if we can't create enemies
            return []
    
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
    # Calculate stats based on archetype and level
    # Use player_level as the "floor" for scaling
    floor = max(1, player_level)
    max_hp, attack, defense, xp, initiative = compute_scaled_stats(archetype, floor)
    
    # Adjust XP per enemy based on total count (more enemies = less XP each)
    # This keeps total XP reward balanced regardless of enemy count
    if total_enemies > 1:
        xp = int(xp / (1.0 + (total_enemies - 1) * 0.3))  # Diminishing returns
        xp = max(1, xp)  # Minimum 1 XP
    
    # Create enemy name - use party name if available, otherwise use party type
    if party.party_name:
        # Use party name for more variety (e.g., "Bandit Gang Member 1")
        base_name = party.party_name.split()[0] if party.party_name else party.party_type_id.title()
        enemy_name = f"{base_name} {index + 1}"
    else:
        enemy_name = f"{party.party_type_id.title()} {index + 1}"  # e.g., "Bandit 1"
    
    # Create Enemy entity
    enemy = Enemy(
        x=0.0,  # Position doesn't matter for battle (set by battle scene)
        y=0.0,
        width=32,  # Standard enemy size
        height=32,
        speed=0.0,  # Enemies don't move in exploration
        color=(200, 80, 80),  # Default enemy color
        max_hp=max_hp,
        hp=max_hp,
        attack_power=attack,
    )
    
    # Set additional enemy properties
    enemy.archetype_id = archetype.id
    enemy.enemy_type = archetype.name
    enemy.xp_reward = xp
    enemy.defense = defense
    enemy.initiative = initiative
    enemy.skill_ids = archetype.skill_ids.copy()
    
    # Store party reference for post-combat updates
    enemy.party_id = party.party_id
    # Store party name for better tracking
    if hasattr(enemy, 'party_name'):
        enemy.party_name = party.party_name
    # Store party type for reference
    if hasattr(enemy, 'party_type_id'):
        enemy.party_type_id = party.party_type_id
    
    return enemy


def _get_default_archetype_for_strength(strength: int) -> EnemyArchetype:
    """
    Get a default enemy archetype based on combat strength.
    
    This is a fallback when battle_unit_template is not set.
    
    Args:
        strength: Combat strength (1-5)
    
    Returns:
        EnemyArchetype to use
    """
    # Map combat_strength (1-5) to appropriate archetypes
    strength_to_archetype = {
        1: "goblin_skirmisher",  # Weak enemies
        2: "bandit_cutthroat",  # Moderate enemies
        3: "orc_raider",        # Strong enemies
        4: "dread_knight",      # Very strong enemies
        5: "dragonkin",         # Boss-level enemies
    }
    
    archetype_id = strength_to_archetype.get(strength, "bandit_cutthroat")
    
    try:
        archetype = get_archetype(archetype_id)
    except (KeyError, Exception) as e:
        print(f"Warning: get_archetype('{archetype_id}') failed: {e}")
        archetype = None
    
        if archetype is None:
            # Ultimate fallback: use goblin_skirmisher if available
            try:
                archetype = get_archetype("goblin_skirmisher")
            except (KeyError, Exception):
                archetype = None
        
        if archetype is None:
            # Last resort: try to get any archetype
            from systems.enemies import ENEMY_ARCHETYPES
            if ENEMY_ARCHETYPES:
                # Use the first available archetype
                archetype = list(ENEMY_ARCHETYPES.values())[0]
                print(f"Warning: Using fallback archetype '{archetype.id}' for strength {strength}")
            else:
                # This should never happen if enemy archetypes are properly registered
                raise RuntimeError(
                    f"No enemy archetype found for strength {strength} "
                    "and no archetypes are registered. "
                    "Ensure enemy archetypes are registered in systems.enemies."
                )
    
    return archetype


def allied_party_to_battle_units(
    party: "RoamingParty",
    party_type: "PartyType",
    game: "Game",
    player_level: int = 1
) -> List[Player]:
    """
    Convert an allied roaming party into Player entities for battle.
    
    Allied parties fight on the player's side but are AI-controlled.
    They are similar to companions but are temporary (only for this battle).
    
    Args:
        party: The allied roaming party
        party_type: The party's type definition
        game: Game instance
        player_level: Current player level (for scaling)
    
    Returns:
        List of Player entities ready for battle (on player's side)
    """
    from systems.party import CompanionDef, create_companion_entity
    
    # Calculate how many allies join (similar to enemy scaling, but fewer)
    # Allied parties typically send 1-2 members to help
    num_allies = min(2, max(1, party_type.combat_strength))
    
    allies: List[Player] = []
    
    # Get reference player stats for scaling
    reference_player = game.player if game.player else None
    if not reference_player:
        return allies
    
    base_hp = getattr(reference_player, "max_hp", 30)
    base_attack = getattr(reference_player, "attack_power", 5)
    base_defense = int(getattr(reference_player, "defense", 0))
    base_skill_power = float(getattr(reference_player, "skill_power", 1.0))
    
    # Create a companion-like template for the ally
    # Use party type name and combat strength to determine stats
    for i in range(num_allies):
        # Create a simple companion template based on party type
        ally_template = CompanionDef(
            id=f"{party_type.id}_ally",
            name=party_type.name,
            role="Ally",
            class_id=None,  # No class for temporary allies
            hp_factor=0.7 + (party_type.combat_strength * 0.1),  # 0.7-1.2
            attack_factor=0.6 + (party_type.combat_strength * 0.1),  # 0.6-1.1
            defense_factor=0.8 + (party_type.combat_strength * 0.1),  # 0.8-1.3
            skill_power_factor=1.0,
            skill_ids=[]  # Allies get basic skills
        )
        
        # Create ally entity (similar to companion)
        ally_entity = create_companion_entity(
            template=ally_template,
            state=None,  # No state for temporary allies
            reference_player=reference_player,
            hero_base_hp=base_hp,
            hero_base_attack=base_attack,
            hero_base_defense=base_defense,
            hero_base_skill_power=base_skill_power,
        )
        
        # Set ally name
        ally_name = f"{party_type.name} Ally {i + 1}"
        ally_entity.name = ally_name
        
        # Store party reference for post-combat
        ally_entity.party_id = party.party_id
        ally_entity.is_ally = True  # Mark as temporary ally
        
        allies.append(ally_entity)
    
    return allies

