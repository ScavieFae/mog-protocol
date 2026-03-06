# Goals

Autonomous API marketplace for the Nevermined Autonomous Business Hackathon.

## Current Priority

**Autonomous portfolio management + revenue tracking.** Four briefs queued in order:

1. **brief-007-portfolio-core** — PortfolioManager class (budget, hypotheses, P&L). Must land first.
2. **brief-008-fix-fx-wire-services** — Fix async FX handler, verify all 12 services work.
3. **brief-009-gateway-revenue** — Wire portfolio into gateway (record_sale on buy_and_call, portfolio in /health).
4. **brief-010-autonomous-investment** — Update conductor/worker prompts for portfolio-aware autonomous loop.

Execute in order. Each brief depends on the previous.

## Done Looks Like

- `src/portfolio.py` exists with tested PortfolioManager
- All 12 services sync, returning JSON strings, registered in catalog
- Gateway records revenue to portfolio on every sale
- `/health` includes portfolio summary (balance, ROI, top earner)
- Conductor reads portfolio + demand signals, dispatches investment briefs
- Worker tracks spend/earn, updates hypotheses
- The autonomous loop can run overnight and make money

## Constraints

- Demo is Friday 5:30 PM. Everything must be stable by noon Friday.
- Portfolio is JSON-on-disk (`data/portfolio.json`), not a database.
- Starting budget: 50 credits (configurable via `MOG_STARTING_CREDITS`).
- All services in `src/services.py`. Gateway picks them up automatically.

Read `docs/specs/09-autonomous-portfolio.md` for full architecture.
