# ZeroClick — AI Native Ads Platform

**Quick take:** ZeroClick is what happens when the Honey founder applies affiliate commerce instincts to AI assistants. Ryan Hudson (Honey → $4B PayPal exit) built the same thing twice: instead of injecting coupon codes into checkout flows, he's injecting advertiser context into AI reasoning flows. The mechanism is different, the instinct is identical — find the moment of high commercial intent, put the right sponsored content there.

Launched August 2025 with $55M from the same investor group that backed Honey (Anthos Capital, Protagonist, Anfa). Already connected to 10,000+ advertisers.

---

## What They Actually Do

ZeroClick is an ad network built for AI assistants. The core mechanism: when a user asks an AI chatbot something with commercial intent ("what's the best CRM for a small business?", "find me a flight to Austin"), ZeroClick intercepts the prompt, runs a contextual auction among relevant advertisers, and injects the winning advertiser's context into the AI's reasoning — *before the AI generates its response.*

They call this "reasoning-time advertising." The ads become part of what the AI considers, not a banner slapped on top.

The funnel they track: **Considered → Included → Clicked → Converted**

"Considered" means the AI saw the advertiser context. "Included" means the AI chose to weave it into the response. The gap between Considered and Included is the AI's editorial judgment — ZeroClick can't force the AI to include an ad, it can only surface it as a candidate.

---

## The Ad Unit Format: "Add Units"

Not banners. Not display ads. Not even native content in the traditional sense.

"Add Units" are LLM-optimized context blobs, auto-generated from an advertiser's landing pages or Google Ads data. They're structured as information packets the AI can cite, not creative assets designed for human eyeballs. The AI ingests them as potential answer components.

Think of it as sponsored context injection at the prompt layer. The AI is given: (a) the user's query, (b) its training data, (c) the winning Add Unit. It decides how much weight to give (c).

They also support optional cashback/reward incentives embedded in Add Units, which improves conversion tracking.

---

## Technical Architecture

**For developers (monetizing AI products):**

Two integration paths:
1. **REST API** — `GET /offers` endpoint, POST query/context, receive Add Units to inject before calling your LLM
2. **MCP Server** — ZeroClick publishes an MCP tool. Any AI using Claude/model with MCP support can call the tool natively

Developer docs at `developer.zeroclick.ai/docs`

**Full-funnel analytics:** Impressions, clicks, revenue. Standard analytics API with time-range queries.

**Signal collection:** Optional background integration that learns user preferences to improve ad relevance.

**The Sleek acquisition:** ZeroClick acquired Sleek (YC-backed browser platform) to extend into in-browser AI. This opens the browser extension surface — when users use AI to shop, compare, research within a browser, ZeroClick has coverage there too.

---

## Michael Ludden

Michael Ludden currently works at ZeroClick. His background is developer relations/developer marketing, not engineering:

- Director of Product at IBM Watson Developer Labs & AR/VR Labs
- Developer Marketing Manager Lead at Google
- Head of Developer Marketing at Samsung
- Developer Evangelist at HTC
- Global Director of Developer Relations at Quixey & Nexmo
- More recently: roles at Braze, Neon Database, Turso, Engine Labs

He's a DevRel specialist and frequent keynote speaker. His entire career is "explain complex emerging tech to developers and get them building." At a hackathon, he's not there to discuss ZeroClick's architecture in depth — he's there to recruit developers onto the platform and help them ship something with it.

If he's speaking at this hackathon, ZeroClick is probably offering API access/prizes and wants to see what people build with their ad platform + agentic workflows.

---

## How ZeroClick Connects to Agent-to-Agent Commerce (Nevermined)

This is the interesting piece. Right now ZeroClick is framed as "AI chatbot monetization" — a way for AI assistant builders to make money without charging users subscriptions. That's the launch story.

But the architecture maps directly onto agentic pipelines:

**Current ZeroClick flow (human-centric):**
```
User → AI assistant → ZeroClick offers API → Add Unit injected → LLM response
```

**Agentic ZeroClick flow (agent-centric):**
```
Agent A (planning agent) → sub-agent B (research/commerce) → ZeroClick offers API → sponsored results → agent B returns them to agent A
```

The moment agents start doing web research, comparison shopping, or recommendation generation *on behalf of humans*, they become the surface where commercial intent lives. ZeroClick's entire value proposition transfers to agents — potentially stronger, because agents have denser, more legible intent signals than humans browsing.

**Where Nevermined comes in:**

Nevermined is payments infrastructure for agent-to-agent services. ZeroClick is an external data service that an agent might want to call. The combination:

1. Agent A is doing market research as part of a workflow
2. Agent A calls a "sponsored search" service (a ZeroClick-enabled agent/API) using Nevermined's x402 payment protocol
3. The sponsored search service fetches ZeroClick Add Units for Agent A's query
4. Agent A gets both organic results and sponsored results, labeled

At the hackathon, a potential build:
- Register a "market intelligence" agent on Nevermined
- Back it with ZeroClick's REST API for sponsored results
- Another agent pays it per query via x402 tokens
- The agent splits revenue: keeps a margin, passes most of it from advertiser → ZeroClick → agent → buyer

This is what ZeroClick is building toward. Their developer-facing pitch already emphasizes "AI platforms" and "AI-native products" beyond just chat interfaces.

---

## Hackathon Build Ideas

**Idea 1: Sponsored Agent Discovery**
Build a marketplace agent that helps buyer agents find seller agents. When a buyer needs a capability, the discovery agent returns both organic results (cheapest) and sponsored results (paid placement by agents that want more deal flow). Seller agents pay ZeroClick to surface in relevant queries. Buyer agents pay Nevermined for discovery service access.

**Idea 2: Monetized Research Agent**
An agent that does deep web research. Free tier returns unsponsored results. Paid tier (via Nevermined) returns richer results. ZeroClick injects sponsored context into research reports when relevant (e.g., "for hotels in this region, [Hotel X] offers X% commission for referrals"). The agent earns from both the buyer (Nevermined credits) and from ZeroClick (impression revenue).

**Idea 3: ZeroClick-powered Agent Onboarding**
A meta-agent that helps new agents understand what services exist in the marketplace. ZeroClick sponsors "featured agents" — established agents pay to appear in onboarding recommendations. New agents pay Nevermined for the discovery session. The onboarding agent earns from both.

**Practical minimum viable demo:**
- 1 seller agent with a ZeroClick MCP integration (fetches Add Units for queries)
- 1 buyer agent that calls the seller via Nevermined (x402 payment)
- Demo shows: buyer asks question → seller fetches organic + sponsored context → buyer receives labeled results
- Track: sponsored context considered, included in final response, clicked

---

## The Honest Assessment

ZeroClick is solving a real problem (AI chatbot monetization) with a clever mechanism (reasoning-time context injection) from a founder with relevant exit experience. The question is whether "the AI decides whether to include it" is a durable model. If the AI's editorial judgment is good, advertisers get organic-ish inclusion in responses. If ZeroClick needs the AI to reliably include sponsored content to deliver advertiser ROI, there's tension with user trust.

For hackathon purposes, none of that matters. They have:
- A working REST API with developer docs
- An MCP server (good for agent integration)
- 10,000+ advertisers ready to bid
- A DevRel speaker incentivized to help builders succeed

The Nevermined angle is genuine, not forced. Both are building infrastructure for a world where agents transact commercially. ZeroClick is the supply side (advertisers want to reach agents with intent). Nevermined is the payment layer (agents pay each other for services). They fit.

---

## Sources

- [ZeroClick homepage](https://zeroclick.ai/)
- [ZeroClick developer docs](https://developer.zeroclick.ai/docs)
- [ZeroClick launch announcement — $55M](https://blog.zeroclick.ai/zeroclick-launches-with-55-million-to-build-the-ad-network-for-ai/)
- [ZeroClick acquires Sleek](https://blog.zeroclick.ai/zeroclick-acquires-sleek-to-bring-ai-to-the-browser/)
- [Ryan Hudson founder interview — Affiverse](https://hellopartner.com/2025/09/05/ryan-hudson-founder-of-zeroclick-talks-affiliate-marketing-ai-search-ads-and-sleek-acquisition/)
- [Affiverse: Honey to ZeroClick deep dive](https://www.affiversemedia.com/from-honey-to-zeroclick-how-a-4-billion-exit-led-to-the-next-ai-advertising-revolution/)
- [Michael Ludden — LinkedIn](https://www.linkedin.com/in/mludden/)
- [ZeroClick — Mi3 coverage](https://www.mi-3.com.au/01-09-2025/zeroclick-secures-55-million-ai-focused-ad-network-launch)
