# API Evaluation: Open-Meteo

**Date:** 2026-03-05
**Source:** Scout 001

## Overview
Free, open-source weather forecast API. No API key required.

## Technical Details
- **Base URL:** `https://api.open-meteo.com/v1/forecast`
- **Auth model:** None (completely open)
- **Upstream cost per call:** $0 (free, open-source)
- **Spec quality:** Good REST docs, no OpenAPI spec file but clean query parameter docs
- **Spec URL:** https://open-meteo.com/en/docs
- **Endpoint count:** 1 main endpoint with extensive query parameters (hourly, daily, current weather)
- **Rate limits:** Fair use, no hard limit documented

## Business Case
- **Estimated demand:** HIGH — weather is universally useful for agents (location context, planning, data enrichment)
- **Competition:** No one else at hackathon likely selling weather via MCP
- **Our price:** 1 credit per call
- **Margin:** 100% (upstream cost = $0)
- **Wrapping complexity:** LOW — simple GET with query params, returns JSON

## Example Call
```
GET https://api.open-meteo.com/v1/forecast?latitude=37.77&longitude=-122.42&current=temperature_2m,wind_speed_10m&hourly=temperature_2m&forecast_days=1
```

## Recommendation: WRAP

**Reasoning:** Zero cost, no key needed, universal demand, simple integration. This is the easiest possible wrap with guaranteed positive ROI on first call. Weather is a common agent need that no competitor is likely serving.
