"""Clean player class sprites from .orig backups into usable game PNGs."""

from __future__ import annotations

from collections import deque
from pathlib import Path

import pygame

ENTITY_DIR = Path(__file__).resolve().parents[1] / "sprites" / "entity"
# 64 is an integer multiple of TILE_SIZE (32) and stays readable when scaled to 24px player.
TARGET = 64
CLASSES = ("warrior", "rogue", "mage")


def load_source(class_id: str) -> tuple[pygame.Surface, Path]:
    out_path = ENTITY_DIR / f"player_{class_id}.png"
    orig = ENTITY_DIR / f"player_{class_id}.png.orig.png"
    if orig.exists():
        return pygame.image.load(str(orig)).convert_alpha(), out_path
    return pygame.image.load(str(out_path)).convert_alpha(), out_path


def is_backdrop(c: pygame.Color) -> bool:
    """Near-black empty backdrop only (not character shadow greys)."""
    return c.a < 8 or (c.r <= 12 and c.g <= 12 and c.b <= 12)


def is_red_artifact(c: pygame.Color) -> bool:
    r, g, b = c.r, c.g, c.b
    if r >= 60 and g <= 55 and b <= 55 and r >= g + 25 and r >= b + 25:
        return True
    if 25 <= r <= 100 and g <= 22 and b <= 22:
        return True
    return False


def flood_from_edges(surf: pygame.Surface, match) -> None:
    w, h = surf.get_size()
    q: deque[tuple[int, int]] = deque()
    seen = [[False] * w for _ in range(h)]

    def push(x: int, y: int) -> None:
        if 0 <= x < w and 0 <= y < h and not seen[y][x] and match(surf.get_at((x, y))):
            seen[y][x] = True
            q.append((x, y))

    for x in range(w):
        push(x, 0)
        push(x, h - 1)
    for y in range(h):
        push(0, y)
        push(w - 1, y)

    while q:
        x, y = q.popleft()
        surf.set_at((x, y), (0, 0, 0, 0))
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h and not seen[ny][nx] and match(surf.get_at((nx, ny))):
                seen[ny][nx] = True
                q.append((nx, ny))


def strip_red_artifacts(surf: pygame.Surface) -> None:
    w, h = surf.get_size()
    for y in range(h):
        for x in range(w):
            c = surf.get_at((x, y))
            if c.a > 0 and is_red_artifact(c):
                surf.set_at((x, y), (0, 0, 0, 0))


def largest_component(surf: pygame.Surface) -> pygame.Surface:
    w, h = surf.get_size()
    visited = [[False] * w for _ in range(h)]
    best: list[tuple[int, int]] = []

    def opaque(x: int, y: int) -> bool:
        return surf.get_at((x, y)).a > 20

    for y in range(h):
        for x in range(w):
            if visited[y][x] or not opaque(x, y):
                continue
            q = deque([(x, y)])
            visited[y][x] = True
            cluster: list[tuple[int, int]] = []
            while q:
                cx, cy = q.popleft()
                cluster.append((cx, cy))
                for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if 0 <= nx < w and 0 <= ny < h and not visited[ny][nx] and opaque(nx, ny):
                        visited[ny][nx] = True
                        q.append((nx, ny))
            if len(cluster) > len(best):
                best = cluster

    out = pygame.Surface((w, h), pygame.SRCALPHA)
    out.fill((0, 0, 0, 0))
    for x, y in best:
        out.set_at((x, y), surf.get_at((x, y)))
    return out


def content_rect(surf: pygame.Surface) -> pygame.Rect:
    w, h = surf.get_size()
    minx, miny, maxx, maxy = w, h, -1, -1
    for y in range(h):
        for x in range(w):
            if surf.get_at((x, y)).a > 20:
                minx = min(minx, x)
                miny = min(miny, y)
                maxx = max(maxx, x)
                maxy = max(maxy, y)
    if maxx < 0:
        return pygame.Rect(0, 0, w, h)
    return pygame.Rect(minx, miny, maxx - minx + 1, maxy - miny + 1)


def to_square(surf: pygame.Surface, pad_ratio: float = 0.08) -> pygame.Surface:
    box = content_rect(surf)
    cropped = surf.subsurface(box).copy()
    cw, ch = cropped.get_size()
    side = max(cw, ch)
    pad = max(2, int(side * pad_ratio))
    side += pad * 2
    out = pygame.Surface((side, side), pygame.SRCALPHA)
    out.fill((0, 0, 0, 0))
    out.blit(cropped, ((side - cw) // 2, (side - ch) // 2))
    return out


def downscale(surf: pygame.Surface) -> pygame.Surface:
    mid = max(TARGET * 2, 128)
    step = pygame.transform.smoothscale(surf, (mid, mid))
    final = pygame.transform.smoothscale(step, (TARGET, TARGET))
    # Only clear nearly-invisible fringe, keep dark hood/armor pixels.
    for y in range(TARGET):
        for x in range(TARGET):
            c = final.get_at((x, y))
            if c.a < 28:
                final.set_at((x, y), (0, 0, 0, 0))
    return final


def process_one(class_id: str) -> None:
    src, out_path = load_source(class_id)
    work = src.copy()
    flood_from_edges(work, is_backdrop)
    if class_id in ("mage", "rogue"):
        strip_red_artifacts(work)
        # Mage red floor may not touch edges as pure black; flood red+black from bottom.
        flood_from_edges(work, lambda c: is_backdrop(c) or is_red_artifact(c))
    work = largest_component(work)
    work = to_square(work)
    final = downscale(work)
    pygame.image.save(final, str(out_path))
    opaque = sum(1 for y in range(TARGET) for x in range(TARGET) if final.get_at((x, y)).a > 24)
    print(f"{out_path.name}: {TARGET}x{TARGET}, opaque={opaque}/{TARGET * TARGET}")


def main() -> None:
    pygame.init()
    pygame.display.set_mode((1, 1))
    for class_id in CLASSES:
        process_one(class_id)


if __name__ == "__main__":
    main()
