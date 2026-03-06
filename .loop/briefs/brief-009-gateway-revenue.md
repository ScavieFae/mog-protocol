# Brief: Gateway Revenue Tracking

**Branch:** brief-009-gateway-revenue
**Model:** sonnet

## Goal

Wire the PortfolioManager into the gateway so every successful `buy_and_call` records revenue, and the `/health` endpoint includes portfolio summary. This closes the loop: agents buy services, we earn credits, portfolio tracks it.

## Context

Read these before starting:
- `docs/specs/09-autonomous-portfolio.md` — full spec, especially "Revenue Flow" section
- `src/portfolio.py` — PortfolioManager class (created in brief-007)
- `src/gateway.py` — the gateway. `buy_and_call` at line ~77 handles purchases. `/health` at line ~152 returns marketplace state.

## Tasks

1. **Import and initialize PortfolioManager in gateway.py.** At module level (after other imports):
   ```python
   from src.portfolio import PortfolioManager
   portfolio = PortfolioManager()
   ```
   This loads existing state from `data/portfolio.json` or initializes fresh.

2. **Wire `portfolio.record_sale()` into `buy_and_call`.** After a successful handler call (the `try` block that calls `service.handler()`), add:
   ```python
   portfolio.record_sale(service_id, price)
   ```
   Only record on success — not on errors. `price` is the surge-adjusted price already computed. Place it right after the telemetry emit for successful calls.

3. **Add portfolio summary to `/health` response.** In the `_health()` function, add `portfolio.get_summary()` to the response dict:
   ```python
   "portfolio": portfolio.get_summary(),
   ```

4. **Test manually.** Start gateway locally (or just verify the import chain works):
   ```python
   python -c "from src.gateway import portfolio; print(portfolio.get_summary())"
   ```
   This will fail if NVM keys aren't set — that's OK. The import test is what matters. If gateway.py exits early on missing NVM keys, test the portfolio integration separately:
   ```python
   python -c "from src.portfolio import PortfolioManager; p = PortfolioManager(); p.record_sale('exa_search', 1); print(p.get_summary())"
   ```

## Completion Criteria

- [ ] PortfolioManager imported and initialized in gateway.py
- [ ] `buy_and_call` calls `portfolio.record_sale()` on success
- [ ] `/health` response includes `portfolio` key with summary
- [ ] No import errors in the chain

## Verification

- `python -c "from src.portfolio import PortfolioManager; p = PortfolioManager(); p.record_sale('test', 5); assert p.balance > 0"` passes
- Read gateway.py and confirm record_sale is in the success path only
