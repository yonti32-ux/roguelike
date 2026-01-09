"""
Overworld controller.

Handles input and movement for the overworld map.
"""

from typing import TYPE_CHECKING
import pygame

from systems.input import InputAction

if TYPE_CHECKING:
    from ..core.game import Game


class OverworldController:
    """
    Handles input and movement for overworld mode.
    
    Tile-based movement: player moves one tile per input.
    """
    
    def __init__(self, game: "Game") -> None:
        self.game = game
        self._last_move_time = 0.0
        self._move_cooldown = 0.15  # Seconds between moves (prevents spam)
    
    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle input events for overworld mode."""
        game = self.game
        
        if game.overworld_map is None:
            return
        
        # Block input if overlays are open
        if game.is_overlay_open():
            return
        
        if event.type != pygame.KEYDOWN:
            return
        
        input_manager = getattr(game, "input_manager", None)
        
        # Movement (8-directional)
        direction = None
        
        if input_manager is not None:
            # Use logical input actions
            if input_manager.event_matches_action(InputAction.MOVE_UP, event):
                direction = (0, -1)
            elif input_manager.event_matches_action(InputAction.MOVE_DOWN, event):
                direction = (0, 1)
            elif input_manager.event_matches_action(InputAction.MOVE_LEFT, event):
                direction = (-1, 0)
            elif input_manager.event_matches_action(InputAction.MOVE_RIGHT, event):
                direction = (1, 0)
        else:
            # Fallback: direct key checks
            if event.key in (pygame.K_w, pygame.K_UP):
                direction = (0, -1)
            elif event.key in (pygame.K_s, pygame.K_DOWN):
                direction = (0, 1)
            elif event.key in (pygame.K_a, pygame.K_LEFT):
                direction = (-1, 0)
            elif event.key in (pygame.K_d, pygame.K_RIGHT):
                direction = (1, 0)
            # Diagonal movement
            elif event.key == pygame.K_q:  # NW
                direction = (-1, -1)
            elif event.key == pygame.K_e:  # NE
                direction = (1, -1)
            elif event.key == pygame.K_z:  # SW
                direction = (-1, 1)
            elif event.key == pygame.K_c:  # SE
                direction = (1, 1)
        
        if direction is not None:
            self.try_move(direction)
            return
        
        # Interaction (enter POI)
        if input_manager is not None:
            if input_manager.event_matches_action(InputAction.INTERACT, event):
                self.try_enter_poi()
                return
        else:
            if event.key == pygame.K_e:
                self.try_enter_poi()
                return
        
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
    
    def update(self, dt: float) -> None:
        """Update overworld state."""
        self._last_move_time += dt
    
    def try_move(self, direction: tuple[int, int]) -> None:
        """
        Attempt to move the player in the given direction.
        
        Args:
            direction: (dx, dy) tuple, e.g., (0, -1) for north
        """
        game = self.game
        
        if game.overworld_map is None:
            return
        
        # Cooldown check
        if self._last_move_time < self._move_cooldown:
            return
        
        dx, dy = direction
        current_x, current_y = game.overworld_map.get_player_position()
        new_x = current_x + dx
        new_y = current_y + dy
        
        # Check if move is valid
        if not game.overworld_map.in_bounds(new_x, new_y):
            return
        
        if not game.overworld_map.is_walkable(new_x, new_y):
            return
        
        # Get sight radius from config
        from world.overworld import OverworldConfig
        config = OverworldConfig.load()
        sight_radius = config.sight_radius
        
        # Move player (this will also explore tiles in sight radius)
        if game.overworld_map.set_player_position(new_x, new_y, sight_radius=sight_radius):
            self._last_move_time = 0.0
            
            # Consume time based on terrain
            if game.time_system is not None:
                tile = game.overworld_map.get_tile(new_x, new_y)
                if tile:
                    cost = config.terrain_costs.get(tile.id, config.movement_cost_base)
                    game.time_system.add_time(cost * config.movement_cost_base)
            
            # Check for nearby POIs to discover (within sight radius)
            nearby_pois = game.overworld_map.get_pois_in_range(new_x, new_y, radius=sight_radius)
            for poi in nearby_pois:
                if not poi.discovered:
                    poi.discover()
                    game.add_message(f"You discover: {poi.name}")
    
    def try_enter_poi(self) -> None:
        """Attempt to enter a POI at the player's current position."""
        game = self.game
        
        if game.overworld_map is None:
            return
        
        x, y = game.overworld_map.get_player_position()
        poi = game.overworld_map.get_poi_at(x, y)
        
        if poi is None:
            game.add_message("There is nothing here to enter.")
            return
        
        if not poi.discovered:
            poi.discover()
            game.add_message(f"You discover: {poi.name}")
            return
        
        # Enter the POI
        game.enter_poi(poi)

