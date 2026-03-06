# ZeroClick — Sponsor Integration Writeup

**Team:** Mog Protocol
**Prize Category:** Best Integration of AI Native Ads Powered by ZeroClick Using Nevermined
**Integration Depth:** Marketplace service + free-tier ad monetization layer

---

## What We Built With ZeroClick

ZeroClick powers two things in Mog Protocol:

1. **`zeroclick_search` — A sellable marketplace service** where buyer agents purchase sponsored offer data through Nevermined billing
2. **Free-tier ad injection** — ZeroClick contextual ads appear in `find_service` and `buy_and_call` responses for free-plan users, subsidizing free access

This directly implements ZeroClick's vision of "reasoning-time advertising" — injecting advertiser context into AI agent workflows where it's commercially relevant.

---

## 1. ZeroClick as a Marketplace Service

### Handler Code (`src/services.py`)

```python
def _zeroclick_offers(query: str, limit: int = 3) -> str:
    """Fetch sponsored offers from ZeroClick for a query with commercial intent."""
    data = json.dumps({
        "method": "server",
        "query": query,
        "limit": min(limit, 5),
        "ipAddress": "0.0.0.0",
    }).encode()
    req = urllib.request.Request(
        "https://zeroclick.dev/api/v2/offers",
        data=data,
        method="POST",
    )
    req.add_header("Content-Type", "application/json")
    req.add_header("x-zc-api-key", ZEROCLICK_API_KEY)
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = json.loads(resp.read().decode())
    offers = []
    for o in (body if isinstance(body, list) else body.get("offers", body.get("data", []))):
        offers.append({
            "id": o.get("id"),
            "title": o.get("title", o.get("name", "")),
            "description": o.get("description", "")[:300],
            "click_url": o.get("clickUrl", o.get("click_url", "")),
            "price": o.get("price", ""),
            "brand": o.get("brand", o.get("advertiser", "")),
        })
    return json.dumps({"query": query, "offers": offers, "count": len(offers)})
```

### Catalog Registration

```python
catalog.register(
    service_id="zeroclick_search",
    name="ZeroClick Sponsored Search",
    description="Get relevant sponsored offers and deals for any commercial query. "
                "Powered by ZeroClick's AI ad network with 10,000+ advertisers. "
                "Ask about products, services, software, travel — anything with "
                "commercial intent. Returns titles, descriptions, prices, and click URLs.",
    price_credits=1,
    example_params={"query": "best CRM for small business", "limit": 3},
    provider="mog-protocol",
    handler=_zeroclick_offers,
    value_adds=["micro_paid", "api_bypass"],
)
```

### Live Response — `zeroclick_search(query="best project management software for startups")`

```json
{
  "query": "best project management software for startups",
  "offers": [
    {
      "id": "9323de97-ce1b-4d92-8e07-8c0083809c99",
      "title": "MS Project Standard 2024 CD Key",
      "description": "",
      "click_url": "https://zero.click/9323de97-ce1b-4d92-8e07-8c0083809c99",
      "price": {
        "amount": "27.14",
        "currency": "USD",
        "originalPrice": "27.14",
        "discount": null,
        "interval": null
      },
      "brand": {
        "name": "Kinguin",
        "url": "https://www.kinguin.net",
        "description": null,
        "iconUrl": "https://t2.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&url=https%3A%2F%2Fwww.kinguin.net&size=128"
      }
    },
    {
      "id": "ba8c21c1-42d2-4a25-a643-ca9843f6001b",
      "title": "MS Project Professional 2019 Bind Key",
      "description": "",
      "click_url": "https://zero.click/ba8c21c1-42d2-4a25-a643-ca9843f6001b",
      "price": {
        "amount": "19.75",
        "currency": "USD",
        "originalPrice": "19.75",
        "discount": null,
        "interval": null
      },
      "brand": {
        "name": "Kinguin",
        "url": "https://www.kinguin.net"
      }
    }
  ],
  "count": 2
}
```

ZeroClick returns real commercial offers with pricing, brand attribution, and trackable click URLs (`https://zero.click/{offer_id}`).

---

## 2. Free-Tier Ad Injection

For buyers on the free ad-supported plan, ZeroClick ads are injected into gateway responses:

### In `find_service` (discovery)

```python
# src/gateway.py
if FREE_AD_PLAN_ID:
    ad = get_contextual_ad(query=query)
    if ad:
        result += f"\n\n---\nSponsored: {json.dumps(ad)}"
```

### In `buy_and_call` (execution)

```python
if FREE_AD_PLAN_ID:
    ad = get_contextual_ad(query=service_id, context=json.dumps(params or {})[:200])
    if ad:
        response["_sponsored"] = {
            **ad,
            "notice": "This call was free, supported by contextual ads. "
                      "Upgrade to a paid plan for ad-free access.",
        }
```

### Pricing Tiers

| Plan | Credits | Ads | Price |
|------|---------|-----|-------|
| Free (ad-supported) | 1000 | Yes — ZeroClick contextual | Free |
| Free trial | 3 | No | Free |
| Starter | 1 | No | 1 USDC |
| Standard | 10 | No | 5 USDC |
| Pro | 25 | No | 10 USDC |

The ad-supported tier gives 1000 free credits — ZeroClick ads subsidize the cost. Paid plans are ad-free. This mirrors the consumer web model (Spotify free vs premium) but for agent-to-agent commerce.

---

## 3. The Agent Commerce Connection

ZeroClick's "reasoning-time advertising" maps perfectly to agent marketplaces:

```
Buyer Agent (planning a task)
  → calls find_service("project management tools")
  → gets marketplace results + ZeroClick sponsored offers
  → sponsored offers are contextually relevant commercial data
  → agent incorporates offer data into its reasoning
  → ZeroClick advertiser gets visibility in agent workflow
```

This is exactly what Ryan Hudson (ZeroClick founder, ex-Honey/PayPal) designed: injecting advertiser context into AI reasoning flows where it's commercially relevant, before the response is generated.

---

## 4. Where ZeroClick Appears in the UI

### Service Card
`zeroclick_search` displays with the zeroclick.ai favicon, call count, revenue, and health bar.

### Ticker
ZeroClick Sponsored Search scrolls in the top ticker with favicon and live price.

### Ad-Supported Badge
Services on the free tier show an "Ad-Supported Free" badge in sage green.

---

## Technical Details

| Detail | Value |
|--------|-------|
| **API Endpoint** | `POST https://zeroclick.dev/api/v2/offers` |
| **Auth** | Header: `x-zc-api-key: {ZEROCLICK_API_KEY}` |
| **Request Body** | `{"method": "server", "query": "...", "limit": 3, "ipAddress": "0.0.0.0"}` |
| **Response** | Array of offers with `id`, `title`, `description`, `clickUrl`, `price`, `brand` |
| **Price** | 1 credit per call (via Nevermined x402) |
| **Upstream Cost** | Free (ZeroClick earns from advertiser bids, not API callers) |
| **Margin** | 100% — advertiser pays ZeroClick, buyer pays us |

---

## Files

| File | What |
|------|------|
| `src/services.py` | `_zeroclick_offers` handler + catalog registration |
| `src/gateway.py` | Free-tier ad injection in `find_service` and `buy_and_call` |
| `src/ads.py` | `get_contextual_ad()` — contextual ad selection |
| `web/src/components/HivePanel.tsx` | ZeroClick favicon in service icons |
| `web/src/components/ServiceCard.tsx` | Ad-Supported Free badge |
| `docs/research/zeroclick.md` | Full research evaluation |

---

## Summary

ZeroClick in Mog Protocol demonstrates two forms of AI-native advertising:

1. **Direct service** — Agents buy sponsored offer data as a marketplace service, paying credits via Nevermined. The offers are contextually relevant commercial data that agents use in their reasoning.

2. **Free-tier subsidy** — ZeroClick ads in free-plan responses create a freemium model for agent commerce. Free users get 1000 credits with ads; paid users get ad-free access. Advertiser context flows naturally into agent workflows — no banners, no popups, just relevant commercial information injected at reasoning time.

This is the first implementation of "reasoning-time advertising" (ZeroClick's term) in an autonomous agent marketplace with real payment flows.
