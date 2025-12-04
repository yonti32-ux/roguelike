# ui/hud.py

from __future__ import annotations

from typing import TYPE_CHECKING, List
import pygame

from settings import TILE_SIZE
from systems.inventory import get_item_def
from systems import perks as perk_system
from world.entities import Enemy
from systems.events import get_event_def

if TYPE_CHECKING:
    from engine.game import Game


def draw_exploration_ui(game: "Game") -> None:
    """
    Draw the main exploration HUD + contextual hints +
    optional overlays (battle log, character sheet, inventory).
    """
    if game.player is None:
        return

    screen = game.screen
    ui_font = game.ui_font
    game_map = game.current_map
    player = game.player

    # Floor
    floor_text = ui_font.render(
        f"Floor {game.floor}",
        True,
        (220, 220, 220),
    )
    screen.blit(floor_text, (8, 8))

    # Level / XP
    xp_text = ui_font.render(
        f"Lv {game.hero_stats.level}  XP {game.hero_stats.xp}/{game.hero_stats.xp_to_next()}",
        True,
        (220, 220, 160),
    )
    screen.blit(xp_text, (8, 30))

    # Gold
    gold_text = ui_font.render(
        f"Gold: {game.hero_stats.gold}",
        True,
        (230, 210, 120),
    )
    screen.blit(gold_text, (0, 120))

    # HP
    player_hp = getattr(player, "hp", 0)
    player_max_hp = getattr(player, "max_hp", 0)
    hp_text = ui_font.render(
        f"HP {player_hp}/{player_max_hp}",
        True,
        (220, 80, 80),
    )
    screen.blit(hp_text, (8, 74))

    # ATK / DEF (include gear bonuses)
    gear_mods = game.inventory.total_stat_modifiers() if game.inventory is not None else {}
    atk_base = game.hero_stats.attack_power
    def_base = game.hero_stats.defense
    atk_total = atk_base + int(gear_mods.get("attack", 0))
    def_total = def_base + int(gear_mods.get("defense", 0))

    atk_def_text = ui_font.render(
        f"ATK {atk_total}  DEF {def_total}",
        True,
        (200, 200, 200),
    )
    screen.blit(atk_def_text, (8, 96))

    # Last message (XP / level-up / heal / reward etc.)
    if getattr(game, "last_message", ""):
        msg_text = ui_font.render(
            game.last_message,
            True,
            (180, 180, 180),
        )
        screen.blit(msg_text, (8, 118))

    # Controls hint (bottom)
    hint_text = ui_font.render(
        "Move WASD/arrows | '.' down ',' up | E: interact | C: sheet | I: inventory | L: log | Z/X: zoom",
        True,
        (160, 160, 160),
    )
    screen.blit(hint_text, (8, game.screen.get_height() - 30))

    # --- Contextual exploration hints (stairs + room vibe + threat + chests/events) ---
    stairs_hint = None
    threat_hint = None
    chest_hint = None
    event_hint = None
    room_hint = None

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
                room_hint = "This room feels dangerous."
            elif tag == "treasure":
                room_hint = "You sense hidden wealth nearby."
            elif tag == "event":
                room_hint = "Something unusual is anchored in this room."
            elif tag == "start":
                room_hint = "A moment of calm before the descent."
            # other tags can be added later (boss, shrine, etc.)

        # Count nearby enemies for a bit of ambient info
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

    # --- Draw contextual hints ---
    y_ui = 144
    if stairs_hint:
        stairs_surf = ui_font.render(stairs_hint, True, (180, 200, 220))
        screen.blit(stairs_surf, (8, y_ui))
        y_ui += 20
    if room_hint:
        room_surf = ui_font.render(room_hint, True, (190, 190, 220))
        screen.blit(room_surf, (8, y_ui))
        y_ui += 20
    if threat_hint:
        threat_surf = ui_font.render(threat_hint, True, (220, 150, 150))
        screen.blit(threat_surf, (8, y_ui))
        y_ui += 20
    if chest_hint:
        chest_surf = ui_font.render(chest_hint, True, (200, 200, 160))
        screen.blit(chest_surf, (8, y_ui))
        y_ui += 20
    elif event_hint:
        event_surf = ui_font.render(event_hint, True, (200, 200, 180))
        screen.blit(event_surf, (8, y_ui))

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

        y = overlay_y + 6
        for line in lines:
            txt = ui_font.render(line, True, (220, 220, 220))
            screen.blit(txt, (overlay_x + 6, y))
            y += line_height

        close_txt = ui_font.render(
            "Press L to hide battle log",
            True,
            (160, 160, 160),
        )
        screen.blit(
            close_txt,
            (overlay_x + 6, overlay_y + log_height - line_height - 4),
        )

    # --- Character sheet overlay (hero + proto-party) ---
    if game.show_character_sheet:
        _draw_character_sheet(game)

    # --- Inventory overlay ---
    if getattr(game, "show_inventory", False):
        draw_inventory_overlay(game)


def _draw_character_sheet(game: "Game") -> None:
    screen = game.screen
    ui_font = game.ui_font
    player = game.player

    hero_name = getattr(
        game.hero_stats,
        "hero_name",
        getattr(player, "name", "Adventurer"),
    )
    level = game.hero_stats.level
    xp = game.hero_stats.xp
    xp_next = game.hero_stats.xp_to_next()
    hp = getattr(player, "hp", 0)
    max_hp = getattr(player, "max_hp", 0)
    atk = game.hero_stats.attack_power
    defense = game.hero_stats.defense
    skill_power = game.hero_stats.skill_power

    # Perks (show branch + name)
    perk_ids = getattr(game.hero_stats, "perks", [])
    if perk_ids:
        perk_lines: List[str] = []
        for pid in perk_ids:
            try:
                perk = perk_system.get(pid)
                branch_label = perk.branch.capitalize()
                perk_lines.append(f"- [{branch_label}] {perk.name}")
            except KeyError:
                perk_lines.append(f"- {pid}")
        if not perk_lines:
            perk_lines = ["(no perks yet)"]
    else:
        perk_lines = ["(no perks yet)"]

    # Proto-party block – still just hero + generic ally preview
    companion_name = "Companion"
    comp_max_hp = int(max_hp * 0.8)
    comp_hp = comp_max_hp
    comp_atk = max(2, int(atk * 0.7))
    comp_def = defense
    comp_sp = skill_power

    party_rows = [
        {
            "role": "Hero",
            "name": hero_name,
            "hp": hp,
            "max_hp": max_hp,
            "atk": atk,
            "def": defense,
            "sp": skill_power,
        },
        {
            "role": "Ally",
            "name": companion_name,
            "hp": comp_hp,
            "max_hp": comp_max_hp,
            "atk": comp_atk,
            "def": comp_def,
            "sp": comp_sp,
        },
    ]

    width = 520
    height = 320
    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 210))

    ox = 120
    oy = 90
    screen.blit(overlay, (ox, oy))

    y = oy + 10
    title = ui_font.render("Character Sheet", True, (255, 255, 210))
    screen.blit(title, (ox + 12, y))
    y += 28

    name_text = ui_font.render(f"Name: {hero_name}", True, (230, 230, 230))
    screen.blit(name_text, (ox + 12, y))
    y += 22

    # Show hero class
    hero_class_id = getattr(game.hero_stats, "hero_class_id", "warrior")
    class_name = hero_class_id.capitalize()
    class_text = ui_font.render(f"Class: {class_name}", True, (220, 220, 200))
    screen.blit(class_text, (ox + 12, y))
    y += 22

    level_text = ui_font.render(
        f"Level {level}   XP {xp}/{xp_next}",
        True,
        (220, 220, 180),
    )
    gold_line = ui_font.render(
        f"Gold: {game.hero_stats.gold}",
        True,
        (230, 220, 180),
    )
    screen.blit(gold_line, (ox + 12, y))
    y += 22

    screen.blit(level_text, (ox + 12, y))
    y += 26

    # Core hero stats (show gear bonuses)
    gear_mods = game.inventory.total_stat_modifiers() if game.inventory is not None else {}
    base_max_hp = game.hero_stats.max_hp
    hp_bonus = int(gear_mods.get("max_hp", 0))
    atk_bonus = int(gear_mods.get("attack", 0))
    def_bonus = int(gear_mods.get("defense", 0))
    sp_bonus = float(gear_mods.get("skill_power", 0.0))

    stats_lines: List[str] = []

    if hp_bonus:
        stats_lines.append(f"HP: {hp}/{max_hp} (base {base_max_hp} +{hp_bonus} gear)")
    else:
        stats_lines.append(f"HP: {hp}/{max_hp}")

    if atk_bonus:
        stats_lines.append(f"ATK: {atk + atk_bonus} (base {atk} +{atk_bonus} gear)")
    else:
        stats_lines.append(f"ATK: {atk}")

    if def_bonus:
        stats_lines.append(f"DEF: {defense + def_bonus} (base {defense} +{def_bonus} gear)")
    else:
        stats_lines.append(f"DEF: {defense}")

    if abs(sp_bonus) > 1e-3:
        stats_lines.append(
            f"Skill Power: {skill_power + sp_bonus:.2f}x (base {skill_power:.2f} +{sp_bonus:.2f})"
        )
    else:
        stats_lines.append(f"Skill Power: {skill_power:.2f}x")

    for line in stats_lines:
        t = ui_font.render(line, True, (220, 220, 220))
        screen.blit(t, (ox + 12, y))
        y += 20

    # Perks
    y += 8
    perks_title = ui_font.render("Perks:", True, (220, 220, 180))
    screen.blit(perks_title, (ox + 12, y))
    y += 22

    for line in perk_lines[:4]:
        t = ui_font.render(line, True, (210, 210, 210))
        screen.blit(t, (ox + 24, y))
        y += 18

    # Party block
    y += 8
    party_title = ui_font.render("Party:", True, (220, 220, 180))
    screen.blit(party_title, (ox + 12, y))
    y += 22

    header = ui_font.render(
        "Role   Name              HP        ATK  DEF  SP",
        True,
        (200, 200, 200),
    )
    screen.blit(header, (ox + 12, y))
    y += 20

    for row in party_rows:
        line = (
            f"{row['role']:<5}  "
            f"{row['name']:<14}  "
            f"{row['hp']:>3}/{row['max_hp']:<3}   "
            f"{row['atk']:>2}   {row['def']:>2}   {row['sp']:.1f}"
        )
        t = ui_font.render(line, True, (220, 220, 220))
        screen.blit(t, (ox + 12, y))
        y += 18

    hint = ui_font.render("Press C to close", True, (160, 160, 160))
    screen.blit(hint, (ox + 12, oy + height - 26))


def draw_perk_choice_overlay(game: "Game") -> None:
    """
    Draw the 'Level Up – choose a perk' overlay on top of the exploration view.
    """
    if not game.pending_perk_choices:
        return

    screen = game.screen
    ui_font = game.ui_font

    width = 560
    height = 260
    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 220))

    ox = 80
    oy = 100
    screen.blit(overlay, (ox, oy))

    y = oy + 10
    title = ui_font.render("Level Up! Choose a perk:", True, (255, 255, 210))
    screen.blit(title, (ox + 12, y))
    y += 30

    for i, perk in enumerate(game.pending_perk_choices):
        label = f"{i + 1}. {perk.name}"
        name_surf = ui_font.render(label, True, (220, 220, 220))
        screen.blit(name_surf, (ox + 12, y))
        y += 20

        desc_surf = ui_font.render(perk.description, True, (200, 200, 200))
        screen.blit(desc_surf, (ox + 32, y))
        y += 26

    hint = ui_font.render("Press 1–3 to choose (ESC to skip)", True, (160, 160, 160))
    screen.blit(hint, (ox + 12, oy + height - 28))


def draw_inventory_overlay(game: "Game") -> None:
    """
    Simple inventory + equipment screen overlay.

    - Shows equipped weapon / armor / trinket
    - Shows a small list of items and how to equip them
    """
    screen = game.screen
    ui_font = game.ui_font

    width = 520
    height = 320
    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 210))

    ox = 120
    oy = 90
    screen.blit(overlay, (ox, oy))

    y = oy + 10
    title = ui_font.render("Inventory & Equipment", True, (255, 255, 210))
    screen.blit(title, (ox + 12, y))
    y += 26

    # Equipped items
    slots = ["weapon", "armor", "trinket"]
    screen.blit(ui_font.render("Equipped:", True, (220, 220, 180)), (ox + 12, y))
    y += 22

    for slot in slots:
        item = game.inventory.get_equipped_item(slot)
        name = item.name if item else "(none)"
        line = f"{slot.capitalize():<7}: {name}"
        t = ui_font.render(line, True, (220, 220, 220))
        screen.blit(t, (ox + 24, y))
        y += 20

    # Backpack items
    y += 10
    screen.blit(ui_font.render("Backpack:", True, (220, 220, 180)), (ox + 12, y))
    y += 22

    if not game.inventory.items:
        t = ui_font.render("(empty)", True, (180, 180, 180))
        screen.blit(t, (ox + 24, y))
        y += 20
    else:
        visible_items = game.inventory.items[:10]
        for idx, item_id in enumerate(visible_items):
            item = get_item_def(item_id)
            if item is None:
                continue

            equipped_id = game.inventory.equipped.get(item.slot)
            is_equipped = equipped_id == item_id

            label = f"{idx + 1}. {item.name} [{item.slot}]"
            if is_equipped:
                label += " *"

            color = (250, 250, 170) if is_equipped else (220, 220, 220)
            t = ui_font.render(label, True, color)
            screen.blit(t, (ox + 24, y))
            y += 18

    hint = ui_font.render("1–9: equip  |  I/ESC: close", True, (160, 160, 160))
    screen.blit(hint, (ox + 12, oy + height - 26))
