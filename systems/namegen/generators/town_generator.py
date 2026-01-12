"""
Town and village name generator.
"""

import random
from typing import Optional, Any

from ..base import NameGenerator
from ..pools import get_pools


class TownNameGenerator(NameGenerator):
    """
    Generates names for towns and villages.
    
    Supports patterns like:
    - "PrefixSuffix" (e.g., "Greenvale")
    - "Prefix Terrain" (e.g., "New Valley")
    """
    
    def __init__(self, pools=None):
        """Initialize town name generator."""
        if pools is None:
            pools = get_pools()
        super().__init__(pools, "town")
    
    def generate(
        self,
        pattern: str = "auto",
        faction_id: Optional[str] = None,
        faction: Optional[Any] = None,
    ) -> str:
        """
        Generate a town name.
        
        Args:
            pattern: "simple", "with_terrain", or "auto"
            faction_id: Optional faction ID for faction-aware naming
            faction: Optional Faction object (if provided, used for alignment-based naming)
        
        Returns:
            Generated town name
        """
        # Determine alignment-based naming style
        alignment_style = None
        if faction:
            from systems.factions import FactionAlignment
            if faction.alignment == FactionAlignment.GOOD:
                alignment_style = "noble"  # "Kingdom of X", "Realm of X"
            elif faction.alignment == FactionAlignment.NEUTRAL:
                alignment_style = "free"  # "Free X", "X Port", "X Market"
            elif faction.alignment == FactionAlignment.EVIL:
                alignment_style = "dark"  # "Shadow X", "Dark X", "Crimson X"
        
        if pattern == "auto":
            # Randomly choose a pattern
            patterns = ["simple", "with_terrain"]
            pattern = random.choice(patterns)
        
        # Generate name based on alignment style
        if alignment_style == "noble":
            # Good factions: "Kingdom of X", "Realm of X", "X Keep", "X Hold"
            noble_prefixes = ["Kingdom of", "Realm of", "Domain of", "Land of"]
            noble_suffixes = ["Keep", "Hold", "Fortress", "Castle", "Stronghold"]
            if random.random() < 0.6:
                # "Kingdom of X" style
                prefix = random.choice(noble_prefixes)
                suffix = random.choice(self.pools.town_suffixes)
                name = f"{prefix} {suffix}"
            else:
                # "X Keep" style
                prefix = random.choice(self.pools.town_prefixes)
                suffix = random.choice(noble_suffixes)
                name = f"{prefix} {suffix}"
        elif alignment_style == "free":
            # Neutral factions: "Free X", "X Port", "X Market", "X Trade"
            free_prefixes = ["Free", "Independent", "Merchant"]
            free_suffixes = ["Port", "Market", "Trade", "Harbor", "Bazaar"]
            if random.random() < 0.5:
                # "Free X" style
                prefix = random.choice(free_prefixes)
                suffix = random.choice(self.pools.town_suffixes)
                name = f"{prefix} {suffix}"
            else:
                # "X Port" style
                prefix = random.choice(self.pools.town_prefixes)
                suffix = random.choice(free_suffixes)
                name = f"{prefix} {suffix}"
        elif alignment_style == "dark":
            # Evil factions: "Shadow X", "Dark X", "Crimson X"
            dark_prefixes = ["Shadow", "Dark", "Crimson", "Black", "Iron"]
            if random.random() < 0.7:
                # "Shadow X" style
                prefix = random.choice(dark_prefixes)
                suffix = random.choice(self.pools.town_suffixes)
                name = f"{prefix} {suffix}"
            else:
                # Simple dark name
                prefix = random.choice(self.pools.town_prefixes)
                suffix = random.choice(self.pools.town_suffixes)
                name = f"{prefix}{suffix}"
        else:
            # Default naming (no faction or unknown alignment)
            if pattern == "simple":
                prefix = random.choice(self.pools.town_prefixes)
                suffix = random.choice(self.pools.town_suffixes)
                name = f"{prefix}{suffix}"
            elif pattern == "with_terrain":
                prefix = random.choice(self.pools.town_prefixes)
                terrain = random.choice(self.pools.terrain_types)
                name = f"{prefix} {terrain}"
            else:
                # Fallback to simple
                prefix = random.choice(self.pools.town_prefixes)
                suffix = random.choice(self.pools.town_suffixes)
                name = f"{prefix}{suffix}"
        
        return name


# Convenience function
def generate_town_name(
    pattern: str = "auto",
    faction_id: Optional[str] = None,
    faction: Optional[Any] = None,
) -> str:
    """
    Generate a town name (convenience function).
    
    Args:
        pattern: "simple", "with_terrain", or "auto"
        faction_id: Optional faction ID for faction-aware naming
        faction: Optional Faction object (if provided, used for alignment-based naming)
    
    Returns:
        Generated town name
    """
    generator = TownNameGenerator()
    return generator.generate(pattern=pattern, faction_id=faction_id, faction=faction)

