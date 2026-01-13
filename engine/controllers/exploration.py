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
try:
    from world.village.npcs import VillageNPC  # Village NPCs
except ImportError:
    VillageNPC = None  # Fallback if village system not available
from world.ai import update_enemy_ai  # NEW: centralised enemy AI
from systems.inventory import get_item_def
from systems.loot import roll_chest_loot, get_shop_stock_for_floor
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


def _rarity_priority(rarity: Optional[str]) -> int:
    """Get priority value for rarity (higher = better)."""
    if rarity is None:
        return 0
    rarity_map = {
        "common": 1,
        "uncommon": 2,
        "rare": 3,
        "epic": 4,
        "legendary": 5,
    }
    return rarity_map.get(rarity.lower(), 0)


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
        
        # Toggle quest screen (J for Journal/Quests)
        if input_manager is not None:
            if input_manager.event_matches_action(InputAction.TOGGLE_QUEST_SCREEN, event):
                game.toggle_quest_screen()
                return
        else:
            if event.key == pygame.K_j:
                game.toggle_quest_screen()
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

        # Interact (chest / event / merchant / stairs / etc.)
        if input_manager is not None:
            if input_manager.event_matches_action(InputAction.INTERACT, event):
                self.try_interact()
                return
        else:
            if event.key == pygame.K_e:
                self.try_interact()
                return

        # Q key: go up stairs (except on first floor where it shows confirmation)
        if event.key == pygame.K_q:
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

            def _can_player_move_to(x: float, y: float) -> tuple[bool, list[Enemy], list[Merchant], list]:
                """Check if player can move to position, returns (can_move, blocking_enemies, blocking_merchants, blocking_village_npcs)."""
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

                # Village NPCs block movement in villages
                blocking_village_npcs = []
                if VillageNPC is not None:
                    blocking_village_npcs = [
                        n
                        for n in game.current_map.entities
                        if isinstance(n, VillageNPC)
                        and getattr(n, "blocks_movement", True)
                        and n.rect.colliderect(test_rect)
                    ]

                can_move = not blocked_by_tiles and not blocking_enemies and not blocking_merchants and not blocking_village_npcs
                return can_move, blocking_enemies, blocking_merchants, blocking_village_npcs

            # Try full diagonal movement first
            can_move, blocking_enemies, blocking_merchants, blocking_village_npcs = _can_player_move_to(new_x, new_y)
            
            if can_move:
                game.player.move_to(new_x, new_y)
                # Check for trap triggers after movement
                self._check_trap_triggers(game)
                # Check for building entry/exit and show hints
                self._check_building_transitions(game)
            elif blocking_enemies:
                # Blocked by enemies - try sliding to see if we can go around them
                # Try X-axis movement (horizontal sliding)
                can_move_x, blocking_enemies_x, blocking_merchants_x, blocking_village_npcs_x = _can_player_move_to(
                    game.player.x + move_vector.x, game.player.y
                )
                if can_move_x:
                    game.player.move_to(game.player.x + move_vector.x, game.player.y)
                    self._check_trap_triggers(game)
                    self._check_building_transitions(game)
                elif blocking_enemies_x and game.post_battle_grace <= 0.0:
                    # Can't slide past enemy on X axis, trigger battle
                    game.start_battle(blocking_enemies_x[0])
                else:
                    # Try Y-axis movement (vertical sliding)
                    can_move_y, blocking_enemies_y, blocking_merchants_y, blocking_village_npcs_y = _can_player_move_to(
                        game.player.x, game.player.y + move_vector.y
                    )
                    if can_move_y:
                        game.player.move_to(game.player.x, game.player.y + move_vector.y)
                        self._check_trap_triggers(game)
                        self._check_building_transitions(game)
                    elif blocking_enemies_y and game.post_battle_grace <= 0.0:
                        # Can't slide past enemy on Y axis either, trigger battle
                        game.start_battle(blocking_enemies_y[0])
                    # If completely blocked and no battle triggered, do nothing
            else:
                # Blocked by tiles, merchants, or village NPCs - try sliding along one axis
                # Try X-axis movement (horizontal sliding)
                can_move_x, blocking_enemies_x, blocking_merchants_x, blocking_village_npcs_x = _can_player_move_to(
                    game.player.x + move_vector.x, game.player.y
                )
                if can_move_x:
                    game.player.move_to(game.player.x + move_vector.x, game.player.y)
                    self._check_trap_triggers(game)
                    self._check_building_transitions(game)
                elif blocking_enemies_x and game.post_battle_grace <= 0.0:
                    game.start_battle(blocking_enemies_x[0])
                else:
                    # Try Y-axis movement (vertical sliding)
                    can_move_y, blocking_enemies_y, blocking_merchants_y, blocking_village_npcs_y = _can_player_move_to(
                        game.player.x, game.player.y + move_vector.y
                    )
                    if can_move_y:
                        game.player.move_to(game.player.x, game.player.y + move_vector.y)
                        self._check_trap_triggers(game)
                        self._check_building_transitions(game)
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

        try:
            # Determine chest type (could be enhanced later with chest entity attributes)
            chest_type = getattr(chest, "chest_type", "normal")
            
            # Roll loot (now returns a list that can include both equipment and consumables)
            loot_items = roll_chest_loot(game.floor, chest_type=chest_type)

            # Roll some gold for the chest as well
            # Floors deeper → more gold
            min_gold = 5 + game.floor
            max_gold = 10 + game.floor * 2
            gold_amount = random.randint(min_gold, max_gold)
            gained_gold = 0
            if hasattr(game.hero_stats, "add_gold"):
                gained_gold = game.hero_stats.add_gold(gold_amount)

            # Build message based on what we actually got
            if not loot_items:
                if gained_gold > 0:
                    game.last_message = f"You open the chest and find {gained_gold} gold."
                else:
                    game.last_message = "The chest is empty."
                return

            # Add all loot items to inventory
            item_names = []
            item_rarities = []
            for item_id in loot_items:
                try:
                    item_def = get_item_def(item_id)
                    if item_def is None:
                        continue  # Skip invalid items
                    
                    # Determine if it's a consumable or equipment
                    is_consumable = item_def.slot == "consumable"
                    game.inventory.add_item(item_id, randomized=not is_consumable)
                    
                    # Store floor index for randomization context
                    if not hasattr(game.inventory, "_current_floor"):
                        game.inventory._current_floor = game.floor
                    else:
                        game.inventory._current_floor = game.floor
                    
                    item_names.append(item_def.name)
                    item_rarities.append(getattr(item_def, "rarity", None))
                except Exception:
                    # Skip items that fail to add
                    continue

            if not item_names:
                # All items failed to add
                if gained_gold > 0:
                    game.last_message = f"You open the chest and find {gained_gold} gold."
                else:
                    game.last_message = "The chest is empty."
                return

            # Build message with all items
            if len(item_names) == 1:
                items_str = item_names[0]
            elif len(item_names) == 2:
                items_str = f"{item_names[0]} and {item_names[1]}"
            else:
                # Multiple items: list all but last, then "and X"
                items_str = ", ".join(item_names[:-1]) + f", and {item_names[-1]}"
            
            # Use highest rarity for color (if any)
            highest_rarity = None
            for rarity in item_rarities:
                if rarity and (highest_rarity is None or _rarity_priority(rarity) > _rarity_priority(highest_rarity)):
                    highest_rarity = rarity
            
            if gained_gold > 0:
                msg = f"You open the chest and find: {items_str} and {gained_gold} gold."
            else:
                msg = f"You open the chest and find: {items_str}."

            color = get_rarity_color(highest_rarity) if highest_rarity else None
            if color is not None and hasattr(game, "add_message_colored"):
                game.add_message_colored(msg, color)
            else:
                game.last_message = msg
        
        except Exception:
            # Error handling: at least give a message
            game.last_message = "You open the chest, but something seems wrong..."

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
    
    # --- Village NPC helpers ------------------------------------------------
    
    def _find_village_npc_near_player(
        self,
        max_distance_px: int = TILE_SIZE,
    ) -> Optional["VillageNPC"]:
        """
        Return a village NPC entity near/under the player, or None.
        """
        if VillageNPC is None:
            return None
        
        game = self.game
        
        if game.current_map is None or game.player is None:
            return None
        
        px, py = game.player.rect.center
        max_dist_sq = max_distance_px * max_distance_px
        
        for entity in getattr(game.current_map, "entities", []):
            if not isinstance(entity, VillageNPC):
                continue
            mx, my = entity.rect.center
            dx = mx - px
            dy = my - py
            if dx * dx + dy * dy <= max_dist_sq:
                return entity
        
        return None
    
    def _interact_with_village_npc(self, npc: "VillageNPC") -> None:
        """
        Interact with a village NPC based on their type.
        
        Args:
            npc: The village NPC to interact with
        """
        game = self.game
        
        npc_type = getattr(npc, "npc_type", "villager")
        
        if npc_type == "merchant":
            # Open shop
            from systems.village.services import open_shop
            # Get village level from current POI
            village_level = 1
            if game.current_poi is not None:
                village_level = getattr(game.current_poi, "level", 1)
            open_shop(game, merchant_id=getattr(npc, "npc_id", None), village_level=village_level)
            
        elif npc_type == "innkeeper":
            # Show rest option
            from systems.village.services import rest_at_inn
            # For now, free rest (can add cost later)
            rest_at_inn(game, cost=0)
            
        elif npc_type == "recruiter":
            # Open recruitment screen
            from systems.village.services import open_recruitment
            open_recruitment(game, recruiter_id=getattr(npc, "npc_id", None))
            
        elif npc_type == "elder":
            # Open quest screen
            from systems.village.services import open_quest_screen
            npc_id = getattr(npc, "npc_id", "elder")
            open_quest_screen(game, elder_id=npc_id)
            
        elif npc_type == "villager":
            # Show dialogue (for now, just a message)
            dialogue = getattr(npc, "dialogue", [])
            if dialogue:
                game.add_message(dialogue[0])
            else:
                game.add_message(f"{getattr(npc, 'name', 'Villager')} greets you warmly.")
        elif npc_type == "camp_merchant":
            # Camp merchant - open camp shop
            from systems.camp.services import open_camp_merchant
            camp_level = 1
            if game.current_poi is not None:
                camp_level = getattr(game.current_poi, "level", 1)
            open_camp_merchant(game, camp_level=camp_level)
        elif npc_type == "camp_guard":
            # Camp guard - just dialogue for now
            dialogue = getattr(npc, "dialogue", [])
            if dialogue:
                game.add_message(dialogue[0])
            else:
                game.add_message(f"{getattr(npc, 'name', 'Guard')} nods at you. 'The camp is safe here.'")
        elif npc_type == "camp_traveler":
            # Camp traveler - dialogue and potential rumors
            dialogue = getattr(npc, "dialogue", [])
            if dialogue:
                game.add_message(dialogue[0])
            else:
                game.add_message(f"{getattr(npc, 'name', 'Traveler')} shares stories of the road.")
        else:
            game.add_message(f"You talk to {getattr(npc, 'name', 'the NPC')}.")

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
        # Clear sorted list so it gets regenerated with new stock
        if hasattr(game, "shop_stock_sorted"):
            delattr(game, "shop_stock_sorted")
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
        Uses sorted list if available (for categorized display), otherwise uses original stock.
        """
        game = self.game

        if game.inventory is None:
            game.last_message = "You have no way to carry more items."
            return

        # Use sorted list if available (for categorized shop display), otherwise use original
        sorted_stock = getattr(game, "shop_stock_sorted", None)
        if sorted_stock is not None:
            stock = sorted_stock
        else:
            stock = list(getattr(game, "shop_stock", []))
        
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

        # Grant the item
        game.inventory.add_item(item_id)
        item_name = getattr(item_def, "name", item_id)
        game.last_message = f"You buy {item_name} for {price} gold."

        # Remove the item from both sorted and original stock
        stock.pop(index)
        game.shop_stock_sorted = stock  # Update sorted list
        
        # Also remove from original stock by finding the item_id
        original_stock = list(getattr(game, "shop_stock", []))
        if item_id in original_stock:
            original_stock.remove(item_id)
        game.shop_stock = original_stock

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

    def _check_building_transitions(self, game: "Game") -> None:
        """
        Check if player has entered or exited a building and show hints for service buildings.
        Called after player movement.
        """
        if game.current_map is None or game.player is None:
            return

        # Get current building
        px, py = game.player.rect.center
        tile_x, tile_y = game.current_map.world_to_tile(px, py)
        current_building = game.current_map.get_building_at(tile_x, tile_y)

        # Get previous building from last check
        last_building = getattr(game, "_last_building_id", None)
        current_building_id = id(current_building) if current_building is not None else None

        # Only show hint when entering a new building (not when staying in the same one)
        if current_building_id != last_building and current_building is not None:
            # Player entered a building - show hint based on building type
            building_type = getattr(current_building, "building_type", None)
            
            if building_type == "shop":
                game.add_message("You enter a shop. Press E near the merchant to browse their wares.")
            elif building_type == "inn":
                game.add_message("You enter an inn. Press E near the innkeeper to rest and recover.")
            elif building_type == "tavern":
                game.add_message("You enter a tavern. Press E near the recruiter to find companions.")
            elif building_type == "town_hall" or building_type == "elder_hall":
                game.add_message("You enter the town hall. Press E near the elder to view available quests.")
            # Houses don't need hints as they're just decorative

        # Update last building tracking
        game._last_building_id = current_building_id

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
        - Else if standing on stairs, use them to go down (or up if on up stairs and not first floor).
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

        # 3) Village NPC interaction (check before merchant, as village NPCs are more specific)
        if VillageNPC is not None:
            village_npc = self._find_village_npc_near_player(max_distance_px=TILE_SIZE)
            if village_npc is not None:
                self._interact_with_village_npc(village_npc)
                return
        
        # 4) Merchant interaction (must be near a merchant entity)
        merchant = self._find_merchant_near_player(max_distance_px=TILE_SIZE)
        if merchant is not None:
            self._open_shop()
            return

        # 5) Try trap detection/disarming
        trap = self._find_trap_near_player(max_distance_px=TILE_SIZE // 2)
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

        # 6) Check for campfire interaction (camp rest)
        if game.current_map is not None and game.player is not None:
            from world.poi.types import CampPOI
            if game.current_poi is not None and isinstance(game.current_poi, CampPOI):
                px, py = game.player.rect.center
                player_tx, player_ty = game.current_map.world_to_tile(px, py)
                
                # Check if standing on or adjacent to campfire
                camp_fire_pos = getattr(game.current_map, "camp_fire_pos", None)
                if camp_fire_pos is not None:
                    fire_tx, fire_ty = camp_fire_pos
                    # Check if player is on fire tile or adjacent (within 1 tile)
                    distance = max(abs(player_tx - fire_tx), abs(player_ty - fire_ty))
                    if distance <= 1:
                        # Can rest at campfire (if not hostile)
                        if not game.current_poi.is_hostile:
                            from systems.camp.services import rest_at_camp
                            # Calculate cost based on faction relations (free for friendly)
                            cost = 0  # Free for now, can be adjusted based on faction
                            rest_at_camp(game, cost=cost)
                        else:
                            game.last_message = "You cannot rest at a hostile camp!"
                        return
        
        # 7) Check for village/camp exit points (return to overworld)
        if game.current_map is not None and game.player is not None:
            # Check if we're in a village
            from world.poi.types import VillagePOI
            if game.current_poi is not None and isinstance(game.current_poi, VillagePOI):
                px, py = game.player.rect.center
                player_tx, player_ty = game.current_map.world_to_tile(px, py)
                
                # Check if standing on any village exit tile
                exit_tiles = getattr(game.current_map, "village_exit_tiles", None)
                if exit_tiles is not None and (player_tx, player_ty) in exit_tiles:
                    game.exit_poi()
                    return

        # 8) Check for stairs (after other interactions, so they don't block chests/merchants on stairs)
        if game.current_map is not None and game.player is not None:
            px, py = game.player.rect.center
            player_tx, player_ty = game.current_map.world_to_tile(px, py)
            
            # Check if standing on down stairs (go down)
            if game.current_map.down_stairs is not None:
                if (player_tx, player_ty) == game.current_map.down_stairs:
                    game.try_change_floor(+1)
                    return
            
            # Check if standing on up stairs (go up) - but not on first floor (use Q instead)
            if game.current_map.up_stairs is not None:
                if (player_tx, player_ty) == game.current_map.up_stairs:
                    # Only go up automatically if not on first floor (first floor needs confirmation via Q)
                    if game.floor > 1:
                        game.try_change_floor(-1)
                        return

        # 9) Nothing
        game.last_message = "There is nothing here to interact with."
