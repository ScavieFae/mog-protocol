# Brief: Portfolio Manager Core

**Branch:** brief-007-portfolio-core
**Model:** sonnet

## Goal

Create `src/portfolio.py` — the PortfolioManager class that tracks agent budget, investment hypotheses, and P&L. This is the economic brain of the autonomous agent. JSON persistence to `data/portfolio.json`.

## Context

Read these before starting:
- `docs/specs/09-autonomous-portfolio.md` — full spec with data model and class API
- `src/gateway.py` — where revenue tracking will be wired (next brief)
- `src/pricing.py` — surge pricing, portfolio will read surge data
- `src/txlog.py` — reference for how we do JSON-based state (but portfolio uses a file, not in-memory)

## Tasks

1. **Create `src/portfolio.py` — PortfolioManager class.** Implement:
   - `__init__(path, starting_credits)` — load from JSON or initialize fresh. Default path `data/portfolio.json`, default credits from env `MOG_STARTING_CREDITS` or 50.
   - `spend(credits, service_id, description) -> bool` — deduct from balance, append to pnl, return False if insufficient funds.
   - `earn(credits, service_id, description)` — add to balance, append to pnl.
   - `balance` property — starting - spent + earned.
   - `roi` property — (earned - spent) / spent, or 0.0 if nothing spent.
   - `propose(service_id, thesis, expected_revenue, cost_to_validate) -> str` — create hypothesis with auto-incremented id, status="proposed", return id.
   - `update_hypothesis(hyp_id, status, **kwargs)` — update status and any extra fields (actual_revenue, resolved_at, etc).
   - `get_active_hypotheses()` — return hypotheses not in terminal states (killed, earning).
   - `get_best_performers(top_k=3)` — hypotheses sorted by actual_revenue descending.
   - `record_sale(service_id, credits_charged)` — convenience: calls earn() and updates hypothesis actual_revenue if one exists for this service.
   - `should_invest(cost, expected_revenue) -> bool` — True if expected_revenue >= 2 * cost AND balance >= cost.
   - `get_summary() -> dict` — dashboard-ready: budget breakdown, active hypotheses count, top earner, ROI.
   - `_save()` — write JSON to disk (called after every mutation).
   - `_load()` — read JSON from disk.
   - Use `threading.Lock` for thread safety (gateway is multi-threaded).

2. **Create `data/` directory with `.gitkeep`.** Portfolio file is gitignored (runtime state), but the directory should exist.

3. **Create `src/test_portfolio.py` — tests.** Test:
   - Fresh initialization: balance = starting_credits.
   - spend/earn: balance updates correctly.
   - spend over budget returns False, balance unchanged.
   - propose: creates hypothesis with correct fields.
   - record_sale: updates both pnl and hypothesis actual_revenue.
   - should_invest: True when affordable and ROI >= 2x, False otherwise.
   - JSON persistence: save, reload, verify state matches.
   - ROI calculation: 0 when nothing spent, correct ratio otherwise.

## Completion Criteria

- [ ] `src/portfolio.py` exists with PortfolioManager class
- [ ] All methods from spec implemented
- [ ] `data/` directory exists
- [ ] `src/test_portfolio.py` passes
- [ ] JSON round-trips correctly (save + load preserves state)

## Verification

- `python -m pytest src/test_portfolio.py -v` passes (or `python src/test_portfolio.py` if no pytest)
- Manually: `python -c "from src.portfolio import PortfolioManager; p = PortfolioManager(); print(p.get_summary())"`
