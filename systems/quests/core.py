"""
Core quest types and definitions.

Contains the fundamental quest structures: Quest, QuestObjective, QuestReward,
and related enums (QuestStatus, QuestType).
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from engine.core.game import Game


class QuestStatus(Enum):
    """Quest status states."""
    AVAILABLE = "available"  # Quest is available to accept
    ACTIVE = "active"  # Quest has been accepted and is in progress
    COMPLETED = "completed"  # Quest objectives are complete, ready to turn in
    TURNED_IN = "turned_in"  # Quest has been turned in


class QuestType(Enum):
    """Types of quests."""
    KILL = "kill"  # Kill specific enemies or reach kill count
    EXPLORE = "explore"  # Explore a specific dungeon/POI
    COLLECT = "collect"  # Collect specific items
    DISCOVER = "discover"  # Discover a specific POI
    ESCORT = "escort"  # Escort NPC (future)
    DELIVERY = "delivery"  # Deliver item to location (future)


@dataclass
class QuestObjective:
    """A single objective within a quest."""
    objective_type: str  # "kill", "explore", "collect", etc.
    description: str  # Human-readable description
    target_id: Optional[str] = None  # ID of target (enemy type, POI ID, item ID)
    target_count: int = 1  # Number required (for kill/collect quests)
    current_count: int = 0  # Current progress
    
    # For POI-related objectives
    poi_id: Optional[str] = None  # POI to explore/visit
    
    def update_progress(self, amount: int = 1) -> None:
        """Update progress on this objective."""
        self.current_count = min(self.current_count + amount, self.target_count)
    
    def is_complete(self) -> bool:
        """Check if objective is complete."""
        return self.current_count >= self.target_count


@dataclass
class QuestReward:
    """Rewards for completing a quest."""
    gold: int = 0
    xp: int = 0
    items: List[str] = field(default_factory=list)  # Item IDs
    
    def apply(self, game: "Game") -> None:
        """Apply quest rewards to the game."""
        if self.gold > 0 and game.hero_stats:
            game.hero_stats.add_gold(self.gold)
            game.add_message(f"You receive {self.gold} gold.")
        
        if self.xp > 0 and game.hero_stats:
            # Add XP (this will trigger level ups if needed)
            xp_messages = game.hero_stats.grant_xp(self.xp)
            for msg in xp_messages:
                game.add_message(msg)
        
        if self.items:
            from systems.inventory import get_item_def
            for item_id in self.items:
                item_def = get_item_def(item_id)
                if item_def:
                    # Add item to inventory
                    if not hasattr(game, "inventory"):
                        game.inventory = []
                    game.inventory.append(item_def)
                    game.add_message(f"You receive {item_def.name}.")


@dataclass
class Quest:
    """
    A quest that can be given by NPCs.
    
    For Phase 1, we'll have simple quest structures.
    Later this will be expanded with randomization and templates.
    """
    quest_id: str
    title: str
    description: str
    quest_giver_id: str  # NPC ID who gives this quest
    
    quest_type: QuestType
    
    objectives: List[QuestObjective] = field(default_factory=list)
    rewards: QuestReward = field(default_factory=QuestReward)
    
    status: QuestStatus = QuestStatus.AVAILABLE
    
    # Optional data for quest tracking
    data: Dict[str, Any] = field(default_factory=dict)
    
    def is_complete(self) -> bool:
        """Check if all objectives are complete."""
        if not self.objectives:
            return False
        return all(obj.is_complete() for obj in self.objectives)
    
    def update_status(self) -> None:
        """Update quest status based on objectives."""
        if self.status == QuestStatus.AVAILABLE:
            return  # Don't change available quests
        
        if self.is_complete() and self.status == QuestStatus.ACTIVE:
            self.status = QuestStatus.COMPLETED
        elif not self.is_complete() and self.status == QuestStatus.COMPLETED:
            # In case progress is lost somehow
            self.status = QuestStatus.ACTIVE
    
    def accept(self, game: "Game") -> bool:
        """Accept the quest."""
        if self.status != QuestStatus.AVAILABLE:
            return False
        
        self.status = QuestStatus.ACTIVE
        
        # Add quest to game's active quests
        if not hasattr(game, "active_quests"):
            game.active_quests = {}
        if not hasattr(game, "available_quests"):
            game.available_quests = {}
        
        # Move from available to active
        if self.quest_id in game.available_quests:
            del game.available_quests[self.quest_id]
        
        game.active_quests[self.quest_id] = self
        game.add_message(f"Quest accepted: {self.title}")
        return True
    
    def turn_in(self, game: "Game") -> bool:
        """Turn in a completed quest."""
        if self.status != QuestStatus.COMPLETED:
            return False
        
        # Apply rewards
        self.rewards.apply(game)
        
        # Mark as turned in
        self.status = QuestStatus.TURNED_IN
        
        # Remove from active quests
        if hasattr(game, "active_quests") and self.quest_id in game.active_quests:
            del game.active_quests[self.quest_id]
        
        # Store in completed quests for reference
        if not hasattr(game, "completed_quests"):
            game.completed_quests = {}
        game.completed_quests[self.quest_id] = self
        
        game.add_message(f"Quest completed: {self.title}")
        return True
    
    def serialize(self) -> Dict[str, Any]:
        """Serialize quest for saving."""
        return {
            "quest_id": self.quest_id,
            "title": self.title,
            "description": self.description,
            "quest_giver_id": self.quest_giver_id,
            "quest_type": self.quest_type.value,
            "objectives": [
                {
                    "objective_type": obj.objective_type,
                    "description": obj.description,
                    "target_id": obj.target_id,
                    "target_count": obj.target_count,
                    "current_count": obj.current_count,
                    "poi_id": obj.poi_id,
                }
                for obj in self.objectives
            ],
            "rewards": {
                "gold": self.rewards.gold,
                "xp": self.rewards.xp,
                "items": self.rewards.items,
            },
            "status": self.status.value,
            "data": self.data,
        }
    
    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> "Quest":
        """Deserialize quest from saved data."""
        quest = cls(
            quest_id=data["quest_id"],
            title=data["title"],
            description=data["description"],
            quest_giver_id=data["quest_giver_id"],
            quest_type=QuestType(data["quest_type"]),
            status=QuestStatus(data["status"]),
            data=data.get("data", {}),
        )
        
        quest.objectives = [
            QuestObjective(
                objective_type=obj_data["objective_type"],
                description=obj_data["description"],
                target_id=obj_data.get("target_id"),
                target_count=obj_data.get("target_count", 1),
                current_count=obj_data.get("current_count", 0),
                poi_id=obj_data.get("poi_id"),
            )
            for obj_data in data.get("objectives", [])
        ]
        
        rewards_data = data.get("rewards", {})
        quest.rewards = QuestReward(
            gold=rewards_data.get("gold", 0),
            xp=rewards_data.get("xp", 0),
            items=rewards_data.get("items", []),
        )
        
        return quest

