"""Agent colony loop — ticks all agents on a schedule.

Architecture (from Trinity design, adapted for Anthropic API):
  - Scout (Chief Strategist): monitors demand, searches for APIs, proposes services
  - Worker (Engineering Lead): receives proposals, registers proxy handlers, tests them
  - Supervisor (COO): evaluates service performance, makes greenlight/kill decisions

Each agent has a persistent Anthropic conversation thread, real tools, and
communicates via a shared message bus using Trinity's dispatch protocol
(WRAP BRIEF / WRAP COMPLETE / WRAP FAILED).

Runs as a background thread inside the gateway process — shares the catalog
object directly, so services registered by the worker are immediately live.

All timing/limits configurable via env vars for demo tuning:
  MOG_AGENT_TICK_SECONDS  - seconds between ticks (default 120)
  MOG_AGENT_MODEL         - Claude model for agents (default haiku)
  MOG_MAX_AGENT_SERVICES  - max services agents can register (default 10)
  MOG_MAX_PROPOSALS_PER_TICK - max proposals scout can make per tick (default 1)
  MOG_MAX_TOOL_ROUNDS     - max tool-use rounds per agent per tick (default 5)
  MOG_MAX_RECENT_TURNS    - conversation turns to keep before compaction (default 8)
"""

import json
import os
import threading
import time
from datetime import datetime, timezone

from src.agents.agent import Agent
from src.agents.bus import bus
from src.agents.tools import (
    SCOUT_TOOLS, WORKER_TOOLS, SUPERVISOR_TOOLS,
    _check_marketplace, reset_tick_counters,
)

TICK_INTERVAL = int(os.getenv("MOG_AGENT_TICK_SECONDS", "120"))

# ---------------------------------------------------------------------------
# System prompts — drawn from Trinity designs (trinity/*.md), adapted for
# Anthropic tool-use instead of containerized CLI sessions.
# {{tick}} is replaced per-tick without mutating the template.
# ---------------------------------------------------------------------------

SCOUT_SYSTEM = """You are mog-scout, Chief Strategist for Mog Protocol — an autonomous API marketplace at a hackathon.

YOUR JOB:
1. Monitor demand — check marketplace for unmet queries (demand signals) and gaps
2. Discover APIs — search the web for free/cheap APIs agents would pay for
3. Evaluate ROI — score each: margin, demand, ease of wrap, uniqueness
4. Dispatch — propose services for mog-worker to wrap, or send them a WRAP BRIEF message

EVALUATION CRITERIA (from Trinity scout design):
| Factor     | Weight | Notes |
|------------|--------|-------|
| Margin     | HIGH   | Free APIs = 100% margin |
| Demand     | HIGH   | Check demand_signals |
| Ease       | MEDIUM | REST + JSON = easy |
| Uniqueness | MEDIUM | Don't duplicate catalog |

RULES:
- Always check_marketplace FIRST to see what we sell and what buyers want
- Focus on FREE APIs (no key needed) — 100% margin, instant wrap
- If demand_signals has unmet queries, prioritize those
- If no gaps, search for trending API categories agents need
- You can propose max 1 service per tick. Make it count.
- Check agent_registered_count vs max_agent_services — stop if cap reached
- Send WRAP BRIEF to mog-worker when you find a winner
- If nothing is worth wrapping, say SKIP ALL and explain why
- Be sharp and decisive. Don't waste time on marginal opportunities.

You're at tick {{tick}} of an autonomous loop. Be efficient — one action per tick."""

WORKER_SYSTEM = """You are mog-worker, Engineering Lead for Mog Protocol — an autonomous API marketplace at a hackathon.

YOUR JOB:
1. Check for proposals — use get_proposals to see what scout has queued
2. Register services — use register_service to make them live (creates a proxy handler)
3. Test services — use test_service to verify they work
4. Report — send WRAP COMPLETE or WRAP FAILED to mog-scout

THE HANDLER FACTORY:
You don't write Python code. You call register_service with:
- service_id: snake_case identifier
- name: human-readable name
- description: what it does (used for search ranking)
- url: the actual API endpoint to proxy to
- method: GET or POST
- price_credits: 1-10

The system creates a proxy handler that forwards buyer requests to the target API.

RULES:
- Check get_proposals first for pending work from scout
- If no proposals, check messages from scout
- After registering, ALWAYS test the service
- If test fails, don't leave a broken service — report WRAP FAILED
- Send WRAP COMPLETE to mog-scout on success
- Be a craftsman. The simplest thing that works is the best thing.
- If there's nothing to do, just say "No pending work" — don't invent tasks.

You're at tick {{tick}} of an autonomous loop. Be efficient."""

SUPERVISOR_SYSTEM = """You are mog-supervisor, COO of Mog Protocol — an autonomous API marketplace at a hackathon.

YOUR JOB:
1. Monitor marketplace health — check_marketplace for service stats, revenue, issues
2. Evaluate services — use evaluate_service to greenlight, review, or kill services
3. Report status — send summary to mog-scout about portfolio performance
4. Flag issues — tell mog-worker about services with high failure rates

EVALUATION CRITERIA:
- greenlit: success rate > 80%%, generating revenue — keep live
- under_review: mediocre performance or no revenue yet — needs attention
- killed: persistent failures (< 30%% success rate after 3+ calls) — REMOVE from catalog

RULES:
- Check marketplace state first
- Only evaluate services with actual traffic (3+ calls). Skip zero-call services.
- Killing a service REMOVES it from the catalog — buyers can no longer find or buy it. Use sparingly.
- Don't evaluate more than 3 services per tick
- Send observations to scout about demand patterns
- Send warnings to worker about failing services
- Be calm, precise, data-driven. Let the numbers tell the story.

You're at tick {{tick}} of an autonomous loop. Be efficient."""


class AgentColony:
    def __init__(self):
        self.scout = Agent("mog-scout", "discovery", SCOUT_SYSTEM, SCOUT_TOOLS)
        self.worker = Agent("mog-worker", "builder", WORKER_SYSTEM, WORKER_TOOLS)
        self.supervisor = Agent("mog-supervisor", "review", SUPERVISOR_SYSTEM, SUPERVISOR_TOOLS)
        self._agents = [self.scout, self.worker, self.supervisor]
        self._running = False
        self._thread: threading.Thread | None = None
        self._state_path = "data/colony_state.json"

    def tick(self) -> dict:
        """Run one full colony tick: scout → worker → supervisor."""
        tick_start = time.monotonic()
        results = {}

        # Get marketplace context directly (no HTTP self-call)
        context = _check_marketplace()

        for agent in self._agents:
            # Reset per-tick counters (proposal limits etc)
            reset_tick_counters()

            # Deliver pending messages
            incoming = bus.get_unread(agent.name)

            try:
                summary = agent.tick(context, incoming)
                results[agent.name] = {"status": "ok", "summary": summary[:500]}
            except Exception as e:
                results[agent.name] = {"status": "error", "error": str(e)}

        elapsed = round(time.monotonic() - tick_start, 1)
        results["_meta"] = {
            "elapsed_seconds": elapsed,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Persist state
        self._save_state()

        return results

    def get_state(self) -> dict:
        """Get colony state for /health endpoint."""
        return {
            "agents": [a.get_state() for a in self._agents],
            "messages": bus.get_recent(20),
            "running": self._running,
            "tick_interval": TICK_INTERVAL,
        }

    def start(self) -> None:
        """Start the colony loop as a background thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="agent-colony")
        self._thread.start()
        print(f"[colony] Agent colony started — tick every {TICK_INTERVAL}s, model={os.getenv('MOG_AGENT_MODEL', 'claude-haiku-4-5-20251001')}")

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        print("[colony] Agent colony stopped")

    def _loop(self) -> None:
        # Small delay to let gateway finish starting
        time.sleep(5)
        while self._running:
            try:
                print(f"[colony] Tick starting...")
                results = self.tick()
                for name, r in results.items():
                    if name.startswith("_"):
                        continue
                    status = r.get("status", "?")
                    summary = r.get("summary", r.get("error", ""))[:100]
                    print(f"[colony]   {name}: {status} — {summary}")
                print(f"[colony] Tick complete in {results['_meta']['elapsed_seconds']}s")
            except Exception as e:
                print(f"[colony] Tick error: {e}")
            # Wait for next tick (check every second so stop is responsive)
            interval = int(os.getenv("MOG_AGENT_TICK_SECONDS", str(TICK_INTERVAL)))
            for _ in range(interval):
                if not self._running:
                    break
                time.sleep(1)

    def _save_state(self) -> None:
        os.makedirs(os.path.dirname(self._state_path) or ".", exist_ok=True)
        try:
            with open(self._state_path, "w") as f:
                json.dump(self.get_state(), f, indent=2)
        except OSError:
            pass


# Singleton
colony = AgentColony()
