from __future__ import annotations

from typing import TYPE_CHECKING, List, Dict, Any, Optional, Tuple
import pygame

from settings import COLOR_BG
from systems.inventory import get_item_def
from systems import perks as perk_system
from systems.party import CompanionDef, CompanionState, get_companion, ensure_companion_stats
from systems.economy import (
    calculate_shop_buy_price,
    calculate_shop_sell_price,
)
from ui.hud_utils import _draw_bar, _draw_resource_bar_with_label, _calculate_hp_color
from ui.status_display import draw_enhanced_status_indicators

if TYPE_CHECKING:
    from engine.core.game import Game
    from systems.inventory import Inventory, ItemDef


def _resolve_item_def(item_id: str, inventory: Optional["Inventory"] = None) -> Optional["ItemDef"]:
    """
    Resolve an item definition, checking for randomized items first.
    
    Args:
        item_id: Item ID to resolve
        inventory: Optional inventory instance to check for randomized items
    
    Returns:
        ItemDef if found, None otherwise
    """
    # If we have an inventory, use its method to resolve randomized items
    if inventory is not None and hasattr(inventory, "_get_item_def"):
        return inventory._get_item_def(item_id)
    
    # Fall back to base item definition
    return get_item_def(item_id)


def _build_item_stats_summary(stats: Dict[str, float]) -> str:
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


def _get_rarity_color(rarity: str) -> tuple[int, int, int]:
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


def _build_item_info_line(item_def: "ItemDef", include_description: bool = False) -> str:
    """
    Build a single compact line for item info.

    By default this only returns a compact stats summary so we don't spam
    long descriptions in lists. If include_description is True, a short
    description snippet is appended after the stats.
    """
    stats_summary = _build_item_stats_summary(getattr(item_def, "stats", {}) or {})
    if not include_description:
        return stats_summary

    desc = (getattr(item_def, "description", "") or "").strip()
    if not desc:
        return stats_summary

    # Keep descriptions short so the UI doesn't get bloated horizontally.
    max_desc_len = 80
    if len(desc) > max_desc_len:
        desc = desc[: max_desc_len - 3] + "..."

    if stats_summary:
        return f"{stats_summary}  |  {desc}"
    if stats_summary:
        return stats_summary
    return desc


def _resolve_focus_character(
    game: "Game",
    focus_index_attr: str,
    use_clamp: bool = False,
) -> tuple[bool, CompanionState | None, CompanionDef | None]:
    """
    Resolve which character is focused (hero or companion) based on focus index.
    
    Args:
        game: Game instance
        focus_index_attr: Attribute name for focus index (e.g., "inventory_focus_index")
        use_clamp: If True, use clamp logic (character sheet), else use modulo (inventory)
    
    Returns:
        Tuple of (is_hero, companion_state, companion_template)
    """
    party_list: List[CompanionState] = getattr(game, "party", None) or []
    total_slots = 1 + len(party_list)
    
    focus_index = int(getattr(game, focus_index_attr, 0))
    if total_slots <= 1:
        focus_index = 0
    else:
        if use_clamp:
            focus_index = max(0, min(focus_index, total_slots - 1))
        else:
            focus_index = focus_index % total_slots
    
    focused_is_hero = focus_index == 0
    focused_comp: CompanionState | None = None
    focused_template: CompanionDef | None = None
    
    if not focused_is_hero and party_list:
        comp_idx = focus_index - 1
        if 0 <= comp_idx < len(party_list):
            candidate = party_list[comp_idx]
            if isinstance(candidate, CompanionState):
                focused_comp = candidate
                template_id = getattr(candidate, "template_id", None)
                if template_id:
                    try:
                        focused_template = get_companion(template_id)
                    except KeyError:
                        focused_template = None
                    else:
                        if focused_template is not None:
                            try:
                                ensure_companion_stats(candidate, focused_template)
                            except Exception:
                                pass
    
    return focused_is_hero, focused_comp, focused_template


def _build_stats_line(
    game: "Game",
    is_hero: bool,
    comp: CompanionState | None = None,
    include_resources: bool = True,
) -> str:
    """
    Build a stats line string for display.
    
    Args:
        game: Game instance
        is_hero: True if hero, False if companion
        comp: Companion state (required if is_hero is False)
        include_resources: Whether to include stamina/mana
    
    Returns:
        Formatted stats string
    """
    stats_parts: List[str] = []
    
    if is_hero:
        hero_stats = getattr(game, "hero_stats", None)
        if hero_stats is not None:
            stats_parts.extend([
                f"HP {hero_stats.max_hp}",
                f"ATK {hero_stats.attack_power}",
                f"DEF {hero_stats.defense}",
            ])
            if include_resources:
                max_stamina = int(getattr(hero_stats, "max_stamina", 0))
                max_mana = int(getattr(hero_stats, "max_mana", 0))
                if max_stamina <= 0:
                    max_stamina = int(getattr(game.player, "max_stamina", 0))
                if max_mana <= 0:
                    max_mana = int(getattr(game.player, "max_mana", 0))
                if max_stamina > 0:
                    stats_parts.append(f"STA {max_stamina}")
                if max_mana > 0:
                    stats_parts.append(f"MANA {max_mana}")
    else:
        if comp is not None:
            stats_parts.extend([
                f"HP {comp.max_hp}",
                f"ATK {comp.attack_power}",
                f"DEF {comp.defense}",
            ])
            if include_resources:
                max_stamina = int(getattr(comp, "max_stamina", 0))
                max_mana = int(getattr(comp, "max_mana", 0))
                if max_stamina > 0:
                    stats_parts.append(f"STA {max_stamina}")
                if max_mana > 0:
                    stats_parts.append(f"MANA {max_mana}")
    
    return "  ".join(stats_parts)


def _get_character_display_info(
    game: "Game",
    is_hero: bool,
    comp: CompanionState | None = None,
    template: CompanionDef | None = None,
) -> tuple[str, dict]:
    """
    Get display name and equipped items map for a character.
    
    Returns:
        Tuple of (display_name, equipped_map)
    """
    if is_hero:
        hero_name = getattr(game.hero_stats, "hero_name", "Adventurer")
        display_name = hero_name
        inv = getattr(game, "inventory", None)
        equipped_map = inv.equipped if inv is not None else {}
    else:
        if comp is not None:
            display_name = getattr(comp, "name_override", None)
            if not display_name and template is not None:
                display_name = template.name
            if not display_name:
                display_name = "Companion"
            equipped_map = getattr(comp, "equipped", None) or {}
        else:
            display_name = "Companion"
            equipped_map = {}
    
    return display_name, equipped_map


def _get_all_equipped_items(game: "Game") -> dict[str, list[tuple[str, str]]]:
    """
    Get all equipped items from hero and all companions.
    
    Returns:
        Dict mapping item_id -> list of (character_name, slot) tuples
        Example: {"sword_1": [("Hero", "weapon"), ("Companion1", "weapon")]}
    """
    equipped_by: dict[str, list[tuple[str, str]]] = {}
    
    # Hero's equipped items
    inv = getattr(game, "inventory", None)
    if inv is not None:
        hero_name = getattr(game.hero_stats, "hero_name", "Hero")
        for slot, item_id in inv.equipped.items():
            if item_id:
                if item_id not in equipped_by:
                    equipped_by[item_id] = []
                equipped_by[item_id].append((hero_name, slot))
    
    # Companions' equipped items
    party_list: List[CompanionState] = getattr(game, "party", None) or []
    for comp in party_list:
        if not isinstance(comp, CompanionState):
            continue
        comp_equipped = getattr(comp, "equipped", None) or {}
        comp_name = getattr(comp, "name_override", None)
        if not comp_name:
            from systems.party import get_companion
            try:
                template_id = getattr(comp, "template_id", None)
                if template_id:
                    template = get_companion(template_id)
                    comp_name = getattr(template, "name", "Companion")
            except (KeyError, AttributeError):
                comp_name = "Companion"
        
        for slot, item_id in comp_equipped.items():
            if item_id:
                if item_id not in equipped_by:
                    equipped_by[item_id] = []
                equipped_by[item_id].append((comp_name, slot))
    
    return equipped_by


def _draw_equipment_section(
    screen: pygame.Surface,
    ui_font: pygame.font.Font,
    x: int,
    y: int,
    equipped_map: dict,
    indent: int = 0,
    inventory: Optional["Inventory"] = None,
) -> int:
    """
    Draw equipment section showing weapon, armor, trinket with enhanced visuals.
    
    Returns:
        Y position after the section
    """
    equipped_title = ui_font.render("Equipped:", True, (240, 240, 200))
    screen.blit(equipped_title, (x, y))
    y += 36
    
    slots = ["weapon", "armor", "trinket"]
    slot_icons = {"weapon": "⚔", "armor": "🛡", "trinket": "💍"}
    slot_colors = {
        "weapon": (255, 200, 150),
        "armor": (200, 220, 255),
        "trinket": (255, 220, 200),
    }
    
    for slot in slots:
        item_def = None
        if equipped_map:
            item_id = equipped_map.get(slot)
            if item_id:
                # Use inventory's method to resolve randomized items
                item_def = _resolve_item_def(item_id, inventory)
        
        # Draw slot background - wider to prevent overlap
        slot_bg = pygame.Surface((440, 32), pygame.SRCALPHA)
        if item_def:
            slot_bg.fill((40, 45, 50, 180))
        else:
            slot_bg.fill((30, 30, 35, 120))
        screen.blit(slot_bg, (x + indent - 4, y - 2))
        
        # Slot icon and name
        icon = slot_icons.get(slot, "•")
        slot_color = slot_colors.get(slot, (220, 220, 220))
        slot_label = f"{icon} {slot.capitalize()}:"
        slot_surf = ui_font.render(slot_label, True, slot_color)
        screen.blit(slot_surf, (x + indent, y))
        
        # Item name
        if item_def is None:
            item_text = "(none)"
            item_color = (120, 120, 120)
        else:
            item_text = item_def.name
            rarity = getattr(item_def, "rarity", "") or ""
            item_color = _get_rarity_color(rarity)
        
        item_x = x + indent + slot_surf.get_width() + 12
        item_surf = ui_font.render(item_text, True, item_color)
        screen.blit(item_surf, (item_x, y))
        y += 32
    
    return y


def _draw_screen_header(
    screen: pygame.Surface,
    ui_font: pygame.font.Font,
    title: str,
    current_screen: str,
    available_screens: List[str],
    w: int,
) -> None:
    """Draw header with title and enhanced tab indicators."""
    # Header background bar
    header_bg = pygame.Surface((w, 60), pygame.SRCALPHA)
    header_bg.fill((15, 20, 25, 240))
    screen.blit(header_bg, (0, 0))
    
    # Divider line
    pygame.draw.line(screen, (80, 100, 120), (0, 60), (w, 60), 2)
    
    # Title with subtle glow
    title_surf = ui_font.render(title, True, (255, 255, 220))
    # Subtle shadow
    title_shadow = ui_font.render(title, True, (0, 0, 0))
    screen.blit(title_shadow, (42, 32))
    screen.blit(title_surf, (40, 30))
    
    # Tab indicators with enhanced styling
    tab_x = w - 400
    tab_y = 30
    tab_spacing = 120
    
    for i, screen_name in enumerate(available_screens):
        is_current = screen_name == current_screen
        tab_text = screen_name.capitalize()
        if is_current:
            # Active tab with background
            tab_surf = ui_font.render(tab_text, True, (255, 255, 200))
            tab_bg = pygame.Surface((tab_surf.get_width() + 16, 28), pygame.SRCALPHA)
            tab_bg.fill((60, 80, 100, 220))
            screen.blit(tab_bg, (tab_x + i * tab_spacing - 8, tab_y - 2))
            screen.blit(tab_surf, (tab_x + i * tab_spacing, tab_y))
            # Bottom accent line
            pygame.draw.line(
                screen,
                (200, 240, 255),
                (tab_x + i * tab_spacing - 8, tab_y + 26),
                (tab_x + i * tab_spacing + tab_surf.get_width() + 8, tab_y + 26),
                3,
            )
        else:
            # Inactive tab
            tab_color = (140, 150, 160)
            tab_surf = ui_font.render(tab_text, True, tab_color)
            screen.blit(tab_surf, (tab_x + i * tab_spacing, tab_y))


def _draw_screen_footer(
    screen: pygame.Surface,
    ui_font: pygame.font.Font,
    hints: List[str],
    w: int,
    h: int,
) -> None:
    """Draw footer with navigation hints and enhanced styling."""
    footer_height = 50 + len(hints) * 22
    footer_y = h - footer_height
    
    # Footer background
    footer_bg = pygame.Surface((w, footer_height), pygame.SRCALPHA)
    footer_bg.fill((15, 20, 25, 240))
    screen.blit(footer_bg, (0, footer_y))
    
    # Top divider line
    pygame.draw.line(screen, (80, 100, 120), (0, footer_y), (w, footer_y), 2)
    
    # Hints with better styling
    hint_start_y = footer_y + 12
    for i, hint in enumerate(hints):
        hint_surf = ui_font.render(hint, True, (180, 200, 220))
        screen.blit(hint_surf, (40, hint_start_y + i * 22))


def _draw_panel(
    screen: pygame.Surface,
    x: int,
    y: int,
    width: int,
    height: int,
    border_color: tuple[int, int, int] = (100, 100, 100),
    bg_color: tuple[int, int, int] = (30, 30, 40),
    border_width: int = 2,
) -> None:
    """Draw a panel with background, border, and subtle shadow."""
    # Draw subtle shadow
    shadow_offset = 3
    shadow_surf = pygame.Surface((width, height), pygame.SRCALPHA)
    shadow_surf.fill((0, 0, 0, 80))
    screen.blit(shadow_surf, (x + shadow_offset, y + shadow_offset))
    
    # Draw background with slight gradient effect
    panel_surf = pygame.Surface((width, height), pygame.SRCALPHA)
    panel_surf.fill((*bg_color, 220))  # Slightly more opaque
    
    # Add subtle inner highlight at top
    highlight_surf = pygame.Surface((width, 2), pygame.SRCALPHA)
    highlight_surf.fill((255, 255, 255, 30))
    panel_surf.blit(highlight_surf, (0, 0))
    
    screen.blit(panel_surf, (x, y))
    
    # Draw border with inner and outer lines for depth
    pygame.draw.rect(screen, border_color, (x, y, width, height), border_width)
    # Inner border highlight
    inner_border = tuple(min(255, c + 40) for c in border_color)
    pygame.draw.rect(screen, inner_border, (x + 1, y + 1, width - 2, height - 2), 1)


def _draw_party_preview_panel(
    screen: pygame.Surface,
    ui_font: pygame.font.Font,
    w: int,
    start_y: int,
    focus_index: int,
    party_list: List[CompanionState],
    hero_name: str,
    class_str: str,
    level: int,
    hp: int,
    max_hp: int,
) -> None:
    """Draw the party preview panel on the right side."""
    right_x = w - 420  # Adjusted for wider panel
    party_panel_width = 380  # Increased from 340
    y = start_y
    
    num_party_members = 1 + len(party_list)
    # Calculate dynamic height: title (32) + padding (30) + entries (53 each: 45 height + 8 spacing)
    party_panel_height = 15 + 32 + (num_party_members * 53) + 15
    if num_party_members == 1 and len(party_list) == 0:
        party_panel_height += 20  # Extra space for "No companions yet" message
    
    _draw_panel(screen, right_x, y, party_panel_width, party_panel_height,
               border_color=(100, 100, 150), bg_color=(25, 25, 35))
    
    panel_padding = 15
    panel_y = y + panel_padding
    
    party_title = ui_font.render("Party", True, (220, 220, 255))
    screen.blit(party_title, (right_x + panel_padding, panel_y))
    panel_y += 32
    
    # Hero entry
    hero_selected = focus_index == 0
    hero_bg_color = (40, 45, 55) if hero_selected else (30, 30, 40)
    hero_border_color = (255, 255, 150) if hero_selected else (80, 80, 100)
    
    hero_entry_height = 45
    hero_entry = pygame.Surface((party_panel_width - 2 * panel_padding, hero_entry_height), pygame.SRCALPHA)
    hero_entry.fill((*hero_bg_color, 180))
    screen.blit(hero_entry, (right_x + panel_padding, panel_y))
    pygame.draw.rect(screen, hero_border_color, 
                    (right_x + panel_padding, panel_y, party_panel_width - 2 * panel_padding, hero_entry_height), 2)
    
    hero_name_color = (255, 255, 200) if hero_selected else (230, 230, 230)
    hero_name_text = f"★ {hero_name}"
    hero_name_surf = ui_font.render(hero_name_text, True, hero_name_color)
    screen.blit(hero_name_surf, (right_x + panel_padding + 5, panel_y + 3))
    
    hero_info_text = f"{class_str}  |  Lv {level}  |  HP {hp}/{max_hp}"
    hero_info_surf = ui_font.render(hero_info_text, True, (200, 200, 220))
    screen.blit(hero_info_surf, (right_x + panel_padding + 5, panel_y + 20))
    
    panel_y += hero_entry_height + 8
    
    # Companions
    if not party_list:
        no_comp_text = ui_font.render("No companions yet", True, (150, 150, 170))
        screen.blit(no_comp_text, (right_x + panel_padding, panel_y))
    else:
        for idx, comp in enumerate(party_list):
            template = None
            comp_level = None
            
            if isinstance(comp, CompanionState):
                template_id = getattr(comp, "template_id", None)
                comp_level = getattr(comp, "level", None)
                if template_id is not None:
                    try:
                        template = get_companion(template_id)
                    except KeyError:
                        template = None
                
                if template is not None:
                    try:
                        ensure_companion_stats(comp, template)
                    except Exception:
                        pass
                
                comp_max_hp = int(getattr(comp, "max_hp", 24))
                comp_hp = int(getattr(comp, "hp", comp_max_hp))
                comp_atk = int(getattr(comp, "attack_power", 5))
                comp_defense = int(getattr(comp, "defense", 0))
                
                if template is not None:
                    name = getattr(template, "name", "Companion")
                    role = getattr(template, "role", "Companion")
                else:
                    name = getattr(comp, "name_override", None) or "Companion"
                    role = "Companion"
            else:
                name = "Companion"
                role = "Companion"
                comp_max_hp = 24
                comp_hp = comp_max_hp
                comp_atk = 5
                comp_defense = 0
            
            is_selected = focus_index == idx + 1
            comp_bg_color = (40, 45, 55) if is_selected else (30, 30, 40)
            comp_border_color = (200, 200, 255) if is_selected else (80, 80, 100)
            
            comp_entry_height = 45
            comp_entry = pygame.Surface((party_panel_width - 2 * panel_padding, comp_entry_height), pygame.SRCALPHA)
            comp_entry.fill((*comp_bg_color, 180))
            screen.blit(comp_entry, (right_x + panel_padding, panel_y))
            pygame.draw.rect(screen, comp_border_color,
                            (right_x + panel_padding, panel_y, party_panel_width - 2 * panel_padding, comp_entry_height), 2)
            
            comp_name_color = (220, 240, 255) if is_selected else (210, 210, 230)
            lvl_prefix = f"Lv {comp_level} " if comp_level is not None else ""
            comp_name_text = f"◆ {lvl_prefix}{name}"
            comp_name_surf = ui_font.render(comp_name_text, True, comp_name_color)
            screen.blit(comp_name_surf, (right_x + panel_padding + 5, panel_y + 3))
            
            comp_info_text = f"{role}  |  HP {comp_hp}/{comp_max_hp}  |  ATK {comp_atk}  DEF {comp_defense}"
            comp_info_surf = ui_font.render(comp_info_text, True, (190, 200, 220))
            screen.blit(comp_info_surf, (right_x + panel_padding + 5, panel_y + 20))
            
            panel_y += comp_entry_height + 8


def draw_inventory_fullscreen(game: "Game") -> None:
    """Full-screen inventory view."""
    screen = game.screen
    ui_font = game.ui_font
    w, h = screen.get_size()
    
    # Fill background
    screen.fill(COLOR_BG)
    
    # Get available screens for tabs
    available_screens = ["inventory", "character", "skills"]
    if getattr(game, "show_shop", False):
        available_screens.append("shop")
    
    # Draw header with tabs
    _draw_screen_header(screen, ui_font, "Inventory", "inventory", available_screens, w)
    
    inv = getattr(game, "inventory", None)
    
    # Resolve focus character
    focused_is_hero, focused_comp, focused_template = _resolve_focus_character(
        game, "inventory_focus_index", use_clamp=False
    )
    
    # Get display info
    title_text, equipped_map = _get_character_display_info(
        game, focused_is_hero, focused_comp, focused_template
    )
    
    # Build stats line
    stats_line_text = _build_stats_line(game, focused_is_hero, focused_comp, include_resources=True)
    
    # Left column: Character info and equipment
    left_x = 40
    y = 90
    
    # Character info panel - made bigger
    char_panel_width = 520
    char_panel_height = 400
    _draw_panel(screen, left_x, y, char_panel_width, char_panel_height,
               border_color=(120, 120, 150), bg_color=(25, 25, 35))
    
    panel_padding = 20
    panel_y = y + panel_padding
    
    # Character name with enhanced styling
    char_title = ui_font.render(title_text, True, (255, 255, 220))
    screen.blit(char_title, (left_x + panel_padding, panel_y))
    panel_y += 36
    
    # Stats with better formatting and more spacing
    if stats_line_text:
        stats_surf = ui_font.render(stats_line_text, True, (200, 220, 240))
        screen.blit(stats_surf, (left_x + panel_padding, panel_y))
        panel_y += 36
    
    # Divider line with more spacing
    pygame.draw.line(screen, (80, 80, 100), 
                    (left_x + panel_padding, panel_y),
                    (left_x + char_panel_width - panel_padding, panel_y), 1)
    panel_y += 20
    
    # Equipped section
    panel_y = _draw_equipment_section(screen, ui_font, left_x + panel_padding, panel_y, 
                                     equipped_map, indent=0, inventory=inv)
    
    y = y + char_panel_height + 20
    
    # Right column: Backpack items - adjust position to account for larger left panel
    right_x = w // 2 + 80
    y = 90
    
    # Backpack panel
    backpack_panel_width = w - right_x - 40
    backpack_panel_height = h - y - 100
    _draw_panel(screen, right_x - 20, y - 20, backpack_panel_width, backpack_panel_height,
               border_color=(100, 120, 140), bg_color=(20, 25, 30))
    
    panel_padding = 20
    panel_y = y
    
    backpack_title = ui_font.render("Backpack", True, (240, 240, 200))
    screen.blit(backpack_title, (right_x, panel_y))
    panel_y += 36
    
    # Show filter/sort/search status with enhanced styling
    from ui.inventory_enhancements import FilterMode, SortMode
    filter_mode = getattr(game, "inventory_filter", FilterMode.ALL)
    sort_mode = getattr(game, "inventory_sort", SortMode.DEFAULT)
    search_query = getattr(game, "inventory_search", "") or ""
    
    status_lines = []
    if filter_mode != FilterMode.ALL:
        status_lines.append(f"Filter: {filter_mode.value}")
    if sort_mode != SortMode.DEFAULT:
        status_lines.append(f"Sort: {sort_mode.value}")
    if search_query:
        status_lines.append(f"Search: \"{search_query}\"")
    
    if status_lines:
        # Draw status badges
        badge_x = right_x
        for i, status_text in enumerate(status_lines):
            # Badge background
            badge_surf = ui_font.render(status_text, True, (255, 255, 255))
            badge_width = badge_surf.get_width() + 12
            badge_height = 22
            badge_bg = pygame.Surface((badge_width, badge_height), pygame.SRCALPHA)
            badge_bg.fill((60, 80, 100, 200))
            screen.blit(badge_bg, (badge_x, panel_y))
            # Badge text
            screen.blit(badge_surf, (badge_x + 6, panel_y + 2))
            badge_x += badge_width + 8
        panel_y += 32
    else:
        panel_y += 12
    
    y = panel_y
    
    if not inv or not getattr(inv, "items", None):
        none = ui_font.render("You are not carrying anything yet.", True, (180, 180, 180))
        screen.blit(none, (right_x, y))
    else:
        # Apply filtering, sorting, and search
        from ui.inventory_enhancements import filter_items, sort_items, search_items
        
        all_items = list(inv.items)
        all_equipped = _get_all_equipped_items(game)
        
        # Apply search first
        filtered_items = search_items(all_items, search_query, inv)
        
        # Apply filter
        filtered_items = filter_items(filtered_items, filter_mode, inv, all_equipped)
        
        # Apply sorting
        sorted_items = sort_items(filtered_items, sort_mode, inv)
        
        # Group items by slot/category (for display with category headers)
        items_by_slot: Dict[str, List[str]] = {}
        for item_id in sorted_items:
            item_def = _resolve_item_def(item_id, inv)
            if item_def is None:
                slot = "misc"
            else:
                slot = item_def.slot or "misc"
            if slot not in items_by_slot:
                items_by_slot[slot] = []
            items_by_slot[slot].append(item_id)
        
        # Build flat list with category markers: (item_id or None for category header, slot_name)
        flat_list: List[Tuple[Optional[str], str]] = []
        slot_order = ["weapon", "armor", "trinket", "consumable", "misc"]
        
        # If sorting is not default, don't show category headers
        show_categories = sort_mode == SortMode.DEFAULT
        
        if show_categories:
            for slot in slot_order:
                if slot in items_by_slot and items_by_slot[slot]:
                    flat_list.append((None, slot))  # Category header
                    for item_id in items_by_slot[slot]:
                        flat_list.append((item_id, slot))
            
            # Add any remaining slots not in the preferred order
            for slot in sorted(items_by_slot.keys()):
                if slot not in slot_order and items_by_slot[slot]:
                    flat_list.append((None, slot))  # Category header
                    for item_id in items_by_slot[slot]:
                        flat_list.append((item_id, slot))
        else:
            # No category headers when sorting
            for item_id in sorted_items:
                item_def = _resolve_item_def(item_id, inv)
                slot = item_def.slot if item_def else "misc"
                flat_list.append((item_id, slot))
        
        # Get cursor position
        cursor = int(getattr(game, "inventory_cursor", 0))
        
        # Find the actual item indices (skip category headers)
        item_indices = [i for i, (item_id, _) in enumerate(flat_list) if item_id is not None]
        if not item_indices:
            none = ui_font.render("You are not carrying anything yet.", True, (180, 180, 180))
            screen.blit(none, (right_x, y))
        else:
            # Clamp cursor to valid range
            cursor = max(0, min(cursor, len(item_indices) - 1))
            game.inventory_cursor = cursor
            
            # Get current item index in flat_list
            current_flat_index = item_indices[cursor]
            
            # Calculate scroll offset to keep cursor visible
            page_size = int(getattr(game, "inventory_page_size", 20))
            start_y = y
            line_height = 50  # Increased height per item (including stats line and spacing)
            max_visible_lines = (h - start_y - 100) // line_height  # Leave space for footer
            
            # Calculate which items to show (scroll to keep cursor visible)
            visible_start = max(0, cursor - max_visible_lines // 2)
            visible_end = min(len(item_indices), visible_start + max_visible_lines)
            
            # Get all equipped items from entire party (hero + companions)
            all_equipped = _get_all_equipped_items(game)
            
            # Build a map of flat_idx -> item_global_idx for quick lookup
            flat_to_global = {}
            for global_idx, flat_idx in enumerate(item_indices):
                flat_to_global[flat_idx] = global_idx
            
            # Track last shown category to avoid duplicate headers
            last_shown_category = None
            
            # Track item positions for hover detection
            item_positions: Dict[str, Tuple[int, int, int, int]] = {}  # item_id -> (x, y, width, height)
            
            # Display items with category headers
            for flat_idx, (item_id, slot) in enumerate(flat_list):
                if item_id is None:
                    # Category header - check if any items in this category are visible
                    category_has_visible = False
                    for check_idx in range(flat_idx + 1, len(flat_list)):
                        check_item_id, check_slot = flat_list[check_idx]
                        if check_item_id is None:  # Hit next category
                            break
                        if check_slot == slot and check_idx in flat_to_global:
                            item_global_idx = flat_to_global[check_idx]
                            if visible_start <= item_global_idx < visible_end:
                                category_has_visible = True
                                break
                    
                    if category_has_visible and last_shown_category != slot:
                        slot_display = slot.capitalize()
                        if slot == "misc":
                            slot_display = "Miscellaneous"
                        
                        # Enhanced category header with background
                        category_text = f"  {slot_display}"
                        category_surf = ui_font.render(category_text, True, (240, 240, 200))
                        category_bg_width = category_surf.get_width() + 20
                        category_bg = pygame.Surface((category_bg_width, 24), pygame.SRCALPHA)
                        category_bg.fill((50, 60, 70, 200))
                        screen.blit(category_bg, (right_x - 4, y - 2))
                        
                        # Divider line
                        pygame.draw.line(screen, (100, 120, 140),
                                       (right_x + category_bg_width, y + 10),
                                       (w - 40, y + 10), 1)
                        
                        screen.blit(category_surf, (right_x, y))
                        y += 36
                        last_shown_category = slot
                else:
                    # Check if this item should be visible
                    if flat_idx not in flat_to_global:
                        continue
                    
                    item_global_idx = flat_to_global[flat_idx]
                    
                    # Only show items in visible range
                    if visible_start <= item_global_idx < visible_end:
                        # Show category header if this is the first item in this category
                        if last_shown_category != slot:
                            slot_display = slot.capitalize()
                            if slot == "misc":
                                slot_display = "Miscellaneous"
                            
                            # Enhanced category header with background
                            category_text = f"  {slot_display}"
                            category_surf = ui_font.render(category_text, True, (240, 240, 200))
                            category_bg_width = category_surf.get_width() + 20
                            category_bg = pygame.Surface((category_bg_width, 24), pygame.SRCALPHA)
                            category_bg.fill((50, 60, 70, 200))
                            screen.blit(category_bg, (right_x - 4, y - 2))
                            
                            # Divider line
                            pygame.draw.line(screen, (100, 120, 140),
                                           (right_x + category_bg_width, y + 10),
                                           (w - 40, y + 10), 1)
                            
                            screen.blit(category_surf, (right_x, y))
                            y += 36
                            last_shown_category = slot
                        
                        item_def = _resolve_item_def(item_id, inv)
                        if item_def is None:
                            continue
                        
                        # Check if this is the selected item
                        is_selected = (item_global_idx == cursor)
                        
                        # Build equipped marker showing who has it equipped
                        equipped_marker = ""
                        if item_id in all_equipped:
                            markers = []
                            for char_name, slot_name in all_equipped[item_id]:
                                slot_abbrev = slot_name[0].upper()  # W, A, or T
                                # Shorten character names for display
                                if char_name == "Hero" or char_name.startswith("Hero"):
                                    char_abbrev = "H"
                                else:
                                    # Use first letter of companion name or "C" for Companion
                                    char_abbrev = char_name[0].upper() if char_name and char_name != "Companion" else "C"
                                markers.append(f"{slot_abbrev}-{char_abbrev}")
                            if markers:
                                equipped_marker = " [" + ",".join(markers) + "]"
                        
                        # Calculate item height for hover detection
                        item_start_y = y
                        item_height = 28  # Name line with spacing
                        
                        # One-line stats/description, slightly dimmer and indented.
                        # Show extra info (description) for the currently selected item.
                        info_line = _build_item_info_line(item_def, include_description=is_selected)
                        if info_line:
                            item_height += 24
                        else:
                            item_height += 12
                        
                        # Store item position for hover detection
                        item_rect_x = right_x - 10
                        item_rect_y = item_start_y - 4
                        item_rect_width = w - right_x - 80
                        item_rect_height = item_height + 6
                        item_positions[item_id] = (item_rect_x, item_rect_y, item_rect_width, item_rect_height)
                        
                        # Highlight selected item with enhanced background and border
                        if is_selected:
                            # Outer glow effect
                            glow_surf = pygame.Surface((item_rect_width + 4, item_rect_height + 4), pygame.SRCALPHA)
                            glow_surf.fill((100, 150, 255, 60))
                            screen.blit(glow_surf, (item_rect_x - 2, item_rect_y - 2))
                            
                            # Main background with gradient effect
                            bg = pygame.Surface((item_rect_width, item_rect_height), pygame.SRCALPHA)
                            # Top lighter, bottom darker
                            for i in range(item_rect_height):
                                alpha = int(220 - (i / item_rect_height) * 40)
                                color = (70, 90, 130, alpha)
                                pygame.draw.line(bg, color, (0, i), (item_rect_width, i))
                            screen.blit(bg, (item_rect_x, item_rect_y))
                        
                            # Border highlight
                            pygame.draw.rect(screen, (150, 200, 255), 
                                           (item_rect_x, item_rect_y, item_rect_width, item_rect_height), 2)
                        
                        # Item name with enhanced styling
                        selection_marker = "▶ " if is_selected else "  "
                        rarity = getattr(item_def, "rarity", "") or ""
                        
                        # Rarity badge
                        rarity_label = ""
                        if rarity:
                            rarity_badge = f"[{rarity.upper()}]"
                            rarity_label = f" {rarity_badge}"
                        
                        line = f"{selection_marker}{item_def.name}{rarity_label}{equipped_marker}"

                        # Base color from rarity, then brighten for equipped/selected
                        base_color = _get_rarity_color(rarity)
                        if is_selected:
                            item_color = tuple(min(255, c + 50) for c in base_color)
                        elif equipped_marker:
                            item_color = tuple(min(255, c + 25) for c in base_color)
                        else:
                            item_color = base_color
                        
                        # Render item name
                        t = ui_font.render(line, True, item_color)
                        screen.blit(t, (right_x, y))
                        y += 28

                        # One-line stats/description with enhanced styling
                        # Show extra info (description) for the currently selected item.
                        if info_line:
                            info_color = (220, 230, 200) if is_selected else (160, 170, 160)
                            # Add subtle icon/bullet for stats
                            stats_prefix = "  • " if is_selected else "    "
                            info_line_with_prefix = stats_prefix + info_line
                            info_surf = ui_font.render(info_line_with_prefix, True, info_color)
                            screen.blit(info_surf, (right_x + 24, y))
                            y += 24
                        else:
                            # Extra spacing if no info line, to keep rows readable
                            y += 12
                        
            
            # Scroll info with enhanced styling
            if len(item_indices) > max_visible_lines:
                first_index = visible_start + 1
                last_index = min(visible_end, len(item_indices))
                scroll_text = f"Showing {first_index}-{last_index} of {len(item_indices)} items"
                scroll_surf = ui_font.render(scroll_text, True, (180, 200, 220))
                # Add subtle background
                scroll_bg = pygame.Surface((scroll_surf.get_width() + 16, 24), pygame.SRCALPHA)
                scroll_bg.fill((40, 50, 60, 180))
                screen.blit(scroll_bg, (right_x - 8, y + 8))
                screen.blit(scroll_surf, (right_x, y + 10))
            
            # Check for mouse hover on items for tooltips using tracked positions
            tooltip = getattr(game, "tooltip", None)
            if tooltip:
                mx, my = tooltip.mouse_pos
                hover_item_id = None
                hover_item_def = None
                
                # Check each item's actual position for hover
                for item_id, (rect_x, rect_y, rect_width, rect_height) in item_positions.items():
                    item_rect = pygame.Rect(rect_x, rect_y, rect_width, rect_height)
                    if item_rect.collidepoint(mx, my):
                        hover_item_def = _resolve_item_def(item_id, inv)
                        if hover_item_def:
                            hover_item_id = item_id
                            break
                
                # Update tooltip if hovering over an item
                if hover_item_def:
                    from ui.tooltip import create_item_tooltip_data
                    tooltip_data = create_item_tooltip_data(
                        hover_item_def, game, focused_is_hero, focused_comp
                    )
                    tooltip.current_tooltip = tooltip_data
                    tooltip.hover_target = hover_item_id
                else:
                    tooltip.current_tooltip = None
                    tooltip.hover_target = None
    
    # Draw tooltip
    tooltip = getattr(game, "tooltip", None)
    if tooltip:
        tooltip.draw(screen, ui_font)
    
    # Footer hints
    hints = [
        "Up/Down: select item | Enter/Space: equip | Q/E: switch character | PgUp/PgDn: page",
        "F1-F7: filter | Ctrl+S: sort | Ctrl+F: search | Ctrl+R: reset | TAB: switch screen | I/ESC: close"
    ]
    _draw_screen_footer(screen, ui_font, hints, w, h)


def draw_character_sheet_fullscreen(game: "Game") -> None:
    """Full-screen character sheet view with polished visuals."""
    screen = game.screen
    ui_font = game.ui_font
    w, h = screen.get_size()
    
    # Fill background
    screen.fill(COLOR_BG)
    
    # Get available screens for tabs
    available_screens = ["inventory", "character", "skills"]
    if getattr(game, "show_shop", False):
        available_screens.append("shop")
    
    # Draw header with tabs
    _draw_screen_header(screen, ui_font, "Character Sheet", "character", available_screens, w)
    
    # Resolve focus character
    focused_is_hero, focused_comp, focused_template = _resolve_focus_character(
        game, "character_sheet_focus_index", use_clamp=True
    )
    
    # Get focus index and party list for party preview section
    focus_index = int(getattr(game, "character_sheet_focus_index", 0))
    party_list: List[CompanionState] = getattr(game, "party", None) or []
    total_slots = 1 + len(party_list)
    if total_slots <= 1:
        focus_index = 0
    else:
        focus_index = max(0, min(focus_index, total_slots - 1))
    
    # Starting Y position
    start_y = 90
    
    if focused_is_hero:
        # Hero info - left column with polished panels
        left_x = 40
        panel_width = 480  # Increased from 400
        panel_spacing = 20
        
        hero_name = getattr(
            game.hero_stats,
            "hero_name",
            getattr(game.player, "name", "Adventurer"),
        )
        level = game.hero_stats.level
        xp = game.hero_stats.xp
        xp_next = game.hero_stats.xp_to_next()
        
        hp = getattr(game.player, "hp", 0)
        max_hp = getattr(game.player, "max_hp", 0)
        atk = game.hero_stats.attack_power
        defense = game.hero_stats.defense
        skill_power = game.hero_stats.skill_power
        
        class_id = getattr(game.hero_stats, "hero_class_id", "unknown")
        class_str = class_id.capitalize()
        
        gold = int(getattr(game.hero_stats, "gold", 0))
        
        # Get resource pools (mana and stamina)
        hero_max_stamina = int(getattr(game.hero_stats, "max_stamina", 0))
        hero_max_mana = int(getattr(game.hero_stats, "max_mana", 0))
        
        # Fall back to player entity if meta-stats aren't wired yet
        if hero_max_stamina <= 0:
            hero_max_stamina = int(getattr(game.player, "max_stamina", 0))
        if hero_max_mana <= 0:
            hero_max_mana = int(getattr(game.player, "max_mana", 0))
        
        current_stamina = int(getattr(game.player, "current_stamina", hero_max_stamina))
        current_mana = int(getattr(game.player, "current_mana", hero_max_mana))
        
        if hero_max_stamina > 0:
            current_stamina = max(0, min(current_stamina, hero_max_stamina))
        if hero_max_mana > 0:
            current_mana = max(0, min(current_mana, hero_max_mana))
        
        # Get status effects if available
        statuses = []
        if hasattr(game.player, "status_effects"):
            statuses = list(getattr(game.player, "status_effects", []))
        
        # Get equipped items
        hero_equipped = getattr(game.hero_stats, "equipped", None) or {}
        inv = getattr(game, "inventory", None)
        
        y = start_y
        
        # === CHARACTER INFO PANEL ===
        # Calculate dynamic height based on content
        panel_padding = 15
        base_height = panel_padding * 2  # Top and bottom padding
        base_height += 32  # Name line
        base_height += 28  # Floor/Level line
        base_height += 22  # XP label
        base_height += 12 + 12  # XP bar + spacing
        base_height += 24  # Gold line
        if statuses:
            base_height += 22  # Status label
            base_height += 24  # Status icons (approximate)
        
        info_panel_height = max(220, base_height)  # Minimum height, grows with content
        _draw_panel(screen, left_x, y, panel_width, info_panel_height, 
                   border_color=(120, 120, 150), bg_color=(25, 25, 35))
        
        panel_y = y + panel_padding
        
        # Name and class (larger, more prominent)
        name_text = f"{hero_name}"
        class_text = f"{class_str}"
        name_surf = ui_font.render(name_text, True, (255, 255, 220))
        screen.blit(name_surf, (left_x + panel_padding, panel_y))
        
        class_surf = ui_font.render(class_text, True, (200, 220, 255))
        class_x = left_x + panel_padding + name_surf.get_width() + 10
        screen.blit(class_surf, (class_x, panel_y))
        panel_y += 32
        
        # Floor and Level
        floor_text = f"Floor {game.floor}  |  Level {level}"
        floor_surf = ui_font.render(floor_text, True, (180, 200, 220))
        screen.blit(floor_surf, (left_x + panel_padding, panel_y))
        panel_y += 28
        
        # XP Bar
        xp_fraction = xp / xp_next if xp_next > 0 else 0.0
        xp_label = f"Experience: {xp}/{xp_next}"
        xp_label_surf = ui_font.render(xp_label, True, (220, 220, 180))
        screen.blit(xp_label_surf, (left_x + panel_padding, panel_y))
        panel_y += 22
        
        bar_width = panel_width - 2 * panel_padding
        bar_height = 12
        _draw_bar(screen, left_x + panel_padding, panel_y, bar_width, bar_height,
                 xp_fraction, (40, 30, 50), (150, 100, 200), (100, 80, 120))
        panel_y += bar_height + 12
        
        # Gold
        gold_text = f"Gold: {gold}"
        gold_surf = ui_font.render(gold_text, True, (255, 220, 100))
        screen.blit(gold_surf, (left_x + panel_padding, panel_y))
        panel_y += 24
        
        # Status effects
        if statuses:
            status_label = ui_font.render("Status Effects:", True, (220, 220, 180))
            screen.blit(status_label, (left_x + panel_padding, panel_y))
            panel_y += 22
            draw_enhanced_status_indicators(
                screen, ui_font, left_x + panel_padding, panel_y,
                statuses, icon_size=18, icon_spacing=24, vertical=False
            )
        
        y += info_panel_height + panel_spacing
        
        # === RESOURCES PANEL ===
        # Calculate dynamic height based on number of resource bars
        num_resources = 1  # HP always present
        if hero_max_stamina > 0:
            num_resources += 1
        if hero_max_mana > 0:
            num_resources += 1
        
        # Each resource bar takes: label (20) + bar (12) + spacing (6) = 38
        resources_panel_height = panel_padding * 2 + 28 + (num_resources * 38)
        resources_panel_height = max(140, resources_panel_height)  # Minimum height
        
        _draw_panel(screen, left_x, y, panel_width, resources_panel_height,
                   border_color=(100, 120, 100), bg_color=(25, 35, 25))
        
        panel_y = y + panel_padding
        resources_title = ui_font.render("Resources", True, (200, 255, 200))
        screen.blit(resources_title, (left_x + panel_padding, panel_y))
        panel_y += 28
        
        # HP Bar
        hp_fraction = hp / max_hp if max_hp > 0 else 0.0
        hp_color = _calculate_hp_color(hp_fraction)
        panel_y = _draw_resource_bar_with_label(
            screen, ui_font, left_x + panel_padding, panel_y, bar_width, bar_height,
            "HP", hp, max_hp, (220, 220, 220), (50, 20, 20), hp_color, (120, 80, 80)
        )
        
        # Stamina Bar
        if hero_max_stamina > 0:
            sta_fraction = current_stamina / hero_max_stamina if hero_max_stamina > 0 else 0.0
            panel_y = _draw_resource_bar_with_label(
                screen, ui_font, left_x + panel_padding, panel_y, bar_width, bar_height,
                "Stamina", current_stamina, hero_max_stamina, (220, 220, 220),
                (30, 40, 30), (100, 200, 100), (80, 120, 80)
            )
        
        # Mana Bar
        if hero_max_mana > 0:
            mana_fraction = current_mana / hero_max_mana if hero_max_mana > 0 else 0.0
            panel_y = _draw_resource_bar_with_label(
                screen, ui_font, left_x + panel_padding, panel_y, bar_width, bar_height,
                "Mana", current_mana, hero_max_mana, (220, 220, 220),
                (30, 30, 40), (100, 150, 255), (80, 100, 150)
            )
        
        y += resources_panel_height + panel_spacing
        
        # === STATS PANEL ===
        # Calculate dynamic height based on stats and equipment
        num_stats = 2  # Attack, Defense
        if skill_power != 1.0:
            num_stats += 1
        num_equipment = 3  # Weapon, Armor, Trinket
        
        stats_panel_height = panel_padding * 2 + 28  # Title
        stats_panel_height += num_stats * 26  # Stats
        stats_panel_height += 8 + 24  # Equipment title + spacing
        stats_panel_height += num_equipment * 22  # Equipment items
        stats_panel_height = max(200, stats_panel_height)  # Minimum height
        
        _draw_panel(screen, left_x, y, panel_width, stats_panel_height,
                   border_color=(120, 100, 100), bg_color=(35, 25, 25))
        
        panel_y = y + panel_padding
        stats_title = ui_font.render("Combat Stats", True, (255, 200, 200))
        screen.blit(stats_title, (left_x + panel_padding, panel_y))
        panel_y += 28
        
        # Stat values with better formatting
        stats_data = [
            ("Attack Power", atk, (255, 200, 150)),
            ("Defense", defense, (200, 200, 255)),
        ]
        
        if skill_power != 1.0:
            stats_data.append(("Skill Power", f"{skill_power:.2f}x", (255, 220, 100)))
        
        for stat_name, stat_value, stat_color in stats_data:
            stat_text = f"{stat_name}: {stat_value}"
            stat_surf = ui_font.render(stat_text, True, stat_color)
            screen.blit(stat_surf, (left_x + panel_padding + 10, panel_y))
            panel_y += 26
        
        # Equipment summary
        panel_y += 8
        equip_title = ui_font.render("Equipment", True, (220, 220, 180))
        screen.blit(equip_title, (left_x + panel_padding, panel_y))
        panel_y += 24
        
        slots = ["weapon", "armor", "trinket"]
        for slot in slots:
            item_id = hero_equipped.get(slot)
            if item_id:
                item_def = _resolve_item_def(item_id, inv)
                if item_def:
                    slot_name = slot.capitalize()
                    item_text = f"{slot_name}: {item_def.name}"
                    item_surf = ui_font.render(item_text, True, (200, 220, 200))
                    screen.blit(item_surf, (left_x + panel_padding + 10, panel_y))
                else:
                    slot_text = f"{slot.capitalize()}: (unknown)"
                    slot_surf = ui_font.render(slot_text, True, (150, 150, 150))
                    screen.blit(slot_surf, (left_x + panel_padding + 10, panel_y))
            else:
                slot_text = f"{slot.capitalize()}: (none)"
                slot_surf = ui_font.render(slot_text, True, (120, 120, 120))
                screen.blit(slot_surf, (left_x + panel_padding + 10, panel_y))
            panel_y += 22
        
        # === PERKS PANEL - middle column ===
        mid_x = w // 2 - 20
        perks_panel_width = 420  # Increased from 350
        y = start_y
        
        perk_ids = getattr(game.hero_stats, "perks", []) or []
        num_perks = len(perk_ids)
        # Calculate dynamic height: title (28) + padding (30) + perks (24 each) or empty message (44)
        if num_perks == 0:
            perks_panel_height = 15 + 28 + 22 + 22 + 15  # padding + title + 2 lines + padding
        else:
            perks_panel_height = 15 + 28 + (num_perks * 24) + 15  # padding + title + perks + padding
        perks_panel_height = max(200, perks_panel_height)  # Minimum height
        
        _draw_panel(screen, mid_x, y, perks_panel_width, perks_panel_height,
                   border_color=(150, 120, 100), bg_color=(35, 30, 25))
        
        panel_padding = 15
        panel_y = y + panel_padding
        
        perks_title = ui_font.render("Perks", True, (255, 220, 180))
        screen.blit(perks_title, (mid_x + panel_padding, panel_y))
        panel_y += 28
        
        if not perk_ids:
            no_perks = ui_font.render("None yet.", True, (180, 180, 180))
            screen.blit(no_perks, (mid_x + panel_padding, panel_y))
            panel_y += 22
            no_perks2 = ui_font.render("Level up to choose perks!", True, (160, 160, 160))
            screen.blit(no_perks2, (mid_x + panel_padding, panel_y))
        else:
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
                    line = f"• {pretty_name}"
                    perk_color = (220, 220, 200)
                else:
                    branch = getattr(perk_def, "branch_name", None)
                    if branch:
                        line = f"• [{branch}] {perk_def.name}"
                    else:
                        line = f"• {perk_def.name}"
                    perk_color = (240, 230, 200)
                
                t = ui_font.render(line, True, perk_color)
                screen.blit(t, (mid_x + panel_padding + 5, panel_y))
                panel_y += 24
        
        # === PARTY PREVIEW PANEL - right column ===
        _draw_party_preview_panel(
            screen, ui_font, w, start_y, focus_index, party_list,
            hero_name, class_str, level, hp, max_hp
        )
    else:
        # Companion info with polished panels
        left_x = 40
        panel_width = 480  # Increased from 400
        panel_spacing = 20
        comp = focused_comp
        assert comp is not None
        
        if focused_template is not None:
            base_name = getattr(focused_template, "name", "Companion")
            role = getattr(focused_template, "role", "Companion")
        else:
            base_name = "Companion"
            role = "Companion"
        
        name_override = getattr(comp, "name_override", None)
        comp_name = name_override or base_name
        
        level = int(getattr(comp, "level", 1))
        xp = int(getattr(comp, "xp", 0))
        
        xp_next_val = getattr(comp, "xp_to_next", None)
        xp_next = None
        if callable(xp_next_val):
            try:
                xp_next = int(xp_next_val())
            except Exception:
                xp_next = None
        elif isinstance(xp_next_val, (int, float)):
            xp_next = int(xp_next_val)
        
        max_hp = int(getattr(comp, "max_hp", 1))
        hp = int(getattr(comp, "hp", max_hp))
        atk = int(getattr(comp, "attack_power", 0))
        defense = int(getattr(comp, "defense", 0))
        skill_power = float(getattr(comp, "skill_power", 1.0))
        
        # Get resource pools for companion
        comp_max_stamina = int(getattr(comp, "max_stamina", 0))
        comp_max_mana = int(getattr(comp, "max_mana", 0))
        
        # Companions don't have current values tracked separately in exploration,
        # so we show max/max (they'll be at full in exploration)
        current_stamina = comp_max_stamina
        current_mana = comp_max_mana
        
        # Get status effects if available
        statuses = []
        if hasattr(comp, "status_effects"):
            statuses = list(getattr(comp, "status_effects", []))
        
        # Get equipped items
        comp_equipped = getattr(comp, "equipped", None) or {}
        inv = getattr(game, "inventory", None)
        
        y = start_y
        
        # === CHARACTER INFO PANEL ===
        # Calculate dynamic height based on content
        panel_padding = 15
        base_height = panel_padding * 2  # Top and bottom padding
        base_height += 32  # Name/role line
        base_height += 28  # Floor/Level line
        base_height += 22  # XP label
        base_height += 12 + 12  # XP bar + spacing (if present)
        if statuses:
            base_height += 22  # Status label
            base_height += 24  # Status icons (approximate)
        
        info_panel_height = max(220, base_height)  # Minimum height, grows with content
        _draw_panel(screen, left_x, y, panel_width, info_panel_height,
                   border_color=(120, 120, 150), bg_color=(25, 25, 35))
        
        panel_y = y + panel_padding
        
        # Name and role
        name_surf = ui_font.render(comp_name, True, (255, 255, 220))
        screen.blit(name_surf, (left_x + panel_padding, panel_y))
        
        role_surf = ui_font.render(role, True, (200, 220, 255))
        role_x = left_x + panel_padding + name_surf.get_width() + 10
        screen.blit(role_surf, (role_x, panel_y))
        panel_y += 32
        
        # Floor and Level
        floor_text = f"Floor {game.floor}  |  Level {level}"
        floor_surf = ui_font.render(floor_text, True, (180, 200, 220))
        screen.blit(floor_surf, (left_x + panel_padding, panel_y))
        panel_y += 28
        
        # XP Bar
        if xp_next is not None and xp_next > 0:
            xp_fraction = xp / xp_next if xp_next > 0 else 0.0
            xp_label = f"Experience: {xp}/{xp_next}"
        else:
            xp_fraction = 0.0
            xp_label = f"Experience: {xp}"
        xp_label_surf = ui_font.render(xp_label, True, (220, 220, 180))
        screen.blit(xp_label_surf, (left_x + panel_padding, panel_y))
        panel_y += 22
        
        bar_width = panel_width - 2 * panel_padding
        bar_height = 12
        if xp_next is not None and xp_next > 0:
            _draw_bar(screen, left_x + panel_padding, panel_y, bar_width, bar_height,
                     xp_fraction, (40, 30, 50), (150, 100, 200), (100, 80, 120))
        panel_y += bar_height + 12
        
        # Status effects
        if statuses:
            status_label = ui_font.render("Status Effects:", True, (220, 220, 180))
            screen.blit(status_label, (left_x + panel_padding, panel_y))
            panel_y += 22
            draw_enhanced_status_indicators(
                screen, ui_font, left_x + panel_padding, panel_y,
                statuses, icon_size=18, icon_spacing=24, vertical=False
            )
        
        y += info_panel_height + panel_spacing
        
        # === RESOURCES PANEL ===
        # Calculate dynamic height based on number of resource bars
        num_resources = 1  # HP always present
        if comp_max_stamina > 0:
            num_resources += 1
        if comp_max_mana > 0:
            num_resources += 1
        
        # Each resource bar takes: label (20) + bar (12) + spacing (6) = 38
        resources_panel_height = panel_padding * 2 + 28 + (num_resources * 38)
        resources_panel_height = max(140, resources_panel_height)  # Minimum height
        
        _draw_panel(screen, left_x, y, panel_width, resources_panel_height,
                   border_color=(100, 120, 100), bg_color=(25, 35, 25))
        
        panel_y = y + panel_padding
        resources_title = ui_font.render("Resources", True, (200, 255, 200))
        screen.blit(resources_title, (left_x + panel_padding, panel_y))
        panel_y += 28
        
        # HP Bar
        hp_fraction = hp / max_hp if max_hp > 0 else 0.0
        hp_color = _calculate_hp_color(hp_fraction)
        panel_y = _draw_resource_bar_with_label(
            screen, ui_font, left_x + panel_padding, panel_y, bar_width, bar_height,
            "HP", hp, max_hp, (220, 220, 220), (50, 20, 20), hp_color, (120, 80, 80)
        )
        
        # Stamina Bar
        if comp_max_stamina > 0:
            sta_fraction = current_stamina / comp_max_stamina if comp_max_stamina > 0 else 0.0
            panel_y = _draw_resource_bar_with_label(
                screen, ui_font, left_x + panel_padding, panel_y, bar_width, bar_height,
                "Stamina", current_stamina, comp_max_stamina, (220, 220, 220),
                (30, 40, 30), (100, 200, 100), (80, 120, 80)
            )
        
        # Mana Bar
        if comp_max_mana > 0:
            mana_fraction = current_mana / comp_max_mana if comp_max_mana > 0 else 0.0
            panel_y = _draw_resource_bar_with_label(
                screen, ui_font, left_x + panel_padding, panel_y, bar_width, bar_height,
                "Mana", current_mana, comp_max_mana, (220, 220, 220),
                (30, 30, 40), (100, 150, 255), (80, 100, 150)
            )
        
        y += resources_panel_height + panel_spacing
        
        # === STATS PANEL ===
        # Calculate dynamic height based on stats and equipment
        num_stats = 2  # Attack, Defense
        if skill_power != 1.0:
            num_stats += 1
        num_equipment = 3  # Weapon, Armor, Trinket
        
        stats_panel_height = panel_padding * 2 + 28  # Title
        stats_panel_height += num_stats * 26  # Stats
        stats_panel_height += 8 + 24  # Equipment title + spacing
        stats_panel_height += num_equipment * 22  # Equipment items
        stats_panel_height = max(200, stats_panel_height)  # Minimum height
        
        _draw_panel(screen, left_x, y, panel_width, stats_panel_height,
                   border_color=(120, 100, 100), bg_color=(35, 25, 25))
        
        panel_y = y + panel_padding
        stats_title = ui_font.render("Combat Stats", True, (255, 200, 200))
        screen.blit(stats_title, (left_x + panel_padding, panel_y))
        panel_y += 28
        
        # Stat values
        stats_data = [
            ("Attack Power", atk, (255, 200, 150)),
            ("Defense", defense, (200, 200, 255)),
        ]
        
        if skill_power != 1.0:
            stats_data.append(("Skill Power", f"{skill_power:.2f}x", (255, 220, 100)))
        
        for stat_name, stat_value, stat_color in stats_data:
            stat_text = f"{stat_name}: {stat_value}"
            stat_surf = ui_font.render(stat_text, True, stat_color)
            screen.blit(stat_surf, (left_x + panel_padding + 10, panel_y))
            panel_y += 26
        
        # Equipment summary
        panel_y += 8
        equip_title = ui_font.render("Equipment", True, (220, 220, 180))
        screen.blit(equip_title, (left_x + panel_padding, panel_y))
        panel_y += 24
        
        slots = ["weapon", "armor", "trinket"]
        for slot in slots:
            item_id = comp_equipped.get(slot)
            if item_id:
                item_def = _resolve_item_def(item_id, inv)
                if item_def:
                    slot_name = slot.capitalize()
                    item_text = f"{slot_name}: {item_def.name}"
                    item_surf = ui_font.render(item_text, True, (200, 220, 200))
                    screen.blit(item_surf, (left_x + panel_padding + 10, panel_y))
                else:
                    slot_text = f"{slot.capitalize()}: (unknown)"
                    slot_surf = ui_font.render(slot_text, True, (150, 150, 150))
                    screen.blit(slot_surf, (left_x + panel_padding + 10, panel_y))
            else:
                slot_text = f"{slot.capitalize()}: (none)"
                slot_surf = ui_font.render(slot_text, True, (120, 120, 120))
                screen.blit(slot_surf, (left_x + panel_padding + 10, panel_y))
            panel_y += 22
        
        # === PERKS PANEL - middle column ===
        mid_x = w // 2 - 20
        perks_panel_width = 420  # Increased from 350
        y = start_y
        
        perk_ids: List[str] = []
        if comp is not None:
            perk_ids = getattr(comp, "perks", []) or []
        
        num_perks = len(perk_ids)
        # Calculate dynamic height: title (28) + padding (30) + perks (24 each) or empty message (44)
        if num_perks == 0:
            perks_panel_height = 15 + 28 + 22 + 22 + 15  # padding + title + 2 lines + padding
        else:
            perks_panel_height = 15 + 28 + (num_perks * 24) + 15  # padding + title + perks + padding
        perks_panel_height = max(200, perks_panel_height)  # Minimum height
        
        _draw_panel(screen, mid_x, y, perks_panel_width, perks_panel_height,
                   border_color=(150, 120, 100), bg_color=(35, 30, 25))
        
        panel_padding = 15
        panel_y = y + panel_padding
        
        perks_title = ui_font.render("Perks", True, (255, 220, 180))
        screen.blit(perks_title, (mid_x + panel_padding, panel_y))
        panel_y += 28
        
        if not perk_ids:
            placeholder = ui_font.render("This companion has", True, (180, 180, 180))
            screen.blit(placeholder, (mid_x + panel_padding, panel_y))
            panel_y += 22
            placeholder2 = ui_font.render("no perks yet.", True, (160, 160, 160))
            screen.blit(placeholder2, (mid_x + panel_padding, panel_y))
        else:
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
                    line = f"• {pretty_name}"
                    perk_color = (220, 220, 200)
                else:
                    branch = getattr(perk_def, "branch_name", None)
                    if branch:
                        line = f"• [{branch}] {perk_def.name}"
                    else:
                        line = f"• {perk_def.name}"
                    perk_color = (240, 230, 200)
                
                t = ui_font.render(line, True, perk_color)
                screen.blit(t, (mid_x + panel_padding + 5, panel_y))
                panel_y += 24
        
        # === PARTY PREVIEW PANEL - right column (always visible) ===
        # Get hero stats for the party panel
        hero_name = getattr(
            game.hero_stats,
            "hero_name",
            getattr(game.player, "name", "Adventurer"),
        )
        hero_level = game.hero_stats.level
        hero_hp = getattr(game.player, "hp", 0)
        hero_max_hp = getattr(game.player, "max_hp", 0)
        hero_class_id = getattr(game.hero_stats, "hero_class_id", "unknown")
        hero_class_str = hero_class_id.capitalize()
        
        _draw_party_preview_panel(
            screen, ui_font, w, start_y, focus_index, party_list,
            hero_name, hero_class_str, hero_level, hero_hp, hero_max_hp
        )
    
    # Footer hints
    hints = [
        "Q/E: switch character | TAB: switch screen | C/ESC: close"
    ]
    _draw_screen_footer(screen, ui_font, hints, w, h)


def draw_shop_fullscreen(game: "Game") -> None:
    """Full-screen shop view."""
    screen = game.screen
    ui_font = game.ui_font
    w, h = screen.get_size()
    
    # Fill background
    screen.fill(COLOR_BG)
    
    # Get available screens for tabs
    available_screens = ["inventory", "character", "skills", "shop"]
    
    # Draw header with tabs
    _draw_screen_header(screen, ui_font, "Dungeon Merchant", "shop", available_screens, w)
    
    mode = getattr(game, "shop_mode", "buy")
    mode_label = "BUY" if mode == "buy" else "SELL"
    
    gold_value = int(getattr(getattr(game, "hero_stats", None), "gold", 0))
    gold_line = ui_font.render(f"Your gold: {gold_value}", True, (230, 210, 120))
    screen.blit(gold_line, (40, 70))
    
    stock_buy: List[str] = list(getattr(game, "shop_stock", []))
    inv: Inventory | None = getattr(game, "inventory", None)
    cursor = int(getattr(game, "shop_cursor", 0))
    
    if mode == "buy":
        active_list = stock_buy
    else:
        if inv is None:
            active_list = []
        else:
            active_list = inv.get_sellable_item_ids()
    
    # Left column: Buy list
    left_x = 40
    y = 110
    
    buy_title = ui_font.render(f"{mode_label} Items:", True, (220, 220, 180))
    screen.blit(buy_title, (left_x, y))
    y += 28
    
    if not active_list:
        msg_text = (
            "The merchant has nothing left to sell."
            if mode == "buy"
            else "You have nothing you're willing to sell."
        )
        msg = ui_font.render(msg_text, True, (190, 190, 190))
        screen.blit(msg, (left_x, y))
    else:
        max_items = len(active_list)
        line_height = 26
        if max_items > 0:
            cursor = max(0, min(cursor, max_items - 1))
        
        # Show more items in fullscreen
        visible_start = max(0, cursor - 10)
        visible_end = min(max_items, cursor + 15)
        visible_items = active_list[visible_start:visible_end]
        
        # Get floor index for economy calculations
        floor_index = getattr(game, "floor", 1)
        
        inv = getattr(game, "inventory", None)
        for i, item_id in enumerate(visible_items):
            actual_index = visible_start + i
            item_def = _resolve_item_def(item_id, inv)
            if item_def is None:
                name = item_id
                price = 0
                rarity = ""
            else:
                name = item_def.name
                rarity = getattr(item_def, "rarity", "")
                # Use economy system for dynamic pricing
                if mode == "buy":
                    price = calculate_shop_buy_price(item_def, floor_index)
                else:
                    price = calculate_shop_sell_price(item_def, floor_index)
            
            label = f"{actual_index + 1}) {name}"
            if rarity:
                label += f" [{rarity}]"
            
            price_str = f"{price}g" if mode == "buy" else f"{price}g (sell)"
            
            if actual_index == cursor:
                # Highlight selected item
                bg = pygame.Surface((w // 2 - 80, line_height), pygame.SRCALPHA)
                bg.fill((60, 60, 90, 210))
                screen.blit(bg, (left_x, y - 2))
                label_color = (255, 255, 200)
            else:
                label_color = (230, 230, 230)
            
            label_surf = ui_font.render(label, True, label_color)
            screen.blit(label_surf, (left_x + 20, y))
            
            price_surf = ui_font.render(price_str, True, (230, 210, 120))
            screen.blit(price_surf, (left_x + w // 2 - 200, y))
            
            y += line_height
        
        # Right column: detailed info for currently selected item
        if 0 <= cursor < max_items:
            info_x = w // 2 + 40
            info_y = 110

            selected_id = active_list[cursor]
            inv = getattr(game, "inventory", None)
            selected_def = _resolve_item_def(selected_id, inv)

            if selected_def is not None:
                info_title = ui_font.render("Item Info:", True, (220, 220, 180))
                screen.blit(info_title, (info_x, info_y))
                info_y += 26

                # Name + rarity
                rarity = getattr(selected_def, "rarity", "")
                if rarity:
                    name_line = f"{selected_def.name} [{rarity}]"
                else:
                    name_line = selected_def.name
                name_surf = ui_font.render(name_line, True, (235, 235, 220))
                screen.blit(name_surf, (info_x, info_y))
                info_y += 24

                # Stats + optional description (shown only for the selected item)
                info_line = _build_item_info_line(selected_def, include_description=True)
                if info_line:
                    info_surf = ui_font.render(info_line, True, (190, 190, 190))
                    screen.blit(info_surf, (info_x, info_y))
    
    # Footer hints
    if mode == "buy":
        hints = [
            "Up/Down: move • Enter/Space: buy • 1–9: quick buy",
            "Shift+TAB: switch to SELL • TAB: switch screen • I/C: jump to screen • ESC: close"
        ]
    else:
        hints = [
            "Up/Down: move • Enter/Space: sell • 1–9: quick sell",
            "Shift+TAB: switch to BUY • TAB: switch screen • I/C: jump to screen • ESC: close"
        ]
    _draw_screen_footer(screen, ui_font, hints, w, h)


def draw_skill_screen_fullscreen(game: "Game") -> None:
    """Full-screen skill allocation view."""
    screen = game.screen
    ui_font = game.ui_font
    w, h = screen.get_size()
    
    # Fill background
    screen.fill(COLOR_BG)
    
    # Get available screens for tabs
    available_screens = ["inventory", "character", "skills"]
    if getattr(game, "show_shop", False):
        available_screens.append("shop")
    
    # Draw header with tabs
    _draw_screen_header(screen, ui_font, "Skill Allocation", "skills", available_screens, w)
    
    # Get skill screen core instance
    skill_screen_core = getattr(game, "skill_screen", None)
    if skill_screen_core is None:
        # Fallback if skill screen core doesn't exist
        error_text = ui_font.render("Skill screen not initialized.", True, (200, 150, 150))
        screen.blit(error_text, (w // 2 - error_text.get_width() // 2, h // 2))
        return
    
    # Draw skill screen content
    skill_screen_core.draw_content(screen, w, h)
    
    # Footer hints
    hints = [
        "Arrow Keys/WASD: pan | +/-: zoom | Click/Enter: select/upgrade | Q/E: switch character",
        "TAB: switch screen | T/ESC: close"
    ]
    _draw_screen_footer(screen, ui_font, hints, w, h)
