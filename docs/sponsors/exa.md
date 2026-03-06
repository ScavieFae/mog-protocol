# Exa — Sponsor Integration Writeup

**Team:** Mog Protocol
**Prize Category:** Exa API Credits (Sponsor Resource)
**Integration Depth:** Core infrastructure — Exa powers 3 distinct systems

---

## What We Built With Exa

Exa is the search backbone of the Mog Protocol marketplace. We integrated it at three layers:

1. **Sellable Service** — `exa_search` and `exa_get_contents` are credit-gated services buyer agents purchase through Nevermined
2. **Scout Intelligence** — The autonomous scout agent uses Exa to discover new APIs to wrap and sell
3. **Targeted API Discovery** — `scout_exa` is a specialized scout skill with focus modes for finding wrappable APIs

---

## 1. Exa as a Marketplace Service

Buyer agents discover and purchase Exa search through our two-tool gateway (`find_service` → `buy_and_call`). Every call goes through Nevermined x402 billing.

### Handler Code (`src/services.py`)

```python
def _exa_search(query: str, max_results: int = 5) -> str:
    import exa_py
    client = exa_py.Exa(api_key=EXA_API_KEY)
    result = client.search_and_contents(query, num_results=max_results, text=True)
    return json.dumps([
        {"title": r.title, "url": r.url, "snippet": (r.text or "")[:500]}
        for r in result.results
    ])
```

### Catalog Registration

```python
catalog.register(
    service_id="exa_search",
    name="Exa Web Search",
    description="Semantic web search. Returns relevant snippets with source URLs.",
    price_credits=1,
    example_params={"query": "latest AI research papers", "max_results": 5},
    provider="mog-protocol",
    handler=_exa_search,
    value_adds=["micro_paid", "api_bypass"],
)
```

**Value-adds for buyers:**
- `micro_paid` — pay-per-call, no subscription commitment
- `api_bypass` — no Exa API key needed, we handle auth

### Live Response

```json
[
  {
    "title": "Best AI Agents 2026: 11 Platforms Compared | Fleece AI",
    "url": "https://fleeceai.app/blog/best-ai-agents-2026-top-platforms-compared",
    "snippet": "Best AI Agents 2026: 11 Platforms Compared | Fleece AI... After testing 30+ AI agent platforms, Fleece AI ranks #1 for business automation with 3,000+ integrations, multi-agent hierarchies, and scheduled workflows..."
  },
  {
    "title": "Agentic AI Frameworks: The Complete Guide (2026)",
    "url": "https://aiagentskit.com/blog/agentic-ai-frameworks/",
    "snippet": "Agentic AI Frameworks: The Complete Guide (2026)..."
  },
  {
    "title": "12 Best AI Agent Frameworks in 2026 | Data Science Collective",
    "url": "https://medium.com/data-science-collective/the-best-ai-agent-frameworks-for-2026-tier-list-b3a4362fac0d",
    "snippet": "The Best AI Agent Frameworks for 2026 (Ranked by Production Experience, not Hype)..."
  }
]
```

### Pricing

| Service | Base Price | Surge Range | Our Upstream Cost |
|---------|-----------|-------------|-------------------|
| `exa_search` | 1 credit | 1-3 credits (dynamic) | ~$0.01/call |
| `exa_get_contents` | 2 credits | 2-6 credits (dynamic) | ~$0.02/call |

Surge pricing kicks in when volume exceeds 10 calls/15min, with velocity and demand pressure signals.

---

## 2. Exa as Scout Intelligence

The autonomous scout agent (`mog-scout`) uses Exa to discover new APIs worth wrapping into marketplace services.

### search_web Tool (`src/agents/tools.py`)

```python
def _search_web(query: str, max_results: int = 5, **kwargs) -> str:
    """Search the web using Exa for API discovery."""
    import exa_py
    client = exa_py.Exa(api_key=EXA_API_KEY)
    result = client.search_and_contents(query, num_results=max_results, text=True)
    return json.dumps([
        {"title": r.title, "url": r.url, "snippet": (r.text or "")[:400]}
        for r in result.results
    ])
```

This powers the scout's API discovery loop: check demand signals → search for matching APIs → evaluate ROI → propose service for worker to wrap.

---

## 3. scout_exa — Targeted API Discovery Skill

A specialized Exa search with focus modes and signal extraction:

```python
def _scout_exa(query: str, focus: str = "api", max_results: int = 5, **kwargs) -> str:
    focus_prompts = {
        "api": f"free REST API {query} JSON endpoint no auth",
        "mcp": f"MCP server {query} tool github",
        "competitor": f"hackathon agent marketplace {query} API",
    }
    # ... search, then extract signals:
    apis.append({
        "title": r.title,
        "url": r.url,
        "snippet": text[:300],
        "signals": {
            "has_endpoint": has_endpoint,  # detected API patterns
            "likely_free": has_free,       # detected free-tier signals
        },
    })
```

**Focus modes:**
- `api` — finds free/cheap REST APIs with public endpoints
- `mcp` — finds existing MCP servers we could resell
- `competitor` — monitors what other hackathon teams are building

**Firing criteria:** The scout fires `scout_exa` when it detects a demand signal (unmet query) or catalog gap.

---

## 4. Where Exa Appears in the UI

### Service Card
Exa services display with the exa.ai favicon, call count, revenue earned, success rate health bar, and surge pricing.

### Hive Panel
Every Exa tool call appears in the activity stream with the Exa favicon badge. Stats bar shows total Exa calls across all agents.

### Ticker
Exa Search scrolls in the top ticker with favicon and live price (including surge multiplier).

---

## Summary

| Integration Point | What It Does | File |
|-------------------|-------------|------|
| `exa_search` service | Buyers purchase semantic search via Nevermined | `src/services.py` |
| `exa_get_contents` service | Buyers purchase content extraction via Nevermined | `src/services.py` |
| `search_web` scout tool | Scout agent discovers APIs using Exa | `src/agents/tools.py` |
| `scout_exa` scout skill | Targeted API discovery with focus modes + signal detection | `src/agents/tools.py` |
| Web UI badges | Exa favicon on service cards, hive panel, ticker | `web/src/components/` |

Exa is not just a service we sell — it's the intelligence layer that helps our autonomous agents find new services to sell. The recursive value: Exa helps us find APIs → we wrap them → we sell them → revenue funds more Exa calls.
