# Light MCP — Two-Tool Gateway Spec

**Classification: NECESSARY**

## Problem

MCP dumps full tool catalogs into buyer agent context on connect. Standard MCP: `tools/list` returns everything — names, descriptions, full JSON schemas. At 30+ tools that's ~6,000 tokens of permanent context, and accuracy drops. Research shows retrieval-first patterns improve tool-selection accuracy from 13% to 43%.

PaymentsMCP (Nevermined's MCP wrapper) adds payment but does nothing for discovery or context. An agent connecting to a PaymentsMCP server with 30 tools still gets 30 tools in context, still has no idea what they cost until after calling one.

## Design

Our gateway sits in front of all services and exposes exactly two tools. The buyer's `tools/list` always returns:

```json
[
  {"name": "find_service", "description": "Search the marketplace...", "inputSchema": {...}},
  {"name": "buy_and_call", "description": "Pay for and execute a service...", "inputSchema": {...}}
]
```

Two tools. Always. Regardless of how many services are behind the gateway. That's ~200 tokens of permanent context instead of 6,000+.

### Tool 1: find_service

This is where purchasing decisions happen.

```python
@mcp.tool()
def find_service(query: str, budget: int = None) -> str:
    """Search the marketplace for services matching your need.

    Args:
        query: Natural language description of what you need
               (e.g. "web search with snippets", "PDF to JSON")
        budget: Max credits you'll pay per call (optional, filters results)

    Returns: JSON array of top 3-5 matches.
    """
```

**Return contract** — each match provides:

| Field | Purpose |
|-------|---------|
| `service_id` | Pass to `buy_and_call` |
| `name` | Quick identification |
| `description` | What it does, when/why to use it |
| `price` | Current credits per call (reflects surge) |
| `example_params` | Calling interface without schema dump |
| `provider` | Who's selling (enables switching decisions) |

This gives agents everything they need to make a purchasing decision: what it does, what it costs, how to call it. No schema bloat.

### Tool 2: buy_and_call

```python
@mcp.tool()
def buy_and_call(service_id: str, params: dict) -> str:
    """Pay for and execute a service in one call.
    Payment is automatic — handled internally via Nevermined.

    Args:
        service_id: From find_service results
        params: Parameters for the underlying service

    Returns: JSON with result, credits_charged, budget_remaining.
    """
```

**Return contract** — enables ROI reasoning:

```json
{
  "content": [{"type": "text", "text": "...actual API response..."}],
  "_meta": {
    "credits_charged": 3,
    "budget_remaining": 47,
    "service_id": "exa-search-v1",
    "surge_multiplier": 1.5
  }
}
```

The `_meta` field follows Nevermined's PaymentsMCP convention. It's allowed by MCP spec for implementation-specific metadata. Agents can reason: "I paid 3 credits, got useful results, 47 left. Buy again or try a cheaper provider?"

## Architecture — Two Layers

```
Buyer Agent
    | MCP protocol (Streamable HTTP, 2 tools)
    v
Mog Gateway (our server — plain MCP, NOT PaymentsMCP)
    | HTTP calls / MCP proxy
    v
Individual Services
    - Our Exa wrapper (PaymentsMCP server)
    - Our other wrapped APIs
    - Other teams' PaymentsMCP servers
    - Plain HTTP APIs
```

The gateway is a **plain MCP server** (FastMCP or payments_py.mcp.PaymentsMCP). It does not use `@requires_payment` per-tool internally. Instead, it handles the buyer-side payment in `buy_and_call` and proxies to upstream services.

Buyer agents connect via standard MCP. They POST JSON-RPC to `/mcp`. Auth is via `Authorization: Bearer <x402_token>` — the same pattern PaymentsMCP uses. Buyer gets a token once from Nevermined, reuses it across calls.

## Implementation

### Gateway Server

```python
from payments_py import Payments, PaymentOptions
from payments_py.mcp import PaymentsMCP

payments = Payments.get_instance(
    PaymentOptions(nvm_api_key=NVM_API_KEY, environment=NVM_ENVIRONMENT)
)

mcp = PaymentsMCP(
    payments,
    name="mog-gateway",
    agent_id=NVM_AGENT_ID,
    version="1.0.0",
    description="API marketplace. Search and buy access to tools.",
)

@mcp.tool(credits=0)  # find_service is free — discovery shouldn't cost
def find_service(query: str, budget: int = None) -> str:
    matches = catalog.search(query, budget=budget, top_k=5)
    return json.dumps(matches)

@mcp.tool(credits=dynamic_credits)  # credits determined by which service is called
def buy_and_call(service_id: str, params: dict) -> str:
    service = catalog.get(service_id)
    result = service.call(params)  # proxy to upstream
    return json.dumps({"result": result, "service_id": service_id})

async def main():
    result = await mcp.start(port=3000)
    # Server running at http://localhost:3000/mcp
```

### Catalog Index

- In-memory dict + numpy for embeddings at hackathon scale
- Each service entry: `{service_id, name, description, price, example_params, provider, embedding}`
- `find_service` embeds the query with `text-embedding-3-small`, cosine similarity, top-k
- At < 50 services, this is fast enough in-memory. No vector DB.

### Adding Services to the Catalog

Services are registered by:
1. **Manual** — our own wrapped APIs (Exa, etc.), added in code
2. **Walk-around** — Mattie gets API keys from teams, we wrap and register
3. **Autonomous** — wrapper agent discovers and adds (Phase 2)

Each registration:
```python
catalog.register(
    service_id="exa-search-v1",
    name="Exa Web Search",
    description="Semantic web search. Returns relevant snippets with URLs. Use when you need current information from the web.",
    price=2,
    example_params={"query": "latest AI research papers", "max_results": 5},
    provider="mog-protocol",
    handler=exa_search_handler,  # function that actually calls Exa
)
```

## Transport

MCP Streamable HTTP. Client POSTs JSON-RPC to `/mcp`. Response is JSON or SSE depending on `Accept` header. The `Accept: application/json, text/event-stream` header is required by the MCP spec.

Health check at `/health`. No WebSocket needed.

## Context Math

| Setup | Permanent Context Cost |
|-------|----------------------|
| Standard MCP, 30 tools | ~6,000 tokens (30 schemas x ~200 tokens) |
| Standard MCP, 100 tools | ~20,000 tokens |
| Mog Gateway, any number of tools | ~200 tokens (2 schemas) |

`find_service` results add ~500 tokens per query to conversation history (transient, not permanent tool definitions). This scales: 300 tools behind the gateway still costs 200 tokens to the buyer.

## Resolved Questions

- **mcpc:** It's a CLI client (npm), not a server framework. Not relevant to us. Our gateway implements the same progressive-discovery concept server-side.
- **Auth:** x402 Bearer token via Nevermined, same as PaymentsMCP pattern.
- **Error handling:** Return the error in `buy_and_call` result. No refunds at hackathon scale.
- **Rate limiting:** Surge pricing handles demand management instead.
- **FastMCP vs PaymentsMCP:** Use PaymentsMCP directly — it wraps FastMCP and adds the payment layer we need.
