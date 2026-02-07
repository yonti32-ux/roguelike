"""
Full-screen blocking scene for perk selection on level-up.

This scene manages the queue of entities (hero + companions) that need
to select perks, displays choices, handles input, and applies selections.
"""

from dataclasses import dataclass
from typing import Optional, List, TYPE_CHECKING

import pygame

from settings import FPS
from systems import perks as perk_system
from systems.party import get_companion, recalc_companion_stats_for_level
from ui.screen_components import draw_gradient_background, draw_panel_with_shadow
from ui.screen_constants import (
    COLOR_BG_PANEL,
    COLOR_BORDER_BRIGHT,
    COLOR_BORDER_GOLD,
    COLOR_GRADIENT_START,
    COLOR_GRADIENT_END,
    COLOR_SHADOW,
    COLOR_SUBTITLE,
    COLOR_TEXT,
    COLOR_TEXT_DIM,
    COLOR_TEXT_DIMMER,
    COLOR_TITLE,
    SHADOW_OFFSET_X,
    SHADOW_OFFSET_Y,
    BORDER_WIDTH_MEDIUM,
    PANEL_SHADOW_SIZE,
)

if TYPE_CHECKING:
    from ..core.game import Game

# Branch accent colors for perk cards (vitality, blade, ward, focus, mobility, general)
BRANCH_COLORS = {
    "vitality": (80, 200, 120),
    "blade": (220, 100, 90),
    "ward": (90, 150, 255),
    "focus": (180, 100, 255),
    "mobility": (255, 180, 80),
    "general": (140, 150, 165),
}

# Perk card layout: taller panels so name, description (wrapped), and tags don't overlap
PERK_CARD_HEIGHT = 132
PERK_DESC_LINE_HEIGHT = 18
PERK_DESC_MAX_LINES = 2


def _wrap_description(font: pygame.font.Font, text: str, max_width: int, max_lines: int = PERK_DESC_MAX_LINES) -> List[str]:
    """Wrap description into lines that fit within max_width. Returns at most max_lines."""
    words = text.split()
    if not words:
        return []
    lines: List[str] = []
    current: List[str] = []
    for word in words:
        trial = " ".join(current + [word])
        if font.size(trial)[0] <= max_width:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current))
                if len(lines) >= max_lines:
                    return lines
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines[:max_lines]


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
            
            # Sync stats to player entity
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
        """Draw the full-screen perk selection scene."""
        w, h = self.screen.get_size()

        # Gradient background
        draw_gradient_background(
            self.screen, 0, 0, w, h,
            COLOR_GRADIENT_START, COLOR_GRADIENT_END, True
        )

        # Title with shadow
        title_text = "Level Up — Choose a Perk"
        title_shadow = self.font_title.render(title_text, True, COLOR_SHADOW[:3])
        title_surf = self.font_title.render(title_text, True, COLOR_TITLE)
        title_x = w // 2 - title_surf.get_width() // 2
        title_y = 36
        self.screen.blit(title_shadow, (title_x + SHADOW_OFFSET_X, title_y + SHADOW_OFFSET_Y))
        self.screen.blit(title_surf, (title_x, title_y))

        # Subtitle: "Selecting for: Name" in a small ribbon
        if self.current_owner_name:
            owner_text = f"Selecting for: {self.current_owner_name}"
            owner_surf = self.font.render(owner_text, True, COLOR_SUBTITLE)
            ribbon_w = owner_surf.get_width() + 32
            ribbon_h = 32
            ribbon_x = w // 2 - ribbon_w // 2
            ribbon_y = 82
            ribbon = pygame.Surface((ribbon_w, ribbon_h), pygame.SRCALPHA)
            ribbon.fill((0, 0, 0, 80))
            pygame.draw.rect(ribbon, COLOR_BORDER_BRIGHT, (0, 0, ribbon_w, ribbon_h), 1)
            self.screen.blit(ribbon, (ribbon_x, ribbon_y))
            self.screen.blit(owner_surf, (w // 2 - owner_surf.get_width() // 2, ribbon_y + 8))

        # Queue status badge
        queue_count = len(self.queue)
        if queue_count > 0:
            queue_text = f"{queue_count} more selection{'s' if queue_count != 1 else ''} pending"
            badge_surf = self.font_small.render(queue_text, True, COLOR_TEXT_DIMMER)
            badge_w = badge_surf.get_width() + 20
            badge_h = 24
            badge_x = w // 2 - badge_w // 2
            badge_y = 120
            badge = pygame.Surface((badge_w, badge_h), pygame.SRCALPHA)
            badge.fill((60, 70, 90, 200))
            pygame.draw.rect(badge, COLOR_BORDER_BRIGHT, (0, 0, badge_w, badge_h), 1)
            self.screen.blit(badge, (badge_x, badge_y))
            self.screen.blit(badge_surf, (w // 2 - badge_surf.get_width() // 2, badge_y + 4))

        # Draw perk choices
        if not self.current_choices:
            no_choices = self.font.render("No perks available", True, COLOR_TEXT_DIMMER)
            self.screen.blit(no_choices, (w // 2 - no_choices.get_width() // 2, h // 2 - 20))
            hint = self.font_small.render("Press ESC to continue", True, COLOR_TEXT_DIMMER)
            self.screen.blit(hint, (w // 2 - hint.get_width() // 2, h - 60))
            return

        # Perk choice list (taller panels so text doesn't overlap)
        start_y = 152
        item_spacing = 14

        for i, perk in enumerate(self.current_choices):
            is_selected = (i == self.selected_index)
            y_pos = start_y + i * (PERK_CARD_HEIGHT + item_spacing)
            self._draw_perk_choice(perk, i, y_pos, w, PERK_CARD_HEIGHT, is_selected)

        # Footer hint panel
        hint_y = h - 72
        hint_w = 520
        hint_h = 44
        hint_x = w // 2 - hint_w // 2
        hint_panel = pygame.Surface((hint_w, hint_h), pygame.SRCALPHA)
        hint_panel.fill((0, 0, 0, 140))
        pygame.draw.rect(hint_panel, COLOR_BORDER_BRIGHT, (0, 0, hint_w, hint_h), 1)
        self.screen.blit(hint_panel, (hint_x, hint_y))
        hint1 = self.font_small.render("1–3 or Enter / Space: select", True, COLOR_TEXT_DIM)
        hint2 = self.font_small.render("↑↓: navigate   ESC: cancel", True, COLOR_TEXT_DIMMER)
        self.screen.blit(hint1, (w // 2 - hint1.get_width() // 2, hint_y + 8))
        self.screen.blit(hint2, (w // 2 - hint2.get_width() // 2, hint_y + 26))

    def _draw_perk_choice(self, perk: perk_system.Perk, index: int, y: int, screen_width: int, height: int, is_selected: bool) -> None:
        """Draw a single perk choice option with branch accent and polish."""
        center_x = screen_width // 2
        box_width = min(620, screen_width - 80)
        box_x = center_x - box_width // 2

        # Panel with shadow
        border_color = COLOR_BORDER_GOLD if is_selected else COLOR_BORDER_BRIGHT
        border_width = BORDER_WIDTH_MEDIUM + 1 if is_selected else BORDER_WIDTH_MEDIUM
        bg_alpha = 250 if is_selected else 240
        panel_bg = (*COLOR_BG_PANEL[:3], bg_alpha)
        draw_panel_with_shadow(
            self.screen, box_x, y, box_width, height,
            bg_color=panel_bg,
            border_color=border_color,
            border_width=border_width,
            shadow_size=PANEL_SHADOW_SIZE,
        )

        # Left accent stripe (branch color)
        branch_key = (perk.branch or "general").lower()
        accent_color = BRANCH_COLORS.get(branch_key, BRANCH_COLORS["general"])
        stripe_width = 5
        pygame.draw.rect(self.screen, accent_color, (box_x, y, stripe_width, height))

        # Selection highlight overlay
        if is_selected:
            overlay = pygame.Surface((box_width - stripe_width, height), pygame.SRCALPHA)
            overlay.fill((255, 255, 240, 12))
            self.screen.blit(overlay, (box_x + stripe_width, y))
            if self.cursor_visible:
                cursor_surf = self.font.render("▶", True, COLOR_TITLE)
                self.screen.blit(cursor_surf, (box_x + stripe_width + 12, y + height // 2 - cursor_surf.get_height() // 2))

        # Number badge (1, 2, 3)
        num_str = str(index + 1)
        num_surf = self.font_small.render(num_str, True, (0, 0, 0))
        num_badge_r = 12
        num_cx = box_x + stripe_width + 20 + num_badge_r
        num_cy = y + 20
        pygame.draw.circle(self.screen, accent_color, (num_cx, num_cy), num_badge_r)
        pygame.draw.circle(self.screen, COLOR_BORDER_BRIGHT, (num_cx, num_cy), num_badge_r, 1)
        self.screen.blit(num_surf, (num_cx - num_surf.get_width() // 2, num_cy - num_surf.get_height() // 2))

        # Content X: after stripe and number badge
        name_x = box_x + stripe_width + 44
        content_right = box_x + box_width - 16
        desc_max_width = content_right - name_x

        # Perk name (single line; truncate if extremely long)
        name_color = COLOR_TITLE if is_selected else COLOR_TEXT
        name_text = perk.name
        name_surf = self.font.render(name_text, True, name_color)
        if name_surf.get_width() > desc_max_width - 80:  # leave room for branch tag
            # Truncate with ellipsis
            while name_text and self.font.size(name_text + "…")[0] > desc_max_width - 80:
                name_text = name_text[:-1]
            name_text = name_text + "…" if len(name_text) < len(perk.name) else name_text
            name_surf = self.font.render(name_text, True, name_color)
        self.screen.blit(name_surf, (name_x, y + 10))

        # Branch tag pill (right of name if branch is not general)
        if perk.branch and perk.branch.lower() != "general":
            branch_label = perk.branch.upper()
            tag_surf = self.font_small.render(branch_label, True, (255, 255, 255))
            tag_w = tag_surf.get_width() + 12
            tag_h = 18
            tag_x = name_x + name_surf.get_width() + 10
            tag_y = y + 8
            tag_bg = (*accent_color, 220)
            tag_rect = pygame.Rect(tag_x, tag_y, tag_w, tag_h)
            tag_panel = pygame.Surface((tag_w, tag_h), pygame.SRCALPHA)
            tag_panel.fill(tag_bg)
            pygame.draw.rect(tag_panel, COLOR_BORDER_BRIGHT, (0, 0, tag_w, tag_h), 1)
            self.screen.blit(tag_panel, tag_rect)
            self.screen.blit(tag_surf, (tag_x + 6, tag_y + 2))

        # Description: word-wrapped to fit panel, max 2 lines
        desc_color = COLOR_TEXT_DIM if is_selected else COLOR_TEXT_DIMMER
        desc_lines = _wrap_description(self.font_small, perk.description, desc_max_width, PERK_DESC_MAX_LINES)
        desc_y = y + 36
        for i_line, line in enumerate(desc_lines):
            line_surf = self.font_small.render(line, True, desc_color)
            self.screen.blit(line_surf, (name_x, desc_y + i_line * PERK_DESC_LINE_HEIGHT))

        # Tags as small pills (if any), placed below description with clear gap
        tags_area_y = y + 36 + PERK_DESC_MAX_LINES * PERK_DESC_LINE_HEIGHT + 10
        if perk.tags and tags_area_y + 20 <= y + height:
            tag_start_x = name_x
            tag_row_y = tags_area_y
            for tag in perk.tags[:5]:
                ts = self.font_small.render(tag, True, COLOR_TEXT_DIMMER)
                tw = ts.get_width() + 10
                th = 16
                tp = pygame.Surface((tw, th), pygame.SRCALPHA)
                tp.fill((80, 85, 100, 200))
                pygame.draw.rect(tp, COLOR_BORDER_BRIGHT, (0, 0, tw, th), 1)
                self.screen.blit(tp, (tag_start_x, tag_row_y))
                self.screen.blit(ts, (tag_start_x + 5, tag_row_y + 1))
                tag_start_x += tw + 6

