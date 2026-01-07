"""
Centralized error handling and logging system.

This module provides:
- Centralized error logging to files
- User-friendly error messages
- Custom exception types for different error categories
- Error recovery mechanisms
"""
import logging
import traceback
from pathlib import Path
from typing import Optional, Callable
from datetime import datetime

# Setup logging directory
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Configure logger
logger = logging.getLogger("roguelike")
logger.setLevel(logging.DEBUG)

# Prevent duplicate handlers
if not logger.handlers:
    # File handler for detailed logs
    log_file = LOG_DIR / f"game_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )

    # Console handler for warnings/errors
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(
        logging.Formatter('%(levelname)s: %(message)s')
    )

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


class GameError(Exception):
    """Base exception for game-specific errors."""
    def __init__(self, message: str, user_message: Optional[str] = None):
        super().__init__(message)
        self.user_message = user_message or message


class SaveError(GameError):
    """Error during save/load operations."""
    pass


class BattleError(GameError):
    """Error during battle operations."""
    pass


class ValidationError(GameError):
    """Error when validation fails."""
    pass


# Global reference to debug console (set by game initialization)
_debug_console: Optional[object] = None


def set_debug_console(console: object) -> None:
    """Set the global debug console reference."""
    global _debug_console
    _debug_console = console


def log_error(
    error: Exception,
    context: str = "",
    user_message: Optional[str] = None,
    show_to_user: bool = False
) -> None:
    """
    Log an error with context information.
    
    Args:
        error: The exception that occurred
        context: Where the error occurred (e.g., "save_game", "battle_init")
        user_message: User-friendly message to display
        show_to_user: Whether to show message to player (requires game reference)
    """
    error_type = type(error).__name__
    error_msg = str(error)
    trace = traceback.format_exc()
    
    logger.error(
        f"Error in {context}: {error_type}: {error_msg}\n{trace}",
        exc_info=True
    )
    
    # Also log to debug console if available
    if _debug_console and hasattr(_debug_console, 'log_error'):
        try:
            _debug_console.log_error(error, context)
        except Exception:
            pass  # Don't let debug console errors break error logging
    
    if show_to_user and user_message:
        # Store for UI to display
        # This would need to be integrated with your message system
        pass


def handle_critical_error(
    error: Exception,
    context: str,
    game: Optional[object] = None,
    recovery_action: Optional[Callable] = None
) -> bool:
    """
    Handle a critical error that might crash the game.
    
    Args:
        error: The exception that occurred
        context: Where the error occurred
        game: Optional game reference to show messages
        recovery_action: Optional function to try for recovery
    
    Returns:
        True if error was handled, False if should re-raise
    """
    log_error(error, context, show_to_user=True)
    
    # Try recovery action if provided
    if recovery_action:
        try:
            recovery_action()
            logger.info(f"Recovery action executed for {context}")
            return True
        except Exception as recovery_error:
            log_error(recovery_error, f"{context}_recovery")
    
    # If game reference available, show error to player
    if game and hasattr(game, "add_message"):
        user_msg = f"An error occurred: {context}. Check logs for details."
        game.add_message(user_msg)
        return True
    
    return False

