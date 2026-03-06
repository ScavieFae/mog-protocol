---
name: nevermined-buy
description: Buy from a Nevermined marketplace agent. Use when the user asks to "buy from", "connect to", "subscribe to", or "purchase from" a service on the Nevermined hackathon marketplace, or mentions buying credits, getting an access token, or configuring MCP for a Nevermined-powered service.
---

# Buy from a Nevermined Marketplace Agent

You are helping the user subscribe to and connect with a service on the Nevermined hackathon marketplace. The user wants to buy from another team's agent. Your job: find the service, subscribe, get a token, configure MCP, and verify with a test call.

**Target:** $ARGUMENTS

This could be a team name, service description, agent name, plan ID, or MCP endpoint URL. Figure out what they gave you and work from there.

## Step 0: Prerequisites

Check that the user has what they need:

```bash
pip install payments-py httpx 2>/dev/null || pip install payments-py httpx
```

Check for a Nevermined API key. Look in `.env` for `NVM_API_KEY`, `NVM_BUYER_API_KEY`, or similar. If not found, ask the user:

> You need a Nevermined API key. Go to https://nevermined.app, create an account, and generate an API key with all 4 permissions enabled (Register, Purchase, Issue, Redeem). Your key looks like `sandbox:eyJ...`. Paste it here.

## Step 1: Find the Service

Based on what the user gave you, resolve it to a **plan ID** and **MCP endpoint URL**.

**If they gave a plan ID** (long number): Use it directly. You still need the endpoint URL -- ask the user or search for it.

**If they gave an endpoint URL**: Try to extract the plan ID from the server's error response. Hit the endpoint without auth and check what comes back:

- **402 + `payment-required` header** (x402 pattern): Decode the base64 header to get plan ID and agent ID
- **401** (bearer pattern): No plan ID in the response -- you'll need it from the user or marketplace UI

```python
import httpx, json, base64

resp = httpx.post("ENDPOINT_URL_HERE", headers={
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}, json={
    "jsonrpc": "2.0",
    "method": "tools/list",
    "params": {},
    "id": 1,
}, timeout=15)

# Should be 402 — decode the payment-required header
if resp.status_code == 402 and "payment-required" in resp.headers:
    payment_info = json.loads(base64.b64decode(resp.headers["payment-required"]))
    print(json.dumps(payment_info, indent=2))
    # Plan ID and agent ID are in payment_info["accepts"][0]
    plan_id = payment_info["accepts"][0]["planId"]
    agent_id = payment_info["accepts"][0]["extra"]["agentId"]
    print(f"Plan ID: {plan_id}")
    print(f"Agent ID: {agent_id}")
```

The `accepts` array may list multiple plans (card, USDC, free). Pick the one matching the user's preferred payment method.

To see ALL plans for this agent (including free tiers not in the 402):

```python
plans = payments.agents.get_agent_plans(agent_id)
for p in plans.get("plans", []):
    price = p.get("registry", {}).get("price", {})
    credits = p.get("registry", {}).get("credits", {})
    name = p.get("metadata", {}).get("main", {}).get("name", "unnamed")
    is_free = all(int(a) == 0 for a in price.get("amounts", ["1"]))
    print(f"  {name}: plan_id={p['id']}, free={is_free}, credits={credits.get('amount')}")
```

**If they gave a team/service name**: The `payments-py` SDK does NOT have a search method. Instead:

1. If you have ANY endpoint URL for them, use the 402 method above to get the plan ID
2. Browse https://nevermined.app and search for the agent in the sandbox environment
3. Ask the user if the seller gave them a plan ID or endpoint URL

## Step 2: Subscribe

Once you have the plan ID:

```python
from payments_py import Payments, PaymentOptions
import os

payments = Payments.get_instance(
    PaymentOptions(
        nvm_api_key=os.getenv("NVM_API_KEY") or "YOUR_KEY",
        environment="sandbox"
    )
)

PLAN_ID = "THE_PLAN_ID"

# Check if already subscribed
try:
    balance = payments.plans.get_plan_balance(PLAN_ID)
    print(f"Balance: {balance}")
    if balance.is_subscriber:
        print("Already subscribed!")
    else:
        payments.plans.order_plan(PLAN_ID)
        print("Subscribed.")
except:
    payments.plans.order_plan(PLAN_ID)
    print("Subscribed.")
```

## Step 3: Get Access Token

```python
token = payments.x402.get_x402_access_token(PLAN_ID)["accessToken"]
print(f"Token: {token}")
```

Save this token -- the user needs it for MCP config.

## Step 4: Configure MCP

Generate the MCP config block for the user's `.mcp.json`:

```json
{
  "mcpServers": {
    "SERVICE_NAME_HERE": {
      "type": "http",
      "url": "ENDPOINT_URL_HERE",
      "headers": {
        "Authorization": "Bearer THE_TOKEN"
      }
    }
  }
}
```

Tell the user to add this to their `.mcp.json` (or Claude Desktop config, or whatever MCP client they use). Use a descriptive key name based on the service.

## Step 5: Test Call

Make a test call to verify the connection works:

PaymentsMCP servers use the `payment-signature` header (NOT `Authorization: Bearer`):

```python
import httpx

headers = {
    "payment-signature": token,
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}

# List tools
resp = httpx.post("ENDPOINT_URL_HERE", headers=headers, json={
    "jsonrpc": "2.0",
    "method": "tools/list",
    "params": {},
    "id": 1,
}, timeout=30)

print(resp.status_code)
tools = resp.json().get("result", {}).get("tools", [])
for t in tools:
    print(f"  {t['name']}: {t.get('description', '')[:80]}")
```

If `payment-signature` gets a 402, try `Authorization: Bearer {token}` instead -- some servers use standard bearer auth.

Then make one real call (pick the simplest/cheapest tool):

```python
resp = httpx.post("ENDPOINT_URL_HERE", headers=headers, json={
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {"name": "TOOL_NAME", "arguments": {}},
    "id": 2,
}, timeout=30)

print(resp.json())
```

## Step 6: Summary

Output a clean summary:

```
CONNECTED: [service name]
ENDPOINT: [url]
PLAN ID: [plan_id]
TOOLS: [list of available tools]
CREDITS: [balance if known]
MCP CONFIG: [the json block above, ready to paste]
```

## Troubleshooting

- **401 Unauthorized**: Token may be expired. Regenerate with `get_x402_access_token`.
- **"Not subscribed"**: Run `order_plan` again. Sometimes takes a moment to propagate.
- **Connection refused**: Check the endpoint URL is correct and the server is running.
- **Empty tool list**: The server might use a different MCP transport. Try adding `/mcp` to the URL if not already there.
- **payments-py import errors**: Make sure you're on the latest version: `pip install -U payments-py`.
