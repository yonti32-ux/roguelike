"""
Enhanced status display system.

Provides better visual representation of status effects with:
- Duration timers
- Stack counts
- Better icons/symbols
- Buff/debuff color coding
- Support for all status types
"""

from typing import List, Optional, Dict, Tuple
import pygame
from systems.statuses import StatusEffect

# Forward reference for TooltipData
if False:  # TYPE_CHECKING equivalent
    from ui.tooltip import TooltipData


# Status type definitions for better display
# Using ASCII-safe symbols that work reliably across fonts
STATUS_DEFINITIONS: Dict[str, Dict[str, any]] = {
    # Buffs (positive effects)
    "guard": {
        "icon": "[",
        "color": (180, 220, 255),  # Light blue
        "is_buff": True,
        "description": "50% damage reduction",
    },
    "regenerating": {
        "icon": "+",
        "color": (150, 255, 150),  # Light green
        "is_buff": True,
        "description": "Heals over time",
    },
    "counter_stance": {
        "icon": "<",
        "color": (255, 255, 180),  # Light yellow
        "is_buff": True,
        "description": "Counters next attack",
    },
    "empowered": {
        "icon": "^",
        "color": (255, 220, 100),  # Golden yellow
        "is_buff": True,
        "description": "30% increased damage output",
    },
    
    # Debuffs (negative effects)
    "weakened": {
        "icon": "v",
        "color": (255, 200, 100),  # Orange
        "is_buff": False,
        "description": "30% reduced damage output",
    },
    "stunned": {
        "icon": "!",
        "color": (255, 100, 100),  # Red
        "is_buff": False,
        "description": "Cannot act",
    },
    
    # DoT effects (damage over time)
    "poisoned": {
        "icon": "P",
        "color": (150, 255, 100),  # Green (poison green)
        "is_buff": False,
        "description": "Takes poison damage each turn",
    },
    "bleeding": {
        "icon": "B",
        "color": (255, 100, 100),  # Red
        "is_buff": False,
        "description": "Takes bleed damage each turn",
    },
    "burning": {
        "icon": "*",
        "color": (255, 150, 50),  # Orange-red
        "is_buff": False,
        "description": "Takes fire damage each turn",
    },
    "diseased": {
        "icon": "D",
        "color": (150, 200, 100),  # Sickly green
        "is_buff": False,
        "description": "Takes stacking disease damage",
    },
    
    # Movement/utility effects
    "chilled": {
        "icon": "~",
        "color": (150, 200, 255),  # Light blue
        "is_buff": False,
        "description": "Reduced movement",
    },
    # Additional status types (for future expansion)
    "haste": {
        "icon": ">>",
        "color": (150, 255, 200),  # Light green
        "is_buff": True,
        "description": "Increased movement",
    },
    "slow": {
        "icon": "<<",
        "color": (200, 150, 255),  # Purple
        "is_buff": False,
        "description": "Reduced movement speed",
    },
    "vulnerable": {
        "icon": "V",
        "color": (255, 150, 100),  # Orange-red
        "is_buff": False,
        "description": "Takes increased damage",
    },
    "protected": {
        "icon": "(",
        "color": (150, 220, 255),  # Light blue
        "is_buff": True,
        "description": "Reduced incoming damage",
    },
    "exposed": {
        "icon": "X",
        "color": (255, 120, 120),  # Red
        "is_buff": False,
        "description": "Cannot guard or defend",
    },
    "warded": {
        "icon": ")",
        "color": (200, 255, 200),  # Light green
        "is_buff": True,
        "description": "Immune to debuffs",
    },
}


def get_status_display_info(status: StatusEffect) -> Dict[str, any]:
    """
    Get display information for a status effect.
    
    Returns a dict with icon, color, and description, with defaults for unknown statuses.
    """
    status_name = getattr(status, "name", "")
    default_info = {
        "icon": "•",
        "color": (200, 200, 200),
        "is_buff": False,
        "description": status_name,
    }
    
    return STATUS_DEFINITIONS.get(status_name, default_info)


def draw_enhanced_status_indicators(
    surface: pygame.Surface,
    font: pygame.font.Font,
    x: int,
    y: int,
    statuses: List[StatusEffect],
    *,
    icon_size: int = 16,
    icon_spacing: int = 20,
    show_timers: bool = True,
    show_stacks: bool = True,
    vertical: bool = True,
    max_statuses: Optional[int] = None,
    return_icon_rects: bool = False,
) -> Tuple[int, int, Optional[List[Tuple[StatusEffect, pygame.Rect]]]]:
    """
    Draw enhanced status indicators with timers and stack counts.
    
    Args:
        surface: Surface to draw on
        font: Font to use for text
        x, y: Starting position
        statuses: List of StatusEffect objects
        icon_size: Size of status icons (default 16)
        icon_spacing: Spacing between icons (default 20)
        show_timers: Whether to show duration timers (default True)
        show_stacks: Whether to show stack counts (default True)
        vertical: If True, stack vertically (default True)
        max_statuses: Maximum number of statuses to show (None = all)
        return_icon_rects: If True, also return list of (status, rect) tuples for hover detection
    
    Returns:
        Tuple of (final_x, final_y) position after drawing, and optionally list of (status, rect) tuples
    """
    if not statuses:
        return x, y, ([] if return_icon_rects else None)
    
    # Limit number of statuses if specified
    display_statuses = statuses[:max_statuses] if max_statuses else statuses
    
    # Sort statuses: buffs first, then debuffs
    buffs = []
    debuffs = []
    for status in display_statuses:
        info = get_status_display_info(status)
        if info["is_buff"]:
            buffs.append((status, info))
        else:
            debuffs.append((status, info))
    
    # If negative spacing (upward stacking), we need to reverse the order
    # and start from the bottom
    is_upward = vertical and icon_spacing < 0
    all_statuses = buffs + debuffs
    if is_upward:
        all_statuses = all_statuses[::-1]  # Reverse for upward stacking
    
    # Draw all statuses
    current_x, current_y = x, y
    icon_rects = [] if return_icon_rects else None
    
    for status, info in all_statuses:
        result = _draw_single_status(
            surface, font, current_x, current_y, status, info,
            icon_size, show_timers, show_stacks, icon_spacing, vertical,
            return_rect=return_icon_rects
        )
        
        if return_icon_rects:
            current_x, current_y, icon_rect = result
            if icon_rect:
                icon_rects.append((status, icon_rect))
        else:
            current_x, current_y = result
    
    return current_x, current_y, icon_rects


def _draw_single_status(
    surface: pygame.Surface,
    font: pygame.font.Font,
    x: int,
    y: int,
    status: StatusEffect,
    info: Dict[str, any],
    icon_size: int,
    show_timers: bool,
    show_stacks: bool,
    icon_spacing: int,
    vertical: bool,
    return_rect: bool = False,
) -> Tuple[int, int, Optional[pygame.Rect]]:
    """
    Draw a single status indicator.
    
    Returns:
        Tuple of (next_x, next_y) for next status position, and optionally the icon rect
    """
    # Get status properties
    duration = getattr(status, "duration", 0)
    stacks = getattr(status, "stacks", 1)
    icon_text = info["icon"]
    color = info["color"]
    
    # Draw status icon/symbol
    # For Unicode symbols, we'll use text rendering
    # Create a small surface for the status indicator
    icon_surf = font.render(icon_text, True, color)
    surface.blit(icon_surf, (x, y))
    
    # Calculate icon rect for hover detection (include timer area if shown)
    icon_rect = None
    if return_rect:
        icon_w = icon_surf.get_width()
        icon_h = icon_surf.get_height()
        # Expand rect to include timer if shown
        if show_timers and duration > 0:
            timer_text = str(duration)
            timer_surf = font.render(timer_text, True, (180, 180, 180))
            if vertical:
                # Timer is to the right, so expand width
                icon_w = icon_w + timer_surf.get_width() + 4  # Add padding
            else:
                icon_w = icon_w + timer_surf.get_width() + 4
        # Make hover area a bit larger for easier clicking (add padding)
        icon_rect = pygame.Rect(x - 2, y - 2, icon_w + 4, max(icon_h, icon_size) + 4)
    
    # Draw duration timer (small number below or to the right)
    next_x = x
    next_y = y
    
    if show_timers and duration > 0:
        timer_text = str(duration)
        # Use a slightly smaller, dimmer color for timers
        timer_surf = font.render(timer_text, True, (180, 180, 180))
        
        if vertical:
            # Timer to the right of icon (better visibility)
            timer_x = x + icon_surf.get_width() + 2
            timer_y = y + 2  # Slight vertical offset to align with icon center
            surface.blit(timer_surf, (timer_x, timer_y))
            next_y = y + icon_spacing
        else:
            # Timer to the right of icon for horizontal layout
            timer_x = x + icon_surf.get_width() + 2
            surface.blit(timer_surf, (timer_x, y))
            next_x = x + icon_spacing + timer_surf.get_width() + 2
    else:
        # No timer, just advance position
        if vertical:
            next_y = y + icon_spacing
        else:
            next_x = x + icon_spacing
    
    # Draw stack count (if stacks > 1)
    if show_stacks and stacks > 1:
        stack_text = f"×{stacks}"
        # Use a smaller offset for stack count (super/subscript style)
        stack_surf = font.render(stack_text, True, (255, 255, 100))
        
        if vertical:
            stack_x = x + icon_surf.get_width() - 4
            stack_y = y - 2
        else:
            stack_x = x + icon_surf.get_width() - 6
            stack_y = y + icon_surf.get_height() - 8
        
        surface.blit(stack_surf, (stack_x, stack_y))
    
    if return_rect:
        return next_x, next_y, icon_rect
    else:
        return next_x, next_y


def get_status_tooltip(status: StatusEffect) -> str:
    """
    Generate a tooltip description for a status effect.
    
    Args:
        status: StatusEffect object
    
    Returns:
        Tooltip text describing the status
    """
    info = get_status_display_info(status)
    name = getattr(status, "name", "Unknown")
    duration = getattr(status, "duration", 0)
    stacks = getattr(status, "stacks", 1)
    dot_damage = getattr(status, "flat_damage_each_turn", 0)
    
    # Format status name
    lines = [f"{name.title()}"]
    
    # Add description
    if info["description"]:
        lines.append(info["description"])
    
    # Add duration
    if duration > 0:
        lines.append(f"Duration: {duration} turns")
    
    # Add stacks
    if stacks > 1:
        lines.append(f"Stacks: {stacks}")
    
    # Add DOT damage
    if dot_damage > 0:
        total_damage = dot_damage * stacks if stacks > 1 else dot_damage
        lines.append(f"Deals {total_damage} damage/turn")
    
    # Add multiplier info
    outgoing = getattr(status, "outgoing_mult", 1.0)
    incoming = getattr(status, "incoming_mult", 1.0)
    
    if outgoing != 1.0:
        pct = int((outgoing - 1.0) * 100)
        sign = "+" if pct > 0 else ""
        lines.append(f"Damage output: {sign}{pct}%")
    
    if incoming != 1.0:
        pct = int((1.0 - incoming) * 100)
        lines.append(f"Damage reduction: {pct}%")
    
    return "\n".join(lines)


def create_status_tooltip_data(status: StatusEffect) -> "TooltipData":
    """
    Create TooltipData object for a status effect (compatible with ui.tooltip.TooltipData).
    
    Args:
        status: StatusEffect object
    
    Returns:
        TooltipData object for rendering
    """
    from ui.tooltip import TooltipData
    
    info = get_status_display_info(status)
    name = getattr(status, "name", "Unknown")
    duration = getattr(status, "duration", 0)
    stacks = getattr(status, "stacks", 1)
    dot_damage = getattr(status, "flat_damage_each_turn", 0)
    outgoing = getattr(status, "outgoing_mult", 1.0)
    incoming = getattr(status, "incoming_mult", 1.0)
    is_stunned = getattr(status, "stunned", False)
    
    # Format title
    title = name.title()
    
    # Build description lines
    lines: List[str] = []
    
    if info["description"]:
        lines.append(info["description"])
    
    # Add effect details
    if is_stunned:
        lines.append("Cannot take actions")
    elif dot_damage > 0:
        total_damage = dot_damage * stacks if stacks > 1 else dot_damage
        lines.append(f"Deals {total_damage} damage per turn")
    
    # Add duration info
    if duration > 0:
        lines.append(f"Lasts {duration} turn{'s' if duration != 1 else ''}")
    
    # Add stack info
    if stacks > 1:
        lines.append(f"{stacks} stacks")
    
    # Build stats dict
    stats: Dict[str, float] = {}
    
    if outgoing != 1.0:
        pct = (outgoing - 1.0) * 100
        stats["Damage Output"] = pct
    
    if incoming != 1.0:
        pct = (1.0 - incoming) * 100
        stats["Damage Reduction"] = pct
    
    return TooltipData(
        title=title,
        lines=lines,
        stats=stats if stats else None,
    )

