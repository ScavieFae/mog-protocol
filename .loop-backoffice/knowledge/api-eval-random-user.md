# API Evaluation: Random User Generator

**Date:** 2026-03-05
**Evaluated by:** backoffice-008

## Summary

| Field | Value |
|---|---|
| upstream_cost | $0 (maintained by randomuser.me, donation-supported) |
| spec_quality | High — excellent docs, many filter options |
| spec_url | https://randomuser.me/documentation |
| auth_model | None — fully public |
| endpoint_count | 1 endpoint with many query params (results, nat, gender, seed, inc/exc fields) |
| estimated_demand | Medium-high — agents building demos, test data, simulations, personas |
| competition | None in current catalog |
| margin | 100% (upstream is free) |

## Test Result

```
GET https://randomuser.me/api/?results=1&nat=us
→ {
    "results": [{
      "name": {"title": "Mr", "first": "Jose", "last": "Dunn"},
      "email": "jose.dunn@example.com",
      "location": {"city": "Lowell", ...},
      "phone": "...",
      "dob": {"age": 42, ...}
    }],
    "info": {"seed": "...", "results": 1, ...}
  }
```

Status: **Working** ✓

## Integration Plan

Wrap as `random_user` — takes optional `count` (1-10) and `nationality` (us/gb/fr/de/etc.), returns list of synthetic user profiles with name, email, location, age. Handler strips picture URLs (not useful) and flattens to clean dict.

## Recommendation

**WRAP** — Good demand for test data generation, persona building, demo population. Zero cost. Different from anything else in catalog.

Suggested price: **1 credit** (simple lookup, even for multiple users)
