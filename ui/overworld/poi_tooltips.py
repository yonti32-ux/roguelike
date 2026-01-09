"""
POI tooltip utilities.

Creates tooltip data for Points of Interest.
"""

from typing import TYPE_CHECKING, Optional
from ui.tooltip import TooltipData

if TYPE_CHECKING:
    from world.poi.base import PointOfInterest
    from engine.core.game import Game


def _calculate_party_average_level(game: Optional["Game"]) -> float:
    """
    Calculate the average level of the player's party (hero + companions).
    
    Args:
        game: Game object (can be None if not available)
        
    Returns:
        Average party level, or 1.0 if game is not available
    """
    if game is None:
        return 1.0
    
    hero_level = getattr(game.hero_stats, "level", 1) if hasattr(game, "hero_stats") else 1
    party = getattr(game, "party", []) if hasattr(game, "party") else []
    
    if not party:
        return float(hero_level)
    
    companion_levels = [comp.level for comp in party if hasattr(comp, "level")]
    total_level = hero_level + sum(companion_levels)
    total_count = 1 + len(companion_levels)
    
    return total_level / total_count if total_count > 0 else 1.0


def _estimate_difficulty(dungeon_level: int, party_level: float) -> str:
    """
    Estimate difficulty of a dungeon compared to party level.
    
    Args:
        dungeon_level: The dungeon's difficulty level
        party_level: Average party level
        
    Returns:
        Difficulty description string
    """
    level_diff = dungeon_level - party_level
    
    if level_diff <= -3:
        return "Very Easy"
    elif level_diff <= -2:
        return "Easy"
    elif level_diff <= -1:
        return "Fairly Easy"
    elif level_diff <= 0:
        return "Appropriate"
    elif level_diff <= 1:
        return "Challenging"
    elif level_diff <= 2:
        return "Hard"
    elif level_diff <= 3:
        return "Very Hard"
    else:
        return "Extreme"


def create_poi_tooltip_data(poi: "PointOfInterest", game: Optional["Game"] = None) -> TooltipData:
    """
    Create tooltip data for a POI.
    
    Args:
        poi: The PointOfInterest to create a tooltip for
        game: Optional game object for difficulty estimation
        
    Returns:
        TooltipData with POI information
    """
    # Title with type icon/color
    type_labels = {
        "dungeon": "Dungeon",
        "village": "Village",
        "town": "Town",
        "camp": "Camp",
    }
    type_label = type_labels.get(poi.poi_type, poi.poi_type.capitalize())
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
    
    # POI-specific information
    if poi.poi_type == "dungeon":
        floors_cleared = len(poi.cleared_floors) if hasattr(poi, "cleared_floors") else 0
        floor_count = poi.floor_count if hasattr(poi, "floor_count") else 0
        
        # Show floor count
        lines.append(f"Floors: {floor_count}")
        
        # Show progress
        if poi.cleared:
            lines.append(f"Progress: {floor_count}/{floor_count} floors cleared (100%)")
        else:
            lines.append(f"Progress: {floors_cleared}/{floor_count} floors")
            if floor_count > 0:
                progress_pct = int((floors_cleared / floor_count) * 100)
                lines.append(f"Completion: {progress_pct}%")
        
        # Difficulty estimation (if game object is available)
        if game is not None:
            party_level = _calculate_party_average_level(game)
            difficulty = _estimate_difficulty(poi.level, party_level)
            lines.append(f"Difficulty: {difficulty} (Party Lv: {party_level:.1f})")
    
    elif poi.poi_type in ("village", "town"):
        buildings = poi.buildings if hasattr(poi, "buildings") else []
        if buildings:
            building_list = ", ".join(b.title() for b in buildings[:3])
            if len(buildings) > 3:
                building_list += "..."
            lines.append(f"Services: {building_list}")
    
    # Position info
    px, py = poi.position
    lines.append(f"Location: ({px}, {py})")
    
    # Action hint
    if poi.discovered:
        if poi.can_enter(None):  # Pass None since we don't need full game check for tooltip
            lines.append("Press E to enter")
        else:
            lines.append("Cannot enter")
    
    # Description if available
    description = poi.get_description()
    if description and description != title:
        # Use the description as the main info
        pass
    
    return TooltipData(
        title=title,
        lines=lines,
    )

