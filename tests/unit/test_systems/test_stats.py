"""
Unit tests for the stats system.
"""

import pytest
from systems.stats import StatBlock


class TestStatBlock:
    """Tests for StatBlock dataclass."""

    def test_stat_block_initialization_defaults(self):
        """Test that StatBlock initializes with default values."""
        stats = StatBlock()
        assert stats.max_hp == 30
        assert stats.attack == 6
        assert stats.defense == 0
        assert stats.speed == 1.0
        assert stats.initiative == 10
        assert stats.skill_power == 1.0
        assert stats.crit_chance == 0.0
        assert stats.dodge_chance == 0.0
        assert stats.status_resist == 0.0
        assert stats.max_mana == 0
        assert stats.max_stamina == 0

    def test_stat_block_custom_values(self):
        """Test creating StatBlock with custom values."""
        stats = StatBlock(
            max_hp=100,
            attack=15,
            defense=10,
            speed=1.5,
            initiative=20,
            skill_power=2.0,
            crit_chance=0.15,
            dodge_chance=0.10,
            status_resist=0.25,
            max_mana=50,
            max_stamina=30,
        )
        
        assert stats.max_hp == 100
        assert stats.attack == 15
        assert stats.defense == 10
        assert stats.speed == 1.5
        assert stats.initiative == 20
        assert stats.skill_power == 2.0
        assert stats.crit_chance == 0.15
        assert stats.dodge_chance == 0.10
        assert stats.status_resist == 0.25
        assert stats.max_mana == 50
        assert stats.max_stamina == 30

    def test_stat_block_immutability(self):
        """Test that StatBlock fields can be modified (dataclass is mutable by default)."""
        stats = StatBlock(max_hp=50)
        assert stats.max_hp == 50
        
        # Dataclasses are mutable by default, so we can modify
        stats.max_hp = 75
        assert stats.max_hp == 75

