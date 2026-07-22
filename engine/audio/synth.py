"""
Tiny procedural SFX synth.

Builds short mono int16 samples in memory so the game needs no audio files.
"""

from __future__ import annotations

import math
from typing import Iterable, List

import numpy as np

SAMPLE_RATE = 22050


def _envelope(n: int, attack: float = 0.008, release: float = 0.04) -> np.ndarray:
    env = np.ones(n, dtype=np.float32)
    a = min(n, max(1, int(SAMPLE_RATE * attack)))
    r = min(n, max(1, int(SAMPLE_RATE * release)))
    env[:a] *= np.linspace(0.0, 1.0, a, dtype=np.float32)
    env[-r:] *= np.linspace(1.0, 0.0, r, dtype=np.float32)
    return env


def _tone(
    freq: float,
    duration: float,
    *,
    volume: float = 0.35,
    wave: str = "sine",
    attack: float = 0.008,
    release: float = 0.05,
) -> np.ndarray:
    n = max(1, int(SAMPLE_RATE * duration))
    t = np.arange(n, dtype=np.float32) / SAMPLE_RATE

    if wave == "square":
        raw = np.sign(np.sin(2.0 * math.pi * freq * t))
    elif wave == "triangle":
        raw = 2.0 * np.abs(2.0 * ((t * freq) % 1.0) - 1.0) - 1.0
    elif wave == "noise":
        rng = np.random.default_rng(int(freq * 1000) % (2**31 - 1))
        raw = rng.uniform(-1.0, 1.0, n).astype(np.float32)
    elif wave == "saw":
        raw = 2.0 * ((t * freq) % 1.0) - 1.0
    else:
        raw = np.sin(2.0 * math.pi * freq * t)

    return (raw * _envelope(n, attack=attack, release=release) * volume).astype(np.float32)


def _sweep(
    start_hz: float,
    end_hz: float,
    duration: float,
    *,
    volume: float = 0.3,
    wave: str = "sine",
    attack: float = 0.005,
    release: float = 0.06,
) -> np.ndarray:
    n = max(1, int(SAMPLE_RATE * duration))
    t = np.arange(n, dtype=np.float32) / SAMPLE_RATE
    # Linear freq sweep via phase integration
    freqs = np.linspace(start_hz, end_hz, n, dtype=np.float32)
    phase = 2.0 * math.pi * np.cumsum(freqs) / SAMPLE_RATE

    if wave == "square":
        raw = np.sign(np.sin(phase))
    elif wave == "triangle":
        # Approximate triangle from saw-like phase
        frac = (phase / (2.0 * math.pi)) % 1.0
        raw = 2.0 * np.abs(2.0 * frac - 1.0) - 1.0
    else:
        raw = np.sin(phase)

    return (raw * _envelope(n, attack=attack, release=release) * volume).astype(np.float32)


def _mix(*parts: np.ndarray) -> np.ndarray:
    if not parts:
        return np.zeros(1, dtype=np.float32)
    length = max(p.shape[0] for p in parts)
    out = np.zeros(length, dtype=np.float32)
    for part in parts:
        out[: part.shape[0]] += part
    peak = float(np.max(np.abs(out))) if out.size else 0.0
    if peak > 1.0:
        out /= peak
    return out


def _concat(parts: Iterable[np.ndarray], gap_s: float = 0.0) -> np.ndarray:
    chunks: List[np.ndarray] = []
    gap = np.zeros(max(0, int(SAMPLE_RATE * gap_s)), dtype=np.float32)
    for i, part in enumerate(parts):
        if i > 0 and gap.size:
            chunks.append(gap)
        chunks.append(part)
    if not chunks:
        return np.zeros(1, dtype=np.float32)
    return np.concatenate(chunks)


def _to_int16(samples: np.ndarray) -> np.ndarray:
    """Convert mono float samples to stereo int16 (N, 2) for pygame mixer."""
    clipped = np.clip(samples, -1.0, 1.0)
    mono = (clipped * 32767.0).astype(np.int16)
    # pygame-ce often opens stereo even when channels=1 is requested
    return np.column_stack((mono, mono))


def build_library() -> dict[str, np.ndarray]:
    """Return name -> mono int16 PCM for each built-in cue."""
    ui_move = _tone(520, 0.035, volume=0.18, wave="triangle", release=0.03)

    ui_confirm = _mix(
        _tone(523.25, 0.05, volume=0.22, wave="triangle"),
        _tone(784.99, 0.07, volume=0.2, wave="sine", attack=0.01),
    )

    hit_body = _tone(90, 0.07, volume=0.45, wave="sine", attack=0.001, release=0.06)
    hit_crack = _tone(180, 0.04, volume=0.25, wave="square", attack=0.001, release=0.03)
    hit_noise = _tone(1, 0.045, volume=0.22, wave="noise", attack=0.001, release=0.04)
    hit = _mix(hit_body, hit_crack, hit_noise)

    dodge = _mix(
        _sweep(700, 220, 0.1, volume=0.16, wave="sine", release=0.08),
        _tone(1, 0.08, volume=0.08, wave="noise", release=0.07),
    )

    crit_spark = _concat(
        [
            _tone(880, 0.04, volume=0.22, wave="triangle"),
            _tone(1175, 0.045, volume=0.2, wave="sine"),
            _tone(1568, 0.06, volume=0.18, wave="sine"),
        ],
        gap_s=0.012,
    )
    crit = _mix(hit, crit_spark)

    kill_thud = _tone(65, 0.12, volume=0.5, wave="sine", attack=0.001, release=0.1)
    kill_ring = _sweep(420, 180, 0.18, volume=0.18, wave="triangle", release=0.14)
    kill = _mix(kill_thud, hit_noise, kill_ring)

    pickup = _concat(
        [
            _tone(988, 0.04, volume=0.2, wave="triangle", release=0.03),
            _tone(1319, 0.05, volume=0.18, wave="sine", release=0.04),
            _tone(1760, 0.07, volume=0.14, wave="sine", release=0.05),
        ],
        gap_s=0.015,
    )

    heal = _mix(
        _sweep(330, 660, 0.14, volume=0.18, wave="sine", release=0.1),
        _tone(880, 0.1, volume=0.12, wave="triangle", attack=0.02, release=0.08),
    )

    level_up = _concat(
        [
            _tone(523.25, 0.08, volume=0.22, wave="triangle"),
            _tone(659.25, 0.08, volume=0.22, wave="triangle"),
            _tone(783.99, 0.08, volume=0.22, wave="triangle"),
            _tone(1046.5, 0.16, volume=0.24, wave="sine", release=0.12),
        ],
        gap_s=0.02,
    )

    victory = _concat(
        [
            _tone(523.25, 0.09, volume=0.24, wave="triangle"),
            _tone(659.25, 0.09, volume=0.24, wave="triangle"),
            _tone(783.99, 0.09, volume=0.24, wave="triangle"),
            _mix(
                _tone(1046.5, 0.22, volume=0.26, wave="sine", release=0.16),
                _tone(1318.5, 0.22, volume=0.14, wave="triangle", release=0.16),
            ),
        ],
        gap_s=0.025,
    )

    defeat = _concat(
        [
            _tone(392, 0.14, volume=0.22, wave="sine", release=0.1),
            _tone(311, 0.16, volume=0.2, wave="sine", release=0.12),
            _tone(233, 0.28, volume=0.22, wave="triangle", release=0.2),
        ],
        gap_s=0.03,
    )

    battle_start = _mix(
        _sweep(140, 420, 0.16, volume=0.28, wave="saw", attack=0.002, release=0.1),
        _tone(90, 0.18, volume=0.35, wave="sine", attack=0.001, release=0.14),
        _concat(
            [
                _tone(523, 0.05, volume=0.16, wave="triangle"),
                _tone(392, 0.08, volume=0.18, wave="triangle"),
            ],
            gap_s=0.02,
        ),
    )

    skill_cast = _mix(
        _sweep(480, 920, 0.12, volume=0.2, wave="sine", release=0.09),
        _tone(1, 0.09, volume=0.1, wave="noise", attack=0.005, release=0.07),
        _tone(660, 0.08, volume=0.12, wave="triangle", attack=0.01, release=0.06),
    )

    ui_open = _mix(
        _sweep(280, 560, 0.07, volume=0.16, wave="triangle", release=0.05),
        _tone(840, 0.05, volume=0.12, wave="sine", attack=0.01),
    )

    ui_close = _mix(
        _sweep(560, 260, 0.07, volume=0.14, wave="triangle", release=0.05),
        _tone(420, 0.05, volume=0.1, wave="sine", attack=0.01),
    )

    return {
        "ui_move": _to_int16(ui_move),
        "ui_confirm": _to_int16(ui_confirm),
        "ui_open": _to_int16(ui_open),
        "ui_close": _to_int16(ui_close),
        "hit": _to_int16(hit),
        "dodge": _to_int16(dodge),
        "crit": _to_int16(crit),
        "kill": _to_int16(kill),
        "pickup": _to_int16(pickup),
        "heal": _to_int16(heal),
        "level_up": _to_int16(level_up),
        "victory": _to_int16(victory),
        "defeat": _to_int16(defeat),
        "battle_start": _to_int16(battle_start),
        "skill_cast": _to_int16(skill_cast),
    }


def _drone(freq: float, duration: float, volume: float, lfo_hz: float = 0.25) -> np.ndarray:
    """Seamless-ish sine drone (duration should contain integer cycles of freq + lfo)."""
    n = max(1, int(SAMPLE_RATE * duration))
    t = np.arange(n, dtype=np.float32) / SAMPLE_RATE
    wave = np.sin(2.0 * math.pi * freq * t)
    lfo = 0.72 + 0.28 * np.sin(2.0 * math.pi * lfo_hz * t)
    return (wave * lfo * volume).astype(np.float32)


def _midi_to_hz(midi: float) -> float:
    return 440.0 * (2.0 ** ((midi - 69.0) / 12.0))


def _adsr(
    n: int,
    *,
    attack: float = 0.02,
    decay: float = 0.08,
    sustain: float = 0.65,
    release: float = 0.12,
) -> np.ndarray:
    env = np.zeros(n, dtype=np.float32)
    if n <= 0:
        return env
    a = min(n, max(1, int(SAMPLE_RATE * attack)))
    d = min(n - a, max(1, int(SAMPLE_RATE * decay)))
    r = min(n, max(1, int(SAMPLE_RATE * release)))
    s_len = max(0, n - a - d - r)

    env[:a] = np.linspace(0.0, 1.0, a, dtype=np.float32)
    if d > 0:
        env[a : a + d] = np.linspace(1.0, sustain, d, dtype=np.float32)
    if s_len > 0:
        env[a + d : a + d + s_len] = sustain
    start_r = n - r
    start_val = float(env[start_r - 1]) if start_r > 0 else sustain
    env[start_r:] = np.linspace(start_val, 0.0, r, dtype=np.float32)
    return env


def _synth_note(
    freq: float,
    duration: float,
    *,
    volume: float = 0.2,
    wave: str = "sine",
    attack: float = 0.02,
    decay: float = 0.08,
    sustain: float = 0.65,
    release: float = 0.12,
) -> np.ndarray:
    n = max(1, int(SAMPLE_RATE * duration))
    t = np.arange(n, dtype=np.float32) / SAMPLE_RATE
    if wave == "triangle":
        raw = 2.0 * np.abs(2.0 * ((t * freq) % 1.0) - 1.0) - 1.0
    elif wave == "square":
        raw = np.sign(np.sin(2.0 * math.pi * freq * t)) * 0.55
    elif wave == "saw":
        raw = (2.0 * ((t * freq) % 1.0) - 1.0) * 0.45
    elif wave == "pluck":
        # Bright decaying pluck: triangle + light overtone
        raw = (
            (2.0 * np.abs(2.0 * ((t * freq) % 1.0) - 1.0) - 1.0) * 0.7
            + np.sin(2.0 * math.pi * freq * 2.0 * t) * 0.3
        )
    elif wave == "pad":
        raw = (
            np.sin(2.0 * math.pi * freq * t) * 0.55
            + np.sin(2.0 * math.pi * freq * 1.5 * t) * 0.25
            + np.sin(2.0 * math.pi * freq * 2.0 * t) * 0.2
        )
    else:
        raw = np.sin(2.0 * math.pi * freq * t)

    env = _adsr(n, attack=attack, decay=decay, sustain=sustain, release=release)
    return (raw.astype(np.float32) * env * volume).astype(np.float32)


def _place(track: np.ndarray, sample: np.ndarray, start_s: float) -> None:
    start = int(start_s * SAMPLE_RATE)
    if start >= track.shape[0] or start < 0:
        return
    end = min(track.shape[0], start + sample.shape[0])
    track[start:end] += sample[: end - start]


def _kick(duration: float = 0.18, volume: float = 0.35) -> np.ndarray:
    n = max(1, int(SAMPLE_RATE * duration))
    t = np.arange(n, dtype=np.float32) / SAMPLE_RATE
    freq = 110.0 * (0.15 ** t)  # pitch drop
    phase = 2.0 * math.pi * np.cumsum(freq) / SAMPLE_RATE
    env = np.exp(-t * 18.0).astype(np.float32)
    return (np.sin(phase) * env * volume).astype(np.float32)


def _hat(duration: float = 0.05, volume: float = 0.08) -> np.ndarray:
    n = max(1, int(SAMPLE_RATE * duration))
    rng = np.random.default_rng(7)
    noise = rng.uniform(-1.0, 1.0, n).astype(np.float32)
    env = np.exp(-np.arange(n, dtype=np.float32) / SAMPLE_RATE * 55.0)
    return (noise * env * volume).astype(np.float32)


def _snare(duration: float = 0.12, volume: float = 0.18) -> np.ndarray:
    n = max(1, int(SAMPLE_RATE * duration))
    t = np.arange(n, dtype=np.float32) / SAMPLE_RATE
    rng = np.random.default_rng(11)
    noise = rng.uniform(-1.0, 1.0, n).astype(np.float32)
    body = np.sin(2.0 * math.pi * 180.0 * t) * np.exp(-t * 30.0)
    env = np.exp(-t * 22.0)
    return ((noise * 0.7 + body * 0.3) * env * volume).astype(np.float32)


def _render_progression(
    *,
    bpm: float,
    bars: int,
    chords: list[list[int]],
    bass_pattern: list[tuple[float, float, int, float]],
    melody: list[tuple[float, float, int, float]],
    style: str,
) -> np.ndarray:
    """
    Render a looping song section.

    chords: list of MIDI chord tone lists, one per bar (loops if shorter).
    bass_pattern / melody: (beat_in_loop, dur_beats, midi, velocity)
    style: "menu" | "explore" | "battle"
    """
    beat = 60.0 / bpm
    duration = bars * 4 * beat
    n = max(1, int(SAMPLE_RATE * duration))
    out = np.zeros(n, dtype=np.float32)

    # Harmony pads / stabs per bar
    for bar in range(bars):
        chord = chords[bar % len(chords)]
        bar_start = bar * 4 * beat
        if style == "battle":
            # Rhythmic chord stabs on beats 1 and 3
            for stab_beat in (0.0, 2.0):
                for midi in chord:
                    note = _synth_note(
                        _midi_to_hz(midi),
                        beat * 0.7,
                        volume=0.045,
                        wave="saw",
                        attack=0.01,
                        decay=0.08,
                        sustain=0.35,
                        release=0.12,
                    )
                    _place(out, note, bar_start + stab_beat * beat)
        elif style == "explore":
            for midi in chord:
                note = _synth_note(
                    _midi_to_hz(midi),
                    beat * 3.6,
                    volume=0.035,
                    wave="pad",
                    attack=0.25,
                    decay=0.4,
                    sustain=0.55,
                    release=0.8,
                )
                _place(out, note, bar_start + 0.05)
            # Soft arp
            arp = chord + [chord[0] + 12]
            for i, midi in enumerate(arp[:4]):
                note = _synth_note(
                    _midi_to_hz(midi),
                    beat * 0.85,
                    volume=0.05,
                    wave="pluck",
                    attack=0.005,
                    decay=0.12,
                    sustain=0.25,
                    release=0.25,
                )
                _place(out, note, bar_start + i * beat)
        else:  # menu
            for midi in chord:
                note = _synth_note(
                    _midi_to_hz(midi),
                    beat * 3.8,
                    volume=0.04,
                    wave="pad",
                    attack=0.3,
                    decay=0.35,
                    sustain=0.6,
                    release=0.7,
                )
                _place(out, note, bar_start)
            # Rolling arp across the bar
            arp = [chord[0], chord[1], chord[2], chord[1], chord[0] + 12, chord[2], chord[1], chord[0]]
            for i, midi in enumerate(arp):
                note = _synth_note(
                    _midi_to_hz(midi),
                    beat * 0.45,
                    volume=0.055,
                    wave="pluck",
                    attack=0.004,
                    decay=0.1,
                    sustain=0.2,
                    release=0.18,
                )
                _place(out, note, bar_start + i * (beat * 0.5))

    # Bass
    for start_beat, dur_beats, midi, vel in bass_pattern:
        wave = "sine" if style != "battle" else "triangle"
        note = _synth_note(
            _midi_to_hz(midi),
            dur_beats * beat * 0.95,
            volume=0.16 * vel,
            wave=wave,
            attack=0.01 if style == "battle" else 0.04,
            decay=0.1,
            sustain=0.55 if style != "battle" else 0.4,
            release=0.15,
        )
        _place(out, note, start_beat * beat)

    # Melody
    for start_beat, dur_beats, midi, vel in melody:
        wave = "triangle" if style == "menu" else ("sine" if style == "explore" else "saw")
        note = _synth_note(
            _midi_to_hz(midi),
            dur_beats * beat * 0.92,
            volume=0.12 * vel,
            wave=wave,
            attack=0.02,
            decay=0.1,
            sustain=0.5,
            release=0.18,
        )
        _place(out, note, start_beat * beat)

    # Percussion for battle (and light pulse for explore)
    if style == "battle":
        for bar in range(bars):
            base = bar * 4
            for b in (0, 2):
                _place(out, _kick(volume=0.28), (base + b) * beat)
            for b in (1, 3):
                _place(out, _snare(volume=0.14), (base + b) * beat)
            for b in range(8):
                _place(out, _hat(volume=0.045), (base + b * 0.5) * beat)
    elif style == "explore":
        for bar in range(bars):
            _place(out, _kick(duration=0.22, volume=0.1), (bar * 4) * beat)

    # Soft root drone under everything for glue
    root = chords[0][0] - 12
    out += _drone(_midi_to_hz(root), duration, 0.04 if style != "battle" else 0.03, lfo_hz=0.125)

    # Soft loop crossfade: blend end toward start so wrap is less audible
    xfade = min(n // 8, int(SAMPLE_RATE * 0.05))
    if xfade > 1:
        fade = np.linspace(0.0, 1.0, xfade, dtype=np.float32)
        out[-xfade:] = out[-xfade:] * (1.0 - fade) + out[:xfade] * fade

    peak = float(np.max(np.abs(out))) if out.size else 0.0
    if peak > 0.95:
        out *= 0.95 / peak
    return out


def build_music_loops(duration: float = 16.0) -> dict[str, np.ndarray]:
    """
    Build looping musical tracks for menu / explore / battle.

    `duration` is approximate; exact length follows BPM * bars.
    """
    # --- Menu: warm D-minor fantasy title theme (96 BPM, 8 bars) ---
    # Dm - Bb - F - C
    menu_chords = [
        [50, 53, 57],  # D3 F A
        [46, 50, 53],  # Bb2 D F
        [53, 57, 60],  # F3 A C
        [48, 52, 55],  # C3 E G
    ]
    menu_bass = []
    menu_melody = []
    for bar, root in enumerate([38, 34, 41, 36]):  # D2 Bb1 F2 C2
        base = bar * 4
        menu_bass.append((base + 0.0, 2.0, root, 1.0))
        menu_bass.append((base + 2.0, 2.0, root + 7, 0.75))
    # Two-phrase melody over 8 bars (repeat progression twice)
    menu_chords = menu_chords * 2
    motif = [
        (0.0, 1.5, 69, 1.0),   # A4
        (1.5, 0.5, 72, 0.85),  # C5
        (2.0, 1.0, 74, 0.95),  # D5
        (3.0, 1.0, 72, 0.8),
        (4.0, 1.5, 70, 0.9),   # Bb4
        (5.5, 0.5, 69, 0.75),
        (6.0, 2.0, 67, 0.85),  # G4
        (8.0, 1.0, 69, 0.9),
        (9.0, 1.0, 72, 0.85),
        (10.0, 1.0, 74, 1.0),
        (11.0, 1.0, 77, 0.9),  # F5
        (12.0, 2.0, 76, 0.95), # E5
        (14.0, 2.0, 74, 1.0),  # D5
    ]
    menu_melody.extend(motif)
    # Second half echoes softer / slightly varied
    for start, dur, midi, vel in motif:
        menu_melody.append((start + 16.0, dur, midi - 5 if start >= 12 else midi, vel * 0.85))
    for bar, root in enumerate([38, 34, 41, 36]):
        base = 16 + bar * 4
        menu_bass.append((base + 0.0, 2.0, root, 0.95))
        menu_bass.append((base + 2.0, 2.0, root + 7, 0.7))

    menu = _render_progression(
        bpm=96.0,
        bars=8,
        chords=menu_chords,
        bass_pattern=menu_bass,
        melody=menu_melody,
        style="menu",
    )

    # --- Explore: dark A-minor dungeon theme (80 BPM, 8 bars) ---
    # Am - Dm - Em - Am
    explore_chords = [
        [45, 48, 52],  # A2 C E
        [50, 53, 57],  # D3 F A
        [52, 55, 59],  # E3 G B
        [45, 48, 52],
    ] * 2
    explore_bass = []
    for bar, root in enumerate([33, 38, 40, 33, 33, 38, 40, 33]):  # A1 D2 E2 ...
        base = bar * 4
        explore_bass.append((base + 0.0, 3.0, root, 1.0))
        explore_bass.append((base + 3.0, 1.0, root + 5, 0.6))
    explore_melody = [
        (0.0, 2.0, 64, 0.7),   # E4
        (4.0, 2.0, 65, 0.65),  # F4
        (8.0, 1.5, 67, 0.7),   # G4
        (9.5, 0.5, 65, 0.55),
        (10.0, 2.0, 64, 0.65),
        (16.0, 2.0, 60, 0.6),  # C4
        (20.0, 2.0, 64, 0.7),
        (24.0, 1.0, 67, 0.65),
        (25.0, 1.0, 69, 0.7),  # A4
        (26.0, 2.0, 64, 0.75),
    ]
    explore = _render_progression(
        bpm=80.0,
        bars=8,
        chords=explore_chords,
        bass_pattern=explore_bass,
        melody=explore_melody,
        style="explore",
    )

    # --- Battle: driving E-minor combat loop (128 BPM, 8 bars) ---
    # Em - C - D - Em
    battle_chords = [
        [52, 55, 59],  # E3 G B
        [48, 52, 55],  # C3 E G
        [50, 54, 57],  # D3 F# A
        [52, 55, 59],
    ] * 2
    battle_bass = []
    for bar, root in enumerate([40, 36, 38, 40, 40, 36, 38, 40]):  # E2 C2 D2 ...
        base = bar * 4
        battle_bass.extend(
            [
                (base + 0.0, 0.5, root, 1.0),
                (base + 0.5, 0.5, root, 0.7),
                (base + 1.0, 0.5, root + 7, 0.85),
                (base + 1.5, 0.5, root, 0.7),
                (base + 2.0, 0.5, root, 1.0),
                (base + 2.5, 0.5, root + 3, 0.75),
                (base + 3.0, 0.5, root + 7, 0.85),
                (base + 3.5, 0.5, root, 0.7),
            ]
        )
    # Aggressive ostinato melody
    battle_melody = []
    ostinato = [71, 67, 69, 67, 71, 74, 72, 71]  # B4 G4 A4 ...
    for bar in range(8):
        base = bar * 4
        for i, midi in enumerate(ostinato):
            battle_melody.append((base + i * 0.5, 0.45, midi if bar % 2 == 0 else midi - 2, 0.85))

    battle = _render_progression(
        bpm=128.0,
        bars=8,
        chords=battle_chords,
        bass_pattern=battle_bass,
        melody=battle_melody,
        style="battle",
    )

    # Keep overall music quieter than SFX
    return {
        "menu": _to_int16(menu * 0.75),
        "explore": _to_int16(explore * 0.72),
        "battle": _to_int16(battle * 0.7),
    }
