"""
Enemy battle formation layouts and safe spawn placement.

Picks a weighted formation, then places each enemy on a free cell on the
enemy half of the grid — never on obstacles, hazards, or occupied tiles.
Falls back toward the classic front line if preferred cells are blocked.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, List, Optional, Sequence, Set, Tuple

from settings import BATTLE_ENEMY_START_COL_OFFSET

if TYPE_CHECKING:
    from world.entities import Enemy

GridPos = Tuple[int, int]
Occupied = Set[GridPos]

# line: how deep on the enemy side
#   0 = advanced (toward player / center)
#   1 = forward
#   2 = classic front line (current default column)
#   3 = rear
#   4 = deep back (near right edge)
# lane: vertical offset from grid center (negative = up)
Slot = Tuple[int, int]


@dataclass(frozen=True)
class FormationDef:
    id: str
    weight: float
    # Preferred slots in assignment order (front-biased roles take earlier slots).
    slots: Sequence[Slot]


FORMATIONS: Sequence[FormationDef] = (
    FormationDef(
        id="front_line",
        weight=0.35,
        slots=((2, -1), (2, 0), (2, 1), (2, -2), (2, 2), (2, -3)),
    ),
    FormationDef(
        id="staggered",
        weight=0.30,
        slots=((2, 0), (3, -1), (3, 1), (1, -2), (4, 0), (2, 2)),
    ),
    FormationDef(
        id="spread",
        weight=0.20,
        slots=((0, -2), (4, 2), (2, 0), (1, 2), (3, -2), (0, 1)),
    ),
    FormationDef(
        id="clustered_deep",
        weight=0.15,
        slots=((4, 0), (4, -1), (4, 1), (3, 0), (4, -2), (4, 2)),
    ),
)

# Roles that prefer the front of a formation (closer to the player).
_FORWARD_ROLES = frozenset({"Brute", "Elite Brute", "Skirmisher"})
# Roles that prefer the back (casters / support).
_BACK_ROLES = frozenset({"Invoker", "Support", "Elite Support", "Elite Invoker"})


def enemy_spawn_min_col(grid_width: int) -> int:
    """Leftmost column enemies may occupy (right portion of the grid)."""
    front_col = grid_width - BATTLE_ENEMY_START_COL_OFFSET
    return max(grid_width // 2 + 1, front_col - 4)


def _pick_formation() -> FormationDef:
    weights = [f.weight for f in FORMATIONS]
    return random.choices(list(FORMATIONS), weights=weights, k=1)[0]


def _line_to_gx(line: int, grid_width: int) -> int:
    """Map formation line index to a column on the enemy side."""
    front = grid_width - BATTLE_ENEMY_START_COL_OFFSET
    min_col = enemy_spawn_min_col(grid_width)
    back = grid_width - 1

    if line <= 0:
        gx = front - 4
    elif line == 1:
        gx = front - 2
    elif line == 2:
        gx = front
    elif line == 3:
        gx = front + 1
    else:
        gx = back

    return max(min_col, min(back, gx))


def _slot_to_pos(
    line: int,
    lane: int,
    grid_width: int,
    grid_height: int,
) -> GridPos:
    gx = _line_to_gx(line, grid_width)
    gy = grid_height // 2 + lane
    gy = max(0, min(grid_height - 1, gy))
    return gx, gy


def _role_front_bias(enemy: "Enemy") -> int:
    """
    Sort key for slot assignment. Lower = earlier slots (usually more forward).
    """
    arch_id = getattr(enemy, "archetype_id", None)
    role = ""
    ai_profile = ""
    if arch_id is not None:
        try:
            from systems.enemies import get_archetype

            arch = get_archetype(arch_id)
            role = arch.role or ""
            ai_profile = arch.ai_profile or ""
        except (KeyError, ImportError):
            pass

    if role in _FORWARD_ROLES or ai_profile in ("brute", "skirmisher"):
        return 0
    if role in _BACK_ROLES or ai_profile == "caster":
        return 2
    return 1


def _is_valid_spawn(
    gx: int,
    gy: int,
    *,
    grid_width: int,
    grid_height: int,
    min_col: int,
    occupied: Occupied,
    get_terrain: Callable[[int, int], object],
) -> bool:
    if gx < min_col or gy < 0 or gx >= grid_width or gy >= grid_height:
        return False
    if (gx, gy) in occupied:
        return False

    terrain = get_terrain(gx, gy)
    if getattr(terrain, "blocks_movement", False):
        return False
    # Don't start the fight standing in fire / acid / etc.
    if getattr(terrain, "terrain_type", "none") == "hazard":
        return False
    return True


def _nearest_free_cell(
    preferred: GridPos,
    *,
    grid_width: int,
    grid_height: int,
    min_col: int,
    occupied: Occupied,
    get_terrain: Callable[[int, int], object],
) -> Optional[GridPos]:
    """Find the closest valid spawn cell to `preferred` within the enemy zone."""
    if _is_valid_spawn(
        preferred[0],
        preferred[1],
        grid_width=grid_width,
        grid_height=grid_height,
        min_col=min_col,
        occupied=occupied,
        get_terrain=get_terrain,
    ):
        return preferred

    candidates: List[Tuple[int, GridPos]] = []
    for gx in range(min_col, grid_width):
        for gy in range(grid_height):
            if not _is_valid_spawn(
                gx,
                gy,
                grid_width=grid_width,
                grid_height=grid_height,
                min_col=min_col,
                occupied=occupied,
                get_terrain=get_terrain,
            ):
                continue
            dist = abs(gx - preferred[0]) + abs(gy - preferred[1])
            candidates.append((dist, (gx, gy)))

    if not candidates:
        return None

    candidates.sort(key=lambda item: (item[0], item[1][0], item[1][1]))
    return candidates[0][1]


def _classic_front_fallback(
    index: int,
    count: int,
    *,
    grid_width: int,
    grid_height: int,
    min_col: int,
    occupied: Occupied,
    get_terrain: Callable[[int, int], object],
) -> Optional[GridPos]:
    """Last-resort placement mirroring the old single-column front line."""
    start_col = grid_width - BATTLE_ENEMY_START_COL_OFFSET
    start_row = max(0, grid_height // 2 - (count // 2))
    preferred = (start_col, start_row + index)
    return _nearest_free_cell(
        preferred,
        grid_width=grid_width,
        grid_height=grid_height,
        min_col=min_col,
        occupied=occupied,
        get_terrain=get_terrain,
    )


def place_enemy_formation(
    enemies: Sequence["Enemy"],
    *,
    grid_width: int,
    grid_height: int,
    get_terrain: Callable[[int, int], object],
    occupied: Optional[Occupied] = None,
    formation: Optional[FormationDef] = None,
) -> Tuple[str, List[GridPos]]:
    """
    Choose a formation and return one (gx, gy) per enemy.

    Args:
        enemies: Enemies to place (already truncated to max battle size).
        grid_width / grid_height: Battle grid size.
        get_terrain: Callback (gx, gy) -> BattleTerrain-like object.
        occupied: Cells already taken (e.g. player units). Mutated as we place.
        formation: Optional forced formation (for tests / debug).

    Returns:
        (formation_id, positions) aligned with `enemies` order.
    """
    if not enemies:
        return "empty", []

    chosen = formation or _pick_formation()
    min_col = enemy_spawn_min_col(grid_width)
    taken: Occupied = set(occupied) if occupied is not None else set()

    # Assign front-biased roles to earlier (usually forward) slots, but return
    # positions in the original enemy list order.
    order = sorted(range(len(enemies)), key=lambda i: (_role_front_bias(enemies[i]), i))
    positions: List[Optional[GridPos]] = [None] * len(enemies)

    for slot_index, enemy_index in enumerate(order):
        if slot_index < len(chosen.slots):
            line, lane = chosen.slots[slot_index]
        else:
            line, lane = chosen.slots[-1] if chosen.slots else (2, 0)
            lane += slot_index - len(chosen.slots) + 1

        preferred = _slot_to_pos(line, lane, grid_width, grid_height)
        pos = _nearest_free_cell(
            preferred,
            grid_width=grid_width,
            grid_height=grid_height,
            min_col=min_col,
            occupied=taken,
            get_terrain=get_terrain,
        )
        if pos is None:
            pos = _classic_front_fallback(
                slot_index,
                len(enemies),
                grid_width=grid_width,
                grid_height=grid_height,
                min_col=min_col,
                occupied=taken,
                get_terrain=get_terrain,
            )

        if pos is None:
            # Absolute last resort: scan whole enemy zone left-to-right.
            for gx in range(min_col, grid_width):
                for gy in range(grid_height):
                    if _is_valid_spawn(
                        gx,
                        gy,
                        grid_width=grid_width,
                        grid_height=grid_height,
                        min_col=min_col,
                        occupied=taken,
                        get_terrain=get_terrain,
                    ):
                        pos = (gx, gy)
                        break
                if pos is not None:
                    break

        if pos is None:
            # Should be nearly impossible (reserved front columns have no
            # obstacles). Keep a deterministic on-grid coordinate anyway.
            pos = (
                max(min_col, grid_width - BATTLE_ENEMY_START_COL_OFFSET),
                min(grid_height - 1, max(0, grid_height // 2 + slot_index)),
            )

        positions[enemy_index] = pos
        taken.add(pos)

    result: List[GridPos] = []
    for pos in positions:
        assert pos is not None
        result.append(pos)
    return chosen.id, result
