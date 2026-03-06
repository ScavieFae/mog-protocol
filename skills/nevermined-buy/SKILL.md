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

**If they gave an endpoint URL**: You have the URL. You still need a plan ID -- try calling the endpoint to see if it returns tool listings, or ask the user.

**If they gave a team/service name**: Search the Nevermined marketplace to find the agent:

```python
from payments_py import Payments, PaymentOptions
import os

payments = Payments.get_instance(
    PaymentOptions(
        nvm_api_key=os.getenv("NVM_API_KEY") or "YOUR_KEY",
        environment="sandbox"
    )
)

# Search for the agent
results = payments.agents.search(query="TARGET_NAME_HERE")
print(results)
```

Look through results for matching agents. Show the user what you found -- name, description, pricing, plan IDs. Let them confirm which one.

If the search doesn't work or returns nothing, check the hackathon marketplace directly:
- https://nevermined.app (browse agents in the sandbox environment)
- Ask the user if the seller gave them a plan ID or URL

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

```python
import httpx

resp = httpx.post("ENDPOINT_URL_HERE", headers={
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}, json={
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

This calls `tools/list` to see what tools the server exposes. Show the user the available tools.

Then make one real call if possible (pick the simplest/cheapest tool):

```python
resp = httpx.post("ENDPOINT_URL_HERE", headers={
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}, json={
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
