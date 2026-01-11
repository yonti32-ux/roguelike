"""
Unit tests for the FloorManager class.
"""

import pytest
from engine.managers.floor_manager import FloorManager
from world.game_map import GameMap


class TestFloorManager:
    """Tests for FloorManager."""

    def test_floor_manager_initialization(self, floor_manager):
        """Test that FloorManager initializes correctly."""
        assert floor_manager.floor == 1
        assert floor_manager.floors == {}
        assert floor_manager.awaiting_floor_start is True

    def test_floor_manager_custom_starting_floor(self):
        """Test FloorManager with custom starting floor."""
        manager = FloorManager(starting_floor=5)
        assert manager.floor == 5

    def test_awaiting_floor_start_property(self, floor_manager):
        """Test awaiting_floor_start property."""
        assert floor_manager.awaiting_floor_start is True
        
        floor_manager.awaiting_floor_start = False
        assert floor_manager.awaiting_floor_start is False
        
        floor_manager.awaiting_floor_start = True
        assert floor_manager.awaiting_floor_start is True

    def test_has_floor(self, floor_manager):
        """Test checking if a floor exists."""
        assert floor_manager.has_floor(1) is False
        assert floor_manager.has_floor(5) is False
        
        # Generate a floor
        floor_manager.get_or_generate_floor(1)
        assert floor_manager.has_floor(1) is True
        assert floor_manager.has_floor(5) is False

    def test_get_or_generate_floor_creates_new(self, floor_manager):
        """Test that get_or_generate_floor creates new floors."""
        assert len(floor_manager.floors) == 0
        
        game_map, newly_created = floor_manager.get_or_generate_floor(1)
        
        assert newly_created is True
        assert isinstance(game_map, GameMap)
        assert len(floor_manager.floors) == 1
        assert floor_manager.has_floor(1) is True

    def test_get_or_generate_floor_reuses_existing(self, floor_manager):
        """Test that get_or_generate_floor reuses existing floors."""
        # Generate floor 1
        game_map1, created1 = floor_manager.get_or_generate_floor(1)
        assert created1 is True
        
        # Get floor 1 again
        game_map2, created2 = floor_manager.get_or_generate_floor(1)
        assert created2 is False
        assert game_map1 is game_map2  # Should be the same object

    def test_get_floor_returns_existing(self, floor_manager):
        """Test get_floor returns existing floor or None."""
        # Initially no floor
        result = floor_manager.get_floor(1)
        assert result is None
        
        # Generate the floor
        floor_manager.get_or_generate_floor(1)
        
        # Now should return it
        result = floor_manager.get_floor(1)
        assert isinstance(result, GameMap)

    def test_change_floor_positive_delta(self, floor_manager):
        """Test changing floor with positive delta."""
        floor_manager.floor = 3
        new_floor = floor_manager.change_floor(1)
        assert new_floor == 4

    def test_change_floor_negative_delta(self, floor_manager):
        """Test changing floor with negative delta."""
        floor_manager.floor = 5
        new_floor = floor_manager.change_floor(-1)
        assert new_floor == 4

    def test_change_floor_prevents_negative(self, floor_manager):
        """Test that change_floor prevents negative floor numbers."""
        floor_manager.floor = 1
        new_floor = floor_manager.change_floor(-1)
        assert new_floor == 0  # Returns 0 for invalid (can't go below 1)
        
        # Test edge case: floor 1, delta -2
        new_floor = floor_manager.change_floor(-2)
        assert new_floor == 0

    def test_change_floor_zero_returns_zero(self, floor_manager):
        """Test that change_floor returns 0 when result would be 0 or negative."""
        floor_manager.floor = 1
        new_floor = floor_manager.change_floor(-1)
        assert new_floor == 0

    def test_multiple_floors_cached(self, floor_manager):
        """Test that multiple floors can be cached."""
        floor1, _ = floor_manager.get_or_generate_floor(1)
        floor2, _ = floor_manager.get_or_generate_floor(2)
        floor3, _ = floor_manager.get_or_generate_floor(3)
        
        assert len(floor_manager.floors) == 3
        assert floor_manager.has_floor(1) is True
        assert floor_manager.has_floor(2) is True
        assert floor_manager.has_floor(3) is True
        
        # Verify they're different objects
        assert floor1 is not floor2
        assert floor2 is not floor3

