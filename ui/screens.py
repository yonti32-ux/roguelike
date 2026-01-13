"""Lightweight screen / overlay system for modal UI/overlays.

This module contains screen controllers for various UI overlays:
- Inventory screen
- Character sheet screen  
- Shop screen

Each screen owns its own input-handling + drawing, and Game forwards
events/draw calls to the active screen when appropriate.
"""

from __future__ import annotations

from typing import Optional, Protocol, TYPE_CHECKING, Dict, List, Tuple

import pygame

from ui.hud_screens import (
    draw_inventory_fullscreen,
    draw_character_sheet_fullscreen,
    draw_shop_fullscreen,
    draw_skill_screen_fullscreen,
    draw_recruitment_fullscreen,
    draw_quest_fullscreen,
    _process_inventory_items,
)
from systems.input import InputAction

if TYPE_CHECKING:
    from engine.core.game import Game


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
        # Handle mouse events for tooltips
        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            # Check if mouse is over an item (this will be handled in draw_inventory_fullscreen)
            game.tooltip.mouse_pos = (mx, my)
            return
        
        if event.type != pygame.KEYDOWN:
            return

        input_manager = getattr(game, "input_manager", None)
        key = event.key

        # Screen switching with TAB (before close check)
        if key == pygame.K_TAB:
            # Check if shift is held for reverse direction
            mods = pygame.key.get_mods()
            direction = -1 if (mods & pygame.KMOD_SHIFT) else 1
            game.cycle_to_next_screen(direction)
            return
        
        # Quick jump to screens
        if key == pygame.K_c:
            game.switch_to_screen("character")
            return
        if key == pygame.K_s and getattr(game, "show_shop", False):
            game.switch_to_screen("shop")
            return
        
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

        # Get inventory and process items using the same logic as the draw function
        inventory = getattr(game, "inventory", None)
        if inventory is None:
            return

        from ui.inventory_enhancements import FilterMode, SortMode
        from systems.inventory import get_item_def
        
        # Use the same processing logic as the draw function to ensure alignment
        filter_mode = getattr(game, "inventory_filter", FilterMode.ALL)
        sort_mode = getattr(game, "inventory_sort", SortMode.DEFAULT)
        search_query = getattr(game, "inventory_search", "") or ""
        
        processed = _process_inventory_items(inventory, game, filter_mode, sort_mode, search_query)
        flat_list = processed.flat_list
        item_indices = processed.item_indices
        
        cursor = getattr(game, "inventory_cursor", 0)
        page_size = getattr(game, "inventory_page_size", 20)
        
        if not item_indices:
            return
        
        # Clamp cursor to valid range
        cursor = max(0, min(cursor, len(item_indices) - 1))
        game.inventory_cursor = cursor
        
        # Cursor navigation (up / down)
        if input_manager is not None:
            if input_manager.event_matches_action(InputAction.SCROLL_UP, event):
                if cursor > 0:
                    game.inventory_cursor = cursor - 1
                return
            if input_manager.event_matches_action(InputAction.SCROLL_DOWN, event):
                if cursor < len(item_indices) - 1:
                    game.inventory_cursor = cursor + 1
                return
        else:
            if key in (pygame.K_UP, pygame.K_w):
                if cursor > 0:
                    game.inventory_cursor = cursor - 1
                return
            if key in (pygame.K_DOWN, pygame.K_s):
                if cursor < len(item_indices) - 1:
                    game.inventory_cursor = cursor + 1
                return

        # Page scroll (move cursor by page_size)
        if input_manager is not None:
            if input_manager.event_matches_action(InputAction.PAGE_UP, event):
                game.inventory_cursor = max(0, cursor - page_size)
                return
            if input_manager.event_matches_action(InputAction.PAGE_DOWN, event):
                game.inventory_cursor = min(len(item_indices) - 1, cursor + page_size)
                return
        else:
            if key == pygame.K_PAGEUP:
                game.inventory_cursor = max(0, cursor - page_size)
                return
            if key == pygame.K_PAGEDOWN:
                game.inventory_cursor = min(len(item_indices) - 1, cursor + page_size)
                return

        # Filter shortcuts (F1-F7)
        from ui.inventory_enhancements import FilterMode
        if key == pygame.K_F1:
            game.inventory_filter = FilterMode.ALL
            game.inventory_cursor = 0
            return
        elif key == pygame.K_F2:
            game.inventory_filter = FilterMode.WEAPON
            game.inventory_cursor = 0
            return
        elif key == pygame.K_F3:
            game.inventory_filter = FilterMode.ARMOR
            game.inventory_cursor = 0
            return
        elif key == pygame.K_F4:
            game.inventory_filter = FilterMode.TRINKET
            game.inventory_cursor = 0
            return
        elif key == pygame.K_F5:
            game.inventory_filter = FilterMode.CONSUMABLE
            game.inventory_cursor = 0
            return
        elif key == pygame.K_F6:
            game.inventory_filter = FilterMode.EQUIPPED
            game.inventory_cursor = 0
            return
        elif key == pygame.K_F7:
            game.inventory_filter = FilterMode.UNEQUIPPED
            game.inventory_cursor = 0
            return
        
        # Sort shortcuts (Ctrl+S cycles through sort modes)
        from ui.inventory_enhancements import SortMode
        mods = pygame.key.get_mods()
        if key == pygame.K_s and (mods & pygame.KMOD_CTRL):
            # Cycle through sort modes
            sort_modes = [
                SortMode.DEFAULT,
                SortMode.NAME,
                SortMode.RARITY,
                SortMode.ATTACK,
                SortMode.DEFENSE,
                SortMode.HP,
            ]
            current_index = sort_modes.index(game.inventory_sort) if game.inventory_sort in sort_modes else 0
            next_index = (current_index + 1) % len(sort_modes)
            game.inventory_sort = sort_modes[next_index]
            game.inventory_cursor = 0
            return
        
        # Search mode toggle (Ctrl+F to start typing search query)
        if key == pygame.K_f and (mods & pygame.KMOD_CTRL):
            # Toggle search mode - for now just clear search
            # In a full implementation, you'd enter a text input mode
            game.inventory_search = ""
            game.inventory_cursor = 0
            return
        
        # Clear filter/sort/search (Ctrl+R)
        if key == pygame.K_r and (mods & pygame.KMOD_CTRL):
            game.inventory_filter = FilterMode.ALL
            game.inventory_sort = SortMode.DEFAULT
            game.inventory_search = ""
            game.inventory_cursor = 0
            return
        
        # Handle text input for search (when not a special key)
        if game.inventory_search is not None:
            # Simple search: type to search, backspace to clear
            if key == pygame.K_BACKSPACE:
                game.inventory_search = game.inventory_search[:-1] if game.inventory_search else ""
                game.inventory_cursor = 0
                return
            elif 32 <= key <= 126:  # Printable ASCII
                char = chr(key)
                if not (mods & (pygame.KMOD_CTRL | pygame.KMOD_ALT | pygame.KMOD_META)):
                    game.inventory_search = (game.inventory_search or "") + char
                    game.inventory_cursor = 0
                    return
        
        # Equip or use selected item with Enter/Space
        if input_manager is not None:
            if input_manager.event_matches_action(InputAction.CONFIRM, event):
                if 0 <= cursor < len(item_indices):
                    item_id = flat_list[item_indices[cursor]][0]
                    if item_id:
                        item_def = get_item_def(item_id)
                        if item_def is not None and item_def.slot == "consumable":
                            # Use consumable instead of equipping it.
                            if hasattr(game, "use_consumable_from_inventory"):
                                game.use_consumable_from_inventory(item_id)
                        else:
                            game.equip_item_for_inventory_focus(item_id)
                return
        else:
            if key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
                if 0 <= cursor < len(item_indices):
                    item_id = flat_list[item_indices[cursor]][0]
                    if item_id:
                        item_def = get_item_def(item_id)
                        if item_def is not None and item_def.slot == "consumable":
                            if hasattr(game, "use_consumable_from_inventory"):
                                game.use_consumable_from_inventory(item_id)
                        else:
                            game.equip_item_for_inventory_focus(item_id)
                return

    def draw(self, game: "Game") -> None:
        """Render the full-screen inventory view."""
        draw_inventory_fullscreen(game)


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

        # Screen switching with TAB (before close check)
        if key == pygame.K_TAB:
            # Check if shift is held for reverse direction
            mods = pygame.key.get_mods()
            direction = -1 if (mods & pygame.KMOD_SHIFT) else 1
            game.cycle_to_next_screen(direction)
            return
        
        # Quick jump to screens
        if key == pygame.K_i:
            game.switch_to_screen("inventory")
            return
        if key == pygame.K_s and getattr(game, "show_shop", False):
            game.switch_to_screen("shop")
            return
        
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
        """Render the full-screen character sheet view."""
        draw_character_sheet_fullscreen(game)

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

        # --- Screen switching with TAB (only if not holding modifier) ---
        # Check modifiers - if no modifier, switch screens; if shift, switch buy/sell
        mods = pygame.key.get_mods()
        if key == pygame.K_TAB:
            if mods & pygame.KMOD_SHIFT:
                # Shift+TAB: Toggle between buy / sell
                game.shop_mode = "sell" if mode == "buy" else "buy"
                game.shop_cursor = 0
            else:
                # TAB: Switch to next screen
                game.cycle_to_next_screen(1)
            return
        
        # Quick jump to screens
        if key == pygame.K_i:
            game.switch_to_screen("inventory")
            return
        if key == pygame.K_c:
            game.switch_to_screen("character")
            return

        # --- Build active list (copied from ExplorationController._handle_shop_key) ---
        stock_buy = list(getattr(game, "shop_stock", []))
        inv = getattr(game, "inventory", None)

        if mode == "buy":
            # Sort items by type for better organization
            from ui.hud_screens import _sort_items_by_type
            active_list = _sort_items_by_type(stock_buy)
            # Store sorted list so purchase function can use it
            game.shop_stock_sorted = active_list
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
        """Render the full-screen shop view."""
        draw_shop_fullscreen(game)


class SkillScreen(BaseScreen):
    """
    Screen wrapper for the skill allocation overlay.
    
    Delegates drawing to hud.draw_skill_screen_fullscreen, and owns the input:
      - closing (T / ESC)
      - cycling focused character (Q / E)
      - skill tree navigation and upgrades
    """

    def handle_event(self, game: "Game", event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            # Handle mouse events for skill tree interaction
            skill_screen_core = getattr(game, "skill_screen", None)
            if skill_screen_core is not None:
                # Mouse click support
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        mx, my = event.pos
                        clicked_skill_id = skill_screen_core.get_node_at_screen_pos(
                            mx, my, game.screen.get_width(), game.screen.get_height()
                        )
                        if clicked_skill_id:
                            skill_screen_core.selected_skill_id = clicked_skill_id
                    elif event.button == 4:  # Mouse wheel up
                        skill_screen_core.zoom = min(2.0, skill_screen_core.zoom * 1.1)
                    elif event.button == 5:  # Mouse wheel down
                        skill_screen_core.zoom = max(0.5, skill_screen_core.zoom / 1.1)
            return

        input_manager = getattr(game, "input_manager", None)
        key = event.key
        skill_screen_core = getattr(game, "skill_screen", None)

        # Screen switching with TAB (before close check)
        if key == pygame.K_TAB:
            # Check if shift is held for reverse direction
            mods = pygame.key.get_mods()
            direction = -1 if (mods & pygame.KMOD_SHIFT) else 1
            game.cycle_to_next_screen(direction)
            return
        
        # Quick jump to screens
        if key == pygame.K_i:
            game.switch_to_screen("inventory")
            return
        if key == pygame.K_c:
            game.switch_to_screen("character")
            return
        if key == pygame.K_s and getattr(game, "show_shop", False):
            game.switch_to_screen("shop")
            return

        # Close skill screen (T or ESC)
        should_close = False
        if input_manager is not None:
            if input_manager.event_matches_action(InputAction.CANCEL, event):
                should_close = True
        else:
            if key in (pygame.K_ESCAPE, pygame.K_t):
                should_close = True

        if should_close:
            game.toggle_skill_screen()
            if not getattr(game, "show_skill_screen", False) and getattr(game, "active_screen", None) is self:
                game.active_screen = None
            return

        if skill_screen_core is None:
            return

        # Switch character with Q/E
        if input_manager is not None:
            if input_manager.event_matches_action(InputAction.FOCUS_PREV, event):
                party_list = getattr(game, "party", None) or []
                total_slots = 1 + len(party_list)
                if total_slots > 1:
                    skill_screen_core.focus_index = (skill_screen_core.focus_index - 1) % total_slots
                    skill_screen_core.selected_skill_id = None
                    skill_screen_core._cached_unlocked_skills = None  # Invalidate cache
                return
            if input_manager.event_matches_action(InputAction.FOCUS_NEXT, event):
                party_list = getattr(game, "party", None) or []
                total_slots = 1 + len(party_list)
                if total_slots > 1:
                    skill_screen_core.focus_index = (skill_screen_core.focus_index + 1) % total_slots
                    skill_screen_core.selected_skill_id = None
                    skill_screen_core._cached_unlocked_skills = None  # Invalidate cache
                return
        else:
            if key == pygame.K_q:
                party_list = getattr(game, "party", None) or []
                total_slots = 1 + len(party_list)
                if total_slots > 1:
                    skill_screen_core.focus_index = (skill_screen_core.focus_index - 1) % total_slots
                    skill_screen_core.selected_skill_id = None
                    skill_screen_core._cached_unlocked_skills = None  # Invalidate cache
                return
            elif key == pygame.K_e:
                party_list = getattr(game, "party", None) or []
                total_slots = 1 + len(party_list)
                if total_slots > 1:
                    skill_screen_core.focus_index = (skill_screen_core.focus_index + 1) % total_slots
                    skill_screen_core.selected_skill_id = None
                    skill_screen_core._cached_unlocked_skills = None  # Invalidate cache
                return

        # Panning with arrow keys
        pan_speed = 20.0
        if key == pygame.K_LEFT or key == pygame.K_a:
            skill_screen_core.camera_x -= pan_speed / skill_screen_core.zoom
        elif key == pygame.K_RIGHT or key == pygame.K_d:
            skill_screen_core.camera_x += pan_speed / skill_screen_core.zoom
        elif key == pygame.K_UP or key == pygame.K_w:
            skill_screen_core.camera_y -= pan_speed / skill_screen_core.zoom
        elif key == pygame.K_DOWN or key == pygame.K_s:
            skill_screen_core.camera_y += pan_speed / skill_screen_core.zoom

        # Zoom with +/- or mouse wheel
        if key == pygame.K_PLUS or key == pygame.K_EQUALS:
            skill_screen_core.zoom = min(2.0, skill_screen_core.zoom * 1.1)
        elif key == pygame.K_MINUS:
            skill_screen_core.zoom = max(0.5, skill_screen_core.zoom / 1.1)

        # Upgrade selected skill with Enter/Space
        if input_manager is not None:
            if input_manager.event_matches_action(InputAction.CONFIRM, event):
                if skill_screen_core.selected_skill_id:
                    if skill_screen_core.can_upgrade_skill(skill_screen_core.selected_skill_id):
                        if skill_screen_core.upgrade_skill(skill_screen_core.selected_skill_id):
                            # Refresh cache and update rank
                            skill_screen_core._cached_unlocked_skills = None
                            if skill_screen_core.tree_layout and skill_screen_core.selected_skill_id in skill_screen_core.tree_layout.nodes:
                                skill_screen_core.tree_layout.nodes[skill_screen_core.selected_skill_id].rank = skill_screen_core.get_skill_rank(skill_screen_core.selected_skill_id)
                            game.add_message(f"Upgraded skill!")
        else:
            if key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
                if skill_screen_core.selected_skill_id:
                    if skill_screen_core.can_upgrade_skill(skill_screen_core.selected_skill_id):
                        if skill_screen_core.upgrade_skill(skill_screen_core.selected_skill_id):
                            # Refresh cache and update rank
                            skill_screen_core._cached_unlocked_skills = None
                            if skill_screen_core.tree_layout and skill_screen_core.selected_skill_id in skill_screen_core.tree_layout.nodes:
                                skill_screen_core.tree_layout.nodes[skill_screen_core.selected_skill_id].rank = skill_screen_core.get_skill_rank(skill_screen_core.selected_skill_id)
                            game.add_message(f"Upgraded skill!")

    def draw(self, game: "Game") -> None:
        """Render the full-screen skill allocation view."""
        draw_skill_screen_fullscreen(game)
