# API Eval: MyMemory Translation API

**Date:** 2026-03-05
**Scout:** backoffice-004

## Summary

MyMemory is the world's largest translation memory service. They offer a free REST API with no API key required, supporting 100+ language pairs. Powered by machine translation (Google/Microsoft under the hood) plus human translation memory.

## Details

- **upstream_cost:** $0 for free tier (no key registration)
- **spec_quality:** high — clean REST API, well-documented
- **spec_url:** https://mymemory.translated.net/doc/spec.php
- **auth_model:** none required — anonymous tier allows 10,000 words/day
- **endpoint_count:** 1 main endpoint:
  - `GET https://api.mymemory.translated.net/get?q={text}&langpair={src}|{tgt}`
  - Returns `responseData.translatedText`
- **estimated_demand:** high — any agent processing multilingual content, docs, or user messages needs translation
- **competition:** LibreTranslate public instance (403 blocked), Google Translate API (paid), DeepL (paid) — MyMemory is the only free no-key REST option tested that works
- **margin:** 100% — upstream cost is $0, charge 1-2 credits per call

## Test Results

Verified live:
- English → Spanish: "Hello world" → "Hola mundo" ✓
- English → French: "The quick brown fox..." → "Le renard brun et rapide..." ✓
- `quotaFinished: false` in response when quota is not exceeded
- Response time: ~500ms

## Integration Notes

Params: `text` (str), `source_lang` (str, default "en"), `target_lang` (str)

URL encode the text with `urllib.parse.quote`. Response: `data["responseData"]["translatedText"]`.

Rate limit: 10,000 words/day anonymous. Well above hackathon usage.

## Recommendation

**WRAP** — No key, works, high demand. Perfect for hackathon agents that process multilingual content. Translation is a universal utility. Charge 2 credits (slightly higher than weather/geo because it's a richer service).
