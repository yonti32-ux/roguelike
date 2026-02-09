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
    choose_archetype_for_floor,
)

if TYPE_CHECKING:
    from .roaming_party import RoamingParty
    from .party_types import PartyType
    from engine.core.game import Game


def get_effective_alignment(
    party: "RoamingParty",
    party_type: "PartyType",
    game: "Game",
    player_faction: Optional[str] = None
) -> str:
    """
    Get the effective alignment of a party considering faction relations.
    
    This allows parties to change from allies to enemies based on reputation.
    
    Args:
        party: The roaming party
        party_type: The party's type definition
        game: Game instance
        player_faction: Player's faction ID (if any)
    
    Returns:
        Effective alignment: "hostile", "neutral", or "friendly"
    """
    # If party is explicitly hostile, always hostile
    if party_type.alignment.value == "hostile":
        return "hostile"
    
    # If party is explicitly friendly, check faction relations
    if party_type.alignment.value == "friendly":
        # Check if faction relations make them hostile
        if party.faction_id and player_faction and game.overworld_map and game.overworld_map.faction_manager:
            relation = game.overworld_map.faction_manager.get_relation(
                player_faction, party.faction_id
            )
            # Very hostile relations (< -50) -> become hostile
            if relation < -50:
                return "hostile"
            # Very friendly relations (> 50) -> stay friendly
            if relation > 50:
                return "friendly"
            # Neutral range -> neutral
            return "neutral"
        return "friendly"
    
    # Neutral parties check faction relations
    if party_type.alignment.value == "neutral":
        if party.faction_id and player_faction and game.overworld_map and game.overworld_map.faction_manager:
            relation = game.overworld_map.faction_manager.get_relation(
                player_faction, party.faction_id
            )
            # Hostile relations (< -50) -> become hostile
            if relation < -50:
                return "hostile"
            # Friendly relations (> 50) -> become friendly
            if relation > 50:
                return "friendly"
        return "neutral"
    
    # Default to party type alignment
    return party_type.alignment.value


def party_to_battle_enemies(
    party: "RoamingParty",
    party_type: "PartyType",
    game: "Game",
    player_level: int = 1,
    player_faction: Optional[str] = None
) -> List[Enemy]:
    """
    Convert a roaming party into a list of Enemy entities for battle.
    
    Strategy:
    1. Get party power from party_power module (type + size + state)
    2. Scale enemy count from player party size and party power
    3. Use party_type.battle_unit_template if available (enemy archetype ID)
    4. Otherwise pick archetype by power-derived floor (choose_archetype_for_floor)
    5. Scale enemy stats by battle_floor (from power + player level) and stat_factor
    
    Note: This function is used when the party is hostile to the player.
    For friendly parties, use allied_party_to_battle_units instead.
    
    Args:
        party: The roaming party to convert
        party_type: The party's type definition
        game: Game instance (for map/context and party access)
        player_level: Current player level (for scaling)
        player_faction: Player's faction ID (for alignment checks)
    
    Returns:
        List of Enemy entities ready for battle
    """
    from .party_power import (
        get_party_power,
        power_to_floor_index,
        power_to_enemy_count_factor,
        power_to_stat_factor,
    )

    enemies = []
    power = get_party_power(party, party_type)
    battle_floor = power_to_floor_index(power, player_level)

    # Calculate player party size (hero + active companions)
    player_party_size = _get_player_party_size(game)

    # Calculate enemy count based on party size and party power
    num_enemies = _calculate_enemy_count(
        player_party_size=player_party_size,
        party_power=power,
        party_type_id=party_type.id,
    )

    # Try to use battle_unit_template if available
    if party_type.battle_unit_template:
        try:
            archetype = get_archetype(party_type.battle_unit_template)
            if archetype:
                for i in range(num_enemies):
                    enemy = _create_enemy_from_archetype(
                        archetype, battle_floor, party, i, num_enemies,
                        stat_factor=power_to_stat_factor(power),
                    )
                    enemies.append(enemy)
                return enemies
        except (KeyError, Exception) as e:
            print(f"Warning: Failed to get archetype '{party_type.battle_unit_template}': {e}")

    # Select archetype by party power (floor) so battle difficulty matches overworld threat
    try:
        default_archetype = choose_archetype_for_floor(battle_floor)
    except Exception as e:
        print(f"Warning: choose_archetype_for_floor failed: {e}, using power fallback")
        default_archetype = _get_default_archetype_for_power(power)

    stat_factor = power_to_stat_factor(power)
    for i in range(num_enemies):
        enemy = _create_enemy_from_archetype(
            default_archetype, battle_floor, party, i, num_enemies,
            stat_factor=stat_factor,
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
    party_power: float,
    party_type_id: str,
) -> int:
    """
    Calculate the number of enemies to spawn based on player party size and party power.

    Scaling:
    - Base count scales with party power (higher power -> more enemies)
    - Per additional player party member: +1.0 to +2.0 enemies (with variation)
    - Party type can have special scaling rules (swarm vs elite)

    Args:
        player_party_size: Number of characters in player party (2+)
        party_power: Dynamic power rating of the overworld party (from party_power module)
        party_type_id: ID of the party type (for special rules)

    Returns:
        Number of enemies to spawn (1-8, with variation)
    """
    from .party_power import power_to_enemy_count_factor

    MIN_ENEMIES = 1
    MAX_ENEMIES = 8
    BASE_ENEMIES_MIN = 1
    BASE_ENEMIES_MAX = 4
    SCALING_MIN = 1.0
    SCALING_MAX = 2.0

    effective_party_size = max(2, player_party_size)
    power_factor = power_to_enemy_count_factor(party_power)

    # Base count: power 20 -> ~1-2, power 50 -> ~2-3, power 80 -> ~2-4
    base_range = max(1, int(1 + power_factor * 2.5))
    base_min = BASE_ENEMIES_MIN
    base_max = min(BASE_ENEMIES_MAX + 1, base_range + 1)

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
    battle_floor: int,
    party: "RoamingParty",
    index: int,
    total_enemies: int,
    stat_factor: float = 1.0,
) -> Enemy:
    """
    Create an Enemy entity from an archetype.

    Stats are scaled by battle_floor (from party power + player level) and
    optionally by stat_factor for fine-tuning from overworld power.

    Args:
        archetype: Enemy archetype definition
        battle_floor: Floor index for stat scaling (from power_to_floor_index)
        party: The roaming party this enemy belongs to
        index: Index of this enemy (0-based)
        total_enemies: Total number of enemies in this battle (for naming)
        stat_factor: Multiplier for HP/attack/defense (from power_to_stat_factor)

    Returns:
        Enemy entity ready for battle
    """
    floor = max(1, battle_floor)
    max_hp, attack, defense, xp, initiative = compute_scaled_stats(archetype, floor)

    if stat_factor != 1.0:
        max_hp = max(1, int(max_hp * stat_factor))
        attack = max(1, int(attack * stat_factor))
        defense = max(0, int(defense * stat_factor))

    if total_enemies > 1:
        xp = int(xp / (1.0 + (total_enemies - 1) * 0.3))
        xp = max(1, xp)
    
    # Create enemy name - use party name if available, otherwise use party type
    if party.party_name:
        # Use party name for more variety (e.g., "Bandit Gang Member 1")
        base_name = party.party_name.split()[0] if party.party_name else party.party_type_id.title()
        enemy_name = f"{base_name} {index + 1}"
    else:
        enemy_name = f"{party.party_type_id.title()} {index + 1}"  # e.g., "Bandit 1"
    
    enemy = Enemy(
        x=0.0,
        y=0.0,
        width=32,
        height=32,
        speed=0.0,
        color=(200, 80, 80),
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


def _get_default_archetype_for_power(power: float) -> EnemyArchetype:
    """
    Get a default enemy archetype based on party power (fallback when choose_archetype_for_floor fails).
    """
    if power < 25:
        archetype_id = "goblin_skirmisher"
    elif power < 45:
        archetype_id = "bandit_cutthroat"
    elif power < 70:
        archetype_id = "orc_raider"
    elif power < 100:
        archetype_id = "dread_knight"
    else:
        archetype_id = "dragonkin"

    try:
        return get_archetype(archetype_id)
    except (KeyError, Exception) as e:
        print(f"Warning: get_archetype('{archetype_id}') failed: {e}")

    for fallback_id in ("goblin_skirmisher", "bandit_cutthroat"):
        try:
            return get_archetype(fallback_id)
        except (KeyError, Exception):
            pass

    from systems.enemies import ENEMY_ARCHETYPES
    if ENEMY_ARCHETYPES:
        return list(ENEMY_ARCHETYPES.values())[0]
    raise RuntimeError(
        "No enemy archetype found for power and no archetypes are registered."
    )


def _get_default_archetype_for_strength(strength: int) -> EnemyArchetype:
    """
    Get a default enemy archetype based on combat strength (1-5).
    Legacy fallback; prefer _get_default_archetype_for_power when party power is available.
    """
    strength_to_archetype = {
        1: "goblin_skirmisher",
        2: "bandit_cutthroat",
        3: "orc_raider",
        4: "dread_knight",
        5: "dragonkin",
    }
    archetype_id = strength_to_archetype.get(strength, "bandit_cutthroat")

    try:
        archetype = get_archetype(archetype_id)
        if archetype is not None:
            return archetype
    except (KeyError, Exception) as e:
        print(f"Warning: get_archetype('{archetype_id}') failed: {e}")

    try:
        return get_archetype("goblin_skirmisher")
    except (KeyError, Exception):
        pass

    from systems.enemies import ENEMY_ARCHETYPES
    if ENEMY_ARCHETYPES:
        return list(ENEMY_ARCHETYPES.values())[0]
    raise RuntimeError(
        f"No enemy archetype found for strength {strength}. "
        "Ensure enemy archetypes are registered in systems.enemies."
    )


def allied_party_to_battle_units(
    party: "RoamingParty",
    party_type: "PartyType",
    game: "Game",
    player_level: int = 1
) -> List[Player]:
    """
    Convert an allied roaming party into Player entities for battle.
    
    Allied parties fight on the player's side but are AI-controlled.
    Uses ally archetypes for variety and proper stat scaling.
    
    Args:
        party: The allied roaming party
        party_type: The party's type definition
        game: Game instance
        player_level: Current player level (for scaling)
    
    Returns:
        List of Player entities ready for battle (on player's side)
    """
    from world.entities import Player
    from systems.allies import get_archetype, get_archetype_for_party_type
    from systems.allies.scaling import compute_scaled_stats
    from .party_power import get_party_power, power_to_stat_factor

    power = get_party_power(party, party_type)
    stat_factor = power_to_stat_factor(power)

    # Number of allies: scale with party power (1-3 typically)
    num_allies = min(3, max(1, int(1 + power / 40)))
    
    allies: List[Player] = []
    
    # Try to use ally pack if multiple allies and pack exists
    from systems.allies import get_packs_for_party_type
    import random
    
    ally_pack = None
    if num_allies >= 2:
        available_packs = get_packs_for_party_type(party_type.id)
        if available_packs:
            # Weighted random selection
            total_weight = sum(pack.weight for pack in available_packs)
            if total_weight > 0:
                rand = random.random() * total_weight
                cumulative = 0
                for pack in available_packs:
                    cumulative += pack.weight
                    if rand <= cumulative:
                        ally_pack = pack
                        break
    
    # If we have a pack, use it
    if ally_pack and len(ally_pack.member_arch_ids) <= num_allies:
        # Use pack members
        for i, arch_id in enumerate(ally_pack.member_arch_ids[:num_allies]):
            try:
                ally_archetype = get_archetype(arch_id)
            except KeyError:
                # Fall back to single archetype lookup
                ally_archetype = get_archetype_for_party_type(party_type.id)
                if not ally_archetype:
                    break
    else:
        # Try to get ally archetype for this party type
        ally_archetype = None
        
        # First, try to get archetype by party type ID
        ally_archetype = get_archetype_for_party_type(party_type.id)
    
    # If no archetype found, try using battle_unit_template (if it's an ally archetype)
    if not ally_archetype and party_type.battle_unit_template:
        try:
            # Check if it's an ally archetype (not an enemy archetype)
            ally_archetype = get_archetype(party_type.battle_unit_template)
        except (KeyError, Exception):
            # Not an ally archetype, fall through to default
            pass
    
    # If still no archetype, use a default based on party type
    if not ally_archetype:
        # Fallback: create a basic ally based on party type
        # This maintains backward compatibility
        from systems.party import CompanionDef, create_companion_entity
        
        reference_player = game.player if game.player else None
        if not reference_player:
            return allies
        
        base_hp = getattr(reference_player, "max_hp", 30)
        base_attack = getattr(reference_player, "attack_power", 5)
        base_defense = int(getattr(reference_player, "defense", 0))
        base_skill_power = float(getattr(reference_player, "skill_power", 1.0))
        
        for i in range(num_allies):
            ally_template = CompanionDef(
                id=f"{party_type.id}_ally",
                name=party_type.name,
                role="Ally",
                class_id=None,
                hp_factor=min(1.2, 0.6 + stat_factor * 0.4),
                attack_factor=min(1.2, 0.5 + stat_factor * 0.4),
                defense_factor=min(1.2, 0.6 + stat_factor * 0.4),
                skill_power_factor=1.0,
                skill_ids=["guard"]
            )
            
            ally_entity = create_companion_entity(
                template=ally_template,
                state=None,
                reference_player=reference_player,
                hero_base_hp=base_hp,
                hero_base_attack=base_attack,
                hero_base_defense=base_defense,
                hero_base_skill_power=base_skill_power,
            )
            
            ally_entity.name = f"{party_type.name} Ally {i + 1}"
            ally_entity.party_id = party.party_id
            ally_entity.is_ally = True
            ally_entity.ally_archetype_id = None  # No archetype for fallback
            
            allies.append(ally_entity)
        
        return allies
    
    # Use ally archetype system
    archetypes_to_use = []
    
    if ally_pack:
        # Use pack members
        for arch_id in ally_pack.member_arch_ids[:num_allies]:
            try:
                arch = get_archetype(arch_id)
                archetypes_to_use.append(arch)
            except KeyError:
                pass
    else:
        # Use single archetype for all allies
        for _ in range(num_allies):
            archetypes_to_use.append(ally_archetype)
    
    # Create allies from archetypes
    for i, archetype in enumerate(archetypes_to_use):
        if not archetype:
            continue
            
        # Calculate scaled stats
        max_hp, attack, defense, skill_power, initiative = compute_scaled_stats(
            archetype, player_level
        )
        
        # Get reference player for dimensions/color
        reference_player = game.player if game.player else None
        if reference_player:
            width = reference_player.width
            height = reference_player.height
            color = reference_player.color
        else:
            width = 32
            height = 32
            color = (100, 150, 255)  # Blue-ish for allies
        
        # Create Player entity
        ally_entity = Player(
            x=0.0,
            y=0.0,
            width=width,
            height=height,
            speed=0.0,
            color=color,
            max_hp=max_hp,
            hp=max_hp,
            attack_power=attack,
        )
        
        # Set additional stats
        setattr(ally_entity, "defense", defense)
        setattr(ally_entity, "skill_power", skill_power)
        setattr(ally_entity, "initiative", initiative)
        setattr(ally_entity, "level", player_level)
        
        # Set ally properties
        if len(archetypes_to_use) > 1:
            ally_entity.name = f"{archetype.name} {i + 1}"
        else:
            ally_entity.name = archetype.name
        ally_entity.party_id = party.party_id
        ally_entity.is_ally = True
        ally_entity.ally_archetype_id = archetype.id  # Store archetype ID for AI profile
        
        # Store skill IDs for later assignment
        ally_entity.ally_skill_ids = archetype.skill_ids.copy()
        
        # Store pack info if using a pack
        if ally_pack:
            ally_entity.ally_pack_id = ally_pack.id
        
        allies.append(ally_entity)
    
    return allies

