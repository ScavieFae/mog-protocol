# Review: brief-013-surge-pricing-signals
Date: 2026-03-06

## Summary
Replaced the blunt 3-tier volume pricing in `src/pricing.py` with a multi-signal surge engine: demand_pressure (search-to-purchase ratio), velocity (5m vs 15m call rate), and cooldown (smooth 0.1x/2min decay). New `get_surge_info()` function returns full breakdown; `get_current_price()` delegates to it (backward compatible). Gateway `/health` now includes per-service surge_signals. Web: new `Ticker.tsx` with trend arrows, new `FlowerNode.tsx` with demand pressure dotted ring, new `useHealth.ts` hook with typed interfaces. 7 files changed, +428/-25. 7/7 tests pass.

## Checklist
- [PASS] Completion criteria met — all 6 criteria satisfied
- [PASS] Code quality acceptable — clean separation of signals, capped/floored, backward compatible API
- [PASS] Scope matches brief — exactly what was asked, no extras
- [PASS] Verification passes — `get_current_price` and `get_surge_info` work correctly, 7 tests pass
- [PASS] No unintended side effects — `get_current_price` signature unchanged, gateway tests pass

## Issues Found
- None blocking. Minor: cooldown uses floating-point time math but precision is fine for 2-minute granularity.

## Verdict
APPROVE
