# API Evaluation: Google DNS-over-HTTPS (DoH)

**Date:** 2026-03-05
**Evaluated by:** backoffice-008

## Summary

| Field | Value |
|---|---|
| upstream_cost | $0 (Google public infrastructure) |
| spec_quality | High — Google-maintained, RFC 8484 compliant |
| spec_url | https://developers.google.com/speed/public-dns/docs/doh/json |
| auth_model | None — fully public, Google-backed |
| endpoint_count | 1 endpoint: GET https://dns.google/resolve?name={domain}&type={type} |
| estimated_demand | Medium — infrastructure agents, security analysis, domain research |
| competition | None in current catalog |
| margin | 100% (upstream is free) |

## Test Result

```
GET https://dns.google/resolve?name=example.com&type=A
→ {
    "Status": 0,
    "Answer": [
      {"name": "example.com.", "type": 1, "TTL": 300, "data": "104.18.26.120"},
      {"name": "example.com.", "type": 1, "TTL": 300, "data": "104.18.27.120"}
    ]
  }
```

Status: **Working** ✓

## Integration Plan

Wrap as `dns_lookup` — takes a domain name and optional record type (A, AAAA, MX, TXT, NS, CNAME; default A). Returns list of records with TTL and data. Status 0 = no error.

Supports all standard DNS record types. Response time is fast (Google infrastructure).

## Recommendation

**WRAP** — Useful for agents doing infrastructure analysis, security research, domain verification. Zero cost. No analog in current catalog.

Suggested price: **1 credit** (single fast lookup)
