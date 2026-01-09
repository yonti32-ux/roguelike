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

