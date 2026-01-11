"""
Village name generator.

Generates rustic, humble names for small settlements.
Villages are smaller than towns and have more nature-oriented,
simpler names.
"""

import random
from typing import Optional

from ..base import NameGenerator
from ..pools import get_pools


class VillageNameGenerator(NameGenerator):
    """
    Generates names for villages (small settlements).
    
    Villages use simpler, more rustic patterns than towns:
    - "PrefixSuffix" (e.g., "Greenham", "Millbrook")
    - "Prefix Suffix" (e.g., "Little Mill", "Oak Glen")
    - Simple nature names (e.g., "Willowbrook", "Meadowcroft")
    
    Patterns are simpler and more nature-oriented than towns.
    """
    
    def __init__(self, pools=None):
        """Initialize village name generator."""
        if pools is None:
            pools = get_pools()
        super().__init__(pools, "village")
    
    def generate(
        self,
        pattern: str = "auto",
    ) -> str:
        """
        Generate a village name.
        
        Args:
            pattern: "simple", "two_word", or "auto"
        
        Returns:
            Generated village name
        """
        if pattern == "auto":
            # Randomly choose a pattern (simple is more common for villages)
            patterns = ["simple", "simple", "two_word"]  # 66% simple, 33% two_word
            pattern = random.choice(patterns)
        
        if pattern == "simple":
            # Simple prefix+suffix combination (e.g., "Greenham", "Millbrook")
            prefix = random.choice(self.pools.village_prefixes)
            suffix = random.choice(self.pools.village_suffixes)
            name = f"{prefix}{suffix}"
        elif pattern == "two_word":
            # Two-word name with space (e.g., "Little Mill", "Oak Glen")
            prefix = random.choice(self.pools.village_prefixes)
            suffix = random.choice(self.pools.village_suffixes)
            # Capitalize suffix for two-word format
            suffix_capitalized = suffix.capitalize()
            name = f"{prefix} {suffix_capitalized}"
        else:
            # Fallback to simple
            prefix = random.choice(self.pools.village_prefixes)
            suffix = random.choice(self.pools.village_suffixes)
            name = f"{prefix}{suffix}"
        
        return name


# Convenience function
def generate_village_name(
    pattern: str = "auto",
) -> str:
    """
    Generate a village name (convenience function).
    
    Args:
        pattern: "simple", "two_word", or "auto"
    
    Returns:
        Generated village name
    """
    generator = VillageNameGenerator()
    return generator.generate(pattern=pattern)

