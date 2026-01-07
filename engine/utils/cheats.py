# engine/cheats.py

from __future__ import annotations

from typing import TYPE_CHECKING
import pygame

if TYPE_CHECKING:
    from .game import Game

# Global cheat mode flag (toggled with F9)
_cheat_mode_enabled = False


def handle_cheat_key(game: "Game", event: pygame.event.Event) -> bool:
    """
    Handle global debug / cheat hotkeys.

    Returns True if the event was consumed (i.e. we performed a cheat and
    the normal input handler should NOT also process this key).
    
    Cheats are only active when cheat mode is enabled (toggle with F9).
    """
    global _cheat_mode_enabled
    
    if event.type != pygame.KEYDOWN:
        return False

    key = event.key

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

    # ------------------------------------------------------------------
    # F1: Toggle full-map reveal (ignore FOV radius)
    # ------------------------------------------------------------------
    if key == pygame.K_F1:
        game.debug_reveal_map = not getattr(game, "debug_reveal_map", False)
        game.update_fov()
        game.last_message = (
            "[DEBUG] Full map reveal ON."
            if game.debug_reveal_map
            else "[DEBUG] Full map reveal OFF."
        )
        return True

    # ------------------------------------------------------------------
    # F2: Full heal the player
    # ------------------------------------------------------------------
    if key == pygame.K_F2:
        if game.player is not None:
            game.player.hp = game.player.max_hp
            game.last_message = "[DEBUG] Player fully healed."
        return True

    # ------------------------------------------------------------------
    # F3: +100 gold
    # ------------------------------------------------------------------
    if key == pygame.K_F3:
        if hasattr(game.hero_stats, "add_gold"):
            gained = game.hero_stats.add_gold(100)
        else:
            gained = 100
        game.last_message = f"[DEBUG] Granted {gained} gold."
        return True

    # ------------------------------------------------------------------
    # F4: +25 XP
    # ------------------------------------------------------------------
    if key == pygame.K_F4:
        if hasattr(game.hero_stats, "grant_xp"):
            msgs = game.hero_stats.grant_xp(25)
            if game.player is not None:
                game.apply_hero_stats_to_player(full_heal=False)
            text = " ".join(msgs) if msgs else "Gained 25 XP."
            game.last_message = "[DEBUG] " + text
        return True

    # ------------------------------------------------------------------
    # F8: Skip to next floor (moved from F5 to avoid conflict with save)
    #      (only if not in battle, to avoid weirdness)
    # ------------------------------------------------------------------
    if key == pygame.K_F8:
        from ..core.game import GameMode  # local import to avoid cycles

        if game.mode != GameMode.BATTLE:
            game.floor += 1
            game.load_floor(game.floor, from_direction=None)
            game.last_message = f"[DEBUG] Skipped to floor {game.floor}."
        return True

    # No cheat handled
    return False
