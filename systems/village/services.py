"""
Village services: inn, shop, recruitment, and other village interactions.
"""

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from engine.core.game import Game
    from world.village.npcs import VillageNPC


def rest_at_inn(game: "Game", cost: Optional[int] = None) -> bool:
    """
    Rest at the inn to fully restore HP and resources.
    
    Args:
        game: Game instance
        cost: Optional gold cost (if None, uses free or level-based cost)
        
    Returns:
        True if rest was successful, False otherwise
    """
    if game.player is None or game.hero_stats is None:
        return False
    
    # Calculate cost if not provided
    if cost is None:
        # Cost based on player level: 5 + (level * 2)
        # Level 1: 7g, Level 5: 15g, Level 10: 25g
        player_level = getattr(game.hero_stats, "level", 1) if game.hero_stats else 1
        cost = 5 + (player_level * 2)
    
    # Check if player can afford it
    if cost > 0 and not game.hero_stats.can_afford(cost):
        game.add_message("You don't have enough gold to rest here.")
        return False
    
    # Pay cost
    if cost > 0:
        game.hero_stats.spend_gold(cost)
    
    # Full heal
    if hasattr(game.player, "max_hp"):
        game.player.hp = game.player.max_hp
    
    # Restore stamina and mana if they exist
    if hasattr(game.player, "max_stamina"):
        game.player.stamina = getattr(game.player, "max_stamina", 0)
    if hasattr(game.player, "max_mana"):
        game.player.mana = getattr(game.player, "max_mana", 0)
    
    # Message
    if cost > 0:
        game.add_message(f"You rest at the inn for {cost} gold and feel completely refreshed.")
    else:
        game.add_message("You rest at the inn and feel completely refreshed.")
    
    return True


def open_shop(game: "Game", merchant_id: Optional[str] = None, village_level: int = 1) -> None:
    """
    Open the shop screen with merchant stock.
    
    Args:
        game: Game instance
        merchant_id: Optional merchant ID (for future use)
        village_level: Village level (used for stock generation)
    """
    from systems.loot import get_shop_stock_for_floor
    from systems.economy import generate_merchant_stock
    
    # Generate shop stock based on village level
    # Use village level instead of floor index
    try:
        # Try using economy system first (better stock generation)
        stock = generate_merchant_stock(village_level, max_items=8)
    except Exception:
        # Fallback to loot system
        stock = get_shop_stock_for_floor(village_level, max_items=8)
    
    # Set shop stock
    game.shop_stock = stock
    # Clear sorted list so it gets regenerated with new stock
    if hasattr(game, "shop_stock_sorted"):
        delattr(game, "shop_stock_sorted")
    game.shop_mode = "buy"  # Start in buy mode
    game.shop_cursor = 0
    
    # Open shop screen
    game.show_shop = True
    game.switch_to_screen("shop")
    
    game.add_message("Welcome to the shop! Browse our wares.")


def open_recruitment(game: "Game", recruiter_id: Optional[str] = None) -> None:
    """
    Open the recruitment screen to view and hire companions.
    
    Args:
        game: Game instance
        recruiter_id: Optional recruiter ID (for future use)
    """
    # Check if we're in a village
    if game.current_poi is None or game.current_poi.poi_type != "village":
        game.add_message("You can only recruit companions in villages.")
        return
    
    # Get available companions from village state
    available_companions = game.current_poi.state.get("available_companions", [])
    
    if not available_companions:
        game.add_message("There are no companions available for recruitment right now.")
        return
    
    # Set recruitment data
    game.show_recruitment = True
    game.recruitment_cursor = 0
    game.available_companions = available_companions
    
    # Open recruitment screen
    game.switch_to_screen("recruitment")
    
    game.add_message(f"There are {len(available_companions)} companions looking for work.")


def recruit_companion(
    game: "Game",
    companion_index: int,
    cost: int,
) -> bool:
    """
    Recruit a companion from the available list.
    
    Args:
        game: Game instance
        companion_index: Index in available_companions list
        cost: Gold cost to recruit
        
    Returns:
        True if recruitment was successful, False otherwise
    """
    if game.current_poi is None or game.current_poi.poi_type != "village":
        return False
    
    # Get available companions
    available_companions = game.current_poi.state.get("available_companions", [])
    
    if companion_index < 0 or companion_index >= len(available_companions):
        return False
    
    # Check party size limit (max 4 total including hero)
    max_party_size = 4
    current_party_size = 1 + len(game.party)  # Hero + companions
    if current_party_size >= max_party_size:
        game.add_message(f"Your party is full! Maximum party size is {max_party_size}.")
        return False
    
    # Check if player can afford it
    if not game.hero_stats.can_afford(cost):
        game.add_message(f"You don't have enough gold. This companion costs {cost} gold.")
        return False
    
    # Get companion data
    from systems.village.companion_generation import AvailableCompanion
    available_comp = available_companions[companion_index]
    
    if not isinstance(available_comp, AvailableCompanion):
        return False
    
    # Pay cost
    game.hero_stats.spend_gold(cost)
    
    # Add companion to party
    game.party.append(available_comp.companion_state)
    
    # Remove from available list
    available_companions.pop(companion_index)
    game.current_poi.state["available_companions"] = available_companions
    
    # Update game's available companions list
    if hasattr(game, "available_companions"):
        game.available_companions = available_companions
    
    # Message
    companion_name = available_comp.generated_name or available_comp.companion_state.name_override or "Companion"
    game.add_message(f"{companion_name} joins your party!")
    
    return True


def open_quest_screen(game: "Game", elder_id: Optional[str] = None) -> None:
    """
    Open the quest screen to view and accept quests from the elder.
    
    Args:
        game: Game instance
        elder_id: Optional elder NPC ID
    """
    # Check if we're in a village
    if game.current_poi is None or game.current_poi.poi_type != "village":
        game.add_message("You can only receive quests in villages.")
        return
    
    # Initialize quests if needed
    if not hasattr(game, "active_quests"):
        game.active_quests = {}
    if not hasattr(game, "available_quests"):
        game.available_quests = {}
    if not hasattr(game, "completed_quests"):
        game.completed_quests = {}
    
    # Initialize elder quests if needed (first time talking to elder)
    elder_id = elder_id or "elder"
    quest_key = f"elder_quests_{game.current_poi.poi_id}"
    
    if quest_key not in game.current_poi.state:
        # Generate initial quests for this elder
        from systems.quests import initialize_elder_quests
        available_quests = initialize_elder_quests(game, elder_id)
        game.current_poi.state[quest_key] = available_quests
        
        # Add to available quests
        for quest in available_quests:
            game.available_quests[quest.quest_id] = quest
    else:
        # Load existing quests
        from systems.quests import QuestStatus
        available_quests = game.current_poi.state[quest_key]
        for quest in available_quests:
            # Handle both Quest objects and serialized dicts
            if isinstance(quest, dict):
                from systems.quests import Quest
                quest = Quest.deserialize(quest)
            if quest.quest_id not in game.active_quests and quest.quest_id not in game.available_quests:
                if quest.status == QuestStatus.AVAILABLE:
                    game.available_quests[quest.quest_id] = quest
    
    # Set quest screen data
    game.show_quests = True
    game.quest_cursor = 0
    game.current_elder_id = elder_id  # Set elder ID so quests are filtered to this elder
    
    # Open quest screen via UI manager
    game.ui_screen_manager.show_quest_screen = True
    game.ui_screen_manager.switch_to_screen(game, "quests")
    
    available_count = len([q for q in game.available_quests.values() if q.quest_giver_id == elder_id])
    active_count = len([q for q in game.active_quests.values() if q.quest_giver_id == elder_id and q.status.value == "active"])
    completed_count = len([q for q in game.active_quests.values() if q.quest_giver_id == elder_id and q.status.value == "completed"])
    
    if available_count > 0:
        game.add_message(f"The elder has {available_count} quest(s) available for you.")
    elif active_count > 0:
        game.add_message(f"You have {active_count} active quest(s) from the elder.")
    elif completed_count > 0:
        game.add_message(f"You have {completed_count} completed quest(s) to turn in.")
    else:
        game.add_message("The elder greets you warmly but has no tasks at the moment.")


def accept_quest(game: "Game", quest_id: str) -> bool:
    """
    Accept a quest from available quests.
    
    Args:
        game: Game instance
        quest_id: Quest ID to accept
        
    Returns:
        True if quest was accepted, False otherwise
    """
    if quest_id not in game.available_quests:
        return False
    
    quest = game.available_quests[quest_id]
    return quest.accept(game)


def turn_in_quest(game: "Game", quest_id: str) -> bool:
    """
    Turn in a completed quest.
    Removes any temporary POIs that were created for this quest.
    
    Args:
        game: Game instance
        quest_id: Quest ID to turn in
        
    Returns:
        True if quest was turned in, False otherwise
    """
    if quest_id not in game.active_quests:
        return False
    
    quest = game.active_quests[quest_id]
    ok = quest.turn_in(game)
    if ok and getattr(game, "overworld_map", None) is not None:
        # Remove temporary POIs that were spawned for this quest
        for obj in getattr(quest, "objectives", []):
            poi_id = getattr(obj, "poi_id", None)
            if not poi_id:
                continue
            poi = game.overworld_map.pois.get(poi_id)
            if poi is None:
                continue
            if getattr(poi, "is_temporary", False) and getattr(poi, "source_quest_id", None) == quest_id:
                game.overworld_map.remove_poi(poi_id)
    return ok