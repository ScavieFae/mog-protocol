"""Autonomous supervisor agent — evaluates live services and makes decisions.

Rules-based evaluation runs on every /health poll. Decisions:
  - greenlit: performing well, keep live
  - under_review: needs attention (low success rate, no revenue yet)
  - killed: not viable (persistent failures, zero usage after threshold)

The supervisor is deterministic — same telemetry yields same decisions — so it's
safe to run on every request without side effects.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Evaluation:
    service_id: str
    status: str  # "greenlit" | "under_review" | "killed" | "pending"
    reason: str
    metrics: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Supervisor:
    # Thresholds
    MIN_CALLS_FOR_REVIEW = 3       # Don't judge until N calls
    GREENLIT_SUCCESS_RATE = 0.80   # >80% success → greenlit
    KILL_SUCCESS_RATE = 0.30       # <30% success after enough calls → kill
    REVIEW_IDLE_MINUTES = 60       # No calls in 60 min → under review
    REVENUE_THRESHOLD = 0          # Must earn >0 to stay greenlit

    def __init__(self):
        self._overrides: dict[str, str] = {}  # manual status overrides
        self._kill_reasons: dict[str, str] = {}

    def override(self, service_id: str, status: str, reason: str = "") -> None:
        """Manual override from conductor or admin."""
        self._overrides[service_id] = status
        if reason:
            self._kill_reasons[service_id] = reason

    def evaluate_all(self, services: list, per_service_stats: dict) -> list[Evaluation]:
        """Evaluate all services given current telemetry stats.

        Args:
            services: list of ServiceEntry-like objects with service_id, name
            per_service_stats: dict of service_id -> stats dict with keys:
                total_calls, successful_calls, failed_calls, revenue_credits,
                first_seen, last_called
        """
        evaluations = []
        now = datetime.now(timezone.utc)

        for svc in services:
            sid = svc.service_id if hasattr(svc, "service_id") else svc.get("service_id", "")

            # Check for manual override
            if sid in self._overrides:
                reason = self._kill_reasons.get(sid, f"Manual override: {self._overrides[sid]}")
                evaluations.append(Evaluation(
                    service_id=sid,
                    status=self._overrides[sid],
                    reason=reason,
                ))
                continue

            stats = per_service_stats.get(sid)
            if not stats:
                evaluations.append(Evaluation(
                    service_id=sid,
                    status="pending",
                    reason="No calls yet — awaiting first buyer",
                    metrics={"total_calls": 0},
                ))
                continue

            total = stats.get("total_calls", 0)
            successful = stats.get("successful_calls", 0)
            failed = stats.get("failed_calls", 0)
            revenue = stats.get("revenue_credits", 0)
            success_rate = successful / total if total > 0 else 0.0
            last_called = stats.get("last_called", "")

            metrics = {
                "total_calls": total,
                "successful_calls": successful,
                "failed_calls": failed,
                "success_rate": round(success_rate, 3),
                "revenue_credits": revenue,
            }

            # Not enough data yet
            if total < self.MIN_CALLS_FOR_REVIEW:
                evaluations.append(Evaluation(
                    service_id=sid,
                    status="pending",
                    reason=f"Gathering data ({total}/{self.MIN_CALLS_FOR_REVIEW} calls)",
                    metrics=metrics,
                ))
                continue

            # Kill: persistent failures
            if success_rate < self.KILL_SUCCESS_RATE:
                evaluations.append(Evaluation(
                    service_id=sid,
                    status="killed",
                    reason=f"Success rate {success_rate:.0%} below {self.KILL_SUCCESS_RATE:.0%} threshold after {total} calls",
                    metrics=metrics,
                ))
                continue

            # Under review: mediocre success rate
            if success_rate < self.GREENLIT_SUCCESS_RATE:
                evaluations.append(Evaluation(
                    service_id=sid,
                    status="under_review",
                    reason=f"Success rate {success_rate:.0%} — needs improvement to reach {self.GREENLIT_SUCCESS_RATE:.0%}",
                    metrics=metrics,
                ))
                continue

            # Greenlit: good success rate and earning
            if revenue > self.REVENUE_THRESHOLD:
                evaluations.append(Evaluation(
                    service_id=sid,
                    status="greenlit",
                    reason=f"Performing well: {success_rate:.0%} success, {revenue}cr earned from {total} calls",
                    metrics=metrics,
                ))
            else:
                evaluations.append(Evaluation(
                    service_id=sid,
                    status="under_review",
                    reason=f"Good success rate ({success_rate:.0%}) but no revenue yet",
                    metrics=metrics,
                ))

        return evaluations

    def get_summary(self, evaluations: list[Evaluation]) -> dict:
        """Summary stats for the supervisor section of /health."""
        by_status: dict[str, int] = {}
        actions: list[str] = []
        for ev in evaluations:
            by_status[ev.status] = by_status.get(ev.status, 0) + 1
            if ev.status == "killed":
                actions.append(f"KILL {ev.service_id}: {ev.reason}")
            elif ev.status == "greenlit":
                actions.append(f"OK {ev.service_id}: {ev.reason}")
            elif ev.status == "under_review":
                actions.append(f"REVIEW {ev.service_id}: {ev.reason}")

        return {
            "counts": by_status,
            "total_evaluated": len(evaluations),
            "recent_actions": actions[:10],
            "evaluations": [
                {
                    "service_id": ev.service_id,
                    "status": ev.status,
                    "reason": ev.reason,
                    "metrics": ev.metrics,
                }
                for ev in evaluations
            ],
        }


# Singleton
supervisor = Supervisor()
