"""
Save/Load menu screen for selecting save slots.
"""

import pygame
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from settings import COLOR_BG, FPS
from ..utils.save_system import list_saves, get_save_path


class SaveMenuScene:
    """
    Menu for selecting save slots (for loading or saving).
    
    Shows available save slots with metadata (floor, hero name, level, etc.)
    """
    
    def __init__(self, screen: pygame.Surface, mode: str = "load") -> None:
        """
        Args:
            screen: pygame.Surface to draw on
            mode: "load" or "save"
        """
        self.screen = screen
        self.mode = mode  # "load" or "save"
        self.font_title = pygame.font.SysFont("consolas", 32)
        self.font_main = pygame.font.SysFont("consolas", 22)
        self.font_small = pygame.font.SysFont("consolas", 16)
        
        self.selected_slot = 1
        self.saves = list_saves()
        
        # Animation timer
        self.animation_timer: float = 0.0
    
    def run(self) -> Optional[int]:
        """
        Main loop for the save/load menu.
        Returns:
            Selected slot number (1-9) if confirmed, None if cancelled
        """
        clock = pygame.time.Clock()
        
        while True:
            dt = clock.tick(FPS) / 1000.0
            self.animation_timer += dt
            
            # Refresh saves list periodically
            if int(self.animation_timer * 2) % 10 == 0:  # Every 5 seconds
                self.saves = list_saves()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                
                if event.type == pygame.KEYDOWN:
                    result = self._handle_keydown(event)
                    if result is not None:
                        return result
            
            self.draw()
            pygame.display.flip()
    
    def _handle_keydown(self, event: pygame.event.Event) -> Optional[int]:
        """Handle key presses in the save/load menu."""
        key = event.key
        
        # Cancel
        if key == pygame.K_ESCAPE or key == pygame.K_q:
            return None
        
        # Slot selection (1-9 keys)
        if pygame.K_1 <= key <= pygame.K_9:
            slot = key - pygame.K_0
            self.selected_slot = slot
            
            # If in save mode and slot is selected, confirm immediately
            # If in load mode, require Enter
            if self.mode == "save":
                return slot
            return None  # Stay in menu, wait for Enter
        
        # Navigation
        if key in (pygame.K_UP, pygame.K_w):
            self.selected_slot = max(1, self.selected_slot - 1)
            return None
        
        if key in (pygame.K_DOWN, pygame.K_s):
            self.selected_slot = min(9, self.selected_slot + 1)
            return None
        
        # Confirm selection
        if key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
            if self.mode == "load":
                # Only allow loading if save exists
                if self.selected_slot in self.saves:
                    return self.selected_slot
            else:  # save mode
                return self.selected_slot
        
        return None
    
    def draw(self) -> None:
        """Draw the save/load menu screen."""
        self.screen.fill(COLOR_BG)
        w, h = self.screen.get_size()
        
        # Title
        title_text = "Load Game" if self.mode == "load" else "Save Game"
        title_surf = self.font_title.render(title_text, True, (255, 255, 210))
        title_x = w // 2 - title_surf.get_width() // 2
        self.screen.blit(title_surf, (title_x, 40))
        
        # Draw save slots (3x3 grid)
        slot_width = 350
        slot_height = 100
        start_x = (w - (slot_width * 3 + 40 * 2)) // 2
        start_y = 120
        
        for slot in range(1, 10):
            row = (slot - 1) // 3
            col = (slot - 1) % 3
            
            x = start_x + col * (slot_width + 40)
            y = start_y + row * (slot_height + 20)
            
            is_selected = (slot == self.selected_slot)
            has_save = slot in self.saves
            
            # Slot background
            bg_color = (40, 40, 50) if is_selected else (25, 25, 30)
            border_color = (255, 255, 200) if is_selected else (100, 100, 100)
            pygame.draw.rect(self.screen, bg_color, (x, y, slot_width, slot_height))
            pygame.draw.rect(self.screen, border_color, (x, y, slot_width, slot_height), 2)
            
            # Slot number
            slot_label = f"Slot {slot}"
            slot_surf = self.font_main.render(slot_label, True, (200, 200, 200))
            self.screen.blit(slot_surf, (x + 10, y + 8))
            
            if has_save:
                save_info = self.saves[slot]
                
                # Hero name
                name_text = save_info.get("hero_name", "Unknown")
                name_surf = self.font_small.render(name_text, True, (255, 255, 200))
                self.screen.blit(name_surf, (x + 10, y + 35))
                
                # Class and level
                class_text = save_info.get("hero_class", "unknown")
                level_text = f"Level {save_info.get('level', 1)}"
                info_text = f"{class_text} - {level_text}"
                info_surf = self.font_small.render(info_text, True, (180, 180, 180))
                self.screen.blit(info_surf, (x + 10, y + 55))
                
                # Floor
                floor_text = f"Floor {save_info.get('floor', 1)}"
                floor_surf = self.font_small.render(floor_text, True, (150, 150, 150))
                self.screen.blit(floor_surf, (x + 10, y + 75))
                
                # Timestamp
                timestamp = save_info.get("timestamp", 0)
                if timestamp:
                    dt = datetime.fromtimestamp(timestamp)
                    time_text = dt.strftime("%Y-%m-%d %H:%M")
                    time_surf = self.font_small.render(time_text, True, (120, 120, 120))
                    time_x = x + slot_width - time_surf.get_width() - 10
                    self.screen.blit(time_surf, (time_x, y + 8))
            else:
                # Empty slot
                empty_text = "Empty" if self.mode == "load" else "Available"
                empty_surf = self.font_small.render(empty_text, True, (100, 100, 100))
                empty_x = x + slot_width // 2 - empty_surf.get_width() // 2
                empty_y = y + slot_height // 2 - empty_surf.get_height() // 2
                self.screen.blit(empty_surf, (empty_x, empty_y))
        
        # Instructions
        if self.mode == "load":
            hint1 = "1-9: Select slot   Enter: Load   Esc: Cancel"
            hint2 = "Only slots with saves can be loaded"
        else:  # save mode
            hint1 = "1-9: Select slot   Enter: Save   Esc: Cancel"
            hint2 = "Saving will overwrite existing saves in that slot"
        
        hint1_surf = self.font_small.render(hint1, True, (150, 150, 150))
        hint2_surf = self.font_small.render(hint2, True, (120, 120, 120))
        hint1_x = w // 2 - hint1_surf.get_width() // 2
        hint2_x = w // 2 - hint2_surf.get_width() // 2
        self.screen.blit(hint1_surf, (hint1_x, h - 60))
        self.screen.blit(hint2_surf, (hint2_x, h - 40))

