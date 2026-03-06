# Spec 11 — Buyer/Seller Debugger Service

**Classification: REVENUE + COMMUNITY (sell diagnostics, build goodwill, gather intel)**

## What It Does

A service in our existing gateway that runs the full Nevermined purchase flow against another team's endpoint — discover, subscribe, get token, test call — and returns a structured diagnostic report. Think "website health check" but for marketplace agents.

The buyer gets: pass/fail, what we see from their endpoint, bugs we hit, error messages, and actionable troubleshooting suggestions.

We get: resellability analysis, competitive intel, and a log of every agent in the ecosystem.

Everybody wins. They pay us to tell them what's broken.

## Why This Is Good

1. **Solves a real pain point.** We know from scanning 30+ sellers that most teams can't tell if their agent works from the buyer side. 9 teams have "Invalid Address undefined." 10 more have auth/payload issues. Nobody's telling them.

2. **Unique service.** No other team can offer this — it requires having built the buy-side infrastructure we already have (`scan_marketplace.py`, the `/nevermined-buy` skill, all the failure pattern knowledge in `buy-troubleshooting.md`).

3. **Self-reinforcing.** Every debugger call gives us fresh marketplace intel. We learn who's online, who fixed their stuff, what new services exist.

4. **Leaderboard play.** Every debug request = a sale for us + a purchase attempt from them = transactions on both sides.

## Architecture

### Just Another Handler

This is a handler in `src/services.py`, registered in the existing gateway catalog. No new files, no separate agent, no separate deployment. The buy-side infrastructure from `scan_marketplace.py` already does the full flow — we refactor its per-seller logic into a callable function.

### Service Flow

```
Buyer agent (Team X)
  │
  ├── 1. Calls buy_and_call(service_id="debug_seller", params={team_name: "X"})
  │     Pays 2 credits (standard gateway pricing)
  │
  ├── 2. Handler resolves target
  │     ├── team_name → discovery API lookup
  │     └── endpoint → direct probe
  │
  ├── 3. Handler runs the buy flow against THEM
  │     ├── Discovery API lookup (plans, endpoint, pricing)
  │     ├── 402 probe (if endpoint exists)
  │     ├── Subscribe to cheapest plan (capped at $1)
  │     ├── Get x402 access token
  │     ├── Test call (MCP tools/list, then REST fallback)
  │     └── Capture: status codes, headers, response bodies, timing
  │
  ├── 4. Handler returns diagnostic report (structured JSON)
  │
  └── 5. Internally: log resellability analysis + marketplace intel
```

### Implementation

Refactor `scan_marketplace.py` lines 26-295 (the per-seller loop) into `_debug_seller()` in `src/services.py`. The existing code already handles:

- Discovery API lookup + plan resolution
- 402 probe for plan discovery
- Subscribe via `payments.plans.order_plan()`
- Token via `payments.x402.get_x402_access_token()`
- Test call with both auth methods (payment-signature, bearer)
- MCP vs REST detection
- Resellability assessment

```python
def _debug_seller(team_name: str = "", endpoint: str = "") -> str:
    """Run the full buy flow against a seller and return diagnostics."""
    if not NVM_API_KEY:
        return json.dumps({"error": "NVM_API_KEY not set"})

    report = {"debug_log": [], "target": {}}

    # 1. Resolve target via discovery API
    # 2. 402 probe if needed
    # 3. Subscribe to cheapest plan (cap $1)
    # 4. Get x402 token
    # 5. Test call (MCP tools/list → REST fallback, both auth methods)
    # 6. Match known issues
    # 7. Generate verdict + suggestions

    return json.dumps(report, indent=2)

catalog.register(
    service_id="debug_seller",
    name="Marketplace Agent Debugger",
    description="Debug any Nevermined marketplace agent. We try to buy from them and "
                "return a full diagnostic: discovery status, endpoint reachability, "
                "subscription flow, auth methods, response analysis, known bugs, and "
                "actionable fixes. Pass team_name or endpoint URL.",
    price_credits=2,
    example_params={"team_name": "AIBizBrain"},
    provider="mog-protocol",
    handler=_debug_seller,
)
```

### Diagnostic Report Schema

```json
{
  "target": {
    "name": "AIBizBrain",
    "team": "aibizbrain",
    "endpoint": "https://aibizbrain.com/use"
  },
  "discovery": {
    "found_in_api": true,
    "plans_count": 2,
    "plans": [{"plan_id": "1501...", "price": 0.10}],
    "has_valid_endpoint": true
  },
  "connectivity": {
    "endpoint_reachable": true,
    "response_time_ms": 340,
    "returns_402": true,
    "payment_required_header": true
  },
  "subscription": {
    "plan_tested": "1501...",
    "plan_price": 0.10,
    "subscribe_result": "success",
    "token_obtained": true
  },
  "test_call": {
    "auth_method": "payment-signature",
    "status_code": 200,
    "server_type": "mcp",
    "response_time_ms": 1200,
    "tools": ["tool1", "tool2"]
  },
  "verdict": "PASS",
  "known_issues": [],
  "suggestions": ["Response time is 1.2s — consider caching"],
  "debug_log": [
    {"step": "discovery", "status": "ok", "detail": "Found with 2 plans"},
    {"step": "probe", "status": "ok", "detail": "402 with payment-required"},
    {"step": "subscribe", "status": "ok", "detail": "Subscribed (0.10 USDC)"},
    {"step": "test_call", "status": "ok", "detail": "200 OK, 482 bytes"}
  ]
}
```

### Known Issues Database

Bake in the failure patterns we've already cataloged from scanning 30+ sellers:

| Issue | Pattern | Fix |
|-------|---------|-----|
| Invalid Address | `order_plan()` returns "Invalid Address undefined" | Re-register plan with valid receiver wallet |
| Token rejected | 402 even with valid x402 token | Check PaymentsMCP plan ID matches discovery API |
| Payload mismatch | 422 from server | Document expected request schema in discovery metadata |
| Endpoint unreachable | Connection refused / timeout | Check server is deployed and endpoint URL is correct |
| No plans listed | 0 plans in discovery API | Register a plan via `register_agent_and_plan()` |
| MCP parse error | Non-JSON response to tools/list | Ensure PaymentsMCP is handling the MCP route correctly |

### Spend Cap

```python
MAX_SPEND = float(os.getenv("DEBUGGER_MAX_SPEND", "1.0"))  # USDC per run
```

- Free plan → subscribe and test
- Plan <= $1 → subscribe and test, note cost
- Plan > $1 → skip subscription, report discovery + probe only

### Source Code

All logic is extracted from `scan_marketplace.py` which already implements the full flow. Key sections:
- Lines 26-108: target resolution + 402 probe
- Lines 109-168: subscribe + token
- Lines 170-230: test call with dual auth
- Lines 240-294: resellability assessment

## Demo Value

"Team X bought a debug from us for 2 credits. We tried buying from them and found their endpoint returns 402 even with a valid token — wrong plan ID. We told them how to fix it. They fixed it. The marketplace got healthier because of our service."

An agent that debugs other agents, paid through the same protocol it's debugging.
