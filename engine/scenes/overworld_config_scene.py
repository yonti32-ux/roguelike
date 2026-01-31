"""
Overworld configuration scene.

Allows player to customize overworld settings before starting a new game.
"""

import pygame
import random
import math
from typing import Optional, TYPE_CHECKING, Dict, Any, List

from settings import COLOR_BG, FPS
from ui.screen_constants import (
    COLOR_GRADIENT_START,
    COLOR_GRADIENT_END,
    COLOR_BG_PANEL,
    COLOR_BORDER_BRIGHT,
    COLOR_SHADOW,
    COLOR_SELECTED_BG_BRIGHT,
    COLOR_TITLE,
    COLOR_SUBTITLE,
    COLOR_TEXT,
    COLOR_TEXT_DIM,
    COLOR_ACCENT_SUCCESS,
    SHADOW_OFFSET_X,
    SHADOW_OFFSET_Y,
)

if TYPE_CHECKING:
    from world.overworld.config import OverworldConfig


class Particle:
    """A small particle that moves randomly around the screen."""
    
    def __init__(self, screen_width: int, screen_height: int):
        self.x = random.uniform(0, screen_width)
        self.y = random.uniform(0, screen_height)
        self.vx = random.uniform(-25, 25)  # Velocity X
        self.vy = random.uniform(-25, 25)  # Velocity Y
        self.size = random.uniform(1.5, 3.0)
        # Subtle colors that fit the overworld theme
        color_variants = [
            (150, 170, 200, 180),  # Soft blue
            (200, 200, 180, 160),  # Soft yellow
            (180, 200, 220, 170),  # Light blue
            (220, 220, 200, 150),  # Pale yellow
            (160, 180, 200, 140),  # Muted blue
            (180, 220, 200, 160),  # Soft green
        ]
        self.color = random.choice(color_variants)
        self.screen_width = screen_width
        self.screen_height = screen_height
        # Random direction change timer
        self.direction_change_timer = random.uniform(1.5, 4.0)
        self.direction_timer = 0.0
    
    def update(self, dt: float):
        """Update particle position and velocity."""
        self.direction_timer += dt
        
        # Occasionally change direction randomly
        if self.direction_timer >= self.direction_change_timer:
            self.vx += random.uniform(-35, 35) * dt
            self.vy += random.uniform(-35, 35) * dt
            # Clamp velocity to reasonable range
            self.vx = max(-50, min(50, self.vx))
            self.vy = max(-50, min(50, self.vy))
            self.direction_timer = 0.0
            self.direction_change_timer = random.uniform(1.5, 4.0)
        
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


class OverworldConfigScene:
    """
    Menu for configuring overworld settings before starting a new game.
    
    Allows customization of:
    - World size (width, height)
    - POI density
    - Random seed (optional)
    - Sight radius
    """
    
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.font_title = pygame.font.SysFont("consolas", 32)
        self.font_main = pygame.font.SysFont("consolas", 22)
        self.font_small = pygame.font.SysFont("consolas", 18)
        
        # Load default config
        from world.overworld.config import OverworldConfig
        from world.generation.config import load_generation_config
        self.config = OverworldConfig.load()
        self.gen_config = load_generation_config()  # Load generation settings
        
        # Editable values (copies of config values)
        self.world_width = self.config.world_width
        self.world_height = self.config.world_height
        self.poi_density = self.config.poi_density
        self.seed_value = self.config.seed
        self.sight_radius = self.config.sight_radius
        
        # World name (generate random name if not set)
        from systems.namegen import generate_world_name
        if self.config.world_name:
            self.world_name = self.config.world_name
        else:
            # Generate random world name if not set
            self.world_name = generate_world_name()
        
        # Current editing field (None = no field selected)
        self.editing_field: Optional[str] = None
        # Buffer for text input
        self.text_buffer = ""
        # Cursor blink
        self.cursor_visible = True
        self.cursor_timer = 0.0
        
        # Mode: "preset" or "advanced"
        self.mode = "preset"
        
        # Field selection index
        self.selected_index = 0
        
        # Preset mode fields (expanded with more options)
        self.preset_fields = [
            "world_name",
            "terrain_preset",  # Terrain type (renamed from world_preset)
            "world_size",  # World size preset
            "poi_density",
            "room_count_preset",
            "seed",
        ]
        
        # Advanced mode fields (all detailed options)
        self.advanced_fields = [
            "world_name",
            "world_width",
            "world_height",
            "poi_density",
            "seed",
            "sight_radius",
            "default_zoom",
            "gen_preset",  # Terrain preset
            "room_count_preset",  # Room count preset
            "shop_chance",  # Shop spawn chance
        ]
        
        self.fields = self.preset_fields  # Start with preset fields
        
        # World size presets
        self.world_size_presets = {
            "small": ("Small", 128, 128, 0.12),
            "medium": ("Medium", 256, 256, 0.10),
            "large": ("Large", 512, 512, 0.08),
            "huge": ("Huge", 1024, 1024, 0.06),
        }
        self.world_size_key = "medium"  # Default size
        # Apply default size
        size_data = self.world_size_presets[self.world_size_key]
        self.world_width = size_data[1]
        self.world_height = size_data[2]
        self.poi_density = size_data[3]
        
        # Terrain presets (terrain distribution) - used in both modes
        self.terrain_presets = {
            "normal": "Normal (Balanced)",
            "forest": "Forest Heavy",
            "desert": "Desert Heavy",
            "water": "Water Heavy",
            "mountain": "Mountain Heavy",
        }
        self.terrain_preset = "normal"
        # Also keep gen_preset for advanced mode compatibility
        self.gen_preset = "normal"
        
        # Room count presets
        self.room_count_presets = {
            "few": ("Few Rooms", 0.7),
            "normal": ("Normal", 1.0),
            "many": ("Many Rooms", 1.5),
        }
        self.room_count_preset = "normal"
        
        # Store original room count base for presets
        self.original_room_base = self.gen_config.floor.room_count["base"]
        
        # Shop spawn chance (0.0 - 1.0)
        self.shop_chance = self.gen_config.room_tags.shop.get("chance", 0.7)
        
        # Zoom level for overworld
        self.zoom_levels = [0.5, 0.75, 1.0, 1.25, 1.5]  # 50% to 150%
        self.zoom_index = self.config.default_zoom_index if hasattr(self.config, "default_zoom_index") else 1
        # Clamp zoom index to valid range
        self.zoom_index = max(0, min(self.zoom_index, len(self.zoom_levels) - 1))
        
        # Animation timer for background effects
        self.animation_timer: float = 0.0
        
        # Initialize particles
        w, h = screen.get_size()
        self.particles: List[Particle] = []
        num_particles = 50  # More particles for richer effect
        for _ in range(num_particles):
            self.particles.append(Particle(w, h))
    
    def run(self) -> Optional["OverworldConfig"]:
        """
        Main loop for overworld configuration.
        Returns: OverworldConfig if confirmed, None if cancelled.
        """
        clock = pygame.time.Clock()
        
        while True:
            dt = clock.tick(FPS) / 1000.0
            
            # Update animation timer
            self.animation_timer += dt
            
            # Update particles
            for particle in self.particles:
                particle.update(dt)
                # Update screen dimensions in case of resize
                w, h = self.screen.get_size()
                particle.screen_width = w
                particle.screen_height = h
            
            # Cursor blink
            self.cursor_timer += dt
            if self.cursor_timer >= 0.5:
                self.cursor_timer = 0.0
                self.cursor_visible = not self.cursor_visible
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                
                if event.type == pygame.KEYDOWN:
                    result = self._handle_keydown(event)
                    if result is not None:
                        return result
            
            self.draw()
            pygame.display.flip()
    
    def _handle_keydown(self, event: pygame.event.Event) -> Optional["OverworldConfig"]:
        """Handle key presses."""
        key = event.key
        
        # Global quit
        if key == pygame.K_q:
            return None
        
        # If editing a field, handle text input
        if self.editing_field is not None:
            if key == pygame.K_ESCAPE:
                # Cancel editing
                self.editing_field = None
                self.text_buffer = ""
                return None
            
            if key == pygame.K_RETURN or key == pygame.K_KP_ENTER:
                # Confirm and apply value
                self._apply_text_input()
                self.editing_field = None
                self.text_buffer = ""
                return None
            
            if key == pygame.K_BACKSPACE:
                if self.text_buffer:
                    self.text_buffer = self.text_buffer[:-1]
                return None
            
            # Handle text input
            if event.unicode:
                char = event.unicode
                if self.editing_field == 'world_name':
                    # World name accepts any printable character
                    if char.isprintable() and len(self.text_buffer) < 50:  # Limit length
                        self.text_buffer += char
                elif self.editing_field in ("world_width", "world_height", "sight_radius"):
                    # Numeric input for these fields
                    if char.isdigit():
                        self.text_buffer += char
                elif self.editing_field == 'poi_density':
                    # Decimal point allowed for density
                    if char.isdigit() or (char == '.' and '.' not in self.text_buffer):
                        self.text_buffer += char
                elif self.editing_field == 'seed':
                    # Seed can be negative integer
                    if char.isdigit() or (char == '-' and not self.text_buffer):
                        self.text_buffer += char
                elif self.editing_field in ('shop_chance', 'poi_density'):
                    # Decimal point allowed for shop chance and POI density
                    if char.isdigit() or (char == '.' and '.' not in self.text_buffer):
                        self.text_buffer += char
                return None
        
        # Toggle between preset and advanced mode
        if key == pygame.K_TAB and self.editing_field is None:
            if self.mode == "preset":
                self.mode = "advanced"
                self.fields = self.advanced_fields
            else:
                self.mode = "preset"
                self.fields = self.preset_fields
            self.selected_index = 0  # Reset to top
            return None
        
        # Navigation
        if key in (pygame.K_UP, pygame.K_w):
            if self.editing_field is None:
                self.selected_index = (self.selected_index - 1) % len(self.fields)
            return None
        
        if key in (pygame.K_DOWN, pygame.K_s):
            if self.editing_field is None:
                self.selected_index = (self.selected_index + 1) % len(self.fields)
            return None
        
        # Start editing field
        if key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
            if self.editing_field is None:
                field = self.fields[self.selected_index]
                # Fields that cycle instead of text input
                if field == "terrain_preset":
                    # Cycle through terrain presets
                    preset_list = list(self.terrain_presets.keys())
                    current_idx = preset_list.index(self.terrain_preset) if self.terrain_preset in preset_list else 0
                    self.terrain_preset = preset_list[(current_idx + 1) % len(preset_list)]
                    self.gen_preset = self.terrain_preset  # Keep in sync
                    return None
                elif field == "world_size":
                    # Cycle through world size presets
                    size_list = list(self.world_size_presets.keys())
                    current_idx = size_list.index(self.world_size_key) if self.world_size_key in size_list else 0
                    self.world_size_key = size_list[(current_idx + 1) % len(size_list)]
                    # Apply size immediately
                    self._apply_world_size(self.world_size_key)
                    return None
                elif field == "default_zoom":
                    # Cycle through zoom levels
                    self.zoom_index = (self.zoom_index + 1) % len(self.zoom_levels)
                    return None
                elif field == "gen_preset":
                    # Cycle through generation presets (uses terrain_presets)
                    preset_list = list(self.terrain_presets.keys())
                    current_idx = preset_list.index(self.gen_preset) if self.gen_preset in preset_list else 0
                    self.gen_preset = preset_list[(current_idx + 1) % len(preset_list)]
                    # Also update terrain_preset to match
                    self.terrain_preset = self.gen_preset
                    return None
                elif field == "room_count_preset":
                    # Cycle through room count presets
                    preset_list = list(self.room_count_presets.keys())
                    current_idx = preset_list.index(self.room_count_preset) if self.room_count_preset in preset_list else 0
                    self.room_count_preset = preset_list[(current_idx + 1) % len(preset_list)]
                    return None
                elif field == "world_name":
                    # World name uses text input
                    self.editing_field = field
                    self.text_buffer = self.world_name
                    return None
                else:
                    self.editing_field = field
                    self.text_buffer = str(self._get_field_value(field))
                return None
        
        # Quick number keys for world size (preset mode only)
        current_field = self.fields[self.selected_index] if self.selected_index < len(self.fields) else None
        if self.mode == "preset" and current_field == "world_size":
            size_keys = list(self.world_size_presets.keys())
            if key == pygame.K_1 and len(size_keys) > 0:
                self.world_size_key = size_keys[0]
                self._apply_world_size(self.world_size_key)
                return None
            elif key == pygame.K_2 and len(size_keys) > 1:
                self.world_size_key = size_keys[1]
                self._apply_world_size(self.world_size_key)
                return None
            elif key == pygame.K_3 and len(size_keys) > 2:
                self.world_size_key = size_keys[2]
                self._apply_world_size(self.world_size_key)
                return None
            elif key == pygame.K_4 and len(size_keys) > 3:
                self.world_size_key = size_keys[3]
                self._apply_world_size(self.world_size_key)
                return None
        
        # Quick presets for world size (advanced mode only)
        if self.mode == "advanced" and key == pygame.K_1 and self.selected_index == 1:  # World width selected
            self.world_width = 128
            self.world_height = 128
            return None
        if self.mode == "advanced" and key == pygame.K_2 and self.selected_index == 1:
            self.world_width = 256
            self.world_height = 256
            return None
        if self.mode == "advanced" and key == pygame.K_3 and self.selected_index == 1:
            self.world_width = 512
            self.world_height = 512
            return None
        if self.mode == "advanced" and key == pygame.K_4 and self.selected_index == 1:
            self.world_width = 1024
            self.world_height = 1024
            return None
        
        # Randomize world name (R key when world_name is selected)
        current_field = self.fields[self.selected_index] if self.selected_index < len(self.fields) else None
        if current_field == "world_name" and key == pygame.K_r:
            from systems.namegen import generate_world_name
            # Generate random name independently of seed
            self.world_name = generate_world_name()
            return None
        
        # Quick zoom presets (when zoom field is selected)
        if current_field == "default_zoom":
            if key == pygame.K_1:
                self.zoom_index = 0  # 50%
                return None
            elif key == pygame.K_2:
                self.zoom_index = 1  # 75%
                return None
            elif key == pygame.K_3:
                self.zoom_index = 2  # 100%
                return None
            elif key == pygame.K_4:
                self.zoom_index = 3  # 125%
                return None
            elif key == pygame.K_5:
                self.zoom_index = 4  # 150%
                return None
        
        # Confirm and return config (F key or Enter on empty field)
        if key == pygame.K_f:
            return self._create_config()
        
        return None
    
    def _apply_world_size(self, size_key: str) -> None:
        """Apply a world size preset to width, height, and POI density."""
        if size_key not in self.world_size_presets:
            return
        
        size_data = self.world_size_presets[size_key]
        self.world_width = size_data[1]  # width
        self.world_height = size_data[2]  # height
        self.poi_density = size_data[3]  # poi_density
    
    def _get_field_value(self, field: str) -> any:
        """Get current value for a field."""
        if field == "terrain_preset":
            return self.terrain_presets.get(self.terrain_preset, "Normal")
        elif field == "world_size":
            return self.world_size_presets.get(self.world_size_key, ("Unknown", 256, 256, 0.10))[0]
        elif field == "world_name":
            return self.world_name
        elif field == "world_width":
            return self.world_width
        elif field == "world_height":
            return self.world_height
        elif field == "poi_density":
            return self.poi_density
        elif field == "seed":
            return self.seed_value if self.seed_value is not None else ""
        elif field == "sight_radius":
            return self.sight_radius
        elif field == "default_zoom":
            return f"{int(self.zoom_levels[self.zoom_index] * 100)}%"
        elif field == "gen_preset":
            return self.terrain_presets.get(self.gen_preset, "Normal")
        elif field == "room_count_preset":
            return self.room_count_presets[self.room_count_preset][0]
        elif field == "shop_chance":
            return self.shop_chance
        return ""
    
    def _apply_text_input(self) -> None:
        """Apply text buffer value to current field."""
        field = self.editing_field
        if field is None:
            return
        
        try:
            if field == "world_name":
                # World name accepts any text (allow empty, but default to random if empty)
                if self.text_buffer.strip():
                    self.world_name = self.text_buffer.strip()
                else:
                    # Empty name - generate random name
                    from systems.namegen import generate_world_name
                    self.world_name = generate_world_name()
            elif field in ("world_width", "world_height", "sight_radius"):
                if not self.text_buffer:
                    return
                value = int(self.text_buffer)
                if field == "world_width":
                    self.world_width = max(64, min(2048, value))  # Clamp 64-2048
                elif field == "world_height":
                    self.world_height = max(64, min(2048, value))  # Clamp 64-2048
                elif field == "sight_radius":
                    self.sight_radius = max(1, min(50, value))  # Clamp 1-50
            elif field == "poi_density":
                if not self.text_buffer:
                    return
                value = float(self.text_buffer)
                self.poi_density = max(0.01, min(1.0, value))  # Clamp 0.01-1.0
            elif field == "shop_chance":
                if not self.text_buffer:
                    return
                value = float(self.text_buffer)
                self.shop_chance = max(0.0, min(1.0, value))  # Clamp 0.0-1.0
            elif field == "seed":
                if self.text_buffer.strip() == "":
                    self.seed_value = None
                else:
                    self.seed_value = int(self.text_buffer)
                # Seed and world name are independent - don't regenerate name when seed changes
            # Note: default_zoom doesn't use text input, it cycles
        except ValueError:
            # Invalid input, ignore
            pass
    
    def _create_config(self) -> "OverworldConfig":
        """Create OverworldConfig from current values and save generation config."""
        from world.overworld.config import OverworldConfig
        from world.generation.config import load_generation_config
        
        # Apply generation preset changes (use terrain_preset from preset mode, gen_preset from advanced)
        terrain_to_use = self.terrain_preset if self.mode == "preset" else self.gen_preset
        self._apply_generation_presets(terrain_to_use)
        
        # Save generation config
        self.gen_config.save()
        
        # Create overworld config
        config = OverworldConfig()
        config.world_width = self.world_width
        config.world_height = self.world_height
        config.poi_density = self.poi_density
        config.seed = self.seed_value
        config.world_name = self.world_name
        config.sight_radius = self.sight_radius
        config.default_zoom_index = self.zoom_index
        # Keep other settings from defaults
        
        return config
    
    def _apply_generation_presets(self, terrain_type: str) -> None:
        """Apply selected generation presets to config."""
        # Apply terrain preset
        if terrain_type == "normal":
            # Default distribution
            self.gen_config.terrain.initial_distribution = {
                "grass": 0.35,
                "plains": 0.20,
                "forest": 0.15,
                "mountain": 0.12,
                "desert": 0.10,
                "water": 0.08,
            }
        elif terrain_type == "forest":
            self.gen_config.terrain.initial_distribution = {
                "grass": 0.20,
                "plains": 0.10,
                "forest": 0.50,  # Much more forest
                "mountain": 0.08,
                "desert": 0.02,
                "water": 0.10,
            }
        elif terrain_type == "desert":
            self.gen_config.terrain.initial_distribution = {
                "grass": 0.10,
                "plains": 0.20,
                "forest": 0.05,
                "mountain": 0.10,
                "desert": 0.50,  # Much more desert
                "water": 0.05,
            }
        elif terrain_type == "water":
            self.gen_config.terrain.initial_distribution = {
                "grass": 0.25,
                "plains": 0.15,
                "forest": 0.15,
                "mountain": 0.05,
                "desert": 0.05,
                "water": 0.35,  # Much more water
            }
        elif terrain_type == "mountain":
            self.gen_config.terrain.initial_distribution = {
                "grass": 0.20,
                "plains": 0.10,
                "forest": 0.15,
                "mountain": 0.45,  # Much more mountain
                "desert": 0.05,
                "water": 0.05,
            }
        
        # Apply room count preset (based on original base)
        room_multiplier = self.room_count_presets[self.room_count_preset][1]
        base_rooms = int(self.original_room_base * room_multiplier)
        self.gen_config.floor.room_count["base"] = max(4, min(30, base_rooms))
        
        # Apply shop chance
        self.gen_config.room_tags.shop["chance"] = self.shop_chance
    
    def draw(self) -> None:
        """Draw the configuration screen with polished styling."""
        screen = self.screen
        w, h = screen.get_size()
        
        # Draw enhanced gradient background with animated effect
        from ui.screen_components import draw_gradient_background
        # Add subtle animation to gradient colors
        pulse = math.sin(self.animation_timer * 0.5) * 5
        start_color = tuple(min(255, max(0, c + int(pulse))) for c in COLOR_GRADIENT_START)
        end_color = tuple(min(255, max(0, c + int(pulse * 0.7))) for c in COLOR_GRADIENT_END)
        draw_gradient_background(
            screen, 0, 0, w, h,
            start_color, end_color, True
        )
        
        # Draw particles (behind UI elements)
        for particle in self.particles:
            particle.draw(screen)
        
        # Title with shadow and subtle animation
        mode_text = "World Generation Presets" if self.mode == "preset" else "Advanced Options"
        title_color = COLOR_TITLE
        title_pulse = int(8 * abs(math.sin(self.animation_timer * 1.5)))
        title_color = tuple(min(255, c + title_pulse) for c in title_color)
        
        title_text = self.font_title.render(mode_text, True, title_color)
        title_shadow = self.font_title.render(mode_text, True, COLOR_SHADOW[:3])
        title_x = w // 2 - title_text.get_width() // 2
        title_y = 40
        
        screen.blit(title_shadow, (title_x + SHADOW_OFFSET_X, title_y + SHADOW_OFFSET_Y))
        screen.blit(title_text, (title_x, title_y))
        
        # Mode indicator panel
        mode_text_str = f"Press TAB to switch to {'Advanced Options' if self.mode == 'preset' else 'Presets'}"
        mode_indicator = self.font_small.render(mode_text_str, True, COLOR_SUBTITLE)
        mode_panel_width = mode_indicator.get_width() + 40
        mode_panel_height = 35
        mode_panel_x = w // 2 - mode_panel_width // 2
        mode_panel_y = 75
        
        mode_panel = pygame.Surface((mode_panel_width, mode_panel_height), pygame.SRCALPHA)
        mode_panel.fill(COLOR_BG_PANEL)
        pygame.draw.rect(mode_panel, COLOR_BORDER_BRIGHT, (0, 0, mode_panel_width, mode_panel_height), 1)
        screen.blit(mode_panel, (mode_panel_x, mode_panel_y))
        screen.blit(mode_indicator, (mode_panel_x + 20, mode_panel_y + 8))
        
        # Instructions panel at bottom
        help_text = "Arrow Keys: Navigate | Enter: Edit/Cycle | TAB: Presets/Advanced | F: Finish | Q: Quit"
        help_surface = self.font_small.render(help_text, True, COLOR_TEXT)
        help_panel_width = help_surface.get_width() + 40
        help_panel_height = 35
        help_panel_x = w // 2 - help_panel_width // 2
        help_panel_y = h - 80
        
        help_panel = pygame.Surface((help_panel_width, help_panel_height), pygame.SRCALPHA)
        help_panel.fill(COLOR_BG_PANEL)
        pygame.draw.rect(help_panel, COLOR_BORDER_BRIGHT, (0, 0, help_panel_width, help_panel_height), 1)
        screen.blit(help_panel, (help_panel_x, help_panel_y))
        screen.blit(help_surface, (help_panel_x + 20, help_panel_y + 8))
        
        # Start button panel
        start_text = "Press F to Finish and Start Game"
        start_surface = self.font_main.render(start_text, True, COLOR_ACCENT_SUCCESS)
        start_panel_width = start_surface.get_width() + 40
        start_panel_height = 45
        start_panel_x = w // 2 - start_panel_width // 2
        start_panel_y = h - 35
        
        start_panel = pygame.Surface((start_panel_width, start_panel_height), pygame.SRCALPHA)
        start_panel.fill((20, 50, 20, 220))
        pygame.draw.rect(start_panel, COLOR_ACCENT_SUCCESS, (0, 0, start_panel_width, start_panel_height), 2)
        screen.blit(start_panel, (start_panel_x, start_panel_y))
        screen.blit(start_surface, (start_panel_x + 20, start_panel_y + 12))
        
        # Main content panel
        panel_width = w - 80
        panel_height = h - 250
        panel_x = 40
        panel_y = 120
        
        main_panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        main_panel.fill(COLOR_BG_PANEL)
        pygame.draw.rect(main_panel, COLOR_BORDER_BRIGHT, (0, 0, panel_width, panel_height), 2)
        screen.blit(main_panel, (panel_x, panel_y))
        
        # Field labels and values (modular dictionary for easy expansion)
        start_y = panel_y + 20
        line_height = 42
        field_labels = {
            "world_name": "World Name:",
            "terrain_preset": "Terrain Type:",
            "world_size": "World Size:",
            "poi_density": "POI Density:",
            "room_count_preset": "Room Count:",
            "world_width": "World Width:",
            "world_height": "World Height:",
            "seed": "Random Seed (empty for random):",
            "sight_radius": "Sight Radius:",
            "default_zoom": "Default Zoom Level:",
            "gen_preset": "Terrain Preset:",
            "shop_chance": "Shop Spawn Chance:",
        }
        
        field_descriptions_preset = {
            "world_name": "World name (Press Enter to edit, R to randomize)",
            "terrain_preset": "Terrain distribution type (Press Enter to cycle: Normal, Forest, Desert, Water, Mountain)",
            "world_size": "World size preset (Press Enter or 1-4 to cycle: Small, Medium, Large, Huge)",
            "poi_density": "Density of Points of Interest (0.01-1.0, higher = more POIs). Press Enter to edit.",
            "room_count_preset": "Dungeon room count (Press Enter to cycle: Few, Normal, Many)",
            "seed": "Random seed for world generation (leave empty for random). Press Enter to edit.",
        }
        
        field_descriptions_advanced = {
            "world_name": "World name (Press Enter to edit, R to randomize)",
            "world_width": "World size in tiles (64-2048). Press 1-4 for presets.",
            "world_height": "World height in tiles (64-2048)",
            "poi_density": "Density of Points of Interest (0.01-1.0, higher = more POIs)",
            "seed": "Random seed for world generation (leave empty for random)",
            "sight_radius": "How far you can see (1-50 tiles)",
            "default_zoom": "Starting zoom level (Press Enter or 1-5 to cycle: 50%, 75%, 100%, 125%, 150%)",
            "gen_preset": "Terrain distribution (Press Enter to cycle: Normal, Forest, Desert, Water, Mountain)",
            "room_count_preset": "Dungeon room count (Press Enter to cycle: Few, Normal, Many)",
            "shop_chance": "Chance for shops to spawn on floors (0.0-1.0, Press Enter to edit)",
        }
        
        field_descriptions = field_descriptions_preset if self.mode == "preset" else field_descriptions_advanced
        
        for idx, field in enumerate(self.fields):
            y = start_y + idx * line_height
            is_selected = idx == self.selected_index
            is_editing = self.editing_field == field
            
            # Highlight selected row with better styling
            if is_selected:
                highlight_width = panel_width - 20
                highlight_x = panel_x + 10
                highlight_y = y - 3
                highlight_height = line_height - 6
                
                highlight_surf = pygame.Surface((highlight_width, highlight_height), pygame.SRCALPHA)
                highlight_surf.fill(COLOR_SELECTED_BG_BRIGHT)
                screen.blit(highlight_surf, (highlight_x, highlight_y))
                
                # Left accent border (golden if editing, otherwise normal)
                accent_color = (255, 215, 0) if is_editing else COLOR_TITLE
                pygame.draw.rect(screen, accent_color, (highlight_x, highlight_y, 4, highlight_height))
                
                # Subtle top/bottom borders for better definition
                pygame.draw.line(screen, COLOR_BORDER_BRIGHT, (highlight_x + 4, highlight_y), (highlight_x + highlight_width, highlight_y), 1)
                pygame.draw.line(screen, COLOR_BORDER_BRIGHT, (highlight_x + 4, highlight_y + highlight_height - 1), (highlight_x + highlight_width, highlight_y + highlight_height - 1), 1)
            
            # Label with better color and icon indicator for editable fields
            label_color = COLOR_TITLE if is_selected else COLOR_TEXT
            label_text_str = field_labels[field]
            
            # Add visual indicator for editable/cyclable fields
            if field in ("world_name", "world_width", "world_height", "poi_density", "seed", "sight_radius", "shop_chance"):
                if is_editing:
                    label_text_str = "✎ " + label_text_str  # Pencil icon when editing
                else:
                    label_text_str = "→ " + label_text_str  # Arrow when selectable
            elif field in ("terrain_preset", "world_size", "room_count_preset", "default_zoom", "gen_preset"):
                label_text_str = "⟲ " + label_text_str  # Cycle icon for preset fields
            
            label_text = self.font_main.render(label_text_str, True, label_color)
            screen.blit(label_text, (panel_x + 30, y))
            
            # Value display (modular rendering - easy to extend)
            value = self._get_field_value(field)
            display_text, value_color = self._format_field_display(field, value, is_selected, is_editing)
            
            value_text = self.font_main.render(display_text, True, value_color)
            screen.blit(value_text, (panel_x + 320, y))
            
            # Description (small, gray) - positioned better
            description = field_descriptions.get(field, "")
            if description:
                desc_text = self.font_small.render(
                    description,
                    True, COLOR_TEXT_DIM
                )
                screen.blit(desc_text, (panel_x + 520, y + 5))
        
        # Additional info panel
        info_y = start_y + len(self.fields) * line_height + 20
        if info_y < panel_y + panel_height - 30:
            if self.mode == "preset":
                info_text = "World Size quick keys (when World Size selected): 1=Small 2=Medium 3=Large 4=Huge"
            else:
                info_text = "Quick presets (when World Width is selected): 1=Small 2=Medium 3=Large 4=Huge"
            
            info_surface = self.font_small.render(info_text, True, COLOR_TEXT_DIM)
            info_panel_width = info_surface.get_width() + 40
            info_panel_height = 30
            info_panel_x = panel_x + 10
            info_panel_y = info_y
            
            info_panel = pygame.Surface((info_panel_width, info_panel_height), pygame.SRCALPHA)
            info_panel.fill((20, 25, 35, 180))
            pygame.draw.rect(info_panel, COLOR_BORDER_BRIGHT, (0, 0, info_panel_width, info_panel_height), 1)
            screen.blit(info_panel, (info_panel_x, info_panel_y))
            screen.blit(info_surface, (info_panel_x + 20, info_panel_y + 6))
    
    def _format_field_display(self, field: str, value: Any, is_selected: bool, is_editing: bool) -> tuple[str, tuple[int, int, int]]:
        """
        Format field display text and color. 
        Modular function - easy to extend for new field types.
        
        Returns:
            (display_text, color_tuple)
        """
        # Preset fields (cycle through options)
        if field in ("terrain_preset", "world_size", "room_count_preset", "gen_preset"):
            if is_selected:
                if field == "world_size":
                    display_text = f"{value} ({self.world_width}x{self.world_height}) (Press Enter or 1-4 to cycle)"
                else:
                    display_text = f"{value} (Press Enter to cycle)"
                value_color = COLOR_ACCENT_SUCCESS
            else:
                if field == "world_size":
                    display_text = f"{value} ({self.world_width}x{self.world_height})"
                else:
                    display_text = str(value)
                value_color = COLOR_TEXT if is_selected else COLOR_TEXT_DIM
        
        # Zoom field
        elif field == "default_zoom":
            if is_selected:
                display_text = f"{int(self.zoom_levels[self.zoom_index] * 100)}% (Press Enter to cycle)"
                value_color = COLOR_ACCENT_SUCCESS
            else:
                display_text = f"{int(self.zoom_levels[self.zoom_index] * 100)}%"
                value_color = COLOR_TEXT if is_selected else COLOR_TEXT_DIM
        
        # World name field
        elif field == "world_name":
            if is_editing:
                display_text = self.text_buffer
                if self.cursor_visible:
                    display_text += "_"
                value_color = COLOR_ACCENT_SUCCESS
            elif is_selected:
                display_text = f"{value} (Press R to randomize)"
                value_color = COLOR_ACCENT_SUCCESS
            else:
                display_text = str(value)
                value_color = COLOR_TEXT if is_selected else COLOR_TEXT_DIM
        
        # Text input fields
        elif is_editing:
            display_text = self.text_buffer
            if self.cursor_visible:
                # Animated cursor with pulse effect
                cursor_pulse = int(5 * abs(math.sin(self.animation_timer * 8)))
                display_text += "_"
            value_color = COLOR_ACCENT_SUCCESS
        
        # Other fields
        else:
            if field == "seed" and value == "":
                display_text = "(random)"
            elif field == "poi_density":
                display_text = f"{value:.2f}"
                if is_selected and not is_editing:
                    display_text += " (Press Enter to edit)"
            elif field == "shop_chance":
                display_text = f"{value:.2f}"
            else:
                display_text = str(value)
                if is_selected and field == "seed" and not is_editing:
                    display_text += " (Press Enter to edit)"
            
            value_color = COLOR_TEXT if is_selected else COLOR_TEXT_DIM
        
        return display_text, value_color

