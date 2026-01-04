from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


def _now_iso() -> str:
    # ISO-ish without importing datetime (fast + good enough for logs)
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())


@dataclass
class TelemetryLogger:
    path: Optional[Path] = None
    enabled: bool = True
    flush_each_write: bool = False
    sample_every_n_frames: int = 10  # log 1 frame snapshot every N frames
    _frame_counter: int = 0
    _started_at: float = field(default_factory=time.time)

    def init(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Touch file (don’t overwrite)
        self.path.touch(exist_ok=True)
        self.log("telemetry_init", file=str(self.path))

    def log(self, event: str, **fields: Any) -> None:
        if not self.enabled or self.path is None:
            return

        row: Dict[str, Any] = {
            "t": time.time(),
            "ts": _now_iso(),
            "event": event,
            **fields,
        }

        try:
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
                if self.flush_each_write:
                    f.flush()
        except Exception:
            # Telemetry must never break the game.
            return

    def tick_frame(self) -> int:
        self._frame_counter += 1
        return self._frame_counter

    def should_log_frame(self) -> bool:
        return self.sample_every_n_frames > 0 and (self._frame_counter % self.sample_every_n_frames == 0)


# global singleton (easy import everywhere)
telemetry = TelemetryLogger()
