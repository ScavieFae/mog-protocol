# Brief 005: Gateway Surge Pricing + Deploy Readiness

**Model:** sonnet

## Goal

Wire surge pricing into the gateway's `buy_and_call` so credits charged reflect demand, and make the gateway deploy-ready for Railway (PORT env var, health endpoint with stats).

## Context

- `src/pricing.py` and `src/txlog.py` exist and work (brief-004)
- `src/gateway.py` already logs transactions to txlog but charges static credits via `_gateway_credits()`
- `railway.toml` and `Procfile` exist (Scav added them)
- The gateway needs to respect `PORT` env var for Railway (currently uses `GATEWAY_PORT` defaulting to 4000)

## Tasks

1. **Wire surge pricing into gateway `_gateway_credits()`**: Import `get_current_price` from `src.pricing` and use it in `_gateway_credits()` so the dynamic credit cost reflects surge multiplier. The `buy_and_call` response `_meta` should include `surge_multiplier`.

2. **Add `/health` endpoint** to gateway that returns JSON with:
   - `status: "ok"`
   - `services_count`: number of registered services
   - `services`: list of `{service_id, name, price_credits}`
   - `recent_transactions`: last 10 txlog entries
   - `demand_signals`: any unmet_demand entries from txlog
   This is already referenced in `railway.toml` as `healthcheckPath = "/health"`

3. **Fix PORT binding for Railway**: The gateway should check `PORT` env var first (Railway sets this), then fall back to `GATEWAY_PORT`, then 4000. Update `main()` in gateway.py.

## Verification

```bash
source .venv/bin/activate
python -m src.test_gateway   # existing tests still pass
curl http://localhost:4000/health  # returns JSON with services + stats
```

## Constraints
- Don't break the existing e2e flow (find_service → buy_and_call)
- Keep it simple — this is hackathon code
