# Wrapper Agent — Autonomous API Wrapping Pipeline

**Classification: NECESSARY (for "autonomous business" judging criteria)**

## What It Does

Discovers APIs, evaluates whether wrapping them is ROI-positive, generates the MCP server, lists it in the marketplace. Runs autonomously via simple-loop on ScavieFae while Mattie does in-person sales.

## Starting Point

Fork `nevermined-io/hackathons/agents/mcp-server-agent/`. It provides:
- PaymentsMCP server with `@mcp.tool(credits=N)` decorators
- `setup.py` for one-shot agent + plan registration
- `client.py` for self-testing
- Dynamic credit pricing via context functions

We swap the example tools (DuckDuckGo search, summarize, research) for real tools backed by real APIs.

## Phase 1 Services (Manual, Thursday Morning)

### Exa Search (we have keys + $50 coupon)

```python
@mcp.tool(credits=1)
def exa_search(query: str, max_results: int = 5) -> str:
    """Semantic web search. Returns relevant snippets with source URLs.
    Use when you need current information, research, or web content."""
    result = exa_client.search_and_contents(
        query, num_results=max_results, text=True
    )
    return json.dumps([{
        "title": r.title,
        "url": r.url,
        "snippet": r.text[:500],
    } for r in result.results])
```

### Second tool — pick based on what's useful at the hackathon

Options (in order of likely value):
1. **Claude summarizer** — takes text, returns structured summary. We have Anthropic keys. 5 credits (uses LLM).
2. **Web scrape** — takes URL, returns clean text. Uses httpx + basic extraction. 2 credits.
3. **Whatever teams are asking for** — listen at the venue, wrap what's in demand.

## Phase 2 Services (Walk-Around, Thursday Afternoon)

Input from Mattie walking the venue:
- "Team 7 needs weather data" → wrap Weatherstack
- "Everyone's using the same OpenAI wrapper" → undercut or differentiate
- "Nobody has PDF extraction" → find an API, wrap it

Each new service follows the same pattern:
1. Get API key (ours or team gives us theirs)
2. Write the tool function with `@mcp.tool(credits=N)`
3. Add to catalog index
4. Test with self-buy
5. List in marketplace spreadsheet

## Evaluation Logic (What Makes This Autonomous)

```python
def should_wrap(api_info: dict) -> dict:
    """LLM call with structured output. Returns {wrap: bool, reasoning: str, suggested_price: int}

    Factors:
    - upstream_cost: What does each API call cost us?
    - estimated_demand: How many agents at this hackathon need this?
    - competition: Did someone else already list this?
    - generation_effort: Simple API call? Complex multi-step?
    - margin: Can we price above cost and below alternatives?
    """
```

At hackathon scale, this is a Claude/GPT call with structured output, not an ML model. The judgment is the point — it's what makes this an autonomous business, not an autonomous wrapper.

## Simple-Loop Integration

ScavieFae runs the daemon. Briefs scoped to 2-3 tasks for fast turnaround.

### Brief 1: Phase 1 Seller
```
Goal: Get first paid MCP service running on Nevermined
Tasks:
  1. Set up project: pyproject.toml, .env, install payments-py[mcp]
  2. Implement Exa search tool with PaymentsMCP, run setup.py to register
  3. Implement self-test client, verify credits burn
Completion: Server running, self-buy succeeds, credits deducted in Nevermined dashboard
```

### Brief 2: Second Service + Catalog
```
Goal: Add a second paid service and the catalog index
Tasks:
  1. Add Claude summarizer (or chosen second tool)
  2. Build catalog module: register services, embed descriptions, search
  3. Test both services via catalog search
Completion: Two services registered, catalog search returns correct results
```

### Brief 3: Gateway (Phase 2)
```
Goal: Build the two-tool gateway that fronts all services
Tasks:
  1. Gateway MCP server with find_service and buy_and_call
  2. Wire find_service to catalog search, buy_and_call to service proxy
  3. End-to-end test: subscriber finds exa search, buys and calls it through gateway
Completion: Gateway running, full find->buy->result flow works
```

## Deployment

All services run as a single process for hackathon simplicity. The gateway and individual service handlers share a Python process. If performance demands it (unlikely at hackathon scale), split into separate processes.

## Open Questions

- **API key management:** `.env` file per service. Fine for hackathon.
- **ToS:** We're wrapping and reselling API access. Worth a wink in the demo. Not a real concern at hackathon scale.
