"""
Skill Management Screen - allows players to assign skills to hotbar slots.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Tuple, Dict

import pygame

from ui.screen_components import draw_screen_header, draw_screen_footer
from ui.screen_utils import safe_getattr
from ui.skill_screen import get_unlocked_skills_for_hero, get_unlocked_skills_for_companion
from systems.skills import get as get_skill
from systems.party import get_companion, CompanionState
from systems.input import InputAction

if TYPE_CHECKING:
    from engine.core.game import Game


class SkillManagementScreen:
    """
    Screen for managing skill hotbar assignments.
    
    Features:
    - View all unlocked skills
    - Assign skills to hotbar slots (click to assign)
    - Visual hotbar preview
    - Support for hero and companions
    """
    
    def __init__(self, game: "Game") -> None:
        self.game = game
        self.font = game.ui_font
        self.font_title = pygame.font.SysFont("consolas", 28)
        self.font_small = pygame.font.SysFont("consolas", 16)
        
        # Current focus: 0 = hero, 1+ = companions
        self.focus_index: int = 0
        
        # Selected skill for assignment (None = not selecting)
        self.selected_skill_id: Optional[str] = None
        
        # Hover state
        self.hovered_skill_id: Optional[str] = None
        self.hovered_slot_index: Optional[int] = None
        
        # Visual state
        self.cursor_visible: bool = True
        self.cursor_timer: float = 0.0
        
        # Loadout management
        self.hovered_loadout_index: Optional[int] = None
    
    def get_focused_entity(self) -> Tuple[bool, Optional[CompanionState], Optional[str]]:
        """Get the currently focused entity (hero or companion)."""
        party_list: List[CompanionState] = getattr(self.game, "party", None) or []
        total_slots = 1 + len(party_list)
        
        if total_slots <= 1:
            self.focus_index = 0
        
        if self.focus_index == 0:
            # Hero
            hero_name = getattr(self.game.hero_stats, "hero_name", "Hero")
            return True, None, hero_name
        else:
            # Companion
            comp_idx = self.focus_index - 1
            if 0 <= comp_idx < len(party_list):
                comp = party_list[comp_idx]
                if isinstance(comp, CompanionState):
                    display_name = getattr(comp, "name_override", None)
                    if not display_name:
                        try:
                            template = get_companion(comp.template_id)
                            display_name = template.name
                        except KeyError:
                            display_name = f"Companion {comp_idx + 1}"
                    return False, comp, display_name
        
        # Fallback
        return True, None, "Hero"
    
    def get_unlocked_skills(self) -> List[str]:
        """Get unlocked skills for the currently focused entity."""
        is_hero, comp, _ = self.get_focused_entity()
        
        if is_hero:
            return get_unlocked_skills_for_hero(self.game)
        else:
            if comp is None:
                return []
            return get_unlocked_skills_for_companion(comp)
    
    def get_skill_slots(self) -> List[Optional[str]]:
        """Get current skill slots for the focused entity."""
        is_hero, comp, _ = self.get_focused_entity()
        
        if is_hero:
            return list(getattr(self.game.hero_stats, "skill_slots", [None, None, None, None]))
        else:
            if comp is None:
                return [None, None, None, None]
            return list(getattr(comp, "skill_slots", [None, None, None, None]))
    
    def set_skill_slot(self, slot_index: int, skill_id: Optional[str]) -> None:
        """Assign a skill to a hotbar slot."""
        is_hero, comp, _ = self.get_focused_entity()
        
        if is_hero:
            slots = getattr(self.game.hero_stats, "skill_slots", [None, None, None, None])
            # Ensure list is long enough
            while len(slots) <= slot_index:
                slots.append(None)
            slots[slot_index] = skill_id
            # Trim to max 8 slots
            slots = slots[:8]
            self.game.hero_stats.skill_slots = slots
        else:
            if comp is None:
                return
            slots = getattr(comp, "skill_slots", [None, None, None, None])
            while len(slots) <= slot_index:
                slots.append(None)
            slots[slot_index] = skill_id
            slots = slots[:8]
            comp.skill_slots = slots
    
    def clear_skill_slot(self, slot_index: int) -> None:
        """Clear a skill from a hotbar slot."""
        self.set_skill_slot(slot_index, None)
    
    def get_active_loadout_index(self) -> int:
        """Get the active loadout index for the focused entity."""
        is_hero, comp, _ = self.get_focused_entity()
        if is_hero:
            return getattr(self.game.hero_stats, "active_loadout_index", 0)
        else:
            if comp is None:
                return 0
            return getattr(comp, "active_loadout_index", 0)
    
    def get_loadout_count(self) -> int:
        """Get the number of loadouts for the focused entity."""
        is_hero, comp, _ = self.get_focused_entity()
        if is_hero:
            loadouts = getattr(self.game.hero_stats, "skill_loadouts", [[None] * 8])
            return len(loadouts)
        else:
            if comp is None:
                return 1
            loadouts = getattr(comp, "skill_loadouts", [[None] * 8])
            return len(loadouts)
    
    def switch_loadout(self, index: int) -> None:
        """Switch to a different loadout."""
        is_hero, comp, _ = self.get_focused_entity()
        if is_hero:
            self.game.hero_stats.switch_loadout(index)
        else:
            if comp is None:
                return
            comp.switch_loadout(index)
    
    def create_new_loadout(self) -> int:
        """Create a new empty loadout and return its index."""
        is_hero, comp, _ = self.get_focused_entity()
        if is_hero:
            return self.game.hero_stats.create_new_loadout()
        else:
            if comp is None:
                return 0
            return comp.create_new_loadout()
    
    def handle_click(self, mx: int, my: int, w: int, h: int) -> None:
        """Handle mouse click for skill assignment and loadout switching."""
        # Check if clicking on loadout selector
        loadout_y = 170
        loadout_x = 50
        loadout_width = 80
        loadout_height = 30
        loadout_spacing = 5
        
        loadout_count = self.get_loadout_count()
        active_loadout = self.get_active_loadout_index()
        
        for idx in range(min(loadout_count, 5)):  # Show up to 5 loadouts
            loadout_rect_x = loadout_x + idx * (loadout_width + loadout_spacing)
            loadout_rect = pygame.Rect(loadout_rect_x, loadout_y, loadout_width, loadout_height)
            if loadout_rect.collidepoint(mx, my):
                # Clicked on a loadout - switch to it
                self.switch_loadout(idx)
                return
        
        # Check for "New Loadout" button
        new_loadout_x = loadout_x + min(loadout_count, 5) * (loadout_width + loadout_spacing) + 10
        new_loadout_rect = pygame.Rect(new_loadout_x, loadout_y, 120, loadout_height)
        if new_loadout_rect.collidepoint(mx, my):
            # Create new loadout
            new_idx = self.create_new_loadout()
            self.switch_loadout(new_idx)
            return
        
        # Check if clicking on a skill in the list
        unlocked_skills = self.get_unlocked_skills()
        skill_list_y = 290
        skill_list_x = 50
        skill_item_height = 40
        skill_item_width = 300
        
        for idx, skill_id in enumerate(unlocked_skills):
            skill_y = skill_list_y + idx * skill_item_height
            skill_rect = pygame.Rect(skill_list_x, skill_y, skill_item_width, skill_item_height)
            if skill_rect.collidepoint(mx, my):
                # Clicked on a skill - select it for assignment
                self.selected_skill_id = skill_id
                return
        
        # Check if clicking on a hotbar slot
        hotbar_x = 400
        hotbar_y = 250
        slot_width = 120
        slot_height = 80
        slot_spacing = 10
        
        slots = self.get_skill_slots()
        max_slots = max(8, len(slots))  # Support up to 8 slots
        
        for idx in range(max_slots):
            slot_x = hotbar_x + idx * (slot_width + slot_spacing)
            slot_rect = pygame.Rect(slot_x, hotbar_y, slot_width, slot_height)
            if slot_rect.collidepoint(mx, my):
                # Clicked on a slot
                if self.selected_skill_id:
                    # Assign selected skill to this slot
                    # If skill is already in another slot, clear that slot first
                    current_slots = self.get_skill_slots()
                    for i, existing_id in enumerate(current_slots):
                        if existing_id == self.selected_skill_id and i != idx:
                            self.clear_skill_slot(i)
                    self.set_skill_slot(idx, self.selected_skill_id)
                    self.selected_skill_id = None
                else:
                    # Right-click or shift-click to clear slot
                    # For now, just clear on click if no skill selected
                    pass
                return
        
        # Check if clicking on "Clear" button in a slot
        for idx in range(max_slots):
            slot_x = hotbar_x + idx * (slot_width + slot_spacing)
            clear_rect = pygame.Rect(slot_x + slot_width - 20, hotbar_y + 5, 15, 15)
            if clear_rect.collidepoint(mx, my):
                self.clear_skill_slot(idx)
                return
    
    def handle_mouse_motion(self, mx: int, my: int, w: int, h: int) -> None:
        """Handle mouse motion for hover effects."""
        self.hovered_skill_id = None
        self.hovered_slot_index = None
        self.hovered_loadout_index = None
        
        # Check if hovering over loadout selector
        loadout_y = 170
        loadout_x = 50
        loadout_width = 80
        loadout_height = 30
        loadout_spacing = 5
        
        loadout_count = self.get_loadout_count()
        for idx in range(min(loadout_count, 5)):
            loadout_rect_x = loadout_x + idx * (loadout_width + loadout_spacing)
            loadout_rect = pygame.Rect(loadout_rect_x, loadout_y, loadout_width, loadout_height)
            if loadout_rect.collidepoint(mx, my):
                self.hovered_loadout_index = idx
                return
        
        # Check for "New Loadout" button hover
        new_loadout_x = loadout_x + min(loadout_count, 5) * (loadout_width + loadout_spacing) + 10
        new_loadout_rect = pygame.Rect(new_loadout_x, loadout_y, 120, loadout_height)
        if new_loadout_rect.collidepoint(mx, my):
            self.hovered_loadout_index = -1  # -1 indicates "new" button
            return
        
        # Check if hovering over a skill
        unlocked_skills = self.get_unlocked_skills()
        skill_list_y = 250
        skill_list_x = 50
        skill_item_height = 40
        skill_item_width = 300
        
        for idx, skill_id in enumerate(unlocked_skills):
            skill_y = skill_list_y + idx * skill_item_height
            skill_rect = pygame.Rect(skill_list_x, skill_y, skill_item_width, skill_item_height)
            if skill_rect.collidepoint(mx, my):
                self.hovered_skill_id = skill_id
                return
        
        # Check if hovering over a hotbar slot
        hotbar_x = 400
        hotbar_y = 250
        slot_width = 120
        slot_height = 80
        slot_spacing = 10
        
        slots = self.get_skill_slots()
        max_slots = max(8, len(slots))
        
        for idx in range(max_slots):
            slot_x = hotbar_x + idx * (slot_width + slot_spacing)
            slot_rect = pygame.Rect(slot_x, hotbar_y, slot_width, slot_height)
            if slot_rect.collidepoint(mx, my):
                self.hovered_slot_index = idx
                return
    
    def _draw_loadout_selector(self, screen: pygame.Surface) -> None:
        """Draw the loadout selector buttons."""
        loadout_y = 170
        loadout_x = 50
        loadout_width = 80
        loadout_height = 30
        loadout_spacing = 5
        
        # Loadout label
        loadout_label = self.font.render("Loadouts:", True, (200, 200, 200))
        screen.blit(loadout_label, (loadout_x, loadout_y - 25))
        
        loadout_count = self.get_loadout_count()
        active_loadout = self.get_active_loadout_index()
        
        # Draw loadout buttons (show up to 5)
        for idx in range(min(loadout_count, 5)):
            loadout_rect_x = loadout_x + idx * (loadout_width + loadout_spacing)
            is_active = (idx == active_loadout)
            is_hovered = (idx == self.hovered_loadout_index)
            
            # Background color
            if is_active:
                bg_color = (80, 120, 80)
                border_color = (150, 255, 150)
            elif is_hovered:
                bg_color = (60, 80, 100)
                border_color = (150, 200, 255)
            else:
                bg_color = (40, 40, 50)
                border_color = (100, 100, 120)
            
            loadout_rect = pygame.Rect(loadout_rect_x, loadout_y, loadout_width, loadout_height)
            pygame.draw.rect(screen, bg_color, loadout_rect)
            pygame.draw.rect(screen, border_color, loadout_rect, 2)
            
            # Loadout number (1-based for display)
            loadout_text = self.font_small.render(f"Loadout {idx + 1}", True, (240, 240, 240) if is_active else (200, 200, 200))
            text_x = loadout_rect_x + (loadout_width - loadout_text.get_width()) // 2
            text_y = loadout_y + (loadout_height - loadout_text.get_height()) // 2
            screen.blit(loadout_text, (text_x, text_y))
        
        # "New Loadout" button
        new_loadout_x = loadout_x + min(loadout_count, 5) * (loadout_width + loadout_spacing) + 10
        new_loadout_rect = pygame.Rect(new_loadout_x, loadout_y, 120, loadout_height)
        is_hovered_new = (self.hovered_loadout_index == -1)  # Use -1 to indicate "new" button hover
        
        if is_hovered_new:
            bg_color = (60, 80, 100)
            border_color = (150, 200, 255)
        else:
            bg_color = (50, 50, 70)
            border_color = (120, 120, 150)
        
        pygame.draw.rect(screen, bg_color, new_loadout_rect)
        pygame.draw.rect(screen, border_color, new_loadout_rect, 2)
        
        new_text = self.font_small.render("+ New", True, (200, 200, 200))
        text_x = new_loadout_x + (new_loadout_rect.width - new_text.get_width()) // 2
        text_y = loadout_y + (loadout_height - new_text.get_height()) // 2
        screen.blit(new_text, (text_x, text_y))
    
    def update(self, dt: float) -> None:
        """Update visual state."""
        self.cursor_timer += dt
        if self.cursor_timer >= 0.5:
            self.cursor_timer = 0.0
            self.cursor_visible = not self.cursor_visible
    
    def draw_content(self, screen: pygame.Surface, w: int, h: int) -> None:
        """Draw the skill management interface."""
        is_hero, comp, display_name = self.get_focused_entity()
        unlocked_skills = self.get_unlocked_skills()
        skill_slots = self.get_skill_slots()
        
        # Character name (offset for tabs)
        char_text = self.font_title.render(f"Character: {display_name}", True, (220, 220, 200))
        screen.blit(char_text, (50, 130))
        
        # Draw loadout selector
        self._draw_loadout_selector(screen)
        
        # Instructions (offset for tabs)
        inst_text = self.font_small.render(
            "Click a skill to select it, then click a hotbar slot to assign it. Click a slot's X to clear.",
            True, (180, 180, 180)
        )
        screen.blit(inst_text, (50, 250))
        
        # Draw available skills list (left side)
        skills_title = self.font.render("Available Skills:", True, (200, 200, 200))
        screen.blit(skills_title, (50, 270))
        
        skill_list_y = 290
        skill_list_x = 50
        skill_item_height = 40
        skill_item_width = 300
        
        for idx, skill_id in enumerate(unlocked_skills):
            skill_y = skill_list_y + idx * skill_item_height
            try:
                skill = get_skill(skill_id)
                skill_name = skill.name
            except KeyError:
                skill_name = skill_id
            
            # Check if skill is already assigned
            is_assigned = skill_id in skill_slots
            is_selected = (skill_id == self.selected_skill_id)
            is_hovered = (skill_id == self.hovered_skill_id)
            
            # Background color
            if is_selected:
                bg_color = (80, 120, 80)
                border_color = (150, 255, 150)
            elif is_hovered:
                bg_color = (60, 60, 80)
                border_color = (150, 200, 255)
            elif is_assigned:
                bg_color = (50, 50, 70)
                border_color = (120, 120, 150)
            else:
                bg_color = (40, 40, 50)
                border_color = (100, 100, 120)
            
            skill_rect = pygame.Rect(skill_list_x, skill_y, skill_item_width, skill_item_height)
            pygame.draw.rect(screen, bg_color, skill_rect)
            pygame.draw.rect(screen, border_color, skill_rect, 2)
            
            # Skill name
            name_color = (240, 240, 240) if is_selected else (220, 220, 220)
            name_surf = self.font.render(skill_name, True, name_color)
            screen.blit(name_surf, (skill_list_x + 8, skill_y + 8))
            
            # Show which slot it's assigned to
            if is_assigned:
                slot_idx = skill_slots.index(skill_id)
                slot_text = self.font_small.render(f"Slot {slot_idx + 1}", True, (150, 200, 150))
                screen.blit(slot_text, (skill_list_x + skill_item_width - 60, skill_y + 20))
        
        # Draw hotbar slots (right side)
        hotbar_title = self.font.render("Hotbar Slots:", True, (200, 200, 200))
        screen.blit(hotbar_title, (400, 270))
        
        hotbar_x = 400
        hotbar_y = 290
        slot_width = 120
        slot_height = 80
        slot_spacing = 10
        
        # Support up to 8 slots
        max_slots = 8
        slots = skill_slots[:max_slots]
        while len(slots) < max_slots:
            slots.append(None)
        
        # Get key bindings for display
        input_manager = getattr(self.game, "input_manager", None)
        key_labels = []
        for idx in range(max_slots):
            key_label = ""
            if input_manager is not None:
                try:
                    action_map = {
                        0: InputAction.SKILL_1,
                        1: InputAction.SKILL_2,
                        2: InputAction.SKILL_3,
                        3: InputAction.SKILL_4,
                        4: InputAction.SKILL_5,
                        5: InputAction.SKILL_6,
                        6: InputAction.SKILL_7,
                        7: InputAction.SKILL_8,
                    }
                    if idx in action_map:
                        bound_keys = input_manager.get_bindings(action_map[idx])
                        if bound_keys:
                            key_label = pygame.key.name(list(bound_keys)[0]).upper()
                except (AttributeError, KeyError, TypeError):
                    pass
            key_labels.append(key_label)
        
        for idx in range(max_slots):
            slot_x = hotbar_x + idx * (slot_width + slot_spacing)
            skill_id = slots[idx]
            is_hovered = (idx == self.hovered_slot_index)
            
            # Slot background
            if is_hovered:
                bg_color = (60, 80, 100)
                border_color = (150, 200, 255)
            elif skill_id:
                bg_color = (50, 70, 50)
                border_color = (100, 200, 100)
            else:
                bg_color = (30, 30, 40)
                border_color = (80, 80, 100)
            
            slot_rect = pygame.Rect(slot_x, hotbar_y, slot_width, slot_height)
            pygame.draw.rect(screen, bg_color, slot_rect)
            pygame.draw.rect(screen, border_color, slot_rect, 3)
            
            # Slot number
            slot_num = self.font_small.render(f"Slot {idx + 1}", True, (150, 150, 150))
            screen.blit(slot_num, (slot_x + 5, hotbar_y + 5))
            
            # Key binding
            if key_labels[idx]:
                key_surf = self.font_small.render(key_labels[idx], True, (150, 200, 255))
                screen.blit(key_surf, (slot_x + slot_width - key_surf.get_width() - 5, hotbar_y + 5))
            
            if skill_id:
                try:
                    skill = get_skill(skill_id)
                    skill_name = skill.name
                    # Truncate if too long
                    if len(skill_name) > 12:
                        skill_name = skill_name[:10] + ".."
                    name_surf = self.font_small.render(skill_name, True, (240, 240, 240))
                    screen.blit(name_surf, (slot_x + 5, hotbar_y + 25))
                except KeyError:
                    pass
            
            # Clear button (X) if slot has a skill
            if skill_id:
                clear_rect = pygame.Rect(slot_x + slot_width - 20, hotbar_y + 5, 15, 15)
                clear_color = (200, 100, 100) if is_hovered else (150, 80, 80)
                pygame.draw.rect(screen, clear_color, clear_rect)
                x_surf = self.font_small.render("X", True, (255, 255, 255))
                screen.blit(x_surf, (slot_x + slot_width - 18, hotbar_y + 3))
            else:
                # Show "Empty" text
                empty_surf = self.font_small.render("Empty", True, (100, 100, 100))
                screen.blit(empty_surf, (slot_x + 5, hotbar_y + 45))


def draw_skill_management_screen_fullscreen(game: "Game") -> None:
    """Full-screen skill management view."""
    screen = game.screen
    ui_font = game.ui_font
    w, h = screen.get_size()
    
    # Draw gradient background
    from ui.screen_components import draw_gradient_background
    from ui.screen_constants import COLOR_GRADIENT_START, COLOR_GRADIENT_END
    draw_gradient_background(
        screen,
        0, 0, w, h,
        COLOR_GRADIENT_START,
        COLOR_GRADIENT_END,
        vertical=True
    )
    
    # Get available screens for tabs
    available_screens = ["inventory", "character", "skills", "skill_management", "quests"]
    if safe_getattr(game, "show_shop", False):
        available_screens.append("shop")
    
    # Draw header with tabs
    draw_screen_header(screen, ui_font, "Skill Management", "skill_management", available_screens, w)
    
    # Get skill management screen instance
    skill_mgmt_screen = getattr(game, "skill_management_screen", None)
    if skill_mgmt_screen is None:
        # Initialize if needed
        skill_mgmt_screen = SkillManagementScreen(game)
        game.skill_management_screen = skill_mgmt_screen
    
    # Draw content
    skill_mgmt_screen.draw_content(screen, w, h)
    
    # Footer hints
    hints = [
        "Click skill to select, then click slot to assign | Click loadout to switch | Q/E: switch character",
        "TAB: switch screen | T/ESC: close"
    ]
    draw_screen_footer(screen, ui_font, hints, w, h)

