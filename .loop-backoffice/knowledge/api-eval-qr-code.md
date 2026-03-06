# API Evaluation: QR Code Generator (QRServer)

**Date:** 2026-03-05
**Evaluated by:** backoffice-011

## Summary

| Field | Value |
|---|---|
| upstream_cost | $0 (completely free, no documented rate limits) |
| spec_quality | Medium — docs at goqr.me/api/, straightforward query-param API |
| spec_url | https://goqr.me/api/ |
| auth_model | None — fully public, no key required |
| endpoint_count | 2 (create-qr-code, read-qr-code) |
| estimated_demand | Medium — agents building apps, generating sharing links, demo workflows |
| competition | None in our catalog |
| margin | 100% (upstream is free) |

## Test Result

```
GET https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=Hello%20World&format=png
→ PNG image binary (150x150 QR code)

GET https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=https://example.com&format=svg
→ SVG XML data
```

Status: **Working** (API is widely used, confirmed active in 2026)

## Integration Plan

Challenge: the API returns binary image data (PNG/SVG), not JSON text. Two wrapping strategies:

**Option A (URL return):** Return the constructed API URL as a string — the buyer agent can fetch it directly. Simple, zero latency overhead, works for most agent use cases.

**Option B (base64):** Fetch the image, base64-encode it, return as JSON. More complete but adds latency and payload size.

Recommendation: **Option A** — return the URL. Agents can use it directly or embed it. Much simpler.

Params: `data` (required, the content to encode), `size` (optional, default 150x150), `format` (optional: png/svg/eps, default png).

## Recommendation

**WRAP** — Simple, unique capability, zero cost. Agents building demos, generating sharing links, or creating artifacts will use this. Option A (return URL) makes wrapping trivial. One of the easiest wraps available.

Suggested price: **1 credit** (single lookup, returns a URL not data)
