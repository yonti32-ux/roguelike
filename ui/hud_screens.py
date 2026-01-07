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

if TYPE_CHECKING:
    from engine.game import Game
    from systems.inventory import Inventory, ItemDef


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
) -> int:
    """
    Draw equipment section showing weapon, armor, trinket.
    
    Returns:
        Y position after the section
    """
    equipped_title = ui_font.render("Equipped:", True, (220, 220, 180))
    screen.blit(equipped_title, (x, y))
    y += 28
    
    slots = ["weapon", "armor", "trinket"]
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
        t = ui_font.render(line, True, (220, 220, 220))
        screen.blit(t, (x + indent, y))
        y += 24
    
    return y


def _draw_screen_header(
    screen: pygame.Surface,
    ui_font: pygame.font.Font,
    title: str,
    current_screen: str,
    available_screens: List[str],
    w: int,
) -> None:
    """Draw header with title and tab indicators."""
    # Title
    title_surf = ui_font.render(title, True, (240, 240, 200))
    screen.blit(title_surf, (40, 30))
    
    # Tab indicators
    tab_x = w - 400
    tab_y = 30
    tab_spacing = 120
    
    for i, screen_name in enumerate(available_screens):
        is_current = screen_name == current_screen
        tab_text = screen_name.capitalize()
        if is_current:
            tab_color = (255, 255, 200)
            # Draw underline
            tab_surf = ui_font.render(tab_text, True, tab_color)
            screen.blit(tab_surf, (tab_x + i * tab_spacing, tab_y))
            pygame.draw.line(
                screen,
                tab_color,
                (tab_x + i * tab_spacing, tab_y + 22),
                (tab_x + i * tab_spacing + tab_surf.get_width(), tab_y + 22),
                2,
            )
        else:
            tab_color = (150, 150, 150)
            tab_surf = ui_font.render(tab_text, True, tab_color)
            screen.blit(tab_surf, (tab_x + i * tab_spacing, tab_y))


def _draw_screen_footer(
    screen: pygame.Surface,
    ui_font: pygame.font.Font,
    hints: List[str],
    w: int,
    h: int,
) -> None:
    """Draw footer with navigation hints."""
    footer_y = h - 50
    for i, hint in enumerate(hints):
        hint_surf = ui_font.render(hint, True, (160, 160, 160))
        screen.blit(hint_surf, (40, footer_y + i * 22))


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
    
    # Character name
    char_title = ui_font.render(title_text, True, (240, 240, 200))
    screen.blit(char_title, (left_x, y))
    y += 30
    
    # Stats
    if stats_line_text:
        stats_surf = ui_font.render(stats_line_text, True, (200, 200, 200))
        screen.blit(stats_surf, (left_x, y))
        y += 30
    
    # Equipped section
    y = _draw_equipment_section(screen, ui_font, left_x, y, equipped_map, indent=20)
    
    # Right column: Backpack items
    right_x = w // 2 + 40
    y = 90
    
    backpack_title = ui_font.render("Backpack:", True, (220, 220, 180))
    screen.blit(backpack_title, (right_x, y))
    y += 28
    
    if not inv or not getattr(inv, "items", None):
        none = ui_font.render("You are not carrying anything yet.", True, (180, 180, 180))
        screen.blit(none, (right_x, y))
    else:
        # Group items by slot/category
        items_by_slot: Dict[str, List[str]] = {}
        for item_id in inv.items:
            item_def = get_item_def(item_id)
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
            line_height = 38  # Approximate height per item (including stats line)
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
                        category_surf = ui_font.render(f"--- {slot_display} ---", True, (200, 200, 150))
                        screen.blit(category_surf, (right_x, y))
                        y += 24
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
                            category_surf = ui_font.render(f"--- {slot_display} ---", True, (200, 200, 150))
                            screen.blit(category_surf, (right_x, y))
                            y += 24
                            last_shown_category = slot
                        
                        item_def = get_item_def(item_id)
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
                        
                        # Highlight selected item with background
                        if is_selected:
                            bg_width = w - right_x - 80
                            bg_height = 38
                            bg = pygame.Surface((bg_width, bg_height), pygame.SRCALPHA)
                            bg.fill((60, 60, 90, 210))
                            screen.blit(bg, (right_x - 10, y - 2))
                        
                        # Item name with selection indicator + rarity tag
                        selection_marker = "> " if is_selected else "  "
                        rarity = getattr(item_def, "rarity", "") or ""
                        rarity_label = f" [{rarity.capitalize()}]" if rarity else ""
                        line = f"{selection_marker}{item_def.name}{rarity_label}{equipped_marker}"

                        # Base color from rarity, then brighten for equipped/selected
                        base_color = _get_rarity_color(rarity)
                        if is_selected:
                            item_color = tuple(min(255, c + 40) for c in base_color)
                        elif equipped_marker:
                            item_color = tuple(min(255, c + 20) for c in base_color)
                        else:
                            item_color = base_color
                        t = ui_font.render(line, True, item_color)
                        screen.blit(t, (right_x, y))
                        y += 20

                        # One-line stats/description, slightly dimmer and indented.
                        # Show extra info (description) for the currently selected item.
                        info_line = _build_item_info_line(item_def, include_description=is_selected)
                        if info_line:
                            info_color = (200, 200, 180) if is_selected else (170, 170, 170)
                            info_surf = ui_font.render(info_line, True, info_color)
                            screen.blit(info_surf, (right_x + 24, y))
                            y += 18
                        else:
                            # Small extra spacing if no info line, to keep rows readable
                            y += 4
            
            # Scroll info
            if len(item_indices) > max_visible_lines:
                first_index = visible_start + 1
                last_index = min(visible_end, len(item_indices))
                scroll_text = f"Items {first_index}-{last_index} of {len(item_indices)}"
                scroll_surf = ui_font.render(scroll_text, True, (150, 150, 150))
                screen.blit(scroll_surf, (right_x, y + 10))
    
    # Footer hints
    hints = [
        "Up/Down: select item | Enter/Space: equip | Q/E: switch character | PgUp/PgDn: page",
        "TAB: switch screen | I/ESC: close"
    ]
    _draw_screen_footer(screen, ui_font, hints, w, h)


def draw_character_sheet_fullscreen(game: "Game") -> None:
    """Full-screen character sheet view."""
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
    
    y = 90
    
    if focused_is_hero:
        # Hero info - left column
        left_x = 40
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
        
        name_line = ui_font.render(f"{hero_name} ({class_str})", True, (230, 230, 230))
        screen.blit(name_line, (left_x, y))
        y += 28
        
        floor_line = ui_font.render(f"Floor: {game.floor}", True, (200, 200, 200))
        screen.blit(floor_line, (left_x, y))
        y += 26
        
        xp_text_str = f"Level {level}  XP {xp}/{xp_next}"
        xp_line = ui_font.render(xp_text_str, True, (220, 220, 180))
        screen.blit(xp_line, (left_x, y))
        y += 26
        
        gold = int(getattr(game.hero_stats, "gold", 0))
        gold_line = ui_font.render(f"Gold: {gold}", True, (230, 210, 120))
        screen.blit(gold_line, (left_x, y))
        y += 30
        
        # Stats
        stats_title = ui_font.render("Stats:", True, (220, 220, 180))
        screen.blit(stats_title, (left_x, y))
        y += 26
        
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
        
        stats_lines = [
            f"HP: {hp}/{max_hp}",
            f"Attack: {atk}",
            f"Defense: {defense}",
        ]
        
        # Add resource pools if they exist
        if hero_max_stamina > 0:
            stats_lines.append(f"Stamina: {current_stamina}/{hero_max_stamina}")
        if hero_max_mana > 0:
            stats_lines.append(f"Mana: {current_mana}/{hero_max_mana}")
        
        if skill_power != 1.0:
            stats_lines.append(f"Skill Power: {skill_power:.2f}x")
        
        for line in stats_lines:
            t = ui_font.render(line, True, (220, 220, 220))
            screen.blit(t, (left_x + 20, y))
            y += 24
        
        # Perks - middle column
        mid_x = w // 2 - 100
        y = 90
        perks_title = ui_font.render("Perks:", True, (220, 220, 180))
        screen.blit(perks_title, (mid_x, y))
        y += 28
        
        perk_ids = getattr(game.hero_stats, "perks", []) or []
        if not perk_ids:
            no_perks = ui_font.render("None yet. Level up to choose perks!", True, (180, 180, 180))
            screen.blit(no_perks, (mid_x, y))
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
                    line = f"- {pretty_name}"
                else:
                    branch = getattr(perk_def, "branch_name", None)
                    if branch:
                        line = f"- {branch}: {perk_def.name}"
                    else:
                        line = f"- {perk_def.name}"
                t = ui_font.render(line, True, (210, 210, 210))
                screen.blit(t, (mid_x, y))
                y += 22
        
        # Party preview - right column
        right_x = w - 300
        y = 90
        party_title = ui_font.render("Party:", True, (220, 220, 180))
        screen.blit(party_title, (right_x, y))
        y += 28
        
        hero_selected = focus_index == 0
        hero_marker = " [*]" if hero_selected else ""
        hero_line = ui_font.render(
            f"[Hero] {hero_name} ({class_str}){hero_marker}",
            True,
            (230, 230, 230),
        )
        screen.blit(hero_line, (right_x, y))
        y += 24
        
        if not party_list:
            companion_line = ui_font.render(
                "[Companion] — no allies recruited yet",
                True,
                (170, 170, 190),
            )
            screen.blit(companion_line, (right_x, y))
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
                    comp_atk = 5
                    comp_defense = 0
                
                lvl_prefix = f"Lv {comp_level} " if comp_level is not None else ""
                is_selected = focus_index == idx + 1
                sel_marker = " [*]" if is_selected else ""
                
                # Build stats line for companion preview
                comp_stats_parts = [
                    f"HP {comp_max_hp}",
                    f"ATK {comp_atk}",
                    f"DEF {comp_defense}",
                ]
                
                # Add mana/stamina if available
                comp_sta = int(getattr(comp, "max_stamina", 0))
                comp_mana = int(getattr(comp, "max_mana", 0))
                if comp_sta > 0:
                    comp_stats_parts.append(f"STA {comp_sta}")
                if comp_mana > 0:
                    comp_stats_parts.append(f"MANA {comp_mana}")
                
                stats_str = ", ".join(comp_stats_parts)
                line = (
                    f"[Companion] {lvl_prefix}{name} ({role}){sel_marker} – {stats_str}"
                )
                t = ui_font.render(line, True, (210, 210, 230))
                screen.blit(t, (right_x, y))
                y += 22
    else:
        # Companion info (similar structure)
        left_x = 40
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
        
        name_line = ui_font.render(f"{comp_name} ({role})", True, (230, 230, 230))
        screen.blit(name_line, (left_x, y))
        y += 28
        
        floor_line = ui_font.render(f"Floor: {game.floor}", True, (200, 200, 200))
        screen.blit(floor_line, (left_x, y))
        y += 26
        
        if xp_next is not None and xp_next > 0:
            xp_text_str = f"Level {level}  XP {xp}/{xp_next}"
        else:
            xp_text_str = f"Level {level}  XP {xp}"
        xp_line = ui_font.render(xp_text_str, True, (220, 220, 180))
        screen.blit(xp_line, (left_x, y))
        y += 30
        
        stats_title = ui_font.render("Stats:", True, (220, 220, 180))
        screen.blit(stats_title, (left_x, y))
        y += 26
        
        # Get resource pools for companion
        comp_max_stamina = int(getattr(comp, "max_stamina", 0))
        comp_max_mana = int(getattr(comp, "max_mana", 0))
        
        # Companions don't have current values tracked separately in exploration,
        # so we show max/max (they'll be at full in exploration)
        current_stamina = comp_max_stamina
        current_mana = comp_max_mana
        
        stats_lines = [
            f"HP: {hp}/{max_hp}",
            f"Attack: {atk}",
            f"Defense: {defense}",
        ]
        
        # Add resource pools if they exist
        if comp_max_stamina > 0:
            stats_lines.append(f"Stamina: {current_stamina}/{comp_max_stamina}")
        if comp_max_mana > 0:
            stats_lines.append(f"Mana: {current_mana}/{comp_max_mana}")
        
        if skill_power != 1.0:
            stats_lines.append(f"Skill Power: {skill_power:.2f}x")
        
        for line in stats_lines:
            t = ui_font.render(line, True, (220, 220, 220))
            screen.blit(t, (left_x + 20, y))
            y += 24
        
        # Perks
        mid_x = w // 2 - 100
        y = 90
        perks_title = ui_font.render("Perks:", True, (220, 220, 180))
        screen.blit(perks_title, (mid_x, y))
        y += 28
        
        perk_ids: List[str] = []
        if comp is not None:
            perk_ids = getattr(comp, "perks", []) or []
        
        if not perk_ids:
            placeholder = ui_font.render("This companion has no perks yet.", True, (180, 180, 180))
            screen.blit(placeholder, (mid_x, y))
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
                    line = f"- {pretty_name}"
                else:
                    branch = getattr(perk_def, "branch_name", None)
                    if branch:
                        line = f"- {branch}: {perk_def.name}"
                    else:
                        line = f"- {perk_def.name}"
                t = ui_font.render(line, True, (210, 210, 210))
                screen.blit(t, (mid_x, y))
                y += 22
    
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
        
        for i, item_id in enumerate(visible_items):
            actual_index = visible_start + i
            item_def = get_item_def(item_id)
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
            selected_def = get_item_def(selected_id)

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
