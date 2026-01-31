"""
Recruitment screen module for hiring companions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List

import pygame

from ui.screen_components import draw_screen_header, draw_screen_footer
from ui.screen_utils import safe_getattr

if TYPE_CHECKING:
    from engine.core.game import Game
    from systems.party import CompanionState
    from systems.village.companion_generation import AvailableCompanion


def draw_recruitment_fullscreen(game: "Game") -> None:
    """Full-screen recruitment view for hiring companions."""
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
    
    # Get available screens for tabs (keep consistent across screens)
    available_screens = ["inventory", "character", "skills", "quests"]
    if safe_getattr(game, "show_shop", False):
        available_screens.append("shop")
    if safe_getattr(game, "show_recruitment", False):
        available_screens.append("recruitment")
    
    # Draw header with tabs
    draw_screen_header(screen, ui_font, "Companion Recruitment", "recruitment", available_screens, w)
    
    # Get available companions
    from systems.village.companion_generation import AvailableCompanion
    available_companions: List[AvailableCompanion] = getattr(game, "available_companions", [])
    
    # Get party info
    from systems.party import CompanionState
    party_list: List[CompanionState] = getattr(game, "party", None) or []
    current_party_size = 1 + len(party_list)  # Hero + companions
    max_party_size = 4
    
    # Gold display
    gold_value = int(getattr(getattr(game, "hero_stats", None), "gold", 0))
    gold_line = ui_font.render(f"Your gold: {gold_value}", True, (230, 210, 120))
    screen.blit(gold_line, (40, 70))
    
    # Party size indicator
    party_size_text = f"Party: {current_party_size}/{max_party_size}"
    party_color = (200, 200, 200) if current_party_size < max_party_size else (255, 150, 150)
    party_line = ui_font.render(party_size_text, True, party_color)
    screen.blit(party_line, (w - 250, 70))
    
    # Left column: Available companions list
    left_x = 40
    y = 110
    
    title = ui_font.render("Available Companions:", True, (220, 220, 180))
    screen.blit(title, (left_x, y))
    y += 28
    
    cursor = int(getattr(game, "recruitment_cursor", 0))
    
    if not available_companions:
        msg = ui_font.render("No companions are available for recruitment.", True, (190, 190, 190))
        screen.blit(msg, (left_x, y))
    else:
        max_companions = len(available_companions)
        line_height = 28
        if max_companions > 0:
            cursor = max(0, min(cursor, max_companions - 1))
        
        # Show companions
        visible_start = max(0, cursor - 8)
        visible_end = min(max_companions, cursor + 12)
        visible_companions = available_companions[visible_start:visible_end]
        
        for i, available_comp in enumerate(visible_companions):
            actual_index = visible_start + i
            comp_state = available_comp.companion_state
            comp_name = available_comp.generated_name
            cost = available_comp.recruitment_cost
            
            # Get class name
            class_name = "Unknown"
            if comp_state.class_id:
                try:
                    from systems.classes import get_class
                    class_def = get_class(comp_state.class_id)
                    class_name = class_def.name
                except Exception:
                    class_name = comp_state.class_id.title()
            
            # Build label
            label = f"{actual_index + 1}) {comp_name} - {class_name} (Lv {comp_state.level})"
            
            # Cost string
            cost_str = f"{cost}g"
            can_afford = gold_value >= cost
            cost_color = (230, 210, 120) if can_afford else (200, 150, 150)
            
            if actual_index == cursor:
                # Highlight selected companion
                bg = pygame.Surface((w // 2 - 80, line_height), pygame.SRCALPHA)
                bg.fill((60, 60, 90, 210))
                screen.blit(bg, (left_x, y - 2))
                label_color = (255, 255, 200)
            else:
                label_color = (230, 230, 230)
            
            label_surf = ui_font.render(label, True, label_color)
            screen.blit(label_surf, (left_x + 20, y))
            
            cost_surf = ui_font.render(cost_str, True, cost_color)
            screen.blit(cost_surf, (left_x + w // 2 - 200, y))
            
            y += line_height
        
        # Right column: detailed info for currently selected companion
        if 0 <= cursor < max_companions:
            info_x = w // 2 + 40
            info_y = 110
            
            selected_comp = available_companions[cursor]
            comp_state = selected_comp.companion_state
            
            info_title = ui_font.render("Companion Info:", True, (220, 220, 180))
            screen.blit(info_title, (info_x, info_y))
            info_y += 26
            
            # Name and class
            comp_name = selected_comp.generated_name
            class_name = "Unknown"
            if comp_state.class_id:
                try:
                    from systems.classes import get_class
                    class_def = get_class(comp_state.class_id)
                    class_name = class_def.name
                except Exception:
                    class_name = comp_state.class_id.title()
            
            name_line = f"{comp_name} - {class_name}"
            name_surf = ui_font.render(name_line, True, (235, 235, 220))
            screen.blit(name_surf, (info_x, info_y))
            info_y += 24
            
            # Level
            level_line = f"Level: {comp_state.level}"
            level_surf = ui_font.render(level_line, True, (200, 200, 200))
            screen.blit(level_surf, (info_x, info_y))
            info_y += 24
            
            # Stats
            stats_parts = [
                f"HP: {comp_state.max_hp}",
                f"ATK: {comp_state.attack_power}",
                f"DEF: {comp_state.defense}",
            ]
            if hasattr(comp_state, "max_stamina") and comp_state.max_stamina > 0:
                stats_parts.append(f"STA: {comp_state.max_stamina}")
            if hasattr(comp_state, "max_mana") and comp_state.max_mana > 0:
                stats_parts.append(f"MANA: {comp_state.max_mana}")
            
            stats_line = "  ".join(stats_parts)
            stats_surf = ui_font.render(stats_line, True, (190, 190, 190))
            screen.blit(stats_surf, (info_x, info_y))
            info_y += 24
            
            # Perks
            if comp_state.perks:
                perks_title = ui_font.render("Perks:", True, (220, 220, 180))
                screen.blit(perks_title, (info_x, info_y))
                info_y += 24
                
                from systems import perks as perk_system
                for perk_id in comp_state.perks:
                    try:
                        perk = perk_system.get(perk_id)
                        perk_line = f"  • {perk.name}"
                        perk_surf = ui_font.render(perk_line, True, (180, 200, 220))
                        screen.blit(perk_surf, (info_x, info_y))
                        info_y += 22
                    except Exception:
                        pass
            
            # Cost
            info_y += 10
            cost = selected_comp.recruitment_cost
            can_afford = gold_value >= cost
            cost_line = f"Recruitment Cost: {cost} gold"
            cost_color = (230, 210, 120) if can_afford else (255, 150, 150)
            cost_surf = ui_font.render(cost_line, True, cost_color)
            screen.blit(cost_surf, (info_x, info_y))
            info_y += 24
            
            if not can_afford:
                need_more = cost - gold_value
                need_line = f"(Need {need_more} more gold)"
                need_surf = ui_font.render(need_line, True, (255, 150, 150))
                screen.blit(need_surf, (info_x, info_y))
                info_y += 24
            
            # Backstory (if available)
            if selected_comp.backstory_snippet:
                info_y += 10
                backstory_title = ui_font.render("About:", True, (220, 220, 180))
                screen.blit(backstory_title, (info_x, info_y))
                info_y += 24
                backstory_surf = ui_font.render(selected_comp.backstory_snippet, True, (180, 180, 180))
                screen.blit(backstory_surf, (info_x, info_y))
    
    # Footer hints
    hints = [
        "Up/Down: move • Enter/Space: recruit • 1–9: quick recruit",
        "TAB: switch screen • I/C: jump to screen • ESC: close"
    ]
    draw_screen_footer(screen, ui_font, hints, w, h)

