"""
Skill screen module for skill allocation UI.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

# screen_constants are imported by screen_components
from ui.screen_components import draw_screen_header, draw_screen_footer
from ui.screen_utils import safe_getattr

if TYPE_CHECKING:
    from engine.core.game import Game


def draw_skill_screen_fullscreen(game: "Game") -> None:
    """Full-screen skill allocation view."""
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
    
    # Draw header with tabs
    draw_screen_header(screen, ui_font, "Skill Allocation", "skills", available_screens, w)
    
    # Get skill screen core instance
    skill_screen_core = getattr(game, "skill_screen", None)
    if skill_screen_core is None:
        # Fallback if skill screen core doesn't exist
        error_text = ui_font.render("Skill screen not initialized.", True, (200, 150, 150))
        screen.blit(error_text, (w // 2 - error_text.get_width() // 2, h // 2))
        return
    
    # Draw skill screen content
    skill_screen_core.draw_content(screen, w, h)
    
    # Footer hints (dynamic based on current tab)
    skill_screen_core = getattr(game, "skill_screen", None)
    if skill_screen_core and getattr(skill_screen_core, "current_tab", "tree") == "management":
        hints = [
            "Click skill to select, then click slot to assign | Q/E: switch character | X on slot: clear",
            "1/2: switch tab | TAB: switch screen | T/ESC: close"
        ]
    else:
        hints = [
            "Arrow Keys/WASD: pan | +/-: zoom | Click/Enter: select/upgrade | Q/E: switch character",
            "1/2: switch tab | TAB: switch screen | T/ESC: close"
        ]
    draw_screen_footer(screen, ui_font, hints, w, h)

