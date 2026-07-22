"""Process raw entity sprites into 64x64 game-ready PNGs.

Uses the framing approach that worked for companion_mercenary:
- remove void black backdrop
- trim sparse bottom junk
- square + pad like player_warrior
- downscale to 64
- keep characters mostly opaque (no heavy alpha fade)
"""

from __future__ import annotations

import shutil
from collections import deque
from pathlib import Path

import pygame

ENTITY_DIR = Path(__file__).resolve().parents[1] / "sprites" / "entity"
TARGET = 64

# New / oversized raw art to process (skip already-finished 64x64 heroes etc.)
TARGETS = (
    "merchant",
    "enemy_goblin_skirmisher",
    "enemy_goblin_brute",
    "enemy_goblin_shaman",
    "enemy_bandit_cutthroat",
    "enemy_cultist_adept",
    "enemy_skeleton_archer",
    "enemy_dire_rat",
)


def is_backdrop(c: pygame.Color) -> bool:
    # Strict void only — do not eat dark boots/cloaks (r/g/b around 8-20).
    return c.a < 8 or (c.r <= 5 and c.g <= 5 and c.b <= 5)


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


def trim_sparse_tail(surf: pygame.Surface, row_threshold: int = 80, gap_rows: int = 20) -> pygame.Surface:
    w, h = surf.get_size()
    row_counts = [0] * h
    for y in range(h):
        for x in range(w):
            if surf.get_at((x, y)).a > 20:
                row_counts[y] += 1

    top = next((y for y, c in enumerate(row_counts) if c >= row_threshold), None)
    if top is None:
        return surf

    peak = max(row_counts)
    low = max(row_threshold, int(peak * 0.08))
    bottom = top
    gap = 0
    started = False
    for y in range(top, h):
        if row_counts[y] >= low:
            bottom = y
            gap = 0
            started = True
        elif started:
            gap += 1
            if gap >= gap_rows:
                break

    out = surf.copy()
    for y in range(h):
        if y < top or y > bottom:
            for x in range(w):
                out.set_at((x, y), (0, 0, 0, 0))
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


def to_square(surf: pygame.Surface, pad_ratio: float = 0.10) -> pygame.Surface:
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
    # Clear only near-invisible fringe; keep body solid like warrior (no ghosting).
    for y in range(TARGET):
        for x in range(TARGET):
            c = final.get_at((x, y))
            if c.a < 28:
                final.set_at((x, y), (0, 0, 0, 0))
            elif c.a >= 50:
                # Body pixels: push toward fully opaque (match warrior readability).
                final.set_at((x, y), (c.r, c.g, c.b, 255))
            else:
                # Soft edge only — keep a light fringe, not washed-out body.
                final.set_at((x, y), (c.r, c.g, c.b, min(255, c.a + 40)))
    return final


def process_one(sprite_id: str) -> None:
    out_path = ENTITY_DIR / f"{sprite_id}.png"
    orig_path = ENTITY_DIR / f"{sprite_id}.png.orig.png"

    if not out_path.exists() and not orig_path.exists():
        print(f"SKIP missing: {sprite_id}")
        return

    if not orig_path.exists():
        shutil.copy2(out_path, orig_path)
        print(f"backed up {sprite_id}")

    src = pygame.image.load(str(orig_path)).convert_alpha()
    # Already processed?
    if src.get_width() == TARGET and src.get_height() == TARGET:
        # Re-process from orig if orig is larger; otherwise leave.
        pass

    work = src.copy()
    flood_from_edges(work, is_backdrop)
    work = trim_sparse_tail(work)
    box = content_rect(work)
    work = to_square(work)
    final = downscale(work)

    pygame.image.save(final, str(out_path))
    opaque = sum(1 for y in range(TARGET) for x in range(TARGET) if final.get_at((x, y)).a > 24)
    alphas = [
        final.get_at((x, y)).a
        for y in range(TARGET)
        for x in range(TARGET)
        if final.get_at((x, y)).a > 24
    ]
    avg = sum(alphas) / len(alphas) if alphas else 0
    print(
        f"{sprite_id}: content={box.w}x{box.h} -> {TARGET}x{TARGET} "
        f"opaque={opaque} avg_a={avg:.0f} max_a={max(alphas) if alphas else 0}"
    )


def main() -> None:
    pygame.init()
    pygame.display.set_mode((1, 1))
    for sprite_id in TARGETS:
        process_one(sprite_id)


if __name__ == "__main__":
    main()
