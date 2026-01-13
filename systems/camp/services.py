"""
Camp services: rest and simple camp merchant behavior.

These are deliberately simpler than village services. Camps are meant
to be quick stops for recovery and basic supplies.
"""

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from engine.core.game import Game


def rest_at_camp(game: "Game", cost: Optional[int] = None) -> bool:
    """
    Rest at a friendly or neutral camp to fully restore HP and resources.

    Cost can depend on faction relations; by default camps are cheaper
    than village inns and often free for friendly factions.
    """
    if game.player is None or game.hero_stats is None:
        return False

    # Calculate cost if not provided: cheaper than inn by default
    if cost is None:
        player_level = getattr(game.hero_stats, "level", 1) if game.hero_stats else 1
        # Example: 2 + level, so Level 1: 3g, Level 5: 7g, Level 10: 12g
        cost = 2 + player_level

    # Check if player can afford it
    if cost > 0 and not game.hero_stats.can_afford(cost):
        game.add_message("You don't have enough gold to rest at this camp.")
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
        game.add_message(f"You rest by the campfire for {cost} gold and feel completely refreshed.")
    else:
        game.add_message("You rest by the campfire and feel completely refreshed.")

    return True


def open_camp_merchant(game: "Game", camp_level: int = 1) -> None:
    """
    Open a simple camp merchant with a limited consumable-focused stock.

    For now this mirrors village shops but can be tuned independently later.
    """
    from systems.loot import get_shop_stock_for_floor
    from systems.economy import generate_merchant_stock

    # Generate shop stock based on camp level (like a shallow floor)
    try:
        stock = generate_merchant_stock(camp_level, max_items=5)
    except Exception:
        stock = get_shop_stock_for_floor(camp_level, max_items=5)

    game.shop_stock = stock
    # Clear sorted list so it gets regenerated with new stock
    if hasattr(game, "shop_stock_sorted"):
        delattr(game, "shop_stock_sorted")
    game.shop_mode = "buy"
    game.shop_cursor = 0

    game.show_shop = True
    game.switch_to_screen("shop")

    game.add_message("A camp merchant offers you some basic supplies.")



