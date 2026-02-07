"""
Town building definitions and placement.

Towns have more building types than villages: blacksmiths, libraries,
markets, guild halls, etc.
"""

from dataclasses import dataclass
from typing import Optional, List, Tuple
import random


@dataclass
class Building:
    """Base building class."""
    building_type: str  # "shop", "inn", "blacksmith", "library", etc.
    x: int  # Top-left tile x
    y: int  # Top-left tile y
    width: int  # Width in tiles
    height: int  # Height in tiles
    npc_id: Optional[str] = None  # ID of NPC in this building
    entrance_x: Optional[int] = None  # Entrance tile x coordinate
    entrance_y: Optional[int] = None  # Entrance tile y coordinate
    material: str = "stone"  # "stone" or "wood" - affects tile appearance
    
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
    """General shop building."""
    def __init__(self, x: int, y: int, width: int = 10, height: int = 10, npc_id: Optional[str] = None):
        super().__init__("shop", x, y, width, height, npc_id, material="stone")


@dataclass
class InnBuilding(Building):
    """Inn building containing an innkeeper."""
    def __init__(self, x: int, y: int, width: int = 10, height: int = 10, npc_id: Optional[str] = None):
        super().__init__("inn", x, y, width, height, npc_id, material="wood")


@dataclass
class TavernBuilding(Building):
    """Tavern/Guild Hall building."""
    def __init__(self, x: int, y: int, width: int = 12, height: int = 12, npc_id: Optional[str] = None):
        super().__init__("tavern", x, y, width, height, npc_id, material="wood")


@dataclass
class BlacksmithBuilding(Building):
    """Blacksmith building for weapon/armor upgrades."""
    def __init__(self, x: int, y: int, width: int = 10, height: int = 10, npc_id: Optional[str] = None):
        super().__init__("blacksmith", x, y, width, height, npc_id, material="stone")


@dataclass
class LibraryBuilding(Building):
    """Library building for skill books and knowledge."""
    def __init__(self, x: int, y: int, width: int = 12, height: int = 12, npc_id: Optional[str] = None):
        super().__init__("library", x, y, width, height, npc_id, material="stone")


@dataclass
class MarketBuilding(Building):
    """Market building - large open area with stalls."""
    def __init__(self, x: int, y: int, width: int = 15, height: int = 15, npc_id: Optional[str] = None):
        super().__init__("market", x, y, width, height, npc_id, material="stone")


@dataclass
class TownHallBuilding(Building):
    """Town hall building containing the mayor/elder."""
    def __init__(self, x: int, y: int, width: int = 14, height: int = 14, npc_id: Optional[str] = None):
        super().__init__("town_hall", x, y, width, height, npc_id, material="stone")


@dataclass
class HouseBuilding(Building):
    """Decorative house building."""
    def __init__(self, x: int, y: int, width: int = 8, height: int = 8, npc_id: Optional[str] = None):
        super().__init__("house", x, y, width, height, npc_id, material="wood")


def place_buildings(
    map_width: int,
    map_height: int,
    level: int,
    seed: Optional[int] = None,
) -> List[Building]:
    """
    Place buildings around the town.
    
    Towns have more buildings than villages, and more variety.
    
    Args:
        map_width: Map width in tiles
        map_height: Map height in tiles
        level: Town level (affects building count)
        seed: Random seed for deterministic generation
        
    Returns:
        List of placed buildings
    """
    if seed is not None:
        random.seed(seed)
    
    buildings: List[Building] = []
    
    # Determine building count based on level
    # Towns are larger: 8-15 buildings for small, 12-20 for medium, 18-28 for large
    if level <= 3:
        min_buildings = 8
        max_buildings = 15
    elif level <= 7:
        min_buildings = 12
        max_buildings = 20
    else:
        min_buildings = 18
        max_buildings = 28
    
    num_buildings = random.randint(min_buildings, max_buildings)
    
    # Essential buildings for towns (more than villages)
    essential_buildings = ["town_hall", "shop", "inn", "tavern", "blacksmith", "library", "market"]
    building_types = essential_buildings.copy()
    
    # Add houses for remaining slots
    remaining = num_buildings - len(essential_buildings)
    building_types.extend(["house"] * max(0, remaining))
    
    # Shuffle to randomize placement order
    random.shuffle(building_types)
    
    # Place buildings around perimeter and in districts
    # Leave a border for paths (at least 2 tiles from edge)
    border = 2
    inner_x = border
    inner_y = border
    inner_width = map_width - 2 * border
    inner_height = map_height - 2 * border
    
    max_attempts = 500  # More attempts for towns (more buildings)
    attempts = 0
    
    for building_type in building_types:
        if attempts >= max_attempts:
            break
        
        # Determine building size based on type
        if building_type == "town_hall":
            w, h = 14, 14
            building_class = TownHallBuilding
        elif building_type == "market":
            w, h = 15, 15
            building_class = MarketBuilding
        elif building_type == "library":
            w, h = 12, 12
            building_class = LibraryBuilding
        elif building_type == "blacksmith":
            w, h = 10, 10
            building_class = BlacksmithBuilding
        elif building_type == "tavern":
            w, h = 12, 12
            building_class = TavernBuilding
        elif building_type == "shop":
            w, h = 10, 10
            building_class = ShopBuilding
        elif building_type == "inn":
            w, h = 10, 10
            building_class = InnBuilding
        else:  # house
            w, h = 8, 8
            building_class = HouseBuilding
        
        # Try to place building
        placed = False
        for _ in range(100):  # More attempts per building
            attempts += 1
            if attempts >= max_attempts:
                break
            
            # Try placing on perimeter (prefer edges) or in interior districts
            # 70% chance to place on perimeter, 30% in interior
            if random.random() < 0.7:
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
            else:
                # Place in interior (but not too close to center where plaza will be)
                center_x = map_width // 2
                center_y = map_height // 2
                plaza_radius = min(map_width, map_height) // 4
                
                # Try to place away from center
                for _ in range(20):
                    x = random.randint(inner_x, inner_x + inner_width - w)
                    y = random.randint(inner_y, inner_y + inner_height - h)
                    
                    # Check distance from center
                    dist = ((x + w//2 - center_x)**2 + (y + h//2 - center_y)**2)**0.5
                    if dist > plaza_radius:
                        break
            
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
