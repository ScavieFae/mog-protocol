# Hackathon Repo Teardown

Source: https://github.com/nevermined-io/hackathons
Cloned to: /tmp/hackathons

## Key Discovery: MCP Server Agent

The repo includes a ready-made MCP server with payment-protected tools at `agents/mcp-server-agent/`. This is basically our Phase 1 seller with minimal modification.

### PaymentsMCP — The Key Abstraction

```python
from payments_py.mcp import PaymentsMCP

mcp = PaymentsMCP(
    payments,
    name="data-mcp-server",
    agent_id=NVM_AGENT_ID,
    version="1.0.0",
    description="Data tools MCP server with Nevermined payments",
)

@mcp.tool(credits=1)
def search_data(query: str) -> str:
    """Search the web."""
    return "results..."
```

`PaymentsMCP` handles: OAuth 2.1, token validation, credit redemption, HTTP transport, session management, MCP JSON-RPC protocol. The `@mcp.tool(credits=N)` decorator is the only payment code needed per tool.

### Dynamic Pricing Built In

Credits can be a function that receives context (args + result) after execution:

```python
def _summarize_credits(ctx: Dict[str, Any]) -> int:
    result = ctx.get("result") or {}
    content = result.get("content", [])
    text = content[0].get("text", "") if content else ""
    return min(10, max(2, 2 + len(text) // 500))

@mcp.tool(credits=_summarize_credits)
def summarize_data(content: str, paywall_context=None) -> str:
    ...
```

### Setup Script — One-Shot Registration

`src/setup.py` registers agent + plan in one call, writes IDs to `.env`:

```python
result = payments.agents.register_agent_and_plan(
    agent_metadata=AgentMetadata(name="...", description="...", tags=[...]),
    agent_api=AgentAPIAttributes(
        endpoints=[Endpoint(verb="POST", url=f"mcp://{MCP_SERVER_NAME}/tools/search_data")],
        agent_definition_url=f"mcp://{MCP_SERVER_NAME}/tools/*",
    ),
    plan_metadata=PlanMetadata(name="...", description="..."),
    price_config=get_free_price_config(),  # or get_erc20_price_config()
    credits_config=get_dynamic_credits_config(credits_granted=100, min=1, max=20),
    access_limit="credits",
)
```

**Only needs NVM_API_KEY to run.** Outputs agent_id and plan_id.

### Client Flow

```python
# 1. Subscribe to plan
payments.plans.order_plan(PLAN_ID)

# 2. Get x402 token (reusable across requests)
token_result = payments.x402.get_x402_access_token(PLAN_ID)
access_token = token_result["accessToken"]

# 3. Call MCP tool via JSON-RPC
response = client.post(f"{SERVER_URL}/mcp", headers={
    "Authorization": f"Bearer {access_token}",
}, json={
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {"name": "search_data", "arguments": {"query": "..."}},
    "id": 1,
})
```

### Two API Keys Required

- **Builder key** (`NVM_API_KEY`) — for the server/seller. Creates plans, registers agents.
- **Subscriber key** (`NVM_SUBSCRIBER_API_KEY`) — for the client/buyer. Orders plans, gets tokens, calls tools.

Different Nevermined accounts. Both start with `sandbox:` for testing.

### MCP Endpoint URIs

Registration uses logical MCP URIs, not HTTP URLs:
```
mcp://data-mcp-server/tools/search_data
mcp://data-mcp-server/tools/summarize_data
```

This decouples registration from physical server location.

## x402 FastAPI Middleware (Alternative to MCP)

For plain HTTP endpoints (not MCP), one-line middleware:

```python
from payments_py.x402.fastapi import PaymentMiddleware

app.add_middleware(
    PaymentMiddleware,
    payments=payments,
    routes={"POST /ask": {"plan_id": PLAN_ID, "credits": 1}},
)
```

Payment goes in `payment-signature` header (not `Authorization: Bearer`).

## Dependencies

```toml
payments-py = {version = ">=1.1.0", extras = ["mcp"]}
fastapi = "^0.120.0"
uvicorn = ">=0.34.2"
httpx = "^0.28.0"
openai = "^1.40.0"
python-dotenv = "^1.0.0"
```

## Repo Structure

```
hackathons/
  agents/
    mcp-server-agent/     <- OUR STARTING POINT
      src/setup.py        <- registers agent+plan, writes .env
      src/server.py       <- PaymentsMCP server with 3 tools
      src/client.py       <- demo client showing full flow
      src/tools/           <- search, summarize, research implementations
    seller-simple-agent/  <- HTTP x402 seller (Strands SDK)
    buyer-simple-agent/   <- HTTP/A2A buyer with React frontend
  workshops/
    getting-started/      <- minimal server+client (~50 lines each)
    payment-plans/        <- plan types, dynamic pricing, registration
    mcp-tools/            <- minimal MCP server+client
    x402/                 <- x402 protocol deep dive
    a2a-payments/         <- A2A buyer/seller
```

## Nevermined MCP Server (for vibe coding)

Add to Claude Code config for live Nevermined docs access:
```json
{"mcpServers": {"nevermined": {"url": "https://docs.nevermined.app/mcp"}}}
```

Also: https://docs.nevermined.app/assets/nevermined_mcp_for_llms.txt

## Impact on Our Plan

The MCP server agent is 90% of our Phase 1. Fork it, swap DuckDuckGo for Exa, add more tools, done. The `PaymentsMCP` class replaces our planned FastMCP + manual @requires_payment wiring. Dynamic pricing is already supported via credit functions.

The two-tool gateway (`find_service` + `buy_and_call`) sits ON TOP of this — it's a separate MCP server that proxies to underlying paid MCP servers. But for the 8PM deadline, we don't need the gateway. We need one paid MCP server with real tools, listed in the marketplace, transacting.
