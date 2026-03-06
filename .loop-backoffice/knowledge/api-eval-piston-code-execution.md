# API Evaluation: Piston Code Execution API

**Date:** 2026-03-05
**Evaluated by:** backoffice-011

## Summary

| Field | Value |
|---|---|
| upstream_cost | Was free; now requires authorization token |
| spec_quality | High — full docs at piston.readthedocs.io, well-structured REST API |
| spec_url | https://piston.readthedocs.io/en/latest/api-v2/ |
| auth_model | **Now requires auth token** (as of Feb 15, 2026) — must contact EngineerMan on Discord |
| endpoint_count | 3 (/api/v2/runtimes, /api/v2/execute, /api/v2/packages) |
| estimated_demand | Very High — sandboxed code execution is the #1 AI agent capability gap |
| competition | E2B (paid), Judge0 (RapidAPI key), self-hosted Piston |
| margin | N/A — can't wrap without a key |

## Test Result

```
POST https://emkc.org/api/v2/piston/execute
→ 401 Unauthorized (as of Feb 2026)
```

Status: **Blocked** — auth token required, cannot obtain without Discord contact

## Notes

Piston was the ideal free code execution API but closed public access Feb 15, 2026. The API itself is excellent — 70+ languages, sandboxed, fast. If Mattie can get an auth token via Discord (non-commercial use qualifies), this would be worth wrapping.

Alternatives explored:
- **Glot.io** — requires API key
- **Judge0 CE** — requires RapidAPI key (already evaluated in backoffice-004)
- **Wandbox** — web-only, no clean REST API
- **Self-hosting** — out of scope for hackathon timeline

## Recommendation

**SKIP** (for now) — Cannot access without authorization. Add to demand_signals as "code execution (blocked, needs Piston auth token or E2B key)".

**DEFER** — If Mattie gets a Piston token or E2B key, reconsider. Code execution would command 5-10 credits per call and be the most-used service in our catalog.
