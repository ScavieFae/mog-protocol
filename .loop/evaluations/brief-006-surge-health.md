# Evaluation: brief-006-surge-health

**Date:** 2026-03-05T23:55Z
**Branch:** brief-006-surge-health
**Verdict:** MERGE

## Summary

Brief asked for 2 tasks (continuation of stalled brief-005):
1. Wire surge pricing into gateway — **DONE**
2. Add /health endpoint — **DONE**

## What's Good

- `get_current_price()` correctly imported and used in both `_gateway_credits()` and `buy_and_call()`
- `surge_multiplier` added to `_meta` response
- `credits_charged` in txlog now uses dynamic price
- `/health` endpoint returns rich JSON: service count, service list with prices, recent transactions, demand signals
- Route manipulation approach (remove default oauth_router /health, add custom) is pragmatic and correct
- PORT handling preserved correctly (`PORT` -> `GATEWAY_PORT` -> `4000`)
- Clean 3-file diff (gateway.py + progress.json + diary), no regressions
- Worker captured useful learnings about FastAPI route manipulation

## Learnings from Worker

- `mcp._manager._fastapi_app` is the FastAPI app instance (available after `mcp.start()`)
- `app.router.routes` is a plain list — safe to filter+append after server start
- Default PaymentsMCP registers its own /health via oauth_router; must remove before adding custom

## Decision

MERGE. Both tasks complete, code is clean, no regressions from brief-005 issues.
