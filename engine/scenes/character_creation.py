import pygame
import traceback
import sys
import copy
from typing import List, Optional

from settings import COLOR_BG, FPS
from systems.classes import all_classes, get_class
from systems.character_creation.stat_distribution import StatDistribution
from systems.character_creation.traits import all_traits, get_trait, traits_by_category

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

    def run(self) -> tuple[str, str, StatDistribution, List[str], str] | None:
        """
        Main loop for the character creation scene.
        Returns (class_id, background_id, stat_distribution, traits, hero_name) or None if the player quits.
        """
        clock = pygame.time.Clock()

        while True:
            dt = clock.tick(FPS) / 1000.0

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
        self.screen.fill(COLOR_BG)
        w, h = self.screen.get_size()

        title = self.font_title.render("Character Creation", True, (255, 255, 210))
        self.screen.blit(title, (w // 2 - title.get_width() // 2, 40))

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
        """Draw the 'choose class' UI."""
        y = 120
        name_surf = self.font_main.render(selected.name, True, (255, 255, 230))
        self.screen.blit(name_surf, (w // 2 - name_surf.get_width() // 2, y))
        y += 32

        # Description (wrapped)
        desc_lines = self._wrap_text(selected.description, self.font_small, w - 80)
        for line in desc_lines:
            surf = self.font_small.render(line, True, (220, 220, 220))
            self.screen.blit(surf, (40, y))
            y += 22

        y += 10

        # Stats summary from base_stats
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
            surf = self.font_small.render(line, True, (210, 210, 210))
            self.screen.blit(surf, (60, y))
            y += 20

        y += 10

        # Starting perks / skills / items
        perks_label = self.font_small.render("Starting Perks:", True, (220, 220, 180))
        self.screen.blit(perks_label, (360, 200))
        py = 224
        for pid in selected.starting_perks:
            surf = self.font_small.render(f"- {pid}", True, (210, 210, 210))
            self.screen.blit(surf, (380, py))
            py += 18

        skills_label = self.font_small.render("Starting Skills:", True, (220, 220, 180))
        self.screen.blit(skills_label, (360, py + 10))
        py += 34
        for sid in selected.starting_skills:
            surf = self.font_small.render(f"- {sid}", True, (210, 210, 210))
            self.screen.blit(surf, (380, py))
            py += 18

        items_label = self.font_small.render("Starting Items:", True, (220, 220, 180))
        self.screen.blit(items_label, (360, py + 10))
        py += 34
        for iid in selected.starting_items:
            surf = self.font_small.render(f"- {iid}", True, (210, 210, 210))
            self.screen.blit(surf, (380, py))
            py += 18

        gold_surf = self.font_small.render(
            f"Starting Gold: {selected.starting_gold}",
            True,
            (230, 210, 120),
        )
        self.screen.blit(gold_surf, (360, py + 10))

        # Class list at the bottom
        list_y = h - 120
        x = 40
        for idx, c in enumerate(self.classes):
            is_sel = (idx == self.selected_class_index)
            label = f"[{c.name}]" if is_sel else c.name
            color = (255, 255, 210) if is_sel else (200, 200, 200)
            surf = self.font_main.render(label, True, color)
            self.screen.blit(surf, (x, list_y))
            x += surf.get_width() + 40

        # Controls hint
        hint = self.font_small.render(
            "←/→ or W/S: change class   Enter/Space: continue   Esc/Q: quit",
            True,
            (180, 180, 180),
        )
        self.screen.blit(hint, (w // 2 - hint.get_width() // 2, h - 40))

    def _draw_background_phase(self, selected_class, selected_background, w: int, h: int) -> None:
        """Draw the 'choose background' UI."""
        if not selected_background:
            msg = self.font_main.render("No backgrounds available.", True, (255, 100, 100))
            self.screen.blit(msg, (w // 2 - msg.get_width() // 2, h // 2))
            return

        y = 100
        title = self.font_main.render("Choose Your Background", True, (255, 255, 230))
        self.screen.blit(title, (w // 2 - title.get_width() // 2, y))
        y += 32

        class_label = self.font_small.render(
            f"Class: {selected_class.name}",
            True,
            (220, 220, 200),
        )
        self.screen.blit(class_label, (w // 2 - class_label.get_width() // 2, y))
        y += 40

        # Background name
        name_surf = self.font_main.render(selected_background.name, True, (255, 255, 230))
        self.screen.blit(name_surf, (w // 2 - name_surf.get_width() // 2, y))
        y += 32

        # Description (wrapped)
        desc_lines = self._wrap_text(selected_background.description, self.font_small, w - 80)
        for line in desc_lines:
            surf = self.font_small.render(line, True, (220, 220, 220))
            self.screen.blit(surf, (40, y))
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
        x = 40
        for idx, bg in enumerate(self.backgrounds):
            is_sel = (idx == self.selected_background_index)
            label = f"[{bg.name}]" if is_sel else bg.name
            color = (255, 255, 210) if is_sel else (200, 200, 200)
            surf = self.font_main.render(label, True, color)
            self.screen.blit(surf, (x, list_y))
            x += surf.get_width() + 40

        # Controls hint
        hint = self.font_small.render(
            "←/→ or W/S: change background   Enter/Space: continue   Esc: back   Q: quit",
            True,
            (180, 180, 180),
        )
        self.screen.blit(hint, (w // 2 - hint.get_width() // 2, h - 40))

    def _draw_stat_distribution_phase(self, selected_class, selected_background, w: int, h: int) -> None:
        """Draw the stat distribution UI."""
        y = 100
        title = self.font_main.render("Distribute Stat Points", True, (255, 255, 230))
        self.screen.blit(title, (w // 2 - title.get_width() // 2, y))
        y += 32

        # Class and background info
        class_label = self.font_small.render(f"Class: {selected_class.name}", True, (220, 220, 200))
        self.screen.blit(class_label, (w // 2 - class_label.get_width() // 2, y))
        y += 24
        bg_label = self.font_small.render(f"Background: {selected_background.name}", True, (220, 220, 200))
        self.screen.blit(bg_label, (w // 2 - bg_label.get_width() // 2, y))
        y += 40

        # Points available
        points_spent = self.stat_distribution.total_points_spent()
        points_remaining = self.stat_points_available - points_spent
        points_color = (255, 255, 210) if points_remaining >= 0 else (255, 150, 150)
        points_label = self.font_main.render(
            f"Points Available: {points_remaining:.1f} / {self.stat_points_available}",
            True,
            points_color,
        )
        self.screen.blit(points_label, (w // 2 - points_label.get_width() // 2, y))
        y += 40

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

            # Color for selection
            text_color = (255, 255, 210) if is_selected else (200, 200, 200)
            
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
            stat_list_y += 32

        # Controls hint
        hint = self.font_small.render(
            "↑/↓ or W/S: select stat   ←/→ or A/D: adjust points   Enter/Space: continue   Esc: back   Q: quit",
            True,
            (180, 180, 180),
        )
        self.screen.blit(hint, (w // 2 - hint.get_width() // 2, h - 40))

    def _draw_name_phase(self, selected_class, w: int, h: int) -> None:
        """Draw the 'enter hero name' UI."""
        y = 140
        title = self.font_main.render("Name Your Hero", True, (255, 255, 230))
        self.screen.blit(title, (w // 2 - title.get_width() // 2, y))
        y += 32

        class_label = self.font_small.render(
            f"Class: {selected_class.name}",
            True,
            (220, 220, 200),
        )
        self.screen.blit(class_label, (w // 2 - class_label.get_width() // 2, y))
        y += 20

        if self.backgrounds:
            selected_background = self.backgrounds[self.selected_background_index]
            bg_label = self.font_small.render(
                f"Background: {selected_background.name}",
                True,
                (220, 220, 200),
            )
            self.screen.blit(bg_label, (w // 2 - bg_label.get_width() // 2, y))
        y += 40

        # Name box
        box_width = 360
        box_height = 44
        box_x = w // 2 - box_width // 2
        box_y = y

        pygame.draw.rect(self.screen, (20, 20, 20), (box_x, box_y, box_width, box_height))
        pygame.draw.rect(self.screen, (200, 200, 200), (box_x, box_y, box_width, box_height), 2)

        name_display = self.name_buffer
        if self.cursor_visible and len(self.name_buffer) < self.max_name_length:
            name_display += "_"

        name_surf = self.font_main.render(name_display, True, (240, 240, 240))
        self.screen.blit(
            name_surf,
            (box_x + 12, box_y + box_height // 2 - name_surf.get_height() // 2),
        )

        # Hint text
        hint1 = self.font_small.render(
            "Type to enter your name (A–Z, numbers, etc.) – Enter to confirm.",
            True,
            (190, 190, 190),
        )
        hint2 = self.font_small.render(
            "Esc: back to traits   Q: quit",
            True,
            (170, 170, 170),
        )
        self.screen.blit(hint1, (w // 2 - hint1.get_width() // 2, box_y + box_height + 16))
        self.screen.blit(hint2, (w // 2 - hint2.get_width() // 2, box_y + box_height + 40))

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
