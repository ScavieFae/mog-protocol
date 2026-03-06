# Nevermined Skills for Claude Code

Three skills for the Nevermined hackathon. Buy from other teams, sell your own services, or register agents and plans. Works for any team -- not Mog-specific.

## Install

```bash
git clone https://github.com/ScavieFae/mog-protocol /tmp/mog-protocol
cp -r /tmp/mog-protocol/skills/nevermined-buy ~/.claude/skills/
cp -r /tmp/mog-protocol/skills/nevermined-sell ~/.claude/skills/
cp -r /tmp/mog-protocol/skills/create-plan-and-agent ~/.claude/skills/
rm -rf /tmp/mog-protocol
```

Or tell your Claude:

> Import the Nevermined skills from https://github.com/ScavieFae/mog-protocol -- they're in the skills/ directory. Copy nevermined-buy, nevermined-sell, and create-plan-and-agent to ~/.claude/skills/

## Skills

### nevermined-buy

Buy from any team on the marketplace. Discovers the service, subscribes, gets a token, configures MCP, makes a test call.

```
"Buy from Mog Markets"
"Subscribe to Trust Net"
"Connect to the weather API on Nevermined"
```

### nevermined-sell

Sell your own service. Wraps your API as a PaymentsMCP server, registers it with pricing, deploys it, generates a buy guide for customers.

```
"Sell my image generation API"
"Set up paid access to my search tool"
"Monetize my agent on Nevermined"
```

### create-plan-and-agent

Just the registration step. Creates an agent and payment plan on Nevermined so you can wire it into your PaymentsMCP server.

```
"Register my weather API on Nevermined"
"Create a plan with USDC pricing"
"Set up a free tier for my service"
```

## Requirements

- Claude Code
- Nevermined API key from [nevermined.app](https://nevermined.app) (all 4 permissions)
- Python 3.10+ with `payments-py` and `httpx`
