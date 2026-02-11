"""
Party tooltip utilities.

Creates tooltip data for roaming parties on the overworld.
Uses get_effective_alignment when game is provided so tooltips reflect
faction relations (e.g. friendly party may appear hostile if player has
poor faction reputation).
"""

from typing import TYPE_CHECKING, Optional
from ui.tooltip import TooltipData

if TYPE_CHECKING:
    from world.overworld.party import RoamingParty, PartyType
    from engine.core.game import Game


def create_party_tooltip_data(
    party: "RoamingParty",
    party_type: "PartyType",
    game: Optional["Game"] = None,
) -> TooltipData:
    """
    Create tooltip data for a roaming party.
    
    When game is provided, uses effective alignment (faction-aware) so tooltip
    text stays in sync with join-battle logic. Base alignment shown in parentheses
    when it differs from effective alignment.
    
    Args:
        party: The RoamingParty to create a tooltip for
        party_type: The PartyType definition
        game: Optional game object for context-dependent information
        
    Returns:
        TooltipData with party information
    """
    # Get effective alignment (faction-aware) when game is available
    effective_alignment = party_type.alignment.value
    alignment_source = ""
    if game is not None:
        try:
            from world.overworld.party import get_effective_alignment
            player_faction = getattr(game, "player_faction_id", None) or getattr(
                getattr(game, "hero_stats", None), "faction_id", None
            )
            effective_alignment = get_effective_alignment(
                party, party_type, game, player_faction
            )
            # Note when effective differs from base (faction relations)
            if effective_alignment != party_type.alignment.value and party.faction_id:
                alignment_source = " (faction)"
        except Exception:
            pass
    
    # Title with effective alignment indicator
    alignment_indicators = {
        "friendly": "✓",
        "neutral": "○",
        "hostile": "✗",
    }
    indicator = alignment_indicators.get(effective_alignment, "?")
    title = f"{party_type.name} {indicator}"
    
    lines = []
    
    # Description
    lines.append(party_type.description)
    
    # Alignment: show effective alignment; append base if different (faction)
    alignment_labels = {
        "friendly": "Friendly",
        "neutral": "Neutral",
        "hostile": "Hostile",
    }
    alignment_label = alignment_labels.get(effective_alignment, "Unknown")
    if alignment_source:
        lines.append(f"Alignment: {alignment_label}{alignment_source}")
    else:
        lines.append(f"Alignment: {alignment_label}")
    
    # Faction (if applicable)
    if party.faction_id:
        from systems.factions import get_faction
        faction = get_faction(party.faction_id)
        if faction:
            lines.append(f"Faction: {faction.name}")
    
    # Behavior
    behavior_labels = {
        "patrol": "Patrolling",
        "travel": "Traveling",
        "wander": "Wandering",
        "guard": "Guarding",
        "hunt": "Hunting",
        "flee": "Fleeing",
    }
    behavior_label = behavior_labels.get(party_type.behavior.value, "Unknown")
    lines.append(f"Behavior: {behavior_label}")
    
    # Combat / threat (dynamic power rating)
    if party_type.can_attack or party_type.can_be_attacked:
        from world.overworld.party import get_party_power, get_power_display_string
        power = get_party_power(party, party_type)
        lines.append(f"Threat: {get_power_display_string(power)}")
        if party_type.can_be_attacked:
            lines.append("Can be attacked")
        elif party_type.can_attack:
            lines.append("Hostile")
    else:
        lines.append("Non-combatant")
    
    # Special properties
    special_props = []
    if party_type.can_trade:
        special_props.append("Can trade")
    if party_type.can_recruit:
        special_props.append("Can recruit")
    if party_type.gives_quests:
        special_props.append("Gives quests")
    
    if special_props:
        lines.append("Special: " + ", ".join(special_props))
    
    # Gold (if applicable)
    if party.gold > 0:
        lines.append(f"Gold: {party.gold}")
    
    # Position
    px, py = party.get_position()
    lines.append(f"Location: ({px}, {py})")
    
    # Relationships
    if party_type.enemy_types:
        sorted_enemies = sorted(party_type.enemy_types)
        if len(sorted_enemies) <= 3:
            # Short list: show on one line
            enemy_list = ", ".join(sorted_enemies)
            lines.append(f"Enemies: {enemy_list}")
        else:
            # Long list: show label first, then list items
            lines.append("Enemies:")
            for enemy in sorted_enemies:
                lines.append(f"  • {enemy}")
    
    if party_type.ally_types:
        sorted_allies = sorted(party_type.ally_types)
        if len(sorted_allies) <= 3:
            # Short list: show on one line
            ally_list = ", ".join(sorted_allies)
            lines.append(f"Allies: {ally_list}")
        else:
            # Long list: show label first, then list items
            lines.append("Allies:")
            for ally in sorted_allies:
                lines.append(f"  • {ally}")
    
    return TooltipData(
        title=title,
        lines=lines,
    )

