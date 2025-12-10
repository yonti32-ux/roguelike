from __future__ import annotations

from typing import TYPE_CHECKING, Optional
import random

import pygame

from settings import TILE_SIZE
from world.entities import Enemy, Chest
from world.entities import EventNode  # NEW
from world.entities import Merchant  # NEW merchant NPC
from world.ai import update_enemy_ai  # NEW: centralised enemy AI
from systems.inventory import get_item_def
from systems.loot import roll_chest_loot, get_shop_stock_for_floor
from systems.events import get_event_def, EventResult  # NEW

from systems.input import InputAction



if TYPE_CHECKING:
    # Only imported for type hints, to avoid circular imports at runtime
    from engine.game import Game


class ExplorationController:
    """
    Owns the exploration phase rules:
    - Keyboard input (movement, overlays, interaction)
    - Player movement & collisions
    - Enemy AI & battle triggers (delegates to world.ai)
    - Chest interaction
    - Calling back into Game for floor transitions / battles
    """

    def __init__(self, game: "Game") -> None:
        self.game = game

    # ---------------------------------------------------------------------
    # Public API used by Game
    # ---------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle input while in exploration mode."""
        game = self.game

        if event.type != pygame.KEYDOWN:
            return

        input_manager = getattr(game, "input_manager", None)

        # --- Shop overlay is open: handle shop input first (legacy fallback) ---
        # Normally, when the ShopScreen is active it will consume input via Game.handle_event.
        if getattr(game, "show_shop", False):
            self._handle_shop_key(event)
            return

        # --- Blocking UI overlays ---
        # While these are open, their screens receive input via Game.handle_event,
        # so exploration has nothing to do here.
        if getattr(game, "show_inventory", False) or getattr(game, "show_character_sheet", False):
            return

        # --- Normal exploration input (overlays closed) ---

        # Toggle inventory
        if input_manager is not None:
            if input_manager.event_matches_action(InputAction.TOGGLE_INVENTORY, event):
                game.toggle_inventory_overlay()
                return
        else:
            if event.key == pygame.K_i:
                game.toggle_inventory_overlay()
                return

        # Toggle character sheet
        if input_manager is not None:
            if input_manager.event_matches_action(InputAction.TOGGLE_CHARACTER_SHEET, event):
                game.toggle_character_sheet_overlay()
                return
        else:
            if event.key == pygame.K_c:
                game.toggle_character_sheet_overlay()
                return

        # Zoom controls (exploration view) – still raw key based for now
        if event.key == pygame.K_z:
            # Zoom out
            if hasattr(game, "zoom_levels"):
                game.zoom_index = max(0, game.zoom_index - 1)
            return

        if event.key == pygame.K_x:
            # Zoom in
            if hasattr(game, "zoom_levels"):
                game.zoom_index = min(len(game.zoom_levels) - 1, game.zoom_index + 1)
            return

        # Toggle last battle log overlay
        if input_manager is not None:
            if input_manager.event_matches_action(InputAction.TOGGLE_BATTLE_LOG, event):
                game.toggle_battle_log_overlay()
                return
        else:
            if event.key == pygame.K_l:
                game.toggle_battle_log_overlay()
                return

        # Toggle exploration log overlay
        if input_manager is not None:
            if input_manager.event_matches_action(InputAction.TOGGLE_EXPLORATION_LOG, event):
                game.toggle_exploration_log_overlay()
                return
        else:
            if event.key == pygame.K_k:
                game.toggle_exploration_log_overlay()
                return

        # Interact (chest / event / merchant / etc.)
        if input_manager is not None:
            if input_manager.event_matches_action(InputAction.INTERACT, event):
                self.try_interact()
                return
        else:
            if event.key == pygame.K_e:
                self.try_interact()
                return

        # Stairs: go down / up (still raw for now)
        if event.key == pygame.K_PERIOD:  # '.'
            game.try_change_floor(+1)
            return

        if event.key == pygame.K_COMMA:  # ','
            game.try_change_floor(-1)
            return

    def update(self, dt: float) -> None:
        """Update exploration state (player movement, enemies, etc.)."""
        game = self.game

        if game.player is None or game.current_map is None:
            return

        # If an overlay is open, pause movement & enemy AI
        if game.show_character_sheet or game.show_inventory or getattr(game, "show_shop", False):
            return

        direction = pygame.Vector2(0, 0)
        input_manager = getattr(game, "input_manager", None)

        if input_manager is not None:
            # Logical movement via actions, so we can remap keys or support pads later.
            if input_manager.is_action_pressed(InputAction.MOVE_UP):
                direction.y -= 1
            if input_manager.is_action_pressed(InputAction.MOVE_DOWN):
                direction.y += 1
            if input_manager.is_action_pressed(InputAction.MOVE_LEFT):
                direction.x -= 1
            if input_manager.is_action_pressed(InputAction.MOVE_RIGHT):
                direction.x += 1
        else:
            # Fallback: direct key checks (legacy behaviour).
            keys = pygame.key.get_pressed()
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                direction.y -= 1
            if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                direction.y += 1
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                direction.x -= 1
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                direction.x += 1

        # Floor intro pause: wait until first movement input
        if getattr(game, "awaiting_floor_start", False):
            if direction.length_squared() == 0:
                # No movement input yet: don't move and don't update enemies
                return
            else:
                # First movement input on this floor: unpause
                game.awaiting_floor_start = False

        # --- Player movement & collision with enemies / merchants ---
        if direction.length_squared() > 0 and getattr(game.player, "hp", 1) > 0:
            direction = direction.normalize()

            move_vector = direction * game.player.speed * dt
            new_x = game.player.x + move_vector.x
            new_y = game.player.y + move_vector.y

            new_rect = pygame.Rect(
                int(new_x),
                int(new_y),
                game.player.width,
                game.player.height,
            )

            blocked_by_tiles = not game.current_map.rect_can_move_to(new_rect)

            # Enemies block movement; stepping into them triggers battle instead
            blocking_enemies: list[Enemy] = [
                e
                for e in game.current_map.entities
                if isinstance(e, Enemy)
                and getattr(e, "blocks_movement", True)
                and e.rect.colliderect(new_rect)
            ]

            # Merchants also block movement, but do NOT start battles
            blocking_merchants: list[Merchant] = [
                m
                for m in game.current_map.entities
                if isinstance(m, Merchant)
                and getattr(m, "blocks_movement", True)
                and m.rect.colliderect(new_rect)
            ]

            if not blocked_by_tiles and not blocking_enemies and not blocking_merchants:
                game.player.move_to(new_x, new_y)
            elif blocking_enemies:
                # During grace, you simply can't walk through them; no new battle yet
                if game.post_battle_grace <= 0.0:
                    game.start_battle(blocking_enemies[0])
            else:
                # Blocked by tiles or merchants only: do nothing (can't move through)
                pass

        # --- Enemy updates (delegated to world.ai) ---
        for entity in list(game.current_map.entities):
            if isinstance(entity, Enemy):
                update_enemy_ai(entity, game, dt)

    # ---------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------

    def _handle_shop_key(self, event: pygame.event.Event) -> None:
        """
        Handle key presses while the shop overlay is open.
        Supports BUY/SELL modes toggled with TAB.
        """
        game = self.game

        if not getattr(game, "show_shop", False):
            return

        mode = getattr(game, "shop_mode", "buy")

        # Close shop with ESC, E, I, or C
        if event.key in (pygame.K_ESCAPE, pygame.K_e, pygame.K_i, pygame.K_c):
            game.show_shop = False
            return

        # TAB: switch between buy / sell modes
        if event.key == pygame.K_TAB:
            game.shop_mode = "sell" if mode == "buy" else "buy"
            game.shop_cursor = 0
            return

        stock_buy: list[str] = list(getattr(game, "shop_stock", []))
        inv = getattr(game, "inventory", None)

        # Determine active list based on mode
        if mode == "buy":
            active_list = stock_buy
        else:
            if inv is None:
                active_list = []
            else:
                active_list = inv.get_sellable_item_ids()

        # If there's nothing to trade in this mode, allow confirmation keys
        # to give a soft message but keep the shop open so TAB is still usable.
        if not active_list:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                if mode == "buy":
                    game.last_message = "The merchant has nothing left to sell."
                else:
                    game.last_message = "You have nothing you're willing to sell."
            return

        # Ensure cursor is within range
        cursor = int(getattr(game, "shop_cursor", 0))
        max_index = len(active_list) - 1
        if max_index < 0:
            game.shop_cursor = 0
        else:
            cursor = max(0, min(cursor, max_index))
            game.shop_cursor = cursor

        # Navigate with arrows or W/S (and vim-like J/K)
        if event.key in (pygame.K_UP, pygame.K_w, pygame.K_k):
            if max_index >= 0:
                cursor = (cursor - 1) % (max_index + 1)
                game.shop_cursor = cursor
            return

        if event.key in (pygame.K_DOWN, pygame.K_s, pygame.K_j):
            if max_index >= 0:
                cursor = (cursor + 1) % (max_index + 1)
                game.shop_cursor = cursor
            return

        # Number keys 1–9: quick-buy/sell that line if present
        idx: Optional[int] = None
        if event.key in (pygame.K_1, pygame.K_KP1):
            idx = 0
        elif event.key in (pygame.K_2, pygame.K_KP2):
            idx = 1
        elif event.key in (pygame.K_3, pygame.K_KP3):
            idx = 2
        elif event.key in (pygame.K_4, pygame.K_KP4):
            idx = 3
        elif event.key in (pygame.K_5, pygame.K_KP5):
            idx = 4
        elif event.key in (pygame.K_6, pygame.K_KP6):
            idx = 5
        elif event.key in (pygame.K_7, pygame.K_KP7):
            idx = 6
        elif event.key in (pygame.K_8, pygame.K_KP8):
            idx = 7
        elif event.key in (pygame.K_9, pygame.K_KP9):
            idx = 8

        if idx is not None:
            if 0 <= idx < len(active_list):
                if mode == "buy":
                    self._attempt_shop_purchase(idx)
                else:
                    self._attempt_shop_sell(idx)
            return

        # Enter / Space confirms the currently selected item
        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            if 0 <= cursor < len(active_list):
                if mode == "buy":
                    self._attempt_shop_purchase(cursor)
                else:
                    self._attempt_shop_sell(cursor)
            return

    # --- Chest helpers ---------------------------------------------------

    def _find_chest_near_player(
        self,
        max_distance_px: int = TILE_SIZE // 2,
    ) -> Optional[Chest]:
        """
        Return a chest entity near/under the player, or None.
        """
        game = self.game

        if game.current_map is None or game.player is None:
            return None

        px, py = game.player.rect.center
        max_dist_sq = max_distance_px * max_distance_px

        for entity in getattr(game.current_map, "entities", []):
            if not isinstance(entity, Chest):
                continue
            cx, cy = entity.rect.center
            dx = cx - px
            dy = cy - py
            if dx * dx + dy * dy <= max_dist_sq:
                return entity

        return None

    def find_chest_near_player(self, max_distance_px: int) -> Optional[Chest]:
        """
        Public wrapper so UI code can query for nearby chests without
        knowing the details.
        """
        return self._find_chest_near_player(max_distance_px=max_distance_px)

    def try_open_chest(self) -> None:
        """
        Attempt to open a chest near the player when pressing the interaction key.
        Uses systems.loot.roll_chest_loot to determine rewards.
        """
        game = self.game

        # Ignore interaction while overlays are open
        if game.show_inventory or game.show_character_sheet:
            return

        if game.current_map is None or game.player is None or game.inventory is None:
            return

        chest = self._find_chest_near_player(max_distance_px=TILE_SIZE // 2)
        if chest is None:
            # Soft feedback, doesn't spam too hard
            game.last_message = "There is nothing here to open."
            return

        if getattr(chest, "opened", False):
            game.last_message = "The chest is empty."
            return

        # Mark as opened regardless of loot outcome
        chest.opened = True

        # Roll item loot first
        item_id = roll_chest_loot(game.floor)

        # Roll some gold for the chest as well
        # Floors deeper → more gold
        min_gold = 5 + game.floor
        max_gold = 10 + game.floor * 2
        gold_amount = random.randint(min_gold, max_gold)
        gained_gold = 0
        if hasattr(game.hero_stats, "add_gold"):
            gained_gold = game.hero_stats.add_gold(gold_amount)

        # Build message based on what we actually got
        if item_id is None:
            if gained_gold > 0:
                game.last_message = f"You open the chest and find {gained_gold} gold."
            else:
                game.last_message = "The chest is empty."
            return

        # Add item to inventory
        game.inventory.add_item(item_id)

        item_def = get_item_def(item_id)
        item_name = item_def.name if item_def is not None else item_id

        if gained_gold > 0:
            game.last_message = (
                f"You open the chest and find: {item_name} and {gained_gold} gold."
            )
        else:
            game.last_message = f"You open the chest and find: {item_name}."

        # Re-sync stats in case gear bonuses matter later (no full heal)
        if game.player is not None:
            game.apply_hero_stats_to_player(full_heal=False)

    # --- Event helpers ---------------------------------------------------

    def _find_event_near_player(
        self,
        max_distance_px: int = TILE_SIZE // 2,
    ) -> Optional["EventNode"]:
        """
        Return an event node near/under the player, or None.
        """
        game = self.game

        if game.current_map is None or game.player is None:
            return None

        px, py = game.player.rect.center
        max_dist_sq = max_distance_px * max_distance_px

        for entity in getattr(game.current_map, "entities", []):
            from world.entities import EventNode  # type: ignore
            if not isinstance(entity, EventNode):
                continue
            ex, ey = entity.rect.center
            dx = ex - px
            dy = ey - py
            if dx * dx + dy * dy <= max_dist_sq:
                return entity

        return None

    def find_event_near_player(self, max_distance_px: int) -> Optional["EventNode"]:
        """
        Public wrapper so UI / HUD code can query nearby events.
        """
        return self._find_event_near_player(max_distance_px=max_distance_px)

    def _trigger_event_node(self, node) -> None:
        """
        Resolve an event node: look up its EventDef, run handler, and
        update messages / stats. The node is consumed afterwards.
        """
        game = self.game

        from systems.events import get_event_def  # already imported at top, but safe
        event_def = get_event_def(node.event_id)
        if event_def is None:
            game.last_message = "Nothing happens."
            return

        # Run the event; handler applies XP/gold/changes directly to game.
        result = event_def.handler(game)

        # Compose a message – primary text from the event result.
        text = getattr(result, "text", None) or "Nothing happens."
        game.last_message = text

        # Re-sync player stats in case perks/stats changed (no full heal)
        if game.player is not None:
            game.apply_hero_stats_to_player(full_heal=False)

        # Consume the node: remove from the map
        if game.current_map is not None:
            try:
                game.current_map.entities.remove(node)
            except ValueError:
                pass

    # --- Merchant helpers ------------------------------------------------

    def _find_merchant_near_player(
        self,
        max_distance_px: int = TILE_SIZE // 2,
    ) -> Optional["Merchant"]:
        """
        Return a merchant entity near/under the player, or None.
        """
        game = self.game

        if game.current_map is None or game.player is None:
            return None

        px, py = game.player.rect.center
        max_dist_sq = max_distance_px * max_distance_px

        for entity in getattr(game.current_map, "entities", []):
            if not isinstance(entity, Merchant):
                continue
            mx, my = entity.rect.center
            dx = mx - px
            dy = my - py
            if dx * dx + dy * dy <= max_dist_sq:
                return entity

        return None

    def find_merchant_near_player(self, max_distance_px: int) -> Optional["Merchant"]:
        """
        Public wrapper so UI code can query nearby merchants if needed.
        """
        return self._find_merchant_near_player(max_distance_px=max_distance_px)

    def _open_shop(self) -> None:
        """
        Open the merchant shop overlay for the current floor, if available.
        """
        game = self.game

        # Don't reopen if already open
        if getattr(game, "show_shop", False):
            return

        if game.inventory is None:
            game.last_message = "You have nothing to trade with."
            return

        stock = get_shop_stock_for_floor(game.floor)
        if not stock:
            game.last_message = "No merchants are trading here right now."
            return

        # Attach transient shop state to the Game object.
        game.shop_stock = stock
        game.shop_cursor = 0
        game.shop_mode = "buy"
        game.show_shop = True
        game.last_message = "The merchant shows you their wares."

        # Route shop input through the ShopScreen if available
        if getattr(game, "shop_screen", None) is not None:
            game.active_screen = game.shop_screen

    def _attempt_shop_purchase(self, index: int) -> None:
        """
        Try to buy the item at ``index`` in the current shop stock.
        """
        game = self.game

        if game.inventory is None:
            game.last_message = "You have no way to carry more items."
            return

        stock: list[str] = list(getattr(game, "shop_stock", []))
        if index < 0 or index >= len(stock):
            return

        item_id = stock[index]
        item_def = get_item_def(item_id)
        if item_def is None:
            game.last_message = "The item seems to have vanished from reality."
            return

        # Price uses the item's "value" field; default to 0 if missing.
        price_raw = getattr(item_def, "value", None)
        try:
            price = int(price_raw) if price_raw is not None else 0
        except (TypeError, ValueError):
            price = 0
        if price < 0:
            price = 0

        hero_gold = getattr(game.hero_stats, "gold", 0)
        if hero_gold < price:
            game.last_message = "You can't afford that."
            return

        # Deduct gold using add_gold(-price) if available
        if hasattr(game.hero_stats, "add_gold"):
            game.hero_stats.add_gold(-price)
        else:
            game.hero_stats.gold = hero_gold - price

        # Grant the item
        game.inventory.add_item(item_id)
        item_name = getattr(item_def, "name", item_id)
        game.last_message = f"You buy {item_name} for {price} gold."

        # Remove the item from the merchant's stock so it's not infinite
        stock.pop(index)
        game.shop_stock = stock

        if stock:
            game.shop_cursor = max(0, min(index, len(stock) - 1))
        else:
            # Merchant sold out; close the shop and release the ShopScreen.
            game.shop_cursor = 0
            game.show_shop = False
            if getattr(game, "active_screen", None) is getattr(game, "shop_screen", None):
                game.active_screen = None

        # Re-sync stats in case gear matters (no full heal)
        if game.player is not None:
            game.apply_hero_stats_to_player(full_heal=False)

    def _attempt_shop_sell(self, index: int) -> None:
        """
        Try to sell one copy of the item at ``index`` in the player's
        sellable inventory list (excluding equipped items).
        """
        game = self.game
        inv = getattr(game, "inventory", None)

        if inv is None:
            game.last_message = "You have nothing to sell."
            return

        sellable_ids = inv.get_sellable_item_ids()
        if index < 0 or index >= len(sellable_ids):
            return

        item_id = sellable_ids[index]
        item_def = get_item_def(item_id)
        if item_def is None:
            game.last_message = "The merchant eyes it suspiciously and declines."
            return

        base_value_raw = getattr(item_def, "value", None)
        try:
            base_value = int(base_value_raw) if base_value_raw is not None else 0
        except (TypeError, ValueError):
            base_value = 0

        # Sell price: 50% of value, minimum 1 gold if it has any value at all.
        if base_value <= 0:
            sell_price = 1
        else:
            sell_price = max(1, base_value // 2)

        # Add gold
        if hasattr(game.hero_stats, "add_gold"):
            game.hero_stats.add_gold(sell_price)
        else:
            game.hero_stats.gold = getattr(game.hero_stats, "gold", 0) + sell_price

        # Remove exactly one instance of this item (we already excluded equipped copies)
        inv.remove_one(item_id)

        # Optionally, the merchant can now sell it back later.
        stock: list[str] = list(getattr(game, "shop_stock", []))
        stock.append(item_id)
        game.shop_stock = stock

        item_name = getattr(item_def, "name", item_id)
        game.last_message = f"You sell {item_name} for {sell_price} gold."

        # Re-sync stats in case something weird changed (no full heal)
        if game.player is not None:
            game.apply_hero_stats_to_player(full_heal=False)

        if not stock and not inv.get_sellable_item_ids():
            game.shop_cursor = 0
            game.show_shop = False
            game.last_message = "There is nothing left to buy or sell."

            if getattr(game, "active_screen", None) is getattr(game, "shop_screen", None):
                game.active_screen = None

    def try_interact(self) -> None:
        """
        Contextual interaction when pressing E:
        - If a chest is nearby, open it.
        - Else if an event node is nearby, trigger it.
        - Else if a merchant is nearby, open the merchant UI.
        - Otherwise, show a soft 'nothing here' message.
        """
        game = self.game

        # Ignore interaction while overlays are open
        if game.show_inventory or game.show_character_sheet:
            return

        # 1) Chest takes priority (so loot remains intuitive)
        chest = self._find_chest_near_player(max_distance_px=TILE_SIZE // 2)
        if chest is not None:
            self.try_open_chest()
            return

        # 2) Try event nodes
        node = self._find_event_near_player(max_distance_px=TILE_SIZE // 2)
        if node is not None:
            self._trigger_event_node(node)
            return

        # 3) Merchant interaction (must be near a merchant entity)
        merchant = self._find_merchant_near_player(max_distance_px=TILE_SIZE)
        if merchant is not None:
            self._open_shop()
            return

        # 4) Nothing
        game.last_message = "There is nothing here to interact with."
