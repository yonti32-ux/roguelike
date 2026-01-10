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
        """Draw the configuration screen."""
        screen = self.screen
        screen.fill(COLOR_BG)
        
        w, h = screen.get_size()
        
        # Title
        mode_text = "World Generation Presets" if self.mode == "preset" else "Advanced Options"
        title_text = self.font_title.render(mode_text, True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(w // 2, 40))
        screen.blit(title_text, title_rect)
        
        # Mode indicator
        mode_indicator = self.font_small.render(
            f"[Press TAB to switch to {'Advanced Options' if self.mode == 'preset' else 'Presets'}]",
            True, (150, 150, 255)
        )
        mode_rect = mode_indicator.get_rect(center=(w // 2, 70))
        screen.blit(mode_indicator, mode_rect)
        
        # Instructions
        help_text = self.font_small.render(
            "Arrow Keys: Navigate | Enter: Edit/Cycle | TAB: Presets/Advanced | F: Finish | Q: Quit",
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
            
            # Highlight selected row
            if is_selected:
                highlight_rect = pygame.Rect(50, y - 5, w - 100, line_height - 5)
                pygame.draw.rect(screen, (50, 50, 50), highlight_rect)
            
            # Label
            label_text = self.font_main.render(field_labels[field], True, (255, 255, 255))
            screen.blit(label_text, (60, y))
            
            # Value display
            value = self._get_field_value(field)
            if field == "terrain_preset" or field == "world_size" or field == "room_count_preset":
                # Preset fields - show current preset
                if is_selected:
                    if field == "world_size":
                        display_text = f"{value} ({self.world_width}x{self.world_height}) (Press Enter or 1-4 to cycle)"
                    else:
                        display_text = f"{value} (Press Enter to cycle)"
                    value_color = (100, 255, 100)  # Green when selected
                else:
                    if field == "world_size":
                        display_text = f"{value} ({self.world_width}x{self.world_height})"
                    else:
                        display_text = str(value)
                    value_color = (200, 200, 200)
            elif field == "default_zoom":
                # Zoom field - show current zoom level
                if is_selected:
                    display_text = f"{int(self.zoom_levels[self.zoom_index] * 100)}% (Press Enter to cycle)"
                    value_color = (100, 255, 100)  # Green when selected
                else:
                    display_text = f"{int(self.zoom_levels[self.zoom_index] * 100)}%"
                    value_color = (200, 200, 200)
            elif field == "gen_preset" or field == "room_count_preset":
                # Preset fields - show current preset
                if is_selected:
                    display_text = f"{value} (Press Enter to cycle)"
                    value_color = (100, 255, 100)  # Green when selected
                else:
                    display_text = str(value)
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
                    if is_selected and not is_editing:
                        display_text += " (Press Enter to edit)"
                    value_color = (200, 200, 200) if not is_selected else (255, 255, 255)
                elif field == "shop_chance":
                    display_text = f"{value:.2f}"
                    value_color = (200, 200, 200) if not is_selected else (255, 255, 255)
                else:
                    display_text = str(value)
                    if is_selected and field == "seed" and not is_editing:
                        display_text += " (Press Enter to edit)"
                    value_color = (200, 200, 200) if not is_selected else (255, 255, 255)
            
            value_text = self.font_main.render(display_text, True, value_color)
            screen.blit(value_text, (350, y))
            
            # Description (small, gray)
            description = field_descriptions.get(field, "")
            if description:
                desc_text = self.font_small.render(
                    description,
                    True, (150, 150, 150)
                )
                screen.blit(desc_text, (550, y + 5))
        
        # Additional info
        info_y = start_y + len(self.fields) * line_height + 20
        if self.mode == "preset":
            preset_text = self.font_small.render(
                "World Size quick keys (when World Size selected): 1=Small 2=Medium 3=Large 4=Huge",
                True, (150, 150, 150)
            )
            screen.blit(preset_text, (60, info_y))
        else:
            preset_text = self.font_small.render(
                "Quick presets (when World Width is selected): 1=Small 2=Medium 3=Large 4=Huge",
                True, (150, 150, 150)
            )
            screen.blit(preset_text, (60, info_y))

