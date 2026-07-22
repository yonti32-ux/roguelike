"""
Shared atmospheric effects for menu screens.
Keeps menus feeling alive without duplicating particle logic.
"""

from __future__ import annotations

import math
import random
from typing import Dict, List, Optional, Tuple

import pygame

from settings import COLOR_BG


Color = Tuple[int, int, int]
ColorA = Tuple[int, int, int, int]


class MenuAtmosphere:
    """Floating particles, mist, vignette, and soft ambient motion for menus."""

    def __init__(
        self,
        screen: pygame.Surface,
        *,
        intensity: float = 1.0,
        warm: bool = True,
    ) -> None:
        self.screen = screen
        self.intensity = max(0.2, intensity)
        self.warm = warm
        self.timer = 0.0
        self.embers: List[Dict] = []
        self.dust: List[Dict] = []
        self.sparks: List[Dict] = []
        self.mist: List[Dict] = []
        self.fireflies: List[Dict] = []
        self.bursts: List[Dict] = []
        self._spark_cooldown = 0.0
        self._last_selected: Optional[int] = None
        self._layers: Dict[str, pygame.Surface] = {}
        self._vignette: Optional[pygame.Surface] = None
        self._vignette_size: Tuple[int, int] = (0, 0)
        self._init_particles()

    def _palette(self) -> List[Color]:
        if self.warm:
            return [
                (255, 180, 90),
                (255, 140, 60),
                (220, 200, 120),
                (180, 120, 70),
                (255, 220, 160),
            ]
        return [
            (100, 150, 255),
            (150, 200, 255),
            (180, 160, 255),
            (120, 180, 220),
            (200, 210, 255),
        ]

    def _layer(self, key: str, size: Tuple[int, int]) -> pygame.Surface:
        surf = self._layers.get(key)
        if surf is None or surf.get_size() != size:
            surf = pygame.Surface(size, pygame.SRCALPHA)
            self._layers[key] = surf
        else:
            surf.fill((0, 0, 0, 0))
        return surf

    def _init_particles(self) -> None:
        w, h = self.screen.get_size()
        palette = self._palette()
        ember_count = int(16 * self.intensity)
        dust_count = int(22 * self.intensity)
        mist_count = max(2, int(3 * self.intensity))
        firefly_count = int(6 * self.intensity)

        self.embers = []
        for _ in range(ember_count):
            self.embers.append(self._make_ember(w, h, palette, scatter=True))

        self.dust = []
        for _ in range(dust_count):
            self.dust.append({
                "x": random.uniform(0, w),
                "y": random.uniform(0, h),
                "vx": random.uniform(-12, 12),
                "vy": random.uniform(-8, 8),
                "size": random.uniform(1.0, 2.2),
                "phase": random.uniform(0, math.pi * 2),
                "color": random.choice(palette),
                "base_alpha": random.randint(30, 90),
            })

        self.mist = []
        for i in range(mist_count):
            self.mist.append({
                "y": h * (0.15 + 0.7 * (i / max(1, mist_count - 1))),
                "phase": random.uniform(0, math.pi * 2),
                "speed": random.uniform(0.15, 0.35),
                "height": random.randint(40, 90),
                "alpha": random.randint(10, 22),
            })

        self.fireflies = []
        for _ in range(firefly_count):
            self.fireflies.append({
                "x": random.uniform(0, w),
                "y": random.uniform(h * 0.2, h * 0.85),
                "phase": random.uniform(0, math.pi * 2),
                "speed": random.uniform(0.8, 1.6),
                "orbit": random.uniform(18, 40),
                "base_x": 0.0,
                "base_y": 0.0,
                "color": random.choice(palette),
            })
            self.fireflies[-1]["base_x"] = self.fireflies[-1]["x"]
            self.fireflies[-1]["base_y"] = self.fireflies[-1]["y"]

        self.sparks = []
        self.bursts = []

    def _make_ember(
        self,
        w: int,
        h: int,
        palette: List[Color],
        *,
        scatter: bool = False,
    ) -> Dict:
        return {
            "x": random.uniform(0, w),
            "y": random.uniform(0, h) if scatter else h + random.uniform(0, 40),
            "vx": random.uniform(-18, 18),
            "vy": random.uniform(-55, -22),
            "size": random.uniform(1.5, 3.5),
            "phase": random.uniform(0, math.pi * 2),
            "life": random.uniform(2.5, 6.0) if not scatter else random.uniform(1.0, 5.0),
            "max_life": random.uniform(3.5, 6.5),
            "color": random.choice(palette),
            "wobble": random.uniform(8, 22),
        }

    def resize(self, screen: pygame.Surface) -> None:
        """Call if the display surface changes size."""
        self.screen = screen
        self._init_particles()

    def notify_selection(self, selected_index: int, center: Optional[Tuple[int, int]] = None) -> None:
        """Spawn a short burst when the highlighted option changes."""
        if self._last_selected is None:
            self._last_selected = selected_index
            return
        if selected_index == self._last_selected:
            return
        self._last_selected = selected_index
        w, h = self.screen.get_size()
        cx, cy = center if center is not None else (w // 2, h // 2)
        self.spawn_burst(cx, cy, count=10)

    def spawn_burst(self, x: float, y: float, *, count: int = 12, color: Optional[Color] = None) -> None:
        palette = self._palette()
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(40, 140)
            c = color or random.choice(palette)
            self.bursts.append({
                "x": x,
                "y": y,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "life": random.uniform(0.25, 0.55),
                "max_life": 0.55,
                "size": random.uniform(1.5, 3.5),
                "color": c,
            })

    def update(self, dt: float) -> None:
        self.timer += dt
        w, h = self.screen.get_size()
        palette = self._palette()

        for ember in self.embers:
            ember["phase"] += dt * 2.2
            ember["x"] += (ember["vx"] + math.sin(ember["phase"]) * ember["wobble"]) * dt
            ember["y"] += ember["vy"] * dt
            ember["life"] -= dt
            if ember["life"] <= 0 or ember["y"] < -20 or ember["x"] < -30 or ember["x"] > w + 30:
                ember.update(self._make_ember(w, h, palette))

        for mote in self.dust:
            mote["phase"] += dt * 1.4
            mote["x"] += (mote["vx"] + math.sin(mote["phase"]) * 10) * dt
            mote["y"] += (mote["vy"] + math.cos(mote["phase"] * 0.7) * 6) * dt
            if mote["x"] < -10:
                mote["x"] = w + 10
            elif mote["x"] > w + 10:
                mote["x"] = -10
            if mote["y"] < -10:
                mote["y"] = h + 10
            elif mote["y"] > h + 10:
                mote["y"] = -10

        for band in self.mist:
            band["phase"] += dt * band["speed"]

        for fly in self.fireflies:
            fly["phase"] += dt * fly["speed"]
            fly["x"] = fly["base_x"] + math.sin(fly["phase"]) * fly["orbit"]
            fly["y"] = fly["base_y"] + math.cos(fly["phase"] * 0.7) * (fly["orbit"] * 0.45)
            # Slow drift of home position
            fly["base_x"] += math.sin(fly["phase"] * 0.2) * 8 * dt
            fly["base_y"] += math.cos(fly["phase"] * 0.15) * 5 * dt
            if fly["base_x"] < 0:
                fly["base_x"] = w
            elif fly["base_x"] > w:
                fly["base_x"] = 0
            if fly["base_y"] < h * 0.1:
                fly["base_y"] = h * 0.8
            elif fly["base_y"] > h * 0.9:
                fly["base_y"] = h * 0.2

        self._spark_cooldown -= dt
        if self._spark_cooldown <= 0 and self.intensity >= 0.7:
            self._spark_cooldown = random.uniform(0.35, 1.1)
            self.sparks.append({
                "x": random.uniform(w * 0.15, w * 0.85),
                "y": random.uniform(h * 0.15, h * 0.75),
                "vx": random.uniform(-40, 40),
                "vy": random.uniform(-80, -20),
                "life": random.uniform(0.35, 0.8),
                "max_life": 0.8,
                "size": random.uniform(1.5, 3.0),
                "color": random.choice(palette),
            })

        alive = []
        for spark in self.sparks:
            spark["life"] -= dt
            spark["x"] += spark["vx"] * dt
            spark["y"] += spark["vy"] * dt
            spark["vy"] += 40 * dt
            if spark["life"] > 0:
                alive.append(spark)
        self.sparks = alive

        alive_bursts = []
        for burst in self.bursts:
            burst["life"] -= dt
            burst["x"] += burst["vx"] * dt
            burst["y"] += burst["vy"] * dt
            burst["vy"] += 90 * dt
            burst["vx"] *= 0.96
            if burst["life"] > 0:
                alive_bursts.append(burst)
        self.bursts = alive_bursts

    def draw_background(self) -> None:
        """Fill with animated gradient + mist + vignette + particles."""
        w, h = self.screen.get_size()
        self.screen.fill(COLOR_BG)
        overlay = self._layer("bg", (w, h))

        # Soft vertical gradient wash (coarse bands)
        pulse = 0.5 + 0.5 * math.sin(self.timer * 0.55)
        top_alpha = int((18 + 10 * pulse) * self.intensity)
        mid_alpha = int((10 + 6 * pulse) * self.intensity)
        if self.warm:
            top = (70, 35, 18, top_alpha)
            mid = (35, 22, 40, mid_alpha)
        else:
            top = (25, 35, 70, top_alpha)
            mid = (30, 20, 55, mid_alpha)

        band_h = max(8, h // 24)
        for i in range(0, h, band_h):
            t = i / max(1, h - 1)
            if t < 0.45:
                u = t / 0.45
                color = self._lerp_color(top, mid, u)
            else:
                u = (t - 0.45) / 0.55
                bottom = (*COLOR_BG, 0)
                color = self._lerp_color(mid, bottom, u)
            pygame.draw.rect(overlay, color, (0, i, w, band_h + 1))

        # Slow drifting light shaft
        shaft_x = w * (0.35 + 0.12 * math.sin(self.timer * 0.25))
        shaft_w = int(w * (0.18 + 0.04 * math.sin(self.timer * 0.4)))
        shaft_alpha = int(18 * self.intensity)
        shaft_color = (255, 210, 140, shaft_alpha) if self.warm else (160, 190, 255, shaft_alpha)
        points = [
            (shaft_x - shaft_w * 0.2, -10),
            (shaft_x + shaft_w * 0.2, -10),
            (shaft_x + shaft_w, h + 10),
            (shaft_x - shaft_w, h + 10),
        ]
        pygame.draw.polygon(overlay, shaft_color, points)

        self._draw_mist(overlay, w, h)
        self._draw_particles(overlay)
        self._draw_fireflies(overlay)
        self._draw_bursts(overlay)
        self.screen.blit(overlay, (0, 0))
        self._blit_vignette(w, h)

    def draw_overlay_only(self) -> None:
        """For pause overlays: particles + vignette without clearing the frame."""
        w, h = self.screen.get_size()
        overlay = self._layer("ov", (w, h))
        self._draw_mist(overlay, w, h)
        self._draw_particles(overlay)
        self._draw_fireflies(overlay)
        self._draw_bursts(overlay)
        self.screen.blit(overlay, (0, 0))
        self._blit_vignette(w, h, strength=0.55)

    def draw_foreground_fx(self) -> None:
        """Draw only transient bursts/fireflies on top of UI content."""
        w, h = self.screen.get_size()
        overlay = self._layer("fg", (w, h))
        self._draw_fireflies(overlay)
        self._draw_bursts(overlay)
        self.screen.blit(overlay, (0, 0))

    def _draw_mist(self, target: pygame.Surface, w: int, h: int) -> None:
        for band in self.mist:
            drift = math.sin(band["phase"]) * (w * 0.08)
            alpha = int(band["alpha"] * self.intensity * (0.7 + 0.3 * abs(math.sin(band["phase"] * 1.3))))
            if self.warm:
                color = (90, 55, 35, alpha)
            else:
                color = (40, 55, 90, alpha)
            rect = pygame.Rect(int(-w * 0.1 + drift), int(band["y"] - band["height"] // 2), int(w * 1.2), band["height"])
            pygame.draw.ellipse(target, color, rect)

    def _draw_particles(self, target: pygame.Surface) -> None:
        for mote in self.dust:
            alpha = int(
                mote["base_alpha"]
                * (0.55 + 0.45 * abs(math.sin(mote["phase"])))
                * self.intensity
            )
            pygame.draw.circle(
                target,
                (*mote["color"], alpha),
                (int(mote["x"]), int(mote["y"])),
                max(1, int(mote["size"])),
            )

        for ember in self.embers:
            life_t = max(0.0, min(1.0, ember["life"] / ember["max_life"]))
            fade = life_t * (0.65 + 0.35 * abs(math.sin(ember["phase"] * 1.7)))
            alpha = int(160 * fade * self.intensity)
            size = max(1, int(ember["size"] * (0.7 + 0.5 * fade)))
            x, y = int(ember["x"]), int(ember["y"])
            pygame.draw.circle(target, (*ember["color"], alpha // 3), (x, y), size * 2)
            pygame.draw.circle(target, (*ember["color"], alpha), (x, y), size)

        for spark in self.sparks:
            life_t = max(0.0, spark["life"] / spark["max_life"])
            alpha = int(220 * life_t * self.intensity)
            size = max(1, int(spark["size"] * (0.6 + 0.8 * life_t)))
            pygame.draw.circle(
                target,
                (*spark["color"], alpha),
                (int(spark["x"]), int(spark["y"])),
                size,
            )

    def _draw_fireflies(self, target: pygame.Surface) -> None:
        for fly in self.fireflies:
            blink = abs(math.sin(fly["phase"] * 2.4))
            if blink < 0.15:
                continue
            alpha = int(90 + 130 * blink * self.intensity)
            size = max(1, int(1.4 + 1.8 * blink))
            pygame.draw.circle(
                target,
                (*fly["color"], alpha),
                (int(fly["x"]), int(fly["y"])),
                size,
            )

    def _draw_bursts(self, target: pygame.Surface) -> None:
        for burst in self.bursts:
            life_t = max(0.0, burst["life"] / burst["max_life"])
            alpha = int(220 * life_t)
            size = max(1, int(burst["size"] * life_t))
            pygame.draw.circle(
                target,
                (*burst["color"], alpha),
                (int(burst["x"]), int(burst["y"])),
                size,
            )

    def _blit_vignette(self, w: int, h: int, strength: float = 1.0) -> None:
        if self._vignette is None or self._vignette_size != (w, h):
            vignette = pygame.Surface((w, h), pygame.SRCALPHA)
            edge = int(140 * strength * self.intensity)
            band = max(40, min(w, h) // 5)
            step = 4
            for i in range(0, band, step):
                t = 1.0 - (i / band)
                a = int(edge * (t * t))
                pygame.draw.rect(vignette, (0, 0, 0, a), (0, i, w, step))
                pygame.draw.rect(vignette, (0, 0, 0, a), (0, h - i - step, w, step))
                pygame.draw.rect(vignette, (0, 0, 0, a), (i, 0, step, h))
                pygame.draw.rect(vignette, (0, 0, 0, a), (w - i - step, 0, step, h))
            self._vignette = vignette
            self._vignette_size = (w, h)
        # Strength variants: rebuild if needed is rare; for pause we accept same cache
        self.screen.blit(self._vignette, (0, 0))

    @staticmethod
    def _lerp_color(a: ColorA, b: ColorA, t: float) -> ColorA:
        t = max(0.0, min(1.0, t))
        return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(4))  # type: ignore[return-value]


def draw_title_glow(
    screen: pygame.Surface,
    font: pygame.font.Font,
    text: str,
    center: Tuple[int, int],
    timer: float,
    *,
    base_color: Color = (255, 236, 190),
    glow_color: Color = (255, 170, 80),
) -> pygame.Rect:
    """Render a title with soft pulsing glow and gentle vertical bob."""
    bob = int(3 * math.sin(timer * 1.6))
    pulse = 0.55 + 0.45 * abs(math.sin(timer * 2.0))
    glow_alpha = int(70 + 50 * pulse)

    main = font.render(text, True, base_color)
    rect = main.get_rect(center=(center[0], center[1] + bob))

    for radius, alpha_mul in ((8, 0.35), (4, 0.55), (2, 0.8)):
        glow = font.render(text, True, glow_color)
        glow.set_alpha(int(glow_alpha * alpha_mul))
        for dx, dy in ((-radius, 0), (radius, 0), (0, -radius), (0, radius)):
            screen.blit(glow, (rect.x + dx, rect.y + dy))

    screen.blit(main, rect)
    return rect


def draw_menu_option(
    screen: pygame.Surface,
    font: pygame.font.Font,
    text: str,
    center_x: int,
    y: int,
    selected: bool,
    timer: float,
    *,
    index: int = 0,
) -> None:
    """Draw a menu row with animated selection treatment."""
    if selected:
        pulse = 0.5 + 0.5 * math.sin(timer * 4.0 + index)
        bar_w = max(220, font.size(text)[0] + 70) + int(18 * pulse)
        bar_h = 34
        bar = pygame.Surface((bar_w, bar_h), pygame.SRCALPHA)
        pygame.draw.rect(
            bar,
            (255, 200, 110, int(28 + 22 * pulse)),
            bar.get_rect(),
            border_radius=6,
        )
        pygame.draw.rect(
            bar,
            (255, 230, 160, int(90 + 50 * pulse)),
            bar.get_rect(),
            width=1,
            border_radius=6,
        )
        screen.blit(bar, (center_x - bar_w // 2, y - 4))

        # Sliding caret
        caret_x = center_x - bar_w // 2 + 14 + int(3 * math.sin(timer * 5))
        caret_color = (255, 230, 160)
        points = [
            (caret_x, y + 8),
            (caret_x + 10, y + 14),
            (caret_x, y + 20),
        ]
        pygame.draw.polygon(screen, caret_color, points)

        color = (255, 245, 210)
        # Soft underline sweep
        underline_w = int((90 + 40 * pulse))
        underline = pygame.Surface((underline_w, 2), pygame.SRCALPHA)
        underline.fill((255, 210, 120, int(140 + 80 * pulse)))
        text_surf = font.render(text, True, color)
        text_x = center_x - text_surf.get_width() // 2
        screen.blit(text_surf, (text_x, y))
        screen.blit(
            underline,
            (center_x - underline_w // 2, y + text_surf.get_height() + 4),
        )
    else:
        dim = 0.85 + 0.05 * math.sin(timer * 0.8 + index)
        shade = int(165 * dim)
        color = (shade, shade, shade + 8)
        text_surf = font.render(text, True, color)
        text_x = center_x - text_surf.get_width() // 2
        screen.blit(text_surf, (text_x, y))


def draw_corner_torches(
    screen: pygame.Surface,
    timer: float,
    *,
    positions: Optional[List[Tuple[int, int]]] = None,
) -> None:
    """Flickering torch ornaments for menu corners."""
    w, h = screen.get_size()
    if positions is None:
        positions = [(48, h - 70), (w - 48, h - 70)]
    flicker = 0.55 + 0.45 * abs(math.sin(timer * 7.5))
    for i, (cx, cy) in enumerate(positions):
        local = 0.55 + 0.45 * abs(math.sin(timer * 7.5 + i * 1.7))
        glow = pygame.Surface((70, 90), pygame.SRCALPHA)
        pygame.draw.circle(
            glow,
            (255, 140, 50, int(55 * local)),
            (35, 40),
            int(22 + 6 * local),
        )
        pygame.draw.circle(
            glow,
            (255, 220, 120, int(120 * local * flicker)),
            (35, 36),
            int(8 + 3 * local),
        )
        pygame.draw.rect(glow, (90, 60, 35, 180), (32, 48, 6, 28))
        screen.blit(glow, (cx - 35, cy - 40))


def draw_pulsing_hint(
    screen: pygame.Surface,
    font: pygame.font.Font,
    text: str,
    center_x: int,
    y: int,
    timer: float,
) -> None:
    """Softly pulsing control hint line."""
    hint_pulse = 0.7 + 0.3 * abs(math.sin(timer * 1.8))
    shade = int(150 * hint_pulse)
    hint_surf = font.render(text, True, (shade, shade, shade))
    screen.blit(hint_surf, (center_x - hint_surf.get_width() // 2, y))
