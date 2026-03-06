# Buy Pass 3 — Troubleshooting Notes

Scan date: 2026-03-06 morning | 30 sellers | 2 connected | Budget: 15 USDC

## Connected (2)

### AIBizBrain (aibizbrain)
- **Endpoint:** `https://aibizbrain.com/use`
- **Plan cost:** 1 USDC
- **Credits:** 90
- **Test status:** 200
- **Auth:** payment-signature
- **Suggestion:** Working. REST API, payment-signature auth. Only confirmed functional seller in the marketplace.

### Winning points for buyers to make transactions (Winning points for this Hackthon)
- **Endpoint:** `https://nevermined.app/checkout/56967594265037429856808399563971245044808728945801185144754818701750048038178`
- **Plan cost:** 10 USDC
- **Credits:** 100
- **Test status:** 200
- **Auth:** payment-signature
- **Suggestion:** Returned 200 but endpoint is a Nevermined checkout page (nevermined.app/checkout/...), not an API. False positive. This is a leaderboard gaming entry, not a real service.

## Subscribed but call failed (10)

### Crypto Market Intelligence (BaseLayer)
- **Endpoint:** `http://54.183.4.35:9010/`
- **Plan cost:** 0 USDC
- **Credits:** 20
- **Error:** call_failed_None
- **Suggestion:** Subscribed (20 credits) but server returns 402 even with valid token. BaseLayer team. Their x402 server validates against a different plan than the one we subscribed to. Try getting plan ID from 402 probe header instead of discovery API.

### Agent Evaluator (BaseLayer)
- **Endpoint:** `http://54.183.4.35:9030/`
- **Plan cost:** 0 USDC
- **Credits:** 100
- **Error:** call_failed_None
- **Suggestion:** Subscribed (100 credits) but 402 on both auth methods. Same BaseLayer pattern. Server expects a specific plan that doesnt match the free plan we have.

### Web Scraper Agent (BaseLayer)
- **Endpoint:** `http://54.183.4.35:9020/`
- **Plan cost:** 0 USDC
- **Credits:** 100
- **Error:** call_failed_None
- **Suggestion:** Subscribed (100 credits) but 402. Same BaseLayer issue. All 3 BaseLayer agents share the same free plan ID in discovery but the servers each expect their own plan.

### AgentCard Enhancement Agent (agenticard)
- **Endpoint:** `https://agenticard-ai.manus.space/api/v1/enhance`
- **Plan cost:** 0 USDC
- **Credits:** 1000
- **Test status:** 400
- **Error:** call_failed_400
- **Suggestion:** Subscribed but returns 400. REST API (not MCP). Needs correct payload schema — try GET instead of POST, or check their API docs. Team has 25 sale txns on leaderboard so something works.

### DataForge Web (SwitchBoard AI)
- **Endpoint:** `https://switchboardai.ayushojha.com/api/dataforge-web/scrape`
- **Plan cost:** 1 USDC
- **Credits:** 100
- **Test status:** 422
- **Error:** call_failed_422
- **Suggestion:** Subscribed (100 credits) but 422 Unprocessable Entity. FastAPI validation error — we send {"query": "test"} but it expects specific fields. Check 422 response body for required schema. Endpoint: /api/dataforge-web/scrape suggests fields like {"url": "..."}.

### DataForge Search (SwitchBoard AI)
- **Endpoint:** `https://switchboardai.ayushojha.com/api/dataforge-search/search`
- **Plan cost:** 1 USDC
- **Credits:** 100
- **Test status:** 422
- **Error:** call_failed_422
- **Suggestion:** Subscribed (100 credits) but 422. Same SwitchBoard AI pattern. Endpoint: /api/dataforge-search/search suggests fields like {"query": "...", "engine": "..."}. Try sending the 422 error body to see required fields.

### ProcurePilot (SwitchBoard AI)
- **Endpoint:** `https://switchboardai.ayushojha.com/api/procurepilot/procure`
- **Plan cost:** 5 USDC
- **Credits:** 50
- **Test status:** 422
- **Error:** call_failed_422
- **Suggestion:** Subscribed (50 credits) but 422. SwitchBoard AI. Endpoint: /api/procurepilot/procure. Likely needs procurement-specific fields. All 3 SwitchBoard agents are fixable if we get the right payload format.

### Portfolio Manager — Agent Rating & Consulting (Gingobellgo)
- **Endpoint:** `http://13.217.131.34:3000/data`
- **Plan cost:** 10 USDC
- **Credits:** 100
- **Test status:** 500
- **Error:** call_failed_500
- **Suggestion:** No notes.

### Platon Memory (Platon)
- **Endpoint:** `https://platon.bigf.me/api/`
- **Plan cost:** 10 USDC
- **Credits:** 1000
- **Test status:** 404
- **Error:** call_failed_404
- **Suggestion:** Subscribed (1000 credits\!) but 404 Not Found. POST /api/ returns route not found. Server is a Fastify app — try /api/memory, /api/store, /api/recall, or check if they use GET. 1000 credits sitting unused. Platon has 20 USD in sales, 0 credits redeemed.

### Demo Agent (V's test)
- **Endpoint:** `http://seller:18789/nevermined/agent`
- **Plan cost:** 1 USDC
- **Credits:** 100
- **Error:** [Errno 8] nodename nor servname provided, or not known
- **Suggestion:** Subscribed but endpoint is internal hostname (http://seller:18789/...). V test team. Not publicly reachable.

## Subscribe failed (Invalid Address) (9)

### AI Landing Page Builder (BaseLayer)
- **Endpoint:** `http://54.183.4.35:9040`
- **Plan cost:** 10 USDC
- **Error:** Invalid Address (seller wallet)
- **Suggestion:** Invalid Address on subscribe. Seller wallet not configured. Card/Stripe might work if available. BaseLayer team — all their paid plans have this issue.

### Sabi (BennySpenny)
- **Endpoint:** `https://spkerber.com/query`
- **Plan cost:** 1 USDC
- **Error:** Invalid Address (seller wallet)
- **Suggestion:** Invalid Address on subscribe. Server was offline (522) in earlier tests too. BennySpenny team has 60 USD in sales — likely self-buys via card.

### Intel Marketplace (Intel Marketplace)
- **Endpoint:** `https://us14.abilityai.dev/ask`
- **Plan cost:** 1 USDC
- **Error:** Invalid Address (seller wallet)
- **Suggestion:** Invalid Address on subscribe. Endpoint is abilityai.dev (same host as Full Stack Agents). May be a misconfigured plan under a different team account.

### Agent Staffing Agency (Agent Staffing Agency)
- **Endpoint:** `https://noel-argumentatious-tomika.ngrok-free.dev/ask`
- **Plan cost:** 1 USDC
- **Error:** Invalid Address (seller wallet)
- **Suggestion:** Invalid Address on subscribe. ngrok endpoint suggests live dev server. 7 USD in sales on leaderboard — likely card self-buys. Could ask team directly for working plan ID.

### AgentIn (Agent Smith)
- **Endpoint:** `https://hackathons-production-0afb.up.railway.app/data`
- **Plan cost:** 0.1 USDC
- **Error:** Invalid Address (seller wallet)
- **Suggestion:** Invalid Address on subscribe. Railway-hosted FastAPI. Agent Smith team. Plan registered but wallet not configured.

### Grants data, guideline, analysis (Data Analyzers)
- **Endpoint:** `https://emery-inflexional-skitishly.ngrok-free.dev`
- **Plan cost:** 10 USDC
- **Error:** Invalid Address (seller wallet)
- **Suggestion:** Invalid Address on subscribe. ngrok endpoint. Data Analyzers team. Same plan as Data Analytics agent below.

### rategenius (MagicStay Market)
- **Endpoint:** `https://unsyllabified-wearifully-blaise.ngrok-free.dev/buy`
- **Plan cost:** 15 USDC
- **Error:** Invalid Address (seller wallet)
- **Suggestion:** Invalid Address on subscribe. Only MagicStay service with a public ngrok URL. Hotel pricing engine — would be unique if it worked. 15 USDC plan.

### The Churninator (TaskRoute)
- **Endpoint:** `https://frequently-statement-machines-codes.trycloudflare.com`
- **Plan cost:** 10 USDC
- **Error:** Invalid Address (seller wallet)
- **Suggestion:** Invalid Address on subscribe. Cloudflare tunnel URL — ephemeral, may change. TaskRoute team. AI consulting — vague offering.

### Data Analystics agent (Data Analyzers)
- **Endpoint:** `https://emery-inflexional-skitishly.ngrok-free.dev/data`
- **Plan cost:** 10 USDC
- **Error:** Invalid Address (seller wallet)
- **Suggestion:** Invalid Address on subscribe. Same ngrok endpoint and plan as Grants data. Data Analyzers team registered two agents on the same plan/endpoint.

## Skipped (9)

### Mog Markets (Mog Markets)
- **Endpoint:** `https://api.mog.markets/mcp`
- **Suggestion:** Self — skip.

### VentureOS (VentureOS)
- **Endpoint:** `/api/run`
- **Suggestion:** Endpoint is relative path /api/run — no host. Dead on arrival. Would need team to share actual URL.

### Market Buyer (Undermined)
- **Endpoint:** `http://localhost:3000/api/agent/research`
- **Suggestion:** Localhost endpoint. Dev-only, never deployed publicly.

### SparkClean (MagicStay Market)
- **Endpoint:** `http://localhost:3001/service`
- **Suggestion:** Localhost endpoint. MagicStay Market team. 4 of their services are localhost, only rategenius has a public URL.

### Quickturn (MagicStay Market)
- **Endpoint:** `http://localhost:3002/service`
- **Suggestion:** Localhost endpoint. MagicStay Market team.

### pricebot (MagicStay Market)
- **Endpoint:** `http://localhost:3004/service`
- **Suggestion:** Localhost endpoint. MagicStay Market team.

### Agent Broker (Albany beach store)
- **Endpoint:** `POST /data`
- **Suggestion:** Endpoint is "POST /data" — relative path, no host. Albany beach store team. Dead on arrival.

### OrchestroPost (Orchestro)
- **Endpoint:** `ask`
- **Suggestion:** Endpoint is just "ask" — no URL. Dead on arrival.

### AI Payments Researcher (DGW)
- **Endpoint:** `http://localhost:3100/research`
- **Suggestion:** Localhost endpoint. DGW team. Has a free plan but never deployed publicly.

