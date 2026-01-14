"""
Camp map generation.

Generates a small outdoor camp map with:
- simple ground tiles
- a central campfire
- a few blocking tent tiles around the campfire
- NPCs (merchant, guard, traveler) for friendly camps
- Enemy entities for hostile camps
"""

import random
from typing import Optional, List, TYPE_CHECKING

from settings import WINDOW_WIDTH, WINDOW_HEIGHT, TILE_SIZE
from .tiles import CAMP_GROUND_TILE, CAMP_FIRE_TILE, CAMP_TENT_TILE
from ..game_map import GameMap
from ..tiles import WALL_TILE

if TYPE_CHECKING:
    from world.entities import Entity


def _create_empty_map(width: int, height: int) -> List[List[object]]:
    """Create a solid-wall map as a base."""
    return [[WALL_TILE for _ in range(width)] for _ in range(height)]


def generate_camp(
    level: int,
    camp_name: str,
    seed: Optional[int] = None,
    is_hostile: bool = False,
    has_merchant: bool = True,
) -> GameMap:
    """
    Generate a simple camp map.

    - Small size (around 20x20 to 30x30 tiles, scaled from window size)
    - Central campfire area
    - A few tents placed around the campfire
    - Simple ground tiles
    - NPCs for friendly camps (merchant, guard, traveler)
    - Enemy entities for hostile camps
    
    Args:
        level: Camp level (affects enemy strength if hostile)
        camp_name: Name of the camp
        seed: Random seed for deterministic generation
        is_hostile: If True, place enemies instead of friendly NPCs
        has_merchant: If True and not hostile, place a merchant NPC
    """
    if seed is not None:
        random.seed(seed)

    # Base on screen size but clamp to a small area
    base_tiles_x = WINDOW_WIDTH // TILE_SIZE
    base_tiles_y = WINDOW_HEIGHT // TILE_SIZE

    # Camps are smaller than full floors
    scale = 0.6
    width = max(20, int(base_tiles_x * scale))
    height = max(20, int(base_tiles_y * scale))

    tiles = _create_empty_map(width, height)

    # Carve out a simple ground area for the whole camp
    for y in range(1, height - 1):
        for x in range(1, width - 1):
            tiles[y][x] = CAMP_GROUND_TILE

    # Place central campfire
    center_x = width // 2
    center_y = height // 2
    tiles[center_y][center_x] = CAMP_FIRE_TILE

    # Place a few tents in a loose ring around the campfire
    tent_positions = []
    for _ in range(4):
        dx = random.randint(-4, 4)
        dy = random.randint(-4, 4)
        tx = max(2, min(width - 3, center_x + dx))
        ty = max(2, min(height - 3, center_y + dy))
        if tiles[ty][tx] is CAMP_GROUND_TILE:
            tiles[ty][tx] = CAMP_TENT_TILE
            tent_positions.append((tx, ty))

    game_map = GameMap(tiles)
    entities: List["Entity"] = []

    # Place NPCs or enemies based on camp type
    if is_hostile:
        # Place enemy entities for hostile camps
        from world.entities import Enemy
        from systems.enemies import get_enemy_archetype
        
        # Place 2-4 enemies around the camp
        num_enemies = random.randint(2, 4)
        for i in range(num_enemies):
            # Place enemies near tents or around the perimeter
            if tent_positions and random.random() < 0.5:
                # Place near a tent
                tent_x, tent_y = random.choice(tent_positions)
                offset_x = random.randint(-2, 2)
                offset_y = random.randint(-2, 2)
                enemy_tx = max(1, min(width - 2, tent_x + offset_x))
                enemy_ty = max(1, min(height - 2, tent_y + offset_y))
            else:
                # Place around perimeter
                side = random.choice(["top", "bottom", "left", "right"])
                if side == "top":
                    enemy_tx = random.randint(2, width - 3)
                    enemy_ty = 2
                elif side == "bottom":
                    enemy_tx = random.randint(2, width - 3)
                    enemy_ty = height - 3
                elif side == "left":
                    enemy_tx = 2
                    enemy_ty = random.randint(2, height - 3)
                else:  # right
                    enemy_tx = width - 3
                    enemy_ty = random.randint(2, height - 3)
            
            # Convert to world coordinates
            world_x, world_y = game_map.center_entity_on_tile(
                enemy_tx, enemy_ty, 24, 24
            )
            
            # Create enemy (use basic enemy archetype for now)
            enemy = Enemy(
                x=world_x,
                y=world_y,
                width=24,
                height=24,
                speed=0.0,  # Enemies in camps might be stationary initially
                max_hp=20 + (level * 5),
                hp=20 + (level * 5),
            )
            # Set enemy archetype if available
            try:
                archetype = get_enemy_archetype("goblin")  # Default archetype
                if archetype:
                    enemy.archetype_id = archetype.id
            except Exception:
                pass
            
            entities.append(enemy)
    else:
        # Place friendly NPCs
        try:
            from world.village.npcs import VillageNPC, MerchantNPC, VillagerNPC
            
            # Place merchant if available
            if has_merchant:
                # Place merchant near campfire but not on it
                merchant_offset_x = random.choice([-2, -1, 1, 2])
                merchant_offset_y = random.choice([-2, -1, 1, 2])
                merchant_tx = max(1, min(width - 2, center_x + merchant_offset_x))
                merchant_ty = max(1, min(height - 2, center_y + merchant_offset_y))
                
                world_x, world_y = game_map.center_entity_on_tile(
                    merchant_tx, merchant_ty, 24, 24
                )
                
                merchant = MerchantNPC(
                    world_x, world_y,
                    npc_id="camp_merchant",
                    name=None,  # Will generate name
                )
                # Mark as camp merchant for special handling
                merchant.npc_type = "camp_merchant"  # type: ignore
                entities.append(merchant)
            
            # Place 1-2 additional NPCs (guard or traveler)
            num_extra_npcs = random.randint(1, 2)
            for i in range(num_extra_npcs):
                # Place around campfire
                npc_offset_x = random.randint(-3, 3)
                npc_offset_y = random.randint(-3, 3)
                npc_tx = max(1, min(width - 2, center_x + npc_offset_x))
                npc_ty = max(1, min(height - 2, center_y + npc_offset_y))
                
                # Skip if too close to campfire or merchant
                if (npc_tx, npc_ty) == (center_x, center_y):
                    continue
                if has_merchant and abs(npc_tx - merchant_tx) < 2 and abs(npc_ty - merchant_ty) < 2:
                    continue
                
                world_x, world_y = game_map.center_entity_on_tile(
                    npc_tx, npc_ty, 24, 24
                )
                
                # Randomly choose guard or traveler
                npc_type = random.choice(["guard", "traveler"])
                if npc_type == "guard":
                    npc = VillagerNPC(
                        world_x, world_y,
                        npc_id=f"camp_guard_{i}",
                        name=None,
                    )
                    npc.npc_type = "camp_guard"  # type: ignore
                    npc.color = (150, 150, 200)  # Guard color
                else:  # traveler
                    npc = VillagerNPC(
                        world_x, world_y,
                        npc_id=f"camp_traveler_{i}",
                        name=None,
                    )
                    npc.npc_type = "camp_traveler"  # type: ignore
                    npc.color = (200, 180, 150)  # Traveler color
                
                entities.append(npc)
        except ImportError:
            # Village NPCs not available, skip NPC placement
            pass

    # Add entities to map
    game_map.entities = entities

    # Place exit tiles on edges (simpler than villages - just mark edge tiles)
    exit_tiles = _place_camp_exits(tiles, width, height, center_x, center_y)
    game_map.camp_exit_tiles = exit_tiles  # type: ignore[attr-defined]

    # Expose camp metadata
    game_map.camp_center = (center_x, center_y)  # type: ignore[attr-defined]
    game_map.camp_fire_pos = (center_x, center_y)  # type: ignore[attr-defined]

    return game_map


def _place_camp_exits(
    tiles: List[List],
    map_width: int,
    map_height: int,
    center_x: int,
    center_y: int,
) -> List[tuple[int, int]]:
    """
    Place exit points on edges of the camp map.
    Since camps are small, we'll place exits on all four edges (3 tiles wide each).
    
    Returns:
        List of (x, y) tile coordinates that are exit points
    """
    exit_tiles: List[tuple[int, int]] = []
    exit_width = 3  # 3 tiles wide exits for camps (smaller than villages)
    
    # Top edge exit (centered horizontally)
    top_exit_start = max(1, center_x - exit_width // 2)
    top_exit_end = min(map_width - 1, top_exit_start + exit_width)
    for x in range(top_exit_start, top_exit_end):
        if 0 <= x < map_width and 0 < map_height:
            # Ensure it's walkable (ground tile)
            tiles[0][x] = CAMP_GROUND_TILE
            exit_tiles.append((x, 0))
    
    # Bottom edge exit (centered horizontally)
    bottom_exit_start = max(1, center_x - exit_width // 2)
    bottom_exit_end = min(map_width - 1, bottom_exit_start + exit_width)
    for x in range(bottom_exit_start, bottom_exit_end):
        if 0 <= x < map_width and map_height > 0:
            # Ensure it's walkable (ground tile)
            tiles[map_height - 1][x] = CAMP_GROUND_TILE
            exit_tiles.append((x, map_height - 1))
    
    # Left edge exit (centered vertically)
    left_exit_start = max(1, center_y - exit_width // 2)
    left_exit_end = min(map_height - 1, left_exit_start + exit_width)
    for y in range(left_exit_start, left_exit_end):
        if 0 < map_width and 0 <= y < map_height:
            # Ensure it's walkable (ground tile)
            tiles[y][0] = CAMP_GROUND_TILE
            exit_tiles.append((0, y))
    
    # Right edge exit (centered vertically)
    right_exit_start = max(1, center_y - exit_width // 2)
    right_exit_end = min(map_height - 1, right_exit_start + exit_width)
    for y in range(right_exit_start, right_exit_end):
        if map_width > 0 and 0 <= y < map_height:
            # Ensure it's walkable (ground tile)
            tiles[y][map_width - 1] = CAMP_GROUND_TILE
            exit_tiles.append((map_width - 1, y))
    
    return exit_tiles



