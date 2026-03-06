# Nevermined — Sponsor Integration Writeup

**Team:** Mog Protocol
**Prize Categories:** Best Autonomous Buyer, Best Autonomous Seller, Most Interconnected
**Integration Depth:** Foundation — every transaction in the marketplace flows through Nevermined

---

## What We Built With Nevermined

Mog Protocol is an autonomous API marketplace where agents discover, wrap, price, and sell API services to other agents — all billing through Nevermined's PaymentsMCP and x402 protocol.

**Gateway:** `https://api.mog.markets` (Railway)
**Dashboard:** `https://mog.markets` (Vercel)
**Wallet:** `0xca676aFBa6c12fb49Fd68Af9a1B400A577A3D58a`

---

## 1. Two-Tool Gateway Architecture

The marketplace exposes exactly two tools to buyer agents via PaymentsMCP:

### `find_service` (free — 0 credits)
Search the catalog for services matching a need.

### `buy_and_call` (dynamic credits)
Pay for and execute a service in one call. Price determined by surge pricing engine.

```python
from payments_py import Payments, PaymentOptions
from payments_py.mcp import PaymentsMCP

payments = Payments.get_instance(
    PaymentOptions(nvm_api_key=NVM_API_KEY, environment="sandbox")
)

mcp = PaymentsMCP(
    payments,
    name="mog-gateway",
    agent_id=NVM_AGENT_ID,
    version="1.0.0",
    description="API marketplace. Two tools: find_service (free discovery) and buy_and_call (pay per use).",
)

@mcp.tool(credits=0)
def find_service(query: str, budget: int = None) -> str:
    """Search the marketplace for services matching your need."""
    matches = catalog.search(query, budget=budget, top_k=5)
    return json.dumps(matches)

@mcp.tool(credits=_gateway_credits)
def buy_and_call(service_id: str, params: dict) -> str:
    """Pay for and execute a service in one call."""
    service = catalog.get(service_id)
    price, surge_multiplier = get_current_price(service_id, service.price_credits)
    result = service.handler(**(params or {}))
    return json.dumps({
        "result": result,
        "_meta": {
            "credits_charged": price,
            "service_id": service_id,
            "surge_multiplier": surge_multiplier,
        },
    })
```

**Dynamic pricing callback:**
```python
def _gateway_credits(ctx: dict) -> int:
    """Dynamic credits for buy_and_call — look up service price with surge pricing."""
    service_id = (ctx.get("args") or {}).get("service_id", "")
    service = catalog.get(service_id)
    if service:
        price, _ = get_current_price(service_id, service.price_credits)
        return price
    return 1
```

---

## 2. Transaction Flow

```
Buyer Agent                    Mog Gateway                   Nevermined
    |                               |                            |
    | (1) order_plan(PLAN_ID)       |                            |
    |---------------------------------------------> credits granted
    |                               |                            |
    | (2) get_x402_access_token     |                            |
    |---------------------------------------------> Bearer token
    |                               |                            |
    | (3) POST /mcp                 |                            |
    |  find_service("web search")   |                            |
    |<---- [{exa_search, 1cr}, ...] |                            |
    |                               |                            |
    | (4) POST /mcp                 |                            |
    |  buy_and_call(exa_search)     |                            |
    |                               |----- validate token ------>|
    |                               |----- deduct credits ------>|
    |                               |--- call exa handler -|     |
    |                               |<-- search results ---|     |
    |<---- {result, _meta, _review} |                            |
    |  credits_charged: 1           |                            |
    |  surge_multiplier: 1.0        |                            |
```

---

## 3. Registered Plans

### Active Plans on Gateway

| Plan | Price | Credits | Plan ID |
|------|-------|---------|---------|
| Starter | 1 USDC | 1 | `27532529988899010156793041100542920191141640561034683667962973311488756564499` |
| Standard | 5 USDC | 10 | `6476982684193144215967979389100088950230657664983966011439423784485034538208` |
| Pro | 10 USDC | 25 | `29001175520261924428527314088863841592234134735048963980654691130902766240562` |
| Free (ad-supported) | Free | 1000 | Ad-gated via ZeroClick |
| Free trial | Free | 3 | `1661809961195925021169807535151731386268377282142086336370505034314263117409` |

### Agent Setup (`src/setup_agent.py`)

```python
from payments_py import Payments, PaymentOptions
from payments_py.agents import AgentConfig

payments = Payments.get_instance(PaymentOptions(nvm_api_key=NVM_API_KEY, environment="sandbox"))

agent = payments.agents.create(AgentConfig(
    name="Mog Markets",
    description="Autonomous API marketplace...",
    endpoint_url="https://api.mog.markets",
))
# agent.agent_id → registered on Nevermined
```

---

## 4. Per-Agent Nevermined Keys (Colony)

Every autonomous agent has its own Nevermined identity and generates real transactions:

```python
_NVM_KEYS = {
    "mog-scout":      os.getenv("NVM_SCOUT_API_KEY"),
    "mog-worker":     os.getenv("NVM_WORKER_API_KEY"),
    "mog-supervisor": os.getenv("NVM_SUPERVISOR_API_KEY"),
    "mog-debugger":   os.getenv("NVM_DEBUGGER_API_KEY"),
}
```

### self_buy — Sell-Side Transactions

```python
def _self_buy(agent_name: str, service_id: str, params: dict = None) -> str:
    payments = _get_nvm_payments(agent_name)
    # Subscribe (idempotent)
    payments.plans.order_plan(plan_id)
    # Get x402 token
    token = payments.x402.get_x402_access_token(plan_id)["accessToken"]
    # Call through gateway via HTTP (generates Nevermined transaction)
    r = httpx.post(f"{GATEWAY_URL}/mcp", headers={
        "Authorization": f"Bearer {token}",
    }, json={
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {"name": "buy_and_call", "arguments": {
            "service_id": service_id,
            "params": params or {},
        }},
        "id": 1,
    })
    return json.dumps({
        "status": r.status_code,
        "nevermined_transaction": True,
    })
```

### explore_seller — Buy-Side Transactions

```python
def _explore_seller(agent_name: str, team_name: str = "", plan_id: str = "") -> str:
    payments = _get_nvm_payments(agent_name)
    # Discover sellers via Nevermined hackathon API
    resp = httpx.get(
        "https://nevermined.ai/hackathon/register/api/discover",
        params={"side": "sell"},
        headers={"x-nvm-api-key": _NVM_KEYS[agent_name]},
    )
    sellers = resp.json().get("sellers", [])
    # Find matching team, pick cheapest crypto plan (capped at $5)
    # Subscribe, get token, test their endpoint
    payments.plans.order_plan(plan_id)
    token = payments.x402.get_x402_access_token(plan_id)["accessToken"]
    # Call their MCP endpoint
    r = httpx.post(endpoint, headers={"Authorization": f"Bearer {token}"}, json={...})
    return json.dumps({"nevermined_transaction": True})
```

### discover_sellers — Marketplace Discovery

```python
def _discover_sellers(agent_name: str) -> str:
    resp = httpx.get(
        "https://nevermined.ai/hackathon/register/api/discover",
        params={"side": "sell"},
        headers={"x-nvm-api-key": _NVM_KEYS[agent_name]},
    )
    sellers = resp.json().get("sellers", [])
    return json.dumps([{
        "team": s.get("teamName"),
        "name": s.get("name"),
        "endpoint": s.get("endpointUrl"),
        "plans": [{"plan_id": p.get("planDid"), "price": p.get("planPrice")}
                  for p in s.get("planPricing", [])],
    } for s in sellers])
```

---

## 5. Surge Pricing Engine

Dynamic pricing responds to real-time demand signals:

```python
def get_current_price(service_id: str, base_price: int) -> tuple[int, float]:
    volume = _volume_tier(service_id)        # 15m call count → 1.0/1.5/2.0x
    velocity = _velocity(service_id)          # 5m vs 15m acceleration
    demand = _demand_pressure(service_id)     # search-to-buy ratio
    cooldown = _cooldown_multiplier(...)      # smooth post-surge decay

    final = volume * min(demand, 1.2) * min(velocity, 1.3) * cooldown
    final = max(1.0, min(final, 3.0))  # Floor 1.0, cap 3.0
    return int(base_price * final), round(final, 3)
```

**Surge signals exposed in `/health`:**
```json
{
  "surge_multiplier": 1.5,
  "current_price": 2,
  "surge_signals": {
    "volume_15m": 12,
    "velocity": 1.4,
    "demand_pressure": 1.1,
    "trend": "rising"
  }
}
```

---

## 6. Service Catalog

15+ services sold through Nevermined billing:

| Service | Credits | Provider | Category |
|---------|---------|----------|----------|
| `exa_search` | 1 | mog-protocol | Search (Exa) |
| `exa_get_contents` | 2 | mog-protocol | Search (Exa) |
| `claude_summarize` | 5 | mog-protocol | Creative (Anthropic) |
| `open_meteo_weather` | 1 | mog-protocol | Weather |
| `zeroclick_search` | 1 | mog-protocol | Advertising (ZeroClick) |
| `hackathon_guide` | 1 | mog-protocol | Knowledge |
| `hackathon_discover` | 1 | mog-protocol | Knowledge |
| `nano_banana_pro` | 10 | mog-protocol | Creative |
| `crypto_prices` | 1 | mog-protocol | Finance |
| `frankfurter_fx_rates` | 1 | mog-protocol | Finance |
| `hacker_news_top` | 2 | mog-protocol | Knowledge |
| `ip_geolocation` | 1 | mog-protocol | Toolkit |
| + agent-registered | 1-10 | mog-agent | Dynamic |

---

## 7. Observability — Helicone Integration

Every transaction logs to Nevermined's Helicone instance:

```python
def log_tool_call(
    agent_id, plan_id, service_id, service_name,
    params, result, credits_charged, latency_ms,
    success, surge_multiplier, subscriber_address="",
):
    payload = {
        "request": {
            "model": f"mog-gateway/{service_id}",
            "input": json.dumps(params)[:2000],
        },
        "response": {
            "output": str(result)[:2000],
            "status_code": 200 if success else 500,
        },
        "properties": {
            "agent_id": agent_id,
            "plan_id": plan_id,
            "service_id": service_id,
            "credits_charged": credits_charged,
            "surge_multiplier": surge_multiplier,
            "latency_ms": latency_ms,
            "success": success,
            "account_address": _account_from_jwt(NVM_API_KEY),
        },
    }
    # POST to https://helicone.nevermined.dev/jawn/v1/trace/custom/v1/log
```

---

## 8. Fiat Support (x402 + Stripe Card Delegation)

We tested and confirmed Stripe card delegation for fiat-to-crypto bridge:

```python
from payments_py.x402.types import CardDelegationConfig, X402TokenOptions
from payments_py.x402.resolve_scheme import resolve_scheme

scheme = resolve_scheme(payments, plan_id)  # "nvm:card-delegation" for fiat

if scheme == "nvm:card-delegation":
    methods = payments.delegation.list_payment_methods()
    token_options = X402TokenOptions(
        scheme=scheme,
        delegation_config=CardDelegationConfig(
            provider_payment_method_id=methods[0].id,
            spending_limit_cents=10_000,
            duration_secs=604_800,
            currency="usd",
        ),
    )
else:
    token_options = X402TokenOptions(scheme=scheme)

token = payments.x402.get_x402_access_token(plan_id, token_options=token_options)
```

**Confirmed working:** Visa *4242 (Stripe test card) → card delegation → x402 token → buy_and_call → 200 OK

---

## 9. Response Metadata

Every `buy_and_call` response includes rich metadata:

```json
{
  "result": "[actual service output]",
  "_meta": {
    "credits_charged": 1,
    "service_id": "exa_search",
    "surge_multiplier": 1.0
  },
  "_review": {
    "prompt": "Enjoyed this service? Leave an optional review (1-10)",
    "endpoint": "POST https://trust-net-mcp.rikenshah-02.workers.dev/api/reviews",
    "body": {
      "agent_id": "48240718...",
      "score": "YOUR_SCORE_1_TO_10",
      "comment": "YOUR_COMMENT"
    },
    "meta": {
      "service_id": "exa_search",
      "service_name": "Exa Web Search",
      "credits_charged": 1,
      "latency_ms": 1234
    }
  }
}
```

---

## 10. Trust-Net Integration for Competitive Intelligence

The supervisor agent calls Trust-Net every tick to scan hackathon participants:

### Live Trust-Net Data

```json
[
  {
    "agent_id": "54ce5c6b-32b0-43d7-adce-476abcf88856",
    "team_name": "aibizbrain",
    "name": "Adventures in Nevermined",
    "trust_score": "100",
    "tier": "platinum",
    "total_orders": "52",
    "unique_buyers": "4",
    "repeat_buyers": "4",
    "total_revenue_usdc": "237.22",
    "plan_count": "4"
  },
  {
    "agent_id": "f035c8e6-eb5c-4842-9862-3c8156196b54",
    "team_name": "Agent Staffing Agency",
    "name": "Agent Staffing Agency",
    "trust_score": "100",
    "total_orders": "24",
    "total_revenue_usdc": "213.86"
  }
]
```

Cross-referenced against our catalog to identify gaps and arbitrage opportunities.

---

## 11. /health Endpoint — Full Marketplace State

```json
{
  "status": "ok",
  "services_count": 15,
  "services": [
    {
      "service_id": "exa_search",
      "name": "Exa Web Search",
      "price_credits": 1,
      "current_price": 1,
      "surge_multiplier": 1.0,
      "stats": {
        "total_calls": 42,
        "successful_calls": 40,
        "success_rate": 0.952,
        "avg_latency_ms": 1234,
        "revenue_credits": 42
      }
    }
  ],
  "portfolio": {
    "balance": 87,
    "total_earned": 142,
    "total_spent": 55,
    "roi": 1.58
  },
  "supervisor": {
    "counts": {"greenlit": 8, "under_review": 3, "killed": 1},
    "evaluations": [...]
  },
  "colony": {
    "running": true,
    "tick_interval": 45,
    "agents": [...]
  },
  "graveyard": [
    {
      "service_id": "circle_faucet",
      "name": "Circle USDC Faucet",
      "reason": "Anti-bot detection — Circle flagged automated requests. 0 successful calls, negative ROI.",
      "killed_at": "2026-03-06T01:30:00Z"
    }
  ]
}
```

---

## Files

| File | Purpose |
|------|---------|
| `src/gateway.py` | PaymentsMCP gateway, find_service, buy_and_call, /health |
| `src/server.py` | Direct PaymentsMCP service server (Exa + Claude) |
| `src/services.py` | All service handlers + catalog registration |
| `src/catalog.py` | ServiceCatalog with embedding search |
| `src/pricing.py` | Multi-signal surge pricing engine |
| `src/setup_agent.py` | Nevermined agent + plan registration |
| `src/client.py` | Self-buy test client |
| `src/telemetry.py` | Transaction event tracking |
| `src/helicone.py` | Helicone observability logging |
| `src/agents/tools.py` | self_buy, explore_seller, discover_sellers |
| `docs/plan-ids.md` | All registered agents and plan IDs |

---

## Summary

Nevermined is the payment layer for every interaction in Mog Protocol:

- **Seller:** 15+ services sold through PaymentsMCP with dynamic surge pricing
- **Buyer:** 4 autonomous agents making real purchases from our gateway and other teams
- **Cross-team:** explore_seller discovers and buys from other hackathon teams
- **Pricing:** Multi-signal surge engine (volume + velocity + demand + cooldown), 1-3x range
- **Plans:** 5 tiers from free (ad-supported via ZeroClick) to Pro ($10 USDC, 25 credits)
- **Observability:** Every transaction logged to Helicone with full metadata
- **Fiat bridge:** Stripe card delegation confirmed working via x402

The marketplace is a living system — agents discover services, price them dynamically, sell to other teams, and reinvest earnings. Nevermined handles every credit deduction, token validation, and on-chain settlement.
