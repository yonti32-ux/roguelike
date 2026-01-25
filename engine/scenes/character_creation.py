import math
import random
import pygame

from settings import COLOR_BG, FPS
from systems.classes import all_classes
from typing import List, Dict, Tuple


class CharacterCreationScene:
    """
    Enhanced character creation / class selection + name entry.

    Phase 1: choose a class (Warrior / Rogue / Mage) with improved card-based UI.
    Phase 2: enter a name for your hero.

    Features:
    - Card-based class selection with visual hierarchy
    - Better organized information display
    - Smooth animations and visual feedback
    """
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.font_title = pygame.font.SysFont("consolas", 36)
        self.font_class_name = pygame.font.SysFont("consolas", 28)
        self.font_main = pygame.font.SysFont("consolas", 20)
        self.font_small = pygame.font.SysFont("consolas", 16)
        self.font_tiny = pygame.font.SysFont("consolas", 14)

        self.classes = all_classes()
        self.selected_index = 0

        # Two-phase flow: "class" selection -> "name" input
        self.phase: str = "class"
        self.name_buffer: str = ""
        self.max_name_length: int = 16

        # Simple blink for the name cursor
        self.cursor_visible: bool = True
        self.cursor_timer: float = 0.0
        
        # Background particles for visual effect
        self.particles: List[Dict] = []
        self.animation_timer: float = 0.0
        self._init_particles()
        
        # Selection animation
        self.selection_pulse: float = 0.0
    
    def _init_particles(self) -> None:
        """Initialize background particles."""
        w, h = self.screen.get_size()
        # Create 40-50 particles
        for _ in range(random.randint(40, 50)):
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

    def run(self) -> tuple[str, str] | None:
        """
        Main loop for the character creation scene.
        Returns (class_id, hero_name) or None if the player quits.
        """
        clock = pygame.time.Clock()

        while True:
            dt = clock.tick(FPS) / 1000.0
            self.animation_timer += dt
            self.selection_pulse += dt * 2.0  # Pulse animation speed

            # Cursor blink for name input
            self.cursor_timer += dt
            if self.cursor_timer >= 0.5:
                self.cursor_timer = 0.0
                self.cursor_visible = not self.cursor_visible
            
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
                    # Global quit shortcut
                    if event.key == pygame.K_q:
                        return None

                    if self.phase == "class":
                        handled = self._handle_class_keydown(event)
                        if isinstance(handled, tuple):
                            # (class_id, hero_name) returned (from name phase)
                            return handled
                    else:  # phase == "name"
                        handled = self._handle_name_keydown(event)
                        if isinstance(handled, tuple):
                            # (class_id, hero_name)
                            return handled

            self.draw()
            pygame.display.flip()

    # ------------------------------------------------------------------
    # Input handling
    # ------------------------------------------------------------------

    def _handle_class_keydown(self, event: pygame.event.Event):
        """
        Handle key presses while choosing a class.
        Esc here quits the game; Enter moves to name entry.
        """
        if event.key == pygame.K_ESCAPE:
            return None  # signal quit to caller

        if event.key in (pygame.K_RIGHT, pygame.K_d, pygame.K_DOWN, pygame.K_s):
            if self.classes:
                self.selected_index = (self.selected_index + 1) % len(self.classes)
                self.selection_pulse = 0.0  # Reset pulse on selection change

        elif event.key in (pygame.K_LEFT, pygame.K_a, pygame.K_UP, pygame.K_w):
            if self.classes:
                self.selected_index = (self.selected_index - 1) % len(self.classes)
                self.selection_pulse = 0.0  # Reset pulse on selection change

        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            # Move to name input, pre-fill with class name as a default
            if not self.classes:
                return None

            selected = self.classes[self.selected_index]
            self.phase = "name"
            self.name_buffer = selected.name
            return  # stay in scene

        return  # no final result yet

    def _handle_name_keydown(self, event: pygame.event.Event):
        """
        Handle key presses while entering a name.
        Esc returns to class selection. Enter confirms.
        """
        # Esc: go back to class selection, keep current class selection
        if event.key == pygame.K_ESCAPE:
            self.phase = "class"
            # don't clear name_buffer so the player can tweak if they come back
            return

        # Confirm name
        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            if not self.classes:
                return None

            selected = self.classes[self.selected_index]
            final_name = self.name_buffer.strip() or selected.name
            return (selected.id, final_name)

        # Delete last character
        if event.key == pygame.K_BACKSPACE:
            if self.name_buffer:
                self.name_buffer = self.name_buffer[:-1]
            return

        # Add typed characters (basic, printable only)
        if event.unicode:
            ch = event.unicode
            if ch.isprintable() and not ch.isspace():
                if len(self.name_buffer) < self.max_name_length:
                    self.name_buffer += ch

        return

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw(self) -> None:
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

        # Title with subtle glow effect
        title_text = "Character Creation"
        title_surf = self.font_title.render(title_text, True, (255, 255, 220))
        title_x = w // 2 - title_surf.get_width() // 2
        title_y = 30
        
        # Subtle shadow for title
        shadow_surf = self.font_title.render(title_text, True, (0, 0, 0))
        self.screen.blit(shadow_surf, (title_x + 2, title_y + 2))
        self.screen.blit(title_surf, (title_x, title_y))

        if not self.classes:
            msg = self.font_main.render("No classes defined.", True, (255, 100, 100))
            self.screen.blit(msg, (w // 2 - msg.get_width() // 2, h // 2))
            return

        if self.phase == "class":
            self._draw_class_phase(w, h)
        else:
            selected = self.classes[self.selected_index]
            self._draw_name_phase(selected, w, h)

    def _draw_class_phase(self, w: int, h: int) -> None:
        """
        Draw the improved 'choose class' UI with card-based layout.
        """
        num_classes = len(self.classes)
        if num_classes == 0:
            return
        
        # Calculate card dimensions and positions - larger cards to prevent overlap
        card_width = 420
        card_height = 600
        card_spacing = 15
        total_width = (num_classes * card_width) + ((num_classes - 1) * card_spacing)
        start_x = (w - total_width) // 2
        card_y = 90
        
        # Draw class cards
        for idx, class_def in enumerate(self.classes):
            is_selected = (idx == self.selected_index)
            card_x = start_x + idx * (card_width + card_spacing)
            self._draw_class_card(class_def, card_x, card_y, card_width, card_height, is_selected)
        
        # Controls hint at bottom
        hint = self.font_small.render(
            "←/→ or A/D: change class   Enter/Space: continue   Esc/Q: quit",
            True,
            (180, 180, 180),
        )
        self.screen.blit(hint, (w // 2 - hint.get_width() // 2, h - 30))
    
    def _draw_class_card(self, class_def, x: int, y: int, width: int, height: int, is_selected: bool) -> None:
        """
        Draw a single class card with all its information.
        """
        # Pulse effect for selected card
        pulse_alpha = int(30 + 20 * abs(math.sin(self.selection_pulse))) if is_selected else 0
        
        # Card background with border
        border_color = (255, 220, 100) if is_selected else (100, 100, 120)
        border_width = 3 if is_selected else 2
        
        # Draw card shadow
        shadow_offset = 4
        shadow_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        shadow_surf.fill((0, 0, 0, 100))
        self.screen.blit(shadow_surf, (x + shadow_offset, y + shadow_offset))
        
        # Draw card background with subtle gradient effect
        bg_color = (40, 40, 50) if is_selected else (28, 28, 38)
        pygame.draw.rect(self.screen, bg_color, (x, y, width, height))
        
        # Subtle inner highlight at top
        highlight_surf = pygame.Surface((width, 60), pygame.SRCALPHA)
        highlight_color = (255, 255, 255, 8) if is_selected else (255, 255, 255, 4)
        highlight_surf.fill(highlight_color)
        self.screen.blit(highlight_surf, (x, y))
        
        pygame.draw.rect(self.screen, border_color, (x, y, width, height), border_width)
        
        # Draw glow effect for selected card
        if is_selected and pulse_alpha > 0:
            glow_surf = pygame.Surface((width + 8, height + 8), pygame.SRCALPHA)
            glow_color = (*border_color, pulse_alpha)
            pygame.draw.rect(glow_surf, glow_color, (0, 0, width + 8, height + 8), 4)
            self.screen.blit(glow_surf, (x - 4, y - 4))
        
        # Card content
        content_x = x + 18
        content_y = y + 18
        current_y = content_y
        content_width = width - 36  # Account for padding on both sides
        
        # Class name (larger, highlighted) with subtle shadow
        name_color = (255, 240, 150) if is_selected else (220, 220, 220)
        name_text = class_def.name
        name_shadow = self.font_class_name.render(name_text, True, (0, 0, 0))
        name_surf = self.font_class_name.render(name_text, True, name_color)
        self.screen.blit(name_shadow, (content_x + 1, current_y + 1))
        self.screen.blit(name_surf, (content_x, current_y))
        current_y += 36
        
        # Description
        desc_lines = self._wrap_text(class_def.description, self.font_small, content_width)
        for line in desc_lines:
            desc_surf = self.font_small.render(line, True, (200, 200, 200))
            self.screen.blit(desc_surf, (content_x, current_y))
            current_y += 18
        current_y += 12
        
        # Divider line with subtle gradient
        divider_y = current_y
        pygame.draw.line(self.screen, (60, 60, 80), 
                        (content_x, divider_y), (x + width - 18, divider_y), 1)
        pygame.draw.line(self.screen, (100, 100, 120), 
                        (content_x, divider_y + 1), (x + width - 18, divider_y + 1), 1)
        current_y += 18
        
        # Stats section with two-column layout to save space
        stats_label_text = "Base Stats"
        stats_label_shadow = self.font_main.render(stats_label_text, True, (0, 0, 0))
        stats_label = self.font_main.render(stats_label_text, True, (220, 220, 180))
        self.screen.blit(stats_label_shadow, (content_x + 1, current_y + 1))
        self.screen.blit(stats_label, (content_x, current_y))
        current_y += 26
        
        bs = class_def.base_stats
        stats_data = [
            ("Max HP", f"{bs.max_hp}", (255, 200, 200)),
            ("Attack", f"{bs.attack}", (255, 150, 150)),
            ("Defense", f"{bs.defense}", (200, 200, 255)),
            ("Speed", f"{bs.speed:.1f}x", (200, 255, 200)),
            ("Skill Power", f"{bs.skill_power:.1f}x", (255, 220, 150)),
            ("Crit Chance", f"{int(bs.crit_chance * 100)}%", (255, 255, 150)),
            ("Dodge", f"{int(bs.dodge_chance * 100)}%", (150, 255, 255)),
            ("Status Resist", f"{int(bs.status_resist * 100)}%", (255, 200, 255)),
        ]
        
        # Add mana/stamina if they exist
        if hasattr(bs, 'max_mana') and bs.max_mana > 0:
            stats_data.append(("Max Mana", f"{bs.max_mana}", (150, 200, 255)))
        if hasattr(bs, 'max_stamina') and bs.max_stamina > 0:
            stats_data.append(("Max Stamina", f"{bs.max_stamina}", (255, 200, 150)))
        
        # Two-column layout for stats
        stats_y_start = current_y
        col1_x = content_x + 8
        col2_x = content_x + (content_width // 2) + 8
        col_height = 16
        
        for idx, (label, value, color) in enumerate(stats_data):
            col = idx % 2
            row = idx // 2
            stat_x = col1_x if col == 0 else col2_x
            stat_y = stats_y_start + (row * col_height)
            
            stat_text = f"{label}: {value}"
            stat_surf = self.font_tiny.render(stat_text, True, color)
            self.screen.blit(stat_surf, (stat_x, stat_y))
        
        # Move current_y to after stats
        stats_rows = (len(stats_data) + 1) // 2
        current_y = stats_y_start + (stats_rows * col_height) + 12
        
        # Divider line with subtle gradient
        divider_y = current_y
        pygame.draw.line(self.screen, (60, 60, 80), 
                        (content_x, divider_y), (x + width - 18, divider_y), 1)
        pygame.draw.line(self.screen, (100, 100, 120), 
                        (content_x, divider_y + 1), (x + width - 18, divider_y + 1), 1)
        current_y += 18
        
        # Starting equipment section - more compact
        section_y_start = current_y
        
        # Starting Perks
        if class_def.starting_perks:
            perks_label_text = "Starting Perks"
            perks_label_shadow = self.font_main.render(perks_label_text, True, (0, 0, 0))
            perks_label = self.font_main.render(perks_label_text, True, (180, 240, 180))
            self.screen.blit(perks_label_shadow, (content_x + 1, current_y + 1))
            self.screen.blit(perks_label, (content_x, current_y))
            current_y += 22
            for pid in class_def.starting_perks:
                perk_surf = self.font_tiny.render(f"• {pid}", True, (160, 220, 160))
                self.screen.blit(perk_surf, (content_x + 8, current_y))
                current_y += 15
        
        # Starting Skills
        if class_def.starting_skills:
            if current_y > section_y_start:
                current_y += 6
            skills_label_text = "Starting Skills"
            skills_label_shadow = self.font_main.render(skills_label_text, True, (0, 0, 0))
            skills_label = self.font_main.render(skills_label_text, True, (180, 180, 240))
            self.screen.blit(skills_label_shadow, (content_x + 1, current_y + 1))
            self.screen.blit(skills_label, (content_x, current_y))
            current_y += 22
            for sid in class_def.starting_skills:
                skill_surf = self.font_tiny.render(f"• {sid}", True, (160, 160, 220))
                self.screen.blit(skill_surf, (content_x + 8, current_y))
                current_y += 15
        
        # Starting Items
        if class_def.starting_items:
            if current_y > section_y_start:
                current_y += 6
            items_label_text = "Starting Items"
            items_label_shadow = self.font_main.render(items_label_text, True, (0, 0, 0))
            items_label = self.font_main.render(items_label_text, True, (240, 220, 180))
            self.screen.blit(items_label_shadow, (content_x + 1, current_y + 1))
            self.screen.blit(items_label, (content_x, current_y))
            current_y += 22
            for iid in class_def.starting_items:
                item_surf = self.font_tiny.render(f"• {iid}", True, (220, 200, 160))
                self.screen.blit(item_surf, (content_x + 8, current_y))
                current_y += 15
        
        # Starting Gold at bottom with better positioning and visual emphasis
        gold_y = y + height - 32
        gold_text = f"Starting Gold: {class_def.starting_gold}"
        
        # Gold text with shadow and highlight
        gold_shadow = self.font_small.render(gold_text, True, (0, 0, 0))
        gold_surf = self.font_small.render(gold_text, True, (255, 220, 100))
        
        # Draw a subtle background for gold
        gold_bg_width = gold_surf.get_width() + 12
        gold_bg_height = gold_surf.get_height() + 4
        gold_bg_x = content_x - 6
        gold_bg_y = gold_y - 2
        gold_bg_surf = pygame.Surface((gold_bg_width, gold_bg_height), pygame.SRCALPHA)
        gold_bg_surf.fill((255, 220, 100, 20))
        self.screen.blit(gold_bg_surf, (gold_bg_x, gold_bg_y))
        
        self.screen.blit(gold_shadow, (content_x + 1, gold_y + 1))
        self.screen.blit(gold_surf, (content_x, gold_y))

    def _draw_name_phase(self, selected, w: int, h: int) -> None:
        """
        Draw the enhanced 'enter hero name' UI with better visuals.
        """
        # Title with shadow and glow
        title_text = "Name Your Hero"
        title_shadow = self.font_title.render(title_text, True, (0, 0, 0))
        title_surf = self.font_title.render(title_text, True, (255, 255, 220))
        title_x = w // 2 - title_surf.get_width() // 2
        title_y = 80
        
        # Draw title with shadow
        self.screen.blit(title_shadow, (title_x + 2, title_y + 2))
        self.screen.blit(title_surf, (title_x, title_y))
        
        y = title_y + 60

        # Class preview card - show selected class info
        card_width = 500
        card_height = 200
        card_x = w // 2 - card_width // 2
        card_y = y
        
        # Draw class preview card background
        card_bg = pygame.Surface((card_width, card_height), pygame.SRCALPHA)
        card_bg.fill((30, 30, 40, 200))
        self.screen.blit(card_bg, (card_x, card_y))
        pygame.draw.rect(self.screen, (100, 100, 120), (card_x, card_y, card_width, card_height), 2)
        
        # Class name and description in preview
        preview_x = card_x + 20
        preview_y = card_y + 20
        
        class_name_text = f"Class: {selected.name}"
        class_name_shadow = self.font_class_name.render(class_name_text, True, (0, 0, 0))
        class_name_surf = self.font_class_name.render(class_name_text, True, (255, 240, 150))
        self.screen.blit(class_name_shadow, (preview_x + 1, preview_y + 1))
        self.screen.blit(class_name_surf, (preview_x, preview_y))
        preview_y += 35
        
        # Class description
        desc_lines = self._wrap_text(selected.description, self.font_small, card_width - 40)
        for line in desc_lines:
            desc_surf = self.font_small.render(line, True, (200, 200, 200))
            self.screen.blit(desc_surf, (preview_x, preview_y))
            preview_y += 20
        
        # Quick stats preview
        preview_y += 10
        bs = selected.base_stats
        quick_stats = [
            f"HP: {bs.max_hp}",
            f"ATK: {bs.attack}",
            f"DEF: {bs.defense}",
            f"SPD: {bs.speed:.1f}x",
        ]
        stats_text = "  |  ".join(quick_stats)
        stats_surf = self.font_tiny.render(stats_text, True, (180, 180, 200))
        self.screen.blit(stats_surf, (preview_x, preview_y))
        
        y = card_y + card_height + 40

        # Enhanced name input box
        box_width = 500
        box_height = 60
        box_x = w // 2 - box_width // 2
        box_y = y
        
        # Box shadow
        shadow_offset = 4
        shadow_surf = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
        shadow_surf.fill((0, 0, 0, 150))
        self.screen.blit(shadow_surf, (box_x + shadow_offset, box_y + shadow_offset))
        
        # Box background with gradient effect
        box_bg = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
        # Top highlight
        highlight_surf = pygame.Surface((box_width, 20), pygame.SRCALPHA)
        highlight_surf.fill((255, 255, 255, 15))
        box_bg.blit(highlight_surf, (0, 0))
        # Main background
        box_bg.fill((25, 25, 35, 255), (0, 20, box_width, box_height - 20))
        self.screen.blit(box_bg, (box_x, box_y))
        
        # Animated border glow
        border_glow = int(30 + 20 * abs(math.sin(self.animation_timer * 3)))
        border_color = (255, 220, 100, border_glow)
        border_surf = pygame.Surface((box_width + 4, box_height + 4), pygame.SRCALPHA)
        pygame.draw.rect(border_surf, border_color, (0, 0, box_width + 4, box_height + 4), 3)
        self.screen.blit(border_surf, (box_x - 2, box_y - 2))
        
        # Main border
        pygame.draw.rect(self.screen, (200, 200, 200), (box_x, box_y, box_width, box_height), 2)
        
        # Name text with better styling
        name_display = self.name_buffer if self.name_buffer else ""
        name_color = (255, 255, 255) if name_display else (150, 150, 150)
        placeholder = "Enter your hero's name..." if not name_display else ""
        
        if name_display:
            name_surf = self.font_main.render(name_display, True, name_color)
        else:
            name_surf = self.font_main.render(placeholder, True, (100, 100, 100))
        
        # Cursor
        cursor_x = box_x + 20 + name_surf.get_width()
        if self.cursor_visible and len(self.name_buffer) < self.max_name_length:
            cursor_surf = self.font_main.render("|", True, (255, 255, 255))
            self.screen.blit(cursor_surf, (cursor_x, box_y + box_height // 2 - cursor_surf.get_height() // 2))
        
        # Draw name text
        self.screen.blit(
            name_surf,
            (box_x + 20, box_y + box_height // 2 - name_surf.get_height() // 2),
        )
        
        # Character count indicator
        char_count = len(self.name_buffer)
        char_count_text = f"{char_count}/{self.max_name_length}"
        char_count_color = (200, 200, 200) if char_count < self.max_name_length else (255, 200, 100)
        char_count_surf = self.font_tiny.render(char_count_text, True, char_count_color)
        char_count_x = box_x + box_width - char_count_surf.get_width() - 15
        char_count_y = box_y + box_height - char_count_surf.get_height() - 8
        self.screen.blit(char_count_surf, (char_count_x, char_count_y))
        
        y = box_y + box_height + 30

        # Enhanced hint text with better styling
        hint_y = y
        hint1_text = "Type to enter your name (A–Z, numbers, etc.)"
        hint1_surf = self.font_small.render(hint1_text, True, (200, 200, 200))
        self.screen.blit(hint1_surf, (w // 2 - hint1_surf.get_width() // 2, hint_y))
        
        hint_y += 25
        hint2_text = "Enter: confirm   Esc: back to class selection   Q: quit"
        hint2_surf = self.font_small.render(hint2_text, True, (170, 170, 170))
        self.screen.blit(hint2_surf, (w // 2 - hint2_surf.get_width() // 2, hint_y))
        
        # Decorative elements - subtle lines
        line_y = hint_y + 35
        line_length = 200
        line_x1 = w // 2 - line_length // 2
        line_x2 = w // 2 + line_length // 2
        pygame.draw.line(self.screen, (80, 80, 100), (line_x1, line_y), (line_x2, line_y), 1)

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
