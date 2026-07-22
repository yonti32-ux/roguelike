import math
import pygame

from settings import FPS
from typing import List

from .menu_fx import (
    MenuAtmosphere,
    draw_corner_torches,
    draw_menu_option,
    draw_pulsing_hint,
    draw_title_glow,
)


class MainMenuScene:
    """
    Main menu screen shown at game startup.
    
    Options:
    - New Game: starts character creation
    - Load Game: opens save file selection (to be implemented)
    - Quit: exits the game
    """
    
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.font_title = pygame.font.SysFont("consolas", 42, bold=True)
        self.font_main = pygame.font.SysFont("consolas", 24)
        self.font_small = pygame.font.SysFont("consolas", 18)
        
        # Menu options
        self.options = [
            ("new_game", "New Game"),
            ("load_game", "Load Game"),
            ("options", "Options"),
            ("quit", "Quit"),
        ]
        self.selected_index = 0
        
        self.animation_timer: float = 0.0
        self.atmosphere = MenuAtmosphere(screen, intensity=1.15, warm=True)
        
        # Decorative rune-like glyphs that drift slowly behind the title
        self._runes: List[dict] = []
        self._init_runes()
    
    def _init_runes(self) -> None:
        w, h = self.screen.get_size()
        glyphs = ["*", "+", "~", ".", "o", "x", "^"]
        self._runes = []
        for i in range(14):
            self._runes.append({
                "glyph": glyphs[i % len(glyphs)],
                "x": (i * 97 + 40) % max(1, w),
                "y": 40 + (i * 37) % max(1, int(h * 0.35)),
                "phase": i * 0.7,
                "speed": 0.35 + (i % 5) * 0.08,
                "alpha": 35 + (i % 4) * 12,
            })
    
    def run(self) -> str | None:
        """
        Main loop for the main menu scene.
        Returns:
            - "new_game": user wants to start a new game
            - "load_game": user wants to load a game
            - "options": user wants to open options menu
            - "quit": user wants to quit the game
            - None: user closed the window (pygame.QUIT event)
        """
        clock = pygame.time.Clock()
        
        while True:
            dt = clock.tick(FPS) / 1000.0
            self.animation_timer += dt
            self.atmosphere.update(dt)
            w, h = self.screen.get_size()
            self.atmosphere.notify_selection(
                self.selected_index,
                (w // 2, h // 2 - 30 + self.selected_index * 58),
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
    
    def _handle_keydown(self, event: pygame.event.Event) -> str | None:
        """Handle key presses in the main menu."""
        key = event.key
        
        # Global quit shortcut
        if key == pygame.K_q or key == pygame.K_ESCAPE:
            # ESC on "Quit" option confirms, otherwise just selects Quit
            if self.selected_index == len(self.options) - 1:  # Quit is last
                return "quit"
            self.selected_index = len(self.options) - 1
            return None  # stay in menu
        
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
            return option_id  # "new_game", "load_game", "options", or "quit"
        
        return None  # no action
    
    def _draw_runes(self) -> None:
        for rune in self._runes:
            phase = rune["phase"] + self.animation_timer * rune["speed"]
            x = rune["x"] + math.sin(phase) * 18
            y = rune["y"] + math.cos(phase * 0.8) * 10
            alpha = int(rune["alpha"] * (0.55 + 0.45 * abs(math.sin(phase * 1.3))))
            surf = self.font_small.render(rune["glyph"], True, (255, 190, 110))
            surf.set_alpha(alpha)
            self.screen.blit(surf, (int(x), int(y)))
    
    def _draw_floor_glow(self, w: int, h: int) -> None:
        """Warm ground wash under the menu options."""
        glow = pygame.Surface((w, h), pygame.SRCALPHA)
        pulse = 0.5 + 0.5 * math.sin(self.animation_timer * 1.2)
        base_y = int(h * 0.55)
        for i in range(90):
            t = i / 90
            alpha = int((22 + 14 * pulse) * (1.0 - t) * (1.0 - t))
            pygame.draw.ellipse(
                glow,
                (255, 150, 60, alpha),
                (int(w * 0.18), base_y + i, int(w * 0.64), 28),
            )
        self.screen.blit(glow, (0, 0))
    
    def draw(self) -> None:
        """Draw the main menu screen."""
        w, h = self.screen.get_size()
        self.atmosphere.draw_background()
        self._draw_runes()
        self._draw_floor_glow(w, h)
        
        # Title
        title_rect = draw_title_glow(
            self.screen,
            self.font_title,
            "Roguelike Dungeon Crawler",
            (w // 2, 92),
            self.animation_timer,
        )
        
        # Subtitle with fade pulse
        subtitle = "A Roguelike Adventure"
        sub_alpha = int(140 + 70 * abs(math.sin(self.animation_timer * 1.4)))
        subtitle_surf = self.font_small.render(subtitle, True, (220, 200, 160))
        subtitle_surf.set_alpha(sub_alpha)
        subtitle_x = w // 2 - subtitle_surf.get_width() // 2
        self.screen.blit(subtitle_surf, (subtitle_x, title_rect.bottom + 10))
        
        # Decorative divider line under subtitle
        div_w = 160 + int(40 * abs(math.sin(self.animation_timer * 1.1)))
        div_surf = pygame.Surface((div_w, 2), pygame.SRCALPHA)
        div_surf.fill((255, 190, 100, 120))
        self.screen.blit(div_surf, (w // 2 - div_w // 2, title_rect.bottom + 36))
        
        # Menu options
        menu_start_y = h // 2 - 30
        option_spacing = 58
        
        for idx, (_option_id, option_text) in enumerate(self.options):
            is_selected = (idx == self.selected_index)
            text_y = menu_start_y + idx * option_spacing
            draw_menu_option(
                self.screen,
                self.font_main,
                option_text,
                w // 2,
                text_y,
                is_selected,
                self.animation_timer,
                index=idx,
            )
        
        # Controls hint with soft blink
        draw_pulsing_hint(
            self.screen,
            self.font_small,
            "↑/↓: Navigate   Enter: Select   Esc/Q: Quit",
            w // 2,
            h - 58,
            self.animation_timer,
        )
        
        # Version
        version_text = "v 0.4 Alpha"
        version_surf = self.font_small.render(version_text, True, (90, 90, 95))
        self.screen.blit(version_surf, (w - version_surf.get_width() - 20, h - 30))
        
        self.atmosphere.draw_foreground_fx()
        draw_corner_torches(self.screen, self.animation_timer)
    