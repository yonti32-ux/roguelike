"""
Village building definitions and placement.
"""

from dataclasses import dataclass
from typing import Optional, List, Tuple
import random


@dataclass
class Building:
    """Base building class."""
    building_type: str  # "shop", "inn", "tavern", "house"
    x: int  # Top-left tile x
    y: int  # Top-left tile y
    width: int  # Width in tiles
    height: int  # Height in tiles
    npc_id: Optional[str] = None  # ID of NPC in this building
    entrance_x: Optional[int] = None  # Entrance tile x coordinate
    entrance_y: Optional[int] = None  # Entrance tile y coordinate
    
    @property
    def x2(self) -> int:
        """Right edge (exclusive)."""
        return self.x + self.width
    
    @property
    def y2(self) -> int:
        """Bottom edge (exclusive)."""
        return self.y + self.height
    
    def center(self) -> Tuple[int, int]:
        """Get center tile coordinates."""
        return (self.x + self.width // 2, self.y + self.height // 2)
    
    def intersects(self, other: "Building") -> bool:
        """Check if this building intersects with another."""
        return (
            self.x < other.x2
            and self.x2 > other.x
            and self.y < other.y2
            and self.y2 > other.y
        )
    
    def contains_tile(self, tx: int, ty: int) -> bool:
        """Check if a tile is inside this building."""
        return self.x <= tx < self.x2 and self.y <= ty < self.y2


@dataclass
class ShopBuilding(Building):
    """Shop building containing a merchant."""
    def __init__(self, x: int, y: int, width: int = 8, height: int = 8, npc_id: Optional[str] = None):
        super().__init__("shop", x, y, width, height, npc_id)


@dataclass
class InnBuilding(Building):
    """Inn building containing an innkeeper."""
    def __init__(self, x: int, y: int, width: int = 8, height: int = 8, npc_id: Optional[str] = None):
        super().__init__("inn", x, y, width, height, npc_id)


@dataclass
class TavernBuilding(Building):
    """Tavern/Guild Hall building containing a recruiter."""
    def __init__(self, x: int, y: int, width: int = 10, height: int = 10, npc_id: Optional[str] = None):
        super().__init__("tavern", x, y, width, height, npc_id)


@dataclass
class HouseBuilding(Building):
    """Decorative house building."""
    def __init__(self, x: int, y: int, width: int = 7, height: int = 7, npc_id: Optional[str] = None):
        super().__init__("house", x, y, width, height, npc_id)


@dataclass
class TownHallBuilding(Building):
    """Town hall building containing the village elder."""
    def __init__(self, x: int, y: int, width: int = 10, height: int = 10, npc_id: Optional[str] = None):
        super().__init__("town_hall", x, y, width, height, npc_id)


def place_buildings(
    map_width: int,
    map_height: int,
    level: int,
    seed: Optional[int] = None,
) -> List[Building]:
    """
    Place buildings around the village perimeter.
    
    Args:
        map_width: Map width in tiles
        map_height: Map height in tiles
        level: Village level (affects building count)
        seed: Random seed for deterministic generation
        
    Returns:
        List of placed buildings
    """
    if seed is not None:
        random.seed(seed)
    
    buildings: List[Building] = []
    
    # Determine building count based on level
    # Adjusted for larger villages - more buildings to fill the space
    # Small village (1-3): 4-6 buildings
    # Medium village (4-7): 6-9 buildings
    # Large village (8+): 9-12 buildings
    if level <= 3:
        min_buildings = 4
        max_buildings = 6
    elif level <= 7:
        min_buildings = 6
        max_buildings = 9
    else:
        min_buildings = 9
        max_buildings = 12
    
    num_buildings = random.randint(min_buildings, max_buildings)
    
    # Ensure we have at least one of each essential building
    # Town hall is essential (contains elder for quests)
    essential_buildings = ["town_hall", "shop", "inn", "tavern"]
    building_types = essential_buildings.copy()
    
    # Add houses for remaining slots
    remaining = num_buildings - len(essential_buildings)
    building_types.extend(["house"] * max(0, remaining))
    
    # Shuffle to randomize placement order
    random.shuffle(building_types)
    
    # Place buildings around perimeter
    # Leave a border for paths (at least 2 tiles from edge)
    border = 2
    inner_x = border
    inner_y = border
    inner_width = map_width - 2 * border
    inner_height = map_height - 2 * border
    
    max_attempts = 200
    attempts = 0
    
    for building_type in building_types:
        if attempts >= max_attempts:
            break
        
        # Determine building size based on type (increased sizes for better visibility)
        if building_type == "town_hall":
            w, h = 10, 10  # Larger, important building for elder
            building_class = TownHallBuilding
        elif building_type == "shop":
            w, h = 8, 8  # Increased from 5x5
            building_class = ShopBuilding
        elif building_type == "inn":
            w, h = 8, 8  # Increased from 5x5
            building_class = InnBuilding
        elif building_type == "tavern":
            w, h = 10, 10  # Increased from 6x6 (larger since it's important)
            building_class = TavernBuilding
        else:  # house
            w, h = 7, 7  # Increased from 4x4
            building_class = HouseBuilding
        
        # Try to place building
        placed = False
        for _ in range(50):  # Try up to 50 positions
            attempts += 1
            if attempts >= max_attempts:
                break
            
            # Try placing on perimeter (prefer edges)
            side = random.choice(["top", "bottom", "left", "right"])
            
            if side == "top":
                x = random.randint(inner_x, inner_x + inner_width - w)
                y = inner_y
            elif side == "bottom":
                x = random.randint(inner_x, inner_x + inner_width - w)
                y = inner_y + inner_height - h
            elif side == "left":
                x = inner_x
                y = random.randint(inner_y, inner_y + inner_height - h)
            else:  # right
                x = inner_x + inner_width - w
                y = random.randint(inner_y, inner_y + inner_height - h)
            
            # Check bounds
            if x < 0 or y < 0 or x + w >= map_width or y + h >= map_height:
                continue
            
            # Create building
            new_building = building_class(x, y, w, h)
            
            # Check for intersections
            if any(new_building.intersects(existing) for existing in buildings):
                continue
            
            # Valid placement
            buildings.append(new_building)
            placed = True
            break
        
        if not placed:
            # Couldn't place this building, skip it
            continue
    
    return buildings

