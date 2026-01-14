"""
Recruitment screen for hiring companions in villages.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import pygame

from ui.fullscreen_screens.recruitment_screen import draw_recruitment_fullscreen
from systems.input import InputAction

if TYPE_CHECKING:
    from engine.core.game import Game


class RecruitmentScreen:
    """
    Screen wrapper for the recruitment overlay.
    
    Handles input for:
    - Navigation (arrows/WASD)
    - Recruiting companions (Enter/Space)
    - Quick recruit (number keys 1-9)
    - Closing (ESC, E)
    """
    
    def handle_event(self, game: "Game", event: pygame.event.Event) -> None:
        """Handle input events for recruitment screen."""
        if event.type != pygame.KEYDOWN:
            return
        
        # If the flag is off, ignore input
        if not getattr(game, "show_recruitment", False):
            return
        
        input_manager = getattr(game, "input_manager", None)
        key = event.key
        
        # Get available companions
        from systems.village.companion_generation import AvailableCompanion
        available_companions: list[AvailableCompanion] = getattr(game, "available_companions", [])
        
        # --- Close recruitment ---
        should_close = False
        if input_manager is not None:
            if (
                input_manager.event_matches_action(InputAction.CANCEL, event)
                or input_manager.event_matches_action(InputAction.INTERACT, event)
            ):
                should_close = True
        else:
            if key in (pygame.K_ESCAPE, pygame.K_e):
                should_close = True
        
        if should_close:
            game.show_recruitment = False
            if getattr(game, "active_screen", None) is getattr(game, "recruitment_screen", None):
                game.active_screen = None
            return
        
        # --- Screen switching with TAB ---
        if key == pygame.K_TAB:
            game.cycle_to_next_screen(1)
            return
        
        # Quick jump to screens
        if key == pygame.K_i:
            game.switch_to_screen("inventory")
            return
        if key == pygame.K_c:
            game.switch_to_screen("character")
            return
        
        # --- Ensure cursor is valid ---
        cursor = int(getattr(game, "recruitment_cursor", 0))
        max_index = len(available_companions) - 1
        
        if max_index < 0:
            game.recruitment_cursor = 0
        else:
            cursor = max(0, min(cursor, max_index))
            game.recruitment_cursor = cursor
        
        # --- Navigation (UP/W/K and DOWN/S/J) ---
        if input_manager is not None:
            if input_manager.event_matches_action(InputAction.SCROLL_UP, event):
                if max_index >= 0:
                    cursor = (cursor - 1) % (max_index + 1)
                    game.recruitment_cursor = cursor
                return
            if input_manager.event_matches_action(InputAction.SCROLL_DOWN, event):
                if max_index >= 0:
                    cursor = (cursor + 1) % (max_index + 1)
                    game.recruitment_cursor = cursor
                return
        else:
            if key in (pygame.K_UP, pygame.K_w, pygame.K_k):
                if max_index >= 0:
                    cursor = (cursor - 1) % (max_index + 1)
                    game.recruitment_cursor = cursor
                return
            
            if key in (pygame.K_DOWN, pygame.K_s, pygame.K_j):
                if max_index >= 0:
                    cursor = (cursor + 1) % (max_index + 1)
                    game.recruitment_cursor = cursor
                return
        
        # --- Quick recruit with number keys 1–9 ---
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
            if 0 <= index_from_number < len(available_companions):
                self._attempt_recruit(game, index_from_number)
            return
        
        # --- Enter/Space to recruit currently highlighted companion ---
        if input_manager is not None:
            if input_manager.event_matches_action(InputAction.CONFIRM, event):
                if 0 <= cursor < len(available_companions):
                    self._attempt_recruit(game, cursor)
                return
        else:
            if key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
                if 0 <= cursor < len(available_companions):
                    self._attempt_recruit(game, cursor)
                return
    
    def _attempt_recruit(self, game: "Game", index: int) -> None:
        """Attempt to recruit the companion at the given index."""
        from systems.village.services import recruit_companion
        from systems.village.companion_generation import AvailableCompanion
        
        available_companions: list[AvailableCompanion] = getattr(game, "available_companions", [])
        
        if index < 0 or index >= len(available_companions):
            return
        
        available_comp = available_companions[index]
        cost = available_comp.recruitment_cost
        
        # Attempt recruitment
        success = recruit_companion(game, index, cost)
        
        if success:
            # Update available companions list
            game.available_companions = game.current_poi.state.get("available_companions", [])
            
            # If no more companions, close screen
            if not game.available_companions:
                game.show_recruitment = False
                if getattr(game, "active_screen", None) is getattr(game, "recruitment_screen", None):
                    game.active_screen = None
    
    def draw(self, game: "Game") -> None:
        """Render the full-screen recruitment view."""
        draw_recruitment_fullscreen(game)

