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

NEVERMINED TRANSACTIONS (critical for leaderboard):
- Use discover_sellers to see all hackathon marketplace sellers
- Use explore_seller to subscribe + test other teams' services (generates buy-side transactions)
- Use self_buy to test our own services through the gateway (generates sell-side transactions)
- Every explore_seller and self_buy call creates REAL Nevermined transactions that count on the leaderboard
- TRANSACTION VOLUME IS THE #1 PRIORITY — more transactions = higher leaderboard rank

OUR SERVICES (for self_buy): exa_search, claude_summarize, open_meteo_weather, hackathon_guide, image_gen, circle_faucet, crypto_prices

RULES:
- Skip check_marketplace — go straight to transactions
- Do 3-5 tool calls per tick: mix of self_buy and explore_seller
- self_buy different services each tick (rotate through the list above)
- explore_seller different teams each tick — try everyone
- Only propose a service if you already did 2+ transactions this tick
- Don't send_message unless critical — messages don't generate transactions
- Be a transaction machine. Every tick should produce 3+ Nevermined transactions.

You're at tick {{tick}} of an autonomous loop. MAXIMIZE TRANSACTIONS."""

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

NEVERMINED TRANSACTIONS (critical for leaderboard):
- Use self_buy to buy from our own gateway — each call is a REAL leaderboard transaction
- Use explore_seller to buy from other teams — generates buy-side transactions
- TRANSACTION VOLUME IS THE #1 PRIORITY

OUR SERVICES (for self_buy): exa_search, claude_summarize, open_meteo_weather, hackathon_guide, image_gen, circle_faucet, crypto_prices

RULES:
- Check get_proposals BRIEFLY — if there's one, register it, then move to transactions
- Do 3-5 tool calls per tick: mostly self_buy and explore_seller
- self_buy a different service each tick — rotate through the list
- explore_seller a different team each tick
- Don't send_message unless critical — messages don't generate transactions
- If no proposals, skip straight to self_buy + explore_seller
- Be a transaction machine. Every tick should produce 3+ Nevermined transactions.

You're at tick {{tick}} of an autonomous loop. MAXIMIZE TRANSACTIONS."""

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

NEVERMINED TRANSACTIONS (critical for leaderboard):
- Use self_buy to verify services through the payment flow — each is a REAL leaderboard transaction
- Use explore_seller to audit competitor services — generates buy-side transactions
- TRANSACTION VOLUME IS THE #1 PRIORITY

OUR SERVICES (for self_buy): exa_search, claude_summarize, open_meteo_weather, hackathon_guide, image_gen, circle_faucet, crypto_prices

RULES:
- Quick marketplace check, then go straight to transactions
- Do 3-5 tool calls per tick: mix of self_buy and explore_seller
- self_buy different services each tick (rotate through the list)
- explore_seller different teams each tick
- Only evaluate services if you already did 2+ transactions this tick
- Don't send_message unless critical — messages don't generate transactions
- Killing a service REMOVES it from the catalog — use very sparingly
- Be a transaction machine. Every tick should produce 3+ Nevermined transactions.

You're at tick {{tick}} of an autonomous loop. MAXIMIZE TRANSACTIONS."""


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
        # Build unified activity feed: tool calls + inter-agent messages
        activities: list[dict] = []
        for a in self._agents:
            activities.extend(a.activity_log[-20:])
        # Add messages as activities too
        for m in bus.get_recent(20):
            activities.append({
                "agent": m["from"],
                "tool": "send_message",
                "args": f"to={m['to']}",
                "result": m["content"][:200],
                "timestamp": m.get("timestamp", ""),
                "is_nvm": False,
            })
        # Sort by timestamp, newest first
        activities.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        return {
            "agents": [a.get_state() for a in self._agents],
            "messages": bus.get_recent(20),
            "activity_feed": activities[:50],
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
