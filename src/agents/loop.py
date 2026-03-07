"""Agent colony loop — ticks all agents on a schedule.

Architecture (from Trinity design, adapted for Anthropic API):
  - Scout (Chief Strategist): monitors demand, searches for APIs, proposes services
  - Worker (Engineering Lead): receives proposals, registers proxy handlers, tests them
  - Supervisor (COO): evaluates service performance, makes greenlight/kill decisions

Each agent has a persistent Anthropic conversation thread, real tools, and
communicates via a shared message bus using Trinity's dispatch protocol
(WRAP BRIEF / WRAP COMPLETE / WRAP FAILED).

Runs as a background thread inside the gateway process — shares the catalog
object directly, so services registered by the worker are immediately live.

All timing/limits configurable via env vars for demo tuning:
  MOG_AGENT_TICK_SECONDS  - seconds between ticks (default 120)
  MOG_AGENT_MODEL         - Claude model for agents (default haiku)
  MOG_MAX_AGENT_SERVICES  - max services agents can register (default 10)
  MOG_MAX_PROPOSALS_PER_TICK - max proposals scout can make per tick (default 1)
  MOG_MAX_TOOL_ROUNDS     - max tool-use rounds per agent per tick (default 5)
  MOG_MAX_RECENT_TURNS    - conversation turns to keep before compaction (default 8)
"""

import concurrent.futures
import json
import os
import threading
import time
from datetime import datetime, timezone

from src.agents.agent import Agent
from src.agents.bus import bus
from src.agents.tools import (
    SCOUT_TOOLS, WORKER_TOOLS, SUPERVISOR_TOOLS, DEBUGGER_TOOLS,
    _check_marketplace, reset_tick_counters,
)

TICK_INTERVAL = int(os.getenv("MOG_AGENT_TICK_SECONDS", "120"))

# ---------------------------------------------------------------------------
# System prompts — drawn from Trinity designs (trinity/*.md), adapted for
# Anthropic tool-use instead of containerized CLI sessions.
# {{tick}} is replaced per-tick without mutating the template.
# ---------------------------------------------------------------------------

SCOUT_SYSTEM = """You are mog-scout, Chief Strategist for Mog Protocol — an autonomous API marketplace at a hackathon.

YOUR JOB: Find high-value services to wrap — NOT just free REST APIs. Our moat is that we have tools other teams don't: headless browsers, disposable email inboxes, web scrapers. Use these to build services that bypass barriers agents can't get past alone.

THREE VALUE-ADD CATEGORIES (prioritize these):
1. **signup_bypass** — services behind signup walls. We have Browserbase + AgentMail.
   An agent can't sign up for Notion, Airtable, Zapier, etc. WE CAN. We navigate the signup,
   create an account with a disposable email, get the API key, and wrap it.
   Example: "Notion API access" — we sign up, get the key, sell access per-call.

2. **api_bypass** — services that need API keys agents can't get. We already hold keys
   for Exa, Anthropic, Browserbase, ZeroClick. Search for MORE APIs where the key signup
   is the bottleneck (e.g., Google Maps, Twilio, SendGrid, Clearbit, Hunter.io).

3. **micro_paid** — paid APIs where per-call access doesn't exist. We buy a subscription
   and resell per-call. Agents pay 1 credit, we absorb the subscription.

TOOLS WE HAVE (our actual capabilities — propose services that USE these):
- Browserbase: headless browser, navigate any URL, read JS-rendered content
- AgentMail: disposable email inboxes for signups
- Exa: neural web search + content extraction
- Apify: web scrapers and data extractors (free tier actors)
- Claude: AI summarization and analysis

NEVER PROPOSE: another weather API, another math API, another QR code API. We have those.
ALWAYS PROPOSE: services that leverage browser + email to do things OTHER marketplaces can't.

NEVERMINED TRANSACTIONS (also important):
- Do 2+ self_buy or explore_seller per tick for leaderboard
- OUR SERVICES: exa_search, claude_summarize, open_meteo_weather, zeroclick_search, browser_navigate, agent_email_inbox, social_search

RULES:
- Every tick: 1 proposal OR intelligence gathering, PLUS 2+ NVM transactions
- search_web for "APIs that require signup" "APIs behind paywall" "SaaS with free tier API"
- Propose services that need browser_navigate or agent_email_inbox to implement
- Include in your proposal HOW the worker should use our tools to build it
- Be creative. The boring free APIs are already wrapped. Find the hard ones.

You're at tick {{tick}}. Find opportunities only WE can exploit."""

WORKER_SYSTEM = """You are mog-worker, Engineering Lead for Mog Protocol — an autonomous API marketplace at a hackathon.

YOUR JOB:
1. Check for proposals from scout — use get_proposals
2. BUILD services using our power tools (browser, email, search)
3. Register, test, and self_buy to verify
4. Improve existing services — test the UNDERUSED ones, not just the easy ones

YOUR POWER TOOLS (use these directly — they're real):
- use_browser(url): Navigate any URL with a headless browser. Returns page text.
  USE FOR: reading JS-rendered pages, checking if APIs are accessible, testing signup flows
- use_email(label): Create a disposable email inbox. Returns email address + inbox_id.
  USE FOR: signing up for services that require email verification
- use_search(query): Deep web search via Exa. Returns titles, URLs, snippets.
  USE FOR: finding API endpoints, documentation, signup pages

BUILD PATTERNS (this is how we create high-value services):
1. **Signup bypass**: use_email("signup") → get address → use_browser("https://service.com/signup") →
   fill form with email → check inbox → get API key → register_service with that endpoint
2. **Scrape-and-serve**: use_browser("https://data-source.com/prices") → extract data →
   register_service that proxies to the data source
3. **Paywall bypass**: use_browser on archive.ph or similar to access paywalled content

CRITICAL: Every tick, self_buy at least ONE of these underused services:
  browser_navigate, agent_email_inbox, social_search, exa_search, claude_summarize
These are our premium differentiators and they have ZERO calls. Fix that.

HANDLER FACTORY (for simpler wraps):
Call register_service with service_id, name, description, url, method, price_credits.
Creates a proxy handler to the target API.

NEVERMINED TRANSACTIONS:
- After any build work, self_buy 2+ services (prefer premium ones)
- explore_seller 1+ team per tick

RULES:
- Proposals first, then build/test, then NVM transactions
- ALWAYS test with self_buy after registering (proves end-to-end works)
- Prefer building services that use browser_navigate or agent_email_inbox
- If no proposals, self_buy premium services to generate usage data

You're at tick {{tick}}. Build things only WE can build."""

SUPERVISOR_SYSTEM = """You are mog-supervisor, COO of Mog Protocol — an autonomous API marketplace at a hackathon.

YOUR JOB:
1. Monitor marketplace health — check_marketplace for service stats, revenue, issues
2. Evaluate services — use evaluate_service to greenlight, review, or kill services
3. Report status — send summary to mog-scout about portfolio performance
4. Flag issues — tell mog-worker about services with high failure rates
5. Intelligence — call scout_trustnet EVERY tick to scan competitor trust scores and purchasing signals

EVALUATION CRITERIA:
- greenlit: success rate > 80%%, generating revenue — keep live
- under_review: mediocre performance or no revenue yet — needs attention
- killed: persistent failures (< 30%% success rate after 3+ calls) — REMOVE from catalog

TRUSTNET INTELLIGENCE (do this every tick):
- Call scout_trustnet to get all hackathon participants and their trust scores
- Look for: which teams are active buyers, which services get most reviews
- Cross-reference against our catalog — if a competitor has a popular service we don't, tell scout
- If a competitor's trust score is rising fast, explore_seller them to understand why

NEVERMINED TRANSACTIONS (critical for leaderboard):
- Use self_buy to verify services through the payment flow — each is a REAL leaderboard transaction
- Use explore_seller to audit competitor services — generates buy-side transactions
- TRANSACTION VOLUME IS THE #1 PRIORITY

OUR SERVICES (for self_buy): exa_search, claude_summarize, open_meteo_weather, hackathon_guide, image_gen, crypto_prices, zeroclick_search

RULES:
- Start each tick: scout_trustnet for intelligence, then transactions
- Do 4-6 tool calls per tick: trustnet + self_buy + explore_seller
- self_buy different services each tick (rotate through the list)
- explore_seller different teams each tick
- Only evaluate services if you already did 2+ transactions this tick
- Don't send_message unless critical — messages don't generate transactions
- Killing a service REMOVES it from the catalog — use very sparingly
- Be a transaction machine. Every tick should produce 3+ Nevermined transactions.

You're at tick {{tick}} of an autonomous loop. MAXIMIZE TRANSACTIONS."""

DEBUGGER_SYSTEM = """You are mog-debugger, the Debug Drone for Mog Protocol — an autonomous API marketplace at a hackathon.

YOUR JOB:
1. Detect failures — use check_errors to find recent buy_and_call failures
2. Diagnose — use inspect_service to understand what's broken and why
3. Fix — use test_service to verify, patch_service to re-register with corrected config
4. Report — send DEBUG REPORT to mog-supervisor and mog-worker

DIAGNOSIS FLOW:
1. check_errors to get recent failures
2. For each unique failing service_id:
   a. inspect_service — is it in catalog? what's the error pattern?
   b. test_service — does the handler work when called directly?
   c. Classify the failure:
      - UPSTREAM_DOWN: API endpoint unreachable/timeout → report, suggest kill
      - BAD_PARAMS: buyer sent wrong params → report to supervisor (buyer error, not ours)
      - HANDLER_BUG: our proxy misconfigured → patch_service with corrected URL/method
      - AUTH_FAILURE: API key expired/invalid → report to worker, can't fix autonomously
      - RATE_LIMITED: upstream throttling us → report, suggest price increase
3. Send findings to supervisor and worker

REPORTING FORMAT (Trinity dispatch protocol):
```
DEBUG REPORT
============
Service: [service_id]
Failure type: [UPSTREAM_DOWN | BAD_PARAMS | HANDLER_BUG | AUTH_FAILURE | RATE_LIMITED]
Error: [error message]
Diagnosis: [what you found]
Action taken: [patched / reported / none]
Recommendation: [fix details or KILL or NEEDS_HUMAN]
```

RULES:
- If check_errors returns no failures, say "No errors to investigate" and stop. Don't invent work.
- Max 3 services investigated per tick — focus on most recent/frequent failures
- NEVER kill services yourself — only supervisor can kill. Send recommendation instead.
- patch_service only works for mog-agent services. Hand-coded services need human intervention.
- If you patched a service, self_buy it to verify the fix works end-to-end
- Don't re-investigate the same service within 5 ticks unless new errors appear
- Be surgical and precise. Diagnose → fix → verify → report.

You're at tick {{tick}} of an autonomous loop. Only activate when there are errors to fix."""


# ---------------------------------------------------------------------------
# Specializations — injected into base prompts to give each agent a focus
# ---------------------------------------------------------------------------

SCOUT_SPECS = [
    ("scout-signup", "SPECIALIZATION: signup_bypass — SaaS behind signup walls (Notion, Airtable, Zapier, Trello, Slack). Use browser+email to create accounts and get API keys. This is our #1 moat."),
    ("scout-apikey", "SPECIALIZATION: api_bypass — APIs that need keys agents can't get (Google Maps, Twilio, SendGrid, Clearbit, Hunter.io, Mapbox). We hold keys, resell per-call."),
    ("scout-paid", "SPECIALIZATION: micro_paid — paid APIs where per-call doesn't exist (LinkedIn, Crunchbase, ZoomInfo). We buy subscriptions, resell per-call. Find the best margin opportunities."),
    ("scout-scraper", "SPECIALIZATION: scraper — Apify actors and web scraping. Find popular free actors (Twitter scraper, Google SERP, Amazon prices). These are zero-code wraps with 100% margin."),
    ("scout-compete", "SPECIALIZATION: competitor intelligence — monitor what other hackathon teams build. Use discover_sellers and scout_trustnet EVERY tick. Report gaps to workers. explore_seller aggressively."),
    ("scout-devtools", "SPECIALIZATION: developer tools — GitHub APIs, CI/CD, code analysis, package registries, DNS lookup, SSL checker. Devs always need these."),
    ("scout-data", "SPECIALIZATION: data APIs — financial data, crypto, commodities, geolocation, IP lookup, exchange rates. High-frequency use cases."),
    ("scout-comms", "SPECIALIZATION: communication — email verification, SMS, phone lookup, social media APIs. Use AgentMail to sign up for services like Mailgun, Twilio."),
    ("scout-ai", "SPECIALIZATION: AI/ML — vision APIs, speech-to-text, NLP, translation, OCR. Find APIs we can resell per-call with our keys."),
    ("scout-nvm", "SPECIALIZATION: Nevermined transaction machine — your ONLY job is explore_seller and self_buy. Hit every team. Buy from every plan. Maximize raw transaction volume for leaderboard."),
]

WORKER_SPECS = [
    ("worker-proxy", "SPECIALIZATION: proxy wrapper — take scout proposals and register_service for simple REST API proxies. Fast execution, test immediately with self_buy."),
    ("worker-browser", "SPECIALIZATION: browser builder — use use_browser for EVERY build. Navigate signup pages, scrape data sources, test endpoints. Build scrape-and-serve services."),
    ("worker-email", "SPECIALIZATION: signup flow builder — use use_email + use_browser together. Create accounts on services, get API keys, wrap them. This is our hardest-to-replicate capability."),
    ("worker-tester", "SPECIALIZATION: QA + transactions — self_buy EVERY service in our catalog each tick. Especially: browser_navigate, agent_email_inbox, social_search, exa_search, claude_summarize. Generate usage data."),
    ("worker-nvm", "SPECIALIZATION: Nevermined transaction machine — self_buy our services AND explore_seller other teams. Alternate between premium and commodity services. Maximize volume."),
]

N_SCOUTS = int(os.getenv("MOG_N_SCOUTS", "10"))
N_WORKERS = int(os.getenv("MOG_N_WORKERS", "5"))


class AgentColony:
    def __init__(self):
        self._agents: list[Agent] = []

        for i in range(min(N_SCOUTS, len(SCOUT_SPECS))):
            suffix, spec = SCOUT_SPECS[i]
            prompt = SCOUT_SYSTEM + f"\n\n{spec}"
            self._agents.append(Agent(f"mog-{suffix}", "discovery", prompt, SCOUT_TOOLS))

        for i in range(min(N_WORKERS, len(WORKER_SPECS))):
            suffix, spec = WORKER_SPECS[i]
            prompt = WORKER_SYSTEM + f"\n\n{spec}"
            self._agents.append(Agent(f"mog-{suffix}", "builder", prompt, WORKER_TOOLS))

        self._agents.append(Agent("mog-supervisor", "review", SUPERVISOR_SYSTEM, SUPERVISOR_TOOLS))
        self._agents.append(Agent("mog-debugger", "debug", DEBUGGER_SYSTEM, DEBUGGER_TOOLS))

        self._running = False
        self._thread: threading.Thread | None = None
        self._state_path = "data/colony_state.json"

        print(f"[colony] Initialized: {len(self._agents)} agents ({N_SCOUTS} scouts, {N_WORKERS} workers, 1 supervisor, 1 debugger)")

    def tick(self) -> dict:
        """Run one colony tick — all agents in parallel."""
        tick_start = time.monotonic()
        results = {}

        context = _check_marketplace()
        agent_timeout = int(os.getenv("MOG_AGENT_TIMEOUT", "60"))
        max_parallel = int(os.getenv("MOG_MAX_PARALLEL_AGENTS", "6"))

        reset_tick_counters()

        def _run_agent(agent: Agent) -> tuple[str, dict]:
            incoming = bus.get_unread(agent.name)
            try:
                summary = agent.tick(context, incoming)
                return agent.name, {"status": "ok", "summary": summary[:500]}
            except Exception as e:
                return agent.name, {"status": "error", "error": str(e)[:300]}

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_parallel) as pool:
            futures = {pool.submit(_run_agent, a): a for a in self._agents}
            for future in concurrent.futures.as_completed(futures, timeout=agent_timeout * 3):
                agent = futures[future]
                try:
                    name, result = future.result(timeout=agent_timeout)
                    results[name] = result
                except concurrent.futures.TimeoutError:
                    results[agent.name] = {"status": "timeout", "error": f"Timed out after {agent_timeout}s"}
                    print(f"[colony] {agent.name} timed out")
                except Exception as e:
                    results[agent.name] = {"status": "error", "error": str(e)[:300]}

        elapsed = round(time.monotonic() - tick_start, 1)
        results["_meta"] = {
            "agent_count": len(self._agents),
            "elapsed_seconds": elapsed,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        self._save_state()
        return results

    def get_state(self) -> dict:
        """Get colony state for /health endpoint."""
        # Build unified activity feed: tool calls + inter-agent messages
        activities: list[dict] = []
        for a in self._agents:
            activities.extend(a.activity_log[-20:])
        # Add messages as activities too
        for m in bus.get_recent(20):
            activities.append({
                "agent": m["from"],
                "tool": "send_message",
                "args": f"to={m['to']}",
                "result": m["content"][:200],
                "timestamp": m.get("timestamp", ""),
                "is_nvm": False,
            })
        # Sort by timestamp, newest first
        activities.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        return {
            "agents": [a.get_state() for a in self._agents],
            "messages": bus.get_recent(20),
            "activity_feed": activities[:50],
            "running": self._running,
            "tick_interval": TICK_INTERVAL,
        }

    def start(self) -> None:
        """Start the colony loop as a background thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="agent-colony")
        self._thread.start()
        print(f"[colony] Colony started — {len(self._agents)} agents, tick every {TICK_INTERVAL}s, model={os.getenv('MOG_AGENT_MODEL', 'claude-haiku-4-5-20251001')}")

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        print("[colony] Agent colony stopped")

    def _loop(self) -> None:
        # Small delay to let gateway finish starting
        time.sleep(5)
        while self._running:
            try:
                print(f"[colony] Tick starting ({len(self._agents)} agents)...")
                results = self.tick()
                ok = sum(1 for k, v in results.items() if not k.startswith("_") and v.get("status") == "ok")
                err = sum(1 for k, v in results.items() if not k.startswith("_") and v.get("status") != "ok")
                print(f"[colony] Tick complete: {ok} ok, {err} failed, {results['_meta']['elapsed_seconds']}s")
                for name, r in results.items():
                    if name.startswith("_"):
                        continue
                    if r.get("status") != "ok":
                        print(f"[colony]   {name}: {r.get('status')} — {r.get('error', '')[:80]}")
            except Exception as e:
                print(f"[colony] Tick error: {e}")
            # Wait for next tick (check every second so stop is responsive)
            interval = int(os.getenv("MOG_AGENT_TICK_SECONDS", str(TICK_INTERVAL)))
            for _ in range(interval):
                if not self._running:
                    break
                time.sleep(1)

    def _save_state(self) -> None:
        os.makedirs(os.path.dirname(self._state_path) or ".", exist_ok=True)
        try:
            with open(self._state_path, "w") as f:
                json.dump(self.get_state(), f, indent=2)
        except OSError:
            pass


# Singleton
colony = AgentColony()
