import pygame
import traceback
import sys
import copy
import random
import math
from typing import List, Optional

from settings import COLOR_BG, FPS
from systems.classes import all_classes, get_class
from systems.character_creation.stat_distribution import StatDistribution
from systems.character_creation.traits import all_traits, get_trait, traits_by_category
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
    SHADOW_OFFSET_X,
    SHADOW_OFFSET_Y,
)

# Lazy import of backgrounds - only import when needed
_backgrounds_for_class_fn = None

def _get_backgrounds_for_class():
    """Lazy import of backgrounds_for_class with error handling."""
    global _backgrounds_for_class_fn
    if _backgrounds_for_class_fn is None:
        try:
            from systems.character_creation import backgrounds_for_class
            _backgrounds_for_class_fn = backgrounds_for_class
        except Exception as e:
            error_msg = f"ERROR: Failed to import backgrounds_for_class: {e}\n"
            sys.stderr.write(error_msg)
            sys.stderr.flush()
            traceback.print_exc(file=sys.stderr)
            sys.stderr.flush()
            # Fallback function that returns empty list
            def _fallback(class_id: str):
                return []
            _backgrounds_for_class_fn = _fallback
    return _backgrounds_for_class_fn


# Random name generator
RANDOM_HERO_NAMES = [
    "Aldric", "Bram", "Cora", "Darrow", "Elara", "Finn", "Gwen", "Hector",
    "Iris", "Jax", "Kira", "Lucian", "Maya", "Nolan", "Orin", "Piper",
    "Quinn", "Raven", "Sage", "Talon", "Vera", "Wren", "Xara", "Zane",
    "Aric", "Brynn", "Cade", "Dara", "Evan", "Faye", "Grey", "Hope",
    "Ivy", "Jace", "Kai", "Leah", "Max", "Nova", "Owen", "Pax",
    "Rune", "Sky", "Tess", "Vex", "Yara", "Zoe",
    "Arden", "Blake", "Case", "Dove", "Echo", "Fox", "Gale", "Haze",
    "Iris", "Jade", "Kip", "Lake", "Mars", "Neo", "Onyx", "Poe",
    "Reed", "Shade", "Thorn", "Vale", "Wren", "Zen"
]


def _generate_random_name() -> str:
    """Generate a random hero name from the list."""
    return random.choice(RANDOM_HERO_NAMES)


class Particle:
    """A small particle that moves randomly around the screen."""
    
    def __init__(self, screen_width: int, screen_height: int):
        self.x = random.uniform(0, screen_width)
        self.y = random.uniform(0, screen_height)
        self.vx = random.uniform(-25, 25)  # Velocity X
        self.vy = random.uniform(-25, 25)  # Velocity Y
        self.size = random.uniform(1.5, 3.0)
        # Subtle colors that fit the character creation theme
        color_variants = [
            (150, 170, 200, 180),  # Soft blue
            (200, 200, 180, 160),  # Soft yellow
            (180, 200, 220, 170),  # Light blue
            (220, 220, 200, 150),  # Pale yellow
            (160, 180, 200, 140),  # Muted blue
            (200, 180, 220, 160),  # Soft purple
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


class CharacterCreationScene:
    """
    Enhanced character creation with class, background, and name selection.
    
    Phase 1: choose a class (Warrior / Rogue / Mage).
    Phase 2: choose a background (filtered by class).
    Phase 3: enter a name for your hero.
    """
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.font_title = pygame.font.SysFont("consolas", 28)
        self.font_main = pygame.font.SysFont("consolas", 22)
        self.font_small = pygame.font.SysFont("consolas", 18)

        self.classes = all_classes()
        self.selected_class_index = 0
        self.selected_background_index = 0
        self.backgrounds = []  # Will be populated when class is selected

        # Four-phase flow: "class" -> "background" -> "stat_distribution" -> "name"
        self.phase: str = "class"
        self.selected_class_id: str = ""  # Store selected class ID
        self.name_buffer: str = ""
        self.max_name_length: int = 16

        # Stat distribution
        self.stat_distribution = StatDistribution()
        self.stat_points_available = 4  # 3-5 points, using 4 as default
        self.selected_stat_index = 0  # Which stat is currently selected
        self.stat_names = [
            ("Max HP", "hp_points", int),
            ("Attack", "attack_points", int),
            ("Defense", "defense_points", int),
            ("Skill Power", "skill_power_points", float),
            ("Crit Chance", "crit_points", float),
            ("Dodge Chance", "dodge_points", float),
            ("Speed", "speed_points", float),
        ]

        # Trait system
        self.selected_traits: List[str] = []  # List of selected trait IDs
        self.trait_points_available = 5  # Starting trait points (5-7, using 5)
        self.selected_trait_index = 0  # Which trait is currently selected
        self.trait_category_filter: Optional[str] = None  # Filter by category (None = all)
        self.trait_categories = ["all", "personality", "physical", "mental", "social"]

        # Simple blink for the name cursor
        self.cursor_visible: bool = True
        self.cursor_timer: float = 0.0
        
        # Animation timer for background effects
        self.animation_timer: float = 0.0
        
        # Initialize particles
        w, h = screen.get_size()
        self.particles: List["Particle"] = []
        num_particles = 50  # More particles for richer effect
        for _ in range(num_particles):
            self.particles.append(Particle(w, h))
        
        # Class card configuration (easily customizable)
        # Will be updated dynamically based on number of classes
        self.card_config = {
            "cards_per_row": 2,  # Default, will adjust
            "card_width": 600,  # Large cards for few classes
            "card_height": 450,  # Large cards for few classes
            "card_spacing": 30,
            "card_padding": 25,
        }

    def run(self) -> tuple[str, str, StatDistribution, List[str], str] | None:
        """
        Main loop for the character creation scene.
        Returns (class_id, background_id, stat_distribution, traits, hero_name) or None if the player quits.
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

            # Cursor blink for name input
            self.cursor_timer += dt
            if self.cursor_timer >= 0.5:
                self.cursor_timer = 0.0
                self.cursor_visible = not self.cursor_visible

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None

                if event.type == pygame.KEYDOWN:
                    # Debug: Log the key press
                    try:
                        key_val = getattr(event, 'key', None)
                        sys.stderr.write(f"DEBUG: Key pressed: {key_val}\n")
                        sys.stderr.flush()
                    except:
                        pass
                    
                    # Global quit shortcut
                    if event.key == pygame.K_q:
                        return None

                    try:
                        if self.phase == "class":
                            handled = self._handle_class_keydown(event)
                            if isinstance(handled, tuple):
                                # (class_id, background_id, hero_name) returned
                                return handled
                            elif handled is None:
                                # None means quit
                                return None
                            elif handled is False:
                                # False means continue loop (navigation)
                                continue
                        elif self.phase == "background":
                            handled = self._handle_background_keydown(event)
                            if isinstance(handled, tuple):
                                return handled
                            elif handled is None:
                                return None
                            elif handled is False:
                                continue  # Continue loop
                        elif self.phase == "stat_distribution":
                            handled = self._handle_stat_distribution_keydown(event)
                            if isinstance(handled, tuple):
                                return handled
                            elif handled is None:
                                return None
                            elif handled is False:
                                continue  # Continue loop
                        else:  # phase == "name"
                            handled = self._handle_name_keydown(event)
                            if isinstance(handled, tuple):
                                return handled
                            elif handled is None:
                                return None
                            elif handled is False:
                                continue  # Continue loop
                    except Exception as e:
                        # Print error for debugging (use stderr so it always shows)
                        error_msg = f"Error in character creation key handling: {e}\n"
                        sys.stderr.write(error_msg)
                        sys.stderr.flush()
                        traceback.print_exc(file=sys.stderr)
                        sys.stderr.flush()
                        # Don't crash - just ignore the key press
                        pass

            try:
                self.draw()
            except Exception as e:
                error_msg = f"ERROR: Failed to draw character creation scene: {e}\n"
                sys.stderr.write(error_msg)
                sys.stderr.flush()
                traceback.print_exc(file=sys.stderr)
                sys.stderr.flush()
                # Try to draw a simple error message
                self.screen.fill(COLOR_BG)
                try:
                    error_msg_surf = self.font_main.render(f"Error: {e}", True, (255, 0, 0))
                    self.screen.blit(error_msg_surf, (40, 40))
                except:
                    pass
            pygame.display.flip()

    # ------------------------------------------------------------------
    # Input handling
    # ------------------------------------------------------------------

    def _handle_class_keydown(self, event: pygame.event.Event):
        """
        Handle key presses while choosing a class.
        Esc here quits the game; Enter moves to background selection.
        """
        try:
            sys.stderr.write(f"DEBUG: _handle_class_keydown called, key={event.key}\n")
            sys.stderr.flush()
            
            if event.key == pygame.K_ESCAPE:
                sys.stderr.write("DEBUG: ESC pressed, returning None\n")
                sys.stderr.flush()
                return None  # signal quit to caller

            sys.stderr.write(f"DEBUG: Checking navigation keys, classes={len(self.classes) if self.classes else 0}\n")
            sys.stderr.flush()

            if event.key in (pygame.K_RIGHT, pygame.K_d, pygame.K_DOWN, pygame.K_s):
                sys.stderr.write("DEBUG: Right/Down key pressed\n")
                sys.stderr.flush()
                if self.classes:
                    self.selected_class_index = (self.selected_class_index + 1) % len(self.classes)
                    sys.stderr.write(f"DEBUG: Selected class index now: {self.selected_class_index}\n")
                    sys.stderr.flush()
                # Return False to indicate "stay in scene, continue loop"
                return False

            elif event.key in (pygame.K_LEFT, pygame.K_a, pygame.K_UP, pygame.K_w):
                sys.stderr.write("DEBUG: Left/Up key pressed\n")
                sys.stderr.flush()
                if self.classes:
                    self.selected_class_index = (self.selected_class_index - 1) % len(self.classes)
                    sys.stderr.write(f"DEBUG: Selected class index now: {self.selected_class_index}\n")
                    sys.stderr.flush()
                # Return False to indicate "stay in scene, continue loop"
                return False

            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                sys.stderr.write("DEBUG: Enter/Space pressed, moving to background selection\n")
                sys.stderr.flush()
                # Move to background selection
                if not self.classes:
                    return None

                selected_class = self.classes[self.selected_class_index]
                self.selected_class_id = selected_class.id
                sys.stderr.write(f"DEBUG: Selected class: {selected_class.id}\n")
                sys.stderr.flush()
                try:
                    backgrounds_fn = _get_backgrounds_for_class()
                    sys.stderr.write("DEBUG: Got backgrounds function\n")
                    sys.stderr.flush()
                    self.backgrounds = backgrounds_fn(selected_class.id)
                    sys.stderr.write(f"DEBUG: Got {len(self.backgrounds)} backgrounds\n")
                    sys.stderr.flush()
                except Exception as e:
                    error_msg = f"ERROR: Failed to get backgrounds for class {selected_class.id}: {e}\n"
                    sys.stderr.write(error_msg)
                    sys.stderr.flush()
                    traceback.print_exc(file=sys.stderr)
                    sys.stderr.flush()
                    self.backgrounds = []  # Fallback to empty list
                self.selected_background_index = 0
                self.phase = "background"
                sys.stderr.write("DEBUG: Phase changed to background, returning False (continue loop)\n")
                sys.stderr.flush()
                return False  # Stay in scene, continue loop to show background selection

            sys.stderr.write("DEBUG: No matching key, returning False (continue loop)\n")
            sys.stderr.flush()
            return False  # Continue loop, no action for unknown keys
        except Exception as e:
            error_msg = f"ERROR in _handle_class_keydown: {e}\n"
            sys.stderr.write(error_msg)
            sys.stderr.flush()
            traceback.print_exc(file=sys.stderr)
            sys.stderr.flush()
            return  # Return None on error

    def _handle_background_keydown(self, event: pygame.event.Event):
        """
        Handle key presses while choosing a background.
        Esc returns to class selection. Enter moves to name entry.
        """
        # Esc: go back to class selection
        if event.key == pygame.K_ESCAPE:
            self.phase = "class"
            return False  # Continue loop

        if not self.backgrounds:
            return False  # Continue loop

        if event.key in (pygame.K_RIGHT, pygame.K_d, pygame.K_DOWN, pygame.K_s):
            self.selected_background_index = (self.selected_background_index + 1) % len(self.backgrounds)
            return False  # Continue loop

        elif event.key in (pygame.K_LEFT, pygame.K_a, pygame.K_UP, pygame.K_w):
            self.selected_background_index = (self.selected_background_index - 1) % len(self.backgrounds)
            return False  # Continue loop

        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            # Move to stat distribution phase
            self.phase = "stat_distribution"
            self.selected_stat_index = 0
            # Reset stat distribution for fresh allocation
            self.stat_distribution = StatDistribution()
            return False  # Continue loop to show stat distribution

        return False  # Continue loop for unknown keys

    def _handle_stat_distribution_keydown(self, event: pygame.event.Event):
        """
        Handle key presses while distributing stat points.
        Esc returns to background selection. Enter confirms and moves to name.
        """
        # Esc: go back to background selection
        if event.key == pygame.K_ESCAPE:
            self.phase = "background"
            return False  # Continue loop

        # Navigation: Up/Down or W/S to select stat
        if event.key in (pygame.K_UP, pygame.K_w):
            self.selected_stat_index = (self.selected_stat_index - 1) % len(self.stat_names)
            return False
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.selected_stat_index = (self.selected_stat_index + 1) % len(self.stat_names)
            return False

        # Adjustment: Left/Right or A/D to adjust points
        stat_name, attr_name, stat_type = self.stat_names[self.selected_stat_index]
        current_value = getattr(self.stat_distribution, attr_name)
        points_spent = self.stat_distribution.total_points_spent()

        if event.key in (pygame.K_LEFT, pygame.K_a):
            # Decrease this stat (if it's above 0)
            if current_value > 0:
                if stat_type == int:
                    setattr(self.stat_distribution, attr_name, current_value - 1)
                else:  # float
                    setattr(self.stat_distribution, attr_name, max(0.0, current_value - 0.1))
            return False
        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            # Increase this stat (if points available)
            remaining_points = self.stat_points_available - points_spent
            if remaining_points > 0:
                if stat_type == int:
                    setattr(self.stat_distribution, attr_name, current_value + 1)
                else:  # float
                    # For float stats, allow 0.1 increments
                    increment = min(0.1, remaining_points)
                    setattr(self.stat_distribution, attr_name, current_value + increment)
            return False

        # Enter/Space: Confirm and move to traits
        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
            selected_class = self.classes[self.selected_class_index]
            self.phase = "traits"
            self.selected_trait_index = 0
            self.selected_traits = []  # Reset traits for fresh selection
            return False  # Continue loop to show trait selection

        return False  # Continue loop

    def _get_available_traits(self) -> List:
        """Get list of available traits, filtered by category if needed."""
        if self.trait_category_filter and self.trait_category_filter != "all":
            return traits_by_category(self.trait_category_filter)
        return all_traits()

    def _handle_traits_keydown(self, event: pygame.event.Event):
        """
        Handle key presses while selecting traits.
        Esc returns to stat distribution. Enter confirms and moves to name.
        """
        # Esc: go back to stat distribution
        if event.key == pygame.K_ESCAPE:
            self.phase = "stat_distribution"
            return False  # Continue loop

        # Get available traits (filtered by category if needed)
        available_traits = self._get_available_traits()
        if not available_traits:
            return False

        # Navigation: Up/Down or W/S to select trait
        if event.key in (pygame.K_UP, pygame.K_w):
            self.selected_trait_index = (self.selected_trait_index - 1) % len(available_traits)
            return False
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.selected_trait_index = (self.selected_trait_index + 1) % len(available_traits)
            return False

        # Category filter: Left/Right or A/D to change category
        if event.key in (pygame.K_LEFT, pygame.K_a):
            current_idx = self.trait_categories.index(self.trait_category_filter or "all")
            new_idx = (current_idx - 1) % len(self.trait_categories)
            self.trait_category_filter = None if self.trait_categories[new_idx] == "all" else self.trait_categories[new_idx]
            self.selected_trait_index = 0  # Reset selection when changing filter
            return False
        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            current_idx = self.trait_categories.index(self.trait_category_filter or "all")
            new_idx = (current_idx + 1) % len(self.trait_categories)
            self.trait_category_filter = None if self.trait_categories[new_idx] == "all" else self.trait_categories[new_idx]
            self.selected_trait_index = 0  # Reset selection when changing filter
            return False

        # Select/Deselect trait: Enter/Space
        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
            if available_traits:
                selected_trait = available_traits[self.selected_trait_index]
                trait_id = selected_trait.id
                
                if trait_id in self.selected_traits:
                    # Deselect trait (refund points)
                    self.selected_traits.remove(trait_id)
                else:
                    # Try to select trait
                    trait = get_trait(trait_id)
                    points_spent = sum(get_trait(tid).cost for tid in self.selected_traits)
                    points_remaining = self.trait_points_available - points_spent
                    
                    # Check if we have enough points
                    if points_remaining >= trait.cost:
                        # Check for conflicts
                        has_conflict = False
                        for existing_trait_id in self.selected_traits:
                            existing_trait = get_trait(existing_trait_id)
                            if trait_id in existing_trait.conflicts or existing_trait_id in trait.conflicts:
                                has_conflict = True
                                break
                        
                        if not has_conflict:
                            self.selected_traits.append(trait_id)
            return False

        # Tab: Move to name (Enter/Space is for select/deselect)
        if event.key == pygame.K_TAB:
            selected_class = self.classes[self.selected_class_index]
            self.phase = "name"
            self.name_buffer = selected_class.name
            return False  # Continue loop to show name input

        return False  # Continue loop

    def _get_available_traits(self) -> List:
        """Get list of available traits, filtered by category if needed."""
        if self.trait_category_filter and self.trait_category_filter != "all":
            return traits_by_category(self.trait_category_filter)
        return all_traits()

    def _handle_name_keydown(self, event: pygame.event.Event):
        """
        Handle key presses while entering a name.
        Esc returns to traits. Enter confirms.
        """
        # Esc: go back to traits
        if event.key == pygame.K_ESCAPE:
            self.phase = "traits"
            return False  # Continue loop

        # Confirm name
        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            if not self.classes or not self.backgrounds:
                return None  # Error, quit

            selected_class = self.classes[self.selected_class_index]
            selected_background = self.backgrounds[self.selected_background_index]
            final_name = self.name_buffer.strip() or selected_class.name
            return (selected_class.id, selected_background.id, self.stat_distribution, self.selected_traits, final_name)

        # Random name generator (R key)
        if event.key == pygame.K_r:
            self.name_buffer = _generate_random_name()
            return False  # Continue loop

        # Delete last character
        if event.key == pygame.K_BACKSPACE:
            if self.name_buffer:
                self.name_buffer = self.name_buffer[:-1]
            return False  # Continue loop

        # Add typed characters (basic, printable only)
        if event.unicode:
            ch = event.unicode
            if ch.isprintable() and not ch.isspace():
                if len(self.name_buffer) < self.max_name_length:
                    self.name_buffer += ch

        return False  # Continue loop

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw(self) -> None:
        w, h = self.screen.get_size()
        
        # Draw enhanced gradient background with animated effect
        from ui.screen_components import draw_gradient_background
        # Add subtle animation to gradient colors
        pulse = math.sin(self.animation_timer * 0.5) * 5
        start_color = tuple(min(255, max(0, c + int(pulse))) for c in COLOR_GRADIENT_START)
        end_color = tuple(min(255, max(0, c + int(pulse * 0.7))) for c in COLOR_GRADIENT_END)
        draw_gradient_background(
            self.screen, 0, 0, w, h,
            start_color, end_color, True
        )
        
        # Draw particles (behind UI elements)
        for particle in self.particles:
            particle.draw(self.screen)

        # Title with shadow and subtle animation
        title_color = COLOR_TITLE
        title_pulse = int(8 * abs(math.sin(self.animation_timer * 1.5)))
        title_color = tuple(min(255, c + title_pulse) for c in title_color)
        
        title_surf = self.font_title.render("Character Creation", True, title_color)
        title_shadow = self.font_title.render("Character Creation", True, COLOR_SHADOW[:3])
        title_x = w // 2 - title_surf.get_width() // 2
        title_y = 40
        
        self.screen.blit(title_shadow, (title_x + SHADOW_OFFSET_X, title_y + SHADOW_OFFSET_Y))
        self.screen.blit(title_surf, (title_x, title_y))

        if not self.classes:
            msg = self.font_main.render("No classes defined.", True, (255, 100, 100))
            self.screen.blit(msg, (w // 2 - msg.get_width() // 2, h // 2))
            return

        if self.phase == "class":
            if not self.classes or self.selected_class_index >= len(self.classes):
                msg = self.font_main.render("Error: No class selected.", True, (255, 100, 100))
                self.screen.blit(msg, (w // 2 - msg.get_width() // 2, h // 2))
                return
            selected = self.classes[self.selected_class_index]
            self._draw_class_phase(selected, w, h)
        elif self.phase == "background":
            selected_class = self.classes[self.selected_class_index]
            selected_background = self.backgrounds[self.selected_background_index] if self.backgrounds else None
            self._draw_background_phase(selected_class, selected_background, w, h)
        elif self.phase == "stat_distribution":
            selected_class = self.classes[self.selected_class_index]
            selected_background = self.backgrounds[self.selected_background_index] if self.backgrounds else None
            self._draw_stat_distribution_phase(selected_class, selected_background, w, h)
        else:  # phase == "name"
            selected_class = self.classes[self.selected_class_index]
            self._draw_name_phase(selected_class, w, h)

    def _draw_class_phase(self, selected, w: int, h: int) -> None:
        """Draw the 'choose class' UI with card-based selection."""
        # Draw class cards in a grid layout (scalable for more classes)
        self._draw_class_cards(w, h)
        
        # Navigation arrows indicator (visual feedback with animation)
        if len(self.classes) > 1:
            arrow_y = h // 2
            # Animate arrows with subtle pulse
            arrow_pulse = int(10 * abs(math.sin(self.animation_timer * 3)))
            arrow_color = tuple(min(255, c + arrow_pulse) for c in COLOR_SUBTITLE)
            
            # Left arrow
            if self.selected_class_index > 0:
                left_arrow = "◄"
                arrow_surf = self.font_main.render(left_arrow, True, arrow_color)
                # Add shadow for depth
                arrow_shadow = self.font_main.render(left_arrow, True, COLOR_SHADOW[:3])
                self.screen.blit(arrow_shadow, (20 + SHADOW_OFFSET_X, arrow_y - arrow_surf.get_height() // 2 + SHADOW_OFFSET_Y))
                self.screen.blit(arrow_surf, (20, arrow_y - arrow_surf.get_height() // 2))
            # Right arrow
            if self.selected_class_index < len(self.classes) - 1:
                right_arrow = "►"
                arrow_surf = self.font_main.render(right_arrow, True, arrow_color)
                # Add shadow for depth
                arrow_shadow = self.font_main.render(right_arrow, True, COLOR_SHADOW[:3])
                self.screen.blit(arrow_shadow, (w - 40 + SHADOW_OFFSET_X, arrow_y - arrow_surf.get_height() // 2 + SHADOW_OFFSET_Y))
                self.screen.blit(arrow_surf, (w - 40, arrow_y - arrow_surf.get_height() // 2))
        
        # Controls hint panel
        hint_text = "←/→ or W/S: change class   Enter/Space: continue   Esc/Q: quit"
        hint = self.font_small.render(hint_text, True, (180, 180, 180))
        hint_panel_width = hint.get_width() + 40
        hint_panel_height = 35
        hint_panel_x = w // 2 - hint_panel_width // 2
        hint_panel_y = h - 50
        
        hint_panel = pygame.Surface((hint_panel_width, hint_panel_height), pygame.SRCALPHA)
        hint_panel.fill((0, 0, 0, 150))
        pygame.draw.rect(hint_panel, COLOR_BORDER_BRIGHT, (0, 0, hint_panel_width, hint_panel_height), 1)
        self.screen.blit(hint_panel, (hint_panel_x, hint_panel_y))
        self.screen.blit(hint, (hint_panel_x + 20, hint_panel_y + 8))
    
    def _draw_class_cards(self, w: int, h: int) -> None:
        """
        Draw class selection cards in a grid layout.
        Modular and scalable - automatically adjusts for any number of classes.
        Uses self.card_config for easy customization.
        """
        if not self.classes:
            return
        
        # Auto-adjust card size based on number of classes
        num_classes = len(self.classes)
        card_spacing = 20
        card_padding = 20
        
        if num_classes <= 3:
            # For 3 or fewer classes, use really large cards side by side (like the image)
            cards_per_row = num_classes
            # Calculate width to fill screen with spacing
            total_spacing = (num_classes - 1) * card_spacing
            card_width = (w - 80 - total_spacing) // num_classes  # 80 for margins
            card_height = h - 250  # Leave space for title and hint
        elif num_classes <= 6:
            # For 4-6 classes, use medium-large cards
            cards_per_row = 3
            total_spacing = (cards_per_row - 1) * card_spacing
            card_width = (w - 80 - total_spacing) // cards_per_row
            card_height = 380
        else:
            # For 7+ classes, use smaller cards
            cards_per_row = 3
            total_spacing = (cards_per_row - 1) * card_spacing
            card_width = (w - 80 - total_spacing) // cards_per_row
            card_height = 280
        
        # Calculate grid layout
        num_rows = (num_classes + cards_per_row - 1) // cards_per_row
        
        # Calculate total width and height needed
        total_width = cards_per_row * card_width + (cards_per_row - 1) * card_spacing
        total_height = num_rows * card_height + (num_rows - 1) * card_spacing
        
        # Center the grid horizontally
        total_width = cards_per_row * card_width + (cards_per_row - 1) * card_spacing
        start_x = (w - total_width) // 2
        start_y = 120
        
        # Draw each class card
        for idx, class_def in enumerate(self.classes):
            row = idx // cards_per_row
            col = idx % cards_per_row
            
            card_x = start_x + col * (card_width + card_spacing)
            card_y = start_y + row * (card_height + card_spacing)
            
            is_selected = (idx == self.selected_class_index)
            self._draw_class_card(class_def, card_x, card_y, card_width, card_height, is_selected, card_padding)
    
    def _draw_class_card(
        self, 
        class_def, 
        x: int, 
        y: int, 
        width: int, 
        height: int, 
        is_selected: bool,
        padding: int
    ) -> None:
        """
        Draw a single class card. Modular function - easy to customize card appearance.
        Now includes all details since we removed the lower panel.
        """
        # Card background with selection highlight
        card_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        
        if is_selected:
            # Selected card - brighter background with golden outline and glow effect
            card_surf.fill(COLOR_SELECTED_BG_BRIGHT)
            # Golden outline (thicker for larger cards)
            golden_color = (255, 215, 0)  # Gold color
            outline_width = 4 if width > 500 else 3
            pygame.draw.rect(card_surf, golden_color, (0, 0, width, height), outline_width)
            # Top accent bar in gold
            pygame.draw.rect(card_surf, golden_color, (0, 0, width, 10))
            # Very subtle inner glow effect (reduced)
            inner_glow = (255, 235, 150, 50)  # Reduced from 100 to 50
            inner_surf = pygame.Surface((width - 8, height - 8), pygame.SRCALPHA)
            inner_surf.fill(inner_glow)
            card_surf.blit(inner_surf, (4, 4), special_flags=pygame.BLEND_ALPHA_SDL2)
        else:
            # Unselected card - dimmer background
            card_surf.fill((30, 35, 45, 240))
            pygame.draw.rect(card_surf, COLOR_BORDER_BRIGHT, (0, 0, width, height), 2)
        
        # Add enhanced shadow for selected card (more prominent for larger cards)
        if is_selected:
            shadow_size = 6 if width > 500 else 4
            # Outer shadow (subtle)
            shadow = pygame.Surface((width + shadow_size, height + shadow_size), pygame.SRCALPHA)
            shadow.fill((0, 0, 0, 100))
            self.screen.blit(shadow, (x - shadow_size // 2, y - shadow_size // 2))
            # Subtle golden glow effect (reduced intensity)
            glow_size = 6
            glow = pygame.Surface((width + glow_size * 2, height + glow_size * 2), pygame.SRCALPHA)
            for i in range(glow_size, 0, -1):
                alpha = 15 // (i + 1)  # Reduced from 30 to 15
                golden_glow = (255, 215, 0, alpha)
                glow_rect = pygame.Rect(glow_size - i, glow_size - i, width + i * 2, height + i * 2)
                pygame.draw.rect(glow, golden_glow, glow_rect, 1)  # Thinner lines
            self.screen.blit(glow, (x - glow_size, y - glow_size), special_flags=pygame.BLEND_ALPHA_SDL2)
        
        self.screen.blit(card_surf, (x, y))
        
        # Card content
        content_x = x + padding
        content_y = y + padding
        current_y = content_y
        
        # Class name (bigger for larger cards, with gold color if selected)
        if is_selected:
            name_color = (255, 215, 0)  # Gold color for selected
            # Add shadow to name
            name_shadow = self.font_title.render(class_def.name, True, COLOR_SHADOW[:3])
            self.screen.blit(name_shadow, (content_x + SHADOW_OFFSET_X, current_y + SHADOW_OFFSET_Y))
        else:
            name_color = COLOR_TEXT
        name_surf = self.font_title.render(class_def.name, True, name_color)
        self.screen.blit(name_surf, (content_x, current_y))
        current_y += 35
        
        # Description (full description for large cards)
        desc_lines = self._wrap_text(class_def.description, self.font_small, width - padding * 2)
        for line in desc_lines:
            desc_surf = self.font_small.render(line, True, COLOR_TEXT_DIM if not is_selected else COLOR_TEXT)
            self.screen.blit(desc_surf, (content_x, current_y))
            current_y += 20
        
        current_y += 15
        
        # Stats section (full stats display like in the image)
        stats_label = self.font_small.render("Base Stats:", True, COLOR_SUBTITLE if is_selected else COLOR_TEXT_DIM)
        self.screen.blit(stats_label, (content_x, current_y))
        current_y += 25
        
        bs = class_def.base_stats
        # Two-column layout for stats (like in the image)
        stats_left = [
            f"Max HP: {bs.max_hp}",
            f"Defense: {bs.defense}",
            f"Skill Power: {bs.skill_power:.1f}x",
            f"Dodge: {int(bs.dodge_chance * 100)}%",
            f"Max Mana: {bs.max_mana}",
        ]
        stats_right = [
            f"Attack: {bs.attack}",
            f"Speed: {bs.speed:.1f}x",
            f"Crit Chance: {int(bs.crit_chance * 100)}%",
            f"Status Resist: {int(bs.status_resist * 100)}%",
            f"Max Stamina: {bs.max_stamina}",
        ]
        
        # Draw stats in two columns
        stats_y = current_y
        for i in range(max(len(stats_left), len(stats_right))):
            if i < len(stats_left):
                left_surf = self.font_small.render(stats_left[i], True, COLOR_TEXT if is_selected else COLOR_TEXT_DIM)
                self.screen.blit(left_surf, (content_x + 10, stats_y))
            if i < len(stats_right):
                right_surf = self.font_small.render(stats_right[i], True, COLOR_TEXT if is_selected else COLOR_TEXT_DIM)
                self.screen.blit(right_surf, (content_x + width // 2, stats_y))
            stats_y += 20
        
        current_y = stats_y + 15
        
        # Starting perks
        if class_def.starting_perks:
            perks_label = self.font_small.render("Starting Perks:", True, COLOR_SUBTITLE if is_selected else COLOR_TEXT_DIM)
            self.screen.blit(perks_label, (content_x, current_y))
            current_y += 22
            for pid in class_def.starting_perks:
                perk_surf = self.font_small.render(f"• {pid}", True, COLOR_TEXT if is_selected else COLOR_TEXT_DIM)
                self.screen.blit(perk_surf, (content_x + 10, current_y))
                current_y += 18
        
        # Starting skills
        if class_def.starting_skills:
            skills_label = self.font_small.render("Starting Skills:", True, COLOR_SUBTITLE if is_selected else COLOR_TEXT_DIM)
            self.screen.blit(skills_label, (content_x, current_y))
            current_y += 22
            for sid in class_def.starting_skills:
                skill_surf = self.font_small.render(f"• {sid}", True, COLOR_TEXT if is_selected else COLOR_TEXT_DIM)
                self.screen.blit(skill_surf, (content_x + 10, current_y))
                current_y += 18
        
        # Starting items
        if class_def.starting_items:
            items_label = self.font_small.render("Starting Items:", True, COLOR_SUBTITLE if is_selected else COLOR_TEXT_DIM)
            self.screen.blit(items_label, (content_x, current_y))
            current_y += 22
            for iid in class_def.starting_items:
                item_surf = self.font_small.render(f"• {iid}", True, COLOR_TEXT if is_selected else COLOR_TEXT_DIM)
                self.screen.blit(item_surf, (content_x + 10, current_y))
                current_y += 18
        
        # Starting gold
        from ui.screen_constants import COLOR_GOLD
        gold_label = self.font_small.render("Starting Gold:", True, COLOR_SUBTITLE if is_selected else COLOR_TEXT_DIM)
        self.screen.blit(gold_label, (content_x, current_y))
        gold_surf = self.font_small.render(str(class_def.starting_gold), True, COLOR_GOLD)
        self.screen.blit(gold_surf, (content_x + 10, current_y + 22))
    
    def _draw_class_details(self, selected, w: int, h: int) -> None:
        """
        Draw detailed information about the selected class.
        Modular function - easy to customize what details are shown.
        """
        # Details panel (below cards or on the side)
        panel_width = w - 80
        panel_height = 280
        panel_x = 40
        panel_y = h - panel_height - 80
        
        panel_surf = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel_surf.fill(COLOR_BG_PANEL)
        pygame.draw.rect(panel_surf, COLOR_BORDER_BRIGHT, (0, 0, panel_width, panel_height), 2)
        self.screen.blit(panel_surf, (panel_x, panel_y))
        
        # Content area
        content_x = panel_x + 30
        content_y = panel_y + 20
        y = content_y
        
        # Class name with shadow
        name_surf = self.font_main.render(selected.name, True, COLOR_TITLE)
        name_shadow = self.font_main.render(selected.name, True, COLOR_SHADOW[:3])
        name_x = w // 2 - name_surf.get_width() // 2
        self.screen.blit(name_shadow, (name_x + SHADOW_OFFSET_X, y + SHADOW_OFFSET_Y))
        self.screen.blit(name_surf, (name_x, y))
        y += 35

        # Description (wrapped)
        desc_lines = self._wrap_text(selected.description, self.font_small, w - 160)
        for line in desc_lines:
            surf = self.font_small.render(line, True, COLOR_TEXT)
            self.screen.blit(surf, (content_x, y))
            y += 20

        y += 10

        # Stats section with panel
        stats_panel_width = 300
        stats_panel_height = 180
        stats_panel_x = content_x
        stats_panel_y = y
        
        stats_panel = pygame.Surface((stats_panel_width, stats_panel_height), pygame.SRCALPHA)
        stats_panel.fill((20, 25, 35, 200))
        pygame.draw.rect(stats_panel, COLOR_BORDER_BRIGHT, (0, 0, stats_panel_width, stats_panel_height), 1)
        self.screen.blit(stats_panel, (stats_panel_x, stats_panel_y))
        
        stats_label = self.font_small.render("Base Stats:", True, COLOR_SUBTITLE)
        self.screen.blit(stats_label, (stats_panel_x + 10, stats_panel_y + 10))
        
        stats_y = stats_panel_y + 30
        bs = selected.base_stats
        stats_lines = [
            f"Max HP: {bs.max_hp}",
            f"Attack: {bs.attack}",
            f"Defense: {bs.defense}",
            f"Skill Power: {bs.skill_power:.1f}x",
            f"Crit Chance: {int(bs.crit_chance * 100)}%",
            f"Dodge Chance: {int(bs.dodge_chance * 100)}%",
            f"Status Resist: {int(bs.status_resist * 100)}%",
        ]
        for line in stats_lines:
            surf = self.font_small.render(line, True, COLOR_TEXT)
            self.screen.blit(surf, (stats_panel_x + 20, stats_y))
            stats_y += 20

        # Starting perks / skills / items (right side)
        right_panel_x = w // 2 + 40
        right_panel_y = y
        
        perks_label = self.font_small.render("Starting Perks:", True, COLOR_SUBTITLE)
        self.screen.blit(perks_label, (right_panel_x, right_panel_y))
        py = right_panel_y + 22
        for pid in selected.starting_perks:
            surf = self.font_small.render(f"• {pid}", True, COLOR_TEXT)
            self.screen.blit(surf, (right_panel_x + 10, py))
            py += 18

        skills_label = self.font_small.render("Starting Skills:", True, COLOR_SUBTITLE)
        self.screen.blit(skills_label, (right_panel_x, py + 8))
        py += 30
        for sid in selected.starting_skills:
            surf = self.font_small.render(f"• {sid}", True, COLOR_TEXT)
            self.screen.blit(surf, (right_panel_x + 10, py))
            py += 18

        items_label = self.font_small.render("Starting Items:", True, COLOR_SUBTITLE)
        self.screen.blit(items_label, (right_panel_x, py + 8))
        py += 30
        for iid in selected.starting_items:
            surf = self.font_small.render(f"• {iid}", True, COLOR_TEXT)
            self.screen.blit(surf, (right_panel_x + 10, py))
            py += 18

        from ui.screen_constants import COLOR_GOLD
        gold_surf = self.font_small.render(
            f"Starting Gold: {selected.starting_gold}",
            True,
            COLOR_GOLD,
        )
        self.screen.blit(gold_surf, (right_panel_x, py + 8))

    def _draw_background_phase(self, selected_class, selected_background, w: int, h: int) -> None:
        """Draw the 'choose background' UI."""
        if not selected_background:
            msg = self.font_main.render("No backgrounds available.", True, (255, 100, 100))
            self.screen.blit(msg, (w // 2 - msg.get_width() // 2, h // 2))
            return

        # Main content panel
        panel_width = w - 80
        panel_height = h - 200
        panel_x = 40
        panel_y = 100
        
        panel_surf = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel_surf.fill(COLOR_BG_PANEL)
        pygame.draw.rect(panel_surf, COLOR_BORDER_BRIGHT, (0, 0, panel_width, panel_height), 2)
        self.screen.blit(panel_surf, (panel_x, panel_y))

        y = panel_y + 30
        title = self.font_main.render("Choose Your Background", True, COLOR_TITLE)
        title_shadow = self.font_main.render("Choose Your Background", True, COLOR_SHADOW[:3])
        title_x = w // 2 - title.get_width() // 2
        self.screen.blit(title_shadow, (title_x + SHADOW_OFFSET_X, y + SHADOW_OFFSET_Y))
        self.screen.blit(title, (title_x, y))
        y += 40

        class_label = self.font_small.render(
            f"Class: {selected_class.name}",
            True,
            COLOR_SUBTITLE,
        )
        self.screen.blit(class_label, (w // 2 - class_label.get_width() // 2, y))
        y += 40

        # Background name
        name_surf = self.font_main.render(selected_background.name, True, COLOR_TITLE)
        name_shadow = self.font_main.render(selected_background.name, True, COLOR_SHADOW[:3])
        name_x = w // 2 - name_surf.get_width() // 2
        self.screen.blit(name_shadow, (name_x + SHADOW_OFFSET_X, y + SHADOW_OFFSET_Y))
        self.screen.blit(name_surf, (name_x, y))
        y += 40

        # Description (wrapped)
        desc_lines = self._wrap_text(selected_background.description, self.font_small, w - 160)
        for line in desc_lines:
            surf = self.font_small.render(line, True, COLOR_TEXT)
            self.screen.blit(surf, (panel_x + 30, y))
            y += 22

        y += 15

        # Stat modifiers (percentage-based) - only show non-default values
        from systems.stats import StatBlock as DefaultStatBlock
        default_mods = DefaultStatBlock()
        mods = selected_background.stat_modifiers
        
        # Check if any modifiers differ from defaults
        has_modifiers = (
            mods.max_hp != default_mods.max_hp or
            mods.attack != default_mods.attack or
            mods.defense != default_mods.defense or
            mods.skill_power != default_mods.skill_power or
            mods.crit_chance != default_mods.crit_chance or
            mods.dodge_chance != default_mods.dodge_chance or
            mods.status_resist != default_mods.status_resist or
            mods.speed != default_mods.speed or
            mods.max_mana != default_mods.max_mana or
            mods.max_stamina != default_mods.max_stamina or
            mods.stamina_regen_bonus != default_mods.stamina_regen_bonus or
            mods.mana_regen_bonus != default_mods.mana_regen_bonus or
            mods.initiative != default_mods.initiative or
            mods.movement_points_bonus != default_mods.movement_points_bonus
        )
        
        if has_modifiers:
            mods_label = self.font_small.render("Stat Modifiers:", True, (220, 220, 180))
            self.screen.blit(mods_label, (60, y))
            y += 24

            mod_lines = []
            # Only display modifiers that differ from defaults
            if mods.max_hp != default_mods.max_hp:
                mod_lines.append(f"Max HP: {mods.max_hp*100:+.0f}%")
            if mods.attack != default_mods.attack:
                mod_lines.append(f"Attack: {mods.attack*100:+.0f}%")
            if mods.defense != default_mods.defense:
                mod_lines.append(f"Defense: {mods.defense*100:+.0f}%")
            if mods.skill_power != default_mods.skill_power:
                mod_lines.append(f"Skill Power: {mods.skill_power*100:+.1f}%")
            if mods.crit_chance != default_mods.crit_chance:
                mod_lines.append(f"Crit Chance: {mods.crit_chance*100:+.0f}%")
            if mods.dodge_chance != default_mods.dodge_chance:
                mod_lines.append(f"Dodge Chance: {mods.dodge_chance*100:+.0f}%")
            if mods.status_resist != default_mods.status_resist:
                mod_lines.append(f"Status Resist: {mods.status_resist*100:+.0f}%")
            if mods.max_mana != default_mods.max_mana:
                mod_lines.append(f"Max Mana: {mods.max_mana*100:+.0f}%")
            if mods.max_stamina != default_mods.max_stamina:
                mod_lines.append(f"Max Stamina: {mods.max_stamina*100:+.0f}%")
            if mods.stamina_regen_bonus != default_mods.stamina_regen_bonus:
                mod_lines.append(f"Stamina Regen: +{mods.stamina_regen_bonus}")
            if mods.mana_regen_bonus != default_mods.mana_regen_bonus:
                mod_lines.append(f"Mana Regen: +{mods.mana_regen_bonus}")
            if mods.speed != default_mods.speed:
                mod_lines.append(f"Speed: {mods.speed*100:+.0f}%")

            for line in mod_lines:
                surf = self.font_small.render(line, True, (210, 210, 210))
                self.screen.blit(surf, (80, y))
                y += 20

        # Gold bonus
        if selected_background.starting_gold_bonus > 0:
            gold_surf = self.font_small.render(
                f"Starting Gold Bonus: +{selected_background.starting_gold_bonus}",
                True,
                (230, 210, 120),
            )
            self.screen.blit(gold_surf, (60, y + 10))
            y += 30

        # Background list at the bottom
        list_y = h - 120
        list_panel_width = w - 80
        list_panel_height = 50
        list_panel_x = 40
        
        list_panel = pygame.Surface((list_panel_width, list_panel_height), pygame.SRCALPHA)
        list_panel.fill((20, 25, 35, 200))
        pygame.draw.rect(list_panel, COLOR_BORDER_BRIGHT, (0, 0, list_panel_width, list_panel_height), 1)
        self.screen.blit(list_panel, (list_panel_x, list_y))
        
        x = list_panel_x + 20
        list_text_y = list_y + 15
        for idx, bg in enumerate(self.backgrounds):
            is_sel = (idx == self.selected_background_index)
            label = bg.name
            color = COLOR_TITLE if is_sel else COLOR_TEXT_DIM
            
            if is_sel:
                indicator_width = 4
                indicator_height = 30
                pygame.draw.rect(self.screen, COLOR_TITLE, (x - 8, list_text_y - 5, indicator_width, indicator_height))
            
            surf = self.font_main.render(label, True, color)
            self.screen.blit(surf, (x, list_text_y))
            x += surf.get_width() + 40

        # Controls hint
        hint_text = "←/→ or W/S: change background   Enter/Space: continue   Esc: back   Q: quit"
        hint = self.font_small.render(hint_text, True, (180, 180, 180))
        hint_panel_width = hint.get_width() + 40
        hint_panel_height = 35
        hint_panel_x = w // 2 - hint_panel_width // 2
        hint_panel_y = h - 50
        
        hint_panel = pygame.Surface((hint_panel_width, hint_panel_height), pygame.SRCALPHA)
        hint_panel.fill((0, 0, 0, 150))
        pygame.draw.rect(hint_panel, COLOR_BORDER_BRIGHT, (0, 0, hint_panel_width, hint_panel_height), 1)
        self.screen.blit(hint_panel, (hint_panel_x, hint_panel_y))
        self.screen.blit(hint, (hint_panel_x + 20, hint_panel_y + 8))

    def _draw_stat_distribution_phase(self, selected_class, selected_background, w: int, h: int) -> None:
        """Draw the stat distribution UI."""
        # Main content panel
        panel_width = w - 80
        panel_height = h - 200
        panel_x = 40
        panel_y = 100
        
        panel_surf = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel_surf.fill(COLOR_BG_PANEL)
        pygame.draw.rect(panel_surf, COLOR_BORDER_BRIGHT, (0, 0, panel_width, panel_height), 2)
        self.screen.blit(panel_surf, (panel_x, panel_y))
        
        y = panel_y + 30
        title = self.font_main.render("Distribute Stat Points", True, COLOR_TITLE)
        title_shadow = self.font_main.render("Distribute Stat Points", True, COLOR_SHADOW[:3])
        title_x = w // 2 - title.get_width() // 2
        self.screen.blit(title_shadow, (title_x + SHADOW_OFFSET_X, y + SHADOW_OFFSET_Y))
        self.screen.blit(title, (title_x, y))
        y += 40

        # Class and background info
        class_label = self.font_small.render(f"Class: {selected_class.name}", True, COLOR_SUBTITLE)
        self.screen.blit(class_label, (w // 2 - class_label.get_width() // 2, y))
        y += 24
        bg_label = self.font_small.render(f"Background: {selected_background.name}", True, COLOR_SUBTITLE)
        self.screen.blit(bg_label, (w // 2 - bg_label.get_width() // 2, y))
        y += 40

        # Points available panel
        points_spent = self.stat_distribution.total_points_spent()
        points_remaining = self.stat_points_available - points_spent
        points_color = COLOR_TITLE if points_remaining >= 0 else (255, 150, 150)
        
        points_panel_width = 400
        points_panel_height = 50
        points_panel_x = w // 2 - points_panel_width // 2
        
        points_panel = pygame.Surface((points_panel_width, points_panel_height), pygame.SRCALPHA)
        points_panel.fill((20, 25, 35, 220))
        pygame.draw.rect(points_panel, COLOR_BORDER_BRIGHT, (0, 0, points_panel_width, points_panel_height), 2)
        self.screen.blit(points_panel, (points_panel_x, y))
        
        points_label = self.font_main.render(
            f"Points Available: {points_remaining:.1f} / {self.stat_points_available}",
            True,
            points_color,
        )
        self.screen.blit(points_label, (w // 2 - points_label.get_width() // 2, y + 15))
        y += 60

        # Calculate preview stats (base class stats + background modifiers)
        from systems.stats import StatBlock
        from systems.character_creation import apply_percentage_stat_modifiers
        
        # Create a copy of base stats for preview
        preview_stats = copy.deepcopy(selected_class.base_stats)
        apply_percentage_stat_modifiers(preview_stats, selected_background.stat_modifiers)
        
        # Apply stat distribution to preview (need a temporary copy since apply modifies in-place)
        temp_dist = copy.deepcopy(self.stat_distribution)
        temp_dist.apply_to_stat_block(preview_stats)

        # Stat list
        stat_list_y = y
        stat_x = 200
        for idx, (stat_display_name, attr_name, stat_type) in enumerate(self.stat_names):
            is_selected = (idx == self.selected_stat_index)
            
            current_value = getattr(self.stat_distribution, attr_name)
            
            # Get base + background value for preview
            if attr_name == "hp_points":
                base_val = selected_class.base_stats.max_hp
                preview_val = preview_stats.max_hp
            elif attr_name == "attack_points":
                base_val = selected_class.base_stats.attack
                preview_val = preview_stats.attack
            elif attr_name == "defense_points":
                base_val = selected_class.base_stats.defense
                preview_val = preview_stats.defense
            elif attr_name == "skill_power_points":
                base_val = selected_class.base_stats.skill_power
                preview_val = preview_stats.skill_power
            elif attr_name == "crit_points":
                base_val = selected_class.base_stats.crit_chance
                preview_val = preview_stats.crit_chance
            elif attr_name == "dodge_points":
                base_val = selected_class.base_stats.dodge_chance
                preview_val = preview_stats.dodge_chance
            else:  # speed_points
                base_val = selected_class.base_stats.speed
                preview_val = preview_stats.speed

            # Draw selection background
            if is_selected:
                selection_width = 500
                selection_height = 32
                selection_x = stat_x - 10
                selection_y = stat_list_y - 4
                
                selection_surf = pygame.Surface((selection_width, selection_height), pygame.SRCALPHA)
                selection_surf.fill(COLOR_SELECTED_BG_BRIGHT)
                self.screen.blit(selection_surf, (selection_x, selection_y))
                
                # Left accent
                pygame.draw.rect(self.screen, COLOR_TITLE, (selection_x, selection_y, 4, selection_height))
            
            # Color for selection
            text_color = COLOR_TITLE if is_selected else COLOR_TEXT
            
            # Format display
            if stat_type == float:
                value_str = f"{current_value:.1f}" if current_value != 0 else "0.0"
                if attr_name in ("crit_points", "dodge_points"):
                    preview_str = f"{preview_val:.2f}"
                else:
                    preview_str = f"{preview_val:.2f}"
            else:
                value_str = str(int(current_value)) if current_value != 0 else "0"
                preview_str = str(int(preview_val))
            
            # Stat line: "→ Max HP: +2 (40 -> 42)"
            prefix = "→ " if is_selected else "  "
            if current_value > 0:
                stat_line = f"{prefix}{stat_display_name}: +{value_str} ({base_val:.1f} -> {preview_str})"
            else:
                stat_line = f"{prefix}{stat_display_name}: {value_str} ({base_val:.1f} -> {preview_str})"
            
            surf = self.font_main.render(stat_line, True, text_color)
            self.screen.blit(surf, (stat_x, stat_list_y))
            stat_list_y += 36

        # Controls hint
        hint_text = "↑/↓ or W/S: select stat   ←/→ or A/D: adjust points   Enter/Space: continue   Esc: back   Q: quit"
        hint = self.font_small.render(hint_text, True, (180, 180, 180))
        hint_panel_width = hint.get_width() + 40
        hint_panel_height = 35
        hint_panel_x = w // 2 - hint_panel_width // 2
        hint_panel_y = h - 50
        
        hint_panel = pygame.Surface((hint_panel_width, hint_panel_height), pygame.SRCALPHA)
        hint_panel.fill((0, 0, 0, 150))
        pygame.draw.rect(hint_panel, COLOR_BORDER_BRIGHT, (0, 0, hint_panel_width, hint_panel_height), 1)
        self.screen.blit(hint_panel, (hint_panel_x, hint_panel_y))
        self.screen.blit(hint, (hint_panel_x + 20, hint_panel_y + 8))

    def _draw_name_phase(self, selected_class, w: int, h: int) -> None:
        """Draw the 'enter hero name' UI."""
        # Main content panel
        panel_width = w - 80
        panel_height = h - 200
        panel_x = 40
        panel_y = 140
        
        panel_surf = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel_surf.fill(COLOR_BG_PANEL)
        pygame.draw.rect(panel_surf, COLOR_BORDER_BRIGHT, (0, 0, panel_width, panel_height), 2)
        self.screen.blit(panel_surf, (panel_x, panel_y))
        
        y = panel_y + 30
        title = self.font_main.render("Name Your Hero", True, COLOR_TITLE)
        title_shadow = self.font_main.render("Name Your Hero", True, COLOR_SHADOW[:3])
        title_x = w // 2 - title.get_width() // 2
        self.screen.blit(title_shadow, (title_x + SHADOW_OFFSET_X, y + SHADOW_OFFSET_Y))
        self.screen.blit(title, (title_x, y))
        y += 40

        class_label = self.font_small.render(
            f"Class: {selected_class.name}",
            True,
            COLOR_SUBTITLE,
        )
        self.screen.blit(class_label, (w // 2 - class_label.get_width() // 2, y))
        y += 24

        if self.backgrounds:
            selected_background = self.backgrounds[self.selected_background_index]
            bg_label = self.font_small.render(
                f"Background: {selected_background.name}",
                True,
                COLOR_SUBTITLE,
            )
            self.screen.blit(bg_label, (w // 2 - bg_label.get_width() // 2, y))
        y += 40

        # Name box with better styling
        box_width = 400
        box_height = 50
        box_x = w // 2 - box_width // 2
        box_y = y

        # Box background with shadow
        box_shadow = pygame.Surface((box_width + 4, box_height + 4), pygame.SRCALPHA)
        box_shadow.fill((0, 0, 0, 150))
        self.screen.blit(box_shadow, (box_x - 2, box_y - 2))
        
        pygame.draw.rect(self.screen, (25, 25, 35), (box_x, box_y, box_width, box_height))
        pygame.draw.rect(self.screen, COLOR_BORDER_BRIGHT, (box_x, box_y, box_width, box_height), 2)

        name_display = self.name_buffer
        if self.cursor_visible and len(self.name_buffer) < self.max_name_length:
            name_display += "_"

        name_surf = self.font_main.render(name_display, True, (240, 240, 240))
        self.screen.blit(
            name_surf,
            (box_x + 12, box_y + box_height // 2 - name_surf.get_height() // 2),
        )

        # Hint text panel
        hint1_text = "Type to enter your name (A–Z, numbers, etc.) – R: random name – Enter to confirm."
        hint2_text = "Esc: back to traits   Q: quit"
        hint1 = self.font_small.render(hint1_text, True, (190, 190, 190))
        hint2 = self.font_small.render(hint2_text, True, (170, 170, 170))
        
        hint_panel_width = max(hint1.get_width(), hint2.get_width()) + 40
        hint_panel_height = 70
        hint_panel_x = w // 2 - hint_panel_width // 2
        hint_panel_y = box_y + box_height + 20
        
        hint_panel = pygame.Surface((hint_panel_width, hint_panel_height), pygame.SRCALPHA)
        hint_panel.fill((0, 0, 0, 150))
        pygame.draw.rect(hint_panel, COLOR_BORDER_BRIGHT, (0, 0, hint_panel_width, hint_panel_height), 1)
        self.screen.blit(hint_panel, (hint_panel_x, hint_panel_y))
        
        self.screen.blit(hint1, (hint_panel_x + 20, hint_panel_y + 10))
        self.screen.blit(hint2, (hint_panel_x + 20, hint_panel_y + 35))

    # ------------------------------------------------------------------
    # Text wrapping helper
    # ------------------------------------------------------------------

    def _wrap_text(self, text: str, font: pygame.font.Font, max_width: int) -> list[str]:
        words = text.split()
        lines: list[str] = []
        current = ""

        for word in words:
            test = word if not current else current + " " + word
            if font.size(test)[0] <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word

        if current:
            lines.append(current)

        return lines
