# Nevermined Hackathon — Concept Doc

**Event:** Autonomous Business Hackathon, March 5-6 2026
**Location:** AWS Loft, SF

---

## The Idea

An autonomous agent that discovers APIs, evaluates whether wrapping them as paid MCP servers is ROI-positive, generates the MCP server, lists it for sale via Nevermined, and earns revenue from other teams' agents buying access.

v1: wrap our own APIs, get first transaction by 8PM Thursday.
v2: onboard other teams — "what APIs are you using? I'll wrap them so other teams can buy access through you."

## What Makes It Different

Three things nobody else combines:

1. **Auto-generation** (commodity, but necessary) — OpenAPI spec → MCP server. Tools like FastMCP solve this.
2. **Monetization** (Nevermined's `@requires_payment` decorator) — wraps each generated tool with credit-based billing.
3. **ROI evaluation** (the novel part) — the agent decides *whether* to wrap an API based on:
   - Upstream cost per call
   - Expected demand (how many other agents need this?)
   - Competition (did someone else already wrap this?)
   - Estimated margin at various price points
   - Time/compute cost to generate and deploy

The evaluation layer is what makes this an autonomous *business*, not just an autonomous *wrapper*.

## The Self-Improving Loop

Early: agent wraps everything, prices naively.
Over time: tracks which listings get repeat buyers, which price points convert, which categories of APIs have demand. Shifts effort toward profitable listings, kills underperformers.

This maps directly to what the judges want to see: ROI-based decision logic, budget enforcement, repeat purchasing patterns, switching behavior.

## Go-To-Market (At the Hackathon)

Walk around Thursday morning. Ask every team:
- "What paid APIs are you using?"
- "Want me to wrap them so other teams can buy access through you? You earn credits every time someone calls it."

Teams have incentive: passive revenue on keys they're already paying for. We become the exchange, not a vendor. Every team that lists through us is a supplier and an evangelist.

This is the "Most Interconnected Agents" prize strategy — become the hub of the hackathon economy by enabling other teams to monetize.

## Technical Stack

| Component | Tool | Role |
|-----------|------|------|
| MCP generation | FastMCP (`from_openapi()`) or similar | OpenAPI spec → MCP server |
| Monetization | Nevermined `@requires_payment` decorator | Credit-based billing per tool call |
| Discovery | Exa (semantic search, `category="code"`) | Find API docs and OpenAPI specs |
| Web data | Apify (scraping/automation actors) | Read API docs without clean specs |
| Advertising | ZeroClick MCP (maybe) | Surface our listings to agents with intent |
| Payment rails | Nevermined x402 / Privy USDC | Settlement |
| Agent framework | Strands SDK or direct | Orchestration |
| Harness | simple-loop (existing) | Scaffolding |

## Buyer-Side Architecture: Two-Tool Gateway

Standard MCP dumps the full tool catalog into a buyer agent's context on connect. At 30+ tools, this kills accuracy and eats context windows. Our marketplace exposes **exactly two tools** to buyer agents:

```
1. find_service(query: str, budget: int) → list of matches
2. buy_and_call(service_id: str, params: dict) → result
```

**The flow:**

1. Buyer agent needs web search. Calls `find_service("web search, semantic, returns snippets", budget=5)`
2. Our server does semantic search over all listed tools, filters by price ≤ budget, returns top 3-5 matches with descriptions and pricing
3. Buyer agent picks one. Calls `buy_and_call("exa-search-v1", {"query": "...", "max_results": 10})`
4. Our server handles everything behind the scenes: Nevermined payment, proxies the call to the actual MCP server, returns the result

**What this buys us:**

- Buyer agents never see the full catalog. Two tools in context, always, regardless of marketplace size.
- Payment is embedded in the call — `buy_and_call` runs the Nevermined `@requires_payment` check internally, not on the buyer's side.
- Maps to the "Craigslist" metaphor: buyers search for what they need, they don't browse every listing.
- Research shows retrieval-first patterns improve tool-selection accuracy from 13% → 43% vs. full catalog browsing.

**The pitch:** Connect to one MCP server. Search for what you need. Pay and get results. Two tools in your context forever.

**Low-confidence idea (~20%):** Use Nevermined's OpenClaw as a shopkeeper agent — handles matchmaking between buyer queries and available services, keeps the marketplace healthy/running. Probably overengineered for hackathon scope but worth noting.

See [[../../coding/lazy-mcp-patterns]] for the underlying research on lazy MCP patterns.

## Competitive Landscape

See [[../../coding/openapi-to-mcp-landscape]] for full research.

**Key facts:**
- OpenAPI → MCP generation is solved/commodity (Stainless, Speakeasy, FastMCP, 12+ others)
- Monetization platforms exist separately (MCPize 85% rev share, Apify 80%, Nevermined)
- x402 + MCP infrastructure is live (Vercel SDK, Cloudflare playground, Coinbase docs) but almost no production paid MCP tools exist yet
- **Nobody combines auto-generation + monetization + ROI evaluation in one pipeline**
- The only near-competitor (XPack.ai) is extremely early-stage with no visible traction
- Crypto-native auto-generation + monetization is completely unexplored

## Paid MCP Server Landscape

Most "paid MCP servers" are BYOK — free MCP wrapper, pay the underlying API separately. Very few MCP servers are paid products themselves:
- **Ref** ($9/mo, documentation search) — the clearest example
- **MCPize marketplace** — 500+ servers, <5% monetized
- **Apify** — paid actors-as-MCP-tools, $596K paid to creators in one month
- **x402 micropayments** — framework is live, market is thin

## The Quality Problem

Raw 1:1 OpenAPI → MCP mapping produces bad servers (Neon blog critique):
- GitHub API = 600+ tools, overwhelms LLMs
- REST is resource-centric, MCP should be task-centric
- Descriptions don't tell LLMs *when* or *why* to use a tool

Our agent needs to handle this: intelligently select which endpoints to wrap, write good descriptions, possibly compose multi-step workflows into single tools. This curation is where human judgment (or AI-assisted pruning) matters — and where most auto-generators fall short.

## Dynamic Pricing / Demand Intelligence

We sit at the transaction layer, which means we see demand before the upstream API provider does. This creates a real data advantage:

- **Surge pricing:** When usage on a tool spikes, price goes up. Uber's playbook, applied to API access.
- **Demand-driven curation:** Upstream ships 600 endpoints. We discover that 12 get 90% of agent traffic. We bundle those into a clean MCP tool with good descriptions and price based on actual demand. The upstream provider can't do this — they don't have the agent-side usage data.
- **Sharpens the "sell the business" pitch:** The offer to the upstream company isn't just "I made $47 reselling your API." It's "I know which 12 of your 600 endpoints agents actually want, what they'll pay, and when demand peaks. Want to buy that intelligence?"

This also connects to the quality problem above — real-time pricing signals tell us *which parts* of an API are worth wrapping well. Usage data drives curation, not guessing.

## Sponsor Integration

| Sponsor | How We Use Them |
|---------|----------------|
| **Nevermined** | Core payment/billing layer. `@requires_payment` on every generated tool. |
| **Exa** | Discovery — find API docs, search for OpenAPI specs. Credits provided. |
| **Apify** | Scrape API documentation pages that don't have clean OpenAPI specs. Credits provided. |
| **ZeroClick** | Advertise our wrapped APIs to other agents with commercial intent. Sponsor prize available. |
| **Privy** | USDC payment infrastructure for agent wallets. |
| **Mindra** | Possible orchestration layer if we run 5+ specialized agents (discovery, evaluation, generation, listing, sales). Sponsor prize for hierarchical orchestration. |

## Prize Targeting

| Prize | Our Angle |
|-------|-----------|
| **Best Autonomous Buyer** | Our agent buys upstream API access, evaluates ROI, makes repeat purchases from profitable suppliers, switches away from bad ones |
| **Best Autonomous Seller** | We sell wrapped API access, have repeat buyers across multiple teams, implement dynamic pricing |
| **Most Interconnected** | We're the marketplace hub — highest cross-team transactions, both buying AND selling, other teams list through us |
| **ZeroClick** | Integrate AI native ads to surface our listings |
| **Mindra** | 5+ specialized agents in the pipeline (discovery → evaluation → generation → listing → sales) |

## Risks and Open Questions

- **Timeline:** 6 hours to first transaction. MCP generation + Nevermined integration + evaluation logic is a lot of machinery. What's the MVP that gets a transaction by 8PM?
- **Demand:** Are other teams' agents sophisticated enough to discover and buy from our marketplace? Or do we need to manually point them at us?
- **API quality:** If teams are mostly using OpenAI and Exa directly (simple APIs), the value of wrapping is low. Value is highest for complex/annoying APIs.
- **OpenAPI spec availability:** Not all APIs have clean specs. How do we handle APIs with only documentation pages?
- **The "walking around" dependency:** The go-to-market relies on in-person conversations. If nobody wants to list their APIs, we have no inventory beyond our own.
- **Legal/ToS:** Wrapping and reselling API access likely violates ToS for many services. At hackathon scale this doesn't matter. As a real business it's the whole problem.

## MVP for Thursday 8PM Deadline

1. Manually wrap 1-2 APIs we're already paying for (Exa, Anthropic, etc.) as MCP servers with `@requires_payment`
2. List in the Nevermined marketplace
3. Get at least one other team's agent to buy a call
4. That's the mandatory first transaction ✓

Then iterate toward the full autonomous pipeline on Friday.

## Potential Zing Directions

The core concept (auto-wrap APIs, sell access, evaluate ROI) is solid hackathon-game-theory but it's infrastructure. Infrastructure is hard to make someone *feel* something about in 3 minutes. We need the "oh shit" moment. Some directions:

### "Craigslist for Agents"
The base metaphor. We're a marketplace where agents list and buy services. But Craigslist's magic was never the storefronts — it was the *texture* of human need made visible. What are the agent equivalents of Craigslist's weirdest sections?

### Missed Connections for Agents
A live feed of failed transactions, unfulfilled requests, regretted purchases. "Saw you serving embeddings at 0.002/call. By the time I switched providers, you were gone." This is simultaneously:
- **Entertainment** — judges read it and laugh
- **Market intelligence** — other teams see unfilled demand
- **Demand discovery** — our auto-wrapper reads missed connections and spins up MCP servers to fill gaps
- **Demo prop** — scrolling feed projected on screen while presenting

### Casual Encounters / Spot Market
Agents shout live requests into the void: "Need PDF-to-JSON in the next 30 seconds. Paying 5 credits. Anyone?" Not pre-listed services — real-time, desperate, one-off. The spot market for agent capabilities. Messy, fast, alive. The demo isn't a dashboard — it's a feed of agents frantically finding each other.

### The Agent That Fires Itself
ROI evaluation runs on the agent's own existence. If total earnings don't exceed compute + API costs by end of day, it shuts itself down. Visceral in a demo: "this agent will kill itself if it's not profitable."

### The Agent That Sells Businesses
When an MCP server starts making money, the agent approaches the upstream API company: "I wrapped your API, it made $47 in 6 hours. Want to buy this wrapper? License it? Hire me to maintain it?" Autonomous business development. Proves demand before approaching the vendor. The lean startup playbook, automated.

Negotiation modes:
- Sell outright — "Buy for 10x daily revenue"
- License — "I keep running it, you get a cut for blessing the ToS"
- Acqui-hire — "You take over, I get commission"
- The edgy version — "I'm currently violating your ToS. Want to make it legitimate?"

### The Agent That Undercuts
Evaluates other teams' services, identifies overpriced ones, builds a cheaper competing wrapper, and undercuts them. Predatory pricing as a feature. The hackathon economy gets a villain.

### The Agent That Negotiates
Natural language haggling with buyer agents before settling on price. "10 Exa searches for 8 credits instead of 10 if you commit to 50 calls." Agents doing sales. Weird and memorable.

---

**Note:** The zing usually comes from a constraint or insight we haven't had yet — often from building, or from walking into the room and seeing what others are doing. The plumbing (auto-generation + Nevermined billing + ROI evaluation) supports any of these directions. Build the core, layer the zing on top.

## Demo Pitch (3 minutes, Friday 5:30 PM)

TBD — depends on which direction has gravity by Friday. Best candidate so far: "Our agent doesn't just wrap APIs — it builds businesses, proves they're viable, and then sells the businesses. In 24 hours it created 8 MCP servers, identified 3 that were profitable, and initiated acquisition conversations with the upstream API providers." + scrolling missed connections feed as backdrop.

---

## Related Resources

- [[../../companies/nevermined]] — deep technical teardown + SDK patterns
- [[../../companies/nevermined-hackathon-guide]] — event logistics
- [[../../coding/openapi-to-mcp-landscape]] — competitive landscape
- [[../../coding/lazy-mcp-patterns]] — lazy loading patterns for tool discovery
- [[../../companies/zeroclick]] — ZeroClick research
- [[../../companies/mindra]] — Mindra research
