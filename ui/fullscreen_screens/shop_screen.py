"""
Shop screen module for buying and selling items.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List

import pygame

from settings import COLOR_BG
from systems.inventory import get_item_def
from systems.economy import (
    calculate_shop_buy_price,
    calculate_shop_sell_price,
)
from ui.screen_components import (
    draw_screen_header,
    draw_screen_footer,
    build_item_info_line,
)
from ui.screen_constants import COLOR_CATEGORY
from ui.screen_utils import safe_getattr

if TYPE_CHECKING:
    from engine.core.game import Game
    from systems.inventory import Inventory


def _sort_items_by_type(item_ids: List[str]) -> List[str]:
    """
    Sort items by type: consumables first, then weapons, armor pieces, and accessories.
    Within each category, maintain original order.
    """
    # Define category order (lower number = appears first)
    # Grouping: consumables, weapons, armor pieces (helmet/armor/gloves/boots), 
    # shields, accessories (cloak/ring/amulet), then others
    category_order = {
        "consumable": 0,
        "weapon": 1,
        "helmet": 2,
        "armor": 3,
        "gloves": 4,
        "boots": 5,
        "shield": 6,
        "cloak": 7,
        "ring": 8,
        "amulet": 9,
    }
    
    def get_sort_key(item_id: str):
        item_def = get_item_def(item_id)
        if item_def is None:
            return (999, item_id)  # Unknown items go last
        slot = item_def.slot.lower()
        category = category_order.get(slot, 999)
        return (category, item_id)
    
    return sorted(item_ids, key=get_sort_key)


def _get_category_name(slot: str) -> str:
    """Get display name for item category."""
    category_names = {
        "consumable": "Consumables",
        "weapon": "Weapons",
        "helmet": "Helmets",
        "armor": "Armor",
        "gloves": "Gloves",
        "boots": "Boots",
        "shield": "Shields",
        "cloak": "Cloaks",
        "ring": "Rings",
        "amulet": "Amulets",
    }
    return category_names.get(slot.lower(), "Other")


def draw_shop_fullscreen(game: "Game") -> None:
    """Full-screen shop view."""
    screen = game.screen
    ui_font = game.ui_font
    w, h = screen.get_size()
    
    # Fill background
    screen.fill(COLOR_BG)
    
    # Get available screens for tabs (keep consistent across screens)
    available_screens = ["inventory", "character", "skills", "quests", "shop"]
    
    # Draw header with tabs
    draw_screen_header(screen, ui_font, "Dungeon Merchant", "shop", available_screens, w)
    
    mode = getattr(game, "shop_mode", "buy")
    mode_label = "BUY" if mode == "buy" else "SELL"
    
    gold_value = int(getattr(getattr(game, "hero_stats", None), "gold", 0))
    gold_line = ui_font.render(f"Your gold: {gold_value}", True, (230, 210, 120))
    screen.blit(gold_line, (40, 70))
    
    stock_buy: List[str] = list(getattr(game, "shop_stock", []))
    inv: Inventory | None = getattr(game, "inventory", None)
    cursor = int(getattr(game, "shop_cursor", 0))
    
    if mode == "buy":
        # Use sorted list if available, otherwise create and store it
        sorted_stock = getattr(game, "shop_stock_sorted", None)
        if sorted_stock is None:
            sorted_stock = _sort_items_by_type(stock_buy)
            game.shop_stock_sorted = sorted_stock
        active_list = sorted_stock
    else:
        if inv is None:
            active_list = []
        else:
            active_list = inv.get_sellable_item_ids()
    
    # Sort items by type (consumables first, then weapons, armor, trinkets)
    # For sell mode, also sort for consistency
    if mode == "sell":
        sorted_list = _sort_items_by_type(active_list)
    else:
        sorted_list = active_list
    
    # Left column: Buy list
    left_x = 40
    y = 110
    
    buy_title = ui_font.render(f"{mode_label} Items:", True, (220, 220, 180))
    screen.blit(buy_title, (left_x, y))
    y += 28
    
    if not sorted_list:
        msg_text = (
            "The merchant has nothing left to sell."
            if mode == "buy"
            else "You have nothing you're willing to sell."
        )
        msg = ui_font.render(msg_text, True, (190, 190, 190))
        screen.blit(msg, (left_x, y))
    else:
        max_items = len(sorted_list)
        line_height = 26
        if max_items > 0:
            cursor = max(0, min(cursor, max_items - 1))
        
        # Show more items in fullscreen
        visible_start = max(0, cursor - 10)
        visible_end = min(max_items, cursor + 15)
        visible_items = sorted_list[visible_start:visible_end]
        
        # Get floor index for economy calculations
        floor_index = getattr(game, "floor", 1)
        
        # Track current category to show headers
        last_category = None
        
        for i, item_id in enumerate(visible_items):
            actual_index = visible_start + i
            item_def = get_item_def(item_id)
            if item_def is None:
                name = item_id
                price = 0
                rarity = ""
                current_category = "Other"
            else:
                name = item_def.name
                rarity = getattr(item_def, "rarity", "")
                current_category = item_def.slot
                # Use economy system for dynamic pricing
                if mode == "buy":
                    price = calculate_shop_buy_price(item_def, floor_index)
                else:
                    price = calculate_shop_sell_price(item_def, floor_index)
            
            # Show category header when category changes
            if current_category != last_category and current_category:
                category_name = _get_category_name(current_category)
                # Add some spacing before category header
                if last_category is not None:
                    y += 4
                category_surf = ui_font.render(f"--- {category_name} ---", True, COLOR_CATEGORY)
                screen.blit(category_surf, (left_x, y))
                y += line_height
                last_category = current_category
            
            label = f"{actual_index + 1}) {name}"
            if rarity:
                label += f" [{rarity}]"
            
            price_str = f"{price}g" if mode == "buy" else f"{price}g (sell)"
            
            if actual_index == cursor:
                # Highlight selected item
                bg = pygame.Surface((w // 2 - 80, line_height), pygame.SRCALPHA)
                bg.fill((60, 60, 90, 210))
                screen.blit(bg, (left_x, y - 2))
                label_color = (255, 255, 200)
            else:
                label_color = (230, 230, 230)
            
            label_surf = ui_font.render(label, True, label_color)
            screen.blit(label_surf, (left_x + 20, y))
            
            price_surf = ui_font.render(price_str, True, (230, 210, 120))
            screen.blit(price_surf, (left_x + w // 2 - 200, y))
            
            y += line_height
        
        # Right column: detailed info for currently selected item
        if 0 <= cursor < max_items:
            info_x = w // 2 + 40
            info_y = 110

            selected_id = sorted_list[cursor]
            selected_def = get_item_def(selected_id)

            if selected_def is not None:
                info_title = ui_font.render("Item Info:", True, (220, 220, 180))
                screen.blit(info_title, (info_x, info_y))
                info_y += 26

                # Name + rarity
                rarity = getattr(selected_def, "rarity", "")
                if rarity:
                    name_line = f"{selected_def.name} [{rarity}]"
                else:
                    name_line = selected_def.name
                name_surf = ui_font.render(name_line, True, (235, 235, 220))
                screen.blit(name_surf, (info_x, info_y))
                info_y += 24

                # Stats + optional description (shown only for the selected item)
                info_line = build_item_info_line(selected_def, include_description=True)
                if info_line:
                    info_surf = ui_font.render(info_line, True, (190, 190, 190))
                    screen.blit(info_surf, (info_x, info_y))
    
    # Footer hints
    if mode == "buy":
        hints = [
            "Up/Down: move • Enter/Space: buy • 1–9: quick buy",
            "Shift+TAB: switch to SELL • TAB: switch screen • I/C: jump to screen • ESC: close"
        ]
    else:
        hints = [
            "Up/Down: move • Enter/Space: sell • 1–9: quick sell",
            "Shift+TAB: switch to BUY • TAB: switch screen • I/C: jump to screen • ESC: close"
        ]
    draw_screen_footer(screen, ui_font, hints, w, h)

