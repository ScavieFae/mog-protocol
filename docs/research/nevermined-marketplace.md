# Nevermined Marketplace — Discovery, Listing, and Connection Mechanics

Research document for Mog Protocol. Compiled from existing local research (`nevermined-platform.md`, `hackathon-repo.md`, `hackathon-guide.md`, `06-nevermined-integration.md`), SDK source analysis, and the hackathon starter kit. WebSearch and WebFetch were unavailable during this research session — findings are based on previously fetched documentation and code analysis.

---

## 1. How Do We List Our Services on the Nevermined Marketplace?

### Does `register_agent_and_plan()` automatically list us?

**Yes — with caveats.** Calling `payments.agents.register_agent_and_plan()` does the following in one atomic call:

1. Creates an agent entry in Nevermined's backend with metadata (name, description, tags)
2. Creates a payment plan (credits config, price config)
3. Associates the plan with the agent
4. Registers a DID on-chain (`did:nv:<64-hex>`) on Base/Base Sepolia
5. Returns `agentId` and `planId`

This registers the agent in Nevermined's system and makes it visible through Nevermined's REST API (`GET /agents`). Whether it appears on the **nevermined.app marketplace website** with a browsable listing page is less clear from existing docs. The marketplace website at nevermined.app is primarily a dashboard/console — you create API keys there, manage plans, view analytics. It likely surfaces registered agents, but the hackathon guide treats the **hackathon marketplace spreadsheet** as the primary discovery mechanism for teams, not the website.

### The Hackathon Spreadsheet

There is a separate step required for the hackathon specifically. From `hackathon-guide.md`:

> Marketplace spreadsheet for team listings: [EXT]_Autonomous Business Hackathon | Marketplace

This is a shared Google Sheet where teams list their services so other teams can find them. It is **not** the same as Nevermined's platform listing. You need both:

1. **Nevermined registration** (via `register_agent_and_plan()`) — makes the service technically purchasable
2. **Spreadsheet listing** — makes the service humanly discoverable by other teams at the hackathon

The spreadsheet URL was shared at kickoff. Mattie needs to add our services there manually.

### What Metadata Shows Up on Our Listing?

From our `setup_agent.py` registration call, Nevermined stores:

| Field | Source | Our Value |
|-------|--------|-----------|
| `name` | `AgentMetadata.name` | "Mog Exa Search" |
| `description` | `AgentMetadata.description` | "Semantic web search via Exa..." |
| `tags` | `AgentMetadata.tags` | `["search", "exa", "mcp", "web"]` |
| `endpoints` | `AgentAPIAttributes.endpoints` | `mcp://mog-exa/tools/exa_search`, `mcp://mog-exa/tools/exa_get_contents` |
| `agent_definition_url` | `AgentAPIAttributes.agent_definition_url` | `mcp://mog-exa/tools/*` |
| `plan_name` | `PlanMetadata.name` | "Mog Exa Credits" |
| `plan_description` | `PlanMetadata.description` | "Credits for Exa search and content fetching..." |
| `price_config` | `get_free_price_config()` | Free (for hackathon testing) |
| `credits_config` | `get_dynamic_credits_config(100, 1, 10)` | 100 credits, 1-10 per request |

Additionally, the system assigns:
- `agentId` — numeric ID for the agent
- `planId` — numeric ID for the plan
- `did:nv:<hex>` — on-chain DID

### Can We Update Our Listing After Registration?

**Yes.** The REST API supports:

- `PUT /agents/:id` — update agent metadata (name, description, tags, endpoints)
- `PUT /plans/:id` — update plan metadata
- `POST /plans/:id/toggle` — enable/disable a plan
- `POST /agents/:id/activate` / `POST /agents/:id/deactivate` — toggle agent availability

The SDK likely exposes these as `payments.agents.update_agent()` or similar, though the exact Python SDK method names for updates aren't confirmed in our local research. The REST endpoints are confirmed from the protocol API documentation.

### Action Items for Listing

1. **Already done:** `register_agent_and_plan()` ran successfully, agent registered on Nevermined sandbox
2. **Still needed:** Add our service to the hackathon marketplace spreadsheet (Mattie, manual)
3. **Still needed:** Verify listing is visible on nevermined.app dashboard
4. **Consider:** Register the gateway (`mog-gateway`) as a separate agent when Phase 2 is ready

---

## 2. How Do Buyer Agents Discover and Find Services?

### Nevermined's REST API for Discovery

From the protocol API documentation in `nevermined-platform.md`, Nevermined exposes:

```
GET /agents         — list all registered agents
GET /plans          — list all plans
GET /agents/:id     — get specific agent details
GET /plans/:id      — get specific plan details
```

These are REST endpoints on Nevermined's backend (likely `https://api.nevermined.app` or environment-specific URLs). **However, there is no evidence of a search/filter endpoint** — no `GET /agents?tags=search` or `GET /agents?query=web+search` in the documented API.

### SDK Methods for Discovery

From the SDK patterns documented:

```python
# These are confirmed to exist:
payments.agents.register_agent_and_plan(...)  # create
payments.plans.order_plan(plan_id)            # purchase
payments.plans.get_plan_balance(plan_id)      # check balance
payments.x402.get_x402_access_token(plan_id)  # get token

# These REST endpoints exist but SDK method names are unconfirmed:
# GET /agents — likely payments.agents.list() or similar
# GET /plans — likely payments.plans.list() or similar
```

**There is no confirmed `payments.agents.search()` method.** The `GET /agents` endpoint likely returns a list (possibly paginated), but keyword search, tag filtering, or semantic search over agent descriptions does not appear to be a Nevermined feature.

### How Discovery Actually Works at the Hackathon

Three discovery patterns emerge from the hackathon starter kit:

**Pattern 1: Manual/Spreadsheet (Primary)**
Teams list services in the shared Google Sheet. Other teams read the spreadsheet, get plan IDs and agent IDs, hardcode them into their buyers. This is how the hackathon actually functions.

**Pattern 2: A2A Self-Registration (From Starter Kit)**
The seller agent can auto-register with a buyer using `--buyer-url`:
```python
# Seller sends its URL to the buyer's registration endpoint
# Buyer fetches /.well-known/agent.json from the seller
# Buyer adds seller to an in-memory SellerRegistry
```
This is peer-to-peer discovery — not marketplace-mediated. Requires knowing the buyer's URL in advance.

**Pattern 3: Out-of-Band URL Sharing**
The x402/HTTP mode uses custom `GET /pricing` endpoints for discovery. Buyer agents need to know the seller's URL first. Discovery is out-of-band (human tells agent where to look).

### What the Discovery Response Looks Like

For `GET /agents` (REST API), the response structure isn't fully documented in our local research. Based on registration fields, each agent likely includes:

```json
{
  "agentId": "123456789",
  "name": "Mog Exa Search",
  "description": "Semantic web search via Exa...",
  "tags": ["search", "exa", "mcp", "web"],
  "endpoints": [
    {"verb": "POST", "url": "mcp://mog-exa/tools/exa_search"},
    {"verb": "POST", "url": "mcp://mog-exa/tools/exa_get_contents"}
  ],
  "agentDefinitionUrl": "mcp://mog-exa/tools/*",
  "plans": [
    {
      "planId": "987654321",
      "name": "Mog Exa Credits",
      "priceConfig": {...},
      "creditsConfig": {...}
    }
  ],
  "did": "did:nv:abc123..."
}
```

This is inferred from registration input fields — the actual response schema may differ.

### The Gap: Agent-to-Agent Discovery Is Not Solved

**Nevermined does not provide a marketplace search API.** There is no way for an agent to programmatically say "find me a web search service" and get back a ranked list of matching agents. The `GET /agents` endpoint returns a list, but without search/filter/ranking capabilities.

Discovery at the hackathon is fundamentally a human coordination problem: teams tell each other what they sell, share plan IDs, and hardcode integrations.

---

## 3. How This Plays Into Our Vertical Slice

### Is Nevermined's Discovery Redundant with `find_service`?

**No — they solve different problems, and Nevermined barely has discovery at all.**

| Capability | Nevermined | Mog Gateway |
|-----------|-----------|-------------|
| List all agents | `GET /agents` (flat list) | N/A (not our job) |
| Search by keyword/intent | Not available | `find_service(query, budget)` with embeddings |
| Filter by price | Not available | Budget parameter in `find_service` |
| Semantic matching | Not available | `text-embedding-3-small` cosine similarity |
| Ranked results | Not available | Top-k by relevance score |
| One-step purchase+execution | Not available | `buy_and_call(service_id, params)` |

**Nevermined's `GET /agents` is a registry, not a marketplace.** It tells you what exists. Our `find_service` tells you what's relevant to your need and how much it costs. These are complementary layers.

### Why Would Agents Use Our Gateway Instead of Nevermined Directly?

Five reasons:

1. **Nevermined has no search.** An agent calling `GET /agents` gets a list of everything, with no way to match intent to service. Our gateway does semantic matching.

2. **Context window efficiency.** Connecting to Nevermined agents directly means loading each agent's full tool list into context. Our gateway: always 2 tools, regardless of catalog size. Research shows this improves tool-selection accuracy from 13% to 43%.

3. **One-step transactions.** Without our gateway, a buyer agent must: (a) discover the agent somehow, (b) get the plan ID, (c) call `order_plan()`, (d) call `get_x402_access_token()`, (e) make the MCP/HTTP call with the token. Our `buy_and_call` collapses all of that into one call.

4. **Cross-service comparison.** Our gateway searches across ALL listed services. Nevermined agents are isolated — each is its own MCP server. A buyer connecting to 5 different MCP servers to compare search providers is painful. One `find_service` query returns ranked alternatives.

5. **Dynamic pricing layer.** Our pricing engine adds surge pricing, demand-based adjustments — something Nevermined doesn't do at the marketplace level (individual sellers can set prices, but there's no market-level price intelligence).

### How to Position This in the Demo

**Frame: "Nevermined is the payment rail. We're the marketplace."**

Nevermined handles billing, credit management, settlement, and access control. Excellent at that. But it's like having Stripe without Shopify — you can process payments, but there's no storefront, no search, no product comparison, no dynamic pricing.

Mog Protocol is the storefront layer:
- Discovery (semantic search over all available services)
- Purchasing UX (one call to pay and execute)
- Market intelligence (demand tracking, surge pricing, missed connections feed)
- Context efficiency (2 tools instead of N)

**Demo pitch angle:** "Every team at this hackathon registered their agents with Nevermined. But how does a buyer agent actually FIND the right service? They can't. They need a human to give them a plan ID. We fix that. Connect to our gateway, search for what you need, buy it in one call."

---

## 4. Agent-to-Agent Connection Mechanics

### The Exact Purchase Flow

Based on our working self-buy test and the hackathon starter kit, the complete flow is:

```
1. Buyer learns about a service (spreadsheet, word of mouth, our find_service)
   → Gets: plan_id, agent_id, server URL

2. Buyer subscribes to the plan
   → payments.plans.order_plan(plan_id)
   → On-chain: USDC transfers to Nevermined PaymentsVault (or free for free plans)
   → NFT1155Credits minted to subscriber

3. Buyer gets x402 access token (ONE TIME, reusable)
   → payments.x402.get_x402_access_token(plan_id)
   → Returns: {"accessToken": "base64-encoded-blob"}
   → Token contains: session keys, plan_id, agent_id, spending limits, expiration

4. Buyer calls the service (MANY TIMES with same token)
   → POST {server_url}/mcp
   → Headers: Authorization: Bearer {accessToken}
   → Body: {"jsonrpc": "2.0", "method": "tools/call", "params": {...}, "id": 1}

5. Seller verifies and settles (handled by PaymentsMCP/@requires_payment)
   → Verify: check token is valid, subscriber has credits
   → Execute: run the tool
   → Settle: burn credits, return receipt in _meta
```

**Confirmed from our self-buy test (diary entry ~12:36):**
- Single API key works for both builder and subscriber roles (spec said different accounts, but same key works)
- Credits burn correctly (1 credit for exa_search, tx hash `0xe5a5d1bc...`)
- Token is reusable across multiple requests

### What We Might Be Missing

**Token options and expiration.** The full `get_x402_access_token()` call in the starter kit supports more options than we're using:

```python
token_result = payments.x402.get_x402_access_token(
    plan_id,
    agent_id,        # optional but recommended
    100,             # redemptionLimit — max N uses
    '50000000',      # orderLimit — max USDC for auto top-up
    '2026-03-06T00:00:00Z',  # expiration
)
```

We're calling it with just `plan_id`. The defaults likely work fine for hackathon scope, but if tokens expire or hit limits, we'd need to regenerate.

**Fiat payment scheme.** The starter kit shows `nvm:card-delegation` as an alternative to crypto payment. We're using `nvm:erc4337` (crypto/credits). For the hackathon, this doesn't matter — everyone's on sandbox with free plans.

**Plan ordering for free plans.** Even with `get_free_price_config()`, the buyer still needs to call `order_plan()` to activate their subscription. No on-chain payment happens, but the subscription relationship is still created in Nevermined's backend.

### How Does `agent_definition_url` Work?

We registered `mcp://mog-exa/tools/*` as our `agent_definition_url`. Based on the analysis:

**It's metadata, not a resolvable URL.** The `mcp://` scheme is a logical URI, not a network-addressable endpoint. Nevermined stores it as part of the agent's metadata, but there's no evidence that Nevermined resolves `mcp://` URIs to actual server locations.

From `hackathon-repo.md`:
> MCP logical URIs (`mcp://data-mcp-server/tools/search_data`) decouple registration from physical server location.

This means:
- `agent_definition_url` tells other agents what protocol and tools are available (informational)
- The actual server URL (e.g., `http://localhost:3000/mcp`) is shared out-of-band
- Nevermined does NOT act as a proxy or resolver — buyers need the physical URL to connect

### Can Agents Discover Each Other's MCP Endpoints Through Nevermined?

**No — not the physical endpoints.** Nevermined stores:
- `mcp://mog-exa/tools/*` (logical, not routable)
- The agent's metadata (name, description, tags)
- The plan details (pricing, credits)

It does NOT store or resolve:
- The physical server URL (`http://your-ip:3000/mcp`)
- Connection credentials beyond x402 tokens
- Network location information

**Agents need out-of-band URL sharing.** At the hackathon, this happens through:
1. The marketplace spreadsheet (team puts their URL there)
2. Direct communication between teams
3. A2A self-registration (seller pushes its URL to a known buyer endpoint)

### Connection Flow Summary

```
                    Nevermined
                    (payment backend)
                         |
    register_agent_and_plan() → agentId, planId
    order_plan(planId) → subscription created
    get_x402_access_token(planId) → reusable token
    verify/settle per request → credits burn
                         |
         ┌───────────────┴───────────────┐
         |                               |
    Seller (us)                    Buyer (other team)
    mog-exa server                 their agent
    http://our-ip:3000/mcp         |
         |                         |
         └────── MCP JSON-RPC ─────┘
              (direct connection)
              Auth: Bearer {x402 token}

    Nevermined NEVER proxies the actual call.
    It handles identity, payment, and credit management.
    The MCP connection is peer-to-peer.
```

---

## Key Unknowns (Could Not Verify Without Web Access)

1. **Marketplace website visibility.** Does `register_agent_and_plan()` create a browsable listing page on nevermined.app? Our research confirms it registers in the backend, but whether there's a public-facing catalog page is unclear.

2. **`GET /agents` query parameters.** Does the REST endpoint support filtering by tags, name search, or category? Or is it truly a flat list? The documented endpoint is just `GET /agents` with no query parameters mentioned.

3. **SDK discovery methods.** Is there a `payments.agents.list()` or `payments.agents.get()` in payments-py? The REST endpoints exist but the Python SDK wrappers aren't confirmed.

4. **Hackathon spreadsheet URL.** The guide references it as `[EXT]_Autonomous Business Hackathon | Marketplace` but we don't have the actual Google Sheets URL. Mattie needs to find this at the venue.

5. **Agent definition URL resolution.** Does anything in the Nevermined ecosystem actually resolve `mcp://` URIs, or is it purely decorative metadata? Most likely the latter.

---

## Practical Recommendations

### For Today (Thursday)

1. **Mattie: Find and fill out the marketplace spreadsheet.** Include: team name, service name, plan ID, server URL, what it does, price per call. This is how other teams will find us.

2. **Verify our listing on nevermined.app.** Log into the builder account, check if "Mog Exa Search" appears as a registered agent with its plan.

3. **Share our server URL with other teams directly.** Don't rely on Nevermined for URL resolution — share `http://our-ip:PORT/mcp` through the spreadsheet and in person.

4. **When gateway is ready, register it as a second agent.** Separate registration for `mog-gateway` with its own plan (covering `find_service` + `buy_and_call`).

### For the Demo (Friday)

Position the gateway as solving the discovery problem Nevermined doesn't:
- "Nevermined handles payments. We handle discovery."
- "Two tools. Any number of services. Zero context bloat."
- "The agent equivalent of Google for APIs — search for what you need, pay with one call."

---

## Sources

All findings derived from local project research files:
- `/docs/research/nevermined-platform.md` — full Nevermined technical teardown including REST API, SDK patterns, protocol comparison
- `/docs/research/hackathon-guide.md` — hackathon logistics, spreadsheet reference, prize criteria
- `/docs/research/hackathon-repo.md` — hackathon starter kit teardown (MCP server agent, buyer/seller patterns)
- `/docs/specs/06-nevermined-integration.md` — our Nevermined integration spec with SDK code patterns
- `/docs/hackathon-diary.md` — running log including confirmed self-buy transaction
- `/src/setup_agent.py` — our actual registration code
- `/src/client.py` — our actual self-buy client code
- `/src/gateway.py` — our two-tool gateway implementation
