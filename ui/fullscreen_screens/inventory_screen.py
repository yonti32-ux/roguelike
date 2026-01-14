"""
Inventory screen module.

For now this is a thin wrapper that delegates to the existing implementation
in ui.hud_screens to avoid behavior changes while we complete the refactor.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from engine.core.game import Game


def draw_inventory_fullscreen(game: "Game") -> None:
    """Full-screen inventory/equipment view."""
    from ui.hud_screens import draw_inventory_fullscreen as _impl

    _impl(game)


