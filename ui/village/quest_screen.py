"""
Quest screen for viewing and accepting quests from NPCs.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import pygame

from ui.fullscreen_screens.quest_screen import draw_quest_fullscreen
from systems.input import InputAction
from systems.quests import QuestStatus

if TYPE_CHECKING:
    from engine.core.game import Game


class QuestScreen:
    """
    Screen wrapper for the quest overlay.
    
    Handles input for:
    - Navigation (arrows/WASD)
    - Accepting quests (Enter/Space)
    - Turning in completed quests (Enter/Space)
    - Quick selection (number keys 1-9)
    - Closing (ESC, E)
    """
    
    def handle_event(self, game: "Game", event: pygame.event.Event) -> None:
        """Handle input events for quest screen."""
        if event.type != pygame.KEYDOWN:
            return
        
        # If the flag is off, ignore input
        if not getattr(game, "show_quests", False):
            return
        
        input_manager = getattr(game, "input_manager", None)
        key = event.key
        
        elder_id = getattr(game, "current_elder_id", None)
        
        # Get quests - if elder_id is None, show all quests; otherwise filter by elder
        from systems.quests import Quest
        available_quests: list[Quest] = [
            q for q in getattr(game, "available_quests", {}).values()
            if q.status == QuestStatus.AVAILABLE and (elder_id is None or q.quest_giver_id == elder_id)
        ]
        
        active_quests: list[Quest] = [
            q for q in getattr(game, "active_quests", {}).values()
            if q.status == QuestStatus.ACTIVE and (elder_id is None or q.quest_giver_id == elder_id)
        ]
        
        completed_quests: list[Quest] = [
            q for q in getattr(game, "active_quests", {}).values()
            if q.status == QuestStatus.COMPLETED and (elder_id is None or q.quest_giver_id == elder_id)
        ]
        
        # Determine which tab we're on
        quest_tab = getattr(game, "quest_tab", "available")  # "available", "active", "completed"
        
        # Get active list based on tab
        if quest_tab == "available":
            active_list = available_quests
        elif quest_tab == "active":
            active_list = active_quests
        elif quest_tab == "completed":
            active_list = completed_quests
        else:
            active_list = available_quests
        
        # --- Close quest screen ---
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
            game.show_quests = False
            game.ui_screen_manager.show_quest_screen = False
            if getattr(game, "active_screen", None) is getattr(game, "quest_screen", None):
                game.active_screen = None
            return
        
        # --- Tab switching ---
        if key == pygame.K_TAB:
            mods = pygame.key.get_mods()
            if mods & pygame.KMOD_SHIFT:
                # Shift+TAB: switch between inner quest tabs (available, active, completed)
                tabs = ["available", "active", "completed"]
                current_index = tabs.index(quest_tab) if quest_tab in tabs else 0
                new_index = (current_index + 1) % len(tabs)
                game.quest_tab = tabs[new_index]
                # Reset cursor when switching tabs
                game.quest_cursor = 0
            else:
                # TAB: switch between main screens (inventory, character, skills, quests, shop, etc.)
                direction = 1  # Next screen
                game.cycle_to_next_screen(direction)
            return
        
        # Quick jump to screens
        if key == pygame.K_i:
            game.switch_to_screen("inventory")
            return
        if key == pygame.K_c:
            game.switch_to_screen("character")
            return
        if key == pygame.K_t:
            game.switch_to_screen("skills")
            return
        
        # --- Ensure cursor is valid ---
        cursor = int(getattr(game, "quest_cursor", 0))
        max_index = len(active_list) - 1
        
        if max_index < 0:
            game.quest_cursor = 0
        else:
            cursor = max(0, min(cursor, max_index))
            game.quest_cursor = cursor
        
        # --- Navigation (UP/W/K and DOWN/S/J) ---
        if input_manager is not None:
            if input_manager.event_matches_action(InputAction.SCROLL_UP, event):
                if max_index >= 0:
                    cursor = (cursor - 1) % (max_index + 1)
                    game.quest_cursor = cursor
                return
            if input_manager.event_matches_action(InputAction.SCROLL_DOWN, event):
                if max_index >= 0:
                    cursor = (cursor + 1) % (max_index + 1)
                    game.quest_cursor = cursor
                return
        else:
            if key in (pygame.K_UP, pygame.K_w, pygame.K_k):
                if max_index >= 0:
                    cursor = (cursor - 1) % (max_index + 1)
                    game.quest_cursor = cursor
                return
            
            if key in (pygame.K_DOWN, pygame.K_s, pygame.K_j):
                if max_index >= 0:
                    cursor = (cursor + 1) % (max_index + 1)
                    game.quest_cursor = cursor
                return
        
        # --- Quick selection with number keys 1–9 ---
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
                if quest_tab == "available":
                    self._attempt_accept_quest(game, active_list[index_from_number].quest_id)
                elif quest_tab == "completed":
                    self._attempt_turn_in_quest(game, active_list[index_from_number].quest_id)
            return
        
        # --- Enter/Space to accept/turn in quest ---
        if input_manager is not None:
            if input_manager.event_matches_action(InputAction.CONFIRM, event):
                if 0 <= cursor < len(active_list):
                    if quest_tab == "available":
                        self._attempt_accept_quest(game, active_list[cursor].quest_id)
                    elif quest_tab == "completed":
                        self._attempt_turn_in_quest(game, active_list[cursor].quest_id)
                return
        else:
            if key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
                if 0 <= cursor < len(active_list):
                    if quest_tab == "available":
                        self._attempt_accept_quest(game, active_list[cursor].quest_id)
                    elif quest_tab == "completed":
                        self._attempt_turn_in_quest(game, active_list[cursor].quest_id)
                return
    
    def _attempt_accept_quest(self, game: "Game", quest_id: str) -> None:
        """Attempt to accept a quest."""
        from systems.village.services import accept_quest
        
        success = accept_quest(game, quest_id)
        
        if success:
            # Update quest lists
            if quest_id in game.available_quests:
                del game.available_quests[quest_id]
            
            # If no more available quests, switch to active tab
            elder_id = getattr(game, "current_elder_id", None)
            available_count = len([
                q for q in getattr(game, "available_quests", {}).values()
                if q.status == QuestStatus.AVAILABLE and (elder_id is None or q.quest_giver_id == elder_id)
            ])
            if available_count == 0:
                active_count = len([
                    q for q in getattr(game, "active_quests", {}).values()
                    if q.status == QuestStatus.ACTIVE and (elder_id is None or q.quest_giver_id == elder_id)
                ])
                if active_count > 0:
                    game.quest_tab = "active"
                else:
                    game.quest_tab = "completed"
                game.quest_cursor = 0
    
    def _attempt_turn_in_quest(self, game: "Game", quest_id: str) -> None:
        """Attempt to turn in a completed quest."""
        from systems.village.services import turn_in_quest
        
        success = turn_in_quest(game, quest_id)
        
        if success:
            # Update quest lists
            # Quest is automatically removed from active_quests by turn_in
            
            # If no more completed quests, switch to appropriate tab
            elder_id = getattr(game, "current_elder_id", None)
            completed_count = len([
                q for q in getattr(game, "active_quests", {}).values()
                if q.status == QuestStatus.COMPLETED and (elder_id is None or q.quest_giver_id == elder_id)
            ])
            if completed_count == 0:
                available_count = len([
                    q for q in getattr(game, "available_quests", {}).values()
                    if q.status == QuestStatus.AVAILABLE and (elder_id is None or q.quest_giver_id == elder_id)
                ])
                active_count = len([
                    q for q in getattr(game, "active_quests", {}).values()
                    if q.status == QuestStatus.ACTIVE and (elder_id is None or q.quest_giver_id == elder_id)
                ])
                if available_count > 0:
                    game.quest_tab = "available"
                elif active_count > 0:
                    game.quest_tab = "active"
                game.quest_cursor = 0
    
    def draw(self, game: "Game") -> None:
        """Render the full-screen quest view."""
        draw_quest_fullscreen(game)

