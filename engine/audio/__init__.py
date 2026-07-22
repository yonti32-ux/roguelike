"""Lightweight audio helpers for UI, combat, and ambient music."""

from .sound_manager import get_sound_manager, init_audio, play_sound
from .music_manager import get_music_manager, play_music, stop_music
from .settings import apply_audio_settings

__all__ = [
    "get_sound_manager",
    "get_music_manager",
    "init_audio",
    "play_sound",
    "play_music",
    "stop_music",
    "apply_audio_settings",
]
