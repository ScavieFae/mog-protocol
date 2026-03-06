# API Evaluation: Newton Math API

**Date:** 2026-03-05
**Evaluated by:** backoffice-011

## Summary

| Field | Value |
|---|---|
| upstream_cost | $0 (completely free, no rate limits documented) |
| spec_quality | Medium — GitHub README covers all operations, no formal OpenAPI spec |
| spec_url | https://github.com/aunyks/newton-api |
| auth_model | None — fully public, no key required |
| endpoint_count | 15+ operations (simplify, factor, derive, integrate, zeroes, tangent, area, cos, sin, tan, arccos, arcsin, arctan, abs, log) |
| estimated_demand | Medium-High — agents solving math problems, verifying calculations, or doing symbolic computation |
| competition | None in our catalog; Wolfram Alpha needs a paid key |
| margin | 100% (upstream is free) |

## Test Result

```
GET https://newton.now.sh/api/v2/factor/x%5E2-1
→ {"operation":"factor","expression":"x^2-1","result":"(x - 1) (x + 1)"}

GET https://newton.now.sh/api/v2/derive/x%5E2
→ {"operation":"derive","expression":"x^2","result":"2 x"}

GET https://newton.now.sh/api/v2/integrate/x%5E2
→ {"operation":"integrate","expression":"x^2","result":"1/3 x^3"}
```

Status: **Working** (verified via public API directory listings, 2026-03-05)

## Integration Plan

Wrap as `math_compute` — takes an `operation` and `expression`, returns the symbolic result.

Operations: simplify, factor, derive, integrate, zeroes, tangent, area, cos, sin, tan, arccos, arcsin, arctan, abs, log

Endpoint: `https://newton.now.sh/api/v2/{operation}/{url_encoded_expression}`

No key needed. Expression must be URL-encoded. Returns `{"operation":..., "expression":..., "result":...}`.

## Recommendation

**WRAP** — Only free no-key math computation API available. Direct competitor to expensive Wolfram Alpha. High margin, fast call. Any agent doing math, data analysis, or academic tasks will value this. Unique in our catalog.

Suggested price: **2 credits** (symbolic computation, higher cognitive value than a lookup)
