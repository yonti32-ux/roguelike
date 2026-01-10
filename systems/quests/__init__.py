"""
Quest system for NPCs to give quests to the player.

This module provides the foundation for a modular quest system.
Organized into submodules:
- core: Core quest types and definitions (Quest, QuestObjective, QuestReward, enums)
- givers: QuestGiver class for managing NPC quests
- generation: Quest creation helpers and templates
- progress: Progress tracking and update hooks

For backward compatibility, this module exports all the main classes and functions.
"""

# Core types
from .core import (
    QuestStatus,
    QuestType,
    QuestObjective,
    QuestReward,
    Quest,
)

# Quest givers
from .givers import QuestGiver

# Quest generation
from .generation import (
    create_explore_dungeon_quest,
    create_kill_enemies_quest,
    initialize_elder_quests,
)

# Progress tracking
from .progress import update_quest_progress

__all__ = [
    # Core types
    "QuestStatus",
    "QuestType",
    "QuestObjective",
    "QuestReward",
    "Quest",
    # Quest givers
    "QuestGiver",
    # Generation
    "create_explore_dungeon_quest",
    "create_kill_enemies_quest",
    "initialize_elder_quests",
    # Progress
    "update_quest_progress",
]

