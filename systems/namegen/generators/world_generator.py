"""
World name generator.

Generates names for worlds/realms.
"""

import random
from typing import Optional

from ..base import NameGenerator
from ..pools import get_pools


class WorldNameGenerator(NameGenerator):
    """
    Generates names for worlds and realms.
    
    Supports patterns like:
    - "Adjective Realm" (e.g., "Mystic Realm")
    - "The Adjective Land" (e.g., "The Forgotten Land")
    - "Proper Noun" (e.g., "Aetheria")
    """
    
    def __init__(self, pools=None):
        """Initialize world name generator."""
        if pools is None:
            pools = get_pools()
        super().__init__(pools, "world")
    
    def generate(
        self,
        pattern: str = "auto",
        seed: Optional[int] = None,
    ) -> str:
        """
        Generate a world name.
        
        Args:
            pattern: "adjective_realm", "proper_noun", "the_land", or "auto"
            seed: Optional seed for deterministic generation
        
        Returns:
            Generated world name
        """
        # If seed is provided, use it for deterministic generation
        if seed is not None:
            rng_state = random.getstate()
            random.seed(seed)
            try:
                name = self._generate_name(pattern)
            finally:
                random.setstate(rng_state)
            return name
        else:
            return self._generate_name(pattern)
    
    def _generate_name(self, pattern: str) -> str:
        """Internal method to generate name."""
        if pattern == "auto":
            # Randomly choose a pattern
            patterns = ["adjective_realm", "proper_noun", "the_land"]
            pattern = random.choice(patterns)
        
        if pattern == "adjective_realm":
            # "Mystic Realm", "Ancient Realm", etc.
            adjectives = [
                "Mystic", "Ancient", "Eternal", "Forgotten", "Sacred",
                "Lost", "Golden", "Crimson", "Dark", "Bright",
                "Frozen", "Burning", "Ethereal", "Divine", "Cursed",
                "Blessed", "Shadow", "Light", "Primal", "Wild",
            ]
            realms = [
                "Realm", "Domain", "Kingdom", "Empire", "World",
                "Land", "Plane", "Dimension", "Realm", "Sphere",
            ]
            adj = random.choice(adjectives)
            realm = random.choice(realms)
            name = f"{adj} {realm}"
        
        elif pattern == "proper_noun":
            # Single proper noun like "Aetheria", "Mythralia"
            # Combine fantasy syllables into a proper name
            first_parts = [
                "Aeth", "Myth", "Arcan", "Celest", "Etern",
                "Myst", "Prim", "Sylv", "Verd", "Aur",
                "Lumen", "Noct", "Sol", "Luna", "Star",
                "Shadow", "Light", "Gold", "Iron", "Crystal",
            ]
            second_parts = [
                "ria", "ia", "ia", "ium", "ara",
                "eth", "ara", "en", "is", "on",
                "al", "ara", "ius", "os", "us",
            ]
            first = random.choice(first_parts)
            second = random.choice(second_parts)
            name = f"{first}{second}"
        
        elif pattern == "the_land":
            # "The Forgotten Land", "The Sacred Realm"
            adjectives = [
                "Forgotten", "Sacred", "Ancient", "Lost", "Golden",
                "Mystic", "Eternal", "Divine", "Cursed", "Blessed",
                "Shadow", "Light", "Primal", "Wild", "Frozen",
                "Burning", "Ethereal", "Dark", "Bright", "Crimson",
            ]
            lands = [
                "Land", "Realm", "Domain", "Kingdom", "World",
                "Plane", "Dimension", "Empire", "Sphere", "Realms",
            ]
            adj = random.choice(adjectives)
            land = random.choice(lands)
            name = f"The {adj} {land}"
        
        else:
            # Fallback to adjective_realm
            adjectives = ["Mystic", "Ancient", "Eternal"]
            name = f"{random.choice(adjectives)} Realm"
        
        return name


# Convenience function
def generate_world_name(
    pattern: str = "auto",
    seed: Optional[int] = None,
) -> str:
    """
    Generate a world name (convenience function).
    
    Args:
        pattern: "adjective_realm", "proper_noun", "the_land", or "auto"
        seed: Optional seed for deterministic generation
    
    Returns:
        Generated world name
    """
    generator = WorldNameGenerator()
    return generator.generate(pattern=pattern, seed=seed)

