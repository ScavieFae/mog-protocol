# Nevermined Integration Spec

**Classification: NECESSARY (mandatory for hackathon)**

## Overview

All transactions flow through Nevermined. The SDK is `payments-py` (Python). Payment uses x402 protocol — HTTP Bearer tokens, credit-based billing, no wallet popups per request.

Reference implementation: `nevermined-io/hackathons` repo, specifically `agents/mcp-server-agent/`.

## SDK Patterns (Actual, From Hackathon Repo)

### Initialization

```python
from payments_py import Payments, PaymentOptions

payments = Payments.get_instance(
    PaymentOptions(
        nvm_api_key=os.getenv("NVM_API_KEY"),  # "sandbox:..." or "live:..."
        environment=os.getenv("NVM_ENVIRONMENT", "sandbox"),
    )
)
```

Environments: `sandbox` (Base Sepolia testnet), `staging`, `live` (Base mainnet).

### One-Shot Agent + Plan Registration

The `setup.py` pattern from the hackathon repo — registers agent and payment plan in one call, writes IDs to `.env`:

```python
from payments_py.common.types import AgentMetadata, AgentAPIAttributes, Endpoint, PlanMetadata
from payments_py.plans import get_free_price_config, get_dynamic_credits_config

result = payments.agents.register_agent_and_plan(
    agent_metadata=AgentMetadata(
        name="Mog Protocol",
        description="API marketplace with search and paid tool access",
        tags=["marketplace", "mcp", "search"],
    ),
    agent_api=AgentAPIAttributes(
        endpoints=[
            Endpoint(verb="POST", url="mcp://mog-gateway/tools/find_service"),
            Endpoint(verb="POST", url="mcp://mog-gateway/tools/buy_and_call"),
        ],
        agent_definition_url="mcp://mog-gateway/tools/*",
    ),
    plan_metadata=PlanMetadata(
        name="Mog Marketplace Credits",
        description="Credits for searching and buying API access",
    ),
    price_config=get_free_price_config(),  # free for hackathon testing
    credits_config=get_dynamic_credits_config(
        credits_granted=100,
        min_credits_per_request=0,  # find_service is free
        max_credits_per_request=20,
    ),
    access_limit="credits",
)

agent_id = result["agentId"]
plan_id = result["planId"]
```

MCP logical URIs (`mcp://mog-gateway/tools/...`) decouple registration from physical server location.

### PaymentsMCP Server (For Individual Services)

```python
from payments_py.mcp import PaymentsMCP

mcp = PaymentsMCP(
    payments,
    name="exa-search-server",
    agent_id=NVM_AGENT_ID,
    version="1.0.0",
    description="Exa semantic web search",
)

@mcp.tool(credits=1)
def exa_search(query: str, max_results: int = 5) -> str:
    """Semantic web search via Exa. Returns relevant snippets with URLs."""
    result = exa_client.search(query, num_results=max_results)
    return json.dumps(result)

# Dynamic pricing: credits calculated after execution
def research_credits(ctx: dict) -> int:
    result = ctx.get("result") or {}
    content = result.get("content", [])
    text = content[0].get("text", "") if content else ""
    return min(10, max(2, 2 + len(text) // 500))

@mcp.tool(credits=research_credits)
def deep_research(query: str, paywall_context=None) -> str:
    """Deep research combining search + AI synthesis. 2-10 credits based on output."""
    ...

# Start server
async def main():
    result = await mcp.start(port=3000)
    # Endpoints: /mcp (JSON-RPC), /health
```

### Client Side — Subscribing and Calling

```python
# Subscriber uses a DIFFERENT API key than the builder
subscriber_payments = Payments.get_instance(
    PaymentOptions(nvm_api_key=os.getenv("NVM_SUBSCRIBER_API_KEY"), environment="sandbox")
)

# Check balance, order if needed
balance = subscriber_payments.plans.get_plan_balance(PLAN_ID)
if not balance.is_subscriber:
    subscriber_payments.plans.order_plan(PLAN_ID)

# Get x402 access token (reusable across multiple requests)
token_result = subscriber_payments.x402.get_x402_access_token(PLAN_ID)
access_token = token_result["accessToken"]

# Call MCP tool via JSON-RPC
response = httpx.post(f"{SERVER_URL}/mcp", headers={
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}, json={
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {"name": "exa_search", "arguments": {"query": "AI trends"}},
    "id": 1,
})

# Response includes _meta with payment receipt
result = response.json()["result"]
content = result["content"]       # tool output
meta = result.get("_meta", {})    # credits_redeemed, success, etc.
```

## Two API Keys Required

| Key | Role | Starts with |
|-----|------|-------------|
| **Builder** (`NVM_API_KEY`) | Creates agents, plans. Used by our servers. | `sandbox:...` |
| **Subscriber** (`NVM_SUBSCRIBER_API_KEY`) | Orders plans, gets tokens. Used by buyer agents / test client. | `sandbox:...` |

These must be different Nevermined accounts. Both obtained from https://nevermined.app.

## Payment Architecture for the Gateway

Two payment relationships:

```
Other Teams' Agents
    | pay us (via our plan)
    v
Mog Gateway (reseller)
    | pays upstream (via their plans, or direct API calls)
    v
Upstream Services (Exa, other teams' APIs)
```

**Reseller model:** Buyer pays us credits. We call upstream services using our own API keys or our own x402 tokens. Buyer never touches Nevermined directly — they just call `buy_and_call` and get results.

This is the simplest integration. Buyer agents don't need the Nevermined SDK or their own accounts. They get an x402 token for our plan and call our gateway.

## Dependencies

```toml
payments-py = {version = ">=1.1.0", extras = ["mcp"]}
fastapi = "^0.120.0"
uvicorn = ">=0.34.2"
httpx = "^0.28.0"
python-dotenv = "^1.0.0"
```

The `extras = ["mcp"]` is critical — it pulls in PaymentsMCP support.

## Setup Steps (Day-Of)

1. Sign up at https://nevermined.app — create TWO accounts (builder + subscriber)
2. Each account: API Keys > Global NVM API Keys > + New API Key
3. Builder account: set `NVM_API_KEY` in `.env`
4. Run `setup.py` — registers agent + plan, writes `NVM_AGENT_ID` and `NVM_PLAN_ID` to `.env`
5. Start server with `python -m src.server`
6. Subscriber account: set `NVM_SUBSCRIBER_API_KEY` in `.env`
7. Run `client.py` — subscribes to plan, gets token, calls a tool
8. Verify credits were burned in the Nevermined dashboard
9. List in hackathon marketplace spreadsheet

## Credits / Coupons

- **Exa:** `EXA50NEVERMINED` — $50 in credits
