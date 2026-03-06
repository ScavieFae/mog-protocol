# Brief: Ad-Supported Free Tier

**Branch:** brief-016-ad-supported-free-tier
**Model:** sonnet

## Goal

Add a genuinely free plan to Mog Markets where the "payment" is a contextual ad in the response. Be fully transparent — agents and orchestrators should know exactly what's happening and why.

## Context

Read these before starting:
- `src/gateway.py` — the `buy_and_call` handler, `find_service`, `/health`
- `src/pricing.py` — current pricing/surge logic
- `src/services.py` — service catalog and handlers
- `docs/plan-ids.md` — active plans (Free Trial = 3 credits, paid plans for USDC)
- `web/src/pages/ConnectPage.tsx` — if it exists (brief-015), update with free tier info

## Research Findings

**ZeroClick** (zeroclick.ai, backed by Honey co-founder Ryan Hudson, $55M raised) is the marquee AI-native ad platform — but it has **no public API**. It's partnership/sales-only. We cannot integrate it today.

**ChatAds** (getchatads.com) is the actionable option:
- **Has a public REST API, Python SDK, TypeScript SDK, and an MCP server wrapper**
- Detects product/service mentions in AI conversations, returns affiliate links/product recs
- Response time: <500ms
- Revenue: developers keep 100% of affiliate commissions; ChatAds charges per-request API fees
- Free tier: 100 requests/month to validate
- GitHub: github.com/Chat-Ads
- Ad formats: text links, product recommendations (8 formats total)

**Other options researched (not recommended for hackathon):**
- **Kevel/AdButler** — full JSON ad server APIs but require sourcing your own advertisers
- **Ad Context Protocol (AdCP)** — open standard built on MCP by AppNexus founder, too early-stage
- **Aryel In-Chat Ads** — more visual/interactive, doesn't fit JSON API responses well

**Pattern precedent:** OpenAI shows ads to free ChatGPT users (launched Feb 2026). Ads appear **at the end of responses**, clearly labeled and visually separated. Projects $1B in "free user monetization" revenue. This validates the "append ad block after real response" pattern.

## Architecture

### Ad provider: ChatAds (primary) + mock fallback

```python
# src/ads.py
import os, httpx
from typing import Optional

CHATADS_API_KEY = os.getenv("CHATADS_API_KEY")

def get_contextual_ad(query: str, context: str = "") -> Optional[dict]:
    """Fetch a contextual ad from ChatAds based on query/context.
    Returns None if no API key, API error, or no relevant ad.
    Never blocks the main response — ads are best-effort.
    """
    if not CHATADS_API_KEY:
        return _mock_ad(query) if os.getenv("ADS_MOCK") else None
    try:
        # ChatAds REST API — check their docs for exact endpoint/format
        resp = httpx.post(
            "https://api.getchatads.com/v1/ads",
            headers={"Authorization": f"Bearer {CHATADS_API_KEY}"},
            json={"query": query, "context": context, "format": "text"},
            timeout=3,
        )
        if resp.status_code == 200:
            data = resp.json()
            return {
                "label": "Sponsored",
                "text": data.get("text", ""),
                "url": data.get("url", ""),
                "sponsor": data.get("advertiser", ""),
            }
    except Exception:
        pass
    return None

def _mock_ad(query: str) -> dict:
    """Deterministic mock ad for testing the wiring without a real ad provider."""
    return {
        "label": "Sponsored (mock)",
        "text": f"Explore more tools related to '{query}' at the Nevermined marketplace",
        "url": "https://nevermined.app",
        "sponsor": "Nevermined",
    }
```

**IMPORTANT**: The worker MUST check ChatAds actual API docs before implementing. Verify:
- Exact endpoint URL (the above is a placeholder)
- Auth method and request format
- Response schema
- Their Python SDK may be simpler than raw HTTP: `pip install chatads`

### Where ads appear

**In `find_service`** — always for free tier. This is the discovery moment:
```json
{
  "results": ["...organic results..."],
  "sponsored": {
    "label": "Sponsored",
    "text": "Try Acme Search API — 10x faster semantic search",
    "url": "https://acme.dev/search",
    "sponsor": "Acme Inc"
  }
}
```

**In `buy_and_call`** — for free-tier calls only. The real result comes first, ad is appended:
```json
{
  "result": "...the actual search results...",
  "_sponsored": {
    "label": "Sponsored — this call was free, supported by contextual ads",
    "text": "...",
    "url": "...",
    "sponsor": "...",
    "notice": "Upgrade to a paid plan for ad-free access."
  }
}
```

**Paid plans never see ads.**

### Transparency contract (non-negotiable)

1. **Clearly labeled** as `"sponsored"` or `"_sponsored"` in the JSON key
2. **Separated** from actual data — never mixed into search results or summaries
3. **Explained** — includes why the ad is there and how to remove it
4. **Optional for the orchestrator** — separate key the agent can ignore or filter

## Tasks

### 1. Create `src/ads.py`

Thin ad client as shown above. ChatAds primary, mock fallback via `ADS_MOCK=true`.
- Install: `pip install chatads` (or use raw httpx if SDK is heavy)
- 3-second timeout — never slow down the main response
- Returns `Optional[dict]` — None means no ad, carry on

### 2. Gateway ad injection (`src/gateway.py`)

Modify `find_service` and `buy_and_call`:

**In `find_service`:**
```python
if is_free_tier(request):
    ad = get_contextual_ad(query=arguments.get("query", ""))
    if ad:
        result_text += f"\n\n---\nSponsored: {json.dumps(ad)}"
```

**In `buy_and_call`:**
```python
if is_free_tier(request):
    ad = get_contextual_ad(query=service_id, context=json.dumps(params)[:200])
    if ad:
        try:
            result_data = json.loads(result)
            result_data["_sponsored"] = {
                **ad,
                "notice": "This call was free, supported by contextual ads. Upgrade to a paid plan for ad-free access."
            }
            result = json.dumps(result_data)
        except json.JSONDecodeError:
            pass  # if result isn't JSON, skip ad injection
```

### 3. Tier detection

```python
import os

FREE_AD_PLAN_ID = os.getenv("NVM_FREE_AD_PLAN_ID", "")

def is_free_tier(request) -> bool:
    """Check if request is from free ad-supported plan."""
    # Check plan ID from x402 token or request metadata
    # Implementation depends on what Nevermined's x402 token exposes
    # Start with: check if the plan ID in the token matches FREE_AD_PLAN_ID
    return False  # safe default — no ads until plan is registered and wired
```

### 4. Register ad-supported plan on Nevermined

Using `payments-py`, register a new plan on the existing gateway agent (`48240718...62731`):
- Price: 0 (free)
- Credits: 1000 (high daily cap)
- Name: "Ad-Supported Free"
- Attach to existing gateway agent via `add_plan_to_agent()`

Add plan ID to `docs/plan-ids.md`, set as `NVM_FREE_AD_PLAN_ID` env var on Railway.

### 5. Update `/health` endpoint

Add plan tier info:
```python
"plans": {
    "free_ad_supported": {"credits": 1000, "ads": True, "price": "free"},
    "free_trial": {"credits": 3, "ads": False, "price": "free"},
    "starter": {"credits": 1, "ads": False, "price": "1 USDC"},
    "standard": {"credits": 10, "ads": False, "price": "5 USDC"},
    "pro": {"credits": 25, "ads": False, "price": "10 USDC"},
}
```

### 6. Update website (if ConnectPage exists)

Add free tier as the highlighted first option on `/connect`:
- "Free — ad-supported, unlimited calls"
- Explain: "Responses include a relevant sponsored suggestion. Upgrade anytime."

### 7. Add `chatads` to dependencies

In `pyproject.toml` or `requirements.txt`, add `chatads` (or `httpx` if using raw API).

## Completion Criteria

- [ ] `src/ads.py` exists with ChatAds client + mock mode
- [ ] `find_service` includes sponsored result for free-tier callers
- [ ] `buy_and_call` appends `_sponsored` field for free-tier callers
- [ ] Ads are clearly labeled and separated from real data
- [ ] Paid plans never see ads
- [ ] Ad fetch has 3s timeout — never slows down the main response
- [ ] Gateway works with `CHATADS_API_KEY` unset (graceful degradation)
- [ ] Mock mode works with `ADS_MOCK=true`
- [ ] `docs/plan-ids.md` updated with new free ad plan
- [ ] `/health` shows plan tiers

## Verification

- `ADS_MOCK=true python -c "from src.ads import get_contextual_ad; print(get_contextual_ad('web search'))"` returns mock ad
- Call `find_service` with free-tier token → response includes `sponsored` block
- Call `buy_and_call` with free-tier token → response includes `_sponsored` block
- Call either with paid-tier token → no ads in response
- Unset `CHATADS_API_KEY` and `ADS_MOCK` → everything works, just no ads

## Design Principles

1. **Never degrade the primary response.** The agent asked for search results — they get search results. The ad is additive, not substitutive.
2. **Be radically transparent.** Label everything. Explain why. Make it easy to upgrade.
3. **Respect the agent.** The `_sponsored` key is structured data the orchestrator can filter, display, or ignore. We don't trick agents into clicking ads.
4. **Best-effort only.** If the ad API is slow, down, or returns nothing — the response goes out without ads. Never block on ad fetch.
5. **Context, not tracking.** We send the query and service type as targeting signals. We do NOT send user identity, conversation history, or behavioral data.

## Future: ZeroClick

ZeroClick (zeroclick.ai) is the premium AI-native ad platform ($55M raised, Honey co-founder) but currently partnership-only with no public API. If they open up or we get a partnership, swap the ChatAds client for ZeroClick in `src/ads.py` — the gateway wiring stays the same. Also watch **Ad Context Protocol (AdCP)** — an open standard for agentic advertising built on MCP, backed by PubMatic/Yahoo/Magnite. Early stage but architecturally aligned with our MCP gateway.
