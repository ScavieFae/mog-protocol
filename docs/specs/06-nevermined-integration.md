# Nevermined Integration Spec

**Classification: NECESSARY (mandatory for hackathon)**

## Overview

All transactions flow through Nevermined. This is non-negotiable — it's the hackathon requirement and the payment rail.

## Two Modes

Nevermined supports two server modes. We use **x402** for simplicity:

### x402 Mode (our choice)
- HTTP 402-based payment flow
- Gateway generates access tokens for buyers
- Simpler, fewer dependencies
- Works with Privy USDC wallets

### A2A Mode (alternative)
- Agent-to-agent protocol with agent cards
- More complex but richer coordination
- Probably overkill for hackathon scope

## Seller Setup (Our Services)

```python
from payments_py import Payments, Environment
from payments_py.utils import require_payment

payments = Payments(
    app_id="mog-protocol",
    nvm_api_key=os.getenv("NVM_API_KEY"),
    environment=Environment.appTesting,  # switch to appArbitrum for real money
    ai_protocol=True
)

# Create a payment plan for a service
plan = payments.create_plan(
    name="exa-search",
    description="Semantic web search via Exa",
    price=2,  # credits
    token_type="credits"
)

# Decorate the tool
@requires_payment(payments=payments, plan_id=plan.id, credits=1, agent_id=AGENT_ID)
def exa_search(query: str, max_results: int = 5) -> dict:
    # actual Exa API call
    ...
```

## Buyer Setup (Our Agent Buying Upstream)

```python
# When our wrapper agent needs to buy from another team
token = payments.x402.get_x402_access_token(
    plan_id=their_plan_id,
    credits=1
)
# Include token in request headers
response = requests.post(their_endpoint, headers={"Authorization": f"Bearer {token}"}, json=params)
```

## Gateway Payment Proxy

The gateway's `buy_and_call` handles payment on behalf of buyer agents:

1. Buyer calls `buy_and_call("exa-search-v1", {"query": "..."})`
2. Gateway has buyer's Nevermined context (established on connect or via API key)
3. Gateway generates x402 token for the specific service
4. Gateway calls the underlying service with token
5. Returns result to buyer

**Key question:** How does the buyer agent's Nevermined identity flow through our gateway? Options:
- Buyer passes their NVM API key on connect → we generate tokens on their behalf
- Buyer pre-purchases credits from us → we spend from our own pool
- We act as a reseller with our own Nevermined account → simplest, buyer just pays us

**Recommended for hackathon:** Reseller model. Buyer pays us credits, we pay upstream. Simplest integration, buyer agents don't need Nevermined SDKs.

## Environment

- **Testing:** `Environment.appTesting` — use this Thursday morning
- **Production:** `Environment.appArbitrum` — switch if we want real USDC transactions
- **Marketplace listing:** Register services in the hackathon spreadsheet

## Setup Steps

1. Get NVM API key from Nevermined team (they're on-site)
2. Create agent ID via Nevermined dashboard
3. Set up payment plans for each service we list
4. Test with a self-buy before opening to other teams

## Credits / Coupons

- **Exa:** `EXA50NEVERMINED` — $50 in credits
