"""
Pause menu screen shown when player presses ESC during gameplay.
"""

import math
import random
import pygame
from typing import Optional

from settings import FPS
from ..core.config import get_config, save_config
from ui.screen_constants import (
    COLOR_BG_PANEL,
    COLOR_BORDER_BRIGHT,
    COLOR_SHADOW,
    COLOR_GRADIENT_START,
    COLOR_GRADIENT_END,
    COLOR_TITLE,
    COLOR_SUBTITLE,
    COLOR_TEXT,
    COLOR_TEXT_DIM,
    COLOR_SELECTED_BG_BRIGHT,
    SHADOW_OFFSET_X,
    SHADOW_OFFSET_Y,
)
from ui.screen_components import draw_gradient_background


class Particle:
    """A small particle that moves randomly around the screen."""
    
    def __init__(self, screen_width: int, screen_height: int):
        self.x = random.uniform(0, screen_width)
        self.y = random.uniform(0, screen_height)
        self.vx = random.uniform(-20, 20)
        self.vy = random.uniform(-20, 20)
        self.size = random.uniform(1, 2.5)
        color_variants = [
            (150, 170, 200, 180),
            (200, 200, 180, 160),
            (180, 200, 220, 170),
            (220, 220, 200, 150),
            (160, 180, 200, 140),
        ]
        self.color = random.choice(color_variants)
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.direction_change_timer = random.uniform(1.0, 3.0)
        self.direction_timer = 0.0
    
    def update(self, dt: float):
        """Update particle position and velocity."""
        self.direction_timer += dt
        if self.direction_timer >= self.direction_change_timer:
            self.vx += random.uniform(-30, 30) * dt
            self.vy += random.uniform(-30, 30) * dt
            self.vx = max(-40, min(40, self.vx))
            self.vy = max(-40, min(40, self.vy))
            self.direction_timer = 0.0
            self.direction_change_timer = random.uniform(1.0, 3.0)
        self.x += self.vx * dt
        self.y += self.vy * dt
        if self.x < 0:
            self.x = self.screen_width
        elif self.x > self.screen_width:
            self.x = 0
        if self.y < 0:
            self.y = self.screen_height
        elif self.y > self.screen_height:
            self.y = 0
    
    def draw(self, surface: pygame.Surface):
        """Draw the particle."""
        if len(self.color) == 4:
            particle_surf = pygame.Surface((int(self.size * 2), int(self.size * 2)), pygame.SRCALPHA)
            pygame.draw.circle(
                particle_surf,
                self.color,
                (int(self.size), int(self.size)),
                int(self.size)
            )
            surface.blit(particle_surf, (int(self.x - self.size), int(self.y - self.size)))


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
        self.font_title = pygame.font.SysFont("consolas", 36)
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
        
        # Particles for background effect
        w, h = screen.get_size()
        self.particles = [Particle(w, h) for _ in range(40)]
        self.animation_timer = 0.0
    
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
            self.animation_timer += dt
            
            # Update particles
            for particle in self.particles:
                particle.update(dt)
            
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
        """Draw the pause menu screen (semi-transparent overlay with gradient background)."""
        w, h = self.screen.get_size()
        
        # Draw gradient background
        draw_gradient_background(
            self.screen,
            0, 0, w, h,
            COLOR_GRADIENT_START,
            COLOR_GRADIENT_END,
            vertical=True
        )
        
        # Draw particles behind UI
        for particle in self.particles:
            particle.draw(self.screen)
        
        # Draw semi-transparent overlay (very light to show gradient and particles)
        overlay = pygame.Surface((w, h))
        overlay.set_alpha(80)  # Much more transparent to show background clearly
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # Animated title with shadow
        title_text = "PAUSED"
        # Subtle pulse effect
        pulse = int(5 * abs(math.sin(self.animation_timer * 2)))
        title_color = tuple(min(255, c + pulse) for c in COLOR_TITLE)
        title_surf = self.font_title.render(title_text, True, title_color)
        title_shadow = self.font_title.render(title_text, True, COLOR_SHADOW[:3])
        title_x = w // 2 - title_surf.get_width() // 2
        title_y = 100
        
        # Draw shadow
        self.screen.blit(title_shadow, (title_x + SHADOW_OFFSET_X, title_y + SHADOW_OFFSET_Y))
        # Draw title
        self.screen.blit(title_surf, (title_x, title_y))
        
        # Menu options panel (larger for less cramped look)
        menu_start_y = h // 2 - 100
        option_spacing = 55
        menu_width = 600
        menu_height = len(self.options) * option_spacing + 60
        menu_x = w // 2 - menu_width // 2
        menu_panel_y = menu_start_y - 30
        
        # Draw menu panel background with shadow
        shadow_offset = 4
        shadow_panel = pygame.Surface((menu_width + shadow_offset, menu_height + shadow_offset), pygame.SRCALPHA)
        shadow_panel.fill((0, 0, 0, 100))
        self.screen.blit(shadow_panel, (menu_x + shadow_offset, menu_panel_y + shadow_offset))
        
        menu_panel = pygame.Surface((menu_width, menu_height), pygame.SRCALPHA)
        menu_panel.fill(COLOR_BG_PANEL)
        pygame.draw.rect(menu_panel, COLOR_BORDER_BRIGHT, (0, 0, menu_width, menu_height), 2)
        self.screen.blit(menu_panel, (menu_x, menu_panel_y))
        
        # Menu options
        for idx, (option_id, option_text) in enumerate(self.options):
            is_selected = (idx == self.selected_index)
            option_y = menu_start_y + idx * option_spacing
            
            # Draw selection indicator (highlighted background)
            if is_selected:
                indicator_width = menu_width - 20
                indicator_x = menu_x + 10
                indicator_height = 38
                indicator_y = option_y - 6
                
                # Selection background
                selection_surf = pygame.Surface((indicator_width, indicator_height), pygame.SRCALPHA)
                selection_surf.fill(COLOR_SELECTED_BG_BRIGHT)
                self.screen.blit(selection_surf, (indicator_x, indicator_y))
                
                # Left accent border (golden)
                pygame.draw.rect(self.screen, (255, 215, 0), (indicator_x, indicator_y, 4, indicator_height))
            
            # Option text with shadow
            color = COLOR_TITLE if is_selected else COLOR_TEXT
            text_surf = self.font_main.render(option_text, True, color)
            text_shadow = self.font_main.render(option_text, True, COLOR_SHADOW[:3])
            text_x = w // 2 - text_surf.get_width() // 2
            
            # Draw shadow
            self.screen.blit(text_shadow, (text_x + SHADOW_OFFSET_X, option_y + SHADOW_OFFSET_Y))
            # Draw text
            self.screen.blit(text_surf, (text_x, option_y))
        
        # Controls hint panel
        hint_y = h - 80
        hint_text = "↑/↓: Navigate   Enter: Select   Esc: Resume"
        hint_width = 550
        hint_height = 45
        hint_x = w // 2 - hint_width // 2
        
        hint_panel = pygame.Surface((hint_width, hint_height), pygame.SRCALPHA)
        hint_panel.fill(COLOR_BG_PANEL)
        pygame.draw.rect(hint_panel, COLOR_BORDER_BRIGHT, (0, 0, hint_width, hint_height), 2)
        self.screen.blit(hint_panel, (hint_x, hint_y))
        
        hint_surf = self.font_small.render(hint_text, True, COLOR_TEXT)
        hint_text_x = w // 2 - hint_surf.get_width() // 2
        self.screen.blit(hint_surf, (hint_text_x, hint_y + 14))


class OptionsMenuScene:
    """
    Options/Controls screen showing hotkey tutorial and settings.
    """
    
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.font_title = pygame.font.SysFont("consolas", 36)
        self.font_main = pygame.font.SysFont("consolas", 22)
        self.font_small = pygame.font.SysFont("consolas", 16)
        
        # Menu mode: "main" (shows options) or "controls" (shows hotkeys)
        self.mode = "main"  # "main" or "controls"
        self.selected_index = 0
        
        # Particles for background effect
        w, h = screen.get_size()
        self.particles = [Particle(w, h) for _ in range(40)]
        self.animation_timer = 0.0
        
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
        
        # Battle camera speed options (pixels per second)
        self.camera_speed_levels = [25.0, 50.0, 100.0, 150.0, 200.0]
        self.camera_speed_index = 1  # Default to 50.0 (normal speed)
        
        # Load current camera speed from config
        current_camera_speed = getattr(config, "battle_camera_speed", 50.0)
        # Find the closest matching speed level
        if current_camera_speed in self.camera_speed_levels:
            self.camera_speed_index = self.camera_speed_levels.index(current_camera_speed)
        else:
            # Find closest match
            self.camera_speed_index = min(
                range(len(self.camera_speed_levels)),
                key=lambda i: abs(self.camera_speed_levels[i] - current_camera_speed)
            )
        
        # Main menu options
        self.main_options = [
            ("controls", "View Controls & Hotkeys"),
            ("battle_speed", "Battle Speed"),  # Will show current speed
            ("camera_speed", "Battle Camera Speed"),  # Will show current camera speed
            ("resolution", "Change Resolution"),
            ("back", "Back"),
        ]
        
        # Define all hotkeys organized by category
        self.hotkey_sections = [
            ("Movement & Interaction", [
                ("WASD / Arrow Keys", "Move (4-directional)"),
                ("Q/E/Z/C", "Diagonal Movement (Overworld)"),
                ("E", "Interact / Enter POI"),
                ("Q (Exploration)", "Go Up Floor"),
            ]),
            ("UI Screens", [
                ("I", "Inventory"),
                ("C", "Character Sheet"),
                ("J", "Quest Screen"),
                ("T", "Skill Tree (Exploration)"),
                ("K", "Exploration Log"),
                ("L", "Battle Log"),
                ("Tab", "Cycle Screens (Shop)"),
                ("Q/E", "Cycle Focus (Hero/Companions)"),
            ]),
            ("Battle Controls", [
                ("WASD / Arrow Keys", "Move Unit"),
                ("Mouse Click", "Move to Tile"),
                ("Space", "Basic Attack"),
                ("Q/E/F/R", "Skills 1-4"),
                ("G", "Guard"),
                ("Tab", "End Turn"),
            ]),
            ("Save & Load", [
                ("F5", "Quick Save (Slot 1)"),
                ("F6", "Save Menu"),
                ("F7", "Load Menu"),
            ]),
            ("Cheats - Universal (F9)", [
                ("F9", "Toggle Cheat Mode"),
                ("F2", "Heal Player"),
                ("F3", "+100 Gold"),
                ("F4", "+25 XP"),
            ]),
            ("Cheats - Overworld", [
                ("F1", "Reveal Map"),
                ("F5", "Teleport to POI"),
                ("F6", "Teleport to Center"),
            ]),
            ("Cheats - Exploration", [
                ("F1", "Toggle Map Reveal"),
                ("F8", "Skip Floor"),
            ]),
            ("Cheats - Battle", [
                ("F1", "Kill All Enemies"),
                ("F2", "Heal All Players"),
                ("F5", "Heal All Units"),
                ("F6", "Refill Resources"),
                ("F7", "Skip Turn"),
                ("F8", "Win Battle"),
            ]),
            ("Debug & System", [
                ("F10", "Debug Sprites (No F9)"),
                ("F11", "Toggle Fullscreen"),
                ("F12 / ~", "Debug Console"),
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
            self.animation_timer += dt
            
            # Update particles
            for particle in self.particles:
                particle.update(dt)
            
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
            # Check if battle speed or camera speed is selected
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
            elif option_id == "camera_speed":
                # Left/Right arrows adjust camera speed
                if key in (pygame.K_LEFT, pygame.K_a):
                    self.camera_speed_index = (self.camera_speed_index - 1) % len(self.camera_speed_levels)
                    self._apply_camera_speed()
                    return None
                if key in (pygame.K_RIGHT, pygame.K_d):
                    self.camera_speed_index = (self.camera_speed_index + 1) % len(self.camera_speed_levels)
                    self._apply_camera_speed()
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
        w, h = self.screen.get_size()
        
        # Draw gradient background
        draw_gradient_background(
            self.screen,
            0, 0, w, h,
            COLOR_GRADIENT_START,
            COLOR_GRADIENT_END,
            vertical=True
        )
        
        # Draw particles behind UI
        for particle in self.particles:
            particle.draw(self.screen)
        
        if self.mode == "main":
            # Draw main options menu
            # Animated title with shadow
            title_text = "Options"
            pulse = int(5 * abs(math.sin(self.animation_timer * 2)))
            title_color = tuple(min(255, c + pulse) for c in COLOR_TITLE)
            title_surf = self.font_title.render(title_text, True, title_color)
            title_shadow = self.font_title.render(title_text, True, COLOR_SHADOW[:3])
            title_x = w // 2 - title_surf.get_width() // 2
            title_y = 60
            
            # Draw shadow
            self.screen.blit(title_shadow, (title_x + SHADOW_OFFSET_X, title_y + SHADOW_OFFSET_Y))
            # Draw title
            self.screen.blit(title_surf, (title_x, title_y))
            
            # Menu options panel
            menu_start_y = h // 2 - 60
            option_spacing = 50
            menu_width = 550
            menu_height = len(self.main_options) * option_spacing + 40
            menu_x = w // 2 - menu_width // 2
            menu_panel_y = menu_start_y - 20
            
            # Draw menu panel background with shadow
            shadow_offset = 4
            shadow_panel = pygame.Surface((menu_width + shadow_offset, menu_height + shadow_offset), pygame.SRCALPHA)
            shadow_panel.fill((0, 0, 0, 100))
            self.screen.blit(shadow_panel, (menu_x + shadow_offset, menu_panel_y + shadow_offset))
            
            menu_panel = pygame.Surface((menu_width, menu_height), pygame.SRCALPHA)
            menu_panel.fill(COLOR_BG_PANEL)
            pygame.draw.rect(menu_panel, COLOR_BORDER_BRIGHT, (0, 0, menu_width, menu_height), 2)
            self.screen.blit(menu_panel, (menu_x, menu_panel_y))
            
            for idx, (option_id, option_text) in enumerate(self.main_options):
                is_selected = (idx == self.selected_index)
                option_y = menu_start_y + idx * option_spacing
                
                # Draw selection indicator (highlighted background)
                if is_selected:
                    indicator_width = menu_width - 40
                    indicator_x = menu_x + 20
                    indicator_height = 42
                    indicator_y = option_y - 8
                    
                    # Selection background
                    selection_surf = pygame.Surface((indicator_width, indicator_height), pygame.SRCALPHA)
                    selection_surf.fill(COLOR_SELECTED_BG_BRIGHT)
                    self.screen.blit(selection_surf, (indicator_x, indicator_y))
                    
                    # Left accent border (golden)
                    pygame.draw.rect(self.screen, (255, 215, 0), (indicator_x, indicator_y, 4, indicator_height))
                
                # Special handling for battle speed and camera speed to show current value
                if option_id == "battle_speed":
                    current_speed = self.battle_speed_levels[self.battle_speed_index]
                    display_text = f"Battle Speed: {current_speed:.1f}x"
                elif option_id == "camera_speed":
                    current_speed = self.camera_speed_levels[self.camera_speed_index]
                    display_text = f"Battle Camera Speed: {current_speed:.0f} px/s"
                else:
                    display_text = option_text
                
                # Option text with shadow
                color = COLOR_TITLE if is_selected else COLOR_TEXT
                text_surf = self.font_main.render(display_text, True, color)
                text_shadow = self.font_main.render(display_text, True, COLOR_SHADOW[:3])
                text_x = w // 2 - text_surf.get_width() // 2
                
                # Draw shadow
                self.screen.blit(text_shadow, (text_x + SHADOW_OFFSET_X, option_y + SHADOW_OFFSET_Y))
                # Draw text
                self.screen.blit(text_surf, (text_x, option_y))
            
            # Hint panel
            option_id, _ = self.main_options[self.selected_index]
            if option_id in ("battle_speed", "camera_speed"):
                hint_text = "←/→: Adjust Speed   ↑/↓: Navigate   Esc: Back"
            else:
                hint_text = "↑/↓: Navigate   Enter: Select   Esc: Back"
            
            hint_y = h - 80
            hint_width = 600
            hint_height = 45
            hint_x = w // 2 - hint_width // 2
            
            hint_panel = pygame.Surface((hint_width, hint_height), pygame.SRCALPHA)
            hint_panel.fill(COLOR_BG_PANEL)
            pygame.draw.rect(hint_panel, COLOR_BORDER_BRIGHT, (0, 0, hint_width, hint_height), 2)
            self.screen.blit(hint_panel, (hint_x, hint_y))
            
            hint_surf = self.font_small.render(hint_text, True, COLOR_TEXT)
            hint_text_x = w // 2 - hint_surf.get_width() // 2
            self.screen.blit(hint_surf, (hint_text_x, hint_y + 14))
        
        else:
            # Draw controls/hotkeys view
            title_text = "Controls & Hotkeys"
            pulse = int(5 * abs(math.sin(self.animation_timer * 2)))
            title_color = tuple(min(255, c + pulse) for c in COLOR_TITLE)
            title_surf = self.font_title.render(title_text, True, title_color)
            title_shadow = self.font_title.render(title_text, True, COLOR_SHADOW[:3])
            title_x = w // 2 - title_surf.get_width() // 2
            title_y = 60
            
            # Draw shadow
            self.screen.blit(title_shadow, (title_x + SHADOW_OFFSET_X, title_y + SHADOW_OFFSET_Y))
            # Draw title
            self.screen.blit(title_surf, (title_x, title_y))
            
            # Draw hotkey sections in columns with panels
            section_width = w // 2 - 60
            start_x = 30
            start_y = 120
            section_spacing = 25
            
            current_y = start_y
            col = 0
            
            for section_title, hotkeys in self.hotkey_sections:
                x = start_x + col * (section_width + 60)
                
                # Section panel
                section_height = 30 + len(hotkeys) * 24 + 10
                section_panel = pygame.Surface((section_width, section_height), pygame.SRCALPHA)
                section_panel.fill((*COLOR_BG_PANEL[:3], 200))
                pygame.draw.rect(section_panel, COLOR_BORDER_BRIGHT, (0, 0, section_width, section_height), 1)
                self.screen.blit(section_panel, (x, current_y))
                
                # Section title
                section_surf = self.font_main.render(section_title, True, COLOR_SUBTITLE)
                self.screen.blit(section_surf, (x + 10, current_y + 8))
                current_y += 35
                
                # Hotkeys in this section
                for key_name, description in hotkeys:
                    # Key name (left-aligned)
                    key_surf = self.font_small.render(key_name, True, COLOR_TEXT)
                    self.screen.blit(key_surf, (x + 20, current_y))
                    
                    # Description (right-aligned in section)
                    desc_surf = self.font_small.render(description, True, COLOR_TEXT_DIM)
                    desc_x = x + section_width - desc_surf.get_width() - 20
                    self.screen.blit(desc_surf, (desc_x, current_y))
                    
                    current_y += 24
                
                current_y += section_spacing
                
                # Switch to second column if we've gone too far down
                if current_y > h - 120 and col == 0:
                    col = 1
                    current_y = start_y
            
            # Hint panel at bottom
            hint_text = "Press Esc, Enter, or Space to return"
            hint_y = h - 80
            hint_width = 500
            hint_height = 45
            hint_x = w // 2 - hint_width // 2
            
            hint_panel = pygame.Surface((hint_width, hint_height), pygame.SRCALPHA)
            hint_panel.fill(COLOR_BG_PANEL)
            pygame.draw.rect(hint_panel, COLOR_BORDER_BRIGHT, (0, 0, hint_width, hint_height), 2)
            self.screen.blit(hint_panel, (hint_x, hint_y))
            
            hint_surf = self.font_small.render(hint_text, True, COLOR_TEXT)
            hint_text_x = w // 2 - hint_surf.get_width() // 2
            self.screen.blit(hint_surf, (hint_text_x, hint_y + 14))
    
    def _apply_battle_speed(self) -> None:
        """Apply the selected battle speed to config and save it."""
        config = get_config()
        config.battle_speed = self.battle_speed_levels[self.battle_speed_index]
        save_config()
    
    def _apply_camera_speed(self) -> None:
        """Apply the selected camera speed to config and save it."""
        config = get_config()
        config.battle_camera_speed = self.camera_speed_levels[self.camera_speed_index]
        save_config()

