"""
Random overworld events that spawn temporary POIs.

Events trigger occasionally while moving on the overworld. Spawned POIs
(e.g. bandit camp, stranded merchant) use long expiry so they don't
disappear too quickly.
"""

import random
from typing import Optional, Tuple, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from engine.core.game import Game

# How long event POIs stay on the map (in-game hours). Kept long so they don't disappear too fast.
EVENT_POI_EXPIRY_HOURS = 120.0  # 5 days

# Max number of event-spawned POIs at once (so the map doesn't get flooded).
MAX_EVENT_POIS_AT_ONCE = 3

# Don't try to trigger again for this many moves after a trigger (or last attempt).
COOLDOWN_MOVES = 30

# Chance to try an event each move when off cooldown (small so events feel occasional).
TRIGGER_CHANCE_PER_MOVE = 0.025  # 2.5%

# Min/max distance from player for spawn (tiles).
SPAWN_MIN_DISTANCE = 12
SPAWN_MAX_DISTANCE = 40


def _count_event_pois(overworld: Any) -> int:
    """Return how many POIs are event-spawned (is_temporary and source_event_id set)."""
    return sum(
        1 for p in overworld.get_all_pois()
        if getattr(p, "is_temporary", False) and getattr(p, "source_event_id", None)
    )


def _find_spawn_position(
    overworld: Any,
    player_x: int,
    player_y: int,
    min_dist: int = SPAWN_MIN_DISTANCE,
    max_dist: int = SPAWN_MAX_DISTANCE,
) -> Optional[Tuple[int, int]]:
    """Find a valid tile for spawning an event POI: walkable, no existing POI, in range."""
    for _ in range(60):
        dx = random.randint(-max_dist, max_dist)
        dy = random.randint(-max_dist, max_dist)
        d_sq = dx * dx + dy * dy
        if d_sq < min_dist * min_dist or d_sq > max_dist * max_dist:
            continue
        x = player_x + dx
        y = player_y + dy
        if not overworld.in_bounds(x, y) or not overworld.is_walkable(x, y):
            continue
        if overworld.get_poi_at(x, y) is not None:
            continue
        return (x, y)
    return None


def _spawn_event_camp(
    game: "Game",
    position: Tuple[int, int],
    event_id: str,
    name: str,
    is_hostile: bool,
    level: Optional[int] = None,
) -> Optional[Any]:
    """Spawn a temporary camp POI for a random event. Returns the POI or None."""
    from world.poi.registry import get_registry

    overworld = getattr(game, "overworld_map", None)
    if overworld is None:
        return None
    x, y = position
    poi_id = f"event_{event_id}_{x}_{y}"
    if poi_id in overworld.pois:
        return None

    current_hours = 0.0
    if getattr(game, "time_system", None) is not None:
        current_hours = game.time_system.get_total_hours()
    expires_at = current_hours + EVENT_POI_EXPIRY_HOURS

    if level is None:
        level = getattr(game.hero_stats, "level", 1) if hasattr(game, "hero_stats") else 1
    level = max(1, min(level, 20))

    registry = get_registry()
    try:
        camp = registry.create(
            "camp",
            poi_id,
            (x, y),
            level=level,
            name=name,
            is_temporary=True,
            source_event_id=event_id,
            expires_at_hours=expires_at,
        )
    except Exception:
        return None

    camp.discovered = True
    camp.is_hostile = is_hostile
    overworld.add_poi(camp)
    return camp


def try_trigger_random_event(game: "Game") -> bool:
    """
    Maybe trigger a random overworld event (spawn a temporary POI).
    Call once per overworld move. Uses cooldown and chance so events
    are occasional; event POIs use long expiry so they don't disappear too fast.

    Returns:
        True if an event was triggered (a POI was spawned), False otherwise.
    """
    overworld = getattr(game, "overworld_map", None)
    if overworld is None:
        return False
    if getattr(game, "time_system", None) is None:
        return False

    move_count = getattr(game, "_overworld_move_count", 0)
    last_trigger = getattr(game, "_random_event_last_trigger_move", -9999)
    if move_count - last_trigger < COOLDOWN_MOVES:
        return False
    if random.random() >= TRIGGER_CHANCE_PER_MOVE:
        return False
    if _count_event_pois(overworld) >= MAX_EVENT_POIS_AT_ONCE:
        return False

    px, py = overworld.get_player_position()
    pos = _find_spawn_position(overworld, px, py)
    if pos is None:
        return False

    # Pick event type (with variety in names and messages)
    event_choice = random.choice(["hostile_camp", "merchant", "ruins"])
    if event_choice == "hostile_camp":
        names = ("Bandit Camp", "Marauder Camp", "Raider Outpost")
        messages = (
            "You hear reports of a bandit camp in the area.",
            "Scouts speak of marauders encamped nearby.",
            "Word spreads of a raider outpost in these parts.",
        )
        idx = random.randint(0, len(names) - 1)
        poi = _spawn_event_camp(
            game,
            pos,
            event_id="hostile_camp",
            name=names[idx],
            is_hostile=True,
        )
        if poi:
            game.add_message(messages[idx])
    elif event_choice == "merchant":
        names = ("Stranded Merchant", "Lost Caravan", "Traveling Peddler")
        messages = (
            "Rumors speak of a stranded merchant in need of aid nearby.",
            "A lost caravan is said to have set up camp in the area.",
            "You hear of a traveling peddler offering wares on the road.",
        )
        idx = random.randint(0, len(names) - 1)
        poi = _spawn_event_camp(
            game,
            pos,
            event_id="stranded_merchant",
            name=names[idx],
            is_hostile=False,
        )
        if poi:
            game.add_message(messages[idx])
    else:
        names = ("Abandoned Ruins", "Forgotten Shrine", "Old Watchtower")
        messages = (
            "You hear of ancient ruins discovered in the wilderness.",
            "Legends tell of a forgotten shrine in these lands.",
            "An old watchtower has been sighted, long since abandoned.",
        )
        idx = random.randint(0, len(names) - 1)
        poi = _spawn_event_camp(
            game,
            pos,
            event_id="ruins",
            name=names[idx],
            is_hostile=False,
        )
        if poi:
            game.add_message(messages[idx])

    if poi is not None:
        game._random_event_last_trigger_move = move_count
        return True
    return False
