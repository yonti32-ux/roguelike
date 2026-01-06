from __future__ import annotations

from typing import TYPE_CHECKING, List
import pygame

from settings import TILE_SIZE
from systems.events import get_event_def
from systems.party import CompanionState, get_companion, ensure_companion_stats
from world.entities import Enemy
from ui.hud_utils import _draw_bar, _draw_resource_bar_with_label, _draw_compact_unit_card

if TYPE_CHECKING:
    from engine.game import Game


def _draw_hero_panel(
    surface: pygame.Surface,
    ui_font: pygame.font.Font,
    game: "Game",
    x: int,
    y: int,
    width: int,
) -> int:
    """
    Draw the hero info panel for exploration HUD.
    
    Returns:
        Y position after the panel (for positioning next elements)
    """
    player = game.player
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

    # Calculate panel height
    panel_h = 8  # top padding
    panel_h += 22  # name line
    panel_h += 20  # floor/level line
    if getattr(game, "debug_reveal_map", False):
        panel_h += 20
    panel_h += 32  # HP bar
    panel_h += 24  # XP bar
    if hero_max_stamina > 0:
        panel_h += 34  # Stamina bar
    if hero_max_mana > 0:
        panel_h += 34  # Mana bar
    panel_h += 6  # spacing before stats
    panel_h += 22  # stats line
    panel_h += 10  # bottom padding

    # Create panel surface
    panel_surf = pygame.Surface((width, panel_h), pygame.SRCALPHA)
    panel_surf.fill((0, 0, 0, 120))
    
    text_x = 10
    y_pos = 8

    # Header
    name_text = ui_font.render(f"{hero_name} ({hero_class_label})", True, (245, 245, 230))
    panel_surf.blit(name_text, (text_x, y_pos))
    gold_text = ui_font.render(f"{gold}g", True, (230, 210, 120))
    panel_surf.blit(gold_text, (width - gold_text.get_width() - 10, y_pos))
    y_pos += 22

    floor_level_text = ui_font.render(f"Floor {game.floor} | Lv {game.hero_stats.level}", True, (220, 220, 220))
    panel_surf.blit(floor_level_text, (text_x, y_pos))
    y_pos += 20

    if getattr(game, "debug_reveal_map", False):
        dbg = ui_font.render("DEBUG: Full map reveal ON.", True, (240, 210, 120))
        panel_surf.blit(dbg, (text_x, y_pos))
        y_pos += 20

    # Resource bars
    bar_x = text_x
    bar_w = width - 20
    bar_h = 10

    y_pos = _draw_resource_bar_with_label(
        panel_surf, ui_font, bar_x, y_pos, bar_w, bar_h,
        "HP", player_hp, player_max_hp,
        (230, 90, 90), (60, 30, 30), (200, 80, 80), (255, 255, 255)
    )

    xp_text = ui_font.render(f"XP {xp_cur}/{xp_needed}", True, (220, 220, 160))
    panel_surf.blit(xp_text, (bar_x, y_pos))
    y_pos += 18
    _draw_bar(panel_surf, bar_x, y_pos, bar_w, 6, xp_ratio, (40, 40, 60), (190, 190, 90), (255, 255, 255))
    y_pos += 10

    if hero_max_stamina > 0:
        current_stamina = max(0, min(current_stamina, hero_max_stamina))
        y_pos = _draw_resource_bar_with_label(
            panel_surf, ui_font, bar_x, y_pos, bar_w, 8,
            "STA", current_stamina, hero_max_stamina,
            (200, 230, 200), (30, 50, 30), (80, 200, 80), (255, 255, 255)
        )

    if hero_max_mana > 0:
        current_mana = max(0, min(current_mana, hero_max_mana))
        y_pos = _draw_resource_bar_with_label(
            panel_surf, ui_font, bar_x, y_pos, bar_w, 8,
            "MANA", current_mana, hero_max_mana,
            (180, 210, 255), (20, 40, 60), (80, 120, 220), (255, 255, 255)
        )

    # Stats line
    y_pos += 6
    atk_text = ui_font.render(atk_label, True, (200, 200, 200))
    def_text = ui_font.render(def_label, True, (200, 200, 200))
    panel_surf.blit(atk_text, (text_x, y_pos))
    def_x = width - def_text.get_width() - 10
    panel_surf.blit(def_text, (def_x, y_pos))

    # Blit panel to surface
    surface.blit(panel_surf, (x, y))
    return y + panel_h


def _gather_context_hints(game: "Game", game_map, player) -> List[str]:
    """
    Gather contextual hints based on player position and surroundings.
    
    Returns:
        List of hint strings to display
    """
    hints: List[str] = []
    
    if game_map is None:
        return hints
    
    cx, cy = player.rect.center
    tx, ty = game_map.world_to_tile(cx, cy)

    # Stairs
    if game_map.up_stairs is not None and (tx, ty) == game_map.up_stairs:
        hints.append("On stairs up – press ',' to ascend.")
    elif game_map.down_stairs is not None and (tx, ty) == game_map.down_stairs:
        hints.append("On stairs down – press '.' to descend.")

    # Room tag
    room = game_map.get_room_at(tx, ty)
    if room is not None:
        tag = getattr(room, "tag", "generic")
        if tag == "lair":
            hints.append("This chamber feels dangerous.")
        elif tag == "treasure":
            hints.append("You sense hidden wealth nearby.")
        elif tag == "event":
            hints.append("Something unusual is anchored in this room.")
        elif tag == "start":
            hints.append("A quiet moment before the descent.")
        elif tag == "shop":
            hints.append("A merchant waits here – find them and press E to trade.")

    # Nearby enemies
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
            hints.append("You sense an enemy nearby.")
        elif nearby <= 3:
            hints.append("Several foes prowl these halls.")
        else:
            hints.append("The air hums with many hostile presences.")

    # Chest / event proximity
    exploration = getattr(game, "exploration", None)
    if exploration is not None:
        chest = exploration.find_chest_near_player(max_distance_px=TILE_SIZE)
        if chest is not None and not getattr(chest, "opened", False):
            hints.append("There is a chest here – press E to open.")
        else:
            event_node = exploration.find_event_near_player(max_distance_px=TILE_SIZE)
            if event_node is not None:
                event_id = getattr(event_node, "event_id", "")
                event_def = get_event_def(event_id)
                if event_def is not None:
                    if event_def.event_id == "shrine_of_power":
                        hints.append("A strange shrine hums here – press E to pray.")
                    elif event_def.event_id == "lore_stone":
                        hints.append("Ancient runes glow here – press E to read.")
                    elif event_def.event_id == "risky_cache":
                        hints.append("A sealed cache lies here – press E to inspect.")
                    else:
                        hints.append("There is something unusual here – press E to interact.")
                else:
                    hints.append("There is something unusual here – press E to interact.")
    
    return hints


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

    # --- Hero panel (top-left) ---
    panel_x = 8
    panel_y = 8
    panel_w = 340
    hero_panel_bottom = _draw_hero_panel(screen, ui_font, game, panel_x, panel_y, panel_w)

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

    # --- Contextual hints ---
    context_lines = _gather_context_hints(game, game_map, player)

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

