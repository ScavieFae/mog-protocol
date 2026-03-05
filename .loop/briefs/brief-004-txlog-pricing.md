# Brief: Transaction Log + Dynamic Pricing

**Branch:** brief-004-txlog-pricing
**Model:** sonnet

## Goal

Add transaction logging to every `buy_and_call` and wire up three-tier surge pricing. This completes Phase 2 (transaction logging) and delivers the Phase 3 pricing differentiator. Judges watch prices move as agents trade.

## Context

Read these before starting:
- `docs/specs/03-dynamic-pricing.md` — full pricing spec with surge tiers and data model
- `src/gateway.py` — current gateway with `buy_and_call` (needs tx logging + dynamic pricing)
- `src/services.py` — service registry with catalog
- `src/catalog.py` — ServiceCatalog with ServiceEntry dataclass

## Tasks

1. **Create `src/txlog.py` — transaction logger.** In-memory list with append + query. Each `buy_and_call` logs:
   ```python
   {
       "timestamp": "ISO 8601",
       "service_id": "exa_search",
       "price_charged": 1,
       "surge_multiplier": 1.0,
       "latency_ms": 420,
       "success": true
   }
   ```
   Methods needed:
   - `log(entry: dict)` — append
   - `count_calls(service_id: str, window_minutes: int = 15) -> int` — count calls in rolling window
   - `get_recent(n: int = 50) -> list[dict]` — for the future marketplace feed

2. **Create `src/pricing.py` — three-tier surge pricing.** Reads from txlog to determine current price:
   ```python
   def get_current_price(service_id: str, base_price: int) -> tuple[int, float]:
       """Returns (price, surge_multiplier)."""
       recent = txlog.count_calls(service_id, window_minutes=15)
       if recent >= 20:  # HIGH
           return int(base_price * 2.0), 2.0
       elif recent >= 10:  # MEDIUM
           return int(base_price * 1.5), 1.5
       else:
           return base_price, 1.0
   ```
   Thresholds should be configurable via env vars (`SURGE_THRESHOLD_HIGH=20`, `SURGE_THRESHOLD_MEDIUM=10`).

3. **Wire into gateway.** Modify `src/gateway.py`:
   - Import txlog and pricing
   - In `buy_and_call`: log every call (success or failure), include latency timing
   - In `_gateway_credits`: use `pricing.get_current_price()` instead of raw `service.price_credits`
   - In `find_service`: return current (surge-adjusted) prices, not base prices
   - Add a `_meta.surge_multiplier` field to `buy_and_call` response

4. **Test.** Create `src/test_pricing.py`:
   - Test txlog: log entries, verify count_calls with time window
   - Test pricing: mock different call counts, verify tier transitions
   - Test gateway integration: after N calls, price should increase

## Completion Criteria

- [ ] `src/txlog.py` exists with log(), count_calls(), get_recent()
- [ ] `src/pricing.py` exists with get_current_price()
- [ ] `src/gateway.py` logs all buy_and_call transactions and uses surge pricing
- [ ] `find_service` returns surge-adjusted prices
- [ ] `buy_and_call` response includes surge_multiplier in _meta
- [ ] `src/test_pricing.py` passes

## Verification

- `python -m src.test_pricing` passes
- Simulate 15 rapid calls → verify price doubles
