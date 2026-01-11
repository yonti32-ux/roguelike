"""
Sprite management system for modular sprite loading and rendering.

This system provides:
- Automatic sprite loading and caching
- Flexible registry for mapping IDs to sprite paths
- Support for multiple sprite categories (entities, tiles, items, etc.)
- Fallback to colored rectangles when sprites are missing
- Sprite set support (sprite sheets and animation sequences)
- Easy expansion for future sprite types
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from enum import Enum

import pygame

from settings import TILE_SIZE


class SpriteCategory(Enum):
    """Categories of sprites in the game."""
    ENTITY = "entity"      # Player, enemies, NPCs
    TILE = "tile"          # Floor, walls, stairs
    ITEM = "item"          # Weapons, armor, consumables
    BATTLE = "battle"      # Battle-specific sprites (units, effects)
    UI = "ui"              # UI elements, icons
    EFFECT = "effect"      # Status effects, buffs, debuffs
    SKILL = "skill"        # Skill icons
    TERRAIN = "terrain"    # Battle terrain types


class SpriteManager:
    """
    Central sprite manager that loads, caches, and provides sprites.
    
    Features:
    - Automatic loading from organized directory structure
    - Caching to avoid reloading sprites
    - Fallback support for missing sprites
    - Support for sprite variants (e.g., different states)
    """
    
    def __init__(self, sprite_root: Optional[Union[str, Path]] = None):
        """
        Initialize the sprite manager.
        
        Args:
            sprite_root: Root directory for sprites. If None, uses 'sprites' in project root.
        """
        if sprite_root is None:
            # Assume we're in engine/ directory, go up one level for sprites/
            script_dir = Path(__file__).parent
            sprite_root = script_dir.parent / "sprites"
        else:
            sprite_root = Path(sprite_root)
        
        self.sprite_root = sprite_root
        self._cache: Dict[str, pygame.Surface] = {}
        self._cache_metadata: Dict[str, bool] = {}  # Track if sprite is a fallback (True = is_fallback)
        self._missing_sprites: set = set()  # Track missing sprites to avoid repeated warnings
        
        # File existence cache: (category, sprite_id, variant) -> Path or None
        # Caches whether sprite files exist to avoid repeated file system I/O
        self._file_existence_cache: Dict[Tuple[SpriteCategory, str, Optional[str]], Optional[Path]] = {}
        
        # Sprite set manager (lazy-loaded)
        self._sprite_set_manager: Optional[object] = None
        
        # Enable sprite sets by default (can be disabled)
        self.enable_sprite_sets: bool = True
        
        # Canonical art size (all sprites should be this size)
        self.canonical_size: int = TILE_SIZE
        
        # Raw sprite cache (before convert_alpha) - keyed by (path, target_size, sprite_set_info)
        # This allows us to convert_alpha once and cache the result
        self._raw_sprite_cache: Dict[Tuple[str, Optional[Tuple[int, int]], Optional[str]], pygame.Surface] = {}
        
        # Tile chunk cache (for future optimization: 16x16 tile chunks)
        # Format: {(chunk_x, chunk_y, zoom_level): Surface}
        self._tile_chunk_cache: Dict[Tuple[int, int, int], pygame.Surface] = {}
        self._tile_chunk_size: int = 16  # 16x16 tiles per chunk
        
        # Ensure sprite directories exist
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """Create sprite directory structure if it doesn't exist."""
        for category in SpriteCategory:
            category_dir = self.sprite_root / category.value
            category_dir.mkdir(parents=True, exist_ok=True)
    
    def _calculate_integer_scale(self, original_size: Tuple[int, int], target_size: Optional[Tuple[int, int]]) -> Tuple[int, Tuple[int, int]]:
        """
        Calculate integer scale factor (2x, 3x, etc.) for scaling.
        Rounds to nearest integer multiple if non-integer scaling requested.
        
        Args:
            original_size: Original sprite size (width, height)
            target_size: Desired size (width, height), or None for canonical size
            
        Returns:
            Tuple of (scale_factor, final_size)
            - scale_factor: Integer scale (1, 2, 3, etc.), or None if can't determine
            - final_size: Final size to use (may be rounded from target_size)
        """
        if target_size is None:
            # Use canonical size
            target_size = (self.canonical_size, self.canonical_size)
        
        # Calculate scale factors
        scale_x = target_size[0] / original_size[0]
        scale_y = target_size[1] / original_size[1]
        
        # Check if both are approximately equal (allow small floating point error)
        if abs(scale_x - scale_y) > 0.01:
            # Non-uniform scaling - use average and round
            avg_scale = (scale_x + scale_y) / 2
            rounded_scale = max(1, round(avg_scale))
            final_size = (original_size[0] * rounded_scale, original_size[1] * rounded_scale)
            return (rounded_scale, final_size)
        
        # Uniform scaling
        rounded_scale = max(1, round(scale_x))
        
        # If it's very close to an integer, use it directly
        if abs(rounded_scale - scale_x) < 0.01:
            final_size = target_size  # Use exact target
        else:
            # Round to nearest integer multiple
            final_size = (original_size[0] * rounded_scale, original_size[1] * rounded_scale)
        
        return (rounded_scale, final_size)
    
    def _validate_sprite_size(self, file_path: Path, sprite: pygame.Surface) -> None:
        """
        Validate sprite size and warn if it's not canonical or an integer multiple.
        
        Args:
            file_path: Path to the sprite file
            sprite: Loaded sprite surface
        """
        width, height = sprite.get_size()
        
        # Check if it's canonical size
        if width == self.canonical_size and height == self.canonical_size:
            return  # Valid canonical size
        
        # Check if it's an integer multiple of canonical size
        if width % self.canonical_size == 0 and height % self.canonical_size == 0:
            scale = width // self.canonical_size
            if scale == height // self.canonical_size:
                return  # Valid integer multiple (e.g., 64x64 = 2x)
        
        # Invalid size - warn once
        file_name = file_path.name
        cache_key = f"size_warn:{file_name}"
        
        if cache_key not in self._missing_sprites:  # Reuse missing_sprites set for warnings
            print(f"WARNING: {file_name} is {width}x{height}; expected {self.canonical_size}x{self.canonical_size} "
                  f"(or integer multiple like {self.canonical_size * 2}x{self.canonical_size * 2})")
            self._missing_sprites.add(cache_key)
    
    def get_sprite(
        self,
        category: SpriteCategory,
        sprite_id: str,
        variant: Optional[str] = None,
        fallback_color: Optional[Tuple[int, int, int]] = None,
        size: Optional[Tuple[int, int]] = None,
        frame_index: Optional[int] = None,
        sheet_row: Optional[int] = None,
        sheet_col: Optional[int] = None,
    ) -> Optional[pygame.Surface]:
        """
        Get a sprite by category and ID.
        
        Optimization features:
        - Canonical art size: All sprites assumed to be TILE_SIZE
        - Integer scaling only: Only scales by whole number multiples (2x, 3x, etc.)
        - convert_alpha caching: Converts once per (path, size, sprite_set)
        
        Args:
            category: Sprite category (entity, tile, item, etc.)
            sprite_id: Unique identifier for the sprite (e.g., "player", "sword", "floor")
            variant: Optional variant name (e.g., "idle", "attacking", "damaged")
            fallback_color: Color to use if sprite is missing (default: magenta)
            size: Desired size (width, height). If None, uses canonical size (TILE_SIZE)
            frame_index: Frame index for sprite sets (animations or sheet frames)
            sheet_row: Row index for sprite sheets (alternative to frame_index)
            sheet_col: Column index for sprite sheets (alternative to frame_index)
            
        Returns:
            pygame.Surface with the sprite, or None if not found and no fallback
        """
        # Use canonical size if size not specified
        if size is None:
            size = (self.canonical_size, self.canonical_size)
        
        # Build cache key (include frame info for sprite sets and size for scaling)
        cache_key = f"{category.value}:{sprite_id}"
        if variant:
            cache_key += f":{variant}"
        if frame_index is not None:
            cache_key += f":frame{frame_index}"
        elif sheet_row is not None and sheet_col is not None:
            cache_key += f":r{sheet_row}c{sheet_col}"
        
        # Include size in cache key for scaled versions
        size_key = f"{cache_key}:{size[0]}x{size[1]}"
        
        # Check cache first
        if size_key in self._cache:
            sprite = self._cache[size_key]
            is_fallback = self._cache_metadata.get(size_key, False)
            sprite._sprite_is_fallback = is_fallback  # type: ignore
            return sprite
        
        # Also check base cache (no size)
        if cache_key in self._cache:
            base_sprite = self._cache[cache_key]
            is_fallback = self._cache_metadata.get(cache_key, False)
            
            # Check if we need to scale
            base_size = base_sprite.get_size()
            if base_size != size:
                # Calculate integer scale (rounds to nearest if needed)
                scale, final_size = self._calculate_integer_scale(base_size, size)
                
                if final_size != base_size:
                    # Need to scale
                    scaled_sprite = pygame.transform.scale(base_sprite, final_size)
                    # Cache the scaled version with actual final size
                    final_size_key = f"{cache_key}:{final_size[0]}x{final_size[1]}"
                    self._cache[final_size_key] = scaled_sprite
                    self._cache_metadata[final_size_key] = is_fallback
                    scaled_sprite._sprite_is_fallback = is_fallback  # type: ignore
                    return scaled_sprite
                else:
                    # Already correct size (scale was 1)
                    self._cache[size_key] = base_sprite
                    self._cache_metadata[size_key] = is_fallback
                    base_sprite._sprite_is_fallback = is_fallback  # type: ignore
                    return base_sprite
            else:
                # Exact size match
                base_sprite._sprite_is_fallback = is_fallback  # type: ignore
                return base_sprite
        
        # Try sprite sets first (if enabled)
        if self.enable_sprite_sets:
            sprite = self._try_get_sprite_set(category, sprite_id, variant, frame_index, sheet_row, sheet_col)
            if sprite:
                self._cache[cache_key] = sprite
                self._cache_metadata[cache_key] = False  # Real sprite from sprite set
                sprite._sprite_is_fallback = False  # type: ignore
                if size and sprite.get_size() != size:
                    sprite = pygame.transform.scale(sprite, size)
                    size_key = f"{cache_key}:{size[0]}x{size[1]}"
                    self._cache[size_key] = sprite
                    self._cache_metadata[size_key] = False
                return sprite
        
        # Build file path
        file_path = self._get_sprite_path(category, sprite_id, variant)
        
        # Try to load the sprite
        if file_path and file_path.exists():
            try:
                # Check raw sprite cache (before convert_alpha)
                # Key: (path, target_size, sprite_set_info)
                sprite_set_info = None
                if frame_index is not None:
                    sprite_set_info = f"frame{frame_index}"
                elif sheet_row is not None and sheet_col is not None:
                    sprite_set_info = f"r{sheet_row}c{sheet_col}"
                
                raw_cache_key = (str(file_path), size, sprite_set_info)
                
                if raw_cache_key in self._raw_sprite_cache:
                    # Use cached converted sprite
                    sprite = self._raw_sprite_cache[raw_cache_key]
                else:
                    # Load and convert_alpha once
                    sprite = pygame.image.load(str(file_path)).convert_alpha()
                    
                    # Validate sprite size (warn if invalid)
                    self._validate_sprite_size(file_path, sprite)
                    
                    # Check if scaling is needed (rounds to nearest integer multiple)
                    original_size = sprite.get_size()
                    if original_size != size:
                        scale, final_size = self._calculate_integer_scale(original_size, size)
                        
                        if final_size != original_size:
                            # Scale to nearest integer multiple
                            sprite = pygame.transform.scale(sprite, final_size)
                            size = final_size  # Use final size for caching
                    
                    # Cache the converted sprite
                    self._raw_sprite_cache[raw_cache_key] = sprite
                
                # Cache in main cache
                final_size = sprite.get_size()
                final_size_key = f"{cache_key}:{final_size[0]}x{final_size[1]}"
                self._cache[final_size_key] = sprite
                self._cache_metadata[final_size_key] = False  # Real sprite, not a fallback
                
                # Also cache base version
                self._cache[cache_key] = sprite
                self._cache_metadata[cache_key] = False
                
                # Attach metadata
                sprite._sprite_is_fallback = False  # type: ignore
                return sprite
            except Exception as e:
                if cache_key not in self._missing_sprites:
                    print(f"Warning: Failed to load sprite {cache_key}: {e}")
                    self._missing_sprites.add(cache_key)
        else:
            if cache_key not in self._missing_sprites:
                # Only warn once per missing sprite
                self._missing_sprites.add(cache_key)
                if fallback_color is None:
                    print(f"Warning: Sprite not found: {cache_key}")
        
        # Handle missing sprite
        if fallback_color is not None:
            # Generate fallback sprite at canonical size
            fallback_size = size if size else (self.canonical_size, self.canonical_size)
            fallback = pygame.Surface(fallback_size, pygame.SRCALPHA)
            fallback.fill(fallback_color)
            
            # Cache the fallback and mark it as such
            fallback_size_key = f"{cache_key}:{fallback_size[0]}x{fallback_size[1]}"
            self._cache[fallback_size_key] = fallback
            self._cache_metadata[fallback_size_key] = True  # Mark as fallback
            fallback._sprite_is_fallback = True  # type: ignore
            return fallback
        else:
            # No fallback color provided - return None
            return None
    
    def _try_get_sprite_set(
        self,
        category: SpriteCategory,
        sprite_id: str,
        variant: Optional[str] = None,
        frame_index: Optional[int] = None,
        sheet_row: Optional[int] = None,
        sheet_col: Optional[int] = None,
    ) -> Optional[pygame.Surface]:
        """
        Try to get sprite from sprite set (sheet or animation sequence).
        
        Returns sprite if found, None otherwise.
        """
        if self._sprite_set_manager is None:
            try:
                from .sprite_sets import SpriteSetManager
                self._sprite_set_manager = SpriteSetManager(self.sprite_root)
            except Exception as e:
                # Sprite sets not available, disable for future calls
                self.enable_sprite_sets = False
                return None
        
        # Check if this sprite_id has a sprite set registered
        if not self._sprite_set_manager.has_sprite_set(sprite_id):
            return None
        
        # Try to get from sprite set
        try:
            # Try animation sequence first (if frame_index provided)
            if frame_index is not None:
                sprite = self._sprite_set_manager.get_animation_frame(sprite_id, frame_index)
                if sprite:
                    return sprite
            
            # Try sprite sheet
            if sheet_row is not None and sheet_col is not None:
                sprite = self._sprite_set_manager.get_sprite_from_sheet(
                    sprite_id, row=sheet_row, col=sheet_col
                )
            elif frame_index is not None:
                sprite = self._sprite_set_manager.get_sprite_from_sheet(
                    sprite_id, frame_index=frame_index
                )
            else:
                # Default: get first frame/sprite
                sprite = self._sprite_set_manager.get_sprite_from_sheet(sprite_id, frame_index=0)
                if not sprite:
                    sprite = self._sprite_set_manager.get_animation_frame(sprite_id, 0)
            
            if sprite:
                # Mark sprite from sprite set as real (not fallback)
                sprite._sprite_is_fallback = False  # type: ignore
            return sprite
        except Exception:
            # Sprite set loading failed, fall back to regular loading
            return None
    
    def _get_sprite_path(
        self,
        category: SpriteCategory,
        sprite_id: str,
        variant: Optional[str] = None,
    ) -> Optional[Path]:
        """
        Build the file path for a sprite.
        
        File naming convention:
        - Base: sprites/{category}/{sprite_id}.png
        - Variant: sprites/{category}/{sprite_id}_{variant}.png
        
        Examples:
        - sprites/entity/player.png
        - sprites/entity/enemy_goblin.png
        - sprites/item/sword_iron.png
        - sprites/tile/floor.png
        
        Performance: Uses file existence cache to avoid repeated file system I/O.
        """
        # Check cache first
        cache_key = (category, sprite_id, variant)
        if cache_key in self._file_existence_cache:
            return self._file_existence_cache[cache_key]
        
        category_dir = self.sprite_root / category.value
        
        # Build filename
        if variant:
            filename = f"{sprite_id}_{variant}.png"
        else:
            filename = f"{sprite_id}.png"
        
        file_path = category_dir / filename
        
        # Check if file exists, otherwise return None
        if file_path.exists():
            self._file_existence_cache[cache_key] = file_path
            return file_path
        
        # Try without variant if variant was provided
        if variant:
            file_path_no_variant = category_dir / f"{sprite_id}.png"
            if file_path_no_variant.exists():
                self._file_existence_cache[cache_key] = file_path_no_variant
                return file_path_no_variant
        
        # Cache the None result so we don't check again
        self._file_existence_cache[cache_key] = None
        return None
    
    def clear_cache(self) -> None:
        """Clear the sprite cache (useful for memory management or reloading)."""
        self._cache.clear()
        self._cache_metadata.clear()
        self._raw_sprite_cache.clear()
        self._tile_chunk_cache.clear()
        self._file_existence_cache.clear()
        self._missing_sprites.clear()
        
        # Also clear sprite set cache if available
        if self._sprite_set_manager:
            self._sprite_set_manager.clear_cache()
    
    def get_tile_chunk(
        self,
        chunk_x: int,
        chunk_y: int,
        zoom_level: int = 1,
        tile_data: Optional[List[List]] = None,
    ) -> Optional[pygame.Surface]:
        """
        Get a cached tile chunk (16x16 tiles).
        
        This is a placeholder for future optimization.
        When implemented, this will render a 16x16 chunk of tiles once
        and cache it for faster redrawing.
        
        Args:
            chunk_x: Chunk X coordinate
            chunk_y: Chunk Y coordinate
            zoom_level: Current zoom level (for cache key)
            tile_data: Optional tile data to render (if not cached)
            
        Returns:
            pygame.Surface with the tile chunk, or None if not available
        """
        cache_key = (chunk_x, chunk_y, zoom_level)
        
        if cache_key in self._tile_chunk_cache:
            return self._tile_chunk_cache[cache_key]
        
        # TODO: Implement chunk rendering
        # For now, return None to indicate chunks not yet implemented
        return None
    
    def clear_tile_chunk_cache(self) -> None:
        """Clear tile chunk cache (useful when map changes)."""
        self._tile_chunk_cache.clear()
    
    def is_sprite_fallback(self, sprite: pygame.Surface) -> bool:
        """
        Check if a sprite surface is a fallback (placeholder) or a real loaded sprite.
        
        Args:
            sprite: Sprite surface to check
            
        Returns:
            True if sprite is a fallback, False if it's a real sprite
        """
        return getattr(sprite, '_sprite_is_fallback', True)  # Default to True if attribute missing
    
    def preload_sprites(self, sprite_list: list[Tuple[SpriteCategory, str, Optional[str]]]) -> None:
        """
        Preload a list of sprites into cache.
        
        Args:
            sprite_list: List of (category, sprite_id, variant) tuples
        """
        for category, sprite_id, variant in sprite_list:
            self.get_sprite(category, sprite_id, variant)
    
    def get_sprite_set_manager(self):
        """Get the sprite set manager (lazy-loaded)."""
        if self._sprite_set_manager is None:
            try:
                from .sprite_sets import SpriteSetManager
                self._sprite_set_manager = SpriteSetManager(self.sprite_root)
            except Exception as e:
                print(f"Warning: Failed to initialize sprite set manager: {e}")
                self.enable_sprite_sets = False
                return None
        return self._sprite_set_manager


# Global sprite manager instance
_sprite_manager: Optional[SpriteManager] = None


def get_sprite_manager() -> SpriteManager:
    """Get the global sprite manager instance."""
    global _sprite_manager
    if _sprite_manager is None:
        _sprite_manager = SpriteManager()
    return _sprite_manager


def init_sprite_manager(sprite_root: Optional[Union[str, Path]] = None) -> SpriteManager:
    """
    Initialize the global sprite manager with a custom root directory.
    
    Args:
        sprite_root: Root directory for sprites
        
    Returns:
        The initialized SpriteManager instance
    """
    global _sprite_manager
    _sprite_manager = SpriteManager(sprite_root)
    return _sprite_manager

