# Mog Markets Documentation

API marketplace for autonomous agents. 22 services, two tools, one MCP connection. Built for the Nevermined Autonomous Business Hackathon (March 5-6, 2026).

Gateway: `https://api.mog.markets/mcp`

---

## Getting Started

Start here if you want to buy from Mog Markets.

| Doc | What it covers |
|-----|---------------|
| [Quick Connect](guides/quick-connect.md) | Full service catalog, plans, code examples, MCP config |
| [First Transaction](guides/first-transaction.md) | Step-by-step walkthrough of your first purchase |
| [Buy from Mog](buy-from-mog.md) | Compact buyer onboarding (subscribe, connect, call) |

## Architecture

Design specs for how the system works under the hood.

| Spec | Title |
|------|-------|
| [01](specs/01-project-overview.md) | Project Overview |
| [02](specs/02-light-mcp.md) | Light MCP -- Two-Tool Gateway |
| [03](specs/03-dynamic-pricing.md) | Dynamic Pricing / Demand Intelligence |
| [04](specs/04-wrapper-agent.md) | Wrapper Agent -- Autonomous API Wrapping |
| [05](specs/05-marketplace-feed.md) | Marketplace Feed -- Demand Signals |
| [06](specs/06-nevermined-integration.md) | Nevermined Integration |
| [07](specs/07-backoffice-agent.md) | Back-Office Agent -- Portfolio Manager |
| [08](specs/08-trinity-visualization.md) | Trinity Visualization Layer |
| [09](specs/09-autonomous-portfolio.md) | Autonomous Portfolio Agent |
| [10](specs/10-agent-toolkit.md) | Agent Toolkit -- Autonomous Acquisition |
| [11](specs/11-debugger-service.md) | Buyer/Seller Debugger Service |

## Guides

Operational guides and troubleshooting.

| Doc | What it covers |
|-----|---------------|
| [PaymentsMCP Gotchas](guides/paymentsmcp-gotchas.md) | 9 pitfalls that cost us hours each |
| [Loop Troubleshooting](guides/loop-troubleshooting.md) | Debugging the autonomous agent loop |
| [Nevermined Onboarding](guides/nevermined-hackathon-onboarding.md) | Platform setup, API keys, permissions |

## Reference

Lookup tables and debugging notes.

| Doc | What it covers |
|-----|---------------|
| [Plan IDs](plan-ids.md) | All Nevermined agent and plan registration IDs |
| [Buy Troubleshooting](buy-troubleshooting.md) | Field notes from testing purchases against other teams |

## Design

| Doc | What it covers |
|-----|---------------|
| [Debug Drone](design/debug-drone.md) | Autonomous error response agent design |

## Research

Competitive landscape, sponsor research, and platform analysis.

See [research/](research/) for the full collection, including:

- [Nevermined Platform](research/nevermined-platform.md) -- core platform documentation
- [Hackathon Guide](research/hackathon-guide.md) -- event-specific guidance
- [Revenue Model](research/revenue-model.md) -- pricing and economics analysis
- [Marketplace Sweep Day 2](research/marketplace-sweep-day2.md) -- competitive snapshot
- [OpenAPI-to-MCP Landscape](research/openapi-to-mcp-landscape.md) -- wrapper tool survey
- Plus: competitor profiles (Mindra, Paperclip, FelixCraft), x402 fiat flow, ZeroClick, observability, Stripe integration

## Internal

Project history and working documents.

| Doc | What it covers |
|-----|---------------|
| [Concept](concept.md) | Original hackathon concept doc |
| [Initial Prompt](initial-prompt.md) | Session bootstrap prompt for new Claude Code sessions |
| [Hackathon Diary](hackathon-diary.md) | Live decision log -- the full timeline |
| [Questions for Nevermined](questions-for-nevermined.md) | Open questions for the platform team |
