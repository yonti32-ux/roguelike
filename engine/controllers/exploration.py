from __future__ import annotations

from typing import TYPE_CHECKING, Optional
import random

import pygame

from settings import TILE_SIZE
from ..managers.message_log import get_rarity_color
from world.entities import Enemy, Chest
from world.entities import EventNode  # NEW
from world.entities import Merchant  # NEW merchant NPC
from world.entities import Trap  # NEW: traps
from world.ai import update_enemy_ai  # NEW: centralised enemy AI
from systems.inventory import get_item_def
from systems.loot import roll_chest_loot, roll_chest_consumable, get_shop_stock_for_floor
from systems.events import get_event_def, EventResult  # NEW
from systems.traps import get_trap_def, TrapResult  # NEW: trap system
from systems.economy import (
    calculate_shop_buy_price,
    calculate_shop_sell_price,
)

from systems.input import InputAction



if TYPE_CHECKING:
    # Only imported for type hints, to avoid circular imports at runtime
    from ..core.game import Game


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

        # Handle mouse wheel for tutorial scrolling
        if event.type == pygame.MOUSEWHEEL:
            if getattr(game, "show_exploration_tutorial", False):
                if not hasattr(game, "exploration_tutorial_scroll_offset"):
                    game.exploration_tutorial_scroll_offset = 0
                # Scroll tutorial (negative y means scroll up)
                game.exploration_tutorial_scroll_offset = max(0, game.exploration_tutorial_scroll_offset - event.y * 30)
            return

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
        if getattr(game, "show_inventory", False) or getattr(game, "show_character_sheet", False) or getattr(game, "show_skill_screen", False):
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

        # Toggle skill screen (T for Talents/Skills)
        if event.key == pygame.K_t:
            game.toggle_skill_screen()
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

        # Toggle exploration tutorial (H key)
        if event.key == pygame.K_h:
            game.show_exploration_tutorial = not getattr(game, "show_exploration_tutorial", False)
            if getattr(game, "show_exploration_tutorial", False):
                # Close other overlays when opening tutorial
                game.show_exploration_log = False
                # Initialize scroll offset if not exists
                if not hasattr(game, "exploration_tutorial_scroll_offset"):
                    game.exploration_tutorial_scroll_offset = 0
            return

        # Handle tutorial scrolling and closing
        if getattr(game, "show_exploration_tutorial", False):
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_h:
                game.show_exploration_tutorial = False
                game.exploration_tutorial_scroll_offset = 0
                return
            # Handle scrolling with arrow keys
            if event.key == pygame.K_UP or event.key == pygame.K_w:
                if not hasattr(game, "exploration_tutorial_scroll_offset"):
                    game.exploration_tutorial_scroll_offset = 0
                game.exploration_tutorial_scroll_offset = max(0, game.exploration_tutorial_scroll_offset - 20)
                return
            if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                if not hasattr(game, "exploration_tutorial_scroll_offset"):
                    game.exploration_tutorial_scroll_offset = 0
                game.exploration_tutorial_scroll_offset += 20
                return
            if event.key == pygame.K_PAGEUP:
                if not hasattr(game, "exploration_tutorial_scroll_offset"):
                    game.exploration_tutorial_scroll_offset = 0
                game.exploration_tutorial_scroll_offset = max(0, game.exploration_tutorial_scroll_offset - 200)
                return
            if event.key == pygame.K_PAGEDOWN:
                if not hasattr(game, "exploration_tutorial_scroll_offset"):
                    game.exploration_tutorial_scroll_offset = 0
                game.exploration_tutorial_scroll_offset += 200
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
        if game.show_character_sheet or game.show_inventory or getattr(game, "show_shop", False) or getattr(game, "show_skill_screen", False):
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

            def _can_player_move_to(x: float, y: float) -> tuple[bool, list[Enemy], list[Merchant]]:
                """Check if player can move to position, returns (can_move, blocking_enemies, blocking_merchants)."""
                test_rect = pygame.Rect(
                    int(x),
                    int(y),
                    game.player.width,
                    game.player.height,
                )

                blocked_by_tiles = not game.current_map.rect_can_move_to(test_rect)

                # Enemies block movement; stepping into them triggers battle instead
                blocking_enemies: list[Enemy] = [
                    e
                    for e in game.current_map.entities
                    if isinstance(e, Enemy)
                    and getattr(e, "blocks_movement", True)
                    and e.rect.colliderect(test_rect)
                ]

                # Merchants also block movement, but do NOT start battles
                blocking_merchants: list[Merchant] = [
                    m
                    for m in game.current_map.entities
                    if isinstance(m, Merchant)
                    and getattr(m, "blocks_movement", True)
                    and m.rect.colliderect(test_rect)
                ]

                can_move = not blocked_by_tiles and not blocking_enemies and not blocking_merchants
                return can_move, blocking_enemies, blocking_merchants

            # Try full diagonal movement first
            can_move, blocking_enemies, blocking_merchants = _can_player_move_to(new_x, new_y)
            
            if can_move:
                old_x, old_y = game.player.x, game.player.y
                game.player.move_to(new_x, new_y)
                
                # Add footstep particles
                if hasattr(game, "_exploration_particles"):
                    # Create subtle dust particles at feet
                    foot_x = new_x + game.player.width // 2
                    foot_y = new_y + game.player.height
                    for _ in range(random.randint(2, 4)):
                        game._exploration_particles.append({
                            "x": foot_x + random.uniform(-5, 5),
                            "y": foot_y + random.uniform(-3, 0),
                            "vx": random.uniform(-10, 10),
                            "vy": random.uniform(-5, 5),
                            "timer": random.uniform(0.3, 0.6),
                            "max_time": random.uniform(0.3, 0.6),
                            "color": (120, 100, 80),  # Brown dust
                            "size": random.randint(1, 2),
                        })
                
                # Check for trap triggers after movement
                self._check_trap_triggers(game)
            elif blocking_enemies:
                # Blocked by enemies - try sliding to see if we can go around them
                # Try X-axis movement (horizontal sliding)
                can_move_x, blocking_enemies_x, blocking_merchants_x = _can_player_move_to(
                    game.player.x + move_vector.x, game.player.y
                )
                if can_move_x:
                    game.player.move_to(game.player.x + move_vector.x, game.player.y)
                    self._check_trap_triggers(game)
                elif blocking_enemies_x and game.post_battle_grace <= 0.0:
                    # Can't slide past enemy on X axis, trigger battle
                    game.start_battle(blocking_enemies_x[0])
                else:
                    # Try Y-axis movement (vertical sliding)
                    can_move_y, blocking_enemies_y, blocking_merchants_y = _can_player_move_to(
                        game.player.x, game.player.y + move_vector.y
                    )
                    if can_move_y:
                        game.player.move_to(game.player.x, game.player.y + move_vector.y)
                        self._check_trap_triggers(game)
                    elif blocking_enemies_y and game.post_battle_grace <= 0.0:
                        # Can't slide past enemy on Y axis either, trigger battle
                        game.start_battle(blocking_enemies_y[0])
                    # If completely blocked and no battle triggered, do nothing
            else:
                # Blocked by tiles or merchants - try sliding along one axis
                # Try X-axis movement (horizontal sliding)
                can_move_x, blocking_enemies_x, blocking_merchants_x = _can_player_move_to(
                    game.player.x + move_vector.x, game.player.y
                )
                if can_move_x:
                    game.player.move_to(game.player.x + move_vector.x, game.player.y)
                    self._check_trap_triggers(game)
                elif blocking_enemies_x and game.post_battle_grace <= 0.0:
                    game.start_battle(blocking_enemies_x[0])
                else:
                    # Try Y-axis movement (vertical sliding)
                    can_move_y, blocking_enemies_y, blocking_merchants_y = _can_player_move_to(
                        game.player.x, game.player.y + move_vector.y
                    )
                    if can_move_y:
                        game.player.move_to(game.player.x, game.player.y + move_vector.y)
                        self._check_trap_triggers(game)
                    elif blocking_enemies_y and game.post_battle_grace <= 0.0:
                        game.start_battle(blocking_enemies_y[0])
                    # If completely blocked, do nothing

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
        if game.show_inventory or game.show_character_sheet or getattr(game, "show_skill_screen", False):
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
        
        # Store chest position for pickup effect
        chest_x, chest_y = chest.rect.center

        # Roll item loot
        item_id = roll_chest_loot(game.floor)
        
        # Roll consumable loot (separate from items)
        consumable_id = roll_chest_consumable(game.floor)

        # Roll some gold for the chest as well
        # Floors deeper → more gold
        min_gold = 5 + game.floor
        max_gold = 10 + game.floor * 2
        gold_amount = random.randint(min_gold, max_gold)
        gained_gold = 0
        if hasattr(game.hero_stats, "add_gold"):
            gained_gold = game.hero_stats.add_gold(gold_amount)

        # Collect all loot items for message
        loot_items = []
        item_color = None

        # Add item to inventory if it dropped
        if item_id is not None:
            game.inventory.add_item(item_id, randomized=True)
            # Store floor index for randomization context
            if not hasattr(game.inventory, "_current_floor"):
                game.inventory._current_floor = game.floor
            else:
                game.inventory._current_floor = game.floor

            item_def = get_item_def(item_id)
            item_name = item_def.name if item_def is not None else item_id
            rarity = getattr(item_def, "rarity", None) if item_def is not None else None
            item_color = get_rarity_color(rarity) if rarity else None
            loot_items.append(item_name)
            
            # Add item pickup effect
            if hasattr(game, "_exploration_particles"):
                # Color based on rarity
                pickup_colors = {
                    "common": (200, 200, 200),
                    "uncommon": (100, 255, 100),
                    "rare": (100, 150, 255),
                    "epic": (200, 100, 255),
                    "legendary": (255, 200, 100),
                }
                color = pickup_colors.get(rarity, (255, 255, 200)) if rarity else (255, 255, 200)
                
                # Create pickup particles
                for _ in range(random.randint(8, 12)):
                    game._exploration_particles.append({
                        "x": chest_x + random.uniform(-10, 10),
                        "y": chest_y + random.uniform(-10, 10),
                        "vx": random.uniform(-30, 30),
                        "vy": random.uniform(-40, -10),  # Upward
                        "timer": random.uniform(0.5, 1.0),
                        "max_time": random.uniform(0.5, 1.0),
                        "color": color,
                        "size": random.randint(2, 4),
                    })

        # Add consumable to inventory if it dropped
        if consumable_id is not None:
            game.inventory.add_item(consumable_id, randomized=False)
            from systems.consumables import get_consumable
            consumable_def = get_consumable(consumable_id)
            consumable_name = consumable_def.name if consumable_def is not None else consumable_id
            loot_items.append(consumable_name)

        # Build message based on what we actually got
        if not loot_items and gained_gold == 0:
            game.last_message = "The chest is empty."
            return

        # Construct message with all loot
        msg_parts = []
        if loot_items:
            if len(loot_items) == 1:
                msg_parts.append(loot_items[0])
            else:
                # Join items with commas, and "and" before the last one
                msg_parts.append(", ".join(loot_items[:-1]) + f" and {loot_items[-1]}")
        
        if gained_gold > 0:
            if msg_parts:
                msg_parts.append(f"{gained_gold} gold")
            else:
                msg_parts.append(f"{gained_gold} gold")

        msg = f"You open the chest and find: {', '.join(msg_parts)}."

        # Use colored message if we have an item with rarity
        if item_color is not None and hasattr(game, "add_message_colored"):
            game.add_message_colored(msg, item_color)
        else:
            game.last_message = msg

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

        # Reuse existing stock if this merchant was already opened on this floor,
        # so the shop inventory doesn't fully refresh every time you step out.
        existing_stock = list(getattr(game, "shop_stock", []))
        if existing_stock:
            stock = existing_stock
        else:
            stock = get_shop_stock_for_floor(game.floor)
            if not stock:
                game.last_message = "No merchants are trading here right now."
                return

        # Attach (or reattach) shop state to the Game object.
        game.shop_stock = stock
        game.shop_cursor = 0
        game.shop_mode = "buy"
        game.show_shop = True
        game.last_message = "The merchant shows you their wares."
        
        # Close other screens when opening shop
        game.show_inventory = False
        game.show_character_sheet = False
        game.show_battle_log = False
        if hasattr(game, "show_exploration_log"):
            game.show_exploration_log = False

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

        # Calculate price using economy system (dynamic pricing with floor scaling)
        floor_index = getattr(game, "floor", 1)
        price = calculate_shop_buy_price(item_def, floor_index)

        hero_gold = getattr(game.hero_stats, "gold", 0)
        if hero_gold < price:
            game.last_message = "You can't afford that."
            return

        # Deduct gold directly; HeroStats.add_gold is for positive amounts only.
        game.hero_stats.gold = hero_gold - price

        # Set floor context for item randomization
        if not hasattr(game.inventory, "_current_floor"):
            game.inventory._current_floor = floor_index
        else:
            game.inventory._current_floor = floor_index

        # Grant the item
            game.inventory.add_item(item_id, randomized=True)
            item_name = getattr(item_def, "name", item_id)
            
            # Add item pickup effect
            if hasattr(game, "_exploration_particles") and chest is not None:
                cx, cy = chest.rect.center
                rarity = getattr(item_def, "rarity", None)
                # Color based on rarity
                pickup_colors = {
                    "common": (200, 200, 200),
                    "uncommon": (100, 255, 100),
                    "rare": (100, 150, 255),
                    "epic": (200, 100, 255),
                    "legendary": (255, 200, 100),
                }
                color = pickup_colors.get(rarity, (255, 255, 200)) if rarity else (255, 255, 200)
                
                # Create pickup particles
                for _ in range(random.randint(8, 12)):
                    game._exploration_particles.append({
                        "x": cx + random.uniform(-10, 10),
                        "y": cy + random.uniform(-10, 10),
                        "vx": random.uniform(-30, 30),
                        "vy": random.uniform(-40, -10),  # Upward
                        "timer": random.uniform(0.5, 1.0),
                        "max_time": random.uniform(0.5, 1.0),
                        "color": color,
                        "size": random.randint(2, 4),
                    })
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

        # Calculate sell price using economy system (dynamic pricing with floor scaling)
        floor_index = getattr(game, "floor", 1)
        sell_price = calculate_shop_sell_price(item_def, floor_index)

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

    # --- Trap helpers ---------------------------------------------------

    def _find_trap_near_player(
        self,
        max_distance_px: int = TILE_SIZE // 2,
    ) -> Optional[Trap]:
        """
        Return a trap entity near/under the player, or None.
        """
        game = self.game

        if game.current_map is None or game.player is None:
            return None

        px, py = game.player.rect.center
        max_dist_sq = max_distance_px * max_distance_px

        for entity in getattr(game.current_map, "entities", []):
            if not isinstance(entity, Trap):
                continue
            tx, ty = entity.rect.center
            dx = tx - px
            dy = ty - py
            if dx * dx + dy * dy <= max_dist_sq:
                return entity

        return None

    def find_trap_near_player(self, max_distance_px: int) -> Optional[Trap]:
        """
        Public wrapper so UI code can query nearby traps.
        """
        return self._find_trap_near_player(max_distance_px=max_distance_px)

    def _check_trap_triggers(self, game: "Game") -> None:
        """
        Check if player is standing on any active traps and trigger them.
        Called after player movement.
        """
        if game.current_map is None or game.player is None:
            return

        px, py = game.player.rect.center
        trigger_radius = TILE_SIZE // 2  # Trigger when player center is within half a tile

        for entity in list(game.current_map.entities):
            if not isinstance(entity, Trap):
                continue
            if not entity.is_active:
                continue

            tx, ty = entity.rect.center
            dx = tx - px
            dy = ty - py
            dist_sq = dx * dx + dy * dy

            if dist_sq <= trigger_radius * trigger_radius:
                # Player stepped on trap - trigger it
                self._trigger_trap(entity)
                break  # Only trigger one trap per movement

    def _trigger_trap(self, trap: Trap) -> None:
        """
        Trigger a trap: run its handler and apply effects.
        """
        game = self.game

        if trap.triggered or trap.disarmed:
            return

        trap_def = get_trap_def(trap.trap_id)
        if trap_def is None:
            game.last_message = "The trap fizzles harmlessly."
            trap.triggered = True
            return

        # Run trap handler
        result = trap_def.handler(game)

        # Mark trap as triggered
        trap.triggered = True

        # Show message
        game.last_message = result.text

        # Apply status effects if any
        if result.status_effect is not None:
            if hasattr(game.player, "statuses"):
                game.player.statuses.append(result.status_effect)
            elif hasattr(game, "player_statuses"):
                if not hasattr(game, "player_statuses"):
                    game.player_statuses = []
                game.player_statuses.append(result.status_effect)

        # Re-sync player stats in case HP changed
        if game.player is not None:
            game.apply_hero_stats_to_player(full_heal=False)

    def _detect_trap(self, trap: Trap) -> bool:
        """
        Attempt to detect a trap. Returns True if successful.
        Uses trap's detection difficulty and player skill (if any).
        """
        trap_def = get_trap_def(trap.trap_id)
        if trap_def is None:
            return False

        # Base detection chance: 1.0 - difficulty (so 0.0 difficulty = always detect)
        base_chance = 1.0 - trap_def.detection_difficulty

        # TODO: Add player skill/perk bonuses here
        # For now, just use base chance with some randomness
        detection_roll = random.random()

        # If trap is already detected, always succeed
        if trap.detected:
            return True

        # Check if detection succeeds
        if detection_roll < base_chance:
            trap.detected = True
            return True

        return False

    def _disarm_trap(self, trap: Trap) -> bool:
        """
        Attempt to disarm a trap. Returns True if successful.
        On failure, trap may trigger (small chance).
        """
        game = self.game

        if trap.triggered or trap.disarmed:
            return False

        trap_def = get_trap_def(trap.trap_id)
        if trap_def is None:
            return False

        # Base disarm chance: 1.0 - difficulty
        base_chance = 1.0 - trap_def.disarm_difficulty

        # TODO: Add player skill/perk bonuses here
        disarm_roll = random.random()

        if disarm_roll < base_chance:
            # Success: trap is disarmed
            trap.disarmed = True
            game.last_message = f"You successfully disarm the {trap_def.name}."
            return True
        else:
            # Failure: small chance trap triggers anyway (10%)
            if random.random() < 0.1:
                game.last_message = "You fail to disarm the trap, and it triggers!"
                self._trigger_trap(trap)
            else:
                game.last_message = "You fail to disarm the trap, but it doesn't trigger."
            return False

    def try_interact(self) -> None:
        """
        Contextual interaction when pressing E:
        - If a chest is nearby, open it.
        - Else if an event node is nearby, trigger it.
        - Else if a merchant is nearby, open the merchant UI.
        - Else if a detected trap is nearby, attempt to disarm it.
        - Otherwise, show a soft 'nothing here' message.
        """
        game = self.game

        # Ignore interaction while overlays are open
        if game.show_inventory or game.show_character_sheet or getattr(game, "show_skill_screen", False):
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

        # 4) Try trap detection/disarming
        # Use TILE_SIZE (larger than trigger radius) so player can disarm from adjacent tiles
        trap = self._find_trap_near_player(max_distance_px=TILE_SIZE)
        if trap is not None:
            if trap.triggered or trap.disarmed:
                game.last_message = "The trap has already been triggered or disarmed."
                return
            
            if not trap.detected:
                # Try to detect it first
                if self._detect_trap(trap):
                    game.last_message = f"You notice a {get_trap_def(trap.trap_id).name if get_trap_def(trap.trap_id) else 'trap'} here. Press E again to disarm."
                else:
                    game.last_message = "You sense something is off, but can't identify what."
                return
            else:
                # Trap is detected, attempt to disarm
                self._disarm_trap(trap)
                return

        # 5) Nothing
        game.last_message = "There is nothing here to interact with."
