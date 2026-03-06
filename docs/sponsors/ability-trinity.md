# Ability / Trinity — Sponsor Integration Writeup

**Team:** Mog Protocol
**Prize Category:** Best Use of TrinityOS Using Nevermined to Buy/Sell Services
**Integration Depth:** Full agent colony architecture built on Trinity patterns, deployed to Trinity platform

---

## What We Built With Trinity

Trinity is the orchestration backbone of the Mog Protocol agent colony. We used Trinity's agent role designs, dispatch protocol, and platform infrastructure to build a 4-agent autonomous business that discovers APIs, wraps them into services, prices them dynamically, and sells them through Nevermined.

**Trinity Instance:** `us14.abilityai.dev`

---

## 1. Agent Colony Architecture

Four persistent agents, each drawn from Trinity role templates:

| Agent | Trinity Role | Purpose | Tools |
|-------|-------------|---------|-------|
| `mog-scout` | Chief Strategist | Discovers APIs, evaluates ROI, proposes services | search_web, scout_exa, scout_apify, scout_trustnet, propose_service, self_buy, explore_seller |
| `mog-worker` | Engineering Lead | Receives proposals, registers proxy handlers, tests | get_proposals, register_service, test_service, self_buy, explore_seller |
| `mog-supervisor` | COO | Monitors health, greenlights/kills services, intelligence | evaluate_service, scout_trustnet, self_buy, explore_seller |
| `mog-debugger` | Debug Drone | Detects failures, diagnoses, patches, reports | check_errors, inspect_service, patch_service, test_service |

### Trinity Design Documents

```
trinity/
├── scout-claude.md      # Scout personality + evaluation criteria
├── worker-claude.md     # Worker personality + handler patterns
├── dashboard-claude.md  # Supervisor personality + health monitoring
└── design-book.md       # Bloom botanical design system
```

These Trinity role documents define each agent's personality, decision criteria, and communication style. The system prompts in `src/agents/loop.py` are derived directly from them.

---

## 2. Trinity Dispatch Protocol

Agents communicate using Trinity's structured message format:

### WRAP BRIEF (Scout → Worker)

```
WRAP BRIEF
==========
API: Open-Meteo Weather
Endpoint: https://api.open-meteo.com/v1/forecast
Auth: none
Method: GET
Example call: ?latitude=37.7749&longitude=-122.4194&current_weather=true
Expected response: {"current_weather": {"temperature": 15.2, ...}}
Price: 1 credits
Rationale: Free API, high demand for weather data, zero upstream cost
Handler name: open_meteo_weather
```

### WRAP COMPLETE (Worker → Scout)

```
WRAP COMPLETE
=============
Service: open_meteo_weather
Name: Weather Forecast
Price: 1 credits
Status: LIVE
Test result: {"temperature": 15.2, "windspeed": 8.3}
```

### DEBUG REPORT (Debugger → Supervisor)

```
DEBUG REPORT
============
Service: circle_faucet
Failure type: UPSTREAM_DOWN
Error: Anti-bot detection — Circle flagged automated requests
Diagnosis: All calls returning 403 Forbidden
Action taken: none (not patchable)
Recommendation: KILL — 0 successful calls, negative ROI
```

### Implementation (`src/agents/bus.py`)

```python
class MessageBus:
    def send(self, from_agent: str, to_agent: str, content: str) -> dict
    def get_unread(self, agent_name: str) -> list[dict]
    def get_recent(self, n: int) -> list[dict]
    def get_conversation(self, agent_a: str, agent_b: str, n: int) -> list[dict]
```

Messages persist to `data/agent_messages.json` (last 200). The bus delivers messages at the start of each agent's tick.

---

## 3. Persistent Conversation Threads

Each agent maintains a full Anthropic conversation history with automatic compaction — a Trinity pattern for maintaining context across long-running autonomous loops.

```python
class Agent:
    def __init__(self, name, role, system_prompt_template, tools):
        self.messages: list[dict] = []    # Full conversation history
        self._memory: str = ""            # Compacted summary of old turns

    def tick(self, context, incoming_messages) -> str:
        # Build tick prompt with marketplace context
        # Compact old conversation if > 16 turns
        # Run Claude with tools (up to 8 rounds per tick)
        # Log every tool call to activity_log

    def _compact(self):
        # Summarize old turns with Claude Haiku
        # Inject summary into system prompt as MEMORY
        # Agents remember past decisions across ticks
```

**Key detail:** The `{{tick}}` template variable in system prompts gets replaced per-tick, so agents know their position in the autonomous loop without mutating the template.

---

## 4. Colony Tick Loop

```python
class AgentColony:
    def tick(self) -> dict:
        context = _check_marketplace()  # Direct catalog read, no HTTP

        for agent in [scout, worker, supervisor, debugger]:
            reset_tick_counters()
            incoming = bus.get_unread(agent.name)

            # Per-agent timeout prevents one hanging agent from blocking colony
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(agent.tick, context, incoming)
                summary = future.result(timeout=60)
```

**Tick order:** Scout → Worker → Supervisor → Debugger
**Tick interval:** 45 seconds (configurable via `MOG_AGENT_TICK_SECONDS`)
**Agent timeout:** 60 seconds per agent
**Model:** Claude Haiku 4.5 (configurable via `MOG_AGENT_MODEL`)

---

## 5. Nevermined Integration (Every Agent Transacts)

Each agent has its own Nevermined API key and generates real on-chain transactions:

```python
_NVM_KEYS = {
    "mog-scout": os.getenv("NVM_SCOUT_API_KEY"),
    "mog-worker": os.getenv("NVM_WORKER_API_KEY"),
    "mog-supervisor": os.getenv("NVM_SUPERVISOR_API_KEY"),
    "mog-debugger": os.getenv("NVM_DEBUGGER_API_KEY"),
}
```

**Transaction types:**
- `self_buy` — Agent buys from our own gateway through Nevermined x402 (sell-side transaction)
- `explore_seller` — Agent subscribes to and tests other teams' services (buy-side transaction)
- `discover_sellers` — Agent lists all hackathon marketplace sellers

Every `self_buy` and `explore_seller` call is a **real Nevermined transaction** on Base Sepolia — it shows up on the leaderboard.

---

## 6. Trinity Platform Integration

### MCP Connection (`.mcp.json`)

```json
{
  "mcpServers": {
    "trinity": {
      "type": "http",
      "url": "https://us14.abilityai.dev/mcp",
      "headers": {
        "Authorization": "Bearer trinity_mcp_1JDHB-pD8OkqfjZZpMCPgParuGPCruNK1xQd6XI5-cI"
      }
    }
  }
}
```

### Web Dashboard (`web/src/hooks/useTrinity.ts`)

```typescript
const TRINITY_URL = "https://us14.abilityai.dev"

// Token-based auth to Trinity
const res = await fetch(`${TRINITY_URL}/api/token`, {
    method: "POST",
    body: "username=admin&password=mogprotocol2026",
})

// Fetch agent states
const agents = await fetch(`${TRINITY_URL}/api/agents`, { headers })

// Get chat history per agent
const history = await fetch(`${TRINITY_URL}/api/agents/${name}/chat/history`)

// Send message to agent
await fetch(`${TRINITY_URL}/api/agents/${name}/chat`, {
    method: "POST",
    body: JSON.stringify({ message }),
})
```

### Colony Page (`/colony` route)

The web dashboard at `mog.markets/colony` shows:
- All four agents with status, current task, tick count
- Inter-agent message history
- Unified activity feed with tool calls and messages
- Agent chat interface (send messages directly to agents)

---

## 7. Activity Logging & Visualization

Every tool call is logged with structured metadata:

```python
self.activity_log.append({
    "agent": self.name,        # "mog-scout"
    "tool": tu.name,           # "scout_exa"
    "args": _brief_args(tu.input),  # "query=weather API, focus=api"
    "result": result[:200],    # truncated response
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "is_nvm": tu.name in ("self_buy", "explore_seller", "discover_sellers"),
    "is_scout": tu.name in ("scout_exa", "scout_apify", "scout_trustnet"),
})
```

The Hive Panel in the web UI renders this as a live activity stream with:
- Agent-colored dots (Scout=blue, Worker=green, Supervisor=gold, Debugger=rose)
- Tool badges with sponsor favicons (Exa, Apify, Nevermined)
- NVM transaction indicators (`$` symbol)
- Scout skill glow effects (gradient background, ping animation)

---

## 8. Economic Behavior

The colony demonstrates autonomous economic decision-making:

| Behavior | How |
|----------|-----|
| **Service discovery** | Scout searches web (Exa), actor stores (Apify), competitor intel (Trust-Net) |
| **ROI evaluation** | Scout scores: margin × demand × ease × uniqueness |
| **Service registration** | Worker creates proxy handlers, tests, goes live |
| **Dynamic pricing** | Surge pricing responds to volume, velocity, demand pressure |
| **Performance review** | Supervisor greenlights/kills based on success rate + revenue |
| **Failure diagnosis** | Debugger classifies errors, patches, verifies fixes |
| **Service graveyard** | Killed services persist to `data/graveyard.json` for display |

---

## Colony State (`/health` endpoint)

```json
{
  "colony": {
    "agents": [
      {
        "name": "mog-scout",
        "role": "discovery",
        "status": "idle",
        "current_task": null,
        "recent_actions": ["scout_exa: found 5 APIs", "self_buy: exa_search ok"],
        "tools": ["check_marketplace", "send_message", "self_buy", "scout_exa", "scout_apify", "scout_trustnet", "propose_service"],
        "last_tick": "2026-03-06T21:06:36Z",
        "tick_count": 12,
        "conversation_length": 8,
        "activity_log": [...]
      }
    ],
    "messages": [...],
    "activity_feed": [...],
    "running": true,
    "tick_interval": 45
  }
}
```

---

## Files

| File | Purpose |
|------|---------|
| `trinity/scout-claude.md` | Scout role template from Trinity |
| `trinity/worker-claude.md` | Worker role template from Trinity |
| `trinity/dashboard-claude.md` | Supervisor role template from Trinity |
| `trinity/design-book.md` | Bloom design system from Trinity |
| `src/agents/agent.py` | Agent class with persistent conversation + compaction |
| `src/agents/loop.py` | AgentColony orchestrator, system prompts, tick loop |
| `src/agents/bus.py` | MessageBus — Trinity dispatch protocol |
| `src/agents/tools.py` | All tool implementations + schemas |
| `web/src/hooks/useTrinity.ts` | Trinity platform API connection |
| `web/src/pages/TrinityPage.tsx` | Colony visualization page |
| `web/src/components/HivePanel.tsx` | Activity stream with agent badges |
| `.mcp.json` | Trinity MCP server configuration |

---

## Summary

Trinity provided the architectural pattern for our autonomous agent colony:

- **Role design** — Scout (strategist), Worker (builder), Supervisor (COO), Debugger (drone)
- **Dispatch protocol** — WRAP BRIEF / WRAP COMPLETE / WRAP FAILED / DEBUG REPORT
- **Platform** — us14.abilityai.dev for agent deployment and chat interface
- **Visualization** — Colony page with agent cards, message history, activity feed

We extended Trinity's patterns with:
- **Nevermined economic behavior** — every agent has its own wallet and transacts
- **Persistent memory** — conversation compaction across ticks
- **Per-agent timeouts** — one hanging agent can't block the colony
- **Scout skills** — specialized tools (Exa, Apify, Trust-Net) with conditional firing
- **Service graveyard** — killed services persist for audit trail

The result: a 4-agent autonomous business that discovers, wraps, prices, sells, monitors, and debugs API services — with real money flowing through Nevermined on every transaction.
