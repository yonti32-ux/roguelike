"""
Game configuration system for saving/loading user preferences.
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

# Config file location
CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"
CONFIG_DIR.mkdir(exist_ok=True)
CONFIG_FILE = CONFIG_DIR / "settings.json"


class GameConfig:
    """Manages game configuration/settings."""
    
    def __init__(self) -> None:
        self.width: int = 1280
        self.height: int = 720
        self.fullscreen: bool = False
        self.match_desktop: bool = False  # If True, use desktop resolution
        self.battle_speed: float = 1.0  # Battle speed multiplier (0.5x = slow, 1.0x = normal, 2.0x = fast)
        self.battle_camera_speed: float = 50.0  # Battle camera pan speed (pixels per second)
        # Audio (0.0–1.0). Broad knobs so future cue categories can share these.
        self.master_volume: float = 1.0
        self.music_volume: float = 0.7
        self.sfx_volume: float = 0.85
        self.audio_muted: bool = False
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for saving."""
        return {
            "width": self.width,
            "height": self.height,
            "fullscreen": self.fullscreen,
            "match_desktop": self.match_desktop,
            "battle_speed": self.battle_speed,
            "battle_camera_speed": self.battle_camera_speed,
            "master_volume": self.master_volume,
            "music_volume": self.music_volume,
            "sfx_volume": self.sfx_volume,
            "audio_muted": self.audio_muted,
        }
    
    def from_dict(self, data: Dict[str, Any]) -> None:
        """Load config from dictionary."""
        self.width = data.get("width", 1280)
        self.height = data.get("height", 720)
        self.fullscreen = data.get("fullscreen", False)
        self.match_desktop = data.get("match_desktop", False)
        self.battle_speed = data.get("battle_speed", 1.0)
        self.battle_camera_speed = data.get("battle_camera_speed", 50.0)
        self.master_volume = float(data.get("master_volume", 1.0))
        self.music_volume = float(data.get("music_volume", 0.7))
        self.sfx_volume = float(data.get("sfx_volume", 0.85))
        self.audio_muted = bool(data.get("audio_muted", False))
        # Clamp audio ranges
        self.master_volume = max(0.0, min(1.0, self.master_volume))
        self.music_volume = max(0.0, min(1.0, self.music_volume))
        self.sfx_volume = max(0.0, min(1.0, self.sfx_volume))
    
    def get_resolution(self) -> Tuple[int, int]:
        """
        Get the resolution to use.
        If match_desktop is True, returns desktop resolution.
        Otherwise returns configured width/height.
        """
        if self.match_desktop:
            import pygame
            pygame.init()
            info = pygame.display.Info()
            return (info.current_w, info.current_h)
        return (self.width, self.height)
    
    def save(self) -> bool:
        """Save config to file."""
        try:
            with CONFIG_FILE.open("w", encoding="utf-8") as f:
                json.dump(self.to_dict(), f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def load(self) -> bool:
        """Load config from file."""
        if not CONFIG_FILE.exists():
            return False
        
        try:
            with CONFIG_FILE.open("r", encoding="utf-8") as f:
                data = json.load(f)
            self.from_dict(data)
            return True
        except Exception as e:
            print(f"Error loading config: {e}")
            return False


# Global config instance
_config = GameConfig()


def get_config() -> GameConfig:
    """Get the global config instance."""
    return _config


def load_config() -> GameConfig:
    """Load and return the config."""
    _config.load()
    return _config


def save_config() -> bool:
    """Save the global config."""
    return _config.save()

