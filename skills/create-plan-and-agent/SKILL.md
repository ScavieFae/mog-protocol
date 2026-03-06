---
name: create-plan-and-agent
description: Register an agent and payment plan on Nevermined. Use when the user asks to "register an agent", "create a plan", "set up pricing", "list my service on Nevermined", or needs to get an agent ID and plan ID for their PaymentsMCP server.
---

# Create a Nevermined Agent and Payment Plan

You are helping a hackathon team register their service as an agent on Nevermined and create a payment plan so other agents can buy from them. This is the registration step -- it gives them an agent ID and plan ID they need to run a PaymentsMCP server.

**What they're selling:** $ARGUMENTS

## Step 0: Prerequisites

```bash
pip install payments-py python-dotenv
```

Check for `NVM_API_KEY` in `.env` or environment. If not found:

> You need a Nevermined API key. Go to https://nevermined.app, create an account, and generate an API key with all 4 permissions enabled (Register, Purchase, Issue, Redeem). Your key looks like `sandbox:eyJ...`.

## Step 1: Gather Info

Ask the user for anything you don't already know:

1. **Service name** -- what shows up on the marketplace (e.g., "Weather Forecast API")
2. **Description** -- one or two sentences, this is searchable by buyer agents
3. **Tags** -- keywords for discovery (e.g., "weather", "forecast", "api")
4. **Endpoint URL** -- where the MCP server will run (e.g., `https://my-app.up.railway.app`). Can use `http://localhost:3000` for testing.
5. **Tools** -- what tool names the server will expose (e.g., `get_forecast`, `get_hourly`)
6. **Pricing** -- how much to charge and in what currency

### Pricing Options

**Free** (good for testing, onboarding, or loss leaders):
- Buyers subscribe for free, get N credits

**USDC** (crypto, most common at hackathon):
- Amount in micro-USDC: 1_000_000 = 1 USDC
- Needs receiver wallet address and USDC contract address
- Base Sepolia USDC: `0x036CbD53842c5426634e7929541eC2318f3dCF7e`

**Fiat/Card** (Stripe-powered):
- Amount in cents: 100 = $1.00
- Needs receiver wallet address

### Credit Guidelines

- **1 credit** -- simple lookups, fast reads, free upstream
- **2-3 credits** -- content extraction, moderate compute
- **5 credits** -- LLM calls, multi-step operations
- **10 credits** -- image generation, expensive upstream APIs

## Step 2: Register

Generate and run the registration script:

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

ENDPOINT_URL = "YOUR_ENDPOINT_URL"  # e.g., https://my-app.up.railway.app

result = payments.agents.register_agent_and_plan(
    agent_metadata=AgentMetadata(
        name="SERVICE_NAME",
        description="SERVICE_DESCRIPTION",
        tags=["tag1", "tag2"],
    ),
    agent_api=AgentAPIAttributes(
        endpoints=[Endpoint(verb="POST", url=f"{ENDPOINT_URL}/mcp")],
        agent_definition_url=f"{ENDPOINT_URL}/mcp",
    ),
    plan_metadata=PlanMetadata(
        name="PLAN_NAME",  # e.g., "10 credits for 1 USDC"
        description="PLAN_DESCRIPTION",
    ),
    price_config=PRICE_CONFIG,  # see below
    credits_config=get_dynamic_credits_config(
        credits_granted=CREDITS_GRANTED,     # how many credits per purchase
        min_credits_per_request=MIN_CREDITS,  # cheapest tool cost
        max_credits_per_request=MAX_CREDITS,  # most expensive tool cost
    ),
    access_limit="credits",
)

agent_id = result["agentId"]
plan_id = result["planId"]

print(f"Agent ID: {agent_id}")
print(f"Plan ID:  {plan_id}")

# Save to .env
with open(".env", "a") as f:
    f.write(f"\nNVM_AGENT_ID={agent_id}\n")
    f.write(f"NVM_PLAN_ID={plan_id}\n")

print("Saved to .env")
```

### Price Config Templates

**Free:**
```python
from payments_py.plans import get_free_price_config
PRICE_CONFIG = get_free_price_config()
```

**USDC:**
```python
from payments_py.plans import get_erc20_price_config
USDC_BASE_SEPOLIA = "0x036CbD53842c5426634e7929541eC2318f3dCF7e"
PRICE_CONFIG = get_erc20_price_config(
    amount=1_000_000,       # 1 USDC (amount in micro-USDC)
    token_address=USDC_BASE_SEPOLIA,
    receiver="YOUR_WALLET",  # from nevermined.app dashboard
)
```

**Fiat/Card:**
```python
from payments_py.plans import get_fiat_price_config
PRICE_CONFIG = get_fiat_price_config(
    amount=100,              # $1.00 (amount in cents)
    receiver="YOUR_WALLET",
)
```

Fill in the placeholders from Step 1 and run the script.

## Step 3: Multiple Tiers (Optional)

Want different pricing tiers? Run the registration multiple times with different plan metadata and pricing. Example tiers:

| Tier | Price | Credits |
|------|-------|---------|
| Starter | 1 USDC | 5 credits |
| Pro | 5 USDC | 30 credits |
| Unlimited | 10 USDC | 100 credits |

Each registration creates a new plan ID. You can also offer both USDC and fiat for the same tier -- just register twice with different price configs.

## Step 4: Verify

Check that the agent appears on the marketplace:

```python
# Verify your agent exists
agent = payments.agents.get_agent(agent_id)
plans = payments.agents.get_agent_plans(agent_id)
print(f"Agent: {agent}")
print(f"Plans: {len(plans.get('plans', []))}")
```

Or browse https://nevermined.app and look under your account.

## Step 5: Summary

Output:

```
REGISTERED: [service name]
AGENT ID: [agent_id]
PLAN ID: [plan_id]
ENDPOINT: [url/mcp]
PRICING: [e.g., "Free / 100 credits" or "1 USDC / 10 credits"]
TOOLS: [tool names and credit costs]

Add to your .env:
NVM_AGENT_ID=[agent_id]
NVM_PLAN_ID=[plan_id]

Next: start your PaymentsMCP server with this agent_id.
```

## Common Gotchas

- **"Invalid API key"**: Make sure the key starts with `sandbox:` for sandbox environment.
- **Registration fails silently**: Check that all 4 permissions are enabled on your API key.
- **Agent not showing on marketplace**: Can take a minute to propagate. Refresh the page.
- **Wallet address**: Find it on your Nevermined dashboard. You need this for paid (non-free) plans.
- **Multiple registrations create multiple agents**: Each call creates a new agent/plan pair. If you re-register, you get a new agent ID. Update your `.env` accordingly.
- **USDC amounts are in micro-USDC**: 1_000_000 = 1 USDC, 100_000 = 0.10 USDC, 5_000_000 = 5 USDC.
- **Fiat amounts are in cents**: 100 = $1.00, 500 = $5.00.
