# Brief: Surge Pricing — Richer Signals + Tracking + Display

**Branch:** brief-013-surge-pricing-signals
**Model:** sonnet

## Goal

Evolve surge pricing from a blunt 3-tier volume counter into a signal-aware pricing engine that reads demand, competition, and time patterns. Make surge state visible in `/health` and the website ticker.

## Context

Read these before starting:
- `src/pricing.py` — current surge: 3 tiers based on 15-min rolling call count
- `src/gateway.py` — where pricing is called (`_gateway_credits`, `buy_and_call`)
- `src/txlog.py` — transaction log (raw data for pricing signals)
- `src/telemetry.py` — telemetry layer (may have been created by brief-008)
- `web/src/components/Ticker.tsx` — ticker already shows surge multiplier
- `web/src/components/FlowerNode.tsx` — flowers already react to surge (color shift, pulse)
- `web/src/hooks/useHealth.ts` — health data types

## Tasks

1. **Enrich `src/pricing.py` with multi-signal surge.** Keep the existing `get_current_price()` signature but add richer inputs. New signals beyond raw call count:

   **Demand signal** — if `find_service` queries mention this service's keywords but nobody buys, that's latent demand. Price should hold or increase slightly (1.1x).
   ```python
   def _demand_pressure(service_id: str) -> float:
       """Ratio of searches that match this service vs actual purchases. >2.0 = high demand, low conversion."""
   ```

   **Velocity** — not just count, but rate of change. 5 calls in the last 2 minutes is hotter than 5 calls spread over 15 minutes.
   ```python
   def _velocity(service_id: str) -> float:
       """Calls per minute in last 5 min vs last 15 min. >1.5 = accelerating."""
   ```

   **Cooldown** — if a service was surging but traffic dropped, decay price gradually rather than cliff-dropping.
   ```python
   def _cooldown_multiplier(service_id: str, last_surge: float) -> float:
       """Smooth decay: if traffic drops from surge tier, step down 0.1x per 2 minutes rather than instant reset."""
   ```

   Combined formula (keep it simple):
   ```python
   base_multiplier = volume_tier()          # existing: 1.0 / 1.5 / 2.0
   demand_boost = min(_demand_pressure(), 1.2)  # cap at 1.2x
   velocity_boost = min(_velocity(), 1.3)        # cap at 1.3x
   cooldown = _cooldown_multiplier()             # 0.8-1.0 during decay
   final = base_multiplier * demand_boost * velocity_boost * cooldown
   return max(1.0, min(final, 3.0))  # floor 1.0, cap 3.0
   ```

   Store surge state per service in a module-level dict so cooldown works across calls:
   ```python
   _surge_state: dict[str, dict] = {}
   # {"exa_search": {"last_multiplier": 1.5, "last_updated": "...", "peak_multiplier": 2.0}}
   ```

2. **Expose surge data in `/health`.** Modify the health endpoint to include per-service surge info:
   ```python
   "services": [
       {
           "service_id": s.service_id,
           "name": s.name,
           "price_credits": s.price_credits,
           "current_price": current_price,       # surge-adjusted
           "surge_multiplier": multiplier,
           "surge_signals": {
               "volume_15m": call_count,
               "velocity": velocity_score,
               "demand_pressure": demand_score,
               "trend": "rising" | "falling" | "stable"
           }
       }
   ]
   ```
   This gives the website everything it needs to show live pricing.

3. **Update `useHealth.ts` types.** Add surge fields to the `Service` interface:
   ```typescript
   interface Service {
     // ...existing...
     current_price?: number
     surge_signals?: {
       volume_15m: number
       velocity: number
       demand_pressure: number
       trend: "rising" | "falling" | "stable"
     }
   }
   ```

4. **Update Ticker to show trend arrows.** In `Ticker.tsx`, next to the surge multiplier, show a trend indicator:
   - rising → thin upward arrow in rose
   - falling → thin downward arrow in sage
   - stable → no indicator
   Use `current_price` from health instead of computing it client-side.

5. **Update FlowerNode for demand pressure.** In `FlowerNode.tsx`, add a subtle visual for high demand pressure (searches but no buys): a dotted ring around the flower, indicating "people are looking for this." This signals opportunity without being noisy.

## Completion Criteria

- [ ] `src/pricing.py` has demand_pressure, velocity, and cooldown signals
- [ ] Surge multiplier is capped at 3.0x, floored at 1.0x
- [ ] `/health` returns per-service surge_signals with volume, velocity, demand, trend
- [ ] Ticker shows trend arrows
- [ ] FlowerNode shows demand pressure ring
- [ ] Cooldown prevents price cliff-drops

## Verification

- `python -c "from src.pricing import get_current_price; print(get_current_price('test', 1))"` works
- Read the /health response and confirm surge_signals is present per service
- Visual: ticker shows arrows when surge state changes
