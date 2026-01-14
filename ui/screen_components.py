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
    MARGIN_X,
    MARGIN_Y_TOP,
    MARGIN_Y_FOOTER,
    LINE_HEIGHT_SMALL,
    LINE_HEIGHT_MEDIUM,
    LINE_HEIGHT_TITLE,
    TAB_SPACING,
    TAB_X_OFFSET,
    MAX_DESC_LENGTH,
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
    Render a category header (e.g., "--- Weapon ---").
    
    Returns:
        Y position after the header
    """
    slot_display = slot.capitalize()
    if slot == "misc":
        slot_display = "Miscellaneous"
    category_surf = ui_font.render(f"--- {slot_display} ---", True, COLOR_CATEGORY)
    screen.blit(category_surf, (x, y))
    return y + LINE_HEIGHT_MEDIUM


def draw_equipment_section(
    screen: pygame.Surface,
    ui_font: pygame.font.Font,
    x: int,
    y: int,
    equipped_map: dict,
    indent: int = 0,
) -> int:
    """
    Draw equipment section showing weapon, armor, trinket.
    
    Returns:
        Y position after the section
    """
    from systems.inventory import get_item_def
    from ui.screen_constants import COLOR_SUBTITLE, COLOR_TEXT, LINE_HEIGHT_TITLE, LINE_HEIGHT_MEDIUM
    
    equipped_title = ui_font.render("Equipped:", True, COLOR_SUBTITLE)
    screen.blit(equipped_title, (x, y))
    y += LINE_HEIGHT_TITLE
    
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
        else:
            line = f"{slot.capitalize()}: {item_def.name}"
        t = ui_font.render(line, True, COLOR_TEXT)
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
    """Draw header with title and tab indicators."""
    # Title
    title_surf = ui_font.render(title, True, COLOR_TITLE)
    screen.blit(title_surf, (MARGIN_X, MARGIN_Y_TOP))
    
    # Tab indicators (aligned near the top-right).
    tab_x = w - TAB_X_OFFSET
    tab_y = MARGIN_Y_TOP
    
    for i, screen_name in enumerate(available_screens):
        is_current = screen_name == current_screen
        tab_text = screen_name.capitalize()
        if is_current:
            tab_color = COLOR_TAB_ACTIVE
            # Draw underline
            tab_surf = ui_font.render(tab_text, True, tab_color)
            screen.blit(tab_surf, (tab_x + i * TAB_SPACING, tab_y))
            pygame.draw.line(
                screen,
                tab_color,
                (tab_x + i * TAB_SPACING, tab_y + 22),
                (tab_x + i * TAB_SPACING + tab_surf.get_width(), tab_y + 22),
                2,
            )
        else:
            tab_color = COLOR_TAB_INACTIVE
            tab_surf = ui_font.render(tab_text, True, tab_color)
            screen.blit(tab_surf, (tab_x + i * TAB_SPACING, tab_y))


def draw_screen_footer(
    screen: pygame.Surface,
    ui_font: pygame.font.Font,
    hints: List[str],
    w: int,
    h: int,
) -> None:
    """Draw footer with navigation hints."""
    footer_y = h - MARGIN_Y_FOOTER
    for i, hint in enumerate(hints):
        hint_surf = ui_font.render(hint, True, COLOR_FOOTER)
        screen.blit(hint_surf, (MARGIN_X, footer_y + i * LINE_HEIGHT_SMALL))

