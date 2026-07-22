"""
Pause menu screen shown when player presses ESC during gameplay.
"""

import math
import pygame
from typing import Optional

from settings import FPS
from ..core.config import get_config, save_config
from .menu_fx import (
    MenuAtmosphere,
    draw_corner_torches,
    draw_menu_option,
    draw_pulsing_hint,
    draw_title_glow,
)


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
        self.font_title = pygame.font.SysFont("consolas", 32, bold=True)
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
        self.animation_timer = 0.0
        self.atmosphere = MenuAtmosphere(screen, intensity=0.55, warm=True)
        self._backdrop: pygame.Surface | None = None
    
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
        # Freeze the gameplay frame so the dim overlay doesn't stack darker each frame
        self._backdrop = self.screen.copy()
        clock = pygame.time.Clock()
        
        while True:
            dt = clock.tick(FPS) / 1000.0
            self.animation_timer += dt
            self.atmosphere.update(dt)
            w, h = self.screen.get_size()
            self.atmosphere.notify_selection(
                self.selected_index,
                (w // 2, h // 2 - 80 + self.selected_index * 50),
            )
            
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
            from engine.audio import play_sound
            play_sound("ui_move")
            return None  # stay in menu
        
        if key in (pygame.K_DOWN, pygame.K_s):
            self.selected_index = (self.selected_index + 1) % len(self.options)
            from engine.audio import play_sound
            play_sound("ui_move")
            return None  # stay in menu
        
        # Selection
        if key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
            from engine.audio import play_sound
            play_sound("ui_confirm")
            option_id, _ = self.options[self.selected_index]
            return option_id
        
        return None  # no action
    
    def draw(self) -> None:
        """Draw the pause menu screen (semi-transparent overlay)."""
        w, h = self.screen.get_size()
        
        if self._backdrop is not None:
            self.screen.blit(self._backdrop, (0, 0))
        
        # Draw semi-transparent overlay once on top of frozen gameplay
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        self.atmosphere.draw_overlay_only()
        
        # Title
        draw_title_glow(
            self.screen,
            self.font_title,
            "PAUSED",
            (w // 2, 130),
            self.animation_timer,
            glow_color=(180, 200, 255),
        )
        
        # Menu options
        menu_start_y = h // 2 - 80
        option_spacing = 50
        
        for idx, (_option_id, option_text) in enumerate(self.options):
            draw_menu_option(
                self.screen,
                self.font_main,
                option_text,
                w // 2,
                menu_start_y + idx * option_spacing,
                idx == self.selected_index,
                self.animation_timer,
                index=idx,
            )
        
        draw_pulsing_hint(
            self.screen,
            self.font_small,
            "↑/↓: Navigate   Enter: Select   Esc: Resume",
            w // 2,
            h - 60,
            self.animation_timer,
        )
        self.atmosphere.draw_foreground_fx()
        draw_corner_torches(self.screen, self.animation_timer)

class OptionsMenuScene:
    """
    Options/Controls screen showing hotkey tutorial and settings.
    """
    
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.font_title = pygame.font.SysFont("consolas", 32, bold=True)
        self.font_main = pygame.font.SysFont("consolas", 20)
        self.font_small = pygame.font.SysFont("consolas", 16)
        
        # Menu mode: "main" | "controls" | "audio"
        self.mode = "main"
        self.selected_index = 0
        self.animation_timer = 0.0
        self.atmosphere = MenuAtmosphere(screen, intensity=0.65, warm=True)
        
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

        # Audio volume steps (0% .. 100%)
        self.volume_levels = [i / 10.0 for i in range(0, 11)]
        self.master_volume_index = self._volume_index(getattr(config, "master_volume", 1.0))
        self.music_volume_index = self._volume_index(getattr(config, "music_volume", 0.7))
        self.sfx_volume_index = self._volume_index(getattr(config, "sfx_volume", 0.85))
        self.audio_muted = bool(getattr(config, "audio_muted", False))
        
        # Main menu options
        self.main_options = [
            ("controls", "View Controls & Hotkeys"),
            ("audio", "Audio"),
            ("battle_speed", "Battle Speed"),  # Will show current speed
            ("camera_speed", "Battle Camera Speed"),  # Will show current camera speed
            ("resolution", "Change Resolution"),
            ("back", "Back"),
        ]

        self.audio_options = [
            ("master_volume", "Master Volume"),
            ("music_volume", "Music Volume"),
            ("sfx_volume", "Sound Effects"),
            ("mute", "Mute All"),
            ("back", "Back"),
        ]        
        # Define all hotkeys organized by category
        self.hotkey_sections = [
            ("Movement & Interaction", [
                ("WASD / Arrow Keys", "Move"),
                ("E", "Interact"),
                ("F", "Use Stairs"),
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

    @staticmethod
    def _volume_index(value: float) -> int:
        """Snap a 0..1 volume to the nearest 10% step."""
        levels = [i / 10.0 for i in range(0, 11)]
        return min(range(len(levels)), key=lambda i: abs(levels[i] - float(value)))

    def _audio_option_list(self):
        return self.audio_options

    def _nudge_volume(self, which: str, delta: int) -> None:
        if which == "master_volume":
            self.master_volume_index = max(0, min(10, self.master_volume_index + delta))
        elif which == "music_volume":
            self.music_volume_index = max(0, min(10, self.music_volume_index + delta))
        elif which == "sfx_volume":
            self.sfx_volume_index = max(0, min(10, self.sfx_volume_index + delta))
        self._apply_audio_settings(preview_sfx=(which in ("sfx_volume", "master_volume")))

    def _apply_audio_settings(self, *, preview_sfx: bool = False) -> None:
        config = get_config()
        config.master_volume = self.volume_levels[self.master_volume_index]
        config.music_volume = self.volume_levels[self.music_volume_index]
        config.sfx_volume = self.volume_levels[self.sfx_volume_index]
        config.audio_muted = self.audio_muted
        save_config()
        from engine.audio import apply_audio_settings, play_sound
        apply_audio_settings(config)
        if preview_sfx and not self.audio_muted:
            play_sound("ui_move")
    
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
            self.atmosphere.update(dt)
            w, h = self.screen.get_size()
            self.atmosphere.notify_selection(
                self.selected_index,
                (w // 2, h // 2 - 60 + self.selected_index * 50),
            )
            
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
            if self.mode in ("controls", "audio"):
                self.mode = "main"
                self.selected_index = 0
                return None
            return "back"  # Explicitly return "back" to close options
        
        if self.mode == "audio":
            return self._handle_audio_keydown(key)

        if self.mode == "main":
            # Check if battle speed or camera speed is selected
            option_id, _ = self.main_options[self.selected_index]
            if option_id == "battle_speed":
                # Left/Right arrows adjust battle speed
                if key in (pygame.K_LEFT, pygame.K_a):
                    self.battle_speed_index = (self.battle_speed_index - 1) % len(self.battle_speed_levels)
                    self._apply_battle_speed()
                    w, h = self.screen.get_size()
                    self.atmosphere.spawn_burst(w // 2, h // 2 - 60 + self.selected_index * 50, count=6)
                    return None
                if key in (pygame.K_RIGHT, pygame.K_d):
                    self.battle_speed_index = (self.battle_speed_index + 1) % len(self.battle_speed_levels)
                    self._apply_battle_speed()
                    w, h = self.screen.get_size()
                    self.atmosphere.spawn_burst(w // 2, h // 2 - 60 + self.selected_index * 50, count=6)
                    return None
            elif option_id == "camera_speed":
                # Left/Right arrows adjust camera speed
                if key in (pygame.K_LEFT, pygame.K_a):
                    self.camera_speed_index = (self.camera_speed_index - 1) % len(self.camera_speed_levels)
                    self._apply_camera_speed()
                    w, h = self.screen.get_size()
                    self.atmosphere.spawn_burst(w // 2, h // 2 - 60 + self.selected_index * 50, count=6)
                    return None
                if key in (pygame.K_RIGHT, pygame.K_d):
                    self.camera_speed_index = (self.camera_speed_index + 1) % len(self.camera_speed_levels)
                    self._apply_camera_speed()
                    w, h = self.screen.get_size()
                    self.atmosphere.spawn_burst(w // 2, h // 2 - 60 + self.selected_index * 50, count=6)
                    return None
            
            # Navigation
            if key in (pygame.K_UP, pygame.K_w):
                self.selected_index = (self.selected_index - 1) % len(self.main_options)
                from engine.audio import play_sound
                play_sound("ui_move")
                return None
            
            if key in (pygame.K_DOWN, pygame.K_s):
                self.selected_index = (self.selected_index + 1) % len(self.main_options)
                from engine.audio import play_sound
                play_sound("ui_move")
                return None
            
            # Selection
            if key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
                option_id, _ = self.main_options[self.selected_index]
                from engine.audio import play_sound
                play_sound("ui_confirm")
                if option_id == "controls":
                    self.mode = "controls"
                    return None
                elif option_id == "audio":
                    self.mode = "audio"
                    self.selected_index = 0
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

    def _handle_audio_keydown(self, key: int) -> Optional[str]:
        options = self._audio_option_list()
        option_id, _ = options[self.selected_index]

        if key in (pygame.K_UP, pygame.K_w):
            self.selected_index = (self.selected_index - 1) % len(options)
            from engine.audio import play_sound
            play_sound("ui_move")
            return None
        if key in (pygame.K_DOWN, pygame.K_s):
            self.selected_index = (self.selected_index + 1) % len(options)
            from engine.audio import play_sound
            play_sound("ui_move")
            return None

        if option_id in ("master_volume", "music_volume", "sfx_volume"):
            if key in (pygame.K_LEFT, pygame.K_a):
                self._nudge_volume(option_id, -1)
                w, h = self.screen.get_size()
                self.atmosphere.spawn_burst(w // 2, h // 2 - 40 + self.selected_index * 48, count=5)
                return None
            if key in (pygame.K_RIGHT, pygame.K_d):
                self._nudge_volume(option_id, 1)
                w, h = self.screen.get_size()
                self.atmosphere.spawn_burst(w // 2, h // 2 - 40 + self.selected_index * 48, count=5)
                return None

        if key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
            from engine.audio import play_sound
            if option_id == "mute":
                self.audio_muted = not self.audio_muted
                self._apply_audio_settings()
                if not self.audio_muted:
                    play_sound("ui_confirm")
                return None
            if option_id == "back":
                play_sound("ui_confirm")
                self.mode = "main"
                self.selected_index = 0
                return None

        return None    
    def draw(self) -> None:
        """Draw the options/controls screen."""
        w, h = self.screen.get_size()
        self.atmosphere.draw_background()
        
        if self.mode == "main":
            draw_title_glow(
                self.screen,
                self.font_title,
                "Options",
                (w // 2, 55),
                self.animation_timer,
            )
            
            # Menu options
            menu_start_y = h // 2 - 60
            option_spacing = 50
            
            for idx, (option_id, option_text) in enumerate(self.main_options):
                # Special handling for battle speed and camera speed to show current value
                if option_id == "battle_speed":
                    current_speed = self.battle_speed_levels[self.battle_speed_index]
                    display_text = f"Battle Speed: {current_speed:.1f}x"
                elif option_id == "camera_speed":
                    current_speed = self.camera_speed_levels[self.camera_speed_index]
                    display_text = f"Battle Camera Speed: {current_speed:.0f} px/s"
                else:
                    display_text = option_text
                
                draw_menu_option(
                    self.screen,
                    self.font_main,
                    display_text,
                    w // 2,
                    menu_start_y + idx * option_spacing,
                    idx == self.selected_index,
                    self.animation_timer,
                    index=idx,
                )
            
            # Hint
            option_id, _ = self.main_options[self.selected_index]
            if option_id in ("battle_speed", "camera_speed"):
                hint_text = "←/→: Adjust Speed   ↑/↓: Navigate   Esc: Back"
            else:
                hint_text = "↑/↓: Navigate   Enter: Select   Esc: Back"
            draw_pulsing_hint(self.screen, self.font_small, hint_text, w // 2, h - 40, self.animation_timer)

        elif self.mode == "audio":
            draw_title_glow(
                self.screen,
                self.font_title,
                "Audio",
                (w // 2, 55),
                self.animation_timer,
            )

            menu_start_y = h // 2 - 40
            option_spacing = 48
            for idx, (option_id, option_text) in enumerate(self.audio_options):
                if option_id == "master_volume":
                    pct = int(self.volume_levels[self.master_volume_index] * 100)
                    display_text = f"Master Volume: {pct}%"
                elif option_id == "music_volume":
                    pct = int(self.volume_levels[self.music_volume_index] * 100)
                    display_text = f"Music Volume: {pct}%"
                elif option_id == "sfx_volume":
                    pct = int(self.volume_levels[self.sfx_volume_index] * 100)
                    display_text = f"Sound Effects: {pct}%"
                elif option_id == "mute":
                    display_text = f"Mute All: {'On' if self.audio_muted else 'Off'}"
                else:
                    display_text = option_text

                draw_menu_option(
                    self.screen,
                    self.font_main,
                    display_text,
                    w // 2,
                    menu_start_y + idx * option_spacing,
                    idx == self.selected_index,
                    self.animation_timer,
                    index=idx,
                )

            option_id, _ = self.audio_options[self.selected_index]
            if option_id in ("master_volume", "music_volume", "sfx_volume"):
                hint_text = "←/→: Adjust Volume   ↑/↓: Navigate   Esc: Back"
            elif option_id == "mute":
                hint_text = "Enter: Toggle Mute   ↑/↓: Navigate   Esc: Back"
            else:
                hint_text = "↑/↓: Navigate   Enter: Select   Esc: Back"
            draw_pulsing_hint(self.screen, self.font_small, hint_text, w // 2, h - 40, self.animation_timer)
        
        else:
            draw_title_glow(
                self.screen,
                self.font_title,
                "Controls & Hotkeys",
                (w // 2, 55),
                self.animation_timer,
            )
            
            # Draw hotkey sections in columns
            section_width = w // 2 - 40
            start_x = 40
            start_y = 100
            section_spacing = 20
            
            current_y = start_y
            col = 0
            
            for section_title, hotkeys in self.hotkey_sections:
                # Section title
                pulse = 0.85 + 0.15 * abs(math.sin(self.animation_timer * 1.2 + col))
                title_color = (int(220 * pulse), int(210 * pulse), int(170 * pulse))
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
            draw_pulsing_hint(
                self.screen,
                self.font_small,
                "Press Esc, Enter, or Space to return",
                w // 2,
                h - 40,
                self.animation_timer,
            )
        
        self.atmosphere.draw_foreground_fx()
        draw_corner_torches(self.screen, self.animation_timer)

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

