from __future__ import annotations

from dataclasses import dataclass
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
    from engine.core.game import Game
    from systems.inventory import Inventory, ItemDef

# UI Constants
# Colors
COLOR_TITLE = (240, 240, 200)
COLOR_SUBTITLE = (220, 220, 180)
COLOR_TEXT = (220, 220, 220)
COLOR_TEXT_DIM = (200, 200, 200)
COLOR_TEXT_DIMMER = (180, 180, 180)
COLOR_TEXT_DIMMEST = (170, 170, 170)
COLOR_GOLD = (230, 210, 120)
COLOR_CATEGORY = (200, 200, 150)
COLOR_STATUS = (180, 200, 220)
COLOR_SELECTED_BG = (60, 60, 90, 210)
COLOR_SELECTED_TEXT = (255, 255, 200)
COLOR_TAB_ACTIVE = (255, 255, 200)
COLOR_TAB_INACTIVE = (150, 150, 150)
COLOR_FOOTER = (160, 160, 160)

# Spacing
MARGIN_X = 40
MARGIN_Y_TOP = 30
MARGIN_Y_START = 90
MARGIN_Y_FOOTER = 50
LINE_HEIGHT_SMALL = 22
LINE_HEIGHT_MEDIUM = 24
LINE_HEIGHT_LARGE = 26
LINE_HEIGHT_TITLE = 28
LINE_HEIGHT_ITEM = 38
SPACING_SECTION = 30

# Layout
TAB_SPACING = 120
TAB_X_OFFSET = 400
INDENT_DEFAULT = 20
INDENT_INFO = 24

# Item display
MAX_DESC_LENGTH = 80
ITEM_NAME_HEIGHT = 20
ITEM_INFO_HEIGHT = 18
ITEM_MIN_SPACING = 4


def _safe_getattr(game: "Game", attr: str, default: Any = None) -> Any:
    """
    Helper to safely get attributes from game object with a default.
    Reduces repetition of getattr(game, ...) calls.
    """
    return getattr(game, attr, default)


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
    if len(desc) > MAX_DESC_LENGTH:
        desc = desc[: MAX_DESC_LENGTH - 3] + "..."

    if stats_summary:
        return f"{stats_summary}  |  {desc}"
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
    party_list: List[CompanionState] = _safe_getattr(game, "party") or []
    total_slots = 1 + len(party_list)
    
    focus_index = int(_safe_getattr(game, focus_index_attr, 0))
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
        hero_stats = _safe_getattr(game, "hero_stats")
        if hero_stats is not None:
            stats_parts.extend([
                f"HP {hero_stats.max_hp}",
                f"ATK {hero_stats.attack_power}",
                f"DEF {hero_stats.defense}",
            ])
            if include_resources:
                max_stamina = int(_safe_getattr(hero_stats, "max_stamina", 0))
                max_mana = int(_safe_getattr(hero_stats, "max_mana", 0))
                if max_stamina <= 0:
                    max_stamina = int(_safe_getattr(game.player, "max_stamina", 0))
                if max_mana <= 0:
                    max_mana = int(_safe_getattr(game.player, "max_mana", 0))
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
                max_stamina = int(_safe_getattr(comp, "max_stamina", 0))
                max_mana = int(_safe_getattr(comp, "max_mana", 0))
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
        hero_name = _safe_getattr(game.hero_stats, "hero_name", "Adventurer")
        display_name = hero_name
        inv = _safe_getattr(game, "inventory")
        equipped_map = inv.equipped if inv is not None else {}
    else:
        if comp is not None:
            display_name = _safe_getattr(comp, "name_override")
            if not display_name and template is not None:
                display_name = template.name
            if not display_name:
                display_name = "Companion"
            equipped_map = _safe_getattr(comp, "equipped") or {}
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
    inv = _safe_getattr(game, "inventory")
    if inv is not None:
        hero_name = _safe_getattr(game.hero_stats, "hero_name", "Hero")
        for slot, item_id in inv.equipped.items():
            if item_id:
                if item_id not in equipped_by:
                    equipped_by[item_id] = []
                equipped_by[item_id].append((hero_name, slot))
    
    # Companions' equipped items
    party_list: List[CompanionState] = _safe_getattr(game, "party") or []
    for comp in party_list:
        if not isinstance(comp, CompanionState):
            continue
        comp_equipped = _safe_getattr(comp, "equipped") or {}
        comp_name = _safe_getattr(comp, "name_override")
        if not comp_name:
            from systems.party import get_companion
            try:
                template_id = _safe_getattr(comp, "template_id")
                if template_id:
                    template = get_companion(template_id)
                    comp_name = _safe_getattr(template, "name", "Companion")
            except (KeyError, AttributeError):
                comp_name = "Companion"
        
        for slot, item_id in comp_equipped.items():
            if item_id:
                if item_id not in equipped_by:
                    equipped_by[item_id] = []
                equipped_by[item_id].append((comp_name, slot))
    
    return equipped_by


def _render_category_header(
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


@dataclass
class ProcessedInventory:
    """Container for processed inventory data."""
    flat_list: List[Tuple[Optional[str], str]]  # (item_id or None, slot) tuples
    item_indices: List[int]  # Indices in flat_list that are actual items
    flat_to_global: Dict[int, int]  # Map from flat_idx to global item index
    sorted_items: List[str]  # Sorted item IDs
    all_equipped: Dict[str, List[Tuple[str, str]]]  # item_id -> list of (char_name, slot)


def _render_inventory_item_list(
    screen: pygame.Surface,
    ui_font: pygame.font.Font,
    flat_list: List[Tuple[Optional[str], str]],
    item_indices: List[int],
    flat_to_global: Dict[int, int],
    visible_start: int,
    visible_end: int,
    cursor: int,
    all_equipped: Dict[str, List[Tuple[str, str]]],
    right_x: int,
    y: int,
    w: int,
) -> Tuple[int, Dict[str, Tuple[int, int, int, int]]]:
    """
    Render the inventory item list with scrolling and selection.
    
    Args:
        screen: Surface to render on
        ui_font: Font to use
        flat_list: List of (item_id or None, slot) tuples
        item_indices: List of flat_list indices that are actual items
        flat_to_global: Map from flat_idx to global item index
        visible_start: First visible item index
        visible_end: Last visible item index (exclusive)
        cursor: Current cursor position (global index)
        all_equipped: Dictionary of item_id -> list of (char_name, slot) tuples
        right_x: X position to start rendering
        y: Y position to start rendering
        w: Screen width
    
    Returns:
        Tuple of (final_y_position, item_positions_dict)
        item_positions: item_id -> (x, y, width, height) for hover detection
    """
    # Track last shown category to avoid duplicate headers
    last_shown_category: Optional[str] = None
    
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
                y = _render_category_header(screen, ui_font, slot, right_x, y)
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
                    y = _render_category_header(screen, ui_font, slot, right_x, y)
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
                
                # Calculate item height for hover detection
                item_start_y = y
                item_height = ITEM_NAME_HEIGHT  # Name line
                
                # One-line stats/description, slightly dimmer and indented.
                # Show extra info (description) for the currently selected item.
                info_line = _build_item_info_line(item_def, include_description=is_selected)
                if info_line:
                    item_height += ITEM_INFO_HEIGHT
                else:
                    item_height += ITEM_MIN_SPACING
                
                # Store item position for hover detection
                item_rect_x = right_x - 10
                item_rect_y = item_start_y - 2
                item_rect_width = w - right_x - 80
                item_rect_height = item_height + 4
                item_positions[item_id] = (item_rect_x, item_rect_y, item_rect_width, item_rect_height)
                
                # Highlight selected item with background
                if is_selected:
                    bg = pygame.Surface((item_rect_width, item_rect_height), pygame.SRCALPHA)
                    bg.fill(COLOR_SELECTED_BG)
                    screen.blit(bg, (item_rect_x, item_rect_y))
                
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
                y += ITEM_NAME_HEIGHT

                # One-line stats/description, slightly dimmer and indented.
                # Show extra info (description) for the currently selected item.
                if info_line:
                    info_color = (200, 200, 180) if is_selected else COLOR_TEXT_DIMMEST
                    info_surf = ui_font.render(info_line, True, info_color)
                    screen.blit(info_surf, (right_x + INDENT_INFO, y))
                    y += ITEM_INFO_HEIGHT
                else:
                    # Small extra spacing if no info line, to keep rows readable
                    y += ITEM_MIN_SPACING
    
    return y, item_positions


def _process_inventory_items(
    inv: "Inventory",
    game: "Game",
    filter_mode: Any,  # FilterMode enum
    sort_mode: Any,  # SortMode enum
    search_query: str,
) -> ProcessedInventory:
    """
    Process inventory items: filter, sort, group, and build display structure.
    
    Args:
        inv: Inventory object
        game: Game instance (for getting all equipped items)
        filter_mode: FilterMode enum value
        sort_mode: SortMode enum value
        search_query: Search query string
    
    Returns:
        ProcessedInventory with all processed data
    """
    from ui.inventory_enhancements import filter_items, sort_items, search_items
    
    all_items = list(inv.items)
    all_equipped = _get_all_equipped_items(game)
    
    # Apply search first
    filtered_items = search_items(all_items, search_query)
    
    # Apply filter
    filtered_items = filter_items(filtered_items, filter_mode, inv, all_equipped)
    
    # Apply sorting
    sorted_items = sort_items(filtered_items, sort_mode)
    
    # Group items by slot/category (for display with category headers)
    items_by_slot: Dict[str, List[str]] = {}
    for item_id in sorted_items:
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
    slot_order = ["weapon", "helmet", "armor", "gloves", "boots", "shield", "cloak", "ring", "amulet", "consumable", "misc"]
    
    # If sorting is not default, don't show category headers
    from ui.inventory_enhancements import SortMode
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
            item_def = get_item_def(item_id)
            slot = item_def.slot if item_def else "misc"
            flat_list.append((item_id, slot))
    
    # Find the actual item indices (skip category headers)
    item_indices = [i for i, (item_id, _) in enumerate(flat_list) if item_id is not None]
    
    # Build a map of flat_idx -> item_global_idx for quick lookup
    flat_to_global = {}
    for global_idx, flat_idx in enumerate(item_indices):
        flat_to_global[flat_idx] = global_idx
    
    return ProcessedInventory(
        flat_list=flat_list,
        item_indices=item_indices,
        flat_to_global=flat_to_global,
        sorted_items=sorted_items,
        all_equipped=all_equipped,
    )


def _calculate_character_stats(
    game: "Game",
    is_hero: bool,
    comp: Optional[CompanionState] = None,
) -> CharacterStats:
    """
    Calculate stats for hero or companion.
    
    Args:
        game: Game instance
        is_hero: True if hero, False if companion
        comp: Companion state (required if is_hero is False)
    
    Returns:
        CharacterStats with all calculated stats
    """
    if is_hero:
        hp = getattr(game.player, "hp", 0)
        max_hp = getattr(game.player, "max_hp", 0)
        atk = game.hero_stats.attack_power
        defense = game.hero_stats.defense
        skill_power = game.hero_stats.skill_power
        
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
        
        return CharacterStats(
            hp=hp,
            max_hp=max_hp,
            attack=atk,
            defense=defense,
            skill_power=skill_power,
            max_stamina=hero_max_stamina,
            current_stamina=current_stamina,
            max_mana=hero_max_mana,
            current_mana=current_mana,
        )
    else:
        # Companion
        if comp is None:
            return CharacterStats(
                hp=0, max_hp=1, attack=0, defense=0, skill_power=1.0
            )
        
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
        
        return CharacterStats(
            hp=hp,
            max_hp=max_hp,
            attack=atk,
            defense=defense,
            skill_power=skill_power,
            max_stamina=comp_max_stamina,
            current_stamina=current_stamina,
            max_mana=comp_max_mana,
            current_mana=current_mana,
        )


def _render_stats_section(
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
    stats_title = ui_font.render("Stats:", True, (220, 220, 180))
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
        t = ui_font.render(line, True, (220, 220, 220))
        screen.blit(t, (x + 20, y))
        y += 24
    
    return y


def _get_character_header_info(
    game: "Game",
    is_hero: bool,
    comp: Optional[CompanionState] = None,
    template: Optional[CompanionDef] = None,
) -> CharacterHeaderInfo:
    """
    Extract header info for hero or companion.
    
    Returns:
        CharacterHeaderInfo with all header display data
    """
    if is_hero:
        hero_name = getattr(
            game.hero_stats,
            "hero_name",
            getattr(game.player, "name", "Adventurer"),
        )
        class_id = getattr(game.hero_stats, "hero_class_id", "unknown")
        class_str = class_id.capitalize()
        level = game.hero_stats.level
        xp = game.hero_stats.xp
        xp_next = game.hero_stats.xp_to_next()
        gold = int(getattr(game.hero_stats, "gold", 0))
        return CharacterHeaderInfo(
            name=hero_name,
            class_name=class_str,
            level=level,
            xp=xp,
            xp_next=xp_next,
            gold=gold,
        )
    else:
        # Companion
        if comp is None:
            comp_name = "Companion"
            role = "Companion"
            level = 1
            xp = 0
            xp_next = None
        else:
            if template is not None:
                base_name = getattr(template, "name", "Companion")
                role = getattr(template, "role", "Companion")
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
        
        return CharacterHeaderInfo(
            name=comp_name,
            class_name=role,
            level=level,
            xp=xp,
            xp_next=xp_next,
            gold=None,  # Companions don't have gold
        )


def _render_character_header(
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
        gold_line = ui_font.render(f"Gold: {header_info.gold}", True, (230, 210, 120))
        screen.blit(gold_line, (x, y))
        y += 30
    else:
        y += 4  # Small spacing if no gold line
    
    return y


def _render_perks_section(
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
    perks_title = ui_font.render("Perks:", True, (220, 220, 180))
    screen.blit(perks_title, (x, y))
    y += 28
    
    if not perk_ids:
        no_perks = ui_font.render(empty_message, True, (180, 180, 180))
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
    title_surf = ui_font.render(title, True, COLOR_TITLE)
    screen.blit(title_surf, (MARGIN_X, MARGIN_Y_TOP))
    
    # Tab indicators
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


def _draw_screen_footer(
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


def draw_inventory_fullscreen(game: "Game") -> None:
    """Full-screen inventory view."""
    screen = game.screen
    ui_font = game.ui_font
    w, h = screen.get_size()
    
    # Fill background
    screen.fill(COLOR_BG)
    
    # Get available screens for tabs
    available_screens = ["inventory", "character", "skills"]
    if _safe_getattr(game, "show_shop", False):
        available_screens.append("shop")
    
    # Draw header with tabs
    _draw_screen_header(screen, ui_font, "Inventory", "inventory", available_screens, w)
    
    inv = _safe_getattr(game, "inventory")
    
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
    left_x = MARGIN_X
    y = MARGIN_Y_START
    
    # Character name
    char_title = ui_font.render(title_text, True, COLOR_TITLE)
    screen.blit(char_title, (left_x, y))
    y += SPACING_SECTION
    
    # Stats
    if stats_line_text:
        stats_surf = ui_font.render(stats_line_text, True, COLOR_TEXT_DIM)
        screen.blit(stats_surf, (left_x, y))
        y += SPACING_SECTION
    
    # Equipped section
    y = _draw_equipment_section(screen, ui_font, left_x, y, equipped_map, indent=INDENT_DEFAULT)
    
    # Right column: Backpack items
    right_x = w // 2 + MARGIN_X
    y = MARGIN_Y_START
    
    backpack_title = ui_font.render("Backpack:", True, COLOR_SUBTITLE)
    screen.blit(backpack_title, (right_x, y))
    y += LINE_HEIGHT_TITLE
    
    # Show filter/sort/search status
    from ui.inventory_enhancements import FilterMode, SortMode
    filter_mode = _safe_getattr(game, "inventory_filter", FilterMode.ALL)
    sort_mode = _safe_getattr(game, "inventory_sort", SortMode.DEFAULT)
    search_query = _safe_getattr(game, "inventory_search", "") or ""
    
    status_lines = []
    if filter_mode != FilterMode.ALL:
        status_lines.append(f"Filter: {filter_mode.value}")
    if sort_mode != SortMode.DEFAULT:
        status_lines.append(f"Sort: {sort_mode.value}")
    if search_query:
        status_lines.append(f"Search: {search_query}")
    
    if status_lines:
        status_text = " | ".join(status_lines)
        status_surf = ui_font.render(status_text, True, COLOR_STATUS)
        screen.blit(status_surf, (right_x, y))
        y += LINE_HEIGHT_MEDIUM
    
    if not inv or not getattr(inv, "items", None):
        none = ui_font.render("You are not carrying anything yet.", True, COLOR_TEXT_DIMMER)
        screen.blit(none, (right_x, y))
    else:
        # Process inventory items: filter, sort, group, and build display structure
        processed = _process_inventory_items(inv, game, filter_mode, sort_mode, search_query)
        
        # Extract processed data
        flat_list = processed.flat_list
        item_indices = processed.item_indices
        flat_to_global = processed.flat_to_global
        all_equipped = processed.all_equipped
        
        # Get cursor position and handle empty inventory
        cursor = int(_safe_getattr(game, "inventory_cursor", 0))
        
        if not item_indices:
            none = ui_font.render("You are not carrying anything yet.", True, (180, 180, 180))
            screen.blit(none, (right_x, y))
        else:
            # Clamp cursor to valid range
            cursor = max(0, min(cursor, len(item_indices) - 1))
            game.inventory_cursor = cursor
            
            # Calculate scroll offset to keep cursor visible
            page_size = int(_safe_getattr(game, "inventory_page_size", 20))
            start_y = y
            line_height = LINE_HEIGHT_ITEM  # Approximate height per item (including stats line)
            max_visible_lines = (h - start_y - 100) // line_height  # Leave space for footer
            
            # Calculate which items to show (scroll to keep cursor visible)
            visible_start = max(0, cursor - max_visible_lines // 2)
            visible_end = min(len(item_indices), visible_start + max_visible_lines)
            
            # Render the item list
            y, item_positions = _render_inventory_item_list(
                screen, ui_font, flat_list, item_indices, flat_to_global,
                visible_start, visible_end, cursor, all_equipped,
                right_x, y, w
            )
                        
            
            # Scroll info
            if len(item_indices) > max_visible_lines:
                first_index = visible_start + 1
                last_index = min(visible_end, len(item_indices))
                scroll_text = f"Items {first_index}-{last_index} of {len(item_indices)}"
                scroll_surf = ui_font.render(scroll_text, True, (150, 150, 150))
                screen.blit(scroll_surf, (right_x, y + 10))
            
            # Check for mouse hover on items for tooltips using tracked positions
            tooltip = _safe_getattr(game, "tooltip")
            if tooltip:
                mx, my = tooltip.mouse_pos
                hover_item_id = None
                hover_item_def = None
                
                # Check each item's actual position for hover
                for item_id, (rect_x, rect_y, rect_width, rect_height) in item_positions.items():
                    item_rect = pygame.Rect(rect_x, rect_y, rect_width, rect_height)
                    if item_rect.collidepoint(mx, my):
                        hover_item_def = get_item_def(item_id)
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
    tooltip = _safe_getattr(game, "tooltip")
    if tooltip:
        tooltip.draw(screen, ui_font)
    
    # Footer hints
    hints = [
        "Up/Down: select item | Enter/Space: equip | Q/E: switch character | PgUp/PgDn: page",
        "F1-F7: filter | Ctrl+S: sort | Ctrl+F: search | Ctrl+R: reset | TAB: switch screen | I/ESC: close"
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
    if _safe_getattr(game, "show_shop", False):
        available_screens.append("shop")
    
    # Draw header with tabs
    _draw_screen_header(screen, ui_font, "Character Sheet", "character", available_screens, w)
    
    # Resolve focus character
    focused_is_hero, focused_comp, focused_template = _resolve_focus_character(
        game, "character_sheet_focus_index", use_clamp=True
    )
    
    # Get focus index and party list for party preview section
    focus_index = int(_safe_getattr(game, "character_sheet_focus_index", 0))
    party_list: List[CompanionState] = _safe_getattr(game, "party") or []
    total_slots = 1 + len(party_list)
    if total_slots <= 1:
        focus_index = 0
    else:
        focus_index = max(0, min(focus_index, total_slots - 1))
    
    y = 90
    
    if focused_is_hero:
        # Hero info - left column
        left_x = 40
        
        # Get header info and render header
        header_info = _get_character_header_info(game, is_hero=True)
        y = _render_character_header(screen, ui_font, header_info, game.floor, left_x, y)
        
        # Get stats for display
        stats = _calculate_character_stats(game, is_hero=True)
        class_id = getattr(game.hero_stats, "hero_class_id", "unknown")
        class_str = class_id.capitalize()
        hero_name = header_info.name
        
        # Render stats section
        y = _render_stats_section(screen, ui_font, stats, left_x, y)
        
        # Perks - middle column
        mid_x = w // 2 - 100
        y = 90
        perk_ids = getattr(game.hero_stats, "perks", []) or []
        y = _render_perks_section(
            screen, ui_font, perk_ids, mid_x, y,
            empty_message="None yet. Level up to choose perks!"
        )
        
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
        
        # Get header info and render header
        header_info = _get_character_header_info(
            game, is_hero=False, comp=comp, template=focused_template
        )
        y = _render_character_header(screen, ui_font, header_info, game.floor, left_x, y)
        
        # Get and render stats section
        stats = _calculate_character_stats(game, is_hero=False, comp=comp)
        y = _render_stats_section(screen, ui_font, stats, left_x, y)
        
        # Perks
        mid_x = w // 2 - 100
        y = 90
        perk_ids: List[str] = []
        if comp is not None:
            perk_ids = getattr(comp, "perks", []) or []
        y = _render_perks_section(
            screen, ui_font, perk_ids, mid_x, y,
            empty_message="This companion has no perks yet."
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
    if _safe_getattr(game, "show_shop", False):
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


def draw_recruitment_fullscreen(game: "Game") -> None:
    """Full-screen recruitment view for hiring companions."""
    screen = game.screen
    ui_font = game.ui_font
    w, h = screen.get_size()
    
    # Fill background
    screen.fill(COLOR_BG)
    
    # Get available screens for tabs
    available_screens = ["inventory", "character", "skills"]
    if _safe_getattr(game, "show_shop", False):
        available_screens.append("shop")
    if _safe_getattr(game, "show_recruitment", False):
        available_screens.append("recruitment")
    
    # Draw header with tabs
    _draw_screen_header(screen, ui_font, "Companion Recruitment", "recruitment", available_screens, w)
    
    # Get available companions
    from systems.village.companion_generation import AvailableCompanion
    available_companions: List[AvailableCompanion] = getattr(game, "available_companions", [])
    
    # Get party info
    party_list: List[CompanionState] = getattr(game, "party", None) or []
    current_party_size = 1 + len(party_list)  # Hero + companions
    max_party_size = 4
    
    # Gold display
    gold_value = int(getattr(getattr(game, "hero_stats", None), "gold", 0))
    gold_line = ui_font.render(f"Your gold: {gold_value}", True, (230, 210, 120))
    screen.blit(gold_line, (40, 70))
    
    # Party size indicator
    party_size_text = f"Party: {current_party_size}/{max_party_size}"
    party_color = (200, 200, 200) if current_party_size < max_party_size else (255, 150, 150)
    party_line = ui_font.render(party_size_text, True, party_color)
    screen.blit(party_line, (w - 250, 70))
    
    # Left column: Available companions list
    left_x = 40
    y = 110
    
    title = ui_font.render("Available Companions:", True, (220, 220, 180))
    screen.blit(title, (left_x, y))
    y += 28
    
    cursor = int(getattr(game, "recruitment_cursor", 0))
    
    if not available_companions:
        msg = ui_font.render("No companions are available for recruitment.", True, (190, 190, 190))
        screen.blit(msg, (left_x, y))
    else:
        max_companions = len(available_companions)
        line_height = 28
        if max_companions > 0:
            cursor = max(0, min(cursor, max_companions - 1))
        
        # Show companions
        visible_start = max(0, cursor - 8)
        visible_end = min(max_companions, cursor + 12)
        visible_companions = available_companions[visible_start:visible_end]
        
        for i, available_comp in enumerate(visible_companions):
            actual_index = visible_start + i
            comp_state = available_comp.companion_state
            comp_name = available_comp.generated_name
            cost = available_comp.recruitment_cost
            
            # Get class name
            class_name = "Unknown"
            if comp_state.class_id:
                try:
                    from systems.classes import get_class
                    class_def = get_class(comp_state.class_id)
                    class_name = class_def.name
                except Exception:
                    class_name = comp_state.class_id.title()
            
            # Build label
            label = f"{actual_index + 1}) {comp_name} - {class_name} (Lv {comp_state.level})"
            
            # Cost string
            cost_str = f"{cost}g"
            can_afford = gold_value >= cost
            cost_color = (230, 210, 120) if can_afford else (200, 150, 150)
            
            if actual_index == cursor:
                # Highlight selected companion
                bg = pygame.Surface((w // 2 - 80, line_height), pygame.SRCALPHA)
                bg.fill((60, 60, 90, 210))
                screen.blit(bg, (left_x, y - 2))
                label_color = (255, 255, 200)
            else:
                label_color = (230, 230, 230)
            
            label_surf = ui_font.render(label, True, label_color)
            screen.blit(label_surf, (left_x + 20, y))
            
            cost_surf = ui_font.render(cost_str, True, cost_color)
            screen.blit(cost_surf, (left_x + w // 2 - 200, y))
            
            y += line_height
        
        # Right column: detailed info for currently selected companion
        if 0 <= cursor < max_companions:
            info_x = w // 2 + 40
            info_y = 110
            
            selected_comp = available_companions[cursor]
            comp_state = selected_comp.companion_state
            
            info_title = ui_font.render("Companion Info:", True, (220, 220, 180))
            screen.blit(info_title, (info_x, info_y))
            info_y += 26
            
            # Name and class
            comp_name = selected_comp.generated_name
            class_name = "Unknown"
            if comp_state.class_id:
                try:
                    from systems.classes import get_class
                    class_def = get_class(comp_state.class_id)
                    class_name = class_def.name
                except Exception:
                    class_name = comp_state.class_id.title()
            
            name_line = f"{comp_name} - {class_name}"
            name_surf = ui_font.render(name_line, True, (235, 235, 220))
            screen.blit(name_surf, (info_x, info_y))
            info_y += 24
            
            # Level
            level_line = f"Level: {comp_state.level}"
            level_surf = ui_font.render(level_line, True, (200, 200, 200))
            screen.blit(level_surf, (info_x, info_y))
            info_y += 24
            
            # Stats
            stats_parts = [
                f"HP: {comp_state.max_hp}",
                f"ATK: {comp_state.attack_power}",
                f"DEF: {comp_state.defense}",
            ]
            if hasattr(comp_state, "max_stamina") and comp_state.max_stamina > 0:
                stats_parts.append(f"STA: {comp_state.max_stamina}")
            if hasattr(comp_state, "max_mana") and comp_state.max_mana > 0:
                stats_parts.append(f"MANA: {comp_state.max_mana}")
            
            stats_line = "  ".join(stats_parts)
            stats_surf = ui_font.render(stats_line, True, (190, 190, 190))
            screen.blit(stats_surf, (info_x, info_y))
            info_y += 24
            
            # Perks
            if comp_state.perks:
                perks_title = ui_font.render("Perks:", True, (220, 220, 180))
                screen.blit(perks_title, (info_x, info_y))
                info_y += 24
                
                for perk_id in comp_state.perks:
                    try:
                        perk = perk_system.get(perk_id)
                        perk_line = f"  • {perk.name}"
                        perk_surf = ui_font.render(perk_line, True, (180, 200, 220))
                        screen.blit(perk_surf, (info_x, info_y))
                        info_y += 22
                    except Exception:
                        pass
            
            # Cost
            info_y += 10
            cost = selected_comp.recruitment_cost
            can_afford = gold_value >= cost
            cost_line = f"Recruitment Cost: {cost} gold"
            cost_color = (230, 210, 120) if can_afford else (255, 150, 150)
            cost_surf = ui_font.render(cost_line, True, cost_color)
            screen.blit(cost_surf, (info_x, info_y))
            info_y += 24
            
            if not can_afford:
                need_more = cost - gold_value
                need_line = f"(Need {need_more} more gold)"
                need_surf = ui_font.render(need_line, True, (255, 150, 150))
                screen.blit(need_surf, (info_x, info_y))
                info_y += 24
            
            # Backstory (if available)
            if selected_comp.backstory_snippet:
                info_y += 10
                backstory_title = ui_font.render("About:", True, (220, 220, 180))
                screen.blit(backstory_title, (info_x, info_y))
                info_y += 24
                backstory_surf = ui_font.render(selected_comp.backstory_snippet, True, (180, 180, 180))
                screen.blit(backstory_surf, (info_x, info_y))
    
    # Footer hints
    hints = [
        "Up/Down: move • Enter/Space: recruit • 1–9: quick recruit",
        "TAB: switch screen • I/C: jump to screen • ESC: close"
    ]
    _draw_screen_footer(screen, ui_font, hints, w, h)


def draw_quest_fullscreen(game: "Game") -> None:
    """Full-screen quest view for viewing and accepting quests."""
    screen = game.screen
    ui_font = game.ui_font
    w, h = screen.get_size()
    
    # Fill background
    screen.fill(COLOR_BG)
    
    # Get available screens for tabs
    available_screens = ["inventory", "character", "skills", "quests"]
    if _safe_getattr(game, "show_shop", False):
        available_screens.append("shop")
    if _safe_getattr(game, "show_recruitment", False):
        available_screens.append("recruitment")
    
    # Draw header with tabs
    _draw_screen_header(screen, ui_font, "Quests", "quests", available_screens, w)
    
    # Get elder ID and quests - if elder_id is None, show all quests
    elder_id = getattr(game, "current_elder_id", None)
    
    from systems.quests import Quest, QuestStatus
    
    available_quests: list[Quest] = [
        q for q in getattr(game, "available_quests", {}).values()
        if q.status == QuestStatus.AVAILABLE and (elder_id is None or q.quest_giver_id == elder_id)
    ]
    
    active_quests: list[Quest] = [
        q for q in getattr(game, "active_quests", {}).values()
        if q.status == QuestStatus.ACTIVE and (elder_id is None or q.quest_giver_id == elder_id)
    ]
    
    completed_quests: list[Quest] = [
        q for q in getattr(game, "active_quests", {}).values()
        if q.status == QuestStatus.COMPLETED and (elder_id is None or q.quest_giver_id == elder_id)
    ]
    
    # Determine which tab we're on
    quest_tab = getattr(game, "quest_tab", "available")
    
    # Tab selection UI
    tab_y = 70
    tab_x = 40
    tab_width = 150
    tabs = [
        ("available", f"Available ({len(available_quests)})"),
        ("active", f"Active ({len(active_quests)})"),
        ("completed", f"Completed ({len(completed_quests)})"),
    ]
    
    for tab_name, tab_label in tabs:
        tab_color = (220, 220, 180) if quest_tab == tab_name else (160, 160, 160)
        tab_surf = ui_font.render(tab_label, True, tab_color)
        screen.blit(tab_surf, (tab_x, tab_y))
        tab_x += tab_width
    
    # Get active list based on tab
    if quest_tab == "available":
        active_list = available_quests
        action_text = "Accept"
    elif quest_tab == "active":
        active_list = active_quests
        action_text = "View"
    elif quest_tab == "completed":
        active_list = completed_quests
        action_text = "Turn In"
    else:
        active_list = available_quests
        action_text = "Accept"
    
    # Left column: Quest list
    left_x = 40
    y = 110
    
    title = ui_font.render(f"{quest_tab.title()} Quests:", True, (220, 220, 180))
    screen.blit(title, (left_x, y))
    y += 28
    
    cursor = int(getattr(game, "quest_cursor", 0))
    
    if not active_list:
        msg = ui_font.render(f"No {quest_tab} quests.", True, (190, 190, 190))
        screen.blit(msg, (left_x, y))
    else:
        max_quests = len(active_list)
        line_height = 32
        if max_quests > 0:
            cursor = max(0, min(cursor, max_quests - 1))
        
        # Show quests with scrolling
        visible_start = max(0, cursor - 8)
        visible_end = min(max_quests, cursor + 10)
        visible_quests = active_list[visible_start:visible_end]
        
        for i, quest in enumerate(visible_quests):
            actual_index = visible_start + i
            
            if actual_index == cursor:
                # Highlight selected quest
                bg = pygame.Surface((w // 2 - 80, line_height), pygame.SRCALPHA)
                bg.fill((60, 60, 90, 210))
                screen.blit(bg, (left_x, y - 2))
                label_color = (255, 255, 200)
            else:
                label_color = (230, 230, 230)
            
            # Quest title
            label = f"{actual_index + 1}) {quest.title}"
            label_surf = ui_font.render(label, True, label_color)
            screen.blit(label_surf, (left_x + 20, y))
            y += line_height
    
    # Right column: Quest details
    if 0 <= cursor < len(active_list):
        info_x = w // 2 + 40
        info_y = 110
        
        selected_quest = active_list[cursor]
        
        info_title = ui_font.render("Quest Details:", True, (220, 220, 180))
        screen.blit(info_title, (info_x, info_y))
        info_y += 26
        
        # Title
        title_surf = ui_font.render(selected_quest.title, True, (235, 235, 220))
        screen.blit(title_surf, (info_x, info_y))
        info_y += 28
        
        # Description
        desc_lines = _wrap_text(selected_quest.description, ui_font, w // 2 - 80)
        for line in desc_lines:
            desc_surf = ui_font.render(line, True, (200, 200, 200))
            screen.blit(desc_surf, (info_x, info_y))
            info_y += 22
        
        info_y += 10
        
        # Objectives
        obj_title = ui_font.render("Objectives:", True, (220, 220, 180))
        screen.blit(obj_title, (info_x, info_y))
        info_y += 24
        
        for obj in selected_quest.objectives:
            progress_str = f"{obj.current_count}/{obj.target_count}"
            if obj.is_complete():
                obj_color = (150, 255, 150)  # Green for complete
                status = "✓"
            else:
                obj_color = (200, 200, 200)
                status = "○"
            
            obj_line = f"  {status} {obj.description} ({progress_str})"
            obj_surf = ui_font.render(obj_line, True, obj_color)
            screen.blit(obj_surf, (info_x, info_y))
            info_y += 22
        
        info_y += 10
        
        # Rewards
        reward_title = ui_font.render("Rewards:", True, (220, 220, 180))
        screen.blit(reward_title, (info_x, info_y))
        info_y += 24
        
        rewards = []
        if selected_quest.rewards.gold > 0:
            rewards.append(f"Gold: {selected_quest.rewards.gold}")
        if selected_quest.rewards.xp > 0:
            rewards.append(f"XP: {selected_quest.rewards.xp}")
        if selected_quest.rewards.items:
            for item_id in selected_quest.rewards.items:
                try:
                    from systems.inventory import get_item_def
                    item_def = get_item_def(item_id)
                    if item_def:
                        rewards.append(f"Item: {item_def.name}")
                except Exception:
                    rewards.append(f"Item: {item_id}")
        
        if rewards:
            for reward_str in rewards:
                reward_surf = ui_font.render(f"  • {reward_str}", True, (230, 210, 120))
                screen.blit(reward_surf, (info_x, info_y))
                info_y += 22
        else:
            no_reward = ui_font.render("  No rewards", True, (160, 160, 160))
            screen.blit(no_reward, (info_x, info_y))
            info_y += 22
        
        # Action hint
        info_y += 20
        if quest_tab == "available":
            action_hint = ui_font.render(f"Press Enter/Space to {action_text.lower()} this quest", True, (180, 220, 180))
        elif quest_tab == "completed":
            action_hint = ui_font.render(f"Press Enter/Space to {action_text.lower()} this quest", True, (220, 220, 150))
        else:
            action_hint = ui_font.render("Quest in progress", True, (200, 200, 200))
        screen.blit(action_hint, (info_x, info_y))
    
    # Footer hints
    hints = [
        f"Up/Down: move • Enter/Space: {action_text.lower()} • 1–9: quick select",
        "TAB: switch tab • I/C/T/J: jump to screen • J: toggle quests • ESC: close"
    ]
    _draw_screen_footer(screen, ui_font, hints, w, h)


def _wrap_text(text: str, font, max_width: int) -> List[str]:
    """Wrap text to fit within max_width."""
    words = text.split()
    lines = []
    current_line = []
    current_width = 0
    
    for word in words:
        word_surf = font.render(word + " ", True, (255, 255, 255))
        word_width = word_surf.get_width()
        
        if current_width + word_width > max_width and current_line:
            lines.append(" ".join(current_line))
            current_line = [word]
            current_width = word_width
        else:
            current_line.append(word)
            current_width += word_width
    
    if current_line:
        lines.append(" ".join(current_line))
    
    return lines if lines else [text]