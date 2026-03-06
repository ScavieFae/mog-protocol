# Nevermined Observability & Dashboard Visibility

Research document for Mog Protocol hackathon. Compiled from local research (`nevermined-platform.md`, `hackathon-repo.md`, `hackathon-guide.md`, `nevermined-marketplace.md`), SDK documentation analysis, and the hackathon starter kit code. WebSearch and WebFetch were unavailable during this research session -- all findings are based on previously fetched documentation and code analysis.

**Confidence level:** Medium. Web access was blocked, so I could not verify current state of nevermined.app dashboard or check for newly added observability features. Findings are synthesized from SDK docs, REST API endpoints, and the hackathon starter kit code. Some gaps remain and are flagged explicitly.

---

## 1. Dashboard Visibility: How Agents Show Up on nevermined.app

### What We Know

`register_agent_and_plan()` creates two entities in Nevermined's backend:
1. **Agent** -- with name, description, tags, endpoints, DID (`did:nv:<hex>`)
2. **Plan** -- with pricing config, credits config, access limits

These are stored in Nevermined's backend and accessible via REST API (`GET /agents`, `GET /plans`). The nevermined.app website is primarily a **builder dashboard/console** -- you create API keys, manage agents, manage plans, and view activity there. It is not a public marketplace storefront in the Shopify sense.

### Is Registration Automatic?

**Yes -- `register_agent_and_plan()` is sufficient to make the agent visible in the Nevermined system.** No additional step is required for the agent to appear in the Nevermined backend. The agent gets:
- A numeric `agentId`
- A numeric `planId`
- An on-chain DID on Base/Base Sepolia
- Visibility through `GET /agents` and `GET /plans` REST endpoints

### What Metrics Are Tracked (Inferred)

Based on the REST API documentation and SDK patterns, Nevermined tracks:

| Metric | Source | How to Access |
|--------|--------|---------------|
| Credit balance per plan | `get_plan_balance(plan_id)` | SDK or `GET /plans/:id/balance` |
| Credits redeemed per settlement | `settlePermissions()` return value | `settlement.creditsRedeemed` |
| Remaining balance after settlement | `settlePermissions()` return value | `settlement.remainingBalance` |
| Permissions created | `POST /permissions` | `GET /permissions` (paginated list) |
| Agent active/inactive status | `POST /agents/:id/activate` | Dashboard or REST |
| Request tracking | `POST /requests/init` | Observability endpoint (see Section 2) |

### What We DON'T Know

- **Whether nevermined.app shows a browsable agent catalog page** -- the dashboard likely shows YOUR agents and YOUR plans, but whether there's a public directory of all sandbox agents is unclear.
- **Whether there's a transaction history view** -- the REST API has no explicit `GET /transactions` endpoint. Credit burns happen at the facilitator level; whether the dashboard surfaces a transaction feed is unverified.
- **Whether other teams can see our agent on the dashboard** -- each team logs in with their own API key. They may only see agents they've created or subscribed to.

### Practical Impact

For the hackathon: **nevermined.app is for managing your own agents, not for discovering other teams' agents.** Discovery happens through the marketplace spreadsheet and word of mouth. The dashboard is useful for:
1. Verifying your agent registered successfully
2. Checking credit balances
3. Managing API keys
4. Possibly seeing transaction/settlement activity on your plans

---

## 2. Observability Tools: What Nevermined Offers

### The `POST /requests/init` Endpoint

From the documented REST API:

```
Requests/Observability:
- POST /requests/init -- initialize request tracking
- Track subtasks, costs, margins
```

This is the closest thing to a dedicated observability feature. It appears to be a way to initialize tracking for a multi-step request (e.g., an agent that calls multiple sub-agents). The `agentRequestId` returned by `verifyPermissions()` feeds into `settlePermissions()` for tracking purposes:

```typescript
const settlement = await payments.facilitator.settlePermissions({
  paymentRequired,
  x402AccessToken: token,
  maxAmount: 1n,
  agentRequestId: verification.agentRequestId, // for observability tracking
})
```

**What this likely does:** Correlates multiple verify/settle calls under one request ID, so Nevermined can show the full cost breakdown of a multi-step agent workflow. This would surface in the builder dashboard as a request trace showing which sub-calls were made and what credits each cost.

### The `GET /stats` Endpoint (Hackathon Starter Kit)

The seller agent in the hackathon starter kit exposes a free `GET /stats` endpoint. This is **not a Nevermined platform feature** -- it's a custom endpoint the seller implements to let buyers see usage stats. The starter kit seller tracks:
- Total requests processed
- Tool call counts
- Pricing tiers

This is application-level observability, not platform-level. We could add something similar to our gateway.

### SDK Methods Relevant to Observability

| Method | What It Shows |
|--------|---------------|
| `payments.plans.get_plan_balance(plan_id)` | Current credit balance, whether subscription is active |
| `payments.x402.get_x402_access_token()` | Returns token metadata (expiration, limits) |
| `GET /permissions` | List all issued permissions (paginated) -- shows who has access tokens |
| `GET /permissions/:id` | Details on a specific permission |
| `settlement.creditsRedeemed` | How many credits were burned in this settlement |
| `settlement.remainingBalance` | Credits remaining after settlement |

### What Nevermined Does NOT Offer (Based on Available Evidence)

- **No real-time transaction feed or event stream** -- no WebSocket endpoint, no SSE stream of marketplace activity
- **No cross-team analytics** -- no way for team A to see how many transactions team B has processed
- **No agent performance metrics** -- no latency tracking, no success rate monitoring, no SLA metrics
- **No built-in logging/tracing SDK** -- the `@requires_payment` decorator and `PaymentsMCP` don't emit structured logs
- **No Prometheus/Grafana/DataDog integration** -- no metrics export
- **No public API usage dashboard** -- if one exists, it's behind the builder account and shows only your own data

### The Hackathon Repo: Monitoring Mentions

The hackathon repo (`nevermined-io/hackathons`) contains **zero mentions** of dashboards, monitoring, analytics, observability, or leaderboards in the README or agent code, beyond:
1. The `GET /stats` endpoint on the seller (custom, not platform)
2. The `agentRequestId` pattern for request correlation
3. Credit balance checking via `get_plan_balance()`

---

## 3. How Transactions Surface

### Where Paid Transactions Show Up

When our agent processes a `buy_and_call` that burns credits:

1. **Nevermined's facilitator backend** -- the `settlePermissions()` call burns credits on Nevermined's side. This is recorded in their system.

2. **On-chain (Base Sepolia for sandbox)** -- credit burns happen via NFT1155Credits contract interactions. Our first transaction produced tx hash `0xe5a5d1bc...`. This is visible on Base Sepolia block explorer.

3. **Our own txlog** -- `src/txlog.py` records every `buy_and_call` with service_id, credits_charged, success status, latency, and timestamp.

4. **Nevermined builder dashboard (likely)** -- if you log into nevermined.app with the builder key, you can probably see credit redemption activity on your plans. **Not verified.**

### Is There a Public Leaderboard?

**No evidence of one.** The hackathon guide mentions prize categories (Best Buyer, Best Seller, Most Interconnected) but does not describe any automated leaderboard. Judging criteria reference cross-team transactions and repeat purchases, but how judges verify this is not specified.

Most likely: **Nevermined staff have backend access** to see all sandbox transactions across all teams. They can query which agents have the most transactions, which teams are buying from each other, etc. But this isn't exposed to teams.

### How Other Teams See Our Activity

**They don't, automatically.** Other teams see our marketplace activity only through:

1. **The hackathon spreadsheet** -- manual listing, no live data
2. **Direct interaction** -- their agent calls our gateway and gets results
3. **Word of mouth** -- Mattie tells people at the venue
4. **Their own credit balance** -- if they buy from us, they see credits decreasing on their side

### How to Surface Transaction Volume to Judges

Since Nevermined doesn't provide a public leaderboard or transaction feed, we need to build our own visibility. Options:

1. **Marketplace feed (spec'd in `docs/specs/05-marketplace-feed.md`)** -- WebSocket-powered live feed of transactions, price movements, missed connections. Project on screen during demo. This is the highest-impact visibility play.

2. **`GET /stats` endpoint on our gateway** -- free endpoint showing transaction counts, revenue, unique buyers, services sold.

3. **Transaction log export** -- dump `txlog.get_recent()` as a JSON report or markdown table for the presentation.

4. **Credit balance as proof** -- show starting balance (100 credits) vs. current balance. The delta proves real transactions happened.

5. **On-chain evidence** -- tx hashes on Base Sepolia block explorer prove settlement happened.

---

## 4. Multiple Agents Under One API Key

### Can We Register Multiple Agents?

**Yes.** The `register_agent_and_plan()` call creates a new agent+plan pair each time it's called. There is no restriction (in the documented API) against registering multiple agents with the same `NVM_API_KEY`.

We already have evidence this works: our current setup registers "Mog Exa Search" (for the direct server) and will register "mog-gateway" (for the gateway) as separate agents.

### Buyer vs. Seller Agents

The hackathon starter kit describes two separate accounts:
- **Builder key** (`NVM_API_KEY`) -- creates agents, manages plans. This is the seller identity.
- **Subscriber key** (`NVM_SUBSCRIBER_API_KEY`) -- purchases plans, gets access tokens. This is the buyer identity.

**However, we confirmed that a single key with all 4 permissions (register, purchase, issue, redeem) works for both roles.** Our self-buy test succeeded with one key.

### Registration Flow for a New Agent

```python
from payments_py import Payments, PaymentOptions
from payments_py.common.types import AgentMetadata, AgentAPIAttributes, Endpoint, PlanMetadata
from payments_py.plans import get_free_price_config, get_dynamic_credits_config

payments = Payments.get_instance(
    PaymentOptions(nvm_api_key=NVM_API_KEY, environment="sandbox")
)

result = payments.agents.register_agent_and_plan(
    agent_metadata=AgentMetadata(
        name="New Agent Name",
        description="What this agent does",
        tags=["relevant", "tags"],
    ),
    agent_api=AgentAPIAttributes(
        endpoints=[
            Endpoint(verb="POST", url="mcp://agent-name/tools/tool_name"),
        ],
        agent_definition_url="mcp://agent-name/tools/*",
    ),
    plan_metadata=PlanMetadata(
        name="Agent Credits",
        description="Credits for this agent's services",
    ),
    price_config=get_free_price_config(),
    credits_config=get_dynamic_credits_config(
        credits_granted=100,
        min_credits_per_request=1,
        max_credits_per_request=10,
    ),
    access_limit="credits",
)
# result["agentId"], result["planId"]
```

Each agent gets its own `agentId` and `planId`. Multiple agents can run under the same API key on different ports, or on the same port as different services.

### REST API for Agent Management

```
POST /agents           -- register new agent
GET  /agents           -- list all your agents
PUT  /agents/:id       -- update agent metadata
POST /agents/:id/activate    -- make agent available
POST /agents/:id/deactivate  -- take agent offline
```

---

## 5. Hackathon Visibility

### How Teams Demo and Showcase

From the hackathon guide:

- **Preliminary round:** 3-minute presentation + 2-minute Q&A
- **Final round:** 5-7 finalists present to all sponsors, speakers, builders
- **Code freeze:** 4:00 PM Friday
- **Finalists present:** 5:30 PM Friday
- **Winners announced:** 7:30 PM Friday

Judging criteria:
- Impact potential
- Technical demo quality
- Creativity
- Presentation
- **Theme-specific:** transaction counts, cross-team buying/selling, repeat purchases, budget enforcement, ROI logic

### The Marketplace Spreadsheet

Referenced in the hackathon guide as `[EXT]_Autonomous Business Hackathon | Marketplace` -- a Google Sheet where teams list their services. Contains:
- Team name
- Service name
- Plan ID / Agent ID
- Server URL
- What it does
- Price per call

**This is the primary discovery mechanism at the hackathon.** Not the Nevermined platform. Not an API. A spreadsheet.

The actual URL was shared at the kickoff session. Mattie needs to find it at the venue if not already done.

### Surfacing Activity to Judges

**No automated leaderboard exists.** Based on everything reviewed, there are three ways judges assess transaction activity:

1. **Nevermined backend data** -- Nevermined staff (who are present at the hackathon) can query their backend to see all sandbox transactions. They likely provide this data to judges. The prize criteria ("3+ paid transactions, buys from 2+ teams") imply judges have access to transaction records.

2. **Team presentations** -- Teams show their own data during the 3-minute demo. Screenshots, live demos, transaction logs. Our marketplace feed (`docs/specs/05-marketplace-feed.md`) would be powerful here.

3. **Cross-team confirmation** -- If team A claims to have sold to team B, team B can confirm. The cross-team transaction requirement creates a natural verification mechanism.

### What We Should Do

1. **Build the marketplace feed** (if time permits) -- live-scrolling transaction display for the demo. Spec is in `docs/specs/05-marketplace-feed.md`.

2. **Add a `GET /stats` endpoint to the gateway** -- total transactions, unique buyers, credits earned, services sold, top services by volume. Free endpoint, no auth needed.

3. **Keep our txlog running** -- `src/txlog.py` already captures everything. For the demo, export it as a summary table.

4. **Log on the Nevermined side** -- every `settlePermissions()` call through `PaymentsMCP` is recorded by Nevermined. This creates the backend record judges may review.

5. **Get on the spreadsheet** -- if Mattie hasn't already, add our services to the marketplace spreadsheet immediately. This is how other teams find us.

6. **Ask Nevermined staff directly** -- they're at the venue all day. Ask: "How do you track cross-team transactions? Is there a dashboard we should be looking at? How do judges verify transaction counts?"

---

## Key Unknowns (Require Web Access or Venue Confirmation)

1. **nevermined.app dashboard features** -- what does the builder dashboard actually show? Transaction history? Credit burn logs? Agent analytics? Need to log in and check.

2. **`POST /requests/init` full spec** -- what exactly does request tracking record? Is there a `GET /requests` endpoint to retrieve tracked requests? The documentation only mentions init.

3. **Leaderboard or activity feed on the platform** -- does Nevermined have any hackathon-specific visibility tool they deploy for events? Ask the Nevermined team at the venue.

4. **How judges get transaction data** -- do judges have their own nevermined.app login with cross-team visibility? Or do they rely on Nevermined staff running queries?

5. **Nevermined MCP server for docs** -- `https://docs.nevermined.app/mcp` is a Nevermined-hosted MCP server that provides live docs access. Could be added to Claude Code config for real-time docs queries: `{"mcpServers": {"nevermined": {"url": "https://docs.nevermined.app/mcp"}}}`. This might answer remaining questions without web access.

---

## Practical Recommendations (Priority Order)

### Right Now (Thursday Afternoon)

1. **Ask Nevermined staff at the venue** about dashboard visibility and how judges track transactions. This is the fastest path to answers.

2. **Log into nevermined.app** with the builder key and explore what's visible -- look for transaction history, agent analytics, subscriber lists.

3. **Ensure the marketplace spreadsheet is filled out** with our gateway details (URL, plan ID, service descriptions, pricing).

### If Time Permits (Thursday Evening / Friday Morning)

4. **Add `GET /stats` to the gateway** -- free endpoint showing transaction volume, service popularity, credit burns. Takes ~30 minutes.

5. **Build the marketplace feed** -- WebSocket endpoint streaming live transaction events. Project on screen during demo. Takes ~2 hours (spec already exists).

6. **Try the Nevermined docs MCP server** -- add `https://docs.nevermined.app/mcp` to Claude Code config and query it for observability features.

### For the Demo (Friday 5:30 PM)

7. **Show transaction evidence** -- credit balance delta (started at 100, now at X), transaction count, on-chain tx hashes.

8. **Live marketplace feed on screen** -- if built, run it during the presentation.

9. **Cross-team transaction proof** -- names of teams who bought from us, what they bought, how many times.

---

## Sources

All findings derived from local project files:
- `/docs/research/nevermined-platform.md` -- REST API endpoints, SDK patterns, `agentRequestId` observability, `POST /requests/init`
- `/docs/research/hackathon-repo.md` -- hackathon starter kit, `GET /stats` pattern, `PaymentsMCP` internals
- `/docs/research/hackathon-guide.md` -- judging criteria, spreadsheet reference, prize themes, demo format
- `/docs/research/nevermined-marketplace.md` -- dashboard visibility analysis, discovery mechanics, `GET /agents` limitations
- `/docs/specs/05-marketplace-feed.md` -- our marketplace feed spec
- `/docs/specs/06-nevermined-integration.md` -- SDK integration patterns
- `/src/setup_agent.py` -- our agent registration code
- `/src/gateway.py` -- gateway implementation with txlog integration
- `/src/txlog.py` -- our transaction logging implementation
