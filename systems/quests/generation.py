"""
Quest generation and creation helpers.

Contains functions to create different types of quests.
Later this will be expanded with modular quest templates and randomization.
"""

from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from engine.core.game import Game
    from .core import Quest, QuestObjective, QuestReward, QuestType, QuestStatus


def create_explore_dungeon_quest(
    quest_id: str,
    quest_giver_id: str,
    dungeon_poi_id: str,
    dungeon_name: str,
    level: int = 1,
) -> "Quest":
    """
    Create a simple quest to explore a dungeon.
    
    Args:
        quest_id: Unique quest identifier
        quest_giver_id: ID of the NPC giving the quest
        dungeon_poi_id: ID of the dungeon POI to explore
        dungeon_name: Display name of the dungeon
        level: Quest level (affects rewards)
    """
    from .core import Quest, QuestObjective, QuestReward, QuestType, QuestStatus
    
    title = f"Explore {dungeon_name}"
    description = f"The elder asks you to explore {dungeon_name} and clear out any threats."
    
    # Create objective: explore the dungeon
    objective = QuestObjective(
        objective_type="explore",
        description=f"Explore {dungeon_name}",
        poi_id=dungeon_poi_id,
        target_count=1,  # Just need to visit/clear it
        current_count=0,
    )
    
    # Calculate rewards based on level
    base_gold = 50 + (level * 25)
    base_xp = 20 + (level * 10)
    
    reward = QuestReward(
        gold=base_gold,
        xp=base_xp,
    )
    
    quest = Quest(
        quest_id=quest_id,
        title=title,
        description=description,
        quest_giver_id=quest_giver_id,
        quest_type=QuestType.EXPLORE,
        objectives=[objective],
        rewards=reward,
        status=QuestStatus.AVAILABLE,
    )
    
    return quest


def create_kill_enemies_quest(
    quest_id: str,
    quest_giver_id: str,
    enemy_type: str,
    enemy_name: str,
    count: int,
    level: int = 1,
) -> "Quest":
    """
    Create a quest to kill specific enemies.
    
    Args:
        quest_id: Unique quest identifier
        quest_giver_id: ID of the NPC giving the quest
        enemy_type: Enemy archetype ID to kill
        enemy_name: Display name of the enemy
        count: Number of enemies to kill
        level: Quest level (affects rewards)
    """
    from .core import Quest, QuestObjective, QuestReward, QuestType, QuestStatus
    
    title = f"Defeat {enemy_name}"
    if count > 1:
        title = f"Defeat {count} {enemy_name}s"
    
    description = f"Clear the area of {enemy_name.lower()} threats. Defeat {count} of them."
    
    objective = QuestObjective(
        objective_type="kill",
        description=f"Kill {count} {enemy_name}s",
        target_id=enemy_type,
        target_count=count,
        current_count=0,
    )
    
    # Calculate rewards
    base_gold = 30 + (level * 15) * count
    base_xp = 15 + (level * 5) * count
    
    reward = QuestReward(
        gold=base_gold,
        xp=base_xp,
    )
    
    quest = Quest(
        quest_id=quest_id,
        title=title,
        description=description,
        quest_giver_id=quest_giver_id,
        quest_type=QuestType.KILL,
        objectives=[objective],
        rewards=reward,
        status=QuestStatus.AVAILABLE,
    )
    
    return quest


def initialize_elder_quests(game: "Game", elder_id: str) -> List["Quest"]:
    """
    Initialize quests for an elder NPC.
    
    For Phase 1, this creates simple quests based on available POIs.
    Later this will be replaced with a modular quest generation system.
    
    Args:
        game: Game instance
        elder_id: ID of the elder NPC
        
    Returns:
        List of available quests
    """
    quests = []
    
    # Get village level for quest difficulty
    village_level = 1
    if game.current_poi is not None:
        village_level = getattr(game.current_poi, "level", 1)
    
    # Use village level for quest difficulty
    quest_level = village_level
    
    # Try to find nearby dungeons to create explore quests
    # For now, we'll create a simple example quest
    # Later this will be connected to actual overworld POIs
    if hasattr(game, "overworld") and game.overworld is not None:
        # Find dungeons near this village
        nearby_dungeons = []
        if game.current_poi is not None:
            village_pos = game.current_poi.position
            # Look for nearby dungeons in overworld
            # This is a placeholder - we'll need to access overworld POIs
            # For now, create a generic quest
        
        # Create a quest to explore a dungeon (placeholder)
        # Later this will use actual dungeon POIs from the overworld
        quest_id = f"{elder_id}_explore_quest_1"
        dungeon_name = "Ancient Ruins"
        dungeon_poi_id = "dungeon_placeholder_1"  # Placeholder
        
        quest = create_explore_dungeon_quest(
            quest_id=quest_id,
            quest_giver_id=elder_id,
            dungeon_poi_id=dungeon_poi_id,
            dungeon_name=dungeon_name,
            level=quest_level,
        )
        quests.append(quest)
    
    # If we don't have overworld access yet, create a simple kill quest as a fallback
    if not quests:
        # Create a simple kill quest for common enemies
        from systems.enemies import get_enemy_archetype
        try:
            # Try to get a common enemy type
            enemy_types = ["goblin", "skeleton", "orc", "zombie"]
            for enemy_id in enemy_types:
                try:
                    enemy_def = get_enemy_archetype(enemy_id)
                    if enemy_def:
                        enemy_name = enemy_def.name
                        quest_id = f"{elder_id}_kill_{enemy_id}_quest"
                        kill_count = max(3, quest_level)  # Scale with level
                        
                        quest = create_kill_enemies_quest(
                            quest_id=quest_id,
                            quest_giver_id=elder_id,
                            enemy_type=enemy_id,
                            enemy_name=enemy_name,
                            count=kill_count,
                            level=quest_level,
                        )
                        quests.append(quest)
                        break  # Just create one quest for now
                except Exception:
                    continue
        except Exception:
            pass
    
    # If still no quests, create a placeholder explore quest
    if not quests:
        quest_id = f"{elder_id}_explore_quest_1"
        dungeon_name = "Nearby Dungeon"
        dungeon_poi_id = "dungeon_placeholder"
        
        quest = create_explore_dungeon_quest(
            quest_id=quest_id,
            quest_giver_id=elder_id,
            dungeon_poi_id=dungeon_poi_id,
            dungeon_name=dungeon_name,
            level=quest_level,
        )
        quests.append(quest)
    
    return quests

