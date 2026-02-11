"""
Overworld controller.

Handles input and movement for the overworld map.
"""

from typing import TYPE_CHECKING
import pygame

# POI type display labels (shared to avoid duplication)
POI_TYPE_LABELS = {
    "dungeon": "Dungeon",
    "village": "Village",
    "town": "Town",
    "camp": "Camp",
}

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
        
        if event.type != pygame.KEYDOWN:
            return
        
        # Toggle overworld tutorial (H key) - works at any time
        if event.key == pygame.K_h:
            game.show_overworld_tutorial = not getattr(game, "show_overworld_tutorial", False)
            if getattr(game, "show_overworld_tutorial", False):
                # Close other overlays when opening tutorial
                if hasattr(game, "show_exploration_log"):
                    game.show_exploration_log = False
                if hasattr(game, "show_discovery_log"):
                    game.show_discovery_log = False
                # Initialize scroll offset if not exists
                if not hasattr(game, "overworld_tutorial_scroll_offset"):
                    game.overworld_tutorial_scroll_offset = 0
            return
        
        
        # Handle tutorial scrolling and closing (works even when tutorial is open)
        if getattr(game, "show_overworld_tutorial", False):
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_h:
                game.show_overworld_tutorial = False
                game.overworld_tutorial_scroll_offset = 0
                return
            # Handle scrolling with arrow keys
            if event.key == pygame.K_UP or event.key == pygame.K_w:
                if not hasattr(game, "overworld_tutorial_scroll_offset"):
                    game.overworld_tutorial_scroll_offset = 0
                game.overworld_tutorial_scroll_offset = max(0, game.overworld_tutorial_scroll_offset - 20)
                return
            if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                if not hasattr(game, "overworld_tutorial_scroll_offset"):
                    game.overworld_tutorial_scroll_offset = 0
                game.overworld_tutorial_scroll_offset += 20
                return
            if event.key == pygame.K_PAGEUP:
                if not hasattr(game, "overworld_tutorial_scroll_offset"):
                    game.overworld_tutorial_scroll_offset = 0
                game.overworld_tutorial_scroll_offset = max(0, game.overworld_tutorial_scroll_offset - 200)
                return
            if event.key == pygame.K_PAGEDOWN:
                if not hasattr(game, "overworld_tutorial_scroll_offset"):
                    game.overworld_tutorial_scroll_offset = 0
                game.overworld_tutorial_scroll_offset += 200
                return
        
        # Handle discovery log (codex) scrolling and closing
        if getattr(game, "show_discovery_log", False):
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_l:
                game.show_discovery_log = False
                return
            if event.key == pygame.K_UP or event.key == pygame.K_w:
                game.discovery_log_scroll_offset = max(0, getattr(game, "discovery_log_scroll_offset", 0) - 24)
                return
            if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                game.discovery_log_scroll_offset = getattr(game, "discovery_log_scroll_offset", 0) + 24
                return
            if event.key == pygame.K_PAGEUP:
                game.discovery_log_scroll_offset = max(0, getattr(game, "discovery_log_scroll_offset", 0) - 200)
                return
            if event.key == pygame.K_PAGEDOWN:
                game.discovery_log_scroll_offset = getattr(game, "discovery_log_scroll_offset", 0) + 200
                return
            # Block all other input while discovery log is open
            return
        
        # Block input if overlays are open (but tutorial was handled above)
        if game.is_overlay_open():
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
        
        # Join battle (J key)
        if event.key == pygame.K_j:
            if self.try_join_battle():
                return  # Battle joined, don't process other actions
        
        # Interaction (enter POI or interact with party)
        if input_manager is not None:
            if input_manager.event_matches_action(InputAction.INTERACT, event):
                # Check for party interaction first
                if self._try_party_interaction():
                    return
                self.try_enter_poi()
                return
        else:
            if event.key == pygame.K_e:
                # Check for party interaction first
                if self._try_party_interaction():
                    return
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
        
        # Toggle minimap (M key)
        if event.key == pygame.K_m:
            game.show_minimap = not getattr(game, "show_minimap", True)
            return
        
        # Rest (R) - short break: pass time, partial heal
        if input_manager is not None and input_manager.event_matches_action(InputAction.REST, event):
            self._do_rest()
            return
        if input_manager is None and event.key == pygame.K_r:
            self._do_rest()
            return

        # Camp (T) - set up camp: pass more time, full heal
        if input_manager is not None and input_manager.event_matches_action(InputAction.CAMP, event):
            self._do_camp()
            return
        if input_manager is None and event.key == pygame.K_t:
            self._do_camp()
            return

        # Toggle discovery log / codex (L key)
        if event.key == pygame.K_l:
            game.show_discovery_log = not getattr(game, "show_discovery_log", False)
            if getattr(game, "show_discovery_log", False):
                if hasattr(game, "show_overworld_tutorial"):
                    game.show_overworld_tutorial = False
                if not hasattr(game, "discovery_log_scroll_offset"):
                    game.discovery_log_scroll_offset = 0
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
        """Handle mouse wheel events for zooming or tutorial/discovery log scrolling."""
        if event.type == pygame.MOUSEWHEEL:
            game = self.game
            # Handle mouse wheel for tutorial scrolling
            if getattr(game, "show_overworld_tutorial", False):
                if not hasattr(game, "overworld_tutorial_scroll_offset"):
                    game.overworld_tutorial_scroll_offset = 0
                # Scroll tutorial (negative y means scroll up)
                game.overworld_tutorial_scroll_offset = max(0, game.overworld_tutorial_scroll_offset - event.y * 30)
            elif getattr(game, "show_discovery_log", False):
                game.discovery_log_scroll_offset = max(0, getattr(game, "discovery_log_scroll_offset", 0) - event.y * 24)
            else:
                # Normal zoom behavior
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
        
        # Check for party interactions (combat, etc.)
        # Note: Party movement is now handled in try_move() when player moves
        self._check_party_interactions()
    
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
        
        # Get sight radius from config (use cached config to avoid loading on every move)
        if not hasattr(game, "_overworld_config_cache"):
            from world.overworld import OverworldConfig
            game._overworld_config_cache = OverworldConfig.load()
        config = game._overworld_config_cache
        sight_radius = config.sight_radius
        
        # Get current time for exploration tracking
        current_time = None
        if game.time_system is not None:
            current_time = game.time_system.get_total_hours()
        
        # Move player (this will also explore tiles in sight radius)
        if game.overworld_map.set_player_position(new_x, new_y, sight_radius=sight_radius, current_time=current_time):
            self._last_move_time = 0.0
            # Store the direction we moved in (for arrow rendering)
            self.last_direction = direction
            
            # Consume time based on terrain; roads reduce cost (faster travel)
            if game.time_system is not None:
                tile = game.overworld_map.get_tile(new_x, new_y)
                if tile:
                    cost = config.terrain_costs.get(tile.id, config.movement_cost_base)
                    if getattr(game.overworld_map, "road_manager", None) and game.overworld_map.road_manager.has_road_at(new_x, new_y):
                        cost *= config.road_movement_multiplier
                    game.time_system.add_time(cost * config.movement_cost_base)
            
            # Update roaming parties when player moves (turn-based movement)
            if game.overworld_map.party_manager is not None:
                player_level = getattr(game.hero_stats, "level", 1) if hasattr(game, "hero_stats") else 1
                game.overworld_map.party_manager.update_on_player_move(
                    player_level=player_level,
                    player_position=(new_x, new_y),
                )
            
            # Check for nearby POIs to discover (within sight radius)
            nearby_pois = game.overworld_map.get_pois_in_range(new_x, new_y, radius=sight_radius)
            for poi in nearby_pois:
                if not poi.discovered:
                    poi.discover()
                    game.overworld_map.record_discovery(poi)
                    # Better discovery message with type, level, and faction
                    type_label = POI_TYPE_LABELS.get(poi.poi_type, "Location")
                    
                    # Add faction info if available
                    faction_info = ""
                    faction_id = getattr(poi, "faction_id", None)
                    if faction_id and game.overworld_map.faction_manager:
                        faction = game.overworld_map.faction_manager.get_faction(faction_id)
                        if faction:
                            faction_info = f" ({faction.name})"
                    
                    game.add_message(f"You discover {poi.name} - A {type_label} (Level {poi.level}){faction_info}")
            
            # Random events: occasionally spawn temporary POIs (bandit camp, stranded merchant)
            game._overworld_move_count = getattr(game, "_overworld_move_count", 0) + 1
            try:
                from world.overworld.random_events import try_trigger_random_event
                try_trigger_random_event(game)
            except Exception:
                pass
    
    def _do_rest(self) -> None:
        """Rest briefly: pass time, heal partially."""
        self._pass_time_with_heal(is_camp=False)

    def _do_camp(self) -> None:
        """Set up camp: pass more time, full heal."""
        self._pass_time_with_heal(is_camp=True)

    def _pass_time_with_heal(self, is_camp: bool) -> None:
        """
        Pass time in overworld. Advances clock, heals player, optionally ticks parties.

        Args:
            is_camp: If True, camp (longer, full heal). If False, rest (shorter, partial heal).
        """
        game = self.game
        if game.overworld_map is None or game.time_system is None:
            return

        if not hasattr(game, "_overworld_config_cache"):
            from world.overworld import OverworldConfig
            game._overworld_config_cache = OverworldConfig.load()
        config = game._overworld_config_cache

        if is_camp:
            hours = config.camp_hours
            full_heal = True
        else:
            hours = config.rest_hours
            full_heal = False

        # Advance time
        game.time_system.add_time(hours)

        # Heal player
        if game.player is not None and hasattr(game.player, "hp"):
            max_hp = getattr(game.player, "max_hp", getattr(game.hero_stats, "max_hp", 30))
            if full_heal:
                game.player.hp = max_hp
            else:
                heal_amount = max(1, int(max_hp * config.rest_heal_ratio))
                game.player.hp = min(max_hp, game.player.hp + heal_amount)

        # Tick party world (parties move, spawn, etc.) proportionally to time passed
        num_ticks = max(1, int(hours))
        if game.overworld_map.party_manager is not None:
            player_level = getattr(game.hero_stats, "level", 1) if hasattr(game, "hero_stats") else 1
            player_x, player_y = game.overworld_map.get_player_position()
            for _ in range(num_ticks):
                game.overworld_map.party_manager.update_on_player_move(
                    player_level=player_level,
                    player_position=(player_x, player_y),
                )

        # Message
        action_name = "Camp" if is_camp else "Rest"
        if is_camp:
            game.add_message(f"You make camp and rest for {int(hours)} hours. You feel fully restored.")
        else:
            game.add_message(f"You take a short rest for {int(hours)} hours, recovering some strength.")

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
            game.overworld_map.record_discovery(poi)
            # Better discovery message
            type_label = POI_TYPE_LABELS.get(poi.poi_type, "Location")
            game.add_message(f"You discover {poi.name} - A {type_label} (Level {poi.level}). Press E again to enter.")
            return
        
        # Check if can enter
        if not poi.can_enter(game):
            game.add_message(f"You cannot enter {poi.name} right now.")
            return
        
        # Enter the POI (message will be shown by POI.enter())
        game.enter_poi(poi)
    
    def _try_party_interaction(self) -> bool:
        """
        Try to interact with a party at player's position.
        
        Returns:
            True if interaction was opened, False otherwise
        """
        game = self.game
        
        if game.overworld_map is None or game.overworld_map.party_manager is None:
            return False
        
        player_x, player_y = game.overworld_map.get_player_position()
        
        # Check for parties at player position (same tile)
        party_at_player = game.overworld_map.party_manager.get_party_at(player_x, player_y)
        
        if party_at_player:
            self._open_party_interaction(party_at_player)
            return True
        
        # Also check adjacent tiles
        for dx, dy in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
            check_x = player_x + dx
            check_y = player_y + dy
            nearby_party = game.overworld_map.party_manager.get_party_at(check_x, check_y)
            if nearby_party:
                self._open_party_interaction(nearby_party)
                return True
        
        return False
    
    def _open_party_interaction(self, party) -> None:
        """Open the party interaction screen."""
        from world.overworld.party import get_party_type
        from engine.scenes.party_interaction_scene import PartyInteractionScene
        
        party_type = get_party_type(party.party_type_id)
        if party_type is None:
            return
        
        # Create and run interaction scene
        scene = PartyInteractionScene(self.game.screen, party, party_type, self.game)
        action = scene.run()
        
        # Handle the selected action (some actions are handled in the scene)
        if action == "attack":
            # TODO: Trigger combat
            pass
        elif action == "trade":
            # TODO: Open trade screen
            pass
    
    def _check_party_interactions(self) -> None:
        """Check for automatic party interactions (combat, etc.)."""
        # This is now only for automatic interactions, not player-initiated
        pass
    
    def try_join_battle(self) -> bool:
        """
        Try to join a nearby battle.
        
        Returns:
            True if a battle was joined, False otherwise
        """
        game = self.game
        
        if game.overworld_map is None or game.overworld_map.party_manager is None:
            return False
        
        player_x, player_y = game.overworld_map.get_player_position()
        
        # Check for battles within 2 tiles
        nearby_battles = game.overworld_map.party_manager.get_battles_in_range(
            player_x, player_y, radius=2
        )
        
        if not nearby_battles:
            return False
        
        # Get the closest battle
        closest_battle = None
        closest_dist = float('inf')
        for battle in nearby_battles:
            bx, by = battle.position
            dist = max(abs(bx - player_x), abs(by - player_y))
            if dist < closest_dist:
                closest_dist = dist
                closest_battle = battle
        
        if not closest_battle or not closest_battle.can_player_join:
            return False
        
        # Show battle join dialog
        self._show_battle_join_dialog(closest_battle)
        return True
    
    def _show_battle_join_dialog(self, battle) -> None:
        """Show dialog for player to choose which side to join."""
        from engine.scenes.battle_join_scene import BattleJoinScene
        
        scene = BattleJoinScene(self.game.screen, battle, self.game)
        result = scene.run()
        
        if result:
            side, party1, party2 = result
            self._join_battle(battle, side, party1, party2)
    
    def _join_battle(self, battle, side: str, party1, party2) -> None:
        """Join a battle on the specified side."""
        from world.overworld.party import party_to_battle_enemies
        from world.overworld.party import get_party_type
        
        # Mark battle as joined
        battle.player_joined = True
        battle.side_joined = side
        battle.can_player_join = False
        
        # Determine which party is enemy and which is ally
        if side == "party1":
            enemy_party = party2
            ally_party = party1
        else:
            enemy_party = party1
            ally_party = party2
        
        # Get player level
        player_level = 1
        if self.game.player:
            if hasattr(self.game.player, 'level'):
                player_level = self.game.player.level
            elif hasattr(self.game, 'hero_stats') and self.game.hero_stats:
                player_level = getattr(self.game.hero_stats, 'level', 1)
        
        # Convert enemy party to battle enemies
        enemy_party_type = get_party_type(enemy_party.party_type_id)
        if not enemy_party_type:
            return
        
        enemies = party_to_battle_enemies(
            party=enemy_party,
            party_type=enemy_party_type,
            game=self.game,
            player_level=player_level
        )
        
        if not enemies:
            self.game.add_message("Unable to join battle.")
            return
        
        # Start battle (pass ally party so they join as player-side units)
        self.game.add_message(f"You join the battle on {ally_party.party_name if ally_party else 'your own'} side!")
        ally_party_type = get_party_type(ally_party.party_type_id) if ally_party else None
        allied_parties_for_battle = [ally_party] if ally_party and ally_party_type and ally_party_type.can_join_battle else []
        self.game.start_battle_from_overworld(enemies, context_party=enemy_party, allied_parties=allied_parties_for_battle)
        
        # Remove battle from active battles (battle is now player-controlled)
        if hasattr(self.game.overworld_map.party_manager, 'active_battles'):
            if battle.battle_id in self.game.overworld_map.party_manager.active_battles:
                del self.game.overworld_map.party_manager.active_battles[battle.battle_id]
        
        # Mark parties as no longer in combat (player took over)
        if party1:
            party1.in_combat = False
        if party2:
            party2.in_combat = False

