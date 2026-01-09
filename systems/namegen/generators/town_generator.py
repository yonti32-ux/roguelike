"""
Town and village name generator.
"""

import random
from typing import Optional

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
    ) -> str:
        """
        Generate a town name.
        
        Args:
            pattern: "simple", "with_terrain", or "auto"
        
        Returns:
            Generated town name
        """
        if pattern == "auto":
            # Randomly choose a pattern
            patterns = ["simple", "with_terrain"]
            pattern = random.choice(patterns)
        
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
) -> str:
    """
    Generate a town name (convenience function).
    
    Args:
        pattern: "simple", "with_terrain", or "auto"
    
    Returns:
        Generated town name
    """
    generator = TownNameGenerator()
    return generator.generate(pattern=pattern)

