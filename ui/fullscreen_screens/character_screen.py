"""
Character sheet screen module.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List

from settings import COLOR_BG
from systems.party import CompanionState, get_companion, ensure_companion_stats
from ui.screen_components import (
    render_character_header,
    render_stats_section,
    render_perks_section,
)
from ui.screen_utils import safe_getattr

if TYPE_CHECKING:
    from engine.core.game import Game


def draw_character_sheet_fullscreen(game: "Game") -> None:
    """Full-screen character sheet view."""
    # To avoid duplicating logic and risking subtle bugs, this function
    # currently delegates to the implementation in ui.hud_screens.
    #
    # Once the inventory screen is fully split out, the shared helpers
    # can be moved into a dedicated module and this wrapper can be
    # replaced with a fully standalone implementation if desired.
    from ui.hud_screens import draw_character_sheet_fullscreen as _impl

    _impl(game)


