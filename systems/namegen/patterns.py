"""
Name pattern templates for different name generation contexts.
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class NamePattern:
    """Defines a pattern template for generating names."""
    template: str
    parts: List[str]
    description: str = ""


# Common name patterns
PATTERNS: Dict[str, NamePattern] = {
    "boss_with_title": NamePattern(
        template="{name}, the {title}",
        parts=["name", "title"],
        description="Boss name with title: 'Name, the Title'",
    ),
    "boss_simple": NamePattern(
        template="{name}",
        parts=["name"],
        description="Simple boss name without title",
    ),
    "dungeon_prefixed": NamePattern(
        template="{prefix} {root}{suffix}",
        parts=["prefix", "root", "suffix"],
        description="Dungeon with prefix and suffix: 'Prefix Root Suffix'",
    ),
    "dungeon_descriptive": NamePattern(
        template="{prefix} {root}{suffix} {descriptor}",
        parts=["prefix", "root", "suffix", "descriptor"],
        description="Dungeon with descriptor: 'Prefix Root Suffix of Something'",
    ),
    "town_simple": NamePattern(
        template="{prefix}{suffix}",
        parts=["prefix", "suffix"],
        description="Simple town name: 'PrefixSuffix'",
    ),
    "town_with_terrain": NamePattern(
        template="{prefix} {terrain}",
        parts=["prefix", "terrain"],
        description="Town with terrain: 'Prefix Valley'",
    ),
}

