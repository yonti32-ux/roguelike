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
        """Enter the village."""
        game.current_poi = self
        game.enter_exploration_mode()
        # TODO: Load village map/interior
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

