# Buy Troubleshooting — Hackathon Field Notes

Findings from testing /nevermined-buy against other teams' marketplace listings.

## Tally (Full Marketplace Scan)

33 reachable sellers probed. 18 subscribed (10 paid, 8 free). 3 connected end-to-end.

| Category | Count | Teams |
|----------|-------|-------|
| Complete buy flow | 3 | Autonomous Business AI (BusyBeeAIs), QA Checker Agent (Full Stack Agents), AIBizBrain (aibizbrain) |
| Subscribed, token valid, call failed | 15 | BaseLayer (x3), Arbitrage Agent, NexusAI Broker, Market Intel Agent, DataForge (x3), Portfolio Manager, SearchResearchAnything, AiRI (timeout), Nexus Intelligence Hub, TrustNet, Platon |
| Subscribe failed (500 from Nevermined) | 12 | Mom, Intel Marketplace, Agent Staffing Agency, Autonomous Silicon Valley, AgentIn, Autonomous Lead Seller, Grants data, rategenius, Celebrity Economy, AgentBank, Social Search, Data Analystics |
| Unreachable (connect error/timeout) | 3 | Sabi, AgentCard Enhancement, The Churninator |
| Localhost/relative path (dead on arrival) | 11 | Market Buyer, SparkClean, Quickturn, pricebot, AI Research Agent (x2), Demo Agent, AI Payments Researcher, VentureOS, Agent Broker, OrchestroPost |

**47 total sellers, 33 probed, 3 connected with real data.**

### Previous manual testing (7 attempts)

Earlier session tested 7 teams individually via the /nevermined-buy skill. AiRI was the first successful buy (resilience score 78 for Slack). Those findings are preserved below.

## Failure Patterns

### Pattern 1: Subscribe fails with 500 (12 teams)

`order_plan()` returns 500 from Nevermined backend. All 12 are paid plans (0.1-15 USDC). Every free plan subscribed fine. Every paid plan from certain teams fails. Likely cause: seller's receiver wallet not configured correctly, or plan registered without valid payment address. This is NOT a buyer-side issue — 10 other paid plans subscribed successfully.

### Pattern 2: Subscribed + token, but call returns 402 (7 teams)

We subscribe, get a valid token, send it via `payment-signature` header — server still returns 402. Token not accepted. Possible causes:
- Server validates against a different plan than the one we subscribed to
- Server expects bearer auth, not payment-signature (but we tried both)
- Token format mismatch between plan types

BaseLayer (3 agents) all show this pattern. They have proper x402 servers (return 402 with `payment-required` header) but reject valid tokens.

### Pattern 3: Subscribed + token, but call returns 422/500 (5 teams)

Server is up but rejects our payload. These are plain REST APIs (FastAPI) that expect specific parameter names. Our generic `{"query": "test"}` doesn't match their schema. Not a payment issue — it's a payload format issue. Would work with correct params.

SwitchBoard AI (DataForge Web, DataForge Search, ProcurePilot) — all return 422 (validation error).
Portfolio Manager — returns 500 on call.

### Pattern 4: Server returns 403 after payment-signature (2 teams)

Market Intel Agent and Nexus Intelligence Hub (both Full Stack Agents). Payment-signature gets 403 (forbidden), bearer gets 402. The server recognizes the auth attempt but rejects it. Possible CORS or middleware issue.

## Successful Buys (Details)

### Autonomous Business AI (BusyBeeAIs) — FREE
- **Endpoint**: https://4d4b-136-25-63-254.ngrok-free.app/ask
- **Auth**: x402 (402 probe, payment-signature header)
- **Response**: `{"answer":"You asked: 'test'. Here is your result!"}`
- Echo server behind PaymentsMCP. Simple but works.

### QA Checker Agent (Full Stack Agents) — FREE
- **Endpoint**: https://us14.abilityai.dev/api/paid/qa-checker/chat
- **Auth**: payment-signature header (probe returned 422, but authenticated call returned 200)
- **Response**: Greeting message offering QA review services
- Interesting: same team (Full Stack Agents) has 5 agents, only this one works end-to-end.

### AIBizBrain (aibizbrain) — 1 USDC
- **Endpoint**: https://aibizbrain.com/use
- **Auth**: x402 (402 probe, payment-signature header)
- **Response**: `{"response":"OK — 10 credits redeemed","credits_used":10}`
- First successful PAID buy from the scan. Real money spent.

### AiRI (AI Resilience Index) — FREE (from earlier manual test)
- **Endpoint**: https://airi-demo.replit.app/resilience-score
- **Auth**: x402 (payment-signature header)
- **Response**: Resilience score 78 for Slack with vulnerabilities/strengths analysis (~6s)
- Timed out during batch scan but worked in manual testing. Likely slow under load.

## Earlier Manual Attempts (Preserved)

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
- **Takeaway**: Registering on Nevermined and deploying a PaymentsMCP server are two separate steps. The marketplace shows plan data from the protocol — it doesn't verify the endpoint actually gates access.

### 3. x402 plan mismatch (Crypto Market Intelligence / BaseLayer)
- **Endpoint**: https://21e4-12-94-132-170.ngrok-free.app/
- **Pricing**: Free USDC, $10.00 Card
- **Result**: 402 with `payment-required` header. Subscribed to free plan successfully. But `payment-signature` header returned 500 "Error verifying permissions."
- **Takeaway**: The plan the server expects must match the plan you subscribe to. If a server has multiple plans, the 402 header may only show one.

### 4. No endpoint URL (Intel Marketplace)
- **Endpoint**: `/ask` (relative path — no domain)
- **Pricing**: $1.00 Card, 1.00 USDC
- **Result**: Can't reach the server. Relative path with no base URL.

### 5. Custom REST API with mock billing (DataForge Web / SwitchBoard AI)
- **Endpoint**: https://switchboardai.ayushojha.com/api/dataforge-web/scrape
- **Pricing**: 1.00 USDC
- **Result**: Server responds 200 with no auth in earlier test. Returns 422 in batch scan (payload format changed or validation added).

### 6. Custom REST API + 500 error (AgentIn / Agent Smith)
- **Endpoint**: https://hackathons-production-0afb.up.railway.app/data
- **Pricing**: $0.10 Card
- **Result**: subscribe fails with 500 in batch scan. Plain FastAPI in earlier manual test.

### 7. Complete buy flow (AiRI / AI Resilience Index)
- **Endpoint**: https://airi-demo.replit.app/resilience-score
- **Pricing**: Free (1000 credits) + 1.00 USDC (100 credits)
- **Result**: Full success in manual test. Timed out in batch scan (likely slow under load).

## Discovery Methods

### Discovery API (primary — works for all registered teams)
```
GET https://nevermined.ai/hackathon/register/api/discover?side=sell
Header: x-nvm-api-key: YOUR_KEY
```
Returns all sellers with plan IDs (`planDid`), endpoints, and pricing. No scraping needed.

### Getting a plan ID from an endpoint URL (fallback)
1. **Hit the endpoint without auth** — if it returns 402, decode the `payment-required` header (base64 JSON) to get `planId` and `agentId`
2. **Use `get_agent_plans(agent_id)`** to list ALL plans once you have the agent ID
3. **If it returns 401** — no plan ID in the response, need it from the discovery API

### Auth patterns
- **x402 pattern**: Server returns 402, expects `payment-signature` header
- **Bearer pattern**: Server returns 401, expects `Authorization: Bearer {token}`
- Both use tokens from `payments.x402.get_x402_access_token(plan_id)`

## SDK Notes

- **Discovery API exists**: `GET https://nevermined.ai/hackathon/register/api/discover` — requires `x-nvm-api-key` header. Returns all sellers with plan IDs. This is the hackathon portal API, not `payments-py`.
- **payments-py has no search**: Only `get_agent(id)` and `get_agent_plans(id)`. No listing or discovery.
- **402 header may be incomplete**: Only shows one plan even when multiple exist.
- **order_plan() 500s are seller-side**: Bad receiver wallet config. Not a buyer issue.
