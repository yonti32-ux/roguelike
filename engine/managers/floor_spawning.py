from __future__ import annotations

from typing import TYPE_CHECKING, Optional, List
import random
import math

from settings import TILE_SIZE
from world.game_map import GameMap
from world.entities import Enemy, Merchant, Trap
from systems.enemies import (
    choose_archetype_for_floor,
    compute_scaled_stats,
    choose_pack_for_floor,
    get_archetype,
    is_elite_spawn,
    make_enemy_elite,
    UNIQUE_ROOM_ENEMIES,
)
from systems.events import EVENTS
from systems.traps import TRAPS

if TYPE_CHECKING:
    from ..core.game import Game


def _choose_enemy_type_for_floor(floor_index: int) -> str:
    """
    Very simple enemy naming based on floor depth.
    Used only for the battle UI group label.
    """
    if floor_index <= 2:
        pool = ["Goblin", "Bandit", "Cultist"]
    elif floor_index <= 4:
        pool = ["Ghoul", "Orc Raider", "Dark Acolyte"]
    else:
        pool = ["Dread Knight", "Voidspawn", "Elite Cultist"]

    return random.choice(pool)


def spawn_enemies_for_floor(game: "Game", game_map: GameMap, floor_index: int) -> None:
    """
    Spawn enemies on this floor, using room-aware logic, enemy archetypes,
    and *packs* (themed groups that spawn together).

    Room-aware logic:
    - Never spawn in the 'start' room.
    - Prefer lair rooms for extra density / heavier packs.
    - Fill remaining quota from other rooms and corridors.
    - Keep a safe radius around the main spawn.
    """
    enemy_width = 24
    enemy_height = 24

    up = game_map.up_stairs
    down = game_map.down_stairs

    # Safe radius (in tiles) around the main spawn (usually up stairs)
    safe_radius_tiles = 3
    if up is not None:
        safe_cx, safe_cy = up
    else:
        safe_cx = game_map.width // 2
        safe_cy = game_map.height // 2

    lair_tiles: List[tuple[int, int]] = []
    room_tiles: List[tuple[int, int]] = []
    corridor_tiles: List[tuple[int, int]] = []

    for ty in range(game_map.height):
        for tx in range(game_map.width):
            if not game_map.is_walkable_tile(tx, ty):
                continue
            if up is not None and (tx, ty) == up:
                continue
            if down is not None and (tx, ty) == down:
                continue

            # Keep a small safe bubble around spawn
            dx = tx - safe_cx
            dy = ty - safe_cy
            if dx * dx + dy * dy <= safe_radius_tiles * safe_radius_tiles:
                continue

            room = game_map.get_room_at(tx, ty) if hasattr(game_map, "get_room_at") else None
            if room is None:
                # Corridors / junctions
                corridor_tiles.append((tx, ty))
            else:
                tag = getattr(room, "tag", "generic")
                if tag == "start":
                    # Extra safety: don't spawn in the start room at all
                    continue
                elif tag == "sanctum":
                    # Sanctum rooms are intentionally enemy-free; used for boons/events.
                    continue
                elif tag == "lair":
                    lair_tiles.append((tx, ty))
                else:
                    room_tiles.append((tx, ty))

    if not (lair_tiles or room_tiles or corridor_tiles):
        return

    random.shuffle(lair_tiles)
    random.shuffle(room_tiles)
    random.shuffle(corridor_tiles)

    # --- Decide roughly how many enemies we want on this floor ---------
    base_desired = 2 + floor_index

    screen_w, screen_h = game.screen.get_size()
    base_tiles_x = screen_w // TILE_SIZE
    base_tiles_y = screen_h // TILE_SIZE
    base_area = max(1, base_tiles_x * base_tiles_y)

    floor_area = game_map.width * game_map.height
    area_ratio = floor_area / base_area
    area_factor = math.sqrt(area_ratio) if area_ratio > 0 else 1.0
    # Keep in a reasonable band so things don't get absurd
    area_factor = max(0.75, min(area_factor, 1.8))

    target_enemies = int(round(base_desired * area_factor))
    # Soft clamp overall difficulty
    target_enemies = min(10, max(2, target_enemies))

    # We'll spawn enemies in *packs*. Each pack is usually 2–3 enemies.
    approx_pack_size = 2.2
    desired_packs = max(1, int(round(target_enemies / approx_pack_size)))

    all_candidate_tiles = lair_tiles + room_tiles + corridor_tiles
    if not all_candidate_tiles:
        return

    desired_packs = min(desired_packs, len(all_candidate_tiles))

    chosen_anchors: List[tuple[int, int]] = []
    remaining_packs = desired_packs

    # Fill roughly half of the pack anchors from lair rooms (if any)
    if lair_tiles and remaining_packs > 0:
        lair_target = min(len(lair_tiles), max(1, remaining_packs // 2))
        chosen_anchors.extend(lair_tiles[:lair_target])
        remaining_packs -= lair_target

    # Then normal rooms
    if room_tiles and remaining_packs > 0:
        room_target = min(len(room_tiles), remaining_packs)
        chosen_anchors.extend(room_tiles[:room_target])
        remaining_packs -= room_target

    # Whatever anchors remain come from corridors
    if corridor_tiles and remaining_packs > 0:
        corr_target = min(len(corridor_tiles), remaining_packs)
        chosen_anchors.extend(corridor_tiles[:corr_target])
        remaining_packs -= corr_target

    if not chosen_anchors:
        return

    # Track which tiles already have an enemy so packs don't overlap
    occupied_enemy_tiles: set[tuple[int, int]] = set()
    spawned_total = 0
    # Hard cap so big floors don't turn into bullet hell
    max_total_enemies = min(target_enemies + 3, 12)

    # Track unique enemies so each archetype appears at most once per floor
    spawned_unique_ids: set[str] = set()
    max_unique_per_floor = 2

    def can_use_tile(tx: int, ty: int) -> bool:
        if (tx, ty) in occupied_enemy_tiles:
            return False
        if up is not None and (tx, ty) == up:
            return False
        if down is not None and (tx, ty) == down:
            return False
        if not game_map.is_walkable_tile(tx, ty):
            return False
        dx_ = tx - safe_cx
        dy_ = ty - safe_cy
        if dx_ * dx_ + dy_ * dy_ <= safe_radius_tiles * safe_radius_tiles:
            return False
        return True

    for anchor_tx, anchor_ty in chosen_anchors:
        if spawned_total >= max_total_enemies:
            break

        room = game_map.get_room_at(anchor_tx, anchor_ty) if hasattr(game_map, "get_room_at") else None
        room_tag = getattr(room, "tag", "generic") if room is not None else None

        # Candidate spawn tiles: anchor + its 8 neighbors (3×3 cluster)
        candidate_tiles: List[tuple[int, int]] = []
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                tx = anchor_tx + dx
                ty = anchor_ty + dy
                if 0 <= tx < game_map.width and 0 <= ty < game_map.height:
                    candidate_tiles.append((tx, ty))
        random.shuffle(candidate_tiles)

        # --- Chance to spawn a room-themed unique enemy instead of a pack ---
        spawned_unique_here = False
        if (
            room_tag is not None
            and room_tag in UNIQUE_ROOM_ENEMIES
            and len(spawned_unique_ids) < max_unique_per_floor
            and random.random() < 0.15  # 15% chance at eligible anchors
        ):
            # Filter uniques that haven't spawned yet
            available_uniques = [
                uid for uid in UNIQUE_ROOM_ENEMIES[room_tag] if uid not in spawned_unique_ids
            ]
            if available_uniques:
                unique_id = random.choice(available_uniques)

                # Find a nearby free tile
                spawn_tx: Optional[int] = None
                spawn_ty: Optional[int] = None
                for tx, ty in candidate_tiles:
                    if can_use_tile(tx, ty):
                        spawn_tx, spawn_ty = tx, ty
                        break

                if spawn_tx is not None and spawn_ty is not None:
                    try:
                        arch = get_archetype(unique_id)
                    except KeyError:
                        arch = choose_archetype_for_floor(floor_index, room_tag=room_tag)

                    max_hp, attack_power, defense, xp_reward, initiative = compute_scaled_stats(
                        arch, floor_index
                    )

                    ex, ey = game_map.center_entity_on_tile(
                        spawn_tx, spawn_ty, enemy_width, enemy_height
                    )
                    enemy = Enemy(
                        x=ex,
                        y=ey,
                        width=enemy_width,
                        height=enemy_height,
                        speed=70.0,
                    )

                    setattr(enemy, "max_hp", max_hp)
                    setattr(enemy, "hp", max_hp)
                    setattr(enemy, "attack_power", attack_power)
                    setattr(enemy, "defense", defense)
                    setattr(enemy, "xp_reward", xp_reward)
                    setattr(enemy, "initiative", initiative)
                    setattr(enemy, "enemy_type", arch.name)
                    setattr(enemy, "archetype_id", arch.id)
                    setattr(enemy, "ai_profile", arch.ai_profile)
                    setattr(enemy, "is_unique", True)

                    # Uniques are always elite to feel special
                    make_enemy_elite(enemy, floor_index)

                    game_map.entities.append(enemy)
                    occupied_enemy_tiles.add((spawn_tx, spawn_ty))
                    spawned_total += 1
                    spawned_unique_ids.add(unique_id)
                    spawned_unique_here = True

        if spawned_unique_here or spawned_total >= max_total_enemies:
            continue

        # --- Otherwise, spawn a normal pack at this anchor ------------------
        try:
            pack = choose_pack_for_floor(floor_index, room_tag=room_tag)
            member_arch_ids = list(pack.member_arch_ids)
        except Exception:
            # Very defensive fallback: just pick a single archetype
            arch = choose_archetype_for_floor(floor_index, room_tag=room_tag)
            member_arch_ids = [arch.id]

        for arch_id in member_arch_ids:
            if spawned_total >= max_total_enemies:
                break

            # Find a nearby free tile for this pack member
            spawn_tx: Optional[int] = None
            spawn_ty: Optional[int] = None
            for tx, ty in candidate_tiles:
                if can_use_tile(tx, ty):
                    spawn_tx, spawn_ty = tx, ty
                    break

            if spawn_tx is None or spawn_ty is None:
                # No more room around this anchor
                continue

            # Look up archetype; if missing, fall back to generic floor-based choice
            try:
                arch = get_archetype(arch_id)
            except KeyError:
                arch = choose_archetype_for_floor(floor_index, room_tag=room_tag)

            max_hp, attack_power, defense, xp_reward, initiative = compute_scaled_stats(arch, floor_index)

            ex, ey = game_map.center_entity_on_tile(spawn_tx, spawn_ty, enemy_width, enemy_height)
            enemy = Enemy(
                x=ex,
                y=ey,
                width=enemy_width,
                height=enemy_height,
                # Slightly slower chase speed for nicer exploration feel
                speed=70.0,
            )

            # Basic combat stats that BattleScene will use
            setattr(enemy, "max_hp", max_hp)
            setattr(enemy, "hp", max_hp)
            setattr(enemy, "attack_power", attack_power)
            setattr(enemy, "defense", defense)

            # XP reward and metadata
            setattr(enemy, "xp_reward", xp_reward)
            setattr(enemy, "initiative", initiative)
            setattr(enemy, "enemy_type", arch.name)
            setattr(enemy, "archetype_id", arch.id)
            setattr(enemy, "ai_profile", arch.ai_profile)

            # Enemies block movement in exploration
            setattr(enemy, "blocks_movement", True)
            
            # Elite system: randomly make this enemy elite
            if is_elite_spawn(floor_index):
                make_enemy_elite(enemy, floor_index)

            game_map.entities.append(enemy)
            occupied_enemy_tiles.add((spawn_tx, spawn_ty))
            spawned_total += 1


def spawn_events_for_floor(game_map: GameMap, floor_index: int) -> None:
    """
    Spawn a few interactive event nodes (shrines, lore stones, caches).

    Room-aware logic:
    - Prefer tiles inside rooms tagged 'event'.
    - Otherwise, use generic rooms.
    - Avoid stairs, existing entities, and the spawn-safe radius.
    """
    from world.entities import EventNode  # local to avoid circulars

    if not getattr(game_map, "rooms", None):
        return

    up = game_map.up_stairs
    down = game_map.down_stairs

    # Safe radius around main spawn (usually up stairs)
    safe_radius_tiles = 3
    if up is not None:
        safe_cx, safe_cy = up
    else:
        safe_cx = game_map.width // 2
        safe_cy = game_map.height // 2

    # Tiles already occupied by entities
    occupied_tiles: set[tuple[int, int]] = set()
    for entity in getattr(game_map, "entities", []):
        if not hasattr(entity, "rect"):
            continue
        cx, cy = entity.rect.center
        tx, ty = game_map.world_to_tile(cx, cy)
        occupied_tiles.add((tx, ty))

    event_room_tiles: list[tuple[int, int]] = []
    other_room_tiles: list[tuple[int, int]] = []

    for ty in range(game_map.height):
        for tx in range(game_map.width):
            if not game_map.is_walkable_tile(tx, ty):
                continue
            if up is not None and (tx, ty) == up:
                continue
            if down is not None and (tx, ty) == down:
                continue
            if (tx, ty) in occupied_tiles:
                continue

            dx = tx - safe_cx
            dy = ty - safe_cy
            if dx * dx + dy * dy <= safe_radius_tiles * safe_radius_tiles:
                continue

            room = game_map.get_room_at(tx, ty)
            if room is None:
                continue  # no corridor events for now

            tag = getattr(room, "tag", "generic")
            if tag == "start":
                continue
            if tag == "event":
                event_room_tiles.append((tx, ty))
            else:
                other_room_tiles.append((tx, ty))

    if not event_room_tiles and not other_room_tiles:
        return

    # 0–2 events per floor, but if we have event rooms we try for at least 1
    max_events = min(2, len(event_room_tiles) + len(other_room_tiles))
    if max_events <= 0:
        return

    min_events = 1 if event_room_tiles else 0
    event_count = random.randint(min_events, max_events)
    if event_count <= 0:
        return

    chosen_tiles: list[tuple[int, int]] = []
    remaining = event_count

    random.shuffle(event_room_tiles)
    random.shuffle(other_room_tiles)

    # First event in an 'event' room if possible
    if event_room_tiles and remaining > 0:
        chosen_tiles.append(event_room_tiles.pop(0))
        remaining -= 1

    # Remaining events in any room tiles
    pool = event_room_tiles + other_room_tiles
    random.shuffle(pool)
    chosen_tiles.extend(pool[:remaining])

    # Choose which event types are available
    available_event_ids = list(EVENTS.keys())
    if not available_event_ids:
        return

    half_tile = TILE_SIZE // 2

    for tx, ty in chosen_tiles:
        # Bias event choice based on room tag, if any
        room = game_map.get_room_at(tx, ty)
        tag = getattr(room, "tag", "generic") if room is not None else "generic"

        if tag == "sanctum" and "sanctuary_font" in available_event_ids:
            # Strong bias towards healing/boon event in sanctum rooms
            weighted_ids = ["sanctuary_font"] * 3 + available_event_ids
            event_id = random.choice(weighted_ids)
        elif tag == "graveyard" and "cursed_tomb" in available_event_ids:
            # Graveyard rooms like cursed tombs
            weighted_ids = ["cursed_tomb"] * 3 + available_event_ids
            event_id = random.choice(weighted_ids)
        else:
            event_id = random.choice(available_event_ids)
        ex, ey = game_map.center_entity_on_tile(tx, ty, half_tile, half_tile)
        node = EventNode(
            x=ex,
            y=ey,
            width=half_tile,
            height=half_tile,
            event_id=event_id,
        )
        game_map.entities.append(node)


def spawn_chests_for_floor(game: "Game", game_map: GameMap, floor_index: int) -> None:
    """
    Spawn a few treasure chests on walkable tiles.

    Room-aware logic:
    - Avoid stairs and the spawn-safe radius.
    - Prefer placing at least one chest in a 'treasure' room if available.
    - Other chests go into generic rooms / corridors.
    """
    from world.entities import Chest  # local import to avoid circular

    chest_width = TILE_SIZE // 2
    chest_height = TILE_SIZE // 2

    up = game_map.up_stairs
    down = game_map.down_stairs

    # Safe radius (in tiles) around main spawn (usually up stairs)
    safe_radius_tiles = 3
    if up is not None:
        safe_cx, safe_cy = up
    else:
        safe_cx = game_map.width // 2
        safe_cy = game_map.height // 2

    # Tiles already occupied by entities (so we don't stack with enemies)
    occupied_tiles: set[tuple[int, int]] = set()
    for entity in getattr(game_map, "entities", []):
        if not hasattr(entity, "rect"):
            continue
        cx, cy = entity.rect.center
        tx, ty = game_map.world_to_tile(cx, cy)
        occupied_tiles.add((tx, ty))

    treasure_tiles: List[tuple[int, int]] = []
    other_tiles: List[tuple[int, int]] = []

    for ty in range(game_map.height):
        for tx in range(game_map.width):
            if not game_map.is_walkable_tile(tx, ty):
                continue
            if up is not None and (tx, ty) == up:
                continue
            if down is not None and (tx, ty) == down:
                continue
            if (tx, ty) in occupied_tiles:
                continue

            dx = tx - safe_cx
            dy = ty - safe_cy
            if dx * dx + dy * dy <= safe_radius_tiles * safe_radius_tiles:
                continue

            room = game_map.get_room_at(tx, ty) if hasattr(game_map, "get_room_at") else None
            if room is not None:
                tag = getattr(room, "tag", "generic")
                if tag == "start":
                    # No loot cluttering the start room
                    continue
                if tag == "treasure":
                    treasure_tiles.append((tx, ty))
                    continue

            # Default bucket for generic rooms / corridors
            other_tiles.append((tx, ty))

    if not treasure_tiles and not other_tiles:
        return

    random.shuffle(treasure_tiles)
    random.shuffle(other_tiles)

    # Scale chest count with floor size:
    # 0–2 on normal floors, up to 3 on big ones.
    screen_w, screen_h = game.screen.get_size()
    base_tiles_x = screen_w // TILE_SIZE
    base_tiles_y = screen_h // TILE_SIZE
    base_area = max(1, base_tiles_x * base_tiles_y)

    floor_area = game_map.width * game_map.height
    area_ratio = floor_area / base_area
    area_factor = math.sqrt(area_ratio) if area_ratio > 0 else 1.0
    area_factor = max(0.75, min(area_factor, 1.8))

    raw_max = 2 + (1 if area_factor > 1.3 else 0)
    max_chests = min(raw_max, len(treasure_tiles) + len(other_tiles))
    if max_chests <= 0:
        return

    # If we have treasure tiles, try for at least 1 chest (1..max_chests).
    # If not, 0..max_chests like before.
    min_chests = 1 if treasure_tiles else 0
    chest_count = random.randint(min_chests, max_chests)

    if chest_count <= 0:
        return

    chosen_spots: List[tuple[int, int]] = []
    remaining = chest_count

    # First chest in treasure room if possible
    if treasure_tiles and remaining > 0:
        chosen_spots.append(treasure_tiles[0])
        remaining -= 1

    # Remaining chests go into other tiles first, then spare treasure tiles
    pool: List[tuple[int, int]] = other_tiles + treasure_tiles[1:]
    random.shuffle(pool)

    for tx, ty in pool:
        if remaining <= 0:
            break
        chosen_spots.append((tx, ty))
        remaining -= 1

    for tx, ty in chosen_spots:
        x, y = game_map.center_entity_on_tile(tx, ty, chest_width, chest_height)
        chest = Chest(x=x, y=y, width=chest_width, height=chest_height)
        # Chests do not block movement
        setattr(chest, "blocks_movement", False)
        game_map.entities.append(chest)


def spawn_merchants_for_floor(game_map: GameMap, floor_index: int) -> None:
    """
    Spawn one stationary merchant in each 'shop' room, if any exist.

    Merchants:
    - Stand roughly at the room's tile centre.
    - Block movement (you walk around them).
    """
    from world.entities import Merchant  # local import to avoid circulars

    # If we don't have room metadata, we can't place shopkeepers
    if not getattr(game_map, "rooms", None):
        return

    up = game_map.up_stairs
    down = game_map.down_stairs

    # Tiles already occupied by entities (enemies, chests, events...)
    occupied_tiles: set[tuple[int, int]] = set()
    for entity in getattr(game_map, "entities", []):
        if not hasattr(entity, "rect"):
            continue
        cx, cy = entity.rect.center
        tx, ty = game_map.world_to_tile(cx, cy)
        occupied_tiles.add((tx, ty))

    # Collect all walkable tiles for each distinct shop room
    room_tiles: dict[object, list[tuple[int, int]]] = {}

    for ty in range(game_map.height):
        for tx in range(game_map.width):
            if not game_map.is_walkable_tile(tx, ty):
                continue
            if up is not None and (tx, ty) == up:
                continue
            if down is not None and (tx, ty) == down:
                continue
            if (tx, ty) in occupied_tiles:
                continue

            if not hasattr(game_map, "get_room_at"):
                continue
            room = game_map.get_room_at(tx, ty)
            if room is None:
                continue
            if getattr(room, "tag", "") != "shop":
                continue

            room_tiles.setdefault(room, []).append((tx, ty))

    if not room_tiles:
        return

    merchant_w = TILE_SIZE // 2
    merchant_h = TILE_SIZE // 2

    for room, tiles in room_tiles.items():
        if not tiles:
            continue

        # Try to place merchant near the "centre" of the room's tiles
        avg_tx = sum(t[0] for t in tiles) // len(tiles)
        avg_ty = sum(t[1] for t in tiles) // len(tiles)

        candidate_tiles = [(avg_tx, avg_ty)] + tiles
        chosen_tx: Optional[int] = None
        chosen_ty: Optional[int] = None

        for tx, ty in candidate_tiles:
            if (tx, ty) in occupied_tiles:
                continue
            # Never spawn merchants on stairs tiles
            if up is not None and (tx, ty) == up:
                continue
            if down is not None and (tx, ty) == down:
                continue
            chosen_tx, chosen_ty = tx, ty
            break

        if chosen_tx is None or chosen_ty is None:
            continue

        mx, my = game_map.center_entity_on_tile(
            chosen_tx,
            chosen_ty,
            merchant_w,
            merchant_h,
        )
        merchant = Merchant(
            x=mx,
            y=my,
            width=merchant_w,
            height=merchant_h,
        )
        # Merchants block movement
        merchant.blocks_movement = True

        game_map.entities.append(merchant)
        occupied_tiles.add((chosen_tx, chosen_ty))


def ensure_debug_merchant_on_floor_three(
    game_map: GameMap,
    floor_index: int,
) -> None:
    """
    Debug / testing helper:

    On floor 3, if no Merchant was spawned (e.g. no 'shop' room on that
    seed), force-spawn a single Merchant near the DOWN stairs tile (but not ON it).

    This guarantees a merchant for testing without affecting other floors.
    """
    if floor_index != 3:
        return

    # If there's already at least one merchant, do nothing
    for entity in getattr(game_map, "entities", []):
        if isinstance(entity, Merchant):
            return

    # Find a walkable tile near the down stairs (but not ON the stairs)
    up = game_map.up_stairs
    down = game_map.down_stairs
    
    # Get occupied tiles
    occupied_tiles: set[tuple[int, int]] = set()
    for entity in getattr(game_map, "entities", []):
        if not hasattr(entity, "rect"):
            continue
        cx, cy = entity.rect.center
        tx, ty = game_map.world_to_tile(cx, cy)
        occupied_tiles.add((tx, ty))
    
    # Start from down stairs position, or center if no stairs
    if down is not None:
        start_tx, start_ty = down
    else:
        start_tx = game_map.width // 2
        start_ty = game_map.height // 2

    # Search for a nearby walkable tile (not on stairs, not occupied)
    chosen_tx: Optional[int] = None
    chosen_ty: Optional[int] = None
    
    # Search in expanding radius around the stairs
    for radius in range(1, 5):
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if abs(dx) < radius and abs(dy) < radius:
                    continue  # Only check the perimeter of this radius
                tx = start_tx + dx
                ty = start_ty + dy
                
                if tx < 0 or tx >= game_map.width or ty < 0 or ty >= game_map.height:
                    continue
                if not game_map.is_walkable_tile(tx, ty):
                    continue
                if up is not None and (tx, ty) == up:
                    continue
                if down is not None and (tx, ty) == down:
                    continue
                if (tx, ty) in occupied_tiles:
                    continue
                
                chosen_tx, chosen_ty = tx, ty
                break
            
            if chosen_tx is not None:
                break
        if chosen_tx is not None:
            break
    
    # Fallback: just find any walkable tile
    if chosen_tx is None:
        for ty in range(game_map.height):
            for tx in range(game_map.width):
                if not game_map.is_walkable_tile(tx, ty):
                    continue
                if up is not None and (tx, ty) == up:
                    continue
                if down is not None and (tx, ty) == down:
                    continue
                if (tx, ty) in occupied_tiles:
                    continue
                chosen_tx, chosen_ty = tx, ty
                break
            if chosen_tx is not None:
                break
    
    if chosen_tx is None or chosen_ty is None:
        return  # Can't find a valid spot

    merchant_w = TILE_SIZE // 2
    merchant_h = TILE_SIZE // 2

    mx, my = game_map.center_entity_on_tile(
        chosen_tx,
        chosen_ty,
        merchant_w,
        merchant_h,
    )

    merchant = Merchant(
        x=mx,
        y=my,
        width=merchant_w,
        height=merchant_h,
    )
    merchant.blocks_movement = True

    game_map.entities.append(merchant)


def spawn_traps_for_floor(game_map: GameMap, floor_index: int) -> None:
    """
    Spawn traps on walkable tiles.
    
    Room-aware logic:
    - Avoid stairs and spawn-safe radius.
    - Prefer corridors and doorways (chokepoints).
    - Sometimes place near treasure (risk/reward).
    - Scale trap count with floor depth.
    """
    if not TRAPS:
        return  # No traps registered
    
    trap_width = TILE_SIZE // 3  # Smaller than chests
    trap_height = TILE_SIZE // 3
    
    up = game_map.up_stairs
    down = game_map.down_stairs
    
    # Safe radius around main spawn
    safe_radius_tiles = 3
    if up is not None:
        safe_cx, safe_cy = up
    else:
        safe_cx = game_map.width // 2
        safe_cy = game_map.height // 2
    
    # Tiles already occupied by entities
    occupied_tiles: set[tuple[int, int]] = set()
    for entity in getattr(game_map, "entities", []):
        if not hasattr(entity, "rect"):
            continue
        cx, cy = entity.rect.center
        tx, ty = game_map.world_to_tile(cx, cy)
        occupied_tiles.add((tx, ty))
    
    # Categorize tiles: corridors, doorways, treasure rooms, other
    corridor_tiles: list[tuple[int, int]] = []
    treasure_tiles: list[tuple[int, int]] = []
    other_tiles: list[tuple[int, int]] = []
    
    for ty in range(game_map.height):
        for tx in range(game_map.width):
            if not game_map.is_walkable_tile(tx, ty):
                continue
            if up is not None and (tx, ty) == up:
                continue
            if down is not None and (tx, ty) == down:
                continue
            if (tx, ty) in occupied_tiles:
                continue
            
            dx = tx - safe_cx
            dy = ty - safe_cy
            if dx * dx + dy * dy <= safe_radius_tiles * safe_radius_tiles:
                continue
            
            room = game_map.get_room_at(tx, ty) if hasattr(game_map, "get_room_at") else None
            if room is None:
                # Corridors are good for traps (chokepoints)
                corridor_tiles.append((tx, ty))
            else:
                tag = getattr(room, "tag", "generic")
                if tag == "start" or tag == "sanctum":
                    continue  # No traps in safe areas
                elif tag == "treasure":
                    treasure_tiles.append((tx, ty))
                else:
                    other_tiles.append((tx, ty))
    
    if not (corridor_tiles or treasure_tiles or other_tiles):
        return
    
    # Scale trap count: 1-3 traps per floor, more on deeper floors
    base_traps = 1 + (floor_index // 3)  # 1 on floors 1-2, 2 on 3-5, 3 on 6+
    max_traps = min(3, base_traps)
    
    # Prefer corridors (chokepoints), then treasure rooms (risk/reward)
    random.shuffle(corridor_tiles)
    random.shuffle(treasure_tiles)
    random.shuffle(other_tiles)
    
    chosen_tiles: list[tuple[int, int]] = []
    remaining = max_traps
    
    # 50% chance to place a trap near treasure (risk/reward)
    if treasure_tiles and remaining > 0 and random.random() < 0.5:
        chosen_tiles.append(treasure_tiles[0])
        remaining -= 1
    
    # Fill rest from corridors (preferred) and other tiles
    pool = corridor_tiles + other_tiles
    random.shuffle(pool)
    chosen_tiles.extend(pool[:remaining])
    
    if not chosen_tiles:
        return
    
    # Choose trap types (weighted by floor)
    available_trap_ids = list(TRAPS.keys())
    
    # Early floors: simpler traps (spike, weakness)
    # Later floors: more dangerous traps (poison, fire, teleport)
    if floor_index <= 2:
        preferred = ["spike_trap", "weakness_trap", "gold_trap"]
        trap_pool = [t for t in preferred if t in available_trap_ids] or available_trap_ids
    elif floor_index <= 5:
        preferred = ["spike_trap", "poison_trap", "fire_trap", "weakness_trap"]
        trap_pool = [t for t in preferred if t in available_trap_ids] or available_trap_ids
    else:
        # Deep floors: all traps available
        trap_pool = available_trap_ids
    
    for tx, ty in chosen_tiles:
        trap_id = random.choice(trap_pool)
        x, y = game_map.center_entity_on_tile(tx, ty, trap_width, trap_height)
        trap = Trap(
            x=x,
            y=y,
            width=trap_width,
            height=trap_height,
            trap_id=trap_id,
            detected=False,
        )
        game_map.entities.append(trap)


def spawn_all_entities_for_floor(
    game: "Game",
    game_map: GameMap,
    floor_index: int,
) -> None:
    """
    Spawn all entities (enemies, events, chests, merchants, traps) for a floor.
    This is the main entry point called from Game.load_floor().
    """
    spawn_enemies_for_floor(game, game_map, floor_index)
    spawn_events_for_floor(game_map, floor_index)
    spawn_chests_for_floor(game, game_map, floor_index)
    spawn_merchants_for_floor(game_map, floor_index)
    spawn_traps_for_floor(game_map, floor_index)

    # Debug/testing: always ensure at least one merchant on floor 3
    ensure_debug_merchant_on_floor_three(game_map, floor_index)

