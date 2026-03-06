"""CLI viewer for recent toolkit traces from blockers + portfolio hypotheses.

Usage: python -m src.traces [--limit N]
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone


def _ago(ts: str) -> str:
    """Return human-readable time since ts (ISO format)."""
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        delta = datetime.now(timezone.utc) - dt
        s = int(delta.total_seconds())
        if s < 60:
            return f"{s}s ago"
        if s < 3600:
            return f"{s // 60}m ago"
        return f"{s // 3600}h ago"
    except Exception:
        return ts


def _load_json(path: str) -> object:
    if not os.path.exists(path):
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None


def main(limit: int = 10) -> None:
    traced = []

    # Blockers with traces
    blockers_data = _load_json("data/blockers.json") or []
    for b in blockers_data:
        if b.get("trace"):
            traced.append({
                "kind": "blocker",
                "label": f"{b.get('service_id', '?')} ({b.get('blocker_type', '?')}) {b.get('recommendation', '')}",
                "ts": b.get("created_at", ""),
                "trace": b["trace"],
            })

    # Portfolio hypotheses with validation_trace
    portfolio_data = _load_json("data/portfolio.json") or {}
    for h in portfolio_data.get("hypotheses", []):
        vt = h.get("validation_trace")
        if vt:
            traced.append({
                "kind": "hypothesis",
                "label": f"{h.get('service_id', '?')} ({h.get('status', '?')})",
                "ts": h.get("resolved_at") or h.get("created_at", ""),
                "trace": {"steps": vt, "step_count": len(vt), "operation": h.get("thesis", "")},
            })

    # Sort newest first
    traced.sort(key=lambda x: x["ts"], reverse=True)
    traced = traced[:limit]

    n_blockers = sum(1 for t in traced if t["kind"] == "blocker")
    n_hyps = sum(1 for t in traced if t["kind"] == "hypothesis")

    print("RECENT TRACES")
    print("\u2500" * 40)

    if not traced:
        print(f"0 traced operations")
        return

    for item in traced:
        t = item["trace"]
        steps = t.get("steps", [])
        step_count = t.get("step_count", len(steps))
        ago = _ago(item["ts"])
        print(f"\n[{item['kind']}] {item['label']} \u2014 {ago}, {step_count} steps")
        for step in steps[:5]:
            print(f"  {step}")
        if step_count > 5:
            print(f"  ... ({step_count - 5} more)")

    print(f"\n{len(traced)} traced operations ({n_blockers} blockers, {n_hyps} hypotheses)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="View recent toolkit traces")
    parser.add_argument("--limit", type=int, default=10, help="Max traces to show")
    args = parser.parse_args()
    main(limit=args.limit)
