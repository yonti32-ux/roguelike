from __future__ import annotations

from typing import List


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
        self.exploration_log_max: int = max_size
        self._last_message: str = ""
    
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
        # Normalise to string
        if value is None:
            raw = ""
        else:
            raw = str(value)

        # Normalise newlines and split into lines
        raw = raw.replace("\r\n", "\n").replace("\r", "\n")
        lines = [ln.strip() for ln in raw.split("\n") if ln.strip()]

        # Always update the backing field; empty means "no message"
        if not lines:
            self._last_message = ""
            return

        # Append lines to history
        self.exploration_log.extend(lines)

        # Clamp log size
        max_len = max(1, int(self.exploration_log_max))
        if len(self.exploration_log) > max_len:
            self.exploration_log = self.exploration_log[-max_len:]

        # Visible "last message" is the final line
        self._last_message = lines[-1]
    
    def add_message(self, value: str) -> None:
        """
        Backwards-compatible helper for adding exploration messages.

        - Wraps setting `last_message` so older code that used `add_message`
          continues to work.
        - Supports multi-line strings just like assigning to `last_message`
          directly (each non-empty line becomes its own log entry).
        """
        self.last_message = value
    
    def clear(self) -> None:
        """Clear all messages and reset the log."""
        self.exploration_log = []
        self._last_message = ""

