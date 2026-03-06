# API Eval: Currency Conversion (fawazahmed0/currency-api)

**Date:** 2026-03-05
**Scout:** backoffice-004

## Summary

CDN-hosted currency exchange rate API. Static JSON files served via jsDelivr CDN, updated daily. No server to go down, no rate limits, completely free.

## Details

- **upstream_cost:** $0 (CDN-hosted static JSON, open-source project)
- **spec_quality:** high — simple REST, well-documented on GitHub
- **spec_url:** https://github.com/fawazahmed0/exchange-api
- **auth_model:** none — no API key, no account required
- **endpoint_count:** 2 endpoints:
  - `GET https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies.json` — list all 342 currencies
  - `GET https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/{base}.json` — rates from base currency
- **estimated_demand:** high — any agent doing pricing, invoicing, finance, or multi-currency data will need this
- **competition:** exchangerate-api.com (needs key), openexchangerates.org (needs key) — this is the only major free no-key option
- **margin:** 100% — zero upstream cost, charge 1 credit per lookup

## Test Results

Verified live:
- 342 currencies covered (crypto + fiat)
- Updated 2026-03-05
- 1 USD = 0.8603 EUR, 0.7484 GBP, 156.88 JPY
- Response time: ~300ms (CDN)

## Integration Notes

Implementation: fetch `https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/{base}.json`, extract `data[base][target]`, compute amount.

Params: `from_currency` (str), `to_currency` (str), `amount` (float = 1.0)

## Recommendation

**WRAP** — Zero cost, no key needed, high demand from any agent dealing with money/international data. Wraps in ~20 lines. Charge 1 credit.
