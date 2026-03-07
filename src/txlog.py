"""Persistent transaction log for buy_and_call events.

Writes each entry as a JSON line to a file on disk so telemetry survives
redeploys. Falls back to pure in-memory if the file can't be opened.
"""

import json
import os
from datetime import datetime, timezone

TXLOG_PATH = os.getenv("TXLOG_PATH", "data/txlog.jsonl")


class TransactionLog:
    def __init__(self, path: str = TXLOG_PATH):
        self._entries: list[dict] = []
        self._path = path
        self._file = None
        self._load()

    def _load(self) -> None:
        """Load existing entries from disk on startup."""
        try:
            os.makedirs(os.path.dirname(self._path) or ".", exist_ok=True)
            if os.path.exists(self._path):
                with open(self._path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                self._entries.append(json.loads(line))
                            except json.JSONDecodeError:
                                continue
                print(f"[txlog] Loaded {len(self._entries)} entries from {self._path}")
            self._file = open(self._path, "a")
        except Exception as exc:
            print(f"[txlog] Can't open {self._path}: {exc} — running in-memory only")
            self._file = None

    def log(self, entry: dict) -> None:
        """Append a transaction entry to memory and disk."""
        self._entries.append(entry)
        if self._file is not None:
            try:
                self._file.write(json.dumps(entry, default=str) + "\n")
                self._file.flush()
            except Exception:
                pass  # don't crash the gateway over a log write

    def count_calls(self, service_id: str, window_minutes: int = 15) -> int:
        """Count calls to service_id within a rolling window."""
        now = datetime.now(timezone.utc)
        cutoff = now.timestamp() - window_minutes * 60
        return sum(
            1
            for e in self._entries
            if e.get("service_id") == service_id
            and _parse_ts(e.get("timestamp", "")).timestamp() >= cutoff
        )

    def get_recent(self, n: int = 50) -> list[dict]:
        """Return the most recent n entries."""
        return list(self._entries[-n:])


def _parse_ts(ts: str) -> datetime:
    """Parse ISO 8601 timestamp string to datetime."""
    try:
        return datetime.fromisoformat(ts)
    except (ValueError, TypeError):
        return datetime.fromtimestamp(0, tz=timezone.utc)


# Module-level singleton used by gateway and pricing
txlog = TransactionLog()
