"""Telemetry wrapper — thin layer over txlog for gateway event emission."""

from datetime import datetime, timezone

from src.txlog import txlog


class TelemetryEvent:
    def __init__(self, event_type: str, **kwargs):
        self.event_type = event_type
        self.data = kwargs
        self.data["event_type"] = event_type
        self.data.setdefault("timestamp", datetime.now(timezone.utc).isoformat())


class Telemetry:
    def emit(self, event: TelemetryEvent) -> None:
        txlog.log(event.data)

    def count_calls(self, service_id: str, window_minutes: int = 15) -> int:
        return txlog.count_calls(service_id, window_minutes)

    def get_recent(self, n: int, event_type: str = None) -> list:
        entries = txlog.get_recent(max(n * 5, 50))
        if event_type is not None:
            entries = [e for e in entries if e.get("event_type") == event_type]
        return entries[-n:]

    def get_stats(self) -> dict:
        all_entries = txlog.get_recent(10000)
        total = len(all_entries)
        successful = sum(1 for e in all_entries if e.get("success"))
        revenue = sum(e.get("credits_charged", 0) for e in all_entries if e.get("credits_charged"))
        per_service: dict[str, int] = {}
        for e in all_entries:
            sid = e.get("service_id")
            if sid:
                per_service[sid] = per_service.get(sid, 0) + 1
        return {
            "total_calls": total,
            "successful_calls": successful,
            "success_rate": round(successful / total, 3) if total else 0.0,
            "total_credits_charged": revenue,
            "per_service": per_service,
        }


telemetry = Telemetry()
