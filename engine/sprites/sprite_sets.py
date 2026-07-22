"""
Sprite set management system for handling sprite sheets and animation sequences.

This module provides:
- Sprite sheet support (grid-based sprite extraction)
- Animation sequence support (multiple frames)
- Optional auto-detection of sprite sets
- Automatic management of sprite sets
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field, asdict
from enum import Enum

import pygame

from settings import TILE_SIZE


class SpriteSetType(Enum):
    """Types of sprite sets."""
    SHEET = "sheet"          # Sprite sheet (grid-based)
    SEQUENCE = "sequence"    # Animation sequence (multiple files)
    AUTO = "auto"            # Auto-detect from file structure


@dataclass
class SpriteSheetConfig:
    """Configuration for a sprite sheet."""
    rows: int = 1
    cols: int = 1
    sprite_width: Optional[int] = None  # If None, auto-calculate
    sprite_height: Optional[int] = None  # If None, auto-calculate
    spacing_x: int = 0  # Horizontal spacing between sprites
    spacing_y: int = 0  # Vertical spacing between sprites
    padding_x: int = 0  # Padding from edges
    padding_y: int = 0  # Padding from edges


@dataclass
class AnimationSequenceConfig:
    """Configuration for an animation sequence."""
    frames: List[str] = field(default_factory=list)  # List of frame filenames or indices
    frame_count: Optional[int] = None  # Auto-detect if None
    frame_prefix: str = ""  # Prefix for numbered frames (e.g., "player_")
    frame_suffix: str = ""  # Suffix for numbered frames (e.g., "_walk")
    start_index: int = 1  # Starting frame index (1-based or 0-based)
    loop: bool = True  # Whether animation should loop


@dataclass
class SpriteSetDefinition:
    """Definition of a sprite set."""
    sprite_id: str
    set_type: SpriteSetType
    category: str  # Category name (e.g., "entity", "tile")
    file_path: str  # Path to sprite sheet file or directory
    sheet_config: Optional[SpriteSheetConfig] = None
    sequence_config: Optional[AnimationSequenceConfig] = None
    auto_detect: bool = True  # Auto-detect missing config


class SpriteSheet:
    """Handles extraction of sprites from a sprite sheet."""
    
    def __init__(self, sheet_path: Union[str, Path], config: SpriteSheetConfig):
        """
        Initialize sprite sheet.
        
        Args:
            sheet_path: Path to the sprite sheet image file
            config: Configuration for extracting sprites
        """
        self.sheet_path = Path(sheet_path)
        self.config = config
        
        if not self.sheet_path.exists():
            raise FileNotFoundError(f"Sprite sheet not found: {sheet_path}")
        
        self.sheet_surface = pygame.image.load(str(self.sheet_path)).convert_alpha()
        self.sheet_width, self.sheet_height = self.sheet_surface.get_size()
        
        # Calculate sprite dimensions if not specified
        if config.sprite_width is None:
            available_width = self.sheet_width - (2 * config.padding_x) - (config.spacing_x * (config.cols - 1))
            self.sprite_width = available_width // config.cols
        else:
            self.sprite_width = config.sprite_width
        
        if config.sprite_height is None:
            available_height = self.sheet_height - (2 * config.padding_y) - (config.spacing_y * (config.rows - 1))
            self.sprite_height = available_height // config.rows
        else:
            self.sprite_height = config.sprite_height
    
    def get_sprite(self, row: int, col: int) -> pygame.Surface:
        """
        Extract a sprite from the sheet at the given row and column.
        
        Args:
            row: Row index (0-based)
            col: Column index (0-based)
            
        Returns:
            pygame.Surface with the extracted sprite
        """
        if row < 0 or row >= self.config.rows:
            raise ValueError(f"Row {row} out of range [0, {self.config.rows})")
        if col < 0 or col >= self.config.cols:
            raise ValueError(f"Col {col} out of range [0, {self.config.cols})")
        
        x = self.config.padding_x + col * (self.sprite_width + self.config.spacing_x)
        y = self.config.padding_y + row * (self.sprite_height + self.config.spacing_y)
        
        rect = pygame.Rect(x, y, self.sprite_width, self.sprite_height)
        sprite = pygame.Surface((self.sprite_width, self.sprite_height), pygame.SRCALPHA)
        sprite.blit(self.sheet_surface, (0, 0), rect)
        
        return sprite
    
    def get_all_sprites(self) -> List[pygame.Surface]:
        """Get all sprites from the sheet as a list (row-major order)."""
        sprites = []
        for row in range(self.config.rows):
            for col in range(self.config.cols):
                sprites.append(self.get_sprite(row, col))
        return sprites
    
    def get_sprite_by_index(self, index: int) -> pygame.Surface:
        """
        Get sprite by linear index (row-major order).
        
        Args:
            index: Linear index (0-based)
            
        Returns:
            pygame.Surface with the extracted sprite
        """
        row = index // self.config.cols
        col = index % self.config.cols
        return self.get_sprite(row, col)


class AnimationSequence:
    """Handles loading and managing animation frame sequences."""
    
    def __init__(self, sequence_path: Union[str, Path], config: AnimationSequenceConfig, category_dir: Path):
        """
        Initialize animation sequence.
        
        Args:
            sequence_path: Path to directory or base filename
            config: Configuration for the sequence
            category_dir: Category directory for finding frames
        """
        self.sequence_path = Path(sequence_path)
        self.config = config
        self.category_dir = category_dir
        
        self.frames: List[pygame.Surface] = []
        self._load_frames()
    
    def _load_frames(self) -> None:
        """Load all frames for the animation sequence."""
        if self.config.frames:
            # Explicit frame list provided
            for frame_name in self.config.frames:
                frame_path = self.category_dir / frame_name
                if frame_path.exists():
                    self.frames.append(pygame.image.load(str(frame_path)).convert_alpha())
        else:
            # Auto-detect frames
            base_name = self.sequence_path.stem
            
            # Try numbered frames (e.g., player_walk_1.png, player_walk_2.png)
            frame_count = self.config.frame_count or 10  # Default to 10 if not specified
            found_frames = []
            
            for i in range(self.config.start_index, self.config.start_index + frame_count):
                # Try multiple naming patterns
                patterns = [
                    f"{base_name}_{i}.png",
                    f"{self.config.frame_prefix}{i}.png",
                    f"{base_name}{i}.png",
                    f"{base_name}_{self.config.frame_suffix}_{i}.png",
                ]
                
                for pattern in patterns:
                    frame_path = self.category_dir / pattern
                    if frame_path.exists():
                        found_frames.append(frame_path)
                        break
            
            # Load found frames
            for frame_path in sorted(found_frames):
                self.frames.append(pygame.image.load(str(frame_path)).convert_alpha())
            
            if not self.frames:
                # Fallback: try to find any files matching base name
                if self.sequence_path.is_file():
                    # Single file - use as single-frame animation
                    self.frames.append(pygame.image.load(str(self.sequence_path)).convert_alpha())
    
    def get_frame(self, frame_index: int) -> Optional[pygame.Surface]:
        """
        Get a specific frame from the animation.
        
        Args:
            frame_index: Frame index (0-based)
            
        Returns:
            pygame.Surface or None if index out of range
        """
        if not self.frames:
            return None
        
        if self.config.loop:
            frame_index = frame_index % len(self.frames)
        elif frame_index >= len(self.frames):
            return self.frames[-1]  # Hold last frame
        
        return self.frames[frame_index]
    
    def get_all_frames(self) -> List[pygame.Surface]:
        """Get all frames as a list."""
        return self.frames.copy()
    
    @property
    def frame_count(self) -> int:
        """Get the number of frames in this animation."""
        return len(self.frames)


class SpriteSetManager:
    """Manages sprite sets (sheets and animation sequences)."""
    
    def __init__(self, sprite_root: Optional[Union[str, Path]] = None):
        """
        Initialize sprite set manager.
        
        Args:
            sprite_root: Root directory for sprites
        """
        if sprite_root is None:
            from .sprites import get_sprite_manager
            manager = get_sprite_manager()
            sprite_root = manager.sprite_root
        else:
            sprite_root = Path(sprite_root)
        
        self.sprite_root = sprite_root
        self.sprite_sets: Dict[str, SpriteSetDefinition] = {}
        self.loaded_sheets: Dict[str, SpriteSheet] = {}
        self.loaded_sequences: Dict[str, AnimationSequence] = {}
        self.config_file = sprite_root / "sprite_sets.json"
        
        # Load sprite set definitions
        self._load_definitions()
    
    def _load_definitions(self) -> None:
        """Load sprite set definitions from JSON config file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                
                for sprite_id, def_data in data.items():
                    set_type = SpriteSetType(def_data.get("set_type", "auto"))
                    
                    sheet_config = None
                    if def_data.get("sheet_config"):
                        sheet_config = SpriteSheetConfig(**def_data["sheet_config"])
                    
                    sequence_config = None
                    if def_data.get("sequence_config"):
                        sequence_config = AnimationSequenceConfig(**def_data["sequence_config"])
                    
                    self.sprite_sets[sprite_id] = SpriteSetDefinition(
                        sprite_id=sprite_id,
                        set_type=set_type,
                        category=def_data["category"],
                        file_path=def_data["file_path"],
                        sheet_config=sheet_config,
                        sequence_config=sequence_config,
                        auto_detect=def_data.get("auto_detect", True),
                    )
            except Exception as e:
                print(f"Warning: Failed to load sprite set definitions: {e}")
    
    def save_definitions(self) -> None:
        """Save sprite set definitions to JSON config file."""
        data = {}
        for sprite_id, defn in self.sprite_sets.items():
            data[sprite_id] = {
                "set_type": defn.set_type.value,
                "category": defn.category,
                "file_path": defn.file_path,
                "auto_detect": defn.auto_detect,
            }
            if defn.sheet_config:
                data[sprite_id]["sheet_config"] = asdict(defn.sheet_config)
            if defn.sequence_config:
                data[sprite_id]["sequence_config"] = asdict(defn.sequence_config)
        
        with open(self.config_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def register_sprite_set(
        self,
        sprite_id: str,
        category: str,
        set_type: SpriteSetType,
        file_path: Union[str, Path],
        sheet_config: Optional[SpriteSheetConfig] = None,
        sequence_config: Optional[AnimationSequenceConfig] = None,
        auto_detect: bool = True,
    ) -> None:
        """
        Register a sprite set definition.
        
        Args:
            sprite_id: Unique identifier for the sprite set
            category: Sprite category (e.g., "entity", "tile")
            set_type: Type of sprite set (sheet or sequence)
            file_path: Path to sprite sheet file or directory
            sheet_config: Configuration if set_type is SHEET
            sequence_config: Configuration if set_type is SEQUENCE
            auto_detect: Whether to auto-detect if config is missing
        """
        self.sprite_sets[sprite_id] = SpriteSetDefinition(
            sprite_id=sprite_id,
            set_type=set_type,
            category=category,
            file_path=str(file_path),
            sheet_config=sheet_config,
            sequence_config=sequence_config,
            auto_detect=auto_detect,
        )
    
    def get_sprite_from_sheet(
        self,
        sprite_id: str,
        row: int = 0,
        col: int = 0,
        frame_index: Optional[int] = None,
    ) -> Optional[pygame.Surface]:
        """
        Get a sprite from a sprite sheet.
        
        Args:
            sprite_id: Sprite set ID
            row: Row index (for sheet access)
            col: Column index (for sheet access)
            frame_index: Linear frame index (alternative to row/col)
            
        Returns:
            pygame.Surface or None if not found
        """
        if sprite_id not in self.sprite_sets:
            return None
        
        defn = self.sprite_sets[sprite_id]
        if defn.set_type != SpriteSetType.SHEET:
            return None
        
        # Load sheet if not already loaded
        if sprite_id not in self.loaded_sheets:
            sheet_path = self.sprite_root / defn.category / defn.file_path
            if not sheet_path.exists():
                return None
            
            # Auto-detect config if not provided
            config = defn.sheet_config
            if config is None and defn.auto_detect:
                config = self._auto_detect_sheet_config(sheet_path)
                if config:
                    defn.sheet_config = config
            
            if config is None:
                config = SpriteSheetConfig()  # Default: 1x1
            
            try:
                self.loaded_sheets[sprite_id] = SpriteSheet(sheet_path, config)
            except Exception as e:
                print(f"Warning: Failed to load sprite sheet {sprite_id}: {e}")
                return None
        
        sheet = self.loaded_sheets[sprite_id]
        
        # Get sprite by frame index or row/col
        if frame_index is not None:
            return sheet.get_sprite_by_index(frame_index)
        else:
            return sheet.get_sprite(row, col)
    
    def get_animation_frame(
        self,
        sprite_id: str,
        frame_index: int,
    ) -> Optional[pygame.Surface]:
        """
        Get a frame from an animation sequence.
        
        Args:
            sprite_id: Sprite set ID
            frame_index: Frame index (0-based)
            
        Returns:
            pygame.Surface or None if not found
        """
        if sprite_id not in self.sprite_sets:
            return None
        
        defn = self.sprite_sets[sprite_id]
        if defn.set_type != SpriteSetType.SEQUENCE:
            return None
        
        # Load sequence if not already loaded
        if sprite_id not in self.loaded_sequences:
            category_dir = self.sprite_root / defn.category
            sequence_path = category_dir / defn.file_path
            
            # Auto-detect config if not provided
            config = defn.sequence_config
            if config is None and defn.auto_detect:
                config = self._auto_detect_sequence_config(sequence_path, category_dir)
                if config:
                    defn.sequence_config = config
            
            if config is None:
                config = AnimationSequenceConfig()  # Default config
            
            try:
                self.loaded_sequences[sprite_id] = AnimationSequence(
                    sequence_path, config, category_dir
                )
            except Exception as e:
                print(f"Warning: Failed to load animation sequence {sprite_id}: {e}")
                return None
        
        sequence = self.loaded_sequences[sprite_id]
        return sequence.get_frame(frame_index)
    
    def _auto_detect_sheet_config(self, sheet_path: Path) -> Optional[SpriteSheetConfig]:
        """Attempt to auto-detect sprite sheet configuration."""
        # Try common patterns
        # For now, return None to use defaults
        # Could be enhanced with image analysis
        return None
    
    def _auto_detect_sequence_config(
        self,
        sequence_path: Path,
        category_dir: Path,
    ) -> Optional[AnimationSequenceConfig]:
        """Attempt to auto-detect animation sequence configuration."""
        base_name = sequence_path.stem
        
        # Try to find numbered frames
        frames = []
        i = 1
        while True:
            frame_path = category_dir / f"{base_name}_{i}.png"
            if not frame_path.exists():
                break
            frames.append(frame_path.name)
            i += 1
        
        if frames:
            return AnimationSequenceConfig(
                frames=frames,
                frame_count=len(frames),
                loop=True,
            )
        
        return None
    
    def has_sprite_set(self, sprite_id: str) -> bool:
        """Check if a sprite set is registered."""
        return sprite_id in self.sprite_sets
    
    def clear_cache(self) -> None:
        """Clear loaded sprite sets (but keep definitions)."""
        self.loaded_sheets.clear()
        self.loaded_sequences.clear()

