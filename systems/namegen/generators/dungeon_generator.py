"""
Dungeon name generator.

Generates names for dungeons and other locations.
"""

import random
from typing import Optional

from ..base import NameGenerator
from ..pools import get_pools


class DungeonNameGenerator(NameGenerator):
    """
    Generates names for dungeons and other locations.
    
    Supports multiple patterns:
    - "Prefix Suffix" (e.g., "Dark Crypt")
    - "Prefix Root Suffix" (e.g., "Ancient Temple")
    - With descriptors (e.g., "Cursed Catacombs of Shadows")
    """
    
    def __init__(self, pools=None):
        """Initialize dungeon name generator."""
        if pools is None:
            pools = get_pools()
        super().__init__(pools, "dungeon")
    
    def generate(
        self,
        include_descriptor: bool = False,
        pattern: str = "auto",
    ) -> str:
        """
        Generate a dungeon name.
        
        Args:
            include_descriptor: If True, adds "of {something}" suffix
            pattern: "prefix_suffix", "prefix_root_suffix", or "auto"
        
        Returns:
            Generated dungeon name
        """
        if pattern == "auto":
            # Randomly choose a pattern
            patterns = ["prefix_suffix", "prefix_root_suffix"]
            pattern = random.choice(patterns)
        
        if pattern == "prefix_suffix":
            prefix = random.choice(self.pools.dungeon_prefixes)
            suffix = random.choice(self.pools.dungeon_suffixes)
            name = f"{prefix} {suffix}"
        elif pattern == "prefix_root_suffix":
            prefix = random.choice(self.pools.dungeon_prefixes)
            # Use a syllable or structure type as root
            if random.random() < 0.5:
                root = random.choice(self.pools.structure_types)
            else:
                # Generate a short root from syllables
                syllable = random.choice(self.pools.fantasy_syllables)
                root = syllable.capitalize()
            suffix = random.choice(self.pools.dungeon_suffixes)
            name = f"{prefix} {root} {suffix}"
        else:
            # Fallback to simple prefix + suffix
            prefix = random.choice(self.pools.dungeon_prefixes)
            suffix = random.choice(self.pools.dungeon_suffixes)
            name = f"{prefix} {suffix}"
        
        # Add descriptor if requested
        if include_descriptor and random.random() < 0.6:
            descriptor = random.choice(self.pools.dungeon_descriptors)
            name = f"{name} {descriptor}"
        
        return name


# Convenience function
def generate_dungeon_name(
    include_descriptor: bool = False,
    pattern: str = "auto",
) -> str:
    """
    Generate a dungeon name (convenience function).
    
    Args:
        include_descriptor: If True, adds "of {something}" suffix
        pattern: "prefix_suffix", "prefix_root_suffix", or "auto"
    
    Returns:
        Generated dungeon name
    """
    generator = DungeonNameGenerator()
    return generator.generate(
        include_descriptor=include_descriptor,
        pattern=pattern,
    )

