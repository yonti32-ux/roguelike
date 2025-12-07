from __future__ import annotations

from typing import TYPE_CHECKING, List
import pygame

from settings import TILE_SIZE
from systems.inventory import get_item_def
from systems import perks as perk_system
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
    Utility: draw a simple filled bar (e.g. HP / XP) at [x, y] with a given
    fill fraction in [0, 1].
    """
    fraction = max(0.0, min(1.0, float(fraction)))
    # Background
    pygame.draw.rect(surface, back_color, (x, y, width, height))
    if fraction > 0.0:
        fill_w = int(width * fraction)
        pygame.draw.rect(surface, fill_color, (x, y, fill_w, height))
    if border_color is not None and height > 2 and width > 2:
        pygame.draw.rect(surface, border_color, (x, y, width, height), 1)


def draw_exploration_ui(game: "Game") -> None:
    """
    Draw the main exploration HUD + contextual hints +
    optional overlays (exploration log, battle log, character sheet, inventory).

    Layout goals:
    - Top-left hero panel with core run info (name, class, floor, HP, XP, stats).
    - Mid-left context stack (stairs, room vibe, nearby threats, chests/events).
    - Bottom message band for the latest log line, with controls above the edge.
    """
    if game.player is None:
        return

    screen = game.screen
    ui_font = game.ui_font
    game_map = game.current_map
    player = game.player

    screen_w, screen_h = screen.get_size()

    # --------------------------------------------------------------
    # HERO PANEL (top-left)
    # --------------------------------------------------------------
    panel_x = 8
    panel_y = 8
    panel_w = 280
    # A bit taller so context panel doesn't overlap gold text
    panel_h = 160

    panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    panel_surf.fill((0, 0, 0, 180))
    screen.blit(panel_surf, (panel_x, panel_y))

    text_x = panel_x + 10
    y = panel_y + 8

    hero_name = getattr(game.hero_stats, "hero_name", "Adventurer")
    hero_class_id = getattr(game.hero_stats, "hero_class_id", "warrior")
    hero_class_label = hero_class_id.capitalize()

    name_text = ui_font.render(f"{hero_name} ({hero_class_label})", True, (245, 245, 230))
    screen.blit(name_text, (text_x, y))
    y += 24

    # Floor + debug flags
    floor_text = ui_font.render(f"Floor {game.floor}", True, (220, 220, 220))
    screen.blit(floor_text, (text_x, y))
    y += 20

    if getattr(game, "debug_reveal_map", False):
        dbg = ui_font.render("DEBUG: Full map reveal ON.", True, (240, 210, 120))
        screen.blit(dbg, (text_x, y))
        y += 20

    # Level / XP + XP bar
    xp_cur = game.hero_stats.xp
    xp_needed = max(1, game.hero_stats.xp_to_next())
    xp_ratio = xp_cur / xp_needed

    xp_text = ui_font.render(
        f"Lv {game.hero_stats.level}  XP {xp_cur}/{xp_needed}",
        True,
        (220, 220, 160),
    )
    screen.blit(xp_text, (text_x, y))
    y += 18

    bar_x = text_x
    bar_w = panel_w - 20
    bar_h = 8
    bar_y = y + 2
    _draw_bar(
        screen,
        bar_x,
        bar_y,
        bar_w,
        bar_h,
        xp_ratio,
        back_color=(40, 40, 60),
        fill_color=(190, 190, 90),
        border_color=(255, 255, 255),
    )
    y = bar_y + bar_h + 6

    # Gear bonuses
    gear_mods = game.inventory.total_stat_modifiers() if game.inventory is not None else {}
    atk_base = game.hero_stats.attack_power
    def_base = game.hero_stats.defense
    atk_bonus = int(gear_mods.get("attack", 0))
    def_bonus = int(gear_mods.get("defense", 0))

    # HP + bar
    player_hp = getattr(player, "hp", 0)
    player_max_hp = max(1, getattr(player, "max_hp", 1))
    hp_ratio = player_hp / player_max_hp

    hp_text = ui_font.render(f"HP {player_hp}/{player_max_hp}", True, (230, 90, 90))
    screen.blit(hp_text, (text_x, y))
    y += 18

    hp_bar_y = y
    _draw_bar(
        screen,
        bar_x,
        hp_bar_y,
        bar_w,
        bar_h,
        hp_ratio,
        back_color=(60, 30, 30),
        fill_color=(200, 80, 80),
        border_color=(255, 255, 255),
    )
    y = hp_bar_y + bar_h + 6

    atk_total = atk_base + atk_bonus
    def_total = def_base + def_bonus

    atk_label = f"ATK {atk_total}"
    if atk_bonus:
        atk_label += f" (+{atk_bonus})"
    def_label = f"DEF {def_total}"
    if def_bonus:
        def_label += f" (+{def_bonus})"

    atk_def_text = ui_font.render(f"{atk_label}   {def_label}", True, (200, 200, 200))
    screen.blit(atk_def_text, (text_x, y))
    y += 18

    gold_text = ui_font.render(f"Gold: {game.hero_stats.gold}", True, (230, 210, 120))
    screen.blit(gold_text, (text_x, y))

    hero_panel_bottom = panel_y + panel_h

    # --------------------------------------------------------------
    # CONTEXTUAL HINTS (stairs, room vibe, threats, chests/events)
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

        # Room 'vibes' based on room tag
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
                room_hint = "A moment of calm before the descent."
            elif tag == "shop":
                room_hint = "A quiet merchant has set up here – find them and press E to trade."

        # Count nearby enemies for ambient info
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

        # Chest / event nearby?
        chest = None
        event_node = None
        if hasattr(game, "exploration") and game.exploration is not None:
            chest = game.exploration.find_chest_near_player(max_distance_px=TILE_SIZE)
            # Only bother looking for events if there's no unopened chest
            if chest is None or getattr(chest, "opened", False):
                event_node = game.exploration.find_event_near_player(
                    max_distance_px=TILE_SIZE
                )

        if chest is not None and not getattr(chest, "opened", False):
            chest_hint = "There is a chest here – press E to open."
        elif event_node is not None:
            # Look up event definition to tailor the hint
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

    # Context panel background sized to the number of active hints
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
        ctx_y = hero_panel_bottom + 8

        ctx_surf = pygame.Surface((ctx_w, ctx_h), pygame.SRCALPHA)
        ctx_surf.fill((0, 0, 0, 150))
        screen.blit(ctx_surf, (ctx_x, ctx_y))

        y_ui = ctx_y + 4
        for text in context_lines:
            color = (180, 200, 220)
            if "dangerous" in text or "hostile" in text or "enemy" in text:
                color = (220, 150, 150)
            elif "wealth" in text or "chest" in text:
                color = (220, 210, 160)
            hint_surf = ui_font.render(text, True, color)
            screen.blit(hint_surf, (ctx_x + 8, y_ui))
            y_ui += line_h

    # --------------------------------------------------------------
    # BOTTOM MESSAGE BAND + CONTROLS
    # --------------------------------------------------------------
    band_h = 52
    band_y = screen_h - band_h
    band_surf = pygame.Surface((screen_w, band_h), pygame.SRCALPHA)
    band_surf.fill((0, 0, 0, 190))
    screen.blit(band_surf, (0, band_y))

    msg_y = band_y + 8
    if getattr(game, "last_message", ""):
        msg_text = ui_font.render(game.last_message, True, (200, 200, 200))
        screen.blit(msg_text, (10, msg_y))

    # Controls hint (bottom line)
    hint_text = ui_font.render(
        "Move WASD/arrows | '.' down ',' up | E: interact | C: sheet | I: inventory | K: history | L: battle log | Z/X: zoom",
        True,
        (170, 170, 170),
    )
    screen.blit(hint_text, (10, band_y + band_h - 24))

    # --------------------------------------------------------------
    # Overlays on top of the exploration HUD
    # --------------------------------------------------------------
    # --- Last battle log overlay (if enabled) ---
    if getattr(game, "show_battle_log", False) and getattr(game, "last_battle_log", None):
        max_lines = 8
        lines = game.last_battle_log[-max_lines:]

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
            txt = ui_font.render(line, True, (220, 220, 220))
            screen.blit(txt, (overlay_x + 6, y_log))
            y_log += line_height

        close_txt = ui_font.render(
            "Press L to hide battle log",
            True,
            (160, 160, 160),
        )
        screen.blit(
            close_txt,
            (overlay_x + 6, overlay_y + log_height - line_height - 4),
        )

    # --- Exploration log overlay (recent exploration messages) ---
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
        log_height = (
            padding_y * 2
            + title_height
            + len(lines) * line_height
            + 20
        )

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
            txt = ui_font.render(line, True, (220, 220, 220))
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

    # --- Character sheet overlay (hero + proto-party) ---
    if game.show_character_sheet:
        _draw_character_sheet(game)

    # --- Inventory overlay ---
    if getattr(game, "show_inventory", False):
        draw_inventory_overlay(game)

    # --- Shop overlay (merchant rooms) ---
    if getattr(game, "show_shop", False):
        draw_shop_overlay(game)


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

    # Title
    title = ui_font.render("Character Sheet", True, (240, 240, 200))
    screen.blit(title, (ox + 12, oy + 10))

    # ------------------------------------------------------------------
    # Determine which character we are focusing:
    # 0 = hero, 1..N = companions in game.party.
    # ------------------------------------------------------------------
    focus_index = int(getattr(game, "character_sheet_focus_index", 0))
    party_list = getattr(game, "party", None) or []
    total_slots = 1 + len(party_list)
    if total_slots <= 1:
        focus_index = 0
    else:
        focus_index = max(0, min(focus_index, total_slots - 1))

    focused_is_hero = (focus_index == 0)
    focused_comp: CompanionState | None = None
    focused_template: CompanionDef | None = None

    if not focused_is_hero and party_list:
        comp_idx = focus_index - 1
        if 0 <= comp_idx < len(party_list):
            raw_comp = party_list[comp_idx]
            if isinstance(raw_comp, CompanionState):
                focused_comp = raw_comp
                template_id = getattr(raw_comp, "template_id", None)
                if template_id:
                    try:
                        focused_template = get_companion(template_id)
                    except KeyError:
                        focused_template = None
                if focused_template is not None:
                    try:
                        ensure_companion_stats(raw_comp, focused_template)
                    except Exception:
                        pass
            else:
                # Legacy / unknown type → fall back to hero view
                focused_is_hero = True

    # ------------------------------------------------------------------
    # Focused character core info + stats
    # ------------------------------------------------------------------
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

        # Companion stats (no gear breakdown yet)
        stats_lines: List[str] = []
        stats_lines.append(f"HP: {hp}/{max_hp}")
        stats_lines.append(f"ATK: {atk}")
        stats_lines.append(f"DEF: {defense}")
        stats_lines.append(f"Skill Power: {skill_power:.2f}x")

    # Render stat lines
    for line in stats_lines:
        t = ui_font.render(line, True, (220, 220, 220))
        screen.blit(t, (ox + 12, y))
        y += 20

    # ------------------------------------------------------------------
    # Perks (hero only for now)
    # ------------------------------------------------------------------
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
        placeholder = ui_font.render(
            "Companion perks: (not implemented yet)",
            True,
            (180, 180, 180),
        )
        screen.blit(placeholder, (ox + 24, y))
        y += 20

    # ------------------------------------------------------------------
    # Party preview block (hero + companions, with focus marker)
    # ------------------------------------------------------------------
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

    hero_selected = (focus_index == 0)
    hero_marker = " [*]" if hero_selected else ""
    hero_line = ui_font.render(
        f"[Hero] {hero_name_list} ({class_str}){hero_marker}",
        True,
        (230, 230, 230),
    )
    screen.blit(hero_line, (ox + 24, y))
    y += 20

    if not party_list:
        companion_line = ui_font.render(
            "[Companion] — no allies recruited yet",
            True,
            (170, 170, 190),
        )
        screen.blit(companion_line, (ox + 24, y))
        y += 20
    else:
        base_max_hp = getattr(game.player, "max_hp", 24)
        base_atk = getattr(game.player, "attack_power", 5)
        base_defense = int(getattr(game.player, "defense", 0))

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
            is_selected = (focus_index == idx + 1)
            sel_marker = " [*]" if is_selected else ""
            line = (
                f"[Companion] {lvl_prefix}{name} ({role}){sel_marker} – "
                f"HP {comp_max_hp}, ATK {comp_atk}, DEF {comp_defense}"
            )
            t = ui_font.render(line, True, (210, 210, 230))
            screen.blit(t, (ox + 24, y))
            y += 20

    # Close hint + switching hint
    hint = ui_font.render(
        "Press Q/E to switch character, C to close",
        True,
        (160, 160, 160),
    )
    screen.blit(hint, (ox + 40, oy + height - 30))




def draw_perk_choice_overlay(game: "Game") -> None:
    """
    Draw the perk choice overlay used both for level-ups and events that
    grant a free perk. Uses game.pending_perk_choices (list of Perk defs).
    """
    # If there are no pending choices, nothing to draw.
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
        # perk is a Perk object from perk_system.pick_perk_choices
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
            desc_surf = ui_font.render(desc, True, (190, 190, 200))
            screen.blit(desc_surf, (ox + 36, y))
            y += 30
        else:
            y += 8

    hint = ui_font.render("Press 1–3 to choose (ESC to skip)", True, (160, 160, 160))
    screen.blit(hint, (ox + 12, oy + height - 28))


def draw_inventory_overlay(game: "Game", inventory: "Inventory | None" = None) -> None:
    """
    Inventory + equipment screen overlay.

    This version is aware of the current inventory focus:
    - Index 0: hero
    - Index 1..N: companions in game.party order

    Q/E while the inventory is open will cycle this focus (handled in Game),
    and we show / equip items for the focused character.
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

    # Figure out who we're focusing in this overlay.
    party_list: list[CompanionState] = getattr(game, "party", None) or []
    total_slots = 1 + len(party_list)  # hero + companions

    focus_index = int(getattr(game, "inventory_focus_index", 0))
    if total_slots <= 1:
        focus_index = 0
    else:
        focus_index = focus_index % total_slots

    focused_is_hero = (focus_index == 0)
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
                    # Safety: make sure stats are initialised.
                    ensure_companion_stats(candidate, focused_template)

    # Resolve a display name + stat line for the focused character.
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
        # Hero equipment comes from the main Inventory object
        equipped_map = inv.equipped if inv is not None else {}
    else:
        # Companion focus
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

    # Backpack items list (always from the shared inventory)
    y += 12
    backpack_title = ui_font.render("Backpack:", True, (220, 220, 180))
    screen.blit(backpack_title, (ox + 12, y))
    y += 24

    if not inv or not inv.items:
        none = ui_font.render(
            "You are not carrying anything yet.",
            True,
            (180, 180, 180),
        )
        screen.blit(none, (ox + 24, y))
        y += 20
    else:
        max_items = 10
        for idx, item_id in enumerate(inv.items[:max_items]):
            item_def = get_item_def(item_id)
            if item_def is None:
                continue

            # Check if this item is equipped on the focused character.
            equipped_marker = ""
            if equipped_map:
                if equipped_map.get("weapon") == item_id:
                    equipped_marker = " [W]"
                elif equipped_map.get("armor") == item_id:
                    equipped_marker = " [A]"
                elif equipped_map.get("trinket") == item_id:
                    equipped_marker = " [T]"

            hotkey = ""
            if idx < 9:
                hotkey = f"[{idx + 1}] "

            line = f"{hotkey}{item_def.name}{equipped_marker}"
            t = ui_font.render(line, True, (220, 220, 220))
            screen.blit(t, (ox + 24, y))
            y += 20

    # Stats + footer hint
    if stats_line_text:
        stats_surf = ui_font.render(stats_line_text, True, (200, 200, 200))
        screen.blit(stats_surf, (ox + 12, oy + height - 52))

    footer = ui_font.render(
        "1–9: equip on focused | Q/E: switch character | I or ESC: close",
        True,
        (170, 170, 170),
    )
    screen.blit(footer, (ox + 12, oy + height - 30))



def draw_companion_choice_overlay(
    game: "Game",
    companion_defs: list[CompanionDef],
    selected_index: int | None = None,
) -> None:
    """
    Draws a simple overlay for choosing a companion from a list of
    CompanionDef templates.

    This is not wired into gameplay yet, but the stat preview is kept
    in sync with how companions are currently derived from the hero:
    we scale off the hero's current stats using the factors on each
    CompanionDef.
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
        msg = ui_font.render("No companions available to recruit yet.", True, (200, 200, 200))
        screen.blit(msg, (ox + 12, oy + 60))
        hint = ui_font.render("Press ESC to cancel.", True, (160, 160, 160))
        screen.blit(hint, (ox + 12, oy + height - 30))
        return

    # Baseline stats taken from the current hero entity
    base_max_hp = getattr(game.player, "max_hp", 24)
    base_atk = getattr(game.player, "attack_power", 5)
    base_defense = int(getattr(game.player, "defense", 0))

    y = oy + 50
    for i, comp in enumerate(companion_defs):
        # Background highlight for selected index
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

        # Lightweight stat preview derived from hero stats
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

    hint = ui_font.render("Press 1–3 to recruit (ESC to cancel)", True, (160, 160, 160))
    screen.blit(hint, (ox + 12, oy + height - 30))



def draw_shop_overlay(game: "Game") -> None:
    """
    Simple shop UI overlay for merchant rooms.

    Uses transient state on the Game object:
    - game.shop_stock: list of item_ids for sale
    - game.shop_cursor: index of the currently highlighted entry
    - game.shop_mode: "buy" or "sell"
    - game.hero_stats.gold: current gold
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

    # Title
    title = ui_font.render(f"Dungeon Merchant — {mode_label}", True, (240, 240, 200))
    screen.blit(title, (ox + 12, oy + 10))

    # Player gold
    gold_value = getattr(getattr(game, "hero_stats", None), "gold", 0)
    gold_line = ui_font.render(
        f"Your gold: {gold_value}",
        True,
        (230, 210, 120),
    )
    screen.blit(gold_line, (ox + 12, oy + 36))

    stock_buy: List[str] = list(getattr(game, "shop_stock", []))
    inv = getattr(game, "inventory", None)
    cursor = int(getattr(game, "shop_cursor", 0))
    y = oy + 70

    # Determine which list we're showing
    if mode == "buy":
        active_list = stock_buy
    else:
        if inv is None:
            active_list = []
        else:
            active_list = inv.get_sellable_item_ids()

    if not active_list:
        if mode == "buy":
            msg_text = "The merchant has nothing left to sell."
        else:
            msg_text = "You have nothing you're willing to sell."
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
                base_price = getattr(item_def, "value", 0) or 0
                rarity = getattr(item_def, "rarity", "")

            if mode == "buy":
                price = base_price
            else:
                # Sell price: 50% of value, minimum 1g
                price = max(1, base_price // 2) if base_price > 0 else 1

            label = f"{i + 1}) {name}"
            if rarity:
                label += f" [{rarity}]"

            if mode == "buy":
                price_str = f"{price}g"
            else:
                price_str = f"{price}g (sell)"

            # Highlight selected line
            if i == cursor:
                bg = pygame.Surface((width - 24, line_height), pygame.SRCALPHA)
                bg.fill((60, 60, 90, 210))
                screen.blit(bg, (ox + 12, y - 2))

            label_surf = ui_font.render(label, True, (230, 230, 230))
            screen.blit(label_surf, (ox + 24, y))

            price_surf = ui_font.render(price_str, True, (230, 210, 120))
            screen.blit(price_surf, (ox + width - 160, y))

            y += line_height

    # Footer hints (wrapped into two shorter lines so they fit)
    color = (170, 170, 170)
    if mode == "buy":
        footer_line1 = "Up/Down or W/S: move • Enter/Space: buy • 1–9: quick buy"
        footer_line2 = "TAB: switch to SELL • ESC/E/I/C: leave shop"
    else:
        footer_line1 = "Up/Down or W/S: move • Enter/Space: sell • 1–9: quick sell"
        footer_line2 = "TAB: switch to BUY • ESC/E/I/C: leave shop"

    line1_surf = ui_font.render(footer_line1, True, color)
    line2_surf = ui_font.render(footer_line2, True, color)

    # Two lines near the bottom of the panel
    base_y = oy + height - 40
    screen.blit(line1_surf, (ox + 12, base_y))
    screen.blit(line2_surf, (ox + 12, base_y + 18))


