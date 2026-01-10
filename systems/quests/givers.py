"""
Quest giver management.

Handles NPCs that can give quests and manages their quest lists.
"""

from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from engine.core.game import Game
    from .core import Quest, QuestStatus


class QuestGiver:
    """Manages quests given by an NPC."""
    
    def __init__(self, npc_id: str):
        self.npc_id = npc_id
        self.quests: List["Quest"] = []
    
    def add_quest(self, quest: "Quest") -> None:
        """Add a quest to this quest giver."""
        self.quests.append(quest)
    
    def get_available_quests(self) -> List["Quest"]:
        """Get all available quests from this NPC."""
        from .core import QuestStatus
        return [q for q in self.quests if q.status == QuestStatus.AVAILABLE]
    
    def get_active_quests(self, game: "Game") -> List["Quest"]:
        """Get all active quests from this NPC."""
        from .core import QuestStatus
        if not hasattr(game, "active_quests"):
            return []
        return [q for q in game.active_quests.values() if q.quest_giver_id == self.npc_id and q.status == QuestStatus.ACTIVE]
    
    def get_completed_quests(self, game: "Game") -> List["Quest"]:
        """Get all completed (ready to turn in) quests from this NPC."""
        from .core import QuestStatus
        if not hasattr(game, "active_quests"):
            return []
        return [q for q in game.active_quests.values() if q.quest_giver_id == self.npc_id and q.status == QuestStatus.COMPLETED]
    
    def get_quest_by_id(self, quest_id: str) -> Optional["Quest"]:
        """Get a quest by ID."""
        for quest in self.quests:
            if quest.quest_id == quest_id:
                return quest
        return None

