"""
Ambient music manager.

Prefers files in assets/music/ (menu.ogg / explore.ogg / battle.ogg).
Falls back to short procedural loops so the game always has atmosphere.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

import pygame

from .synth import SAMPLE_RATE, build_music_loops
from .sound_manager import ensure_mixer

MUSIC_DIR = Path(__file__).resolve().parents[2] / "assets" / "music"
TRACK_FILES = {
    "menu": ("menu.ogg", "menu.wav", "menu.mp3"),
    "explore": ("explore.ogg", "explore.wav", "explore.mp3"),
    "battle": ("battle.ogg", "battle.wav", "battle.mp3"),
}


class MusicManager:
    def __init__(self) -> None:
        self.enabled: bool = True
        self.master_volume: float = 1.0
        self.music_volume: float = 1.0
        self.muted: bool = False
        # Internal bus trim so default user levels sound balanced with SFX.
        self._bus_trim: float = 0.34
        self._tracks: Dict[str, pygame.mixer.Sound] = {}
        self._ready: bool = False
        self._current: Optional[str] = None
        self._channels: list[pygame.mixer.Channel] = []
        self._active_slot: int = 0

    def init(self) -> bool:
        if self._ready:
            return True

        if not ensure_mixer():
            self.enabled = False
            return False

        try:
            # Keep two channels reserved for crossfading music.
            pygame.mixer.set_num_channels(max(16, pygame.mixer.get_num_channels()))
            pygame.mixer.set_reserved(2)
            self._channels = [pygame.mixer.Channel(0), pygame.mixer.Channel(1)]
        except pygame.error as exc:
            print(f"[music] channel setup failed: {exc}")
            self.enabled = False
            return False

        try:
            from pygame import sndarray

            # Procedural fallbacks first, then override with files if present.
            for name, samples in build_music_loops().items():
                self._tracks[name] = sndarray.make_sound(samples)

            MUSIC_DIR.mkdir(parents=True, exist_ok=True)
            for name, candidates in TRACK_FILES.items():
                for filename in candidates:
                    path = MUSIC_DIR / filename
                    if path.exists():
                        try:
                            self._tracks[name] = pygame.mixer.Sound(str(path))
                            print(f"[music] loaded {path.name}")
                        except pygame.error as exc:
                            print(f"[music] failed to load {path.name}: {exc}")
                        break

            for sound in self._tracks.values():
                sound.set_volume(1.0)

            self._ready = True
            return True
        except Exception as exc:
            print(f"[music] failed to build tracks: {exc}")
            self.enabled = False
            return False

    def apply_user_levels(self, *, master: float, music: float, muted: bool) -> None:
        self.master_volume = max(0.0, min(1.0, master))
        self.music_volume = max(0.0, min(1.0, music))
        self.muted = bool(muted)
        self._push_channel_volume()

    def effective_volume(self) -> float:
        if not self.enabled or self.muted:
            return 0.0
        return self._bus_trim * self.master_volume * self.music_volume

    def _push_channel_volume(self) -> None:
        vol = self.effective_volume()
        for ch in self._channels:
            try:
                ch.set_volume(vol)
            except pygame.error:
                pass

    def set_volume(self, volume: float) -> None:
        """Legacy helper: treat as music bus level (keeps master)."""
        self.music_volume = max(0.0, min(1.0, volume))
        self._push_channel_volume()

    def play(self, name: str, *, fade_ms: int = 900) -> None:
        if not self.enabled or not self._ready:
            return
        if name == self._current:
            # Still refresh volume in case settings changed while same track plays.
            self._push_channel_volume()
            return
        sound = self._tracks.get(name)
        if sound is None:
            return

        try:
            # Crossfade on alternating reserved channels.
            old = self._channels[self._active_slot]
            if old.get_busy():
                old.fadeout(max(0, fade_ms))

            self._active_slot = 1 - self._active_slot
            new = self._channels[self._active_slot]
            new.set_volume(self.effective_volume())
            new.play(sound, loops=-1, fade_ms=max(0, fade_ms))
            self._current = name
        except pygame.error:
            pass

    def stop(self, *, fade_ms: int = 600) -> None:
        if not self._ready:
            return
        try:
            for ch in self._channels:
                if ch.get_busy():
                    ch.fadeout(max(0, fade_ms))
            self._current = None
        except pygame.error:
            pass


_music: Optional[MusicManager] = None


def get_music_manager() -> MusicManager:
    global _music
    if _music is None:
        _music = MusicManager()
    return _music


def init_music() -> bool:
    return get_music_manager().init()


def play_music(name: str, *, fade_ms: int = 900) -> None:
    get_music_manager().play(name, fade_ms=fade_ms)


def stop_music(*, fade_ms: int = 600) -> None:
    get_music_manager().stop(fade_ms=fade_ms)
