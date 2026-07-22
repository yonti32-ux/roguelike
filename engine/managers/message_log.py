from __future__ import annotations

from typing import List, Optional, Tuple

# Type alias for RGB colors used in UI rendering
Color = Tuple[int, int, int]

# ---------------------------------------------------------------------------
# Rarity → color helpers (used by exploration log to highlight item finds)
# ---------------------------------------------------------------------------

_RARITY_COLORS: dict[str, Color] = {
    "common": (200, 200, 200),
    "uncommon": (140, 210, 160),
    "rare": (140, 170, 240),
    "epic": (220, 140, 220),
    "legendary": (255, 210, 120),
}


def get_rarity_color(rarity: str) -> Optional[Color]:
    """
    Map an item rarity string to an RGB color.

    Returns None if the rarity is unknown, so callers can fall back
    to default text colors.
    """
    if not rarity:
        return None
    return _RARITY_COLORS.get(str(rarity).lower())


class MessageLog:
    """
    Manages exploration message history and the current last message.
    
    Features:
    - Stores message history (exploration_log)
    - Tracks the latest visible message (last_message)
    - Supports multi-line messages (each line becomes a log entry)
    - Automatically clamps log size to prevent memory bloat
    """
    
    def __init__(self, max_size: int = 60) -> None:
        """
        Initialize a new message log.
        
        Args:
            max_size: Maximum number of log entries to keep (default 60)
        """
        self.exploration_log: List[str] = []
        # Parallel list storing an optional color for each log entry.
        # If an entry is None, the UI will use its default text color.
        self.exploration_log_colors: List[Optional[Color]] = []

        self.exploration_log_max: int = max_size
        self._last_message: str = ""
        self._last_message_color: Optional[Color] = None

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    def _append_lines(
        self,
        lines: List[str],
        color: Optional[Color] = None,
    ) -> None:
        """
        Internal helper to append one or more log lines with an optional color.

        All lines in this batch share the same color, which is suitable for
        multi-line messages like XP breakdowns, etc.
        """
        if not lines:
            # No visible lines – treat as clearing last message.
            self._last_message = ""
            self._last_message_color = None
            return

        # Append text + colors
        self.exploration_log.extend(lines)
        self.exploration_log_colors.extend([color] * len(lines))

        # Clamp log size (keep most recent entries)
        max_len = max(1, int(self.exploration_log_max))
        if len(self.exploration_log) > max_len:
            overflow = len(self.exploration_log) - max_len
            self.exploration_log = self.exploration_log[-max_len:]
            if len(self.exploration_log_colors) >= overflow:
                self.exploration_log_colors = self.exploration_log_colors[-max_len:]
            else:
                # Defensive fallback if lengths ever got out of sync
                self.exploration_log_colors = [None] * len(self.exploration_log)

        # Visible "last message" is the final line in this batch
        self._last_message = lines[-1]
        self._last_message_color = color

    def add_entry(self, value: str, color: Optional[Color] = None) -> None:
        """
        Add a new exploration message, optionally with a specific text color.

        This is the preferred modern entry point – it supports:
        - Multi-line messages (each non-empty line becomes its own log entry)
        - Optional per-message color (used by the HUD if provided)
        """
        if value is None:
            raw = ""
        else:
            raw = str(value)

        # Normalise newlines and split into visible lines
        raw = raw.replace("\r\n", "\n").replace("\r", "\n")
        lines = [ln.strip() for ln in raw.split("\n") if ln.strip()]

        if not lines:
            # Treat empty/whitespace-only strings as "clear last message"
            self._last_message = ""
            self._last_message_color = None
            return

        self._append_lines(lines, color=color)
    
    @property
    def last_message(self) -> str:
        """
        Latest message shown in the bottom exploration band.
        Also mirrors the final line added to the exploration log.
        """
        return self._last_message
    
    @last_message.setter
    def last_message(self, value: str) -> None:
        """
        Set the latest message and append it to the exploration log.

        - Accepts any value, coerced to string.
        - Supports multi-line strings; each non-empty line becomes
          a distinct log entry.
        - The final line becomes the visible bottom-band message.
        """
        # Backwards-compatible: default to no special color.
        self.add_entry(value, color=None)

    @property
    def last_message_color(self) -> Optional[Color]:
        """Color associated with the latest message, if any."""
        return self._last_message_color
    
    def add_message(self, value: str) -> None:
        """
        Backwards-compatible helper for adding exploration messages.

        - Wraps setting `last_message` so older code that used `add_message`
          continues to work.
        - Supports multi-line strings just like assigning to `last_message`
          directly (each non-empty line becomes its own log entry).
        """
        # Kept for backwards compatibility – calls through to last_message,
        # which now supports multi-line messages and color metadata.
        self.last_message = value
    
    def clear(self) -> None:
        """Clear all messages and reset the log."""
        self.exploration_log = []
        self.exploration_log_colors = []
        self._last_message = ""
        self._last_message_color = None


