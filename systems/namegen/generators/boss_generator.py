"""
Boss name generator.

Generates names for bosses and mini-bosses in the format:
"{name}, the {title}"

Supports tier-based title selection for appropriate difficulty scaling.
"""

import random
from typing import Optional

from ..base import NameGenerator
from ..pools import get_pools, get_brutal_descriptor_for_tier, get_mystical_descriptor_for_tier


class BossNameGenerator(NameGenerator):
    """
    Generates names for bosses and mini-bosses.
    
    Names follow the pattern: "{name}, the {title}"
    Titles are selected based on tier (difficulty level).
    """
    
    def __init__(self, pools=None):
        """Initialize boss name generator."""
        if pools is None:
            pools = get_pools()
        super().__init__(pools, "boss")
    
    def generate(
        self,
        tier: int = 2,
        is_final_boss: bool = False,
        use_title: bool = True,
        name_style: str = "auto",
    ) -> str:
        """
        Generate a boss name.
        
        Args:
            tier: Difficulty tier (1=early, 2=mid, 3=late)
            is_final_boss: If True, uses final boss titles
            use_title: If True, includes ", the {title}" suffix
            name_style: "brutal", "mystical", "beast", or "auto" (random)
        
        Returns:
            Generated boss name (e.g., "Gorthak, the Bloodthirsty")
        """
        # Generate the base name
        if name_style == "auto":
            # Randomly choose a style
            styles = ["brutal", "mystical", "fantasy"]
            name_style = random.choice(styles)
        
        base_name = self._generate_base_name(name_style)
        
        # Add title if requested
        if use_title:
            if is_final_boss:
                from ..pools import FINAL_BOSS_TITLES
                title = random.choice(FINAL_BOSS_TITLES)
            elif name_style in ("brutal", "beast", "fantasy"):
                title = get_brutal_descriptor_for_tier(tier)
            else:  # mystical
                title = get_mystical_descriptor_for_tier(tier)
            
            return f"{base_name}, {title}"
        else:
            return base_name
    
    def _generate_base_name(self, style: str) -> str:
        """
        Generate a base boss name from syllables.
        
        Args:
            style: Name style ("brutal", "mystical", "beast", "fantasy")
        
        Returns:
            Generated name
        """
        if style == "brutal":
            syllables = self.pools.brutal_syllables
        elif style == "mystical":
            syllables = self.pools.mystical_syllables
        elif style == "beast":
            syllables = self.pools.beast_syllables
        else:  # fantasy (default)
            syllables = self.pools.fantasy_syllables
        
        # Build name from 2-3 syllables
        num_parts = random.randint(2, 3)
        selected = random.sample(syllables, min(num_parts, len(syllables)))
        
        # Capitalize first letter of each part and combine
        name_parts = [part.capitalize() for part in selected]
        name = "".join(name_parts)
        
        # Ensure it's capitalized
        if name:
            name = name[0].upper() + name[1:] if len(name) > 1 else name.upper()
        
        return name if name else "Unknown"


# Convenience function for easy access
def generate_boss_name(
    tier: int = 2,
    is_final_boss: bool = False,
    use_title: bool = True,
    name_style: str = "auto",
) -> str:
    """
    Generate a boss name (convenience function).
    
    Args:
        tier: Difficulty tier (1=early, 2=mid, 3=late)
        is_final_boss: If True, uses final boss titles
        use_title: If True, includes ", the {title}" suffix
        name_style: "brutal", "mystical", "beast", or "auto" (random)
    
    Returns:
        Generated boss name
    """
    generator = BossNameGenerator()
    return generator.generate(
        tier=tier,
        is_final_boss=is_final_boss,
        use_title=use_title,
        name_style=name_style,
    )

