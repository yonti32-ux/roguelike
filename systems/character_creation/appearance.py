# systems/appearance.py

"""Appearance customization data structures for characters."""

from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class AppearanceConfig:
    """
    Character appearance configuration.
    
    - sprite_id: Which sprite variant to use (default: class-based)
    - color_primary: Primary RGB color for customization (optional)
    - color_secondary: Secondary RGB color for customization (optional)
    - scale_factor: Sprite scale factor (default: 1.0)
    """
    sprite_id: str = "default"
    color_primary: Optional[Tuple[int, int, int]] = None  # RGB tuple
    color_secondary: Optional[Tuple[int, int, int]] = None  # RGB tuple
    scale_factor: float = 1.0

