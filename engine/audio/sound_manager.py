"""
Simple global sound manager.

Call init_audio() once after pygame.init(), then play_sound("hit") etc.
Fails soft: missing cues / mixer issues never crash gameplay.
"""

from __future__ import annotations

from typing import Dict, Optional

import pygame

from .synth import SAMPLE_RATE, build_library

# Per-cue mix relative to the SFX bus (0..1)
_CUE_VOLUME: Dict[str, float] = {
    "ui_move": 0.35,
    "ui_confirm": 0.45,
    "ui_open": 0.4,
    "ui_close": 0.35,
    "hit": 0.55,
    "dodge": 0.4,
    "crit": 0.7,
    "kill": 0.65,
    "pickup": 0.5,
    "heal": 0.45,
    "level_up": 0.7,
    "victory": 0.75,
    "defeat": 0.65,
    "battle_start": 0.7,
    "skill_cast": 0.5,
}

# Internal bus trim so default user levels (~1.0) sound balanced.
_SFX_BUS_TRIM = 0.55


def ensure_mixer() -> bool:
    """Open (or reopen) the mixer at our synth sample rate."""
    try:
        current = pygame.mixer.get_init()
        if current is None or int(current[0]) != SAMPLE_RATE:
            if current is not None:
                pygame.mixer.quit()
            pygame.mixer.init(
                frequency=SAMPLE_RATE,
                size=-16,
                channels=2,
                buffer=512,
            )
        return pygame.mixer.get_init() is not None
    except pygame.error as exc:
        print(f"[audio] mixer init failed: {exc}")
        return False


class SoundManager:
    def __init__(self) -> None:
        self.enabled: bool = True
        self.master_volume: float = 1.0
        self.sfx_volume: float = 1.0
        self.muted: bool = False
        self._sounds: Dict[str, pygame.mixer.Sound] = {}
        self._ready: bool = False

    def init(self) -> bool:
        """Initialize mixer and build procedural cues. Safe to call more than once."""
        if self._ready:
            return True

        if not ensure_mixer():
            self.enabled = False
            return False

        try:
            from pygame import sndarray

            library = build_library()
            for name, samples in library.items():
                sound = sndarray.make_sound(samples)
                self._sounds[name] = sound
            self._ready = True
            return True
        except Exception as exc:
            print(f"[audio] failed to build sounds: {exc}")
            self.enabled = False
            return False

    def apply_user_levels(self, *, master: float, sfx: float, muted: bool) -> None:
        self.master_volume = max(0.0, min(1.0, master))
        self.sfx_volume = max(0.0, min(1.0, sfx))
        self.muted = bool(muted)

    def effective_volume(self) -> float:
        if not self.enabled or self.muted:
            return 0.0
        return _SFX_BUS_TRIM * self.master_volume * self.sfx_volume

    def play(self, name: str, volume_scale: float = 1.0) -> None:
        if not self.enabled or not self._ready or self.muted:
            return
        sound = self._sounds.get(name)
        if sound is None:
            return
        try:
            base = _CUE_VOLUME.get(name, 0.5) * self.effective_volume()
            sound.set_volume(max(0.0, min(1.0, base * volume_scale)))
            sound.play()
        except pygame.error:
            pass


_manager: Optional[SoundManager] = None


def get_sound_manager() -> SoundManager:
    global _manager
    if _manager is None:
        _manager = SoundManager()
    return _manager


def init_audio() -> bool:
    sfx_ok = get_sound_manager().init()
    from .music_manager import init_music
    music_ok = init_music()
    # Apply saved preferences if config is already loaded; safe defaults otherwise.
    try:
        from .settings import apply_audio_settings
        apply_audio_settings()
    except Exception:
        pass
    return sfx_ok and music_ok


def play_sound(name: str, volume_scale: float = 1.0) -> None:
    get_sound_manager().play(name, volume_scale=volume_scale)
