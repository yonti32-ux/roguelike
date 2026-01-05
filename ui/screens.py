"""Lightweight screen / overlay system for modal UI/overlays.

This module contains screen controllers for various UI overlays:
- Inventory screen
- Character sheet screen  
- Shop screen

Each screen owns its own input-handling + drawing, and Game forwards
events/draw calls to the active screen when appropriate.
"""

from __future__ import annotations

from typing import Optional, Protocol, TYPE_CHECKING

import pygame

from ui.hud import (
    draw_inventory_overlay,
    _draw_character_sheet,
    draw_shop_overlay,
)
from systems.input import InputAction

if TYPE_CHECKING:
    from engine.game import Game


class BaseScreen(Protocol):
    """Protocol for simple modal/overlay screens."""

    def handle_event(self, game: "Game", event: pygame.event.Event) -> None:
        ...

    def draw(self, game: "Game") -> None:
        ...


class InventoryScreen:
    """
    Screen wrapper for the inventory/equipment overlay.

    This delegates all rendering to hud.draw_inventory_overlay and centralises
    the input logic for:
      - closing the overlay (I / ESC)
      - cycling focused character (Q / E)
      - equipping items via number keys 1–9
    """

    def handle_event(self, game: "Game", event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return

        input_manager = getattr(game, "input_manager", None)
        key = event.key

        # Close inventory overlay (I or ESC)
        should_close = False
        if input_manager is not None:
            if (
                    input_manager.event_matches_action(InputAction.TOGGLE_INVENTORY, event)
                    or input_manager.event_matches_action(InputAction.CANCEL, event)
            ):
                should_close = True
        else:
            if key in (pygame.K_ESCAPE, pygame.K_i):
                should_close = True

        if should_close:
            # Use the game helper so open/close semantics stay centralised.
            game.toggle_inventory_overlay()
            # If the inventory screen no longer owns focus, release it.
            if not game.show_inventory and getattr(game, "active_screen", None) is self:
                game.active_screen = None
            return

        # Cycle focus between hero and companions (Q / E)
        if input_manager is not None:
            if input_manager.event_matches_action(InputAction.FOCUS_PREV, event):
                game.cycle_inventory_focus(-1)
                return
            if input_manager.event_matches_action(InputAction.FOCUS_NEXT, event):
                game.cycle_inventory_focus(+1)
                return
        else:
            if key == pygame.K_q:
                game.cycle_inventory_focus(-1)
                return
            if key == pygame.K_e:
                game.cycle_inventory_focus(+1)
                return

        # Inventory scrolling: arrow keys / W/S for line scroll,
        # PageUp/PageDown for paging by a full screen.
        inventory = getattr(game, "inventory", None)
        if inventory is None:
            return

        items = list(getattr(inventory, "items", []))
        total_items = len(items)
        page_size = getattr(game, "inventory_page_size", 10)
        offset = getattr(game, "inventory_scroll_offset", 0)

        # Normalise offset in case inventory size changed.
        if total_items <= page_size:
            offset = 0
        else:
            max_offset = max(0, total_items - page_size)
            if offset < 0:
                offset = 0
            elif offset > max_offset:
                offset = max_offset
        game.inventory_scroll_offset = offset

        # Line scroll (up / down)
        if input_manager is not None:
            if input_manager.event_matches_action(InputAction.SCROLL_UP, event):
                if total_items > 0:
                    offset = max(0, offset - 1)
                    game.inventory_scroll_offset = offset
                return
            if input_manager.event_matches_action(InputAction.SCROLL_DOWN, event):
                if total_items > 0:
                    max_offset = max(0, total_items - page_size)
                    offset = min(max_offset, offset + 1)
                    game.inventory_scroll_offset = offset
                return
        else:
            if key in (pygame.K_UP, pygame.K_w):
                if total_items > 0:
                    offset = max(0, offset - 1)
                    game.inventory_scroll_offset = offset
                return
            if key in (pygame.K_DOWN, pygame.K_s):
                if total_items > 0:
                    max_offset = max(0, total_items - page_size)
                    offset = min(max_offset, offset + 1)
                    game.inventory_scroll_offset = offset
                return

        # Page scroll
        if input_manager is not None:
            if input_manager.event_matches_action(InputAction.PAGE_UP, event):
                if total_items > 0:
                    offset = max(0, offset - page_size)
                    game.inventory_scroll_offset = offset
                return
            if input_manager.event_matches_action(InputAction.PAGE_DOWN, event):
                if total_items > 0:
                    max_offset = max(0, total_items - page_size)
                    offset = min(max_offset, offset + page_size)
                    game.inventory_scroll_offset = offset
                return
        else:
            if key == pygame.K_PAGEUP:
                if total_items > 0:
                    offset = max(0, offset - page_size)
                    game.inventory_scroll_offset = offset
                return
            if key == pygame.K_PAGEDOWN:
                if total_items > 0:
                    max_offset = max(0, total_items - page_size)
                    offset = min(max_offset, offset + page_size)
                    game.inventory_scroll_offset = offset
                return

        # Equipping via 1–9 keys on the *current page* (unchanged)
        index: Optional[int] = None
        if key in (pygame.K_1, pygame.K_KP1):
            index = 0
        elif key in (pygame.K_2, pygame.K_KP2):
            index = 1
        elif key in (pygame.K_3, pygame.K_KP3):
            index = 2
        elif key in (pygame.K_4, pygame.K_KP4):
            index = 3
        elif key in (pygame.K_5, pygame.K_KP5):
            index = 4
        elif key in (pygame.K_6, pygame.K_KP6):
            index = 5
        elif key in (pygame.K_7, pygame.K_KP7):
            index = 6
        elif key in (pygame.K_8, pygame.K_KP8):
            index = 7
        elif key in (pygame.K_9, pygame.K_KP9):
            index = 8

        if index is None:
            return

        if not items:
            return

        # Recompute/clamp offset before indexing, in case inventory changed.
        total_items = len(items)
        page_size = getattr(game, "inventory_page_size", 10)
        offset = getattr(game, "inventory_scroll_offset", 0)
        if total_items <= page_size:
            offset = 0
        else:
            max_offset = max(0, total_items - page_size)
            if offset < 0:
                offset = 0
            elif offset > max_offset:
                offset = max_offset
        game.inventory_scroll_offset = offset

        visible_items = items[offset:offset + page_size]
        if not (0 <= index < len(visible_items)):
            return

        item_id = visible_items[index]
        # Delegate actual equip logic (hero vs companion) to the Game helper.
        game.equip_item_for_inventory_focus(item_id)

    def draw(self, game: "Game") -> None:
        """Render the inventory/equipment overlay."""
        draw_inventory_overlay(game)


class CharacterSheetScreen:
    """
    Screen wrapper for the character sheet overlay.

    Delegates drawing to hud._draw_character_sheet, and owns the basic input:
      - closing (C / ESC)
      - cycling focused character (Q / E)
    """

    def handle_event(self, game: "Game", event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return

        input_manager = getattr(game, "input_manager", None)
        key = event.key

        # Close character sheet (C or ESC)
        should_close = False
        if input_manager is not None:
            if (
                    input_manager.event_matches_action(InputAction.TOGGLE_CHARACTER_SHEET, event)
                    or input_manager.event_matches_action(InputAction.CANCEL, event)
            ):
                should_close = True
        else:
            if key in (pygame.K_ESCAPE, pygame.K_c):
                should_close = True

        if should_close:
            game.toggle_character_sheet_overlay()
            if not game.show_character_sheet and getattr(game, "active_screen", None) is self:
                game.active_screen = None
            return

        # Cycle focus between hero and companions (Q / E)
        if input_manager is not None:
            if input_manager.event_matches_action(InputAction.FOCUS_PREV, event):
                game.cycle_character_sheet_focus(-1)
                return
            if input_manager.event_matches_action(InputAction.FOCUS_NEXT, event):
                game.cycle_character_sheet_focus(+1)
                return
        else:
            if key == pygame.K_q:
                game.cycle_character_sheet_focus(-1)
            elif key == pygame.K_e:
                game.cycle_character_sheet_focus(+1)

    def draw(self, game: "Game") -> None:
        """Render the character sheet overlay."""
        _draw_character_sheet(game)

class ShopScreen(BaseScreen):
    """Blocking screen wrapper for the merchant/shop overlay.

    Rendering is handled by hud.draw_shop_overlay; this class owns the input:
      - navigation (arrows / W/S / J/K)
      - switching between buy/sell (TAB)
      - buying/selling via number keys or Enter/Space
      - closing (ESC, E, I, C)
    """

    def handle_event(self, game: "Game", event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return

        # If the flag is off for some reason, ignore input.
        if not getattr(game, "show_shop", False):
            return

        input_manager = getattr(game, "input_manager", None)
        key = event.key
        mode = getattr(game, "shop_mode", "buy")  # "buy" or "sell"

        # --- Close shop ---
        should_close = False
        if input_manager is not None:
            if (
                    input_manager.event_matches_action(InputAction.CANCEL, event)
                    or input_manager.event_matches_action(InputAction.INTERACT, event)
                    or input_manager.event_matches_action(InputAction.TOGGLE_INVENTORY, event)
                    or input_manager.event_matches_action(InputAction.TOGGLE_CHARACTER_SHEET, event)
            ):
                should_close = True
        else:
            if key in (
                    pygame.K_ESCAPE,
                    pygame.K_e,
                    pygame.K_i,
                    pygame.K_c,
            ):
                should_close = True

        if should_close:
            game.show_shop = False
            # If this screen owns focus, release it.
            if getattr(game, "active_screen", None) is getattr(game, "shop_screen", None):
                game.active_screen = None
            return

        # --- Toggle between buy / sell ---
        if key == pygame.K_TAB:
            game.shop_mode = "sell" if mode == "buy" else "buy"
            game.shop_cursor = 0
            return

        # --- Build active list (copied from ExplorationController._handle_shop_key) ---
        stock_buy = list(getattr(game, "shop_stock", []))
        inv = getattr(game, "inventory", None)

        if mode == "buy":
            active_list = stock_buy
        else:
            if inv is None:
                active_list = []
            else:
                active_list = inv.get_sellable_item_ids()

        # Nothing to show: keep overlay, just show message on Enter/Space.
        if not active_list:
            if input_manager is not None:
                if input_manager.event_matches_action(InputAction.CONFIRM, event):
                    if mode == "buy":
                        game.last_message = "The merchant has nothing left to sell."
                    else:
                        game.last_message = "You have nothing you're willing to sell."
            else:
                if key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
                    if mode == "buy":
                        game.last_message = "The merchant has nothing left to sell."
                    else:
                        game.last_message = "You have nothing you're willing to sell."
            return

        # --- Ensure cursor is valid ---
        cursor = int(getattr(game, "shop_cursor", 0))
        max_index = len(active_list) - 1

        if max_index < 0:
            game.shop_cursor = 0
        else:
            cursor = max(0, min(cursor, max_index))
            game.shop_cursor = cursor

        # --- Navigation (UP/W/K and DOWN/S/J) ---
        if input_manager is not None:
            if input_manager.event_matches_action(InputAction.SCROLL_UP, event):
                if max_index >= 0:
                    cursor = (cursor - 1) % (max_index + 1)
                    game.shop_cursor = cursor
                return
            if input_manager.event_matches_action(InputAction.SCROLL_DOWN, event):
                if max_index >= 0:
                    cursor = (cursor + 1) % (max_index + 1)
                    game.shop_cursor = cursor
                return
        else:
            if key in (pygame.K_UP, pygame.K_w, pygame.K_k):
                if max_index >= 0:
                    cursor = (cursor - 1) % (max_index + 1)
                    game.shop_cursor = cursor
                return

            if key in (pygame.K_DOWN, pygame.K_s, pygame.K_j):
                if max_index >= 0:
                    cursor = (cursor + 1) % (max_index + 1)
                    game.shop_cursor = cursor
                return

        # --- Quick buy/sell with number keys 1–9 ---
        index_from_number: Optional[int] = None
        if key in (pygame.K_1, pygame.K_KP1):
            index_from_number = 0
        elif key in (pygame.K_2, pygame.K_KP2):
            index_from_number = 1
        elif key in (pygame.K_3, pygame.K_KP3):
            index_from_number = 2
        elif key in (pygame.K_4, pygame.K_KP4):
            index_from_number = 3
        elif key in (pygame.K_5, pygame.K_KP5):
            index_from_number = 4
        elif key in (pygame.K_6, pygame.K_KP6):
            index_from_number = 5
        elif key in (pygame.K_7, pygame.K_KP7):
            index_from_number = 6
        elif key in (pygame.K_8, pygame.K_KP8):
            index_from_number = 7
        elif key in (pygame.K_9, pygame.K_KP9):
            index_from_number = 8

        if index_from_number is not None:
            if 0 <= index_from_number < len(active_list):
                exploration = getattr(game, "exploration", None)
                if exploration is not None:
                    if mode == "buy":
                        exploration._attempt_shop_purchase(index_from_number)
                    else:
                        exploration._attempt_shop_sell(index_from_number)
            return

        # --- Enter/Space to buy/sell currently highlighted item ---
        if input_manager is not None:
            if input_manager.event_matches_action(InputAction.CONFIRM, event):
                if 0 <= cursor < len(active_list):
                    exploration = getattr(game, "exploration", None)
                    if exploration is not None:
                        if mode == "buy":
                            exploration._attempt_shop_purchase(cursor)
                        else:
                            exploration._attempt_shop_sell(cursor)
                return
        else:
            if key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                if 0 <= cursor < len(active_list):
                    exploration = getattr(game, "exploration", None)
                    if exploration is not None:
                        if mode == "buy":
                            exploration._attempt_shop_purchase(cursor)
                        else:
                            exploration._attempt_shop_sell(cursor)
                return

    def draw(self, game: "Game") -> None:
        draw_shop_overlay(game)
