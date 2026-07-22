from __future__ import annotations

from enum import Enum
from typing import Dict, Iterable, List, Optional, Set, Union

import pygame


ActionType = Union["InputAction", str]


class InputAction(str, Enum):
    """
    Logical input actions the game can respond to.

    These are intentionally decoupled from any specific key so we can
    remap them, support gamepads, or add keybinding menus later.
    """

    # Movement
    MOVE_UP = "move_up"
    MOVE_DOWN = "move_down"
    MOVE_LEFT = "move_left"
    MOVE_RIGHT = "move_right"

    # Interaction / general confirm-ish
    INTERACT = "interact"

    # Meta / overlays
    TOGGLE_INVENTORY = "toggle_inventory"
    TOGGLE_CHARACTER_SHEET = "toggle_character_sheet"
    TOGGLE_BATTLE_LOG = "toggle_battle_log"
    TOGGLE_EXPLORATION_LOG = "toggle_exploration_log"

    # Focus switching (hero vs companions, etc.)
    FOCUS_NEXT = "focus_next"
    FOCUS_PREV = "focus_prev"

    # List navigation
    SCROLL_UP = "scroll_up"
    SCROLL_DOWN = "scroll_down"
    PAGE_UP = "page_up"
    PAGE_DOWN = "page_down"

    # Generic confirm / cancel
    CONFIRM = "confirm"
    CANCEL = "cancel"

    # Battle-related / player actions
    BASIC_ATTACK = "basic_attack"

    # Hotbar-style skill slots (for future rebinding / skill selection screen)
    SKILL_1 = "skill_1"
    SKILL_2 = "skill_2"
    SKILL_3 = "skill_3"
    SKILL_4 = "skill_4"

    GUARD = "GUARD"
    # Reserved for later (end turn button, etc.)
    END_TURN = "end_turn"


class InputManager:
    """
    Centralised stateful input handler.

    Responsibilities:
    - Maintain bindings: logical InputAction -> one or more pygame keycodes.
    - Track which keys are currently held down.
    - Track which keys were just pressed/released this frame.
    - Provide query helpers in terms of *actions*, not raw keys.
    """

    def __init__(self) -> None:
        # Map from action -> set of pygame key constants
        self._bindings: Dict[InputAction, Set[int]] = {}

        # Low-level key state
        self._keys_down: Set[int] = set()
        self._keys_just_pressed: Set[int] = set()
        self._keys_just_released: Set[int] = set()

    # ------------------------------------------------------------------
    # Binding helpers
    # ------------------------------------------------------------------

    def _normalise_action(self, action: ActionType) -> InputAction:
        """
        Ensure we always use a stable InputAction key internally.

        Accepts either an InputAction or a matching string value.
        """
        if isinstance(action, InputAction):
            return action
        # Will raise ValueError if an unknown string is passed, which is fine:
        # better an explicit crash than silently having a dead binding.
        return InputAction(action)

    def bind_key(self, action: ActionType, key: int) -> None:
        """Bind a pygame key constant to the given logical action."""
        act = self._normalise_action(action)
        if act not in self._bindings:
            self._bindings[act] = set()
        self._bindings[act].add(int(key))

    def unbind_key(self, action: ActionType, key: int) -> None:
        """Remove a specific key binding from an action (if present)."""
        act = self._normalise_action(action)
        if act in self._bindings:
            self._bindings[act].discard(int(key))
            if not self._bindings[act]:
                del self._bindings[act]

    def clear_bindings(self, action: ActionType) -> None:
        """Remove all key bindings for the given action."""
        act = self._normalise_action(action)
        self._bindings.pop(act, None)

    def get_bindings(self, action: ActionType) -> Set[int]:
        """Return a *copy* of the key set bound to the given action."""
        act = self._normalise_action(action)
        return set(self._bindings.get(act, set()))

    # ------------------------------------------------------------------
    # Per-frame lifecycle
    # ------------------------------------------------------------------

    def begin_frame(self) -> None:
        """
        Reset transient per-frame state.

        Call this once per frame *before* processing events.
        """
        self._keys_just_pressed.clear()
        self._keys_just_released.clear()

    # ------------------------------------------------------------------
    # Event processing
    # ------------------------------------------------------------------

    def process_event(self, event: pygame.event.Event) -> None:
        """
        Consume a raw pygame event and update internal key state.

        This does not stop you from also using the event elsewhere;
        InputManager is passive and never "eats" events.
        """
        if event.type == pygame.KEYDOWN:
            key = int(getattr(event, "key", -1))
            if key >= 0 and key not in self._keys_down:
                self._keys_down.add(key)
                self._keys_just_pressed.add(key)

        elif event.type == pygame.KEYUP:
            key = int(getattr(event, "key", -1))
            if key >= 0 and key in self._keys_down:
                self._keys_down.remove(key)
                self._keys_just_released.add(key)

        # Non-key events are ignored here (mouse, joystick, etc.).
        # We'll extend this later if/when we add gamepad support.

    # ------------------------------------------------------------------
    # Action queries
    # ------------------------------------------------------------------

    def _keys_for_action(self, action: ActionType) -> Set[int]:
        act = self._normalise_action(action)
        return self._bindings.get(act, set())

    def is_action_pressed(self, action: ActionType) -> bool:
        """
        True while any bound key is currently held down.

        Good for continuous input like movement.
        """
        keys = self._keys_for_action(action)
        return any(k in self._keys_down for k in keys)

    def was_action_just_pressed(self, action: ActionType) -> bool:
        """
        True only on the frame where the key transitioned from up -> down.

        Good for toggles and single-fire actions (open inventory, end turn...).
        """
        keys = self._keys_for_action(action)
        return any(k in self._keys_just_pressed for k in keys)

    def was_action_just_released(self, action: ActionType) -> bool:
        """Opposite of just_pressed; rarely needed but handy sometimes."""
        keys = self._keys_for_action(action)
        return any(k in self._keys_just_released for k in keys)

    def event_matches_action(self, action: ActionType, event: pygame.event.Event) -> bool:
        """
        Convenience helper for existing event-based code:

        Use inside KEYDOWN/KEYUP handlers:

            if event.type == pygame.KEYDOWN and input_mgr.event_matches_action(
                InputAction.TOGGLE_INVENTORY, event
            ):
                ...

        This lets us migrate code gradually away from hard-coded key constants.
        """
        if event.type not in (pygame.KEYDOWN, pygame.KEYUP):
            return False
        key = getattr(event, "key", None)
        if key is None:
            return False
        keys = self._keys_for_action(action)
        return int(key) in keys
