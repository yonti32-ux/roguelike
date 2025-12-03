# engine/exploration.py

from __future__ import annotations

from typing import TYPE_CHECKING, Optional
import random

import pygame

from settings import TILE_SIZE
from world.entities import Enemy, Chest
from world.ai import update_enemy_ai  # NEW: centralised enemy AI
from systems.inventory import get_item_def
from systems.loot import roll_chest_loot

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

        # --- Inventory is open: handle item actions / closing first ---
        if game.show_inventory:
            self._handle_inventory_key(event)
            return

        # --- Normal exploration input (inventory closed) ---

        # Toggle inventory
        if event.key == pygame.K_i:
            game.show_inventory = not game.show_inventory
            if game.show_inventory:
                # Pause other overlays while inventory is open
                game.show_character_sheet = False
                game.show_battle_log = False
            return

        # Toggle character sheet
        if event.key == pygame.K_c:
            game.show_character_sheet = not game.show_character_sheet
            if game.show_character_sheet:
                game.show_battle_log = False
            return

        # Toggle last battle log overlay
        if event.key == pygame.K_l:
            if game.last_battle_log:
                game.show_battle_log = not game.show_battle_log
            else:
                game.show_battle_log = False
            return

        # Interact (open chest etc.)
        if event.key == pygame.K_e:
            self.try_open_chest()
            return

        # Stairs: go down / up
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
        if game.show_character_sheet or game.show_inventory:
            return

        keys = pygame.key.get_pressed()
        direction = pygame.Vector2(0, 0)

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

        # --- Player movement & collision with enemies ---
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

            if not blocked_by_tiles and not blocking_enemies:
                game.player.move_to(new_x, new_y)
            elif blocking_enemies:
                # During grace, you simply can't walk through them; no new battle yet
                if game.post_battle_grace <= 0.0:
                    game.start_battle(blocking_enemies[0])

        # --- Enemy updates (delegated to world.ai) ---
        for entity in list(game.current_map.entities):
            if isinstance(entity, Enemy):
                update_enemy_ai(entity, game, dt)

    # ---------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------

    def _handle_inventory_key(self, event: pygame.event.Event) -> None:
        """
        Handle key presses while the inventory overlay is open.
        """
        game = self.game

        # Close inventory with I or ESC
        if event.key in (pygame.K_i, pygame.K_ESCAPE):
            game.show_inventory = False
            return

        if game.inventory is None:
            return

        # 1–9 / Numpad 1–9: equip that item from the visible list
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

        if idx is None:
            return

        visible_items = game.inventory.items[:10]
        if idx >= len(visible_items):
            return

        item_id = visible_items[idx]
        msg = game.inventory.equip(item_id)
        game.last_message = msg

        # Re-apply hero stats + gear to the player (no full heal)
        if game.player is not None:
            game.apply_hero_stats_to_player(full_heal=False)

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
