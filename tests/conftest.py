"""
Pytest configuration and shared fixtures.

This file is automatically discovered by pytest and provides fixtures
available to all test files.
"""

import pytest
import pygame
from typing import Generator

# Initialize pygame once for all tests
# Note: This is done at module level, but we handle cleanup in fixtures


@pytest.fixture(scope="session", autouse=True)
def pygame_init() -> Generator[None, None, None]:
    """
    Initialize pygame for the test session.
    This runs once before all tests and cleans up after.
    """
    pygame.init()
    # Use a small headless surface (no display needed)
    pygame.display.set_mode((800, 600), pygame.HIDDEN)
    yield
    pygame.quit()


@pytest.fixture
def sample_screen() -> pygame.Surface:
    """
    Create a sample pygame surface for tests that need a screen.
    """
    return pygame.Surface((800, 600))


@pytest.fixture
def sample_inventory():
    """
    Create a sample inventory for testing.
    """
    from systems.inventory import Inventory
    return Inventory()


@pytest.fixture
def sample_stat_block():
    """
    Create a sample StatBlock for testing.
    """
    from systems.stats import StatBlock
    return StatBlock(
        max_hp=100,
        attack=10,
        defense=5,
        speed=1.0,
        initiative=10,
        skill_power=1.0,
    )


@pytest.fixture
def sample_hero_stats():
    """
    Create a sample HeroStats object for testing.
    """
    from systems.progression import HeroStats
    stats = HeroStats()
    stats.level = 1
    stats.xp = 0
    stats.gold = 100
    stats.hero_class_id = "warrior"
    return stats


@pytest.fixture
def sample_status_effects():
    """
    Create sample status effects for testing.
    """
    from systems.statuses import StatusEffect
    return [
        StatusEffect(
            name="Poison",
            duration=3,
            stacks=1,
            flat_damage_each_turn=5,
        ),
        StatusEffect(
            name="Stunned",
            duration=1,
            stacks=1,
            stunned=True,
        ),
    ]


@pytest.fixture
def floor_manager():
    """
    Create a FloorManager for testing.
    """
    from engine.managers.floor_manager import FloorManager
    return FloorManager(starting_floor=1)

