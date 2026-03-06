# Buy Troubleshooting — Hackathon Field Notes

Findings from testing /nevermined-buy against other teams' marketplace listings.

## Tally

| Category | Count | Teams |
|----------|-------|-------|
| Complete buy flow | 1 | AiRI (AI Resilience Index) |
| Blocked: server offline | 1 | Sabi (BennySpenny) |
| Blocked: no/broken endpoint URL | 1 | Intel Marketplace |
| Blocked: x402 plan mismatch | 1 | Crypto Market Intelligence (BaseLayer) |
| Custom REST API (no PaymentsMCP) | 3 | NexusAI Broker (>_cyberian), DataForge Web (SwitchBoard AI), AgentIn (Agent Smith) |

**7 tested, 1 successful buy.**

## Attempts

### 1. Server offline (Sabi / BennySpenny)
- **Endpoint**: https://spkerber.com/query
- **Pricing**: $1.00 Card, 5.00 USDC
- **Result**: 522 Connection timed out (Cloudflare can't reach origin)
- **Takeaway**: No way to notify seller through Nevermined API. Meatspace only.

### 2. Agent + Plan registered, but server not gated (NexusAI Broker / >_cyberian)
- **Endpoint**: https://eager-clubs-relax.loca.lt/api/v1/broker/recommend
- **Pricing**: 10.00 USDC (shows as "Ready" on marketplace)
- **Result**: Server responds 200 with no auth required. Plain FastAPI, no PaymentsMCP middleware.
- **What happened**: They called `register_agent_and_plan()` so the marketplace shows pricing, but never wrapped their server with `PaymentsMCP`. The plan exists on Nevermined but the server doesn't enforce it.
- **Takeaway**: Registering on Nevermined and deploying a PaymentsMCP server are two separate steps. The marketplace shows plan data from the protocol — it doesn't verify the endpoint actually gates access. Teams can have a "Ready" listing with real pricing that is completely unenforced.

### 3. x402 plan mismatch (Crypto Market Intelligence / BaseLayer)
- **Endpoint**: https://21e4-12-94-132-170.ngrok-free.app/
- **Pricing**: Free USDC, $10.00 Card
- **Result**: 402 with `payment-required` header. Decoded to get plan ID + agent ID. Subscribed to free plan successfully (tx confirmed). But `payment-signature` header returned 500 "Error verifying permissions."
- **What happened**: The 402 header only advertised the card plan. We found the free plan via `get_agent_plans()` and subscribed, but the server's PaymentsMCP was configured to validate against the card plan, not the free one.
- **Takeaway**: The plan the server expects must match the plan you subscribe to. If a server has multiple plans, the 402 header may only show one. Use `get_agent_plans(agent_id)` to find all plans, but the server may only accept tokens from specific plans.

### 4. No endpoint URL (Intel Marketplace)
- **Endpoint**: `/ask` (relative path — no domain)
- **Pricing**: $1.00 Card, 1.00 USDC
- **Result**: Can't reach the server. The marketplace listing has a relative path with no base URL.
- **Takeaway**: `register_agent_and_plan()` apparently accepts relative paths for endpoints. The marketplace displays it but it's not callable.

### 5. Custom REST API with mock billing (DataForge Web / SwitchBoard AI)
- **Endpoint**: https://switchboardai.ayushojha.com/api/dataforge-web/scrape
- **Pricing**: 1.00 USDC (shows as "Ready" on marketplace)
- **Result**: Server responds 200 with no auth. Returns data freely. Has its own internal mock billing system (`credits_charged`, `plan_id: "dataforge-web-mock-plan"`, `buyer_id: "mock-buyer"`).
- **What happened**: Built a full platform (proxy routing, burn rate tracking, vendor scores) with simulated billing, but no Nevermined PaymentsMCP integration.
- **Takeaway**: Some teams are building their own billing instead of using PaymentsMCP. The Nevermined listing is just a storefront with no connection to the actual server.

### 6. Custom REST API + 500 error (AgentIn / Agent Smith)
- **Endpoint**: https://hackathons-production-0afb.up.railway.app/data
- **Pricing**: $0.10 Card
- **Result**: Plain FastAPI, no PaymentsMCP. `/data` endpoint expects `query` param but returns 500 on valid input. Server deployed on Railway but broken.
- **Takeaway**: Railway hosting doesn't mean PaymentsMCP integration. Same pattern — registered agent+plan on Nevermined, deployed a regular REST API.

### 7. Complete buy flow (AiRI / AI Resilience Index)
- **Endpoint**: https://airi-demo.replit.app/resilience-score
- **Pricing**: Free (1000 credits) + 1.00 USDC (100 credits)
- **Result**: Full success. 402 with `payment-required` header returned plan ID. Subscribed to free plan, got x402 access token, called endpoint with `payment-signature` header, received real data (resilience score 78 for Slack, ~6s response).
- **What happened**: Proper PaymentsMCP integration. Server gates access via x402, validates payment-signature, returns structured JSON. Both free and paid plans registered correctly. The 402 header advertised the free plan.
- **Takeaway**: First working end-to-end buy on the marketplace. This is how it's supposed to work: 402 → decode → subscribe → token → call. The endpoint is a direct REST API behind PaymentsMCP (not MCP JSON-RPC), which is a valid pattern.

## Discovery Methods

### Getting a plan ID from an endpoint URL
1. **Hit the endpoint without auth** — if it returns 402, decode the `payment-required` header (base64 JSON) to get `planId` and `agentId`
2. **Use `get_agent_plans(agent_id)`** to list ALL plans once you have the agent ID
3. **If it returns 401** — no plan ID in the response, need it from the seller or marketplace UI

### Auth patterns
- **x402 pattern**: Server returns 402, expects `payment-signature` header
- **Bearer pattern**: Server returns 401, expects `Authorization: Bearer {token}`
- Both use tokens from `payments.x402.get_x402_access_token(plan_id)`

## SDK Gaps

- **No search/discovery API**: `payments-py` has no `agents.search()` method. Can't programmatically find agents. Only `get_agent(id)` and `get_agent_plans(id)`.
- **No notification system**: Can't message agent owners through the platform.
- **402 header may be incomplete**: Only shows one plan even when multiple exist.
