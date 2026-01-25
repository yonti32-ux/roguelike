import math
import random
import pygame

from settings import COLOR_BG, FPS, TITLE
from typing import List, Dict


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
        self.font_title = pygame.font.SysFont("consolas", 36)
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
        
        # Simple animation timer for title/subtitle
        self.animation_timer: float = 0.0
        
        # Background particles for visual effect
        self.particles: List[Dict] = []
        self._init_particles()
    
    def _init_particles(self) -> None:
        """Initialize background particles."""
        w, h = self.screen.get_size()
        # Create 45-55 particles (increased slightly)
        for _ in range(random.randint(45, 55)):
            self.particles.append({
                "x": random.uniform(0, w),
                "y": random.uniform(0, h),
                "vx": random.uniform(-20, 20),
                "vy": random.uniform(-20, 20),
                "size": random.uniform(1, 3),
                "alpha": random.uniform(50, 150),
                "color": random.choice([
                    (100, 150, 255),  # Blue
                    (150, 200, 255),  # Light blue
                    (200, 150, 255),  # Purple
                    (255, 200, 150),  # Orange
                ]),
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
            
            # Update particles
            w, h = self.screen.get_size()
            for particle in self.particles:
                particle["x"] += particle["vx"] * dt
                particle["y"] += particle["vy"] * dt
                
                # Wrap around screen edges
                if particle["x"] < 0:
                    particle["x"] = w
                elif particle["x"] > w:
                    particle["x"] = 0
                if particle["y"] < 0:
                    particle["y"] = h
                elif particle["y"] > h:
                    particle["y"] = 0
                
                # Subtle pulsing alpha
                particle["alpha"] = 50 + int(100 * abs(math.sin(self.animation_timer * 0.5 + particle["x"] * 0.01)))
            
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
            return None  # stay in menu
        
        if key in (pygame.K_DOWN, pygame.K_s):
            self.selected_index = (self.selected_index + 1) % len(self.options)
            return None  # stay in menu
        
        # Selection
        if key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
            option_id, _ = self.options[self.selected_index]
            return option_id  # "new_game", "load_game", "options", or "quit"
        
        return None  # no action
    
    def draw(self) -> None:
        """Draw the main menu screen."""
        self.screen.fill(COLOR_BG)
        w, h = self.screen.get_size()
        
        # Draw background particles
        for particle in self.particles:
            x = int(particle["x"])
            y = int(particle["y"])
            size = int(particle["size"])
            alpha = int(particle["alpha"])
            color = particle["color"]
            
            # Draw particle with alpha
            particle_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            particle_color = (*color, alpha)
            pygame.draw.circle(particle_surf, particle_color, (size, size), size)
            self.screen.blit(particle_surf, (x - size, y - size))
        
        # Title with subtle animation
        title_color = (255, 255, 210)
        # Add a subtle pulsing effect
        pulse = int(10 * abs(math.sin(self.animation_timer * 2)))
        title_color = tuple(min(255, c + pulse) for c in title_color)
        
        title_surf = self.font_title.render("Roguelike Dungeon Crawler Demo", True, title_color)
        title_x = w // 2 - title_surf.get_width() // 2
        title_y = 80
        self.screen.blit(title_surf, (title_x, title_y))
        
        # Subtitle
        subtitle = "A Roguelike Adventure"
        subtitle_surf = self.font_small.render(subtitle, True, (200, 200, 200))
        subtitle_x = w // 2 - subtitle_surf.get_width() // 2
        self.screen.blit(subtitle_surf, (subtitle_x, title_y + 50))
        
        # Menu options
        menu_start_y = h // 2 - 40
        option_spacing = 60
        
        for idx, (option_id, option_text) in enumerate(self.options):
            is_selected = (idx == self.selected_index)
            
            # Highlight selected option
            if is_selected:
                # Draw selection indicator
                indicator_x = w // 2 - 200
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
        hint_text = "↑/↓: Navigate   Enter: Select   Esc/Q: Quit"
        hint_surf = self.font_small.render(hint_text, True, (150, 150, 150))
        hint_x = w // 2 - hint_surf.get_width() // 2
        self.screen.blit(hint_surf, (hint_x, hint_y))
        
        # Version or additional info (optional)
        version_text = "v 0.4 Alpha"
        version_surf = self.font_small.render(version_text, True, (100, 100, 100))
        self.screen.blit(version_surf, (w - version_surf.get_width() - 20, h - 30))

