# engine/cheats.py

from __future__ import annotations

from typing import TYPE_CHECKING
import pygame
import random

if TYPE_CHECKING:
    from .game import Game

# Global cheat mode flag (toggled with F9)
_cheat_mode_enabled = False

# Global debug sprites overlay flag (toggled with F10)
# This doesn't require cheat mode - it's a development tool
DEBUG_SPRITES = False


def handle_cheat_key(game: "Game", event: pygame.event.Event) -> bool:
    """
    Handle global debug / cheat hotkeys.

    Returns True if the event was consumed (i.e. we performed a cheat and
    the normal input handler should NOT also process this key).
    
    Cheats are only active when cheat mode is enabled (toggle with F9).
    
    Mode-specific cheats:
    - OVERWORLD: F1 (reveal map), F5 (teleport to POI)
    - EXPLORATION: F1 (reveal map), F8 (skip floor)
    - BATTLE: F1 (kill enemies), F2 (heal all units), F5 (heal all), F6 (refill resources), F7 (skip turn), F8 (win battle)
    - ALL MODES: F2 (heal player), F3 (gold), F4 (XP)
    """
    global _cheat_mode_enabled
    
    if event.type != pygame.KEYDOWN:
        return False

    key = event.key

    # ------------------------------------------------------------------
    # F10: Toggle debug sprite overlay (doesn't require cheat mode)
    # ------------------------------------------------------------------
    if key == pygame.K_F10:
        global DEBUG_SPRITES
        DEBUG_SPRITES = not DEBUG_SPRITES
        game.last_message = (
            "[DEBUG] Sprite overlay ON. Press F10 again to disable."
            if DEBUG_SPRITES
            else "[DEBUG] Sprite overlay OFF."
        )
        return True

    # ------------------------------------------------------------------
    # F9: Toggle cheat mode on/off
    # ------------------------------------------------------------------
    if key == pygame.K_F9:
        _cheat_mode_enabled = not _cheat_mode_enabled
        game.last_message = (
            "[CHEAT MODE] Enabled. Press F9 again to disable."
            if _cheat_mode_enabled
            else "[CHEAT MODE] Disabled."
        )
        return True

    # All other cheats require cheat mode to be enabled
    if not _cheat_mode_enabled:
        return False

    # Import GameMode locally to avoid cycles
    from ..core.game import GameMode
    
    # Route to mode-specific cheat handlers
    if game.mode == GameMode.OVERWORLD:
        return _handle_overworld_cheat(game, key)
    elif game.mode == GameMode.BATTLE:
        return _handle_battle_cheat(game, key)
    elif game.mode == GameMode.EXPLORATION:
        return _handle_exploration_cheat(game, key)
    else:
        # Unknown mode, try universal cheats only
        return _handle_universal_cheat(game, key)


def _handle_universal_cheat(game: "Game", key: int) -> bool:
    """Handle cheats that work in all modes."""
    # ------------------------------------------------------------------
    # F2: Full heal the player (if player exists)
    # ------------------------------------------------------------------
    if key == pygame.K_F2:
        if game.player is not None:
            game.player.hp = game.player.max_hp
            game.last_message = "[CHEAT] Player fully healed."
        return True

    # ------------------------------------------------------------------
    # F3: +100 gold
    # ------------------------------------------------------------------
    if key == pygame.K_F3:
        if hasattr(game, "hero_stats") and game.hero_stats is not None:
            if hasattr(game.hero_stats, "add_gold"):
                gained = game.hero_stats.add_gold(100)
            else:
                game.hero_stats.gold += 100
                gained = 100
            game.last_message = f"[CHEAT] Granted {gained} gold."
        return True

    # ------------------------------------------------------------------
    # F4: +25 XP
    # ------------------------------------------------------------------
    if key == pygame.K_F4:
        if hasattr(game, "hero_stats") and game.hero_stats is not None:
            if hasattr(game.hero_stats, "grant_xp"):
                msgs = game.hero_stats.grant_xp(25)
                if game.player is not None:
                    game.apply_hero_stats_to_player(full_heal=False)
                text = " ".join(msgs) if msgs else "Gained 25 XP."
                game.last_message = "[CHEAT] " + text
            else:
                if hasattr(game.hero_stats, "xp"):
                    game.hero_stats.xp += 25
                game.last_message = "[CHEAT] Gained 25 XP."
        return True

    return False


def _handle_overworld_cheat(game: "Game", key: int) -> bool:
    """Handle overworld-specific cheats."""
    # First try universal cheats
    if _handle_universal_cheat(game, key):
        return True
    
    # ------------------------------------------------------------------
    # F1: Reveal entire overworld map
    # ------------------------------------------------------------------
    if key == pygame.K_F1:
        if hasattr(game, "overworld_map") and game.overworld_map is not None:
            # Explore all tiles
            for y in range(game.overworld_map.height):
                for x in range(game.overworld_map.width):
                    game.overworld_map.explore_tile(x, y)
            # Discover all POIs
            pois_discovered = 0
            for poi in game.overworld_map.get_all_pois():
                if not poi.discovered:
                    poi.discover()
                    pois_discovered += 1
            if pois_discovered > 0:
                game.last_message = f"[CHEAT] Overworld map fully revealed. Discovered {pois_discovered} POI(s)."
            else:
                game.last_message = "[CHEAT] Overworld map fully revealed."
        return True
    
    # ------------------------------------------------------------------
    # F5: Teleport to random POI
    # ------------------------------------------------------------------
    if key == pygame.K_F5:
        if hasattr(game, "overworld_map") and game.overworld_map is not None:
            pois = list(game.overworld_map.pois.values())
            if pois:
                poi = random.choice(pois)
                if hasattr(poi, "position"):
                    x, y = poi.position
                    if game.overworld_map.set_player_position(x, y):
                        game.last_message = f"[CHEAT] Teleported to {getattr(poi, 'name', 'POI')}."
                    else:
                        game.last_message = "[CHEAT] Failed to teleport to POI."
                else:
                    game.last_message = "[CHEAT] POI has no position."
            else:
                game.last_message = "[CHEAT] No POIs available."
        return True
    
    # ------------------------------------------------------------------
    # F6: Teleport to center of map
    # ------------------------------------------------------------------
    if key == pygame.K_F6:
        if hasattr(game, "overworld_map") and game.overworld_map is not None:
            center_x = game.overworld_map.width // 2
            center_y = game.overworld_map.height // 2
            if game.overworld_map.set_player_position(center_x, center_y):
                game.last_message = "[CHEAT] Teleported to map center."
            else:
                game.last_message = "[CHEAT] Failed to teleport to center."
        return True
    
    return False


def _handle_exploration_cheat(game: "Game", key: int) -> bool:
    """Handle exploration (dungeon) specific cheats."""
    # First try universal cheats
    if _handle_universal_cheat(game, key):
        return True
    
    # ------------------------------------------------------------------
    # F1: Toggle full-map reveal (ignore FOV radius)
    # ------------------------------------------------------------------
    if key == pygame.K_F1:
        game.debug_reveal_map = not getattr(game, "debug_reveal_map", False)
        if hasattr(game, "update_fov"):
            game.update_fov()
        game.last_message = (
            "[CHEAT] Full map reveal ON."
            if game.debug_reveal_map
            else "[CHEAT] Full map reveal OFF."
        )
        return True

    # ------------------------------------------------------------------
    # F8: Skip to next floor
    # ------------------------------------------------------------------
    if key == pygame.K_F8:
        if hasattr(game, "floor") and hasattr(game, "load_floor"):
            game.floor += 1
            game.load_floor(game.floor, from_direction=None)
            game.last_message = f"[CHEAT] Skipped to floor {game.floor}."
        return True
    
    return False


def _handle_battle_cheat(game: "Game", key: int) -> bool:
    """Handle battle-specific cheats."""
    # First try universal cheats
    if _handle_universal_cheat(game, key):
        return True
    
    battle_scene = getattr(game, "battle_scene", None)
    if battle_scene is None:
        return False
    
    # ------------------------------------------------------------------
    # F1: Kill all enemies
    # ------------------------------------------------------------------
    if key == pygame.K_F1:
        if hasattr(battle_scene, "enemy_units"):
            killed = 0
            for unit in battle_scene.enemy_units:
                if unit.is_alive:
                    unit.entity.hp = 0
                    killed += 1
            game.last_message = f"[CHEAT] Killed {killed} enemy unit(s)."
            # Check for victory
            battle_scene._next_turn()
        return True
    
    # ------------------------------------------------------------------
    # F2: Full heal all player units
    # ------------------------------------------------------------------
    if key == pygame.K_F2:
        if hasattr(battle_scene, "player_units"):
            healed = 0
            for unit in battle_scene.player_units:
                if unit.is_alive and hasattr(unit.entity, "hp") and hasattr(unit.entity, "max_hp"):
                    unit.entity.hp = unit.entity.max_hp
                    healed += 1
            game.last_message = f"[CHEAT] Fully healed {healed} player unit(s)."
        return True
    
    # ------------------------------------------------------------------
    # F5: Full heal all units (player + enemies)
    # ------------------------------------------------------------------
    if key == pygame.K_F5:
        healed_player = 0
        healed_enemy = 0
        if hasattr(battle_scene, "player_units"):
            for unit in battle_scene.player_units:
                if unit.is_alive and hasattr(unit.entity, "hp") and hasattr(unit.entity, "max_hp"):
                    unit.entity.hp = unit.entity.max_hp
                    healed_player += 1
        if hasattr(battle_scene, "enemy_units"):
            for unit in battle_scene.enemy_units:
                if unit.is_alive and hasattr(unit.entity, "hp") and hasattr(unit.entity, "max_hp"):
                    unit.entity.hp = unit.entity.max_hp
                    healed_enemy += 1
        game.last_message = f"[CHEAT] Fully healed {healed_player} player and {healed_enemy} enemy unit(s)."
        return True
    
    # ------------------------------------------------------------------
    # F6: Refill all resources (stamina/mana) for player units
    # ------------------------------------------------------------------
    if key == pygame.K_F6:
        if hasattr(battle_scene, "player_units"):
            refilled = 0
            for unit in battle_scene.player_units:
                if unit.is_alive:
                    # Refill stamina
                    if hasattr(unit, "current_stamina") and hasattr(unit, "max_stamina"):
                        unit.current_stamina = unit.max_stamina
                    # Refill mana
                    if hasattr(unit, "current_mana") and hasattr(unit, "max_mana"):
                        unit.current_mana = unit.max_mana
                    # Refill movement points
                    if hasattr(unit, "current_movement_points") and hasattr(unit, "max_movement_points"):
                        unit.current_movement_points = unit.max_movement_points
                    refilled += 1
            game.last_message = f"[CHEAT] Refilled resources for {refilled} player unit(s)."
        return True
    
    # ------------------------------------------------------------------
    # F7: Skip current unit's turn
    # ------------------------------------------------------------------
    if key == pygame.K_F7:
        if hasattr(battle_scene, "_next_turn"):
            battle_scene._next_turn()
            active_unit = battle_scene._active_unit() if hasattr(battle_scene, "_active_unit") else None
            unit_name = active_unit.name if active_unit else "unit"
            game.last_message = f"[CHEAT] Skipped turn. Now {unit_name}'s turn."
        return True
    
    # ------------------------------------------------------------------
    # F8: Win battle (set all enemies to 0 HP)
    # ------------------------------------------------------------------
    if key == pygame.K_F8:
        if hasattr(battle_scene, "enemy_units"):
            killed = 0
            for unit in battle_scene.enemy_units:
                if unit.is_alive:
                    unit.entity.hp = 0
                    killed += 1
            game.last_message = f"[CHEAT] Battle won! Defeated {killed} enemy unit(s)."
            # Check for victory (this will set status to "victory" if all enemies are dead)
            if hasattr(battle_scene, "_next_turn"):
                battle_scene._next_turn()
        return True
    
    return False


def is_debug_sprites_enabled() -> bool:
    """Check if debug sprite overlay is enabled."""
    return DEBUG_SPRITES
