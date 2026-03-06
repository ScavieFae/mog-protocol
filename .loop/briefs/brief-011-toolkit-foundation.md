# Brief: Agent Toolkit Foundation

**Branch:** brief-011-toolkit-foundation
**Model:** sonnet

## Goal

Create `src/toolkit.py` — the unified capability layer that lets our agents browse the web, manage email, store credentials, and file structured blocker reports. This is the swiss army knife that unblocks the "needs signup" wall.

## Context

Read these before starting:
- `docs/specs/10-agent-toolkit.md` — full spec with architecture, code examples, credential flow
- `src/services.py` — existing service handlers (for reference on style/patterns)
- `src/portfolio.py` — PortfolioManager (toolkit integrates with this for spend decisions)

## Tasks

1. **Create `src/toolkit.py` with Trace + four sublayers.** Single file, class-per-layer. Each layer is a module-level singleton.

   **Trace** — Lightweight operation trace. Every toolkit method accepts an optional `trace` param and appends one short line. This is how the conductor reconstructs what happened without reading logs.
   ```python
   class Trace:
       def __init__(self, operation: str = ""):
           self.operation = operation        # e.g. "evaluate openweather"
           self.steps: list[str] = []
           self.started_at = datetime.now(timezone.utc).isoformat()

       def log(self, layer: str, action: str, result: str):
           """Append one trace step. Keep result SHORT — truncate to 80 chars."""
           result = result[:80]
           self.steps.append(f"{layer}:{action} -> {result}")

       def summary(self) -> list[str]:
           """Return last 20 steps (cap to prevent bloat)."""
           return self.steps[-20:]

       def to_dict(self) -> dict:
           return {
               "operation": self.operation,
               "started_at": self.started_at,
               "step_count": len(self.steps),
               "steps": self.summary(),
           }
   ```

   Usage pattern — caller creates a trace, passes it through, trace ends up on the right record:
   ```python
   trace = Trace("evaluate openweather")
   results = research.social_comments("twitter.com", "weather API", trace=trace)
   page = browse.navigate(session, "https://openweathermap.org/signup", trace=trace)
   # ...if blocked:
   blockers.report(service_id="openweather", ..., trace=trace)
   # ...if success:
   portfolio.update_hypothesis(hyp_id, "validated", validation_trace=trace.summary())
   ```

   The blocker report stores `trace.to_dict()` in its `trace` field. Hypotheses store `trace.summary()` in `validation_trace`. Short, clean, reconstructable.

   **BrowseLayer** — Browserbase headless browser:
   ```python
   class BrowseLayer:
       def __init__(self):
           self.api_key = os.getenv("BROWSERBASE_API_KEY")
           self.project_id = os.getenv("BROWSERBASE_PROJECT_ID")

       def create_session(self, trace: Trace = None) -> dict:
           """Create a Browserbase session. Returns {session_id, connect_url}."""
           # trace.log("browse", "create_session", f"ok sid={session_id[:8]}")

       def navigate(self, session_id: str, url: str, trace: Trace = None) -> dict:
           """Navigate to URL, return {title, text, url}."""
           # trace.log("browse", f"navigate({url})", f"ok title='{title}'")

       def get_text(self, session_id: str, selector: str = "body", trace: Trace = None) -> str:
           """Get text content from current page or specific selector."""

       def fill_form(self, session_id: str, fields: dict, trace: Trace = None) -> bool:
           """Fill form fields by name/id/label. Returns success."""
           # trace.log("browse", f"fill_form({','.join(fields.keys())})", "ok" or "FAIL ...")

       def click(self, session_id: str, selector_or_text: str, trace: Trace = None) -> bool:
           """Click an element by CSS selector or visible text."""
           # trace.log("browse", f"click({selector_or_text})", "ok" or "FAIL ...")

       def screenshot(self, session_id: str, trace: Trace = None) -> str:
           """Take screenshot, return base64 data URI."""

       def close_session(self, session_id: str) -> None:
           """Close the browser session."""
   ```
   If `BROWSERBASE_API_KEY` is not set, all methods return `{"error": "BROWSERBASE_API_KEY not set"}` (graceful degradation, same pattern as other services).

   **EmailLayer** — AgentMail:
   ```python
   class EmailLayer:
       def __init__(self):
           self.api_key = os.getenv("AGENTMAIL_API_KEY")

       def create_inbox(self, label: str, trace: Trace = None) -> dict:
           """Create a named inbox. Returns {inbox_id, address}."""
           # trace.log("email", f"create_inbox({label})", f"ok {address}")

       def send(self, inbox_id: str, to: str, subject: str, body: str, trace: Trace = None) -> bool:
           """Send an email from an inbox."""
           # trace.log("email", f"send(to={to})", "ok" or "FAIL ...")

       def check_inbox(self, inbox_id: str, wait_seconds: int = 0, limit: int = 10, trace: Trace = None) -> list:
           """List messages. If wait_seconds > 0, poll until a message arrives or timeout."""
           # trace.log("email", f"check_inbox(wait={wait_seconds})", f"{n} messages")

       def extract_verification(self, message: dict, trace: Trace = None) -> str | None:
           """Extract verification code (6-digit) or URL from email body."""
           # trace.log("email", "extract_verification", "code found" or "link found" or "FAIL none")
   ```

   **VaultLayer** — Credential storage:
   ```python
   class VaultLayer:
       def __init__(self, path="data/vault.json"):
           # Same persistence pattern as PortfolioManager

       def store(self, key_name: str, value: str, service_id: str = "", source: str = "") -> None:
           """Store a credential. Overwrites if key_name exists."""

       def get(self, key_name: str) -> str | None:
           """Retrieve a credential by name."""

       def list_keys(self) -> list[dict]:
           """List all stored credentials (name, service_id, created_at — NOT values)."""

       def delete(self, key_name: str) -> bool:
           """Remove a credential."""
   ```
   File: `data/vault.json` (gitignored). Thread-safe with `threading.Lock`.

   **BlockerLayer** — Structured failure reporting:
   ```python
   class BlockerLayer:
       def __init__(self, path="data/blockers.json"):

       def report(self, service_id: str, blocker_type: str, description: str,
                  trace: Trace = None, recommendation: str = "SKIP",
                  opportunity_value: int = 5) -> str:
           """File a blocker report. Returns report ID.
           If trace is provided, stores trace.to_dict() on the report.
           blocker_type: signup_required | api_key_needed | paywall | rate_limited | auth_flow | captcha | other
           recommendation: ESCALATE | RETRY_WITH_TOOL | SKIP | DEFER"""

       def get_recent(self, limit: int = 10) -> list[dict]:
           """Recent blockers, newest first."""

       def get_by_type(self, blocker_type: str) -> list[dict]:
           """All blockers of a given type."""

       def get_escalations(self) -> list[dict]:
           """Blockers with recommendation=ESCALATE."""
   ```
   File: `data/blockers.json` (gitignored). Thread-safe.

   Module-level singletons:
   ```python
   browse = BrowseLayer()
   email = EmailLayer()
   vault = VaultLayer()
   blockers = BlockerLayer()
   ```

2. **Ensure `data/` directory exists with `.gitkeep`, and add `data/vault.json` and `data/blockers.json` to `.gitignore`.** Portfolio JSON too if not already there.

3. **Add `python -m src.traces` CLI viewer.** Create `src/traces.py` with a `__main__` block that prints recent traces from blockers and portfolio hypotheses in a clean format:
   ```
   $ python -m src.traces
   RECENT TRACES
   ─────────────
   [blocker] stripe (captcha) ESCALATE — 2m ago, 8 steps
     browse:navigate(stripe.com/signup) -> ok title='Sign Up'
     browse:fill_form(email,password) -> ok
     browse:click(Create Account) -> FAIL captcha detected

   [hypothesis] openweather (validated) — 15m ago, 5 steps
     exa:social_comments(twitter.com, weather API) -> 12 results
     browse:navigate(openweathermap.org/signup) -> ok
     email:check_inbox(wait=30) -> 1 message
     vault:store(openweather_api_key) -> ok

   3 traced operations (2 blockers, 1 hypothesis)
   ```
   Implementation: read `data/blockers.json` and `data/portfolio.json`, filter entries that have traces, sort by timestamp, print with simple formatting. Keep it under 50 lines. Accepts optional `--limit N` flag (default 10).

4. **Create `src/test_toolkit.py` — tests for Trace, vault, and blockers (no API keys needed).** Test:
   - Trace: log steps, summary caps at 20, to_dict includes operation and step_count, result truncation at 80 chars
   - Trace with blocker: create trace, log steps, pass to blockers.report(), verify trace appears on report
   - Vault: store, get, list_keys (no values exposed), delete, overwrite, persistence round-trip
   - Blockers: report (returns ID), get_recent, get_by_type, get_escalations
   - BrowseLayer: test graceful degradation when no API key (returns error dict)
   - EmailLayer: test graceful degradation when no API key
   Skip tests that require live Browserbase/AgentMail connections (mark them or just don't write them — the env-missing graceful degradation test is sufficient).

## Completion Criteria

- [ ] `src/toolkit.py` exists with Trace, BrowseLayer, EmailLayer, VaultLayer, BlockerLayer
- [ ] All five exports: `Trace`, `browse`, `email`, `vault`, `blockers`
- [ ] Every toolkit method accepts optional `trace: Trace` and logs one short line
- [ ] BlockerLayer.report() stores trace.to_dict() when trace is provided
- [ ] `python -m src.traces` prints recent traces from blockers + hypotheses
- [ ] Graceful degradation: no crashes when API keys are missing
- [ ] `data/vault.json` and `data/blockers.json` gitignored
- [ ] `src/test_toolkit.py` passes for vault + blockers + graceful degradation
- [ ] Thread-safe persistence for vault and blockers

## Verification

- `python -m pytest src/test_toolkit.py -v` (or `python src/test_toolkit.py`)
- `python -c "from src.toolkit import browse, email, vault, blockers; print('All layers loaded')"` works
- `python -c "from src.toolkit import vault; vault.store('test', 'val'); assert vault.get('test') == 'val'; print('Vault works')"` works
- `python -m src.traces` runs without error (prints "0 traced operations" if no data yet)
