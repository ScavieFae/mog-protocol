# Back-Office Agent — Autonomous API Portfolio Manager

**Classification: DIFFERENTIATOR (the "autonomous business" the judges want to see)**

## What It Does

Runs as a simple-loop daemon. Discovers APIs via Exa, evaluates ROI, wraps profitable ones as gateway services, monitors revenue, kills underperformers, reinvests earnings. Each wrapped API is a mini business with its own P&L.

This is the layer that makes Mog an autonomous *business*, not an autonomous *wrapper*.

## Why Simple-Loop, Not a Skill

| | Skill (agents.md) | Harness (simple-loop) |
|---|---|---|
| Persistence | Dies with session | Runs indefinitely |
| Autonomy | Needs human to invoke | Self-directing |
| Budget tracking | Manual | Built into conductor |
| Recovery | None | Auto-retry, escalation |
| Demo value | "We ran this command" | "This has been running for 12 hours" |

The harness already works. The conductor/worker split maps to strategy/execution. The researcher agent template is a *tool the worker uses*, not a replacement for the loop.

## Architecture

```
Back-Office Daemon (simple-loop, separate instance from ScavieFae build daemon)
│
├── Conductor (every tick):
│   Reads: txlog revenue, catalog state, budget, demand signals, api-eval files
│   Decides: scout / evaluate / wrap / reprice / kill / idle
│   Writes: next brief for worker
│
├── Worker Briefs:
│   ├── SCOUT  — run Exa discovery, produce api-eval-*.md files
│   ├── WRAP   — generate handler code, add to catalog + services.py, self-test
│   ├── REPRICE — analyze txlog, adjust credits for a service
│   └── KILL   — remove underperforming service from catalog
│
└── State:
    ├── .loop/knowledge/api-eval-*.md    — structured API evaluations
    ├── .loop/knowledge/portfolio.json   — P&L per service
    └── .loop/state/backoffice.json      — budget, last scout, decisions
```

## The Budget Loop

The agent starts with a budget (e.g., 50 credits worth of operating cost, tracked internally — not Nevermined credits, but a virtual operating budget based on real costs).

```
Budget Categories:
  discovery:   Exa API calls to find candidate APIs (~$0.01/search)
  evaluation:  Claude calls to assess API quality (~$0.005/eval)
  wrapping:    Dev time + testing to generate handler (~$0.02/wrap)
  monitoring:  Periodic checks on revenue + health (~$0.001/check)

Revenue:
  Each buy_and_call through the gateway earns credits.
  Gateway txlog tracks per-service earnings.

ROI Decision:
  "I spent 3 credits discovering and wrapping weather-api.
   It's earned 12 credits in 4 hours from 8 buyers.
   ROI = 4x. Keep it, consider raising price."

  "I spent 5 credits wrapping pdf-extract.
   Zero buyers in 6 hours.
   ROI = -100%. Kill it, reclaim catalog slot."
```

## Conductor Decision Tree

```python
def decide_next_action(state):
    # 1. Any demand signals? (find_service queries with 0 results)
    unmet = get_unmet_demand()
    if unmet:
        return Brief("SCOUT", query=unmet[0], reason="unmet demand")

    # 2. Any evaluated APIs ready to wrap?
    ready = [e for e in get_evals() if e.recommendation == "wrap" and not e.wrapped]
    if ready and budget.can_afford("wrapping"):
        best = max(ready, key=lambda e: e.estimated_margin)
        return Brief("WRAP", api=best, reason=f"margin={best.estimated_margin}")

    # 3. Any underperformers to kill?
    losers = [s for s in portfolio if s.roi < -0.5 and s.age_hours > 2]
    if losers:
        return Brief("KILL", service=losers[0], reason=f"roi={losers[0].roi}")

    # 4. Time to scout? (every N minutes if budget allows)
    if time_since_last_scout() > 30 and budget.can_afford("discovery"):
        return Brief("SCOUT", query=next_scout_query(), reason="scheduled")

    # 5. Any services needing price adjustment?
    repriceables = [s for s in portfolio if s.needs_reprice()]
    if repriceables:
        return Brief("REPRICE", service=repriceables[0])

    return None  # idle
```

## Scout Brief (Worker)

Uses the researcher agent template. Worker runs Exa discovery with specific search strategies:

```
Search strategies (rotate):
  1. "REST API free tier" + category filter — find cheap-to-wrap APIs
  2. "OpenAPI specification {domain}" — find APIs with clean specs
  3. "{category} API documentation" — fill gaps in our catalog
  4. find_similar(existing_profitable_api) — find more of what works
```

Output: `.loop/knowledge/api-eval-{name}.md` with the structured assessment from the researcher template (upstream_cost, spec_quality, auth_model, margin, recommendation).

## Wrap Brief (Worker)

Given an api-eval that recommends wrapping:

1. Fetch API docs (Exa `get_contents` or WebFetch)
2. Write handler function in `src/services.py` pattern:
   ```python
   def _weather_search(location: str, days: int = 3) -> str:
       # call upstream API
       # return JSON result
   ```
3. Add `catalog.register(...)` call with handler
4. Self-test: call handler directly, verify JSON output
5. Update portfolio.json with new service entry

**Key constraint:** The worker doesn't modify gateway.py. It adds handlers to `src/services.py` and registers them in the catalog. The gateway's `buy_and_call` automatically picks up new catalog entries.

## Kill Brief (Worker)

1. Remove handler function from `src/services.py`
2. Remove `catalog.register()` call
3. Log reason in portfolio.json
4. Update diary

## Demand Signal Tracking

The gateway should log failed searches — queries where `find_service` returned 0 results or only low-relevance matches. This is the strongest demand signal.

```python
# In gateway.py find_service:
matches = catalog.search(query, budget=budget, top_k=5)
if not matches or all(score < 0.3 for score, _ in scored):
    txlog.log({
        "type": "unmet_demand",
        "query": query,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "matches_returned": len(matches),
    })
```

The conductor reads these and feeds them into scout queries.

## Portfolio State

```json
// .loop/knowledge/portfolio.json
{
  "services": {
    "exa_search": {
      "added_at": "2026-03-05T12:00:00Z",
      "upstream_cost_per_call": 0.01,
      "our_price_credits": 1,
      "total_calls": 15,
      "total_revenue_credits": 15,
      "total_upstream_cost": 0.15,
      "discovery_cost_credits": 0,
      "wrapping_cost_credits": 0,
      "roi": "infinity",
      "status": "active"
    },
    "weather_api": {
      "added_at": "2026-03-05T18:00:00Z",
      "upstream_cost_per_call": 0.005,
      "our_price_credits": 2,
      "total_calls": 0,
      "total_revenue_credits": 0,
      "total_upstream_cost": 0,
      "discovery_cost_credits": 1,
      "wrapping_cost_credits": 3,
      "roi": -1.0,
      "status": "active"
    }
  },
  "budget": {
    "initial": 50,
    "spent_discovery": 5,
    "spent_wrapping": 12,
    "earned": 22,
    "available": 55
  }
}
```

## Deployment: Git Worktree Isolation

The back-office daemon runs in a **git worktree** — a separate working directory backed by the same repository. This gives full filesystem isolation from ScavieFae's build daemon while sharing the same git history and remote.

### Why Worktrees

```
mog-protocol/          ← ScavieFae's build daemon lives here
  .loop/               ← ScavieFae's state, briefs, prompts
  src/                 ← shared codebase (same repo)

mog-backoffice/        ← Back-office daemon lives here (git worktree)
  .loop-backoffice/    ← back-office state, briefs, prompts
  src/                 ← same files, separate checkout
```

Two daemons, same repo, zero conflicts:
- Each has its own branch checkouts (worktrees can't share branches)
- Each has its own `.loop*` state directory
- Both push/pull to the same `origin` remote
- When back-office wraps a new API (adds to `src/services.py`), it commits and pushes — ScavieFae sees the change on next pull

### Setup

```bash
# From mog-protocol/:
git worktree add ../mog-backoffice main

# Creates ../mog-backoffice as a full working directory on main
# Shares .git storage — no extra disk, instant creation

cd ../mog-backoffice
cp ../mog-protocol/.env .env   # copy API keys

# The back-office has its own loop directory:
# .loop-backoffice/
#   config.sh
#   prompts/conductor.md
#   prompts/worker.md
#   state/running.json
#   state/progress.json
#   knowledge/portfolio.json
#   briefs/
#   logs/
```

### Running Locally vs Remote

**Local (same machine as ScavieFae):**
```bash
cd ../mog-backoffice
LOOP_DIR=.loop-backoffice bash lib/daemon.sh . 120
```

**Remote (Railway, VPS, etc.):**
```bash
git clone <repo> mog-backoffice && cd mog-backoffice
# Set env vars (Railway dashboard or .env file)
# Install: python3 -m venv .venv && pip install -r requirements.txt
# Auth: export ANTHROPIC_API_KEY=<for-claude-code-cli>
LOOP_DIR=.loop-backoffice bash lib/daemon.sh . 120
```

### Git Flow for Wrapped APIs

When the back-office wraps a new API:
1. Worker creates branch `backoffice/wrap-weather-api`
2. Adds handler to `src/services.py`, registers in catalog
3. Commits, pushes branch
4. Conductor evaluates, merges to main
5. ScavieFae's next `git pull` picks up the new service
6. Gateway automatically serves it (imports catalog at startup)

## Implementation Priority

1. **Demand signal logging** in gateway.py — 10 min, P0
2. **Portfolio state file** — schema + initial population from existing services — 15 min
3. **Conductor prompt** (conductor-backoffice.md) — decision tree, reads portfolio + txlog + demand signals — 30 min
4. **Scout brief template** — Exa discovery + api-eval output — 20 min
5. **Wrap brief template** — handler generation + catalog registration — 30 min
6. **Run it** — start the daemon, watch it discover and wrap — ongoing

Total bootstrap: ~2 hours to get the loop running. Then it's autonomous.

## Demo Value

"While we were presenting, our back-office agent discovered that 3 teams needed PDF extraction, wrapped a free PDF API, priced it at 2 credits, and earned 14 credits from 7 buyers. It also killed a weather service that nobody was buying. Here's the P&L."

This is the "autonomous business" story. The gateway is plumbing. The back-office agent is the brain.

## Open Questions

- **Budget units:** Virtual credits? USD equivalent? Simplest: just track Nevermined credits since that's what we earn and spend.
- **API key acquisition:** The agent can discover APIs but can't sign up for API keys. Either pre-load keys in .env, or the agent flags "need key for X" as an escalation to Mattie.
- **Concurrent daemons:** Two simple-loop instances on the same repo will fight over git state. Options: (a) separate loop dirs, (b) separate branches, (c) time-slice. Separate loop dirs is cleanest.
- **Wrapping quality:** Auto-generated handlers may be buggy. Self-test step is critical. If the handler fails self-test, the wrap brief fails and conductor can retry or skip.
