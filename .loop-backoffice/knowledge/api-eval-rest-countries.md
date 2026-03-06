# API Eval: REST Countries API

**Date:** 2026-03-05
**Scout:** backoffice-004

## Summary

REST Countries provides structured data about all countries in the world — capitals, populations, currencies, languages, flags, timezones, calling codes, etc. Completely free, no key required, open-source.

## Details

- **upstream_cost:** $0
- **spec_quality:** excellent — well-documented, stable v3.1 API
- **spec_url:** https://restcountries.com
- **auth_model:** none — fully open
- **endpoint_count:** multiple:
  - `GET /v3.1/name/{name}` — search by country name (partial match)
  - `GET /v3.1/alpha/{code}` — by ISO 2/3 letter code
  - `GET /v3.1/currency/{currency}` — countries using a currency
  - `GET /v3.1/lang/{language}` — countries by language
  - `GET /v3.1/all` — all 250 countries
  - Supports `?fields=` filter to get only needed fields
- **estimated_demand:** medium — useful for enriching location data, building context about places, international use cases
- **competition:** local data (agents could have country data baked in), but having a live queryable service is cleaner
- **margin:** 100% — upstream cost $0, charge 1 credit

## Test Results

Verified live:
- `?fields=name,capital,population,currencies,languages` for France returns clean structured data ✓
- Response time: ~200ms
- 250 countries in database

## Integration Notes

Simple lookup: search by name or ISO code, filter fields. The `?fields=` param is important to limit response size.

Primary use case for agents: "what currency does X use?", "what's the capital of Y?", "what languages are spoken in Z?"

## Recommendation

**WRAP** — Zero cost, no key, works. Useful complement to ip_geolocation (which returns country/city, agents then might want to know currency/language/capital). Natural follow-on call pattern. 1 credit.
