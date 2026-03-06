# API Eval: Judge0 CE (Code Execution)

**Date:** 2026-03-05
**Scout:** backoffice-004

## Summary

Judge0 CE is an open-source code execution system. There's a public hosted instance at ce.judge0.com, but the free public tier requires API key via RapidAPI. Direct access returns 403.

## Details

- **upstream_cost:** Unknown for RapidAPI tier; self-hosted is free
- **spec_quality:** excellent — full OpenAPI spec, well-known in competitive programming
- **spec_url:** https://ce.judge0.com/
- **auth_model:** RapidAPI key required for the public hosted instance
- **endpoint_count:** 15+ endpoints for submissions, languages, system info
- **estimated_demand:** high — code execution is a top need for AI agents
- **competition:** E2B (needs API key from Mattie), Runyx (unverified)
- **margin:** unknown (need to price against RapidAPI costs)

## Test Results

- `GET https://ce.judge0.com/` → HTTP 403 Forbidden (unauthenticated)
- Cannot confirm working without RapidAPI key

## Recommendation

**SKIP** — Blocked at the door without a key, and getting a RapidAPI key would require Mattie's involvement. E2B is the better code execution option (already on the radar). If E2B key comes through, wrap that instead.
