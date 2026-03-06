# Brief: Autonomous Investment Loop

**Branch:** brief-010-autonomous-investment
**Model:** sonnet

## Goal

Update the simple-loop prompts and goals so the conductor/worker autonomously manage a portfolio — proposing hypotheses, spending credits to validate APIs, wrapping winners, tracking revenue, and killing underperformers. This is the brief that makes the agent an investor.

## Context

Read these before starting:
- `docs/specs/09-autonomous-portfolio.md` — full spec, especially "Updated Scout Loop" and "Updated Worker Loop"
- `src/portfolio.py` — PortfolioManager class
- `.loop/prompts/conductor.md` — current conductor prompt (needs portfolio awareness)
- `.loop/prompts/worker.md` — current worker prompt (needs spend/earn tracking)
- `.loop/state/goals.md` — current goals (needs updating for portfolio phase)
- `src/services.py` — where new services get added (worker writes here)
- `src/gateway.py` — gateway /health endpoint (worker reads this for demand signals)

## Tasks

1. **Update `.loop/state/goals.md` — new priority.** Replace current goals with portfolio-driven goals:
   ```
   ## Current Priority

   **Autonomous portfolio management.** The agent has a 50-credit budget.
   Goal: maximize ROI by discovering, validating, and wrapping APIs that buyers want.

   ## Done Looks Like

   - Portfolio has 3+ hypotheses (some validated, some earning)
   - At least 1 new service wrapped autonomously based on demand signals
   - Portfolio shows positive ROI (earned > spent)
   - Underperforming services identified (zero revenue after 1hr)
   - data/portfolio.json has real P&L entries
   ```

2. **Update `.loop/prompts/conductor.md` — add portfolio awareness.** Add a new section after "Step 1: Read State" that includes reading portfolio state. The conductor should:
   - Read `data/portfolio.json` (or run `python -c "from src.portfolio import PortfolioManager; import json; print(json.dumps(PortfolioManager().get_summary(), indent=2))"`)
   - Read gateway health: `curl -s https://beneficial-essence-production-99c7.up.railway.app/health | python -m json.tool` for demand signals and surge data
   - In assessment: consider portfolio balance, active hypotheses, revenue trends
   - When dispatching briefs: prefer opportunities where `should_invest()` returns True
   - Add a new assessment case: "Portfolio review needed?" — if any hypothesis has been in "wrapped" status for >1hr with zero actual_revenue, consider a KILL or REPRICE brief
   - When writing briefs for the worker, include the hypothesis ID so the worker can update it

3. **Update `.loop/prompts/worker.md` — add portfolio tracking.** Add instructions for the worker:
   - After reading state, also read `data/portfolio.json` for context
   - When the brief includes a hypothesis ID, update it via portfolio after completing work
   - When wrapping a new service: call `portfolio.spend()` for any validation costs, then `portfolio.update_hypothesis(hyp_id, "wrapped")` after successful wrap
   - When testing a service (self-buy via gateway): record as `portfolio.spend()`
   - Include example Python snippets the worker can use:
     ```python
     from src.portfolio import PortfolioManager
     p = PortfolioManager()
     p.spend(1, "service_id", "validation call")
     p.update_hypothesis("hyp-001", "validated")
     ```

4. **Update `.loop/knowledge/learnings.md` — add portfolio patterns.** Add a section with practical guidance:
   - How to read demand signals from /health
   - How to propose a hypothesis before wrapping
   - How to use should_invest() to gate spending
   - Gateway URL: https://beneficial-essence-production-99c7.up.railway.app
   - All handlers go in src/services.py, must be sync, return JSON string
   - Free APIs (no key) = 100% margin = best investment targets

## Completion Criteria

- [ ] `goals.md` updated with portfolio-driven priorities
- [ ] `conductor.md` reads portfolio state, considers ROI in dispatch decisions
- [ ] `worker.md` tracks spend/earn, updates hypotheses
- [ ] `learnings.md` has portfolio patterns section
- [ ] The prompts reference concrete file paths and Python snippets the agent can execute
- [ ] The conductor knows to kill underperformers and reinvest

## Verification

- Read all four updated files and confirm they form a coherent autonomous loop:
  conductor reads portfolio + health → dispatches brief with hypothesis → worker wraps + spends → gateway earns revenue → portfolio updates → conductor reviews
- No circular dependencies or missing file references
