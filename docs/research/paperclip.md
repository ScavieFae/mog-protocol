# Paperclip — Deep Teardown

[source: https://github.com/paperclipai/paperclip]
[source: https://paperclip.ing]

**Last updated:** 2026-03-04
**Repo created:** 2026-03-02 (two days old as of this research)
**Stars:** ~1,263 | **Forks:** 135 | **Primary language:** TypeScript (~2M lines)
**Sole contributor:** `cryppadotta` (387 commits in 2 days)
**License:** MIT

---

## 1. What It Actually Is

Paperclip is a **Node.js server + React UI that orchestrates multiple AI agents as a simulated company**. It's not an agent framework — it doesn't tell you how to build agents. It's the management layer that sits above them: org charts, task assignment, budgets, governance, and coordination.

The tagline: "If OpenClaw is an _employee_, Paperclip is the _company_."

The core mental model: you define a company goal ("Build the #1 AI note-taking app to $1M MRR"), hire AI "employees" (CEO, CTO, engineers, marketers), set budgets, and let them run. You sit as the "board of directors" — approving hires, reviewing strategy, pausing agents, overriding decisions.

**This is closer to a project management tool for AI agents than it is to an agent runtime.** Think Linear or Asana, but where the employees are Claude Code sessions and Codex instances instead of humans.

---

## 2. Architecture & Technical Approach

### Stack

| Layer | Tech |
|-------|------|
| Frontend | React 19, Vite 6, React Router 7, Radix UI, Tailwind CSS 4, TanStack Query |
| Backend | Express.js 5, TypeScript, Node.js 20+ |
| Database | PostgreSQL 17 (PGlite embedded for dev, real Postgres for prod) |
| ORM | Drizzle ORM with 23+ migrations already |
| Auth | Better Auth (sessions + agent API keys) |
| Package manager | pnpm workspaces (monorepo) |

### Monorepo Structure

```
paperclip/
├── server/          # Express REST API, services, adapters, middleware
├── ui/              # React frontend (50+ components, 20+ pages)
├── cli/             # CLI client (onboarding, doctor, heartbeat-run)
├── packages/
│   ├── db/          # Drizzle schema (25+ tables), migrations
│   ├── shared/      # Types, validators, constants
│   ├── adapter-utils/   # Shared adapter interfaces
│   └── adapters/
│       ├── claude-local/   # Claude Code CLI adapter
│       ├── codex-local/    # OpenAI Codex adapter
│       └── openclaw/       # OpenClaw adapter
├── skills/          # Agent skills (Paperclip heartbeat protocol)
└── doc/             # Specs, plans, product docs
```

### Database Schema (Key Tables)

The schema reveals what's real vs. aspirational:

- `companies` — multi-tenant, each with budget tracking
- `agents` — full employee model: name, role, title, reportsTo, capabilities, adapter config, budget, spend tracking, status
- `agent_config_revisions` — versioned config changes with rollback
- `agent_runtime_state` — persistent state across heartbeats (session IDs)
- `agent_task_sessions` — tracks which agent has which task checked out
- `issues` — full ticket system: status, priority, assignee, parent/child, project, goal linking, billing codes
- `heartbeat_runs` — execution audit log: status, timing, invocation source
- `heartbeat_run_events` — granular event stream per run
- `cost_events` — token/dollar cost tracking per agent per run
- `approvals` — governance gates (hire approvals, strategy approvals)
- `goals` — hierarchical goal trees
- `projects` — project containers with workspace configs
- `project_workspaces` — links projects to local dirs or git repos

### Adapter System

This is the key integration point. Five built-in adapters:

1. **`claude_local`** — Spawns Claude Code CLI as a child process. Passes a prompt, env vars, and optional session resume. Parses stream-json output for usage/cost/session data. Supports `--dangerously-skip-permissions`, model selection, max turns.

2. **`codex_local`** — Same pattern for OpenAI's Codex CLI.

3. **`openclaw`** — Adapter for the OpenClaw agent framework (webhook-style).

4. **`process`** — Generic: runs any shell command as a child process.

5. **`http`** — Generic: fires an HTTP request to any webhook endpoint.

Each adapter implements:
- `execute(context)` — start the agent's work cycle
- `testEnvironment()` — validate the adapter is properly configured
- Optional: `sessionCodec` for persisting/resuming sessions

The adapter contract is clean: **if it can receive a heartbeat, it's hired.**

---

## 3. Agent Orchestration — The Core Interest

This is where Paperclip gets genuinely interesting. The orchestration model has several non-obvious design decisions:

### Heartbeat Protocol

Agents don't run continuously. They run in **heartbeats** — short execution windows triggered by:
- Scheduled intervals (cron-like)
- Event triggers (task assignment, @-mentions in comments)
- Manual invocation from the dashboard

Each heartbeat, the agent wakes up, checks its assignments, does work, reports back, and exits. The `SKILL.md` file defines a 9-step heartbeat procedure that every agent follows:

1. Check identity (`GET /api/agents/me`)
2. Handle approval follow-ups if triggered
3. Fetch assignments (issues assigned to me, filtered by status)
4. Pick work (in_progress first, then todo)
5. **Atomic checkout** — `POST /api/issues/{id}/checkout` (409 Conflict if another agent has it)
6. Read full context (issue + ancestors + comments)
7. Do the actual work
8. Update status and communicate via comments
9. Delegate if needed (create subtasks assigned to other agents)

### Atomic Task Checkout — This Solves a Real Problem

The single-assignee model with atomic checkout is the most important orchestration primitive:

```
POST /api/issues/{issueId}/checkout
{ "agentId": "{your-agent-id}", "expectedStatuses": ["todo", "backlog", "blocked"] }
```

If another agent already has the task: **409 Conflict, stop, pick a different task. Never retry a 409.** This prevents double-work without needing distributed locks, CRDTs, or optimistic concurrency.

This is genuinely well-designed. It's the same pattern as database row-level locking but applied at the task management layer. Combined with cost tracking per checkout, you get accountability.

### Org Chart as Communication Channel

All inter-agent communication flows through the **task system** — not a separate messaging layer:
- **Delegation** = creating a subtask assigned to another agent
- **Coordination** = commenting on tasks
- **Status updates** = patching issue status
- **Escalation** = reassigning to your manager

There's no Slack, no inbox, no side channel. The task graph IS the communication graph. This is a strong design choice — it means every agent interaction is auditable and traceable.

### Cross-Team Delegation

When Agent A needs work from Agent B (outside their reporting line):
- A creates a task assigned to B with a `billingCode` for cost attribution
- B can accept and do it, mark as blocked, or **cannot cancel it** — must reassign to their own manager to decide
- Request depth is tracked (how many delegation hops from the original requester)

### Governance Model

The human sits as the "board of directors" with full powers:
- **Approval gates**: Agent hires require board approval. CEO's initial strategy requires approval.
- **Live controls**: Pause/resume any agent, any task, at any time
- **Budget hard stops**: When an agent hits its monthly budget ceiling, it auto-pauses. Board is notified and can override.
- **Full PM access**: Board can create, edit, reassign, cancel any task directly

### Session Persistence

The Claude adapter maintains session IDs across heartbeats. When an agent wakes up for its next heartbeat, it can resume the same Claude Code session — preserving conversation context rather than starting from scratch. This is stored in `agent_runtime_state` and `agent_task_sessions`.

### Concurrent Run Control

Each agent has a configurable `maxConcurrentRuns` (1-10). Start operations use a per-agent lock (`startLocksByAgent`) to prevent race conditions when multiple triggers fire simultaneously.

---

## 4. What's Real vs. Vaporware

### Definitely Real (Code Exists and Works)

- **Full monorepo with 2M+ lines of TypeScript** — this isn't a demo
- **5 working adapters** (claude_local, codex_local, openclaw, process, http)
- **Complete REST API** with routes for companies, agents, issues, goals, projects, costs, approvals, activity, dashboard
- **Full React UI** with 20+ pages: Dashboard, Org Chart, Kanban Board, Agent Detail, Costs, Approvals, Settings
- **Database schema** with 23+ migrations — iterative development, not a one-shot
- **Heartbeat orchestration** with atomic checkout, session persistence, concurrent run control
- **Cost tracking** with per-agent budgets and auto-pause at ceiling
- **Approval system** with hire gates and status flow
- **Activity logging** for audit trail
- **CLI** with `onboard`, `doctor`, `run`, configuration commands
- **npm publishable** — the CLI is `npx paperclipai onboard --yes`
- **Test suite** present (vitest)

### Partially Built / In Progress

- **Agent permissions system** — schema exists, service exists, but feels early
- **Company portability** (export/import) — types and service code present, but not the full template format from the ClipHub spec
- **WebSocket live updates** — `live-events-ws.ts` exists
- **Multi-company isolation** — schema supports it, but testing depth unclear given 2-day repo age

### Announced but Not Built Yet

- **Clipmart (formerly ClipHub)** — "COMING SOON" in README. Extensive spec exists in `doc/CLIPHUB.md` (a marketplace for downloadable company templates). No code yet.
- **Plugin system** — mentioned in spec and roadmap, no implementation
- **Cloud agent adapters** — on the roadmap
- **Knowledge base** — explicitly an anti-requirement for core (future plugin)
- **Advanced governance** — multi-member boards, hiring budgets, delegated authority — all spec'd but not built
- **Revenue/expense tracking** beyond tokens — explicitly punted to plugin
- **Semantic search** for ClipHub — spec'd but no code

### The Velocity Question

387 commits in 2 days from a single contributor is... a lot. This is almost certainly substantially AI-generated code (using Claude Code or similar). The commit messages show a pattern of rapid iteration: multiple version bumps, fix-after-fix chains, docs corrections. The codebase is large and coherent, but the speed suggests heavy AI assistance in generation.

This doesn't mean it's bad code — the architecture is thoughtful and the spec documents show genuine product thinking. But it does mean the testing surface is probably thin relative to the code volume.

---

## 5. Relationship to Autonomous Business / Agent Orchestration

### What It Gets Right

**The company metaphor is the right abstraction.** Most agent orchestration tools think in terms of workflows or pipelines. Paperclip thinks in terms of companies — with hierarchy, delegation, budgets, and governance. This maps better to the actual problem of managing many agents with different capabilities working toward a shared goal.

**Tasks as the communication primitive.** No side channels, no message buses, no event streams that agents need to understand. Create a task, assign it, comment on it. Every agent already understands this because it's how humans work too. This is drastically simpler than most multi-agent frameworks.

**Atomic checkout solves the coordination problem.** Multi-agent systems routinely fail on "two agents pick up the same work." Paperclip solves this at the data layer with single-assignment and 409 conflicts. Simple, correct, no distributed consensus needed.

**Cost attribution is built in, not bolted on.** Billing codes, per-agent budgets, spend tracking per task — this is essential for autonomous systems and most frameworks ignore it entirely.

**The board governance model is realistic.** Instead of pretending agents can be fully autonomous, Paperclip puts humans in the loop at the right points: hiring decisions, strategic direction, budget approval. This is how actual companies work.

### What's Questionable

**Single-process architecture.** The `startLocksByAgent` uses an in-memory Map, meaning the heartbeat system assumes a single server instance. The issue #60 (horizontal scaling) confirms this is a known limitation. Running "zero-human companies" at scale on a single Node.js process is a hard ceiling.

**No error recovery automation.** By design, when agents crash mid-task, Paperclip surfaces it but doesn't auto-recover. This is philosophically consistent ("surface problems, don't hide them") but means a 24/7 autonomous company still needs human monitoring.

**The CEO agent is doing... what exactly?** The default CEO agent is just a Claude Code session with a prompt telling it to "review strategy, check on reports." There's no actual strategic reasoning — it's an LLM doing task management through API calls. This is fine as a demo but the gap between "CEO agent" and actual strategic direction is vast.

**ClipHub/Clipmart is the real play, and it doesn't exist yet.** The vision of "download and run entire companies with one click" is the transformative feature. Without it, Paperclip is a sophisticated task manager. With it, it's potentially an app store for businesses. But it's entirely spec at this point.

### The Ambition

From GOAL.md:

> "Our goal is for Paperclip-powered companies to collectively generate economic output that rivals the GDP of the world's largest countries."

This is a genuinely bold thesis: that autonomous AI companies become an economic layer comparable to national economies, and Paperclip is the operating system they run on. The name is obviously a reference to the paperclip maximizer — which is either cheeky or concerning depending on your disposition.

---

## 6. MCP, Payments, and Agent-to-Agent Commerce

### MCP (Model Context Protocol)

There's a `doc/TASKS-mcp.md` file that defines **35 MCP operations** for the task management system. This is an interface spec — `list_issues`, `create_issue`, `update_issue`, `checkout_issue`, etc. — designed to expose Paperclip's task system via MCP so that external tools and agents can interact with it through the standard protocol.

However, this appears to be a **spec document, not working code**. The actual agent integration currently works through:
1. Environment variables injected at heartbeat time
2. Direct REST API calls from agents
3. The `SKILL.md` file that teaches agents the API

The MCP interface is planned but not yet the primary integration path.

### Payments / Agent Commerce

**There is no payments system, crypto integration, or agent-to-agent commerce layer.** The cost tracking is purely internal accounting — tracking token spend per agent per task. There's:
- No external payment processing
- No agent-to-agent financial transactions
- No crypto, blockchain, or tokenization
- No x402, no payment channels, no invoicing
- No concept of agents buying services from other agents

The "budget" system is about cost control (auto-pause when spend exceeds threshold), not about agents having wallets or making purchases.

### Where Commerce Could Emerge

The ClipHub/Clipmart marketplace spec is the closest thing to a commerce layer:
- Company templates published and downloaded (currently free-only, paid is "not in scope")
- The template format is a portable artifact — an "agent configuration package"
- If ClipHub added paid templates, you'd have agent-to-agent commerce (one company buying another company's template)

But this is speculative. The current design is explicitly free and public.

<!-- riff id="paperclip-agent-commerce-gap" status="draft" could_become="interview_answer, blog" -->

The interesting gap here is that Paperclip models the *internal* economics of an agent company (budgets, cost attribution, billing codes) but completely ignores the *external* economics (revenue, payments, pricing). The spec explicitly punts revenue tracking to a "future plugin." But if you're building autonomous companies, the revenue side is where autonomy actually matters — an agent that can't accept payment or price its services isn't really autonomous, it's subsidized.

This is the exact gap that x402 / payment protocols for agents could fill. Paperclip provides the organizational layer; something like x402 or Nevermined could provide the economic layer. They're complementary rather than competitive.

<!-- /riff -->

---

## 7. Key Technical Details Worth Knowing

### The Skill System

Paperclip ships "skills" — markdown files that teach agents how to interact with the Paperclip API. The main `skills/paperclip/SKILL.md` is injected into every Claude Code agent via `--add-dir`. This is the closest thing to "agent training" — it's really just prompt injection with API documentation and behavioral rules.

There's also a `skills/create-agent-adapter/SKILL.md` for teaching agents how to create new adapter types, and a `skills/paperclip-create-agent/SKILL.md` for the hiring workflow.

### Environment Variable Injection

When a heartbeat fires, the adapter injects:
- `PAPERCLIP_AGENT_ID`, `PAPERCLIP_COMPANY_ID`, `PAPERCLIP_API_URL`
- `PAPERCLIP_RUN_ID` (for audit trail)
- `PAPERCLIP_API_KEY` (short-lived JWT for local adapters)
- `PAPERCLIP_TASK_ID` (if triggered by a specific task)
- `PAPERCLIP_WAKE_REASON` (why this heartbeat fired)
- `PAPERCLIP_WAKE_COMMENT_ID` (if triggered by an @-mention)
- `PAPERCLIP_APPROVAL_ID` (if triggered by approval resolution)
- Workspace context (cwd, repo URL, workspace ID)

This is well-designed — the agent gets everything it needs to orient itself without calling the API first.

### The Wakeup System

Beyond scheduled heartbeats, agents can be woken by events:
- Task assignment triggers a wakeup for the assigned agent
- @-mentions in comments trigger wakeups
- Approval resolutions trigger wakeups for the requesting agent
- `agent_wakeup_requests` table queues these

### Config Revisions with Rollback

Every change to an agent's configuration is versioned in `agent_config_revisions`. Bad config changes can be rolled back to a previous revision. This is unusually thoughtful for a 2-day-old project.

---

## 8. Assessment

### Strength of the Idea: Strong

The "company as orchestration primitive" model is genuinely novel and well-reasoned. Most multi-agent frameworks either go too low-level (message passing, tool calling) or too high-level (drag-and-drop workflows). Paperclip hits a sweet spot: org charts, tasks, budgets, and governance are concepts that both humans and agents can reason about.

### Strength of the Execution: Impressive but Unproven

2M lines of TypeScript in 2 days is staggering output, likely AI-generated. The architecture is coherent, the spec documents show real product thinking, and the code structure is professional. But: thin test coverage relative to code volume, single-process limitations, and the most ambitious features (ClipHub, plugin system) don't exist yet.

### Risk: Sole Developer

387 commits from one person (`cryppadotta`). No team, no institutional backing visible. The project could stall tomorrow. The MIT license means anyone could fork it, but the architecture knowledge lives in one person's head.

### Competitive Positioning

- vs. **CrewAI / AutoGen / LangGraph** — Different category. Those are agent frameworks (how to build agents). Paperclip is agent management (how to run a company of agents). Complementary, not competitive.
- vs. **Linear / Asana / Jira** — Paperclip is what these tools would look like if your entire team were AI agents. The task model borrows heavily from Linear (the MCP spec is almost a Linear-compatible interface).
- vs. **OpenClaw** — Paperclip explicitly positions above OpenClaw: "If OpenClaw is an employee, Paperclip is the company."

### -> Interview / Anthropolitic

The "zero-human company" framing is a strong conversation topic for interviews at AI companies. The key insight: **orchestrating agents requires company-shaped infrastructure, not pipeline-shaped infrastructure.** Hierarchy, delegation, budgets, governance — these are management problems, not engineering problems, and they need management tools.

The gap between Paperclip (internal orchestration) and payment/commerce protocols (external economics) is a genuine research thread worth developing. Autonomous companies that can't transact aren't really autonomous.

---

## 9. Links

- GitHub: https://github.com/paperclipai/paperclip
- Website: https://paperclip.ing
- Docs: https://paperclip.ing/docs
- Discord: https://discord.gg/m4HZY7xNG3
- npm: `npx paperclipai onboard --yes`
