"""
Floor management system.

Handles floor generation, caching, and floor state management.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Dict, Tuple

from world.mapgen import generate_floor
from world.game_map import GameMap

if TYPE_CHECKING:
    pass


class FloorManager:
    """
    Manages dungeon floors: generation, caching, and state.
    
    Responsibilities:
    - Generate floors on demand
    - Cache generated floors for reuse
    - Track current floor number
    - Provide floor lookup functionality
    """
    
    def __init__(self, starting_floor: int = 1) -> None:
        """
        Initialize the floor manager.
        
        Args:
            starting_floor: The initial floor number (default: 1)
        """
        self.floor: int = starting_floor
        self.floors: Dict[int, GameMap] = {}  # Cache of generated floors
        self._awaiting_floor_start: bool = True
    
    @property
    def awaiting_floor_start(self) -> bool:
        """Whether we're waiting for the player to make the first move on a floor."""
        return self._awaiting_floor_start
    
    @awaiting_floor_start.setter
    def awaiting_floor_start(self, value: bool) -> None:
        """Set whether we're awaiting floor start."""
        self._awaiting_floor_start = value
    
    def get_or_generate_floor(self, floor_index: int) -> Tuple[GameMap, bool]:
        """
        Get a floor from cache or generate it if it doesn't exist.
        
        Args:
            floor_index: The floor number to get or generate
        
        Returns:
            Tuple of (GameMap, is_newly_created)
        """
        # Try to reuse an existing GameMap instance for this floor
        game_map = self.floors.get(floor_index)
        newly_created = False
        
        if game_map is None:
            # Generate raw tiles + stair positions + high-level rooms
            tiles, up_tx, up_ty, down_tx, down_ty, rooms = generate_floor(floor_index)
            
            # Wrap them in a GameMap object
            game_map = GameMap(
                tiles,
                up_stairs=(up_tx, up_ty),
                down_stairs=(down_tx, down_ty),
                entities=None,
                rooms=rooms,
            )
            self.floors[floor_index] = game_map
            newly_created = True
        
        return game_map, newly_created
    
    def get_floor(self, floor_index: int) -> Optional[GameMap]:
        """
        Get a floor from cache if it exists.
        
        Args:
            floor_index: The floor number to get
        
        Returns:
            GameMap if found, None otherwise
        """
        return self.floors.get(floor_index)
    
    def has_floor(self, floor_index: int) -> bool:
        """Check if a floor has been generated and cached."""
        return floor_index in self.floors
    
    def calculate_spawn_position(
        self,
        game_map: GameMap,
        from_direction: Optional[str],
        player_width: int,
        player_height: int,
    ) -> Tuple[int, int]:
        """
        Calculate where the player should spawn on a floor.
        
        Args:
            game_map: The GameMap to spawn on
            from_direction: "down" (from floor above), "up" (from floor below), or None (starting)
            player_width: Player sprite width
            player_height: Player sprite height
        
        Returns:
            Tuple of (spawn_x, spawn_y) in world coordinates
        """
        # Decide spawn position based on stair direction
        if from_direction == "down" and game_map.up_stairs is not None:
            spawn_x, spawn_y = game_map.center_entity_on_tile(
                game_map.up_stairs[0],
                game_map.up_stairs[1],
                player_width,
                player_height,
            )
        elif from_direction == "up" and game_map.down_stairs is not None:
            spawn_x, spawn_y = game_map.center_entity_on_tile(
                game_map.down_stairs[0],
                game_map.down_stairs[1],
                player_width,
                player_height,
            )
        else:
            # Starting game or fallback: up stairs if they exist, else center
            if game_map.up_stairs is not None:
                spawn_x, spawn_y = game_map.center_entity_on_tile(
                    game_map.up_stairs[0],
                    game_map.up_stairs[1],
                    player_width,
                    player_height,
                )
            else:
                center_tx = game_map.width // 2
                center_ty = game_map.height // 2
                spawn_x, spawn_y = game_map.center_entity_on_tile(
                    center_tx,
                    center_ty,
                    player_width,
                    player_height,
                )
        
        return spawn_x, spawn_y
    
    def change_floor(self, delta: int) -> int:
        """
        Calculate new floor number after a floor change.
        
        Args:
            delta: Change in floor number (+1 for down, -1 for up)
        
        Returns:
            New floor number (0 or negative means invalid)
        """
        new_floor = self.floor + delta
        return new_floor if new_floor > 0 else 0

