"""
Base name generation classes and interfaces.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class NamePools:
    """
    Container for all name pools used by generators.
    This allows sharing pools across different generators.
    """
    # Syllables for constructing names
    fantasy_syllables: List[str]
    brutal_syllables: List[str]
    mystical_syllables: List[str]
    beast_syllables: List[str]
    
    # Prefixes
    dungeon_prefixes: List[str]
    town_prefixes: List[str]
    
    # Suffixes
    dungeon_suffixes: List[str]
    town_suffixes: List[str]
    
    # Descriptors/Adjectives
    brutal_descriptors: List[str]
    mystical_descriptors: List[str]
    dungeon_descriptors: List[str]
    
    # Geographical terms
    terrain_types: List[str]
    structure_types: List[str]
    
    def get_pool(self, pool_name: str) -> List[str]:
        """Get a pool by name."""
        return getattr(self, pool_name, [])


class NameGenerator(ABC):
    """
    Base class for all name generators.
    
    Subclasses should implement `generate()` to produce names
    for their specific context.
    """
    
    def __init__(self, pools: NamePools, context: str):
        """
        Initialize a name generator.
        
        Args:
            pools: Shared name pools
            context: Context name (e.g., "boss", "dungeon", "town")
        """
        self.pools = pools
        self.context = context
    
    @abstractmethod
    def generate(self, **kwargs) -> str:
        """
        Generate a name.
        
        Args:
            **kwargs: Context-specific parameters
            
        Returns:
            Generated name string
        """
        raise NotImplementedError
    
    def apply_pattern(self, pattern: str, values: Dict[str, str]) -> str:
        """
        Apply a pattern template with values.
        
        Args:
            pattern: Template string with placeholders (e.g., "{name}, the {title}")
            values: Dictionary mapping placeholder names to values
            
        Returns:
            Formatted string
        """
        try:
            return pattern.format(**values)
        except KeyError as e:
            # Missing key in pattern - return fallback
            return f"Unknown {self.context}"

