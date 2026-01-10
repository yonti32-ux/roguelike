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
        self.last_direction: tuple[int, int] = (0, -1)  # Default: pointing up (north)
        self._zoom_cooldown = 0.0  # Cooldown for zoom to prevent spam
    
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
        
        # Toggle quest screen (J for Journal/Quests)
        if input_manager is not None:
            if input_manager.event_matches_action(InputAction.TOGGLE_QUEST_SCREEN, event):
                game.toggle_quest_screen()
                return
        else:
            if event.key == pygame.K_j:
                game.toggle_quest_screen()
                return
        
        # Zoom controls
        if event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS or event.key == pygame.K_KP_PLUS:
            self.zoom_in()
            return
        if event.key == pygame.K_MINUS or event.key == pygame.K_UNDERSCORE or event.key == pygame.K_KP_MINUS:
            self.zoom_out()
            return
        if event.key == pygame.K_0 or event.key == pygame.K_KP0:
            self.reset_zoom()
            return
    
    def handle_mouse_wheel(self, event: pygame.event.Event) -> None:
        """Handle mouse wheel events for zooming."""
        if event.type == pygame.MOUSEWHEEL:
            if event.y > 0:
                self.zoom_in()
            elif event.y < 0:
                self.zoom_out()
    
    def zoom_in(self) -> None:
        """Zoom in on the overworld map."""
        if self._zoom_cooldown > 0:
            return
        
        game = self.game
        if not hasattr(game, "overworld_zoom_levels"):
            return
        
        levels = game.overworld_zoom_levels
        current_idx = getattr(game, "overworld_zoom_index", len(levels) // 2)
        
        if current_idx < len(levels) - 1:
            game.overworld_zoom_index = current_idx + 1
            self._zoom_cooldown = 0.1  # Small cooldown to prevent spam
            zoom_value = levels[game.overworld_zoom_index]
            game.add_message(f"Zoom: {int(zoom_value * 100)}%")
    
    def zoom_out(self) -> None:
        """Zoom out on the overworld map."""
        if self._zoom_cooldown > 0:
            return
        
        game = self.game
        if not hasattr(game, "overworld_zoom_levels"):
            return
        
        levels = game.overworld_zoom_levels
        current_idx = getattr(game, "overworld_zoom_index", len(levels) // 2)
        
        if current_idx > 0:
            game.overworld_zoom_index = current_idx - 1
            self._zoom_cooldown = 0.1
            zoom_value = levels[game.overworld_zoom_index]
            game.add_message(f"Zoom: {int(zoom_value * 100)}%")
    
    def reset_zoom(self) -> None:
        """Reset zoom to default (100%)."""
        game = self.game
        if not hasattr(game, "overworld_zoom_levels"):
            return
        
        # Find index of 1.0 (100% zoom)
        levels = game.overworld_zoom_levels
        default_idx = 2  # Default should be index 2 (1.0)
        for i, zoom in enumerate(levels):
            if abs(zoom - 1.0) < 0.01:
                default_idx = i
                break
        
        game.overworld_zoom_index = default_idx
        game.add_message("Zoom: 100%")
    
    def update(self, dt: float) -> None:
        """Update overworld state."""
        self._last_move_time += dt
        if self._zoom_cooldown > 0:
            self._zoom_cooldown = max(0.0, self._zoom_cooldown - dt)
    
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
            # Store the direction we moved in (for arrow rendering)
            self.last_direction = direction
            
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
                    # Better discovery message with type and level
                    type_labels = {
                        "dungeon": "Dungeon",
                        "village": "Village",
                        "town": "Town",
                        "camp": "Camp",
                    }
                    type_label = type_labels.get(poi.poi_type, "Location")
                    game.add_message(f"You discover {poi.name} - A {type_label} (Level {poi.level})")
    
    def try_enter_poi(self) -> None:
        """Attempt to enter a POI at the player's current position."""
        game = self.game
        
        if game.overworld_map is None:
            return
        
        x, y = game.overworld_map.get_player_position()
        poi = game.overworld_map.get_poi_at(x, y)
        
        if poi is None:
            # Check for nearby POIs
            nearby_pois = game.overworld_map.get_pois_in_range(x, y, radius=1)
            if nearby_pois:
                closest_poi = nearby_pois[0]
                dx = abs(closest_poi.position[0] - x)
                dy = abs(closest_poi.position[1] - y)
                if dx <= 1 and dy <= 1:
                    game.add_message(f"You must stand directly on {closest_poi.name} to enter. (Move to {closest_poi.position[0]}, {closest_poi.position[1]})")
                else:
                    game.add_message("There is nothing here to enter.")
            else:
                game.add_message("There is nothing here to enter.")
            return
        
        if not poi.discovered:
            poi.discover()
            # Better discovery message
            type_labels = {
                "dungeon": "Dungeon",
                "village": "Village",
                "town": "Town",
                "camp": "Camp",
            }
            type_label = type_labels.get(poi.poi_type, "Location")
            game.add_message(f"You discover {poi.name} - A {type_label} (Level {poi.level}). Press E again to enter.")
            return
        
        # Check if can enter
        if not poi.can_enter(game):
            game.add_message(f"You cannot enter {poi.name} right now.")
            return
        
        # Enter the POI (message will be shown by POI.enter())
        game.enter_poi(poi)

