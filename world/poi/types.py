"""
POI type implementations.

Specific POI types: Dungeons, Villages, Towns, Camps, etc.
"""

from typing import Set, Optional, TYPE_CHECKING
from .base import PointOfInterest

if TYPE_CHECKING:
    from engine.core.game import Game


class DungeonPOI(PointOfInterest):
    """
    Dungeon POI - leads to floor-based exploration.
    
    When entered, transitions to the existing exploration/combat system.
    """
    
    def __init__(
        self,
        poi_id: str,
        position: tuple[int, int],
        level: int = 1,
        name: Optional[str] = None,
        floor_count: int = 5,
    ) -> None:
        """
        Initialize a dungeon POI.
        
        Args:
            poi_id: Unique identifier
            position: Overworld tile position
            level: Difficulty level
            name: Display name
            floor_count: Number of floors in this dungeon
        """
        super().__init__(poi_id, "dungeon", position, level, name)
        self.floor_count = floor_count
        self.cleared_floors: Set[int] = set()
        
        # Store starting floor for this dungeon
        # When entering, we'll start at floor 1 (or continue from cleared)
        if "starting_floor" not in self.state:
            self.state["starting_floor"] = 1
    
    def enter(self, game: "Game") -> None:
        """
        Enter the dungeon. Transitions to exploration mode.
        
        This will use the existing floor system, but we need to:
        1. Set the current POI reference
        2. Switch to exploration mode
        3. Load the first floor (or continue from where we left off)
        """
        # Store reference to this POI
        game.current_poi = self
        
        # Determine which floor to load
        # For now, start at floor 1, or continue from highest cleared floor + 1
        if self.cleared_floors:
            next_floor = max(self.cleared_floors) + 1
            if next_floor > self.floor_count:
                # All floors cleared
                game.add_message(f"{self.name} has been fully explored! All {self.floor_count} floors are cleared.")
                return
        else:
            next_floor = 1
        
        # Set the floor index
        # Note: We'll need to adjust how floors work - they should be
        # relative to this dungeon, not global
        game.floor = next_floor
        
        # Load the floor (this will use existing load_floor logic)
        game.load_floor(game.floor, from_direction=None)
        
        # Switch to exploration mode
        game.enter_exploration_mode()
        
        # Better entry message with more detail
        floors_cleared = len(self.cleared_floors)
        if floors_cleared > 0:
            game.add_message(f"You enter {self.name} (Level {self.level}). Continuing from floor {next_floor}/{self.floor_count}...")
        else:
            game.add_message(f"You enter {self.name} (Level {self.level}). This dungeon has {self.floor_count} floors. Starting at floor 1...")
    
    def exit(self, game: "Game") -> None:
        """Exit the dungeon and return to overworld."""
        if game.current_poi is self:
            floors_cleared = len(self.cleared_floors)
            progress = f"{floors_cleared}/{self.floor_count} floors" if self.floor_count > 0 else "explored"
            game.current_poi = None
            game.enter_overworld_mode()
            game.add_message(f"You exit {self.name}. Progress: {progress} cleared.")
    
    def mark_floor_cleared(self, floor: int) -> None:
        """Mark a floor as cleared."""
        self.cleared_floors.add(floor)
        
        # If all floors cleared, mark POI as cleared
        if len(self.cleared_floors) >= self.floor_count:
            self.cleared = True
    
    def get_description(self) -> str:
        """Get description including floor progress."""
        if self.cleared:
            return f"{self.name} (Level {self.level}, Cleared - {self.floor_count} floors)"
        floors_cleared = len(self.cleared_floors)
        return f"{self.name} (Level {self.level}, {floors_cleared}/{self.floor_count} floors)"


class VillagePOI(PointOfInterest):
    """
    Village POI - safe zone with shops, healing, etc.
    
    For Phase 1, this is a placeholder. Will be expanded later.
    """
    
    def __init__(
        self,
        poi_id: str,
        position: tuple[int, int],
        level: int = 1,
        name: Optional[str] = None,
    ) -> None:
        super().__init__(poi_id, "village", position, level, name)
        self.buildings: list[str] = ["shop", "inn"]
        self.merchants: list[str] = ["general_merchant"]
    
    def enter(self, game: "Game") -> None:
        """Enter the village and load village map."""
        game.current_poi = self
        
        # Generate village map if not already generated
        if "village_map" not in self.state:
            from world.village import generate_village
            # Use POI position as seed for deterministic generation
            seed = hash((self.poi_id, self.position[0], self.position[1]))
            village_map = generate_village(self.level, self.name, seed=seed)
            self.state["village_map"] = village_map
            
            # Generate available companions on first visit
            # Scale companion level with player level, not village level
            from systems.village.companion_generation import generate_village_companions
            player_level = getattr(game.hero_stats, "level", 1) if game.hero_stats else 1
            companion_count = min(3, max(1, player_level // 2 + 1))  # 1-3 companions based on player level
            companions = generate_village_companions(
                village_level=player_level,  # Use player level instead of village level
                count=companion_count,
                seed=seed + 10000,  # Different seed for companions
            )
            self.state["available_companions"] = companions
        else:
            village_map = self.state["village_map"]
        
        # Load the village map
        game.current_map = village_map
        
        # Ensure player exists (create if needed, e.g., when entering from overworld)
        if game.player is None:
            from world.entities import Player
            from settings import TILE_SIZE
            # Create player at a default position (will be moved to entrance)
            game.player = Player(
                x=0.0,
                y=0.0,
                width=24,
                height=24,
            )
            # Apply hero stats to the newly created player
            from engine.managers.hero_manager import apply_hero_stats_to_player
            apply_hero_stats_to_player(game, full_heal=True)
        
        # Place player at entrance
        entrance_pos = getattr(village_map, "village_entrance", None)
        if entrance_pos is not None:
            entrance_x, entrance_y = entrance_pos
            # Use GameMap's center_entity_on_tile to properly position player
            player_width = game.player.width
            player_height = game.player.height
            world_x, world_y = village_map.center_entity_on_tile(
                entrance_x,
                entrance_y,
                player_width,
                player_height,
            )
            game.player.move_to(world_x, world_y)
        
        # Update camera to follow player
        game.camera_x = game.player.x
        game.camera_y = game.player.y
        
        # Initialize FOV for the village
        if hasattr(game, "update_fov"):
            game.update_fov()
        
        # Switch to exploration mode
        game.enter_exploration_mode()
        
        # Better entry message with more detail
        buildings = ", ".join(b.title() for b in self.buildings[:2]) if self.buildings else "basic services"
        game.add_message(f"You enter {self.name} (Level {self.level}). A peaceful village with {buildings}.")
    
    def exit(self, game: "Game") -> None:
        """Exit the village."""
        if game.current_poi is self:
            game.current_poi = None
            game.enter_overworld_mode()
            game.add_message(f"You leave {self.name} and return to the overworld.")


class TownPOI(PointOfInterest):
    """
    Town POI - larger than village, more services.
    
    For Phase 1, this is a placeholder.
    """
    
    def __init__(
        self,
        poi_id: str,
        position: tuple[int, int],
        level: int = 1,
        name: Optional[str] = None,
    ) -> None:
        super().__init__(poi_id, "town", position, level, name)
        self.buildings: list[str] = ["shop", "inn", "blacksmith", "library"]
        self.merchants: list[str] = ["general_merchant", "weapon_merchant", "armor_merchant"]
    
    def enter(self, game: "Game") -> None:
        """Enter the town."""
        game.current_poi = self
        game.enter_exploration_mode()
        # TODO: Load town map/interior
        buildings = ", ".join(b.title() for b in self.buildings[:3]) if self.buildings else "many services"
        game.add_message(f"You enter {self.name} (Level {self.level}). A bustling town with {buildings}.")
    
    def exit(self, game: "Game") -> None:
        """Exit the town."""
        if game.current_poi is self:
            game.current_poi = None
            game.enter_overworld_mode()
            game.add_message(f"You leave {self.name} and return to the overworld.")


class CampPOI(PointOfInterest):
    """
    Camp POI - temporary safe spot with basic rest/healing.
    
    For Phase 1, this is a placeholder.
    """
    
    def __init__(
        self,
        poi_id: str,
        position: tuple[int, int],
        level: int = 1,
        name: Optional[str] = None,
    ) -> None:
        super().__init__(poi_id, "camp", position, level, name)
    
    def enter(self, game: "Game") -> None:
        """Enter the camp."""
        game.current_poi = self
        game.enter_exploration_mode()
        # TODO: Load camp map/interior
        game.add_message(f"You enter {self.name} (Level {self.level}). A small, temporary camp.")
    
    def exit(self, game: "Game") -> None:
        """Exit the camp."""
        if game.current_poi is self:
            game.current_poi = None
            game.enter_overworld_mode()
            game.add_message(f"You leave {self.name} and return to the overworld.")

