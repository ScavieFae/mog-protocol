# API Evaluation: ip-api.com

**Date:** 2026-03-05
**Source:** Scout 001

## Overview
Free IP geolocation API. No API key required.

## Technical Details
- **Base URL:** `http://ip-api.com/json/{ip}`
- **Auth model:** None (free tier, HTTP only)
- **Upstream cost per call:** $0
- **Spec quality:** Simple JSON docs, straightforward
- **Spec URL:** https://ip-api.com/docs/api:json
- **Endpoint count:** 1 (JSON endpoint; also XML/CSV variants)
- **Rate limits:** 45 requests/minute on free tier

## Business Case
- **Estimated demand:** MEDIUM — useful for agents doing location-based work, security analysis, or data enrichment
- **Competition:** Low — niche but handy
- **Our price:** 1 credit per call
- **Margin:** 100% (upstream cost = $0)
- **Wrapping complexity:** LOW — simple GET, returns JSON

## Caveats
- Free tier is HTTP only (no HTTPS) — acceptable for hackathon
- 45 req/min rate limit — sufficient for hackathon traffic

## Example Call
```
GET http://ip-api.com/json/8.8.8.8
```

## Recommendation: WRAP

**Reasoning:** Zero cost, no key, simple integration. Lower demand than weather but still useful. Queue as second wrap after Open-Meteo.
