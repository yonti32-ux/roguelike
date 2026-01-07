"""
Pause menu screen shown when player presses ESC during gameplay.
"""

import pygame
from typing import Optional

from settings import COLOR_BG, FPS
from ..core.config import get_config, save_config


class PauseMenuScene:
    """
    Pause menu screen shown during gameplay.
    
    Options:
    - Resume: continue playing
    - Save Game: open save menu
    - Load Game: open load menu
    - Options: settings/hotkey tutorial
    - Exit to Main Menu: return to main menu
    - Quit Game: exit completely
    """
    
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.font_title = pygame.font.SysFont("consolas", 32)
        self.font_main = pygame.font.SysFont("consolas", 24)
        self.font_small = pygame.font.SysFont("consolas", 18)
        
        # Menu options
        self.options = [
            ("resume", "Resume"),
            ("save", "Save Game"),
            ("load", "Load Game"),
            ("options", "Options / Controls"),
            ("main_menu", "Exit to Main Menu"),
            ("quit", "Quit Game"),
        ]
        self.selected_index = 0
    
    def run(self) -> str | None:
        """
        Main loop for the pause menu scene.
        Returns:
            - "resume": continue playing
            - "save": open save menu
            - "load": open load menu
            - "options": show options/controls
            - "main_menu": return to main menu
            - "quit": quit game
            - None: cancelled/resume
        """
        clock = pygame.time.Clock()
        
        while True:
            dt = clock.tick(FPS) / 1000.0
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                
                if event.type == pygame.KEYDOWN:
                    result = self._handle_keydown(event)
                    if result is not None:
                        return result
            
            self.draw()
            pygame.display.flip()
    
    def _handle_keydown(self, event: pygame.event.Event) -> str | None:
        """Handle key presses in the pause menu."""
        key = event.key
        
        # ESC always resumes (or closes pause menu)
        if key == pygame.K_ESCAPE:
            return "resume"
        
        # Navigation
        if key in (pygame.K_UP, pygame.K_w):
            self.selected_index = (self.selected_index - 1) % len(self.options)
            return None  # stay in menu
        
        if key in (pygame.K_DOWN, pygame.K_s):
            self.selected_index = (self.selected_index + 1) % len(self.options)
            return None  # stay in menu
        
        # Selection
        if key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
            option_id, _ = self.options[self.selected_index]
            return option_id
        
        return None  # no action
    
    def draw(self) -> None:
        """Draw the pause menu screen (semi-transparent overlay)."""
        w, h = self.screen.get_size()
        
        # Draw semi-transparent overlay
        overlay = pygame.Surface((w, h))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # Title
        title_surf = self.font_title.render("PAUSED", True, (255, 255, 210))
        title_x = w // 2 - title_surf.get_width() // 2
        title_y = 120
        self.screen.blit(title_surf, (title_x, title_y))
        
        # Menu options
        menu_start_y = h // 2 - 80
        option_spacing = 50
        
        for idx, (option_id, option_text) in enumerate(self.options):
            is_selected = (idx == self.selected_index)
            
            # Highlight selected option
            if is_selected:
                # Draw selection indicator
                indicator_x = w // 2 - 250
                indicator_y = menu_start_y + idx * option_spacing
                pygame.draw.circle(
                    self.screen,
                    (255, 255, 200),
                    (indicator_x, indicator_y + 12),
                    6
                )
            
            # Option text
            color = (255, 255, 210) if is_selected else (180, 180, 180)
            text_surf = self.font_main.render(option_text, True, color)
            text_x = w // 2 - text_surf.get_width() // 2
            text_y = menu_start_y + idx * option_spacing
            self.screen.blit(text_surf, (text_x, text_y))
        
        # Controls hint
        hint_y = h - 60
        hint_text = "↑/↓: Navigate   Enter: Select   Esc: Resume"
        hint_surf = self.font_small.render(hint_text, True, (150, 150, 150))
        hint_x = w // 2 - hint_surf.get_width() // 2
        self.screen.blit(hint_surf, (hint_x, hint_y))


class OptionsMenuScene:
    """
    Options/Controls screen showing hotkey tutorial and settings.
    """
    
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.font_title = pygame.font.SysFont("consolas", 32)
        self.font_main = pygame.font.SysFont("consolas", 20)
        self.font_small = pygame.font.SysFont("consolas", 16)
        
        # Menu mode: "main" (shows options) or "controls" (shows hotkeys)
        self.mode = "main"  # "main" or "controls"
        self.selected_index = 0
        
        # Battle speed options (multipliers) - must be defined before use
        self.battle_speed_levels = [0.5, 1.0, 1.5, 2.0]
        self.battle_speed_index = 1  # Default to 1.0x (normal speed)
        
        # Load current battle speed from config
        config = get_config()
        current_speed = getattr(config, "battle_speed", 1.0)
        # Find the closest matching speed level
        if current_speed in self.battle_speed_levels:
            self.battle_speed_index = self.battle_speed_levels.index(current_speed)
        else:
            # Find closest match
            self.battle_speed_index = min(
                range(len(self.battle_speed_levels)),
                key=lambda i: abs(self.battle_speed_levels[i] - current_speed)
            )
        
        # Main menu options
        self.main_options = [
            ("controls", "View Controls & Hotkeys"),
            ("battle_speed", "Battle Speed"),  # Will show current speed
            ("resolution", "Change Resolution"),
            ("back", "Back"),
        ]
        
        # Define all hotkeys organized by category
        self.hotkey_sections = [
            ("Movement & Interaction", [
                ("WASD / Arrow Keys", "Move"),
                ("E", "Interact"),
            ]),
            ("UI Screens", [
                ("I", "Inventory"),
                ("C", "Character Sheet"),
                ("T", "Skill Tree"),
                ("K", "Exploration Log"),
                ("L", "Battle Log"),
                ("Tab", "Cycle Screens"),
                ("Q/E", "Cycle Focus (Hero/Companions)"),
            ]),
            ("Save & Load", [
                ("F5", "Quick Save (Slot 1)"),
                ("F6", "Save Menu"),
                ("F7", "Load Menu"),
            ]),
            ("Cheats (Requires F9)", [
                ("F9", "Toggle Cheat Mode"),
                ("F1", "Toggle Map Reveal"),
                ("F2", "Full Heal"),
                ("F3", "+100 Gold"),
                ("F4", "+25 XP"),
                ("F8", "Skip Floor"),
            ]),
            ("Other", [
                ("F11", "Toggle Fullscreen"),
                ("Esc", "Pause Menu"),
            ]),
        ]
    
    def run(self) -> Optional[str]:
        """
        Main loop for the options/controls screen.
        Returns:
            "resolution" if resolution menu should open, None otherwise
        """
        clock = pygame.time.Clock()
        
        while True:
            dt = clock.tick(FPS) / 1000.0
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                
                if event.type == pygame.KEYDOWN:
                    result = self._handle_keydown(event)
                    if result is not None:
                        return result
            
            self.draw()
            pygame.display.flip()
    
    def _handle_keydown(self, event: pygame.event.Event) -> Optional[str]:
        """Handle key presses in options menu."""
        key = event.key
        
        # ESC always goes back/closes options
        if key == pygame.K_ESCAPE:
            if self.mode == "controls":
                self.mode = "main"
                return None
            return "back"  # Explicitly return "back" to close options
        
        if self.mode == "main":
            # Check if battle speed is selected
            option_id, _ = self.main_options[self.selected_index]
            if option_id == "battle_speed":
                # Left/Right arrows adjust battle speed
                if key in (pygame.K_LEFT, pygame.K_a):
                    self.battle_speed_index = (self.battle_speed_index - 1) % len(self.battle_speed_levels)
                    self._apply_battle_speed()
                    return None
                if key in (pygame.K_RIGHT, pygame.K_d):
                    self.battle_speed_index = (self.battle_speed_index + 1) % len(self.battle_speed_levels)
                    self._apply_battle_speed()
                    return None
            
            # Navigation
            if key in (pygame.K_UP, pygame.K_w):
                self.selected_index = (self.selected_index - 1) % len(self.main_options)
                return None
            
            if key in (pygame.K_DOWN, pygame.K_s):
                self.selected_index = (self.selected_index + 1) % len(self.main_options)
                return None
            
            # Selection
            if key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
                option_id, _ = self.main_options[self.selected_index]
                if option_id == "controls":
                    self.mode = "controls"
                    return None
                elif option_id == "resolution":
                    return "resolution"
                elif option_id == "back":
                    return None
        else:
            # In controls view, any key goes back to main
            if key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                self.mode = "main"
                return None
        
        return None
    
    def draw(self) -> None:
        """Draw the options/controls screen."""
        self.screen.fill(COLOR_BG)
        w, h = self.screen.get_size()
        
        if self.mode == "main":
            # Draw main options menu
            title_surf = self.font_title.render("Options", True, (255, 255, 210))
            title_x = w // 2 - title_surf.get_width() // 2
            self.screen.blit(title_surf, (title_x, 40))
            
            # Menu options
            menu_start_y = h // 2 - 60
            option_spacing = 50
            
            for idx, (option_id, option_text) in enumerate(self.main_options):
                is_selected = (idx == self.selected_index)
                
                # Highlight selected option
                if is_selected:
                    indicator_x = w // 2 - 250
                    indicator_y = menu_start_y + idx * option_spacing
                    pygame.draw.circle(
                        self.screen,
                        (255, 255, 200),
                        (indicator_x, indicator_y + 12),
                        6
                    )
                
                # Option text
                color = (255, 255, 210) if is_selected else (180, 180, 180)
                
                # Special handling for battle speed to show current value
                if option_id == "battle_speed":
                    current_speed = self.battle_speed_levels[self.battle_speed_index]
                    display_text = f"Battle Speed: {current_speed:.1f}x"
                else:
                    display_text = option_text
                
                text_surf = self.font_main.render(display_text, True, color)
                text_x = w // 2 - text_surf.get_width() // 2
                text_y = menu_start_y + idx * option_spacing
                self.screen.blit(text_surf, (text_x, text_y))
            
            # Hint
            option_id, _ = self.main_options[self.selected_index]
            if option_id == "battle_speed":
                hint_text = "←/→: Adjust Speed   ↑/↓: Navigate   Esc: Back"
            else:
                hint_text = "↑/↓: Navigate   Enter: Select   Esc: Back"
            hint_surf = self.font_small.render(hint_text, True, (150, 150, 150))
            hint_x = w // 2 - hint_surf.get_width() // 2
            self.screen.blit(hint_surf, (hint_x, h - 40))
        
        else:
            # Draw controls/hotkeys view
            title_surf = self.font_title.render("Controls & Hotkeys", True, (255, 255, 210))
            title_x = w // 2 - title_surf.get_width() // 2
            self.screen.blit(title_surf, (title_x, 40))
            
            # Draw hotkey sections in columns
            section_width = w // 2 - 40
            start_x = 40
            start_y = 100
            section_spacing = 20
            
            current_y = start_y
            col = 0
            
            for section_title, hotkeys in self.hotkey_sections:
                # Section title
                title_color = (220, 220, 180)
                section_surf = self.font_main.render(section_title, True, title_color)
                x = start_x + col * (section_width + 40)
                self.screen.blit(section_surf, (x, current_y))
                current_y += 30
                
                # Hotkeys in this section
                for key_name, description in hotkeys:
                    # Key name (left-aligned)
                    key_surf = self.font_small.render(key_name, True, (200, 200, 200))
                    self.screen.blit(key_surf, (x + 20, current_y))
                    
                    # Description (right-aligned in section)
                    desc_surf = self.font_small.render(description, True, (160, 160, 160))
                    desc_x = x + section_width - desc_surf.get_width() - 20
                    self.screen.blit(desc_surf, (desc_x, current_y))
                    
                    current_y += 24
                
                current_y += section_spacing
                
                # Switch to second column if we've gone too far down
                if current_y > h - 100 and col == 0:
                    col = 1
                    current_y = start_y
            
            # Hint at bottom
            hint_text = "Press Esc, Enter, or Space to return"
            hint_surf = self.font_small.render(hint_text, True, (120, 120, 120))
            hint_x = w // 2 - hint_surf.get_width() // 2
            self.screen.blit(hint_surf, (hint_x, h - 40))
    
    def _apply_battle_speed(self) -> None:
        """Apply the selected battle speed to config and save it."""
        config = get_config()
        config.battle_speed = self.battle_speed_levels[self.battle_speed_index]
        save_config()

