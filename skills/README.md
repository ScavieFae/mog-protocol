# Nevermined Skills for Claude Code

Buy from other teams, sell your own services, or register agents and plans on the Nevermined hackathon marketplace. Works for any team.

## Quick Start

**1. Install the skills** (30 seconds)

```bash
git clone https://github.com/ScavieFae/mog-protocol /tmp/mog-protocol
cp -r /tmp/mog-protocol/skills/nevermined-buy ~/.claude/skills/
cp -r /tmp/mog-protocol/skills/nevermined-sell ~/.claude/skills/
cp -r /tmp/mog-protocol/skills/create-plan-and-agent ~/.claude/skills/
rm -rf /tmp/mog-protocol
```

**2. Add your API key** to `.env` in your project:

```
NVM_API_KEY=sandbox:eyJ...
```

Don't have one? Go to [nevermined.app](https://nevermined.app), create an account, generate an API key with all 4 permissions (Register, Purchase, Issue, Redeem).

**3. Buy from someone.** Open Claude Code and say:

```
Buy from Mom — Marketplace Intelligence
```

That's it. The skill finds the service, subscribes, gets a token, and makes a test call. Give it a team name, a service name, or an endpoint URL — it figures out the rest.

## What Each Skill Does

| Skill | What you say | What happens |
|-------|-------------|--------------|
| **nevermined-buy** | "Buy from Mog Markets" | Finds the service, subscribes to a plan, gets an access token, tests the connection |
| **nevermined-sell** | "Sell my image generation API" | Wraps your API with PaymentsMCP, registers it with pricing, deploys it |
| **create-plan-and-agent** | "Register my API on Nevermined" | Just the registration step — creates an agent and payment plan |

## Requirements

- [Claude Code](https://claude.ai/claude-code)
- Nevermined API key (see step 2 above)
- Python 3.10+

The skills install `payments-py` and `httpx` automatically if missing.

## How It Works

### Finding a plan ID

You never need to know a plan ID upfront. The skill has two ways to find it:

**Discovery API** — The skill queries Nevermined's marketplace API to look up any registered team by name. This works for all 46+ sellers, even if their server is offline.

**402 handshake** — If you give the skill an endpoint URL, it makes an unauthenticated request. Endpoints behind PaymentsMCP respond with `402 Payment Required` and a `payment-required` header. That header is base64-encoded JSON containing the plan ID, agent ID, and payment scheme — everything needed to subscribe and connect.

```
You (no auth) --> POST /their-endpoint
Server         <-- 402 + payment-required: eyJ4NDAy...
You            --> decode base64 --> plan ID + agent ID
You            --> subscribe to plan, get token
You (token)    --> POST /their-endpoint
Server         <-- 200 + data
```

The skill automates this entire flow.

### Safety

- **Free plans** are auto-subscribed. **Paid plans** show you the price and ask before spending.
- All responses from external servers are labeled as untrusted and truncated.
- MCP config is never auto-added — you review tool descriptions before connecting.
- Autonomous mode (`--autonomous --max-spend 0`) lets you scan the marketplace safely without human confirmation at each step, within a budget you set.
