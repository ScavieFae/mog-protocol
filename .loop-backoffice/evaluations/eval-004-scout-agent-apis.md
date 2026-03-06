# Evaluation: backoffice-004-scout-agent-apis

**Date:** 2026-03-06
**Verdict:** ACCEPTED

## What was delivered

5 API evaluations with live test results:

| API | Recommendation | Key needed? | Demand |
|-----|---------------|-------------|--------|
| Currency Conversion (fawazahmed0) | WRAP | No | High |
| MyMemory Translation | WRAP | No | High |
| REST Countries | WRAP | No | Medium |
| Judge0 CE | SKIP | Yes (RapidAPI) | High but blocked |
| LibreTranslate | SKIP | Yes (now) | High but blocked |

## Quality Assessment

- All 5 evaluations include required fields (upstream_cost, spec_quality, auth_model, demand, margin, recommendation)
- All have verified live test results with actual data
- Skip decisions are well-reasoned (key-blocked, better alternatives exist)
- Wrap candidates are all free, no-key, verified working
- Integration notes include specific params and URL patterns — ready for wrapping

## Wrapping Priority

1. **MyMemory Translation** — universal utility, highest incremental value (no translation service yet)
2. **Currency Conversion** — high demand for finance/international agents, zero cost
3. **REST Countries** — good complement to ip_geolocation, medium demand

## Budget Impact

Scout cost: ~1 credit (Exa searches)
Wrapping 3 APIs: ~9-15 credits
Budget remaining: ~90 credits — can comfortably afford all 3

## Decision

Accept and merge. Dispatch wrap briefs in priority order starting with MyMemory Translation.
