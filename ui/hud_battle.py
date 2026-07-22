from __future__ import annotations

from typing import List
import pygame

from systems.input import InputAction
from ui.hud_utils import _draw_bar, _draw_status_indicators, _calculate_hp_color
from ui.status_display import draw_enhanced_status_indicators
from ui.ui_scaling import scale_value


def _draw_battle_unit_card(
    surface: pygame.Surface,
    font: pygame.font.Font,
    x: int,
    y: int,
    width: int,
    name: str,
    hp: int,
    max_hp: int,
    current_stamina: int = 0,
    max_stamina: int = 0,
    current_mana: int = 0,
    max_mana: int = 0,
    is_active: bool = False,
    is_player: bool = True,
    statuses: List = None,
    *,
    scale: float = 1.0,
    unit_id: Optional[str] = None,
    status_tracker: Optional[dict] = None,
) -> None:
    """
    Draw a battle unit card showing name, HP, resources, and status indicators.
    Used for party and enemy panels in battle.
    """
    if statuses is None:
        statuses = []

    # Scaled dimensions
    card_h = scale_value(78, scale)
    padding_x = scale_value(8, scale)
    padding_y = scale_value(6, scale)
    portrait_size = scale_value(46, scale)
    bar_height = scale_value(10, scale)

    card_surf = pygame.Surface((width, card_h), pygame.SRCALPHA)

    # Background color based on side and active state
    if is_active:
        bg_color = (42, 52, 68, 220) if is_player else (68, 42, 42, 220)
        border_color = (110, 170, 255) if is_player else (255, 120, 120)
    else:
        bg_color = (18, 20, 30, 190) if is_player else (30, 18, 18, 190)
        border_color = (80, 100, 130) if is_player else (140, 90, 90)

    card_surf.fill(bg_color)
    pygame.draw.rect(card_surf, border_color, (0, 0, width, card_h), 2)
    surface.blit(card_surf, (x, y))

    # --- Portrait placeholder (left) ---
    portrait_x = x + padding_x
    portrait_y = y + padding_y
    portrait_rect = pygame.Rect(portrait_x, portrait_y, portrait_size, portrait_size)
    # Slightly inset background so future portrait art has a frame
    pygame.draw.rect(surface, (10, 10, 16), portrait_rect)
    pygame.draw.rect(surface, border_color, portrait_rect, 2)

    # --- Text + bars column (right of portrait) ---
    text_x = portrait_rect.right + padding_x
    text_y = y + padding_y
    usable_width = max(40, x + width - padding_x - text_x)

    # Name (slightly brighter when active)
    name_color = (245, 245, 245) if is_active else (210, 210, 210)
    name_surf = font.render(name, True, name_color)
    surface.blit(name_surf, (text_x, text_y))
    text_y += scale_value(20, scale)

    # HP label + bar
    hp_ratio = hp / max_hp if max_hp > 0 else 0.0
    if hp > 0:
        hp_color = _calculate_hp_color(hp_ratio)
    else:
        hp_color = (110, 60, 60)  # Dark red when dead
    hp_label = font.render(f"HP {hp}/{max_hp}", True, (225, 225, 225))
    surface.blit(hp_label, (text_x, text_y))
    text_y += scale_value(14, scale)
    _draw_bar(
        surface,
        text_x,
        text_y,
        usable_width,
        bar_height,
        hp_ratio,
        (60, 30, 30),
        hp_color,
        (255, 255, 255),
    )
    text_y += bar_height + scale_value(4, scale)

    # Resources (stamina / mana) - compact, but with clearer color coding
    if max_stamina > 0 or max_mana > 0:
        res_parts = []
        if max_stamina > 0:
            res_parts.append(f"STA {current_stamina}/{max_stamina}")
        if max_mana > 0:
            res_parts.append(f"MP {current_mana}/{max_mana}")
        res_text = font.render(" | ".join(res_parts), True, (180, 210, 235))
        surface.blit(res_text, (text_x, text_y))

    # Status indicators (right side, vertically stacked) - enhanced display
    icon_x = x + width - padding_x - scale_value(14, scale)
    icon_y = y + padding_y
    if statuses:
        # Track status icon positions for tooltip if tracker provided
        return_icon_rects = (status_tracker is not None and unit_id is not None)
        _, _, icon_rects = draw_enhanced_status_indicators(
            surface,
            font,
            icon_x,
            icon_y,
            statuses,
            icon_spacing=scale_value(14, scale),
            vertical=True,
            show_timers=True,
            show_stacks=True,
            max_statuses=None,  # Show all statuses
            return_icon_rects=return_icon_rects,
        )
        
        # Store status icon rects for hover detection if tracker provided
        if return_icon_rects and icon_rects and status_tracker is not None:
            # Clear old status rects for this unit
            from systems.statuses import StatusEffect
            status_icon_rects = status_tracker.get("status_icon_rects", {})
            status_objects = status_tracker.get("status_objects", {})
            
            keys_to_remove = [k for k in status_icon_rects.keys() if k[0] == unit_id]
            for key in keys_to_remove:
                if key in status_icon_rects:
                    del status_icon_rects[key]
                if key in status_objects:
                    del status_objects[key]
            
            # Store new status icon rects and objects
            for status, icon_rect in icon_rects:
                if isinstance(status, StatusEffect):
                    status_name = getattr(status, "name", getattr(status, "status_id", "unknown"))
                    key = (unit_id, status_name)
                    status_icon_rects[key] = icon_rect
                    status_objects[key] = status


def _draw_battle_skill_hotbar(
    surface: pygame.Surface,
    font: pygame.font.Font,
    x: int,
    y: int,
    skills: List,
    skill_slots: List[str],
    cooldowns: dict,
    current_stamina: int,
    max_stamina: int,
    current_mana: int,
    max_mana: int,
    input_manager=None,
) -> None:
    """
    Draw a visible skill hotbar showing skill slots with key bindings,
    cooldowns, and resource costs.
    """
    # Increased size for better visibility
    slot_width = 140
    slot_height = 85
    slot_spacing = 12
    hotbar_w = len(skill_slots) * (slot_width + slot_spacing) - slot_spacing
    
    # Larger, more prominent background panel with border
    panel_h = slot_height + 30
    panel_w = hotbar_w + 40
    panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    # Dark background with stronger opacity
    panel_surf.fill((10, 10, 20, 240))
    # Bright border to make it stand out
    pygame.draw.rect(panel_surf, (100, 150, 255, 255), (0, 0, panel_w, panel_h), width=3)
    surface.blit(panel_surf, (x - 20, y - 15))
    
    slot_x = x
    slot_actions = [
        "SKILL_1",
        "SKILL_2", 
        "SKILL_3",
        "SKILL_4",
    ]
    
    for idx, skill_id in enumerate(skill_slots[:4]):
        if idx >= len(slot_actions):
            break
        
        # Get skill
        skill = skills.get(skill_id) if skill_id else None
        
        # Get key binding
        key_label = ""
        if input_manager is not None:
            try:
                action_map = {
                    0: InputAction.SKILL_1,
                    1: InputAction.SKILL_2,
                    2: InputAction.SKILL_3,
                    3: InputAction.SKILL_4,
                }
                if idx in action_map:
                    bound_keys = input_manager.get_bindings(action_map[idx])
                    if bound_keys:
                        key_label = pygame.key.name(list(bound_keys)[0]).upper()
            except (AttributeError, KeyError, TypeError):
                pass
        
        # Draw slot background
        slot_rect = pygame.Rect(slot_x, y, slot_width, slot_height)
        if skill:
            # Check if available (cooldown, resources)
            cooldown = cooldowns.get(skill_id, 0)
            can_use = cooldown == 0
            
            # Check resource costs
            stamina_cost = getattr(skill, "stamina_cost", 0)
            mana_cost = getattr(skill, "mana_cost", 0)
            has_resources = (stamina_cost <= current_stamina and mana_cost <= current_mana)
            can_use = can_use and has_resources
            
            # More vibrant colors for better visibility
            if can_use:
                bg_color = (50, 70, 50)
                border_color = (100, 200, 100)
            else:
                bg_color = (40, 40, 40)
                border_color = (80, 80, 80)
        else:
            bg_color = (25, 25, 25)
            border_color = (60, 60, 60)
            can_use = False
        
        pygame.draw.rect(surface, bg_color, slot_rect)
        pygame.draw.rect(surface, border_color, slot_rect, 3)
        
        if skill:
            # Skill name (truncated if too long) - larger font
            skill_name = getattr(skill, "name", skill_id)
            if len(skill_name) > 12:
                skill_name = skill_name[:10] + ".."
            # Use a slightly larger font for skill names
            name_font = pygame.font.Font(None, int(font.get_height() * 1.1))
            name_surf = name_font.render(skill_name, True, (240, 240, 240) if can_use else (140, 140, 140))
            surface.blit(name_surf, (slot_x + 6, y + 6))
            
            # Key binding - larger and more prominent
            if key_label:
                key_font = pygame.font.Font(None, int(font.get_height() * 1.2))
                key_surf = key_font.render(key_label, True, (150, 200, 255))
                # Draw key binding with background
                key_bg = pygame.Rect(slot_x + slot_width - key_surf.get_width() - 10, y + 6, key_surf.get_width() + 8, key_surf.get_height() + 4)
                pygame.draw.rect(surface, (30, 50, 80), key_bg)
                pygame.draw.rect(surface, (100, 150, 200), key_bg, 2)
                surface.blit(key_surf, (slot_x + slot_width - key_surf.get_width() - 6, y + 8))
            
            # Cooldown - larger text
            if cooldown > 0:
                cd_font = pygame.font.Font(None, int(font.get_height() * 1.1))
                cd_surf = cd_font.render(f"CD: {cooldown}", True, (255, 150, 150))
                surface.blit(cd_surf, (slot_x + 6, y + 28))
            
            # Resource costs - larger and clearer
            cost_parts = []
            cost_colors = []
            if stamina_cost > 0:
                sta_color = (150, 255, 150) if stamina_cost <= current_stamina else (255, 150, 150)
                cost_parts.append(f"STA:{stamina_cost}")
                cost_colors.append(sta_color)
            if mana_cost > 0:
                mp_color = (150, 200, 255) if mana_cost <= current_mana else (255, 150, 150)
                cost_parts.append(f"MP:{mana_cost}")
                cost_colors.append(mp_color)
            
            if cost_parts:
                cost_text = " ".join(cost_parts)
                # Use first cost color, or default if none
                final_color = cost_colors[0] if cost_colors else (200, 200, 200)
                cost_font = pygame.font.Font(None, int(font.get_height() * 1.0))
                cost_surf = cost_font.render(cost_text, True, final_color)
                surface.blit(cost_surf, (slot_x + 6, y + 50))
        else:
            # Empty slot
            if key_label:
                key_font = pygame.font.Font(None, int(font.get_height() * 1.2))
                key_surf = key_font.render(key_label, True, (100, 100, 100))
                surface.blit(key_surf, (slot_x + slot_width - key_surf.get_width() - 6, y + 6))
            empty_font = pygame.font.Font(None, int(font.get_height() * 1.0))
            empty_surf = empty_font.render("Empty", True, (100, 100, 100))
            surface.blit(empty_surf, (slot_x + 6, y + 30))
        
        slot_x += slot_width + slot_spacing


def _draw_battle_log_line(
    surface: pygame.Surface,
    font: pygame.font.Font,
    x: int,
    y: int,
    message: str,
) -> None:
    """
    Draw a single combat log line with color coding based on message content.
    """
    # Determine color based on message content
    msg_lower = message.lower()
    if any(word in msg_lower for word in ["damage", "hit", "attack", "strike"]):
        color = (255, 180, 180)  # Red for damage
    elif any(word in msg_lower for word in ["heal", "restore", "recover"]):
        color = (180, 255, 180)  # Green for healing
    elif any(word in msg_lower for word in ["skill", "ability", "cast"]):
        color = (180, 200, 255)  # Blue for skills
    elif any(word in msg_lower for word in ["defeat", "kill", "destroy"]):
        color = (255, 200, 100)  # Orange for kills
    elif any(word in msg_lower for word in ["victory", "win"]):
        color = (120, 255, 120)  # Bright green for victory
    elif any(word in msg_lower for word in ["defeat", "death", "died"]):
        color = (255, 100, 100)  # Bright red for defeat
    else:
        color = (200, 200, 200)  # Default gray
    
    log_surf = font.render(message, True, color)
    surface.blit(log_surf, (x, y))

