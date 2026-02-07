"""
Territory Control System.

Manages faction territories on the overworld map. This is a modular system
that can be enabled/disabled without affecting core game functionality.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, TYPE_CHECKING
import math
import random

if TYPE_CHECKING:
    from .map import OverworldMap
    from ..factions.faction_manager import FactionManager
    from ..poi.base import PointOfInterest


@dataclass
class Territory:
    """
    Represents a territory controlled by a faction.
    
    Territories are chunk-based (groups of tiles) for performance.
    """
    territory_id: str
    faction_id: str
    chunk_x: int  # Chunk coordinates (not tile coordinates)
    chunk_y: int
    strength: float = 1.0  # 0.0 to 1.0, how strongly controlled
    last_update_time: float = 0.0  # Time when last updated (hours)
    border_tiles: Set[Tuple[int, int]] = field(default_factory=set)  # Border tile positions
    center_poi_id: Optional[str] = None  # POI that anchors this territory
    controlled_tiles: Set[Tuple[int, int]] = field(default_factory=set)  # All tiles in territory


class TerritoryManager:
    """
    Manages faction territories on the overworld map.
    
    This system is modular and optional - it can be disabled without
    affecting core game functionality.
    """
    
    def __init__(
        self,
        overworld_map: "OverworldMap",
        faction_manager: Optional["FactionManager"] = None,
        chunk_size: int = 8,
        enabled: bool = True,
    ):
        """
        Initialize territory manager.
        
        Args:
            overworld_map: The overworld map to manage territories for
            faction_manager: Faction manager (if None, tries to get from map)
            chunk_size: Size of territory chunks (default 8x8 tiles)
            enabled: Whether territory system is enabled
        """
        self.overworld_map = overworld_map
        self.chunk_size = chunk_size
        
        # Get faction manager
        if faction_manager is None:
            faction_manager = getattr(overworld_map, "faction_manager", None)
        self.faction_manager = faction_manager
        
        # Territory storage: (chunk_x, chunk_y) -> Territory
        self.territories: Dict[Tuple[int, int], Territory] = {}
        
        # Reverse lookup: tile (x, y) -> Territory
        self.tile_to_territory: Dict[Tuple[int, int], Territory] = {}
        
        # Border conflicts: (territory1_id, territory2_id) -> conflict_strength
        self.border_conflicts: Dict[Tuple[str, str], float] = {}
        
        # System state
        self.enabled = enabled
        self.initialized = False
        
        # Configuration
        self.update_interval_hours = 24.0  # Update territories every 24 hours
        self.border_conflict_threshold = -50  # Relation threshold for conflicts
        
    def add_territory_for_poi(self, poi: "PointOfInterest") -> None:
        """
        Add or update a territory for a specific POI.
        
        Useful when a POI is discovered or created.
        
        Args:
            poi: The POI to create/update territory for
        """
        if not self.enabled or not self.faction_manager:
            return
        
        # Get faction
        faction_id = getattr(poi, "faction_id", None)
        if faction_id is None:
            faction_id = self.faction_manager.get_faction_for_poi_type(poi.poi_type)
        
        if faction_id is None:
            faction_id = "neutral"
        
        # Get chunk coordinates
        chunk_x = poi.position[0] // self.chunk_size
        chunk_y = poi.position[1] // self.chunk_size
        
        # Check if territory already exists
        existing_territory = self.territories.get((chunk_x, chunk_y))
        if existing_territory:
            # Update existing territory
            existing_territory.faction_id = faction_id
            existing_territory.center_poi_id = poi.poi_id
            existing_territory.strength = 1.0
        else:
            # Create new territory
            territory_id = f"territory_{poi.poi_id}"
            territory = Territory(
                territory_id=territory_id,
                faction_id=faction_id,
                chunk_x=chunk_x,
                chunk_y=chunk_y,
                strength=1.0,
                center_poi_id=poi.poi_id,
            )
            
            # Calculate controlled tiles
            self._calculate_territory_tiles(territory, chunk_x, chunk_y)
            
            # Store territory
            self.territories[(chunk_x, chunk_y)] = territory
            
            # Update tile lookup
            for tile_pos in territory.controlled_tiles:
                self.tile_to_territory[tile_pos] = territory
        
        # Recalculate borders and conflicts
        self._calculate_borders()
        self._detect_border_conflicts()
    
    def initialize_from_pois(self) -> None:
        """
        Initialize territories from POI positions.
        
        Each POI creates a territory around it controlled by its faction.
        If a POI has no faction, it creates a neutral territory.
        """
        if not self.enabled:
            self.initialized = True  # Mark as initialized even if disabled
            return
        
        if not self.faction_manager:
            print("Warning: Cannot initialize territories - no faction manager")
            self.initialized = True  # Mark as initialized (system is ready, just no factions)
            return
        
        self.territories.clear()
        self.tile_to_territory.clear()
        
        # Calculate chunk dimensions
        chunks_x = (self.overworld_map.width + self.chunk_size - 1) // self.chunk_size
        chunks_y = (self.overworld_map.height + self.chunk_size - 1) // self.chunk_size
        
        # Create territories from ALL POIs (not just discovered ones)
        # This ensures territories exist even before discovery
        for poi in self.overworld_map.get_all_pois():
            
            faction_id = getattr(poi, "faction_id", None)
            if faction_id is None:
                # Try to get faction from faction manager based on POI type
                if self.faction_manager:
                    faction_id = self.faction_manager.get_faction_for_poi_type(poi.poi_type)
            
            # If still no faction, create neutral territory
            if faction_id is None:
                faction_id = "neutral"
            
            # Get chunk coordinates for POI position
            chunk_x = poi.position[0] // self.chunk_size
            chunk_y = poi.position[1] // self.chunk_size
            
            # Create territory
            territory_id = f"territory_{poi.poi_id}"
            territory = Territory(
                territory_id=territory_id,
                faction_id=faction_id,
                chunk_x=chunk_x,
                chunk_y=chunk_y,
                strength=1.0,
                center_poi_id=poi.poi_id,
            )
            
            # Calculate controlled tiles (chunk area around POI)
            self._calculate_territory_tiles(territory, chunk_x, chunk_y)
            
            # Store territory
            self.territories[(chunk_x, chunk_y)] = territory
            
            # Update tile lookup
            for tile_pos in territory.controlled_tiles:
                self.tile_to_territory[tile_pos] = territory
        
        # Calculate borders after all territories are created
        self._calculate_borders()
        
        # Detect border conflicts
        self._detect_border_conflicts()
        
        # Mark as initialized (even if no territories were created)
        self.initialized = True
    
    def _calculate_territory_tiles(
        self,
        territory: Territory,
        chunk_x: int,
        chunk_y: int,
    ) -> None:
        """Calculate which tiles belong to this territory."""
        start_x = chunk_x * self.chunk_size
        start_y = chunk_y * self.chunk_size
        end_x = min(start_x + self.chunk_size, self.overworld_map.width)
        end_y = min(start_y + self.chunk_size, self.overworld_map.height)
        
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                if self.overworld_map.in_bounds(x, y) and self.overworld_map.is_walkable(x, y):
                    territory.controlled_tiles.add((x, y))
    
    def _calculate_borders(self) -> None:
        """Calculate border tiles for each territory."""
        for territory in self.territories.values():
            territory.border_tiles.clear()
            
            for tile_x, tile_y in territory.controlled_tiles:
                # Check if this tile is on a border (has neighbor in different territory)
                is_border = False
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    neighbor_x = tile_x + dx
                    neighbor_y = tile_y + dy
                    
                    if not self.overworld_map.in_bounds(neighbor_x, neighbor_y):
                        is_border = True
                        break
                    
                    neighbor_territory = self.tile_to_territory.get((neighbor_x, neighbor_y))
                    if neighbor_territory is None or neighbor_territory.territory_id != territory.territory_id:
                        is_border = True
                        break
                
                if is_border:
                    territory.border_tiles.add((tile_x, tile_y))
    
    def _detect_border_conflicts(self) -> None:
        """Detect conflicts between adjacent territories of hostile factions."""
        if not self.faction_manager:
            return
        
        self.border_conflicts.clear()
        
        territories_list = list(self.territories.values())
        
        for i, territory1 in enumerate(territories_list):
            for territory2 in territories_list[i + 1:]:
                # Check if territories are adjacent
                if not self._are_territories_adjacent(territory1, territory2):
                    continue
                
                # Check faction relations
                relation = self.faction_manager.get_relation(
                    territory1.faction_id,
                    territory2.faction_id,
                )
                
                # If hostile (relation <= threshold), mark as conflict
                if relation <= self.border_conflict_threshold:
                    conflict_key = (
                        min(territory1.territory_id, territory2.territory_id),
                        max(territory1.territory_id, territory2.territory_id),
                    )
                    # Conflict strength based on how hostile (more negative = stronger conflict)
                    conflict_strength = abs(relation) / 100.0
                    self.border_conflicts[conflict_key] = conflict_strength
    
    def _are_territories_adjacent(self, territory1: Territory, territory2: Territory) -> bool:
        """Check if two territories are adjacent (share border tiles)."""
        # Check if any border tiles are adjacent
        for tile1 in territory1.border_tiles:
            for tile2 in territory2.border_tiles:
                dx = abs(tile1[0] - tile2[0])
                dy = abs(tile1[1] - tile2[1])
                if (dx == 1 and dy == 0) or (dx == 0 and dy == 1):
                    return True
        return False
    
    def get_territory_at(self, x: int, y: int) -> Optional[Territory]:
        """
        Get the territory at the given tile coordinates.
        
        Args:
            x: Tile X coordinate
            y: Tile Y coordinate
            
        Returns:
            Territory at that position, or None if no territory
        """
        if not self.enabled or not self.initialized:
            return None
        
        return self.tile_to_territory.get((x, y))
    
    def get_faction_at(self, x: int, y: int) -> Optional[str]:
        """
        Get the faction controlling the territory at the given coordinates.
        
        Args:
            x: Tile X coordinate
            y: Tile Y coordinate
            
        Returns:
            Faction ID, or None if no territory
        """
        territory = self.get_territory_at(x, y)
        if territory:
            return territory.faction_id
        return None
    
    def has_border_conflict(self, territory1: Territory, territory2: Territory) -> bool:
        """Check if two territories have a border conflict."""
        if not self.enabled:
            return False
        
        conflict_key = (
            min(territory1.territory_id, territory2.territory_id),
            max(territory1.territory_id, territory2.territory_id),
        )
        return conflict_key in self.border_conflicts
    
    def get_conflict_strength(self, territory1: Territory, territory2: Territory) -> float:
        """Get the conflict strength between two territories (0.0 to 1.0)."""
        if not self.enabled:
            return 0.0
        
        conflict_key = (
            min(territory1.territory_id, territory2.territory_id),
            max(territory1.territory_id, territory2.territory_id),
        )
        return self.border_conflicts.get(conflict_key, 0.0)
    
    def update_territories(self, current_time: float) -> None:
        """
        Update territories based on time and game state.
        
        This can expand/contract territories, resolve conflicts, etc.
        
        Args:
            current_time: Current game time in hours
        """
        if not self.enabled or not self.initialized:
            return
        
        # Only update if enough time has passed
        for territory in self.territories.values():
            time_since_update = current_time - territory.last_update_time
            if time_since_update < self.update_interval_hours:
                continue
            
            # Update territory strength (can decay over time if no POI support)
            if territory.center_poi_id:
                # Territory with POI maintains strength
                territory.strength = min(1.0, territory.strength + 0.1)
            else:
                # Territory without POI slowly decays
                territory.strength = max(0.0, territory.strength - 0.05)
            
            territory.last_update_time = current_time
        
        # Recalculate borders and conflicts periodically
        if random.random() < 0.1:  # 10% chance per update
            self._calculate_borders()
            self._detect_border_conflicts()
    
    def expand_territory(self, territory: Territory, direction: Tuple[int, int]) -> bool:
        """
        Attempt to expand a territory in a given direction.
        
        Args:
            territory: Territory to expand
            direction: (dx, dy) direction to expand
            
        Returns:
            True if expansion was successful, False otherwise
        """
        if not self.enabled:
            return False
        
        # TODO: Implement territory expansion logic
        # This would check adjacent chunks, handle conflicts, etc.
        return False
    
    def get_all_territories(self) -> List[Territory]:
        """Get all territories."""
        return list(self.territories.values())
    
    def get_territories_for_faction(self, faction_id: str) -> List[Territory]:
        """Get all territories controlled by a faction."""
        return [
            t for t in self.territories.values()
            if t.faction_id == faction_id
        ]
    
    def get_territories_in_viewport(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
    ) -> List[Territory]:
        """
        Get territories that intersect with the given viewport.
        
        Uses chunk-based quick filtering for performance.
        
        Args:
            start_x, start_y: Viewport start (tile coordinates)
            end_x, end_y: Viewport end (tile coordinates)
            
        Returns:
            List of territories that might be visible in viewport
        """
        if not self.enabled or not self.initialized:
            return []
        
        # Add small margin for border tiles
        margin = 2
        viewport_min_x = start_x - margin
        viewport_max_x = end_x + margin
        viewport_min_y = start_y - margin
        viewport_max_y = end_y + margin
        
        visible = []
        for territory in self.territories.values():
            # Quick chunk-based intersection check
            chunk_min_x = territory.chunk_x * self.chunk_size
            chunk_max_x = chunk_min_x + self.chunk_size
            chunk_min_y = territory.chunk_y * self.chunk_size
            chunk_max_y = chunk_min_y + self.chunk_size
            
            # Check if chunk overlaps viewport
            if (chunk_max_x >= viewport_min_x and chunk_min_x <= viewport_max_x and
                chunk_max_y >= viewport_min_y and chunk_min_y <= viewport_max_y):
                visible.append(territory)
        
        return visible

