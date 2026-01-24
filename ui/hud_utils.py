from __future__ import annotations

from typing import List, Optional
import pygame


def _calculate_hp_color(hp_fraction: float) -> tuple[int, int, int]:
    """
    Calculate HP bar color based on HP percentage.
    
    Args:
        hp_fraction: HP percentage (0.0 to 1.0)
    
    Returns:
        RGB color tuple (red, green, blue)
        - Green (100, 255, 100) at 100% HP
        - Yellow (255, 255, 100) at 50% HP
        - Red (255, 100, 100) at 0% HP
    """
    hp_fraction = max(0.0, min(1.0, hp_fraction))
    
    if hp_fraction > 0.5:
        # Green to Yellow (100% to 50%)
        # At 100%: green (100, 255, 100)
        # At 50%: yellow (255, 255, 100)
        # Interpolate between these
        t = (hp_fraction - 0.5) * 2.0  # Maps 0.5-1.0 to 0.0-1.0
        r = int(100 + (255 - 100) * (1 - t))
        g = 255
        b = int(100 + (100 - 100) * (1 - t))
    else:
        # Yellow to Red (50% to 0%)
        # At 50%: yellow (255, 255, 100)
        # At 0%: red (255, 100, 100)
        # Interpolate between these
        t = hp_fraction * 2.0  # Maps 0.0-0.5 to 0.0-1.0
        r = 255
        g = int(255 + (100 - 255) * (1 - t))
        b = int(100 + (100 - 100) * (1 - t))
    
    return (r, g, b)


def _draw_bar(
    surface: pygame.Surface,
    x: int,
    y: int,
    width: int,
    height: int,
    fraction: float,
    back_color: tuple[int, int, int],
    fill_color: tuple[int, int, int],
    border_color: tuple[int, int, int] | None = (255, 255, 255),
) -> None:
    """
    Utility: draw a simple filled bar (e.g. HP / XP / stamina / mana).
    """
    fraction = max(0.0, min(1.0, float(fraction)))
    pygame.draw.rect(surface, back_color, (x, y, width, height))
    if fraction > 0.0:
        fill_w = int(width * fraction)
        pygame.draw.rect(surface, fill_color, (x, y, fill_w, height))
    if border_color is not None and width > 2 and height > 2:
        pygame.draw.rect(surface, border_color, (x, y, width, height), 1)


def _draw_resource_bar_with_label(
    surface: pygame.Surface,
    font: pygame.font.Font,
    x: int,
    y: int,
    width: int,
    bar_height: int,
    label: str,
    current: int,
    maximum: int,
    text_color: tuple[int, int, int],
    back_color: tuple[int, int, int],
    fill_color: tuple[int, int, int],
    border_color: tuple[int, int, int] | None = (255, 255, 255),
) -> int:
    """
    Draw a resource bar with label text above it.
    Returns the y position after the bar (for chaining).
    """
    # Draw label
    label_surf = font.render(f"{label} {current}/{maximum}", True, text_color)
    surface.blit(label_surf, (x, y))
    y += 20  # Increased spacing to prevent overlap
    
    # Draw bar
    fraction = current / maximum if maximum > 0 else 0.0
    _draw_bar(surface, x, y, width, bar_height, fraction, back_color, fill_color, border_color)
    return y + bar_height + 6  # Increased spacing after bar


def _draw_status_indicators(
    surface: pygame.Surface,
    font: pygame.font.Font,
    x: int,
    y: int,
    *,
    statuses: List | None = None,
    has_guard: bool = False,
    has_weakened: bool = False,
    has_stunned: bool = False,
    has_dot: bool = False,
    icon_spacing: int = 18,
    vertical: bool = True,
) -> None:
    """
    Draw status indicator icons (G for guard, W for weakened, ! for stunned, • for DOT).
    
    Args:
        surface: Surface to draw on
        font: Font to use for text
        x, y: Starting position
        statuses: Optional list of status objects (will check status_id/name)
        has_guard, has_weakened, has_stunned, has_dot: Direct boolean flags
        icon_spacing: Pixels between icons
        vertical: If True, icons stack vertically (y increases), else horizontal (x increases)
    """
    if statuses is not None:
        # Extract status names from status objects
        for status in statuses[:4]:  # Limit to 4 status icons
            status_name = getattr(status, "status_id", getattr(status, "name", str(status)))
            if status_name == "guard":
                has_guard = True
            elif status_name == "weakened":
                has_weakened = True
            elif status_name == "stunned":
                has_stunned = True
            elif getattr(status, "flat_damage_each_turn", 0) > 0:
                has_dot = True
    
    current_x = x
    current_y = y
    
    if has_guard:
        g_text = font.render("G", True, (255, 255, 180))
        surface.blit(g_text, (current_x, current_y))
        if vertical:
            current_y += icon_spacing
        else:
            current_x += icon_spacing
    
    if has_weakened:
        w_text = font.render("W", True, (255, 200, 100))
        surface.blit(w_text, (current_x, current_y))
        if vertical:
            current_y += icon_spacing
        else:
            current_x += icon_spacing
    
    if has_dot:
        dot_text = font.render("•", True, (180, 255, 180))
        surface.blit(dot_text, (current_x, current_y))
        if vertical:
            current_y += icon_spacing
        else:
            current_x += icon_spacing
    
    if has_stunned:
        s_text = font.render("!", True, (255, 100, 100))
        surface.blit(s_text, (current_x, current_y))


def _draw_compact_unit_card(
    surface: pygame.Surface,
    font: pygame.font.Font,
    x: int,
    y: int,
    width: int,
    name: str,
    hp: int,
    max_hp: int,
    is_alive: bool = True,
) -> None:
    """
    Draw a compact unit card for party preview.
    Shows name and HP bar.
    """
    card_h = 28  # Smaller card
    card_surf = pygame.Surface((width, card_h), pygame.SRCALPHA)
    card_surf.fill((0, 0, 0, 120))  # More transparent
    surface.blit(card_surf, (x, y))
    
    # Name
    name_color = (220, 220, 220) if is_alive else (150, 150, 150)
    name_surf = font.render(name, True, name_color)
    surface.blit(name_surf, (x + 4, y + 2))
    
    # HP bar
    bar_x = x + 4
    bar_y = y + 16
    bar_w = width - 8
    bar_h = 7  # Smaller bar
    hp_ratio = hp / max_hp if max_hp > 0 else 0.0
    if is_alive:
        hp_color = _calculate_hp_color(hp_ratio)
    else:
        hp_color = (100, 50, 50)  # Gray when dead
    _draw_bar(surface, bar_x, bar_y, bar_w, bar_h, hp_ratio, (60, 30, 30), hp_color, (255, 255, 255))
    
    # HP text
    hp_text = font.render(f"{hp}/{max_hp}", True, (200, 200, 200))
    surface.blit(hp_text, (x + width - hp_text.get_width() - 4, y + 2))

