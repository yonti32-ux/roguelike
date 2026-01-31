import math
import random
import pygame

from settings import COLOR_BG, FPS, TITLE
from ui.screen_constants import (
    COLOR_GRADIENT_START,
    COLOR_GRADIENT_END,
    COLOR_BG_PANEL,
    COLOR_BORDER_BRIGHT,
    COLOR_SHADOW,
    SHADOW_OFFSET_X,
    SHADOW_OFFSET_Y,
)


class Particle:
    """A small particle that moves randomly around the screen."""
    
    def __init__(self, screen_width: int, screen_height: int):
        self.x = random.uniform(0, screen_width)
        self.y = random.uniform(0, screen_height)
        self.vx = random.uniform(-20, 20)  # Velocity X
        self.vy = random.uniform(-20, 20)  # Velocity Y
        self.size = random.uniform(1, 2.5)
        # Subtle colors that fit the theme
        color_variants = [
            (150, 170, 200, 180),  # Soft blue
            (200, 200, 180, 160),  # Soft yellow
            (180, 200, 220, 170),  # Light blue
            (220, 220, 200, 150),  # Pale yellow
            (160, 180, 200, 140),  # Muted blue
        ]
        self.color = random.choice(color_variants)
        self.screen_width = screen_width
        self.screen_height = screen_height
        # Random direction change timer
        self.direction_change_timer = random.uniform(1.0, 3.0)
        self.direction_timer = 0.0
    
    def update(self, dt: float):
        """Update particle position and velocity."""
        self.direction_timer += dt
        
        # Occasionally change direction randomly
        if self.direction_timer >= self.direction_change_timer:
            self.vx += random.uniform(-30, 30) * dt
            self.vy += random.uniform(-30, 30) * dt
            # Clamp velocity to reasonable range
            self.vx = max(-40, min(40, self.vx))
            self.vy = max(-40, min(40, self.vy))
            self.direction_timer = 0.0
            self.direction_change_timer = random.uniform(1.0, 3.0)
        
        # Update position
        self.x += self.vx * dt
        self.y += self.vy * dt
        
        # Wrap around screen edges
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
            # Create a small surface for the particle with alpha
            particle_surf = pygame.Surface((int(self.size * 2), int(self.size * 2)), pygame.SRCALPHA)
            pygame.draw.circle(
                particle_surf,
                self.color,
                (int(self.size), int(self.size)),
                int(self.size)
            )
            surface.blit(particle_surf, (int(self.x - self.size), int(self.y - self.size)))
        else:
            pygame.draw.circle(
                surface,
                self.color[:3],
                (int(self.x), int(self.y)),
                int(self.size)
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
        
        # Initialize particles
        w, h = screen.get_size()
        self.particles: list[Particle] = []
        num_particles = 40  # Reasonable number, not too excessive
        for _ in range(num_particles):
            self.particles.append(Particle(w, h))
    
    def run(self) -> str | None:
        """
        Main loop for the main menu scene.
        Returns:
            - "new_game": user wants to start a new game
            - "load_game": user wants to load a game (to be implemented)
            - "quit": user wants to quit
            - None: window closed (pygame.QUIT event)
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
    
    def _handle_keydown(self, event: pygame.event.Event) -> str | None:
        """Handle key presses in the main menu."""
        key = event.key
        
        # Global quit shortcut
        if key == pygame.K_q or key == pygame.K_ESCAPE:
            # ESC on "Quit" option confirms, otherwise just selects Quit
            if self.selected_index == len(self.options) - 1:  # Quit is last
                return "quit"
            self.selected_index = len(self.options) - 1
            return  # stay in menu
        
        # Navigation
        if key in (pygame.K_UP, pygame.K_w):
            self.selected_index = (self.selected_index - 1) % len(self.options)
            return  # stay in menu
        
        if key in (pygame.K_DOWN, pygame.K_s):
            self.selected_index = (self.selected_index + 1) % len(self.options)
            return  # stay in menu
        
        # Selection
        if key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
            option_id, _ = self.options[self.selected_index]
            if option_id == "quit":
                return "quit"
            return option_id  # "new_game", "load_game", or "options"
        
        return  # no action
    
    def draw(self) -> None:
        """Draw the main menu screen."""
        w, h = self.screen.get_size()
        
        # Update particle screen dimensions in case of resize
        for particle in self.particles:
            particle.screen_width = w
            particle.screen_height = h
        
        # Draw gradient background
        from ui.screen_components import draw_gradient_background
        draw_gradient_background(
            self.screen, 0, 0, w, h,
            COLOR_GRADIENT_START, COLOR_GRADIENT_END, True
        )
        
        # Draw particles (behind UI elements)
        for particle in self.particles:
            particle.draw(self.screen)
        
        # Title with subtle animation and shadow
        title_color = (255, 255, 210)
        # Add a subtle pulsing effect
        pulse = int(10 * abs(math.sin(self.animation_timer * 2)))
        title_color = tuple(min(255, c + pulse) for c in title_color)
        
        # Render title with shadow
        title_surf = self.font_title.render(TITLE, True, title_color)
        shadow_surf = self.font_title.render(TITLE, True, COLOR_SHADOW[:3])
        title_x = w // 2 - title_surf.get_width() // 2
        title_y = 80
        
        # Draw shadow
        self.screen.blit(shadow_surf, (title_x + SHADOW_OFFSET_X, title_y + SHADOW_OFFSET_Y))
        # Draw title
        self.screen.blit(title_surf, (title_x, title_y))
        
        # Subtitle with shadow
        subtitle = "A Roguelike Adventure"
        subtitle_surf = self.font_small.render(subtitle, True, (220, 220, 220))
        subtitle_shadow = self.font_small.render(subtitle, True, COLOR_SHADOW[:3])
        subtitle_x = w // 2 - subtitle_surf.get_width() // 2
        subtitle_y = title_y + 50
        
        self.screen.blit(subtitle_shadow, (subtitle_x + SHADOW_OFFSET_X, subtitle_y + SHADOW_OFFSET_Y))
        self.screen.blit(subtitle_surf, (subtitle_x, subtitle_y))
        
        # Menu options panel
        menu_start_y = h // 2 - 40
        option_spacing = 60
        menu_width = 400
        menu_height = len(self.options) * option_spacing + 40
        menu_x = w // 2 - menu_width // 2
        menu_panel_y = menu_start_y - 20
        
        # Draw menu panel background
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
                indicator_height = 40
                indicator_y = option_y - 8
                
                # Selection background
                selection_surf = pygame.Surface((indicator_width, indicator_height), pygame.SRCALPHA)
                selection_surf.fill((70, 80, 110, 220))
                self.screen.blit(selection_surf, (indicator_x, indicator_y))
                
                # Left accent border
                pygame.draw.rect(self.screen, (255, 255, 200), (indicator_x, indicator_y, 4, indicator_height))
            
            # Option text
            color = (255, 255, 210) if is_selected else (200, 200, 200)
            text_surf = self.font_main.render(option_text, True, color)
            text_x = w // 2 - text_surf.get_width() // 2
            self.screen.blit(text_surf, (text_x, option_y))
        
        # Controls hint panel
        hint_y = h - 80
        hint_text = "↑/↓: Navigate   Enter: Select   Esc/Q: Quit"
        hint_width = 500
        hint_height = 40
        hint_x = w // 2 - hint_width // 2
        
        hint_panel = pygame.Surface((hint_width, hint_height), pygame.SRCALPHA)
        hint_panel.fill((0, 0, 0, 120))
        pygame.draw.rect(hint_panel, COLOR_BORDER_BRIGHT, (0, 0, hint_width, hint_height), 1)
        self.screen.blit(hint_panel, (hint_x, hint_y))
        
        hint_surf = self.font_small.render(hint_text, True, (180, 180, 180))
        hint_text_x = w // 2 - hint_surf.get_width() // 2
        self.screen.blit(hint_surf, (hint_text_x, hint_y + 12))
        
        # Version or additional info (optional)
        version_text = "v2.0"
        version_surf = self.font_small.render(version_text, True, (120, 120, 120))
        self.screen.blit(version_surf, (w - version_surf.get_width() - 20, h - 30))

