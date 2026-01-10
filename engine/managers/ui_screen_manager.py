"""
UI Screen and overlay management system.

Handles screen state, toggling overlays, cycling between screens, and focus management.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from ..core.game import Game


class UIScreenManager:
    """
    Manages UI screen state, overlays, and transitions.
    
    Responsibilities:
    - Track which screens/overlays are visible
    - Handle screen switching and cycling
    - Manage focus indices for character/inventory screens
    - Coordinate overlay state (hiding/showing)
    """
    
    def __init__(self) -> None:
        """Initialize the UI screen manager with default state."""
        # Screen visibility flags
        self.show_inventory: bool = False
        self.show_character_sheet: bool = False
        self.show_skill_screen: bool = False
        self.show_quest_screen: bool = False
        self.show_battle_log: bool = False
        self.show_exploration_log: bool = False
        
        # Focus indices (0 = hero, 1+ = companions)
        self.character_sheet_focus_index: int = 0
        self.inventory_focus_index: int = 0
        self.skill_screen_focus_index: int = 0
        
        # Inventory scrolling/cursor
        self.inventory_scroll_offset: int = 0
        self.inventory_cursor: int = 0
    
    def toggle_inventory_overlay(self, game: "Game") -> None:
        """Toggle inventory overlay and manage its active screen."""
        self.show_inventory = not self.show_inventory
        
        if self.show_inventory:
            # Inventory takes focus; hide character sheet & logs
            self.show_character_sheet = False
            self.show_battle_log = False
            self.show_exploration_log = False
            
            # When opening inventory, default focus is hero and reset scroll
            self.inventory_focus_index = 0
            self.inventory_scroll_offset = 0
            self.inventory_cursor = 0
            
            # Route input to inventory screen while open
            if hasattr(game, "inventory_screen"):
                game.active_screen = game.inventory_screen
        else:
            # Closing inventory: if it owned focus, clear active_screen
            if getattr(game, "active_screen", None) is getattr(game, "inventory_screen", None):
                game.active_screen = None
            
            # Clear tooltip when closing inventory
            tooltip = getattr(game, "tooltip", None)
            if tooltip:
                tooltip.clear()
    
    def toggle_character_sheet_overlay(self, game: "Game") -> None:
        """Toggle character sheet overlay and manage its active screen."""
        self.show_character_sheet = not self.show_character_sheet
        
        if self.show_character_sheet:
            # When opening sheet, default focus back to hero
            self.character_sheet_focus_index = 0
            self.show_battle_log = False
            self.show_exploration_log = False
            
            # Route input to character sheet screen while open
            if hasattr(game, "character_sheet_screen"):
                game.active_screen = game.character_sheet_screen
        else:
            # Closing sheet: if it owned focus, clear active_screen
            if getattr(game, "active_screen", None) is getattr(game, "character_sheet_screen", None):
                game.active_screen = None
    
    def toggle_skill_screen(self, game: "Game") -> None:
        """Toggle skill screen overlay and manage its active screen."""
        if self.show_skill_screen:
            # Closing skill screen
            self.show_skill_screen = False
            if getattr(game, "active_screen", None) is game.skill_screen_wrapper:
                game.active_screen = None
        else:
            # Opening skill screen - use switch_to_screen for consistency
            self.switch_to_screen(game, "skills")
    
    def toggle_quest_screen(self, game: "Game") -> None:
        """Toggle quest screen overlay and manage its active screen."""
        self.show_quest_screen = not self.show_quest_screen
        
        if self.show_quest_screen:
            # When opening quest screen, hide other overlays
            self.show_inventory = False
            self.show_character_sheet = False
            self.show_skill_screen = False
            self.show_battle_log = False
            self.show_exploration_log = False
            
            # Initialize quest data if needed
            if not hasattr(game, "active_quests"):
                game.active_quests = {}
            if not hasattr(game, "available_quests"):
                game.available_quests = {}
            if not hasattr(game, "completed_quests"):
                game.completed_quests = {}
            
            # Initialize quest screen state
            if not hasattr(game, "quest_tab"):
                game.quest_tab = "available"
            if not hasattr(game, "quest_cursor"):
                game.quest_cursor = 0
            if not hasattr(game, "current_elder_id"):
                game.current_elder_id = None  # None means show all quests
            
            # Route input to quest screen while open
            if hasattr(game, "quest_screen"):
                game.active_screen = game.quest_screen
                # Set flag for rendering
                game.show_quests = True
        else:
            # Closing quest screen
            if getattr(game, "active_screen", None) is getattr(game, "quest_screen", None):
                game.active_screen = None
            if hasattr(game, "show_quests"):
                game.show_quests = False
    
    def toggle_battle_log_overlay(self, game: "Game") -> None:
        """
        Toggle last battle log overlay ONLY if we actually have one.
        If there is no log, keep it off.
        """
        if not getattr(game, "last_battle_log", None):
            self.show_battle_log = False
            return
        
        self.show_battle_log = not self.show_battle_log
        if self.show_battle_log:
            # Don't stack both log overlays at once
            self.show_exploration_log = False
    
    def toggle_exploration_log_overlay(self, game: "Game") -> None:
        """Toggle the exploration log overlay showing recent messages in exploration mode."""
        self.show_exploration_log = not self.show_exploration_log
        if self.show_exploration_log:
            # Hide battle log when opening exploration log
            self.show_battle_log = False
    
    def get_available_screens(self, game: "Game") -> List[str]:
        """Get list of available screen names (shop only if vendor nearby)."""
        screens = ["inventory", "character", "skills", "quests"]
        if getattr(game, "show_shop", False):
            screens.append("shop")
        if getattr(game, "show_recruitment", False):
            screens.append("recruitment")
        return screens
    
    def switch_to_screen(self, game: "Game", screen_name: str) -> None:
        """Switch to a different full-screen UI."""
        # Close all screen flags
        self.show_inventory = False
        self.show_character_sheet = False
        self.show_skill_screen = False
        self.show_quest_screen = False
        self.show_battle_log = False
        self.show_exploration_log = False
        
        # Open the requested screen
        if screen_name == "inventory":
            self.show_inventory = True
            self.inventory_focus_index = 0
            self.inventory_scroll_offset = 0
            game.active_screen = game.inventory_screen
        elif screen_name == "character":
            self.show_character_sheet = True
            self.character_sheet_focus_index = 0
            game.active_screen = game.character_sheet_screen
        elif screen_name == "skills":
            self.show_skill_screen = True
            self.skill_screen_focus_index = 0
            if hasattr(game.skill_screen, "focus_index"):
                game.skill_screen.focus_index = 0
            if hasattr(game.skill_screen, "reset_selection"):
                game.skill_screen.reset_selection()
            game.active_screen = game.skill_screen_wrapper
        elif screen_name == "shop" and getattr(game, "show_shop", False):
            # Shop is already open (show_shop is True), just set active screen
            game.active_screen = game.shop_screen
        elif screen_name == "recruitment" and getattr(game, "show_recruitment", False):
            # Recruitment is already open, just set active screen
            game.active_screen = game.recruitment_screen
        elif screen_name == "quests":
            # Open quest screen
            self.show_quest_screen = True
            if not hasattr(game, "active_quests"):
                game.active_quests = {}
            if not hasattr(game, "available_quests"):
                game.available_quests = {}
            if not hasattr(game, "completed_quests"):
                game.completed_quests = {}
            if not hasattr(game, "quest_tab"):
                game.quest_tab = "available"
            if not hasattr(game, "quest_cursor"):
                game.quest_cursor = 0
            # Only set current_elder_id to None if not already set (preserves elder context when opened from village)
            if not hasattr(game, "current_elder_id"):
                game.current_elder_id = None
            game.show_quests = True
            game.active_screen = game.quest_screen
        else:
            # Invalid screen, clear active
            game.active_screen = None
    
    def cycle_to_next_screen(self, game: "Game", direction: int = 1) -> None:
        """Cycle to next/previous available screen. direction: 1 for next, -1 for previous."""
        available = self.get_available_screens(game)
        if not available:
            return
        
        # Determine current screen
        current = None
        if self.show_inventory:
            current = "inventory"
        elif self.show_character_sheet:
            current = "character"
        elif self.show_skill_screen:
            current = "skills"
        elif self.show_quest_screen:
            current = "quests"
        elif getattr(game, "show_shop", False) and getattr(game, "active_screen", None) is getattr(game, "shop_screen", None):
            current = "shop"
        elif getattr(game, "show_recruitment", False) and getattr(game, "active_screen", None) is getattr(game, "recruitment_screen", None):
            current = "recruitment"
        
        if current is None:
            # No screen open, open first available
            self.switch_to_screen(game, available[0])
            return
        
        # Find current index and cycle
        try:
            current_idx = available.index(current)
            next_idx = (current_idx + direction) % len(available)
            self.switch_to_screen(game, available[next_idx])
        except ValueError:
            # Current screen not in available list, open first
            self.switch_to_screen(game, available[0])
    
    def cycle_character_sheet_focus(self, game: "Game", direction: int) -> None:
        """
        Cycle which character the character sheet is focusing on.
        
        0 = hero, 1..N = companions in game.party order.
        direction: +1 (next) or -1 (previous).
        """
        party_list = getattr(game, "party", None) or []
        total_slots = 1 + len(party_list)  # hero + companions
        
        if total_slots <= 1:
            # Only hero exists
            self.character_sheet_focus_index = 0
            return
        
        cur = self.character_sheet_focus_index % total_slots
        direction = 1 if direction > 0 else -1
        new_index = (cur + direction) % total_slots
        self.character_sheet_focus_index = new_index
    
    def cycle_inventory_focus(self, game: "Game", direction: int) -> None:
        """
        Cycle which character the inventory overlay is focusing on.
        
        0 = hero, 1..N = companions in game.party order.
        """
        party_list = getattr(game, "party", None) or []
        total_slots = 1 + len(party_list)
        
        if total_slots <= 1:
            self.inventory_focus_index = 0
            return
        
        current = self.inventory_focus_index % total_slots
        # Normalize direction to -1 / +1 so weird values still work
        step = -1 if direction < 0 else 1
        self.inventory_focus_index = (current + step) % total_slots
    
    def is_overlay_open(self) -> bool:
        """
        Return True if a major overlay (inventory, character sheet, skill screen, quest screen) is open.
        Used to pause exploration updates.
        """
        return self.show_inventory or self.show_character_sheet or self.show_skill_screen or self.show_quest_screen

