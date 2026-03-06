# Wrap: Currency Conversion

**Type:** wrap
**Model:** sonnet

## Goal
Add Currency Conversion as a paid service in the gateway catalog.

## Context
API evaluation: `.loop-backoffice/knowledge/api-eval-currency-conversion.md`

## Tasks
1. Read the API evaluation at `.loop-backoffice/knowledge/api-eval-currency-conversion.md`
2. Add a `_currency_convert` handler function in `src/services.py` following the existing pattern (see `_ip_geolocation`, `_open_meteo_weather`, `_mymemory_translate`)
3. Add `catalog.register(...)` call with service_id `currency_convert`
4. Self-test: import and call the handler with a simple USD->EUR conversion, verify it returns valid JSON
5. Update `.loop-backoffice/knowledge/portfolio.json`: add service entry with upstream_cost=0, price=1

## Handler Spec

```python
def _currency_convert(from_currency: str = "usd", to_currency: str = "eur", amount: float = 1.0) -> str:
```

- URL: `https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/{from_currency}.json`
- Lowercase both currency codes
- Response: `data[from_currency][to_currency]` gives the exchange rate
- Compute: `converted = rate * amount`
- Return JSON: `{"from": "usd", "to": "eur", "amount": 1.0, "rate": 0.8603, "converted": 0.8603}`
- Handle errors gracefully (return error JSON)

## Catalog Registration

```python
catalog.register(
    service_id="currency_convert",
    name="Currency Conversion",
    description="Convert between 342 currencies (fiat and crypto). Real-time exchange rates updated daily. Use for pricing, invoicing, financial calculations, or multi-currency data.",
    price_credits=1,
    example_params={"from_currency": "usd", "to_currency": "eur", "amount": 100},
    provider="mog-protocol",
    handler=_currency_convert,
)
```

## Constraints
- Follow the exact pattern in src/services.py — handler function + catalog.register()
- Handler must return JSON string
- Handle errors gracefully (return error JSON, don't crash)
- No API key needed — CDN-hosted static JSON
- Lowercase currency codes before making the request
