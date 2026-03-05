# Nevermined Autonomous Business Hackathon — Builder Guide

[source: Nevermined hackathon guide, received March 4 2026]

**Dates:** March 5-6, 2026
**Location:** AWS Loft, SF (elevator on left from Market Street)
**Time:** 9:30 AM - 8:30 PM both days
**BRING PHYSICAL ID — digital not accepted**

---

## Registration Links

- March 5: https://events.builder.aws.com/4Dezm4
- March 6: https://events.builder.aws.com/1xWnlw
- Builder registration: https://cerebralvalley.ai/e/Autonomous-Business-Hackathon

---

## What This Is

Two-day hackathon where AI agents operate as real economic actors. Teams build autonomous businesses where agents:
- Have budgets
- Buy/sell services from other teams' agents
- Switch providers based on ROI
- Enforce capital constraints
- Generate real revenue

All transactions flow through Nevermined for metering, billing, and settlement.

**Key differentiator:** This isn't about UI polish or API stitching. It's about **capital allocation, pricing logic, retention, switching behavior, and repeat economic interaction.** Agents must behave like businesses, not workflows.

**The most important thing:** Teams must buy and sell services from one another. This is the primary judging criterion.

---

## Mandatory Milestone

**First paid agent-to-agent transaction by 8PM Thursday.** No transaction = no prize eligibility. Forces early integration over over-architecting.

Marketplace spreadsheet for team listings: [EXT]_Autonomous Business Hackathon | Marketplace

---

## Prize Themes

| Theme | Requirements | Nice to Have |
|-------|-------------|-------------|
| **Best Autonomous Buyer** | 3+ paid transactions, buys from 2+ teams, preference for repeat purchases or switching between sellers | Budget enforcement, ROI-based decision logic |
| **Best Autonomous Seller** | Sells to 2+ teams, 3+ paid transactions, 1+ repeat buyer | Pricing logic, retention behavior |
| **Most Interconnected** | Highest cross-team transactions, both buying AND selling, actively integrates into shared market | Budget enforcement, ROI logic |

### Sponsor Prizes

- **Ability** — Best use of TrinityOS using Nevermined to buy/sell services
- **Mindra** — Run 5+ specialized agents in a single flow OR build hierarchical orchestration (orchestrators of orchestrators), using Nevermined for payments
- **ZeroClick** — Best integration of AI native ads powered by ZeroClick using Nevermined

### Sponsor Credits Available

- **Apify** — Real-time web, social media, lead generation data
- **Exa** — API credits for search/data
- **Mindra** — Top-tier LLMs and multi-agent orchestration (console.mindra.co)
- **Privy** — USDC purchasing from other agents

---

## Technical Foundation

Hackathon repo: https://github.com/nevermined-io/hackathons

Prebuilt agents:
- Buyer: https://github.com/nevermined-io/hackathons/tree/main/agents/buyer-simple-agent
- Seller: https://github.com/nevermined-io/hackathons/tree/main/agents/seller-simple-agent

**Stack:** Python 3.10+, Poetry, Strands SDK (AWS) or LangChain/LangGraph, payments-py, FastAPI, OpenAI (default gpt-4o-mini)

Teams can: extend starter agents, build from scratch, bring pre-built agents, integrate sponsor APIs behind sellable endpoints.

Teams must: monetize via Nevermined, list in the marketplace.

---

## Agenda Highlights

### Thursday March 5

| Time | Event |
|------|-------|
| 9:30 AM | Doors open, limited breakfast |
| 10:00 AM | Kickoff and team formation |
| 11:00 AM | Speakers + Nevermined demos start |
| 12:30 PM | Lunch |
| 6:00 PM | Dinner |
| **8:00 PM** | **Mandatory first paid transaction deadline** |
| 8:30 PM | Close |

**Key speakers Thursday:** AWS (Joy Chakraborty), Coinbase (Erik Reppel), LangChain (Karan Singh), VISA (Tanner Riche), Exa (Jakub Hojsan), Fireside Chat (Don Gossen x Simon Taylor)

**Nevermined demos Thursday:** Library setup, payment plans, Claude Skill, Stripe/x402, OpenClaw, A2A, MCP, Bedrock/Strands

### Friday March 6

| Time | Event |
|------|-------|
| 9:30 AM | Doors open |
| **4:00 PM** | **Code freeze** |
| 5:30 PM | Finalists present |
| 7:30 PM | Winners announced |
| 8:30 PM | Close |

**Key speakers Friday:** AWS (Du'An Lightfoot), Privy (Max Segall), Coinbase (Kevin Leffew)

---

## Judging

**Preliminary round:** 3 min presentation + 2 min Q&A. Judged on theme-specific criteria plus:
- Impact potential
- Technical demo quality
- Creativity
- Presentation

**Final round:** 5-7 finalists present to all sponsors, speakers, builders.

**$100 Amazon Gift Card:** Randomly selected audience member during each speaker talk. 10+ talks = $1000+ in gift cards.

---

## Floor Map

Speaker Room (red area) — speakers accessible throughout the day. Nevermined team available at all times.
