"""
Reusable UI helper functions for creating modular, customizable screens.

This module provides common UI patterns that can be reused across different screens
to maintain consistency and make screens easier to customize and extend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Tuple, Optional, Dict, Any
import pygame

from ui.screen_constants import (
    COLOR_BG_PANEL,
    COLOR_BORDER_BRIGHT,
    COLOR_SHADOW,
    COLOR_SELECTED_BG_BRIGHT,
    COLOR_TITLE,
    COLOR_SUBTITLE,
    COLOR_TEXT,
    COLOR_TEXT_DIM,
    SHADOW_OFFSET_X,
    SHADOW_OFFSET_Y,
)

if TYPE_CHECKING:
    pass


def draw_panel(
    screen: pygame.Surface,
    x: int,
    y: int,
    width: int,
    height: int,
    bg_color: Tuple[int, int, int, int] = COLOR_BG_PANEL,
    border_color: Tuple[int, int, int] = COLOR_BORDER_BRIGHT,
    border_width: int = 2,
    shadow: bool = True,
) -> pygame.Surface:
    """
    Draw a reusable panel with optional shadow.
    
    Returns:
        The panel surface (for potential caching)
    """
    panel_surf = pygame.Surface((width, height), pygame.SRCALPHA)
    panel_surf.fill(bg_color)
    pygame.draw.rect(panel_surf, border_color, (0, 0, width, height), border_width)
    
    if shadow:
        shadow_surf = pygame.Surface((width + 4, height + 4), pygame.SRCALPHA)
        shadow_surf.fill((0, 0, 0, 100))
        screen.blit(shadow_surf, (x - 2, y - 2))
    
    screen.blit(panel_surf, (x, y))
    return panel_surf


def draw_text_with_shadow(
    screen: pygame.Surface,
    font: pygame.font.Font,
    text: str,
    x: int,
    y: int,
    color: Tuple[int, int, int] = COLOR_TITLE,
    shadow_color: Tuple[int, int, int] = COLOR_SHADOW[:3],
) -> pygame.Rect:
    """
    Draw text with shadow for better readability.
    
    Returns:
        The bounding rect of the text
    """
    shadow_surf = font.render(text, True, shadow_color)
    screen.blit(shadow_surf, (x + SHADOW_OFFSET_X, y + SHADOW_OFFSET_Y))
    
    text_surf = font.render(text, True, color)
    screen.blit(text_surf, (x, y))
    
    return text_surf.get_rect(topleft=(x, y))


def draw_selection_highlight(
    screen: pygame.Surface,
    x: int,
    y: int,
    width: int,
    height: int,
    accent_width: int = 4,
) -> None:
    """
    Draw a selection highlight with accent border.
    Reusable pattern for selected items.
    """
    highlight_surf = pygame.Surface((width, height), pygame.SRCALPHA)
    highlight_surf.fill(COLOR_SELECTED_BG_BRIGHT)
    screen.blit(highlight_surf, (x, y))
    
    # Left accent border
    pygame.draw.rect(screen, COLOR_TITLE, (x, y, accent_width, height))


def draw_hint_panel(
    screen: pygame.Surface,
    font: pygame.font.Font,
    text: str,
    center_x: int,
    y: int,
) -> None:
    """
    Draw a standardized hint panel at the bottom of screens.
    """
    hint_surf = font.render(text, True, COLOR_TEXT_DIM)
    hint_panel_width = hint_surf.get_width() + 40
    hint_panel_height = 35
    
    hint_panel_x = center_x - hint_panel_width // 2
    
    hint_panel = pygame.Surface((hint_panel_width, hint_panel_height), pygame.SRCALPHA)
    hint_panel.fill((0, 0, 0, 150))
    pygame.draw.rect(hint_panel, COLOR_BORDER_BRIGHT, (0, 0, hint_panel_width, hint_panel_height), 1)
    screen.blit(hint_panel, (hint_panel_x, y))
    screen.blit(hint_surf, (hint_panel_x + 20, y + 8))


def calculate_grid_layout(
    num_items: int,
    items_per_row: int,
    item_width: int,
    item_height: int,
    spacing: int,
    screen_width: int,
) -> Tuple[int, int, int, int]:
    """
    Calculate grid layout for items (cards, buttons, etc.).
    
    Returns:
        (start_x, start_y, num_rows, total_height)
    """
    num_rows = (num_items + items_per_row - 1) // items_per_row
    
    total_width = items_per_row * item_width + (items_per_row - 1) * spacing
    total_height = num_rows * item_height + (num_rows - 1) * spacing
    
    start_x = (screen_width - total_width) // 2
    start_y = 120  # Default start position
    
    return start_x, start_y, num_rows, total_height

