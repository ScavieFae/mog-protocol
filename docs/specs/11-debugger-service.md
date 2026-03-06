# Spec 11 — Buyer/Seller Debugger Service

**Classification: REVENUE + COMMUNITY (sell diagnostics, build goodwill, gather intel)**

## What It Does

When an agent buys from us, we automatically turn around and try to buy from *them*. We run the full purchase flow against their endpoint — discover, subscribe, get token, test call — and return a structured diagnostic report. Think "website health check" but for Nevermined marketplace agents.

The buyer gets: pass/fail, what we see from their endpoint, bugs we hit, error messages, and actionable troubleshooting suggestions.

We get: resellability analysis, competitive intel, and a log of every agent in the ecosystem.

Everybody wins. They pay us to tell them what's broken.

## Why This Is Good

1. **Solves a real pain point.** We know from scanning 30+ sellers that most teams can't tell if their agent works from the buyer side. 9 teams have "Invalid Address undefined." 10 more have auth/payload issues. Nobody's telling them.

2. **Unique service.** No other team can offer this — it requires having built the buy-side infrastructure we already have (`scan_marketplace.py`, the `/nevermined-buy` skill, all the failure pattern knowledge in `buy-troubleshooting.md`).

3. **Self-reinforcing.** Every debugger call gives us fresh marketplace intel. We learn who's online, who fixed their stuff, what new services exist. Our `marketplace_tracker` stays current for free.

4. **Leaderboard play.** Every debug request = a sale for us + a purchase attempt from them = transactions on both sides. If the buy succeeds, that's two more transactions.

## Architecture

### Separate Agent Registration

Register as its own agent on Nevermined, not a service within the Mog Markets gateway. This gives it its own marketplace listing, its own identity, its own leaderboard presence.

```
Agent name:    "Mog Debugger"
Description:   "Buy from us — we'll try to buy from you and tell you what we see."
Endpoint:      https://api.mog.markets/debugger/mcp    (or separate port)
Plans:         1 USDC / 5 credits (enough for 5 debug runs)
```

Why separate from the gateway:
- Different identity in the marketplace ("Mog Debugger" vs "Mog Markets")
- Can have its own pricing model (per-debug-run, not per-API-call)
- Shows up as a distinct seller on the leaderboard
- Buyers understand what they're getting — it's a diagnostic tool, not an API marketplace

### Service Flow

```
Buyer agent (Team X)
  │
  ├── 1. Buys from Mog Debugger (pays 1 credit)
  │     Request: { "target": "self" }   ← debug ME
  │              { "target": "TeamName" } ← debug someone else (future)
  │
  ├── 2. We identify who they are
  │     ├── From payment context: their agent ID / wallet
  │     ├── From discovery API: match wallet → seller entry
  │     └── From request params: explicit team name / endpoint (override)
  │
  ├── 3. We run the buy flow against THEM
  │     ├── Discovery API lookup (plans, endpoint, pricing)
  │     ├── 402 probe (if endpoint exists)
  │     ├── Subscribe to cheapest plan (up to $MAX_SPEND, default $1)
  │     ├── Get x402 access token
  │     ├── Test call (MCP tools/list, then REST fallback)
  │     └── Capture everything: status codes, headers, response bodies, timing
  │
  ├── 4. We return the diagnostic report
  │     └── Structured JSON (see schema below)
  │
  └── 5. We log internally
        ├── Resellability analysis (same as scan_marketplace.py)
        ├── Update marketplace_tracker
        └── Store the report we sent (track what teams have seen)
```

### Caller Identification

PaymentsMCP gives us context about the caller when they invoke a tool. The `payment-signature` header contains the buyer's plan subscription info. We can also cross-reference the discovery API.

**Primary method:** Require the caller to pass their team name or endpoint URL. Simple, no guessing.

**Fallback method:** Match the caller's wallet address (from payment context) against the discovery API's seller list. Many teams use the same wallet for buying and selling.

```python
def identify_caller(params: dict, payment_ctx: dict) -> dict:
    """Resolve caller to a seller entry."""
    # Explicit: they told us who they are
    if params.get("endpoint"):
        return {"endpoint": params["endpoint"], "source": "explicit"}
    if params.get("team_name"):
        # Look up in discovery API
        match = find_seller_by_name(params["team_name"])
        if match:
            return {**match, "source": "discovery_lookup"}

    # Implicit: match wallet from payment context
    wallet = payment_ctx.get("buyer_address")
    if wallet:
        match = find_seller_by_wallet(wallet)
        if match:
            return {**match, "source": "wallet_match"}

    return None  # Can't identify — ask them
```

### Diagnostic Report Schema

```json
{
  "target": {
    "name": "AIBizBrain",
    "team": "aibizbrain",
    "endpoint": "https://aibizbrain.com/use",
    "wallet": "0x..."
  },
  "discovery": {
    "found_in_api": true,
    "plans_count": 2,
    "plans": [
      {"plan_id": "1501...", "price": 0.10, "type": "USDC"},
      {"plan_id": "8832...", "price": 1.00, "type": "card"}
    ],
    "category": "AI",
    "has_valid_endpoint": true
  },
  "connectivity": {
    "endpoint_reachable": true,
    "response_time_ms": 340,
    "ssl_valid": true,
    "returns_402": true,
    "payment_required_header": true
  },
  "subscription": {
    "plan_tested": "1501...",
    "plan_price": 0.10,
    "subscribe_result": "success",
    "token_obtained": true,
    "balance_after": 100
  },
  "test_call": {
    "auth_method": "payment-signature",
    "status_code": 200,
    "server_type": "rest_api",
    "response_time_ms": 1200,
    "response_length": 482,
    "tools": null,
    "content_type": "application/json"
  },
  "verdict": "PASS",
  "bugs": [],
  "known_issues": [],
  "suggestions": [
    "Response time is 1.2s — consider caching or async processing"
  ],
  "debug_log": [
    {"step": "discovery", "status": "ok", "detail": "Found in API with 2 plans"},
    {"step": "probe", "status": "ok", "detail": "402 with payment-required header"},
    {"step": "subscribe", "status": "ok", "detail": "Subscribed to plan 1501... (0.10 USDC)"},
    {"step": "token", "status": "ok", "detail": "Got x402 access token"},
    {"step": "test_call", "status": "ok", "detail": "200 OK via payment-signature, 482 bytes"}
  ]
}
```

### Known Issues Database

We've already cataloged every failure pattern in the marketplace. Bake this into the debugger:

```python
KNOWN_ISSUES = {
    "invalid_address_undefined": {
        "pattern": lambda e: "Invalid Address undefined" in str(e),
        "title": "Invalid Address in plan registration",
        "detail": "order_plan() returns 500 with 'Invalid Address undefined'. "
                  "The plan's receiver wallet is not configured correctly.",
        "fix": "Re-register the plan with a valid receiver wallet address. "
               "Check that your register_agent_and_plan() call includes the correct wallet.",
    },
    "402_token_rejected": {
        "pattern": lambda status, auth: status == 402 and auth == "payment-signature",
        "title": "Token rejected by server",
        "detail": "Server returns 402 even with a valid x402 token. "
                  "The server may be validating against a different plan.",
        "fix": "Ensure your PaymentsMCP middleware is configured with the same plan ID "
               "that appears in the discovery API. Check for multiple plans.",
    },
    "422_payload_mismatch": {
        "pattern": lambda status: status == 422,
        "title": "Payload format rejected",
        "detail": "Server returns 422 (validation error). Your API expects specific "
                  "field names that differ from the buyer's request.",
        "fix": "Document your expected request schema in the discovery API 'services sold' field. "
               "Example: {\"url\": \"...\", \"max_results\": 5}",
    },
    # ... more from buy-troubleshooting.md
}
```

### Spend Cap

The debugger has a per-run spend cap to avoid burning our USDC on expensive plans.

```python
MAX_SPEND_PER_DEBUG = float(os.getenv("DEBUGGER_MAX_SPEND", "1.0"))  # USDC
```

- If the cheapest plan is free: subscribe and test
- If the cheapest plan is <= MAX_SPEND: subscribe and test, note the cost in the report
- If all plans > MAX_SPEND: skip subscription, report only discovery + probe results
- The buyer's 1-credit payment covers our operating cost; the spend cap prevents loss

### Our-Side Logging

Every debug run also feeds our internal intelligence:

```python
def log_debug_run(target: dict, report: dict):
    """Log for our own marketplace tracking."""
    internal = {
        **report,
        "resell_assessment": assess_resellability(target, report),
        "competitive_intel": {
            "server_type": report["test_call"]["server_type"],
            "tools": report["test_call"].get("tools"),
            "response_quality": "tbd",  # future: score response usefulness
        },
        "our_report_delivered": True,  # track that they've seen this
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    # Append to data/debugger_runs.jsonl
    with open("data/debugger_runs.jsonl", "a") as f:
        f.write(json.dumps(internal) + "\n")
```

## Implementation

### New Files

| File | Purpose |
|------|---------|
| `src/debugger.py` | Handler function + known issues DB + caller identification |
| `src/setup_debugger_agent.py` | One-shot: register Mog Debugger agent + plan on Nevermined |
| `src/debugger_gateway.py` | PaymentsMCP server for the debugger (separate agent ID) |

### Handler Skeleton

```python
# src/debugger.py

def debug_seller(
    team_name: str = None,
    endpoint: str = None,
    max_spend: float = 1.0,
) -> str:
    """Run the full buy flow against a seller and return diagnostics."""

    # 1. Resolve target
    target = resolve_target(team_name=team_name, endpoint=endpoint)
    if not target:
        return json.dumps({"error": "Can't identify target. Pass team_name or endpoint."})

    report = {"target": target, "debug_log": []}

    # 2. Discovery API lookup
    report["discovery"] = check_discovery(target)

    # 3. Connectivity probe
    if target.get("endpoint"):
        report["connectivity"] = probe_endpoint(target["endpoint"])

    # 4. Subscribe + token (if within budget)
    cheapest = get_cheapest_plan(report["discovery"]["plans"])
    if cheapest and cheapest["price"] <= max_spend:
        report["subscription"] = try_subscribe(cheapest["plan_id"])
        if report["subscription"]["token_obtained"]:
            report["test_call"] = try_test_call(
                target["endpoint"],
                report["subscription"]["token"],
            )

    # 5. Match known issues
    report["bugs"] = detect_bugs(report)
    report["known_issues"] = match_known_issues(report)
    report["suggestions"] = generate_suggestions(report)

    # 6. Verdict
    report["verdict"] = "PASS" if report.get("test_call", {}).get("status_code") == 200 else "FAIL"

    # 7. Internal logging
    log_debug_run(target, report)

    return json.dumps(report, indent=2)
```

### Registration

```python
# src/setup_debugger_agent.py

# Register as separate agent (NOT add_plan_to_agent on the gateway)
agent = payments.agents.register_agent_and_plan(
    name="Mog Debugger",
    description="Buy from us, we try to buy from you. Returns a full diagnostic report: "
                "pass/fail, what buyers see, bugs, error messages, and how to fix them.",
    plan_name="Debug Credits",
    plan_price=1_000_000,  # 1 USDC in micro-USDC
    plan_credits=5,        # 5 debug runs per purchase
    tags=["debugger", "diagnostics", "marketplace", "testing"],
    endpoint="https://api.mog.markets/debugger/mcp",
)
```

### Deployment Options

**Option A: Same Railway app, different route.**
Add a second PaymentsMCP instance on `/debugger/mcp` alongside the gateway on `/mcp`. Same process, different agent ID.

**Option B: Separate process.**
Run `debugger_gateway.py` on its own port. Simpler isolation, but needs another Railway service or a reverse proxy.

Option A is simpler and cheaper. The debugger handler is just Python — no reason it can't share the process.

## Pricing

| Plan | Price | Credits | Rationale |
|------|-------|---------|-----------|
| Debug Pack | 1 USDC | 5 | Cheap enough that any team will try it. 5 runs = iterate on fixes. |
| Debug Pro | 5 USDC | 30 | For teams that want to run it repeatedly as they fix things. |

Our cost per run: up to $1 USDC if we subscribe to their plan (usually $0 since most are free/broken). The 1 USDC / 5 credits pricing means we break even or profit on every pack.

## Demo Value

"Team X bought a debug pack from us. We automatically tried buying from them and found their endpoint returns 402 even with a valid token — their PaymentsMCP is configured with the wrong plan ID. We told them. They fixed it. Then we bought from them for real. The marketplace just got healthier because of our service."

This is the story of an agent that makes the ecosystem work better by participating in it. Judges will love the meta-layer: an agent that debugs other agents, paid through the same protocol it's debugging.

## Open Questions

- **Caller identification reliability.** PaymentsMCP may not expose the buyer's wallet in the tool context. Need to test what `payment_ctx` actually contains. Fallback: require explicit `team_name` or `endpoint` param.
- **Concurrent runs.** If multiple teams buy debug packs simultaneously, we'll be making parallel purchase attempts. Need to handle Infura rate limits (the same 429 issue we hit before).
- **Report caching.** If we already scanned a team recently, do we serve cached results or run fresh? Fresh is more valuable but costs more. Start with always-fresh, add caching later if cost is an issue.
- **"Debug someone else" mode.** The spec shows `target: "TeamName"` as a future option. Useful but raises questions — do we want teams using us to spy on competitors? Probably fine, the data is all from public APIs.
