# API Eval: LibreTranslate

**Date:** 2026-03-05
**Scout:** backoffice-004

## Summary

LibreTranslate is an open-source machine translation API. The public instance at libretranslate.com now requires an API key even for basic use. Returned 403 on unauthenticated test.

## Details

- **upstream_cost:** $0 if self-hosted; key required for public instance
- **spec_quality:** excellent — clean OpenAPI spec, actively maintained
- **spec_url:** https://docs.libretranslate.com/
- **auth_model:** API key required for public instance at libretranslate.com
- **endpoint_count:** 5 endpoints (translate, detect, languages, suggest, frontend)
- **estimated_demand:** high if accessible
- **competition:** MyMemory (free, no key, verified working)

## Test Results

- POST to `https://libretranslate.com/translate` with `{"q": "Hello", "source": "en", "target": "es"}` → HTTP 403 Forbidden

## Recommendation

**SKIP** — The public endpoint now requires an API key. MyMemory is the better alternative: same use case, verified working without a key. Use MyMemory.
