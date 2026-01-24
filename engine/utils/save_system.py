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

    return {
        "version": "1.0",  # Save format version
        "floor": current_floor_num,
        "hero_stats": hero_stats_dict,
        "inventory": inventory_dict,
        "party": party_list,
        "floors": floors_dict,
        "player": player_data,
        "message_log": message_log_data,
        "camera": camera_data,
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
        "skill_loadouts": hero_stats.skill_loadouts,
        "current_loadout": hero_stats.current_loadout,
        "max_skill_slots": hero_stats.max_skill_slots,
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
        "skill_loadouts": getattr(companion, "skill_loadouts", {}),
        "current_loadout": getattr(companion, "current_loadout", "default"),
        "max_skill_slots": getattr(companion, "max_skill_slots", 4),
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
    hero_stats.skill_loadouts = dict(data.get("skill_loadouts", {}))
    hero_stats.current_loadout = data.get("current_loadout", "default")
    hero_stats.max_skill_slots = int(data.get("max_skill_slots", 4))
    # Ensure default loadout exists
    hero_stats._ensure_default_loadout()
    
    # Migrate skills from skill_slots to default loadout if loadout is empty
    # This handles old saves that don't have loadouts yet
    if "default" in hero_stats.skill_loadouts:
        default_loadout = hero_stats.skill_loadouts["default"]
        # If default loadout is empty but skill_slots has skills, migrate them
        if not any(default_loadout) and any(hero_stats.skill_slots):
            for i, skill_id in enumerate(hero_stats.skill_slots):
                if i < len(default_loadout) and skill_id:
                    default_loadout[i] = skill_id
    
    # Auto-assign all unlocked skills to default loadout if it's still mostly empty
    # This ensures new skills from perks get added automatically
    default_loadout = hero_stats.skill_loadouts.get("default", [])
    if default_loadout.count(None) >= len(default_loadout) // 2:  # If more than half empty
        hero_stats.auto_assign_all_unlocked_skills_to_default_loadout()
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
        skill_loadouts=dict(data.get("skill_loadouts", {})),
        current_loadout=data.get("current_loadout", "default"),
        max_skill_slots=int(data.get("max_skill_slots", 4)),
        skill_points=data.get("skill_points", 0),
        skill_ranks=dict(data.get("skill_ranks", {})),
    )
    # Ensure default loadout exists for backward compatibility
    companion._ensure_default_loadout()
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

