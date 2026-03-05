"""In-memory transaction log for buy_and_call events."""

from datetime import datetime, timezone


class TransactionLog:
    def __init__(self):
        self._entries: list[dict] = []

    def log(self, entry: dict) -> None:
        """Append a transaction entry."""
        self._entries.append(entry)

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
