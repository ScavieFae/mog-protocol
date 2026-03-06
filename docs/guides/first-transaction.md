# Your First Nevermined Transaction in 5 Minutes

You're at the hackathon. You need a paid agent-to-agent transaction. Here's the fastest path.

**What you'll do:** Subscribe to a plan, get an access token, call an API through Nevermined's x402 payment protocol. Real credits burn, real on-chain settlement.

**What you'll call:** The Mog Marketplace gateway — it has web search, content extraction, and text summarization behind a two-tool interface. You find a service, you buy it, done.

---

## Step 1: Get Your API Key (2 min)

Go to [nevermined.app](https://nevermined.app), create an account, generate an API key.

When creating the key, enable all four permissions:
- **Register** agents and plans
- **Purchase** plans
- **Issue** access tokens
- **Redeem** credits

Your key will look like: `sandbox:eyJhbGciOiJF...`

Save it. You only need this one key — it works for both building and buying.

## Step 2: Install the SDK (30 sec)

```bash
pip install payments-py httpx python-dotenv
```

## Step 3: Subscribe and Call (2 min)

Create a file called `first_buy.py`:

```python
import httpx
from payments_py import Payments, PaymentOptions

# Your key from Step 1
NVM_API_KEY = "sandbox:eyJhbG..."  # paste yours here

# Mog Marketplace plan — already registered, ready to buy from
PLAN_ID = "56064655340635502751035227097531184395429221588387852227963461103927877061446"
GATEWAY = "https://beneficial-essence-production-99c7.up.railway.app"

# Connect to Nevermined
payments = Payments.get_instance(
    PaymentOptions(nvm_api_key=NVM_API_KEY, environment="sandbox")
)

# Subscribe to the plan (free — grants you 100 credits)
print("Subscribing...")
payments.plans.order_plan(PLAN_ID)

# Get your x402 access token
token = payments.x402.get_x402_access_token(PLAN_ID)["accessToken"]
print(f"Token: {token[:30]}...")

# Call find_service — discover what's available (costs 0 credits)
print("\nSearching for services...")
resp = httpx.post(f"{GATEWAY}/mcp", headers={
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}, json={
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {"name": "find_service", "arguments": {"query": "web search"}},
    "id": 1,
}, timeout=30)

print(resp.json()["result"]["content"][0]["text"][:500])

# Call buy_and_call — actually buy a service (costs 1 credit)
print("\nBuying exa_search...")
resp = httpx.post(f"{GATEWAY}/mcp", headers={
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}, json={
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {"name": "buy_and_call", "arguments": {
        "service_id": "exa_search",
        "params": {"query": "Nevermined autonomous agents", "max_results": 3}
    }},
    "id": 2,
}, timeout=30)

result = resp.json()["result"]
print(result["content"][0]["text"][:500])
print("\nPayment meta:", result.get("_meta", {}))
print("\nDone! Check your balance — 1 credit burned.")
```

Run it:
```bash
python first_buy.py
```

That's it. You just completed a paid agent-to-agent transaction through Nevermined.

---

## What Just Happened

1. **You subscribed** to the Mog Marketplace plan → Nevermined granted you 100 credits
2. **You got an x402 token** → a signed bearer token that proves you have credits
3. **You called `find_service`** → searched the marketplace (free, 0 credits)
4. **You called `buy_and_call`** → executed `exa_search`, which did a real Exa web search and returned results. 1 credit burned. Settled on Base Sepolia.

## What's Available

The Mog Marketplace currently has these services:

| Service | Credits | What It Does |
|---------|---------|-------------|
| `exa_search` | 1 | Semantic web search with snippets and URLs |
| `exa_get_contents` | 2 | Fetch full text from URLs |
| `claude_summarize` | 5 | Summarize text (bullets, paragraph, or structured) |

Use `find_service` to discover them — it does semantic search, so queries like "I need to research a topic" or "get the text of this webpage" will match.

## Connect Your Agent via MCP

If your agent supports MCP, add this to your `.mcp.json`:

```json
{
  "mcpServers": {
    "mog-marketplace": {
      "type": "http",
      "url": "https://beneficial-essence-production-99c7.up.railway.app/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_X402_TOKEN_HERE"
      }
    }
  }
}
```

Your agent gets two tools: `find_service` and `buy_and_call`. That's it. ~200 tokens of context regardless of how many services are behind the gateway.

## Common Gotchas

**"I got a 401 Unauthorized"**
→ Your x402 token might be expired. Get a fresh one with `payments.x402.get_x402_access_token(PLAN_ID)`.

**"payments-py[mcp] doesn't install"**
→ The `[mcp]` extra doesn't exist in payments-py 1.3.x. Install `payments-py` and `fastapi` separately.

**"PaymentsMCP.start() exits immediately"**
→ `start()` returns a dict. You need `await asyncio.Event().wait()` to keep the server alive. See our [gateway source](https://github.com/ScavieFae/mog-protocol/blob/main/src/gateway.py).

**"Do I need two API keys?"**
→ No. One key with all four permissions works for both building (selling) and subscribing (buying).

---

*Built by the Mog Protocol team at the Nevermined Autonomous Business Hackathon, March 2026.*
*Gateway: https://beneficial-essence-production-99c7.up.railway.app*
