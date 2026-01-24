import math
import random
import pygame

from settings import COLOR_BG, FPS
from systems.classes import all_classes
from typing import List, Dict


class CharacterCreationScene:
    """
    Simple character creation / class selection + name entry.

    Phase 1: choose a class (Warrior / Rogue / Mage).
    Phase 2: enter a name for your hero.

    Later we can expand this with:
    - backgrounds / traits
    - starting perk/skill previews
    - custom starting stats
    """
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.font_title = pygame.font.SysFont("consolas", 28)
        self.font_main = pygame.font.SysFont("consolas", 22)
        self.font_small = pygame.font.SysFont("consolas", 18)

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

        elif event.key in (pygame.K_LEFT, pygame.K_a, pygame.K_UP, pygame.K_w):
            if self.classes:
                self.selected_index = (self.selected_index - 1) % len(self.classes)

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

        title = self.font_title.render("Character Creation", True, (255, 255, 210))
        self.screen.blit(title, (w // 2 - title.get_width() // 2, 40))

        if not self.classes:
            msg = self.font_main.render("No classes defined.", True, (255, 100, 100))
            self.screen.blit(msg, (w // 2 - msg.get_width() // 2, h // 2))
            return

        selected = self.classes[self.selected_index]

        # Class list at the bottom (always visible)
        list_y = h - 120
        x = 40
        for idx, c in enumerate(self.classes):
            is_sel = (idx == self.selected_index)
            label = f"[{c.name}]" if is_sel else c.name
            color = (255, 255, 210) if is_sel else (200, 200, 200)
            surf = self.font_main.render(label, True, color)
            self.screen.blit(surf, (x, list_y))
            x += surf.get_width() + 40

        if self.phase == "class":
            self._draw_class_phase(selected, w, h)
        else:
            self._draw_name_phase(selected, w, h)

    def _draw_class_phase(self, selected, w: int, h: int) -> None:
        """
        Draw the 'choose class' UI.
        """
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

        # Controls hint
        hint = self.font_small.render(
            "←/→ or W/S: change class   Enter/Space: continue   Esc/Q: quit",
            True,
            (180, 180, 180),
        )
        self.screen.blit(hint, (w // 2 - hint.get_width() // 2, h - 40))

    def _draw_name_phase(self, selected, w: int, h: int) -> None:
        """
        Draw the 'enter hero name' UI.
        """
        y = 140
        title = self.font_main.render("Name Your Hero", True, (255, 255, 230))
        self.screen.blit(title, (w // 2 - title.get_width() // 2, y))
        y += 32

        class_label = self.font_small.render(
            f"Class: {selected.name}",
            True,
            (220, 220, 200),
        )
        self.screen.blit(class_label, (w // 2 - class_label.get_width() // 2, y))
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
            "Esc: back to class selection   Q: quit",
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
