"""
Quest progress tracking and update hooks.

Handles updating quest progress when game events occur (enemy kills, POI exploration, etc.).
"""

from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from engine.core.game import Game
    from .core import QuestStatus


def update_quest_progress(
    game: "Game",
    objective_type: str,
    target_id: Optional[str] = None,
    amount: int = 1,
    poi_id: Optional[str] = None,
) -> None:
    """
    Update quest progress when game events occur.
    
    This will be called from various places:
    - When enemies are killed (objective_type="kill")
    - When POIs are explored (objective_type="explore")
    - When items are collected (objective_type="collect")
    
    Args:
        game: Game instance
        objective_type: Type of objective to update ("kill", "explore", "collect", etc.)
        target_id: Optional target ID to match (enemy type, item ID, etc.)
        amount: Amount to increment progress (default: 1)
        poi_id: Optional POI ID to match (for explore/discover objectives)
    """
    from .core import QuestStatus
    
    if not hasattr(game, "active_quests"):
        return
    
    for quest in game.active_quests.values():
        if quest.status != QuestStatus.ACTIVE:
            continue
        
        for objective in quest.objectives:
            # Check if this objective matches the event
            if objective.objective_type != objective_type:
                continue
            
            # Check target match (if specified)
            if target_id is not None and objective.target_id != target_id:
                continue
            
            # Check POI match (if specified)
            if poi_id is not None and objective.poi_id != poi_id:
                continue
            
            # Update progress
            objective.update_progress(amount)
            quest.update_status()

