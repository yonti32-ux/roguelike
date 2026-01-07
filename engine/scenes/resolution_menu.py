"""
Resolution selection menu.
"""

import pygame
from typing import Optional, Tuple

from settings import COLOR_BG, FPS
from ..core.config import get_config, save_config


# Common resolutions
COMMON_RESOLUTIONS = [
    (1024, 576),   # 16:9
    (1280, 720),   # 720p HD
    (1366, 768),   # Common laptop
    (1600, 900),   # 16:9
    (1920, 1080),  # 1080p Full HD
    (2560, 1440),  # 1440p QHD
    (3840, 2160),  # 4K UHD
]


class ResolutionMenuScene:
    """
    Menu for selecting game resolution.
    """
    
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.font_title = pygame.font.SysFont("consolas", 32)
        self.font_main = pygame.font.SysFont("consolas", 22)
        self.font_small = pygame.font.SysFont("consolas", 18)
        
        self.config = get_config()
        
        # Build resolution options
        self.resolutions = []
        
        # First option: Match Desktop
        self.resolutions.append(("desktop", "Match Desktop Resolution", None))
        
        # Then common resolutions
        for width, height in COMMON_RESOLUTIONS:
            label = f"{width} x {height}"
            self.resolutions.append((f"{width}x{height}", label, (width, height)))
        
        # Find current selection
        self.selected_index = 0
        if self.config.match_desktop:
            self.selected_index = 0
        else:
            current_res = (self.config.width, self.config.height)
            for idx, (res_id, label, res) in enumerate(self.resolutions):
                if res == current_res:
                    self.selected_index = idx
                    break
    
    def run(self) -> Optional[Tuple[int, int, bool]]:
        """
        Main loop for resolution selection.
        Returns:
            (width, height, match_desktop) if confirmed, None if cancelled
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
    
    def _handle_keydown(self, event: pygame.event.Event) -> Optional[Tuple[int, int, bool]]:
        """Handle key presses."""
        key = event.key
        
        # Cancel
        if key == pygame.K_ESCAPE:
            return None
        
        # Navigation
        if key in (pygame.K_UP, pygame.K_w):
            self.selected_index = (self.selected_index - 1) % len(self.resolutions)
            return None
        
        if key in (pygame.K_DOWN, pygame.K_s):
            self.selected_index = (self.selected_index + 1) % len(self.resolutions)
            return None
        
        # Selection
        if key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
            res_id, label, res = self.resolutions[self.selected_index]
            
            if res_id == "desktop":
                # Match desktop
                info = pygame.display.Info()
                width, height = info.current_w, info.current_h
                self.config.match_desktop = True
                self.config.width = width
                self.config.height = height
            else:
                # Specific resolution
                width, height = res
                self.config.match_desktop = False
                self.config.width = width
                self.config.height = height
            
            # Save config
            save_config()
            
            return (self.config.width, self.config.height, self.config.match_desktop)
        
        return None
    
    def draw(self) -> None:
        """Draw the resolution selection menu."""
        self.screen.fill(COLOR_BG)
        w, h = self.screen.get_size()
        
        # Title
        title_surf = self.font_title.render("Resolution Settings", True, (255, 255, 210))
        title_x = w // 2 - title_surf.get_width() // 2
        self.screen.blit(title_surf, (title_x, 40))
        
        # Current resolution info
        current_w, current_h = self.screen.get_size()
        current_text = f"Current: {current_w} x {current_h}"
        current_surf = self.font_small.render(current_text, True, (180, 180, 180))
        current_x = w // 2 - current_surf.get_width() // 2
        self.screen.blit(current_surf, (current_x, 90))
        
        # Resolution options
        menu_start_y = 150
        option_spacing = 45
        
        for idx, (res_id, label, res) in enumerate(self.resolutions):
            is_selected = (idx == self.selected_index)
            
            # Highlight selected option
            if is_selected:
                indicator_x = w // 2 - 300
                indicator_y = menu_start_y + idx * option_spacing
                pygame.draw.circle(
                    self.screen,
                    (255, 255, 200),
                    (indicator_x, indicator_y + 12),
                    6
                )
            
            # Option text
            color = (255, 255, 210) if is_selected else (180, 180, 180)
            
            # Show additional info for selected resolution
            display_text = label
            if res_id == "desktop":
                info = pygame.display.Info()
                display_text = f"{label} ({info.current_w} x {info.current_h})"
            elif res is not None:
                # Show aspect ratio
                aspect = res[0] / res[1] if res[1] > 0 else 0
                if abs(aspect - 16/9) < 0.01:
                    display_text = f"{label} (16:9)"
                elif abs(aspect - 16/10) < 0.01:
                    display_text = f"{label} (16:10)"
                elif abs(aspect - 4/3) < 0.01:
                    display_text = f"{label} (4:3)"
            
            text_surf = self.font_main.render(display_text, True, color)
            text_x = w // 2 - text_surf.get_width() // 2
            text_y = menu_start_y + idx * option_spacing
            self.screen.blit(text_surf, (text_x, text_y))
        
        # Hint
        hint_y = h - 60
        hint_text = "↑/↓: Navigate   Enter: Apply   Esc: Cancel"
        hint_surf = self.font_small.render(hint_text, True, (150, 150, 150))
        hint_x = w // 2 - hint_surf.get_width() // 2
        self.screen.blit(hint_surf, (hint_x, hint_y))
        
        # Warning about restart
        warning_text = "Note: Resolution change will apply after restart"
        warning_surf = self.font_small.render(warning_text, True, (200, 150, 150))
        warning_x = w // 2 - warning_surf.get_width() // 2
        self.screen.blit(warning_surf, (warning_x, hint_y + 25))

