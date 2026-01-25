"""
Full-screen blocking scene for perk selection on level-up.

This scene manages the queue of entities (hero + companions) that need
to select perks, displays choices, handles input, and applies selections.
"""

from dataclasses import dataclass
from typing import Optional, List, TYPE_CHECKING

import pygame

from settings import COLOR_BG, FPS
from systems import perks as perk_system
from systems.party import get_companion, recalc_companion_stats_for_level

if TYPE_CHECKING:
    from ..core.game import Game


@dataclass
class PerkChoiceEntry:
    """Entry in the perk selection queue."""
    owner: str  # "hero" or "companion"
    companion_index: Optional[int] = None  # Only used if owner == "companion"


class PerkSelectionScene:
    """
    Full-screen blocking scene for selecting perks on level-up.
    
    Manages:
    - Queue of entities (hero + companions) needing perk selection
    - Current perk choices display
    - Input handling (selection, navigation, cancel)
    - Complete rendering (full-screen scene)
    """

    def __init__(self, game: "Game") -> None:
        self.game = game
        self.screen = game.screen
        self.font = game.ui_font
        self.font_title = pygame.font.SysFont("consolas", 28)
        self.font_small = pygame.font.SysFont("consolas", 16)
        
        # Queue of entities needing perk selection
        self.queue: List[PerkChoiceEntry] = []
        
        # Current selection state
        self.current_entry: Optional[PerkChoiceEntry] = None
        self.current_choices: List[perk_system.Perk] = []
        self.selected_index: int = 0
        self.current_owner_name: str = ""
        
        # Visual state
        self.cursor_visible: bool = True
        self.cursor_timer: float = 0.0

    def enqueue(self, owner: str, companion_index: Optional[int] = None) -> None:
        """
        Add an entity to the perk selection queue.
        
        owner: "hero" or "companion"
        companion_index: Index in game.party (only used if owner == "companion")
        """
        self.queue.append(PerkChoiceEntry(owner=owner, companion_index=companion_index))

    def run(self) -> None:
        """
        Main blocking loop for perk selection.
        
        Processes the queue, displays choices, handles input until all
        selections are made (or queue is cancelled/cleared).
        """
        clock = pygame.time.Clock()
        
        # Start processing the queue
        self._start_next_selection()
        
        while self.current_entry is not None or self.queue:
            dt = clock.tick(FPS) / 1000.0
            
            # Cursor blink for visual feedback
            self.cursor_timer += dt
            if self.cursor_timer >= 0.5:
                self.cursor_timer = 0.0
                self.cursor_visible = not self.cursor_visible
            
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    # Clear queue and exit
                    self.queue.clear()
                    self.current_entry = None
                    return
                
                if event.type == pygame.KEYDOWN:
                    handled = self._handle_keydown(event)
                    if handled == "exit":
                        # Cancelled - clear queue and return
                        self.queue.clear()
                        self.current_entry = None
                        return
            
            # Draw
            self.draw()
            pygame.display.flip()

    def _start_next_selection(self) -> None:
        """Process the next entry in the queue and generate perk choices."""
        self.current_entry = None
        self.current_choices = []
        self.selected_index = 0
        self.current_owner_name = ""
        
        # Process queue until we find a valid entry with choices
        while self.queue:
            entry = self.queue.pop(0)
            
            if entry.owner == "hero":
                choices = perk_system.pick_perk_choices(self.game.hero_stats, max_choices=3)
                owner_name = "Hero"
                
            elif (
                entry.owner == "companion"
                and entry.companion_index is not None
                and 0 <= entry.companion_index < len(self.game.party)
            ):
                comp_state = self.game.party[entry.companion_index]
                choices = perk_system.pick_perk_choices(comp_state, max_choices=3)
                
                # Build display name for companion
                display_name = getattr(comp_state, "name_override", None)
                if not display_name:
                    display_name = getattr(comp_state, "name", None)
                if not display_name:
                    try:
                        template = get_companion(comp_state.template_id)
                        display_name = getattr(template, "name", None)
                    except Exception:
                        pass
                if not display_name:
                    display_name = f"Companion {entry.companion_index + 1}"
                owner_name = display_name
            else:
                # Invalid entry, skip
                continue
            
            if not choices:
                # No valid perks available, skip to next
                continue
            
            # Found valid entry with choices
            self.current_entry = entry
            self.current_choices = choices
            self.current_owner_name = owner_name
            return
        
        # Queue is empty, no more selections needed
        self.current_entry = None

    def _handle_keydown(self, event: pygame.event.Event) -> Optional[str]:
        """
        Handle keyboard input.
        
        Returns:
        - None: event handled, continue
        - "exit": user cancelled, should exit scene
        """
        if not self.current_entry or not self.current_choices:
            return None
        
        key = event.key
        input_manager = getattr(self.game, "input_manager", None)
        
        # Cancel with ESC
        should_cancel = False
        if input_manager is not None:
            from systems.input import InputAction
            if input_manager.event_matches_action(InputAction.CANCEL, event):
                should_cancel = True
        else:
            if key == pygame.K_ESCAPE:
                should_cancel = True
        
        if should_cancel:
            return "exit"
        
        # Navigation with arrow keys (optional, for future enhancement)
        if key in (pygame.K_UP, pygame.K_w):
            if self.current_choices:
                self.selected_index = (self.selected_index - 1) % len(self.current_choices)
            return None
        elif key in (pygame.K_DOWN, pygame.K_s):
            if self.current_choices:
                self.selected_index = (self.selected_index + 1) % len(self.current_choices)
            return None
        
        # Selection with number keys 1-3
        index: Optional[int] = None
        if key in (pygame.K_1, pygame.K_KP1):
            index = 0
        elif key in (pygame.K_2, pygame.K_KP2):
            index = 1
        elif key in (pygame.K_3, pygame.K_KP3):
            index = 2
        elif key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
            # Enter/Space selects currently highlighted option
            index = self.selected_index
        
        if index is not None and 0 <= index < len(self.current_choices):
            chosen_perk = self.current_choices[index]
            self._apply_perk_selection(chosen_perk)
            # Move to next selection
            self._start_next_selection()
        
        return None

    def _apply_perk_selection(self, perk: perk_system.Perk) -> None:
        """Apply the selected perk to the current entry's entity."""
        if not self.current_entry:
            return
        
        entry = self.current_entry
        
        if entry.owner == "hero":
            perk_system.apply_perk_to_hero(self.game.hero_stats, perk)
            self.game.add_message(f"You chose perk: {perk.name}")
            
            # Auto-assign any newly granted skills to default loadout
            # (This is already done in apply_perk_to_hero, but ensure loadout is synced)
            self.game.hero_stats._ensure_default_loadout()
            
            # Sync stats to player entity (includes loadout sync)
            if self.game.player is not None:
                self.game.apply_hero_stats_to_player(full_heal=False)
        
        elif entry.owner == "companion" and entry.companion_index is not None:
            if 0 <= entry.companion_index < len(self.game.party):
                comp_state = self.game.party[entry.companion_index]
                perk_system.apply_perk_to_companion(comp_state, perk)
                self.game.add_message(f"{self.current_owner_name} gained perk: {perk.name}")
                
                # Recalculate companion stats
                try:
                    template = get_companion(comp_state.template_id)
                    recalc_companion_stats_for_level(comp_state, template)
                except Exception:
                    # Be defensive - bad template shouldn't crash
                    pass

    def draw(self) -> None:
        """Draw the full-screen perk selection scene with polished visuals."""
        self.screen.fill(COLOR_BG)
        w, h = self.screen.get_size()
        
        # === HEADER PANEL ===
        header_height = 130  # Slightly taller to prevent overlap
        header_y = 20
        header_panel = pygame.Surface((w - 40, header_height), pygame.SRCALPHA)
        header_panel.fill((15, 20, 25, 240))
        self.screen.blit(header_panel, (20, header_y))
        
        # Header border
        pygame.draw.rect(self.screen, (80, 100, 120), (20, header_y, w - 40, header_height), 2)
        
        # Title with glow effect
        title_text = "Level Up - Choose a Perk"
        title_shadow = self.font_title.render(title_text, True, (0, 0, 0))
        title_surf = self.font_title.render(title_text, True, (255, 255, 220))
        title_x = w // 2 - title_surf.get_width() // 2
        title_y = header_y + 18
        self.screen.blit(title_shadow, (title_x + 2, title_y + 2))
        self.screen.blit(title_surf, (title_x, title_y))
        
        # Current owner name with icon
        if self.current_owner_name:
            # Use ASCII-safe indicators
            owner_prefix = "[HERO]" if self.current_entry and self.current_entry.owner == "hero" else "[COMP]"
            owner_text = f"{owner_prefix} Selecting for: {self.current_owner_name}"
            owner_surf = self.font.render(owner_text, True, (220, 240, 255))
            owner_y = title_y + self.font_title.get_height() + 12
            self.screen.blit(owner_surf, (w // 2 - owner_surf.get_width() // 2, owner_y))
        
        # Queue status badge
        queue_count = len(self.queue)
        if queue_count > 0:
            queue_text = f"{queue_count} more selection{'s' if queue_count != 1 else ''} pending"
            queue_surf = self.font_small.render(queue_text, True, (255, 220, 150))
            queue_bg = pygame.Surface((queue_surf.get_width() + 16, 24), pygame.SRCALPHA)
            queue_bg.fill((80, 60, 40, 200))
            queue_x = w // 2 - queue_surf.get_width() // 2
            queue_y = (owner_y if self.current_owner_name else title_y + self.font_title.get_height() + 12) + self.font.get_height() + 10
            self.screen.blit(queue_bg, (queue_x - 8, queue_y - 2))
            self.screen.blit(queue_surf, (queue_x, queue_y))
        
        # Draw perk choices
        if not self.current_choices:
            # No choices available - centered message
            no_choices_panel = pygame.Surface((500, 150), pygame.SRCALPHA)
            no_choices_panel.fill((30, 30, 40, 220))
            no_choices_x = w // 2 - 250
            no_choices_y = h // 2 - 75
            self.screen.blit(no_choices_panel, (no_choices_x, no_choices_y))
            pygame.draw.rect(self.screen, (100, 100, 120), (no_choices_x, no_choices_y, 500, 150), 2)
            
            no_choices = self.font.render("No perks available", True, (180, 180, 180))
            self.screen.blit(no_choices, (w // 2 - no_choices.get_width() // 2, h // 2 - 30))
            
            hint = self.font_small.render("Press ESC to continue", True, (140, 140, 140))
            self.screen.blit(hint, (w // 2 - hint.get_width() // 2, h // 2 + 10))
            return
        
        # === PERK CHOICES SECTION ===
        start_y = header_y + header_height + 30
        item_height = 160  # Increased height to prevent text overlap
        item_spacing = 25
        
        for i, perk in enumerate(self.current_choices):
            is_selected = (i == self.selected_index)
            y_pos = start_y + i * (item_height + item_spacing)
            
            self._draw_perk_choice(perk, i, y_pos, w, item_height, is_selected)
        
        # === FOOTER INSTRUCTIONS ===
        footer_height = 80
        footer_y = h - footer_height
        footer_panel = pygame.Surface((w - 40, footer_height), pygame.SRCALPHA)
        footer_panel.fill((15, 20, 25, 240))
        self.screen.blit(footer_panel, (20, footer_y))
        pygame.draw.line(self.screen, (80, 100, 120), (20, footer_y), (w - 20, footer_y), 2)
        
        hint_y = footer_y + 15
        hint1 = self.font_small.render("Press 1-3 or Enter/Space to select", True, (200, 220, 240))
        hint2 = self.font_small.render("Arrow keys: navigate | ESC: cancel all", True, (180, 200, 220))
        
        self.screen.blit(hint1, (w // 2 - hint1.get_width() // 2, hint_y))
        self.screen.blit(hint2, (w // 2 - hint2.get_width() // 2, hint_y + 24))

    def _draw_perk_choice(self, perk: perk_system.Perk, index: int, y: int, screen_width: int, height: int, is_selected: bool) -> None:
        """Draw a single perk choice option with enhanced visuals."""
        center_x = screen_width // 2
        box_width = min(700, screen_width - 80)
        box_x = center_x - box_width // 2
        
        # Get branch color
        branch_colors = {
            "vitality": (200, 100, 100),  # Red
            "blade": (150, 150, 200),     # Blue
            "ward": (150, 200, 150),      # Green
            "focus": (200, 150, 200),     # Purple
            "mobility": (200, 200, 150),  # Yellow
            "general": (180, 180, 180),   # Gray
        }
        branch = perk.branch or "general"
        branch_color = branch_colors.get(branch, (180, 180, 180))
        
        # Enhanced selection highlighting
        if is_selected:
            # Outer glow effect
            glow_surf = pygame.Surface((box_width + 8, height + 8), pygame.SRCALPHA)
            glow_alpha = 80 if self.cursor_visible else 40
            glow_color = (*branch_color, glow_alpha)
            pygame.draw.rect(glow_surf, glow_color, (0, 0, box_width + 8, height + 8), 4)
            self.screen.blit(glow_surf, (box_x - 4, y - 4))
            
            # Main background with gradient
            bg = pygame.Surface((box_width, height), pygame.SRCALPHA)
            for i in range(height):
                alpha = int(240 - (i / height) * 30)
                # Blend branch color with background
                r = int(branch_color[0] * 0.15 + 50)
                g = int(branch_color[1] * 0.15 + 50)
                b = int(branch_color[2] * 0.15 + 50)
                color = (r, g, b, alpha)
                pygame.draw.line(bg, color, (0, i), (box_width, i))
            self.screen.blit(bg, (box_x, y))
            
            # Border with branch color accent
            pygame.draw.rect(self.screen, branch_color, (box_x, y, box_width, height), 3)
            # Inner highlight
            inner_color = tuple(min(255, c + 60) for c in branch_color)
            pygame.draw.rect(self.screen, inner_color, (box_x + 2, y + 2, box_width - 4, height - 4), 1)
        else:
            # Unselected background
            bg = pygame.Surface((box_width, height), pygame.SRCALPHA)
            bg.fill((30, 35, 40, 200))
            self.screen.blit(bg, (box_x, y))
            
            # Subtle border
            pygame.draw.rect(self.screen, (80, 80, 100), (box_x, y, box_width, height), 2)
        
        # Selection indicator (number badge)
        badge_size = 40
        badge_x = box_x + 15
        badge_y = y + 15
        badge_bg = pygame.Surface((badge_size, badge_size), pygame.SRCALPHA)
        if is_selected:
            badge_bg.fill((*branch_color, 220))
        else:
            badge_bg.fill((60, 60, 70, 200))
        self.screen.blit(badge_bg, (badge_x, badge_y))
        pygame.draw.rect(self.screen, branch_color if is_selected else (100, 100, 120), 
                       (badge_x, badge_y, badge_size, badge_size), 2)
        
        # Number in badge
        number_text = str(index + 1)
        number_surf = self.font_title.render(number_text, True, (255, 255, 255))
        number_x = badge_x + (badge_size - number_surf.get_width()) // 2
        number_y = badge_y + (badge_size - number_surf.get_height()) // 2
        self.screen.blit(number_surf, (number_x, number_y))
        
        # Content area - better spacing to prevent overlap
        content_x = box_x + badge_size + 30
        content_y = y + 18
        content_width = box_width - badge_size - 50  # More margin
        
        # Branch badge
        if perk.branch:
            branch_label = perk.branch.upper()
            branch_surf = self.font_small.render(branch_label, True, (255, 255, 255))
            branch_bg_width = branch_surf.get_width() + 12
            branch_bg_height = 22
            branch_bg = pygame.Surface((branch_bg_width, branch_bg_height), pygame.SRCALPHA)
            branch_bg.fill((*branch_color, 240))
            branch_bg_x = content_x
            branch_bg_y = content_y
            self.screen.blit(branch_bg, (branch_bg_x, branch_bg_y))
            pygame.draw.rect(self.screen, tuple(min(255, c + 40) for c in branch_color),
                          (branch_bg_x, branch_bg_y, branch_bg_width, branch_bg_height), 1)
            self.screen.blit(branch_surf, (branch_bg_x + 6, branch_bg_y + 3))
            content_y += branch_bg_height + 14  # More spacing after branch badge
        
        # Perk name
        name_color = tuple(min(255, c + 80) for c in branch_color) if is_selected else (240, 240, 240)
        name_surf = self.font.render(perk.name, True, name_color)
        self.screen.blit(name_surf, (content_x, content_y))
        content_y += name_surf.get_height() + 14  # More spacing after name
        
        # Description (word-wrapped) - ensure it fits
        desc_lines = self._wrap_text(perk.description, self.font_small, content_width)
        desc_color = (220, 230, 240) if is_selected else (190, 200, 210)
        line_height = self.font_small.get_height() + 4
        max_desc_lines = max(2, (height - (content_y - y) - 30) // line_height)  # Calculate available space
        for i, line in enumerate(desc_lines[:max_desc_lines]):  # Limit lines to fit
            desc_surf = self.font_small.render(line, True, desc_color)
            self.screen.blit(desc_surf, (content_x, content_y))
            content_y += line_height
        
        # Tags (if any) - as small badges, only if there's room
        if perk.tags and content_y < y + height - 25:
            content_y += 8
            tag_x = content_x
            for tag in perk.tags:
                tag_surf = self.font_small.render(tag, True, (180, 200, 220))
                tag_bg_width = tag_surf.get_width() + 8
                tag_bg_height = 18
                # Check if tag fits on current line, otherwise wrap
                if tag_x + tag_bg_width > box_x + box_width - 20:
                    tag_x = content_x
                    content_y += tag_bg_height + 4
                    # Don't draw if it would overflow
                    if content_y + tag_bg_height > y + height - 5:
                        break
                tag_bg = pygame.Surface((tag_bg_width, tag_bg_height), pygame.SRCALPHA)
                tag_bg.fill((60, 70, 80, 180))
                self.screen.blit(tag_bg, (tag_x, content_y))
                self.screen.blit(tag_surf, (tag_x + 4, content_y + 2))
                tag_x += tag_bg_width + 6
    
    def _wrap_text(self, text: str, font: pygame.font.Font, max_width: int) -> List[str]:
        """Word-wrap text to fit within max_width."""
        words = text.split()
        lines: List[str] = []
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

