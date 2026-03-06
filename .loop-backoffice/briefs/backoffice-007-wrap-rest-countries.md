# Wrap: REST Countries

**Type:** wrap
**Model:** sonnet

## Goal
Add REST Countries as a paid service in the gateway catalog.

## Context
API evaluation: `.loop-backoffice/knowledge/api-eval-rest-countries.md`

## Tasks
1. Read the API evaluation and API documentation
2. Write handler function `_rest_countries` in `src/services.py` following the existing pattern
   - Primary endpoint: `GET https://restcountries.com/v3.1/name/{name}?fields=name,capital,population,currencies,languages,flags,region,timezones`
   - Also support lookup by ISO code: `GET https://restcountries.com/v3.1/alpha/{code}?fields=...`
   - Use `query` param for the search term, `lookup_type` param ("name" or "code", default "name")
   - Always use `?fields=` to limit response size
   - Return first match as clean JSON
3. Add `catalog.register(...)` call with the handler
4. Self-test: look up "France" and verify structured response
5. Update `.loop-backoffice/knowledge/portfolio.json` with the new service entry

## Constraints
- Follow the exact pattern in src/services.py — handler function + catalog.register()
- Handler must return JSON string
- Handle missing/unknown countries gracefully (return error JSON, don't crash)
- No API key needed — fully open
