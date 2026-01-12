"""
Village name generator.

Generates rustic, humble names for small settlements.
Villages are smaller than towns and have more nature-oriented,
simpler names.
"""

import random
from typing import Optional, Any

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
        faction_id: Optional[str] = None,
        faction: Optional[Any] = None,
    ) -> str:
        """
        Generate a village name.
        
        Args:
            pattern: "simple", "two_word", or "auto"
            faction_id: Optional faction ID for faction-aware naming
            faction: Optional Faction object (if provided, used for alignment-based naming)
        
        Returns:
            Generated village name
        """
        # Determine alignment-based naming style
        alignment_style = None
        if faction:
            from systems.factions import FactionAlignment
            if faction.alignment == FactionAlignment.GOOD:
                alignment_style = "noble"  # "X Hamlet", "X Village", "X Settlement"
            elif faction.alignment == FactionAlignment.NEUTRAL:
                alignment_style = "free"  # "X Crossing", "X Outpost", "X Camp"
            elif faction.alignment == FactionAlignment.EVIL:
                alignment_style = "dark"  # "X Den", "X Hideout", "X Lair"
        
        if pattern == "auto":
            # Randomly choose a pattern (simple is more common for villages)
            patterns = ["simple", "simple", "two_word"]  # 66% simple, 33% two_word
            pattern = random.choice(patterns)
        
        # Generate name based on alignment style
        if alignment_style == "noble":
            # Good factions: "X Hamlet", "X Village", "X Settlement"
            noble_suffixes = ["Hamlet", "Village", "Settlement", "Haven", "Refuge"]
            if random.random() < 0.6:
                # "X Hamlet" style
                prefix = random.choice(self.pools.village_prefixes)
                suffix = random.choice(noble_suffixes)
                name = f"{prefix} {suffix}"
            else:
                # Simple combined name
                prefix = random.choice(self.pools.village_prefixes)
                suffix = random.choice(self.pools.village_suffixes)
                name = f"{prefix}{suffix}"
        elif alignment_style == "free":
            # Neutral factions: "X Crossing", "X Outpost", "X Camp"
            free_suffixes = ["Crossing", "Outpost", "Camp", "Rest", "Stop"]
            if random.random() < 0.5:
                # "X Crossing" style
                prefix = random.choice(self.pools.village_prefixes)
                suffix = random.choice(free_suffixes)
                name = f"{prefix} {suffix}"
            else:
                # Simple combined name
                prefix = random.choice(self.pools.village_prefixes)
                suffix = random.choice(self.pools.village_suffixes)
                name = f"{prefix}{suffix}"
        elif alignment_style == "dark":
            # Evil factions: "X Den", "X Hideout", "X Lair"
            dark_suffixes = ["Den", "Hideout", "Lair", "Nest", "Pit"]
            if random.random() < 0.6:
                # "X Den" style
                prefix = random.choice(self.pools.village_prefixes)
                suffix = random.choice(dark_suffixes)
                name = f"{prefix} {suffix}"
            else:
                # Simple dark name
                prefix = random.choice(self.pools.village_prefixes)
                suffix = random.choice(self.pools.village_suffixes)
                name = f"{prefix}{suffix}"
        else:
            # Default naming (no faction or unknown alignment)
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
    faction_id: Optional[str] = None,
    faction: Optional[Any] = None,
) -> str:
    """
    Generate a village name (convenience function).
    
    Args:
        pattern: "simple", "two_word", or "auto"
        faction_id: Optional faction ID for faction-aware naming
        faction: Optional Faction object (if provided, used for alignment-based naming)
    
    Returns:
        Generated village name
    """
    generator = VillageNameGenerator()
    return generator.generate(pattern=pattern, faction_id=faction_id, faction=faction)

