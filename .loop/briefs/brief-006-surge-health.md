# Brief 006: Gateway Surge Pricing + Health Endpoint

**Model:** sonnet

## Goal

Wire surge pricing into the gateway and add a /health endpoint. Continuation of brief-005 (which stalled).

## Context

- `src/pricing.py` has `get_current_price(service_id, base_price) -> (price, surge_multiplier)`
- `src/txlog.py` has `txlog.get_recent(n)` and `txlog.count_calls(service_id, window_seconds)`
- `src/gateway.py` already has txlog imported but uses static `service.price_credits` everywhere
- PORT binding is already correct (`PORT` -> `GATEWAY_PORT` -> `4000`), do NOT change it
- `railway.toml` references `healthcheckPath = "/health"`

## Tasks

### 1. Wire surge pricing into gateway

In `src/gateway.py`:
- Add `from src.pricing import get_current_price`
- In `_gateway_credits()`: replace `return service.price_credits` with `price, _ = get_current_price(service_id, service.price_credits); return price`
- In `buy_and_call()` after getting the service: call `price, surge_multiplier = get_current_price(service_id, service.price_credits)`
- Use `price` instead of `service.price_credits` in the txlog entry and response `_meta`
- Add `"surge_multiplier": surge_multiplier` to the `_meta` dict

### 2. Add /health endpoint

The gateway uses PaymentsMCP which is built on FastAPI. Add a health endpoint that returns:
```json
{
  "status": "ok",
  "services_count": N,
  "services": [{"service_id": "...", "name": "...", "price_credits": N}, ...],
  "recent_transactions": [...last 10 txlog entries...],
  "demand_signals": [...unmet_demand entries from txlog...]
}
```

The PaymentsMCP server exposes a FastAPI app. You can access it via `mcp.app` or similar. If that doesn't work, add a simple HTTP endpoint using the same approach the MCP server uses for its port. Check how PaymentsMCP/FastAPI exposes routes.

## Verification

```bash
source .venv/bin/activate
python -m src.test_gateway   # existing tests still pass
```

## Constraints
- Do NOT change the PORT binding in main() — it's already correct
- Do NOT modify any files other than `src/gateway.py` and `src/test_gateway.py`
- Keep it simple — hackathon code
