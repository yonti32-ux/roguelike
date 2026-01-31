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
from ui.screen_constants import (
    COLOR_TITLE,
    COLOR_SUBTITLE,
    COLOR_TEXT,
    COLOR_TEXT_DIM,
    COLOR_TEXT_DIMMER,
    COLOR_TEXT_DIMMEST,
    COLOR_GOLD,
    COLOR_CATEGORY,
    COLOR_STATUS,
    COLOR_SELECTED_BG,
    COLOR_SELECTED_BG_BRIGHT,
    COLOR_SELECTED_TEXT,
    COLOR_TAB_ACTIVE,
    COLOR_TAB_INACTIVE,
    COLOR_FOOTER,
    COLOR_BG_PANEL,
    COLOR_BORDER_BRIGHT,
    COLOR_BORDER_DIM,
    COLOR_HOVER_BG,
    COLOR_SHADOW,
    SHADOW_OFFSET_X,
    SHADOW_OFFSET_Y,
    MARGIN_X,
    MARGIN_Y_TOP,
    MARGIN_Y_START,
    MARGIN_Y_FOOTER,
    LINE_HEIGHT_SMALL,
    LINE_HEIGHT_MEDIUM,
    LINE_HEIGHT_LARGE,
    LINE_HEIGHT_TITLE,
    LINE_HEIGHT_ITEM,
    SPACING_SECTION,
    TAB_SPACING,
    TAB_X_OFFSET,
    INDENT_DEFAULT,
    INDENT_INFO,
    MAX_DESC_LENGTH,
    ITEM_NAME_HEIGHT,
    ITEM_INFO_HEIGHT,
    ITEM_MIN_SPACING,
    ITEM_SPACING_BETWEEN,
    ITEM_PADDING_VERTICAL,
    ITEM_PADDING_HORIZONTAL,
)
from ui.screen_components import (
    CharacterHeaderInfo,
    CharacterStats,
    build_item_stats_summary,
    get_rarity_color,
    build_item_info_line,
    render_category_header,
    draw_equipment_section,
    render_stats_section,
    render_perks_section,
    render_character_header,
    draw_screen_header,
    draw_screen_footer,
)

if TYPE_CHECKING:
    from engine.core.game import Game
    from systems.inventory import Inventory, ItemDef


def _safe_getattr(game: "Game", attr: str, default: Any = None) -> Any:
    """
    Helper to safely get attributes from game object with a default.
    Reduces repetition of getattr(game, ...) calls.
    """
    return getattr(game, attr, default)


# Item utility functions are now imported from ui.screen_components


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


# Rendering functions are now imported from ui.screen_components


# CharacterHeaderInfo and CharacterStats are imported from ui.screen_components

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
    game: Optional["Game"] = None,
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
                y = render_category_header(screen, ui_font, slot, right_x, y)
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
                    y = render_category_header(screen, ui_font, slot, right_x, y)
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
                
                # Calculate item height with proper padding
                item_start_y = y
                item_content_height = ITEM_NAME_HEIGHT  # Name line
                
                # One-line stats/description, slightly dimmer and indented.
                # Show extra info (description) for the currently selected item.
                info_line = build_item_info_line(item_def, include_description=is_selected)
                if info_line:
                    item_content_height += ITEM_INFO_HEIGHT
                else:
                    item_content_height += ITEM_MIN_SPACING
                
                # Calculate item card dimensions with padding
                item_rect_x = right_x - 10 - ITEM_PADDING_HORIZONTAL
                item_rect_y = item_start_y - ITEM_PADDING_VERTICAL
                item_rect_width = w - right_x - 80 + ITEM_PADDING_HORIZONTAL * 2
                item_rect_height = item_content_height + ITEM_PADDING_VERTICAL * 2
                # Use flat_idx as unique key to handle duplicate items correctly
                # Format: (item_id, flat_idx) -> position
                item_positions[(item_id, flat_idx)] = (item_rect_x, item_rect_y, item_rect_width, item_rect_height)
                
                # Get rarity for visual styling
                rarity = getattr(item_def, "rarity", "") or ""
                base_color = get_rarity_color(rarity)
                
                # Check for hover (check mouse position if tooltip system is available)
                is_hovered = False
                if game:
                    tooltip = _safe_getattr(game, "tooltip")
                    if tooltip and hasattr(tooltip, "mouse_pos"):
                        mx, my = tooltip.mouse_pos
                        item_rect = pygame.Rect(item_rect_x, item_rect_y, item_rect_width, item_rect_height)
                        is_hovered = item_rect.collidepoint(mx, my) and not is_selected
                
                # Draw item card background with enhanced styling
                # Always draw a subtle background for better visual separation
                card_bg_alpha = 40  # Very subtle default background
                card_bg_color = COLOR_BG_PANEL
                
                if is_selected:
                    card_bg_alpha = 240
                    card_bg_color = COLOR_SELECTED_BG_BRIGHT
                elif is_hovered:
                    card_bg_alpha = 120
                    card_bg_color = COLOR_HOVER_BG
                elif equipped_marker:
                    card_bg_alpha = 80
                    card_bg_color = (*base_color[:3], card_bg_alpha)
                
                # Draw main card background
                card_bg = pygame.Surface((item_rect_width, item_rect_height), pygame.SRCALPHA)
                if equipped_marker and not is_selected and not is_hovered:
                    card_bg.fill(card_bg_color)
                else:
                    card_bg.fill((*card_bg_color[:3], card_bg_alpha))
                screen.blit(card_bg, (item_rect_x, item_rect_y))
                
                # Draw subtle border around item card
                border_alpha = 100 if is_selected else 60
                border_color = COLOR_BORDER_BRIGHT if is_selected else COLOR_BORDER_DIM
                border_surf = pygame.Surface((item_rect_width, item_rect_height), pygame.SRCALPHA)
                pygame.draw.rect(border_surf, (*border_color[:3], border_alpha), (0, 0, item_rect_width, item_rect_height), 1)
                screen.blit(border_surf, (item_rect_x, item_rect_y))
                
                # Draw rarity-colored left border accent (4px wide for better visibility)
                if rarity:
                    border_color = base_color
                    # Add subtle glow effect for higher rarities
                    if rarity.lower() in ["epic", "legendary"]:
                        # Draw a subtle glow behind the border
                        glow_width = 6
                        glow_rect = pygame.Rect(item_rect_x, item_rect_y, glow_width, item_rect_height)
                        glow_surf = pygame.Surface((glow_width, item_rect_height), pygame.SRCALPHA)
                        glow_surf.fill((*border_color[:3], 60))
                        screen.blit(glow_surf, (item_rect_x, item_rect_y))
                    border_rect = pygame.Rect(item_rect_x, item_rect_y, 4, item_rect_height)
                    pygame.draw.rect(screen, border_color, border_rect)
                
                # Adjust text position to account for padding
                text_x = right_x - ITEM_PADDING_HORIZONTAL
                text_y = y + ITEM_PADDING_VERTICAL
                
                # Item name with selection indicator + rarity tag
                selection_marker = "▶ " if is_selected else "  "
                rarity_label = f" [{rarity.capitalize()}]" if rarity else ""
                line = f"{selection_marker}{item_def.name}{rarity_label}{equipped_marker}"

                # Base color from rarity, then brighten for equipped/selected
                if is_selected:
                    item_color = tuple(min(255, c + 50) for c in base_color)
                elif equipped_marker:
                    item_color = tuple(min(255, c + 25) for c in base_color)
                elif is_hovered:
                    item_color = tuple(min(255, c + 15) for c in base_color)
                else:
                    item_color = base_color
                
                # Render with shadow for better readability
                text_shadow = ui_font.render(line, True, COLOR_SHADOW[:3])
                screen.blit(text_shadow, (text_x + SHADOW_OFFSET_X, text_y + SHADOW_OFFSET_Y))
                t = ui_font.render(line, True, item_color)
                screen.blit(t, (text_x, text_y))
                text_y += ITEM_NAME_HEIGHT

                # One-line stats/description, slightly dimmer and indented.
                # Show extra info (description) for the currently selected item.
                if info_line:
                    info_color = (200, 200, 180) if is_selected else (160, 160, 150) if is_hovered else COLOR_TEXT_DIMMEST
                    info_surf = ui_font.render(info_line, True, info_color)
                    screen.blit(info_surf, (text_x + INDENT_INFO, text_y))
                    text_y += ITEM_INFO_HEIGHT
                else:
                    # Small extra spacing if no info line, to keep rows readable
                    text_y += ITEM_MIN_SPACING
                
                # Move y position forward with proper spacing
                y = item_rect_y + item_rect_height + ITEM_SPACING_BETWEEN
    
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


# render_stats_section is now imported from ui.screen_components


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


# render_character_header is now imported from ui.screen_components


# render_perks_section, draw_screen_header, and draw_screen_footer are now imported from ui.screen_components


def draw_inventory_fullscreen(game: "Game") -> None:
    """Full-screen inventory view."""
    screen = game.screen
    ui_font = game.ui_font
    w, h = screen.get_size()
    
    # Draw gradient background
    from ui.screen_components import draw_gradient_background
    from ui.screen_constants import COLOR_GRADIENT_START, COLOR_GRADIENT_END
    draw_gradient_background(
        screen,
        0, 0, w, h,
        COLOR_GRADIENT_START,
        COLOR_GRADIENT_END,
        vertical=True
    )
    
    # Get available screens for tabs (keep consistent across screens)
    # Always include core screens, conditionally add shop
    available_screens = ["inventory", "character", "skills", "quests"]
    if _safe_getattr(game, "show_shop", False):
        available_screens.append("shop")
    if _safe_getattr(game, "show_recruitment", False):
        available_screens.append("recruitment")
    
    # Draw header with tabs
    draw_screen_header(screen, ui_font, "Inventory", "inventory", available_screens, w)
    
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
    
    # Left column: Character info and equipment (with panel background)
    left_x = MARGIN_X
    left_panel_width = w // 2 - MARGIN_X * 2
    left_panel_start_y = MARGIN_Y_START - 10
    left_panel_height = h - left_panel_start_y - MARGIN_Y_FOOTER - 20
    
    # Draw left panel background
    left_panel = pygame.Surface((left_panel_width, left_panel_height), pygame.SRCALPHA)
    left_panel.fill((*COLOR_BG_PANEL[:3], 200))
    pygame.draw.rect(left_panel, COLOR_BORDER_BRIGHT, (0, 0, left_panel_width, left_panel_height), 2)
    screen.blit(left_panel, (left_x - 10, left_panel_start_y))
    
    y = MARGIN_Y_START
    
    # Character name with shadow
    char_title = ui_font.render(title_text, True, COLOR_TITLE)
    char_title_shadow = ui_font.render(title_text, True, COLOR_SHADOW[:3])
    screen.blit(char_title_shadow, (left_x + SHADOW_OFFSET_X, y + SHADOW_OFFSET_Y))
    screen.blit(char_title, (left_x, y))
    y += SPACING_SECTION
    
    # Stats
    if stats_line_text:
        stats_surf = ui_font.render(stats_line_text, True, COLOR_TEXT_DIM)
        screen.blit(stats_surf, (left_x, y))
        y += SPACING_SECTION
    
    # Equipped section
    y = draw_equipment_section(screen, ui_font, left_x, y, equipped_map, indent=INDENT_DEFAULT)
    
    # Right column: Backpack items (with panel background)
    right_x = w // 2 + MARGIN_X
    right_panel_width = w - right_x - MARGIN_X
    right_panel_start_y = MARGIN_Y_START - 10
    right_panel_height = h - right_panel_start_y - MARGIN_Y_FOOTER - 20
    
    # Draw right panel background
    right_panel = pygame.Surface((right_panel_width, right_panel_height), pygame.SRCALPHA)
    right_panel.fill((*COLOR_BG_PANEL[:3], 200))
    pygame.draw.rect(right_panel, COLOR_BORDER_BRIGHT, (0, 0, right_panel_width, right_panel_height), 2)
    screen.blit(right_panel, (right_x - 10, right_panel_start_y))
    
    y = MARGIN_Y_START
    
    # Backpack title with shadow
    backpack_title = ui_font.render("Backpack:", True, COLOR_SUBTITLE)
    backpack_title_shadow = ui_font.render("Backpack:", True, COLOR_SHADOW[:3])
    screen.blit(backpack_title_shadow, (right_x + SHADOW_OFFSET_X, y + SHADOW_OFFSET_Y))
    screen.blit(backpack_title, (right_x, y))
    y += LINE_HEIGHT_TITLE
    
    # Show filter/sort/search status with enhanced styling
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
        # Create a subtle background panel for status indicators
        status_text = " | ".join(status_lines)
        status_surf = ui_font.render(status_text, True, COLOR_STATUS)
        status_width = status_surf.get_width()
        status_height = status_surf.get_height()
        
        # Draw background panel
        panel_padding = 6
        panel_width = status_width + panel_padding * 2
        panel_height = status_height + panel_padding * 2
        status_panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        status_panel.fill((*COLOR_BG_PANEL[:3], 200))
        pygame.draw.rect(status_panel, COLOR_BORDER_DIM, (0, 0, panel_width, panel_height), 1)
        screen.blit(status_panel, (right_x - panel_padding, y - panel_padding))
        
        # Draw text with shadow
        status_shadow = ui_font.render(status_text, True, COLOR_SHADOW[:3])
        screen.blit(status_shadow, (right_x + SHADOW_OFFSET_X, y + SHADOW_OFFSET_Y))
        screen.blit(status_surf, (right_x, y))
        y += LINE_HEIGHT_MEDIUM + 4
    
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
            # Updated line height to account for new spacing (name + info + padding + spacing)
            line_height = ITEM_NAME_HEIGHT + ITEM_INFO_HEIGHT + ITEM_PADDING_VERTICAL * 2 + ITEM_SPACING_BETWEEN
            max_visible_lines = (h - start_y - 100) // line_height  # Leave space for footer
            
            # Calculate which items to show (scroll to keep cursor visible)
            visible_start = max(0, cursor - max_visible_lines // 2)
            visible_end = min(len(item_indices), visible_start + max_visible_lines)
            
            # Render the item list
            y, item_positions = _render_inventory_item_list(
                screen, ui_font, flat_list, item_indices, flat_to_global,
                visible_start, visible_end, cursor, all_equipped,
                right_x, y, w, game
            )
            
            # Store item positions and mapping in game object for mouse interaction
            # Create a mapping from (item_id, flat_idx) to its global index for quick lookup
            # Also create a reverse mapping from item_id to all instances
            item_key_to_global_idx = {}
            item_id_to_instances = {}  # item_id -> list of (flat_idx, global_idx)
            
            for global_idx, flat_idx in enumerate(item_indices):
                item_id = flat_list[flat_idx][0]
                if item_id:
                    item_key = (item_id, flat_idx)
                    item_key_to_global_idx[item_key] = global_idx
                    if item_id not in item_id_to_instances:
                        item_id_to_instances[item_id] = []
                    item_id_to_instances[item_id].append((flat_idx, global_idx))
            
            # Store in game object for event handling
            game.inventory_item_positions = item_positions
            game.inventory_item_key_to_index = item_key_to_global_idx
            game.inventory_item_id_to_instances = item_id_to_instances
            game.inventory_flat_list = flat_list
            game.inventory_item_indices = item_indices
                        
            # Scroll info
            if len(item_indices) > max_visible_lines:
                first_index = visible_start + 1
                last_index = min(visible_end, len(item_indices))
                scroll_text = f"Items {first_index}-{last_index} of {len(item_indices)}"
                scroll_surf = ui_font.render(scroll_text, True, (150, 150, 150))
                screen.blit(scroll_surf, (right_x, y + 10))
            
            # Check for mouse hover on items for tooltips and cursor update
            tooltip = _safe_getattr(game, "tooltip")
            if tooltip:
                mx, my = tooltip.mouse_pos
                hover_item_id = None
                hover_item_def = None
                hover_global_idx = None
                
                # Check each item's actual position for hover
                # item_positions now uses (item_id, flat_idx) as keys
                for item_key, (rect_x, rect_y, rect_width, rect_height) in item_positions.items():
                    item_rect = pygame.Rect(rect_x, rect_y, rect_width, rect_height)
                    if item_rect.collidepoint(mx, my):
                        item_id, flat_idx = item_key
                        hover_item_def = get_item_def(item_id)
                        if hover_item_def:
                            hover_item_id = item_id
                            # Get the global index for this specific item instance
                            hover_global_idx = item_key_to_global_idx.get(item_key)
                            break
                
                # Update cursor position when hovering over an item
                if hover_global_idx is not None and hover_global_idx != cursor:
                    game.inventory_cursor = hover_global_idx
                
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
        "Up/Down: select item | Enter/Space/Click: equip | Q/E: switch character | PgUp/PgDn: page",
        "F1-F7: filter | Ctrl+S: sort | Ctrl+F: search | Ctrl+R: reset | TAB: switch screen | I/ESC: close"
    ]
    draw_screen_footer(screen, ui_font, hints, w, h)


def draw_character_sheet_fullscreen(game: "Game") -> None:
    """Full-screen character sheet view."""
    screen = game.screen
    ui_font = game.ui_font
    w, h = screen.get_size()
    
    # Draw gradient background
    from ui.screen_components import draw_gradient_background
    from ui.screen_constants import COLOR_GRADIENT_START, COLOR_GRADIENT_END
    draw_gradient_background(
        screen,
        0, 0, w, h,
        COLOR_GRADIENT_START,
        COLOR_GRADIENT_END,
        vertical=True
    )
    
    # Get available screens for tabs
    available_screens = ["inventory", "character", "skills", "quests"]
    if _safe_getattr(game, "show_shop", False):
        available_screens.append("shop")
    if _safe_getattr(game, "show_recruitment", False):
        available_screens.append("recruitment")
    
    # Draw header with tabs
    draw_screen_header(screen, ui_font, "Character Sheet", "character", available_screens, w)
    
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
        y = render_character_header(screen, ui_font, header_info, game.floor, left_x, y)
        
        # Get stats for display
        stats = _calculate_character_stats(game, is_hero=True)
        class_id = getattr(game.hero_stats, "hero_class_id", "unknown")
        class_str = class_id.capitalize()
        hero_name = header_info.name
        
        # Render stats section
        y = render_stats_section(screen, ui_font, stats, left_x, y)
        
        # Perks - middle column
        mid_x = w // 2 - 100
        y = 90
        perk_ids = getattr(game.hero_stats, "perks", []) or []
        y = render_perks_section(
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
        y = render_character_header(screen, ui_font, header_info, game.floor, left_x, y)
        
        # Get and render stats section
        stats = _calculate_character_stats(game, is_hero=False, comp=comp)
        y = render_stats_section(screen, ui_font, stats, left_x, y)
        
        # Perks
        mid_x = w // 2 - 100
        y = 90
        perk_ids: List[str] = []
        if comp is not None:
            perk_ids = getattr(comp, "perks", []) or []
        y = render_perks_section(
            screen, ui_font, perk_ids, mid_x, y,
            empty_message="This companion has no perks yet."
        )
    
    # Footer hints
    hints = [
        "Q/E: switch character | TAB: switch screen | C/ESC: close"
    ]
    draw_screen_footer(screen, ui_font, hints, w, h)


def _sort_items_by_type(item_ids: List[str]) -> List[str]:
    """
    Sort items by type: consumables first, then weapons, armor pieces, and accessories.
    Within each category, maintain original order.
    """
    # Define category order (lower number = appears first)
    # Grouping: consumables, weapons, armor pieces (helmet/armor/gloves/boots), 
    # shields, accessories (cloak/ring/amulet), then others
    category_order = {
        "consumable": 0,
        "weapon": 1,
        "helmet": 2,
        "armor": 3,
        "gloves": 4,
        "boots": 5,
        "shield": 6,
        "cloak": 7,
        "ring": 8,
        "amulet": 9,
    }
    
    def get_sort_key(item_id: str) -> Tuple[int, str]:
        item_def = get_item_def(item_id)
        if item_def is None:
            return (999, item_id)  # Unknown items go last
        slot = item_def.slot.lower()
        category = category_order.get(slot, 999)
        return (category, item_id)
    
    return sorted(item_ids, key=get_sort_key)


def _get_category_name(slot: str) -> str:
    """Get display name for item category."""
    category_names = {
        "consumable": "Consumables",
        "weapon": "Weapons",
        "helmet": "Helmets",
        "armor": "Armor",
        "gloves": "Gloves",
        "boots": "Boots",
        "shield": "Shields",
        "cloak": "Cloaks",
        "ring": "Rings",
        "amulet": "Amulets",
    }
    return category_names.get(slot.lower(), "Other")


def draw_shop_fullscreen(game: "Game") -> None:
    """Full-screen shop view."""
    screen = game.screen
    ui_font = game.ui_font
    w, h = screen.get_size()
    
    # Draw gradient background
    from ui.screen_components import draw_gradient_background
    from ui.screen_constants import COLOR_GRADIENT_START, COLOR_GRADIENT_END
    draw_gradient_background(
        screen,
        0, 0, w, h,
        COLOR_GRADIENT_START,
        COLOR_GRADIENT_END,
        vertical=True
    )
    
    # Get available screens for tabs
    available_screens = ["inventory", "character", "skills", "quests", "shop"]
    
    # Draw header with tabs
    draw_screen_header(screen, ui_font, "Dungeon Merchant", "shop", available_screens, w)
    
    mode = getattr(game, "shop_mode", "buy")
    mode_label = "BUY" if mode == "buy" else "SELL"
    
    gold_value = int(getattr(getattr(game, "hero_stats", None), "gold", 0))
    gold_line = ui_font.render(f"Your gold: {gold_value}", True, (230, 210, 120))
    screen.blit(gold_line, (40, 70))
    
    stock_buy: List[str] = list(getattr(game, "shop_stock", []))
    inv: Inventory | None = getattr(game, "inventory", None)
    cursor = int(getattr(game, "shop_cursor", 0))
    
    if mode == "buy":
        # Use sorted list if available, otherwise create and store it
        sorted_stock = getattr(game, "shop_stock_sorted", None)
        if sorted_stock is None:
            sorted_stock = _sort_items_by_type(stock_buy)
            game.shop_stock_sorted = sorted_stock
        active_list = sorted_stock
    else:
        if inv is None:
            active_list = []
        else:
            active_list = inv.get_sellable_item_ids()
    
    # Sort items by type (consumables first, then weapons, armor, trinkets)
    # For sell mode, also sort for consistency
    if mode == "sell":
        sorted_list = _sort_items_by_type(active_list)
    else:
        sorted_list = active_list
    
    # Left column: Buy list
    left_x = 40
    y = 110
    
    buy_title = ui_font.render(f"{mode_label} Items:", True, (220, 220, 180))
    screen.blit(buy_title, (left_x, y))
    y += 28
    
    if not sorted_list:
        msg_text = (
            "The merchant has nothing left to sell."
            if mode == "buy"
            else "You have nothing you're willing to sell."
        )
        msg = ui_font.render(msg_text, True, (190, 190, 190))
        screen.blit(msg, (left_x, y))
    else:
        max_items = len(sorted_list)
        line_height = 26
        if max_items > 0:
            cursor = max(0, min(cursor, max_items - 1))
        
        # Show more items in fullscreen
        visible_start = max(0, cursor - 10)
        visible_end = min(max_items, cursor + 15)
        visible_items = sorted_list[visible_start:visible_end]
        
        # Get floor index for economy calculations
        floor_index = getattr(game, "floor", 1)
        
        # Track current category to show headers
        last_category = None
        
        for i, item_id in enumerate(visible_items):
            actual_index = visible_start + i
            item_def = get_item_def(item_id)
            if item_def is None:
                name = item_id
                price = 0
                rarity = ""
                current_category = "Other"
            else:
                name = item_def.name
                rarity = getattr(item_def, "rarity", "")
                current_category = item_def.slot
                # Use economy system for dynamic pricing
                if mode == "buy":
                    price = calculate_shop_buy_price(item_def, floor_index)
                else:
                    price = calculate_shop_sell_price(item_def, floor_index)
            
            # Show category header when category changes
            if current_category != last_category and current_category:
                category_name = _get_category_name(current_category)
                # Add some spacing before category header
                if last_category is not None:
                    y += 4
                category_surf = ui_font.render(f"--- {category_name} ---", True, COLOR_CATEGORY)
                screen.blit(category_surf, (left_x, y))
                y += line_height
                last_category = current_category
            
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
                info_line = build_item_info_line(selected_def, include_description=True)
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
    draw_screen_footer(screen, ui_font, hints, w, h)


def draw_skill_screen_fullscreen(game: "Game") -> None:
    """Full-screen skill allocation view."""
    screen = game.screen
    ui_font = game.ui_font
    w, h = screen.get_size()
    
    # Draw gradient background
    from ui.screen_components import draw_gradient_background
    from ui.screen_constants import COLOR_GRADIENT_START, COLOR_GRADIENT_END
    draw_gradient_background(
        screen,
        0, 0, w, h,
        COLOR_GRADIENT_START,
        COLOR_GRADIENT_END,
        vertical=True
    )
    
    # Get available screens for tabs
    available_screens = ["inventory", "character", "skills", "quests"]
    if _safe_getattr(game, "show_shop", False):
        available_screens.append("shop")
    if _safe_getattr(game, "show_recruitment", False):
        available_screens.append("recruitment")
    
    # Draw header with tabs
    draw_screen_header(screen, ui_font, "Skill Allocation", "skills", available_screens, w)
    
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
    draw_screen_footer(screen, ui_font, hints, w, h)


def draw_recruitment_fullscreen(game: "Game") -> None:
    """Full-screen recruitment view for hiring companions."""
    screen = game.screen
    ui_font = game.ui_font
    w, h = screen.get_size()
    
    # Draw gradient background
    from ui.screen_components import draw_gradient_background
    from ui.screen_constants import COLOR_GRADIENT_START, COLOR_GRADIENT_END
    draw_gradient_background(
        screen,
        0, 0, w, h,
        COLOR_GRADIENT_START,
        COLOR_GRADIENT_END,
        vertical=True
    )
    
    # Get available screens for tabs
    available_screens = ["inventory", "character", "skills", "quests"]
    if _safe_getattr(game, "show_shop", False):
        available_screens.append("shop")
    if _safe_getattr(game, "show_recruitment", False):
        available_screens.append("recruitment")
    if _safe_getattr(game, "show_recruitment", False):
        available_screens.append("recruitment")
    
    # Draw header with tabs
    draw_screen_header(screen, ui_font, "Companion Recruitment", "recruitment", available_screens, w)
    
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
    draw_screen_footer(screen, ui_font, hints, w, h)


def draw_quest_fullscreen(game: "Game") -> None:
    """Full-screen quest view for viewing and accepting quests."""
    screen = game.screen
    ui_font = game.ui_font
    w, h = screen.get_size()
    
    # Draw gradient background
    from ui.screen_components import draw_gradient_background
    from ui.screen_constants import COLOR_GRADIENT_START, COLOR_GRADIENT_END
    draw_gradient_background(
        screen,
        0, 0, w, h,
        COLOR_GRADIENT_START,
        COLOR_GRADIENT_END,
        vertical=True
    )
    
    # Get available screens for tabs
    available_screens = ["inventory", "character", "skills", "quests"]
    if _safe_getattr(game, "show_shop", False):
        available_screens.append("shop")
    if _safe_getattr(game, "show_recruitment", False):
        available_screens.append("recruitment")
    
    # Draw header with tabs
    draw_screen_header(screen, ui_font, "Quests", "quests", available_screens, w)
    
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
    draw_screen_footer(screen, ui_font, hints, w, h)


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