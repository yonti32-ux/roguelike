"""
UI scaling utilities for responsive UI that adapts to screen size.
"""

from typing import Tuple


# Base resolution that UI is designed for (windowed mode default)
BASE_WIDTH = 1280
BASE_HEIGHT = 720


def get_ui_scale(screen_width: int, screen_height: int) -> float:
    """
    Calculate UI scale factor based on screen size.
    
    Uses a logarithmic approach to prevent UI from becoming too large at high resolutions.
    Returns a scale factor (1.0 = base size, 1.5 = 50% larger, etc.)
    """
    import math
    
    scale_x = screen_width / BASE_WIDTH
    scale_y = screen_height / BASE_HEIGHT
    
    # Use the smaller scale to ensure UI fits on screen
    # This prevents UI from going off-screen on wide or tall displays
    linear_scale = min(scale_x, scale_y)
    
    # Use square root scaling for high resolutions to prevent UI from becoming too large
    # This makes UI scale more conservatively at 4K and above
    # At 2x resolution (2560x1440), scale = sqrt(2) ≈ 1.41
    # At 3x resolution (3840x2160), scale = sqrt(3) ≈ 1.73
    # At 4x resolution, scale = sqrt(4) = 2.0
    if linear_scale > 1.0:
        # For resolutions larger than base, use square root scaling
        scale = 1.0 + (math.sqrt(linear_scale) - 1.0) * 0.7  # 0.7 factor to make it even more conservative
    else:
        # For resolutions smaller than base, use linear scaling
        scale = linear_scale
    
    # Clamp to reasonable bounds (0.5x to 2.0x)
    scale = max(0.5, min(2.0, scale))
    
    return scale


def scale_font_size(base_size: int, scale: float) -> int:
    """Scale a font size by the UI scale factor."""
    return max(8, int(base_size * scale))


def scale_value(value: int, scale: float) -> int:
    """Scale a pixel value (padding, spacing, etc.) by the UI scale factor."""
    return max(1, int(value * scale))


def get_scaled_font(font_name: str, base_size: int, scale: float) -> "pygame.font.Font":
    """Get a scaled font."""
    import pygame
    scaled_size = scale_font_size(base_size, scale)
    return pygame.font.SysFont(font_name, scaled_size)


def get_hud_panel_width(screen_width: int, scale: float) -> int:
    """Get the width for HUD panels, scaled appropriately."""
    base_width = 320
    return scale_value(base_width, scale)


def get_hud_panel_padding(scale: float) -> int:
    """Get padding for HUD panels."""
    base_padding = 10
    return scale_value(base_padding, scale)


def get_hud_spacing(scale: float) -> int:
    """Get spacing between HUD elements."""
    base_spacing = 8
    return scale_value(base_spacing, scale)

