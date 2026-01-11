"""
Unit tests for the status effects system.
"""

import pytest
from systems.statuses import StatusEffect, tick_statuses, has_status, is_stunned, outgoing_multiplier, incoming_multiplier


class TestStatusEffect:
    """Tests for StatusEffect dataclass."""

    def test_status_effect_creation(self):
        """Test creating a status effect."""
        status = StatusEffect(
            name="Poison",
            duration=3,
            stacks=2,
            flat_damage_each_turn=5,
        )
        assert status.name == "Poison"
        assert status.duration == 3
        assert status.stacks == 2
        assert status.flat_damage_each_turn == 5

    def test_status_effect_defaults(self):
        """Test status effect default values."""
        status = StatusEffect(name="Test")
        assert status.name == "Test"
        assert status.duration == 0
        assert status.stacks == 1
        assert status.flat_damage_each_turn == 0
        assert status.stunned is False
        assert status.outgoing_mult == 1.0
        assert status.incoming_mult == 1.0


class TestTickStatuses:
    """Tests for tick_statuses function."""

    def test_tick_statuses_decrements_duration(self):
        """Test that status durations are decremented."""
        statuses = [
            StatusEffect(name="Test1", duration=3),
            StatusEffect(name="Test2", duration=1),
        ]
        
        damage = tick_statuses(statuses)
        
        # First status should have duration 2
        assert statuses[0].duration == 2
        # Second status should be removed (duration was 1, now 0)
        assert len(statuses) == 1
        assert statuses[0].name == "Test1"
        assert damage == 0

    def test_tick_statuses_applies_dot(self):
        """Test that damage over time is applied correctly."""
        statuses = [
            StatusEffect(
                name="Poison",
                duration=3,
                stacks=1,
                flat_damage_each_turn=5,
            ),
            StatusEffect(
                name="Burn",
                duration=2,
                stacks=2,
                flat_damage_each_turn=3,
            ),
        ]
        
        damage = tick_statuses(statuses)
        
        # Poison: 5 * 1 = 5 damage
        # Burn: 3 * 2 = 6 damage
        # Total: 11 damage
        assert damage == 11
        assert statuses[0].duration == 2
        assert statuses[1].duration == 1

    def test_tick_statuses_removes_expired(self):
        """Test that expired statuses are removed."""
        statuses = [
            StatusEffect(name="Short", duration=1),
            StatusEffect(name="Long", duration=3),
        ]
        
        tick_statuses(statuses)
        # Short should be removed, Long should remain
        assert len(statuses) == 1
        assert statuses[0].name == "Long"
        assert statuses[0].duration == 2

    def test_tick_statuses_empty_list(self):
        """Test ticking an empty status list."""
        statuses = []
        damage = tick_statuses(statuses)
        assert damage == 0
        assert len(statuses) == 0

    def test_tick_statuses_no_dot(self):
        """Test ticking statuses without damage over time."""
        statuses = [
            StatusEffect(name="Stun", duration=2, stunned=True),
            StatusEffect(name="Buff", duration=3),
        ]
        
        damage = tick_statuses(statuses)
        assert damage == 0
        assert len(statuses) == 2


class TestStatusQueries:
    """Tests for status query functions."""

    def test_has_status(self):
        """Test checking if a status exists."""
        statuses = [
            StatusEffect(name="Poison", duration=3),
            StatusEffect(name="Burn", duration=2),
        ]
        
        assert has_status(statuses, "Poison") is True
        assert has_status(statuses, "Burn") is True
        assert has_status(statuses, "Freeze") is False
        assert has_status([], "Poison") is False

    def test_is_stunned(self):
        """Test checking if unit is stunned."""
        statuses = [
            StatusEffect(name="Poison", duration=3),
            StatusEffect(name="Stun", duration=2, stunned=True),
        ]
        
        assert is_stunned(statuses) is True
        
        statuses_no_stun = [
            StatusEffect(name="Poison", duration=3),
        ]
        assert is_stunned(statuses_no_stun) is False
        assert is_stunned([]) is False

    def test_outgoing_multiplier(self):
        """Test calculating outgoing damage multiplier."""
        statuses = [
            StatusEffect(name="Weak", duration=3, outgoing_mult=0.5),
            StatusEffect(name="Rage", duration=2, outgoing_mult=1.5),
        ]
        
        # Multipliers are multiplied: 0.5 * 1.5 = 0.75
        mult = outgoing_multiplier(statuses)
        assert mult == 0.75
        
        # Single multiplier
        single = [StatusEffect(name="Weak", duration=3, outgoing_mult=0.5)]
        assert outgoing_multiplier(single) == 0.5
        
        # No statuses
        assert outgoing_multiplier([]) == 1.0

    def test_incoming_multiplier(self):
        """Test calculating incoming damage multiplier."""
        statuses = [
            StatusEffect(name="Armor", duration=3, incoming_mult=0.8),
            StatusEffect(name="Vulnerable", duration=2, incoming_mult=1.2),
        ]
        
        # Multipliers are multiplied: 0.8 * 1.2 = 0.96
        mult = incoming_multiplier(statuses)
        assert mult == 0.96
        
        # Single multiplier
        single = [StatusEffect(name="Armor", duration=3, incoming_mult=0.5)]
        assert incoming_multiplier(single) == 0.5
        
        # No statuses
        assert incoming_multiplier([]) == 1.0

