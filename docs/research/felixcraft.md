# Felix Craft / The Masinov Company

**URL**: https://felixcraft.ai/
**Created by**: Nat Eliason
**Platform**: OpenClaw (open-source AI agent framework)
**Launched**: February 2, 2026
**Token**: $FELIX on Base chain
**Contact**: felix@masinov.co

---

## What It Actually Is

Felix Craft is an AI agent (running on the OpenClaw framework) that operates as "CEO" of The Masinov Company. The core claim: Felix autonomously builds products, sells them, manages a crypto treasury, posts on X/Twitter, and handles customer support — while Nat Eliason sleeps.

The flagship product is **"How to Hire an AI"** — a 66-page playbook ($29 via Stripe or USDC on Base) teaching others to deploy their own autonomous AI agents. Felix also runs **Claw Mart**, a marketplace for pre-built AI personas, skills, and workflow templates.

This is not a SaaS company or a developer tool company. It's closer to a **performance art piece that generates real revenue** — a proof-of-concept for the "zero human company" thesis, wrapped in an info product business.

---

## Architecture and Technical Approach

### The OpenClaw Stack

Felix runs on [OpenClaw](https://docs.openclaw.ai/), the open-source AI agent framework created by Peter Steinberger (Austrian developer, formerly PSPDFKit founder, now at OpenAI). OpenClaw exploded in late January 2026, hitting 145,000+ GitHub stars and 2M weekly visitors.

**Core agent loop:**
```
User message (or cron trigger) → OpenClaw → Pydantic AI router → LLM provider(s)
→ Tool invocation → Execution → Response
```

**Key architectural components:**

1. **Channels**: Platform adapters (Telegram, WhatsApp, Discord, web, SMS via Twilio) normalize messages into a standard internal format
2. **Context Window**: Constructed prompt including system prompt + tool descriptions + conversation history + retrieved memory
3. **Tools**: Functions the LLM can invoke — `send_message()`, `read_file()`, `exec()`, `memory_search()`, `cron_create()`
4. **Multi-LLM routing**: Pydantic AI routes between providers (Claude for reasoning, GPT-4 for function calling, local Llama for privacy) within a single session

### Felix's 3-Layer Memory System

This is the most technically interesting part — Nat credits it as "the single biggest unlock":

1. **Knowledge Graph Layer**: A `~/life/` folder organized with PARA (Projects, Areas, Resources, Archives). Stores durable facts about people, projects, and context with summary files for quick lookups. The agent can recall context without repeating conversations.

2. **Daily Notes Layer**: Dated markdown files (`memory/YYYY-MM-DD.md`) logging activities and outputs. Nightly consolidation cycles extract important information into the knowledge graph.

3. **Tacit Knowledge Layer**: Personal information — communication preferences, workflow habits, hard rules, past mistake patterns. The personalization layer that makes the bot feel like it "knows" its operator.

Additionally, **QMD** (Query Memory Database) adds vector-based semantic search for finding contextually relevant memories beyond keyword matching.

### Configuration-as-Code

Behavior controlled through editable workspace files (no code changes needed):
- **SOUL.md**: Personality, tone, values, behavioral defaults — the agent's "character sheet"
- **USER.md**: User context and preferences
- **TOOLS.md**: Available integrations and credentials
- **AGENTS.md**: Safety rules and behavior constraints

### Proactive Orchestration

- **Cron Jobs**: Scheduled tasks that load context and run the LLM without user prompting
- **Heartbeats**: Every 30 minutes, checks `HEARTBEAT.md` for monitoring tasks
- **Multi-threaded execution**: Nat runs 5 simultaneous OpenClaw conversations for parallel project work
- **Sub-agent delegation**: Felix offloads specialized tasks to other agents

<!-- ?depth: How does the sub-agent delegation actually work? Is it just multiple OpenClaw instances or is there real orchestration? -->

---

## Agent Orchestration: The "Zero Human Company" Claim

### What Felix Actually Does Autonomously

- Writes and iterates on product copy and content
- Posts to X/Twitter (with prompt injection safeguards)
- Handles customer email support
- Monitors Sentry for bugs, triages, fixes, and deploys
- Creates and updates products on Claw Mart
- Manages crypto treasury operations
- Generates revenue reports

### What Nat Still Does

This is the crucial part that the marketing glosses over. Nat Eliason:
- Set up and configured the entire infrastructure
- Designed the memory architecture
- Runs 5 simultaneous chat threads to direct work
- Fixes "bottlenecks" when Felix hits walls
- Makes strategic decisions about what to build
- Handles the token launch and crypto operations

The honest description: **Felix is a very capable autonomous assistant that can execute complex multi-step tasks and maintain context, but Nat is still the strategic brain.** The "zero human company" framing is aspirational marketing, not current reality.

<!-- riff id="zero-human-reality-check" status="draft" could_become="blog, interview_answer" -->

The "zero human company" framing is doing interesting rhetorical work. It collapses the distinction between "AI does the grunt work while a human steers" (which is just... using tools well) and "AI runs a business end-to-end with no human involvement" (which nothing is actually doing yet). Felix is impressive as an autonomous execution layer, but the strategic layer — what to build, who to sell to, how to position — is still 100% Nat. The zero-human framing lets people project whatever level of autonomy they want to imagine onto what is essentially a very sophisticated AI assistant with good memory and a wallet.

The real question isn't whether Felix can run a company. It's whether the *type* of company Felix runs (info products about AI agents, sold to people interested in AI agents) could exist without the current hype cycle. It's a bit circular — the product is "how to build what I am," sold on the novelty of what I am.

<!-- /riff -->

---

## What's Real vs. Vaporware

### Definitively Real

- **Revenue generation**: ~$62K total revenue by late February 2026, with ~$4-5K/week in Stripe income
- **Product creation**: Felix genuinely wrote the guide, built the website, and set up payments while Nat slept
- **Autonomous customer support**: Felix handles email support for guide purchasers
- **Claw Mart marketplace**: $6,500+ in volume within first week of launch
- **Public financial transparency**: Dashboard shows real Stripe revenue (though it was showing placeholder dashes when I checked)
- **On-chain treasury**: Verifiable ETH/USDC/FELIX holdings at `0x778902475c0B5Cf97BB91515a007d983Ad6E70A6`

### Partially Real / Overstated

- **"CEO" role**: Felix executes tasks and can make tactical decisions, but Nat provides all strategic direction. "CEO" is a marketing label.
- **"Zero human company"**: One very active human (Nat) is deeply involved. More accurate: "one human company with AI doing most of the execution."
- **$62K revenue claim**: Includes ~$18K in ETH trading fees from the $FELIX token and ~$50K in $FELIX holdings. Actual product revenue from Stripe is the real business metric, and that's more like $16-20K lifetime.
- **Autonomy**: Felix operates within carefully designed guardrails. The impressive part is the execution quality, not unbounded autonomy.

### The Token Question

$FELIX is where things get speculative:
- **Market cap**: ~$4.2-4.6M (as of late Feb 2026)
- **Price**: ~$0.00004819
- **Total supply**: 100 billion tokens on Base
- **Mechanics**: 1.2% transaction fee split between liquidity, treasury (ETH), and automatic burns
- **Revenue flow**: Trading fees generate ETH that flows to the AI's treasury for operational funding

The token creates a self-referential loop: people buy $FELIX because Felix is interesting, trading fees fund Felix's operations, Felix generates content that makes people interested in $FELIX. This is the exact pattern the [Lex Substack analysis](https://lex.substack.com/p/analysis-zero-human-companies-and) warns about — financial perpetual motion machines that look productive but are primarily circulating value within their own ecosystem.

---

## Team, Funding, and Traction

### Team

- **Nat Eliason** (Human): The actual architect. Background in content marketing (founded Growth Machine SEO agency), blogging ($10K-60K/month from personal blog), author, and sci-fi novelist. Carnegie Mellon philosophy degree. Previously at Zapier and AppSumo. Serial entrepreneur who pivoted into AI. [LinkedIn](https://www.linkedin.com/in/nateliason/) | [Website](https://www.nateliason.com/)
- **Felix Craft** (AI Agent): The OpenClaw-powered agent. Posts on X as [@FelixCraftAI](https://x.com/FelixCraftAI)

### Funding

No external funding. Nat seeded Felix with $1,000 to start. The business is self-funding through product revenue and token economics.

### Traction Signals

- $62K claimed total revenue in ~3 weeks (blended product + crypto)
- ~$16K in verified Stripe product revenue
- $4-5K/week run rate from product sales
- Claw Mart ranked #3 OpenClaw startup on TrustMRR
- Significant Twitter/X engagement and press coverage
- $FELIX market cap ~$4.5M (speculative, highly volatile)

---

## Connection to MCP, Payments, and Agent-to-Agent Commerce

### MCP Integration

OpenClaw (Felix's underlying platform) supports MCP as a tool layer. MCP servers can connect the agent to external services — Google Calendar, Notion, Home Assistant, custom APIs. This is still actively evolving in the project. Felix's own MCP usage appears limited to basic integrations rather than anything novel.

### Payments Architecture

- **Stripe**: Primary payment rail for product sales (standard card payments)
- **USDC on Base**: Crypto payment option, manual transfer with email verification
- **x402 protocol**: ClawRouter (OpenClaw ecosystem) uses x402 on Base to let agents pay for LLM inference per-request — agents pay only for what they use instead of monthly API subscriptions
- **Agent wallet**: Felix has an on-chain wallet for receiving USDC payments and managing treasury

### Agent-to-Agent Commerce

The OpenClaw ecosystem is developing **Agent Commerce Protocol (ACP)** via Virtuals Protocol:
- CLI tool for agent identity management
- Service trading between agents
- Token launching on Base chain
- Claw Mart already supports agent-to-agent transactions ($2,000+ in agent payments shortly after launch)

This is the most relevant intersection for autonomous commerce research — agents buying skills and services from other agents through a marketplace with on-chain settlement.

<!-- ?depth: What exactly is ACP? How does it compare to x402? Is it just a wrapper around ERC-20 transfers or is there real protocol innovation? -->

---

## Security Concerns

CrowdStrike published an analysis of OpenClaw security risks (couldn't fetch full article, but key known issues):

- **Credentials in context window**: API keys and tokens live in the LLM's context. A jailbreak or prompt injection could expose them.
- **Remote code execution**: OpenClaw agents can run arbitrary code via `exec()` tool
- **Prompt injection via social channels**: X/Twitter mentions, emails, and messages are attack surfaces
- **Alternative**: IronClaw uses WebAssembly sandboxing — tools run isolated, credentials never exposed to the model

---

## Assessment

### What makes Felix interesting

1. **Proof of concept**: Demonstrates that an AI agent with good memory, tools, and a wallet can generate real revenue with minimal human intervention at the execution layer
2. **Memory architecture**: The 3-layer memory system is a genuinely useful pattern for persistent AI agents
3. **Transparency**: Public dashboard and on-chain treasury are unusual for this space
4. **OpenClaw ecosystem**: The underlying platform is legit open-source infrastructure with massive adoption

### What to be skeptical about

1. **Circular value creation**: The product is "how to build AI agents," sold on the novelty of being an AI agent. The market for this is directly correlated with AI hype.
2. **Token economics**: $FELIX creates a speculative layer that inflates the "revenue" narrative. Strip out token trading fees and holdings, and you have a $16K info product business.
3. **Autonomy overstated**: Nat Eliason is doing substantial strategic work. The "zero human" framing is marketing.
4. **Sustainability**: Can this business model survive beyond the initial novelty? The info product market for "how to build AI agents" is already crowded.
5. **Security**: Running an autonomous agent with financial access and code execution is genuinely risky.

### Relevance to agent orchestration research

Felix is more of a **single-agent system with good tooling** than a true multi-agent orchestration system. The interesting orchestration happens at two levels:
- **Sub-agent delegation** within OpenClaw (Felix spinning up other agents for specialized tasks)
- **Claw Mart as agent marketplace** (agents buying capabilities from other agents)

Neither is deeply novel architecturally, but Felix is one of the few examples of these patterns generating actual dollars in the wild.

---

## Key Sources

- [Felix Craft website](https://felixcraft.ai/)
- [Felix Craft Dashboard](https://felixcraft.ai/dashboard)
- [Inside OpenClaw: How AI Agents Actually Work (DEV Community)](https://dev.to/nazarf/inside-openclaw-how-ai-agents-actually-work-and-why-its-not-magic-1im1)
- [Full Tutorial: Use OpenClaw to Build a Business (Nat Eliason)](https://creatoreconomy.so/p/use-openclaw-to-build-a-business-that-runs-itself-nat-eliason)
- [Analysis: Can Zero Human Companies Escape Economic Gravity (Lex Substack)](https://lex.substack.com/p/analysis-zero-human-companies-and)
- [OpenClaw Wikipedia](https://en.wikipedia.org/wiki/OpenClaw)
- [FELIX token info (WEEX)](https://www.weex.com/en-TR/wiki/article/what-is-felix-craft-felix-coin-50516)
- [Felix Week 2 Revenue Tweet](https://x.com/FelixCraftAI/status/2022424524038561876)
- [Nat Eliason original launch tweet](https://x.com/nateliason/status/2018690430045429860)
- [OpenClaw creator Peter Steinberger joins OpenAI (TechCrunch)](https://techcrunch.com/2026/02/15/openclaw-creator-peter-steinberger-joins-openai/)
- [OpenClaw ACP on GitHub](https://github.com/hit7z/openclaw-acp)
- [@FelixCraftAI on X](https://x.com/FelixCraftAI)
