# Evaluation: brief-005-gateway-surge-deploy

**Date:** 2026-03-05T23:36Z
**Branch:** brief-005-gateway-surge-deploy
**Verdict:** FIX (do not merge)

## Summary

Brief asked for 3 tasks:
1. Wire surge pricing into gateway `_gateway_credits()` — **DONE** (correct)
2. Add `/health` endpoint — **NOT DONE**
3. Fix PORT binding for Railway — **REGRESSED** (removed `PORT` env var check; main already has the correct `PORT` → `GATEWAY_PORT` → `4000` fallback)

## What's Good

- `get_current_price()` correctly imported and used in both `_gateway_credits()` and `buy_and_call()`
- `surge_multiplier` added to `_meta` response
- `credits_charged` in txlog now uses dynamic price

## Issues

- Only 1 of 3 tasks completed
- PORT handling was made worse: branch reverts `os.getenv("PORT", os.getenv("GATEWAY_PORT", "4000"))` to just `os.getenv("GATEWAY_PORT", "4000")`. Main commit `8025712` already fixed this.
- Branch is behind main (diverged before pump, guides, open-meteo service were added). Merge would conflict on gateway.py.
- Progress.json shows iteration 0, no learnings — worker didn't properly track state.

## Decision

Do NOT merge. The surge pricing change is good but merging this branch risks:
1. Gateway.py merge conflict with the PORT fix on main
2. Missing the health endpoint entirely

Better approach: cherry-pick the surge pricing logic directly, or create a new brief from current main that only adds the health endpoint (surge pricing can be cherry-picked first).
