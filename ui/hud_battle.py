from __future__ import annotations

from typing import List
import pygame

from systems.input import InputAction
from ui.hud_utils import _draw_bar, _draw_status_indicators


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
) -> None:
    """
    Draw a battle unit card showing name, HP, resources, and status indicators.
    Used for party and enemy panels in battle.
    """
    if statuses is None:
        statuses = []
    
    card_h = 70
    card_surf = pygame.Surface((width, card_h), pygame.SRCALPHA)
    
    # Background color based on side and active state
    if is_active:
        bg_color = (40, 50, 60, 200) if is_player else (60, 40, 40, 200)
        border_color = (100, 150, 255) if is_player else (255, 100, 100)
    else:
        bg_color = (20, 20, 30, 180) if is_player else (30, 20, 20, 180)
        border_color = (80, 100, 120) if is_player else (120, 80, 80)
    
    card_surf.fill(bg_color)
    pygame.draw.rect(card_surf, border_color, (0, 0, width, card_h), 2)
    surface.blit(card_surf, (x, y))
    
    text_x = x + 6
    text_y = y + 4
    
    # Name
    name_color = (240, 240, 240) if is_active else (200, 200, 200)
    name_surf = font.render(name, True, name_color)
    surface.blit(name_surf, (text_x, text_y))
    text_y += 18
    
    # HP bar
    hp_ratio = hp / max_hp if max_hp > 0 else 0.0
    hp_color = (200, 80, 80) if hp > 0 else (100, 50, 50)
    hp_label = font.render(f"HP {hp}/{max_hp}", True, (220, 220, 220))
    surface.blit(hp_label, (text_x, text_y))
    text_y += 16
    _draw_bar(surface, text_x, text_y, width - 12, 8, hp_ratio, (60, 30, 30), hp_color, (255, 255, 255))
    text_y += 12
    
    # Resources (stamina/mana) - compact
    if max_stamina > 0 or max_mana > 0:
        res_parts = []
        if max_stamina > 0:
            res_parts.append(f"STA {current_stamina}/{max_stamina}")
        if max_mana > 0:
            res_parts.append(f"MP {current_mana}/{max_mana}")
        res_text = font.render(" | ".join(res_parts), True, (180, 200, 220))
        surface.blit(res_text, (text_x, text_y))
        text_y += 16
    
    # Status indicators (right side)
    icon_x = x + width - 20
    icon_y = y + 4
    _draw_status_indicators(surface, font, icon_x, icon_y, statuses=statuses, icon_spacing=14)


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
    slot_width = 100
    slot_height = 60
    slot_spacing = 8
    hotbar_w = len(skill_slots) * (slot_width + slot_spacing) - slot_spacing
    
    # Background panel
    panel_h = slot_height + 20
    panel_surf = pygame.Surface((hotbar_w + 20, panel_h), pygame.SRCALPHA)
    panel_surf.fill((0, 0, 0, 180))
    surface.blit(panel_surf, (x - 10, y - 10))
    
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
            
            bg_color = (40, 50, 40) if can_use else (30, 30, 30)
        else:
            bg_color = (20, 20, 20)
            can_use = False
        
        pygame.draw.rect(surface, bg_color, slot_rect)
        pygame.draw.rect(surface, (100, 100, 120), slot_rect, 2)
        
        if skill:
            # Skill name (truncated if too long)
            skill_name = getattr(skill, "name", skill_id)
            if len(skill_name) > 10:
                skill_name = skill_name[:8] + ".."
            name_surf = font.render(skill_name, True, (220, 220, 220) if can_use else (120, 120, 120))
            surface.blit(name_surf, (slot_x + 4, y + 4))
            
            # Key binding
            if key_label:
                key_surf = font.render(key_label, True, (200, 200, 255))
                surface.blit(key_surf, (slot_x + slot_width - key_surf.get_width() - 4, y + 4))
            
            # Cooldown
            if cooldown > 0:
                cd_surf = font.render(f"CD: {cooldown}", True, (255, 150, 150))
                surface.blit(cd_surf, (slot_x + 4, y + 20))
            
            # Resource costs
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
                cost_surf = font.render(cost_text, True, final_color)
                surface.blit(cost_surf, (slot_x + 4, y + 36))
        else:
            # Empty slot
            if key_label:
                key_surf = font.render(key_label, True, (100, 100, 100))
                surface.blit(key_surf, (slot_x + slot_width - key_surf.get_width() - 4, y + 4))
            empty_surf = font.render("Empty", True, (80, 80, 80))
            surface.blit(empty_surf, (slot_x + 4, y + 20))
        
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

