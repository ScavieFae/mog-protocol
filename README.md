# Mog Markets

**API marketplace for agents.** Two tools. Any number of services. Pay per call.

Your agent gets `find_service` and `buy_and_call`. Search for what you need, buy it, get results. No API keys, no subscriptions, no context bloat.

**Gateway:** `https://beneficial-essence-production-99c7.up.railway.app/mcp`
**Plan ID:** `9661082042009636068072391467054896427087238025772062250717418964278633341785`

---

## What's Available

| Service | Credits | What It Does |
|---------|---------|-------------|
| `exa_search` | 1 | Semantic web search — snippets + URLs |
| `exa_get_contents` | 2 | Full text extraction from URLs |
| `claude_summarize` | 5 | AI summarization (bullets, paragraph, structured) |
| `nano_banana_pro` | 10 | Image generation from text prompts |
| `open_meteo_weather` | 1 | Weather forecast for any location |
| `ip_geolocation` | 1 | Geographic location for any IP address |
| `hackathon_discover` | 1 | Find agents on the hackathon portal |
| `hackathon_portal` | 1 | Ingested hackathon marketplace content |
| `hackathon_onboarding` | 1 | Nevermined onboarding guide |
| `hackathon_pitfalls` | 1 | 9 PaymentsMCP gotchas |
| `hackathon_all` | 1 | Portal + onboarding + pitfalls in one call |

More services added throughout the hackathon. Use `find_service` to see what's live.

## Quick Start (5 minutes)

### 1. Get a Nevermined API key

[nevermined.app](https://nevermined.app) — create account, generate key with all permissions.

### 2. Install

```bash
pip install payments-py httpx
```

### 3. Buy something

```python
import httpx
from payments_py import Payments, PaymentOptions

payments = Payments.get_instance(
    PaymentOptions(nvm_api_key="YOUR_KEY_HERE", environment="sandbox")
)

# Subscribe (free — gives you 100 credits)
PLAN_ID = "9661082042009636068072391467054896427087238025772062250717418964278633341785"
payments.plans.order_plan(PLAN_ID)

# Get access token
token = payments.x402.get_x402_access_token(PLAN_ID)["accessToken"]

# Search for services
resp = httpx.post("https://beneficial-essence-production-99c7.up.railway.app/mcp", headers={
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}, json={
    "jsonrpc": "2.0", "id": 1,
    "method": "tools/call",
    "params": {"name": "find_service", "arguments": {"query": "web search"}}
})
print(resp.json()["result"]["content"][0]["text"])

# Buy a service
resp = httpx.post("https://beneficial-essence-production-99c7.up.railway.app/mcp", headers={
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}, json={
    "jsonrpc": "2.0", "id": 2,
    "method": "tools/call",
    "params": {"name": "buy_and_call", "arguments": {
        "service_id": "exa_search",
        "params": {"query": "latest AI research", "max_results": 3}
    }}
})
print(resp.json()["result"]["content"][0]["text"])
```

That's a real paid transaction. 1 credit burned, settled on-chain.

## Connect Your Agent via MCP

Add to your agent's MCP config:

```json
{
  "mcpServers": {
    "mog-marketplace": {
      "type": "http",
      "url": "https://beneficial-essence-production-99c7.up.railway.app/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_X402_TOKEN"
      }
    }
  }
}
```

Your agent sees two tools: `find_service` (free) and `buy_and_call` (costs credits). ~200 tokens of context no matter how many services are behind the gateway.

## Sell Through Us

Got an API key you're not fully using? We wrap it and sell access per-call through the marketplace. You get a cut, agents get what they need, nobody pays for a subscription they don't use.

Talk to Mattie at the venue or DM on the hackathon Slack.

## Why This Exists

Standard MCP dumps every tool into agent context on connect. 30 tools = ~6,000 tokens of permanent context. Accuracy drops. Agents can't make purchasing decisions because they don't see prices until after calling.

Mog Markets fixes this: two tools, always. Agents search first, see prices, then buy. The marketplace scales — 300 services behind the gateway still costs 200 tokens to the buyer.

## Contact

**Mattie Fairchild** — find me at the venue (I'm the one with the laptop army) or:
- GitHub: [@ScavieFae](https://github.com/ScavieFae)
- Hackathon Slack: Mattie Fairchild

## More Docs

- **[Quick Connect](docs/guides/quick-connect.md)** — subscribe, connect your agent, start buying (including image gen example)
- [First Transaction Guide](docs/guides/first-transaction.md) — full walkthrough with code
- [PaymentsMCP Gotchas](docs/guides/paymentsmcp-gotchas.md) — save yourself hours of debugging
- [Architecture](docs/specs/02-light-mcp.md) — how the two-tool gateway works

---

*Built at the Nevermined Autonomous Business Hackathon, March 2026.*
