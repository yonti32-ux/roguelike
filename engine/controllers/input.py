from __future__ import annotations

import pygame

from systems.input import InputManager, InputAction


def create_default_input_manager() -> InputManager:
    """
    Create an InputManager instance with the game's default keyboard bindings.

    This keeps all key-to-action wiring in one place so we can:
    - Tweak controls easily.
    - Add per-profile / per-save custom bindings later.
    - Extend with gamepad bindings without touching game logic.
    """
    mgr = InputManager()

    # ------------------------------------------------------------------
    # Movement: WASD + arrow keys
    # ------------------------------------------------------------------
    mgr.bind_key(InputAction.MOVE_UP, pygame.K_w)
    mgr.bind_key(InputAction.MOVE_UP, pygame.K_UP)

    mgr.bind_key(InputAction.MOVE_DOWN, pygame.K_s)
    mgr.bind_key(InputAction.MOVE_DOWN, pygame.K_DOWN)

    mgr.bind_key(InputAction.MOVE_LEFT, pygame.K_a)
    mgr.bind_key(InputAction.MOVE_LEFT, pygame.K_LEFT)

    mgr.bind_key(InputAction.MOVE_RIGHT, pygame.K_d)
    mgr.bind_key(InputAction.MOVE_RIGHT, pygame.K_RIGHT)

    # ------------------------------------------------------------------
    # Interaction
    # ------------------------------------------------------------------
    mgr.bind_key(InputAction.INTERACT, pygame.K_e)

    # ------------------------------------------------------------------
    # Overlays / meta
    # ------------------------------------------------------------------
    mgr.bind_key(InputAction.TOGGLE_INVENTORY, pygame.K_i)
    mgr.bind_key(InputAction.TOGGLE_CHARACTER_SHEET, pygame.K_c)
    mgr.bind_key(InputAction.TOGGLE_QUEST_SCREEN, pygame.K_j)  # J for Journal/Quests

    # Logs – match HUD hints: K = exploration log, L = battle log.
    mgr.bind_key(InputAction.TOGGLE_BATTLE_LOG, pygame.K_l)
    mgr.bind_key(InputAction.TOGGLE_EXPLORATION_LOG, pygame.K_k)

    # Focus cycling (hero / companions, etc.)
    mgr.bind_key(InputAction.FOCUS_PREV, pygame.K_q)
    mgr.bind_key(InputAction.FOCUS_NEXT, pygame.K_e)

    # ------------------------------------------------------------------
    # List scrolling & paging (inventory, shop, etc.)
    # ------------------------------------------------------------------
    # Line scroll: W/Up/K for up, S/Down/J for down.
    mgr.bind_key(InputAction.SCROLL_UP, pygame.K_w)
    mgr.bind_key(InputAction.SCROLL_UP, pygame.K_UP)
    mgr.bind_key(InputAction.SCROLL_UP, pygame.K_k)

    mgr.bind_key(InputAction.SCROLL_DOWN, pygame.K_s)
    mgr.bind_key(InputAction.SCROLL_DOWN, pygame.K_DOWN)
    mgr.bind_key(InputAction.SCROLL_DOWN, pygame.K_j)

    # Page scroll
    mgr.bind_key(InputAction.PAGE_UP, pygame.K_PAGEUP)
    mgr.bind_key(InputAction.PAGE_DOWN, pygame.K_PAGEDOWN)

    # Generic confirm / cancel
    mgr.bind_key(InputAction.CONFIRM, pygame.K_RETURN)
    mgr.bind_key(InputAction.CONFIRM, pygame.K_KP_ENTER)
    mgr.bind_key(InputAction.CONFIRM, pygame.K_SPACE)

    # Cancel / close overlays:
    # - X is the primary "back/cancel" key
    # - ESC is also bound so fullscreen screens (inventory, character, skills, etc.)
    #   can advertise and respond to ESC to close.
    mgr.bind_key(InputAction.CANCEL, pygame.K_x)
    mgr.bind_key(InputAction.CANCEL, pygame.K_ESCAPE)

    # ------------------------------------------------------------------
    # Battle-related – hotbar + basic attack
    # ------------------------------------------------------------------
    mgr.bind_key(InputAction.END_TURN, pygame.K_TAB)

    # Default hotbar layout: Q / E / F / R -> skill slots 1–4
    mgr.bind_key(InputAction.SKILL_1, pygame.K_q)
    mgr.bind_key(InputAction.SKILL_2, pygame.K_e)
    mgr.bind_key(InputAction.SKILL_3, pygame.K_f)
    mgr.bind_key(InputAction.SKILL_4, pygame.K_r)

    # Dedicated Guard key: always uses the 'guard' skill if the unit has it
    mgr.bind_key(InputAction.GUARD, pygame.K_g)

    # Basic attack: SPACE (same as in the on-screen hint)
    mgr.bind_key(InputAction.BASIC_ATTACK, pygame.K_SPACE)

    return mgr

