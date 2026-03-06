# Apify — Sponsor Integration Writeup

**Team:** Mog Protocol
**Prize Category:** Apify Credits (Sponsor Resource)
**Integration Depth:** Scout discovery layer — autonomous actor store search

---

## What We Built With Apify

Apify powers the `scout_apify` tool — an autonomous scout skill that searches Apify's actor store to find pre-built scrapers and automations our agents can wrap as marketplace services with zero code.

The key insight: Apify's 3,000+ actors are already-built API endpoints. Our agents can discover them, evaluate their commercial potential, and wrap them as credit-gated services in our Nevermined marketplace — turning Apify actors into autonomous revenue streams.

---

## scout_apify — Actor Store Discovery

### Implementation (`src/agents/tools.py`)

```python
def _scout_apify(query: str = "", category: str = "", max_results: int = 5, **kwargs) -> str:
    """Search Apify's actor store for wrappable actors.

    Apify actors are pre-built scrapers/automations that can be called via REST API.
    Each actor has a run endpoint: POST https://api.apify.com/v2/acts/{actorId}/runs
    We can wrap these as marketplace services with zero code.
    """
    import httpx
    params = {"limit": max_results}
    if query:
        params["search"] = query
    if category:
        params["category"] = category

    resp = httpx.get("https://api.apify.com/v2/store", params=params, timeout=10)
    data = resp.json().get("data", {}).get("items", [])

    actors = []
    for item in data[:max_results]:
        actors.append({
            "actor_id": item.get("id", ""),
            "name": item.get("name", ""),
            "title": item.get("title", ""),
            "description": (item.get("description") or "")[:200],
            "username": item.get("username", ""),
            "stats": {
                "total_runs": item.get("stats", {}).get("totalRuns", 0),
                "total_users": item.get("stats", {}).get("totalUsers", 0),
            },
            "is_free": item.get("currentPricingInfo", {}).get("pricingModel") == "FREE",
            "run_endpoint": f"https://api.apify.com/v2/acts/{item.get('username','')}/{item.get('name','')}/runs",
            "wrap_difficulty": "easy" if free else "medium",
        })

    return json.dumps({
        "query": query or "(trending)",
        "actors_found": len(actors),
        "actors": actors,
        "recommendation": "Free actors with high total_runs are best candidates.",
    }, indent=2)
```

### Tool Schema

```json
{
  "name": "scout_apify",
  "description": "FIRE WHEN: looking for scrapers, data extraction, or automation services. Searches Apify's actor store for pre-built actors we can wrap as marketplace services with zero code. Free actors = 100% margin.",
  "input_schema": {
    "type": "object",
    "properties": {
      "query": {"type": "string", "description": "What to search for"},
      "category": {"type": "string", "description": "Apify category filter"},
      "max_results": {"type": "integer", "description": "Max results (default 5)"}
    }
  }
}
```

### Live Response — `scout_apify(query="twitter scraper")`

```json
{
  "query": "twitter scraper",
  "actors_found": 3,
  "actors": [
    {
      "actor_id": "61RPP7dywgiy0JPD0",
      "name": "tweet-scraper",
      "title": "Tweet Scraper V2 - X / Twitter Scraper",
      "description": "Lightning-fast search, URL, list, and profile scraping, with customizable filters. At $0.40 per 1000 tweets, and 30-80 tweets per second...",
      "username": "apidojo",
      "stats": {
        "total_runs": 131557810,
        "total_users": 39549
      },
      "is_free": false,
      "run_endpoint": "https://api.apify.com/v2/acts/apidojo/tweet-scraper/runs",
      "wrap_difficulty": "medium"
    },
    {
      "actor_id": "nfp1fpt5gUlBwPcor",
      "name": "twitter-scraper-lite",
      "title": "Twitter (X.com) Scraper Unlimited: No Limits",
      "description": "The most comprehensive Twitter data extraction solution available...",
      "username": "apidojo",
      "stats": {
        "total_runs": 10697128,
        "total_users": 18236
      },
      "is_free": false,
      "run_endpoint": "https://api.apify.com/v2/acts/apidojo/twitter-scraper-lite/runs",
      "wrap_difficulty": "medium"
    },
    {
      "actor_id": "CJdippxWmn9uRfooo",
      "name": "twitter-x-data-tweet-scraper-pay-per-result-cheapest",
      "title": "Tweet Scraper | $0.25/1K Tweets | Pay-Per Result",
      "description": "Only $0.25/1000 tweets for Twitter scraping, 100% reliability, swift data retrieval...",
      "username": "kaitoeasyapi",
      "stats": {
        "total_runs": 32725098,
        "total_users": 8919
      },
      "is_free": false,
      "run_endpoint": "https://api.apify.com/v2/acts/kaitoeasyapi/twitter-x-data-tweet-scraper-pay-per-result-cheapest/runs",
      "wrap_difficulty": "medium"
    }
  ],
  "recommendation": "Free actors with high total_runs are best candidates. Wrap via POST to run_endpoint with APIFY_API_TOKEN."
}
```

---

## How It Fits the Autonomous Pipeline

The scout agent's decision loop:

```
1. Check demand signals (unmet buyer queries)
2. If demand matches scraping/data/automation → fire scout_apify
3. Evaluate actors: is_free? total_runs high? run_endpoint available?
4. If viable → propose_service with the actor's run_endpoint
5. Worker agent receives proposal → register_service with proxy handler
6. Service goes live on marketplace → buyer agents can purchase via Nevermined
```

### Firing Criteria

The scout fires `scout_apify` when:
- A demand signal mentions scraping, data extraction, social media, or automation
- An existing service has been killed and needs a replacement
- The scout is exploring new revenue opportunities

The tool description includes `FIRE WHEN:` criteria so the LLM knows exactly when to reach for it.

---

## Where Apify Appears in the UI

### Hive Panel Activity Stream
When `scout_apify` fires, it appears with:
- **Badge:** `SCOUT:APIFY` in orange (#FF6B35) with Apify favicon
- **Glow:** Gradient background + ping animation (bright scout skill treatment)
- **Summary:** `"twitter scraper 3 actors"` (parsed from JSON response)

### Stats Bar
Scout skill firings counted separately: `"3 scout"` in pink

### Service Cards
Any Apify-sourced service registered by the worker displays the apify.com favicon.

---

## The Arbitrage Model

Apify actors as marketplace arbitrage:

| Layer | What | Cost |
|-------|------|------|
| **Upstream** | Apify actor run | Free (free actors) or $0.25-0.40/1K results |
| **Our service** | Credit-gated proxy via Nevermined | 1-3 credits per call |
| **Buyer pays** | USDC via x402 | $1-5 per plan |

Free Apify actors give us **100% margin** — we charge credits, the upstream cost is zero. Even paid actors at $0.40/1K give us strong margin at 1 credit ($1) per call.

---

## Summary

| What | Detail |
|------|--------|
| **Tool** | `scout_apify` — searches Apify's public actor store API |
| **Endpoint** | `GET https://api.apify.com/v2/store?search={query}` |
| **Auth** | None needed for discovery (public store API) |
| **Output** | Actor metadata with run endpoint, stats, pricing, wrap difficulty |
| **Pipeline** | Discovery → evaluate → propose → register → sell via Nevermined |
| **Files** | `src/agents/tools.py`, `web/src/components/HivePanel.tsx` |

Apify's actor store is the largest catalog of pre-built scrapers and automations on the web. By giving our autonomous scout the ability to search it, we turned Apify into a supply pipeline — the scout finds actors, the worker wraps them, and the marketplace sells them. The agent colony does the work humans would normally do: evaluate, integrate, price, and ship.
