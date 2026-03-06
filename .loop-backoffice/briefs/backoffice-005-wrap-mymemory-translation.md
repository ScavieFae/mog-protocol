# Wrap: MyMemory Translation

**Type:** wrap
**Model:** sonnet

## Goal
Add MyMemory Translation as a paid service in the gateway catalog.

## Context
API evaluation: `.loop-backoffice/knowledge/api-eval-mymemory-translation.md`

## Tasks
1. Read the API evaluation at `.loop-backoffice/knowledge/api-eval-mymemory-translation.md`
2. Add a `_mymemory_translate` handler function in `src/services.py` following the existing pattern (see `_ip_geolocation`, `_open_meteo_weather`)
3. Add `catalog.register(...)` call with service_id `mymemory_translate`
4. Self-test: import and call the handler with a simple English->Spanish translation, verify it returns valid JSON
5. Update `.loop-backoffice/knowledge/portfolio.json`: add service entry with upstream_cost=0, price=2

## Handler Spec

```python
def _mymemory_translate(text: str, source_lang: str = "en", target_lang: str = "es") -> str:
```

- URL: `https://api.mymemory.translated.net/get?q={text}&langpair={source_lang}|{target_lang}`
- URL-encode the text with `urllib.parse.quote`
- Response: `data["responseData"]["translatedText"]`
- Return JSON: `{"translated_text": "...", "source": "en", "target": "es", "original": "..."}`
- Handle errors gracefully (return error JSON)

## Catalog Registration

```python
catalog.register(
    service_id="mymemory_translate",
    name="Text Translation",
    description="Translate text between 100+ languages. Supports all major language pairs. Use when processing multilingual content, translating user messages, or localizing output.",
    price_credits=2,
    example_params={"text": "Hello world", "source_lang": "en", "target_lang": "es"},
    provider="mog-protocol",
    handler=_mymemory_translate,
)
```

## Constraints
- Follow the exact pattern in src/services.py — handler function + catalog.register()
- Handler must return JSON string
- Handle errors gracefully (return error JSON, don't crash)
- No API key needed — this is a free, no-auth API
- Rate limit: 10,000 words/day anonymous (well above hackathon usage)
