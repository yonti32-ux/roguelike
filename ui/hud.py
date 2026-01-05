from __future__ import annotations

from typing import TYPE_CHECKING, List
import pygame

from settings import TILE_SIZE, COLOR_BG
from systems.inventory import get_item_def
from systems import perks as perk_system
from systems.input import InputAction
from world.entities import Enemy
from systems.events import get_event_def
from systems.party import CompanionDef, CompanionState, get_companion, ensure_companion_stats

if TYPE_CHECKING:
    from engine.game import Game
    from systems.inventory import Inventory


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
    hp_color = (200, 80, 80) if is_alive else (100, 50, 50)
    _draw_bar(surface, bar_x, bar_y, bar_w, bar_h, hp_ratio, (60, 30, 30), hp_color, (255, 255, 255))
    
    # HP text
    hp_text = font.render(f"{hp}/{max_hp}", True, (200, 200, 200))
    surface.blit(hp_text, (x + width - hp_text.get_width() - 4, y + 2))


# ---------------------------------------------------------------------------
# Battle HUD Components
# ---------------------------------------------------------------------------


def _draw_battle_unit_card(
    surface: pygame.Surface,
    font: pygame.font.Font,
    x: int,
    y: int,
    width: int,
    name: str,
    hp: int,
    max_hp: int,
    current_stamina: int = 0,
    max_stamina: int = 0,
    current_mana: int = 0,
    max_mana: int = 0,
    is_active: bool = False,
    is_player: bool = True,
    statuses: List = None,
) -> None:
    """
    Draw a battle unit card showing name, HP, resources, and status indicators.
    Used for party and enemy panels in battle.
    """
    if statuses is None:
        statuses = []
    
    card_h = 70
    card_surf = pygame.Surface((width, card_h), pygame.SRCALPHA)
    
    # Background color based on side and active state
    if is_active:
        bg_color = (40, 50, 60, 200) if is_player else (60, 40, 40, 200)
        border_color = (100, 150, 255) if is_player else (255, 100, 100)
    else:
        bg_color = (20, 20, 30, 180) if is_player else (30, 20, 20, 180)
        border_color = (80, 100, 120) if is_player else (120, 80, 80)
    
    card_surf.fill(bg_color)
    pygame.draw.rect(card_surf, border_color, (0, 0, width, card_h), 2)
    surface.blit(card_surf, (x, y))
    
    text_x = x + 6
    text_y = y + 4
    
    # Name
    name_color = (240, 240, 240) if is_active else (200, 200, 200)
    name_surf = font.render(name, True, name_color)
    surface.blit(name_surf, (text_x, text_y))
    text_y += 18
    
    # HP bar
    hp_ratio = hp / max_hp if max_hp > 0 else 0.0
    hp_color = (200, 80, 80) if hp > 0 else (100, 50, 50)
    hp_label = font.render(f"HP {hp}/{max_hp}", True, (220, 220, 220))
    surface.blit(hp_label, (text_x, text_y))
    text_y += 16
    _draw_bar(surface, text_x, text_y, width - 12, 8, hp_ratio, (60, 30, 30), hp_color, (255, 255, 255))
    text_y += 12
    
    # Resources (stamina/mana) - compact
    if max_stamina > 0 or max_mana > 0:
        res_parts = []
        if max_stamina > 0:
            res_parts.append(f"STA {current_stamina}/{max_stamina}")
        if max_mana > 0:
            res_parts.append(f"MP {current_mana}/{max_mana}")
        res_text = font.render(" | ".join(res_parts), True, (180, 200, 220))
        surface.blit(res_text, (text_x, text_y))
        text_y += 16
    
    # Status indicators (right side)
    icon_x = x + width - 20
    icon_y = y + 4
    _draw_status_indicators(surface, font, icon_x, icon_y, statuses=statuses, icon_spacing=14)


def _draw_battle_skill_hotbar(
    surface: pygame.Surface,
    font: pygame.font.Font,
    x: int,
    y: int,
    skills: List,
    skill_slots: List[str],
    cooldowns: dict,
    current_stamina: int,
    max_stamina: int,
    current_mana: int,
    max_mana: int,
    input_manager=None,
) -> None:
    """
    Draw a visible skill hotbar showing skill slots with key bindings,
    cooldowns, and resource costs.
    """
    slot_width = 100
    slot_height = 60
    slot_spacing = 8
    hotbar_w = len(skill_slots) * (slot_width + slot_spacing) - slot_spacing
    
    # Background panel
    panel_h = slot_height + 20
    panel_surf = pygame.Surface((hotbar_w + 20, panel_h), pygame.SRCALPHA)
    panel_surf.fill((0, 0, 0, 180))
    surface.blit(panel_surf, (x - 10, y - 10))
    
    slot_x = x
    slot_actions = [
        "SKILL_1",
        "SKILL_2", 
        "SKILL_3",
        "SKILL_4",
    ]
    
    for idx, skill_id in enumerate(skill_slots[:4]):
        if idx >= len(slot_actions):
            break
        
        # Get skill
        skill = skills.get(skill_id) if skill_id else None
        
        # Get key binding
        key_label = ""
        if input_manager is not None:
            try:
                action_map = {
                    0: InputAction.SKILL_1,
                    1: InputAction.SKILL_2,
                    2: InputAction.SKILL_3,
                    3: InputAction.SKILL_4,
                }
                if idx in action_map:
                    bound_keys = input_manager.get_bindings(action_map[idx])
                    if bound_keys:
                        key_label = pygame.key.name(list(bound_keys)[0]).upper()
            except (AttributeError, KeyError, TypeError):
                pass
        
        # Draw slot background
        slot_rect = pygame.Rect(slot_x, y, slot_width, slot_height)
        if skill:
            # Check if available (cooldown, resources)
            cooldown = cooldowns.get(skill_id, 0)
            can_use = cooldown == 0
            
            # Check resource costs
            stamina_cost = getattr(skill, "stamina_cost", 0)
            mana_cost = getattr(skill, "mana_cost", 0)
            has_resources = (stamina_cost <= current_stamina and mana_cost <= current_mana)
            can_use = can_use and has_resources
            
            bg_color = (40, 50, 40) if can_use else (30, 30, 30)
        else:
            bg_color = (20, 20, 20)
            can_use = False
        
        pygame.draw.rect(surface, bg_color, slot_rect)
        pygame.draw.rect(surface, (100, 100, 120), slot_rect, 2)
        
        if skill:
            # Skill name (truncated if too long)
            skill_name = getattr(skill, "name", skill_id)
            if len(skill_name) > 10:
                skill_name = skill_name[:8] + ".."
            name_surf = font.render(skill_name, True, (220, 220, 220) if can_use else (120, 120, 120))
            surface.blit(name_surf, (slot_x + 4, y + 4))
            
            # Key binding
            if key_label:
                key_surf = font.render(key_label, True, (200, 200, 255))
                surface.blit(key_surf, (slot_x + slot_width - key_surf.get_width() - 4, y + 4))
            
            # Cooldown
            if cooldown > 0:
                cd_surf = font.render(f"CD: {cooldown}", True, (255, 150, 150))
                surface.blit(cd_surf, (slot_x + 4, y + 20))
            
            # Resource costs
            cost_parts = []
            cost_colors = []
            if stamina_cost > 0:
                sta_color = (150, 255, 150) if stamina_cost <= current_stamina else (255, 150, 150)
                cost_parts.append(f"STA:{stamina_cost}")
                cost_colors.append(sta_color)
            if mana_cost > 0:
                mp_color = (150, 200, 255) if mana_cost <= current_mana else (255, 150, 150)
                cost_parts.append(f"MP:{mana_cost}")
                cost_colors.append(mp_color)
            
            if cost_parts:
                cost_text = " ".join(cost_parts)
                # Use first cost color, or default if none
                final_color = cost_colors[0] if cost_colors else (200, 200, 200)
                cost_surf = font.render(cost_text, True, final_color)
                surface.blit(cost_surf, (slot_x + 4, y + 36))
        else:
            # Empty slot
            if key_label:
                key_surf = font.render(key_label, True, (100, 100, 100))
                surface.blit(key_surf, (slot_x + slot_width - key_surf.get_width() - 4, y + 4))
            empty_surf = font.render("Empty", True, (80, 80, 80))
            surface.blit(empty_surf, (slot_x + 4, y + 20))
        
        slot_x += slot_width + slot_spacing


def _draw_battle_log_line(
    surface: pygame.Surface,
    font: pygame.font.Font,
    x: int,
    y: int,
    message: str,
) -> None:
    """
    Draw a single combat log line with color coding based on message content.
    """
    # Determine color based on message content
    msg_lower = message.lower()
    if any(word in msg_lower for word in ["damage", "hit", "attack", "strike"]):
        color = (255, 180, 180)  # Red for damage
    elif any(word in msg_lower for word in ["heal", "restore", "recover"]):
        color = (180, 255, 180)  # Green for healing
    elif any(word in msg_lower for word in ["skill", "ability", "cast"]):
        color = (180, 200, 255)  # Blue for skills
    elif any(word in msg_lower for word in ["defeat", "kill", "destroy"]):
        color = (255, 200, 100)  # Orange for kills
    elif any(word in msg_lower for word in ["victory", "win"]):
        color = (120, 255, 120)  # Bright green for victory
    elif any(word in msg_lower for word in ["defeat", "death", "died"]):
        color = (255, 100, 100)  # Bright red for defeat
    else:
        color = (200, 200, 200)  # Default gray
    
    log_surf = font.render(message, True, color)
    surface.blit(log_surf, (x, y))


# ---------------------------------------------------------------------------
# Exploration HUD
# ---------------------------------------------------------------------------


def draw_exploration_ui(game: "Game") -> None:
    """
    Draw the main exploration HUD + contextual hints +
    optional overlays (exploration log, battle log, character sheet, inventory).

    Overhauled layout:
    - Top-left: Compact hero panel with resources and stats
    - Mid-left: Party preview (if companions exist)
    - Mid-left: Context hints panel
    - Bottom: Enhanced message bar with controls
    """
    if game.player is None:
        return

    screen = game.screen
    ui_font = game.ui_font
    game_map = game.current_map
    player = game.player

    screen_w, screen_h = screen.get_size()

    # --- Hero panel (top-left, wider and better organized) ---
    panel_x = 8
    panel_y = 8
    panel_w = 340  # Even wider to spread content and prevent overlap

    # Gather data first
    hero_name = getattr(game.hero_stats, "hero_name", "Adventurer")
    hero_class_id = getattr(game.hero_stats, "hero_class_id", "warrior")
    hero_class_label = str(hero_class_id).capitalize()
    gold = int(getattr(game.hero_stats, "gold", 0))
    player_hp = getattr(player, "hp", 0)
    player_max_hp = max(1, getattr(player, "max_hp", 1))
    xp_cur = game.hero_stats.xp
    xp_needed = max(1, game.hero_stats.xp_to_next())
    xp_ratio = xp_cur / xp_needed
    
    hero_max_stamina = int(getattr(game.hero_stats, "max_stamina", 0))
    hero_max_mana = int(getattr(game.hero_stats, "max_mana", 0))
    if hero_max_stamina <= 0:
        hero_max_stamina = int(getattr(player, "max_stamina", 0))
    if hero_max_mana <= 0:
        hero_max_mana = int(getattr(player, "max_mana", 0))
    
    current_stamina = int(getattr(player, "current_stamina", hero_max_stamina))
    current_mana = int(getattr(player, "current_mana", hero_max_mana))
    
    gear_mods = game.inventory.total_stat_modifiers() if game.inventory else {}
    atk_base = float(getattr(game.hero_stats, "attack_power", 0))
    def_base = float(getattr(game.hero_stats, "defense", 0))
    atk_bonus = int(gear_mods.get("attack", 0))
    def_bonus = int(gear_mods.get("defense", 0))
    atk_total = atk_base + atk_bonus
    def_total = def_base + def_bonus
    atk_label = f"ATK {int(atk_total)}"
    if atk_bonus:
        atk_label += f" (+{atk_bonus})"
    def_label = f"DEF {int(def_total)}"
    if def_bonus:
        def_label += f" (+{def_bonus})"

    # Calculate panel height - ensure ALL content fits including stats
    panel_h = 8  # top padding
    panel_h += 22  # name line
    panel_h += 20  # floor/level line
    if getattr(game, "debug_reveal_map", False):
        panel_h += 20
    panel_h += 32  # HP bar (20 label + 10 bar + 2 spacing)
    panel_h += 24  # XP bar (18 label + 6 bar + 0 spacing)
    if hero_max_stamina > 0:
        panel_h += 34  # Stamina bar (20 label + 8 bar + 6 spacing)
    if hero_max_mana > 0:
        panel_h += 34  # Mana bar (20 label + 8 bar + 6 spacing)
    panel_h += 6  # spacing before stats
    panel_h += 22  # stats line (with proper height)
    panel_h += 10  # bottom padding (extra to prevent cutoff)

    # Create panel surface and draw to it (more transparent)
    panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    panel_surf.fill((0, 0, 0, 120))  # More transparent (was 200)
    
    text_x = 10
    y = 8

    # Header (proper spacing)
    name_text = ui_font.render(f"{hero_name} ({hero_class_label})", True, (245, 245, 230))
    panel_surf.blit(name_text, (text_x, y))
    gold_text = ui_font.render(f"{gold}g", True, (230, 210, 120))
    panel_surf.blit(gold_text, (panel_w - gold_text.get_width() - 10, y))
    y += 22

    floor_level_text = ui_font.render(f"Floor {game.floor} | Lv {game.hero_stats.level}", True, (220, 220, 220))
    panel_surf.blit(floor_level_text, (text_x, y))
    y += 20

    if getattr(game, "debug_reveal_map", False):
        dbg = ui_font.render("DEBUG: Full map reveal ON.", True, (240, 210, 120))
        panel_surf.blit(dbg, (text_x, y))
        y += 20

    # Resource bars (proper spacing to prevent overlap)
    bar_x = text_x
    bar_w = panel_w - 20
    bar_h = 10  # Standard bar height

    y = _draw_resource_bar_with_label(
        panel_surf, ui_font, bar_x, y, bar_w, bar_h,
        "HP", player_hp, player_max_hp,
        (230, 90, 90), (60, 30, 30), (200, 80, 80), (255, 255, 255)
    )

    xp_text = ui_font.render(f"XP {xp_cur}/{xp_needed}", True, (220, 220, 160))
    panel_surf.blit(xp_text, (bar_x, y))
    y += 18
    _draw_bar(panel_surf, bar_x, y, bar_w, 6, xp_ratio, (40, 40, 60), (190, 190, 90), (255, 255, 255))
    y += 10

    if hero_max_stamina > 0:
        current_stamina = max(0, min(current_stamina, hero_max_stamina))
        y = _draw_resource_bar_with_label(
            panel_surf, ui_font, bar_x, y, bar_w, 8,
            "STA", current_stamina, hero_max_stamina,
            (200, 230, 200), (30, 50, 30), (80, 200, 80), (255, 255, 255)
        )

    if hero_max_mana > 0:
        current_mana = max(0, min(current_mana, hero_max_mana))
        y = _draw_resource_bar_with_label(
            panel_surf, ui_font, bar_x, y, bar_w, 8,
            "MANA", current_mana, hero_max_mana,
            (180, 210, 255), (20, 40, 60), (80, 120, 220), (255, 255, 255)
        )

    # Stats line - use two-column layout for better organization
    y += 6  # Extra spacing before stats to prevent overlap
    
    # Two-column layout: ATK on left, DEF on right
    atk_text = ui_font.render(atk_label, True, (200, 200, 200))
    def_text = ui_font.render(def_label, True, (200, 200, 200))
    
    # Left column: ATK
    panel_surf.blit(atk_text, (text_x, y))
    
    # Right column: DEF (aligned to right side)
    def_x = panel_w - def_text.get_width() - 10
    panel_surf.blit(def_text, (def_x, y))

    # Blit complete panel to screen
    screen.blit(panel_surf, (panel_x, panel_y))
    hero_panel_bottom = panel_y + panel_h

    # --------------------------------------------------------------
    # Party preview (if companions exist)
    # --------------------------------------------------------------
    party_list: List[CompanionState] = getattr(game, "party", None) or []
    if party_list:
        party_panel_w = panel_w
        party_panel_x = panel_x
        party_panel_y = hero_panel_bottom + 12  # More spacing to avoid cutting stats
        card_height = 28  # Smaller cards
        card_spacing = 3
        party_panel_h = 6 + len(party_list) * (card_height + card_spacing)
        
        party_surf = pygame.Surface((party_panel_w, party_panel_h), pygame.SRCALPHA)
        party_surf.fill((0, 0, 0, 120))  # More transparent (was 180)
        
        # Title
        party_title = ui_font.render("Party", True, (220, 220, 180))
        party_surf.blit(party_title, (8, 2))
        
        # Draw companion cards
        card_y = 20
        for comp in party_list:
            if isinstance(comp, CompanionState):
                try:
                    template = get_companion(comp.template_id)
                    ensure_companion_stats(comp, template)
                    comp_name = getattr(comp, "name_override", None) or getattr(template, "name", "Companion")
                except (KeyError, Exception):
                    comp_name = getattr(comp, "name_override", None) or "Companion"
                
                comp_hp = int(getattr(comp, "hp", 0))
                comp_max_hp = int(getattr(comp, "max_hp", 1))
                is_alive = comp_hp > 0
                
                _draw_compact_unit_card(
                    party_surf, ui_font, 4, card_y, party_panel_w - 8,
                    comp_name, comp_hp, comp_max_hp, is_alive
                )
                card_y += card_height + card_spacing
        
        screen.blit(party_surf, (party_panel_x, party_panel_y))
        hero_panel_bottom = party_panel_y + party_panel_h

    # --------------------------------------------------------------
    # Contextual hints – stairs, room tag, nearby enemies, chests/events
    # --------------------------------------------------------------
    stairs_hint: str | None = None
    threat_hint: str | None = None
    chest_hint: str | None = None
    event_hint: str | None = None
    room_hint: str | None = None

    if game_map is not None:
        cx, cy = player.rect.center
        tx, ty = game_map.world_to_tile(cx, cy)

        # Stairs underfoot
        if game_map.up_stairs is not None and (tx, ty) == game_map.up_stairs:
            stairs_hint = "On stairs up – press ',' to ascend."
        elif game_map.down_stairs is not None and (tx, ty) == game_map.down_stairs:
            stairs_hint = "On stairs down – press '.' to descend."

        # Room tag "vibes"
        room = game_map.get_room_at(tx, ty)
        if room is not None:
            tag = getattr(room, "tag", "generic")
            if tag == "lair":
                room_hint = "This chamber feels dangerous."
            elif tag == "treasure":
                room_hint = "You sense hidden wealth nearby."
            elif tag == "event":
                room_hint = "Something unusual is anchored in this room."
            elif tag == "start":
                room_hint = "A quiet moment before the descent."
            elif tag == "shop":
                room_hint = "A merchant waits here – find them and press E to trade."

        # Ambient nearby enemy info
        nearby = 0
        radius_tiles = 7
        radius_sq = (TILE_SIZE * radius_tiles) ** 2
        for entity in getattr(game_map, "entities", []):
            if isinstance(entity, Enemy):
                dx = entity.rect.centerx - cx
                dy = entity.rect.centery - cy
                if dx * dx + dy * dy <= radius_sq:
                    nearby += 1

        if nearby > 0:
            if nearby == 1:
                threat_hint = "You sense an enemy nearby."
            elif nearby <= 3:
                threat_hint = "Several foes prowl these halls."
            else:
                threat_hint = "The air hums with many hostile presences."

        # Chest / event proximity
        chest = None
        event_node = None
        exploration = getattr(game, "exploration", None)
        if exploration is not None:
            chest = exploration.find_chest_near_player(max_distance_px=TILE_SIZE)
            if chest is None or getattr(chest, "opened", False):
                event_node = exploration.find_event_near_player(max_distance_px=TILE_SIZE)

        if chest is not None and not getattr(chest, "opened", False):
            chest_hint = "There is a chest here – press E to open."
        elif event_node is not None:
            event_id = getattr(event_node, "event_id", "")
            event_def = get_event_def(event_id)
            if event_def is not None:
                if event_def.event_id == "shrine_of_power":
                    event_hint = "A strange shrine hums here – press E to pray."
                elif event_def.event_id == "lore_stone":
                    event_hint = "Ancient runes glow here – press E to read."
                elif event_def.event_id == "risky_cache":
                    event_hint = "A sealed cache lies here – press E to inspect."
                else:
                    event_hint = "There is something unusual here – press E to interact."
            else:
                event_hint = "There is something unusual here – press E to interact."

    context_lines: list[str] = []
    if stairs_hint:
        context_lines.append(stairs_hint)
    if room_hint:
        context_lines.append(room_hint)
    if threat_hint:
        context_lines.append(threat_hint)
    if chest_hint:
        context_lines.append(chest_hint)
    elif event_hint:
        context_lines.append(event_hint)

    if context_lines:
        line_h = 20
        ctx_h = 8 + len(context_lines) * line_h
        ctx_w = panel_w
        ctx_x = panel_x
        # Position context panel below party panel if it exists, otherwise below hero panel
        if party_list:
            party_panel_bottom = party_panel_y + party_panel_h
            ctx_y = party_panel_bottom + 8
        else:
            ctx_y = hero_panel_bottom + 10

        ctx_surf = pygame.Surface((ctx_w, ctx_h), pygame.SRCALPHA)
        ctx_surf.fill((0, 0, 0, 120))  # More transparent (was 150)
        screen.blit(ctx_surf, (ctx_x, ctx_y))

        y_ui = ctx_y + 4
        for text in context_lines:
            color = (180, 200, 220)
            if any(word in text for word in ("dangerous", "hostile", "enemy")):
                color = (220, 150, 150)
            elif "wealth" in text or "chest" in text:
                color = (220, 210, 160)
            hint_surf = ui_font.render(text, True, color)
            screen.blit(hint_surf, (ctx_x + 8, y_ui))
            y_ui += line_h

    # Bottom message band
    band_h = 52
    band_y = screen_h - band_h
    band_surf = pygame.Surface((screen_w, band_h), pygame.SRCALPHA)
    band_surf.fill((0, 0, 0, 190))
    screen.blit(band_surf, (0, band_y))

    msg_y = band_y + 8
    last_msg = getattr(game, "last_message", "")
    if last_msg:
        msg_text = ui_font.render(last_msg, True, (200, 200, 200))
        screen.blit(msg_text, (10, msg_y))

    hint_text = ui_font.render(
        "Move WASD/arrows | '.' down ',' up | E: interact | C: sheet | I: inventory | "
        "K: history | L: battle log | Z/X: zoom",
        True,
        (170, 170, 170),
    )
    screen.blit(hint_text, (10, band_y + band_h - 24))

    # Overlays: battle log
    if getattr(game, "show_battle_log", False) and getattr(game, "last_battle_log", None):
        max_lines = 8
        lines = game.last_battle_log[-max_lines:]  # type: ignore[index]

        line_height = 18
        log_width = 520
        log_height = 10 + len(lines) * line_height + 24

        overlay = pygame.Surface((log_width, log_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        overlay_x = 8
        overlay_y = 150
        screen.blit(overlay, (overlay_x, overlay_y))

        y_log = overlay_y + 6
        for line in lines:
            txt = ui_font.render(str(line), True, (220, 220, 220))
            screen.blit(txt, (overlay_x + 6, y_log))
            y_log += line_height

        close_txt = ui_font.render("Press L to hide battle log", True, (160, 160, 160))
        screen.blit(close_txt, (overlay_x + 6, overlay_y + log_height - line_height - 4))

    # Exploration log overlay
    if getattr(game, "show_exploration_log", False):
        history: List[str] = list(getattr(game, "exploration_log", []))
        if not history:
            history = ["(No messages yet.)"]

        max_lines = 10
        lines = history[-max_lines:]

        line_height = 18
        padding_x = 8
        padding_y = 6
        title_height = 22

        log_width = min(520, screen_w - 16)
        log_height = padding_y * 2 + title_height + len(lines) * line_height + 20

        overlay = pygame.Surface((log_width, log_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))

        overlay_x = screen_w - log_width - 8
        overlay_y = max(8, band_y - log_height - 8)
        screen.blit(overlay, (overlay_x, overlay_y))

        y_log = overlay_y + padding_y
        title_surf = ui_font.render(
            "Exploration Log (latest at bottom)",
            True,
            (235, 235, 210),
        )
        screen.blit(title_surf, (overlay_x + padding_x, y_log))
        y_log += title_height

        for line in lines:
            txt = ui_font.render(str(line), True, (220, 220, 220))
            screen.blit(txt, (overlay_x + padding_x, y_log))
            y_log += line_height

        close_txt = ui_font.render(
            "Press K to hide exploration log",
            True,
            (170, 170, 170),
        )
        screen.blit(
            close_txt,
            (overlay_x + padding_x, overlay_y + log_height - line_height - 4),
        )

    # Legacy merchant overlay (only when not using separate ShopScreen)
    if getattr(game, "show_shop", False) and getattr(game, "active_screen", None) is not getattr(game, "shop_screen", None):
        draw_shop_overlay(game)


# ---------------------------------------------------------------------------
# Character sheet
# ---------------------------------------------------------------------------


def _draw_character_sheet(game: "Game") -> None:
    """
    Character sheet overlay.

    Shows:
    - Focused character (hero or selected companion):
      level/XP, floor, gold, stats.
    - Hero perks (for now companions don't have their own perks yet).
    - Party preview with a marker on the focused entry and Q/E cycling.
    """
    screen = game.screen
    ui_font = game.ui_font

    # Slightly larger panel so things don't feel cramped
    width = 560
    height = 440
    ox = (screen.get_width() - width) // 2
    oy = (screen.get_height() - height) // 2

    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 210))
    screen.blit(overlay, (ox, oy))

    title = ui_font.render("Character Sheet", True, (240, 240, 200))
    screen.blit(title, (ox + 12, oy + 10))

    # Determine focus: 0 = hero, 1..N = companions
    focus_index = int(getattr(game, "character_sheet_focus_index", 0))
    party_list: List[CompanionState] = getattr(game, "party", None) or []
    total_slots = 1 + len(party_list)
    if total_slots <= 1:
        focus_index = 0
    else:
        focus_index = max(0, min(focus_index, total_slots - 1))

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
                if focused_template is not None:
                    try:
                        ensure_companion_stats(candidate, focused_template)
                    except Exception:
                        pass
            else:
                focused_is_hero = True

    y = oy + 40

    if focused_is_hero:
        # Hero core info
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
        name_line = ui_font.render(
            f"{hero_name}  ({class_str})",
            True,
            (230, 230, 230),
        )
        screen.blit(name_line, (ox + 12, y))
        y += 24

        floor_line = ui_font.render(
            f"Current Floor: {game.floor}",
            True,
            (200, 200, 200),
        )
        screen.blit(floor_line, (ox + 12, y))
        y += 22

        xp_text_str = f"Level {level}  XP {xp}/{xp_next}"
        xp_line = ui_font.render(
            xp_text_str,
            True,
            (220, 220, 180),
        )
        screen.blit(xp_line, (ox + 12, y))
        y += 22

        gold_line = ui_font.render(
            f"Gold: {game.hero_stats.gold}",
            True,
            (230, 210, 120),
        )
        screen.blit(gold_line, (ox + 12, y))
        y += 26

        # Stat breakdown (base vs gear)
        gear_mods = game.inventory.total_stat_modifiers() if game.inventory else {}
        base_max_hp = game.hero_stats.max_hp
        hp_bonus = int(gear_mods.get("max_hp", 0))
        atk_bonus = int(gear_mods.get("attack", 0))
        def_bonus = int(gear_mods.get("defense", 0))
        sp_bonus = float(gear_mods.get("skill_power", 0.0))

        stats_lines: List[str] = []
        if hp_bonus:
            stats_lines.append(
                f"HP: {hp}/{max_hp} (base {base_max_hp} +{hp_bonus} gear)"
            )
        else:
            stats_lines.append(f"HP: {hp}/{max_hp}")

        # Resource pools (only shown if non-zero).
        hero_max_stamina = int(getattr(game.hero_stats, "max_stamina", 0))
        hero_max_mana = int(getattr(game.hero_stats, "max_mana", 0))

        # Fall back to the player entity if meta-stats aren't wired yet.
        if hero_max_stamina <= 0:
            hero_max_stamina = int(getattr(game.player, "max_stamina", 0))
        if hero_max_mana <= 0:
            hero_max_mana = int(getattr(game.player, "max_mana", 0))

        current_stamina = int(getattr(game.player, "current_stamina", hero_max_stamina))
        current_mana = int(getattr(game.player, "current_mana", hero_max_mana))

        if hero_max_stamina > 0:
            current_stamina = max(0, min(current_stamina, hero_max_stamina))
            stats_lines.append(f"Stamina: {current_stamina}/{hero_max_stamina}")

        if hero_max_mana > 0:
            current_mana = max(0, min(current_mana, hero_max_mana))
            stats_lines.append(f"Mana: {current_mana}/{hero_max_mana}")

        if atk_bonus:
            stats_lines.append(
                f"ATK: {atk + atk_bonus} (base {atk} +{atk_bonus} gear)"
            )
        else:
            stats_lines.append(f"ATK: {atk}")

        if def_bonus:
            stats_lines.append(
                f"DEF: {defense + def_bonus} (base {defense} +{def_bonus} gear)"
            )
        else:
            stats_lines.append(f"DEF: {defense}")

        if abs(sp_bonus) > 1e-3:
            stats_lines.append(
                f"Skill Power: {skill_power + sp_bonus:.2f}x "
                f"(base {skill_power:.2f} +{sp_bonus:.2f})"
            )
        else:
            stats_lines.append(f"Skill Power: {skill_power:.2f}x")

    else:
        # Companion core info
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

        name_line = ui_font.render(
            f"{comp_name}  ({role})",
            True,
            (230, 230, 230),
        )
        screen.blit(name_line, (ox + 12, y))
        y += 24

        floor_line = ui_font.render(
            f"Current Floor: {game.floor}",
            True,
            (200, 200, 200),
        )
        screen.blit(floor_line, (ox + 12, y))
        y += 22

        if xp_next is not None and xp_next > 0:
            xp_text_str = f"Level {level}  XP {xp}/{xp_next}"
        else:
            xp_text_str = f"Level {level}  XP {xp}"
        xp_line = ui_font.render(
            xp_text_str,
            True,
            (220, 220, 180),
        )
        screen.blit(xp_line, (ox + 12, y))
        y += 22

        gold_line = ui_font.render(
            f"Gold: {game.hero_stats.gold}",
            True,
            (230, 210, 120),
        )
        screen.blit(gold_line, (ox + 12, y))
        y += 26

        stats_lines = [
            f"HP: {hp}/{max_hp}",
            f"ATK: {atk}",
            f"DEF: {defense}",
            f"Skill Power: {skill_power:.2f}x",
        ]

    # Render stat lines
    for line in stats_lines:
        t = ui_font.render(line, True, (220, 220, 220))
        screen.blit(t, (ox + 12, y))
        y += 20

    # Perks
    y += 8
    perks_title = ui_font.render("Perks:", True, (220, 220, 180))
    screen.blit(perks_title, (ox + 12, y))
    y += 22

    if focused_is_hero:
        perk_ids = getattr(game.hero_stats, "perks", []) or []
        if not perk_ids:
            no_perks = ui_font.render(
                "None yet. Level up to choose perks!",
                True,
                (180, 180, 180),
            )
            screen.blit(no_perks, (ox + 24, y))
            y += 20
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
                screen.blit(t, (ox + 24, y))
                y += 20
    else:
        comp = focused_comp
        perk_ids: List[str] = []
        if comp is not None:
            perk_ids = getattr(comp, "perks", []) or []

        if not perk_ids:
            placeholder = ui_font.render(
                "This companion has no perks yet.",
                True,
                (180, 180, 180),
            )
            screen.blit(placeholder, (ox + 24, y))
            y += 20
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
                screen.blit(t, (ox + 24, y))
                y += 20

    # Party preview
    y += 12
    party_title = ui_font.render("Party Preview:", True, (220, 220, 180))
    screen.blit(party_title, (ox + 12, y))
    y += 24

    hero_name_list = getattr(
        game.hero_stats,
        "hero_name",
        getattr(game.player, "name", "Adventurer"),
    )
    class_id = getattr(game.hero_stats, "hero_class_id", "unknown")
    class_str = class_id.capitalize()

    hero_selected = focus_index == 0
    hero_marker = " [*]" if hero_selected else ""
    hero_line = ui_font.render(
        f"[Hero] {hero_name_list} ({class_str}){hero_marker}",
        True,
        (230, 230, 230),
    )
    screen.blit(hero_line, (ox + 24, y))
    y += 20

    base_max_hp = getattr(game.player, "max_hp", 24)
    base_atk = getattr(game.player, "attack_power", 5)
    base_defense = getattr(game.player, "defense", 0)

    if not party_list:
        companion_line = ui_font.render(
            "[Companion] — no allies recruited yet",
            True,
            (170, 170, 190),
        )
        screen.blit(companion_line, (ox + 24, y))
        y += 20
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

                comp_max_hp = int(getattr(comp, "max_hp", base_max_hp))
                comp_atk = int(getattr(comp, "attack_power", base_atk))
                comp_defense = int(getattr(comp, "defense", base_defense))

                if template is not None:
                    name = getattr(template, "name", "Companion")
                    role = getattr(template, "role", "Companion")
                else:
                    name = getattr(comp, "name_override", None) or "Companion"
                    role = "Companion"
            elif isinstance(comp, CompanionDef):
                template = comp
                name = getattr(template, "name", "Companion")
                role = getattr(template, "role", "Companion")

                hp_factor = float(getattr(template, "hp_factor", 1.0))
                atk_factor = float(getattr(template, "attack_factor", 1.0))
                def_factor = float(getattr(template, "defense_factor", 1.0))

                comp_max_hp = max(1, int(base_max_hp * hp_factor))
                comp_atk = max(1, int(base_atk * atk_factor))
                comp_defense = int(base_defense * def_factor)
                comp_level = None
            else:
                name = getattr(comp, "name", "Ally")
                role = getattr(comp, "role", "Companion")
                comp_max_hp = base_max_hp
                comp_atk = base_atk
                comp_defense = base_defense
                comp_level = None

            lvl_prefix = f"Lv {comp_level} " if comp_level is not None else ""
            is_selected = focus_index == idx + 1
            sel_marker = " [*]" if is_selected else ""
            line = (
                f"[Companion] {lvl_prefix}{name} ({role}){sel_marker} – "
                f"HP {comp_max_hp}, ATK {comp_atk}, DEF {comp_defense}"
            )
            t = ui_font.render(line, True, (210, 210, 230))
            screen.blit(t, (ox + 24, y))
            y += 20

    hint = ui_font.render(
        "Press Q/E to switch character, C to close",
        True,
        (160, 160, 160),
    )
    screen.blit(hint, (ox + 40, oy + height - 30))


# ---------------------------------------------------------------------------
# Perk choice overlay
# ---------------------------------------------------------------------------


def draw_perk_choice_overlay(game: "Game") -> None:
    """
    Perk choice overlay, used for level-ups and events that grant a free perk.

    Expects game.pending_perk_choices to be a list of Perk objects (or None).
    """
    choices = getattr(game, "pending_perk_choices", None)
    if not choices:
        return

    screen = game.screen
    ui_font = game.ui_font

    width = 520
    height = 360
    ox = (screen.get_width() - width) // 2
    oy = (screen.get_height() - height) // 2

    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 220))
    screen.blit(overlay, (ox, oy))

    title = ui_font.render("Choose a perk", True, (240, 240, 200))
    screen.blit(title, (ox + 12, oy + 10))

    y = oy + 50
    for i, perk in enumerate(choices):
        if perk is None:
            label = f"{i + 1}) (unknown perk)"
            desc = ""
        else:
            branch = getattr(perk, "branch_name", "")
            if branch:
                label = f"{i + 1}) {branch}: {perk.name}"
            else:
                label = f"{i + 1}) {perk.name}"
            desc = getattr(perk, "description", "")

        label_surf = ui_font.render(label, True, (230, 230, 230))
        screen.blit(label_surf, (ox + 18, y))
        y += 22

        if desc:
            desc_surf = ui_font.render(str(desc), True, (190, 190, 200))
            screen.blit(desc_surf, (ox + 36, y))
            y += 30
        else:
            y += 8

    hint = ui_font.render("Press 1–3 to choose (ESC to skip)", True, (160, 160, 160))
    screen.blit(hint, (ox + 12, oy + height - 28))


# ---------------------------------------------------------------------------
# Inventory overlay (hero + companions)
# ---------------------------------------------------------------------------


def draw_inventory_overlay(game: "Game", inventory: "Inventory | None" = None) -> None:
    """
    Inventory + equipment screen overlay.

    Focus index (on Game):
        0  -> hero
        1+ -> companions from game.party

    Q/E while the inventory is open cycles the focus index (handled on Game).
    """
    screen = game.screen
    ui_font = game.ui_font
    inv = inventory if inventory is not None else getattr(game, "inventory", None)

    width = 520
    height = 420
    ox = (screen.get_width() - width) // 2
    oy = (screen.get_height() - height) // 2

    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 210))
    screen.blit(overlay, (ox, oy))

    party_list: List[CompanionState] = getattr(game, "party", None) or []
    total_slots = 1 + len(party_list)

    focus_index = int(getattr(game, "inventory_focus_index", 0))
    if total_slots <= 1:
        focus_index = 0
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
                try:
                    focused_template = get_companion(candidate.template_id)
                except KeyError:
                    focused_template = None
                else:
                    ensure_companion_stats(candidate, focused_template)

    # Resolve display name + stat line + equipped map for the focused character
    if focused_is_hero:
        hero_name = getattr(game.hero_stats, "hero_name", "Adventurer")
        title_text = f"Inventory – {hero_name}"

        hero_stats = getattr(game, "hero_stats", None)
        if hero_stats is not None:
            stats_line_text = (
                f"HP {hero_stats.max_hp}  ATK {hero_stats.attack_power}  DEF {hero_stats.defense}"
            )
        else:
            stats_line_text = ""

        equipped_map = inv.equipped if inv is not None else {}
    else:
        if focused_comp is not None:
            display_name = getattr(focused_comp, "name_override", None)
            if not display_name and focused_template is not None:
                display_name = focused_template.name
            if not display_name:
                display_name = "Companion"

            title_text = f"Inventory – {display_name}"
            stats_line_text = (
                f"HP {focused_comp.max_hp}  ATK {focused_comp.attack_power}  DEF {focused_comp.defense}"
            )
            equipped_map = getattr(focused_comp, "equipped", None) or {}
        else:
            title_text = "Inventory – Companion"
            stats_line_text = ""
            equipped_map = {}

    title = ui_font.render(title_text, True, (240, 240, 200))
    screen.blit(title, (ox + 12, oy + 10))

    # Equipped section
    y = oy + 46
    equipped_title = ui_font.render("Equipped:", True, (220, 220, 180))
    screen.blit(equipped_title, (ox + 12, y))
    y += 24

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
        screen.blit(t, (ox + 24, y))
        y += 22

    # Backpack items (shared inventory)
    y += 12
    backpack_title = ui_font.render("Backpack:", True, (220, 220, 180))
    screen.blit(backpack_title, (ox + 12, y))
    y += 24

    if not inv or not getattr(inv, "items", None):
        none = ui_font.render(
            "You are not carrying anything yet.",
            True,
            (180, 180, 180),
        )
        screen.blit(none, (ox + 24, y))
        y += 20
    else:
        items = list(inv.items)
        page_size = int(getattr(game, "inventory_page_size", 10))
        offset = int(getattr(game, "inventory_scroll_offset", 0))
        total_items = len(items)

        if total_items <= page_size:
            offset = 0
        else:
            max_offset = max(0, total_items - page_size)
            offset = max(0, min(offset, max_offset))
        game.inventory_scroll_offset = offset

        visible_items = items[offset : offset + page_size]

        for idx, item_id in enumerate(visible_items):
            item_def = get_item_def(item_id)
            if item_def is None:
                continue

            equipped_marker = ""
            if equipped_map:
                if equipped_map.get("weapon") == item_id:
                    equipped_marker = " [W]"
                elif equipped_map.get("armor") == item_id:
                    equipped_marker = " [A]"
                elif equipped_map.get("trinket") == item_id:
                    equipped_marker = " [T]"

            hotkey = f"[{idx + 1}] " if idx < 9 else ""
            line = f"{hotkey}{item_def.name}{equipped_marker}"
            t = ui_font.render(line, True, (220, 220, 220))
            screen.blit(t, (ox + 24, y))
            y += 20

        # Scroll info when there are more items than one page
        if total_items > page_size:
            first_index = offset + 1
            last_index = min(offset + page_size, total_items)
            scroll_text = (
                f"Items {first_index}-{last_index} of {total_items} (↑/↓ or PgUp/PgDn to scroll)"
            )
            scroll_surf = ui_font.render(scroll_text, True, (150, 150, 150))
            screen.blit(scroll_surf, (ox + 12, oy + height - 72))

    # Stats line + footer hints
    if stats_line_text:
        stats_surf = ui_font.render(stats_line_text, True, (200, 200, 200))
        screen.blit(stats_surf, (ox + 12, oy + height - 52))

    footer = ui_font.render(
        "1–9: equip on focused | Q/E: switch | I/ESC: close",
        True,
        (170, 170, 170),
    )
    screen.blit(footer, (ox + 12, oy + height - 30))


# ---------------------------------------------------------------------------
# Companion choice overlay (for future recruitment)
# ---------------------------------------------------------------------------


def draw_companion_choice_overlay(
    game: "Game",
    companion_defs: List[CompanionDef],
    selected_index: int | None = None,
) -> None:
    """
    Simple overlay for choosing a companion from a list of CompanionDef
    templates. Stat preview is scaled off the current hero.
    """
    screen = game.screen
    ui_font = game.ui_font

    width = 560
    height = 420
    ox = (screen.get_width() - width) // 2
    oy = (screen.get_height() - height) // 2

    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 220))
    screen.blit(overlay, (ox, oy))

    title = ui_font.render("Choose a Companion", True, (240, 240, 200))
    screen.blit(title, (ox + 12, oy + 10))

    if not companion_defs:
        msg = ui_font.render(
            "No companions available to recruit yet.",
            True,
            (200, 200, 200),
        )
        screen.blit(msg, (ox + 12, oy + 60))
        hint = ui_font.render("Press ESC to cancel.", True, (160, 160, 160))
        screen.blit(hint, (ox + 12, oy + height - 30))
        return

    base_max_hp = getattr(game.player, "max_hp", 24)
    base_atk = getattr(game.player, "attack_power", 5)
    base_defense = getattr(game.player, "defense", 0)

    y = oy + 50
    for i, comp in enumerate(companion_defs):
        if selected_index is not None and i == selected_index:
            bg = pygame.Surface((width - 24, 68), pygame.SRCALPHA)
            bg.fill((60, 60, 90, 200))
            screen.blit(bg, (ox + 12, y - 4))

        name = getattr(comp, "name", "Ally")
        role = getattr(comp, "role", "Companion")
        label = f"{i + 1}) {name} ({role})"
        label_surf = ui_font.render(label, True, (230, 230, 230))
        screen.blit(label_surf, (ox + 18, y))
        y += 22

        hp_factor = float(getattr(comp, "hp_factor", 1.0))
        atk_factor = float(getattr(comp, "attack_factor", 1.0))
        def_factor = float(getattr(comp, "defense_factor", 1.0))

        comp_max_hp = max(1, int(base_max_hp * hp_factor))
        comp_atk = max(1, int(base_atk * atk_factor))
        comp_defense = int(base_defense * def_factor)

        stats_preview = f"HP {comp_max_hp}  ATK {comp_atk}  DEF {comp_defense}"
        stats_surf = ui_font.render(stats_preview, True, (200, 200, 210))
        screen.blit(stats_surf, (ox + 36, y))
        y += 20

        tagline = getattr(comp, "tagline", "")
        if tagline:
            tag_surf = ui_font.render(str(tagline), True, (180, 180, 190))
            screen.blit(tag_surf, (ox + 36, y))
            y += 24
        else:
            y += 8

    hint = ui_font.render(
        "Press 1–3 to recruit (ESC to cancel)",
        True,
        (160, 160, 160),
    )
    screen.blit(hint, (ox + 12, oy + height - 30))


# ---------------------------------------------------------------------------
# Simple shop overlay (merchant rooms)
# ---------------------------------------------------------------------------


def draw_shop_overlay(game: "Game") -> None:
    """
    Simple shop UI overlay for merchant rooms.

    Transient fields on Game:
        - shop_stock: list of item_ids for sale
        - shop_cursor: index of highlighted entry
        - shop_mode: "buy" or "sell"
        - hero_stats.gold: current gold
    """
    screen = game.screen
    ui_font = game.ui_font

    width = 520
    height = 420
    ox = (screen.get_width() - width) // 2
    oy = (screen.get_height() - height) // 2

    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 215))
    screen.blit(overlay, (ox, oy))

    mode = getattr(game, "shop_mode", "buy")
    mode_label = "BUY" if mode == "buy" else "SELL"

    title = ui_font.render(f"Dungeon Merchant — {mode_label}", True, (240, 240, 200))
    screen.blit(title, (ox + 12, oy + 10))

    gold_value = int(getattr(getattr(game, "hero_stats", None), "gold", 0))
    gold_line = ui_font.render(f"Your gold: {gold_value}", True, (230, 210, 120))
    screen.blit(gold_line, (ox + 12, oy + 36))

    stock_buy: List[str] = list(getattr(game, "shop_stock", []))
    inv: Inventory | None = getattr(game, "inventory", None)
    cursor = int(getattr(game, "shop_cursor", 0))
    y = oy + 70

    if mode == "buy":
        active_list = stock_buy
    else:
        if inv is None:
            active_list = []
        else:
            active_list = inv.get_sellable_item_ids()

    if not active_list:
        msg_text = (
            "The merchant has nothing left to sell."
            if mode == "buy"
            else "You have nothing you're willing to sell."
        )
        msg = ui_font.render(msg_text, True, (190, 190, 190))
        screen.blit(msg, (ox + 12, y))
    else:
        max_items = len(active_list)
        line_height = 24
        if max_items > 0:
            cursor = max(0, min(cursor, max_items - 1))

        for i, item_id in enumerate(active_list):
            item_def = get_item_def(item_id)
            if item_def is None:
                name = item_id
                base_price = 0
                rarity = ""
            else:
                name = item_def.name
                base_price = int(getattr(item_def, "value", 0) or 0)
                rarity = getattr(item_def, "rarity", "")

            if mode == "buy":
                price = base_price
            else:
                price = max(1, base_price // 2) if base_price > 0 else 1

            label = f"{i + 1}) {name}"
            if rarity:
                label += f" [{rarity}]"

            price_str = f"{price}g" if mode == "buy" else f"{price}g (sell)"

            if i == cursor:
                bg = pygame.Surface((width - 24, line_height), pygame.SRCALPHA)
                bg.fill((60, 60, 90, 210))
                screen.blit(bg, (ox + 12, y - 2))

            label_surf = ui_font.render(label, True, (230, 230, 230))
            screen.blit(label_surf, (ox + 24, y))

            price_surf = ui_font.render(price_str, True, (230, 210, 120))
            screen.blit(price_surf, (ox + width - 160, y))

            y += line_height

    color = (170, 170, 170)
    if mode == "buy":
        footer_line1 = "Up/Down or W/S: move • Enter/Space: buy • 1–9: quick buy"
        footer_line2 = "TAB: switch to SELL • ESC/E/I/C: leave shop"
    else:
        footer_line1 = "Up/Down or W/S: move • Enter/Space: sell • 1–9: quick sell"
        footer_line2 = "TAB: switch to BUY • ESC/E/I/C: leave shop"

    line1_surf = ui_font.render(footer_line1, True, color)
    line2_surf = ui_font.render(footer_line2, True, color)

    base_y = oy + height - 40
    screen.blit(line1_surf, (ox + 12, base_y))
    screen.blit(line2_surf, (ox + 12, base_y + 18))


# ---------------------------------------------------------------------------
# Fullscreen screen drawing functions
# ---------------------------------------------------------------------------


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
    available_screens = ["inventory", "character"]
    if getattr(game, "show_shop", False):
        available_screens.append("shop")
    
    # Draw header with tabs
    _draw_screen_header(screen, ui_font, "Inventory", "inventory", available_screens, w)
    
    inv = getattr(game, "inventory", None)
    party_list: List[CompanionState] = getattr(game, "party", None) or []
    total_slots = 1 + len(party_list)
    
    focus_index = int(getattr(game, "inventory_focus_index", 0))
    if total_slots <= 1:
        focus_index = 0
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
                try:
                    focused_template = get_companion(candidate.template_id)
                except KeyError:
                    focused_template = None
                else:
                    ensure_companion_stats(candidate, focused_template)
    
    # Resolve display name + stats + equipment
    if focused_is_hero:
        hero_name = getattr(game.hero_stats, "hero_name", "Adventurer")
        title_text = f"{hero_name}"
        hero_stats = getattr(game, "hero_stats", None)
        if hero_stats is not None:
            # Get max values
            max_hp = hero_stats.max_hp
            atk = hero_stats.attack_power
            defense = hero_stats.defense
            max_stamina = int(getattr(hero_stats, "max_stamina", 0))
            max_mana = int(getattr(hero_stats, "max_mana", 0))
            
            # Fall back to player entity if needed
            if max_stamina <= 0:
                max_stamina = int(getattr(game.player, "max_stamina", 0))
            if max_mana <= 0:
                max_mana = int(getattr(game.player, "max_mana", 0))
            
            # Build stats line
            stats_parts = [
                f"HP {max_hp}",
                f"ATK {atk}",
                f"DEF {defense}",
            ]
            if max_stamina > 0:
                stats_parts.append(f"STA {max_stamina}")
            if max_mana > 0:
                stats_parts.append(f"MANA {max_mana}")
            stats_line_text = "  ".join(stats_parts)
        else:
            stats_line_text = ""
        equipped_map = inv.equipped if inv is not None else {}
    else:
        if focused_comp is not None:
            display_name = getattr(focused_comp, "name_override", None)
            if not display_name and focused_template is not None:
                display_name = focused_template.name
            if not display_name:
                display_name = "Companion"
            title_text = display_name
            
            # Build stats line for companion
            stats_parts = [
                f"HP {focused_comp.max_hp}",
                f"ATK {focused_comp.attack_power}",
                f"DEF {focused_comp.defense}",
            ]
            max_stamina = int(getattr(focused_comp, "max_stamina", 0))
            max_mana = int(getattr(focused_comp, "max_mana", 0))
            if max_stamina > 0:
                stats_parts.append(f"STA {max_stamina}")
            if max_mana > 0:
                stats_parts.append(f"MANA {max_mana}")
            stats_line_text = "  ".join(stats_parts)
            equipped_map = getattr(focused_comp, "equipped", None) or {}
        else:
            title_text = "Companion"
            stats_line_text = ""
            equipped_map = {}
    
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
    equipped_title = ui_font.render("Equipped:", True, (220, 220, 180))
    screen.blit(equipped_title, (left_x, y))
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
        screen.blit(t, (left_x + 20, y))
        y += 24
    
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
        items = list(inv.items)
        page_size = int(getattr(game, "inventory_page_size", 20))  # More items visible
        offset = int(getattr(game, "inventory_scroll_offset", 0))
        total_items = len(items)
        
        if total_items <= page_size:
            offset = 0
        else:
            max_offset = max(0, total_items - page_size)
            offset = max(0, min(offset, max_offset))
        game.inventory_scroll_offset = offset
        
        visible_items = items[offset : offset + page_size]
        
        for idx, item_id in enumerate(visible_items):
            item_def = get_item_def(item_id)
            if item_def is None:
                continue
            
            equipped_marker = ""
            if equipped_map:
                if equipped_map.get("weapon") == item_id:
                    equipped_marker = " [W]"
                elif equipped_map.get("armor") == item_id:
                    equipped_marker = " [A]"
                elif equipped_map.get("trinket") == item_id:
                    equipped_marker = " [T]"
            
            hotkey = f"[{idx + 1}] " if idx < 9 else ""
            line = f"{hotkey}{item_def.name}{equipped_marker}"
            t = ui_font.render(line, True, (220, 220, 220))
            screen.blit(t, (right_x, y))
            y += 22
        
        # Scroll info
        if total_items > page_size:
            first_index = offset + 1
            last_index = min(offset + page_size, total_items)
            scroll_text = f"Items {first_index}-{last_index} of {total_items}"
            scroll_surf = ui_font.render(scroll_text, True, (150, 150, 150))
            screen.blit(scroll_surf, (right_x, y + 10))
    
    # Footer hints
    hints = [
        "1–9: equip item | Q/E: switch character | TAB: switch screen | I/ESC: close"
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
    available_screens = ["inventory", "character"]
    if getattr(game, "show_shop", False):
        available_screens.append("shop")
    
    # Draw header with tabs
    _draw_screen_header(screen, ui_font, "Character Sheet", "character", available_screens, w)
    
    # Determine focus
    focus_index = int(getattr(game, "character_sheet_focus_index", 0))
    party_list: List[CompanionState] = getattr(game, "party", None) or []
    total_slots = 1 + len(party_list)
    if total_slots <= 1:
        focus_index = 0
    else:
        focus_index = max(0, min(focus_index, total_slots - 1))
    
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
                if focused_template is not None:
                    try:
                        ensure_companion_stats(candidate, focused_template)
                    except Exception:
                        pass
    
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
    available_screens = ["inventory", "character", "shop"]
    
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
        
        for i, item_id in enumerate(visible_items):
            actual_index = visible_start + i
            item_def = get_item_def(item_id)
            if item_def is None:
                name = item_id
                base_price = 0
                rarity = ""
            else:
                name = item_def.name
                base_price = int(getattr(item_def, "value", 0) or 0)
                rarity = getattr(item_def, "rarity", "")
            
            if mode == "buy":
                price = base_price
            else:
                price = max(1, base_price // 2) if base_price > 0 else 1
            
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
