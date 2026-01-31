"""
Reusable UI components for fullscreen screens.

This module contains common rendering functions and utilities that can be
reused across different screen types (inventory, character sheet, shop, etc.).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Dict, Optional

import pygame

from ui.screen_constants import (
    COLOR_TITLE,
    COLOR_SUBTITLE,
    COLOR_TEXT,
    COLOR_TEXT_DIM,
    COLOR_TEXT_DIMMER,
    COLOR_CATEGORY,
    COLOR_GOLD,
    COLOR_TAB_ACTIVE,
    COLOR_TAB_INACTIVE,
    COLOR_FOOTER,
    COLOR_BG_PANEL,
    COLOR_BG_PANEL_DARK,
    COLOR_BORDER,
    COLOR_BORDER_BRIGHT,
    COLOR_SHADOW,
    COLOR_SHADOW_LIGHT,
    COLOR_SELECTED_BG_BRIGHT,
    COLOR_HOVER_BG,
    COLOR_GRADIENT_START,
    COLOR_GRADIENT_END,
    MARGIN_X,
    MARGIN_Y_TOP,
    MARGIN_Y_FOOTER,
    LINE_HEIGHT_SMALL,
    LINE_HEIGHT_MEDIUM,
    LINE_HEIGHT_TITLE,
    TAB_SPACING,
    TAB_X_OFFSET,
    MAX_DESC_LENGTH,
    SHADOW_OFFSET_X,
    SHADOW_OFFSET_Y,
    BORDER_WIDTH_MEDIUM,
    PANEL_PADDING,
    PANEL_SHADOW_SIZE,
)

if TYPE_CHECKING:
    from systems.inventory import ItemDef
    from systems import perks as perk_system


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class CharacterHeaderInfo:
    """Container for character header display data."""
    name: str
    class_name: str
    level: int
    xp: int
    xp_next: Optional[int]
    gold: Optional[int]  # None means don't show gold (companions)


@dataclass
class CharacterStats:
    """Container for character stats data."""
    hp: int
    max_hp: int
    attack: int
    defense: int
    skill_power: float
    max_stamina: int = 0
    current_stamina: int = 0
    max_mana: int = 0
    current_mana: int = 0


# ============================================================================
# Item Utility Functions
# ============================================================================

def build_item_stats_summary(stats: Dict[str, float]) -> str:
    """
    Build a compact one-line summary from an item's stats dict.

    Example: "ATK +2  DEF +1  HP +10"
    """
    if not stats:
        return ""

    # Preferred order for well-known stats
    preferred_order = [
        "attack",
        "defense",
        "max_hp",
        "hp",
        "max_stamina",
        "max_mana",
        "range",
        "crit_chance",
    ]

    def _label_for(key: str) -> str:
        mapping = {
            "attack": "ATK",
            "defense": "DEF",
            "max_hp": "HP",
            "hp": "HP",
            "max_stamina": "STA",
            "max_mana": "MANA",
            "range": "RNG",
            "crit_chance": "CRIT",
        }
        return mapping.get(key, key.upper())

    def _fmt_value(value: float) -> str:
        # Show integers without .0, small non-int values with one decimal.
        if isinstance(value, int) or value.is_integer():
            v = int(value)
        else:
            v = round(value, 1)
        sign = "+" if v >= 0 else ""
        return f"{sign}{v}"

    parts: List[str] = []

    # First render preferred keys in order
    for key in preferred_order:
        if key in stats:
            parts.append(f"{_label_for(key)} {_fmt_value(float(stats[key]))}")

    # Then add any remaining keys in alphabetical order
    remaining_keys = sorted(k for k in stats.keys() if k not in preferred_order)
    for key in remaining_keys:
        parts.append(f"{_label_for(key)} {_fmt_value(float(stats[key]))}")

    return "  ".join(parts)


def get_rarity_color(rarity: str) -> tuple[int, int, int]:
    """
    Get a display color for an item based on its rarity.
    
    Falls back to a neutral color if the rarity is unknown.
    """
    rarity_key = (rarity or "").lower()
    palette = {
        "common": (220, 220, 220),
        "uncommon": (140, 220, 140),   # soft green
        "rare": (140, 180, 255),       # soft blue
        "epic": (200, 150, 255),       # purple
        "legendary": (255, 200, 120),  # orange/gold
    }
    return palette.get(rarity_key, (220, 220, 220))


def build_item_info_line(item_def: "ItemDef", include_description: bool = False) -> str:
    """
    Build a single compact line for item info.

    By default this only returns a compact stats summary so we don't spam
    long descriptions in lists. If include_description is True, a short
    description snippet is appended after the stats.
    """
    stats_summary = build_item_stats_summary(getattr(item_def, "stats", {}) or {})
    if not include_description:
        return stats_summary

    desc = (getattr(item_def, "description", "") or "").strip()
    if not desc:
        return stats_summary

    # Keep descriptions short so the UI doesn't get bloated horizontally.
    if len(desc) > MAX_DESC_LENGTH:
        desc = desc[: MAX_DESC_LENGTH - 3] + "..."

    if stats_summary:
        return f"{stats_summary}  |  {desc}"
    return desc


# ============================================================================
# Rendering Functions
# ============================================================================

def render_category_header(
    screen: pygame.Surface,
    ui_font: pygame.font.Font,
    slot: str,
    x: int,
    y: int,
) -> int:
    """
    Render a category header with enhanced styling (e.g., "--- Weapon ---").
    
    Returns:
        Y position after the header
    """
    from ui.screen_constants import COLOR_BG_PANEL_DARK, COLOR_BORDER_DIM
    
    slot_display = slot.capitalize()
    if slot == "misc":
        slot_display = "Miscellaneous"
    
    # Render text first to get dimensions
    category_text = f"--- {slot_display} ---"
    category_surf = ui_font.render(category_text, True, COLOR_CATEGORY)
    text_width = category_surf.get_width()
    text_height = category_surf.get_height()
    
    # Create a subtle background panel for the category header
    panel_padding = 8
    panel_height = text_height + panel_padding * 2
    panel_width = text_width + panel_padding * 2
    
    # Draw subtle background panel
    panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
    panel.fill((*COLOR_BG_PANEL_DARK[:3], 180))
    pygame.draw.rect(panel, COLOR_BORDER_DIM, (0, 0, panel_width, panel_height), 1)
    screen.blit(panel, (x - panel_padding, y - panel_padding // 2))
    
    # Draw text with shadow
    text_shadow = ui_font.render(category_text, True, COLOR_SHADOW[:3])
    screen.blit(text_shadow, (x + SHADOW_OFFSET_X, y + SHADOW_OFFSET_Y))
    screen.blit(category_surf, (x, y))
    
    return y + LINE_HEIGHT_MEDIUM + 4  # Extra spacing after header


def draw_equipment_section(
    screen: pygame.Surface,
    ui_font: pygame.font.Font,
    x: int,
    y: int,
    equipped_map: dict,
    indent: int = 0,
) -> int:
    """
    Draw equipment section showing weapon, armor, trinket with enhanced styling.
    
    Returns:
        Y position after the section
    """
    from systems.inventory import get_item_def
    from ui.screen_constants import COLOR_SUBTITLE, COLOR_TEXT, COLOR_TEXT_DIMMER, LINE_HEIGHT_TITLE, LINE_HEIGHT_MEDIUM
    
    equipped_title = ui_font.render("Equipped:", True, COLOR_SUBTITLE)
    equipped_title_shadow = ui_font.render("Equipped:", True, COLOR_SHADOW[:3])
    screen.blit(equipped_title_shadow, (x + SHADOW_OFFSET_X, y + SHADOW_OFFSET_Y))
    screen.blit(equipped_title, (x, y))
    y += LINE_HEIGHT_TITLE + 4
    
    # Use all equipment slots from the inventory (new system has 9 slots)
    # Order them logically: weapon, then armor pieces, then accessories
    slot_order = ["weapon", "helmet", "armor", "gloves", "boots", "shield", "cloak", "ring", "amulet"]
    # Filter to only show slots that exist in equipped_map (or show all if equipped_map is None)
    if equipped_map is not None:
        slots = [slot for slot in slot_order if slot in equipped_map]
    else:
        slots = slot_order
    
    for slot in slots:
        item_def = None
        if equipped_map:
            item_id = equipped_map.get(slot)
            if item_id:
                item_def = get_item_def(item_id)
        
        if item_def is None:
            line = f"{slot.capitalize()}: (none)"
            text_color = COLOR_TEXT_DIMMER
        else:
            # Get rarity color for equipped items
            rarity = getattr(item_def, "rarity", "") or ""
            rarity_color = get_rarity_color(rarity)
            # Slightly brighten the color for equipped items
            text_color = tuple(min(255, c + 30) for c in rarity_color)
            line = f"{slot.capitalize()}: {item_def.name}"
        
        t = ui_font.render(line, True, text_color)
        screen.blit(t, (x + indent, y))
        y += LINE_HEIGHT_MEDIUM
    
    return y


def render_stats_section(
    screen: pygame.Surface,
    ui_font: pygame.font.Font,
    stats: CharacterStats,
    x: int,
    y: int,
) -> int:
    """
    Render stats section.
    
    Args:
        screen: Surface to render on
        ui_font: Font to use
        stats: CharacterStats to display
        x: X position
        y: Y position to start
    
    Returns:
        Y position after stats section
    """
    from ui.screen_constants import COLOR_SUBTITLE, COLOR_TEXT, LINE_HEIGHT_MEDIUM
    
    stats_title = ui_font.render("Stats:", True, COLOR_SUBTITLE)
    screen.blit(stats_title, (x, y))
    y += 26
    
    stats_lines = [
        f"HP: {stats.hp}/{stats.max_hp}",
        f"Attack: {stats.attack}",
        f"Defense: {stats.defense}",
    ]
    
    # Add resource pools if they exist
    if stats.max_stamina > 0:
        stats_lines.append(f"Stamina: {stats.current_stamina}/{stats.max_stamina}")
    if stats.max_mana > 0:
        stats_lines.append(f"Mana: {stats.current_mana}/{stats.max_mana}")
    
    if stats.skill_power != 1.0:
        stats_lines.append(f"Skill Power: {stats.skill_power:.2f}x")
    
    for line in stats_lines:
        t = ui_font.render(line, True, COLOR_TEXT)
        screen.blit(t, (x + 20, y))
        y += 24
    
    return y


def render_perks_section(
    screen: pygame.Surface,
    ui_font: pygame.font.Font,
    perk_ids: List[str],
    x: int,
    y: int,
    empty_message: str = "None yet. Level up to choose perks!",
) -> int:
    """
    Render a perks list section.
    
    Args:
        screen: Surface to render on
        ui_font: Font to use for rendering
        perk_ids: List of perk IDs to display
        x: X position to start rendering
        y: Y position to start rendering
        empty_message: Message to show when no perks
    
    Returns:
        Y position after the perks section
    """
    from systems import perks as perk_system
    from ui.screen_constants import COLOR_SUBTITLE, COLOR_TEXT_DIMMER
    
    perks_title = ui_font.render("Perks:", True, COLOR_SUBTITLE)
    screen.blit(perks_title, (x, y))
    y += 28
    
    if not perk_ids:
        no_perks = ui_font.render(empty_message, True, COLOR_TEXT_DIMMER)
        screen.blit(no_perks, (x, y))
        return y + 22  # Return position after empty message
    
    getter = getattr(perk_system, "get_perk", None)
    if not callable(getter):
        getter = getattr(perk_system, "get", None)
    
    for pid in perk_ids:
        perk_def = None
        if callable(getter):
            try:
                perk_def = getter(pid)
            except KeyError:
                perk_def = None
        
        if perk_def is None:
            pretty_name = pid.replace("_", " ").title()
            line = f"- {pretty_name}"
        else:
            branch = getattr(perk_def, "branch_name", None)
            if branch:
                line = f"- {branch}: {perk_def.name}"
            else:
                line = f"- {perk_def.name}"
        t = ui_font.render(line, True, (210, 210, 210))
        screen.blit(t, (x, y))
        y += 22
    
    return y


def render_character_header(
    screen: pygame.Surface,
    ui_font: pygame.font.Font,
    header_info: CharacterHeaderInfo,
    floor: int,
    x: int,
    y: int,
) -> int:
    """
    Render character header (name, level, XP, gold, floor).
    
    Args:
        screen: Surface to render on
        ui_font: Font to use
        header_info: Header data to display
        floor: Current floor number
        x: X position
        y: Y position to start
    
    Returns:
        Y position after the header
    """
    # Name and class
    name_line = ui_font.render(
        f"{header_info.name} ({header_info.class_name})",
        True,
        (230, 230, 230),
    )
    screen.blit(name_line, (x, y))
    y += 28
    
    # Floor
    floor_line = ui_font.render(f"Floor: {floor}", True, (200, 200, 200))
    screen.blit(floor_line, (x, y))
    y += 26
    
    # XP
    if header_info.xp_next is not None and header_info.xp_next > 0:
        xp_text_str = f"Level {header_info.level}  XP {header_info.xp}/{header_info.xp_next}"
    else:
        xp_text_str = f"Level {header_info.level}  XP {header_info.xp}"
    xp_line = ui_font.render(xp_text_str, True, (220, 220, 180))
    screen.blit(xp_line, (x, y))
    y += 26
    
    # Gold (only for hero)
    if header_info.gold is not None:
        gold_line = ui_font.render(f"Gold: {header_info.gold}", True, COLOR_GOLD)
        screen.blit(gold_line, (x, y))
        y += 30
    else:
        y += 4  # Small spacing if no gold line
    
    return y


def draw_screen_header(
    screen: pygame.Surface,
    ui_font: pygame.font.Font,
    title: str,
    current_screen: str,
    available_screens: List[str],
    w: int,
) -> None:
    """Draw enhanced header with title and tab indicators (with panel background)."""
    header_height = 50
    header_y = 0
    
    # Draw header panel background with shadow
    shadow_offset = 3
    shadow_panel = pygame.Surface((w, header_height + shadow_offset), pygame.SRCALPHA)
    shadow_panel.fill((0, 0, 0, 80))
    screen.blit(shadow_panel, (0, header_y + shadow_offset))
    
    header_panel = pygame.Surface((w, header_height), pygame.SRCALPHA)
    header_panel.fill((*COLOR_BG_PANEL[:3], 240))  # Slightly more opaque
    pygame.draw.rect(header_panel, COLOR_BORDER_BRIGHT, (0, 0, w, header_height), 2)
    # Bottom border line for separation
    pygame.draw.line(header_panel, COLOR_BORDER_BRIGHT, (0, header_height - 1), (w, header_height - 1), 1)
    screen.blit(header_panel, (0, header_y))
    
    # Title with shadow
    title_surf = ui_font.render(title, True, COLOR_TITLE)
    title_shadow = ui_font.render(title, True, COLOR_SHADOW[:3])
    title_x = MARGIN_X
    title_y = header_y + (header_height - title_surf.get_height()) // 2
    
    # Draw shadow
    screen.blit(title_shadow, (title_x + SHADOW_OFFSET_X, title_y + SHADOW_OFFSET_Y))
    # Draw title
    screen.blit(title_surf, (title_x, title_y))
    
    # Tab indicators (centered in header) with enhanced styling
    # Calculate total width of all tabs to center them
    tab_spacing = 15  # Spacing between tabs
    tab_padding = 8  # Padding inside each tab
    tab_texts = []
    tab_widths = []
    total_tabs_width = 0
    
    for screen_name in available_screens:
        tab_text = screen_name.capitalize()
        tab_texts.append(tab_text)
        tab_surf = ui_font.render(tab_text, True, COLOR_TAB_ACTIVE)
        tab_width = tab_surf.get_width() + tab_padding * 2
        tab_widths.append(tab_width)
        total_tabs_width += tab_width
    
    # Add spacing between tabs
    total_tabs_width += tab_spacing * (len(available_screens) - 1)
    
    # Start position to center tabs
    tab_start_x = (w - total_tabs_width) // 2
    tab_y = header_y + (header_height - title_surf.get_height()) // 2
    
    current_x = tab_start_x
    for i, screen_name in enumerate(available_screens):
        is_current = screen_name == current_screen
        tab_text = tab_texts[i]
        tab_width = tab_widths[i]
        
        if is_current:
            tab_color = COLOR_TAB_ACTIVE
            # Draw active tab with background highlight
            tab_surf = ui_font.render(tab_text, True, tab_color)
            tab_height = tab_surf.get_height() + 6
            tab_bg_x = current_x
            tab_bg_y = tab_y - 3
            
            # Tab background
            tab_bg = pygame.Surface((tab_width, tab_height), pygame.SRCALPHA)
            tab_bg.fill((*COLOR_SELECTED_BG_BRIGHT[:3], 180))
            pygame.draw.rect(tab_bg, COLOR_BORDER_BRIGHT, (0, 0, tab_width, tab_height), 1)
            screen.blit(tab_bg, (tab_bg_x, tab_bg_y))
            
            # Tab text with shadow (centered in tab)
            tab_text_x = current_x + (tab_width - tab_surf.get_width()) // 2
            tab_shadow = ui_font.render(tab_text, True, COLOR_SHADOW[:3])
            screen.blit(tab_shadow, (tab_text_x + SHADOW_OFFSET_X, tab_y + SHADOW_OFFSET_Y))
            screen.blit(tab_surf, (tab_text_x, tab_y))
        else:
            tab_color = COLOR_TAB_INACTIVE
            tab_surf = ui_font.render(tab_text, True, tab_color)
            # Center text in tab
            tab_text_x = current_x + (tab_width - tab_surf.get_width()) // 2
            screen.blit(tab_surf, (tab_text_x, tab_y))
        
        # Move to next tab position
        current_x += tab_width + tab_spacing


def draw_screen_footer(
    screen: pygame.Surface,
    ui_font: pygame.font.Font,
    hints: List[str],
    w: int,
    h: int,
) -> None:
    """Draw enhanced footer with navigation hints (with panel background)."""
    if not hints:
        return
    
    footer_height = len(hints) * LINE_HEIGHT_SMALL + 20
    footer_y = h - footer_height
    
    # Draw footer panel background with shadow
    shadow_offset = 3
    shadow_panel = pygame.Surface((w, footer_height + shadow_offset), pygame.SRCALPHA)
    shadow_panel.fill((0, 0, 0, 80))
    screen.blit(shadow_panel, (0, footer_y - shadow_offset))
    
    footer_panel = pygame.Surface((w, footer_height), pygame.SRCALPHA)
    footer_panel.fill((*COLOR_BG_PANEL[:3], 240))  # Slightly more opaque
    pygame.draw.rect(footer_panel, COLOR_BORDER_BRIGHT, (0, 0, w, footer_height), 2)
    # Top border line for separation
    pygame.draw.line(footer_panel, COLOR_BORDER_BRIGHT, (0, 0), (w, 0), 1)
    screen.blit(footer_panel, (0, footer_y))
    
    # Draw hints with shadow
    hint_start_y = footer_y + 10
    for i, hint in enumerate(hints):
        hint_surf = ui_font.render(hint, True, COLOR_FOOTER)
        hint_shadow = ui_font.render(hint, True, COLOR_SHADOW[:3])
        hint_x = MARGIN_X
        hint_y = hint_start_y + i * LINE_HEIGHT_SMALL
        
        # Draw shadow
        screen.blit(hint_shadow, (hint_x + SHADOW_OFFSET_X, hint_y + SHADOW_OFFSET_Y))
        # Draw hint
        screen.blit(hint_surf, (hint_x, hint_y))


# ============================================================================
# Enhanced Rendering Utilities
# ============================================================================

def render_text_with_shadow(
    screen: pygame.Surface,
    font: pygame.font.Font,
    text: str,
    color: tuple[int, int, int],
    x: int,
    y: int,
    shadow_color: tuple[int, int, int] = COLOR_SHADOW,
    shadow_offset: tuple[int, int] = (SHADOW_OFFSET_X, SHADOW_OFFSET_Y),
) -> pygame.Rect:
    """
    Render text with a shadow for better readability.
    
    Returns:
        The bounding rect of the text
    """
    # Render shadow
    shadow_surf = font.render(text, True, shadow_color)
    screen.blit(shadow_surf, (x + shadow_offset[0], y + shadow_offset[1]))
    
    # Render main text
    text_surf = font.render(text, True, color)
    screen.blit(text_surf, (x, y))
    
    return text_surf.get_rect(topleft=(x, y))


def draw_panel_with_shadow(
    screen: pygame.Surface,
    x: int,
    y: int,
    width: int,
    height: int,
    bg_color: tuple[int, int, int, int] = COLOR_BG_PANEL,
    border_color: tuple[int, int, int] = COLOR_BORDER,
    border_width: int = BORDER_WIDTH_MEDIUM,
    shadow_size: int = PANEL_SHADOW_SIZE,
) -> pygame.Surface:
    """
    Draw a panel with shadow and border.
    
    Returns:
        A surface containing the panel (for potential caching)
    """
    # Create panel surface
    panel_surf = pygame.Surface((width, height), pygame.SRCALPHA)
    
    # Draw shadow (multiple layers for soft shadow effect)
    shadow_alpha = COLOR_SHADOW[3] if len(COLOR_SHADOW) > 3 else 180
    for i in range(shadow_size, 0, -1):
        shadow_alpha_layer = shadow_alpha // (shadow_size + 1 - i)
        shadow_surf = pygame.Surface((width + i * 2, height + i * 2), pygame.SRCALPHA)
        shadow_surf.fill((0, 0, 0, shadow_alpha_layer))
        screen.blit(shadow_surf, (x - i + SHADOW_OFFSET_X, y - i + SHADOW_OFFSET_Y))
    
    # Draw background
    panel_surf.fill(bg_color)
    
    # Draw border
    if border_width > 0:
        pygame.draw.rect(panel_surf, border_color, (0, 0, width, height), border_width)
    
    # Blit panel to screen
    screen.blit(panel_surf, (x, y))
    
    return panel_surf


def draw_selection_indicator(
    screen: pygame.Surface,
    x: int,
    y: int,
    width: int,
    height: int,
    is_selected: bool = True,
    is_hovered: bool = False,
) -> None:
    """
    Draw a modern selection indicator (highlighted background with border).
    """
    if is_selected:
        # Draw selection background
        bg_color = COLOR_SELECTED_BG_BRIGHT if is_selected else COLOR_HOVER_BG
        selection_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        selection_surf.fill(bg_color)
        screen.blit(selection_surf, (x, y))
        
        # Draw left border accent
        accent_width = 4
        accent_color = COLOR_TAB_ACTIVE
        pygame.draw.rect(screen, accent_color, (x, y, accent_width, height))
        
        # Draw top/bottom borders for emphasis
        border_color = COLOR_BORDER_BRIGHT
        pygame.draw.line(screen, border_color, (x + accent_width, y), (x + width, y), 1)
        pygame.draw.line(screen, border_color, (x + accent_width, y + height - 1), (x + width, y + height - 1), 1)
    elif is_hovered:
        # Subtle hover effect
        hover_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        hover_surf.fill(COLOR_HOVER_BG)
        screen.blit(hover_surf, (x, y))


def draw_gradient_background(
    screen: pygame.Surface,
    x: int,
    y: int,
    width: int,
    height: int,
    start_color: tuple[int, int, int],
    end_color: tuple[int, int, int],
    vertical: bool = True,
) -> None:
    """
    Draw a gradient background (simulated with multiple rectangles).
    """
    steps = max(width, height) if vertical else max(width, height)
    for i in range(steps):
        ratio = i / steps if steps > 0 else 0
        r = int(start_color[0] + (end_color[0] - start_color[0]) * ratio)
        g = int(start_color[1] + (end_color[1] - start_color[1]) * ratio)
        b = int(start_color[2] + (end_color[2] - start_color[2]) * ratio)
        
        if vertical:
            pygame.draw.line(screen, (r, g, b), (x, y + i), (x + width, y + i), 1)
        else:
            pygame.draw.line(screen, (r, g, b), (x + i, y), (x + i, y + height), 1)

