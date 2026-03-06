"""Portfolio manager: budget, investment hypotheses, and P&L tracking."""

import json
import os
import threading
from datetime import datetime, timezone


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class PortfolioManager:
    TERMINAL_STATES = {"killed", "earning"}

    def __init__(self, path: str = "data/portfolio.json", starting_credits: int | None = None):
        if starting_credits is None:
            starting_credits = int(os.environ.get("MOG_STARTING_CREDITS", 50))
        self._path = path
        self._starting_credits = starting_credits
        self._lock = threading.Lock()
        self._state = self._load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self) -> dict:
        if os.path.exists(self._path):
            try:
                with open(self._path) as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        return {
            "budget": {
                "starting_credits": self._starting_credits,
                "spent": 0,
                "earned": 0,
            },
            "hypotheses": [],
            "pnl": [],
        }

    def _save(self) -> None:
        os.makedirs(os.path.dirname(self._path) if os.path.dirname(self._path) else ".", exist_ok=True)
        with open(self._path, "w") as f:
            json.dump(self._state, f, indent=2)

    # ------------------------------------------------------------------
    # Budget
    # ------------------------------------------------------------------

    @property
    def balance(self) -> int:
        b = self._state["budget"]
        return b["starting_credits"] - b["spent"] + b["earned"]

    @property
    def roi(self) -> float:
        b = self._state["budget"]
        if b["spent"] == 0:
            return 0.0
        return (b["earned"] - b["spent"]) / b["spent"]

    def spend(self, credits: int, service_id: str, description: str) -> bool:
        with self._lock:
            if self.balance < credits:
                return False
            self._state["budget"]["spent"] += credits
            self._state["pnl"].append({
                "timestamp": _now(),
                "type": "cost",
                "service_id": service_id,
                "credits": credits,
                "description": description,
            })
            self._save()
            return True

    def earn(self, credits: int, service_id: str, description: str) -> None:
        with self._lock:
            self._state["budget"]["earned"] += credits
            self._state["pnl"].append({
                "timestamp": _now(),
                "type": "revenue",
                "service_id": service_id,
                "credits": credits,
                "description": description,
            })
            self._save()

    # ------------------------------------------------------------------
    # Hypotheses
    # ------------------------------------------------------------------

    def propose(self, service_id: str, thesis: str, expected_revenue: int, cost_to_validate: int) -> str:
        with self._lock:
            hyp_id = f"hyp-{len(self._state['hypotheses']) + 1:03d}"
            self._state["hypotheses"].append({
                "id": hyp_id,
                "service_id": service_id,
                "thesis": thesis,
                "expected_revenue": expected_revenue,
                "cost_to_validate": cost_to_validate,
                "cost_to_wrap": 0,
                "status": "proposed",
                "actual_revenue": 0,
                "created_at": _now(),
                "resolved_at": None,
            })
            self._save()
            return hyp_id

    def update_hypothesis(self, hyp_id: str, status: str, **kwargs) -> None:
        with self._lock:
            for hyp in self._state["hypotheses"]:
                if hyp["id"] == hyp_id:
                    hyp["status"] = status
                    hyp.update(kwargs)
                    self._save()
                    return

    def get_active_hypotheses(self) -> list:
        with self._lock:
            return [h for h in self._state["hypotheses"] if h["status"] not in self.TERMINAL_STATES]

    def get_best_performers(self, top_k: int = 3) -> list:
        with self._lock:
            return sorted(self._state["hypotheses"], key=lambda h: h.get("actual_revenue", 0), reverse=True)[:top_k]

    # ------------------------------------------------------------------
    # Revenue sync
    # ------------------------------------------------------------------

    def record_sale(self, service_id: str, credits_charged: int) -> None:
        self.earn(credits_charged, service_id, f"Sale: {service_id}")
        with self._lock:
            # Update the first non-terminal hypothesis for this service
            for hyp in self._state["hypotheses"]:
                if hyp["service_id"] == service_id:
                    hyp["actual_revenue"] = hyp.get("actual_revenue", 0) + credits_charged
                    self._save()
                    break

    # ------------------------------------------------------------------
    # Decision support
    # ------------------------------------------------------------------

    def should_invest(self, cost: int, expected_revenue: int) -> bool:
        return expected_revenue >= 2 * cost and self.balance >= cost

    def get_summary(self) -> dict:
        with self._lock:
            b = self._state["budget"]
            active = [h for h in self._state["hypotheses"] if h["status"] not in self.TERMINAL_STATES]
            earners = sorted(self._state["hypotheses"], key=lambda h: h.get("actual_revenue", 0), reverse=True)
            top_earner = earners[0]["service_id"] if earners else None
            spent = b["spent"]
            earned = b["earned"]
            return {
                "balance": b["starting_credits"] - spent + earned,
                "starting_credits": b["starting_credits"],
                "total_spent": spent,
                "total_earned": earned,
                "roi": (earned - spent) / spent if spent else 0.0,
                "active_hypotheses": len(active),
                "total_hypotheses": len(self._state["hypotheses"]),
                "top_earner": top_earner,
            }
