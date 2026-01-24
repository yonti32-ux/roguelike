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
        """Draw the full-screen perk selection scene."""
        self.screen.fill(COLOR_BG)
        w, h = self.screen.get_size()
        
        # Title
        title = self.font_title.render("Level Up - Choose a Perk", True, (240, 240, 200))
        self.screen.blit(title, (w // 2 - title.get_width() // 2, 40))
        
        # Current owner name
        if self.current_owner_name:
            owner_text = self.font.render(f"Selecting for: {self.current_owner_name}", True, (200, 200, 200))
            self.screen.blit(owner_text, (w // 2 - owner_text.get_width() // 2, 90))
        
        # Queue status
        queue_count = len(self.queue)
        if queue_count > 0:
            queue_text = self.font_small.render(f"{queue_count} more selection{'s' if queue_count != 1 else ''} pending", True, (160, 160, 160))
            self.screen.blit(queue_text, (w // 2 - queue_text.get_width() // 2, 120))
        
        # Draw perk choices
        if not self.current_choices:
            # No choices available
            no_choices = self.font.render("No perks available", True, (150, 150, 150))
            self.screen.blit(no_choices, (w // 2 - no_choices.get_width() // 2, h // 2))
            
            hint = self.font_small.render("Press ESC to continue", True, (120, 120, 120))
            self.screen.blit(hint, (w // 2 - hint.get_width() // 2, h - 60))
            return
        
        # Perk choice list
        start_y = 180
        item_height = 100
        item_spacing = 20
        
        for i, perk in enumerate(self.current_choices):
            is_selected = (i == self.selected_index)
            y_pos = start_y + i * (item_height + item_spacing)
            
            self._draw_perk_choice(perk, i, y_pos, w, item_height, is_selected)
        
        # Instructions
        hint_y = h - 80
        hint1 = self.font_small.render("Press 1-3 or Enter/Space to select", True, (160, 160, 160))
        hint2 = self.font_small.render("Arrow keys: navigate | ESC: cancel all", True, (140, 140, 140))
        
        self.screen.blit(hint1, (w // 2 - hint1.get_width() // 2, hint_y))
        self.screen.blit(hint2, (w // 2 - hint2.get_width() // 2, hint_y + 22))

    def _draw_perk_choice(self, perk: perk_system.Perk, index: int, y: int, screen_width: int, height: int, is_selected: bool) -> None:
        """Draw a single perk choice option."""
        center_x = screen_width // 2
        box_width = min(600, screen_width - 80)
        box_x = center_x - box_width // 2
        
        # Background box
        bg_color = (40, 40, 50) if not is_selected else (60, 60, 75)
        border_color = (100, 100, 120) if not is_selected else (180, 180, 200)
        border_width = 2 if not is_selected else 3
        
        pygame.draw.rect(self.screen, bg_color, (box_x, y, box_width, height))
        pygame.draw.rect(self.screen, border_color, (box_x, y, box_width, height), border_width)
        
        # Selection indicator
        if is_selected and self.cursor_visible:
            indicator = self.font.render(">", True, (255, 255, 200))
            self.screen.blit(indicator, (box_x + 10, y + height // 2 - indicator.get_height() // 2))
        
        # Perk name
        name_label = f"{index + 1}) {perk.name}"
        if perk.branch:
            branch_label = f"[{perk.branch.upper()}]"
            name_label = f"{index + 1}) {branch_label} {perk.name}"
        
        name_color = (240, 240, 220) if is_selected else (220, 220, 200)
        name_surf = self.font.render(name_label, True, name_color)
        self.screen.blit(name_surf, (box_x + 40, y + 12))
        
        # Description
        desc_color = (190, 190, 200) if is_selected else (170, 170, 180)
        desc_surf = self.font_small.render(perk.description, True, desc_color)
        self.screen.blit(desc_surf, (box_x + 40, y + 40))
        
        # Tags (if any)
        if perk.tags:
            tags_text = ", ".join(perk.tags)
            tags_surf = self.font_small.render(f"Tags: {tags_text}", True, (140, 140, 150))
            self.screen.blit(tags_surf, (box_x + 40, y + 60))

