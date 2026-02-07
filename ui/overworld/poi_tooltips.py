"""
POI tooltip utilities.

Creates tooltip data for Points of Interest.
Uses extensibility methods from POI classes for type-specific information.
"""

from typing import TYPE_CHECKING, Optional
from ui.tooltip import TooltipData

if TYPE_CHECKING:
    from world.poi.base import PointOfInterest
    from engine.core.game import Game


def create_poi_tooltip_data(poi: "PointOfInterest", game: Optional["Game"] = None) -> TooltipData:
    """
    Create tooltip data for a POI.
    
    Uses extensibility methods from the POI class for type-specific information.
    This makes the tooltip system fully extensible - new POI types just need to
    implement get_tooltip_lines() and get_display_label().
    
    Args:
        poi: The PointOfInterest to create a tooltip for
        game: Optional game object for context-dependent information
        
    Returns:
        TooltipData with POI information
    """
    # Title with type label (uses extensibility method)
    type_label = poi.get_display_label()
    title = f"{poi.name} [{type_label}]"
    
    lines = []
    
    # Status
    if poi.cleared:
        lines.append("Status: Cleared")
    elif poi.discovered:
        lines.append("Status: Discovered")
    else:
        lines.append("Status: Undiscovered")
    
    # Level/difficulty
    lines.append(f"Level: {poi.level}")
    
    # Faction information (if available)
    faction_id = getattr(poi, "faction_id", None)
    if faction_id and game and game.overworld_map and game.overworld_map.faction_manager:
        faction = game.overworld_map.faction_manager.get_faction(faction_id)
        if faction:
            alignment_colors = {
                "good": "Light Blue",
                "neutral": "Gray", 
                "evil": "Dark Red"
            }
            alignment = faction.alignment.value if hasattr(faction.alignment, "value") else str(faction.alignment)
            color_name = alignment_colors.get(alignment, "Unknown")
            lines.append(f"Faction: {faction.name} ({color_name})")
    
    # POI-specific information (uses extensibility method)
    poi_specific_lines = poi.get_tooltip_lines(game)
    lines.extend(poi_specific_lines)
    
    # Position info
    px, py = poi.position
    lines.append(f"Location: ({px}, {py})")
    
    # Action hint
    if poi.discovered:
        if poi.can_enter(None):  # Pass None since we don't need full game check for tooltip
            lines.append("Press E to enter")
        else:
            lines.append("Cannot enter")
    
    return TooltipData(
        title=title,
        lines=lines,
    )

