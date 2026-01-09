"""
Base Point of Interest (POI) class.

All POI types inherit from this base class.
"""

from typing import Dict, Any, Tuple, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from engine.core.game import Game


class PointOfInterest:
    """
    Base class for all Points of Interest.
    
    POIs are locations on the overworld that the player can enter,
    such as dungeons, villages, towns, etc.
    """
    
    def __init__(
        self,
        poi_id: str,
        poi_type: str,
        position: Tuple[int, int],
        level: int = 1,
        name: Optional[str] = None,
    ) -> None:
        """
        Initialize a POI.
        
        Args:
            poi_id: Unique identifier for this POI
            poi_type: Type of POI ("dungeon", "village", etc.)
            position: Overworld tile position (x, y)
            level: Difficulty/level rating
            name: Display name (if None, generates from type)
        """
        self.poi_id = poi_id
        self.poi_type = poi_type
        self.position = position
        self.level = level
        self.name = name or f"{poi_type.title()} {poi_id.split('_')[-1]}"
        
        # State
        self.discovered: bool = False
        self.cleared: bool = False
        self.state: Dict[str, Any] = {}
    
    def can_enter(self, game: "Game") -> bool:
        """
        Check if the player can enter this POI.
        
        Args:
            game: Game instance
            
        Returns:
            True if player can enter, False otherwise
        """
        # Base implementation: can always enter if discovered
        return self.discovered
    
    def enter(self, game: "Game") -> None:
        """
        Enter this POI. Transitions game to exploration mode.
        
        Args:
            game: Game instance
        """
        # Base implementation does nothing
        # Subclasses override this
        pass
    
    def exit(self, game: "Game") -> None:
        """
        Exit this POI. Returns to overworld.
        
        Args:
            game: Game instance
        """
        # Base implementation does nothing
        # Subclasses override this
        pass
    
    def get_description(self) -> str:
        """Get a description of this POI."""
        status = "Cleared" if self.cleared else "Active"
        return f"{self.name} (Level {self.level}, {status})"
    
    def discover(self) -> None:
        """Mark this POI as discovered."""
        self.discovered = True
    
    def clear(self) -> None:
        """Mark this POI as cleared/completed."""
        self.cleared = True
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.poi_id}, pos={self.position}, level={self.level})>"

