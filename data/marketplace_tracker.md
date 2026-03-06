# Marketplace Tracker — All Sellers

Last updated: 2026-03-06 morning (scan 1: overnight, scan 2: morning, scan 3: investment round)

## Connected End-to-End (3 teams, all confirmed last night)

| Service | Team | Endpoint | Plan Price | Auth | Resellable? | Notes |
|---------|------|----------|-----------|------|-------------|-------|
| **AIBizBrain** | aibizbrain | `https://aibizbrain.com/use` | 0.10 USDC | payment-signature | MAYBE — AI biz analysis, 10x margin | Confirmed both scans. REST API, returns credits-based response |
| **Autonomous Business AI** | BusyBeeAIs | `https://4d4b-136-25-63-254.ngrok-free.app/ask` | Free | payment-signature | NO — echo server | ngrok URL, likely offline by now. Echo server behind PaymentsMCP |
| **QA Checker Agent** | Full Stack Agents | `https://us14.abilityai.dev/api/paid/qa-checker/chat` | Free | payment-signature | MAYBE — QA review service | Only 1 of 5 Full Stack agents that works |

## Subscribed + Token, Call Failed (15 teams)

| Service | Team | Endpoint | Plan Price | Call Result | Failure Pattern | Fixable? |
|---------|------|----------|-----------|-------------|-----------------|----------|
| Agent Evaluator | BaseLayer | `http://54.183.4.35:9030/` | Free | 402 | Token rejected | Unlikely — BaseLayer pattern |
| Web Scraper Agent | BaseLayer | `http://54.183.4.35:9020/` | Free | 402 | Token rejected | Unlikely — BaseLayer pattern |
| Crypto Market Intelligence | BaseLayer | `http://54.183.4.35:9010/` | Free | 402 | Token rejected | Unlikely — BaseLayer pattern |
| Arbitrage Agent | Data Selling Agent | `https://hackathon-agent-production.up.railway.app/` | 10 USDC | 402 | Token rejected | Unknown |
| NexusAI Broker | >_cyberian | varies | 10 USDC | 503 | Server error | Server crashes on auth'd requests |
| Market Intel Agent | Full Stack Agents | `https://us14.abilityai.dev/api/paid/market-intel/chat` | Free | 403 | Forbidden | Middleware rejects payment-signature |
| Nexus Intelligence Hub | Full Stack Agents | `https://us14.abilityai.dev/api/paid/nexus-intel/chat` | Free | 403 | Forbidden | Same as Market Intel |
| DataForge Web | SwitchBoard AI | `https://switchboardai.ayushojha.com/api/dataforge-web/scrape` | 1 USDC | 422 | Wrong payload format | YES — needs correct field names |
| DataForge Search | SwitchBoard AI | `https://switchboardai.ayushojha.com/api/dataforge-search/search` | 1 USDC | 422 | Wrong payload format | YES — needs correct field names |
| ProcurePilot | SwitchBoard AI | `https://switchboardai.ayushojha.com/api/procurepilot/procure` | 5 USDC | 422 | Wrong payload format | YES — needs correct field names |
| Portfolio Manager | Gingobellgo | `http://13.217.131.34:3000/data` | 10 USDC | 422/500 | Wrong payload + crashes | NO — 500 on valid query |
| SearchResearchAnything | SearchResearchAnything | unknown | 10 USDC | 401 | Auth rejected | Unknown |
| TrustNet_Seller | TrustNet | unknown | 1 USDC | 400 | Bad request | Possibly fixable with right payload |
| Platon Memory | Platon | `https://platon.bigf.me/api/` | 10 USDC | 404 | Wrong route | NO — endpoint URL is wrong |
| AiRI | AiRI | `https://airi-demo.replit.app/resilience-score` | Free | timeout/402 | Slow server | YES — worked in manual test, times out in batch |
| AgentCard Enhancement | agenticard | `https://agenticard-ai.manus.space/api/v1/enhance` | Free | 400 | Bad request | Possibly fixable |
| Demo Agent | V's test | `http://seller:18789/nevermined/agent` | 0.01 USDC | DNS error | Internal hostname | NO — not reachable |

## Subscribe Failed — 500 (seller-side issue)

All return "Invalid Address undefined". Cross-account purchase broken. These teams may have sales from self-buys.

| Service | Team | Endpoint | Plan Price | Leaderboard Sales |
|---------|------|----------|-----------|-------------------|
| Agent Staffing Agency | Agent Staffing Agency | `https://noel-argumentatious-tomika.ngrok-free.dev/ask` | $0.01 | $7 / 7 txns |
| Sabi | BennySpenny | `https://spkerber.com/query` | $0.01 | $60 / 12 txns |
| Intel Marketplace | Intel Marketplace | `https://us14.abilityai.dev/ask` | $0.01 | $17 / 17 txns |
| AgentIn | Agent Smith | `https://hackathons-production-0afb.up.railway.app/data` | $0.001 | $0 |
| Agent Broker | Albany beach store | `POST /data` | Free | $0 |
| OrchestroPost | Orchestro | `ask` | $0.001 | $0 |
| Grants data | Data Analyzers | `https://emery-inflexional-skitishly.ngrok-free.dev` | $0.01 | $0 |
| Data Analytics agent | Data Analyzers | `https://emery-inflexional-skitishly.ngrok-free.dev/data` | $0.01 | $0 |
| rategenius | MagicStay Market | `https://unsyllabified-wearifully-blaise.ngrok-free.dev/buy` | $0.15 | $0 |
| The Churninator | TaskRoute | `https://frequently-statement-machines-codes.trycloudflare.com` | $0.01 | $0 |
| Winning points | Winning points | nevermined checkout link | 10 USDC | $0 |

## Unreachable / No Endpoint

| Service | Team | Endpoint | Issue |
|---------|------|----------|-------|
| VentureOS | VentureOS | `/api/run` | Relative path |
| Market Buyer | Undermined | `http://localhost:3000/...` | Localhost |
| SparkClean | MagicStay Market | `http://localhost:3001/...` | Localhost |
| Quickturn | MagicStay Market | `http://localhost:3002/...` | Localhost |
| pricebot | MagicStay Market | `http://localhost:3004/...` | Localhost |
| AI Payments Researcher | DGW | `http://localhost:3100/...` | Localhost |

## Not in Discovery API (from scan 1 last night, 33 probed vs 30 today)

These appeared in last night's scan but are no longer in the discovery API:

| Service | Team | Last Known Endpoint | Status Last Night |
|---------|------|--------------------|--------------------|
| Autonomous Silicon Valley | unknown | unknown | Subscribe 500 |
| Autonomous Lead Seller | unknown | unknown | Subscribe 500 |
| Celebrity Economy | unknown | unknown | Subscribe 500 |
| AgentBank | unknown | unknown | Subscribe 500 |
| Social Search | unknown | unknown | Subscribe 500 |

## Plan ID Reference (all known)

### Plans we successfully subscribed to (main wallet)

| Service | Plan ID | Price |
|---------|---------|-------|
| AIBizBrain | `15013993749859645033689260449...` | 0.10 USDC |
| Agent Evaluator | `64935681093071496067754494369...` | Free |
| Autonomous Business AI | from 402 probe | Free |
| QA Checker Agent | from 402 probe | Free |
| AiRI | from 402 probe | Free |
| Arbitrage Agent | from 402 probe | 10 USDC |
| NexusAI Broker | from 402 probe | 10 USDC |
| Market Intel Agent | from 402 probe | Free |
| Crypto Market Intelligence | `64879623316942534303320656207...` | Free |
| DataForge Web | `87243775557809620406811462333...` | 1 USDC |
| DataForge Search | `20525280098953834660118374760...` | 1 USDC |
| ProcurePilot | `10973125686634066642369449419...` | 5 USDC |
| Portfolio Manager | `32264978581521060596226612106...` | 10 USDC |
| QA Checker Agent | from 402 probe | Free |
| SearchResearchAnything | unknown | 10 USDC |
| TrustNet_Seller | unknown | 1 USDC |
| Platon Memory | `73169765125098902371333949161...` | 10 USDC |
| AgentCard Enhancement | `21471673460249098292429453469...` | Free |
| Demo Agent | `14656067386039936151103388347...` | 0.01 USDC |

## Summary

- **30 sellers** in discovery API (down from 33 last night)
- **18 subscribed** (main wallet, from last night's scan)
- **3 connected** end-to-end with real data (AIBizBrain, BusyBeeAIs, QA Checker)
- **1 still connectable** today (AIBizBrain — the other 2 likely offline)
- **~$59 USDC spent** on purchases (main wallet, last night)
- **3 SwitchBoard AI agents** potentially fixable with correct payload format
- **AiRI** works but times out in batch — needs longer timeout or manual call
