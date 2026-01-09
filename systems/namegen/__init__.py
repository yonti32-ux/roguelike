"""
Name Generation System

A modular, extensible name generation framework for generating names
for bosses, dungeons, towns, NPCs, and other entities.
"""

from .base import NameGenerator, NamePools
from .generators.boss_generator import BossNameGenerator, generate_boss_name
from .generators.dungeon_generator import DungeonNameGenerator, generate_dungeon_name
from .generators.town_generator import TownNameGenerator, generate_town_name
from .generators.world_generator import WorldNameGenerator, generate_world_name

__all__ = [
    # Base classes
    "NameGenerator",
    "NamePools",
    # Boss generator
    "BossNameGenerator",
    "generate_boss_name",
    # Dungeon generator
    "DungeonNameGenerator",
    "generate_dungeon_name",
    # Town generator
    "TownNameGenerator",
    "generate_town_name",
    # World generator
    "WorldNameGenerator",
    "generate_world_name",
]

