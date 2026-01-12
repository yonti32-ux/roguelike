"""
POI type implementations.

Specific POI types: Dungeons, Villages, Towns, Camps, etc.

All POI types are automatically registered with the global registry on import.
"""

from typing import Set, Optional, Dict, Any, List, TYPE_CHECKING
from .base import PointOfInterest
from .registry import register_poi_type

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
        faction_id: Optional[str] = None,
    ) -> None:
        """
        Initialize a dungeon POI.
        
        Args:
            poi_id: Unique identifier
            position: Overworld tile position
            level: Difficulty level
            name: Display name
            floor_count: Number of floors in this dungeon
            faction_id: Optional faction that controls this POI
        """
        super().__init__(poi_id, "dungeon", position, level, name, faction_id=faction_id)
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
    
    def serialize_state(self) -> Dict[str, Any]:
        """Serialize dungeon-specific state."""
        return {
            "floor_count": self.floor_count,
            "cleared_floors": list(self.cleared_floors),
        }
    
    def deserialize_state(self, data: Dict[str, Any]) -> None:
        """Deserialize dungeon-specific state."""
        if "floor_count" in data:
            self.floor_count = data["floor_count"]
        if "cleared_floors" in data:
            self.cleared_floors = set(data["cleared_floors"])
    
    def get_tooltip_lines(self, game: Optional["Game"] = None) -> List[str]:
        """Get dungeon-specific tooltip lines."""
        lines = []
        floors_cleared = len(self.cleared_floors)
        
        lines.append(f"Floors: {self.floor_count}")
        
        if self.cleared:
            lines.append(f"Progress: {self.floor_count}/{self.floor_count} floors cleared (100%)")
        else:
            lines.append(f"Progress: {floors_cleared}/{self.floor_count} floors")
            if self.floor_count > 0:
                progress_pct = int((floors_cleared / self.floor_count) * 100)
                lines.append(f"Completion: {progress_pct}%")
        
        if game is not None:
            # Calculate difficulty estimation
            hero_level = getattr(game.hero_stats, "level", 1) if hasattr(game, "hero_stats") else 1
            party = getattr(game, "party", []) if hasattr(game, "party") else []
            companion_levels = [comp.level for comp in party if hasattr(comp, "level")]
            total_level = hero_level + sum(companion_levels)
            total_count = 1 + len(companion_levels)
            party_level = total_level / total_count if total_count > 0 else 1.0
            
            level_diff = self.level - party_level
            if level_diff <= -3:
                difficulty = "Very Easy"
            elif level_diff <= -2:
                difficulty = "Easy"
            elif level_diff <= -1:
                difficulty = "Fairly Easy"
            elif level_diff <= 0:
                difficulty = "Appropriate"
            elif level_diff <= 1:
                difficulty = "Challenging"
            elif level_diff <= 2:
                difficulty = "Hard"
            elif level_diff <= 3:
                difficulty = "Very Hard"
            else:
                difficulty = "Extreme"
            
            lines.append(f"Difficulty: {difficulty} (Party Lv: {party_level:.1f})")
        
        return lines


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
        faction_id: Optional[str] = None,
    ) -> None:
        super().__init__(poi_id, "village", position, level, name, faction_id=faction_id)
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
    
    def get_tooltip_lines(self, game: Optional["Game"] = None) -> List[str]:
        """Get village-specific tooltip lines."""
        lines = []
        if hasattr(self, "buildings") and self.buildings:
            building_list = ", ".join(b.title() for b in self.buildings[:3])
            if len(self.buildings) > 3:
                building_list += "..."
            lines.append(f"Services: {building_list}")
        return lines
    
    def get_display_label(self) -> str:
        """Get display label for village."""
        return "Village"


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
        faction_id: Optional[str] = None,
    ) -> None:
        super().__init__(poi_id, "town", position, level, name, faction_id=faction_id)
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
    
    def get_tooltip_lines(self, game: Optional["Game"] = None) -> List[str]:
        """Get town-specific tooltip lines."""
        lines = []
        if hasattr(self, "buildings") and self.buildings:
            building_list = ", ".join(b.title() for b in self.buildings[:3])
            if len(self.buildings) > 3:
                building_list += "..."
            lines.append(f"Services: {building_list}")
        return lines
    
    def get_display_label(self) -> str:
        """Get display label for town."""
        return "Town"


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
        faction_id: Optional[str] = None,
    ) -> None:
        super().__init__(poi_id, "camp", position, level, name, faction_id=faction_id)
    
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
    
    def get_display_label(self) -> str:
        """Get display label for camp."""
        return "Camp"


# -----------------------------------------------------------------------------
# Register all POI types with the global registry
# -----------------------------------------------------------------------------

def _register_poi_types() -> None:
    """Register all POI types with the global registry."""
    
    # Register DungeonPOI with custom factory (needs floor_count)
    def create_dungeon(poi_id: str, position: tuple, level: int = 1, name: Optional[str] = None, **kwargs):
        floor_count = kwargs.pop("floor_count", 5)  # Default floor count
        return DungeonPOI(poi_id, position, level=level, name=name, floor_count=floor_count)
    
    register_poi_type("dungeon", factory=create_dungeon, poi_class=DungeonPOI)
    register_poi_type("village", poi_class=VillagePOI)
    register_poi_type("town", poi_class=TownPOI)
    register_poi_type("camp", poi_class=CampPOI)


# Auto-register on import
_register_poi_types()

