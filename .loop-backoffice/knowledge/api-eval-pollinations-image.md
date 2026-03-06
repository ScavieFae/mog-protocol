# API Evaluation: Pollinations.ai Image Generation

**Date:** 2026-03-05
**Evaluated by:** backoffice-011

## Summary

| Field | Value |
|---|---|
| upstream_cost | $0 for basic usage (Pollen credits for advanced; basic remains free forever per their FAQ) |
| spec_quality | High — full API docs at enter.pollinations.ai/api/docs, well-maintained |
| spec_url | https://pollinations.ai / https://enter.pollinations.ai/api/docs |
| auth_model | None for basic — no signup, no key, no account required |
| endpoint_count | Unified endpoint: gen.pollinations.ai + legacy image.pollinations.ai |
| estimated_demand | High — image generation is a marquee AI capability; agents love it for demos |
| competition | None in our catalog |
| margin | 100% on basic tier (upstream free) |

## Test Result

```
GET https://image.pollinations.ai/prompt/a%20cute%20robot%20at%20a%20hackathon
→ JPEG image binary (AI-generated image)
```

Status: **Working** (confirmed active, models include Flux, GPT Image, Seedream 5.0 as of Feb 2026)

## Integration Plan

Same challenge as QR codes: returns binary image data.

**Option A (URL return):** Construct and return the image URL. The buyer agent fetches or embeds it. Zero wrapping complexity.

Endpoint: `https://image.pollinations.ai/prompt/{url_encoded_prompt}?model=flux&width=512&height=512&seed=42`

Params: `prompt` (required), `model` (flux, gpt-image-large, seedream), `width`, `height`, `seed`, `nologo=true`

This is basically URL construction + return, which is trivially wrappable.

## Recommendation

**WRAP** — Image generation for free with no key is rare and extremely valuable for hackathon agents. Returning the URL is the right pattern. Agents at the hackathon will absolutely use this for demos. Unique capability, highest wow factor of any service we could add.

Suggested price: **3 credits** (image generation is perceived as high-value, inference is real compute even if free to us)
