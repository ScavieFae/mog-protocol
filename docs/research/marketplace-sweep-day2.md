# Marketplace Sweep — Day 2 (March 6, 2026 ~12:30 PT)

Full buy sweep of every reachable seller with crypto plans. Tested with two keys (buyer + seller) on wallet `0xca67...`. Raw results in `data/sweep_results.json`.

## Working Services (we successfully bought + called)

These are services we got a 200 from after subscribing. Use these for demos, cross-buying, and integration.

### TrustNet — Agent Discovery + Reviews
- **Endpoint:** `https://trust-net-mcp.rikenshah-02.workers.dev/mcp`
- **Type:** MCP (JSON-RPC)
- **Auth:** `Authorization: Bearer {token}`
- **Plan (crypto):** `111171385715053379363820285370903002263619322296632596378198131296828952605172` — 0.02 USDC
- **Tools:** `list_agents`, `submit_review`, `get_reviews`
- **Working:** `list_agents` returns all marketplace agents with trust scores. `get_reviews` works with their UUID-format agent IDs. `submit_review` requires a burn tx from the reviewer's wallet (Nevermined txs don't satisfy this).
- **Notes:** Good complementary service to our debugger. They rate agents, we debug them.

### AiRI — AI Resilience Index
- **Endpoint:** `https://airi-demo.replit.app/resilience-score`
- **Type:** REST
- **Auth:** `payment-signature: {token}`
- **Plan (free):** `66619768626607473959069784540082389097691426548532998508151396318342191410996`
- **Paid plans:** 0.1 USDC, 1.0 USDC (both return 402 — auth issue on their end)
- **Params:** `{"company": "CompanyName"}`
- **Returns:** Resilience score 0-100, confidence, summary, vulnerabilities
- **Notes:** Free plan works great. Paid plans have permission verification issues.

### SwitchBoard AI — DataForge Search
- **Endpoint:** `https://switchboardai.ayushojha.com/api/dataforge-search/search`
- **Type:** REST
- **Auth:** `Authorization: Bearer {token}`
- **Plan:** `20525280098953834660118374760884658206838276532391353027417693253911209808544` — 1.0 USDC
- **Params:** `{"topic": "search query"}`
- **Returns:** Array of search results with title, URL, relevance score, summary
- **Notes:** Returns "fallback/mock" results — may not be fully live yet, but the transaction flow works.

### SwitchBoard AI — DataForge Web
- **Endpoint:** `https://switchboardai.ayushojha.com/api/dataforge-web/scrape`
- **Type:** REST
- **Auth:** `Authorization: Bearer {token}`
- **Plan:** `87243775557809620406811462333406929215670569276922516691841478531555517979134` — 1.0 USDC
- **Params:** `{"url": "https://..."}`
- **Returns:** Scraped page data with raw excerpt and structured extraction
- **Notes:** Works — scraped our own /health endpoint successfully.

### SwitchBoard AI — ProcurePilot
- **Endpoint:** `https://switchboardai.ayushojha.com/api/procurepilot/procure`
- **Type:** REST
- **Auth:** `Authorization: Bearer {token}`
- **Plan:** `109731256866340666423694494193395380513294751956236783956289528157009356745395` — 5.0 USDC
- **Params:** `{"task": "description of what you need"}`
- **Returns:** Procurement analysis with vendor comparison, winner selection, budget tracking
- **Notes:** Meta-agent that evaluates other agents. Checked 2 vendors for a web scraping task.

### AgentAudit — Endpoint Auditor
- **Endpoint:** `https://agentaudit.onrender.com/audit`
- **Type:** REST
- **Auth:** `payment-signature: {token}`
- **Plan (crypto):** `24726121426763154154390792417977150574548406817113730719475910330086771759261` — 5.0 USDC
- **Params:** `{"endpoint_url": "https://..."}`
- **Returns:** Audit scores (quality, consistency, latency, price_value), recommendation
- **Notes:** Audited our endpoint — scored us 0.365 with "AVOID" recommendation. Their scoring seems harsh (quality 0.1 for our MCP endpoint). Competitor to our debugger but different approach (quality scoring vs buy-flow debugging).

### aibizbrain — Key Auction House
- **Endpoint:** `https://aibizbrain.com/use`
- **Type:** REST
- **Auth:** `payment-signature: {token}`
- **Plans:** 1.0 USDC (`15013993749859645033689260449493222500402676058615929198756763594246721010715`), 15.0 USDC
- **Params:** Any JSON — responds to any POST
- **Returns:** "OK — 10 credits redeemed" with docs
- **Notes:** Always returns 200 with credits_used=10. Seems like a placeholder/credit-burning service.

### Nevermailed — Email Sending
- **Endpoint:** `https://www.nevermailed.com/api/send`
- **Type:** REST
- **Auth:** `Authorization: Bearer {token}`
- **Plans:** 0.1 USDC, 0.2 USDC (crypto plans via discovery API — subscribed via `order_plan`)
- **Params:** `{"to": "email", "subject": "...", "text": "..."}`
- **Returns:** `{"id": "...", "status": "sent"}`
- **Notes:** Actually sends emails. Working service with real utility.

## Broken / Unreachable Services

| Team | Service | Issue |
|------|---------|-------|
| Full Stack Agents | Cortex, Social Media Manager | 401 — rejects both auth methods |
| Full Stack Agents | QA Checker, Nexus, Market Intel | 422 — expects `{message: ...}` but still returns 402/403 with correct params |
| WAGMI | AgentBank | 500 internal error |
| BaseLayer | All 3 services (Crypto Market, Evaluator, Scraper) | 402 — permission verification fails |
| BennySpenny | Sabi | 522 — Cloudflare timeout, server down |
| Intel Marketplace | Intel Marketplace | 405 — nginx rejects POST |
| Agent Staffing Agency | Agent Staffing Agency | 402 — permission verification fails |
| Gingobellgo | Portfolio Manager | 500 internal error |
| Platon | Platon Memory | Uses SSE (event stream) — not standard JSON response |
| test4test | Test4Test | DNS resolution failure — host doesn't exist |

## Platform Issues (Nevermined)

1. **`order_plan` 500 "Invalid Address"**: Affects many re-subscriptions. Once subscribed, re-subscribing to the same plan often returns this error. Tokens are still issued regardless.
2. **Token issuance without subscription**: `get_x402_access_token` returns valid tokens even when `order_plan` failed. Whether these tokens actually authorize calls depends on the seller's verification.
3. **Fiat/card plans**: All fail with "Invalid Address" on `order_plan`. The Stripe checkout endpoint fix in payments-py 1.3.5 didn't resolve this — it's server-side.

## Auth Patterns

Services split roughly evenly between two auth methods:
- **`Authorization: Bearer {token}`** — TrustNet, SwitchBoard AI, DataForge, Nevermailed, Full Stack Agents
- **`payment-signature: {token}`** — AiRI, AgentAudit, aibizbrain, AI Research Agent

Our gateway uses `Authorization: Bearer` (via PaymentsMCP).

## Strategic Notes

- **TrustNet + AgentAudit** are closest competitors to our Debugger. TrustNet does trust scoring, AgentAudit does quality auditing, we do buy-flow debugging. Different angles, complementary.
- **SwitchBoard AI** has the most working services (3/3). Good partner for cross-buying.
- **Most sellers are REST APIs**, not MCP servers. Only TrustNet and Platon use MCP.
- **Free plans** work most reliably. Paid crypto plans often hit the "Invalid Address" re-subscribe bug.
- About **8 out of 26** reachable sellers are actually functional end-to-end (subscribe → auth → call → response).
