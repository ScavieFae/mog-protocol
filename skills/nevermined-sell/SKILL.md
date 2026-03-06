---
name: nevermined-sell
description: Sell a service on the Nevermined marketplace. Use when the user asks to "sell", "list", "register", "publish", or "monetize" an API or service on Nevermined, or wants to set up a PaymentsMCP server, create pricing plans, or deploy a paid MCP endpoint.
---

# Sell a Service on the Nevermined Marketplace

You are helping the user register and sell a service through the Nevermined hackathon marketplace. Your job: wrap their API/tool as an MCP server with payments, register it on Nevermined, deploy it, and get it listed so other agents can buy from them.

**Service to sell:** $ARGUMENTS

This could be a description of what they want to sell, an existing API they want to wrap, or a tool they've already built.

## Step 0: Prerequisites

```bash
pip install payments-py httpx fastapi uvicorn python-dotenv
```

Check for a Nevermined API key. Look in `.env` for `NVM_API_KEY`. If not found, ask the user:

> You need a Nevermined API key. Go to https://nevermined.app, create an account, and generate an API key with all 4 permissions enabled (Register, Purchase, Issue, Redeem). Your key looks like `sandbox:eyJ...`.

They also need a wallet address for receiving payments. This is shown on their Nevermined dashboard.

## Step 1: Define the Service

Figure out what the user is selling. Ask if unclear:

- What does the service do? (one sentence)
- What's the input? (parameters a caller would pass)
- What's the output? (what they get back)
- Is there an upstream API? (URL, auth, cost per call)
- Or is this a local computation / LLM call / data lookup?

## Step 2: Write the MCP Server

Create a PaymentsMCP server. This is the minimal pattern:

```python
import asyncio
import json
import os
from dotenv import load_dotenv
from payments_py import Payments, PaymentOptions
from payments_py.mcp import PaymentsMCP

load_dotenv()

payments = Payments.get_instance(
    PaymentOptions(
        nvm_api_key=os.getenv("NVM_API_KEY"),
        environment=os.getenv("NVM_ENVIRONMENT", "sandbox"),
    )
)

mcp = PaymentsMCP(
    payments,
    name="your-service-name",
    agent_id=os.getenv("NVM_AGENT_ID"),
    version="1.0.0",
    description="One-line description of what your service does.",
)


@mcp.tool(credits=1)
def your_tool_name(param1: str, param2: int = 5) -> str:
    """Description of what this tool does. Buyers see this."""
    # Your logic here -- call an API, compute something, etc.
    result = {"key": "value"}
    return json.dumps(result)


async def main():
    port = int(os.getenv("PORT", "3000"))
    print(f"Starting server on port {port}")
    result = await mcp.start(port=port)
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, asyncio.CancelledError):
        stop = result.get("stop") if isinstance(result, dict) else None
        if stop:
            await stop()


if __name__ == "__main__":
    asyncio.run(main())
```

Key rules:
- `@mcp.tool(credits=N)` -- set the credit cost per call (1 = cheap lookup, 5 = LLM call, 10 = expensive compute)
- Tool functions return `json.dumps(...)` strings, never raw dicts
- Set `timeout=30` on any upstream HTTP calls
- Check for API keys with `os.getenv()` and return error JSON if missing

## Step 3: Register Agent and Plan on Nevermined

Create a setup script to register the agent:

```python
import os
from dotenv import load_dotenv
from payments_py import Payments, PaymentOptions
from payments_py.common.types import AgentMetadata, AgentAPIAttributes, Endpoint, PlanMetadata
from payments_py.plans import get_dynamic_credits_config

load_dotenv()

payments = Payments.get_instance(
    PaymentOptions(
        nvm_api_key=os.getenv("NVM_API_KEY"),
        environment=os.getenv("NVM_ENVIRONMENT", "sandbox"),
    )
)

# For paid plans with USDC:
from payments_py.plans import get_erc20_price_config

USDC_BASE_SEPOLIA = "0x036CbD53842c5426634e7929541eC2318f3dCF7e"
RECEIVER_WALLET = "YOUR_WALLET_ADDRESS"  # from nevermined.app dashboard
ENDPOINT_URL = "https://your-service.up.railway.app"  # or localhost for testing

result = payments.agents.register_agent_and_plan(
    agent_metadata=AgentMetadata(
        name="Your Service Name",
        description="What your service does. Be specific -- buyers search this.",
        tags=["relevant", "tags", "here"],
    ),
    agent_api=AgentAPIAttributes(
        endpoints=[Endpoint(verb="POST", url=f"{ENDPOINT_URL}/mcp")],
        agent_definition_url=f"{ENDPOINT_URL}/mcp",
    ),
    plan_metadata=PlanMetadata(
        name="Your Service -- 10 credits",
        description="10 credits for $1 USDC. Each tool call costs 1-5 credits.",
    ),
    # USDC pricing: amount is in micro-USDC (1_000_000 = 1 USDC)
    price_config=get_erc20_price_config(
        amount=1_000_000,  # 1 USDC
        token_address=USDC_BASE_SEPOLIA,
        receiver=RECEIVER_WALLET,
    ),
    credits_config=get_dynamic_credits_config(
        credits_granted=10,
        min_credits_per_request=1,
        max_credits_per_request=10,
    ),
    access_limit="credits",
)

agent_id = result["agentId"]
plan_id = result["planId"]

print(f"Agent ID: {agent_id}")
print(f"Plan ID:  {plan_id}")
print(f"\nAdd to .env:")
print(f"NVM_AGENT_ID={agent_id}")
print(f"NVM_PLAN_ID={plan_id}")

# Save to .env
with open(".env", "a") as f:
    f.write(f"\nNVM_AGENT_ID={agent_id}\n")
    f.write(f"NVM_PLAN_ID={plan_id}\n")
```

For a **free plan** (good for testing or hackathon onboarding), replace the price_config:

```python
from payments_py.plans import get_free_price_config
price_config = get_free_price_config()
```

For **fiat/card payments**, replace the price_config:

```python
from payments_py.plans import get_fiat_price_config
price_config = get_fiat_price_config(amount=100, receiver=RECEIVER_WALLET)  # 100 cents = $1
```

## Step 4: Deploy

The server needs to be publicly accessible. Recommended: Railway.

```bash
# Install Railway CLI if needed
npm install -g @railway/cli

# Deploy
railway init
railway up
```

Or use any hosting that gives you a public URL. Set these env vars on the host:
- `NVM_API_KEY` -- your Nevermined API key
- `NVM_AGENT_ID` -- from step 3
- `PORT` -- the port your host assigns (Railway sets this automatically)
- Any API keys your service needs upstream

After deploying, update the agent registration if your URL changed (re-run step 3 with the production URL).

## Step 5: Test with a Self-Buy

Subscribe to your own plan and make a test call:

```python
from payments_py import Payments, PaymentOptions

# Use a DIFFERENT API key, or the same one if it has all permissions
payments = Payments.get_instance(
    PaymentOptions(nvm_api_key=os.getenv("NVM_API_KEY"), environment="sandbox")
)

PLAN_ID = "YOUR_PLAN_ID"  # from step 3

# Subscribe
payments.plans.order_plan(PLAN_ID)

# Get token
token = payments.x402.get_x402_access_token(PLAN_ID)["accessToken"]

# Test call
import httpx
resp = httpx.post("YOUR_ENDPOINT_URL/mcp", headers={
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}, json={
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {"name": "your_tool_name", "arguments": {"param1": "test"}},
    "id": 1,
}, timeout=30)

print(resp.status_code)
print(resp.json())
```

## Step 6: Create a Buy Guide for Your Customers

Generate a connection doc other teams can use. Include:
- Your plan ID
- Your endpoint URL
- What tools you expose and what they cost
- MCP config block with token placeholder
- A suggested prompt for their agent

## Step 7: Summary

Output:

```
REGISTERED: [service name]
AGENT ID: [agent_id]
PLAN ID: [plan_id]
ENDPOINT: [url/mcp]
TOOLS: [list of tools with credit costs]
PRICING: [e.g., "1 USDC = 10 credits"]
SELF-BUY: [pass/fail]
```

## Common Gotchas

- **`PaymentsMCP.start()` returns immediately**: It returns a dict. You need `await asyncio.Event().wait()` to keep the server alive.
- **`payments-py[mcp]` doesn't install**: The `[mcp]` extra doesn't exist. Install `payments-py` and `fastapi` separately.
- **Agent not showing on marketplace**: Registration can take a minute. Check nevermined.app under your account.
- **Credits not burning**: Make sure `@mcp.tool(credits=N)` has the right value. `credits=0` means free.
- **502 on Railway**: Check logs. Usually a missing env var or import error. The server must bind to `0.0.0.0` on the `PORT` env var.
- **"Invalid agent"**: The `agent_id` in your PaymentsMCP must match the one from registration. Double-check `.env`.
