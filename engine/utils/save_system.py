"""
Save/Load system for the game.

Handles serialization and deserialization of game state to/from JSON files.
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import asdict, is_dataclass

from systems.progression import HeroStats
from systems.inventory import Inventory
from systems.party import CompanionState
from systems.stats import StatBlock
from world.game_map import GameMap
from world.entities import Player
from world.tiles import Tile, FLOOR_TILE, WALL_TILE, UP_STAIRS_TILE, DOWN_STAIRS_TILE


# Save directory (in project root / saves)
SAVE_DIR = Path(__file__).resolve().parent.parent / "saves"
SAVE_DIR.mkdir(exist_ok=True)


def get_save_path(slot: int = 1) -> Path:
    """Get the file path for a save slot."""
    return SAVE_DIR / f"save_{slot}.json"


def save_game(game, slot: int = 1) -> bool:
    """
    Save the current game state to a file.
    
    Args:
        game: The Game instance to save
        slot: Save slot number (1-9)
    
    Returns:
        True if save was successful, False otherwise
    """
    try:
        save_data = _serialize_game(game)
        save_path = get_save_path(slot)
        
        # Write to a temporary file first, then rename (atomic write)
        temp_path = save_path.with_suffix(".tmp")
        with temp_path.open("w", encoding="utf-8") as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)
        
        # Atomic rename
        temp_path.replace(save_path)
        return True
    except Exception as e:
        print(f"Error saving game: {e}")
        return False


def load_game(screen, slot: int = 1) -> Optional[Any]:
    """
    Load a game from a save file.
    
    Args:
        screen: pygame.Surface for the game
        slot: Save slot number (1-9)
    
    Returns:
        Game instance if load was successful, None otherwise
    """
    try:
        save_path = get_save_path(slot)
        if not save_path.exists():
            return None
        
        with save_path.open("r", encoding="utf-8") as f:
            save_data = json.load(f)
        
        return _deserialize_game(screen, save_data)
    except Exception as e:
        print(f"Error loading game: {e}")
        return None


def list_saves() -> Dict[int, Dict[str, Any]]:
    """
    List all available save files with metadata.
    
    Returns:
        Dict mapping slot numbers to save metadata (floor, hero_name, timestamp, etc.)
    """
    saves = {}
    
    for slot in range(1, 10):  # Slots 1-9
        save_path = get_save_path(slot)
        if not save_path.exists():
            continue
        
        try:
            with save_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Extract metadata
            hero_stats = data.get("hero_stats", {})
            saves[slot] = {
                "floor": data.get("floor", 1),
                "hero_name": hero_stats.get("hero_name", "Unknown"),
                "hero_class": hero_stats.get("hero_class_id", "unknown"),
                "level": hero_stats.get("level", 1),
                "timestamp": save_path.stat().st_mtime,
            }
        except Exception:
            # Corrupted save file, skip it
            continue
    
    return saves


# -----------------------------------------------------------------------------
# Serialization helpers
# -----------------------------------------------------------------------------

def _serialize_game(game) -> Dict[str, Any]:
    """Convert a Game instance to a JSON-serializable dict."""
    
    # Serialize hero stats
    hero_stats_dict = _serialize_hero_stats(game.hero_stats)
    
    # Serialize inventory
    inventory_dict = _serialize_inventory(game.inventory)
    
    # Serialize party
    party_list = [_serialize_companion(comp) for comp in game.party]
    
    # Serialize floors (current map state)
    floors_dict = {}
    for floor_num, floor_map in game.floors.items():
        floors_dict[str(floor_num)] = _serialize_map(floor_map)
    
    # Serialize current map index
    current_floor_num = game.floor
    
    # Serialize player position (if exists)
    player_data = None
    if game.player is not None:
        player_data = {
            "x": float(game.player.x),
            "y": float(game.player.y),
            "hp": int(game.player.hp),
            "max_hp": int(game.player.max_hp),
        }
    
    # Serialize message log
    message_log_data = {
        "messages": list(game.message_log.exploration_log),
        "last_message": game.message_log.last_message,
    }
    
    # Serialize camera
    camera_data = {
        "x": float(game.camera_x),
        "y": float(game.camera_y),
        "zoom_index": int(game.zoom_index),
    }

    # Consumables are stored as regular inventory items with slot==\"consumable\",
    # so they are already covered by the inventory serializer. No extra section
    # is required here for Phase 1.
    
    # Serialize overworld
    overworld_data = None
    if hasattr(game, "overworld_map") and game.overworld_map is not None:
        overworld_data = _serialize_overworld(game.overworld_map)
    
    # Serialize POIs
    pois_data = {}
    if hasattr(game, "overworld_map") and game.overworld_map is not None:
        pois_data = _serialize_pois(game.overworld_map)
    
    # Serialize time system
    time_data = None
    if hasattr(game, "time_system") and game.time_system is not None:
        time_data = {
            "days": game.time_system.days,
            "hours": game.time_system.hours,
            "minutes": game.time_system.minutes,
        }
    
    # Current POI reference
    current_poi_id = None
    if hasattr(game, "current_poi") and game.current_poi is not None:
        current_poi_id = game.current_poi.poi_id

    return {
        "version": "1.1",  # Save format version (bumped for overworld support)
        "floor": current_floor_num,
        "hero_stats": hero_stats_dict,
        "inventory": inventory_dict,
        "party": party_list,
        "floors": floors_dict,
        "player": player_data,
        "message_log": message_log_data,
        "camera": camera_data,
        "overworld": overworld_data,
        "pois": pois_data,
        "time": time_data,
        "current_poi": current_poi_id,
    }


def _serialize_hero_stats(hero_stats: HeroStats) -> Dict[str, Any]:
    """Serialize HeroStats to dict."""
    return {
        "level": hero_stats.level,
        "xp": hero_stats.xp,
        "gold": hero_stats.gold,
        "hero_class_id": hero_stats.hero_class_id,
        "hero_name": hero_stats.hero_name,
        "base": _serialize_stat_block(hero_stats.base),
        "perks": list(hero_stats.perks),
        "skill_slots": hero_stats.skill_slots,
        "skill_points": hero_stats.skill_points,
        "skill_ranks": dict(hero_stats.skill_ranks),
    }


def _serialize_stat_block(stat_block: StatBlock) -> Dict[str, Any]:
    """Serialize StatBlock to dict."""
    return {
        "max_hp": stat_block.max_hp,
        "attack": stat_block.attack,
        "defense": stat_block.defense,
        "skill_power": stat_block.skill_power,
        "crit_chance": stat_block.crit_chance,
        "dodge_chance": stat_block.dodge_chance,
        "status_resist": stat_block.status_resist,
        "max_mana": stat_block.max_mana,
        "max_stamina": stat_block.max_stamina,
        "stamina_regen_bonus": stat_block.stamina_regen_bonus,
        "mana_regen_bonus": stat_block.mana_regen_bonus,
        "speed": stat_block.speed,
        "initiative": stat_block.initiative,
        "movement_points_bonus": stat_block.movement_points_bonus,
    }


def _serialize_inventory(inventory: Inventory) -> Dict[str, Any]:
    """Serialize Inventory to dict."""
    return {
        "items": list(inventory.items),
        "equipped": dict(inventory.equipped),
    }


def _serialize_companion(companion: CompanionState) -> Dict[str, Any]:
    """Serialize CompanionState to dict."""
    return {
        "template_id": companion.template_id,
        "name_override": companion.name_override,
        "level": companion.level,
        "xp": companion.xp,
        "class_id": companion.class_id,
        "perks": list(companion.perks),
        "equipped": dict(companion.equipped),
        "skill_slots": companion.skill_slots,
        "skill_points": companion.skill_points,
        "skill_ranks": dict(companion.skill_ranks),
    }


def _serialize_map(game_map: GameMap) -> Dict[str, Any]:
    """Serialize GameMap to dict."""
    # Serialize tiles as a 2D list of tile type strings
    tiles_data = []
    for row in game_map.tiles:
        row_data = []
        for tile in row:
            # Convert Tile to string identifier
            if tile == FLOOR_TILE:
                row_data.append("floor")
            elif tile == WALL_TILE:
                row_data.append("wall")
            elif tile == UP_STAIRS_TILE:
                row_data.append("up_stairs")
            elif tile == DOWN_STAIRS_TILE:
                row_data.append("down_stairs")
            else:
                row_data.append("floor")  # fallback
        tiles_data.append(row_data)
    
    # Serialize explored/visible sets as lists of tuples
    explored_list = [list(coord) for coord in game_map.explored]
    visible_list = [list(coord) for coord in game_map.visible]
    
    # Serialize entities (only basic info, enemies are regenerated)
    entities_data = []
    for entity in game_map.entities:
        # Only save non-enemy entities (chests, merchants, etc.)
        # Enemies will be respawned when loading
        entity_type = type(entity).__name__
        if entity_type not in ("Enemy",):  # Skip enemies
            entities_data.append({
                "type": entity_type,
                "x": float(entity.x),
                "y": float(entity.y),
            })
    
    return {
        "tiles": tiles_data,
        "width": game_map.width,
        "height": game_map.height,
        "up_stairs": list(game_map.up_stairs) if game_map.up_stairs else None,
        "down_stairs": list(game_map.down_stairs) if game_map.down_stairs else None,
        "explored": explored_list,
        "visible": visible_list,
        "entities": entities_data,
    }


def _serialize_overworld(overworld_map) -> Dict[str, Any]:
    """Serialize OverworldMap to dict."""
    # Serialize terrain tiles
    tiles_data = []
    for row in overworld_map.tiles:
        row_data = []
        for tile in row:
            # Store terrain ID
            row_data.append(tile.id if hasattr(tile, "id") else "grass")
        tiles_data.append(row_data)
    
    # Serialize explored tiles
    explored_list = [list(coord) for coord in overworld_map.explored_tiles]
    
    return {
        "width": overworld_map.width,
        "height": overworld_map.height,
        "seed": overworld_map.seed,
        "tiles": tiles_data,
        "player_position": list(overworld_map.player_position),
        "explored_tiles": explored_list,
    }


def _serialize_pois(overworld_map) -> Dict[str, Any]:
    """Serialize all POIs to dict."""
    pois_data = {}
    
    for poi in overworld_map.get_all_pois():
        poi_data = {
            "poi_id": poi.poi_id,
            "poi_type": poi.poi_type,
            "position": list(poi.position),
            "level": poi.level,
            "name": poi.name,
            "discovered": poi.discovered,
            "cleared": poi.cleared,
            "state": poi.state,
        }
        
        # Add type-specific data
        if poi.poi_type == "dungeon" and hasattr(poi, "floor_count"):
            poi_data["floor_count"] = poi.floor_count
            poi_data["cleared_floors"] = list(poi.cleared_floors)
        
        pois_data[poi.poi_id] = poi_data
    
    return pois_data


# -----------------------------------------------------------------------------
# Deserialization helpers
# -----------------------------------------------------------------------------

def _deserialize_game(screen, save_data: Dict[str, Any]) -> Any:
    """Reconstruct a Game instance from saved data."""
    from ..core.game import Game
    
    # Get hero class from save data
    hero_class_id = save_data.get("hero_stats", {}).get("hero_class_id", "warrior")
    
    # Create game instance
    game = Game(screen, hero_class_id=hero_class_id)
    
    # Restore hero stats
    if "hero_stats" in save_data:
        _deserialize_hero_stats(game.hero_stats, save_data["hero_stats"])
    
    # Restore inventory
    if "inventory" in save_data:
        _deserialize_inventory(game.inventory, save_data["inventory"])
    
    # Restore party
    if "party" in save_data:
        game.party = [
            _deserialize_companion(comp_data)
            for comp_data in save_data["party"]
        ]
    
    # Restore floors
    if "floors" in save_data:
        game.floors = {}
        for floor_str, floor_data in save_data["floors"].items():
            floor_num = int(floor_str)
            game.floors[floor_num] = _deserialize_map(floor_data)
    
    # Restore current floor
    game.floor = save_data.get("floor", 1)
    
    # Restore current map
    if game.floor in game.floors:
        game.current_map = game.floors[game.floor]
    else:
        # Regenerate if missing
        game.load_floor(game.floor, from_direction=None)
    
    # Restore player
    if "player" in save_data and save_data["player"] is not None:
        player_data = save_data["player"]
        if game.player is not None:
            game.player.x = player_data["x"]
            game.player.y = player_data["y"]
            game.player.hp = player_data["hp"]
            game.player.max_hp = player_data["max_hp"]
    
    # Restore message log
    if "message_log" in save_data:
        log_data = save_data["message_log"]
        game.message_log.exploration_log = list(log_data.get("messages", []))
        game.message_log.last_message = log_data.get("last_message", "")
    
    # Restore camera
    if "camera" in save_data:
        camera_data = save_data["camera"]
        game.camera_x = camera_data.get("x", 0.0)
        game.camera_y = camera_data.get("y", 0.0)
        game.zoom_index = camera_data.get("zoom_index", 1)
    
    # Re-apply hero stats to player
    if game.player is not None:
        game.apply_hero_stats_to_player(full_heal=False)
        # Restore HP from save
        if "player" in save_data and save_data["player"]:
            game.player.hp = save_data["player"]["hp"]
    
    # Recalculate companion stats
    for companion in game.party:
        from systems.party import recalc_companion_stats_for_level, get_companion
        try:
            template = get_companion(companion.template_id)
            recalc_companion_stats_for_level(companion, template)
        except KeyError:
            pass
    
    # Restore overworld
    if "overworld" in save_data and save_data["overworld"] is not None:
        game.overworld_map = _deserialize_overworld(save_data["overworld"])
    
    # Restore POIs
    if "pois" in save_data and game.overworld_map is not None:
        _deserialize_pois(game.overworld_map, save_data["pois"])
    
    # Restore time system
    if "time" in save_data and save_data["time"] is not None:
        from world.time import TimeSystem
        time_data = save_data["time"]
        game.time_system = TimeSystem(
            days=time_data.get("days", 0),
            hours=time_data.get("hours", 0),
            minutes=time_data.get("minutes", 0),
        )
    
    # Restore current POI reference
    if "current_poi" in save_data and save_data["current_poi"] is not None:
        if game.overworld_map is not None:
            poi_id = save_data["current_poi"]
            if poi_id in game.overworld_map.pois:
                game.current_poi = game.overworld_map.pois[poi_id]
    
    # Set game mode based on current POI
    from ..core.game import GameMode
    if game.current_poi is not None:
        game.mode = GameMode.EXPLORATION
    elif game.overworld_map is not None:
        game.mode = GameMode.OVERWORLD
    
    return game


def _deserialize_hero_stats(hero_stats: HeroStats, data: Dict[str, Any]) -> None:
    """Restore HeroStats from dict."""
    hero_stats.level = data.get("level", 1)
    hero_stats.xp = data.get("xp", 0)
    hero_stats.gold = data.get("gold", 0)
    hero_stats.hero_class_id = data.get("hero_class_id", "warrior")
    hero_stats.hero_name = data.get("hero_name", "Adventurer")
    hero_stats.perks = list(data.get("perks", []))
    hero_stats.skill_slots = list(data.get("skill_slots", [None, None, None, None]))
    hero_stats.skill_points = data.get("skill_points", 0)
    hero_stats.skill_ranks = dict(data.get("skill_ranks", {}))
    
    if "base" in data:
        _deserialize_stat_block(hero_stats.base, data["base"])


def _deserialize_stat_block(stat_block: StatBlock, data: Dict[str, Any]) -> None:
    """Restore StatBlock from dict."""
    stat_block.max_hp = data.get("max_hp", 30)
    stat_block.attack = data.get("attack", 5)
    stat_block.defense = data.get("defense", 0)
    stat_block.skill_power = data.get("skill_power", 1.0)
    stat_block.crit_chance = data.get("crit_chance", 0.1)
    stat_block.dodge_chance = data.get("dodge_chance", 0.0)
    stat_block.status_resist = data.get("status_resist", 0.0)
    stat_block.max_mana = data.get("max_mana", 0)
    stat_block.max_stamina = data.get("max_stamina", 6)
    stat_block.stamina_regen_bonus = data.get("stamina_regen_bonus", 0)
    stat_block.mana_regen_bonus = data.get("mana_regen_bonus", 0)
    stat_block.speed = data.get("speed", 1.0)
    stat_block.initiative = data.get("initiative", 10)
    stat_block.movement_points_bonus = data.get("movement_points_bonus", 0)


def _deserialize_inventory(inventory: Inventory, data: Dict[str, Any]) -> None:
    """Restore Inventory from dict."""
    inventory.items = list(data.get("items", []))
    inventory.equipped = dict(data.get("equipped", {"weapon": None, "armor": None, "trinket": None}))


def _deserialize_companion(data: Dict[str, Any]) -> CompanionState:
    """Reconstruct CompanionState from dict."""
    companion = CompanionState(
        template_id=data["template_id"],
        name_override=data.get("name_override"),
        level=data.get("level", 1),
        xp=data.get("xp", 0),
        class_id=data.get("class_id"),
        perks=list(data.get("perks", [])),
        equipped=dict(data.get("equipped", {"weapon": None, "armor": None, "trinket": None})),
        skill_slots=list(data.get("skill_slots", [None, None, None, None])),
        skill_points=data.get("skill_points", 0),
        skill_ranks=dict(data.get("skill_ranks", {})),
    )
    return companion


def _deserialize_map(data: Dict[str, Any]) -> GameMap:
    """Reconstruct GameMap from dict."""
    from world.tiles import Tile
    from world.mapgen import RectRoom
    
    # Reconstruct tiles
    tiles_data = data.get("tiles", [])
    tiles = []
    for row_data in tiles_data:
        row = []
        for tile_str in row_data:
            if tile_str == "floor":
                row.append(FLOOR_TILE)
            elif tile_str == "wall":
                row.append(WALL_TILE)
            elif tile_str == "up_stairs":
                row.append(UP_STAIRS_TILE)
            elif tile_str == "down_stairs":
                row.append(DOWN_STAIRS_TILE)
            else:
                row.append(FLOOR_TILE)  # fallback
        tiles.append(row)
    
    # Reconstruct stairs
    up_stairs = tuple(data["up_stairs"]) if data.get("up_stairs") else None
    down_stairs = tuple(data["down_stairs"]) if data.get("down_stairs") else None
    
    # Reconstruct explored/visible sets
    explored = {tuple(coord) for coord in data.get("explored", [])}
    visible = {tuple(coord) for coord in data.get("visible", [])}
    
    # Reconstruct entities (basic ones, enemies will be respawned)
    entities = []
    for entity_data in data.get("entities", []):
        entity_type = entity_data.get("type")
        # For now, we'll skip entity reconstruction as it's complex
        # Enemies will be respawned when the floor loads
        pass
    
    # Create GameMap
    game_map = GameMap(
        tiles=tiles,
        up_stairs=up_stairs,
        down_stairs=down_stairs,
        entities=entities,
        rooms=None,  # Rooms can be regenerated if needed
    )
    
    # Restore FOV state
    game_map.explored = explored
    game_map.visible = visible
    
    return game_map


def _deserialize_overworld(data: Dict[str, Any]):
    """Reconstruct OverworldMap from dict."""
    from world.overworld.map import OverworldMap
    from world.overworld.terrain import get_terrain, TERRAIN_GRASS
    
    # Reconstruct tiles
    tiles_data = data.get("tiles", [])
    tiles = []
    for row_data in tiles_data:
        row = []
        for terrain_id in row_data:
            terrain = get_terrain(terrain_id)
            if terrain is None:
                terrain = TERRAIN_GRASS
            row.append(terrain)
        tiles.append(row)
    
    # Create map
    overworld = OverworldMap(
        width=data.get("width", 512),
        height=data.get("height", 512),
        seed=data.get("seed"),
        tiles=tiles,
    )
    
    # Restore player position
    player_pos = data.get("player_position", [0, 0])
    overworld.set_player_position(player_pos[0], player_pos[1])
    
    # Restore explored tiles
    explored_list = data.get("explored_tiles", [])
    overworld.explored_tiles = {tuple(coord) for coord in explored_list}
    
    return overworld


def _deserialize_pois(overworld_map, pois_data: Dict[str, Any]) -> None:
    """Restore POIs to overworld map."""
    from world.poi.types import DungeonPOI, VillagePOI, TownPOI, CampPOI
    
    for poi_id, poi_data in pois_data.items():
        poi_type = poi_data.get("poi_type", "dungeon")
        position = tuple(poi_data.get("position", [0, 0]))
        level = poi_data.get("level", 1)
        name = poi_data.get("name")
        
        # Create appropriate POI type
        if poi_type == "dungeon":
            floor_count = poi_data.get("floor_count", 5)
            poi = DungeonPOI(poi_id, position, level, name, floor_count)
            cleared_floors = poi_data.get("cleared_floors", [])
            poi.cleared_floors = set(cleared_floors)
        elif poi_type == "village":
            poi = VillagePOI(poi_id, position, level, name)
        elif poi_type == "town":
            poi = TownPOI(poi_id, position, level, name)
        elif poi_type == "camp":
            poi = CampPOI(poi_id, position, level, name)
        else:
            # Default to dungeon
            poi = DungeonPOI(poi_id, position, level, name)
        
        # Restore state
        poi.discovered = poi_data.get("discovered", False)
        poi.cleared = poi_data.get("cleared", False)
        poi.state = poi_data.get("state", {})
        
        # Add to map
        overworld_map.add_poi(poi)

