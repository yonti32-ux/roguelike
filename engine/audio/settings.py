"""
Apply persisted audio preferences to the live mixers.

User-facing knobs (all 0..1 except mute):
  - master_volume
  - music_volume
  - sfx_volume
  - audio_muted

These are intentionally broad so future categories (UI, ambience, voice, etc.)
can hang off the same master/mute path.
"""

from __future__ import annotations

from typing import Any, Optional


def apply_audio_settings(config: Optional[Any] = None) -> None:
    """Push config audio values into SoundManager + MusicManager."""
    if config is None:
        from engine.core.config import get_config
        config = get_config()

    master = float(getattr(config, "master_volume", 1.0))
    music = float(getattr(config, "music_volume", 0.7))
    sfx = float(getattr(config, "sfx_volume", 0.85))
    muted = bool(getattr(config, "audio_muted", False))

    from .sound_manager import get_sound_manager
    from .music_manager import get_music_manager

    get_sound_manager().apply_user_levels(master=master, sfx=sfx, muted=muted)
    get_music_manager().apply_user_levels(master=master, music=music, muted=muted)
