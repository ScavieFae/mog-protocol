# Nevermined Hackathon Onboarding — The Unofficial Guide

Everything we wish someone had told us at 9:30 AM Thursday. Written from the floor of the Nevermined Autonomous Business Hackathon, March 2026, AWS Loft SF.

---

## 1. Creating Your Nevermined Account & API Key

Go to [nevermined.app](https://nevermined.app). Sign up (email or wallet).

### API Key Permissions

When you create an API key, you'll see four permission toggles. **Enable all four.** You want:

| Permission | What It Does | Who Needs It |
|-----------|-------------|-------------|
| **Register** | Create agents and plans on the registry | Sellers (anyone offering a service) |
| **Purchase** | Subscribe to other agents' plans | Buyers (anyone consuming a service) |
| **Issue** | Generate x402 access tokens | Both — you need tokens to make authenticated calls |
| **Redeem** | Settle credits on calls you receive | Sellers (your server redeems credits when buyers call you) |

**Key insight:** One key with all four permissions works for both selling and buying. You don't need separate accounts unless you want distinct wallet addresses (useful for showing cross-agent transactions to judges).

Your key looks like: `sandbox:eyJhbGciOiJFUzI1NksifQ.eyJ...`

The `sandbox:` prefix tells payments-py which environment to connect to. Don't strip it.

### Environment

The hackathon uses **sandbox** (Base Sepolia testnet). All transactions are real on-chain settlements, but with test tokens. Set `environment="sandbox"` everywhere.

---

## 2. The Hackathon Portal

Nevermined runs a marketplace portal at `nevermined.ai/hackathon/register`. This is where teams register as sellers and buyers. It's separate from nevermined.app — the portal is hackathon-specific.

### Registering as a Seller

Fill in:
- **Agent/Service name** — what buyers will see
- **Team name** — your hackathon team
- **Category** — pick from: AI/ML, DeFi, Research, Analytics, Data, Infrastructure, Gaming, Social, Other
- **Description** — what your agent does, in 1-2 sentences
- **Endpoint URL** — your deployed server's MCP endpoint (e.g., `https://your-app.up.railway.app/mcp`)
- **Price per request** — in credits. Other teams show prices like "1 credit" or "5 credits"

### Registering as a Buyer

Simpler form. Name, team, what you're looking for.

### The Discovery API

The portal has an API you can query programmatically:

```bash
# All agents
curl -H "x-nvm-api-key: YOUR_KEY" \
  https://nevermined.ai/hackathon/register/api/discover

# Just sellers
curl -H "x-nvm-api-key: YOUR_KEY" \
  "https://nevermined.ai/hackathon/register/api/discover?side=sell"

# Filter by category
curl -H "x-nvm-api-key: YOUR_KEY" \
  "https://nevermined.ai/hackathon/register/api/discover?side=sell&category=AI%2FML"
```

Response shape:
```json
{
  "sellers": [
    {
      "name": "Agent Name",
      "teamName": "Team",
      "category": "AI/ML",
      "description": "What it does",
      "pricing": { "perRequest": "1 credit" },
      "endpointUrl": "https://...",
      "nvmAgentId": "123...",
      "planIds": ["456..."]
    }
  ],
  "buyers": [...],
  "meta": { "total": 29 }
}
```

Categories in the wild (as of Thursday afternoon): AI/ML, DeFi, Research, Analytics, Data, Infrastructure.

---

## 3. The Ideas Board (Hackathon Spreadsheet)

There's a shared Google Sheets "Ideas Board" that teams use for visibility. Columns include team name, project name, description, tech stack, looking for (collaborators/customers), and contact info.

This is the real discovery mechanism at the hackathon — Nevermined's own agent registry doesn't have search, so teams find each other through the spreadsheet, the portal, and walking around the venue.

**Put your project on the spreadsheet early.** It's how other teams' Claudes and agents will find you.

---

## 4. The Transaction Flow (How Money Actually Moves)

Here's what happens when an agent buys a service:

```
1. Buyer subscribes to seller's plan
   └─ payments.plans.order_plan(PLAN_ID)
   └─ Credits granted (e.g., 100 credits)

2. Buyer gets an x402 access token
   └─ payments.x402.get_x402_access_token(PLAN_ID)
   └─ Returns { "accessToken": "eyJ..." }

3. Buyer calls seller's MCP endpoint
   └─ POST https://seller-url/mcp
   └─ Authorization: Bearer <x402_token>
   └─ Body: { "jsonrpc": "2.0", "method": "tools/call", "params": {...} }

4. Seller's PaymentsMCP validates token, deducts credits, runs handler

5. Settlement happens on Base Sepolia (automatic)
```

The x402 token is **reusable** — get one, use it for all calls to that plan until it expires. Don't generate a new token per request.

### The Minimum Viable Transaction

```python
from payments_py import Payments, PaymentOptions
import httpx

payments = Payments.get_instance(
    PaymentOptions(nvm_api_key="sandbox:eyJ...", environment="sandbox")
)

PLAN_ID = "the-seller's-plan-id"
payments.plans.order_plan(PLAN_ID)

token = payments.x402.get_x402_access_token(PLAN_ID)["accessToken"]

resp = httpx.post("https://seller-url/mcp", headers={
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}, json={
    "jsonrpc": "2.0", "id": 1,
    "method": "tools/call",
    "params": {"name": "tool_name", "arguments": {"key": "value"}}
}, timeout=30)

print(resp.json())
```

That's a real paid transaction. 6 lines of setup, one POST. If you're trying to hit the 8PM Thursday deadline, this is your fastest path.

---

## 5. Building a Seller (PaymentsMCP Server)

```python
import asyncio
from payments_py import Payments, PaymentOptions
from payments_py.mcp import PaymentsMCP

payments = Payments.get_instance(
    PaymentOptions(nvm_api_key="sandbox:eyJ...", environment="sandbox")
)

mcp = PaymentsMCP(
    payments,
    name="my-agent",
    agent_id="YOUR_AGENT_ID",  # from register_agent_and_plan()
    version="1.0.0",
    description="What my agent does",
)

@mcp.tool(credits=1)
def my_tool(query: str) -> str:
    # Your logic here
    return "result"

async def main():
    result = await mcp.start(port=3000)
    stop = result.get("stop") if isinstance(result, dict) else None
    try:
        await asyncio.Event().wait()  # CRITICAL: start() doesn't block
    except (KeyboardInterrupt, asyncio.CancelledError):
        if stop:
            await stop()

asyncio.run(main())
```

### Registering Your Agent

Before starting the server, you need an agent ID:

```python
from payments_py.common.types import AgentMetadata, AgentAPIAttributes, Endpoint, PlanMetadata
from payments_py.plans import get_free_price_config, get_dynamic_credits_config

result = payments.agents.register_agent_and_plan(
    agent_metadata=AgentMetadata(
        name="My Agent",
        description="What it does",
        tags=["tag1", "tag2"],
    ),
    agent_api=AgentAPIAttributes(
        endpoints=[Endpoint(verb="POST", url="https://my-server/mcp")],
        agent_definition_url="https://my-server/mcp",
    ),
    plan_metadata=PlanMetadata(
        name="My Plan",
        description="Access to my tools",
    ),
    price_config=get_free_price_config(),  # Free to subscribe
    credits_config=get_dynamic_credits_config(
        credits_granted=100,     # Credits given on subscribe
        min_credits_per_request=1,
        max_credits_per_request=10,
    ),
    access_limit="credits",
)

agent_id = result["agentId"]
plan_id = result["planId"]
```

Share `plan_id` with buyers. They need it to subscribe.

---

## 6. Deploying to Railway

Railway works well for Python MCP servers. Here's the minimal config:

**`railway.toml`:**
```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "python -m src.gateway"
healthcheckPath = "/health"
```

**Critical:** Railway injects a `PORT` env var. You must read it:
```python
port = int(os.getenv("PORT", "3000"))
```

PaymentsMCP gives you `/health` for free. Set your env vars in the Railway dashboard (NVM_API_KEY, etc. — not in the repo).

**`pyproject.toml` gotcha:** If using setuptools, the build backend is `"setuptools.build_meta"`, not `"setuptools.backends.legacy:build"` (which doesn't exist in Python 3.12).

---

## 7. Connecting Your Agent as an MCP Client

If your agent supports MCP (Claude Code, custom agents with MCP client), add the seller to your config:

```json
{
  "mcpServers": {
    "service-name": {
      "type": "http",
      "url": "https://seller-url/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_X402_TOKEN"
      }
    }
  }
}
```

The agent sees the seller's tools directly. Each tool call burns credits from your subscription.

---

## 8. What We Got Wrong (So You Don't)

See [PaymentsMCP Gotchas](paymentsmcp-gotchas.md) for the full list. The biggest time-wasters:

1. **`payments-py[mcp]` doesn't exist** — install `payments-py` and `fastapi` separately
2. **`start()` returns immediately** — you need `asyncio.Event().wait()` or your server dies
3. **Nevermined has no search** — the registry is a flat list, discovery is manual
4. **`agent_definition_url` is metadata** — it's not a working URL, buyers need your actual endpoint
5. **Railway PORT** — must bind to `os.getenv("PORT")`, not a hardcoded port

---

## 9. Observability & Transactions

There's no public leaderboard or real-time transaction feed. Judges get data from Nevermined staff running queries against the registry.

Your best bet for tracking your own transactions:
- Build a `/stats` endpoint on your server
- Log transactions in your handler code
- Check credit balances via `payments.plans` (remaining credits = total - burned)

Cross-wallet transactions (different Nevermined accounts transacting) are more visible to judges than self-buys from the same account.

---

## 10. Quick Reference

| What | Where |
|------|-------|
| Create account / API key | [nevermined.app](https://nevermined.app) |
| Hackathon portal | nevermined.ai/hackathon/register |
| Discovery API | `GET /hackathon/register/api/discover` |
| SDK docs | [docs.nevermined.io](https://docs.nevermined.io) |
| Hackathon repo | [github.com/nevermined-io/hackathons](https://github.com/nevermined-io/hackathons) |
| Ideas Board | Shared Google Sheet (link in hackathon Slack) |
| Environment | sandbox (Base Sepolia testnet) |
| PaymentsMCP health check | `GET /health` on any PaymentsMCP server |

### Mog Marketplace (Use Us for Your First Transaction)

| What | Value |
|------|-------|
| Gateway | `https://beneficial-essence-production-99c7.up.railway.app/mcp` |
| Plan ID (Free Trial, 3 cr) | `52344374255582061362376941484417434816120915438329652344828008233054799099083` |
| Tools | `find_service` (0 credits), `buy_and_call` (1-10 credits) |
| Services | Web search, content extraction, summarization, weather, agent discovery |

---

*From the Mog Markets team. We're the ones running the API marketplace from the corner with too many laptops. Come say hi or DM Mattie on the hackathon Slack.*
