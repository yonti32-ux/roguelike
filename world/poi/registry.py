"""
POI Registry System

Provides a registry pattern for extensible POI type creation and management.
Allows new POI types to be registered without modifying core placement logic.
"""

from typing import Dict, Callable, Optional, Type, Any
from .base import PointOfInterest


class POIRegistry:
    """
    Registry for POI types and their factory functions.
    
    Supports:
    - Factory functions for creating POI instances
    - Optional custom serialization/deserialization
    - Optional tooltip generation
    """
    
    def __init__(self):
        self._factories: Dict[str, Callable[..., PointOfInterest]] = {}
        self._poi_classes: Dict[str, Type[PointOfInterest]] = {}
    
    def register(
        self,
        poi_type: str,
        factory: Optional[Callable[..., PointOfInterest]] = None,
        poi_class: Optional[Type[PointOfInterest]] = None,
    ) -> None:
        """
        Register a POI type.
        
        Args:
            poi_type: String identifier for the POI type (e.g., "dungeon", "village")
            factory: Optional factory function that creates a POI instance.
                     Signature: (poi_id: str, position: tuple, level: int, name: Optional[str], **kwargs) -> PointOfInterest
                     If None, will use default constructor from poi_class
            poi_class: Optional POI class. Used as fallback if factory is None
        """
        if factory is not None:
            self._factories[poi_type] = factory
        elif poi_class is not None:
            # Create a default factory that uses the class constructor
            def default_factory(poi_id: str, position: tuple, level: int = 1, name: Optional[str] = None, **kwargs):
                return poi_class(poi_id, position, level=level, name=name, **kwargs)
            self._factories[poi_type] = default_factory
            self._poi_classes[poi_type] = poi_class
        else:
            raise ValueError(f"Either factory or poi_class must be provided for POI type '{poi_type}'")
        
        if poi_class is not None:
            self._poi_classes[poi_type] = poi_class
    
    def create(
        self,
        poi_type: str,
        poi_id: str,
        position: tuple[int, int],
        level: int = 1,
        name: Optional[str] = None,
        **kwargs,
    ) -> PointOfInterest:
        """
        Create a POI instance of the given type.
        
        Args:
            poi_type: Type of POI to create
            poi_id: Unique identifier
            position: Overworld position (x, y)
            level: Difficulty level
            name: Optional display name
            **kwargs: Additional arguments passed to factory function
            
        Returns:
            PointOfInterest instance
            
        Raises:
            ValueError: If poi_type is not registered
        """
        if poi_type not in self._factories:
            raise ValueError(f"POI type '{poi_type}' is not registered. Registered types: {list(self._factories.keys())}")
        
        factory = self._factories[poi_type]
        return factory(poi_id, position, level=level, name=name, **kwargs)
    
    def get_poi_class(self, poi_type: str) -> Optional[Type[PointOfInterest]]:
        """Get the POI class for a given type, if registered."""
        return self._poi_classes.get(poi_type)
    
    def is_registered(self, poi_type: str) -> bool:
        """Check if a POI type is registered."""
        return poi_type in self._factories
    
    def get_registered_types(self) -> list[str]:
        """Get list of all registered POI types."""
        return list(self._factories.keys())


# Global registry instance
_global_registry = POIRegistry()


def get_registry() -> POIRegistry:
    """Get the global POI registry."""
    return _global_registry


def register_poi_type(
    poi_type: str,
    factory: Optional[Callable[..., PointOfInterest]] = None,
    poi_class: Optional[Type[PointOfInterest]] = None,
) -> None:
    """
    Register a POI type with the global registry.
    
    Convenience function for registering POI types.
    
    Args:
        poi_type: String identifier for the POI type
        factory: Optional factory function
        poi_class: Optional POI class (used if factory is None)
    """
    _global_registry.register(poi_type, factory, poi_class)

