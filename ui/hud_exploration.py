from __future__ import annotations

from typing import TYPE_CHECKING, List
import pygame

from settings import TILE_SIZE
from systems.events import get_event_def
from systems.party import CompanionState, get_companion, ensure_companion_stats
from world.entities import Enemy
from ui.hud_utils import _draw_bar, _draw_resource_bar_with_label, _draw_compact_unit_card, _calculate_hp_color
from ui.ui_scaling import scale_value

if TYPE_CHECKING:
    from engine.core.game import Game


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

    # Get UI scale
    ui_scale = getattr(game, "ui_scale", 1.0)
    
    # Calculate panel height (scaled)
    panel_h = scale_value(8, ui_scale)  # top padding
    panel_h += scale_value(22, ui_scale)  # name line
    panel_h += scale_value(20, ui_scale)  # floor/level line
    if getattr(game, "debug_reveal_map", False):
        panel_h += scale_value(20, ui_scale)
    panel_h += scale_value(32, ui_scale)  # HP bar
    panel_h += scale_value(24, ui_scale)  # XP bar
    if hero_max_stamina > 0:
        panel_h += scale_value(34, ui_scale)  # Stamina bar
    if hero_max_mana > 0:
        panel_h += scale_value(34, ui_scale)  # Mana bar
    panel_h += scale_value(6, ui_scale)  # spacing before stats
    panel_h += scale_value(22, ui_scale)  # stats line
    panel_h += scale_value(10, ui_scale)  # bottom padding

    # Create panel surface
    panel_surf = pygame.Surface((width, panel_h), pygame.SRCALPHA)
    panel_surf.fill((0, 0, 0, 120))
    
    text_x = scale_value(10, ui_scale)
    y_pos = scale_value(8, ui_scale)

    # Header
    name_text = ui_font.render(f"{hero_name} ({hero_class_label})", True, (245, 245, 230))
    panel_surf.blit(name_text, (text_x, y_pos))
    gold_text = ui_font.render(f"{gold}g", True, (230, 210, 120))
    panel_surf.blit(gold_text, (width - gold_text.get_width() - scale_value(10, ui_scale), y_pos))
    y_pos += scale_value(22, ui_scale)

    floor_level_text = ui_font.render(f"Floor {game.floor} | Lv {game.hero_stats.level}", True, (220, 220, 220))
    panel_surf.blit(floor_level_text, (text_x, y_pos))
    y_pos += scale_value(20, ui_scale)

    if getattr(game, "debug_reveal_map", False):
        dbg = ui_font.render("DEBUG: Full map reveal ON.", True, (240, 210, 120))
        panel_surf.blit(dbg, (text_x, y_pos))
        y_pos += scale_value(20, ui_scale)

    # Resource bars
    bar_x = text_x
    bar_w = width - scale_value(20, ui_scale)
    bar_h = scale_value(10, ui_scale)

    # Calculate dynamic HP color based on HP percentage
    hp_ratio = player_hp / player_max_hp if player_max_hp > 0 else 0.0
    hp_color = _calculate_hp_color(hp_ratio) if player_hp > 0 else (100, 50, 50)
    y_pos = _draw_resource_bar_with_label(
        panel_surf, ui_font, bar_x, y_pos, bar_w, bar_h,
        "HP", player_hp, player_max_hp,
        (230, 90, 90), (60, 30, 30), hp_color, (255, 255, 255)
    )

    xp_text = ui_font.render(f"XP {xp_cur}/{xp_needed}", True, (220, 220, 160))
    panel_surf.blit(xp_text, (bar_x, y_pos))
    y_pos += scale_value(18, ui_scale)
    _draw_bar(panel_surf, bar_x, y_pos, bar_w, scale_value(6, ui_scale), xp_ratio, (40, 40, 60), (190, 190, 90), (255, 255, 255))
    y_pos += scale_value(10, ui_scale)

    if hero_max_stamina > 0:
        current_stamina = max(0, min(current_stamina, hero_max_stamina))
        y_pos = _draw_resource_bar_with_label(
            panel_surf, ui_font, bar_x, y_pos, bar_w, scale_value(8, ui_scale),
            "STA", current_stamina, hero_max_stamina,
            (200, 230, 200), (30, 50, 30), (80, 200, 80), (255, 255, 255)
        )

    if hero_max_mana > 0:
        current_mana = max(0, min(current_mana, hero_max_mana))
        y_pos = _draw_resource_bar_with_label(
            panel_surf, ui_font, bar_x, y_pos, bar_w, scale_value(8, ui_scale),
            "MANA", current_mana, hero_max_mana,
            (180, 210, 255), (20, 40, 60), (80, 120, 220), (255, 255, 255)
        )

    # Stats line
    y_pos += scale_value(6, ui_scale)
    atk_text = ui_font.render(atk_label, True, (200, 200, 200))
    def_text = ui_font.render(def_label, True, (200, 200, 200))
    panel_surf.blit(atk_text, (text_x, y_pos))
    def_x = width - def_text.get_width() - scale_value(10, ui_scale)
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

    # Chest / event / trap proximity
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
            else:
                # Check for traps
                from world.entities import Trap
                from systems.traps import get_trap_def
                trap = exploration.find_trap_near_player(max_distance_px=TILE_SIZE)
                if trap is not None:
                    if trap.triggered or trap.disarmed:
                        pass  # Don't show hints for inactive traps
                    elif trap.detected:
                        trap_def = get_trap_def(trap.trap_id)
                        trap_name = trap_def.name if trap_def else "trap"
                        hints.append(f"A {trap_name} is visible here – press E to disarm.")
                    else:
                        hints.append("You sense danger nearby – press E to investigate.")
    
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
    
    # Get UI scale from game
    ui_scale = getattr(game, "ui_scale", 1.0)

    # --- Hero panel (top-left) ---
    panel_x = scale_value(8, ui_scale)
    panel_y = scale_value(8, ui_scale)
    panel_w = scale_value(340, ui_scale)
    hero_panel_bottom = _draw_hero_panel(screen, ui_font, game, panel_x, panel_y, panel_w)

    # --------------------------------------------------------------
    # Party preview (if companions exist)
    # --------------------------------------------------------------
    party_list: List[CompanionState] = getattr(game, "party", None) or []
    if party_list:
        party_panel_w = panel_w
        party_panel_x = panel_x
        party_panel_y = hero_panel_bottom + scale_value(12, ui_scale)  # More spacing to avoid cutting stats
        card_height = scale_value(28, ui_scale)  # Smaller cards
        card_spacing = scale_value(3, ui_scale)
        party_panel_h = scale_value(6, ui_scale) + len(party_list) * (card_height + card_spacing)
        
        party_surf = pygame.Surface((party_panel_w, party_panel_h), pygame.SRCALPHA)
        party_surf.fill((0, 0, 0, 120))  # More transparent (was 180)
        
        # Title
        party_title = ui_font.render("Party", True, (220, 220, 180))
        party_surf.blit(party_title, (scale_value(8, ui_scale), scale_value(2, ui_scale)))
        
        # Draw companion cards
        card_y = scale_value(20, ui_scale)
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
                    party_surf, ui_font, scale_value(4, ui_scale), card_y, party_panel_w - scale_value(8, ui_scale),
                    comp_name, comp_hp, comp_max_hp, is_alive
                )
                card_y += card_height + card_spacing
        
        screen.blit(party_surf, (party_panel_x, party_panel_y))
        hero_panel_bottom = party_panel_y + party_panel_h

    # --- Contextual hints ---
    context_lines = _gather_context_hints(game, game_map, player)

    if context_lines:
        line_h = scale_value(20, ui_scale)
        ctx_h = scale_value(8, ui_scale) + len(context_lines) * line_h
        ctx_w = panel_w
        ctx_x = panel_x
        # Position context panel below party panel if it exists, otherwise below hero panel
        if party_list:
            party_panel_bottom = party_panel_y + party_panel_h
            ctx_y = party_panel_bottom + scale_value(8, ui_scale)
        else:
            ctx_y = hero_panel_bottom + scale_value(10, ui_scale)

        ctx_surf = pygame.Surface((ctx_w, ctx_h), pygame.SRCALPHA)
        ctx_surf.fill((0, 0, 0, 120))  # More transparent (was 150)
        screen.blit(ctx_surf, (ctx_x, ctx_y))

        y_ui = ctx_y + scale_value(4, ui_scale)
        for text in context_lines:
            color = (180, 200, 220)
            if any(word in text for word in ("dangerous", "hostile", "enemy")):
                color = (220, 150, 150)
            elif "wealth" in text or "chest" in text:
                color = (220, 210, 160)
            hint_surf = ui_font.render(text, True, color)
            screen.blit(hint_surf, (ctx_x + scale_value(8, ui_scale), y_ui))
            y_ui += line_h

    # Bottom message band
    band_h = scale_value(52, ui_scale)
    band_y = screen_h - band_h
    band_surf = pygame.Surface((screen_w, band_h), pygame.SRCALPHA)
    band_surf.fill((0, 0, 0, 190))
    screen.blit(band_surf, (0, band_y))

    msg_y = band_y + scale_value(8, ui_scale)
    last_msg = getattr(game, "last_message", "")
    if last_msg:
        # Allow the message log to specify a preferred color (e.g. item rarity)
        msg_color = getattr(game, "last_message_color", None) or (200, 200, 200)
        msg_text = ui_font.render(last_msg, True, msg_color)
        screen.blit(msg_text, (scale_value(10, ui_scale), msg_y))

    hint_text = ui_font.render(
        "Move WASD/arrows | '.' down ',' up | E: interact | C: sheet | I: inventory | "
        "K: history | L: battle log | H: tutorial | Z/X: zoom",
        True,
        (170, 170, 170),
    )
    screen.blit(hint_text, (scale_value(10, ui_scale), band_y + band_h - scale_value(24, ui_scale)))

    # Overlays: battle log
    if getattr(game, "show_battle_log", False) and getattr(game, "last_battle_log", None):
        max_lines = 8
        lines = game.last_battle_log[-max_lines:]  # type: ignore[index]

        line_height = scale_value(18, ui_scale)
        log_width = scale_value(520, ui_scale)
        log_height = scale_value(10, ui_scale) + len(lines) * line_height + scale_value(24, ui_scale)

        overlay = pygame.Surface((log_width, log_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        overlay_x = scale_value(8, ui_scale)
        overlay_y = scale_value(150, ui_scale)
        screen.blit(overlay, (overlay_x, overlay_y))

        y_log = overlay_y + scale_value(6, ui_scale)
        for line in lines:
            txt = ui_font.render(str(line), True, (220, 220, 220))
            screen.blit(txt, (overlay_x + scale_value(6, ui_scale), y_log))
            y_log += line_height

        close_txt = ui_font.render("Press L to hide battle log", True, (160, 160, 160))
        screen.blit(close_txt, (overlay_x + scale_value(6, ui_scale), overlay_y + log_height - line_height - scale_value(4, ui_scale)))

    # Exploration log overlay
    if getattr(game, "show_exploration_log", False):
        history: List[str] = list(getattr(game, "exploration_log", []))
        # Optional parallel color list from the message log, if available.
        history_colors: List = list(getattr(game, "exploration_log_colors", []))
        if not history:
            history = ["(No messages yet.)"]

        max_lines = 10
        lines = history[-max_lines:]

        line_height = scale_value(18, ui_scale)
        padding_x = scale_value(8, ui_scale)
        padding_y = scale_value(6, ui_scale)
        title_height = scale_value(22, ui_scale)

        log_width = min(scale_value(520, ui_scale), screen_w - scale_value(16, ui_scale))
        log_height = padding_y * 2 + title_height + len(lines) * line_height + scale_value(20, ui_scale)

        overlay = pygame.Surface((log_width, log_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))

        overlay_x = screen_w - log_width - scale_value(8, ui_scale)
        overlay_y = max(scale_value(8, ui_scale), band_y - log_height - scale_value(8, ui_scale))
        screen.blit(overlay, (overlay_x, overlay_y))

        y_log = overlay_y + padding_y
        title_surf = ui_font.render(
            "Exploration Log (latest at bottom)",
            True,
            (235, 235, 210),
        )
        screen.blit(title_surf, (overlay_x + padding_x, y_log))
        y_log += title_height

        for idx, line in enumerate(lines):
            # Default color for log entries
            color = (220, 220, 220)
            # If we have a parallel color list that matches history length,
            # pull the matching color for this visible line.
            if history_colors and len(history_colors) == len(history):
                history_index = len(history) - len(lines) + idx
                if 0 <= history_index < len(history_colors):
                    entry_color = history_colors[history_index]
                    if entry_color is not None:
                        color = entry_color

            txt = ui_font.render(str(line), True, color)
            screen.blit(txt, (overlay_x + padding_x, y_log))
            y_log += line_height

        close_txt = ui_font.render(
            "Press K to hide exploration log",
            True,
            (170, 170, 170),
        )
        screen.blit(
            close_txt,
            (overlay_x + padding_x, overlay_y + log_height - line_height - scale_value(4, ui_scale)),
        )

    # Exploration tutorial overlay
    if getattr(game, "show_exploration_tutorial", False):
        from ui.exploration_tutorial import draw_exploration_tutorial
        draw_exploration_tutorial(screen, ui_font, game)

