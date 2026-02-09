"""
Quest generation and creation helpers.

Contains functions to create different types of quests.
Later this will be expanded with modular quest templates and randomization.
"""

from typing import Any, List, Optional, TYPE_CHECKING

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


def spawn_quest_camp_poi(
    game: "Game",
    village_position: tuple,
    quest_id: str,
    quest_level: int = 1,
) -> Optional[Any]:
    """
    Spawn a temporary camp POI near the village for a "clear the camp" style quest.
    Finds a walkable tile with no existing POI, creates a hostile camp, adds it to the overworld.
    
    Returns:
        The created PointOfInterest, or None if no valid position found.
    """
    import random
    overworld = getattr(game, "overworld_map", None)
    if overworld is None:
        return None
    vx, vy = village_position
    min_dist_sq, max_dist_sq = 8 * 8, 22 * 22
    for _ in range(50):
        dx = random.randint(-22, 22)
        dy = random.randint(-22, 22)
        d_sq = dx * dx + dy * dy
        if d_sq < min_dist_sq or d_sq > max_dist_sq:
            continue
        x = vx + dx
        y = vy + dy
        if not overworld.in_bounds(x, y) or not overworld.is_walkable(x, y):
            continue
        if overworld.get_poi_at(x, y) is not None:
            continue
        # Create temporary camp POI (unique id per quest and position so multiple villages don't collide)
        from world.poi.registry import get_registry
        poi_id = f"quest_camp_{quest_id}_{vx}_{vy}"
        if poi_id in overworld.pois:
            continue  # Already spawned for this quest (e.g. re-opened elder)
        registry = get_registry()
        try:
            camp = registry.create(
                "camp",
                poi_id,
                (x, y),
                level=quest_level,
                name="Bandit Camp",
                is_temporary=True,
                source_quest_id=quest_id,
            )
        except Exception:
            continue
        camp.discovered = True  # Show on map so player can go there
        camp.is_hostile = True
        overworld.add_poi(camp)
        return camp
    return None


def _get_nearby_pois_for_quest(
    game: "Game",
    center_position: tuple,
    radius: int = 40,
    poi_types: tuple = ("dungeon", "camp"),
    exclude_temporary: bool = True,
) -> List[Any]:
    """
    Get POIs near a position that can be used as quest targets.
    Prefers dungeons and camps; excludes temporary POIs by default.
    """
    overworld = getattr(game, "overworld_map", None)
    if overworld is None:
        return []
    cx, cy = center_position
    in_range = overworld.get_pois_in_range(cx, cy, radius)
    result = []
    for poi in in_range:
        if poi.poi_type not in poi_types:
            continue
        if exclude_temporary and getattr(poi, "is_temporary", False):
            continue
        result.append(poi)
    # Sort by distance (closest first)
    result.sort(key=lambda p: (p.position[0] - cx) ** 2 + (p.position[1] - cy) ** 2)
    return result


def initialize_elder_quests(game: "Game", elder_id: str) -> List["Quest"]:
    """
    Initialize quests for an elder NPC.
    Uses real nearby dungeons/camps from the overworld when available.
    Falls back to kill quest or placeholder explore if no suitable POI.
    
    Args:
        game: Game instance
        elder_id: ID of the elder NPC
        
    Returns:
        List of available quests
    """
    quests = []
    
    # Get village/town level for quest difficulty
    village_level = 1
    if game.current_poi is not None:
        village_level = getattr(game.current_poi, "level", 1)
    quest_level = village_level
    
    # Use overworld_map to find real nearby dungeons/camps
    if game.current_poi is not None and getattr(game, "overworld_map", None) is not None:
        village_pos = game.current_poi.position
        nearby = _get_nearby_pois_for_quest(game, village_pos, radius=40, exclude_temporary=True)
        # Prefer dungeons, then camps; optionally prefer not-yet-cleared
        dungeons = [p for p in nearby if p.poi_type == "dungeon"]
        camps = [p for p in nearby if p.poi_type == "camp"]
        # Prefer uncleared for "clear the threat" flavor
        def prefer_uncleared(poi_list: List[Any]) -> "Optional[Any]":
            for p in poi_list:
                if not getattr(p, "cleared", True):
                    return p
            return poi_list[0] if poi_list else None
        
        target_poi = prefer_uncleared(dungeons) or prefer_uncleared(camps) or (dungeons[0] if dungeons else None) or (camps[0] if camps else None)
        if target_poi is not None:
            quest_id = f"{elder_id}_explore_{target_poi.poi_id}"
            quest = create_explore_dungeon_quest(
                quest_id=quest_id,
                quest_giver_id=elder_id,
                dungeon_poi_id=target_poi.poi_id,
                dungeon_name=target_poi.name,
                level=quest_level,
            )
            quests.append(quest)
    
    # Fallback: kill quest when no suitable dungeon/camp nearby
    if not quests:
        from systems.enemies import get_enemy_archetype
        try:
            enemy_types = ["goblin", "skeleton", "orc", "zombie"]
            for enemy_id in enemy_types:
                try:
                    enemy_def = get_enemy_archetype(enemy_id)
                    if enemy_def:
                        enemy_name = enemy_def.name
                        quest_id = f"{elder_id}_kill_{enemy_id}_quest"
                        kill_count = max(3, quest_level)
                        quest = create_kill_enemies_quest(
                            quest_id=quest_id,
                            quest_giver_id=elder_id,
                            enemy_type=enemy_id,
                            enemy_name=enemy_name,
                            count=kill_count,
                            level=quest_level,
                        )
                        quests.append(quest)
                        break
                except Exception:
                    continue
        except Exception:
            pass
    
    # Last resort: spawn a temporary "bandit camp" POI and create explore quest for it
    if not quests and game.current_poi is not None and getattr(game, "overworld_map", None) is not None:
        quest_id = f"{elder_id}_explore_quest_1"
        camp = spawn_quest_camp_poi(game, game.current_poi.position, quest_id, quest_level)
        if camp is not None:
            quest = create_explore_dungeon_quest(
                quest_id=quest_id,
                quest_giver_id=elder_id,
                dungeon_poi_id=camp.poi_id,
                dungeon_name=camp.name,
                level=quest_level,
            )
            quests.append(quest)
    
    # If still no quests (spawn failed or no overworld), use placeholder explore
    if not quests:
        quest_id = f"{elder_id}_explore_quest_1"
        quest = create_explore_dungeon_quest(
            quest_id=quest_id,
            quest_giver_id=elder_id,
            dungeon_poi_id="dungeon_placeholder",
            dungeon_name="Nearby Dungeon",
            level=quest_level,
        )
        quests.append(quest)
    
    return quests

