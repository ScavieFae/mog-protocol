# Wrap: Open-Meteo Weather API

**Type:** wrap
**Model:** sonnet

## Goal
Add Open-Meteo weather forecast as a paid service in the gateway catalog.

## Context
API evaluation: `.loop-backoffice/knowledge/api-eval-open-meteo.md`

## Tasks
1. Read the API evaluation at `.loop-backoffice/knowledge/api-eval-open-meteo.md`
2. Write a `_open_meteo_weather` handler function in `src/services.py` following the existing pattern (_exa_search, _claude_summarize):
   - Accept parameters: `latitude` (float), `longitude` (float), `forecast_days` (int, default 1)
   - Call `https://api.open-meteo.com/v1/forecast` with `current=temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code` and `hourly=temperature_2m` and `forecast_days`
   - Use `urllib.request` (stdlib) — no new dependencies
   - Return JSON string with the API response
   - No API key needed — just make the HTTP call
3. Add `catalog.register(...)` call:
   - service_id: `open_meteo_weather`
   - name: `Weather Forecast`
   - description: Clear description of what it does (current conditions + forecast for any lat/lon)
   - price_credits: 1
   - example_params: `{"latitude": 37.77, "longitude": -122.42, "forecast_days": 1}`
4. Self-test: Run `python -c "from src.services import catalog; print(catalog.get('open_meteo_weather'))"` to verify registration works
5. Update `.loop-backoffice/knowledge/portfolio.json`:
   - Add `open_meteo_weather` entry with status "active", upstream_cost 0, our_price 1, total_calls 0
   - Update budget: spent_wrapping += 3 (cost of this wrap brief)

## Constraints
- Follow the exact pattern in src/services.py — handler function + catalog.register()
- Handler must return JSON string
- Use only stdlib (urllib.request) — no new pip dependencies
- No API key needed for Open-Meteo
