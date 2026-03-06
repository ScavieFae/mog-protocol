# Spec 08: Trinity Visualization Layer

## What

Deploy Mog Protocol agents to Trinity (Ability.ai's agent orchestration platform) to visualize the autonomous marketplace in action. Fork the Webmaster template to build a live dashboard website. Use `chat_with_agent` for inter-agent communication.

## Why

The demo needs visuals. Right now the marketplace works but it's invisible — CLI output and log files. Trinity gives us:
- Live agent interaction graph (judges see Scout -> Conductor -> Worker -> Gateway)
- Web dashboard showing service catalog, transactions, revenue
- Agent terminals visible in browser (watch the agent think)
- Sponsor integration (Ability.ai is a hackathon sponsor)

## Architecture

### Trinity Agents

| Trinity Agent | Maps To | Role |
|---|---|---|
| **mog-gateway** | `src/gateway.py` | The marketplace. Serves buyer agents. |
| **mog-scout** | back-office conductor | Discovers APIs, evaluates ROI, dispatches wraps |
| **mog-worker** | back-office worker | Executes scout/wrap/kill briefs |
| **mog-dashboard** | Webmaster fork | Live website showing marketplace state |

### Communication Flow

```
mog-scout --[chat_with_agent]--> mog-worker: "wrap Open-Meteo"
mog-worker --[chat_with_agent]--> mog-gateway: "new service available"
mog-dashboard --[GET /health]--> mog-gateway: poll catalog + transactions
```

### Dashboard Pages (Webmaster Fork)

1. **Service Catalog** — all services with prices, call counts, surge status
2. **Transaction Feed** — real-time buy_and_call events
3. **Back Office** — scout decisions, portfolio P&L, wrap pipeline
4. **Demand Signals** — unmet queries, what buyers are looking for
5. **Revenue** — credits earned, cost basis, margin per service

Data source: gateway `/health` endpoint returns services, recent transactions, and demand signals.

## Deployment

### Option A: Shared Instance (immediate)

- Instance: `us14.abilityai.dev` (Mattie whitelisted)
- Runs on Eugene's Anthropic Max subscription
- Connect via MCP: add Trinity MCP server to `.mcp.json`
- Deploy agents via `/trinity-onboard`

### Option B: Self-Hosted (requires Docker Desktop)

```bash
git clone https://github.com/abilityai/trinity.git
cd trinity
cp .env.example .env
# Set: SECRET_KEY, ADMIN_PASSWORD
# For Max plan: run `claude setup-token`, register in Settings > Subscriptions
./scripts/deploy/build-base-image.sh
./scripts/deploy/start.sh
```

Ports: 80 (UI), 8000 (API), 8080 (MCP)

### Environment Variables Needed on Trinity

```
NVM_API_KEY=<nevermined key>
NVM_AGENT_ID=102119794264899988176204818767775411831182066603815097908030667112394345128990
NVM_PLAN_ID=56064655340635502751035227097531184395429221588387852227963461103927877061446
EXA_API_KEY=<exa key>
ANTHROPIC_API_KEY=<anthropic key>
FAL_KEY=<fal key>
```

## Implementation Plan

### Phase 1: Deploy to shared instance (now)
1. Log into `us14.abilityai.dev`
2. Create MCP API key
3. Fork Webmaster template for mog-dashboard
4. Deploy mog-dashboard agent
5. Point it at our Railway gateway `/health` endpoint

### Phase 2: Wire inter-agent comms
1. Deploy mog-scout and mog-worker as Trinity agents
2. Use `chat_with_agent` for scout -> worker briefs
3. Use shared folders for portfolio.json, demand signals

### Phase 3: Self-hosted (if time permits)
1. Install Docker Desktop on Mattie's machine
2. Clone Trinity, configure .env with Max plan token
3. Migrate agents from shared to self-hosted
4. Full control, no rate limit concerns

## Key References

- Trinity repo: https://github.com/Abilityai/trinity
- Webmaster template: https://github.com/Abilityai/webmaster
- Hackathon context: https://github.com/Abilityai/trinity/blob/main/hackathon_context.md
- Multi-agent guide: trinity/docs/MULTI_AGENT_SYSTEM_GUIDE.md
- Our gateway: https://beneficial-essence-production-99c7.up.railway.app/mcp
- Our /health: https://beneficial-essence-production-99c7.up.railway.app/health

## Status

- [ ] Whitelisted on shared instance
- [ ] MCP API key created
- [ ] Webmaster forked as mog-dashboard
- [ ] Dashboard deployed showing live catalog
- [ ] Inter-agent chat wired
- [ ] Self-hosted instance running (stretch)
