"""
Overworld configuration scene.

Allows player to customize overworld settings before starting a new game.
"""

import pygame
from typing import Optional, TYPE_CHECKING

from settings import COLOR_BG, FPS

if TYPE_CHECKING:
    from world.overworld.config import OverworldConfig


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
        self.config = OverworldConfig.load()
        
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
        
        # Field selection index
        self.selected_index = 0
        self.fields = [
            "world_name",
            "world_width",
            "world_height",
            "poi_density",
            "seed",
            "sight_radius",
            "default_zoom",
        ]
        
        # Zoom level for overworld
        self.zoom_levels = [0.5, 0.75, 1.0, 1.25, 1.5]  # 50% to 150%
        self.zoom_index = self.config.default_zoom_index if hasattr(self.config, "default_zoom_index") else 1
        # Clamp zoom index to valid range
        self.zoom_index = max(0, min(self.zoom_index, len(self.zoom_levels) - 1))
        
        # Preset world sizes
        self.world_size_presets = [
            ("small", 128, 128, "Small (128x128)"),
            ("medium", 256, 256, "Medium (256x256)"),
            ("large", 512, 512, "Large (512x512)"),
            ("huge", 1024, 1024, "Huge (1024x1024)"),
        ]
    
    def run(self) -> Optional["OverworldConfig"]:
        """
        Main loop for overworld configuration.
        Returns: OverworldConfig if confirmed, None if cancelled.
        """
        clock = pygame.time.Clock()
        
        while True:
            dt = clock.tick(FPS) / 1000.0
            
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
                # Zoom field doesn't use text input, it cycles
                if field == "default_zoom":
                    # Cycle through zoom levels
                    self.zoom_index = (self.zoom_index + 1) % len(self.zoom_levels)
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
        
        # Quick presets for world size
        if key == pygame.K_1 and self.selected_index == 0:  # World width selected
            self.world_width = 128
            self.world_height = 128
            return None
        if key == pygame.K_2 and self.selected_index == 0:
            self.world_width = 256
            self.world_height = 256
            return None
        if key == pygame.K_3 and self.selected_index == 0:
            self.world_width = 512
            self.world_height = 512
            return None
        if key == pygame.K_4 and self.selected_index == 0:
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
    
    def _get_field_value(self, field: str) -> any:
        """Get current value for a field."""
        if field == "world_name":
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
        """Create OverworldConfig from current values."""
        from world.overworld.config import OverworldConfig
        
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
    
    def draw(self) -> None:
        """Draw the configuration screen."""
        screen = self.screen
        screen.fill(COLOR_BG)
        
        w, h = screen.get_size()
        
        # Title
        title_text = self.font_title.render("Overworld Configuration", True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(w // 2, 40))
        screen.blit(title_text, title_rect)
        
        # Instructions
        help_text = self.font_small.render(
            "Arrow Keys: Navigate | Enter: Edit | ESC: Cancel | Q: Quit",
            True, (200, 200, 200)
        )
        help_rect = help_text.get_rect(center=(w // 2, h - 60))
        screen.blit(help_text, help_rect)
        
        # Start button
        start_text = self.font_main.render(
            "Press F to Finish and Start Game",
            True, (100, 255, 100)
        )
        start_rect = start_text.get_rect(center=(w // 2, h - 30))
        screen.blit(start_text, start_rect)
        
        # Field labels and values
        start_y = 120
        line_height = 40
        field_labels = {
            "world_name": "World Name:",
            "world_width": "World Width:",
            "world_height": "World Height:",
            "poi_density": "POI Density:",
            "seed": "Random Seed (empty for random):",
            "sight_radius": "Sight Radius:",
            "default_zoom": "Default Zoom Level:",
        }
        
        field_descriptions = {
            "world_name": "World name (Press Enter to edit, R to randomize)",
            "world_width": "World size in tiles (64-2048). Press 1-4 for presets.",
            "world_height": "World height in tiles (64-2048)",
            "poi_density": "Density of Points of Interest (0.01-1.0, higher = more POIs)",
            "seed": "Random seed for world generation (leave empty for random)",
            "sight_radius": "How far you can see (1-50 tiles)",
            "default_zoom": "Starting zoom level (Press Enter or 1-5 to cycle: 50%, 75%, 100%, 125%, 150%)",
        }
        
        for idx, field in enumerate(self.fields):
            y = start_y + idx * line_height
            is_selected = idx == self.selected_index
            is_editing = self.editing_field == field
            
            # Highlight selected row
            if is_selected:
                highlight_rect = pygame.Rect(50, y - 5, w - 100, line_height - 5)
                pygame.draw.rect(screen, (50, 50, 50), highlight_rect)
            
            # Label
            label_text = self.font_main.render(field_labels[field], True, (255, 255, 255))
            screen.blit(label_text, (60, y))
            
            # Value display
            value = self._get_field_value(field)
            if field == "default_zoom":
                # Zoom field - show current zoom level
                if is_selected:
                    display_text = f"{int(self.zoom_levels[self.zoom_index] * 100)}% (Press Enter to cycle)"
                    value_color = (100, 255, 100)  # Green when selected
                else:
                    display_text = f"{int(self.zoom_levels[self.zoom_index] * 100)}%"
                    value_color = (200, 200, 200)
            elif field == "world_name":
                # World name field - show name and randomize hint
                if is_editing:
                    display_text = self.text_buffer
                    if self.cursor_visible:
                        display_text += "_"
                    value_color = (100, 255, 100)  # Green when editing
                elif is_selected:
                    display_text = f"{value} (Press R to randomize)"
                    value_color = (100, 255, 100)  # Green when selected
                else:
                    display_text = str(value)
                    value_color = (200, 200, 200)
            elif is_editing:
                # Show text buffer with cursor
                display_text = self.text_buffer
                if self.cursor_visible:
                    display_text += "_"
                value_color = (100, 255, 100)  # Green when editing
            else:
                if field == "seed" and value == "":
                    display_text = "(random)"
                elif field == "poi_density":
                    display_text = f"{value:.2f}"
                else:
                    display_text = str(value)
                value_color = (200, 200, 200) if not is_selected else (255, 255, 255)
            
            value_text = self.font_main.render(display_text, True, value_color)
            screen.blit(value_text, (350, y))
            
            # Description (small, gray)
            desc_text = self.font_small.render(
                field_descriptions[field],
                True, (150, 150, 150)
            )
            screen.blit(desc_text, (550, y + 5))
        
        # World size presets info
        preset_y = start_y + len(self.fields) * line_height + 20
        preset_text = self.font_small.render(
            "Quick presets (when World Width is selected): 1=Small 2=Medium 3=Large 4=Huge",
            True, (150, 150, 150)
        )
        screen.blit(preset_text, (60, preset_y))

